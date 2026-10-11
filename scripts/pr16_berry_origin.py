#!/usr/bin/env python3
"""選定originの限定identity検査。近傍symbolや命令形から型受入へ昇格しない。"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_HEAD = 'fea040c43cf7ac05cd25038f342d0dd3535df231'
CANDIDATE = {'size': 33554432, 'sha256': '0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
START, END, HIT = 0x086C48AC, 0x086C7D38, 0x086C51BF
HIT_ID = {'size': 4, 'sha256': '169f39595db6c1ad1cf83234441b8a0ec54dc2a94afab2cc05d80713fb0a0a41'}
SOURCE = 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'
PUBLIC_PATHS = {
    'data/multiboot_berry_glitch_fix.s': 'd0d54d5502762431a8cfef4c4eed5201138c3108',
    'src/berry_fix_program.c': '4ef103aecaf43c2409ed9f8e9d872561b1772716',
    'src/multiboot.c': 'b44c421dc565ad1750c30f60afb5b5c61a10fee8',
    # バイナリblobは固定commitのGit treeから取得して全byteを別照合する。
    'data/mb_berry_fix.gba': None,
}
SYMBOL_SOURCE = {
    'repository': 'ComplexRobot/frlg-sym',
    'commit': 'c04a31542086b20d8c6ee641eaa70b8db6713fd3',
    'path': 'diagnostics/pokefirered_jp.sym.audit.tsv',
    'git_blob': '53316c0d61da2c6cc22acf3d79f68c61c64c65be',
    'size': 4147002,
    'sha256': 'fc1e4b579b21a592b8e09fa3c36f242833837190401128cd6866c945eff2f44e',
}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def blob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def encode(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def section(raw: bytes, base: int, address: int, size: int) -> bytes:
    need(all(type(n) is int for n in (base, address, size)), '範囲は整数')
    need(size > 0 and base <= address and address - base + size <= len(raw), '有限範囲外')
    return raw[address - base:address - base + size]


def parse_symbols(raw: bytes, names: set[str]) -> dict:
    """必要名だけの重複を拒否。compiler-local名を全体一意とは仮定しない。"""
    result, rows = {}, []
    for line, text in enumerate(raw.decode('utf-8').splitlines(), 1):
        cells = text.split('\t')
        if len(cells) != 8 or not re.fullmatch(r'(?:0x)?[0-9a-fA-F]{8}', cells[1]):
            continue
        address, name = int(cells[1], 16), cells[4]
        if not 0x08000000 <= address < 0x0A000000:
            continue
        rows.append(address & ~1)
        if name in names:
            need(name not in result, '必要symbol名重複: ' + name)
            result[name] = {'address': address, 'line': line, 'row_sha256': identity(text.encode())['sha256']}
    for value in result.values():
        value['following_distinct_address'] = min((n for n in rows if n > (value['address'] & ~1)), default=None)
    return {'found': result, 'missing': sorted(names - result.keys())}


def compare_regions(current: bytes, reference: bytes, hit_offset: int) -> dict:
    need(16 <= len(current) <= 131072 and 16 <= len(reference) <= 131072, 'asset有限長')
    need(type(hit_offset) is int and 8 <= hit_offset <= len(current) - 12, 'hit/context範囲')
    size = min(len(current), len(reference))
    prefix = 0
    while prefix < size and current[prefix] == reference[prefix]:
        prefix += 1
    suffix = 0
    while suffix < size - prefix and current[-1 - suffix] == reference[-1 - suffix]:
        suffix += 1
    context_start = (hit_offset & ~1) - 8
    context = current[context_start:context_start + 24]
    # 公開asset内だけを有限探索。ROM全域/旧874参照scanではない。
    positions, offset = [], 0
    while offset <= len(reference) - len(context):
        found = reference.find(context, offset)
        if found < 0:
            break
        positions.append(found)
        offset = found + 1
    return {
        'current_region_identity': identity(current), 'public_asset_identity': identity(reference),
        'whole_asset_equal': current == reference, 'same_size': len(current) == len(reference),
        'equal_prefix_bytes': prefix, 'equal_suffix_bytes': suffix,
        'equal_bytes_at_same_offsets': sum(current[i] == reference[i] for i in range(size)),
        'header_192_equal': len(current) >= 192 and len(reference) >= 192 and current[:192] == reference[:192],
        'context_offset': context_start, 'context_identity': identity(context),
        'public_exact_context_offsets': positions, 'context_match_is_owner_proof': False,
        'actual_consumer_proven': False,
    }


def arm_header(raw: bytes) -> dict:
    need(len(raw) >= 192, 'multiboot header切断')
    word = struct.unpack_from('<I', raw)[0]
    is_branch = word & 0xFF000000 == 0xEA000000
    displacement = word & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    target = 8 + displacement * 4 if is_branch else None
    return {'unconditional_arm_branch_shape': is_branch, 'relative_entry_if_arm': target,
            'entry_inside_region': is_branch and 192 <= target < len(raw),
            'runtime_mapping_proven': False, 'natural_boot_executed': False}


def thumb_shapes(raw: bytes, base: int, hit: int) -> list[dict]:
    """交差する完全BLの形だけ。復号形をinstruction fetch/reader受入にしない。"""
    section(raw, base, hit, 4)
    need(base % 2 == 0, 'Thumb基準整列')
    out = []
    for address in ((hit & ~1) - 2, hit & ~1, (hit & ~1) + 2):
        if address < base or address + 4 > base + len(raw):
            continue
        hi, lo = struct.unpack('<HH', section(raw, base, address, 4))
        if hi & 0xF800 != 0xF000 or lo & 0xF800 != 0xF800:
            continue
        displacement = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
        if displacement & 0x400000:
            displacement -= 0x800000
        overlap_start, overlap_end = max(address, hit), min(address + 4, hit + 4)
        if overlap_start >= overlap_end:
            continue
        out.append({'address': address, 'size': 4, 'shape': 'THUMB1_BL',
                    'conditional_target_if_executed_at_rom_address': (address + 4 + displacement) & 0xFFFFFFFF,
                    'hit_overlap_start': overlap_start, 'hit_overlap_size': overlap_end - overlap_start,
                    'actual_instruction_fetch_proven': False, 'reachability_proven': False})
    return out


def literal_occurrences(raw: bytes, base: int, values: dict[str, int]) -> list[dict]:
    need(type(base) is int and base % 4 == 0 and 0 < len(raw) <= 8192, '有限literal窓/整列')
    need(all(type(n) is int and 0 <= n <= 0xFFFFFFFF for n in values.values()), 'literal値')
    result = []
    for offset in range(0, len(raw) - 3, 4):
        value = struct.unpack_from('<I', raw, offset)[0]
        labels = sorted(name for name, wanted in values.items() if value == wanted)
        if labels:
            result.append({'address': base + offset, 'value_labels': labels,
                           'actual_ldr_consumer_proven': False})
    return result


def bind_hit(raw: bytes) -> bytes:
    need(identity(raw) == CANDIDATE, '現候補全32MiB identity')
    current = section(raw, 0x08000000, START, END - START)
    need(identity(section(raw, 0x08000000, HIT, 4)) == HIT_ID, '保存origin全4byte')
    return current
