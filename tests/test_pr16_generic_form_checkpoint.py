"""Fail-closed tests for the preserved generic FORM native acceptance original."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "pr16_generic_form_checkpoint.py"
spec = importlib.util.spec_from_file_location("pr16_generic_form_checkpoint", SCRIPT)
assert spec and spec.loader
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)


class GenericFormCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        directory = ROOT / checkpoint.DIRECTORY / str(checkpoint.RUN)
        cls.raw = (directory / "original.zip").read_bytes()
        cls.files = checkpoint.archive(cls.raw)
        cls.actions = checkpoint.load((directory / "actions.json").read_bytes())
        cls.aggregate = checkpoint.load(
            cls.files["pr16-generic-form-carry/result.json"]
        )

    def test_exact_original_builds_scoped_nonrelease_receipt(self) -> None:
        value = checkpoint.build(ROOT)
        self.assertTrue(value["generic_form_carry_physical_accepted"])
        self.assertFalse(value["fixed_form_transition_physical_accepted"])
        self.assertFalse(value["full_p03_acceptance"])
        self.assertFalse(value["successor_transfer_complete"])
        self.assertFalse(value["release_ready"])
        self.assertEqual(value["native_execution"]["acceptance_processes"], 2)
        self.assertEqual(value["native_execution"]["acceptance_fresh_cores"], 5)
        self.assertEqual(value["native_execution"]["diagnostic_processes"], 14)
        self.assertFalse(value["native_execution"]["diagnostics_are_acceptance"])
        self.assertFalse(value["accepted_scope"]["all_61_rows_individually_executed"])
        self.assertEqual(value["emulator_runs_by_this_verifier"], 0)

    def test_stored_receipt_is_exact_rebuild(self) -> None:
        stored = checkpoint.load((ROOT / checkpoint.RECEIPT).read_bytes())
        self.assertTrue(checkpoint.same(stored, checkpoint.build(ROOT)))

    def test_metadata_rejects_promoted_or_wrong_original(self) -> None:
        checkpoint.metadata(self.actions)
        for key, value in (
            ("head_sha", "0" * 40),
            ("run_attempt", 2),
            ("conclusion", "failure"),
            ("artifact_id", 0),
            ("sha256", "0" * 64),
        ):
            with self.subTest(key=key):
                altered = deepcopy(self.actions)
                altered[key] = value
                with self.assertRaises(checkpoint.CheckpointError):
                    checkpoint.metadata(altered)

    def test_raw_case_cannot_be_promoted_or_detached_from_aggregate(self) -> None:
        checkpoint._validate_case(self.files, self.aggregate, checkpoint.CASES[0])
        files = dict(self.files)
        path = "pr16-generic-form-carry/shaymin-four-slot-roundtrip.stdout"
        row = checkpoint.load(files[path])
        row["native_acceptance_claimed_for_all_61_individual_rows"] = True
        files[path] = checkpoint.stable(row)
        with self.assertRaises(checkpoint.CheckpointError):
            checkpoint._validate_case(files, self.aggregate, checkpoint.CASES[0])

    def test_guard_must_be_real_nonzero_host_write_failure(self) -> None:
        stem = "pr16-generic-form-carry/guard-bus8"
        checkpoint.process(self.files, stem, 1)
        self.assertEqual(
            self.files[stem + ".stderr"],
            b"P03 archive: host write after observation barrier\n",
        )
        files = dict(self.files)
        files[stem + ".stderr"] = b"PASS\n"
        self.assertNotEqual(
            files[stem + ".stderr"],
            b"P03 archive: host write after observation barrier\n",
        )

    def test_executed_source_binding_is_not_transferable_after_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = checkpoint.archive(
                self.files["pr16-generic-form-evidence/sources.zip"]
            )
            for name in checkpoint.SOURCE_BINDINGS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(snapshot[name])
            checkpoint._validate_sources(root, self.files)
            changed = root / checkpoint.SOURCE_BINDINGS[0]
            changed.write_bytes(changed.read_bytes() + b"\n")
            with self.assertRaises(checkpoint.CheckpointError):
                checkpoint._validate_sources(root, self.files)

    def test_diagnostics_remain_diagnostic_only(self) -> None:
        report = checkpoint._validate_diagnostics(self.files, self.aggregate)
        self.assertEqual(report["status"], "PASS_DIAGNOSTIC_ONLY")
        self.assertFalse(report["acceptance_claimed"])
        self.assertEqual(report["successful_fresh_cores"], 14)


if __name__ == "__main__":
    unittest.main()
