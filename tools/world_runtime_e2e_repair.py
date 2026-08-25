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
WILD_STAGE51_HOOK = bytes.fromhex("004b184781cf3d09")
WILD_HEADER_ROOT_POINTER_OFFSET = 0x0008257C
WILD_LEGACY_TABLE_ADDRESS = 0x08390B34
WILD_HEADER_CONSUMER_COUNT = 13
COOLDOWN_OFFSET = 0x00082F76
COOLDOWN_STOCK = bytes.fromhex("c1f7")
TRAINER_PARTY_HOOK_OFFSET = 0x01096EC4
TRAINER_PARTY_HOOK_EXPECTED = bytes.fromhex("33f3a6ff")
TRAINER_PARTY_DELEGATE = 0x093CAE15
TRAINER_TABLE_ADDRESS = 0x09329070
TRAINER_RECORD_SIZE = 0x20
TRAINER_PARTY_SIZE_OFFSET = 0x18
TRAINER_OPPONENT_A_ADDRESS = 0x020385E2
ENEMY_PARTY_COUNT_ADDRESS = 0x02023F8A
TRAINER_SCRIPT_FLAG_SCANNER_OFFSET = 0x0007FA98
TRAINER_SCRIPT_FLAG_SCANNER_EXPECTED = bytes.fromhex("00b50230fff794fe")
TRAINER_FLAG_MAP_ADDRESS = 0x09303CA8
TRAINER_FLAG_MAP_COUNT = 372
STOCK_TRAINER_BATTLE_LOAD_ARG16 = 0x0807F7C9
STOCK_FLAG_GET = 0x0806DEC5
CONTINUE_RECAP_BRANCH_OFFSET = 0x0111AA2
CONTINUE_RECAP_BRANCH_EXPECTED = bytes.fromhex("0fd0")
CONTINUE_RECAP_BRANCH_DISABLED = bytes.fromhex("0fe0")
NEW_BATTLE_STRUCT_POINTER_ADDRESS = 0x0203DFB0
REMATCH_TRAINER_KINDS = {5, 7}
INVALID_OBJECT_SCRIPT_POINTERS = {0, GBA_ROM_BASE}
PRIMARY_METATILE_COUNT = 0x280
WATERWAY_GROUP = 3
WATERWAY_MAP = 29
WATERWAY_LAND_METATILES = (0x009, 0x011)
CODEX_OPPONENT_CONTROLLER = 0x093C9D11
CODEX_ACTIVE_BATTLER_ADDRESS = 0x02023B24
CODEX_RUNTIME_ACTIVE_ADDRESS = 0x0203FA14
CODEX_RUNTIME_LAST_REQUEST_ADDRESS = 0x0203FA44
CODEX_RUNTIME_REQUEST_COMMAND_ADDRESS = 0x0203F9AA
CODEX_RUNTIME_REQUEST_SEQUENCE_ADDRESS = 0x0203F9FC
CODEX_READ_KEYS_POINTER_OFFSET = 0x000005EC
CODEX_READ_KEYS_TOP_ADAPTER = 0x093D1F99
CODEX_READ_KEYS_BRIDGE_ADAPTER = 0x093C99AD
CODEX_CHOICE_ROUTES = (
    (0x0020D484, 0x08037D01, "choose_action"),
    (0x0020D48C, 0x08037D1D, "choose_move"),
    (0x0020D494, 0x08037EB1, "choose_pokemon"),
)
REWARD_READ_KEYS_RESTORE_CALL_OFFSET = 0x013D1FA0
REWARD_READ_KEYS_RESTORE_CALL_EXPECTED = bytes.fromhex("01f04efe")
REWARD_READ_KEYS_RESTORE_CALL_DISABLED = bytes.fromhex("c046c046")
REWARD_RESTORE_BUFFER_LITERAL_OFFSET = 0x013D3D3C
REWARD_RESTORE_SHARED_BUFFER = 0x020399B0
REWARD_RESTORE_PRIVATE_BUFFER = 0x0203E300
SAVE_BLOCK1_POINTER_ADDRESS = 0x03005048
SPECIAL_VAR_8000_ADDRESS = 0x02036FEC
SPECIAL_VAR_RESULT_ADDRESS = 0x02037004
FIELD_INPUT_OWNER_HOOK_OFFSET = 0x0006C2BC
FIELD_INPUT_OWNER_HOOK_EXPECTED = bytes.fromhex("f0b5474680b482b0")
FIELD_INPUT_STOCK_BODY = 0x0806C2C5
SCRIPT_CONTEXT_IS_ENABLED = 0x08069219
BATTLE_TRANSITION_START_HOOK_OFFSET = 0x000D1978
BATTLE_TRANSITION_START_HOOK_EXPECTED = bytes.fromhex("30b5041c2406240e")
STOCK_BATTLE_TRANSITION_START_BODY = 0x080D1981
BROKEN_BATTLE_TRANSITION = 4
SAFE_BATTLE_TRANSITION = 8
REWARD_SCIENTIST_COORDINATE = (96, 5, 5)
REWARD_SCIENTIST_POSITION = (25, 7)
REWARD_SCIENTIST_SCRIPT_ADDRESS = 0x093C330C
REWARD_SCIENTIST_FIELD_NATIVE = 0x093C10E9
REWARD_SCIENTIST_SCRIPT_EXPECTED = bytes.fromhex("6a5a23e9103c09276c02")
REWARD_BUSY = 9


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
                # CFRU's sight engine reads the battle type and defeat flag
                # directly from bytes 0..3 of the object script.  Legacy
                # Vega roots which begin with a branch are therefore not
                # valid trainer roots here.  Rematch commands remain owned by
                # their separate rematch consumers; the visible object owns
                # the selected initial command.
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
    if counts != {
        "RUNTIME_DIRECT_TRAINERBATTLE": 825,
        "NON_RUNTIME_SPECIAL_ACTOR": 4,
    }:
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


def _add_finditem(blob: _Blob, label: str, item: int, quantity: int, flag: int) -> None:
    """stock finditem成功後のexpanded object flagを直接確定する。

    STD_FIND_ITEMはitem名、pocket、fanfare、Bag full、removeobjectを正しく
    所有する。一方、0x140D以降のproject flagはQuest Log記録中の次入力で
    byte復元されるため、STD側が実際にflagを立てた場合だけnative setterで
    同じbitを再確定する。既所持itemではなくobject flagを成功判定に使うので、
    Bag fullと元から同種itemを持つ場合も誤commitしない。
    """
    main = bytearray((0x1A, 0x00, 0x80))
    main.extend(struct.pack("<H", item))
    main.extend(bytes((0x1A, 0x01, 0x80)))
    main.extend(struct.pack("<H", quantity))
    main.extend(bytes((0x09, 0x01)))
    main.extend(bytes((0x1A, 0x00, 0x80)))
    main.extend(struct.pack("<H", flag))
    main.append(0x23)
    get_fixup = len(main)
    main.extend(bytes(4))
    main.extend(bytes((0x21, 0x0D, 0x80, 0x01, 0x00, 0x06, 0x01)))
    success_fixup = len(main)
    main.extend(bytes(4))
    main.append(0x02)
    start = blob.add(label, bytes(main), 4)
    success_label = f"{label}::success"
    blob.pointer(start + get_fixup, "runtime::hidden_flag_get", thumb=True)
    blob.pointer(start + success_fixup, success_label)

    success = bytearray((0x1A, 0x00, 0x80))
    success.extend(struct.pack("<H", flag))
    success.append(0x23)
    set_fixup = len(success)
    success.extend(bytes(4))
    success.append(0x02)
    success_start = blob.add(success_label, bytes(success), 1)
    blob.pointer(success_start + set_fixup, "runtime::hidden_flag_set", thumb=True)


def _add_hidden_flag_runtime(blob: _Blob) -> None:
    """Quest Logのbyte復元を迂回してexpanded save flagを直接扱う。"""
    get_raw = struct.pack(
        "<22HIII",
        0x480A, 0x8800, 0x08C1, 0x2307, 0x4018, 0x4A09,
        0x6812, 0x23EE, 0x011B, 0x18D2, 0x1852, 0x7812,
        0x2301, 0x4083, 0x401A, 0x2A00, 0xD000, 0x2201,
        0x4803, 0x8002, 0x4770, 0x46C0,
        SPECIAL_VAR_8000_ADDRESS, SAVE_BLOCK1_POINTER_ADDRESS,
        SPECIAL_VAR_RESULT_ADDRESS,
    )
    set_raw = struct.pack(
        "<18HII",
        0x4808, 0x8800, 0x08C1, 0x2307, 0x4018, 0x4A07,
        0x6812, 0x23EE, 0x011B, 0x18D2, 0x1852, 0x7811,
        0x2301, 0x4083, 0x4319, 0x7011, 0x4770, 0x46C0,
        SPECIAL_VAR_8000_ADDRESS, SAVE_BLOCK1_POINTER_ADDRESS,
    )
    blob.add("runtime::hidden_flag_get", get_raw, 4)
    blob.add("runtime::hidden_flag_set", set_raw, 4)


def _add_hidden_item(blob: _Blob, label: str, item: int, quantity: int, flag: int) -> None:
    # Quest Log記録中もexpanded flagを巻き戻さないnative read/writeを使う。
    # STD_OBTAIN_ITEM成功後だけflagをcommitし、Bag fullは未取得のまま残す。
    main = bytearray((0x69, 0x1A, 0x00, 0x80))
    main.extend(struct.pack("<H", flag))
    main.append(0x23)
    get_fixup = len(main)
    main.extend(bytes(4))
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
    blob.pointer(start + get_fixup, "runtime::hidden_flag_get", thumb=True)
    blob.pointer(start + collected_fixup, end_label)
    blob.pointer(start + success_fixup, success_label)
    success = bytearray((0x1A, 0x00, 0x80))
    success.extend(struct.pack("<H", flag))
    success.append(0x23)
    set_fixup = len(success)
    success.extend(bytes(4))
    success.extend(bytes((0x6B, 0x02)))
    success_start = blob.add(success_label, bytes(success), 1)
    blob.pointer(success_start + set_fixup, "runtime::hidden_flag_set", thumb=True)
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


def _add_reward_scientist_safe_script(blob: _Blob) -> None:
    """同期終了時だけwaitstateを迂回し、非同期メニューだけ完了を待つ。"""
    root = bytearray((0x6A, 0x5A, 0x23))
    root.extend(struct.pack("<I", REWARD_SCIENTIST_FIELD_NATIVE))
    root.append(0x21)  # compare LASTRESULT, REWARD_BUSY
    root.extend(struct.pack("<HH", 0x800D, REWARD_BUSY))
    root.extend((0x06, 0x01))  # goto_if equal
    wait_fixup = len(root)
    root.extend(bytes(4))
    root.extend((0x6C, 0x02))
    start = blob.add("script::reward_encounter_scientist_safe", bytes(root), 4)
    blob.pointer(start + wait_fixup, "script::reward_encounter_scientist_wait")
    blob.add(
        "script::reward_encounter_scientist_wait",
        bytes((0x27, 0x6C, 0x02)),
        1,
    )


def _add_opponent_choice_router(blob: _Blob, label: str, stock: int) -> int:
    """Codex activeのbank 1だけCodexへ渡し、全通常戦はstock AIへ戻す。"""
    raw = struct.pack(
        "<12HIIII",
        0x4805,  # ldr r0, =gCodexBattleRuntimeState.active
        0x7800,  # ldrb r0, [r0]
        0x2800,  # cmp r0, #0
        0xD005,  # beq stock
        0x4804,  # ldr r0, =gActiveBattler
        0x7800,  # ldrb r0, [r0]
        0x2801,  # cmp r0, #1
        0xD101,  # bne stock
        0x4B03,  # codex: ldr r3, =Codex controller
        0x4718,  # bx r3
        0x4B03,  # stock: ldr r3, =stock
        0x4718,  # bx r3
        CODEX_RUNTIME_ACTIVE_ADDRESS,
        CODEX_ACTIVE_BATTLER_ADDRESS,
        CODEX_OPPONENT_CONTROLLER,
        stock,
    )
    return blob.add(label, raw, 4)


def _add_world_read_keys_router(blob: _Blob) -> int:
    """通常worldはT26 bridge、明示Codex requestだけT27+へ渡す。

    T27以降のmailbox pollはprivate battle stateのCRC・party snapshotを扱うため、
    通常fieldへ毎frame常駐させない。active match、未処理のcommit済みrequest
    （command 1..20）だけ現行top adapterへ渡し、それ以外は安全なT26 bridge
    まで戻す。処理済みsequenceを比較するため、古いrequestも再pollしない。
    """
    raw = struct.pack(
        "<26H6I",
        0x480C, 0x7800, 0x2800, 0xD111,
        0x490B, 0x6808, 0x2800, 0xD00F,
        0x3904, 0x680A, 0x43C3, 0x429A, 0xD10A,
        0x4908, 0x6809, 0x4288, 0xD006,
        0x4907, 0x8809, 0x3901, 0x2913, 0xD801,
        0x4B05, 0x4718, 0x4B05, 0x4718,
        CODEX_RUNTIME_ACTIVE_ADDRESS,
        CODEX_RUNTIME_REQUEST_SEQUENCE_ADDRESS,
        CODEX_RUNTIME_LAST_REQUEST_ADDRESS,
        CODEX_RUNTIME_REQUEST_COMMAND_ADDRESS,
        CODEX_READ_KEYS_TOP_ADAPTER,
        CODEX_READ_KEYS_BRIDGE_ADAPTER,
    )
    if len(raw) != 76:
        raise WorldRuntimeRepairError("world ReadKeys router sizeが不正です")
    return blob.add("runtime::world_read_keys_router", raw, 4)


def _add_field_input_script_owner(blob: _Blob) -> int:
    """stock未処理のscript中Aだけをfield移動側へ漏らさない。"""
    raw = bytes.fromhex(
        "10b5047801210c4000f00cf8012806d0002c04d000f00cf8"
        "002800d0012010bc02bc0847f0b5474680b482b0014b1847"
        "014b1847"
    ) + struct.pack("<II", FIELD_INPUT_STOCK_BODY, SCRIPT_CONTEXT_IS_ENABLED)
    if len(raw) != 60:
        raise WorldRuntimeRepairError("field input script owner sizeが不正です")
    return blob.add("runtime::field_input_script_owner", raw, 4)


def _add_direction_wild_encounter(blob: _Blob) -> int:
    """同一map内のplayer座標が変わった完了歩を一度だけstock遭遇へ渡す。"""
    raw = bytes.fromhex(
        "31b51e494a790f2a33d824235a431c4951180d1c2a780123"
        "1a422ad0194c2188194a91421bd1a179aa7a914217d1e179"
        "6a7a914213d161882a8a914203d1a1886a8a914215d0298a"
        "6180698aa180a97aa171697ae17131bc02bc0c4b18470a4a"
        "2280298a6180698aa180a97aa171697ae17132bc02bc0020"
        "08470000"
    ) + struct.pack(
        "<5I", 0x02036FAC, 0x02036D6C, 0x0203EDF0,
        0x0000A753, 0x08082F9D,
    )
    if len(raw) != 144:
        raise WorldRuntimeRepairError("completed-step wild encounter adapter sizeが不正です")
    return blob.add("runtime::moving_wild_encounter", raw, 4)


def _add_battle_transition_router(blob: _Blob) -> int:
    """停止するPokeballsTrailだけをstock Slice演出へ正規化する。

    BattleTransition_StartOnField入口の上書き済み8 byteを再生し、残りの
    stock本体へ戻すため、全field battleの共通経路で同じ修正になる。
    """
    raw = struct.pack(
        "<10HI",
        0x2804,  # cmp r0, #B_TRANSITION_POKEBALLS_TRAIL
        0xD100,  # bne stock
        0x2008,  # movs r0, #B_TRANSITION_SLICE
        0xB530,  # stock: push {r4, r5, lr}
        0x1C04,  # movs r4, r0
        0x0624,  # lsls r4, r4, #24
        0x0E24,  # lsrs r4, r4, #24
        0x4B01,  # ldr r3, =BattleTransition_StartOnField + 8
        0x4718,  # bx r3
        0x46C0,  # alignment nop
        STOCK_BATTLE_TRANSITION_START_BODY,
    )
    if len(raw) != 24:
        raise WorldRuntimeRepairError("battle transition router sizeが不正です")
    return blob.add("runtime::battle_transition_router", raw, 4)


def _add_waterway_land_tileset(blob: _Blob, stage51: bytes) -> tuple[str, dict[str, Any]]:
    """3/29だけ雪上の歩行地面をland encounterへ接続する。"""
    _, header_offset = _map_header_offset(stage51, WATERWAY_GROUP, WATERWAY_MAP)
    layout_pointer = struct.unpack_from("<I", stage51, header_offset)[0]
    layout_offset = layout_pointer - GBA_ROM_BASE
    primary_pointer = struct.unpack_from("<I", stage51, layout_offset + 16)[0]
    primary_offset = primary_pointer - GBA_ROM_BASE
    attributes_pointer = struct.unpack_from("<I", stage51, primary_offset + 20)[0]
    attributes_offset = attributes_pointer - GBA_ROM_BASE
    header = bytearray(stage51[primary_offset:primary_offset + 24])
    attributes = bytearray(stage51[
        attributes_offset:attributes_offset + PRIMARY_METATILE_COUNT * 4
    ])
    if len(header) != 24 or len(attributes) != PRIMARY_METATILE_COUNT * 4:
        raise WorldRuntimeRepairError("511番水道primary tileset ABIが不正")
    before: dict[str, str] = {}
    for metatile in WATERWAY_LAND_METATILES:
        value = struct.unpack_from("<I", attributes, metatile * 4)[0]
        before[f"0x{metatile:03X}"] = f"0x{value:08X}"
        value = (value & ~0x03000000) | 0x01000000
        struct.pack_into("<I", attributes, metatile * 4, value)
    attributes_label = "runtime::waterway_511_primary_attributes"
    header_label = "runtime::waterway_511_primary_tileset"
    blob.add(attributes_label, bytes(attributes), 4)
    start = blob.add(header_label, bytes(header), 4)
    blob.pointer(start + 20, attributes_label)
    return header_label, {
        "group": WATERWAY_GROUP,
        "map": WATERWAY_MAP,
        "layout_pointer": layout_pointer,
        "site": layout_offset + 16,
        "expected": primary_pointer,
        "source_attributes": attributes_pointer,
        "land_metatiles": list(WATERWAY_LAND_METATILES),
        "before": before,
    }


def _wild_header_consumer_sites(stage51: bytes) -> tuple[int, list[int]]:
    """拡張header検索と同じ正本を全stock consumerへ接続する。"""
    root = struct.unpack_from("<I", stage51, WILD_HEADER_ROOT_POINTER_OFFSET)[0]
    if not GBA_ROM_BASE <= root < GBA_ROM_BASE + ROM_SIZE or root & 3:
        raise WorldRuntimeRepairError("wild header root pointerがROM ABI外です")
    legacy_info = struct.pack("<I", WILD_LEGACY_TABLE_ADDRESS)
    sites = [
        offset
        for offset in range(0, len(stage51) - 3, 4)
        if stage51[offset:offset + 4] == legacy_info
    ]
    if len(sites) != WILD_HEADER_CONSUMER_COUNT:
        raise WorldRuntimeRepairError(
            f"legacy wild header consumer数が不正です: {len(sites)}"
        )
    return root, sites


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
    """全adapter chain完了後に正規のlive敵人数だけを同期する。"""
    raw = bytearray(struct.pack(
        "<24HIIII",
        0xB510,       # push {r4, lr}
        0x0000, 0x0000,  # bl delegate veneer
        0x480A,       # ldr r0, =TRAINER_OPPONENT_A_ADDRESS
        0x8800,       # ldrh r0, [r0]
        0x2800,       # cmp r0, #0
        0xD008,       # beq done
        0x0140,       # lsls r0, r0, #5
        0x4908,       # ldr r1, =TRAINER_TABLE_ADDRESS
        0x1840,       # adds r0, r0, r1
        0x7E00,       # ldrb r0, [r0, #0x18]
        0x1E41,       # subs r1, r0, #1
        0x2905,       # cmp r1, #5
        0xD801,       # bhi done
        0x4906,       # ldr r1, =ENEMY_PARTY_COUNT_ADDRESS
        0x7008,       # strb r0, [r1]
        0xBC10,       # done: pop {r4}
        0xBC01,       # pop {r0}
        0x4700,       # bx r0
        0x46C0,       # alignment nop
        0x4B04,       # delegate veneer: ldr r3, =delegate
        0x4718,       # bx r3
        0x46C0, 0x46C0,
        TRAINER_OPPONENT_A_ADDRESS,
        TRAINER_TABLE_ADDRESS,
        ENEMY_PARTY_COUNT_ADDRESS,
        TRAINER_PARTY_DELEGATE,
    ))
    start = blob.add("runtime::trainer_party_count", bytes(raw), 4)
    blob.patch(start + 2, _thumb_bl(start + 2, start + 40))
    return start


def _add_trainer_script_flag_scanner(blob: _Blob, stage51: bytes) -> int:
    """視線判定をV5のexternal->physical flag表へ直接接続する。

    高位overlayのruntime entryをフィールドobject scannerから再入すると
    callback/EWRAMを失うため、保存ABIと同じ生成済み表だけを参照し、stock
    FlagGetへ戻す小さいleaf adapterにする。
    """
    table_offset = TRAINER_FLAG_MAP_ADDRESS - GBA_ROM_BASE
    table_size = TRAINER_FLAG_MAP_COUNT * 4
    if table_offset < 0 or table_offset + table_size > len(stage51):
        raise WorldRuntimeRepairError("trainer flag mapがStage51 ROM外です")
    rows = [
        struct.unpack_from("<HH", stage51, table_offset + index * 4)
        for index in range(TRAINER_FLAG_MAP_COUNT)
    ]
    if rows != sorted(rows) or len({external for external, _ in rows}) != len(rows):
        raise WorldRuntimeRepairError("trainer flag mapが一意な昇順表ではありません")
    # Route 506 trainer 1338はexternal 0xA3Aからsave-backed physical 0x7ADへ
    # 写る。ここを固定probeにして誤ったtable/address/countを早期検出する。
    if dict(rows).get(0x500 + 1338) != 0x7AD:
        raise WorldRuntimeRepairError("trainer flag mapの固定probeが不一致です")

    raw = bytes.fromhex(
        "f0b5023000f020f80004040ca020c00024182404240c00250d4e0e4bb542"
        "0dd2af197f08b800c0180188a14204d001d87d1cf3e73e1cf1e7408800e0"
        "201c00f005f8f0bc02bc0847034b1847034b184774010000a83c3009c9f7"
        "0708c5de0608"
    )
    if len(raw) != 96:
        raise WorldRuntimeRepairError("trainer flag scanner adapter sizeが不正です")
    if struct.unpack_from("<I", raw, 0x54)[0] != TRAINER_FLAG_MAP_ADDRESS \
            or struct.unpack_from("<I", raw, 0x58)[0] != STOCK_TRAINER_BATTLE_LOAD_ARG16 \
            or struct.unpack_from("<I", raw, 0x5C)[0] != STOCK_FLAG_GET:
        raise WorldRuntimeRepairError("trainer flag scanner adapter literalが不正です")
    return blob.add("runtime::trainer_script_flag_scanner", raw, 4)


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
    _add_trainer_script_flag_scanner(blob, stage51)
    _add_hidden_flag_runtime(blob)
    _add_world_read_keys_router(blob)
    _add_field_input_script_owner(blob)
    _add_direction_wild_encounter(blob)
    _add_battle_transition_router(blob)
    mapping, tokens = _charmap(root)
    hisui_text = _encode_text("ヒスイシティは\nしずかな みずべの まちです。", mapping, tokens)
    _add_text_host(blob, "script::hisui_general", hisui_text, object_host=True)
    recovered_text = _encode_text(
        "この ばしょを\nみまもっています。", mapping, tokens
    )
    _add_text_host(blob, "script::recovered_npc", recovered_text, object_host=True)
    _add_reward_scientist_safe_script(blob)
    for address, row in sorted(item_contract.items()):
        label = f"script::{row['kind'].lower()}::{address:08X}"
        if row["kind"] == "ITEM_BALL":
            _add_finditem(
                blob, label, int(row["item"]), int(row["quantity"]), int(row["flag"])
            )
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
        _, map_header_offset = _map_header_offset(stage51, group, number)
        layout_pointer = struct.unpack_from("<I", stage51, map_header_offset)[0]
        layout_offset = layout_pointer - GBA_ROM_BASE
        map_width, map_height = struct.unpack_from("<II", stage51, layout_offset)
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
            object_key = (group, number, int(fields["local_id"]))
            if object_key == REWARD_SCIENTIST_COORDINATE:
                if (
                    (int(fields["x"]), int(fields["y"]))
                    != REWARD_SCIENTIST_POSITION
                    or old_script != REWARD_SCIENTIST_SCRIPT_ADDRESS
                    or stage51[
                        old_script - GBA_ROM_BASE:
                        old_script - GBA_ROM_BASE + len(REWARD_SCIENTIST_SCRIPT_EXPECTED)
                    ] != REWARD_SCIENTIST_SCRIPT_EXPECTED
                ):
                    raise WorldRuntimeRepairError(
                        "96/5 local 5 reward scientist physical/script contract differs"
                    )
                label_or_pointer = "script::reward_encounter_scientist_safe"
                role = "REWARD_ENCOUNTER_SCIENTIST_FINITE_WAIT"
                detail = {
                    "original_script": old_script,
                    "field_native": REWARD_SCIENTIST_FIELD_NATIVE,
                    "synchronous_waitstate_bypassed": True,
                }
                changed = True
            elif trainer_patch is not None:
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
                if source_pointer == 0:
                    label_or_pointer = "script::recovered_npc"
                    role = "SOURCE_RECOVERED_FINITE_DIALOGUE"
                else:
                    label_or_pointer = source_pointer
                    authored = _source_authored_row(source, source_authored_objects)
                    role = "SOURCE_DIRECT_OBJECT_OWNER"
                    detail = {
                        "source_script_pointer": source_pointer,
                        "source_script_label": str(authored.get("script", "")),
                        "source_local_id": str(authored.get("local_id", "")),
                    }
                changed = True
            elif old_script == repaired:
                label_or_pointer = "script::recovered_npc"
                role = "VEGA_RECOVERED_FINITE_DIALOGUE"
                changed = True
            elif old_script == hisui:
                label_or_pointer = "script::hisui_general"
                role = "HISUI_AUTHORED_DIALOGUE"
                changed = True
            elif old_script == CUT_SCRIPT:
                role = "FIELD_CUT"
            elif old_script == ROCK_SMASH_SCRIPT:
                role = "FIELD_ROCK_SMASH"
            elif old_script in INVALID_OBJECT_SCRIPT_POINTERS \
                    and int(fields["kind"]) == 0 \
                    and 0 <= int(fields["x"]) < map_width \
                    and 0 <= int(fields["y"]) < map_height:
                label_or_pointer = "script::recovered_npc"
                role = "EXISTING_INVALID_RECOVERED_FINITE_DIALOGUE"
                changed = True
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

    waterway_tileset_label, waterway_tileset = _add_waterway_land_tileset(blob, stage51)
    map_patches.append({
        "kind": "waterway_land_tileset", "group": WATERWAY_GROUP,
        "map": WATERWAY_MAP, "site": int(waterway_tileset["site"]),
        "expected": int(waterway_tileset["expected"]),
        "label": waterway_tileset_label,
    })
    wild_header_root, wild_consumer_sites = _wild_header_consumer_sites(stage51)
    map_patches.extend({
        "kind": "wild_header_consumer_unified",
        "name": f"consumer_{index:02d}",
        "site": site,
        "expected": WILD_LEGACY_TABLE_ADDRESS,
        "replacement": wild_header_root,
    } for index, site in enumerate(wild_consumer_sites))
    map_patches.append({
        "kind": "trainer_party_count_after_adapter_chain",
        "site": TRAINER_PARTY_HOOK_OFFSET,
        "expected_hex": TRAINER_PARTY_HOOK_EXPECTED.hex(),
        "mode": "THUMB_BL",
        "target_offset": trainer_party_count_wrapper,
    })
    map_patches.append({
        "kind": "broken_battle_transition_router",
        "site": BATTLE_TRANSITION_START_HOOK_OFFSET,
        "expected_hex": BATTLE_TRANSITION_START_HOOK_EXPECTED.hex(),
        "mode": "THUMB_JUMP_LABEL",
        "label": "runtime::battle_transition_router",
    })
    map_patches.append({
        "kind": "continue_recap_disabled",
        "site": CONTINUE_RECAP_BRANCH_OFFSET,
        "expected_hex": CONTINUE_RECAP_BRANCH_EXPECTED.hex(),
        "replacement_hex": CONTINUE_RECAP_BRANCH_DISABLED.hex(),
    })
    for site, stock, name in CODEX_CHOICE_ROUTES:
        label = f"runtime::opponent_{name}_router"
        _add_opponent_choice_router(blob, label, stock)
        map_patches.append({
            "kind": "ordinary_double_choice_router", "name": name,
            "site": site, "expected": CODEX_OPPONENT_CONTROLLER,
            "label": label,
        })
    map_patches.extend((
        {
            "kind": "field_input_script_owner",
            "site": FIELD_INPUT_OWNER_HOOK_OFFSET,
            "expected_hex": FIELD_INPUT_OWNER_HOOK_EXPECTED.hex(),
            "mode": "THUMB_JUMP_LABEL",
            "label": "runtime::field_input_script_owner",
        },
        {
            "kind": "wild_encounter_moving_gate",
            "site": WILD_HOOK_OFFSET,
            "expected_hex": WILD_STAGE51_HOOK.hex(),
            "mode": "THUMB_JUMP_LABEL",
            "label": "runtime::moving_wild_encounter",
        },
        {
            "kind": "reward_restore_world_hook_disabled",
            "site": REWARD_READ_KEYS_RESTORE_CALL_OFFSET,
            "expected_hex": REWARD_READ_KEYS_RESTORE_CALL_EXPECTED.hex(),
            "replacement_hex": REWARD_READ_KEYS_RESTORE_CALL_DISABLED.hex(),
        },
        {
            "kind": "reward_restore_private_buffer",
            "site": REWARD_RESTORE_BUFFER_LITERAL_OFFSET,
            "expected": REWARD_RESTORE_SHARED_BUFFER,
            "replacement": REWARD_RESTORE_PRIVATE_BUFFER,
        },
    ))
    map_patches.append({
        "kind": "codex_explicit_read_keys_router",
        "name": "gMain.readKeys",
        "site": CODEX_READ_KEYS_POINTER_OFFSET,
        "expected": CODEX_READ_KEYS_TOP_ADAPTER,
        "label": "runtime::world_read_keys_router",
        "thumb": True,
    })
    map_patches.append({
        "kind": "trainer_sight_physical_flag_scanner",
        "name": "stock_script_flag_scanner",
        "site": TRAINER_SCRIPT_FLAG_SCANNER_OFFSET,
        "expected_hex": TRAINER_SCRIPT_FLAG_SCANNER_EXPECTED.hex(),
        "mode": "THUMB_JUMP_LABEL",
        "label": "runtime::trainer_script_flag_scanner",
    })
    payload = blob.finish(payload_offset)
    trainer_counts = Counter(row["disposition"] for row in trainer_ledger)
    required = {
        "SOURCE_DIRECT_OBJECT_OWNER": 469,
        "SOURCE_RECOVERED_FINITE_DIALOGUE": 24,
        "SOURCE_DIRECT_BG_OWNER": 375,
        "ITEM_BALL_STD_FIND_ITEM": 126,
        "HIDDEN_ITEM_STD_OBTAIN_ITEM": 124,
        "ITEM_BALL_EXISTING_STD_FIND_ITEM": 136,
        "FIELD_CUT": 47,
        "FIELD_ROCK_SMASH": 124,
        "HISUI_AUTHORED_DIALOGUE": 1,
        "VEGA_RECOVERED_FINITE_DIALOGUE": 85,
        "REWARD_ENCOUNTER_SCIENTIST_FINITE_WAIT": 1,
        "EXISTING_INVALID_RECOVERED_FINITE_DIALOGUE": 10,
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
            "enemy_party_count_after_adapter_chain": True,
            "new_battle_struct_untouched": True,
            "flag_storage": "V5_PHYSICAL_FLAG_VIA_STOCK_SIGHT_MAP_ADAPTER",
            "legacy_flag_migration": "NOT_REQUIRED",
        },
        "items": {
            "item_ball_count": 262, "kanto_item_ball_scope_count": 129,
            "hidden_item_count": 124,
            "item_ball_flow": "STD_FIND_ITEM", "hidden_item_flow": "STD_OBTAIN_ITEM",
            "bag_full_commit_guard": True,
        },
        "source_owner_restore": {
            "object_direct_count": counts["SOURCE_DIRECT_OBJECT_OWNER"],
            "object_dynamic_count": counts["SOURCE_RECOVERED_FINITE_DIALOGUE"],
            "bg_direct_count": counts["SOURCE_DIRECT_BG_OWNER"],
            "strategy": "EXACT_CLEAN_SOURCE_SCRIPT_ROOT_OR_FINITE_CONTACT_FALLBACK",
        },
        "wild": {
            "moving_gate_rebuilt": True, "minimum_step_patch_removed": True,
            "stock_hook_hex": WILD_STOCK_HOOK.hex(),
            "stage51_hook_hex": WILD_STAGE51_HOOK.hex(),
            "stock_cooldown_hex": COOLDOWN_STOCK.hex(),
            "header_root": wild_header_root,
            "legacy_consumer_address": WILD_LEGACY_TABLE_ADDRESS,
            "unified_consumer_count": len(wild_consumer_sites),
            "unified_consumer_sites": wild_consumer_sites,
            "waterway_511_land_tileset": waterway_tileset,
        },
        "runtime_backports": {
            "field_input_stock_encounter_gate": True,
            "field_input_script_owner": True,
            "ordinary_double_bank_routers": 3,
            "continue_recap_disabled": True,
            "trainer_quest_log_recording_preserved": True,
            "trainer_flags_save_backed_before_battle_teardown": True,
            "reward_restore_requires_idle_input": True,
            "reward_restore_private_buffer": REWARD_RESTORE_PRIVATE_BUFFER,
            "broken_transition_4_remapped_to_slice_8": True,
        },
        "stage50_payload_reachability_allowlist": [
            "script_heal", "script_mart", "wild_511_land_info"
        ],
    }
    return payload, plan, map_patches
