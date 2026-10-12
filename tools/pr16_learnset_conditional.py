"""受入済み条件payloadをPLC1へbyte単位で再配置する。原本再収集/再採用なし。"""
from __future__ import annotations
from pathlib import Path
import struct
from tools import pr16_learnset_runtime as prior
from tools import pr16_learnset_successor as source

FAMILIES = ('egg', 'evolution', 'reminder', 'shared_egg', 'tutor')
IDS = (0, 1, 6, 7, 8)
COUNT = 1671
DATA = 1704 + COUNT * 5 * 8
need = prior.need


def compose(root: Path, parent: Path, floette: Path) -> tuple[bytes, dict]:
    """元poolを全byte保持。eggのmarkerとEOFは候補moveとして参照しない。"""
    pc = prior.accepted_files(root, parent, prior.PARENT)
    fc = prior.accepted_files(root, floette, prior.FLOETTE)
    policies = (floette / 'owner-policies.bin').read_bytes()
    need(len(policies) == COUNT and policies.count(1) == 1483 and all(1 <= x <= 7 for x in policies), 'owner policy不正')
    rows = list(source.rows(floette / 'consumer-index.jsonl'))
    index = {(r['species_id'], r['consumer']): r for r in rows}
    need(len(rows) == len(index) == COUNT * 9, 'owner/consumer重複・欠落')
    image = bytearray(DATA)
    image[32:32 + COUNT] = policies
    copies, pools, positions = [], {}, {}
    for sid, directory, prefix in ((0, parent, ''), (1029, floette, 'floette.')):
        for family in FAMILIES:
            name = prefix + family + '.bin'
            raw = (directory / name).read_bytes()
            need(len(raw) % 2 == 0, 'pool alignment不正')
            at = len(image); image.extend(raw)
            pools[sid, family], positions[sid, family] = raw, at
            copies.append({'arena': 'FLOETTE_DELTA' if sid else 'ACCEPTED_PARENT',
                           'file': name, 'image_offset': at, **source.identity(directory / name)})
    counts = dict.fromkeys(FAMILIES, 0)
    for sid, policy in enumerate(policies):
        for column, (family, cid) in enumerate(zip(FAMILIES, IDS)):
            row = index[sid, family]; tag = (sid << 4) | cid
            if policy != 1:
                need(row['status'] == 'IDENTITY_ONLY_NO_REPLACEMENT' and row['payload'] is None, '188保全枠への候補付与禁止')
                offset, count = 0xFFFFFFFF, 0
            else:
                need(row['status'] == 'PAYLOAD_PREPARED_NOT_INSTALLED', '未採用owner')
                arena = 1029 if sid == 1029 else 0
                span = row['payload']; pool = pools[arena, family]
                name = ('floette.' if arena else '') + family + '.bin'
                at, size = span['offset'], span['size']
                need(span['file'] == name and type(at) is int and type(size) is int and at % 2 == size % 2 == 0
                     and 0 <= at <= len(pool) and 0 <= size <= len(pool) - at, '別consumer/arena/spanの混入')
                raw = pool[at:at + size]; offset = positions[arena, family] + at
                if family == 'tutor':
                    need(size == 16 and not any(raw[8:]), '未供給tutor上位slot禁止')
                    count = 64
                else:
                    if family == 'egg':
                        need(len(raw) >= 2 and struct.unpack_from('<H', raw)[0] == 20000 + sid, 'egg owner marker不一致')
                        raw = raw[2:]; offset += 2
                        if raw.endswith(b'\xff\xff'): raw = raw[:-2]
                    moves = [x[0] for x in struct.iter_unpack('<H', raw)]
                    need(len(moves) <= 50 and all(1 <= x <= 1062 for x in moves), 'move容量/Side Change/marker混入')
                    count = len(moves)
                counts[family] += count if family != 'tutor' else sum(x.bit_count() for x in raw)
            struct.pack_into('<IHH', image, 1704 + (sid * 5 + column) * 8, offset, count, tag)
    struct.pack_into('<4sHHIIIIII', image, 0, b'PLC1', 1, COUNT, 32, 1704, DATA, len(image), 0x1C3, 0)
    return bytes(image), {'format': 'PLC1', 'species_count': COUNT, 'learning_owners': 1483,
        'identity_only_preserved': 188, 'families': list(FAMILIES), 'counts': counts, 'copies': copies,
        'parent_run': pc['run_id'], 'floette_run': fc['run_id'], 'size': len(image),
        'accepted_source_regenerations': 0, 'accepted_payload_regenerations': 0,
        'archive_moves_granted': 0, 'conditional_breeding_flattened': False,
        'form_change_connected': False, 'existing_moves_rewritten': False,
        'gameplay_e2e_accepted': False, 'issue19_complete': False, 'release_ready': False}
