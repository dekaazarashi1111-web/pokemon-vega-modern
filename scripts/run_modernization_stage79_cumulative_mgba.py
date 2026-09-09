#!/usr/bin/env python3
"""最新累積ROMに対する重いmGBA最終1セットを再開可能に順次実行する。"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path("config/modernization_stage79_cumulative_mgba.json")
TASK = "USER-MODERNIZATION-STAGE79-CUMULATIVE-MGBA"
STAGE = 79
INPUT_TASK = "USER-MODERNIZATION-P05-STAGE78-EELEVATE-SWITCH-AI"
EXPECTED_STAGE78_COMMIT = "a98e6fea59db1f020bc902a1b1676699f8c06c41"
ROM_BASE = 0x08000000
ROM_SIZE = 32 * 1024 * 1024
READY = "READY"
PENDING = "PENDING_MISSING_RUNNER"
EXPECTED_STAGE78_INPUT = {
    "stage": 78,
    "task": INPUT_TASK,
    "commit": EXPECTED_STAGE78_COMMIT,
    "allocation_count": 82,
    "allocation_last_sequence": 81,
    "rom": {
        "path": "build/stages/78_modernization_p05_eelevate_switch_ai.gba",
        "size": 33554432,
        "sha256": "98fde60231175492032f0e28ca16549a73ca5b29e3f37438b77c6e3c80e9d06b",
        "crc32": "BFF0203C",
    },
    "metadata": {
        "path": "build/stages/78_modernization_p05_eelevate_switch_ai.json",
        "size": 27723,
        "sha256": "1ab572da80715bc07a275781fda27b0f04ababa19e8214bdc6df3bcf00e0c7d8",
    },
    "allocation": {
        "path": "build/stages/78_modernization_p05_eelevate_switch_ai_allocation.json",
        "size": 47029,
        "sha256": "b92ef83b96482c6fc5f751af87a4dc7eb4783a10258b1c193fa298cc485d8d3b",
    },
    "checkpoint": {
        "path": "content/modernization/p05_stage78_eelevate_switch_ai_checkpoint.json",
        "size": 27494,
        "sha256": "19f0f88c1ddecd2f4270e259c81f1535f81ca1716437854d05d90e080111c22f",
    },
}

EXPECTED_STAGE78_P05_SOURCES = {
    "stage78_config": {
        "path": "config/modernization_p05_stage78_eelevate_switch_ai.json",
        "size": 10010,
        "sha256": "649535b79d6ac2c0ec61a8e5c4ae5df9028bf515d92d05d2f37048bfa7bebe7a",
    },
    "stage78_symbols": {
        "path": "generated/runtime/modernization_p05_stage78_eelevate_switch_ai_symbols.json",
        "size": 5165,
        "sha256": "36d009a404c61182c6178bfe64b95fea03bf2dde901352a14bc018ed21ba45f6",
    },
    "stage78_contract": {
        "path": "content/modernization/p05_stage78_eelevate_switch_ai_contract.json",
        "size": 24370,
        "sha256": "c10362f53806421e79a5ea3b63d49eb90587b6dbc63446e94b267cbbe4700b5c",
    },
}

EXPECTED_STAGE78_STATUS = (
    "EELEVATE_DEDICATED_SWITCH_AI_MATERIALIZED_CUMULATIVE_MGBA_PENDING"
)
EXPECTED_STAGE78_FIRST81_SHA256 = (
    "583a335d22131d9afe78859a6e14d7acede052ba187375f7a566be0b09befaf5"
)
EXPECTED_STAGE78_FIRST82_SHA256 = (
    "cbccabcf6c00d8b34e31174ac076644f3b6da0d03cc74a413c772774de64c046"
)
EXPECTED_STAGE78_PAYLOAD_SHA256 = (
    "a6b5fb28cca365af8e08862e673ce5040bbcf4deb0683566b79a552853d1f905"
)
EXPECTED_STAGE78_ALLOCATION = {
    "alignment": 16,
    "content_sha256": EXPECTED_STAGE78_PAYLOAD_SHA256,
    "end_exclusive": 22896624,
    "gba_end_exclusive": 157114352,
    "gba_start": 157113664,
    "name": "modernization_p05_stage78_eelevate_switch_ai_payload",
    "owner": INPUT_TASK,
    "placement": "FIRST_FIT",
    "purpose": "Eelevate-aware FindMonThatAbsorbsOpponentsMove adapters and stable runtime probe",
    "region": "integration_modules",
    "sequence": 81,
    "size": 688,
    "start": 22895936,
}
EXPECTED_STAGE78_PAYLOAD = {
    "allocation_sequence": 81,
    "load_address": "0x095D5D40",
    "path": "generated/runtime/modernization_p05_stage78_eelevate_switch_ai.bin",
    "sha256": EXPECTED_STAGE78_PAYLOAD_SHA256,
    "size": 688,
    "start": 22895936,
}
EXPECTED_STAGE78_LINEAGE = {
    "first81_all_fields_equal": True,
    "new_count": 82,
    "new_first81_sha256": EXPECTED_STAGE78_FIRST81_SHA256,
    "new_sequence": 81,
    "parent_count": 81,
    "parent_first81_sha256": EXPECTED_STAGE78_FIRST81_SHA256,
    "parent_last_sequence": 80,
    "payload_slice_sha256": EXPECTED_STAGE78_PAYLOAD_SHA256,
}

EXPECTED_DOMAIN_ORDER = (
    "p02", "mega_shop", "floette", "p03", "p04_mega_runtime",
    "battle_policy", "p05",
)

P03_SYMBOL_BINDINGS = (
    ("stage73", "Stage73_RuntimeProbe", "stage73-probe", "thumb_address"),
    ("stage73", "Stage73_GetAllEggMoves", "stage73-get-all-egg", "thumb_address"),
    ("stage73", "Stage73_RotomSignatureMove", "stage73-rotom-signature", "thumb_address"),
    ("stage74", "Stage74_RuntimeProbe", "stage74-probe", "thumb_address"),
    ("stage75", "Stage75_RuntimeProbe", "stage75-probe", "thumb_address"),
    ("stage75", "Stage75_GetEggSpecies", "stage75-get-egg-species", "thumb_address"),
    ("stage75", "Stage75_GetEggMoves", "stage75-get-egg-moves", "thumb_address"),
    ("stage75", "Stage75_GetMoveRelearnerMoves", "stage75-get-relearner", "thumb_address"),
    ("stage75", "Stage75_BuildLearnableMoveset", "stage75-build-learnable", "thumb_address"),
    ("stage75", "Stage75_SetMachineMode", "stage75-set-machine", "thumb_address"),
    ("stage75", "Stage75_SetTutorMode", "stage75-set-tutor", "thumb_address"),
    ("stage75", "Stage75_ResetMode", "stage75-reset-mode", "thumb_address"),
    ("stage75", "Stage75_PrepareMachinePages", "stage75-prepare-pages", "thumb_address"),
    ("stage75", "Stage75_SelectedMachinePageHasMoves", "stage75-page-has-moves", "thumb_address"),
    ("stage75", "Stage75_CommitMachinePage", "stage75-commit-page", "thumb_address"),
    ("stage75", "Stage75_OpenArchiveModeMenu", "stage75-open-archive", "thumb_address"),
    ("stage75", "Stage75_OpenMachinePageMenu", "stage75-open-page", "thumb_address"),
    ("stage75", "Stage75_Table_evolution", "stage75-evolution-table", "address"),
)

P03_ROOT_BINDINGS = (
    ("level-root-site", "level-root", 4),
    ("level-root-mirror-site", "level-root", 4),
    ("tutor-root-site", "tutor-root", 4),
    ("tutor-catalog-site", "tutor-catalog", 4),
    ("egg-root-site-a", "egg-root", 4),
    ("egg-root-site-b", "egg-root", 4),
    ("egg-limit-site", "egg-limit", 4),
)

P03_DYNAMIC_ARGUMENT_KEYS = (
    "own-tempo-egg-move0", "own-tempo-egg-move1",
    "own-tempo-egg-move2", "own-tempo-egg-move3", "scratch-address",
)

P03_TERMINAL_REQUIRED_TOKENS = (
    "STAGE75_EXPORT Stage75_FinishScript",
    "STAGE75_CALLNATIVE Stage75_ResetMode",
    "STAGE75_BRANCH 1, Stage75_FinishScript",
    "STAGE75_GOTO Stage75_FinishScript",
    "STAGE75_EXPORT Stage75_MachineChoosePageScript",
    "STAGE75_EXPORT Stage75_MachinePageNoMovesScript",
)

P05_GLOBAL_ARGUMENT_NAMES = (
    "Stage77_RuntimeProbe", "gBattleTypeFlags", "gBattleCircusFlags",
    "gStatuses3", "IsAbilitySuppressed", "Stage76_RuntimeProbe",
    "Stage76_PayloadStart", "Stage76_PayloadSize", "Stage76_MegaSolRoute",
    "Stage76_QuarterPredictedProtectDamage",
    "Stage76_NormalizePredictedProtectionMove", "Stage76_IsPlannedMaxGuard",
    "Stage76_DirectEffectCanDamagePartner", "Stage76_SelectAIAttackerAbility",
    "Stage76_SpicyPolicyCore", "Stage76_SpicyPathQualifies",
    "Stage76_DispatchMegaSolSolarBeam", "Stage76_BattleScriptMegaSolPopup",
    "HOOK_Stage76SolarBeam", "Stage76_BattleScriptSolarBeam",
    "HOOK_Stage76AICalcDmg", "Stage76_EntryAICalcDmg",
    "HOOK_Stage76AIScriptPartner", "Stage76_EntryAIScriptPartner",
    "HOOK_Stage76RangeMoveCanHurtPartner",
    "Stage76_EntryRangeMoveCanHurtPartner",
    "Stage78_RuntimeProbe", "Stage78_MapEelevateAbsorber",
    "Stage78_ActiveAbsorberAbility", "Stage78_PartyAbsorberAbility",
    "Stage78_EntryFindMonAbsorberActive",
    "Stage78_EntryFindMonAbsorberParty",
    "HOOK_FindMonAbsorberActiveAbilityBlock",
    "HOOK_FindMonAbsorberPartyAbilityBlock",
    "CONT_FindMonAbsorberActiveAbilityBlock",
    "CONT_FindMonAbsorberPartyAbilityBlock",
    "gBattlersCount", "gBattleMons", "gAbsentBattlerFlags", "gBattleMoves",
    "LoadBattlersAndFoes", "GetPredictedAIAbility", "GetAIAbility",
    "IsValidMovePrediction", "GetMonAbility", "GetBankItemEffect",
    "GetMonItemEffect", "CheckMonGrounding", "CheckGrounding",
    "IsTargetAbilityIgnored", "GetMoveTypeSpecial",
)

P05_DISPATCHER_SUFFIXES = (
    "AbilityBattleEffects", "ProtectAffects", "DoesProtectionMoveBlockMove",
    "AccuracyCalc", "VisualAccuracyCalc", "VisualAccuracyCalcNoTarget",
    "Atk01AccuracyCheck", "ModifyGrowthInSun", "NonInvasiveCheckGrounding",
    "CheckMonGrounding", "CheckGroundingByDetails", "CheckGrounding",
    "AttacksThisTurn", "Atk49MoveEnd", "AdjustBasePower",
    "Atk4ATypeCalc2", "Atk06TypeCalc", "GetMoveTypeSpecialPostAbility",
    "GetExceptionMoveType", "GetMonExceptionMoveType",
    "GetMoveTypeSpecialPreAbility", "VisualTypeCalcPart", "AITypeCalcPart",
    "AISpecialTypeCalc", "TypeCalc", "CalcVisualBasePower",
    "CalculateBaseDamage", "RecoverBasedOnSunlight", "SetMoveEffect2",
)

P05_FIFTH_STACK_ARGUMENT_SUFFIXES = (
    "AbilityBattleEffects", "NonInvasiveCheckGrounding", "TypeCalc",
)

BATTLE_POLICY_SYMBOL_NAMES = (
    "cfru_integration_stat_inputs_are_valid",
    "cfru_integration_effective_nature",
    "cfru_integration_effective_iv",
    "cfru_integration_ability_slot",
    "cfru_integration_receives_battle_exp",
    "cfru_integration_apply_exp_candy",
    "cfru_integration_trainer_build_apply",
    "VegaConfigureNextBattlePolicy",
    "VegaConfigureNextFacility",
    "VegaConfigureNextMirageItem",
    "VegaConfigureNextRaid",
    "VegaBattlePolicyEnd",
    "VegaFacilityStateIsActive",
    "VegaFacilityStateGet",
    "VegaFacilityStateSet",
    "VegaBattlePolicyCanMega",
    "VegaBattlePolicyMarkMega",
    "VegaBattlePolicyCanZ",
    "VegaBattlePolicyMarkZ",
    "VegaBattlePolicyCanDynamax",
    "VegaBattlePolicyMarkDynamax",
    "VegaBattlePolicyCanTera",
    "VegaBattlePolicyMarkTera",
    "cfru_integration_mechanic_can_use",
    "cfru_integration_mechanic_try_use",
    "cfru_integration_mechanic_is_forced",
    "cfru_integration_persistent_effect_allowed",
    "cfru_integration_mirage_current",
    "cfru_integration_mirage_set_battle_value",
    "cfru_integration_raid_begin",
    "cfru_integration_raid_partner_is_active",
    "cfru_integration_raid_shields_remaining",
    "cfru_integration_raid_break_shield",
    "cfru_integration_raid_set_boss_hp",
    "cfru_integration_raid_advance_turn",
    "cfru_integration_raid_try_capture",
    "cfru_integration_raid_end",
    "GetNumRaidShieldsUp",
    "IsRaidBattle",
    "IsCatchableRaidBattle",
    "sp067_GenerateRandomBattleTowerTeam",
    "HandleInputChooseAction",
    "HandleInputChooseMove",
    "HandleInputChooseTarget",
)

RESULT_TOP_LEVEL_KEYS = {
    "p02": frozenset({
        "schema_version", "status", "classification", "rom_sha256",
        "known_good_seed_sha256", "boot_route",
        "initial_normal_continue_field", "fixture_replacement_after_field",
        "warnings_errors", "temporary_save_only", "direct_conditions",
        "normal_evolution_cancel", "normal_evolution_success",
        "conditional_form_success", "bag_item_use", "bag_item_missing",
        "save_reload",
    }),
    "mega_shop": frozenset({
        "schema_version", "stage", "status", "warnings_errors", "checks",
        "representative_indices", "representative_item_ids",
        "representative_claim_flags", "accepted_item_boundary_ids",
        "first_rejected_item_id", "hold_effect", "price_bp", "initial_bp",
        "final_bp", "bag_full_capacity", "core_instances", "process_runs",
        "framebuffer_transitions", "state_fixture", "retained_artifacts",
    }),
    "floette": frozenset({
        "schema_version", "task", "stage", "status", "warnings_errors",
        "checks", "pc_destination", "core_instances", "process_runs",
        "framebuffer_transitions", "state_fixture", "retained_artifacts",
    }),
    "p03": frozenset({
        "schema_version", "status", "classification", "rom_sha256",
        "process_runs", "read_only", "warnings_errors", "checks",
        "full_p03_acceptance", "scheduler_e2e", "breeding_e2e",
        "save_reload_e2e", "artifacts_written",
    }),
    "mega_runtime_triples": frozenset({
        "schema_version", "status", "classification", "rom_sha256",
        "read_only", "mapping_count", "correct_stone_matches",
        "stone_less_rejections", "mega_species_recognized",
        "base_species_rejected_as_mega", "reversions_to_base",
        "direct_calls", "instructions", "symbols", "payload_pc_seen",
        "warnings_errors", "artifacts_written",
    }),
    "battle_policy": frozenset({
        "schema_version", "status", "fixture", "rom_sha256",
        "fixed_rtc_unix", "read_only", "boot_trace_segments",
        "warnings_errors", "direct_calls", "direct_call_instructions",
        "payload_calls", "actual_battle_setups", "stat_inputs",
        "exp_candy", "trainer_build", "mechanics", "facility", "mirage",
        "raid", "non_e2e_routes", "unreached_routes", "artifacts_written",
    }),
    "p05_runtime": frozenset({
        "schema_version", "status", "classification", "rom_sha256",
        "read_only", "warnings_errors", "dispatcher_count",
        "ability_surface_occurrence_count", "normal_delegations",
        "circus_original_delegations", "predicate_truth_table_pass",
        "stage76_helpers_preserved", "suppression_paths_pass",
        "stage76_megasol_production_dispatch_pass",
        "stage76_suppression_link_count", "dispatcher_observations",
        "direct_calls", "dispatcher_instructions", "direct_call_instructions",
        "fifth_stack_argument_observations", "fifth_stack_arguments_preserved",
        "eelevate_switch_ai_done", "eelevate_matrix_case_count",
        "eelevate_matrix_observations", "eelevate_matrix_sha256",
        "eelevate_pure_helper_pass", "eelevate_active_helper_pass",
        "eelevate_party_helper_pass", "eelevate_active_hook_route_pass",
        "eelevate_party_hook_route_pass", "eelevate_stub_calls_observed",
        "eelevate_active_hook_observations",
        "eelevate_party_hook_observations",
        "eelevate_register_continuation_abi_pass",
        "full_p05_acceptance", "scheduler_e2e",
        "artifacts_written",
    }),
}

EXPECTED_PREIMAGES = (
    ("P02_BeginEvolutionScene", 0x080CEF00, "70b50c1c151c1e1c"),
    ("P02_GetEvolutionTargetSpecies", 0x090FB774, "f0b557464e464546"),
    ("P02_ItemEvolutionRemoval", 0x090FB630, "10b50c4b040082b0"),
    ("P02_GetMonAbility", 0x090DA23C, "f8b500220b21144f"),
    ("P02_CalculateMonStats", 0x090D939C, "f0b5de4657464e46"),
    ("P02_ItemUseCB_EvolutionStone", 0x09122C8C, "f0b5d6464f464646"),
    ("P02_TrySavingData", 0x080DB34C, "004b184761763709"),
    ("P02_Save_LoadGameData", 0x080DB4E4, "004b1847815d4009"),
    ("MegaShop_Probe", 0x09452350, "034b044a1380044a"),
    ("MegaShop_EnsureSave", 0x09452370, "10b500f0c1fa431e"),
    ("MegaShop_GetBalance", 0x09452390, "10b500f0b1fa0023"),
    ("MegaShop_IsUnlocked", 0x094523BC, "10b5040000f09afa"),
    ("MegaShop_IsClaimed", 0x094523F0, "002310b52c2802d8"),
    ("MegaShop_PurchaseByIndex", 0x09452410, "10b5040000f0d8fa"),
    ("MegaShop_Open", 0x0945244C, "70b500f099f80028"),
    ("FloetteGift_Probe", 0x09462AB0, "024b034a03481a80"),
    ("FloetteGift_Claim", 0x09462B14, "f0b5784887b0784f"),
    ("FloetteGift_IsFormObtained", 0x09462AC8, "054b10b5054800f0"),
    ("FloetteGift_IsNationalDexSeen", 0x09462AF0, "034b1878034b4007"),
    ("FloetteGift_IsNationalDexCaught", 0x09462B08, "10b5fff7f1ff10bc"),
    ("P03_GetEvolutionTargetSpecies", 0x09114120, "8446f8b562465423"),
    ("P03_CanLearnTutorMove", 0x09110228, "f8b500220c00544f"),
    ("Stage73_RuntimeProbe", 0x095347D0, "03000020032b02d8"),
    ("Stage74_RuntimeProbe", 0x09539C80, "03000020042b02d8"),
    ("Stage75_RuntimeProbe", 0x0954B030, "03000020052b02d8"),
    ("Stage75_GetEggSpecies", 0x0954B188, "064a10b5064b9042"),
    ("Stage75_BuildLearnableMoveset", 0x0954B41C, "73b500220c001f4b"),
    ("P04_GetMegaSpecies", 0x09114CF0, "c3011e481b18f0b5"),
    ("P04_TryRevertMega", 0x09114F74, "70b5048c0d4be401"),
    ("P04_IsMegaSpecies", 0x09115098, "0c4bc001c0180200"),
)


class Stage79CumulativeMgbaError(RuntimeError):
    """累積ROM identity、runner、result、または再開契約の違反。"""


def _fail(message: str) -> NoReturn:
    raise Stage79CumulativeMgbaError(message)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _stable(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}がboolです")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}が整数ではありません: {value!r}")


def _relative_path(value: Any, label: str, *, must_exist: bool = True) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        _fail(f"{label}はrepository相対path必須です")
    candidate = ROOT / value
    try:
        resolved = candidate.resolve(strict=must_exist)
        resolved.relative_to(ROOT.resolve())
    except (OSError, ValueError) as error:
        _fail(f"{label}がworkspace外または欠落です: {value}: {error}")
    if must_exist and (candidate.is_symlink() or not resolved.is_file()):
        _fail(f"{label}がworkspace内の通常fileではありません: {value}")
    return resolved


def _read_json_path(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"{label}をJSONとして読めません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _read_json(relative: str, label: str) -> dict[str, Any]:
    return _read_json_path(_relative_path(relative, label), label)


def _fixed_json(record: Mapping[str, Any], label: str) -> dict[str, Any]:
    _path, raw = _fixed(record, label)
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        _fail(f"{label}をJSONとして読めません: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _member(value: Any, path: Sequence[str], label: str) -> Any:
    current = value
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            _fail(f"{label}に{'.'.join(path)}がありません")
        current = current[key]
    return current


def _identity(relative: str, label: str) -> dict[str, Any]:
    path = _relative_path(relative, label)
    raw = path.read_bytes()
    return {"path": relative, "size": len(raw), "sha256": _sha(raw)}


def _fixed(record: Mapping[str, Any], label: str) -> tuple[Path, bytes]:
    if not isinstance(record, Mapping):
        _fail(f"{label} identityがobjectではありません")
    relative = record.get("path")
    if not isinstance(relative, str):
        _fail(f"{label}.pathがありません")
    path = _relative_path(relative, label)
    raw = path.read_bytes()
    expected_size = _integer(record.get("size"), f"{label}.size")
    expected_sha = record.get("sha256")
    if expected_size != len(raw) or not isinstance(expected_sha, str) \
            or len(expected_sha) != 64 or _sha(raw) != expected_sha:
        _fail(f"{label} size/SHA-256不一致")
    return path, raw


def _config_path(path: Path) -> Path:
    absolute = path if path.is_absolute() else ROOT / path
    try:
        resolved = absolute.resolve(strict=True)
        resolved.relative_to(ROOT.resolve())
    except (OSError, ValueError) as error:
        _fail(f"Stage79 configがworkspace内の通常fileではありません: {error}")
    if absolute.is_symlink() or not resolved.is_file():
        _fail("Stage79 configがworkspace内の通常fileではありません")
    return resolved


def _validate_config(config: Mapping[str, Any]) -> None:
    if (config.get("schema_version"), config.get("task"), config.get("stage")) \
            != (1, TASK, STAGE):
        _fail("Stage79 config schema/task/stage不一致")
    if config.get("classification") != "VALIDATION_ONLY_NO_PRODUCT_ROM_PATCH":
        _fail("Stage79はvalidation-onlyでなければなりません")
    input_contract = config.get("input_identity")
    if not isinstance(input_contract, Mapping) \
            or dict(input_contract) != EXPECTED_STAGE78_INPUT:
        _fail("input_identity exact Stage78 contract不一致")
    input_stage = _integer(input_contract.get("stage"), "input_identity.stage")
    if input_stage != 78 or input_contract.get("task") != INPUT_TASK:
        _fail("Stage79 inputはexact Stage78必須です")
    for key in ("rom", "metadata", "allocation", "checkpoint"):
        row = input_contract.get(key)
        if not isinstance(row, Mapping):
            _fail(f"input_identity.{key}がありません")
        if key == "rom" and _integer(row.get("size"), "ROM size") != ROM_SIZE:
            _fail("累積入力ROMは32 MiB必須です")
        if not isinstance(row.get("sha256"), str) or len(row["sha256"]) != 64:
            _fail(f"input_identity.{key} SHA-256 pin不一致")

    execution = config.get("execution")
    if not isinstance(execution, Mapping):
        _fail("execution contractがありません")
    order = execution.get("domain_order")
    domains = config.get("domains")
    if not isinstance(order, list) or not isinstance(domains, list) or not domains:
        _fail("domain_order/domainsが不正です")
    ids = [row.get("id") for row in domains if isinstance(row, Mapping)]
    if len(ids) != len(domains) or order != ids or len(ids) != len(set(ids)):
        _fail("domain順序/IDが一意に固定されていません")
    if tuple(ids) != EXPECTED_DOMAIN_ORDER:
        _fail("Stage79累積domainのexact順序不一致")
    state_root = execution.get("state_root")
    if not isinstance(state_root, str) or not state_root.startswith(".local/"):
        _fail("再開stateは.local配下必須です")
    gate = execution.get("runtime_gate")
    if gate != "content/modernization/stage79_cumulative_mgba_runtime_gate.json":
        _fail("Stage79 runtime gate path不一致")

    kinds = {
        "p02", "mega_shop", "floette", "p03", "battle_policy",
        "mega_runtime_triples", "p05_runtime", "generic_json",
    }
    for index, row in enumerate(domains):
        assert isinstance(row, Mapping)
        label = f"domains[{index}]"
        if row.get("state") not in {READY, PENDING}:
            _fail(f"{label}.state不一致")
        if row.get("kind") not in kinds:
            _fail(f"{label}.kind不一致")
        timeout = _integer(row.get("timeout_seconds"), f"{label}.timeout_seconds")
        if timeout < 30 or timeout > 1800:
            _fail(f"{label}.timeout_seconds範囲外")
        runner = row.get("runner")
        if not isinstance(runner, Mapping) or not isinstance(runner.get("path"), str):
            _fail(f"{label}.runner不一致")
        if row.get("state") == READY:
            if not isinstance(runner.get("sha256"), str) \
                    or len(runner["sha256"]) != 64:
                _fail(f"{label} READY runner identity未固定")
            compile_contract = row.get("compile")
            if not isinstance(compile_contract, Mapping) \
                    or not isinstance(compile_contract.get("flags"), list) \
                    or not isinstance(compile_contract.get("link_flags"), list):
                _fail(f"{label} compile contract不一致")
            if compile_contract.get("compiler") != "cc" \
                    or compile_contract.get("flags") != [
                        "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                        "-Itools",
                    ] \
                    or compile_contract.get("link_flags") != ["-lmgba"]:
                _fail(f"{label} compile exact contract不一致")
        else:
            if row.get("pending_reason") not in {
                "RUNNER_NOT_YET_IMPLEMENTED",
                "WAITING_FINAL_INPUT_AND_RUNNER",
            }:
                _fail(f"{label} pending reason不一致")

    p03 = config.get("p03_contract")
    if not isinstance(p03, Mapping) or not isinstance(p03.get("arguments"), Mapping):
        _fail("P03 dynamic ABI contractがありません")
    expected_argument_keys = config.get("p03_required_argument_keys")
    if not isinstance(expected_argument_keys, list) \
            or expected_argument_keys != sorted(set(expected_argument_keys)) \
            or set(p03["arguments"]) != set(expected_argument_keys):
        _fail("P03 dynamic CLI argument集合不一致")
    for key, value in p03["arguments"].items():
        _integer(value, f"p03_contract.arguments.{key}")


def _validate_input(config: Mapping[str, Any]) -> tuple[Path, bytes, dict[str, Any]]:
    contract = config["input_identity"]
    if not isinstance(contract, Mapping) \
            or dict(contract) != EXPECTED_STAGE78_INPUT:
        _fail("cumulative input exact Stage78 identity不一致")
    rom_path, rom = _fixed(contract["rom"], "cumulative input ROM")
    _metadata_path, metadata_raw = _fixed(contract["metadata"], "input metadata")
    _allocation_path, allocation_raw = _fixed(contract["allocation"], "input allocation")
    _checkpoint_path, checkpoint_raw = _fixed(contract["checkpoint"], "input checkpoint")
    if len(rom) != ROM_SIZE:
        _fail("cumulative input ROM size不一致")
    actual_crc32 = f"{zlib.crc32(rom) & 0xFFFFFFFF:08X}"
    if contract["rom"].get("crc32") != actual_crc32:
        _fail("cumulative input ROM CRC32不一致")
    try:
        metadata = json.loads(metadata_raw)
        allocation = json.loads(allocation_raw)
        checkpoint = json.loads(checkpoint_raw)
    except (UnicodeError, json.JSONDecodeError) as error:
        _fail(f"input identity JSON不一致: {error}")
    stage = _integer(contract["stage"], "input stage")
    rom_identity = dict(contract["rom"])
    if metadata.get("stage") != stage or metadata.get("task") != INPUT_TASK \
            or metadata.get("output") != rom_identity:
        _fail("input metadata stage/output identity不一致")
    checkpoint_output = checkpoint.get("output", checkpoint.get("rom"))
    if checkpoint.get("stage") != stage \
            or checkpoint.get("task") != INPUT_TASK \
            or checkpoint_output != rom_identity:
        _fail("input checkpoint stage/output identity不一致")
    for document, label in ((metadata, "metadata"), (checkpoint, "checkpoint")):
        if document.get("schema_version") != 1 \
                or document.get("status") != EXPECTED_STAGE78_STATUS \
                or document.get("allocation_sequence") != 81 \
                or document.get("done") is not False \
                or document.get("full_p05_done") is not False \
                or document.get("release_ready") is not False \
                or document.get("allocation_lineage") \
                    != EXPECTED_STAGE78_LINEAGE \
                or document.get("payload") != EXPECTED_STAGE78_PAYLOAD:
            _fail(f"input {label} Stage78 status/lineage不一致")
    allocations = allocation.get("allocations")
    if not isinstance(allocations, list) \
            or allocation.get("summaries", {}).get("overlap_count") != 0:
        _fail("input allocation lineage/overlap不一致")
    expected_count = _integer(contract.get("allocation_count"),
                              "input allocation count")
    expected_last = _integer(contract.get("allocation_last_sequence"),
                             "input allocation last sequence")
    sequences = [row.get("sequence") for row in allocations
                 if isinstance(row, Mapping)]
    if len(allocations) != expected_count or len(sequences) != expected_count \
            or sequences != list(range(expected_count)) \
            or expected_last != expected_count - 1:
        _fail("input allocation count/sequence lineage不一致")
    if allocation.get("summaries", {}).get("allocation_count") != 82 \
            or allocations[-1] != EXPECTED_STAGE78_ALLOCATION \
            or _sha(_stable(allocations[:81])) \
                != EXPECTED_STAGE78_FIRST81_SHA256 \
            or _sha(_stable(allocations[:82])) \
                != EXPECTED_STAGE78_FIRST82_SHA256 \
            or metadata.get("allocation") != EXPECTED_STAGE78_ALLOCATION \
            or _sha(rom[
                EXPECTED_STAGE78_PAYLOAD["start"]:
                EXPECTED_STAGE78_PAYLOAD["start"]
                    + EXPECTED_STAGE78_PAYLOAD["size"]
            ]) != EXPECTED_STAGE78_PAYLOAD_SHA256:
        _fail("input Stage78 allocation row/first81 contract不一致")
    for document, label in ((metadata, "metadata"), (checkpoint, "checkpoint")):
        lineage = document.get("allocation_lineage")
        if not isinstance(lineage, Mapping) \
                or lineage.get("new_count") != expected_count \
                or lineage.get("new_sequence") != expected_last:
            _fail(f"input {label} allocation lineage cross-link不一致")
    return rom_path, rom, {
        "stage": stage,
        "task": INPUT_TASK,
        "commit": contract["commit"],
        "rom": rom_identity,
        "metadata": dict(contract["metadata"]),
        "allocation": dict(contract["allocation"]),
        "checkpoint": dict(contract["checkpoint"]),
        "allocation_count": len(allocations),
        "allocation_last_sequence": expected_last,
        "allocation_first81_sha256": EXPECTED_STAGE78_FIRST81_SHA256,
        "allocation_first82_sha256": EXPECTED_STAGE78_FIRST82_SHA256,
        "allocation_sequence81": EXPECTED_STAGE78_ALLOCATION,
        "payload_sha256": EXPECTED_STAGE78_PAYLOAD_SHA256,
    }


EXPECTED_STAGE80_ROM = {
    "path": "build/stages/80_modernization_runtime_boundary_repair.gba",
    "size": 33554432,
    "sha256": "6570b82fc062cf163fa66a6d821fea6563021e5a9ca6f26efd583bae71623442",
    "crc32": "E41C2632",
}


def _validate_runtime_candidate(
    config: Mapping[str, Any], parent: bytes, parent_audit: Mapping[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    """Verify a separately materialized derivative; never patch a runtime ROM."""
    candidate = config.get("runtime_candidate")
    if not isinstance(candidate, Mapping) or candidate.get("stage") != 80 \
            or candidate.get("task") != "USER-MODERNIZATION-STAGE80-RUNTIME-BOUNDARY-REPAIR" \
            or candidate.get("rom") != EXPECTED_STAGE80_ROM:
        _fail("Stage80 exact repaired candidate identity mismatch")
    for key, path in (
        ("recipe", "tools/modernization_runtime_boundary_repair.py"),
        ("report", "build/stages/80_modernization_runtime_boundary_repair.json"),
    ):
        if not isinstance(candidate.get(key), Mapping) or candidate[key].get("path") != path:
            _fail(f"Stage80 {key} path mismatch")
    recipe_path, _ = _fixed(candidate["recipe"], "Stage80 repair recipe")
    _report_path, report_raw = _fixed(candidate["report"], "Stage80 repair report")
    _candidate_path, rom = _fixed(candidate["rom"], "Stage80 candidate ROM")
    spec = importlib.util.spec_from_file_location("stage80_boundary_recipe", recipe_path)
    if spec is None or spec.loader is None:
        _fail("Stage80 recipe cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        expected = module.repair_rom(parent)
        report = json.loads(report_raw)
        if rom != expected or report != module.make_report(parent, rom) \
                or report["output"] != EXPECTED_STAGE80_ROM:
            _fail("Stage80 candidate/report differs from exact parent repair")
    except (ValueError, RuntimeError) as error:
        _fail(f"Stage80 repair validation failed: {error}")
    return rom, {
        "stage": 80, "task": candidate["task"], "rom": dict(candidate["rom"]),
        "repair_recipe": dict(candidate["recipe"]), "repair_report": dict(candidate["report"]),
        "parent": dict(parent_audit), "patches": report["patches"],
        "changed_bytes_from_parent": report["changed_bytes"],
        "allocation_layout_unchanged": True,
        "parent_allocation_content_hashes_reused_as_candidate": False,
    }


def _rom_bytes(rom: bytes, address: int, size: int, label: str) -> bytes:
    offset = address - ROM_BASE
    if offset < 0 or offset + size > len(rom):
        _fail(f"{label} ROM範囲外: 0x{address:08X}+{size}")
    return rom[offset:offset + size]


def _u16(rom: bytes, address: int, label: str) -> int:
    return int.from_bytes(_rom_bytes(rom, address, 2, label), "little")


def _u32(rom: bytes, address: int, label: str) -> int:
    return int.from_bytes(_rom_bytes(rom, address, 4, label), "little")


def _validate_preimages(config: Mapping[str, Any], rom: bytes) -> list[dict[str, Any]]:
    rows = config.get("latest_rom_preimages")
    if not isinstance(rows, list) or not rows:
        _fail("latest ROM ABI preimagesがありません")
    normalized = tuple(
        (
            str(row.get("name")),
            _integer(row.get("address"), "latest preimage address"),
            str(row.get("hex")),
        )
        for row in rows if isinstance(row, Mapping)
    )
    if len(normalized) != len(rows) or normalized != EXPECTED_PREIMAGES:
        _fail("latest ROM ABI preimages exact set/order不一致")
    seen: set[tuple[int, int]] = set()
    result = []
    for row in rows:
        if not isinstance(row, Mapping):
            _fail("latest ROM ABI preimage rowがobjectではありません")
        name = row.get("name")
        address = _integer(row.get("address"), f"{name}.address")
        try:
            expected = bytes.fromhex(str(row.get("hex", "")))
        except ValueError:
            _fail(f"{name} preimage hex不正")
        if not name or not expected or (address, len(expected)) in seen:
            _fail("latest ROM ABI preimage重複/空値")
        seen.add((address, len(expected)))
        actual = _rom_bytes(rom, address, len(expected), str(name))
        if actual != expected:
            _fail(f"latest ROM ABI preimage不一致: {name}")
        result.append({"name": name, "address": f"0x{address:08X}",
                       "size": len(expected), "sha256": _sha(actual)})
    return result


def _symbol_address(document: Mapping[str, Any], name: str,
                    field: str = "thumb_address") -> int:
    symbols = document.get("symbols")
    if not isinstance(symbols, Mapping) or not isinstance(symbols.get(name), Mapping):
        _fail(f"symbol documentに{name}がありません")
    row = symbols[name]
    if field not in {"address", "thumb_address"} or field not in row:
        _fail(f"symbol {name}.{field}がありません")
    value = row[field]
    return _integer(value, f"symbol {name}")


def _validate_p03(config: Mapping[str, Any], rom: bytes) -> dict[str, Any]:
    contract = config["p03_contract"]
    evidence = contract.get("symbol_sources")
    if not isinstance(evidence, Mapping):
        _fail("P03 symbol_sourcesがありません")
    documents: dict[str, dict[str, Any]] = {}
    identities: dict[str, dict[str, Any]] = {}
    for key in ("stage73", "stage74", "stage75"):
        path, raw = _fixed(evidence[key], f"P03 {key} symbols")
        try:
            document = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as error:
            _fail(f"P03 {key} symbols JSON不一致: {error}")
        if not isinstance(document, dict):
            _fail(f"P03 {key} symbols root不一致")
        documents[key] = document
        identities[key] = dict(evidence[key])
    for key in ("stage73_route_audit", "stage74_route_audit", "stage75_route_audit"):
        _path, raw = _fixed(evidence[key], f"P03 {key}")
        try:
            value = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as error:
            _fail(f"P03 {key} JSON不一致: {error}")
        if not isinstance(value, dict):
            _fail(f"P03 {key} root不一致")
        identities[key] = dict(evidence[key])
    args = {key: _integer(value, f"P03 arg {key}")
            for key, value in contract["arguments"].items()}
    p03_domain = next(
        (row for row in config["domains"] if row.get("id") == "p03"), None
    )
    if not isinstance(p03_domain, Mapping) \
            or p03_domain.get("kind") != "p03" \
            or p03_domain.get("state") != READY:
        _fail("P03 domainはREADY/p03必須です")
    runner_path, runner_raw = _fixed(p03_domain["runner"], "P03 dynamic runner")
    try:
        runner_text = runner_raw.decode("utf-8")
    except UnicodeError as error:
        _fail(f"P03 dynamic runner decode失敗: {error}")
    runner_keys = sorted(
        set(re.findall(r'p03x_arg\(args, "([^"]+)"', runner_text))
        | set(P03_DYNAMIC_ARGUMENT_KEYS)
    )
    if runner_keys != config["p03_required_argument_keys"] \
            or set(runner_keys) != set(args):
        _fail("P03 runner実使用CLI argument集合不一致")
    if p03_domain.get("argument_count") != len(runner_keys):
        _fail("P03 domain argument count不一致")
    if "mgba_modernization_stage67_p03_acceptance_smoke" in runner_text:
        _fail("P03 runnerが旧Stage67 runnerをincludeしています")
    bindings = contract.get("symbol_bindings")
    if not isinstance(bindings, list) or not bindings:
        _fail("P03 symbol_bindingsがありません")
    normalized_bindings = tuple(
        (
            str(row.get("source")), str(row.get("symbol")),
            str(row.get("argument")), str(row.get("field")),
        )
        for row in bindings
    )
    if normalized_bindings != P03_SYMBOL_BINDINGS:
        _fail("P03 symbol_bindings exact contract不一致")
    for row in bindings:
        source = str(row.get("source"))
        symbol = str(row.get("symbol"))
        argument = str(row.get("argument"))
        field = str(row.get("field"))
        if source not in documents:
            _fail(f"P03 symbol source不一致: {source}")
        actual = _symbol_address(documents[source], symbol, field)
        if args.get(argument) != actual:
            _fail(f"P03 CLI/symbol binding不一致: {argument}/{symbol}")
    roots = contract.get("root_bindings")
    if not isinstance(roots, list) or not roots:
        _fail("P03 root bindingsがありません")
    normalized_roots = tuple(
        (
            str(row.get("site_argument")), str(row.get("value_argument")),
            _integer(row.get("width"), "P03 root width"),
        )
        for row in roots
    )
    if normalized_roots != P03_ROOT_BINDINGS:
        _fail("P03 root bindings exact contract不一致")
    for row in roots:
        site_arg = str(row.get("site_argument"))
        value_arg = str(row.get("value_argument"))
        width = _integer(row.get("width"), "P03 root width")
        actual = _u16(rom, args[site_arg], site_arg) if width == 2 \
            else _u32(rom, args[site_arg], site_arg)
        if actual != args[value_arg]:
            _fail(f"P03 latest root mismatch: {site_arg}->{value_arg}")
    terminal = contract.get("terminal_source")
    terminal_path, terminal_raw = _fixed(terminal, "P03 Stage75 script terminals")
    try:
        terminal_text = terminal_raw.decode("utf-8")
    except UnicodeError as error:
        _fail(f"P03 terminal source decode失敗: {error}")
    required_tokens = contract.get("terminal_required_tokens")
    if not isinstance(required_tokens, list) \
            or tuple(required_tokens) != P03_TERMINAL_REQUIRED_TOKENS \
            or any(token not in terminal_text for token in required_tokens):
        _fail("P03 all-terminal/reset/cancel source contract不一致")
    return {
        "arguments_sha256": _sha(_stable(args)),
        "symbol_sources": identities,
        "symbol_binding_count": len(bindings),
        "root_binding_count": len(roots),
        "terminal_source": dict(terminal),
        "terminal_required_token_count": len(required_tokens),
        "legacy_stage67_runner_used": False,
        "latest_dynamic_runner": True,
        "runner": _identity(
            runner_path.relative_to(ROOT).as_posix(), "P03 dynamic runner"
        ),
        "runner_argument_count": len(runner_keys),
    }


def _validate_domain_sources(domain: Mapping[str, Any]) -> dict[str, Any]:
    if domain["state"] == PENDING:
        path = _relative_path(domain["runner"]["path"],
                              f"{domain['id']} pending runner", must_exist=False)
        return {
            "runner_path": domain["runner"]["path"],
            "runner_present": path.is_file(),
            "status": PENDING,
            "reason": domain["pending_reason"],
        }
    _path, _raw = _fixed(domain["runner"], f"{domain['id']} runner")
    dependencies = domain.get("dependencies", [])
    if not isinstance(dependencies, list):
        _fail(f"{domain['id']} dependencies不一致")
    resolved = [dict(domain["runner"])]
    for index, row in enumerate(dependencies):
        _fixed(row, f"{domain['id']} dependency[{index}]")
        resolved.append(dict(row))
    compiler = str(domain["compile"].get("compiler", "cc"))
    compiler_path = shutil.which(compiler)
    if compiler_path is None:
        _fail(f"{domain['id']} C compilerがありません: {compiler}")
    return {
        "runner": dict(domain["runner"]),
        "sources": resolved,
        "compiler": compiler_path,
        "compile_flags": list(domain["compile"]["flags"]),
        "link_flags": list(domain["compile"]["link_flags"]),
        "status": READY,
    }


def _int_list(value: Any, label: str) -> list[int]:
    if not isinstance(value, list):
        _fail(f"{label}がlistではありません")
    return [_integer(item, f"{label}[{index}]")
            for index, item in enumerate(value)]


def _mega_shop_arguments(domain: Mapping[str, Any]) -> tuple[list[int], dict[str, Any]]:
    source = _fixed_json(domain.get("contract_source"), "Mega shop symbols")
    # Stage68 owns the shop ABI; Stage69 owns the cumulative map graph.
    # Do not edit historical symbols or accept arbitrary extra objects.
    map_source = _fixed_json(domain.get("map_contract_source"),
                             "Stage79 Factory map symbols")
    old_map = source["map"]
    current_map = map_source["map"]
    if (current_map.get("group_id") != 96
            or current_map.get("map_id") != 5
            or old_map.get("group_id") != 96
            or old_map.get("map_id") != 5
            or current_map.get("header_address") != old_map.get("header_address")
            or current_map.get("old_events_pointer") != old_map.get("events_after_address")
            or current_map.get("old_objects_pointer") != old_map.get("objects_after_address")
            or current_map.get("old_scripts_pointer") != old_map.get("old_scripts_pointer")
            or current_map.get("object_count_before") != 14
            or old_map.get("object_count_after") != 14
            or current_map.get("object_count_after") != 15
            or current_map.get("old_event_counts") != [14, 10, 0, 7]
            or current_map.get("existing_14_objects_preserved") is not True
            or current_map.get("stage68_shop_local14_preserved") is not True
            or current_map.get("map_scripts_preserved") is not True
            or current_map.get("gift_object", {}).get("local_id") != 15):
        _fail("Stage79 Factory map provenance/count contract mismatch")
    values = [
        _member(source, ("entrypoints", "MegaShop_Probe"), "Mega shop symbols"),
        _member(source, ("entrypoints", "MegaShop_EnsureSave"), "Mega shop symbols"),
        _member(source, ("entrypoints", "MegaShop_GetBalance"), "Mega shop symbols"),
        _member(source, ("entrypoints", "MegaShop_IsUnlocked"), "Mega shop symbols"),
        _member(source, ("entrypoints", "MegaShop_IsClaimed"), "Mega shop symbols"),
        _member(source, ("entrypoints", "MegaShop_PurchaseByIndex"), "Mega shop symbols"),
        _member(source, ("entrypoints", "MegaShop_Open"), "Mega shop symbols"),
        _member(source, ("scripts", "npc_address"), "Mega shop symbols"),
        _member(map_source, ("map", "events_after_address"), "Stage79 Factory map symbols"),
        _member(map_source, ("map", "old_scripts_pointer"), "Stage79 Factory map symbols"),
        _member(source, ("item_tables", "item_data", "new_address"),
                "Mega shop symbols"),
    ]
    return [_integer(value, "Mega shop source value") for value in values], source


def _floette_arguments(
    domain: Mapping[str, Any],
) -> tuple[list[int], dict[str, Any], dict[str, Any]]:
    sources = domain.get("contract_sources")
    if not isinstance(sources, Mapping):
        _fail("Floette contract_sourcesがありません")
    symbols = _fixed_json(sources.get("symbols"), "Floette symbols")
    contract = _fixed_json(sources.get("contract"), "Floette contract")
    abi_names = ("VegaAcqEngine_GetPending", "GetBoxMonDataAt",
                 "GetBoxedMonPtr", "ZeroBoxMonAt")
    for name in abi_names:
        generated = _member(
            symbols, ("linked_acquisition_abi", name, "thumb_entrypoint"),
            "Floette symbols",
        )
        contracted = _member(
            contract, ("acquisition_abi", "entrypoints", name,
                       "thumb_entrypoint"),
            "Floette contract",
        )
        if _integer(generated, f"Floette generated {name}") \
                != _integer(contracted, f"Floette contract {name}"):
            _fail(f"Floette acquisition ABI cross-link不一致: {name}")
    values = [
        _member(symbols, ("entrypoints", "FloetteGift_Probe"), "Floette symbols"),
        _member(symbols, ("entrypoints", "FloetteGift_Claim"), "Floette symbols"),
        _member(symbols, ("entrypoints", "FloetteGift_IsFormObtained"), "Floette symbols"),
        _member(symbols, ("entrypoints", "FloetteGift_IsNationalDexSeen"), "Floette symbols"),
        _member(symbols, ("entrypoints", "FloetteGift_IsNationalDexCaught"), "Floette symbols"),
        _member(symbols, ("scripts", "npc_address"), "Floette symbols"),
        _member(symbols, ("map", "events_after_address"), "Floette symbols"),
        _member(symbols, ("map", "old_scripts_pointer"), "Floette symbols"),
        *[
            _member(symbols,
                    ("linked_acquisition_abi", name, "thumb_entrypoint"),
                    "Floette symbols")
            for name in abi_names
        ],
    ]
    return ([_integer(value, "Floette source value") for value in values],
            symbols, contract)


def _p04_records(domain: Mapping[str, Any]) -> tuple[list[list[int]], dict[str, Any]]:
    mapping = _fixed_json(domain.get("contract_source"), "P04 Mega mapping")
    rows = mapping.get("mappings")
    if not isinstance(rows, list) or len(rows) != 49 \
            or _integer(_member(mapping, ("counts", "mappings"), "P04 mapping"),
                        "P04 count") != 49 \
            or _integer(_member(mapping, ("counts", "forward_entries"),
                                "P04 mapping"), "P04 forward count") != 49 \
            or _integer(_member(mapping, ("counts", "reverse_entries"),
                                "P04 mapping"), "P04 reverse count") != 49:
        _fail("P04 Mega mapping 49 forward/reverse contract不一致")
    records = [
        [
            _integer(row.get("source_species_id"), "P04 base"),
            _integer(row.get("mega_stone_id"), "P04 stone"),
            _integer(row.get("target_species_id"), "P04 target"),
        ]
        for row in rows if isinstance(row, Mapping)
    ]
    if len(records) != 49 \
            or len({(row[0], row[1]) for row in records}) != 49 \
            or len({row[2] for row in records}) != 49:
        _fail("P04 Mega runtime triplesが欠落または重複しています")
    return records, mapping


def _battle_policy_symbols(
    domain: Mapping[str, Any],
) -> tuple[dict[str, int], dict[str, Any]]:
    source = _fixed_json(domain.get("contract_source"),
                         "Battle policy Stage06 metadata")
    runs = source.get("upstream_runs")
    if not isinstance(runs, list) or len(runs) != 2:
        _fail("Battle policy reproducible upstream run count不一致")
    sets = [row.get("integration_symbols")
            for row in runs if isinstance(row, Mapping)]
    if len(sets) != 2 or not isinstance(sets[0], Mapping) or sets[0] != sets[1]:
        _fail("Battle policy two-run symbol identity不一致")
    symbols = {
        name: _integer(sets[0].get(name), f"Battle policy symbol {name}")
        for name in BATTLE_POLICY_SYMBOL_NAMES
    }
    return symbols, source


def _flat_symbol(document: Mapping[str, Any], name: str, label: str) -> int:
    symbols = document.get("symbols")
    if not isinstance(symbols, Mapping) or name not in symbols:
        _fail(f"{label}にsymbol {name}がありません")
    value = symbols[name]
    if isinstance(value, Mapping):
        value = value.get("address")
    return _integer(value, f"{label}.{name}")


def _p05_arguments(
    domain: Mapping[str, Any],
) -> tuple[dict[str, int], dict[str, dict[str, Any]]]:
    sources = domain.get("contract_sources")
    if not isinstance(sources, Mapping) or set(sources) != {
        "stage76_config", "stage76_symbols", "stage77_config", "stage77_symbols",
        "stage78_config", "stage78_symbols", "stage78_contract",
    }:
        _fail("P05 exact Stage76/77/78 contract_sources不一致")
    if {key: dict(sources[key]) for key in EXPECTED_STAGE78_P05_SOURCES} \
            != EXPECTED_STAGE78_P05_SOURCES:
        _fail("P05 Stage78 source identitiesがknown product commitと不一致")
    documents = {
        key: _fixed_json(value, f"P05 {key}")
        for key, value in sources.items()
    }
    stage76_config = documents["stage76_config"]
    stage76_symbols = documents["stage76_symbols"]
    stage77_config = documents["stage77_config"]
    stage77_symbols = documents["stage77_symbols"]
    stage78_config = documents["stage78_config"]
    stage78_symbols = documents["stage78_symbols"]
    stage78_contract = documents["stage78_contract"]
    if stage76_config.get("stage") != 76 or stage76_symbols.get("stage") != 76 \
            or stage77_config.get("stage") != 77 \
            or stage77_symbols.get("stage") != 77 \
            or stage78_config.get("stage") != 78 \
            or stage78_symbols.get("stage") != 78 \
            or stage78_contract.get("stage") != 78:
        _fail("P05 Stage76/77/78 source stage不一致")

    runner_path, runner_raw = _fixed(domain.get("runner"), "P05 runner")
    try:
        runner_text = runner_raw.decode("utf-8")
    except UnicodeError as error:
        _fail(f"P05 runner decode失敗: {error}")
    dispatcher_rows = re.findall(
        r'^\s*\{"([^"]+)", (\d+)U, (\d+)U, (true|false)\},$',
        runner_text,
        re.MULTILINE,
    )
    if tuple(row[0] for row in dispatcher_rows) != P05_DISPATCHER_SUFFIXES \
            or sum(int(row[2]) for row in dispatcher_rows) != 33 \
            or sum(int(row[1]) == 12 for row in dispatcher_rows) != 7 \
            or tuple(row[0] for row in dispatcher_rows if row[3] == "true") \
                != P05_FIFTH_STACK_ARGUMENT_SUFFIXES:
        _fail("P05 runner dispatcher suffix/width/surface contract不一致")
    for name in P05_GLOBAL_ARGUMENT_NAMES:
        if f'"{name}"' not in runner_text:
            _fail(f"P05 runner global argument欠落: {name}")

    stage76_symbol_names = (
        "Stage76_RuntimeProbe", "Stage76_MegaSolRoute",
        "Stage76_QuarterPredictedProtectDamage",
        "Stage76_NormalizePredictedProtectionMove", "Stage76_IsPlannedMaxGuard",
        "Stage76_DirectEffectCanDamagePartner", "Stage76_SelectAIAttackerAbility",
        "Stage76_SpicyPolicyCore", "Stage76_SpicyPathQualifies",
        "Stage76_DispatchMegaSolSolarBeam", "Stage76_BattleScriptMegaSolPopup",
        "Stage76_BattleScriptSolarBeam", "Stage76_EntryAICalcDmg",
        "Stage76_EntryAIScriptPartner", "Stage76_EntryRangeMoveCanHurtPartner",
    )
    values: dict[str, int] = {
        "Stage77_RuntimeProbe": _flat_symbol(
            stage77_symbols, "Stage77_RuntimeProbe", "Stage77 symbols"
        ),
        "gBattleTypeFlags": _integer(_member(
            stage77_config,
            ("suppression_contract", "battle_circus_global",
             "battle_type_flags_address"), "Stage77 config"),
            "Stage77 gBattleTypeFlags",
        ),
        "gBattleCircusFlags": _integer(_member(
            stage77_config,
            ("suppression_contract", "battle_circus_global",
             "circus_flags_address"), "Stage77 config"),
            "Stage77 gBattleCircusFlags",
        ),
        "gStatuses3": _integer(domain.get("g_statuses3_address"),
                               "P05 gStatuses3"),
        "IsAbilitySuppressed": _integer(_member(
            stage77_config, ("parent_abi", "is_ability_suppressed", "address"),
            "Stage77 config"), "Stage77 IsAbilitySuppressed"),
        "Stage76_PayloadStart": _integer(
            stage76_symbols.get("load_address"), "Stage76 payload start"
        ),
        "Stage76_PayloadSize": _integer(
            stage76_symbols.get("payload_size"), "Stage76 payload size"
        ),
    }
    if values["gStatuses3"] != 0x02023D5C:
        _fail("P05 gStatuses3 exact ABI不一致")
    for name in stage76_symbol_names:
        values[name] = _flat_symbol(stage76_symbols, name, "Stage76 symbols")

    pointer_rows = _member(
        stage76_config, ("parent_abi", "pointer_patches"), "Stage76 config"
    )
    stage76_hooks = _member(
        stage76_config, ("parent_abi", "hooks"), "Stage76 config"
    )
    if not isinstance(pointer_rows, list) or len(pointer_rows) != 1 \
            or not isinstance(stage76_hooks, list) or len(stage76_hooks) != 3:
        _fail("P05 Stage76 exact 1 pointer + 3 hook contract不一致")
    pointer = pointer_rows[0]
    if not isinstance(pointer, Mapping) \
            or pointer.get("name") != "SolarBeamEffectScript" \
            or pointer.get("target") != "Stage76_BattleScriptSolarBeam":
        _fail("P05 Stage76 Solar Beam pointer contract不一致")
    values["HOOK_Stage76SolarBeam"] = _integer(
        pointer.get("address"), "Stage76 Solar Beam hook"
    )
    stage76_hook_contract = (
        ("AI_CalcDmg", "HOOK_Stage76AICalcDmg", "Stage76_EntryAICalcDmg"),
        ("AIScript_Partner", "HOOK_Stage76AIScriptPartner",
         "Stage76_EntryAIScriptPartner"),
        ("RangeMoveCanHurtPartner", "HOOK_Stage76RangeMoveCanHurtPartner",
         "Stage76_EntryRangeMoveCanHurtPartner"),
    )
    if tuple((row.get("name"), row.get("target"))
             for row in stage76_hooks if isinstance(row, Mapping)) != tuple(
                 (name, target) for name, _key, target in stage76_hook_contract
             ):
        _fail("P05 Stage76 hook name/target contract不一致")
    for row, (_name, key, _target) in zip(
        stage76_hooks, stage76_hook_contract, strict=True
    ):
        values[key] = _integer(row.get("address"), f"P05 {key}")

    hooks = _member(stage77_config, ("parent_abi", "hooks"), "Stage77 config")
    if not isinstance(hooks, list) or len(hooks) != 29:
        _fail("P05 Stage77 hook count不一致")
    hook_suffixes = tuple(
        str(row.get("target", "")).removeprefix("Stage77_Dispatch")
        for row in hooks if isinstance(row, Mapping)
    )
    if hook_suffixes != P05_DISPATCHER_SUFFIXES:
        _fail("P05 Stage77 hook/runner suffix order不一致")
    for index, (row, suffix) in enumerate(
        zip(hooks, P05_DISPATCHER_SUFFIXES, strict=True)
    ):
        assert isinstance(row, Mapping)
        target = f"Stage77_Dispatch{suffix}"
        width = _integer(row.get("width"), f"P05 hook[{index}].width")
        if row.get("target") != target \
                or width != int(dispatcher_rows[index][1]):
            _fail(f"P05 hook target/width不一致: {suffix}")
        values[f"HOOK_{suffix}"] = _integer(
            row.get("address"), f"P05 hook {suffix}"
        )
        values[f"DISPATCH_{suffix}"] = _flat_symbol(
            stage77_symbols, target, "Stage77 symbols"
        )
        values[f"NORMAL_{suffix}"] = _integer(
            row.get("normal_address"), f"P05 normal {suffix}"
        )
        values[f"SUPPRESSED_{suffix}"] = _integer(
            row.get("suppressed_address"), f"P05 suppressed {suffix}"
        )

    matrix = stage78_contract.get("matrix")
    if not isinstance(matrix, Mapping) \
            or matrix.get("case_count") != 32 \
            or matrix.get("all_pass") is not True \
            or _sha(_stable(matrix)) \
                != "3b0ce8e8a5fa75857971b59091f2a95d73ec5597d90be4756eb9e3717e8383ed" \
            or domain.get("eelevate_matrix_case_count") != 32 \
            or domain.get("eelevate_matrix_sha256") \
                != "3b0ce8e8a5fa75857971b59091f2a95d73ec5597d90be4756eb9e3717e8383ed":
        _fail("P05 Stage78 exact 32-case matrix contract不一致")
    stage78_exports = (
        "Stage78_RuntimeProbe", "Stage78_MapEelevateAbsorber",
        "Stage78_ActiveAbsorberAbility", "Stage78_PartyAbsorberAbility",
        "Stage78_EntryFindMonAbsorberActive",
        "Stage78_EntryFindMonAbsorberParty",
    )
    for name in stage78_exports:
        values[name] = _flat_symbol(stage78_symbols, name, "Stage78 symbols")
    runtime_abi = stage78_symbols.get("runtime_abi")
    if not isinstance(runtime_abi, Mapping):
        _fail("P05 Stage78 runtime ABI欠落")
    globals_abi = runtime_abi.get("globals")
    functions_abi = runtime_abi.get("functions")
    hooks_abi = runtime_abi.get("hooks")
    if not isinstance(globals_abi, Mapping) \
            or not isinstance(functions_abi, Mapping) \
            or not isinstance(hooks_abi, list) or len(hooks_abi) != 2:
        _fail("P05 Stage78 runtime global/function/hook ABI不一致")
    for name in ("gBattlersCount", "gBattleMons", "gAbsentBattlerFlags",
                 "gBattleMoves"):
        values[name] = _integer(globals_abi.get(name), f"Stage78 {name}")
    for name in ("LoadBattlersAndFoes", "GetPredictedAIAbility",
                 "GetAIAbility", "IsValidMovePrediction", "GetMonAbility",
                 "GetBankItemEffect", "GetMonItemEffect", "CheckMonGrounding",
                 "CheckGrounding", "IsTargetAbilityIgnored",
                 "GetMoveTypeSpecial"):
        values[name] = _integer(functions_abi.get(name), f"Stage78 {name}")
    if _integer(globals_abi.get("gBattleTypeFlags"), "Stage78 battle flags") \
            != values["gBattleTypeFlags"] \
            or _integer(globals_abi.get("gBattleCircusFlags"),
                        "Stage78 circus flags") != values["gBattleCircusFlags"] \
            or _integer(functions_abi.get("IsAbilitySuppressed"),
                        "Stage78 suppression") != values["IsAbilitySuppressed"]:
        _fail("P05 Stage77/78 inherited suppression ABI drift")
    exact_hooks = (
        ("FindMonAbsorberActiveAbilityBlock", 0x090A03E4, 16,
         "Stage78_EntryFindMonAbsorberActive", 0x090A03F5),
        ("FindMonAbsorberPartyAbilityBlock", 0x090A0426, 12,
         "Stage78_EntryFindMonAbsorberParty", 0x090A0433),
    )
    for row, expected in zip(hooks_abi, exact_hooks, strict=True):
        if not isinstance(row, Mapping) or (
            row.get("name"), _integer(row.get("site"), "Stage78 hook site"),
            row.get("width"), row.get("entry"),
            _integer(row.get("continuation_thumb"), "Stage78 continuation")
        ) != expected:
            _fail("P05 Stage78 exact hook ABI不一致")
        name, site, _width, entry, continuation = expected
        values[f"HOOK_{name}"] = site
        values[f"CONT_{name}"] = continuation
        if values[entry] != _integer(row.get("entry_address"),
                                     f"Stage78 {entry} address"):
            _fail("P05 Stage78 hook entry/symbol cross-link不一致")
    expected_keys = [*P05_GLOBAL_ARGUMENT_NAMES]
    for suffix in P05_DISPATCHER_SUFFIXES:
        expected_keys.extend(
            f"{prefix}{suffix}"
            for prefix in ("HOOK_", "DISPATCH_", "NORMAL_", "SUPPRESSED_")
        )
    if len(values) != 167 or set(values) != set(expected_keys):
        _fail("P05 exact 167 CLI arguments不一致")
    ordered = {key: values[key] for key in expected_keys}
    identities = {key: dict(value) for key, value in sources.items()}
    identities["runner"] = _identity(
        runner_path.relative_to(ROOT).as_posix(), "P05 runner"
    )
    return ordered, identities


def _validate_domain_contracts(
    config: Mapping[str, Any], *, allow_missing_p02_seed: bool = False,
) -> dict[str, Any]:
    by_id = {str(row["id"]): row for row in config["domains"]}
    audit: dict[str, Any] = {}

    p02 = by_id["p02"]
    if p02.get("kind") != "p02" or p02.get("state") != READY:
        _fail("P02 domainはREADY/p02必須です")
    seed_record = p02.get("seed_save")
    if not isinstance(seed_record, Mapping) \
            or _integer(seed_record.get("size"), "P02 seed size") != 0x20000 \
            or not isinstance(seed_record.get("sha256"), str) \
            or len(seed_record["sha256"]) != 64:
        _fail("P02 seed saveはexact 128 KiB必須です")
    seed_path = _relative_path(seed_record.get("path"), "P02 seed save",
                               must_exist=False)
    seed_present = seed_path.is_file()
    if seed_present:
        _seed_path, seed_raw = _fixed(seed_record, "P02 seed save")
        if len(seed_raw) != 0x20000:
            _fail("P02 seed saveはexact 128 KiB必須です")
    elif not allow_missing_p02_seed:
        _fail("P02 seed saveがありません")
    audit["p02"] = {
        "seed_save": dict(p02["seed_save"]),
        "private_copy_only": True,
        "latest_rom_sha_cli": True,
    }

    mega = by_id["mega_shop"]
    if mega.get("kind") != "mega_shop" or mega.get("state") != READY:
        _fail("Mega shop domainはREADY/mega_shop必須です")
    mega_expected, _mega_symbols = _mega_shop_arguments(mega)
    if mega.get("argument_count") != len(mega_expected) \
            or mega.get("arguments_sha256") != _sha(_stable(mega_expected)):
        _fail("Mega shop derived CLI argument contract不一致")
    audit["mega_shop"] = {
        "contract_source": dict(mega["contract_source"]),
        "map_contract_source": dict(mega["map_contract_source"]),
        "factory_object_count": 15,
        "argument_count": len(mega_expected),
        "arguments_sha256": _sha(_stable(mega_expected)),
        "all_45_purchases_claimed": False,
        "representative_purchase_count": 3,
    }

    floette = by_id["floette"]
    if floette.get("kind") != "floette" or floette.get("state") != READY:
        _fail("Floette domainはREADY/floette必須です")
    floette_sources = floette.get("contract_sources")
    floette_expected, _floette_symbols, _floette_contract = \
        _floette_arguments(floette)
    if floette.get("argument_count") != len(floette_expected) \
            or floette.get("arguments_sha256") != _sha(_stable(floette_expected)):
        _fail("Floette derived CLI argument contract不一致")
    audit["floette"] = {
        "contract_sources": {key: dict(value)
                             for key, value in floette_sources.items()},
        "argument_count": len(floette_expected),
        "arguments_sha256": _sha(_stable(floette_expected)),
        "one_time_gift": True,
    }

    p04 = by_id["p04_mega_runtime"]
    if p04.get("kind") != "mega_runtime_triples" or p04.get("state") != READY:
        _fail("P04 Mega runtime domainはREADY/mega_runtime_triples必須です")
    expected_records, _mapping = _p04_records(p04)
    if p04.get("mapping_count") != 49 \
            or p04.get("records_sha256") != _sha(_stable(expected_records)):
        _fail("P04 Mega runtime derived triple contract不一致")
    audit["p04_mega_runtime"] = {
        "contract_source": dict(p04["contract_source"]),
        "mapping_count": 49,
        "direct_call_count": 245,
        "records_sha256": _sha(_stable(expected_records)),
        "all_49_runtime_not_yet_executed": True,
    }

    policy = by_id["battle_policy"]
    if policy.get("kind") != "battle_policy" or policy.get("state") != READY:
        _fail("Battle policy domainはREADY/battle_policy必須です")
    expected_symbols, _policy_source = _battle_policy_symbols(policy)
    if policy.get("symbol_count") != len(BATTLE_POLICY_SYMBOL_NAMES) \
            or policy.get("symbols_sha256") != _sha(_stable(expected_symbols)):
        _fail("Battle policy derived exact 44-symbol CLI contract不一致")
    audit["battle_policy"] = {
        "contract_source": dict(policy["contract_source"]),
        "symbol_count": len(expected_symbols),
        "two_upstream_runs_equal": True,
        "actual_runtime_deferred_to_heavy_run": True,
    }

    p05 = by_id["p05"]
    if p05.get("state") != READY \
            or p05.get("kind") != "p05_runtime":
        _fail("P05 domainはREADY/p05_runtime必須です")
    p05_arguments, p05_sources = _p05_arguments(p05)
    if p05.get("argument_count") != 167 \
            or p05.get("arguments_sha256") \
                != _sha(_stable(p05_arguments)):
        _fail("P05 derived exact 167-argument contract不一致")
    audit["p05"] = {
        "status": READY,
        "contract_sources": p05_sources,
        "argument_count": 167,
        "arguments_sha256": _sha(_stable(p05_arguments)),
        "dispatcher_count": 29,
        "surface_occurrence_count": 33,
        "full_p05_done": False,
        "eelevate_switch_ai_done": True,
        "eelevate_matrix_case_count": 32,
        "eelevate_matrix_sha256": p05["eelevate_matrix_sha256"],
        "overclaim": False,
    }

    return audit


def build_plan(
    config_path: Path = DEFAULT_CONFIG, *, allow_missing_p02_seed: bool = False,
) -> dict[str, Any]:
    absolute = _config_path(config_path)
    config = _read_json_path(absolute, "Stage79 config")
    _validate_config(config)
    orchestrator_path, _orchestrator_raw = _fixed(
        config.get("orchestrator"), "Stage79 orchestrator"
    )
    if orchestrator_path != Path(__file__).resolve():
        _fail("configが実行中Stage79 orchestrator自身をpinしていません")
    orchestrator = dict(config["orchestrator"])
    _rom_path, rom, input_audit = _validate_input(config)
    rom, input_audit = _validate_runtime_candidate(config, rom, input_audit)
    preimages = _validate_preimages(config, rom)
    p03 = _validate_p03(config, rom)
    domains = [_validate_domain_sources(row) for row in config["domains"]]
    domain_contracts = _validate_domain_contracts(
        config, allow_missing_p02_seed=allow_missing_p02_seed
    )
    config_relative = absolute.relative_to(ROOT.resolve()).as_posix()
    config_identity = _identity(config_relative, "Stage79 config")
    fingerprint_basis = {
        "task": TASK,
        "stage": STAGE,
        "config": config_identity,
        "orchestrator": orchestrator,
        "input": input_audit,
        "domains": domains,
        "domain_contracts": domain_contracts,
        "p03": p03,
    }
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "PREFLIGHT_PASS_NOT_EXECUTED",
        "classification": "LATEST_CUMULATIVE_EXACT_ROM_SEQUENTIAL_RESUMABLE",
        "config": config_identity,
        "orchestrator": orchestrator,
        "input": input_audit,
        "latest_rom_preimages": preimages,
        "p03": p03,
        "domains": [
            {
                "id": row["id"],
                "kind": row["kind"],
                "state": row["state"],
                "timeout_seconds": row["timeout_seconds"],
                "source_audit": audit,
            }
            for row, audit in zip(config["domains"], domains, strict=True)
        ],
        "domain_contracts": domain_contracts,
        "domain_order": list(config["execution"]["domain_order"]),
        "plan_fingerprint": _sha(_stable(fingerprint_basis)),
        "product_rom_patch_bytes": 0,
        "execution_performed": False,
    }


def _compile(domain: Mapping[str, Any], output: Path) -> dict[str, Any]:
    compile_contract = domain["compile"]
    compiler = shutil.which(str(compile_contract.get("compiler", "cc")))
    if compiler is None:
        _fail(f"{domain['id']} compiler欠落")
    runner = _relative_path(domain["runner"]["path"], f"{domain['id']} runner")
    if output.parent.is_symlink() or not output.parent.is_dir():
        _fail(f"{domain['id']} compile出力親directory不正")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.compile-", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    command = [
        compiler,
        *map(str, compile_contract["flags"]),
        str(runner),
        "-o", str(temporary),
        *map(str, compile_contract["link_flags"]),
    ]
    try:
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True,
            check=False, timeout=90,
        )
        if completed.returncode != 0:
            _fail(f"{domain['id']} compile失敗: {completed.stdout}{completed.stderr}")
        if completed.stdout or completed.stderr:
            _fail(f"{domain['id']} compileが予期しない出力を生成しました")
        executable = temporary.read_bytes()
        os.replace(temporary, output)
    except (OSError, subprocess.TimeoutExpired) as error:
        _fail(f"{domain['id']} compile実行失敗: {error}")
    finally:
        if temporary.exists():
            temporary.unlink()
    if output.is_symlink() or output.stat().st_nlink != 1:
        _fail(f"{domain['id']} compile出力isolation不一致")
    return {
        "compiler": compiler,
        "flags": list(compile_contract["flags"]),
        "link_flags": list(compile_contract["link_flags"]),
        "executable_size": len(executable),
        "executable_sha256": _sha(executable),
    }


def compile_check(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    plan = build_plan(config_path)
    config = _read_json_path(_config_path(config_path), "Stage79 config")
    results = []
    with tempfile.TemporaryDirectory(prefix="vega-stage79-compile-check-") as raw:
        temporary = Path(raw)
        for domain in config["domains"]:
            if domain["state"] == PENDING:
                results.append({"id": domain["id"], "status": PENDING})
                continue
            results.append({
                "id": domain["id"], "status": "COMPILE_PASS",
                "compilation": _compile(domain, temporary / domain["id"]),
            })
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "COMPILE_CHECK_PASS_NOT_EXECUTED",
        "plan_fingerprint": plan["plan_fingerprint"],
        "domains": results,
        "mGBA_process_runs": 0,
        "artifacts_written": [],
    }


def _command(domain: Mapping[str, Any], executable: Path, rom: Path,
             rom_sha: str, work: Path, config: Mapping[str, Any]) -> list[str]:
    kind = domain["kind"]
    base = [str(executable), str(rom)]
    if kind == "p02":
        save = work / "p02-private.sav"
        if save.is_symlink() or save.parent.resolve() != work.resolve():
            _fail("P02 private saveがsymlinkです")
        seed, seed_raw = _fixed(domain["seed_save"], "P02 seed save")
        del seed
        _atomic_write(save, seed_raw)
        if save.is_symlink() or save.stat().st_nlink != 1 \
                or _sha(save.read_bytes()) != _sha(seed_raw):
            _fail("P02 private seed copy不一致")
        return [*base, str(save), rom_sha, domain["seed_save"]["sha256"]]
    if kind == "mega_shop":
        arguments, _source = _mega_shop_arguments(domain)
        save = work / "mega-shop.sav"
        if save.is_symlink() or save.parent.resolve() != work.resolve():
            _fail("Mega shop private saveがsymlinkです")
        _atomic_write(save, b"")
        if save.is_symlink() or save.stat().st_nlink != 1:
            _fail("Mega shop private save isolation不一致")
        return [*base, str(save),
                *[hex(_integer(value, "mega shop arg"))
                  for value in arguments]]
    if kind == "floette":
        arguments, _symbols, _contract = _floette_arguments(domain)
        save = work / "floette.sav"
        if save.is_symlink() or save.parent.resolve() != work.resolve():
            _fail("Floette private saveがsymlinkです")
        _atomic_write(save, b"")
        if save.is_symlink() or save.stat().st_nlink != 1:
            _fail("Floette private save isolation不一致")
        return [*base, str(save),
                *[hex(_integer(value, "Floette arg"))
                  for value in arguments]]
    if kind == "p03":
        args = config["p03_contract"]["arguments"]
        return [*base, rom_sha,
                *[f"--{key}={hex(_integer(value, f'P03 {key}'))}"
                  for key, value in sorted(args.items())]]
    if kind == "battle_policy":
        symbols, _source = _battle_policy_symbols(domain)
        return [*base, rom_sha,
                *[f"{key}={hex(_integer(value, f'policy {key}'))}"
                  for key, value in symbols.items()]]
    if kind == "mega_runtime_triples":
        records, _mapping = _p04_records(domain)
        flattened = [str(len(records))]
        for row in records:
            if not isinstance(row, list) or len(row) != 3:
                _fail("P04 mega runtime triple不一致")
            flattened.extend(hex(_integer(value, "P04 triple")) for value in row)
        return [*base, rom_sha, *flattened]
    if kind == "p05_runtime":
        arguments, _sources = _p05_arguments(domain)
        return [
            *base, rom_sha,
            *[f"{key}={hex(value)}" for key, value in arguments.items()],
        ]
    arguments = domain.get("arguments", [])
    if not isinstance(arguments, list):
        _fail(f"{domain['id']} generic arguments不一致")
    return [*base, rom_sha, *map(str, arguments)]


def _exact_true_map(value: Any, keys: Sequence[str]) -> bool:
    return isinstance(value, Mapping) \
        and set(value) == set(keys) \
        and all(value[key] is True for key in keys)


def _exact_key_map(value: Any, keys: Sequence[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == set(keys)


def _validate_result(domain: Mapping[str, Any], result: Mapping[str, Any],
                     rom_sha: str) -> None:
    kind = domain["kind"]
    expected_top = RESULT_TOP_LEVEL_KEYS.get(kind)
    if expected_top is None or set(result) != expected_top:
        _fail(f"{domain['id']} runner top-level field集合不一致")
    if type(result.get("schema_version")) is not int \
            or result.get("schema_version") != 1 \
            or result.get("status") != "PASS":
        _fail(f"{domain['id']} runner top-level result不一致")
    if type(result.get("warnings_errors")) is not int \
            or result.get("warnings_errors") != 0:
        _fail(f"{domain['id']} mGBA warnings/errors欠落または非0")
    if "rom_sha256" in result and result.get("rom_sha256") != rom_sha:
        _fail(f"{domain['id']} runner ROM identity不一致")
    if kind == "p02":
        direct = result.get("direct_conditions")
        expected_direct_keys = {
            "level", "friendship", "known_move", "trade", "night_form",
            "level_held_item_six",
        }
        held = direct.get("level_held_item_six") \
            if isinstance(direct, Mapping) else None
        expected_held = {
            "species_count": 6,
            "conditional_selected": 6,
            "conditional_item_consumed": 6,
            "below_level_rejected": 6,
            "wrong_or_missing_item_regular": 12,
            "hidden_ability_preserved": 24,
            "payload_pc_seen": True,
        }
        if result.get("classification") \
                != "STAGE71_EXACT_ROM_NORMAL_INPUT_AND_FRESH_CORE" \
                or result.get("known_good_seed_sha256") \
                    != domain["seed_save"]["sha256"] \
                or result.get("boot_route") \
                    != "NORMAL_TITLE_CONTINUE_PINNED_SAVE" \
                or result.get("initial_normal_continue_field") is not True \
                or result.get("fixture_replacement_after_field") is not True \
                or result.get("temporary_save_only") is not True \
                or not isinstance(direct, Mapping) \
                or set(direct) != expected_direct_keys \
                or any(direct[key] is not True for key in (
                    "level", "friendship", "known_move", "trade",
                    "night_form",
                )) \
                or held != expected_held:
            _fail("P02 cumulative runtime result不一致")
        p02_sections = {
            "normal_evolution_cancel": (
                "normal_bag_party_input", "scene_callbacks_seen",
                "physical_b_cancel", "source_retained", "four_moves_retained",
                "ability_slot_retained",
            ),
            "normal_evolution_success": (
                "normal_bag_party_input", "scene_callbacks_seen",
                "target_applied", "four_moves_retained",
                "ability_slot_retained", "ability_matches_slot",
            ),
            "conditional_form_success": (
                "normal_bag_party_input", "scene_callbacks_seen",
                "exact_form_applied", "condition_item_consumed",
                "four_moves_retained", "hidden_ability_preserved",
                "ability_matches_hidden",
            ),
            "bag_item_use": (
                "normal_start_bag_party_input", "scene_callbacks_seen",
                "target_applied", "bag_item_consumed", "four_moves_retained",
            ),
            "bag_item_missing": (
                "normal_start_bag_input_attempted", "item_absent",
                "party_not_opened_for_item", "species_unchanged",
            ),
            "save_reload": (
                "stock_save_twice", "original_core_destroyed",
                "fresh_core_created", "stock_load_succeeded",
                "normal_continue_load_succeeded", "exact_form_reloaded",
                "four_moves_reloaded", "condition_item_still_consumed",
                "hidden_ability_reloaded", "ability_matches_hidden",
            ),
        }
        for key, keys in p02_sections.items():
            if not _exact_true_map(result.get(key), keys):
                _fail(f"P02 {key} acceptance field/value不一致")
    elif kind == "mega_shop":
        mega_checks = (
            "physical_npc_script_graph_to_entrypoint",
            "item_consumer_boundaries_999_1023_1024_1043_1044",
            "name_hold_effect_and_is_mega_stone_consumers",
            "probe_and_save_init", "mega_ring_580_gate",
            "insufficient_bp_no_mutation", "bag_full_no_mutation",
            "index_0_item_999_price_16", "index_22_item_1021_price_16",
            "index_44_item_1043_price_16", "claim_flags_14a0_14b6_14cc",
            "fresh_core_normal_save_reload", "fresh_core_once_rejected",
        )
        if result.get("stage") != 68 \
                or not _exact_true_map(result.get("checks"), mega_checks) \
                or result.get("representative_indices") != [0, 22, 44] \
                or result.get("representative_item_ids") != [999, 1021, 1043] \
                or result.get("representative_claim_flags") \
                    != [5280, 5302, 5324] \
                or result.get("accepted_item_boundary_ids") \
                    != [999, 1023, 1024, 1043] \
                or result.get("first_rejected_item_id") != 1044 \
                or result.get("hold_effect") != 73 \
                or result.get("price_bp") != 16 \
                or result.get("initial_bp") != 100 \
                or result.get("final_bp") != 52 \
                or _integer(result.get("bag_full_capacity"),
                            "Mega shop bag capacity") <= 0 \
                or result.get("core_instances") != 2 \
                or result.get("process_runs") != 1 \
                or _integer(result.get("framebuffer_transitions"),
                            "Mega shop framebuffer transitions") <= 0 \
                or result.get("state_fixture") \
                    != "PRODUCTION_ROM_FUNCTIONS_ONLY" \
                or result.get("retained_artifacts") != []:
            _fail("Mega shop cumulative runtime result不一致")
    elif kind == "floette":
        floette_checks = (
            "physical_npc_script_graph_to_entrypoint", "mega_ring_580_gate",
            "party_delivery_species1029_level50",
            "full_party_pc_delivery_species1029_level50",
            "pc_level50_create_mon_experience_identity",
            "party_and_pc_full_unclaimed", "claim_flag_14cd",
            "national670_collection_bit850",
            "standard_save_fresh_core_reload", "fresh_core_once_rejected",
        )
        pc_destination = result.get("pc_destination")
        pc_box = _integer(
            pc_destination.get("box") if isinstance(pc_destination, Mapping)
            else None, "Floette PC destination box",
        )
        pc_position = _integer(
            pc_destination.get("position")
            if isinstance(pc_destination, Mapping) else None,
            "Floette PC destination position",
        )
        if result.get("stage") != 69 \
                or result.get("task") != "USER-MODERNIZATION-FLOETTE-ETERNAL-GIFT" \
                or not _exact_true_map(result.get("checks"), floette_checks) \
                or not isinstance(pc_destination, Mapping) \
                or set(pc_destination) != {"box", "position"} \
                or not 0 <= pc_box < 14 \
                or not 0 <= pc_position < 30 \
                or result.get("core_instances") != 2 \
                or result.get("process_runs") != 1 \
                or _integer(result.get("framebuffer_transitions"),
                            "Floette framebuffer transitions") <= 0 \
                or result.get("state_fixture") \
                    != "PRODUCTION_ROM_FUNCTIONS_ONLY" \
                or result.get("retained_artifacts") != []:
            _fail("Floette cumulative runtime result不一致")
    elif kind == "p03":
        expected_checks = {
            "stage67_level_evolution_tutor_egg": True,
            "stage73_exact_alias_shared_egg_reminder_rotom": True,
            "stage74_machine_tutor_paging_cancel_failure_capacity": True,
            "stage75_species1670_egg_evolution_route_owner": True,
            "all_known_terminal_mode_reset_source_pinned": True,
        }
        if result.get("classification") \
                != "LATEST_CUMULATIVE_P03_REPRESENTATIVE_DIRECT_CALL" \
                or result.get("read_only") is not True \
                or result.get("warnings_errors") != 0 \
                or result.get("process_runs") != 1 \
                or result.get("checks") != expected_checks \
                or result.get("full_p03_acceptance") is not False \
                or result.get("scheduler_e2e") is not False \
                or result.get("breeding_e2e") is not False \
                or result.get("save_reload_e2e") is not False \
                or result.get("artifacts_written") != []:
            _fail("P03 cumulative representative result不一致")
    elif kind == "battle_policy":
        stat_inputs = result.get("stat_inputs")
        exp_candy = result.get("exp_candy")
        trainer_build = result.get("trainer_build")
        mechanics = result.get("mechanics")
        facility = result.get("facility")
        mirage = result.get("mirage")
        raid = result.get("raid")
        facility_keys = (
            "formats", "rules", "matrix_cases", "frontier_flag",
            "persistent_effects_denied", "capture_denied",
            "scheduler_faint_end", "experience_before", "experience_after",
            "held_item_before", "held_item_after", "outcome", "enemy_fainted",
            "runtime_cleaned", "rental_generation",
        )
        mirage_expected = {
            "virtual_item": 900,
            "pending_configure_actual_battle": True,
            "owner": "opponent_party_slot_0",
            "opponent_battle_mon_virtualized": True,
            "opponent_original_restored_each_exit": True,
            "player_party_unchanged_each_exit": True,
            "battle_mon_virtualized": True,
            "consume_swap_mutation": True,
            "exit_paths": 7,
            "party_original_restored_each_exit": True,
            "virtual_or_mutated_item_leaked_to_bag": False,
            "leaked_to_bag": False,
        }
        raid_keys = (
            "high_difficulty_policy", "pending_configure_actual_battle",
            "existing_three_controller_ui_initialized", "boss_side",
            "partner_mask", "shield_boundary_max", "initial_shields",
            "shield_breaks", "controller_turns", "player_pp_before",
            "player_pp_after", "boss_fainted", "catch_phase_seen",
            "capture_action", "bag_opened", "ball_consumed",
            "pc_storage_pointer_dynamic", "full_party_pc_routed", "pc_box_id",
            "pc_box_position", "pc_captured_species",
            "party_count_after_capture", "party_species_unchanged",
            "stock_pc_box_stride_80", "adjacent_pc_slot_unchanged", "outcome",
            "runtime_cleaned", "policy_state_cleaned", "normal_wild_no_leak",
            "normal_trainer_no_leak", "partner_spread_moves_preserved",
            "turn_limit_checked", "turn_limit_scheduler_end",
            "capture_allowed_path", "capture_denied_path",
            "contract_unit_direct_calls", "cleanup",
            "raid_state_completion_scheduler_e2e",
        )
        if result.get("fixture") != "t06_battle_policy_integration_v1" \
                or result.get("fixed_rtc_unix") != 946684800 \
                or result.get("read_only") is not True \
                or result.get("boot_trace_segments") != 233 \
                or result.get("non_e2e_routes") != [] \
                or result.get("unreached_routes") != [] \
                or result.get("artifacts_written") != [] \
                or _integer(result.get("direct_calls"),
                            "battle policy direct calls") <= 200 \
                or _integer(result.get("direct_call_instructions"),
                            "battle policy direct-call instructions") \
                    <= _integer(result.get("direct_calls"),
                                "battle policy direct calls") \
                or result.get("payload_calls") != result.get("direct_calls") \
                or result.get("actual_battle_setups") != 41 \
                or stat_inputs != {
                    "exp_share_off_participant_only": True,
                    "exp_share_on_unparticipated": True,
                    "mint_nature": 6, "ability_slot": 2,
                    "hyper_trained_iv": 31,
                } \
                or not _exact_true_map(exp_candy, (
                    "selected_target_only", "zero_no_effect_not_consumed",
                    "cap_clamped", "at_cap_not_consumed",
                )) \
                or trainer_build != {
                    "fully_specified": True, "unspecified_identity": True,
                    "ev_total": 510,
                } \
                or mechanics != {
                    "modes": ["MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL"],
                    "side_wide_exclusive": True, "one_use": True,
                    "cross_mode_exclusive": True, "cleanup": True,
                } \
                or not _exact_key_map(facility, facility_keys) \
                or mirage != mirage_expected \
                or not _exact_key_map(raid, raid_keys):
            _fail("battle policy cumulative result不一致")
        rental = facility["rental_generation"]
        if (facility["formats"], facility["rules"],
                facility["matrix_cases"], facility["frontier_flag"],
                facility["persistent_effects_denied"],
                facility["capture_denied"], facility["scheduler_faint_end"],
                facility["enemy_fainted"], facility["runtime_cleaned"]) \
                != (3, 8, 24, True, 7, True, True, True, True) \
                or facility["experience_after"] != facility["experience_before"] \
                or facility["held_item_before"] != 41 \
                or facility["held_item_after"] != 41 \
                or facility["outcome"] != 1 \
                or not _exact_key_map(
                    rental, ("bounded_call", "party_count", "species")
                ) \
                or rental["bounded_call"] is not True \
                or not 3 <= rental["party_count"] <= 6 \
                or not isinstance(rental["species"], list) \
                or len(rental["species"]) != 6 \
                or sum(species != 0 for species in rental["species"]) \
                    != rental["party_count"] \
                or any(type(species) is not int or not 0 <= species <= 411
                       for species in rental["species"]):
            _fail("battle policy facility evidence不一致")
        raid_true_keys = set(raid_keys) - {
            "boss_side", "partner_mask", "shield_boundary_max",
            "initial_shields", "shield_breaks", "controller_turns",
            "player_pp_before", "player_pp_after", "capture_action",
            "pc_box_id", "pc_box_position", "pc_captured_species",
            "party_count_after_capture", "outcome",
        }
        if raid["boss_side"] != 1 or raid["partner_mask"] != 6 \
                or raid["shield_boundary_max"] != 5 \
                or raid["initial_shields"] != 5 \
                or raid["shield_breaks"] != 5 \
                or raid["controller_turns"] <= 0 \
                or raid["player_pp_before"] <= raid["player_pp_after"] \
                or raid["capture_action"] != 1 \
                or raid["pc_box_id"] != 0 \
                or raid["pc_box_position"] != 0 \
                or raid["pc_captured_species"] != 150 \
                or raid["party_count_after_capture"] != 6 \
                or raid["outcome"] != 7 \
                or any(raid[key] is not True for key in raid_true_keys):
            _fail("battle policy raid evidence不一致")
    elif kind == "mega_runtime_triples":
        records, _mapping = _p04_records(domain)
        count = len(records)
        if result.get("classification") != "DIRECT_CALL_BOUNDED" \
                or result.get("read_only") is not True \
                or result.get("mapping_count") != count \
                or result.get("correct_stone_matches") != count \
                or result.get("stone_less_rejections") != count \
                or result.get("mega_species_recognized") != count \
                or result.get("base_species_rejected_as_mega") != count \
                or result.get("reversions_to_base") != count \
                or result.get("direct_calls") != count * 5 \
                or _integer(result.get("instructions"),
                            "P04 direct-call instructions") <= 0 \
                or result.get("symbols") != {
                    "GetMegaSpecies": "0x09114CF0",
                    "TryRevertMega": "0x09114F74",
                    "IsMegaSpecies": "0x09115098",
                } \
                or result.get("payload_pc_seen") is not True \
                or result.get("artifacts_written") != []:
            _fail("P04 exact Mega runtime result不一致")
    elif kind == "p05_runtime":
        if result.get("classification") \
                != "STAGE78_P05_RUNTIME_DIRECT_CALL" \
                or result.get("read_only") is not True \
                or result.get("warnings_errors") != 0 \
                or result.get("dispatcher_count") != 29 \
                or result.get("ability_surface_occurrence_count") != 33 \
                or result.get("normal_delegations") != 29 \
                or result.get("circus_original_delegations") != 29 \
                or result.get("predicate_truth_table_pass") is not True \
                or result.get("stage76_helpers_preserved") is not True \
                or result.get("suppression_paths_pass") is not True \
                or result.get("stage76_megasol_production_dispatch_pass") \
                    is not True \
                or result.get("stage76_suppression_link_count") != 3 \
                or result.get("dispatcher_observations") != 203 \
                or _integer(result.get("direct_calls"),
                            "P05 direct calls") <= 0 \
                or _integer(result.get("dispatcher_instructions"),
                            "P05 dispatcher instructions") <= 0 \
                or _integer(result.get("direct_call_instructions"),
                            "P05 direct-call instructions") <= 0 \
                or result.get("fifth_stack_argument_observations") != 21 \
                or result.get("fifth_stack_arguments_preserved") is not True \
                or result.get("eelevate_switch_ai_done") is not True \
                or result.get("eelevate_matrix_case_count") != 32 \
                or result.get("eelevate_matrix_observations") != 32 \
                or result.get("eelevate_matrix_sha256") \
                    != domain.get("eelevate_matrix_sha256") \
                or result.get("eelevate_pure_helper_pass") is not True \
                or result.get("eelevate_active_helper_pass") is not True \
                or result.get("eelevate_party_helper_pass") is not True \
                or result.get("eelevate_active_hook_route_pass") is not True \
                or result.get("eelevate_party_hook_route_pass") is not True \
                or result.get("eelevate_active_hook_observations") != 13 \
                or result.get("eelevate_party_hook_observations") != 13 \
                or _integer(result.get("eelevate_stub_calls_observed"),
                            "P05 Eelevate stub observations") <= 0 \
                or result.get("eelevate_register_continuation_abi_pass") \
                    is not True \
                or result.get("full_p05_acceptance") is not False \
                or result.get("scheduler_e2e") is not False \
                or result.get("artifacts_written") != []:
            _fail("P05 Stage78 bounded runtime result不一致")
    else:
        expected = domain.get("expected_result", {})
        if not isinstance(expected, Mapping):
            _fail(f"{domain['id']} expected_result不一致")
        for key, value in expected.items():
            if result.get(key) != value:
                _fail(f"{domain['id']} result.{key}不一致")


def _safe_write_parent(path: Path) -> Path:
    if not path.is_absolute():
        _fail("書込先はworkspace絶対path必須です")
    try:
        relative = path.parent.relative_to(ROOT)
    except ValueError:
        _fail("書込先がworkspace外です")
    current = ROOT
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            _fail("書込先parent componentがsymlinkです")
        try:
            current.mkdir(exist_ok=True)
        except OSError as error:
            _fail(f"書込先parentを作成できません: {error}")
        if not current.is_dir():
            _fail("書込先parent componentがdirectoryではありません")
    try:
        current.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
    except (OSError, ValueError) as error:
        _fail(f"書込先parentがworkspace外です: {error}")
    return current


def _atomic_write(path: Path, raw: bytes) -> None:
    parent = _safe_write_parent(path)
    if path.is_symlink() or path.is_dir():
        _fail("atomic書込先leafがsymlinkまたはdirectoryです")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if path.is_symlink() or path.stat().st_nlink != 1:
            _fail("atomic書込先leaf isolation不一致")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _expected_command_argument_count(domain: Mapping[str, Any]) -> int:
    kind = domain["kind"]
    if kind == "p02":
        return 5
    if kind in {"mega_shop", "floette"}:
        return 3 + _integer(domain.get("argument_count"),
                            f"{domain['id']} argument count")
    if kind == "p03":
        return 3 + _integer(domain.get("argument_count"), "P03 argument count")
    if kind == "mega_runtime_triples":
        return 4 + 3 * _integer(domain.get("mapping_count"),
                                "P04 mapping count")
    if kind == "battle_policy":
        return 3 + _integer(domain.get("symbol_count"),
                            "Battle policy symbol count")
    if kind == "p05_runtime":
        return 3 + _integer(domain.get("argument_count"), "P05 argument count")
    arguments = domain.get("arguments")
    if not isinstance(arguments, list):
        _fail(f"{domain['id']} generic argument count不一致")
    return 3 + len(arguments)


def _validate_result_record(
    domain: Mapping[str, Any], record: Mapping[str, Any], fingerprint: str,
    input_rom: Mapping[str, Any], rom_sha: str,
) -> None:
    expected_record_keys = {
        "schema_version", "task", "stage", "id", "status",
        "plan_fingerprint", "input_rom", "runner", "compilation",
        "command_argument_count", "stderr_sha256", "runner_result",
    }
    if set(record) != expected_record_keys:
        _fail(f"{domain['id']} cached result field集合不一致")
    expected_top = {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "id": domain["id"],
        "status": "PASS",
        "plan_fingerprint": fingerprint,
        "input_rom": dict(input_rom),
        "runner": dict(domain["runner"]),
    }
    for key, value in expected_top.items():
        if record.get(key) != value:
            _fail(f"{domain['id']} cached result.{key} identity不一致")
    compilation = record.get("compilation")
    if not isinstance(compilation, Mapping) \
            or set(compilation) != {
                "compiler", "flags", "link_flags", "executable_size",
                "executable_sha256",
            } \
            or not isinstance(compilation.get("compiler"), str) \
            or not compilation["compiler"] \
            or compilation.get("flags") != domain["compile"]["flags"] \
            or compilation.get("link_flags") != domain["compile"]["link_flags"] \
            or _integer(compilation.get("executable_size"),
                        f"{domain['id']} executable size") <= 0 \
            or not isinstance(compilation.get("executable_sha256"), str) \
            or len(compilation["executable_sha256"]) != 64:
        _fail(f"{domain['id']} cached compilation identity不一致")
    if not isinstance(record.get("stderr_sha256"), str) \
            or len(record["stderr_sha256"]) != 64:
        _fail(f"{domain['id']} cached stderr identity不一致")
    if record.get("command_argument_count") \
            != _expected_command_argument_count(domain):
        _fail(f"{domain['id']} cached command argument count不一致")
    runner_result = record.get("runner_result")
    if not isinstance(runner_result, Mapping):
        _fail(f"{domain['id']} cached runner result不一致")
    _validate_result(domain, runner_result, rom_sha)


def _ready_gate(plan: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task": TASK,
        "stage": STAGE,
        "status": "READY_NOT_RUN",
        "classification": "LATEST_CUMULATIVE_EXACT_ROM_SEQUENTIAL_RESUMABLE",
        "config": plan["config"],
        "orchestrator": plan["orchestrator"],
        "input": plan["input"],
        "plan_fingerprint": plan["plan_fingerprint"],
        "domain_order": plan["domain_order"],
        "domains": [
            {
                "id": row["id"],
                "status": "NOT_RUN" if row["state"] == READY else PENDING,
                "pending_reason": row.get("pending_reason"),
                "runner": dict(row["runner"])
                    if row["state"] == READY else None,
            }
            for row in config["domains"]
        ],
        "execution": {
            "fresh_mGBA_process_runs": 0,
            "cached_domain_results_reused": 0,
            "evidenced_domain_runs": 0,
            "individual_results_written_this_invocation": 0,
            "checkpoint_written": False,
            "resume_supported": True,
            "explicit_heavy_run_required": True,
        },
        "claims": {
            "product_rom_patched": False,
            "full_p03_done": False,
            "full_p05_done": False,
            "release_ready": False,
            "physical_all_menu_paths_e2e": False,
            "link_runtime_e2e": False,
        },
        "not_yet_executed": True,
        "artifacts_written": [config["execution"]["runtime_gate"]],
    }


def prepare(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    plan = build_plan(config_path)
    config = _read_json_path(_config_path(config_path), "Stage79 config")
    gate_path = ROOT / config["execution"]["runtime_gate"]
    _safe_write_parent(gate_path)
    if gate_path.is_symlink() or gate_path.is_dir():
        _fail("Stage79 runtime gate leafがsymlinkまたはdirectoryです")
    expected = _ready_gate(plan, config)
    if gate_path.exists():
        current = _read_json_path(gate_path, "Stage79 runtime gate")
        if current != expected:
            execution = current.get("execution")
            replaceable = current.get("status") == "READY_NOT_RUN" \
                and current.get("not_yet_executed") is True \
                and isinstance(execution, Mapping) \
                and execution.get("fresh_mGBA_process_runs",
                                  execution.get("mGBA_process_runs")) == 0 \
                and execution.get("cached_domain_results_reused", 0) == 0 \
                and execution.get("evidenced_domain_runs", 0) == 0 \
                and execution.get(
                    "individual_results_written_this_invocation",
                    execution.get("individual_results_written")) == 0
            if not replaceable:
                _fail("実行済みまたは不正なruntime gateをprepareで上書きできません")
            _atomic_write(gate_path, _stable(expected))
        return expected
    _atomic_write(gate_path, _stable(expected))
    return expected


def _state_directory(config: Mapping[str, Any], fingerprint: str) -> Path:
    relative = Path(str(config["execution"]["state_root"])) / fingerprint
    current = ROOT
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            _fail("resume state path componentがsymlinkです")
    resolved = current.resolve()
    try:
        resolved.relative_to(ROOT.resolve() / ".local")
    except ValueError:
        _fail("resume state directoryが.local外です")
    return resolved


def _ensure_state_subdirectory(path: Path, state: Path, label: str) -> Path:
    if path.is_symlink():
        _fail(f"{label}がsymlinkです")
    try:
        path.mkdir(parents=True, exist_ok=True)
        resolved = path.resolve(strict=True)
        resolved.relative_to(state.resolve(strict=True))
    except (OSError, ValueError) as error:
        _fail(f"{label}がresume state外または作成不能です: {error}")
    if path.is_symlink() or not resolved.is_dir():
        _fail(f"{label}が通常directoryではありません")
    return resolved


def _path_content_identity(path: Path, label: str) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file():
            _fail(f"{label}が通常fileではありません")
        raw = path.read_bytes()
    except OSError as error:
        _fail(f"{label}を読めません: {error}")
    return {"size": len(raw), "sha256": _sha(raw)}


def _ensure_private_rom(
    source: Path, state: Path, expected: Mapping[str, Any],
) -> Path:
    input_directory = _ensure_state_subdirectory(
        state / "input", state, "private ROM directory"
    )
    private = input_directory / "stage78-private.gba"
    expected_content = {
        "size": _integer(expected.get("size"), "private ROM expected size"),
        "sha256": expected.get("sha256"),
    }
    valid = private.is_file() and not private.is_symlink() \
        and _path_content_identity(private, "private cumulative ROM") \
            == expected_content
    if valid:
        try:
            valid = not os.path.samefile(source, private) \
                and private.stat().st_nlink == 1
        except OSError:
            valid = False
    if not valid:
        try:
            source_raw = source.read_bytes()
        except OSError as error:
            _fail(f"cumulative source ROMをcopyできません: {error}")
        if {"size": len(source_raw), "sha256": _sha(source_raw)} \
                != expected_content:
            _fail("private copy前のcumulative source ROM identity不一致")
        _atomic_write(private, source_raw)
    try:
        private.chmod(0o444)
    except OSError as error:
        _fail(f"private cumulative ROMをread-only化できません: {error}")
    if _path_content_identity(private, "private cumulative ROM") \
            != expected_content \
            or os.path.samefile(source, private) \
            or private.stat().st_nlink != 1:
        _fail("private cumulative ROM copy identity不一致")
    return private


def _validate_runtime_roms_unchanged(
    source: Path, private: Path, expected: Mapping[str, Any],
) -> None:
    expected_content = {
        "size": _integer(expected.get("size"), "runtime ROM expected size"),
        "sha256": expected.get("sha256"),
    }
    if _path_content_identity(source, "cumulative source ROM") \
            != expected_content:
        _fail("mGBA subprocess経路でcumulative source ROMが変更されました")
    if _path_content_identity(private, "private cumulative ROM") \
            != expected_content:
        _fail("mGBA subprocess経路でprivate cumulative ROMが変更されました")
    try:
        if os.path.samefile(source, private) or private.stat().st_nlink != 1:
            _fail("mGBA subprocess経路でprivate ROM isolationが失われました")
    except OSError as error:
        _fail(f"mGBA subprocess後のprivate ROM isolation確認失敗: {error}")


def _validate_resume_checkpoint(
    checkpoint: Mapping[str, Any], plan: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    expected_keys = {
        "schema_version", "task", "stage", "status", "plan_fingerprint",
        "input", "domain_order", "domains",
    }
    if set(checkpoint) != expected_keys \
            or (checkpoint.get("schema_version"), checkpoint.get("task"),
                checkpoint.get("stage")) != (1, TASK, STAGE) \
            or checkpoint.get("status") not in {
                "IN_PROGRESS", "PASS_WITH_DECLARED_LIMITS",
            } \
            or checkpoint.get("plan_fingerprint") \
                != plan["plan_fingerprint"] \
            or checkpoint.get("input") != plan["input"] \
            or checkpoint.get("domain_order") != plan["domain_order"]:
        _fail("resume checkpoint top-level identity不一致")
    states = checkpoint.get("domains")
    if not isinstance(states, Mapping) \
            or set(states) != set(plan["domain_order"]):
        _fail("resume checkpoint domain集合不一致")
    reached_not_run = False
    for domain in config["domains"]:
        domain_id = domain["id"]
        actual = states.get(domain_id)
        if domain["state"] == PENDING:
            if actual != PENDING:
                _fail(f"resume checkpoint pending state不一致: {domain_id}")
            continue
        if actual not in {"NOT_RUN", "PASS"}:
            _fail(f"resume checkpoint state不一致: {domain_id}")
        if actual == "NOT_RUN":
            reached_not_run = True
        elif reached_not_run:
            _fail("resume checkpoint PASSがsequential prefixではありません")
    if checkpoint["status"] == "PASS_WITH_DECLARED_LIMITS" \
            and any(
                states[domain["id"]] != "PASS"
                for domain in config["domains"] if domain["state"] == READY
            ):
        _fail("completed resume checkpointに未実行domainがあります")


def run(
    config_path: Path = DEFAULT_CONFIG, *, heavy_confirmed: bool = False,
) -> dict[str, Any]:
    if not heavy_confirmed:
        _fail("runにはprogrammatic heavy_confirmed=Trueも必要です")
    plan = build_plan(config_path)
    config = _read_json_path(_config_path(config_path), "Stage79 config")
    rom_path = _relative_path(plan["input"]["rom"]["path"], "cumulative ROM")
    rom_before = _identity(plan["input"]["rom"]["path"], "cumulative ROM")
    fingerprint = plan["plan_fingerprint"]
    state = _state_directory(config, fingerprint)
    if state.is_symlink():
        _fail("resume state directoryがsymlinkです")
    state.mkdir(parents=True, exist_ok=True)
    state = _ensure_state_subdirectory(state, state, "resume state directory")
    results_directory = _ensure_state_subdirectory(
        state / "results", state, "resume results directory"
    )
    work_directory = _ensure_state_subdirectory(
        state / "work", state, "resume work directory"
    )
    private_rom = _ensure_private_rom(rom_path, state, rom_before)
    checkpoint_path = state / "checkpoint.json"
    if checkpoint_path.is_symlink():
        _fail("resume checkpointがsymlinkです")
    checkpoint: dict[str, Any]
    if checkpoint_path.is_file():
        checkpoint = _read_json_path(checkpoint_path, "Stage79 resume checkpoint")
        _validate_resume_checkpoint(checkpoint, plan, config)
    else:
        checkpoint = {
            "schema_version": 1, "task": TASK, "stage": STAGE,
            "status": "IN_PROGRESS", "plan_fingerprint": fingerprint,
            "input": plan["input"], "domain_order": plan["domain_order"],
            "domains": {
                row["id"]: ("NOT_RUN" if row["state"] == READY else PENDING)
                for row in config["domains"]
            },
        }
        _atomic_write(checkpoint_path, _stable(checkpoint))

    results: list[dict[str, Any]] = []
    fresh_run_count = 0
    cached_result_count = 0
    for domain in config["domains"]:
        domain_id = domain["id"]
        result_path = results_directory / f"{domain_id}.json"
        if result_path.is_symlink():
            _fail(f"{domain_id} resume resultがsymlinkです")
        if domain["state"] == PENDING:
            results.append({
                "id": domain_id, "status": PENDING,
                "reason": domain["pending_reason"],
            })
            continue
        if checkpoint["domains"].get(domain_id) == "PASS" and result_path.is_file():
            record = _read_json_path(result_path, f"{domain_id} cached result")
            _validate_result_record(
                domain, record, fingerprint, rom_before, rom_before["sha256"]
            )
            results.append(record)
            cached_result_count += 1
            continue

        domain_work = _ensure_state_subdirectory(
            work_directory / domain_id, state, f"{domain_id} work directory"
        )
        executable = domain_work / "runner"
        if executable.is_symlink():
            _fail(f"{domain_id} executableがsymlinkです")
        compilation = _compile(domain, executable)
        command = _command(domain, executable, private_rom, rom_before["sha256"],
                           domain_work, config)
        try:
            completed = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, check=False,
                timeout=_integer(domain["timeout_seconds"], f"{domain_id} timeout"),
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            _validate_runtime_roms_unchanged(
                rom_path, private_rom, rom_before
            )
            _fail(f"{domain_id} mGBA実行失敗: {error}")
        _validate_runtime_roms_unchanged(rom_path, private_rom, rom_before)
        if completed.returncode != 0:
            _fail(f"{domain_id} mGBA失敗({completed.returncode}): "
                  f"{(completed.stderr or completed.stdout).strip()}")
        try:
            runner_result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            _fail(f"{domain_id} stdout JSON不一致: {error}")
        if not isinstance(runner_result, dict):
            _fail(f"{domain_id} stdout rootがobjectではありません")
        _validate_result(domain, runner_result, rom_before["sha256"])
        fresh_run_count += 1
        record = {
            "schema_version": 1, "task": TASK, "stage": STAGE,
            "id": domain_id, "status": "PASS",
            "plan_fingerprint": fingerprint,
            "input_rom": rom_before,
            "runner": dict(domain["runner"]),
            "compilation": compilation,
            "command_argument_count": len(command),
            "stderr_sha256": _sha(completed.stderr.encode("utf-8")),
            "runner_result": runner_result,
        }
        _atomic_write(result_path, _stable(record))
        checkpoint["domains"][domain_id] = "PASS"
        _atomic_write(checkpoint_path, _stable(checkpoint))
        results.append(record)

    ready_ids = [row["id"] for row in config["domains"] if row["state"] == READY]
    if any(checkpoint["domains"].get(domain_id) != "PASS" for domain_id in ready_ids):
        _fail("READY domainが全件PASSしていません")
    checkpoint["status"] = "PASS_WITH_DECLARED_LIMITS"
    _atomic_write(checkpoint_path, _stable(checkpoint))
    after = _identity(plan["input"]["rom"]["path"], "cumulative ROM")
    if after != rom_before:
        _fail("累積mGBA setが製品ROMを変更しました")
    _validate_runtime_roms_unchanged(rom_path, private_rom, rom_before)
    result_by_id = {row["id"]: row for row in results}
    embedded_domains = []
    resume_result_paths = []
    for domain in config["domains"]:
        domain_id = domain["id"]
        if domain["state"] == PENDING:
            embedded_domains.append({
                "id": domain_id,
                "status": PENDING,
                "pending_reason": domain["pending_reason"],
                "resume_cache_path": None,
            })
            continue
        record = result_by_id[domain_id]
        result_relative = (
            state / "results" / f"{domain_id}.json"
        ).relative_to(ROOT).as_posix()
        resume_result_paths.append(result_relative)
        embedded_domains.append({
            "id": domain_id,
            "status": "PASS",
            "pending_reason": None,
            "runner": record["runner"],
            "compilation": record["compilation"],
            "command_argument_count": record["command_argument_count"],
            "stderr_sha256": record["stderr_sha256"],
            "runner_result_sha256": _sha(_stable(record["runner_result"])),
            "runner_result": record["runner_result"],
            "resume_cache_path": result_relative,
        })
    gate = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "PASS_WITH_DECLARED_LIMITS",
        "classification": "LATEST_CUMULATIVE_EXACT_ROM_SEQUENTIAL_RESUMABLE",
        "config": plan["config"], "orchestrator": plan["orchestrator"],
        "input": plan["input"], "plan_fingerprint": fingerprint,
        "domain_order": plan["domain_order"],
        "domains": embedded_domains,
        "execution": {
            "fresh_mGBA_process_runs": fresh_run_count,
            "cached_domain_results_reused": cached_result_count,
            "evidenced_domain_runs": len(ready_ids),
            "individual_results_written_this_invocation": fresh_run_count,
            "checkpoint_written": True,
            "resume_cache_checkpoint_path": checkpoint_path.relative_to(ROOT).as_posix(),
            "resume_supported": True,
            "explicit_heavy_run_required": True,
            "runner_results_embedded": True,
        },
        "claims": {
            "product_rom_patched": False,
            "full_p03_done": False,
            "full_p05_done": False,
            "release_ready": False,
            "physical_all_menu_paths_e2e": False,
            "link_runtime_e2e": False,
        },
        "not_yet_executed": False,
        "runner_results_embedded": True,
        "resume_cache": {
            "required_for_check": False,
            "checkpoint_path": checkpoint_path.relative_to(ROOT).as_posix(),
            "private_rom_path": private_rom.relative_to(ROOT).as_posix(),
            "result_paths": resume_result_paths,
        },
        "artifacts_written": [config["execution"]["runtime_gate"]],
    }
    gate_path = ROOT / config["execution"]["runtime_gate"]
    _safe_write_parent(gate_path)
    _atomic_write(gate_path, _stable(gate))
    return gate


def check(config_path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = _read_json_path(_config_path(config_path), "Stage79 config")
    _validate_config(config)
    gate_path = _relative_path(config["execution"]["runtime_gate"],
                               "Stage79 runtime gate")
    gate = _read_json_path(gate_path, "Stage79 runtime gate")
    completed = gate.get("status") == "PASS_WITH_DECLARED_LIMITS"
    plan = build_plan(config_path, allow_missing_p02_seed=completed)
    expected_ready = _ready_gate(plan, config)
    if gate.get("status") == "READY_NOT_RUN":
        if gate != expected_ready:
            _fail("Stage79 READY runtime gate不一致")
    elif gate.get("status") == "PASS_WITH_DECLARED_LIMITS":
        if set(gate) != {
                "schema_version", "task", "stage", "status",
                "classification", "config", "orchestrator", "input",
                "plan_fingerprint",
                "domain_order", "domains", "execution", "claims",
                "not_yet_executed", "runner_results_embedded",
                "resume_cache", "artifacts_written",
            } \
                or (gate.get("schema_version"), gate.get("task"),
                    gate.get("stage"), gate.get("classification")) != (
                    1, TASK, STAGE,
                    "LATEST_CUMULATIVE_EXACT_ROM_SEQUENTIAL_RESUMABLE",
                ) \
                or gate.get("config") != plan["config"] \
                or gate.get("orchestrator") != plan["orchestrator"] \
                or gate.get("input") != plan["input"] \
                or gate.get("plan_fingerprint") != plan["plan_fingerprint"] \
                or gate.get("domain_order") != plan["domain_order"] \
                or gate.get("claims") != expected_ready["claims"]:
            _fail("Stage79 completed gate identity/claims不一致")
        rows = gate.get("domains")
        if not isinstance(rows, list) or [row.get("id") for row in rows] \
                != plan["domain_order"]:
            _fail("Stage79 completed domain order不一致")
        config_by_id = {row["id"]: row for row in config["domains"]}
        ready_ids = [row["id"] for row in config["domains"]
                     if row["state"] == READY]
        state = _state_directory(config, plan["plan_fingerprint"])
        expected_checkpoint = (state / "checkpoint.json").relative_to(ROOT).as_posix()
        expected_private_rom = (
            state / "input" / "stage78-private.gba"
        ).relative_to(ROOT).as_posix()
        expected_result_paths = [
            (state / "results" / f"{domain_id}.json").relative_to(ROOT).as_posix()
            for domain_id in ready_ids
        ]
        expected_execution = {
            "resume_cache_checkpoint_path": expected_checkpoint,
            "resume_supported": True,
            "explicit_heavy_run_required": True,
            "runner_results_embedded": True,
        }
        actual_execution = gate.get("execution")
        fresh_runs = _integer(
            actual_execution.get("fresh_mGBA_process_runs")
            if isinstance(actual_execution, Mapping) else None,
            "fresh mGBA process runs",
        )
        cached_runs = _integer(
            actual_execution.get("cached_domain_results_reused")
            if isinstance(actual_execution, Mapping) else None,
            "cached domain results",
        )
        if not isinstance(actual_execution, Mapping) \
                or set(actual_execution) != set(expected_execution) | {
                    "fresh_mGBA_process_runs", "cached_domain_results_reused",
                    "evidenced_domain_runs",
                    "individual_results_written_this_invocation",
                    "checkpoint_written",
                } \
                or any(actual_execution.get(key) != value
                       for key, value in expected_execution.items()) \
                or actual_execution.get("checkpoint_written") is not True \
                or actual_execution.get("evidenced_domain_runs") \
                    != len(ready_ids) \
                or not 0 <= fresh_runs <= len(ready_ids) \
                or not 0 <= cached_runs <= len(ready_ids) \
                or fresh_runs + cached_runs != len(ready_ids) \
                or actual_execution.get("individual_results_written_this_invocation") \
                    != actual_execution.get("fresh_mGBA_process_runs") \
                or gate.get("not_yet_executed") is not False \
                or gate.get("runner_results_embedded") is not True \
                or gate.get("artifacts_written") \
                    != [config["execution"]["runtime_gate"]] \
                or gate.get("resume_cache") != {
                    "required_for_check": False,
                    "checkpoint_path": expected_checkpoint,
                    "private_rom_path": expected_private_rom,
                    "result_paths": expected_result_paths,
                }:
            _fail("Stage79 completed execution/artifact contract不一致")
        input_rom = _identity(plan["input"]["rom"]["path"], "cumulative ROM")
        for row in rows:
            domain = config_by_id[row["id"]]
            if domain["state"] == PENDING:
                if row.get("status") != PENDING \
                        or row.get("pending_reason") != domain["pending_reason"] \
                        or row.get("resume_cache_path") is not None \
                        or set(row) != {
                            "id", "status", "pending_reason", "resume_cache_path"
                        }:
                    _fail(f"{row['id']} pending境界不一致")
                continue
            expected_path = (
                state / "results" / f"{row['id']}.json"
            ).relative_to(ROOT).as_posix()
            if set(row) != {
                    "id", "status", "pending_reason", "runner",
                    "compilation", "command_argument_count",
                    "stderr_sha256", "runner_result_sha256",
                    "runner_result", "resume_cache_path",
                } \
                    or not isinstance(row.get("runner_result"), Mapping) \
                    or row.get("status") != "PASS" \
                    or row.get("resume_cache_path") != expected_path \
                    or row.get("pending_reason") is not None \
                    or row.get("runner") != domain["runner"] \
                    or row.get("runner_result_sha256") \
                        != _sha(_stable(row.get("runner_result"))):
                _fail(f"{row['id']} completed result不一致")
            record = {
                "schema_version": 1,
                "task": TASK,
                "stage": STAGE,
                "id": row["id"],
                "status": "PASS",
                "plan_fingerprint": plan["plan_fingerprint"],
                "input_rom": input_rom,
                "runner": row.get("runner"),
                "compilation": row.get("compilation"),
                "command_argument_count": row.get("command_argument_count"),
                "stderr_sha256": row.get("stderr_sha256"),
                "runner_result": row.get("runner_result"),
            }
            _validate_result_record(
                domain, record, plan["plan_fingerprint"], input_rom,
                plan["input"]["rom"]["sha256"],
            )
    else:
        _fail("Stage79 runtime gate status不一致")
    return {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "CHECK_PASS", "gate_status": gate["status"],
        "plan_fingerprint": plan["plan_fingerprint"],
        "mGBA_process_runs": 0, "artifacts_written": [],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode", choices=("prepare", "dry-run", "compile-check", "run", "check")
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--yes-heavy", action="store_true",
        help="重いmGBA process実行を明示承認する（run専用）",
    )
    args = parser.parse_args(argv)
    try:
        if args.mode == "prepare":
            result = prepare(args.config)
        elif args.mode == "dry-run":
            result = build_plan(args.config)
        elif args.mode == "compile-check":
            result = compile_check(args.config)
        elif args.mode == "check":
            result = check(args.config)
        else:
            if not args.yes_heavy:
                _fail("runには--yes-heavyが必要です")
            result = run(args.config, heavy_confirmed=True)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (Stage79CumulativeMgbaError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
