from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import build_fast_rom


class FastRomSelectionTests(unittest.TestCase):
    def test_ui_change_starts_at_ui(self) -> None:
        self.assertEqual(
            build_fast_rom.choose_start(["overlays/battle_ui/battle_ui.c"]),
            "battle-ui",
        )

    def test_core_change_wins_over_later_change(self) -> None:
        self.assertEqual(
            build_fast_rom.choose_start([
                "tools/mgba_first_battle_loop_smoke.c",
                "scripts/build_battle_core.py",
            ]),
            "battle-core",
        )

    def test_document_only_change_reuses_all_rom_stages(self) -> None:
        self.assertEqual(
            build_fast_rom.choose_start(["design/current_state.md"]),
            "final",
        )

    def test_test_only_change_reuses_all_rom_stages(self) -> None:
        self.assertEqual(
            build_fast_rom.choose_start(["tests/test_battle_ui.py"]),
            "final",
        )

    def test_shared_ram_ledger_change_starts_conservatively_at_core(self) -> None:
        self.assertEqual(
            build_fast_rom.choose_start(["config/ram_layout.csv"]),
            "battle-core",
        )

    def test_unknown_runtime_input_fails_conservatively_to_core(self) -> None:
        self.assertEqual(
            build_fast_rom.choose_start(["content/new_runtime.csv"]),
            "battle-core",
        )

    def test_git_input_inventory_includes_untracked_nonignored_files(self) -> None:
        completed = SimpleNamespace(
            returncode=0, stdout="tracked.py\nuntracked.py\n", stderr=""
        )
        with patch.object(build_fast_rom.subprocess, "run", return_value=completed) as run:
            self.assertEqual(
                build_fast_rom._git_files(), ["tracked.py", "untracked.py"]
            )
        self.assertEqual(
            run.call_args.args[0],
            ("git", "ls-files", "--cached", "--others", "--exclude-standard"),
        )


if __name__ == "__main__":
    unittest.main()
