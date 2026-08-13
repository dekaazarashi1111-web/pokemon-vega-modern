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
        self.assertEqual(len(self.manifests["raid_encounters.csv"]), 250)
        shared = {row["shared_capture_key"] for row in self.manifests["raid_encounters.csv"]}
        self.assertEqual(len(shared), 125)
        maps = rows(self.outputs["content/maps.csv"])
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
