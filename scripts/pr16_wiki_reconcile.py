#!/usr/bin/env python3
"""4回の完了Actions原本を照合して記録だけを確定する。Wiki/build/nativeの再実行なし。"""
from __future__ import annotations
import argparse
import datetime
import io
import json
import os
from pathlib import PurePosixPath
import re
import sys
import urllib.request
import zipfile
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, ROOT, STATE, digest, need, stable
from pr16_resume import DOC, render

REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
API = 'https://api.github.com/repos/' + REPO + '/'
TASK = 'USER-20260921-P08-CANDIDATE-WIKI'
RECEIPT = 'content/modernization/pr16_candidate_wiki_acceptance.json'
FOLLOW = 'content/modernization/pr16_candidate_wiki_followup.json'
REPORT = 'content/modernization/pr16_candidate_wiki_completed_runs_20260921.json'
RUNS = (
    (35561743057, '69100d45363f7c22ad6d6b87dbdfab9aa15d68c4', '12bf4d7dd277c82a1bd2d9642a4c893303a3e4b0', 26, 'EFFECT_ORIGIN'),
    (35562396044, 'a2307c7b7fafd6f50913d3effbe49cc500b18070', 'dbd3f10e67935511092f3d0a7d9fa761015403ae', 26, 'HIDDEN_PATCH'),
    (35563498591, '3969be6bfb4083ce4cb1e5dd48f0697a62665127', '3099c3123a40fda64f6610ca9052932253a508c9', 32, 'CREATION_MOVESET'),
    (35564248203, '6ea91ae2da54398fdc01bb3d0cf4f89427855ba4', '24cc366c71df6a7e982635a33f4374cf965e75e1', 26, 'LINK_GRAPH'),
)
ZERO_KEYS = ('new_native_runs', 'accepted_native_reruns', 'arm_builds', 'rom_changes')
PROOF_FILES = ('build-11.json', 'build-29.json', 'check.stdout.json', 'check.stderr.txt',
               'cli-check.json', 'followup-unit.txt', 'reflected-head.txt', 'acceptance.json')


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        need(newurl.startswith('https://'), '非HTTPS redirect禁止')
        result = super().redirect_request(req, fp, code, msg, headers, newurl)
        if result is not None:
            result.remove_header('Authorization')
        return result


def fetch(path: str, *, binary: bool = False):
    need(not path.startswith('/') and '://' not in path and '..' not in path.split('/'), 'API相対path不正')
    headers = {'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN']}
    request = urllib.request.Request(API + path, headers=headers)
    bound = 32_000_000 if binary else 3_000_000
    with urllib.request.build_opener(SafeRedirect()).open(request, timeout=45) as response:
        raw = response.read(bound + 1)
    need(len(raw) <= bound, '応答size超過')
    return raw if binary else json.loads(raw)


def validate_run(run: dict, jobs: dict, artifacts: dict, expected: tuple) -> dict:
    rid, head, _child, _tests, _scope = expected
    need(run['id'] == rid and run['head_sha'] == head and run['head_branch'] == BRANCH, 'run/HEAD/branch不一致')
    need(run['repository']['full_name'] == REPO and run['event'] == 'push'
         and run['path'] == '.github/workflows/pr16-candidate-wiki.yml', 'run repository/event/workflow不一致')
    need(run['status'] == 'completed' and run['conclusion'] == 'success', 'runは完了成功ではない')
    need(jobs['total_count'] == len(jobs['jobs']) == 1, 'job欠落/未処理ページ')
    job = jobs['jobs'][0]
    need(job['run_id'] == rid and job['head_sha'] == head and job['name'] == 'wiki'
         and job['status'] == 'completed' and job['conclusion'] == 'success', 'job結果不一致')
    steps = job['steps']
    need(bool(steps) and all(s['status'] == 'completed' and s['conclusion'] == 'success' for s in steps), '未成功stepあり')
    names = [s['name'] for s in steps]
    need(any('非force push' in n for n in names) and 'Run actions/upload-artifact@v4' in names, 'push/upload完了step欠落')
    need(artifacts['total_count'] == len(artifacts['artifacts']), 'artifact未処理ページ')
    matches = [a for a in artifacts['artifacts'] if a['name'] == 'pr16-candidate-wiki-cli']
    need(len(matches) == 1, '検証artifact欠落/重複')
    artifact = matches[0]; binding = artifact['workflow_run']
    need(binding['id'] == rid and binding['head_sha'] == head and binding['head_branch'] == BRANCH
         and artifact['expired'] is False and re.fullmatch(r'sha256:[0-9a-f]{64}', artifact['digest']), 'artifact binding/有効性不一致')
    return artifact


def proof_files(raw: bytes, sha256: str) -> dict[str, bytes]:
    need(digest(raw) == sha256, 'artifact SHA-256不一致')
    result = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)) <= 64, 'ZIP重複/件数超過')
        for name in names:
            path = PurePosixPath(name)
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in name, 'ZIP path不正')
        need(set(PROOF_FILES) <= set(names), '検証原本欠落')
        for name in PROOF_FILES:
            info = archive.getinfo(name)
            need(info.file_size <= 3_000_000 and info.external_attr >> 28 != 0xA, '原本size/symlink不正')
            data = archive.read(name); data.decode('utf-8'); need(b'\0' not in data, '原本NUL')
            result[name] = data
    return result


def validate_proof(files: dict[str, bytes], expected: tuple, candidate: dict) -> dict:
    rid, head, child, count, scope = expected
    build = json.loads(files['build-11.json']); check = json.loads(files['check.stdout.json'])
    report = json.loads(files['cli-check.json']); receipt = json.loads(files['acceptance.json'])
    need(build == json.loads(files['build-29.json']), '2seed生成原本不一致')
    need(build['status'] == check['status'] == 'PASS' and build['command'] == 'build' and check['command'] == 'check', 'CLI検証未成功')
    need(build['candidate'] == check['candidate'] == receipt['candidate'] == candidate, 'candidate結合不一致')
    for key in ('files', 'bytes', 'tree_sha256', 'internal_links', 'output', 'counts', 'record_counts'):
        need(build[key] == check[key] == receipt[key], '出力原本不一致: ' + key)
    need(files['check.stderr.txt'] == b'' and check['check_writes'] == 0, 'check副作用/stderrあり')
    need(report['status'] == 'PASS_WIKI_BUILD_CHECK' and report['two_process_builds_identical'] is True
         and report['actual_check_unchanged_bytes_and_mtimes'] is True and report['stage61_unchanged'] is True
         and report['active_baseline_changed'] is False, '受入境界の原本不一致')
    need(all(type(report[k]) is int and report[k] == 0 for k in ZERO_KEYS)
         and report['issue18_complete'] is False and receipt['issue18_complete'] is False, 'native/ROM/全体完了の不正昇格')
    log = files['followup-unit.txt'].decode()
    need(re.findall(r'^Ran (\d+) tests? in ', log, re.M) == [str(count)] and re.search(r'\nOK\s*$', log), '追加試験原本不一致')
    need(receipt['source_head'] == head and receipt['verification_run'] == rid and receipt['unit']['tests'] == count
         and all(receipt['unit'][k] == 0 for k in ('errors', 'failures', 'skips')), 'receipt run/test binding不一致')
    need(files['reflected-head.txt'].decode().strip() == child, 'push先commit不一致')
    return {'id': rid, 'head_sha': head, 'reflected_head': child, 'scope': scope, 'status': 'completed', 'conclusion': 'success',
            'tests': count, 'candidate': candidate, 'files': build['files'], 'bytes': build['bytes'],
            'tree_sha256': build['tree_sha256'], 'internal_links': build['internal_links'],
            'proof_bindings': {n: {'size': len(v), 'sha256': digest(v)} for n, v in sorted(files.items())},
            'verification': {k: report[k] for k in (*ZERO_KEYS, 'two_process_builds_identical',
                'actual_check_unchanged_bytes_and_mtimes', 'stage61_unchanged', 'active_baseline_changed', 'issue18_complete')}}


def validate_child(commit: dict, expected: tuple) -> None:
    need(commit['sha'] == expected[2] and [p['sha'] for p in commit['parents']] == [expected[1]]
         and commit['message'].startswith(TASK + ':'), '反映commitの親/タスク不一致')


def collect(candidate: dict) -> list[dict]:
    records = []
    for expected in RUNS:
        rid = expected[0]
        run = fetch(f'actions/runs/{rid}')
        jobs = fetch(f'actions/runs/{rid}/jobs?per_page=100')
        artifacts = fetch(f'actions/runs/{rid}/artifacts?per_page=100')
        artifact = validate_run(run, jobs, artifacts, expected)
        raw = fetch(f'actions/artifacts/{artifact["id"]}/zip', binary=True)
        files = proof_files(raw, artifact['digest'].removeprefix('sha256:'))
        result = validate_proof(files, expected, candidate)
        validate_child(fetch('git/commits/' + expected[2]), expected)
        result['job'] = {k: jobs['jobs'][0][k] for k in ('id', 'name', 'status', 'conclusion', 'completed_at')}
        result['artifact'] = {k: artifact[k] for k in ('id', 'name', 'size_in_bytes', 'digest', 'expired')}
        result['run_url'] = run['html_url']
        records.append(result)
    return records


def record() -> None:
    inputs = Inputs(); receipt = inputs.json(RECEIPT); state = inputs.json(STATE); follow = inputs.json(FOLLOW)
    need(receipt['verification_run'] == RUNS[-1][0] and receipt['source_head'] == RUNS[-1][1], '最新Wiki以外のreceipt')
    need(state['candidate_wiki']['candidate'] == receipt['candidate'], '引継ぎcandidate不一致')
    source = os.environ['GITHUB_SHA']
    current = fetch('git/commits/' + source)
    need([p['sha'] for p in current['parents']] == [RUNS[-1][2]], '記録sourceは最後のWiki commit直後ではない')
    unit_log = (ROOT/'.local/pr16-wiki-reconcile/unit.txt').read_text(encoding='utf-8')
    need(re.findall(r'^Ran (\d+) tests? in ', unit_log, re.M) == ['34'] and re.search(r'\nOK\s*$', unit_log), '記録差分34試験が未成功')
    records = collect(receipt['candidate']); latest = records[-1]
    for key in ('files', 'bytes', 'tree_sha256', 'internal_links'):
        need(receipt[key] == latest[key], '最新receiptと検証原本不一致')
    previous = receipt.get('verification_run_reconciled')
    need(previous is None or previous['id'] != latest['id'], 'このrunは照合済み。再実行しない')
    report = {'schema_version': 1, 'status': 'PASS_COMPLETED_WIKI_RUN_RECONCILIATION',
              'task': TASK, 'source_head_at_reconciliation': source,
              'record_execution_run': int(os.environ['GITHUB_RUN_ID']), 'record_execution_success_claimed_before_push': False,
              'candidate': receipt['candidate'], 'completed_runs': records,
              'new_scoped_tests_total': sum(r['tests'] for r in records), 'record_validation_tests': 34,
              'wiki_rebuilds_in_reconciliation': 0, **{k: 0 for k in ZERO_KEYS}, 'issue18_complete': False,
              'remaining_work_ja': receipt['remaining_work_ja']}
    need(report['new_scoped_tests_total'] == 110, '今回110試験の集計不一致')
    if previous is not None:
        history = receipt.setdefault('reconciled_run_history', [])
        if not any(r['id'] == previous['id'] for r in history): history.append(previous)
    history = receipt.setdefault('reconciled_run_history', [])
    for result in records[:-1]:
        if not any(r['id'] == result['id'] for r in history): history.append(result)
    receipt['verification_run_reconciled'] = latest
    receipt['verification_run_status_at_recording'] = 'completed: success（4回のGET・job全step・artifact SHA・検証原本・反映commit親を照合）'
    receipt['completion_reconciliation'] = {'path': REPORT, 'source_head': source, 'completed_runs': [r['id'] for r in records], 'new_scoped_tests_total': 110}
    follow['completed_wiki_runs'] = records
    follow['latest_checkpoint']['verification_run_status'] = 'completed_success'
    follow['latest_checkpoint']['reflected_head'] = latest['reflected_head']
    follow['completion_reconciliation'] = receipt['completion_reconciliation']
    state['candidate_wiki'].update(verification_run_status='completed_success', reflected_head=latest['reflected_head'],
        completion_reconciliation=receipt['completion_reconciliation'])
    state['bp']['current_stop'] = (f'候補Wiki {latest["files"]} files、effect/夢特性patch/初期技/Z入口graphの4差分を実装・110試験受入。'
        f'4回のActionsはpush/upload完了までGETと原本で照合済み。最新Wiki commit {latest["reflected_head"]} / run {latest["id"]}。'
        'Issue18全体は未完。残りのsource/caller未結合をcandidate_wiki.remaining_work_jaに固定。')
    state['next_action']['goal_ja'] = 'Issue18の残件だけを継続。4分野の既存generator/110試験は重複実装せず、残りのcaller・供給・handler結合を証拠に応じて進める。必要な変更影響がない受入済みnative/buildの反復なし。'
    state['bp']['next_step'] = state['next_action']['goal_ja']
    state['next_action']['stop_rule_ja'] = '今回の4差分はActions全step・artifact原本・同branch反映まで完了照合済み。残件はsource推定を実行受入に昇格しない。Issue18の全体完了・merge・release・active baseline切替は別判断。'
    state['next_action']['read_paths'] = [RECEIPT, REPORT, 'docs/wiki/p08-candidate-46487d98/RUNTIME_LIMITATIONS.md',
        'scripts/build_pr16_candidate_wiki.py', 'scripts/pr16_candidate_wiki_effect_origin.py',
        'scripts/pr16_candidate_wiki_hidden_patch.py', 'scripts/pr16_candidate_wiki_creation.py', 'scripts/pr16_candidate_wiki_link_graph.py']
    state['logs_synchronized'] = True
    for name, value in ((REPORT, report), (RECEIPT, receipt), (FOLLOW, follow)):
        (ROOT/name).write_bytes(stable(value))
    (ROOT/STATE).write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (ROOT/DOC).write_text(render(state), encoding='utf-8')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    for name in ('design/run_log.md', 'design/version_log.md'):
        with (ROOT/name).open('a', encoding='utf-8') as stream:
            stream.write(f'\n\n## {now} — 4差分Wikiの完了Actions照合\n- Task: {TASK} / 完了GETと原本の記録確定\n'
                '- Version: wiki-audit-20260921\n- Status: DONE（4差分の実装・検証・記録・反映。Issue18全体の完了ではない）\n'
                f'- Summary: {latest["files"]} files / {latest["bytes"]} bytes / {latest["internal_links"]}内部リンク。effect全1063技、patch全1671slot、生成技311経路/95野生行/4776profile、Z3入口32node/4BL。\n'
                '- Files changed: 完了照合script/差分試験/workflow、completed runs JSON、receipt/followup、固定引継ぎMD/JSON、両ログ。Wiki本文はこの記録段階では変更しない。\n'
                '- Verify: 4回のcompleted/success・全job/step・artifact digestと検証原本・反映commit親を照合。差分26+26+32+26=110試験、各2seed build一致・実check byte/mtime不変の保存結果を再利用。記録差分34試験・resume/task graph・最終index guard。\n'
                f'- Commit: 本記録を含むcommit。記録source HEAD={source}。最新Wiki反映={latest["reflected_head"]}。\n'
                '- Network: GitHub API run35561743057/35562396044/35563498591/35564248203とそのjob/artifact/commitのGETのみ。署名download URL/credentialは記録しない。\n'
                '- Boundary: この記録段階でWiki再build0・ROM変更0・ARM0・native0・受入native再実行0。Stage61/active baseline/原本/過去失敗記録は保持。named Z callee・通常野生/旧配布・夢特性初回供給/daycare・技511/全handler履歴は未完のまま。\n')
    print(json.dumps({'status': report['status'], 'completed_runs': len(records), 'accepted_scoped_tests': 110,
                      'files': latest['files'], 'wiki_rebuilds': 0, 'new_native_runs': 0}, sort_keys=True))


def guard() -> None:
    import pr16_wiki_checkpoint as checkpoint
    checkpoint.ALLOWED = {REPORT, RECEIPT, FOLLOW, STATE, DOC, 'design/run_log.md', 'design/version_log.md'}
    import subprocess
    names = set(filter(None, subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=ROOT).decode().split('\0')))
    need(names <= checkpoint.ALLOWED, '記録以外の最終index変更')
    checkpoint.guard()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('record', 'guard'))
    args = parser.parse_args()
    try:
        globals()[args.command]()
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        # signed redirect URLやtokenが例外文字列へ混入しないよう要約する。
        print('wiki reconciliation failed: ' + type(error).__name__, file=sys.stderr)
        raise SystemExit(1)
