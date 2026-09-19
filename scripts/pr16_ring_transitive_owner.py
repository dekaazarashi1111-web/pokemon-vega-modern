#!/usr/bin/env python3
"""Ring未解決calleeの有限byte監査。通常取得/全owner不存在を主張しない。

既存compiled receiptはfreshnessを検査して再利用し、map/event再compileや
native受入を再実行しない。未知命令は停止し、間接分岐/領域外の先を推測しない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_compiled_owner as prior

TASK = 'PR-P08-7-RING-TRANSITIVE-OWNER'
SELF = 'scripts/pr16_ring_transitive_owner.py'
TEST = 'tests/test_pr16_ring_transitive_owner.py'
WORKFLOW = '.github/workflows/pr16-ring-transitive-owner.yml'
REPORT = 'content/modernization/pr16_ring_transitive_owner.json'
OUT = ROOT / '.local/pr16-ring-transitive-owner'
BASE = prior.BASE
STANDARD_TABLE = 0x08163758  # pinned tools/stage61_interaction_oracle.py ABI
STANDARD_INDEX = 4
STANDARD_LIMIT = 64
NATIVE_WINDOW = 1024
NATIVE_LIMIT = 512
# Only the message/lock/return vocabulary is admitted. No call/native/special,
# giveitem/setflag, guessed instruction length, or byte resynchronization.
STANDARD_OPS = {0x03: ('return', 1), 0x5A: ('faceplayer', 1),
                0x66: ('waitmessage', 1), 0x67: ('message', 5),
                0x68: ('closemessage', 1), 0x69: ('lockall', 1),
                0x6A: ('lock', 1), 0x6B: ('releaseall', 1),
                0x6C: ('release', 1), 0x6D: ('waitbuttonpress', 1)}
MACROS = ('EVENT_DESIGN_QOL_FEATURE_ADDRESS', 'EVENT_DESIGN_QOL_DISPATCH_ADDRESS',
          'EVENT_DESIGN_TRAINER_DEFEATED_ADDRESS', 'EVENT_DESIGN_SAVE_FINALIZE_ADDRESS')
need, stable, identity, span, u32 = prior.need, prior.stable, prior.identity, prior.span, prior.u32


def safe(path: Path) -> Path:
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink path rejected')
    return path


def reuse(receipt: dict, root: Path = ROOT) -> dict:
    """Revalidate only identity/bindings, never re-run the accepted auditor."""
    need(receipt.get('task') == prior.TASK, 'wrong compiled receipt')
    need(receipt.get('classification') == 'COMPILED_OWNER_BOUNDARY_NOT_NATIVE_ACCEPTANCE', 'wrong compiled scope')
    need(receipt.get('candidate') == prior.CANDIDATE, 'candidate binding differs')
    need(receipt.get('compiled_event_runtime_verified') is True
         and receipt.get('candidate_bytes_checked') is True, 'missing compiled proof')
    need(receipt.get('ring_acquisition_accepted') is False
         and receipt.get('all_runtime_owners_excluded') is False, 'unsupported prior acceptance')
    v = receipt['verification']
    need(v['run']['status'] == v['job']['status'] == 'completed'
         and v['run']['conclusion'] == v['job']['conclusion'] == 'success', 'compiled run not successful')
    need(v['run']['head_sha'] == receipt['source_head']
         and v['job']['run_id'] == v['run']['id']
         and v['artifact']['run_id'] == v['run']['id']
         and v['artifact']['head_sha'] == receipt['source_head'], 'compiled provenance mismatch')
    need(set(receipt['source_bindings']) == set(prior.SOURCES), 'incomplete compiled bindings')
    for name, binding in receipt['source_bindings'].items():
        p = Path(name)
        need(not p.is_absolute() and '..' not in p.parts, 'unsafe source binding')
        need(identity(safe(root / p).read_bytes()) == binding, 'stale compiled source: ' + name)
    need(receipt['external_owners_not_excluded'] == [{'kind': 'standard_script', 'target': 4}], 'standard boundary moved')
    return {'path': prior.REPORT, 'source_head': receipt['source_head'],
            'run_id': v['run']['id'], 'artifact': v['artifact'],
            'compiled_runtime': receipt['compiled_runtime'], 'recompiled': False,
            'map_graph_rescanned': False}


def header_values(data: bytes, expected: dict) -> dict:
    need(identity(data) == expected, 'generated header binding differs')
    text = data.decode('utf-8')
    values = {}
    for name in (*MACROS, 'EVENT_DESIGN_STATE_DAYCARE_COMPLETE',
                 'EVENT_DESIGN_STATE_KANTO_LEAGUE_CLEAR', 'EVENT_DESIGN_STATE_FINAL_LEAGUE_CLEARED'):
        rows = re.findall(r'^#define ' + re.escape(name) + r' (0x[0-9A-Fa-f]+|[0-9]+)u$', text, re.M)
        need(len(rows) == 1, 'missing/duplicate header macro: ' + name)
        values[name] = int(rows[0], 0)
    need(all(values[k] & 1 and BASE <= (values[k] & ~1) < BASE + prior.CANDIDATE['size'] for k in MACROS), 'invalid native header pointer')
    return values


def standard_script(raw: bytes, table: int = STANDARD_TABLE, limit: int = STANDARD_LIMIT) -> dict:
    need(type(limit) is int and 1 <= limit <= STANDARD_LIMIT, 'invalid standard bound')
    need(type(table) is int and table % 4 == 0, 'unaligned standard table')
    record = table + 4 * STANDARD_INDEX
    root = u32(raw, record)
    # Scripts are bytecode, not Thumb functions: do NOT clear the low address bit.
    span(raw, root, 1)
    at, nodes, messages = root, [], 0
    for _ in range(limit):
        op = span(raw, at, 1)[0]
        need(op in STANDARD_OPS, f'unreviewed callstd4 opcode 0x{op:02X} at 0x{at:08X}')
        name, size = STANDARD_OPS[op]
        data = span(raw, at, size)
        row = {'address': at, 'opcode': op, 'command': name, 'hex': data.hex()}
        if op == 0x67:
            need(u32(raw, at + 1) == 0, 'callstd4 must use caller loadword0 text')
            row['text_owner'] = 'caller_loadword0'
            messages += 1
        nodes.append(row)
        at += size
        if op == 0x03:
            need(messages == 1, 'missing/duplicate caller message')
            need(any(n['opcode'] == 0x66 for n in nodes) and any(n['opcode'] == 0x6D for n in nodes), 'missing message/button waits')
            return {'table': table, 'index': STANDARD_INDEX, 'record': record, 'target': root,
                    'pointer_hex': span(raw, record, 4).hex(), 'nodes': nodes,
                    'bytes': identity(span(raw, root, at - root)),
                    'script_layer_gift_or_native_commands': [],
                    'scope': 'MESSAGE_SCRIPT_VOCABULARY_ONLY_ENGINE_HANDLERS_NOT_EXCLUDED'}
    raise ValueError('callstd4 bound exceeded without return')


def signed(value: int, bits: int) -> int:
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def thumb_instruction(raw: bytes, at: int) -> dict:
    """ARM7TDMI Thumb-1 control-flow decoder (not a disassembler/emulator).

    Every memory write remains visible; a call-free function is NOT assumed
    side-effect-free. BX/high-register PC writes stay unresolved boundaries.
    """
    need(type(at) is int and at % 2 == 0, 'unaligned Thumb instruction')
    half = struct.unpack('<H', span(raw, at, 2))[0]
    row = {'address': at, 'size': 2, 'hex': span(raw, at, 2).hex(), 'kind': 'ordinary'}
    if half & 0xF800 == 0xF000:
        second = struct.unpack('<H', span(raw, at + 2, 2))[0]
        need(second & 0xF800 == 0xF800, 'invalid Thumb-1 BL suffix')
        row.update(size=4, hex=span(raw, at, 4).hex(), kind='call',
                   target=at + 4 + (signed(half & 0x7FF, 11) << 12) + ((second & 0x7FF) << 1))
    elif half & 0xF800 == 0xE000:
        row.update(kind='jump', target=at + 4 + (signed(half & 0x7FF, 11) << 1))
    elif half & 0xF000 == 0xD000:
        condition = (half >> 8) & 15
        need(condition < 14, 'SWI/undefined Thumb control boundary')
        row.update(kind='conditional', target=at + 4 + (signed(half & 255, 8) << 1))
    elif half & 0xFC00 == 0x4400:
        operation = (half >> 8) & 3
        rd = (half & 7) | ((half >> 4) & 8)
        rs = (half >> 3) & 15
        if operation == 3:
            need(half & 0x0087 == 0, 'BLX/reserved BX encoding unsupported on ARM7')
            row.update(kind='return' if rs == 14 else 'indirect', register=rs)
        elif operation in (0, 2) and rd == 15:
            row.update(kind='indirect', register=rs)
    elif half & 0xFE00 == 0xBC00:
        need(half & 0x1FF != 0, 'empty POP')
        if half & 0x100:
            row['kind'] = 'return'
    elif half & 0xFE00 == 0xB400:
        need(half & 0x1FF != 0, 'empty PUSH')
    elif half & 0xF000 == 0xC000:
        need(half & 255 != 0, 'empty STM/LDM')
    elif half & 0xF800 == 0x4800:
        address = ((at + 4) & ~3) + (half & 255) * 4
        row.update(literal_address=address, literal_value=u32(raw, address))
    elif half < 0x4400 or 0x5000 <= half < 0xB000 or half & 0xFF00 == 0xB000:
        pass
    else:
        raise ValueError(f'unknown Thumb-1 encoding 0x{half:04X} at 0x{at:08X}')
    # STR/STRH/STRB (immediate, register or SP-relative). Keep writes as unresolved
    # side effects, never promote lack of BL into an absence-of-giver proof.
    register_store = half & 0xF000 == 0x5000 and ((half >> 9) & 7) in (0, 1, 2)
    immediate_store = half & 0xE000 == 0x6000 and not half & 0x0800
    halfword_store = half & 0xF800 == 0x8000
    sp_store = half & 0xF800 == 0x9000
    row['memory_write'] = bool(register_store or immediate_store or halfword_store or sp_store
                               or half & 0xF800 == 0xC000 or half & 0xFE00 == 0xB400)
    return row


def native_graph(raw: bytes, pointer: int, window: int = NATIVE_WINDOW,
                 limit: int = NATIVE_LIMIT) -> dict:
    need(type(pointer) is int and pointer & 1, 'non-Thumb native root')
    need(type(window) is int and 2 <= window <= NATIVE_WINDOW and window % 2 == 0, 'invalid native window')
    need(type(limit) is int and 1 <= limit <= NATIVE_LIMIT, 'invalid native bound')
    root = pointer & ~1
    span(raw, root, window)
    pending, nodes, occupied, edges = [root], {}, {}, []
    while pending:
        at = pending.pop()
        if at in nodes:
            continue
        need(root <= at < root + window, 'native root/branch escaped window')
        need(at not in occupied, 'native branch into instruction operand')
        need(len(nodes) < limit, 'native graph bound exceeded')
        row = thumb_instruction(raw, at)
        need(at + row['size'] <= root + window, 'native instruction truncated at window')
        need(not any(x in occupied for x in range(at, at + row['size'])), 'overlapping Thumb instructions')
        kind, next_pc = row['kind'], at + row['size']
        successors = [] if kind in ('return', 'indirect', 'jump') else [next_pc]
        if kind in ('call', 'jump', 'conditional'):
            target = row['target']
            need(target % 2 == 0, 'unaligned native target')
            span(raw, target, 2)
            if kind == 'call' or not root <= target < root + window:
                edges.append({'site': at, 'kind': kind, 'target': target | 1,
                              'resolved_to_code_address_only': True})
            else:
                successors.append(target)
        if kind == 'indirect':
            edges.append({'site': at, 'kind': kind, 'register': row['register'], 'target': None})
        for target in successors:
            if root <= target < root + window:
                pending.append(target)
            else:
                edges.append({'site': at, 'kind': 'window_fallthrough', 'target': target | 1})
        row['successors'] = successors
        nodes[at] = row
        occupied.update({x: at for x in range(at, at + row['size'])})
    return {'entry': pointer, 'window': window, 'window_identity': identity(span(raw, root, window)),
            'nodes': [nodes[x] for x in sorted(nodes)],
            'external_edges': sorted(edges, key=lambda x: (x['site'], x['kind'])),
            'memory_write_sites': sorted(x for x, n in nodes.items() if n['memory_write']),
            'side_effects_excluded': False}


def audit(raw: bytes, header: bytes, receipt: dict, root: Path = ROOT) -> dict:
    prior.exact_candidate(raw)
    reused = reuse(receipt, root)
    values = header_values(header, receipt['generated_header'])
    need(values['EVENT_DESIGN_STATE_KANTO_LEAGUE_CLEAR'] == 74
         and values['EVENT_DESIGN_STATE_FINAL_LEAGUE_CLEARED'] == 79, 'Ring state input drift')
    # Both are actual SetState arguments from the reused candidate graph.
    state_calls = [n for n in receipt['script_nodes'] if n['opcode'] == 0x16 and n.get('value') in (74, 79)]
    need(len(state_calls) == 2 and all(n['variable'] == 0x8000 for n in state_calls), 'SetState arguments differ')
    need(values['EVENT_DESIGN_STATE_DAYCARE_COMPLETE'] not in (74, 79), 'QOL dispatch can no longer be pruned')
    roots = {'FlagGet': 0x0806DEC5, 'FlagSet': 0x0806DE75,
             'ScriptContextSetup': 0x080693A5,
             **{name.removeprefix('EVENT_DESIGN_').removesuffix('_ADDRESS'): values[name] for name in MACROS
                if name != 'EVENT_DESIGN_QOL_DISPATCH_ADDRESS'}}
    # One function per unresolved imported owner. Transitive targets are output,
    # not recursively guessed/scanned across all ROM allocations.
    natives = {name: native_graph(raw, pointer) for name, pointer in roots.items()}
    return {'schema_version': 1, 'task': TASK,
            'classification': 'TRANSITIVE_CALLEE_BOUNDARY_NOT_NATIVE_ACCEPTANCE',
            'candidate': prior.CANDIDATE, 'reused_compiled_owner': reused,
            'standard_script': standard_script(raw), 'header_values': values,
            'pruned': [{'owner': 'QOL_DISPATCH', 'only_guard': 'STATE_DAYCARE_COMPLETE',
                        'guard_value': values['EVENT_DESIGN_STATE_DAYCARE_COMPLETE'],
                        'actual_setstate_inputs': [74, 79],
                        'scope': 'SetState daycare branch only; QOL_FEATURE is not excluded'}],
            'native_owners': natives,
            'all_runtime_owners_excluded': False, 'ring_acquisition_accepted': False,
            'release_ready': False, 'new_emulator_processes': 0,
            'accepted_native_cases_replayed': 0, 'rom_changes': 0,
            'candidate_reconstructions': 1, 'compiled_owner_recompilations': 0}


def run(rom: Path, header: Path) -> dict:
    raw, generated = safe(rom).read_bytes(), safe(header).read_bytes()
    receipt = json.loads(safe(ROOT / prior.REPORT).read_bytes())
    abi_source = safe(ROOT / 'tools/stage61_interaction_oracle.py').read_text(encoding='utf-8')
    pins = re.findall(r'^STANDARD_SCRIPT_TABLE = (0x[0-9A-Fa-f]+)$', abi_source, re.M)
    need(len(pins) == 1 and int(pins[0], 16) == STANDARD_TABLE, 'standard table source ABI drift')
    report = audit(raw, generated, receipt)
    need(rom.read_bytes() == raw, 'candidate changed during read-only audit')
    report['source_head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    sources = (SELF, TEST, WORKFLOW, prior.REPORT, 'overlays/save_migration/save_migration.c',
               'overlays/save_migration/save_migration.h', 'tools/stage61_interaction_oracle.py')
    report['source_bindings'] = {n: identity(safe(ROOT / n).read_bytes()) for n in sources}
    safe(OUT).mkdir(parents=True, exist_ok=True)
    (OUT / 'audit.json').write_bytes(stable(report))
    print(json.dumps({'classification': report['classification'],
          'standard_script_target': report['standard_script']['target'],
          'native_owner_nodes': {k: len(v['nodes']) for k, v in report['native_owners'].items()},
          'ring_acquisition_accepted': False}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--header', type=Path, required=True)
    args = parser.parse_args()
    run(args.rom, args.header)
