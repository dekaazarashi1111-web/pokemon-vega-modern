#!/usr/bin/env python3
"""T10 engine/QOL-A vertical sliceの焦点試験。"""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.build_engine_vertical_slice import ARTIFACTS, check

ROOT = Path(__file__).resolve().parents[1]


class EngineVerticalSliceTests(unittest.TestCase):
    def load(self, name: str) -> dict:
        return json.loads((ROOT / "tests/fixtures" / name).read_text(encoding="utf-8"))

    def test_selected_elements_are_appended_and_continuous(self) -> None:
        fixture = self.load("engine_slice.json")
        selected = fixture["selected"]
        self.assertEqual(selected["species"]["id"], 445)
        self.assertGreaterEqual(selected["move"]["id"], 512)
        self.assertGreaterEqual(selected["ability"]["id"], 78)
        self.assertGreaterEqual(selected["held_item"]["id"], 375)
        self.assertEqual(selected["evolution"]["method"], 26)
        self.assertEqual(selected["evolution"]["param"], selected["move"]["id"])
        self.assertEqual(fixture["continuous_save"], "T10_SAVE_A")
        self.assertEqual(fixture["mgba_smoke"]["status"], "PASS")
        self.assertEqual(fixture["mgba_smoke"]["process_runs"], 2)

    def test_release_defaults_and_debug_guard(self) -> None:
        with (ROOT / "config/feature_matrix.csv").open(encoding="utf-8", newline="") as stream:
            rows = {row["feature_key"]: row for row in csv.DictReader(stream)}
        self.assertEqual(rows["TEXT_SPEED"]["release_default"], "INSTANT")
        self.assertEqual(rows["HATCH_MODE"]["release_default"], "FAST")
        self.assertEqual(rows["EXP_SHARE"]["release_default"], "ON")
        self.assertEqual(rows["DEBUG_GIFT"]["release_default"], "OFF")
        self.assertEqual(rows["DEBUG_GIFT"]["release_enabled"], "false")
        self.assertLessEqual(float(rows["RUN_COURSE_FRAME_RATIO"]["release_default"]), 0.75)
        self.assertLessEqual(float(rows["BICYCLE_COURSE_FRAME_RATIO"]["release_default"]), 0.50)

    def test_movement_and_text_preserve_order_and_events(self) -> None:
        movement = self.load("qol_movement_courses.json")
        for course in movement["courses"]:
            self.assertGreaterEqual(course["run_reduction_percent"], 25)
            self.assertGreaterEqual(course["bicycle_reduction_percent"], 50)
            self.assertEqual(course["events"]["step"], 100)
            self.assertTrue(all(count == 1 for kind, count in course["events"].items() if kind != "step"))
        qol = self.load("qol_slice.json")
        self.assertEqual(qol["text"]["glyph_delay"], 0)
        self.assertEqual(qol["text"]["preserved_controls"],
                         ["variable", "color", "page", "choice", "wait", "sound"])
        self.assertTrue(qol["existing_ui_only"])

    def test_facility_ai_encounter_research_and_raid_boundaries(self) -> None:
        factory = self.load("factory_trial.json")
        self.assertEqual((factory["candidate_count"], factory["selected_count"], factory["battle_count"]),
                         (6, 3, 3))
        self.assertTrue(factory["held_items_restored"])
        self.assertTrue(factory["caught_unchanged"])
        reward = self.load("reward_encounter.json")
        self.assertTrue(reward["capacity_checked_before_payment"])
        self.assertTrue(reward["flee_keeps_pending"] and reward["capture_clears_pending"])
        trainer = self.load("trainer_ai_slice.json")
        self.assertEqual({row["profile"] for row in trainer["fixtures"]},
                         {"AI_SEMI_SMART", "AI_FULL_SMART"})
        self.assertIn("DOUBLE", {row["format"] for row in trainer["fixtures"]})
        research = self.load("research_encounter_slice.json")
        self.assertEqual(research["normal_fallback"], "BYTE_EQUIVALENT_ORIGINAL_TABLE")
        self.assertFalse(research["tohoku_overlay"]["replaces_one_percent_slot"])
        raid = self.load("raid_slice.json")
        self.assertEqual(raid["tier"], 4)
        self.assertIn("GIMMICK", raid["cleanup"])

    def test_manifest_schema_frozen_and_check_read_only(self) -> None:
        schema = json.loads((ROOT / "config/engine_manifest_schema.json").read_text())
        self.assertTrue(schema["frozen"])
        tracked = [ROOT / path for path in ARTIFACTS]
        before = {path: path.read_bytes() for path in tracked}
        self.assertEqual(check(ROOT)["status"], "PASS")
        self.assertEqual(before, {path: path.read_bytes() for path in tracked})


if __name__ == "__main__":
    unittest.main()
