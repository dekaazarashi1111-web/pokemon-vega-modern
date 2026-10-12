#!/usr/bin/env python3
"""全十六段749親deltaを固定するevent/battle boundary batch参照chain。最小型と全到達・安全寿命は分離。"""
from __future__ import annotations

import collections
import copy
import importlib
import json

import pr16_dex_hof_donor as d
import pr16_dex_hof_field_consumer_batch_chain as previous

BASELINE = previous.BASELINE
BASELINE_ID = previous.BASELINE_ID
EARLIER = previous.EARLIER
EARLIER_ID = previous.EARLIER_ID
PARENT = 'content/modernization/pr16_dex_hof_field_consumer_batch_evidence/reference-chain.json'
PARENT_ID = {'size': 75712, 'sha256': 'f2b07ad37d428bb4d1be56da6fb65b3a9086a6957c60056697c32ecfc38d8fb3'}
PARENT_CHECKPOINT = 'content/modernization/pr16_dex_hof_field_consumer_batch_checkpoint.json'
PARENT_CHECKPOINT_ID = {'size': 75332, 'sha256': '608c5faa5f2f2b8ff988ef25dbbf77ad5fffbcafc4da4aee8809a521251f098f'}
PARENT_AUDIT_ID = {'size': 3723169, 'sha256': '4926244f68c3f522eef9b40293c086ede8ccc8831e4fcbf00e93b207e7784a84'}
PARENT_INPUTS = (*previous.PARENT_INPUTS, PARENT, PARENT_CHECKPOINT)

# 各原本の全byteを束縛する。記録本文は複製しない。
PARENT_INPUT_IDENTITIES = {'content/modernization/pr16_dex_hof_typed_recovery_evidence/egg-typed-audit.json': {'size': 4063919, 'sha256': '814082398937869b6cc17faa09cbf1833f0c7f4aa300ddbd83d0de833d44b74c'}, 'content/modernization/pr16_dex_hof_reference_evidence/reference-delta.json': {'size': 149772, 'sha256': '762320ba350f528777b90be404b5fec1d88caeb6dbf6594590d4f45b852c1c87'}, 'content/modernization/pr16_dex_hof_reference_gaps_evidence/reference-chain.json': {'size': 95619, 'sha256': 'c38d8e67a6718cacc17a3999922dca9edd9977734711b3cf5a74f85c1b76bb32'}, 'content/modernization/pr16_dex_hof_remaining_references_evidence/reference-chain.json': {'size': 71138, 'sha256': '185e66b6e93eb94a6d1850b7f29b4ccfd00dfd3b3a5668a6021dbf5059fd3bd2'}, 'content/modernization/pr16_dex_hof_remaining_references_checkpoint.json': {'size': 8001, 'sha256': '62411cded366aa43cb449af76b13166e2df6476532b3997664c22baa00e1d226'}, 'content/modernization/pr16_dex_hof_script_references_evidence/reference-chain.json': {'size': 134951, 'sha256': 'da105fd05e4ddb51bd7648af890db509c9b8f1e7e79112dbc1b295ce15b51279'}, 'content/modernization/pr16_dex_hof_script_references_checkpoint.json': {'size': 8864, 'sha256': '026944a1ae8d2bfeca0eb3105868d9ebe3fc1b8f0d7669fc18b7fb69fddc58ff'}, 'content/modernization/pr16_dex_hof_consumer_references_evidence/reference-chain.json': {'size': 28406, 'sha256': '20a394e6ce825113bbfd833989c18528a44f665f79eaf1c91f1ab6899a796dc7'}, 'content/modernization/pr16_dex_hof_consumer_references_checkpoint.json': {'size': 11195, 'sha256': '660b6dc8b99c0005e8804998ad962772358233338eb2876d12853d75507342b9'}, 'content/modernization/pr16_dex_hof_controller_space_evidence/reference-chain.json': {'size': 23481, 'sha256': '1ede9031a30c4c5f52ec2b6cbf47ad177c4117931fb72796ce597c2786c01476'}, 'content/modernization/pr16_dex_hof_controller_space_checkpoint.json': {'size': 9621, 'sha256': 'a81a17085d98690f9e397c02f6334680e8064f76e0e7e24cc9f9fabb520ef631'}, 'content/modernization/pr16_dex_hof_callback_references_evidence/reference-chain.json': {'size': 22816, 'sha256': 'c49c05072bb5dcf19de4620440bfde82ad66e3c1269566a9b6184ebc9870bbc6'}, 'content/modernization/pr16_dex_hof_callback_references_checkpoint.json': {'size': 10439, 'sha256': 'f6530690ae80c432d94aef8288273eb8f5a1bbf7b4c80115146a9cac9329e464'}, 'content/modernization/pr16_dex_hof_callback_lifetimes_evidence/reference-chain.json': {'size': 60153, 'sha256': '06595ebf5830e45334dbb83ec1fb96658d40879f6f4a0126e3718a8d5ae6100a'}, 'content/modernization/pr16_dex_hof_callback_lifetimes_checkpoint.json': {'size': 52637, 'sha256': '974f9bc2cb87f30112a40e6c5df29ad4734336216a2e64f3568aeddb5150705a'}, 'content/modernization/pr16_dex_hof_runtime_closure_evidence/reference-chain.json': {'size': 68925, 'sha256': '7fdc8ed846f529fd7dfd5b35b322ddf8bd1eb46e18f5fd45239e21e998adae8e'}, 'content/modernization/pr16_dex_hof_runtime_closure_checkpoint.json': {'size': 55238, 'sha256': 'b9252156201ab5c7506396270d9757522240767a3a781a7330237b1c9ba50927'}, 'content/modernization/pr16_dex_hof_boundary_references_evidence/reference-chain.json': {'size': 13165, 'sha256': '5b9ff2600caec75c226e720010e772725c76ec52da2391024176d01f19892eb7'}, 'content/modernization/pr16_dex_hof_boundary_references_checkpoint.json': {'size': 14687, 'sha256': 'd97afe368fecf0b369e3630180dc1f579501ac6a2d276cfcbe5647a973703f7a'}, 'content/modernization/pr16_dex_hof_party_references_evidence/reference-chain.json': {'size': 375903, 'sha256': '55bc39b3b22ad61654fa24dbf37e5c44b33aae16357acf70e823af5baf4a748c'}, 'content/modernization/pr16_dex_hof_party_references_checkpoint.json': {'size': 349521, 'sha256': '5236fec1ccd849b4110093ba2587885913a3f0eb767759d21a6932ef21ba8cda'}, 'content/modernization/pr16_dex_hof_summary_references_evidence/reference-chain.json': {'size': 681669, 'sha256': 'c11d71495d60fda8fed98464eb6962f7b57be75dc39e8b479be3d57903d68586'}, 'content/modernization/pr16_dex_hof_summary_references_checkpoint.json': {'size': 627652, 'sha256': 'e63d3dfda20758d9a2f120a06bfc870183adf1cd997d887462babdae9af6529a'}, 'content/modernization/pr16_dex_hof_remaining_consumers_evidence/reference-chain.json': {'size': 875373, 'sha256': '1fb58b88ac19198de7ef29fc0728908c1fb720915bfa53d265b78994252a6917'}, 'content/modernization/pr16_dex_hof_remaining_consumers_checkpoint.json': {'size': 809502, 'sha256': '55cfbf03e124c26f78ed00b52b9d2da7604642c892dc8c85f0754b3e1a82aca3'}, 'content/modernization/pr16_dex_hof_help_batch_evidence/reference-chain.json': {'size': 352753, 'sha256': '53f4789fb532d93791fa7e0962b7feea9f74003d342f5175d00e1b07de7aa5d0'}, 'content/modernization/pr16_dex_hof_help_batch_checkpoint.json': {'size': 335169, 'sha256': 'dff4dcab9cd7fadce44cbc6456d00ade32b724f9553455e3d66acfe9850e547f'}, 'content/modernization/pr16_dex_hof_root_batch_evidence/reference-chain.json': {'size': 478118, 'sha256': '2089134cff6c3f920bea3476e8c0b9e883901eff42eb7f933fd86c91e71f485e'}, 'content/modernization/pr16_dex_hof_root_batch_checkpoint.json': {'size': 444776, 'sha256': '5fadebac1cd15e645ce5cb047148e1e59fa193af735518138fc8373beb565d55'}, 'content/modernization/pr16_dex_hof_field_consumer_batch_evidence/reference-chain.json': {'size': 75712, 'sha256': 'f2b07ad37d428bb4d1be56da6fb65b3a9086a6957c60056697c32ecfc38d8fb3'}, 'content/modernization/pr16_dex_hof_field_consumer_batch_checkpoint.json': {'size': 75332, 'sha256': '608c5faa5f2f2b8ff988ef25dbbf77ad5fffbcafc4da4aee8809a521251f098f'}}
INHERITED_NAMES = (*previous.INHERITED_NAMES, previous.NAMESPACE)
FIELDS = ('address', 'target', 'kind', 'size', 'sha256')
FLAGS = ('donor_leased', 'donor_eligible', 'indirect_reference_completeness_claimed')
need, identity = d.need, d.identity
MAX_DELTA_BYTES = 2000000
# producerが結合済みの新consumerだけを登録する。guardは型witnessへ昇格させない。
# field_consumer_batchの既存証拠はpreviousが旧validatorで検査し、新registryへ渡さない。
NEW_KIND_MODULES = {
    'rooted_battle_tail_minimum_cross_field': 'pr16_dex_hof_battle_tail_roots',
}
NAMESPACE = 'event_boundary_batch_reference_chain'
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
    need(False, 'new event/battle boundary batch requires its dedicated registered consumer kind')


def read_measured(raw, expected, audit):
    # expectedは独立measurement envelopeの全file size/SHA。自己hashを測定根にしない。
    need(valid_identity(expected) and type(raw) is bytes and identity(raw) == expected and 0 < len(raw) <= MAX_DELTA_BYTES and raw.endswith(b'\n') and b'\r' not in raw,
         'entire independent measured delta bytes')
    delta = json.loads(raw)
    validate(audit, delta)
    return delta


def parent(*args):
    """独立checkpointで749親を検査し、全十六段130行120witnessを保存する。"""
    need(len(args) == len(PARENT_INPUTS), 'all thirty-one independently identified parent inputs')
    need(all(type(raw) is bytes and raw.endswith(b'\n') and b'\r' not in raw for raw in args),
         'all parent inputs are complete LF bytes')
    need(tuple(PARENT_INPUT_IDENTITIES) == PARENT_INPUTS and
         all(identity(raw) == PARENT_INPUT_IDENTITIES[path] for path, raw in zip(PARENT_INPUTS, args)),
         'all thirty-one parent inputs match their independent complete identities')
    checkpoint_raw = args[-1]
    need(identity(checkpoint_raw) == PARENT_CHECKPOINT_ID,
         'whole independently recorded749 checkpoint')
    cp = json.loads(checkpoint_raw)
    need(cp['delta_identity'] == PARENT_ID and cp['classified'] == 749 and cp['unclassified'] == 125,
         'latest checkpoint exact749 measured frontier')
    original = previous.parent(*args[:-2])
    inherited_delta = previous.read_measured(args[-2], cp['delta_identity'], original)
    result = previous.materialize(original, inherited_delta)
    need((result['classified'], result['unclassified'], inherited_delta['newly_classified']) == (749,125,3),
         'exact measured749 parent frontier')
    need(len(result['hits']) == 874 and
         sum(len(result[name]['changes']) for name in INHERITED_NAMES) == 130 and
         sum(len(result[name]['witnesses']) for name in INHERITED_NAMES) == 120,
         'entire874 inventory and all130 changes120 witnesses retained')
    for name, changes, witnesses in (('reference_delta',25,22),('reference_chain',17,16),
            ('remaining_reference_chain',33,33),('script_reference_chain',29,23),('consumer_reference_chain',3,3),('space_reference_chain',2,2),('callback_reference_chain',1,1),('lifetime_reference_chain',0,0),('runtime_reference_chain',3,3),('boundary_reference_chain',1,1),('party_reference_chain',2,2),('summary_reference_chain',2,2),('remaining_consumers_reference_chain',4,4),('help_batch_reference_chain',2,2),('root_batch_reference_chain',3,3),('field_consumer_batch_reference_chain',3,3)):
        need((len(result[name]['changes']), len(result[name]['witnesses'])) == (changes, witnesses),
             'all sixteen complete inherited changes and witnesses')
        if name in original:
            need(result[name] == original[name], 'every earlier namespace entirely unchanged')
    need(identity(canonical(result)) == PARENT_AUDIT_ID,
         'entire canonical749 parent with all original fields')
    song = inherited_delta['proof']['song']
    need(cp['combined_song_models'] == song['combined_song_models'] == 133 and
         cp['retained_sample_witnesses'] == song['retained_sample_witnesses'] == 50 and
         song['all133_models_exact'] is True and song['all50_sample_identities_exact'] is True,
         'all133 song models and50 sample identities retained')
    validate_parent_state(result)
    return result



def validate_parent_state(audit):
    """749親の全fieldを認証し、旧accepted改変や暗黙の安全昇格を拒否する。"""
    need(type(audit) is dict and identity(canonical(audit)) == PARENT_AUDIT_ID,
         'entire exact749 parent state with all original fields')
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
                    'safe_to_lease', 'lease_authorized', 'lease_eligible',
                    'indirect_reference_completeness_proven', 'target_retirement_proven',
                    'partial_retirement_proven', 'explicit_owner_transfer_proven',
                    'owner_transfer_proven', 'all_save_entry_heap_ready_proven',
                    'synchronous_nonreentrant_use_proven',
                    'universal_nonreachability_claimed', 'all_callers_unreachable_claimed',
                    'all_writers_absent_claimed', 'guard_promoted_to_classification',
                    'full_game_unreachability_claimed', 'all_game_contexts_unreachable'}
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
        elif type(node) in (list, tuple):
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
    """749と746以下の各独立親を明示名で保持する。"""
    latest=parent(*args)
    inherited=previous.parent_audits(*args[:-2])
    inherited['field_consumer_batch_parent']=inherited.pop('parent_audit')
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
    delta = dict(schema_version=1, status='PASS_749_PARENT_BOUND_EVENT_BOUNDARY_BATCH_REFERENCE_CHAIN',
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
         delta['status'] == 'PASS_749_PARENT_BOUND_EVENT_BOUNDARY_BATCH_REFERENCE_CHAIN', 'closed delta schema and status')
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
        validate_restricted_proof(row['evidence'])
        need(valid_identity(row['evidence_identity']) and
             identity(canonical(row['evidence'])) == row['evidence_identity'], 'canonical witness evidence identity')
        geometry = witness_geometry(row)
        need(type(geometry) in (tuple, list) and len(geometry) == 2 and
             all(type(value) is int for value in geometry) and
             geometry[0] >= 0 and geometry[1] > 0 and
             (row['address'], row['size']) == tuple(geometry),
             'exact strictly integer source-derived witness geometry')
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
                evidence=[dict(event_boundary_batch_reference_chain_witness=i) for i in change['witness_ids']])
        else:
            need(result['hits'][index] == old, 'all retained rows exactly immutable')
    result.update(classified=delta['classified'], unclassified=delta['unclassified'],
                  classifications=dict(collections.Counter(h['classification'] for h in result['hits'])),
                  event_boundary_batch_reference_chain=copy.deepcopy(delta))
    need(d.compare_inventory(result['hits'], audit)['same_inventory'], 'all original hit identities retained')
    return result
