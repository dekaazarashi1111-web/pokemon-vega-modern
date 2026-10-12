#!/usr/bin/env python3
"""保存済みFlagSet graphと継承frameを結合する。ROM取得・既存15辺の再分類はしない。"""
from __future__ import annotations

from collections import deque
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_indirect_abi as abi
import pr16_ring_flagset_continuation as saved

TASK = 'PR-P08-7-RING-FRAME-JOIN'
BASE = '1c64151fe28cd2646b894e4bfb188b601275fcef'
SELF = 'scripts/pr16_ring_frame_join.py'
TEST = 'tests/test_pr16_ring_frame_join.py'
WORKFLOW = '.github/workflows/pr16-ring-frame-join.yml'
REPORT = 'content/modernization/pr16_ring_frame_join.json'
OUTPUTS = (REPORT, saved.STATE, saved.DOC, saved.BACKLOG, *saved.LOGS)
SOURCES = (SELF, TEST, WORKFLOW, saved.SELF, saved.REPORT, saved.ABI,
           saved.PATCH, saved.PRIOR, abi.SELF)
OUT = ROOT / '.local/pr16-ring-frame-join'
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
SAVED_R4 = ('saved-register', 4)
need, stable, identity = saved.need, saved.stable, saved.identity
NEXT = ('保存済みFlagSet継続と継承8byte frameの条件付き結合は完了。次は旧18未読targetのうち'
        '0x09097105だけを優先し、0x0806DDB5 veneerから渡るcalleeのreturn・SP/r4保存・'
        '返却pointerとstack非alias条件を限定確認する。0x0806DE7D/FlagGetの再採取、'
        '15間接辺の再分類、受入済みBPの再実行はしない。旧18targetの台帳を削らず、'
        '条件付き帰還をstack integrity/全caller/全owner除外やRing通常取得へ昇格しない。')
STOP = ('保存済みprologue→0x0806DE7D→call veneerを結合。継承SP=-8とLR保存offset -4から、'
        'calleeが帰還してSP/保存slotを保ち、STRBがframeへaliasしない条件下で、'
        '0x0806DE9AのBX r1がentry LRへ戻りSP=0/r4復元となることを確認。'
        'BL 0x0806DDB5は保存済みveneerを経由して旧未読0x09097105へ到達。'
        'そのcalleeの帰還・stack integrity・全caller/全owner網羅性は未証明。'
        '旧18未読targetと正式BP受入は維持し、ROM/native/既存15辺再分類0。')


def flow_from(graph, initial):
    """既存transferを新しい継承状態で使用。opaque call/unknown storeの安全性は仮定。"""
    nodes = {n['address']: n for n in graph['nodes']}
    need(len(nodes) == len(graph['nodes']), 'duplicate graph nodes')
    entry = graph['entry'] & ~1
    need(graph['entry'] & 1 and entry in nodes, 'missing Thumb entry')
    for node in nodes.values():
        abi.validate_node(node)
    states, queue, steps = {entry: initial}, deque([entry]), 0
    while queue:
        at = queue.popleft()
        steps += 1
        need(steps <= 512, 'frame-join budget exceeded')
        after = abi.transfer(nodes[at], states[at])
        for dest in nodes[at]['successors']:
            need(dest in nodes, 'missing CFG successor')
            joined = abi.merge(states[dest], after) if dest in states else after
            if states.get(dest) != joined:
                states[dest] = joined
                queue.append(dest)
    need(set(states) == set(nodes), 'unreachable stored nodes')
    return states


def analyze(receipt, classification, patch, prior):
    """証拠の結合のみ。未読calleeを成功した呼出しとして扱わない。"""
    a = receipt['analysis']
    edge, old, graphs, cached = saved.saved_metadata(classification, patch, prior)
    need(receipt['schema_version'] == 1 and receipt['task'] == saved.TASK, 'wrong saved scope')
    need(a['classification'] == 'FLAGSET_CONTINUATION_BYTES_NOT_NATIVE_ACCEPTANCE', 'wrong collection class')
    need(a['candidate'] == saved.CANDIDATE and a['target'] == saved.TARGET, 'wrong candidate/target')
    need(a['inherited_edge'] == edge, 'inherited frame metadata differs')
    need(a['old_unread_targets'] == old and a['remaining_unread_targets'] == old
         and a['additional_unread_targets'] == [], 'saved frontier differs')
    for key in ('inherited_frame_return_verified', 'stack_integrity_proven', 'all_callers_resolved',
                'ring_acquisition_accepted', 'all_runtime_owners_excluded', 'release_ready'):
        need(a[key] is False, 'unsupported saved proof: ' + key)
    graph = a['graph']
    saved.validate_graph(graph, cached)
    need(a['sampled_instruction_bytes'] == sum(n['size'] for n in graph['nodes']), 'sample size differs')
    samples = {(x['address'], x['size']): x for x in a['sampled_ranges']}
    need(len(samples) == len(a['sampled_ranges']), 'duplicate byte samples')
    for n in graph['nodes']:
        raw = bytes.fromhex(n['hex'])
        sample = samples[(n['address'], n['size'])]
        need(sample['hex'] == n['hex'] and identity(raw) == {k: sample[k] for k in ('size', 'sha256')},
             'saved bytes/hash differ')
    by_entry = {}
    for g in graphs:
        need(g['entry'] not in by_entry, 'duplicate saved graph entry')
        by_entry[g['entry']] = g
    prologue = by_entry[edge['owner']]
    need(not any(n['kind'] == 'call' for n in prologue['nodes']), 'unexpected prologue call')
    regs, slots = abi.initial()
    regs = list(regs)
    regs[4] = SAVED_R4
    prefix = flow_from(prologue, (tuple(regs), slots))
    terminals = [n for n in prologue['nodes'] if not n['successors']]
    need(len(terminals) == 1 and terminals[0]['address'] == edge['site']
         and terminals[0]['kind'] == 'indirect', 'prologue terminal differs')
    inherited = prefix[edge['site']]
    need(inherited[0][edge['register']] == abi.const(saved.TARGET), 'branch target differs')
    need(inherited[0][13] == ('sp', -8) and dict(inherited[1]) == {-8: SAVED_R4, -4: abi.RETURN},
         'inherited saved LR/r4/SP differ')
    calls = [n for n in graph['nodes'] if n['kind'] == 'call']
    need(len(calls) == 1, 'unexpected continuation call count')
    call = calls[0]
    abi.transfer(call, inherited)  # BL byte/target整合性を検査。帰還の証明には使わない。
    entry = call['target'] | 1
    need(a['reused_saved_entries'] == [entry], 'callee cache binding differs')
    chain, opaque = abi.literal_chain(entry, by_entry)
    need(chain and opaque in old and opaque not in by_entry, 'missing old unread callee')
    for link in chain:
        g = by_entry[link['entry']]
        for n in g['nodes']:
            abi.validate_node(n)
        need(g['memory_write_sites'] == [] and g['external_edges'] == [
            {'site': link['site'], 'kind': 'indirect', 'register': (abi.half(g['nodes'][1]) >> 3) & 15,
             'target': None}], 'veneer edge/write metadata differs')
        recorded = g.get('resolved_veneer', {})
        need(recorded.get('site') == link['site'] and recorded.get('target') == link['target'],
             'recorded veneer resolution differs')
    # 以下はopaque callee帰還と非aliasを前提とする条件付きsuffixであり、実行証拠ではない。
    states = flow_from(graph, inherited)
    exits = [n for n in graph['nodes'] if not n['successors']]
    need(len(exits) == 1 and exits[0]['kind'] == 'indirect', 'unexpected return frontier')
    terminal = exits[0]
    need(graph['external_edges'] == [
        {'site': call['address'], 'kind': 'call', 'target': entry, 'resolved_to_code_address_only': True},
        {'site': terminal['address'], 'kind': 'indirect', 'register': terminal['register'], 'target': None}],
        'continuation edge metadata differs')
    result = states[terminal['address']]
    need(result[0][terminal['register']] == abi.RETURN and result[0][13] == ('sp', 0)
         and result[0][4] == SAVED_R4 and result[1] == (), 'conditional frame not restored')
    shared = [{'owner': g['entry'], 'site': n['address']} for g in [*graphs, graph]
              for n in g['nodes'] if n['kind'] == 'call' and n['target'] | 1 == entry]
    return {
        'classification': 'CONDITIONAL_FRAME_JOIN_NOT_NATIVE_ACCEPTANCE',
        'candidate': copy.deepcopy(saved.CANDIDATE), 'inherited_edge': copy.deepcopy(edge),
        'call': {'site': call['address'], 'entry': entry, 'bl_return_thumb': (call['address'] + 4) | 1,
                 'saved_veneer_chain': chain, 'unread_callee': opaque,
                 'callee_return_observed': False, 'callee_return_proven': False},
        'conditional_return': {'site': terminal['address'], 'register': terminal['register'],
            'entry_lr_restored': True, 'r4_restored': True, 'sp_offset': 0,
            'scope': 'ONLY_IF_OPAQUE_CALLEE_RETURNS_AND_PRESERVES_FRAME_AND_STORE_DOES_NOT_ALIAS',
            'assumptions': ['opaque callee returns to the BL continuation',
                            'callee preserves SP, r4 and both inherited saved slots',
                            'continuation memory store does not alias inherited saved slots'],
            'memory_write_sites': graph['memory_write_sites']},
        'saved_graph_callsites_to_shared_veneer': shared,
        'priority_unread_targets': [opaque], 'other_unread_targets': [t for t in old if t != opaque],
        'old_unread_targets': old, 'remaining_unread_targets': old, 'additional_unread_targets': [],
        'inherited_frame_return_verified': False, 'stack_integrity_proven': False,
        'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
        'ring_acquisition_accepted': False, 'release_ready': False,
        'rom_changes': 0, 'new_emulator_processes': 0, 'candidate_reconstructions': 0,
        'new_graph_decodes': 0, 'prior_abi_classifications_replayed': 0,
        'accepted_native_cases_replayed': 0}


def read_saved():
    receipt = json.loads((ROOT / saved.REPORT).read_bytes())
    saved.bindings_fresh(ROOT, receipt['source_bindings'])
    need(receipt['run_id'] == 34971661219 and receipt['source_head'] ==
         '27f29ff3ce6b26ca9b1ac439e29f655910d5eebd', 'collection provenance differs')
    return receipt, *saved.read_inputs()


def check():
    value = json.loads((ROOT / REPORT).read_bytes())
    saved.bindings_fresh(ROOT, value['source_bindings'])
    need(value['analysis'] == analyze(*read_saved()), 'frame join report drift')
    need(value['task'] == TASK and value['focused_tests']['successful'] is True, 'unverified report')
    return value


def run():
    from datetime import datetime, timezone
    import unittest
    import pr16_resume as resume
    import pr16_ring_compiled_record as guard
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT / REPORT).exists(), 'already recorded; do not repeat')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'execution HEAD differs')
    need(subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head]).returncode == 0, 'wrong ancestry')
    pr = saved.api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head
         and pr['head']['ref'] == 'codex/modernization-followup-20260908'
         and pr['head']['repo']['full_name'] == os.environ['GITHUB_REPOSITORY'], 'PR boundary differs')
    state = resume.validate(ROOT)
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True
         and GAP in state['remaining_physical_gap_ids'], 'accepted scope changed')
    checkpoint = identity((ROOT / saved.CHECKPOINT).read_bytes())
    backlog = resume.load(ROOT, saved.BACKLOG)
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(GAP in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][GAP] is None,
         'Ring owner/acceptance changed')
    values = read_saved()
    bindings = {p: identity((ROOT / p).read_bytes()) for p in SOURCES}
    previous = []
    for run_id, source in ((34971661219, '27f29ff3ce6b26ca9b1ac439e29f655910d5eebd'),
                           (34968485915, '0449002040cefe9c7df01c2bf7804ea51fb16491'),
                           (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        r = saved.api('actions/runs/' + str(run_id))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == source,
             'prior Actions conclusion differs')
        previous.append({k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    runs = saved.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    observed = [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs]
    analysis = analyze(*values)
    suite = unittest.TestSuite()
    for pattern in ('test_pr16_ring_frame_join.py', 'test_pr16_resume.py'):
        suite.addTests(unittest.defaultTestLoader.discover('tests', pattern=pattern))
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
             'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'], 'focused tests failed')
    value = {'schema_version': 1, 'task': TASK, 'source_head': head,
             'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
             'analysis': analysis, 'focused_tests': tests, 'source_bindings': bindings,
             'reused_successful_actions': previous, 'actions_observed_before_record': observed}
    (ROOT / REPORT).write_bytes(stable(value))
    row['ring_frame_join'] = REPORT
    state['ring_frame_join'] = {'path': REPORT, 'source_head': head, 'run_id': value['run_id'],
        'priority_unread_targets': analysis['priority_unread_targets'], 'ring_acquisition_accepted': False}
    state['bp']['current_stop'] = state['source_change_review_ja'] = STOP
    state['bp']['next_step'] = state['next_action']['goal_ja'] = NEXT
    state['next_action']['read_paths'] = [REPORT, SELF, saved.REPORT, saved.ABI, saved.PATCH]
    state['observed_head'] = head
    state['observed_head_semantics'] = '保存済みgraphと継承frameを条件付き結合したsource HEAD。完了commit/run結論はremote ref/Actionsで確認する。'
    state['observed_head_checks']['reason_ja'] = (f'前回採取run34971661219、ABI run34968485915、BP run34946969126のcompleted/successを照合。'
        f'今回run{value["run_id"]}は保存時in_progress。通常CIのaction_requiredをsuccessへ読み替えない。最新snapshotは結合receiptへ保存。')
    state['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': 0, 'accepted_standalone_replays': 0,
        'scope_ja': '保存済み23命令の境界を結合。ROM再採取/decoder/15辺再分類/受入済みnative再実行0。'}
    note = 'FlagSet継続の継承frame結合は条件付きで完了。opaque callee 0x09097105のreturn/SP/r4/保存slotと返却pointer非aliasは未証明。結合を全owner除外やRing受入へ昇格せず、同一入力で単独再実行しない。'
    if note not in state['do_not_repeat']:
        state['do_not_repeat'].append(note)
    for p in (SELF, TEST, WORKFLOW, REPORT):
        state['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / saved.STATE).write_bytes(stable(state))
    (ROOT / saved.BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    before_check = {p: identity((ROOT / p).read_bytes()) for p in (REPORT, saved.STATE, saved.DOC, saved.BACKLOG)}
    check()
    need(before_check == {p: identity((ROOT / p).read_bytes()) for p in before_check}, 'check has write side effects')
    need(identity((ROOT / saved.CHECKPOINT).read_bytes()) == checkpoint, 'accepted checkpoint mutated')
    saved.bindings_fresh(ROOT, bindings)
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / FlagSet継承frameとcall/return境界の結合\n'
        '- Status: DONE / 限定結合の実装・検証・記録。Ring正規取得は未完。\n- Version: PR16 conditional frame join\n'
        '- Summary: ' + STOP + '\n'
        f'- Files changed: {SELF}, {TEST}, {WORKFLOW}, {REPORT}, 固定引継ぎMD/JSON、P08 Ring参照、両ログ。\n'
        f'- Verify: 新規結合/異常系と固定resume {tests["tests_run"]} tests PASS。render/check PASS、check読取専用、限定source hash/BP checkpoint全byte不変。task graph・最終index差分guard・diffを完了commit前の必須gateとする。\n'
        f'- Evidence: {REPORT}; source HEAD={head}; run={value["run_id"]}（保存時in_progress、最終結論はActionsで確認）。前回採取run34971661219はcompleted/successを照合済み。\n'
        '- Preserved: candidate ceddbe91 / CRC32 3EB17B36、旧18未読target、受入済みBP原本。ROM編集/再構築/新規decode/native/既存15辺再分類/受入済み単独再実行0。\n'
        '- Commit: この記録を含む同branchへの非force commit。自己SHAはremote refとresult artifactで確認。\n'
        '- Network: GitHub connector/Actionsでexact HEADと最新runを照合。container直接Git取得はDNS失敗。private入力復元・外部技術資料検索なし。\n'
        '- Boundary: 帰還はopaque calleeと非aliasの仮定付き。全体private guardの既存違反は前後一致・新規違反0を要求し全体PASSと混同しない。通常CI action_requiredをsuccessへ変更しない。merge/release/baseline変更なし。\n'
        '- Next: ' + NEXT + '\n')
    for p in saved.LOGS:
        need(TASK not in (ROOT / p).read_text(encoding='utf-8'), 'duplicate completion log')
        with (ROOT / p).open('a', encoding='utf-8') as stream:
            stream.write(entry)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], check=True)
    subprocess.run(['git', 'add', '--', *OUTPUTS], check=True)
    guard.BASE, guard.OUT, guard.ALLOWED = BASE, OUT, set((SELF, TEST, WORKFLOW, *OUTPUTS))
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    (OUT / 'summary.json').write_bytes(stable(analysis))
    print(json.dumps({'tests': tests, 'priority_unread_targets': analysis['priority_unread_targets'],
                      'conditional_return': analysis['conditional_return'], 'ring_acquisition_accepted': False}))


if __name__ == '__main__':
    if sys.argv[1:] == ['run']:
        run()
    elif sys.argv[1:] == ['check']:
        check()
        print('PASS_READ_ONLY_CONDITIONAL_FRAME_JOIN')
    else:
        raise SystemExit('usage: pr16_ring_frame_join.py run|check')
