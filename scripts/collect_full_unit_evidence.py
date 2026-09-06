#!/usr/bin/env python3
"""PRコメントで起動した全unitの生ログから、許可した実測結果だけを取り出す。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import time
from scripts.audit_private_unit_log import decode_log, TIMESTAMP, ANSI
from scripts.collect_comment_suite_evidence import REPO, BRANCH
from scripts.github_private_environment import SECRET_PATTERNS

PREFIX = 'VEGA_FULL_UNIT_RESULT_JSON='
IDENTITY = re.compile(r'[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)+')
SHA = re.compile(r'[0-9a-f]{64}')
COUNTS = ('tests', 'failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes')
LABELS = {'T05 fixed inputs', 'T06 AI stage', 'T06 battle-core', 'runtime-trigger', '生成物', 'Task06 private ChangeKit'}


def _identity(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        raise ValueError('test identity rejected')
    return value


def extract_report(raw: bytes, head: str) -> dict:
    lines = [TIMESTAMP.sub('', line).replace('##[error]', '').strip()
             for line in ANSI.sub('', decode_log(raw)).splitlines()]
    rows = [line[len(PREFIX):] for line in lines if line.startswith(PREFIX)]
    if len(rows) != 1:
        raise ValueError('complete full-unit result is missing or ambiguous')
    data = json.loads(rows[0])
    keys = set(COUNTS) | {'schema_version', 'head_sha', 'seconds', 'stage62_rom_unchanged',
        'stage62_rom_sha256', 'details', 'skip_records', 'expected_failure_tests', 'unexpected_success_tests'}
    if set(data) != keys or data['schema_version'] != 1 or data['head_sha'] != head \
            or not re.fullmatch(r'[0-9a-f]{40}', head):
        raise ValueError('full-unit schema or exact HEAD mismatch')
    if any(type(data[key]) is not int or data[key] < 0 for key in COUNTS) or data['tests'] == 0:
        raise ValueError('invalid full-unit counts')
    if type(data['seconds']) not in {float, int} or not 0 <= data['seconds'] < 86400 \
            or type(data['stage62_rom_unchanged']) is not bool \
            or not isinstance(data['stage62_rom_sha256'], str) or not SHA.fullmatch(data['stage62_rom_sha256']):
        raise ValueError('invalid full-unit duration or ROM integrity record')
    observed = {'FAIL': 0, 'ERROR': 0}
    for item in data['details']:
        if set(item) != {'outcome', 'test', 'exception_type', 'frames'} or item['outcome'] not in observed:
            raise ValueError('unknown failure record')
        _identity(item['test'])
        if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', item['exception_type']):
            raise ValueError('exception identity rejected')
        observed[item['outcome']] += 1
        for frame in item['frames']:
            if set(frame) != {'path', 'line'} or type(frame['line']) is not int or frame['line'] <= 0:
                raise ValueError('invalid source frame')
            path = PurePosixPath(frame['path'])
            if path.is_absolute() or '..' in path.parts or '\\' in str(path) or path.suffix != '.py':
                raise ValueError('non-source traceback path rejected')
    if (observed['FAIL'], observed['ERROR']) != (data['failures'], data['errors']):
        raise ValueError('failure records do not match counters')
    for item in data['skip_records']:
        if set(item) != {'test', 'reason_labels', 'reason_sha256'}:
            raise ValueError('unknown skip record')
        _identity(item['test'])
        if not set(item['reason_labels']) <= LABELS or not SHA.fullmatch(item['reason_sha256']):
            raise ValueError('skip reason record rejected')
    for key in ('expected_failure_tests', 'unexpected_success_tests'):
        for value in data[key]:
            _identity(value)
    if (len(data['skip_records']), len(data['expected_failure_tests']), len(data['unexpected_success_tests'])) != (
            data['skipped'], data['expected_failures'], data['unexpected_successes']):
        raise ValueError('terminal result records do not match counters')
    encoded = json.dumps(data, ensure_ascii=False).encode()
    if any(pattern.search(encoded) for pattern in SECRET_PATTERNS.values()):
        raise ValueError('secret candidate rejected')
    summaries = [line for line in lines if re.fullmatch(r'Ran \d+ tests in [0-9.]+s', line)]
    if len(summaries) != 1 or not summaries[0].startswith(f"Ran {data['tests']} tests in "):
        raise ValueError('unittest text and machine counts disagree')
    return data


def result_comment(comment: dict, suite: str, head: str) -> int | None:
    if comment.get('user', {}).get('id') != 41898282 or comment.get('user', {}).get('login') != 'github-actions[bot]':
        return None
    pattern = (r'ChatGPT comment command: \*\*(?:SUCCESS|FAILURE)\*\*\n\n'
        r'- command: `private suite ' + re.escape(suite) + r'`\n- ref: `' + re.escape(BRANCH)
        + r'`\n- SHA: `' + re.escape(head) + r'`\n- run: https://github\.com/' + re.escape(REPO) + r'/actions/runs/([0-9]+)')
    match = re.fullmatch(pattern, comment.get('body', ''))
    return int(match[1]) if match else None


def main() -> int:
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    pull, repo = event['pull_request'], event['repository']
    checkout = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if (not repo['private'] or repo['full_name'] != REPO or event['sender']['login'] != repo['owner']['login']
            or pull['number'] != 3 or pull['head']['ref'] != BRANCH or pull['head']['repo']['full_name'] != REPO
            or pull['head']['sha'] != checkout):
        raise ValueError('collector authorization mismatch')
    requests = re.findall(r'<!-- collect-unit (full-unit|all) ([0-9a-f]{40}) -->', pull.get('body') or '')
    if len(requests) != 1:
        raise ValueError('one explicit unit evidence request required')
    suite, head = requests[0]
    def api(endpoint):
        proc = subprocess.run(['gh', 'api', '--allow-escape-sequences', f'repos/{REPO}/{endpoint}'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=120)
        if proc.returncode:
            raise ValueError('evidence API request failed')
        return proc.stdout
    # 過去の同PR commitも読めるが、別branchやmainのunit結果へ取り違えない。
    commits = json.loads(api('pulls/3/commits?per_page=100'))
    if head != checkout and head not in {row['sha'] for row in commits}:
        raise ValueError('requested HEAD is not part of this PR')
    deadline = time.monotonic() + 5400
    while time.monotonic() < deadline:
        comments = []
        for page in range(1, 11):
            rows = json.loads(api(f'issues/3/comments?per_page=100&page={page}'))
            comments.extend(rows)
            if len(rows) < 100:
                break
        matches = [(row, result_comment(row, suite, head)) for row in comments]
        matches = [(row, run) for row, run in matches if run is not None]
        if not matches:
            time.sleep(10)
            continue
        comment, run_id = max(matches, key=lambda item: item[0]['id'])
        run = json.loads(api(f'actions/runs/{run_id}'))
        if run['status'] != 'completed':
            time.sleep(10)
            continue
        if run['event'] != 'issue_comment' or run['path'] != '.github/workflows/chatgpt-comment-control.yml':
            raise ValueError('run is not the comment-controlled private suite')
        jobs = json.loads(api(f'actions/runs/{run_id}/jobs?per_page=100'))['jobs']
        private = [row for row in jobs if row['name'] == 'private_test']
        if len(private) != 1:
            raise ValueError('private job is missing or ambiguous')
        job = private[0]
        raw = api(f"actions/jobs/{job['id']}/logs")
        unit = extract_report(raw, head)
        steps = {row['name']: row.get('conclusion') for row in job['steps']}
        report = {'schema_version': 1, 'suite': suite, 'head_sha': head, 'collector_head_sha': checkout,
            'branch': BRANCH, 'run_id': run_id, 'job_id': job['id'], 'raw_log_sha256': hashlib.sha256(raw).hexdigest(),
            'run_conclusion': run['conclusion'], 'job_conclusion': job['conclusion'],
            'private_release_download': steps.get('Private Release資材を取得'),
            'private_hash_restore': steps.get('Private環境をhash検証して復元'),
            'auto_reply_comment_id': comment['id'], 'unit': unit}
        output = Path('build/private-full-unit-evidence/result.json')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        print(json.dumps({key: report[key] for key in ('suite', 'head_sha', 'run_id', 'job_id', 'run_conclusion')}))
        print(json.dumps({key: unit[key] for key in COUNTS}))
        return 0 if (run['conclusion'] == 'success' and job['conclusion'] == 'success'
            and unit['failures'] == unit['errors'] == unit['unexpected_successes'] == 0
            and unit['stage62_rom_unchanged']
            and report['private_release_download'] == report['private_hash_restore'] == 'success') else 1
    raise ValueError('requested unit result was not observed')


if __name__ == '__main__':
    try:
        status = main()
    except Exception:
        print('full-unit evidence collection failed; no raw private log emitted')
        status = 2
    raise SystemExit(status)
