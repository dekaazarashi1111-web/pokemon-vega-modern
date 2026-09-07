from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_github_patch_test.py"


class GitHubPatchTestRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "patch-test@example.invalid"],
            cwd=self.root, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Patch Test"],
            cwd=self.root, check=True,
        )
        (self.root / "tests").mkdir()
        (self.root / "tests/__init__.py").write_text("", encoding="utf-8")
        (self.root / "tests/test_fixture.py").write_text(
            """import unittest
from outside_helper import explode

class ExampleTests(unittest.TestCase):
    def test_pass(self):
        print('private ROM output must be discarded')
        self.assertTrue(True)

    def test_failure(self):
        self.assertEqual('actual-private-value', 'expected-private-value')

    @unittest.skip('private skip reason')
    def test_skip(self):
        pass

    def test_external_frame(self):
        explode()

class SetupErrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raise RuntimeError('private setup contents')

    def test_case(self):
        pass
""",
            encoding="utf-8",
        )
        # Importable during the test, but deliberately outside Git tracking.
        (self.root / "outside_helper.py").write_text(
            "def explode():\n    raise ValueError('outside private frame')\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "tests"], cwd=self.root, check=True,
        )
        subprocess.run(
            ["git", "commit", "-qm", "fixture"], cwd=self.root, check=True,
        )
        self.head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True,
        ).strip()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_case(self, suffix: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        output = self.root / f"{suffix}.json"
        test_id = f"tests.test_fixture.{suffix}"
        process = subprocess.run(
            [
                sys.executable, str(RUNNER), "--root", str(self.root),
                "--test-id", test_id, "--expected-sha", self.head,
                "--output", str(output),
            ],
            cwd=self.root, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
        return process, json.loads(output.read_text(encoding="utf-8"))

    def test_pass_result_has_exact_identity_and_no_output(self) -> None:
        process, data = self.run_case("ExampleTests.test_pass")
        self.assertEqual(process.returncode, 0)
        self.assertEqual(process.stdout.strip(), "GitHub patch test: SAFE_RESULT_WRITTEN")
        self.assertEqual(process.stderr, "")
        self.assertEqual(data["test_id"], "tests.test_fixture.ExampleTests.test_pass")
        self.assertEqual(data["counts"], {
            "tests": 1, "failures": 0, "errors": 0, "skips": 0,
        })
        self.assertEqual(data["result"], {
            "test_id": data["test_id"], "outcome": "PASS",
            "exception_class": None, "frames": [],
        })
        self.assertNotIn("private ROM output", process.stdout)

    def test_assertion_failure_contains_class_and_tracked_frame_only(self) -> None:
        process, data = self.run_case("ExampleTests.test_failure")
        self.assertEqual(process.returncode, 1)
        self.assertEqual(data["result"]["outcome"], "FAIL")
        self.assertEqual(data["result"]["exception_class"], "AssertionError")
        self.assertEqual(
            {row["path"] for row in data["result"]["frames"]},
            {"tests/test_fixture.py"},
        )
        serialized = json.dumps(data, sort_keys=True)
        self.assertNotIn("actual-private-value", serialized)
        self.assertNotIn("expected-private-value", serialized)
        self.assertNotIn(str(self.root), serialized)

    def test_setup_class_error_is_attributed_to_requested_test(self) -> None:
        process, data = self.run_case("SetupErrorTests.test_case")
        self.assertEqual(process.returncode, 1)
        self.assertEqual(data["counts"], {
            "tests": 0, "failures": 0, "errors": 1, "skips": 0,
        })
        self.assertEqual(data["result"]["test_id"], (
            "tests.test_fixture.SetupErrorTests.test_case"
        ))
        self.assertEqual(data["result"]["exception_class"], "RuntimeError")
        self.assertNotIn("private setup contents", json.dumps(data))

    def test_skip_is_a_noncommittable_safe_result_without_reason(self) -> None:
        process, data = self.run_case("ExampleTests.test_skip")
        self.assertEqual(process.returncode, 1)
        self.assertEqual(data["result"]["outcome"], "SKIP")
        self.assertEqual(data["counts"]["skips"], 1)
        self.assertNotIn("private skip reason", json.dumps(data))

    def test_untracked_external_frame_is_excluded(self) -> None:
        process, data = self.run_case("ExampleTests.test_external_frame")
        self.assertEqual(process.returncode, 1)
        self.assertEqual(data["result"]["exception_class"], "ValueError")
        self.assertNotIn("outside_helper.py", json.dumps(data))
        self.assertEqual(
            {row["path"] for row in data["result"]["frames"]},
            {"tests/test_fixture.py"},
        )

    def test_invalid_or_unloadable_test_id_writes_no_result(self) -> None:
        for test_id in (
            "../../private.test_case",
            "tests.test_fixture.MissingTests.test_missing",
        ):
            output = self.root / "invalid.json"
            output.unlink(missing_ok=True)
            process = subprocess.run(
                [
                    sys.executable, str(RUNNER), "--root", str(self.root),
                    "--test-id", test_id, "--expected-sha", self.head,
                    "--output", str(output),
                ],
                cwd=self.root, text=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False,
            )
            with self.subTest(test_id=test_id):
                self.assertEqual(process.returncode, 2)
                self.assertFalse(output.exists())
                self.assertEqual(process.stdout.strip(), "GitHub patch test: FAIL")

    def test_contract_failure_removes_a_stale_result(self) -> None:
        output = self.root / "stale.json"
        output.write_text('{"private": "stale"}\n', encoding="utf-8")
        process = subprocess.run(
            [
                sys.executable, str(RUNNER), "--root", str(self.root),
                "--test-id", "tests.test_fixture.Missing.test_case",
                "--expected-sha", self.head, "--output", str(output),
            ],
            cwd=self.root, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(process.returncode, 2)
        self.assertFalse(output.exists())
        self.assertNotIn("stale", process.stdout + process.stderr)

    def test_result_output_must_remain_inside_repository(self) -> None:
        output = self.root.parent / "escaped-patch-test-result.json"
        output.write_text("must remain\n", encoding="utf-8")
        process = subprocess.run(
            [
                sys.executable, str(RUNNER), "--root", str(self.root),
                "--test-id", "tests.test_fixture.ExampleTests.test_pass",
                "--expected-sha", self.head, "--output", str(output),
            ],
            cwd=self.root, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(output.read_text(encoding="utf-8"), "must remain\n")
        output.unlink()


if __name__ == "__main__":
    unittest.main()
