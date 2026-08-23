#!/usr/bin/env python3
"""Stage 35へQOL 35機能の実runtime/UI/hookを接続しStage 36を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import struct
import subprocess
import sys
import tempfile
from collections import Counter
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
from tools.regression.rom_runtime import _charmap, _encode_text  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv  # noqa: E402


TASK = "T19"
ROM_SIZE = 32 * 1024 * 1024
INPUT_ROM = Path("build/stages/35_trainer_changekit_final.gba")
INPUT_META = Path("build/stages/35_trainer_changekit_final.json")
INPUT_ALLOC = Path("build/stages/35_allocation.json")
BATTLE_CORE_META = Path("build/stages/06_battle_core.json")
BASE_ROM = Path("build/final/vega-modern-kanto-v1.4.0.gba")
CLEAN_ROM = Path("inputs/private/FireRed_JPN_Rev0_clean.gba")
OUTPUT_ROM = Path("build/stages/36_qol_production.gba")
OUTPUT_META = Path("build/stages/36_qol_production.json")
OUTPUT_ALLOC = Path("build/stages/36_allocation.json")
OUTPUT_SERIALIZED = Path("generated/runtime/qol_production_serialized.json")
OUTPUT_HEADER = Path("generated/runtime/qol_production_generated.h")
OUTPUT_RUNTIME = Path("generated/runtime/qol_production_runtime.bin")
OUTPUT_SYMBOLS = Path("generated/runtime/qol_production_symbols.json")
OUTPUT_CASES = Path("generated/runtime/qol_production_mgba_cases.csv")
OUTPUT_AUDIT = Path("reports/generated/qol_production_audit.json")
OUTPUT_COVERAGE = Path("reports/generated/qol_production_coverage.json")
OUTPUT_REPORT = Path("reports/generated/qol_production.md")
OUTPUT_MGBA_QUICK = Path("build/stages/36_mgba_qol_production_quick.json")
OUTPUT_MGBA_FULL = Path("build/stages/36_mgba_qol_production_full.json")
PATCH_INCREMENTAL = Path("build/patches/trainer-stage35-to-qol-production-stage36.bps")
PATCH_CUMULATIVE = Path("build/patches/vega-modern-kanto-v1.4.0-to-qol-production-stage36.bps")

EXPECTED_STAGE35_SHA256 = "60b00504b7c90ee026c15ee285be69edc43c12c0eedcc64096fcadd1f290aa7b"
EXPECTED_STAGE35_META_SHA256 = "51240a82f53eaa59eae3dd5dda1c802afac870a8ec2e36a2611876d09fc96c14"
EXPECTED_STAGE35_ALLOC_SHA256 = "34412386b4e93b15b8c2214147f7aa444cb3e0f973ccae086b8998ceded75767"
EXPECTED_STAGE06_SHA256 = "32b3e4d72b538c2bd085d39cc69af81c79d1319bf71e943fe888c911265366d3"
EXPECTED_BASE_SHA256 = "30f19ee3ebab856379393a572bfde33c2ccfdac7351e73ff3a7f3e231f3f553e"
EXPECTED_CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"
EXPECTED_RESEARCH_SHA256 = "da96838351dfa2f003f70378d40699d3d1208932781535d8cca6729463999b15"
EXPECTED_RESEARCH_RULE_COUNT = 846

FEATURE_COUNT = 35
PAYLOAD_HEADER_SIZE = 0x100
ALLOCATION_NAME = "qol_production_stage36_payload"
RAM_OWNER = "T19_QOL_PRODUCTION"
CLASSIFICATIONS = {"LIVE_ENGINE_UI", "LIVE_SERVICE", "LIVE_SUPPLY"}
ACCEPTANCE_KEYS = (
    "35_UNIQUE_LIVE_OWNERS",
    "REAL_BOX_PSS_SAVE",
    "NORMAL_USER_ENTRY",
    "UNLOCK_SAVE_RELOAD",
    "ATOMIC_CANCEL_CAPACITY_FORBIDDEN",
    "PC_MULTI_BOX_EGG_SPECIAL_ADDED_SPECIES",
    "BASKET_255_256_QUEUE_SAVE",
    "AUTO_RANDOM_ONLY",
    "TEXT_CONTROL_AND_MOVEMENT_EVENTS",
    "TRAINING_STATS_DISPLAY_SAVE",
    "SUPPLY_UNLOCK_ONCE_REPEAT",
    "STAGE35_TRAINER_REGRESSION",
    "DETERMINISTIC_BPS_DECLARED_ONLY",
    "MGBA_TWO_PROCESS",
    "DOC_LEDGER_BUILD_ALIGNMENT",
)
DYNAMIC_ACCEPTANCE_KEYS = (
    "REAL_BOX_PSS_SAVE",
    "NORMAL_USER_ENTRY",
    "UNLOCK_SAVE_RELOAD",
    "ATOMIC_CANCEL_CAPACITY_FORBIDDEN",
    "PC_MULTI_BOX_EGG_SPECIAL_ADDED_SPECIES",
    "BASKET_255_256_QUEUE_SAVE",
    "AUTO_RANDOM_ONLY",
    "TEXT_CONTROL_AND_MOVEMENT_EVENTS",
    "TRAINING_STATS_DISPLAY_SAVE",
    "SUPPLY_UNLOCK_ONCE_REPEAT",
)

PROGRESSION = Path("content/qol_progression.csv")
BINDINGS = Path("config/qol_production_bindings.csv")
FEATURE_MATRIX = Path("config/feature_matrix.csv")
QOL_B = Path("config/qol_b.json")
SUPPLY = Path("content/qol_supply.csv")
SUPPLY_CATALOG = Path("config/qol_production_supply_catalog.csv")
ITEMS = Path("manifests/item_ids.csv")
TYPES = Path("manifests/type_ids.csv")
ABILITIES = Path("manifests/ability_ids.csv")
MOVES = Path("manifests/move_ids.csv")
MAPS = Path("content/maps.csv")
MAP_BINDINGS = Path("content/map_bindings.csv")
RESEARCH = Path("manifests/research_encounters.csv")
SPECIES = Path("manifests/species_ids.csv")
SPECIAL = Path("vendor/vega_acquisition/content/special_event_catalog_125.csv")
RAIDS = Path("manifests/raid_encounters.csv")
TRAINER_RUNTIME_CONSUMERS = Path(
    "content/trainer_changekit_final/trainer_runtime_consumers.csv"
)
HOOK_CONTRACT = Path("overlays/qol_production/hook_contract_stage35.json")


def _cfru_symbol_handoff() -> tuple[dict[str, int], str]:
    metadata_path = ROOT / BATTLE_CORE_META
    metadata = _read_json(metadata_path)
    output = metadata.get("output")
    symbols = metadata.get("downstream_symbols")
    if (
        metadata.get("status") != "PASS"
        or not isinstance(output, dict)
        or output.get("sha256") != EXPECTED_STAGE06_SHA256
        or not isinstance(symbols, dict)
    ):
        _fail("Stage06 CFRU downstream symbol handoff is missing/stale")
    resolved: dict[str, int] = {}
    for name, value in symbols.items():
        if (
            not isinstance(name, str)
            or isinstance(value, bool)
            or not isinstance(value, int)
            or not 0x09000000 <= value < 0x09200000
            or value & 1
        ):
            _fail(f"Stage06 CFRU downstream symbol is invalid: {name}")
        resolved[name] = value
    if not resolved or len(set(resolved.values())) != len(resolved):
        _fail("Stage06 CFRU downstream symbol handoff is empty/aliased")
    return resolved, _sha(metadata_path.read_bytes())

UNLOCK_CODES = {
    "VEGA_PRE_ENTRY": 0,
    "VEGA_BADGE_1": 1,
    "VEGA_BADGE_2": 2,
    "VEGA_SHIOU_BADGE_3": 3,
    "VEGA_BADGE_5": 4,
    "VEGA_BADGE_6": 5,
    "VEGA_BADGE_7": 6,
    "VEGA_BADGE_8": 7,
    "VEGA_HALL_OF_FAME": 8,
    "KANTO_EARLY_ACCESS": 9,
    "KANTO_CERT_1": 10,
    "KANTO_CERT_2": 11,
    "KANTO_CERT_3": 12,
    "KANTO_CERT_4": 13,
    "KANTO_CERT_5": 14,
    "KANTO_CERT_6": 15,
    "KANTO_LEAGUE": 16,
}

REQUIRED_ENTRYPOINTS = {
    "VegaQolProduction_Probe",
    "VegaQolProduction_Dispatch",
    "VegaQolProduction_StartMenuPanel",
    "VegaQolProduction_PssHandleInputAdapter",
    "VegaQolProduction_ShouldEggHatchAdapter",
    "VegaQolProduction_TryGenerateWildMonAdapter",
    "VegaQolProduction_GenerateFishingEncounterAdapter",
    "VegaQolProduction_DoStandardWildBattleAdapter",
    "VegaQolProduction_HandleInputChooseActionAdapter",
    "VegaQolProduction_HandleInputChooseMoveAdapter",
    "VegaQolProduction_ConfigureTrainerBattleAdapter",
    "VegaQolProduction_ConfigureHighRaid",
    "VegaQolProduction_ConfigureLowRaid",
}


class QolBuildError(ValueError):
    """QOL production入力・ABI・配置・検証契約違反。"""


def _fail(message: str) -> NoReturn:
    raise QolBuildError(message)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        _fail(f"JSON root differs: {path}")
    return value


def _index(rows: Sequence[Mapping[str, str]], key: str, label: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            _fail(f"{label}: missing/duplicate {key}: {value!r}")
        result[value] = row
    return result


def _run(command: Sequence[str], label: str, *, timeout: int | None = None) -> str:
    try:
        completed = subprocess.run(
            list(command), cwd=ROOT, text=True, capture_output=True,
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


def _input_contract() -> dict[str, Any]:
    stage = (ROOT / INPUT_ROM).read_bytes()
    base = (ROOT / BASE_ROM).read_bytes()
    clean = (ROOT / CLEAN_ROM).read_bytes()
    meta_raw = (ROOT / INPUT_META).read_bytes()
    alloc_raw = (ROOT / INPUT_ALLOC).read_bytes()
    if len(stage) != ROM_SIZE or _sha(stage) != EXPECTED_STAGE35_SHA256:
        _fail("Stage35 input size/hash differs")
    if _sha(meta_raw) != EXPECTED_STAGE35_META_SHA256:
        _fail("Stage35 metadata hash differs")
    if _sha(alloc_raw) != EXPECTED_STAGE35_ALLOC_SHA256:
        _fail("Stage35 allocation hash differs")
    if len(base) != ROM_SIZE or _sha(base) != EXPECTED_BASE_SHA256:
        _fail("v1.4.0 base size/hash differs")
    if len(clean) != 16 * 1024 * 1024 or _sha(clean) != EXPECTED_CLEAN_SHA256:
        _fail("clean FireRed JPN Rev.0 size/hash differs")
    meta = json.loads(meta_raw)
    alloc = json.loads(alloc_raw)
    coverage = meta.get("coverage", {})
    formats = coverage.get("battle_format_counts", {})
    invariants = meta.get("invariants", {})
    if (
        meta.get("output", {}).get("sha256") != EXPECTED_STAGE35_SHA256
        or coverage.get("encounter_count") != 1302
        or coverage.get("member_count") != 6490
        or formats != {"DOUBLE": 74, "SINGLE": 1228}
        or not all(invariants.values())
    ):
        _fail("Stage35 trainer regression metadata differs")
    if alloc.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage35 allocator overlap is nonzero")
    stage35 = [
        row for row in alloc.get("allocations", [])
        if row.get("name") == "trainer_changekit_final_stage35_payload"
    ]
    if len(stage35) != 1 or int(stage35[0]["start"]) != 0x01302B50:
        _fail("Stage35 allocation pin differs")
    return {
        "stage": stage, "base": base, "clean": clean,
        "meta": meta, "allocation": alloc,
    }


def _stage35_runtime_handoff(metadata: Mapping[str, Any]) -> dict[str, int]:
    entrypoints = metadata.get("runtime", {}).get("entrypoints", {})
    probe = entrypoints.get("TrainerV5Runtime_Probe")
    rows = metadata.get("physical_bindings", {}).get("rows", [])
    selected: dict[int, int] = {}
    for trainer_id in (130, 208):
        matches = [
            row for row in rows
            if int(row.get("target_trainer_id", -1)) == trainer_id
        ]
        if len(matches) != 1:
            _fail(
                f"Stage35 trainer {trainer_id} physical binding is not unique"
            )
        selected[trainer_id] = int(matches[0]["data_address"])
    values = {
        "trainer_probe": int(probe) if probe is not None else 0,
        "dynamax_command_data": selected[130],
        "tera_command_data": selected[208],
    }
    if any(not 0x08000000 <= address < 0x0A000000
           for address in values.values()):
        _fail("Stage35 runtime handoff address is outside GBA ROM")
    return values


def _validate_ram_and_state() -> dict[str, Any]:
    rows = _rows(ROOT / "config/ram_layout.csv")
    parsed: list[dict[str, Any]] = []
    for row in rows:
        start = int(row["start"], 0)
        end = int(row["end_exclusive"], 0)
        if end - start != int(row["size"], 0):
            _fail(f"RAM row size differs: {row['symbol']}")
        parsed.append({**row, "start_value": start, "end_value": end})
    owned = [row for row in parsed if row["owner"] == RAM_OWNER and row["status"] == "LIVE"]
    if owned:
        _fail("QOL must not reserve heap-backed EWRAM rows")
    expanded = [row for row in parsed if row["symbol"] == "gExpandedVars"
                and row["status"] == "LIVE"]
    if len(expanded) != 1 or (expanded[0]["start_value"], expanded[0]["end_value"]) != (
            0x0203B2E8, 0x0203B6E8):
        _fail("expanded vars RAM owner differs")
    flags = _index(_rows(ROOT / "manifests/flags.csv"), "flag_key", "flags")
    variables = _index(_rows(ROOT / "manifests/vars.csv"), "var_key", "vars")
    if int(flags["FLAG_KEY_QOL_EXP_SHARE_INITIALIZED"]["id"], 0) != 0x12FD:
        _fail("exp share initialization flag differs")
    if int(flags["FLAG_KEY_QOL_DAYCARE_QUEST"]["id"], 0) != 0x12FE:
        _fail("daycare quest flag differs")
    if int(flags["FLAG_KEY_QOL_EGG_BASKET"]["id"], 0) != 0x12FF:
        _fail("egg basket flag differs")
    if int(variables["VAR_KEY_QOL_EGG_BASKET_COUNTER"]["id"], 0) != 0x51FE:
        _fail("egg basket counter var differs")
    if int(variables["VAR_KEY_QOL_VOLATILE_STATE_BASE"]["id"], 0) != 0x5180:
        _fail("QOL volatile state base var differs")
    all_ids = [int(row["id"], 0) for row in flags.values()]
    if len(all_ids) != len(set(all_ids)):
        _fail("flag manifest ID collision")
    return {
        "owner": RAM_OWNER,
        "ranges": {"gVegaQolProductionState": [0x0203B5E8, 0x0203B6E4]},
        "live_overlap_count": 0,
        "flags": {"exp_share_initialized": 0x12FD,
                  "daycare_quest": 0x12FE, "egg_basket": 0x12FF},
        "vars": {"volatile_state_base": 0x5180,
                 "volatile_state_end": 0x51FD,
                 "egg_basket_counter": 0x51FE},
    }


def _load_model() -> dict[str, Any]:
    progression_rows = _rows(ROOT / PROGRESSION)
    binding_rows = _rows(ROOT / BINDINGS)
    if len(progression_rows) != FEATURE_COUNT or len(binding_rows) != FEATURE_COUNT:
        _fail("QOL progression/binding row count differs from 35")
    progression = _index(progression_rows, "feature_key", "qol progression")
    bindings = _index(binding_rows, "feature_key", "qol production bindings")
    if set(progression) != set(bindings):
        _fail("QOL progression/binding key set differs")
    if not all(row["release_enabled"].lower() == "true" for row in progression.values()):
        _fail("QOL progression contains non-release row")
    owners = [row["production_owner"] for row in binding_rows]
    if len(owners) != len(set(owners)) or any(not owner for owner in owners):
        _fail("QOL production owner is missing or duplicated")
    if any(row["classification"] not in CLASSIFICATIONS for row in binding_rows):
        _fail("non-live QOL production classification remains")
    matrix = _index(_rows(ROOT / FEATURE_MATRIX), "feature_key", "feature matrix")
    qol_b = _read_json(ROOT / QOL_B)
    qol_b_keys = {row["key"] for row in qol_b.get("features", [])}
    capabilities = set(matrix) | qol_b_keys
    for row in binding_rows:
        unknown = set(row["capability_keys"].split("|")) - capabilities
        if unknown:
            _fail(f"{row['feature_key']}: unknown capability crosswalk {sorted(unknown)}")
        if not row["entry_symbol"] or not row["ui_owner"] or not row["mgba_case"]:
            _fail(f"{row['feature_key']}: incomplete production binding")
    if matrix["PC_RELEARN"]["unlock_key"] != "VEGA_BADGE_2":
        _fail("PC relearn unlock contract differs")
    if progression["FREE_MOVE_RELEARN"]["unlock_key"] != "VEGA_BADGE_1":
        _fail("free move memory unlock contract differs")
    supply = _index(_rows(ROOT / SUPPLY), "supply_key", "QOL supply")
    expected_supply = {
        "SUPPLY_KEY_EVERSTONE": "VEGA_BADGE_1",
        "SUPPLY_KEY_EXP_CANDY_XS": "VEGA_DH_CLEAR",
        "SUPPLY_KEY_EXP_CANDY_S": "VEGA_DH_CLEAR",
        "SUPPLY_KEY_EXP_CANDY_M_ONCE": "VEGA_DH_CLEAR",
    }
    if any(supply[key]["unlock_key"] != value for key, value in expected_supply.items()):
        _fail("QOL supply unlock alignment differs")
    item_rows = _index(_rows(ROOT / ITEMS), "item_key", "item IDs")
    type_rows = [row for row in _rows(ROOT / TYPES)
                 if row["status"] != "RESERVED"]
    ability_rows = [row for row in _rows(ROOT / ABILITIES)
                    if int(row["id"]) != 0]
    move_rows = _rows(ROOT / MOVES)
    if (len(type_rows) != 20 or len(ability_rows) != 311
            or len(move_rows) != 1063
            or [int(row["id"]) for row in move_rows] != list(range(1063))):
        _fail("QOL search type/ability catalog differs")
    feature_index = {key: index for index, key in enumerate(progression)}
    supply_catalog: list[dict[str, Any]] = []
    seen_supply_items: set[int] = set()
    limited_repeatable_slots = 0
    repeatability_ids = {
        "REPEATABLE": 0,
        "LIMITED": 1,
        "LIMITED_REPEATABLE": 2,
    }
    for row in _rows(ROOT / SUPPLY_CATALOG):
        item = item_rows.get(row["item_key"])
        feature = row["unlock_feature"]
        if item is None or feature not in feature_index:
            _fail(f"QOL supply catalog row is unresolved: {row['supply_entry_key']}")
        item_id = int(item["id"])
        price = int(row["price_bp"])
        repeatability = row["repeatability"]
        if (item_id <= 0 or item_id >= 999 or price <= 0
            or repeatability not in repeatability_ids
            or item_id in seen_supply_items):
            _fail(f"QOL supply catalog row is invalid: {row['supply_entry_key']}")
        limit_slot = 0xFF
        if repeatability == "LIMITED_REPEATABLE":
            if limited_repeatable_slots >= 8:
                _fail("QOL limited-repeatable catalog exceeds session bitmap")
            limit_slot = limited_repeatable_slots
            limited_repeatable_slots += 1
        seen_supply_items.add(item_id)
        supply_catalog.append({
            "supply_entry_key": row["supply_entry_key"],
            "item_key": row["item_key"], "item_id": item_id,
            "display_name": item["display_name"], "price_bp": price,
            "feature": feature_index[feature], "unlock_feature": feature,
            "repeatability": repeatability,
            "repeatability_id": repeatability_ids[repeatability],
            "limit_slot": limit_slot,
        })
    if len(supply_catalog) != 49:
        _fail("QOL production supply catalog differs from 49 entries")

    maps = _index(_rows(ROOT / MAPS), "map_key", "maps")
    map_bindings = _index(_rows(ROOT / MAP_BINDINGS), "map_key", "map bindings")
    field_maps: list[dict[str, int]] = []
    for key, row in maps.items():
        if row["field_pc_allowed"].lower() != "true":
            continue
        binding = map_bindings.get(key)
        if binding is None or binding["status"] != "ACTIVE":
            _fail(f"field-PC map has no physical binding: {key}")
        field_maps.append({"group": int(binding["group_id"]), "map": int(binding["map_id"])})
    if len(field_maps) != 69 or len({(row['group'], row['map']) for row in field_maps}) != 69:
        _fail("field-PC physical whitelist differs from 69 unique maps")

    species = _index(_rows(ROOT / SPECIES), "species_key", "species IDs")
    official_dex = sorted({
        int(row["canonical_national_dex"], 0)
        for row in species.values()
        if row["is_official"].lower() == "true"
        and int(row["canonical_national_dex"], 0) > 0
    })
    if official_dex != list(range(1, 1026)):
        _fail("official canonical National Dex catalog differs from 1..1025")
    research_rows: list[dict[str, int | str]] = []
    for row in _rows(ROOT / RESEARCH):
        if row["status"] != "ACTIVE" or row["shared_capture_key"] != "NONE":
            continue
        binding = map_bindings.get(row["map_key"])
        identity = species.get(row["species_key"])
        if binding is None or identity is None:
            _fail(f"research row cannot bind: {row['research_key']}")
        if row["unlock_key"] not in UNLOCK_CODES:
            _fail(f"research unlock is unsupported: {row['unlock_key']}")
        if row["shiny_policy"] != "MINOR_BONUS_NO_CHAIN_LEAK":
            _fail(f"research shiny policy is unsupported: {row['research_key']}")
        research_rows.append({
            "research_key": row["research_key"],
            "group": int(binding["group_id"]), "map": int(binding["map_id"]),
            "species": int(identity["id"]),
            "level_min": int(row["level_min"]), "level_max": int(row["level_max"]),
            "iv_floor": int(row["iv_floor"]),
            "hidden_ability_rate": int(row["hidden_ability_rate"]),
            "held_item_rate": 5 if row["held_item_policy"] == "MODERN_LEGAL_LOW_RATE" else 0,
            # One ordinary shiny check is inherited from the original wild
            # generation.  RESEARCH receives exactly one additional PID
            # check; there is deliberately no persistent chain counter.
            "shiny_rolls": 2,
            "unlock": UNLOCK_CODES[row["unlock_key"]],
            "normal_preserved": 1 if row["normal_preserved"].lower() == "true" else 0,
        })
    research_rows.sort(key=lambda row: (int(row["group"]), int(row["map"]), str(row["research_key"])))
    if _sha((ROOT / RESEARCH).read_bytes()) != EXPECTED_RESEARCH_SHA256:
        _fail("research encounter manifest hash differs")
    if len(research_rows) != EXPECTED_RESEARCH_RULE_COUNT:
        _fail(f"research production rule count differs: {len(research_rows)}")
    protected = sorted({
        int(row["canonical_id"])
        for row in _rows(ROOT / SPECIAL)
    })
    if len(protected) != 125:
        _fail("special release-protection catalog differs from 125")
    raid_rows = [row for row in _rows(ROOT / RAIDS)
                 if row["status"] == "ACTIVE"]
    high_raid_rows = [row for row in raid_rows
                      if row["unlock_key"] == "RAID_HIGH_UNLOCKED"]
    low_raid_rows = [row for row in raid_rows
                     if row["raid_key"].startswith("RAID_KEY_LOW_")]
    if (len(high_raid_rows) != 250
        or {row["mechanic_policy"] for row in high_raid_rows} != {"RAID_DYNAMAX"}
        or len(low_raid_rows) != 6
        or {row["mechanic_policy"] for row in low_raid_rows} != {"RAID_DYNAMAX"}
        or {row["shield_policy"] for row in low_raid_rows} != {"SHIELD_NONE"}):
        _fail("high/low Raid manifest production boundary differs")
    gimmick_rows = [
        row for row in _rows(ROOT / TRAINER_RUNTIME_CONSUMERS)
        if row["gimmick_type"] in {"DYNAMAX", "TERASTAL"}
    ]
    gimmick_counts = Counter(row["gimmick_type"] for row in gimmick_rows)
    late_gimmick_trainers = sorted(
        int(row["runtime_trainer_id"]) for row in gimmick_rows
    )
    if (gimmick_counts != {"DYNAMAX": 4, "TERASTAL": 67}
        or len(late_gimmick_trainers) != 71
        or len(set(late_gimmick_trainers)) != 71):
        _fail("late trainer-gimmick production consumers differ from 4/67")
    return {
        "progression": progression_rows, "bindings": binding_rows,
        "capability_count": len(capabilities), "field_maps": field_maps,
        "research": research_rows, "protected": protected,
        "late_gimmick_trainers": late_gimmick_trainers,
        "raid_count": len(high_raid_rows),
        "low_raid_count": len(low_raid_rows),
        "official_dex": official_dex, "supply_catalog": supply_catalog,
        "search_types": [{"id": int(row["id"]), "name": row["display_name"]}
                         for row in type_rows],
        "search_abilities": [{"id": int(row["id"]), "name": row["display_name"]}
                             for row in ability_rows],
        "moves": [{"id": int(row["id"]), "name": row["display_name"]}
                  for row in move_rows],
        "source_hashes": {
            path.as_posix(): _sha((ROOT / path).read_bytes())
            for path in (PROGRESSION, BINDINGS, FEATURE_MATRIX, QOL_B, SUPPLY,
                         SUPPLY_CATALOG, ITEMS, TYPES, ABILITIES, MOVES, MAPS,
                         MAP_BINDINGS, RESEARCH,
                         SPECIES, SPECIAL, RAIDS, TRAINER_RUNTIME_CONSUMERS,
                         HOOK_CONTRACT)
        },
    }


def _c_bytes(raw: bytes, width: int | None = None) -> str:
    data = raw if width is None else raw + bytes(max(0, width - len(raw)))
    return "{" + ",".join(f"0x{value:02X}" for value in data) + "}"


def _generated_header(model: Mapping[str, Any]) -> bytes:
    mapping, tokens = _charmap(ROOT)
    encode = lambda text: _encode_text(text, mapping, tokens)  # noqa: E731
    panels = [
        ["ぶんしょう:しゅんじ", "ぶんしょう:はやい", "ぶんしょう:ふつう"],
        ["がくしゅうそうち:OFF", "がくしゅうそうち:ON"],
        ["ふか:ふつう", "ふか:はやい", "ふか:SKIP"],
        ["そうぐう:NORMAL", "そうぐう:RESEARCH"],
        ["FIELD PCをひらく"],
        ["タマゴQUEUEをうけとる"],
        ["おうかん:HP L/R:たいしょう", "おうかん:こうげき", "おうかん:ぼうぎょ",
         "おうかん:すばやさ", "おうかん:とくこう", "おうかん:とくぼう", "きんのおうかん:ぜんぶ"],
        ["EVをすべてRESET L/R:たいしょう"],
        ["タマゴBASKET:OFF", "タマゴBASKET:ON"],
        ["いちどかぎりの ほうしゅう"],
        ["いくせいSUPPLY うえしたでえらぶ"],
        ["QOL MENUをとじる"],
    ]
    panel_width = 64
    panel_rows: list[list[bytes]] = []
    for values in panels:
        encoded = [encode(value) for value in values]
        if any(len(raw) > panel_width for raw in encoded):
            _fail("QOL panel message exceeds fixed ABI")
        panel_rows.append([encoded[min(index, len(encoded) - 1)] for index in range(7)])
    digits = encode("0123456789")[:-1]
    lines = [
        "#ifndef VEGA_QOL_PRODUCTION_GENERATED_H",
        "#define VEGA_QOL_PRODUCTION_GENERATED_H",
        "#define VEGA_QOL_PANEL_COUNT 12u",
        "#define VEGA_QOL_PANEL_STATE_COUNT 7u",
        f"#define VEGA_QOL_FIELD_PC_MAP_COUNT {len(model['field_maps'])}u",
        f"#define VEGA_QOL_RESEARCH_RULE_COUNT {len(model['research'])}u",
        f"#define VEGA_QOL_PROTECTED_SPECIES_COUNT {len(model['protected'])}u",
        f"#define VEGA_QOL_OFFICIAL_DEX_COUNT {len(model['official_dex'])}u",
        # The Stage27 physical BP shop also sold Fire Stone.  Stage36 takes
        # ownership of that same NPC/menu and preserves the legacy row as the
        # final union entry instead of silently regressing an existing sale.
        f"#define VEGA_QOL_SUPPLY_CATALOG_COUNT {len(model['supply_catalog']) + 1}u",
        f"#define VEGA_QOL_LEGACY_FIRE_STONE_INDEX {len(model['supply_catalog'])}u",
        f"#define VEGA_QOL_SEARCH_TYPE_COUNT {len(model['search_types'])}u",
        f"#define VEGA_QOL_SEARCH_ABILITY_COUNT {len(model['search_abilities'])}u",
        f"#define VEGA_QOL_MOVE_COUNT {len(model['moves'])}u",
        f"#define VEGA_QOL_HIGH_RAID_COUNT {model['raid_count']}u",
        f"#define VEGA_QOL_LOW_RAID_COUNT {model['low_raid_count']}u",
        f"#define VEGA_QOL_LATE_GIMMICK_TRAINER_COUNT {len(model['late_gimmick_trainers'])}u",
        "#define VEGA_RESEARCH_UNLOCK_GAME_START 0u",
        "#define VEGA_RESEARCH_UNLOCK_BADGE_1 1u",
        "#define VEGA_RESEARCH_UNLOCK_BADGE_2 2u",
        "#define VEGA_RESEARCH_UNLOCK_BADGE_3 3u",
        "#define VEGA_RESEARCH_UNLOCK_BADGE_5 4u",
        "#define VEGA_RESEARCH_UNLOCK_BADGE_6 5u",
        "#define VEGA_RESEARCH_UNLOCK_BADGE_7 6u",
        "#define VEGA_RESEARCH_UNLOCK_BADGE_8 7u",
        "#define VEGA_RESEARCH_UNLOCK_HALL_OF_FAME 8u",
        "#define VEGA_RESEARCH_UNLOCK_KANTO 9u",
        "#define VEGA_RESEARCH_UNLOCK_CERT_1 10u",
        "#define VEGA_RESEARCH_UNLOCK_CERT_2 11u",
        "#define VEGA_RESEARCH_UNLOCK_CERT_3 12u",
        "#define VEGA_RESEARCH_UNLOCK_CERT_4 13u",
        "#define VEGA_RESEARCH_UNLOCK_CERT_5 14u",
        "#define VEGA_RESEARCH_UNLOCK_CERT_6 15u",
        "#define VEGA_RESEARCH_UNLOCK_KANTO_LEAGUE 16u",
        "typedef struct VegaQolFieldPcMap { uint8_t group; uint8_t number; } VegaQolFieldPcMap;",
        "typedef struct VegaQolResearchRule {",
        "  uint8_t group, map; uint16_t species;",
        "  uint8_t level_min, level_max, iv_floor, hidden_ability_rate, held_item_rate, shiny_rolls, unlock, normal_preserved;",
        "} VegaQolResearchRule;",
        "#define VEGA_QOL_SUPPLY_REPEATABLE 0u",
        "#define VEGA_QOL_SUPPLY_LIMITED 1u",
        "#define VEGA_QOL_SUPPLY_LIMITED_REPEATABLE 2u",
        "typedef struct VegaQolSupplyEntry { uint16_t item_id; uint16_t price_bp; uint8_t feature; uint8_t repeatability; uint8_t limit_slot; } VegaQolSupplyEntry;",
        "typedef struct VegaQolGeneratedListItem { const uint8_t *name; int32_t id; } VegaQolGeneratedListItem;",
        f"static const uint8_t gVegaQolDigits[10] = {_c_bytes(digits)};",
        f"static const uint8_t gVegaQolBpPrefix[] = {_c_bytes(encode('BP '))};",
        f"static const uint8_t gVegaQolSupplyNext[] = {_c_bytes(encode('つぎへ'))};",
        f"static const uint8_t gVegaQolSupplyCancel[] = {_c_bytes(encode('やめる'))};",
        f"static const uint8_t gVegaQolSelectedPrefix[] = {_c_bytes(encode('*'))};",
        f"static const uint8_t gVegaQolIvPrefix[] = {_c_bytes(encode('IV '))};",
        f"static const uint8_t gVegaQolEvPrefix[] = {_c_bytes(encode('EV '))};",
        f"static const uint8_t gVegaQolSpace[] = {_c_bytes(encode(' '))};",
        f"static const uint8_t gVegaQolSeparator[] = {_c_bytes(encode('/'))};",
        f"static const uint8_t gVegaQolTrainedText[] = {_c_bytes(encode('きたえた！'))};",
        f"static const uint8_t gVegaQolTrainedMarker[] = {_c_bytes(encode('*'))};",
        f"static const uint8_t gVegaQolMaxText[] = {_c_bytes(encode('MAX'))};",
        "static const uint8_t gVegaQolStatLabels[6][12] = {",
        *[f"  {_c_bytes(encode(value), 12)}," for value in
          ("HP", "こうげき", "ぼうぎょ", "とくこう", "とくぼう", "すばやさ")],
        "};",
        "static const uint8_t gVegaQolShortStatLabels[6][4] = {",
        *[f"  {_c_bytes(encode(value), 4)}," for value in
          ("H", "A", "B", "C", "D", "S")],
        "};",
        "static const uint8_t gVegaQolIvJudgeWords[6][16] = {",
        *[f"  {_c_bytes(encode(value), 16)}," for value in
          ("さいこう", "すばらしい", "すごくいい", "かなりいい", "まあまあ", "ダメかも")],
        "};",
        f"static const uint8_t gVegaQolTotalText[] = {_c_bytes(encode('ごうけい'))};",
        "static const uint8_t gVegaQolSearchMenuTexts[5][24] = {",
        *[f"  {_c_bytes(encode(value), 24)}," for value in
          ("なまえをにゅうりょく", "タイプ", "とくせい", "じょうけんをけす", "もどる")],
        "};",
        "static const VegaQolGeneratedListItem gVegaQolSearchMenuItems[5] = {",
        *[f"  {{gVegaQolSearchMenuTexts[{index}],{index}}}," for index in range(5)],
        "};",
        "static const uint8_t gVegaQolSearchTypeTexts[VEGA_QOL_SEARCH_TYPE_COUNT][12] = {",
        *[f"  {_c_bytes(encode(str(row['name'])), 12)}," for row in model["search_types"]],
        "};",
        "static const VegaQolGeneratedListItem gVegaQolSearchTypeItems[VEGA_QOL_SEARCH_TYPE_COUNT] = {",
        *[f"  {{gVegaQolSearchTypeTexts[{index}],{row['id']}}},"
          for index, row in enumerate(model["search_types"])],
        "};",
        "static const uint8_t gVegaQolSearchAbilityTexts[VEGA_QOL_SEARCH_ABILITY_COUNT][12] = {",
        *[f"  {_c_bytes(encode(str(row['name'])), 12)}," for row in model["search_abilities"]],
        "};",
        "static const VegaQolGeneratedListItem gVegaQolSearchAbilityItems[VEGA_QOL_SEARCH_ABILITY_COUNT] = {",
        *[f"  {{gVegaQolSearchAbilityTexts[{index}],{row['id']}}},"
          for index, row in enumerate(model["search_abilities"])],
        "};",
        "static const uint8_t gVegaQolMoveTexts[VEGA_QOL_MOVE_COUNT][16] = {",
        *[f"  {_c_bytes(encode(str(row['name'])), 16)}," for row in model["moves"]],
        "};",
        "static const uint8_t gVegaQolMoveSlotTexts[4][16] = {",
        *[f"  {_c_bytes(encode(value), 16)}," for value in
          ("わざ SLOT1", "わざ SLOT2", "わざ SLOT3", "わざ SLOT4")],
        "};",
        "static const VegaQolGeneratedListItem gVegaQolMoveSlotItems[4] = {",
        *[f"  {{gVegaQolMoveSlotTexts[{index}],{index}}}," for index in range(4)],
        "};",
        "static const uint8_t gVegaQolYesNoTexts[2][8] = {",
        f"  {_c_bytes(encode('はい'), 8)},",
        f"  {_c_bytes(encode('いいえ'), 8)},",
        "};",
        "static const VegaQolGeneratedListItem gVegaQolYesNoItems[2] = {",
        "  {gVegaQolYesNoTexts[0],1},",
        "  {gVegaQolYesNoTexts[1],0},",
        "};",
        f"static const uint8_t gVegaQolConfirmMessage[] = {_c_bytes(encode('もういちどAでけってい Bでキャンセル'))};",
        f"static const uint8_t gVegaQolMovePrefix[] = {_c_bytes(encode('わざ'))};",
        f"static const uint8_t gVegaQolSlotPrefix[] = {_c_bytes(encode(' SLOT'))};",
        "static const uint8_t gVegaQolQuantityTexts[4][12] = {",
        f"  {_c_bytes(encode('x1'), 12)},",
        f"  {_c_bytes(encode('x5'), 12)},",
        f"  {_c_bytes(encode('x10'), 12)},",
        f"  {_c_bytes(encode('すべて'), 12)},",
        "};",
        "static const VegaQolGeneratedListItem gVegaQolQuantityItems[4] = {",
        *[f"  {{gVegaQolQuantityTexts[{index}],{index}}}," for index in range(4)],
        "};",
        f"static const uint8_t gVegaQolCandyAppliedMessage[] = {_c_bytes(encode('けいけんちが あがった！ Aでつづける'))};",
        f"static const uint8_t gVegaQolQuantityAppliedMessage[] = {_c_bytes(encode('どうぐを つかった！ Aでつづける'))};",
        f"static const uint8_t gVegaQolCandyNoEffectMessage[] = {_c_bytes(encode('こうかが ないようだ'))};",
        f"const uint8_t gVegaQolDaycarePersistFailedText[] = {_c_bytes(encode('ほぞんに しっぱいしました'))};",
        "static const uint8_t gVegaQolStatusMessages[16][64] = {",
        *[f"  {_c_bytes(encode(value), 64)}," for value in (
          "かんりょうしました A/Bでもどる",
          "まだ つかえません A/Bでもどる",
          "キャンセルしました A/Bでもどる",
          "えらびかたが ただしくありません A/Bでもどる",
          "たいしょうが えらばれていません A/Bでもどる",
          "あきが ありません A/Bでもどる",
          "このポケモンは たいしょうにできません A/Bでもどる",
          "このどうぐは たいしょうにできません A/Bでもどる",
          "こうかが ありません A/Bでもどる",
          "おぼえられない わざです A/Bでもどる",
          "ここでは つかえません A/Bでもどる",
          "ほぞんに しっぱいしました A/Bでもどる",
          "セーブデータを よみこめません A/Bでもどる",
          "はい/いいえを えらんでください",
          "BPが たりません A/Bでもどる",
          "すでに うけとっています A/Bでもどる",
        )],
        "};",
        "static const uint8_t gVegaQolPssStatusMessages[16][36] = {",
        *[f"  {_c_bytes(encode(value), 36)}," for value in (
          "かんりょう", "まだつかえません", "キャンセル", "えらびかたエラー",
          "たいしょうなし", "あきがありません", "このポケモンはNG",
          "このどうぐはNG", "こうかなし", "わざPOOLそと",
          "ここではつかえません", "ほぞんしっぱい", "セーブエラー",
          "はい/いいえ", "BPがたりません", "うけとりずみ",
        )],
        "};",
        "static const uint8_t gVegaQolOneTimeRewardMessages[6][64] = {",
        f"  {_c_bytes(encode('うけとれる ほうしゅうは ありません'), 64)},",
        f"  {_c_bytes(encode('ほうしゅう:かわらずのいし'), 64)},",
        f"  {_c_bytes(encode('ほうしゅう:けいけんアメM'), 64)},",
        f"  {_c_bytes(encode('ほうしゅう:パワーけい6しゅ'), 64)},",
        f"  {_c_bytes(encode('ほうしゅう:けいけんアメXL'), 64)},",
        f"  {_c_bytes(encode('ほうしゅう:あかいいと・おまもり'), 64)},",
        "};",
        "static const VegaQolSupplyEntry gVegaQolSupplyCatalog[VEGA_QOL_SUPPLY_CATALOG_COUNT] = {",
        *[
            f"  {{{row['item_id']}u,{row['price_bp']}u,{row['feature']}u,{row['repeatability_id']}u,{row['limit_slot']}u}},"
            for row in model["supply_catalog"]
        ],
        "  {95u,3u,0xFFu,VEGA_QOL_SUPPLY_REPEATABLE,0xFFu},",
        "};",
        "static const uint8_t gVegaQolSupplyMessages[VEGA_QOL_SUPPLY_CATALOG_COUNT][64] = {",
        *[
            f"  {_c_bytes(encode(str(row['display_name']) + ' ' + str(row['price_bp']) + 'BP'), 64)},"
            for row in model["supply_catalog"]
        ],
        f"  {_c_bytes(encode('ほのおのいし 3BP'), 64)},",
        "};",
        "static const VegaQolFieldPcMap gVegaQolFieldPcMaps[VEGA_QOL_FIELD_PC_MAP_COUNT] = {",
    ]
    lines.extend(f"  {{{row['group']}u,{row['map']}u}}," for row in model["field_maps"])
    lines.extend([
        "};",
        "static const VegaQolResearchRule gVegaQolResearchRules[VEGA_QOL_RESEARCH_RULE_COUNT] = {",
    ])
    for row in model["research"]:
        lines.append(
            "  {%du,%du,%du,%du,%du,%du,%du,%du,%du,%du,%du}," % (
                row["group"], row["map"], row["species"], row["level_min"],
                row["level_max"], row["iv_floor"], row["hidden_ability_rate"],
                row["held_item_rate"], row["shiny_rolls"], row["unlock"],
                row["normal_preserved"],
            )
        )
    lines.extend([
        "};",
        "static const uint16_t gVegaQolProtectedSpecies[VEGA_QOL_PROTECTED_SPECIES_COUNT] = {",
        "  " + ",".join(f"{value}u" for value in model["protected"]),
        "};",
        "static const uint16_t gVegaQolOfficialNationalDex[VEGA_QOL_OFFICIAL_DEX_COUNT] = {",
        "  " + ",".join(f"{value}u" for value in model["official_dex"]),
        "};",
        "static const uint16_t gVegaQolLateGimmickTrainers[VEGA_QOL_LATE_GIMMICK_TRAINER_COUNT] = {",
        "  " + ",".join(f"{value}u" for value in model["late_gimmick_trainers"]),
        "};",
        "static const uint8_t gVegaQolPanelMessages[VEGA_QOL_PANEL_COUNT][VEGA_QOL_PANEL_STATE_COUNT][64] = {",
    ])
    for panel in panel_rows:
        lines.append("  {")
        lines.extend(f"    {_c_bytes(raw, panel_width)}," for raw in panel)
        lines.append("  },")
    lines.extend(["};", "#endif", ""])
    return "\n".join(lines).encode("ascii")


def _compile_runtime(load_address: int, header: bytes) -> tuple[bytes, dict[str, int]]:
    compiler = _arm_tool(ROOT, "arm-none-eabi-gcc")
    objcopy = _arm_tool(ROOT, "arm-none-eabi-objcopy")
    nm = _arm_tool(ROOT, "arm-none-eabi-nm")
    with tempfile.TemporaryDirectory(prefix="vega-qol-production-") as temporary:
        directory = Path(temporary)
        (directory / "qol_production_generated.h").write_bytes(header)
        common = [
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork", "-Os",
            "-Wall", "-Wextra", "-Werror", "-ffreestanding", "-fno-builtin",
            "-fno-unwind-tables", "-fno-asynchronous-unwind-tables",
            "-fdata-sections", "-ffunction-sections", "-fno-common",
            f"-I{directory}", f"-I{ROOT}",
        ]
        c_obj = directory / "qol.o"
        s_obj = directory / "hooks.o"
        _run([
            *common, "-std=c11", "-c",
            str(ROOT / "overlays/qol_production/qol_production.c"),
            "-o", str(c_obj),
        ], "compile QOL production C")
        _run([
            *common, "-c",
            str(ROOT / "overlays/qol_production/qol_production_hooks.S"),
            "-o", str(s_obj),
        ], "compile QOL production hooks")
        linker = directory / "linker.ld"
        linker.write_text(
            "SECTIONS\n{\n"
            f"  . = 0x{load_address:08X};\n"
            "  .text : { KEEP(*(.text.VegaQolProduction_*)) KEEP(*(.text.VegaQolProductionHooks)) *(.text*) *(.rodata*) *(.data*) }\n"
            "  .bss (NOLOAD) : { *(.bss*) *(COMMON) }\n"
            "  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }\n"
            "}\n", encoding="ascii",
        )
        elf = directory / "qol.elf"
        binary = directory / "qol.bin"
        _run([
            compiler, "-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork",
            "-nostdlib", "-Wl,--build-id=none", "-Wl,--gc-sections",
            "-Wl,-e,VegaQolProduction_Probe", f"-Wl,-T,{linker}",
            str(c_obj), str(s_obj), "-lgcc", "-o", str(elf),
        ], "link QOL production runtime")
        undefined = _run([nm, "-u", str(elf)], "QOL undefined symbol audit")
        if undefined:
            _fail("QOL runtime has undefined symbols: " + undefined)
        _run([objcopy, "-O", "binary", str(elf), str(binary)], "QOL objcopy")
        symbols: dict[str, int] = {}
        mutable: list[str] = []
        for line in _run([nm, "-n", "--defined-only", str(elf)], "QOL nm").splitlines():
            fields = line.split()
            if len(fields) != 3:
                continue
            try:
                symbols[fields[2]] = int(fields[0], 16)
            except ValueError:
                continue
            if fields[1] in {"B", "b", "C", "c"}:
                mutable.append(fields[2])
        if mutable:
            _fail("QOL runtime linked mutable ROM state: " + ", ".join(mutable))
        missing = sorted(REQUIRED_ENTRYPOINTS - set(symbols))
        if missing:
            _fail(f"QOL entrypoints are missing: {missing}")
        raw = binary.read_bytes()
        if not raw or len(raw) > 512 * 1024:
            _fail(f"QOL runtime size is unreasonable: {len(raw)}")
        return raw, symbols


def _allocation(previous: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    requests = _previous_requests(previous)
    requests.append({
        "name": ALLOCATION_NAME, "region": "integration_modules",
        "size": size, "alignment": 16, "owner": TASK,
        "purpose": "QOL 35 production UI/PC/daycare/battle/save runtime and authored research table",
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(ROOT / "config/rom_regions.csv", requests)
    if report.get("summaries", {}).get("overlap_count") != 0:
        _fail("Stage36 allocator overlap detected")
    matches = [row for row in report["allocations"] if row["name"] == ALLOCATION_NAME]
    if len(matches) != 1:
        _fail("Stage36 allocation is not unique")
    return matches[0], report


def _patch(
    output: bytearray, stage: bytes, declared: list[dict[str, Any]],
    address: int, expected: bytes, replacement: bytes, name: str,
) -> dict[str, Any]:
    if len(expected) != len(replacement):
        _fail(f"{name}: expected/replacement length differs")
    offset = address - GBA_ROM_BASE
    if offset < 0 or offset + len(expected) > len(stage):
        _fail(f"{name}: hook is outside ROM")
    actual = stage[offset:offset + len(expected)]
    if actual != expected:
        _fail(f"{name}: expected bytes differ: {actual.hex()} != {expected.hex()}")
    output[offset:offset + len(replacement)] = replacement
    declared.append({"start": offset, "end_exclusive": offset + len(replacement), "kind": name})
    return {
        "name": name, "address": address, "size": len(expected),
        "expected_hex": expected.hex(), "replacement_hex": replacement.hex(),
    }


def _unaligned_jump_stub(address: int, target: int) -> bytes:
    """Emit a Thumb-1 literal jump for a hook at address % 4 == 2.

    The normal 8-byte ``ldr/bx/literal`` form would load the ``bx`` opcode as
    the low half of its literal because Thumb aligns PC down to four bytes.
    A NOP places the literal at the next aligned word instead.
    """
    if address & 3 != 2:
        _fail(f"unaligned jump hook has unexpected alignment: 0x{address:08X}")
    return b"\x01\x4B\x18\x47\xC0\x46" + struct.pack("<I", target | 1)


def _report(metadata: Mapping[str, Any]) -> bytes:
    text = f"""# QOL production統合 / Stage 36

## 結論

- release対象35/35行を一意のproduction ownerへ結合し、非live分類を0件にした。
- Stage35の実80-byte BoxPokemon、14箱、通常field/PC/summary/bag/battle/daycare/save導線へ接続した。
- NORMAL野生profileはStage35 overlayへbyte/RNG同値委譲し、RESEARCHだけmanifest由来{metadata['content']['research_rule_count']}行を消費する。
- タマゴbasketは独立256歩clock、通常相性・Oval Charm補正・1回の生成RNG、共有5件FIFOを使う。
- Stage35の1,302戦・6,490体・SINGLE 1,228 / DOUBLE 74を保持した。

## 物理証跡

- ROM SHA-256: `{metadata['output']['sha256']}`
- hook/repoint: {metadata['hooks']['count']}件（全件expected-byte一致）
- allocator overlap: {metadata['allocation']['overlap_count']}
- declared span外変更: {metadata['change_audit']['outside_declared_span_count']}
- QOL RAM overlap: {metadata['runtime_ram']['live_overlap_count']}
- incremental/cumulative BPS: exact round-trip

## 操作

- Start menu表示中にSELECT: QOL panel。左右で機能、Aで実行、Bで終了。
- PCでSELECT: marker。SELECT+L/R/START/A/UP/DOWNで検索・移動・逃がし・回収・技・解除。
- 通常random野生戦でSELECT: auto。各turn Bで解除。
- Hyper/EV panelではL/Rでparty対象を切替。Hyperは上下で能力を選ぶ。

`!`付きIVは実IV31ではなく「きたえた！」状態を示す。
"""
    return text.encode("utf-8")


def _mgba_cases(model: Mapping[str, Any]) -> bytes:
    rows = [
        {
            "case_id": row["feature_key"],
            "path": row["mgba_case"],
            "mode": "quick",
        }
        for row in model["bindings"]
    ]
    if len(rows) != FEATURE_COUNT or len({row["case_id"] for row in rows}) != FEATURE_COUNT:
        _fail("QOL mGBA feature case rows are not exact 35 unique bindings")
    return _csv_bytes(rows, ("case_id", "path", "mode"))


def build_outputs() -> dict[str, bytes]:
    inputs = _input_contract()
    cfru_symbols, cfru_metadata_sha256 = _cfru_symbol_handoff()
    stage35_handoff = _stage35_runtime_handoff(inputs["meta"])
    ram = _validate_ram_and_state()
    model = _load_model()
    header = _generated_header(model)
    provisional_code, _ = _compile_runtime(GBA_ROM_BASE + PAYLOAD_HEADER_SIZE, header)
    provisional_size = _align(PAYLOAD_HEADER_SIZE + len(provisional_code), 16)
    allocation, _ = _allocation(inputs["allocation"], provisional_size, "0" * 64)
    payload_offset = int(allocation["start"])
    code_address = GBA_ROM_BASE + payload_offset + PAYLOAD_HEADER_SIZE
    code, symbols = _compile_runtime(code_address, header)
    if len(code) != len(provisional_code):
        _fail("provisional/final QOL link size differs")
    payload = bytearray(provisional_size)
    payload[PAYLOAD_HEADER_SIZE:PAYLOAD_HEADER_SIZE + len(code)] = code
    entrypoints = {
        name: address | 1 for name, address in symbols.items()
        if name.startswith("VegaQolProduction_")
    }
    struct.pack_into(
        "<8s12I", payload, 0, b"VEGAQP36", 1, len(payload), len(code),
        FEATURE_COUNT, len(model["field_maps"]), len(model["research"]),
        len(model["protected"]), entrypoints["VegaQolProduction_Probe"],
        entrypoints["VegaQolProduction_Dispatch"],
        entrypoints["VegaQolProduction_StartMenuPanel"],
        0x0203B5E8, 0x0203B6E8,
    )
    allocation, allocation_report = _allocation(inputs["allocation"], len(payload), _sha(payload))
    if int(allocation["start"]) != payload_offset:
        _fail("final QOL allocation placement changed")
    payload_end = int(allocation["end_exclusive"])
    stage = inputs["stage"]
    if stage[payload_offset:payload_end] != b"\xFF" * len(payload):
        _fail("Stage36 QOL payload destination is not erased FF")
    output = bytearray(stage)
    output[payload_offset:payload_end] = payload
    declared: list[dict[str, Any]] = [{
        "start": payload_offset, "end_exclusive": payload_end,
        "kind": "qol_production_stage36_payload",
    }]
    contract = _read_json(ROOT / HOOK_CONTRACT)
    if contract.get("input_sha256") != EXPECTED_STAGE35_SHA256:
        _fail("QOL hook contract input hash differs")
    hook_rows: list[dict[str, Any]] = []
    for row in contract.get("hooks", []):
        address = int(row["address"], 0)
        expected = bytes.fromhex(row["expected"])
        mode = row["mode"]
        target_value: int | None = None
        if mode == "cfru_symbol_jump":
            target = row["target"]
            if target not in cfru_symbols:
                _fail(f"CFRU hook target symbol is missing: {target}")
            target_value = cfru_symbols[target] | 1
        elif mode.startswith("symbol"):
            target = row["target"]
            if target not in entrypoints:
                _fail(f"hook target symbol is missing: {target}")
            target_value = entrypoints[target]
        elif mode == "absolute_jump":
            target_value = int(row["target"], 0)
            if 0x09000000 <= target_value < 0x09200000:
                _fail(
                    f"relocatable CFRU target must use cfru_symbol_jump: {row['name']}"
                )
        if mode in {"symbol_jump", "cfru_symbol_jump", "absolute_jump"}:
            replacement = _jump_stub(target_value)
        elif mode == "symbol_jump_unaligned":
            replacement = _unaligned_jump_stub(address, target_value)
        elif mode == "symbol_jump_nop":
            replacement = _jump_stub(target_value) + b"\xC0\x46" * ((len(expected) - 8) // 2)
        elif mode == "symbol_bl":
            replacement = _thumb_bl(address, target_value)
        elif mode == "symbol_pointer":
            replacement = int(target_value | 1).to_bytes(4, "little")
        elif mode == "symbol_script_goto":
            replacement = b"\x05" + int(target_value).to_bytes(4, "little")
        elif mode == "raw":
            replacement = bytes.fromhex(row["replacement"])
        else:
            _fail(f"unknown QOL hook mode: {mode}")
        audit = _patch(output, stage, declared, address, expected, replacement, row["name"])
        if target_value is not None:
            audit["target"] = target_value
        hook_rows.append(audit)
    changed = [index for index, pair in enumerate(zip(stage, output)) if pair[0] != pair[1]]
    outside = [
        index for index in changed
        if not any(row["start"] <= index < row["end_exclusive"] for row in declared)
    ]
    if outside:
        _fail(f"Stage36 changes outside declared spans: {outside[:16]}")
    output_raw = bytes(output)
    incremental = _sparse_bps(stage, output_raw)
    cumulative = _sparse_bps(inputs["base"], output_raw)
    if apply_bps(stage, incremental) != output_raw:
        _fail("Stage35->36 BPS round trip differs")
    if apply_bps(inputs["base"], cumulative) != output_raw:
        _fail("v1.4.0->36 BPS round trip differs")
    classifications = Counter(row["classification"] for row in model["bindings"])
    audit = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "release_feature_count": FEATURE_COUNT,
        "unique_owner_count": len({row["production_owner"] for row in model["bindings"]}),
        "classification_counts": dict(classifications),
        "non_live_count": 0,
        "bindings": model["bindings"],
        "qol_b_real_abi": {
            "box_count": 14, "box_capacity": 30, "box_mon_size": 80,
            "party_mon_size": 100, "storage_pointer_slot": "0x03005050",
            "shadow_model_used": False,
        },
        "source_hashes": model["source_hashes"],
    }
    metadata: dict[str, Any] = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "input": {"path": INPUT_ROM.as_posix(), "sha256": _sha(stage), "size": len(stage)},
        "clean_input": {"path": CLEAN_ROM.as_posix(), "sha256": _sha(inputs["clean"]), "size": len(inputs["clean"])},
        "base_release": {"path": BASE_ROM.as_posix(), "sha256": _sha(inputs["base"]), "size": len(inputs["base"])},
        "output": {"path": OUTPUT_ROM.as_posix(), "sha256": _sha(output_raw), "size": len(output_raw)},
        "content": {
            "feature_count": FEATURE_COUNT, "field_pc_map_count": len(model["field_maps"]),
            "research_rule_count": len(model["research"]),
            "protected_special_species_count": len(model["protected"]),
        },
        "runtime": {
            "payload": {"offset": payload_offset, "address": GBA_ROM_BASE + payload_offset,
                        "size": len(payload), "sha256": _sha(payload),
                        "code_address": code_address, "code_size": len(code), "code_sha256": _sha(code)},
            "entrypoints": entrypoints,
            "cfru_symbol_handoff": {
                "metadata_path": BATTLE_CORE_META.as_posix(),
                "metadata_sha256": cfru_metadata_sha256,
                "symbols": cfru_symbols,
            },
            "stage35_runtime_handoff": stage35_handoff,
        },
        "runtime_ram": ram,
        "hooks": {"count": len(hook_rows), "rows": hook_rows},
        "allocation": {"path": OUTPUT_ALLOC.as_posix(), "name": ALLOCATION_NAME,
                       "overlap_count": allocation_report["summaries"]["overlap_count"],
                       "remaining_allocatable_bytes": allocation_report["summaries"]["remaining_allocatable_bytes"]},
        "trainer_regression": {
            "encounters": 1302, "members": 6490, "single": 1228, "double": 74,
            "kanto_trainers": 201,
            "stage35_metadata_sha256": EXPECTED_STAGE35_META_SHA256,
        },
        "release_patches": {
            "incremental": {"path": PATCH_INCREMENTAL.as_posix(), "sha256": _sha(incremental), "exact": True},
            "cumulative": {"path": PATCH_CUMULATIVE.as_posix(), "sha256": _sha(cumulative), "exact": True},
        },
        "change_audit": {"changed_byte_count": len(changed), "declared_spans": declared,
                         "outside_declared_span_count": len(outside)},
        "invariants": {
            "stage35_hash_pinned": True, "stage35_metadata_pinned": True,
            "stage35_allocation_pinned": True, "features_35_unique_live": True,
            "qol_b_real_box_abi": True, "research_normal_delegate": True,
            "trainer_1302_member_6490_single1228_double74": True,
            "allocator_overlap_zero": True, "ram_overlap_zero": True,
            "declared_changes_only": True, "incremental_bps_exact": True,
            "cumulative_bps_exact": True,
        },
    }
    serialized = {
        "schema_version": 1, "task": TASK, "status": "PASS",
        "bindings": model["bindings"], "field_pc_maps": model["field_maps"],
        "research_rules": model["research"], "protected_species": model["protected"],
        "source_hashes": model["source_hashes"],
    }
    symbols_doc = {
        "schema_version": 1, "task": TASK,
        "payload": metadata["runtime"]["payload"],
        "entrypoints": entrypoints,
        "symbols": {name: value for name, value in symbols.items()
                    if code_address <= value < code_address + len(code)},
        "hooks": hook_rows,
    }
    return {
        OUTPUT_ROM.as_posix(): output_raw,
        OUTPUT_META.as_posix(): _stable(metadata),
        OUTPUT_ALLOC.as_posix(): _stable(allocation_report),
        OUTPUT_SERIALIZED.as_posix(): _stable(serialized),
        OUTPUT_HEADER.as_posix(): header,
        OUTPUT_RUNTIME.as_posix(): bytes(payload),
        OUTPUT_SYMBOLS.as_posix(): _stable(symbols_doc),
        OUTPUT_CASES.as_posix(): _mgba_cases(model),
        OUTPUT_AUDIT.as_posix(): _stable(audit),
        OUTPUT_REPORT.as_posix(): _report(metadata),
        PATCH_INCREMENTAL.as_posix(): incremental,
        PATCH_CUMULATIVE.as_posix(): cumulative,
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
        _fail("QOL production generated outputs differ: " + ", ".join(differences))


def _exact_true_map(
    document: Mapping[str, Any], field: str, expected: set[str], label: str,
) -> dict[str, bool]:
    value = document.get(field)
    if not isinstance(value, dict) or set(value) != expected:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        _fail(f"{label} {field} keys differ: {actual}")
    if any(result is not True for result in value.values()):
        failed = sorted(key for key, result in value.items() if result is not True)
        _fail(f"{label} {field} is not exact all-true: {failed}")
    return {str(key): True for key in value}


def _binding_evidence(
    outputs: Mapping[str, bytes],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    serialized = json.loads(outputs[OUTPUT_SERIALIZED.as_posix()])
    bindings = serialized.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != FEATURE_COUNT:
        _fail("serialized QOL bindings are not exact 35 rows")
    if not all(isinstance(row, dict) for row in bindings):
        _fail("serialized QOL binding row is not an object")
    feature_keys = [str(row.get("feature_key", "")) for row in bindings]
    if "" in feature_keys or len(set(feature_keys)) != FEATURE_COUNT:
        _fail("serialized QOL feature keys are missing or duplicated")

    try:
        cases = list(csv.DictReader(io.StringIO(
            outputs[OUTPUT_CASES.as_posix()].decode("utf-8")
        )))
    except UnicodeDecodeError as exc:
        _fail(f"QOL mGBA case fixture is not UTF-8: {exc}")
    if len(cases) != FEATURE_COUNT:
        _fail(f"QOL mGBA case fixture count differs: {len(cases)}")
    expected_cases = [
        {
            "case_id": str(row["feature_key"]),
            "path": str(row["mgba_case"]),
            "mode": "quick",
        }
        for row in bindings
    ]
    if cases != expected_cases:
        _fail("QOL mGBA cases do not exactly match the 35-row binding ledger")
    return bindings, cases


def _stage35_trainer_evidence(outputs: Mapping[str, bytes]) -> dict[str, Any]:
    stage35 = (ROOT / INPUT_ROM).read_bytes()
    stage36 = outputs[OUTPUT_ROM.as_posix()]
    metadata35 = _read_json(ROOT / INPUT_META)
    allocation35 = _read_json(ROOT / INPUT_ALLOC)
    coverage35 = metadata35.get("coverage", {})
    if (
        _sha(stage35) != EXPECTED_STAGE35_SHA256
        or coverage35.get("encounter_count") != 1302
        or coverage35.get("member_count") != 6490
        or coverage35.get("battle_format_counts") != {"DOUBLE": 74, "SINGLE": 1228}
        or coverage35.get("gimmick_type_counts") != {
            "DYNAMAX": 4, "MEGA": 86, "NONE": 1034,
            "TERASTAL": 67, "Z_MOVE": 111,
        }
    ):
        _fail("Stage35 trainer metadata gate differs")

    allocation_rows = [
        row for row in allocation35.get("allocations", [])
        if row.get("name") == "trainer_changekit_final_stage35_payload"
    ]
    if len(allocation_rows) != 1:
        _fail("Stage35 trainer payload allocation is not unique")
    payload_start = int(allocation_rows[0]["start"])
    payload_end = int(allocation_rows[0]["end_exclusive"])
    if stage36[payload_start:payload_end] != stage35[payload_start:payload_end]:
        _fail("Stage36 changed the Stage35 trainer payload")

    table = metadata35.get("trainer_table", {})
    table_start = int(table["new_address"]) - GBA_ROM_BASE
    table_end = table_start + int(table["new_count"]) * int(table["record_size"])
    if stage36[table_start:table_end] != stage35[table_start:table_end]:
        _fail("Stage36 changed the Stage35 trainer table")

    physical = metadata35.get("physical_bindings", {})
    physical_rows = physical.get("rows", [])
    if (
        physical.get("count") != 1302
        or physical.get("unique_command_count") != 1302
        or not isinstance(physical_rows, list)
        or len(physical_rows) != 1302
    ):
        _fail("Stage35 physical trainer binding count differs")
    for row in physical_rows:
        offset = int(row["command_address"]) - GBA_ROM_BASE
        if stage36[offset:offset + 8] != stage35[offset:offset + 8]:
            _fail(f"Stage36 changed trainer command: {row['encounter_key']}")

    hooks = metadata35.get("hooks", {})
    protected_hooks: list[Mapping[str, Any]] = []
    for name in ("trainer_v5", "policy_bl"):
        rows = hooks.get(name, [])
        if not isinstance(rows, list):
            _fail(f"Stage35 {name} hook metadata is not a list")
        protected_hooks.extend(rows)
    ability = hooks.get("ability_load")
    if not isinstance(ability, dict):
        _fail("Stage35 ability hook metadata is unavailable")
    protected_hooks.append(ability)
    stage36_hooks = json.loads(
        outputs[OUTPUT_META.as_posix()]
    ).get("hooks", {}).get("rows", [])
    chained = {
        row.get("name"): row for row in stage36_hooks
        if isinstance(row, dict)
    }
    chained_count = 0
    for row in protected_hooks:
        offset = int(row["offset"])
        size = int(row["size"])
        if stage36[offset:offset + size] != stage35[offset:offset + size]:
            if row.get("name") != "configure_trainer_battle":
                _fail(f"Stage36 changed Stage35 trainer hook: {row.get('name', '?')}")
            adapter = chained.get("trainer_battle_configure")
            if (not isinstance(adapter, dict)
                or int(adapter.get("address", 0)) != int(row["address"])
                or int(adapter.get("size", 0)) != size
                or stage36[offset:offset + size]
                   != bytes.fromhex(str(adapter.get("replacement_hex", "")))):
                _fail("Stage36 trainer configure hook is not an audited chain")
            chained_count += 1

    physical_events = metadata35.get("physical_events", {}).get("summary", {})
    if physical_events.get("task06_encounters") != 201:
        _fail("Stage35 Kanto physical trainer count differs")
    return {
        "stage35_rom_sha256": _sha(stage35),
        "payload_sha256": _sha(stage35[payload_start:payload_end]),
        "trainer_table_sha256": _sha(stage35[table_start:table_end]),
        "trainer_commands_compared": len(physical_rows),
        "trainer_hooks_compared": len(protected_hooks),
        "trainer_hooks_chained": chained_count,
        "encounters": 1302,
        "members": 6490,
        "single": 1228,
        "double": 74,
        "kanto_trainers": 201,
    }


def _static_acceptance_evidence(
    outputs: Mapping[str, bytes], bindings: Sequence[Mapping[str, Any]],
    cases: Sequence[Mapping[str, str]],
) -> dict[str, dict[str, Any]]:
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    allocation = json.loads(outputs[OUTPUT_ALLOC.as_posix()])
    audit = json.loads(outputs[OUTPUT_AUDIT.as_posix()])
    serialized = json.loads(outputs[OUTPUT_SERIALIZED.as_posix()])
    stage35 = (ROOT / INPUT_ROM).read_bytes()
    base = (ROOT / BASE_ROM).read_bytes()
    stage36 = outputs[OUTPUT_ROM.as_posix()]
    incremental = outputs[PATCH_INCREMENTAL.as_posix()]
    cumulative = outputs[PATCH_CUMULATIVE.as_posix()]

    owners = [str(row.get("production_owner", "")) for row in bindings]
    classifications = [str(row.get("classification", "")) for row in bindings]
    unique_checks = {
        "binding_count_35": len(bindings) == FEATURE_COUNT,
        "owners_unique_35": len(set(owners)) == FEATURE_COUNT and "" not in owners,
        "classifications_live": all(value in CLASSIFICATIONS for value in classifications),
        "audit_non_live_zero": audit.get("non_live_count") == 0,
        "audit_unique_owner_35": audit.get("unique_owner_count") == FEATURE_COUNT,
    }

    trainer = metadata.get("trainer_regression", {})
    trainer_details = _stage35_trainer_evidence(outputs)
    trainer_checks = {
        "stage35_input_pinned": metadata.get("input", {}).get("sha256")
        == EXPECTED_STAGE35_SHA256,
        "trainer_counts_exact": trainer == {
            "encounters": 1302, "members": 6490, "single": 1228,
            "double": 74, "kanto_trainers": 201,
            "stage35_metadata_sha256": EXPECTED_STAGE35_META_SHA256,
        },
        "trainer_payload_preserved": True,
        "trainer_table_preserved": True,
        "trainer_commands_preserved": True,
        "trainer_hooks_preserved": True,
    }

    change = metadata.get("change_audit", {})
    patches = metadata.get("release_patches", {})
    deterministic_checks = {
        "declared_span_outside_zero": change.get("outside_declared_span_count") == 0,
        "allocator_overlap_zero": allocation.get("summaries", {}).get("overlap_count") == 0,
        "ram_overlap_zero": metadata.get("runtime_ram", {}).get("live_overlap_count") == 0,
        "incremental_metadata_exact": patches.get("incremental", {}).get("exact") is True
        and patches.get("incremental", {}).get("sha256") == _sha(incremental),
        "cumulative_metadata_exact": patches.get("cumulative", {}).get("exact") is True
        and patches.get("cumulative", {}).get("sha256") == _sha(cumulative),
        "incremental_round_trip": apply_bps(stage35, incremental) == stage36,
        "cumulative_round_trip": apply_bps(base, cumulative) == stage36,
    }

    binding_list = list(bindings)
    document_checks = {
        "audit_matches_serialized": audit.get("bindings") == serialized.get("bindings"),
        "serialized_matches_runtime_model": serialized.get("bindings") == binding_list,
        "case_count_35": len(cases) == FEATURE_COUNT,
        "case_ids_match_ledger": [row["case_id"] for row in cases]
        == [str(row["feature_key"]) for row in bindings],
        "case_paths_match_ledger": [row["path"] for row in cases]
        == [str(row["mgba_case"]) for row in bindings],
        "metadata_feature_count_35": metadata.get("content", {}).get("feature_count")
        == FEATURE_COUNT,
        "source_hashes_match": audit.get("source_hashes")
        == serialized.get("source_hashes"),
    }

    evidence = {
        "35_UNIQUE_LIVE_OWNERS": {
            "source": "binding_ledger+audit",
            "checks": unique_checks,
        },
        "STAGE35_TRAINER_REGRESSION": {
            "source": "pinned_stage35_metadata+byte_comparison",
            "checks": trainer_checks,
            "details": trainer_details,
        },
        "DETERMINISTIC_BPS_DECLARED_ONLY": {
            "source": "stage36_metadata+allocator+BPS_round_trip",
            "checks": deterministic_checks,
        },
        "DOC_LEDGER_BUILD_ALIGNMENT": {
            "source": "audit+serialized+35_case_fixture+metadata",
            "checks": document_checks,
        },
    }
    for key, row in evidence.items():
        failed = sorted(name for name, passed in row["checks"].items() if passed is not True)
        if failed:
            _fail(f"static acceptance {key} failed: {failed}")
        row["status"] = "PASS"
    return evidence


def _coverage_document(
    outputs: Mapping[str, bytes], bindings: Sequence[Mapping[str, Any]],
    cases: Sequence[Mapping[str, str]], documents: Mapping[str, Mapping[str, Any]],
) -> bytes:
    quick = documents["quick"]
    full = documents["full"]
    static = _static_acceptance_evidence(outputs, bindings, cases)
    acceptance_evidence: dict[str, dict[str, Any]] = dict(static)
    for key in DYNAMIC_ACCEPTANCE_KEYS:
        checks = {
            "quick": quick["acceptance_checks"][key],
            "full": full["acceptance_checks"][key],
        }
        if any(value is not True for value in checks.values()):
            _fail(f"dynamic acceptance {key} is not quick/full PASS")
        acceptance_evidence[key] = {
            "status": "PASS",
            "source": "mGBA_quick+full_acceptance_checks",
            "checks": checks,
        }

    mgba_checks = {
        "quick_process_runs_1": quick.get("process_runs") == 1,
        "full_process_runs_1": full.get("process_runs") == 1,
        "modes_independent": quick.get("mode") == "quick" and full.get("mode") == "full",
        "rom_identity_equal": quick.get("rom_sha256") == full.get("rom_sha256"),
        "runner_identity_equal": quick.get("runner_sha256") == full.get("runner_sha256"),
        "cases_identity_equal": quick.get("cases_sha256") == full.get("cases_sha256"),
        "warnings_errors_zero": quick.get("warnings_errors") == 0
        and full.get("warnings_errors") == 0,
    }
    failed_mgba = sorted(key for key, passed in mgba_checks.items() if passed is not True)
    if failed_mgba:
        _fail(f"MGBA_TWO_PROCESS acceptance failed: {failed_mgba}")
    acceptance_evidence["MGBA_TWO_PROCESS"] = {
        "status": "PASS",
        "source": "mGBA_quick+full_process_identity",
        "checks": mgba_checks,
    }

    if set(acceptance_evidence) != set(ACCEPTANCE_KEYS):
        missing = sorted(set(ACCEPTANCE_KEYS) - set(acceptance_evidence))
        extra = sorted(set(acceptance_evidence) - set(ACCEPTANCE_KEYS))
        _fail(f"acceptance evidence keys differ: missing={missing} extra={extra}")
    if any(row.get("status") != "PASS" for row in acceptance_evidence.values()):
        _fail("not all 15 QOL acceptance rows are grounded PASS")

    features = {
        str(binding["feature_key"]): {
            "status": "PASS",
            "case": str(binding["mgba_case"]),
            "quick": quick["feature_checks"][str(binding["feature_key"])],
            "full": full["feature_checks"][str(binding["feature_key"])],
        }
        for binding in bindings
    }
    coverage = {
        "schema_version": 1,
        "task": TASK,
        "status": "PASS",
        "acceptance": {
            key: {
                "status": acceptance_evidence[key]["status"],
                "evidence": {
                    field: value for field, value in acceptance_evidence[key].items()
                    if field != "status"
                },
            }
            for key in ACCEPTANCE_KEYS
        },
        "feature_checks": features,
        "mgba": {
            mode: {
                "artifact": path.as_posix(),
                "rom_sha256": documents[mode]["rom_sha256"],
                "runner_sha256": documents[mode]["runner_sha256"],
                "cases_sha256": documents[mode]["cases_sha256"],
                "process_runs": documents[mode]["process_runs"],
                "warnings_errors": documents[mode]["warnings_errors"],
            }
            for mode, path in (("quick", OUTPUT_MGBA_QUICK), ("full", OUTPUT_MGBA_FULL))
        },
        "normal_entry_paths": {
            "settings": "start_menu+SELECT", "pc": "Task_PokeStorageMain HandleInput",
            "summary": "PrintSkillsPage", "bag": "existing item callbacks",
            "field": "ReadKeys/field movement", "battle": "action/move controllers",
            "daycare": "ShouldEggHatch step path",
        },
        "fault_contracts": [
            "cancel-before-mutation", "bag-preflight-then-exact-rollback",
            "box-capacity-preflight", "stock-save+sector31 compensation",
            "queue-full-no-RNG", "random-wild-PID-one-shot-token",
        ],
        "mgba_case_count": len(cases),
    }
    return _stable(coverage)


def _mgba_outputs(outputs: Mapping[str, bytes]) -> dict[str, bytes]:
    runner = ROOT / "tools/mgba_qol_production_smoke.c"
    if not runner.is_file():
        _fail("QOL mGBA runner is missing")
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    bindings, case_rows = _binding_evidence(outputs)
    feature_keys = {str(row["feature_key"]) for row in bindings}
    entry = metadata["runtime"]["entrypoints"]
    stage35_handoff = metadata["runtime"].get("stage35_runtime_handoff", {})
    handoff_names = (
        "trainer_probe", "dynamax_command_data", "tera_command_data",
    )
    if set(stage35_handoff) != set(handoff_names):
        _fail("QOL mGBA Stage35 runtime handoff differs")
    names = [
        "VegaQolProduction_Probe", "VegaQolProduction_Dispatch",
        "VegaQolProduction_ReadKeysAdapter", "VegaQolProduction_PssHandleInputAdapter",
        "VegaQolProduction_GetTextSpeedDelay", "VegaQolProduction_ShouldEggHatchAdapter",
        "VegaQolProduction_HandleInputChooseActionAdapter",
        "VegaQolProduction_StartMenuPanel", "VegaQolProduction_SaveLoadAdapter",
        "VegaQolProduction_TryGenerateWildMonAdapter",
        "VegaQolProduction_GenerateFishingEncounterAdapter",
        "VegaQolProduction_DoStandardWildBattleAdapter",
        "VegaQolProduction_HandleInputChooseMoveAdapter",
        "VegaQolProduction_FeatureUnlocked",
        "VegaQolProduction_ClaimOneTimeReward",
        "VegaQolProduction_PurchaseSupply",
        "VegaQolProduction_IsReusableTm",
        "VegaQolProduction_ModifyBreedingScore",
        "VegaQolProduction_TryHiddenEncounterAdapter",
        "VegaQolProduction_FieldUseCommonQuantityAdapter",
        "VegaQolProduction_SummaryInputAdapter",
        "VegaQolProduction_PrintSkillsPageAdapter",
        "VegaQolProduction_EggHatchPresentationAdapter",
        "VegaQolProduction_GiveEggFromDaycareAdapter",
        "VegaQolProduction_GiveEggFromDaycareSpecial",
        "VegaQolProduction_CalculatePartyCountForDaycare",
        "VegaQolProduction_RunTextPrintersForInstantText",
        "VegaQolProduction_ApplyExpCandyQuantityAdapter",
        "VegaQolProduction_TestInjectPersistenceFault",
        "VegaQolProduction_OpenSupplyShop",
        "VegaQolProduction_ConfigureTrainerBattleAdapter",
    ]
    missing = [name for name in names if name not in entry]
    if missing:
        _fail(f"QOL mGBA entrypoints missing: {missing}")
    with tempfile.TemporaryDirectory(prefix="vega-qol-mgba-") as temporary:
        directory = Path(temporary)
        executable = directory / "mgba-qol-production"
        rom = directory / "stage36.gba"
        cases = directory / "cases.csv"
        rom.write_bytes(outputs[OUTPUT_ROM.as_posix()])
        cases.write_bytes(outputs[OUTPUT_CASES.as_posix()])
        _run([
            _host_cc(ROOT), "-std=c11", "-Wall", "-Wextra", "-Werror",
            str(runner), "-o", str(executable), "-lmgba",
        ], "QOL libmGBA compile")
        result: dict[str, bytes] = {}
        documents: dict[str, dict[str, Any]] = {}
        for mode, output_path, timeout in (
            ("quick", OUTPUT_MGBA_QUICK, 300), ("full", OUTPUT_MGBA_FULL, 900),
        ):
            save = directory / f"{mode}.sav"
            stdout = _run([
                str(executable), str(rom), str(save), str(cases), mode,
                *[hex(entry[name]) for name in names],
                *[hex(stage35_handoff[name]) for name in handoff_names],
            ], f"QOL mGBA {mode}", timeout=timeout)
            try:
                document = json.loads(stdout)
            except json.JSONDecodeError as exc:
                _fail(f"QOL mGBA output is not JSON: {exc}: {stdout[-1000:]}")
            checks = document.get("checks")
            runner_coverage = document.get("coverage")
            if (document.get("status") != "PASS"
                or document.get("mode") != mode
                or not isinstance(checks, dict)
                or not checks
                or any(value is not True for value in checks.values())
                or not isinstance(runner_coverage, dict)
                or runner_coverage.get("features") != FEATURE_COUNT
                or runner_coverage.get("case_rows") != FEATURE_COUNT
                or document.get("warnings_errors") != 0):
                _fail(f"QOL mGBA {mode} did not report all-PASS")
            _exact_true_map(document, "feature_checks", feature_keys, f"QOL mGBA {mode}")
            _exact_true_map(
                document, "acceptance_checks", set(DYNAMIC_ACCEPTANCE_KEYS),
                f"QOL mGBA {mode}",
            )
            document.update({
                "fixture": "qol_production_exact_rom_user_paths",
                "rom_sha256": _sha(outputs[OUTPUT_ROM.as_posix()]),
                "cases_sha256": _sha(outputs[OUTPUT_CASES.as_posix()]),
                "runner_sha256": _sha(runner.read_bytes()),
                "process_runs": 1,
            })
            documents[mode] = document
            result[output_path.as_posix()] = _stable(document)
        result[OUTPUT_COVERAGE.as_posix()] = _coverage_document(
            outputs, bindings, case_rows, documents,
        )
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "check", "build-runtime-only", "mgba"))
    args = parser.parse_args()
    try:
        outputs = build_outputs()
        repeated = build_outputs()
        if outputs != repeated:
            _fail("QOL production build is not byte deterministic")
        if args.mode == "build-runtime-only":
            _write_outputs(outputs)
        elif args.mode in {"check", "mgba"}:
            _check_outputs(outputs)
        mgba: dict[str, bytes] = {}
        if args.mode in {"build", "check", "mgba"}:
            mgba = _mgba_outputs(outputs)
            if args.mode == "build":
                _write_outputs({**outputs, **mgba})
            elif args.mode == "mgba":
                _write_outputs(mgba)
            else:
                _check_outputs(mgba)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, QolBuildError) as error:
        print(f"QOL production build failed: {error}", file=sys.stderr)
        return 1
    metadata = json.loads(outputs[OUTPUT_META.as_posix()])
    print(
        "QOL production %s: PASS stage=%s features=%d hooks=%d artifacts=%d"
        % (args.mode, metadata["output"]["sha256"], FEATURE_COUNT,
           metadata["hooks"]["count"], len(outputs) + len(mgba))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
