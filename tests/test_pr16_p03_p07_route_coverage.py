from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pr16_p03_p07_route_coverage.py"
MANIFEST = ROOT / "content" / "modernization" / "pr16_p03_p07_route_coverage.json"

spec = importlib.util.spec_from_file_location("route_coverage", SCRIPT)
assert spec and spec.loader
route_coverage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route_coverage)


class RouteCoverageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_canonical_manifest_passes(self) -> None:
        receipt = route_coverage.validate_manifest(self.manifest)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(
            receipt["p03_remaining_physical_gap_ids"],
            [
                "P03_GENERIC_FORM_CHANGE_CARRY_PHYSICAL",
                "P03_FIXED_FORM_TRANSITION_PHYSICAL",
            ],
        )
        self.assertEqual(receipt["p07_remaining_physical_gap_ids"], [])

    def test_form_inventory_is_finite_and_exact(self) -> None:
        form = self.manifest["p03"]["form_inventory"]
        self.assertEqual(form["routes"], 70)
        self.assertEqual(form["species"], 19)
        self.assertEqual(
            form["generic_carry_routes"] + form["fixed_transition_routes"] + form["rotom_routes"],
            70,
        )

    def test_ordinary_daycare_is_not_reopened(self) -> None:
        ordinary = next(
            route
            for route in self.manifest["p03"]["route_groups"]
            if route["id"] == "ORDINARY_DIRECT_EGG_DAYCARE"
        )
        self.assertEqual(ordinary["coverage"], "ACCEPTED_NATIVE")
        self.assertEqual(ordinary["evidence"][0]["run_id"], 34434453733)
        self.assertEqual(ordinary["evidence"][0]["case_count"], 8)

    def test_p07_changed_surface_has_no_gap(self) -> None:
        p07 = self.manifest["p07"]
        self.assertEqual(p07["remaining_physical_gap_ids"], [])
        self.assertTrue(p07["complete_on_parent_candidate"])
        self.assertFalse(p07["successor_transfer_complete"])
        changed = {item["id"]: item for item in p07["change_surface"]["changed_by_p07"]}
        self.assertEqual(changed["PRESERVED_LEVEL_ROWS"]["rows"], 310)
        self.assertEqual(changed["PRESERVED_EGG_ROWS"]["rows"], 189)
        self.assertEqual(changed["HAPPINY_COLLISION_ADAPTER"]["moves"], [461, 464, 357])

    def test_successor_transfer_stays_in_p08(self) -> None:
        scope = self.manifest["candidate_scope"]
        self.assertFalse(scope["successor_transfer_is_route_gap"])
        self.assertEqual(scope["successor_transfer_condition_id"], "FINAL_NATIVE_ACCEPTANCE")
        self.assertEqual(self.manifest["p07"]["successor_transfer_owned_by"], "P08:FINAL_NATIVE_ACCEPTANCE")

    def test_tampered_form_total_fails(self) -> None:
        tampered = copy.deepcopy(self.manifest)
        tampered["p03"]["form_inventory"]["routes"] = 71
        with self.assertRaises(route_coverage.CoverageError):
            route_coverage.validate_manifest(tampered)

    def test_tampered_p07_gap_fails(self) -> None:
        tampered = copy.deepcopy(self.manifest)
        tampered["p07"]["remaining_physical_gap_ids"] = ["REPLAY_ALL_ROWS"]
        with self.assertRaises(route_coverage.CoverageError):
            route_coverage.validate_manifest(tampered)

    def test_projection_updates_only_two_condition_objects(self) -> None:
        fixture = {
            "unrelated": {"id": "UNCHANGED", "status": "PENDING"},
            "conditions": [
                {
                    "id": "EVOLUTION_FORM_OTHER_EGG",
                    "status": "PENDING_ACCEPTED_CONSUMER_COVERAGE",
                    "coverage_inventory_complete": False,
                },
                {
                    "id": "P07_REMAINING_ROUTE_ACCEPTANCE",
                    "status": "PENDING_CHANGE_COVERAGE_MAPPING",
                    "coverage_inventory_complete": False,
                },
            ],
        }
        updated = route_coverage.apply_remaining_projection(fixture, self.manifest)
        route_coverage.check_remaining_projection(updated, self.manifest)
        self.assertEqual(updated["unrelated"], fixture["unrelated"])
        self.assertEqual(fixture["conditions"][0]["coverage_inventory_complete"], False)


if __name__ == "__main__":
    unittest.main()
