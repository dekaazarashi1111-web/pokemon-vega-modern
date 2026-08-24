"""Stage50 interaction-owner repair payload and physical-map audit planner.

Stage49 treated every missing FireRed object as a civilian.  This module uses
the immutable Stage48 event arrays as the project baseline and reintroduces
only interactions whose owner is explicit: dialogue, service, item, field
move, sign, or hidden item.  FireRed story scripts are never imported.
"""

from __future__ import annotations

import csv
import hashlib
import json
import struct
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.regression.rom_runtime import _Blob, _charmap, _encode_text
from tools.trainer_final.kanto_events import (
    OBJECT_LIMIT,
    _map_header_offset,
    _object_fields,
    _read_map_catalog,
    _stage_map_state,
)
from tools.world_item_recovery import (
    BG_SIZE,
    EVENT_SIZE,
    GBA_ROM_BASE,
    OBJECT_SIZE,
    ROM_SIZE,
    _audit_items,
    _source_event_arrays,
    _source_locations,
)


ITEM_FLAG_BASE = 0x140D
ITEM_FLAG_COUNT = 139
CUT_SCRIPT = 0x081A4721
ROCK_SMASH_SCRIPT = 0x081A47E3
WILD_HEADERS_POINTER_SITE = 0x0008257C
EXPECTED_WILD_HEADER_COUNT = 265
TARGET_WATERWAY = (3, 29)
NEIGHBOR_ROUTE = (3, 32)


class InteractionRepairError(ValueError):
    """The interaction graph cannot be rebuilt without guessing."""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _u32(raw: bytes, offset: int, label: str) -> int:
    if offset < 0 or offset + 4 > len(raw):
        raise InteractionRepairError(f"{label}: truncated u32")
    return struct.unpack_from("<I", raw, offset)[0]


def _offset(pointer: int, size: int, rom_size: int, label: str) -> int:
    value = (pointer & ~1) - GBA_ROM_BASE
    if value < 0 or value + size > rom_size:
        raise InteractionRepairError(f"{label}: ROM pointer outside image: {pointer:#010x}")
    return value


@dataclass
class _Script:
    data: bytearray
    fixups: list[tuple[int, str]]
    operations: list[str]

    def __init__(self) -> None:
        self.data = bytearray()
        self.fixups = []
        self.operations = []

    def emit(self, *values: int, operation: str | None = None) -> "_Script":
        self.data.extend(values)
        if operation:
            self.operations.append(operation)
        return self

    def half(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<H", value))
        return self

    def pointer(self, label: str) -> "_Script":
        self.fixups.append((len(self.data), label))
        self.data.extend(bytes(4))
        return self

    def msgbox(self, label: str, kind: int = 4) -> "_Script":
        self.operations.append(f"msgbox:{label}:{kind}")
        return self.emit(0x0F, 0x00).pointer(label).emit(0x09, kind)

    def compare_result(self, value: int) -> "_Script":
        self.operations.append(f"compare:0x800D:{value}")
        return self.emit(0x21).half(0x800D).half(value)

    def if_equal(self, label: str) -> "_Script":
        self.operations.append(f"if_equal:{label}")
        return self.emit(0x06, 0x01).pointer(label)

    def goto(self, label: str) -> "_Script":
        self.operations.append(f"goto:{label}")
        return self.emit(0x05).pointer(label)

    def checkflag(self, flag: int) -> "_Script":
        self.operations.append(f"checkflag:{flag:#06x}")
        return self.emit(0x2B).half(flag)

    def setflag(self, flag: int) -> "_Script":
        self.operations.append(f"setflag:{flag:#06x}")
        return self.emit(0x29).half(flag)

    def additem(self, item: int, quantity: int) -> "_Script":
        self.operations.append(f"additem:{item}:{quantity}")
        return self.emit(0x44).half(item).half(quantity)

    def removeobject(self, local_id: int = 0x800F) -> "_Script":
        self.operations.append(f"removeobject:{local_id:#06x}")
        return self.emit(0x53).half(local_id)


def _add_script(blob: _Blob, label: str, script: _Script,
                audit: dict[str, Any]) -> None:
    at = blob.add(label, bytes(script.data), 4)
    for relative, target in script.fixups:
        blob.pointer(at + relative, target)
    audit[label] = {
        "offset": at,
        "size": len(script.data),
        "operations": script.operations,
    }


def _text_script(blob: _Blob, label: str, text_label: str,
                 *, object_host: bool, scripts: dict[str, Any]) -> None:
    script = _Script().emit(
        0x6A if object_host else 0x69,
        operation="lock" if object_host else "lockall",
    )
    if object_host:
        script.emit(0x5A, operation="faceplayer")
    script.msgbox(text_label).emit(
        0x6C if object_host else 0x6B, 0x02,
        operation="release_end" if object_host else "releaseall_end",
    )
    _add_script(blob, label, script, scripts)


def _shared_scripts(root: Path, blob: _Blob) -> dict[str, Any]:
    mapping, tokens = _charmap(root)
    texts = {
        "text_outdoor": "この ちほうには\nいろいろな みちが あるよ。",
        "text_indoor": "ここでは みんな\nそれぞれの しごとを しているよ。",
        "text_dungeon": "どうくつでは あしもとに\nきをつけて すすんでね。",
        "text_sign": "この ばしょの あんないが\nかかれている。",
        "text_hisui": "ヒスイシティは\nしずかな みずべの まちです。",
        "text_repaired": "いまは じゅんびちゅうです。\nまた はなしかけてね。",
        "text_item_found": "どうぐを ひろった！",
        "text_item_full": "バッグが いっぱいで\nひろうことが できない。",
        "text_item_empty": "もう なにも ない。",
        "text_heal": "ポケモンは げんきに なりました！",
        "text_mart": "ぼうけんに ひつような\nどうぐを そろえています。",
    }
    for label, text in texts.items():
        blob.add(label, _encode_text(text, mapping, tokens), 1)

    scripts: dict[str, Any] = {}
    _text_script(blob, "script_outdoor", "text_outdoor", object_host=True, scripts=scripts)
    _text_script(blob, "script_indoor", "text_indoor", object_host=True, scripts=scripts)
    _text_script(blob, "script_dungeon", "text_dungeon", object_host=True, scripts=scripts)
    _text_script(blob, "script_sign", "text_sign", object_host=False, scripts=scripts)
    _text_script(blob, "script_hisui", "text_hisui", object_host=True, scripts=scripts)
    _text_script(blob, "script_repaired", "text_repaired", object_host=True, scripts=scripts)

    heal = _Script().emit(0x6A, 0x5A, operation="lock_faceplayer")
    heal.emit(0x25, operation="special:HealPlayerParty").half(0)
    heal.msgbox("text_heal").emit(0x6C, 0x02, operation="release_end")
    _add_script(blob, "script_heal", heal, scripts)

    blob.add("mart_items", struct.pack("<9H", 4, 13, 14, 15, 17, 18, 22, 86, 0), 2)
    mart = _Script().emit(0x6A, 0x5A, operation="lock_faceplayer")
    mart.msgbox("text_mart").emit(0x86, operation="pokemart").pointer("mart_items")
    mart.emit(0x6C, 0x02, operation="release_end")
    _add_script(blob, "script_mart", mart, scripts)

    # Turning in place must not call TryStandardWildEncounter.  The wrapper
    # accepts only gPlayerAvatar.runningState == MOVING (2).
    wrapper = bytes.fromhex("10b504498978022902d1034b984710bd002010bd")
    wrapper += struct.pack("<II", 0x02036FAC, 0x08082F9D)
    blob.add("runtime_moving_wild_encounter", wrapper, 4)

    # 511ばんすいどう receives an independent land owner based on the next
    # physical route's native species, with levels kept in the local 25..31 band.
    slots = (
        (25, 27, 21), (25, 27, 97), (26, 28, 21), (26, 28, 97),
        (27, 29, 33), (27, 29, 30), (28, 30, 22), (28, 30, 101),
        (29, 31, 101), (29, 31, 98), (30, 31, 85), (30, 31, 98),
    )
    blob.add("wild_511_land_slots", b"".join(struct.pack("<BBH", *row) for row in slots), 4)
    at = blob.add("wild_511_land_info", bytes((21, 0, 0, 0)) + bytes(4), 4)
    blob.pointer(at + 4, "wild_511_land_slots")
    return scripts


def _finish_item_script(blob: _Blob, label: str, *, flag: int, item: int,
                        quantity: int, object_host: bool,
                        audit: dict[str, Any]) -> None:
    already = f"{label}::already"
    full = f"{label}::full"
    end = f"{label}::end"
    script = _Script().emit(
        0x6A if object_host else 0x69,
        operation="lock" if object_host else "lockall",
    )
    if object_host:
        script.emit(0x5A, operation="faceplayer")
    script.checkflag(flag).compare_result(1).if_equal(already)
    script.additem(item, quantity).compare_result(0).if_equal(full)
    script.setflag(flag)
    if object_host:
        script.removeobject()
    script.msgbox("text_item_found").goto(end)
    _add_script(blob, label, script, audit)
    _add_script(blob, already, _Script().msgbox("text_item_empty").goto(end), audit)
    _add_script(blob, full, _Script().msgbox("text_item_full").goto(end), audit)
    _add_script(
        blob, end,
        _Script().emit(
            0x6C if object_host else 0x6B, 0x02,
            operation="release_end" if object_host else "releaseall_end",
        ),
        audit,
    )


def _event_rows(state: Mapping[str, Any]) -> tuple[list[tuple[bytes, str | int | None]],
                                                    list[tuple[bytes, str | int | None]]]:
    objects = [(bytes(raw), None) for raw in state["objects"]]
    bg_raw = bytes.fromhex(str(state["bg_hex"]))
    bg = [(bg_raw[index:index + BG_SIZE], None)
          for index in range(0, len(bg_raw), BG_SIZE)]
    return objects, bg


def _emit_event(blob: _Blob, label: str, state: Mapping[str, Any],
                objects: Sequence[tuple[bytes, str | int | None]],
                bg: Sequence[tuple[bytes, str | int | None]]) -> str:
    object_label = f"{label}::objects"
    bg_label = f"{label}::bg"
    if objects:
        at = blob.add(object_label, b"".join(raw for raw, _ in objects), 4)
        for index, (_, script) in enumerate(objects):
            if isinstance(script, str):
                blob.pointer(at + index * OBJECT_SIZE + 0x10, script)
            elif isinstance(script, int):
                struct.pack_into("<I", blob.data, at + index * OBJECT_SIZE + 0x10, script)
    if bg:
        at = blob.add(bg_label, b"".join(raw for raw, _ in bg), 4)
        for index, (_, script) in enumerate(bg):
            if isinstance(script, str):
                blob.pointer(at + index * BG_SIZE + 8, script)
            elif isinstance(script, int):
                struct.pack_into("<I", blob.data, at + index * BG_SIZE + 8, script)
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


def _identity(raw: bytes) -> tuple[int, int, int]:
    fields = _object_fields(raw)
    return fields["graphics_id"], fields["x"], fields["y"]


def _next_local_id(objects: Sequence[tuple[bytes, str | int | None]]) -> int:
    used = {_object_fields(raw)["local_id"] for raw, _ in objects}
    for value in range(1, 0x100):
        if value not in used:
            return value
    raise InteractionRepairError("object local-ID namespace exhausted")


def _copy_source_object(template: bytes, local_id: int, *, flag: int,
                        script: int = 0) -> bytes:
    if len(template) != OBJECT_SIZE:
        raise InteractionRepairError("source object record size differs")
    raw = bytearray(template)
    raw[0] = local_id
    if raw[2] != 0:
        raise InteractionRepairError("clone object cannot become an interaction host")
    struct.pack_into("<HH", raw, 0x0C, 0, 0)
    struct.pack_into("<I", raw, 0x10, script)
    struct.pack_into("<H", raw, 0x14, flag)
    return bytes(raw)


def _reduce_sight(raw: bytes) -> tuple[bytes, bool]:
    fields = _object_fields(raw)
    if fields["kind"] != 0 or fields["trainer_type"] != 1 or fields["sight_range"] <= 1:
        return raw, False
    result = bytearray(raw)
    struct.pack_into("<H", result, 0x0E, fields["sight_range"] - 1)
    return bytes(result), True


def _dialogue_script(classification: str) -> str:
    if classification == "DUNGEON":
        return "script_dungeon"
    if classification == "INDOOR":
        return "script_indoor"
    return "script_outdoor"


def _classify_object(authored: Mapping[str, Any], raw: bytes) -> tuple[str, int | None]:
    if authored.get("type") == "clone" or _object_fields(raw)["kind"] != 0:
        return "clone", None
    graphics = str(authored.get("graphics_id", ""))
    script = str(authored.get("script", ""))
    if str(authored.get("trainer_type", "TRAINER_TYPE_NONE")) != "TRAINER_TYPE_NONE":
        return "trainer", None
    if "ITEM_BALL" in graphics:
        pointer = _object_fields(raw)["script_pointer"]
        at = _offset(pointer, 20, ROM_SIZE // 2, "clean item script")
        return "item_ball", at
    if script == "EventScript_CutTree" or "CUT_TREE" in graphics:
        return "cut_tree", None
    if script == "EventScript_RockSmash" or "ROCK_SMASH" in graphics:
        return "rock_smash", None
    if "NURSE" in graphics:
        return "nurse", None
    if "CLERK" in graphics:
        return "clerk", None
    return "civilian", None


def _standard_item(clean: bytes, script_offset: int) -> int | None:
    raw = clean[script_offset:script_offset + 24]
    for start in range(3):
        if raw[start:start + 3] != bytes((0x1A, 0x00, 0x80)):
            continue
        if raw[start + 5:start + 13] != bytes((0x1A, 0x01, 0x80, 0x01, 0x00, 0x09, 0x01, 0x02)):
            continue
        return struct.unpack_from("<H", raw, start + 3)[0]
    return None


def _load_item_manifests(root: Path) -> tuple[dict[str, int], dict[str, tuple[int, int]]]:
    with (root / "manifests/item_ids.csv").open(encoding="utf-8-sig", newline="") as stream:
        items = {row["item_key"]: int(row["id"]) for row in csv.DictReader(stream)}
    with (root / "manifests/flags.csv").open(encoding="utf-8-sig", newline="") as stream:
        flags = {row["flag_key"]: int(row["id"], 0) for row in csv.DictReader(stream)}
    expected_item_flags = {
        f"FLAG_KEY_STAGE50_KANTO_ITEM_BALL_{index:03d}": ITEM_FLAG_BASE + index
        for index in range(ITEM_FLAG_COUNT)
    }
    actual_item_flags = {key: flags.get(key) for key in expected_item_flags}
    if actual_item_flags != expected_item_flags:
        raise InteractionRepairError("Stage50 item-ball flag manifest is incomplete or shifted")
    with (root / "manifests/kanto_items.csv").open(encoding="utf-8-sig", newline="") as stream:
        placements = {
            row["placement_key"]: (items[row["item_key"]], flags[row["flag_key"]])
            for row in csv.DictReader(stream)
            if row["status"] == "ACTIVE" and row["placement_type"] == "HIDDEN_ITEM"
        }
    return items, placements


def _source_map_json(root: Path, source: str) -> dict[str, Any]:
    return json.loads((root / "vendor/upstream/pokefirered/data/maps" / source / "map.json").read_text(encoding="utf-8"))


def _kanto_maps(root: Path, blob: _Blob, stage49: bytes, stage48: bytes,
                clean: bytes, script_audit: dict[str, Any]) -> tuple[list[dict[str, Any]],
                                                                      list[dict[str, Any]],
                                                                      set[tuple[int, int]],
                                                                      dict[str, Any]]:
    catalog = _read_map_catalog(root)
    locations = _source_locations(root)
    _, hidden_manifest = _load_item_manifests(root)
    patches: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    rebuilt: set[tuple[int, int]] = set()
    counts: Counter[str] = Counter()
    omitted: list[dict[str, Any]] = []
    source_safe_overflow: list[dict[str, Any]] = []
    item_index = 0

    for key, row in sorted(catalog.items(), key=lambda value: (
            int(value[1]["map_header"]["group_id"]), int(value[1]["map_header"]["map_id"]))):
        header = row["map_header"]
        group, number = int(header["group_id"]), int(header["map_id"])
        base = _stage_map_state(stage48, group, number)
        current = _stage_map_state(stage49, group, number)
        objects, bg = _event_rows(base)
        adjusted: list[tuple[bytes, str | int | None]] = []
        map_sight_changed = False
        for raw, script in objects:
            fixed, changed = _reduce_sight(raw)
            adjusted.append((fixed, script))
            counts["sight_reduced_in_payload"] += changed
            map_sight_changed = map_sight_changed or changed
        objects = adjusted
        identities = {_identity(raw) for raw, _ in objects}
        occupied_bg = {(struct.unpack_from("<H", raw, 0)[0], struct.unpack_from("<H", raw, 2)[0])
                       for raw, _ in bg}

        source_name = str(header["source_map"])
        source = _source_event_arrays(clean, locations[source_name], key)
        source_objects = [source["arrays"][0][index:index + OBJECT_SIZE]
                          for index in range(0, len(source["arrays"][0]), OBJECT_SIZE)]
        authored = list(_source_map_json(root, source_name).get("object_events", []))
        candidates: list[dict[str, Any]] = []
        for index, (source_row, raw) in enumerate(zip(authored, source_objects)):
            kind, script_offset = _classify_object(source_row, raw)
            if kind == "item_ball":
                flag = ITEM_FLAG_BASE + item_index
                item_index += 1
                item = _standard_item(clean, int(script_offset))
                if item is None:
                    counts["special_ball_excluded"] += 1
                    continue
            else:
                flag, item = 0, None
            counts[f"source_{kind}"] += 1
            if kind in {"clone", "trainer"}:
                continue
            if _identity(raw) in identities:
                counts[f"preserved_{kind}"] += 1
                continue
            priority = {
                "item_ball": 0, "cut_tree": 1, "rock_smash": 1,
                "nurse": 2, "clerk": 2, "civilian": 3,
            }[kind]
            candidates.append({
                "index": index, "kind": kind, "raw": raw, "flag": flag,
                "item": item, "priority": priority,
            })
        candidates.sort(key=lambda value: (value["priority"], value["index"]))
        # The runtime owns 16 simultaneously active object slots, not 15 map
        # templates.  FireRed maps legitimately carry more templates and load
        # only nearby objects.  Keep every source-positioned field/service
        # owner; apply the conservative template cap only to generic dialogue.
        required = [value for value in candidates if value["priority"] <= 2]
        optional = [value for value in candidates if value["priority"] > 2]
        room = max(0, OBJECT_LIMIT - len(objects) - len(required))
        chosen, dropped = required + optional[:room], optional[room:]
        if len(objects) + len(required) > OBJECT_LIMIT:
            source_safe_overflow.append({
                "map_key": key,
                "stage48_templates": len(objects),
                "required_source_templates": len(required),
                "stage50_templates_before_dialogue": len(objects) + len(required),
                "clean_source_templates": len(source_objects),
            })
        if dropped:
            omitted.append({
                "map_key": key, "count": len(dropped),
                "owners": dict(Counter(value["kind"] for value in dropped)),
                "reason": "OBJECT_LIMIT_15",
            })
        for value in chosen:
            kind = str(value["kind"])
            local = _next_local_id(objects)
            if kind == "item_ball":
                script = f"script_item::{key}::{value['index']:03d}"
                _finish_item_script(
                    blob, script, flag=int(value["flag"]), item=int(value["item"]),
                    quantity=1, object_host=True, audit=script_audit,
                )
                direct = 0
            elif kind == "cut_tree":
                script, direct = CUT_SCRIPT, CUT_SCRIPT
            elif kind == "rock_smash":
                script, direct = ROCK_SMASH_SCRIPT, ROCK_SMASH_SCRIPT
            elif kind == "nurse":
                script, direct = "script_heal", 0
            elif kind == "clerk":
                script, direct = "script_mart", 0
            else:
                script, direct = _dialogue_script(str(header["classification"])), 0
            record = _copy_source_object(
                bytes(value["raw"]), local, flag=int(value["flag"]), script=direct,
            )
            objects.append((record, script))
            identities.add(_identity(record))
            counts[f"restored_{kind}"] += 1

        source_bg = source["arrays"][3]
        authored_bg = list(row.get("bg_events", []))
        for index, event in enumerate(authored_bg):
            raw = bytearray(source_bg[index * BG_SIZE:(index + 1) * BG_SIZE])
            if len(raw) != BG_SIZE:
                continue
            identity = (struct.unpack_from("<H", raw, 0)[0], struct.unpack_from("<H", raw, 2)[0])
            if identity in occupied_bg:
                if event.get("type") == "hidden_item":
                    placement = str(event.get("placement_key", ""))
                    if placement not in hidden_manifest:
                        raise InteractionRepairError(
                            f"{placement}: preserved hidden item lacks canonical manifest"
                        )
                    counts["preserved_hidden_item"] += 1
                elif event.get("type") == "sign":
                    counts["preserved_sign"] += 1
                continue
            if event.get("type") == "sign":
                raw[5] = 0
                struct.pack_into("<I", raw, 8, 0)
                bg.append((bytes(raw), "script_sign"))
                counts["restored_sign"] += 1
            elif event.get("type") == "hidden_item":
                placement = str(event.get("placement_key", ""))
                if placement not in hidden_manifest:
                    raise InteractionRepairError(f"{placement}: hidden item lacks canonical manifest")
                item, flag = hidden_manifest[placement]
                script = f"script_hidden::{placement}"
                _finish_item_script(
                    blob, script, flag=flag, item=item, quantity=int(event.get("quantity", 1)),
                    object_host=False, audit=script_audit,
                )
                raw[5] = 0
                struct.pack_into("<I", raw, 8, 0)
                bg.append((bytes(raw), script))
                counts["restored_hidden_item"] += 1
            else:
                continue
            occupied_bg.add(identity)

        needs_rebuild = (
            int(current["event_header_address"]) != int(base["event_header_address"])
            or len(objects) != len(base["objects"])
            or len(bg) != int(base["counts"]["bg"])
            or map_sight_changed
        )
        if needs_rebuild:
            label = f"map::KANTO::{group:03d}_{number:03d}"
            event_label = _emit_event(blob, label, base, objects, bg)
            _, header_offset = _map_header_offset(stage49, group, number)
            patches.append({
                "kind": "map_event", "map_key": key, "group": group, "map": number,
                "site": header_offset + 4, "expected": int(current["event_header_address"]),
                "label": event_label,
            })
            rebuilt.add((group, number))
            rows.append({
                "map_key": key, "group": group, "map": number,
                "objects_stage48": len(base["objects"]), "objects_stage49": len(current["objects"]),
                "objects_stage50": len(objects), "bg_stage48": int(base["counts"]["bg"]),
                "bg_stage49": int(current["counts"]["bg"]), "bg_stage50": len(bg),
            })

    if item_index != ITEM_FLAG_COUNT:
        raise InteractionRepairError(f"Kanto item-ball inventory differs: {item_index} != {ITEM_FLAG_COUNT}")
    if counts["restored_item_ball"] + counts["preserved_item_ball"] != 129 \
            or counts["restored_cut_tree"] + counts["preserved_cut_tree"] != 33 \
            or counts["restored_rock_smash"] + counts["preserved_rock_smash"] != 40:
        raise InteractionRepairError(
            f"field-object recovery coverage differs: {dict(counts)}; omitted={omitted}"
        )
    if counts["restored_nurse"] + counts["preserved_nurse"] != 12 \
            or counts["restored_clerk"] + counts["preserved_clerk"] != 16:
        raise InteractionRepairError(f"service recovery coverage differs: {dict(counts)}")
    if counts["restored_hidden_item"] + counts["preserved_hidden_item"] != len(hidden_manifest):
        raise InteractionRepairError(
            "hidden item manifest is not fully rooted: "
            f"{counts['restored_hidden_item']} + {counts['preserved_hidden_item']} "
            f"!= {len(hidden_manifest)}"
        )
    return patches, rows, rebuilt, {
        "counts": dict(counts), "omitted": omitted,
        "source_safe_overflow": source_safe_overflow,
        "item_flag_base": ITEM_FLAG_BASE, "item_flag_count": ITEM_FLAG_COUNT,
        "hidden_item_count": len(hidden_manifest),
    }


def _plausible_unresponsive(raw: bytes) -> bool:
    fields = _object_fields(raw)
    return (
        fields["kind"] == 0
        and fields["script_pointer"] in (0, GBA_ROM_BASE)
        and fields["graphics_id"] not in (0, 108)
        and fields["x"] < 0x8000 and fields["y"] < 0x8000
    )


def _tohoku_maps(blob: _Blob, stage49: bytes, stage48: bytes,
                 group_sizes: Sequence[int]) -> tuple[list[dict[str, Any]],
                                                       list[dict[str, Any]],
                                                       set[tuple[int, int]],
                                                       dict[str, Any]]:
    force = {(3, 19), (3, 21), (3, 23)}
    patches: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    rebuilt: set[tuple[int, int]] = set()
    repaired: list[dict[str, Any]] = []
    sight = 0
    for group, size in enumerate(group_sizes):
        for number in range(int(size)):
            try:
                base = _stage_map_state(stage48, group, number)
                current = _stage_map_state(stage49, group, number)
            except (ValueError, RuntimeError):
                continue
            indices = [index for index, raw in enumerate(base["objects"])
                       if _plausible_unresponsive(raw)]
            if not indices and (group, number) not in force:
                continue
            objects, bg = _event_rows(base)
            changed: list[tuple[bytes, str | int | None]] = []
            for index, (raw, script) in enumerate(objects):
                raw, reduced = _reduce_sight(raw)
                sight += reduced
                if index in indices:
                    replacement = "script_hisui" if (group, number, index) == (3, 5, 3) \
                        else "script_repaired"
                    record = bytearray(raw)
                    struct.pack_into("<I", record, 0x10, 0)
                    raw, script = bytes(record), replacement
                    fields = _object_fields(raw)
                    repaired.append({
                        "group": group, "map": number, "object_index": index,
                        "local_id": fields["local_id"], "graphics_id": fields["graphics_id"],
                        "x": fields["x"], "y": fields["y"], "script": replacement,
                    })
                changed.append((raw, script))
            objects = changed
            label = f"map::TOHOKU::{group:03d}_{number:03d}"
            event_label = _emit_event(blob, label, base, objects, bg)
            _, header_offset = _map_header_offset(stage49, group, number)
            patches.append({
                "kind": "map_event", "map_key": f"VEGA_PHYSICAL_{group:02d}_{number:03d}",
                "group": group, "map": number, "site": header_offset + 4,
                "expected": int(current["event_header_address"]), "label": event_label,
            })
            rebuilt.add((group, number))
            rows.append({
                "group": group, "map": number, "objects": len(objects),
                "repaired_indices": indices, "stage49_raid_reverted": (group, number) in force,
            })
    hisui = [row for row in repaired if (row["group"], row["map"], row["object_index"]) == (3, 5, 3)]
    if len(hisui) != 1:
        raise InteractionRepairError("Hisui City local object 4 was not repaired exactly once")
    return patches, rows, rebuilt, {
        "repaired_objects": repaired, "repaired_count": len(repaired),
        "hisui": hisui[0], "stage49_low_raid_hosts_removed": 6,
        "sight_reduced_in_payload": sight,
    }


def _sight_patches(stage49: bytes, coordinates: Sequence[tuple[int, int]],
                   rebuilt: set[tuple[int, int]]) -> list[dict[str, Any]]:
    patches: dict[int, dict[str, Any]] = {}
    for group, number in coordinates:
        if (group, number) in rebuilt:
            continue
        try:
            state = _stage_map_state(stage49, group, number)
        except (ValueError, RuntimeError):
            continue
        objects = int(state["pointers"]["objects"])
        if not state["objects"]:
            continue
        _offset(objects, len(state["objects"]) * OBJECT_SIZE, len(stage49), "trainer object array")
        for index, raw in enumerate(state["objects"]):
            fields = _object_fields(raw)
            if fields["kind"] != 0 or fields["trainer_type"] != 1 or fields["sight_range"] <= 1:
                continue
            site = objects - GBA_ROM_BASE + index * OBJECT_SIZE + 0x0E
            replacement = fields["sight_range"] - 1
            prior = patches.get(site)
            row = {
                "kind": "trainer_sight", "group": group, "map": number,
                "object_index": index, "site": site,
                "expected": fields["sight_range"], "replacement": replacement,
            }
            if prior is not None and (prior["expected"], prior["replacement"]) != (fields["sight_range"], replacement):
                raise InteractionRepairError("shared trainer sight record has inconsistent values")
            patches[site] = row
    return [patches[site] for site in sorted(patches)]


def _wild_header_patch(stage49: bytes, blob: _Blob) -> dict[str, Any]:
    root = _u32(stage49, WILD_HEADERS_POINTER_SITE, "gWildMonHeaders root")
    root_offset = _offset(root, (EXPECTED_WILD_HEADER_COUNT + 1) * 20,
                          len(stage49), "gWildMonHeaders")
    target = None
    neighbor = None
    for index in range(EXPECTED_WILD_HEADER_COUNT):
        at = root_offset + index * 20
        coordinate = (stage49[at], stage49[at + 1])
        if coordinate == TARGET_WATERWAY:
            target = (index, at)
        if coordinate == NEIGHBOR_ROUTE:
            neighbor = (index, at)
    if target is None or neighbor is None:
        raise InteractionRepairError("511 waterway/native neighbor wild header is missing")
    target_land = _u32(stage49, target[1] + 4, "511 land pointer")
    neighbor_land = _u32(stage49, neighbor[1] + 4, "neighbor land pointer")
    if target_land != 0 or neighbor_land == 0:
        raise InteractionRepairError("511 waterway land owner precondition differs")
    return {
        "kind": "wild_land_pointer", "group": 3, "map": 29,
        "header_index": target[0], "site": target[1] + 4,
        "expected": 0, "label": "wild_511_land_info",
        "neighbor_header_index": neighbor[0], "neighbor_land": neighbor_land,
    }


def build_payload(root: Path, stage49: bytes, stage48: bytes, clean: bytes,
                  payload_offset: int, group_sizes: Sequence[int]) -> tuple[bytes, dict[str, Any],
                                                                           list[dict[str, Any]],
                                                                           list[dict[str, Any]]]:
    if len(stage49) != ROM_SIZE or len(stage48) != ROM_SIZE or len(clean) != ROM_SIZE // 2:
        raise InteractionRepairError("Stage49/Stage48/clean ROM size differs")
    blob = _Blob()
    script_audit = _shared_scripts(root, blob)
    kanto_patches, kanto_rows, kanto_rebuilt, kanto = _kanto_maps(
        root, blob, stage49, stage48, clean, script_audit,
    )
    tohoku_patches, tohoku_rows, tohoku_rebuilt, tohoku = _tohoku_maps(
        blob, stage49, stage48, group_sizes,
    )
    wild_patch = _wild_header_patch(stage49, blob)
    coordinates = [
        (group, number)
        for group, size in enumerate(group_sizes)
        for number in range(int(size))
    ]
    coordinates.extend(
        (int(row["map_header"]["group_id"]), int(row["map_header"]["map_id"]))
        for row in _read_map_catalog(root).values()
    )
    rebuilt = kanto_rebuilt | tohoku_rebuilt
    sight = _sight_patches(stage49, coordinates, rebuilt)
    payload = blob.finish(payload_offset)
    map_patches = kanto_patches + tohoku_patches
    pointer_patches = map_patches + [wild_patch]
    plan = {
        "status": "PASS", "payload_size": len(payload), "payload_sha256": _sha(payload),
        "labels": dict(blob.labels), "scripts": script_audit,
        "map_patch_count": len(map_patches), "map_rows": kanto_rows + tohoku_rows,
        "kanto": kanto, "tohoku": tohoku,
        "trainer_sight": {
            "direct_patch_count": len(sight),
            "payload_patch_count": int(kanto["counts"].get("sight_reduced_in_payload", 0))
                + int(tohoku["sight_reduced_in_payload"]),
            "policy": "max(1, authored_range - 1)",
        },
        "wild": {
            "waterway": "511ばんすいどう", "group": 3, "map": 29,
            "land_rate": 21, "land_slot_count": 12,
            "wisdom_cave_maps": [[1, 11], [1, 83], [1, 84], [1, 85], [1, 100], [3, 59]],
            "turning_does_not_advance": True, "minimum_grace_has_no_early_roll": True,
        },
        "item_abi": _audit_items(root, stage49),
        "safety": {
            "stage48_event_arrays_authoritative": True,
            "stage49_generic_welcome_removed": True,
            "stage49_ad_hoc_low_raid_removed": True,
            "fire_red_story_scripts_imported": False,
            "existing_noninvalid_tohoku_scripts_preserved": True,
        },
    }
    return payload, plan, pointer_patches, sight
