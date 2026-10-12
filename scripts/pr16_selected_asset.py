#!/usr/bin/env python3
"""0880FA64の有限asset候補と実descriptorを照合する。型受入を先取りしない。"""
from __future__ import annotations
import hashlib
import json
import struct

HIT = 0x0880FA64
HIT_ID = {'size': 4, 'sha256': 'b12945a9395fea471444b59c0a9e33507a82af3be4b8d0a17ffbf5077f926c37'}
CANDIDATE = {'size': 33554432, 'sha256': '0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
BASE = '2e3a0f5bc497c8819eb8dba8a5422834fcb1fba8'
RADIUS = 65536


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def interval(start, size):
    need(type(start) is int and type(size) is int and 0 <= start < 2**32 and
         0 < size <= 2**32 - start, '正の32bit有限範囲')
    return start, start + size


def inside(start, size, address, width=4):
    a, b = interval(start, size)
    c, d = interval(address, width)
    return a <= c and d <= b


def section(raw, base, address, size):
    need(inside(base, len(raw), address, size), '有限入力範囲外')
    return raw[address-base:address-base+size]


def lz77(raw, base, start, hit, width=4, max_output=131072):
    """厳密なLZ77構文候補。CPU/BIOS実行やowner成立の代用にしない。"""
    interval(hit, width)
    header = section(raw, base, start, 4)
    need(header[0] == 0x10, 'LZ77 header')
    size = int.from_bytes(header[1:], 'little')
    need(type(max_output) is int and 0 < size <= max_output <= 131072, '展開上限')
    out, roles, cursor = bytearray(), [], start + 4
    def take(n, kind, output_start):
        nonlocal cursor
        at = cursor
        data = section(raw, base, at, n)
        cursor += n
        indexes = [i for i in range(width) if at <= hit+i < cursor]
        if indexes:
            roles.append(dict(kind=kind, source_address=at, size=n, target_byte_indexes=indexes,
                              output_start=output_start, sha256=identity(data)['sha256']))
        return data
    while len(out) < size:
        flags = take(1, 'flags', len(out))[0]
        for bit in range(7, -1, -1):
            if len(out) == size:
                break
            if flags & (1 << bit):
                pair = take(2, 'backreference', len(out))
                length = (pair[0] >> 4) + 3
                distance = ((pair[0] & 15) << 8 | pair[1]) + 1
                need(distance <= len(out), '先頭以前への逆参照')
                need(len(out) + length <= size, '宣言展開長越境')
                for _ in range(length):
                    out.append(out[-distance])
            else:
                out.extend(take(1, 'literal', len(out)))
    consumed = section(raw, base, start, cursor-start)
    return dict(start=start, end_exclusive=cursor, consumed=identity(consumed), expanded=identity(out),
                target_roles=roles, target_fully_consumed=inside(start+4, cursor-start-4, hit, width),
                parser_only=True, actual_consumer_proven=False)


def candidates(raw, base, hit, width=4, radius=RADIUS):
    """整列headerだけを有限探索。探索打切りを完全性へ読み替えない。"""
    need(type(radius) is int and 0 < radius <= RADIUS, '探索半径')
    section(raw, base, hit, width)
    low = max(base, hit-radius)
    low = (low+3) & ~3
    selected, checked, rejected = [], 0, 0
    for start in range(low, hit+1, 4):
        header = section(raw, base, start, 4)
        if header[0] != 0x10 or not 0 < int.from_bytes(header[1:], 'little') <= 131072:
            continue
        checked += 1
        need(checked <= 512, '有限header件数上限')
        try:
            parsed = lz77(raw, base, start, hit, width)
        except ValueError:
            rejected += 1
            continue
        if parsed['target_fully_consumed']:
            selected.append(parsed)
            need(len(selected) <= 32, '候補件数上限')
    return dict(search_start=low, search_end_exclusive=hit+1, header_alignment=4,
                input_region=dict(start=base, **identity(raw)), plausible_headers=checked,
                rejected_headers=rejected, matches=selected, bounded_search_complete=True,
                all_rom_search=False, actual_consumer_proven=False)


def tileset(raw, base, address):
    data = section(raw, base, address, 24)
    need(data[0] in (0, 1) and data[1] in (0, 1), 'Tileset bool8')
    fields = struct.unpack_from('<5I', data, 4)
    need(all(0x08000000 <= p < 0x0A000000 and p % 4 == 0 for p in fields[:4]), 'Tileset ROM field')
    return dict(address=address, identity=identity(data), is_compressed=bool(data[0]),
                is_secondary=bool(data[1]), tiles=fields[0], palettes=fields[1],
                metatiles=fields[2], attributes=fields[3], callback=fields[4],
                layout_assumed_from_fixed_public_source=True, actual_consumer_proven=False)


def bind_descriptors(raw, symbols, matches):
    starts = {r['start'] for r in matches}
    bound, rejected = [], []
    for name, symbol in sorted(symbols.items()):
        if not name.startswith('gTileset_'):
            continue
        try:
            row = tileset(raw, 0x08000000, symbol['address'])
        except ValueError:
            rejected.append(name)
            continue
        if row['tiles'] in starts:
            bound.append(dict(symbol=name, symbol_source=symbol, **row))
    return dict(matching_descriptors=bound, rejected_descriptor_names=rejected,
                checked_descriptors=sum(n.startswith('gTileset_') for n in symbols),
                actual_consumer_proven=False)
