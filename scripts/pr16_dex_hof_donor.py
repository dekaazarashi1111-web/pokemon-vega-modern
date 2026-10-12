#!/usr/bin/env python3
"""旧egg ownerの参照形を現候補へ再束縛する読取専用監査。donor権限は発行しない。"""
from __future__ import annotations

import collections
import hashlib
import io
import json
import struct
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000
DONOR_LO = 0x09FED0C4
DONOR_SIZE = 15118
DONOR_HI = DONOR_LO + DONOR_SIZE
STAGE75 = 'modernization_rockruff_own_tempo_stage75_payload'
PROOFS = (
    'content/modernization/pr16_dex_union_tail_lease.json',
    'content/modernization/pr16_dex_fallback_tail_lease.json',
    'content/modernization/pr16_dex_hof_tail_lease.json',
)
# 既受入proofとその型decoderを個別に固定。manifestのowner名だけでは分類しない。
SOURCE_SHA256 = {
    PROOFS[0]: '42992e362bca9f807cbe55697955dcaf40ea214bf0a486ea217ab179d9380f80',
    PROOFS[1]: '51e2f9bd2709bf7fa485db6c0f8b7822edb64cc952f1cc6c287f1c7c3f0d228a',
    PROOFS[2]: '5af6a4932ccf87c0183a1ece1423416d79a5f989cdcb348db78534396c6879be',
    'scripts/pr16_dex_tail_lease.py': 'f0b8d18b4ff533372a10841ff08b71506c4a305e5d9126704ec919d985572ee6',
    'scripts/pr16_dex_fallback_tail_lease.py': 'b58773fe21c1e42c0e0fa287dfe8b067b4d41b0f3b668ba12b016204526413aa',
    'scripts/build_species_surface.py': 'd032f6cbf3e38914e332899deed99168873d85746f3c340cdafc5bc5db791bad',
    'config/species_surface.json': 'b490fcea065d0b1c176784139355312618061258d715e5785132b72908eee160',
    'config/modernization_rockruff_own_tempo_stage75.json': '2accef3c5cb3e45e3b032035acfbc727b2785deafd652a45f56ca0db3ebbf121',
    'content/modernization/rockruff_own_tempo_stage75_contract.json': 'f57efb88124fdf18681a012d520d4382b715763c917fd40eb56a30ba6dce5684',
    'content/modernization/p04_species_runtime_contract.json': '80ded428ec1df683b758555c8e4357123baee2ce8b5201dea960fa89618818a4',
}
SOURCE_GIT_BLOB = {
    'tools/modernization_rockruff_own_tempo_stage75.py': '42572388e42476ce46c0a0376859d3efde403621',
    'tools/modernization_p04_species_runtime.py': '3bfe8d18fa09a38e9aaf992830e79ad11e64e765',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def canonical(value):
    value &= ~1
    return BASE + (value - BASE) % 0x02000000 if BASE <= value < 0x0E000000 else -1


def contains(lo, hi, address, size=4):
    return type(size) is int and size > 0 and lo <= address and address + size <= hi


def chunk(raw, address, size):
    need(type(address) is int and type(size) is int and size > 0,
         'positive integer ROM window')
    offset = address - BASE
    need(0 <= offset and offset + size <= len(raw), 'bounded ROM window')
    return raw[offset:offset + size]


def u32(raw, address):
    return struct.unpack('<I', chunk(raw, address, 4))[0]


def signed(raw, node):
    """assetだけでなく、既存proofのheader/row/consumer全体を照合する。"""
    if isinstance(node, dict):
        if {'address', 'size', 'sha256'} <= node.keys():
            need(identity(chunk(raw, node['address'], node['size'])) ==
                 {k: node[k] for k in ('size', 'sha256')}, 'typed window identity drift')
        for value in node.values():
            signed(raw, value)
    elif isinstance(node, list):
        for value in node:
            signed(raw, value)


def source_bindings(root=ROOT):
    result = {}
    for path in sorted(set(SOURCE_SHA256) | set(SOURCE_GIT_BLOB)):
        p = root / path
        need(p.is_file() and not p.is_symlink(), 'missing regular typed source: ' + path)
        raw = p.read_bytes()
        record = identity(raw)
        if path in SOURCE_SHA256:
            need(record['sha256'] == SOURCE_SHA256[path], 'typed source SHA drift: ' + path)
        if path in SOURCE_GIT_BLOB:
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            need(blob == SOURCE_GIT_BLOB[path], 'typed source Git blob drift: ' + path)
            record['git_blob_sha'] = blob
        result[path] = record
    return result


def inventory(raw, lo=DONOR_LO, hi=DONOR_HI):
    """全byte開始/全3mirror/Thumb-bitと全halfword開始BL形。境界を跨ぐoriginを落とさない。"""
    need(BASE <= lo < hi <= BASE + len(raw), 'donor inside ROM')
    result = []
    for offset in range(len(raw) - 3):
        target = canonical(struct.unpack_from('<I', raw, offset)[0])
        address = BASE + offset
        if lo <= target < hi and not contains(lo, hi, address):
            result.append(dict(address=address, target=target,
                               kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
                               **identity(raw[offset:offset + 4])))
    for offset in range(0, len(raw) - 3, 2):
        first, second = struct.unpack_from('<HH', raw, offset)
        if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
            continue
        displacement = ((first & 0x7FF) << 12) | ((second & 0x7FF) << 1)
        if displacement & (1 << 22):
            displacement -= 1 << 23
        target = BASE + offset + 4 + displacement
        address = BASE + offset
        if lo <= target < hi and not contains(lo, hi, address):
            result.append(dict(address=address, target=target, kind='THUMB_BL_SHAPE',
                               **identity(raw[offset:offset + 4])))
    return result


@dataclass(frozen=True)
class TypedRegion:
    start: int
    end: int
    kind: str
    evidence: dict


def decode_lz_at(raw, address, maximum=100000):
    """既存LZ10 decoderへ渡す正確な入力終端をbounded parseで求める。paddingは含めない。"""
    import pr16_dex_tail_lease as decoder
    header = chunk(raw, address, 4)
    need(header[0] == 0x10, 'rooted GBA LZ10 asset header')
    size = int.from_bytes(header[1:4], 'little')
    need(0 < size <= maximum, 'bounded rooted decoded asset')
    cursor, produced = 4, 0
    while produced < size:
        flags = chunk(raw, address + cursor, 1)[0]
        cursor += 1
        for bit in range(7, -1, -1):
            if produced == size:
                break
            if flags & (1 << bit):
                a, b = chunk(raw, address + cursor, 2)
                cursor += 2
                length, distance = (a >> 4) + 3, ((a & 15) << 8 | b) + 1
                need(distance <= produced and produced + length <= size,
                     'rooted LZ10 back-reference extent')
                produced += length
            else:
                chunk(raw, address + cursor, 1)
                cursor += 1
                produced += 1
    encoded = chunk(raw, address, cursor)
    decoded = decoder.lz(encoded)
    need(len(decoded) == size, 'whole rooted LZ10 output')
    return encoded, decoded


def wave_asset(raw, address):
    import pr16_dex_fallback_tail_lease as decoder
    typ, status, frequency, loop, samples = struct.unpack('<HHIII', chunk(raw, address, 16))
    need(typ in (0, 1) and status in (0, 0x4000) and 0 < samples <= 1000000,
         'bounded direct-sound WaveData type')
    need(0 <= loop < samples and frequency > 0, 'rooted WaveData loop/frequency')
    payload_size = decoder.dpcm_size(samples) if typ == 1 else samples
    encoded = chunk(raw, address, 16 + payload_size)
    decoded = decoder.decode_dpcm(encoded[16:], samples) if typ == 1 else encoded[16:]
    return encoded, decoded, 'dpcm4' if typ else 'pcm8'


def validate_existing_root(raw, record, proof_path, selector, root=ROOT):
    """既受入の型付きroot証拠を最新byteで再確認。解読形だけの新root推定は禁止。"""
    kind, address = record['kind'], record['address']
    need(kind in ('pcm8', 'dpcm4', 'pcm8_source_exact', 'lz77'), 'unsupported typed asset')
    signed(raw, record)
    evidence = dict(source_path=proof_path, selector=selector,
                    asset=dict(address=address, size=record['size'], sha256=record['sha256']))
    refs = record.get('refs', [])
    if kind == 'pcm8_source_exact':
        source = root / 'vendor/upstream/CFRU-JP/audio/sounds/Wav_grass_footstep_sample.wav'
        need(source.is_file() and not source.is_symlink(), 'independent fixed WAV unavailable')
        source_raw = source.read_bytes()
        need(identity(source_raw) == dict(size=record['source_size'], sha256=record['source_sha256']),
             'independent fixed WAV identity')
        with wave.open(io.BytesIO(source_raw), 'rb') as wav:
            need((wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) ==
                 (record['source_wav_channels'], record['source_wav_sample_width'], record['source_wav_rate']),
                 'independent WAV format')
            pcm = bytes(x ^ 128 for x in wav.readframes(wav.getnframes()))
        need(pcm == chunk(raw, address + 16, record['decoded_size']), 'all fixed WAV sample bytes')
        evidence['source_asset'] = dict(path=str(source.relative_to(root)), **identity(source_raw))
    else:
        need(refs, 'typed asset consumer provenance required')
        if kind in ('pcm8', 'dpcm4'):
            need(all(isinstance(ref, dict) and 'tone_record' in ref for ref in refs),
                 'every audio consumer needs signed typed ToneData provenance')
    for ref in refs:
        site = ref['address'] if isinstance(ref, dict) else ref
        need(u32(raw, site) == address, 'all declared asset pointers remain rooted')
        if isinstance(ref, dict):
            need(ref['value'] == address, 'declared asset pointer value')
        if isinstance(ref, dict) and 'tone_record' in ref:
            tone = ref['tone_record']
            need(tone['address'] + 4 == site and tone['size'] == 12, 'ToneData pointer field')
            fields = struct.unpack('<4BI4B', chunk(raw, tone['address'], 12))
            need(list(fields) == tone['fields'] and fields[0] & 0xC7 == 0 and
                 fields[1] <= 127 and fields[4] == address, 'whole typed direct-sound ToneData')
    if kind == 'lz77':
        need(record.get('typed_tables'), 'LZ asset needs typed table consumer')
        for table in record['typed_tables']:
            row = table['row']
            need(table['stride'] == 8 and row['size'] == 8 and row['address'] ==
                 table['table_address'] + 8 * table['row_index'], 'typed sprite row placement')
            need(struct.unpack('<IHH', chunk(raw, row['address'], 8)) ==
                 (address, row['size_field'], row['tag_field']), 'typed sprite row fields')
            need(table['table_root_sites'], 'live sprite consumer roots')
            for ref in table['table_root_sites']:
                need(u32(raw, ref['address']) == ref['value'] == table['table_address'], 'live sprite table root')
        encoded, decoded = decode_lz_at(raw, address)
        payload_start = address + 4
    else:
        encoded, decoded, observed_kind = wave_asset(raw, address)
        need(observed_kind == ('pcm8' if kind == 'pcm8_source_exact' else kind), 'declared WaveData codec')
        fields = struct.unpack('<HHIII', encoded[:16])
        need(fields == tuple(record[k] for k in ('wave_type', 'wave_status', 'wave_frequency',
                                                 'wave_loop_start', 'decoded_size')), 'all WaveData header fields')
        payload_start = address + 16
    need(identity(encoded) == dict(size=record['size'], sha256=record['sha256']),
         'exact encoded extent and identity')
    need(identity(decoded) == dict(size=record['decoded_size'], sha256=record['decoded_sha256']),
         'whole decoded asset identity')
    evidence['decoded'] = identity(decoded)
    return TypedRegion(payload_start, address + len(encoded), kind, evidence)


def bind_owners(raw, checkpoint):
    rows = checkpoint['placement']['owner_byte_audit']
    owners = {row['name']: row for row in rows}
    need(len(owners) == len(rows), 'unique exact owner bindings')
    allocation = checkpoint['placement']['allocation']['allocations']
    need(len(allocation) == len(owners) and {r['name'] for r in allocation} == set(owners),
         'complete allocator to current byte-owner join')
    for row in allocation:
        current = owners[row['name']]
        need((current['address'], current['size']) == (BASE + row['start'], row['size']) and
             row['start'] + row['size'] == row['end_exclusive'], 'exact declared owner extent')
    for row in rows:
        need(identity(chunk(raw, row['address'], row['size'])) ==
             dict(size=row['size'], sha256=row['after_sha256']), 'latest owner actual bytes')
    return owners


def compare_inventory(hits, previous):
    fields = ('address', 'target', 'kind', 'size', 'sha256')
    key = lambda r: tuple(r[k] for k in fields)
    before, after = {key(r) for r in previous['hits']}, {key(r) for r in hits}
    need(len(before) == len(previous['hits']) and len(after) == len(hits), 'unique scan identities')
    render = lambda keys: [dict(zip(fields, k)) for k in sorted(keys)]
    return dict(previous_candidate=previous['candidate'], previous_count=len(before), current_count=len(after),
                same_inventory=before == after, introduced=render(after - before), removed=render(before - after))


def species_regions(raw, owners, documents, hits):
    """Stage75の全root集合から全sprite/cry行を辿る。任意header走査はしない。"""
    p04 = documents['content/modernization/p04_species_runtime_contract.json']
    contract = documents['content/modernization/rockruff_own_tempo_stage75_contract.json']['table_contract']
    need(contract['new_species_count'] == 1671 and contract['old_species_count'] == 1670,
         'fixed Stage75 species table generation')
    owner = owners[STAGE75]
    owner_lo, owner_hi = owner['address'], owner['address'] + owner['size']
    regions, diagnostics, table_bindings = [], [], []
    seen, decoded_cache, region_by_key = set(), {}, {}
    for name in ('species_front', 'species_back', 'species_palette', 'species_shiny_palette', 'species_cry', 'species_cry2'):
        table = p04['tables'][name]
        stride = 12 if name in ('species_cry', 'species_cry2') else 8
        need(table['stride'] == stride and table['new_count'] == 1670 and
             name in contract['relocated_species_tables'], 'source-defined species table schema')
        sites = table['pointer_consumers']['site_offsets']
        need(sites == sorted(set(sites)) and len(sites) == table['pointer_consumers']['count'] and sites,
             'complete pinned typed consumer set')
        address = u32(raw, BASE + sites[0])
        need(all(u32(raw, BASE + site) == address for site in sites), 'all live Stage75 typed table roots')
        size = 1671 * stride
        need(contains(owner_lo, owner_hi, address, size), 'whole typed table inside bound Stage75 owner')
        table_raw = chunk(raw, address, size)
        binding = dict(name=name, address=address, **identity(table_raw), stride=stride, rows=1671,
                       consumer_sites=[dict(address=BASE + site, **identity(chunk(raw, BASE + site, 4))) for site in sites],
                       source='tools/modernization_rockruff_own_tempo_stage75.py#_table_rows',
                       contract='content/modernization/p04_species_runtime_contract.json#tables/' + name,
                       owner=STAGE75)
        table_bindings.append(binding)
        for index in range(1671):
            row_address = address + index * stride
            row = table_raw[index * stride:(index + 1) * stride]
            try:
                if stride == 12:
                    fields = struct.unpack('<4BI4B', row)
                    need(fields[0] & 0xC7 == 0 and fields[1] <= 127, 'direct-sound cry ToneData required')
                    asset = fields[4]
                    key = ('wave', asset)
                    if key not in decoded_cache:
                        decoded_cache[key] = wave_asset(raw, asset)
                    encoded, decoded, kind = decoded_cache[key]
                    payload = asset + 16
                else:
                    asset, first, second = struct.unpack('<IHH', row)
                    if name in ('species_front', 'species_back'):
                        need(first in (2048, 4096, 8192) and second == index, 'source typed CompressedSpriteSheet row')
                    else:
                        need(first == index + (1621 if name == 'species_shiny_palette' else 0), 'source typed palette tag')
                    key = ('lz77', asset)
                    if key not in decoded_cache:
                        decoded_cache[key] = decode_lz_at(raw, asset)
                    encoded, decoded = decoded_cache[key]
                    expected = (32, 64, 128) if 'palette' in name else (2048, 4096, 8192)
                    need(len(decoded) in expected, 'source typed sprite/palette decoded size')
                    kind, payload = 'lz77', asset + 4
                # source assetがdonor自体を跨ぐなら「非参照」とはしない。
                need(asset + len(encoded) <= DONOR_LO or DONOR_HI <= asset,
                     'typed asset itself overlaps retired owner')
                # 同assetの別table consumerも行型・解読size検証を済ませてから統合する。
                if key in seen:
                    if key in region_by_key:
                        consumers = region_by_key[key].evidence['consumers']
                        same_table = next((r for r in consumers if r['table'] == name), None)
                        if same_table is None:
                            consumers.append(dict(table=name, row_indices=[index]))
                        else:
                            same_table['row_indices'].append(index)
                    continue
                seen.add(key)
                if not any(contains(payload, asset + len(encoded), hit['address']) for hit in hits):
                    continue
                evidence = dict(source_path='tools/modernization_rockruff_own_tempo_stage75.py',
                                selector='_table_rows/' + name, table=name,
                                table_address=address, row_index=index,
                                row=dict(address=row_address, **identity(row)),
                                asset=dict(address=asset, **identity(encoded)), decoded=identity(decoded),
                                consumers=[dict(table=name, row_indices=[index])])
                region = TypedRegion(payload, asset + len(encoded), kind, evidence)
                regions.append(region)
                region_by_key[key] = region
            except ValueError as exc:
                # 不明instrument/圧縮形を推測して救済しない。
                diagnostics.append(dict(table=name, row_index=index, reason=str(exc)))
    return regions, table_bindings, diagnostics


def classify_hits(hits, regions, owners=()):
    result = []
    for hit in hits:
        witnesses = [r for r in regions if contains(r.start, r.end, hit['address'], hit['size'])]
        kinds = {('pcm8' if r.kind == 'pcm8_source_exact' else r.kind) for r in witnesses}
        accepted = len(kinds) == 1
        row = dict(hit, classification='FALSE_POSITIVE_TYPED_' + next(iter(kinds)).upper()
                   if accepted else 'UNCLASSIFIED', accepted=accepted)
        if accepted:
            row['evidence'] = [r.evidence for r in witnesses]
        else:
            row['reason'] = 'conflicting_typed_asset_witnesses' if len(kinds) > 1 else 'no_complete_typed_asset_consumer_witness'
            row['owner_candidates'] = [r['name'] for r in owners
                                       if contains(r['address'], r['address'] + r['size'], hit['address'], hit['size'])]
        result.append(row)
    return result


def audit(current, checkpoint, root=ROOT):
    need(len(current) == 0x02000000 and identity(current) == checkpoint['candidate'], 'exact current candidate and CP')
    bindings = source_bindings(root)
    documents = {p: json.loads((root / p).read_bytes()) for p in bindings if p.endswith('.json')}
    owners = bind_owners(current, checkpoint)
    old = owners['modernization_p03_stage67_normal_egg_rows']
    live = owners['modernization-p07-preserved-egg']
    need((old['address'], old['size']) == (DONOR_LO, DONOR_SIZE), 'exact Stage67 owner extent')
    need((live['address'], live['size']) == (0x095D9EFC, 15396), 'exact live P07 egg owner')
    roots = (BASE + 0x45214, BASE + 0x4528C)
    need(all(u32(current, site) == live['address'] for site in roots), 'all known egg roots migrated')
    need(u32(current, BASE + 0x45288) == 7696, 'live egg scan limit')
    words = struct.unpack('<7698H', chunk(current, live['address'], live['size']))
    need(words[-1] == 65535 and words[0] >= 20000 and all(x < 22000 for x in words[:-1]),
         'live egg table is bounded value encoding')
    hits = inventory(current)
    prior_comparison = compare_inventory(hits, checkpoint['capacity_donor_audit'])
    regions, diagnostics = [], []
    for path in PROOFS:
        for index, record in enumerate(documents[path]['roots']):
            if record['kind'] not in ('pcm8', 'dpcm4', 'pcm8_source_exact', 'lz77'):
                continue
            skip = 4 if record['kind'] == 'lz77' else 16
            if not any(contains(record['address'] + skip, record['address'] + record['size'], hit['address']) for hit in hits):
                continue
            try:
                regions.append(validate_existing_root(current, record, path, 'roots/' + str(index), root))
            except (ValueError, wave.Error) as exc:
                diagnostics.append(dict(source_path=path, selector='roots/' + str(index), reason=str(exc)))
    expanded, tables, unsupported = species_regions(current, owners, documents, hits)
    regions.extend(expanded)
    classified = classify_hits(hits, regions, owners.values())
    unknown = sum(not row['accepted'] for row in classified)
    return dict(schema_version=1, status='AUDIT_ONLY_TYPED_CLASSIFICATION_NO_DONOR_LEASE',
                candidate=identity(current), retired_candidate=old, current_replacement=live,
                active_roots=[dict(address=a, points_to=live['address'], **identity(chunk(current, a, 4))) for a in roots],
                current_scan_limit=7696,
                scan_scope='all32MiB every byte-start U32 all ROM mirrors/Thumb-bit and every halfword ThumbBL; whole15118byte owner; boundary-overlap origins retained',
                source_bindings=bindings, typed_tables=tables, hits=classified,
                prior_inventory_comparison=prior_comparison,
                candidates=len(hits), classified=len(hits) - unknown, unclassified=unknown,
                classifications=dict(collections.Counter(row['classification'] for row in classified)),
                verified_asset_witnesses=len(regions), evidence_diagnostics=diagnostics,
                unsupported_typed_rows=unsupported, donor_leased=False, donor_eligible=False,
                indirect_reference_completeness_claimed=False, raw_rom_included=False,
                native_processes=0, rom_writes=0, save_reads=0, save_writes=0,
                limitations_ja=['型付きasset外の命令、数値表、text、未到達voicegroupは推測で除外しない。',
                                '未知0件でも間接参照・owner退役全consumerの完全性を証明する別ゲートが必要。',
                                '音声末尾padding、LZ終端以降、table外、境界を跨ぐ4byteは余剰容量と扱わない。'])


if __name__ == '__main__':
    need(len(sys.argv) == 3, 'usage: pr16_dex_hof_donor.py ROM CHECKPOINT_JSON')
    print(json.dumps(audit(Path(sys.argv[1]).read_bytes(), json.loads(Path(sys.argv[2]).read_bytes())),
                     ensure_ascii=False, indent=2))
