"""固定CFRU-JP battle rule ownerとstage 23の限定回帰。"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_battle_rules import (  # noqa: E402
    EXPECTED_CFRU_COMMIT,
    EXPECTED_STAGE22_SHA256,
    STAGE22,
    STAGE23,
    audit_owner,
    audit_source,
)


class BattleRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.metadata = json.loads(
            (ROOT / "build/stages/23_battle_rules.json").read_text(encoding="utf-8")
        )
        cls.fixture = json.loads(
            (ROOT / "build/stages/23_mgba_battle_rules.json").read_text(
                encoding="utf-8"
            )
        )
        cls.policy = json.loads(
            (ROOT / "build/stages/23_mgba_battle_policy.json").read_text(
                encoding="utf-8"
            )
        )

    def test_pinned_source_defaults_disable_legacy_switches(self) -> None:
        audit = audit_source(ROOT)
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["commit"], EXPECTED_CFRU_COMMIT)
        self.assertTrue(audit["source_lock_verified"])
        self.assertFalse(any(audit["legacy_defines_active"].values()))
        self.assertEqual(
            audit["defaults"]["critical"]["stage_denominators"],
            [24, 8, 2, 1, 1],
        )
        self.assertEqual(audit["defaults"]["weather"]["move_duration"], 5)
        self.assertEqual(audit["defaults"]["weather"]["extender_duration"], 8)

    def test_all_rule_roots_have_one_unchanged_cfru_owner(self) -> None:
        audit = audit_owner(ROOT)
        self.assertEqual(audit["current_owner"], "CFRU_PAYLOAD")
        self.assertEqual(audit["post_owner"], "CFRU_PAYLOAD")
        self.assertEqual(audit["rom_patch_count"], 0)
        self.assertEqual(len(audit["roots"]), 5)
        self.assertEqual({row["pointer"] for row in audit["roots"]}, {"0x0903F450"})
        self.assertTrue(audit["all_verified_surfaces_unchanged_since_t06"])
        self.assertTrue(all(row["byte_identical"] for row in audit["verified_surfaces"]))
        self.assertEqual(audit["t06_hook_audit"]["forbidden"], 0)
        self.assertEqual(audit["t06_hook_audit"]["unclassified_bytes"], 0)

    def test_fixed_rng_status_critical_and_weather_values(self) -> None:
        value = self.fixture
        self.assertEqual(value["status"], "PASS")
        self.assertEqual(value["process_runs"], 2)
        self.assertEqual(value["warnings_errors"], 0)
        self.assertEqual(value["rom_sha256"], EXPECTED_STAGE22_SHA256)
        self.assertEqual(
            value["paralysis"]["speed"],
            {"clear_vs_60": 0, "paralysis_vs_60": 1, "paralysis_vs_30": 0},
        )
        self.assertTrue(value["paralysis"]["immobile"]["unable"])
        self.assertFalse(value["paralysis"]["mobile"]["unable"])
        self.assertEqual(value["sleep"]["status_after"], 2)
        self.assertEqual(value["freeze"]["thaw"]["status_after"], 0)
        self.assertEqual(value["freeze"]["frozen"]["status_after"], 32)
        self.assertEqual(value["critical"]["hit"]["multiplier"], 15)
        self.assertEqual(value["critical"]["miss"]["multiplier"], 10)
        self.assertEqual(
            [(row["flag"], row["duration"]) for row in value["weather"]["start"]],
            [(1, 5), (8, 5), (32, 5), (128, 5)],
        )
        damage = value["weather"]["damage"]
        self.assertEqual(damage["rain"], damage["clear"] // 2)
        self.assertEqual(damage["sun"], damage["clear"] * 15 // 10)

    def test_residual_is_queued_once_without_direct_hp_double_apply(self) -> None:
        residual = self.fixture["residual"]
        self.assertEqual(residual["poison"]["queued_damage"], 20)
        self.assertEqual(residual["toxic"]["queued_damage"], 20)
        self.assertEqual(residual["toxic"]["status_after"], 0x180)
        self.assertEqual(residual["burn"]["queued_damage"], 10)
        for row in residual.values():
            self.assertEqual(row["hp_before"], row["hp_after"])
            self.assertEqual(row["bank_after"], 1)
        self.assertTrue(self.metadata["invariants"]["residual_queued_once"])

    def test_current_rom_normal_double_factory_and_raid_regressions_pass(self) -> None:
        self.assertTrue(self.fixture["modes"]["wild"])
        self.assertEqual(self.fixture["modes"]["trainer"]["battlers"], 2)
        self.assertTrue(self.fixture["modes"]["double"]["both_opponents_hit"])
        self.assertEqual(self.policy["status"], "PASS")
        self.assertEqual(self.policy["facility"]["matrix_cases"], 24)
        self.assertTrue(self.policy["facility"]["scheduler_faint_end"])
        self.assertTrue(self.policy["facility"]["runtime_cleaned"])
        self.assertEqual(self.policy["raid"]["shield_breaks"], 5)
        self.assertTrue(self.policy["raid"]["raid_state_completion_scheduler_e2e"])
        self.assertTrue(self.policy["raid"]["turn_limit_scheduler_end"])
        self.assertTrue(self.policy["raid"]["normal_wild_no_leak"])
        self.assertTrue(self.policy["raid"]["normal_trainer_no_leak"])
        self.assertEqual(self.policy["unreached_routes"], [])

    def test_stage23_is_an_explicit_zero_patch_promotion(self) -> None:
        self.assertEqual((ROOT / STAGE23).read_bytes(), (ROOT / STAGE22).read_bytes())
        self.assertEqual(self.metadata["input"]["sha256"], EXPECTED_STAGE22_SHA256)
        self.assertEqual(self.metadata["output"]["sha256"], EXPECTED_STAGE22_SHA256)
        self.assertEqual(self.metadata["owner_audit"]["rom_patch_count"], 0)
        self.assertTrue(all(self.metadata["invariants"].values()))
        runner = (ROOT / "tools/mgba_battle_rules_smoke.c").read_text(
            encoding="utf-8"
        )
        self.assertIn("run_multi_target_double(core, &field)", runner)
        self.assertIn("RULES_SEED_HIT = 0", runner)
        self.assertNotIn("fopen(", runner)


if __name__ == "__main__":
    unittest.main()
