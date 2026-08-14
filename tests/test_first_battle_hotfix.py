import hashlib
import json
import unittest
from pathlib import Path

from scripts.build_first_battle_hotfix import (
    EXPECTED,
    MGBA_FIXTURE,
    PATCH_OFFSET,
    REPLACEMENT,
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
            self.rom[PATCH_OFFSET:PATCH_OFFSET + len(REPLACEMENT)],
            REPLACEMENT,
        )
        self.assertNotEqual(EXPECTED, REPLACEMENT)
        self.assertEqual(self.meta["allocation"]["new_allocation_count"], 0)
        self.assertEqual(self.meta["allocation"]["overlap_count"], 0)
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
        fault = fixture["invalid_indicator_fault_injection"]
        self.assertTrue(fault["invalid_indicator_injected"])
        self.assertTrue(fault["invalid_indicator_rejected"])
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


if __name__ == "__main__":
    unittest.main()
