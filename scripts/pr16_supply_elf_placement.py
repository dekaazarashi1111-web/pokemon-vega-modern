#!/usr/bin/env python3
"""保存ELFの実load addressをROM配置へ保存する。compile/原本生成を行わない。"""
from __future__ import annotations
import copy
import hashlib
import struct
import zlib

BASE = 0x08000000
MAX_IMAGE = 4028


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def elf_image(elf: bytes, raw: bytes, origin: int, capacity: int = MAX_IMAGE) -> tuple[bytes, dict]:
    """単一RX LOAD / 単一AX PROGBITSの固定moduleを有界・fail-closedで読む。"""
    need(len(elf) >= 52 and elf[:7] == b'\x7fELF\x01\x01\x01', 'ELF32 little-endian header')
    h = struct.unpack_from('<HHIIIIIHHHHHH', elf, 16)
    etype, machine, version, entry, phoff, shoff, _, ehsize, phsize, phnum, shsize, shnum, _ = h
    need((etype, machine, version, ehsize) == (2, 40, 1, 52), 'ARM executable ELF')
    need(phsize == 32 and 1 <= phnum <= 64 and 52 <= phoff <= len(elf)-phnum*phsize, 'program header bounds')
    need(shsize == 40 and 1 <= shnum <= 4096 and 52 <= shoff <= len(elf)-shnum*shsize, 'section header bounds')
    loads = []
    for i in range(phnum):
        p = struct.unpack_from('<8I', elf, phoff+i*phsize)
        if p[0] == 1:
            loads.append(p)
    need(len(loads) == 1, 'one load segment required')
    _, offset, vaddr, paddr, filesz, memsz, flags, alignment = loads[0]
    need(flags == 5 and filesz == memsz and filesz > 0, 'RX file-backed segment only')
    need(vaddr == paddr and BASE <= paddr < BASE+0x2000000, 'VMA/LMA identity')
    need(0 < alignment <= 0x10000 and alignment & (alignment-1) == 0
         and offset % alignment == paddr % alignment, 'load alignment')
    need(offset >= 52 and offset <= len(elf)-filesz, 'load bytes truncated')
    need(paddr <= (entry & ~1) < paddr+filesz, 'entry outside load')
    sections = [struct.unpack_from('<10I', elf, shoff+i*shsize) for i in range(shnum)]
    allocated = [(i, s) for i, s in enumerate(sections) if s[2] & 2 and s[5]]
    need(len(allocated) == 1, 'one allocated section required')
    text_index, text = allocated[0]
    need(text[1:6] == (1, 6, paddr, offset, filesz), 'AX PROGBITS/load mapping')
    need(text[8] > 0 and text[8] & (text[8]-1) == 0 and paddr % text[8] == 0, 'section alignment')
    need(elf[offset:offset+filesz] == raw, 'objcopy/ELF bytes differ')
    gap = paddr-origin
    need(origin % 4 == 0 and 0 <= gap <= 64 and 0 < gap+filesz <= capacity
         and origin >= BASE and origin+gap+filesz <= BASE+0x2000000, 'placement capacity/origin')
    symbols = {}
    for section in sections:
        if section[1] != 2:
            continue
        _, _, _, _, at, size, strings, _, _, entsize = section
        need(entsize == 16 and size % 16 == 0 and at <= len(elf)-size and strings < shnum, 'symbol bounds')
        st = sections[strings]
        need(st[1] == 3 and st[4] <= len(elf)-st[5], 'symbol strings')
        names = elf[st[4]:st[4]+st[5]]
        for pos in range(at, at+size, 16):
            name, value, width, info, _, index = struct.unpack_from('<IIIBBH', elf, pos)
            if index != text_index or info & 15 != 2:
                continue
            need(name < len(names) and b'\0' in names[name:], 'symbol name terminator')
            label = names[name:names.index(b'\0', name)].decode('ascii')
            if label.startswith('Pr16'):
                need(label not in symbols and paddr <= (value & ~1) < paddr+filesz
                     and (value & ~1)+width <= paddr+filesz, 'exported symbol range/duplicate')
                symbols[label] = value & ~1
    image = b'\xff'*gap+raw
    return image, {'elf': identity(elf), 'objcopy': identity(raw), 'placed_image': identity(image),
                   'origin': origin, 'load_address': paddr, 'prefix_bytes': gap, 'section_alignment': text[8],
                   'symbols': symbols, 'all_load_bytes_mapped': True}


def repair(candidate: bytes, link: dict, elf: bytes, raw: bytes) -> tuple[bytes, dict, bytes]:
    """過去候補を変更せず後継を返す。hook/PLA1/PLC2/全宣言外byteを保持。"""
    need(identity(candidate) == link['candidate'], 'candidate identity')
    result = copy.deepcopy(link)
    parts = [s for s in result['segments'] if s['name'] == 'pr16_supply_arm']
    need(len(parts) == 1, 'one ARM segment')
    part = parts[0]
    start, end = part['start'], part['end_exclusive']
    need(start >= 0 and end <= len(candidate) and end-start == len(raw) == part['size']
         and candidate[start:end] == raw and part['content_sha256'] == identity(raw)['sha256']
         and part['sha256'] == part['content_sha256'] and link['code_start'] == BASE+start
         and link['code_end'] == BASE+end, 'old ARM span')
    image, mapping = elf_image(elf, raw, BASE+start)
    need(mapping['prefix_bytes'] > 0, 'already aligned: do not repair twice')
    need(mapping['symbols'] and all(mapping['symbols'].get(k) == v for k, v in link['symbols'].items()), 'ELF/exported symbol binding')
    new_end = start+len(image)
    need(new_end <= len(candidate) and candidate[end:new_end] == b'\xff'*(new_end-end), 'extension is not free')
    plan = result['allocation']
    regions = [r for r in plan['regions'] if r['name'] == part['region']]
    need(len(regions) == 1 and regions[0]['kind'] == 'allocatable'
         and regions[0]['start'] <= start < new_end <= regions[0]['end_exclusive'], 'allocation region')
    allocations = [a for a in plan['allocations'] if a['name'] == part['name']]
    need(len(allocations) == 1 and allocations[0]['start'] == start
         and allocations[0]['end_exclusive'] == end, 'allocation identity')
    for other in plan['allocations']:
        if other is not allocations[0]:
            need(new_end <= other['start'] or other['end_exclusive'] <= start, 'allocation overlap')
    out = bytearray(candidate)
    out[start:new_end] = image
    need(out[:start] == candidate[:start] and out[new_end:] == candidate[new_end:], 'outside repair span')
    checks = []
    for hook in link['hooks']:
        target = hook['target'] & ~1
        need(mapping['symbols'].get(hook['symbol']) == target, 'hook symbol')
        at = hook['offset']
        need(out[at:at+8].hex() == hook['after'], 'hook bytes changed')
        index = target-mapping['load_address']
        need(0 <= index <= len(raw)-2 and out[target-BASE:target-BASE+2] == raw[index:index+2], 'hook first instruction')
        checks.append({'symbol': hook['symbol'], 'target': hook['target'],
                       'first_instruction_hex': raw[index:index+2].hex()})
    delta = len(image)-len(raw)
    for row in (part, allocations[0]):
        row.update(size=len(image), end_exclusive=new_end, gba_end_exclusive=BASE+new_end,
                   content_sha256=identity(image)['sha256'])
        if 'sha256' in row:
            row['sha256'] = row['content_sha256']
    summary = plan['summaries']
    summary['allocated_bytes'] += delta
    summary['remaining_allocatable_bytes'] -= delta
    usage = [u for u in summary['region_usage'] if u['region'] == part['region']]
    need(len(usage) == 1 and usage[0]['remaining_bytes'] >= delta, 'region summary')
    usage[0]['allocated_bytes'] += delta
    usage[0]['remaining_bytes'] -= delta
    mapping.update(hook_entries=checks, repair_start=start, repair_end_exclusive=new_end,
                   outside_repair_span_changes=0, hook_bytes_changed=0, new_arm_compiles=0, new_arm_links=0)
    result.update(candidate=identity(out), candidate_crc32=f'{zlib.crc32(out)&0xffffffff:08X}',
                  code_end=BASE+new_end, placement_repair=mapping, repair_parent=identity(candidate),
                  status='REPAIRED_ELF_LOAD_ADDRESS_NATIVE_PENDING')
    return bytes(out), result, image
