from __future__ import annotations

import csv
import hashlib
import json
import stat
import subprocess
import unittest
from pathlib import Path

from scripts import build_factory_high_modes_v2 as builder
from tools.release.bps import apply_bps


ROOT = Path(__file__).resolve().parents[1]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class FactoryHighModesV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / builder.CONFIG).read_text(encoding="utf-8"))
        cls.outputs = builder.build_outputs()
        cls.model = json.loads(cls.outputs[builder.OUTPUT_MODEL.as_posix()])
        cls.final_meta = json.loads((ROOT / builder.OUTPUT_META).read_text(encoding="utf-8"))
        cls.matrix = json.loads((ROOT / builder.OUTPUT_MODE_MATRIX).read_text(encoding="utf-8"))

    def test_fixed_inputs_and_private_guard(self) -> None:
        inputs = self.config["inputs"]
        for key in ("stage41_rom", "stage41_metadata", "stage41_allocation",
                    "stage41_clean_bps", "clean_rom", "submission_zip"):
            raw = (ROOT / inputs[key]["path"]).read_bytes()
            self.assertEqual(inputs[key]["sha256"], sha(raw), key)
            if "size" in inputs[key]:
                self.assertEqual(inputs[key]["size"], len(raw), key)
        private = ROOT / inputs["submission_zip"]["path"]
        self.assertEqual(0o444, stat.S_IMODE(private.stat().st_mode))
        tracked = subprocess.run(
            ["git", "ls-files", "userfile", "inputs/private"], cwd=ROOT,
            check=True, text=True, capture_output=True,
        ).stdout.strip()
        self.assertEqual("inputs/private/.gitkeep", tracked)

    def test_canonical_counts_slots_and_existing_semantics(self) -> None:
        self.assertEqual(
            {"mode_count": 24, "requirement_count": 28, "rental_count": 248,
             "profile_count": 55, "reward_count": 16, "dialogue_count": 28,
             "batch_count": 7, "stable_key_duplicates": 0,
             "unresolved_references": 0, "open_questions": 0},
            self.model["normalization"],
        )
        self.assertEqual(list(range(24)), [row["slot"] for row in self.model["modes"]])
        with (ROOT / "manifests/facility_modes.csv").open(
                encoding="utf-8", newline="") as stream:
            old = list(csv.DictReader(stream))
        for expected, actual in zip(old, self.model["modes"][:16]):
            self.assertEqual(expected["mode_key"], actual["mode_key"])
            self.assertEqual(expected["tier"], actual["tier"])
            self.assertEqual(int(expected["battle_count"]), actual["round_battle_count"])
            self.assertEqual(expected["unlock_key"], actual["unlock_key"])
            self.assertEqual(expected["rental_pool_key"], actual["rental_pool_key"])
            self.assertEqual(expected["ai_profile_key"], actual["ai_profile_key"])

    def test_trial_oracle_and_packed_save_contract(self) -> None:
        trial = self.final_meta["trial_oracle"]
        self.assertEqual(3, trial["round_battles"])
        self.assertEqual(9, trial["bp"])
        self.assertEqual(600, trial["snapshot_bytes"])
        self.assertEqual(trial["masked_sha256_before"], trial["masked_sha256_after"])
        source = (ROOT / "overlays/factory_high_modes_v2/factory_high_modes_v2.c").read_text(
            encoding="utf-8")
        self.assertIn("HIGH_PENDING_BATTLE_MASK = 0x07u", source)
        self.assertIn("HIGH_PENDING_MODE_SHIFT = 3u", source)
        self.assertIn("HIGH_MARKER_GIMMICK_MASK = 0x38u", source)
        self.assertIn("HIGH_MARKER_UBER = 0x40u", source)
        self.assertIn("return (u8)(value & 0x7Fu);", source)

    def test_finite_generator_full_seed_equivalence_matrix(self) -> None:
        self.assertEqual("PASS", self.matrix["status"])
        self.assertEqual(7440, self.matrix["row_count"])
        self.assertEqual(24, self.matrix["mode_count"])
        self.assertEqual(30, self.matrix["option_variant_count"])
        self.assertLessEqual(self.matrix["maximum_rental_scan_attempts"], 248)
        self.assertLessEqual(self.matrix["maximum_subset_attempts"], 256)
        self.assertTrue(all(self.matrix["checks"].values()))
        self.assertEqual("PASS", self.matrix["mgba"]["status"])
        source = (ROOT / "overlays/factory_high_modes_v2/factory_high_modes_v2.c").read_text(
            encoding="utf-8")
        self.assertNotIn("while (1", source)
        self.assertIn("attempt < FACTORY_HIGH_RENTAL_COUNT", source)
        self.assertIn("combination < (u16)(1u << candidate_count)", source)

    def test_reward_schedule_and_atomic_claims(self) -> None:
        rewards = self.model["rewards"]
        self.assertEqual(
            [9, 0, 0, 0, 21, 12, 0, 0, 35, 25, 0, 0, 100, 0, 0, 0],
            [row["bp_amount"] for row in rewards],
        )
        self.assertEqual(
            [255, 1, 2, 10, 255, 11, 12, 13,
             255, 14, 15, 16, 255, 8, 9, 17],
            [row["claim_bit"] for row in rewards],
        )
        source = (ROOT / "overlays/factory_high_modes_v2/factory_high_modes_v2.c").read_text(
            encoding="utf-8")
        self.assertIn("transaction_begin();", source)
        self.assertIn("rollback_items(grants, grant_count);", source)
        self.assertIn("gFactoryHighCreditThresholds[index]", source)
        self.assertIn("HIGH_CLAIM_SHINY_DUE", source)

    def test_generated_files_match_deterministic_builder(self) -> None:
        dynamic = {
            builder.OUTPUT_META.as_posix(), builder.OUTPUT_AUDIT.as_posix(),
            builder.OUTPUT_COVERAGE.as_posix(), builder.OUTPUT_REPORT.as_posix(),
            builder.OUTPUT_MODE_MATRIX.as_posix(),
        }
        for relative, expected in self.outputs.items():
            if relative not in dynamic:
                self.assertEqual(expected, (ROOT / relative).read_bytes(), relative)
        self.assertEqual("PASS", self.final_meta["status"])
        self.assertTrue(all(self.final_meta["static_acceptance"].values()))

    def test_declared_spans_allocator_and_upstream_regression(self) -> None:
        self.assertEqual(0, self.final_meta["change_audit"]["outside_declared_span_count"])
        self.assertEqual(0, self.final_meta["change_audit"]["declared_span_overlap_count"])
        self.assertEqual({"rom": 0, "ram": 0, "save": 0, "ui": 0, "hook": 0},
                         self.final_meta["overlap_audit"])
        self.assertEqual(5, self.final_meta["consumer_bindings"]["patch_count"])
        self.assertEqual(0, self.final_meta["upstream_regression"]
                         ["previous_allocations_changed_outside_roots"])
        allocation = json.loads((ROOT / builder.OUTPUT_ALLOC).read_text(encoding="utf-8"))
        self.assertEqual(0, allocation["summaries"]["overlap_count"])

    def test_incremental_and_clean_bps_round_trip(self) -> None:
        inputs = self.config["inputs"]
        outputs = self.config["outputs"]
        stage41 = (ROOT / inputs["stage41_rom"]["path"]).read_bytes()
        clean = (ROOT / inputs["clean_rom"]["path"]).read_bytes()
        stage42 = (ROOT / outputs["rom"]).read_bytes()
        incremental = (ROOT / outputs["incremental_bps"]).read_bytes()
        direct = (ROOT / outputs["clean_bps"]).read_bytes()
        self.assertEqual(stage42, apply_bps(stage41, incremental))
        self.assertEqual(stage42, apply_bps(clean, direct))

    def test_exact_rom_mgba_quick_full(self) -> None:
        outputs = self.config["outputs"]
        documents = [json.loads((ROOT / outputs[key]).read_text(encoding="utf-8"))
                     for key in ("mgba_quick", "mgba_full")]
        for mode, document in zip(("quick", "full"), documents):
            self.assertEqual(mode, document["mode"])
            self.assertEqual("PASS", document["status"])
            self.assertEqual(0, document["warnings"])
            self.assertTrue(all(document["tests"].values()))
            self.assertTrue(all(document["acceptance_checks"].values()))
        self.assertEqual(documents[0]["result_identity"], documents[1]["result_identity"])

    def test_clean_rebuild_evidence(self) -> None:
        evidence = json.loads((ROOT / self.config["outputs"]["clean_rebuild"])
                              .read_text(encoding="utf-8"))
        self.assertEqual("PASS", evidence["status"])
        self.assertTrue(evidence["private_submission_unchanged"])
        self.assertTrue(all(evidence["acceptance"].values()))
        self.assertTrue(evidence["bps"]["chain_direct_identity_equal"])
        self.assertEqual(2, evidence["mgba"]["process_count"])


if __name__ == "__main__":
    unittest.main()
