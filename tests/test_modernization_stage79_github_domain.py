"""Regression tests for the Actions wrapper; no product ROM or mGBA required."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_modernization_stage79_github_domain.py"
spec = importlib.util.spec_from_file_location("stage79_github_domain", SCRIPT)
assert spec is not None and spec.loader is not None
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class DomainLifetimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "stage78.gba"
        self.source.write_bytes(b"test ROM identity, not a product ROM")
        self.output = self.root / "output"
        self.work = None
        self.private = None
        self.runner_result = {"status": "PASS"}
        self.completed = subprocess.CompletedProcess(
            ["runner"], 0, json.dumps(self.runner_result), "runner diagnostic\n"
        )
        self.domain = {
            "id": "p03", "state": "READY", "timeout_seconds": 1,
            "runner": {"path": "test-runner.c"},
        }
        self.identity = self.identify("stage78.gba", "test")
        self.orchestrator = SimpleNamespace(
            READY="READY", TASK="TEST-STAGE79", STAGE=79,
            _atomic_write=lambda path, data: path.write_bytes(data),
            _sha=lambda data: hashlib.sha256(data).hexdigest(),
            _stable=lambda value: json.dumps(value, sort_keys=True).encode(),
            _integer=lambda value, label: int(value),
            _identity=self.identify,
            _compile=mock.Mock(return_value={"status": "compiled"}),
            _command=self.command,
            _validate_result=mock.Mock(),
            _validate_result_record=mock.Mock(),
        )
        self.stage_plan = {"plan_fingerprint": "test-fingerprint"}
        patches = [
            mock.patch.object(helper, "ROOT", self.root),
            mock.patch.object(helper, "_load_orchestrator", return_value=self.orchestrator),
            mock.patch.object(helper, "_context", return_value=(
                self.stage_plan, {"domains": [self.domain]}, self.identity,
            )),
            mock.patch.object(helper.subprocess, "run", side_effect=self.execute),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def identify(self, path, label):
        data = (self.root / path).read_bytes()
        return {"path": path, "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}

    def command(self, domain, executable, private, digest, work, config):
        self.work = work
        self.private = private
        self.assertTrue(private.is_file())
        self.assertEqual(private.stat().st_mode & 0o777, 0o444)
        self.assertEqual(private.read_bytes(), self.source.read_bytes())
        return [str(executable), str(private)]

    def execute(self, command, **kwargs):
        self.assertTrue(self.private.is_file())
        return self.completed

    def run_domain(self):
        return helper.run_domain(Path("unused-config.json"), "p03", self.output)

    def assert_cleaned(self):
        self.assertIsNotNone(self.work)
        self.assertFalse(self.work.exists())
        self.assertFalse(self.private.exists())

    def test_pass_survives_temporary_directory_cleanup(self):
        result = self.run_domain()
        self.assertEqual(result["status"], "DOMAIN_PASS")
        self.assert_cleaned()
        record = json.loads((self.output / "result.json").read_text())
        self.assertEqual(record["input_rom"], self.identity)
        self.assertEqual(record["runner_result"], self.runner_result)
        self.orchestrator._validate_result.assert_called_once_with(
            self.domain, self.runner_result, self.identity["sha256"]
        )
        self.orchestrator._validate_result_record.assert_called_once()

    def test_nonzero_reports_runner_failure_and_preserves_logs(self):
        self.completed.returncode = 7
        with self.assertRaisesRegex(helper.Stage79GithubDomainError, r"mGBA失敗\(7\)"):
            self.run_domain()
        self.assert_cleaned()
        self.assertEqual((self.output / "runner.stdout.json").read_text(), self.completed.stdout)
        self.assertEqual((self.output / "runner.stderr.log").read_text(), self.completed.stderr)
        self.assertFalse((self.output / "result.json").exists())
        self.orchestrator._validate_result.assert_not_called()

    def test_private_rom_mutation_is_rejected(self):
        def mutate(command, **kwargs):
            self.private.chmod(0o600)
            self.private.write_bytes(b"mutated")
            return self.completed
        with mock.patch.object(helper.subprocess, "run", side_effect=mutate):
            with self.assertRaisesRegex(helper.Stage79GithubDomainError, "ROM identity"):
                self.run_domain()
        self.assert_cleaned()
        self.assertFalse((self.output / "result.json").exists())

    def test_source_rom_mutation_is_rejected(self):
        def mutate(command, **kwargs):
            self.source.write_bytes(b"mutated")
            return self.completed
        with mock.patch.object(helper.subprocess, "run", side_effect=mutate):
            with self.assertRaisesRegex(helper.Stage79GithubDomainError, "ROM identity"):
                self.run_domain()
        self.assert_cleaned()
        self.assertFalse((self.output / "result.json").exists())

    def test_invalid_stdout_is_not_cached(self):
        self.completed.stdout = "not JSON"
        with self.assertRaisesRegex(helper.Stage79GithubDomainError, "stdout JSON"):
            self.run_domain()
        self.assert_cleaned()
        self.assertFalse((self.output / "result.json").exists())

    def test_result_validation_failure_is_not_cached(self):
        self.orchestrator._validate_result.side_effect = RuntimeError("contract mismatch")
        with self.assertRaisesRegex(RuntimeError, "contract mismatch"):
            self.run_domain()
        self.assert_cleaned()
        self.assertFalse((self.output / "result.json").exists())


if __name__ == "__main__":
    unittest.main()
