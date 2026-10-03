"""受入PLC1の意味を保ち、重複行だけを共有するPLC2配置形式。"""
from __future__ import annotations
import hashlib
import struct

COUNT = 1671
CONSUMERS = (0, 1, 6, 7, 8)
HEADER = struct.Struct('<4sHH6I')
POLICY = 32
INDEX = 1704
DATA = 18416
OLD_DATA = 68544
MASK = 0x1C3


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def identity(data: bytes) -> dict:
    return {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}


def source_rows(image: bytes) -> list[bytes | None]:
    """固定PLC1の全owner/全列を検査。基準の再抽出・再生成はしない。"""
    need(len(image) >= OLD_DATA, 'PLC1 truncated')
    need(HEADER.unpack_from(image) == (b'PLC1', 1, COUNT, POLICY, INDEX, OLD_DATA,
                                      len(image), MASK, 0), 'PLC1 header')
    need(all(1 <= p <= 7 for p in image[POLICY:POLICY + COUNT]), 'PLC1 policy')
    need(image[POLICY + COUNT:INDEX] == b'\0', 'PLC1 alignment')
    result = []
    for sid in range(COUNT):
        for column, consumer in enumerate(CONSUMERS):
            at = INDEX + (sid * 5 + column) * 8
            offset, count, owner_key = struct.unpack_from('<IHH', image, at)
            need(owner_key == (sid << 4) | consumer, 'PLC1 owner key')
            if image[POLICY + sid] != 1:
                need(offset == 0xFFFFFFFF and count == 0, 'PLC1 non-learning span')
                result.append(None)
                continue
            tutor = consumer == 8
            length = 16 if tutor else count * 2
            need((count == 64 if tutor else count <= 50), 'PLC1 count')
            need(OLD_DATA <= offset <= len(image) and offset % 2 == 0
                 and length <= len(image) - offset, 'PLC1 bounds')
            raw = image[offset:offset + length]
            if tutor:
                need(raw[8:] == bytes(8), 'PLC1 tutor padding')
            else:
                need(all(1 <= m[0] <= 1062 for m in struct.iter_unpack('<H', raw)),
                     'PLC1 move/Side Change')
            result.append(struct.pack('<H', (0x8000 if tutor else 0) | count) + raw)
    return result


def compact(image: bytes) -> tuple[bytes, dict]:
    rows = source_rows(image)
    out = bytearray(DATA)
    out[POLICY:POLICY + COUNT] = image[POLICY:POLICY + COUNT]
    offsets: dict[bytes, int] = {}
    for index, row in enumerate(rows):
        if row is None:
            offset = 0xFFFF
        else:
            if row not in offsets:
                offsets[row] = len(out)
                out.extend(row)
            offset = offsets[row]
        need(offset <= 0xFFFF, 'PLC2 index overflow')
        struct.pack_into('<H', out, INDEX + index * 2, offset)
    need(len(out) < 0xFFFF, 'PLC2 image overflow')
    HEADER.pack_into(out, 0, b'PLC2', 1, COUNT, POLICY, INDEX, DATA, len(out), MASK, 0)
    result = bytes(out)
    decoded = compact_rows(result)
    need(decoded == rows, 'PLC1/PLC2 semantic mismatch')
    return result, {'format': 'PLC2', 'source': identity(image), 'image': identity(result),
                    'owner_consumer_pairs': len(rows), 'unique_records': len(offsets),
                    'semantic_rows_equal': True, 'owner_policy_equal': True,
                    'source_regenerations': 0, 'archive_moves_granted': 0}


def compact_rows(image: bytes) -> list[bytes | None]:
    """レコード境界・未参照データも検査する独立した配置側validator。"""
    need(DATA <= len(image) < 0xFFFF, 'PLC2 size')
    need(HEADER.unpack_from(image) == (b'PLC2', 1, COUNT, POLICY, INDEX, DATA,
                                      len(image), MASK, 0), 'PLC2 header')
    need(all(1 <= p <= 7 for p in image[POLICY:POLICY + COUNT]), 'PLC2 policy')
    need(image[POLICY + COUNT:INDEX] == b'\0' and image[INDEX + COUNT * 10:DATA] == bytes(2),
         'PLC2 alignment')
    records: dict[int, bytes] = {}
    at = DATA
    while at < len(image):
        need(len(image) - at >= 2, 'PLC2 record header')
        tag = struct.unpack_from('<H', image, at)[0]
        need(tag == 0x8040 or tag <= 50, 'PLC2 record type')
        length = 16 if tag == 0x8040 else tag * 2
        need(length <= len(image) - at - 2, 'PLC2 record bounds')
        raw = image[at + 2:at + 2 + length]
        if tag == 0x8040:
            need(raw[8:] == bytes(8), 'PLC2 tutor padding')
        else:
            need(all(1 <= m[0] <= 1062 for m in struct.iter_unpack('<H', raw)), 'PLC2 move')
        records[at] = image[at:at + 2 + length]
        at += 2 + length
    used = set()
    result = []
    for index in range(COUNT * 5):
        offset = struct.unpack_from('<H', image, INDEX + index * 2)[0]
        if image[POLICY + index // 5] != 1:
            need(offset == 0xFFFF, 'PLC2 non-learning span')
            result.append(None)
        else:
            need(offset in records, 'PLC2 not a record boundary')
            row = records[offset]
            tag = struct.unpack_from('<H', row)[0]
            need((tag == 0x8040) == (index % 5 == 4), 'PLC2 consumer type')
            used.add(offset)
            result.append(row)
    need(used == set(records), 'PLC2 unreferenced record')
    need(len(set(records.values())) == len(records), 'PLC2 duplicate record')
    return result
