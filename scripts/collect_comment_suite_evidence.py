#!/usr/bin/env python3
"""同じexact PR HEADのcomment起動結果から、非秘密の実数だけを保存する。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import time
from scripts.audit_private_unit_log import decode_log, TIMESTAMP, ANSI

REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'chatgpt/fix-private-full-unit-20260905-r2'
SUITES = ('battle-cli-offline', 'stage62-check', 'stage62-mgba')
ROM_SHA = 'd97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f'


def result_comment(comment: dict, head: str) -> tuple[str, int] | None:
    if comment.get('user', {}).get('id') != 41898282 or comment.get('user', {}).get('login') != 'github-actions[bot]':
        return None
    body = comment.get('body', '')
    pattern = (r'ChatGPT comment command: \*\*(?:SUCCESS|FAILURE)\*\*\n\n'
               r'- command: `private suite (battle-cli-offline|stage62-check|stage62-mgba)`\n'
               r'- ref: `' + re.escape(BRANCH) + r'`\n- SHA: `' + re.escape(head) + r'`\n'
               r'- run: https://github\.com/' + re.escape(REPO) + r'/actions/runs/([0-9]+)')
    match = re.fullmatch(pattern, body)
    return (match[1], int(match[2])) if match else None


def summarize_log(suite: str, raw: bytes) -> dict:
    lines = [TIMESTAMP.sub('', value).replace('##[error]', '').strip()
             for value in ANSI.sub('', decode_log(raw)).splitlines()]
    text = '\n'.join(lines)
    if suite == 'battle-cli-offline':
        counts = re.findall(r'^Ran (\d+) tests in ([0-9.]+)s$', text, re.M)
        versions = re.findall(r'^vega-codex-battle ([0-9]+\.[0-9]+\.[0-9]+)$', text, re.M)
        if len(counts) != 1 or len(versions) != 1 or not re.search(r'^OK$', text, re.M):
            raise ValueError('CLI complete unittest/version summary missing')
        return {'tests': int(counts[0][0]), 'seconds': counts[0][1], 'failures': 0, 'errors': 0,
                'skipped': 0, 'version': versions[0], 'counts_match_contract': int(counts[0][0]) == 37}
    if suite not in {'stage62-check', 'stage62-mgba'}:
        raise ValueError('unknown evidence suite')
    records = []
    for line in lines:
        if not line.startswith('{') or not line.endswith('}'):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get('stage') == 62 and value.get('status') == 'PASS':
            records.append(value)
    if len(records) != 1 or records[0].get('rom_sha256') != ROM_SHA:
        raise ValueError('Stage62 exact ROM result is missing or ambiguous')
    value = records[0]
    result = {'status': 'PASS', 'rom_sha256': ROM_SHA}
    if suite == 'stage62-mgba':
        result.update({'fixture_count': value.get('fixture_count'),
                       'process_runs_per_fixture': value.get('process_runs_per_fixture')})
        result['counts_match_contract'] = result['fixture_count'] == 6 and result['process_runs_per_fixture'] == 2
    else:
        result['counts_match_contract'] = value.get('command') == 'check'
    return result


def main() -> int:
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    pull = event['pull_request']
    if (not event['repository']['private'] or event['repository']['full_name'] != REPO
        or event['sender']['login'] != event['repository']['owner']['login']
        or pull['number'] != 3 or pull['head']['sha'] != head
        or pull['head']['ref'] != BRANCH or pull['head']['repo']['full_name'] != REPO):
        raise ValueError('evidence collector authorization mismatch')
    def api(endpoint):
        result = subprocess.run(['gh', 'api', '--allow-escape-sequences', f'repos/{REPO}/{endpoint}'],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=120)
        if result.returncode:
            raise ValueError('evidence API request failed')
        return result.stdout
    deadline, observed = time.monotonic() + 5400, {}
    while len(observed) < len(SUITES) and time.monotonic() < deadline:
        comments = json.loads(api('issues/3/comments?per_page=100'))
        for comment in comments:
            matched = result_comment(comment, head)
            if not matched or matched[0] in observed:
                continue
            suite, run_id = matched
            run = json.loads(api(f'actions/runs/{run_id}'))
            if run.get('status') != 'completed':
                continue
            if run.get('event') != 'issue_comment' or run.get('path') != '.github/workflows/chatgpt-comment-control.yml':
                raise ValueError('source workflow identity mismatch')
            jobs = json.loads(api(f'actions/runs/{run_id}/jobs?per_page=100'))['jobs']
            private_jobs = [job for job in jobs if job['name'] == 'private_test']
            if len(private_jobs) != 1:
                raise ValueError('private job identity missing')
            job = private_jobs[0]
            result = summarize_log(suite, api(f"actions/jobs/{job['id']}/logs"))
            steps = {step['name']: step.get('conclusion') for step in job.get('steps', [])}
            result.update({'run_id': run_id, 'job_id': job['id'], 'run_conclusion': run.get('conclusion'),
                           'job_conclusion': job.get('conclusion'),
                           'private_release_download': steps.get('Private Release資材を取得'),
                           'private_hash_restore': steps.get('Private環境をhash検証して復元'),
                           'suite_execution': steps.get('固定suiteを実行'), 'auto_reply_comment_id': comment['id']})
            observed[suite] = result
        if len(observed) < len(SUITES):
            time.sleep(10)
    report = {'schema_version': 1, 'head_sha': head, 'branch': BRANCH, 'suites': observed,
              'complete': set(observed) == set(SUITES)}
    output = Path('build/private-comment-evidence/result.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    return 0 if report['complete'] and all(row['counts_match_contract'] and row['run_conclusion'] == 'success'
             and row['job_conclusion'] == 'success' and row['private_hash_restore'] == 'success'
             and row['private_release_download'] == 'success' and row['suite_execution'] == 'success'
             for row in observed.values()) else 1


if __name__ == '__main__':
    try:
        status = main()
    except Exception:
        print('comment evidence collector failed; no raw log emitted')
        status = 2
    raise SystemExit(status)
