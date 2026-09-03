#!/usr/bin/env python3
"""Stage61の誤ったNPC自動配置だけを復元し、追加NPCだけを再配置する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_stage61_display_npc_event_audit import (  # noqa: E402
    GBA_BASE,
    POSITION_ANCHORED_OBJECT_OPERATIONS,
    _block_elevation,
    _collision_zero,
    _decode_event_tiles,
    _external_movement_footprint,
    _global_local_object_operation_index,
    _map_geometry,
    _rom_offset,
    _stage_map_state,
)
from tools.npc_placement_integrity import (  # noqa: E402
    NpcPlacementIntegrityError,
    build_explicit_added_owner_manifest,
    object_owner_id,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.trainer_final.kanto_events import _object_fields  # noqa: E402


TASK = "USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT"
STAGE = 62
ROM_SIZE = 32 * 1024 * 1024
DEFAULT_CONFIG = Path("config/stage62_npc_placement_integrity_repair.json")
OBJECT_SIZE = 24
PLACEMENT_SLICE = slice(4, 11)
FACING_FOR_PORT = {
    (0, -1): 0x07,
    (0, 1): 0x08,
    (-1, 0): 0x09,
    (1, 0): 0x0A,
}
FACING_VECTOR = {value: key for key, value in FACING_FOR_PORT.items()}
WISDOM_FIXTURES = (
    "wisdom_cave_north_route",
    "wisdom_cave_south_route",
    "wisdom_cave_b2f_route",
    "wisdom_cave_b1f",
    "wisdom_cave_b2f",
)
WISDOM_STORY_FIXTURE = "wisdom_cave_story"
WISDOM_ALL_FIXTURES = WISDOM_FIXTURES + (WISDOM_STORY_FIXTURE,)


class Stage62BuildError(RuntimeError):
    """NPC配置復元または安全配置監査が成立しない。"""


def _fail(message: str) -> NoReturn:
    raise Stage62BuildError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _identity(contract: Mapping[str, Any], label: str) -> bytes:
    path = ROOT / str(contract.get("path", ""))
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _fail(f"{label}を読めません: {path}: {exc}")
    if "size" in contract and len(raw) != int(contract["size"]):
        _fail(f"{label} size不一致: {len(raw)} != {contract['size']}")
    if _sha(raw) != str(contract.get("sha256")):
        _fail(f"{label} SHA-256不一致: {path}")
    return raw


def _load_config(path: Path) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"config読込失敗: {exc}")
    if not isinstance(value, dict) or (
        value.get("schema_version"), value.get("task"), value.get("stage")
    ) != (1, TASK, STAGE):
        _fail("config schema/task/stage不一致")
    if not isinstance(value.get("inputs"), dict) \
            or not isinstance(value.get("outputs"), dict):
        _fail("config inputs/outputs不正")
    return value


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail(f"{label} JSON不正: {exc}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _physical_coordinates(map_catalog: Mapping[str, Any]) -> list[tuple[int, int, str]]:
    rows = map_catalog.get("maps")
    if not isinstance(rows, list):
        _fail("Stage61 map catalog maps不正")
    result: list[tuple[int, int, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            _fail("Stage61 map catalog row不正")
        group, number = int(row["group"]), int(row["map"])
        # base 425 mapの数値座標はVegaのphysical identityである。旧reportの
        # FireRed名は表示上の誤分類なので、新証跡へ伝播させない。
        key = (
            f"VEGA_STOCK:{group:03d}/{number:03d}"
            if group < 96 else str(row["map_key"])
        )
        result.append((group, number, key))
    result.sort()
    if len(result) != 678 \
            or len({(g, m) for g, m, _ in result}) != 678:
        _fail(f"physical map 678件契約不一致: {len(result)}")
    if (1, 73, "VEGA_STOCK:001/073") not in result:
        _fail("1/73がVega physical mapへ固定されていません")
    return result


def _all_objects(
    rom: bytes, coords: Sequence[tuple[int, int, str]],
) -> tuple[list[dict[str, Any]], dict[str, tuple[int, bytes, dict[str, int]]]]:
    rows: list[dict[str, Any]] = []
    by_id: dict[str, tuple[int, bytes, dict[str, int]]] = {}
    for group, number, map_key in coords:
        try:
            state = _stage_map_state(rom, group, number)
        except RuntimeError:
            continue
        count = len(state["objects"])
        if not count:
            continue
        array = _rom_offset(
            int(state["pointers"]["objects"]), count * OBJECT_SIZE,
            f"object array {group}/{number}",
        )
        local_ids: set[int] = set()
        for index, raw in enumerate(state["objects"]):
            fields = _object_fields(raw)
            local_id = int(fields["local_id"])
            if local_id in local_ids:
                _fail(f"object local ID重複: {group}/{number} local={local_id}")
            local_ids.add(local_id)
            owner_id = object_owner_id(group, number, index)
            row = {
                "npc_id": owner_id,
                "group": group,
                "map": number,
                "map_key": map_key,
                "object_index": index,
                "local_id": local_id,
                **fields,
                "movement_range_x": raw[10] & 0xF,
                "movement_range_y": raw[10] >> 4,
                "record_address": f"0x{GBA_BASE + array + index * OBJECT_SIZE:08X}",
                "record_raw_hex": raw.hex(),
            }
            rows.append(row)
            by_id[owner_id] = (array + index * OBJECT_SIZE, raw, fields)
    if len(rows) != 3112 or len(by_id) != len(rows):
        _fail(f"final object owner cardinality不一致: {len(rows)}")
    return rows, by_id


def _added_manifest(
    npc_catalog: Mapping[str, Any], trainer_plan: Mapping[str, Any],
    post_ledger: Mapping[str, Any], event_design_raw: bytes,
) -> dict[str, Any]:
    try:
        event_rows = list(csv.DictReader(
            event_design_raw.decode("utf-8").splitlines()
        ))
        result = build_explicit_added_owner_manifest(
            npc_catalog["npcs"], trainer_plan,
            post_ledger["owners"], event_rows,
        )
    except (KeyError, TypeError, UnicodeDecodeError,
            NpcPlacementIntegrityError) as exc:
        _fail(f"明示追加NPC manifest不正: {exc}")
    expected = {
        "trainer_plan_new_objects": 269,
        "stage58_post_ledger_additions": 9,
        "stage37_event_design_additions": 4,
    }
    if result.get("owner_count") != 282 \
            or result.get("origin_row_counts") != expected:
        _fail(
            "明示追加NPC 282件契約不一致: "
            f"{result.get('owner_count')}/{result.get('origin_row_counts')}"
        )
    return result


def _restore_immutable_placement(
    stage61: bytes, placement_audit: Mapping[str, Any],
    mutable_ids: set[str], object_sites: Mapping[
        str, tuple[int, bytes, dict[str, int]]
    ],
) -> tuple[bytearray, dict[str, Any], dict[str, bytes]]:
    output = bytearray(stage61)
    manual = placement_audit.get("manual_placement_repairs")
    if not isinstance(manual, Mapping) \
            or not isinstance(manual.get("repairs"), list):
        _fail("Stage61 placement repair report不正")
    immutable_authority = {
        owner_id: raw[PLACEMENT_SLICE]
        for owner_id, (_site, raw, _fields) in object_sites.items()
        if owner_id not in mutable_ids
    }
    restored: list[dict[str, Any]] = []
    retained_added: list[dict[str, Any]] = []
    field_counts: Counter[str] = Counter()
    applied_count = 0
    runtime_restored: list[dict[str, Any]] = []
    for row in manual["repairs"]:
        if not isinstance(row, Mapping):
            _fail("Stage61 placement repair row不正")
        owner_id = str(row["npc_id"])
        if owner_id not in object_sites:
            _fail(f"placement repair owner不在: {owner_id}")
        record_site, raw, fields = object_sites[owner_id]
        expected = bytes.fromhex(str(row["expected_hex"]))
        replacement = bytes.fromhex(str(row["replacement_hex"]))
        if len(expected) != 7 or len(replacement) != 7:
            _fail(f"placement repair byte長不正: {owner_id}")
        patch_site = int(str(row["patch_address"]), 16) - GBA_BASE
        if patch_site != record_site + 4:
            _fail(
                f"placement patch address/owner不一致: {owner_id} "
                f"{patch_site:#x}!={record_site + 4:#x}"
            )
        if bool(row["patch_applied"]):
            applied_count += 1
            if bytes(output[patch_site:patch_site + 7]) != replacement:
                _fail(f"Stage61 placement replacement preimage不一致: {owner_id}")
            if owner_id in mutable_ids:
                retained_added.append({
                    "npc_id": owner_id,
                    "map": list(map(int, row["map"])),
                    "local_id": int(row["local_id"]),
                    "stage61_hex": replacement.hex(),
                    "source_hex": expected.hex(),
                    "reason": "EXPLICIT_PROJECT_ADDITION_MAY_BE_REEVALUATED",
                })
            else:
                output[patch_site:patch_site + 7] = expected
                immutable_authority[owner_id] = expected
                before = _placement_fields(replacement)
                after = _placement_fields(expected)
                for field in after:
                    if before[field] != after[field]:
                        field_counts[field] += 1
                restored.append({
                    "npc_id": owner_id,
                    "map": list(map(int, row["map"])),
                    "object_index": int(row["object_index"]),
                    "local_id": int(row["local_id"]),
                    "patch_address": str(row["patch_address"]),
                    "stage61": before,
                    "restored": after,
                    "stage61_hex": replacement.hex(),
                    "restored_hex": expected.hex(),
                    "source_authority": (
                        "PINNED_VEGA_REFERENCE" if int(row["map"][0]) < 96
                        else "PINNED_CLEAN_FIRERED_CANONICAL_IMPORT"
                    ),
                })
        for runtime in row.get("runtime_position_patches", []):
            if owner_id in mutable_ids:
                _fail(f"追加NPC runtime座標patchは想定外です: {owner_id}")
            site = int(str(runtime["operand_address"]), 16) - GBA_BASE
            expected_runtime = bytes.fromhex(str(runtime["expected_hex"]))
            replacement_runtime = bytes.fromhex(str(runtime["replacement_hex"]))
            if bytes(output[site:site + 4]) != replacement_runtime:
                _fail(f"runtime placement preimage不一致: {owner_id}")
            output[site:site + 4] = expected_runtime
            runtime_restored.append({
                "npc_id": owner_id,
                "instruction_address": str(runtime["instruction_address"]),
                "operand_address": str(runtime["operand_address"]),
                "stage61_hex": replacement_runtime.hex(),
                "restored_hex": expected_runtime.hex(),
            })
    if applied_count != 356 or len(restored) != 316 \
            or len(retained_added) != 40 or len(runtime_restored) != 2:
        _fail(
            "Stage61誤配置復元件数drift: "
            f"applied={applied_count} immutable={len(restored)} "
            f"added={len(retained_added)} runtime={len(runtime_restored)}"
        )
    return output, {
        "schema_version": 1,
        "policy": "RESTORE_EVERY_NON_ADDED_STAGE61_PLACEMENT_PATCH",
        "stage61_applied_placement_patch_count": applied_count,
        "restored_non_added_npc_count": len(restored),
        "retained_added_npc_patch_count_before_safety_reallocation": len(
            retained_added
        ),
        "restored_runtime_position_operand_count": len(runtime_restored),
        "restored_field_counts": dict(sorted(field_counts.items())),
        "restored_non_added_npcs": restored,
        "retained_added_npcs": retained_added,
        "restored_runtime_position_operands": runtime_restored,
        "assertions": {
            "all_applied_stage61_placement_rows_classified": True,
            "all_non_added_rows_restored": True,
            "script_pointer_bytes_not_part_of_placement_slice": True,
            "trainer_type_and_sight_bytes_not_rewritten": True,
        },
    }, immutable_authority


def _placement_fields(raw: bytes) -> dict[str, int]:
    if len(raw) != 7:
        _fail("placement slice length不正")
    return {
        "x": struct.unpack_from("<h", raw, 0)[0],
        "y": struct.unpack_from("<h", raw, 2)[0],
        "elevation": raw[4],
        "movement_type": raw[5],
        "movement_range_x": raw[6] & 0xF,
        "movement_range_y": raw[6] >> 4,
    }


def _entry_seed_index(
    placement_audit: Mapping[str, Any],
) -> tuple[dict[tuple[int, int], set[tuple[int, int]]], dict[tuple[int, int], Mapping[str, Any]]]:
    map_rows = placement_audit.get("maps")
    if not isinstance(map_rows, list):
        _fail("Stage61 placement maps不正")
    result: dict[tuple[int, int], set[tuple[int, int]]] = {}
    reports: dict[tuple[int, int], Mapping[str, Any]] = {}
    for row in map_rows:
        if not isinstance(row, Mapping):
            _fail("Stage61 placement map row不正")
        key = (int(row["group"]), int(row["map"]))
        entry = row.get("entry")
        if not isinstance(entry, Mapping):
            _fail(f"entry report不正: {key}")
        seeds: set[tuple[int, int]] = set()
        for incoming in entry.get("incoming_warps", []):
            if incoming.get("source_trigger_usable") \
                    and incoming.get("in_bounds"):
                seeds.add(tuple(map(int, incoming["arrival_tile"])))
        for connection in entry.get("connections", []):
            seeds.update(
                tuple(map(int, point))
                for point in connection.get("arrival_tiles", [])
            )
        for producer in entry.get("scripted_entries", []):
            if producer.get("in_bounds") and producer.get("arrival_tile"):
                seeds.add(tuple(map(int, producer["arrival_tile"])))
        for producer in entry.get("engine_entries", []):
            if producer.get("in_bounds") and producer.get("arrival_tile"):
                seeds.add(tuple(map(int, producer["arrival_tile"])))
        if len(seeds) != int(entry.get("seed_count", -1)):
            _fail(
                f"entry seed再構成件数不一致: {key} "
                f"{len(seeds)}/{entry.get('seed_count')}"
            )
        result[key] = seeds
        reports[key] = row
    return result, reports


def _reachable(
    geometry: Mapping[str, Any], seeds: Iterable[tuple[int, int]],
    blocked: set[tuple[int, int]],
) -> dict[tuple[int, int], int]:
    reached = {
        point: 0 for point in seeds
        if point not in blocked
        and 0 <= point[0] < int(geometry["width"])
        and 0 <= point[1] < int(geometry["height"])
    }
    pending = deque(sorted(reached, key=lambda p: (p[1], p[0])))
    while pending:
        x, y = pending.popleft()
        for point in ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)):
            if point in reached or point in blocked \
                    or not _collision_zero(geometry, point):
                continue
            reached[point] = reached[(x, y)] + 1
            pending.append(point)
    return reached


def _ports(
    geometry: Mapping[str, Any], point: tuple[int, int],
    reached: Mapping[tuple[int, int], int], reserved: set[tuple[int, int]],
    blockers: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    elevation = _block_elevation(geometry, point)
    return [
        port for port in (
            (point[0], point[1] - 1),
            (point[0] - 1, point[1]),
            (point[0] + 1, point[1]),
            (point[0], point[1] + 1),
        )
        if port in reached and port not in reserved and port not in blockers
        and _block_elevation(geometry, port) == elevation
    ]


def _trainer_ray_safe(
    geometry: Mapping[str, Any], point: tuple[int, int], movement_type: int,
    sight_range: int, reserved: set[tuple[int, int]],
    entry_seeds: set[tuple[int, int]], fixed: set[tuple[int, int]],
) -> tuple[bool, list[list[int]]]:
    if sight_range == 0:
        return True, []
    vector = FACING_VECTOR.get(movement_type)
    if vector is None:
        return False, []
    ray: list[list[int]] = []
    elevation = _block_elevation(geometry, point)
    for distance in range(1, sight_range + 1):
        target = (
            point[0] + vector[0] * distance,
            point[1] + vector[1] * distance,
        )
        if not _collision_zero(geometry, target) \
                or _block_elevation(geometry, target) != elevation:
            break
        if target in fixed:
            break
        ray.append(list(target))
        if target in reserved or target in entry_seeds:
            return False, ray
    return True, ray


def _map_unsafe_reasons(
    rom: bytes, group: int, number: int, additions: set[str],
    anchors: set[str], seeds: set[tuple[int, int]],
) -> tuple[list[str], dict[str, Any]]:
    state = _stage_map_state(rom, group, number)
    geometry = _map_geometry(rom, group, number)
    _warps, reserved = _decode_event_tiles(state)
    decoded = [_object_fields(raw) for raw in state["objects"]]
    rows = [
        (object_owner_id(group, number, index), row)
        for index, row in enumerate(decoded)
    ]
    fixed = {
        (int(row["x"]), int(row["y"]))
        for owner_id, row in rows
        if owner_id not in additions or owner_id in anchors
    }
    movable = {
        (int(row["x"]), int(row["y"]))
        for owner_id, row in rows
        if owner_id in additions and owner_id not in anchors
    }
    all_points = [(int(row["x"]), int(row["y"])) for _owner, row in rows]
    duplicates = {
        point for point, count in Counter(all_points).items() if count > 1
    }
    reasons: set[str] = set()
    base_reached = _reachable(geometry, seeds, fixed)
    final_blockers = set(all_points)
    final_reached = _reachable(geometry, seeds, final_blockers)
    lost = set(base_reached) - set(final_reached)
    if lost - movable:
        reasons.add("PASSAGE_COMPONENT_LOSS")
    owner_rows: list[dict[str, Any]] = []
    for owner_id, row in rows:
        if owner_id not in additions:
            continue
        point = (int(row["x"]), int(row["y"]))
        collision = _collision_zero(geometry, point)
        elevation_match = collision and (
            int(row["elevation"]) in {0, _block_elevation(geometry, point)}
        )
        owner_reasons: list[str] = []
        if not collision:
            owner_reasons.append("OBJECT_COLLISION_NONZERO")
        if point in reserved:
            owner_reasons.append("OBJECT_ON_WARP_COORD_BG")
        if point in duplicates:
            owner_reasons.append("DUPLICATE_OBJECT_TILE")
        if not elevation_match:
            owner_reasons.append("OBJECT_ELEVATION_MISMATCH")
        available_ports = _ports(
            geometry, point, final_reached, reserved,
            final_blockers - {point},
        ) if collision else []
        if owner_id not in anchors and not available_ports:
            owner_reasons.append("NO_REACHABLE_INTERACTION_PORT")
        reasons.update(owner_reasons)
        owner_rows.append({
            "npc_id": owner_id,
            "local_id": int(row["local_id"]),
            "object": list(point),
            "position_anchored": owner_id in anchors,
            "reachable_ports": [list(port) for port in available_ports],
            "reasons": owner_reasons,
        })
    return sorted(reasons), {
        "map": [group, number],
        "entry_seed_count": len(seeds),
        "reserved_event_tile_count": len(reserved),
        "fixed_blocker_count": len(fixed),
        "movable_added_tile_count": len(movable),
        "baseline_reachable_tile_count": len(base_reached),
        "final_reachable_tile_count": len(final_reached),
        "unexplained_lost_reachable_tile_count": len(lost - movable),
        "duplicate_tile_count": len(duplicates),
        "reasons": sorted(reasons),
        "added_objects": owner_rows,
    }


def _allocate_unsafe_maps(
    output: bytearray, coords: Sequence[tuple[int, int, str]],
    mutable_ids: set[str], anchors: set[str],
    seeds_by_map: Mapping[tuple[int, int], set[tuple[int, int]]],
    unsafe_maps: Sequence[tuple[int, int]],
) -> tuple[list[dict[str, Any]], int]:
    moved_rows: list[dict[str, Any]] = []
    backtracks = 0
    for group, number in sorted(unsafe_maps):
        current = bytes(output)
        state = _stage_map_state(current, group, number)
        geometry = _map_geometry(current, group, number)
        _warps, reserved = _decode_event_tiles(state)
        seeds = set(seeds_by_map.get((group, number), set()))
        if not seeds:
            _fail(f"追加NPC mapにexact entry seedがありません: {group}/{number}")
        decoded = [_object_fields(raw) for raw in state["objects"]]
        array = _rom_offset(
            int(state["pointers"]["objects"]),
            len(decoded) * OBJECT_SIZE, f"object array {group}/{number}",
        )
        targets = [
            (object_owner_id(group, number, index), index, row)
            for index, row in enumerate(decoded)
            if object_owner_id(group, number, index) in mutable_ids
            and object_owner_id(group, number, index) not in anchors
        ]
        if not targets:
            _fail(f"unsafe mapに再配置可能な追加NPCがありません: {group}/{number}")
        fixed = {
            (int(row["x"]), int(row["y"]))
            for index, row in enumerate(decoded)
            if object_owner_id(group, number, index) not in {
                owner_id for owner_id, _i, _row in targets
            }
        }
        base_reached = _reachable(geometry, seeds, fixed)
        if not base_reached:
            _fail(f"追加NPC除外後も入口componentが空です: {group}/{number}")
        candidate_sets: list[tuple[str, int, dict[str, int], list[dict[str, Any]]]] = []
        width, height = int(geometry["width"]), int(geometry["height"])
        for owner_id, index, fields in sorted(targets):
            origin = (int(fields["x"]), int(fields["y"]))
            candidates: list[dict[str, Any]] = []
            rejections: Counter[str] = Counter()
            for y in range(height):
                for x in range(width):
                    point = (x, y)
                    if not _collision_zero(geometry, point) \
                            or point in reserved or point in fixed:
                        rejections["OBJECT_TILE"] += 1
                        continue
                    for order, port in enumerate((
                        (x, y - 1), (x - 1, y),
                        (x + 1, y), (x, y + 1),
                    )):
                        if port not in base_reached \
                                or port in reserved or port in fixed:
                            rejections["PORT"] += 1
                            continue
                        if _block_elevation(geometry, port) \
                                != _block_elevation(geometry, point):
                            rejections["PORT_ELEVATION"] += 1
                            continue
                        movement = FACING_FOR_PORT[
                            (port[0] - x, port[1] - y)
                        ]
                        trainer_ok, ray = _trainer_ray_safe(
                            geometry, point, movement,
                            int(fields["sight_range"]), reserved,
                            seeds, fixed,
                        )
                        if int(fields["trainer_type"]) and not trainer_ok:
                            rejections["TRAINER_SIGHT"] += 1
                            continue
                        candidates.append({
                            "object": point,
                            "port": port,
                            "movement_type": movement,
                            "trainer_sight_ray": ray,
                            "distance_from_entry": base_reached[port],
                            "score": (
                                abs(x - origin[0]) + abs(y - origin[1]),
                                base_reached[port], y, x, order,
                            ),
                        })
            candidates.sort(key=lambda row: row["score"])
            # The deterministic nearest subset is ample for the current maps
            # and bounds fail-closed backtracking on future dense additions.
            candidates = candidates[:256]
            if not candidates:
                _fail(
                    f"追加NPCの安全配置候補なし: map={group}/{number} "
                    f"owner={owner_id} local={fields['local_id']} "
                    f"rejections={dict(rejections)}"
                )
            candidate_sets.append((owner_id, index, fields, candidates))
        candidate_sets.sort(key=lambda item: (len(item[3]), item[0]))
        selected_objects = set(fixed)
        selected_ports: set[tuple[int, int]] = set()
        assignments: dict[str, dict[str, Any]] = {}

        def search(position: int) -> bool:
            nonlocal backtracks
            if position == len(candidate_sets):
                final_reached = _reachable(geometry, seeds, selected_objects)
                if any(
                    tuple(row["port"]) not in final_reached
                    for row in assignments.values()
                ):
                    return False
                lost = set(base_reached) - set(final_reached)
                selected_target_tiles = {
                    tuple(row["object"]) for row in assignments.values()
                }
                return not (lost - selected_target_tiles)
            owner_id, _index, _fields, candidates = candidate_sets[position]
            for candidate in candidates:
                point = tuple(candidate["object"])
                port = tuple(candidate["port"])
                if point in selected_objects or point in selected_ports \
                        or port in selected_objects or port in selected_ports:
                    continue
                selected_objects.add(point)
                selected_ports.add(port)
                assignments[owner_id] = candidate
                reached = _reachable(geometry, seeds, selected_objects)
                viable = all(
                    tuple(row["port"]) in reached
                    for row in assignments.values()
                )
                if viable and search(position + 1):
                    return True
                assignments.pop(owner_id)
                selected_ports.remove(port)
                selected_objects.remove(point)
                backtracks += 1
            return False

        if not search(0):
            _fail(
                f"追加NPC合同配置解なし: map={group}/{number} "
                f"owners={[row[0] for row in candidate_sets]}"
            )
        final_reached = _reachable(geometry, seeds, selected_objects)
        for owner_id, index, fields, candidates in sorted(
            candidate_sets, key=lambda item: item[0]
        ):
            chosen = assignments[owner_id]
            point = tuple(chosen["object"])
            port = tuple(chosen["port"])
            site = array + index * OBJECT_SIZE + 4
            old = bytes(output[site:site + 7])
            old_fields = _placement_fields(old)
            moved = point != (int(fields["x"]), int(fields["y"]))
            if moved:
                new = struct.pack(
                    "<hhBBB", point[0], point[1],
                    _block_elevation(geometry, point),
                    int(chosen["movement_type"]), 0,
                )
                output[site:site + 7] = new
            else:
                new = old
            moved_rows.append({
                "npc_id": owner_id,
                "map": [group, number],
                "object_index": index,
                "local_id": int(fields["local_id"]),
                "patch_address": f"0x{GBA_BASE + site:08X}",
                "moved": moved,
                "stage61_after_immutable_restore": old_fields,
                "stage62": _placement_fields(new),
                "stage61_hex": old.hex(),
                "stage62_hex": new.hex(),
                "selected_port": list(port),
                "distance_from_entry": int(chosen["distance_from_entry"]),
                "candidate_count": len(candidates),
                "trainer_type_preserved": int(fields["trainer_type"]),
                "trainer_sight_preserved": int(fields["sight_range"]),
                "trainer_sight_ray": chosen["trainer_sight_ray"],
                "placement_mutability": "EXPLICIT_PROJECT_ADDITION",
            })
    return moved_rows, backtracks


def _anchored_movement_audit(
    rom: bytes, anchored_ids: set[str], operation_index: Mapping[
        str, Sequence[Mapping[str, Any]]
    ], object_sites: Mapping[str, tuple[int, bytes, dict[str, int]]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for owner_id in sorted(anchored_ids):
        _site, _raw, fields = object_sites[owner_id]
        group, number = map(int, owner_id[7:14].split("/"))
        geometry = _map_geometry(rom, group, number)
        footprint = _external_movement_footprint(operation_index[owner_id])
        origin = (int(fields["x"]), int(fields["y"]))
        translated = {
            (origin[0] + int(point[0]), origin[1] + int(point[1]))
            for point in footprint["conservative_independent_relative_tiles"]
        }
        translated.update(
            tuple(map(int, point))
            for point in footprint["absolute_runtime_tiles"]
        )
        invalid = [
            list(point) for point in sorted(translated)
            if not _collision_zero(geometry, point)
            or _block_elevation(geometry, point)
                != _block_elevation(geometry, origin)
        ]
        row = {
            "npc_id": owner_id,
            "map": [group, number],
            "local_id": int(fields["local_id"]),
            "template": list(origin),
            "operations": [
                str(item["operation"]) for item in operation_index[owner_id]
            ],
            "operation_evidence": list(operation_index[owner_id]),
            "movement_footprint": footprint,
            "translated_runtime_tiles": [list(point) for point in sorted(translated)],
            "invalid_runtime_tiles": invalid,
            "status": "PASS" if not invalid else "FAIL",
        }
        rows.append(row)
        if invalid:
            failures.append(row)
    if failures:
        _fail(f"script-controlled追加actor movement footprint不正: {failures}")
    return {
        "schema_version": 1,
        "status": "PASS",
        "anchored_added_owner_count": len(rows),
        "owners": rows,
        "assertions": {
            "every_referenced_added_owner_is_position_anchored": True,
            "all_movement_footprint_tiles_collision_zero": True,
            "all_movement_footprint_elevations_match": True,
        },
    }


def _final_safety_audit(
    rom: bytes, coords: Sequence[tuple[int, int, str]],
    mutable_ids: set[str], anchors: set[str],
    seeds_by_map: Mapping[tuple[int, int], set[tuple[int, int]]],
) -> dict[str, Any]:
    additions_by_map: dict[tuple[int, int], set[str]] = defaultdict(set)
    for owner_id in mutable_ids:
        group, number = map(int, owner_id[7:14].split("/"))
        additions_by_map[(group, number)].add(owner_id)
    map_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for key in sorted(additions_by_map):
        reasons, row = _map_unsafe_reasons(
            rom, key[0], key[1], additions_by_map[key], anchors,
            set(seeds_by_map.get(key, set())),
        )
        map_rows.append(row)
        if reasons:
            failures.append(row)
    if failures:
        _fail(
            "追加NPC最終安全監査FAIL: "
            + "; ".join(
                f"{row['map']}:{row['reasons']}" for row in failures
            )
        )
    return {
        "schema_version": 1,
        "status": "PASS",
        "physical_map_count": len(coords),
        "maps_with_added_npcs": len(map_rows),
        "added_npc_count": len(mutable_ids),
        "position_anchored_added_npc_count": len(anchors),
        "failures": [],
        "maps": map_rows,
        "assertions": {
            "all_678_physical_maps_inventoried": len(coords) == 678,
            "no_added_npc_on_collision": True,
            "no_added_npc_on_warp_coord_bg": True,
            "no_added_npc_duplicate_tile": True,
            "every_unanchored_added_npc_has_reachable_port": True,
            "no_added_npc_causes_passage_component_loss": True,
            "trainer_sight_does_not_capture_entry_or_event_tile": True,
        },
    }


def _vega_reference_audit(
    final_rom: bytes, stage60: bytes, vega: bytes,
) -> dict[str, Any]:
    groups = json.loads((
        ROOT / "vendor/upstream/pokefirered/data/maps/map_groups.json"
    ).read_text(encoding="utf-8"))
    coords = [
        (group, number)
        for group, group_name in enumerate(groups["group_order"])
        for number, _name in enumerate(groups[group_name])
    ]
    failures: list[dict[str, Any]] = []
    invalid: list[list[int]] = []
    count = 0
    for group, number in coords:
        try:
            source = _stage_map_state(vega, group, number)
            baseline = _stage_map_state(stage60, group, number)
            final = _stage_map_state(final_rom, group, number)
        except RuntimeError:
            invalid.append([group, number])
            continue
        if len(source["objects"]) != len(baseline["objects"]) \
                or len(source["objects"]) != len(final["objects"]):
            failures.append({
                "map": [group, number], "reason": "OBJECT_COUNT",
                "source": len(source["objects"]),
                "stage60": len(baseline["objects"]),
                "stage62": len(final["objects"]),
            })
            continue
        for index, (source_raw, baseline_raw, final_raw) in enumerate(zip(
            source["objects"], baseline["objects"], final["objects"],
        )):
            count += 1
            if source_raw[PLACEMENT_SLICE] != baseline_raw[PLACEMENT_SLICE] \
                    or source_raw[PLACEMENT_SLICE] != final_raw[PLACEMENT_SLICE]:
                failures.append({
                    "map": [group, number], "object_index": index,
                    "source_hex": source_raw[PLACEMENT_SLICE].hex(),
                    "stage60_hex": baseline_raw[PLACEMENT_SLICE].hex(),
                    "stage62_hex": final_raw[PLACEMENT_SLICE].hex(),
                })
    if len(coords) != 425 or count != 2042 or len(invalid) != 5 \
            or failures:
        _fail(
            f"Vega既存NPC source placement audit不一致: "
            f"objects={count} invalid={invalid} failures={failures[:3]}"
        )
    return {
        "status": "PASS",
        "source_rom_sha256": _sha(vega),
        "stage60_rom_sha256": _sha(stage60),
        "physical_map_count": len(coords),
        "valid_object_map_count": len(coords) - len(invalid),
        "normalized_empty_or_invalid_event_map_count": len(invalid),
        "object_count": count,
        "placement_mismatch_count": 0,
        "assertions": {
            "all_valid_vega_object_placements_match_pinned_reference": True,
            "stage60_and_stage62_both_match_source_placement": True,
            "numeric_map_identity_is_vega_not_firered": True,
        },
    }


def _immutable_contract_audit(
    stage61: bytes, final_rom: bytes, mutable_ids: set[str],
    authority: Mapping[str, bytes],
    coords: Sequence[tuple[int, int, str]],
) -> dict[str, Any]:
    _before_rows, before = _all_objects(stage61, coords)
    _after_rows, after = _all_objects(final_rom, coords)
    failures: list[dict[str, Any]] = []
    nonplacement_changes = 0
    mutable_changed = 0
    immutable_changed_from_stage61 = 0
    for owner_id in sorted(after):
        before_site, before_raw, _before_fields = before[owner_id]
        after_site, after_raw, _after_fields = after[owner_id]
        if before_site != after_site:
            _fail(f"object record siteが移動しました: {owner_id}")
        if before_raw[:4] + before_raw[11:] != after_raw[:4] + after_raw[11:]:
            nonplacement_changes += 1
            failures.append({
                "npc_id": owner_id,
                "reason": "NON_PLACEMENT_OBJECT_BYTES_CHANGED",
            })
        if owner_id in mutable_ids:
            mutable_changed += int(
                before_raw[PLACEMENT_SLICE] != after_raw[PLACEMENT_SLICE]
            )
            continue
        immutable_changed_from_stage61 += int(
            before_raw[PLACEMENT_SLICE] != after_raw[PLACEMENT_SLICE]
        )
        expected = authority.get(owner_id)
        if expected is None or after_raw[PLACEMENT_SLICE] != expected:
            failures.append({
                "npc_id": owner_id,
                "reason": "IMMUTABLE_AUTHORITY_MISMATCH",
                "expected_hex": expected.hex() if expected else None,
                "actual_hex": after_raw[PLACEMENT_SLICE].hex(),
            })
    if failures or nonplacement_changes or immutable_changed_from_stage61 != 316:
        _fail(
            "immutable placement contract不一致: "
            f"changed={immutable_changed_from_stage61} "
            f"nonplacement={nonplacement_changes} failures={failures[:3]}"
        )
    return {
        "status": "PASS",
        "object_owner_count": len(after),
        "explicit_added_owner_count": len(mutable_ids),
        "immutable_owner_count": len(after) - len(mutable_ids),
        "restored_immutable_owner_count": immutable_changed_from_stage61,
        "relocated_existing_npc_count": 0,
        "changed_added_owner_count_vs_stage61": mutable_changed,
        "changed_nonplacement_object_record_count": nonplacement_changes,
        "assertions": {
            "every_immutable_owner_matches_authoritative_preplacement_bytes": True,
            "all_object_script_pointers_preserved": True,
            "all_object_trainer_type_and_sight_fields_preserved": True,
            "only_explicit_additions_may_receive_new_placement": True,
        },
    }


def _wisdom_cave_audit(
    stage61: bytes, final_rom: bytes, stage60: bytes, vega: bytes,
    operation_index: Mapping[str, Sequence[Mapping[str, Any]]],
    object_sites: Mapping[str, tuple[int, bytes, dict[str, int]]],
) -> dict[str, Any]:
    states = {
        "vega": _stage_map_state(vega, 1, 73),
        "stage60": _stage_map_state(stage60, 1, 73),
        "stage61": _stage_map_state(stage61, 1, 73),
        "stage62": _stage_map_state(final_rom, 1, 73),
    }
    source_by_local = {
        int(_object_fields(raw)["local_id"]): (index, raw, _object_fields(raw))
        for index, raw in enumerate(states["vega"]["objects"])
    }
    final_by_local = {
        int(_object_fields(raw)["local_id"]): (index, raw, _object_fields(raw))
        for index, raw in enumerate(states["stage62"]["objects"])
    }
    current_by_local = {
        int(_object_fields(raw)["local_id"]): (index, raw, _object_fields(raw))
        for index, raw in enumerate(states["stage61"]["objects"])
    }
    restored_rows: list[dict[str, Any]] = []
    for local_id in sorted(source_by_local):
        source_index, source_raw, source = source_by_local[local_id]
        final_index, final_raw, final = final_by_local[local_id]
        _current_index, current_raw, current = current_by_local[local_id]
        if source_index != final_index \
                or final_raw[PLACEMENT_SLICE] != source_raw[PLACEMENT_SLICE]:
            _fail(f"ちえのどうくつsource placement不一致: local {local_id}")
        if current_raw[PLACEMENT_SLICE] != final_raw[PLACEMENT_SLICE]:
            restored_rows.append({
                "local_id": local_id,
                "object_index": final_index,
                "stage61": _placement_fields(current_raw[PLACEMENT_SLICE]),
                "stage62": _placement_fields(final_raw[PLACEMENT_SLICE]),
            })
        if current_raw[16:20] != final_raw[16:20] \
                or current_raw[12:16] != final_raw[12:16]:
            _fail(f"ちえのどうくつ script/trainer field drift: local {local_id}")
    local1_owner = object_owner_id(1, 73, final_by_local[1][0])
    evidence = list(operation_index.get(local1_owner, []))
    external = [row for row in evidence if row.get("external_to_owner")]
    operation_counts = Counter(str(row["operation"]) for row in external)
    if operation_counts.get("APPLY_MOVEMENT") != 5 \
            or operation_counts.get("REMOVE_OBJECT") != 1:
        _fail(f"1/73 local 1 external operation不一致: {operation_counts}")
    coords_raw = bytes.fromhex(str(states["stage62"]["coords_hex"]))
    if int(states["stage62"]["counts"]["coords"]) <= 9:
        _fail("1/73 COORD:9がありません")
    coord9 = coords_raw[9 * 16:10 * 16]
    coord_root = struct.unpack_from("<I", coord9, 12)[0]
    coord9_row = {
        "owner_id": "COORD:001/073:009",
        "x": struct.unpack_from("<H", coord9, 0)[0],
        "y": struct.unpack_from("<H", coord9, 2)[0],
        "elevation": coord9[4],
        "trigger_var": struct.unpack_from("<H", coord9, 6)[0],
        "trigger_value": struct.unpack_from("<H", coord9, 8)[0],
        "script_root": f"0x{coord_root:08X}",
        "record_raw_hex": coord9.hex(),
    }
    expected_highlights = {
        1: (4, 11, 3, 8, 1, 1),
        3: (6, 14, 3, 7, 1, 1),
        8: (19, 11, 3, 9, 1, 1),
    }
    highlights: list[dict[str, Any]] = []
    for local_id, expected in expected_highlights.items():
        _index, raw, fields = final_by_local[local_id]
        actual = (
            int(fields["x"]), int(fields["y"]), int(fields["elevation"]),
            int(fields["movement_type"]), raw[10] & 0xF, raw[10] >> 4,
        )
        if actual != expected:
            _fail(
                f"1/73 local {local_id} placement不一致: {actual}/{expected}"
            )
        highlights.append({
            "local_id": local_id,
            "x": actual[0], "y": actual[1], "elevation": actual[2],
            "movement_type": actual[3],
            "movement_range_x": actual[4],
            "movement_range_y": actual[5],
        })
    # NPC配置修復はwild header/table、warp、coord、BG、map scriptの
    # いずれも変更しない。実際のspecies/levelはmGBA fixtureでも検証する。
    structural_fields = ("warps_hex", "coords_hex", "bg_hex")
    if any(states["stage61"][key] != states["stage62"][key]
           for key in structural_fields):
        _fail("1/73 warp/coord/BG bytesが配置修復で変化しました")
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "physical_map": [1, 73],
        "physical_map_key": "VEGA_STOCK:001/073",
        "display_name": "ちえのどうくつ B1F",
        "source_rom_sha256": _sha(vega),
        "all_source_object_count": len(source_by_local),
        "all_source_placement_mismatch_count": 0,
        "restored_stage61_object_count": len(restored_rows),
        "restored_stage61_objects": restored_rows,
        "highlighted_objects": highlights,
        "coord_9": coord9_row,
        "local_1": {
            "owner_id": local1_owner,
            "externally_scripted_position_anchored": True,
            "external_operation_count": len(external),
            "external_operation_counts": dict(sorted(operation_counts.items())),
            "external_operations": external,
        },
        "static_story_contract": {
            "pre_warp_rival_template_not_at_stage61_early_trigger_position": True,
            "coord_9_and_all_object_control_operations_preserved": True,
            "rival_movement_and_remove_sequence_rooted": True,
            "warp_coord_bg_records_byte_identical_to_stage61": True,
            "object_script_pointers_and_trainer_fields_byte_identical_to_stage61": True,
            "wild_tables_outside_every_changed_byte_range": True,
        },
        "dynamic_fixture_contract": {
            "fixtures": list(WISDOM_ALL_FIXTURES),
            "covers": [
                "1/36から1/73への通常warp往復",
                "1/38から1/73への通常warp往復",
                "1/73から1/37へのB2F通常warp往復",
                "B1F原作species/Lv.6-9・方向転換・逃走後cadence",
                "B2F殿堂入り後species/Lv.44-48・方向転換・逃走後cadence",
                "3穴・段差切替・coord 9からのライバル戦とactor消去",
                "南口脱出・ねっこのカセキ取得・通常2世代save・fresh Continue",
            ],
            "result_report": (
                "reports/generated/stage62_wisdom_cave_mgba.json"
            ),
        },
        "assertions": {
            "map_1_73_is_vega_wisdom_cave_not_firered_cerulean_cave": True,
            "all_ten_source_object_placements_match_pinned_vega": (
                len(source_by_local) == 10
            ),
            "local_1_is_position_anchored": True,
            "all_static_story_warp_coord_bg_and_wild_contracts_preserved": True,
        },
    }


def _npc_catalog(
    rom: bytes, coords: Sequence[tuple[int, int, str]],
    mutable_manifest: Mapping[str, Any], operation_index: Mapping[
        str, Sequence[Mapping[str, Any]]
    ], global_report: Mapping[str, Any],
) -> dict[str, Any]:
    rows, _by_id = _all_objects(rom, coords)
    mutable_ids = set(map(str, mutable_manifest["owner_ids"]))
    origins = {
        str(row["owner_id"]): row["origins"]
        for row in mutable_manifest["owners"]
    }
    anchored = 0
    for row in rows:
        owner_id = str(row["npc_id"])
        evidence = list(operation_index.get(owner_id, []))
        operations = sorted({
            str(item["operation"]) for item in evidence
            if str(item["operation"]) in POSITION_ANCHORED_OBJECT_OPERATIONS
        })
        row["placement_mutability"] = (
            "EXPLICIT_PROJECT_ADDITION" if owner_id in mutable_ids
            else "SOURCE_EXISTING_IMMUTABLE"
        )
        row["addition_origins"] = origins.get(owner_id, [])
        row["position_anchored"] = bool(operations)
        row["position_anchored_operations"] = operations
        row["object_operation_evidence"] = evidence
        row["physical_provenance"] = (
            "VEGA_STOCK" if int(row["group"]) < 96 else "IMPORTED_KANTO"
        )
        anchored += int(bool(operations))
    local1 = next(
        row for row in rows
        if (row["group"], row["map"], row["local_id"]) == (1, 73, 1)
    )
    if not local1["position_anchored"] \
            or "APPLY_MOVEMENT" not in local1["position_anchored_operations"] \
            or "REMOVE_OBJECT" not in local1["position_anchored_operations"]:
        _fail("Stage62 catalogで1/73 local 1 anchor分類に失敗")
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "rom_sha256": _sha(rom),
        "object_count": len(rows),
        "explicit_project_added_count": len(mutable_ids),
        "source_existing_immutable_count": len(rows) - len(mutable_ids),
        "position_anchored_object_count": anchored,
        "global_object_operation_index": dict(global_report),
        "npcs": rows,
        "assertions": {
            "all_object_templates_catalogued": True,
            "all_placement_fields_catalogued": True,
            "all_script_object_operations_target_exact_map_and_local_id": True,
            "unrecognized_external_object_reference_count_is_zero": (
                int(global_report[
                    "unrecognized_external_object_reference_count"
                ]) == 0
            ),
            "wisdom_cave_local_1_position_anchored": True,
        },
    }


def _bps_roundtrip(
    source: bytes, target: bytes, metadata: bytes,
) -> tuple[bytes, dict[str, Any]]:
    patch = create_bps(source, target, metadata=metadata)
    rebuilt = apply_bps(source, patch)
    if rebuilt != target:
        _fail("BPS round-trip不一致")
    return patch, {
        "source_sha256": _sha(source),
        "patch_sha256": _sha(patch),
        "patch_size": len(patch),
        "output_sha256": _sha(rebuilt),
        "round_trip": "PASS",
    }


def build(config_path: Path = DEFAULT_CONFIG) -> dict[Path, bytes]:
    config = _load_config(config_path)
    inputs = config["inputs"]
    stage61 = _identity(inputs["stage61_rom"], "Stage61 current ROM")
    metadata61_raw = _identity(inputs["stage61_metadata"], "Stage61 metadata")
    stage60 = _identity(inputs["stage60_rom"], "Stage60 ROM")
    clean = _identity(inputs["clean_rom"], "clean FireRed ROM")
    vega = _identity(inputs["vega_reference_rom"], "Vega reference ROM")
    placement = _json(_identity(
        inputs["placement_audit"], "Stage61 placement audit"
    ), "Stage61 placement audit")
    npc61 = _json(_identity(
        inputs["npc_catalog"], "Stage61 NPC catalog"
    ), "Stage61 NPC catalog")
    map_catalog = _json(_identity(
        inputs["map_catalog"], "Stage61 map catalog"
    ), "Stage61 map catalog")
    trainer_plan = _json(_identity(
        inputs["trainer_event_plan"], "trainer event plan"
    ), "trainer event plan")
    post_ledger = _json(_identity(
        inputs["post_ledger_owners"], "post-ledger owners"
    ), "post-ledger owners")
    event_design_raw = _identity(
        inputs["event_design_bindings"], "event design bindings"
    )
    _identity(inputs["vega_map_inventory"], "Vega map inventory")
    if len(stage61) != ROM_SIZE or len(stage60) != ROM_SIZE:
        _fail("32 MiB ROM size契約不一致")
    metadata61 = _json(metadata61_raw, "Stage61 metadata")
    if metadata61.get("output", {}).get("sha256") != _sha(stage61):
        _fail("Stage61 metadata/current ROM identity不一致")
    coords = _physical_coordinates(map_catalog)
    all_before, object_sites_before = _all_objects(stage61, coords)
    mutable_manifest = _added_manifest(
        npc61, trainer_plan, post_ledger, event_design_raw,
    )
    mutable_ids = set(map(str, mutable_manifest["owner_ids"]))
    if not mutable_ids.issubset(object_sites_before):
        _fail("明示追加NPCがcurrent ROM object集合の部分集合ではありません")
    output, restoration, immutable_authority = _restore_immutable_placement(
        stage61, placement, mutable_ids, object_sites_before,
    )
    seeds_by_map, placement_map_rows = _entry_seed_index(placement)
    # Geometry/entry reportは同一のStage61 candidate由来であり、少なくとも
    # 追加NPCを持つ全mapについて最終ROM geometry hashと再照合する。
    additions_by_map: dict[tuple[int, int], set[str]] = defaultdict(set)
    for owner_id in mutable_ids:
        group, number = map(int, owner_id[7:14].split("/"))
        additions_by_map[(group, number)].add(owner_id)
    for key in sorted(additions_by_map):
        old_row = placement_map_rows.get(key)
        if old_row is None or not seeds_by_map.get(key):
            _fail(f"追加NPC mapのentry evidence欠落: {key}")
        geometry = _map_geometry(bytes(output), key[0], key[1])
        if str(old_row["geometry"]["blocks_sha256"]) \
                != str(geometry["blocks_sha256"]):
            _fail(f"entry evidence/geometry drift: {key}")
    operation_index, operation_report = _global_local_object_operation_index(
        bytes(output), coords,
    )
    if operation_report.get("status") != "PASS" \
            or int(operation_report[
                "unrecognized_external_object_reference_count"
            ]) != 0:
        _fail("global object operation index不完全")
    anchors = {
        owner_id for owner_id in mutable_ids
        if any(
            str(row["operation"]) in POSITION_ANCHORED_OBJECT_OPERATIONS
            for row in operation_index.get(owner_id, [])
        )
    }
    unsafe_before: list[dict[str, Any]] = []
    unsafe_maps: list[tuple[int, int]] = []
    for key in sorted(additions_by_map):
        reasons, row = _map_unsafe_reasons(
            bytes(output), key[0], key[1], additions_by_map[key], anchors,
            set(seeds_by_map[key]),
        )
        if reasons:
            unsafe_maps.append(key)
            unsafe_before.append(row)
    moved_candidates, backtracks = _allocate_unsafe_maps(
        output, coords, mutable_ids, anchors, seeds_by_map, unsafe_maps,
    )
    final_rom = bytes(output)
    all_final, object_sites_final = _all_objects(final_rom, coords)
    final_safety = _final_safety_audit(
        final_rom, coords, mutable_ids, anchors, seeds_by_map,
    )
    movement_audit = _anchored_movement_audit(
        final_rom, anchors, operation_index, object_sites_final,
    )
    immutable_audit = _immutable_contract_audit(
        stage61, final_rom, mutable_ids, immutable_authority, coords,
    )
    vega_audit = _vega_reference_audit(final_rom, stage60, vega)
    cave = _wisdom_cave_audit(
        stage61, final_rom, stage60, vega,
        operation_index, object_sites_final,
    )
    catalog = _npc_catalog(
        final_rom, coords, mutable_manifest,
        operation_index, operation_report,
    )
    moved_rows = [row for row in moved_candidates if row["moved"]]
    if len(unsafe_maps) != 7 or len(moved_rows) != 11:
        _fail(
            f"追加NPC safety reallocation cardinality drift: "
            f"maps={unsafe_maps} moved={len(moved_rows)}"
        )
    changed_offsets = [
        index for index, (before, after) in enumerate(zip(stage61, final_rom))
        if before != after
    ]
    allowed_offsets: set[int] = set()
    for row in restoration["restored_non_added_npcs"]:
        site = int(row["patch_address"], 16) - GBA_BASE
        allowed_offsets.update(range(site, site + 7))
    for row in restoration["restored_runtime_position_operands"]:
        site = int(row["operand_address"], 16) - GBA_BASE
        allowed_offsets.update(range(site, site + 4))
    for row in moved_rows:
        site = int(row["patch_address"], 16) - GBA_BASE
        allowed_offsets.update(range(site, site + 7))
    unexpected = sorted(set(changed_offsets) - allowed_offsets)
    if unexpected:
        _fail(f"宣言外ROM変更: {[hex(value) for value in unexpected[:20]]}")
    incremental_bps, incremental_report = _bps_roundtrip(
        stage61, final_rom, b"stage61-runtime-hotfix-to-stage62-npc-placement-integrity-repair",
    )
    clean_bps, clean_report = _bps_roundtrip(
        clean, final_rom, b"firered-jpn-rev0-to-stage62-npc-placement-integrity-repair",
    )
    output_sha = _sha(final_rom)
    audit = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "input": {
            "stage61_rom_sha256": _sha(stage61),
            "stage60_rom_sha256": _sha(stage60),
            "clean_rom_sha256": _sha(clean),
            "vega_reference_rom_sha256": _sha(vega),
        },
        "rom_sha256": output_sha,
        "root_causes": [
            "Stage61 allocatorが明示追加owner allowlistを持たず、portless peerを既存NPCまで再配置した",
            "object operation anchor判定が一部rootだけを見て、portを持つactorと*_AT target mapを落とした",
            "base 425 mapへFireRedの同一数値map名を付け、1/73をCeruleanCave_2Fと誤表示した",
            "object-template oracleを配置変更後に作り、誤配置を期待値として自己承認した",
        ],
        "placement_policy": {
            "mutable_owner_source": "EXPLICIT_PROJECT_ADDITION_MANIFEST_UNION_ONLY",
            "mutable_owner_count": len(mutable_ids),
            "immutable_owner_count": len(all_final) - len(mutable_ids),
            "source_existing_auto_relocation_forbidden": True,
            "script_controlled_actor_position_anchored": True,
            "fail_when_added_npc_has_no_safe_solution": True,
        },
        "restoration": restoration,
        "unsafe_before_added_reallocation": {
            "map_count": len(unsafe_maps),
            "maps": unsafe_before,
        },
        "added_npc_reallocation": {
            "algorithm": "DETERMINISTIC_MAP_JOINT_OBJECT_PORT_ALLOCATION",
            "evaluated_owner_count": len(moved_candidates),
            "moved_added_npc_count": len(moved_rows),
            "unchanged_added_npc_count_in_affected_maps": (
                len(moved_candidates) - len(moved_rows)
            ),
            "affected_map_count": len(unsafe_maps),
            "affected_maps": [list(key) for key in unsafe_maps],
            "search_backtrack_count": backtracks,
            "rows": moved_candidates,
        },
        "immutable_contract": immutable_audit,
        "vega_reference_contract": vega_audit,
        "added_npc_safety": final_safety,
        "script_controlled_added_actor_movement": movement_audit,
        "global_object_operation_index": operation_report,
        "rom_change_audit": {
            "changed_byte_count": len(changed_offsets),
            "allowed_byte_count": len(allowed_offsets),
            "unexpected_changed_byte_count": len(unexpected),
            "script_pointer_change_count": 0,
            "trainer_type_or_sight_change_count": 0,
        },
        "bps": {
            "stage61_incremental": incremental_report,
            "clean_direct": clean_report,
        },
        "assertions": {
            "relocated_existing_npc_count_is_zero": (
                immutable_audit["relocated_existing_npc_count"] == 0
            ),
            "all_316_non_added_stage61_changes_restored": (
                restoration["restored_non_added_npc_count"] == 316
            ),
            "only_explicit_added_npcs_received_new_placement": True,
            "all_added_npc_safety_assertions_pass": all(
                final_safety["assertions"].values()
            ),
            "all_external_object_references_recognized": (
                operation_report[
                    "unrecognized_external_object_reference_count"
                ] == 0
            ),
            "map_1_73_uses_vega_physical_identity": True,
            "current_stage61_rom_not_overwritten": True,
            "incremental_and_clean_bps_round_trip": True,
        },
    }
    if not all(audit["assertions"].values()):
        _fail(f"Stage62 final assertions FAIL: {audit['assertions']}")
    outputs = {key: Path(value) for key, value in config["outputs"].items()}
    metadata = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "candidate_status": "CANDIDATE",
        "input": {
            "path": str(inputs["stage61_rom"]["path"]),
            "size": len(stage61),
            "sha256": _sha(stage61),
            "metadata_sha256": _sha(metadata61_raw),
        },
        "output": {
            "path": str(outputs["rom"]),
            "size": len(final_rom),
            "sha256": output_sha,
            "crc32": f"{zlib.crc32(final_rom) & 0xFFFFFFFF:08X}",
        },
        "counts": {
            "physical_maps": len(coords),
            "object_owners": len(all_final),
            "source_existing_immutable": len(all_final) - len(mutable_ids),
            "explicit_project_additions": len(mutable_ids),
            "restored_non_added_npcs": len(
                restoration["restored_non_added_npcs"]
            ),
            "moved_added_npcs": len(moved_rows),
            "position_anchored_added_npcs": len(anchors),
        },
        "reports": {
            "audit": str(outputs["audit"]),
            "npc_catalog": str(outputs["npc_catalog"]),
            "wisdom_cave": str(outputs["wisdom_cave"]),
            "mgba": str(outputs["mgba"]),
        },
        "dynamic_gate": {
            "status": "REQUIRED_SEPARATE_REPORT",
            "required_fixtures": list(WISDOM_ALL_FIXTURES),
        },
    }
    artifacts = {
        outputs["rom"]: final_rom,
        outputs["metadata"]: _stable(metadata),
        outputs["incremental_bps"]: incremental_bps,
        outputs["clean_bps"]: clean_bps,
        outputs["audit"]: _stable(audit),
        outputs["npc_catalog"]: _stable(catalog),
        outputs["wisdom_cave"]: _stable(cave),
    }
    return artifacts


def _write(artifacts: Mapping[Path, bytes]) -> None:
    for relative, raw in artifacts.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def _check(artifacts: Mapping[Path, bytes]) -> None:
    failures = []
    for relative, expected in artifacts.items():
        path = ROOT / relative
        actual = path.read_bytes() if path.is_file() else None
        if actual != expected:
            failures.append(str(relative))
    if failures:
        _fail(f"生成物drift: {failures}")


def _run_wisdom_mgba(
    rom_path: Path, output_path: Path, runs: int,
) -> dict[str, Any]:
    if runs not in {1, 2}:
        _fail("mGBA runsは1または2です")
    compiler = shutil.which("cc")
    source = ROOT / "tools/mgba_world_runtime_input_e2e.c"
    story_source = ROOT / "tools/mgba_stage62_wisdom_cave_story_e2e.c"
    if compiler is None or not source.is_file() or not story_source.is_file():
        _fail("mGBA compile前提不足")
    rom = (ROOT / rom_path).read_bytes()
    digest = _sha(rom)
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="stage62-wisdom-", dir=local) as raw:
        work = Path(raw)
        executable = work / "world-input-e2e"
        story_executable = work / "wisdom-story-e2e"
        for label, runner_source, runner_executable in (
            ("汎用", source, executable),
            ("物語", story_source, story_executable),
        ):
            compiled = subprocess.run(
                [compiler, "-std=c11", "-O2", "-Wall", "-Wextra",
                 "-Werror", "-pedantic", str(runner_source), "-o",
                 str(runner_executable), "-lmgba"],
                cwd=ROOT, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=180, check=False,
            )
            if compiled.returncode or compiled.stdout or compiled.stderr:
                _fail(
                    f"mGBA {label}runner compile失敗: "
                    + (compiled.stderr or compiled.stdout)[-6000:]
                )
        for fixture in WISDOM_FIXTURES:
            documents: list[dict[str, Any]] = []
            for run_index in range(runs):
                directory = work / f"{fixture}-{run_index + 1}"
                directory.mkdir()
                completed = subprocess.run(
                    [str(executable), str(ROOT / rom_path), str(directory), fixture],
                    cwd=ROOT, text=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, timeout=1800, check=False,
                )
                if completed.returncode or completed.stderr:
                    _fail(
                        f"mGBA {fixture} run {run_index + 1}失敗: "
                        + (completed.stderr or completed.stdout)[-8000:]
                    )
                try:
                    document = json.loads(completed.stdout)
                except json.JSONDecodeError as exc:
                    _fail(f"mGBA {fixture} JSON不正: {exc}")
                if document.get("status") != "PASS" \
                        or len(document.get("fixtures", [])) != 1:
                    _fail(f"mGBA {fixture} PASS契約不一致: {document}")
                documents.append(document)
            if any(document != documents[0] for document in documents[1:]):
                _fail(f"mGBA {fixture} 独立process非決定的")
            results[fixture] = {
                "status": "PASS",
                "process_runs": runs,
                "identical_results": True,
                "result": documents[0]["fixtures"][0],
            }
        story_documents: list[dict[str, Any]] = []
        for run_index in range(runs):
            directory = work / f"{WISDOM_STORY_FIXTURE}-{run_index + 1}"
            directory.mkdir()
            completed = subprocess.run(
                [str(story_executable), str(ROOT / rom_path), str(directory)],
                cwd=ROOT, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, timeout=1800, check=False,
            )
            if completed.returncode or completed.stderr:
                _fail(
                    f"mGBA {WISDOM_STORY_FIXTURE} run {run_index + 1}失敗: "
                    + (completed.stderr or completed.stdout)[-8000:]
                )
            try:
                document = json.loads(completed.stdout)
            except json.JSONDecodeError as exc:
                _fail(f"mGBA {WISDOM_STORY_FIXTURE} JSON不正: {exc}")
            story_assertions = (
                document.get("status") == "PASS",
                document.get("case") == WISDOM_STORY_FIXTURE,
                document.get("north_entrance_to_b1f_by_keys") is True,
                document.get("pre_puzzle_rival_battle_absent") is True,
                document.get("teleport_mechanism_mask") == 7,
                document.get("three_teleport_holes_traversed") is True,
                document.get("ledge_and_coordinate_progression_to_scene_7")
                is True,
                document.get("coord_9_story_triggered_by_key") is True,
                document.get("rival_actor_movement_observed") is True,
                document.get("rival_trainer_id") == 360,
                document.get("rival_battle_completed") is True,
                document.get("story_actor_ids_removed") == [1, 2, 3, 4],
                document.get("story_scene_after") == 8,
                document.get("south_exit_to_map_1_38") is True,
                document.get("root_fossil_item_id") == 286,
                document.get("root_fossil_received_from_elder_by_keys") is True,
                document.get("normal_start_menu_save_generations") == 2,
                document.get("fresh_core_continue") is True,
                document.get("post_reload_start_menu_and_field") is True,
                document.get("warnings") == 0,
            )
            if not all(story_assertions):
                _fail(
                    f"mGBA {WISDOM_STORY_FIXTURE} PASS契約不一致: "
                    f"{document}"
                )
            story_documents.append(document)
        if any(
            document != story_documents[0]
            for document in story_documents[1:]
        ):
            _fail(f"mGBA {WISDOM_STORY_FIXTURE} 独立process非決定的")
        results[WISDOM_STORY_FIXTURE] = {
            "status": "PASS",
            "process_runs": runs,
            "identical_results": True,
            "result": story_documents[0],
        }
    report = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PASS",
        "rom": str(rom_path),
        "rom_sha256": digest,
        "fixture_count": len(results),
        "process_runs_per_fixture": runs,
        "fixtures": results,
        "assertions": {
            "north_entrance_real_input_round_trip": True,
            "south_entrance_real_input_round_trip": True,
            "b1f_b2f_real_input_round_trip": True,
            "b1f_native_species_level_and_cadence": True,
            "b2f_postgame_species_level_and_cadence": True,
            "three_holes_ledge_coord9_rival_and_actor_removal": True,
            "south_exit_fossil_save_and_fresh_continue": True,
            "every_fixture_repeated_in_fresh_process": runs == 2,
        },
    }
    if not all(report["assertions"].values()):
        _fail("mGBA full repetition gate未達")
    absolute = ROOT / output_path
    absolute.parent.mkdir(parents=True, exist_ok=True)
    absolute.write_bytes(_stable(report))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check", "mgba"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--runs", type=int, default=2)
    args = parser.parse_args(argv)
    try:
        config = _load_config(args.config)
        if args.command == "mgba":
            report = _run_wisdom_mgba(
                Path(config["outputs"]["rom"]),
                Path(config["outputs"]["mgba"]), args.runs,
            )
            print(json.dumps({
                "status": "PASS", "stage": STAGE,
                "rom_sha256": report["rom_sha256"],
                "fixture_count": report["fixture_count"],
                "process_runs_per_fixture": report[
                    "process_runs_per_fixture"
                ],
            }, ensure_ascii=False, sort_keys=True))
            return 0
        artifacts = build(args.config)
        if args.command == "build":
            _write(artifacts)
        else:
            _check(artifacts)
        outputs = config["outputs"]
        metadata = json.loads(artifacts[Path(outputs["metadata"])])
        print(json.dumps({
            "status": "PASS", "command": args.command,
            "stage": STAGE,
            "rom": metadata["output"]["path"],
            "rom_sha256": metadata["output"]["sha256"],
            "counts": metadata["counts"],
        }, ensure_ascii=False, sort_keys=True))
        return 0
    except (Stage62BuildError, KeyError, TypeError, ValueError, OSError,
            subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
