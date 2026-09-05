#!/usr/bin/env python3
"""GitHub PRコメントを固定allowlistのActions要求へ変換する。"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from scripts.run_github_battle_command import (
        READ_ACTIONS,
        WRITE_ACTIONS,
        BattleActionError,
        load_request,
    )
except ModuleNotFoundError:  # `python3 scripts/github_comment_control.py`
    from run_github_battle_command import (  # type: ignore[no-redef]
        READ_ACTIONS,
        WRITE_ACTIONS,
        BattleActionError,
        load_request,
    )


PRIVATE_SUITES = {
    "battle-cli-offline",
    "stage62-check",
    "stage62-mgba",
    "full-unit",
    "all",
}
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


class CommentCommandError(ValueError):
    pass


def _test_command(raw: str) -> dict[str, Any]:
    fields = raw.split()
    if len(fields) not in {2, 3} or fields[0] != "/vega-test":
        raise CommentCommandError(
            "test commandは /vega-test <suite> [expected-sha] です"
        )
    suite = fields[1]
    if suite not in PRIVATE_SUITES:
        raise CommentCommandError(f"未対応suiteです: {suite}")
    expected_sha = fields[2].lower() if len(fields) == 3 else ""
    if expected_sha and not SHA_PATTERN.fullmatch(expected_sha):
        raise CommentCommandError("expected-shaは40桁hexでなければなりません")
    return {
        "kind": "test",
        "suite": suite,
        "expected_sha": expected_sha,
        "action": "",
        "request_json": "",
        "confirm_write": False,
    }


def _live_command(raw: str, *, write: bool) -> dict[str, Any]:
    prefix = "/vega-live-write " if write else "/vega-live "
    if not raw.startswith(prefix):
        raise CommentCommandError("live command prefixが不正です")
    encoded = raw[len(prefix):].strip()
    if not encoded:
        raise CommentCommandError("live commandのJSON requestがありません")
    try:
        request = load_request(encoded)
    except BattleActionError as exc:
        raise CommentCommandError(str(exc)) from exc
    action = str(request["action"])
    allowed = WRITE_ACTIONS if write else READ_ACTIONS
    if action not in allowed:
        boundary = "write" if write else "read-only"
        raise CommentCommandError(
            f"{boundary} prefixではaction {action!r}を実行できません"
        )
    return {
        "kind": "live",
        "suite": "",
        "expected_sha": "",
        "action": action,
        "request_json": json.dumps(
            request, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        "confirm_write": write,
    }


def parse_comment(body: str) -> dict[str, Any]:
    raw = body.strip()
    if raw.startswith("/vega-test "):
        return _test_command(raw)
    if raw.startswith("/vega-live-write "):
        return _live_command(raw, write=True)
    if raw.startswith("/vega-live "):
        return _live_command(raw, write=False)
    raise CommentCommandError("未対応のVega comment commandです")


def _write_github_output(path: Path, result: dict[str, Any]) -> None:
    lines = []
    for key in (
        "kind", "suite", "expected_sha", "action", "request_json",
    ):
        lines.append(f"{key}={result[key]}")
    lines.append(
        f"confirm_write={'true' if result['confirm_write'] else 'false'}"
    )
    with path.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-env", default="GITHUB_COMMENT_BODY")
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    body = os.environ.get(args.body_env)
    if body is None:
        print(f"GitHub comment control: FAIL: env {args.body_env}がありません")
        return 2
    try:
        result = parse_comment(body)
    except CommentCommandError as exc:
        print(f"GitHub comment control: FAIL: {exc}")
        return 2
    if args.github_output is not None:
        _write_github_output(args.github_output, result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
