from __future__ import annotations

import unittest

from scripts.github_result_summary import ResultSummaryError, render_summary


HEAD = "a" * 40
ROM_SHA = "b" * 64


def focused_result() -> dict:
    return {
        "head_sha": HEAD,
        "tests": 4,
        "failures": 2,
        "errors": 1,
        "skipped": 1,
        "expected_failures": 0,
        "unexpected_successes": 0,
        "details": [
            {
                "outcome": "FAIL",
                "test": "tests.test_example.ExampleTests.test_case",
                "exception_type": "AssertionError",
                "frames": [{"path": "tests/test_example.py", "line": 8}],
            },
            {
                "outcome": "FAIL",
                "test": "tests.test_example.ExampleTests.test_case",
                "exception_type": "AssertionError",
                "frames": [{"path": "tests/test_example.py", "line": 8}],
            },
            {
                "outcome": "ERROR",
                "test": "tests.test_example.ExampleTests.setUpClass",
                "exception_type": "RuntimeError",
                "frames": [{"path": "tools/example.py", "line": 12}],
            },
        ],
        "skip_records": [{
            "test": "tests.test_example.ExampleTests.test_skip",
            "reason_sha256": "c" * 64,
        }],
        "stage62_rom_unchanged": True,
        "stage62_rom_sha256": ROM_SHA,
    }


def full_result() -> dict:
    data = focused_result()
    data.update({
        "schema_version": 1,
        "seconds": 1.25,
        "expected_failure_tests": [],
        "unexpected_success_tests": [],
    })
    data["skip_records"][0]["reason_labels"] = ["T05 fixed inputs"]
    return data


class GitHubResultSummaryTests(unittest.TestCase):
    def test_focused_summary_collapses_duplicate_subtests(self) -> None:
        text = render_summary(
            focused_result(), kind="focused-unit", expected_sha=HEAD,
        )
        self.assertIn("failures=`2`", text)
        self.assertIn("`FAIL` ×`2`", text)
        self.assertIn("tests/test_example.py:8", text)
        self.assertNotIn("private input", text.lower())

    def test_full_summary_preserves_safe_skip_classification(self) -> None:
        text = render_summary(
            full_result(), kind="full-unit", expected_sha=HEAD,
        )
        self.assertIn("seconds: `1.25`", text)
        self.assertIn("labels=`T05 fixed inputs`", text)
        self.assertIn("reason_sha256=`" + "c" * 64 + "`", text)

    def test_head_schema_and_counts_are_exact(self) -> None:
        with self.assertRaises(ResultSummaryError):
            render_summary(focused_result(), kind="focused-unit", expected_sha="d" * 40)
        data = focused_result()
        data["private_message"] = "not allowed"
        with self.assertRaises(ResultSummaryError):
            render_summary(data, kind="focused-unit", expected_sha=HEAD)
        data = focused_result()
        data["failures"] = 1
        with self.assertRaises(ResultSummaryError):
            render_summary(data, kind="focused-unit", expected_sha=HEAD)

    def test_private_paths_and_arbitrary_exception_text_are_rejected(self) -> None:
        data = focused_result()
        data["details"][0]["frames"][0]["path"] = "/private/game.py"
        with self.assertRaises(ResultSummaryError):
            render_summary(data, kind="focused-unit", expected_sha=HEAD)
        data = focused_result()
        data["details"][0]["exception_type"] = "failure: secret contents"
        with self.assertRaises(ResultSummaryError):
            render_summary(data, kind="focused-unit", expected_sha=HEAD)

    def test_full_result_requires_safe_labels_and_duration(self) -> None:
        data = full_result()
        data["skip_records"][0]["reason_labels"] = ["private path"]
        with self.assertRaises(ResultSummaryError):
            render_summary(data, kind="full-unit", expected_sha=HEAD)
        data = full_result()
        data["seconds"] = True
        with self.assertRaises(ResultSummaryError):
            render_summary(data, kind="all", expected_sha=HEAD)

    def test_runner_redaction_sentinels_are_accepted(self) -> None:
        data = focused_result()
        data["details"][0]["test"] = "unittest.class_fixture"
        data["details"][1]["test"] = "unittest.redacted_identity"
        text = render_summary(data, kind="focused-unit", expected_sha=HEAD)
        self.assertIn("unittest.class_fixture", text)
        self.assertIn("unittest.redacted_identity", text)


if __name__ == "__main__":
    unittest.main()
