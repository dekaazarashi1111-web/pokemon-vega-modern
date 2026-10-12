#!/usr/bin/env python3
"""619原本と全十三段741親deltaを固定するHelp batch参照chain。"""
from __future__ import annotations

import collections
import copy
import importlib
import json

import pr16_dex_hof_donor as d
import pr16_dex_hof_remaining_consumers_chain as previous

BASELINE = previous.BASELINE
BASELINE_ID = previous.BASELINE_ID
EARLIER = previous.EARLIER
EARLIER_ID = previous.EARLIER_ID
PARENT = 'content/modernization/pr16_dex_hof_remaining_consumers_evidence/reference-chain.json'
PARENT_ID = {'size': 875373, 'sha256': '1fb58b88ac19198de7ef29fc0728908c1fb720915bfa53d265b78994252a6917'}
PARENT_CHECKPOINT = 'content/modernization/pr16_dex_hof_remaining_consumers_checkpoint.json'
PARENT_CHECKPOINT_ID = {'size': 809502, 'sha256': '55cfbf03e124c26f78ed00b52b9d2da7604642c892dc8c85f0754b3e1a82aca3'}
PARENT_AUDIT_ID = {'size': 3407435, 'sha256': 'cdf348c0be4aee9c2135d9adab214ad9ab23b460ed1bb405779c625fb94a3e95'}
PARENT_INPUTS = (*previous.PARENT_INPUTS, PARENT, PARENT_CHECKPOINT)
INHERITED_NAMES = (*previous.INHERITED_NAMES, 'remaining_consumers_reference_chain')
FIELDS = ('address', 'target', 'kind', 'size', 'sha256')
FLAGS = ('donor_leased', 'donor_eligible', 'indirect_reference_completeness_claimed')
need, identity = d.need, d.identity
MAX_DELTA_BYTES = 2000000
# 新consumer検証器への接続表。登録は採用・分類ではなく、741親の旧証拠には旧validatorだけを適用する。
NEW_KIND_MODULES = {
    'rooted_help_context_topic_minimum_ids': 'pr16_dex_hof_help_roots',
}
NAMESPACE = 'help_batch_reference_chain'
BATCH_FLAGS = ('controller_runtime_wired', 'universal_irq_or_heap_lifetime_claimed',
               'natural_play_universal_reachability_claimed', 'formal_rom_changed', 'formal_save_changed')
TOP_FIELDS = {'schema_version', 'status', 'baseline', 'parent', 'candidate', 'inherited_candidates',
 'inherited_classified', 'inherited_unclassified', 'changes', 'witnesses', 'classified',
 'unclassified', 'newly_classified', 'proof', 'proof_identity', *FLAGS,
 'old_full_rom_scan_runs', 'native_processes', 'donor_safe_bytes', *BATCH_FLAGS}


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()



def valid_identity(value):
    """sizeのfloat/bool別名や自己申告の余剰fieldを受け付けない。"""
    return (type(value) is dict and set(value) == {'size', 'sha256'} and
            type(value['size']) is int and value['size'] >= 0 and
            type(value['sha256']) is str and len(value['sha256']) == 64 and
            all(ch in '0123456789abcdef' for ch in value['sha256']))


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
    need(False, 'new help batch requires its dedicated registered consumer kind')


def read_measured(raw, expected, audit):
    # expectedは独立measurement envelopeの全file size/SHA。自己hashを測定根にしない。
    need(valid_identity(expected) and type(raw) is bytes and identity(raw) == expected and 0 < len(raw) <= MAX_DELTA_BYTES and raw.endswith(b'\n') and b'\r' not in raw,
         'entire independent measured delta bytes')
    delta = json.loads(raw)
    validate(audit, delta)
    return delta


def parent(*args):
    """独立checkpointで741親を検査し、全十三段122行112witnessを保存する。"""
    need(len(args) == len(PARENT_INPUTS), 'all twenty-five independently identified parent inputs')
    need(all(type(raw) is bytes and raw.endswith(b'\n') and b'\r' not in raw for raw in args),
         'all parent inputs are complete LF bytes')
    checkpoint_raw = args[-1]
    need(identity(checkpoint_raw) == PARENT_CHECKPOINT_ID,
         'whole independently recorded741 checkpoint')
    cp = json.loads(checkpoint_raw)
    need(cp['delta_identity'] == PARENT_ID and cp['classified'] == 741 and cp['unclassified'] == 133,
         'latest checkpoint exact741 measured frontier')
    original = previous.parent(*args[:-2])
    inherited_delta = previous.read_measured(args[-2], cp['delta_identity'], original)
    result = previous.materialize(original, inherited_delta)
    need((result['classified'], result['unclassified'], inherited_delta['newly_classified']) == (741,133,4),
         'exact measured741 parent frontier')
    need(len(result['hits']) == 874 and
         sum(len(result[name]['changes']) for name in INHERITED_NAMES) == 122 and
         sum(len(result[name]['witnesses']) for name in INHERITED_NAMES) == 112,
         'entire874 inventory and all122 changes112 witnesses retained')
    for name, changes, witnesses in (('reference_delta',25,22),('reference_chain',17,16),
            ('remaining_reference_chain',33,33),('script_reference_chain',29,23),('consumer_reference_chain',3,3),('space_reference_chain',2,2),('callback_reference_chain',1,1),('lifetime_reference_chain',0,0),('runtime_reference_chain',3,3),('boundary_reference_chain',1,1),('party_reference_chain',2,2),('summary_reference_chain',2,2),('remaining_consumers_reference_chain',4,4)):
        need((len(result[name]['changes']), len(result[name]['witnesses'])) == (changes, witnesses),
             'all thirteen complete inherited changes and witnesses')
        if name in original:
            need(result[name] == original[name], 'every earlier namespace entirely unchanged')
    need(identity(canonical(result)) == PARENT_AUDIT_ID,
         'entire canonical741 parent with all original fields')
    song = inherited_delta['proof']['song']
    need(cp['combined_song_models'] == song['combined_song_models'] == 133 and
         cp['retained_sample_witnesses'] == song['retained_sample_witnesses'] == 50 and
         song['all133_models_exact'] is True and song['all50_sample_identities_exact'] is True,
         'all133 song models and50 sample identities retained')
    validate_parent_state(result)
    return result



def validate_parent_state(audit):
    """741親の全fieldを認証し、旧accepted改変や暗黙の安全昇格を拒否する。"""
    need(type(audit) is dict and identity(canonical(audit)) == PARENT_AUDIT_ID,
         'entire exact741 parent state with all original fields')
    need(all(audit.get(flag) is False for flag in FLAGS), 'parent cannot grant lease or completeness')
    need(NAMESPACE not in audit, 'new batch cannot substitute for its immediate parent')


def validate_restricted_proof(proof):
    """新診断の容器も、旧原本複製と未証明な権限・全寿命claimを受理しない。"""
    forbidden_copies = {*INHERITED_NAMES, 'baseline_audit', 'parent_audit', 'inherited_audit'}
    false_claims = {*FLAGS, *BATCH_FLAGS, 'universal_heap_or_irq_lifetime_claimed',
                    'natural_gameplay_reachability_claimed', 'full_story_reachability_claimed',
                    'natural_screen_context_invocation_proven', 'actual_runtime_execution_observed',
                    'independent_old_final_source_review_completed', 'maximum_target_access_width_proven',
                    'whole_id_tables_classified', 'padding_classified', 'source_pointer_interpretation',
                    'universal_heap_or_irq_lifetime_proven',
                    'universal_irq_or_heap_lifetime_proven', 'full_lifetime_proven',
                    'heap_lifetime_proven', 'stock_save_boundary_crossing_allowed',
                    'safe_to_lease', 'lease_authorized', 'lease_eligible'}
    zero_claims = {'donor_safe_bytes', 'safe_donor_bytes'}
    def visit(node):
        if type(node) is dict:
            need(not (set(node) & forbidden_copies) and not {'hits', 'candidate'} <= set(node),
                 'proof references old originals instead of duplicating parent state')
            for key, value in node.items():
                if key in false_claims:
                    need(value is False, 'proof cannot promote unproved lease IRQ lifetime or runtime')
                if key in zero_claims:
                    need(type(value) is int and value == 0, 'proof cannot promote safe donor capacity')
                visit(value)
        elif type(node) is list:
            for value in node:
                visit(value)
    need(type(proof) is dict, 'canonical diagnostic proof mapping')
    visit(proof)


def validate_materialized(parent_audit, full):
    """容量評価の直前も、新deltaが実際に作れる全fieldだけを認める。"""
    validate_parent_state(parent_audit)
    need(type(full) is dict, 'complete materialized mapping')
    if NAMESPACE not in full:
        need(identity(canonical(full)) == identity(canonical(parent_audit)), 'without a new delta the entire parent must remain unchanged')
    else:
        expected = materialize(parent_audit, full[NAMESPACE])
        need(identity(canonical(full)) == identity(canonical(expected)), 'all materialized fields derive only from the exact parent and new delta')
    return full

def parent_audits(*args):
    """741と737以下の各独立親を明示名で保持する。"""
    latest=parent(*args)
    inherited=previous.parent_audits(*args[:-2])
    inherited['remaining_consumers_parent']=inherited.pop('parent_audit')
    return dict(parent_audit=latest,**inherited)


def build(audit, regions, proof):
    """一意の型に完全包含される旧unknownだけを変更。分類0の診断も親行を不変で保存。"""
    validate_parent_state(audit)
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
                       kind=region.kind, evidence=copy.deepcopy(region.evidence), evidence_identity=identity(canonical(region.evidence)))
            key = json.dumps(row, sort_keys=True, separators=(',', ':'))
            if key not in witness_ids:
                witness_ids[key] = len(witness_rows)
                witness_rows.append(dict(id=len(witness_rows), **row))
            selected.append(witness_ids[key])
        hits.append(dict(**{k: old[k] for k in FIELDS},
                         classification='FALSE_POSITIVE_TYPED_REFERENCE_' + matches[0].kind.upper(),
                         accepted=True, witness_ids=sorted(set(selected))))
    delta = dict(schema_version=1, status='PASS_741_PARENT_BOUND_HELP_BATCH_REFERENCE_CHAIN',
        baseline=dict(path=BASELINE, **BASELINE_ID), parent=dict(path=PARENT, **PARENT_ID), candidate=copy.deepcopy(audit['candidate']),
        inherited_candidates=len(audit['hits']), inherited_classified=audit['classified'],
        inherited_unclassified=audit['unclassified'], changes=hits, witnesses=witness_rows,
        classified=audit['classified'] + len(hits), unclassified=audit['unclassified'] - len(hits),
        newly_classified=len(hits), proof=copy.deepcopy(proof), proof_identity=identity(canonical(proof)), donor_leased=False, donor_eligible=False,
        indirect_reference_completeness_claimed=False, old_full_rom_scan_runs=0, native_processes=0,
        donor_safe_bytes=0, **{flag: False for flag in BATCH_FLAGS})
    validate(audit, delta)
    return delta


def validate(audit, delta):
    validate_parent_state(audit)
    need(type(delta) is dict, 'canonical delta mapping')
    validate_restricted_proof(delta.get('proof'))
    need(set(delta) == TOP_FIELDS and type(delta['schema_version']) is int and delta['schema_version'] == 1 and
         delta['status'] == 'PASS_741_PARENT_BOUND_HELP_BATCH_REFERENCE_CHAIN', 'closed delta schema and status')
    counter_fields = ('inherited_candidates', 'inherited_classified', 'inherited_unclassified',
                      'classified', 'unclassified', 'newly_classified', 'old_full_rom_scan_runs', 'native_processes', 'donor_safe_bytes')
    need(all(type(delta[k]) is int and delta[k] >= 0 for k in counter_fields),
         'all counters are nonnegative integers, never booleans')
    need(type(delta['changes']) is list and type(delta['witnesses']) is list,
         'canonical change and witness lists')
    need(len(canonical(delta)) <= MAX_DELTA_BYTES, 'bounded delta without inherited evidence duplication')
    need(valid_identity(delta['proof_identity']) and
         identity(canonical(delta['proof'])) == delta['proof_identity'], 'canonical proof identity')
    need(canonical(delta['baseline']) == canonical(dict(path=BASELINE, **BASELINE_ID)), 'immutable explicit baseline identity')
    need(canonical(delta['parent']) == canonical(dict(path=PARENT, **PARENT_ID)), 'entire immutable parent delta identity')
    need(canonical(delta['candidate']) == canonical(audit['candidate']) and
         delta['inherited_candidates'] == len(audit['hits']) and
         delta['inherited_classified'] == audit['classified'] and
         delta['inherited_unclassified'] == audit['unclassified'], 'same inherited frontier')
    need(all(delta[k] is False for k in (*FLAGS, *BATCH_FLAGS)) and
         delta['old_full_rom_scan_runs'] == delta['native_processes'] == delta['donor_safe_bytes'] == 0,
         'delta cannot grant lease or fabricated execution')
    originals = {h['address']: h for h in audit['hits']}
    need(len(originals) == len(audit['hits']), 'unique original hit identity')
    changes, witnesses = delta['changes'], delta['witnesses']
    need(all(type(row) is dict and set(row) == {*FIELDS, 'classification', 'accepted', 'witness_ids'}
             for row in changes), 'closed change mappings before identity lookup')
    need(len({h['address'] for h in changes}) == len(changes) and
         [h['address'] for h in changes] == [h['address'] for h in audit['hits'] if h['address'] in
            {c['address'] for c in changes}], 'zero-or-more unique changes preserve original ordering')
    need(all(type(r) is dict and set(r) == {'id', 'address', 'size', 'kind', 'evidence', 'evidence_identity'} and
             type(r['id']) is int and type(r['address']) is int and r['address'] >= 0 and
             type(r['size']) is int and r['size'] > 0 and type(r['kind']) is str for r in witnesses) and
         [r['id'] for r in witnesses] == list(range(len(witnesses))), 'closed canonical witness rows')
    for row in witnesses:
        need(valid_identity(row['evidence_identity']) and
             identity(canonical(row['evidence'])) == row['evidence_identity'], 'canonical witness evidence identity')
        need((row['address'], row['size']) == witness_geometry(row), 'exact source-derived witness geometry')
    keys = [json.dumps({k: v for k, v in r.items() if k != 'id'}, sort_keys=True) for r in witnesses]
    need(len(set(keys)) == len(keys), 'no duplicate shared witness')
    used = set()
    for row in changes:
        need(type(row) is dict and set(row) == {*FIELDS, 'classification', 'accepted', 'witness_ids'} and
             all(type(row[k]) is int for k in ('address', 'target', 'size')) and
             all(type(row[k]) is str for k in ('kind', 'sha256', 'classification')) and
             type(row['witness_ids']) is list, 'closed strictly typed change schema')
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
                evidence=[dict(help_batch_reference_chain_witness=i) for i in change['witness_ids']])
        else:
            need(result['hits'][index] == old, 'all retained rows exactly immutable')
    result.update(classified=delta['classified'], unclassified=delta['unclassified'],
                  classifications=dict(collections.Counter(h['classification'] for h in result['hits'])),
                  help_batch_reference_chain=copy.deepcopy(delta))
    need(d.compare_inventory(result['hits'], audit)['same_inventory'], 'all original hit identities retained')
    return result
