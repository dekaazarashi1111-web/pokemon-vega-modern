#!/usr/bin/env python3
"""旧874行を複製せず、不変原本と一意witnessを参照する追記専用分類delta。"""
from __future__ import annotations

import collections
import copy
import json

import pr16_dex_hof_donor as d

BASELINE = 'content/modernization/pr16_dex_hof_typed_recovery_evidence/egg-typed-audit.json'
BASELINE_ID = dict(size=4063919, sha256='814082398937869b6cc17faa09cbf1833f0c7f4aa300ddbd83d0de833d44b74c')
FIELDS = ('address', 'target', 'kind', 'size', 'sha256')
FLAGS = ('donor_leased', 'donor_eligible', 'indirect_reference_completeness_claimed')
need, identity = d.need, d.identity
MAX_DELTA_BYTES = 2000000
TOP_FIELDS = {'schema_version', 'status', 'baseline', 'candidate', 'inherited_candidates',
 'inherited_classified', 'inherited_unclassified', 'changes', 'witnesses', 'classified',
 'unclassified', 'newly_classified', 'proof', 'proof_identity', *FLAGS,
 'old_full_rom_scan_runs', 'native_processes'}


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n').encode()


def witness_geometry(row):
    evidence, kind = row['evidence'], row['kind']
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


def baseline(raw):
    need(identity(raw) == BASELINE_ID, 'entire immutable baseline with final LF')
    audit = json.loads(raw)
    need(audit['candidates'] == len(audit['hits']) == 874 and audit['classified'] == 619 and
         audit['unclassified'] == 255 and sum(h['accepted'] for h in audit['hits']) == 619,
         'exact inherited 874/619/255 frontier')
    need(len({h['address'] for h in audit['hits']}) == 874 and
         not any(audit[k] for k in FLAGS), 'unique baseline inventory without lease')
    return audit


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
    delta = dict(schema_version=1, status='PASS_SHARED_WITNESS_REFERENCE_DELTA',
        baseline=dict(path=BASELINE, **BASELINE_ID), candidate=audit['candidate'],
        inherited_candidates=len(audit['hits']), inherited_classified=audit['classified'],
        inherited_unclassified=audit['unclassified'], changes=hits, witnesses=witness_rows,
        classified=audit['classified'] + len(hits), unclassified=audit['unclassified'] - len(hits),
        newly_classified=len(hits), proof=proof, proof_identity=identity(canonical(proof)), donor_leased=False, donor_eligible=False,
        indirect_reference_completeness_claimed=False, old_full_rom_scan_runs=0, native_processes=0)
    validate(audit, delta)
    return delta


def validate(audit, delta):
    need(set(delta) == TOP_FIELDS and type(delta['schema_version']) is int and delta['schema_version'] == 1 and
         delta['status'] == 'PASS_SHARED_WITNESS_REFERENCE_DELTA', 'closed delta schema and status')
    need(len(canonical(delta)) <= MAX_DELTA_BYTES, 'bounded delta without inherited evidence duplication')
    need(identity(canonical(delta['proof'])) == delta['proof_identity'], 'canonical proof identity')
    need(delta['baseline'] == dict(path=BASELINE, **BASELINE_ID), 'immutable explicit baseline identity')
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
                evidence=[dict(reference_delta_witness=i) for i in change['witness_ids']])
        else:
            need(result['hits'][index] == old, 'all retained rows exactly immutable')
    result.update(classified=delta['classified'], unclassified=delta['unclassified'],
                  classifications=dict(collections.Counter(h['classification'] for h in result['hits'])),
                  reference_delta=copy.deepcopy(delta))
    need(d.compare_inventory(result['hits'], audit)['same_inventory'], 'all original hit identities retained')
    return result
