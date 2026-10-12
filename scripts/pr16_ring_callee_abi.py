#!/usr/bin/env python3
"""保存済み10命令のframe/外部境界を検証。callee全体の帰還やpointer安全を仮定しない。"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
BASE = '4c836bb00cba34130d6d6c0f418e88051203aebf'
TASK = 'PR-P08-7-RING-CALLEE-ABI'
SELF = 'scripts/pr16_ring_callee_abi.py'
TEST = 'tests/test_pr16_ring_callee_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-callee-abi.yml'
REPORT = 'content/modernization/pr16_ring_callee_abi.json'
SAMPLE = 'content/modernization/pr16_ring_callee_bytes.json'
FRAME = 'content/modernization/pr16_ring_frame_join.json'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)
SOURCES = (SELF, TEST, WORKFLOW, SAMPLE, FRAME, 'scripts/pr16_ring_callee_bytes.py',
           'scripts/pr16_ring_flagset_continuation.py', 'scripts/pr16_resume.py')
OUT = ROOT / '.local/pr16-ring-callee-abi'
TARGET = 0x09097105
HELPER = 0x091281D1
NONZERO = 0x090970F7
ZERO = 0x0806DDBD
CANDIDATE = {'size': 33554432, 'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b', 'crc32': '3EB17B36'}
# この採取済みprefixだけを許可する。新opcode/別ABIを既存成功へ読み替えない。
ENCODINGS = ('70b5', '0504', '2c0c', '261c', '201c', '91f05ff8', '0028', 'efd1', '0148', '0047')
STOP = ('0x09097105の保存済み10命令/22byteを限定検証。PUSH {r4-r6,lr}で追加16byte、'
        'FlagSet継承8byteと合わせてSP=-24、callee entry LR保存offsetは元entry SPから-12。'
        '引数low16をr0/r4/r6へ渡しBL 0x091281D1。helper帰還時は非0→0x090970F7、'
        '0→literal BX 0x0806DDBDへ進む。観測prefixにPOP/returnなし。'
        'literalはcode targetで返却data pointerではない。callee帰還/SP/r4復元/非aliasは未証明。'
        '旧18target台帳を維持し、この3外部targetを追加境界に記録。BP受入不変。')
NEXT = ('次は未読helper 0x091281D1だけを優先してreturn値とSP/r4-r6/保存slotへの影響を限定確認する。'
        'その後の0x090970F7と0x0806DDBDの継続は未読として保持する。'
        '0x09097105/FlagSet/FlagGetの再採取、15辺再分類、受入済みBPの再実行はしない。'
        '旧18target台帳を削らず、条件付き境界を全caller/全owner除外やRing正規取得へ昇格しない。')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def normalize_argument(value):
    """実opcodeのLSL16→LSR16とADD immediate0を独立した32bit算術で評価。"""
    need(type(value) is int and 0 <= value <= 0xffffffff, 'not a uint32 argument')
    r5 = (value << 16) & 0xffffffff
    r4 = r5 >> 16
    r6 = (r4 + 0) & 0xffffffff
    return {'r0': (r4 + 0) & 0xffffffff, 'r4': r4, 'r5': r5, 'r6': r6}


def analyze(sample, frame):
    """byte/hash/CFGを照合し、証明できたprefixと未読suffixを明確に分離する。"""
    a, f = sample['analysis'], frame['analysis']
    need(sample['schema_version'] == 1 and sample['task'] == 'PR-P08-7-RING-CALLEE-BYTES', 'wrong sample schema')
    need(a['classification'] == 'ONE_CALLEE_BYTES_NOT_NATIVE_ACCEPTANCE'
         and a['target'] == TARGET and a['candidate'] == f['candidate'] == CANDIDATE, 'wrong sample identity')
    need(f['classification'] == 'CONDITIONAL_FRAME_JOIN_NOT_NATIVE_ACCEPTANCE'
         and f['call']['unread_callee'] == TARGET, 'wrong inherited call')
    edge = f['inherited_edge']
    need(edge['frame_bytes'] == 8 and edge['entry_lr_saved_offsets'] == [-4], 'inherited frame differs')
    need(f['call']['bl_return_thumb'] == ((f['call']['site'] + 4) | 1), 'caller BL return differs')
    old = a['old_unread_targets']
    need(old == f['old_unread_targets'] and len(old) == len(set(old)) == 18 and TARGET in old,
         'old frontier changed')
    for k in ('callee_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
              'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready', 'old_frontier_removed'):
        need(a[k] is False, 'unsupported sample claim: ' + k)
    for k in ('stack_integrity_proven', 'all_callers_resolved', 'all_runtime_owners_excluded',
              'ring_acquisition_accepted', 'release_ready'):
        need(f[k] is False, 'unsupported inherited claim: ' + k)
    need(f['call']['callee_return_proven'] is False and f['call']['callee_return_observed'] is False,
         'unobserved callee promoted')
    g = a['graph']
    need(g['entry'] == TARGET and g['window'] == 1024 and g['side_effects_excluded'] is False, 'wrong graph scope')
    nodes = g['nodes']
    need(len(nodes) == len(ENCODINGS), 'unexpected prefix length')
    samples = {}
    for s in a['sampled_ranges']:
        raw = bytes.fromhex(s['hex'])
        need(identity(raw) == {k: s[k] for k in ('size', 'sha256')}, 'sample hash differs')
        key = (s['address'], s['size'])
        need(key not in samples, 'duplicate sample')
        samples[key] = raw
    at, words, required = TARGET & ~1, [], set()
    for i, (n, expected) in enumerate(zip(nodes, ENCODINGS)):
        raw = bytes.fromhex(n['hex'])
        need(n['address'] == at and n['size'] == len(raw) and n['hex'] == expected,
             'unreviewed instruction/ABI change')
        key = (at, len(raw))
        need(samples.get(key) == raw, 'node/sample differ')
        required.add(key)
        words.append(int.from_bytes(raw[:2], 'little'))
        kinds = {5: 'call', 7: 'conditional', 9: 'indirect'}
        need(n['kind'] == kinds.get(i, 'ordinary') and n['memory_write'] is (i == 0), 'instruction kind/write differs')
        need(n['successors'] == ([] if i == 9 else [at + len(raw)]), 'stored CFG differs')
        at += len(raw)
    need(a['sampled_instruction_bytes'] == 22 and g['memory_write_sites'] == [TARGET & ~1], 'write/sample count differs')
    # PUSH順は低register→高register、full-descending。元frameに重ならない16byte。
    pushed = [r for r in range(8) if words[0] & (1 << r)] + ([14] if words[0] & 0x100 else [])
    need(pushed == [4, 5, 6, 14], 'callee saved-register layout differs')
    local_size = len(pushed) * 4
    local_slots = [{'register': r, 'callee_entry_sp_offset': -local_size + i * 4,
                    'flagset_entry_sp_offset': -edge['frame_bytes'] - local_size + i * 4}
                   for i, r in enumerate(pushed)]
    # 実shift/copyのoperandを検査。帰還後にr4-r6が復元されるとは仮定しない。
    need(((words[1] >> 11) & 3, (words[1] >> 6) & 31, (words[1] >> 3) & 7, words[1] & 7) == (0, 16, 0, 5), 'LSL differs')
    need(((words[2] >> 11) & 3, (words[2] >> 6) & 31, (words[2] >> 3) & 7, words[2] & 7) == (1, 16, 5, 4), 'LSR differs')
    for w, rd in ((words[3], 6), (words[4], 0)):
        need(w & 0xfe00 == 0x1c00 and (w >> 6) & 7 == 0 and (w >> 3) & 7 == 4 and w & 7 == rd, 'ADD0 copy differs')
    call = nodes[5]
    tail = int.from_bytes(bytes.fromhex(call['hex'])[2:], 'little')
    helper = (call['address'] + 4 + (signed(words[5] & 0x7ff, 11) << 12) + ((tail & 0x7ff) << 1)) | 1
    need(helper == HELPER and call['target'] == helper & ~1, 'helper BL target differs')
    condition = nodes[7]
    nonzero = (condition['address'] + 4 + (signed(words[7] & 255, 8) << 1)) | 1
    need(nonzero == NONZERO and condition['target'] == nonzero & ~1, 'BNE external target differs')
    literal = nodes[8]
    pool = ((literal['address'] + 4) & ~3) + (words[8] & 255) * 4
    required.add((pool, 4))
    need(set(samples) == required, 'missing/extra samples')
    zero = int.from_bytes(samples[(pool, 4)], 'little')
    need(literal['literal_address'] == pool and literal['literal_value'] == zero == ZERO, 'literal code target differs')
    need(nodes[9]['register'] == (words[9] >> 3) & 15 == 0, 'BX register differs')
    expected_edges = [
        {'site': call['address'], 'kind': 'call', 'target': helper, 'resolved_to_code_address_only': True},
        {'site': condition['address'], 'kind': 'conditional', 'target': nonzero, 'resolved_to_code_address_only': True},
        {'site': nodes[9]['address'], 'kind': 'indirect', 'register': 0, 'target': None}]
    need(g['external_edges'] == expected_edges, 'external frontier differs')
    need(a['external_targets'] == sorted([helper, nonzero])
         and a['additional_unread_targets'] == sorted([helper, nonzero]), 'sample direct frontier differs')
    need(a['sampled_old_targets'] == [TARGET], 'sampled old target differs')
    new = sorted({helper, nonzero, zero})
    need(not set(new) & set(old), 'new frontier already in old ledger')
    return {
        'classification': 'LIVE_FRAME_CALLEE_PREFIX_NOT_RETURN_PROOF', 'candidate': copy.deepcopy(CANDIDATE),
        'target': TARGET, 'instructions_verified': len(nodes), 'instruction_bytes_verified': 22,
        'prefix': {'additional_frame_bytes': local_size, 'total_flagset_frame_bytes': edge['frame_bytes'] + local_size,
            'callee_entry_sp_offset_before_helper': -local_size,
            'flagset_entry_sp_offset_before_helper': -edge['frame_bytes'] - local_size,
            'saved_register_slots': local_slots, 'callee_entry_lr_value': f['call']['bl_return_thumb'],
            'inherited_flagset_saved_offsets': [-8, -4],
            'local_push_does_not_overlap_inherited_slots': True,
            'non_alias_scope': 'ONLY_THIS_PUSH_WITH_VALID_ALIGNED_NONWRAPPING_STACK',
            'argument_r0_r4_r6': 'entry_r0 & 0xffff', 'argument_r5': '(entry_r0 & 0xffff) << 16',
            'r4_r5_r6_rewritten_not_yet_restored': True, 'sampled_return_instructions': 0},
        'helper': {'site': call['address'], 'target': helper, 'bl_return_thumb': (call['address'] + 4) | 1,
                   'return_observed': False, 'return_proven': False, 'stack_preservation_proven': False},
        'conditional_exits': [
            {'condition': 'helper returns here with r0 != 0', 'site': condition['address'], 'target': nonzero,
             'r0_role': 'unconstrained helper result; not an observed returned data pointer'},
            {'condition': 'helper returns here with r0 == 0', 'site': nodes[9]['address'], 'target': zero,
             'r0_role': 'literal Thumb code destination, not returned data pointer', 'literal_address': pool}],
        'exit_frame_assumptions': ['helper returns to its BL continuation',
            'helper preserves SP, r4-r6 and all local/inherited saved slots'],
        'return_pointer': {'established': False, 'non_alias_proven': False,
            'reason': 'Neither outgoing continuation has been read; BX code destination is not a returned buffer.'},
        'callee_return_proven': False, 'callee_sp_restored': False, 'callee_r4_restored': False,
        'inherited_frame_return_verified': False, 'stack_integrity_proven': False,
        'old_unread_targets': copy.deepcopy(old), 'old_frontier_removed': False,
        'sampled_old_targets_still_transitively_unresolved': [TARGET],
        'additional_unread_targets': new, 'priority_unread_targets': [helper],
        'remaining_unread_targets': sorted(set(old) | set(new)),
        'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
        'ring_acquisition_accepted': False, 'release_ready': False,
        'rom_changes': 0, 'new_emulator_processes': 0, 'candidate_reconstructions': 0,
        'new_graph_decodes': 0, 'prior_abi_classifications_replayed': 0, 'accepted_native_cases_replayed': 0}


def read_inputs():
    sys.path.insert(0, str(ROOT / 'scripts'))
    import pr16_ring_callee_bytes as collector
    import pr16_ring_flagset_continuation as saved
    sample = json.loads((ROOT / SAMPLE).read_bytes())
    saved.bindings_fresh(ROOT, sample['source_bindings'])
    need(sample['source_head'] == '680ec66c4406ee027b389585ae06a98cf6b86176'
         and sample['run_id'] == 34976478801 and sample['focused_tests']['successful'] is True, 'sample provenance differs')
    frame, cached = collector.read_prior()
    need(not any((t & ~1) in cached for t in (HELPER, NONZERO, ZERO)), 'frontier has saved code; reuse instead')
    return sample, frame


def check():
    import pr16_ring_flagset_continuation as saved
    value = json.loads((ROOT / REPORT).read_bytes())
    saved.bindings_fresh(ROOT, value['source_bindings'])
    need(value['task'] == TASK and value['focused_tests']['successful'] is True, 'unverified ABI report')
    need(value['analysis'] == analyze(*read_inputs()), 'callee ABI report drift')
    return value


def run():
    import unittest
    sys.path.insert(0, str(ROOT / 'scripts'))
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_compiled_record as guard
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT / REPORT).exists(), 'already recorded; do not repeat')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'execution HEAD differs')
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], check=True)
    pr = saved.api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head
         and pr['head']['ref'] == 'codex/modernization-followup-20260908'
         and pr['head']['repo']['full_name'] == os.environ['GITHUB_REPOSITORY'], 'PR boundary differs')
    state = resume.validate(ROOT)
    gap = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True
         and gap in state['remaining_physical_gap_ids'], 'accepted boundary changed')
    checkpoint = identity((ROOT / CHECKPOINT).read_bytes())
    backlog = resume.load(ROOT, BACKLOG)
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(gap in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][gap] is None, 'Ring owner changed')
    sample, frame = read_inputs()
    bindings = {p: identity((ROOT / p).read_bytes()) for p in SOURCES}
    prior = []
    for run_id, source in ((sample['run_id'], sample['source_head']), (frame['run_id'], frame['source_head']),
                           (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        r = saved.api('actions/runs/' + str(run_id))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == source, 'prior Actions differs')
        prior.append({k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    runs = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    observed = [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs]
    analysis = analyze(sample, frame)
    suite = unittest.TestSuite()
    for pattern in ('test_pr16_ring_callee_abi.py', 'test_pr16_resume.py'):
        suite.addTests(unittest.defaultTestLoader.discover('tests', pattern=pattern))
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
             'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'], 'focused tests failed')
    value = {'schema_version': 1, 'task': TASK, 'source_head': head, 'run_id': int(os.environ['GITHUB_RUN_ID']),
             'run_status_at_record': 'in_progress', 'analysis': analysis, 'focused_tests': tests,
             'source_bindings': bindings, 'reused_successful_actions': prior,
             'sample_artifact': {'id': 10399054270, 'run_id': sample['run_id'],
                 'sha256': '6af2ddda1e74febab447c58064507b97fefc61891d29b802d4f3cb62a8c43a40'},
             'actions_observed_before_record': observed}
    (ROOT / REPORT).write_bytes(stable(value))
    row['ring_callee_abi'] = REPORT
    state['ring_callee_abi'] = {'path': REPORT, 'source_head': head, 'run_id': value['run_id'],
        'priority_unread_targets': [HELPER], 'callee_return_proven': False, 'ring_acquisition_accepted': False}
    state['bp']['current_stop'] = state['source_change_review_ja'] = STOP
    state['bp']['next_step'] = state['next_action']['goal_ja'] = NEXT
    state['next_action']['read_paths'] = [REPORT, SELF, SAMPLE, FRAME, saved.REPORT]
    state['observed_head'] = head
    state['observed_head_semantics'] = '保存済みcallee prefixのframe/外部境界を検証したsource HEAD。完了commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = (f'採取run34976478801・frame結合run34974346670・BP run34946969126はcompleted/successを照合。'
        f'今回run{value["run_id"]}は保存時in_progress。通常CI action_requiredは成功へ読み替えずreceiptへ最新snapshot保存。')
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': 1, 'accepted_standalone_replays': 0,
        'scope_ja': '本セッションは新規callee byte用の同一candidate復元1。ABI工程は保存byteのみでROM復元/decode/native/既存分類再実行0。'}
    note = ('0x09097105の10命令/22byteと追加16byte live-frameの限定検証は完了。'
            'helper091281D1・非0継続090970F7・0継続0806DDBDは未読。'
            'callee return/SP/r4/返却pointer非aliasを受入せず、literal code pointerを返却bufferへ読み替えない。同一prefixを再採取しない。')
    if note not in state['do_not_repeat']:
        state['do_not_repeat'].append(note)
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(state))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    before = {p: identity((ROOT / p).read_bytes()) for p in (REPORT, STATE, DOC, BACKLOG)}
    check()
    need(before == {p: identity((ROOT / p).read_bytes()) for p in before}, 'check writes files')
    need(identity((ROOT / CHECKPOINT).read_bytes()) == checkpoint, 'BP checkpoint changed')
    saved.bindings_fresh(ROOT, bindings)
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 未読callee prefixのABI・非alias境界検証\n'
        '- Status: DONE / 指定1根の限定検証を実装・検証・記録。callee全帰還/Ring正規取得は未完。\n- Version: PR16 callee ABI boundary\n'
        '- Summary: ' + STOP + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定引継ぎMD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: 新規ABI/異常系＋固定resume {tests["tests_run"]} tests PASS。render/check PASS、check副作用0、BP checkpointと保存byte/source binding不変。task graph・最終index差分guard・diffを完了commit前の必須gateとする。\n'
        f'- Evidence: {REPORT}; source={head}; run={value["run_id"]}（保存時in_progress）。採取run34976478801/job104405361675は36tests PASS・checkpoint4c836bb、artifact10399054270のSHA-256をconnector取得byteと照合。\n'
        '- Preserved: 本セッションROM変更/native/受入済み単独再実行/15辺再分類0。同一candidate再構築1は新規byte採取のみ、ABI工程0。旧18targetを保持し追加未読3targetを別記。\n'
        '- Commit: この記録を含む同branch非force commit。自己SHAはremote refとresult artifactで照合。\n'
        '- Network: GitHub connector/Actions、既存hash固定入力。外部検索語「site.github.com/ARM-software/abi-aa aapcs32 r4 r8 SP preserved」および「site.developer.arm.com ARM7TDMI Thumb PUSH POP BX instruction set」。公式AAPCS32 https://github.com/ARM-software/abi-aa/blob/main/aapcs32/aapcs32.rst の本文を確認。ARM7TDMI https://developer.arm.com/documentation/ddi0029/g/CIHEDIDG は検索抄録のみで本文取得は失敗。r4等/SP保存は呼出規約の要求であり、未読helperが遵守する実証とはしない。\n'
        '- Boundary: 既存全体guard違反は前後一致/新規差分0を要求し全体PASSとは呼ばない。通常CI action_requiredを成功へ改称しない。merge/release/baseline変更なし。\n'
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
    (OUT / 'summary.json').write_bytes(stable(analysis))
    print(json.dumps({'tests': tests, 'analysis': analysis}))


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT / 'scripts'))
    if sys.argv[1:] == ['run']:
        run()
    elif sys.argv[1:] == ['check']:
        check()
        print('PASS_READ_ONLY_CALLEE_PREFIX_NOT_RETURN_PROOF')
    else:
        raise SystemExit('usage: pr16_ring_callee_abi.py run|check')
