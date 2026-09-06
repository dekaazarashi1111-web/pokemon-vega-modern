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
    "focused-unit",
    "stage62-check",
    "stage62-mgba",
    "full-unit",
    "all",
}
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
PATCH_PATH_PATTERN = re.compile(
    r"^\.chatgpt/patches/[A-Za-z0-9][A-Za-z0-9._-]{0,80}\.patch$"
)
TEST_ID_PATTERN = re.compile(
    r"^tests(?:\.[A-Za-z_][A-Za-z0-9_]*){2,}$"
)
SOURCE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9_./+-]+$")
FIND_QUERY_PATTERN = re.compile(r"^[A-Za-z0-9_.:/@+-]{1,120}$")
MAX_READ_LINES = 200


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
        "path": "",
        "start_line": "",
        "end_line": "",
        "query": "",
        "patch_path": "",
        "test_id": "",
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
        "path": "",
        "start_line": "",
        "end_line": "",
        "query": "",
        "patch_path": "",
        "test_id": "",
    }


def _read_command(raw: str) -> dict[str, Any]:
    fields = raw.split()
    if len(fields) not in {4, 5} or fields[0] != "/vega-read":
        raise CommentCommandError(
            "read commandは /vega-read <path> <start> <end> [expected-sha] です"
        )
    path = fields[1]
    if (not SOURCE_PATH_PATTERN.fullmatch(path) or path.startswith("/")
            or "\\" in path or ".." in path.split("/")):
        raise CommentCommandError("read pathは安全なPOSIX相対pathでなければなりません")
    try:
        start, end = int(fields[2]), int(fields[3])
    except ValueError as exc:
        raise CommentCommandError("start/endは整数でなければなりません") from exc
    if start <= 0 or end < start or end - start + 1 > MAX_READ_LINES:
        raise CommentCommandError(f"read範囲は1〜{MAX_READ_LINES}行です")
    expected_sha = fields[4].lower() if len(fields) == 5 else ""
    if expected_sha and not SHA_PATTERN.fullmatch(expected_sha):
        raise CommentCommandError("expected-shaは40桁hexでなければなりません")
    return {
        "kind": "read", "suite": "", "expected_sha": expected_sha,
        "action": "", "request_json": "", "confirm_write": False,
        "path": path, "start_line": str(start), "end_line": str(end),
        "query": "", "patch_path": "", "test_id": "",
    }


def _find_command(raw: str) -> dict[str, Any]:
    fields = raw.split()
    if len(fields) not in {3, 4} or fields[0] != "/vega-find":
        raise CommentCommandError(
            "find commandは /vega-find <path> <query> [expected-sha] です"
        )
    path, query = fields[1], fields[2]
    if (not SOURCE_PATH_PATTERN.fullmatch(path) or path.startswith("/")
            or "\\" in path or ".." in path.split("/")):
        raise CommentCommandError("find pathは安全なPOSIX相対pathでなければなりません")
    if not FIND_QUERY_PATTERN.fullmatch(query):
        raise CommentCommandError("find queryは安全な空白なし120文字以下に限定されます")
    expected_sha = fields[3].lower() if len(fields) == 4 else ""
    if expected_sha and not SHA_PATTERN.fullmatch(expected_sha):
        raise CommentCommandError("expected-shaは40桁hexでなければなりません")
    return {
        "kind": "find", "suite": "", "expected_sha": expected_sha,
        "action": "", "request_json": "", "confirm_write": False,
        "path": path, "start_line": "", "end_line": "", "query": query,
        "patch_path": "", "test_id": "",
    }


def _patch_command(raw: str) -> dict[str, Any]:
    fields = raw.split()
    if len(fields) != 4 or fields[0] != "/vega-patch":
        raise CommentCommandError(
            "patch commandは /vega-patch <patch-path> <expected-sha> <test-id> です"
        )
    patch_path, expected_sha, test_id = fields[1], fields[2].lower(), fields[3]
    if not PATCH_PATH_PATTERN.fullmatch(patch_path):
        raise CommentCommandError(
            "patch-pathは.chatgpt/patches/<safe-name>.patch限定です"
        )
    if not SHA_PATTERN.fullmatch(expected_sha):
        raise CommentCommandError("expected-shaは40桁hexでなければなりません")
    if not TEST_ID_PATTERN.fullmatch(test_id):
        raise CommentCommandError("test-idはtests.から始まるunittest ID限定です")
    return {
        "kind": "patch", "suite": "", "expected_sha": expected_sha,
        "action": "", "request_json": "", "confirm_write": False,
        "path": "", "start_line": "", "end_line": "",
        "query": "", "patch_path": patch_path, "test_id": test_id,
    }


def parse_comment(body: str) -> dict[str, Any]:
    raw = body.strip()
    if raw.startswith("/vega-test "):
        return _test_command(raw)
    if raw.startswith("/vega-read "):
        return _read_command(raw)
    if raw.startswith("/vega-find "):
        return _find_command(raw)
    if raw.startswith("/vega-patch "):
        return _patch_command(raw)
    if raw.startswith("/vega-live-write "):
        return _live_command(raw, write=True)
    if raw.startswith("/vega-live "):
        return _live_command(raw, write=False)
    raise CommentCommandError("未対応のVega comment commandです")


def _write_github_output(path: Path, result: dict[str, Any]) -> None:
    lines = []
    for key in (
        "kind", "suite", "expected_sha", "action", "request_json",
        "path", "start_line", "end_line", "query", "patch_path", "test_id",
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
