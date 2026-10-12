#!/usr/bin/env python3
"""保存済みhelperだけをbyte解釈しu16全域を検証。callee全体の帰還へ昇格しない。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = '6ccc42361673876d2b0933e736e2ad201418a72d'
TASK = 'PR-P08-7-RING-HELPER-ABI'
SELF = 'scripts/pr16_ring_helper_abi.py'
TEST = 'tests/test_pr16_ring_helper_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-helper-abi.yml'
SAMPLE = 'content/modernization/pr16_ring_helper_bytes.json'
CALLER = 'content/modernization/pr16_ring_callee_abi.json'
REPORT = 'content/modernization/pr16_ring_helper_abi.json'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)
SOURCES = (SELF, TEST, WORKFLOW, SAMPLE, CALLER, 'scripts/pr16_ring_helper_bytes.py',
           'scripts/pr16_ring_flagset_continuation.py', 'scripts/pr16_resume.py')
OUT = ROOT / '.local/pr16-ring-helper-abi'
TARGET, START, RETURN_SITE, RETURN_LR = 0x091281D1, 0x091281D0, 0x091281FE, 0x09097113
NONZERO, ZERO = 0x090970F7, 0x0806DDBD
CANDIDATE = {'size': 33554432, 'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b', 'crc32': '3EB17B36'}
ENCODINGS = ('8021', '0e4b', 'c318', '1a04', '4901', '120c', '8a42', '0fd3',
    '0b4b', '9c22', 'c318', '0020', '1b04', '1b0c', '9201', '9342', '4041',
    '084b', '4042', '1840', '074b', '9c46', '6044', '7047', 'd810', '064b',
    '9c46', '6044', 'f9e7')
LITERALS = {0x0912820C: 0xFFFFF700, 0x09128210: 0xFFFFE700,
    0x09128214: 0xFDFC9014, 0x09128218: 0x02036FEC, 0x0912821C: 0x0203B0E8}
PRESERVED = tuple(range(4, 12)) + (13, 14)
STOP = ('helper 0x091281D1の保存済み29命令/58byteとliteral20byteを検証し、'
    'callerでzero-extendされたu16全65536値をbyte interpreterと独立式で照合。'
    '0x0900..0x18FF→0x0203B0E8+((id-0x0900)>>3)、0x1900..0x3FFF→0x02036FEC、他は0。'
    '外部呼出し/書込み/stack操作0、r4-r11/SP/LRと保存slotを変更せずBX LRで0x09097113へ帰還する。'
    'helper帰還後もFlagSet基準SP=-24。実native帰還は未観測。'
    '0x090970F7/0x0806DDBDの継続、callee全体帰還と返却pointer非aliasは未証明。旧18target・BP受入を保持。')
NEXT = ('次は未読0x090970F7だけを優先し、helper非0側の返却pointer使用・SP/r4-r6/保存slot復元を限定確認する。'
    '0x0806DDBDは未読として保持。helper/callee/FlagSet/FlagGet再採取、15辺再分類、BP再実行をしない。'
    '旧18targetを削らず、helper単体の帰還証明をcallee全体・全caller/全owner除外・Ring通常取得へ昇格しない。')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def validate_sample(sample):
    """命令/CFG/literal/保存hashを固定許可。別byteを同じ証明へ通さない。"""
    need(sample['schema_version'] == 1 and sample['task'] == 'PR-P08-7-RING-HELPER-BYTES', 'wrong sample')
    a = sample['analysis']
    need(a['classification'] == 'ONE_HELPER_BYTES_NOT_RETURN_PROOF' and a['target'] == TARGET
         and a['candidate'] == CANDIDATE, 'wrong sample identity')
    for k in ('helper_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
              'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready', 'old_frontier_removed'):
        need(a[k] is False, 'unsupported prior claim: ' + k)
    need(len(a['old_unread_targets']) == len(set(a['old_unread_targets'])) == 18, 'old ledger differs')
    need(a['external_targets'] == [] and a['sampled_instruction_bytes'] == 58, 'sample scope differs')
    g = a['graph']
    need(g['entry'] == TARGET and g['window'] == 1024 and g['side_effects_excluded'] is False, 'graph scope differs')
    need(g['window_identity'] == {'size': 1024, 'sha256': 'dbf8363f5f5c00f167b3fb0f5bed639ba41b7b6905ba6fb210a59b8c107f63e8'}, 'window binding differs')
    need(g['external_edges'] == g['memory_write_sites'] == [], 'external/write edge differs')
    need(len(g['nodes']) == 29, 'instruction count differs')
    samples = {}
    for s in a['sampled_ranges']:
        raw = bytes.fromhex(s['hex'])
        need(identity(raw) == {k: s[k] for k in ('size', 'sha256')}, 'sample hash differs')
        key = (s['address'], s['size'])
        need(key not in samples, 'duplicate sample')
        samples[key] = raw
    required, words = set(), []
    for i, (n, encoding) in enumerate(zip(g['nodes'], ENCODINGS)):
        at = START + i * 2
        raw = bytes.fromhex(encoding)
        w = int.from_bytes(raw, 'little')
        words.append(w)
        successors = [] if i == 23 else [at + 2]
        expected = {'address': at, 'size': 2, 'hex': encoding, 'kind': 'ordinary',
                    'memory_write': False, 'successors': successors}
        if i == 7:
            target = at + 4 + signed(w & 255, 8) * 2
            expected.update(kind='conditional', target=target, successors=[at + 2, target])
        elif i == 23:
            expected.update(kind='return', register=14)
        elif i == 28:
            target = at + 4 + signed(w & 0x7ff, 11) * 2
            expected.update(kind='jump', target=target, successors=[target])
        elif w & 0xf800 == 0x4800:
            pool = ((at + 4) & ~3) + (w & 255) * 4
            need(pool in LITERALS, 'unreviewed literal')
            expected.update(literal_address=pool, literal_value=LITERALS[pool])
        need(n == expected, 'instruction/CFG differs at ' + hex(at))
        required.add((at, 2))
        need(samples.get((at, 2)) == raw, 'instruction/sample differ')
    for at, value in LITERALS.items():
        required.add((at, 4))
        need(samples.get((at, 4)) == value.to_bytes(4, 'little'), 'literal/sample differ')
    need(set(samples) == required, 'missing/extra sample')
    return tuple(words), tuple(sorted(LITERALS.items()))


def initial_registers(value):
    regs = [(0x51000000 + i * 0x01010101) & 0xffffffff for i in range(16)]
    regs[0], regs[13], regs[14], regs[15] = value, 0x03007EF0, RETURN_LR, START
    return regs


def execute(words, pools, value, registers=None, carry=0):
    """このhelperのThumb命令を32bitで評価。C以外の条件分岐・store・callは非対応で拒否。"""
    need(type(value) is int and 0 <= value <= 0xffff, 'caller domain is zero-extended u16')
    need(carry in (0, 1), 'invalid carry')
    r = initial_registers(value) if registers is None else list(registers)
    need(len(r) == 16 and all(type(v) is int and 0 <= v <= 0xffffffff for v in r), 'invalid registers')
    need(r[0] == value and r[14] & 1, 'wrong argument/Thumb LR')
    program = {START + i * 2: w for i, w in enumerate(words)}
    literals = dict(pools)
    at, visited, written, reads = START, [], set(), set()
    def put(rd, value):
        need(rd not in (13, 14, 15), 'unreviewed SP/LR/PC destination')
        r[rd] = value & 0xffffffff
        written.add(rd)
    for _ in range(32):
        need(at in program, 'execution escaped saved instructions')
        w = program[at]
        visited.append(at)
        next_at = at + 2
        if w & 0xf800 == 0x2000:
            put((w >> 8) & 7, w & 255)
        elif w & 0xf800 == 0x4800:
            pool = ((at + 4) & ~3) + (w & 255) * 4
            need(pool in literals, 'unknown ROM literal read')
            reads.add(pool)
            put((w >> 8) & 7, literals[pool])
        elif w & 0xfe00 == 0x1800:
            total = r[(w >> 3) & 7] + r[(w >> 6) & 7]
            put(w & 7, total)
            carry = int(total > 0xffffffff)
        elif w & 0xf800 in (0x0000, 0x0800, 0x1000):
            op, shift, source, dest = w >> 11, (w >> 6) & 31, (w >> 3) & 7, w & 7
            value_in = r[source]
            if op == 0:
                if shift:
                    carry = (value_in >> (32 - shift)) & 1
                result = value_in << shift
            else:
                shift = shift or 32
                carry = (value_in >> (shift - 1)) & 1
                result = (value_in if op == 1 else signed(value_in, 32)) >> shift
            put(dest, result)
        elif w & 0xffc0 == 0x4280:
            carry = int(r[w & 7] >= r[(w >> 3) & 7])
        elif w & 0xffc0 == 0x4140:
            total = r[w & 7] + r[(w >> 3) & 7] + carry
            put(w & 7, total)
            carry = int(total > 0xffffffff)
        elif w & 0xffc0 == 0x4240:
            source = r[(w >> 3) & 7]
            put(w & 7, -source)
            carry = int(source == 0)
        elif w & 0xffc0 == 0x4000:
            put(w & 7, r[w & 7] & r[(w >> 3) & 7])
        elif w == 0x4770:
            return {'registers': r, 'return_site': at, 'return_thumb': r[14],
                    'visited': visited, 'written_registers': sorted(written),
                    'literal_reads': sorted(reads), 'memory_writes': []}
        elif w & 0xfc00 == 0x4400:
            op, dest, source = (w >> 8) & 3, (w & 7) | ((w >> 4) & 8), (w >> 3) & 15
            need(op in (0, 2) and source not in (13, 14, 15), 'unreviewed high-register instruction')
            put(dest, r[source] if op == 2 else r[dest] + r[source])
        elif w & 0xff00 == 0xd300:
            if carry == 0:
                next_at = at + 4 + signed(w & 255, 8) * 2
        elif w & 0xf800 == 0xe000:
            next_at = at + 4 + signed(w & 0x7ff, 11) * 2
        else:
            raise ValueError('unreviewed helper encoding: ' + hex(w))
        at = next_at
    raise ValueError('helper did not return within bound')


def specification(value):
    """byte interpreterと別の範囲判定式。callerのu16値以外には外挿しない。"""
    need(type(value) is int and 0 <= value <= 0xffff, 'not u16')
    if 0x0900 <= value <= 0x18ff:
        return 0x0203B0E8 + (value - 0x0900) // 8
    if 0x1900 <= value <= 0x3fff:
        return 0x02036FEC
    return 0


@lru_cache(maxsize=1)
def exhaustive(words, pools):
    visited, written, reads, returns, lengths = set(), set(), set(), set(), {}
    digest, zero_count = hashlib.sha256(), 0
    for value in range(0x10000):
        before = initial_registers(value)
        result = execute(words, pools, value, before)
        after = result['registers']
        need(after[0] == specification(value), 'return expression differs: ' + hex(value))
        need(result['return_site'] == RETURN_SITE and result['return_thumb'] == RETURN_LR, 'return boundary differs')
        need(all(after[i] == before[i] for i in PRESERVED) and not result['memory_writes'], 'preserved state differs')
        visited.update(result['visited']); written.update(result['written_registers']); reads.update(result['literal_reads'])
        returns.add(after[0]); zero_count += int(after[0] == 0)
        steps = len(result['visited']); lengths[steps] = lengths.get(steps, 0) + 1
        digest.update(struct.pack('<I', after[0]))
    need(visited == {START + i * 2 for i in range(29)}, 'uncovered instruction')
    need(written == {0, 1, 2, 3, 12} and not written & set(PRESERVED), 'destination set differs')
    need(reads == set(LITERALS) and lengths == {14: 4096, 24: 61440}, 'coverage differs')
    need(zero_count == 51456 and len(returns) == 514, 'return counts differ')
    return {'domain': {'minimum': 0, 'maximum': 65535, 'values_checked': 65536},
        'zero_returns': zero_count, 'nonzero_returns': 65536 - zero_count,
        'distinct_nonzero_addresses': len(returns) - 1, 'return_table_sha256': digest.hexdigest(),
        'instructions_covered': len(visited), 'max_instructions_per_call': max(lengths),
        'path_instruction_counts': {str(k): v for k, v in sorted(lengths.items())},
        'written_registers': sorted(written), 'preserved_registers': list(PRESERVED),
        'literal_read_addresses': sorted(reads), 'memory_writes': 0,
        'return_site': RETURN_SITE, 'return_thumb': RETURN_LR}


def pointer_address_overlaps_saved_frame(pointer, flagset_entry_sp):
    """pointer先頭byteのみの条件。未読calleeのアクセス幅を推測しない。"""
    need(type(pointer) is int and 0 <= pointer <= 0xffffffff, 'invalid pointer')
    need(type(flagset_entry_sp) is int and 24 <= flagset_entry_sp <= 0xffffffff
         and flagset_entry_sp % 4 == 0, 'invalid/nonwrapping aligned stack')
    return pointer != 0 and flagset_entry_sp - 24 <= pointer < flagset_entry_sp


def analyze(sample, caller):
    words, pools = validate_sample(sample)
    a, c = sample['analysis'], caller['analysis']
    need(caller['schema_version'] == 1 and caller['task'] == 'PR-P08-7-RING-CALLEE-ABI', 'wrong caller')
    need(c['classification'] == 'LIVE_FRAME_CALLEE_PREFIX_NOT_RETURN_PROOF' and c['candidate'] == CANDIDATE, 'caller identity differs')
    need(c['helper']['target'] == TARGET and c['helper']['bl_return_thumb'] == RETURN_LR
         and c['helper']['site'] == 0x0909710E and c['helper']['return_proven'] is False, 'caller helper boundary differs')
    need(c['prefix']['argument_r0_r4_r6'] == 'entry_r0 & 0xffff'
         and c['prefix']['total_flagset_frame_bytes'] == 24
         and c['prefix']['flagset_entry_sp_offset_before_helper'] == -24, 'caller argument/frame differs')
    expected_slots = [{'register': r, 'callee_entry_sp_offset': -16 + 4 * i,
        'flagset_entry_sp_offset': -24 + 4 * i} for i, r in enumerate((4, 5, 6, 14))]
    need(c['prefix']['saved_register_slots'] == expected_slots
         and c['prefix']['inherited_flagset_saved_offsets'] == [-8, -4], 'saved slots differ')
    need(sorted(e['target'] for e in c['conditional_exits']) == sorted([NONZERO, ZERO]), 'caller exits differ')
    need(c['old_unread_targets'] == a['old_unread_targets'] and c['additional_unread_targets'] == a['prior_additional_unread_targets']
         and c['remaining_unread_targets'] == a['remaining_unread_targets'], 'frontier changed')
    for k in ('callee_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
              'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready', 'old_frontier_removed'):
        need(c[k] is False, 'unsupported caller claim: ' + k)
    result = copy.deepcopy(exhaustive(words, pools))
    counterexample_sp = 0x02036FEC + 24
    need(pointer_address_overlaps_saved_frame(specification(0x1900), counterexample_sp), 'non-alias counterexample differs')
    return {'classification': 'U16_HELPER_RETURN_NOT_CALLEE_OR_NATIVE_ACCEPTANCE', 'candidate': copy.deepcopy(CANDIDATE),
        'target': TARGET, 'instructions_verified': 29, 'instruction_bytes_verified': 58, 'literal_bytes_verified': 20,
        'verification': result,
        'return_regions': [
            {'input_first': 0x0900, 'input_last': 0x18ff, 'expression': '0x0203B0E8 + ((id - 0x0900) >> 3)',
             'output_first': 0x0203B0E8, 'output_last': 0x0203B2E7},
            {'input_first': 0x1900, 'input_last': 0x3fff, 'expression': '0x02036FEC', 'output': 0x02036FEC},
            {'input_regions': [[0, 0x08ff], [0x4000, 0xffff]], 'expression': '0', 'output': 0}],
        'helper_return_proven': True, 'helper_return_observed': False,
        'proof_scope': 'SAVED_IMMUTABLE_THUMB_CODE_AND_LITERALS_ZERO_EXTENDED_U16_CALLER_NO_ASYNCHRONOUS_INTERFERENCE',
        'helper_sp_preserved': True, 'helper_r4_r11_preserved': True, 'helper_lr_preserved': True,
        'helper_memory_unchanged': True, 'helper_saved_slots_unchanged': True,
        'helper_stack_operations': 0, 'helper_external_calls': 0, 'apsr_flags_may_change': True,
        'caller_frame_after_helper': {'flagset_entry_sp_offset': -24,
            'saved_register_slots': copy.deepcopy(c['prefix']['saved_register_slots']),
            'inherited_flagset_saved_offsets': copy.deepcopy(c['prefix']['inherited_flagset_saved_offsets']),
            'callee_register_restore_not_yet_observed': True},
        'return_pointer': {'nonzero_data_address_computed': True, 'dereferenced_by_helper': False,
            'non_alias_proven': False, 'downstream_access_width_known': False,
            'counterexample_pointer': 0x02036FEC, 'counterexample_flagset_entry_sp': counterexample_sp,
            'scope': 'POINTER_START_BYTE_ONLY_ACTUAL_STACK_AND_DOWNSTREAM_ACCESSES_UNOBSERVED'},
        'conditional_exits_reused': copy.deepcopy(c['conditional_exits']),
        'callee_return_proven': False, 'inherited_frame_return_verified': False, 'stack_integrity_proven': False,
        'old_unread_targets': copy.deepcopy(a['old_unread_targets']), 'old_frontier_removed': False,
        'prior_additional_targets_preserved': copy.deepcopy(a['prior_additional_unread_targets']),
        'scoped_resolved_additional_targets': [TARGET], 'additional_unread_targets': sorted([NONZERO, ZERO]),
        'priority_unread_targets': [NONZERO],
        'remaining_unread_targets': [t for t in a['remaining_unread_targets'] if t != TARGET],
        'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
        'ring_acquisition_accepted': False, 'release_ready': False,
        'rom_changes': 0, 'new_emulator_processes': 0, 'candidate_reconstructions': 0,
        'new_graph_decodes': 0, 'prior_abi_classifications_replayed': 0, 'accepted_native_cases_replayed': 0}


def read_inputs():
    sys.path.insert(0, str(ROOT / 'scripts'))
    import pr16_ring_flagset_continuation as saved
    sample = json.loads((ROOT / SAMPLE).read_bytes())
    caller = json.loads((ROOT / CALLER).read_bytes())
    saved.bindings_fresh(ROOT, sample['source_bindings'])
    saved.bindings_fresh(ROOT, caller['source_bindings'])
    return sample, caller


def run():
    sys.path.insert(0, str(ROOT / 'scripts'))
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_compiled_record as guard
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT / REPORT).exists(), 'helper ABI already recorded; do not duplicate')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'execution HEAD differs')
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], check=True)
    pr = saved.api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head
         and pr['head']['ref'] == 'codex/modernization-followup-20260908'
         and pr['head']['repo']['full_name'] == os.environ['GITHUB_REPOSITORY'], 'PR boundary differs')
    state = resume.validate(ROOT)
    checkpoint = identity((ROOT / CHECKPOINT).read_bytes())
    backlog = resume.load(ROOT, BACKLOG)
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    gap = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True
         and gap in state['remaining_physical_gap_ids'] and gap in row['remaining_supply_gap_ids']
         and row['selected_supply_entrypoints'][gap] is None, 'acceptance boundary changed')
    sample, caller = read_inputs()
    reused = []
    for rid, source in ((sample['run_id'], sample['source_head']), (caller['run_id'], caller['source_head']),
                        (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        r = saved.api('actions/runs/' + str(rid))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == source, 'prior Actions differs')
        reused.append({k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    runs = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    active = [r for r in runs if r['status'] != 'completed' and r['id'] != int(os.environ['GITHUB_RUN_ID'])
              and r['path'].startswith('.github/workflows/pr16-ring-')]
    need(not active, 'another Ring run is active')
    observed = [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs]
    bindings = {p: identity((ROOT / p).read_bytes()) for p in SOURCES}
    result = analyze(sample, caller)
    value = {'schema_version': 1, 'task': TASK, 'source_head': head,
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
        'analysis': result, 'source_bindings': bindings, 'reused_successful_actions': reused,
        'actions_observed_before_record': observed}
    (OUT / 'audit.json').write_bytes(stable(value))
    suite = unittest.TestSuite()
    for pattern in ('test_pr16_ring_helper_abi.py', 'test_pr16_resume.py'):
        suite.addTests(unittest.defaultTestLoader.discover('tests', pattern=pattern))
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
        'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'], 'focused tests failed')
    value['focused_tests'] = tests
    (ROOT / REPORT).write_bytes(stable(value))
    row['ring_helper_abi'] = REPORT
    state['ring_helper_abi'] = {'path': REPORT, 'source_head': head, 'run_id': value['run_id'], 'target': TARGET,
        'helper_return_proven': True, 'helper_return_observed': False, 'ring_acquisition_accepted': False}
    state['bp']['current_stop'] = state['source_change_review_ja'] = STOP
    state['bp']['next_step'] = state['next_action']['goal_ja'] = NEXT
    state['next_action']['read_paths'] = [REPORT, SELF, SAMPLE, CALLER, 'content/modernization/pr16_ring_frame_join.json']
    state['observed_head'] = head
    state['observed_head_semantics'] = '保存済みhelperのu16 return/SP/register境界を検証したsource HEAD。完了commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = (f'採取run{sample["run_id"]}・caller ABI run{caller["run_id"]}・BP run34946969126成功照合。'
        f'今回run{value["run_id"]}は保存時in_progress。通常CIのfailure/action_requiredはそのままsnapshotに保持し、全greenを主張しない。')
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0, 'candidate_reconstructions': 1,
        'phase_candidate_reconstructions': 0, 'accepted_standalone_replays': 0,
        'scope_ja': 'helper一根採取checkpoint後、保存bytesだけを全u16/stack境界検証。既読graph/受入済みnative再実行0。'}
    state['do_not_repeat'].append('0x091281D1の保存29命令/全u16 return・SP/r4-r11/LR/保存slot非変更検証は完了。source不変なら再採取/単独再実行せず0x090970F7へ進む。callee全体帰還/非alias/Ring受入とは区別する。')
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(state))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    need(identity((ROOT / CHECKPOINT).read_bytes()) == checkpoint, 'BP checkpoint mutated')
    saved.bindings_fresh(ROOT, bindings)
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / helper一根のreturn・stack境界検証\n'
        '- Status: DONE / 指定helperの限定検証・記録完了。Ring通常取得とcallee全体帰還は未完。\n- Version: PR16 helper u16 ABI boundary\n'
        '- Summary: ' + STOP + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定MD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: helper異常系/固定resume {tests["tests_run"]} tests PASS。29命令58byte+literal20byte、全65536入力、独立範囲式/全命令coverage、render/check、BP checkpoint不変。task graph・最終index差分guard・diff必須。\n'
        f'- Evidence: source={head}; run={value["run_id"]}（保存時in_progress）。採取run{sample["run_id"]}・caller ABI・BP原本はcompleted/success照合。\n'
        '- Preserved: ROM変更/native/既読graph再scan/15辺再分類/受入済み単独再実行0。セッション同一candidate復元1、当工程0。旧18target台帳と未読2継続を保持。\n'
        '- Commit: この完了記録を同branchへ非force push、自己SHAはremote ref/resultで照合。\n'
        '- Network: GitHub connector/Actionsと前工程のhash固定入力復元。外部技術資料なし。\n'
        '- Boundary: 既存全体guard違反の前後一致/新規違反0。全体guard PASS/全CI green/全caller/Ring受入を主張しない。merge/release/baseline変更なし。\n'
        '- Next: ' + NEXT + '\n')
    for p in LOGS:
        need(TASK not in (ROOT / p).read_text(encoding='utf-8'), 'duplicate completion log')
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
    sys.modules.setdefault('pr16_ring_helper_abi', sys.modules[__name__])
    if sys.argv[1:] == ['run']:
        run()
    else:
        raise SystemExit('usage: pr16_ring_helper_abi.py run')
