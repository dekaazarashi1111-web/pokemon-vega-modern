#!/usr/bin/env python3
"""不変619原本・644親deltaを固定し、新証拠だけ追記する参照chain。"""
from __future__ import annotations

import collections
import copy
import json

import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_delta as previous

BASELINE = previous.BASELINE
BASELINE_ID = previous.BASELINE_ID
PARENT = 'content/modernization/pr16_dex_hof_reference_evidence/reference-delta.json'
PARENT_ID = dict(size=149772, sha256='762320ba350f528777b90be404b5fec1d88caeb6dbf6594590d4f45b852c1c87')
FIELDS = ('address', 'target', 'kind', 'size', 'sha256')
FLAGS = ('donor_leased', 'donor_eligible', 'indirect_reference_completeness_claimed')
need, identity = d.need, d.identity
MAX_DELTA_BYTES = 2000000
TOP_FIELDS = {'schema_version', 'status', 'baseline', 'parent', 'candidate', 'inherited_candidates',
 'inherited_classified', 'inherited_unclassified', 'changes', 'witnesses', 'classified',
 'unclassified', 'newly_classified', 'proof', 'proof_identity', *FLAGS,
 'old_full_rom_scan_runs', 'native_processes'}


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n').encode()


def witness_geometry(row):
    evidence, kind = row['evidence'], row['kind']
    if kind == 'indexed_u16_pair':
        pair=evidence['selected_elements'];need(pair['size']==4 and pair['address']%2==0 and evidence['element_size']==2,'two exact adjacent u16 elements')
        return pair['address'],4
    if kind == 'rooted_tileset_lz77':
        asset=evidence['asset'];need(4<asset['size']<=100000 and evidence['decoded']['size']>0,'complete finite rooted LZ stream')
        return asset['address']+4,asset['size']-4
    if kind == 'rooted_sprite_4bpp_frame':
        asset=evidence['asset'];need(asset['size']==evidence['width']*evidence['height']//2==256 and evidence['frame_index']==8,'source-sized raw sprite frame')
        return asset['address'],asset['size']
    if kind == 'packed_u16_cross_row':
        rows=evidence['selected_rows'];need(rows['size']==8 and rows['address']%2==0,
             'two complete packed two-u16 records')
        need(evidence['record_size']==4 and evidence['field_offsets']==[0,2],
             'exact u16 scalar fields without pointer slot')
        return rows['address']+2,4
    if kind == 'adjacent_jp_text_crossing':
        left, right = evidence['left'], evidence['right']
        need(type(left['size']) is int and left['size'] >= 3 and
             type(right['size']) is int and right['size'] > 0 and
             left['address'] + left['size'] == right['address'],
             'two independently rooted adjacent complete text records')
        need(evidence['both_text_consumers_verified'] is True and
             evidence['source_pointer_interpretation'] is False,
             'two byte-text consumers, never pointer reinterpretation')
        return right['address'] - 3, 4
    if kind == 'rooted_thumb_instruction_stream':
        source = evidence['instruction_window']
        instructions = evidence['instructions']
        need(type(source['address']) is int and source['address'] % 2 == 0 and
             type(source['size']) is int and 0 < source['size'] <= 4096,
             'bounded aligned rooted instruction stream')
        cursor = source['address']
        for instruction in instructions:
            need(instruction['address'] == cursor and instruction['size'] in (2, 4),
                 'complete consecutive instruction boundaries')
            cursor += instruction['size']
        need(instructions and cursor == source['address'] + source['size'],
             'all typed instruction bytes have exact instruction roles')
        need(evidence['root_verified'] is True and evidence['literal_pool_included'] is False,
             'source root required and literal pools forbidden')
        return source['address'], source['size']
    if kind == 'trainer_name_item_cross_field':
        source = evidence['row']
        need(source['size'] == 32, 'whole trainer source row')
        return source['address'] + 7, 4
    if kind == 'zlib_serialized_archive':
        source = evidence['stream']
        need(0 < source['size'] <= 1000000, 'bounded compressed stream geometry')
        return source['address'], source['size']
    if kind == 'rooted_thumb_instruction_crossing':
        source = evidence['rooted_entry']
        need(source['size'] == 12, 'whole rooted instruction prefix')
        return source['address'] + 6, 6
    if kind in ('pcm8', 'dpcm4'):
        source = evidence['asset']
        need(16 < source['size'] <= 1000016, 'bounded typed sound payload geometry')
        return source['address'] + 16, source['size'] - 16
    raise ValueError('closed supported reference witness kind')


def read_measured(raw, expected, audit):
    # expectedは独立measurement envelopeの全file size/SHA。自己hashを測定根にしない。
    need(identity(raw) == expected and 0 < len(raw) <= MAX_DELTA_BYTES and raw.endswith(b'\n'),
         'entire independent measured delta bytes')
    delta = json.loads(raw)
    validate(audit, delta)
    return delta


def parent(baseline_raw, parent_raw):
    """親の全25行・22witnessをhash固定で継承。型分類の再測定はしない。"""
    original = previous.baseline(baseline_raw)
    inherited_delta = previous.read_measured(parent_raw, PARENT_ID, original)
    result = previous.materialize(original, inherited_delta)
    need(result['classified'] == 644 and result['unclassified'] == 230 and
         inherited_delta['newly_classified'] == 25, 'exact measured parent frontier')
    return result


def build(audit, regions, proof):
    """一意の型に完全包含される旧unknownだけを変更。未参照witnessは出力しない。"""
    hits = []
    witness_rows, witness_ids = [], {}
    for old in audit['hits']:
        if old['accepted']:
            continue
        matches = [r for r in regions if d.contains(r.start, r.end, old['address'], old['size'])]
        if len({r.kind for r in matches}) != 1:
            continue
        selected = []
        for region in matches:
            row = dict(address=region.start, size=region.end - region.start,
                       kind=region.kind, evidence=region.evidence, evidence_identity=identity(canonical(region.evidence)))
            key = json.dumps(row, sort_keys=True, separators=(',', ':'))
            if key not in witness_ids:
                witness_ids[key] = len(witness_rows)
                witness_rows.append(dict(id=len(witness_rows), **row))
            selected.append(witness_ids[key])
        hits.append(dict(**{k: old[k] for k in FIELDS},
                         classification='FALSE_POSITIVE_TYPED_REFERENCE_' + matches[0].kind.upper(),
                         accepted=True, witness_ids=sorted(set(selected))))
    delta = dict(schema_version=1, status='PASS_PARENT_BOUND_REFERENCE_CHAIN',
        baseline=dict(path=BASELINE, **BASELINE_ID), parent=dict(path=PARENT, **PARENT_ID), candidate=audit['candidate'],
        inherited_candidates=len(audit['hits']), inherited_classified=audit['classified'],
        inherited_unclassified=audit['unclassified'], changes=hits, witnesses=witness_rows,
        classified=audit['classified'] + len(hits), unclassified=audit['unclassified'] - len(hits),
        newly_classified=len(hits), proof=proof, proof_identity=identity(canonical(proof)), donor_leased=False, donor_eligible=False,
        indirect_reference_completeness_claimed=False, old_full_rom_scan_runs=0, native_processes=0)
    validate(audit, delta)
    return delta


def validate(audit, delta):
    need(set(delta) == TOP_FIELDS and type(delta['schema_version']) is int and delta['schema_version'] == 1 and
         delta['status'] == 'PASS_PARENT_BOUND_REFERENCE_CHAIN', 'closed delta schema and status')
    need(len(canonical(delta)) <= MAX_DELTA_BYTES, 'bounded delta without inherited evidence duplication')
    need(identity(canonical(delta['proof'])) == delta['proof_identity'], 'canonical proof identity')
    need(delta['baseline'] == dict(path=BASELINE, **BASELINE_ID), 'immutable explicit baseline identity')
    need(delta['parent'] == dict(path=PARENT, **PARENT_ID), 'entire immutable parent delta identity')
    need(delta['candidate'] == audit['candidate'] and
         delta['inherited_candidates'] == len(audit['hits']) and
         delta['inherited_classified'] == audit['classified'] and
         delta['inherited_unclassified'] == audit['unclassified'], 'same inherited frontier')
    need(all(delta[k] is False for k in FLAGS) and delta['old_full_rom_scan_runs'] == delta['native_processes'] == 0,
         'delta cannot grant lease or fabricated execution')
    originals = {h['address']: h for h in audit['hits']}
    need(len(originals) == len(audit['hits']), 'unique original hit identity')
    changes, witnesses = delta['changes'], delta['witnesses']
    need(changes and len({h['address'] for h in changes}) == len(changes) and
         [h['address'] for h in changes] == [h['address'] for h in audit['hits'] if h['address'] in
            {c['address'] for c in changes}], 'nonempty unique changes preserve original ordering')
    need(all(set(r) == {'id', 'address', 'size', 'kind', 'evidence', 'evidence_identity'} and
             type(r['id']) is int for r in witnesses) and
         [r['id'] for r in witnesses] == list(range(len(witnesses))), 'closed canonical witness rows')
    for row in witnesses:
        need(identity(canonical(row['evidence'])) == row['evidence_identity'], 'canonical witness evidence identity')
        need((row['address'], row['size']) == witness_geometry(row), 'exact source-derived witness geometry')
    keys = [json.dumps({k: v for k, v in r.items() if k != 'id'}, sort_keys=True) for r in witnesses]
    need(len(set(keys)) == len(keys), 'no duplicate shared witness')
    used = set()
    for row in changes:
        need(set(row) == {*FIELDS, 'classification', 'accepted', 'witness_ids'}, 'closed change schema')
        old = originals.get(row['address'])
        need(old is not None and old['accepted'] is False and
             all(row[k] == old[k] for k in FIELDS), 'only exact original unknowns may change')
        ids = row['witness_ids']
        need(row['accepted'] is True and ids and ids == sorted(set(ids)) and
             all(type(i) is int and 0 <= i < len(witnesses) for i in ids), 'valid positive witness references')
        selected = [witnesses[i] for i in ids]
        need(len({r['kind'] for r in selected}) == 1 and
             all(type(r['size']) is int and r['size'] > 0 and
                 d.contains(r['address'], r['address'] + r['size'], row['address'], row['size']) for r in selected),
             'same-type witnesses completely contain hit')
        need(row['classification'] == 'FALSE_POSITIVE_TYPED_REFERENCE_' + selected[0]['kind'].upper(),
             'classification derives from shared witness kind')
        used.update(ids)
    need(used == set(range(len(witnesses))), 'no unreferenced witness expansion')
    need(delta['newly_classified'] == len(changes) and
         delta['classified'] == audit['classified'] + len(changes) and
         delta['unclassified'] == audit['unclassified'] - len(changes) and
         delta['classified'] + delta['unclassified'] == len(audit['hits']), 'exact additive counters')
    return len(changes)


def materialize(audit, delta):
    """計算時だけ874行を再構成。履歴のevidenceやunknownを上書きしない。"""
    validate(audit, delta)
    result = copy.deepcopy(audit)
    changes = {h['address']: h for h in delta['changes']}
    for index, old in enumerate(audit['hits']):
        if old['address'] in changes:
            change = changes[old['address']]
            result['hits'][index] = dict(**{k: change[k] for k in FIELDS},
                classification=change['classification'], accepted=True,
                evidence=[dict(reference_chain_witness=i) for i in change['witness_ids']])
        else:
            need(result['hits'][index] == old, 'all retained rows exactly immutable')
    result.update(classified=delta['classified'], unclassified=delta['unclassified'],
                  classifications=dict(collections.Counter(h['classification'] for h in result['hits'])),
                  reference_chain=copy.deepcopy(delta))
    need(d.compare_inventory(result['hits'], audit)['same_inventory'], 'all original hit identities retained')
    return result
