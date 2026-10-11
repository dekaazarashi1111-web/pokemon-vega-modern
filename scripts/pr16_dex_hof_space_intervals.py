"""部分lease候補の純粋な区間計算。権限・退役証明・ROM書換は実装しない。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Span:
    start: int
    end: int

    def __post_init__(self):
        if (type(self.start) is not int or type(self.end) is not int
                or not 0 <= self.start < self.end <= 2 ** 32):
            raise ValueError("区間は非空の32bit整数半開区間でなければならない")

    @property
    def size(self):
        return self.end - self.start


@dataclass(frozen=True)
class Access:
    """extent=Noneはconsumerの最大アクセス範囲が不明であることを表す。"""
    origin: int
    target: int
    extent: tuple[Span, ...] | None = None

    def __post_init__(self):
        if any(type(v) is not int or not 0 <= v < 2 ** 32
               for v in (self.origin, self.target)):
            raise ValueError("origin/targetは32bit整数アドレスのみ")
        if self.extent is not None:
            if (type(self.extent) is not tuple or not self.extent
                    or any(not isinstance(s, Span) for s in self.extent)
                    or not any(s.start <= self.target < s.end for s in self.extent)):
                raise ValueError("有限extentはtargetを含む非空の保守的包絡のみ")


def merge_clip(domain: Span, spans: tuple[Span, ...]) -> tuple[Span, ...]:
    """domainへ切り詰め、重複と隣接を一回だけ数える。"""
    pieces = sorted((max(domain.start, s.start), min(domain.end, s.end))
                    for s in spans if s.start < domain.end and domain.start < s.end)
    out = []
    for start, end in pieces:
        if out and start <= out[-1][1]:
            out[-1] = (out[-1][0], max(end, out[-1][1]))
        else:
            out.append((start, end))
    return tuple(Span(*p) for p in out)


def complement(domain: Span, protected: tuple[Span, ...]) -> tuple[Span, ...]:
    cursor, out = domain.start, []
    for s in merge_clip(domain, protected):
        if cursor < s.start:
            out.append(Span(cursor, s.start))
        cursor = s.end
    if cursor < domain.end:
        out.append(Span(cursor, domain.end))
    return tuple(out)


def aligned(gaps: tuple[Span, ...], alignment: int) -> tuple[Span, ...]:
    if type(alignment) is not int or alignment <= 0 or alignment & (alignment - 1):
        raise ValueError("整列は正の2冪整数のみ")
    result = []
    for s in gaps:
        start = (s.start + alignment - 1) & -alignment
        if start < s.end:
            result.append(Span(start, s.end))
    return tuple(result)


def plan_geometry(domain: Span, owners: tuple[Span, ...], accesses: tuple[Access, ...],
                  unresolved_obligations: tuple[str, ...], request_bytes: int,
                  alignment: int = 4) -> dict:
    """数学的候補のみ。ownerを解放する引数やlease承認booleanは存在しない。

    ownersは既存ownerを省略せず入力する。有限extentの正しさを本関数は証明しない。
    生産用の署名検証/退役validatorを追加するまでは出力を使用権限へ昇格できない。
    """
    if type(request_bytes) is not int or request_bytes <= 0:
        raise ValueError("要求byte数は正の整数のみ")
    if (type(owners) is not tuple or any(not isinstance(s, Span) for s in owners)
            or type(accesses) is not tuple or any(not isinstance(a, Access) for a in accesses)
            or type(unresolved_obligations) is not tuple
            or any(type(s) is not str or not s for s in unresolved_obligations)):
        raise ValueError("型付き不変入力だけを受け取る")
    aligned((), alignment)
    if len({a.origin for a in accesses}) != len(accesses):
        raise ValueError("同一originを別consumerとして二重計上できない")
    if any(not domain.start <= a.target < domain.end for a in accesses):
        raise ValueError("全targetは監査対象domainに含まれなければならない")
    unknown = tuple(a for a in accesses if a.extent is None)
    protect = list(owners)
    for a in accesses:
        protect.extend((domain,) if a.extent is None else a.extent)
    if unresolved_obligations:
        protect.append(domain)
    merged = merge_clip(domain, tuple(protect))
    gaps = complement(domain, merged)
    usable = aligned(gaps, alignment)
    return {
        "status": "GEOMETRY_ONLY_NOT_A_LEASE",
        "owner_count": len(owners),
        "unbounded_access_count": len(unknown),
        "unresolved_obligations": list(unresolved_obligations),
        "protected": [{"address": s.start, "size": s.size} for s in merged],
        "gaps": [{"address": s.start, "size": s.size} for s in gaps],
        "aligned_gaps": [{"address": s.start, "size": s.size} for s in usable],
        "total_unprotected_bytes": sum(s.size for s in gaps),
        "largest_aligned_gap_bytes": max((s.size for s in usable), default=0),
        "requested_bytes": request_bytes,
        "geometry_fits_contiguously": any(s.size >= request_bytes for s in usable),
        "lease_eligible": False,
        "lease_authorized_semantics": "technical_allocator_lease_not_user_permission",
        "lease_authorized": False,
        "rom_mutation_performed": False,
    }


def plan_materialized_successor(parent_audit: dict, current_audit: dict,
                                owner_checkpoint: dict, domain: Span,
                                request_bytes: int = 6528, alignment: int = 4) -> dict:
    """同一874 inventoryの後継unknown Nへ適用する。chainの受入validatorではない。

    呼出側が独立identityで認証済みの親・materialized後継・owner CPを渡す。
    この関数は保存済みchainの意味を再レビューせず、inventory保存と保守容量だけ検査。
    新分類の根拠は別validatorで確認する必要があり、この結果はlease権限にならない。
    """
    fields = ("address", "target", "kind", "size", "sha256")
    candidate = parent_audit["candidate"]
    if current_audit["candidate"] != candidate or owner_checkpoint["candidate"] != candidate:
        raise ValueError("親・後継・owner checkpointは同一candidateが必須")
    old, current = parent_audit["hits"], current_audit["hits"]
    if len(old) != 874 or len(current) != 874:
        raise ValueError("全874行を省略できない")
    if (len({r["address"] for r in old}) != 874
            or len({r["address"] for r in current}) != 874):
        raise ValueError("inventoryのoriginは一意")
    for before, after in zip(old, current):
        if any(before[k] != after[k] for k in fields):
            raise ValueError("全874行のidentity・順序を変更できない")
        if type(before["accepted"]) is not bool or type(after["accepted"]) is not bool:
            raise ValueError("acceptedは厳密booleanのみ")
        if before["accepted"] or not after["accepted"]:
            if before != after:
                raise ValueError("既acceptedと残unknownの全fieldを保持する")
    for audit in (parent_audit, current_audit):
        count = sum(r["accepted"] for r in audit["hits"])
        if audit["classified"] != count or audit["unclassified"] != 874 - count:
            raise ValueError("保存済みcounterと全874行が不一致")
    owner_rows = owner_checkpoint["placement"]["owner_byte_audit"]
    if len(owner_rows) != 115 or len({r["name"] for r in owner_rows}) != 115:
        raise ValueError("全115actual ownerを省略できない")
    owners = tuple(Span(r["address"], r["address"] + r["size"]) for r in owner_rows)
    if not any(s == domain for s in owners):
        raise ValueError("明示移管前の旧egg owner全域が保持されていない")
    remaining = tuple(Access(r["address"], r["target"]) for r in current if not r["accepted"])
    result = plan_geometry(domain, owners, remaining, (
        "indirect_reference_completeness_unproven",
        "partial_retirement_and_explicit_owner_transfer_unproven",
    ), request_bytes, alignment)
    result.update(parent_unknown_count=parent_audit["unclassified"],
                  current_unknown_count=current_audit["unclassified"],
                  newly_classified_count=current_audit["classified"] - parent_audit["classified"],
                  full_inventory_count=874, candidate=candidate,
                  semantic_chain_acceptance_rechecked=False)
    return result
