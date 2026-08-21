from __future__ import annotations

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "overlays" / "save_migration" / "save_migration.c"
ACQUISITION_SOURCE = (
    ROOT / "vendor" / "vega_acquisition" / "overlays" / "acquisition_runtime"
    / "acquisition_save_migration.c"
)
ACQUISITION_INCLUDE = ACQUISITION_SOURCE.parent
ACQUISITION_GENERATED = (
    ROOT / "vendor" / "vega_acquisition" / "generated"
)
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
                    "-I",
                    str(ACQUISITION_INCLUDE),
                    str(SOURCE),
                    str(ACQUISITION_SOURCE),
                    str(ACQUISITION_GENERATED / "acquisition_event_defs.c"),
                    str(ACQUISITION_GENERATED / "acquisition_collection_defs.c"),
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
        research = by_symbol["OWNER_KEY_RESEARCH_ECONOMY_V1"]
        self.assertEqual(research["status"], "LIVE")
        self.assertNotEqual(research["owner"], by_symbol["factory_transaction"]["owner"])
        self.assertNotEqual(
            research["owner"],
            by_symbol["mirage_records_and_item_reward"]["owner"],
        )


if __name__ == "__main__":
    unittest.main()
