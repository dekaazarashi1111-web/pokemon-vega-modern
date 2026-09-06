from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.github_large_file_bridge import (
    BridgeError,
    apply_patch,
    render_find,
    render_slice,
    verify_worktree,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=root, text=True,
    ).strip()


class GitHubLargeFileBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "bridge@example.invalid"],
            cwd=self.root, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Bridge Test"],
            cwd=self.root, check=True,
        )
        (self.root / "tools").mkdir()
        (self.root / "tools/large.py").write_text(
            "one\ntwo\nthree\nfour\nfive\n", encoding="utf-8",
        )
        (self.root / ".chatgpt/patches").mkdir(parents=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "fixture"], cwd=self.root, check=True,
        )
        self.head = _git(self.root, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _commit_patch(self, text: str, name: str = "change.patch") -> str:
        path = self.root / ".chatgpt/patches" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", str(path)], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "patch request"],
            cwd=self.root, check=True,
        )
        return _git(self.root, "rev-parse", "HEAD")

    def test_read_returns_only_numbered_requested_lines(self) -> None:
        value = render_slice(self.root, "tools/large.py", 2, 4)
        self.assertIn("- lines: `2-4` / `5`", value)
        self.assertIn("2: two\n3: three\n4: four", value)
        self.assertNotIn("1: one", value)
        self.assertNotIn("5: five", value)

    def test_read_rejects_private_and_oversized_ranges(self) -> None:
        with self.assertRaises(BridgeError):
            render_slice(self.root, "inputs/private/game.gba", 1, 1)
        with self.assertRaises(BridgeError):
            render_slice(self.root, "tools/large.py", 1, 201)

    def test_find_returns_bounded_numbered_matches(self) -> None:
        value = render_find(self.root, "tools/large.py", "o")
        self.assertIn("- matches: `3` (showing first `3`)", value)
        self.assertIn("1: one", value)
        self.assertIn("2: two", value)
        self.assertIn("4: four", value)

    def test_find_rejects_missing_or_whitespace_query(self) -> None:
        with self.assertRaises(BridgeError):
            render_find(self.root, "tools/large.py", "missing")
        with self.assertRaises(BridgeError):
            render_find(self.root, "tools/large.py", "two words")

    def test_patch_modifies_tracked_source_and_deletes_request(self) -> None:
        head = self._commit_patch(
            """diff --git a/tools/large.py b/tools/large.py
--- a/tools/large.py
+++ b/tools/large.py
@@ -1,5 +1,5 @@
 one
-two
+TWO
 three
 four
 five
"""
        )
        targets = apply_patch(
            self.root, ".chatgpt/patches/change.patch", head,
        )
        self.assertEqual(targets, ["tools/large.py"])
        self.assertEqual(
            (self.root / "tools/large.py").read_text(encoding="utf-8"),
            "one\nTWO\nthree\nfour\nfive\n",
        )
        self.assertFalse((self.root / ".chatgpt/patches/change.patch").exists())
        self.assertEqual(
            verify_worktree(
                self.root, ".chatgpt/patches/change.patch",
                json.dumps(targets),
            ),
            targets,
        )

    def test_patch_rejects_wrong_head_and_workflow_target(self) -> None:
        head = self._commit_patch(
            """diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -1 +1 @@
-old
+new
"""
        )
        with self.assertRaises(BridgeError):
            apply_patch(
                self.root, ".chatgpt/patches/change.patch", "0" * 40,
            )
        with self.assertRaises(BridgeError):
            apply_patch(
                self.root, ".chatgpt/patches/change.patch", head,
            )

    def test_patch_rejects_create_delete_and_secret_candidates(self) -> None:
        head = self._commit_patch(
            """diff --git a/tools/new.py b/tools/new.py
new file mode 100644
--- /dev/null
+++ b/tools/new.py
@@ -0,0 +1 @@
+value = 1
"""
        )
        with self.assertRaises(BridgeError):
            apply_patch(
                self.root, ".chatgpt/patches/change.patch", head,
            )

        subprocess.run(
            ["git", "reset", "--hard", "-q", self.head],
            cwd=self.root, check=True,
        )
        secret_head = self._commit_patch(
            """diff --git a/tools/large.py b/tools/large.py
--- a/tools/large.py
+++ b/tools/large.py
@@ -1,5 +1,5 @@
 one
-two
+github_pat_abcdefghijklmnopqrstuvwxyz123456
 three
 four
 five
""",
            name="secret.patch",
        )
        with self.assertRaises(BridgeError):
            apply_patch(
                self.root, ".chatgpt/patches/secret.patch", secret_head,
            )


if __name__ == "__main__":
    unittest.main()
