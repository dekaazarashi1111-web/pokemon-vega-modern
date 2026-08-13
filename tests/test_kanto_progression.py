import copy
import json
import unittest
from pathlib import Path

from tools.content.content_schema import ContentError
from tools.content.progression import (PROGRESSION_HEADER, _read, build_outputs,
                                       validate_progression_rows)

ROOT = Path(__file__).resolve().parents[1]


class KantoProgressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_outputs(ROOT)
        cls.graph = json.loads(cls.outputs["generated/kanto/progression/graph.json"])
        cls.areas = json.loads(cls.outputs["generated/kanto/progression/area_gates.json"])
        cls.matrix = json.loads(cls.outputs["tests/fixtures/progression_boundaries.json"])
        cls.rows = _read(ROOT / "content/kanto_progression.csv", PROGRESSION_HEADER)

    def test_dual_phase_and_permanent_return(self):
        self.assertNotIn("VEGA_HALL_OF_FAME", self.graph["KANTO_CERT_4"]["predecessors"])
        self.assertIn("VEGA_HALL_OF_FAME", self.graph["KANTO_CERT_5"]["predecessors"])
        self.assertTrue(self.matrix["return_edge"]["all_kanto_states"])
        self.assertFalse(self.matrix["early_access"]["requires_national_dex"])

    def test_all_maps_and_boundaries(self):
        self.assertEqual(len(self.areas), 253)
        self.assertEqual({x["logical_code"] for x in self.areas}, {f"K{x:02d}" for x in range(1, 48)})
        keys = {x["unlock_key"] for x in self.matrix["boundary_fixtures"]}
        for key in ("FACTORY_STANDARD", "FACTORY_FULL", "FACTORY_MASTER",
                    "LEAGUE_I_AVAILABLE", "LEAGUE_II_AVAILABLE", "FINAL_LEAGUE_AVAILABLE",
                    "RESEARCH_PROFILE_UNLOCKED", "RAID_HIGH_UNLOCKED"):
            self.assertIn(key, keys)

    def test_state_isolation_and_release_policy(self):
        self.assertTrue(self.matrix["factory_mirage_isolated"])
        self.assertTrue(self.matrix["normal_profile_preserved"])
        self.assertFalse(self.matrix["release_dev_shortcut"])
        self.assertTrue(self.matrix["development_fast_travel_available"])
        self.assertIn("DUAL_REGION_RESONANCE", self.matrix["state_model"])
        self.assertIn("SHARED_SPECIAL_CAPTURE_STATE", self.matrix["state_model"])
        self.assertIn(b"Kanto writes to Vega badge/HM/story state: 0",
                      self.outputs["reports/generated/progression_graph.md"])

    def test_cycle_and_unreachable_prerequisite_rejected(self):
        cycle = copy.deepcopy(self.rows)
        cycle[0]["predecessor_keys"] = "FINAL_LEAGUE_CLEARED"
        with self.assertRaisesRegex(ContentError, "cycle"):
            validate_progression_rows(cycle)
        missing = copy.deepcopy(self.rows)
        missing[0]["predecessor_keys"] = "MISSING_NODE"
        with self.assertRaisesRegex(ContentError, "unreachable predecessor"):
            validate_progression_rows(missing)


if __name__ == "__main__":
    unittest.main()
