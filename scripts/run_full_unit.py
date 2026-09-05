#!/usr/bin/env python3
"""全unittestを通常discoveryで実行し、非秘密の結果だけを出力する。"""
from __future__ import annotations
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_private_unit_focus import Result
from scripts.github_private_environment import SECRET_PATTERNS


def safe_id(test) -> str:
    value = getattr(test, 'test_case', test).id()
    fixture = re.fullmatch(r'(setUpClass|tearDownClass|setUpModule|tearDownModule) \(([A-Za-z_][A-Za-z_0-9.]*)\)', value)
    if fixture:
        value = fixture[2] + '.' + fixture[1]
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)+', value):
        return 'unittest.redacted_identity'
    if any(pattern.search(value.encode()) for pattern in SECRET_PATTERNS.values()):
        return 'unittest.redacted_identity'
    return value


class PrivateResult(Result):
    def addSkip(self, test, reason):
        self.skipped.append((test, 'redacted'))
        labels = [key for key in ('T05 fixed inputs', 'T06 AI stage', 'T06 battle-core',
                                  'runtime-trigger', '生成物', 'Task06 private ChangeKit') if key in reason]
        self.skip_details.append({'test': safe_id(test), 'reason_labels': labels,
                                  'reason_sha256': hashlib.sha256(reason.encode()).hexdigest()})

    def addExpectedFailure(self, test, err):
        self.expectedFailures.append((test, 'redacted'))

    def report(self) -> dict:
        return {'tests': self.testsRun, 'failures': len(self.failures), 'errors': len(self.errors),
                'skipped': len(self.skipped), 'expected_failures': len(self.expectedFailures),
                'unexpected_successes': len(self.unexpectedSuccesses), 'details': self.details,
                'skip_records': self.skip_details,
                'expected_failure_tests': [safe_id(test) for test, _ in self.expectedFailures],
                'unexpected_success_tests': [safe_id(test) for test in self.unexpectedSuccesses]}


@contextlib.contextmanager
def private_output():
    """Python/native/subprocess出力を同時に抑制。テストの戻り値には触れない。"""
    sys.stdout.flush()
    sys.stderr.flush()
    saved = [os.dup(1), os.dup(2)]
    with open(os.devnull, 'w', encoding='utf-8') as sink:
        try:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                yield
        finally:
            sink.flush()
            for target, descriptor in zip((1, 2), saved):
                os.dup2(descriptor, target)
                os.close(descriptor)


def run_suite(suite: unittest.TestSuite, tracked: set[str]) -> PrivateResult:
    result = PrivateResult(tracked)
    suite.run(result)
    return result


def main() -> int:
    os.chdir(ROOT)
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z', '--', '*.py']).decode().split('\0'))
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    rom = ROOT / 'build/stages/62_npc_placement_integrity_repair.gba'
    def rom_digest():
        if not rom.exists():
            return None
        with rom.open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    before = rom_digest()
    started = time.monotonic()
    with private_output():
        # python -m unittest discover -s tests の標準pattern/load_testsと同一。
        suite = unittest.defaultTestLoader.discover('tests')
        result = run_suite(suite, tracked)
    after = rom_digest()
    report = result.report()
    report.update({'schema_version': 1, 'head_sha': head, 'seconds': round(time.monotonic() - started, 3),
                   'stage62_rom_unchanged': before == after, 'stage62_rom_sha256': after})
    path = ROOT / 'build/github-private/full-unit-result.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print('VEGA_FULL_UNIT_RESULT_JSON=' + json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(',', ':')))
    print(f"Ran {result.testsRun} tests in {report['seconds']:.3f}s")
    passed = result.wasSuccessful() and before == after
    print(('OK' if passed else 'FAILED') + f" (failures={len(result.failures)}, errors={len(result.errors)}, skipped={len(result.skipped)}, expected failures={len(result.expectedFailures)}, unexpected successes={len(result.unexpectedSuccesses)})")
    return 0 if passed else 1


if __name__ == '__main__':
    try:
        code = main()
    except Exception:
        print('full-unit runner infrastructure failed before a complete safe report', file=sys.stderr)
        code = 2
    raise SystemExit(code)
