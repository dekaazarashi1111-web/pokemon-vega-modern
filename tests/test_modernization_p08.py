#!/usr/bin/env python3
"""工程8統合監査checkpointのfocused tests。"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_modernization_p08 import render_outputs  # noqa: E402
from tools.modernization_p08_integration import (  # noqa: E402
    ModernizationP08Error,
    PARALLEL_OUTPUTS,
    PINNED_TRACKED_INPUTS,
    STATUS,
    build_integration_matrix,
    build_release_handoff,
    build_runtime_handoff,
    validate_active_baseline,
    validate_integration_matrix,
    verify_exact_bytes,
)


class ModernizationP08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 32 MiB候補ROM群と大きなcontractのhashは一度だけ計算する。
        cls.matrix = build_integration_matrix(ROOT)

    def test_active_play_baseline_remains_exact_stage62(self) -> None:
        active = self.matrix["active_play_baseline"]
        self.assertEqual(active["stage"], 62)
        self.assertFalse(active["changed"])
        self.assertFalse(active["candidate_auto_promoted"])
        self.assertEqual(
            active["config_sha256"],
            "4800257add049ea99cdedda91413a70a255dcff9a85823463596edefa8785053",
        )
        self.assertEqual(
            active["rom"]["sha256"],
            "d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f",
        )

    def test_only_p01_is_completed(self) -> None:
        phases = {row["phase"]: row for row in self.matrix["phases"]}
        self.assertEqual(phases["P01"]["completion_state"], "COMPLETED")
        for phase in ("P02", "P03", "P04", "P05", "P06", "P07"):
            self.assertEqual(phases[phase]["completion_state"], "CHECKPOINT_NOT_DONE")
        self.assertEqual(phases["P08"]["completion_state"], STATUS)
        self.assertEqual(
            self.matrix["integration_summary"]["completed_phases"], ["P01"]
        )

    def test_contract_pass_does_not_mean_phase_done(self) -> None:
        phases = {row["phase"]: row for row in self.matrix["phases"]}
        for phase in ("P02", "P03"):
            self.assertIn("PASS", phases[phase]["contract_statuses"])
            self.assertNotEqual(phases[phase]["completion_state"], "COMPLETED")

        for index in (1, 2):
            false_done = copy.deepcopy(self.matrix)
            false_done["phases"][index]["completion_state"] = "COMPLETED"
            with self.subTest(phase=false_done["phases"][index]["phase"]):
                with self.assertRaises(ModernizationP08Error):
                    validate_integration_matrix(false_done)

    def test_adoption_and_runtime_boundaries_are_explicit(self) -> None:
        phases = {row["phase"]: row for row in self.matrix["phases"]}
        self.assertEqual(phases["P01"]["adoption"]["runtime_corrections"], 2)
        self.assertEqual(phases["P02"]["adoption"]["stage64_changed_rom_bytes"], 2)
        self.assertEqual(phases["P03"]["adoption"]["reference_routes"], 118_528)
        self.assertEqual(phases["P03"]["adoption"]["side_change_1063_routes"], 159)
        self.assertEqual(phases["P03"]["adoption"]["stage65_routes_materialized"], 4)
        self.assertEqual(phases["P03"]["adoption"]["stage65_changed_rom_bytes"], 17)
        self.assertEqual(phases["P04"]["adoption"]["selected_candidate_records"], 52)
        self.assertEqual(phases["P04"]["adoption"]["runtime_adopted_records"], 0)
        self.assertEqual(phases["P05"]["adoption"]["performance_adjustments"], 0)
        self.assertEqual(phases["P06"]["adoption"]["species_adjustment_records"], 0)
        self.assertEqual(phases["P07"]["adoption"]["normal_to_vega_move"], 0)
        self.assertTrue(phases["P03"]["rom_reflection"]["reflected"])
        self.assertEqual(phases["P03"]["rom_reflection"]["stage"], 65)
        self.assertEqual(
            phases["P04"]["adoption"]["asset_staging"],
            {
                "mega_covered": 49, "mega_required": 49,
                "stones_covered": 45, "stones_required": 45,
                "palette_ready": 47, "palette_required": 49,
                "winds_waves_covered": 0, "winds_waves_required": 3,
                "asset_set_sha256": "ffd5e1f9c04646299af566f450f02f11e4b894e1c121dfb944637a56e24bef86",
            },
        )

    def test_stage65_chain_is_exact_but_not_release_candidate(self) -> None:
        chain = self.matrix["candidate_chain"]
        self.assertEqual(chain["active_stage"], 62)
        self.assertEqual(chain["selected_checkpoint_stage"], 65)
        self.assertTrue(chain["parent_chain_verified"])
        self.assertTrue(chain["stage65_integrated"])
        self.assertFalse(chain["release_candidate"])
        self.assertEqual(
            chain["inheritance"][3]["rom"]["sha256"],
            "116781c8be7cbd327ba7783ebdad9d9dda77554c33839eebed15ae6b065bb680",
        )
        self.assertEqual(chain["inheritance"][3]["parent_stage"], 64)
        self.assertEqual(chain["stage65_scope"]["routes_materialized"], 4)
        self.assertFalse(chain["stage65_scope"]["full_p03_done"])
        self.assertEqual(
            chain["registry"],
            {
                "path": "config/modernization_candidate.json",
                "schema_version": 2,
                "status": "P03_STAGE65_VERIFIED_CHECKPOINT",
                "completed_through": "USER-MODERNIZATION-P01",
                "checkpointed_through": "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE",
                "release_ready": False,
                "active_parent_stage": 62,
                "parent_stage": 64,
                "candidate_stage": 65,
            },
        )

    def test_checkpointed_through_does_not_extend_completed_through(self) -> None:
        registry = self.matrix["candidate_chain"]["registry"]
        self.assertEqual(registry["completed_through"], "USER-MODERNIZATION-P01")
        self.assertIn("P03", registry["checkpointed_through"])

        false_done = copy.deepcopy(self.matrix)
        false_done["candidate_chain"]["registry"]["completed_through"] = (
            "USER-MODERNIZATION-P03-STAGE65-CATERPIE-SLICE"
        )
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_done)

    def test_newly_tracked_checkpoints_are_explicitly_integrated(self) -> None:
        snapshot = self.matrix["snapshot"]
        self.assertFalse(snapshot["auto_discovery"])
        self.assertEqual(snapshot["parallel_outputs"], PARALLEL_OUTPUTS)
        pinned = {row["path"] for row in snapshot["tracked_inputs"]}
        for lane in PARALLEL_OUTPUTS.values():
            self.assertTrue(lane["included"])
            self.assertIn("INTEGRATED", lane["status"])
        self.assertIn("content/modernization/p03_stage65_checkpoint.json", pinned)
        self.assertIn("content/modernization/p03_stage65_mgba_runtime_gate.json", pinned)
        self.assertIn("content/modernization/p04_asset_import_manifest.json", pinned)

    def test_pinned_input_and_referenced_source_hashes_pass(self) -> None:
        snapshot = self.matrix["snapshot"]
        self.assertEqual(snapshot["tracked_input_count"], len(PINNED_TRACKED_INPUTS))
        self.assertEqual(len(snapshot["tracked_inputs"]), 25)
        self.assertEqual(len(self.matrix["referenced_source_bindings"]), 7)
        self.assertTrue(
            all(row["status"] == "PASS" for row in self.matrix["referenced_source_bindings"])
        )

    def test_hash_drift_is_rejected(self) -> None:
        raw = b"fixed input\n"
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(
            verify_exact_bytes("fixture", raw, len(raw), digest)["sha256"], digest
        )
        with self.assertRaises(ModernizationP08Error):
            verify_exact_bytes("fixture", raw + b"drift", len(raw), digest)

        mutated = copy.deepcopy(self.matrix)
        mutated["snapshot"]["tracked_inputs"][0]["sha256"] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(mutated)

    def test_active_baseline_change_is_rejected(self) -> None:
        active_doc = json.loads((ROOT / "config/active_play_baseline.json").read_text())
        active_doc["stage"] = 64
        markdown = (ROOT / "design/active_play_baseline.md").read_bytes()
        stage62 = self.matrix["active_play_baseline"]["rom"]
        with self.assertRaises(ModernizationP08Error):
            validate_active_baseline(active_doc, markdown, stage62)

        mutated = copy.deepcopy(self.matrix)
        mutated["active_play_baseline"]["changed"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(mutated)

    def test_candidate_hash_or_false_release_is_rejected(self) -> None:
        bad_hash = copy.deepcopy(self.matrix)
        bad_hash["candidate_artifacts"][0]["sha256"] = "f" * 64
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(bad_hash)

        false_release = copy.deepcopy(self.matrix)
        false_release["release_ready"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_release)

        false_p03_done = copy.deepcopy(self.matrix)
        false_p03_done["candidate_chain"]["stage65_scope"]["full_p03_done"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_p03_done)

        false_p04_rom = copy.deepcopy(self.matrix)
        false_p04_rom["phases"][3]["rom_reflection"]["reflected"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_p04_rom)

    def test_every_requirement_has_implementation_and_test_mapping(self) -> None:
        trace = self.matrix["traceability"]
        self.assertEqual(len(trace), 14)
        self.assertEqual(len({row["requirement_key"] for row in trace}), len(trace))
        for row in trace:
            self.assertTrue(row["implementation_evidence"])
            self.assertTrue(row["test_evidence"])
            self.assertTrue(row["status"])
        for phase in self.matrix["phases"]:
            self.assertTrue(phase["required_gates"])
            if phase["phase"] != "P01":
                self.assertTrue(phase["blockers"])

    def test_runtime_and_release_handoffs_stay_blocked(self) -> None:
        runtime = build_runtime_handoff(self.matrix)
        release = build_release_handoff(self.matrix)
        self.assertEqual(runtime["status"], STATUS)
        self.assertFalse(runtime["release_ready"])
        self.assertFalse(runtime["runtime_execution"]["new_rom_written"])
        self.assertEqual(release["status"], STATUS)
        self.assertFalse(release["release_ready"])
        self.assertFalse(release["promotion"]["authorized"])
        self.assertEqual(release["completed_phases"], ["P01"])
        self.assertEqual(release["candidate_stage"], 65)
        self.assertEqual(len(release["release_blockers"]), 7)

    def test_generated_outputs_are_deterministic(self) -> None:
        outputs = render_outputs(self.matrix)
        self.assertEqual(
            set(outputs),
            {
                "content/modernization/p08_integration_matrix.json",
                "content/modernization/p08_runtime_handoff.json",
                "content/modernization/p08_release_handoff.json",
            },
        )
        for relative, raw in outputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), raw, relative)
            self.assertIsInstance(json.loads(raw), dict)


if __name__ == "__main__":
    unittest.main()
