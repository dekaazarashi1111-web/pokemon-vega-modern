#!/usr/bin/env python3
"""One exact loss-callback pointer plus a guarded native shim over immutable bffd."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
SELF = 'scripts/pr16_bp_loss_return_successor.py'
SOURCE = 'overlays/facility_loss_return/facility_loss_return.c'
OUT = ROOT / '.local/pr16-bp-loss-return-successor'
BASE = 0x08000000
PARENT_SHA = 'bffd0b83e3724c2fba216052a3ff45afd3ab194ca2168244874746ce0e4a9e92'
SIZE = 33554432
OFFSET = 0x7FC5C
PAYLOAD_OFFSET = 0x1FF4680
ENTRY = BASE + PAYLOAD_OFFSET + 1
WHITEOUT = 0x08055F65
AFTERBATTLE = 0x092CE7B9
ROOTS = (0x092CF669, 0x092CF6A5, 0x092CF6E1)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def patch_bytes(raw, offset, before, after):
    need(type(raw) is bytes and type(offset) is int, 'immutable bytes/integer required')
    need(type(before) is bytes and type(after) is bytes and len(before) == len(after) > 0, 'fixed-size edit required')
    need(0 <= offset <= len(raw)-len(before) and raw[offset:offset+len(before)] == before, 'patch preimage differs')
    need(before != after, 'empty edit rejected')
    return raw[:offset]+after+raw[offset+len(before):]


def binding(raw):
    need(identity(raw) == dict(size=SIZE, sha256=PARENT_SHA), 'exact bffd parent required')
    need(raw[0x7FC44:0x7FC78] == bytes.fromhex(
        '04480078fff7d2fd012807d1024880f777fc0ae0ea3d0202655f0508'
        '044880f76ffcff f759ff94f039fc01bc00470000a1610508'.replace(' ', '')),
        'EndTrainerBattle loss dispatch preimage differs')
    need(raw[0x12CE7B8:0x12CE7EA] == bytes.fromhex(
        'f7b53c4b1c7800f033fa002804d03a4d3a4beb5c002b07d100f012fa0022384b1a80'
        'f7bc01bc00477f2300261c40012c05d0'), 'AfterBattle owner/ledger-valid BL preimage differs')
    need(all(raw[p-BASE:p-BASE+5] == b'\x23'+struct.pack('<I', AFTERBATTLE) for p in ROOTS),
         'not the three native AfterBattle call sites')
    return dict(loss_callback_literal=BASE+OFFSET, original_callback=WHITEOUT,
        dispatch_ldr=0x0807FC50, dispatch_set_main_callback=0x0807FC52,
        afterbattle=AFTERBATTLE, afterbattle_roots=list(ROOTS),
        ledger_valid_call=0x092CE7BE, ledger_valid=0x092CEC29,
        static_owner_bound=True, native_loss_return_accepted=False)


def compile_runtime(out):
    need(not any(p.is_symlink() for p in (out, *out.parents)), 'unsafe compile output')
    out.mkdir(parents=True, exist_ok=True)
    linker = out/'runtime.ld'
    linker.write_text('ENTRY(VegaFacilityLossReturn)\nSECTIONS { . = '+hex(BASE+PAYLOAD_OFFSET)+
        '; .text : { KEEP(*(.text.entry)) *(.text*) *(.rodata*) } /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) } }\n')
    elf, binary = out/'runtime.elf', out/'runtime.bin'
    cmd = ['arm-none-eabi-gcc', '-std=c11', '-Os', '-mthumb', '-mcpu=arm7tdmi',
           '-ffreestanding', '-fno-builtin', '-ffunction-sections', '-fdata-sections',
           '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror',
           '-nostdlib', '-Wl,--gc-sections', '-Wl,--build-id=none', '-T', str(linker),
           str(ROOT/SOURCE), '-o', str(elf)]
    subprocess.run(cmd, check=True, capture_output=True)
    symbols = subprocess.check_output(['arm-none-eabi-nm', '-n', str(elf)], text=True)
    entries = [int(line.split()[0], 16) for line in symbols.splitlines() if line.split()[-1:] == ['VegaFacilityLossReturn']]
    need(len(entries) == 1 and entries[0] & ~1 == ENTRY & ~1, 'runtime entry placement differs')
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', str(elf), str(binary)], check=True)
    data = binary.read_bytes()
    need(16 <= len(data) <= 1024, 'bounded native shim size differs')
    disassembly = subprocess.check_output(['arm-none-eabi-objdump', '-d', str(elf)], text=True).replace(str(elf), 'loss-return-runtime.elf')
    (out/'runtime-disassembly.txt').write_text(disassembly)
    (out/'runtime-symbols.txt').write_text(symbols)
    return data


def allocation(parent, payload, original):
    sys.path[:0] = [str(ROOT)]
    from tools.rom_allocator import REQUEST_FIELDS, build_allocation_report_from_csv
    need(original['summaries']['overlap_count'] == 0, 'parent allocation overlap')
    requests = []
    for i, row in enumerate(original['allocations']):
        a, b = row['start'], row['end_exclusive']
        need(row['sequence'] == i and b-a == row['size'] and 0 <= a < b <= SIZE, 'allocation bounds')
        need(identity(parent[a:b])['sha256'] == row['content_sha256'], 'parent allocation bytes differ')
        need(b <= PAYLOAD_OFFSET or a >= PAYLOAD_OFFSET+len(payload), 'shim overlaps prior allocation')
        request = {k:v for k,v in row.items() if k in REQUEST_FIELDS}
        if row['placement'] == 'FIRST_FIT':
            request.pop('start')
        requests.append(request)
    need(build_allocation_report_from_csv(ROOT/'config/rom_regions.csv', requests) == original, 'parent allocation reconstruction differs')
    requests.append(dict(name='pr16_factory_loss_return', region='future_tail', start=PAYLOAD_OFFSET,
        size=len(payload), alignment=4, owner='USER-20260913-BP-LOSS-RETURN',
        purpose='Bounded Trial loss script continuation; ordinary WhiteOut preserved', content_sha256=identity(payload)['sha256']))
    return build_allocation_report_from_csv(ROOT/'config/rom_regions.csv', requests)


def build(parent, plan, payload):
    bound = binding(parent)
    need(type(payload) is bytes and 16 <= len(payload) <= 1024, 'bounded payload required')
    need(parent[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)] == b'\xFF'*len(payload), 'allocation is not erased free space')
    successor = patch_bytes(parent, OFFSET, struct.pack('<I', WHITEOUT), struct.pack('<I', ENTRY))
    successor = patch_bytes(successor, PAYLOAD_OFFSET, b'\xFF'*len(payload), payload)
    # Full unchanged regions, including every other WhiteOut site and all old allocations.
    need(successor[:OFFSET] == parent[:OFFSET]
         and successor[OFFSET+4:PAYLOAD_OFFSET] == parent[OFFSET+4:PAYLOAD_OFFSET]
         and successor[PAYLOAD_OFFSET+len(payload):] == parent[PAYLOAD_OFFSET+len(payload):], 'undeclared ROM changes')
    allocated = allocation(parent, payload, plan)
    for row in allocated['allocations']:
        need(identity(successor[row['start']:row['end_exclusive']])['sha256'] == row['content_sha256'], 'output allocation mismatch')
    return successor, dict(schema_version=1, status='BUILT_SCOPED_LOSS_RETURN_NOT_NATIVE_ACCEPTED',
        parent=identity(parent), candidate=identity(successor), crc32=f'{zlib.crc32(successor)&0xffffffff:08X}',
        allocation=allocated, binding=bound, runtime=identity(payload), runtime_entry=ENTRY,
        change=dict(offset=OFFSET, before=struct.pack('<I',WHITEOUT).hex(), after=struct.pack('<I',ENTRY).hex(), size=4),
        payload=dict(offset=PAYLOAD_OFFSET,size=len(payload)), undeclared_changed_bytes=0,
        original_allocations_changed=0, new_allocations=1, save_layout_changes=0,
        candidate_rom_changed=True, active_baseline_changed=False, native_loss_return_accepted=False,
        native_bp_earning_accepted=False, p05_native_bp_gap_closed=False, release_ready=False)


def run():
    sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
    import pr16_bp_chooser_successor as previous
    need(not any(p.is_symlink() for p in (OUT, *OUT.parents)), 'unsafe successor output')
    OUT.mkdir(parents=True, exist_ok=True)
    recipe = previous.run()
    parent = (previous.OUT/'candidate.gba').read_bytes()
    binding(parent)
    payloads = [compile_runtime(OUT/f'compile-{i}') for i in (1,2)]
    need(payloads[0] == payloads[1], 'independent native compilations differ')
    left, report = build(parent, recipe['allocation'], payloads[0])
    right, again = build(parent, recipe['allocation'], payloads[1])
    need(left == right and report == again, 'independent bounded successors differ')
    (OUT/'candidate.gba').write_bytes(left)
    # Full source/parent identities bind reconstruction, not a guessed successor SHA.
    report.update(independent_native_compiles=2, independent_bounded_builds=2,
        sources={p:identity((ROOT/p).read_bytes()) for p in (SELF,SOURCE,previous.SELF,
            'overlays/save_migration/save_migration.h','overlays/facility_runtime/facility_runtime.c','config/rom_regions.csv')})
    (OUT/'candidate.json').write_bytes(stable(report))
    (OUT/'ledger-valid-bytes.json').write_bytes(stable(dict(address=0x092CEC28,
        bytes=parent[0x12CEC28:0x12CEC44].hex(), source='overlays/facility_runtime/facility_runtime.c:ledger_valid')))
    need(identity((previous.OUT/'candidate.gba').read_bytes()) == report['parent'], 'parent mutated')
    return report


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False))
