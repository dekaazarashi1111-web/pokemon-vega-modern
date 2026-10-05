#!/usr/bin/env python3
"""根付きpalette structのpointer/tag跨ぎ6窓だけを型分類する。"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import pr16_dex_hof_donor as donor

ROOT = Path(__file__).resolve().parents[1]
REVIEW = 'content/modernization/pr16_dex_hof_typed_palette_review.json'
REVIEW_ID = {'size': 8325, 'sha256': 'da2a4d9acb437e81c2843264840585a1adc49fc7ccc2e4abd42c35131250dbb9'}
CANDIDATE = {'size': 33554432, 'sha256': '0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
P04 = 'content/modernization/p04_species_runtime_contract.json'
STAGE75 = 'content/modernization/rockruff_own_tempo_stage75_contract.json'
LAYOUT = dict(stride=8, data_offset=0, data_bytes=4, tag_offset=4,
              tag_bytes=2, padding_offset=6, padding_bytes=2, tag_base=1621,
              classified_origin_offset=2, classified_origin_size=4)
need, identity, chunk = donor.need, donor.identity, donor.chunk


def _source_identity(raw, expected, label):
    need(identity(raw) == {k: expected[k] for k in ('size', 'sha256')},
         'palette fixed source identity: ' + label)
    if 'git_blob_sha' in expected:
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        need(blob == expected['git_blob_sha'], 'palette fixed Git blob: ' + label)


def source_proof(root=ROOT):
    path = root / REVIEW
    need(path.is_file() and not path.is_symlink(), 'regular palette semantic review')
    raw = path.read_bytes()
    need(identity(raw) == REVIEW_ID, 'immutable palette semantic review')
    review = json.loads(raw)
    bindings = {REVIEW: identity(raw)}
    documents = {}
    for name, expected in review['source_bindings'].items():
        path = root / name
        need(path.is_file() and not path.is_symlink(), 'regular palette fixed source: ' + name)
        data = path.read_bytes()
        _source_identity(data, expected, name)
        bindings[name] = expected
        if name.endswith('.json'):
            documents[name] = json.loads(data)
    p04 = documents[P04]['tables']['species_shiny_palette']
    old, middle, current = review['tables']
    need((p04['old_address'], p04['old_count'], p04['old_size'], p04['old_sha256']) ==
         (old['address'], old['count'], old['size'], old['sha256']), 'fixed original palette table')
    need((p04['new_address'], p04['new_count'], p04['new_size'], p04['new_sha256'], p04['stride']) ==
         (middle['address'], middle['count'], middle['size'], middle['sha256'], 8),
         'fixed Stage70 palette table')
    sites = p04['pointer_consumers']['site_offsets']
    need([donor.BASE + s for s in sites] == [r['address'] for r in review['roots']] and
         p04['pointer_consumers']['count'] == len(sites) == 3,
         'all pinned palette roots')
    contract = documents[STAGE75]['table_contract']
    need((contract['old_species_count'], contract['new_species_count']) ==
         (middle['count'], current['count']) and
         'species_shiny_palette' in contract['relocated_species_tables'],
         'Stage75 palette relocation contract')
    return review, bindings


def _bound_regions(raw, latest, review):
    """固定reviewの型境界を現byteへ束縛。公開APIは全候補identityも要求する。"""
    need(review['layout'] == LAYOUT and review['row_indices'] == [938, 1450],
         'exact cross-field palette schema')
    tables = review['tables']
    need(len(tables) == 3 and [t['count'] for t in tables] == [1621, 1670, 1671],
         'exact three palette generations')
    rows = latest['placement']['owner_byte_audit']
    owners = {o['name']: o for o in rows}
    allocation_rows = latest['placement']['allocation']['allocations']
    allocations = {o['name']: o for o in allocation_rows}
    need(len(owners) == len(rows) and len(allocations) == len(allocation_rows),
         'unique latest palette owner identities')
    need(len(review['owners']) == 3 and {o['name'] for o in review['owners']} ==
         {t['owner'] for t in tables}, 'exact palette owner set')
    for expected in review['owners']:
        name = expected['name']
        need(name in owners and name in allocations, 'palette owner present')
        owner, allocation = owners[name], allocations[name]
        fields = ('name', 'address', 'size', 'after_sha256')
        need(all(owner[k] == expected[k] for k in fields), 'fixed latest palette owner')
        need((donor.BASE + allocation['start'], allocation['size'],
              donor.BASE + allocation['end_exclusive']) ==
             (owner['address'], owner['size'], owner['address'] + owner['size']),
             'palette allocation to actual owner join')
        need(identity(chunk(raw, owner['address'], owner['size'])) ==
             dict(size=owner['size'], sha256=owner['after_sha256']),
             'whole latest palette owner afterSHA')
    need(len(review['consumer_windows']) == 4 and
         {w['name'] for w in review['consumer_windows']} == {
             'GetMonSpritePalFromSpeciesAndPersonality',
             'GetMonSpritePalStructFromOtIdPersonality',
             'LoadCompressedSpritePalette', 'LoadSpritePalette'},
         'complete fixed palette semantic windows')
    donor.signed(raw, review['consumer_windows'])
    need(len(review['roots']) == 3 and len({r['address'] for r in review['roots']}) == 3,
         'three unique palette roots')
    donor.signed(raw, review['roots'])
    need(all(donor.u32(raw, r['address']) == tables[-1]['address'] for r in review['roots']),
         'all live palette roots select current table')
    table_bytes = []
    for table in tables:
        owner = owners[table['owner']]
        need(table['size'] == table['count'] * 8 and
             donor.contains(owner['address'], owner['address'] + owner['size'],
                            table['address'], table['size']), 'whole palette table within owner')
        donor.signed(raw, table)
        data = chunk(raw, table['address'], table['size'])
        table_bytes.append(data)
    need(table_bytes[0] == table_bytes[1][:len(table_bytes[0])] and
         table_bytes[1] == table_bytes[2][:len(table_bytes[1])],
         'all retired palette bytes equal rooted current prefix')
    regions = []
    assets = {}
    for table, data in zip(tables, table_bytes):
        need([r['row_index'] for r in table['rows']] == review['row_indices'],
             'exact selected palette rows')
        for row in table['rows']:
            index = row['row_index']
            address = table['address'] + index * 8
            need(row['address'] == address and row['size'] == 8,
                 'exact palette row boundary')
            row_raw = data[index * 8:(index + 1) * 8]
            pointer, tag, pad = struct.unpack('<IHH', row_raw)
            need(tag == index + 1621 and pad == 0, 'numeric palette tag and padding')
            need(pointer % 4 == 0 and donor.BASE <= pointer < donor.BASE + len(raw),
                 'aligned full palette data pointer')
            need(not donor.DONOR_LO <= donor.canonical(pointer) < donor.DONOR_HI,
                 'real palette data pointer outside donor')
            if pointer not in assets:
                encoded, decoded = donor.decode_lz_at(raw, pointer)
                need(len(decoded) in (32, 64, 128), 'whole rooted palette asset extent')
                need(pointer + len(encoded) <= donor.DONOR_LO or donor.DONOR_HI <= pointer,
                     'whole palette asset outside donor')
                assets[pointer] = dict(address=pointer, **identity(encoded), decoded=identity(decoded))
            origin = address + 2
            target = donor.canonical(struct.unpack_from('<I', row_raw, 2)[0])
            need(donor.DONOR_LO <= target < donor.DONOR_HI,
                 'exact palette cross-field apparent reference')
            evidence = dict(row_index=index, row=row, table=dict(
                address=table['address'], size=table['size'], sha256=table['sha256'],
                count=table['count'], owner=table['owner']),
                origin=dict(address=origin, **identity(row_raw[2:6])),
                layout=LAYOUT, tag=tag, pointer_target=pointer,
                asset=assets[pointer], rooted_current_table=tables[-1]['address'],
                root_sites=review['roots'], consumer_windows=review['consumer_windows'],
                retired_prefix_byte_equivalence=True,
                scope_ja='row+2の4byteはdata pointer上位半分とu16 tagを跨ぐ。実data readはrow+0のu32、tag readはrow+4のu16。')
            regions.append(donor.TypedRegion(origin, origin + 4, 'palette_cross_field', evidence))
    need(len(regions) == 6 and len({r.start for r in regions}) == 6,
         'exact six distinct palette cross-field windows')
    return regions, dict(status='PASS_CURRENT_ROOTED_PALETTE_CROSS_FIELD_WINDOWS',
        windows=6, tables=tables, roots=review['roots'], consumer_windows=review['consumer_windows'],
        public_source_review=review['public_sources'], retired_prefix_byte_equivalence=True,
        complete_table_pointer_fields_not_classified=True, old_full_rom_scan_runs=0,
        native_processes=0, rom_writes=0, donor_eligible=False, donor_leased=False,
        indirect_reference_completeness_claimed=False)


def palette_regions(raw, latest, root=ROOT):
    """現候補全SHA・固定source・最新owner・JP consumer窓が一致した6窓を返す。"""
    need(identity(raw) == CANDIDATE == latest['candidate'], 'exact current palette candidate')
    review, bindings = source_proof(root)
    need(review['required_current_sha256'] == CANDIDATE['sha256'],
         'review targets exact current palette candidate')
    regions, proof = _bound_regions(raw, latest, review)
    proof['source_bindings'] = bindings
    return regions, proof
