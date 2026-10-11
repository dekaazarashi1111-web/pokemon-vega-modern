#!/usr/bin/env python3
"""619原本と全十二段親deltaを固定する残consumer参照chain。"""
from __future__ import annotations

import collections
import copy
import importlib
import json

import pr16_dex_hof_donor as d
import pr16_dex_hof_summary_chain as previous

BASELINE = previous.BASELINE
BASELINE_ID = previous.BASELINE_ID
EARLIER = previous.EARLIER
EARLIER_ID = previous.EARLIER_ID
PARENT = 'content/modernization/pr16_dex_hof_summary_references_evidence/reference-chain.json'
PARENT_ID = {'size': 681669, 'sha256': 'c11d71495d60fda8fed98464eb6962f7b57be75dc39e8b479be3d57903d68586'}
PARENT_CHECKPOINT = 'content/modernization/pr16_dex_hof_summary_references_checkpoint.json'
PARENT_CHECKPOINT_ID = {'size': 627652, 'sha256': 'e63d3dfda20758d9a2f120a06bfc870183adf1cd997d887462babdae9af6529a'}
PARENT_AUDIT_ID = {'size': 3132197, 'sha256': '072e3ff7d1094f9f7ffb47fe55c8a3da9c1a5a4546eac728b9852af746f5d2e2'}
PARENT_INPUTS = (*previous.PARENT_INPUTS, PARENT, PARENT_CHECKPOINT)
INHERITED_NAMES = (*previous.INHERITED_NAMES, 'summary_reference_chain')
FIELDS = ('address', 'target', 'kind', 'size', 'sha256')
FLAGS = ('donor_leased', 'donor_eligible', 'indirect_reference_completeness_claimed')
need, identity = d.need, d.identity
MAX_DELTA_BYTES = 2000000
# 新consumer検証器への接続表。登録は採用・分類ではなく、旧親復元ではimportしない。
NEW_KIND_MODULES = {
    'rooted_rfu_parent_disconnect_minimum_thumb': 'pr16_dex_hof_new_code',
    'rooted_fame_checker_minimum_thumb': 'pr16_dex_hof_ui_data',
    'rooted_credits_minimum_text_consumption': 'pr16_dex_hof_menu_text',
}
TOP_FIELDS = {'schema_version', 'status', 'baseline', 'parent', 'candidate', 'inherited_candidates',
 'inherited_classified', 'inherited_unclassified', 'changes', 'witnesses', 'classified',
 'unclassified', 'newly_classified', 'proof', 'proof_identity', *FLAGS,
 'old_full_rom_scan_runs', 'native_processes'}


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()


def witness_geometry(row):
    """旧型の意味を変更しない。新consumer型の接続は専用moduleへ限定する。"""
    module_name = NEW_KIND_MODULES.get(row['kind'])
    if module_name is not None:
        module = importlib.import_module(module_name)
        kinds = getattr(module, 'KINDS', (getattr(module, 'KIND', None),))
        need(type(kinds) in (tuple, list, set, frozenset) and
             all(type(kind) is str for kind in kinds) and row['kind'] in kinds,
             'registered consumer kind agrees with dedicated validator')
        return module.witness_geometry(row['evidence'])
    return previous.witness_geometry(row)


def read_measured(raw, expected, audit):
    # expectedは独立measurement envelopeの全file size/SHA。自己hashを測定根にしない。
    need(identity(raw) == expected and 0 < len(raw) <= MAX_DELTA_BYTES and raw.endswith(b'\n') and b'\r' not in raw,
         'entire independent measured delta bytes')
    delta = json.loads(raw)
    validate(audit, delta)
    return delta


def parent(*args):
    """独立checkpointで737親を検査し、全十二段118行108witnessを保存する。"""
    need(len(args) == len(PARENT_INPUTS), 'all twenty-three independently identified parent inputs')
    need(all(type(raw) is bytes and raw.endswith(b'\n') and b'\r' not in raw for raw in args),
         'all parent inputs are complete LF bytes')
    checkpoint_raw = args[-1]
    need(identity(checkpoint_raw) == PARENT_CHECKPOINT_ID,
         'whole independently recorded737 checkpoint')
    cp = json.loads(checkpoint_raw)
    need(cp['delta_identity'] == PARENT_ID and cp['classified'] == 737 and cp['unclassified'] == 137,
         'latest checkpoint exact737 measured frontier')
    original = previous.parent(*args[:-2])
    inherited_delta = previous.read_measured(args[-2], cp['delta_identity'], original)
    result = previous.materialize(original, inherited_delta)
    need((result['classified'], result['unclassified'], inherited_delta['newly_classified']) == (737,137,2),
         'exact measured737 parent frontier')
    need(len(result['hits']) == 874 and
         sum(len(result[name]['changes']) for name in INHERITED_NAMES) == 118 and
         sum(len(result[name]['witnesses']) for name in INHERITED_NAMES) == 108,
         'entire874 inventory and all118 changes108 witnesses retained')
    for name, changes, witnesses in (('reference_delta',25,22),('reference_chain',17,16),
            ('remaining_reference_chain',33,33),('script_reference_chain',29,23),('consumer_reference_chain',3,3),('space_reference_chain',2,2),('callback_reference_chain',1,1),('lifetime_reference_chain',0,0),('runtime_reference_chain',3,3),('boundary_reference_chain',1,1),('party_reference_chain',2,2),('summary_reference_chain',2,2)):
        need((len(result[name]['changes']), len(result[name]['witnesses'])) == (changes, witnesses),
             'all twelve complete inherited changes and witnesses')
        if name in original:
            need(result[name] == original[name], 'every earlier namespace entirely unchanged')
    need(identity(canonical(result)) == PARENT_AUDIT_ID,
         'entire canonical737 parent with all original fields')
    return result


def parent_audits(*args):
    """737と735以下の各独立親を明示名で保持する。"""
    latest=parent(*args)
    inherited=previous.parent_audits(*args[:-2])
    inherited['summary_parent']=inherited.pop('parent_audit')
    return dict(parent_audit=latest,**inherited)


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
    delta = dict(schema_version=1, status='PASS_737_PARENT_BOUND_REMAINING_CONSUMERS_REFERENCE_CHAIN',
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
         delta['status'] == 'PASS_737_PARENT_BOUND_REMAINING_CONSUMERS_REFERENCE_CHAIN', 'closed delta schema and status')
    counter_fields = ('inherited_candidates', 'inherited_classified', 'inherited_unclassified',
                      'classified', 'unclassified', 'newly_classified', 'old_full_rom_scan_runs', 'native_processes')
    need(all(type(delta[k]) is int and delta[k] >= 0 for k in counter_fields),
         'all counters are nonnegative integers, never booleans')
    need(type(delta['changes']) is list and type(delta['witnesses']) is list,
         'canonical change and witness lists')
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
             type(r['id']) is int and type(r['address']) is int and r['address'] >= 0 and
             type(r['size']) is int and r['size'] > 0 and type(r['kind']) is str for r in witnesses) and
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
                evidence=[dict(remaining_consumers_reference_chain_witness=i) for i in change['witness_ids']])
        else:
            need(result['hits'][index] == old, 'all retained rows exactly immutable')
    result.update(classified=delta['classified'], unclassified=delta['unclassified'],
                  classifications=dict(collections.Counter(h['classification'] for h in result['hits'])),
                  remaining_consumers_reference_chain=copy.deepcopy(delta))
    need(d.compare_inventory(result['hits'], audit)['same_inventory'], 'all original hit identities retained')
    return result
