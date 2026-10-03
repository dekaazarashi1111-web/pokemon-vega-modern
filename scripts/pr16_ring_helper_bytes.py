#!/usr/bin/env python3
"""未読helper一根を採取し保存。既読calleeやnative受入は再実行しない。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_flagset_continuation as saved
import pr16_ring_callee_bytes as prior_bytes

BASE = 'ce9e2e3532f4f0a723ad2d74001808a2e4411869'
TASK = 'PR-P08-7-RING-HELPER-BYTES'
SELF = 'scripts/pr16_ring_helper_bytes.py'
TEST = 'tests/test_pr16_ring_helper_bytes.py'
WORKFLOW = '.github/workflows/pr16-ring-helper-bytes.yml'
RESTORE = '.github/workflows/pr16-ring-callee-bytes.yml'
PRIOR = 'content/modernization/pr16_ring_callee_abi.json'
REPORT = 'content/modernization/pr16_ring_helper_bytes.json'
OUT = ROOT / '.local/pr16-ring-helper-bytes'
TARGET, WINDOW, LIMIT = 0x091281D1, 1024, 512
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
SOURCES = (SELF, TEST, WORKFLOW, RESTORE, PRIOR, prior_bytes.REPORT,
           prior_bytes.FRAME, saved.REPORT, saved.SELF, prior_bytes.SELF,
           'scripts/pr16_ring_transitive_owner.py', 'scripts/pr16_resume.py')
OUTPUTS = (REPORT, saved.STATE, saved.DOC, saved.BACKLOG, *saved.LOGS)
need, stable, identity = saved.need, saved.stable, saved.identity


def inputs():
    prior = json.loads((ROOT / PRIOR).read_bytes())
    saved.bindings_fresh(ROOT, prior['source_bindings'])
    a = prior['analysis']
    need(a['classification'] == 'LIVE_FRAME_CALLEE_PREFIX_NOT_RETURN_PROOF', 'scope differs')
    need(a['candidate'] == saved.CANDIDATE and a['priority_unread_targets'] == [TARGET], 'target differs')
    need(a['helper']['target'] == TARGET and a['helper']['return_proven'] is False, 'helper already proven')
    need(len(a['old_unread_targets']) == 18 and a['old_frontier_removed'] is False, 'old ledger differs')
    _, cached = prior_bytes.read_prior()
    sample = json.loads((ROOT / prior_bytes.REPORT).read_bytes())
    for n in sample['analysis']['graph']['nodes']:
        cached.update(range(n['address'], n['address'] + n['size']))
    need((TARGET & ~1) not in cached, 'helper already sampled')
    return prior, cached


def validate_graph(g, cached):
    need(g['entry'] == TARGET and g['window'] == WINDOW, 'wrong root/window')
    need(g['side_effects_excluded'] is False, 'unsupported side-effect claim')
    nodes = g['nodes']
    need(1 <= len(nodes) <= LIMIT, 'node budget')
    starts = [n['address'] for n in nodes]
    need(starts == sorted(set(starts)) and starts[0] == TARGET & ~1, 'node order')
    occupied = set()
    for n in nodes:
        at, size = n['address'], n['size']
        need(type(at) is int and not at & 1 and size in (2, 4), 'invalid instruction')
        need(TARGET & ~1 <= at and at + size <= (TARGET & ~1) + WINDOW, 'escaped window')
        span = set(range(at, at + size))
        need(not span & (cached | occupied), 'overlap/previous code rescan')
        occupied |= span
        raw = bytes.fromhex(n['hex'])
        need(len(raw) == size and n['kind'] in ('ordinary', 'call', 'jump', 'conditional', 'indirect', 'return'), 'bad opcode record')
        if 'literal_address' in n:
            w = int.from_bytes(raw[:2], 'little')
            need(w & 0xf800 == 0x4800 and n['literal_address'] == ((at + 4) & ~3) + (w & 255) * 4, 'bad literal')
    need(g['memory_write_sites'] == [n['address'] for n in nodes if n['memory_write']], 'write sites differ')
    for e in g['external_edges']:
        need(e['site'] in starts, 'orphan edge')
        t = e.get('target')
        need(t is None or (type(t) is int and t & 1 and saved.ROM_BASE <= (t & ~1) < saved.ROM_BASE + saved.CANDIDATE['size']), 'bad target')


def collect(raw, prior, cached, decode):
    saved.candidate_identity(raw)
    g = decode(raw, TARGET, window=WINDOW, limit=LIMIT)
    validate_graph(g, cached)
    samples = {}
    for n in g['nodes']:
        at, size = n['address'], n['size']
        data = raw[at - saved.ROM_BASE:at - saved.ROM_BASE + size]
        need(data.hex() == n['hex'], 'instruction bytes differ')
        samples[(at, size)] = data
        if 'literal_address' in n:
            at = n['literal_address']
            need(saved.ROM_BASE <= at <= saved.ROM_BASE + len(raw) - 4, 'literal outside ROM')
            data = raw[at - saved.ROM_BASE:at - saved.ROM_BASE + 4]
            need(int.from_bytes(data, 'little') == n['literal_value'], 'literal bytes differ')
            samples[(at, 4)] = data
    a = prior['analysis']
    external = sorted({e['target'] for e in g['external_edges'] if e.get('target') is not None})
    return {'classification': 'ONE_HELPER_BYTES_NOT_RETURN_PROOF', 'candidate': copy.deepcopy(saved.CANDIDATE),
        'target': TARGET, 'graph': g,
        'sampled_ranges': [dict(address=at, hex=b.hex(), **identity(b)) for (at, _), b in sorted(samples.items())],
        'sampled_instruction_bytes': sum(n['size'] for n in g['nodes']),
        'old_unread_targets': copy.deepcopy(a['old_unread_targets']),
        'prior_additional_unread_targets': copy.deepcopy(a['additional_unread_targets']),
        'external_targets': external, 'old_frontier_removed': False,
        'remaining_unread_targets': sorted(set(a['remaining_unread_targets']) | set(external)),
        'helper_return_proven': False, 'stack_integrity_proven': False,
        'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
        'ring_acquisition_accepted': False, 'release_ready': False,
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
         and GAP in state['remaining_physical_gap_ids'], 'BP boundary differs')
    row = next(r for r in resume.load(ROOT, saved.BACKLOG)['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(GAP in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][GAP] is None, 'Ring owner moved')
    prior, _ = inputs()
    reused = []
    for rid, source in ((prior['run_id'], prior['source_head']), (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        r = saved.api('actions/runs/' + str(rid))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == source, 'prior Actions differs')
        reused.append({k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    runs = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    need(not [r for r in runs if r['status'] != 'completed' and r['id'] != int(os.environ['GITHUB_RUN_ID'])
              and r['name'].startswith('pr16-ring-')], 'another Ring run active')
    before = {'head': head, 'reused_successful_actions': reused,
        'actions_before': [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs],
        'checkpoint': identity((ROOT / saved.CHECKPOINT).read_bytes()),
        'source_bindings': {p: identity((ROOT / p).read_bytes()) for p in SOURCES}}
    (OUT / 'preflight.json').write_bytes(stable(before))
    print(json.dumps(before))


def restore():
    """hash照合済み既存workflowのcandidate復元stepのみ再利用。旧採取stepは実行しない。"""
    before = json.loads((OUT / 'preflight.json').read_bytes())
    saved.bindings_fresh(ROOT, before['source_bindings'])
    text = (ROOT / RESTORE).read_text(encoding='utf-8')
    marker = '      - name: 未読byte取得用の同一hash candidateのみ復元\n'
    need(text.count(marker) == 1, 'restore step ambiguous')
    block = text.split(marker, 1)[1].split('      - name:', 1)[0]
    lines = block.split('        run: |\n', 1)[1].splitlines()
    need(all(not line or line.startswith('          ') for line in lines), 'restore indentation')
    command = '\n'.join(line[10:] if line else '' for line in lines)
    subprocess.run(['bash', '-euo', 'pipefail', '-c', command], cwd=ROOT, check=True)


def record(rom):
    import pr16_resume as resume
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_compiled_record as guard
    before = json.loads((OUT / 'preflight.json').read_bytes())
    need(before['head'] == os.environ['GITHUB_SHA'], 'preflight HEAD differs')
    saved.bindings_fresh(ROOT, before['source_bindings'])
    need(not (ROOT / REPORT).exists(), 'already sampled')
    prior, cached = inputs()
    raw = saved.safe(ROOT, rom).read_bytes()
    result = collect(raw, prior, cached, decoder.native_graph)
    need(saved.safe(ROOT, rom).read_bytes() == raw, 'candidate changed')
    value = {'schema_version': 1, 'task': TASK, 'source_head': before['head'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
        'analysis': result, 'source_bindings': before['source_bindings'],
        'reused_successful_actions': before['reused_successful_actions'],
        'actions_observed_before_record': before['actions_before']}
    (OUT / 'audit.json').write_bytes(stable(value))
    suite = unittest.TestSuite()
    for pattern in ('test_pr16_ring_helper_bytes.py', 'test_pr16_resume.py'):
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
    next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')['ring_helper_bytes'] = REPORT
    stop = (f'WIP: 未読helper 0x091281D1だけを同一candidateから{len(result["graph"]["nodes"])}命令/'
        f'{result["sampled_instruction_bytes"]}bytes採取して保存。return/SP/r4-r6/保存slotの限定検証は保存byteから続行。'
        '旧18targetと0x090970F7/0x0806DDBDの未読境界・BP受入を保持。')
    next_step = ('保存済みpr16_ring_helper_bytes.jsonだけからhelper 0x091281D1のreturn値・SP/r4-r6/保存slotへの影響を限定検証する。'
        'candidate/helper/callee/FlagSet/FlagGetの再採取、15辺再分類、BP再実行をしない。'
        '0x090970F7/0x0806DDBDは未読のまま保持し全owner除外やRing受入へ昇格しない。')
    state['ring_helper_bytes'] = {'path': REPORT, 'source_head': before['head'], 'run_id': value['run_id'], 'target': TARGET, 'ring_acquisition_accepted': False}
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = next_step
    state['next_action']['read_paths'] = [REPORT, SELF, PRIOR, prior_bytes.REPORT, prior_bytes.FRAME]
    state['observed_head'] = before['head']
    state['observed_head_semantics'] = '未読helper一根を採取したsource HEAD。完了commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = f'前回ABI run{prior["run_id"]}とBP run34946969126成功照合。今回run{value["run_id"]}は保存時in_progress。action_requiredは成功へ読み替えない。'
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0, 'candidate_reconstructions': 1,
        'accepted_standalone_replays': 0, 'scope_ja': '未読helper一根のみ採取。既読graph/受入済みnative再実行0。'}
    state['do_not_repeat'].append('0x091281D1のhelper byte採取は保存済み。同一candidateから再採取せず、保存byteでreturn/stackを限定検証する。')
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / saved.STATE).write_bytes(stable(state))
    (ROOT / saved.BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    need(identity((ROOT / saved.CHECKPOINT).read_bytes()) == before['checkpoint'], 'BP checkpoint mutated')
    saved.bindings_fresh(ROOT, before['source_bindings'])
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 未読helper限定採取checkpoint\n'
        '- Status: STOPPED / 採取保存工程完了、同一作業のABI検証へ続行。\n- Version: PR16 helper bytes checkpoint\n'
        '- Summary: ' + stop + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定MD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: helper異常系/固定resume {tests["tests_run"]} tests PASS、render/check PASS、BP checkpoint不変。task graph・最終index差分guard・diff必須。\n'
        f'- Evidence: source={before["head"]}; run={value["run_id"]}（保存時in_progress）。\n'
        '- Preserved: ROM変更/native/既読graph再scan/15辺再分類/受入済み再実行0。同一candidate復元1。旧18target台帳を保持。\n'
        '- Commit: checkpointを同branchへ非force push、最終SHAはremote ref/resultで照合。\n'
        '- Network: GitHub connector/Actions、既存hash固定入力復元。直接cloneはDNS失敗。外部技術資料なし。\n'
        '- Boundary: 既存全体guard違反前後一致/新規違反0を要求。全体guard PASSや全CI greenを主張しない。merge/release/baseline変更なし。\n'
        '- Next: ' + next_step + '\n')
    for p in saved.LOGS:
        need(TASK not in (ROOT / p).read_text(encoding='utf-8'), 'duplicate log')
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
    elif sys.argv[1:] == ['restore']:
        restore()
    elif len(sys.argv) == 3 and sys.argv[1] == 'record':
        record(sys.argv[2])
    else:
        raise SystemExit('usage: pr16_ring_helper_bytes.py preflight|restore|record <candidate>')
