#!/usr/bin/env python3
"""ChatGPT Pro向けStage35イベント設計パケットを再現可能に生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PACKET_NAME = "Pokemon-Vega_CHATGPT-PRO_EVENT-AUTHORING_STAGE35_20260819"
ZIP_NAME = f"{PACKET_NAME}.zip"
GBA_ROM_BASE = 0x08000000
MAP_GROUPS_POINTER_SITE = 0x54B0C
OBJECT_LIMIT = 15
OBJECT_SIZE = 0x18
EVENT_HEADER_SIZE = 0x14

MAP_HEADER = [
    "map_key", "group_id", "map_id", "source_map", "logical_code",
    "map_name_ja", "classification", "width", "height", "unlock_key",
    "recommended_level_min", "recommended_level_max", "current_object_count",
    "free_object_slots", "source_object_count", "available_source_hosts",
    "bg_event_count", "coord_event_count", "warp_count", "connection_count",
    "field_pc_allowed", "script_policy", "notes",
]
OBJECT_HOST_HEADER = [
    "host_ref", "map_key", "root_index", "local_id", "graphics_id", "x", "y",
    "elevation", "movement_type", "trainer_type", "source_role",
    "current_occupancy", "status", "implementation_cost", "notes",
]
BG_HOST_HEADER = [
    "host_ref", "map_key", "root_index", "type", "x", "y", "elevation",
    "status", "implementation_cost", "notes",
]
COORD_HOST_HEADER = [
    "host_ref", "map_key", "root_index", "x", "y", "elevation",
    "condition_key", "status", "implementation_cost", "notes",
]
LIVE_OBJECT_HEADER = [
    "map_key", "record_index", "local_id", "graphics_numeric", "x", "y",
    "elevation", "movement_numeric", "trainer_type_numeric", "sight_range",
    "flag_numeric", "owner_kind", "owner_key",
]
LOGICAL_HEADER = [
    "logical_code", "map_name_ja", "progress_stage", "legacy_unlock_description",
    "recommended_level_range", "biome_tags", "encounter_modes", "narrative_role",
    "linked_event_ids", "linked_event_titles", "physical_map_count", "physical_map_keys",
]
PROGRESSION_HEADER = [
    "unlock_key", "region", "sequence", "predecessor_keys", "recommended_level_min",
    "recommended_level_max", "difficulty_policy", "mandatory", "warning_key",
    "safe_route_key", "allowed_gimmicks", "event_coverage_required",
]
QOL_HEADER = [
    "feature_key", "unlock_key", "source_boundary", "save_state_key",
    "storage_policy", "presentation_profile", "repeatability", "release_enabled",
    "event_design_requirement",
]
TRAINER_HEADER = [
    "encounter_key", "physical_map_key", "group_id", "map_id", "story_phase",
    "battle_type", "unlock_expression", "initial_or_rematch", "mandatory",
    "dialogue_set_key", "reward_key", "status",
]
ACQUISITION_HEADER = [
    "host_key", "physical_map_key", "group_id", "map_id", "x", "y", "elevation",
    "wrapper_symbol", "status", "notes",
]
REWARD_HEADER = [
    "catalog_reward_key", "resource_key", "resource_kind", "quantity", "unlock_key",
    "repeatability", "use_policy", "owner", "notes",
]
SERVICE_HEADER = [
    "service_profile_key", "availability", "unlock_key", "implementation_owner", "notes",
]
GRAPHICS_HEADER = ["graphics_id", "source_object_count", "recommended_use", "notes"]
STATE_HEADER = [
    "state_key", "owner", "storage_policy", "unlock_key", "write_policy", "notes",
]

REQUIRED_EVENT_GATES = {
    "KANTO_EARLY_ACCESS", "KANTO_DAYCARE_QUEST",
    *(f"KANTO_CERT_{index}" for index in range(1, 9)),
    "VEGA_HALL_OF_FAME", "KANTO_LEAGUE", "KANTO_LEAGUE_CLEAR",
    "SPHERE_COMPLETE", "FINAL_LEAGUE_AVAILABLE", "FINAL_LEAGUE_CLEARED",
}


class PacketError(RuntimeError):
    pass


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise PacketError(f"必須CSVがありません: {path}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, header: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(header), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _u32(raw: bytes, offset: int, label: str) -> int:
    if not 0 <= offset <= len(raw) - 4:
        raise PacketError(f"{label}: u32範囲外")
    return struct.unpack_from("<I", raw, offset)[0]


def _rom_offset(pointer: int, size: int, raw: bytes, label: str) -> int:
    offset = pointer - GBA_ROM_BASE
    if pointer < GBA_ROM_BASE or offset < 0 or offset + size > len(raw):
        raise PacketError(f"{label}: ROM pointer範囲外 {pointer:#010x}")
    return offset


def _stage_objects(raw: bytes, group_id: int, map_id: int) -> list[dict[str, int]]:
    root_pointer = _u32(raw, MAP_GROUPS_POINTER_SITE, "gMapGroups")
    root = _rom_offset(root_pointer, (group_id + 1) * 4, raw, "gMapGroups")
    group_pointer = _u32(raw, root + group_id * 4, f"map group {group_id}")
    group = _rom_offset(group_pointer, (map_id + 1) * 4, raw, f"map group {group_id}")
    header_pointer = _u32(raw, group + map_id * 4, f"map {group_id}/{map_id}")
    header = _rom_offset(header_pointer, 0x1C, raw, f"map header {group_id}/{map_id}")
    events_pointer = _u32(raw, header + 4, f"events {group_id}/{map_id}")
    events = _rom_offset(events_pointer, EVENT_HEADER_SIZE, raw, f"events {group_id}/{map_id}")
    count = raw[events]
    if count > OBJECT_LIMIT:
        raise PacketError(f"map {group_id}/{map_id}: live object {count} > {OBJECT_LIMIT}")
    if count == 0:
        return []
    pointer = _u32(raw, events + 4, f"objects {group_id}/{map_id}")
    objects = _rom_offset(pointer, count * OBJECT_SIZE, raw, f"objects {group_id}/{map_id}")
    result: list[dict[str, int]] = []
    for index in range(count):
        at = objects + index * OBJECT_SIZE
        result.append({
            "record_index": index,
            "local_id": raw[at],
            "graphics_numeric": raw[at + 1],
            "movement_numeric": raw[at + 3],
            "x": struct.unpack_from("<H", raw, at + 4)[0],
            "y": struct.unpack_from("<H", raw, at + 6)[0],
            "elevation": raw[at + 8],
            "trainer_type_numeric": struct.unpack_from("<H", raw, at + 12)[0],
            "sight_range": struct.unpack_from("<H", raw, at + 14)[0],
            "flag_numeric": struct.unpack_from("<H", raw, at + 20)[0],
        })
    return result


def _load_maps(root: Path) -> list[dict[str, Any]]:
    maps: list[dict[str, Any]] = []
    for path in sorted((root / "generated/maps/kanto").glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        header = row.get("map_header")
        if header and header.get("scope_decision") in {"INCLUDE", "REBUILD"}:
            maps.append(row)
    if len(maps) != 253:
        raise PacketError(f"Kanto map catalog drift: {len(maps)} != 253")
    logical = {row["map_header"]["logical_code"] for row in maps}
    if logical != {f"K{index:02d}" for index in range(1, 48)}:
        raise PacketError("Kanto logical location coverage drift")
    return maps


def _split_component(value: str, index: int) -> str:
    parts = value.split("+")
    return parts[index] if index < len(parts) else parts[0]


def _owner_index(trainers: list[dict[str, str]], acquisitions: list[dict[str, Any]]) \
        -> dict[tuple[str, int, int, int], tuple[str, str]]:
    result: dict[tuple[str, int, int, int], tuple[str, str]] = {}
    for row in trainers:
        xs, ys = row["x"].split("+"), row["y"].split("+")
        elevations = row["elevation"].split("+")
        for index, (x, y) in enumerate(zip(xs, ys)):
            elevation = elevations[index] if index < len(elevations) else elevations[0]
            result[(row["physical_map_key"], int(x), int(y), int(elevation))] = (
                "TRAINER", row["encounter_key"]
            )
    for row in acquisitions:
        result[(row["physical_map_key"], int(row["x"]), int(row["y"]),
                int(row["elevation"]))] = ("ACQUISITION", row["host_key"])
    return result


def _parse_charmap(path: Path) -> dict[str, Any]:
    mapping: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith("/") or "=" not in line:
            continue
        encoded, token = line.split("=", 1)
        encoded = encoded.strip()
        if not encoded or token == "":
            continue
        if token.startswith("\\") and token not in {"\\n", "\\p", "\\l"}:
            token = token[1:]
        mapping.setdefault(token, encoded.upper())
    if not all(token in mapping for token in ("あ", "ア", "A", " ", "\\n", "$")):
        raise PacketError("game charmap parse failed")
    return {
        "schema_version": 1,
        "encoding": "CFRU-JP one-byte game text",
        "max_line_glyphs": 18,
        "max_message_lines": 2,
        "line_break_token": "\\n",
        "terminator_token": "$",
        "mapping": dict(sorted(mapping.items())),
        "notes": [
            "dialogue.csvでは物理改行ではなくliteral \\nを使う",
            "幅はtoken数で数え、1行18 token以内・1 message 2行以内",
        ],
    }


def _catalogs(root: Path, packet: Path) -> dict[str, int]:
    stage_path = root / "build/stages/35_trainer_changekit_final.gba"
    stage_metadata_path = root / "build/stages/35_trainer_changekit_final.json"
    if not stage_path.is_file() or not stage_metadata_path.is_file():
        raise PacketError("Stage35 ROM/metadataがありません。先にStage35を再生成してください")
    stage = stage_path.read_bytes()
    metadata = json.loads(stage_metadata_path.read_text(encoding="utf-8"))
    if _sha256(stage_path) != metadata["output"]["sha256"]:
        raise PacketError("Stage35 ROM hash differs from metadata")

    maps = _load_maps(root)
    progression_source = _read_csv(root / "content/kanto_progression.csv")
    progression_by_key = {row["unlock_key"]: row for row in progression_source}
    map_policy_by_logical = {
        row["logical_location_key"]: row for row in _read_csv(root / "content/maps.csv")
        if row["region"] == "KANTO"
    }
    logical_source = {
        row["map_code"]: row for row in _read_csv(root /
            "design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data/二地方マップ別_出現レイヤーマスター_96地点.csv")
        if row["region"] == "カントー"
    }
    if len(logical_source) != 47:
        raise PacketError("legacy Kanto logical context drift")

    trainer_source = [
        row for row in _read_csv(root / "content/trainer_changekit_final/trainer_encounters.csv")
        if row["region"] == "KANTO"
    ]
    if len(trainer_source) != 201:
        raise PacketError(f"Kanto trainer count drift: {len(trainer_source)}")
    acquisition_meta = json.loads((root / "build/stages/26_acquisition_events.json").read_text())
    acquisition_source = acquisition_meta["map_scripts"]["patches"]
    if len(acquisition_source) != 24:
        raise PacketError(f"acquisition host count drift: {len(acquisition_source)}")
    owners = _owner_index(trainer_source, acquisition_source)

    live_by_map: dict[str, list[dict[str, int]]] = {}
    map_source_by_key = {row["map_header"]["map_key"]: row for row in maps}
    for source in maps:
        header = source["map_header"]
        live_by_map[header["map_key"]] = _stage_objects(
            stage, int(header["group_id"]), int(header["map_id"])
        )

    object_rows: list[dict[str, Any]] = []
    bg_rows: list[dict[str, Any]] = []
    coord_rows: list[dict[str, Any]] = []
    live_rows: list[dict[str, Any]] = []
    graphics_counts: Counter[str] = Counter()
    available_by_map: Counter[str] = Counter()
    for source in maps:
        header = source["map_header"]
        map_key = header["map_key"]
        live = live_by_map[map_key]
        occupied = {(row["x"], row["y"], row["elevation"]): row for row in live}
        for index, obj in enumerate(source["objects"]):
            graphics_counts[obj["graphics_id"]] += 1
            coordinate = (int(obj["x"]), int(obj["y"]), int(obj["elevation"]))
            if coordinate in occupied:
                status = "OCCUPIED_CURRENT_ROM"
                occupancy = "YES"
            elif obj["trainer_type"] != "TRAINER_TYPE_NONE":
                status = "RESERVED_TRAINER_TEMPLATE"
                occupancy = "NO"
            elif len(live) >= OBJECT_LIMIT:
                status = "NO_CAPACITY"
                occupancy = "NO"
            else:
                status = "AVAILABLE_RESTORE"
                occupancy = "NO"
                available_by_map[map_key] += 1
            object_rows.append({
                "host_ref": f"OBJHOST::{map_key}::{index:03d}", "map_key": map_key,
                "root_index": index, "local_id": obj["local_id"],
                "graphics_id": obj["graphics_id"], "x": obj["x"], "y": obj["y"],
                "elevation": obj["elevation"], "movement_type": obj["movement_type"],
                "trainer_type": obj["trainer_type"], "source_role": obj["source_role"],
                "current_occupancy": occupancy, "status": status,
                "implementation_cost": 1,
                "notes": "clean FireRed source object record。script/local ID/flagはCodexが再割当",
            })
        for index, event in enumerate(source["bg_events"]):
            event_type = event.get("type", "unknown")
            status = "AVAILABLE_REPOINT" if event_type == "sign" else "RESERVED_EXISTING_ITEM"
            bg_rows.append({
                "host_ref": f"BGHOST::{map_key}::{index:03d}", "map_key": map_key,
                "root_index": index, "type": event_type, "x": event.get("x", ""),
                "y": event.get("y", ""), "elevation": event.get("elevation", ""),
                "status": status, "implementation_cost": 0,
                "notes": "sign script repoint可" if status == "AVAILABLE_REPOINT"
                         else "T16 hidden-item ownerを維持",
            })
        for index, event in enumerate(source["coord_events"]):
            coord_rows.append({
                "host_ref": f"COORDHOST::{map_key}::{index:03d}", "map_key": map_key,
                "root_index": index, "x": event.get("x", ""), "y": event.get("y", ""),
                "elevation": event.get("elevation", ""),
                "condition_key": event.get("condition", event.get("trigger", "NONE")),
                "status": "AVAILABLE_WITH_AUDIT", "implementation_cost": 0,
                "notes": "step trigger/collision/warp到達性をCodexがexact audit",
            })
        for row in live:
            owner = owners.get((map_key, row["x"], row["y"], row["elevation"]),
                               ("BASELINE_OR_ARCHIVE", "NONE"))
            live_rows.append({"map_key": map_key, **row, "owner_kind": owner[0],
                              "owner_key": owner[1]})

    logical_maps: dict[str, list[str]] = defaultdict(list)
    map_rows: list[dict[str, Any]] = []
    for source in maps:
        header, layout = source["map_header"], source["layout"]
        code, map_key = header["logical_code"], header["map_key"]
        logical_maps[code].append(map_key)
        policy = map_policy_by_logical[code]
        progression = progression_by_key[policy["unlock_key"]]
        logical = logical_source[code]
        current_count = len(live_by_map[map_key])
        map_rows.append({
            "map_key": map_key, "group_id": header["group_id"], "map_id": header["map_id"],
            "source_map": header["source_map"], "logical_code": code,
            "map_name_ja": logical["map_name"], "classification": header["classification"],
            "width": layout["width"], "height": layout["height"],
            "unlock_key": policy["unlock_key"],
            "recommended_level_min": progression["recommended_level_min"],
            "recommended_level_max": progression["recommended_level_max"],
            "current_object_count": current_count,
            "free_object_slots": OBJECT_LIMIT - current_count,
            "source_object_count": len(source["objects"]),
            "available_source_hosts": available_by_map[map_key],
            "bg_event_count": len(source["bg_events"]),
            "coord_event_count": len(source["coord_events"]),
            "warp_count": len(source["warps"]), "connection_count": len(source["connections"]),
            "field_pc_allowed": policy["field_pc_allowed"],
            "script_policy": "SIMPLE_EVENT_ONLY",
            "notes": "Stage35 live objectを基準。object上限15",
        })

    logical_rows: list[dict[str, Any]] = []
    for code in sorted(logical_source):
        source = logical_source[code]
        physical = sorted(logical_maps[code])
        logical_rows.append({
            "logical_code": code, "map_name_ja": source["map_name"],
            "progress_stage": source["progress_stage"],
            "legacy_unlock_description": source["unlock_requirement"],
            "recommended_level_range": source["recommended_level_range"],
            "biome_tags": source["biome_tags"], "encounter_modes": source["encounter_modes"],
            "narrative_role": source["narrative_role"],
            "linked_event_ids": source["linked_event_ids"],
            "linked_event_titles": source["linked_event_titles"],
            "physical_map_count": len(physical), "physical_map_keys": "|".join(physical),
        })

    qol_source = _read_csv(root / "content/qol_progression.csv")
    progression_rows = [
        {**row, "event_coverage_required":
         "true" if row["unlock_key"] in REQUIRED_EVENT_GATES else "false"}
        for row in progression_source
    ]
    qol_rows = [
        {**row, "event_design_requirement":
         "REQUIRED_SIMPLE_EVENT" if row["presentation_profile"] == "SIMPLE_EVENT"
         else "AUTO_OR_EXISTING_UI"}
        for row in qol_source
    ]
    trainer_rows = [{key: row[key] for key in TRAINER_HEADER} for row in trainer_source]
    acquisition_rows = [{
        "host_key": row["host_key"], "physical_map_key": row["physical_map_key"],
        "group_id": row["group_id"], "map_id": row["map_id"], "x": row["x"],
        "y": row["y"], "elevation": row["elevation"],
        "wrapper_symbol": row["wrapper_symbol"], "status": "LIVE_STAGE35",
        "notes": "CALL_ACQUISITION_HOSTで既存transactionを呼ぶ。再実装禁止",
    } for row in acquisition_source]

    reward_rows = [
        {"catalog_reward_key": "REWARD_KEY_NONE", "resource_key": "NONE",
         "resource_kind": "NONE", "quantity": 0, "unlock_key": "VEGA_PRE_ENTRY",
         "repeatability": "NONE", "use_policy": "GRANT_ALLOWED", "owner": "EVENT_BUNDLE",
         "notes": "報酬なし"},
        {"catalog_reward_key": "CATALOG_REWARD_EVENT_ORAN_BERRY",
         "resource_key": "ITEM_KEY_ORAN_BERRY", "resource_kind": "ITEM", "quantity": 1,
         "unlock_key": "KANTO_EARLY_ACCESS", "repeatability": "ONCE",
         "use_policy": "GRANT_ALLOWED", "owner": "EVENT_BUNDLE",
         "notes": "低額sidequest reward。bag precheck必須"},
        {"catalog_reward_key": "CATALOG_REWARD_EVENT_POKE_BALLS",
         "resource_key": "ITEM_KEY_POKE_BALL", "resource_kind": "ITEM", "quantity": 5,
         "unlock_key": "KANTO_EARLY_ACCESS", "repeatability": "ONCE",
         "use_policy": "GRANT_ALLOWED", "owner": "EVENT_BUNDLE",
         "notes": "低額sidequest reward。bag precheck必須"},
        {"catalog_reward_key": "CATALOG_REWARD_EVENT_ULTRA_BALLS",
         "resource_key": "ITEM_KEY_ULTRA_BALL", "resource_kind": "ITEM", "quantity": 3,
         "unlock_key": "KANTO_CERT_4", "repeatability": "ONCE",
         "use_policy": "GRANT_ALLOWED", "owner": "EVENT_BUNDLE",
         "notes": "後半sidequest reward。bag precheck必須"},
        {"catalog_reward_key": "CATALOG_REWARD_EVENT_ESCAPE_ROPE",
         "resource_key": "ITEM_KEY_ESCAPE_ROPE", "resource_kind": "ITEM", "quantity": 1,
         "unlock_key": "KANTO_EARLY_ACCESS", "repeatability": "ONCE",
         "use_policy": "GRANT_ALLOWED", "owner": "EVENT_BUNDLE",
         "notes": "探索sidequest reward。bag precheck必須"},
    ]
    for row in _read_csv(root / "manifests/qol_rewards.csv"):
        reward_rows.append({
            "catalog_reward_key": row["reward_key"],
            "resource_key": row["item_key"] if row["item_key"] != "NONE" else row["service_key"],
            "resource_kind": "ITEM" if row["item_key"] != "NONE" else "SERVICE",
            "quantity": row["quantity"], "unlock_key": row["unlock_key"],
            "repeatability": row["repeatability"], "use_policy": "EXISTING_OWNER_ONLY",
            "owner": row["source_kind"], "notes": "QOL既存owner。新規GIVE_REWARD禁止",
        })
    for row in _read_csv(root / "manifests/facility_rewards.csv"):
        reward_rows.append({
            "catalog_reward_key": row["facility_reward_key"],
            "resource_key": row["item_key"] if row["item_key"] != "NONE" else row["currency_key"],
            "resource_kind": "ITEM" if row["item_key"] != "NONE" else "CURRENCY",
            "quantity": row["quantity"] if row["item_key"] != "NONE" else row["amount"],
            "unlock_key": row["unlock_key"], "repeatability": row["repeatability"],
            "use_policy": "EXISTING_OWNER_ONLY", "owner": "FACTORY",
            "notes": "Factory既存owner。新規GIVE_REWARD禁止",
        })

    service_rows = [
        ("SERVICE_PROFILE_NONE", "ALWAYS", "VEGA_PRE_ENTRY", "NONE", "serviceなし"),
        ("SERVICE_PROFILE_EXISTING_POKECENTER", "CATALOG_MAP", "KANTO_EARLY_ACCESS", "BASELINE", "既存回復施設"),
        ("SERVICE_PROFILE_EXISTING_MART", "CATALOG_MAP", "KANTO_EARLY_ACCESS", "BASELINE", "既存shop"),
        ("SERVICE_PROFILE_FIELD_PC", "QOL", "VEGA_DH_CLEAR", "QOL", "FIELD_PC解禁済み時のみ"),
        ("SERVICE_PROFILE_MOVE_MEMORY", "QOL", "VEGA_BADGE_2", "QOL", "FREE_MOVE_RELEARN/PC_MOVE_EDIT"),
        ("SERVICE_PROFILE_EV_RESET_ALL", "QOL", "VEGA_DH_CLEAR", "QOL", "既存transaction"),
        ("SERVICE_PROFILE_DAYCARE", "QOL", "VEGA_DAYCARE_FIRST", "QOL", "既存daycare owner"),
        ("SERVICE_PROFILE_FACTORY_TRIAL", "FACILITY", "KANTO_EARLY_ACCESS", "FACTORY", "既存Trial"),
        ("SERVICE_PROFILE_BP_SHOP", "FACILITY", "VEGA_DH_CLEAR", "FACTORY", "既存BP shop"),
        ("SERVICE_PROFILE_ECOLOGY_RADAR", "QOL", "RESEARCH_PROFILE_UNLOCKED", "QOL", "既存research profile"),
        ("SERVICE_PROFILE_AUTO_BATTLE_UNLOCK", "QOL", "VEGA_DH_CLEAR", "QOL", "説明eventのみ"),
        ("SERVICE_PROFILE_EGG_BASKET", "QOL", "KANTO_DAYCARE_QUEST", "QOL", "既存egg queue"),
    ]
    service_dicts = [dict(zip(SERVICE_HEADER, row)) for row in service_rows]

    state_rows = [{
        "state_key": row["state_key"], "owner": row["owner"],
        "storage_policy": row["storage_policy"], "unlock_key": row["unlock_key"],
        "write_policy": row["write_policy"],
        "notes": "既存state。イベント側で新規IDを割り当てない",
    } for row in _read_csv(root / "content/kanto_state_model.csv")]
    for row in qol_source:
        if row["save_state_key"] != "NONE":
            state_rows.append({
                "state_key": row["save_state_key"], "owner": "QOL",
                "storage_policy": row["storage_policy"], "unlock_key": row["unlock_key"],
                "write_policy": "EXISTING_QOL_OWNER_ONLY",
                "notes": f"{row['feature_key']}の既存state。イベントから直接write禁止",
            })

    graphics_rows = [{
        "graphics_id": key, "source_object_count": count,
        "recommended_use": "SOURCE_HOST_MATCH_OR_SAFE_TILE",
        "notes": "RESTORE_SOURCE_OBJECTではhostと同じgraphics必須",
    } for key, count in sorted(graphics_counts.items())]

    catalogs = packet / "catalogs"
    _write_csv(catalogs / "maps.csv", MAP_HEADER, map_rows)
    _write_csv(catalogs / "logical_locations.csv", LOGICAL_HEADER, logical_rows)
    _write_csv(catalogs / "source_object_hosts.csv", OBJECT_HOST_HEADER, object_rows)
    _write_csv(catalogs / "bg_event_hosts.csv", BG_HOST_HEADER, bg_rows)
    _write_csv(catalogs / "coord_event_hosts.csv", COORD_HOST_HEADER, coord_rows)
    _write_csv(catalogs / "current_live_objects.csv", LIVE_OBJECT_HEADER, live_rows)
    _write_csv(catalogs / "progression.csv", PROGRESSION_HEADER, progression_rows)
    _write_csv(catalogs / "qol_features.csv", QOL_HEADER, qol_rows)
    _write_csv(catalogs / "existing_kanto_trainers.csv", TRAINER_HEADER, trainer_rows)
    _write_csv(catalogs / "acquisition_hosts.csv", ACQUISITION_HEADER, acquisition_rows)
    _write_csv(catalogs / "reward_catalog.csv", REWARD_HEADER, reward_rows)
    _write_csv(catalogs / "service_profiles.csv", SERVICE_HEADER, service_dicts)
    _write_csv(catalogs / "object_graphics_catalog.csv", GRAPHICS_HEADER, graphics_rows)
    _write_csv(catalogs / "existing_state_keys.csv", STATE_HEADER, state_rows)
    shutil.copy2(root / "content/events.csv", catalogs / "existing_events.csv")

    legacy = _read_csv(root /
        "design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data/二地方_追加イベント詳細マスター_34件.csv")
    legacy_header = list(legacy[0]) + ["adoption_status", "review_notes"]
    _write_csv(catalogs / "legacy_event_seeds.csv", legacy_header, [
        {**row, "adoption_status": "REWRITE_REQUIRED",
         "review_notes": "発想材料のみ。現Stage35 catalog/contractへ全面書換"}
        for row in legacy
    ])
    _write_json(catalogs / "game_charmap.json",
                _parse_charmap(root / "vendor/upstream/CFRU-JP/charmap.tbl"))
    return {
        "maps": len(map_rows), "logical_locations": len(logical_rows),
        "source_object_hosts": len(object_rows),
        "available_source_object_hosts": sum(row["status"] == "AVAILABLE_RESTORE" for row in object_rows),
        "bg_event_hosts": len(bg_rows),
        "available_bg_event_hosts": sum(row["status"] == "AVAILABLE_REPOINT" for row in bg_rows),
        "coord_event_hosts": len(coord_rows), "current_live_objects": len(live_rows),
        "progression_gates": len(progression_rows), "qol_features": len(qol_rows),
        "kanto_trainers": len(trainer_rows), "acquisition_hosts": len(acquisition_rows),
        "reward_entries": len(reward_rows), "service_profiles": len(service_dicts),
        "existing_states": len(state_rows),
    }


def _template(packet: Path) -> None:
    submission = packet / "submission_template"
    submission.mkdir(parents=True, exist_ok=True)
    event_key = "EVENT_KEY_TEMPLATE_VERMILION_SIGN"
    arc_key = "ARC_KEY_TEMPLATE"
    batch_key = "BATCH_KEY_PILOT_VERMILION"
    placement_key = "PLACEMENT_KEY_EVENT_TEMPLATE_VERMILION_SIGN"
    condition_key = "CONDITION_KEY_EVENT_TEMPLATE_KANTO_ACCESS"
    dialogue_key = "DIALOGUE_KEY_TEMPLATE_VERMILION_SIGN"
    plan = {
        "schema_version": 1, "project_key": "POKEMON_VEGA_MODERN_STAGE35",
        "bundle_key": "BUNDLE_KEY_KANTO_EVENT_DESIGN", "language": "ja",
        "design_status": "TEMPLATE",
        "design_summary": "出力形式とhost参照方法を示す最小テンプレート",
        "assumptions": ["完成版では全項目を実設計へ置換する"], "open_questions": [],
        "arcs": [{
            "arc_key": arc_key, "title": "テンプレート", "category": "FLAVOR",
            "priority": "P2", "start_unlock_key": "KANTO_EARLY_ACCESS",
            "completion_state_key": "NONE", "event_keys": [event_key],
            "summary": "sign eventの形式例", "player_goal": "signを読む",
            "failure_policy": "NO_FAILURE", "notes": "完成版では置換",
        }],
        "states": [], "actors": [],
        "placements": [{
            "placement_key": placement_key, "map_key": "KANTO_OUTDOOR_VERMILION_CITY",
            "trigger_type": "READ_SIGN",
            "host_ref": "BGHOST::KANTO_OUTDOOR_VERMILION_CITY::000",
            "allocation_policy": "REPOINT_SOURCE_BG", "object_cost": 0,
            "graphics_id": "NONE", "movement_type": "NONE",
            "collision_audit_required": False, "notes": "catalog sign hostの例",
        }],
        "conditions": [{
            "condition_key": condition_key,
            "all_of": [{"kind": "UNLOCK", "key": "KANTO_EARLY_ACCESS",
                        "operator": "SET", "value": 1}],
            "any_of": [], "none_of": [], "notes": "Kanto access後",
        }],
        "rewards": [],
        "events": [{
            "event_key": event_key, "title": "みなとの あんない", "region": "KANTO",
            "arc_key": arc_key, "batch_key": batch_key,
            "map_key": "KANTO_OUTDOOR_VERMILION_CITY", "logical_code": "K46",
            "placement_key": placement_key, "unlock_key": "KANTO_EARLY_ACCESS",
            "condition_key": condition_key, "presentation_profile": "SIMPLE_EVENT",
            "repeatability": "REPEATABLE", "mandatory": False,
            "result_policy": "NO_BATTLE", "completion_state_key": "NONE",
            "reward_key": "NONE",
            "steps": [
                {"step_key": "STEP_KEY_TEMPLATE_SHOW", "op": "SHOW_DIALOGUE",
                 "arg_key": dialogue_key, "next_step_key": "STEP_KEY_TEMPLATE_END",
                 "alt_step_key": "NONE", "notes": "短い案内"},
                {"step_key": "STEP_KEY_TEMPLATE_END", "op": "END", "arg_key": "NONE",
                 "next_step_key": "NONE", "alt_step_key": "NONE", "notes": "終了"},
            ],
            "failure_policy": {
                "decline": "NOT_APPLICABLE", "battle_loss": "NOT_APPLICABLE",
                "bag_full": "NOT_APPLICABLE", "party_pc_full": "NOT_APPLICABLE",
                "reset_during_event": "RETRY_FROM_COMMITTED_STATE",
                "save_reload": "PRESERVE_COMMITTED_STATE",
            },
            "acceptance_tests": [
                {"test_key": "TEST_KEY_TEMPLATE_LOCK", "category": "UNLOCK_BOUNDARY",
                 "setup_terms": ["KANTO_EARLY_ACCESS未成立"], "action": "signを調べる",
                 "expected": "eventは開始しない"},
                {"test_key": "TEST_KEY_TEMPLATE_HAPPY", "category": "HAPPY_PATH",
                 "setup_terms": ["KANTO_EARLY_ACCESS成立"], "action": "signを調べる",
                 "expected": "案内を表示して終了する"},
                {"test_key": "TEST_KEY_TEMPLATE_REVISIT", "category": "REVISIT",
                 "setup_terms": ["一度読了"], "action": "再びsignを調べる",
                 "expected": "同じ案内を安全に表示する"},
                {"test_key": "TEST_KEY_TEMPLATE_SAVE", "category": "SAVE_RELOAD",
                 "setup_terms": ["読了後save/reload"], "action": "再びsignを調べる",
                 "expected": "同じ案内を安全に表示する"},
            ],
            "notes": "完成版では実eventへ置換",
        }],
        "batches": [{
            "batch_key": batch_key, "title": "クチバpilot template", "priority": "P0",
            "depends_on": [], "event_keys": [event_key],
            "map_keys": ["KANTO_OUTDOOR_VERMILION_CITY"], "state_keys": [],
            "rollback_boundary": "このbatchのmap script repointだけを戻す",
            "verify_cases": ["sign会話と再訪"], "notes": "完成版は5〜10 event",
        }],
    }
    _write_json(submission / "event_plan.json", plan)
    _write_csv(submission / "dialogue.csv",
               ["dialogue_key", "event_key", "speaker_actor_key", "usage", "text",
                "next_step_key", "notes"], [{
                    "dialogue_key": dialogue_key, "event_key": event_key,
                    "speaker_actor_key": "ACTOR_KEY_SYSTEM", "usage": "FLAVOR",
                    "text": "カントーの みなと\\nたびの じゅんびを。",
                    "next_step_key": "STEP_KEY_TEMPLATE_END", "notes": "形式例",
               }])
    coverage: list[dict[str, str]] = []
    for index in range(1, 48):
        code = f"K{index:02d}"
        coverage.append({"coverage_key": f"COVERAGE_LOGICAL_{code}",
                         "subject_kind": "LOGICAL_LOCATION", "subject_key": code,
                         "coverage_status": "TEMPLATE_TODO", "event_keys": "",
                         "rationale": "テンプレート。完成版で判断する"})
    with (packet / "catalogs/qol_features.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            coverage.append({"coverage_key": f"COVERAGE_QOL_{row['feature_key']}",
                             "subject_kind": "QOL_FEATURE", "subject_key": row["feature_key"],
                             "coverage_status": "TEMPLATE_TODO", "event_keys": "",
                             "rationale": "テンプレート。完成版で判断する"})
    with (packet / "catalogs/progression.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["event_coverage_required"] == "true":
                coverage.append({"coverage_key": f"COVERAGE_GATE_{row['unlock_key']}",
                                 "subject_kind": "PROGRESSION_GATE",
                                 "subject_key": row["unlock_key"],
                                 "coverage_status": "TEMPLATE_TODO", "event_keys": "",
                                 "rationale": "テンプレート。完成版で判断する"})
    _write_csv(submission / "coverage.csv",
               ["coverage_key", "subject_kind", "subject_key", "coverage_status",
                "event_keys", "rationale"], coverage)
    (submission / "EVENT_BIBLE_JA.md").write_text(
        "# Event Bible template\n\n"
        f"{arc_key} と {batch_key} の形式例です。完成版では全面的に置換します。\n",
        encoding="utf-8")
    (submission / "OPEN_QUESTIONS.md").write_text(
        "# Open questions\n\nテンプレートのため、完成版では質問0件へ確定します。\n",
        encoding="utf-8")
    validator = packet / "tools/validate_submission.py"
    report = submission / "VALIDATION_REPORT.json"
    run = subprocess.run(
        [sys.executable, str(validator), str(submission), "--packet-root", str(packet),
         "--allow-template", "--report", str(report)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if run.returncode:
        raise PacketError(f"submission template validation failed:\n{run.stdout}\n{run.stderr}")


def _manifest(root: Path, packet: Path, counts: dict[str, int]) -> dict[str, Any]:
    stage = root / "build/stages/35_trainer_changekit_final.gba"
    stage_metadata = root / "build/stages/35_trainer_changekit_final.json"
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                            stdout=subprocess.PIPE, check=True).stdout.strip()
    files = []
    for path in sorted(packet.rglob("*")):
        if path.is_file() and path.name != "PACKET_MANIFEST.json":
            files.append({"path": path.relative_to(packet).as_posix(),
                          "size": path.stat().st_size, "sha256": _sha256(path)})
    value = {
        "schema_version": 1, "packet_name": PACKET_NAME,
        "purpose": "ChatGPT ProからCodex実装可能なKanto event設計bundleを受け取る",
        "baseline": {
            "stage": 35, "rom_sha256": _sha256(stage),
            "metadata_sha256": _sha256(stage_metadata), "git_commit": commit,
        },
        "privacy": {"rom_included": False, "save_included": False,
                    "private_input_included": False},
        "catalog_counts": counts, "files": files,
    }
    _write_json(packet / "PACKET_MANIFEST.json", value)
    return value


def _deterministic_zip(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            name = f"{source.name}/{path.relative_to(source).as_posix()}"
            info = zipfile.ZipInfo(name, date_time=(2026, 8, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)


def _verify_packet(packet: Path) -> dict[str, Any]:
    manifest = json.loads((packet / "PACKET_MANIFEST.json").read_text(encoding="utf-8"))
    expected = {row["path"]: row for row in manifest["files"]}
    actual = {
        path.relative_to(packet).as_posix(): path for path in packet.rglob("*")
        if path.is_file() and path.name != "PACKET_MANIFEST.json"
    }
    if set(expected) != set(actual):
        raise PacketError("packet manifest file set mismatch")
    for name, row in expected.items():
        if actual[name].stat().st_size != row["size"] or _sha256(actual[name]) != row["sha256"]:
            raise PacketError(f"packet manifest mismatch: {name}")
    report = json.loads((packet / "submission_template/VALIDATION_REPORT.json").read_text())
    if report.get("status") != "PASS":
        raise PacketError("template validation report is not PASS")
    return {"manifest_files": len(expected), "template_validation": "PASS"}


def build_packet(root: Path, output_parent: Path, zip_path: Path) -> dict[str, Any]:
    template = root / "templates/event_authoring_packet"
    if not template.is_dir():
        raise PacketError(f"packet template missing: {template}")
    packet = output_parent / PACKET_NAME
    if packet.exists():
        shutil.rmtree(packet)
    packet.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template, packet,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    counts = _catalogs(root, packet)
    _template(packet)
    manifest = _manifest(root, packet, counts)
    verify = _verify_packet(packet)
    _deterministic_zip(packet, zip_path)
    digest = _sha256(zip_path)
    zip_path.with_suffix(zip_path.suffix + ".sha256").write_text(
        f"{digest}  {zip_path.name}\n", encoding="ascii")
    prompt_path = zip_path.with_name(f"{PACKET_NAME}_PROMPT_JA.txt")
    shutil.copy2(packet / "01_CHATGPT_PRO_PROMPT_JA.txt", prompt_path)
    with tempfile.TemporaryDirectory(prefix="event-packet-verify-") as temporary:
        unpack = Path(temporary)
        with zipfile.ZipFile(zip_path) as archive:
            bad = archive.testzip()
            if bad:
                raise PacketError(f"ZIP CRC failed: {bad}")
            archive.extractall(unpack)
        extracted = unpack / PACKET_NAME
        extracted_verify = _verify_packet(extracted)
        with tempfile.TemporaryDirectory(prefix="event-packet-repack-") as second:
            repacked = Path(second) / ZIP_NAME
            _deterministic_zip(extracted, repacked)
            if _sha256(repacked) != digest:
                raise PacketError("re-expanded packet is not byte-deterministic")
    return {
        "status": "PASS", "packet_dir": str(packet), "zip": str(zip_path),
        "prompt": str(prompt_path),
        "zip_size": zip_path.stat().st_size, "zip_sha256": digest,
        "manifest_files": len(manifest["files"]), "catalog_counts": counts,
        "verification": {**verify, **extracted_verify, "zip_crc": "PASS",
                         "repack_determinism": "PASS"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-parent", type=Path,
                        default=Path("dist/event_authoring_packet"))
    parser.add_argument("--zip", type=Path,
                        default=Path("dist") / ZIP_NAME)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output_parent = args.output_parent
    if not output_parent.is_absolute():
        output_parent = root / output_parent
    zip_path = args.zip
    if not zip_path.is_absolute():
        zip_path = root / zip_path
    try:
        result = build_packet(root, output_parent.resolve(), zip_path.resolve())
    except (PacketError, OSError, ValueError, KeyError, subprocess.SubprocessError,
            zipfile.BadZipFile) as exc:
        result = {"status": "FAIL", "error": str(exc)}
    raw = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.report:
        report = args.report if args.report.is_absolute() else root / args.report
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
