from __future__ import annotations

import unittest

from scripts.run_github_private_suite import command_plan


class GitHubPrivateSuiteTests(unittest.TestCase):
    def test_each_declared_suite_has_a_plan(self) -> None:
        for suite in (
            "battle-cli-offline", "stage62-check", "stage62-mgba",
            "full-unit", "all",
        ):
            with self.subTest(suite=suite):
                self.assertTrue(command_plan(suite, python="python3"))

    def test_all_does_not_repeat_focused_battle_unit(self) -> None:
        plan = command_plan("all", python="python3")
        flattened = [" ".join(command) for command in plan]
        self.assertIn("make test", flattened)
        self.assertFalse(any("test_codex_battle_runtime" in row for row in flattened))
        self.assertTrue(any("stage62_npc_placement" in row for row in flattened))
        self.assertTrue(any("catalog species search" in row for row in flattened))

    def test_unknown_suite_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            command_plan("shell", python="python3")


if __name__ == "__main__":
    unittest.main()
