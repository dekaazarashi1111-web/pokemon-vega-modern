#!/usr/bin/env python3
"""歴史的serializer境界を現候補へ束縛。data名や命令形だけでは採用しない。"""
from __future__ import annotations

import collections
import hashlib
import json
import struct
import zlib
from pathlib import Path

import pr16_dex_hof_donor as d

ROOT = Path(__file__).resolve().parents[1]
REVIEW = 'content/modernization/pr16_dex_hof_reference_data_review.json'
REVIEW_ID = dict(size=9630, sha256='d84045c48abe5110d473befa1c9441b5d062f1712f0116cdaa503d369a0f523f')
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
LAYOUT = dict(stride=32, name_offset=4, name_size=6, item_offset=10, item_size=2,
              origin_offset=7, origin_size=4, party_pointer_offset=28)
need, identity, chunk = d.need, d.identity, d.chunk


def source_proof(root=ROOT):
    path = root / REVIEW
    need(path.is_file() and not path.is_symlink(), 'regular data semantic review')
    need(identity(path.read_bytes()) == REVIEW_ID, 'immutable data review identity')
    review = json.loads(path.read_bytes())
    need(review['required_candidate'] == CANDIDATE and review['trainer_layout'] == LAYOUT,
         'review current candidate and independently derived JP C ABI')
    bindings = {REVIEW: identity(path.read_bytes())}
    for name, expected in review['source_bindings'].items():
        file = root / name
        need(file.is_file() and not file.is_symlink(), 'regular fixed data source')
        raw = file.read_bytes()
        need(identity(raw) == {k: expected[k] for k in ('size', 'sha256')} and
             hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() ==
             expected['git_blob_sha'], 'entire fixed source and Git blob')
        bindings[name] = expected
    return review, bindings


def archive_streams(payload, address, expected):
    """TOC全体hash・連続被覆・全streamの圧縮終端/展開hashを検査。byteを公開しない。"""
    need(len(payload) >= 56, 'complete archive header')
    magic, version, count, toc_size, body_size, digest = struct.unpack_from('<8sIIII32s', payload)
    need((magic, version, count, toc_size, body_size) ==
         (b'VEGA16\0\0', 1, expected['file_count'], expected['table_size'], expected['body_size']),
         'fixed source archive header')
    need(0 < count <= 100 and 0 < toc_size <= 100000 and 0 < body_size <= 1000000 and
         56 + toc_size + body_size == len(payload), 'bounded whole archive partition')
    need(hashlib.sha256(payload[56:]).digest() == digest, 'whole TOC and body digest')
    toc = json.loads(payload[56:56 + toc_size])
    need(toc['schema_version'] == 1 and toc['task'] == 'T16', 'fixed archive TOC schema')
    rows = toc['files']
    need(len(rows) == count and [r['name'] for r in rows] == sorted({r['name'] for r in rows}),
         'unique sorted serializer file order')
    cursor, result = 0, []
    for row in rows:
        need(set(row) == {'name', 'offset', 'compressed_size', 'raw_size', 'sha256'} and
             row['name'].startswith(('content/', 'manifests/')) and '..' not in Path(row['name']).parts,
             'closed archive source row')
        size, decoded_size = row['compressed_size'], row['raw_size']
        need(type(row['offset']) is int and row['offset'] == cursor and type(size) is int and
             0 < size <= body_size - cursor and type(decoded_size) is int and
             0 < decoded_size <= 2000000, 'exact contiguous compressed stream bounds')
        start = 56 + toc_size + cursor
        encoded = payload[start:start + size]
        decoder = zlib.decompressobj()
        decoded = decoder.decompress(encoded, decoded_size + 1)
        need(decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data and
             identity(decoded) == dict(size=decoded_size, sha256=row['sha256']),
             'entire independent zlib stream terminator and expanded SHA')
        result.append(dict(source=row['name'], address=address + start, **identity(encoded),
                           decoded=identity(decoded)))
        cursor += size
    need(cursor == body_size, 'complete archive body with no untyped gaps')
    return result


def _data_regions(raw, latest, review, hits):
    owners = {o['name']: o for o in latest['placement']['owner_byte_audit']}
    for expected in review['owners']:
        owner = owners.get(expected['name'])
        need(owner is not None and all(owner[k] == expected[k] for k in expected),
             'latest actual data owner, not nominal allocation hash')
        need(identity(chunk(raw, owner['address'], owner['size'])) ==
             dict(size=owner['size'], sha256=owner['after_sha256']), 'whole actual data owner')
    roots = review['trainer_roots']
    need(collections.Counter(r['field_offset'] for r in roots) == {4: 3, 10: 1} and
         len({r['address'] for r in roots}) == 4, 'four pinned scalar field consumers')
    d.signed(raw, roots)
    tables = review['trainer_tables']
    need(len(tables) == 5 and [t['count'] for t in tables] == [743, 1367, 1367, 1367, 4284],
         'fixed original and relocated trainer table extents')
    need(all(d.u32(raw, r['address']) == r['value'] == tables[-1]['address'] + r['field_offset']
             for r in roots), 'current trainer field roots select last table')
    regions, summaries = [], []
    magics = (b'VEGATV32', b'VEGATV33', b'VEGATV34', b'VEGATC35')
    for ordinal, table in enumerate(tables):
        need(table['size'] == table['count'] * 32, 'whole JP trainer struct extent')
        d.signed(raw, table)
        if ordinal:
            owner = owners[table['owner']]
            need(d.contains(owner['address'], owner['address'] + owner['size'],
                            table['address'], table['size']), 'trainer table inside actual owner')
            header = chunk(raw, owner['address'], 72)
            fields = struct.unpack_from('<16I', header, 8)
            need(header[:8] == magics[ordinal - 1] and fields[1] == owner['size'] and
                 fields[3] == table['count'] and
                 fields[9 if ordinal == 4 else 8] == table['address'],
                 'serializer magic/count/current table field')
        else:
            need(table['address'] == 0x081FDFD8 and table['owner'] is None,
                 'explicit fixed JP original table constant')
        for row in table['rows']:
            index = row['index']
            need(type(index) is int and 0 <= index < table['count'] and row['size'] == 32 and
                 row['address'] == table['address'] + index * 32, 'exact scalar row boundary')
            address = row['address'] + 7
            matching = [h for h in hits if h['address'] == address]
            need(len(matching) == 1 and not matching[0]['accepted'] and matching[0]['size'] == 4 and
                 matching[0]['kind'] == 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
                 'only original unknown name/item cross-field window')
            data = chunk(raw, address, 4)
            need(identity(data) == {k: matching[0][k] for k in ('size', 'sha256')},
                 'exact original cross-field hit bytes')
            need(d.DONOR_LO <= d.canonical(int.from_bytes(data, 'little')) < d.DONOR_HI,
                 'retained apparent pointer target')
            evidence = dict(row=row, table={k: table[k] for k in ('name', 'address', 'count', 'size', 'sha256')},
                layout=LAYOUT, fixed_review=REVIEW, historical_typing_only=True,
                current_consumer_reachability_claimed=False,
                scope_ja='name[3..5]のu8三つとitems[0]の下位byteを跨ぐ。party pointerはrow+28で別。')
            regions.append(d.TypedRegion(address, address + 4, 'trainer_name_item_cross_field', evidence))
        summaries.append({k: table[k] for k in ('name', 'address', 'count', 'size', 'sha256')})
    owner = owners[review['archive']['owner']]
    streams = archive_streams(chunk(raw, owner['address'], owner['size']), owner['address'], review['archive'])
    selected = []
    for stream in streams:
        if not any(not h['accepted'] and d.contains(stream['address'], stream['address'] + stream['size'],
                    h['address'], h['size']) for h in hits):
            continue
        evidence = dict(stream=stream, fixed_review=REVIEW, archive_owner=owner['name'],
                        historical_typing_only=True, runtime_consumer_reachability_claimed=False)
        regions.append(d.TypedRegion(stream['address'], stream['address'] + stream['size'],
                                     'zlib_serialized_archive', evidence))
        selected.append(stream)
    need(len(regions) == 17 and len(selected) == 2, 'exact fifteen cross-field and two archive witnesses')
    return regions, dict(status='PASS_BOUND_HISTORICAL_SERIALIZER_TYPES', tables=summaries,
                         roots=roots, complete_archive_streams=len(streams), selected_streams=selected,
                         indirect_reference_completeness_claimed=False, donor_leased=False)


def data_regions(raw, latest, inherited, root=ROOT):
    need(identity(raw) == latest['candidate'] == inherited['candidate'] == CANDIDATE,
         'exact whole current candidate')
    review, bindings = source_proof(root)
    regions, proof = _data_regions(raw, latest, review, inherited['hits'])
    proof['source_bindings'] = bindings
    return regions, proof
