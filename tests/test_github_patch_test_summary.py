from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.github_patch_test_summary import (
    PatchTestSummaryError,
    render_summary,
)


TEST_ID = "tests.test_example.ExampleTests.test_case"


class GitHubPatchTestSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "summary@example.invalid"],
            cwd=self.root, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Summary Test"],
            cwd=self.root, check=True,
        )
        (self.root / "tests").mkdir()
        (self.root / "tests/test_example.py").write_text(
            "def tracked():\n    return True\n", encoding="utf-8",
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "fixture"], cwd=self.root, check=True,
        )
        self.head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=self.root, text=True,
        ).strip()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def result(self, outcome: str = "PASS") -> dict:
        counts = {"tests": 1, "failures": 0, "errors": 0, "skips": 0}
        exception = None
        frames: list[dict] = []
        if outcome == "FAIL":
            counts["failures"] = 1
            exception = "AssertionError"
            frames = [{"path": "tests/test_example.py", "line": 2}]
        elif outcome == "ERROR":
            counts.update({"tests": 0, "errors": 1})
            exception = "RuntimeError"
            frames = [{"path": "tests/test_example.py", "line": 1}]
        elif outcome == "SKIP":
            counts["skips"] = 1
        return {
            "schema_version": 1,
            "head_sha": self.head,
            "test_id": TEST_ID,
            "counts": counts,
            "result": {
                "test_id": TEST_ID,
                "outcome": outcome,
                "exception_class": exception,
                "frames": frames,
            },
        }

    def render(self, data: dict) -> str:
        return render_summary(
            data, root=self.root, expected_sha=self.head,
            expected_test_id=TEST_ID,
        )

    def test_pass_failure_error_and_skip_have_fixed_safe_fields(self) -> None:
        for outcome in ("PASS", "FAIL", "ERROR", "SKIP"):
            text = self.render(self.result(outcome))
            with self.subTest(outcome=outcome):
                self.assertIn(f"outcome: `{outcome}`", text)
                self.assertIn(f"test: `{TEST_ID}`", text)
                self.assertIn("例外本文・actual/expected値", text)
        failure = self.render(self.result("FAIL"))
        self.assertIn("AssertionError", failure)
        self.assertIn("tests/test_example.py:2", failure)

    def test_schema_head_test_and_counts_are_exact(self) -> None:
        mutations = []
        extra = self.result()
        extra["message"] = "private"
        mutations.append(extra)
        wrong_head = self.result()
        wrong_head["head_sha"] = "a" * 40
        mutations.append(wrong_head)
        wrong_test = self.result()
        wrong_test["result"]["test_id"] = "tests.test_other.X.test_y"
        mutations.append(wrong_test)
        wrong_counts = self.result("FAIL")
        wrong_counts["counts"]["failures"] = 0
        mutations.append(wrong_counts)
        for data in mutations:
            with self.subTest(data=data), self.assertRaises(PatchTestSummaryError):
                self.render(data)

    def test_untracked_private_absolute_and_traversal_frames_are_rejected(self) -> None:
        values = (
            "tests/untracked.py",
            "/private/game.py",
            "tests/../private.py",
            "inputs/private/secret.py",
            "tests/test_`injection`.py",
        )
        for path in values:
            data = self.result("ERROR")
            data["result"]["frames"] = [{"path": path, "line": 1}]
            with self.subTest(path=path), self.assertRaises(PatchTestSummaryError):
                self.render(data)

    def test_arbitrary_exception_text_and_extra_frame_fields_are_rejected(self) -> None:
        data = self.result("FAIL")
        data["result"]["exception_class"] = "AssertionError: actual=private"
        with self.assertRaises(PatchTestSummaryError):
            self.render(data)
        data = self.result("FAIL")
        data["result"]["frames"][0]["message"] = "private ROM value"
        with self.assertRaises(PatchTestSummaryError):
            self.render(data)

        data = self.result("FAIL")
        data["result"]["frames"][0]["line"] = 999
        with self.assertRaises(PatchTestSummaryError):
            self.render(data)

    def test_rendered_failure_cannot_contain_message_or_private_values(self) -> None:
        data = self.result("FAIL")
        rendered = self.render(data)
        serialized = json.dumps(data)
        for forbidden in (
            "actual-private", "expected-private", "/private/", "ROM contents",
        ):
            self.assertNotIn(forbidden, rendered)
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
