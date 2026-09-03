#!/usr/bin/env python3
"""NPC配置の可変owner集合とobject操作targetをfail-closedで解決する。"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping, Sequence


class NpcPlacementIntegrityError(RuntimeError):
    """配置ポリシーの入力またはowner対応が曖昧な場合の例外。"""


TRAINER_ADDITION_KINDS = frozenset({"NORMAL", "ARCHIVE", "RELOCATED"})
EVENT_DESIGN_ADDITION_KINDS = frozenset({
    "ALLOCATED_SAFE_OBJECT",
    "RESTORED_OBJECT_RELOCATED",
})

# *_AT commandはlocal IDの後ろに対象map group/mapを持つ。通常commandは
# 実行rootと同じphysical mapを対象とする。dynamic local IDは静的ownerへ
# 帰属させない。
LOCAL_OBJECT_AT_OPCODES = frozenset({0x50, 0x52, 0x54, 0x56, 0x58, 0x59})
LOCAL_OBJECT_AT_SHORT_OPCODES = frozenset({0x52, 0x54, 0x56, 0x58, 0x59})
LOCAL_OBJECT_SUBPRIORITY_AT_OPCODES = frozenset({0xA8, 0xA9})


def object_owner_id(group: int, map_number: int, object_index: int) -> str:
    return f"OBJECT:{group:03d}/{map_number:03d}:{object_index:03d}"


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        raise NpcPlacementIntegrityError(f"{label}が整数ではありません")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise NpcPlacementIntegrityError(
            f"{label}が整数ではありません: {value!r}"
        ) from exc


def _rows(value: Any, label: str) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        values = list(value.values())
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values = list(value)
    else:
        raise NpcPlacementIntegrityError(f"{label}がrow集合ではありません")
    if any(not isinstance(row, Mapping) for row in values):
        raise NpcPlacementIntegrityError(f"{label}にmapping以外があります")
    return values


def build_explicit_added_owner_manifest(
    npc_rows: Iterable[Mapping[str, Any]],
    trainer_plan: Mapping[str, Any],
    post_ledger_owners: Any,
    event_design_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """明示的な生成記録だけから自動配置可能ownerを構成する。"""

    by_local: dict[tuple[int, int, int], str] = {}
    known_ids: set[str] = set()
    for index, row in enumerate(npc_rows):
        try:
            group = _integer(row["group"], f"npc_rows[{index}].group")
            number = _integer(row["map"], f"npc_rows[{index}].map")
            local_id = _integer(row["local_id"], f"npc_rows[{index}].local_id")
            object_index = _integer(
                row["object_index"], f"npc_rows[{index}].object_index"
            )
        except KeyError as exc:
            raise NpcPlacementIntegrityError(
                f"npc_rows[{index}] identity不足: {exc}"
            ) from exc
        owner_id = str(row.get(
            "npc_id", object_owner_id(group, number, object_index),
        ))
        expected_id = object_owner_id(group, number, object_index)
        if owner_id != expected_id:
            raise NpcPlacementIntegrityError(
                f"NPC owner ID不一致: {owner_id} != {expected_id}"
            )
        key = (group, number, local_id)
        if key in by_local or owner_id in known_ids:
            raise NpcPlacementIntegrityError(
                f"NPC local/owner identity重複: {key}/{owner_id}"
            )
        by_local[key] = owner_id
        known_ids.add(owner_id)

    origins: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def bind_local(
        group: Any, number: Any, local_id: Any, *,
        source: str, detail: Mapping[str, Any],
    ) -> None:
        key = (
            _integer(group, f"{source}.group"),
            _integer(number, f"{source}.map"),
            _integer(local_id, f"{source}.local_id"),
        )
        owner_id = by_local.get(key)
        if owner_id is None:
            raise NpcPlacementIntegrityError(
                f"明示追加local IDをfinal ownerへ解決できません: {source} {key}"
            )
        origins[owner_id].append({"source": source, **dict(detail)})

    maps = trainer_plan.get("maps")
    if not isinstance(maps, list):
        raise NpcPlacementIntegrityError("trainer plan mapsがlistではありません")
    trainer_row_count = 0
    for map_index, map_row in enumerate(maps):
        if not isinstance(map_row, Mapping):
            raise NpcPlacementIntegrityError(
                f"trainer plan maps[{map_index}]がmappingではありません"
            )
        additions = map_row.get("new_objects", [])
        if not isinstance(additions, list):
            raise NpcPlacementIntegrityError(
                f"trainer plan maps[{map_index}].new_objectsがlistではありません"
            )
        for object_index, addition in enumerate(additions):
            if not isinstance(addition, Mapping):
                raise NpcPlacementIntegrityError("trainer new object schema不正")
            owner_kind = str(addition.get("owner_kind"))
            if owner_kind not in TRAINER_ADDITION_KINDS:
                raise NpcPlacementIntegrityError(
                    f"trainer new object owner kind不正: {owner_kind}"
                )
            bind_local(
                map_row.get("group_id"), map_row.get("map_id"),
                addition.get("local_id"),
                source="TRAINER_PLAN_NEW_OBJECT",
                detail={
                    "map_row": map_index,
                    "new_object_row": object_index,
                    "owner_kind": owner_kind,
                    "encounter_key": addition.get("encounter_key"),
                },
            )
            trainer_row_count += 1

    post_rows = _rows(post_ledger_owners, "post-ledger owners")
    for index, row in enumerate(post_rows):
        bind_local(
            row.get("group"), row.get("map"), row.get("local_id"),
            source="STAGE58_POST_LEDGER_ADDITION",
            detail={"row": index, "role": row.get("role")},
        )

    event_row_count = 0
    for index, row in enumerate(event_design_rows):
        kind = str(row.get("stage37_binding_kind", ""))
        if kind not in EVENT_DESIGN_ADDITION_KINDS:
            continue
        bind_local(
            row.get("group_id"), row.get("map_id"), row.get("local_id"),
            source="STAGE37_EVENT_DESIGN_ADDITION",
            detail={
                "row": index,
                "stage37_binding_kind": kind,
                "placement_key": row.get("placement_key"),
            },
        )
        event_row_count += 1

    owner_rows = [
        {"owner_id": owner_id, "origins": sorted(
            rows, key=lambda row: (str(row["source"]), str(row)),
        )}
        for owner_id, rows in sorted(origins.items())
    ]
    if not owner_rows:
        raise NpcPlacementIntegrityError("明示追加owner集合が空です")
    return {
        "schema_version": 1,
        "status": "PASS",
        "policy": "EXPLICIT_PROJECT_ADDITION_MANIFEST_UNION_ONLY",
        "owner_count": len(owner_rows),
        "origin_row_counts": {
            "trainer_plan_new_objects": trainer_row_count,
            "stage58_post_ledger_additions": len(post_rows),
            "stage37_event_design_additions": event_row_count,
        },
        "owner_ids": [row["owner_id"] for row in owner_rows],
        "owners": owner_rows,
        "assertions": {
            "all_origins_resolve_to_unique_final_owner": True,
            "no_role_or_provenance_guess_used": True,
            "source_existing_objects_are_not_implicitly_mutable": True,
        },
    }


def decode_local_object_target(
    opcode: int,
    raw: bytes,
    source_group: int,
    source_map: int,
) -> dict[str, Any]:
    """object bytecodeの対象を(group,map,local ID)へ厳密に復号する。"""

    if len(raw) < 3:
        raise NpcPlacementIntegrityError(
            f"object commandがlocal IDを含みません: opcode=0x{opcode:02X}"
        )
    local_id = int.from_bytes(raw[1:3], "little")
    dynamic = local_id >= 0x4000
    if opcode == 0x50:
        if len(raw) < 9:
            raise NpcPlacementIntegrityError("APPLY_MOVEMENT_AT length不正")
        target_group, target_map = raw[7], raw[8]
    elif opcode in LOCAL_OBJECT_AT_SHORT_OPCODES \
            or opcode in LOCAL_OBJECT_SUBPRIORITY_AT_OPCODES:
        if len(raw) < 5:
            raise NpcPlacementIntegrityError(
                f"*_AT object command length不正: opcode=0x{opcode:02X}"
            )
        target_group, target_map = raw[3], raw[4]
    else:
        target_group, target_map = source_group, source_map
    return {
        "local_id": local_id,
        "target_group": int(target_group),
        "target_map": int(target_map),
        "dynamic_local_id": dynamic,
        "target_is_explicit_map": opcode in LOCAL_OBJECT_AT_OPCODES
            or opcode in LOCAL_OBJECT_SUBPRIORITY_AT_OPCODES,
    }


__all__ = [
    "EVENT_DESIGN_ADDITION_KINDS",
    "LOCAL_OBJECT_AT_OPCODES",
    "LOCAL_OBJECT_SUBPRIORITY_AT_OPCODES",
    "NpcPlacementIntegrityError",
    "TRAINER_ADDITION_KINDS",
    "build_explicit_added_owner_manifest",
    "decode_local_object_target",
    "object_owner_id",
]
