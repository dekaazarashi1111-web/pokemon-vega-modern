#!/usr/bin/env python3
"""選定4byte近傍の逆参照を列挙。pointer形をowner/readerへ昇格しない。"""
from __future__ import annotations
import bisect
import hashlib
import json
import re
import struct

BASE_HEAD = '0063d978e49216edcf7219c97b3560b51688f9a8'
HIT = 0x0880FA64
RADIUS = 4096
ROM_BASE = 0x08000000
ROM_SIZE = 0x02000000
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
HIT_ID = dict(size=4, sha256='b12945a9395fea471444b59c0a9e33507a82af3be4b8d0a17ffbf5077f926c37')
NEXT = 'SAVE_CAPACITY_SELECTED_ASSET_XREF_READER'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def interval(start, size):
    need(type(start) is int and type(size) is int and 0 <= start < 2**32 and 0 < size <= 2**32-start, '正の32bit範囲')
    return start, start+size


def section(raw, base, address, size):
    lo, hi = interval(address, size)
    begin, end = interval(base, len(raw))
    need(begin <= lo < hi <= end, '入力範囲外')
    return raw[lo-base:hi-base]


def canonical(value):
    need(type(value) is int and 0x08000000 <= value < 0x0E000000, 'ROM mirror範囲')
    return ROM_BASE + (value-ROM_BASE) % ROM_SIZE


def inverse_pointers(raw, base, low, high, limit=4096):
    """全byte開始、3 ROM mirror。高位16bit検索を厳密なu32範囲で再検証する。"""
    interval(base, len(raw))
    need(type(low) is int and type(high) is int and ROM_BASE <= low < high <= ROM_BASE+ROM_SIZE, '正規ROM範囲')
    need(high-low <= 8192 and type(limit) is int and 0 < limit <= 8192, '有限範囲/件数')
    found = {}
    for mirror in range(3):
        lo, hi = low+mirror*ROM_SIZE, high+mirror*ROM_SIZE
        for page in range(lo >> 16, ((hi-1) >> 16)+1):
            needle = struct.pack('<H', page)
            at = raw.find(needle)
            while at != -1:
                pos = at-2
                if 0 <= pos <= len(raw)-4:
                    value = struct.unpack_from('<I', raw, pos)[0]
                    if lo <= value < hi:
                        address = base+pos
                        found[address] = dict(address=address, size=4, target=value,
                            canonical_target=canonical(value), mirror=mirror,
                            sha256=identity(raw[pos:pos+4])['sha256'])
                        need(len(found) <= limit, '件数上限到達。部分集合を完全結果にしない')
                at = raw.find(needle, at+1)
    return [found[n] for n in sorted(found)]


def literal_shapes(raw, base, literal, radius=1024):
    """PC-relative Thumb LDRの形。命令境界・実行・到達を主張しない。"""
    need(type(radius) is int and 0 < radius <= 1024, 'LDR有限半径')
    section(raw, base, literal, 4)
    if literal % 4:
        return []
    lower = max(base, literal-radius)
    lower += lower % 2
    result = []
    for pc in range(lower, literal, 2):
        word = struct.unpack('<H', section(raw, base, pc, 2))[0]
        if word & 0xF800 == 0x4800 and ((pc+4) & ~3)+4*(word & 255) == literal:
            result.append(dict(address=pc, size=2, register=(word >> 8) & 7,
                literal_address=literal, sha256=identity(section(raw, base, pc, 2))['sha256'],
                actual_instruction_fetch_proven=False))
    return result


def symbol_index(raw):
    """公開JP symbolは近傍情報だけ。現候補のowner境界としない。"""
    result = {}
    for line, text in enumerate(raw.decode('utf-8').splitlines(), 1):
        cells = text.split('\t')
        if len(cells) != 8 or not re.fullmatch(r'(?:0x)?[0-9a-fA-F]{8}', cells[1]):
            continue
        address = int(cells[1], 16) & ~1
        if ROM_BASE <= address < ROM_BASE+ROM_SIZE:
            result.setdefault(address, []).append(dict(name=cells[4], line=line,
                row_sha256=identity(text.encode())['sha256']))
    need(result, 'symbol空入力')
    return sorted(result), result


def neighborhood(index, address):
    addresses, labels = index
    pos = bisect.bisect_right(addresses, address)-1
    preceding = None if pos < 0 else dict(address=addresses[pos], labels=labels[addresses[pos]])
    following = None if pos+1 == len(addresses) else dict(address=addresses[pos+1], labels=labels[addresses[pos+1]])
    return dict(preceding=preceding, following=following, current_owner_proven=False)


def measure(raw, symbol_raw):
    need(identity(raw) == CANDIDATE, '全候補SHA/size')
    need(identity(section(raw, ROM_BASE, HIT, 4)) == HIT_ID, '選定origin4byte')
    index = symbol_index(symbol_raw)
    rows = inverse_pointers(raw, ROM_BASE, HIT-RADIUS, HIT+4)
    for row in rows:
        row['target_offset_from_hit'] = row['canonical_target']-HIT
        row['origin_neighborhood'] = neighborhood(index, row['address'])
        row['target_neighborhood'] = neighborhood(index, row['canonical_target'])
        row['thumb_literal_shapes'] = literal_shapes(raw, ROM_BASE, row['address'])
        for shape in row['thumb_literal_shapes']:
            shape['public_neighborhood'] = neighborhood(index, shape['address'])
    # 直接参照元自身への第2段逆参照。table基点の推測や全間接参照の代用ではない。
    second = []
    for address in sorted({r['address'] for r in rows}):
        refs = inverse_pointers(raw, ROM_BASE, address, address+1, limit=4096)
        if refs:
            for row in refs:
                row['origin_neighborhood'] = neighborhood(index, row['address'])
            second.append(dict(referenced_origin=address, references=refs))
    return dict(schema_version=1, candidate=CANDIDATE, origin=dict(address=HIT, **HIT_ID),
        target_search=dict(start=HIT-RADIUS, end_exclusive=HIT+4, all_byte_starts=True, rom_mirrors=3),
        first_level=rows, first_level_count=len(rows), second_level=second,
        second_level_count=sum(len(x['references']) for x in second),
        literal_shape_count=sum(len(x['thumb_literal_shapes']) for x in rows),
        input_identity=identity(raw), bounded_target_search_complete=True,
        accepted_inventory_reruns=0, prior_lz_search_reruns=0, map_probe_reruns=0,
        new_inverse_reference_passes=1+len(rows), formal_classification_changes=0,
        formal_classified=789, formal_unclassified=85, selected_unknown_origins=6, donor_safe_bytes=0,
        owner_identified=False, actual_asset_reader_proven=False, global_owner_absence_proven=False,
        limitations_ja=[
            '新規の対象限定逆参照。旧874参照inventory/旧LZ/map測定を再走したものではない。',
            'asset開始が前4096byteより外、計算参照、RAM再配置、table基点への参照は未網羅。',
            'u32 pointer/LDR形と旧symbol近傍は実行証拠ではない。正式型・容量へ昇格しない。'])
