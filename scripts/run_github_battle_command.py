#!/usr/bin/env python3
"""self-hosted GitHub Actionsから対戦CLIをshell injectionなしで実行する。"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Sequence


class BattleActionError(RuntimeError):
    pass


WRITE_ACTIONS = {
    "match_configure",
    "match_upload_team",
    "choose_team",
    "choose_move",
    "choose_switch",
    "match_forfeit",
    "match_disconnect",
    "reward_close",
}
READ_ACTIONS = {
    "doctor",
    "session_guide",
    "match_status",
    "match_view",
    "reward_status",
    "bank_status",
    "vault_status",
    "wait",
}
ALLOWED_ACTIONS = READ_ACTIONS | WRITE_ACTIONS
GIMMICKS = {"none", "mega", "zmove", "dynamax", "tera"}


def _integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise BattleActionError(f"{label}は{minimum}..{maximum}の整数でなければなりません")
    return value


def _selection(value: Any) -> str:
    if not isinstance(value, list) or len(value) != 3:
        raise BattleActionError("selectionは3件のlistでなければなりません")
    selected = [_integer(item, "selection", 1, 6) for item in value]
    if len(set(selected)) != 3:
        raise BattleActionError("selectionは重複できません")
    return ",".join(str(item) for item in selected)


def load_request(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BattleActionError(f"request JSONが不正です: {exc}") from exc
    if not isinstance(value, dict):
        raise BattleActionError("requestはJSON objectでなければなりません")
    action = value.get("action")
    if action not in ALLOWED_ACTIONS:
        raise BattleActionError(f"未対応actionです: {action!r}")
    return value


def command_for_request(request: dict[str, Any], team_file: Path | None) -> list[str]:
    action = request["action"]
    fixed = {
        "doctor": ["doctor", "--json"],
        "session_guide": ["session", "guide", "--json"],
        "match_status": ["match", "status", "--json"],
        "match_view": ["match", "view", "--json"],
        "reward_status": ["reward", "status", "--json"],
        "bank_status": ["bank", "status", "--json"],
        "vault_status": ["vault", "status", "--json"],
        "match_forfeit": ["choose", "forfeit", "--json"],
        "match_disconnect": ["match", "disconnect", "--json"],
        "reward_close": ["reward", "close", "--json"],
    }
    if action in fixed:
        return fixed[action]
    if action == "wait":
        timeout = _integer(request.get("timeout", 55), "timeout", 1, 55)
        return ["wait", "--timeout", str(timeout), "--compact", "--json"]
    if action == "match_configure":
        level = request.get("level")
        if level not in {"flat50", "open"}:
            raise BattleActionError("levelはflat50またはopenです")
        return ["match", "configure", "--level", str(level), "--json"]
    if action == "match_upload_team":
        if team_file is None:
            raise BattleActionError("match_upload_teamにはteamが必要です")
        return ["match", "upload-team", "--file", str(team_file), "--json"]
    if action == "choose_team":
        return ["choose", "team", _selection(request.get("selection")), "--json"]
    if action == "choose_move":
        index = _integer(request.get("index"), "move index", 1, 4)
        gimmick = request.get("gimmick", "none")
        if gimmick not in GIMMICKS:
            raise BattleActionError("gimmickが不正です")
        return [
            "choose", "move", str(index), "--gimmick", str(gimmick), "--json"
        ]
    if action == "choose_switch":
        index = _integer(request.get("index"), "switch index", 1, 3)
        return ["choose", "switch", str(index), "--json"]
    raise BattleActionError(f"commandを構築できません: {action}")


def _run(cli: str, arguments: Sequence[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [cli, *arguments], capture_output=True, text=True, check=False
    )
    stdout = completed.stdout.strip()
    if completed.returncode:
        detail = stdout or completed.stderr.strip() or f"exit={completed.returncode}"
        raise BattleActionError(f"CLI command failed ({' '.join(arguments[:2])}): {detail}")
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise BattleActionError("CLIがJSONを返しませんでした") from exc
    if not isinstance(value, dict):
        raise BattleActionError("CLI JSON rootがobjectではありません")
    return value


def execute(request: dict[str, Any], allow_write: bool, cli: str) -> dict[str, Any]:
    action = str(request["action"])
    if action in WRITE_ACTIONS and not allow_write:
        raise BattleActionError("write actionにはconfirm_write=trueが必要です")

    preflight = {
        "doctor": _run(cli, ["doctor", "--json"]),
        "session_guide": _run(cli, ["session", "guide", "--json"]),
        "match_status": _run(cli, ["match", "status", "--json"]),
    }
    team_file: Path | None = None
    with tempfile.TemporaryDirectory(prefix="github-vega-battle-") as temporary:
        if action == "match_upload_team":
            team = request.get("team")
            if not isinstance(team, dict):
                raise BattleActionError("teamはJSON objectでなければなりません")
            team_file = Path(temporary) / "team.json"
            team_file.write_text(
                json.dumps(team, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _run(cli, ["team", "validate", "--file", str(team_file), "--json"])
        if action in WRITE_ACTIONS:
            preflight["write_boundary_match_status"] = _run(
                cli, ["match", "status", "--json"]
            )
            if action == "reward_close":
                preflight["write_boundary_reward_status"] = _run(
                    cli, ["reward", "status", "--json"]
                )
        command = command_for_request(request, team_file)
        result = _run(cli, command)
    return {
        "schema_version": 1,
        "status": "PASS",
        "action": action,
        "write": action in WRITE_ACTIONS,
        "preflight": preflight,
        "result": result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-env", default="VEGA_BATTLE_REQUEST")
    parser.add_argument("--confirm-write", action="store_true")
    parser.add_argument("--cli", default="vega-codex-battle")
    args = parser.parse_args(argv)
    raw = os.environ.get(args.request_env)
    if raw is None:
        print(f"GitHub battle action: FAIL: env {args.request_env}がありません")
        return 2
    cli = shutil.which(args.cli) if "/" not in args.cli else args.cli
    if not cli or not Path(cli).is_file():
        print("GitHub battle action: FAIL: vega-codex-battleがありません")
        return 2
    try:
        result = execute(load_request(raw), args.confirm_write, cli)
    except BattleActionError as exc:
        print(f"GitHub battle action: FAIL: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
