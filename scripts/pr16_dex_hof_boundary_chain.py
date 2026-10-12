#!/usr/bin/env python3
"""619原本と全九段親deltaを固定する異種consumer境界参照chain。"""
from __future__ import annotations

import collections
import copy
import json

import pr16_dex_hof_donor as d
import pr16_dex_hof_runtime_chain as previous
import pr16_dex_hof_lifetime_chain as lifetime_chain
import pr16_dex_hof_callback_chain as callback_chain
import pr16_dex_hof_space_chain as space_chain

BASELINE = previous.BASELINE
BASELINE_ID = previous.BASELINE_ID
EARLIER = previous.EARLIER
EARLIER_ID = previous.EARLIER_ID
PARENT = 'content/modernization/pr16_dex_hof_runtime_closure_evidence/reference-chain.json'
PARENT_ID = {'size': 68925, 'sha256': '7fdc8ed846f529fd7dfd5b35b322ddf8bd1eb46e18f5fd45239e21e998adae8e'}
PARENT_CHECKPOINT = 'content/modernization/pr16_dex_hof_runtime_closure_checkpoint.json'
PARENT_CHECKPOINT_ID = {'size': 55238, 'sha256': 'b9252156201ab5c7506396270d9757522240767a3a781a7330237b1c9ba50927'}
PARENT_AUDIT_ID = {'size': 2738557, 'sha256': '1d3de6cd2b35a0e3df71d84c0cbee8a2e2dd2baf37f33fa28287cd27c147b309'}
PARENT_INPUTS = (*previous.PARENT_INPUTS, PARENT, PARENT_CHECKPOINT)
INHERITED_NAMES = ('reference_delta', 'reference_chain', 'remaining_reference_chain', 'script_reference_chain', 'consumer_reference_chain', 'space_reference_chain', 'callback_reference_chain', 'lifetime_reference_chain', 'runtime_reference_chain')
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


BOUNDARY_KIND = 'rooted_mask_literal_thumb_boundary'


def witness_geometry(row):
    """異種境界の完整要素だけを新validatorへ渡し、旧kindは一切変更しない。"""
    if row['kind'] == BOUNDARY_KIND:
        import pr16_dex_hof_boundary_mystery as mystery
        return mystery.witness_geometry(row['evidence'])
    return previous.witness_geometry(row)


def read_measured(raw, expected, audit):
    # expectedは独立measurement envelopeの全file size/SHA。自己hashを測定根にしない。
    need(identity(raw) == expected and 0 < len(raw) <= MAX_DELTA_BYTES and raw.endswith(b'\n'),
         'entire independent measured delta bytes')
    delta = json.loads(raw)
    validate(audit, delta)
    return delta


def parent(*args):
    """独立checkpointで732親を検査し、全九段113行103witnessを保存する。"""
    need(len(args) == len(PARENT_INPUTS), 'all seventeen independently identified parent inputs')
    checkpoint_raw = args[-1]
    need(identity(checkpoint_raw) == PARENT_CHECKPOINT_ID and checkpoint_raw.endswith(b'\n'),
         'whole independently recorded732 checkpoint')
    cp = json.loads(checkpoint_raw)
    need(cp['delta_identity'] == PARENT_ID and cp['classified'] == 732 and cp['unclassified'] == 142,
         'latest checkpoint exact732 measured frontier')
    original = previous.parent(*args[:-2])
    inherited_delta = previous.read_measured(args[-2], cp['delta_identity'], original)
    result = previous.materialize(original, inherited_delta)
    need((result['classified'], result['unclassified'], inherited_delta['newly_classified']) == (732,142,3),
         'exact measured732 parent frontier')
    for name, changes, witnesses in (('reference_delta',25,22),('reference_chain',17,16),
            ('remaining_reference_chain',33,33),('script_reference_chain',29,23),('consumer_reference_chain',3,3),('space_reference_chain',2,2),('callback_reference_chain',1,1),('lifetime_reference_chain',0,0),('runtime_reference_chain',3,3)):
        need((len(result[name]['changes']), len(result[name]['witnesses'])) == (changes, witnesses),
             'all nine complete inherited changes and witnesses')
        if name in original:
            need(result[name] == original[name], 'every earlier namespace entirely unchanged')
    need(identity(canonical(result)) == PARENT_AUDIT_ID,
         'entire canonical732 parent with all original fields')
    return result


def parent_audits(*args):
    """容量照合で必要な固定親を名前付きで返す。呼出側の深いprevious参照を避ける。"""
    latest = parent(*args)
    return dict(parent_audit=latest,
                runtime_parent=previous.parent(*args[:len(previous.PARENT_INPUTS)]),
                lifetime_parent=lifetime_chain.parent(*args[:len(lifetime_chain.PARENT_INPUTS)]),
                callback_parent=callback_chain.parent(*args[:len(callback_chain.PARENT_INPUTS)]),
                baseline_audit=space_chain.parent(*args[:len(space_chain.PARENT_INPUTS)]))


def build(audit, regions, proof):
    """一意の型に完全包含される旧unknownだけを変更。分類0の診断も親行を不変で保存。"""
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
    delta = dict(schema_version=1, status='PASS_732_PARENT_BOUND_BOUNDARY_REFERENCE_CHAIN',
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
         delta['status'] == 'PASS_732_PARENT_BOUND_BOUNDARY_REFERENCE_CHAIN', 'closed delta schema and status')
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
    need(len({h['address'] for h in changes}) == len(changes) and
         [h['address'] for h in changes] == [h['address'] for h in audit['hits'] if h['address'] in
            {c['address'] for c in changes}], 'zero-or-more unique changes preserve original ordering')
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
                evidence=[dict(boundary_reference_chain_witness=i) for i in change['witness_ids']])
        else:
            need(result['hits'][index] == old, 'all retained rows exactly immutable')
    result.update(classified=delta['classified'], unclassified=delta['unclassified'],
                  classifications=dict(collections.Counter(h['classification'] for h in result['hits'])),
                  boundary_reference_chain=copy.deepcopy(delta))
    need(d.compare_inventory(result['hits'], audit)['same_inventory'], 'all original hit identities retained')
    return result
