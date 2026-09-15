#!/usr/bin/env python3
"""完了済みcompiled監査の記録だけを投影する。ROM/native受入は再実行しない。"""
from __future__ import annotations
import argparse
import collections
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_resume as resume
import pr16_ring_compiled_owner as owner

BASE = '155acde916ccaf38040252ab80195662f8f8f5b3'
SELF = 'scripts/pr16_ring_compiled_record.py'
TEST = 'tests/test_pr16_ring_compiled_record.py'
WORKFLOW = '.github/workflows/pr16-ring-compiled-record.yml'
OUT = ROOT / '.local/pr16-ring-compiled-record'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUTPUTS = (owner.REPORT, resume.STATE, resume.DOC, resume.BACKLOG, *LOGS)
ALLOWED = set(OUTPUTS + (SELF, TEST, WORKFLOW, owner.SELF, owner.TEST, owner.WORKFLOW))
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
NEXT = ('同一candidateのcompiled owner証拠を再利用し、未除外のcallstd4と、'
        'EventDesignからのFlag/QOL/Save finalize等の推移的native呼出し先だけを限定追跡する。'
        'map97/80の既存transition nativeは存在しないことがbyte確認済み。'
        'Ring580のstory取得ownerの有無を確定する。'
        '未実装と確認できた場合だけ正規story取引を実装し、条件不足・取消・二重取得・'
        '容量不足から通常取得、装備実戦、Save/fresh Continueへ進む。')


def need(ok, text):
    if not ok:
        raise ValueError(text)


def git(*args, env=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, env=env)


def validate_receipt(value):
    need(value['task'] == owner.TASK and value['classification'] == 'COMPILED_OWNER_BOUNDARY_NOT_NATIVE_ACCEPTANCE', 'wrong evidence scope')
    need(value['candidate'] == owner.CANDIDATE, 'wrong candidate')
    for key in ('candidate_bytes_checked', 'compiled_event_runtime_verified'):
        need(value[key] is True, 'missing compiled proof: ' + key)
    for key in ('all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
        need(value[key] is False, 'unsupported acceptance: ' + key)
    for key in ('new_emulator_processes', 'accepted_native_cases_replayed', 'rom_changes'):
        need(type(value[key]) is int and value[key] == 0, 'unexpected execution: ' + key)
    need(value['reachable_event_reward_calls'] == [] and value['script_nodes'], 'changed compiled graph')
    need(set(value['source_bindings']) == set(owner.SOURCES), 'incomplete source bindings')
    for name, binding in value['source_bindings'].items():
        need(owner.identity(resume.safe_path(ROOT, name).read_bytes()) == binding, 'stale compiled proof: ' + name)
    verification = value['verification']
    need(verification['run']['head_sha'] == value['source_head'], 'run/source mismatch')
    need(verification['run']['status'] == 'completed' and verification['run']['conclusion'] == 'success', 'unverified Actions success')
    need(verification['job']['status'] == 'completed' and verification['job']['conclusion'] == 'success', 'unverified job success')
    need(verification['job']['run_id'] == verification['run']['id'], 'job/run mismatch')
    need(verification['artifact']['head_sha'] == value['source_head'] and verification['artifact']['run_id'] == verification['run']['id'], 'artifact/run mismatch')
    need(re.fullmatch('[0-9a-f]{64}', verification['artifact']['sha256']) is not None, 'artifact digest missing')
    need(verification['focused_tests'] == {'tests_run': 24, 'successful': True, 'failures': 0, 'errors': 0, 'skips': 0}, 'focused tests not verified')
    return value


def project(state, backlog, report):
    """状態入力を壊さずRing限定参照のみ追加。BP受入/他gapはそのまま。"""
    s, b = copy.deepcopy(state), copy.deepcopy(backlog)
    need({k: s['candidate'].get(k) for k in owner.CANDIDATE} == owner.CANDIDATE
         and s['bp']['spending_accepted'] is True, 'accepted BP boundary differs')
    need(s['candidate'].get('final_product_sha_fixed') is False
         and s['candidate'].get('full_candidate_regression_complete') is False,
         'candidate acceptance boundary differs')
    need(s['latest_native_run'] == 34946969126 and GAP in s['remaining_physical_gap_ids'], 'native checkpoint moved')
    rows = [r for r in b['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR']
    need(len(rows) == 1 and GAP in rows[0]['remaining_supply_gap_ids'], 'Ring gap already closed or missing')
    need(rows[0]['selected_supply_entrypoints'][GAP] is None, 'Ring preferred entry changed')
    rows[0]['ring_compiled_owner'] = owner.REPORT
    s['ring_compiled_owner'] = {'path': owner.REPORT, 'classification': report['classification'],
        'source_head': report['source_head'], 'run_id': report['verification']['run']['id'],
        'compiled_event_runtime_verified': True, 'ring_acquisition_accepted': False}
    stop = ('Ring map97/80のcompiled owner限定監査は完了。candidate ceddbe91のevent runtimeを'
            '独立compileと全byte一致させ、map root→transition→dispatcherと有限CFGを照合。'
            '共有dispatcherはKANTO_LEAGUE_CLEAR/FINAL_LEAGUE_CLEAREDの2eventへ接続。'
            '70命令332 bytes、native4種11呼出し、到達EventDesign reward呼出し0。'
            '既存transition nativeなし。callstd4/推移的calleeは未除外で、'
            'Ring通常取得や全ROMのgiver不存在を証明したものではない。正式BP受入run34946969126は維持。')
    s['bp']['current_stop'] = stop
    s['bp']['next_step'] = s['next_action']['goal_ja'] = NEXT
    s['next_action']['read_paths'] = [owner.REPORT, owner.SOURCE_REPORT, owner.SELF,
        'overlays/event_design/event_design.c', 'scripts/build_event_design_stage.py',
        'config/event_design_bindings.csv']
    s['source_change_review_ja'] = stop + ' ゲームruntime・受入原本は変更していない。'
    s['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'accepted_standalone_replays': 0, 'candidate_reconstructions': 2,
        'scope_ja': 'compiled監査実装。初回はCLI importで失敗、修正後に同一候補で完了。native受入追加なし。'}
    note = 'Ring compiled監査の成功原本とsource hashが同じなら再compile/再scanしない。記録された未解決外部ownerだけを進め、受入済みBPを再実行しない。'
    if note not in s['do_not_repeat']:
        s['do_not_repeat'].append(note)
    return s, b


def prepare(path):
    report = validate_receipt(json.loads(path.read_text()))
    need(not (ROOT / owner.REPORT).exists(), 'compiled receipt already recorded; do not duplicate')
    state = resume.validate(ROOT)
    backlog = resume.load(ROOT, resume.BACKLOG)
    state, backlog = project(state, backlog, report)
    (ROOT / owner.REPORT).write_bytes(owner.stable(report))
    for name in (*owner.SOURCES, owner.REPORT, SELF, TEST, WORKFLOW, owner.WORKFLOW):
        state['source_bindings'][name] = owner.identity((ROOT / name).read_bytes())
    state['logs_synchronized'] = False
    (ROOT / resume.BACKLOG).write_bytes(owner.stable(backlog))
    (ROOT / resume.STATE).write_bytes(owner.stable(state))
    (ROOT / resume.DOC).write_text(resume.render(state), encoding='utf-8')
    check()


def check():
    report = validate_receipt(resume.load(ROOT, owner.REPORT))
    state = resume.validate(ROOT)
    need(state['ring_compiled_owner']['run_id'] == report['verification']['run']['id'], 'resume receipt mismatch')
    backlog = resume.load(ROOT, resume.BACKLOG)
    need(project(state, backlog, report) == (state, backlog), 'compiled projection drift')
    return report


def logs():
    report = check()
    tests = json.loads((OUT / 'tests.json').read_text())
    need(tests['successful'] is True and tests['tests_run'] > 0, 'recording tests failed')
    stamp = datetime.now(timezone.utc).isoformat()
    verify = report['verification']
    entry = (f'\n\n## {stamp} — {owner.TASK}\n- Timestamp: {stamp}\n- Task: {owner.TASK}\n'
        '- Status: DONE / compiled owner限定監査実装・検証・記録。Ring通常取得は未完。\n'
        '- Version: PR16 Ring compiled owner boundary\n'
        '- Summary: map97/80の誤解しやすいscript_pointer列をtransition本体として扱い、map table、schedule、有限CFGと独立compileしたevent runtimeをcandidateのbyteへ結合。未知opcode/外部分岐/operand途中/不正Thumbをfail-closedにし、未解決nativeをgiver不存在へ昇格しない。\n'
        f'- Verify: compiled異常系24 tests PASS、Actions run{verify["run"]["id"]} / job{verify["job"]["id"]} success。記録/固定引継ぎ {tests["tests_run"]} tests PASS、read-only check、task graph、diff、最終index差分guardを必須gateとする。\n'
        f'- Evidence: {owner.REPORT}; tested HEAD={report["source_head"]}; artifact={verify["artifact"]["id"]} / SHA256={verify["artifact"]["sha256"]}。初回run34956435284のimport失敗と記録run34957907451のmetadata比較失敗は保持しsuccessへ読み替えない。\n'
        '- Preserved: candidate ceddbe91 / CRC3EB17B36、正式BP checkpoint/原本、Ring source-only原本不変。候補再構築2回（初回CLI失敗の修正を含む）、native0、受入済み単独再実行0、ゲームruntime変更0。\n'
        '- Files changed: compiled監査と起動/異常系tests、限定検証/記録workflow、記録helper/tests、compiled receipt、P08のRing参照、固定引継ぎMD/JSON、両ログ。\n'
        '- Commit: この記録を含む同branchへの非force commit。自己SHAは外部refで確認。既存full guard failureは保持し追加違反0と前後出力完全一致を要求。\n'
        '- Network: GitHub connector/Actions。固定private入力はrunner内のみ、ROM/save/private archiveをtracked/artifactへ追加しない。全Actions green・merge・release・baseline変更を主張しない。\n'
        '- Next: ' + NEXT + '\n')
    for name in LOGS:
        p = ROOT / name
        need(owner.TASK not in p.read_text(), 'completion log already exists')
        with p.open('a', encoding='utf-8') as stream:
            stream.write(entry)
    state = resume.load(ROOT, resume.STATE)
    state['logs_synchronized'] = True
    (ROOT / resume.STATE).write_bytes(owner.stable(state))
    (ROOT / resume.DOC).write_text(resume.render(state), encoding='utf-8')
    check()


def guard():
    import guard_private_files as g
    changed = git('diff', '--cached', '--name-only', BASE).decode().splitlines()
    need(set(changed) == ALLOWED, 'unexpected changed paths or missing task output')
    for name in changed:
        raw = git('show', ':' + name)
        need(raw == (ROOT / name).read_bytes(), 'index/worktree differ')
        raw.decode('utf-8')
        need(b'\0' not in raw and Path(name).suffix not in g.BLOCKED_SUFFIXES, 'non-text/private suffix')
        need(not any(name == p or name.startswith(p + '/') for p in g.BLOCKED_PARTS), 'private path')
        before = subprocess.run(['git', 'show', BASE + ':' + name], cwd=ROOT, capture_output=True).stdout
        def bad(data):
            lines = data.decode('utf-8', errors='replace').splitlines()
            return collections.Counter(lines[n-1] for n in g.document_user_path_lines(data))
        need(not (bad(raw) - bad(before)), 'new private document path')
    with tempfile.TemporaryDirectory(dir=OUT) as temporary:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'baseline.index'))
        git('read-tree', BASE, env=env)
        command = [sys.executable, 'scripts/guard_private_files.py']
        before = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
        after = subprocess.run(command, cwd=ROOT, capture_output=True)
    need(before.returncode in (0, 1) and (before.returncode, before.stdout, before.stderr) ==
         (after.returncode, after.stdout, after.stderr), 'standard private guard output changed')
    result = {'base': BASE, 'changed_paths': changed, 'new_violations': 0,
        'full_guard_before': before.returncode, 'full_guard_after': after.returncode,
        'exact_output_match': True, 'full_guard_pass_claimed': after.returncode == 0}
    (OUT / 'guard.json').write_bytes(owner.stable(result))
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'check', 'logs', 'guard'))
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        need(args.receipt is not None, 'receipt required')
        prepare(args.receipt)
    elif args.command == 'check':
        check()
        print('PASS_COMPILED_OWNER_RECORD_NOT_NATIVE_ACCEPTANCE')
    elif args.command == 'logs':
        logs()
    else:
        guard()
