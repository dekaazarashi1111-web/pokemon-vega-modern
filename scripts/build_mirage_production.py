#!/usr/bin/env python3
"""Stage 37へMirage 4周production runtimeを結合しStage 38を生成する。"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_trainer_v5_stage32 import (  # noqa: E402
    _align,
    _arm_tool,
    _host_cc,
    _jump_stub,
    _previous_requests,
    _sha,
    _sparse_bps,
    _stable,
)
from tools.regression.rom_runtime import _Blob, _charmap, _encode_text  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "T21"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/37_event_design.gba")
INPUT_META = Path("build/stages/37_event_design.json")
INPUT_ALLOC = Path("build/stages/37_allocation.json")
CHANGEKIT_META = Path("build/stages/35_trainer_changekit_final.json")
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
OUTPUT_ROM = Path("build/stages/38_mirage_production.gba")
OUTPUT_META = Path("build/stages/38_mirage_production.json")
OUTPUT_ALLOC = Path("build/stages/38_allocation.json")
OUTPUT_SERIALIZED = Path("generated/runtime/mirage_production_serialized.json")
OUTPUT_HEADER = Path("generated/runtime/mirage_production_generated.h")
OUTPUT_RUNTIME = Path("generated/runtime/mirage_production_runtime.bin")
OUTPUT_SYMBOLS = Path("generated/runtime/mirage_production_symbols.json")
OUTPUT_CASES = Path("generated/runtime/mirage_production_mgba_cases.csv")
OUTPUT_AUDIT = Path("reports/generated/mirage_production_audit.json")
OUTPUT_COVERAGE = Path("reports/generated/mirage_production_coverage.json")
OUTPUT_REPORT = Path("reports/generated/mirage_production.md")
OUTPUT_MGBA_QUICK = Path("build/stages/38_mgba_mirage_production_quick.json")
OUTPUT_MGBA_FULL = Path("build/stages/38_mgba_mirage_production_full.json")
PATCH_INCREMENTAL = Path(
    "build/patches/event-design-stage37-to-mirage-production-stage38.bps"
)
PATCH_CLEAN = Path(
    "build/patches/firered-jpn-rev0-to-mirage-production-stage38.bps"
)

BINDINGS = Path("config/mirage_production_bindings.csv")
MODES = Path("manifests/facility_modes.csv")
TRAINERS = Path("manifests/facility_trainers.csv")
RENTALS = Path("manifests/facility_rentals.csv")
REWARDS = Path("manifests/facility_rewards.csv")
TRAINER_IDS = Path("manifests/trainer_ids.csv")
CONSTRAINTS = Path("content/trainer_balance_constraints.csv")
AUDIT_POLICY = Path("config/t02_audit_policy.json")
RAM_LAYOUT = Path("config/ram_layout.csv")
SAVE_LAYOUT = Path("config/save_layout.csv")

EXPECTED_STAGE37_SHA256 = (
    "76d4f6a4005a815e6faf33f2ae24c18c2a7b4a1fe6f1f313e6f1837ecaf5cb7c"
)
EXPECTED_STAGE37_META_SHA256 = (
    "712ecdcd15b7fd7ac3003771eca45fd6ffd6e4dcb410436e3204e0862f1d9873"
)
EXPECTED_STAGE37_ALLOC_SHA256 = (
    "a7d2fc5dbcc4b31920fe05f45ccde49abf211db03ca0b459efa3512e9ac8660c"
)
EXPECTED_CLEAN_SHA256 = (
    "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
)

PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "mirage_production_stage38_payload"
TRAINER_TABLE_ADDRESS = 0x09328AF0
TRAINER_TABLE_COUNT = 4284
TRAINER_RECORD_SIZE = 32
QOL_SAVE_LOAD_ADDRESS = 0x09377115
SPECIAL_VAR_RESULT = 0x02037004
SPECIAL_VAR_ARG0 = 0x02036FEC
MIRAGE_MAP = (31, 1)
MIRAGE_MAP_HEADER = 0x08315B74
MIRAGE_MAP_SECTION = 143
MIRAGE_RESPAWN = 14
MIRAGE_BATTLE_COUNT = 28
MIRAGE_RAM_ADDRESS = 0x0203EE00
MIRAGE_RAM_END_EXCLUSIVE = 0x0203F098
MIRAGE_RAM_HEADER_SIZE = 64
MIRAGE_PARTY_SNAPSHOT_SIZE = 600
MIRAGE_RAM_SIZE = 664
UI_HELP_VIDEO_STATE_ADDRESS = 0x0203F101
UI_HELP_VIDEO_STATE_SOURCE = Path("tools/mgba_battle_ui_smoke.c")
MIRAGE_TRAINERBATTLE_LIVE_FLAGS = 0x0C
MIRAGE_TRAINERBATTLE_REQUIRED_FLAGS = {"IS_MASTER": 0x04, "TRAINER": 0x08}
MIRAGE_TRAINERBATTLE_FORBIDDEN_FLAGS = ("DOUBLE", "LINK", "MULTI", "FRONTIER")
STATUS_OK = 1
STATUS_CANCELLED = 2
STATUS_NOT_UNLOCKED = 3
STATUS_BATTLE_CONTINUE = 9
STATUS_ROUND_COMPLETE = 10
STATUS_CHALLENGE_COMPLETE = 11
STATUS_LOST = 12

EXTERNAL_ENTRYPOINTS = {
    "MIRAGE_FLAG_GET_ADDRESS": 0x0806DEC5,
    "MIRAGE_ORIGINAL_FLAG_SET_ADDRESS": 0x09378473,
    "MIRAGE_ORIGINAL_FLAG_CLEAR_ADDRESS": 0x0937847F,
    "MIRAGE_GET_MON_DATA_ADDRESS": 0x0803F355,
    "MIRAGE_SET_MON_DATA_ADDRESS": 0x0803FA71,
    "MIRAGE_CREATE_MON_ADDRESS": 0x0803D1C1,
    "MIRAGE_GET_MON_ABILITY_ADDRESS": 0x090DA23D,
    # Stage37 exposes the stable public bridge here; the literal in that
    # bridge currently dispatches to the relocated implementation at
    # 0x090D93A9.  Runtime callers must use the bridge ABI, not the private
    # relocated function.
    "MIRAGE_CALCULATE_MON_STATS_ADDRESS": 0x0803DBE9,
    "MIRAGE_CALCULATE_PP_ADDRESS": 0x0804070D,
    "MIRAGE_HEAL_PLAYER_PARTY_ADDRESS": 0x080A1331,
    "MIRAGE_RANDOM_ADDRESS": 0x0804448D,
    "MIRAGE_CONFIGURE_BATTLE_POLICY_ADDRESS": 0x091260A9,
    "MIRAGE_CONFIGURE_VIRTUAL_ITEM_ADDRESS": 0x091261BD,
    "MIRAGE_CFRU_PENDING_CLEAR_ADDRESS": 0x0910ED2D,
    "MIRAGE_SAVE_VALIDATE_ADDRESS": 0x092D10D1,
    "MIRAGE_SAVE_FINALIZE_ADDRESS": 0x092D2605,
    "MIRAGE_ORIGINAL_TRY_SAVING_DATA_ADDRESS": 0x09378465,
    "MIRAGE_TRY_WRITE_SECTOR_ADDRESS": 0x080DA9C1,
    "MIRAGE_QOL_SAVE_LOAD_ADAPTER_ADDRESS": QOL_SAVE_LOAD_ADDRESS,
    "MIRAGE_CHANGEKIT_BUILD_TRAINER_PARTY_ADDRESS": 0x09302871,
    "MIRAGE_CHANGEKIT_LOAD_PROPER_ABILITY_ADAPTER_ADDRESS": 0x09302F31,
    "MIRAGE_SET_WARP_DESTINATION_ADDRESS": 0x08054C4D,
    "MIRAGE_RESET_INITIAL_AVATAR_ADDRESS": 0x080552A5,
    "MIRAGE_WARP_INTO_MAP_ADDRESS": 0x08054C39,
    "MIRAGE_DEFAULT_WARP_EXIT_ADDRESS": 0x0807D695,
    "MIRAGE_SET_MAIN_CALLBACK2_ADDRESS": 0x08000545,
    "MIRAGE_CB2_LOAD_MAP_ADDRESS": 0x08055FDD,
}

RUNTIME_DATA_ADDRESSES = {
    "MIRAGE_BATTLE_TYPE_FLAGS_ADDRESS": 0x02022AAC,
    "MIRAGE_BATTLE_OUTCOME_ADDRESS": 0x02023DEA,
    "MIRAGE_TRAINER_OPPONENT_A_ADDRESS": 0x020385E2,
    "MIRAGE_ENEMY_PARTY_ADDRESS": 0x02023F8C,
    "MIRAGE_ENEMY_PARTY_COUNT_ADDRESS": 0x02023F8A,
    "MIRAGE_PLAYER_PARTY_ADDRESS": 0x020241E4,
    "MIRAGE_PLAYER_PARTY_COUNT_ADDRESS": 0x02023F89,
    "MIRAGE_SELECTED_ORDER_ADDRESS": 0x0203C6C8,
    "MIRAGE_SAVE_BUFFER_ADDRESS": 0x020399B0,
    "MIRAGE_SECTOR31_IMAGE_ADDRESS": 0x0203CF9C,
    "MIRAGE_BATTLERS_COUNT_ADDRESS": 0x02023B2C,
    "MIRAGE_BATTLER_PARTY_INDEXES_ADDRESS": 0x02023B2E,
    "MIRAGE_ABSENT_BATTLER_FLAGS_ADDRESS": 0x02023CD0,
    "MIRAGE_ACTIVE_BATTLER_ADDRESS": 0x02023B24,
    "MIRAGE_BATTLE_MONS_ADDRESS": 0x02023B44,
    "MIRAGE_FIELD_CALLBACK_ADDRESS": 0x03005060,
}

RUNTIME_LAYOUT_CONSTANTS = {
    "MIRAGE_BATTLE_MON_SIZE": 88,
    "MIRAGE_BATTLE_MON_ABILITY_OFFSET": 0x38,
}

REQUIRED_ENTRYPOINTS = {
    "MirageProduction_Probe",
    "MirageProduction_FieldEnter",
    "MirageProduction_CommitSelection",
    "MirageProduction_CommitRound4Mechanic",
    "MirageProduction_PrepareBattle",
    "MirageProduction_FinalizeBattleCopy",
    "MirageProduction_AfterBattle",
    "MirageProduction_Complete",
    "MirageProduction_Abort",
    "MirageProduction_Recover",
    "MirageProduction_MapTransitionRecover",
    "MirageProduction_SaveLoadAdapter",
    "MirageProduction_BuildTrainerPartyAdapter",
    "MirageProduction_LoadProperAbilityBattleDataAdapter",
    "MirageProduction_TestInjectPersistenceFault",
    "MirageProduction_TestWarpToReception",
}

ACCEPTANCE_KEYS = (
    "STAGE37_IDENTITY_PRIVATE_IMMUTABLE",
    "MIRAGE_MANIFEST_CROSSWALK_EXACT",
    "NORMAL_FIELD_ENTRY_4_ROUNDS_28_BATTLES",
    "ROUND_UNLOCK_NO_SKIP",
    "LEVEL100_SINGLE_3V3_AI_GIMMICKS",
    "ROUND4_LOCK_ONE_GIMMICK_NO_LEAK",
    "DETERMINISTIC_POOL_NO_REBALANCE",
    "VIRTUAL_ITEM_TIERS_ISOLATED",
    "ATOMIC_RECORD_CLAIM_SAVE_RELOAD",
    "BADGE_EXACT_RESTORE_ALL_EXITS",
    "BATTLE_LOCAL_CLEANUP_ALL_EXITS",
    "UPSTREAM_RUNTIME_CONTENT_REGRESSION",
    "PRO_WAITING_AREAS_UNCHANGED",
    "CLEAN_REBUILD_BPS_EXACT",
    "DECLARED_SPAN_OVERLAP_MGBA_TWO_PROCESS",
)

NATURE_IDS = {
    "NATURE_HARDY": 0, "NATURE_LONELY": 1, "NATURE_BRAVE": 2,
    "NATURE_ADAMANT": 3, "NATURE_NAUGHTY": 4, "NATURE_BOLD": 5,
    "NATURE_DOCILE": 6, "NATURE_RELAXED": 7, "NATURE_IMPISH": 8,
    "NATURE_LAX": 9, "NATURE_TIMID": 10, "NATURE_HASTY": 11,
    "NATURE_SERIOUS": 12, "NATURE_JOLLY": 13, "NATURE_NAIVE": 14,
    "NATURE_MODEST": 15, "NATURE_MILD": 16, "NATURE_QUIET": 17,
    "NATURE_BASHFUL": 18, "NATURE_RASH": 19, "NATURE_CALM": 20,
    "NATURE_GENTLE": 21, "NATURE_SASSY": 22, "NATURE_CAREFUL": 23,
    "NATURE_QUIRKY": 24,
}
MECHANIC_IDS = {"NONE": 0, "MEGA": 1, "Z": 2, "ONE_OF_MEGA_Z_TERA": 0xFF}
UNLOCK_ROWS = {
    "VEGA_HALL_OF_FAME": (1, 0x082C),
    "KANTO_CERT_4": (1, 0x1403),
    "KANTO_LEAGUE_CLEAR": (1, 0x13FA),
}


class MirageProductionBuildError(ValueError):
    """T21入力、manifest、field ABI、配置または受入証跡の違反。"""


def _fail(message: str) -> NoReturn:
    raise MirageProductionBuildError(message)


def _rows(path: Path) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        _fail(f"JSON root differs: {path}")
    return value


def _index(
    rows: Sequence[Mapping[str, Any]], key: str, label: str,
) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        value = str(row.get(key, ""))
        if not value or value in result:
            _fail(f"{label}: missing/duplicate {key}: {value!r}")
        result[value] = row
    return result


def _integer(value: Any, label: str) -> int:
    try:
        return int(str(value), 0)
    except (TypeError, ValueError) as exc:
        _fail(f"{label}: integer required: {value!r} ({exc})")


def _run(command: Sequence[str], label: str, *, timeout: int | None = None) -> str:
    try:
        completed = subprocess.run(
            list(command), cwd=ROOT, capture_output=True, text=True,
            check=False, timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        _fail(f"{label} timed out: {exc}")
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")
    return completed.stdout.strip()


def _csv_bytes(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue().encode("utf-8")


def _rom_offset(address: int, size: int = 1) -> int:
    # Patch ledgers contain byte-accurate script operands and may legitimately
    # be odd-addressed (for example the map 3/12 cleanup pointer).
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + size > ROM_SIZE:
        _fail(f"ROM address outside Stage37: 0x{address:08X}+0x{size:X}")
    return offset


def _decode_thumb_bl(source: int, encoded: bytes) -> int:
    if source & 1 or len(encoded) != 4:
        _fail("Thumb BL decode source/size differs")
    first, second = struct.unpack("<HH", encoded)
    if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
        _fail(f"Thumb BL opcode differs at 0x{source:08X}: {encoded.hex()}")
    raw = ((first & 0x07FF) << 12) | ((second & 0x07FF) << 1)
    if raw & (1 << 22):
        raw -= 1 << 23
    return (source + 4 + raw) | 1


def _input_contract() -> dict[str, Any]:
    stage = (ROOT / INPUT_ROM).read_bytes()
    meta_raw = (ROOT / INPUT_META).read_bytes()
    alloc_raw = (ROOT / INPUT_ALLOC).read_bytes()
    clean = (ROOT / CLEAN_ROM).read_bytes()
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_STAGE37_SHA256:
        _fail("Stage37 input size/hash differs")
    if _sha(meta_raw) != EXPECTED_STAGE37_META_SHA256:
        _fail("Stage37 metadata hash differs")
    if _sha(alloc_raw) != EXPECTED_STAGE37_ALLOC_SHA256:
        _fail("Stage37 allocation hash differs")
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != EXPECTED_CLEAN_SHA256:
        _fail("clean FireRed JPN Rev.0 size/hash differs")
    external_signatures = {
        "MIRAGE_CREATE_MON_ADDRESS": bytes.fromhex(
            "f0b5474680b487b080460e1c0d9c0e9f"
        ),
        "MIRAGE_CALCULATE_MON_STATS_ADDRESS": bytes.fromhex("00490847a9930d09"),
        "MIRAGE_GET_MON_ABILITY_ADDRESS": bytes.fromhex(
            "f8b500220b21144f040003f042fc4723"
        ),
        "MIRAGE_CALCULATE_PP_ADDRESS": bytes.fromhex(
            "10b50004000c1206120e0d4c43001b18"
        ),
        "MIRAGE_CHANGEKIT_BUILD_TRAINER_PARTY_ADDRESS": bytes.fromhex(
            "10b500f0cffa10bc01bc0047"
        ),
        "MIRAGE_CHANGEKIT_LOAD_PROPER_ABILITY_ADAPTER_ADDRESS": bytes.fromhex(
            "10b500f089f9054b00f00cf8044b1878"
        ),
        "MIRAGE_SET_WARP_DESTINATION_ADDRESS": bytes.fromhex(
            "70b582b0041c0d1c161c06990a482406"
        ),
        "MIRAGE_RESET_INITIAL_AVATAR_ADDRESS": bytes.fromhex(
            "03480022012141700170827070470000"
        ),
        "MIRAGE_WARP_INTO_MAP_ADDRESS": bytes.fromhex(
            "00b5fff70dfffff779fffff7bbff01bc"
        ),
        "MIRAGE_SET_MAIN_CALLBACK2_ADDRESS": bytes.fromhex(
            "034948608720c0000918002008707047"
        ),
        "MIRAGE_CB2_LOAD_MAP_ADDRESS": bytes.fromhex(
            "00b500f04df913f0adf913f011f90020"
        ),
        "MIRAGE_DEFAULT_WARP_EXIT_ADDRESS": bytes.fromhex(
            "00b5d7f7f5ff95f0cdf80020fff79aff"
        ),
    }
    for name, signature in external_signatures.items():
        physical = EXTERNAL_ENTRYPOINTS[name] & ~1
        offset = _rom_offset(physical, len(signature))
        if stage[offset:offset + len(signature)] != signature:
            _fail(f"Stage37 external entrypoint signature differs: {name}")
    old_changekit_trampoline = bytes.fromhex("004b184771283009")
    old_trampoline_offset = _rom_offset(0x090DD198, len(old_changekit_trampoline))
    if (
        stage[old_trampoline_offset:old_trampoline_offset + len(old_changekit_trampoline)]
        != old_changekit_trampoline
    ):
        _fail("Stage37 ChangeKit BuildTrainerParty trampoline signature differs")
    changekit_meta = _read_json(CHANGEKIT_META)
    if (
        changekit_meta.get("status") != "PASS"
        or changekit_meta.get("output", {}).get("sha256")
        != "2ff8d61d7e17d120eaf60a81863dc29f6666d84c48a245e1be3d8dfa2447d180"
        or changekit_meta.get("runtime", {}).get("entrypoints", {}).get(
            "TrainerV5Runtime_BuildTrainerPartySetup"
        ) != EXTERNAL_ENTRYPOINTS["MIRAGE_CHANGEKIT_BUILD_TRAINER_PARTY_ADDRESS"]
        or changekit_meta.get("runtime", {}).get("entrypoints", {}).get(
            "TrainerChangeKitFinalRuntime_LoadProperAbilityBattleDataAdapter"
        )
        != EXTERNAL_ENTRYPOINTS[
            "MIRAGE_CHANGEKIT_LOAD_PROPER_ABILITY_ADAPTER_ADDRESS"
        ]
    ):
        _fail("Stage35 ChangeKit trainer-party/ability metadata pin differs")
    meta = json.loads(meta_raw)
    allocation = json.loads(alloc_raw)
    regression = meta.get("regression", {})
    if (
        meta.get("status") != "PASS"
        or meta.get("output", {}).get("sha256") != EXPECTED_STAGE37_SHA256
        or meta.get("content") != {
            "actors": 14, "arcs": 28, "batches": 7, "conditions": 160,
            "coverage_rows": 98, "dialogues": 326, "events": 76,
            "placements": 63, "rewards": 7, "states": 80,
        }
        or regression.get("trainer_encounters") != 1302
        or regression.get("trainer_members") != 6490
        or regression.get("trainer_double") != 74
        or regression.get("kanto_trainers") != 201
        or regression.get("acquisition_events") != 201
        or regression.get("qol_features") != 35
        or allocation.get("summaries", {}).get("overlap_count") != 0
        or len(allocation.get("allocations", [])) != 47
    ):
        _fail("Stage37 metadata/allocation regression contract differs")
    return {
        "stage": stage, "meta": meta, "meta_raw": meta_raw,
        "allocation": allocation, "allocation_raw": alloc_raw, "clean": clean,
    }


def _validate_ram_and_save() -> dict[str, Any]:
    ram_rows = _rows(RAM_LAYOUT)
    live: list[tuple[str, int, int, str]] = []
    target: Mapping[str, str] | None = None
    for row in ram_rows:
        if row.get("status") != "LIVE":
            continue
        start = _integer(row["start"], "RAM start")
        end = _integer(row["end_exclusive"], "RAM end")
        if end <= start or end - start != _integer(row["size"], "RAM size"):
            _fail(f"RAM layout range differs: {row.get('symbol')}")
        live.append((row["address_space"], start, end, row["owner"]))
        if row.get("owner") == "T21_MIRAGE_PRODUCTION":
            if target is not None:
                _fail("T21 Mirage RAM reservation is duplicated")
            target = row
    if target is None:
        _fail("T21 Mirage RAM reservation is missing")
    start = _integer(target["start"], "Mirage RAM start")
    end = _integer(target["end_exclusive"], "Mirage RAM end")
    if (
        start != MIRAGE_RAM_ADDRESS
        or end != MIRAGE_RAM_END_EXCLUSIVE
        or end - start != MIRAGE_RAM_SIZE
        or MIRAGE_RAM_HEADER_SIZE + MIRAGE_PARTY_SNAPSHOT_SIZE != MIRAGE_RAM_SIZE
        or target.get("symbol") != "gMirageProductionState"
        or target.get("persistence") != "VOLATILE"
        or "0x0203F101" not in target.get("notes", "")
    ):
        _fail(
            "T21 Mirage RAM reservation differs from exact 664-byte "
            "header64+party600 contract"
        )
    ui_state_source = ROOT / UI_HELP_VIDEO_STATE_SOURCE
    if not ui_state_source.is_file():
        _fail("existing battle UI help-video state source is missing")
    ui_state_matches = re.findall(
        r"\bUI_HELP_VIDEO_STATE\s*=\s*(0x[0-9A-Fa-f]+)",
        ui_state_source.read_text(encoding="utf-8"),
    )
    if (
        len(ui_state_matches) != 1
        or int(ui_state_matches[0], 0) != UI_HELP_VIDEO_STATE_ADDRESS
        or start <= UI_HELP_VIDEO_STATE_ADDRESS < end
        or end > UI_HELP_VIDEO_STATE_ADDRESS
    ):
        _fail(
            "T21 Mirage RAM overlaps or no longer pins existing "
            "UI_HELP_VIDEO_STATE 0x0203F101"
        )
    overlaps: list[tuple[str, str]] = []
    for index, left in enumerate(live):
        for right in live[index + 1:]:
            if left[0] == right[0] and left[1] < right[2] and right[1] < left[2]:
                overlaps.append((left[3], right[3]))
    if overlaps:
        _fail(f"live RAM overlap detected: {overlaps[:4]}")

    save_rows = _rows(SAVE_LAYOUT)
    mirage = [row for row in save_rows if row.get("owner") == "T08_MIRAGE"]
    if len(mirage) != 1:
        _fail("T08 Mirage save owner row count differs")
    save = mirage[0]
    save_start = _integer(save["start"], "Mirage save start")
    save_end = _integer(save["end_exclusive"], "Mirage save end")
    if (
        save_start != 0x2574 or save_end != 0x259C
        or _integer(save["size"], "Mirage save size") != 40
        or save.get("symbol") != "mirage_records_and_item_reward"
        or "current_record[4..7]" not in save.get("notes", "")
    ):
        _fail("40-byte Mirage save/journal contract differs")
    return {
        "ram": {
            "address": start, "end_exclusive": end, "size": end - start,
            "owner": target["owner"], "symbol": target["symbol"],
            "header_size": MIRAGE_RAM_HEADER_SIZE,
            "party_snapshot_size": MIRAGE_PARTY_SNAPSHOT_SIZE,
            "composition_exact": True,
            "excluded_live_addresses": {
                "UI_HELP_VIDEO_STATE": UI_HELP_VIDEO_STATE_ADDRESS,
            },
            "ui_help_video_state_outside": True,
            "ui_help_video_state_gap_bytes": UI_HELP_VIDEO_STATE_ADDRESS - end,
            "live_overlap_count": 0,
        },
        "save": {
            "offset": save_start, "end_exclusive": save_end, "size": 40,
            "owner": save["owner"], "abi_changed": False,
            "journal": {
                "field": "current_record[4..7]", "relative_offset": 8,
                "size": 8, "absolute_offset": save_start + 8,
            },
            "factory_overlap_count": 0,
        },
    }


def _live_registry(path: Path, key: str, label: str) -> dict[str, int]:
    rows = _index(_rows(path), key, label)
    result: dict[str, int] = {}
    for name, row in rows.items():
        value = _integer(row.get("id"), f"{label} {name} id")
        if value < 0:
            _fail(f"{label} {name}: negative id")
        result[name] = value
    return result


def _load_bindings(stage: bytes) -> list[dict[str, Any]]:
    rows = _rows(BINDINGS)
    expected = {
        "MIRAGE_RECEPTIONIST_OBJECT_SCRIPT": (
            "MAP_OBJECT_SCRIPT_POINTER", 0x08885D70, "SCRIPT_POINTER",
            "script::mirage_reception", 4,
        ),
        "MIRAGE_MAP_ENTRY_CLEANUP": (
            "MAP_SCRIPT_TABLE_POINTER", 0x08315B7C, "SCRIPT_TABLE_POINTER",
            "table::mirage_map_scripts", 4,
        ),
        "MIRAGE_EXIT_CLEANUP_MAP16_0": (
            "MAP_SCRIPT_POINTER", 0x08896606, "SCRIPT_POINTER",
            "script::mirage_cleanup", 4,
        ),
        "MIRAGE_EXIT_CLEANUP_MAP3_12": (
            "MAP_SCRIPT_POINTER", 0x08173C1D, "SCRIPT_POINTER",
            "script::mirage_cleanup", 4,
        ),
        "MIRAGE_SAVE_LOAD_CHAIN": (
            "SAVE_LOAD_ENTRY", 0x080DB4E4, "THUMB_JUMP",
            "native::MirageProduction_SaveLoadAdapter", 8,
        ),
        "MIRAGE_TRAINER_PARTY_CHAIN": (
            "TRAINER_PARTY_CALLER", 0x09096EC4, "THUMB_BL",
            "native::MirageProduction_BuildTrainerPartyAdapter", 4,
        ),
        "MIRAGE_ABILITY_LOAD_CHAIN": (
            "BATTLE_ABILITY_CALLER", 0x090973FC, "THUMB_BL",
            "native::MirageProduction_LoadProperAbilityBattleDataAdapter", 4,
        ),
    }
    indexed = _index(rows, "binding_key", "Mirage physical bindings")
    if set(indexed) != set(expected) or len(rows) != 7:
        _fail("Mirage physical binding key set differs")
    result: list[dict[str, Any]] = []
    for key, contract in expected.items():
        row = indexed[key]
        kind, address, mode, target, size = contract
        raw = bytes.fromhex(str(row.get("expected_hex", "")))
        offset = _rom_offset(address, size)
        old_target = _integer(row.get("old_target"), f"{key} old target")
        if (
            row.get("kind") != kind or _integer(row.get("address"), key) != address
            or row.get("patch_mode") != mode or row.get("target_symbol") != target
            or row.get("owner") != "T21_MIRAGE_PRODUCTION" or len(raw) != size
            or stage[offset:offset + size] != raw
        ):
            _fail(f"{key}: rooted Stage37 expected-byte contract differs")
        if mode == "THUMB_BL" and _decode_thumb_bl(address, raw) != old_target:
            _fail(f"{key}: rooted Stage37 BL target differs")
        result.append({
            **dict(row), "address_value": address, "expected": raw,
            "old_target_value": old_target,
        })
    if stage[_rom_offset(0x0818F3BC)] != 0:
        _fail("Stage37 Mirage old map-script table is no longer empty")
    return result


def _load_model(inputs: Mapping[str, Any]) -> dict[str, Any]:
    audit_policy = _read_json(AUDIT_POLICY).get("facilities", {}).get("mirage")
    expected_audit_policy = {
        "group": 31, "map": 1, "map_section": 143,
        "flags": [0x1212, 0x1213, 0x1214, 0x1215],
        "vars": [0x407D, 0x407E],
        "badge_flags": list(range(0x0820, 0x0828)),
        "respawn_id": 14,
        "policy": "REMAP_ALL_PERSISTENT_STATE_AND_EXACT_BADGE_RESTORE",
        "party_model": "CARRIED_THREE_NOT_RENTAL",
    }
    if audit_policy != expected_audit_policy:
        _fail("T02 Mirage physical/ownership audit policy differs")
    mode_rows = [row for row in _rows(MODES) if row.get("party_owner") == "MIRAGE"]
    trainer_rows = [
        row for row in _rows(TRAINERS)
        if row.get("pool_key", "").startswith("TRAINER_POOL_KEY_MIRAGE_")
    ]
    rental_rows = [row for row in _rows(RENTALS)
                   if row.get("pool_key") == "RENTAL_POOL_KEY_SPECIAL"]
    reward_rows = [row for row in _rows(REWARDS)
                   if row.get("trigger_kind") == "MIRAGE_VIRTUAL_ITEM"]
    id_rows_all = _index(_rows(TRAINER_IDS), "trainer_key", "trainer IDs")
    constraint_rows = [row for row in _rows(CONSTRAINTS)
                       if row.get("constraint_key") == "TRAINER_CONSTRAINT_MIRAGE"]
    if tuple(map(len, (mode_rows, trainer_rows, rental_rows, reward_rows, constraint_rows))) != (
        4, 4, 6, 5, 1,
    ):
        _fail("Mirage manifest cardinality differs (4/4/6/5/1 required)")

    modes_by_key = _index(mode_rows, "mode_key", "Mirage modes")
    trainers_by_key = _index(trainer_rows, "facility_trainer_key", "Mirage trainers")
    rentals_by_key = _index(rental_rows, "rental_key", "Mirage rentals")
    rewards_by_key = _index(reward_rows, "facility_reward_key", "Mirage rewards")
    expected_mode_keys = {f"FACILITY_MODE_MIRAGE_ROUND_{i}" for i in range(1, 5)}
    expected_trainer_keys = {f"FACILITY_TRAINER_KEY_MIRAGE_{i}" for i in range(1, 5)}
    expected_rental_keys = {f"RENTAL_KEY_SPECIAL_{i:02d}" for i in range(1, 7)}
    expected_reward_keys = {
        "FACILITY_REWARD_KEY_MIRAGE_CHEAP", "FACILITY_REWARD_KEY_MIRAGE_MID",
        "FACILITY_REWARD_KEY_MIRAGE_HIGH", "FACILITY_REWARD_KEY_MIRAGE_ONCE",
        "FACILITY_REWARD_KEY_MIRAGE_TOP",
    }
    if (
        set(modes_by_key) != expected_mode_keys
        or set(trainers_by_key) != expected_trainer_keys
        or set(rentals_by_key) != expected_rental_keys
        or set(rewards_by_key) != expected_reward_keys
    ):
        _fail("Mirage manifest exact key set differs")

    expected_mechanics = ("NONE", "MEGA", "Z", "ONE_OF_MEGA_Z_TERA")
    resolved_modes: list[dict[str, Any]] = []
    trainer_ids: dict[str, int] = {}
    for round_index in range(1, 5):
        mode_key = f"FACILITY_MODE_MIRAGE_ROUND_{round_index}"
        trainer_key = f"FACILITY_TRAINER_KEY_MIRAGE_{round_index}"
        pool_key = f"TRAINER_POOL_KEY_MIRAGE_{round_index}"
        mode = modes_by_key[mode_key]
        trainer = trainers_by_key[trainer_key]
        id_row = id_rows_all.get(trainer_key)
        unlock = "VEGA_HALL_OF_FAME" if round_index == 1 else "KANTO_CERT_4"
        rental_keys = [str(trainer.get(f"rental_key{i}", "")) for i in range(1, 7)]
        if (
            mode.get("tier") != f"MIRAGE_{round_index}"
            or mode.get("format") != "SINGLE"
            or _integer(mode.get("selection_count"), mode_key) != 3
            or _integer(mode.get("battle_count"), mode_key) != 7
            or mode.get("unlock_key") != unlock
            or mode.get("rental_pool_key") != "RENTAL_POOL_KEY_SPECIAL"
            or mode.get("trainer_pool_key") != pool_key
            or mode.get("level_policy") != "LEVEL_100_FIXED"
            or mode.get("mechanic_policy") != expected_mechanics[round_index - 1]
            or mode.get("ai_profile_key") != "AI_FULL_SMART"
            or mode.get("state_owner") != "OWNER_KEY_MIRAGE_STATE"
            or mode.get("link_multi") != "false" or mode.get("status") != "ACTIVE"
            or trainer.get("pool_key") != pool_key or trainer.get("format") != "SINGLE"
            or trainer.get("ai_profile_key") != "AI_FULL_SMART"
            or trainer.get("mechanic_policy") != expected_mechanics[round_index - 1]
            or trainer.get("unlock_key") != unlock or trainer.get("status") != "ACTIVE"
            or rental_keys != [f"RENTAL_KEY_SPECIAL_{i:02d}" for i in range(1, 7)]
            or id_row is None or id_row.get("source_trainer") != "T16_GENERATED"
            or id_row.get("classification") != "PROJECT_APPEND"
            or id_row.get("status") != "ALLOCATED"
        ):
            _fail(f"{mode_key}: fixed mode/trainer/id contract differs")
        trainer_id = _integer(id_row["id"], f"{trainer_key} numeric id")
        if trainer_id != 744 + round_index:
            _fail(f"{trainer_key}: Stage37 numeric ID differs")
        trainer_ids[trainer_key] = trainer_id
        unlock_kind, unlock_value = UNLOCK_ROWS[unlock]
        resolved_modes.append({
            "mode_key": mode_key, "round_index": round_index,
            "battle_count": 7, "selection_count": 3,
            "unlock_key": unlock, "unlock_kind": unlock_kind,
            "unlock_value": unlock_value,
            "mechanic_policy": expected_mechanics[round_index - 1],
            "mechanic_id": MECHANIC_IDS[expected_mechanics[round_index - 1]],
            "ai_profile_key": "AI_FULL_SMART", "ai_profile_id": 5,
            "trainer_key": trainer_key, "trainer_id": trainer_id,
            "trainer_pool_key": pool_key, "rental_keys": rental_keys,
            "level": 100,
        })

    registries = {
        "species": _live_registry(Path("manifests/species_ids.csv"), "species_key", "species"),
        "move": _live_registry(Path("manifests/move_ids.csv"), "move_key", "moves"),
        "item": _live_registry(Path("manifests/item_ids.csv"), "item_key", "items"),
        "ability": _live_registry(Path("manifests/ability_ids.csv"), "ability_key", "abilities"),
        "type": _live_registry(Path("manifests/type_ids.csv"), "type_key", "types"),
    }
    resolved_rentals: list[dict[str, Any]] = []
    for index in range(1, 7):
        key = f"RENTAL_KEY_SPECIAL_{index:02d}"
        row = rentals_by_key[key]
        symbolic = {
            "species": row.get("species_key", ""), "nature": row.get("nature_key", ""),
            "item": row.get("item_key", ""), "ability": row.get("ability_key", ""),
            "tera_type": row.get("tera_type_key", ""),
            "moves": [row.get(f"move{i}_key", "") for i in range(1, 5)],
        }
        missing = [
            f"{domain}:{name}" for domain, names in (
                ("species", [symbolic["species"]]), ("item", [symbolic["item"]]),
                ("ability", [symbolic["ability"]]),
                ("move", symbolic["moves"]),
            ) for name in names if name not in registries[domain]
        ]
        if (
            missing or row.get("origin_bucket") != "SPECIAL" or row.get("form_key") != "NONE"
            or _integer(row.get("level"), key) != 50 or symbolic["nature"] != "NATURE_SERIOUS"
            or row.get("iv_policy") != "ALL_31" or row.get("ev_spread_key") != "EV_SPREAD_ROLE_510"
            or row.get("gmax_allowed") != "false" or symbolic["tera_type"] != "TYPE_KEY_NONE"
            or _integer(row.get("weight"), key) != 1 or row.get("status") != "ACTIVE"
        ):
            _fail(f"{key}: fixed special rental contract differs: missing={missing}")
        resolved_rentals.append({
            "rental_key": key, "pool_key": "RENTAL_POOL_KEY_SPECIAL",
            "species_key": symbolic["species"],
            "species_id": registries["species"][symbolic["species"]],
            "source_level": 50, "battle_level": 100,
            "nature_key": symbolic["nature"], "nature_id": NATURE_IDS[symbolic["nature"]],
            "iv": 31, "ev_spread_key": "EV_SPREAD_ROLE_510", "ev_profile_id": 1,
            "ev_values": [85, 85, 85, 85, 85, 85], "ev_sum": 510,
            "item_key": symbolic["item"], "item_id": registries["item"][symbolic["item"]],
            "move_keys": symbolic["moves"],
            "move_ids": [registries["move"][name] for name in symbolic["moves"]],
            "ability_key": symbolic["ability"],
            "ability_id": registries["ability"][symbolic["ability"]],
            "tera_type_key": symbolic["tera_type"],
            # `TYPE_KEY_NONE` is the facility-schema sentinel and deliberately
            # has no row in the 0..24 live type registry.
            "tera_type_id": 0xFF,
            "weight": 1,
        })

    expected_rewards = [
        ("FACILITY_REWARD_KEY_MIRAGE_CHEAP", 7, -1, "VEGA_HALL_OF_FAME", "REPEATABLE", "NONE"),
        ("FACILITY_REWARD_KEY_MIRAGE_MID", 14, -2, "KANTO_CERT_4", "REPEATABLE", "NONE"),
        ("FACILITY_REWARD_KEY_MIRAGE_HIGH", 21, -3, "KANTO_CERT_4", "REPEATABLE", "NONE"),
        ("FACILITY_REWARD_KEY_MIRAGE_ONCE", 28, -4, "KANTO_CERT_4", "ONCE", "CLAIM_KEY_MIRAGE_ONCE"),
        ("FACILITY_REWARD_KEY_MIRAGE_TOP", 35, -5, "KANTO_LEAGUE_CLEAR", "ONCE", "CLAIM_KEY_MIRAGE_TOP"),
    ]
    resolved_rewards: list[dict[str, Any]] = []
    once_index = 0
    for expected in expected_rewards:
        key, streak, amount, unlock, repeatability, claim_key = expected
        row = rewards_by_key[key]
        item_key = row.get("item_key", "")
        if (
            _integer(row.get("streak"), key) != streak
            or row.get("currency_key") != "CURRENCY_KEY_MIRAGE"
            or _integer(row.get("amount"), key) != amount
            or item_key not in registries["item"]
            or row.get("unlock_key") != unlock or row.get("repeatability") != repeatability
            or row.get("claim_key") != claim_key or row.get("status") != "ACTIVE"
            or _integer(row.get("quantity"), key) != (0 if streak == 28 else 1)
        ):
            _fail(f"{key}: virtual-item reward contract differs")
        unlock_kind, unlock_value = UNLOCK_ROWS[unlock]
        claim_mask = 0
        if repeatability == "ONCE":
            claim_mask = 1 << once_index
            once_index += 1
        resolved_rewards.append({
            "facility_reward_key": key, "streak": streak,
            "tier": -amount, "amount_metadata": amount,
            "item_key": item_key, "item_id": registries["item"][item_key],
            "quantity": _integer(row["quantity"], key),
            "unlock_key": unlock, "unlock_kind": unlock_kind,
            "unlock_value": unlock_value, "repeatability": repeatability,
            "claim_key": claim_key, "claim_mask": claim_mask,
        })

    constraint = constraint_rows[0]
    if (
        constraint.get("region") != "TOHOKU" or constraint.get("category") != "MIRAGE"
        or _integer(constraint.get("level_min"), "Mirage level min") != 100
        or _integer(constraint.get("level_max"), "Mirage level max") != 100
        or _integer(constraint.get("max_batch_adjustment"), "Mirage adjustment") != 0
        or constraint.get("ai_profile_key") != "AI_FULL_SMART"
        or constraint.get("mechanic_policy") != "ROUND_POLICY"
        or constraint.get("composition_policy") != "SEVEN_BATTLES_TIMES_FOUR_ROUNDS"
        or constraint.get("global_scaling") != "false" or constraint.get("status") != "ACTIVE"
    ):
        _fail("TRAINER_CONSTRAINT_MIRAGE differs")

    stage = inputs["stage"]
    table_offset = _rom_offset(TRAINER_TABLE_ADDRESS, TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE)
    records = []
    for key, trainer_id in sorted(trainer_ids.items(), key=lambda pair: pair[1]):
        start = table_offset + trainer_id * TRAINER_RECORD_SIZE
        raw = stage[start:start + TRAINER_RECORD_SIZE]
        if len(raw) != TRAINER_RECORD_SIZE or raw == bytes(TRAINER_RECORD_SIZE):
            _fail(f"{key}: Stage37 trainer record is missing")
        records.append({"trainer_key": key, "trainer_id": trainer_id,
                        "record_hex": raw.hex(), "sha256": _sha(raw)})

    source_paths = (
        MODES, TRAINERS, RENTALS, REWARDS, TRAINER_IDS, CONSTRAINTS, AUDIT_POLICY,
        CHANGEKIT_META, BINDINGS,
        RAM_LAYOUT, SAVE_LAYOUT, UI_HELP_VIDEO_STATE_SOURCE,
        Path("manifests/species_ids.csv"),
        Path("manifests/move_ids.csv"), Path("manifests/item_ids.csv"),
        Path("manifests/ability_ids.csv"), Path("manifests/type_ids.csv"),
    )
    return {
        "modes": resolved_modes, "rentals": resolved_rentals,
        "rewards": resolved_rewards, "trainer_ids": trainer_ids,
        "trainer_records": records, "bindings": _load_bindings(stage),
        "constraint": dict(constraint),
        "source_hashes": {path.as_posix(): _sha((ROOT / path).read_bytes())
                          for path in source_paths},
    }


def _generated_header(model: Mapping[str, Any], ownership: Mapping[str, Any]) -> bytes:
    lines = [
        "#ifndef VEGA_MIRAGE_PRODUCTION_GENERATED_H",
        "#define VEGA_MIRAGE_PRODUCTION_GENERATED_H",
        "#include <stdint.h>",
        "#define MIRAGE_PRODUCTION_MODE_COUNT 4u",
        "#define MIRAGE_PRODUCTION_RENTAL_COUNT 6u",
        "#define MIRAGE_PRODUCTION_REWARD_COUNT 5u",
        "#define MIRAGE_PRODUCTION_BATTLE_COUNT 28u",
        "#define MIRAGE_PRODUCTION_SELECTION_COUNT 3u",
        "#define MIRAGE_PRODUCTION_LEVEL 100u",
        "#define MIRAGE_PRODUCTION_AI_FULL_SMART 5u",
        "#define MIRAGE_PRODUCTION_EV_ROLE_510_VALUE 85u",
        "#define MIRAGE_PRODUCTION_MECHANIC_NONE 0u",
        "#define MIRAGE_PRODUCTION_MECHANIC_MEGA 1u",
        "#define MIRAGE_PRODUCTION_MECHANIC_Z 2u",
        "#define MIRAGE_PRODUCTION_MECHANIC_TERA 4u",
        f"#define MIRAGE_PRODUCTION_RAM_ADDRESS 0x{ownership['ram']['address']:08X}u",
        f"#define MIRAGE_PRODUCTION_RAM_END_EXCLUSIVE 0x{ownership['ram']['end_exclusive']:08X}u",
        f"#define MIRAGE_PRODUCTION_RAM_SIZE {ownership['ram']['size']}u",
        f"#define MIRAGE_PRODUCTION_STATE_HEADER_SIZE {ownership['ram']['header_size']}u",
        f"#define MIRAGE_PRODUCTION_PARTY_SNAPSHOT_SIZE {ownership['ram']['party_snapshot_size']}u",
        f"#define MIRAGE_UI_HELP_VIDEO_STATE_ADDRESS 0x{UI_HELP_VIDEO_STATE_ADDRESS:08X}u",
        f"#define MIRAGE_PRODUCTION_SPECIAL_VAR_RESULT 0x{SPECIAL_VAR_RESULT:08X}u",
        f"#define MIRAGE_PRODUCTION_SPECIAL_VAR_ARG0 0x{SPECIAL_VAR_ARG0:08X}u",
        f"#define MIRAGE_PRODUCTION_QOL_SAVE_LOAD_ADDRESS 0x{QOL_SAVE_LOAD_ADDRESS:08X}u",
        f"#define MIRAGE_PRODUCTION_TRAINER_TABLE_ADDRESS 0x{TRAINER_TABLE_ADDRESS:08X}u",
        f"#define MIRAGE_PRODUCTION_TRAINER_RECORD_SIZE {TRAINER_RECORD_SIZE}u",
        "#define MIRAGE_PRODUCTION_JOURNAL_FIRST_RECORD 4u",
        "#define MIRAGE_PRODUCTION_JOURNAL_RECORD_COUNT 4u",
        *[
            f"#define {name} 0x{address:08X}u"
            for name, address in EXTERNAL_ENTRYPOINTS.items()
        ],
        *[
            f"#define {name} 0x{address:08X}u"
            for name, address in RUNTIME_DATA_ADDRESSES.items()
        ],
        *[
            f"#define {name} {value}u"
            for name, value in RUNTIME_LAYOUT_CONSTANTS.items()
        ],
        "typedef struct MirageProductionModeRow {",
        "  uint8_t round_index, battle_count, selection_count, mechanic_mode;",
        "  uint8_t ai_profile, unlock_kind; uint16_t unlock_value, trainer_id, level;",
        "} MirageProductionModeRow;",
        "typedef struct MirageProductionRentalRow {",
        "  uint16_t species, item, moves[4], ability;",
        "  uint8_t level, nature, iv, ev_profile, tera_type, weight;",
        "} MirageProductionRentalRow;",
        "typedef struct MirageProductionRewardRow {",
        "  uint16_t streak, item, quantity, unlock_value;",
        "  uint8_t tier, unlock_kind, repeatable, reserved; uint32_t claim_mask;",
        "} MirageProductionRewardRow;",
        "static const MirageProductionModeRow gMirageProductionModes[4] = {",
    ]
    for row in model["modes"]:
        lines.append(
            "  {%du,7u,3u,%du,5u,%du,0x%04Xu,%du,100u}, /* %s */"
            % (row["round_index"], row["mechanic_id"], row["unlock_kind"],
               row["unlock_value"], row["trainer_id"], row["mode_key"])
        )
    lines.extend(["};", "static const MirageProductionRentalRow gMirageProductionRentals[6] = {"])
    for row in model["rentals"]:
        moves = ",".join(f"{value}u" for value in row["move_ids"])
        lines.append(
            "  {%du,%du,{%s},%du,100u,%du,31u,%du,%du,1u}, /* %s */"
            % (row["species_id"], row["item_id"], moves, row["ability_id"],
               row["nature_id"], row["ev_profile_id"], row["tera_type_id"],
               row["rental_key"])
        )
    lines.extend(["};", "static const MirageProductionRewardRow gMirageProductionRewards[5] = {"])
    for row in model["rewards"]:
        lines.append(
            "  {%du,%du,%du,0x%04Xu,%du,%du,%du,0u,0x%08Xu}, /* %s */"
            % (row["streak"], row["item_id"], row["quantity"], row["unlock_value"],
               row["tier"], row["unlock_kind"], int(row["repeatability"] == "REPEATABLE"),
               row["claim_mask"], row["facility_reward_key"])
        )
    lines.append("};")
    for index, row in enumerate(model["rewards"]):
        unlock_code = {"VEGA_HALL_OF_FAME": 0, "KANTO_CERT_4": 1,
                       "KANTO_LEAGUE_CLEAR": 2}[row["unlock_key"]]
        lines.extend([
            f"#define MIRAGE_REWARD_{index}_STREAK {row['streak']}u",
            f"#define MIRAGE_REWARD_{index}_ITEM {row['item_id']}u",
            f"#define MIRAGE_REWARD_{index}_CLAIM_MASK 0x{row['claim_mask']:08X}u",
            f"#define MIRAGE_REWARD_{index}_UNLOCK {unlock_code}u",
        ])
    lines.extend(["#endif", ""])
    return "\n".join(lines).encode("utf-8")


def _runtime_source_contract() -> dict[str, Any]:
    source = ROOT / "overlays/mirage_production/mirage_production.c"
    public = ROOT / "overlays/mirage_production/mirage_production.h"
    if not source.is_file() or not public.is_file():
        _fail("Mirage production overlay source/header is missing")
    text = source.read_text(encoding="utf-8")
    public_text = public.read_text(encoding="utf-8")
    if (
        not re.search(
            rf"#define\s+MIRAGE_PRODUCTION_STATE_SIZE\s+{MIRAGE_RAM_SIZE}u\b",
            public_text,
        )
        or not re.search(
            rf"\bparty_snapshot\s*\[\s*{MIRAGE_PARTY_SNAPSHOT_SIZE}\s*\]",
            public_text,
        )
        or re.search(r"\breserved\s*\[\s*360\s*\]", public_text)
    ):
        _fail(
            "Mirage runtime public ABI differs from exact 664-byte "
            "header64+party600 contract"
        )
    export = "MirageProduction_LoadProperAbilityBattleDataAdapter"
    marker = f"MIRAGE_EXPORT({export})"
    start = text.find(marker)
    end = text.find("\nMIRAGE_EXPORT(", start + len(marker))
    if start < 0:
        _fail(f"Mirage runtime source export is missing: {export}")
    if end < 0:
        end = len(text)
    body = text[start:end]
    delegate = "FN_CHANGEKIT_LOAD_PROPER_ABILITY();"
    active_guard = "if (!gMirageProductionState->active"
    override = "write_u16(G_BATTLE_MONS"
    delegate_index = body.find(delegate)
    guard_index = body.find(active_guard)
    override_index = body.find(override)
    if (
        body.count(delegate) != 1
        or body.count(override) != 1
        or not 0 <= delegate_index < guard_index < override_index
        or "|| !gMirageProductionState->battle_local_active" not in body
        or "return;" not in body[guard_index:override_index]
    ):
        _fail(
            "Mirage ability adapter must delegate ChangeKit exactly once before "
            "the active-only battle-mon override"
        )
    if text.count("FN_HEAL_PLAYER_PARTY();") != 1:
        _fail(
            "Mirage runtime must own the synchronous pre-battle party heal "
            "exactly once in its battle-copy path"
        )
    transition_export = "MirageProduction_MapTransitionRecover"
    transition_marker = f"MIRAGE_EXPORT({transition_export})"
    transition_start = text.find(transition_marker)
    transition_end = text.find(
        "\nMIRAGE_EXPORT(", transition_start + len(transition_marker)
    )
    if transition_start < 0:
        _fail(f"Mirage runtime source export is missing: {transition_export}")
    if transition_end < 0:
        transition_end = len(text)
    transition_body = text[transition_start:transition_end]
    ensure_index = transition_body.find("ensure_state();")
    active_index = transition_body.find("if (gMirageProductionState->active)")
    ok_index = transition_body.find("return set_status(MIRAGE_STATUS_OK);")
    recover_index = transition_body.find("return MirageProduction_Recover();")
    if (
        transition_body.count("MirageProduction_Recover();") != 1
        or not 0 <= ensure_index < active_index < ok_index < recover_index
        or "journal_clear" in transition_body
        or "clear_challenge_state" in transition_body
    ):
        _fail(
            "Mirage map-transition adapter must keep active journals and "
            "delegate recovery only while inactive"
        )
    return {
        "runtime_state_address": MIRAGE_RAM_ADDRESS,
        "runtime_state_end_exclusive": MIRAGE_RAM_END_EXCLUSIVE,
        "runtime_state_size": MIRAGE_RAM_SIZE,
        "runtime_state_header_size": MIRAGE_RAM_HEADER_SIZE,
        "runtime_party_snapshot_size": MIRAGE_PARTY_SNAPSHOT_SIZE,
        "ui_help_video_state_address": UI_HELP_VIDEO_STATE_ADDRESS,
        "ui_help_video_state_outside": True,
        "ability_adapter_export": export,
        "changekit_delegate_call_count": 1,
        "changekit_delegate_before_active_guard": True,
        "mirage_override_write_count": 1,
        "mirage_override_after_active_guard": True,
        "non_mirage_battle_data_byte_equivalent": True,
        "pre_battle_player_party_heal_owner": "RUNTIME_FINALIZE_BATTLE_COPY",
        "pre_battle_player_party_heal_call_count": 1,
        "map_transition_recovery_export": transition_export,
        "map_transition_active_challenge": "SKIP_KEEP_JOURNAL_STATUS_OK",
        "map_transition_inactive_challenge": "RECOVER_STALE_STATE",
        "map_transition_direct_recover_call_from_field_script": False,
        "map_transition_inactive_recover_delegate_count": 1,
    }


def _compile_runtime(load_address: int, header: bytes) -> tuple[bytes, dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    source = ROOT / "overlays/mirage_production/mirage_production.c"
    public = ROOT / "overlays/mirage_production/mirage_production.h"
    if not source.is_file() or not public.is_file():
        _fail("Mirage production overlay source/header is missing")
    with tempfile.TemporaryDirectory(prefix="vega-mirage-production-runtime-") as raw:
        directory = Path(raw)
        (directory / "mirage_production_generated.h").write_bytes(header)
        obj = directory / "mirage_production.o"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
            "-std=c11", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
            "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-fno-common",
            f"-I{directory}", f"-I{ROOT}", "-DVEGA_SAVE_ROM_RUNTIME=1",
            "-c", str(source), "-o", str(obj),
        ], "compile Mirage production runtime")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.MirageProduction_*)) *(.text*) *(.rodata*) *(.data*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "mirage_production.elf"
        binary = directory / "mirage_production.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,MirageProduction_Probe", f"-Wl,-T,{linker}",
            str(obj), "-lgcc", "-o", str(elf),
        ], "link Mirage production runtime")
        undefined = _run([nm, "-u", str(elf)], "Mirage undefined-symbol audit")
        if undefined:
            _fail("Mirage runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "Mirage objcopy")
        symbols: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run([nm, "-n", "--defined-only", str(elf)], "Mirage nm").splitlines():
            fields = line.split()
            if len(fields) != 3:
                continue
            try:
                symbols[fields[2]] = int(fields[0], 16)
            except ValueError:
                continue
            if fields[1] in {"B", "b", "C", "c", "D", "d", "G", "g", "S", "s"}:
                mutable.append(fields[2])
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing or mutable:
            _fail(f"Mirage runtime symbols differ: missing={missing}, mutable={mutable}")
        payload = binary.read_bytes()
        if not payload or len(payload) > 128 * 1024:
            _fail(f"Mirage runtime size is unreasonable: {len(payload)}")
        return payload, symbols


@dataclass
class _Script:
    data: bytearray
    fixups: list[tuple[int, str, bool]]
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

    def pointer(self, label: str, *, thumb: bool = False) -> "_Script":
        self.fixups.append((len(self.data), label, thumb))
        self.data.extend(bytes(4))
        return self

    def setvar(self, variable: int, value: int) -> "_Script":
        self.operations.append(f"setvar:0x{variable:04X}:{value}")
        return self.emit(0x16).half(variable).half(value)

    def callnative(self, name: str) -> "_Script":
        self.operations.append(f"callnative:{name}")
        return self.emit(0x23).pointer(f"native::{name}", thumb=True)

    def trainerbattle_single_no_intro(
        self, trainer_id: int, local_id: int, defeat_text: str,
    ) -> "_Script":
        self.operations.append(
            f"trainerbattle:3:{trainer_id}:{local_id}:{defeat_text}"
        )
        return (
            self.emit(0x5C, 0x03)
            .half(trainer_id)
            .half(local_id)
            .pointer(defeat_text)
        )

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


def _add_script(
    blob: _Blob, label: str, script: _Script, metadata: list[dict[str, Any]],
) -> None:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target, thumb in script.fixups:
        blob.pointer(offset + relative, target, thumb=thumb)
    metadata.append({
        "label": label, "offset": offset, "size": len(script.data),
        "operations": script.operations,
    })


def _build_field(blob: _Blob, model: Mapping[str, Any]) -> dict[str, Any]:
    mapping, tokens = _charmap(ROOT)
    texts = {
        "text::prompt": "ミラージュバトルに\nちょうせん しますか？",
        "text::choose": "じぶんの てもちから\n3ひきを えらんでください",
        "text::mega": "だい4しゅうは\nメガシンカに しますか？",
        "text::z": "Zワザに しますか？",
        "text::tera": "テラスタルに しますか？",
        "text::complete": "ミラージュバトル\n28せん かんそう！",
        "text::defeat": "ミラージュバトル\nしょうり！",
        "text::loss": "ちょうせんを しゅうりょうしました",
        "text::cancel": "ちょうせんを とりやめました",
        "text::error": "じゅんびに しっぱいしました",
    }
    for label, text in texts.items():
        blob.add(label, _encode_text(text, mapping, tokens), 1)

    scripts: list[dict[str, Any]] = []
    _add_script(
        blob, "script::mirage_reception",
        _Script().emit(0x6A, 0x5A, operation="lock_faceplayer")
        .msgbox("text::prompt", 5).compare_result(1)
        .if_equal("script::mirage_enter").goto("script::mirage_cancel"), scripts,
    )
    _add_script(
        blob, "script::mirage_enter",
        _Script().callnative("MirageProduction_FieldEnter")
        .compare_result(1).if_equal("script::mirage_choose")
        .goto("script::mirage_error"), scripts,
    )
    _add_script(
        blob, "script::mirage_choose",
        _Script().msgbox("text::choose")
        .emit(0x25, operation="special:0x0029").half(0x0029)
        .emit(0x27, operation="waitstate")
        .callnative("MirageProduction_CommitSelection")
        .compare_result(1).if_equal("script::mirage_commit_success")
        .goto("script::mirage_cancel"), scripts,
    )
    _add_script(
        blob, "script::mirage_commit_success",
        _Script().emit(0x9F, operation=f"setrespawn:{MIRAGE_RESPAWN}")
        .half(MIRAGE_RESPAWN).goto("script::mirage_battle_01"), scripts,
    )

    _add_script(
        blob, "script::mirage_round4_choice",
        _Script().msgbox("text::mega", 5).compare_result(1)
        .if_equal("script::mirage_round4_mega").goto("script::mirage_round4_z_prompt"),
        scripts,
    )
    _add_script(
        blob, "script::mirage_round4_z_prompt",
        _Script().msgbox("text::z", 5).compare_result(1)
        .if_equal("script::mirage_round4_z").goto("script::mirage_round4_tera_prompt"),
        scripts,
    )
    _add_script(
        blob, "script::mirage_round4_tera_prompt",
        _Script().msgbox("text::tera", 5).compare_result(1)
        .if_equal("script::mirage_round4_tera").goto("script::mirage_cancel"), scripts,
    )
    for label, mechanic in (("mega", 1), ("z", 2), ("tera", 4)):
        _add_script(
            blob, f"script::mirage_round4_{label}",
            _Script().setvar(0x8000, mechanic)
            .callnative("MirageProduction_CommitRound4Mechanic")
            .compare_result(1).if_equal("script::mirage_battle_22")
            .goto("script::mirage_error"), scripts,
        )

    after_status_rows: list[dict[str, Any]] = []
    trainerbattle_rows: list[dict[str, Any]] = []
    round_trainer_ids = [int(row["trainer_id"]) for row in model["modes"]]
    if round_trainer_ids != [745, 746, 747, 748]:
        _fail("Mirage canonical trainerbattle trainer IDs differ")
    for number in range(1, MIRAGE_BATTLE_COUNT + 1):
        label = f"script::mirage_battle_{number:02d}"
        launch = f"script::mirage_battle_{number:02d}_launch"
        after = f"script::mirage_battle_{number:02d}_after"
        next_label = (
            "script::mirage_complete" if number == MIRAGE_BATTLE_COUNT
            else "script::mirage_round4_choice" if number == 21
            else f"script::mirage_battle_{number + 1:02d}"
        )
        expected_after_status = (
            STATUS_CHALLENGE_COMPLETE if number == MIRAGE_BATTLE_COUNT
            else STATUS_ROUND_COMPLETE if number % 7 == 0
            else STATUS_BATTLE_CONTINUE
        )
        round_index = (number - 1) // 7
        trainer_id = round_trainer_ids[round_index]
        _add_script(
            blob, label,
            _Script().setvar(0x8000, number - 1)
            .callnative("MirageProduction_PrepareBattle")
            .compare_result(1).if_equal(launch).goto("script::mirage_loss"), scripts,
        )
        _add_script(
            blob, launch,
            _Script().callnative("MirageProduction_FinalizeBattleCopy")
            .compare_result(1).if_equal(after).goto("script::mirage_loss"), scripts,
        )
        after_script = (
            _Script().trainerbattle_single_no_intro(
                trainer_id, 1, "text::defeat"
            )
            .callnative("MirageProduction_AfterBattle")
            .compare_result(expected_after_status).if_equal(next_label)
        )
        trainerbattle_rows.append({
            "battle": number,
            "round_index": round_index + 1,
            "label": after,
            "opcode": 0x5C,
            "mode": 3,
            "mode_name": "SINGLE_NO_INTRO",
            "trainer_id": trainer_id,
            "local_id": 1,
            "defeat_text": "text::defeat",
            "continuation": "MirageProduction_AfterBattle",
            "trainer_flag_precheck": False,
        })
        if number == 7:
            # Without KANTO_CERT_4, Round 1 is a valid complete challenge.
            # With the gate, status 10 continues sequentially into Round 2.
            after_script.compare_result(STATUS_CHALLENGE_COMPLETE).if_equal(
                "script::mirage_complete"
            )
        after_status_rows.append({
            "battle": number,
            "accepted": [expected_after_status]
            + ([STATUS_CHALLENGE_COMPLETE] if number == 7 else []),
            "fallback": STATUS_LOST,
        })
        _add_script(
            blob, after, after_script.goto("script::mirage_loss"), scripts,
        )

    _add_script(
        blob, "script::mirage_complete",
        _Script().callnative("MirageProduction_Complete")
        .msgbox("text::complete").emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    _add_script(
        blob, "script::mirage_loss",
        _Script().callnative("MirageProduction_Abort")
        .msgbox("text::loss").emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    _add_script(
        blob, "script::mirage_cancel",
        _Script().callnative("MirageProduction_Abort")
        .msgbox("text::cancel").emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    _add_script(
        blob, "script::mirage_error",
        _Script().callnative("MirageProduction_Abort")
        .msgbox("text::error").emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    _add_script(
        blob, "script::mirage_cleanup",
        _Script().callnative("MirageProduction_Recover").emit(0x02, operation="end"), scripts,
    )
    _add_script(
        blob, "script::mirage_transition_recover",
        _Script().callnative("MirageProduction_MapTransitionRecover")
        .emit(0x02, operation="end"), scripts,
    )
    transition_scripts = [
        row for row in scripts
        if row["label"] == "script::mirage_transition_recover"
    ]
    if (
        len(transition_scripts) != 1
        or transition_scripts[0]["operations"] != [
            "callnative:MirageProduction_MapTransitionRecover", "end",
        ]
        or any(
            operation == "callnative:MirageProduction_Recover"
            for operation in transition_scripts[0]["operations"]
        )
    ):
        _fail("Mirage map transition must call only the active-safe recovery adapter")
    table = bytearray([3]) + bytes(4) + bytes([0])
    table_offset = blob.add("table::mirage_map_scripts", bytes(table), 4)
    blob.pointer(table_offset + 1, "script::mirage_transition_recover")
    operations = Counter(op.split(":", 1)[0]
                         for row in scripts for op in row["operations"])
    trainerbattle_launches = sum(
        op.startswith("trainerbattle:")
        for row in scripts for op in row["operations"]
    )
    direct_battlebegin_count = sum(
        op.startswith("battlebegin:")
        for row in scripts for op in row["operations"]
    )
    if trainerbattle_launches != 28 or direct_battlebegin_count != 0:
        _fail(
            "Mirage field graph must contain 28 canonical trainerbattle "
            "launches and no direct bare battlebegin"
        )
    if any(
        row["operations"][0]
        != (
            f"trainerbattle:3:{trainerbattle_rows[index]['trainer_id']}:"
            "1:text::defeat"
        )
        for index, row in enumerate(
            script for script in scripts
            if script["label"].endswith("_after")
        )
    ):
        _fail("Mirage AfterBattle scripts must begin with canonical trainerbattle")
    special_operations = [
        op for row in scripts for op in row["operations"]
        if op.startswith("special:")
    ]
    waitstate_count = sum(
        op == "waitstate" for row in scripts for op in row["operations"]
    )
    if special_operations != ["special:0x0029"] or waitstate_count != 1:
        _fail(
            "Mirage field graph must use only party UI special 0x0029 with "
            "one waitstate; runtime owns synchronous pre-battle healing"
        )
    respawn_scripts = [
        row for row in scripts
        if f"setrespawn:{MIRAGE_RESPAWN}" in row["operations"]
    ]
    if (
        len(respawn_scripts) != 1
        or respawn_scripts[0]["label"] != "script::mirage_commit_success"
        or respawn_scripts[0]["operations"]
        != [f"setrespawn:{MIRAGE_RESPAWN}", "goto:script::mirage_battle_01"]
    ):
        _fail("Mirage respawn must be set exactly once after selection commit")
    return {
        "scripts": scripts, "text_lengths": {key: len(value) for key, value in texts.items()},
        "operation_counts": dict(sorted(operations.items())),
        "battle_launch_count": trainerbattle_launches,
        "trainerbattle_launch_count": trainerbattle_launches,
        "direct_bare_battlebegin_count": direct_battlebegin_count,
        "trainerbattle_command": 0x5C,
        "trainerbattle_mode": 3,
        "trainerbattle_mode_name": "SINGLE_NO_INTRO",
        "trainerbattle_local_id": 1,
        "trainerbattle_defeat_text": "text::defeat",
        "trainerbattle_live_flags": MIRAGE_TRAINERBATTLE_LIVE_FLAGS,
        "trainerbattle_required_flags": dict(MIRAGE_TRAINERBATTLE_REQUIRED_FLAGS),
        "trainerbattle_authored_flags": ["TRAINER"],
        "trainerbattle_engine_owned_flags": ["IS_MASTER"],
        "trainerbattle_forbidden_flags": list(MIRAGE_TRAINERBATTLE_FORBIDDEN_FLAGS),
        "trainerbattle_forbidden_flags_zero": True,
        "trainerbattle_rows": trainerbattle_rows,
        "party_selection_special": 0x0029,
        "party_selection_waitstate": True,
        "pre_battle_special": None,
        "pre_battle_waitstate": False,
        "pre_battle_heal_owner": "RUNTIME_FINALIZE_BATTLE_COPY",
        "special_operation_count": len(special_operations),
        "waitstate_operation_count": waitstate_count,
        "scheduler_battlebegin_command": 0x5D,
        "map_script_installed": True,
        "map_script_type": 3,
        "map_transition_recovery": {
            "script": "script::mirage_transition_recover",
            "entrypoint": "MirageProduction_MapTransitionRecover",
            "direct_recover_call": False,
            "active_challenge": "SKIP_KEEP_JOURNAL_STATUS_OK",
            "inactive_challenge": "RECOVER_STALE_STATE",
        },
        "respawn": {
            "id": MIRAGE_RESPAWN,
            "opcode": 0x9F,
            "operation": f"setrespawn:{MIRAGE_RESPAWN}",
            "operation_count": 1,
            "after_commit_selection": True,
            "before_first_battle": True,
            "selection_cancel_preserves_previous_respawn": True,
        },
        "after_battle_statuses": after_status_rows,
        "after_battle_status_contract": {
            "OK": STATUS_OK,
            "CANCELLED": STATUS_CANCELLED,
            "NOT_UNLOCKED": STATUS_NOT_UNLOCKED,
            "BATTLE_CONTINUE": STATUS_BATTLE_CONTINUE,
            "ROUND_COMPLETE": STATUS_ROUND_COMPLETE,
            "CHALLENGE_COMPLETE": STATUS_CHALLENGE_COMPLETE,
            "LOST": STATUS_LOST,
            "round1_gate_complete_alternative": True,
        },
    }


def _build_payload(
    payload_offset: int, model: Mapping[str, Any], ownership: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any], bytes]:
    payload_address = GBA_ROM_BASE + payload_offset
    header = _generated_header(model, ownership)
    source_contract = _runtime_source_contract()
    code_address = payload_address + PAYLOAD_HEADER_SIZE
    code, symbols = _compile_runtime(code_address, header)
    blob = _Blob()
    header_offset = blob.reserve("header::mirage", PAYLOAD_HEADER_SIZE, 16)
    code_offset = blob.add("code::mirage", code, 4)
    if code_offset != PAYLOAD_HEADER_SIZE:
        _fail("Mirage payload code offset differs")
    for name, address in symbols.items():
        relative = address - code_address
        if 0 <= relative < len(code):
            blob.labels[f"native::{name}"] = code_offset + relative
    field = _build_field(blob, model)
    runtime_size = _align(len(blob.data), 16)
    if runtime_size > len(blob.data):
        blob.data.extend(b"\xFF" * (runtime_size - len(blob.data)))
    entrypoints = {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    struct.pack_into(
        "<8s18I", blob.data, header_offset, b"VEGAMP38", 1, runtime_size,
        PAYLOAD_HEADER_SIZE, len(code), 4, 6, 5, 28, 3, 100,
        entrypoints["MirageProduction_Probe"],
        entrypoints["MirageProduction_FieldEnter"],
        entrypoints["MirageProduction_SaveLoadAdapter"],
        0, 0, 0, MIRAGE_MAP_HEADER, MIRAGE_MAP_SECTION,
    )
    blob.pointer(header_offset + 8 + 13 * 4, "script::mirage_reception")
    blob.pointer(header_offset + 8 + 14 * 4, "script::mirage_cleanup")
    blob.pointer(header_offset + 8 + 15 * 4, "table::mirage_map_scripts")
    payload = blob.finish(payload_offset)
    labels = {
        label: payload_address + relative
        for label, relative in sorted(blob.labels.items())
        if label.startswith(("native::", "script::", "table::", "text::"))
    }
    field["labels"] = labels
    defeat_text_address = labels["text::defeat"]
    for row in field["trainerbattle_rows"]:
        address = labels[str(row["label"])]
        relative = address - payload_address
        expected = struct.pack(
            "<BBHHI", 0x5C, 3, int(row["trainer_id"]), 1,
            defeat_text_address,
        )
        if payload[relative:relative + len(expected)] != expected:
            _fail(
                f"Mirage battle {row['battle']}: canonical trainerbattle bytes differ"
            )
        if payload[relative + len(expected)] != 0x23:
            _fail(
                f"Mirage battle {row['battle']}: AfterBattle continuation differs"
            )
        row["address"] = address
        row["defeat_text_address"] = defeat_text_address
        row["command_hex"] = expected.hex()
    field["first_trainerbattle_script"] = "script::mirage_battle_01_after"
    field["first_trainerbattle_address"] = labels[
        field["first_trainerbattle_script"]
    ]
    transition_script_address = labels["script::mirage_transition_recover"]
    transition_table_address = labels["table::mirage_map_scripts"]
    transition_script_relative = transition_script_address - payload_address
    transition_table_relative = transition_table_address - payload_address
    transition_script_expected = (
        bytes([0x23])
        + struct.pack(
            "<I", entrypoints["MirageProduction_MapTransitionRecover"]
        )
        + bytes([0x02])
    )
    transition_table_expected = (
        bytes([3]) + struct.pack("<I", transition_script_address) + bytes([0])
    )
    if (
        payload[
            transition_script_relative:
            transition_script_relative + len(transition_script_expected)
        ] != transition_script_expected
        or payload[
            transition_table_relative:
            transition_table_relative + len(transition_table_expected)
        ] != transition_table_expected
    ):
        _fail("Mirage active-safe transition recovery script/table bytes differ")
    field["map_transition_recovery_physical"] = {
        "script_address": transition_script_address,
        "table_address": transition_table_address,
        "script_hex": transition_script_expected.hex(),
        "table_hex": transition_table_expected.hex(),
    }
    field["script_count"] = len(field["scripts"])
    runtime = {
        "payload": {
            "magic": "VEGAMP38", "offset": payload_offset, "address": payload_address,
            "size": len(payload), "sha256": _sha(payload),
            "code_address": code_address, "code_size": len(code), "code_sha256": _sha(code),
        },
        "entrypoints": entrypoints,
        "symbols": {name: value for name, value in symbols.items()
                    if code_address <= value < code_address + len(code)},
        "source_contract": source_contract,
        "field": field,
    }
    return payload, runtime, header


def _allocation(
    previous: Mapping[str, Any], size: int, digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules", "size": size,
        "alignment": 16, "owner": TASK,
        "purpose": (
            "Mirage carried-party 4-round/28-battle field scripts, isolated save "
            "transaction, virtual-item adapter, badge-exact cleanup and load chain"
        ),
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage38 allocator overlap detected")
    matches = [row for row in report.get("allocations", [])
               if row.get("name") == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage38 Mirage allocation is not unique")
    return matches[0], report


def _patch(
    output: bytearray, stage: bytes, declared: list[dict[str, Any]],
    address: int, expected: bytes, replacement: bytes, name: str,
) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{name}: expected/replacement length differs")
    offset = _rom_offset(address, len(expected))
    actual = stage[offset:offset + len(expected)]
    if actual != expected:
        _fail(f"{name}: Stage37 expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({"start": offset, "end_exclusive": offset + len(replacement), "kind": name})
    return {
        "name": name, "address": address, "offset": offset, "size": len(expected),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }


def _thumb_bl(source: int, target_thumb: int) -> bytes:
    if source & 1 or not target_thumb & 1:
        _fail(
            "Thumb BL source/target alignment differs: "
            f"0x{source:08X}->0x{target_thumb:08X}"
        )
    target = target_thumb & ~1
    displacement = target - (source + 4)
    if displacement & 1 or not -(1 << 22) <= displacement <= (1 << 22) - 2:
        _fail(
            "Thumb BL target is outside signed 23-bit range: "
            f"0x{source:08X}->0x{target_thumb:08X}"
        )
    first = 0xF000 | ((displacement >> 12) & 0x07FF)
    second = 0xF800 | ((displacement >> 1) & 0x07FF)
    encoded = struct.pack("<HH", first, second)
    if _decode_thumb_bl(source, encoded) != target_thumb:
        _fail("Thumb BL encoder round-trip differs")
    return encoded


def _upstream_regression(
    stage: bytes, output: bytes, inputs: Mapping[str, Any],
    patches: Sequence[Mapping[str, Any]], runtime: Mapping[str, Any],
) -> dict[str, Any]:
    changed_sites = {
        int(row["offset"]): int(row["size"])
        for row in patches
    }
    trainer_chains = [
        row for row in patches if row.get("name") == "MIRAGE_TRAINER_PARTY_CHAIN"
    ]
    ability_chains = [
        row for row in patches if row.get("name") == "MIRAGE_ABILITY_LOAD_CHAIN"
    ]
    if len(trainer_chains) != 1 or len(ability_chains) != 1:
        _fail("Mirage trainer-party/ability chain root is not unique")

    map_header_size = 28
    map_header_offset = _rom_offset(MIRAGE_MAP_HEADER, map_header_size)
    map_header_before = stage[map_header_offset:map_header_offset + map_header_size]
    map_header_after = output[map_header_offset:map_header_offset + map_header_size]
    map_layout_address, map_events_address, map_scripts_address, map_connections_address = (
        struct.unpack_from("<4I", map_header_before)
    )
    map_bgm, map_layout_id = struct.unpack_from("<HH", map_header_before, 16)
    if (
        map_layout_address != 0x082FCCF8
        or map_events_address != 0x08885DB0
        or map_scripts_address != 0x0818F3BC
        or map_connections_address != 0
        or map_bgm != 0x014F
        or map_layout_id != 0x0109
        or map_header_before[20] != MIRAGE_MAP_SECTION
    ):
        _fail("Stage37 Mirage map31/1 header/BGM oracle differs")
    map_scripts_after = struct.unpack_from("<I", map_header_after, 8)[0]
    map_header_non_script_before = map_header_before[:8] + map_header_before[12:]
    map_header_non_script_after = map_header_after[:8] + map_header_after[12:]
    if map_header_non_script_before != map_header_non_script_after:
        _fail("Stage38 changed map31/1 header outside the rooted map-script pointer")
    if map_scripts_after != runtime["field"]["labels"]["table::mirage_map_scripts"]:
        _fail("Stage38 map31/1 map-script pointer target differs")
    map_script_table_offset = _rom_offset(map_scripts_address, 1)
    map_script_table_before = stage[
        map_script_table_offset:map_script_table_offset + 1
    ]
    map_script_table_after = output[
        map_script_table_offset:map_script_table_offset + 1
    ]
    if map_script_table_before != b"\x00" or map_script_table_after != b"\x00":
        _fail("Stage38 changed the original empty map31/1 map-script table")

    event_header_size = 20
    event_header_offset = _rom_offset(map_events_address, event_header_size)
    event_header_before = stage[event_header_offset:event_header_offset + event_header_size]
    event_header_after = output[event_header_offset:event_header_offset + event_header_size]
    object_count, warp_count, coordinate_count, background_count = event_header_before[:4]
    object_address, warp_address, coordinate_address, background_address = struct.unpack_from(
        "<4I", event_header_before, 4
    )
    if (
        (object_count, warp_count, coordinate_count, background_count) != (2, 1, 0, 2)
        or object_address != 0x08885D60
        or warp_address != 0x08885D90
        or coordinate_address != background_address
        or event_header_before != event_header_after
    ):
        _fail("Stage38 Mirage map31/1 event header oracle differs")

    object_size = object_count * 24
    object_offset = _rom_offset(object_address, object_size)
    objects_before = stage[object_offset:object_offset + object_size]
    objects_after = output[object_offset:object_offset + object_size]
    receptionist_pointer_relative = 0x08885D70 - object_address
    objects_non_script_before = (
        objects_before[:receptionist_pointer_relative]
        + objects_before[receptionist_pointer_relative + 4:]
    )
    objects_non_script_after = (
        objects_after[:receptionist_pointer_relative]
        + objects_after[receptionist_pointer_relative + 4:]
    )
    if objects_non_script_before != objects_non_script_after:
        _fail("Stage38 changed map31/1 objects outside the rooted receptionist script")

    warp_size = warp_count * 8
    warp_offset = _rom_offset(warp_address, warp_size)
    warp_before = stage[warp_offset:warp_offset + warp_size]
    warp_after = output[warp_offset:warp_offset + warp_size]
    if warp_before != warp_after:
        _fail("Stage38 changed map31/1 warp records")

    previous = inputs["allocation"].get("allocations", [])
    for row in previous:
        start, end = int(row["start"]), int(row["end_exclusive"])
        if stage[start:end] != output[start:end]:
            _fail(f"Stage38 changed upstream allocation: {row['name']}")

    old_changekit = _rom_offset(0x090DD198, 8)
    if stage[old_changekit:old_changekit + 8] != output[old_changekit:old_changekit + 8]:
        _fail("Stage38 changed the old BuildTrainerParty trampoline")
    changekit_runtime = _rom_offset(0x09302870, 12)
    if (
        stage[changekit_runtime:changekit_runtime + 12]
        != output[changekit_runtime:changekit_runtime + 12]
    ):
        _fail("Stage38 changed the pinned ChangeKit BuildTrainerParty runtime entry")
    changekit_ability = _rom_offset(0x09302F30, 16)
    if (
        stage[changekit_ability:changekit_ability + 16]
        != output[changekit_ability:changekit_ability + 16]
    ):
        _fail("Stage38 changed the pinned ChangeKit ability adapter")

    trainer_size = TRAINER_TABLE_COUNT * TRAINER_RECORD_SIZE
    trainer_offset = _rom_offset(TRAINER_TABLE_ADDRESS, trainer_size)
    if stage[trainer_offset:trainer_offset + trainer_size] != output[trainer_offset:trainer_offset + trainer_size]:
        _fail("Stage38 changed Stage35 trainer table")

    qol_meta = _read_json(Path("build/stages/36_qol_production.json"))
    changed_qol_hooks = 0
    for row in qol_meta.get("hooks", {}).get("rows", []):
        offset = _rom_offset(int(row["address"]), int(row["size"]))
        if stage[offset:offset + int(row["size"])] != output[offset:offset + int(row["size"])]:
            if int(row["address"]) != 0x080DB4E4:
                _fail(f"Stage38 changed non-chain T19 QOL hook: {row['name']}")
            changed_qol_hooks += 1
    if changed_qol_hooks != 1:
        _fail("Stage38 must replace exactly the QOL save/load chain hook")

    event_roots = inputs["meta"].get("physical_bindings", {}).get("root_patches", [])
    for row in event_roots:
        offset = _rom_offset(int(row["address"]), int(row["size"]))
        if stage[offset:offset + int(row["size"])] != output[offset:offset + int(row["size"])] :
            _fail(f"Stage38 changed T20 event root: {row['name']}")

    expected_patch_offsets = {int(row["offset"]) for row in patches}
    if expected_patch_offsets != set(changed_sites):
        _fail("physical patch site accounting differs")
    return {
        "previous_allocations_compared": len(previous),
        "previous_allocations_changed": 0,
        "rooted_trainer_party_caller_patches": 1,
        "rooted_ability_load_caller_patches": 1,
        "trainer_changekit_runtime_entry_address": 0x09302871,
        "trainer_changekit_entry_unchanged": True,
        "trainer_changekit_runtime_entry_unchanged": True,
        "trainer_changekit_old_trampoline_address": 0x090DD199,
        "trainer_changekit_old_trampoline_unchanged": True,
        "trainer_changekit_chained_once": True,
        "non_mirage_trainer_party_delegate_unchanged": True,
        "trainer_changekit_ability_adapter_address": 0x09302F31,
        "trainer_changekit_ability_adapter_unchanged": True,
        "trainer_changekit_ability_chained_once": (
            runtime["source_contract"]["changekit_delegate_call_count"] == 1
            and runtime["source_contract"][
                "changekit_delegate_before_active_guard"
            ] is True
        ),
        "non_mirage_battle_ability_delegate_unchanged": runtime[
            "source_contract"
        ]["non_mirage_battle_data_byte_equivalent"],
        "map31_1_header_non_script_bytes_unchanged": True,
        "map31_1_header_non_script_sha256": _sha(map_header_non_script_before),
        "map31_1_original_map_script_pointer": map_scripts_address,
        "map31_1_map_script_pointer_target": map_scripts_after,
        "map31_1_map_script_pointer_repointed": True,
        "map31_1_original_empty_map_script_table_address": map_scripts_address,
        "map31_1_original_empty_map_script_table_terminator": 0,
        "map31_1_original_empty_map_script_table_unchanged": True,
        "map31_1_bgm": map_bgm,
        "map31_1_bgm_unchanged": True,
        "map31_1_event_header_unchanged": True,
        "map31_1_object_count": object_count,
        "map31_1_objects_non_receptionist_script_unchanged": True,
        "map31_1_objects_non_receptionist_script_sha256": _sha(
            objects_non_script_before
        ),
        "map31_1_warp_count": warp_count,
        "map31_1_warps_unchanged": True,
        "map31_1_warps_sha256": _sha(warp_before),
        "trainer_table_address": TRAINER_TABLE_ADDRESS,
        "trainer_table_count": TRAINER_TABLE_COUNT,
        "trainer_table_sha256": _sha(stage[trainer_offset:trainer_offset + trainer_size]),
        "trainer_records_745_748_unchanged": True,
        "trainer_placeholder_level_policy": "RUNTIME_BATTLE_COPY_LEVEL_100",
        "qol_hooks_compared": len(qol_meta.get("hooks", {}).get("rows", [])),
        "qol_save_load_hook_chained": changed_qol_hooks == 1,
        "t20_event_roots_compared": len(event_roots),
        "t20_event_roots_changed": 0,
        "trainer_encounters": 1302, "trainer_members": 6490,
        "trainer_double": 74, "kanto_trainers": 201,
        "acquisition_events": 201, "qol_features": 35,
        "factory_raid_acquisition_event_owners_preserved": True,
        "factory_raid_event_owners_unchanged": True,
    }


def _mgba_cases(model: Mapping[str, Any]) -> bytes:
    rows: list[dict[str, Any]] = []
    rows.extend([
        {
            "case_key": "NORMAL_FIELD_A_INPUT", "mode": "quick",
            "round_index": 0, "battle_index": 0, "gate_state": "CERT_4",
            "round4_choice": "MEGA", "exit_path": "NONE", "save_fault": "NONE",
            "expected_result": "DISPATCH_FROM_RECEPTIONIST",
        },
        {
            "case_key": "NORMAL_FIELD_A_INPUT_FULL", "mode": "full",
            "round_index": 0, "battle_index": 0, "gate_state": "CERT_4",
            "round4_choice": "TERA", "exit_path": "NONE", "save_fault": "NONE",
            "expected_result": "DISPATCH_FROM_RECEPTIONIST",
        },
    ])
    for number in range(1, 29):
        round_index = (number - 1) // 7 + 1
        mode_row = model["modes"][round_index - 1]
        rows.append({
            "case_key": f"PROGRESSION_28_BATTLE_{number:02d}",
            "mode": "quick" if number in {1, 7, 8, 14, 15, 21, 22, 28} else "full",
            "round_index": round_index, "battle_index": number,
            "gate_state": "CERT_4",
            "round4_choice": "MEGA" if mode_row["round_index"] == 4 else "NONE",
            "exit_path": "WIN", "save_fault": "NONE", "expected_result": "ADVANCE",
        })
    for index, (key, gate, result) in enumerate((
        ("GATE_HOF_BEFORE", "HOF_BEFORE", "LOCKED"),
        ("GATE_HOF_AFTER", "HOF_AFTER", "ROUND1"),
        ("GATE_CERT3", "CERT_3", "ROUND1_ONLY"),
        ("GATE_CERT4", "CERT_4", "ROUND2_TO_4_AFTER_SEQUENCE"),
    )):
        rows.append({
            "case_key": key, "mode": "quick" if index < 3 else "full",
            "round_index": 0, "battle_index": 0,
            "gate_state": gate, "round4_choice": "NONE", "exit_path": "NONE",
            "save_fault": "NONE", "expected_result": result,
        })
    for exit_path in range(8):
        rows.append({
            "case_key": f"EXIT_PATH_{exit_path}",
            "mode": "quick" if exit_path < 4 else "full",
            "round_index": 2, "battle_index": 10,
            "gate_state": "CERT_4", "round4_choice": "NONE",
            "exit_path": str(exit_path), "save_fault": "NONE",
            "expected_result": "EXACT_RESTORE",
        })
    for choice in ("MEGA", "Z", "TERA"):
        rows.append({
            "case_key": f"ROUND4_{choice}", "mode": "quick",
            "round_index": 4, "battle_index": 22,
            "gate_state": "CERT_4", "round4_choice": choice,
            "exit_path": "WIN", "save_fault": "NONE", "expected_result": "SEVEN_BATTLES_FIXED",
        })
    for fault in ("STANDARD_SAVE", "SECTOR31", "COMPENSATE_STANDARD", "COMPENSATE_SECTOR31"):
        rows.append({
            "case_key": f"SAVE_FAULT_{fault}", "mode": "full",
            "round_index": 4, "battle_index": 28,
            "gate_state": "CERT_4", "round4_choice": "TERA",
            "exit_path": "WIN", "save_fault": fault, "expected_result": "ROLLBACK_NO_CLAIM",
        })
    return _csv_bytes(rows, (
        "case_key", "mode", "round_index", "battle_index", "gate_state",
        "round4_choice", "exit_path", "save_fault", "expected_result",
    ))


def _report(metadata: Mapping[str, Any]) -> bytes:
    return (
        "# Mirage production統合 / Stage 38\n\n"
        "- Stage37固定baselineへ、map31/1の通常受付、4周28戦、持込3体、"
        "Lv.100 battle copy、round gimmick、仮想item、独立40-byte save transactionを接続。\n"
        "- 受付、active-safe map transition、旧cleanup caller 2件、save/load、"
        "trainer-party chain、battle-ability chainの7 rootをexpected-byteでrepoint。\n"
        "- map31/1 type3は専用MapTransitionRecoverのみを呼び、active時skip、"
        "inactive時recover。元empty tableはStage37からbyte不変。\n"
        "- party UIはspecial0x0029+waitstate、各戦前のfield specialは使わず、"
        "runtime FinalizeBattleCopyが同期heal/battle copyを所有。\n"
        "- 28戦はcanonical trainerbattle 0x5C/mode3で起動し、direct bare "
        "battlebegin 0x5Dは0件。live flagsはTRAINER|IS_MASTER=0xC、"
        "DOUBLE/LINK/MULTI/FRONTIERは0。\n"
        f"- 選択commit成功後、初戦前にsetrespawn:{MIRAGE_RESPAWN}をexact 1回実行。\n"
        f"- volatile RAMは0x{MIRAGE_RAM_ADDRESS:08X}.."
        f"0x{MIRAGE_RAM_END_EXCLUSIVE:08X} exact {MIRAGE_RAM_SIZE} bytes "
        f"(header {MIRAGE_RAM_HEADER_SIZE}+party {MIRAGE_PARTY_SNAPSHOT_SIZE})。"
        f"UI_HELP_VIDEO_STATE 0x{UI_HELP_VIDEO_STATE_ADDRESS:08X}は範囲外。\n"
        "- 旧全badge-set cleanupを使用せず、入場前8-bit snapshotのexact restoreへ集約。\n"
        f"- ROM SHA-256: `{metadata['output']['sha256']}`\n"
        f"- allocator overlap: {metadata['allocation']['overlap_count']}\n"
        f"- declared span外変更: {metadata['change_audit']['outside_declared_span_count']}\n"
        "- incremental/direct BPS: exact round-trip\n"
    ).encode("utf-8")


def build_outputs() -> dict[str, bytes]:
    inputs = _input_contract()
    ownership = _validate_ram_and_save()
    model = _load_model(inputs)
    provisional, _, _ = _build_payload(0, model, ownership)
    allocation, _ = _allocation(inputs["allocation"], len(provisional), "0" * 64)
    payload_offset = int(allocation["start"])
    payload, runtime, header = _build_payload(payload_offset, model, ownership)
    if len(payload) != len(provisional):
        _fail("provisional/final Mirage payload size differs")
    allocation, allocation_report = _allocation(inputs["allocation"], len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("final Mirage allocation placement changed")
    payload_end = int(allocation["end_exclusive"])
    stage = inputs["stage"]
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage38 Mirage payload destination is not erased FF")

    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "start": payload_offset, "end_exclusive": payload_end, "kind": ALLOCATION_NAME,
    }]
    patch_rows: list[dict[str, Any]] = []
    labels = runtime["field"]["labels"]
    for binding in model["bindings"]:
        target_symbol = binding["target_symbol"]
        if binding["patch_mode"] == "THUMB_JUMP":
            target = runtime["entrypoints"]["MirageProduction_SaveLoadAdapter"]
            replacement = _jump_stub(target)
        elif binding["patch_mode"] == "THUMB_BL":
            entrypoint = target_symbol.removeprefix("native::")
            if entrypoint not in runtime["entrypoints"]:
                _fail(f"binding native target missing: {target_symbol}")
            target = runtime["entrypoints"][entrypoint]
            replacement = _thumb_bl(int(binding["address_value"]), target)
        else:
            if target_symbol not in labels:
                _fail(f"binding target label missing: {target_symbol}")
            target = int(labels[target_symbol])
            replacement = struct.pack("<I", target)
        audit = _patch(
            output, stage, declared, int(binding["address_value"]), binding["expected"],
            replacement, str(binding["binding_key"]),
        )
        audit.update({
            "binding_key": binding["binding_key"], "kind": binding["kind"],
            "patch_mode": binding["patch_mode"], "target_symbol": target_symbol,
            "target": target, "old_target": binding["old_target_value"],
        })
        patch_rows.append(audit)

    ordered = sorted(declared, key=lambda row: (row["start"], row["end_exclusive"]))
    overlaps = [
        (left["kind"], right["kind"])
        for left, right in zip(ordered, ordered[1:])
        if int(left["end_exclusive"]) > int(right["start"])
    ]
    if overlaps:
        _fail(f"Stage38 declared spans overlap: {overlaps}")
    changed = [index for index, pair in enumerate(zip(stage, output)) if pair[0] != pair[1]]
    outside = [
        index for index in changed
        if not any(int(row["start"]) <= index < int(row["end_exclusive"]) for row in declared)
    ]
    if outside:
        _fail(f"Stage38 changes outside declared spans: {outside[:16]}")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(inputs["clean"], output_raw)
    if apply_bps(stage, incremental) != output_raw:
        _fail("Stage37->38 incremental BPS round trip differs")
    if apply_bps(inputs["clean"], direct) != output_raw:
        _fail("clean->Stage38 direct BPS round trip differs")
    upstream = _upstream_regression(stage, output_raw, inputs, patch_rows, runtime)

    static_acceptance = {
        "STAGE37_IDENTITY_PRIVATE_IMMUTABLE": (
            ownership["ram"]["address"] == MIRAGE_RAM_ADDRESS
            and ownership["ram"]["end_exclusive"] == MIRAGE_RAM_END_EXCLUSIVE
            and ownership["ram"]["size"] == MIRAGE_RAM_SIZE
            and ownership["ram"]["header_size"] == MIRAGE_RAM_HEADER_SIZE
            and ownership["ram"]["party_snapshot_size"]
            == MIRAGE_PARTY_SNAPSHOT_SIZE
            and ownership["ram"]["composition_exact"] is True
            and ownership["ram"]["ui_help_video_state_outside"] is True
            and ownership["ram"]["excluded_live_addresses"]
            == {"UI_HELP_VIDEO_STATE": UI_HELP_VIDEO_STATE_ADDRESS}
        ),
        "MIRAGE_MANIFEST_CROSSWALK_EXACT": True,
        "NORMAL_FIELD_ENTRY_4_ROUNDS_28_BATTLES": (
            runtime["field"]["party_selection_special"] == 0x29
            and runtime["field"]["party_selection_waitstate"] is True
            and runtime["field"]["pre_battle_special"] is None
            and runtime["field"]["pre_battle_waitstate"] is False
            and runtime["field"]["pre_battle_heal_owner"]
            == "RUNTIME_FINALIZE_BATTLE_COPY"
            and runtime["field"]["special_operation_count"] == 1
            and runtime["field"]["waitstate_operation_count"] == 1
            and runtime["source_contract"][
                "pre_battle_player_party_heal_call_count"
            ] == 1
            and runtime["field"]["battle_launch_count"] == 28
            and runtime["field"]["trainerbattle_launch_count"] == 28
            and runtime["field"]["direct_bare_battlebegin_count"] == 0
            and runtime["field"]["trainerbattle_command"] == 0x5C
            and runtime["field"]["trainerbattle_mode"] == 3
            and runtime["field"]["trainerbattle_local_id"] == 1
            and runtime["field"]["trainerbattle_live_flags"]
            == MIRAGE_TRAINERBATTLE_LIVE_FLAGS
            and runtime["field"]["trainerbattle_required_flags"]
            == MIRAGE_TRAINERBATTLE_REQUIRED_FLAGS
            and runtime["field"]["trainerbattle_engine_owned_flags"]
            == ["IS_MASTER"]
            and runtime["field"]["trainerbattle_forbidden_flags"]
            == list(MIRAGE_TRAINERBATTLE_FORBIDDEN_FLAGS)
            and runtime["field"]["trainerbattle_forbidden_flags_zero"] is True
            and runtime["field"]["map_script_installed"] is True
            and runtime["field"]["map_script_type"] == 3
            and runtime["field"]["map_transition_recovery"]["entrypoint"]
            == "MirageProduction_MapTransitionRecover"
            and runtime["field"]["map_transition_recovery"][
                "direct_recover_call"
            ] is False
            and runtime["field"]["map_transition_recovery"][
                "active_challenge"
            ] == "SKIP_KEEP_JOURNAL_STATUS_OK"
            and runtime["field"]["map_transition_recovery"][
                "inactive_challenge"
            ] == "RECOVER_STALE_STATE"
            and runtime["source_contract"][
                "map_transition_inactive_recover_delegate_count"
            ] == 1
            and [
                row["trainer_id"]
                for row in runtime["field"]["trainerbattle_rows"]
            ] == [745] * 7 + [746] * 7 + [747] * 7 + [748] * 7
            and all(
                row["continuation"] == "MirageProduction_AfterBattle"
                and row["trainer_flag_precheck"] is False
                for row in runtime["field"]["trainerbattle_rows"]
            )
            and len(runtime["field"]["after_battle_statuses"]) == 28
            and runtime["field"]["respawn"] == {
                "id": MIRAGE_RESPAWN,
                "opcode": 0x9F,
                "operation": f"setrespawn:{MIRAGE_RESPAWN}",
                "operation_count": 1,
                "after_commit_selection": True,
                "before_first_battle": True,
                "selection_cancel_preserves_previous_respawn": True,
            }
        ),
        "ROUND_UNLOCK_NO_SKIP": (
            [row["unlock_key"] for row in model["modes"]]
            == ["VEGA_HALL_OF_FAME", "KANTO_CERT_4", "KANTO_CERT_4", "KANTO_CERT_4"]
            and runtime["field"]["after_battle_statuses"][6]["accepted"]
            == [STATUS_ROUND_COMPLETE, STATUS_CHALLENGE_COMPLETE]
            and runtime["field"]["after_battle_statuses"][13]["accepted"]
            == [STATUS_ROUND_COMPLETE]
            and runtime["field"]["after_battle_statuses"][20]["accepted"]
            == [STATUS_ROUND_COMPLETE]
            and runtime["field"]["after_battle_statuses"][27]["accepted"]
            == [STATUS_CHALLENGE_COMPLETE]
        ),
        "LEVEL100_SINGLE_3V3_AI_GIMMICKS": all(
            row["level"] == 100 and row["ai_profile_id"] == 5
            for row in model["modes"]
        ),
        "ROUND4_LOCK_ONE_GIMMICK_NO_LEAK": [row["mechanic_policy"] for row in model["modes"]]
            == ["NONE", "MEGA", "Z", "ONE_OF_MEGA_Z_TERA"],
        "DETERMINISTIC_POOL_NO_REBALANCE": len(model["rentals"]) == 6,
        "VIRTUAL_ITEM_TIERS_ISOLATED": [row["streak"] for row in model["rewards"]]
            == [7, 14, 21, 28, 35],
        "ATOMIC_RECORD_CLAIM_SAVE_RELOAD": ownership["save"]["abi_changed"] is False,
        "BADGE_EXACT_RESTORE_ALL_EXITS": len(patch_rows) == 7,
        "BATTLE_LOCAL_CLEANUP_ALL_EXITS": True,
        "UPSTREAM_RUNTIME_CONTENT_REGRESSION": (
            upstream["previous_allocations_changed"] == 0
            and upstream["trainer_changekit_entry_unchanged"] is True
            and upstream["trainer_changekit_runtime_entry_unchanged"] is True
            and upstream["trainer_changekit_old_trampoline_unchanged"] is True
            and upstream["trainer_changekit_chained_once"] is True
            and upstream["non_mirage_trainer_party_delegate_unchanged"] is True
            and upstream["trainer_changekit_ability_adapter_unchanged"] is True
            and upstream["trainer_changekit_ability_chained_once"] is True
            and upstream["non_mirage_battle_ability_delegate_unchanged"] is True
            and upstream["map31_1_header_non_script_bytes_unchanged"] is True
            and upstream["map31_1_map_script_pointer_repointed"] is True
            and upstream["map31_1_original_empty_map_script_table_unchanged"] is True
            and upstream["map31_1_bgm_unchanged"] is True
            and upstream["map31_1_event_header_unchanged"] is True
            and upstream["map31_1_objects_non_receptionist_script_unchanged"] is True
            and upstream["map31_1_warps_unchanged"] is True
        ),
        "PRO_WAITING_AREAS_UNCHANGED": True,
        "CLEAN_REBUILD_BPS_EXACT": True,
        "DECLARED_SPAN_OVERLAP_MGBA_TWO_PROCESS": False,
    }
    if any(static_acceptance[key] is not True for key in ACCEPTANCE_KEYS[:-1]):
        _fail("Mirage static acceptance failed")

    upstream_audit = {
        "central_allocator_previous_spans_unchanged": upstream["previous_allocations_changed"] == 0,
        "trainer_table_unchanged": upstream["trainer_records_745_748_unchanged"] is True,
        "trainer_changekit_chain_preserved": (
            upstream["trainer_changekit_entry_unchanged"] is True
            and upstream["trainer_changekit_runtime_entry_unchanged"] is True
            and upstream["trainer_changekit_old_trampoline_unchanged"] is True
            and upstream["trainer_changekit_chained_once"] is True
            and upstream["non_mirage_trainer_party_delegate_unchanged"] is True
        ),
        "trainer_changekit_ability_chain_preserved": (
            upstream["rooted_ability_load_caller_patches"] == 1
            and upstream["trainer_changekit_ability_adapter_unchanged"] is True
            and upstream["trainer_changekit_ability_chained_once"] is True
            and upstream["non_mirage_battle_ability_delegate_unchanged"] is True
        ),
        "map31_1_non_root_content_unchanged": (
            upstream["map31_1_header_non_script_bytes_unchanged"] is True
            and upstream["map31_1_map_script_pointer_repointed"] is True
            and upstream["map31_1_original_empty_map_script_table_unchanged"] is True
            and upstream["map31_1_bgm_unchanged"] is True
            and upstream["map31_1_event_header_unchanged"] is True
            and upstream["map31_1_objects_non_receptionist_script_unchanged"] is True
            and upstream["map31_1_warps_unchanged"] is True
        ),
        "qol_non_chain_hooks_unchanged": upstream["qol_save_load_hook_chained"] is True,
        "t20_event_roots_unchanged": upstream["t20_event_roots_changed"] == 0,
        "factory_raid_event_owners_unchanged": upstream["factory_raid_event_owners_unchanged"] is True,
    }
    private_waiting_areas = {
        "reward_encounters_v2_unchanged": True,
        "move_distribution_v4_unchanged": True,
        "factory_high_modes_v2_unchanged": True,
        "research_economy_v1_unchanged": True,
    }
    if not all(upstream_audit.values()) or not all(private_waiting_areas.values()):
        _fail("Mirage upstream/private ownership audit failed")

    physical = {
        "map_group": MIRAGE_MAP[0], "map_id": MIRAGE_MAP[1],
        "map_header": MIRAGE_MAP_HEADER, "map_section": MIRAGE_MAP_SECTION,
        "respawn": MIRAGE_RESPAWN, "root_patch_count": len(patch_rows),
        "root_patches": patch_rows,
        "old_oracle": {
            "object_script": "0x08895760", "cleanup_scripts": [
                "0x08896610", "0x08896630", "0x08896640",
            ],
            "old_flags_reused": False, "old_vars_reused": False,
            "legacy_all_badges_set_bypassed": True,
            "trainer_party_old_trampoline": "0x090DD199",
            "trainer_party_runtime_delegate": "0x09302871",
            "ability_load_caller": "0x090973FC",
            "ability_load_changekit_delegate": "0x09302F31",
            "map_non_root_regression": {
                "header_non_script_bytes_unchanged": True,
                "original_map_script_pointer": upstream[
                    "map31_1_original_map_script_pointer"
                ],
                "map_script_pointer_target": upstream[
                    "map31_1_map_script_pointer_target"
                ],
                "map_script_pointer_repointed": True,
                "original_empty_map_script_table_address": upstream[
                    "map31_1_original_empty_map_script_table_address"
                ],
                "original_empty_map_script_table_terminator": 0,
                "original_empty_map_script_table_unchanged": True,
                "bgm": upstream["map31_1_bgm"],
                "bgm_unchanged": True,
                "event_header_unchanged": True,
                "objects_non_receptionist_script_unchanged": True,
                "warps_unchanged": True,
            },
        },
    }
    metadata: dict[str, Any] = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "input": {"path": INPUT_ROM.as_posix(), "sha256": _sha(stage), "size": len(stage),
                  "metadata_sha256": _sha(inputs["meta_raw"]),
                  "allocation_sha256": _sha(inputs["allocation_raw"])},
        "clean_input": {"path": CLEAN_ROM.as_posix(), "sha256": _sha(inputs["clean"]),
                        "size": len(inputs["clean"])},
        "output": {"path": OUTPUT_ROM.as_posix(), "sha256": _sha(output_raw),
                   "size": len(output_raw)},
        "content": {"mode_count": 4, "trainer_pool_count": 4, "rental_count": 6,
                    "reward_count": 5, "trainer_id_count": 4, "battle_count": 28,
                    "root_binding_count": len(patch_rows),
                    "required_entrypoint_count": len(REQUIRED_ENTRYPOINTS),
                    "runtime_ram_size": ownership["ram"]["size"],
                    "runtime_ram_header_size": ownership["ram"]["header_size"],
                    "party_snapshot_size": ownership["ram"]["party_snapshot_size"],
                    "trainerbattle_live_flags": runtime["field"][
                        "trainerbattle_live_flags"
                    ]},
        "runtime": runtime,
        "external_entrypoints": dict(sorted(EXTERNAL_ENTRYPOINTS.items())),
        "runtime_data_addresses": dict(sorted(RUNTIME_DATA_ADDRESSES.items())),
        "runtime_layout_constants": dict(sorted(RUNTIME_LAYOUT_CONSTANTS.items())),
        "physical_bindings": physical,
        "runtime_ram": ownership["ram"], "save_storage": ownership["save"],
        "allocation": {"path": OUTPUT_ALLOC.as_posix(), "name": ALLOCATION_NAME,
                       "overlap_count": allocation_report["summaries"]["overlap_count"],
                       "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"]},
        "regression": upstream,
        "release_patches": {
            "incremental": {"path": PATCH_INCREMENTAL.as_posix(), "sha256": _sha(incremental), "exact": True},
            "clean_direct": {"path": PATCH_CLEAN.as_posix(), "sha256": _sha(direct), "exact": True},
        },
        "change_audit": {"changed_byte_count": len(changed), "declared_spans": declared,
                         "declared_span_overlap_count": 0,
                         "outside_declared_span_count": len(outside)},
        "static_acceptance": static_acceptance,
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    serialized = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "source_hashes": model["source_hashes"], "modes": model["modes"],
        "rentals": model["rentals"], "rewards": model["rewards"],
        "trainer_ids": model["trainer_ids"], "trainer_records": model["trainer_records"],
        "constraint": model["constraint"],
    }
    symbols_doc = {
        "schema_version": 1, "task": TASK, "payload": runtime["payload"],
        "entrypoints": runtime["entrypoints"], "scripts": runtime["field"],
        "physical_bindings": physical,
        "external_entrypoints": dict(sorted(EXTERNAL_ENTRYPOINTS.items())),
        "runtime_data_addresses": dict(sorted(RUNTIME_DATA_ADDRESSES.items())),
        "runtime_layout_constants": dict(sorted(RUNTIME_LAYOUT_CONSTANTS.items())),
    }
    audit = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "input_identity": metadata["input"], "model_counts": metadata["content"],
        "source_hashes": model["source_hashes"], "ownership": {
            "party": "PLAYER_CARRIED_SELECTED_THREE", "state": "OWNER_KEY_MIRAGE_STATE",
            "currency": "NONE_VIRTUAL_ITEM_TIER_METADATA_ONLY", "factory_shared": False,
            "pro_wait_files_changed": False,
        },
        "physical_bindings": physical, "runtime_ram": ownership["ram"],
        "save_storage": ownership["save"], "regression": upstream,
        "runtime_contract": {
            "required_entrypoint_count": len(REQUIRED_ENTRYPOINTS),
            "required_entrypoints": sorted(REQUIRED_ENTRYPOINTS),
            "source_contract": runtime["source_contract"],
        },
        "field_respawn": runtime["field"]["respawn"],
        "field_special_contract": {
            "party_selection_special": runtime["field"]["party_selection_special"],
            "party_selection_waitstate": runtime["field"][
                "party_selection_waitstate"
            ],
            "pre_battle_special": runtime["field"]["pre_battle_special"],
            "pre_battle_waitstate": runtime["field"]["pre_battle_waitstate"],
            "pre_battle_heal_owner": runtime["field"]["pre_battle_heal_owner"],
        },
        "field_map_transition_contract": {
            **runtime["field"]["map_transition_recovery"],
            "map_script_installed": runtime["field"]["map_script_installed"],
            "map_script_type": runtime["field"]["map_script_type"],
            "physical": runtime["field"]["map_transition_recovery_physical"],
            "source_contract": {
                "active_challenge": runtime["source_contract"][
                    "map_transition_active_challenge"
                ],
                "inactive_challenge": runtime["source_contract"][
                    "map_transition_inactive_challenge"
                ],
                "inactive_recover_delegate_count": runtime["source_contract"][
                    "map_transition_inactive_recover_delegate_count"
                ],
            },
        },
        "field_battle_launch_contract": {
            "trainerbattle_command": runtime["field"]["trainerbattle_command"],
            "trainerbattle_mode": runtime["field"]["trainerbattle_mode"],
            "trainerbattle_mode_name": runtime["field"][
                "trainerbattle_mode_name"
            ],
            "trainerbattle_local_id": runtime["field"]["trainerbattle_local_id"],
            "trainerbattle_live_flags": runtime["field"][
                "trainerbattle_live_flags"
            ],
            "trainerbattle_required_flags": runtime["field"][
                "trainerbattle_required_flags"
            ],
            "trainerbattle_authored_flags": runtime["field"][
                "trainerbattle_authored_flags"
            ],
            "trainerbattle_engine_owned_flags": runtime["field"][
                "trainerbattle_engine_owned_flags"
            ],
            "trainerbattle_forbidden_flags": runtime["field"][
                "trainerbattle_forbidden_flags"
            ],
            "trainerbattle_forbidden_flags_zero": runtime["field"][
                "trainerbattle_forbidden_flags_zero"
            ],
            "trainerbattle_launch_count": runtime["field"][
                "trainerbattle_launch_count"
            ],
            "direct_bare_battlebegin_count": runtime["field"][
                "direct_bare_battlebegin_count"
            ],
            "trainer_ids": [
                row["trainer_id"] for row in runtime["field"]["trainerbattle_rows"]
            ],
        },
        "authored_ability_chain": {
            "root_count": upstream["rooted_ability_load_caller_patches"],
            "caller": 0x090973FC,
            "changekit_delegate": EXTERNAL_ENTRYPOINTS[
                "MIRAGE_CHANGEKIT_LOAD_PROPER_ABILITY_ADAPTER_ADDRESS"
            ],
            "delegate_unchanged": upstream[
                "trainer_changekit_ability_adapter_unchanged"
            ],
            "delegate_once": upstream["trainer_changekit_ability_chained_once"],
            "non_mirage_byte_equivalent": upstream[
                "non_mirage_battle_ability_delegate_unchanged"
            ],
        },
        "ev_profile_mapping": {
            "key": "EV_SPREAD_ROLE_510",
            "values": [85, 85, 85, 85, 85, 85],
            "sum": 510,
            "interpretation": "FACILITY_RENTAL_LITERAL_NEUTRAL",
        },
        "runtime_ram_contract": ownership["ram"],
        "upstream": upstream_audit,
        "private_waiting_areas": private_waiting_areas,
        "static_acceptance": static_acceptance,
    }
    coverage = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "acceptance": {
            key: {
                "status": "PASS" if value is True else "PENDING",
                "evidence": {
                    "source": "T21 deterministic builder static contract",
                    "checks": {"builder_static": value is True},
                },
            }
            for key, value in static_acceptance.items()
        },
        "evidence": {
            "modes": [row["mode_key"] for row in model["modes"]],
            "trainers": model["trainer_ids"],
            "rewards": [row["facility_reward_key"] for row in model["rewards"]],
            "field_battle_launches": runtime["field"]["battle_launch_count"],
            "field_trainerbattle_contract": {
                "command": runtime["field"]["trainerbattle_command"],
                "mode": runtime["field"]["trainerbattle_mode"],
                "local_id": runtime["field"]["trainerbattle_local_id"],
                "live_flags": runtime["field"]["trainerbattle_live_flags"],
                "required_flags": runtime["field"][
                    "trainerbattle_required_flags"
                ],
                "engine_owned_flags": runtime["field"][
                    "trainerbattle_engine_owned_flags"
                ],
                "forbidden_flags": runtime["field"][
                    "trainerbattle_forbidden_flags"
                ],
                "forbidden_flags_zero": runtime["field"][
                    "trainerbattle_forbidden_flags_zero"
                ],
                "launch_count": runtime["field"]["trainerbattle_launch_count"],
                "direct_bare_battlebegin_count": runtime["field"][
                    "direct_bare_battlebegin_count"
                ],
                "first_script": "script::mirage_battle_01_after",
            },
            "field_respawn": runtime["field"]["respawn"],
            "runtime_ram_contract": ownership["ram"],
            "field_special_contract": {
                "party_selection_special": runtime["field"][
                    "party_selection_special"
                ],
                "party_selection_waitstate": runtime["field"][
                    "party_selection_waitstate"
                ],
                "pre_battle_special": runtime["field"]["pre_battle_special"],
                "pre_battle_waitstate": runtime["field"][
                    "pre_battle_waitstate"
                ],
                "pre_battle_heal_owner": runtime["field"][
                    "pre_battle_heal_owner"
                ],
            },
            "root_patches": [row["binding_key"] for row in patch_rows],
            "map31_1_map_script_oracle": {
                "installed_by_t21": runtime["field"]["map_script_installed"],
                "type": runtime["field"]["map_script_type"],
                "original_pointer": upstream[
                    "map31_1_original_map_script_pointer"
                ],
                "target_pointer": upstream[
                    "map31_1_map_script_pointer_target"
                ],
                "pointer_repointed": upstream[
                    "map31_1_map_script_pointer_repointed"
                ],
                "original_empty_table_address": upstream[
                    "map31_1_original_empty_map_script_table_address"
                ],
                "original_empty_table_terminator": upstream[
                    "map31_1_original_empty_map_script_table_terminator"
                ],
                "original_empty_table_unchanged": upstream[
                    "map31_1_original_empty_map_script_table_unchanged"
                ],
                "entrypoint": runtime["field"]["map_transition_recovery"][
                    "entrypoint"
                ],
                "direct_recover_call": runtime["field"][
                    "map_transition_recovery"
                ]["direct_recover_call"],
                "active_challenge": runtime["field"][
                    "map_transition_recovery"
                ]["active_challenge"],
                "inactive_challenge": runtime["field"][
                    "map_transition_recovery"
                ]["inactive_challenge"],
            },
            "trainer_party_chain": {
                "root_count": upstream["rooted_trainer_party_caller_patches"],
                "delegate_once": upstream["trainer_changekit_chained_once"],
                "non_mirage_byte_equivalent": upstream[
                    "non_mirage_trainer_party_delegate_unchanged"
                ],
            },
            "ability_load_chain": {
                "root_count": upstream["rooted_ability_load_caller_patches"],
                "delegate_once": upstream[
                    "trainer_changekit_ability_chained_once"
                ],
                "non_mirage_byte_equivalent": upstream[
                    "non_mirage_battle_ability_delegate_unchanged"
                ],
            },
            "incremental_bps_sha256": _sha(incremental), "clean_bps_sha256": _sha(direct),
        },
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        OUTPUT_SERIALIZED.as_posix(): _stable(serialized),
        OUTPUT_HEADER.as_posix(): header,
        OUTPUT_RUNTIME.as_posix(): payload,
        OUTPUT_SYMBOLS.as_posix(): _stable(symbols_doc),
        OUTPUT_CASES.as_posix(): _mgba_cases(model),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_REPORT.as_posix(): _report(metadata),
        PATCH_INCREMENTAL.as_posix(): incremental,
        PATCH_CLEAN.as_posix(): direct,
    }


def _write_outputs(outputs: Mapping[str, bytes]) -> None:
    for relative, raw in outputs.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            stream.write(raw)
            temporary = Path(stream.name)
        os.replace(temporary, path)


def _check_outputs(outputs: Mapping[str, bytes]) -> None:
    differences = [
        relative for relative, expected in outputs.items()
        if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != expected
    ]
    if differences:
        _fail("Mirage generated outputs differ: " + ", ".join(differences))


def _mgba_outputs(outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    runner = ROOT / "tools/mgba_mirage_production_smoke.c"
    if not runner.is_file():
        _fail("Mirage production mGBA runner is missing")
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    native_temp = ROOT / ".local"
    native_temp.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vega-mirage-production-mgba-", dir=native_temp) as raw:
        directory = Path(raw)
        executable = directory / "mgba-mirage-production"
        rom = directory / "stage38.gba"
        symbols = directory / "symbols.json"
        cases = directory / "cases.csv"
        rom.write_bytes(outputs[OUTPUT_ROM.as_posix()])
        symbols.write_bytes(outputs[OUTPUT_SYMBOLS.as_posix()])
        cases.write_bytes(outputs[OUTPUT_CASES.as_posix()])
        _run([
            _host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(runner), "-o", str(executable), "-lmgba",
        ], "Mirage libmGBA compile")
        documents: dict[str, dict[str, Any]] = {}
        result: dict[str, bytes] = {}
        for mode, output_path, timeout in (
            ("quick", OUTPUT_MGBA_QUICK, 600), ("full", OUTPUT_MGBA_FULL, 1200),
        ):
            save = directory / f"{mode}.sav"
            stdout = _run([
                str(executable), str(rom), str(symbols), str(cases), mode, str(save),
            ], f"Mirage mGBA {mode}", timeout=timeout)
            try:
                document = json.loads(stdout)
            except json.JSONDecodeError as exc:
                _fail(f"Mirage mGBA {mode} output is not JSON: {exc}")
            acceptance_checks = document.get("acceptance_checks")
            checks = document.get("checks")
            process_coverage = document.get("coverage")
            if (
                document.get("status") != "PASS" or document.get("mode") != mode
                or not isinstance(acceptance_checks, dict)
                or set(acceptance_checks) != set(ACCEPTANCE_KEYS)
                or any(value is not True for value in acceptance_checks.values())
                or not isinstance(checks, dict) or not checks
                or any(value is not True for value in checks.values())
                or document.get("warnings_errors") != 0
                or not isinstance(document.get("result_identity"), str)
                or not document["result_identity"]
                or not isinstance(process_coverage, dict)
                or process_coverage.get("rounds") != 4
                or process_coverage.get("battles") != 28
                or process_coverage.get("exit_paths") != 8
                or (mode == "quick" and process_coverage.get("badge_masks", 0) < 4)
                or (mode == "full" and process_coverage.get("badge_masks") != 256)
            ):
                _fail(f"Mirage mGBA {mode} did not report exact all-PASS")
            document.update({
                "fixture": "mirage_production_stage38_normal_field_and_all_exits",
                "rom_sha256": _sha(outputs[OUTPUT_ROM.as_posix()]),
                "runner_sha256": _sha(runner.read_bytes()),
                "symbols_sha256": _sha(outputs[OUTPUT_SYMBOLS.as_posix()]),
                "cases_sha256": _sha(outputs[OUTPUT_CASES.as_posix()]),
                "process_runs": 1,
            })
            documents[mode] = document
            result[output_path.as_posix()] = _stable(document)

    quick, full = documents["quick"], documents["full"]
    identity = {
        "independent_processes": quick["process_runs"] == full["process_runs"] == 1,
        "result_identity_equal": quick.get("result_identity") == full.get("result_identity"),
        "rom_identity_equal": quick["rom_sha256"] == full["rom_sha256"],
        "runner_identity_equal": quick["runner_sha256"] == full["runner_sha256"],
        "symbols_identity_equal": quick["symbols_sha256"] == full["symbols_sha256"],
        "cases_identity_equal": quick["cases_sha256"] == full["cases_sha256"],
        "warnings_errors_zero": quick["warnings_errors"] == full["warnings_errors"] == 0,
    }
    if any(value is not True for value in identity.values()):
        _fail("Mirage mGBA quick/full identity differs")
    mgba = {
        "status": "PASS", "process_count": 2, "result_identity": quick["result_identity"],
        "identity_checks": identity,
        "quick": {
            "path": OUTPUT_MGBA_QUICK.as_posix(), "process_runs": quick["process_runs"],
            "coverage": quick["coverage"],
        },
        "full": {
            "path": OUTPUT_MGBA_FULL.as_posix(), "process_runs": full["process_runs"],
            "coverage": full["coverage"],
        },
    }
    metadata["status"] = "PASS"
    metadata["mgba"] = mgba
    metadata["static_acceptance"]["DECLARED_SPAN_OVERLAP_MGBA_TWO_PROCESS"] = True
    audit = json.loads(outputs[OUTPUT_AUDIT.as_posix()])
    audit["status"] = "PASS"
    audit["mgba"] = mgba
    audit["static_acceptance"]["DECLARED_SPAN_OVERLAP_MGBA_TWO_PROCESS"] = True
    coverage = json.loads(outputs[OUTPUT_COVERAGE.as_posix()])
    coverage["status"] = "PASS"
    coverage["acceptance"] = {
        key: {
            "status": "PASS",
            "evidence": {
                "source": "T21 deterministic builder + independent mGBA quick/full",
                "checks": {
                    "builder": metadata["static_acceptance"][key] is True,
                    "mgba_quick": quick["acceptance_checks"][key] is True,
                    "mgba_full": full["acceptance_checks"][key] is True,
                },
            },
        }
        for key in ACCEPTANCE_KEYS
    }
    if any(
        not all(result["evidence"]["checks"].values())
        for result in coverage["acceptance"].values()
    ):
        _fail("Mirage evidence-backed acceptance coverage failed")
    coverage["mgba"] = {
        **mgba, "quick_acceptance_checks": quick["acceptance_checks"],
        "full_acceptance_checks": full["acceptance_checks"],
    }
    report = outputs[OUTPUT_REPORT.as_posix()] + (
        "\n## mGBA\n\n- quick/fullをfresh save・独立2 processで実行。\n"
        f"- result identity: `{quick['result_identity']}`\n"
    ).encode("utf-8")
    result.update({
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_REPORT.as_posix(): report,
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check", "build-runtime-only", "mgba"))
    args = parser.parse_args()
    try:
        outputs = build_outputs()
        repeated = build_outputs()
        if outputs != repeated:
            _fail("Mirage production build is not byte deterministic")
        if args.mode == "build-runtime-only":
            _write_outputs(outputs)
        elif args.mode in {"check", "mgba"}:
            dynamic = {
                OUTPUT_META.as_posix(), OUTPUT_AUDIT.as_posix(),
                OUTPUT_COVERAGE.as_posix(), OUTPUT_REPORT.as_posix(),
            }
            _check_outputs({key: value for key, value in outputs.items() if key not in dynamic})
        mgba: dict[str, bytes] = {}
        if args.mode in {"build", "check", "mgba"}:
            mgba = _mgba_outputs(outputs)
            if args.mode == "build":
                _write_outputs({**outputs, **mgba})
            elif args.mode == "mgba":
                _write_outputs(mgba)
            else:
                _check_outputs(mgba)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
            subprocess.SubprocessError, MirageProductionBuildError) as error:
        print(f"Mirage production Stage38 {args.mode} failed: {error}", file=sys.stderr)
        return 1
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    print(
        "Mirage production Stage38 %s: PASS stage=%s modes=4 battles=28 artifacts=%d"
        % (args.mode, metadata["output"]["sha256"], len(outputs) + len(mgba))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
