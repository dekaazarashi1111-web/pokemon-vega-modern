#!/usr/bin/env python3
"""保存済みThumb graphの間接辺だけをABI/dataflow分類する。ROMは読まない。"""
from __future__ import annotations
from collections import Counter, deque
import copy
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
TASK = 'PR-P08-7-RING-INDIRECT-ABI'
BASE = '93635dcc022a12a794df67e2d16a739fe15b29fc'
SELF = 'scripts/pr16_ring_indirect_abi.py'
TEST = 'tests/test_pr16_ring_indirect_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-indirect-abi.yml'
REPORT = 'content/modernization/pr16_ring_indirect_abi.json'
PATCH = 'content/modernization/pr16_ring_patch_owner.json'
PRIOR = 'content/modernization/pr16_ring_transitive_owner.json'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)
ALLOWED = set((SELF, TEST, WORKFLOW, *OUTPUTS))
OUT = ROOT / '.local/pr16-ring-indirect-abi'
RETURN = ('entry-lr', 0)
UNKNOWN = None
NEXT = ('保存済み15間接辺の分類を再実行せず、次は未読の0x0806DE7D（live frameを受けるFlagSet継続）'
        'だけcandidate byteを採取する。QOL_FEATURE→0x0806DEC5は保存済みFlagGet graphを再利用し再採取しない。'
        '旧18未読targetは保持し必要なrootだけ進める。QOLのcompiler helper後のinline table/CFGも'
        '全経路網羅とは見なさない。callsite限定解決を全callerの解決へ昇格せず、'
        '全owner未除外のままRing story giftを新設しない。Ring正規取得・装備実戦・Save/fresh Continueは未受入。')


def need(value, message):
    if not value:
        raise ValueError(message)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def thumb(value):
    return type(value) is int and value & 1 and 0x08000000 <= (value & ~1) < 0x0A000000


def half(node):
    raw = bytes.fromhex(node['hex'])
    need(len(raw) == node['size'] and len(raw) in (2, 4), 'instruction size differs')
    return struct.unpack_from('<H', raw)[0]


def const(value):
    return ('const', value & 0xffffffff)


def initial():
    regs = [None] * 16
    regs[13], regs[14] = ('sp', 0), RETURN
    return tuple(regs), ()


def merge(left, right):
    need(left[0][13] == right[0][13], 'inconsistent stack depth at CFG join')
    regs = tuple(a if a == b else None for a, b in zip(left[0], right[0]))
    a, b = dict(left[1]), dict(right[1])
    slots = tuple(sorted((k, a[k] if a[k] == b[k] else None) for k in a.keys() & b.keys()))
    return regs, slots


def transfer(node, state):
    """AAPCS callee/SP保存を仮定。任意memory corruption不存在の証明ではない。"""
    regs, memory = list(state[0]), dict(state[1])
    sp = regs[13]
    need(sp is not None and sp[0] == 'sp', 'unknown SP')
    offset = sp[1]
    w, at = half(node), node['address']
    kind = node['kind']
    if kind == 'call':
        need(node['size'] == 4 and w & 0xf800 == 0xf000, 'unsupported call encoding')
        tail = int.from_bytes(bytes.fromhex(node['hex'])[2:], 'little')
        need(tail & 0xf800 == 0xf800, 'not Thumb-1 BL')
        delta = ((w & 0x7ff) << 12) | ((tail & 0x7ff) << 1)
        if delta & (1 << 22): delta -= 1 << 23
        need(node['target'] == at + 4 + delta, 'BL target differs')
        for r in (0, 1, 2, 3, 12, 14): regs[r] = None
    elif kind in ('jump', 'conditional', 'indirect', 'return'):
        if kind == 'indirect':
            need(w & 0xff87 == 0x4700 and (w >> 3) & 15 == node['register'], 'BX encoding differs')
        elif kind == 'jump':
            need(w & 0xf800 == 0xe000, 'unsupported jump')
        elif kind == 'conditional':
            need(w & 0xf000 == 0xd000 and (w >> 8) & 15 < 14, 'unsupported condition')
    elif w & 0xfe00 == 0xb400:
        selected = [r for r in range(8) if w & (1 << r)] + ([14] if w & 0x100 else [])
        need(selected, 'empty PUSH')
        offset -= 4 * len(selected)
        for i, r in enumerate(selected): memory[offset + i * 4] = regs[r]
        regs[13] = ('sp', offset)
    elif w & 0xfe00 == 0xbc00:
        need(not w & 0x100, 'unexpected nonterminal POP PC')
        selected = [r for r in range(8) if w & (1 << r)]
        need(selected, 'empty POP')
        for i, r in enumerate(selected): regs[r] = memory.pop(offset + i * 4, None)
        regs[13] = ('sp', offset + 4 * len(selected))
    elif w & 0xff00 == 0xb000:
        regs[13] = ('sp', offset + (-1 if w & 0x80 else 1) * (w & 127) * 4)
    elif w & 0xf800 == 0x4800:
        need(node.get('literal_address') == ((at + 4) & ~3) + (w & 255) * 4, 'literal address differs')
        need(type(node.get('literal_value')) is int, 'missing literal bytes')
        regs[(w >> 8) & 7] = const(node['literal_value'])
    elif w & 0xf000 == 0x9000:
        r, slot = (w >> 8) & 7, offset + (w & 255) * 4
        if w & 0x800: regs[r] = memory.get(slot)
        else: memory[slot] = regs[r]
    elif w & 0xf000 == 0xa000:
        regs[(w >> 8) & 7] = ('sp', offset + (w & 255) * 4) if w & 0x800 else const(((at + 4) & ~3) + (w & 255) * 4)
    elif w & 0xfc00 == 0x4400:
        op, rd, rs = (w >> 8) & 3, (w & 7) | ((w >> 4) & 8), (w >> 3) & 15
        need(op < 3 and rd != 15, 'unsupported high-register control transfer')
        if op != 1:
            need(rd != 13, 'unmodelled SP assignment')
            regs[rd] = regs[rs] if op == 2 else None
    elif w & 0xe000 == 0x0000:
        rd = w & 7
        if w & 0xf800 == 0x1800:
            src = regs[(w >> 3) & 7]
            other = const((w >> 6) & 7) if w & 0x400 else regs[(w >> 6) & 7]
            regs[rd] = src if other == const(0) else None
        else:
            src, amount, op = regs[(w >> 3) & 7], (w >> 6) & 31, (w >> 11) & 3
            regs[rd] = src if op == 0 and amount == 0 else None
            if src is not None and src[0] == 'const':
                if op == 0: regs[rd] = const(src[1] << amount)
                elif op == 1: regs[rd] = const(src[1] >> (amount or 32))
    elif w & 0xe000 == 0x2000:
        op, rd = (w >> 11) & 3, (w >> 8) & 7
        if op == 0: regs[rd] = const(w & 255)
        elif op != 1:
            old = regs[rd]
            regs[rd] = const(old[1] + (1 if op == 2 else -1) * (w & 255)) if old and old[0] == 'const' else None
    elif w & 0xfc00 == 0x4000:
        if (w >> 6) & 15 not in (8, 10, 11): regs[w & 7] = None
    elif w & 0xf000 in (0x5000, 0x6000, 0x7000, 0x8000):
        rd, base = w & 7, regs[(w >> 3) & 7]
        need(base is None or base[0] != 'sp', 'unmodelled stack-alias load/store')
        load = ((w >> 9) & 7) >= 3 if w & 0xf000 == 0x5000 else bool(w & 0x800)
        if load: regs[rd] = None
    elif w & 0xf000 == 0xc000:
        rn = (w >> 8) & 7
        need(regs[rn] is None or regs[rn][0] != 'sp', 'unmodelled stack-alias multiple transfer')
        if w & 0x800:
            for r in range(8):
                if w & (1 << r): regs[r] = None
        regs[rn] = None
    else:
        raise ValueError(f'unsupported ABI instruction at 0x{at:08X}: {node["hex"]}')
    return tuple(regs), tuple(sorted(memory.items()))


def validate_node(node):
    w, at, kind = half(node), node['address'], node['kind']
    need(type(at) is int and not at & 1, 'unaligned code address')
    if kind == 'conditional':
        delta = w & 255
        if delta & 128: delta -= 256
        target = at + 4 + delta * 2
        expected = [at + 2, target]
        need(node.get('target') == target, 'conditional target differs')
    elif kind == 'jump':
        delta = w & 0x7ff
        if delta & 0x400: delta -= 0x800
        target = at + 4 + delta * 2
        expected = [target]
        need(node.get('target') == target, 'jump target differs')
    elif kind in ('indirect', 'return'):
        expected = []
        if kind == 'return':
            need(w == 0x4770 or w & 0xff00 == 0xbd00, 'return encoding differs')
    else:
        need(kind in ('ordinary', 'call'), 'unknown instruction kind')
        expected = [at + node['size']]
    need(node['successors'] == expected, 'CFG successors differ from bytes')


def flow(graph):
    for node in graph['nodes']: validate_node(node)
    nodes = {n['address']: n for n in graph['nodes']}
    need(len(nodes) == len(graph['nodes']) and graph['entry'] & 1, 'invalid graph')
    entry = graph['entry'] & ~1
    need(entry in nodes, 'missing graph entry')
    states, queue, count = {entry: initial()}, deque([entry]), 0
    while queue:
        at = queue.popleft(); node = nodes[at]; count += 1
        need(count <= 4096, 'ABI dataflow budget exceeded')
        after = transfer(node, states[at])
        for dest in node['successors']:
            need(dest in nodes, 'missing CFG successor')
            joined = merge(states[dest], after) if dest in states else after
            if states.get(dest) != joined:
                states[dest] = joined; queue.append(dest)
    return states


def literal_chain(target, graphs):
    chain, seen = [], set()
    while target in graphs and target not in seen:
        seen.add(target); g = graphs[target]; ns = g['nodes']
        if len(ns) != 2: break
        a, b = ns; w, bx = half(a), half(b)
        if a['address'] != target & ~1 or b['address'] != a['address'] + 2: break
        if w & 0xf800 != 0x4800 or bx != 0x4700 | (((w >> 8) & 7) << 3): break
        transfer(a, initial())
        dest = a['literal_value']
        need(thumb(dest), 'invalid veneer target')
        chain.append({'entry': target, 'site': b['address'], 'target': dest})
        target = dest
    need(target not in {v['entry'] for v in chain}, 'veneer cycle')
    return chain, target


def analyze(patch, prior):
    """正本の15辺のみ分類。過去graphを再decodeせず、新しい到達網羅性を主張しない。"""
    current = {g['entry']: g for g in patch['frontier']['graphs']}
    graphs = {g['entry']: g for g in prior['native_owners'].values()}
    graphs.update(current)
    states = {entry: flow(g) for entry, g in graphs.items()}
    rows, new_targets = [], set()
    boundaries = patch['frontier']['remaining_boundaries']
    for edge in boundaries:
        if edge['reason'] != 'UNRESOLVED_INDIRECT': continue
        entry, site, reg = edge['owner'], edge['site'], edge['register']
        st = states[entry].get(site)
        need(st is not None, 'unreachable recorded indirect site')
        value = st[0][reg]
        row = {'owner': entry, 'site': site, 'register': reg, 'classification': 'UNRESOLVED',
               'frame_bytes': -st[0][13][1], 'entry_lr_saved_offsets': [k for k, v in st[1] if v == RETURN],
               'all_runtime_owners_excluded': False}
        if value == RETURN and st[0][13] == ('sp', 0):
            row.update(classification='ABI_SAVED_LR_RETURN', basis='ENTRY_LR_PUSH_POP_ALL_RECORDED_CFG_PATHS')
        elif value and value[0] == 'const' and thumb(value[1]):
            row.update(classification='LITERAL_BRANCH_LIVE_FRAME' if row['frame_bytes'] else 'LITERAL_BRANCH', target=value[1])
            if value[1] not in graphs: new_targets.add(value[1])
        elif len(graphs[entry]['nodes']) == 1 and reg == 3:
            callers = []
            for caller, g in graphs.items():
                for n in g['nodes']:
                    if n['kind'] != 'call' or n['target'] | 1 != entry: continue
                    state = states[caller].get(n['address'])
                    v = state[0][reg] if state else None
                    call = {'owner': caller, 'site': n['address'], 'target': None,
                            'return_address': (n['address'] + n['size']) | 1}
                    if v and v[0] == 'const' and thumb(v[1]):
                        chain, end = literal_chain(v[1], graphs)
                        call.update(target=v[1], reused_veneer_chain=chain, final_target=end,
                                    final_target_already_decoded=end in graphs)
                        if end not in graphs: new_targets.add(end)
                    callers.append(call)
            row.update(classification='CALLSITE_R3_TRAMPOLINE' if callers and all(c['target'] for c in callers) else 'UNRESOLVED',
                       observed_callers=callers, unseen_callers_excluded=False,
                       basis='RECORDED_CALLSITE_VALUES_ONLY_NOT_ALL_CALLERS')
        rows.append(row)
    old = sorted({b['target'] for b in boundaries if b['reason'] != 'UNRESOLVED_INDIRECT'})
    counts = dict(sorted(Counter(r['classification'] for r in rows).items()))
    return {'classification': 'RECORDED_INDIRECT_ABI_NOT_NATIVE_ACCEPTANCE', 'edges': rows,
            'counts': counts, 'classified_edges': sum(r['classification'] != 'UNRESOLVED' for r in rows),
            'old_unread_targets': old, 'additional_unread_targets': sorted(new_targets - set(old)),
            'remaining_unread_targets': sorted(set(old) | new_targets),
            'assumptions': ['AAPCS_CALLEE_PRESERVED_SP_AND_NONVOLATILE_REGISTERS',
                            'NO_MEMORY_CORRUPTION_OF_CALLER_FRAME_ASSUMED_NOT_PROVEN',
                            'RECORDED_CFG_ONLY_INLINE_TABLE_AND_UNSEEN_CALLERS_NOT_COVERED'],
            'new_graph_decodes': 0, 'candidate_reconstructions': 0, 'rom_changes': 0,
            'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0,
            'ring_acquisition_accepted': False, 'all_runtime_owners_excluded': False, 'release_ready': False}


def inputs():
    import pr16_ring_patch_record as record
    patch = record.validate_receipt(json.loads((ROOT / PATCH).read_bytes()))
    prior = json.loads((ROOT / PRIOR).read_bytes())
    return patch, prior


def project(state, backlog, result, head, run_id):
    need(result['counts'] == {'ABI_SAVED_LR_RETURN': 12, 'CALLSITE_R3_TRAMPOLINE': 2, 'LITERAL_BRANCH_LIVE_FRAME': 1}
         and result['additional_unread_targets'] == [0x0806DE7D], 'classification differs; review required')
    s, b = copy.deepcopy(state), copy.deepcopy(backlog)
    need(s['bp']['spending_accepted'] and s['latest_native_run'] == 34946969126, 'BP acceptance changed')
    gap = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
    need(gap in s['remaining_physical_gap_ids'], 'Ring already accepted')
    row = next(r for r in b['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(gap in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][gap] is None, 'Ring owner changed')
    row['ring_indirect_abi'] = REPORT
    s['ring_indirect_abi'] = {'path': REPORT, 'source_head': head, 'run_id': run_id,
        'counts': result['counts'], 'classified_edges': result['classified_edges'],
        'additional_unread_targets': result['additional_unread_targets'], 'ring_acquisition_accepted': False}
    stop = ('保存済み15間接辺をABI/dataflowで分類。12辺はentry LRのpush/popとSP復元を確認したABI return、'
            '2辺は記録済みcallsite限定R3 trampoline、1辺は8byte live frameを保持した0x0806DE7Dへの分岐。'
            'QOL_FEATURE→0x09376F45→0x0806DEC5、FlagSet→0x09377615→既存SAVE_FINALIZE veneer→0x093BDD7Dを結合。'
            '旧18未読targetは不変、新規未読1targetを明示。全caller・全ownerの網羅性、stack memory corruption不存在、'
            'Ring通常取得は未証明。BP正式受入run34946969126は不変。')
    s['bp']['current_stop'] = s['source_change_review_ja'] = stop
    s['bp']['next_step'] = s['next_action']['goal_ja'] = NEXT
    s['next_action']['read_paths'] = [REPORT, SELF, PATCH, PRIOR, 'overlays/save_migration/save_migration.c']
    s['observed_head'] = head
    s['observed_head_semantics'] = '保存済みgraphのABI分類を実行したsource HEAD。完了commitとrun結論はremote ref/Actionsで確認する。'
    s['observed_head_checks']['reason_ja'] = (f'ABI分類のsource-only検証run{run_id}を記録。保存時のrunは実行中で、'
        '最終conclusion/commitはActionsで照合する。開始HEADのsource-validation run34965203985はaction_required。'
        '自動CIのfailure/action_requiredと正式native受入を混同せず、新しいActions snapshotを分類receiptへ保存。')
    s['session_execution_summary'] = {k: result[k] for k in ('new_emulator_processes', 'rom_changes', 'candidate_reconstructions')}
    s['session_execution_summary'].update(accepted_standalone_replays=0, scope_ja='既存graph上の新規ABI分類のみ。byte採取・decode・候補生成・native実行0。')
    note = '15間接辺のABI分類12return/2callsite trampoline/1live-frame branchを同一入力で再実行しない。旧18未読targetと新1target、全caller/CFG/stack-integrityの仮定を保持し、Ring受入や全owner不存在へ昇格しない。'
    if note not in s['do_not_repeat']: s['do_not_repeat'].append(note)
    return s, b


def check():
    import pr16_resume as resume
    value = json.loads((ROOT / REPORT).read_bytes())
    need(value['analysis'] == analyze(*inputs()), 'ABI receipt projection differs')
    for name, binding in value['source_bindings'].items():
        need(identity((ROOT / name).read_bytes()) == binding, 'ABI source binding differs: ' + name)
    s = resume.validate(ROOT)
    need((ROOT / DOC).read_text(encoding='utf-8') == resume.render(s), 'resume rendering differs')
    need(project(s, resume.load(ROOT, BACKLOG), value['analysis'], value['source_head'], value['run_id']) == (s, resume.load(ROOT, BACKLOG)), 'resume ABI projection differs')
    return value


def run():
    import os
    import subprocess
    import sys
    import unittest
    from datetime import datetime, timezone
    import pr16_resume as resume
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT / REPORT).exists(), 'already recorded; do not repeat')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'execution HEAD differs')
    repo = os.environ['GITHUB_REPOSITORY']
    def api(path): return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + repo + '/' + path]))
    pr = api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head
         and pr['head']['ref'] == 'codex/modernization-followup-20260908' and pr['head']['repo']['full_name'] == repo, 'PR boundary differs')
    for run_id, source in ((34964225479, '03ca035d5617b4d381845189e15838b5ba495a7d'), (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        remote = api('actions/runs/' + str(run_id))
        need(remote['status'] == 'completed' and remote['conclusion'] == 'success' and remote['head_sha'] == source, 'prior Actions differs')
    observed = api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    actions = [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in observed]
    (OUT / 'actions-before.json').write_bytes(stable(actions))
    s = resume.validate(ROOT); backlog = resume.load(ROOT, BACKLOG)
    checkpoint_before = (ROOT / resume.CHECKPOINT).read_bytes()
    patch, prior = inputs(); result = analyze(patch, prior)
    need(result['counts'] == {'ABI_SAVED_LR_RETURN': 12, 'CALLSITE_R3_TRAMPOLINE': 2, 'LITERAL_BRANCH_LIVE_FRAME': 1}, 'unexpected classification; review instead of promoting')
    need(result['additional_unread_targets'] == [0x0806DE7D], 'unexpected next targets')
    suite = unittest.TestSuite()
    for pattern in ('test_pr16_ring_indirect_abi.py', 'test_pr16_resume.py'):
        suite.addTests(unittest.defaultTestLoader.discover('tests', pattern=pattern))
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors), 'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    print(json.dumps(tests)); need(tests['successful'], 'focused tests failed')
    run_id = int(os.environ['GITHUB_RUN_ID'])
    value = {'schema_version': 1, 'task': TASK, 'source_head': head, 'run_id': run_id,
        'run_status_at_record': 'in_progress', 'candidate': patch['candidate'], 'analysis': result,
        'focused_tests': tests, 'actions_observed_before_record': actions,
        'source_bindings': {p: identity((ROOT / p).read_bytes()) for p in (SELF, TEST, WORKFLOW, PATCH, PRIOR)},
        'reused_run_ids': [34964225479, 34960361700],
        'abi_reference': 'https://github.com/ARM-software/abi-aa/blob/main/aapcs32/aapcs32.rst'}
    (ROOT / REPORT).write_bytes(stable(value))
    s, backlog = project(s, backlog, result, head, run_id)
    for name in (SELF, TEST, WORKFLOW, REPORT): s['source_bindings'][name] = identity((ROOT / name).read_bytes())
    (ROOT / BACKLOG).write_bytes(stable(backlog)); (ROOT / STATE).write_bytes(stable(s))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    check()
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / 保存済み間接辺のABI分類\n'
        '- Status: DONE / 限定分類実装・検証・記録。Ring正規取得は未完。\n- Version: PR16 Ring recorded indirect ABI\n'
        '- Summary: 15辺を12 ABI saved-LR return、2記録callsite限定R3 trampoline、1live-frame literal branchへ分類。'
        'QOL→0x0806DEC5、FlagSet→SaveFinalize既存veneer、0x093789F3→0x0806DE7Dを追跡。旧18未読targetと新1targetを保持。\n'
        f'- Verify: 新規分類/異常系および固定resume {tests["tests_run"]} tests PASS、render/check PASS。task graph・最終index差分guard・diffは完了commit前の必須gate。\n'
        f'- Evidence: {REPORT}; source HEAD={head}; 実行run={run_id}（保存時in_progress、最終結論はActionsで照合）。\n'
        '- Preserved: ROM変更/候補生成/native/受入済み単独再実行/新規decodeすべて0。BP checkpointの全byteとcandidate ceddbe91/CRC3EB17B36不変。ABI stack-integrityは仮定でありruntime無副作用や全owner除外を主張しない。\n'
        '- Files changed: 新規classifier/tests/workflow/receipt、固定引継ぎMD/JSON、P08 Ring参照、両ログ。\n'
        '- Commit: この記録を含む同branchへの非force commit。自己SHAはremote refとresult artifactで確認。\n'
        '- Network: GitHub connector/Actions。container直接Git取得はDNS失敗、権限不足とは扱わない。検索語: site.github.com/ARM-software/abi-aa aapcs32 rst r0 r3 r12 lr subroutine call。'
        '一次資料: https://github.com/ARM-software/abi-aa/blob/main/aapcs32/aapcs32.rst ; call後r0-r3/r12/LRを未知化しSP/非揮発register保存をABI仮定とする。\n'
        '- Boundary: 開始HEADのsource-validation action_required/既存CI failureを成功へ読み替えない。既存全体private guard違反は前後一致を要求し、新規違反0を別検査。merge/release/baseline変更なし。\n'
        '- Next: ' + NEXT + '\n')
    for name in LOGS:
        need(TASK not in (ROOT / name).read_text(encoding='utf-8'), 'duplicate completion log')
        with (ROOT / name).open('a', encoding='utf-8') as stream: stream.write(entry)
    need((ROOT / resume.CHECKPOINT).read_bytes() == checkpoint_before, 'accepted checkpoint mutated')
    check()
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], check=True)
    subprocess.run(['git', 'add', '--', *OUTPUTS], check=True)
    import pr16_ring_compiled_record as previous
    previous.BASE, previous.OUT, previous.ALLOWED = BASE, OUT, ALLOWED
    previous.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    (OUT / 'analysis-summary.json').write_bytes(stable({'counts': result['counts'], 'new_targets': result['additional_unread_targets'], 'tests': tests}))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    if sys.argv[1:] == ['check']:
        check(); print('PASS_RECORDED_INDIRECT_ABI_NOT_NATIVE_ACCEPTANCE')
    elif sys.argv[1:] == ['run']:
        run()
    else:
        raise SystemExit('usage: pr16_ring_indirect_abi.py run|check')
