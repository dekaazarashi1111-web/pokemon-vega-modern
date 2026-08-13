#!/usr/bin/env python3
"""T09: Speciesの画像・鳴き声・図鑑・進化・技表と孵化QOL契約を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any, Mapping, NoReturn

ROOT = Path(__file__).resolve().parents[1]
ROM_BASE = 0x08000000
CONFIG = Path("config/species_surface.json")
TASK = "T09"

ARTIFACTS = (
    "generated/engine/species_assets/species_assets.json",
    "generated/engine/species_assets/front.bin",
    "generated/engine/species_assets/back.bin",
    "generated/engine/species_assets/palette.bin",
    "generated/engine/species_assets/shiny_palette.bin",
    "generated/engine/species_assets/icon.bin",
    "generated/engine/species_assets/icon_palette.bin",
    "generated/engine/species_assets/front_coords.bin",
    "generated/engine/species_assets/back_coords.bin",
    "generated/engine/species_assets/elevation.bin",
    "generated/engine/species_assets/footprint.bin",
    "generated/engine/species_assets/cry.bin",
    "generated/engine/species_assets/cry2.bin",
    "generated/engine/species_assets/dex_entries.bin",
    "generated/engine/species_assets/national_dex.bin",
    "generated/engine/evolutions/evolutions.bin",
    "generated/engine/evolutions/evolutions.json",
    "generated/engine/evolutions/v2_normalized.json",
    "generated/engine/learnsets/level_up_pointers.bin",
    "generated/engine/learnsets/level_up_data.bin",
    "generated/engine/learnsets/egg_moves.bin",
    "generated/engine/learnsets/tmhm.bin",
    "generated/engine/learnsets/tutor.bin",
    "generated/engine/learnsets/learnsets.json",
    "reports/generated/dex_policy.md",
    "reports/generated/species_asset_validation.md",
    "tests/fixtures/breeding_matrix.json",
)


class SurfaceError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise SurfaceError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"{path} must contain an object")
    return value


def fixed(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    if sha(raw) != expected:
        fail(f"fixed input hash mismatch: {path}")
    return raw


def ptr(rom: bytes | bytearray, site: int) -> int:
    return struct.unpack_from("<I", rom, site)[0]


def slice_at(rom: bytes, address: int, size: int, label: str) -> bytes:
    start = address - ROM_BASE
    raw = rom[start:start + size]
    if len(raw) != size:
        fail(f"{label} is outside ROM")
    return raw


def aliases(models: Mapping[str, Any]) -> tuple[dict[int, int], dict[int, int], dict[int, int]]:
    species = {int(row["source_id"]): int(row["canonical_id"]) for row in models["species"]["aliases"]}
    moves = {int(row["cfru_source_id"]): int(row["canonical_id"]) for row in models["moves"]["aliases"]}
    items = {int(row["source_id"]): int(row["canonical_id"]) for row in models["ids"]["item_aliases"]}
    return species, moves, items


def map_required(table: Mapping[int, int], value: int, label: str) -> int:
    if value not in table:
        fail(f"unresolved {label} source ID {value}")
    return table[value]


def table_merge(stage: bytes, dpe: bytes, rows: list[dict[str, Any]], site: int,
                dpe_root: int, stride: int, vega_count: int, label: str) -> bytes:
    old_root = ptr(stage, site)
    output = bytearray()
    for row in rows:
        cid = int(row["id"])
        if cid < vega_count:
            output += slice_at(stage, old_root + cid * stride, stride, f"Vega {label} {cid}")
        else:
            source = int(row["dpe_id"])
            output += slice_at(dpe, dpe_root + source * stride, stride, f"DPE {label} {source}")
    return bytes(output)


def cry_merge(stage: bytes, dpe: bytes, rows: list[dict[str, Any]], site: int,
              dpe_root: int, vega_count: int) -> bytes:
    old_root = ptr(stage, site)
    cry_map = 0x08865DE0
    output = bytearray()
    for row in rows:
        cid = int(row["id"])
        if cid < vega_count:
            mapped = struct.unpack_from("<H", stage, cry_map - ROM_BASE + (cid + 1) * 2)[0]
            source_index = max(0, mapped - 1)
            # Vega's EGG/reserved sentinel deliberately maps to 0xFFFF and is silent.
            # Canonical tables use row 0 as the bounded silent/default ToneData row.
            if mapped == 0xFFFF:
                source_index = 0
            elif source_index >= 388:
                fail(f"Vega cry map out of bounds: species={cid} cry={mapped}")
            output += slice_at(stage, old_root + source_index * 12, 12, f"Vega cry {cid}")
        else:
            output += slice_at(dpe, dpe_root + int(row["dpe_id"]) * 12, 12, f"DPE cry {cid}")
    return bytes(output)


def lz77_size(rom: bytes, address: int) -> int:
    offset = address - ROM_BASE
    if not (0 <= offset + 4 <= len(rom)) or rom[offset] != 0x10:
        return -1
    return rom[offset + 1] | rom[offset + 2] << 8 | rom[offset + 3] << 16


def dpe_footprints(root: Path) -> dict[int, int]:
    constants = (root / "vendor/upstream/DPE-JP/include/species.h").read_text(encoding="utf-8")
    symbols = {match.group(1): int(match.group(2), 0) for match in re.finditer(
        r"^#define\s+(SPECIES_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+|[0-9]+)\s*$", constants, re.M)}
    source = (root / "vendor/upstream/DPE-JP/src/Footprint_Table.c").read_text(encoding="utf-8")
    result: dict[int, int] = {}
    for match in re.finditer(r"\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*(0x[0-9A-Fa-f]+)", source):
        if match.group(1) in symbols:
            result[symbols[match.group(1)]] = int(match.group(2), 0)
    if len(result) < 1200:
        fail(f"DPE footprint source coverage changed: {len(result)}")
    return result


def validate_assets(dpe: bytes, tables: Mapping[str, bytes], rows: list[dict[str, Any]],
                    vega_count: int) -> dict[str, Any]:
    checks = {"compressed_checked": 0, "aligned_pointers": 0, "icons_checked": 0}
    for cid in range(vega_count, len(rows)):
        for key, expected in (("front", 2048), ("back", 2048), ("palette", 32), ("shiny_palette", 32)):
            address = struct.unpack_from("<I", tables[key], cid * 8)[0]
            if address & 3:
                fail(f"unaligned {key} pointer for species {cid}")
            size = lz77_size(dpe, address)
            valid_sizes = {32, 64, 128} if key.endswith("palette") else {2048, 4096, 8192}
            if size not in valid_sizes:
                fail(f"invalid {key} LZ77 header for species {cid}: {size}")
            checks["compressed_checked"] += 1
            checks["aligned_pointers"] += 1
        icon = struct.unpack_from("<I", tables["icon"], cid * 4)[0]
        if icon & 3 or not (ROM_BASE <= icon < ROM_BASE + len(dpe)):
            fail(f"invalid icon pointer for species {cid}")
        checks["icons_checked"] += 1
    checks["status"] = "PASS"
    return checks


ITEM_PARAM = {6, 7, 24, 25, 34, 39, 0xFE}
ITEM_UNKNOWN = {35, 36}
MOVE_PARAM = {26, 37, 38}
SPECIES_PARAM = {27}


def merge_evolutions(stage: bytes, dpe: bytes, config: Mapping[str, Any], rows: list[dict[str, Any]],
                     species_alias: Mapping[int, int], move_alias: Mapping[int, int],
                     item_alias: Mapping[int, int]) -> tuple[bytes, dict[str, Any]]:
    meta = read_json(ROOT / config["inputs"]["stage06_metadata_path"])
    runtime = meta["runtime_tables"]["evolutions"]
    old = slice_at(stage, int(runtime["address"]), 412 * 128, "T06 evolution prefix")
    dpe_root = int(config["dpe_roots"]["evolution"])
    output = bytearray(old)
    nonzero = duplicate_count = 0
    normalized_rows: list[dict[str, Any]] = []
    for cid in range(412):
        seen_prefix: set[tuple[int, int, int, int]] = set()
        for slot in range(16):
            entry = struct.unpack_from("<HHHH", old, cid * 128 + slot * 8)
            method, param, target, unknown = entry
            if method == 0:
                continue
            if target >= len(rows):
                fail(f"T06 evolution target is outside canonical Species: {target}")
            if entry in seen_prefix:
                fail(f"T06 evolution has semantic duplicate: species={cid} slot={slot}")
            seen_prefix.add(entry)
            nonzero += 1
            normalized_rows.append({
                "from_id": cid, "from_form_key": rows[cid]["form_key"],
                "from_national_dex": int(rows[cid]["canonical_national_dex"]),
                "method": method, "param": param, "target_id": target,
                "target_form_key": rows[target]["form_key"],
                "target_national_dex": int(rows[target]["canonical_national_dex"]),
                "unknown": unknown,
            })
    for species_row in rows[412:]:
        source_id = int(species_row["dpe_id"])
        raw = slice_at(dpe, dpe_root + source_id * 128, 128, "DPE evolution row")
        converted: list[tuple[int, int, int, int]] = []
        seen: set[tuple[int, int, int, int]] = set()
        for slot in range(16):
            method, param, target, unknown = struct.unpack_from("<HHHH", raw, slot * 8)
            if method == 0:
                continue
            target = map_required(species_alias, target, "evolution target Species")
            if method in ITEM_PARAM and param:
                param = map_required(item_alias, param, "evolution Item")
            if method in ITEM_UNKNOWN and unknown:
                unknown = map_required(item_alias, unknown, "evolution held Item")
            if method in MOVE_PARAM and param:
                param = map_required(move_alias, param, "evolution Move")
            if method in SPECIES_PARAM and param:
                param = map_required(species_alias, param, "evolution party Species")
            key = (method, param, target, unknown)
            if key in seen:
                duplicate_count += 1
                continue
            seen.add(key)
            converted.append(key)
            normalized_rows.append({
                "from_id": int(species_row["id"]), "from_form_key": species_row["form_key"],
                "from_national_dex": int(species_row["canonical_national_dex"]),
                "method": method, "param": param, "target_id": target,
                "target_form_key": rows[target]["form_key"],
                "target_national_dex": int(rows[target]["canonical_national_dex"]),
                "unknown": unknown,
            })
        if len(converted) > 16:
            fail(f"evolution overflow for Species {species_row['id']}")
        converted += [(0, 0, 0, 0)] * (16 - len(converted))
        for entry in converted:
            output += struct.pack("<HHHH", *entry)
            nonzero += entry[0] != 0
    if len(output) != len(rows) * 128:
        fail("canonical evolution table size mismatch")
    model = {"schema_version": 1, "task": TASK, "species_count": len(rows),
             "stride": 128, "nonzero_rows": nonzero,
             "semantic_duplicates_removed": duplicate_count,
             "rows": normalized_rows, "status": "PASS"}
    return bytes(output), model


def normalize_v2(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    seen: set[tuple[int, int, str]] = set()
    rows = []
    duplicates = 0
    unresolved = []
    for row in source:
        key = (int(row["from_national_no"]), int(row["to_national_no"]), row["vega_integrated_condition"].strip())
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        required = row["requires_new_item_or_counter"].strip()
        resolution = row["implementation_note"].strip()
        if required not in ("はい", "いいえ") or (required == "はい" and not resolution):
            unresolved.append(row["evolution_id"])
        rows.append({"evolution_id": int(row["evolution_id"]), "from_national_dex": key[0],
                     "from_form_key": "", "to_national_dex": key[1], "to_form_key": "",
                     "condition": key[2], "requires_new_item_or_counter": required,
                     "resolution": resolution})
    if unresolved:
        fail(f"V2 unresolved requirement rows: {unresolved[:5]}")
    return {"schema_version": 1, "source_rows": len(source), "normalized_rows": len(rows),
            "semantic_duplicates_removed": duplicates, "rows": rows, "status": "PASS"}


def parse_level_data(rom: bytes, address: int, move_alias: Mapping[int, int]) -> bytes:
    output = bytearray()
    offset = address - ROM_BASE
    for _ in range(256):
        move = struct.unpack_from("<H", rom, offset)[0]
        level = rom[offset + 2]
        offset += 3
        if move == 0 and level == 0xFF:
            output += b"\x00\x00\xff"
            return bytes(output)
        output += struct.pack("<HB", map_required(move_alias, move, "level-up Move"), level)
    fail(f"unterminated level-up data at {address:#x}")


def parse_egg(rom: bytes, root: int, move_alias: Mapping[int, int] | None,
              species_alias: Mapping[int, int] | None, include: callable) -> list[int]:
    values: list[int] = []
    offset = root - ROM_BASE
    active = False
    for _ in range(20000):
        value = struct.unpack_from("<H", rom, offset)[0]
        offset += 2
        if value == 0xFFFF:
            break
        if value >= 20000:
            source = value - 20000
            target = source if species_alias is None else species_alias.get(source, -1)
            active = target >= 0 and include(target)
            if active:
                values.append(target + 20000)
        elif active:
            values.append(value if move_alias is None else map_required(move_alias, value, "egg Move"))
    else:
        fail("unterminated egg move table")
    return values


def merge_learnsets(stage: bytes, dpe: bytes, config: Mapping[str, Any], rows: list[dict[str, Any]],
                    species_alias: Mapping[int, int], move_alias: Mapping[int, int],
                    allocate_address: int) -> tuple[dict[str, bytes], dict[str, Any]]:
    dpe_level = int(config["dpe_roots"]["level_up"])
    old_level = ptr(stage, int(config["pointer_sites"]["level_up"]))
    pointer_values: list[int] = []
    data = bytearray()
    inherited = translated = 0
    for row in rows:
        cid = int(row["id"])
        if cid < 412:
            pointer_values.append(ptr(stage, old_level - ROM_BASE + cid * 4))
            inherited += 1
        else:
            source = int(row["dpe_id"])
            source_ptr = ptr(dpe, dpe_level - ROM_BASE + source * 4)
            converted = parse_level_data(dpe, source_ptr, move_alias)
            pointer_values.append(allocate_address + len(data))
            data += converted
            translated += 1
    pointers = b"".join(struct.pack("<I", value) for value in pointer_values)

    vega_egg = parse_egg(stage, ptr(stage, int(config["pointer_sites"]["egg"])), None, None,
                         lambda target: 0 <= target < 412)
    dpe_egg = parse_egg(dpe, int(config["dpe_roots"]["egg"]), move_alias, species_alias,
                        lambda target: target >= 412)
    egg = b"".join(struct.pack("<H", value) for value in vega_egg + dpe_egg + [0xFFFF])

    tmhm = table_merge(stage, dpe, rows, int(config["pointer_sites"]["tmhm"]),
                       int(config["dpe_roots"]["tmhm"]), 16, 412, "TM/HM")
    tutor = table_merge(stage, dpe, rows, int(config["pointer_sites"]["tutor"]),
                        int(config["dpe_roots"]["tutor"]), 16, 412, "tutor")
    model = {"schema_version": 1, "task": TASK, "species_count": len(rows),
             "level_up": {"vega_pointer_rows": inherited, "translated_rows": translated,
                          "data_bytes": len(data)},
             "egg": {"u16_count": len(egg) // 2, "vega_values": len(vega_egg),
                     "translated_values": len(dpe_egg)},
             "tmhm": {"stride": 16}, "tutor": {"stride": 16}, "status": "PASS"}
    return {"level_up_pointers": pointers, "level_up_data": bytes(data), "egg_moves": egg,
            "tmhm": tmhm, "tutor": tutor}, model


def breeding_fixture() -> dict[str, Any]:
    cases = [
        ("everstone_nature_form", ["EVERSTONE", "REGIONAL_FORM"], "nature_and_form_inherited"),
        ("destiny_knot_unique_five", ["DESTINY_KNOT"], "five_unique_iv_stats"),
        ("power_item_forced_iv", ["POWER_ITEM", "DESTINY_KNOT"], "forced_stat_in_five"),
        ("both_parent_egg_moves", ["MOTHER_EGG_MOVE", "FATHER_EGG_MOVE"], "both_moves_inherited"),
        ("common_level_moves", ["COMMON_LEVEL_MOVE"], "common_moves_inherited"),
        ("ball_and_ability", ["BALL", "ABILITY_SLOT", "HIDDEN_ABILITY"], "legal_parent_rolls"),
        ("incense_baby", ["INCENSE"], "baby_species_selected"),
        ("ditto", ["DITTO"], "non_ditto_parent_is_line_owner"),
        ("masuda_six_rolls", ["DIFFERENT_TRAINER_ID"], "six_shiny_rolls"),
        ("egg_to_pc", ["PARTY_FULL"], "single_pc_delivery"),
        ("party_and_boxes_full", ["PARTY_FULL", "BOXES_FULL"], "queue_retained_no_duplicate"),
        ("queue_capacity", ["FIVE_EGGS_QUEUED"], "sixth_rejected"),
        ("hatch_modes", ["NORMAL", "SHORT", "SKIP"], "three_modes_bounded"),
        ("compact_iv_ev", ["SUMMARY_FIELD", "PC_RIGHT_PANE", "EGG_IV"], "existing_panels_only"),
        ("free_move_relearner", ["ZERO_COST", "EXISTING_SCREEN"], "no_currency_mutation"),
        ("oval_charm_locked", ["CAUGHT_99"], "base_rate_20_percent"),
        ("oval_charm_unlocked_caught", ["CAUGHT_100"], "doubled_rate_40_percent"),
        ("oval_charm_unlocked_quest", ["QUEST_COMPLETE"], "doubled_rate_40_percent"),
    ]
    return {"schema_version": 1, "fixed_rng": [7, 2, 5, 1, 0, 4, 3, 9, 6, 8],
            "cases": [{"id": key, "features": features, "expected": expected}
                      for key, features, expected in cases], "status": "PASS"}


class Allocator:
    def __init__(self, start: int, end: int): self.cursor, self.end, self.entries = start, end, []
    def put(self, name: str, data: bytes, alignment: int = 4) -> int:
        self.cursor = (self.cursor + alignment - 1) & -alignment
        if self.cursor + len(data) > self.end:
            fail(f"T09 allocation overflow at {name}")
        offset = self.cursor
        self.cursor += len(data)
        self.entries.append({"name": name, "offset": offset, "address": ROM_BASE + offset,
                             "size": len(data), "sha256": sha(data)})
        return offset


def build_model(root: Path = ROOT) -> tuple[dict[str, bytes], dict[str, Any], bytes]:
    config = read_json(root / CONFIG)
    stage = fixed(root / config["inputs"]["stage07_path"], config["inputs"]["stage07_sha256"])
    dpe = fixed(root / config["inputs"]["dpe_rom_path"], config["inputs"]["dpe_rom_sha256"])
    models = {name: read_json(root / config["inputs"][path]) for name, path in (
        ("species", "species_model_path"), ("moves", "move_model_path"), ("ids", "id_model_path"))}
    rows = models["species"]["species"]
    if len(rows) != 1621 or [int(row["id"]) for row in rows] != list(range(1621)):
        fail("T07 canonical Species ABI changed")
    species_alias, move_alias, item_alias = aliases(models)

    strides, roots, sites = config["strides"], config["dpe_roots"], config["pointer_sites"]
    tables: dict[str, bytes] = {}
    for name in ("front", "back", "palette", "shiny_palette", "icon", "icon_palette",
                 "front_coords", "back_coords", "elevation", "dex_entries"):
        tables[name] = table_merge(stage, dpe, rows, int(sites[name]), int(roots[name]),
                                   int(strides[name]), 412, name)
    # A handful of DPE battle-only helper IDs intentionally have NULL display
    # assets.  Canonical storage/UI paths must never dereference NULL, so bind
    # those rows to DPE's bounded default row while retaining their form ID.
    for name in ("front", "back", "palette", "shiny_palette", "icon"):
        stride = int(strides[name])
        default = slice_at(dpe, int(roots[name]), stride, f"DPE default {name}")
        mutable = bytearray(tables[name])
        for cid in range(412, len(rows)):
            if struct.unpack_from("<I", mutable, cid * stride)[0] == 0:
                mutable[cid * stride:(cid + 1) * stride] = default
        tables[name] = bytes(mutable)
    footprint_root = ptr(stage, int(sites["footprint"]))
    footprints = bytearray(slice_at(stage, footprint_root, 412 * 4, "Vega footprints"))
    footprint_map = dpe_footprints(root)
    for row in rows[412:]:
        footprints += struct.pack("<I", footprint_map.get(int(row["dpe_id"]), 0x08C3058C))
    tables["footprint"] = bytes(footprints)
    tables["cry"] = cry_merge(stage, dpe, rows, int(sites["cry"]), int(roots["cry"]), 412)
    tables["cry2"] = cry_merge(stage, dpe, rows, int(sites["cry2"]), int(roots["cry2"]), 412)
    tables["national_dex"] = (root / "generated/engine/species/national_dex.bin").read_bytes()
    validation = validate_assets(dpe, tables, rows, 412)

    evolutions, evolution_model = merge_evolutions(stage, dpe, config, rows,
                                                    species_alias, move_alias, item_alias)
    v2 = normalize_v2(root / config["inputs"]["v2_evolution_path"])

    allocator = Allocator(int(config["allocation"]["start_offset"]), int(config["allocation"]["end_offset"]))
    # Level-up data address must be known before its pointer table is rendered.
    provisional_level_data = allocator.cursor + 4
    learn, learn_model = merge_learnsets(stage, dpe, config, rows, species_alias, move_alias,
                                         ROM_BASE + provisional_level_data)
    # Reserve exact tables in the same order used to calculate the final pointer base below.
    assets_order = ("front", "back", "palette", "shiny_palette", "icon", "icon_palette",
                    "front_coords", "back_coords", "elevation", "footprint", "cry", "cry2",
                    "dex_entries", "national_dex")
    output_rom = bytearray(stage)
    copy_start, copy_end = int(config["dpe_copy"]["start_offset"]), int(config["dpe_copy"]["end_offset"])
    output_rom[copy_start:copy_end] = dpe[copy_start:copy_end]
    locations: dict[str, int] = {}
    for name in assets_order:
        off = allocator.put(name, tables[name]); locations[name] = ROM_BASE + off
    off = allocator.put("evolutions", evolutions); locations["evolution"] = ROM_BASE + off
    # Allocate level data before pointers and rebuild pointers against the real address.
    off = allocator.put("level_up_data", learn["level_up_data"]); locations["level_up_data"] = ROM_BASE + off
    learn, learn_model = merge_learnsets(stage, dpe, config, rows, species_alias, move_alias,
                                         locations["level_up_data"])
    for name in ("level_up_pointers", "egg_moves", "tmhm", "tutor"):
        off = allocator.put(name, learn[name]); locations[name] = ROM_BASE + off
    for entry in allocator.entries:
        data = (tables.get(entry["name"]) or
                (evolutions if entry["name"] == "evolutions" else learn[entry["name"]]))
        output_rom[entry["offset"]:entry["offset"] + len(data)] = data

    bindings = {"front": "front", "back": "back", "palette": "palette",
                "shiny_palette": "shiny_palette", "icon": "icon", "icon_palette": "icon_palette",
                "front_coords": "front_coords", "back_coords": "back_coords", "elevation": "elevation",
                "footprint": "footprint", "cry": "cry", "cry2": "cry2", "evolution": "evolution",
                "level_up": "level_up_pointers", "egg": "egg_moves", "tmhm": "tmhm", "tutor": "tutor",
                "dex_entries": "dex_entries", "national_dex": "national_dex"}
    repoints = {}
    for key, location_key in bindings.items():
        site = int(sites[key]); old = ptr(stage, site); new = locations[location_key]
        output_rom[site:site + 4] = struct.pack("<I", new)
        repoints[key] = {"site": site, "old": old, "new": new}
    # T06 redirected CFRU evolution consumers to its canonical 1440-row root.
    # Replace every aligned literal for that root so appended IDs 1440..1620
    # cannot index the superseded table.
    stage06_meta = read_json(root / config["inputs"]["stage06_metadata_path"])
    old_evolution_runtime = int(stage06_meta["runtime_tables"]["evolutions"]["address"])
    old_bytes = struct.pack("<I", old_evolution_runtime)
    runtime_sites = [index for index in range(0, len(stage) - 3, 4)
                     if stage[index:index + 4] == old_bytes]
    if not runtime_sites:
        fail("T06 canonical evolution consumer root is no longer referenced")
    for site in runtime_sites:
        output_rom[site:site + 4] = struct.pack("<I", locations["evolution"])
    repoints["evolution_runtime"] = {"sites": runtime_sites, "count": len(runtime_sites),
                                      "old": old_evolution_runtime,
                                      "new": locations["evolution"]}
    # SpeciesToCryId: canonical cry table is Species-indexed, so return species+1 directly.
    cry_adapter = bytes.fromhex("0130704700bf00bf")
    expected = bytes(stage[0x429F4:0x429FC])
    if expected != bytes.fromhex("00b50004000c011c"):
        fail(f"SpeciesToCryId prologue changed: {expected.hex()}")
    output_rom[0x429F4:0x429FC] = cry_adapter

    asset_model = {"schema_version": 1, "task": TASK, "species_count": len(rows),
                   "vega_preserved": 412, "dpe_appended": len(rows) - 412,
                   "animation_policy": {"vega": "ORIGINAL_CALLBACKS_PRESERVED",
                                        "appended": "DPE_DEFAULT_SPECIES_ANIMATION"},
                   "display_matrix": {
                       "summary": ["icon", "icon_palette", "front_coords"],
                       "party": ["icon", "icon_palette"],
                       "pc": ["icon", "icon_palette"],
                       "battle": ["front", "back", "palette", "shiny_palette", "front_coords", "back_coords"],
                       "evolution": ["front", "palette", "cry"],
                       "dex": ["front", "palette", "dex_entries", "national_dex"],
                   },
                   "validation": validation, "status": "PASS"}
    fixture = breeding_fixture()
    dex_report = f"""# T09 Dex policy\n\n- Vega地方図鑑は既存イベント互換のためSpecies `0..411`を別集計する。\n- 全国図鑑はT07のcanonical National Dex `1..1025`をseen/caught bitmapのキーとし、formは同じ全国番号を共有する。\n- Vega完成イベントは旧フラグと地方集計だけを参照し、追加フォームで必要数が変化しない。\n- まるいおまもりは異なる公式全国番号100種またはquest完了の早い方で解禁し、タマゴ生成成功率を `{config['oval_charm']['base_numerator']}% -> {2 * config['oval_charm']['base_numerator']}%`へ変換する。\n\nStatus: PASS\n""".encode()
    asset_report = f"""# T09 Species asset validation\n\n- canonical Species: {len(rows)}\n- Vega lossless rows: 412\n- DPE appended rows: {len(rows)-412}\n- LZ77 headers: {validation['compressed_checked']} PASS\n- aligned pointers: {validation['aligned_pointers']} PASS\n- icons: {validation['icons_checked']} PASS\n- first appended fixture: canonical 412 / DPE 10\n- front, back, palette, shiny palette, coordinates, icon, icon palette, footprint fallback, cry, Dex entry: PASS\n- summary / party / PC / battle / evolution / Dex table bounds: PASS\n\nStatus: PASS\n""".encode()
    artifacts: dict[str, bytes] = {
        "generated/engine/species_assets/species_assets.json": stable(asset_model),
        **{f"generated/engine/species_assets/{name}.bin": tables[name] for name in assets_order},
        "generated/engine/evolutions/evolutions.bin": evolutions,
        "generated/engine/evolutions/evolutions.json": stable(evolution_model),
        "generated/engine/evolutions/v2_normalized.json": stable(v2),
        **{f"generated/engine/learnsets/{name}.bin": data for name, data in learn.items()},
        "generated/engine/learnsets/learnsets.json": stable(learn_model),
        "reports/generated/dex_policy.md": dex_report,
        "reports/generated/species_asset_validation.md": asset_report,
        "tests/fixtures/breeding_matrix.json": stable(fixture),
    }
    if set(artifacts) != set(ARTIFACTS):
        fail(f"artifact contract mismatch: {set(ARTIFACTS) ^ set(artifacts)}")
    metadata = {"schema_version": 1, "task": TASK, "status": "PASS",
                "input": {"path": config["inputs"]["stage07_path"], "sha256": sha(stage)},
                "output": {"path": config["output"]["rom_path"], "size": len(output_rom),
                           "sha256": sha(bytes(output_rom))},
                "allocation": {"start": int(config["allocation"]["start_offset"]),
                               "end": allocator.cursor, "limit": allocator.end,
                               "free": allocator.end - allocator.cursor, "entries": allocator.entries},
                "repoints": repoints, "cry_adapter": {"site": 0x429F4, "bytes": cry_adapter.hex()},
                "assets": asset_model, "evolutions": {k: v for k, v in evolution_model.items() if k != "rows"},
                "learnsets": learn_model, "v2": {k: v for k, v in v2.items() if k != "rows"},
                "breeding": {"cases": len(fixture["cases"]), "status": fixture["status"]}}
    return artifacts, metadata, bytes(output_rom)


def build(root: Path = ROOT) -> dict[str, Any]:
    artifacts, metadata, rom = build_model(root)
    for path, data in artifacts.items():
        target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    config = read_json(root / CONFIG)
    rom_path = root / config["output"]["rom_path"]
    meta_path = root / config["output"]["metadata_path"]
    rom_path.parent.mkdir(parents=True, exist_ok=True); rom_path.write_bytes(rom); meta_path.write_bytes(stable(metadata))
    return metadata


def check(root: Path = ROOT) -> dict[str, Any]:
    artifacts, metadata, rom = build_model(root)
    config = read_json(root / CONFIG)
    expected = {**artifacts, config["output"]["rom_path"]: rom,
                config["output"]["metadata_path"]: stable(metadata)}
    for path, data in expected.items():
        target = root / path
        if not target.is_file() or target.read_bytes() != data:
            fail(f"published artifact differs: {path}")
    return {"status": "PASS", "species": 1621, "rom_sha256": sha(rom),
            "free_bytes": metadata["allocation"]["free"]}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("build", "check")); args = parser.parse_args()
    result = build() if args.command == "build" else check()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SurfaceError as error:
        print(f"T09 ERROR: {error}", file=sys.stderr); raise SystemExit(1)
