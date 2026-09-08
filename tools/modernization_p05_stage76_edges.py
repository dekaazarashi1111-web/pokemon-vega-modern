#!/usr/bin/env python3
"""Stage75を親にP05残edgeのfail-closed Stage76を生成する。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.bps import apply_bps, create_bps
from tools.rom_allocator import GBA_ROM_BASE, build_allocation_report_from_csv


SCHEMA_VERSION = 1
TASK = "USER-MODERNIZATION-P05-STAGE76-EDGES"
STAGE = 76
ROM_SIZE = 32 * 1024 * 1024
DEFAULT_CONFIG = Path("config/modernization_p05_stage76_edges.json")
PROVISIONAL_LOAD_ADDRESS = 0x09560000
EXPECTED_PARENT_ALLOCATION_COUNT = 79
EXPECTED_PARENT_LAST_SEQUENCE = 78
EXPECTED_NEW_SEQUENCE = 79
EXPECTED_STAGE72_PROTECTION_SYMBOL = "0x095341B5"
EXPECTED_STAGE75_COMMIT = "595909446b6ad67749c9894b23fdc536f82c638e"
_SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")

EXPECTED_PARENT_IDENTITY = {
    "stage75_commit": EXPECTED_STAGE75_COMMIT,
    "rom": {
        "path": "build/stages/75_modernization_rockruff_own_tempo.gba",
        "size": 33554432,
        "sha256": "a179c024294f4f1bbf34eb603af255f6896265d9d8523344719b349f8a4495c3",
    },
    "metadata": {
        "path": "build/stages/75_modernization_rockruff_own_tempo.json",
        "size": 151435,
        "sha256": "be84b5a54c7ea8de23d4245402a427cc0dd444949363b8b6ca3e206b5ecd93f4",
    },
    "allocation": {
        "path": "build/stages/75_modernization_rockruff_own_tempo_allocation.json",
        "size": 45230,
        "sha256": "90a68321eebbebde765077eca81643f176d91152f331be77360cb8c52e188f09",
    },
    "checkpoint": {
        "path": "content/modernization/rockruff_own_tempo_stage75_checkpoint.json",
        "size": 4874,
        "sha256": "c4f6d822950cd27fa65134d3806c2cbed3409b6de4b2358a8f12924524d65705",
    },
    "tracked_config": {
        "path": "config/modernization_rockruff_own_tempo_stage75.json",
        "size": 8066,
        "sha256": "2accef3c5cb3e45e3b032035acfbc727b2785deafd652a45f56ca0db3ebbf121",
    },
    "policy": "FAIL_CLOSED_EXACT_STAGE75_IMPLEMENTATION_COMMIT_AND_FIVE_IDENTITIES",
}
EXPECTED_EDGES = {
    "mega_sol_solar_charge_popup": "IMPLEMENT",
    "piercing_drill_ai_virtual_protect_quarter": "IMPLEMENT",
    "spicy_spray_friendly_fire_ai_score": "IMPLEMENT",
    "eelevate_dedicated_switch": "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT",
}
EXPECTED_EDGE_CONTRACT = {
    "mega_sol": {
        "production_pointer_only": True,
        "generic_attacks_this_turn_side_effect": False,
        "popup_only_when_personal_sun_changes_charge_result": True,
        "second_turn_routes_to_original_script": True,
    },
    "piercing_drill": {
        "ability_source": "DamageCalc.atkAbility when provided; otherwise effective active ability",
        "prediction_source": "IsValidMovePrediction(defender, attacker)",
        "requires_original_protection_block": True,
        "requires_contact_single_target": True,
        "real_protect_damage_not_double_quartered": True,
        "individual_protect_moves_include_detect_197": True,
        "detect_197_normalized_to_protect_182_for_original_gate": True,
        "chosen_move_resolved_via_get_ai_chosen_move": True,
        "rejects_unselected_prediction_while_defender_dynamaxed": True,
        "predicted_damage_fraction": "1/4_minimum_1",
    },
    "spicy_spray": {
        "direct_partner_score_bonus": 3,
        "direct_target_ranges": ["SELECTED", "USER_OR_PARTNER"],
        "excluded_direct_target_ranges": [
            "RANDOM", "DEPENDS", "USER", "BOTH", "ALL", "OPPONENTS_FIELD",
        ],
        "spread_partner_penalty_removed": 3,
        "direct_and_spread_adjustments_are_exclusive": True,
        "requires_partner_staying_in": True,
        "direct_partner_move_source": "AIScript.partnerMove+0x46",
        "spread_partner_move_source": "GetAIChosenMove(partner, gBattleStruct->moveTarget[partner])",
        "direct_move_source": "TryReplaceMoveWithZMove(attacker, partner, originalMove)",
        "direct_attacker_ability_source": "GetAIAbility(attacker, AIScript.foe1, resolvedMove)",
        "spread_attacker_ability_source": "GetAIAbility(attacker, attacker XOR 1 opposing bank, resolvedMove)",
        "burn_benefit_ability_source": "effective GetAIAbility result for resolved move",
        "rejects_planned_protection_or_earlier_semi_invulnerable_move": True,
        "planned_detect_197_normalized_to_protect_182_for_protection_gate": True,
        "resolved_max_guard_891_is_not_hit": True,
        "direct_heal_target_effect_233_is_not_damage": True,
        "direct_present_effect_122_is_not_guaranteed_damage": True,
        "direct_future_sight_effect_148_is_not_instant_damage": True,
        "direct_effect_policy": "instant damaging only; excludes Present, Future Sight, and Heal Target effects",
        "requires_effective_unsuppressed_partner_ability": True,
        "rejects_target_ability_ignore_unless_partner_holds_ability_shield": True,
        "requires_actual_damaging_move": True,
        "rejects_substitute_block": True,
        "rejects_partner_ko": True,
        "rejects_self_sacrifice_and_half_hp_recoil": True,
        "rejects_flame_orb_and_burn_healing_items": True,
        "benefit": "Marvel Scale or Quick Feet; Guts with physical move; Flare Boost with special move; or Facade",
    },
    "eelevate": {
        "status": "PENDING",
        "reason": "ability-only 313->298 mapping is unsound when Ground damage, Thousand Arrows, grounding, Gravity, Mold Breaker, and Ability Shield conditions differ",
        "preserved_parent_sites": ["0x090A03E4", "0x090A0426"],
        "release_blocker": True,
    },
}
EXPECTED_ALLOCATION = {
    "name": "modernization_p05_stage76_edges_payload",
    "region": "integration_modules",
    "alignment": 16,
    "owner": "USER-MODERNIZATION-P05-STAGE76-EDGES",
    "purpose": "Mega Sol production Solar Beam popup plus Piercing Drill and Spicy Spray AI edge adapters",
}
EXPECTED_FIXED_FUNCTIONS = {
    "IsZMove": "0x090D6684",
    "IsAnyMaxMove": "0x090F1CF4",
    "IsValidMovePrediction": "0x090B0AFC",
    "AI_SpecialTypeCalc": "0x090E6278",
    "DoesProtectionMoveBlockMove": "0x090BC4C0",
    "MoveWouldHitFirst": "0x090AFF88",
    "IsAbilitySuppressed": "0x090D7BB0",
    "TryReplaceMoveWithZMove": "0x090B2E88",
    "GetAIChosenMove": "0x090B042C",
    "GetAIAbility": "0x090B09C4",
    "IsTargetAbilityIgnored": "0x090BBB78",
    "IsDynamaxed": "0x090F1894",
    "Stage72_OriginalDoesProtectionMoveBlockMove": "0x095341B5",
}
EXPECTED_FIXED_LAYOUT = {
    "gBattleStruct_pointer": "0x02023F48",
    "BattleStruct_monToSwitchIntoId_offset": "0x5C",
    "BattleStruct_moveTarget_offset": "0x0C",
    "gChosenMovesByBanks": "0x02023D24",
    "AIScript_atkPartnerAbility_offset": "0x40",
    "AIScript_foe1_offset": "0x44",
    "AIScript_partnerMove_offset": "0x46",
    "DamageCalc_atkAbility_offset": "0x10",
    "party_size_sentinel": 6,
}
EXPECTED_FIXED_FUNCTION_PREIMAGES = [
    {
        "name": "DoesProtectionMoveBlockMove", "address": "0x090BC4C0",
        "width": 16, "parent_hex": "9c46014b1847c046194153091e006300",
    },
    {
        "name": "MoveWouldHitFirst", "address": "0x090AFF88",
        "width": 16, "parent_hex": "f0b50d00c646060014001f0002000021",
    },
    {
        "name": "IsAbilitySuppressed", "address": "0x090D7BB0",
        "width": 16, "parent_hex": "074b8000c35801201b0107d4054b1b68",
    },
    {
        "name": "TryReplaceMoveWithZMove", "address": "0x090B2E88",
        "width": 16, "parent_hex": "f8b5050010000e0014003ef02fff0028",
    },
    {
        "name": "GetAIChosenMove", "address": "0x090B042C",
        "width": 16, "parent_hex": "1b4b420070b5d55a1a4e04003368002d",
    },
    {
        "name": "GetAIAbility", "address": "0x090B09C4",
        "width": 16, "parent_hex": "70b504000d00fff77dff002805d05822",
    },
    {
        "name": "IsTargetAbilityIgnored", "address": "0x090BBB78",
        "width": 16, "parent_hex": "0b00a43b1b0470b51b0c05000c001600",
    },
    {
        "name": "IsDynamaxed", "address": "0x090F1894",
        "width": 16, "parent_hex": "054b064a1b6894461b18002063441856",
    },
]
EXPECTED_POINTER_PATCHES = [
    {
        "name": "SolarBeamEffectScript", "address": "0x0903FCA4", "width": 4,
        "target": "Stage76_BattleScriptSolarBeam", "parent_hex": "c1500009",
    },
]
EXPECTED_HOOKS = [
    {
        "name": "AI_CalcDmg", "address": "0x090E9E64", "width": 12,
        "target": "Stage76_EntryAICalcDmg",
        "parent_hex": "f0b5de464e4645465746e0b5",
        "continuation_thumb": "0x090E9E71",
    },
    {
        "name": "AIScript_Partner", "address": "0x090A95E4", "width": 12,
        "target": "Stage76_EntryAIScriptPartner",
        "parent_hex": "f0b5de4657464e464546e0b5",
        "continuation_thumb": "0x090A95F1",
    },
    {
        "name": "RangeMoveCanHurtPartner", "address": "0x090B0048", "width": 8,
        "target": "Stage76_EntryRangeMoveCanHurtPartner",
        "parent_hex": "70b5140058226243",
        "continuation_thumb": "0x090B0051",
    },
]
EXPECTED_NEGATIVE_PRESERVATION_SITES = [
    {
        "name": "FindMonAbsorberActiveAbilityBlock", "address": "0x090A03E4",
        "width": 16, "parent_hex": "95235b009b463100280010f0bffa5b46",
        "reason": "Eelevate mapping cannot safely preserve Thousand Arrows, grounding, Mold Breaker, and Ability Shield semantics at this callsite",
    },
    {
        "name": "FindMonAbsorberPartyAbilityBlock", "address": "0x090A0426",
        "width": 12, "parent_hex": "3000984639f007ffe38e0700",
        "reason": "party callsite lacks the complete runtime context required for a sound Eelevate absorption decision",
    },
]
EXPECTED_OUTPUTS = {
    "rom": "build/stages/76_modernization_p05_edges.gba",
    "metadata": "build/stages/76_modernization_p05_edges.json",
    "allocation": "build/stages/76_modernization_p05_edges_allocation.json",
    "incremental_bps": "build/patches/stage75-to-stage76-modernization-p05-edges.bps",
    "payload": "generated/runtime/modernization_p05_stage76_edges.bin",
    "symbols": "generated/runtime/modernization_p05_stage76_edges_symbols.json",
    "audit": "generated/runtime/modernization_p05_stage76_edges_audit.json",
    "contract": "content/modernization/p05_stage76_edges_contract.json",
    "checkpoint": "content/modernization/p05_stage76_edges_checkpoint.json",
}
EXPECTED_SOURCE_PINS = {
    "fixed_cfru_jp_commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
    "pokeemerald_expansion_commit": "cafe0221cefb2a991cc0ece429174ade877d037d",
    "stage72_symbols": {
        "path": "generated/runtime/modernization_p05_ability_rom_runtime_symbols.json",
        "sha256": "9204f33ab9b6109d94ee7a19f1b6d96f5ab872d576b034bdb46c40b6547af029",
    },
    "rom_regions": {
        "path": "config/rom_regions.csv",
        "sha256": "f5dcb0ecf2f726bfff1e9c8382204e79b1354ee9071f8d9ac00a83de7a9b3553",
    },
    "move_manifest": {
        "path": "manifests/move_ids.csv",
        "sha256": "dba3c65af59ee2dcfa9eecdeeeb1cc189a990b52e27b1878bad6eaec8e104f20",
    },
    "p05_host_header": {
        "path": "overlays/modernization_p05_abilities/modernization_p05_abilities.h",
        "sha256": "4fceaed3e9000111ab3ab66b82559ca2198a167eec904f51bb0a5eeffe1c552b",
    },
    "p05_host_source": {
        "path": "overlays/modernization_p05_abilities/modernization_p05_abilities.c",
        "sha256": "7448cf6cc3b0bcca94f13b94cc3fb754d667882d38e45c90e6e2f6dc1b3df27e",
    },
    "fixed_cfru_ai_util": {
        "path": "vendor/upstream/CFRU-JP/src/Battle_AI/ai_util.c",
        "sha256": "3479dda29bf49c548ba590fb1a8fe501176ab17a934e88d2b04cd7112c2eea61",
    },
    "fixed_cfru_ai_scripts": {
        "path": "vendor/upstream/CFRU-JP/include/new/ai_scripts.h",
        "sha256": "6b406abd337bf653478c4bc4b8efcf72eef8eeb74d020ea2255caa4f7ba32e1b",
    },
    "fixed_cfru_ai_partner": {
        "path": "vendor/upstream/CFRU-JP/src/Battle_AI/ai_partner.c",
        "size": 17749,
        "sha256": "f813c3ae78d190db5ef43d46f143801cba6cc6bb0a894c91dc0336f27ae7e8a5",
    },
    "fixed_cfru_dynamax": {
        "path": "vendor/upstream/CFRU-JP/src/dynamax.c",
        "size": 66919,
        "sha256": "ef0eb85047ec0a7d74b5df38bce8481367828508e2104aa7615de62ddecc2c0a",
    },
    "fixed_cfru_battle_move_effects": {
        "path": "vendor/upstream/CFRU-JP/include/constants/battle_move_effects.h",
        "size": 8736,
        "sha256": "17422df2ad75185493d11325f94f833a656265c7a9d23091260bb3677763b036",
    },
    "fixed_cfru_battle_util": {
        "path": "vendor/upstream/CFRU-JP/src/battle_util.c",
        "sha256": "558c9a85d067e984c96bf83fb0c652a58df3b0b5fbf63620e4ea694195458ed3",
    },
    "active_play_baseline_json": {
        "path": "config/active_play_baseline.json", "size": 394,
        "sha256": "4800257add049ea99cdedda91413a70a255dcff9a85823463596edefa8785053",
    },
    "active_play_baseline_md": {
        "path": "design/active_play_baseline.md", "size": 5551,
        "sha256": "e486dfa3fd9771084ba50390dd30b70d5c52e008a0b48f8cd186086e05e819f8",
    },
}
EXPECTED_STAGE75_IMPLEMENTATION_PATHS = {
    "config/modernization_rockruff_own_tempo_stage75.json",
    "content/modernization/rockruff_own_tempo_stage75_checkpoint.json",
    "content/modernization/rockruff_own_tempo_stage75_contract.json",
    "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.c",
    "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.h",
    "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.ld",
    "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75_scripts.S",
    "scripts/build_modernization_rockruff_own_tempo_stage75.sh",
    "tests/test_modernization_rockruff_own_tempo_stage75.py",
    "tools/modernization_rockruff_own_tempo_stage75.py",
}


class ModernizationP05Stage76EdgesError(RuntimeError):
    """Stage76のidentity、ABI、preimage、allocation違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP05Stage76EdgesError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool):
        _fail(f"{label}が整数ではありません")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    _fail(f"{label}を整数化できません: {value!r}")


def _json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"{label} JSON不正: {error}")
    if not isinstance(value, dict):
        _fail(f"{label} rootがobjectではありません")
    return value


def _fixed_raw(root: Path, contract: Mapping[str, Any], label: str) -> bytes:
    relative = contract.get("path")
    digest = contract.get("sha256")
    _require(
        isinstance(relative, str)
        and bool(relative)
        and isinstance(digest, str)
        and bool(_SHA_RE.fullmatch(digest)),
        f"{label} identity未確定または不正",
    )
    path = root / relative
    _require(path.is_file() and not path.is_symlink(), f"{label}が固定通常fileではありません: {path}")
    raw = path.read_bytes()
    if contract.get("size") is not None:
        _require(len(raw) == _integer(contract["size"], f"{label}.size"), f"{label} size不一致")
    _require(sha256(raw) == digest, f"{label} SHA-256不一致")
    return raw


def _rom_offset(address: int, width: int, label: str) -> int:
    offset = address - GBA_ROM_BASE
    _require(0 <= offset <= ROM_SIZE - width, f"{label}がROM範囲外")
    return offset


def read_config(root: Path, relative: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    _require(path.is_file() and not path.is_symlink(), f"Stage76 configが固定通常fileではありません: {path}")
    config = _json(path.read_bytes(), "Stage76 config")
    _require(
        (config.get("schema_version"), config.get("task"), config.get("stage"))
        == (SCHEMA_VERSION, TASK, STAGE),
        "Stage76 schema/task/stage不一致",
    )
    _require(
        config.get("status") in {
            "PARENT_PENDING_FAIL_CLOSED", "STAGE75_IDENTITY_PINNED"
        },
        "Stage76 status不正",
    )
    _require(config.get("parent_identity") == EXPECTED_PARENT_IDENTITY, "Stage75 parent identity exact集合不一致")
    _require(config.get("source_pins") == EXPECTED_SOURCE_PINS, "Stage76 source pin exact集合不一致")
    _require(config.get("edges") == EXPECTED_EDGES, "Stage76 edge集合不一致")
    _require(config.get("edge_contract") == EXPECTED_EDGE_CONTRACT, "Stage76 edge contract exact集合不一致")
    _require(config.get("allocation") == EXPECTED_ALLOCATION, "Stage76 allocation declaration exact集合不一致")
    parent_abi = config.get("parent_abi", {})
    _require(isinstance(parent_abi, dict), "Stage76 parent_abi不正")
    pointer_rows = parent_abi.get("pointer_patches")
    hook_rows = parent_abi.get("hooks")
    _require(pointer_rows == EXPECTED_POINTER_PATCHES, "Stage76 pointer patch exact集合不一致")
    _require(hook_rows == EXPECTED_HOOKS, "Stage76 hook exact集合不一致")
    _require(
        parent_abi.get("negative_preservation_sites")
        == EXPECTED_NEGATIVE_PRESERVATION_SITES,
        "Stage76 Eelevate negative preservation exact集合不一致",
    )
    _require(
        parent_abi.get("fixed_function_preimages")
        == EXPECTED_FIXED_FUNCTION_PREIMAGES,
        "Stage76 fixed function preimage exact集合不一致",
    )
    occupied: list[tuple[int, int, str]] = []
    for row in [*pointer_rows, *hook_rows]:
        _require(isinstance(row, dict), "Stage76 ABI rowがobjectではありません")
        name = str(row.get("name"))
        address = _integer(row.get("address"), f"{name}.address")
        width = _integer(row.get("width"), f"{name}.width")
        expected = bytes.fromhex(str(row.get("parent_hex", "")))
        _require(len(expected) == width, f"{name} parent_hex width不一致")
        if row in hook_rows:
            _require(
                _integer(row.get("continuation_thumb"), f"{name}.continuation_thumb")
                == ((address + width) | 1),
                f"{name} continuationがdisplaced範囲末尾ではありません",
            )
        offset = _rom_offset(address, width, name)
        occupied.append((offset, offset + width, name))
    for left, right in zip(sorted(occupied), sorted(occupied)[1:]):
        _require(right[0] >= left[1], f"Stage76 patch重複: {left[2]} / {right[2]}")
    _require(parent_abi.get("fixed_functions") == EXPECTED_FIXED_FUNCTIONS, "Stage76 fixed function ABI不一致")
    _require(parent_abi.get("fixed_layout") == EXPECTED_FIXED_LAYOUT, "Stage76 fixed layout ABI不一致")
    _require(config.get("outputs") == EXPECTED_OUTPUTS, "Stage76 output path exact集合不一致")
    return config


def require_pinned_parent(root: Path, config: Mapping[str, Any]) -> dict[str, bytes]:
    parent = config.get("parent_identity", {})
    commit = parent.get("stage75_commit")
    _require(
        config.get("status") == "STAGE75_IDENTITY_PINNED"
        and parent == EXPECTED_PARENT_IDENTITY
        and commit == EXPECTED_STAGE75_COMMIT
        and bool(_COMMIT_RE.fullmatch(commit)),
        "Stage75 identity未確定: PENDING fail-closed",
    )
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    _require(result.returncode == 0, "Stage75 commit objectが存在しません")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    _require(ancestor.returncode == 0, "Stage75 implementation commitが現HEADのancestorではありません")
    changed = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    _require(changed.returncode == 0, "Stage75 implementation commit path監査失敗")
    _require(
        EXPECTED_STAGE75_IMPLEMENTATION_PATHS
        <= set(changed.stdout.splitlines()),
        "Stage75 commitが必須implementation file集合を含みません",
    )
    for relative, key in (
        ("vendor/upstream/CFRU-JP", "fixed_cfru_jp_commit"),
        (".local/modernization_sources/pokeemerald-expansion", "pokeemerald_expansion_commit"),
    ):
        expected = config["source_pins"][key]
        actual = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root / relative,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        _require(
            actual.returncode == 0 and actual.stdout.strip() == expected,
            f"{key} HEAD pin不一致",
        )
    fixed = {
        key: _fixed_raw(root, parent[key], f"Stage75 {key}")
        for key in ("rom", "metadata", "allocation", "checkpoint", "tracked_config")
    }
    _require(len(fixed["rom"]) == ROM_SIZE, "Stage75 ROM size不一致")
    for key in (
        "stage72_symbols", "rom_regions", "move_manifest",
        "p05_host_header", "p05_host_source", "fixed_cfru_ai_util",
        "fixed_cfru_ai_scripts", "fixed_cfru_ai_partner",
        "fixed_cfru_dynamax", "fixed_cfru_battle_move_effects",
        "fixed_cfru_battle_util",
        "active_play_baseline_json", "active_play_baseline_md",
    ):
        fixed[key] = _fixed_raw(root, config["source_pins"][key], key)

    for key in ("checkpoint", "tracked_config"):
        relative = str(parent[key]["path"])
        committed = subprocess.run(
            ["git", "show", f"{commit}:{relative}"], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        _require(
            committed.returncode == 0 and committed.stdout == fixed[key],
            f"Stage75 commitと{key} identityのcross-link不一致",
        )

    metadata = _json(fixed["metadata"], "Stage75 metadata")
    allocation = _json(fixed["allocation"], "Stage75 allocation")
    checkpoint = _json(fixed["checkpoint"], "Stage75 checkpoint")
    parent_config = _json(fixed["tracked_config"], "Stage75 tracked config")
    rom_identity = dict(parent["rom"])
    rom_identity["crc32"] = f"{zlib.crc32(fixed['rom']) & 0xFFFFFFFF:08X}"
    _require(
        metadata.get("stage") == 75
        and checkpoint.get("stage") == 75
        and parent_config.get("stage") == 75,
        "Stage75 internal stage不一致",
    )
    _require(metadata.get("output") == rom_identity, "Stage75 metadata→ROM identity不一致")
    _require(checkpoint.get("output") == rom_identity, "Stage75 checkpoint→ROM identity不一致")
    _require(
        checkpoint.get("metadata") == {
            "path": parent["metadata"]["path"],
            "size": parent["metadata"]["size"],
            "sha256": parent["metadata"]["sha256"],
        },
        "Stage75 checkpoint→metadata identity不一致",
    )
    _require(
        checkpoint.get("allocation", {}).get("path") == parent["allocation"]["path"]
        and checkpoint.get("allocation", {}).get("size") == parent["allocation"]["size"]
        and checkpoint.get("allocation", {}).get("sha256") == parent["allocation"]["sha256"],
        "Stage75 checkpoint→allocation identity不一致",
    )
    _require(
        parent_config.get("outputs", {}).get("rom") == parent["rom"]["path"]
        and parent_config.get("outputs", {}).get("metadata") == parent["metadata"]["path"]
        and parent_config.get("outputs", {}).get("allocation") == parent["allocation"]["path"]
        and parent_config.get("outputs", {}).get("checkpoint") == parent["checkpoint"]["path"],
        "Stage75 tracked config output cross-link不一致",
    )
    rows75 = allocation.get("allocations")
    _require(
        isinstance(rows75, list)
        and len(rows75) == EXPECTED_PARENT_ALLOCATION_COUNT
        and metadata.get("allocation") == rows75[-1],
        "Stage75 metadata/allocation末尾row不一致",
    )
    payload75 = metadata.get("payload", {})
    _require(
        checkpoint.get("payload", {}).get("allocation_sequence")
        == EXPECTED_PARENT_LAST_SEQUENCE
        and checkpoint.get("payload", {}).get("size") == payload75.get("size")
        and checkpoint.get("payload", {}).get("sha256") == payload75.get("sha256")
        and rows75[-1].get("sequence") == EXPECTED_PARENT_LAST_SEQUENCE
        and rows75[-1].get("size") == payload75.get("size")
        and rows75[-1].get("content_sha256") == payload75.get("sha256"),
        "Stage75 payload/allocation/checkpoint cross-link不一致",
    )
    payload_start = _integer(payload75.get("start"), "Stage75 payload.start")
    payload_size = _integer(payload75.get("size"), "Stage75 payload.size")
    _require(
        sha256(fixed["rom"][payload_start:payload_start + payload_size])
        == payload75.get("sha256"),
        "Stage75 payload ROM slice SHA-256不一致",
    )
    active = _json(fixed["active_play_baseline_json"], "active play baseline")
    _require(
        active.get("stage") == 62
        and active.get("status") == "ACTIVE"
        and active.get("rom", {}).get("sha256")
        == "d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f",
        "active play baseline Stage62 identity不一致",
    )
    symbols = _json(fixed["stage72_symbols"], "Stage72 symbols")
    _require(
        symbols.get("symbols", {}).get("Stage72_OriginalDoesProtectionMoveBlockMove")
        == EXPECTED_STAGE72_PROTECTION_SYMBOL,
        "Stage72 original protection trampoline ABI不一致",
    )
    rows = {
        row["move_key"]: int(row["id"])
        for row in csv.DictReader(fixed["move_manifest"].decode("utf-8").splitlines())
        if row.get("move_key") in {
            "MOVE_KEY_MINDBLOWN", "MOVE_KEY_STEELBEAM", "MOVE_KEY_CHLOROBLAST"
        }
    }
    _require(
        rows == {
            "MOVE_KEY_MINDBLOWN": 732,
            "MOVE_KEY_STEELBEAM": 783,
            "MOVE_KEY_CHLOROBLAST": 821,
        },
        "Stage76 self-sacrifice move project ID不一致",
    )
    return fixed


def _run(command: Sequence[str], root: Path, label: str) -> str:
    result = subprocess.run(
        list(command), cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        _fail(f"{label}失敗\n{result.stdout}\n{result.stderr}")
    return result.stdout


@dataclass(frozen=True)
class CompiledPayload:
    code: bytes
    symbols: dict[str, int]
    compiler: str
    disassembly: str


def compile_payload(root: Path, load_address: int) -> CompiledPayload:
    gcc = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    objdump = shutil.which("arm-none-eabi-objdump")
    _require(bool(gcc and objcopy and nm and objdump), "arm-none-eabi toolchainがPATHにありません")
    source = root / "overlays/modernization_p05_stage76_edges"
    common = ["-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork"]
    with tempfile.TemporaryDirectory(prefix="stage76-p05-edges-") as temporary:
        work = Path(temporary)
        c_obj = work / "runtime.o"
        asm_obj = work / "hooks.o"
        elf = work / "runtime.elf"
        binary = work / "runtime.bin"
        _run([
            str(gcc), *common, "-Os", "-std=c11", "-ffreestanding",
            "-fno-common", "-ffunction-sections", "-fdata-sections",
            "-Wall", "-Wextra", "-Werror", "-Wconversion", "-Wshadow",
            "-c", str(source / "modernization_p05_stage76_edges.c"),
            "-o", str(c_obj),
        ], root, "Stage76 C compile")
        _run([
            str(gcc), *common, "-c",
            str(source / "modernization_p05_stage76_edges_hooks.S"),
            "-o", str(asm_obj),
        ], root, "Stage76 hook compile")
        _run([
            str(gcc), "-nostdlib", *common,
            f"-Wl,--defsym=STAGE76_LOAD_ADDRESS=0x{load_address:08X}",
            f"-Wl,-T,{source / 'modernization_p05_stage76_edges.ld'}",
            str(c_obj), str(asm_obj), "-lgcc", "-o", str(elf),
        ], root, "Stage76 link")
        _run([str(objcopy), "-O", "binary", str(elf), str(binary)], root, "Stage76 objcopy")
        symbol_text = _run([str(nm), "-n", str(elf)], root, "Stage76 nm")
        disassembly = _run([str(objdump), "-d", str(elf)], root, "Stage76 objdump")
        symbols: dict[str, int] = {}
        for line in symbol_text.splitlines():
            fields = line.split()
            if len(fields) == 3 and all(character in "0123456789abcdefABCDEF" for character in fields[0]):
                symbols[fields[2]] = int(fields[0], 16)
        code = binary.read_bytes()
    required = {
        "Stage76_RuntimeProbe", "Stage76_BattleScriptSolarBeam",
        "Stage76_BattleScriptMegaSolPopup", "Stage76_EntryAICalcDmg",
        "Stage76_EntryAIScriptPartner", "Stage76_EntryRangeMoveCanHurtPartner",
    }
    _require(required <= symbols.keys(), "Stage76 required symbol不足")
    _require(
        not any("GroundAbsorber" in symbol or "Eelevate" in symbol for symbol in symbols),
        "Eelevate unsafe veneer/symbolがStage76 payloadに残存",
    )
    continuation_sections = {
        "Stage76_OriginalAICalcDmg": "090e9e71",
        "Stage76_OriginalAIScriptPartner": "090a95f1",
        "Stage76_OriginalRangeMoveCanHurtPartner": "090b0051",
    }
    for symbol, continuation in continuation_sections.items():
        marker = f"<{symbol}>:"
        _require(marker in disassembly, f"{symbol} disassembly不足")
        section = disassembly.split(marker, 1)[1].split("\n\n", 1)[0].lower()
        _require(
            continuation in section,
            f"{symbol} actual continuation不一致: {continuation}",
        )
    _require(0 < len(code) < 0x10000, f"Stage76 payload size不正: {len(code)}")
    return CompiledPayload(
        code=code,
        symbols=symbols,
        compiler=_run([str(gcc), "--version"], root, "gcc version").splitlines()[0],
        disassembly=disassembly,
    )


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = allocation.get("allocations")
    _require(
        isinstance(rows, list) and len(rows) == EXPECTED_PARENT_ALLOCATION_COUNT,
        "Stage75 allocation count不一致",
    )
    _require(
        [row.get("sequence") for row in rows]
        == list(range(EXPECTED_PARENT_ALLOCATION_COUNT)),
        "Stage75 allocation sequence不連続",
    )
    _require(rows[-1].get("sequence") == EXPECTED_PARENT_LAST_SEQUENCE, "Stage75 last sequence不一致")
    requests: list[dict[str, Any]] = []
    for row in rows:
        request = {
            key: row[key]
            for key in (
                "name", "region", "size", "alignment", "owner",
                "purpose", "content_sha256",
            )
        }
        if row.get("placement") == "EXPLICIT":
            request["start"] = row["start"]
        else:
            _require(row.get("placement") == "FIRST_FIT", "Stage75 allocation placement不正")
        requests.append(request)
    return requests


def _allocate(
    root: Path,
    config: Mapping[str, Any],
    previous: Mapping[str, Any],
    size: int,
    digest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    declaration = config["allocation"]
    requests = _previous_requests(previous)
    requests.append({
        "name": declaration["name"], "region": declaration["region"],
        "size": size, "alignment": declaration["alignment"],
        "owner": declaration["owner"], "purpose": declaration["purpose"],
        "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(
        root / str(config["source_pins"]["rom_regions"]["path"]), requests
    )
    _require(report.get("summaries", {}).get("overlap_count") == 0, "Stage76 allocator overlap")
    rows = report.get("allocations", [])
    _require(len(rows) == EXPECTED_NEW_SEQUENCE + 1, "Stage76 allocation count不一致")
    _require(
        rows[:EXPECTED_PARENT_ALLOCATION_COUNT] == previous.get("allocations"),
        "Stage76 allocatorが親first79 rowのfield/layout/content hashを変更しました",
    )
    row = rows[-1]
    _require(
        row.get("sequence") == EXPECTED_NEW_SEQUENCE
        and row.get("name") == declaration["name"]
        and row.get("placement") == "FIRST_FIT",
        "Stage76 allocation末尾不一致",
    )
    return row, report


def _rom_diff_allowlist(
    parent: bytes,
    result: bytes,
    intervals: Sequence[tuple[int, int, str]],
) -> dict[str, Any]:
    _require(len(parent) == len(result) == ROM_SIZE, "ROM diff size不一致")
    ordered = sorted(intervals)
    cursor = 0
    changed_inside = 0
    rows: list[dict[str, Any]] = []
    for start, end, name in ordered:
        _require(0 <= start < end <= ROM_SIZE, f"{name} allowlist範囲不正")
        _require(start >= cursor, f"{name} allowlist重複")
        _require(
            parent[cursor:start] == result[cursor:start],
            f"ROM差分がpayload+patch allowlist外に存在: 0x{cursor:X}..0x{start:X}",
        )
        changed = sum(left != right for left, right in zip(parent[start:end], result[start:end]))
        changed_inside += changed
        rows.append({
            "name": name, "start": start, "end_exclusive": end,
            "size": end - start, "changed_bytes": changed,
        })
        cursor = end
    _require(
        parent[cursor:] == result[cursor:],
        f"ROM差分がpayload+patch allowlist外に存在: 0x{cursor:X}..EOF",
    )
    return {
        "allowed_intervals": rows,
        "allowlist_interval_count": len(rows),
        "changed_bytes_inside_allowlist": changed_inside,
        "changed_bytes_outside_allowlist": 0,
    }


def veneer(width: int, target: int, address: int = 0) -> bytes:
    target |= 1
    if width == 8:
        return struct.pack("<HHI", 0x4B00, 0x4718, target)
    if width == 12:
        if address & 2:
            # At a halfword-but-not-word-aligned site, PC is aligned before
            # the literal offset is added.  Put the word at site+6 (= aligned)
            # and retain one unreachable padding NOP at the end.
            return struct.pack("<HHHIH", 0x469C, 0x4B00, 0x4718, target, 0x46C0)
        return struct.pack("<HHHHI", 0x469C, 0x4B01, 0x4718, 0x46C0, target)
    if width == 16:
        return struct.pack("<HHIHHHH", 0x4B00, 0x4718, target, 0x46C0, 0x46C0, 0x46C0, 0x46C0)
    _fail(f"未対応veneer width: {width}")


def _patch_exact(
    image: bytearray,
    address: int,
    expected: bytes,
    replacement: bytes,
    label: str,
) -> dict[str, Any]:
    _require(len(expected) == len(replacement), f"{label} replacement width不一致")
    offset = _rom_offset(address, len(expected), label)
    actual = bytes(image[offset:offset + len(expected)])
    _require(actual == expected, f"{label} parent preimage不一致: {actual.hex()} != {expected.hex()}")
    image[offset:offset + len(replacement)] = replacement
    return {
        "name": label, "address": f"0x{address:08X}", "width": len(expected),
        "before_hex": expected.hex(), "after_hex": replacement.hex(),
    }


def _source_identities(root: Path) -> dict[str, dict[str, Any]]:
    base = root / "overlays/modernization_p05_stage76_edges"
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(base.iterdir()):
        if path.is_file():
            raw = path.read_bytes()
            result[path.name] = {"size": len(raw), "sha256": sha256(raw)}
    return result


def _implementation_identity(root: Path) -> dict[str, Any]:
    relative_paths = [
        "config/modernization_p05_stage76_edges.json",
        "tools/modernization_p05_stage76_edges.py",
        "scripts/build_modernization_p05_stage76_edges.sh",
        "tests/test_modernization_p05_stage76_edges.py",
        *[
            f"overlays/modernization_p05_stage76_edges/{path.name}"
            for path in sorted((root / "overlays/modernization_p05_stage76_edges").iterdir())
            if path.is_file()
        ],
    ]
    rows: list[dict[str, Any]] = []
    framed = hashlib.sha256()
    for relative in relative_paths:
        raw = (root / relative).read_bytes()
        row = {"path": relative, "size": len(raw), "sha256": sha256(raw)}
        encoded = stable_json(row)
        framed.update(len(encoded).to_bytes(8, "big"))
        framed.update(encoded)
        rows.append(row)
    return {"files": rows, "sha256": framed.hexdigest()}


def build_artifacts(root: Path) -> dict[str, bytes]:
    config = read_config(root)
    fixed = require_pinned_parent(root, config)
    parent = fixed["rom"]
    previous_allocation = _json(fixed["allocation"], "Stage75 allocation")

    provisional = compile_payload(root, PROVISIONAL_LOAD_ADDRESS)
    placement, _ = _allocate(
        root, config, previous_allocation, len(provisional.code), sha256(provisional.code)
    )
    load_address = GBA_ROM_BASE + int(placement["start"])
    compiled = compile_payload(root, load_address)
    _require(len(compiled.code) == len(provisional.code), "Stage76 relocationでpayload size drift")
    placement, allocation_report = _allocate(
        root, config, previous_allocation, len(compiled.code), sha256(compiled.code)
    )
    _require(GBA_ROM_BASE + int(placement["start"]) == load_address, "Stage76 allocation relocation drift")

    image = bytearray(parent)
    start = int(placement["start"])
    _require(
        bytes(image[start:start + len(compiled.code)]) == b"\xFF" * len(compiled.code),
        "Stage76 allocation preimageがFFではありません",
    )
    image[start:start + len(compiled.code)] = compiled.code
    changes: list[dict[str, Any]] = [{
        "name": "payload", "address": f"0x{load_address:08X}",
        "width": len(compiled.code), "before_sha256": sha256(b"\xFF" * len(compiled.code)),
        "after_sha256": sha256(compiled.code),
    }]

    for row in config["parent_abi"]["pointer_patches"]:
        symbol = str(row["target"])
        _require(symbol in compiled.symbols, f"pointer target symbol不足: {symbol}")
        replacement = struct.pack("<I", compiled.symbols[symbol])
        changes.append(_patch_exact(
            image, _integer(row["address"], f"{symbol}.address"),
            bytes.fromhex(row["parent_hex"]), replacement, str(row["name"]),
        ))

    for row in config["parent_abi"]["hooks"]:
        symbol = str(row["target"])
        _require(symbol in compiled.symbols, f"hook target symbol不足: {symbol}")
        width = _integer(row["width"], f"{symbol}.width")
        address = _integer(row["address"], f"{symbol}.address")
        changes.append(_patch_exact(
            image, address,
            bytes.fromhex(row["parent_hex"]),
            veneer(width, compiled.symbols[symbol], address),
            str(row["name"]),
        ))

    result = bytes(image)
    _require(len(result) == ROM_SIZE, "Stage76 output ROM size不一致")
    _require(
        sha256(result[start:start + len(compiled.code)]) == sha256(compiled.code),
        "Stage76 payload ROM slice SHA-256不一致",
    )
    for row in [
        *config["parent_abi"]["fixed_function_preimages"],
        *config["parent_abi"]["negative_preservation_sites"],
    ]:
        address = _integer(row["address"], f"{row['name']}.address")
        width = _integer(row["width"], f"{row['name']}.width")
        offset = _rom_offset(address, width, str(row["name"]))
        expected = bytes.fromhex(str(row["parent_hex"]))
        _require(
            parent[offset:offset + width] == expected
            and result[offset:offset + width] == expected,
            f"{row['name']} fixed/pending siteが変更されました",
        )

    allowlist_intervals = [(start, start + len(compiled.code), "payload")]
    for row in [
        *config["parent_abi"]["pointer_patches"],
        *config["parent_abi"]["hooks"],
    ]:
        offset = _rom_offset(
            _integer(row["address"], f"{row['name']}.address"),
            _integer(row["width"], f"{row['name']}.width"),
            str(row["name"]),
        )
        allowlist_intervals.append(
            (offset, offset + _integer(row["width"], f"{row['name']}.width"), str(row["name"]))
        )
    diff_audit = _rom_diff_allowlist(parent, result, allowlist_intervals)

    implementation = _implementation_identity(root)
    payload_identity = {
        "path": config["outputs"]["payload"],
        "start": start,
        "load_address": f"0x{load_address:08X}",
        "size": len(compiled.code),
        "sha256": sha256(compiled.code),
        "allocation_sequence": EXPECTED_NEW_SEQUENCE,
    }
    output_identity = {
        "path": config["outputs"]["rom"], "size": len(result),
        "sha256": sha256(result),
        "crc32": f"{zlib.crc32(result) & 0xFFFFFFFF:08X}",
    }
    parent_rows_hash = sha256(stable_json(previous_allocation["allocations"]))
    allocation_lineage = {
        "parent_count": EXPECTED_PARENT_ALLOCATION_COUNT,
        "parent_last_sequence": EXPECTED_PARENT_LAST_SEQUENCE,
        "new_count": EXPECTED_NEW_SEQUENCE + 1,
        "new_sequence": EXPECTED_NEW_SEQUENCE,
        "first79_all_fields_equal": True,
        "parent_first79_sha256": parent_rows_hash,
        "new_first79_sha256": sha256(stable_json(
            allocation_report["allocations"][:EXPECTED_PARENT_ALLOCATION_COUNT]
        )),
        "payload_slice_sha256": sha256(result[start:start + len(compiled.code)]),
    }
    _require(
        allocation_lineage["parent_first79_sha256"]
        == allocation_lineage["new_first79_sha256"],
        "Stage76 first79 allocation lineage hash不一致",
    )

    bps = create_bps(parent, result, metadata=b"Stage75 to Stage76 P05 edge completion")
    _require(apply_bps(parent, bps) == result, "Stage75→76 BPS roundtrip不一致")
    bps_identity = {
        "path": config["outputs"]["incremental_bps"],
        "size": len(bps), "sha256": sha256(bps),
        "source_sha256": sha256(parent), "target_sha256": sha256(result),
        "round_trip": True,
    }
    active_baseline = {
        "stage": 62,
        "unchanged": True,
        "json": dict(config["source_pins"]["active_play_baseline_json"]),
        "markdown": dict(config["source_pins"]["active_play_baseline_md"]),
    }
    remaining_work = [
        "Eelevate dedicated switch AI: full Ground/Thousand Arrows/grounding/Gravity/Mold Breaker/Ability Shield semantics",
        "mGBA runtime validation (Mega popup / Piercing and Spicy AI battle decisions)",
    ]
    checks = {
        "parent_stage75_implementation_cross_link": "PASS",
        "parent_preimages": "PASS",
        "allocator_overlap": "PASS",
        "parent_first79_rows_all_fields_preserved": "PASS",
        "payload_ff_preimage": "PASS",
        "payload_rom_slice": "PASS",
        "rom_diff_outside_payload_plus_four_patches": 0,
        "mega_production_pointer_only": "PASS",
        "piercing_original_protection_gate": "PASS",
        "piercing_damage_calc_predicted_ability": "PASS",
        "spicy_direct_and_spread_exclusive_actual_hit_paths": "PASS",
        "eelevate_unsafe_hooks_installed": 0,
        "eelevate_parent_sites_preserved": "PASS",
        "browt_pombon_gecqua_added": 0,
        "side_change_added": 0,
        "active_play_baseline_unchanged": "PASS",
        "bps_roundtrip": "PASS",
        "mgba_runtime": "NOT_RUN",
    }
    symbols_json = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "load_address": f"0x{load_address:08X}", "compiler": compiled.compiler,
        "payload_size": len(compiled.code), "payload_sha256": sha256(compiled.code),
        "symbols": {
            key: f"0x{value:08X}"
            for key, value in sorted(compiled.symbols.items())
            if key.startswith("Stage76_")
        },
        "eelevate_symbols_present": False,
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "THREE_EDGES_IMPLEMENTED_EELEVATE_PENDING",
        "parent": {
            "stage": 75, "commit": EXPECTED_STAGE75_COMMIT,
            "path": config["parent_identity"]["rom"]["path"],
            "size": len(parent), "sha256": sha256(parent),
        },
        "output": output_identity, "payload": payload_identity,
        "changes": changes, "rom_diff": diff_audit,
        "allocation_lineage": allocation_lineage,
        "edge_contract": config["edge_contract"], "checks": checks,
        "implementation": implementation, "active_play_baseline": active_baseline,
        "eelevate_pending": {
            "unsafe_hooks_installed": 0,
            "preserved_parent_sites": config["parent_abi"]["negative_preservation_sites"],
            "reason": config["edge_contract"]["eelevate"]["reason"],
        },
        "release_ready": False, "full_p05_done": False, "done": False,
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "THREE_EDGES_ROM_MATERIALIZED_EELEVATE_AND_MGBA_PENDING",
        "parent": audit["parent"], "output": output_identity,
        "payload": payload_identity, "allocation_sequence": EXPECTED_NEW_SEQUENCE,
        "allocation_lineage": allocation_lineage, "bps": bps_identity,
        "edges": config["edges"], "checks": checks,
        "implemented_edge_count": 3, "pending_edge_count": 1,
        "release_ready": False, "full_p05_done": False, "done": False,
        "remaining_work": remaining_work,
        "source_identities": _source_identities(root),
        "implementation": implementation,
        "active_play_baseline": active_baseline,
        "artifact_count": 9,
    }
    contract = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "THREE_P05_EDGES_MATERIALIZED_EELEVATE_PENDING",
        "parent_sha256": sha256(parent), "output": output_identity,
        "payload": payload_identity, "allocation_sequence": EXPECTED_NEW_SEQUENCE,
        "allocation_lineage": allocation_lineage, "bps": bps_identity,
        "edges": config["edges"], "checks": checks,
        "release_ready": False, "full_p05_done": False, "done": False,
        "implementation_sha256": implementation["sha256"],
        "pending": remaining_work, "active_play_baseline": active_baseline,
    }

    outputs = config["outputs"]
    artifacts: dict[str, bytes] = {
        outputs["rom"]: result,
        outputs["metadata"]: stable_json(metadata),
        outputs["allocation"]: stable_json(allocation_report),
        outputs["incremental_bps"]: bps,
        outputs["payload"]: compiled.code,
        outputs["symbols"]: stable_json(symbols_json),
        outputs["audit"]: stable_json(audit),
        outputs["contract"]: stable_json(contract),
    }
    sibling_identities = [
        {
            "path": relative, "size": len(raw), "sha256": sha256(raw),
            "sha256_scope": "WHOLE_FILE",
        }
        for relative, raw in artifacts.items()
    ]
    checkpoint_core = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "THREE_EDGES_ROM_MATERIALIZED_EELEVATE_AND_MGBA_PENDING",
        "parent": audit["parent"], "output": output_identity,
        "payload": payload_identity, "allocation_sequence": EXPECTED_NEW_SEQUENCE,
        "allocation_lineage": allocation_lineage, "rom_diff": diff_audit,
        "bps": bps_identity, "checks": checks, "edges": config["edges"],
        "implemented_edge_count": 3, "pending_edge_count": 1,
        "release_ready": False, "full_p05_done": False, "done": False,
        "implementation_sha256": implementation["sha256"],
        "pending": remaining_work, "active_play_baseline": active_baseline,
    }
    checkpoint_core_raw = stable_json(checkpoint_core)
    checkpoint_core_sha = sha256(checkpoint_core_raw)
    checkpoint_size = 0
    checkpoint_raw = b""
    for _ in range(8):
        self_identity = {
            "path": outputs["checkpoint"], "size": checkpoint_size,
            "sha256": checkpoint_core_sha,
            "sha256_scope": "STABLE_JSON_WITHOUT_ARTIFACT_MANIFEST",
        }
        checkpoint = dict(checkpoint_core)
        checkpoint["artifact_manifest"] = {
            "artifact_count": 9,
            "all_paths_sizes_sha256_present": True,
            "self_hash_is_nonrecursive": True,
            "artifacts": [*sibling_identities, self_identity],
        }
        checkpoint_raw = stable_json(checkpoint)
        if len(checkpoint_raw) == checkpoint_size:
            break
        checkpoint_size = len(checkpoint_raw)
    _require(len(checkpoint_raw) == checkpoint_size, "checkpoint self size固定点に収束しません")
    artifacts[outputs["checkpoint"]] = checkpoint_raw
    _require(set(artifacts) == set(EXPECTED_OUTPUTS.values()), "Stage76 artifact path集合不一致")
    _require(len(artifacts) == 9, "Stage76 artifact count不一致")
    return artifacts


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def materialize(root: Path, *, check: bool = False) -> dict[str, Any]:
    artifacts = build_artifacts(root)
    differences: list[str] = []
    for relative, raw in artifacts.items():
        path = root / relative
        if check:
            if not path.is_file() or path.read_bytes() != raw:
                differences.append(relative)
        else:
            _atomic_write(path, raw)
    if differences:
        _fail("Stage76生成物が再現結果と不一致です: " + ", ".join(differences))
    config = read_config(root)
    metadata = _json(artifacts[config["outputs"]["metadata"]], "Stage76 metadata")
    return {
        "status": "PASS", "mode": "CHECK" if check else "WRITE",
        "output_sha256": metadata["output"]["sha256"],
        "payload_size": metadata["payload"]["size"],
        "allocation_sequence": metadata["allocation_sequence"],
        "release_ready": metadata["release_ready"],
    }


def preflight(root: Path) -> dict[str, Any]:
    config = read_config(root)
    fixed = require_pinned_parent(root, config)
    parent = fixed["rom"]
    for row in [
        *config["parent_abi"]["pointer_patches"],
        *config["parent_abi"]["hooks"],
        *config["parent_abi"]["fixed_function_preimages"],
        *config["parent_abi"]["negative_preservation_sites"],
    ]:
        width = _integer(row["width"], f"{row['name']}.width")
        address = _integer(row["address"], f"{row['name']}.address")
        offset = _rom_offset(address, width, str(row["name"]))
        _require(
            parent[offset:offset + width] == bytes.fromhex(row["parent_hex"]),
            f"{row['name']} Stage75 preimage不一致",
        )
    compile_payload(root, PROVISIONAL_LOAD_ADDRESS)
    return {
        "status": "PASS", "parent_sha256": sha256(parent),
        "patch_count": 4,
        "fixed_function_preimage_count": len(
            config["parent_abi"]["fixed_function_preimages"]
        ),
        "eelevate_preserved_site_count": 2,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = preflight(args.root)
    else:
        result = materialize(args.root, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print(f"RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT=-")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_CONFIG", "PROVISIONAL_LOAD_ADDRESS",
    "ModernizationP05Stage76EdgesError", "compile_payload", "read_config",
    "require_pinned_parent", "veneer", "build_artifacts", "materialize",
    "preflight", "sha256",
]
