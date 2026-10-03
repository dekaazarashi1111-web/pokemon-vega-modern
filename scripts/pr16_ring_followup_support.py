#!/usr/bin/env python3
"""PR16限定工程の検証・正本更新・非force記録。受入済みnativeは起動しない。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
SELF = 'scripts/pr16_ring_followup_support.py'
CANDIDATE = {'size': 33554432, 'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b', 'crc32': '3EB17B36'}
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'


def need(ok, text):
    if not ok:
        raise ValueError(text)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def load(path):
    return json.loads((ROOT / path).read_bytes())


def cmd(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def api(path):
    return json.loads(cmd('gh', 'api', 'repos/' + REPO + '/' + path))


def assert_remote(head):
    need(cmd('git', 'ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == head, 'remote HEAD競合')
    pr = api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged']
         and pr['head']['sha'] == head and pr['head']['ref'] == BRANCH
         and pr['head']['repo']['full_name'] == REPO, 'PR境界不一致')
    return pr


def run(task):
    """taskのsource/testを検証後、1工程だけ記録する。重複実行は拒否する。"""
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_compiled_record as guard
    need(os.environ.get('GITHUB_REPOSITORY') == REPO, 'repository不一致')
    need(os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'branch不一致')
    head = cmd('git', 'rev-parse', 'HEAD')
    need(head == os.environ['GITHUB_SHA'], 'checkout不一致')
    assert_remote(head)
    subprocess.run(['git', 'merge-base', '--is-ancestor', task.BASE, head], cwd=ROOT, check=True)
    need(not (ROOT / task.REPORT).exists(), '完了済み工程: 保存原本を再利用すること')
    out = ROOT / '.local' / task.SLUG
    out.mkdir(parents=True, exist_ok=True)
    state, backlog = resume.validate(ROOT), load(BACKLOG)
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(state['candidate']['sha256'] == CANDIDATE['sha256']
         and state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True
         and GAP in state['remaining_physical_gap_ids'] and GAP in row['remaining_supply_gap_ids']
         and row['selected_supply_entrypoints'][GAP] is None, '受入境界不一致')
    checkpoint = identity((ROOT / CHECKPOINT).read_bytes())
    prior = load(task.PRIOR)
    need(prior['analysis']['candidate'] == CANDIDATE, '先行candidate不一致')
    # 保存証拠の入力が変わっていないことだけ確認。先行ABI/nativeは実行しない。
    saved.bindings_fresh(ROOT, prior['source_bindings'])
    actions = []
    for rid, sha in ((prior['run_id'], prior['source_head']),
                     (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        r = api('actions/runs/' + str(rid))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == sha, '先行Actions不一致')
        actions.append({k: r[k] for k in ('id', 'head_sha', 'status', 'conclusion')})
    query = 'actions/runs?branch=codex%2Fmodernization-followup-20260908&'
    live = api(query + 'per_page=20')['workflow_runs']
    active = sum((api(query + 'status=' + status + '&per_page=100')['workflow_runs']
                  for status in ('in_progress', 'queued')), [])
    need(not [r for r in active if r['id'] != int(os.environ['GITHUB_RUN_ID'])
              and '/pr16-ring-' in r['path']], '別Ring工程が実行中')
    sources = tuple(dict.fromkeys((SELF, task.SELF, task.TEST, task.WORKFLOW,
        task.PRIOR, CHECKPOINT, 'scripts/pr16_resume.py', 'scripts/pr16_ring_compiled_record.py',
        'scripts/guard_private_files.py', *task.SOURCES)))
    bindings = {p: identity((ROOT / p).read_bytes()) for p in sources}
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=Path(task.TEST).name)
    with (out / 'tests.txt').open('w', encoding='utf-8') as stream:
        t = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': t.testsRun, 'failures': len(t.failures), 'errors': len(t.errors),
             'skips': len(t.skipped), 'successful': t.wasSuccessful() and not t.skipped}
    (out / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'] and t.testsRun >= task.MIN_TESTS, '限定tests失敗')
    result = task.analyze(prior, out)
    need(result['candidate'] == CANDIDATE and result['ring_acquisition_accepted'] is False
         and result['release_ready'] is False and result['rom_changes'] == 0
         and result['new_emulator_processes'] == 0, 'scope逸脱')
    saved.bindings_fresh(ROOT, bindings)
    value = {'schema_version': 1, 'task': task.TASK, 'source_head': head,
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
        'analysis': result, 'source_bindings': bindings, 'focused_tests': tests,
        'reused_successful_actions': actions,
        'actions_observed_before_record': [{k: r[k] for k in ('id','name','head_sha','status','conclusion')} for r in live]}
    (ROOT / task.REPORT).write_bytes(stable(value))
    stop, next_step = task.summaries(result)
    state[task.KEY] = {'path': task.REPORT, 'source_head': head, 'run_id': value['run_id']}
    row[task.KEY] = task.REPORT
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = next_step
    state['next_action']['read_paths'] = [task.REPORT, task.SELF, task.PRIOR]
    state['observed_head'] = head
    state['observed_head_semantics'] = '限定工程のsource HEAD。完了commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = f'先行run{prior["run_id"]}とBP run34946969126成功照合。今回run{value["run_id"]}は記録時in_progress。action_requiredを成功へ読み替えない。'
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': result.get('candidate_reconstructions', 0),
        'accepted_standalone_replays': 0, 'scope_ja': stop}
    state['do_not_repeat'].append(task.NO_REPEAT)
    for p in (SELF, task.SELF, task.TEST, task.WORKFLOW, task.REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(state))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    for action in ('render', 'check'):
        subprocess.run([sys.executable, 'scripts/pr16_resume.py', action], cwd=ROOT, check=True)
    need(identity((ROOT / CHECKPOINT).read_bytes()) == checkpoint, 'BP checkpoint変更')
    stamp = datetime.now(timezone.utc).isoformat()
    outputs = (task.REPORT, STATE, DOC, BACKLOG, *LOGS)
    entry = (f'\n\n## {stamp} — {task.TASK}\n- Timestamp: {stamp}\n- Task: {task.TASK} / {task.TITLE}\n'
        f'- Status: DONE / 限定工程。Ring通常取得の受入ではない。\n- Version: {task.SLUG}\n'
        f'- Summary: {stop}\n- Files changed: {task.SELF}, {task.TEST}, {task.WORKFLOW}, {task.REPORT}, 固定MD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: 限定{tests["tests_run"]} tests PASS、source hash照合、render/check PASS、BP checkpoint不変。task graph/最終index差分guard/diffはcommit前必須。\n'
        f'- Evidence: source={head}; run={value["run_id"]}（記録時in_progress）。\n'
        f'- Preserved: ROM変更0、emulator0、受入済みnative/既読ABI再実行0。今回候補復元{result.get("candidate_reconstructions",0)}。\n'
        '- Commit: 本工程のguard PASS後、同branchへ非force push。完了SHAはremote ref/Actionsで確認。\n'
        '- Network: GitHub connector/Actions、必要時のみ既存hash固定candidate復元。外部技術資料なし。\n'
        '- Boundary: 既存全体guard違反の前後一致と新規違反0を検査。全体guard PASS、全CI green、merge/release/baseline変更は主張しない。\n'
        f'- Next: {next_step}\n')
    for p in LOGS:
        need(task.TASK not in (ROOT / p).read_text(encoding='utf-8'), 'ログ重複')
        with (ROOT / p).open('a', encoding='utf-8') as stream:
            stream.write(entry)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], cwd=ROOT, check=True)
    subprocess.run(['git', 'add', '--', *outputs], cwd=ROOT, check=True)
    guard.BASE, guard.OUT, guard.ALLOWED = task.BASE, out, set((task.SELF, task.TEST, task.WORKFLOW, *task.EXTRA_CODE, *outputs))
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    saved.bindings_fresh(ROOT, bindings)
    assert_remote(head)
    for key, val in (('user.name', 'github-actions[bot]'), ('user.email', '41898282+github-actions[bot]@users.noreply.github.com')):
        subprocess.run(['git', 'config', key, val], cwd=ROOT, check=True)
    subprocess.run(['git', 'commit', '-m', task.TASK + ': ' + task.TITLE], cwd=ROOT, check=True)
    commit = cmd('git', 'rev-parse', 'HEAD')
    subprocess.run(['git', 'push', 'origin', 'HEAD:refs/heads/' + BRANCH], cwd=ROOT, check=True)
    assert_remote(commit)
    for p in outputs:
        need(subprocess.check_output(['git','show','HEAD:'+p], cwd=ROOT) == (ROOT / p).read_bytes(), 'commit byte不一致')
    need(not cmd('git','status','--porcelain','--untracked-files=no'), 'tracked差分残存')
    receipt = {'status': 'PASS_RECORDED_NONFORCE_PUSHED', 'task': task.TASK, 'source_head': head,
               'commit': commit, 'run_id': value['run_id'], 'tests': tests, 'outputs': list(outputs),
               'new_emulator_processes': 0, 'ring_acquisition_accepted': False, 'release_ready': False}
    (out / 'recorded-result.json').write_bytes(stable(receipt))
    print('RESULT=DONE TASK='+task.TASK+' VERIFY=PASS COMMIT='+commit)
    print(json.dumps(receipt, ensure_ascii=False))
