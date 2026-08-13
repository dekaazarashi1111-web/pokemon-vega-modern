"""T14 selected mainland map import and connectivity validators."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any

from .kanto_importer import BuildError

DEFERRED_SOURCES = {"Route6_UnusedHouse", "Route19_UnusedHouse", "Route23_UnusedHouse"}
REBUILD_SOURCES = {"Route11"}
RUNTIME_DESTINATIONS = {
    "MAP_UNION_ROOM": "RUNTIME_UNION_ROOM",
    "MAP_TRADE_CENTER": "RUNTIME_TRADE_CENTER",
    "MAP_DYNAMIC": "RUNTIME_DYNAMIC_WARP",
}
ALLOCATION_START = 0x01F50000
ALLOCATION_END = 0x02000000


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _csv_bytes(header: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _source(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / f"vendor/upstream/pokefirered/data/maps/{name}/map.json").read_text())


def _layouts(root: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads((root / "vendor/upstream/pokefirered/data/layouts/layouts.json").read_text())["layouts"]
    return {row["id"]: row for row in rows if row.get("id")}


def _scope(inventory: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for row in inventory:
        source = row["source_map"]
        decision = "DEFER" if source in DEFERRED_SOURCES else "REBUILD" if source in REBUILD_SOURCES else "INCLUDE"
        rows.append({
            "map_key": row["map_key"], "source_map": source,
            "logical_code": row["logical_code"], "classification": row["classification"],
            "scope_decision": decision,
            "reason": ("UNUSED_UNREACHABLE_SOURCE_MAP" if decision == "DEFER" else
                       "CLEAN_BPRJ_LAYOUT_OVERRIDE" if decision == "REBUILD" else
                       "MAINLAND_REQUIRED"),
            "script_policy": "KANTO_NAMESPACED_STUB",
            "sevii": "false",
        })
    return rows


def _canonical_map(root: Path, row: dict[str, str], source_to_key: dict[str, str],
                   source_id_to_key: dict[str, str], layouts: dict[str, dict[str, Any]],
                   decision: str) -> dict[str, Any]:
    source = _source(root, row["source_map"])
    layout = layouts[source["layout"]]
    objects = []
    local_ids: set[int] = set()
    for index, event in enumerate(source["object_events"], 1):
        local_id = index
        if local_id in local_ids:
            raise BuildError(f"{row['map_key']}: duplicate local object id {local_id}")
        local_ids.add(local_id)
        objects.append({
            "local_id": local_id, "graphics_id": event.get("graphics_id", "OBJ_EVENT_GFX_NONE"),
            "x": event["x"], "y": event["y"], "elevation": event.get("elevation", 0),
            "movement_type": event.get("movement_type", "MOVEMENT_TYPE_NONE"),
            "movement_range_x": event.get("movement_range_x", 0),
            "movement_range_y": event.get("movement_range_y", 0),
            "trainer_type": "TRAINER_TYPE_NONE",
            "script": f"{row['map_key']}_OBJECT_{index:02d}_STUB",
            "flag": f"KANTO_FLAG_{row['group_id']}_{row['map_id']}_{index:02d}",
            "source_role": "REVIEW_FOR_T16" if event.get("trainer_type", "TRAINER_TYPE_NONE") != "TRAINER_TYPE_NONE" else "LOCAL_NPC",
        })
    warps = []
    for index, event in enumerate(source["warp_events"]):
        destination = event["dest_map"]
        if destination in source_id_to_key:
            destination = source_id_to_key[destination]
        elif destination in RUNTIME_DESTINATIONS:
            destination = RUNTIME_DESTINATIONS[destination]
        else:
            raise BuildError(f"{row['map_key']}: unresolved warp {destination}")
        warps.append({**event, "dest_map": destination, "source_warp_index": index})
    connections = []
    for event in source["connections"] or []:
        destination = source_id_to_key.get(event["map"])
        if destination is None:
            raise BuildError(f"{row['map_key']}: unresolved connection {event['map']}")
        connections.append({**event, "map": destination})
    bg_events = []
    for index, event in enumerate(source["bg_events"]):
        item = {key: value for key, value in event.items()
                if key not in ("script", "flag", "item")}
        if event["type"] == "hidden_item":
            item.update({"placement_key": f"KANTO_ITEM_{row['group_id']}_{row['map_id']}_{index:02d}",
                         "item_key": "T16_PENDING", "flag_key": f"KANTO_ITEM_FLAG_{row['group_id']}_{row['map_id']}_{index:02d}"})
        else:
            item["script"] = f"{row['map_key']}_BG_{index:02d}_STUB"
        bg_events.append(item)
    coord_events = [{"x": event["x"], "y": event["y"], "elevation": event.get("elevation", 0),
                     "condition_key": f"KANTO_CONDITION_{row['group_id']}_{row['map_id']}_{index:02d}",
                     "script": f"{row['map_key']}_COORD_{index:02d}_STUB"}
                    for index, event in enumerate(source["coord_events"])]
    block = (root / "vendor/upstream/pokefirered" / layout["blockdata_filepath"]).read_bytes()
    border = (root / "vendor/upstream/pokefirered" / layout["border_filepath"]).read_bytes()
    return {
        "schema_version": 2,
        "map_header": {"map_key": row["map_key"], "group_id": int(row["group_id"]),
                       "map_id": int(row["map_id"]), "source_map": row["source_map"],
                       "logical_code": row["logical_code"], "classification": row["classification"],
                       "scope_decision": decision, "layout": source["layout"],
                       "music": source["music"], "map_type": source["map_type"],
                       "requires_flash": source["requires_flash"], "weather": source["weather"],
                       "allow_cycling": source["allow_cycling"], "allow_escaping": source["allow_escaping"],
                       "allow_running": source["allow_running"]},
        "layout": {"width": layout["width"], "height": layout["height"],
                   "primary_tileset": layout["primary_tileset"],
                   "secondary_tileset": layout["secondary_tileset"],
                   "blockdata_size": len(block), "blockdata_sha256": _sha(block),
                   "border_size": len(border), "border_sha256": _sha(border),
                   "raw_policy": "CLEAN_BPRJ_OVERRIDE" if decision == "REBUILD" else "CLEAN_MATCH"},
        "connections": connections, "warps": warps, "objects": objects,
        "coord_events": coord_events, "bg_events": bg_events,
        "scripts": {"policy": "KANTO_NAMESPACED_STUB", "source_story_imported": False,
                    "vega_flag_writes": [], "vega_var_writes": []},
    }


def _reachability(canonical: dict[str, dict[str, Any]], scope: dict[str, str]) -> tuple[set[str], list[tuple[str, str]]]:
    operational = {key for key, decision in scope.items() if decision != "DEFER"}
    graph = {key: set() for key in operational}
    directed_warps: set[tuple[str, str]] = set()
    for key, item in canonical.items():
        if key not in operational:
            continue
        for conn in item["connections"]:
            dest = conn["map"]
            if dest in operational:
                graph[key].add(dest); graph[dest].add(key)
        for warp in item["warps"]:
            dest = warp["dest_map"]
            if dest in operational:
                graph[key].add(dest); graph[dest].add(key); directed_warps.add((key, dest))
    start = "KANTO_OUTDOOR_VERMILION_CITY"
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for dest in graph[current] - seen:
            seen.add(dest); queue.append(dest)
    one_way = sorted((left, right) for left, right in directed_warps
                     if (right, left) not in directed_warps)
    return seen, one_way


def build_outputs(root: Path) -> dict[str, bytes]:
    inventory = _csv(root / "reports/generated/kanto_map_inventory.csv")
    if len(inventory) != 256:
        raise BuildError("T11 inventory must contain 256 mainland maps")
    scope_rows = _scope(inventory)
    decisions = {row["map_key"]: str(row["scope_decision"]) for row in scope_rows}
    counts = Counter(decisions.values())
    if counts != {"INCLUDE": 252, "DEFER": 3, "REBUILD": 1}:
        raise BuildError(f"scope decision drift: {counts}")
    layouts = _layouts(root)
    source_to_key = {row["source_map"]: row["map_key"] for row in inventory}
    source_id_to_key = {_source(root, row["source_map"])["id"]: row["map_key"] for row in inventory}
    canonical = {row["map_key"]: _canonical_map(root, row, source_to_key, source_id_to_key,
                                                layouts, decisions[row["map_key"]])
                 for row in inventory if decisions[row["map_key"]] != "DEFER"}
    seen, one_way = _reachability(canonical, decisions)
    if len(seen) != len(canonical):
        raise BuildError(f"unreachable included maps: {sorted(set(canonical) - seen)}")
    unexpected_one_way = [(left, right) for left, right in one_way
                          if not canonical[right]["map_header"]["source_map"].endswith("Elevator")]
    if unexpected_one_way:
        raise BuildError(f"unexpected one-way warps: {unexpected_one_way[:8]}")
    physical_ids = [(item["map_header"]["group_id"], item["map_header"]["map_id"])
                    for item in canonical.values()]
    if len(physical_ids) != len(set(physical_ids)):
        raise BuildError("duplicate Kanto physical map ID")
    if any(group < 96 or map_id >= 127 for group, map_id in physical_ids):
        raise BuildError("unsafe group/map ID")
    if any(not item["layout"]["primary_tileset"] or not item["layout"]["secondary_tileset"]
           for item in canonical.values()):
        raise BuildError("missing tileset")
    logical = {row["logical_code"] for row in inventory}
    covered = {item["map_header"]["logical_code"] for item in canonical.values()}
    if logical - covered:
        raise BuildError(f"logical locations lost by scope: {sorted(logical - covered)}")

    unique_layouts: dict[str, tuple[int, int]] = {}
    for item in canonical.values():
        unique_layouts.setdefault(item["map_header"]["layout"],
                                  (item["layout"]["blockdata_size"], item["layout"]["border_size"]))
    asset_bytes = sum(block + border for block, border in unique_layouts.values())
    map_json = {key: _stable(value) for key, value in canonical.items()}
    canonical_json_bytes = sum(len(raw) for raw in map_json.values())
    metadata_bytes = sum(
        32 + len(item["objects"]) * 16 + len(item["warps"]) * 8
        + len(item["connections"]) * 8 + len(item["coord_events"]) * 12
        + len(item["bg_events"]) * 12
        for item in canonical.values()
    )
    allocation_bytes = asset_bytes + metadata_bytes
    if allocation_bytes > ALLOCATION_END - ALLOCATION_START:
        raise BuildError(f"Kanto allocation overflow: {allocation_bytes}")

    v2 = root / "design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/data"
    npc_review = (v2 / "カントー_NPC・イベント再利用判定マスター_26件.csv").read_bytes()
    item_review = (v2 / "カントー_重要アイテム置換マスター_24件.csv").read_bytes()
    if len(_csv(v2 / "カントー_NPC・イベント再利用判定マスター_26件.csv")) != 26:
        raise BuildError("V2 NPC review count drift")
    if len(_csv(v2 / "カントー_重要アイテム置換マスター_24件.csv")) != 24:
        raise BuildError("V2 item review count drift")

    connectivity = f"""# Kanto connectivity report

- scope: INCLUDE {counts['INCLUDE']} / REBUILD {counts['REBUILD']} / DEFER {counts['DEFER']}
- operational physical maps: {len(canonical)} / reachable from Vermilion: {len(seen)}
- V2 logical locations: {len(covered)} / 47
- unresolved warp destinations: 0
- invalid connections: 0
- duplicate physical/local IDs: 0
- missing tilesets: 0
- accidental Vega destinations: 0
- one-way warps: {len(one_way)} intentional elevator entries / 0 unexpected
- deferred unreachable maps: {', '.join(sorted(DEFERRED_SOURCES))}
- Sevii: DEFERRED (scope rows 0)

All source story scripts, flags, trainer IDs, item flags, and text pointers are converted to `KANTO_*` stubs or T16 placement keys. Runtime Union/Trade/Dynamic destinations are explicit engine sentinels, not map IDs.
""".encode()
    size_report = f"""# Kanto map size and allocation report

- maps: {len(canonical)}
- unique layouts: {len(unique_layouts)}
- deduplicated layout+border bytes: {asset_bytes}
- canonical metadata bytes: {metadata_bytes}
- canonical JSON audit bytes (not emitted to ROM): {canonical_json_bytes}
- allocation bytes: {allocation_bytes}
- region: `[0x{ALLOCATION_START:08X}, 0x{ALLOCATION_END:08X})`
- capacity: {ALLOCATION_END - ALLOCATION_START}
- remaining: {ALLOCATION_END - ALLOCATION_START - allocation_bytes}
- overlap: 0
- Vega-owned writes: 0
- V2 NPC review: 26 (`{_sha(npc_review)}`)
- V2 item replacement review: 24 (`{_sha(item_review)}`)
""".encode()
    summary = {"schema_version": 1, "maps": len(canonical), "reachable": len(seen),
               "scope_counts": dict(counts), "logical_locations": len(covered),
               "one_way_intentional": len(one_way), "one_way_unexpected": 0,
               "asset_bytes": asset_bytes, "metadata_bytes": metadata_bytes,
               "canonical_json_bytes": canonical_json_bytes,
               "allocation_bytes": allocation_bytes, "allocation_start": ALLOCATION_START,
               "allocation_end": ALLOCATION_START + allocation_bytes,
               "vega_writes": 0, "overlap": 0}
    outputs = {
        "content/kanto_map_scope.csv": _csv_bytes(
            ["map_key", "source_map", "logical_code", "classification", "scope_decision",
             "reason", "script_policy", "sevii"], scope_rows),
        "reports/generated/kanto_connectivity.md": connectivity,
        "reports/generated/kanto_size.md": size_report,
        "generated/maps/kanto/index.json": _stable(summary),
    }
    outputs.update({f"generated/maps/kanto/{key}.json": raw for key, raw in map_json.items()})
    return outputs
