#!/usr/bin/env python3
"""成功済み入口を再走査せず、patch先/標準handlerの有限frontierだけ進める。"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TASK = 'PR-P08-7-RING-PATCH-OWNER'
SELF = 'scripts/pr16_ring_patch_owner.py'
TEST = 'tests/test_pr16_ring_patch_owner.py'
WORKFLOW = '.github/workflows/pr16-ring-patch-owner.yml'
REPORT = 'content/modernization/pr16_ring_patch_owner.json'
PRIOR = 'content/modernization/pr16_ring_transitive_owner.json'
OUT = ROOT / '.local/pr16-ring-patch-owner'
BASE = 0x08000000
SIZE = 33554432
MAX_ROOTS = 24
MAX_DEPTH = 2
PRIOR_ID = {'size': 34036, 'sha256': '2045f5f2d9b2f234f58b8c596121f26794ae578a220e960d38b4a2999ab51cb7'}
PATCHES = {'FlagSet': 0x093775C5, 'SAVE_FINALIZE': 0x093BDD7D}
HANDLER_OPS = (0x03, 0x66, 0x67, 0x6D)


def need(value, message):
    if not value:
        raise ValueError(message)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def safe(root, name):
    p = Path(name)
    need(not p.is_absolute() and '..' not in p.parts and '\\' not in name, 'unsafe source path')
    path = root / p
    need(not any(q.is_symlink() for q in (path, *path.parents)), 'symlink source path')
    return path


def pointer(value, size=SIZE):
    need(type(value) is int and value & 1 and BASE <= (value & ~1) < BASE + size - 1,
         'invalid Thumb target')
    return value


def veneer(graph):
    """LDR Rd,[PC,#imm]; BX Rd の正確な2命令だけ。任意の間接辺は推測しない。"""
    nodes = graph['nodes']
    if len(nodes) != 2:
        return None
    first, last = nodes
    at = graph['entry'] & ~1
    if first['address'] != at or last['address'] != at + 2:
        return None
    a, b = bytes.fromhex(first['hex']), bytes.fromhex(last['hex'])
    if len(a) != 2 or len(b) != 2:
        return None
    load, branch = struct.unpack('<H', a)[0], struct.unpack('<H', b)[0]
    if load & 0xF800 != 0x4800 or branch != 0x4700 | (((load >> 8) & 7) << 3):
        return None
    literal = ((at + 4) & ~3) + (load & 255) * 4
    need(first.get('literal_address') == literal and 'literal_value' in first, 'veneer literal binding differs')
    return {'site': last['address'], 'target': pointer(first['literal_value']),
            'literal_address': literal, 'register': (load >> 8) & 7,
            'basis': 'EXACT_LDR_LITERAL_BX_PAIR_NOT_GENERAL_INDIRECT_RESOLUTION'}


def engine_table(receipt):
    """記録済みSetupのr1/r2とInitScriptContext呼出しABIからtable範囲を照合。"""
    nodes = {n['address']: n for n in receipt['native_owners']['ScriptContextSetup']['nodes']}
    expected = {0x080693B6: '0949', 0x080693B8: '094a', 0x080693BA: '201c', 0x080693BC: 'fff756fe'}
    need(all(nodes.get(a, {}).get('hex') == h for a, h in expected.items()), 'script table setup ABI differs')
    need(nodes[0x080693BC].get('target') == 0x0806906C, 'InitScriptContext callee differs')
    table, end = nodes[0x080693B6]['literal_value'], nodes[0x080693B8]['literal_value']
    need((table, end) == (0x08162CC4, 0x08163010), 'script table bounds differ')
    need(tuple(sorted(n['opcode'] for n in receipt['standard_script']['nodes'])) == HANDLER_OPS,
         'reused callstd vocabulary differs')
    return table, end


def seeds(raw, receipt):
    result, patched = [], {}
    for name, expected in PATCHES.items():
        edge = veneer(receipt['native_owners'][name])
        need(edge is not None and edge['target'] == expected, 'recorded patch target differs: ' + name)
        patched[name] = edge
        result.append((edge['target'], 'patch:' + name))
    table, end = engine_table(receipt)
    handlers = {}
    for op in HANDLER_OPS:
        at = table + op * 4
        need(table <= at < end and at + 4 <= BASE + len(raw), 'handler table out of range')
        target = pointer(struct.unpack_from('<I', raw, at - BASE)[0], len(raw))
        handlers[f'{op:02X}'] = {'record': at, 'entry': target,
                                'pointer_hex': raw[at - BASE:at - BASE + 4].hex()}
        result.append((target, f'handler:{op:02X}'))
    for name, graph in receipt['native_owners'].items():
        for edge in graph['external_edges']:
            if edge.get('target') is not None:
                result.append((pointer(edge['target'], len(raw)), 'prior:' + name))
    return result, patched, handlers


def frontier(raw, initial, cached, decode, max_roots=MAX_ROOTS, max_depth=MAX_DEPTH):
    """BFS、根数/深さを固定。既存graphは読戻すだけ。unknownは未解決のまま残す。"""
    need(type(max_roots) is int and 1 <= max_roots <= MAX_ROOTS, 'invalid root bound')
    need(type(max_depth) is int and 0 <= max_depth <= MAX_DEPTH, 'invalid depth bound')
    queue = deque((pointer(p, len(raw)), label, 0) for p, label in initial)
    graphs, failures, reused, boundaries = {}, {}, set(), []
    while queue:
        entry, label, depth = queue.popleft()
        if entry in cached:
            reused.add(entry)
            continue
        if entry in graphs or entry in failures:
            continue
        if depth > max_depth or len(graphs) + len(failures) >= max_roots:
            boundaries.append({'owner': label, 'target': entry, 'reason': 'DEPTH_BOUND' if depth > max_depth else 'ROOT_BOUND'})
            continue
        try:
            graph = decode(raw, entry)
        except ValueError as exc:
            failures[entry] = {'entry': entry, 'reason': 'DECODER_STOP', 'detail': str(exc)[:180]}
            continue
        need(graph['entry'] == entry and graph.get('side_effects_excluded') is False, 'decoder scope differs')
        graphs[entry] = graph
        edges = list(graph['external_edges'])
        resolved = veneer(graph)
        if resolved is not None:
            graph['resolved_veneer'] = resolved
            edges = [e for e in edges if e['site'] != resolved['site']]
            edges.append(dict(resolved, kind='veneer'))
        for edge in edges:
            target = edge.get('target')
            if target is None:
                boundaries.append({'owner': entry, **edge, 'reason': 'UNRESOLVED_INDIRECT'})
            else:
                queue.append((pointer(target, len(raw)), f'0x{entry:08X}@0x{edge["site"]:08X}', depth + 1))
    # 後から別の浅い経路で到達した根は、未処理根数に重複計上しない。
    boundaries = [b for b in boundaries if b.get('target') not in graphs and b.get('target') not in cached]
    return {'graphs': list(graphs.values()), 'decoder_stops': list(failures.values()),
            'reused_entries': sorted(reused), 'remaining_boundaries': boundaries,
            'max_new_roots': max_roots, 'max_depth': max_depth,
            'side_effects_excluded': False}


def run(rom):
    sys.path.insert(0, str(ROOT / 'scripts'))
    import pr16_ring_transitive_owner as old
    import pr16_ring_transitive_record as saved
    receipt_bytes = safe(ROOT, PRIOR).read_bytes()
    need(identity(receipt_bytes) == PRIOR_ID, 'prior receipt bytes differ')
    receipt = saved.validate_receipt(json.loads(receipt_bytes))
    old.reuse(json.loads(safe(ROOT, old.prior.REPORT).read_bytes()))
    raw = rom.read_bytes()
    old.prior.exact_candidate(raw)
    initial, patched, handlers = seeds(raw, receipt)
    cached = {v['entry']: v for v in receipt['native_owners'].values()}
    result = frontier(raw, initial, cached, old.native_graph)
    decoded = {g['entry']: g for g in result['graphs']}
    primary_ok = (all(p in decoded for p in PATCHES.values())
                  and all(h['entry'] in decoded or h['entry'] in cached for h in handlers.values()))
    need(rom.read_bytes() == raw, 'read-only candidate changed')
    report = {'schema_version': 1, 'task': TASK,
        'classification': 'PATCH_AND_HANDLER_FRONTIER_NOT_NATIVE_ACCEPTANCE',
        'candidate': receipt['candidate'],
        'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'reused_prior': {'path': PRIOR, **PRIOR_ID, 'run_id': 34960361700,
                         'entry_graphs_rescanned': 0, 'callstd_script_rescanned': False},
        'patch_targets': patched, 'standard_handlers': handlers, 'frontier': result,
        'primary_roots_decoded': primary_ok,
        'ring_acquisition_accepted': False, 'all_runtime_owners_excluded': False,
        'release_ready': False, 'rom_changes': 0, 'new_emulator_processes': 0,
        'accepted_native_cases_replayed': 0, 'candidate_reconstructions': 1,
        'source_bindings': {n: identity(safe(ROOT, n).read_bytes()) for n in (SELF, TEST, WORKFLOW, PRIOR)}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'audit.json').write_bytes(stable(report))
    summary = {'patches': {k: hex(v['target']) for k, v in patched.items()},
        'handlers': {k: hex(v['entry']) for k, v in handlers.items()},
        'new_graphs': len(decoded), 'decoder_stops': len(result['decoder_stops']),
        'remaining_boundaries': len(result['remaining_boundaries']),
        'new_memory_write_sites': sum(len(g['memory_write_sites']) for g in decoded.values()),
        'ring_acquisition_accepted': False}
    (OUT / 'summary.json').write_bytes(stable(summary))
    print(json.dumps(summary))
    need(primary_ok, 'primary root decoding incomplete; partial audit retained')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    args = parser.parse_args()
    need(not any(p.is_symlink() for p in (args.rom, *args.rom.parents)), 'symlink candidate')
    run(args.rom)
