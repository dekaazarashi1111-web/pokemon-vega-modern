#!/usr/bin/env python3
"""Validate a /vega-patch test result and render a bounded safe summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Sequence


TOP_KEYS = {"schema_version", "head_sha", "test_id", "counts", "result"}
COUNT_KEYS = {"tests", "failures", "errors", "skips"}
RESULT_KEYS = {"test_id", "outcome", "exception_class", "frames"}
FRAME_KEYS = {"path", "line"}
TEST_ID = re.compile(r"^tests(?:\.[A-Za-z_][A-Za-z0-9_]*){2,}$")
EXCEPTION = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SOURCE_PATH = re.compile(r"^[A-Za-z0-9_./+-]+\.py$")
MAX_FRAMES = 30
MAX_COMMENT_BYTES = 16 * 1024


class PatchTestSummaryError(ValueError):
    pass


def _git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args], cwd=root, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if process.returncode:
        raise PatchTestSummaryError("git identity unavailable")
    return process.stdout.strip()


def _counter(counts: dict[str, Any], key: str) -> int:
    value = counts.get(key)
    if type(value) is not int or value < 0:
        raise PatchTestSummaryError(f"invalid counter: {key}")
    return value


def _validate_frame(root: Path, value: Any) -> tuple[str, int]:
    if not isinstance(value, dict) or set(value) != FRAME_KEYS:
        raise PatchTestSummaryError("source frame schema rejected")
    raw_path, line = value["path"], value["line"]
    if not isinstance(raw_path, str) or len(raw_path) > 300 \
            or not SOURCE_PATH.fullmatch(raw_path) \
            or type(line) is not int or line <= 0:
        raise PatchTestSummaryError("source frame value rejected")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or ".." in path.parts or "\\" in raw_path \
            or path.suffix != ".py" or not path.parts:
        raise PatchTestSummaryError("source frame path rejected")
    normalized = path.as_posix()
    if _git(root, "ls-files", "--error-unmatch", "--", normalized) != normalized:
        raise PatchTestSummaryError("source frame is not tracked")
    target = root.joinpath(*path.parts)
    if target.is_symlink() or not target.is_file():
        raise PatchTestSummaryError("source frame is not a regular file")
    try:
        maximum_line = len(target.read_bytes().splitlines())
    except OSError as exc:
        raise PatchTestSummaryError("source frame is unreadable") from exc
    if line > maximum_line:
        raise PatchTestSummaryError("source frame line is outside tracked source")
    return normalized, line


def validate_result(
    data: Any, *, root: Path, expected_sha: str, expected_test_id: str,
) -> dict[str, Any]:
    root = root.resolve()
    if not SHA40.fullmatch(expected_sha) \
            or _git(root, "rev-parse", "HEAD") != expected_sha:
        raise PatchTestSummaryError("exact HEAD mismatch")
    if not TEST_ID.fullmatch(expected_test_id):
        raise PatchTestSummaryError("expected test identity rejected")
    if not isinstance(data, dict) or set(data) != TOP_KEYS \
            or data.get("schema_version") != 1:
        raise PatchTestSummaryError("result schema rejected")
    if data.get("head_sha") != expected_sha \
            or data.get("test_id") != expected_test_id:
        raise PatchTestSummaryError("result identity mismatch")

    raw_counts = data.get("counts")
    if not isinstance(raw_counts, dict) or set(raw_counts) != COUNT_KEYS:
        raise PatchTestSummaryError("counter schema rejected")
    counts = {key: _counter(raw_counts, key) for key in COUNT_KEYS}
    if counts["tests"] not in {0, 1}:
        raise PatchTestSummaryError("single test count rejected")

    result = data.get("result")
    if not isinstance(result, dict) or set(result) != RESULT_KEYS \
            or result.get("test_id") != expected_test_id:
        raise PatchTestSummaryError("test result schema rejected")
    outcome = result.get("outcome")
    if outcome not in {"PASS", "FAIL", "ERROR", "SKIP"}:
        raise PatchTestSummaryError("test outcome rejected")
    exception = result.get("exception_class")
    if outcome in {"FAIL", "ERROR"}:
        if not isinstance(exception, str) or len(exception) > 128 \
                or not EXCEPTION.fullmatch(exception):
            raise PatchTestSummaryError("exception class rejected")
    elif exception is not None:
        raise PatchTestSummaryError("unexpected exception class")

    frames_value = result.get("frames")
    if not isinstance(frames_value, list) or len(frames_value) > MAX_FRAMES:
        raise PatchTestSummaryError("source frames rejected")
    frames = [_validate_frame(root, frame) for frame in frames_value]
    if len(frames) != len(set(frames)):
        raise PatchTestSummaryError("duplicate source frame rejected")
    if outcome in {"PASS", "SKIP"} and frames:
        raise PatchTestSummaryError("unexpected source frame")

    f, e, s, tests = (
        counts["failures"], counts["errors"], counts["skips"],
        counts["tests"],
    )
    valid_counts = (
        outcome == "PASS" and (tests, f, e, s) == (1, 0, 0, 0)
        or outcome == "FAIL" and tests == 1 and f >= 1 and e == s == 0
        or outcome == "ERROR" and tests in {0, 1} and e >= 1 and f == s == 0
        or outcome == "SKIP" and (tests, f, e, s) == (1, 0, 0, 1)
    )
    if not valid_counts:
        raise PatchTestSummaryError("outcome counters disagree")
    return {
        "counts": counts,
        "outcome": outcome,
        "exception_class": exception,
        "frames": frames,
    }


def render_summary(
    data: Any, *, root: Path, expected_sha: str, expected_test_id: str,
) -> str:
    result = validate_result(
        data, root=root, expected_sha=expected_sha,
        expected_test_id=expected_test_id,
    )
    counts = result["counts"]
    locations = ", ".join(
        f"{path}:{line}" for path, line in result["frames"]
    ) or "-"
    lines = [
        "<!-- vega-patch-test-result -->",
        "#### Safe unittest result",
        "",
        f"- test: `{expected_test_id}`",
        f"- outcome: `{result['outcome']}`",
        "- counts: " + ", ".join(
            f"{key}=`{counts[key]}`"
            for key in ("tests", "failures", "errors", "skips")
        ),
        f"- exception class: `{result['exception_class'] or '-'}`",
        f"- tracked frames: `{locations}`",
        "",
        "例外本文・actual/expected値・subtest値・private path・生ログは含みません。",
        "",
    ]
    rendered = "\n".join(lines)
    if len(rendered.encode("utf-8")) > MAX_COMMENT_BYTES:
        raise PatchTestSummaryError("summary exceeds comment boundary")
    return rendered


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--expected-test-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        rendered = render_summary(
            data, root=args.root, expected_sha=args.expected_sha,
            expected_test_id=args.expected_test_id,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    except (OSError, json.JSONDecodeError, PatchTestSummaryError):
        print("GitHub patch test summary: FAIL")
        return 2
    print("GitHub patch test summary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
