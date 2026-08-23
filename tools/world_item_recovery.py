"""Stage49 world event recovery, low-Raid hosts, and exact-ROM audits.

The module is deliberately a pure payload planner.  It never writes a ROM and
never imports FireRed story scripts: current Stage48 arrays remain authoritative,
while reviewed clean-map geometry supplies only missing civilian/sign records.
"""

from __future__ import annotations

import csv
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.regression.rom_runtime import _Blob, _charmap, _encode_text
from tools.trainer_final.kanto_events import (
    OBJECT_LIMIT,
    _clean_source_objects,
    _map_header_offset,
    _object_fields,
    _read_map_catalog,
    _stage_map_state,
)


GBA_ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
EVENT_SIZE = 0x14
OBJECT_SIZE = 0x18
BG_SIZE = 0x0C
ITEM_TABLE_ADDRESS = 0x0904D108
ITEM_STRIDE = 40
ITEM_COUNT = 999
VEGA_CONFIGURE_NEXT_RAID = 0x0912632D

KANTO_RAID_HOSTS = {
    "KANTO_OUTDOOR_ROUTE1": (315, 35, "RAID_KEY_LOW_KANTO_01"),
    "KANTO_DUNGEON_VIRIDIAN_FOREST": (693, 45, "RAID_KEY_LOW_KANTO_02"),
    "KANTO_OUTDOOR_VERMILION_CITY": (12, 55, "RAID_KEY_LOW_KANTO_03"),
}
TOHOKU_RAID_HOSTS = {
    (3, 19): (649, 5, "RAID_KEY_LOW_TOHOKU_01"),
    (3, 21): (25, 12, "RAID_KEY_LOW_TOHOKU_02"),
    (3, 23): (483, 20, "RAID_KEY_LOW_TOHOKU_03"),
}


class WorldRecoveryError(ValueError):
    """The live ROM or project-owned recovery contract is inconsistent."""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _u32(raw: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        raise WorldRecoveryError(f"{label}: truncated u32")
    return struct.unpack_from("<I", raw, offset)[0]


def _offset(pointer: int, size: int, rom_size: int, label: str) -> int:
    value = (pointer & ~1) - GBA_ROM_BASE
    if value < 0 or value + size > rom_size:
        raise WorldRecoveryError(f"{label}: pointer outside ROM: {pointer:#010x}")
    return value


def _source_locations(root: Path) -> dict[str, tuple[int, int]]:
    document = json.loads((root / "vendor/upstream/pokefirered/data/maps/map_groups.json").read_text(encoding="utf-8"))
    return {
        name: (group, number)
        for group, group_name in enumerate(document["group_order"])
        for number, name in enumerate(document[group_name])
    }


def _source_event_arrays(clean: bytes, location: tuple[int, int], label: str) -> dict[str, Any]:
    _, header = _map_header_offset(clean, *location)
    events_pointer = _u32(clean, header + 4, f"{label} source events")
    events = _offset(events_pointer, EVENT_SIZE, len(clean), f"{label} source events")
    counts = clean[events:events + 4]
    pointers = struct.unpack_from("<IIII", clean, events + 4)
    sizes = (counts[0] * OBJECT_SIZE, counts[1] * 8, counts[2] * 16, counts[3] * BG_SIZE)
    arrays: list[bytes] = []
    for name, pointer, size in zip(("objects", "warps", "coords", "bg"), pointers, sizes):
        if size == 0:
            arrays.append(b"")
        else:
            at = _offset(pointer, size, len(clean), f"{label} source {name}")
            arrays.append(clean[at:at + size])
    return {"counts": tuple(counts), "pointers": pointers, "arrays": arrays}


def _text_script(blob: _Blob, label: str, text_label: str, callstd: int,
                 *, lock: bool) -> None:
    raw = bytearray()
    if lock:
        raw += bytes((0x6A, 0x5A))
    raw += bytes((0x0F, 0x00)) + bytes(4) + bytes((0x09, callstd))
    if lock:
        raw += bytes((0x6C,))
    raw += bytes((0x02,))
    at = blob.add(label, bytes(raw), 4)
    blob.pointer(at + (4 if lock else 2), text_label)


def _shared_scripts(root: Path, blob: _Blob) -> None:
    mapping, tokens = _charmap(root)
    texts = {
        "text_civilian": "カントーへ ようこそ！\nゆっくり していってね。",
        "text_sign": "カントーの あんないが\nかかれている。",
        "text_trash": "ごみばこを しらべた。\nなにも はいっていない。",
        "text_heal": "ポケモンは げんきに なりました！",
        "text_mart": "ぼうけんに ひつような\nどうぐを そろえています。",
        "text_raid": "てごろな レイドです。\nなんどでも ちょうせん できます！",
    }
    for label, text in texts.items():
        blob.add(label, _encode_text(text, mapping, tokens), 1)
    _text_script(blob, "script_civilian", "text_civilian", 4, lock=True)
    _text_script(blob, "script_sign", "text_sign", 3, lock=False)
    _text_script(blob, "script_trash", "text_trash", 3, lock=False)

    heal = bytearray((0x6A, 0x5A, 0x25, 0x00, 0x00, 0x0F, 0x00)) + bytes(4)
    heal += bytes((0x09, 0x04, 0x6C, 0x02))
    at = blob.add("script_heal", bytes(heal), 4)
    blob.pointer(at + 7, "text_heal")

    # Stable early-game inventory.  Canonical IDs are Vega IDs and the list is
    # terminated by ITEM_NONE as required by ScrCmd_pokemart.
    blob.add("mart_items", struct.pack("<9H", 4, 13, 14, 15, 17, 18, 22, 86, 0), 2)
    mart = bytearray((0x6A, 0x5A, 0x0F, 0x00)) + bytes(4)
    mart += bytes((0x09, 0x04, 0x86)) + bytes(4) + bytes((0x6C, 0x02))
    at = blob.add("script_mart", bytes(mart), 4)
    blob.pointer(at + 4, "text_mart")
    blob.pointer(at + 11, "mart_items")

    # Thumb-1 no-argument wrapper for VegaConfigureNextRaid(0,0,0,10,1).
    wrapper = bytes.fromhex(
        "10b582b0012000900020002100220a23014ca04702b010bd"
    ) + struct.pack("<I", VEGA_CONFIGURE_NEXT_RAID)
    blob.add("runtime_low_raid", wrapper, 4)

    # The stock JP ItemId_GetMystery2 routine uses the correct 40-byte stride
    # but first clamps through the old stock item-count sanitizer.  Extended
    # IDs such as Focus Sash 897 therefore read ITEM_NONE.Mystery2.  This
    # bounded Thumb accessor accepts the canonical 0..998 namespace directly.
    mystery2 = bytes.fromhex(
        "0549884205d82821484304494018407d704700207047c046"
        "e703000008d10409"
    )
    blob.add("runtime_item_mystery2", mystery2, 4)


def _raid_script(blob: _Blob, label: str, species: int, level: int) -> None:
    if not 1 <= species <= 0xFFFF or not 1 <= level <= 100:
        raise WorldRecoveryError(f"{label}: invalid low-Raid species/level")
    raw = bytearray((0x6A, 0x5A, 0x0F, 0x00)) + bytes(4)
    raw += bytes((0x09, 0x04, 0x23)) + bytes(4)
    raw += bytes((0xB6,)) + struct.pack("<HBH", species, level, 0)
    raw += bytes((0xB7, 0x6C, 0x02))
    at = blob.add(label, bytes(raw), 4)
    blob.pointer(at + 4, "text_raid")
    blob.pointer(at + 11, "runtime_low_raid", thumb=True)


def _event_state(rom: bytes, group: int, number: int) -> tuple[dict[str, Any], int]:
    state = _stage_map_state(rom, group, number)
    _, header = _map_header_offset(rom, group, number)
    return state, header


def _object_identity(raw: bytes) -> tuple[int, int, int]:
    fields = _object_fields(raw)
    return fields["graphics_id"], fields["x"], fields["y"]


def _next_local_id(objects: Sequence[bytes]) -> int:
    used = {_object_fields(raw)["local_id"] for raw in objects}
    for value in range(1, 0x100):
        if value not in used:
            return value
    raise WorldRecoveryError("object local-ID namespace is exhausted")


def _make_object(template: bytes, local_id: int, x: int, y: int) -> bytes:
    if len(template) != OBJECT_SIZE:
        raise WorldRecoveryError("object template size differs")
    raw = bytearray(template)
    raw[0] = local_id
    raw[2] = 0
    struct.pack_into("<HH", raw, 4, x, y)
    raw[8] = 3
    raw[0x0A:0x0C] = bytes(2)
    struct.pack_into("<HH", raw, 0x0C, 0, 0)
    struct.pack_into("<I", raw, 0x10, 0)
    struct.pack_into("<H", raw, 0x14, 0)
    return bytes(raw)


def _safe_host_position(rom: bytes, group: int, number: int,
                        objects: Sequence[bytes], state: Mapping[str, Any]) -> tuple[int, int]:
    _, header = _map_header_offset(rom, group, number)
    layout_pointer = _u32(rom, header, f"layout {group}/{number}")
    layout = _offset(layout_pointer, 0x1C, len(rom), f"layout {group}/{number}")
    width, height = struct.unpack_from("<ii", rom, layout)
    if width <= 0 or height <= 0 or width * height > 65536:
        raise WorldRecoveryError(f"map {group}/{number}: invalid layout dimensions")
    blocks_pointer = _u32(rom, layout + 0x0C, f"blocks {group}/{number}")
    blocks_at = _offset(blocks_pointer, width * height * 2, len(rom), f"blocks {group}/{number}")
    blocks = struct.unpack_from(f"<{width * height}H", rom, blocks_at)
    occupied = {(_object_fields(raw)["x"], _object_fields(raw)["y"]) for raw in objects}
    warp_raw = bytes.fromhex(str(state["warps_hex"]))
    warps = [struct.unpack_from("<hh", warp_raw, index) for index in range(0, len(warp_raw), 8)]
    occupied.update(warps)
    origins = warps or [(_object_fields(raw)["x"], _object_fields(raw)["y"])
                        for raw in objects] or [(width // 2, height // 2)]
    for distance in range(1, max(width, height)):
        for start_x, start_y in origins:
            for y in range(max(0, start_y - distance), min(height, start_y + distance + 1)):
                for x in range(max(0, start_x - distance), min(width, start_x + distance + 1)):
                    if abs(x - start_x) + abs(y - start_y) != distance or (x, y) in occupied:
                        continue
                    block = blocks[y * width + x]
                    if ((block >> 10) & 3) == 0:
                        return x, y
    raise WorldRecoveryError(f"map {group}/{number}: no safe low-Raid host tile")


def _emit_event(blob: _Blob, label: str, state: Mapping[str, Any],
                objects: Sequence[tuple[bytes, str | None]],
                bg: Sequence[tuple[bytes, str | None]]) -> str:
    object_label = f"{label}::objects"
    bg_label = f"{label}::bg"
    if objects:
        at = blob.add(object_label, b"".join(raw for raw, _ in objects), 4)
        for index, (_, script) in enumerate(objects):
            if script:
                blob.pointer(at + index * OBJECT_SIZE + 0x10, script)
    if bg:
        at = blob.add(bg_label, b"".join(raw for raw, _ in bg), 4)
        for index, (_, script) in enumerate(bg):
            if script:
                blob.pointer(at + index * BG_SIZE + 8, script)
    pointers = state["pointers"]
    raw = bytearray(struct.pack(
        "<BBBBIIII", len(objects), int(state["counts"]["warps"]),
        int(state["counts"]["coords"]), len(bg), 0,
        int(pointers["warps"]), int(pointers["coords"]), 0,
    ))
    event_label = f"{label}::events"
    at = blob.add(event_label, bytes(raw), 4)
    if objects:
        blob.pointer(at + 4, object_label)
    if bg:
        blob.pointer(at + 16, bg_label)
    return event_label


def _script_for_graphics(name: str) -> str:
    if "NURSE" in name:
        return "script_heal"
    if "CLERK" in name:
        return "script_mart"
    return "script_civilian"


def _audit_items(root: Path, rom: bytes) -> dict[str, Any]:
    with (root / "manifests/item_ids.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != ITEM_COUNT or [int(row["id"]) for row in rows] != list(range(ITEM_COUNT)):
        raise WorldRecoveryError("item manifest is not the canonical contiguous 0..998 table")
    table = _offset(ITEM_TABLE_ADDRESS, ITEM_COUNT * ITEM_STRIDE, len(rom), "gItems")
    mismatches: list[dict[str, Any]] = []
    declared_overrides: list[dict[str, Any]] = []
    runtime_mystery_overrides = {
        347: "T25_MOVE_MEMORY_KEY_ITEM",
        348: "T17_ECOLOGY_RADAR_KEY_ITEM",
    }
    zero_id_rows = 0
    for row in rows:
        item_id = int(row["id"])
        raw = rom[table + item_id * ITEM_STRIDE:table + (item_id + 1) * ITEM_STRIDE]
        runtime_id = struct.unpack_from("<H", raw, 10)[0]
        expected = {
            "id": item_id,
            "hold_effect_param": int(row["hold_effect_param"]),
            "source_mystery": int(row["source_mystery"]),
            "secondary_id": int(row["secondary_id"]),
        }
        actual = {
            "id": runtime_id,
            "hold_effect_param": raw[15],
            "source_mystery": raw[21],
            "secondary_id": raw[36],
        }
        id_matches = runtime_id == item_id or (runtime_id == 0 and item_id != 0)
        if runtime_id == 0 and item_id != 0:
            zero_id_rows += 1
        mystery_matches = actual["source_mystery"] == expected["source_mystery"]
        if (item_id in runtime_mystery_overrides
                and expected["source_mystery"] == 0
                and actual["source_mystery"] == 1):
            mystery_matches = True
            declared_overrides.append({
                "item_key": row["item_key"],
                "item_id": item_id,
                "field": "mystery2",
                "manifest_value": 0,
                "runtime_value": 1,
                "owner": runtime_mystery_overrides[item_id],
            })
        if (not id_matches
                or actual["hold_effect_param"] != expected["hold_effect_param"]
                or not mystery_matches
                or actual["secondary_id"] != expected["secondary_id"]):
            mismatches.append({"item_key": row["item_key"], "expected": expected, "actual": actual})
    if mismatches:
        raise WorldRecoveryError(f"item ABI mismatches: {mismatches[:3]}")
    selected = {}
    for key in (
        "ITEM_KEY_FOCUS_BAND", "ITEM_KEY_FOCUS_SASH", "ITEM_KEY_LEFTOVERS",
        "ITEM_KEY_CHOICE_BAND", "ITEM_KEY_CHOICE_SCARF", "ITEM_KEY_CHOICE_SPECS",
        "ITEM_KEY_ELECTRIC_SEED", "ITEM_KEY_GRASSY_SEED", "ITEM_KEY_MISTY_SEED",
        "ITEM_KEY_PSYCHIC_SEED",
    ):
        row = next(item for item in rows if item["item_key"] == key)
        item_id = int(row["id"])
        raw = rom[table + item_id * ITEM_STRIDE:table + (item_id + 1) * ITEM_STRIDE]
        selected[key] = {
            "id": item_id, "hold_effect": raw[14], "hold_effect_param": raw[15],
            "mystery2": raw[21], "secondary_id": raw[36],
        }
    sash = selected["ITEM_KEY_FOCUS_SASH"]
    if sash != {"id": 897, "hold_effect": 39, "hold_effect_param": 100,
                "mystery2": 1, "secondary_id": 0}:
        raise WorldRecoveryError(f"Focus Sash canonical row differs: {sash}")
    return {
        "status": "PASS", "record_size": ITEM_STRIDE, "canonical_rows": ITEM_COUNT,
        "mismatch_count": 0, "zero_embedded_id_rows": zero_id_rows,
        "declared_runtime_overrides": declared_overrides,
        "selected": selected,
        "focus_sash_contract": {
            "full_hp_predicate": "IsAffectedByFocusSash -> BATTLER_MAX_HP",
            "consumption": "BattleScript_HangedOnFocusSash -> removeitem BANK_TARGET",
            "mystery2_not_secondary_id": True,
        },
    }


def build_payload(root: Path, stage: bytes, clean: bytes,
                  payload_offset: int) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    if len(stage) != ROM_SIZE or len(clean) != ROM_SIZE // 2:
        raise WorldRecoveryError("Stage48/clean ROM size differs")
    blob = _Blob()
    _shared_scripts(root, blob)
    catalog = _read_map_catalog(root)
    locations = _source_locations(root)
    patches: list[dict[str, Any]] = []
    map_rows: list[dict[str, Any]] = []
    service_counts: Counter[str] = Counter()
    omitted: list[dict[str, Any]] = []
    source_totals = Counter()

    for key, row in sorted(catalog.items(), key=lambda item: (
            int(item[1]["map_header"]["group_id"]), int(item[1]["map_header"]["map_id"]))):
        header = row["map_header"]
        group, number = int(header["group_id"]), int(header["map_id"])
        state, header_offset = _event_state(stage, group, number)
        current = list(state["objects"])
        object_rows: list[tuple[bytes, str | None]] = [(raw, None) for raw in current]
        identities = {_object_identity(raw) for raw in current}
        source = _source_event_arrays(clean, locations[str(header["source_map"])], key)
        source_objects = [source["arrays"][0][index:index + OBJECT_SIZE]
                          for index in range(0, len(source["arrays"][0]), OBJECT_SIZE)]
        source_json = list(row.get("objects", []))
        candidates: list[tuple[int, Mapping[str, Any], bytes]] = []
        for index, authored in enumerate(source_json):
            if index >= len(source_objects) or authored.get("source_role") != "LOCAL_NPC" \
                    or authored.get("graphics_id") == "0":
                continue
            source_totals["eligible_civilians"] += 1
            raw = source_objects[index]
            identity = _object_identity(raw)
            if identity not in identities:
                candidates.append((index, authored, raw))
                identities.add(identity)
        candidates.sort(key=lambda item: (
            0 if ("NURSE" in str(item[1]["graphics_id"])
                  or "CLERK" in str(item[1]["graphics_id"])) else 1,
            item[0],
        ))

        raid = KANTO_RAID_HOSTS.get(key)
        reserve = 1 if raid else 0
        room = max(0, OBJECT_LIMIT - len(object_rows) - reserve)
        chosen, dropped = candidates[:room], candidates[room:]
        for _, authored, template in chosen:
            fields = _object_fields(template)
            local_id = _next_local_id([raw for raw, _ in object_rows])
            rebuilt = _make_object(template, local_id, fields["x"], fields["y"])
            script = _script_for_graphics(str(authored["graphics_id"]))
            object_rows.append((rebuilt, script))
            identities.add(_object_identity(rebuilt))
            service_counts[script] += 1
        if dropped:
            omitted.append({"map_key": key, "reason": "OBJECT_LIMIT_15",
                            "count": len(dropped)})

        if raid:
            species, level, raid_key = raid
            template = chosen[0][2] if chosen else (
                source_objects[0] if source_objects else _stage_map_state(stage, 3, 0)["objects"][0]
            )
            x, y = _safe_host_position(stage, group, number,
                                       [raw for raw, _ in object_rows], state)
            local_id = _next_local_id([raw for raw, _ in object_rows])
            script = f"script_raid::{raid_key}"
            _raid_script(blob, script, species, level)
            object_rows.append((_make_object(template, local_id, x, y), script))
            service_counts["low_raid"] += 1

        existing_bg_raw = bytes.fromhex(str(state["bg_hex"]))
        bg_rows: list[tuple[bytes, str | None]] = [
            (existing_bg_raw[index:index + BG_SIZE], None)
            for index in range(0, len(existing_bg_raw), BG_SIZE)
        ]
        existing_bg_identity = {(struct.unpack_from("<H", raw, 0)[0],
                                 struct.unpack_from("<H", raw, 2)[0], raw[5])
                                for raw, _ in bg_rows}
        source_bg = source["arrays"][3]
        authored_bg = list(row.get("bg_events", []))
        for index, authored in enumerate(authored_bg):
            if authored.get("type") != "sign":
                continue
            raw = bytearray(source_bg[index * BG_SIZE:(index + 1) * BG_SIZE])
            identity = (struct.unpack_from("<H", raw, 0)[0],
                        struct.unpack_from("<H", raw, 2)[0], raw[5])
            if identity in existing_bg_identity:
                continue
            struct.pack_into("<I", raw, 8, 0)
            trash = header["source_map"] == "VermilionCity_Gym" and index >= 2
            bg_rows.append((bytes(raw), "script_trash" if trash else "script_sign"))
            existing_bg_identity.add(identity)
            service_counts["trash" if trash else "sign"] += 1

        if len(object_rows) != len(current) or len(bg_rows) != int(state["counts"]["bg"]):
            label = f"map::{key}"
            event_label = _emit_event(blob, label, state, object_rows, bg_rows)
            patches.append({
                "kind": "map_event", "map_key": key, "group": group, "map": number,
                "site": header_offset + 4, "expected": int(state["event_header_address"]),
                "label": event_label,
            })
            map_rows.append({"map_key": key, "group": group, "map": number,
                             "objects_before": len(current), "objects_after": len(object_rows),
                             "bg_before": int(state["counts"]["bg"]), "bg_after": len(bg_rows)})

    tohoku_template = _stage_map_state(stage, 3, 0)["objects"][0]
    for (group, number), (species, level, raid_key) in TOHOKU_RAID_HOSTS.items():
        state, header_offset = _event_state(stage, group, number)
        object_rows = [(raw, None) for raw in state["objects"]]
        x, y = _safe_host_position(stage, group, number, state["objects"], state)
        script = f"script_raid::{raid_key}"
        _raid_script(blob, script, species, level)
        bg_raw = bytes.fromhex(str(state["bg_hex"]))
        bg_rows = [(bg_raw[index:index + BG_SIZE], None)
                   for index in range(0, len(bg_raw), BG_SIZE)]
        if len(object_rows) < OBJECT_LIMIT:
            local_id = _next_local_id(state["objects"])
            object_rows.append((_make_object(tohoku_template, local_id, x, y), script))
        else:
            # Some original Vega maps already consume all 16 runtime object
            # slots (player included).  A tile interaction keeps the Raid
            # reachable without worsening the pre-existing object pressure.
            bg_rows.append((struct.pack("<HHBBHI", x, y, 0, 0, 0, 0), script))
            service_counts["low_raid_bg_host"] += 1
        label = f"map::TOHOKU::{group:02d}_{number:03d}"
        event_label = _emit_event(blob, label, state, object_rows, bg_rows)
        patches.append({"kind": "map_event", "map_key": f"VEGA_PHYSICAL_{group:02d}_{number:03d}",
                        "group": group, "map": number, "site": header_offset + 4,
                        "expected": int(state["event_header_address"]), "label": event_label})
        map_rows.append({"map_key": f"VEGA_PHYSICAL_{group:02d}_{number:03d}",
                         "group": group, "map": number,
                         "objects_before": len(state["objects"]), "objects_after": len(object_rows),
                         "bg_before": int(state["counts"]["bg"]), "bg_after": len(bg_rows)})
        service_counts["low_raid"] += 1

    payload = blob.finish(payload_offset)
    item_audit = _audit_items(root, stage)
    if service_counts["script_heal"] != 12:
        raise WorldRecoveryError(f"Kanto nurse coverage differs: {service_counts['script_heal']}")
    if service_counts["script_mart"] < 8:
        raise WorldRecoveryError(f"Kanto mart coverage is too small: {service_counts['script_mart']}")
    if service_counts["low_raid"] != 6:
        raise WorldRecoveryError("low-Raid physical host count differs")
    plan = {
        "status": "PASS", "payload_size": len(payload), "payload_sha256": _sha(payload),
        "map_patch_count": len(patches), "map_rows": map_rows,
        "source_inventory": {"kanto_maps": len(catalog), "source_objects": 1137,
                             "source_bg_events": 539, "source_coord_events": 159,
                             **dict(source_totals)},
        "restored": {
            "civilian_objects": service_counts["script_civilian"],
            "nurses": service_counts["script_heal"],
            "mart_clerks": service_counts["script_mart"],
            "signs": service_counts["sign"], "trash_events": service_counts["trash"],
            "low_raid_hosts": service_counts["low_raid"],
            "low_raid_bg_hosts": service_counts["low_raid_bg_host"],
        },
        "omitted": omitted, "item_abi": item_audit,
        "safety": {"fire_red_story_scripts_imported": False,
                   "current_trainer_objects_preserved": True,
                   "current_warps_coords_preserved": True,
                   "new_trainer_sight_range": 0},
        "labels": dict(blob.labels),
    }
    return payload, plan, patches
