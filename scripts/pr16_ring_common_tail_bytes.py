#!/usr/bin/env python3
"""未読共通末尾1根だけを採取。保存済みABI/nativeは再実行しない。"""
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
sys.path.insert(0, str(ROOT / 'scripts'))
BASE = 'ffa3fecf487a89c789f2577511ff0e68e809db5c'
BRANCH = 'codex/modernization-followup-20260908'
TASK = 'PR-P08-7-RING-COMMON-TAIL-BYTES'
SELF = 'scripts/pr16_ring_common_tail_bytes.py'
TEST = 'tests/test_pr16_ring_common_tail_bytes.py'
WORKFLOW = '.github/workflows/pr16-ring-common-tail-bytes.yml'
PRIOR = 'content/modernization/pr16_ring_zero_abi.json'
REPORT = 'content/modernization/pr16_ring_common_tail_bytes.json'
RESTORE = '.github/workflows/pr16-ring-callee-bytes.yml'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUT = ROOT / '.local/pr16-ring-common-tail-bytes'
TARGET, MAX_WINDOW, LIMIT, ROM_BASE = 0x0806DE3D, 64, 32, 0x08000000
OTHER_ROOTS = (0x0806DE51, 0x0806DE63, 0x08113889, 0x0806DD1D, 0x081138F9)
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
SAMPLES = tuple('content/modernization/pr16_ring_' + s + '_bytes.json'
                for s in ('callee', 'helper', 'nonzero', 'zero'))
SOURCES = (SELF, TEST, WORKFLOW, RESTORE, PRIOR, *SAMPLES,
    'scripts/pr16_ring_zero_bytes.py', 'scripts/pr16_ring_callee_bytes.py',
    'scripts/pr16_ring_transitive_owner.py', 'scripts/pr16_ring_compiled_owner.py',
    'scripts/pr16_ring_flagset_continuation.py', 'scripts/pr16_ring_compiled_record.py',
    'scripts/pr16_resume.py')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)
CANDIDATE = {'size': 33554432,
    'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b',
    'crc32': '3EB17B36'}
NO_PROOF = ('callee_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
            'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready')


def need(ok, text):
    if not ok:
        raise ValueError(text)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def validate_prior(prior):
    a = prior['analysis']
    need(prior['task'] == 'PR-P08-7-RING-ZERO-ABI', 'prior task differs')
    need(a['classification'] == 'ZERO_CONTINUATION_PREFIX_WITH_CONDITIONAL_STORES_NOT_RETURN_PROOF', 'prior scope differs')
    need(a['candidate'] == CANDIDATE and a['priority_unread_targets'] == [TARGET], 'target/candidate moved')
    need(a['instructions_verified'] == 54 and a['instruction_bytes_verified'] == 114, 'saved prefix differs')
    old = a['old_unread_targets']
    need(len(old) == len(set(old)) == 18, 'old frontier differs')
    need(set(a['additional_unread_targets']) == {TARGET, *OTHER_ROOTS}, 'new frontier differs')
    need(set(old) | {TARGET, *OTHER_ROOTS} == set(a['remaining_unread_targets']), 'remaining frontier differs')
    for key in (*NO_PROOF, 'old_frontier_removed', 'zero_callee_return_proven',
                'zero_callee_return_observed', 'saved_slot_preservation_proven', 'return_pointer_non_alias_proven'):
        need(a[key] is False, 'unsupported prior claim: ' + key)
    return a


def window_for(cached):
    root = TARGET & ~1
    need(root not in cached, 'root already sampled')
    end = min([root + MAX_WINDOW] + [x for x in cached if root < x < root + MAX_WINDOW])
    need(end > root and (end - root) % 2 == 0, 'invalid unread boundary')
    return end - root


def validate_graph(g, cached):
    root, window = TARGET & ~1, window_for(cached)
    need(g['entry'] == TARGET and g['window'] == window, 'wrong root/window')
    need(g['side_effects_excluded'] is False, 'unsupported side-effect claim')
    nodes = g['nodes']
    need(1 <= len(nodes) <= LIMIT, 'node budget')
    starts = [n['address'] for n in nodes]
    need(starts == sorted(set(starts)) and starts[0] == root, 'node order/root')
    need(not set(starts) & {p & ~1 for p in OTHER_ROOTS}, 'another unread root reached')
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
        need(type(n['memory_write']) is bool, 'invalid write annotation')
        if 'literal_address' in n:
            h = int.from_bytes(raw[:2], 'little')
            address = n['literal_address']
            need(h & 0xf800 == 0x4800 and address == ((at + 4) & ~3) + (h & 255) * 4, 'literal address differs')
            need(ROM_BASE <= address <= ROM_BASE + CANDIDATE['size'] - 4, 'literal outside ROM')
            need(type(n['literal_value']) is int and 0 <= n['literal_value'] <= 0xffffffff, 'literal value invalid')
        for dest in n['successors']:
            need(type(dest) is int and not dest & 1, 'unaligned successor')
            need(not root <= dest < root + window or dest in starts, 'missing successor')
    need(g['memory_write_sites'] == [n['address'] for n in nodes if n['memory_write']], 'write sites differ')
    for edge in g['external_edges']:
        need(edge['site'] in starts, 'orphan edge')
        t = edge.get('target')
        need(t is None or (type(t) is int and t & 1 and ROM_BASE <= (t & ~1) < ROM_BASE + CANDIDATE['size']), 'invalid edge')
    return occupied


def sample_ranges(raw, graph):
    samples = {}
    for n in graph['nodes']:
        at, size = n['address'], n['size']
        data = raw[at - ROM_BASE:at - ROM_BASE + size]
        need(len(data) == size and data.hex() == n['hex'], 'instruction bytes differ')
        samples[(at, size)] = data
        if 'literal_address' in n:
            at = n['literal_address']
            need(ROM_BASE <= at <= ROM_BASE + len(raw) - 4, 'literal outside candidate')
            data = raw[at - ROM_BASE:at - ROM_BASE + 4]
            need(int.from_bytes(data, 'little') == n['literal_value'], 'literal differs')
            samples[(at, 4)] = data
    return [dict(address=at, hex=b.hex(), **identity(b)) for (at, _), b in sorted(samples.items())]


def analysis(prior, graph, ranges):
    a = validate_prior(prior)
    external = {e['target'] for e in graph['external_edges'] if e.get('target') is not None}
    return {'classification': 'COMMON_TAIL_BYTES_NOT_ABI_PROOF',
        'candidate': copy.deepcopy(CANDIDATE), 'target': TARGET, 'graph': graph,
        'sampled_ranges': ranges, 'sampled_instruction_bytes': sum(n['size'] for n in graph['nodes']),
        'old_unread_targets': copy.deepcopy(a['old_unread_targets']), 'old_frontier_removed': False,
        'remaining_unread_targets': sorted(set(a['remaining_unread_targets']) | external),
        'priority_unread_targets': [TARGET], 'other_unread_roots_preserved': list(OTHER_ROOTS),
        'zero_prefix_abi_result_reused': True, 'zero_callee_return_proven': False,
        'zero_callee_return_observed': False, 'saved_slot_preservation_proven': False,
        'return_pointer_non_alias_proven': False, **dict.fromkeys(NO_PROOF, False),
        'rom_changes': 0, 'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0,
        'prior_abi_classifications_replayed': 0, 'new_graph_decodes': 1,
        'candidate_reconstructions': 1}


def inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_callee_bytes as previous
    prior = json.loads((ROOT / PRIOR).read_bytes())
    saved.bindings_fresh(ROOT, prior['source_bindings'])
    validate_prior(prior)
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
    active = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&status=in_progress&per_page=100')['workflow_runs']
    queued = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&status=queued&per_page=100')['workflow_runs']
    need(not [r for r in active + queued if r['id'] != int(os.environ['GITHUB_RUN_ID']) and '/pr16-ring-' in r['path']], 'another Ring run active')
    suite = unittest.defaultTestLoader.discover('tests', pattern=Path(TEST).name)
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
             'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'] and tests['tests_run'] >= 20, 'focused tests failed')
    before = {'head': head, 'pr': {'number': 16, 'state': pr['state'], 'draft': pr['draft'], 'merged': pr['merged']},
        'unread_window': window_for(cached), 'reused_successful_actions': reused,
        'actions_before': [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs],
        'checkpoint': identity((ROOT / CHECKPOINT).read_bytes()),
        'source_bindings': {p: identity((ROOT / p).read_bytes()) for p in SOURCES}}
    (OUT / 'preflight.json').write_bytes(stable(before))
    print(json.dumps(before, ensure_ascii=False))


def restore():
    import pr16_ring_zero_bytes as base
    base.OUT = OUT
    base.restore()


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
    result = analysis(prior, graph, sample_ranges(raw, graph))
    need(saved.safe(ROOT, rom).read_bytes() == raw, 'candidate changed')
    tests = json.loads((OUT / 'tests.json').read_bytes())
    value = {'schema_version': 1, 'task': TASK, 'source_head': before['head'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
        'analysis': result, 'source_bindings': before['source_bindings'], 'focused_tests': tests,
        'reused_successful_actions': before['reused_successful_actions'],
        'actions_observed_before_record': before['actions_before']}
    (ROOT / REPORT).write_bytes(stable(value))
    state, backlog = resume.validate(ROOT), resume.load(ROOT, BACKLOG)
    next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')['ring_common_tail_bytes'] = REPORT
    stop = (f'未読共通末尾0x0806DE3Dの1根だけを最大{graph["window"]}byte範囲で{len(graph["nodes"])}命令/'
        f'{result["sampled_instruction_bytes"]}byte採取・保存。採取工程は完了。返却pointer生成/復元のABIは保存byteで検証する。'
        'zero54命令の限定ABI成功run35002458426を再利用。0x0806DE51/0x0806DE63と外部call3本、'
        '旧18target、保存slot/返却pointer非aliasの未証明を保持。BP受入は不変。')
    next_step = ('保存済みpr16_ring_common_tail_bytes.jsonの共通末尾だけを限定ABI検証する。'
        '同じcandidateの復元/共通末尾再採取、zero54命令/helper全u16/非0側/callee prefix/FlagSet/FlagGet/15辺分類/BPを単独再実行しない。'
        '0x0806DE51/0x0806DE63と外部call0x08113889/0x0806DD1D/0x081138F9は未解決で保持。'
        '局所復元をcallee全体の帰還/保存slot不変/全owner除外/Ring通常取得受入へ昇格しない。')
    state['ring_common_tail_bytes'] = {'path': REPORT, 'run_id': value['run_id'], 'source_head': before['head'], 'target': TARGET}
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = next_step
    state['next_action']['read_paths'] = [REPORT, SELF, PRIOR,
        'content/modernization/pr16_ring_callee_abi.json', 'content/modernization/pr16_ring_helper_abi.json']
    state['observed_head'] = before['head']
    state['observed_head_semantics'] = '未読共通末尾1根の採取source HEAD。完了commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = f'zero限定ABI run{prior["run_id"]}とBP run34946969126成功照合。今回run{value["run_id"]}は保存時in_progress。action_requiredは成功へ読み替えない。'
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': 1, 'accepted_standalone_replays': 0,
        'scope_ja': '未読共通末尾1根の限定採取完了。既読graph/受入済みnative再実行0。'}
    state['do_not_repeat'].append('0x0806DE3Dの共通末尾1根は採取保存済み。同一candidateを復元/再採取せず、保存byteのABI検証へ進む。')
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(state))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    need(identity((ROOT / CHECKPOINT).read_bytes()) == before['checkpoint'], 'BP checkpoint mutated')
    saved.bindings_fresh(ROOT, before['source_bindings'])
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 未読共通末尾1根の限定採取\n'
        '- Status: DONE / 限定採取工程。Ring通常取得・ABI全体の受入ではない。\n- Version: PR16 common-tail bytes\n'
        '- Summary: ' + stop + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定MD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: 限定異常系{tests["tests_run"]} tests PASS、candidate全体SHA/size/CRC一致、既読命令重複0、render/check PASS、BP checkpoint不変。task graph・最終index差分guard・diff必須。\n'
        f'- Evidence: source={before["head"]}; run={value["run_id"]}（保存時in_progress）。\n'
        '- Preserved: ROM変更/native/既読graph/受入済み再実行0。候補復元1。旧18targetと別の未読5入口保持。\n'
        '- Commit: 完了条件PASS後、同branchへ非force push。最終SHAはremote ref/recorded-result.jsonで照合。\n'
        '- Network: GitHub connector/Actions、既存hash固定入力復元。直接cloneはDNS解決失敗。外部技術資料なし。\n'
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
    if sys.argv[1:] == ['preflight']:
        preflight()
    elif sys.argv[1:] == ['restore']:
        restore()
    elif len(sys.argv) == 3 and sys.argv[1] == 'record':
        record(sys.argv[2])
    else:
        raise SystemExit('usage: pr16_ring_common_tail_bytes.py preflight|restore|record <candidate>')
