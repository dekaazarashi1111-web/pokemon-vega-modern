from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import build_stage61_display_npc_event_audit as BUILDER
from scripts import run_stage61_critical_release_validation as AGGREGATE
from scripts import run_stage61_critical_runtime as RUNTIME
from scripts import run_stage61_mgba_validation as STRICT_RUNNER


class Stage61CriticalReleaseUnitTests(unittest.TestCase):
    @staticmethod
    def _capture() -> dict:
        return {
            "execution": {"invalid_control_flow": False},
            "messages": [{
                "raw_hex": "01FF",
                "framebuffer_fnv1a64": "0123456789ABCDEF",
            }],
        }

    @staticmethod
    def _roundtrip() -> dict:
        return {
            name: True for name in (
                "controls_released", "running_state_released",
                "tile_transition_released", "start_pressed",
                "start_menu_opened", "back_pressed", "callback_ordered",
                "map_preserved", "field_input_recovered",
            )
        }

    def _core_result(self) -> dict:
        return {
            "producer_via_normal_dialogue": True,
            "stock_warp_then_fresh_continue": True,
            "no_branch_preserved": True,
            "yes_branch_battle_started": True,
            "battle_completed_via_normal_fight_input": True,
            "post_battle_field_input_recovered": True,
            "fresh_continue_after_normal_save": True,
            "save_raw_128k_exact_after_continue": True,
            "flute_item_persisted": True,
            "snorlax_hidden_flag_persisted": True,
            "fresh_core_continue_count": 3,
            "normal_start_menu_save_generations": 2,
            "actual_walk_steps": 2,
            "battle_species": 491,
            "battle_outcome_last_sample": 0,
            "pre_battle_save_fnv1a64": "0123456789ABCDEF",
            "saved_fnv1a64": "1111111111111111",
            "reloaded_fnv1a64": "1111111111111111",
            "captures": {
                "producer": self._capture(),
                "no": self._capture(),
                "yes": self._capture(),
            },
            "post_battle_field_roundtrip": self._roundtrip(),
            "reload_field_roundtrip": self._roundtrip(),
        }

    def test_critical_fixed_encounter_accepts_required_vertical_slice(self):
        RUNTIME._validate_core(self._core_result())

    def test_critical_fixed_encounter_rejects_missing_field_recovery(self):
        result = self._core_result()
        result["reload_field_roundtrip"]["field_input_recovered"] = False
        with self.assertRaises(RUNTIME.CriticalRuntimeError):
            RUNTIME._validate_core(result)

    def test_framebuffer_registry_checks_file_and_rgb_hash(self):
        rgb = bytes((index % 251 for index in range(240 * 160 * 3)))
        raw = RUNTIME._PPM_HEADER + rgb
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "frame.ppm").write_bytes(raw)
            result = {"framebuffer_artifacts": [{
                "path": "frame.ppm",
                "rgb_fnv1a64": RUNTIME._fnv1a64(rgb),
                "framebuffer_role": "FIELD_INPUT_RECOVERED_FRAME",
            }]}
            rows = RUNTIME._validate_framebuffers(
                result, directory, "snorlax_missing_flute",
            )
        self.assertEqual(rows[0]["size"], 115215)

    def test_changed_spans_are_derived_and_checked_against_union(self):
        spans = AGGREGATE._changed_spans(b"abcdefghi", b"abXXefYYi")
        self.assertEqual(spans, [
            {"start": 2, "end_exclusive": 4, "size": 2},
            {"start": 6, "end_exclusive": 8, "size": 2},
        ])
        self.assertTrue(AGGREGATE._all_spans_declared(
            spans, [(2, 4), (6, 9)],
        ))
        self.assertFalse(AGGREGATE._all_spans_declared(
            spans, [(2, 4), (7, 9)],
        ))

    def test_critical_case_does_not_enter_default_strict_case_set(self):
        self.assertNotIn(
            "critical_fixed_encounter_save", STRICT_RUNNER.ALL_CASES,
        )
        self.assertNotEqual(
            BUILDER.CRITICAL_RELEASE_OUTPUTS["rom"],
            "build/stages/61_display_npc_event_audit.gba",
        )

    def test_deferred_observations_are_not_task_completion_claims(self):
        rows = AGGREGATE._strict_observations()
        self.assertGreaterEqual(len(rows), 1)
        self.assertTrue(all(row["status"] == "DEFERRED_AUDIT" for row in rows))
        self.assertTrue(all(row["play_critical"] is False for row in rows))


if __name__ == "__main__":
    unittest.main()
