#!/usr/bin/env python3
"""32 MiB GBA ROM向けの決定的なnamed-region allocator。

入力は配置metadataだけを受け取り、ROMやmoduleのraw bytesは受け取らない。
全intervalはROM file offsetのhalf-open ``[start, end_exclusive)`` で扱う。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = 1
ROM_SIZE = 32 * 1024 * 1024
GBA_ROM_BASE = 0x08000000
REGION_CSV_FIELDS = (
    "name",
    "start",
    "end_exclusive",
    "alignment",
    "kind",
    "owner",
    "purpose",
)
REGION_KINDS = frozenset({"allocatable", "reserved"})
REQUEST_FIELDS = frozenset(
    {
        "name",
        "region",
        "size",
        "alignment",
        "start",
        "owner",
        "purpose",
        "content_sha256",
    }
)
_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]*\Z")
_SHA256_RE = re.compile(r"[0-9a-fA-F]{64}\Z")
_INTEGER_RE = re.compile(r"(?:0[xX][0-9a-fA-F]+|[0-9]+)\Z")


class RomAllocationError(ValueError):
    """Regionまたはallocation contract違反。"""


@dataclass(frozen=True, slots=True)
class RomRegion:
    name: str
    start: int
    end_exclusive: int
    alignment: int
    kind: str
    owner: str
    purpose: str

    @property
    def size(self) -> int:
        return self.end_exclusive - self.start

    def to_report(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start": self.start,
            "end_exclusive": self.end_exclusive,
            "size": self.size,
            "alignment": self.alignment,
            "kind": self.kind,
            "owner": self.owner,
            "purpose": self.purpose,
            "gba_start": GBA_ROM_BASE + self.start,
            "gba_end_exclusive": GBA_ROM_BASE + self.end_exclusive,
        }


@dataclass(frozen=True, slots=True)
class RomAllocation:
    name: str
    region: str
    start: int
    end_exclusive: int
    size: int
    alignment: int
    placement: str
    owner: str
    purpose: str
    content_sha256: str
    sequence: int

    def to_report(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "region": self.region,
            "start": self.start,
            "end_exclusive": self.end_exclusive,
            "size": self.size,
            "alignment": self.alignment,
            "placement": self.placement,
            "owner": self.owner,
            "purpose": self.purpose,
            "content_sha256": self.content_sha256,
            "sequence": self.sequence,
            "gba_start": GBA_ROM_BASE + self.start,
            "gba_end_exclusive": GBA_ROM_BASE + self.end_exclusive,
        }


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise RomAllocationError(f"{label} must be an integer, not bool")
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        raise RomAllocationError(f"{label} must be an integer or integer string")
    text = value.strip()
    if not _INTEGER_RE.fullmatch(text):
        raise RomAllocationError(f"{label} is not a canonical decimal/hex integer: {value!r}")
    return int(text, 16 if text.lower().startswith("0x") else 10)


def _name(value: object, label: str) -> str:
    if not isinstance(value, str) or not _NAME_RE.fullmatch(value):
        raise RomAllocationError(
            f"{label} must match [A-Za-z0-9][A-Za-z0-9_.:-]*"
        )
    return value


def _text(value: object, label: str, *, allow_empty: bool) -> str:
    if not isinstance(value, str):
        raise RomAllocationError(f"{label} must be text")
    text = value.strip()
    if not allow_empty and not text:
        raise RomAllocationError(f"{label} must not be empty")
    if "\x00" in text or "\r" in text or "\n" in text:
        raise RomAllocationError(f"{label} contains a forbidden control character")
    return text


def _alignment(value: object, label: str) -> int:
    alignment = _integer(value, label)
    if alignment <= 0 or alignment > ROM_SIZE or alignment & (alignment - 1):
        raise RomAllocationError(f"{label} must be a positive power of two")
    return alignment


def _align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _validate_region(region: RomRegion) -> None:
    _name(region.name, "region.name")
    if not isinstance(region.kind, str) or region.kind not in REGION_KINDS:
        raise RomAllocationError(
            f"region {region.name!r} kind must be allocatable or reserved"
        )
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in (region.start, region.end_exclusive, region.alignment)
    ):
        raise RomAllocationError(
            f"region {region.name!r} start/end/alignment must be integers"
        )
    if not 0 <= region.start < region.end_exclusive <= ROM_SIZE:
        raise RomAllocationError(
            f"region {region.name!r} is outside [0, {ROM_SIZE:#x}) or empty"
        )
    alignment = _alignment(region.alignment, f"region {region.name!r} alignment")
    if region.start % alignment:
        raise RomAllocationError(
            f"region {region.name!r} start is not aligned to {alignment}"
        )
    _text(region.owner, f"region {region.name!r} owner", allow_empty=False)
    _text(region.purpose, f"region {region.name!r} purpose", allow_empty=False)


def validate_regions(regions: Iterable[RomRegion]) -> tuple[RomRegion, ...]:
    """Regionを検証し、address/nameの安定順で返す。

    ``reserved`` 同士を含む全region pairのoverlapを拒否する。隣接は許可する。
    """

    materialized = tuple(regions)
    if not materialized:
        raise RomAllocationError("at least one ROM region is required")
    seen: set[str] = set()
    for region in materialized:
        if not isinstance(region, RomRegion):
            raise RomAllocationError("regions must contain RomRegion values")
        _validate_region(region)
        if region.name in seen:
            raise RomAllocationError(f"duplicate region name: {region.name}")
        seen.add(region.name)
    ordered = tuple(
        sorted(
            materialized,
            key=lambda item: (item.start, item.end_exclusive, item.name),
        )
    )
    for left, right in zip(ordered, ordered[1:]):
        if right.start < left.end_exclusive:
            raise RomAllocationError(
                "overlapping ROM regions: "
                f"{left.name}[{left.start:#x},{left.end_exclusive:#x}) and "
                f"{right.name}[{right.start:#x},{right.end_exclusive:#x})"
            )
    return ordered


def load_regions_csv(path: Path) -> tuple[RomRegion, ...]:
    """厳密なCSV schemaからregionを読み込み、検証済み安定順で返す。"""

    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise RomAllocationError(f"region CSV must be a regular non-symlink file: {path}")
    source_text = path.read_text(encoding="utf-8-sig")
    for line_number, line in enumerate(source_text.splitlines(), 1):
        if not line.strip():
            raise RomAllocationError(f"region CSV line {line_number} is blank")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REGION_CSV_FIELDS:
            raise RomAllocationError(
                "region CSV header mismatch; expected " + ",".join(REGION_CSV_FIELDS)
            )
        regions: list[RomRegion] = []
        for line_number, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise RomAllocationError(f"region CSV line {line_number} has extra/missing cells")
            try:
                region = RomRegion(
                    name=_name(row["name"], "region.name"),
                    start=_integer(row["start"], "region.start"),
                    end_exclusive=_integer(
                        row["end_exclusive"], "region.end_exclusive"
                    ),
                    alignment=_alignment(row["alignment"], "region.alignment"),
                    kind=_text(row["kind"], "region.kind", allow_empty=False),
                    owner=_text(row["owner"], "region.owner", allow_empty=False),
                    purpose=_text(
                        row["purpose"], "region.purpose", allow_empty=False
                    ),
                )
            except RomAllocationError as error:
                raise RomAllocationError(
                    f"region CSV line {line_number}: {error}"
                ) from error
            regions.append(region)
    if not regions:
        raise RomAllocationError("region CSV must contain at least one region")
    return validate_regions(regions)


class RomAllocator:
    """検証済みregion内へmetadata-only allocationを配置する。"""

    def __init__(self, regions: Iterable[RomRegion]):
        self._regions = validate_regions(regions)
        self._regions_by_name = {region.name: region for region in self._regions}
        self._allocations: list[RomAllocation] = []
        self._allocation_names: set[str] = set()

    @property
    def regions(self) -> tuple[RomRegion, ...]:
        return self._regions

    @property
    def allocations(self) -> tuple[RomAllocation, ...]:
        return tuple(self._allocations)

    def _occupied(self, region_name: str) -> list[RomAllocation]:
        return sorted(
            (
                allocation
                for allocation in self._allocations
                if allocation.region == region_name
            ),
            key=lambda item: (item.start, item.end_exclusive, item.name),
        )

    def _first_fit(self, region: RomRegion, size: int, alignment: int) -> int:
        candidate = _align_up(region.start, alignment)
        for occupied in self._occupied(region.name):
            if candidate + size <= occupied.start:
                return candidate
            if candidate < occupied.end_exclusive:
                candidate = _align_up(occupied.end_exclusive, alignment)
        if candidate + size <= region.end_exclusive:
            return candidate
        raise RomAllocationError(
            f"allocation of {size} bytes does not fit region {region.name!r}"
        )

    def allocate(
        self,
        name: str,
        region: str,
        size: int | str,
        *,
        alignment: int | str | None = None,
        start: int | str | None = None,
        owner: str = "",
        purpose: str = "",
        content_sha256: str = "",
    ) -> RomAllocation:
        """1件を配置する。``start=None`` はregion内の決定的first-fit。"""

        allocation_name = _name(name, "allocation.name")
        if allocation_name in self._allocation_names:
            raise RomAllocationError(f"duplicate allocation name: {allocation_name}")
        region_name = _name(region, "allocation.region")
        target = self._regions_by_name.get(region_name)
        if target is None:
            raise RomAllocationError(f"unknown allocation region: {region_name}")
        if target.kind != "allocatable":
            raise RomAllocationError(f"region {region_name!r} is reserved")
        allocation_size = _integer(size, f"allocation {allocation_name!r} size")
        if allocation_size <= 0:
            raise RomAllocationError(
                f"allocation {allocation_name!r} size must be greater than zero"
            )
        requested_alignment = (
            target.alignment
            if alignment is None or alignment == ""
            else _alignment(alignment, f"allocation {allocation_name!r} alignment")
        )
        effective_alignment = max(target.alignment, requested_alignment)
        allocation_owner = _text(
            owner, f"allocation {allocation_name!r} owner", allow_empty=True
        )
        allocation_purpose = _text(
            purpose, f"allocation {allocation_name!r} purpose", allow_empty=True
        )
        if content_sha256:
            if not isinstance(content_sha256, str) or not _SHA256_RE.fullmatch(
                content_sha256
            ):
                raise RomAllocationError(
                    f"allocation {allocation_name!r} content_sha256 must be 64 hex digits"
                )
            digest = content_sha256.lower()
        else:
            if not isinstance(content_sha256, str):
                raise RomAllocationError(
                    f"allocation {allocation_name!r} content_sha256 must be text"
                )
            digest = ""

        if start is None or start == "":
            allocation_start = self._first_fit(
                target, allocation_size, effective_alignment
            )
            placement = "FIRST_FIT"
        else:
            allocation_start = _integer(
                start, f"allocation {allocation_name!r} start"
            )
            placement = "EXPLICIT"
        allocation_end = allocation_start + allocation_size
        if allocation_start % effective_alignment:
            raise RomAllocationError(
                f"allocation {allocation_name!r} start is not aligned to "
                f"{effective_alignment}"
            )
        if not target.start <= allocation_start < allocation_end <= target.end_exclusive:
            raise RomAllocationError(
                f"allocation {allocation_name!r} is outside region {region_name!r}"
            )
        for occupied in self._occupied(region_name):
            if (
                allocation_start < occupied.end_exclusive
                and occupied.start < allocation_end
            ):
                raise RomAllocationError(
                    f"allocation overlap: {allocation_name!r} and {occupied.name!r}"
                )

        allocation = RomAllocation(
            name=allocation_name,
            region=region_name,
            start=allocation_start,
            end_exclusive=allocation_end,
            size=allocation_size,
            alignment=effective_alignment,
            placement=placement,
            owner=allocation_owner,
            purpose=allocation_purpose,
            content_sha256=digest,
            sequence=len(self._allocations),
        )
        self._allocations.append(allocation)
        self._allocation_names.add(allocation_name)
        return allocation

    def allocate_request(self, request: Mapping[str, object]) -> RomAllocation:
        """厳密なmetadata mappingを1件配置する。raw byte用keyは許可しない。"""

        if not isinstance(request, Mapping):
            raise RomAllocationError("allocation request must be an object")
        unknown = set(request) - REQUEST_FIELDS
        required = {"name", "region", "size"}
        missing = required - set(request)
        if unknown:
            raise RomAllocationError(
                f"allocation request has unknown fields: {sorted(map(str, unknown))}"
            )
        if missing:
            raise RomAllocationError(
                f"allocation request is missing fields: {sorted(missing)}"
            )
        return self.allocate(
            name=request["name"],  # type: ignore[arg-type]
            region=request["region"],  # type: ignore[arg-type]
            size=request["size"],  # type: ignore[arg-type]
            alignment=request.get("alignment"),  # type: ignore[arg-type]
            start=request.get("start"),  # type: ignore[arg-type]
            owner=request.get("owner", ""),  # type: ignore[arg-type]
            purpose=request.get("purpose", ""),  # type: ignore[arg-type]
            content_sha256=request.get("content_sha256", ""),  # type: ignore[arg-type]
        )

    def allocate_many(
        self, requests: Iterable[Mapping[str, object]]
    ) -> tuple[RomAllocation, ...]:
        """入力sequence順に配置し、その順をreportへ固定する。"""

        allocated: list[RomAllocation] = []
        for request in requests:
            allocated.append(self.allocate_request(request))
        return tuple(allocated)

    def report(self) -> dict[str, Any]:
        """raw bytesやtimestampを含まない、決定的なmachine-readable report。"""

        regions = [region.to_report() for region in self._regions]
        allocations = [item.to_report() for item in self._allocations]
        allocatable = [region for region in self._regions if region.kind == "allocatable"]
        reserved = [region for region in self._regions if region.kind == "reserved"]
        usage = []
        for region in self._regions:
            allocated_bytes = sum(
                item.size for item in self._allocations if item.region == region.name
            )
            usage.append(
                {
                    "region": region.name,
                    "kind": region.kind,
                    "size": region.size,
                    "allocated_bytes": allocated_bytes,
                    "remaining_bytes": (
                        region.size - allocated_bytes
                        if region.kind == "allocatable"
                        else 0
                    ),
                    "allocation_count": sum(
                        item.region == region.name for item in self._allocations
                    ),
                }
            )
        allocated_total = sum(item.size for item in self._allocations)
        allocatable_total = sum(region.size for region in allocatable)
        return {
            "schema_version": SCHEMA_VERSION,
            "regions": regions,
            "allocations": allocations,
            "summaries": {
                "rom_size": ROM_SIZE,
                "gba_rom_base": GBA_ROM_BASE,
                "region_count": len(self._regions),
                "allocatable_region_count": len(allocatable),
                "reserved_region_count": len(reserved),
                "region_bytes": sum(region.size for region in self._regions),
                "allocatable_bytes": allocatable_total,
                "reserved_bytes": sum(region.size for region in reserved),
                "allocation_count": len(self._allocations),
                "allocated_bytes": allocated_total,
                "remaining_allocatable_bytes": allocatable_total - allocated_total,
                "overlap_count": 0,
                "region_usage": usage,
            },
        }


def build_allocation_report(
    regions: Iterable[RomRegion], requests: Iterable[Mapping[str, object]]
) -> dict[str, Any]:
    """公開pure API: regionとrequestから決定的reportを構築する。"""

    allocator = RomAllocator(regions)
    allocator.allocate_many(requests)
    return allocator.report()


def build_allocation_report_from_csv(
    region_csv: Path, requests: Iterable[Mapping[str, object]]
) -> dict[str, Any]:
    """公開CSV API: ``config/rom_regions.csv`` とrequestからreportを構築する。"""

    return build_allocation_report(load_regions_csv(region_csv), requests)


def _load_requests(path: Path) -> list[Mapping[str, object]]:
    if path.is_symlink() or not path.is_file():
        raise RomAllocationError(
            f"allocation request JSON must be a regular non-symlink file: {path}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        if set(payload) != {"allocations"}:
            raise RomAllocationError(
                "request JSON object must contain only the allocations key"
            )
        payload = payload["allocations"]
    if not isinstance(payload, list):
        raise RomAllocationError("request JSON must be a list or {allocations: [...]} object")
    if not all(isinstance(item, Mapping) for item in payload):
        raise RomAllocationError("every allocation request must be an object")
    return payload


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regions", type=Path, required=True)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        help="report JSON path; omitted means sanitized metadata JSON on stdout",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        requests = _load_requests(args.requests)
        report = build_allocation_report_from_csv(args.regions, requests)
        if args.output is None:
            print(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        else:
            _write_json(args.output, report)
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "allocation_count": report["summaries"]["allocation_count"],
                        "overlap_count": report["summaries"]["overlap_count"],
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
