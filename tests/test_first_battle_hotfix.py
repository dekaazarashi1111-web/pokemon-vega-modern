import hashlib
import json
import unittest
from pathlib import Path

from scripts.build_first_battle_hotfix import (
    EXPECTED,
    MGBA_FIXTURE,
    REPLACEMENT,
    RUN_TURN_PROLOGUE,
    RUNTIME_BIN,
    SOURCE_GUARD,
    SOURCE_GUARD_OFFSET,
    STAGE21,
    STAGE21_META,
    build_hotfix_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


class FirstBattleHotfixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_hotfix_outputs(ROOT)
        cls.rom = cls.outputs[STAGE21.as_posix()]
        cls.meta = json.loads(cls.outputs[STAGE21_META.as_posix()])

    def test_stage_identity_patch_span_and_allocator(self):
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(
            hashlib.sha256(self.rom).hexdigest(),
            self.meta["output"]["sha256"],
        )
        self.assertEqual(
            self.meta["patch"]["item_guard_integration_mode"],
            "t06_source_integrated",
        )
        self.assertEqual(
            self.rom[SOURCE_GUARD_OFFSET:SOURCE_GUARD_OFFSET + len(SOURCE_GUARD)],
            SOURCE_GUARD,
        )
        self.assertNotEqual(EXPECTED, REPLACEMENT)
        self.assertGreater(self.meta["patch"]["changed_byte_count"], 8)
        self.assertEqual(self.meta["patch"]["expected_hex"], RUN_TURN_PROLOGUE.hex())
        self.assertEqual(self.meta["allocation"]["new_allocation_count"], 1)
        self.assertEqual(self.meta["allocation"]["overlap_count"], 0)
        self.assertEqual(
            self.meta["actashi_ability_contract"],
            {
                "species_id": 7,
                "primary": 67,
                "secondary": 64,
                "base_stats_address": 151358552,
            },
        )
        self.assertEqual(
            hashlib.sha256(self.outputs[RUNTIME_BIN.as_posix()]).hexdigest(),
            self.meta["runtime"]["sha256"],
        )
        self.assertTrue(all(self.meta["invariants"].values()))

    def test_clean_rom_bps_round_trip_is_exact(self):
        round_trip = self.meta["release_patch_round_trip"]
        self.assertEqual(round_trip["format"], "BPS1")
        self.assertTrue(round_trip["exact"])
        self.assertEqual(
            round_trip["target_sha256"],
            self.meta["output"]["sha256"],
        )

    def test_published_mgba_fixture_covers_fault_and_valid_effects(self):
        fixture = json.loads((ROOT / MGBA_FIXTURE).read_text(encoding="utf-8"))
        self.assertEqual(fixture["status"], "PASS")
        self.assertEqual(fixture["process_runs"], 2)
        self.assertEqual(len(fixture["branches"]), 3)
        natural = fixture["natural_actashi_route"]
        self.assertTrue(natural["selected_actashi"])
        self.assertTrue(natural["trainer_327_started"])
        self.assertTrue(natural["pointer_stable"])
        self.assertTrue(natural["pending_shadow_stable"])
        observation = natural["observation"]
        self.assertEqual(observation["player_ability"], 67)
        self.assertEqual(observation["opponent_ability"], 65)
        self.assertEqual(observation["quick_claw_script_entries"], 0)
        self.assertEqual(observation["quick_draw_script_entries"], 0)
        self.assertEqual(observation["placeholder_item_entries"], 0)
        self.assertTrue(observation["pp_spent_once"])
        self.assertTrue(observation["hp_changed"])
        faults = {
            row["indicator"]: row
            for row in fixture["invalid_indicator_fault_injections"]
        }
        self.assertEqual(
            set(faults),
            {"QUICK_CLAW", "QUICK_DRAW_ACTASHI_ABILITY_64"},
        )
        self.assertEqual(faults["QUICK_DRAW_ACTASHI_ABILITY_64"]["bank"], 0)
        self.assertEqual(faults["QUICK_DRAW_ACTASHI_ABILITY_64"]["ability"], 64)
        for row in faults.values():
            fault = row["observation"]
            self.assertTrue(fault["invalid_indicator_injected"])
            self.assertTrue(fault["invalid_indicator_rejected"])
            self.assertEqual(fault["quick_claw_script_entries"], 0)
            self.assertEqual(fault["quick_draw_script_entries"], 0)
            self.assertEqual(fault["placeholder_item_entries"], 0)
            self.assertTrue(fault["pp_spent_once"])
        by_effect = {
            row["effect"]: row for row in fixture["legitimate_priority_effects"]
        }
        self.assertEqual(
            set(by_effect), {"QUICK_CLAW", "CUSTAP_BERRY", "QUICK_DRAW"}
        )
        for row in by_effect.values():
            with self.subTest(effect=row["effect"]):
                self.assertTrue(row["indicator_seen"])
                self.assertTrue(row["notification_seen"])
                self.assertEqual(row["first_bank"], 1)
                self.assertTrue(row["observation"]["pp_spent_once"])
                self.assertTrue(row["observation"]["hp_changed"])
        self.assertTrue(by_effect["QUICK_DRAW"]["ability_name_valid"])
        self.assertEqual(by_effect["QUICK_DRAW"]["popup_ability"], 260)


if __name__ == "__main__":
    unittest.main()
