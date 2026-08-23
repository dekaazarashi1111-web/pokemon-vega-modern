import copy
import csv
import io
import json
import unittest
from pathlib import Path

from tools.content.populate_content import HEADERS, build_outputs
from tools.content.validate_population import collect_population_errors, collect_stage_errors


ROOT = Path(__file__).resolve().parents[1]


def rows(raw: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))


class ContentPopulationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_outputs(ROOT)
        cls.manifests = {name: rows(cls.outputs[f"manifests/{name}"]) for name in HEADERS}
        cls.fixture = json.loads(cls.outputs["tests/fixtures/content_population.json"])

    def test_exact_dual_region_coverage(self):
        self.assertEqual(self.fixture["logical_locations"], {"TOHOKU": 49, "KANTO": 47})
        self.assertEqual(self.fixture["physical_bindings"], {"TOHOKU": 49, "KANTO": 47})
        self.assertEqual(len(self.manifests["kanto_encounters.csv"]), 541)
        self.assertEqual(len(self.manifests["research_encounters.csv"]), 1082)
        self.assertEqual(len(self.manifests["raid_encounters.csv"]), 256)
        shared = {row["shared_capture_key"] for row in self.manifests["raid_encounters.csv"]
                  if row["shared_capture_key"] != "NONE"}
        self.assertEqual(len(shared), 125)
        maps = rows(self.outputs["content/maps.csv"])
        bindings = rows(self.outputs["content/map_bindings.csv"])
        first_route = next(
            row for row in bindings if row["logical_location_key"] == "T501"
        )
        self.assertEqual(
            (first_route["group_id"], first_route["map_id"]), ("3", "19")
        )
        self.assertIn("Lv3.3", first_route["notes"])
        route_bindings = {
            row["logical_location_key"]: (int(row["group_id"]), int(row["map_id"]))
            for row in bindings if row["region"] == "TOHOKU"
        }
        expected_routes = {
            "T501": (3, 19), "T502": (3, 20), "T503": (3, 21),
            "T504": (3, 44), "T505": (3, 23), "T506": (3, 24),
            "T507": (3, 25), "T508": (3, 26), "T509": (3, 27),
            "T510": (3, 28), "T511": (3, 29), "T512": (3, 31),
            "T513": (3, 30), "T514": (3, 32), "T515": (3, 33),
            "T516": (3, 34), "T517": (3, 35), "T518": (3, 36),
            "T519": (3, 37), "T520": (3, 42), "T521": (3, 43),
            "T522": (3, 41), "T523": (3, 38),
        }
        self.assertEqual({key: route_bindings[key] for key in expected_routes}, expected_routes)
        low_raids = [row for row in self.manifests["raid_encounters.csv"]
                     if row["raid_key"].startswith("RAID_KEY_LOW_")]
        self.assertEqual(sorted(int(row["level"]) for row in low_raids), [5, 12, 20, 35, 45, 55])
        league = next(row for row in maps if row["logical_location_key"] == "K42")
        self.assertEqual(league["unlock_key"], "KANTO_LEAGUE")
        self.assertEqual(league["warning_key"], "WARNING_KANTO_LEAGUE")
        self.assertEqual(
            {row["difficulty_policy"] for row in self.manifests["kanto_encounters.csv"]},
            {"FIXED_HIGH_LEVEL_OPTIONAL"},
        )
        audit = self.outputs["reports/generated/kanto_content_audit.md"].decode("utf-8")
        self.assertEqual(audit.count("| TOHOKU |") + audit.count("| KANTO |"), 96)

    def test_facility_and_progression_contracts(self):
        mix = [row for row in self.manifests["facility_rentals.csv"]
               if row["pool_key"] == "RENTAL_POOL_KEY_MIX"]
        weights = {}
        for bucket in ("OFFICIAL", "VEGA", "SPECIAL"):
            weights[bucket] = sum(int(row["weight"]) for row in mix if row["origin_bucket"] == bucket)
        total = sum(weights.values())
        self.assertEqual({key: value * 100 // total for key, value in weights.items()},
                         {"OFFICIAL": 70, "VEGA": 25, "SPECIAL": 5})
        mirage = [row for row in self.manifests["facility_modes.csv"] if row["party_owner"] == "MIRAGE"]
        self.assertEqual(len(mirage), 4)
        self.assertTrue(all(row["battle_count"] == "7" and row["level_policy"] == "LEVEL_100_FIXED"
                            for row in mirage))

    def test_semantic_validator_and_mutation_rejection(self):
        self.assertEqual(collect_population_errors(ROOT, self.manifests), [])
        broken = copy.deepcopy(self.manifests)
        broken["facility_rentals.csv"][0]["species_key"] = "SPECIES_KEY_DOES_NOT_EXIST"
        errors = collect_population_errors(ROOT, broken)
        self.assertTrue(any("unresolved species_key" in error for error in errors), errors)

    def test_rom_payload_and_central_allocation(self):
        metadata = json.loads(self.outputs["build/stages/16_content.json"])
        allocation = json.loads(self.outputs["build/stages/16_allocation.json"])
        payload = self.outputs["generated/content/t16_content.bin"]
        rom = self.outputs["build/stages/16_content.gba"]
        start = metadata["payload"]["offset"]
        self.assertEqual(len(rom), 32 * 1024 * 1024)
        self.assertEqual(rom[start:start + len(payload)], payload)
        self.assertEqual(allocation["summaries"]["overlap_count"], 0)
        self.assertEqual(collect_stage_errors(ROOT), [])


if __name__ == "__main__":
    unittest.main()
