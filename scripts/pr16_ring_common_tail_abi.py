#!/usr/bin/env python3
"""保存された共通末尾6命令だけのABI検査。ROM復元・既読ABI実行は禁止。"""
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
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
BASE = '4c3045a69f2263161896b8a7fce96e3be73687dd'
BRANCH = 'codex/modernization-followup-20260908'
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
TASK = 'PR-P08-7-RING-COMMON-TAIL-ABI'
SELF = 'scripts/pr16_ring_common_tail_abi.py'
TEST = 'tests/test_pr16_ring_common_tail_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-common-tail-abi.yml'
SAMPLE = 'content/modernization/pr16_ring_common_tail_bytes.json'
ZERO = 'content/modernization/pr16_ring_zero_abi.json'
CALLEE = 'content/modernization/pr16_ring_callee_abi.json'
HELPER = 'content/modernization/pr16_ring_helper_abi.json'
REPORT = 'content/modernization/pr16_ring_common_tail_abi.json'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)
SOURCES = (SELF, TEST, WORKFLOW, SAMPLE, ZERO, CALLEE, HELPER, CHECKPOINT,
           'scripts/pr16_resume.py', 'scripts/pr16_ring_compiled_record.py',
           'scripts/pr16_ring_compiled_owner.py', 'scripts/guard_private_files.py')
OUT = ROOT / '.local/pr16-ring-common-tail-abi'
TARGET, EXIT, MASK = 0x0806DE3D, 0x0806DE63, 0xffffffff
SAVED_WORD_ADDRESS = 0x03005048
OTHER_ROOTS = (0x0806DE51, EXIT, 0x08113889, 0x0806DD1D, 0x081138F9)
SLOT_OFFSETS = (-24, -20, -16, -12, -8, -4)
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
CANDIDATE = {'size': 33554432,
    'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b',
    'crc32': '3EB17B36'}
EXPECTED = ((0x0806DE3C, 'ee23'), (0x0806DE3E, '1b01'),
            (0x0806DE40, 'c918'), (0x0806DE42, '0068'),
            (0x0806DE44, '0ce0'), (0x0806DE60, '4018'))
NO_PROOF = ('callee_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
            'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready',
            'zero_callee_return_proven', 'zero_callee_return_observed',
            'saved_slot_preservation_proven', 'return_pointer_non_alias_proven')
STOP = ('保存済み共通末尾0x0806DE3Dの6命令/12byteを限定ABI検証。'
        'r0=mem32[entry_r0]+entry_r1+0xEE0 (mod 2^32)を計算し、未読0x0806DE63へ続く。'
        '低域の保存済み入口条件ではmem32[0x03005048]+0xEE0+(id>>3)。'
        'POP/return/局所storeは0、SP変化0。先行経路の保存仮定下でFlagSet基準-24のframeが残る。'
        '計算pointerが保存6slotへaliasする反例を保持し、callee帰還/保存slot不変/非aliasは未証明。'
        '旧18target、0x0806DE51と外部call3本、BP受入を保持。')
NEXT = ('次は新規未読0x0806DE63だけを限定採取し、共通末尾後の復元/帰還命令を確認する。'
        '0x0806DE51と外部call0x08113889/0x0806DD1D/0x081138F9は未解決で保持。'
        '保存済み共通末尾6命令、zero54命令、helper全u16、非0側、callee prefix、'
        'FlagSet/FlagGet/15辺分類/BPを再採取・単独再実行しない。'
        '条件付きpointer計算を実帰還・保存slot不変・非alias・全owner除外・Ring通常取得受入へ昇格しない。')


def need(ok, text):
    if not ok:
        raise ValueError(text)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def load(path):
    return json.loads((ROOT / path).read_bytes())


def u32(value):
    need(type(value) is int and 0 <= value <= MASK, 'u32範囲外')
    return value


def decode(address, raw):
    """この6命令で必要なThumb形式のみ。未知命令は拒否する。"""
    need(type(address) is int and address % 2 == 0, '命令address不正')
    need(isinstance(raw, bytes) and len(raw) == 2, '命令長不正')
    h = int.from_bytes(raw, 'little')
    if h & 0xf800 == 0x2000:
        return ('movs', (h >> 8) & 7, h & 255)
    if h & 0xf800 == 0:
        return ('lsls', h & 7, (h >> 3) & 7, (h >> 6) & 31)
    if h & 0xfe00 == 0x1800:
        return ('adds', h & 7, (h >> 3) & 7, (h >> 6) & 7)
    if h & 0xf800 == 0x6800:
        return ('ldr', h & 7, (h >> 3) & 7, ((h >> 6) & 31) * 4)
    if h & 0xf800 == 0xe000:
        disp = h & 0x7ff
        if disp & 0x400:
            disp -= 0x800
        return ('b', (address + 4 + disp * 2) & MASK)
    raise ValueError('未対応命令')


def expected_nodes():
    nodes = []
    for address, hexcode in EXPECTED:
        op = decode(address, bytes.fromhex(hexcode))
        node = {'address': address, 'size': 2, 'hex': hexcode,
                'kind': 'jump' if op[0] == 'b' else 'ordinary', 'memory_write': False}
        if op[0] == 'b':
            node['target'] = op[1]
        node['successors'] = [] if address == 0x0806DE60 else [op[1] if op[0] == 'b' else address + 2]
        nodes.append(node)
    return nodes


def validate_sample(value):
    need(value['schema_version'] == 1 and value['task'] == 'PR-P08-7-RING-COMMON-TAIL-BYTES', '採取scope不一致')
    need(value['source_head'] == 'b0fbc529b66f6043ccbcde0d08da8f3678247181'
         and value['run_id'] == 35007034033, '採取source/run不一致')
    a = value['analysis']
    need(a['classification'] == 'COMMON_TAIL_BYTES_NOT_ABI_PROOF', '採取をABI受入へ昇格している')
    need(a['candidate'] == CANDIDATE and a['target'] == TARGET, 'candidate/root不一致')
    for key in NO_PROOF:
        need(a[key] is False, '採取原本の過大主張: ' + key)
    g = a['graph']
    need(g['entry'] == TARGET and g['window'] == 56, '採取窓不一致')
    need(g['window_identity'] == {'size': 56, 'sha256': '9f4637a8de6ad0f4ad5f8ccd27393d7397b06338db5ec2d227c8043047d4dd33'}, '窓identity不一致')
    need(g['nodes'] == expected_nodes(), '保存命令/辺/注釈不一致')
    need(g['external_edges'] == [{'site': 0x0806DE60, 'kind': 'window_fallthrough',
        'target': EXIT, 'resolved_to_code_address_only': True,
        'stop_reason': 'DEFERRED_UNREAD_ROOT_NOT_DECODED'}], '未読境界不一致')
    need(g['deferred_unread_roots'] == list(OTHER_ROOTS) and g['deferred_roots_decoded'] == 0, '別未読根の混入')
    need(g['memory_write_sites'] == [] and g['side_effects_excluded'] is False, '副作用境界不一致')
    ranges = [{'address': at, 'hex': h, **identity(bytes.fromhex(h))} for at, h in EXPECTED]
    need(a['sampled_ranges'] == ranges and a['sampled_instruction_bytes'] == 12, '保存byte/hash不一致')
    need(len(a['old_unread_targets']) == len(set(a['old_unread_targets'])) == 18
         and a['old_frontier_removed'] is False, '旧18target境界不一致')
    need(set(a['remaining_unread_targets']) == set(a['old_unread_targets']) | {TARGET, *OTHER_ROOTS}, '残辺不一致')
    return a


def validate_links(sample, zero, callee, helper):
    a = validate_sample(sample)
    z, c, h = (x['analysis'] for x in (zero, callee, helper))
    for value, task in ((zero, 'ZERO'), (callee, 'CALLEE'), (helper, 'HELPER')):
        need(value['task'] == 'PR-P08-7-RING-' + task + '-ABI', '先行ABI種別不一致')
        need(value['analysis']['candidate'] == CANDIDATE, '先行candidate不一致')
        need(value['analysis']['ring_acquisition_accepted'] is False, 'Ring受入境界不一致')
    need(z['instructions_verified'] == 54 and z['instruction_bytes_verified'] == 114, 'zero保存prefix不一致')
    low = z['low_input_scope']
    need(low['input_first'] == 1 and low['input_last'] == 2303 and low['common_boundary'] == TARGET, '入口条件不一致')
    need(low['common_boundary_registers_under_preserving_call_assumption'] == {
        'r0': SAVED_WORD_ADDRESS, 'r1': 'id >> 3'}, '保存済み入口register条件不一致')
    need(z['flagset_entry_sp_offset_at_boundaries'] == -24 and z['local_sp_delta'] == 0, 'zero frame不一致')
    need(c['prefix']['total_flagset_frame_bytes'] == 24
         and c['prefix']['flagset_entry_sp_offset_before_helper'] == -24, 'callee frame不一致')
    slots = c['prefix']['saved_register_slots']
    need([s['flagset_entry_sp_offset'] for s in slots] == list(SLOT_OFFSETS[:4])
         and [s['register'] for s in slots] == [4, 5, 6, 14], '保存slot不一致')
    need(c['prefix']['inherited_flagset_saved_offsets'] == list(SLOT_OFFSETS[4:]), '継承slot不一致')
    need(h['helper_return_proven'] is True and h['helper_return_observed'] is False
         and h['helper_sp_preserved'] is True and h['helper_memory_unchanged'] is True, 'helper再利用契約不一致')
    need(h['caller_frame_after_helper']['flagset_entry_sp_offset'] == -24
         and h['caller_frame_after_helper']['saved_register_slots'] == slots, 'helper frame不一致')
    for key in NO_PROOF:
        need(z[key] is False, 'zero過大主張: ' + key)
    need(a['old_unread_targets'] == z['old_unread_targets'] == c['old_unread_targets'], '旧残辺変更')
    return a


def execute(nodes, registers, memory, flags=(0, 0, 0, 0)):
    """整列した副作用のないRAM wordだけを読む有限モデル。未読命令へ入らない。"""
    need(nodes == expected_nodes(), '保存6命令以外は実行不可')
    need(len(registers) == 16 and all(type(x) is int and 0 <= x <= MASK for x in registers), 'register不正')
    need(len(flags) == 4 and all(type(x) is int and x in (0, 1) for x in flags), 'NZCV不正')
    r, f, at, visited, reads = list(registers), list(flags), TARGET & ~1, [], []
    by_address = {n['address']: n for n in nodes}
    while at != EXIT & ~1:
        need(at in by_address and at not in visited and len(visited) < 6, '未読/循環へ到達')
        n = by_address[at]
        op = decode(at, bytes.fromhex(n['hex']))
        visited.append(at)
        after = at + 2
        if op[0] == 'movs':
            _, dest, value = op
            r[dest] = value
            f[:2] = [value >> 31, int(value == 0)]
        elif op[0] == 'lsls':
            _, dest, source, shift = op
            value = r[source]
            if shift:
                f[2] = (value >> (32 - shift)) & 1
            r[dest] = value << shift & MASK
            f[:2] = [r[dest] >> 31, int(r[dest] == 0)]
        elif op[0] == 'adds':
            _, dest, left, right = op
            x, y = r[left], r[right]
            value = (x + y) & MASK
            r[dest] = value
            f[:] = [value >> 31, int(value == 0), int(x + y > MASK),
                     int(bool((~(x ^ y) & (x ^ value)) & 0x80000000))]
        elif op[0] == 'ldr':
            _, dest, source, offset = op
            addr = (r[source] + offset) & MASK
            need(addr % 4 == 0 and addr in memory, '未整列または未提供word')
            r[dest] = u32(memory[addr])
            reads.append(addr)
        elif op[0] == 'b':
            after = op[1]
        else:
            raise ValueError('未知operation')
        at = after
    r[15] = at
    need(visited == [at for at, _ in EXPECTED], '命令coverage不一致')
    return {'registers': r, 'nzcv': f, 'visited': visited, 'word_reads': reads,
            'word_writes': [], 'continuation_thumb': EXIT, 'local_sp_delta': 0}


def analyze(sample, zero, callee, helper):
    a = validate_links(sample, zero, callee, helper)
    nodes, count = a['graph']['nodes'], 0
    bases = (0, 0x02000000, 0x03000000, 0xfffff000, MASK)
    # 新規末尾だけを実行する。helper/zeroの命令も外部callも実行しない。
    for item_id in range(1, 2304):
        for base in bases:
            r = [0x12340000 + k * 0x100 for k in range(16)]
            r[0], r[1], r[13] = SAVED_WORD_ADDRESS, item_id >> 3, 0x02010000
            before = {SAVED_WORD_ADDRESS: base}
            memory = dict(before)
            result = execute(nodes, r, memory)
            after = result['registers']
            need(after[0] == (base + 0xee0 + (item_id >> 3)) & MASK, 'pointer式不一致')
            need(after[1] == (item_id >> 3) + 0xee0 and after[3] == 0xee0, '中間register不一致')
            need(all(after[k] == r[k] for k in (2, *range(4, 15))), '保存register変更')
            need(result['word_reads'] == [SAVED_WORD_ADDRESS] and memory == before, 'memory効果不一致')
            count += 1
    aliases = []
    for offset in SLOT_OFFSETS:
        sp, item_id = 0x02010018, 1
        slot = sp + offset
        base = (slot - 0xee0 - (item_id >> 3)) & MASK
        r = [0] * 16
        r[0], r[1], r[13] = SAVED_WORD_ADDRESS, item_id >> 3, sp - 24
        result = execute(nodes, r, {SAVED_WORD_ADDRESS: base})
        need(result['registers'][0] == slot, 'alias反例不成立')
        aliases.append({'id': item_id, 'flagset_entry_sp': sp, 'saved_slot_offset': offset,
                        'save_base_value': base, 'computed_pointer': slot})
    return {
        'classification': 'COMMON_TAIL_POINTER_PREFIX_NOT_RETURN_PROOF',
        'candidate': copy.deepcopy(CANDIDATE), 'target': TARGET,
        'instructions_verified': 6, 'instruction_bytes_verified': 12,
        'decoded_operations': [{'address': at, 'operation': list(decode(at, bytes.fromhex(raw)))} for at, raw in EXPECTED],
        'pointer_expression': '(mem32[entry_r0] + entry_r1 + 0xEE0) mod 2^32',
        'low_input_pointer_expression_under_saved_entry_assumptions': '(mem32[0x03005048] + 0xEE0 + (id >> 3)) mod 2^32',
        'proof_assumptions_ja': [
            '共通末尾へ到達し、entry_r0が整列した読取可能・非volatile・副作用なしRAM wordを指す。非同期変更なし。',
            '低域式の入口register条件だけは保存zero証拠から再利用。外部calleeの帰還/保存は観測していない。',
            'FlagSet基準frameの結合には先行calleeのSP/r4-r11/保存slot保存と先行storeの非aliasを仮定。'],
        'verification': {'new_tail_low_id_cases': count, 'low_ids': [1, 2303],
            'memory_base_representatives': list(bases), 'instructions_covered': 6,
            'prior_helper_domain_reexecuted': False, 'zero_prefix_reexecuted': False,
            'external_callees_executed': False},
        'data_word_reads_per_path': 1, 'data_read_address': 'entry_r0',
        'local_store_instructions': 0, 'computed_pointer_dereferenced_here': False,
        'local_stack_operations': 0, 'local_sp_delta': 0,
        'local_pop_or_return_instructions': 0, 'local_r4_r5_r6_restoration_instructions': 0,
        'preserved_registers': [2, *range(4, 15)], 'apsr_flags_may_change': True,
        'flagset_entry_sp_offset_at_boundary_under_saved_assumptions': -24,
        'saved_slots_consumed_by_local_instructions': [],
        'local_memory_unchanged_under_read_assumptions': True,
        'entire_callee_memory_unchanged_proven': False,
        'continuation_thumb': EXIT, 'continuation_is_return': False,
        'computed_pointer_is_observed_return_value': False,
        'return_pointer_alias_counterexamples': aliases,
        'counterexamples_are_hypothetical_not_observed_corruption': True,
        'non_alias_scope': 'POINTER_START_BYTE_ONLY_NO_DOWNSTREAM_ACCESS_EXECUTED',
        'old_unread_targets': copy.deepcopy(a['old_unread_targets']), 'old_frontier_removed': False,
        'remaining_unread_targets': copy.deepcopy(a['remaining_unread_targets']),
        'sampled_root_still_transitively_unresolved': TARGET,
        'other_unread_roots_preserved': list(OTHER_ROOTS), 'priority_unread_targets': [EXIT],
        **{k: False for k in NO_PROOF},
        'rom_changes': 0, 'candidate_reconstructions': 0, 'new_emulator_processes': 0,
        'new_graph_decodes': 0, 'prior_abi_classifications_replayed': 0, 'accepted_native_cases_replayed': 0}


def fresh(bindings):
    for path, bound in bindings.items():
        p = ROOT / path
        need(not p.is_symlink() and identity(p.read_bytes()) == bound, 'source freshness不一致: ' + path)


def inputs():
    values = [load(p) for p in (SAMPLE, ZERO, CALLEE, HELPER)]
    need(identity((ROOT / SAMPLE).read_bytes()) == {'size': 15198, 'sha256': 'd20be32b02bbc9e6e134f3edaa9fdfad467258ab7c9c6211c5993c1758d87745'}, '採取原本identity不一致')
    for value in values:
        fresh(value['source_bindings'])
    validate_links(*values)
    return values


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + REPO + '/' + path], cwd=ROOT))


def head_check():
    head = os.environ['GITHUB_SHA']
    need(os.environ['GITHUB_REPOSITORY'] == REPO and os.environ['GITHUB_REF'] == 'refs/heads/' + BRANCH, 'repo/branch不一致')
    need(git('rev-parse', 'HEAD').decode().strip() == head, 'checkout HEAD不一致')
    need(git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == head, 'remote HEAD進行を検出')
    pr = api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'], 'PR状態変更')
    need(pr['head']['sha'] == head and pr['head']['ref'] == BRANCH
         and pr['head']['repo']['full_name'] == REPO, 'PR HEAD不一致')
    return head


def run_tests(pattern, name):
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=pattern)
    with (OUT / (name + '.txt')).open('w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    summary = {'tests_run': result.testsRun, 'failures': len(result.failures),
               'errors': len(result.errors), 'skips': len(result.skipped),
               'successful': result.wasSuccessful() and not result.skipped}
    (OUT / (name + '.json')).write_bytes(stable(summary))
    need(summary['successful'] and summary['tests_run'] > 0, name + '失敗')
    return summary


def preflight():
    import pr16_resume as resume
    OUT.mkdir(parents=True, exist_ok=True)
    head = head_check()
    need(not (ROOT / REPORT).exists(), '完了済み。同じ解析を再実行しない')
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], cwd=ROOT, check=True)
    need(set(git('diff', '--name-only', BASE, head).decode().splitlines()) == {SELF, TEST, WORKFLOW}, '対象外source差分')
    for path in (*SOURCES, *OUTPUTS):
        for parent in Path(path).parents:
            if str(parent) != '.':
                need(not (ROOT / parent / 'AGENTS.md').exists(), '未読の下位AGENTS: ' + str(parent))
    state = resume.validate(ROOT)
    need(state['next_action']['read_paths'][0] == SAMPLE, '次作業が別工程へ進行済み')
    values = inputs()
    reused = []
    for prior in [*values, {'run_id': 34946969126, 'source_head': '0b7497b575a3180a045f2be377386490f192a012'}]:
        rid = prior['run_id']
        run = api('actions/runs/' + str(rid))
        need(run['status'] == 'completed' and run['conclusion'] == 'success'
             and run['head_sha'] == prior['source_head'], '先行Actions不一致')
        jobs = api('actions/runs/' + str(rid) + '/jobs')['jobs']
        need(jobs and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in jobs), '先行job未成功')
        reused.append({**{k: run[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')},
                       'job_ids': [j['id'] for j in jobs]})
    failed = values[0]['failed_attempt_preserved']
    run = api('actions/runs/' + str(failed['run_id']))
    need(run['status'] == 'completed' and run['conclusion'] == 'failure'
         and run['head_sha'] == failed['source_head'], '失敗原本改変')
    query = 'actions/runs?branch=codex%2Fmodernization-followup-20260908'
    runs = api(query + '&per_page=30')['workflow_runs']
    active = []
    for status in ('in_progress', 'queued', 'waiting', 'requested', 'pending'):
        active.extend(api(query + '&status=' + status + '&per_page=100')['workflow_runs'])
    need(not [r for r in active if r['id'] != int(os.environ['GITHUB_RUN_ID']) and '/pr16-ring-' in r['path']], '別Ring run実行中')
    tests = run_tests(Path(TEST).name, 'tests')
    before = {'head': head, 'reused_successful_actions': reused,
        'failed_attempt_preserved': copy.deepcopy(failed), 'focused_tests': tests,
        'actions_before': [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs],
        'source_bindings': {p: identity((ROOT / p).read_bytes()) for p in SOURCES},
        'entry_state_identity': identity((ROOT / STATE).read_bytes()),
        'entry_backlog_identity': identity((ROOT / BACKLOG).read_bytes())}
    (OUT / 'preflight.json').write_bytes(stable(before))
    print(json.dumps({'head': head, 'tests': tests, 'reused_run_ids': [r['id'] for r in reused]}))


def project(state, backlog, report):
    result = report['analysis']
    need(result['classification'] == 'COMMON_TAIL_POINTER_PREFIX_NOT_RETURN_PROOF'
         and result['target'] == TARGET and result['continuation_thumb'] == EXIT
         and result['instructions_verified'] == 6 and result['instruction_bytes_verified'] == 12
         and all(result[k] is False for k in NO_PROOF), '結果のscope/受入境界不一致')
    s, b = copy.deepcopy(state), copy.deepcopy(backlog)
    need({k: s['candidate'][k] for k in CANDIDATE} == CANDIDATE and s['bp']['spending_accepted'] is True, 'BP受入境界変更')
    need(GAP in s['remaining_physical_gap_ids'] and s['latest_native_run'] == 34946969126, 'physical/native境界変更')
    rows = [r for r in b['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR']
    need(len(rows) == 1 and GAP in rows[0]['remaining_supply_gap_ids']
         and rows[0]['selected_supply_entrypoints'][GAP] is None, 'Ring受入へ進行済み')
    rows[0]['ring_common_tail_abi'] = REPORT
    s['ring_common_tail_abi'] = {'path': REPORT, 'run_id': report['run_id'],
        'source_head': report['source_head'], 'classification': report['analysis']['classification'],
        'target': TARGET, 'continuation_thumb': EXIT, 'ring_acquisition_accepted': False}
    s['bp']['current_stop'] = s['source_change_review_ja'] = STOP
    s['bp']['next_step'] = s['next_action']['goal_ja'] = NEXT
    s['next_action']['read_paths'] = [REPORT, SELF, SAMPLE, ZERO, CALLEE]
    s['observed_head'] = report['source_head']
    s['observed_date_jst'] = datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
    s['observed_head_semantics'] = '保存共通末尾6命令の限定ABI source HEAD。完了commit/runはremote ref/Actionsで確認。'
    s['observed_head_checks']['reason_ja'] = (f'共通末尾採取run35007034033/job104509276799とzero/helper/callee/BP成功を照合。'
        f'今回run{report["run_id"]}は保存時in_progress。action_required/既存failureは成功へ読み替えない。')
    s['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': 0, 'accepted_standalone_replays': 0,
        'prior_abi_classifications_replayed': 0, 'scope_ja': '保存共通末尾6命令の限定ABI・pointer計算と未読帰還境界。'}
    note = '共通末尾0x0806DE3Dの保存6命令/12byteの限定ABIは完了。再採取/単独再実行せず、新規未読0x0806DE63へ進む。局所store/POP/return0をcallee全体の保存/帰還証明へ昇格しない。'
    if note not in s['do_not_repeat']:
        s['do_not_repeat'].append(note)
    return s, b


def record():
    import pr16_resume as resume
    import pr16_ring_compiled_record as guard
    before = load('.local/pr16-ring-common-tail-abi/preflight.json')
    need(head_check() == before['head'] and not (ROOT / REPORT).exists(), 'HEAD/既存結果不一致')
    fresh(before['source_bindings'])
    need(identity((ROOT / STATE).read_bytes()) == before['entry_state_identity']
         and identity((ROOT / BACKLOG).read_bytes()) == before['entry_backlog_identity'], '正本が途中変更')
    state, backlog = resume.validate(ROOT), load(BACKLOG)
    report = {'schema_version': 1, 'task': TASK, 'source_head': before['head'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
        'analysis': analyze(*inputs()), 'source_bindings': before['source_bindings'],
        'focused_tests': before['focused_tests'], 'reused_successful_actions': before['reused_successful_actions'],
        'failed_attempt_preserved': before['failed_attempt_preserved'],
        'actions_observed_before_record': before['actions_before']}
    (ROOT / REPORT).write_bytes(stable(report))
    state, backlog = project(state, backlog, report)
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(state))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], cwd=ROOT, check=True)
    resume_tests = run_tests('test_pr16_resume.py', 'resume-tests')
    fresh(before['source_bindings'])
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 保存共通末尾の限定ABI\n'
        '- Status: DONE / 保存6命令の限定ABI工程。callee全体・Ring通常取得は未受入。\n'
        '- Version: PR16 common-tail ABI\n- Summary: ' + STOP + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定引継ぎMD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: 新規限定ABI {before["focused_tests"]["tests_run"]} tests PASS、固定引継ぎ {resume_tests["tests_run"]} tests PASS、render/check PASS。新規末尾のみ11515低域ケース、保存6slotへのalias反例6件。採取原本/source hash照合、BP checkpoint byte不変。\n'
        '- Commit gate: task graph、diff、最終indexとworktree一致、既存全体private guard前後出力完全一致・新規違反0を後続gateで要求。結果は同runのguard.json/recorded-result.json。\n'
        f'- Evidence: source={before["head"]}; run={report["run_id"]}（保存時in_progress）。先行採取run35007034033/job104509276799成功を新規照合。失敗run35006120653はfailure原本で保持。\n'
        '- Preserved: ROM変更0、candidate再構築0、mGBA0、既読ABI/受入済みnative単独再実行0。BP正式受入・他gap・旧18targetを保持。外部callは未実行。\n'
        '- Commit: 完了条件PASS後に同branchへ非force push。自己SHAはremote ref/recorded-result.jsonで確認。\n'
        '- Network: GitHub connector/Actions APIだけ。containerの直接cloneはDNS解決失敗。private Release/ROM/save/外部技術資料の取得なし。\n'
        '- Boundary: 整列・読取可能・非volatile RAMの局所モデル。先行保存契約は仮定であり実観測ではない。全体guard PASS・全CI green・merge・release・baseline変更を主張しない。\n'
        '- Next: ' + NEXT + '\n')
    for path in LOGS:
        need(TASK not in (ROOT / path).read_text(encoding='utf-8'), 'ログ二重記録')
        with (ROOT / path).open('a', encoding='utf-8') as stream:
            stream.write(entry)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], cwd=ROOT, check=True)
    subprocess.run(['git', 'add', '--', *OUTPUTS], cwd=ROOT, check=True)
    guard.BASE, guard.OUT, guard.ALLOWED = BASE, OUT, set((SELF, TEST, WORKFLOW, *OUTPUTS))
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    need(set(git('diff', '--cached', '--name-only').decode().splitlines()) == set(OUTPUTS), 'commit対象外差分')
    (OUT / 'summary.json').write_bytes(stable(report['analysis']))
    print(json.dumps({'instructions': 6, 'bytes': 12, 'continuation_thumb': EXIT,
                      'callee_return_proven': False, 'ring_acquisition_accepted': False}))


if __name__ == '__main__':
    if sys.argv[1:] == ['preflight']:
        preflight()
    elif sys.argv[1:] == ['record']:
        record()
    else:
        raise SystemExit('usage: pr16_ring_common_tail_abi.py preflight|record')
