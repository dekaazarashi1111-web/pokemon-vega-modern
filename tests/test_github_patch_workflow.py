from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/chatgpt-comment-control.yml"
BRIDGE = ROOT / "scripts/github_large_file_bridge.py"


class GitHubPatchWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.bridge = BRIDGE.read_text(encoding="utf-8")

    def test_failed_test_cannot_reach_verify_commit_or_push(self) -> None:
        self.assertIn("id: patch_test", self.workflow)
        self.assertIn("continue-on-error: true", self.workflow)
        self.assertGreaterEqual(
            self.workflow.count("if: steps.patch_test.outcome == 'success'"), 2,
        )
        self.assertIn(
            'run: test "$PATCH_TEST_OUTCOME" = success', self.workflow,
        )
        commit = self.workflow.index(
            "検証済みpatchをcommitして同じPR branchへpush"
        )
        condition = self.workflow.rfind(
            "if: steps.patch_test.outcome == 'success'", 0, commit + 200,
        )
        self.assertGreater(condition, commit)
        self.assertIn("git push origin", self.workflow[commit:])

    def test_success_path_retains_patch_removal_verification_and_commit(self) -> None:
        self.assertIn("github_large_file_bridge.py verify-worktree", self.workflow)
        self.assertIn("git add -u -- .", self.workflow)
        self.assertIn("CHATGPT-BRIDGE: apply", self.workflow)
        self.assertIn("git push origin", self.workflow)

    def test_only_safe_json_is_transferred_and_raw_log_is_absent(self) -> None:
        self.assertNotIn("test.log", self.workflow)
        self.assertIn("test-result.json", self.workflow)
        self.assertIn("run_github_patch_test.py", self.workflow)
        self.assertIn("github_patch_test_summary.py", self.workflow)
        self.assertIn("vega-patch-test-${{ github.event.comment.id }}", self.workflow)
        self.assertNotIn("build/chatgpt-large-file-bridge/*", self.workflow)

    def test_malformed_result_cannot_reach_comment(self) -> None:
        self.assertIn(
            "if: steps.sanitize_patch_result.outcome == 'success'",
            self.workflow,
        )
        self.assertIn("sanitizer不成立時はコメントせずfail closed", self.workflow)
        self.assertIn(
            'run: test "$SUMMARY_OUTCOME" = success', self.workflow,
        )

    def test_runner_and_sanitizer_are_not_patchable(self) -> None:
        self.assertIn('"scripts/run_github_patch_test.py"', self.bridge)
        self.assertIn('"scripts/github_patch_test_summary.py"', self.bridge)


if __name__ == "__main__":
    unittest.main()
