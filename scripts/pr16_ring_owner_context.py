#!/usr/bin/env python3
"""保存nodeをcallsiteへ結合する有限データフロー。native到達/ABI成立は主張しない。"""
from __future__ import annotations
from collections import deque
import copy
import hashlib
from pathlib import Path
import sys

BASE = '1656ebba8d9237f9fbe5a1c1980a73a796326ea4'
SLUG = 'pr16-ring-owner-context'
TASK = 'PR-P08-7-RING-OWNER-CONTEXT'
TITLE = '保存18targetを実callsiteの引数・中継先・保存境界へ結合'
SELF = 'scripts/pr16_ring_owner_context.py'
TEST = 'tests/test_pr16_ring_owner_context.py'
WORKFLOW = '.github/workflows/pr16-ring-owner-context.yml'
PRIOR = 'content/modernization/pr16_ring_owner_frontier.json'
PATCH = 'content/modernization/pr16_ring_patch_owner.json'
LEAP = 'content/modernization/pr16_ring_leap_contracts.json'
REPORT = 'content/modernization/pr16_ring_owner_context.json'
KEY = 'latest_ring_diagnostic'
SOURCES = (PATCH, LEAP, 'scripts/pr16_ring_flagset_continuation.py')
EXTRA_CODE = ()
MIN_TESTS = 40
NO_REPEAT = ('保存18targetのcallsite結合を再利用。中継先の定数とcallee帰還/SP/保存register仮定を区別する。'
             'ROM/native再採取や受入済みBPを単独再実行しない。未解決caller・jump table・calleeを残す。')
TOP = ('unknown',)
MASK = 0xffffffff


def need(ok, message):
    if not ok:
        raise ValueError(message)


def expr(op, a, b=None):
    if a == TOP or b == TOP:
        return TOP
    if isinstance(a, int) and (b is None or isinstance(b, int)):
        if op == 'add': return (a + b) & MASK
        if op == 'sub': return (a - b) & MASK
        if op == 'and': return a & b
        if op == 'or': return a | b
        if op == 'xor': return a ^ b
        if op == 'mul': return (a * b) & MASK
        if op == 'lsl': return (a << b) & MASK if b < 32 else 0
        if op == 'lsr': return a >> b if b < 32 else 0
        if op == 'asr': return ((a if a < 0x80000000 else a - 0x100000000) >> min(b, 32)) & MASK
        if op == 'neg': return -a & MASK
        if op == 'not': return ~a & MASK
    if b == 0 and op in ('add', 'sub', 'lsl', 'lsr', 'asr', 'or', 'xor'):
        return a
    value = (op, a) if b is None else (op, a, b)
    return TOP if len(repr(value)) > 256 else value


def show(value):
    if isinstance(value, int): return f'0x{value:08X}'
    if value == TOP: return 'UNKNOWN'
    return str(value)


def node_map(nodes):
    result = {}; occupied = set()
    for node in nodes:
        at, size = node['address'], node['size']
        raw = bytes.fromhex(node['hex'])
        need(type(at) is int and not at & 1 and size in (2, 4) and len(raw) == size, 'node境界')
        if at in result:
            need(result[at] == node, 'node矛盾')
            continue
        need(not occupied.intersection(range(at, at + size)), '命令重複')
        occupied.update(range(at, at + size)); result[at] = copy.deepcopy(node)
    return result


def transfer(node, before):
    """保存済Thumb nodeのregister効果のみ。未知命令は停止し、memory aliasは証明しない。"""
    r = list(before); h = int.from_bytes(bytes.fromhex(node['hex'])[:2], 'little')
    pc = node['address']; rd = h & 7; rs = (h >> 3) & 7
    if h & 0xf800 == 0x1800:
        imm, sub = bool(h & 0x400), bool(h & 0x200)
        x = (h >> 6) & 7
        r[rd] = expr('sub' if sub else 'add', r[rs], x if imm else r[x])
    elif h & 0xe000 == 0:
        op = (h >> 11) & 3; amount = (h >> 6) & 31
        need(op < 3, 'shift opcode')
        r[rd] = expr(('lsl', 'lsr', 'asr')[op], r[rs], amount or (0 if op == 0 else 32))
    elif h & 0xe000 == 0x2000:
        reg = (h >> 8) & 7; op = (h >> 11) & 3; imm = h & 255
        if op == 0: r[reg] = imm
        elif op != 1: r[reg] = expr('add' if op == 2 else 'sub', r[reg], imm)
    elif h & 0xfc00 == 0x4000:
        op = (h >> 6) & 15
        binary = {0:'and', 1:'xor', 2:'lsl', 3:'lsr', 4:'asr', 12:'or', 13:'mul'}
        if op in binary: r[rd] = expr(binary[op], r[rd], r[rs])
        elif op == 9: r[rd] = expr('neg', r[rs])
        elif op == 14: r[rd] = expr('and', r[rd], expr('not', r[rs]))
        elif op == 15: r[rd] = expr('not', r[rs])
        elif op not in (8, 10, 11): r[rd] = TOP
    elif h & 0xfc00 == 0x4400:
        dst = rd | ((h >> 4) & 8); src = (h >> 3) & 15; op = (h >> 8) & 3
        need(op != 3 and dst != 15, '間接branchはtransfer対象外')
        if op == 0: r[dst] = expr('add', r[dst], r[src])
        elif op == 2: r[dst] = r[src]
    elif h & 0xf800 == 0x4800:
        pool = ((pc + 4) & ~3) + (h & 255) * 4
        need(node.get('literal_address') == pool and type(node.get('literal_value')) is int, 'literal結合')
        need(0 <= node['literal_value'] <= MASK, 'literal範囲')
        r[(h >> 8) & 7] = node['literal_value']
    elif h & 0xf000 == 0x5000:
        op = (h >> 9) & 7; address = expr('add', r[rs], r[(h >> 6) & 7])
        if op >= 3: r[rd] = ('load', pc, (8,32,16,8,16)[op-3], address)
    elif h & 0xe000 == 0x6000:
        byte = bool(h & 0x1000); offset = ((h >> 6) & 31) * (1 if byte else 4)
        if h & 0x800: r[rd] = ('load', pc, 8 if byte else 32, expr('add', r[rs], offset))
    elif h & 0xf000 == 0x8000:
        if h & 0x800: r[rd] = ('load', pc, 16, expr('add', r[rs], ((h >> 6) & 31) * 2))
    elif h & 0xf000 == 0x9000:
        if h & 0x800: r[(h >> 8) & 7] = TOP
    elif h & 0xf000 == 0xa000:
        r[(h >> 8) & 7] = TOP if h & 0x800 else (((pc + 4) & ~3) + (h & 255) * 4)
    elif h & 0xf600 == 0xb400:
        if h & 0x800:
            for i in range(8):
                if h & (1 << i): r[i] = TOP
    elif h & 0xff00 == 0xb000:
        r[13] = TOP
    else:
        raise ValueError(f'未対応register効果 {pc:08X}')
    return tuple(r)


def join(old, new):
    if old is None: return new
    regs = tuple(a if a == b else TOP for a, b in zip(old[0], new[0]))
    return regs, old[1] | new[1]


def contexts(graph, max_steps=20000):
    """CFG固定点。条件分岐は両辺を残す過大近似。call後の保存仮定を明示する。"""
    need(type(max_steps) is int and 1 <= max_steps <= 20000, '資源上限')
    nodes = node_map(graph['nodes']); root = graph['entry'] & ~1
    need(root in nodes, 'owner入口欠落')
    initial = (tuple(('entry', i) for i in range(16)), frozenset())
    states = {root: initial}; pending = deque([root]); calls = {}; stops = {}; steps = 0
    def enqueue(at, state):
        if at not in nodes:
            stops[(at, 'saved_graph_boundary')] = {'site':at, 'kind':'saved_graph_boundary'}
            return
        merged = join(states.get(at), state)
        if merged != states.get(at): states[at] = merged; pending.append(at)
    while pending:
        steps += 1; need(steps <= max_steps, 'CFG資源上限')
        pc = pending.popleft(); n = nodes[pc]; regs, requirements = states[pc]
        kind = n['kind']; raw = bytes.fromhex(n['hex']); h = int.from_bytes(raw[:2], 'little')
        if kind == 'call':
            need(len(raw) == 4 and h & 0xf800 == 0xf000, 'call形式')
            lo = int.from_bytes(raw[2:], 'little'); need(lo & 0xf800 == 0xf800, 'call下位')
            hi = h & 0x7ff; hi = hi - 0x800 if hi & 0x400 else hi
            target = pc + 4 + (hi << 12) + ((lo & 0x7ff) << 1)
            need(target == n['target'], 'call target不一致')
            calls[pc] = {'site':pc, 'target':target | 1, 'registers':regs, 'requirements':requirements}
            req = requirements | {f'callee@0x{pc:08X}: returns/SP/frame/r4-r11 preservation NOT PROVEN'}
            after = list(regs)
            after[:4] = [('call_result', pc), TOP, TOP, TOP]; after[12] = TOP; after[14] = pc + 5
            enqueue(pc + 4, (tuple(after), req))
        elif kind in ('return', 'indirect'):
            stops[(pc, kind)] = {'site':pc, 'kind':kind}
        elif kind in ('jump', 'conditional'):
            need(len(raw) == 2, 'branch長')
            if kind == 'jump':
                need(h & 0xf800 == 0xe000, 'jump形式')
                d = h & 0x7ff; d = d - 0x800 if d & 0x400 else d
            else:
                need(h & 0xf000 == 0xd000 and (h >> 8) & 15 < 14, 'conditional形式')
                d = h & 255; d = d - 256 if d & 128 else d
            need(pc + 4 + 2*d == n['target'], 'branch target不一致')
            enqueue(n['target'], (regs, requirements))
            if kind == 'conditional': enqueue(pc + 2, (regs, requirements))
        else:
            try: after = transfer(n, regs)
            except ValueError:
                stops[(pc, 'unsupported_effect')] = {'site':pc, 'kind':'unsupported_effect'}
                continue
            enqueue(pc + n['size'], (after, requirements))
    return {'calls':calls, 'stops':list(stops.values()), 'states':states, 'iterations':steps}


def bind(frontier, patch):
    roots = frontier['roots']; new = node_map(frontier['new_nodes'])
    graphs = patch['frontier']['graphs']
    owners = {g['entry']:g for g in graphs}
    need(len(owners) == len(graphs), 'owner重複')
    flows = {entry:contexts(g) for entry,g in owners.items()}
    rows = []; targets = set(); linked_calls = []
    for row in roots:
        entry = row['entry']; body = [new[a] for a in row['new_node_addresses']]
        origins = frontier['saved_origins'][str(entry)]; links = []
        trampoline = None
        if len(body) == 1 and body[0]['kind'] == 'indirect':
            h = int.from_bytes(bytes.fromhex(body[0]['hex']), 'little')
            need(h & 0xff87 == 0x4700, 'BX中継形式')
            trampoline = (h >> 3) & 15
        for origin in origins:
            flow = flows[origin['owner']]; site = origin['site']
            need(site in flow['calls'], 'callsite到達データ欠落')
            call = flow['calls'][site]; need(call['target'] == entry, 'origin target不一致')
            resolved = call['registers'][trampoline] if trampoline is not None else None
            if type(resolved) is not int: resolved = None
            if resolved is not None:
                need(resolved & 1 and 0x08000000 <= resolved < 0x0a000000, 'Thumb宛先境界')
                targets.add(resolved)
            links.append({'owner':origin['owner'], 'site':site,
                'arguments':{f'r{i}':show(call['registers'][i]) for i in range(4)},
                'branch_register':trampoline, 'resolved_target':resolved,
                'binding_basis':'SAVED_CFG_REGISTER_FLOW_WITH_EXPLICIT_ABI_PRECONDITIONS',
                'required_unproven_abi':sorted(call['requirements']),
                'runtime_reachable':False, 'callee_abi_proven':False})
        for boundary in row['boundaries']:
            if boundary['kind'] == 'unread_call' and boundary['target'] in owners:
                linked_calls.append({'root':entry, 'site':boundary['site'], 'target':boundary['target'],
                    'saved_graph_reused':True, 'callee_contract_proven':False})
        rows.append({'entry':entry, 'saved_node_count':len(body), 'callsite_bindings':links,
            'trampoline_register':trampoline, 'memory_write_sites':[n['address'] for n in body if n['memory_write']],
            'boundaries_retained':copy.deepcopy(row['boundaries']),
            'return_opcode_is_not_frame_proof':True, 'side_effects_excluded':False})
    return {'rows':rows, 'old_target_count':len(rows), 'bound_callsite_count':sum(len(r['callsite_bindings']) for r in rows),
        'trampoline_callsite_count':sum(len(r['callsite_bindings']) for r in rows if r['trampoline_register'] is not None),
        'resolved_trampoline_targets':sorted(targets), 'saved_callee_links':linked_calls,
        'origin_missing_targets':[r['entry'] for r in rows if not r['callsite_bindings']],
        'owner_cfg_stops':{str(k):v['stops'] for k,v in flows.items()},
        'branch_feasibility_proven':False, 'all_callers_resolved':False, 'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False, 'ring_acquisition_accepted':False, 'release_ready':False,
        'rom_changes':0, 'new_emulator_processes':0, 'accepted_native_cases_replayed':0,
        'candidate_reconstructions':0, 'new_byte_samples':0, 'prior_graph_decoders_replayed':0}


def analyze(prior, out):
    import pr16_ring_followup_v2 as support
    import pr16_ring_flagset_continuation as saved
    patch = support.load(PATCH)
    saved.bindings_fresh(support.ROOT, patch['source_bindings'])
    result = bind(prior['analysis'], patch)
    need(result['old_target_count'] == 18 and result['bound_callsite_count'] == 21, '18target/21callsite差分')
    need(result['trampoline_callsite_count'] == 9 and len(result['saved_callee_links']) == 3, '中継/保存callee差分')
    result['candidate'] = copy.deepcopy(support.CANDIDATE)
    result['classification'] = 'SAVED_OWNER_CALLSITE_BINDINGS_NOT_NATIVE_OR_UNCONDITIONAL_ABI_ACCEPTANCE'
    (out / 'analysis.json').write_bytes(support.stable(result))
    return result


def summaries(result):
    return (f'保存18targetを{result["bound_callsite_count"]}実callsiteへ結合。9中継callsiteの宛先5種、保存済callee3辺を明示。'
            '帰還/SP/frame/保存registerの未証明仮定と未読境界は維持。候補復元/ROM変更/native再実行0。',
            '保存nodeの書込・copy/hash/LE32・initializerを実引数と結合して限定契約を検証する。'
            '中継先5種のうち既読FlagGet等を再採取せず、新規実体だけを追う。'
            'computed jump、2未読callee、窓外継続、caller/pointer/size/LIMITとRing正規取得・実戦保存は未受入。')


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:] == ['run'], 'runだけを許可')
    support.run(sys.modules[__name__])
