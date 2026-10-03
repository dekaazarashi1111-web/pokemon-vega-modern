from __future__ import annotations

import copy
import csv
import ctypes
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.modernization_p05_stage76_edges import (
    DEFAULT_CONFIG,
    PROVISIONAL_LOAD_ADDRESS,
    ModernizationP05Stage76EdgesError,
    build_artifacts,
    compile_payload,
    preflight,
    read_config,
    require_pinned_parent,
    sha256,
    stable_json,
    veneer,
)
from tools.release.bps import apply_bps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "overlays/modernization_p05_stage76_edges"
EXPECTED_STAGE75_COMMIT = "595909446b6ad67749c9894b23fdc536f82c638e"
EXPECTED_OUTPUT_PATHS = {
    "build/stages/76_modernization_p05_edges.gba",
    "build/stages/76_modernization_p05_edges.json",
    "build/stages/76_modernization_p05_edges_allocation.json",
    "build/patches/stage75-to-stage76-modernization-p05-edges.bps",
    "generated/runtime/modernization_p05_stage76_edges.bin",
    "generated/runtime/modernization_p05_stage76_edges_symbols.json",
    "generated/runtime/modernization_p05_stage76_edges_audit.json",
    "content/modernization/p05_stage76_edges_contract.json",
    "content/modernization/p05_stage76_edges_checkpoint.json",
}
EXPECTED_POINTERS = [
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
EXPECTED_EELEVATE_SITES = {
    "FindMonAbsorberActiveAbilityBlock": (
        0x090A03E4, bytes.fromhex("95235b009b463100280010f0bffa5b46")
    ),
    "FindMonAbsorberPartyAbilityBlock": (
        0x090A0426, bytes.fromhex("3000984639f007ffe38e0700")
    ),
}


class ModernizationP05Stage76EdgesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = read_config(ROOT, DEFAULT_CONFIG)
        cls.fixed = require_pinned_parent(ROOT, cls.config)
        cls.compiled = compile_payload(ROOT, PROVISIONAL_LOAD_ADDRESS)
        cls.artifacts = build_artifacts(ROOT)
        cls.source = (
            SOURCE_DIR / "modernization_p05_stage76_edges.c"
        ).read_text(encoding="utf-8")
        cls.hooks_source = (
            SOURCE_DIR / "modernization_p05_stage76_edges_hooks.S"
        ).read_text(encoding="utf-8")
        outputs = cls.config["outputs"]
        cls.result = cls.artifacts[outputs["rom"]]
        cls.metadata = json.loads(cls.artifacts[outputs["metadata"]])
        cls.allocation = json.loads(cls.artifacts[outputs["allocation"]])
        cls.audit = json.loads(cls.artifacts[outputs["audit"]])
        cls.contract = json.loads(cls.artifacts[outputs["contract"]])
        cls.checkpoint = json.loads(cls.artifacts[outputs["checkpoint"]])

    def _assert_read_config_rejects(self, mutated: dict) -> None:
        with tempfile.TemporaryDirectory(prefix="stage76-config-mutation-") as temporary:
            path = Path(temporary) / "mutated.json"
            path.write_text(json.dumps(mutated), encoding="utf-8")
            with self.assertRaises(ModernizationP05Stage76EdgesError):
                read_config(ROOT, path)

    def test_exact_config_fixes_pointer_hooks_targets_preimages_and_continuations(self) -> None:
        abi = self.config["parent_abi"]
        self.assertEqual(abi["pointer_patches"], EXPECTED_POINTERS)
        self.assertEqual(abi["hooks"], EXPECTED_HOOKS)
        self.assertEqual(len(abi["fixed_function_preimages"]), 8)
        self.assertEqual(len(abi["negative_preservation_sites"]), 2)
        self.assertEqual(preflight(ROOT)["fixed_function_preimage_count"], 8)
        for row in EXPECTED_HOOKS:
            self.assertEqual(
                int(row["continuation_thumb"], 0),
                (int(row["address"], 0) + row["width"]) | 1,
            )

    def test_config_mutations_fail_closed_independently(self) -> None:
        mutations: list[dict] = []
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["hooks"][0]["target"] = "Stage76_EntryAIScriptPartner"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["hooks"][0]["continuation_thumb"] = "0x090E9E73"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["hooks"][0]["parent_hex"] = "00" * 12
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["pointer_patches"][0]["address"] = "0x0903FCA8"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["fixed_layout"]["DamageCalc_atkAbility_offset"] = "0x12"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_abi"]["negative_preservation_sites"].pop()
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["outputs"]["rom"] = "build/stages/wrong.gba"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["edge_contract"]["mega_sol"]["production_pointer_only"] = False
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["allocation"]["owner"] = "WRONG-OWNER"
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["source_pins"]["fixed_cfru_ai_partner"]["sha256"] = "0" * 64
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["source_pins"]["fixed_cfru_dynamax"]["sha256"] = "0" * 64
        mutations.append(mutated)
        mutated = copy.deepcopy(self.config)
        mutated["parent_identity"]["stage75_commit"] = (
            "e43e1c0888c6c75e648f7d132428c7b57dcd33a4"
        )
        mutations.append(mutated)
        for index, value in enumerate(mutations):
            with self.subTest(mutation=index):
                self._assert_read_config_rejects(value)

    def test_parent_is_exact_stage75_implementation_commit_and_cross_linked(self) -> None:
        self.assertEqual(
            self.config["parent_identity"]["stage75_commit"], EXPECTED_STAGE75_COMMIT
        )
        for key in ("rom", "metadata", "allocation", "checkpoint", "tracked_config"):
            raw = self.fixed[key]
            identity = self.config["parent_identity"][key]
            self.assertEqual(len(raw), identity["size"])
            self.assertEqual(sha256(raw), identity["sha256"])
        ai_partner = self.config["source_pins"]["fixed_cfru_ai_partner"]
        self.assertEqual(len(self.fixed["fixed_cfru_ai_partner"]), ai_partner["size"])
        self.assertEqual(sha256(self.fixed["fixed_cfru_ai_partner"]), ai_partner["sha256"])
        for key in ("fixed_cfru_dynamax", "fixed_cfru_battle_move_effects"):
            identity = self.config["source_pins"][key]
            self.assertEqual(len(self.fixed[key]), identity["size"])
            self.assertEqual(sha256(self.fixed[key]), identity["sha256"])
        for key in ("checkpoint", "tracked_config"):
            path = self.config["parent_identity"][key]["path"]
            committed = subprocess.run(
                ["git", "show", f"{EXPECTED_STAGE75_COMMIT}:{path}"], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(committed.returncode, 0, committed.stderr.decode())
            self.assertEqual(committed.stdout, self.fixed[key])
        parent_metadata = json.loads(self.fixed["metadata"])
        parent_checkpoint = json.loads(self.fixed["checkpoint"])
        parent_allocation = json.loads(self.fixed["allocation"])
        self.assertEqual(parent_metadata["output"], parent_checkpoint["output"])
        self.assertEqual(parent_metadata["allocation"], parent_allocation["allocations"][-1])
        self.assertEqual(parent_checkpoint["payload"]["allocation_sequence"], 78)

    def test_patch_and_fixed_function_preimages_match_parent(self) -> None:
        parent = self.fixed["rom"]
        patch_rows = [*EXPECTED_POINTERS, *EXPECTED_HOOKS]
        fixed_rows = self.config["parent_abi"]["fixed_function_preimages"]
        for row in [*patch_rows, *fixed_rows]:
            expected = bytes.fromhex(row["parent_hex"])
            offset = int(row["address"], 0) - 0x08000000
            self.assertEqual(parent[offset:offset + len(expected)], expected, row["name"])
        for row in patch_rows:
            offset = int(row["address"], 0) - 0x08000000
            self.assertNotEqual(
                self.result[offset:offset + row["width"]],
                parent[offset:offset + row["width"]],
            )
        for row in fixed_rows:
            offset = int(row["address"], 0) - 0x08000000
            self.assertEqual(
                self.result[offset:offset + row["width"]],
                parent[offset:offset + row["width"]],
            )

    def test_mega_sol_uses_production_pointer_and_parent_weather_semantics(self) -> None:
        symbols = self.compiled.symbols
        code = self.compiled.code
        script = symbols["Stage76_BattleScriptSolarBeam"] - PROVISIONAL_LOAD_ADDRESS
        dispatch = symbols["Stage76_DispatchMegaSolSolarBeam"] | 1
        self.assertEqual(code[script:script + 5], b"\xF8" + struct.pack("<I", dispatch))
        popup = symbols["Stage76_BattleScriptMegaSolPopup"] - PROVISIONAL_LOAD_ADDRESS
        self.assertEqual(
            code[popup:popup + 18],
            bytes.fromhex("4100120009391000410f1200092810510009"),
        )
        self.assertNotIn("AttacksThisTurn", self.source)
        self.assertIn("target - 5u", self.source)
        weather = self.source.split("static Stage76U8 Stage76_WeatherHasEffect", 1)[1]
        weather = weather.split("static Stage76U8 Stage76_HasMove", 1)[0]
        self.assertIn("Stage76_BattleMonAbility(bank)", weather)
        self.assertNotIn("Stage76_EffectiveActiveAbility", weather)

    def test_piercing_uses_predicted_ability_and_real_damage_gates(self) -> None:
        for token in (
            "STAGE76_DAMAGE_CALC_ATK_ABILITY_OFFSET = 0x10",
            "Stage76_SelectAIAttackerAbility",
            "Stage76_IsAbilitySuppressed(bankAtk)",
            "STAGE76_IS_VALID_MOVE_PREDICTION",
            ")(bankDef, bankAtk);",
            "STAGE76_STAGE72_ORIGINAL_PROTECTION",
            "Stage76_IsIndividualProtectMove",
            "STAGE76_MOVE_DETECT = 197",
            "case STAGE76_MOVE_DETECT:",
            "Stage76_NormalizePredictedProtectionMove",
            "STAGE76_PROTECT_INDIVIDUAL_MASK",
            "Stage76_IsSingleTargetMove",
            "STAGE76_CHECK_CONTACT",
            "STAGE76_EFFECT_OHKO",
            "STAGE76_IS_Z_MOVE",
            "STAGE76_IS_ANY_MAX_MOVE",
            "STAGE76_IS_DYNAMAXED = 0x090F1894u",
            "STAGE76_G_CHOSEN_MOVES_BY_BANKS[bankDef] != 0",
            ")(bankDef, bankAtk);",
            "Stage76_QuarterPredictedProtectDamage(damage, 1)",
        ):
            self.assertIn(token, self.source)
        self.assertIn("STAGE76_GET_AI_ABILITY = 0x090B09C4u", self.source)
        self.assertIn("(Stage76U8)(bankAtk ^ 1u)", self.source)
        self.assertEqual(
            self.config["parent_abi"]["fixed_layout"]["DamageCalc_atkAbility_offset"],
            "0x10",
        )
        self.assertTrue(
            self.config["edge_contract"]["piercing_drill"]
            ["individual_protect_moves_include_detect_197"]
        )
        self.assertTrue(
            self.config["edge_contract"]["piercing_drill"]
            ["detect_197_normalized_to_protect_182_for_original_gate"]
        )

    def test_spicy_paths_are_exclusive_and_use_resolved_moves(self) -> None:
        self.assertEqual(self.source.count("Stage76_ShouldRewardSpicySpray("), 3)
        direct_range = self.source.split(
            "static Stage76U8 Stage76_IsDirectPartnerTargetMove", 1
        )[1].split("static Stage76U8 Stage76_IsFriendlyFireSpreadMove", 1)[0]
        self.assertIn("STAGE76_MOVE_TARGET_SELECTED", direct_range)
        self.assertIn("STAGE76_MOVE_TARGET_USER_OR_PARTNER", direct_range)
        self.assertNotIn("STAGE76_MOVE_TARGET_RANDOM", direct_range)
        for token in (
            "STAGE76_TRY_REPLACE_MOVE_WITH_Z_MOVE", "Stage76FnResolveMove",
            "resolvedMove", "STAGE76_GET_AI_CHOSEN_MOVE",
            "STAGE76_GET_AI_ABILITY", "STAGE76_BATTLE_STRUCT_MOVE_TARGET_OFFSET",
            "STAGE76_AI_SCRIPT_FOE1_OFFSET = 0x44",
            "STAGE76_G_CHOSEN_MOVES_BY_BANKS[bankAtkPartner] == 0",
            "Stage76_GetResolvedPartnerMove", "STAGE76_SPICY_PATH_DIRECT",
            "STAGE76_SPICY_PATH_SPREAD", "Stage76_SpicyPathQualifies",
        ):
            self.assertIn(token, self.source)
        self.assertEqual(
            self.config["edge_contract"]["spicy_spray"]["direct_target_ranges"],
            ["SELECTED", "USER_OR_PARTNER"],
        )
        self.assertIn("TryReplaceMoveWithZMove", self.config["parent_abi"]["fixed_functions"])
        self.assertIn("GetAIChosenMove", self.config["parent_abi"]["fixed_functions"])
        self.assertIn("GetAIAbility", self.config["parent_abi"]["fixed_functions"])
        self.assertIn("IsTargetAbilityIgnored", self.config["parent_abi"]["fixed_functions"])
        self.assertEqual(
            self.config["parent_abi"]["fixed_functions"]["IsDynamaxed"],
            "0x090F1894",
        )

    def test_spicy_requires_staying_effective_ability_and_actual_reach(self) -> None:
        for token in (
            "STAGE76_BATTLE_STRUCT_MON_TO_SWITCH_OFFSET = 0x5C",
            "STAGE76_PARTY_SIZE_SENTINEL = 6",
            "STAGE76_AI_SCRIPT_ATK_PARTNER_ABILITY_OFFSET = 0x40",
            "STAGE76_AI_SCRIPT_PARTNER_MOVE_OFFSET = 0x46",
            "Stage76_IsAbilitySuppressed(bankAtkPartner)",
            "Stage76_IsAbilitySuppressed(bankAtk)",
            "STAGE76_IS_TARGET_ABILITY_IGNORED",
            "STAGE76_ITEM_EFFECT_ABILITY_SHIELD = 147",
            "STAGE76_DOES_PROTECTION_MOVE_BLOCK_MOVE",
            "Stage76_NormalizePredictedProtectionMove(partnerMove)",
            "STAGE76_MOVE_MAX_GUARD = 891",
            "Stage76_IsPlannedMaxGuard(partnerMove)",
            "STAGE76_EFFECT_HEAL_TARGET = 233",
            "STAGE76_EFFECT_PRESENT = 122",
            "STAGE76_EFFECT_FUTURE_SIGHT = 148",
            "Stage76_DirectEffectCanDamagePartner",
            "STAGE76_EFFECT_SEMI_INVULNERABLE", "STAGE76_MOVE_WOULD_HIT_FIRST",
            "STAGE76_SPICY_PARTNER_STAYING", "STAGE76_SPICY_REACHABLE",
            "Stage76_HasBurnBenefit(bankAtk, attackerAbility)",
            "Stage76_OriginalRangeMoveCanHurtPartner",
            ")(bankAtk, bankAtkPartner, 1)",
        ):
            self.assertIn(token, self.source)
        self.assertTrue(
            self.config["edge_contract"]["spicy_spray"]
            ["planned_detect_197_normalized_to_protect_182_for_protection_gate"]
        )
        self.assertTrue(
            self.config["edge_contract"]["spicy_spray"]
            ["resolved_max_guard_891_is_not_hit"]
        )
        self.assertTrue(
            self.config["edge_contract"]["spicy_spray"]
            ["direct_heal_target_effect_233_is_not_damage"]
        )
        self.assertTrue(
            self.config["edge_contract"]["spicy_spray"]
            ["direct_present_effect_122_is_not_guaranteed_damage"]
        )
        self.assertTrue(
            self.config["edge_contract"]["spicy_spray"]
            ["direct_future_sight_effect_148_is_not_instant_damage"]
        )
        for token in (
            "STAGE76_SPICY_NOT_SUB_BLOCKED", "STAGE76_SPICY_NOT_KO",
            "STAGE76_MOVE_MIND_BLOWN = 732", "STAGE76_MOVE_STEEL_BEAM = 783",
            "STAGE76_MOVE_CHLOROBLAST = 821", "STAGE76_ITEM_EFFECT_FLAME_ORB",
            "STAGE76_ITEM_EFFECT_CURE_BURN", "STAGE76_ITEM_EFFECT_CURE_STATUS",
        ):
            self.assertIn(token, self.source)

    def test_move_manifest_fixes_self_sacrifice_project_ids(self) -> None:
        manifest_path = ROOT / self.config["source_pins"]["move_manifest"]["path"]
        self.assertEqual(
            sha256(manifest_path.read_bytes()),
            self.config["source_pins"]["move_manifest"]["sha256"],
        )
        with manifest_path.open(encoding="utf-8", newline="") as stream:
            ids = {
                row["move_key"]: int(row["id"])
                for row in csv.DictReader(stream)
                if row["move_key"] in {
                    "MOVE_KEY_MINDBLOWN", "MOVE_KEY_STEELBEAM", "MOVE_KEY_CHLOROBLAST",
                    "MOVE_KEY_MAX_GUARD", "MOVE_KEY_POLLENPUFF", "MOVE_KEY_PRESENT",
                    "MOVE_KEY_FUTURESIGHT", "MOVE_KEY_DOOMDESIRE",
                }
            }
        self.assertEqual(
            ids,
            {
                "MOVE_KEY_MINDBLOWN": 732,
                "MOVE_KEY_STEELBEAM": 783,
                "MOVE_KEY_CHLOROBLAST": 821,
                "MOVE_KEY_MAX_GUARD": 891,
                "MOVE_KEY_POLLENPUFF": 672,
                "MOVE_KEY_PRESENT": 217,
                "MOVE_KEY_FUTURESIGHT": 248,
                "MOVE_KEY_DOOMDESIRE": 353,
            },
        )
        battle_moves_offset = 0x10421F4
        for move, effect in ((217, 122), (248, 148), (353, 148), (672, 233)):
            self.assertEqual(self.fixed["rom"][battle_moves_offset + move * 12], effect)

    def test_displaced_prologues_and_actual_continuations_are_fixed(self) -> None:
        expected = {
            "Stage76_OriginalAICalcDmg": ["push\t{r4, r5, r6, r7, lr}", "090e9e71"],
            "Stage76_OriginalAIScriptPartner": ["push\t{r4, r5, r6, r7, lr}", "090a95f1"],
            "Stage76_OriginalRangeMoveCanHurtPartner": [
                "push\t{r4, r5, r6, lr}", "movs\tr4, r2", "090b0051"
            ],
        }
        for symbol, instructions in expected.items():
            section = self.compiled.disassembly.split(f"<{symbol}>:", 1)[1]
            section = section.split("\n\n", 1)[0].lower()
            for instruction in instructions:
                self.assertIn(instruction, section)

    def test_eelevate_is_pending_and_parent_sites_are_untouched(self) -> None:
        self.assertEqual(
            self.config["edges"]["eelevate_dedicated_switch"],
            "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT",
        )
        self.assertEqual(self.config["edge_contract"]["eelevate"]["status"], "PENDING")
        self.assertNotIn("GroundAbsorber", self.source)
        self.assertNotIn("GroundAbsorber", self.hooks_source)
        self.assertNotIn("Eelevate", self.source)
        self.assertFalse(any(
            "GroundAbsorber" in symbol or "Eelevate" in symbol
            for symbol in self.compiled.symbols
        ))
        for name, (address, expected) in EXPECTED_EELEVATE_SITES.items():
            offset = address - 0x08000000
            self.assertEqual(self.fixed["rom"][offset:offset + len(expected)], expected, name)
            self.assertEqual(self.result[offset:offset + len(expected)], expected, name)

    def test_far_veneer_shapes_are_fixed(self) -> None:
        self.assertEqual(veneer(8, 0x09560000).hex(), "004b184701005609")
        self.assertEqual(veneer(12, 0x09560000).hex(), "9c46014b1847c04601005609")
        self.assertGreater(PROVISIONAL_LOAD_ADDRESS - 0x090A95E4, 0x3FFFFE)

    def test_pure_policy_helpers_cover_every_negative_gate(self) -> None:
        host_gcc = shutil.which("gcc") or shutil.which("cc")
        if host_gcc is None:
            self.skipTest("host C compilerなし")
        stub = r'''
#include "modernization_p05_stage76_edges.h"
Stage76U32 Stage76_OriginalAICalcDmg(Stage76U8 a, Stage76U8 b, Stage76U16 m, void *d)
{ (void)a; (void)b; (void)m; (void)d; return 0; }
Stage76U8 Stage76_OriginalAIScriptPartner(Stage76U8 a, Stage76U8 b, Stage76U16 m, Stage76U8 v, void *d)
{ (void)a; (void)b; (void)m; (void)d; return v; }
Stage76U8 Stage76_OriginalRangeMoveCanHurtPartner(Stage76U16 m, Stage76U8 a, Stage76U8 b)
{ (void)m; (void)a; (void)b; return 0; }
const Stage76U8 Stage76_BattleScriptMegaSolPopup[1] = {0};
'''
        with tempfile.TemporaryDirectory(prefix="stage76-host-policy-") as temporary:
            work = Path(temporary)
            stub_path = work / "stub.c"
            library = work / "policy.so"
            stub_path.write_text(stub, encoding="utf-8")
            result = subprocess.run([
                host_gcc, "-shared", "-fPIC", "-O2",
                "-Wno-int-to-pointer-cast", "-Wno-pointer-to-int-cast",
                "-I", str(SOURCE_DIR),
                str(SOURCE_DIR / "modernization_p05_stage76_edges.c"),
                str(stub_path), "-o", str(library),
            ], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0, result.stderr)
            policy = ctypes.CDLL(str(library))
            policy.Stage76_MegaSolRoute.argtypes = [ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint8]
            policy.Stage76_MegaSolRoute.restype = ctypes.c_uint8
            self.assertEqual(policy.Stage76_MegaSolRoute(315, 0, 0), 2)
            self.assertEqual(policy.Stage76_MegaSolRoute(315, 0, 1), 1)
            self.assertEqual(policy.Stage76_MegaSolRoute(315, 1, 0), 0)
            policy.Stage76_QuarterPredictedProtectDamage.argtypes = [ctypes.c_uint32, ctypes.c_uint8]
            policy.Stage76_QuarterPredictedProtectDamage.restype = ctypes.c_uint32
            self.assertEqual(policy.Stage76_QuarterPredictedProtectDamage(100, 1), 25)
            self.assertEqual(policy.Stage76_QuarterPredictedProtectDamage(3, 1), 1)
            self.assertEqual(policy.Stage76_QuarterPredictedProtectDamage(100, 0), 100)
            policy.Stage76_NormalizePredictedProtectionMove.argtypes = [ctypes.c_uint16]
            policy.Stage76_NormalizePredictedProtectionMove.restype = ctypes.c_uint16
            self.assertEqual(policy.Stage76_NormalizePredictedProtectionMove(197), 182)
            self.assertEqual(policy.Stage76_NormalizePredictedProtectionMove(599), 599)
            self.assertEqual(policy.Stage76_NormalizePredictedProtectionMove(0), 0)
            policy.Stage76_IsPlannedMaxGuard.argtypes = [ctypes.c_uint16]
            policy.Stage76_IsPlannedMaxGuard.restype = ctypes.c_uint8
            self.assertEqual(policy.Stage76_IsPlannedMaxGuard(891), 1)
            self.assertEqual(policy.Stage76_IsPlannedMaxGuard(182), 0)
            self.assertEqual(policy.Stage76_IsPlannedMaxGuard(0), 0)
            policy.Stage76_DirectEffectCanDamagePartner.argtypes = [ctypes.c_uint8]
            policy.Stage76_DirectEffectCanDamagePartner.restype = ctypes.c_uint8
            self.assertEqual(policy.Stage76_DirectEffectCanDamagePartner(233), 0)
            self.assertEqual(policy.Stage76_DirectEffectCanDamagePartner(122), 0)
            self.assertEqual(policy.Stage76_DirectEffectCanDamagePartner(148), 0)
            self.assertEqual(policy.Stage76_DirectEffectCanDamagePartner(38), 1)
            self.assertEqual(policy.Stage76_DirectEffectCanDamagePartner(0), 1)
            policy.Stage76_SpicyPolicyCore.argtypes = [ctypes.c_uint16]
            policy.Stage76_SpicyPolicyCore.restype = ctypes.c_uint8
            all_flags = (1 << 13) - 1
            self.assertEqual(policy.Stage76_SpicyPolicyCore(all_flags), 1)
            for bit in range(13):
                self.assertEqual(policy.Stage76_SpicyPolicyCore(all_flags & ~(1 << bit)), 0)
            policy.Stage76_SpicyPathQualifies.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
            policy.Stage76_SpicyPathQualifies.restype = ctypes.c_uint8
            self.assertEqual(policy.Stage76_SpicyPathQualifies(0, 0, 1), 1)
            self.assertEqual(policy.Stage76_SpicyPathQualifies(0, 1, 1), 0)
            self.assertEqual(policy.Stage76_SpicyPathQualifies(1, 1, 1), 1)
            self.assertEqual(policy.Stage76_SpicyPathQualifies(1, 0, 1), 0)
            self.assertEqual(policy.Stage76_SpicyPathQualifies(0, 0, 0), 0)
            self.assertEqual(policy.Stage76_SpicyPathQualifies(2, 0, 1), 0)
            policy.Stage76_SelectAIAttackerAbility.argtypes = [
                ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint16
            ]
            policy.Stage76_SelectAIAttackerAbility.restype = ctypes.c_uint16
            self.assertEqual(policy.Stage76_SelectAIAttackerAbility(316, 0, 0, 0), 316)
            self.assertEqual(policy.Stage76_SelectAIAttackerAbility(1, 0, 1, 316), 316)
            self.assertEqual(policy.Stage76_SelectAIAttackerAbility(316, 1, 0, 0), 0)
            self.assertEqual(policy.Stage76_SelectAIAttackerAbility(1, 1, 1, 316), 0)

    def test_allocation_preserves_first79_and_adds_exact_payload(self) -> None:
        parent_allocation = json.loads(self.fixed["allocation"])
        self.assertEqual(self.allocation["allocations"][:79], parent_allocation["allocations"])
        row = self.allocation["allocations"][79]
        payload = self.artifacts[self.config["outputs"]["payload"]]
        self.assertEqual(row["sequence"], 79)
        self.assertEqual(row["size"], len(payload))
        self.assertEqual(row["content_sha256"], sha256(payload))
        self.assertEqual(sha256(self.result[row["start"]:row["end_exclusive"]]), sha256(payload))
        lineage = self.checkpoint["allocation_lineage"]
        self.assertTrue(lineage["first79_all_fields_equal"])
        self.assertEqual(lineage["parent_first79_sha256"], lineage["new_first79_sha256"])

    def test_rom_diff_is_only_payload_pointer_and_three_hooks(self) -> None:
        parent = self.fixed["rom"]
        intervals = [(
            self.checkpoint["payload"]["start"],
            self.checkpoint["payload"]["start"] + self.checkpoint["payload"]["size"],
        )]
        for row in [*EXPECTED_POINTERS, *EXPECTED_HOOKS]:
            start = int(row["address"], 0) - 0x08000000
            intervals.append((start, start + row["width"]))
        cursor = 0
        for start, end in sorted(intervals):
            self.assertEqual(parent[cursor:start], self.result[cursor:start])
            cursor = end
        self.assertEqual(parent[cursor:], self.result[cursor:])
        self.assertEqual(self.checkpoint["rom_diff"]["allowlist_interval_count"], 5)
        self.assertEqual(self.checkpoint["rom_diff"]["changed_bytes_outside_allowlist"], 0)

    def test_checkpoint_pins_nine_artifacts_and_nonrecursive_self_hash(self) -> None:
        manifest = self.checkpoint["artifact_manifest"]
        self.assertEqual(manifest["artifact_count"], 9)
        self.assertTrue(manifest["all_paths_sizes_sha256_present"])
        rows = {row["path"]: row for row in manifest["artifacts"]}
        self.assertEqual(set(rows), EXPECTED_OUTPUT_PATHS)
        checkpoint_path = self.config["outputs"]["checkpoint"]
        for path, raw in self.artifacts.items():
            self.assertEqual(rows[path]["size"], len(raw))
            if path != checkpoint_path:
                self.assertEqual(rows[path]["sha256_scope"], "WHOLE_FILE")
                self.assertEqual(rows[path]["sha256"], sha256(raw))
        core = dict(self.checkpoint)
        core.pop("artifact_manifest")
        self.assertEqual(
            rows[checkpoint_path]["sha256_scope"],
            "STABLE_JSON_WITHOUT_ARTIFACT_MANIFEST",
        )
        self.assertEqual(rows[checkpoint_path]["sha256"], sha256(stable_json(core)))

    def test_crc_bps_flags_and_active_baseline_are_fixed(self) -> None:
        output = self.checkpoint["output"]
        self.assertEqual(output["sha256"], sha256(self.result))
        self.assertEqual(output["crc32"], f"{zlib.crc32(self.result) & 0xFFFFFFFF:08X}")
        bps = self.artifacts[self.config["outputs"]["incremental_bps"]]
        self.assertEqual(self.checkpoint["bps"]["sha256"], sha256(bps))
        self.assertEqual(self.checkpoint["bps"]["source_sha256"], sha256(self.fixed["rom"]))
        self.assertEqual(self.checkpoint["bps"]["target_sha256"], sha256(self.result))
        self.assertEqual(apply_bps(self.fixed["rom"], bps), self.result)
        for document in (self.metadata, self.audit, self.contract, self.checkpoint):
            self.assertFalse(document["release_ready"])
            self.assertFalse(document["full_p05_done"])
            self.assertFalse(document["done"])
        self.assertEqual(self.checkpoint["implemented_edge_count"], 3)
        self.assertEqual(self.checkpoint["pending_edge_count"], 1)
        baseline = self.checkpoint["active_play_baseline"]
        self.assertEqual(baseline["stage"], 62)
        self.assertTrue(baseline["unchanged"])
        for key, source_key in (
            ("json", "active_play_baseline_json"),
            ("markdown", "active_play_baseline_md"),
        ):
            identity = baseline[key]
            raw = (ROOT / identity["path"]).read_bytes()
            self.assertEqual(len(raw), identity["size"])
            self.assertEqual(sha256(raw), identity["sha256"])
            self.assertEqual(identity, self.config["source_pins"][source_key])


if __name__ == "__main__":
    unittest.main()
