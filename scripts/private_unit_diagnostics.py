#!/usr/bin/env python3
"""Private unit修復の調査専用。ROM/saveを出力せず、実結果を記録する。"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.github_private_environment import SECRET_PATTERNS
OUT = ROOT / 'build/private-unit-diagnostics'
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redact(text: str) -> str:
    raw = text.encode('utf-8', errors='replace')
    for pattern in SECRET_PATTERNS.values():
        raw = pattern.sub(b'<secret-redacted>', raw)
    text = raw.decode('utf-8', errors='replace')
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '<address-redacted>', text)
    text = re.sub(r'(?im)^.*(?:password|credential|private.key|ipad.host|hostname).*$', '<sensitive-line-redacted>', text)
    text = re.sub(r'\b[0-9a-fA-F]{128,}\b', '<binary-hex-redacted>', text)
    return re.sub(r"b(['\"])(?:\\.|[^\n])*?\1", '<byte-literal-redacted>', text)


def safe(value, key: str = ''):
    if any(part in key.lower() for part in ('password', 'credential', 'private_key', 'device', 'ipad', 'hostname', 'token')):
        return '<sensitive-field-redacted>'
    if isinstance(value, dict):
        return {str(k): safe(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [safe(v, key) for v in value]
    if isinstance(value, str):
        if 'hex' in key.lower() or key.lower() in {'raw', 'payload', 'data_bytes', 'rom_bytes', 'save_bytes'}:
            return '<binary-field-redacted>'
        return redact(value)
    return value


def write(name: str, value) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(safe(value), ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def git(*args: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(['git', *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return result.stdout.rstrip() if result.returncode == 0 else 'git-command-failed:' + str(result.returncode)


def baseline() -> None:
    if os.environ.get('GITHUB_REPOSITORY') != REPO:
        raise SystemExit('repository mismatch')
    # gh handles authenticated GitHub redirects; never print the token or raw log.
    raw = subprocess.run(['gh', 'api', '--allow-escape-sequences', 'repos/' + REPO + '/actions/jobs/101309429531/logs'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90, check=True).stdout
    text = raw.decode('utf-8', errors='replace')
    lines = [re.sub(r'^\d{4}-\d\d-\d\dT[^ ]+ ', '', line) for line in text.splitlines()]
    outcomes, skipped = [], []
    for line in lines:
        match = re.match(r'^(ERROR|FAIL): (.+)$', line)
        if match:
            outcomes.append({'outcome': match[1], 'test': match[2]})
        match = re.match(r'^(.+) \.\.\. skipped (.+)$', line)
        if match:
            skipped.append({'test': match[1], 'reason': match[2]})
    final = re.findall(r'Ran (\d+) tests in ([\d.]+)s', text)[-1]
    summary = re.findall(r'FAILED \(failures=(\d+), errors=(\d+), skipped=(\d+)\)', text)[-1]
    if (final[0], *summary) != ('1594', '17', '41', '29') or len(outcomes) != 58 or text.lower().count('capstone') != 0:
        raise SystemExit('baseline evidence differs')
    write('baseline.json', {'run_id': 33967241290, 'job_id': 101309429531,
        'raw_log_sha256': sha(raw), 'tests': int(final[0]), 'seconds': float(final[1]),
        'failures': int(summary[0]), 'errors': int(summary[1]), 'skipped': int(summary[2]),
        'capstone_mentions': 0, 'outcomes': outcomes, 'skip_records': skipped})
    print('baseline verified: tests=1594 failures=17 errors=41 skipped=29 capstone=0')


def snapshot() -> None:
    metadata = {}
    prefixes = ('06_', '07_', '09_', '16_', '25_', '26_', '35_', '37_', '38_', '39_', '40_', '41_', '42_', '58_', '60_', '61_', '62_')
    for path in sorted((ROOT / 'build/stages').glob('*.json')):
        if not path.name.startswith(prefixes) or path.stat().st_size > 16 * 1024 * 1024:
            continue
        raw = path.read_bytes()
        metadata[str(path.relative_to(ROOT))] = {'sha256': sha(raw), 'value': json.loads(raw)}
    write('stage-metadata.json', metadata)
    vendor = ROOT / 'vendor/upstream/CFRU-JP'
    status = git('status', '--porcelain=v1', '--untracked-files=no', cwd=vendor)
    dirty = []
    for line in status.splitlines():
        relative = line[3:]
        path = vendor / relative
        if path.is_file() and not path.is_symlink():
            old = subprocess.run(['git', 'show', 'HEAD:' + relative], cwd=vendor, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            dirty.append({'path': relative, 'status': line[:2], 'mode': oct(path.stat().st_mode & 0o777),
                'current_sha256': sha(path.read_bytes()), 'committed_sha256': sha(old.stdout) if old.returncode == 0 else None})
    write('source-state.json', {'head': git('rev-parse', 'HEAD'), 'shallow': git('rev-parse', '--is-shallow-repository'),
        'vendor_head': git('rev-parse', 'HEAD', cwd=vendor), 'vendor_status': status, 'vendor_drift': dirty})
    pins = []
    def inspect(value, source):
        if isinstance(value, dict):
            relative = value.get('path') or value.get('rom') or value.get('source')
            expected = value.get('sha256')
            if isinstance(relative, str) and isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected):
                p = Path(relative)
                if not p.is_absolute() and '..' not in p.parts:
                    path = ROOT / p
                    actual = sha(path.read_bytes()) if path.is_file() else None
                    if actual != expected:
                        pins.append({'config': source, 'path': relative, 'expected': expected, 'actual': actual})
            for child in value.values():
                inspect(child, source)
        elif isinstance(value, list):
            for child in value:
                inspect(child, source)
    for path in sorted((ROOT / 'config').glob('*.json')):
        inspect(json.loads(path.read_text()), str(path.relative_to(ROOT)))
    write('pin-drift.json', pins)
    located = []
    for start in (ROOT / 'userfile', ROOT / '.local/github-private-environment/PRIVATE_INPUTS'):
        if start.is_dir():
            for path in start.rglob('nature_ids.csv'):
                located.append(str(path.relative_to(ROOT)))
    write('fixture-locations.json', {'authoring_registries': located,
        'project_config_exists': (ROOT / 'config/project.toml').is_file(),
        'stage60_save_exists': (ROOT / '.local/60_wild_species_root_repair.srm').is_file()})
    toolchain = {}
    manifest = json.loads((ROOT / 'infra/toolchain_manifest.json').read_text())
    for key, row in manifest['tools'].items():
        path = Path(row['path'])
        if path.is_file():
            owner = subprocess.run(['/usr/bin/dpkg-query', '-S', str(path.resolve())], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            package = owner.stdout.partition(': ')[0]
            version = subprocess.run(['/usr/bin/dpkg-query', '-W', '-f=${Package} ${Version} ${Architecture}', package], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            toolchain[key] = {'path': str(path), 'resolved': str(path.resolve()), 'sha256': sha(path.read_bytes()),
                'reference_sha256': row.get('sha256'), 'package': version.stdout.strip(), 'owner_status': owner.returncode}
    probe = subprocess.run(['/usr/bin/python3', '-I', '-c', 'import sys,sysconfig,platform,json; print(json.dumps({"version":sys.version,"soabi":sysconfig.get_config_var("SOABI"),"platform":platform.machine(),"implementation":sys.implementation.name}))'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    write('host-toolchain.json', {'tools': toolchain, 'python_abi': json.loads(probe.stdout)})
    print('non-secret metadata snapshot written')


def worker(name: str) -> int:
    if not re.fullmatch(r'tests\.test_[A-Za-z0-9_.]+', name):
        raise SystemExit('invalid focused test name')
    suite = unittest.defaultTestLoader.loadTestsFromName(name)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=2).run(suite)
    write('worker-result.json', {'name': name, 'tests': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors),
        'skipped': [{'test': str(test), 'reason': str(reason)} for test, reason in result.skipped],
        'details': [{'test': str(test), 'traceback': redact(trace)[-10000:]} for test, trace in result.failures + result.errors]})
    return 0 if result.wasSuccessful() else 1


def focus() -> int:
    plan = json.loads((ROOT / 'config/private_unit_repair_plan.json').read_text())
    results, failed = [], False
    for name in plan['focus']:
        target = OUT / 'worker-result.json'
        target.unlink(missing_ok=True)
        try:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), 'worker', name],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1800)
            row = json.loads(target.read_text()) if target.is_file() else {'name': name, 'worker_failed': True}
            row['returncode'] = result.returncode
            row['process_output'] = redact((result.stdout + result.stderr).decode('utf-8', errors='replace'))[-16000:]
            failed |= result.returncode != 0
        except subprocess.TimeoutExpired:
            row, failed = {'name': name, 'timeout': True}, True
        results.append(row)
        write('focused-results.json', {'head': git('rev-parse', 'HEAD'), 'results': results, 'all_passed': not failed})
        print(json.dumps({k: v for k, v in row.items() if k not in {'details', 'process_output'}}, ensure_ascii=False), flush=True)
    return int(failed)


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'baseline':
        baseline()
    elif command == 'snapshot':
        snapshot()
    elif command == 'worker':
        raise SystemExit(worker(sys.argv[2]))
    elif command == 'focus':
        raise SystemExit(focus())
    else:
        raise SystemExit('unknown diagnostic command')
