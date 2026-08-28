from __future__ import annotations

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAM_LAYOUT = ROOT / "config" / "ram_layout.csv"
SAVE_LAYOUT = ROOT / "config" / "save_layout.csv"
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


def _live_intervals(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["status"] != "LIVE" or not row["start"]:
                continue
            yield row, int(row["start"], 0), int(row["end_exclusive"], 0)


class SaveLayoutTests(unittest.TestCase):
    def test_live_layouts_have_valid_non_overlapping_intervals(self) -> None:
        for path in (RAM_LAYOUT, SAVE_LAYOUT):
            by_space: dict[str, list[tuple[dict[str, str], int, int]]] = {}
            for row, start, end in _live_intervals(path):
                self.assertLess(start, end, row["symbol"])
                self.assertEqual(end - start, int(row["size"], 0), row["symbol"])
                by_space.setdefault(row["address_space"], []).append((row, start, end))
            for intervals in by_space.values():
                intervals.sort(key=lambda item: item[1])
                for left, right in zip(intervals, intervals[1:]):
                    self.assertLessEqual(left[2], right[1], f"{left[0]['symbol']} / {right[0]['symbol']}")

    def test_required_owners_and_exclusions_are_explicit(self) -> None:
        with SAVE_LAYOUT.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        symbols = {row["symbol"]: row for row in rows}
        required = {
            "KANTO_TRAVEL_UNLOCKED",
            "KANTO_VISITED",
            "VEGA_HALL_OF_FAME",
            "kanto_certifications_8bit",
            "region_heal_return_anchors",
            "bag_pockets_items_keyitems_balls_tmhm_berries",
            "seen_primary_412",
            "seen_secondary_412",
            "pokedex_header_and_personality",
            "owned_412",
            "seen_save2_412",
            "shared_special_capture_125",
            "egg_queue_box_mon_5x80",
            "factory_transaction",
            "pending_encounter",
            "itemObtainedFlags_999",
            "OWNER_KEY_RESEARCH_ECONOMY_V1",
            "reserved_v2_tail",
        }
        self.assertTrue(required.issubset(symbols))
        self.assertNotIn("research_point_currency", symbols)
        research = symbols["OWNER_KEY_RESEARCH_ECONOMY_V1"]
        self.assertEqual(research["owner"], "T23_RESEARCH_ECONOMY")
        self.assertEqual(research["status"], "LIVE")
        self.assertEqual(int(research["size"]), 64)
        self.assertEqual(research["migration"], "ZERO_EXTEND_VERSIONED")
        self.assertEqual(int(symbols["reserved_v2_tail"]["size"]), 129)
        self.assertEqual(symbols["battle_local_virtual_item"]["status"], "EXCLUDED")
        self.assertEqual(symbols["arcade_coin_u16"]["owner"], "VEGA_ARCADE_COIN")
        self.assertEqual(
            (symbols["national_dex_seen_1025_legacy_misidentified"]["status"],
             symbols["national_dex_caught_1025_legacy_misidentified"]["status"]),
            ("RETIRED", "RETIRED"),
        )
        self.assertEqual(
            (int(symbols["bag_pockets_items_keyitems_balls_tmhm_berries"]["start"], 0),
             int(symbols["bag_pockets_items_keyitems_balls_tmhm_berries"]["end_exclusive"], 0),
             int(symbols["bag_pockets_items_keyitems_balls_tmhm_berries"]["size"])),
            (0x310, 0x5F8, 744),
        )
        self.assertEqual(
            {
                name: (row["address_space"], int(row["start"], 0),
                       int(row["size"]))
                for name, row in symbols.items()
                if name in {"seen_primary_412", "seen_secondary_412",
                            "owned_412", "seen_save2_412"}
            },
            {
                "seen_primary_412": ("SAVE_BLOCK1_OFFSET", 0x5F8, 52),
                "seen_secondary_412": ("SAVE_BLOCK1_OFFSET", 0x3A18, 52),
                "owned_412": ("SAVE_BLOCK2_OFFSET", 0x28, 52),
                "seen_save2_412": ("SAVE_BLOCK2_OFFSET", 0x5C, 52),
            },
        )
        self.assertEqual(int(symbols["shared_special_capture_125"]["size"]), 16)
        self.assertEqual(int(symbols["itemObtainedFlags_999"]["size"]), 125)

    def test_c_runtime_roundtrip_migration_checksum_and_bounds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t08-save-") as temp:
            executable = Path(temp) / "save_fixture"
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
                [str(executable), "save"], cwd=ROOT, check=True, text=True, capture_output=True
            )
            self.assertIn("save-suite: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
