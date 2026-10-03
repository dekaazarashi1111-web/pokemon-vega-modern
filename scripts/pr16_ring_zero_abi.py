#!/usr/bin/env python3
"""保存zero継続54命令の限定ABI監査。外部call/帰還/保存slot不変を過大主張しない。"""
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
import pr16_ring_zero_model as model
import pr16_ring_zero_bytes as base

need, stable, identity = base.need, base.stable, base.identity
BASE = '7d5e22c800dd84c95c7fa515578948a2494b128a'
TASK = 'PR-P08-7-RING-ZERO-ABI'
SELF, MODEL, TEST = 'scripts/pr16_ring_zero_abi.py', 'scripts/pr16_ring_zero_model.py', 'tests/test_pr16_ring_zero_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-zero-abi.yml'
SAMPLE, NONZERO = base.REPORT, base.PRIOR
HELPER, CALLER = 'content/modernization/pr16_ring_helper_abi.json', 'content/modernization/pr16_ring_callee_abi.json'
REPORT = 'content/modernization/pr16_ring_zero_abi.json'
STATE, DOC, BACKLOG, CHECKPOINT, LOGS = base.STATE, base.DOC, base.BACKLOG, base.CHECKPOINT, base.LOGS
OUT = ROOT / '.local/pr16-ring-zero-abi'
SOURCES = (SELF, MODEL, TEST, WORKFLOW, SAMPLE, NONZERO, HELPER, CALLER, base.SELF,
           'scripts/pr16_ring_flagset_continuation.py', 'scripts/pr16_ring_compiled_record.py', 'scripts/pr16_resume.py')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)
CANDIDATE = {'size': 33554432, 'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b', 'crc32': '3EB17B36'}
CODE_HASH = 'd17154269e70a461dbbe49b7394727099632768c837a93907272a51a247bc43b'
LITERALS = {0x0806DDDC: 0x3FFF, 0x0806DDE0: model.SELECTOR, 0x0806DE08: model.SAVE_PTR,
            0x0806DE48: model.HALFWORD, 0x0806DE4C: model.SAVE_PTR}
ZERO_TAIL, HIGH_TAIL, COMMON_TAIL = 0x0806DE63, 0x0806DE51, 0x0806DE3D
REFERENCE = 'https://sourceware.org/cgen/gen-doc/arm-thumb-insn.html'
STOP = ('保存zero継続0x0806DDBDの54命令/114byteを限定ABI検証。helper結果は再実行せず、'
        'zero域51456入力を0→未読0x0806DE63、1..2303→selector経路、16384..65535→未読0x0806DE51へ分類。'
        'selector=1/2は未解決外部call3本と条件付きSTRB/STRHを含む。共通末尾0x0806DE3Dも未読。'
        '保存命令にPOP/復元はなく局所SP変化0、FlagSet基準-24のframeが残る。'
        '書込み先と保存slotのalias反例を保持し、zero/callee全体の帰還・保存slot不変・全owner除外は未証明。旧18target・BP受入を保持。')
NEXT = ('次は新規未読0x0806DE3Dだけを優先し、共通返却pointer生成/復元区間を限定採取する。'
        '0x0806DE51/0x0806DE63と外部call0x08113889/0x0806DD1D/0x081138F9は未解決で保持。'
        '保存zero54命令、非0側、helper全u16、callee prefix、FlagSet/FlagGet、15辺分類、BPを再採取/単独再実行しない。'
        '新規未読targetの採取だけを進め、仮想call契約のモデルをnative帰還/保存slot不変/Ring受入へ昇格しない。')


def audit_sample(sample):
    a = sample['analysis']
    need(a['classification'] == 'ZERO_CONTINUATION_BYTES_NOT_ABI_PROOF' and a['candidate'] == CANDIDATE, 'sample scope')
    need(a['target'] == model.ENTRY and a['old_frontier_removed'] is False, 'sample target/frontier')
    for key in ('callee_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
                'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
        need(a[key] is False, 'sample overclaim: ' + key)
    g = a['graph']
    need(g['entry'] == model.ENTRY and g['window'] == 128 and g['side_effects_excluded'] is False, 'sample boundary')
    rows = g['nodes']
    need(len(rows) == 54 and sum(n['size'] for n in rows) == a['sampled_instruction_bytes'] == 114, 'code budget')
    digest = hashlib.sha256(json.dumps([(n['address'], n['hex']) for n in rows], separators=(',', ':')).encode()).hexdigest()
    need(digest == CODE_HASH, 'saved code differs')
    nodes, literals, samples, writes, edges = {}, {}, {}, [], []
    root, end = model.ENTRY & ~1, (model.ENTRY & ~1) + 128
    for n in rows:
        at, raw = n['address'], bytes.fromhex(n['hex'])
        need(len(raw) == n['size'] and len(raw) in (2, 4), 'instruction width')
        nodes[at] = raw
        samples[(at, len(raw))] = raw
        h, after = int.from_bytes(raw[:2], 'little'), at + len(raw)
        write = h & 0xf800 in (0x7000, 0x8000)
        need(n['memory_write'] is write, 'write annotation')
        if write: writes.append(at)
        if len(raw) == 4:
            target, kind = model.bl_target(at, raw), 'call'
            need(n['target'] == target & ~1 and n['successors'] == [after], 'call metadata')
            edges.append((at, kind, target))
        elif h & 0xf000 == 0xd000 or h & 0xf800 == 0xe000:
            target = model.branch_target(at, h)
            kind = 'conditional' if h & 0xf000 == 0xd000 else 'jump'
            successors = ([after] if kind == 'conditional' else []) + ([target] if root <= target < end else [])
            need(n['target'] == target and n['successors'] == sorted(set(successors)), 'branch metadata')
            if not root <= target < end: edges.append((at, kind, target | 1))
        else:
            kind = 'ordinary'
            need(n['successors'] == [after], 'ordinary successor')
            if after >= end: edges.append((at, 'window_fallthrough', after | 1))
        need(n['kind'] == kind, 'opcode classification')
        if h & 0xf800 == 0x4800:
            address = ((at + 4) & ~3) + (h & 255) * 4
            need(n['literal_address'] == address and n['literal_value'] == LITERALS[address], 'literal metadata')
            literals[address] = n['literal_value']
            samples[(address, 4)] = n['literal_value'].to_bytes(4, 'little')
        else:
            need('literal_address' not in n and 'literal_value' not in n, 'unexpected literal')
    need(literals == LITERALS and writes == g['memory_write_sites'] == [0x0806DE02, 0x0806DE1E], 'effects/literals')
    need([(e['site'], e['kind'], e['target']) for e in g['external_edges']] == edges, 'external frontier')
    expected = [dict(address=at, hex=raw.hex(), **identity(raw)) for (at, _), raw in sorted(samples.items())]
    need(a['sampled_ranges'] == expected, 'sample byte/hash binding')
    return nodes, literals, edges


def premises(sample, nonzero, helper, caller):
    s, n, h, c = (v['analysis'] for v in (sample, nonzero, helper, caller))
    old = s['old_unread_targets']
    need(len(old) == len(set(old)) == 18 and n['old_unread_targets'] == h['old_unread_targets'] == c['old_unread_targets'] == old, 'old frontier differs')
    for a in (n, h, c):
        need(a['candidate'] == CANDIDATE and a['old_frontier_removed'] is False, 'prior scope')
        for key in ('callee_return_proven', 'stack_integrity_proven', 'all_callers_resolved', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
            need(a[key] is False, 'prior overclaim')
    need(n['nonzero_callee_return_proven'] is True and n['nonzero_callee_return_observed'] is False
         and n['additional_unread_targets'] == n['priority_unread_targets'] == [model.ENTRY], 'nonzero premise')
    for key in ('helper_return_proven', 'helper_sp_preserved', 'helper_r4_r11_preserved',
                'helper_lr_preserved', 'helper_memory_unchanged', 'helper_saved_slots_unchanged'):
        need(h[key] is True, 'helper premise: ' + key)
    need(h['helper_return_observed'] is False and h['verification']['zero_returns'] == 51456
         and h['verification']['return_thumb'] == model.HELPER_LR, 'helper boundary')
    need(h['return_regions'][2] == {'input_regions': [[0, 2303], [16384, 65535]], 'expression': '0', 'output': 0}, 'zero domain')
    p = c['prefix']
    need(p['argument_r0_r4_r6'] == 'entry_r0 & 0xffff' and p['argument_r5'] == '(entry_r0 & 0xffff) << 16', 'arguments')
    need(p['flagset_entry_sp_offset_before_helper'] == h['caller_frame_after_helper']['flagset_entry_sp_offset'] == -24
         and p['callee_entry_lr_value'] == 0x0806DE81, 'frame/return')
    slots = [{'register': r, 'callee_entry_sp_offset': -16 + i*4,
              'flagset_entry_sp_offset': -24 + i*4} for i, r in enumerate((4, 5, 6, 14))]
    need(p['saved_register_slots'] == h['caller_frame_after_helper']['saved_register_slots'] == slots
         and p['inherited_flagset_saved_offsets'] == [-8, -4], 'saved slots')
    need(c['conditional_exits'][1]['target'] == model.ENTRY
         and c['conditional_exits'][1]['r0_role'].startswith('literal Thumb code destination'), 'zero entry r0')
    return old


def verify_program(nodes, literals):
    covered, dispatch, selectors = set(), {'zero': 0, 'low': 0, 'high': 0}, {}
    def run(ident, selector=0, returns=None):
        r = model.execute(nodes, literals, ident, selector, returns)
        covered.update(r['coverage'])
        need(r['registers'][13] == -24 and [r['registers'][x] for x in (4, 5, 6)] == [ident, ident << 16, ident], 'local frame/clobber')
        return r
    for ident in list(range(2304)) + list(range(16384, 65536)):
        r = run(ident)
        key, boundary = ('zero', ZERO_TAIL) if ident == 0 else (('low', COMMON_TAIL) if ident < 2304 else ('high', HIGH_TAIL))
        need(r['boundary'] == boundary and not r['writes'] and not r['calls'], 'dispatch')
        if ident == 0: need(r['registers'][0] == 0 and not r['reads'], 'zero value')
        if key == 'high': need(r['registers'][0] == 0x3fff and not r['reads'], 'high boundary r0')
        if key == 'low': need(r['registers'][0] == model.SAVE_PTR and r['registers'][1] == ident >> 3, 'common prefix registers')
        dispatch[key] += 1
    for selector in range(256):
        r = run(1, selector)
        expected = model.CALL1 if selector == 1 else model.CALL2 if selector == 2 else COMMON_TAIL
        need(r['boundary'] == expected, 'selector partition')
        selectors[str(selector)] = expected
    conditional_cases = 0
    for ident in range(1, 2304):
        off = 0xee0 + (ident >> 3)
        for selector, returns in ((1, {model.CALL1: 0}), (1, {model.CALL1: ('call1_nonzero', 0)}),
                                  (2, {model.CALL2: 0}), (2, {model.CALL2: 256}),
                                  (2, {model.CALL2: 1}), (2, {model.CALL2: 257})):
            r = run(ident, selector, returns)
            conditional_cases += 1
            if selector == 1:
                need(r['calls'][0]['args'][:2] == [1, ident], 'call1 arguments')
                expected = [] if returns[model.CALL1] == 0 else [{'site': 0x0806DE02,
                    'address': ('save_base', off), 'width': 1,
                    'value': {'read_width': 1, 'address': ('call1_nonzero', 0)}}]
                need(r['writes'] == expected and r['boundary'] == COMMON_TAIL, 'mode1 effects')
            else:
                need(r['calls'][0]['args'][:2] == [ident, 0], 'call2 arguments')
                succeeds = returns[model.CALL2] & 255 == 1
                expected = [{'site': 0x0806DE1E, 'address': model.HALFWORD, 'width': 2, 'value': ident}] if succeeds else []
                need(r['writes'] == expected and r['boundary'] == (model.CALL3 if succeeds else COMMON_TAIL), 'mode2 effects')
                if succeeds:
                    need(r['calls'][-1]['args'] == [1, ident, {'read_width': 1, 'address': ('save_base', off)}]
                         and r['calls'][-1]['return_assumed'] is False, 'call3 boundary')
    need(covered == set(nodes) and dispatch == {'zero': 1, 'low': 2303, 'high': 49152}, 'coverage/domain')
    return {'new_zero_dispatch_inputs_checked': sum(dispatch.values()), 'dispatch_counts': dispatch,
        'selector_values_checked': len(selectors), 'conditional_model_cases': conditional_cases,
        'instructions_covered': len(covered), 'helper_domain_reexecuted': False,
        'external_callees_executed': False, 'external_returns_are_explicit_assumptions_not_observations': True}


def analyze(sample, nonzero, helper, caller):
    nodes, literals, edges = audit_sample(sample)
    old = premises(sample, nonzero, helper, caller)
    verified = verify_program(nodes, literals)
    targets = sorted({e[2] for e in edges})
    counterexamples = [
        {'condition': 'selector=1, call1 returns a readable nonzero pointer with otherwise preserving ABI',
         'id': 1, 'save_base_value': 0x0200F120, 'flagset_entry_sp': 0x02010018,
         'write_address': 0x02010000, 'write_width': 1, 'saved_slot_offset': -24},
        {'condition': 'selector=2, low byte of call2 result is 1 with otherwise preserving ABI',
         'id': 1, 'flagset_entry_sp': model.HALFWORD + 24,
         'write_address': model.HALFWORD, 'write_width': 2, 'saved_slot_offset': -24}]
    need((counterexamples[0]['save_base_value'] + 0xee0) & model.MASK == counterexamples[0]['write_address'], 'alias arithmetic')
    need(all(c['flagset_entry_sp'] % 4 == 0 and c['flagset_entry_sp'] - 24 == c['write_address'] for c in counterexamples), 'alias slot')
    return {'classification': 'ZERO_CONTINUATION_PREFIX_WITH_CONDITIONAL_STORES_NOT_RETURN_PROOF',
        'candidate': copy.deepcopy(CANDIDATE), 'target': model.ENTRY,
        'instructions_verified': len(nodes), 'instruction_bytes_verified': 114, 'literal_bytes_verified': 20,
        'verification': verified,
        'zero_input_to_epilogue': {'input': 0, 'boundary': ZERO_TAIL, 'r0': 0, 'callee_return_proven': False},
        'high_input_to_special_path': {'input_first': 16384, 'input_last': 65535, 'boundary': HIGH_TAIL, 'r0': 16383},
        'low_input_scope': {'input_first': 1, 'input_last': 2303, 'selector_address': model.SELECTOR, 'selector_width': 1,
            'selector_1_call': model.CALL1, 'selector_2_call': model.CALL2,
            'other_selectors': [[0, 0], [3, 255]], 'common_boundary': COMMON_TAIL,
            'common_boundary_registers_under_preserving_call_assumption': {'r0': model.SAVE_PTR, 'r1': 'id >> 3'}},
        'conditional_stores': [
            {'site': 0x0806DE02, 'width': 1, 'condition': 'selector=1 and call1 returns p!=0, with preserving ABI/readable memory',
             'destination': '(mem32[0x03005048] + 0xEE0 + (id >> 3)) mod 2^32', 'value': 'mem8[p]'},
            {'site': 0x0806DE1E, 'width': 2, 'condition': 'selector=2 and (call2_result & 0xff)==1, with preserving ABI',
             'destination': '0x030050BC', 'value': 'id'}],
        'external_calls': [{'site': 0x0806DDE8, 'target': model.CALL1, 'args': ['1', 'id'], 'return_thumb': 0x0806DDED},
            {'site': 0x0806DE10, 'target': model.CALL2, 'args': ['id', '0'], 'return_thumb': 0x0806DE15},
            {'site': 0x0806DE34, 'target': model.CALL3, 'args': ['1', 'id', 'mem8[mem32[0x03005048]+0xEE0+(id>>3)]'], 'return_thumb': 0x0806DE39}],
        'local_stack_operations': 0, 'local_sp_delta': 0, 'flagset_entry_sp_offset_at_boundaries': -24,
        'local_r4_r5_r6_restoration_instructions': 0, 'saved_slots_consumed_by_local_instructions': [],
        'conditional_frame_assumption': 'External returns must preserve SP/r4-r11 and slots; sampled stores must not alias slots. Neither premise is established for all paths.',
        'saved_slot_preservation_proven': False, 'saved_slot_alias_counterexamples': counterexamples,
        'counterexamples_are_hypothetical_not_observed_corruption': True,
        'zero_callee_return_proven': False, 'zero_callee_return_observed': False,
        'callee_return_proven': False, 'stack_integrity_proven': False, 'return_pointer_non_alias_proven': False,
        'nonzero_callee_return_proof_reused': True, 'sampled_root_still_transitively_unresolved': model.ENTRY,
        'old_unread_targets': old, 'old_frontier_removed': False, 'additional_unread_targets': targets,
        'priority_unread_targets': [COMMON_TAIL], 'remaining_unread_targets': sorted(set(old) | set(targets)),
        'all_callers_resolved': False, 'all_runtime_owners_excluded': False, 'ring_acquisition_accepted': False,
        'release_ready': False, 'rom_changes': 0, 'new_emulator_processes': 0, 'candidate_reconstructions': 0,
        'new_graph_decodes': 0, 'prior_abi_classifications_replayed': 0, 'accepted_native_cases_replayed': 0}


def run():
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_compiled_record as guard
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT / REPORT).exists(), 'already recorded: reuse proof')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'HEAD differs')
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], check=True)
    pr = saved.api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head
         and pr['head']['ref'] == base.BRANCH and pr['head']['repo']['full_name'] == os.environ['GITHUB_REPOSITORY'], 'PR boundary')
    state, backlog = resume.validate(ROOT), resume.load(ROOT, BACKLOG)
    checkpoint = identity((ROOT / CHECKPOINT).read_bytes())
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True
         and base.GAP in state['remaining_physical_gap_ids'] and base.GAP in row['remaining_supply_gap_ids']
         and row['selected_supply_entrypoints'][base.GAP] is None, 'acceptance boundary')
    values = [json.loads((ROOT / p).read_bytes()) for p in (SAMPLE, NONZERO, HELPER, CALLER)]
    for v in values: saved.bindings_fresh(ROOT, v['source_bindings'])
    runs = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    need(not [r for r in runs if r['status'] != 'completed' and r['id'] != int(os.environ['GITHUB_RUN_ID'])
              and '/pr16-ring-' in r['path']], 'another Ring run active')
    reused = []
    for v in values[:2]:
        r = saved.api('actions/runs/' + str(v['run_id']))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == v['source_head'], 'prior run')
        reused.append({k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    bindings = {p: identity((ROOT / p).read_bytes()) for p in SOURCES}
    suite = unittest.defaultTestLoader.discover('tests', pattern='test_pr16_ring_zero_abi.py')
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
             'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'] and tests['tests_run'] >= 20, 'focused tests failed')
    result = analyze(*values)
    value = {'schema_version': 1, 'task': TASK, 'source_head': head, 'run_id': int(os.environ['GITHUB_RUN_ID']),
        'run_status_at_record': 'in_progress', 'analysis': result, 'focused_tests': tests,
        'source_bindings': bindings, 'reused_successful_actions': reused, 'instruction_reference': REFERENCE,
        'actions_observed_before_record': [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs]}
    (ROOT / REPORT).write_bytes(stable(value))
    row['ring_zero_abi'] = REPORT
    state['ring_zero_abi'] = {'path': REPORT, 'run_id': value['run_id'], 'source_head': head, 'target': model.ENTRY}
    state['bp']['current_stop'] = state['source_change_review_ja'] = STOP
    state['bp']['next_step'] = state['next_action']['goal_ja'] = NEXT
    state['next_action']['read_paths'] = [REPORT, SELF, MODEL, SAMPLE, HELPER, CALLER]
    state['observed_head'] = head
    state['observed_head_semantics'] = '保存zero継続の限定ABI source HEAD。完了commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = f'zero採取run{values[0]["run_id"]}と非0側run{values[1]["run_id"]}成功照合。今回run{value["run_id"]}は保存時in_progress。action_requiredを成功へ読み替えない。'
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': 0, 'accepted_standalone_replays': 0,
        'scope_ja': '保存zero54命令の限定ABI監査。外部call未実行、条件付き書込みと未解決帰還を区別。'}
    state['do_not_repeat'].append('保存zero54命令/114byteの採取・限定モデルは完了。次の採取は新規未読targetのみ。仮想call契約を実帰還や保存slot不変へ昇格しない。')
    for p in (SELF, MODEL, TEST, WORKFLOW, REPORT): state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(state))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    need(identity((ROOT / CHECKPOINT).read_bytes()) == checkpoint, 'BP checkpoint mutated')
    saved.bindings_fresh(ROOT, bindings)
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / zero継続の限定ABI監査\n'
        '- Status: DONE / 保存範囲のABI監査完了。zero/callee全体帰還とphysical受入は未完。\n- Version: PR16 zero-prefix ABI\n'
        '- Summary: ' + STOP + '\n'
        f'- Files changed: {SELF}, {MODEL}, {TEST}, {WORKFLOW}, {REPORT}, 固定MD/JSON、P08参照、両ログ。\n'
        f'- Verify: {tests["tests_run"]} focused tests PASS; 新zero域51456入力/selector256値/仮想call契約13818ケース、54命令被覆。render/check、BP checkpoint不変。task graph・最終index差分guard・diff必須。\n'
        f'- Evidence: source={head}; run={value["run_id"]}（保存時in_progress）。zero採取run35000269301成功原本再利用。\n'
        '- Preserved: 本ABI工程のROM/native/候補再構築/再採取/helper再実行/受入済み再実行0。旧18targetと未解決新6target保持。\n'
        '- Commit: 完了commitを同branchへ非force push。最終SHAはremote ref/resultで照合。\n'
        '- Network: GitHub connector/Actions。一次資料検索語 site:sourceware.org/cgen/gen-doc/arm-thumb-insn.html Thumb ldr pop bx semantics; '
        + REFERENCE + '。Thumb-1の分岐、load/store幅、BLを照合。\n'
        '- Boundary: 全体guard既存違反は前後同一/新規0を要求。全体guard PASS・全CI green・merge/release/baseline変更は主張しない。\n'
        '- Next: ' + NEXT + '\n')
    for p in LOGS:
        need(TASK not in (ROOT / p).read_text(encoding='utf-8'), 'duplicate log')
        with (ROOT / p).open('a', encoding='utf-8') as stream: stream.write(entry)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], check=True)
    subprocess.run(['git', 'add', '--', *OUTPUTS], check=True)
    guard.BASE, guard.OUT, guard.ALLOWED = BASE, OUT, set((SELF, MODEL, TEST, WORKFLOW, *OUTPUTS))
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    (OUT / 'summary.json').write_bytes(stable(result))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    run()
