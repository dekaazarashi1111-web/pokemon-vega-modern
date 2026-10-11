#!/usr/bin/env python3
"""Ringの誤ったsource入口を修正し、限定event graphと未完境界を記録する。

ROMやセーブを生成・変更せず、eventの宣言をnative取得証拠に昇格しない。
checkはread-only。prepareは同じ固定引継ぎとRing項目だけを書き換える。
"""
from __future__ import annotations

import argparse
import collections
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import pr16_resume as resume

ROOT = Path(__file__).resolve().parents[1]
BASE = 'dc491d88c86a99d86513a74cce6c55deb165eb4a'
BRANCH = 'codex/modernization-followup-20260908'
TASK = 'PR-P08-7-RING-OWNER'
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
EVENT = 'EVENT_KEY_MAIN_FINAL_LEAGUE_CLEARED'
PLAN = 'content/event_design_implementation/event_plan.json'
BINDINGS = 'config/event_design_bindings.csv'
CANONICAL = 'content/collection_supply_v1/canonical_model.json'
REPORT = 'content/modernization/pr16_ring_owner_resolution.json'
MAPPER = 'scripts/pr16_p05_native_supply_evidence_map.py'
TEST = 'tests/test_pr16_ring_owner.py'
WORKFLOW = '.github/workflows/pr16-ring-owner.yml'
SELF = 'scripts/pr16_ring_owner.py'
LOGS = ('design/run_log.md', 'design/version_log.md')
SOURCES = (PLAN, BINDINGS, CANONICAL, 'overlays/event_design/event_design.c',
           'scripts/build_event_design_stage.py', 'scripts/pr16_gear_originals.py',
           MAPPER, 'tests/test_pr16_p05_native_supply_evidence_map.py', SELF, TEST)
OUTPUTS = (REPORT, resume.BACKLOG, resume.STATE, resume.DOC, *LOGS)
ALLOWED = set(OUTPUTS + (SELF, TEST, MAPPER,
    'tests/test_pr16_p05_native_supply_evidence_map.py', WORKFLOW))
NEXT = ('同じcandidateのmap97/80・FINAL_LEAGUE_CLEARED dispatcherを限定byte照合し、'
        '既存native/specialによるRing付与の有無を追う。未実装と確認できた場合だけ'
        '正規story取引を実装し、条件不足・取消・二重取得・容量不足から通常取得、'
        '装備実戦、Save/fresh Continueへ進む。')
STOP = ('Ringの誤入口pr16_gear_originals.py:verifyを選択しないよう実装し、'
        '旧inventoryの再投影で受入済みBPを再openしないよう修正。'
        '限定source graphでは最終リーグ完了eventのreward_key=NONE・到達GIVE_REWARD=0。'
        'これはROM内の全owner不在証明ではない。Ring native受入は未完、次はmap97/80のcompiled owner。')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(name):
    raw = resume.safe_path(ROOT, name).read_bytes()
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def git(*args, env=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, env=env)


def one(rows, key, value):
    matches = [row for row in rows if row.get(key) == value]
    need(len(matches) == 1, '対象keyの欠落または重複: ' + value)
    return matches[0]


def analyze_event(plan, bindings):
    """1件の明示step graphだけを読む。runtimeの副作用やROM到達性は主張しない。"""
    event = one(plan['events'], 'event_key', EVENT)
    placement = one(plan['placements'], 'placement_key', event['placement_key'])
    binding = one(bindings, 'placement_key', event['placement_key'])
    need(EVENT in binding['event_keys'].split('|'), 'eventとplacement bindingが不一致')
    need(event['map_key'] == placement['map_key'] == binding['map_key'], 'map ownerが不一致')
    need(event['unlock_key'] == 'FINAL_LEAGUE_CLEARED', 'unlock変更は再審査が必要')
    need(placement['trigger_type'] == binding['trigger_type'] == 'MAP_ENTER', 'trigger不一致')
    need(binding['status'] == 'PASS' and binding['script_owner'] == 'EVENT_DESIGN_DISPATCHER', 'binding未検証')
    one(plan['conditions'], 'condition_key', event['condition_key'])
    steps = event['steps']
    need(bool(steps), '空event graph')
    nodes = {step['step_key']: step for step in steps}
    need(len(nodes) == len(steps), '重複step')
    known = {'CHECK_CONDITION', 'SHOW_DIALOGUE', 'SET_STATE', 'GIVE_REWARD', 'END'}
    for step in steps:
        need(step['op'] in known, '未解釈opを取得証拠へ読み替えない')
        for key in ('next_step_key', 'alt_step_key'):
            need(step[key] == 'NONE' or step[key] in nodes, '未解決step参照')
        if step['op'] == 'GIVE_REWARD':
            one(plan['rewards'], 'reward_key', step['arg_key'])
    visited, pending = set(), [steps[0]['step_key']]
    while pending:
        key = pending.pop()
        if key in visited:
            continue
        visited.add(key)
        step = nodes[key]
        if step['op'] != 'END':
            pending += [step[k] for k in ('next_step_key', 'alt_step_key') if step[k] != 'NONE']
    need(any(nodes[key]['op'] == 'END' for key in visited), '到達可能なENDがない')
    gives = [step['step_key'] for step in steps if step['step_key'] in visited and step['op'] == 'GIVE_REWARD']
    return {'event_key': EVENT, 'placement_key': event['placement_key'],
        'map_group': int(binding['group_id']), 'map_id': int(binding['map_id']),
        'unlock_key': event['unlock_key'], 'condition_key': event['condition_key'],
        'declared_reward_key': event['reward_key'], 'trigger': binding['trigger_type'],
        'binding_addresses': {key: binding[key] for key in ('dispatcher_address',
            'stage37_record_address', 'stage37_script_pointer_address')},
        'reachable_step_keys': [step['step_key'] for step in steps if step['step_key'] in visited],
        'reachable_give_reward_step_keys': gives,
        'source_graph_only': True, 'candidate_bytes_checked': False,
        'all_runtime_owners_excluded': False, 'ring_acquisition_accepted': False}


def build_report(source_head, run_id=0):
    need(re.fullmatch('[0-9a-f]{40}', source_head), 'source HEAD不正')
    state = resume.load(ROOT, resume.STATE)
    canonical = resume.load(ROOT, CANONICAL)
    ring = one(canonical['items'], 'item_key', 'ITEM_KEY_MEGA_RING')
    need(ring['item_id'] == 580 and ring['quantity'] == 1 and
         ring['source'] == 'STORY_EVENT' and ring['unlock'] == 'FINAL_LEAGUE_CLEARED', 'Ring正本が変更された')
    with (ROOT/BINDINGS).open(encoding='utf-8', newline='') as stream:
        bindings = list(csv.DictReader(stream))
    graph = analyze_event(resume.load(ROOT, PLAN), bindings)
    need(graph['declared_reward_key'] == 'NONE' and not graph['reachable_give_reward_step_keys'],
         'event取引が変更されたため旧停止点を再利用しない')
    return {'schema_version': 1, 'task': TASK, 'gap_id': GAP,
        'classification': 'SOURCE_ONLY_NOT_NATIVE_ACCEPTANCE', 'source_head': source_head,
        'run_id': run_id, 'candidate': {k: state['candidate'][k] for k in ('sha256', 'size', 'crc32')},
        'canonical_ring': ring, 'event_graph': graph,
        'rejected_entry': {'path': 'scripts/pr16_gear_originals.py', 'scope': 'verify',
            'reason_ja': '過去artifactの検証関数であり、通常プレイのRing取得ownerではない。'},
        'preferred_entry_candidate': None, 'runtime_owner_verified': False,
        'next_step_ja': NEXT, 'new_emulator_processes': 0, 'rom_changes': 0,
        'accepted_bp_replays': 0, 'ring_acquisition_accepted': False, 'release_ready': False,
        'source_bindings': {name: identity(name) for name in SOURCES}}


def project_ring_only(backlog, report):
    value = copy.deepcopy(backlog)
    row = one(value['remaining_conditions'], 'id', 'NATURAL_CAPTURE_GEAR')
    need(GAP in row['remaining_supply_gap_ids'], 'Ring受入済み台帳を再openしない')
    need(report['preferred_entry_candidate'] is None and report['ring_acquisition_accepted'] is False,
         'source記録だけではRingを受入しない')
    row['selected_supply_entrypoints'][GAP] = None
    row['ring_owner_resolution'] = REPORT
    return value


def check():
    report = resume.load(ROOT, REPORT)
    need(report == build_report(report['source_head'], report['run_id']), 'Ring source記録が陳腐化')
    state = resume.validate(ROOT)
    backlog = resume.load(ROOT, resume.BACKLOG)
    need(project_ring_only(backlog, report) == backlog, 'Ring台帳が未同期')
    need(state['ring_owner_resolution']['path'] == REPORT, 'Ring引継ぎが未同期')
    need(state['bp']['spending_accepted'] is True and GAP in state['remaining_physical_gap_ids'],
         '受入境界が変更された')
    return report


def prepare(source_head, run_id):
    state = resume.validate(ROOT)
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'], 'BP正本が進んだ')
    report = build_report(source_head, run_id)
    (ROOT/REPORT).write_bytes(stable(report))
    backlog = project_ring_only(resume.load(ROOT, resume.BACKLOG), report)
    (ROOT/resume.BACKLOG).write_bytes(stable(backlog))
    state['ring_owner_resolution'] = {'path': REPORT, 'source_head': source_head,
        'run_id': run_id, 'classification': report['classification'], 'runtime_owner_verified': False}
    state['bp']['current_stop'] = STOP
    state['bp']['next_step'] = NEXT
    state['next_action']['goal_ja'] = NEXT
    state['next_action']['read_paths'] = [REPORT, PLAN, BINDINGS,
        'overlays/event_design/event_design.c', 'scripts/build_event_design_stage.py', SELF]
    state['candidate_scope_ja'] = '同一candidateのBP3勝・稼得・通常購入・保存再開は受入済み。Ring/policy/Circusと最終製品SHAは未受入。'
    state['source_change_review_ja'] = STOP + ' ROM/runtime/受入原本は不変。'
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'accepted_standalone_replays': 0, 'scope_ja': 'Ring source入口選択と既受入BPを保全する投影処理の修正。native受入の追加なし。'}
    note = 'Ring source graphと誤入口選択の修正は完了。同一sourceで再scanせず、map97/80 compiled ownerの未観測区間へ進む。source-onlyをRing通常取得や全ROMのgiver不在証明にしない。'
    if note not in state['do_not_repeat']:
        state['do_not_repeat'].append(note)
    for name in (*SOURCES, REPORT):
        state['source_bindings'][name] = identity(name)
    state['logs_synchronized'] = False
    (ROOT/resume.STATE).write_bytes(stable(state))
    (ROOT/resume.DOC).write_text(resume.render(state), encoding='utf-8')
    check()


def record_logs():
    report = check()
    out = ROOT/'.local/pr16-ring-owner'
    tests = json.loads((out/'tests.json').read_text())
    need(tests['successful'] is True and tests['tests_run'] > 0, 'focused tests未成功')
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n'
        f'- Task: {TASK} / Ring誤入口選択と既受入BP再openの防止\n'
        '- Status: DONE / source入口選択修正。P05_NATIVE_RING_ACQUISITION_PHYSICALは未完。\n'
        '- Version: PR16 Ring source owner boundary\n'
        '- Summary: '+STOP+'\n'
        f'- Verify: Ring/旧mapper/固定引継ぎ focused {tests["tests_run"]} tests PASS。check、task graph、diff検査を実行。最終index guardは開始HEADとの差分と既存違反を別計上し、非force反映の必須gateにする。\n'
        f'- Evidence: {REPORT}; source HEAD={report["source_head"]}; Actions run={report["run_id"]}。全Actions green、Ring実取得成功、最終candidate受入は主張しない。\n'
        '- Files changed: source mapper・回帰tests、Ring限定graph検査/記録scriptとtests、専用workflow、限定JSON、P08のRing参照、固定引継ぎMD/JSON、両ログ。\n'
        '- Preserved: BP run34946969126、candidate ceddbe91、正式checkpoint、過去receiptは不変。ROM生成0・native0・受入済み単独再実行0。merge/release/baseline変更なし。\n'
        '- Commit: この記録を含むcommit。自己SHAは外部refで確認。同一branchへ非force pushのみ。\n'
        '- Network: GitHub connector/Actionsでexact HEADと最新runを確認。新しいprivate入力やROM/saveを公開しない。\n'
        '- Next: '+NEXT+'\n')
    for name in LOGS:
        path = ROOT/name
        need(TASK not in path.read_text(), '同じ完了ログを重複追記しない')
        with path.open('a', encoding='utf-8') as stream:
            stream.write(entry)
    state = resume.load(ROOT, resume.STATE)
    observations = json.loads((out/'actions-observed.json').read_text())
    state['ring_owner_resolution']['actions_observed'] = observations
    state['ring_owner_resolution']['recording_status'] = 'FOCUSED_PASS_BEFORE_NONFORCE_PUSH'
    state['logs_synchronized'] = True
    (ROOT/resume.STATE).write_bytes(stable(state))
    (ROOT/resume.DOC).write_text(resume.render(state), encoding='utf-8')
    check()


def guard(base):
    """開始HEADと最終indexの標準guard結果を比較。既存違反を抑制しない。"""
    import guard_private_files as g
    need(base == BASE, '監査開始HEADが不一致')
    changed = [p for p in git('diff', '--cached', '--name-only', '-z', base).decode().split('\0') if p]
    need(set(changed) == ALLOWED, '許可path以外の変更または記録欠落')
    for name in changed:
        raw = git('show', ':'+name)
        need(raw == (ROOT/name).read_bytes(), 'index/worktree不一致')
        raw.decode('utf-8')
        need(b'\0' not in raw and Path(name).suffix not in g.BLOCKED_SUFFIXES, 'binary/private suffix')
        need(not any(name == p or name.startswith(p+'/') for p in g.BLOCKED_PARTS), 'private path')
        old = subprocess.run(['git', 'show', base+':'+name], cwd=ROOT, capture_output=True).stdout
        def bad(body):
            lines = body.decode('utf-8', errors='replace').splitlines()
            return collections.Counter(lines[n-1] for n in g.document_user_path_lines(body))
        need(not (bad(raw)-bad(old)), '新規private文書path')
    out = ROOT/'.local/pr16-ring-owner'
    with tempfile.TemporaryDirectory(dir=out) as directory:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(directory)/'baseline.index'))
        git('read-tree', base, env=env)
        command = [sys.executable, 'scripts/guard_private_files.py']
        before = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
        after = subprocess.run(command, cwd=ROOT, capture_output=True)
    need(before.returncode in (0, 1) and (before.returncode, before.stdout, before.stderr) ==
         (after.returncode, after.stdout, after.stderr), '標準private guard結果が変化した')
    result = {'base': base, 'changed_paths': changed, 'new_violations': 0,
        'full_guard_before': before.returncode, 'full_guard_after': after.returncode,
        'exact_output_match': True, 'full_guard_pass_claimed': after.returncode == 0}
    (out/'guard.json').write_bytes(stable(result))
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'check', 'logs', 'guard'))
    args = parser.parse_args()
    if args.command == 'prepare':
        source_head = os.environ['GITHUB_SHA']
        need(git('rev-parse', 'HEAD').decode().strip() == source_head, 'checkout HEAD不一致')
        prepare(source_head, int(os.environ['GITHUB_RUN_ID']))
    elif args.command == 'check':
        check()
        print('PASS_SOURCE_ONLY_RING_OWNER_BOUNDARY')
    elif args.command == 'logs':
        record_logs()
    else:
        guard(BASE)


if __name__ == '__main__':
    main()
