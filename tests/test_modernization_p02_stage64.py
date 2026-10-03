from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts import build_modernization_p02_stage64 as stage64  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


class ModernizationP02Stage64Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / stage64.DEFAULT_CONFIG).read_text(encoding="utf-8")
        )
        outputs = cls.config["outputs"]
        cls.parent = (ROOT / cls.config["inputs"]["parent_rom"]["path"]).read_bytes()
        cls.output = (ROOT / outputs["rom"]).read_bytes()
        cls.metadata = json.loads(
            (ROOT / outputs["metadata"]).read_text(encoding="utf-8")
        )
        cls.checkpoint = json.loads(
            (ROOT / outputs["checkpoint"]).read_text(encoding="utf-8")
        )

    def test_patch_is_exactly_two_parameter_bytes_and_has_stable_keys(self) -> None:
        patch = self.checkpoint["patch"]
        self.assertEqual(patch["species_key"], "SPECIES_KEY_RAYQUAZA")
        self.assertEqual(patch["species_id"], 645)
        self.assertEqual(patch["target_species_key"], "SPECIES_KEY_RAYQUAZA_MEGA")
        self.assertEqual(patch["target_species_id"], 1092)
        self.assertEqual(patch["before_move_key"], "MOVE_KEY_OVERDRIVE")
        self.assertEqual(patch["after_move_key"], "MOVE_KEY_DRAGONASCENT")
        self.assertEqual(patch["changed_bytes"], 2)
        self.assertEqual(patch["changed_spans"], [{
            "start": 0x01F8E1BA,
            "end_exclusive": 0x01F8E1BC,
            "size": 2,
        }])
        differences = [
            index for index, (before, after) in enumerate(zip(self.parent, self.output, strict=True))
            if before != after
        ]
        self.assertEqual(differences, [0x01F8E1BA, 0x01F8E1BB])

    def test_entry_preimage_and_replacement_match_runtime_abi(self) -> None:
        offset = 0x01F8E1B8
        self.assertEqual(
            struct.unpack_from("<HHHH", self.parent, offset),
            (254, 773, 1092, 2),
        )
        self.assertEqual(
            struct.unpack_from("<HHHH", self.output, offset),
            (254, 630, 1092, 2),
        )
        rebuilt, audit = stage64.apply_rayquaza_patch(
            self.parent, self.config["patch"],
        )
        self.assertEqual(rebuilt, self.output)
        self.assertEqual(audit, self.checkpoint["patch"])
        self.assertEqual(
            audit["parameter_policy"]["historical_resolved_parameter_id"], 773,
        )
        self.assertEqual(
            audit["parameter_policy"]["modernization_resolved_parameter_id"], 630,
        )

    def test_wrong_parent_preimage_fails_closed(self) -> None:
        corrupted = bytearray(self.parent)
        corrupted[0x01F8E1BA] ^= 0x01
        with self.assertRaisesRegex(
            stage64.ModernizationP02Stage64Error, "preimage不一致",
        ):
            stage64.apply_rayquaza_patch(bytes(corrupted), self.config["patch"])

    def test_bps_outputs_round_trip_to_the_exact_checkpoint_rom(self) -> None:
        outputs = self.config["outputs"]
        incremental = (ROOT / outputs["incremental_bps"]).read_bytes()
        clean_bps = (ROOT / outputs["clean_bps"]).read_bytes()
        clean = (ROOT / self.config["inputs"]["clean_rom"]["path"]).read_bytes()
        self.assertEqual(apply_bps(self.parent, incremental), self.output)
        self.assertEqual(apply_bps(clean, clean_bps), self.output)
        self.assertEqual(
            hashlib.sha256(self.output).hexdigest(),
            "ddb9bf76d7f35c375d44941cd276f07e64501ed5cee34b8d448e76f0454095c3",
        )
        self.assertTrue(self.checkpoint["bps"]["incremental"]["round_trip"])
        self.assertTrue(self.checkpoint["bps"]["clean"]["round_trip"])

    def test_checkpoint_never_claims_unrun_runtime_acceptance(self) -> None:
        self.assertEqual(self.metadata["status"], "CHECKPOINT")
        self.assertFalse(self.metadata["done"])
        self.assertEqual(self.metadata["acceptance"]["mgba_runtime_gate"], "PASS")
        self.assertEqual(
            self.checkpoint["input"]["p02_mgba_runtime_gate"]["process_runs"], 2,
        )
        self.assertEqual(
            self.checkpoint["input"]["p02_mgba_runtime_gate"]["status"], "PASS",
        )
        self.assertEqual(
            self.metadata["acceptance"]["ability_move_cancel_item_save_reload_gate"],
            "NOT_RUN",
        )
        self.assertEqual(self.metadata["acceptance"]["task_completion"], "CHECKPOINT_NOT_DONE")
        self.assertTrue(self.checkpoint["producer_boundary"]["root_fix_applied"])
        self.assertFalse(
            self.checkpoint["producer_boundary"]["historical_outputs_overwritten"],
        )
        self.assertFalse(self.checkpoint["scope"]["active_play_baseline_changed"])
        self.assertFalse(self.checkpoint["scope"]["review_only_branches_applied"])

    def test_check_mode_is_deterministic_and_read_only(self) -> None:
        outputs = [ROOT / path for path in self.config["outputs"].values()]
        before = {path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()) for path in outputs}
        completed = subprocess.run(
            ["python3", "scripts/build_modernization_p02_stage64.py", "check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("P02 Stage64 check: CHECKPOINT", completed.stdout)
        after = {path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()) for path in outputs}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
