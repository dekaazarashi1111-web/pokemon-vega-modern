#!/usr/bin/env python3
"""Stage76を親にBattle Circus特性抑制adapterのStage77を生成する。"""

from __future__ import annotations

import argparse
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
TASK = "USER-MODERNIZATION-P05-STAGE77-CIRCUS-SUPPRESSION"
STAGE = 77
ROM_SIZE = 32 * 1024 * 1024
DEFAULT_CONFIG = Path("config/modernization_p05_stage77_suppression.json")
PROVISIONAL_LOAD_ADDRESS = 0x095E0000
EXPECTED_STAGE76_COMMIT = "cbf98eddf712ee677eef011e6fc106a67e536c08"
EXPECTED_PARENT_ALLOCATION_COUNT = 80
EXPECTED_PARENT_LAST_SEQUENCE = 79
EXPECTED_NEW_SEQUENCE = 80
EXPECTED_HOOK_COUNT = 29
EXPECTED_SURFACE_COUNT = 33
_SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")

EXPECTED_PARENT_IDENTITY = {
    "stage76_commit": EXPECTED_STAGE76_COMMIT,
    "rom": {
        "path": "build/stages/76_modernization_p05_edges.gba",
        "size": 33554432,
        "sha256": "f753f13720aeb5331cfc8a9bf9dd5fd4ad9ac34537356d20d76b73e0100100ac",
    },
    "metadata": {
        "path": "build/stages/76_modernization_p05_edges.json",
        "size": 6059,
        "sha256": "46eb197ba064f4380d6bfd31b16b7ad04bc63599707b72254adde2231aa4d792",
    },
    "allocation": {
        "path": "build/stages/76_modernization_p05_edges_allocation.json",
        "size": 45818,
        "sha256": "64f992d8288b3d861a8e2cc160af880991e76de1eb1ae7dd4081ee4e8c59ae3e",
    },
    "checkpoint": {
        "path": "content/modernization/p05_stage76_edges_checkpoint.json",
        "size": 7018,
        "sha256": "f2951cd2a1cb770d5d325e8f1f596f6251f855e19b2e92d7c05b4f5ce205aa23",
    },
    "tracked_config": {
        "path": "config/modernization_p05_stage76_edges.json",
        "size": 11451,
        "sha256": "98da12855ec46c456e0a01912d33659ce2a4d7d49fb250e131355ff6e48eb26f",
    },
    "contract": {
        "path": "content/modernization/p05_stage76_edges_contract.json",
        "size": 3469,
        "sha256": "e7bb30ccd0fe8540970295d0ad3f9ced6ce6aeb67bfcd1c67ab7cd4cf0ba295b",
    },
    "policy": "FAIL_CLOSED_EXACT_STAGE76_COMMIT_AND_SIX_IDENTITIES",
}

EXPECTED_SOURCE_PINS = {
    "fixed_cfru_jp_commit": "e24a16fe39e27ae162faf5b78596d1f3df18489d",
    "rom_regions": {
        "path": "config/rom_regions.csv", "size": 513,
        "sha256": "f5dcb0ecf2f726bfff1e9c8382204e79b1354ee9071f8d9ac00a83de7a9b3553",
    },
    "stage72_config": {
        "path": "config/modernization_p05_ability_rom_runtime.json", "size": 8975,
        "sha256": "862fa1e89606a00ee71350c107c53014722392c4cd8c06af93dbcbe405b42cd6",
    },
    "stage72_symbols": {
        "path": "generated/runtime/modernization_p05_ability_rom_runtime_symbols.json", "size": 4341,
        "sha256": "9204f33ab9b6109d94ee7a19f1b6d96f5ab872d576b034bdb46c40b6547af029",
    },
    "stage72_source": {
        "path": "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c", "size": 52635,
        "sha256": "a00e37540d968ecda3c26ab4e7606a7c5efe249621067449921be120ed03a60b",
    },
    "fixed_cfru_battle_util": {
        "path": "vendor/upstream/CFRU-JP/src/battle_util.c", "size": 67724,
        "sha256": "558c9a85d067e984c96bf83fb0c652a58df3b0b5fbf63620e4ea694195458ed3",
    },
    "fixed_cfru_battle_constants": {
        "path": "vendor/upstream/CFRU-JP/include/constants/battle.h", "size": 16608,
        "sha256": "88681a4d9e3f34b8608417adf44f828b8c1a19669bba30e00fe22540e2936fb0",
    },
    "fixed_cfru_attackcanceler": {
        "path": "vendor/upstream/CFRU-JP/src/attackcanceler.c", "size": 43335,
        "sha256": "5344ba9c634786753235ffc6d72cc0c8554930a42991bc81aa04bb1b839f768f",
    },
    "fixed_cfru_set_effect": {
        "path": "vendor/upstream/CFRU-JP/src/set_effect.c", "size": 36110,
        "sha256": "eb05f91b0ce07c7c56000573492b4ea9ef8c7617db0fcc518dfee71af0241096",
    },
    "fixed_cfru_ability_battle_effects": {
        "path": "vendor/upstream/CFRU-JP/src/ability_battle_effects.c", "size": 113039,
        "sha256": "760725330a1c94117de914f880807543ab97d97e502b1166d3278e0061144382",
    },
    "fixed_cfru_build_pokemon": {
        "path": "vendor/upstream/CFRU-JP/src/build_pokemon.c", "size": 138366,
        "sha256": "ac81e3a9a8c7a58105573e6ee2abf62a4b22922e88c6c7d3a1ecdc6c9431e824",
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

EXPECTED_SUPPRESSION_CONTRACT = {
    "ordinary_suppression": {
        "gastro_acid": "ALREADY_SAFE_ACTIVE_ABILITY_MOVED_TO_SUPPRESSED_ABILITIES_AND_RAW_SET_NONE",
        "neutralizing_gas": "ALREADY_SAFE_ACTIVE_ABILITY_MOVED_TO_NEUTRALIZING_GAS_BLOCKED_AND_RAW_SET_NONE",
        "mold_breaker": "ALREADY_SAFE_ONLY_EELEVATE_FLAGGED_AND_IGNORED_ACTIVE_ABILITY_MOVED_TO_DISABLED_MOLD_BREAKER_AND_RAW_SET_NONE",
        "stage77_behavior": "NO_CHANGE",
    },
    "battle_circus_global": {
        "status": "IMPLEMENT",
        "battle_type_flags_address": "0x02022AAC",
        "battle_type_mask": "0x04000000",
        "circus_flags_address": "0x0203DFBC",
        "ability_suppression_mask": "0x80000000",
        "predicate": "(battle_type_flags & 0x04000000) != 0 && (circus_flags & 0x80000000) != 0",
        "suppressed_path": "TAIL_DELEGATE_STAGE72_ORIGINAL_TRAMPOLINE",
        "normal_path": "TAIL_DELEGATE_STAGE72_WRAPPER",
        "unique_hook_count": 29,
        "ability_surface_occurrence_count": 33,
        "ability_hook_counts": {
            "Dragonize": 5, "Eelevate": 12, "Fire Mane": 1,
            "Mega Sol": 11, "Piercing Drill": 3, "Spicy Spray": 1,
        },
    },
    "exclusions": {
        "eelevate_dedicated_switch_ai": "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT",
        "mgba_runtime": "DEFERRED_TO_SINGLE_CUMULATIVE_P05_SMOKE",
        "browt_pombon_gecqua_added": 0,
        "side_change_added": 0,
        "active_play_baseline_changed": False,
        "release_ready": False,
        "full_p05_done": False,
        "done": False,
    },
}

EXPECTED_ALLOCATION = {
    "name": "modernization_p05_stage77_circus_suppression_payload",
    "region": "integration_modules", "alignment": 16,
    "owner": TASK,
    "purpose": "Battle Circus global ability-suppression dispatch for all 29 Stage72 ability hooks",
}

EXPECTED_OUTPUTS = {
    "rom": "build/stages/77_modernization_p05_circus_suppression.gba",
    "metadata": "build/stages/77_modernization_p05_circus_suppression.json",
    "allocation": "build/stages/77_modernization_p05_circus_suppression_allocation.json",
    "incremental_bps": "build/patches/stage76-to-stage77-modernization-p05-circus-suppression.bps",
    "payload": "generated/runtime/modernization_p05_stage77_suppression.bin",
    "symbols": "generated/runtime/modernization_p05_stage77_suppression_symbols.json",
    "audit": "generated/runtime/modernization_p05_stage77_suppression_audit.json",
    "contract": "content/modernization/p05_stage77_suppression_contract.json",
    "checkpoint": "content/modernization/p05_stage77_suppression_checkpoint.json",
}

_HOOK_TUPLES = [
    ("AbilityBattleEffects", "0x090B667C", 12, "Stage77_DispatchAbilityBattleEffects", "9c46014b1847c0460d415309", "Stage72_EntryAbilityBattleEffects", "0x0953410D", "Stage72_OriginalAbilityBattleEffects", "0x0953417D", "u8(u8,u8,u16,u16,u16)", ["Spicy Spray"]),
    ("ProtectAffects", "0x090BC1E8", 12, "Stage77_DispatchProtectAffects", "9c46014b1847c04625415309", "Stage72_EntryProtectAffects", "0x09534125", "Stage72_OriginalProtectAffects", "0x09534199", "u8(u16,u8,u8,u8)", ["Piercing Drill"]),
    ("DoesProtectionMoveBlockMove", "0x090BC4C0", 12, "Stage77_DispatchDoesProtectionMoveBlockMove", "9c46014b1847c04619415309", "Stage72_EntryDoesProtectionMoveBlockMove", "0x09534119", "Stage72_OriginalDoesProtectionMoveBlockMove", "0x095341B5", "u8(u8,u8,u16,u16)", ["Piercing Drill"]),
    ("AccuracyCalc", "0x090BC688", 8, "Stage77_DispatchAccuracyCalc", "004b1847b1315309", "Stage72_AccuracyCalc", "0x095331B1", "Stage72_OriginalAccuracyCalc", "0x09534409", "u32(u16,u8,u8)", ["Mega Sol"]),
    ("VisualAccuracyCalc", "0x090BC6B8", 8, "Stage77_DispatchVisualAccuracyCalc", "004b1847f7315309", "Stage72_VisualAccuracyCalc", "0x095331F7", "Stage72_OriginalVisualAccuracyCalc", "0x09534421", "u32(u16,u8,u8)", ["Mega Sol"]),
    ("VisualAccuracyCalc_NoTarget", "0x090BC7CC", 8, "Stage77_DispatchVisualAccuracyCalcNoTarget", "004b18473d325309", "Stage72_VisualAccuracyCalcNoTarget", "0x0953323D", "Stage72_OriginalVisualAccuracyCalcNoTarget", "0x09534439", "u32(u16,u8)", ["Mega Sol"]),
    ("atk01_accuracycheck", "0x090BCADC", 8, "Stage77_DispatchAtk01AccuracyCheck", "004b184775315309", "Stage72_Atk01AccuracyCheck", "0x09533175", "Stage72_OriginalAtk01AccuracyCheck", "0x095343F1", "void(void)", ["Mega Sol"]),
    ("ModifyGrowthInSun", "0x090C8EF0", 8, "Stage77_DispatchModifyGrowthInSun", "004b184781325309", "Stage72_ModifyGrowthInSun", "0x09533281", "Stage72_OriginalModifyGrowthInSun", "0x09534451", "void(void)", ["Mega Sol"]),
    ("NonInvasiveCheckGrounding", "0x090D42F8", 12, "Stage77_DispatchNonInvasiveCheckGrounding", "9c46014b1847c04631415309", "Stage72_EntryNonInvasiveCheckGrounding", "0x09534131", "Stage72_OriginalNonInvasiveCheckGrounding", "0x095341D1", "u8(u8,u16,u8,u8,u8)", ["Eelevate"]),
    ("CheckMonGrounding", "0x090D43D4", 8, "Stage77_DispatchCheckMonGrounding", "004b18474d385309", "Stage72_CheckMonGrounding", "0x0953384D", "Stage72_OriginalCheckMonGrounding", "0x09534311", "u8(void*)", ["Eelevate"]),
    ("CheckGroundingByDetails", "0x090D445C", 8, "Stage77_DispatchCheckGroundingByDetails", "004b1847a5385309", "Stage72_CheckGroundingByDetails", "0x095338A5", "Stage72_OriginalCheckGroundingByDetails", "0x0953432D", "u8(u16,u16,u16)", ["Eelevate"]),
    ("CheckGrounding", "0x090D4718", 8, "Stage77_DispatchCheckGrounding", "004b1847b1375309", "Stage72_CheckGrounding", "0x095337B1", "Stage72_OriginalCheckGrounding", "0x095342F5", "u8(u8)", ["Eelevate"]),
    ("AttacksThisTurn", "0x090D657C", 8, "Stage77_DispatchAttacksThisTurn", "004b184769375309", "Stage72_AttacksThisTurn", "0x09533769", "Stage72_OriginalAttacksThisTurn", "0x095342D9", "u8(u8,u16)", ["Mega Sol"]),
    ("atk49_moveend", "0x090DF7A0", 8, "Stage77_DispatchAtk49MoveEnd", "004b18472d3f5309", "Stage72_Atk49MoveEnd", "0x09533F2D", "Stage72_OriginalAtk49MoveEnd", "0x095343A5", "void(void)", ["Eelevate"]),
    ("AdjustBasePower", "0x090E3130", 8, "Stage77_DispatchAdjustBasePower", "004b1847d1335309", "Stage72_AdjustBasePower", "0x095333D1", "Stage72_OriginalAdjustBasePower", "0x09534279", "u16(void*,u16)", ["Dragonize", "Fire Mane"]),
    ("atk4A_typecalc2", "0x090E4780", 8, "Stage77_DispatchAtk4ATypeCalc2", "004b1847753e5309", "Stage72_Atk4ATypeCalc2", "0x09533E75", "Stage72_OriginalAtk4ATypeCalc2", "0x0953438D", "void(void)", ["Eelevate"]),
    ("atk06_typecalc", "0x090E4A80", 8, "Stage77_DispatchAtk06TypeCalc", "004b18478d3d5309", "Stage72_Atk06TypeCalc", "0x09533D8D", "Stage72_OriginalAtk06TypeCalc", "0x09534375", "void(void)", ["Eelevate"]),
    ("GetMoveTypeSpecialPostAbility", "0x090E53B4", 8, "Stage77_DispatchGetMoveTypeSpecialPostAbility", "004b184775335309", "Stage72_GetMoveTypeSpecialPostAbility", "0x09533375", "Stage72_OriginalGetMoveTypeSpecialPostAbility", "0x09534241", "u8(u16,u16,u8)", ["Dragonize"]),
    ("GetExceptionMoveType", "0x090E5414", 8, "Stage77_DispatchGetExceptionMoveType", "004b184789365309", "Stage72_GetExceptionMoveType", "0x09533689", "Stage72_OriginalGetExceptionMoveType", "0x095342A9", "u8(u8,u16)", ["Dragonize", "Mega Sol"]),
    ("GetMonExceptionMoveType", "0x090E5794", 8, "Stage77_DispatchGetMonExceptionMoveType", "004b18470d375309", "Stage72_GetMonExceptionMoveType", "0x0953370D", "Stage72_OriginalGetMonExceptionMoveType", "0x095342C1", "u8(void*,u16)", ["Dragonize", "Mega Sol"]),
    ("GetMoveTypeSpecialPreAbility", "0x090E59D0", 8, "Stage77_DispatchGetMoveTypeSpecialPreAbility", "004b1847dd325309", "Stage72_GetMoveTypeSpecialPreAbility", "0x095332DD", "Stage72_OriginalGetMoveTypeSpecialPreAbility", "0x0953425D", "u8(u16,u8,void*)", ["Dragonize"]),
    ("VisualTypeCalc.part.0", "0x090E5A60", 8, "Stage77_DispatchVisualTypeCalcPart", "004b1847353a5309", "Stage72_VisualTypeCalcPart", "0x09533A35", "Stage72_OriginalVisualTypeCalcPart", "0x0953435D", "u8(u16,u8,u8)", ["Eelevate"]),
    ("AI_TypeCalc.part.0", "0x090E5ECC", 12, "Stage77_DispatchAITypeCalcPart", "9c46014b1847c04649415309", "Stage72_EntryAITypeCalcPart", "0x09534149", "Stage72_OriginalAITypeCalcPart", "0x09534209", "u8(u16,u8,u8,void*)", ["Eelevate"]),
    ("AI_SpecialTypeCalc", "0x090E6278", 8, "Stage77_DispatchAISpecialTypeCalc", "004b1847d9395309", "Stage72_AISpecialTypeCalc", "0x095339D9", "Stage72_OriginalAISpecialTypeCalc", "0x09534345", "u8(u16,u8,u8)", ["Eelevate"]),
    ("TypeCalc", "0x090E66D4", 12, "Stage77_DispatchTypeCalc", "9c46014b1847c0463d415309", "Stage72_EntryTypeCalc", "0x0953413D", "Stage72_OriginalTypeCalc", "0x095341ED", "u8(u16,u8,u8,void*,u8)", ["Eelevate"]),
    ("CalcVisualBasePower", "0x090E8064", 12, "Stage77_DispatchCalcVisualBasePower", "9c46014b1847c04655415309", "Stage72_EntryCalcVisualBasePower", "0x09534155", "Stage72_OriginalCalcVisualBasePower", "0x09534225", "u16(u8,u8,u16,u8)", ["Mega Sol"]),
    ("CalculateBaseDamage", "0x090E83D4", 8, "Stage77_DispatchCalculateBaseDamage", "004b1847c5345309", "Stage72_CalculateBaseDamage", "0x095334C5", "Stage72_OriginalCalculateBaseDamage", "0x09534291", "s32(void*)", ["Mega Sol", "Piercing Drill"]),
    ("atkC0_recoverbasedonsunlight", "0x0910C1EC", 8, "Stage77_DispatchRecoverBasedOnSunlight", "004b1847d13f5309", "Stage72_RecoverBasedOnSunlight", "0x09533FD1", "Stage72_OriginalRecoverBasedOnSunlight", "0x095343D5", "void(void)", ["Mega Sol"]),
    ("SetMoveEffect2", "0x0912B964", 8, "Stage77_DispatchSetMoveEffect2", "004b1847f53e5309", "Stage72_SetMoveEffect2", "0x09533EF5", "Stage72_OriginalSetMoveEffect2", "0x095343BD", "u8(void)", ["Eelevate"]),
]


def _expected_hooks() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (name, address, width, target, parent_hex, normal_name, normal_address,
         original_name, original_address, abi, abilities) in _HOOK_TUPLES:
        rows.append({
            "name": name, "address": address, "width": width, "target": target,
            "parent_hex": parent_hex,
            "normal_delegate": normal_name, "normal_address": normal_address,
            "suppressed_delegate": original_name,
            "suppressed_address": original_address,
            "continuation_thumb": f"0x{((int(address, 0) + width) | 1):08X}",
            "abi": abi, "abilities": abilities,
            "r3_contract": (
                "ORIGINAL_R3_IN_R12" if width == 12
                else "STAGE72_R3_CLOBBER_VENEER_COMPATIBLE"
            ),
        })
    return rows


EXPECTED_HOOKS = _expected_hooks()
EXPECTED_IS_SUPPRESSED = {
    "name": "IsAbilitySuppressed", "address": "0x090D7BB0", "width": 16,
    "parent_hex": "074b8000c35801201b0107d4054b1b68",
}
EXPECTED_PRESERVED_STAGE76 = [
    {"name": "SolarBeamEffectScript", "address": "0x0903FCA4", "width": 4, "parent_hex": "48585d09"},
    {"name": "AI_CalcDmg", "address": "0x090E9E64", "width": 12, "parent_hex": "9c46014b1847c046c1575d09"},
    {"name": "AIScript_Partner", "address": "0x090A95E4", "width": 12, "parent_hex": "9c46014b1847c046cd575d09"},
    {"name": "RangeMoveCanHurtPartner", "address": "0x090B0048", "width": 8, "parent_hex": "004b1847e1575d09"},
]
EXPECTED_NEGATIVE_SITES = [
    {"name": "FindMonAbsorberActiveAbilityBlock", "address": "0x090A03E4", "width": 16, "parent_hex": "95235b009b463100280010f0bffa5b46"},
    {"name": "FindMonAbsorberPartyAbilityBlock", "address": "0x090A0426", "width": 12, "parent_hex": "3000984639f007ffe38e0700"},
]

EXPECTED_STAGE76_IMPLEMENTATION_PATHS = {
    "config/modernization_p05_stage76_edges.json",
    "content/modernization/p05_stage76_edges_checkpoint.json",
    "content/modernization/p05_stage76_edges_contract.json",
    "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.c",
    "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.h",
    "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.ld",
    "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges_hooks.S",
    "scripts/build_modernization_p05_stage76_edges.sh",
    "tests/test_modernization_p05_stage76_edges.py",
    "tools/modernization_p05_stage76_edges.py",
}


class ModernizationP05Stage77SuppressionError(RuntimeError):
    """Stage77のidentity、ABI、preimage、allocation違反。"""


def _fail(message: str) -> NoReturn:
    raise ModernizationP05Stage77SuppressionError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def stable_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


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
        isinstance(relative, str) and bool(relative)
        and isinstance(digest, str) and bool(_SHA_RE.fullmatch(digest)),
        f"{label} identity不正",
    )
    path = root / relative
    _require(path.is_file() and not path.is_symlink(), f"{label}が固定通常fileではありません")
    raw = path.read_bytes()
    _require(len(raw) == _integer(contract.get("size"), f"{label}.size"), f"{label} size不一致")
    _require(sha256(raw) == digest, f"{label} SHA-256不一致")
    return raw


def _rom_offset(address: int, width: int, label: str) -> int:
    offset = address - GBA_ROM_BASE
    _require(0 <= offset <= ROM_SIZE - width, f"{label}がROM範囲外")
    return offset


def circus_global_suppressed(battle_type_flags: int, circus_flags: int) -> bool:
    """Assembly gateと同じ、bank非依存のBattle Circus全特性抑制判定。"""
    return bool((battle_type_flags & 0x04000000) and (circus_flags & 0x80000000))


def selected_delegate(row: Mapping[str, Any], battle_type_flags: int, circus_flags: int) -> int:
    key = "suppressed_address" if circus_global_suppressed(battle_type_flags, circus_flags) else "normal_address"
    return _integer(row[key], f"{row.get('name')}.{key}")


def read_config(root: Path, relative: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    _require(path.is_file() and not path.is_symlink(), f"Stage77 configが固定通常fileではありません: {path}")
    config = _json(path.read_bytes(), "Stage77 config")
    _require(
        (config.get("schema_version"), config.get("task"), config.get("stage"))
        == (SCHEMA_VERSION, TASK, STAGE), "Stage77 schema/task/stage不一致",
    )
    _require(config.get("status") == "STAGE76_IDENTITY_PINNED", "Stage77 status不正")
    _require(config.get("parent_identity") == EXPECTED_PARENT_IDENTITY, "Stage76 parent identity exact集合不一致")
    _require(config.get("source_pins") == EXPECTED_SOURCE_PINS, "Stage77 source pin exact集合不一致")
    _require(config.get("suppression_contract") == EXPECTED_SUPPRESSION_CONTRACT, "Stage77 suppression contract不一致")
    _require(config.get("allocation") == EXPECTED_ALLOCATION, "Stage77 allocation declaration不一致")
    _require(config.get("outputs") == EXPECTED_OUTPUTS, "Stage77 output path exact集合不一致")
    abi = config.get("parent_abi")
    _require(isinstance(abi, dict), "Stage77 parent_abi不正")
    _require(abi.get("is_ability_suppressed") == EXPECTED_IS_SUPPRESSED, "IsAbilitySuppressed preimage不一致")
    _require(abi.get("hooks") == EXPECTED_HOOKS, "Stage77 29 hook exact集合不一致")
    _require(abi.get("preserved_stage76_patches") == EXPECTED_PRESERVED_STAGE76, "Stage76 preserved patch集合不一致")
    _require(abi.get("negative_preservation_sites") == EXPECTED_NEGATIVE_SITES, "Eelevate pending site集合不一致")
    _require(len(EXPECTED_HOOKS) == EXPECTED_HOOK_COUNT, "内部hook count不一致")
    names = [str(row["name"]) for row in EXPECTED_HOOKS]
    addresses = [_integer(row["address"], f"{row['name']}.address") for row in EXPECTED_HOOKS]
    targets = [str(row["target"]) for row in EXPECTED_HOOKS]
    _require(len(set(names)) == len(set(addresses)) == len(set(targets)) == EXPECTED_HOOK_COUNT, "Stage77 hook一意性不一致")
    occupied: list[tuple[int, int, str]] = []
    for row in EXPECTED_HOOKS:
        width = _integer(row["width"], f"{row['name']}.width")
        address = _integer(row["address"], f"{row['name']}.address")
        _require(width in {8, 12}, f"{row['name']} width不正")
        _require(len(bytes.fromhex(str(row["parent_hex"]))) == width, f"{row['name']} preimage width不一致")
        _require(_integer(row["continuation_thumb"], f"{row['name']}.continuation") == ((address + width) | 1), f"{row['name']} continuation不一致")
        _require(
            row["r3_contract"] == ("ORIGINAL_R3_IN_R12" if width == 12 else "STAGE72_R3_CLOBBER_VENEER_COMPATIBLE"),
            f"{row['name']} r3 contract不一致",
        )
        start = _rom_offset(address, width, str(row["name"]))
        occupied.append((start, start + width, str(row["name"])))
    for left, right in zip(sorted(occupied), sorted(occupied)[1:]):
        _require(right[0] >= left[1], f"Stage77 hook重複: {left[2]} / {right[2]}")
    counts: dict[str, int] = {}
    for row in EXPECTED_HOOKS:
        for ability in row["abilities"]:
            counts[ability] = counts.get(ability, 0) + 1
    _require(counts == EXPECTED_SUPPRESSION_CONTRACT["battle_circus_global"]["ability_hook_counts"], "特性surface count不一致")
    _require(sum(counts.values()) == EXPECTED_SURFACE_COUNT, "特性surface total不一致")
    return config


def require_pinned_parent(root: Path, config: Mapping[str, Any]) -> dict[str, bytes]:
    parent = config["parent_identity"]
    commit = str(parent["stage76_commit"])
    _require(bool(_COMMIT_RE.fullmatch(commit)) and commit == EXPECTED_STAGE76_COMMIT, "Stage76 commit不正")
    result = subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _require(result.returncode == 0, "Stage76 commit object不存在")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _require(ancestor.returncode == 0, "Stage76 commitがHEAD ancestorではありません")
    changed = subprocess.run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _require(changed.returncode == 0 and EXPECTED_STAGE76_IMPLEMENTATION_PATHS <= set(changed.stdout.splitlines()), "Stage76 commit implementation path不足")
    fixed = {
        key: _fixed_raw(root, parent[key], f"Stage76 {key}")
        for key in ("rom", "metadata", "allocation", "checkpoint", "tracked_config", "contract")
    }
    for key, identity in config["source_pins"].items():
        if isinstance(identity, dict):
            fixed[key] = _fixed_raw(root, identity, key)
    upstream = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root / "vendor/upstream/CFRU-JP", text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _require(upstream.returncode == 0 and upstream.stdout.strip() == config["source_pins"]["fixed_cfru_jp_commit"], "CFRU-JP HEAD pin不一致")
    for key in ("checkpoint", "tracked_config", "contract"):
        relative = parent[key]["path"]
        committed = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _require(committed.returncode == 0 and committed.stdout == fixed[key], f"Stage76 commit→{key} cross-link不一致")
    metadata = _json(fixed["metadata"], "Stage76 metadata")
    allocation = _json(fixed["allocation"], "Stage76 allocation")
    checkpoint = _json(fixed["checkpoint"], "Stage76 checkpoint")
    parent_config = _json(fixed["tracked_config"], "Stage76 config")
    rom_identity = dict(parent["rom"])
    rom_identity["crc32"] = f"{zlib.crc32(fixed['rom']) & 0xFFFFFFFF:08X}"
    _require(metadata.get("stage") == checkpoint.get("stage") == parent_config.get("stage") == 76, "Stage76 internal stage不一致")
    _require(metadata.get("output") == checkpoint.get("output") == rom_identity, "Stage76 ROM identity cross-link不一致")
    artifact_rows = checkpoint.get("artifact_manifest", {}).get("artifacts")
    _require(isinstance(artifact_rows, list), "Stage76 checkpoint artifact manifest不正")
    artifacts_by_path = {str(row.get("path")): row for row in artifact_rows}
    for key in ("rom", "metadata", "allocation", "contract"):
        identity = parent[key]
        artifact = artifacts_by_path.get(str(identity["path"]))
        _require(
            isinstance(artifact, dict)
            and artifact.get("size") == identity["size"]
            and artifact.get("sha256") == identity["sha256"]
            and artifact.get("sha256_scope") == "WHOLE_FILE",
            f"Stage76 checkpoint→{key} identity不一致",
        )
    rows = allocation.get("allocations")
    _require(isinstance(rows, list) and len(rows) == EXPECTED_PARENT_ALLOCATION_COUNT, "Stage76 allocation count不一致")
    _require([row.get("sequence") for row in rows] == list(range(EXPECTED_PARENT_ALLOCATION_COUNT)), "Stage76 allocation sequence不連続")
    _require(rows[-1].get("sequence") == EXPECTED_PARENT_LAST_SEQUENCE and metadata.get("allocation_sequence") == EXPECTED_PARENT_LAST_SEQUENCE, "Stage76 terminal allocation不一致")
    _require(metadata.get("allocation") is None or metadata.get("allocation") == rows[-1], "Stage76 metadata allocation row不一致")
    _require(checkpoint.get("payload", {}).get("allocation_sequence") == EXPECTED_PARENT_LAST_SEQUENCE, "Stage76 checkpoint payload sequence不一致")
    parent_outputs = parent_config.get("outputs", {})
    _require(
        parent_outputs.get("rom") == parent["rom"]["path"]
        and parent_outputs.get("metadata") == parent["metadata"]["path"]
        and parent_outputs.get("allocation") == parent["allocation"]["path"]
        and parent_outputs.get("contract") == parent["contract"]["path"]
        and parent_outputs.get("checkpoint") == parent["checkpoint"]["path"],
        "Stage76 config output cross-link不一致",
    )
    active = _json(fixed["active_play_baseline_json"], "active baseline")
    _require(active.get("stage") == 62 and active.get("status") == "ACTIVE", "active baseline Stage62不一致")
    _validate_source_semantics(fixed)
    _validate_stage72_abi(fixed, config)
    return fixed


def _validate_source_semantics(fixed: Mapping[str, bytes]) -> None:
    battle_util = fixed["fixed_cfru_battle_util"].decode("utf-8")
    battle_constants = fixed["fixed_cfru_battle_constants"].decode("utf-8")
    attack = fixed["fixed_cfru_attackcanceler"].decode("utf-8")
    effect = fixed["fixed_cfru_set_effect"].decode("utf-8")
    ability = fixed["fixed_cfru_ability_battle_effects"].decode("utf-8")
    build = fixed["fixed_cfru_build_pokemon"].decode("utf-8")
    stage72 = fixed["stage72_source"].decode("utf-8")
    for token in (
        "bool8 IsAbilitySuppressed(u8 bank)", "BATTLE_CIRCUS_ABILITY_SUPPRESSION",
        "gNewBS->SuppressedAbilities[bank]", "gNewBS->neutralizingGasBlockedAbilities[bank]",
        "gNewBS->DisabledMoldBreakerAbilities[bank]",
    ):
        _require(token in battle_util, f"CFRU suppression根拠不足: {token}")
    _require(
        "#define BATTLE_TYPE_BATTLE_CIRCUS" in battle_constants
        and "0x4000000" in battle_constants
        and "#define BATTLE_CIRCUS_ABILITY_SUPPRESSION" in battle_constants
        and "0x80000000" in battle_constants,
        "Battle Circus flag mask根拠不足",
    )
    _require("gNewBS->DisabledMoldBreakerAbilities[i] = gBattleMons[i].ability" in attack and "gBattleMons[i].ability = ABILITY_NONE" in attack, "Mold Breaker raw-zero根拠不足")
    _require("gNewBS->SuppressedAbilities[gEffectBank] = *defAbilityLoc" in effect and "*defAbilityLoc = 0" in effect, "Gastro Acid raw-zero根拠不足")
    _require("gNewBS->neutralizingGasBlockedAbilities[i] = *abilityLoc" in ability and "*abilityLoc = 0" in ability, "Neutralizing Gas raw-zero根拠不足")
    _require("u16 GetMonAbility(const struct Pokemon* mon)" in build and "BATTLE_CIRCUS_ABILITY_SUPPRESSION" in build, "Circus party ability根拠不足")
    _require("static Stage72U16 Stage72_BattleMonAbility" in stage72 and "Stage72_BattleMonAbility(" in stage72, "Stage72 raw ability根拠不足")


def _validate_stage72_abi(fixed: Mapping[str, bytes], config: Mapping[str, Any]) -> None:
    stage72_config = _json(fixed["stage72_config"], "Stage72 config")
    stage72_symbols = _json(fixed["stage72_symbols"], "Stage72 symbols").get("symbols")
    _require(isinstance(stage72_symbols, dict), "Stage72 symbols不正")
    source_hooks = stage72_config.get("hooks")
    _require(isinstance(source_hooks, list) and len(source_hooks) == EXPECTED_HOOK_COUNT, "Stage72 hook count不一致")
    by_name = {str(row.get("name")): row for row in source_hooks}
    _require(len(by_name) == EXPECTED_HOOK_COUNT, "Stage72 hook name重複")
    for row in config["parent_abi"]["hooks"]:
        source = by_name.get(str(row["name"]))
        _require(source is not None, f"Stage72 hook不存在: {row['name']}")
        _require(source.get("address") == row["address"] and source.get("width") == row["width"] and source.get("target") == row["normal_delegate"], f"Stage72 hook ABI不一致: {row['name']}")
        _require(stage72_symbols.get(row["normal_delegate"]) == row["normal_address"], f"Stage72 normal symbol不一致: {row['name']}")
        _require(stage72_symbols.get(row["suppressed_delegate"]) == row["suppressed_address"], f"Stage72 original symbol不一致: {row['name']}")
    abilities = stage72_config.get("abilities")
    _require(
        isinstance(abilities, list)
        and [(row.get("id"), row.get("mold_breaker_ignored")) for row in abilities]
        == [(312, 0), (313, 1), (314, 0), (315, 0), (316, 0), (317, 0)],
        "Stage72 Mold Breaker flag集合不一致",
    )


def _run(command: Sequence[str], root: Path, label: str) -> str:
    result = subprocess.run(list(command), cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        _fail(f"{label}失敗\n{result.stdout}\n{result.stderr}")
    return result.stdout


@dataclass(frozen=True)
class CompiledPayload:
    code: bytes
    symbols: dict[str, int]
    sizes: dict[str, int]
    compiler: str
    disassembly: str


def compile_payload(root: Path, load_address: int, hooks: Sequence[Mapping[str, Any]] | None = None) -> CompiledPayload:
    hook_rows = list(EXPECTED_HOOKS if hooks is None else hooks)
    gcc = shutil.which("arm-none-eabi-gcc")
    objcopy = shutil.which("arm-none-eabi-objcopy")
    nm = shutil.which("arm-none-eabi-nm")
    objdump = shutil.which("arm-none-eabi-objdump")
    _require(bool(gcc and objcopy and nm and objdump), "arm-none-eabi toolchainがPATHにありません")
    source = root / "overlays/modernization_p05_stage77_suppression"
    common = ["-mthumb", "-mcpu=arm7tdmi", "-mthumb-interwork"]
    with tempfile.TemporaryDirectory(prefix="stage77-p05-suppression-") as temporary:
        work = Path(temporary)
        obj = work / "runtime.o"
        elf = work / "runtime.elf"
        binary = work / "runtime.bin"
        _run([str(gcc), *common, "-c", str(source / "modernization_p05_stage77_suppression.S"), "-o", str(obj)], root, "Stage77 ASM compile")
        _run([str(gcc), "-nostdlib", *common, f"-Wl,--defsym=STAGE77_LOAD_ADDRESS=0x{load_address:08X}", f"-Wl,-T,{source / 'modernization_p05_stage77_suppression.ld'}", str(obj), "-o", str(elf)], root, "Stage77 link")
        _run([str(objcopy), "-O", "binary", str(elf), str(binary)], root, "Stage77 objcopy")
        symbol_text = _run([str(nm), "-n", "-S", str(elf)], root, "Stage77 nm")
        disassembly = _run([str(objdump), "-d", str(elf)], root, "Stage77 objdump")
        symbols: dict[str, int] = {}
        sizes: dict[str, int] = {}
        for line in symbol_text.splitlines():
            fields = line.split()
            if len(fields) == 4 and all(character in "0123456789abcdefABCDEF" for character in fields[0]):
                symbols[fields[3]] = int(fields[0], 16)
                sizes[fields[3]] = int(fields[1], 16)
        code = binary.read_bytes()
        compiler = _run([str(gcc), "--version"], root, "gcc version").splitlines()[0]
    required = {"Stage77_RuntimeProbe", *(str(row["target"]) for row in hook_rows)}
    _require(required <= symbols.keys(), "Stage77 required symbol不足")
    _require(len([name for name in symbols if name.startswith("Stage77_Dispatch")]) == EXPECTED_HOOK_COUNT, "Stage77 dispatcher symbol数不一致")
    for row in hook_rows:
        name = str(row["target"])
        offset = symbols[name] - load_address
        size = sizes.get(name, 0)
        _require(size in {40, 48}, f"{name} stub size不正: {size}")
        section = code[offset:offset + size]
        for value, label in (
            (0x02022AAC, "battle type flags"),
            (0x0203DFBC, "circus flags"),
            (_integer(row["normal_address"], f"{name}.normal"), "normal delegate"),
            (_integer(row["suppressed_address"], f"{name}.suppressed"), "suppressed delegate"),
        ):
            _require(struct.pack("<I", value) in section, f"{name} {label} literal不足")
        expected_size = 48 if row["width"] == 12 else 40
        _require(size == expected_size, f"{name} ABI stub size不一致")
    _require(0 < len(code) < 0x10000, f"Stage77 payload size不正: {len(code)}")
    return CompiledPayload(code=code, symbols=symbols, sizes=sizes, compiler=compiler, disassembly=disassembly)


def _previous_requests(allocation: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = allocation.get("allocations")
    _require(isinstance(rows, list) and len(rows) == EXPECTED_PARENT_ALLOCATION_COUNT, "Stage76 allocation count不一致")
    _require([row.get("sequence") for row in rows] == list(range(EXPECTED_PARENT_ALLOCATION_COUNT)), "Stage76 allocation sequence不連続")
    requests: list[dict[str, Any]] = []
    for row in rows:
        request = {key: row[key] for key in ("name", "region", "size", "alignment", "owner", "purpose", "content_sha256")}
        if row.get("placement") == "EXPLICIT":
            request["start"] = row["start"]
        else:
            _require(row.get("placement") == "FIRST_FIT", "Stage76 allocation placement不正")
        requests.append(request)
    return requests


def _allocate(root: Path, config: Mapping[str, Any], previous: Mapping[str, Any], size: int, digest: str) -> tuple[dict[str, Any], dict[str, Any]]:
    declaration = config["allocation"]
    requests = _previous_requests(previous)
    requests.append({
        "name": declaration["name"], "region": declaration["region"], "size": size,
        "alignment": declaration["alignment"], "owner": declaration["owner"],
        "purpose": declaration["purpose"], "content_sha256": digest,
    })
    report = build_allocation_report_from_csv(root / config["source_pins"]["rom_regions"]["path"], requests)
    rows = report.get("allocations")
    _require(report.get("summaries", {}).get("overlap_count") == 0, "Stage77 allocator overlap")
    _require(isinstance(rows, list) and len(rows) == EXPECTED_NEW_SEQUENCE + 1, "Stage77 allocation count不一致")
    _require(rows[:EXPECTED_PARENT_ALLOCATION_COUNT] == previous.get("allocations"), "Stage77 allocatorが親first80 rowを変更")
    row = rows[-1]
    _require(row.get("sequence") == EXPECTED_NEW_SEQUENCE and row.get("name") == declaration["name"] and row.get("placement") == "FIRST_FIT", "Stage77 terminal allocation不一致")
    return row, report


def veneer(width: int, target: int, address: int = 0) -> bytes:
    target |= 1
    if width == 8:
        return struct.pack("<HHI", 0x4B00, 0x4718, target)
    if width == 12:
        if address & 2:
            return struct.pack("<HHHIH", 0x469C, 0x4B00, 0x4718, target, 0x46C0)
        return struct.pack("<HHHHI", 0x469C, 0x4B01, 0x4718, 0x46C0, target)
    _fail(f"未対応veneer width: {width}")


def _patch_exact(image: bytearray, address: int, expected: bytes, replacement: bytes, label: str) -> dict[str, Any]:
    _require(len(expected) == len(replacement), f"{label} replacement width不一致")
    offset = _rom_offset(address, len(expected), label)
    actual = bytes(image[offset:offset + len(expected)])
    _require(actual == expected, f"{label} parent preimage不一致: {actual.hex()} != {expected.hex()}")
    image[offset:offset + len(replacement)] = replacement
    return {"name": label, "address": f"0x{address:08X}", "width": len(expected), "before_hex": expected.hex(), "after_hex": replacement.hex()}


def _rom_diff_allowlist(parent: bytes, result: bytes, intervals: Sequence[tuple[int, int, str]]) -> dict[str, Any]:
    ordered = sorted(intervals)
    cursor = 0
    changed_inside = 0
    rows: list[dict[str, Any]] = []
    for start, end, name in ordered:
        _require(0 <= start < end <= ROM_SIZE and start >= cursor, f"{name} allowlist不正/重複")
        _require(parent[cursor:start] == result[cursor:start], f"ROM差分がallowlist外: 0x{cursor:X}..0x{start:X}")
        changed = sum(left != right for left, right in zip(parent[start:end], result[start:end]))
        changed_inside += changed
        rows.append({"name": name, "start": start, "end_exclusive": end, "size": end - start, "changed_bytes": changed})
        cursor = end
    _require(parent[cursor:] == result[cursor:], f"ROM差分がallowlist外: 0x{cursor:X}..EOF")
    return {"allowed_intervals": rows, "allowlist_interval_count": len(rows), "changed_bytes_inside_allowlist": changed_inside, "changed_bytes_outside_allowlist": 0}


def _implementation_identity(root: Path) -> dict[str, Any]:
    paths = [
        "config/modernization_p05_stage77_suppression.json",
        "tools/modernization_p05_stage77_suppression.py",
        "scripts/build_modernization_p05_stage77_suppression.sh",
        "tests/test_modernization_p05_stage77_suppression.py",
        "overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S",
        "overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.ld",
    ]
    rows: list[dict[str, Any]] = []
    framed = hashlib.sha256()
    for relative in paths:
        raw = (root / relative).read_bytes()
        row = {"path": relative, "size": len(raw), "sha256": sha256(raw)}
        encoded = stable_json(row)
        framed.update(len(encoded).to_bytes(8, "big"))
        framed.update(encoded)
        rows.append(row)
    return {"files": rows, "sha256": framed.hexdigest()}


def _source_identities(root: Path) -> dict[str, dict[str, Any]]:
    base = root / "overlays/modernization_p05_stage77_suppression"
    return {
        path.name: {"size": len(path.read_bytes()), "sha256": sha256(path.read_bytes())}
        for path in sorted(base.iterdir()) if path.is_file()
    }


def build_artifacts(root: Path) -> dict[str, bytes]:
    config = read_config(root)
    fixed = require_pinned_parent(root, config)
    parent = fixed["rom"]
    previous_allocation = _json(fixed["allocation"], "Stage76 allocation")
    provisional = compile_payload(root, PROVISIONAL_LOAD_ADDRESS, config["parent_abi"]["hooks"])
    placement, _ = _allocate(root, config, previous_allocation, len(provisional.code), sha256(provisional.code))
    load_address = GBA_ROM_BASE + int(placement["start"])
    compiled = compile_payload(root, load_address, config["parent_abi"]["hooks"])
    _require(len(compiled.code) == len(provisional.code), "Stage77 relocation payload size drift")
    placement, allocation_report = _allocate(root, config, previous_allocation, len(compiled.code), sha256(compiled.code))
    _require(GBA_ROM_BASE + int(placement["start"]) == load_address, "Stage77 allocation relocation drift")
    image = bytearray(parent)
    start = int(placement["start"])
    _require(bytes(image[start:start + len(compiled.code)]) == b"\xFF" * len(compiled.code), "Stage77 payload preimage非FF")
    image[start:start + len(compiled.code)] = compiled.code
    changes: list[dict[str, Any]] = [{
        "name": "payload", "address": f"0x{load_address:08X}", "width": len(compiled.code),
        "before_sha256": sha256(b"\xFF" * len(compiled.code)), "after_sha256": sha256(compiled.code),
    }]
    for row in config["parent_abi"]["hooks"]:
        symbol = str(row["target"])
        _require(symbol in compiled.symbols, f"dispatcher symbol不足: {symbol}")
        address = _integer(row["address"], f"{symbol}.address")
        width = _integer(row["width"], f"{symbol}.width")
        changes.append(_patch_exact(image, address, bytes.fromhex(row["parent_hex"]), veneer(width, compiled.symbols[symbol], address), str(row["name"])))
    result = bytes(image)
    _require(len(result) == ROM_SIZE, "Stage77 output ROM size不一致")
    _require(sha256(result[start:start + len(compiled.code)]) == sha256(compiled.code), "Stage77 payload ROM slice不一致")
    preserved = [
        config["parent_abi"]["is_ability_suppressed"],
        *config["parent_abi"]["preserved_stage76_patches"],
        *config["parent_abi"]["negative_preservation_sites"],
    ]
    for row in preserved:
        address = _integer(row["address"], f"{row['name']}.address")
        width = _integer(row["width"], f"{row['name']}.width")
        offset = _rom_offset(address, width, str(row["name"]))
        expected = bytes.fromhex(row["parent_hex"])
        _require(parent[offset:offset + width] == result[offset:offset + width] == expected, f"{row['name']} preserved byte変更")
    intervals = [(start, start + len(compiled.code), "payload")]
    for row in config["parent_abi"]["hooks"]:
        offset = _rom_offset(_integer(row["address"], f"{row['name']}.address"), int(row["width"]), str(row["name"]))
        intervals.append((offset, offset + int(row["width"]), str(row["name"])))
    diff_audit = _rom_diff_allowlist(parent, result, intervals)
    implementation = _implementation_identity(root)
    payload_identity = {
        "path": config["outputs"]["payload"], "start": start,
        "load_address": f"0x{load_address:08X}", "size": len(compiled.code),
        "sha256": sha256(compiled.code), "allocation_sequence": EXPECTED_NEW_SEQUENCE,
    }
    output_identity = {
        "path": config["outputs"]["rom"], "size": len(result), "sha256": sha256(result),
        "crc32": f"{zlib.crc32(result) & 0xFFFFFFFF:08X}",
    }
    parent_rows_hash = sha256(stable_json(previous_allocation["allocations"]))
    new_rows_hash = sha256(stable_json(allocation_report["allocations"][:EXPECTED_PARENT_ALLOCATION_COUNT]))
    _require(parent_rows_hash == new_rows_hash, "Stage77 first80 allocation lineage hash不一致")
    allocation_lineage = {
        "parent_count": EXPECTED_PARENT_ALLOCATION_COUNT,
        "parent_last_sequence": EXPECTED_PARENT_LAST_SEQUENCE,
        "new_count": EXPECTED_NEW_SEQUENCE + 1,
        "new_sequence": EXPECTED_NEW_SEQUENCE,
        "first80_all_fields_equal": True,
        "parent_first80_sha256": parent_rows_hash,
        "new_first80_sha256": new_rows_hash,
        "payload_slice_sha256": sha256(result[start:start + len(compiled.code)]),
    }
    bps = create_bps(parent, result, metadata=b"Stage76 to Stage77 P05 Battle Circus suppression")
    _require(apply_bps(parent, bps) == result, "Stage76→77 BPS roundtrip不一致")
    bps_identity = {
        "path": config["outputs"]["incremental_bps"], "size": len(bps), "sha256": sha256(bps),
        "source_sha256": sha256(parent), "target_sha256": sha256(result), "round_trip": True,
    }
    checks = {
        "parent_stage76_commit_and_six_identities": "PASS",
        "stage72_symbol_and_hook_abi_exact": "PASS",
        "stage72_unique_hooks_repointed": EXPECTED_HOOK_COUNT,
        "stage72_ability_surface_occurrences_guarded": EXPECTED_SURFACE_COUNT,
        "ordinary_gastro_neutralizing_gas_mold_breaker_semantics_unchanged": "PASS",
        "battle_circus_global_suppression_delegates_original": "PASS",
        "normal_path_delegates_stage72_wrapper": "PASS",
        "r3_saved_veneer_count": sum(row["width"] == 12 for row in EXPECTED_HOOKS),
        "stage76_pointer_and_three_hooks_preserved": "PASS",
        "eelevate_unsafe_switch_hooks_installed": 0,
        "browt_pombon_gecqua_added": 0,
        "side_change_added": 0,
        "active_play_baseline_unchanged": "PASS",
        "allocator_overlap": "PASS",
        "parent_first80_rows_all_fields_preserved": "PASS",
        "rom_diff_outside_payload_plus_29_hooks": 0,
        "bps_roundtrip": "PASS",
        "mgba_runtime": "NOT_RUN",
    }
    parent_identity = {
        "stage": 76, "commit": EXPECTED_STAGE76_COMMIT,
        "path": config["parent_identity"]["rom"]["path"], "size": len(parent),
        "sha256": sha256(parent), "crc32": f"{zlib.crc32(parent) & 0xFFFFFFFF:08X}",
    }
    active_baseline = {
        "stage": 62, "unchanged": True,
        "json": dict(config["source_pins"]["active_play_baseline_json"]),
        "markdown": dict(config["source_pins"]["active_play_baseline_md"]),
    }
    remaining = [
        "Eelevate dedicated switch AI: full Ground/Thousand Arrows/grounding/Gravity/Mold Breaker/Ability Shield semantics",
        "single cumulative P05 mGBA smoke on the latest ROM",
    ]
    dispatch_rows = [{
        "hook": row["name"], "address": row["address"], "width": row["width"],
        "abi": row["abi"], "r3_contract": row["r3_contract"],
        "abilities": row["abilities"], "normal_delegate": row["normal_delegate"],
        "normal_address": row["normal_address"],
        "suppressed_delegate": row["suppressed_delegate"],
        "suppressed_address": row["suppressed_address"],
    } for row in config["parent_abi"]["hooks"]]
    symbols_json = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "load_address": f"0x{load_address:08X}", "compiler": compiled.compiler,
        "payload_size": len(compiled.code), "payload_sha256": sha256(compiled.code),
        "symbols": {key: f"0x{value:08X}" for key, value in sorted(compiled.symbols.items()) if key.startswith("Stage77_")},
    }
    audit = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "BATTLE_CIRCUS_GLOBAL_SUPPRESSION_MATERIALIZED_MGBA_AND_EELEVATE_SWITCH_PENDING",
        "parent": parent_identity, "output": output_identity, "payload": payload_identity,
        "changes": changes, "rom_diff": diff_audit, "allocation_lineage": allocation_lineage,
        "suppression_contract": config["suppression_contract"], "dispatchers": dispatch_rows,
        "checks": checks, "implementation": implementation,
        "active_play_baseline": active_baseline,
        "release_ready": False, "full_p05_done": False, "done": False,
    }
    metadata = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": audit["status"], "parent": parent_identity, "output": output_identity,
        "payload": payload_identity, "allocation_sequence": EXPECTED_NEW_SEQUENCE,
        "allocation": placement, "allocation_lineage": allocation_lineage, "bps": bps_identity,
        "suppression": {
            "battle_circus_global_fixed": True, "ordinary_suppression_changed": False,
            "hook_count": EXPECTED_HOOK_COUNT, "ability_surface_occurrence_count": EXPECTED_SURFACE_COUNT,
        },
        "checks": checks, "remaining_work": remaining,
        "source_identities": _source_identities(root), "implementation": implementation,
        "active_play_baseline": active_baseline, "artifact_count": 9,
        "release_ready": False, "full_p05_done": False, "done": False,
    }
    contract = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": "BATTLE_CIRCUS_SUPPRESSION_CONNECTED_NOT_P05_DONE",
        "parent": parent_identity, "output": output_identity, "payload": payload_identity,
        "allocation_sequence": EXPECTED_NEW_SEQUENCE, "allocation_lineage": allocation_lineage,
        "bps": bps_identity, "suppression_contract": config["suppression_contract"],
        "checks": checks, "pending": remaining,
        "implementation_sha256": implementation["sha256"],
        "active_play_baseline": active_baseline,
        "release_ready": False, "full_p05_done": False, "done": False,
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
    sibling_identities = [{
        "path": relative, "size": len(raw), "sha256": sha256(raw), "sha256_scope": "WHOLE_FILE",
    } for relative, raw in artifacts.items()]
    checkpoint_core = {
        "schema_version": 1, "task": TASK, "stage": STAGE,
        "status": audit["status"], "parent": parent_identity, "output": output_identity,
        "payload": payload_identity, "allocation_sequence": EXPECTED_NEW_SEQUENCE,
        "allocation_lineage": allocation_lineage, "rom_diff": diff_audit,
        "bps": bps_identity, "suppression_contract": config["suppression_contract"],
        "checks": checks, "pending": remaining,
        "implementation_sha256": implementation["sha256"],
        "active_play_baseline": active_baseline,
        "release_ready": False, "full_p05_done": False, "done": False,
    }
    core_sha = sha256(stable_json(checkpoint_core))
    checkpoint_size = 0
    checkpoint_raw = b""
    for _ in range(8):
        checkpoint = dict(checkpoint_core)
        checkpoint["artifact_manifest"] = {
            "artifact_count": 9, "all_paths_sizes_sha256_present": True,
            "self_hash_is_nonrecursive": True,
            "artifacts": [*sibling_identities, {
                "path": outputs["checkpoint"], "size": checkpoint_size,
                "sha256": core_sha, "sha256_scope": "STABLE_JSON_WITHOUT_ARTIFACT_MANIFEST",
            }],
        }
        checkpoint_raw = stable_json(checkpoint)
        if len(checkpoint_raw) == checkpoint_size:
            break
        checkpoint_size = len(checkpoint_raw)
    _require(len(checkpoint_raw) == checkpoint_size, "Stage77 checkpoint self size非収束")
    artifacts[outputs["checkpoint"]] = checkpoint_raw
    _require(set(artifacts) == set(EXPECTED_OUTPUTS.values()) and len(artifacts) == 9, "Stage77 artifact path/count不一致")
    return artifacts


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
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
        _fail("Stage77生成物が再現結果と不一致です: " + ", ".join(differences))
    config = read_config(root)
    metadata = _json(artifacts[config["outputs"]["metadata"]], "Stage77 metadata")
    return {
        "status": "PASS", "mode": "CHECK" if check else "WRITE",
        "output_sha256": metadata["output"]["sha256"],
        "payload_size": metadata["payload"]["size"],
        "allocation_sequence": metadata["allocation_sequence"],
        "hook_count": metadata["suppression"]["hook_count"],
        "release_ready": metadata["release_ready"],
    }


def preflight(root: Path) -> dict[str, Any]:
    config = read_config(root)
    fixed = require_pinned_parent(root, config)
    parent = fixed["rom"]
    for row in [
        *config["parent_abi"]["hooks"], config["parent_abi"]["is_ability_suppressed"],
        *config["parent_abi"]["preserved_stage76_patches"],
        *config["parent_abi"]["negative_preservation_sites"],
    ]:
        width = int(row["width"])
        address = _integer(row["address"], f"{row['name']}.address")
        offset = _rom_offset(address, width, str(row["name"]))
        _require(parent[offset:offset + width] == bytes.fromhex(row["parent_hex"]), f"{row['name']} Stage76 preimage不一致")
    compiled = compile_payload(root, PROVISIONAL_LOAD_ADDRESS, config["parent_abi"]["hooks"])
    return {
        "status": "PASS", "parent_sha256": sha256(parent),
        "hook_count": len(config["parent_abi"]["hooks"]),
        "r3_saved_hook_count": sum(row["width"] == 12 for row in config["parent_abi"]["hooks"]),
        "payload_size": len(compiled.code),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    result = preflight(args.root) if args.preflight else materialize(args.root, check=args.check)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print(f"RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT=-")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_CONFIG", "PROVISIONAL_LOAD_ADDRESS", "EXPECTED_HOOKS",
    "ModernizationP05Stage77SuppressionError", "build_artifacts",
    "circus_global_suppressed", "compile_payload", "materialize", "preflight",
    "read_config", "require_pinned_parent", "selected_delegate", "sha256",
    "stable_json", "veneer",
]
