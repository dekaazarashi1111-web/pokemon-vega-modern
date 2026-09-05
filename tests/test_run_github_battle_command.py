from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_github_battle_command as runner  # noqa: E402


class GitHubBattleCommandTests(unittest.TestCase):
    def test_request_rejects_shell_or_unknown_actions(self) -> None:
        with self.assertRaisesRegex(runner.BattleActionError, "未対応action"):
            runner.load_request('{"action":"doctor; rm -rf /"}')
        with self.assertRaisesRegex(runner.BattleActionError, "JSON"):
            runner.load_request("not-json")

    def test_write_requires_confirmation_and_rereads_match_status(self) -> None:
        request = {"action": "choose_move", "index": 2, "gimmick": "none"}
        with self.assertRaisesRegex(runner.BattleActionError, "confirm_write"):
            runner.execute(request, False, "/fake/cli")
        calls: list[tuple[str, ...]] = []

        def fake_run(_cli: str, arguments: list[str]) -> dict:
            calls.append(tuple(arguments))
            return {"status": "ok"}

        with mock.patch.object(runner, "_run", side_effect=fake_run):
            result = runner.execute(request, True, "/fake/cli")
        self.assertTrue(result["write"])
        self.assertEqual(calls[0], ("doctor", "--json"))
        self.assertEqual(calls[1], ("session", "guide", "--json"))
        self.assertEqual(calls[2], ("match", "status", "--json"))
        self.assertEqual(calls[3], ("match", "status", "--json"))
        self.assertEqual(
            calls[4],
            ("choose", "move", "2", "--gimmick", "none", "--json"),
        )

    def test_team_selection_and_numeric_fields_are_bounded(self) -> None:
        self.assertEqual(
            runner.command_for_request(
                {"action": "choose_team", "selection": [1, 3, 6]}, None
            ),
            ["choose", "team", "1,3,6", "--json"],
        )
        with self.assertRaisesRegex(runner.BattleActionError, "重複"):
            runner.command_for_request(
                {"action": "choose_team", "selection": [1, 1, 2]}, None
            )
        with self.assertRaisesRegex(runner.BattleActionError, "1..4"):
            runner.command_for_request(
                {"action": "choose_move", "index": 5}, None
            )

    def test_read_action_runs_after_required_session_preflight(self) -> None:
        calls: list[tuple[str, ...]] = []

        def fake_run(_cli: str, arguments: list[str]) -> dict:
            calls.append(tuple(arguments))
            return {"status": "ok"}

        with mock.patch.object(runner, "_run", side_effect=fake_run):
            result = runner.execute({"action": "vault_status"}, False, "/fake/cli")
        self.assertFalse(result["write"])
        self.assertEqual(calls[-1], ("vault", "status", "--json"))


if __name__ == "__main__":
    unittest.main()
