#!/usr/bin/env python3
"""旧未読callee 0x09097105だけを採取する。保存済みgraphとnative受入は再実行しない。"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_flagset_continuation as saved

BASE = 'd0a03bbf0501a23de9bcf9845d5b0decbf7b80bc'
TASK = 'PR-P08-7-RING-CALLEE-BYTES'
SELF = 'scripts/pr16_ring_callee_bytes.py'
TEST = 'tests/test_pr16_ring_callee_bytes.py'
WORKFLOW = '.github/workflows/pr16-ring-callee-bytes.yml'
REPORT = 'content/modernization/pr16_ring_callee_bytes.json'
FRAME = 'content/modernization/pr16_ring_frame_join.json'
SOURCES = (SELF, TEST, WORKFLOW, FRAME, saved.REPORT, saved.ABI, saved.PATCH, saved.PRIOR,
           saved.SELF, 'scripts/pr16_ring_transitive_owner.py', 'scripts/pr16_ring_compiled_owner.py')
OUTPUTS = (REPORT, saved.STATE, saved.DOC, saved.BACKLOG, *saved.LOGS)
OUT = ROOT / '.local/pr16-ring-callee-bytes'
TARGET = 0x09097105
WINDOW = 1024
LIMIT = 512
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
need, stable, identity = saved.need, saved.stable, saved.identity


def read_prior():
    frame = json.loads((ROOT / FRAME).read_bytes())
    saved.bindings_fresh(ROOT, frame['source_bindings'])
    a = frame['analysis']
    need(a['classification'] == 'CONDITIONAL_FRAME_JOIN_NOT_NATIVE_ACCEPTANCE', 'wrong join scope')
    need(a['candidate'] == saved.CANDIDATE and a['priority_unread_targets'] == [TARGET], 'wrong target')
    need(a['call']['unread_callee'] == TARGET and not a['call']['callee_return_proven'], 'callee already proven')
    need(len(a['old_unread_targets']) == 18 and TARGET in a['old_unread_targets'], 'old frontier differs')
    for k in ('stack_integrity_proven', 'all_callers_resolved', 'all_runtime_owners_excluded',
              'ring_acquisition_accepted', 'release_ready'):
        need(a[k] is False, 'unsupported prior claim: ' + k)
    values = saved.read_inputs()
    graphs = [*values[1]['frontier']['graphs'], *values[2]['native_owners'].values(),
              json.loads((ROOT / saved.REPORT).read_bytes())['analysis']['graph']]
    need(all(g['entry'] != TARGET for g in graphs), 'callee already sampled')
    cached = {x for g in graphs for n in g['nodes'] for x in range(n['address'], n['address'] + n['size'])}
    return frame, cached


def validate_graph(g, cached):
    need(g['entry'] == TARGET and g['window'] == WINDOW, 'wrong bounded root')
    need(g['side_effects_excluded'] is False, 'unsupported side-effect claim')
    nodes = g['nodes']
    need(1 <= len(nodes) <= LIMIT, 'node budget')
    starts = [n['address'] for n in nodes]
    need(starts == sorted(set(starts)) and starts[0] == TARGET & ~1, 'unordered/duplicate nodes')
    occupied = set()
    for n in nodes:
        at, size = n['address'], n['size']
        need(type(at) is int and not at & 1 and size in (2, 4), 'bad instruction')
        need(TARGET & ~1 <= at and at + size <= (TARGET & ~1) + WINDOW, 'escaped window')
        region = set(range(at, at + size))
        need(not region & (occupied | cached), 'overlap or saved code rescan')
        need(len(bytes.fromhex(n['hex'])) == size, 'byte size mismatch')
        occupied |= region
        need(n['kind'] in ('ordinary', 'call', 'jump', 'conditional', 'indirect', 'return'), 'unknown node')
        if 'literal_address' in n:
            h = int.from_bytes(bytes.fromhex(n['hex'])[:2], 'little')
            need(h & 0xf800 == 0x4800 and n['literal_address'] == ((at + 4) & ~3) + (h & 255) * 4,
                 'literal address mismatch')
    need(g['memory_write_sites'] == [n['address'] for n in nodes if n['memory_write']], 'write sites mismatch')
    for e in g['external_edges']:
        need(e['site'] in starts, 'orphan external edge')
        t = e.get('target')
        need(t is None or (type(t) is int and t & 1 and saved.ROM_BASE <= (t & ~1) <
                          saved.ROM_BASE + saved.CANDIDATE['size']), 'bad external target')


def collect(raw, frame, cached, decode):
    saved.candidate_identity(raw)
    g = decode(raw, TARGET, window=WINDOW, limit=LIMIT)
    validate_graph(g, cached)
    samples = {}
    for n in g['nodes']:
        at, size = n['address'], n['size']
        data = raw[at - saved.ROM_BASE:at - saved.ROM_BASE + size]
        need(data.hex() == n['hex'], 'instruction byte mismatch')
        samples[(at, size)] = data
        if 'literal_address' in n:
            at = n['literal_address']
            need(saved.ROM_BASE <= at <= saved.ROM_BASE + len(raw) - 4, 'literal out of ROM')
            data = raw[at - saved.ROM_BASE:at - saved.ROM_BASE + 4]
            need(int.from_bytes(data, 'little') == n['literal_value'], 'literal value mismatch')
            samples[(at, 4)] = data
    old = frame['analysis']['old_unread_targets']
    external = sorted({e['target'] for e in g['external_edges'] if e.get('target') is not None})
    return {'classification': 'ONE_CALLEE_BYTES_NOT_NATIVE_ACCEPTANCE', 'candidate': saved.CANDIDATE,
            'target': TARGET, 'graph': g, 'sampled_ranges': [dict(address=a, hex=b.hex(), **identity(b))
                for (a, _), b in sorted(samples.items())],
            'sampled_instruction_bytes': sum(n['size'] for n in g['nodes']),
            'old_unread_targets': copy.deepcopy(old), 'sampled_old_targets': [TARGET],
            'external_targets': external,
            'additional_unread_targets': [t for t in external if t not in old and (t & ~1) not in cached],
            'old_frontier_removed': False, 'callee_return_proven': False,
            'stack_integrity_proven': False, 'all_callers_resolved': False,
            'all_runtime_owners_excluded': False, 'ring_acquisition_accepted': False, 'release_ready': False,
            'rom_changes': 0, 'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0,
            'prior_abi_classifications_replayed': 0, 'new_graph_decodes': 1, 'candidate_reconstructions': 1}


def preflight():
    import pr16_resume as resume
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT / REPORT).exists(), 'already sampled; use saved bytes')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'execution HEAD differs')
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], check=True)
    pr = saved.api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head
         and pr['head']['ref'] == 'codex/modernization-followup-20260908'
         and pr['head']['repo']['full_name'] == os.environ['GITHUB_REPOSITORY'], 'PR boundary differs')
    state = resume.validate(ROOT)
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True
         and GAP in state['remaining_physical_gap_ids'], 'accepted boundary differs')
    backlog = resume.load(ROOT, saved.BACKLOG)
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(GAP in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][GAP] is None, 'Ring owner moved')
    frame, _ = read_prior()
    reused = []
    for run_id, source in ((frame['run_id'], frame['source_head']),
                           (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        r = saved.api('actions/runs/' + str(run_id))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == source, 'prior Actions differs')
        reused.append({k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    runs = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    active = [r for r in runs if r['status'] != 'completed' and r['id'] != int(os.environ['GITHUB_RUN_ID'])
              and r['name'].startswith('pr16-ring-')]
    need(not active, 'another Ring run is active; do not duplicate')
    observed = [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs]
    value = {'head': head, 'reused_successful_actions': reused, 'actions_before': observed,
             'checkpoint': identity((ROOT / saved.CHECKPOINT).read_bytes()),
             'source_bindings': {p: identity((ROOT / p).read_bytes()) for p in SOURCES}}
    (OUT / 'preflight.json').write_bytes(stable(value))
    print(json.dumps({'preflight': 'PASS', 'previous': reused, 'actions': observed,
                      'remaining_physical_gap_ids': state['remaining_physical_gap_ids']}))


def record(rom):
    import pr16_resume as resume
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_compiled_record as guard
    before = json.loads((OUT / 'preflight.json').read_bytes())
    need(before['head'] == os.environ['GITHUB_SHA'], 'preflight HEAD differs')
    saved.bindings_fresh(ROOT, before['source_bindings'])
    need(not (ROOT / REPORT).exists(), 'already sampled; do not repeat')
    frame, cached = read_prior()
    raw = saved.safe(ROOT, rom).read_bytes()
    result = collect(raw, frame, cached, decoder.native_graph)
    need(saved.safe(ROOT, rom).read_bytes() == raw, 'candidate changed')
    value = {'schema_version': 1, 'task': TASK, 'source_head': before['head'],
             'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
             'analysis': result, 'source_bindings': before['source_bindings'],
             'reused_successful_actions': before['reused_successful_actions'],
             'actions_observed_before_record': before['actions_before']}
    (OUT / 'audit.json').write_bytes(stable(value))
    suite = unittest.TestSuite()
    for pattern in ('test_pr16_ring_callee_bytes.py', 'test_pr16_resume.py'):
        suite.addTests(unittest.defaultTestLoader.discover('tests', pattern=pattern))
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
             'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'], 'focused tests failed')
    value['focused_tests'] = tests
    (ROOT / REPORT).write_bytes(stable(value))
    state = resume.validate(ROOT)
    backlog = resume.load(ROOT, saved.BACKLOG)
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    row['ring_callee_bytes'] = REPORT
    stop = (f'WIP: 旧未読callee 0x09097105だけを同一candidateから{len(result["graph"]["nodes"])}命令採取し保存。'
            '帰還/SP/r4/返却pointerの検証は次のsource-only工程。旧18target台帳、継承frame、BP正式受入は維持。')
    next_step = ('保存済みpr16_ring_callee_bytes.jsonの0x09097105 graphからreturn/SP/r4と返却pointer・'
                 'stack非alias条件を限定検証する。candidate/FlagSet/FlagGet再採取、15辺再分類、BP再実行はしない。'
                 '旧18target台帳を削らず、全caller/全owner/Ring正規取得受入へ昇格しない。')
    state['ring_callee_bytes'] = {'path': REPORT, 'source_head': before['head'], 'run_id': value['run_id'],
                                'target': TARGET, 'ring_acquisition_accepted': False}
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = next_step
    state['next_action']['read_paths'] = [REPORT, SELF, FRAME, saved.REPORT, saved.ABI]
    state['observed_head'] = before['head']
    state['observed_head_semantics'] = '未読callee1根を採取したsource HEAD。最終commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = (f'前回frame結合run{frame["run_id"]}とBP run34946969126はcompleted/successを照合。'
        f'採取run{value["run_id"]}は保存時in_progress。通常CI action_requiredは成功に読み替えずreceiptにsnapshotを保存。')
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': 1, 'accepted_standalone_replays': 0,
        'scope_ja': '旧未読callee1根の限定byte取得のみ。既存graph/受入済みnativeの再実行0。'}
    state['do_not_repeat'].append('0x09097105の限定byte採取は保存済み。保存graphを再利用し、同一candidateから再採取しない。帰還/SP/r4/非alias検証は別工程。')
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / saved.STATE).write_bytes(stable(state))
    (ROOT / saved.BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    need(identity((ROOT / saved.CHECKPOINT).read_bytes()) == before['checkpoint'], 'BP checkpoint mutated')
    saved.bindings_fresh(ROOT, before['source_bindings'])
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 未読calleeの限定採取checkpoint\n'
        '- Status: STOPPED / 採取保存工程のみ完了。次に同じ保存byteでABIを検証する。\n- Version: PR16 callee bytes checkpoint\n'
        '- Summary: ' + stop + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定MD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: 新規採取異常系/固定resume {tests["tests_run"]} tests PASS、render/check PASS、BP checkpoint不変。task graph・最終index差分guard・diffを必須gateとする。\n'
        f'- Evidence: source={before["head"]}; run={value["run_id"]}（保存時in_progress）。\n'
        '- Preserved: ROM変更/native/既存15辺再分類/受入済み単独再実行0。未読byte用の同一candidate再構築1。旧18target台帳は削除しない。\n'
        '- Commit: このcheckpointを同branchに非force push。最終SHAはremote ref/resultで照合。\n'
        '- Network: GitHub connector/Actionsと既存hash固定入力復元。直接cloneはDNS失敗。外部技術資料検索なし。\n'
        '- Boundary: 既存全体guard違反の前後一致/新規違反0を要求。全体guard PASS、全Actions green、Ring受入を主張しない。merge/release/baseline変更なし。\n'
        '- Next: ' + next_step + '\n')
    for p in saved.LOGS:
        need(TASK not in (ROOT / p).read_text(encoding='utf-8'), 'duplicate checkpoint log')
        with (ROOT / p).open('a', encoding='utf-8') as stream:
            stream.write(entry)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], check=True)
    subprocess.run(['git', 'add', '--', *OUTPUTS], check=True)
    guard.BASE, guard.OUT, guard.ALLOWED = BASE, OUT, set((SELF, TEST, WORKFLOW, *OUTPUTS))
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    (OUT / 'summary.json').write_bytes(stable(result))
    print(json.dumps(result))


if __name__ == '__main__':
    if sys.argv[1:] == ['preflight']:
        preflight()
    elif len(sys.argv) == 3 and sys.argv[1] == 'record':
        record(sys.argv[2])
    else:
        raise SystemExit('usage: pr16_ring_callee_bytes.py preflight|record <candidate>')
