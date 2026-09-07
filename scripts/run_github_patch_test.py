#!/usr/bin/env python3
"""Run one /vega-patch unittest while emitting only a fixed safe JSON record."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import traceback
from typing import Any, Iterator, Sequence
import unittest


TEST_ID = re.compile(
    r"^tests(?:\.[A-Za-z_][A-Za-z0-9_]*){2,}$"
)
SHA40 = re.compile(r"^[0-9a-f]{40}$")
EXCEPTION = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MAX_FRAMES = 30


class PatchTestError(RuntimeError):
    """The requested test cannot be represented by the safe result schema."""


def _git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args], cwd=root, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if process.returncode:
        raise PatchTestError("git identity unavailable")
    return process.stdout.strip()


@contextmanager
def _silence_process_output() -> Iterator[None]:
    """Discard Python, native, and child-process output during test loading/run."""

    saved_stdout = os.dup(1)
    saved_stderr = os.dup(2)
    try:
        with open(os.devnull, "wb") as sink:
            sys.stdout.flush()
            sys.stderr.flush()
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(saved_stdout, 1)
        os.dup2(saved_stderr, 2)
        os.close(saved_stdout)
        os.close(saved_stderr)


class _SafeResult(unittest.TestResult):
    def __init__(self, root: Path, tracked: set[str], requested_test_id: str):
        super().__init__()
        self.root = root
        self.tracked = tracked
        self.requested_test_id = requested_test_id
        self.failure_count = 0
        self.error_count = 0
        self.skip_count = 0
        self.success_count = 0
        self.records: list[dict[str, Any]] = []
        self.expected_result_seen = False

    def _frames(self, tb: Any) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        for frame, line in traceback.walk_tb(tb):
            try:
                path = Path(frame.f_code.co_filename).resolve()
                relative = path.relative_to(self.root).as_posix()
            except (OSError, ValueError):
                continue
            key = (relative, line)
            if relative not in self.tracked or key in seen:
                continue
            seen.add(key)
            rows.append({"path": relative, "line": line})
            if len(rows) >= MAX_FRAMES:
                break
        return rows

    def _record(self, outcome: str, err: tuple[type, BaseException, Any]) -> None:
        name = getattr(err[0], "__name__", "Exception")
        if not isinstance(name, str) or not EXCEPTION.fullmatch(name):
            name = "Exception"
        self.records.append({
            "outcome": outcome,
            "exception_class": name,
            "frames": self._frames(err[2]),
        })

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        self.success_count += 1

    def addFailure(
        self, test: unittest.case.TestCase,
        err: tuple[type, BaseException, Any],
    ) -> None:
        self.failure_count += 1
        self._record("FAIL", err)

    def addError(
        self, test: unittest.case.TestCase,
        err: tuple[type, BaseException, Any],
    ) -> None:
        self.error_count += 1
        self._record("ERROR", err)

    def addSkip(self, test: unittest.case.TestCase, reason: str) -> None:
        self.skip_count += 1

    def addSubTest(
        self, test: unittest.case.TestCase, subtest: unittest.case._SubTest,
        err: tuple[type, BaseException, Any] | None,
    ) -> None:
        if err is None:
            return
        if issubclass(err[0], test.failureException):
            self.addFailure(test, err)
        else:
            self.addError(test, err)

    def addExpectedFailure(
        self, test: unittest.case.TestCase,
        err: tuple[type, BaseException, Any],
    ) -> None:
        self.expected_result_seen = True

    def addUnexpectedSuccess(self, test: unittest.case.TestCase) -> None:
        self.expected_result_seen = True


def _only_test_id(suite: unittest.TestSuite) -> str:
    tests: list[unittest.case.TestCase] = []

    def collect(value: unittest.TestSuite | unittest.case.TestCase) -> None:
        if isinstance(value, unittest.TestSuite):
            for child in value:
                collect(child)
        else:
            tests.append(value)

    collect(suite)
    if len(tests) != 1:
        raise PatchTestError("single test required")
    identity = tests[0].id()
    if not isinstance(identity, str):
        raise PatchTestError("test identity unavailable")
    return identity


def run_single_test(root: Path, test_id: str, expected_sha: str) -> tuple[dict, int]:
    root = root.resolve()
    if not TEST_ID.fullmatch(test_id):
        raise PatchTestError("test identity rejected")
    if not SHA40.fullmatch(expected_sha) \
            or _git(root, "rev-parse", "HEAD") != expected_sha:
        raise PatchTestError("exact HEAD mismatch")
    tracked = set(filter(None, _git(
        root, "ls-files", "-z", "--", "*.py",
    ).split("\0")))
    if not tracked:
        raise PatchTestError("tracked Python source unavailable")

    previous_cwd = Path.cwd()
    previous_path = list(sys.path)
    try:
        os.chdir(root)
        sys.path.insert(0, str(root))
        with _silence_process_output():
            suite = unittest.defaultTestLoader.loadTestsFromName(test_id)
            if _only_test_id(suite) != test_id:
                raise PatchTestError("loaded test identity mismatch")
            result = _SafeResult(root, tracked, test_id)
            suite.run(result)
    finally:
        sys.path[:] = previous_path
        os.chdir(previous_cwd)

    if result.expected_result_seen:
        raise PatchTestError("expected-result modes are unsupported")
    active = sum(value > 0 for value in (
        result.failure_count, result.error_count, result.skip_count,
    ))
    if active > 1:
        raise PatchTestError("ambiguous test outcome")
    if result.failure_count:
        outcome = "FAIL"
    elif result.error_count:
        outcome = "ERROR"
    elif result.skip_count:
        outcome = "SKIP"
    elif result.testsRun == 1 and result.success_count == 1:
        outcome = "PASS"
    else:
        raise PatchTestError("incomplete test outcome")

    records = [row for row in result.records if row["outcome"] == outcome]
    exception_class: str | None = None
    frames: list[dict[str, Any]] = []
    if outcome in {"FAIL", "ERROR"}:
        if not records:
            raise PatchTestError("missing failure identity")
        exception_classes = {row["exception_class"] for row in records}
        if len(exception_classes) != 1:
            raise PatchTestError("ambiguous exception identity")
        exception_class = next(iter(exception_classes))
        seen_frames: set[tuple[str, int]] = set()
        for row in records:
            for frame in row["frames"]:
                key = (frame["path"], frame["line"])
                if key not in seen_frames and len(frames) < MAX_FRAMES:
                    seen_frames.add(key)
                    frames.append(frame)

    data = {
        "schema_version": 1,
        "head_sha": expected_sha,
        "test_id": test_id,
        "counts": {
            "tests": result.testsRun,
            "failures": result.failure_count,
            "errors": result.error_count,
            "skips": result.skip_count,
        },
        "result": {
            "test_id": test_id,
            "outcome": outcome,
            "exception_class": exception_class,
            "frames": frames,
        },
    }
    return data, 0 if outcome == "PASS" else 1


def _result_path(root: Path, output: Path) -> Path:
    root = root.resolve()
    output = output if output.is_absolute() else Path.cwd() / output
    try:
        output.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise PatchTestError("result output escaped repository") from exc
    if output.is_symlink():
        raise PatchTestError("result output is a symlink")
    return output


def _write_result(root: Path, output: Path, data: dict[str, Any]) -> None:
    """Atomically replace a result only inside the checked-out repository."""

    output = _result_path(root, output)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        data, ensure_ascii=True, sort_keys=True, indent=2,
    ) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent,
            prefix=".patch-test-result-", suffix=".tmp", delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary_name = temporary.name
        os.replace(temporary_name, output)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        output = _result_path(args.root, args.output)
        output.unlink(missing_ok=True)
        data, status = run_single_test(
            args.root, args.test_id, args.expected_sha,
        )
        _write_result(args.root, output, data)
    except BaseException:
        print("GitHub patch test: FAIL")
        return 2
    print("GitHub patch test: SAFE_RESULT_WRITTEN")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
