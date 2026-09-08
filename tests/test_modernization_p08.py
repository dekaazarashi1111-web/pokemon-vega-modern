#!/usr/bin/env python3
"""工程8統合監査checkpointのfocused tests。"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_modernization_p08 import render_outputs  # noqa: E402
from tools.modernization_p08_integration import (  # noqa: E402
    ModernizationP08Error,
    PARALLEL_OUTPUTS,
    PINNED_IMPLEMENTATION_PATHS,
    PINNED_TRACKED_INPUTS,
    STATUS,
    audit_declared_source_rows,
    build_integration_fingerprint,
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
        self.assertEqual(phases["P03"]["adoption"]["stage65_preserved_ancestor_routes"], 4)
        self.assertEqual(phases["P03"]["adoption"]["stage65_changed_rom_bytes"], 17)
        self.assertEqual(phases["P03"]["adoption"]["stage66_routes_materialized"], 47_548)
        self.assertEqual(phases["P03"]["adoption"]["stage66_routes_remaining"], 70_980)
        self.assertEqual(phases["P03"]["adoption"]["stage66_changed_rom_bytes"], 81_693)
        self.assertEqual(phases["P04"]["adoption"]["selected_candidate_records"], 52)
        self.assertEqual(phases["P04"]["adoption"]["runtime_adopted_records"], 0)
        self.assertEqual(phases["P05"]["adoption"]["performance_adjustments"], 0)
        self.assertEqual(phases["P06"]["adoption"]["species_adjustment_records"], 0)
        self.assertEqual(phases["P07"]["adoption"]["normal_to_vega_move"], 0)
        self.assertTrue(phases["P03"]["rom_reflection"]["reflected"])
        self.assertEqual(phases["P03"]["rom_reflection"]["stage"], 66)
        self.assertEqual(
            phases["P04"]["adoption"]["asset_staging"],
            {
                "mega_covered": 49, "mega_required": 49,
                "stones_covered": 45, "stones_required": 45,
                "palette_ready": 49, "palette_required": 49,
                "winds_waves_covered": 0, "winds_waves_required": 3,
                "asset_set_sha256": "462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c",
            },
        )
        self.assertEqual(
            phases["P04"]["adoption"]["capacity_reservation"],
            {
                "species_form": [1621, 1672],
                "item": [999, 1043],
                "ability": [312, 317],
                "move": [1063, 1063],
                "capacity_basis_stage": 65,
                "fixed_table_count": 39,
                "fixed_table_delta_bytes": 20905,
                "aligned_bundle_bytes": 676772,
                "integration_modules_remaining_bytes": 1083916,
                "stage66_cross_check": {
                    "allocation_region": "future_tail",
                    "allocation_start": 33399368,
                    "allocation_size": 60116,
                    "allocation_end_exclusive": 33459484,
                    "stage65_future_tail_remaining_bytes": 155064,
                    "stage66_future_tail_remaining_bytes": 94948,
                    "p04_candidate_region": "integration_modules",
                    "p04_candidate_start": 21307984,
                    "p04_candidate_end_exclusive": 23068672,
                    "overlap": False,
                },
                "runtime_ready": False,
            },
        )

    def test_stage66_chain_is_exact_but_not_release_candidate(self) -> None:
        chain = self.matrix["candidate_chain"]
        self.assertEqual(chain["active_stage"], 62)
        self.assertEqual(chain["selected_checkpoint_stage"], 66)
        self.assertTrue(chain["parent_chain_verified"])
        self.assertTrue(chain["stage65_integrated"])
        self.assertTrue(chain["stage66_integrated"])
        self.assertFalse(chain["release_candidate"])
        self.assertEqual(
            chain["inheritance"][4]["rom"]["sha256"],
            "0d92f5377b4ad1a2fa5cbf905f81b5b6162e16cdd09a12c65c4a342e73c5c97e",
        )
        self.assertEqual(chain["inheritance"][4]["parent_stage"], 65)
        self.assertEqual(chain["stage65_scope"]["routes_materialized"], 4)
        self.assertFalse(chain["stage65_scope"]["full_p03_done"])
        self.assertEqual(chain["stage66_scope"]["routes_materialized"], 47_548)
        self.assertEqual(chain["stage66_scope"]["routes_remaining"], 70_980)
        self.assertFalse(chain["stage66_scope"]["full_p03_done"])
        self.assertEqual(
            chain["registry"],
            {
                "path": "config/modernization_candidate.json",
                "schema_version": 2,
                "status": "P03_STAGE66_BULK_VERIFIED_CHECKPOINT",
                "completed_through": "USER-MODERNIZATION-P01",
                "checkpointed_through": "USER-MODERNIZATION-P03-STAGE66-BULK-LEARNSET-CHECKPOINT",
                "checkpoint_commit": "90a1811964a19e3c058448af173007678b42a7e3",
                "release_ready": False,
                "active_parent_stage": 62,
                "parent_stage": 65,
                "candidate_stage": 66,
            },
        )

    def test_checkpointed_through_does_not_extend_completed_through(self) -> None:
        registry = self.matrix["candidate_chain"]["registry"]
        self.assertEqual(registry["completed_through"], "USER-MODERNIZATION-P01")
        self.assertIn("P03", registry["checkpointed_through"])

        false_done = copy.deepcopy(self.matrix)
        false_done["candidate_chain"]["registry"]["completed_through"] = (
            "USER-MODERNIZATION-P03-STAGE66-BULK-LEARNSET-CHECKPOINT"
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
        self.assertIn("config/modernization_p03_stage66.json", pinned)
        self.assertIn("content/modernization/p03_stage66_bulk_route_audit.json", pinned)
        self.assertIn("content/modernization/p03_stage66_change_audit.json", pinned)
        self.assertIn("content/modernization/p03_stage66_checkpoint.json", pinned)
        self.assertIn("content/modernization/p03_stage66_mgba_runtime_gate.json", pinned)
        self.assertIn("content/modernization/p04_asset_import_manifest.json", pinned)
        self.assertIn(
            "content/modernization/p04_capacity_allocation_manifest.json", pinned
        )
        artifacts = {row["path"] for row in self.matrix["candidate_artifacts"]}
        self.assertTrue(
            {
                "build/stages/66_modernization_p03_bulk_learnsets.gba",
                "build/stages/66_modernization_p03_bulk_learnsets.json",
                "build/stages/66_modernization_p03_allocation.json",
                "build/patches/stage65-to-stage66-modernization-p03-bulk-learnsets.bps",
                "build/patches/firered-jpn-rev0-to-stage66-modernization-p03-bulk-learnsets.bps",
            }
            <= artifacts
        )

    def test_pinned_input_and_referenced_source_hashes_pass(self) -> None:
        snapshot = self.matrix["snapshot"]
        self.assertEqual(snapshot["tracked_input_count"], len(PINNED_TRACKED_INPUTS))
        self.assertEqual(len(snapshot["tracked_inputs"]), 31)
        self.assertEqual(snapshot["implementation_input_count"], len(PINNED_IMPLEMENTATION_PATHS))
        self.assertEqual(
            len(snapshot["implementation_inputs"]), len(PINNED_IMPLEMENTATION_PATHS)
        )
        self.assertIn(
            "scripts/run_modernization_p03_stage66_mgba.py",
            {row["path"] for row in snapshot["implementation_inputs"]},
        )
        required_direct_implementation_inputs = {
            "scripts/build_trainer_v5_stage32.py",
            "tools/rom_allocator.py",
            "tools/release/__init__.py",
            "tools/release/bps.py",
            "Makefile",
            ".github/workflows/private-runtime.yml",
            ".github/workflows/chatgpt-comment-control.yml",
            "infra/setup_github_actions.sh",
            "infra/toolchain_manifest.json",
            "scripts/build_modernization_p03_stage66.py",
            "scripts/run_modernization_p03_stage66_mgba.py",
            "tools/modernization_p03_stage66.py",
            "tools/mgba_modernization_p03_stage66_smoke.c",
            "tests/test_modernization_p03_stage66.py",
        }
        self.assertTrue(
            required_direct_implementation_inputs
            <= {row["path"] for row in snapshot["implementation_inputs"]}
        )
        self.assertEqual(len(self.matrix["referenced_source_bindings"]), 27)
        self.assertTrue(
            all(row["status"] == "PASS" for row in self.matrix["referenced_source_bindings"])
        )

    def test_declared_evidence_source_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = "tools/source.py"
            path = root / relative
            path.parent.mkdir(parents=True)
            original = b"print('fixed')\n"
            path.write_bytes(original)
            row = {
                "path": relative,
                "size": len(original),
                "sha256": hashlib.sha256(original).hexdigest(),
            }
            self.assertEqual(
                audit_declared_source_rows(
                    root, [row], {relative}, binding="FIXTURE",
                )[0]["status"],
                "PASS",
            )
            path.write_bytes(b"print('drift')\n")
            with self.assertRaises(ModernizationP08Error):
                audit_declared_source_rows(
                    root, [row], {relative}, binding="FIXTURE",
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

        implementation_drift = copy.deepcopy(self.matrix)
        implementation_drift["snapshot"]["implementation_inputs"][0]["sha256"] = (
            "0" * 64
        )
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(implementation_drift)

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
        false_p03_done["candidate_chain"]["stage66_scope"]["full_p03_done"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_p03_done)

        false_p04_rom = copy.deepcopy(self.matrix)
        false_p04_rom["phases"][3]["rom_reflection"]["reflected"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_p04_rom)

    def test_every_requirement_has_implementation_and_test_mapping(self) -> None:
        trace = self.matrix["traceability"]
        self.assertEqual(len(trace), 16)
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
        self.assertEqual(
            runtime["integration_fingerprint"],
            self.matrix["snapshot"]["integration_fingerprint"],
        )
        self.assertEqual(release["status"], STATUS)
        self.assertFalse(release["release_ready"])
        self.assertFalse(release["promotion"]["authorized"])
        self.assertEqual(release["completed_phases"], ["P01"])
        self.assertEqual(release["candidate_stage"], 66)
        self.assertEqual(
            release["integration_fingerprint"],
            self.matrix["snapshot"]["integration_fingerprint"],
        )
        self.assertEqual(len(release["release_blockers"]), 7)

    def test_composite_fingerprint_changes_for_one_byte_implementation_drift(self) -> None:
        snapshot = self.matrix["snapshot"]
        original = snapshot["integration_fingerprint"]
        implementation = copy.deepcopy(snapshot["implementation_inputs"])
        source_path = ROOT / implementation[0]["path"]
        one_byte_drift = source_path.read_bytes() + b"\x00"
        implementation[0]["size"] = len(one_byte_drift)
        implementation[0]["sha256"] = hashlib.sha256(one_byte_drift).hexdigest()
        changed = build_integration_fingerprint(
            snapshot["tracked_inputs"],
            implementation,
            self.matrix["referenced_source_bindings"],
            self.matrix["candidate_artifacts"],
            self.matrix["phases"],
        )
        self.assertNotEqual(changed["sha256"], original["sha256"])
        self.assertNotEqual(
            changed["components"]["implementation_inputs"]["sha256"],
            original["components"]["implementation_inputs"]["sha256"],
        )

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
