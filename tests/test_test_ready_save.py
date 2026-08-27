from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_test_ready_save", ROOT / "scripts/build_test_ready_save.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TestTestReadySave(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / "config/test_ready_save.json").read_text(encoding="utf-8")
        )

    def test_profile_and_canonical_ids(self) -> None:
        MODULE.validate_profile(self.config)
        self.assertEqual(self.config["stage"], 57)
        self.assertEqual(
            self.config["profile_key"],
            "STAGE57_TEST_READY_V2_OVERPOWERED_PARTY",
        )
        self.assertEqual(
            Path(self.config["input"]["rom"]).stem,
            self.config["ipad_policy"]["rom_basename"],
        )

    def test_progression_and_obedience_contract(self) -> None:
        self.assertEqual(
            [row["id"] for row in self.config["progression_flags"]],
            [0x0828, 0x0829, 0x082F],
        )
        self.assertEqual(
            self.config["obedience"]["badge_flags"], list(range(0x0820, 0x0828))
        )
        self.assertEqual(self.config["obedience"]["max_obedient_level"], 100)

    def test_overpowered_level_100_party_contract(self) -> None:
        party = self.config["party"]
        self.assertEqual(len(party), 6)
        self.assertEqual(
            [row["species_id"] for row in party],
            [150, 643, 644, 645, 1005, 1363],
        )
        self.assertEqual([row["level"] for row in party], [100] * 6)
        self.assertEqual(
            (
                party[0]["species_id"],
                party[0]["level"],
                party[0]["held_item_id"],
                [move["move_id"] for move in party[0]["moves"]],
            ),
            (150, 100, 761, [600, 59, 87, 366]),
        )
        self.assertTrue(all(len(row["moves"]) == 4 for row in party))

    def test_only_rom_apis_generate_serialized_save(self) -> None:
        policy = self.config["generation_policy"]
        self.assertTrue(policy["blank_flash_first"])
        self.assertFalse(policy["host_side_save_edit"])
        source = (ROOT / "tools/mgba_test_ready_save.c").read_text(encoding="utf-8")
        for marker in (
            "QA_FLAG_SET",
            "create_mon(core",
            "set_mon_data_u32(core",
            "QA_CALCULATE_PP",
            "BOOTSTRAP_TRY_SAVE",
        ):
            self.assertIn(marker, source)

    def test_generated_artifact_check(self) -> None:
        output = ROOT / self.config["output"]["save"]
        report = ROOT / self.config["output"]["report"]
        if not output.exists() or not report.exists():
            self.skipTest("build後にcheckする生成物")
        MODULE.check(ROOT / "config/test_ready_save.json")


if __name__ == "__main__":
    unittest.main()
