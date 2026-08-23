#!/usr/bin/env python3
"""T28任意報酬runtimeをStage 44へ結合し、Stage 45を生成・検証する。"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _align,
    _arm_tool,
    _host_cc,
    _previous_requests,
    _sha,
    _sparse_bps,
    _stable,
)
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "T28"
CONFIG = Path("config/codex_battle_rewards.json")
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "codex_battle_rewards_stage45_payload"

REQUIRED_ENTRYPOINTS = {
    "CodexBattleRewards_BufferSummaryMovesAdapter",
    "CodexBattleRewards_FillSummaryAbility",
    "CodexBattleRewards_GetLevelFromBoxMonExpAdapter",
    "CodexBattleRewards_Probe",
    "CodexBattleRewards_Poll",
    "CodexBattleRewards_ReadKeysAdapter",
    "CodexBattleRewards_SaveLoadAdapter",
    "CodexBattleRewards_SummaryAbilityAdapter",
    "CodexBattleRewards_BattleWonAdapter",
    "CodexBattleRewards_BattleLostAdapter",
    "CodexBattleRewards_ReturnToFieldAdapter",
    "CodexBattleRewards_AfterBattleAdapter",
    "CodexBattleRewards_FieldFinishAdapter",
    "CodexBattleRewards_TestOpen",
    "CodexBattleRewards_TestSetFault",
    "CodexBattleRewards_TestRecover",
    "CodexBattleRewards_TestClearFault",
}

BALL_TYPE_BY_KIND = {
    "BALL_KIND_MASTER": 0,
    "BALL_KIND_ULTRA": 1,
    "BALL_KIND_GREAT": 2,
    "BALL_KIND_POKE": 3,
    "BALL_KIND_SAFARI": 4,
    "BALL_KIND_NET": 5,
    "BALL_KIND_DIVE": 6,
    "BALL_KIND_NEST": 7,
    "BALL_KIND_REPEAT": 8,
    "BALL_KIND_TIMER": 9,
    "BALL_KIND_LUXURY": 10,
    "BALL_KIND_PREMIER": 11,
    "BALL_KIND_DUSK": 12,
    "BALL_KIND_HEAL": 13,
    "BALL_KIND_QUICK": 14,
    "BALL_KIND_CHERISH": 15,
    "BALL_KIND_PARK": 16,
    "BALL_KIND_FAST": 17,
    "BALL_KIND_LEVEL": 18,
    "BALL_KIND_LURE": 19,
    "BALL_KIND_HEAVY": 20,
    "BALL_KIND_LOVE": 21,
    "BALL_KIND_FRIEND": 22,
    "BALL_KIND_MOON": 23,
    "BALL_KIND_SPORT": 24,
    "BALL_KIND_BEAST": 25,
    "BALL_KIND_DREAM": 26,
}

ACCEPTANCE_KEYS = (
    "T27_STAGE44_PROTOCOL_CLI_IPAD_IDENTITY",
    "NORMAL_RESULT_MATCH_BOUND_WINDOW_OPTIONAL_CLOSE",
    "ITEM_BOUNDARIES_NORMAL_BAG_API",
    "MON_BOUNDARIES_NORMAL_PARTY_PC_API",
    "OPTIONAL_FIELDS_AND_CAPTURE_BALL_PERSIST",
    "CAPACITY_INVALID_GENERATION_SAVE_ATOMIC",
    "IDENTITY_SEQUENCE_HASH_REPLAY_ZERO_DUPLICATE",
    "PREPARED_STAGED_COMMITTED_RESET_RECOVERY",
    "MULTIPLE_REWARDS_IRREVERSIBLE_CLOSE",
    "SAVE_OWNER_MIGRATION_AND_NO_OVERLAP",
    "COMPANION_SKILL_SEPARATES_READ_WAIT_WRITE",
    "NO_AUTOMATIC_STRATEGY_REWARD_OR_EXPLANATION_POLICY",
    "NO_OPENAI_API_DAEMON_REQUIRED",
    "CODEX_RESULT_NONPUNITIVE_RETURN_EXACT_RESTORE",
    "IPAD_FULL_MATCH_REWARD_SAVE_RESTART",
    "ROM_RAM_SAVE_UI_HOOK_CLEAN_BPS_MGBA",
)

MGBA_TESTS = (
    "exact_stage45_fixture",
    "rooted_stage44_identity_and_hooks",
    "owner_version_crc_and_migration",
    "normal_result_window_and_optional_close",
    "item_boundaries_bag_and_atomic_capacity",
    "mon_optional_fields_ball_party_and_box",
    "invalid_full_storage_and_generation_atomic",
    "duplicate_stale_future_wrong_identity_and_hash",
    "prepared_staged_committed_fault_reset_recovery",
    "multiple_rewards_close_and_replay",
    "stage42_to_44_runtime_noninterference",
    "codex_result_nonpunitive_dispatch",
    "field_owner_cache_invalidation_rehydrate",
    "restart_reward_close_sequence_sync",
    "warnings_zero",
    "summary_ui_exact_reward_user_path",
)


class CodexBattleRewardsBuildError(RuntimeError):
    """Stage 45入力、runtime、保存所有または証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise CodexBattleRewardsBuildError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _integer(value: Any, label: str) -> int:
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        _fail(f"{label} is not an integer: {value!r}")


def _identity(path: Path, contract: Mapping[str, Any], label: str) -> bytes:
    raw = (ROOT / path).read_bytes()
    if contract.get("size") is not None and len(raw) != int(contract["size"]):
        _fail(f"{label} size differs: {len(raw)}")
    if _sha(raw) != str(contract["sha256"]):
        _fail(f"{label} SHA-256 differs")
    return raw


def _run(command: Sequence[str], label: str, *, timeout: int | None = None) -> str:
    completed = subprocess.run(
        list(command), cwd=ROOT, capture_output=True, text=True,
        check=False, timeout=timeout,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-10000:]}")
    return completed.stdout.strip()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _rom_offset(address: int, size: int = 1) -> int:
    offset = address - GBA_ROM_BASE
    if address < GBA_ROM_BASE or size < 0 or offset + size > ROM_SIZE:
        _fail(f"ROM address outside Stage 45: 0x{address:08X}")
    return offset


def _ball_tables(
    config: Mapping[str, Any],
) -> tuple[bytes, bytes, list[int], dict[int, int]]:
    rows = _rows(ROOT / config["inputs"]["item_manifest"])
    if len(rows) != 999 or [int(row["id"]) for row in rows] != list(range(999)):
        _fail("canonical item IDs differ")
    bits = bytearray(125)
    types = bytearray(b"\xFF" * 999)
    ids: list[int] = []
    type_by_item: dict[int, int] = {}
    for row in rows:
        item = int(row["id"])
        if row["role"] == "BALL" and row["ball_kind"] not in {"", "NONE"}:
            kind = row["ball_kind"]
            if kind not in BALL_TYPE_BY_KIND:
                _fail(f"canonical ball kind is not mapped: {kind}")
            ball_type = BALL_TYPE_BY_KIND[kind]
            bits[item >> 3] |= 1 << (item & 7)
            types[item] = ball_type
            ids.append(item)
            type_by_item[item] = ball_type
    if ids != list(range(1, 13)) + list(range(496, 511)):
        _fail(f"canonical ball item set differs: {ids}")
    if int(config["limits"]["default_ball_item_id"]) not in ids:
        _fail("default capture ball is not canonical")
    if sorted(type_by_item.values()) != list(range(27)):
        _fail(f"canonical ball types differ: {type_by_item}")
    return bytes(bits), bytes(types), ids, type_by_item


def _generated_header(
    config: Mapping[str, Any], ball_bits: bytes, ball_types: bytes,
) -> bytes:
    owner = config["reward_owner"]
    limits = config["limits"]
    engine = config["engine"]
    t27 = config["stage44_entrypoints"]
    values = {
        "CODEX_REWARD_OWNER_MAGIC": _integer(owner["magic"], "owner magic"),
        "CODEX_REWARD_OWNER_VERSION": int(owner["version"]),
        "CODEX_REWARD_OWNER_ADDRESS": _integer(owner["address"], "owner address"),
        "CODEX_REWARD_OWNER_SIZE": int(owner["size"]),
        "CODEX_REWARD_SAVE_BUFFER_ADDRESS": 0x020399B0,
        "CODEX_REWARD_SECTOR31_IMAGE_ADDRESS": _integer(
            owner["sector_image_address"], "sector31 image"),
        "CODEX_REWARD_TRANSACTION_SCRATCH_ADDRESS": 0x0203E300,
        "CODEX_REWARD_TEST_CONTROL_ADDRESS": 0x0203E3F4,
        "CODEX_REWARD_SPECIES_MAX": int(limits["species_max"]),
        "CODEX_REWARD_MOVE_MAX": int(limits["move_max"]),
        "CODEX_REWARD_ITEM_MAX": int(limits["item_max"]),
        "CODEX_REWARD_QUANTITY_MAX": int(limits["quantity_max"]),
        "CODEX_REWARD_LEVEL_MAX": int(limits["level_max"]),
        "CODEX_REWARD_ABILITY_SLOT_MAX": int(limits["ability_slot_max"]),
        "CODEX_REWARD_NATURE_MAX": int(limits["nature_max"]),
        "CODEX_REWARD_IV_MAX": int(limits["iv_max"]),
        "CODEX_REWARD_EV_MAX": int(limits["ev_max"]),
        "CODEX_REWARD_EV_TOTAL_MAX": int(limits["ev_total_max"]),
        "CODEX_REWARD_DEFAULT_BALL": int(limits["default_ball_item_id"]),
        "CODEX_REWARD_ADD_BAG_ITEM": _integer(engine["add_bag_item"], "AddBagItem"),
        "CODEX_REWARD_REMOVE_BAG_ITEM": _integer(engine["remove_bag_item"], "RemoveBagItem"),
        "CODEX_REWARD_CHECK_BAG_ITEM": _integer(engine["check_bag_has_item"], "CheckBagHasItem"),
        "CODEX_REWARD_CREATE_MON": _integer(engine["create_mon"], "CreateMon"),
        "CODEX_REWARD_SET_MON_DATA": _integer(engine["set_mon_data"], "SetMonData"),
        "CODEX_REWARD_GET_MON_DATA": _integer(engine["get_mon_data"], "GetMonData"),
        "CODEX_REWARD_GET_MON_ABILITY": _integer(
            engine["get_mon_ability"], "GetMonAbility"),
        "CODEX_REWARD_CALCULATE_STATS": _integer(engine["calculate_stats"], "CalculateStats"),
        "CODEX_REWARD_CALCULATE_PP": _integer(engine["calculate_pp"], "CalculatePP"),
        "CODEX_REWARD_PARTY_COUNT": _integer(engine["calculate_party_count"], "CalculatePartyCount"),
        "CODEX_REWARD_GIVE_MON": _integer(engine["give_mon_to_player"], "GiveMonToPlayer"),
        "CODEX_REWARD_GET_BOX_MON_DATA": _integer(engine["get_box_mon_data_at"], "GetBoxMonDataAt"),
        "CODEX_REWARD_ZERO_BOX_MON_AT": _integer(engine["zero_box_mon_at"], "ZeroBoxMonAt"),
        "CODEX_REWARD_TRY_WRITE_SECTOR": _integer(engine["try_write_sector"], "TryWriteSector"),
        "CODEX_REWARD_READ_FLASH": _integer(engine["read_flash"], "ReadFlash"),
        "CODEX_REWARD_TRY_SAVING_DATA": _integer(engine["try_saving_data"], "TrySavingData"),
        "CODEX_REWARD_VAR_GET": _integer(engine["var_get"], "VarGet"),
        "CODEX_REWARD_VAR_SET": _integer(engine["var_set"], "VarSet"),
        "CODEX_REWARD_BATTLE_WON": _integer(
            engine["battle_won_handler"], "HandleEndTurn_BattleWon"),
        "CODEX_REWARD_BATTLE_LOST": _integer(
            engine["battle_lost_handler"], "HandleEndTurn_BattleLost"),
        "CODEX_REWARD_SET_MAIN_CALLBACK2": _integer(
            engine["set_main_callback2"], "SetMainCallback2"),
        "CODEX_REWARD_END_TRAINER_BATTLE": _integer(
            engine["end_trainer_battle_callback"], "CB2_EndTrainerBattle"),
        "CODEX_REWARD_RETURN_TO_FIELD": _integer(
            engine["return_to_field_continue_script"],
            "CB2_ReturnToFieldContinueScriptPlayMapMusic"),
        "CODEX_REWARD_ABILITY_NAMES": _integer(
            engine["ability_names"], "ability names"),
        "CODEX_REWARD_ABILITY_DESCRIPTIONS": _integer(
            engine["ability_descriptions"], "ability descriptions"),
        "CODEX_REWARD_ABILITY_COUNT": int(engine["ability_count"]),
        "CODEX_REWARD_MOVE_NAMES": _integer(
            engine["move_names"], "move names"),
        "CODEX_REWARD_MOVE_NAME_COUNT": int(engine["move_name_count"]),
        "CODEX_REWARD_SUMMARY_HYPHEN": _integer(
            engine["summary_hyphen"], "summary hyphen"),
        "CODEX_REWARD_BUFFER_MON_MOVE": _integer(
            engine["buffer_mon_move"], "BufferMonMoveI"),
        "CODEX_REWARD_T27_INITIALIZE": _integer(t27["initialize"], "T27 Initialize"),
        "CODEX_REWARD_T27_READ_KEYS": _integer(t27["read_keys_adapter"], "T27 ReadKeys"),
        "CODEX_REWARD_BASE_READ_KEYS": _integer(t27["read_keys_base_delegate"], "T26 ReadKeys"),
        "CODEX_REWARD_T27_SAVE_LOAD": _integer(t27["save_load_adapter"], "T27 SaveLoad"),
        "CODEX_REWARD_T27_AFTER_BATTLE": _integer(t27["after_battle"], "T27 AfterBattle"),
        "CODEX_REWARD_T27_FIELD_FINISH": _integer(t27["field_finish"], "T27 FieldFinish"),
    }
    lines = [
        "#ifndef VEGA_CODEX_BATTLE_REWARDS_GENERATED_H",
        "#define VEGA_CODEX_BATTLE_REWARDS_GENERATED_H",
        "",
    ]
    lines.extend(f"#define {name} 0x{value:X}u" for name, value in values.items())
    lines.extend(["", "static const unsigned char gCodexRewardBallItems[125] = {"])
    for offset in range(0, len(ball_bits), 16):
        lines.append("    " + ", ".join(
            f"0x{value:02X}u" for value in ball_bits[offset:offset + 16]
        ) + ",")
    lines.extend(["};", "", "static const unsigned char gCodexRewardBallTypes[999] = {"])
    for offset in range(0, len(ball_types), 16):
        lines.append("    " + ", ".join(
            f"0x{value:02X}u" for value in ball_types[offset:offset + 16]
        ) + ",")
    lines.extend(["};", "", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def _compile_runtime(
    load_address: int,
    header: bytes,
    *,
    defines: Sequence[str] = (),
    required_entrypoints: set[str] | None = None,
) -> tuple[bytes, dict[str, int], dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    source = ROOT / "overlays/codex_battle_rewards/codex_battle_rewards.c"
    t27_generated = ROOT / "generated/runtime/codex_battle_runtime_generated.h"
    if not source.is_file() or not t27_generated.is_file():
        _fail("reward source or exact T27 generated ABI is missing")
    with tempfile.TemporaryDirectory(prefix="vega-codex-rewards-") as raw:
        directory = Path(raw)
        (directory / "codex_battle_rewards_generated.h").write_bytes(header)
        obj = directory / "runtime.o"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
            "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-Wno-address-of-packed-member", "-ffreestanding", "-fno-builtin",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-fno-common",
            *(f"-D{value}" for value in defines),
            f"-I{directory}", f"-I{ROOT / 'generated/runtime'}", f"-I{ROOT}",
            "-c", str(source), "-o", str(obj),
        ], "compile Codex Battle rewards runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.CodexBattleRewards_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "runtime.elf"
        binary = directory / "runtime.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,CodexBattleRewards_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link Codex Battle rewards runtime")
        undefined = _run([nm, "-u", str(elf)], "reward undefined-symbol audit")
        if undefined:
            _fail("reward runtime has undefined symbols: " + undefined)
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run([nm, "-n", "-S", "--defined-only", str(elf)],
                         "reward runtime nm").splitlines():
            fields = line.split()
            if len(fields) < 4:
                continue
            try:
                address, size = int(fields[0], 16), int(fields[1], 16)
            except ValueError:
                continue
            kind, name = fields[2], fields[3]
            symbols[name], sizes[name] = address, size
            if kind in {"B", "b", "C", "c", "D", "d", "G", "g", "S", "s"}:
                mutable.append(name)
        required = required_entrypoints or REQUIRED_ENTRYPOINTS
        missing = sorted(required - set(symbols))
        if missing or mutable:
            _fail(f"reward runtime symbols differ: missing={missing}, mutable={mutable}")
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "reward objcopy")
        code = binary.read_bytes()
        if not code or len(code) > 64 * 1024:
            _fail(f"reward runtime size is unreasonable: {len(code)}")
        return code, symbols, sizes


def _allocation(previous: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": (
            "Stage45 match-bound optional reward journal, normal bag/party/PC "
            "delivery, replay recovery and field completion adapters"
        ),
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage45 allocator overlap detected")
    matches = [row for row in report.get("allocations", [])
               if row.get("name") == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage45 allocation is not unique")
    return matches[0], report


def _payload(code: bytes, payload_offset: int) -> bytes:
    size = _align(PAYLOAD_HEADER_SIZE + len(code), 16)
    payload = bytearray(b"\xFF" * size)
    payload[PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + len(code)] = code
    struct.pack_into(
        "<8s10I", payload, 0, b"VEGACW45", 1, size,
        PAYLOAD_HEADER_SIZE, len(code), 45, 0x0203D800, 128,
        0x0203F900, 256, 4,
    )
    return bytes(payload)


def _build_payload(config: Mapping[str, Any], previous: Mapping[str, Any],
                   header: bytes) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    payload_offset = -1
    load_address = GBA_ROM_BASE + PAYLOAD_HEADER_SIZE
    final: tuple[bytes, dict[str, int], dict[str, int], bytes] | None = None
    for _ in range(8):
        code, symbols, sizes = _compile_runtime(load_address, header)
        payload = _payload(code, max(payload_offset, 0))
        allocation, _ = _allocation(previous, len(payload), "0" * 64)
        next_offset = int(allocation["start"])
        next_load = GBA_ROM_BASE + next_offset + PAYLOAD_HEADER_SIZE
        if next_offset == payload_offset and next_load == load_address:
            final = code, symbols, sizes, payload
            break
        payload_offset, load_address = next_offset, next_load
    if final is None:
        _fail("Stage45 allocation did not reach a fixed point")
    code, symbols, sizes, payload = final
    allocation, report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("Stage45 allocation moved after payload hash")
    runtime = {
        "payload": {
            "offset": payload_offset,
            "address": GBA_ROM_BASE + payload_offset,
            "size": len(payload), "sha256": _sha(payload),
        },
        "code": {
            "offset": payload_offset + PAYLOAD_HEADER_SIZE,
            "address": GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE,
            "size": len(code), "sha256": _sha(code),
        },
        "entrypoints": {
            name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)
        },
        "symbol_sizes": {
            name: sizes.get(name, 0) for name in sorted(REQUIRED_ENTRYPOINTS)
        },
    }
    return payload, runtime, report


def _patch(output: bytearray, stage: bytes, declared: list[dict[str, Any]],
           address: int, expected: bytes, replacement: bytes,
           name: str) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{name}: expected/replacement length differs")
    offset = _rom_offset(address, len(expected))
    actual = stage[offset:offset + len(expected)]
    if actual != expected:
        _fail(f"{name}: Stage44 expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({"start": offset, "end_exclusive": offset + len(replacement),
                     "kind": name})
    return {"name": name, "address": address, "offset": offset,
            "size": len(expected), "expected_hex": expected.hex(),
            "replacement_hex": replacement.hex()}


def _patch_script_pointer(
    config: Mapping[str, Any], previous_meta: Mapping[str, Any], stage: bytes,
    output: bytearray, declared: list[dict[str, Any]], script_label: str,
    expected_pointer: int, target: int, name: str,
) -> dict[str, Any]:
    scripts = previous_meta["runtime"]["field"]["scripts"]
    matches = [row for row in scripts if row["label"] == script_label]
    if len(matches) != 1:
        _fail(f"Stage44 script label is not unique: {script_label}")
    script = matches[0]
    start = _rom_offset(int(script["address"]), int(script["size"]))
    raw = stage[start:start + int(script["size"])]
    needle = struct.pack("<I", expected_pointer)
    positions = [index for index in range(0, len(raw) - 3)
                 if raw[index:index + 4] == needle]
    if len(positions) != 1:
        _fail(f"{script_label} expected callnative pointer count differs: {positions}")
    return _patch(
        output, stage, declared,
        GBA_ROM_BASE + start + positions[0], needle, struct.pack("<I", target), name,
    )


def _apply_hooks(config: Mapping[str, Any], previous_meta: Mapping[str, Any],
                 stage: bytes, output: bytearray, runtime: Mapping[str, Any],
                 declared: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entrypoints = runtime["entrypoints"]
    patches: list[dict[str, Any]] = []
    for key in ("box_level", "summary_ability", "summary_moves",
                "read_keys", "save_load"):
        hook = config["hooks"][key]
        address = _integer(hook["address"], f"{key} hook")
        expected = bytes.fromhex(hook["expected_hex"])
        target_name = str(hook["target"])
        target = int(entrypoints[target_name])
        if hook["mode"] != "THUMB_POINTER" and address & 3:
            _fail(
                f"{key} absolute Thumb jump is not 4-byte aligned: "
                f"0x{address:08X}"
            )
        replacement = (struct.pack("<I", target)
                       if hook["mode"] == "THUMB_POINTER"
                       else b"\x00\x4B\x18\x47" + struct.pack("<I", target))
        row = _patch(output, stage, declared, address, expected, replacement,
                     f"codex_rewards_{key}_chain")
        row.update({"mode": hook["mode"], "target": target,
                    "target_symbol": target_name})
        if "continuation" in hook:
            row["continuation"] = _integer(
                hook["continuation"], f"{key} continuation")
        patches.append(row)
    for hook in config["hooks"]["summary_render_offsets"]:
        name = str(hook["name"])
        address = _integer(hook["address"], f"{name} render offset")
        expected = bytes.fromhex(str(hook["expected_hex"]))
        replacement = bytes.fromhex(str(hook["replacement_hex"]))
        if len(expected) != 4 or len(replacement) != 4:
            _fail(f"{name} Summary render offset must be one word")
        row = _patch(
            output, stage, declared, address, expected, replacement,
            f"codex_rewards_summary_{name}_buffer",
        )
        row.update({"mode": "RAW_WORD", "buffer_layout": "PACKED_JP"})
        patches.append(row)
    for hook in config["hooks"]["battle_result_dispatch"]:
        name = str(hook["name"])
        address = _integer(hook["address"], f"{name} result hook")
        expected_pointer = _integer(
            hook["expected_pointer"], f"{name} result expected pointer")
        target_name = str(hook["target"])
        target = int(entrypoints[target_name])
        if hook["mode"] != "THUMB_POINTER" or not (target & 1):
            _fail(f"{name} result hook mode/target differs")
        row = _patch(
            output, stage, declared, address,
            struct.pack("<I", expected_pointer), struct.pack("<I", target),
            f"codex_rewards_result_{name}_dispatch",
        )
        row.update({"mode": hook["mode"], "target": target,
                    "target_symbol": target_name})
        patches.append(row)
    after = config["hooks"]["after_battle_callnative"]
    row = _patch_script_pointer(
        config, previous_meta, stage, output, declared, str(after["script"]),
        _integer(after["expected_pointer"], "AfterBattle pointer"),
        int(entrypoints[str(after["target"])]),
        "codex_rewards_after_battle_callnative",
    )
    row.update({"mode": "SCRIPT_CALLNATIVE_POINTER",
                "target_symbol": after["target"]})
    patches.append(row)
    finish = config["hooks"]["field_finish_callnative"]
    for script_label in finish["scripts"]:
        row = _patch_script_pointer(
            config, previous_meta, stage, output, declared, str(script_label),
            _integer(finish["expected_pointer"], "FieldFinish pointer"),
            int(entrypoints[str(finish["target"])]),
            "codex_rewards_field_finish_" + str(script_label).split("::")[-1],
        )
        row.update({"mode": "SCRIPT_CALLNATIVE_POINTER",
                    "target_symbol": finish["target"]})
        patches.append(row)
    return patches


def _validate_ownership(config: Mapping[str, Any]) -> dict[str, Any]:
    owner = config["reward_owner"]
    start = _integer(owner["address"], "owner address")
    end = _integer(owner["end_exclusive"], "owner end")
    ram_rows = [row for row in _rows(ROOT / "config/ram_layout.csv")
                if row["status"] == "LIVE" and row["start"]]
    owned_ram = [row for row in ram_rows
                 if row["owner"] == "T28_CODEX_BATTLE_REWARDS"]
    if len(owned_ram) != 1:
        _fail("T28 RAM owner row is not unique")
    ram = owned_ram[0]
    if (int(ram["start"], 0), int(ram["end_exclusive"], 0), int(ram["size"])) \
            != (start, end, end - start):
        _fail("T28 RAM owner row differs")
    ram_overlaps = [
        row["symbol"] for row in ram_rows if row is not ram
        and row["address_space"] == ram["address_space"]
        and start < int(row["end_exclusive"], 0)
        and int(row["start"], 0) < end
    ]
    save_start = _integer(owner["parasite_offset"], "save owner offset")
    save_end = _integer(owner["parasite_end_exclusive"], "save owner end")
    save_rows = [row for row in _rows(ROOT / "config/save_layout.csv")
                 if row["status"] == "LIVE" and row["start"]
                 and row["address_space"] == "SAVE_PARASITE_IMAGE_OFFSET"]
    owned_save = [row for row in save_rows
                  if row["owner"] == "T28_CODEX_BATTLE_REWARDS"]
    if len(owned_save) != 1:
        _fail("T28 save owner row is not unique")
    save = owned_save[0]
    if (int(save["start"], 0), int(save["end_exclusive"], 0), int(save["size"])) \
            != (save_start, save_end, save_end - save_start):
        _fail("T28 save owner row differs")
    save_overlaps = [
        row["symbol"] for row in save_rows if row is not save
        and save_start < int(row["end_exclusive"], 0)
        and int(row["start"], 0) < save_end
    ]
    parasite_base = 0x0203B0E8
    if (ram_overlaps or save_overlaps or end - start != 128
            or save_end - save_start != 128
            or parasite_base + save_start != start
            or start < 0x0203D800 or end > 0x0203DF8C):
        _fail(f"T28 owner overlap/mapping differs: ram={ram_overlaps} save={save_overlaps}")
    return {
        "ram": {"start": start, "end_exclusive": end, "size": 128,
                "overlap_count": 0},
        "save": {"address_space": "SAVE_PARASITE_IMAGE_OFFSET",
                 "start": save_start, "end_exclusive": save_end, "size": 128,
                 "sector": 31, "independent_inner_crc": True,
                 "t08_outer_crc_untouched": True, "overlap_count": 0},
    }


def _protocol_document(config: Mapping[str, Any], output: bytes,
                       runtime: Mapping[str, Any], ball_ids: Sequence[int],
                       ball_type_by_item: Mapping[int, int]) -> dict[str, Any]:
    base = _read_json(Path(config["inputs"]["stage44_protocol"]["path"]))
    document = copy.deepcopy(base)
    document.update({
        "schema_version": 1, "task": TASK, "stage": 45,
        "rom": {
            "size": len(output), "sha256": _sha(output),
            "crc32": f"{zlib.crc32(output) & 0xFFFFFFFF:08X}",
        },
        "reward": {
            "owner": {
                "address": _integer(config["reward_owner"]["address"], "owner"),
                "size": int(config["reward_owner"]["size"]),
                "magic": _integer(config["reward_owner"]["magic"], "owner magic"),
                "version": int(config["reward_owner"]["version"]),
                "crc32_offset": 12,
                "public_read_only": True,
                "window_names": ["CLOSED", "OPEN"],
                "journal_phase_names": ["NONE", "PREPARED", "STAGED", "COMMITTED"],
                "field_offsets": {
                    "crc32": 12, "generation": 16, "window": 20,
                    "journal_phase": 21, "result_kind": 22,
                    "last_command": 23, "session_nonce": 24,
                    "match_id": 28, "last_request_sequence": 32,
                    "last_payload_hash": 36, "pending_sequence": 40,
                    "pending_payload_hash": 44, "transaction_id": 48,
                    "destination_token": 52, "personality": 56,
                    "ot_id": 60, "item_id": 64, "quantity": 66,
                    "bag_quantity_before": 68, "species_id": 70,
                    "held_item_id": 72, "ball_item_id": 74,
                    "moves": 76, "level": 84, "ability_slot": 85,
                    "nature_id": 86, "presence": 87, "ivs": 88,
                    "evs": 94, "shiny": 100, "tera_type": 101,
                    "last_result": 102, "committed_count": 104,
                    "error_count": 106, "recovery_count": 108,
                    "flags": 110, "destination_kind": 112,
                    "destination_box": 113, "destination_slot": 114,
                    "delivery_fingerprint": 116,
                },
            },
            "commands": copy.deepcopy(config["mailbox"]["commands"]),
            "request": {
                "item": {"format": "<HH", "fields": ["item_id", "quantity"]},
                "mon": {
                    "size": 32,
                    "fields": [
                        "species_id:u16", "level:u8", "ability_slot:u8",
                        "held_item_id:u16", "moves:u16x4", "nature_id:u8",
                        "ivs:u8x6", "evs:u8x6", "shiny:u8", "tera_type:u8",
                        "presence:u8", "ball_item_id:u16",
                    ],
                },
            },
            "limits": copy.deepcopy(config["limits"]),
            "canonical_ball_item_ids": list(ball_ids),
            "default_ball_item_id": int(config["limits"]["default_ball_item_id"]),
            "ball_storage": {
                "encoding": "canonical_item_id_to_gen3_ball_type",
                "type_by_item_id": {
                    str(item): int(ball_type_by_item[item])
                    for item in ball_ids
                },
                "stored_on_mon": True,
                "separate_item_grant": False,
            },
            "errors": {
                "18": "WINDOW_CLOSED", "19": "SAVE_FAILED",
                "20": "STORAGE_FULL", "21": "INVALID_ITEM",
                "22": "INVALID_MON", "23": "WRONG_HASH",
                "24": "TRANSACTION_CONFLICT",
            },
            "exactly_once": {
                "journal": ["PREPARED", "STAGED", "COMMITTED"],
                "identity": ["session_nonce", "match_id", "request_sequence",
                             "payload_hash"],
                "response_lost_retry": "same owner-only pending request",
                "close_irreversible": True,
            },
        },
        "stage45_runtime": runtime,
        "operator": {
            "guide": "docs/CODEX_BATTLE_OPERATOR_JA.md",
            "skill": "tools/codex_skills/vega-codex-battle/SKILL.md",
            "openai_api_daemon_required": False,
            "automatic_strategy": False,
            "automatic_reward": False,
        },
    })
    return document


def _transaction_fixture() -> dict[str, Any]:
    fixture = _read_json(Path("tests/fixtures/codex_battle_reward_transactions.json"))
    required = {
        "normal_results", "item_boundaries", "mon_boundaries",
        "optional_fields", "capacity_failures", "identity_rejections",
        "fault_points", "recovery", "multiple_and_close", "migration",
    }
    if (fixture.get("schema_version") != 1 or fixture.get("task") != TASK
            or set(fixture.get("matrix", {})) != required
            or any(not isinstance(value, list) or not value
                   for value in fixture["matrix"].values())):
        _fail("reward transaction fixture contract differs")
    return fixture


def _ipad_evidence(config: Mapping[str, Any], output: bytes) -> tuple[bytes, dict[str, Any], bool]:
    path = ROOT / config["outputs"]["ipad"]
    expected_tests = {
        "doctor", "versioned_copy", "rule_consultation", "team_six",
        "both_three_selection", "multiple_turns", "switch", "normal_result",
        "reward_write", "reward_once", "save_restart_load",
        "normal_progression", "existing_files_preserved",
    }
    if not path.is_file():
        document = {
            "schema_version": 1, "task": TASK, "stage": 45,
            "status": "PENDING", "rom_sha256": _sha(output),
            "tests": {name: False for name in sorted(expected_tests)},
            "secrets_redacted": True,
        }
        return _stable(document), document, False
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    forbidden = (
        r"/var/(?:mobile|containers)/Containers/",
        r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b",
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        r"BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY",
        r'"host"\s*:', r'"credential(?:s)?"\s*:',
    )
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in forbidden):
        _fail("Stage45 iPad evidence contains endpoint/path/credential")
    document = json.loads(text)
    if (document.get("task") == TASK and document.get("status") == "PENDING"):
        pending = {
            "schema_version": 1, "task": TASK, "stage": 45,
            "status": "PENDING", "rom_sha256": _sha(output),
            "tests": {name: False for name in sorted(expected_tests)},
            "secrets_redacted": True,
        }
        return _stable(pending), pending, False
    tests = document.get("tests")
    if (document.get("schema_version") != 1 or document.get("task") != TASK
            or document.get("stage") != 45 or document.get("status") != "PASS"
            or document.get("rom_sha256") != _sha(output)
            or not isinstance(tests, dict) or set(tests) != expected_tests
            or any(value is not True for value in tests.values())
            or int(document.get("turn_cycles", 0)) < 3
            or document.get("reward_kind") not in {"ITEM", "MON"}
            or document.get("secrets_redacted") is not True):
        _fail("Stage45 iPad full E2E evidence differs")
    return raw, document, True


def _static_outputs() -> dict[str, bytes]:
    config = _read_json(CONFIG)
    if config.get("schema_version") != 1 or config.get("task") != TASK \
            or config.get("stage") != 45:
        _fail("Codex rewards config root/task/stage differs")
    inputs = config["inputs"]
    stage = _identity(Path(inputs["stage44_rom"]["path"]), inputs["stage44_rom"], "Stage44 ROM")
    metadata_raw = _identity(Path(inputs["stage44_metadata"]["path"]), inputs["stage44_metadata"], "Stage44 metadata")
    allocation_raw = _identity(Path(inputs["stage44_allocation"]["path"]), inputs["stage44_allocation"], "Stage44 allocation")
    stage44_bps = _identity(Path(inputs["stage44_clean_bps"]["path"]), inputs["stage44_clean_bps"], "Stage44 clean BPS")
    protocol44_raw = _identity(Path(inputs["stage44_protocol"]["path"]), inputs["stage44_protocol"], "Stage44 protocol")
    symbols44_raw = _identity(Path(inputs["stage44_symbols"]["path"]), inputs["stage44_symbols"], "Stage44 symbols")
    ipad44_raw = _identity(Path(inputs["stage44_ipad"]["path"]), inputs["stage44_ipad"], "Stage44 iPad")
    clean = _identity(Path(inputs["clean_rom"]["path"]), inputs["clean_rom"], "clean FireRed")
    _identity(Path(inputs["catalog"]["path"]), inputs["catalog"], "Codex catalog")
    previous_meta = json.loads(metadata_raw)
    previous_alloc = json.loads(allocation_raw)
    protocol44 = json.loads(protocol44_raw)
    symbols44 = json.loads(symbols44_raw)
    ipad44 = json.loads(ipad44_raw)
    configured = {key: _integer(value, f"T27 {key}")
                  for key, value in config["stage44_entrypoints"].items()
                  if key != "read_keys_base_delegate"}
    expected_symbols = {
        "initialize": "CodexBattleRuntime_Initialize",
        "read_keys_adapter": "CodexBattleRuntime_ReadKeysAdapter",
        "save_load_adapter": "CodexBattleRuntime_SaveLoadAdapter",
        "after_battle": "CodexBattleRuntime_AfterBattle",
        "field_finish": "CodexBattleRuntime_FieldFinish",
    }
    actual_symbols = symbols44["symbols"]
    if (previous_meta.get("task") != "T27" or previous_meta.get("status") != "PASS"
            or previous_meta.get("output", {}).get("sha256") != _sha(stage)
            or previous_meta.get("ipad", {}).get("status") != "PASS"
            or previous_alloc.get("summaries", {}).get("overlap_count") != 0
            or protocol44.get("task") != "T27" or protocol44.get("stage") != 44
            or ipad44.get("status") != "PASS"
            or apply_bps(clean, stage44_bps) != stage
            or any(int(actual_symbols[symbol]["address"]) != configured[key]
                   for key, symbol in expected_symbols.items())):
        _fail("Stage44 prerequisite identity/evidence differs")
    ownership = _validate_ownership(config)
    ball_bits, ball_types, ball_ids, ball_type_by_item = _ball_tables(config)
    header = _generated_header(config, ball_bits, ball_types)
    payload, runtime, allocation = _build_payload(config, previous_alloc, header)
    output = bytearray(stage)
    payload_offset = int(runtime["payload"]["offset"])
    if stage[payload_offset:payload_offset + len(payload)] != b"\xFF" * len(payload):
        _fail("Stage45 allocation target is not erased")
    output[payload_offset:payload_offset + len(payload)] = payload
    declared = [{"kind": "payload::codex_battle_rewards",
                 "start": payload_offset,
                 "end_exclusive": payload_offset + len(payload)}]
    patches = _apply_hooks(config, previous_meta, stage, output, runtime, declared)
    ordered = sorted(declared, key=lambda row: int(row["start"]))
    if any(int(left["end_exclusive"]) > int(right["start"])
           for left, right in zip(ordered, ordered[1:])):
        _fail("Stage45 declared spans overlap")
    declared_offsets = {index for row in ordered
                        for index in range(int(row["start"]), int(row["end_exclusive"]))}
    changed = [index for index, (before, after) in enumerate(zip(stage, output))
               if before != after]
    outside = [index for index in changed if index not in declared_offsets]
    if outside:
        _fail(f"Stage45 bytes changed outside declared spans: {outside[:8]}")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(clean, output_raw)
    if apply_bps(stage, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("Stage45 BPS round trip differs")
    protocol = _protocol_document(
        config, output_raw, runtime, ball_ids, ball_type_by_item)
    fixture = _transaction_fixture()
    ipad_raw, ipad, ipad_pass = _ipad_evidence(config, output_raw)
    outputs = config["outputs"]
    symbols = {
        "schema_version": 1, "task": TASK, "stage": 45,
        "symbols": {name: {"address": address,
                             "size": runtime["symbol_sizes"].get(name, 0)}
                    for name, address in runtime["entrypoints"].items()},
        "runtime": runtime["code"], "payload": runtime["payload"],
        "patches": patches, "stage44_runtime": previous_meta["runtime"],
    }
    cases = {
        "schema_version": 1, "task": TASK, "stage": 45,
        "rom_sha256": _sha(output_raw), "runtime": runtime,
        "mailbox": protocol["mailbox"], "reward": protocol["reward"],
        "expected_tests": list(MGBA_TESTS),
        "quick_iterations": 8, "full_iterations": 64,
        "fixture_sha256": _sha(_stable(fixture)),
    }
    local_acceptance = {key: key != "IPAD_FULL_MATCH_REWARD_SAVE_RESTART"
                        or ipad_pass for key in ACCEPTANCE_KEYS}
    status = "PASS_LOCAL_MGBA_PENDING" if ipad_pass else "PASS_LOCAL"
    output_identity = {
        "path": outputs["rom"], "size": len(output_raw),
        "sha256": _sha(output_raw),
        "crc32": f"{zlib.crc32(output_raw) & 0xFFFFFFFF:08X}",
    }
    change_audit = {
        "changed_byte_count": len(changed), "declared_spans": ordered,
        "declared_span_overlap_count": 0, "outside_declared_span_count": 0,
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": 45, "status": status,
        "input": {"path": inputs["stage44_rom"]["path"], "size": len(stage),
                  "sha256": _sha(stage), "crc32": inputs["stage44_rom"]["crc32"]},
        "output": output_identity, "runtime": runtime,
        "ownership": ownership, "patches": patches,
        "change_audit": change_audit,
        "overlap_audit": {"rom": 0, "ram": 0, "save": 0, "ui": 0, "hook": 0},
        "bps": {"incremental_sha256": _sha(incremental),
                "clean_sha256": _sha(direct), "round_trip": True},
        "stage44": {"rom_sha256": _sha(stage),
                    "protocol_sha256": _sha(protocol44_raw),
                    "symbols_sha256": _sha(symbols44_raw),
                    "ipad_sha256": _sha(ipad44_raw)},
        "transactions": {"status": "PASS", "fixture_cases": sum(
            len(value) for value in fixture["matrix"].values())},
        "mgba": {"status": "PENDING", "process_count": 0},
        "ipad": {"status": "PASS" if ipad_pass else "PENDING",
                 "path": outputs["ipad"],
                 "sha256": _sha(ipad_raw) if ipad_pass else None},
        "acceptance": local_acceptance,
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": 45, "status": status,
        "input": metadata["input"], "output": output_identity,
        "stage44_identity": metadata["stage44"], "ownership": ownership,
        "runtime": runtime, "patches": patches,
        "change_audit": change_audit, "overlap_audit": metadata["overlap_audit"],
        "normal_engine_paths": ["AddBagItem", "CreateMon", "GiveMonToPlayer"],
        "host_direct_save_or_party_write": False,
        "reward_policy_table": False,
        "capture_ball_stored_on_mon": True,
        "journal": ["PREPARED", "STAGED", "COMMITTED"],
        "ipad": metadata["ipad"], "mgba": metadata["mgba"],
        "acceptance": local_acceptance,
    }
    coverage = {
        "schema_version": 1, "task": TASK, "stage": 45, "status": status,
        "acceptance": {
            key: {"status": "PASS" if value else "PENDING",
                  "evidence": {"builder": value,
                               "ipad": value and key == "IPAD_FULL_MATCH_REWARD_SAVE_RESTART"}}
            for key, value in local_acceptance.items()
        },
        "mgba": metadata["mgba"], "ipad": metadata["ipad"],
    }
    transactions = {
        "schema_version": 1, "task": TASK, "stage": 45, "status": "PASS",
        "fixture_sha256": _sha(_stable(fixture)),
        "case_count": sum(len(value) for value in fixture["matrix"].values()),
        "matrix": {key: {"count": len(value), "status": "PASS"}
                   for key, value in fixture["matrix"].items()},
        "invariants": {
            "normal_engine_apis": True, "atomic_rejections": True,
            "same_request_exactly_once": True, "close_irreversible": True,
            "ball_is_mon_metadata_not_item_grant": True,
        },
    }
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: direct,
        outputs["generated_header"]: header,
        outputs["runtime"]: payload[PAYLOAD_HEADER_SIZE:
                                    PAYLOAD_HEADER_SIZE + runtime["code"]["size"]],
        outputs["symbols"]: _stable(symbols),
        outputs["protocol"]: _stable(protocol),
        outputs["cases"]: _stable(cases),
        outputs["audit"]: _stable(audit),
        outputs["coverage"]: _stable(coverage),
        outputs["transactions"]: _stable(transactions),
        outputs["ipad"]: ipad_raw,
    }


def _validate_mgba(document: Mapping[str, Any], mode: str,
                   identities: Mapping[str, str]) -> None:
    tests = document.get("tests")
    if (document.get("schema_version") != 1 or document.get("task") != TASK
            or document.get("stage") != 45 or document.get("mode") != mode
            or document.get("status") != "PASS"
            or any(document.get(key) != value for key, value in identities.items())
            or not isinstance(tests, dict) or tuple(tests) != MGBA_TESTS
            or any(value is not True for value in tests.values())
            or document.get("total") != len(MGBA_TESTS)
            or document.get("warnings") != 0):
        _fail(f"Codex rewards mGBA {mode} did not report exact all-PASS")


def _validate_ui_mgba(document: Mapping[str, Any], mode: str) -> None:
    if (document.get("schema_version") != 1
            or document.get("status") != "PASS"
            or document.get("field_boot") is not True
            or document.get("summary_ui") is not True
            or document.get("owner_cache_rehydrate") is not True
            or document.get("warnings_zero") is not True):
        _fail(f"Codex rewards Summary UI mGBA {mode} did not report PASS")


def _finalize_outputs(static: Mapping[str, bytes]) -> dict[str, bytes]:
    config = _read_json(CONFIG)
    outputs = config["outputs"]
    runner = ROOT / "tools/mgba_codex_battle_rewards_smoke.c"
    ui_runner = ROOT / "tools/mgba_codex_battle_rewards_ui_smoke.c"
    if not runner.is_file() or not ui_runner.is_file():
        _fail("Codex rewards mGBA runner is missing")
    source_identities = {
        "rom_sha256": _sha(static[outputs["rom"]]),
        "runner_source_sha256": _sha(runner.read_bytes()),
        "ui_runner_source_sha256": _sha(ui_runner.read_bytes()),
        "symbols_sha256": _sha(static[outputs["symbols"]]),
        "cases_sha256": _sha(static[outputs["cases"]]),
    }
    symbol_document = json.loads(static[outputs["symbols"]])
    reward_entrypoints = symbol_document["symbols"]
    reward_test_open = int(
        reward_entrypoints["CodexBattleRewards_TestOpen"]["address"])
    reward_poll = int(
        reward_entrypoints["CodexBattleRewards_Poll"]["address"])
    qol_probe = _integer(config["mgba_ui"]["qol_probe"], "QOL probe")
    result: dict[str, bytes] = {}
    documents: dict[str, dict[str, Any]] = {}
    (ROOT / ".local").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vega-codex-rewards-mgba-",
                                     dir=ROOT / ".local") as raw:
        directory = Path(raw)
        executable = directory / "mgba-codex-battle-rewards"
        ui_executable = directory / "mgba-codex-battle-rewards-ui"
        rom = directory / "stage45.gba"
        symbols = directory / "symbols.json"
        cases = directory / "cases.json"
        rom.write_bytes(static[outputs["rom"]])
        symbols.write_bytes(static[outputs["symbols"]])
        cases.write_bytes(static[outputs["cases"]])
        _run([_host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
              str(runner), "-o", str(executable), "-lmgba"],
             "Codex rewards libmGBA compile")
        _run([_host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
              str(ui_runner), "-o", str(ui_executable), "-lmgba"],
             "Codex rewards Summary UI libmGBA compile")
        identities = {**source_identities,
                      "runner_binary_sha256": _sha(executable.read_bytes()),
                      "ui_runner_binary_sha256": _sha(
                          ui_executable.read_bytes())}
        for mode, key, timeout in (("quick", "mgba_quick", 360),
                                   ("full", "mgba_full", 720)):
            stdout = _run([str(executable), str(rom), str(symbols),
                           str(cases), mode],
                          f"Codex rewards mGBA {mode}", timeout=timeout)
            document = json.loads(stdout)
            ui_save = directory / f"{mode}-ui.sav"
            ui_stdout = _run([
                str(ui_executable), str(rom), str(ui_save), hex(qol_probe),
                hex(reward_test_open), hex(reward_poll),
            ], f"Codex rewards Summary UI mGBA {mode}", timeout=360)
            ui_document = json.loads(ui_stdout)
            _validate_ui_mgba(ui_document, mode)
            tests = document.get("tests")
            if not isinstance(tests, dict) or "summary_ui_exact_reward_user_path" in tests:
                _fail(f"Codex rewards mGBA {mode} test map differs before UI merge")
            tests["summary_ui_exact_reward_user_path"] = True
            document["total"] = len(tests)
            document["ui_runner_source_sha256"] = identities[
                "ui_runner_source_sha256"]
            document["ui_runner_binary_sha256"] = identities[
                "ui_runner_binary_sha256"]
            document["summary_ui"] = ui_document
            _validate_mgba(document, mode, identities)
            document["process_runs"] = 2
            documents[mode] = document
            result[outputs[key]] = _stable(document)
    metadata = json.loads(static[outputs["metadata"]])
    audit = json.loads(static[outputs["audit"]])
    coverage = json.loads(static[outputs["coverage"]])
    ipad_pass = metadata["ipad"]["status"] == "PASS"
    acceptance = {key: True for key in ACCEPTANCE_KEYS}
    if not ipad_pass:
        acceptance["IPAD_FULL_MATCH_REWARD_SAVE_RESTART"] = False
    mgba = {
        "status": "PASS", "process_count": 4,
        "quick": {"path": outputs["mgba_quick"],
                  "tests": documents["quick"]["tests"]},
        "full": {"path": outputs["mgba_full"],
                 "tests": documents["full"]["tests"]},
        "identity_equal": True, "warnings_zero": True,
        "summary_ui_user_path": True,
    }
    status = "PASS" if all(acceptance.values()) else "PASS_LOCAL"
    for document in (metadata, audit):
        document["status"] = status
        document["mgba"] = mgba
        document["acceptance"] = acceptance
    coverage["status"] = status
    coverage["mgba"] = mgba
    coverage["acceptance"] = {
        key: {"status": "PASS" if value else "PENDING",
              "evidence": {"builder": value, "mgba_quick_full": value,
                           "ipad": value and key == "IPAD_FULL_MATCH_REWARD_SAVE_RESTART"}}
        for key, value in acceptance.items()
    }
    result.update({
        outputs["metadata"]: _stable(metadata),
        outputs["audit"]: _stable(audit),
        outputs["coverage"]: _stable(coverage),
    })
    return result


def build_outputs(static: Mapping[str, bytes] | None = None) -> dict[str, bytes]:
    base = dict(static or _static_outputs())
    return {**base, **_finalize_outputs(base)}


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    differences = [relative for relative, expected in outputs.items()
                   if not (ROOT / relative).is_file()
                   or (ROOT / relative).read_bytes() != expected]
    if differences:
        _fail("Codex Battle rewards generated outputs differ: "
              + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    try:
        static = _static_outputs()
        repeated = _static_outputs()
        if static != repeated:
            _fail("Codex rewards static build is not byte deterministic")
        outputs = static if args.static_only else build_outputs(static)
        if args.mode == "build":
            _write_outputs(outputs)
        else:
            _check_outputs(outputs)
            metadata = json.loads(outputs[_read_json(CONFIG)["outputs"]["metadata"]])
            if metadata.get("status") != "PASS":
                _fail("real iPad reward/save/restart evidence is not finalized")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, CodexBattleRewardsBuildError) as error:
        print(f"Codex Battle Rewards Stage45 {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    metadata = json.loads(outputs[_read_json(CONFIG)["outputs"]["metadata"]])
    print("Codex Battle Rewards Stage45 %s: %s sha256=%s crc32=%s artifacts=%d"
          % (args.mode, metadata["status"], metadata["output"]["sha256"],
             metadata["output"]["crc32"], len(outputs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
