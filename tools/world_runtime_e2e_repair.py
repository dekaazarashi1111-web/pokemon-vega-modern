"""Stage51のworld interaction ownerを全物理map単位で再構築する。

Stage50の症状別wrapperを継ぎ足さず、FireRedのobject/trainer/item/wild ABIへ
戻すための純粋なpayload plannerである。生成とmGBA検証はscripts側が担当する。
"""

from __future__ import annotations

import hashlib
import json
import struct
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.interaction_ownership_repair import (
    BG_SIZE,
    CUT_SCRIPT,
    GBA_ROM_BASE,
    OBJECT_SIZE,
    ROCK_SMASH_SCRIPT,
    ROM_SIZE,
    _emit_event,
    _event_rows,
    _identity,
    _load_item_manifests,
    _source_event_arrays,
    _source_locations,
    _source_map_json,
    _standard_item,
)
from tools.regression.rom_runtime import _Blob, _charmap, _encode_text
from tools.t02.rom_inventory import RomImage, ScriptRoot, ScriptWalker
from tools.trainer_final.kanto_events import (
    _map_header_offset,
    _object_fields,
    _read_map_catalog,
    _stage_map_state,
)


TASK = "USER-20260824-STAGE51-WORLD-RUNTIME-E2E-REPAIR"
WILD_HOOK_OFFSET = 0x0006CFE8
WILD_STOCK_HOOK = bytes.fromhex("00b515f0d7ff0006")
COOLDOWN_OFFSET = 0x00082F76
COOLDOWN_STOCK = bytes.fromhex("c1f7")
TRAINER_PARTY_CONTINUATION_OFFSET = 0x010DD2AC
TRAINER_PARTY_CONTINUATION_EXPECTED = bytes.fromhex("5746e0b5a3b048f0b7ff")
TRAINER_PARTY_SETUP_FIRST_CALL = 0x09126225
TRAINER_PARTY_CONTINUATION_RETURN = 0x090DD2B7
TRAINER_TABLE_ADDRESS = 0x09329070
TRAINER_RECORD_SIZE = 0x20
TRAINER_PARTY_SIZE_OFFSET = 0x18
TRAINER_OPPONENT_A_ADDRESS = 0x020385E2
ENEMY_PARTY_COUNT_ADDRESS = 0x02023F8A
NEW_BATTLE_STRUCT_POINTER_ADDRESS = 0x0203DFB0
REMATCH_TRAINER_KINDS = {5, 7}


class WorldRuntimeRepairError(ValueError):
    """world runtimeのownerを推測なしで一意に再構築できない。"""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _script_address(metadata50: Mapping[str, Any], label: str) -> int:
    return int(metadata50["payload"]["address"]) + int(
        metadata50["interaction_plan"]["labels"][label]
    )


def _coordinates(root: Path, group_sizes: Sequence[int]) -> list[tuple[int, int]]:
    rows = [
        (group, number)
        for group, size in enumerate(group_sizes)
        for number in range(int(size))
    ]
    rows.extend(
        (
            int(row["map_header"]["group_id"]),
            int(row["map_header"]["map_id"]),
        )
        for row in _read_map_catalog(root).values()
    )
    if len(rows) != 678 or len(set(rows)) != 678:
        raise WorldRuntimeRepairError("physical map inventory is not exactly 678 unique rows")
    return sorted(rows)


def _raw_pointer(raw: bytes) -> int:
    return struct.unpack_from("<I", raw, 0x10)[0]


def _movement_type(raw: bytes) -> int:
    # ObjectEventTemplate ABI: byte 9。従来helperのbyte 3はpaddingである。
    return raw[9]


def _trainer_candidates(stage51: bytes, roots: Mapping[int, list[str]]) -> dict[int, list[dict[str, int]]]:
    rom = RomImage("Stage51", stage51)
    walker = ScriptWalker(rom)
    for address, labels in sorted(roots.items()):
        walker.add_root(ScriptRoot(address=address, label=labels[0], kind="object"))
    graph = walker.walk()
    by_root: dict[int, list[dict[str, int]]] = {address: [] for address in roots}
    label_to_root = {label: address for address, labels in roots.items() for label in labels}
    for ref in graph["references"]:
        if ref["category"] != "trainer" or ref["access"] != "battle":
            continue
        row = {
            "command_address": int(ref["instruction_address"]),
            "kind": int(ref["battle_type"]),
            "trainer_id": int(ref["value"]),
        }
        for label in ref["roots"]:
            root = label_to_root.get(label)
            if root is not None and row not in by_root[root]:
                by_root[root].append(row)
    for rows in by_root.values():
        rows.sort(key=lambda row: (row["command_address"], row["kind"], row["trainer_id"]))
    return by_root


def _select_initial_trainer(rows: Sequence[Mapping[str, int]]) -> dict[str, int] | None:
    initial = [dict(row) for row in rows if int(row["kind"]) not in REMATCH_TRAINER_KINDS]
    if not initial:
        return None
    if len(initial) == 1:
        return initial[0]
    # SINGLE_CONTINUE_SCRIPT (2) is the authored first encounter. kind 3 is a
    # no-intro auxiliary battle and must not own visual trainer detection.
    kind_two = [row for row in initial if int(row["kind"]) == 2]
    if len(kind_two) == 1:
        return kind_two[0]
    unique = {(row["command_address"], row["trainer_id"]) for row in initial}
    if len(unique) == 1:
        return initial[0]
    raise WorldRuntimeRepairError(f"trainer root has ambiguous initial commands: {initial}")


def _trainer_plan(stage51: bytes, stage48: bytes, coordinates: Sequence[tuple[int, int]]) -> tuple[dict[tuple[int, int, int], dict[str, Any]], list[dict[str, Any]]]:
    object_rows: list[tuple[int, int, int, bytes, dict[str, Any]]] = []
    roots: dict[int, list[str]] = {}
    authored_sight: dict[tuple[int, int, int], int] = {}
    for group, number in coordinates:
        try:
            current = _stage_map_state(stage51, group, number)
            baseline = _stage_map_state(stage48, group, number)
        except (ValueError, RuntimeError):
            continue
        authored_sight.update({
            (group, number, int(_object_fields(raw)["local_id"])): int(
                _object_fields(raw)["sight_range"]
            )
            for raw in baseline["objects"]
            if int(_object_fields(raw)["kind"]) == 0
            and int(_object_fields(raw)["trainer_type"]) == 1
        })
        for index, raw in enumerate(current["objects"]):
            fields = _object_fields(raw)
            if int(fields["kind"]) != 0 or int(fields["trainer_type"]) != 1:
                continue
            # Event bytecode is byte-aligned. Odd pointers are valid script
            # addresses and are not Thumb function pointers.
            address = int(fields["script_pointer"])
            label = f"trainer::{group:03d}_{number:03d}_{index:03d}"
            roots.setdefault(address, []).append(label)
            object_rows.append((group, number, index, raw, fields))
    if len(object_rows) != 829:
        raise WorldRuntimeRepairError(f"trainer template count differs: {len(object_rows)}")
    candidates = _trainer_candidates(stage51, roots)
    patches: dict[tuple[int, int, int], dict[str, Any]] = {}
    ledger: list[dict[str, Any]] = []
    for group, number, index, raw, fields in object_rows:
        root = int(fields["script_pointer"])
        selected = _select_initial_trainer(candidates[root])
        key = (group, number, index)
        local_id = int(fields["local_id"])
        sight_key = (group, number, local_id)
        if selected is None:
            patches[key] = {"script": _raw_pointer(raw), "trainer_type": 0, "sight": 0}
            disposition = "NON_RUNTIME_SPECIAL_ACTOR"
        else:
            if sight_key not in authored_sight:
                raise WorldRuntimeRepairError(f"trainer authored sight missing: {key}")
            patches[key] = {
                "script": int(selected["command_address"]),
                "trainer_type": 1,
                "sight": authored_sight[sight_key],
            }
            disposition = "RUNTIME_DIRECT_TRAINERBATTLE"
        ledger.append({
            "group": group,
            "map": number,
            "object_index": index,
            "local_id": local_id,
            "graphics_id": int(fields["graphics_id"]),
            "x": int(fields["x"]),
            "y": int(fields["y"]),
            "movement_type": _movement_type(raw),
            "authored_sight_range": authored_sight.get(sight_key),
            "stage51_sight_range": int(fields["sight_range"]),
            "stage51_script_root": root,
            "reachable_commands": candidates[root],
            "selected_command": selected,
            "disposition": disposition,
        })
    counts = Counter(row["disposition"] for row in ledger)
    if counts != {"RUNTIME_DIRECT_TRAINERBATTLE": 825, "NON_RUNTIME_SPECIAL_ACTOR": 4}:
        raise WorldRuntimeRepairError(f"trainer root classification differs: {dict(counts)}")
    return patches, ledger


def _script_item_contract(metadata50: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    base = int(metadata50["payload"]["address"])
    labels = metadata50["interaction_plan"]["labels"]
    scripts = metadata50["interaction_plan"]["scripts"]
    for label, audit in scripts.items():
        if "::already" in label or "::full" in label or "::end" in label:
            continue
        if not (label.startswith("script_item::") or label.startswith("script_hidden::")):
            continue
        operations = list(audit["operations"])
        add = next(value for value in operations if value.startswith("additem:"))
        flag = next(value for value in operations if value.startswith("checkflag:"))
        _, item, quantity = add.split(":")
        result[base + int(labels[label])] = {
            "label": label,
            "item": int(item),
            "quantity": int(quantity),
            "flag": int(flag.split(":", 1)[1], 0),
            "kind": "ITEM_BALL" if label.startswith("script_item::") else "HIDDEN_ITEM",
        }
    counts = Counter(row["kind"] for row in result.values())
    if counts != {"ITEM_BALL": 126, "HIDDEN_ITEM": 124}:
        raise WorldRuntimeRepairError(f"Stage50 item contract differs: {dict(counts)}")
    return result


def _add_finditem(blob: _Blob, label: str, item: int, quantity: int) -> None:
    # setorcopyvar VAR_8000,item; setorcopyvar VAR_8001,quantity; callstd 1; end
    raw = bytes((0x1A, 0x00, 0x80)) + struct.pack("<H", item)
    raw += bytes((0x1A, 0x01, 0x80)) + struct.pack("<H", quantity)
    raw += bytes((0x09, 0x01, 0x02))
    blob.add(label, raw, 4)


def _add_hidden_item(blob: _Blob, label: str, item: int, quantity: int, flag: int) -> None:
    # checkflag -> collected end; callstd STD_OBTAIN_ITEM -> VAR_RESULT success
    # only then set the project-width hidden flag. Bag full leaves state untouched.
    main = bytearray((0x69, 0x2B))
    main.extend(struct.pack("<H", flag))
    main.extend(bytes((0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x01)))
    collected_fixup = len(main)
    main.extend(bytes(4))
    main.extend(bytes((0x1A, 0x00, 0x80)))
    main.extend(struct.pack("<H", item))
    main.extend(bytes((0x1A, 0x01, 0x80)))
    main.extend(struct.pack("<H", quantity))
    main.extend(bytes((0x09, 0x00, 0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x01)))
    success_fixup = len(main)
    main.extend(bytes(4))
    main.extend(bytes((0x6B, 0x02)))
    start = blob.add(label, bytes(main), 4)
    success_label = f"{label}::success"
    end_label = f"{label}::end"
    blob.pointer(start + collected_fixup, end_label)
    blob.pointer(start + success_fixup, success_label)
    blob.add(success_label, bytes((0x29,)) + struct.pack("<H", flag) + bytes((0x6B, 0x02)), 1)
    blob.add(end_label, bytes((0x6B, 0x02)), 1)


def _add_text_host(blob: _Blob, label: str, text: bytes, *, object_host: bool) -> None:
    text_label = f"{label}::text"
    blob.add(text_label, text, 1)
    raw = bytearray((0x6A, 0x5A, 0x0F, 0x00) if object_host else (0x69, 0x0F, 0x00))
    fixup = len(raw)
    raw.extend(bytes(4))
    raw.extend(bytes((0x09, 0x04, 0x6C, 0x02)) if object_host else (0x09, 0x03, 0x6B, 0x02))
    start = blob.add(label, bytes(raw), 4)
    blob.pointer(start + fixup, text_label)


def _thumb_bl(site: int, target: int) -> bytes:
    delta = target - (site + 4)
    if delta & 1 or not -0x400000 <= delta < 0x400000:
        raise WorldRuntimeRepairError(
            f"Thumb BL out of range: {site:#x} -> {target:#x}"
        )
    return struct.pack(
        "<HH",
        0xF000 | ((delta >> 12) & 0x07FF),
        0xF800 | ((delta >> 1) & 0x07FF),
    )


def _add_trainer_party_count_wrapper(blob: _Blob) -> int:
    """全party builder共通継続点でlive人数とbattle snapshotを同期する。"""
    raw = bytearray(bytes.fromhex(
        "0e48"          # ldr r0, =TRAINER_OPPONENT_A_ADDRESS
        "0088"          # ldrh r0, [r0]
        "0028"          # cmp r0, #0
        "0fd0"          # beq replay
        "4001"          # lsls r0, r0, #5
        "0d49"          # ldr r1, =TRAINER_TABLE_ADDRESS
        "4018"          # adds r0, r0, r1
        "007e"          # ldrb r0, [r0, #0x18]
        "0128"          # cmp r0, #1
        "09d3"          # blo replay
        "0628"          # cmp r0, #6
        "07d8"          # bhi replay
        "0a49"          # ldr r1, =ENEMY_PARTY_COUNT_ADDRESS
        "0870"          # strb r0, [r1]
        "0a49"          # ldr r1, =NEW_BATTLE_STRUCT_POINTER_ADDRESS
        "0968"          # ldr r1, [r1]
        "0029"          # cmp r1, #0
        "01d0"          # beq replay
        "3731"          # adds r1, #0x37
        "0870"          # strb r0, [r1]
        "5746"          # replay: mov r7, r10
        "e0b5"          # push {r5, r6, r7, lr}
        "a3b0"          # sub sp, #0x8c
        "00000000"      # bl first setup call veneer
        "064b"          # ldr r3, =continuation return
        "1847"          # bx r3
        "064b"          # first-call veneer: ldr r3, literal
        "1847"          # bx r3
        "c046"          # alignment nop
    ))
    raw.extend(struct.pack(
        "<IIIII",
        TRAINER_OPPONENT_A_ADDRESS,
        TRAINER_TABLE_ADDRESS,
        ENEMY_PARTY_COUNT_ADDRESS,
        NEW_BATTLE_STRUCT_POINTER_ADDRESS,
        TRAINER_PARTY_CONTINUATION_RETURN,
    ))
    raw.extend(struct.pack("<I", TRAINER_PARTY_SETUP_FIRST_CALL))
    start = blob.add("runtime::trainer_party_count", bytes(raw), 4)
    blob.patch(start + 46, _thumb_bl(start + 46, start + 54))
    return start


def _source_map_objects(root: Path, clean: bytes, catalog_row: Mapping[str, Any], map_key: str) -> tuple[list[bytes], list[bytes]]:
    source_name = str(catalog_row["map_header"]["source_map"])
    source = _source_event_arrays(clean, _source_locations(root)[source_name], map_key)
    object_raw = source["arrays"][0]
    bg_raw = source["arrays"][3]
    return (
        [object_raw[index:index + OBJECT_SIZE] for index in range(0, len(object_raw), OBJECT_SIZE)],
        [bg_raw[index:index + BG_SIZE] for index in range(0, len(bg_raw), BG_SIZE)],
    )


def _match_source_object(current: bytes, source_objects: Sequence[bytes]) -> bytes | None:
    matches = [raw for raw in source_objects if _identity(raw) == _identity(current)]
    if len(matches) > 1:
        exact = [raw for raw in matches if _movement_type(raw) == _movement_type(current)]
        if len(exact) == 1:
            return exact[0]
    return matches[0] if len(matches) == 1 else None


def _source_authored_row(source: bytes, authored: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    fields = _object_fields(source)
    matches = [
        row for row in authored
        if int(row.get("x", -32768)) == int(fields["x"])
        and int(row.get("y", -32768)) == int(fields["y"])
    ]
    return matches[0] if len(matches) == 1 else {}


def _patch_record(raw: bytes, *, script: int | None = None,
                  trainer_type: int | None = None, sight: int | None = None) -> bytes:
    result = bytearray(raw)
    if script is not None:
        struct.pack_into("<I", result, 0x10, script)
    if trainer_type is not None:
        result[0x0C] = trainer_type
    if sight is not None:
        struct.pack_into("<H", result, 0x0E, sight)
    return bytes(result)


def build_payload(root: Path, stage51: bytes, stage48: bytes, stage03: bytes,
                  clean: bytes, metadata50: Mapping[str, Any], payload_offset: int,
                  group_sizes: Sequence[int]) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    if any(len(raw) != ROM_SIZE for raw in (stage51, stage48, stage03)) or len(clean) != ROM_SIZE // 2:
        raise WorldRuntimeRepairError("ROM size contract differs")
    coordinates = _coordinates(root, group_sizes)
    trainer_patches, trainer_ledger = _trainer_plan(stage51, stage48, coordinates)
    item_contract = _script_item_contract(metadata50)
    blob = _Blob()
    trainer_party_count_wrapper = _add_trainer_party_count_wrapper(blob)
    mapping, tokens = _charmap(root)
    hisui_text = _encode_text("ヒスイシティは\nしずかな みずべの まちです。", mapping, tokens)
    _add_text_host(blob, "script::hisui_general", hisui_text, object_host=True)
    for address, row in sorted(item_contract.items()):
        label = f"script::{row['kind'].lower()}::{address:08X}"
        if row["kind"] == "ITEM_BALL":
            _add_finditem(blob, label, int(row["item"]), int(row["quantity"]))
        else:
            _add_hidden_item(
                blob, label, int(row["item"]), int(row["quantity"]), int(row["flag"])
            )
        row["new_label"] = label

    catalog = _read_map_catalog(root)
    catalog_by_coord = {
        (int(row["map_header"]["group_id"]), int(row["map_header"]["map_id"])): (key, row)
        for key, row in catalog.items()
    }
    generic_object_addresses = {
        _script_address(metadata50, name)
        for name in ("script_outdoor", "script_indoor", "script_dungeon")
    }
    generic_sign = _script_address(metadata50, "script_sign")
    repaired = _script_address(metadata50, "script_repaired")
    hisui = _script_address(metadata50, "script_hisui")
    map_patches: list[dict[str, Any]] = []
    owner_rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for group, number in coordinates:
        try:
            state = _stage_map_state(stage51, group, number)
        except (ValueError, RuntimeError):
            owner_rows.append({
                "event": "MAP", "group": group, "map": number,
                "role": "NO_VALID_EVENT_HEADER",
            })
            counts["NO_VALID_EVENT_HEADER"] += 1
            continue
        try:
            base03 = _stage_map_state(stage03, group, number)
        except (ValueError, RuntimeError):
            base03 = {"objects": []}
        objects, bg = _event_rows(state)
        source_objects: list[bytes] = []
        source_bg: list[bytes] = []
        source_authored_objects: list[dict[str, Any]] = []
        if (group, number) in catalog_by_coord:
            map_key, catalog_row = catalog_by_coord[(group, number)]
            source_objects, source_bg = _source_map_objects(root, clean, catalog_row, map_key)
            source_name = str(catalog_row["map_header"]["source_map"])
            source_authored_objects = list(
                _source_map_json(root, source_name).get("object_events", [])
            )
        changed = False
        new_objects: list[tuple[bytes, str | int | None]] = []
        base03_by_local = {
            int(_object_fields(raw)["local_id"]): raw for raw in base03["objects"]
        }
        for index, (raw, _) in enumerate(objects):
            fields = _object_fields(raw)
            old_script = int(fields["script_pointer"])
            label_or_pointer: str | int | None = None
            role = "EXISTING_PROJECT_OWNER"
            detail: dict[str, Any] = {}
            trainer_patch = trainer_patches.get((group, number, index))
            if trainer_patch is not None:
                raw = _patch_record(
                    raw,
                    script=int(trainer_patch["script"]),
                    trainer_type=int(trainer_patch["trainer_type"]),
                    sight=int(trainer_patch["sight"]),
                )
                role = "TRAINER" if trainer_patch["trainer_type"] else "NON_RUNTIME_SPECIAL_ACTOR"
                changed = True
            elif old_script in item_contract and item_contract[old_script]["kind"] == "ITEM_BALL":
                label_or_pointer = str(item_contract[old_script]["new_label"])
                role = "ITEM_BALL_STD_FIND_ITEM"
                detail = {key: item_contract[old_script][key] for key in ("item", "quantity", "flag")}
                changed = True
            elif GBA_ROM_BASE <= old_script < GBA_ROM_BASE + len(stage51) \
                    and _standard_item(stage51, old_script - GBA_ROM_BASE) is not None:
                role = "ITEM_BALL_EXISTING_STD_FIND_ITEM"
                detail = {
                    "item": int(_standard_item(stage51, old_script - GBA_ROM_BASE)),
                    "quantity": 1,
                    "flag": int(fields["flag"]),
                }
            elif old_script in generic_object_addresses:
                source = _match_source_object(raw, source_objects)
                source_pointer = _raw_pointer(source) if source is not None else 0
                label_or_pointer = source_pointer
                if source_pointer == 0:
                    role = "SOURCE_DYNAMIC_OR_MAP_SCRIPT_ACTOR"
                else:
                    authored = _source_authored_row(source, source_authored_objects)
                    role = "SOURCE_DIRECT_OBJECT_OWNER"
                    detail = {
                        "source_script_pointer": source_pointer,
                        "source_script_label": str(authored.get("script", "")),
                        "source_local_id": str(authored.get("local_id", "")),
                    }
                changed = True
            elif old_script == repaired:
                local_id = int(fields["local_id"])
                source = base03_by_local.get(local_id)
                label_or_pointer = _raw_pointer(source) if source is not None else 0
                role = "VEGA_DYNAMIC_OR_MAP_SCRIPT_ACTOR"
                changed = True
            elif old_script == hisui:
                label_or_pointer = "script::hisui_general"
                role = "HISUI_AUTHORED_DIALOGUE"
                changed = True
            elif old_script == CUT_SCRIPT:
                role = "FIELD_CUT"
            elif old_script == ROCK_SMASH_SCRIPT:
                role = "FIELD_ROCK_SMASH"
            if isinstance(label_or_pointer, int):
                raw = _patch_record(raw, script=label_or_pointer)
            new_objects.append((raw, label_or_pointer if isinstance(label_or_pointer, str) else None))
            counts[role] += 1
            owner_rows.append({
                "event": "OBJECT", "group": group, "map": number, "index": index,
                "local_id": int(fields["local_id"]), "graphics_id": int(fields["graphics_id"]),
                "x": int(fields["x"]), "y": int(fields["y"]),
                "movement_type": _movement_type(raw), "role": role,
                "stage51_script": old_script, **detail,
            })

        new_bg: list[tuple[bytes, str | int | None]] = []
        for index, (raw, _) in enumerate(bg):
            pointer = struct.unpack_from("<I", raw, 8)[0]
            label_or_pointer: str | int | None = None
            role = "EXISTING_BG_OWNER"
            detail: dict[str, Any] = {}
            if pointer in item_contract and item_contract[pointer]["kind"] == "HIDDEN_ITEM":
                label_or_pointer = str(item_contract[pointer]["new_label"])
                role = "HIDDEN_ITEM_STD_OBTAIN_ITEM"
                detail = {key: item_contract[pointer][key] for key in ("item", "quantity", "flag")}
                changed = True
            elif pointer == generic_sign:
                x, y = struct.unpack_from("<HH", raw, 0)
                matches = [row for row in source_bg if struct.unpack_from("<HH", row, 0) == (x, y)]
                source_pointer = struct.unpack_from("<I", matches[0], 8)[0] if len(matches) == 1 else 0
                label_or_pointer = source_pointer
                role = (
                    "SOURCE_DIRECT_BG_OWNER" if source_pointer
                    else "SOURCE_DYNAMIC_OR_SPECIAL_BG_OWNER"
                )
                if source_pointer:
                    detail = {"source_script_pointer": source_pointer}
                changed = True
            raw_copy = bytearray(raw)
            if isinstance(label_or_pointer, int):
                struct.pack_into("<I", raw_copy, 8, label_or_pointer)
            new_bg.append((bytes(raw_copy), label_or_pointer if isinstance(label_or_pointer, str) else None))
            counts[role] += 1
            owner_rows.append({
                "event": "BG", "group": group, "map": number, "index": index,
                "x": struct.unpack_from("<H", raw, 0)[0],
                "y": struct.unpack_from("<H", raw, 2)[0],
                "role": role, "stage51_script": pointer, **detail,
            })
        if changed:
            label = f"map::{group:03d}_{number:03d}"
            event_label = _emit_event(blob, label, state, new_objects, new_bg)
            _, header_offset = _map_header_offset(stage51, group, number)
            map_patches.append({
                "kind": "map_event", "group": group, "map": number,
                "site": header_offset + 4,
                "expected": int(state["event_header_address"]),
                "label": event_label,
            })

    payload = blob.finish(payload_offset)
    trainer_counts = Counter(row["disposition"] for row in trainer_ledger)
    required = {
        "SOURCE_DIRECT_OBJECT_OWNER": 469,
        "SOURCE_DYNAMIC_OR_MAP_SCRIPT_ACTOR": 24,
        "SOURCE_DIRECT_BG_OWNER": 375,
        "ITEM_BALL_STD_FIND_ITEM": 126,
        "HIDDEN_ITEM_STD_OBTAIN_ITEM": 124,
        "ITEM_BALL_EXISTING_STD_FIND_ITEM": 136,
        "FIELD_CUT": 47,
        "FIELD_ROCK_SMASH": 124,
        "HISUI_AUTHORED_DIALOGUE": 1,
    }
    for key, value in required.items():
        if counts[key] != value:
            raise WorldRuntimeRepairError(
                f"{key} coverage differs: {counts[key]} != {value}; all={dict(counts)}"
            )
    plan = {
        "status": "PASS", "task": TASK,
        "payload_size": len(payload), "payload_sha256": _sha(payload),
        "labels": dict(blob.labels), "map_patch_count": len(map_patches),
        "owner_counts": dict(sorted(counts.items())), "owner_rows": owner_rows,
        "trainer": {
            "template_count": len(trainer_ledger),
            "dispositions": dict(trainer_counts), "rows": trainer_ledger,
            "root_opcode": 0x5C, "authored_sight_restored": True,
            "party_count_wrapper_label": "runtime::trainer_party_count",
            "party_count_wrapper_offset": trainer_party_count_wrapper,
            "enemy_party_count_loader_repaired": True,
        },
        "items": {
            "item_ball_count": 262, "kanto_item_ball_scope_count": 129,
            "hidden_item_count": 124,
            "item_ball_flow": "STD_FIND_ITEM", "hidden_item_flow": "STD_OBTAIN_ITEM",
            "bag_full_commit_guard": True,
        },
        "source_owner_restore": {
            "object_direct_count": counts["SOURCE_DIRECT_OBJECT_OWNER"],
            "object_dynamic_count": counts["SOURCE_DYNAMIC_OR_MAP_SCRIPT_ACTOR"],
            "bg_direct_count": counts["SOURCE_DIRECT_BG_OWNER"],
            "strategy": "EXACT_CLEAN_SOURCE_SCRIPT_ROOT",
        },
        "wild": {
            "global_wrapper_removed": True, "minimum_step_patch_removed": True,
            "stock_hook_hex": WILD_STOCK_HOOK.hex(), "stock_cooldown_hex": COOLDOWN_STOCK.hex(),
        },
        "stage50_payload_reachability_allowlist": [
            "script_heal", "script_mart", "wild_511_land_info"
        ],
    }
    return payload, plan, map_patches
