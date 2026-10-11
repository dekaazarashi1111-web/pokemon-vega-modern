#!/usr/bin/env python3
"""保存済み非0継続のPOPを既証明frameへ結合。ROM/nativeは実行しない。"""
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
BASE = '944c3ee1d6c82954e19a12fcb93907c81a7d6e42'
TASK = 'PR-P08-7-RING-NONZERO-ABI'
SELF = 'scripts/pr16_ring_nonzero_abi.py'
TEST = 'tests/test_pr16_ring_nonzero_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-nonzero-abi.yml'
SAMPLE = 'content/modernization/pr16_ring_nonzero_bytes.json'
HELPER = 'content/modernization/pr16_ring_helper_abi.json'
CALLER = 'content/modernization/pr16_ring_callee_abi.json'
FRAME = 'content/modernization/pr16_ring_frame_join.json'
REPORT = 'content/modernization/pr16_ring_nonzero_abi.json'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUT = ROOT / '.local/pr16-ring-nonzero-abi'
TARGET, ZERO, RETURN, HELPER_RETURN = 0x090970F7, 0x0806DDBD, 0x0806DE81, 0x09097113
CANDIDATE = {'size': 33554432, 'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b', 'crc32': '3EB17B36'}
SOURCES = (SELF, TEST, WORKFLOW, SAMPLE, HELPER, CALLER, FRAME,
    'scripts/pr16_ring_nonzero_bytes.py', 'scripts/pr16_ring_flagset_continuation.py',
    'scripts/pr16_ring_compiled_record.py', 'scripts/pr16_resume.py')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)
STOP = ('保存済み0x090970F7は70bd=POP {r4-r6,pc}の1命令2byte。'
    'helper非0側だけで保存r4/r5/r6とsaved LRからPCを復元し、SPはFlagSet基準-24→-8、callee入口へ戻る。'
    '帰還先0x0806DE81、r0返却pointer不変、pointer参照/書込み0、外側8byte frameと保存slotは残る。'
    'LR register自体は復元せず0x09097113を保持。既証明prefix/helperと有効不変stackを前提とするsource結合で、native帰還は未観測。'
    '未読0x0806DDBD、callee全体/返却pointer非alias/全caller・ownerは未証明。旧18target・BP受入を保持。')
NEXT = ('次は未読0x0806DDBDだけを優先し、helper zero側の返却値生成・SP/r4-r6/保存slot復元を限定確認する。'
    '今回の非0継続POP、helper全u16、callee prefix、FlagSet/FlagGet、15辺分類、BP受入を再採取/単独再実行しない。'
    '旧18targetを削らず、非0側の条件付き帰還をcallee全体・全caller/全owner除外・Ring通常取得へ昇格しない。')
REFERENCE = 'https://sourceware.org/cgen/gen-doc/arm-thumb-insn.html#insn-pop-pc'


def need(ok, text):
    if not ok:
        raise ValueError(text)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def pop_registers(raw):
    """Thumb-1 POP-PC形式から低registerを昇順に導出。推測decodeしない。"""
    need(len(raw) == 2, 'POP must be one halfword')
    word = int.from_bytes(raw, 'little')
    need(word & 0xff00 == 0xbd00, 'not Thumb-1 POP with PC')
    return [r for r in range(8) if word & (1 << r)] + [15]


def symbolic_pop(raw, sp, memory, registers):
    """相対SPで表す有効不変stack。値は任意symbol、memoryを変更しない。"""
    need(type(sp) is int and sp % 4 == 0, 'unaligned relative stack')
    result, reads = dict(registers), []
    for r in pop_registers(raw):
        need(sp in memory, 'missing saved slot')
        result[r] = memory[sp]
        reads.append({'register': r, 'flagset_entry_sp_offset': sp, 'width': 4, 'value': memory[sp]})
        sp += 4
    return result, sp, reads


def analyze(sample, helper, caller):
    """検証済みhelper/prefixは再実行せず、その結論と今回の2byteだけを結合。"""
    a, h, c = (v['analysis'] for v in (sample, helper, caller))
    expected_classes = ('NONZERO_CONTINUATION_BYTES_NOT_ABI_PROOF',
        'U16_HELPER_RETURN_NOT_CALLEE_OR_NATIVE_ACCEPTANCE', 'LIVE_FRAME_CALLEE_PREFIX_NOT_RETURN_PROOF')
    for value, classification in zip((a, h, c), expected_classes):
        need(value['classification'] == classification and value['candidate'] == CANDIDATE, 'scope/candidate differs')
        need(value['old_frontier_removed'] is False and value['callee_return_proven'] is False, 'prior overclaim')
        for key in ('stack_integrity_proven', 'all_callers_resolved', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
            need(value[key] is False, 'unsupported prior acceptance: ' + key)
    old = h['old_unread_targets']
    need(len(old) == len(set(old)) == 18 and a['old_unread_targets'] == c['old_unread_targets'] == old, 'old frontier differs')
    need(h['additional_unread_targets'] == [ZERO, TARGET] and h['priority_unread_targets'] == [TARGET]
         and a['priority_unread_targets'] == [TARGET], 'next target differs')
    need(c['target'] == 0x09097105 and h['target'] == 0x091281D1 and a['target'] == TARGET, 'entry differs')
    g = a['graph']
    need(g['entry'] == TARGET and g['window'] == 14 and g['side_effects_excluded'] is False, 'graph boundary differs')
    need(len(g['nodes']) == 1 and g['external_edges'] == g['memory_write_sites'] == [], 'not terminal single POP')
    node = g['nodes'][0]
    need(node == {'address': TARGET & ~1, 'size': 2, 'hex': '70bd', 'kind': 'return',
                  'memory_write': False, 'successors': []}, 'instruction metadata/bytes differ')
    raw = bytes.fromhex(node['hex'])
    need(a['sampled_instruction_bytes'] == 2 and a['sampled_ranges'] == [
        dict(address=TARGET & ~1, hex=raw.hex(), **identity(raw))], 'sample binding differs')
    need(pop_registers(raw) == [4, 5, 6, 15], 'unexpected POP register mask')
    for key in ('helper_return_proven', 'helper_sp_preserved', 'helper_r4_r11_preserved',
                'helper_lr_preserved', 'helper_memory_unchanged', 'helper_saved_slots_unchanged'):
        need(h[key] is True, 'missing helper premise: ' + key)
    need(h['helper_return_observed'] is False and h['helper_stack_operations'] == h['helper_external_calls'] == 0, 'helper boundary differs')
    need(h['verification']['return_thumb'] == c['helper']['bl_return_thumb'] == HELPER_RETURN
         and c['helper']['target'] == h['target'], 'helper continuation differs')
    exits = c['conditional_exits']
    need(h['conditional_exits_reused'] == exits and len(exits) == 2, 'conditional exits differ')
    need(exits[0]['target'] == TARGET and exits[0]['site'] == 0x09097114
         and exits[0]['condition'] == 'helper returns here with r0 != 0', 'nonzero route differs')
    need(exits[1]['target'] == ZERO and exits[1]['condition'] == 'helper returns here with r0 == 0', 'zero boundary differs')
    p, frame = c['prefix'], h['caller_frame_after_helper']
    slots = [{'register': r, 'callee_entry_sp_offset': -16 + 4*i,
              'flagset_entry_sp_offset': -24 + 4*i} for i, r in enumerate((4, 5, 6, 14))]
    need(p['saved_register_slots'] == frame['saved_register_slots'] == slots, 'saved layout differs')
    need(p['additional_frame_bytes'] == 16 and p['total_flagset_frame_bytes'] == 24
         and p['callee_entry_sp_offset_before_helper'] == -16
         and p['flagset_entry_sp_offset_before_helper'] == frame['flagset_entry_sp_offset'] == -24, 'SP premise differs')
    need(p['inherited_flagset_saved_offsets'] == frame['inherited_flagset_saved_offsets'] == [-8, -4]
         and p['local_push_does_not_overlap_inherited_slots'] is True, 'outer frame differs')
    need(p['callee_entry_lr_value'] == RETURN, 'saved return differs')
    memory = {-24: 'callee_entry_r4', -20: 'callee_entry_r5', -16: 'callee_entry_r6',
              -12: RETURN, -8: 'flagset_entry_r4', -4: 'flagset_entry_lr'}
    registers = {r: f'continuation_entry_r{r}' for r in range(16)}
    registers[0], registers[14] = 'helper_nonzero_result', HELPER_RETURN
    restored, sp, reads = symbolic_pop(raw, -24, memory, registers)
    need(sp == -8 and restored[15] == RETURN and restored[14] == HELPER_RETURN, 'return join differs')
    need(all(restored[r] == f'callee_entry_r{r}' for r in (4, 5, 6)) and restored[0] == registers[0], 'register join differs')
    need(all(restored[r] == registers[r] for r in (1, 2, 3, 7, 8, 9, 10, 11, 12)), 'unexpected clobber')
    need(not {row['flagset_entry_sp_offset'] for row in reads} & {-8, -4}, 'outer frame consumed')
    return {'classification': 'CONDITIONAL_NONZERO_CALLEE_RETURN_NOT_WHOLE_CALLEE_OR_NATIVE_ACCEPTANCE',
        'candidate': copy.deepcopy(CANDIDATE), 'target': TARGET,
        'instructions_verified': 1, 'instruction_bytes_verified': 2, 'opcode_hex': raw.hex(),
        'stack_reads': reads, 'flagset_entry_sp_before': -24, 'flagset_entry_sp_after': sp,
        'callee_entry_sp_after': 0, 'remaining_inherited_frame_bytes': 8,
        'saved_return_word_loaded_into_pc': restored[15], 'return_instruction_address': RETURN & ~1,
        'r4_r5_r6_restored': True, 'r0_helper_pointer_preserved': True,
        'lr_register_restored_from_stack': False, 'lr_register_after': restored[14],
        'pointer_dereferences': 0, 'memory_writes': 0, 'external_calls': 0,
        'inherited_saved_slots_unchanged': True, 'local_saved_slots_unchanged': True,
        'apsr_changed_by_pop': False, 'condition_flags_before_pop_not_restored': True,
        'nonzero_callee_return_proven': True, 'nonzero_callee_return_observed': False,
        'proof_assumptions': ['hash固定codeとliteral・既証明zero-extend u16 caller/helperの非0経路',
            '有効・word-aligned・非wrap stack、保存済みprefixのentry LRと保存slotが不変',
            '正常な同期実行。割込み等の非同期変更・実stack位置は未観測'],
        'helper_nonzero_inputs_reused': h['verification']['nonzero_returns'],
        'helper_domain_reexecuted': False, 'helper_return_regions_reused': copy.deepcopy(h['return_regions']),
        'return_pointer': {'established_on_nonzero_path': True, 'dereferenced_by_continuation': False,
            'non_alias_proven': False, 'prior_counterexample_preserved': copy.deepcopy(h['return_pointer']),
            'scope': 'POP_READS_STACK_ONLY_DOES_NOT_TEST_POINTER_VS_ACTUAL_STACK_OR_DOWNSTREAM_STORES'},
        'callee_return_proven': False, 'inherited_frame_return_verified': False, 'stack_integrity_proven': False,
        'old_unread_targets': copy.deepcopy(old), 'old_frontier_removed': False,
        'prior_additional_targets_preserved': copy.deepcopy(h['prior_additional_targets_preserved']),
        'scoped_resolved_additional_targets': sorted(set(h['scoped_resolved_additional_targets']) | {TARGET}),
        'additional_unread_targets': [ZERO], 'priority_unread_targets': [ZERO],
        'remaining_unread_targets': sorted(set(old) | {ZERO}),
        'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
        'ring_acquisition_accepted': False, 'release_ready': False, 'rom_changes': 0,
        'new_emulator_processes': 0, 'candidate_reconstructions': 0, 'new_graph_decodes': 0,
        'prior_abi_classifications_replayed': 0, 'accepted_native_cases_replayed': 0}


def read_inputs():
    return tuple(json.loads((ROOT / p).read_bytes()) for p in (SAMPLE, HELPER, CALLER))


def run():
    sys.path.insert(0, str(ROOT / 'scripts'))
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
         and pr['head']['ref'] == 'codex/modernization-followup-20260908'
         and pr['head']['repo']['full_name'] == os.environ['GITHUB_REPOSITORY'], 'PR boundary differs')
    state, backlog = resume.validate(ROOT), resume.load(ROOT, BACKLOG)
    checkpoint = identity((ROOT / CHECKPOINT).read_bytes())
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    gap = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True
         and gap in state['remaining_physical_gap_ids'] and gap in row['remaining_supply_gap_ids']
         and row['selected_supply_entrypoints'][gap] is None, 'acceptance boundary differs')
    sample, helper, caller = read_inputs()
    for v in (sample, helper, caller):
        saved.bindings_fresh(ROOT, v['source_bindings'])
    reused = []
    for rid, source in ((sample['run_id'], sample['source_head']), (helper['run_id'], helper['source_head']),
                        (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        r = saved.api('actions/runs/' + str(rid))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == source, 'prior run differs')
        reused.append({k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    runs = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    need(not [r for r in runs if r['status'] != 'completed' and r['id'] != int(os.environ['GITHUB_RUN_ID'])
              and '/pr16-ring-' in r['path']], 'another Ring run active')
    bindings = {p: identity((ROOT / p).read_bytes()) for p in SOURCES}
    result = analyze(sample, helper, caller)
    value = {'schema_version': 1, 'task': TASK, 'source_head': head,
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
        'analysis': result, 'source_bindings': bindings, 'reused_successful_actions': reused,
        'actions_observed_before_record': [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs],
        'instruction_reference': {'url': REFERENCE, 'scope': 'POP-PCのencoding・低register昇順load・最後にPC・SP更新のみ'}}
    (OUT / 'audit.json').write_bytes(stable(value))
    suite = unittest.defaultTestLoader.discover('tests', pattern='test_pr16_ring_nonzero_abi.py')
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
        'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'] and tests['tests_run'] > 0, 'focused tests failed')
    value['focused_tests'] = tests
    (ROOT / REPORT).write_bytes(stable(value))
    row['ring_nonzero_abi'] = REPORT
    state['ring_nonzero_abi'] = {'path': REPORT, 'source_head': head, 'run_id': value['run_id'], 'target': TARGET,
        'nonzero_callee_return_proven': True, 'callee_return_proven': False, 'ring_acquisition_accepted': False}
    state['bp']['current_stop'] = state['source_change_review_ja'] = STOP
    state['bp']['next_step'] = state['next_action']['goal_ja'] = NEXT
    state['next_action']['read_paths'] = [REPORT, SELF, SAMPLE, HELPER, CALLER, FRAME]
    state['observed_head'] = head
    state['observed_head_semantics'] = '保存済み非0継続POPの限定ABI結合source HEAD。完了commit/runはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja'] = (f'採取run{sample["run_id"]}・helper run{helper["run_id"]}・BP run34946969126成功照合。'
        f'今回run{value["run_id"]}は記録時in_progress。failure/action_requiredは原状態を保持し全CI greenを主張しない。')
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0, 'candidate_reconstructions': 1,
        'phase_candidate_reconstructions': 0, 'accepted_standalone_replays': 0,
        'scope_ja': '未読非0継続一根を採取保存後、その1命令2byteだけを既存frameへ結合。helper全u16/既読graph/native再実行0。'}
    state['do_not_repeat'].append('0x090970F7の保存POP1命令2byte・非0側SP/r4-r6/保存slot結合は完了。同一入力を再採取/単独再実行せず未読0x0806DDBDへ進む。callee全体/非alias/Ring受入とは区別。')
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(state))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    need(identity((ROOT / CHECKPOINT).read_bytes()) == checkpoint, 'BP checkpoint mutated')
    saved.bindings_fresh(ROOT, bindings)
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 非0継続の限定帰還・stack結合\n'
        '- Status: DONE / 指定非0継続の実装・検証・記録完了。Ring通常取得とcallee全体帰還は未完。\n- Version: PR16 nonzero conditional ABI\n'
        '- Summary: ' + STOP + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定MD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: POP/結合異常系{tests["tests_run"]} tests PASS、render/check PASS、BP checkpoint不変、task graph・最終index差分guard・diff必須。\n'
        f'- Evidence: source={head}; run={value["run_id"]}（記録時in_progress）。採取run{sample["run_id"]}・helper・BP原本はsuccess照合。\n'
        '- Preserved: ROM変更/native/既読graph/15辺再分類/受入済み単独再実行0。セッション候補復元1、当工程0。旧18target保持。\n'
        '- Commit: 完了記録を同branchへ非force push。自己SHAはremote ref/resultで照合。\n'
        '- Network: GitHub connector/Actions。検索語「ARM Thumb POP PC semantics」、一次資料 ' + REFERENCE + '。POP低register昇順load→PC・SP更新のencoding/意味だけ参照。\n'
        '- Boundary: 既存全体guard違反の前後一致/新規違反0を要求。全体guard PASS・全CI green・全owner除外・merge・release・baseline変更を主張しない。\n'
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
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    if sys.argv[1:] == ['run']:
        run()
    else:
        raise SystemExit('usage: pr16_ring_nonzero_abi.py run')
