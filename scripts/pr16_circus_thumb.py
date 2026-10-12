#!/usr/bin/env python3
"""Circus adapterだけをThumb関数として再結合し、受入prefixの非影響を証明する。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OWNERS = {'cfru_integration_pending_copy': 0x0910ED25,
          'cfru_integration_pending_facility_set': 0x0910EE49}
ADAPTER_SIZE = 304
PREVIOUS_SHA = '022bd5e6383f5513f7b43fd00923f8ed66908b18a07f7be252b8ce7a011c5c72'
ARCHIVE_SHA = 'ca5353b6d728960702beb4f16fb4b829714d947474d2a10c2f831f9c0403b0a0'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def thumb_source(owners):
    need(type(owners) is dict and set(owners) == set(OWNERS), 'unexpected Thumb owners')
    for name, value in owners.items():
        need(type(value) is int and value == OWNERS[name], 'Thumb owner identity differs')
    rows = ['.syntax unified', '.cpu arm7tdmi', '.thumb']
    for name, value in sorted(owners.items()):
        rows += [f'.section .text.{name},"ax",%progbits', '.balign 4',
                 f'.global {name}', f'.type {name}, %function', '.thumb_func',
                 name + ':', 'ldr r3, 1f', 'bx r3', '.balign 4',
                 f'1: .word {value:#x}', f'.size {name}, .-{name}']
    return '\n'.join(rows) + '\n'


def check_thunks(code, address, symbols, readelf):
    """ELFの関数型・Thumb bitと実機命令の両方を検査。BLX/ARM veneerに依存しない。"""
    need(type(address) is int and address % 4 == 0, 'unaligned Thumb adapter')
    for name, target in OWNERS.items():
        need(name in symbols, 'missing Thumb owner symbol')
        at = symbols[name]
        need(at % 4 == 0 and address <= at <= address + len(code) - 8,
             'Thumb thunk outside adapter')
        need(code[at-address:at-address+8] == struct.pack('<HHI', 0x4B00, 0x4718, target),
             'Thumb thunk instructions or target differ')
        matches = [r.split() for r in readelf.splitlines() if r.split() and r.split()[-1] == name]
        need(len(matches) == 1 and len(matches[0]) == 8, 'ambiguous ELF owner symbol')
        row = matches[0]
        need(row[3] == 'FUNC' and int(row[1], 16) == (at | 1), 'ELF owner lacks Thumb function type')


def compile_adapter(root, folder, address, owners):
    folder.mkdir(parents=True, exist_ok=True)
    ld, elf, assembly = folder/'circus.ld', folder/'circus.elf', folder/'owners.S'
    assembly.write_text(thumb_source(owners))
    ld.write_text('ENTRY(VegaCircusAdmissionSelectScript)\nSECTIONS { . = '+hex(address)+'; '
        '.text : { KEEP(*(.text.VegaCircusAdmissionSelectScript)) *(.text*) *(.rodata*) } '
        '/DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) } }\n')
    cmd = ['arm-none-eabi-gcc', '-std=c11', '-Os', '-mthumb', '-mcpu=arm7tdmi', '-ffreestanding',
           '-fno-builtin', '-ffunction-sections', '-fdata-sections', '-fno-unwind-tables',
           '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror', '-nostdlib',
           '-Wl,--gc-sections', '-Wl,--build-id=none', '-Wl,--defsym,VegaCircusScriptResult=0x02037004',
           '-T', str(ld), str(root/'overlays/circus_admission/circus_script.c'),
           str(root/'overlays/circus_admission/circus_admission.c'), str(assembly), '-o', str(elf)]
    p = subprocess.run(cmd, capture_output=True)
    (folder/'compile.stdout').write_bytes(p.stdout); (folder/'compile.stderr').write_bytes(p.stderr)
    need(p.returncode == 0, 'typed Thumb adapter compile failed')
    need(not subprocess.check_output(['arm-none-eabi-nm', '-u', str(elf)]).strip(), 'undefined adapter symbol')
    listing = subprocess.check_output(['arm-none-eabi-nm', '-n', str(elf)], text=True)
    (folder/'symbols.txt').write_text(listing)
    symbols = {r.split()[2]: int(r.split()[0], 16) for r in listing.splitlines() if len(r.split()) == 3}
    need(symbols['VegaCircusAdmissionSelectScript'] == address, 'script entry drift')
    binary = folder/'circus.bin'
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', str(elf), str(binary)], check=True)
    code = binary.read_bytes()
    need(256 <= len(code) <= ADAPTER_SIZE, 'adapter exceeds accepted layout')
    readelf = subprocess.check_output(['arm-none-eabi-readelf', '-sW', str(elf)], text=True)
    (folder/'elf-symbols.txt').write_text(readelf)
    check_thunks(code, address, symbols, readelf)
    dis = subprocess.check_output(['arm-none-eabi-objdump', '-d', str(elf)], text=True)
    need('_from_thumb' not in dis and not re.search(r'\bbx\s+pc\b', dis), 'ARM interworking veneer reappeared')
    (folder/'disassembly.txt').write_text(dis.replace(str(elf), 'circus-script.elf'))
    # 旧adapterの領域長を保持し、受付テキスト/分岐/取消/Factoryの配置を変えない。
    return code.ljust(ADAPTER_SIZE, b'\xff'), address | 1


def decode_saved_adapter(text, address):
    """保存されたobjdump原本のみから旧adapterを復元。最終ROM全体hashが正否を判定する。"""
    code, seen = bytearray(ADAPTER_SIZE), set()
    for line in text.splitlines():
        match = re.match(r'^\s*([0-9a-f]+):\s+(.+)$', line)
        if not match:
            continue
        at = int(match[1], 16)
        for token in match[2].split():
            if not re.fullmatch(r'(?:[0-9a-f]{4}|[0-9a-f]{8})', token):
                break
            size = len(token)//2
            need(address <= at and at+size <= address+ADAPTER_SIZE, 'saved adapter outside range')
            offset = at-address
            need(not set(range(offset, offset+size)) & seen, 'duplicate saved instruction')
            code[offset:offset+size] = int(token, 16).to_bytes(size, 'little')
            seen.update(range(offset, offset+size)); at += size
    need(len(seen) >= ADAPTER_SIZE-16, 'saved adapter is incomplete')
    return bytes(code)


def prove_bytes(candidate, previous, current, saved_disassembly):
    need(identity(candidate) == current['candidate'], 'new candidate identity differs')
    need(previous['candidate'] == dict(size=33554432, sha256=PREVIOUS_SHA), 'unaccepted prefix candidate')
    for key in ('entries', 'launch_sites', 'gateway', 'payload_offset'):
        need(current[key] == previous[key], 'accepted prefix layout changed: '+key)
    need(current['payload']['size'] == previous['payload']['size'], 'payload size changed')
    address = current['entries']['selector'] & ~1
    start = address-0x08000000
    need(start == current['payload_offset']+64, 'adapter header boundary differs')
    old = decode_saved_adapter(saved_disassembly, address)
    restored = bytearray(candidate); restored[start:start+ADAPTER_SIZE] = old
    need(identity(restored) == previous['candidate'], 'bytes outside adapter changed')
    changed = [i for i, (a, b) in enumerate(zip(old, candidate[start:start+ADAPTER_SIZE])) if a != b]
    need(bool(changed), 'Thumb repair made no change')
    return dict(status='PASS_ADAPTER_ONLY_PREFIX_INHERITANCE', previous=previous['candidate'],
        candidate=current['candidate'], changed_bytes=len(changed),
        allowed_range=[start, start+ADAPTER_SIZE], restored_whole_rom_sha256=PREVIOUS_SHA,
        inherited_cases=['circus-cancel-save-continue', 'factory-fallback-cancel'],
        accepted_native_cases_replayed=0, physical_admission_accepted=False, suppression_accepted=False)


def prove():
    out = ROOT/'.local/pr16-circus-entry'
    archive = ROOT/'.local/pr16-circus-prefix-original.zip'
    raw = archive.read_bytes()
    need(identity(raw) == dict(size=295538, sha256=ARCHIVE_SHA), 'saved prefix archive differs')
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read('members.json'))
        def member(name):
            data = z.read(name)
            need(identity(data) == manifest[name], 'saved prefix member differs')
            return data
        previous = json.loads(member('pr16-circus-entry/report.json'))
        dis = member('pr16-circus-entry/compile-1/disassembly.txt').decode()
    current = json.loads((out/'report.json').read_bytes())
    result = prove_bytes((out/'candidate.gba').read_bytes(), previous, current, dis)
    (out/'thumb-inheritance.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    prove()
