from __future__ import annotations

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "overlays" / "save_migration" / "save_migration.c"
FIXTURE = ROOT / "tests" / "fixtures" / "save_migration_fixture.c"
SAVE_LAYOUT = ROOT / "config" / "save_layout.csv"


class FacilitySaveTests(unittest.TestCase):
    def test_atomic_factory_pending_encounter_and_reward_transactions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t08-facility-") as temp:
            executable = Path(temp) / "facility_fixture"
            subprocess.run(
                [
                    "cc",
                    "-std=c11",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-I",
                    str(SOURCE.parent),
                    str(SOURCE),
                    str(FIXTURE),
                    "-o",
                    str(executable),
                ],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )
            result = subprocess.run(
                [str(executable), "facility"],
                cwd=ROOT,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("facility-suite: PASS", result.stdout)

    def test_factory_mirage_and_virtual_item_have_disjoint_policies(self) -> None:
        with SAVE_LAYOUT.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        by_symbol = {row["symbol"]: row for row in rows}
        self.assertNotEqual(
            by_symbol["factory_transaction"]["owner"],
            by_symbol["mirage_records_and_item_reward"]["owner"],
        )
        self.assertEqual(by_symbol["battle_local_virtual_item"]["status"], "EXCLUDED")
        self.assertEqual(by_symbol["research_point_currency"]["status"], "DEFER")


if __name__ == "__main__":
    unittest.main()
