#!/usr/bin/env python3
"""Private testの限定result.jsonを安全なPRコメントへ変換する。"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Sequence


COUNTERS = (
    "tests", "failures", "errors", "skipped",
    "expected_failures", "unexpected_successes",
)
FOCUSED_KEYS = {
    "head_sha", *COUNTERS, "details", "skip_records",
    "stage62_rom_unchanged", "stage62_rom_sha256",
}
FULL_KEYS = {
    "schema_version", "head_sha", *COUNTERS, "seconds", "details",
    "skip_records", "expected_failure_tests", "unexpected_success_tests",
    "stage62_rom_unchanged", "stage62_rom_sha256",
}
IDENTITY = re.compile(
    r"^tests(?:\.[A-Za-z_][A-Za-z0-9_]*){2,}$"
)
SAFE_IDENTITY_SENTINELS = {
    "unittest.class_fixture",
    "unittest.redacted_identity",
}
EXCEPTION = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_LABELS = {
    "T05 fixed inputs", "T06 AI stage", "T06 battle-core",
    "runtime-trigger", "生成物", "Task06 private ChangeKit",
}
MAX_RECORDS = 5000
MAX_COMMENT_BYTES = 58 * 1024


class ResultSummaryError(ValueError):
    pass


def _counter(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if type(value) is not int or value < 0:
        raise ResultSummaryError(f"invalid counter: {key}")
    return value


def _identity(value: Any) -> str:
    if (not isinstance(value, str) or len(value) > 512
            or (not IDENTITY.fullmatch(value)
                and value not in SAFE_IDENTITY_SENTINELS)):
        raise ResultSummaryError("test identity rejected")
    return value


def _frames(value: Any) -> tuple[tuple[str, int], ...]:
    if not isinstance(value, list) or len(value) > 30:
        raise ResultSummaryError("source frames rejected")
    rows: list[tuple[str, int]] = []
    for frame in value:
        if not isinstance(frame, dict) or set(frame) != {"path", "line"}:
            raise ResultSummaryError("source frame schema rejected")
        raw_path, line = frame["path"], frame["line"]
        if (not isinstance(raw_path, str) or len(raw_path) > 300
                or type(line) is not int or line <= 0):
            raise ResultSummaryError("source frame value rejected")
        path = PurePosixPath(raw_path)
        if (path.is_absolute() or ".." in path.parts or "\\" in raw_path
                or path.suffix != ".py" or not path.parts
                or path.parts[0] not in {"scripts", "tests", "tools"}):
            raise ResultSummaryError("source frame path rejected")
        rows.append((path.as_posix(), line))
    return tuple(rows)


def validate_result(
    data: Any, *, kind: str, expected_sha: str,
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ResultSummaryError("result must be an object")
    full = kind in {"full-unit", "all"}
    expected_keys = FULL_KEYS if full else FOCUSED_KEYS
    if set(data) != expected_keys:
        raise ResultSummaryError("result schema rejected")
    if not SHA40.fullmatch(expected_sha) or data["head_sha"] != expected_sha:
        raise ResultSummaryError("exact HEAD mismatch")
    counts = {key: _counter(data, key) for key in COUNTERS}
    if counts["tests"] <= 0:
        raise ResultSummaryError("empty test result rejected")
    if (not isinstance(data["stage62_rom_unchanged"], bool)
            or not isinstance(data["stage62_rom_sha256"], str)
            or not SHA256.fullmatch(data["stage62_rom_sha256"])):
        raise ResultSummaryError("ROM integrity record rejected")

    raw_details = data["details"]
    if not isinstance(raw_details, list) or len(raw_details) > MAX_RECORDS:
        raise ResultSummaryError("failure records rejected")
    details = []
    outcomes = Counter()
    for row in raw_details:
        if (not isinstance(row, dict)
                or set(row) != {"outcome", "test", "exception_type", "frames"}
                or row["outcome"] not in {"FAIL", "ERROR"}):
            raise ResultSummaryError("failure record schema rejected")
        test = _identity(row["test"])
        exception = row["exception_type"]
        if (not isinstance(exception, str) or len(exception) > 128
                or not EXCEPTION.fullmatch(exception)):
            raise ResultSummaryError("exception identity rejected")
        frames = _frames(row["frames"])
        details.append((row["outcome"], test, exception, frames))
        outcomes[row["outcome"]] += 1
    if (outcomes["FAIL"], outcomes["ERROR"]) != (
        counts["failures"], counts["errors"],
    ):
        raise ResultSummaryError("failure counters disagree")

    raw_skips = data["skip_records"]
    if not isinstance(raw_skips, list) or len(raw_skips) > MAX_RECORDS:
        raise ResultSummaryError("skip records rejected")
    skips = []
    for row in raw_skips:
        expected = {"test", "reason_sha256", "reason_labels"} if full else {
            "test", "reason_sha256",
        }
        if not isinstance(row, dict) or set(row) != expected:
            raise ResultSummaryError("skip record schema rejected")
        test = _identity(row["test"])
        digest = row["reason_sha256"]
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ResultSummaryError("skip reason identity rejected")
        labels: tuple[str, ...] = ()
        if full:
            raw_labels = row["reason_labels"]
            if (not isinstance(raw_labels, list)
                    or any(label not in SAFE_LABELS for label in raw_labels)):
                raise ResultSummaryError("skip reason label rejected")
            labels = tuple(raw_labels)
        skips.append((test, labels, digest))
    if len(skips) != counts["skipped"]:
        raise ResultSummaryError("skip counter disagrees")

    expected_tests: tuple[str, ...] = ()
    unexpected_tests: tuple[str, ...] = ()
    seconds: float | int | None = None
    if full:
        if data["schema_version"] != 1:
            raise ResultSummaryError("full-unit schema version rejected")
        seconds = data["seconds"]
        if type(seconds) not in {int, float} or not 0 <= seconds < 86400:
            raise ResultSummaryError("duration rejected")
        expected_tests = tuple(
            _identity(value) for value in data["expected_failure_tests"]
        )
        unexpected_tests = tuple(
            _identity(value) for value in data["unexpected_success_tests"]
        )
        if (len(expected_tests), len(unexpected_tests)) != (
            counts["expected_failures"], counts["unexpected_successes"],
        ):
            raise ResultSummaryError("expected result counters disagree")
    elif counts["expected_failures"] or counts["unexpected_successes"]:
        raise ResultSummaryError("focused expected result details are unavailable")

    return {
        "counts": counts,
        "details": details,
        "skips": skips,
        "expected_tests": expected_tests,
        "unexpected_tests": unexpected_tests,
        "seconds": seconds,
        "stage62_rom_unchanged": data["stage62_rom_unchanged"],
        "stage62_rom_sha256": data["stage62_rom_sha256"],
    }


def render_summary(
    data: Any, *, kind: str, expected_sha: str,
) -> str:
    result = validate_result(data, kind=kind, expected_sha=expected_sha)
    counts = result["counts"]
    lines = [
        "<!-- vega-private-test-result -->",
        "### Vega private test: limited result",
        "",
        f"- suite: `{kind}`",
        f"- HEAD: `{expected_sha}`",
        "- counts: " + ", ".join(
            f"{key}=`{counts[key]}`" for key in COUNTERS
        ),
        f"- Stage62 ROM unchanged: `{str(result['stage62_rom_unchanged']).lower()}`",
        f"- Stage62 ROM SHA-256: `{result['stage62_rom_sha256']}`",
    ]
    if result["seconds"] is not None:
        lines.append(f"- seconds: `{result['seconds']}`")

    grouped = Counter(result["details"])
    if grouped:
        lines.extend(("", "#### Failure / error identities", ""))
        for (outcome, test, exception, frames), occurrences in sorted(grouped.items()):
            locations = ", ".join(f"{path}:{line}" for path, line in frames) or "-"
            lines.append(
                f"- `{outcome}` ×`{occurrences}` `{test}` "
                f"(`{exception}`; `{locations}`)"
            )
    if result["skips"]:
        lines.extend(("", "#### Skip identities", ""))
        for test, labels, digest in result["skips"]:
            label = ",".join(labels) if labels else "-"
            lines.append(
                f"- `{test}` (labels=`{label}`; reason_sha256=`{digest}`)"
            )
    for title, values in (
        ("Expected failures", result["expected_tests"]),
        ("Unexpected successes", result["unexpected_tests"]),
    ):
        if values:
            lines.extend(("", f"#### {title}", ""))
            lines.extend(f"- `{value}`" for value in values)
    lines.extend(("", "例外本文・subtest値・private入力・Actions生ログは含みません。", ""))
    rendered = "\n".join(lines)
    if len(rendered.encode("utf-8")) > MAX_COMMENT_BYTES:
        raise ResultSummaryError("limited result exceeds comment boundary")
    return rendered


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("focused-unit", "full-unit", "all"), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        rendered = render_summary(
            data, kind=args.kind, expected_sha=args.expected_sha,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    except (OSError, json.JSONDecodeError, ResultSummaryError) as exc:
        print(f"GitHub result summary: FAIL: {exc}")
        return 2
    print(f"GitHub result summary: PASS kind={args.kind} head={args.expected_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
