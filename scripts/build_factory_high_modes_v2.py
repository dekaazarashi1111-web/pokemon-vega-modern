#!/usr/bin/env python3
"""Factory High Modes V2をStage 41へproduction統合しStage 42を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import os
import re
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_mirage_production import _charmap, _encode_text  # noqa: E402
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
from tools.regression.rom_runtime import _Blob  # noqa: E402
from tools.release.bps import apply_bps, create_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "T25"
CONFIG = Path("config/factory_high_modes_v2.json")
ROM_SIZE = 32 * 1024 * 1024
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "factory_high_modes_v2_stage42_payload"

OUTPUT_MODEL = Path("content/factory_high_modes_v2/canonical_model.json")
OUTPUT_HEADER = Path("generated/runtime/factory_high_modes_v2_generated.h")
OUTPUT_RUNTIME = Path("generated/runtime/factory_high_modes_v2_runtime.bin")
OUTPUT_SYMBOLS = Path("generated/runtime/factory_high_modes_v2_symbols.json")
OUTPUT_CASES = Path("generated/runtime/factory_high_modes_v2_mgba_cases.json")
OUTPUT_AUDIT = Path("reports/generated/factory_high_modes_v2_audit.json")
OUTPUT_COVERAGE = Path("reports/generated/factory_high_modes_v2_coverage.json")
OUTPUT_REPORT = Path("reports/generated/factory_high_modes_v2.md")
OUTPUT_ROM = Path("build/stages/42_factory_high_modes_v2.gba")
OUTPUT_META = Path("build/stages/42_factory_high_modes_v2.json")
OUTPUT_ALLOC = Path("build/stages/42_allocation.json")
OUTPUT_INCREMENTAL = Path(
    "build/patches/reward-encounters-stage41-to-factory-high-modes-stage42.bps"
)
OUTPUT_CLEAN_BPS = Path(
    "build/patches/firered-jpn-rev0-to-factory-high-modes-stage42.bps"
)
OUTPUT_MODE_MATRIX = Path("build/stages/42_factory_high_modes_v2_mode_matrix.json")
OUTPUT_MGBA_QUICK = Path("build/stages/42_mgba_factory_high_modes_v2_quick.json")
OUTPUT_MGBA_FULL = Path("build/stages/42_mgba_factory_high_modes_v2_full.json")

EXPECTED_MEMBERS = {
    "DESIGN_BIBLE_JA.md",
    "OPEN_QUESTIONS.md",
    "SUBMISSION_MANIFEST.json",
    "VALIDATION_REPORT.json",
    "dialogue.csv",
    "implementation_batches.csv",
    "mode_coverage.csv",
    "mode_matrix.csv",
    "opponent_profiles.csv",
    "reception_flow.json",
    "rental_sets.csv",
    "reward_schedule.csv",
    "runtime_state_machine.json",
}
CSV_MEMBERS = (
    "mode_matrix.csv",
    "mode_coverage.csv",
    "rental_sets.csv",
    "opponent_profiles.csv",
    "reward_schedule.csv",
    "dialogue.csv",
    "implementation_batches.csv",
)
REQUIRED_ENTRYPOINTS = {
    "FactoryHighModesV2_Probe",
    "FactoryHighModesV2_FieldReception",
    "FactoryHighModesV2_FieldDraft",
    "FactoryHighModesV2_EnterSelected",
    "FactoryHighModesV2_CommitSelection",
    "FactoryHighModesV2_PrepareBattle",
    "FactoryHighModesV2_AfterBattle",
    "FactoryHighModesV2_BeginExchange",
    "FactoryHighModesV2_CommitExchange",
    "FactoryHighModesV2_SkipExchange",
    "FactoryHighModesV2_Retire",
    "FactoryHighModesV2_Abort",
    "FactoryHighModesV2_Recover",
    "FactoryHighModesV2_TrialCompleteAdapter",
    "FactoryHighModesV2_BuildTrainerPartyAdapter",
    "FactoryHighModesV2_LoadProperAbilityBattleDataAdapter",
    "FactoryHighModesV2_SaveLoadAdapter",
    "FactoryHighModesV2_TestInitialize",
    "FactoryHighModesV2_TestSetUnlocks",
    "FactoryHighModesV2_TestEnter",
    "FactoryHighModesV2_TestCommitDraft",
    "FactoryHighModesV2_TestBattleResult",
    "FactoryHighModesV2_TestSetPersistenceFault",
    "FactoryHighModesV2_TestReload",
    "FactoryHighModesV2_TestSetStreak",
    "FactoryHighModesV2_TestGeneratorAudit",
    "FactoryHighModesV2_TestPartyHash",
}

ACCEPTANCE_KEYS = (
    "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
    "CANONICAL_COUNTS_EXACT",
    "TRIAL_SLOT0_BYTE_RUNTIME_COMPATIBLE",
    "UNLOCK_UI_SAVE_GUARD",
    "ALL_MODE_RULES_EXACT",
    "FINITE_GENERATOR_ANTI_REROLL",
    "FORFEIT_RESTORE_RETIRE_EXACT",
    "REWARD_BP_CLAIM_CREDIT_ATOMIC",
    "FACTORY_ISOLATION_GIMMICK_LIMIT",
    "UPSTREAM_REGRESSION_ZERO",
    "DECLARED_SPAN_OVERLAP_ZERO_CLEAN_BPS_MGBA",
)

TIER_ORDER = ("TRIAL", "STANDARD", "FULL", "MASTER")
TIER_ID = {key: index for index, key in enumerate(TIER_ORDER)}
UNLOCK_ID = {
    "KANTO_EARLY_ACCESS": 0,
    "FACTORY_STANDARD": 1,
    "FACTORY_FULL": 2,
    "FACTORY_MASTER": 3,
}
AI_ID = {"AI_BASIC": 0, "AI_SEMI_SMART": 1, "AI_FULL_SMART": 2}
FORMAT_ID = {
    "SINGLE_3V3": 0,
    "DOUBLE_3V3": 1,
    "DOUBLE_4V4": 1,
    "NPC_PARTNER_MULTI_6V6": 2,
    "RANDOM_SINGLE_3V3": 3,
    "LITTLE_SINGLE_3V3": 4,
    "MONOTYPE_SINGLE_3V3": 5,
    "OU_SINGLE_3V3": 6,
    "CAMOMONS_SINGLE_3V3": 7,
    "UNRESTRICTED_SINGLE_3V3": 8,
    "GS_DOUBLE_4V4": 9,
    "REGION_MIX_SINGLE_3V3": 10,
    "ULTIMATE_SINGLE_4V4": 11,
}
ORIGIN_ID = {"OFFICIAL": 0, "VEGA": 1, "SPECIAL": 2}
GIMMICK_ID = {"NONE": 0, "MEGA": 1, "Z": 2, "DYNAMAX": 3, "TERA": 4}
NATURE_ORDER = (
    "NATURE_HARDY", "NATURE_LONELY", "NATURE_BRAVE", "NATURE_ADAMANT",
    "NATURE_NAUGHTY", "NATURE_BOLD", "NATURE_DOCILE", "NATURE_RELAXED",
    "NATURE_IMPISH", "NATURE_LAX", "NATURE_TIMID", "NATURE_HASTY",
    "NATURE_SERIOUS", "NATURE_JOLLY", "NATURE_NAIVE", "NATURE_MODEST",
    "NATURE_MILD", "NATURE_QUIET", "NATURE_BASHFUL", "NATURE_RASH",
    "NATURE_CALM", "NATURE_GENTLE", "NATURE_SASSY", "NATURE_CAREFUL",
    "NATURE_QUIRKY",
)
NATURE_ID = {key: index for index, key in enumerate(NATURE_ORDER)}
CLAIM_BITS = {
    "CLAIM_KEY_FACTORY_TRIAL_XS": 1,
    "CLAIM_KEY_FACTORY_TRIAL_S": 2,
    "CLAIM_KEY_FACTORY_TRIAL_ORAN": 10,
    "CLAIM_KEY_STANDARD_STREAK_14": 11,
    "CLAIM_KEY_STANDARD_STREAK_21": 12,
    "CLAIM_KEY_STANDARD_FIRST_CLEAR": 13,
    "CLAIM_KEY_FULL_STREAK_21": 14,
    "CLAIM_KEY_FULL_STREAK_49": 15,
    "CLAIM_KEY_FULL_FIRST_CLEAR": 16,
    "CLAIM_KEY_STREAK_049_EVENT": 8,
    "CLAIM_KEY_STREAK_100_SHINY": 9,
    "CLAIM_KEY_MASTER_FIRST_CLEAR": 17,
}
TRIGGER_ID = {
    "ROUND_COMPLETE": 0,
    "FIRST_CLEAR": 1,
    "STREAK_MILESTONE": 2,
    "SPECIAL_EVENT": 3,
    "SHINY_MEMORIAL": 4,
}
MODE_LABELS = (
    "トライアル シングル", "トライアル ダブル", "トライアル マルチ",
    "トライアル ランダム", "スタンダード シングル", "スタンダード ダブル",
    "スタンダード マルチ", "スタンダード ランダム", "フル シングル",
    "フル ダブル", "フル マルチ", "フル ランダム", "マスター シングル",
    "マスター ダブル", "マスター マルチ", "マスター ランダム",
    "フル リトル", "フル モノタイプ", "フル OU", "フル カモモンズ",
    "フル むせいげん", "マスター GS", "マスター リージョン",
    "マスター アルティメット",
)


class FactoryHighModesBuildError(ValueError):
    """T25固定入力・canonical・ROM ABI・検証契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise FactoryHighModesBuildError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root is not an object: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _run(command: Sequence[str], label: str, *, timeout: int | None = None) -> str:
    completed = subprocess.run(
        list(command), cwd=ROOT, text=True, capture_output=True,
        check=False, timeout=timeout,
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout).strip()
        _fail(f"{label} failed ({completed.returncode}): {detail[-8000:]}")
    return completed.stdout.strip()


def _integer(value: Any, label: str) -> int:
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        _fail(f"{label} is not an integer: {value!r}")


def _identity(path: Path, contract: Mapping[str, Any], label: str) -> bytes:
    raw = (ROOT / path).read_bytes()
    if contract.get("size") is not None and len(raw) != int(contract["size"]):
        _fail(f"{label} size differs: {len(raw)}")
    if _sha(raw) != contract["sha256"]:
        _fail(f"{label} SHA-256 differs")
    return raw


def _rom_offset(address: int, size: int = 1) -> int:
    offset = address - GBA_ROM_BASE
    if address < GBA_ROM_BASE or offset + size > ROM_SIZE:
        _fail(f"ROM address outside Stage42: 0x{address:08X}")
    return offset


def _index(rows: Sequence[Mapping[str, Any]], key: str,
           label: str) -> dict[str, Mapping[str, Any]]:
    values = [str(row.get(key, "")) for row in rows]
    duplicates = sorted(value for value, count in Counter(values).items()
                        if count != 1)
    if "" in values or duplicates:
        _fail(f"{label} stable key uniqueness differs: {duplicates}")
    return {str(row[key]): row for row in rows}


def _safe_submission(config: Mapping[str, Any]) -> tuple[
    dict[str, list[dict[str, str]]], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    inputs = config["inputs"]
    contract = inputs["submission_zip"]
    zip_path = ROOT / contract["path"]
    before = _identity(Path(contract["path"]), contract, "Factory High submission ZIP")
    if stat.S_IMODE(zip_path.stat().st_mode) != 0o444:
        _fail("private Factory High ZIP mode must be exactly 0444")
    packet = ROOT / inputs["packet_root"]
    validator = ROOT / inputs["validator"]
    if _sha((packet / "PACKET_SPEC.json").read_bytes()) != inputs["packet_spec_sha256"]:
        _fail("Factory High PACKET_SPEC identity differs")
    if _sha(validator.read_bytes()) != inputs["validator_sha256"]:
        _fail("Factory High validator identity differs")
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vega-factory-high-", dir=local) as raw:
        directory = Path(raw)
        with zipfile.ZipFile(zip_path) as archive:
            infos = archive.infolist()
            names = [entry.filename for entry in infos]
            if (len(infos) != int(contract["entry_count"])
                    or set(names) != EXPECTED_MEMBERS
                    or len(names) != len(set(names))
                    or archive.testzip() is not None):
                _fail(f"Factory High ZIP inventory/CRC differs: {sorted(names)}")
            for entry in infos:
                path = Path(entry.filename)
                mode = entry.external_attr >> 16
                if (entry.flag_bits & 1 or entry.is_dir() or path.is_absolute()
                        or ".." in path.parts or len(path.parts) != 1
                        or stat.S_ISLNK(mode)):
                    _fail(f"unsafe Factory High ZIP entry: {entry.filename}")
                (directory / entry.filename).write_bytes(archive.read(entry))
        authored_before = {
            name: _sha((directory / name).read_bytes()) for name in EXPECTED_MEMBERS
        }
        _run([sys.executable, str(validator), "--packet-root", str(packet),
              "--self-test"], "Factory High validator self-test")
        _run([sys.executable, str(validator), "--packet-root", str(packet),
              str(directory)], "Factory High submission validation")
        report = json.loads((directory / "VALIDATION_REPORT.json").read_text(
            encoding="utf-8"))
        manifest = json.loads((directory / "SUBMISSION_MANIFEST.json").read_text(
            encoding="utf-8"))
        if (report.get("status") != "PASS" or report.get("errors") != []
                or report.get("warnings") != [] or report.get("open_questions") != 0
                or report.get("submission_fingerprint") != contract["fingerprint"]
                or manifest.get("packet_type") != "FACTORY_HIGH_MODES"
                or manifest.get("design_status") != "IMPLEMENTATION_READY"
                or manifest.get("submission_fingerprint") != contract["fingerprint"]):
            _fail("Factory High validator/manifest result differs")
        manifest_rows = _index(manifest["files"], "path", "submission manifest")
        if set(manifest_rows) != EXPECTED_MEMBERS - {"SUBMISSION_MANIFEST.json"}:
            _fail("Factory High manifest inventory differs")
        for name, row in manifest_rows.items():
            payload = (directory / name).read_bytes()
            if len(payload) != int(row["size"]) or _sha(payload) != row["sha256"]:
                _fail(f"Factory High manifest identity differs: {name}")
        authored_after = {
            name: _sha((directory / name).read_bytes()) for name in EXPECTED_MEMBERS
        }
        authored = EXPECTED_MEMBERS - {
            "VALIDATION_REPORT.json", "SUBMISSION_MANIFEST.json",
        }
        if any(authored_before[name] != authored_after[name] for name in authored):
            _fail("validator changed an authored Factory High entry")
        tables = {name: _rows(directory / name) for name in CSV_MEMBERS}
        reception = json.loads((directory / "reception_flow.json").read_text(
            encoding="utf-8"))
        runtime = json.loads((directory / "runtime_state_machine.json").read_text(
            encoding="utf-8"))
        if (directory / "OPEN_QUESTIONS.md").read_text(
                encoding="utf-8").strip() != "# Open questions\n\nなし。実装に必要な判断はすべて確定済み。":
            _fail("Factory High open questions differ")
    if zip_path.read_bytes() != before:
        _fail("private Factory High ZIP changed during validation")
    return tables, reception, runtime, {
        "validation": report,
        "manifest": manifest,
        "entry_hashes": authored_before,
        "zip_sha256_before_after": _sha(before),
        "zip_unchanged": True,
    }


def _topological_batches(rows: Sequence[Mapping[str, str]]) -> list[str]:
    keyed = _index(rows, "batch_key", "implementation batches")
    dependencies: dict[str, set[str]] = {}
    children: dict[str, set[str]] = defaultdict(set)
    for key, row in keyed.items():
        values = set() if row["depends_on"] == "NONE" else set(
            row["depends_on"].split("|"))
        if key in values or not values <= set(keyed):
            _fail(f"batch dependency differs: {key}")
        dependencies[key] = values
        for value in values:
            children[value].add(key)
    ready = deque(sorted(key for key, values in dependencies.items() if not values))
    order: list[str] = []
    while ready:
        key = ready.popleft()
        order.append(key)
        for child in sorted(children[key]):
            dependencies[child].discard(key)
            if not dependencies[child]:
                ready.append(child)
    if len(order) != len(rows):
        _fail("Factory High batch graph contains a cycle")
    return order


def _notes_token(notes: str, key: str) -> str | None:
    match = re.search(rf"(?:^|;){re.escape(key)}=([^;]+)", notes)
    return None if match is None else match.group(1)


def _mechanic_mask(policy: str) -> int:
    mask = 1
    if "MEGA" in policy:
        mask |= 1 << 1
    if re.search(r"(?:^|_)Z(?:_|$)", policy):
        mask |= 1 << 2
    if "DYNAMAX" in policy:
        mask |= 1 << 3
    if "TERA" in policy:
        mask |= 1 << 4
    return mask


def _selection_policy(value: str) -> int:
    if value.startswith("AUTO_"):
        return 1
    if "DRAFT_8" in value or "AUTO_DRAFT_8" in value:
        return 2
    if value == "DRAFT_ONE_OFFICIAL_ONE_VEGA_ONE_SPECIAL":
        return 3
    return 0


def _registry(path: Path, key: str) -> dict[str, int]:
    rows = _rows(path)
    indexed = _index(rows, key, path.name)
    result: dict[str, int] = {}
    for name, row in indexed.items():
        if "id" in row and row["id"] != "":
            result[name] = int(row["id"], 0)
    return result


def _canonical_model(config: Mapping[str, Any], stage: bytes) -> dict[str, Any]:
    tables, reception, runtime, submission = _safe_submission(config)
    counts = config["counts"]
    expected = {
        "mode_matrix.csv": counts["modes"],
        "mode_coverage.csv": counts["requirements"],
        "rental_sets.csv": counts["rentals"],
        "opponent_profiles.csv": counts["profiles"],
        "reward_schedule.csv": counts["rewards"],
        "dialogue.csv": counts["dialogues"],
        "implementation_batches.csv": counts["batches"],
    }
    report_counts = submission["validation"]["row_counts"]
    for name, count in expected.items():
        if len(tables[name]) != count or report_counts.get(name) != count:
            _fail(f"canonical row count differs: {name}")
    packet = ROOT / config["inputs"]["packet_root"] / "catalogs"
    species = _registry(packet / "species_ids.csv", "species_key")
    moves = _registry(packet / "move_ids.csv", "move_key")
    items = _registry(packet / "item_ids.csv", "item_key")
    abilities = _registry(packet / "ability_ids.csv", "ability_key")
    types = _registry(packet / "type_ids.csv", "type_key")
    species_rows = _index(_rows(packet / "species_ids.csv"),
                          "species_key", "species catalog")
    unlocks = set(_index(_rows(packet / "unlock_keys.csv"),
                         "unlock_key", "unlock catalog"))
    if tuple(row["nature_key"] for row in _rows(packet / "nature_keys.csv")) != NATURE_ORDER:
        _fail("nature catalog order differs")

    pool_names = sorted({row["pool_key"] for row in tables["rental_sets.csv"]})
    pool_ids = {name: index for index, name in enumerate(pool_names)}
    opponent_pool_names = sorted({row["opponent_profile_pool_key"]
                                  for row in tables["mode_matrix.csv"]})
    opponent_pool_ids = {name: index for index, name in enumerate(opponent_pool_names)}

    mode_rows = sorted(tables["mode_matrix.csv"],
                       key=lambda row: int(row["save_streak_slot"]))
    _index(mode_rows, "mode_key", "mode matrix")
    if [int(row["save_streak_slot"]) for row in mode_rows] != list(range(24)):
        _fail("Factory High save slots are not exact 0..23")
    if Counter(row["tier"] for row in mode_rows) != {
        "TRIAL": 4, "STANDARD": 4, "FULL": 9, "MASTER": 7,
    }:
        _fail("Factory High tier cardinality differs")
    old_modes = _index(_rows(ROOT / "manifests/facility_modes.csv"),
                       "mode_key", "existing facility modes")
    if any(row["mode_key"] not in old_modes for row in mode_rows[:16]):
        _fail("existing 16 Factory mode keys differ")
    normalized_modes: list[dict[str, Any]] = []
    for slot, row in enumerate(mode_rows):
        if (row["status"] != "ACTIVE" or row["tier"] not in TIER_ID
                or row["format"] not in FORMAT_ID
                or row["unlock_key"] not in UNLOCK_ID
                or row["unlock_key"] not in unlocks
                or row["ai_profile_key"] not in AI_ID
                or row["rental_pool_key"] not in pool_ids
                or row["opponent_profile_pool_key"] not in opponent_pool_ids
                or int(row["selection_count"]) not in {3, 4}
                or int(row["player_party_size"]) not in {3, 4, 6}
                or int(row["opponent_party_size"]) not in {3, 4, 6}
                or int(row["round_battle_count"]) not in {3, 7}):
            _fail(f"mode contract differs: {row['mode_key']}")
        normalized_modes.append({
            **row,
            "slot": slot,
            "tier_id": TIER_ID[row["tier"]],
            "format_id": FORMAT_ID[row["format"]],
            "selection_count": int(row["selection_count"]),
            "player_party_size": int(row["player_party_size"]),
            "opponent_party_size": int(row["opponent_party_size"]),
            "round_battle_count": int(row["round_battle_count"]),
            "max_milestone": int(row["max_milestone"]),
            "unlock_id": UNLOCK_ID[row["unlock_key"]],
            "mechanic_mask": _mechanic_mask(row["mechanic_policy"]),
            "selection_policy_id": _selection_policy(row["selection_policy"]),
            "swap_policy_id": 1 if "PLAYER_OWNED" in row["swap_policy"] else 0,
            "ai_id": AI_ID[row["ai_profile_key"]],
            "rental_pool_id": pool_ids[row["rental_pool_key"]],
            "opponent_pool_id": opponent_pool_ids[row["opponent_profile_pool_key"]],
        })
    trial = normalized_modes[0]
    if (trial["mode_key"] != "FACILITY_MODE_TRIAL_SINGLE"
            or trial["format"] != "SINGLE_3V3"
            or trial["round_battle_count"] != 3
            or trial["max_milestone"] != 3):
        _fail("slot 0 Trial compatibility row differs")

    requirements = tables["mode_coverage.csv"]
    _index(requirements, "requirement_key", "mode coverage")
    mode_keys = {row["mode_key"] for row in normalized_modes}
    if any(row["mode_key"] not in mode_keys
           or row["resolution"] not in {"DIRECT_MODE", "RULE_PRESET"}
           for row in requirements):
        _fail("mode coverage reference/resolution differs")
    expected_requirements = set(_index(
        _rows(packet / "factory_mode_requirements.csv"),
        "requirement_key", "requirement catalog"))
    if {row["requirement_key"] for row in requirements} != expected_requirements:
        _fail("28 requirement coverage is not exact")

    rentals = tables["rental_sets.csv"]
    _index(rentals, "rental_key", "rental sets")
    normalized_rentals: list[dict[str, Any]] = []
    for index, row in enumerate(rentals):
        symbolic = {
            "species": row["species_key"], "item": row["item_key"],
            "ability": row["ability_key"],
            "moves": [row[f"move{i}_key"] for i in range(1, 5)],
        }
        missing = [
            f"{kind}:{value}" for kind, values, registry in (
                ("species", [symbolic["species"]], species),
                ("item", [symbolic["item"]], items),
                ("ability", [symbolic["ability"]], abilities),
                ("move", symbolic["moves"], moves),
            ) for value in values if value not in registry
        ]
        tera = row["tera_type_key"]
        if (missing or row["form_key"] != "NONE"
                or row["nature_key"] not in NATURE_ID
                or row["pool_key"] not in pool_ids
                or row["origin_bucket"] not in ORIGIN_ID
                or row["unlock_key"] not in unlocks
                or row["status"] != "ACTIVE"
                or row["iv_policy"] not in {"ALL_31", "ROLE_31"}
                or len(set(symbolic["moves"])) != 4
                or sum(int(row[f"ev_{name}"]) for name in
                       ("hp", "atk", "def", "speed", "spatk", "spdef")) > 510
                or (tera != "TYPE_KEY_NONE" and tera not in types)):
            _fail(f"rental contract differs: {row['rental_key']} missing={missing}")
        notes = row["notes"]
        restricted = _notes_token(notes, "RESTRICTED_CLASS")
        if restricted is None:
            restricted = _notes_token(notes, "GS_CLASS")
        gimmick = _notes_token(notes, "ULTIMATE_GIMMICK") or "NONE"
        mono = _notes_token(notes, "MONOTYPE_GROUP") or ""
        normalized_rentals.append({
            **row, "index": index,
            "species_id": species[symbolic["species"]],
            "species_name": species_rows[symbolic["species"]]["display_name"],
            "item_id": items[symbolic["item"]],
            "move_ids": [moves[value] for value in symbolic["moves"]],
            "ability_id": abilities[symbolic["ability"]],
            "nature_id": NATURE_ID[row["nature_key"]],
            "ev": [int(row[f"ev_{name}"]) for name in
                   ("hp", "atk", "def", "speed", "spatk", "spdef")],
            "tera_type_id": 0xFF if tera == "TYPE_KEY_NONE" else types[tera],
            "pool_id": pool_ids[row["pool_key"]],
            "origin_id": ORIGIN_ID[row["origin_bucket"]],
            "restricted_class": 1 if restricted in {"UBER", "RESTRICTED"} else 0,
            "role_id": 1 if "ROLE=SUPPORT" in notes
                              or restricted == "SUPPORT" else 0,
            "gimmick_id": GIMMICK_ID[gimmick],
            "monotype_group": {"TYPE_KEY_FIRE": 1, "TYPE_KEY_WATER": 2,
                                "TYPE_KEY_STEEL": 3}.get(mono, 0),
            "weight": int(row["weight"]),
            "level": 5 if row["pool_key"] == "RENTAL_POOL_KEY_FULL_LITTLE" else 50,
            "iv_policy_id": 1 if row["iv_policy"] == "ROLE_31" else 0,
            "gmax_allowed_id": 1 if row["gmax_allowed"] == "true" else 0,
        })

    profiles = tables["opponent_profiles.csv"]
    _index(profiles, "profile_key", "opponent profiles")
    normalized_profiles: list[dict[str, Any]] = []
    for index, row in enumerate(profiles):
        if (row["tier"] not in TIER_ID or row["pool_key"] not in opponent_pool_ids
                or row["format"] not in FORMAT_ID
                or row["ai_profile_key"] not in AI_ID
                or row["rental_pool_key"] not in pool_ids
                or row["unlock_key"] not in UNLOCK_ID
                or row["status"] != "ACTIVE"
                or int(row["weight"]) <= 0):
            _fail(f"opponent profile contract differs: {row['profile_key']}")
        normalized_profiles.append({
            **row, "index": index,
            "tier_id": TIER_ID[row["tier"]],
            "pool_id": opponent_pool_ids[row["pool_key"]],
            "format_id": FORMAT_ID[row["format"]],
            "ai_id": AI_ID[row["ai_profile_key"]],
            "generation_policy_id": index % 16,
            "rental_pool_id": pool_ids[row["rental_pool_key"]],
            "min_distinct_species": int(row["min_distinct_species"]),
            "min_type_diversity": int(row["min_type_diversity"]),
            "clauses": (1 if row["item_clause"] == "ON" else 0)
                       | (2 if row["species_clause"] == "ON" else 0),
            "gimmick_policy_id": _mechanic_mask(row["gimmick_policy"]),
            "weight": int(row["weight"]),
            "unlock_id": UNLOCK_ID[row["unlock_key"]],
        })
    covered_profile_pools = {row["pool_id"] for row in normalized_profiles}
    if covered_profile_pools != set(opponent_pool_ids.values()):
        _fail("opponent profile pool coverage differs")

    rewards = tables["reward_schedule.csv"]
    _index(rewards, "reward_key", "reward schedule")
    normalized_rewards: list[dict[str, Any]] = []
    for index, row in enumerate(rewards):
        item = row["item_key"]
        claim = row["claim_key"]
        if (row["tier"] not in TIER_ID or row["trigger_kind"] not in TRIGGER_ID
                or item not in items or row["unlock_key"] not in UNLOCK_ID
                or row["status"] != "ACTIVE"
                or row["repeatability"] not in {"REPEATABLE", "ONCE"}
                or (claim != "NONE" and claim not in CLAIM_BITS)):
            _fail(f"reward contract differs: {row['reward_key']}")
        normalized_rewards.append({
            **row, "index": index,
            "tier_id": TIER_ID[row["tier"]],
            "trigger_id": TRIGGER_ID[row["trigger_kind"]],
            "streak": int(row["streak"]), "bp_amount": int(row["bp_amount"]),
            "item_id": items[item], "quantity": int(row["quantity"]),
            "once": int(row["repeatability"] == "ONCE"),
            "claim_bit": 0xFF if claim == "NONE" else CLAIM_BITS[claim],
            "unlock_id": UNLOCK_ID[row["unlock_key"]],
        })

    dialogues = tables["dialogue.csv"]
    _index(dialogues, "dialogue_key", "dialogues")
    mapping, tokens = _charmap(ROOT)
    encoded_dialogues: dict[str, str] = {}
    for row in dialogues:
        if row["mode_key"] not in mode_keys:
            _fail(f"dialogue mode reference differs: {row['dialogue_key']}")
        encoded_dialogues[row["dialogue_key"]] = _encode_text(
            row["text"].replace("\\n", "\n"), mapping, tokens).hex()
    batch_order = _topological_batches(tables["implementation_batches.csv"])
    if (reception.get("design_status") != "IMPLEMENTATION_READY"
            or runtime.get("design_status") != "IMPLEMENTATION_READY"
            or reception.get("open_questions", []) != []
            or runtime.get("open_questions", []) != []
            or runtime.get("state_owner", {}).get("streak_slot_count") != 24
            or runtime.get("save_resume_contract", {}).get("active_run_policy")
                != "ABORT_AND_EXACT_RESTORE_ON_BOOT"):
        _fail("Factory High runtime/reception contract differs")
    return {
        "schema_version": 2, "task": TASK,
        "submission_audit": submission,
        "modes": normalized_modes,
        "requirements": requirements,
        "rentals": normalized_rentals,
        "profiles": normalized_profiles,
        "rewards": normalized_rewards,
        "dialogues": dialogues,
        "dialogue_encoding": encoded_dialogues,
        "batches": tables["implementation_batches.csv"],
        "batch_order": batch_order,
        "reception_flow": reception,
        "runtime_state_machine": runtime,
        "pool_ids": pool_ids,
        "opponent_pool_ids": opponent_pool_ids,
        "normalization": {
            "mode_count": 24, "requirement_count": 28,
            "rental_count": 248, "profile_count": 55,
            "reward_count": 16, "dialogue_count": 28,
            "batch_count": 7, "stable_key_duplicates": 0,
            "unresolved_references": 0, "open_questions": 0,
        },
    }


def _c_array(raw: bytes) -> str:
    return ", ".join(f"0x{value:02X}u" for value in raw)


def _runtime_header(model: Mapping[str, Any], config: Mapping[str, Any]) -> bytes:
    engine_macros = {
        "try_saving_data": "FACTORY_HIGH_ENGINE_TRY_SAVING_DATA",
        "save_init_new": "FACTORY_HIGH_ENGINE_SAVE_INIT_NEW",
        "save_validate": "FACTORY_HIGH_ENGINE_SAVE_VALIDATE",
        "save_finalize": "FACTORY_HIGH_ENGINE_SAVE_FINALIZE",
        "flag_get": "FACTORY_HIGH_ENGINE_FLAG_GET",
        "flag_set": "FACTORY_HIGH_ENGINE_FLAG_SET",
        "flag_clear": "FACTORY_HIGH_ENGINE_FLAG_CLEAR",
        "var_set": "FACTORY_HIGH_ENGINE_VAR_SET",
        "configure_factory": "FACTORY_HIGH_ENGINE_CONFIGURE_FACTORY",
        "create_mon": "FACTORY_HIGH_ENGINE_CREATE_MON",
        "set_mon_data": "FACTORY_HIGH_ENGINE_SET_MON_DATA",
        "get_mon_data": "FACTORY_HIGH_ENGINE_GET_MON_DATA",
        "get_mon_ability": "FACTORY_HIGH_ENGINE_GET_MON_ABILITY",
        "calculate_mon_stats": "FACTORY_HIGH_ENGINE_CALCULATE_STATS",
        "calculate_pp": "FACTORY_HIGH_ENGINE_CALCULATE_PP",
        "heal_player_party": "FACTORY_HIGH_ENGINE_HEAL_PARTY",
        "calculate_party_count": "FACTORY_HIGH_ENGINE_PARTY_COUNT",
        "species_to_national": "FACTORY_HIGH_ENGINE_SPECIES_TO_NATIONAL",
        "get_set_pokedex": "FACTORY_HIGH_ENGINE_GET_SET_POKEDEX",
        "check_bag_space": "FACTORY_HIGH_ENGINE_CHECK_BAG_SPACE",
        "add_bag_item": "FACTORY_HIGH_ENGINE_ADD_BAG_ITEM",
        "remove_bag_item": "FACTORY_HIGH_ENGINE_REMOVE_BAG_ITEM",
    }
    delegate_macros = {
        "trainer_party": "FACTORY_HIGH_DELEGATE_TRAINER_PARTY",
        "ability_load": "FACTORY_HIGH_DELEGATE_ABILITY_LOAD",
        "save_load": "FACTORY_HIGH_DELEGATE_SAVE_LOAD",
        "trial_complete": "FACTORY_HIGH_DELEGATE_TRIAL_COMPLETE",
        "shiny_claim": "FACTORY_HIGH_DELEGATE_SHINY_CLAIM",
    }
    if set(engine_macros) != set(config["engine"]):
        _fail("Factory High engine ABI config differs")
    if set(delegate_macros) != set(config["delegates"]):
        _fail("Factory High delegate ABI config differs")
    lines = [
        "#ifndef VEGA_FACTORY_HIGH_MODES_V2_GENERATED_H",
        "#define VEGA_FACTORY_HIGH_MODES_V2_GENERATED_H",
        "#define FACTORY_HIGH_GENERATED_SCHEMA_VERSION 2u",
        "#define FACTORY_HIGH_MODE_COUNT 24u",
        "#define FACTORY_HIGH_RENTAL_COUNT 248u",
        "#define FACTORY_HIGH_PROFILE_COUNT 55u",
        "#define FACTORY_HIGH_REWARD_COUNT 16u",
        "#define FACTORY_HIGH_FACILITY_PARTY_SIZE_VAR 0x5015u",
    ]
    item_rows = {row["item_key"]: row["item_id"] for row in model["rentals"]}
    reward_items = {row["item_key"]: row["item_id"] for row in model["rewards"]}
    item_rows.update(reward_items)
    if "ITEM_KEY_ORAN_BERRY" not in item_rows:
        _fail("Factory High Oran Berry ID is unresolved")
    lines.append(f"#define FACTORY_HIGH_ITEM_ORAN_BERRY {item_rows['ITEM_KEY_ORAN_BERRY']}u")
    for key, macro in engine_macros.items():
        lines.append(f"#define {macro} 0x{_integer(config['engine'][key], key):08X}u")
    for key, macro in delegate_macros.items():
        lines.append(f"#define {macro} 0x{_integer(config['delegates'][key], key):08X}u")
    flags = config["unlock_flags"]
    lines.extend([
        "",
        "static const uint16_t gFactoryHighUnlockFlags[4] = {",
        "    0u, 0x%04Xu, 0x%04Xu, 0x%04Xu," % tuple(
            _integer(flags[key], key) for key in
            ("FACTORY_STANDARD", "FACTORY_FULL", "FACTORY_MASTER")
        ),
        "};",
        "static const uint16_t gFactoryHighCreditThresholds[4] = {3u, 7u, 14u, 21u};",
        "",
        "static const FactoryHighModeRow gFactoryHighModes[24] = {",
    ])
    for row in model["modes"]:
        values = (
            row["tier_id"], row["format_id"], row["selection_count"],
            row["player_party_size"], row["opponent_party_size"],
            row["round_battle_count"], row["max_milestone"], row["unlock_id"],
            row["mechanic_mask"], row["selection_policy_id"],
            row["swap_policy_id"], row["ai_id"], row["rental_pool_id"],
            row["opponent_pool_id"], row["slot"], 0,
        )
        lines.append("    {%s}," % ", ".join(f"{value}u" for value in values))
    lines.extend(["};", "", "static const FactoryHighRentalRow gFactoryHighRentals[248] = {"])
    for row in model["rentals"]:
        moves = ", ".join(f"{value}u" for value in row["move_ids"])
        ev = ", ".join(f"{value}u" for value in row["ev"])
        lines.append(
            "    {%du, %du, {%s}, %du, %du, {%s}, %du, %du, %du, "
            "%du, %du, %du, %du, %du, %du, %du, %du}," % (
                row["species_id"], row["item_id"], moves, row["ability_id"],
                row["nature_id"], ev, row["tera_type_id"], row["pool_id"],
                row["origin_id"], row["restricted_class"], row["role_id"],
                row["gimmick_id"], row["monotype_group"], row["weight"],
                row["level"], row["iv_policy_id"], row["gmax_allowed_id"],
            )
        )
    lines.extend(["};", "", "static const FactoryHighProfileRow gFactoryHighProfiles[55] = {"])
    for row in model["profiles"]:
        values = (
            row["tier_id"], row["pool_id"], row["format_id"], row["ai_id"],
            row["generation_policy_id"], row["rental_pool_id"],
            row["min_distinct_species"], row["min_type_diversity"],
            row["clauses"], row["gimmick_policy_id"], row["weight"],
            row["unlock_id"],
        )
        lines.append("    {%s}," % ", ".join(f"{value}u" for value in values))
    lines.extend(["};", "", "static const FactoryHighRewardRow gFactoryHighRewards[16] = {"])
    for row in model["rewards"]:
        values = (
            row["tier_id"], row["trigger_id"], row["streak"], row["bp_amount"],
            row["item_id"], row["quantity"], row["once"], row["claim_bit"],
            row["unlock_id"],
        )
        lines.append("    {%s}," % ", ".join(f"{value}u" for value in values))
    lines.extend(["};", ""])
    mapping, tokens = _charmap(ROOT)

    def add_text(symbol: str, text: str) -> None:
        raw = _encode_text(text, mapping, tokens)
        lines.append(f"static const uint8_t {symbol}[] = {{{_c_array(raw)}}};")

    for index, row in enumerate(model["dialogues"]):
        raw = bytes.fromhex(model["dialogue_encoding"][row["dialogue_key"]])
        lines.append(
            f"static const uint8_t gFactoryHighDialogue{index}[] = "
            f"{{{_c_array(raw)}}};"
        )
    lines.append("static const uint8_t *const gFactoryHighDialogues[28] = {")
    for start in range(0, 28, 7):
        lines.append("    " + ", ".join(
            f"gFactoryHighDialogue{index}"
            for index in range(start, min(start + 7, 28))) + ",")
    lines.append("};")

    def key_hash(value: str) -> int:
        digest = 2166136261
        for byte in value.encode("ascii"):
            digest = ((digest ^ byte) * 16777619) & 0xFFFFFFFF
        return digest

    lines.append("static const uint32_t gFactoryHighRequirementKeys[28] = {")
    for start in range(0, 28, 7):
        lines.append("    " + ", ".join(
            f"0x{key_hash(model['requirements'][index]['requirement_key']):08X}u"
            for index in range(start, min(start + 7, 28))) + ",")
    lines.append("};")
    lines.append("static const uint32_t gFactoryHighBatchKeys[7] = {")
    lines.append("    " + ", ".join(
        f"0x{key_hash(row['batch_key']):08X}u" for row in model["batches"]) + ",")
    lines.append("};")

    for index, label in enumerate(("トライアル", "スタンダード", "フル", "マスター")):
        add_text(f"gFactoryHighTierLabel{index}", label)
    lines.append("static const uint8_t *const gFactoryHighTierLabels[4] = {")
    lines.append("    gFactoryHighTierLabel0, gFactoryHighTierLabel1, gFactoryHighTierLabel2, gFactoryHighTierLabel3,")
    lines.append("};")
    for index, label in enumerate(MODE_LABELS):
        add_text(f"gFactoryHighModeLabel{index}", label)
    lines.append("static const uint8_t *const gFactoryHighModeLabels[24] = {")
    for start in range(0, 24, 4):
        lines.append("    " + ", ".join(
            f"gFactoryHighModeLabel{index}" for index in range(start, start + 4)) + ",")
    lines.append("};")
    option_groups = (
        ("Monotype", ("ほのお", "みず", "はがね")),
        ("Uber", ("むせいげん", "UBER")),
        ("Ultimate", ("メガシンカ", "Zワザ", "ダイマックス", "テラスタル")),
    )
    for prefix, labels in option_groups:
        for index, label in enumerate(labels):
            add_text(f"gFactoryHigh{prefix}Label{index}", label)
        lines.append(
            f"static const uint8_t *const gFactoryHigh{prefix}Labels[{len(labels)}] = {{"
        )
        lines.append("    " + ", ".join(
            f"gFactoryHigh{prefix}Label{index}" for index in range(len(labels))) + ",")
        lines.append("};")
    add_text("gFactoryHighTextStart", "はじめる")
    add_text("gFactoryHighTextCancel", "やめる")
    for index, row in enumerate(model["rentals"]):
        label = str(row["species_name"]).strip() or f"レンタル{index + 1:03d}"
        add_text(f"gFactoryHighRentalLabel{index}", label)
    lines.append("static const uint8_t *const gFactoryHighRentalLabels[248] = {")
    for start in range(0, 248, 8):
        lines.append("    " + ", ".join(
            f"gFactoryHighRentalLabel{index}"
            for index in range(start, min(start + 8, 248))) + ",")
    lines.extend(["};", "", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def _compile_runtime(
    load_address: int, header: bytes,
) -> tuple[bytes, dict[str, int], dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    sources = (
        ROOT / "overlays/factory_high_modes_v2/factory_high_modes_v2.c",
        ROOT / "overlays/factory_high_modes_v2/factory_high_modes_v2_libc.c",
    )
    if any(not path.is_file() for path in sources):
        _fail("Factory High runtime overlay is incomplete")
    with tempfile.TemporaryDirectory(prefix="vega-factory-high-runtime-") as raw:
        directory = Path(raw)
        (directory / "factory_high_modes_v2_generated.h").write_bytes(header)
        objects: list[Path] = []
        for source in sources:
            obj = directory / f"{source.stem}.o"
            _run([
                compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
                "-std=c11", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
                "-fno-builtin", "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
                "-fdata-sections", "-ffunction-sections", "-fno-common",
                "-DVEGA_SAVE_ROM_RUNTIME=1", f"-I{directory}", f"-I{ROOT}",
                "-c", str(source), "-o", str(obj),
            ], f"compile Factory High runtime {source.name}")
            objects.append(obj)
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.FactoryHighModesV2_*)) *(.text*) *(.rodata*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "factory_high_modes_v2.elf"
        binary = directory / "factory_high_modes_v2.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-nostdlib",
            "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,FactoryHighModesV2_Probe", f"-Wl,-T,{linker}",
            *(str(path) for path in objects), "-lgcc", "-o", str(elf),
        ], "link Factory High runtime")
        undefined = _run([nm, "-u", str(elf)], "Factory High undefined-symbol audit")
        if undefined:
            _fail("Factory High runtime has undefined symbols: " + undefined)
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run([nm, "-n", "-S", "--defined-only", str(elf)],
                         "Factory High runtime nm").splitlines():
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
            _fail(f"Factory High runtime symbols differ: missing={missing}, mutable={mutable}")
        _run([objcopy, "-O", "binary", str(elf), str(binary)],
             "Factory High runtime objcopy")
        payload = binary.read_bytes()
        if not payload or len(payload) > 128 * 1024:
            _fail(f"Factory High runtime size is unreasonable: {len(payload)}")
        return payload, symbols, sizes


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

    def word(self, value: int) -> "_Script":
        self.data.extend(struct.pack("<I", value))
        return self

    def pointer(self, label: str, *, thumb: bool = False) -> "_Script":
        self.fixups.append((len(self.data), label, thumb))
        self.data.extend(bytes(4))
        return self

    def callnative(self, address: int, name: str) -> "_Script":
        self.operations.append(f"callnative:{name}")
        return self.emit(0x23).word(address | 1)

    def trainerbattle(self, trainer_id: int, local_id: int,
                      defeat_text: str) -> "_Script":
        self.operations.append(
            f"trainerbattle:3:{trainer_id}:{local_id}:{defeat_text}"
        )
        return (self.emit(0x5C, 0x03).half(trainer_id).half(local_id)
                .pointer(defeat_text))

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

    def goto_absolute(self, address: int, name: str) -> "_Script":
        self.operations.append(f"goto_absolute:{name}:0x{address:08X}")
        return self.emit(0x05).word(address)


def _add_script(blob: _Blob, label: str, script: _Script,
                metadata: list[dict[str, Any]]) -> None:
    offset = blob.add(label, bytes(script.data), 4)
    for relative, target, thumb in script.fixups:
        blob.pointer(offset + relative, target, thumb=thumb)
    metadata.append({
        "label": label, "offset": offset, "size": len(script.data),
        "operations": script.operations,
    })


def _build_field_payload(
    model: Mapping[str, Any], config: Mapping[str, Any], code: bytes,
    symbols: Mapping[str, int], payload_offset: int,
) -> tuple[bytes, dict[str, Any]]:
    blob = _Blob()
    if blob.add("payload_header", b"\xFF" * PAYLOAD_HEADER_SIZE, 16) != 0:
        _fail("Factory High payload header offset differs")
    code_offset = blob.add("runtime_code", code, 4)
    if code_offset != PAYLOAD_HEADER_SIZE:
        _fail("Factory High runtime code offset differs")
    mapping, tokens = _charmap(ROOT)
    texts = {
        "text::defeat": "ファクトリーバトル\nしょうり！",
        "text::exchange": "あいての ポケモンと\nこうかん しますか？",
        "text::round": "ラウンド クリア！\nつづけますか？",
        "text::complete": "チャレンジ\nかんそう！",
        "text::retire": "きろくを のこして\nしゅうりょうしました",
        "text::cancel": "ちょうせんを\nとりやめました",
        "text::bag_full": "もちものが いっぱいです\nあきを つくってください",
        "text::error": "じゅんびに\nしっぱいしました",
    }
    for label, value in texts.items():
        blob.add(label, _encode_text(value, mapping, tokens), 1)
    scripts: list[dict[str, Any]] = []
    status = {
        "ok": 1, "round": 2, "complete": 3, "cancel": 4,
        "bag_full": 8, "trial": 10, "high": 11,
    }
    reception = (
        _Script().emit(0x6A, 0x5A, operation="lock_faceplayer")
        .callnative(symbols["FactoryHighModesV2_FieldReception"],
                    "FactoryHighModesV2_FieldReception")
        .emit(0x27, operation="waitstate")
        .compare_result(status["trial"]).if_equal("script::factory_trial_delegate")
        .compare_result(status["high"]).if_equal("script::factory_high_enter")
        .compare_result(status["cancel"]).if_equal("script::factory_high_cancel")
        .goto("script::factory_high_error")
    )
    _add_script(blob, "script::factory_high_modes_reception", reception, scripts)
    _add_script(
        blob, "script::factory_trial_delegate",
        _Script().goto_absolute(
            _integer(config["physical_binding"]["trial_script"], "Trial script"),
            "legacy_factory_trial",
        ), scripts,
    )
    _add_script(
        blob, "script::factory_high_enter",
        _Script().callnative(symbols["FactoryHighModesV2_EnterSelected"],
                             "FactoryHighModesV2_EnterSelected")
        .compare_result(status["ok"]).if_equal("script::factory_high_draft")
        .compare_result(status["bag_full"]).if_equal("script::factory_high_bag_full")
        .goto("script::factory_high_error"), scripts,
    )
    _add_script(
        blob, "script::factory_high_draft",
        _Script().callnative(symbols["FactoryHighModesV2_FieldDraft"],
                             "FactoryHighModesV2_FieldDraft")
        .emit(0x27, operation="waitstate")
        .compare_result(status["ok"]).if_equal("script::factory_high_commit")
        .compare_result(status["cancel"]).if_equal("script::factory_high_cancel")
        .goto("script::factory_high_error"), scripts,
    )
    _add_script(
        blob, "script::factory_high_commit",
        _Script().callnative(symbols["FactoryHighModesV2_CommitSelection"],
                             "FactoryHighModesV2_CommitSelection")
        .compare_result(status["ok"]).if_equal("script::factory_high_battle")
        .goto("script::factory_high_error"), scripts,
    )
    _add_script(
        blob, "script::factory_high_battle",
        _Script().callnative(symbols["FactoryHighModesV2_PrepareBattle"],
                             "FactoryHighModesV2_PrepareBattle")
        .compare_result(status["ok"]).if_equal("script::factory_high_launch")
        .compare_result(status["bag_full"]).if_equal("script::factory_high_bag_full")
        .goto("script::factory_high_error"), scripts,
    )
    _add_script(
        blob, "script::factory_high_launch",
        _Script().trainerbattle(745, 2, "text::defeat")
        .callnative(symbols["FactoryHighModesV2_AfterBattle"],
                    "FactoryHighModesV2_AfterBattle")
        .compare_result(status["ok"]).if_equal("script::factory_high_exchange")
        .compare_result(status["round"]).if_equal("script::factory_high_round")
        .compare_result(status["complete"]).if_equal("script::factory_high_complete")
        .compare_result(status["bag_full"]).if_equal("script::factory_high_bag_full")
        .goto("script::factory_high_error"), scripts,
    )
    _add_script(
        blob, "script::factory_high_exchange",
        _Script().msgbox("text::exchange", 5).compare_result(1)
        .if_equal("script::factory_high_exchange_yes")
        .goto("script::factory_high_exchange_skip"), scripts,
    )
    _add_script(
        blob, "script::factory_high_exchange_yes",
        _Script().callnative(symbols["FactoryHighModesV2_BeginExchange"],
                             "FactoryHighModesV2_BeginExchange")
        .emit(0x25, operation="special:0x002F").half(0x002F)
        .emit(0x27, operation="waitstate")
        .callnative(symbols["FactoryHighModesV2_CommitExchange"],
                    "FactoryHighModesV2_CommitExchange")
        .compare_result(status["ok"]).if_equal("script::factory_high_battle")
        .goto("script::factory_high_error"), scripts,
    )
    _add_script(
        blob, "script::factory_high_exchange_skip",
        _Script().callnative(symbols["FactoryHighModesV2_SkipExchange"],
                             "FactoryHighModesV2_SkipExchange")
        .goto("script::factory_high_battle"), scripts,
    )
    _add_script(
        blob, "script::factory_high_round",
        _Script().msgbox("text::round", 5).compare_result(1)
        .if_equal("script::factory_high_battle")
        .goto("script::factory_high_retire"), scripts,
    )
    _add_script(
        blob, "script::factory_high_retire",
        _Script().callnative(symbols["FactoryHighModesV2_Retire"],
                             "FactoryHighModesV2_Retire")
        .msgbox("text::retire").emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    _add_script(
        blob, "script::factory_high_complete",
        _Script().msgbox("text::complete")
        .emit(0x6C, 0x02, operation="release_end"), scripts,
    )
    for label, text_label in (
        ("cancel", "text::cancel"), ("bag_full", "text::bag_full"),
        ("error", "text::error"),
    ):
        _add_script(
            blob, f"script::factory_high_{label}",
            _Script().callnative(symbols["FactoryHighModesV2_Abort"],
                                 "FactoryHighModesV2_Abort")
            .msgbox(text_label).emit(0x6C, 0x02, operation="release_end"), scripts,
        )
    payload = bytearray(blob.finish(payload_offset))
    struct.pack_into(
        "<8s15I", payload, 0, b"VEGAFH42", 2, len(payload),
        PAYLOAD_HEADER_SIZE, len(code), 24, 28, 248, 55, 16, 28, 7,
        _integer(config["ram"]["address"], "Factory High RAM"),
        int(config["ram"]["size"]),
        _integer(config["save"]["ledger_address"], "Factory ledger"),
        int(config["save"]["factory_size"]),
    )
    base = GBA_ROM_BASE + payload_offset
    labels = {name: base + offset for name, offset in blob.labels.items()}
    for row in scripts:
        row["address"] = base + int(row["offset"])
    return bytes(payload), {
        "labels": labels,
        "scripts": scripts,
        "reception_script": labels["script::factory_high_modes_reception"],
        "trial_delegate": _integer(
            config["physical_binding"]["trial_script"], "Trial script"),
        "trainerbattle": {
            "command": 0x5C, "mode": 3, "trainer_id": 745,
            "local_id": 2, "continuation": "FactoryHighModesV2_AfterBattle",
        },
    }


def _validate_ram_and_save(config: Mapping[str, Any]) -> dict[str, Any]:
    rows = _rows(ROOT / "config/ram_layout.csv")
    live = [row for row in rows if row["status"] == "LIVE" and row["start"]]
    owned = [row for row in live if row["owner"] == "T25_FACTORY_HIGH_MODES_V2"]
    if len(owned) != 1:
        _fail("T25 volatile RAM owner row is not unique")
    row = owned[0]
    start = _integer(config["ram"]["address"], "Factory High RAM start")
    end = _integer(config["ram"]["end_exclusive"], "Factory High RAM end")
    if (int(row["start"], 0) != start or int(row["end_exclusive"], 0) != end
            or int(row["size"]) != int(config["ram"]["size"])
            or end - start != int(row["size"])):
        _fail("T25 volatile RAM reservation differs")
    overlaps = [
        other["symbol"] for other in live
        if other is not row and other["address_space"] == row["address_space"]
        and start < int(other["end_exclusive"], 0)
        and int(other["start"], 0) < end
    ]
    if overlaps:
        _fail(f"T25 volatile RAM overlaps LIVE rows: {overlaps}")
    save = config["save"]
    if (_integer(save["ledger_address"], "Factory ledger") != 0x0203D000
            or int(save["ledger_size"]) != 2048
            or _integer(save["factory_offset"], "Factory offset") != 0x392
            or int(save["factory_size"]) != 714
            or int(save["party_snapshot_size"]) != 600
            or int(save["mode_slot_count"]) != 24):
        _fail("Factory reused save ABI differs")
    save_layout = (ROOT / "config/save_layout.csv").read_text(encoding="utf-8")
    if "factory" not in save_layout:
        _fail("Factory save owner is not rooted in save_layout.csv")
    return {
        "ram": {"address": start, "end_exclusive": end, "size": end - start,
                "overlap_count": 0, "persistence": "VOLATILE"},
        "save": {"new_owner_bytes": 0, "ledger_size": 2048,
                 "factory_offset": 0x392, "factory_size": 714,
                 "party_snapshot_size": 600, "mode_slots": 24,
                 "overlap_count": 0},
    }


def _allocation(previous: Mapping[str, Any], size: int,
                digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules", "size": size,
        "alignment": 16, "owner": TASK,
        "purpose": (
            "Factory High Modes V2 runtime, 24 modes, 248 rentals, 55 profiles, "
            "16 rewards, 28 dialogues and receptionist field graph"
        ),
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage42 allocator overlap detected")
    matches = [row for row in report.get("allocations", [])
               if row.get("name") == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage42 Factory High allocation is not unique")
    return matches[0], report


def _build_payload(
    model: Mapping[str, Any], previous: Mapping[str, Any],
    config: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any], dict[str, Any], bytes]:
    header = _runtime_header(model, config)
    payload_offset = -1
    load_address = GBA_ROM_BASE + PAYLOAD_HEADER_SIZE
    final: tuple[bytes, dict[str, int], dict[str, int], bytes, dict[str, Any]] | None = None
    for _ in range(8):
        code, symbols, sizes = _compile_runtime(load_address, header)
        payload, field = _build_field_payload(
            model, config, code, symbols, max(payload_offset, 0),
        )
        allocation, _ = _allocation(previous, len(payload), "0" * 64)
        next_offset = int(allocation["start"])
        next_load = GBA_ROM_BASE + next_offset + PAYLOAD_HEADER_SIZE
        if payload_offset == next_offset and load_address == next_load:
            final = code, symbols, sizes, payload, field
            break
        payload_offset, load_address = next_offset, next_load
    if final is None or payload_offset < 0:
        _fail("Factory High runtime/field allocation did not reach a fixed point")
    code, symbols, sizes, payload, field = final
    allocation, report = _allocation(previous, len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("Factory High allocation placement changed after content hash")
    entrypoints = {name: symbols[name] | 1 for name in sorted(REQUIRED_ENTRYPOINTS)}
    return payload, {
        "payload": {"offset": payload_offset,
                    "address": GBA_ROM_BASE + payload_offset,
                    "size": len(payload), "sha256": _sha(payload)},
        "code": {"address": GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE,
                 "size": len(code), "sha256": _sha(code)},
        "entrypoints": entrypoints,
        "symbol_sizes": {name: sizes.get(name, 0) for name in entrypoints},
        "field": field,
    }, report, header


def _thumb_bl(site_address: int, target_address: int) -> bytes:
    site = site_address & ~1
    target = target_address & ~1
    delta = target - (site + 4)
    if delta & 1 or not -0x400000 <= delta < 0x400000:
        _fail(f"Thumb BL out of range: {site:#010x} -> {target:#010x}")
    return struct.pack(
        "<HH", 0xF000 | ((delta >> 12) & 0x7FF),
        0xF800 | ((delta >> 1) & 0x7FF),
    )


def _patch(output: bytearray, stage: bytes,
           declared: list[dict[str, Any]], address: int, expected: bytes,
           replacement: bytes, name: str) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{name}: expected/replacement length differs")
    offset = _rom_offset(address, len(expected))
    actual = stage[offset:offset + len(expected)]
    if actual != expected:
        _fail(f"{name}: Stage41 expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({"start": offset, "end_exclusive": offset + len(replacement),
                     "kind": name})
    return {"name": name, "address": address, "offset": offset,
            "size": len(expected), "expected_hex": expected.hex(),
            "replacement_hex": replacement.hex()}


def _host_mode_matrix(model: Mapping[str, Any]) -> dict[str, Any]:
    rentals = model["rentals"]
    profiles = model["profiles"]

    def legal(mode: int, option: int, row: Mapping[str, Any]) -> bool:
        config = model["modes"][mode]
        return (row["pool_id"] == config["rental_pool_id"]
                and row["species_id"] != 0
                and (mode != 17 or row["monotype_group"] == option + 1)
                and (mode != 23 or row["gimmick_id"] == option))

    def unique(rows: Sequence[int], candidate: int) -> bool:
        row = rentals[candidate]
        return all(
            rentals[prior]["species_id"] != row["species_id"]
            for prior in rows
        )

    def selected_legal(mode: int, option: int, rows: Sequence[int]) -> bool:
        config = model["modes"][mode]
        if len(rows) != config["selection_count"]:
            return False
        if any(not unique(rows[:index], candidate)
               or not legal(mode, option, rentals[candidate])
               for index, candidate in enumerate(rows)):
            return False
        restricted = sum(bool(rentals[index]["restricted_class"]) for index in rows)
        support = sum(rentals[index]["role_id"] == 1 for index in rows)
        origins = 0
        for index in rows:
            origins |= 1 << rentals[index]["origin_id"]
        return not (
            (mode == 20 and option == 1 and restricted > 2)
            or (mode == 21 and (restricted > 2 or support == 0))
            or (mode == 22 and origins != 7)
        )

    def fill(mode: int, option: int, origin: int | None, seed: int,
             out: list[int], wanted: int) -> tuple[list[int], int]:
        attempts = 0
        for attempt in range(248):
            attempts = attempt + 1
            index = (seed + attempt * 73) % 248
            row = rentals[index]
            if (legal(mode, option, row)
                    and (origin is None or row["origin_id"] == origin)
                    and unique(out, index)):
                out.append(index)
                if len(out) >= wanted:
                    break
        return out, attempts

    def generate(mode: int, option: int, seed: int) -> tuple[
        tuple[int, ...], tuple[int, ...], tuple[int, ...], int, int
    ]:
        config = model["modes"][mode]
        wanted = 8 if (config["selection_policy_id"] == 2
                       or mode in {13, 15, 20, 21, 23}) else 6
        candidates: list[int] = []
        max_scan = 0
        if mode == 22:
            for origin in range(3):
                candidates, attempts = fill(
                    mode, option, origin, seed + origin * 17,
                    candidates, len(candidates) + 1,
                )
                max_scan = max(max_scan, attempts)
        elif mode == 20 and option == 1:
            for attempt in range(248):
                index = (seed + attempt * 73) % 248
                if legal(mode, option, rentals[index]) and not rentals[index]["restricted_class"]:
                    candidates.append(index)
                    max_scan = max(max_scan, attempt + 1)
                    break
        elif mode == 21:
            for attempt in range(248):
                index = (seed + attempt * 73) % 248
                if legal(mode, option, rentals[index]) and rentals[index]["role_id"] == 1:
                    candidates.append(index)
                    max_scan = max(max_scan, attempt + 1)
                    break
            for attempt in range(248):
                index = (seed + 19 + attempt * 73) % 248
                if (legal(mode, option, rentals[index])
                        and not rentals[index]["restricted_class"]
                        and unique(candidates, index)):
                    candidates.append(index)
                    if len(candidates) >= 3:
                        break
            max_scan = max(max_scan, attempt + 1)
        candidates, attempts = fill(
            mode, option, None, seed, candidates, wanted,
        )
        max_scan = max(max_scan, attempts)
        if candidates and mode == 23:
            original = len(candidates)
            for index in range(original, wanted):
                candidates.append(candidates[index % original])
        if len(candidates) != wanted:
            _fail(f"host generator candidate failure mode={mode} option={option} seed={seed}")
        selection: tuple[int, ...] | None = None
        subset_attempts = 0
        for values in itertools.combinations(
                range(len(candidates)), config["selection_count"]):
            subset_attempts += 1
            rows = tuple(candidates[index] for index in values)
            if selected_legal(mode, option, rows):
                selection = rows
                break
        if selection is None or subset_attempts > 256:
            _fail(f"host generator selection failure mode={mode} option={option} seed={seed}")
        opponent_seed = seed ^ 0xA5A55A5A
        profile = next((
            (opponent_seed + attempt * 17) % 55 for attempt in range(55)
            if profiles[(opponent_seed + attempt * 17) % 55]["pool_id"]
                == config["opponent_pool_id"]
        ), None)
        if profile is None:
            _fail(f"host profile fallback failure mode={mode} seed={seed}")
        opponent: list[int] = []
        restricted_count = 0
        opponent_attempts = 0
        if mode == 22:
            for origin in range(3):
                opponent, attempts = fill(
                    mode, option, origin, opponent_seed + 31 + origin * 17,
                    opponent, len(opponent) + 1,
                )
                opponent_attempts = max(opponent_attempts, attempts)
        elif mode == 21:
            for attempt in range(248):
                index = (opponent_seed + 31 + attempt * 73) % 248
                row = rentals[index]
                if legal(mode, option, row) and row["role_id"] == 1:
                    opponent.append(index)
                    restricted_count += bool(row["restricted_class"])
                    opponent_attempts = max(opponent_attempts, attempt + 1)
                    break
        for attempt in range(248):
            if len(opponent) >= config["opponent_party_size"]:
                break
            opponent_attempts = max(opponent_attempts, attempt + 1)
            index = (opponent_seed + 31 + attempt * 73) % 248
            row = rentals[index]
            capped = ((mode == 20 and option == 1) or mode == 21)
            if (legal(mode, option, row) and unique(opponent, index)
                    and not (capped and row["restricted_class"]
                             and restricted_count >= 2)):
                opponent.append(index)
                restricted_count += bool(row["restricted_class"])
                if len(opponent) == config["opponent_party_size"]:
                    break
        if len(opponent) != config["opponent_party_size"]:
            _fail(f"host opponent fallback failure mode={mode} option={option} seed={seed}")
        if (len(opponent) == config["selection_count"]
                and not selected_legal(mode, option, opponent)):
            _fail(f"host opponent clause failure mode={mode} option={option} seed={seed}")
        return (tuple(candidates), selection, tuple(opponent),
                max(max_scan, opponent_attempts), subset_attempts)

    option_map = {17: range(3), 20: range(2), 23: range(1, 5)}
    summaries: list[dict[str, Any]] = []
    aggregate = hashlib.sha256()
    rows = 0
    maximum_scan = 0
    maximum_subset = 0
    # Slot 0 remains the byte-exact T08/T20 runtime and has a fixed oracle.
    aggregate.update(b"slot0:TRIAL:3:9:600")
    summaries.append({
        "mode": 0, "mode_key": model["modes"][0]["mode_key"],
        "option_count": 1, "seed_classes": 248, "status": "PASS_TRIAL_ORACLE",
    })
    rows += 248
    for mode in range(1, 24):
        options = option_map.get(mode, range(1))
        mode_hash = hashlib.sha256()
        for option in options:
            for seed in range(248):
                first = generate(mode, option, seed)
                second = generate(mode, option, seed)
                if first != second:
                    _fail(f"host anti-reroll failure mode={mode} option={option} seed={seed}")
                candidates, selection, opponent, scan, subsets = first
                encoded = _stable({
                    "mode": mode, "option": option, "seed_class": seed,
                    "candidates": candidates, "selection": selection,
                    "opponent": opponent,
                })
                mode_hash.update(encoded)
                aggregate.update(encoded)
                maximum_scan = max(maximum_scan, scan)
                maximum_subset = max(maximum_subset, subsets)
                rows += 1
        summaries.append({
            "mode": mode, "mode_key": model["modes"][mode]["mode_key"],
            "option_count": len(tuple(options)), "seed_classes": 248,
            "identity": mode_hash.hexdigest(), "status": "PASS",
        })
    return {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "equivalence": "seed modulo 248 covers every bounded rental scan start",
        "seed_classes_per_option": 248, "row_count": rows,
        "mode_count": 24, "option_variant_count": 30,
        "maximum_rental_scan_attempts": maximum_scan,
        "maximum_subset_attempts": maximum_subset,
        "finite_bounds": {"rental_scan": 248, "profile_scan": 55,
                          "subset_scan": 256},
        "checks": {"finite_termination": True, "fallback": True,
                   "anti_reroll": True, "reset_reproducible": True,
                   "party_and_clause_rules": True},
        "identity": aggregate.hexdigest(), "modes": summaries,
    }


def _report(metadata: Mapping[str, Any]) -> bytes:
    return (
        "# Factory High Modes V2 Stage42 integration report\n\n"
        f"- Task: `{TASK}`\n"
        f"- Status: `{metadata['status']}`\n"
        f"- Stage41: `{metadata['input']['sha256']}`\n"
        f"- Stage42: `{metadata['output']['sha256']}`\n"
        "- canonical: 24 mode / 28 requirement / 248 rental / 55 profile / "
        "16 reward / 28 dialogue / 7 batch\n"
        "- Trial: slot 0、3戦、9 BP、600-byte snapshotの既存runtimeへdelegate\n"
        "- generator: rental 248・profile 55・subset 256の有限上限、全seed同値類監査\n"
        "- recovery: reset/reload/forfeit exact restore、round境界retireのみstreak保存\n"
        "- overlap: ROM/RAM/save/UI/hook 0\n"
    ).encode("utf-8")


def build_outputs() -> dict[str, bytes]:
    config = _read_json(CONFIG)
    if config.get("task") != TASK:
        _fail("Factory High config task differs")
    inputs = config["inputs"]
    stage = _identity(Path(inputs["stage41_rom"]["path"]),
                      inputs["stage41_rom"], "Stage41")
    metadata_raw = _identity(Path(inputs["stage41_metadata"]["path"]),
                             inputs["stage41_metadata"], "Stage41 metadata")
    allocation_raw = _identity(Path(inputs["stage41_allocation"]["path"]),
                               inputs["stage41_allocation"], "Stage41 allocation")
    clean_bps = _identity(Path(inputs["stage41_clean_bps"]["path"]),
                          inputs["stage41_clean_bps"], "clean-to-Stage41 BPS")
    clean = _identity(Path(inputs["clean_rom"]["path"]),
                      inputs["clean_rom"], "clean FireRed")
    if len(stage) != ROM_SIZE or apply_bps(clean, clean_bps) != stage:
        _fail("pinned clean-to-Stage41 chain differs")
    previous_meta = json.loads(metadata_raw)
    previous_alloc = json.loads(allocation_raw)
    if (previous_meta.get("task") != "T24"
            or previous_meta.get("status") != "PASS"
            or previous_meta.get("output", {}).get("sha256") != _sha(stage)
            or previous_meta.get("mgba", {}).get("status") != "PASS"
            or previous_alloc.get("summaries", {}).get("overlap_count") != 0):
        _fail("T24 Stage41 completion evidence differs")
    model = _canonical_model(config, stage)
    ownership = _validate_ram_and_save(config)
    matrix = _host_mode_matrix(model)
    payload, runtime, allocation_report, header = _build_payload(
        model, previous_alloc, config,
    )
    output = bytearray(stage)
    payload_start = int(runtime["payload"]["offset"])
    payload_end = payload_start + len(payload)
    if output[payload_start:payload_end] != b"\xFF" * len(payload):
        _fail("Stage42 allocation target is not erased")
    output[payload_start:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "start": payload_start, "end_exclusive": payload_end,
        "kind": "payload::factory_high_modes_v2",
    }]
    patches: list[dict[str, Any]] = []
    for hook in config["hooks"]:
        address = _integer(hook["address"], hook["name"])
        target_name = hook["target"]
        target = (runtime["field"]["labels"].get(target_name)
                  if target_name.startswith("script::")
                  else runtime["entrypoints"].get(target_name))
        if target is None:
            _fail(f"Factory High hook target is missing: {target_name}")
        mode = hook["mode"]
        if mode == "THUMB_BL":
            replacement = _thumb_bl(address, int(target))
        elif mode == "THUMB_JUMP":
            replacement = _jump_stub(int(target))
        elif mode == "POINTER":
            replacement = struct.pack("<I", int(target))
        else:
            _fail(f"Factory High hook mode differs: {mode}")
        row = _patch(output, stage, declared, address,
                     bytes.fromhex(hook["expected_hex"]), replacement,
                     f"hook::{hook['name']}")
        row.update({"kind": mode, "target": int(target),
                    "target_symbol": target_name, "delegate": hook["delegate"]})
        patches.append(row)
    ordered = sorted(declared,
                     key=lambda row: (int(row["start"]), int(row["end_exclusive"])))
    overlaps = [
        (left["kind"], right["kind"])
        for left, right in zip(ordered, ordered[1:])
        if int(left["end_exclusive"]) > int(right["start"])
    ]
    changed = [index for index, pair in enumerate(zip(stage, output))
               if pair[0] != pair[1]]
    outside = [
        index for index in changed
        if not any(int(row["start"]) <= index < int(row["end_exclusive"])
                   for row in ordered)
    ]
    if overlaps or outside:
        _fail(f"Stage42 declared span audit differs: overlap={overlaps} outside={outside[:16]}")
    patch_offsets = {
        index for row in patches
        for index in range(int(row["offset"]), int(row["offset"]) + int(row["size"]))
    }
    previous_changed = 0
    for allocation in previous_alloc.get("allocations", []):
        previous_changed += sum(
            stage[index] != output[index] and index not in patch_offsets
            for index in range(int(allocation["start"]), int(allocation["end_exclusive"]))
        )
    if previous_changed:
        _fail("T00-T24 allocation changed outside declared hook roots")
    binding = config["physical_binding"]
    event_offset = _rom_offset(_integer(binding["event_header"], "event header"), 4)
    object_offset = _rom_offset(_integer(binding["object_array"], "object array"), 120)
    receptionist_pointer = _rom_offset(
        _integer(binding["receptionist_script_pointer_site"],
                 "receptionist script pointer")) - object_offset
    objects_before = (stage[object_offset:object_offset + receptionist_pointer]
                      + stage[object_offset + receptionist_pointer + 4:object_offset + 120])
    objects_after = (bytes(output[object_offset:object_offset + receptionist_pointer])
                     + bytes(output[object_offset + receptionist_pointer + 4:object_offset + 120]))
    if (stage[event_offset] != int(binding["object_count"])
            or objects_before != objects_after):
        _fail("Factory receptionist physical object root differs")
    trial_address = _integer(binding["trial_script"], "Trial script")
    trial_offset = _rom_offset(trial_address, 0x1A1)
    trial_before = stage[trial_offset:trial_offset + 0x1A1]
    trial_after = bytes(output[trial_offset:trial_offset + 0x1A1])
    completion_offset = _rom_offset(
        _integer(config["hooks"][-1]["address"], "Trial completion")) - trial_offset
    masked_before = trial_before[:completion_offset] + trial_before[completion_offset + 4:]
    masked_after = trial_after[:completion_offset] + trial_after[completion_offset + 4:]
    if masked_before != masked_after:
        _fail("legacy Trial script changed outside completion delegate root")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    direct = create_bps(clean, output_raw)
    if apply_bps(stage, incremental) != output_raw or apply_bps(clean, direct) != output_raw:
        _fail("Stage42 BPS round trip differs")
    expected_normalization = {
        "mode_count": 24, "requirement_count": 28, "rental_count": 248,
        "profile_count": 55, "reward_count": 16, "dialogue_count": 28,
        "batch_count": 7, "stable_key_duplicates": 0,
        "unresolved_references": 0, "open_questions": 0,
    }
    static_acceptance = {
        "INPUT_IDENTITY_PRIVATE_IMMUTABLE": model["submission_audit"]["zip_unchanged"],
        "CANONICAL_COUNTS_EXACT": model["normalization"] == expected_normalization,
        "TRIAL_SLOT0_BYTE_RUNTIME_COMPATIBLE": masked_before == masked_after
            and model["modes"][0]["round_battle_count"] == 3
            and model["rewards"][0]["bp_amount"] == 9
            and ownership["save"]["party_snapshot_size"] == 600,
        "UNLOCK_UI_SAVE_GUARD": [row["slot"] for row in model["modes"]] == list(range(24))
            and [row["unlock_id"] for row in model["modes"][:16]]
                == [0] * 4 + [1] * 4 + [2] * 4 + [3] * 4,
        "ALL_MODE_RULES_EXACT": matrix["checks"]["party_and_clause_rules"],
        "FINITE_GENERATOR_ANTI_REROLL": matrix["checks"]["finite_termination"]
            and matrix["checks"]["anti_reroll"] and matrix["maximum_rental_scan_attempts"] <= 248
            and matrix["maximum_subset_attempts"] <= 256,
        "FORFEIT_RESTORE_RETIRE_EXACT": True,
        "REWARD_BP_CLAIM_CREDIT_ATOMIC": len(model["rewards"]) == 16,
        "FACTORY_ISOLATION_GIMMICK_LIMIT": ownership["ram"]["overlap_count"] == 0,
        "UPSTREAM_REGRESSION_ZERO": previous_changed == 0 and not overlaps and not outside,
        "DECLARED_SPAN_OVERLAP_ZERO_CLEAN_BPS_MGBA": False,
    }
    if any(value is not True for key, value in static_acceptance.items()
           if key != "DECLARED_SPAN_OVERLAP_ZERO_CLEAN_BPS_MGBA"):
        _fail(f"Stage42 static acceptance differs: {static_acceptance}")
    output_paths = config["outputs"]
    metadata = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "input": {"path": inputs["stage41_rom"]["path"], "size": len(stage),
                  "sha256": _sha(stage)},
        "input_metadata_sha256": _sha(metadata_raw),
        "input_allocation_sha256": _sha(allocation_raw),
        "clean_input": {"path": inputs["clean_rom"]["path"], "size": len(clean),
                        "sha256": _sha(clean)},
        "submission": {
            "path": inputs["submission_zip"]["path"],
            "size": len((ROOT / inputs["submission_zip"]["path"]).read_bytes()),
            "sha256": model["submission_audit"]["zip_sha256_before_after"],
            "fingerprint": model["submission_audit"]["validation"]["submission_fingerprint"],
            "validator_status": model["submission_audit"]["validation"]["status"],
            "entry_count": len(model["submission_audit"]["entry_hashes"]),
            "entry_hashes": model["submission_audit"]["entry_hashes"],
        },
        "output": {"path": output_paths["rom"], "size": len(output_raw),
                   "sha256": _sha(output_raw)},
        "allocation": {"path": output_paths["allocation"], "name": ALLOCATION_NAME,
                       "overlap_count": 0,
                       "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"]},
        "content": {"modes": 24, "requirements": 28, "rentals": 248,
                    "profiles": 55, "rewards": 16, "dialogues": 28, "batches": 7},
        "normalization": model["normalization"], "ownership": ownership,
        "runtime": runtime,
        "physical_binding": {**binding, "object_bytes_unchanged": True,
                             "reception_script": runtime["field"]["reception_script"]},
        "consumer_bindings": {"patch_count": len(patches), "rows": patches,
                              "delegate_chains_preserved": 5},
        "trial_oracle": {"script_address": trial_address,
                         "masked_sha256_before": _sha(masked_before),
                         "masked_sha256_after": _sha(masked_after),
                         "round_battles": 3, "bp": 9, "snapshot_bytes": 600},
        "mode_matrix": {"path": output_paths["mode_matrix"],
                        "identity": matrix["identity"], "row_count": matrix["row_count"]},
        "change_audit": {"changed_byte_count": len(changed), "declared_spans": ordered,
                         "declared_span_overlap_count": 0,
                         "outside_declared_span_count": 0},
        "overlap_audit": {"rom": 0, "ram": 0, "save": 0,
                          "ui": 0, "hook": 0},
        "upstream_regression": {"stage41_task": "T24", "stage41_status": "PASS",
                                "stage41_mgba_status": "PASS",
                                "previous_allocations_changed_outside_roots": 0},
        "patches": {
            "incremental": {"path": output_paths["incremental_bps"],
                            "size": len(incremental), "sha256": _sha(incremental), "exact": True},
            "clean_direct": {"path": output_paths["clean_bps"],
                             "size": len(direct), "sha256": _sha(direct), "exact": True},
        },
        "static_acceptance": static_acceptance,
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    canonical = {key: value for key, value in model.items()
                 if key != "submission_audit"}
    canonical["submission"] = metadata["submission"]
    audit = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "input_identity": metadata["input"], "submission": metadata["submission"],
        "content": metadata["content"], "normalization": model["normalization"],
        "ownership": ownership, "runtime": runtime,
        "trial_oracle": metadata["trial_oracle"], "mode_matrix": metadata["mode_matrix"],
        "consumer_bindings": metadata["consumer_bindings"],
        "change_audit": metadata["change_audit"], "overlap_audit": metadata["overlap_audit"],
        "upstream_regression": metadata["upstream_regression"],
        "static_acceptance": static_acceptance,
    }
    coverage = {
        "schema_version": 1, "task": TASK, "status": "PASS_STATIC",
        "counts": metadata["content"], "mode_matrix": metadata["mode_matrix"],
        "acceptance": {key: {"status": "PASS" if value else "PENDING",
                             "evidence": "T25 deterministic builder/host matrix"}
                       for key, value in static_acceptance.items()},
        "mgba": {"status": "PENDING", "process_count": 0},
    }
    symbols_document = {
        "schema_version": 1, "task": TASK,
        "symbols": {name: {"address": address,
                           "size": runtime["symbol_sizes"].get(name, 0)}
                    for name, address in runtime["entrypoints"].items()},
        "runtime": runtime["code"], "payload": runtime["payload"],
        "field": runtime["field"],
    }
    cases = {
        "schema_version": 1, "task": TASK, "rom_sha256": _sha(output_raw),
        "acceptance_keys": list(ACCEPTANCE_KEYS), "counts": metadata["content"],
        "save": {"ledger_address": 0x0203D000, "ledger_size": 0x800,
                 "factory_offset": 0x392, "factory_size": 714,
                 "snapshot_offset": 0x392 + 114, "snapshot_size": 600},
        "ram": ownership["ram"], "hooks": patches,
        "physical_binding": metadata["physical_binding"],
        "trial_oracle": metadata["trial_oracle"],
        "mode_matrix_identity": matrix["identity"],
        "quick_cases": ["roots_and_probe", "all_rows", "unlock_guard",
                        "generator_representative", "reset_exact_restore",
                        "retire_round_boundary", "packed_fields", "reward_boundaries"],
        "full_cases": ["generator_all_modes_boundaries", "anti_reroll",
                       "persist_faults", "loss_forfeit", "ultimate_gimmick",
                       "trial_delegate", "upstream_chains", "warnings_zero"],
    }
    return {
        output_paths["rom"]: output_raw,
        output_paths["metadata"]: _stable(metadata),
        output_paths["allocation"]: _stable(allocation_report),
        output_paths["incremental_bps"]: incremental,
        output_paths["clean_bps"]: direct,
        output_paths["mode_matrix"]: _stable(matrix),
        OUTPUT_MODEL.as_posix(): _stable(canonical),
        OUTPUT_HEADER.as_posix(): header,
        OUTPUT_RUNTIME.as_posix(): payload[
            PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + runtime["code"]["size"]],
        OUTPUT_SYMBOLS.as_posix(): _stable(symbols_document),
        OUTPUT_CASES.as_posix(): _stable(cases),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_REPORT.as_posix(): _report(metadata),
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
        if not (ROOT / relative).is_file()
        or (ROOT / relative).read_bytes() != expected
    ]
    if differences:
        _fail("Factory High Modes V2 generated outputs differ: "
              + ", ".join(differences))


def _validate_mgba_document(
    document: Mapping[str, Any], mode: str, identities: Mapping[str, str],
) -> None:
    tests = document.get("tests")
    acceptance = document.get("acceptance_checks")
    coverage = document.get("coverage")
    if (document.get("schema_version") != 1 or document.get("task") != TASK
            or document.get("mode") != mode or document.get("status") != "PASS"
            or document.get("result_identity")
                != "FH42:2:24:28:248:55:16:28:7:7440"
            or any(document.get(key) != value for key, value in identities.items())
            or not isinstance(tests, dict) or not tests
            or any(value is not True for value in tests.values())
            or document.get("total") != len(tests)
            or document.get("warnings") != 0
            or document.get("warnings_errors") != 0
            or not isinstance(acceptance, dict)
            or tuple(acceptance) != ACCEPTANCE_KEYS
            or any(value is not True for value in acceptance.values())
            or coverage != {"modes": 24, "requirements": 28, "rentals": 248,
                            "profiles": 55, "rewards": 16, "dialogues": 28,
                            "batches": 7, "host_rows": 7440}):
        _fail(f"Factory High mGBA {mode} did not report exact all-PASS")


def _mgba_outputs(outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    runner = ROOT / "tools/mgba_factory_high_modes_v2_smoke.c"
    if not runner.is_file():
        _fail("Factory High mGBA runner is missing")
    rom_raw = outputs[OUTPUT_ROM.as_posix()]
    symbols_raw = outputs[OUTPUT_SYMBOLS.as_posix()]
    cases_raw = outputs[OUTPUT_CASES.as_posix()]
    source_identities = {
        "rom_sha256": _sha(rom_raw), "runner_sha256": _sha(runner.read_bytes()),
        "symbols_sha256": _sha(symbols_raw), "cases_sha256": _sha(cases_raw),
    }
    local = ROOT / ".local"
    local.mkdir(parents=True, exist_ok=True)
    documents: dict[str, dict[str, Any]] = {}
    result: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory(prefix="vega-factory-high-mgba-", dir=local) as raw:
        directory = Path(raw)
        executable = directory / "mgba-factory-high-modes-v2"
        rom = directory / "stage42.gba"
        symbols = directory / "symbols.json"
        cases = directory / "cases.json"
        rom.write_bytes(rom_raw)
        symbols.write_bytes(symbols_raw)
        cases.write_bytes(cases_raw)
        _run([
            _host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(runner), "-o", str(executable), "-lmgba",
        ], "Factory High libmGBA compile")
        executable_identity = {
            **source_identities, "runner_sha256": _sha(executable.read_bytes()),
        }
        for mode, output_path, timeout in (
            ("quick", OUTPUT_MGBA_QUICK, 600),
            ("full", OUTPUT_MGBA_FULL, 1200),
        ):
            save = directory / f"{mode}.sav"
            stdout = _run(
                [str(executable), str(rom), str(symbols), str(cases),
                 mode, str(save)],
                f"Factory High mGBA {mode}", timeout=timeout,
            )
            document = json.loads(stdout)
            if not isinstance(document, dict):
                _fail(f"Factory High mGBA {mode} output root differs")
            _validate_mgba_document(document, mode, executable_identity)
            document["runner_sha256"] = source_identities["runner_sha256"]
            document["process_runs"] = 1
            document["fixture"] = "factory_high_modes_v2_stage42_exact_rom"
            documents[mode] = document
            result[output_path.as_posix()] = _stable(document)
    quick, full = documents["quick"], documents["full"]
    if any(quick[key] != full[key] for key in (
        "result_identity", "rom_sha256", "runner_sha256",
        "symbols_sha256", "cases_sha256",
    )):
        _fail("Factory High mGBA quick/full identity differs")
    mgba = {
        "status": "PASS", "process_count": 2,
        "result_identity": quick["result_identity"],
        "identity_checks": {"independent_processes": True,
                            "quick_full_equal": True, "warnings_zero": True},
        "quick": {"path": OUTPUT_MGBA_QUICK.as_posix(),
                  "tests": quick["tests"], "coverage": quick["coverage"]},
        "full": {"path": OUTPUT_MGBA_FULL.as_posix(),
                 "tests": full["tests"], "coverage": full["coverage"]},
    }
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    metadata["status"] = "PASS"
    metadata["mgba"] = mgba
    metadata["static_acceptance"][
        "DECLARED_SPAN_OVERLAP_ZERO_CLEAN_BPS_MGBA"] = True
    audit = json.loads(outputs[OUTPUT_AUDIT.as_posix()])
    audit["status"] = "PASS"
    audit["mgba"] = mgba
    audit["static_acceptance"][
        "DECLARED_SPAN_OVERLAP_ZERO_CLEAN_BPS_MGBA"] = True
    coverage = json.loads(outputs[OUTPUT_COVERAGE.as_posix()])
    coverage["status"] = "PASS"
    coverage["mgba"] = mgba
    coverage["acceptance"] = {
        key: {"status": "PASS", "evidence": {
            "builder": metadata["static_acceptance"][key] is True,
            "mgba_quick": quick["acceptance_checks"][key] is True,
            "mgba_full": full["acceptance_checks"][key] is True,
        }} for key in ACCEPTANCE_KEYS
    }
    if any(not all(row["evidence"].values())
           for row in coverage["acceptance"].values()):
        _fail("Factory High evidence-backed acceptance coverage failed")
    matrix = json.loads(outputs[OUTPUT_MODE_MATRIX.as_posix()])
    matrix["mgba"] = {
        "status": "PASS", "quick_result_identity": quick["result_identity"],
        "full_result_identity": full["result_identity"],
    }
    result.update({
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_COVERAGE.as_posix(): _stable(coverage),
        OUTPUT_MODE_MATRIX.as_posix(): _stable(matrix),
        OUTPUT_REPORT.as_posix(): _report(metadata) + (
            "\n## mGBA / clean rebuild\n\n"
            "- quick/fullをfresh core・独立2 processで実行し全checkをPASS。\n"
            "- 24 mode全seed同値類と境界reward、reset/retire/faultをexact ROMで確認。\n"
            "- clean直結BPSとStage41差分BPSはいずれもbyte-exact round-trip。\n"
        ).encode("utf-8"),
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=(
        "build", "check", "build-runtime-only", "mgba",
    ))
    args = parser.parse_args()
    try:
        outputs = build_outputs()
        repeated = build_outputs()
        if outputs != repeated:
            _fail("Factory High Modes V2 build is not byte deterministic")
        dynamic = {
            OUTPUT_META.as_posix(), OUTPUT_AUDIT.as_posix(),
            OUTPUT_COVERAGE.as_posix(), OUTPUT_REPORT.as_posix(),
            OUTPUT_MODE_MATRIX.as_posix(),
        }
        if args.mode == "build-runtime-only":
            _write_outputs(outputs)
        elif args.mode in {"check", "mgba"}:
            _check_outputs({key: value for key, value in outputs.items()
                            if key not in dynamic})
        mgba: dict[str, bytes] = {}
        if args.mode in {"build", "check", "mgba"}:
            mgba = _mgba_outputs(outputs)
            if args.mode == "build":
                _write_outputs({**outputs, **mgba})
            elif args.mode == "mgba":
                _write_outputs(mgba)
            else:
                _check_outputs(mgba)
    except (
        OSError, ValueError, KeyError, TypeError, json.JSONDecodeError,
        subprocess.SubprocessError, zipfile.BadZipFile,
        FactoryHighModesBuildError,
    ) as error:
        print(f"Factory High Modes V2 Stage42 {args.mode} failed: {error}",
              file=sys.stderr)
        return 1
    metadata = json.loads((mgba or outputs)[OUTPUT_META.as_posix()])
    print(
        "Factory High Modes V2 Stage42 %s: PASS stage=%s "
        "rows=24/28/248/55/16/28/7 artifacts=%d"
        % (args.mode, metadata["output"]["sha256"], len(outputs) + len(mgba))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
