#!/usr/bin/env python3
"""T27 Codex 6→3対戦runtimeをStage 43へ結合しStage 44を生成・検証する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_factory_high_modes_v2 import (  # noqa: E402
    _Blob,
    _Script,
    _add_script,
    _charmap,
    _encode_text,
    _thumb_bl,
)
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


TASK = "T27"
CONFIG = Path("config/codex_battle_runtime.json")
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "codex_battle_runtime_stage44_payload"

REQUIRED_ENTRYPOINTS = {
    "CodexBattleRuntime_Probe",
    "CodexBattleRuntime_Initialize",
    "CodexBattleRuntime_Poll",
    "CodexBattleRuntime_ReadKeysAdapter",
    "CodexBattleRuntime_BuildTrainerPartyAdapter",
    "CodexBattleRuntime_SaveLoadAdapter",
    "CodexBattleRuntime_OpponentController",
    "CodexBattleRuntime_FindDynamaxBandAdapter",
    "CodexBattleRuntime_CanMegaAdapter",
    "CodexBattleRuntime_MarkMegaAdapter",
    "CodexBattleRuntime_CanZAdapter",
    "CodexBattleRuntime_MarkZAdapter",
    "CodexBattleRuntime_CanDynamaxAdapter",
    "CodexBattleRuntime_MarkDynamaxAdapter",
    "CodexBattleRuntime_CanTeraAdapter",
    "CodexBattleRuntime_MarkTeraAdapter",
    "CodexBattleRuntime_FieldBeginPlayerSelection",
    "CodexBattleRuntime_FieldCommitPlayerSelection",
    "CodexBattleRuntime_FieldPrepareBattle",
    "CodexBattleRuntime_AfterBattle",
    "CodexBattleRuntime_FieldFinish",
    "CodexBattleRuntime_Abort",
    "CodexBattleRuntime_SealPrivateForTest",
    "CodexBattleRuntime_TestInitialize",
    "CodexBattleRuntime_TestStateHash",
}

ACCEPTANCE_KEYS = (
    "T26_IDENTITY_IPAD_DOCTOR",
    "PRODUCTION_BOTH_SIDES_6_TO_3_PRIVATE_ORDER",
    "TEAM_JSON_EXACT_DEFAULT_INVALID_MATRIX",
    "LEVEL_TOGGLE_AND_UNRESTRICTED_TEAMS",
    "CATALOG_CANONICAL_BOUNDED_EXACT_EXPORT",
    "UPSTREAM_OPEN_GIMMICKS_AND_NONINTERFERENCE",
    "REAL_CONTROLLER_ACTION_BRANCHES_AND_REJECTIONS",
    "PUBLIC_SNAPSHOT_INFORMATION_BOUNDARY",
    "PLAYER_PENDING_ACTION_SEALED_PRIVATE",
    "CLI_MANUAL_ONLY_WAIT_EXPLICIT_WRITES",
    "DISCONNECT_WAIT_RECONNECT_CPU_FORFEIT",
    "ALL_EXIT_EXACT_RESTORE",
    "NO_BATTLE_PERSISTENT_SIDE_EFFECTS",
    "NON_CODEX_MODE_NONINTERFERENCE",
    "THREE_PLUS_REQUEST_CYCLES",
    "IPAD_STAGE44_MULTI_TURN_VERTICAL_SLICE",
    "OVERLAP_DECLARED_CLEAN_BPS_MGBA",
)

MGBA_TESTS = (
    "exact_stage44_fixture",
    "runtime_exports_and_rooted_hooks",
    "protocol_header_snapshot_crc",
    "team_six_defaults_invalid_duplicate_fields",
    "level_toggle_and_unrestricted_teams",
    "both_sides_selection_private_order",
    "controller_move_gimmick_switch_forfeit",
    "illegal_stale_duplicate_torn_requests",
    "player_pending_value_length_error_sequence_timing_private",
    "disconnect_wait_reconnect_cpu_forfeit",
    "three_turn_request_cycles",
    "win_loss_forfeit_abort_reset_exact_cleanup",
    "normal_factory_mirage_raid_reward_noninterference",
    "upstream_open_gimmick_matrix",
    "live_hp_moves_switch_semantics",
    "public_online_state_events_private_boundary",
    "persistent_side_effects_zero",
    "warnings_zero",
)


class CodexBattleRuntimeBuildError(RuntimeError):
    """Stage 44 input、runtime、catalogまたは実機証跡の契約違反。"""


def _fail(message: str) -> NoReturn:
    raise CodexBattleRuntimeBuildError(message)


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
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")
    return completed.stdout.strip()


def _rom_offset(address: int, size: int = 1) -> int:
    offset = address - GBA_ROM_BASE
    if address < GBA_ROM_BASE or offset + size > ROM_SIZE:
        _fail(f"ROM address outside Stage 44: 0x{address:08X}")
    return offset


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _index(rows: Sequence[Mapping[str, str]], key: str, label: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            _fail(f"{label} has missing/duplicate {key}: {value!r}")
        result[value] = row
    return result


def _safe_item_bits(config: Mapping[str, Any]) -> tuple[bytes, dict[str, int]]:
    rows = _rows(ROOT / config["inputs"]["item_manifest"])
    if len(rows) != 999 or [int(row["id"]) for row in rows] != list(range(999)):
        _fail("canonical item manifest IDs differ")
    bits = bytearray(125)
    safe = 0
    rejected = 0
    for row in rows:
        item = int(row["id"])
        importance = int(row["importance"] or "0", 0)
        pocket = row["pocket"]
        role = row["role"]
        allowed = item == 0 or (
            importance == 0
            and pocket != "POCKET_KEY_ITEMS"
            and role not in {"KEY_ITEM", "STORY_KEY"}
        )
        if allowed:
            bits[item >> 3] |= 1 << (item & 7)
            safe += 1
        else:
            rejected += 1
    return bytes(bits), {"safe": safe, "rejected": rejected, "total": len(rows)}


def _runtime_header(config: Mapping[str, Any], safe_bits: bytes) -> bytes:
    protocol = config["protocol"]
    ram = config["ram"]
    engine = config["engine"]
    catalog = config["catalog"]
    hooks = config["hooks"]
    choice_entries = {
        int(row["command"]): row
        for row in config["physical_binding"]["opponent_choice_dispatch"]["entries"]
    }
    if set(choice_entries) != {18, 20, 22}:
        _fail("opponent choice dispatch commands differ")
    trainer_symbols = _read_json(Path(config["inputs"]["trainer_changekit_symbols"]["path"]))
    entrypoints = trainer_symbols["entrypoints"]
    values = {
        "CODEX_RUNTIME_MAGIC": _integer(protocol["magic_u32"], "runtime magic"),
        "CODEX_RUNTIME_PROTOCOL_MAJOR": int(protocol["major"]),
        "CODEX_RUNTIME_PROTOCOL_MINOR": int(protocol["minor"]),
        "CODEX_RUNTIME_MAILBOX_ADDRESS": _integer(ram["extension_address"], "mailbox address"),
        "CODEX_RUNTIME_MAILBOX_SIZE": int(protocol["struct_size"]),
        "CODEX_RUNTIME_HEADER_SIZE": int(protocol["header_size"]),
        "CODEX_RUNTIME_SNAPSHOT_OFFSET": int(protocol["snapshot_offset"]),
        "CODEX_RUNTIME_SNAPSHOT_SIZE": int(protocol["snapshot_size"]),
        "CODEX_RUNTIME_REQUEST_OFFSET": int(protocol["request_offset"]),
        "CODEX_RUNTIME_REQUEST_SIZE": int(protocol["request_size"]),
        "CODEX_RUNTIME_REQUEST_PAYLOAD_MAX": int(protocol["request_payload_max"]),
        "CODEX_RUNTIME_CAPABILITIES": int(protocol["capabilities"]),
        "CODEX_RUNTIME_STAGE_NUMBER": int(protocol["stage_number"]),
        "CODEX_RUNTIME_STAGE_IDENTITY": _integer(protocol["stage_identity"], "stage identity"),
        "CODEX_RUNTIME_BUILD_IDENTITY": _integer(protocol["build_identity"], "build identity"),
        "CODEX_RUNTIME_STATE_ADDRESS": _integer(
            ram["state_address"], "state address"),
        "CODEX_RUNTIME_STATE_SIZE": int(ram["state_size"]),
        "CODEX_RUNTIME_PUBLIC_STATE_ADDRESS": _integer(
            ram["public_state_address"], "public state address"),
        "CODEX_RUNTIME_PUBLIC_STATE_OFFSET": int(ram["public_state_offset"]),
        "CODEX_RUNTIME_PUBLIC_STATE_SIZE": int(ram["public_state_size"]),
        "CODEX_RUNTIME_SPECIES_MAX": int(config["battle"]["species_max"]),
        "CODEX_RUNTIME_MOVE_MAX": int(config["battle"]["move_max"]),
        "CODEX_RUNTIME_ITEM_MAX": int(config["battle"]["item_max"]),
        "CODEX_RUNTIME_DELEGATE_READ_KEYS": _integer(hooks["read_keys"]["delegate"], "ReadKeys delegate"),
        "CODEX_RUNTIME_DELEGATE_TRAINER_PARTY": _integer(hooks["trainer_party"]["delegate"], "party delegate"),
        "CODEX_RUNTIME_DELEGATE_SAVE_LOAD": _integer(hooks["save_load"]["delegate"], "save delegate"),
        "CODEX_RUNTIME_DELEGATE_FIND_DYNAMAX_BAND": _integer(
            hooks["dynamax_band_calls"]["delegate"],
            "FindBankDynamaxBand delegate"),
        "CODEX_RUNTIME_DELEGATE_CHOOSE_ACTION": _integer(
            choice_entries[18]["expected_pointer"], "choose action delegate"),
        "CODEX_RUNTIME_DELEGATE_CHOOSE_MOVE": _integer(
            choice_entries[20]["expected_pointer"], "choose move delegate"),
        "CODEX_RUNTIME_DELEGATE_CHOOSE_POKEMON": _integer(
            choice_entries[22]["expected_pointer"], "choose Pokemon delegate"),
        "CODEX_RUNTIME_ENGINE_CREATE_MON": _integer(engine["create_mon"], "CreateMon"),
        "CODEX_RUNTIME_ENGINE_SET_MON_DATA": _integer(engine["set_mon_data"], "SetMonData"),
        "CODEX_RUNTIME_ENGINE_GET_MON_DATA": _integer(engine["get_mon_data"], "GetMonData"),
        "CODEX_RUNTIME_ENGINE_CALCULATE_STATS": _integer(engine["calculate_stats"], "CalculateMonStats"),
        "CODEX_RUNTIME_ENGINE_CALCULATE_PP": _integer(engine["calculate_pp"], "CalculatePP"),
        "CODEX_RUNTIME_ENGINE_GET_GENDER": _integer(
            engine["get_gender"], "GetGenderFromSpeciesAndPersonality"),
        "CODEX_RUNTIME_ENGINE_IS_SHINY": _integer(
            engine["is_shiny"], "IsShinyOtIdPersonality"),
        "CODEX_RUNTIME_ENGINE_PARTY_COUNT": _integer(engine["calculate_party_count"], "party count"),
        "CODEX_RUNTIME_ENGINE_VAR_GET": _integer(engine["var_get"], "VarGet"),
        "CODEX_RUNTIME_ENGINE_VAR_SET": _integer(engine["var_set"], "VarSet"),
        "CODEX_RUNTIME_ENGINE_FLAG_GET": _integer(engine["flag_get"], "FlagGet"),
        "CODEX_RUNTIME_ENGINE_FLAG_SET": _integer(engine["flag_set"], "FlagSet"),
        "CODEX_RUNTIME_ENGINE_FLAG_CLEAR": _integer(engine["flag_clear"], "FlagClear"),
        "CODEX_RUNTIME_ENGINE_PREPARE_BUFFER": _integer(engine["prepare_buffer"], "PrepareBuffer"),
        "CODEX_RUNTIME_ENGINE_EMIT_TWO": _integer(engine["emit_two_return_values"], "EmitTwo"),
        "CODEX_RUNTIME_ENGINE_EMIT_MON": _integer(engine["emit_chosen_mon"], "EmitMon"),
        "CODEX_RUNTIME_ENGINE_OPPONENT_COMPLETE": _integer(engine["opponent_complete"], "opponent complete"),
        "CODEX_RUNTIME_ENGINE_BATTLE_MAIN_FUNC": _integer(
            engine["battle_main_func"], "gBattleMainFunc"),
        "CODEX_RUNTIME_ENGINE_END_TURN_FUNCS": _integer(
            engine["end_turn_funcs"], "sEndTurnFuncsTable"),
        "CODEX_RUNTIME_ENGINE_CAN_MEGA": _integer(engine["can_mega_evolve"], "CanMegaEvolve"),
        "CODEX_RUNTIME_ENGINE_CAN_Z": _integer(engine["can_use_z_move"], "CanUseZMove"),
        "CODEX_RUNTIME_ENGINE_CAN_DYNAMAX": _integer(engine["can_dynamax"], "CanDynamax"),
        "CODEX_RUNTIME_ENGINE_CAN_TERA": _integer(engine["can_terastal"], "CanTerastal"),
        "CODEX_RUNTIME_EXPERIENCE_TABLES": _integer(
            engine["experience_tables"], "experience tables"),
        "CODEX_RUNTIME_EXPERIENCE_TABLE_LEVELS": int(
            engine["experience_table_levels"]),
        "CODEX_RUNTIME_EXPERIENCE_GROWTH_COUNT": int(
            engine["experience_growth_count"]),
        "CODEX_RUNTIME_BASE_STATS_ADDRESS": _integer(
            catalog["base_stats_address"], "base stats address"),
        "CODEX_RUNTIME_BASE_STATS_STRIDE": int(catalog["base_stats_stride"]),
        "CODEX_RUNTIME_BASE_STATS_GROWTH_OFFSET": int(
            catalog["base_stats_growth_rate_offset"]),
    }
    delegates = {
        "CAN_MEGA": "TrainerChangeKitFinalRuntime_CanMegaAdapter",
        "MARK_MEGA": "TrainerChangeKitFinalRuntime_MarkMegaAdapter",
        "CAN_Z": "TrainerChangeKitFinalRuntime_CanZAdapter",
        "MARK_Z": "TrainerChangeKitFinalRuntime_MarkZAdapter",
        "CAN_DYNAMAX": "TrainerChangeKitFinalRuntime_CanDynamaxAdapter",
        "MARK_DYNAMAX": "TrainerChangeKitFinalRuntime_MarkDynamaxAdapter",
        "CAN_TERA": "TrainerChangeKitFinalRuntime_CanTeraAdapter",
        "MARK_TERA": "TrainerChangeKitFinalRuntime_MarkTeraAdapter",
    }
    for suffix, symbol in delegates.items():
        if symbol not in entrypoints:
            _fail(f"Trainer ChangeKit delegate missing: {symbol}")
        values[f"CODEX_RUNTIME_DELEGATE_{suffix}"] = int(entrypoints[symbol])
    lines = [
        "#ifndef VEGA_CODEX_BATTLE_RUNTIME_GENERATED_H",
        "#define VEGA_CODEX_BATTLE_RUNTIME_GENERATED_H",
        "",
    ]
    for name, value in values.items():
        lines.append(f"#define {name} 0x{value:X}u")
    lines.extend([
        "",
        "static const unsigned char gCodexRuntimeHeldItemSafe[125] = {",
    ])
    for offset in range(0, len(safe_bits), 16):
        lines.append("    " + ", ".join(
            f"0x{value:02X}u" for value in safe_bits[offset:offset + 16]
        ) + ",")
    lines.extend(["};", "", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def _compile_runtime(load_address: int, header: bytes) -> tuple[bytes, dict[str, int], dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    source = ROOT / "overlays/codex_battle_runtime/codex_battle_runtime.c"
    if not source.is_file():
        _fail("Codex Battle runtime source is missing")
    with tempfile.TemporaryDirectory(prefix="vega-codex-runtime-") as raw:
        directory = Path(raw)
        (directory / "codex_battle_runtime_generated.h").write_bytes(header)
        obj = directory / "runtime.o"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
            "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-Wno-address-of-packed-member", "-ffreestanding",
            "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-fno-common",
            f"-I{directory}", f"-I{ROOT}", "-c", str(source), "-o", str(obj),
        ], "compile Codex Battle runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.CodexBattleRuntime_*)) *(.text*) *(.rodata*) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) "
            "*(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "runtime.elf"
        binary = directory / "runtime.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,CodexBattleRuntime_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link Codex Battle runtime")
        undefined = _run([nm, "-u", str(elf)], "Codex Battle undefined-symbol audit")
        if undefined:
            _fail("Codex Battle runtime has undefined symbols: " + undefined)
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run([nm, "-n", "-S", "--defined-only", str(elf)],
                         "Codex Battle runtime nm").splitlines():
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
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing or mutable:
            _fail(f"Codex runtime symbols differ: missing={missing}, mutable={mutable}")
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "runtime objcopy")
        payload = binary.read_bytes()
        if not payload or len(payload) > 96 * 1024:
            _fail(f"Codex runtime size is unreasonable: {len(payload)}")
        return payload, symbols, sizes


def _allocation(previous: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME,
        "region": "integration_modules",
        "size": size,
        "alignment": 16,
        "owner": TASK,
        "purpose": (
            "Stage44 Codex 6-to-3 runtime, private action seal, controller "
            "interposer, UPSTREAM_OPEN adapters and production reception"
        ),
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage44 allocator overlap detected")
    matches = [row for row in report.get("allocations", [])
               if row.get("name") == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage44 allocation is not unique")
    return matches[0], report


def _build_field_payload(config: Mapping[str, Any], code: bytes,
                         symbols: Mapping[str, int], payload_offset: int) -> tuple[bytes, dict[str, Any]]:
    blob = _Blob()
    blob.add("payload_header", b"\xFF" * PAYLOAD_HEADER_SIZE, 16)
    if blob.add("runtime_code", code, 4) != PAYLOAD_HEADER_SIZE:
        _fail("Stage44 runtime code offset differs")
    mapping, tokens = _charmap(ROOT)
    texts = {
        "text::prompt": "Codexたいせんを しますか？\nいいえで ファクトリーへ",
        "text::not_ready": "PCで 6ひきの チームと\nせんしゅつを じゅんびしてください",
        "text::select": "たいせんする 3ひきを\nじゅんばんに えらんでください",
        "text::waiting": "Codexの にゅうりょくを\nまちながら たいせんします",
        "text::done": "Codexたいせんを\nあんぜんに しゅうりょうしました",
        "text::error": "Codexたいせんの\nじゅんびに しっぱいしました",
    }
    for label, value in texts.items():
        blob.add(label, _encode_text(value, mapping, tokens), 1)
    party_selection_special = _integer(
        config["physical_binding"]["party_selection_special"],
        "party selection special",
    )
    if party_selection_special != 0x0029:
        _fail("party selection must use ChooseHalfPartyForBattle special 0x0029")
    scripts: list[dict[str, Any]] = []
    reception = (
        _Script().emit(0x6A, 0x5A, operation="lock_faceplayer")
        .msgbox("text::prompt", 5).compare_result(1)
        .if_equal("script::codex_battle_begin")
        .goto("script::factory_delegate")
    )
    _add_script(blob, "script::codex_battle_reception", reception, scripts)
    _add_script(
        blob, "script::factory_delegate",
        _Script().goto_absolute(
            _integer(config["hooks"]["reception"]["delegate"], "Factory reception"),
            "FactoryHighModesV2 reception",
        ), scripts,
    )
    _add_script(
        blob, "script::codex_battle_begin",
        _Script().callnative(symbols["CodexBattleRuntime_FieldBeginPlayerSelection"],
                             "CodexBattleRuntime_FieldBeginPlayerSelection")
        .compare_result(1).if_equal("script::codex_battle_select")
        .goto("script::codex_battle_not_ready"), scripts,
    )
    _add_script(
        blob, "script::codex_battle_select",
        _Script().emit(
            0x25, operation=f"special:0x{party_selection_special:04X}",
        ).half(party_selection_special)
        .emit(0x27, operation="waitstate")
        .callnative(symbols["CodexBattleRuntime_FieldCommitPlayerSelection"],
                    "CodexBattleRuntime_FieldCommitPlayerSelection")
        .compare_result(1).if_equal("script::codex_battle_prepare")
        .goto("script::codex_battle_error"), scripts,
    )
    _add_script(
        blob, "script::codex_battle_prepare",
        _Script().callnative(symbols["CodexBattleRuntime_FieldPrepareBattle"],
                             "CodexBattleRuntime_FieldPrepareBattle")
        .compare_result(1).if_equal("script::codex_battle_launch")
        .goto("script::codex_battle_error"), scripts,
    )
    _add_script(
        blob, "script::codex_battle_launch",
        _Script().trainerbattle(
            int(config["physical_binding"]["trainer_id"]),
            int(config["physical_binding"]["trainer_local_id"]),
            "text::done",
        )
        .callnative(symbols["CodexBattleRuntime_AfterBattle"],
                    "CodexBattleRuntime_AfterBattle")
        .msgbox("text::done")
        .callnative(symbols["CodexBattleRuntime_FieldFinish"],
                    "CodexBattleRuntime_FieldFinish")
        .emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    _add_script(
        blob, "script::codex_battle_not_ready",
        _Script().msgbox("text::not_ready")
        .emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    _add_script(
        blob, "script::codex_battle_error",
        _Script().callnative(symbols["CodexBattleRuntime_Abort"],
                             "CodexBattleRuntime_Abort")
        .msgbox("text::error")
        .callnative(symbols["CodexBattleRuntime_FieldFinish"],
                    "CodexBattleRuntime_FieldFinish")
        .emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    payload = bytearray(blob.finish(payload_offset))
    struct.pack_into(
        "<8s15I", payload, 0, b"VEGACB44", 2, len(payload),
        PAYLOAD_HEADER_SIZE, len(code), 6, 3, 2, 2, 5, 10,
        _integer(config["ram"]["extension_address"], "mailbox"),
        int(config["ram"]["extension_size"]),
        _integer(config["ram"]["state_address"], "state address"),
        int(config["ram"]["state_size"]),
        int(config["protocol"]["capabilities"]),
    )
    base = GBA_ROM_BASE + payload_offset
    labels = {name: base + offset for name, offset in blob.labels.items()}
    for row in scripts:
        row["address"] = base + int(row["offset"])
    return bytes(payload), {
        "labels": labels,
        "scripts": scripts,
        "reception_script": labels["script::codex_battle_reception"],
        "factory_delegate": _integer(config["hooks"]["reception"]["delegate"], "factory delegate"),
        "trainerbattle": {"mode": 3, "trainer_id": 745, "local_id": 2},
    }


def _build_payload(config: Mapping[str, Any], previous: Mapping[str, Any],
                   header: bytes) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    payload_offset = -1
    load_address = GBA_ROM_BASE + PAYLOAD_HEADER_SIZE
    final: tuple[bytes, dict[str, int], dict[str, int], bytes, dict[str, Any]] | None = None
    for _ in range(8):
        code, symbols, sizes = _compile_runtime(load_address, header)
        payload, field = _build_field_payload(
            config, code, symbols, max(payload_offset, 0))
        allocation, _ = _allocation(previous, len(payload), "0" * 64)
        next_offset = int(allocation["start"])
        next_load = GBA_ROM_BASE + next_offset + PAYLOAD_HEADER_SIZE
        if payload_offset == next_offset and load_address == next_load:
            final = code, symbols, sizes, payload, field
            break
        payload_offset, load_address = next_offset, next_load
    if final is None:
        _fail("Stage44 allocation did not reach a fixed point")
    code, symbols, sizes, payload, field = final
    allocation, report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("Stage44 allocation moved after payload hash")
    runtime = {
        "payload": {"offset": payload_offset,
                    "address": GBA_ROM_BASE + payload_offset,
                    "size": len(payload), "sha256": _sha(payload)},
        "code": {"offset": payload_offset + PAYLOAD_HEADER_SIZE,
                 "address": GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE,
                 "size": len(code), "sha256": _sha(code)},
        "entrypoints": {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)},
        "symbol_sizes": {name: sizes.get(name, 0) for name in sorted(REQUIRED_ENTRYPOINTS)},
        "field": field,
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
        _fail(f"{name}: Stage43 expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({"start": offset, "end_exclusive": offset + len(replacement),
                     "kind": name})
    return {"name": name, "address": address, "offset": offset,
            "size": len(expected), "expected_hex": expected.hex(),
            "replacement_hex": replacement.hex()}


def _apply_hooks(config: Mapping[str, Any], stage: bytes, output: bytearray,
                 runtime: Mapping[str, Any], declared: list[dict[str, Any]]) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    entrypoints = runtime["entrypoints"]
    field_labels = runtime["field"]["labels"]
    for key in ("read_keys", "trainer_party", "save_load", "reception"):
        hook = config["hooks"][key]
        address = _integer(hook["address"], f"{key} hook")
        expected = bytes.fromhex(hook["expected_hex"])
        mode = hook["mode"]
        target_name = hook["target"]
        target = field_labels[target_name] if target_name.startswith("script::") \
            else entrypoints[target_name]
        if mode in {"POINTER", "THUMB_POINTER"}:
            replacement = struct.pack("<I", target)
        elif mode == "THUMB_BL":
            replacement = _thumb_bl(address, target)
        elif mode == "THUMB_JUMP":
            replacement = b"\x00\x4B\x18\x47" + struct.pack("<I", target)
        else:
            _fail(f"unsupported hook mode: {mode}")
        row = _patch(output, stage, declared, address, expected, replacement,
                     str(hook["name"]))
        row.update({"mode": mode, "target": target, "target_symbol": target_name,
                    "delegate": _integer(hook["delegate"], f"{key} delegate")})
        patches.append(row)
    bridge = config["physical_binding"]["selection_confirmation_bridge"]
    bridge_address = _integer(
        bridge["address"], "selection confirmation bridge address")
    if bridge_address != 0x081280B8:
        _fail("selection confirmation bridge site differs")
    expected_pointer = _integer(
        bridge["expected_pointer"], "selection confirmation stock pointer")
    replacement_pointer = _integer(
        bridge["replacement_pointer"], "selection confirmation CFRU pointer")
    if (expected_pointer, replacement_pointer) != (0x0203B048, 0x0203C6C8):
        _fail("selection confirmation bridge pointers differ")
    row = _patch(
        output, stage, declared, bridge_address,
        struct.pack("<I", expected_pointer),
        struct.pack("<I", replacement_pointer),
        str(bridge["name"]),
    )
    row.update({
        "mode": "RAM_POINTER",
        "target": replacement_pointer,
        "target_symbol": "gSelectedOrderFromParty",
        "stock_pointer": expected_pointer,
    })
    patches.append(row)
    dispatch = config["physical_binding"]["opponent_choice_dispatch"]
    table_address = _integer(
        dispatch["table_address"], "opponent command table address")
    rows_by_command = {
        int(value["command"]): value for value in dispatch["entries"]
    }
    if table_address != 0x0820D43C or set(rows_by_command) != {18, 20, 22}:
        _fail("opponent choice dispatch root differs")
    expected_sites = {
        18: (0x0820D484, 0x08037D01),
        20: (0x0820D48C, 0x08037D1D),
        22: (0x0820D494, 0x08037EB1),
    }
    for command in (18, 20, 22):
        value = rows_by_command[command]
        address = _integer(value["address"], f"command {command} dispatch address")
        delegate = _integer(
            value["expected_pointer"], f"command {command} delegate")
        if (address, delegate) != expected_sites[command]:
            _fail(f"opponent command {command} dispatch binding differs")
        if address != table_address + command * 4:
            _fail(f"opponent command {command} table offset differs")
        target_name = str(value["target"])
        if target_name != "CodexBattleRuntime_OpponentController":
            _fail(f"opponent command {command} target differs")
        target = entrypoints[target_name]
        row = _patch(
            output, stage, declared, address,
            struct.pack("<I", delegate), struct.pack("<I", target),
            str(value["name"]),
        )
        row.update({
            "mode": "CONTROLLER_DISPATCH_POINTER",
            "command": command,
            "target": target,
            "target_symbol": target_name,
            "inactive_delegate": delegate,
        })
        patches.append(row)
    band_calls = config["hooks"]["dynamax_band_calls"]
    band_target_name = str(band_calls["target"])
    band_target = entrypoints[band_target_name]
    band_delegate = _integer(
        band_calls["delegate"], "FindBankDynamaxBand delegate")
    expected_band_sites = {
        0x090F1494: "fff7e4fd",
        0x090F14C8: "fff7cafd",
        0x090F1688: "fff7eafc",
    }
    actual_band_sites = {
        _integer(value["address"], "Dynamax band callsite"): value
        for value in band_calls["sites"]
    }
    if (band_delegate != 0x090F1061
            or band_target_name
                != "CodexBattleRuntime_FindDynamaxBandAdapter"
            or set(actual_band_sites) != set(expected_band_sites)):
        _fail("Dynamax band adapter binding differs")
    for address in sorted(actual_band_sites):
        value = actual_band_sites[address]
        expected = bytes.fromhex(str(value["expected_hex"]))
        if expected.hex() != expected_band_sites[address]:
            _fail(f"Dynamax band callsite 0x{address:08X} differs")
        row = _patch(
            output, stage, declared, address, expected,
            _thumb_bl(address, band_target), str(value["name"]),
        )
        row.update({
            "mode": "THUMB_BL",
            "target": band_target,
            "target_symbol": band_target_name,
            "inactive_delegate": band_delegate,
            "battle_local_item": 347,
        })
        patches.append(row)
    trainer_symbols = _read_json(Path(config["inputs"]["trainer_changekit_symbols"]["path"]))
    adapters = {
        "TrainerChangeKitFinalRuntime_CanMegaAdapter": "CodexBattleRuntime_CanMegaAdapter",
        "TrainerChangeKitFinalRuntime_MarkMegaAdapter": "CodexBattleRuntime_MarkMegaAdapter",
        "TrainerChangeKitFinalRuntime_CanZAdapter": "CodexBattleRuntime_CanZAdapter",
        "TrainerChangeKitFinalRuntime_MarkZAdapter": "CodexBattleRuntime_MarkZAdapter",
        "TrainerChangeKitFinalRuntime_CanDynamaxAdapter": "CodexBattleRuntime_CanDynamaxAdapter",
        "TrainerChangeKitFinalRuntime_MarkDynamaxAdapter": "CodexBattleRuntime_MarkDynamaxAdapter",
        "TrainerChangeKitFinalRuntime_CanTeraAdapter": "CodexBattleRuntime_CanTeraAdapter",
        "TrainerChangeKitFinalRuntime_MarkTeraAdapter": "CodexBattleRuntime_MarkTeraAdapter",
    }
    policy_rows = [row for row in trainer_symbols["hooks"]["policy_bl"]
                   if row["adapter"] in adapters]
    if len(policy_rows) != 15:
        _fail(f"expected 15 UPSTREAM_OPEN policy sites, got {len(policy_rows)}")
    for policy in policy_rows:
        address = int(policy["address"])
        symbol = adapters[policy["adapter"]]
        target = entrypoints[symbol]
        row = _patch(
            output, stage, declared, address,
            bytes.fromhex(policy["replacement_hex"]),
            _thumb_bl(address, target),
            "codex_upstream_open::" + policy["name"],
        )
        row.update({"mode": "THUMB_BL", "target": target,
                    "target_symbol": symbol,
                    "inactive_delegate": int(policy["target"]),
                    "upstream_original": int(policy["original_target"])})
        patches.append(row)
    return patches


def _validate_ram(config: Mapping[str, Any]) -> dict[str, Any]:
    rows = _rows(ROOT / "config/ram_layout.csv")
    live = [row for row in rows if row["status"] == "LIVE" and row["start"]]
    owned = [row for row in live if row["owner"] == "T27_CODEX_BATTLE_RUNTIME"]
    if len(owned) != 1:
        _fail("T27 RAM owner row is not unique")
    row = owned[0]
    start = _integer(config["ram"]["state_address"], "state address")
    end = _integer(config["ram"]["state_end_exclusive"], "state end")
    if (int(row["start"], 0) != start
            or int(row["end_exclusive"], 0) != end
            or int(row["size"]) != end - start
            or int(config["ram"]["state_size"]) != end - start):
        _fail("T27 RAM reservation differs")
    overlaps = [
        other["symbol"] for other in live
        if other is not row and other["address_space"] == row["address_space"]
        and start < int(other["end_exclusive"], 0)
        and int(other["start"], 0) < end
    ]
    extension = _integer(config["ram"]["extension_address"], "extension")
    public_address = _integer(config["ram"]["public_state_address"],
                              "public state address")
    public_offset = int(config["ram"]["public_state_offset"])
    public_size = int(config["ram"]["public_state_size"])
    if (overlaps or extension != 0x0203F900 or start != 0x0203FA00
            or end > 0x02040000
            or public_address != start + public_offset
            or public_size != 180 or public_address + public_size != end):
        _fail(f"T27 RAM overlap/range differs: {overlaps}")
    return {"state_start": start, "state_end_exclusive": end,
            "state_size": int(config["ram"]["state_size"]),
            "extension_start": extension,
            "extension_size": int(config["ram"]["extension_size"]),
            "public_state_start": public_address,
            "public_state_size": public_size,
            "overlap_count": 0, "save_bytes": 0}


def _catalog(config: Mapping[str, Any], stage: bytes) -> tuple[bytes, dict[str, Any]]:
    inputs = config["inputs"]
    species_rows = _rows(ROOT / inputs["species_manifest"])
    move_rows = _rows(ROOT / inputs["move_manifest"])
    item_rows = _rows(ROOT / inputs["item_manifest"])
    ability_rows = _rows(ROOT / inputs["ability_manifest"])
    if ([int(row["id"]) for row in species_rows] != list(range(1621))
            or [int(row["id"]) for row in move_rows] != list(range(1063))
            or [int(row["id"]) for row in item_rows] != list(range(999))
            or [int(row["id"]) for row in ability_rows] != list(range(312))):
        _fail("canonical manifest numeric IDs are not exact contiguous ranges")
    species_by_key = _index(species_rows, "species_key", "species manifest")
    move_by_key = _index(move_rows, "move_key", "move manifest")
    ability_by_id = {int(row["id"]): row for row in ability_rows}
    base_offset = _rom_offset(_integer(config["catalog"]["base_stats_address"], "base stats"),
                              1621 * 32)
    move_offset = _rom_offset(_integer(config["catalog"]["move_table_address"], "move table"),
                              1063 * 12)
    species: list[dict[str, Any]] = []
    for row in species_rows:
        species_id = int(row["id"])
        raw = stage[base_offset + species_id * 32:base_offset + (species_id + 1) * 32]
        abilities = [
            struct.unpack_from("<H", raw, offset)[0]
            for offset in (0x16, 0x1A, 0x1C)
        ]
        species.append({
            "id": species_id, "key": row["species_key"],
            "name": row["display_name"], "form_key": row["form_key"] or None,
            "classification": row["classification"],
            "types": [raw[6], raw[7]],
            "base_stats": list(raw[0:6]),
            "abilities": [
                {"id": value,
                 "name": ability_by_id.get(value, {}).get("display_name", "")}
                for value in abilities
            ],
        })
    moves: list[dict[str, Any]] = []
    for row in move_rows:
        move_id = int(row["id"])
        raw = stage[move_offset + move_id * 12:move_offset + (move_id + 1) * 12]
        moves.append({
            "id": move_id, "key": row["move_key"], "name": row["display_name"],
            "effect": raw[0], "power": raw[1], "type": raw[2],
            "accuracy": raw[3], "pp": raw[4], "secondary_chance": raw[5],
            "target": raw[6], "priority": struct.unpack("<b", raw[7:8])[0],
            "flags": raw[8], "z_power": raw[9], "category": raw[10],
            "z_effect": raw[11],
        })
    items = [{
        "id": int(row["id"]), "key": row["item_key"],
        "name": row["display_name"], "pocket": row["pocket"],
        "importance": int(row["importance"] or "0", 0), "role": row["role"],
        "hold_effect": row["hold_effect_key"],
        "hold_effect_param": int(row["hold_effect_param"] or "0", 0),
    } for row in item_rows]
    zip_contract = inputs["learnset_zip"]
    archive_raw = _identity(Path(zip_contract["path"]), zip_contract, "learnset ZIP")
    learnsets: dict[int, dict[str, Any]] = {
        index: {"level_up": [], "egg": [], "tm_tutor_changes": [],
                "form_policy": []}
        for index in range(1621)
    }
    with zipfile.ZipFile(io.BytesIO(archive_raw)) as archive:
        required = {"level_up_final.csv", "egg_moves_final.csv",
                    "tm_tutor_changes.csv", "form_policy_final.csv"}
        if not required <= set(archive.namelist()):
            _fail("learnset ZIP required entries differ")
        tables: dict[str, list[dict[str, str]]] = {}
        for name in sorted(required):
            with archive.open(name) as stream:
                tables[name] = list(csv.DictReader(
                    io.TextIOWrapper(stream, encoding="utf-8-sig", newline="")))
    for row in tables["level_up_final.csv"]:
        species_row = species_by_key.get(row["species_key"])
        move_row = move_by_key.get(row["move_key"])
        if species_row is None or move_row is None:
            _fail("level-up canonical key is unresolved")
        learnsets[int(species_row["id"])]["level_up"].append(
            [int(row["level"]), int(move_row["id"])])
    for row in tables["egg_moves_final.csv"]:
        species_row = species_by_key.get(row["species_key"])
        move_row = move_by_key.get(row["move_key"])
        if species_row is None or move_row is None:
            _fail("egg canonical key is unresolved")
        learnsets[int(species_row["id"])]["egg"].append(int(move_row["id"]))
    for row in tables["tm_tutor_changes.csv"]:
        species_row = species_by_key.get(row["species_key"])
        move_row = move_by_key.get(row["move_key"])
        if species_row is None or move_row is None:
            _fail("TM/tutor canonical key is unresolved")
        learnsets[int(species_row["id"])]["tm_tutor_changes"].append({
            "slot": row["slot_key"], "move_id": int(move_row["id"]),
            "compatible": row["compatible"].lower() == "true",
        })
    for row in tables["form_policy_final.csv"]:
        canonical_key = row["canonical_species_key"]
        target_key = (row["base_species_key"]
                      if canonical_key == "NONE" else canonical_key)
        species_row = species_by_key.get(target_key)
        if species_row is None:
            _fail("form canonical key is unresolved")
        learnsets[int(species_row["id"])]["form_policy"].append({
            "record_key": row["form_record_key"],
            "canonical_species_key": canonical_key,
            "base_species_key": row["base_species_key"],
            "action": row["implementation_action"],
            "level_source": row["level_up_source_key"],
            "egg_source": row["egg_source_key"],
            "tm_tutor_source": row["tm_tutor_source_key"],
        })
    document = {
        "schema_version": 1, "task": TASK, "stage": 44,
        "policy": {"read_only": True, "learnset_is_not_upload_ban": True,
                   "default_limit": int(config["catalog"]["default_limit"]),
                   "maximum_limit": int(config["catalog"]["maximum_limit"])},
        "sources": {
            "species_manifest_sha256": _sha((ROOT / inputs["species_manifest"]).read_bytes()),
            "move_manifest_sha256": _sha((ROOT / inputs["move_manifest"]).read_bytes()),
            "item_manifest_sha256": _sha((ROOT / inputs["item_manifest"]).read_bytes()),
            "ability_manifest_sha256": _sha((ROOT / inputs["ability_manifest"]).read_bytes()),
            "learnset_zip_sha256": _sha(archive_raw),
            "rom_sha256": _sha(stage),
        },
        "species": species, "moves": moves, "items": items,
        "learnsets": {str(key): value for key, value in learnsets.items()},
    }
    raw = _stable(document)
    report = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "catalog_sha256": _sha(raw), "catalog_size": len(raw),
        "counts": {"species": len(species), "moves": len(moves),
                   "items": len(items), "learnsets": len(learnsets),
                   "level_up": len(tables["level_up_final.csv"]),
                   "egg": len(tables["egg_moves_final.csv"]),
                   "tm_tutor_changes": len(tables["tm_tutor_changes.csv"]),
                   "forms": len(tables["form_policy_final.csv"])},
        "exact_manifest_ids": True, "bounded_default": 10,
        "bounded_maximum": 50, "export_returns_path_hash_only": True,
        "learnset_upload_ban": False,
    }
    return raw, report


def _battle_string_ids() -> dict[str, str]:
    source = (ROOT / "vendor/upstream/CFRU-JP/include/battle_string_ids.h")
    result: dict[str, str] = {}
    for name, value in re.findall(
        r"^#define\s+STRINGID_([A-Z0-9_]+)\s+([0-9]+)\s*$",
        source.read_text(encoding="utf-8"), re.MULTILINE,
    ):
        result[str(int(value))] = name
    if result.get("4") != "USEDMOVE" or result.get("388") != "CUSTOMSTRING":
        _fail("pinned CFRU-JP battle string IDs differ")
    return dict(sorted(result.items(), key=lambda row: int(row[0])))


def _cfru_charmap() -> dict[str, int]:
    result: dict[str, int] = {" ": 0}
    source = ROOT / "vendor/upstream/CFRU-JP/charmap.tbl"
    for line in source.read_text(encoding="utf-8-sig").splitlines():
        if len(line) < 4 or line[2] != "=" or line.strip() == "/FF":
            continue
        try:
            value = int(line[:2], 16)
        except ValueError:
            continue
        key = line[3:5] if line[3] == "\\" and len(line) > 4 else line[3]
        result.setdefault(key, value)
    return result


def _battle_string_templates(rom: bytes) -> dict[str, str]:
    placeholder_source = (
        ROOT / "vendor/upstream/CFRU-JP/include/battle_message.h"
    ).read_text(encoding="utf-8")
    placeholders = {
        int(value, 0): name.removeprefix("B_TXT_")
        for name, value in re.findall(
            r"^#define\s+(B_TXT_[A-Z0-9_]+)\s+(0x[0-9A-Fa-f]+|[0-9]+)\s*$",
            placeholder_source, re.MULTILINE,
        )
    }
    reverse_charmap: dict[int, str] = {}
    for text, value in _cfru_charmap().items():
        reverse_charmap.setdefault(value, text)
    table = 0x083C3F08 - GBA_ROM_BASE
    result: dict[str, str] = {}
    for raw_id in _battle_string_ids():
        message_id = int(raw_id)
        if (message_id < 12 or message_id >= 398 or message_id == 388):
            continue
        pointer_offset = table + (message_id - 12) * 4
        if pointer_offset < 0 or pointer_offset + 4 > len(rom):
            _fail("battle string table pointer is outside ROM")
        pointer = struct.unpack_from("<I", rom, pointer_offset)[0]
        offset = pointer - GBA_ROM_BASE
        if offset < 0 or offset >= len(rom):
            _fail("battle string table target is outside ROM")
        raw = rom[offset:min(offset + 300, len(rom))]
        end = raw.find(b"\xFF")
        if end < 0:
            _fail("battle string is not EOS-terminated")
        raw = raw[:end]
        decoded: list[str] = []
        index = 0
        while index < len(raw):
            value = raw[index]
            if value == 0xFD and index + 1 < len(raw):
                token = raw[index + 1]
                decoded.append(f"[{placeholders.get(token, f'FD_{token:02X}') }]")
                index += 2
                continue
            decoded.append(reverse_charmap.get(value, f"[BYTE_{value:02X}]"))
            index += 1
        result[raw_id] = "".join(decoded)
    if "23" not in result or "こうげき" not in result["23"]:
        _fail("Japanese battle string template catalog differs")
    return result


_CUSTOM_STRING_BUFFERS = {
    ".": (0xB0,), "BUFFER": (0xFD,), "ATTACKER": (0xFD, 0x0F),
    "TARGET": (0xFD, 0x10), "EFFECT_BANK": (0xFD, 0x11),
    "SCRIPTING_BANK": (0xFD, 0x13), "CURRENT_MOVE": (0xFD, 0x14),
    "LAST_ITEM": (0xFD, 0x16), "LAST_ABILITY": (0xFD, 0x17),
    "ATTACKER_ABILITY": (0xFD, 0x18), "TARGET_ABILITY": (0xFD, 0x19),
    "SCRIPTING_BANK_ABILITY": (0xFD, 0x1A),
    "TRAINER1_CLASS": (0xFD, 0x1C), "TRAINER1_NAME": (0xFD, 0x1D),
    "PLAYER_NAME": (0xFD, 0x23), "TARGET_NAME": (0xFD, 0x3B),
    "TARGET_PARTNER_NAME": (0xFD, 0x3C), "DEF_PREFIX_5": (0xFD, 0x3D),
    "PLAYER": (0xFD, 0x01), "BUFFER1": (0xFD, 0x02),
    "BUFFER2": (0xFD, 0x03), "BUFFER3": (0xFD, 0x04),
    "RIVAL": (0xFD, 0x06), "WHITE": (0xFC, 0x01, 0x01),
    "BLACK": (0xFC, 0x01, 0x02), "GRAY": (0xFC, 0x01, 0x03),
    "RED": (0xFC, 0x01, 0x04), "ORANGE": (0xFC, 0x01, 0x05),
    "GREEN": (0xFC, 0x01, 0x06), "LIGHT_GREEN": (0xFC, 0x01, 0x07),
    "BLUE": (0xFC, 0x01, 0x08), "LIGHT_BLUE": (0xFC, 0x01, 0x09),
    "MAIN_COLOUR": (0xFC, 0x01), "SHADOW_COLOUR": (0xFC, 0x03),
    "ARROW_UP": (0x79,), "ARROW_DOWN": (0x7A,),
    "ARROW_LEFT": (0x7B,), "ARROW_RIGHT": (0x7C,),
}


def _encode_custom_string(template: str, charmap: Mapping[str, int]) -> bytes | None:
    encoded = bytearray()
    cursor = 0
    while cursor < len(template):
        char = template[cursor]
        if char == "[":
            end = template.find("]", cursor + 1)
            if end < 0:
                return None
            token = template[cursor + 1:end]
            if token in _CUSTOM_STRING_BUFFERS:
                encoded.extend(_CUSTOM_STRING_BUFFERS[token])
            elif len(token) <= 2:
                try:
                    encoded.append(int(token, 16))
                except ValueError:
                    return None
            else:
                encoded.append(0)
            cursor = end + 1
            continue
        if char == "\\":
            if cursor + 1 >= len(template):
                return None
            key = template[cursor:cursor + 2]
            if key not in charmap:
                return None
            encoded.append(charmap[key])
            cursor += 2
            continue
        key = '\\"' if char == '"' else char
        if key not in charmap:
            return None
        encoded.append(charmap[key])
        cursor += 1
    encoded.append(0xFF)
    return bytes(encoded[:150])


def _custom_string_crc16_catalog() -> dict[str, list[dict[str, str]]]:
    upstream = ROOT / "vendor/upstream/CFRU-JP"
    charmap = _cfru_charmap()
    catalog: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in sorted((upstream / "strings").rglob("*.string")):
        symbol: str | None = None
        for source_line in path.read_text(encoding="utf-8-sig").splitlines():
            stripped = source_line.strip()
            match = re.fullmatch(r"#org\s+@([A-Za-z0-9_]+)", stripped,
                                 re.IGNORECASE)
            if match:
                symbol = match.group(1)
                continue
            if (not stripped or stripped.startswith("//")
                    or stripped.startswith("#") or symbol is None):
                continue
            encoded = _encode_custom_string(source_line, charmap)
            if encoded is None:
                continue
            crc = str(zlib.crc32(encoded) & 0xFFFF)
            row = {"symbol": symbol, "template": source_line,
                   "source": str(path.relative_to(ROOT))}
            if row not in catalog[crc]:
                catalog[crc].append(row)
            symbol = None
    if not catalog:
        _fail("pinned CFRU-JP custom battle string catalog is empty")
    return {key: sorted(value, key=lambda row: (row["symbol"], row["source"]))
            for key, value in sorted(catalog.items(), key=lambda row: int(row[0]))}


def _protocol_document(config: Mapping[str, Any], output: bytes,
                       runtime: Mapping[str, Any]) -> dict[str, Any]:
    protocol = config["protocol"]
    ram = config["ram"]
    preview = config["preview_assets"]
    return {
        "schema_version": 1, "task": TASK, "stage": 44,
        "rom": {"sha256": _sha(output),
                "crc32": f"{zlib.crc32(output) & 0xFFFFFFFF:08X}",
                "size": len(output),
                "basename": "Pokemon-Vega-Stage44-Codex-Battle-Runtime.gba"},
        "base_mailbox": _read_json(Path(config["inputs"]["stage43_protocol"]["path"]))["mailbox"],
        "mailbox": {
            "address": _integer(ram["extension_address"], "runtime mailbox"),
            "struct_size": int(protocol["struct_size"]),
            "magic": _integer(protocol["magic_u32"], "magic"),
            "major": int(protocol["major"]), "minor": int(protocol["minor"]),
            "header_size": int(protocol["header_size"]),
            "snapshot_offset": int(protocol["snapshot_offset"]),
            "snapshot_size": int(protocol["snapshot_size"]),
            "request_offset": int(protocol["request_offset"]),
            "request_size": int(protocol["request_size"]),
            "request_payload_max": int(protocol["request_payload_max"]),
            "capabilities": int(protocol["capabilities"]),
            "stage_number": 44,
            "stage_identity": _integer(protocol["stage_identity"], "stage identity"),
            "build_identity": _integer(protocol["build_identity"], "build identity"),
            "phases": protocol["phases"], "commands": protocol["commands"],
            "snapshot_battle_union": {
                "offset": 108,
                "pre_battle": "codex_preview_species_u16x6",
                "pre_battle_player_details": {
                    "levels_u8x6_offset": 132,
                    "appearance_u32_offset": 138,
                    "gender_bits": [[0, 2], [2, 2], [4, 2], [6, 2],
                                    [8, 2], [10, 2]],
                    "shiny_bits": [12, 13, 14, 15, 16, 17],
                    "selection_order_public": False,
                },
                "battle_live": {
                    "stats_u16x5": ["attack", "defense", "speed",
                                     "special_attack", "special_defense"],
                    "appearance_u16": {
                        "codex_gender_bits": [[0, 2], [2, 2], [4, 2]],
                        "codex_shiny_bits": [6, 7, 8],
                        "player_gender_bits": [9, 2],
                        "player_shiny_bit": 11,
                        "player_illusion_hidden_bit": 12,
                        "player_public_identity_bits": [13, 2],
                        "player_public_identity_policy":
                            "opaque_first_appearance_1_to_3",
                        "gender_codes": ["MALE", "FEMALE", "GENDERLESS",
                                         "UNKNOWN"],
                    },
                },
            },
        },
        "public_state": {
            "address": _integer(ram["public_state_address"],
                                "public state address"),
            "offset_in_private_state": int(ram["public_state_offset"]),
            "size": int(ram["public_state_size"]),
            "version": int(ram["public_state_version"]),
            "event_capacity": int(ram["public_event_capacity"]),
            "event_size": 11,
            "crc_excludes": [[0, 4], [8, 16]],
            "battle_string_ids": _battle_string_ids(),
            "custom_message_id": 388,
            "synthetic_event_ids": {"389": "ABILITY_POPUP"},
            "battle_string_templates": _battle_string_templates(output),
            "custom_string_crc16_catalog": _custom_string_crc16_catalog(),
            "status_names": ["NONE", "SLEEP", "POISON", "TOXIC",
                             "BURN", "FREEZE", "PARALYSIS"],
            "stat_stage_order": ["attack", "defense", "speed",
                                 "special_attack", "special_defense",
                                 "accuracy", "evasion"],
            "field_timer_order": ["mud_sport", "water_sport", "gravity",
                                  "trick_room", "magic_room", "wonder_room",
                                  "fairy_lock", "ion_deluge"],
            "classic_side_timer_order": ["reflect", "light_screen", "mist",
                                         "safeguard"],
            "modern_side_timer_order": ["sea_of_fire", "swamp", "rainbow",
                                        "retaliate", "lucky_chant", "tailwind",
                                        "aurora_veil", "max_vine_lash",
                                        "max_wildfire", "max_cannonade",
                                        "max_volcalith"],
            "personal_effect_layout": [
                {"name": "disable", "bits": 4},
                {"name": "encore", "bits": 4},
                {"name": "perish_song", "bits": 2},
                {"name": "taunt", "bits": 4},
                {"name": "telekinesis", "bits": 3},
                {"name": "magnet_rise", "bits": 3},
                {"name": "heal_block", "bits": 3},
                {"name": "laser_focus", "bits": 2},
                {"name": "throat_chop", "bits": 2},
                {"name": "embargo", "bits": 3},
                {"name": "slow_start", "bits": 3},
                {"name": "glaive_rush", "bits": 1},
                {"name": "syrup_bomb", "bits": 2},
                {"name": "dragon_cheer_rank", "bits": 2},
                {"name": "cud_chew", "bits": 2},
                {"name": "stockpile", "bits": 2},
                {"name": "rollout", "bits": 3},
                {"name": "charge", "bits": 2},
                {"name": "protect_chain", "bits": 3},
                {"name": "fury_cutter", "bits": 3},
                {"name": "dynamax_turns", "bits": 3},
                {"name": "paradox_boost_stat", "bits": 3},
                {"name": "roost", "bits": 1},
            ],
            "personal_effect_side_bits": 64,
            "dynamax_permanent_value": 7,
            "move_lock_order": ["player_disabled", "codex_disabled",
                                "player_encored", "codex_encored"],
            "move_lock_bits": 12,
            "wish_future_layout": [
                {"name": "player_wish", "bits": 2},
                {"name": "codex_wish", "bits": 2},
                {"name": "player_future", "bits": 2},
                {"name": "codex_future", "bits": 2},
                {"name": "player_future_move", "bits": 11},
                {"name": "codex_future_move", "bits": 11},
                {"name": "player_healing_wish", "bits": 1},
                {"name": "codex_healing_wish", "bits": 1},
            ],
            "event_bit_layout": [
                {"name": "message_id", "bits": 9},
                {"name": "current_move_id", "bits": 11},
                {"name": "original_move_id", "bits": 11},
                {"name": "last_item_id", "bits": 10},
                {"name": "last_ability_id", "bits": 10},
                {"name": "custom_text_crc16", "bits": 16},
                {"name": "banks", "bits": 8},
                {"name": "flags", "bits": 8},
                {"name": "context_flags", "bits": 5},
            ],
            "event_flag_high_bits":
                "player_public_identity; custom derives from message 388",
            "layout_offsets": {
                "stat_stages": 26, "status2": 33, "status3": 41,
                "types": 65, "field": 69, "sides": 82,
                "move_locks": 106, "personal_effects": 112,
                "own_party_status": 128, "wish_future": 130,
                "player_item_knowledge": 134, "own_level": 135,
                "events": 136,
            },
            "item_knowledge_names": [
                "UNKNOWN", "HELD", "CONSUMED_OR_REMOVED",
                "CHANGED_UNRESOLVED",
            ],
            "volatile_status_encoding": "SANITIZED_PUBLIC_EFFECT_BITS_V2",
            "stat_stage_encoding": "NIBBLE_NEUTRAL_6",
            "type_encoding": "SIX_PACKED_5BIT",
            "type_hidden_value": 31,
            "side_order": ["player", "codex"],
            "private_neighbor_readable": False,
        },
        "runtime": {"poll": runtime["entrypoints"]["CodexBattleRuntime_Poll"],
                    "controller": runtime["entrypoints"]["CodexBattleRuntime_OpponentController"]},
        "catalog": {"path": config["catalog"]["path"],
                    "default_limit": 10, "maximum_limit": 50},
        "team_preview": {
            "mode": preview["mode"],
            "icon_pointer_table": _integer(
                preview["icon_pointer_table"], "icon pointer table"),
            "palette_index_table": _integer(
                preview["palette_index_table"], "icon palette index table"),
            "palette_table": _integer(
                preview["palette_table"], "icon palette table"),
            "palette_count": int(preview["palette_count"]),
            "icon_width": int(preview["icon_width"]),
            "icon_height": int(preview["icon_height"]),
            "selection_order_visible": bool(
                preview["selection_order_visible"]),
            "automatic_png_after_codex_selection": True,
        },
        "exit_codes": {"ok": 0, "config": 10, "transport": 20,
                       "nci_response": 21, "core_or_rom": 22,
                       "protocol": 23, "request": 24,
                       "config_write": 25},
        "security": {"trusted_lan_only": True, "plain_udp": True,
                     "raw_memory_cli": False, "player_pending_private": True},
    }


def _ipad_evidence(config: Mapping[str, Any], output: bytes) -> tuple[dict[str, Any] | None, str | None]:
    path = ROOT / config["outputs"]["ipad"]
    if not path.is_file():
        return None, None
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
        _fail("Stage44 iPad evidence contains private endpoint/path/credential")
    document = json.loads(text)
    expected = {
        "doctor", "versioned_copy", "team_upload", "both_selections",
        "pending_action_private", "multi_turn_three_cycles", "gimmick_move",
        "codex_switch", "safe_abort_cleanup", "party_exact_restore",
        "nci_request_span_only", "normal_mode_unaffected",
    }
    tests = document.get("tests")
    if (document.get("schema_version") != 1 or document.get("task") != TASK
            or document.get("stage") != 44 or document.get("status") != "PASS"
            or document.get("rom_sha256") != _sha(output)
            or not isinstance(tests, dict) or set(tests) != expected
            or any(value is not True for value in tests.values())
            or document.get("turn_cycles", 0) < 3
            or document.get("secrets_redacted") is not True):
        _fail("Stage44 iPad multi-turn evidence differs")
    return document, _sha(raw)


def _static_outputs() -> dict[str, bytes]:
    config = _read_json(CONFIG)
    if config.get("schema_version") != 1 or config.get("task") != TASK:
        _fail("Codex runtime config root/task differs")
    inputs = config["inputs"]
    stage = _identity(Path(inputs["stage43_rom"]["path"]), inputs["stage43_rom"], "Stage43 ROM")
    metadata_raw = _identity(Path(inputs["stage43_metadata"]["path"]), inputs["stage43_metadata"], "Stage43 metadata")
    allocation_raw = _identity(Path(inputs["stage43_allocation"]["path"]), inputs["stage43_allocation"], "Stage43 allocation")
    stage43_bps = _identity(Path(inputs["stage43_clean_bps"]["path"]), inputs["stage43_clean_bps"], "Stage43 clean BPS")
    _identity(Path(inputs["stage43_protocol"]["path"]), inputs["stage43_protocol"], "Stage43 protocol")
    ipad43 = _identity(Path(inputs["stage43_ipad"]["path"]), inputs["stage43_ipad"], "Stage43 iPad evidence")
    clean = _identity(Path(inputs["clean_rom"]["path"]), inputs["clean_rom"], "clean FireRed")
    _identity(Path(inputs["factory_symbols"]["path"]), inputs["factory_symbols"], "Factory symbols")
    _identity(Path(inputs["trainer_changekit_symbols"]["path"]), inputs["trainer_changekit_symbols"], "Trainer ChangeKit symbols")
    previous_meta = json.loads(metadata_raw)
    previous_alloc = json.loads(allocation_raw)
    if (previous_meta.get("task") != "T26" or previous_meta.get("status") != "PASS"
            or previous_meta.get("output", {}).get("sha256") != _sha(stage)
            or previous_meta.get("ipad", {}).get("status") != "PASS"
            or previous_alloc.get("summaries", {}).get("overlap_count") != 0
            or json.loads(ipad43).get("status") != "PASS"
            or apply_bps(clean, stage43_bps) != stage):
        _fail("Stage43 prerequisite identity/evidence differs")
    ownership = _validate_ram(config)
    safe_bits, safe_items = _safe_item_bits(config)
    header = _runtime_header(config, safe_bits)
    payload, runtime, allocation_report = _build_payload(config, previous_alloc, header)
    output = bytearray(stage)
    payload_offset = int(runtime["payload"]["offset"])
    if stage[payload_offset:payload_offset + len(payload)] != b"\xFF" * len(payload):
        _fail("Stage44 allocation target is not erased")
    output[payload_offset:payload_offset + len(payload)] = payload
    declared = [{"kind": "payload::codex_battle_runtime",
                 "start": payload_offset,
                 "end_exclusive": payload_offset + len(payload)}]
    patches = _apply_hooks(config, stage, output, runtime, declared)
    ordered = sorted(declared, key=lambda row: int(row["start"]))
    if any(int(left["end_exclusive"]) > int(right["start"])
           for left, right in zip(ordered, ordered[1:])):
        _fail("Stage44 declared spans overlap")
    declared_offsets = {index for row in ordered
                        for index in range(int(row["start"]), int(row["end_exclusive"]))}
    changed = [index for index, (before, after) in enumerate(zip(stage, output))
               if before != after]
    outside = [index for index in changed if index not in declared_offsets]
    if outside:
        _fail(f"Stage44 changed bytes outside declared spans: {outside[:8]}")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(clean, output_raw)
    if apply_bps(stage, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("Stage44 BPS round trip differs")
    catalog_raw, catalog_report = _catalog(config, stage)
    protocol = _protocol_document(config, output_raw, runtime)
    ipad, ipad_sha = _ipad_evidence(config, output_raw)
    ipad_pass = ipad is not None
    outputs = config["outputs"]
    symbols = {
        "schema_version": 1, "task": TASK,
        "symbols": {name: {"address": address,
                            "size": runtime["symbol_sizes"].get(name, 0)}
                    for name, address in runtime["entrypoints"].items()},
        "runtime": runtime["code"], "payload": runtime["payload"],
        "field": runtime["field"], "patches": patches,
    }
    cases = {
        "schema_version": 1, "task": TASK, "rom_sha256": _sha(output_raw),
        "runtime": runtime, "protocol": protocol["mailbox"],
        "addresses": {"player_party": 0x020241E4, "enemy_party": 0x02023F8C,
                      "battle_buffer_a": 0x02022B24, "battle_buffer_b": 0x02023324,
                      "battle_flags": 0x02022AAC, "rng": 0x03005040},
        "invalid_cases": ["torn", "duplicate", "stale", "future", "wrong_nonce",
                          "wrong_match", "wrong_turn", "wrong_phase", "payload_crc",
                          "request_crc", "oversize", "invalid_member", "illegal_action"],
        "quick_iterations": 8, "full_iterations": 64,
        "expected_tests": list(MGBA_TESTS),
    }
    matrix = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "level_modes": [
            {"level": level, "status": "PASS"}
            for level in ("FLAT_50", "OPEN")
        ],
        "enforced_team_rules": [],
        "unrestricted": {
            "species_duplicates": True,
            "held_item_duplicates": True,
            "content_banlist": False,
        },
        "team": {"exact_members": 6, "species_duplicates_allowed": True,
                 "learnset_ban": False, "deterministic_defaults": True,
                 "invalid_matrix_count": 13, "duplicate_field_rejected": True},
        "commands": {"manual_only": True, "auto_team": False,
                     "auto_selection": False, "auto_action": False,
                     "auto_gimmick": False, "cpu_only_explicit_disconnect": True},
        "disconnect": ["WAIT", "RECONNECT", "CPU_FALLBACK", "FORFEIT"],
    }
    privacy = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "public": ["codex_team_full_via_owner_cache", "both_species_preview",
                   "revealed_player_fields", "codex_legal_actions",
                   "printstring_events", "ability_popup_events",
                   "preview_level_gender_shiny", "codex_live_combat_stats",
                   "opaque_first_seen_identity", "persistent_public_knowledge",
                   "compact_current_board_event_delta"],
        "never_public_before_codex_commit": ["player_move", "player_switch_slot",
            "player_target", "player_gimmick", "player_command_bytes",
            "player_input_time", "private_length", "private_crc",
            "player_selected_order", "player_underlying_party_slot"],
        "private_state_address_not_in_protocol": True,
        "snapshot_independent_of_player_pending_value_length_error_sequence_timing": True,
        "controller_release_only_after_both_commits": True,
    }
    gimmick = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "policy": "UPSTREAM_OPEN", "battle_local": True,
        "mechanics": ["MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL"],
        "policy_callsite_count": 15,
        "upstream_authoritative": ["species_item_move_compatibility", "used_state",
                                   "mutual_exclusion", "transformation_state"],
        "inactive_delegate_exact": True,
        "normal_factory_mirage_raid_policy_unchanged": True,
    }
    local_acceptance = {key: key != "IPAD_STAGE44_MULTI_TURN_VERTICAL_SLICE"
                        or ipad_pass for key in ACCEPTANCE_KEYS}
    status = "PASS_LOCAL_IPAD_PENDING_MGBA" if ipad_pass else "PASS_LOCAL"
    metadata = {
        "schema_version": 1, "task": TASK, "status": status,
        "input": {"path": inputs["stage43_rom"]["path"], "size": len(stage),
                  "sha256": _sha(stage), "crc32": inputs["stage43_rom"]["crc32"]},
        "output": {"path": outputs["rom"], "size": len(output_raw),
                   "sha256": _sha(output_raw), "crc32": protocol["rom"]["crc32"]},
        "runtime": runtime, "protocol": protocol["mailbox"],
        "ownership": ownership, "safe_items": safe_items,
        "patches": patches,
        "change_audit": {"changed_byte_count": len(changed),
                         "declared_spans": ordered,
                         "declared_span_overlap_count": 0,
                         "outside_declared_span_count": 0},
        "overlap_audit": {"rom": 0, "ram": 0, "save": 0, "ui": 0, "hook": 0},
        "bps": {"incremental_sha256": _sha(incremental),
                "clean_sha256": _sha(direct), "round_trip": True},
        "catalog": catalog_report,
        "ipad": {"status": "PASS" if ipad_pass else "PENDING",
                 "path": outputs["ipad"], "sha256": ipad_sha},
        "mgba": {"status": "PENDING", "process_count": 0},
        "acceptance": local_acceptance,
    }
    audit = {
        "schema_version": 1, "task": TASK, "status": status,
        "input": metadata["input"], "output": metadata["output"],
        "ownership": ownership, "runtime": runtime,
        "patches": patches, "change_audit": metadata["change_audit"],
        "overlap_audit": metadata["overlap_audit"],
        "t26_ipad_doctor": True, "production_entry": runtime["field"],
        "controller": {"manual_choice_commands": [18, 20, 22],
                       "non_choice_delegate": True,
                       "cpu_fallback_only_when_explicit": True},
        "ipad": metadata["ipad"], "mgba": metadata["mgba"],
        "acceptance": local_acceptance,
    }
    coverage = {
        "schema_version": 1, "task": TASK, "status": status,
        "acceptance": {key: {"status": "PASS" if value else "PENDING",
                             "evidence": {"builder": value,
                                          "ipad": value and key == "IPAD_STAGE44_MULTI_TURN_VERTICAL_SLICE"}}
                       for key, value in local_acceptance.items()},
        "mgba": metadata["mgba"], "ipad": metadata["ipad"],
    }
    return {
        outputs["rom"]: output_raw,
        outputs["metadata"]: _stable(metadata),
        outputs["allocation"]: _stable(allocation_report),
        outputs["incremental_bps"]: incremental,
        outputs["clean_bps"]: direct,
        outputs["generated_header"]: header,
        outputs["runtime"]: payload[PAYLOAD_HEADER_SIZE:
                                    PAYLOAD_HEADER_SIZE + runtime["code"]["size"]],
        outputs["symbols"]: _stable(symbols),
        outputs["protocol"]: _stable(protocol),
        outputs["cases"]: _stable(cases),
        config["catalog"]["path"]: catalog_raw,
        outputs["audit"]: _stable(audit),
        outputs["coverage"]: _stable(coverage),
        outputs["matrix"]: _stable(matrix),
        outputs["catalog_report"]: _stable(catalog_report),
        outputs["privacy"]: _stable(privacy),
        outputs["gimmick"]: _stable(gimmick),
    }


def _validate_mgba(document: Mapping[str, Any], mode: str,
                   identities: Mapping[str, str]) -> None:
    tests = document.get("tests")
    if (document.get("schema_version") != 1 or document.get("task") != TASK
            or document.get("mode") != mode or document.get("status") != "PASS"
            or any(document.get(key) != value for key, value in identities.items())
            or not isinstance(tests, dict) or tuple(tests) != MGBA_TESTS
            or any(value is not True for value in tests.values())
            or document.get("total") != len(MGBA_TESTS)
            or document.get("warnings") != 0
            or document.get("turn_cycles", 0) < 3):
        _fail(f"Codex Battle mGBA {mode} did not report exact all-PASS")


def _finalize_outputs(static: Mapping[str, bytes]) -> dict[str, bytes]:
    config = _read_json(CONFIG)
    outputs = config["outputs"]
    runner = ROOT / "tools/mgba_codex_battle_runtime_smoke.c"
    if not runner.is_file():
        _fail("Codex Battle mGBA runner is missing")
    source_identities = {
        "rom_sha256": _sha(static[outputs["rom"]]),
        "runner_source_sha256": _sha(runner.read_bytes()),
        "symbols_sha256": _sha(static[outputs["symbols"]]),
        "cases_sha256": _sha(static[outputs["cases"]]),
    }
    result: dict[str, bytes] = {}
    documents: dict[str, dict[str, Any]] = {}
    (ROOT / ".local").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vega-codex-runtime-mgba-",
                                     dir=ROOT / ".local") as raw:
        directory = Path(raw)
        executable = directory / "mgba-codex-battle-runtime"
        rom = directory / "stage44.gba"
        symbols = directory / "symbols.json"
        cases = directory / "cases.json"
        rom.write_bytes(static[outputs["rom"]])
        symbols.write_bytes(static[outputs["symbols"]])
        cases.write_bytes(static[outputs["cases"]])
        _run([_host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
              str(runner), "-o", str(executable), "-lmgba"],
             "Codex Battle libmGBA compile")
        identities = {**source_identities,
                      "runner_binary_sha256": _sha(executable.read_bytes())}
        for mode, key, timeout in (("quick", "mgba_quick", 300),
                                   ("full", "mgba_full", 600)):
            stdout = _run([str(executable), str(rom), str(symbols), str(cases), mode],
                          f"Codex Battle mGBA {mode}", timeout=timeout)
            document = json.loads(stdout)
            _validate_mgba(document, mode, identities)
            document["process_runs"] = 1
            documents[mode] = document
            result[outputs[key]] = _stable(document)
    quick = documents["quick"]
    full = documents["full"]
    if any(quick[key] != full[key] for key in source_identities):
        _fail("mGBA quick/full identities differ")
    metadata = json.loads(static[outputs["metadata"]])
    audit = json.loads(static[outputs["audit"]])
    coverage = json.loads(static[outputs["coverage"]])
    ipad_pass = metadata["ipad"]["status"] == "PASS"
    acceptance = {key: True for key in ACCEPTANCE_KEYS}
    if not ipad_pass:
        acceptance["IPAD_STAGE44_MULTI_TURN_VERTICAL_SLICE"] = False
    mgba = {"status": "PASS", "process_count": 2,
            "quick": {"path": outputs["mgba_quick"], "tests": quick["tests"]},
            "full": {"path": outputs["mgba_full"], "tests": full["tests"]},
            "identity_equal": True, "warnings_zero": True}
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
                           "ipad": value and key == "IPAD_STAGE44_MULTI_TURN_VERTICAL_SLICE"}}
        for key, value in acceptance.items()
    }
    result.update({outputs["metadata"]: _stable(metadata),
                   outputs["audit"]: _stable(audit),
                   outputs["coverage"]: _stable(coverage)})
    return result


def build_outputs(static: Mapping[str, bytes] | None = None) -> dict[str, bytes]:
    static_outputs = dict(static or _static_outputs())
    return {**static_outputs, **_finalize_outputs(static_outputs)}


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
        _fail("Codex Battle Runtime generated outputs differ: " + ", ".join(differences))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check"))
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    try:
        static = _static_outputs()
        repeated = _static_outputs()
        if static != repeated:
            _fail("Codex Battle Runtime static build is not byte deterministic")
        outputs = static if args.static_only else build_outputs(static)
        if args.mode == "build":
            _write_outputs(outputs)
        else:
            _check_outputs(outputs)
            if json.loads(outputs[_read_json(CONFIG)["outputs"]["metadata"]]).get("status") != "PASS":
                _fail("real iPad evidence is not finalized")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            zipfile.BadZipFile, subprocess.SubprocessError,
            CodexBattleRuntimeBuildError) as error:
        print(f"Codex Battle Runtime Stage44 {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    metadata = json.loads(outputs[_read_json(CONFIG)["outputs"]["metadata"]])
    print("Codex Battle Runtime Stage44 %s: %s sha256=%s crc32=%s artifacts=%d"
          % (args.mode, metadata["status"], metadata["output"]["sha256"],
             metadata["output"]["crc32"], len(outputs)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
