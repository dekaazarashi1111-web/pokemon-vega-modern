"""保存済み不足技archiveを順序不変のPLA1へ圧縮。原本/PLC2は生成しない。"""
from __future__ import annotations
import hashlib
import heapq
import json
from pathlib import Path
import struct

COUNT = 1671
FAMILIES = ('machine', 'tutor')
LIMITS = (160, 40)
HEADER = struct.Struct('<4sHHHBBIIIII')
DIRECTORY = 32
TEMPLATES = DIRECTORY + COUNT * 4
MAX_DEPTH = 8
MAGIC = b'PLA1'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def accepted_rows(parent: Path, floette: Path):
    """最新の明示owner indexのみ使用。祖先/旧ROM/通常Floetteへfallbackしない。"""
    policies = (floette/'owner-policies.bin').read_bytes()
    need(len(policies) == COUNT and set(policies) <= set(range(1, 8)), 'owner policy不一致')
    entries = {}
    for line in (floette/'consumer-index.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        key = row['species_id'], row['consumer']
        need(key not in entries, 'index重複')
        entries[key] = row
    need(len(entries) == COUNT * 9, 'index件数不一致')
    pools = {}
    result = {}
    for sid, policy in enumerate(policies):
        for family, limit in zip(FAMILIES, LIMITS):
            entry = entries[sid, family]
            if policy != 1:
                need(entry['payload'] is None and 'archive' not in entry,
                     '非学習ownerのarchive')
                result[sid, family] = None
                continue
            a = entry['archive']
            file = ('floette.' if sid == 1029 else '') + family + '_archive.bin'
            need(a['file'] == file and type(a['offset']) is int and a['offset'] >= 0,
                 'archive owner/path不一致')
            path = (floette if sid == 1029 else parent)/file
            if path not in pools:
                pools[path] = path.read_bytes()
            start, size = a['offset'], a['size']
            need(type(size) is int and size == a['moves'] * 2 and size % 2 == 0
                 and 0 <= a['moves'] <= limit and start + size <= len(pools[path]),
                 'archive span/capacity不一致')
            seq = tuple(x[0] for x in struct.iter_unpack('<H', pools[path][start:start+size]))
            need(all(1 <= m <= 1062 for m in seq) and len(set(seq)) == len(seq),
                 'archive技ID/重複不一致')
            result[sid, family] = seq
    return result, policies


def topology(graph):
    """set/hash seedの順序に依存しない最小技ID優先の位相順。"""
    degree = {m: len(p) for m, p in graph.items()}
    children = {m: [] for m in graph}
    for m, predecessors in graph.items():
        for p in predecessors:
            children[p].append(m)
    ready = [m for m, n in degree.items() if n == 0]
    heapq.heapify(ready)
    result = []
    while ready:
        m = heapq.heappop(ready)
        result.append(m)
        for child in sorted(children[m]):
            degree[child] -= 1
            if degree[child] == 0:
                heapq.heappush(ready, child)
    return tuple(result) if len(result) == len(graph) else None


def compose(rows, policies):
    need(set(rows) == {(s, f) for s in range(COUNT) for f in FAMILIES}, 'owner/family集合不一致')
    need(len(policies) == COUNT and set(policies) <= set(range(1, 8)), 'owner policy不一致')
    sequences = set()
    for (sid, family), seq in rows.items():
        need((seq is None) == (policies[sid] != 1), 'owner action不一致')
        if seq is not None:
            need(isinstance(seq, tuple) and len(seq) <= LIMITS[FAMILIES.index(family)]
                 and len(set(seq)) == len(seq) and all(type(m) is int and 1 <= m <= 1062 for m in seq),
                 'archive行不正')
            sequences.add(seq)
    need(sequences, '明示行なし')
    graphs, members = [], []
    for seq in sorted(sequences, key=lambda x: (-len(x), x)):
        edges = {m: set() for m in seq}
        for a, b in zip(seq, seq[1:]):
            edges[b].add(a)
        for i, graph in enumerate(graphs):
            merged = {m: graph.get(m, set()) | edges.get(m, set()) for m in sorted(set(graph) | set(edges))}
            if topology(merged) is not None:
                graphs[i] = merged
                members[i].append(seq)
                break
        else:
            graphs.append(edges)
            members.append([seq])
    templates = [topology(g) for g in graphs]
    # Empty-only synthetic inputs still receive a valid template with no selected bits.
    templates = [t or (1,) for t in templates]
    need(1 <= len(templates) <= 16 and all(len(t) <= 256 for t in templates), 'template容量超過')
    raw = bytearray(TEMPLATES + len(templates) * 4)
    for i, template in enumerate(templates):
        struct.pack_into('<HH', raw, TEMPLATES+i*4, len(raw), len(template))
        raw.extend(struct.pack('<'+'H'*len(template), *template))
    records_start = len(raw)
    locations, depths, record_count = {}, [], 0
    for ti, group in enumerate(members):
        template = templates[ti]
        pos = {m: i for i, m in enumerate(template)}
        n = (len(template)+7)//8
        previous = []
        for seq in sorted(group, key=lambda x: (len(x), x)):
            mask = bytearray(n)
            for m in seq:
                mask[pos[m]//8] |= 1 << (pos[m] % 8)
            need(tuple(m for i, m in enumerate(template) if mask[i//8] >> (i % 8) & 1) == seq,
                 'templateで順序変化')
            # Literal, or bounded XOR differences against an earlier same-template row.
            choices = [(3+n, 0, 0xffff, None)]
            for at, prior, depth in previous:
                if depth < MAX_DEPTH:
                    count = sum(a != b for a, b in zip(mask, prior))
                    choices.append((3+(n+7)//8+count, depth+1, at, prior))
            _, depth, base, prior = min(choices, key=lambda x: x[:3])
            at = len(raw)
            raw.extend(struct.pack('<HB', base, ti))
            if prior is None:
                raw.extend(mask)
            else:
                changed = bytearray((n+7)//8)
                delta = bytearray()
                for i, (a, b) in enumerate(zip(mask, prior)):
                    if a != b:
                        changed[i//8] |= 1 << (i % 8)
                        delta.append(a ^ b)
                raw.extend(changed)
                raw.extend(delta)
            locations[seq] = at
            previous.append((at, bytes(mask), depth))
            depths.append(depth)
            record_count += 1
    need(len(raw) < 65535, '16-bit配置上限')
    for sid in range(COUNT):
        for fi, family in enumerate(FAMILIES):
            seq = rows[sid, family]
            struct.pack_into('<H', raw, DIRECTORY+(sid*2+fi)*2,
                             0xffff if seq is None else locations[seq])
    HEADER.pack_into(raw, 0, MAGIC, 1, HEADER.size, COUNT, len(templates), MAX_DEPTH,
                     DIRECTORY, TEMPLATES, records_start, len(raw), record_count)
    image = bytes(raw)
    decoded = validate(image)
    need(decoded == rows, '全owner/順序/技列の同値性不一致')
    return image, {'format': 'PLA1', 'image': identity(image), 'owners': COUNT,
        'owner_family_pairs': len(rows), 'learning_owners': policies.count(1),
        'identity_only_owners': COUNT-policies.count(1), 'templates': len(templates),
        'unique_rows': record_count, 'max_delta_depth': max(depths),
        'machine_moves': sum(len(v) for (s, f), v in rows.items() if f == 'machine' and v is not None),
        'tutor_moves': sum(len(v) for (s, f), v in rows.items() if f == 'tutor' and v is not None),
        'max_machine_rows': max(len(v) for (s, f), v in rows.items() if f == 'machine' and v is not None),
        'max_tutor_rows': max(len(v) for (s, f), v in rows.items() if f == 'tutor' and v is not None),
        'all_rows_order_equal': True, 'accepted_source_regenerations': 0,
        'accepted_payload_regenerations': 0, 'game_tutor_connected': False,
        'archive_rebound': False, 'physical_supply_verified': False,
        'gameplay_e2e_accepted': False, 'issue19_complete': False, 'release_ready': False}


def validate(raw):
    """独立構造walk: 全record境界、全参照、未参照/重複/循環/余剰を拒否。"""
    need(len(raw) >= HEADER.size, '短いheader')
    magic, version, size, count, nt, depth_limit, directory, table, records, total, nr = HEADER.unpack_from(raw)
    need((magic, version, size, count, directory, table, total, depth_limit) ==
         (MAGIC, 1, 32, COUNT, DIRECTORY, TEMPLATES, len(raw), MAX_DEPTH), 'header不一致')
    need(1 <= nt <= 16 and 1 <= nr <= COUNT*2 and table+nt*4 <= records <= total < 65535, 'header境界')
    cursor = table+nt*4
    templates = []
    for i in range(nt):
        at, count = struct.unpack_from('<HH', raw, table+i*4)
        need(at == cursor and 1 <= count <= 256 and at+count*2 <= records, 'template境界')
        seq = tuple(x[0] for x in struct.iter_unpack('<H', raw[at:at+count*2]))
        need(len(set(seq)) == count and all(1 <= m <= 1062 for m in seq), 'template技ID/重複')
        templates.append(seq)
        cursor += count*2
    need(cursor == records, 'template余剰')
    decoded, types, depths, sequences = {}, {}, {}, set()
    for _ in range(nr):
        at = cursor
        need(cursor+3 <= total, 'record切詰め')
        base, ti = struct.unpack_from('<HB', raw, cursor)
        cursor += 3
        need(ti < nt, 'template参照不正')
        template = templates[ti]
        n = (len(template)+7)//8
        if base == 0xffff:
            need(cursor+n <= total, 'literal切詰め')
            mask = bytearray(raw[cursor:cursor+n])
            cursor += n
            depth = 0
        else:
            need(base in decoded and types[base] == ti and depths[base] < depth_limit, 'base境界/型/深さ')
            nselectors = (n+7)//8
            need(cursor+nselectors <= total, 'selector切詰め')
            selectors = int.from_bytes(raw[cursor:cursor+nselectors], 'little')
            cursor += nselectors
            need(selectors >> n == 0, 'selector padding')
            mask = bytearray(decoded[base])
            for i in range(n):
                if selectors >> i & 1:
                    need(cursor < total and raw[cursor] != 0, 'delta切詰め/zero')
                    mask[i] ^= raw[cursor]
                    cursor += 1
            depth = depths[base]+1
        need(int.from_bytes(mask, 'little') >> len(template) == 0, 'mask padding')
        seq = tuple(m for i, m in enumerate(template) if mask[i//8] >> (i % 8) & 1)
        need(seq not in sequences, '重複record')
        sequences.add(seq)
        decoded[at], types[at], depths[at] = bytes(mask), ti, depth
    need(cursor == total, 'record余剰')
    rows, used = {}, set()
    for sid in range(COUNT):
        for fi, family in enumerate(FAMILIES):
            at = struct.unpack_from('<H', raw, DIRECTORY+(sid*2+fi)*2)[0]
            if at == 0xffff:
                rows[sid, family] = None
                continue
            need(at in decoded, 'directory境界')
            used.add(at)
            mask, template = decoded[at], templates[types[at]]
            seq = tuple(m for i, m in enumerate(template) if mask[i//8] >> (i % 8) & 1)
            need(len(seq) <= LIMITS[fi], 'consumer容量')
            rows[sid, family] = seq
        need((rows[sid, 'machine'] is None) == (rows[sid, 'tutor'] is None), 'owner不一致')
    need(used == set(decoded), '未参照record')
    return rows
