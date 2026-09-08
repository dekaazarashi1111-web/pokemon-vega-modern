from __future__ import annotations

import json
import hashlib
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/mgba_modernization_stage79_p05_runtime_smoke.c"
STAGE77_CONFIG = ROOT / "config/modernization_p05_stage77_suppression.json"
STAGE77_SYMBOLS = (
    ROOT / "generated/runtime/modernization_p05_stage77_suppression_symbols.json"
)
STAGE76_CONFIG = ROOT / "config/modernization_p05_stage76_edges.json"
STAGE76_SYMBOLS = (
    ROOT / "generated/runtime/modernization_p05_stage76_edges_symbols.json"
)
STAGE72_SYMBOLS = (
    ROOT / "generated/runtime/modernization_p05_ability_rom_runtime_symbols.json"
)
STAGE78_CONFIG = ROOT / "config/modernization_p05_stage78_eelevate_switch_ai.json"
STAGE78_SYMBOLS = (
    ROOT / "generated/runtime/modernization_p05_stage78_eelevate_switch_ai_symbols.json"
)
STAGE78_CONTRACT = (
    ROOT / "content/modernization/p05_stage78_eelevate_switch_ai_contract.json"
)


class ModernizationStage79P05RuntimeSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = RUNNER.read_text(encoding="utf-8")
        cls.stage77 = json.loads(STAGE77_CONFIG.read_text(encoding="utf-8"))
        cls.stage77_symbols = json.loads(
            STAGE77_SYMBOLS.read_text(encoding="utf-8")
        )["symbols"]
        cls.stage76 = json.loads(STAGE76_CONFIG.read_text(encoding="utf-8"))
        cls.stage76_symbols = json.loads(
            STAGE76_SYMBOLS.read_text(encoding="utf-8")
        )["symbols"]
        cls.stage72_symbols = json.loads(
            STAGE72_SYMBOLS.read_text(encoding="utf-8")
        )["symbols"]
        cls.stage78 = json.loads(STAGE78_CONFIG.read_text(encoding="utf-8"))
        cls.stage78_symbols = json.loads(
            STAGE78_SYMBOLS.read_text(encoding="utf-8")
        )
        cls.stage78_contract = json.loads(
            STAGE78_CONTRACT.read_text(encoding="utf-8")
        )

    def test_strict_host_compile(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("ccなし")
        with tempfile.TemporaryDirectory(prefix="stage79-p05-runner-") as temporary:
            output = Path(temporary) / "stage79-p05-smoke"
            result = subprocess.run(
                [
                    compiler,
                    "-std=c11",
                    "-O2",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-Itools",
                    str(RUNNER),
                    "-o",
                    str(output),
                    "-lmgba",
                    "-lm",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())

    def test_all_29_dispatchers_and_33_surfaces_match_stage77_contract(self) -> None:
        actual = re.findall(
            r'^\s*\{"([A-Za-z0-9]+)", (8|12)U, ([12])U, '
            r'(true|false)\},$',
            self.source,
            flags=re.MULTILINE,
        )
        expected = []
        for row in self.stage77["parent_abi"]["hooks"]:
            self.assertTrue(row["target"].startswith("Stage77_Dispatch"))
            expected.append(
                (
                    row["target"].removeprefix("Stage77_Dispatch"),
                    str(row["width"]),
                    str(len(row["abilities"])),
                    "true" if row["abi"].count(",") == 4 else "false",
                )
            )
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 29)
        self.assertEqual(sum(int(row[2]) for row in actual), 33)
        self.assertEqual(sum(row[1] == "12" for row in actual), 7)
        self.assertEqual(
            [row[0] for row in actual if row[3] == "true"],
            [
                "AbilityBattleEffects",
                "NonInvasiveCheckGrounding",
                "TypeCalc",
            ],
        )

    def test_every_dynamic_dispatch_address_has_a_pinned_source(self) -> None:
        for row in self.stage77["parent_abi"]["hooks"]:
            suffix = row["target"].removeprefix("Stage77_Dispatch")
            self.assertIn(f'{{"{suffix}",', self.source)
            self.assertEqual(
                int(self.stage77_symbols[row["target"]], 0) & ~1,
                int(self.stage77_symbols[row["target"]], 0),
            )
            self.assertEqual(
                self.stage72_symbols[row["normal_delegate"]],
                row["normal_address"],
            )
            self.assertEqual(
                self.stage72_symbols[row["suppressed_delegate"]],
                row["suppressed_address"],
            )
        for prefix in ("HOOK_", "DISPATCH_", "NORMAL_", "SUPPRESSED_"):
            self.assertIn(f'"{prefix}"', self.source)
        self.assertIn("p05x_key(key, sizeof(key)", self.source)
        # Stage77/76 relocated payload addresses must arrive through NAME=VALUE.
        self.assertIsNone(re.search(r"0x095D[0-9A-Fa-f]{4}", self.source))

    def test_stage76_symbols_and_all_four_production_patches_are_required(self) -> None:
        required_symbols = {
            "Stage76_RuntimeProbe",
            "Stage76_MegaSolRoute",
            "Stage76_QuarterPredictedProtectDamage",
            "Stage76_NormalizePredictedProtectionMove",
            "Stage76_IsPlannedMaxGuard",
            "Stage76_DirectEffectCanDamagePartner",
            "Stage76_SelectAIAttackerAbility",
            "Stage76_SpicyPolicyCore",
            "Stage76_SpicyPathQualifies",
            "Stage76_DispatchMegaSolSolarBeam",
            "Stage76_BattleScriptMegaSolPopup",
            "Stage76_BattleScriptSolarBeam",
            "Stage76_EntryAICalcDmg",
            "Stage76_EntryAIScriptPartner",
            "Stage76_EntryRangeMoveCanHurtPartner",
        }
        self.assertTrue(required_symbols <= self.stage76_symbols.keys())
        for symbol in required_symbols:
            self.assertIn(f'"{symbol}"', self.source)
        self.assertEqual(
            [row["name"] for row in self.stage76["parent_abi"]["pointer_patches"]],
            ["SolarBeamEffectScript"],
        )
        self.assertEqual(
            [row["name"] for row in self.stage76["parent_abi"]["hooks"]],
            ["AI_CalcDmg", "AIScript_Partner", "RangeMoveCanHurtPartner"],
        )
        for key in (
            "HOOK_Stage76SolarBeam",
            "HOOK_Stage76AICalcDmg",
            "HOOK_Stage76AIScriptPartner",
            "HOOK_Stage76RangeMoveCanHurtPartner",
        ):
            self.assertIn(f'"{key}"', self.source)

    def test_predicate_boundaries_register_abi_and_no_overclaim_are_explicit(self) -> None:
        for token in (
            "P05X_BATTLE_TYPE_CIRCUS = 0x04000000U",
            "P05X_CIRCUS_ABILITY_SUPPRESSION",
            "P05X_ADJACENT_BATTLE_TYPE = 0x02000000U",
            "P05X_ADJACENT_CIRCUS_FLAG = 0x40000000U",
            'write_register(core, "r12", original_r3)',
            "fifth_stack_argument ? &fifth_argument : NULL",
            "UINT32_C(0xC0DEF00D)",
            "read32(core, call_stack.entry_sp) == fifth_argument",
            "p05x_pc_matches_target(pc, normal)",
            "either the entry or Thumb entry + 2",
            "restore_host_call_stack(core, &call_stack)",
            '"\\\"classification\\\":\\\"STAGE78_P05_RUNTIME_DIRECT_CALL\\\","',
            '"\\\"predicate_truth_table_pass\\\":true,"',
            '"\\\"stage76_helpers_preserved\\\":true,"',
            '"\\\"suppression_paths_pass\\\":true,"',
            '"\\\"fifth_stack_argument_observations\\\":21,"',
            '"\\\"fifth_stack_arguments_preserved\\\":true,"',
            '"\\\"eelevate_switch_ai_done\\\":true,"',
            '"\\\"eelevate_matrix_case_count\\\":32,"',
            '"\\\"eelevate_matrix_observations\\\":32,"',
            '"\\\"eelevate_pure_helper_pass\\\":true,"',
            '"\\\"eelevate_active_hook_observations\\\":13,"',
            '"\\\"eelevate_party_hook_observations\\\":13,"',
            '"\\\"full_p05_acceptance\\\":false,"',
            '"\\\"scheduler_e2e\\\":false,\\\"artifacts_written\\\":[]}',
        ):
            self.assertIn(token, self.source)

    def test_stage78_matrix_hooks_and_runtime_boundaries_are_exact(self) -> None:
        stable = (
            json.dumps(
                self.stage78_contract["matrix"],
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ) + "\n"
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(stable).hexdigest(),
            "3b0ce8e8a5fa75857971b59091f2a95d73ec5597d90be4756eb9e3717e8383ed",
        )
        cases = self.stage78_contract["matrix"]["cases"]
        self.assertEqual(len(cases), 32)
        for row in cases:
            self.assertIn(f'{{"{row["name"]}",', self.source)
        symbols = self.stage78_symbols["symbols"]
        for name in (
            "Stage78_RuntimeProbe", "Stage78_MapEelevateAbsorber",
            "Stage78_ActiveAbsorberAbility", "Stage78_PartyAbsorberAbility",
            "Stage78_EntryFindMonAbsorberActive",
            "Stage78_EntryFindMonAbsorberParty",
        ):
            self.assertIn(name, symbols)
            self.assertIn(f'"{name}"', self.source)
        for token in (
            "HOOK_FindMonAbsorberActiveAbilityBlock",
            "HOOK_FindMonAbsorberPartyAbilityBlock",
            "CONT_FindMonAbsorberActiveAbilityBlock",
            "CONT_FindMonAbsorberPartyAbilityBlock",
            "P05X_EELEVATE_ACTIVE_BANK = 2U",
            "active_foe2_after_switch",
            "party_foe2_after_out_of_range",
            "active_absent_gas_excluded",
            "party_dead_gas_excluded",
            "active_battler_count_capped",
            "party_outgoing_gastro_not_inherited",
            "party_mold_breaker_shield",
            "party_neutralizing_gas_shield",
            "P05X_ABILITY_MOLD_BREAKER = 105U",
            "scenario->party || !row.suppression_stub_seen",
            "row.mon_item_stub_seen",
        ):
            self.assertIn(token, self.source)
        ability_rows = (ROOT / "manifests/ability_ids.csv").read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertTrue(any(
            row.startswith("ABILITY_KEY_MOLDBREAKER,105,")
            for row in ability_rows
        ))

    def test_pc_normalization_accepts_only_entry_and_entry_plus_two(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("ccなし")
        harness = r'''
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#define MODERNIZATION_STAGE79_P05_EMBEDDED
#include "mgba_modernization_stage79_p05_runtime_smoke.c"
#pragma GCC diagnostic pop

int main(void)
{
    const uint32_t target = UINT32_C(0x0953410D);
    if (!p05x_pc_matches_target(UINT32_C(0x0953410C), target))
        return 1;
    if (!p05x_pc_matches_target(UINT32_C(0x0953410E), target))
        return 2;
    if (!p05x_pc_matches_target(UINT32_C(0x0953410D), target))
        return 3;
    if (p05x_pc_matches_target(UINT32_C(0x0953410A), target))
        return 4;
    if (p05x_pc_matches_target(UINT32_C(0x09534110), target))
        return 5;
    if (p05x_pc_matches_target(UINT32_C(0x095D5874), target))
        return 6;
    return 0;
}
'''
        with tempfile.TemporaryDirectory(prefix="stage79-p05-pc-") as temporary:
            directory = Path(temporary)
            source = directory / "pc_contract.c"
            executable = directory / "pc_contract"
            source.write_text(harness, encoding="utf-8")
            compiled = subprocess.run(
                [
                    compiler,
                    "-std=c11",
                    "-O2",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-pedantic",
                    "-Itools",
                    str(source),
                    "-o",
                    str(executable),
                    "-lmgba",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            executed = subprocess.run(
                [str(executable)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(executed.returncode, 0, executed.stderr)


if __name__ == "__main__":
    unittest.main()
