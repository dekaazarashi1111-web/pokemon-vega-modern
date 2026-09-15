#!/usr/bin/env python3
"""未読zero継続一根だけを採取。既証明graph/nativeは再実行しない。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = '878fdf65995378a97493dcee86872616aaea1236'
BRANCH = 'codex/modernization-followup-20260908'
TASK = 'PR-P08-7-RING-ZERO-BYTES'
SELF = 'scripts/pr16_ring_zero_bytes.py'
TEST = 'tests/test_pr16_ring_zero_bytes.py'
WORKFLOW = '.github/workflows/pr16-ring-zero-bytes.yml'
PRIOR = 'content/modernization/pr16_ring_nonzero_abi.json'
REPORT = 'content/modernization/pr16_ring_zero_bytes.json'
RESTORE = '.github/workflows/pr16-ring-callee-bytes.yml'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUT = ROOT / '.local/pr16-ring-zero-bytes'
TARGET, MAX_WINDOW, LIMIT, ROM_BASE = 0x0806DDBD, 128, 64, 0x08000000
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
SAMPLES = tuple('content/modernization/pr16_ring_' + s + '.json' for s in
                ('callee_bytes', 'helper_bytes', 'nonzero_bytes'))
SOURCES = (SELF, TEST, WORKFLOW, RESTORE, PRIOR, *SAMPLES,
    'scripts/pr16_ring_callee_bytes.py', 'scripts/pr16_ring_transitive_owner.py',
    'scripts/pr16_ring_flagset_continuation.py', 'scripts/pr16_ring_compiled_record.py',
    'scripts/pr16_resume.py')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)


def need(ok, text):
    if not ok:
        raise ValueError(text)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def window_for(cached):
    root = TARGET & ~1
    need(root not in cached, 'root already sampled')
    end = min([root + MAX_WINDOW] + [x for x in cached if root < x < root + MAX_WINDOW])
    need(end > root and not (end - root) % 2, 'invalid unread boundary')
    return end - root


def validate_graph(g, cached):
    root, window = TARGET & ~1, window_for(cached)
    need(g['entry'] == TARGET and g['window'] == window, 'wrong root/window')
    need(g['side_effects_excluded'] is False, 'unsupported side-effect claim')
    nodes = g['nodes']
    need(1 <= len(nodes) <= LIMIT, 'node budget')
    starts = [n['address'] for n in nodes]
    need(starts == sorted(set(starts)) and starts[0] == root, 'node order/root')
    occupied = set()
    for n in nodes:
        at, size = n['address'], n['size']
        need(type(at) is int and not at & 1 and size in (2, 4), 'invalid instruction')
        need(root <= at and at + size <= root + window, 'escaped unread range')
        span = set(range(at, at + size))
        need(not span & (occupied | cached), 'overlap/previous code rescan')
        occupied |= span
        raw = bytes.fromhex(n['hex'])
        need(len(raw) == size, 'instruction size differs')
        need(n['kind'] in ('ordinary', 'call', 'jump', 'conditional', 'indirect', 'return'), 'bad kind')
        if 'literal_address' in n:
            h = int.from_bytes(raw[:2], 'little')
            need(h & 0xf800 == 0x4800 and n['literal_address'] == ((at + 4) & ~3) + (h & 255) * 4,
                 'literal address differs')
    need(g['memory_write_sites'] == [n['address'] for n in nodes if n['memory_write']], 'write sites differ')
    for edge in g['external_edges']:
        need(edge['site'] in starts, 'orphan edge')
        t = edge.get('target')
        need(t is None or (type(t) is int and t & 1 and ROM_BASE <= (t & ~1) < 0x0A000000), 'invalid edge')
    return occupied


def inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_callee_bytes as previous
    prior = json.loads((ROOT / PRIOR).read_bytes())
    saved.bindings_fresh(ROOT, prior['source_bindings'])
    a = prior['analysis']
    need(a['candidate'] == saved.CANDIDATE and a['priority_unread_targets'] == [TARGET], 'target/candidate moved')
    need(a['nonzero_callee_return_proven'] is True and a['nonzero_callee_return_observed'] is False, 'nonzero premise')
    need(len(a['old_unread_targets']) == 18 and a['additional_unread_targets'] == [TARGET], 'frontier differs')
    for key in ('callee_return_proven', 'old_frontier_removed', 'stack_integrity_proven',
                'all_callers_resolved', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
        need(a[key] is False, 'unsupported prior claim: ' + key)
    _, cached = previous.read_prior()
    for path in SAMPLES:
        for n in json.loads((ROOT / path).read_bytes())['analysis']['graph']['nodes']:
            cached.update(range(n['address'], n['address'] + n['size']))
    window_for(cached)
    return prior, cached


def preflight():
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT / REPORT).exists(), 'already sampled: reuse report')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'HEAD differs')
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], check=True)
    pr = saved.api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head
         and pr['head']['ref'] == BRANCH and pr['head']['repo']['full_name'] == os.environ['GITHUB_REPOSITORY'], 'PR boundary differs')
    state = resume.validate(ROOT)
    row = next(r for r in resume.load(ROOT, BACKLOG)['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True
         and GAP in state['remaining_physical_gap_ids'] and GAP in row['remaining_supply_gap_ids']
         and row['selected_supply_entrypoints'][GAP] is None, 'acceptance boundary differs')
    prior, cached = inputs()
    reused = []
    for rid, source in ((prior['run_id'], prior['source_head']), (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        run = saved.api('actions/runs/' + str(rid))
        need(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == source, 'prior run differs')
        reused.append({k: run[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    runs = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    need(not [r for r in runs if r['status'] != 'completed' and r['id'] != int(os.environ['GITHUB_RUN_ID'])
              and '/pr16-ring-' in r['path']], 'another Ring run active')
    suite = unittest.defaultTestLoader.discover('tests', pattern='test_pr16_ring_zero_bytes.py')
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
             'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'] and tests['tests_run'] >= 14, 'focused tests failed')
    before = {'head': head, 'pr': {'number': 16, 'state': pr['state'], 'draft': pr['draft'], 'merged': pr['merged']},
        'unread_window': window_for(cached), 'reused_successful_actions': reused,
        'actions_before': [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs],
        'checkpoint': identity((ROOT / CHECKPOINT).read_bytes()),
        'source_bindings': {p: identity((ROOT / p).read_bytes()) for p in SOURCES}}
    (OUT / 'preflight.json').write_bytes(stable(before))
    print(json.dumps(before, ensure_ascii=False))


def restore():
    import pr16_ring_flagset_continuation as saved
    saved.bindings_fresh(ROOT, json.loads((OUT / 'preflight.json').read_bytes())['source_bindings'])
    text = (ROOT / RESTORE).read_text(encoding='utf-8')
    marker = '      - name: 未読byte取得用の同一hash candidateのみ復元\n'
    need(text.count(marker) == 1, 'restore step ambiguous')
    block = text.split(marker, 1)[1].split('      - name:', 1)[0]
    lines = block.split('        run: |\n', 1)[1].splitlines()
    need(all(not line or line.startswith('          ') for line in lines), 'restore indentation')
    subprocess.run(['bash', '-euo', 'pipefail', '-c', '\n'.join(line[10:] if line else '' for line in lines)], cwd=ROOT, check=True)


def record(rom):
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_compiled_record as guard
    before = json.loads((OUT / 'preflight.json').read_bytes())
    need(before['head'] == os.environ['GITHUB_SHA'] and not (ROOT / REPORT).exists(), 'HEAD/report differs')
    saved.bindings_fresh(ROOT, before['source_bindings'])
    prior, cached = inputs()
    raw = saved.safe(ROOT, rom).read_bytes()
    saved.candidate_identity(raw)
    graph = decoder.native_graph(raw, TARGET, window=window_for(cached), limit=LIMIT)
    validate_graph(graph, cached)
    samples = {}
    for n in graph['nodes']:
        at, size = n['address'], n['size']
        data = raw[at - ROM_BASE:at - ROM_BASE + size]
        need(data.hex() == n['hex'], 'instruction bytes differ')
        samples[(at, size)] = data
        if 'literal_address' in n:
            at = n['literal_address']
            need(ROM_BASE <= at <= ROM_BASE + len(raw) - 4, 'literal outside ROM')
            data = raw[at - ROM_BASE:at - ROM_BASE + 4]
            need(int.from_bytes(data, 'little') == n['literal_value'], 'literal differs')
            samples[(at, 4)] = data
    need(saved.safe(ROOT, rom).read_bytes() == raw, 'candidate changed')
    a = prior['analysis']
    result = {'classification': 'ZERO_CONTINUATION_BYTES_NOT_ABI_PROOF',
        'candidate': copy.deepcopy(a['candidate']), 'target': TARGET, 'graph': graph,
        'sampled_ranges': [dict(address=at, hex=b.hex(), **identity(b)) for (at, _), b in sorted(samples.items())],
        'sampled_instruction_bytes': sum(n['size'] for n in graph['nodes']),
        'old_unread_targets': a['old_unread_targets'], 'old_frontier_removed': False,
        'remaining_unread_targets': sorted(set(a['remaining_unread_targets']) |
            {e['target'] for e in graph['external_edges'] if e.get('target') is not None}),
        'priority_unread_targets': [TARGET], 'nonzero_callee_return_proof_reused': True,
        'callee_return_proven': False, 'stack_integrity_proven': False,
        'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
        'ring_acquisition_accepted': False, 'release_ready': False,
        'rom_changes': 0, 'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0,
        'prior_abi_classifications_replayed': 0, 'new_graph_decodes': 1, 'candidate_reconstructions': 1}
    tests = json.loads((OUT / 'tests.json').read_bytes())
    value = {'schema_version': 1, 'task': TASK, 'source_head': before['head'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
        'analysis': result, 'source_bindings': before['source_bindings'], 'focused_tests': tests,
        'reused_successful_actions': before['reused_successful_actions'],
        'actions_observed_before_record': before['actions_before']}
    (ROOT / REPORT).write_bytes(stable(value))
    state, backlog = resume.validate(ROOT), resume.load(ROOT, BACKLOG)
    next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')['ring_zero_bytes'] = REPORT
    stop = (f'WIP: 未読0x0806DDBDだけを最大{graph["window"]}byte範囲で{len(graph["nodes"])}命令/'
        f'{result["sampled_instruction_bytes"]}byte採取し保存。zero側の返却値・SP/r4-r6/保存slotは保存byteで検証する。'
        '非0側の既証明条件付き帰還・旧18target・BP受入を保持。')
    next_step = ('保存済みpr16_ring_zero_bytes.jsonの0x0806DDBD継続だけを限定ABI検証する。'
        '候補復元/byte採取/helper全u16/非0側/既読callee/FlagSet/FlagGet/15辺分類/BPを再実行しない。'
        '全caller/全owner除外・Ring通常取得へ昇格しない。')
    state['ring_zero_bytes'] = {'path': REPORT, 'run_id': value['run_id'], 'source_head': before['head'], 'target': TARGET}
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = next_step
    state['next_action']['read_paths'] = [REPORT, SELF, PRIOR, 'content/modernization/pr16_ring_callee_abi.json',
                                       'content/modernization/pr16_ring_helper_abi.json']
    state['observed_head'] = before['head']
    state['observed_head_semantics'] = '未読zero継続一根の採取source HEAD。保存commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = f'非0側run{prior["run_id"]}とBP run34946969126成功照合。今回run{value["run_id"]}は保存時in_progress。action_requiredは成功へ読み替えない。'
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': 1, 'accepted_standalone_replays': 0,
        'scope_ja': '未読zero継続一根だけ採取。既読graph/受入済みnative再実行0。'}
    state['do_not_repeat'].append('0x0806DDBDの限定byte採取は保存済み。同一candidateを再構築/再採取せず、保存byteでABI検証する。')
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(state))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    need(identity((ROOT / CHECKPOINT).read_bytes()) == before['checkpoint'], 'BP checkpoint mutated')
    saved.bindings_fresh(ROOT, before['source_bindings'])
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / zero継続一根採取\n'
        '- Status: STOPPED / 採取保存工程完了。同一作業のABI検証へ続行。\n- Version: PR16 zero bytes checkpoint\n'
        '- Summary: ' + stop + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定MD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: 限定異常系{tests["tests_run"]} tests PASS、render/check PASS、BP checkpoint不変。task graph・最終index差分guard・diff必須。\n'
        f'- Evidence: source={before["head"]}; run={value["run_id"]}（保存時in_progress）。\n'
        '- Preserved: ROM変更/native/既読graph/受入済み再実行0。候補復元1。旧18target保持。\n'
        '- Commit: checkpointを同branchへ非force push。最終SHAはremote ref/resultで照合。\n'
        '- Network: GitHub connector/Actions、既存hash固定入力復元。直接cloneはDNS失敗。外部技術資料なし。\n'
        '- Boundary: 既存全体guard違反の前後一致/新規違反0を要求。全体guard PASS・全CI green・merge・release・baseline変更を主張しない。\n'
        '- Next: ' + next_step + '\n')
    for p in LOGS:
        need(TASK not in (ROOT / p).read_text(encoding='utf-8'), 'duplicate log')
        with (ROOT / p).open('a', encoding='utf-8') as stream:
            stream.write(entry)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], check=True)
    subprocess.run(['git', 'add', '--', *OUTPUTS], check=True)
    guard.BASE, guard.OUT, guard.ALLOWED = BASE, OUT, set((SELF, TEST, WORKFLOW, *OUTPUTS))
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    (OUT / 'summary.json').write_bytes(stable(result))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'scripts'))
    if sys.argv[1:] == ['preflight']:
        preflight()
    elif sys.argv[1:] == ['restore']:
        restore()
    elif len(sys.argv) == 3 and sys.argv[1] == 'record':
        record(sys.argv[2])
    else:
        raise SystemExit('usage: pr16_ring_zero_bytes.py preflight|restore|record <candidate>')
