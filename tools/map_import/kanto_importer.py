"""FireRed mainland map inventory and one-map canonical import.

pokefirered is used only for names/structure.  Layout bytes are accepted only
when the pinned clean Japanese BPRJ ROM contains the same blockdata sequence.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any

GROUPS = {
    "OUTDOOR": (96, "KANTO_OUTDOOR"),
    "DUNGEON": (97, "KANTO_DUNGEON"),
    "INDOOR": (98, "KANTO_INDOOR"),
}
IMPORTED_SOURCE = "VermilionCity_House1"
IMPORTED_KEY = "KANTO_INDOOR_VERMILION_CITY_HOUSE1"
SAFE_RETURN = "KANTO_OUTDOOR_VERMILION_TERMINAL"


class BuildError(RuntimeError):
    pass


def _stable_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _csv_bytes(header: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _symbol(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).upper()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def mainland_sources(root: Path) -> list[tuple[str, str, str]]:
    """Return the frozen 256-map mainland scope in source order."""
    groups = _read_json(root / "vendor/upstream/pokefirered/data/maps/map_groups.json")
    result: list[tuple[str, str, str]] = []
    # The first 96 dungeon entries end at PowerPlant.  Remaining entries are Sevii.
    result.extend(("DUNGEON", "gMapGroup_Dungeons", name)
                  for name in groups["gMapGroup_Dungeons"][:96])
    # Town/city entries 0..11 and mainland routes 19..44.
    towns = groups["gMapGroup_TownsAndRoutes"]
    result.extend(("OUTDOOR", "gMapGroup_TownsAndRoutes", name)
                  for name in towns[:12] + towns[19:45])
    # Every indoor group through Route25 is mainland; later groups are Sevii.
    for group in groups["group_order"]:
        if group == "gMapGroup_IndoorSevenIsland":
            break
        if group.startswith("gMapGroup_Indoor"):
            result.extend(("INDOOR", group, name) for name in groups[group])
    if len(result) != 256:
        raise BuildError(f"mainland scope drift: {len(result)} != 256")
    return result


def _logical_location(name: str) -> str:
    for number in range(25, 0, -1):
        if name.startswith(f"Route{number}"):
            return f"K{number:02d}"
    prefixes = (
        ("ViridianForest", "K26"), ("MtMoon", "K27"),
        ("DiglettsCave", "K28"), ("SSAnne", "K29"),
        ("RockTunnel", "K30"), ("PokemonTower", "K31"),
        ("RocketHideout", "K32"), ("Celadon", "K33"),
        ("SafariZone_Center", "K34"), ("SafariZone_East", "K35"),
        ("SafariZone_North", "K36"), ("SafariZone_West", "K37"),
        ("SafariZone_SecretHouse", "K34"),
        ("Seafoam", "K38"), ("PokemonMansion", "K39"),
        ("PowerPlant", "K40"), ("SilphCo", "K41"),
        ("VictoryRoad", "K42"), ("PokemonLeague", "K42"),
        ("IndigoPlateau", "K42"), ("CeruleanCave", "K43"),
        ("Pewter", "K44"), ("Cinnabar", "K45"),
        ("Vermilion", "K46"), ("Pallet", "K47"),
        ("Viridian", "K26"), ("Cerulean", "K43"),
        ("Lavender", "K31"), ("Fuchsia", "K34"),
        ("Saffron", "K41"),
    )
    for prefix, key in prefixes:
        if name.startswith(prefix):
            return key
    # Underground paths connect their corresponding route-number gates.
    if name.startswith("UndergroundPath_North"):
        return "K05"
    if name.startswith("UndergroundPath_South"):
        return "K06"
    if name.startswith("UndergroundPath_West"):
        return "K07"
    if name.startswith("UndergroundPath_East"):
        return "K08"
    raise BuildError(f"physical map has no V2 logical owner: {name}")


def _v2_locations(root: Path) -> dict[str, str]:
    path = root / ("design/imported/VEGA_CFRU_DPE_統合設計_V2_二地方生態版/"
                   "data/二地方マップ別_出現レイヤーマスター_96地点.csv")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["region"] == "カントー"]
    result = {r["map_code"]: r["map_name"] for r in rows}
    if len(rows) != 47 or set(result) != {f"K{x:02d}" for x in range(1, 48)}:
        raise BuildError("V2 Kanto logical-location set drift")
    return result


def _layout_table(root: Path) -> dict[str, dict[str, Any]]:
    data = _read_json(root / "vendor/upstream/pokefirered/data/layouts/layouts.json")
    return {row["id"]: row for row in data["layouts"] if row.get("id")}


def _source_map(root: Path, name: str) -> dict[str, Any]:
    return _read_json(root / f"vendor/upstream/pokefirered/data/maps/{name}/map.json")


def _source_dependencies(root: Path, name: str) -> tuple[str, str]:
    base = root / f"vendor/upstream/pokefirered/data/maps/{name}"
    scripts = base / "scripts.inc"
    text = base / "text.inc"
    return (str(scripts.relative_to(root)) if scripts.is_file() else "NONE",
            str(text.relative_to(root)) if text.is_file() else "NONE")


def _find_raw_layout(root: Path, clean: bytes, layout: dict[str, Any]) -> tuple[str, int, str]:
    block = (root / "vendor/upstream/pokefirered" / layout["blockdata_filepath"]).read_bytes()
    offset = clean.find(block)
    if offset < 0:
        return "CLEAN_OVERRIDE_REQUIRED", -1, _sha(block)
    return "MATCH", offset, _sha(clean[offset:offset + len(block)])


def _canonical_import(root: Path, clean: bytes, layouts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = _source_map(root, IMPORTED_SOURCE)
    layout = layouts[source["layout"]]
    status, offset, block_sha = _find_raw_layout(root, clean, layout)
    if status != "MATCH":
        raise BuildError("vertical-slice layout is not present in clean Japanese ROM")
    block = (root / "vendor/upstream/pokefirered" / layout["blockdata_filepath"]).read_bytes()
    border = (root / "vendor/upstream/pokefirered" / layout["border_filepath"]).read_bytes()
    objects = []
    for index, event in enumerate(source["object_events"]):
        item = dict(event)
        item["script"] = f"{IMPORTED_KEY}_LOCAL_TALK_{index:02d}"
        item["flag"] = "FLAG_NONE"
        objects.append(item)
    warps = [{**event, "dest_map": SAFE_RETURN, "dest_warp_id": "0"}
             for event in source["warp_events"]]
    canonical = {
        "schema_version": 1,
        "map_header": {
            "map_key": IMPORTED_KEY, "group_id": GROUPS["INDOOR"][0], "map_id": 0,
            "source_map": IMPORTED_SOURCE, "layout_key": f"{IMPORTED_KEY}_LAYOUT",
            "music": source["music"], "region_map_section": source["region_map_section"],
            "requires_flash": source["requires_flash"], "weather": source["weather"],
            "map_type": source["map_type"], "allow_cycling": source["allow_cycling"],
            "allow_escaping": source["allow_escaping"], "allow_running": source["allow_running"],
            "show_map_name": source["show_map_name"], "floor_number": source["floor_number"],
            "battle_scene": source["battle_scene"],
        },
        "layout": {
            "width": layout["width"], "height": layout["height"],
            "border_width": layout["border_width"], "border_height": layout["border_height"],
            "primary_tileset": layout["primary_tileset"],
            "secondary_tileset": layout["secondary_tileset"],
            "blockdata_sha256": block_sha, "blockdata_size": len(block),
            "clean_bprj_offset": offset, "border_sha256": _sha(border),
            "border_size": len(border),
        },
        "connections": [], "warps": warps, "objects": objects,
        "coord_events": list(source["coord_events"]), "bg_events": list(source["bg_events"]),
        "map_scripts": [],
        "scripts": [{"symbol": f"{IMPORTED_KEY}_LOCAL_TALK_00", "kind": "LOCAL_FLAVOR_STUB",
                     "operations": ["lock", "faceplayer", "msgbox", "release", "end"]}],
        "text": [{"symbol": f"{IMPORTED_KEY}_TEXT_FISHING_RESEARCH",
                  "locale": "ja", "text_key": "TEXT_KANTO_FISHING_RESEARCH"}],
        "wild_header": None,
        "safety": {"original_story_scripts_imported": False, "global_flags": [], "global_vars": [],
                   "warp_policy": "UNIMPORTED_DESTINATIONS_TO_SAFE_RETURN"},
    }
    return canonical


def _roundtrip(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(_stable_json(value))


def build_outputs(root: Path) -> dict[str, bytes]:
    clean_path = root / "userfile/imports/roms/Pocket Monsters - FireRed (Japan).gba"
    clean = clean_path.read_bytes()
    layouts = _layout_table(root)
    logical = _v2_locations(root)
    sources = mainland_sources(root)
    counters = {kind: 0 for kind in GROUPS}
    records: list[dict[str, Any]] = []
    raw_cache: dict[str, tuple[str, int, str]] = {}
    for kind, source_group, name in sources:
        source = _source_map(root, name)
        layout = layouts[source["layout"]]
        raw_cache.setdefault(source["layout"], _find_raw_layout(root, clean, layout))
        raw_status, raw_offset, raw_sha = raw_cache[source["layout"]]
        group_id, group_key = GROUPS[kind]
        map_id = counters[kind]
        counters[kind] += 1
        map_key = f"{group_key}_{_symbol(name)}"
        scripts, text = _source_dependencies(root, name)
        records.append({
            "map_key": map_key, "group_id": group_id, "map_id": map_id,
            "source_group": source_group, "source_map": name, "classification": kind,
            "logical_code": _logical_location(name), "layout": source["layout"],
            "width": layout["width"], "height": layout["height"],
            "primary_tileset": layout["primary_tileset"],
            "secondary_tileset": layout["secondary_tileset"],
            "object_count": len(source["object_events"]), "warp_count": len(source["warp_events"]),
            "coord_count": len(source["coord_events"]), "bg_count": len(source["bg_events"]),
            "connection_count": len(source["connections"] or []), "scripts": scripts, "text": text,
            "raw_status": raw_status, "raw_offset": raw_offset, "raw_sha256": raw_sha,
            "status": "IMPORTED" if name == IMPORTED_SOURCE else "RESERVED",
        })
    if counters != {"OUTDOOR": 38, "DUNGEON": 96, "INDOOR": 122}:
        raise BuildError(f"classification drift: {counters}")
    if len(raw_cache) != 180 or sum(v[0] == "MATCH" for v in raw_cache.values()) != 179:
        raise BuildError("clean BPRJ layout proof drift")
    if {r["logical_code"] for r in records} != set(logical):
        raise BuildError("not every V2 logical location has a physical map")

    imported = _canonical_import(root, clean, layouts)
    roundtripped = _roundtrip(imported)
    if imported != roundtripped:
        raise BuildError("canonical round-trip changed structure")

    map_ids = [{"map_key": r["map_key"], "group_id": r["group_id"], "map_id": r["map_id"],
                "source_map": r["source_map"], "classification": f"KANTO_{r['classification']}",
                "status": r["status"], "notes": "新規namespace。Vega mapを置換しない"}
               for r in records]
    kanto_maps = [{"map_key": r["map_key"], "source_map": r["source_map"], "scope": "MAINLAND",
                   "import_mode": "CANONICAL_IMPORT" if r["status"] == "IMPORTED" else "RESERVED",
                   "preserve_npcs": "yes", "preserve_local_events": "stub",
                   "status": r["status"], "notes": f"V2={r['logical_code']}; layout={r['layout']}"}
                  for r in records]
    inventory_header = ["map_key", "group_id", "map_id", "source_group", "source_map",
                        "classification", "logical_code", "layout", "width", "height",
                        "primary_tileset", "secondary_tileset", "object_count", "warp_count",
                        "coord_count", "bg_count", "connection_count", "scripts", "text",
                        "raw_status", "raw_offset", "raw_sha256", "status"]
    cross_header = ["logical_code", "logical_name", "physical_map_key", "source_map", "layout",
                    "primary_tileset", "secondary_tileset", "warp_dependencies",
                    "connection_dependencies", "script_dependency", "text_dependency", "new_group_id", "new_map_id"]
    cross = [{"logical_code": r["logical_code"], "logical_name": logical[r["logical_code"]],
              "physical_map_key": r["map_key"], "source_map": r["source_map"], "layout": r["layout"],
              "primary_tileset": r["primary_tileset"], "secondary_tileset": r["secondary_tileset"],
              "warp_dependencies": r["warp_count"], "connection_dependencies": r["connection_count"],
              "script_dependency": r["scripts"], "text_dependency": r["text"],
              "new_group_id": r["group_id"], "new_map_id": r["map_id"]} for r in records]
    imported_raw = _stable_json(imported)
    roundtrip_raw = _stable_json(roundtripped)
    source_house = _source_map(root, IMPORTED_SOURCE)
    report = f"""# Kanto map round-trip report

- source: `{IMPORTED_SOURCE}`
- destination: `{IMPORTED_KEY}` (`98/0`)
- Vega既存group範囲: `0..42`（T02 `vega_map_inventory.csv`）
- clean BPRJ SHA-256: `{_sha(clean)}`
- canonical SHA-256: `{_sha(imported_raw)}`
- re-export SHA-256: `{_sha(roundtrip_raw)}`
- structural diff: `NONE`

## Structure

| Item | Source | Imported | Result |
|---|---:|---:|---|
| width x height | {imported['layout']['width']} x {imported['layout']['height']} | {roundtripped['layout']['width']} x {roundtripped['layout']['height']} | PASS |
| blockdata bytes | {imported['layout']['blockdata_size']} | {roundtripped['layout']['blockdata_size']} | PASS |
| objects | {len(source_house['object_events'])} | {len(imported['objects'])} | PASS |
| warps | {len(source_house['warp_events'])} | {len(imported['warps'])} | PASS |
| connections | 0 | {len(imported['connections'])} | PASS |

`map.bin` はclean日本版ROMの `0x{imported['layout']['clean_bprj_offset']:X}` でbyte一致した。collision/elevationを含むblockdata、tileset、border、NPC座標を保持した。未取込先warpは `{SAFE_RETURN}` へ明示remapした。原作の `FLAG_GOT_OLD_ROD` / `VAR_RESULT` と英語textは取り込まず、名前空間化した日本語local flavor stubだけを残した。

## Scope proof

- physical maps: 256 (outdoor 38 / dungeon 96 / indoor 122)
- unique layouts: 180
- clean BPRJ blockdata match: 179 / 180 (`Route11` はclean raw再抽出待ち)
- V2 logical locations: 47 / 47 covered
- Sevii: deferred; manifestには含めない
""".encode()
    outputs = {
        "manifests/map_ids.csv": _csv_bytes(
            ["map_key", "group_id", "map_id", "source_map", "classification", "status", "notes"], map_ids),
        "manifests/kanto_maps.csv": _csv_bytes(
            ["map_key", "source_map", "scope", "import_mode", "preserve_npcs", "preserve_local_events", "status", "notes"], kanto_maps),
        "reports/generated/kanto_map_inventory.csv": _csv_bytes(inventory_header, records),
        "reports/generated/kanto_v2_crosswalk.csv": _csv_bytes(cross_header, cross),
        "reports/generated/map_roundtrip.md": report,
        f"generated/maps/{IMPORTED_KEY}.json": imported_raw,
        f"generated/maps/{IMPORTED_KEY}.roundtrip.json": roundtrip_raw,
    }
    return outputs
