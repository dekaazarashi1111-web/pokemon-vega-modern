from __future__ import annotations

import unittest

from scripts.github_comment_control import CommentCommandError, parse_comment


class GitHubCommentControlTests(unittest.TestCase):
    def test_private_suite_and_optional_sha(self) -> None:
        sha = "a" * 40
        result = parse_comment(f"/vega-test stage62-check {sha}")
        self.assertEqual(result["kind"], "test")
        self.assertEqual(result["suite"], "stage62-check")
        self.assertEqual(result["expected_sha"], sha)
        self.assertFalse(result["confirm_write"])

    def test_all_suite(self) -> None:
        self.assertEqual(parse_comment("/vega-test all")["suite"], "all")

    def test_unknown_suite_is_rejected(self) -> None:
        with self.assertRaises(CommentCommandError):
            parse_comment("/vega-test arbitrary-shell")

    def test_malformed_sha_is_rejected(self) -> None:
        with self.assertRaises(CommentCommandError):
            parse_comment("/vega-test stage62-check deadbeef")

    def test_large_file_read_with_exact_head(self) -> None:
        sha = "b" * 40
        result = parse_comment(
            "/vega-read tools/stage61_interaction_oracle.py 21000 21199 "
            + sha
        )
        self.assertEqual(result["kind"], "read")
        self.assertEqual(result["path"], "tools/stage61_interaction_oracle.py")
        self.assertEqual(result["start_line"], "21000")
        self.assertEqual(result["end_line"], "21199")
        self.assertEqual(result["expected_sha"], sha)

    def test_large_file_read_rejects_traversal_and_oversized_range(self) -> None:
        with self.assertRaises(CommentCommandError):
            parse_comment("/vega-read ../secret 1 2")
        with self.assertRaises(CommentCommandError):
            parse_comment("/vega-read tools/large.py 1 201")

    def test_large_file_find_with_exact_head(self) -> None:
        sha = "d" * 40
        result = parse_comment(
            "/vega-find scripts/large.py target_symbol " + sha
        )
        self.assertEqual(result["kind"], "find")
        self.assertEqual(result["path"], "scripts/large.py")
        self.assertEqual(result["query"], "target_symbol")
        self.assertEqual(result["expected_sha"], sha)

    def test_large_file_patch_requires_safe_path_head_and_test(self) -> None:
        sha = "c" * 40
        test_id = "tests.test_module.TestClass.test_case"
        result = parse_comment(
            f"/vega-patch .chatgpt/patches/fix.patch {sha} {test_id}"
        )
        self.assertEqual(result["kind"], "patch")
        self.assertEqual(result["patch_path"], ".chatgpt/patches/fix.patch")
        self.assertEqual(result["test_id"], test_id)
        self.assertEqual(result["expected_sha"], sha)
        with self.assertRaises(CommentCommandError):
            parse_comment(f"/vega-patch ../fix.patch {sha} {test_id}")
        with self.assertRaises(CommentCommandError):
            parse_comment(
                f"/vega-patch .chatgpt/patches/fix.patch {sha} shell.command"
            )

    def test_read_action_requires_read_prefix(self) -> None:
        result = parse_comment('/vega-live {"action":"doctor"}')
        self.assertEqual(result["kind"], "live")
        self.assertEqual(result["action"], "doctor")
        self.assertFalse(result["confirm_write"])
        with self.assertRaises(CommentCommandError):
            parse_comment('/vega-live-write {"action":"doctor"}')

    def test_write_action_requires_write_prefix(self) -> None:
        result = parse_comment(
            '/vega-live-write {"action":"match_configure","level":"flat50"}'
        )
        self.assertEqual(result["action"], "match_configure")
        self.assertTrue(result["confirm_write"])
        with self.assertRaises(CommentCommandError):
            parse_comment(
                '/vega-live {"action":"match_configure","level":"flat50"}'
            )

    def test_live_json_is_canonicalized(self) -> None:
        result = parse_comment(
            '/vega-live { "timeout": 10, "action": "wait" }'
        )
        self.assertEqual(
            result["request_json"], '{"action":"wait","timeout":10}'
        )


if __name__ == "__main__":
    unittest.main()
