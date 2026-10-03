#!/usr/bin/env python3
"""Ringのmap97/80 compiled ownerを有限・読取専用で検証する。

全ROMのgiver不存在や通常取得を主張しない。未知命令を読み飛ばさず、
script/native境界と未解決の外部ownerを明示する。ROM/セーブへは書かない。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
BASE = 0x08000000
CANDIDATE = {'size': 33554432, 'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b', 'crc32': '3EB17B36'}
TASK = 'PR-P08-7-RING-COMPILED-OWNER'
OUT = ROOT / '.local/pr16-ring-compiled-owner'
REPORT = 'content/modernization/pr16_ring_compiled_owner.json'
SOURCE_REPORT = 'content/modernization/pr16_ring_owner_resolution.json'
SELF = 'scripts/pr16_ring_compiled_owner.py'
TEST = 'tests/test_pr16_ring_compiled_owner.py'
WORKFLOW = '.github/workflows/pr16-ring-compiled-owner.yml'
SOURCES = (SELF, TEST, 'content/event_design_implementation/event_plan.json',
           'config/event_design_bindings.csv', 'overlays/event_design/event_design.c',
           'overlays/event_design/event_design.h', 'scripts/build_event_design_stage.py', SOURCE_REPORT)
LENGTHS = {0x02: 1, 0x05: 5, 0x06: 6, 0x09: 2, 0x0F: 6,
           0x16: 5, 0x21: 5, 0x23: 5, 0x5A: 1, 0x6A: 1, 0x6C: 1}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def span(raw: bytes, address: int, size: int) -> bytes:
    need(type(address) is int and type(size) is int and size > 0, 'invalid span')
    offset = address - BASE
    need(0 <= offset <= len(raw) - size, 'span outside ROM')
    return raw[offset:offset + size]


def u32(raw: bytes, address: int) -> int:
    return struct.unpack('<I', span(raw, address, 4))[0]


def exact_candidate(raw: bytes) -> None:
    need(identity(raw) == {k: CANDIDATE[k] for k in ('size', 'sha256')}, 'candidate size/SHA differs')
    need(f'{zlib.crc32(raw) & 0xffffffff:08X}' == CANDIDATE['crc32'], 'candidate CRC differs')


def owner_header(raw: bytes) -> dict:
    at = raw.find(b'VEGAED37')
    need(at >= 0 and raw.find(b'VEGAED37', at + 1) < 0, 'event owner header missing/duplicate')
    values = struct.unpack('<16I', span(raw, BASE + at + 8, 64))
    version, size, code_off, code_size, field_off, field_size = values[:6]
    need(version == 1 and code_off == 0x100 and 0 < code_size <= 131072, 'event code ABI differs')
    need(code_off + code_size <= field_off <= code_off + code_size + 3, 'event code/field overlap or gap')
    need(0 < field_size and field_off + field_size <= size <= 262144, 'event payload bounds differ')
    span(raw, BASE + at, size)
    need(values[6:13] == (80, 160, 76, 63, 326, 7, 7), 'event counts differ')
    code_start, field_start = BASE + at + code_off, BASE + at + field_off
    exports = dict(zip(('EventDesign_Probe', 'EventDesign_SetState', 'EventDesign_GrantReward'), values[13:]))
    need(all(p & 1 and code_start <= (p & ~1) < code_start + code_size for p in exports.values()), 'event export outside code')
    return {'address': BASE + at, 'size': size, 'code_start': code_start, 'code_size': code_size,
            'field_start': field_start, 'field_end': field_start + field_size, 'exports': exports}


def map_transition(raw: bytes, binding: dict) -> dict:
    """stage37_script_pointer_addressはpointer格納先でなくtransition script自体。"""
    groups = u32(raw, BASE + 0x54B0C)
    group = u32(raw, groups + 4 * int(binding['group_id']))
    header = u32(raw, group + 4 * int(binding['map_id']))
    span(raw, header, 0x1C)
    need(header + 8 == int(binding['stage37_record_address'], 0), 'map record owner differs')
    table = u32(raw, header + 8)
    rows = []
    for index in range(32):
        at = table + 5 * index
        kind = span(raw, at, 1)[0]
        if kind == 0:
            break
        need(kind in range(1, 8), 'unsupported map-script kind')
        target = u32(raw, at + 1)
        span(raw, target, 1)
        rows.append({'kind': kind, 'script': target})
    else:
        raise ValueError('unterminated map-script table')
    transitions = [r['script'] for r in rows if r['kind'] == 3]
    need(len(transitions) == 1, 'missing/duplicate ON_TRANSITION')
    need(transitions[0] == int(binding['stage37_script_pointer_address'], 0), 'transition binding differs')
    return {'groups': groups, 'group': group, 'header': header, 'table': table,
            'scripts': rows, 'transition': transitions[0],
            'pointer_field_name_is_historical_script_address': True}


def graph(raw: bytes, roots: list[int], lower: int, upper: int, limit: int = 512) -> list[dict]:
    """有限CFG。native/callstdは外部ownerとして列挙し、その先を推測しない。"""
    need(BASE <= lower < upper <= BASE + len(raw), 'invalid graph bounds')
    pending, nodes, occupied = list(roots), {}, {}
    while pending:
        at = pending.pop()
        if at in nodes:
            continue
        need(lower <= at < upper and at not in occupied, 'branch outside field or inside operand')
        need(len(nodes) < limit, 'graph bound exceeded')
        op = span(raw, at, 1)[0]
        need(op in LENGTHS, f'unknown opcode 0x{op:02X} at 0x{at:08X}; no resynchronization')
        size = LENGTHS[op]
        need(at + size <= upper, 'truncated field instruction')
        need(not any(p in occupied for p in range(at, at + size)), 'overlapping instructions')
        data = span(raw, at, size)
        row = {'address': at, 'opcode': op, 'hex': data.hex()}
        successors = [] if op == 2 else [at + size]
        if op in (5, 6):
            target = struct.unpack_from('<I', data, 1 if op == 5 else 2)[0]
            row['target'] = target
            if op == 6:
                need(data[1] == 1, 'unexpected branch condition')
            successors = [target] if op == 5 else [at + size, target]
        elif op in (0x16, 0x21):
            row['variable'], row['value'] = struct.unpack_from('<HH', data, 1)
        elif op == 0x23:
            ptr = struct.unpack_from('<I', data, 1)[0]
            need(ptr & 1, 'non-Thumb native pointer')
            span(raw, ptr & ~1, 2)
            row['native'] = ptr
        elif op == 0x09:
            need(data[1] in (4, 5), 'unreviewed standard script')
            row['standard_script'] = data[1]
        elif op == 0x0F:
            need(data[1] == 0, 'unreviewed text pointer register')
            row['text'] = struct.unpack_from('<I', data, 2)[0]
            span(raw, row['text'], 1)
        row['successors'] = successors
        nodes[at] = row
        occupied.update({p: at for p in range(at, at + size)})
        pending.extend(successors)
    need(any(r['opcode'] == 2 for r in nodes.values()), 'no reachable end')
    return [nodes[k] for k in sorted(nodes)]


def schedule(raw: bytes, transition: int, dispatcher: int, native: int) -> dict:
    expected = (b'\x16' + struct.pack('<HH', 0x8000, dispatcher & 0xffff)
                + b'\x16' + struct.pack('<HH', 0x8001, dispatcher >> 16)
                + b'\x23' + struct.pack('<I', native | 1) + b'\x02')
    prefix = 5 if span(raw, transition, 1) == b'\x23' else 0
    need(span(raw, transition + prefix, len(expected)) == expected, 'schedule byte contract differs')
    old = u32(raw, transition + 1) if prefix else None
    return {'scheduler_native': native | 1, 'dispatcher': dispatcher,
            'preexisting_transition_native': old, 'schedule_bytes_verified': True}


def audit(raw: bytes, symbols: dict, compiled: bytes) -> dict:
    exact_candidate(raw)
    owner = owner_header(raw)
    need(len(compiled) == owner['code_size'] and span(raw, owner['code_start'], len(compiled)) == compiled,
         'compiled event runtime differs from candidate; do not trust source-only symbols')
    for name, pointer in owner['exports'].items():
        need(symbols.get(name, 0) | 1 == pointer, 'compiled export/header mismatch')
    with (ROOT / 'config/event_design_bindings.csv').open(encoding='utf-8', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if r['placement_key'] == 'PLACEMENT_KEY_EVENT_FINAL_LEAGUE_CLEAR']
    need(len(rows) == 1, 'Ring binding missing/duplicate')
    binding = rows[0]
    need((binding['group_id'], binding['map_id'], binding['trigger_type'], binding['status']) == ('97', '80', 'MAP_ENTER', 'PASS'), 'Ring binding identity differs')
    route = map_transition(raw, binding)
    dispatcher = int(binding['dispatcher_address'], 0)
    scheduler = schedule(raw, route['transition'], dispatcher, symbols['EventDesign_ScriptSchedule'])
    nodes = graph(raw, [route['transition'], dispatcher], owner['field_start'], owner['field_end'])
    names = {address | 1: name for name, address in symbols.items() if name.startswith('EventDesign_')}
    natives = sorted({r['native'] for r in nodes if 'native' in r})
    calls = [{'address': r['address'], 'native': r['native'], 'symbol': names.get(r['native']),
              'compiled_owner_matched': r['native'] in names} for r in nodes if 'native' in r]
    grants = [c for c in calls if c['symbol'] in ('EventDesign_GrantReward', 'EventDesign_ScriptGrantReward')]
    need(not grants, 'compiled reward route has changed; stop old source-only assumptions')
    # The selected roots are finite, not all gameplay roots. Standard scripts,
    # prior transition natives and transitive native callees remain separate.
    external = [{'kind': 'native', 'target': p} for p in natives if p not in names]
    external += [{'kind': 'standard_script', 'target': p} for p in sorted({r['standard_script'] for r in nodes if 'standard_script' in r})]
    return {'schema_version': 1, 'task': TASK,
            'classification': 'COMPILED_OWNER_BOUNDARY_NOT_NATIVE_ACCEPTANCE',
            'candidate': CANDIDATE, 'event_owner': owner, 'map_route': route, 'schedule': scheduler,
            'compiled_runtime': identity(compiled), 'script_nodes': nodes, 'native_calls': calls,
            'reachable_event_reward_calls': grants, 'external_owners_not_excluded': external,
            'source_graph_record': SOURCE_REPORT, 'candidate_bytes_checked': True,
            'compiled_event_runtime_verified': True, 'all_runtime_owners_excluded': False,
            'ring_acquisition_accepted': False, 'release_ready': False,
            'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0, 'rom_changes': 0}


def run(rom: Path, header: Path) -> dict:
    for path in (rom, header, OUT):
        need(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink rejected')
    raw = rom.read_bytes()
    exact_candidate(raw)
    owner = owner_header(raw)
    from scripts.build_event_design_stage import _compile_runtime
    generated = header.read_bytes()
    compiled, symbols = _compile_runtime(owner['code_start'], generated)
    report = audit(raw, symbols, compiled)
    report['generated_header'] = identity(generated)
    report['source_head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    report['source_bindings'] = {name: identity((ROOT / name).read_bytes()) for name in SOURCES}
    report['native_excerpt_identity'] = {}
    out_text = []
    pointers = sorted({c['native'] for c in report['native_calls']})
    need(len(pointers) <= 16, 'native excerpt bound exceeded')
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory) / 'bounded.bin'
        for ptr in pointers:
            data = span(raw, ptr & ~1, 384)
            report['native_excerpt_identity'][f'0x{ptr:08X}'] = identity(data)
            tmp.write_bytes(data)
            text = subprocess.check_output(['arm-none-eabi-objdump', '-D', '-b', 'binary', '-m', 'arm',
                '-M', 'force-thumb', '--adjust-vma=' + str(ptr & ~1), str(tmp)], text=True)
            out_text.append(f'## native 0x{ptr:08X}\n' + text.replace(str(tmp), 'bounded-native'))
    need(rom.read_bytes() == raw, 'candidate mutated')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'audit.json').write_bytes(stable(report))
    (OUT / 'native-disassembly.txt').write_text('\n'.join(out_text), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('classification', 'candidate', 'schedule', 'native_calls',
          'external_owners_not_excluded', 'compiled_event_runtime_verified', 'ring_acquisition_accepted')}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--header', type=Path, required=True)
    args = parser.parse_args()
    run(args.rom, args.header)
