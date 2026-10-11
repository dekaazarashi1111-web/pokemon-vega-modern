#!/usr/bin/env python3
"""619原本と25/17/33親deltaを固定する残script参照chain。"""
from __future__ import annotations

import collections
import copy
import json

import pr16_dex_hof_donor as d
import pr16_dex_hof_remaining_chain as previous

BASELINE = previous.BASELINE
BASELINE_ID = previous.BASELINE_ID
EARLIER = previous.EARLIER
EARLIER_ID = previous.EARLIER_ID
ANCESTOR = previous.PARENT
ANCESTOR_ID = previous.PARENT_ID
PARENT = 'content/modernization/pr16_dex_hof_remaining_references_evidence/reference-chain.json'
PARENT_ID = dict(size=71138, sha256='185e66b6e93eb94a6d1850b7f29b4ccfd00dfd3b3a5668a6021dbf5059fd3bd2')
PARENT_CHECKPOINT = 'content/modernization/pr16_dex_hof_remaining_references_checkpoint.json'
PARENT_CHECKPOINT_ID = dict(size=8001, sha256='62411cded366aa43cb449af76b13166e2df6476532b3997664c22baa00e1d226')
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
    if row['kind']=='battle_script_cross_field':
        import pr16_dex_hof_script_battle as battle
        e=row['evidence'];battle.geometry(e,e['hit'])
        return e['hit']['address'],4
    if row['kind']in('rooted_object_sprite_4bpp_frame','rooted_field_effect_sprite_4bpp_frame'):
        e=row['evidence'];a=e['asset'];extent=e['source_extent']
        need(e['root_verified']is True and e['bits_per_pixel']==4 and a['size']==512 and
             e['width']*e['height']//2==a['size'] and e['frame_record']['size']==8,
             'exact rooted complete raw4bpp frame geometry')
        need(e['actual_screen_rendered']is False and e['full_story_reachability_claimed']is False,
             'static frame typing never grants actual rendering or story reachability')
        need(extent['command_stride']==4 and extent['table_stride']==4 and
             e['animation']['size']==extent['command_count']*4,
             'complete source animation record extent')
        if row['kind']=='rooted_object_sprite_4bpp_frame':
            need((e['width'],e['height'],extent['table_count'])==(32,32,21) and
                 (e['graphics_id'],e['animation_index'],e['frame_index'])in
                 ((53,2,2),(53,6,7),(53,6,8),(144,4,4)), 'exact finite source object frame selectors')
        else:
            need((e['width'],e['height'],extent['table_count'],extent['frame_count'],extent['frame_stride'])==(16,64,4,6,8) and
                 (e['field_effect_id'],e['object_template_id'],e['animation_index'],e['frame_index'])==(8,7,2,4),
                 'exact finite field-effect and SurfBlob source selector')
        return a['address'],a['size']
    if row['kind']=='legacy_dpe_level_numeric_boundary':
        import pr16_dex_hof_script_learnsets as learnsets
        e=row['evidence'];w=e['typed_window'];h=e['hit'];left,right=e['left'],e['right']
        a,b=left['span'],right['span']
        need((h['address'],left['species_id'],right['species_id'])in learnsets.PAIRS,
             'exact declared original cross-sequence numeric selector')
        need(w['address']==h['address']==b['address']-3 and w['size']==6 and h['size']==4 and
             a['address']+a['size']==b['address'] and b['size']>=6 and a['size']>=3,
             'only source terminal triple plus first next numeric triple')
        need(e['historical_typing_only']is True and
             all(e[k]is False for k in('current_runtime_reachability_claimed',
                 'current_reference_absence_claimed','retirement_completeness_claimed')),
             'historical scalar typing never implies runtime retirement')
        for r in(left,right):
            need(r['pointer']['address']==learnsets.ROOT_ADDRESS+r['species_id']*4 and
                 r['pointer']['size']==4 and r['pointer']['target']==r['span']['address'] and
                 r['span']['size']==3*(r['row_count']+1), 'both actual source numeric roots and full extents')
        return w['address'],w['size']
    return previous.witness_geometry(row)


def read_measured(raw, expected, audit):
    # expectedは独立measurement envelopeの全file size/SHA。自己hashを測定根にしない。
    need(identity(raw) == expected and 0 < len(raw) <= MAX_DELTA_BYTES and raw.endswith(b'\n'),
         'entire independent measured delta bytes')
    delta = json.loads(raw)
    validate(audit, delta)
    return delta


def parent(baseline_raw, earlier_raw, ancestor_raw, parent_raw, checkpoint_raw):
    """CPの独立delta_identityで694親を検査し、25/17/33全行と全witnessを保持する。"""
    need(identity(checkpoint_raw) == PARENT_CHECKPOINT_ID and checkpoint_raw.endswith(b'\n'),
         'whole independently recorded latest parent checkpoint')
    cp = json.loads(checkpoint_raw)
    need(cp['delta_identity'] == PARENT_ID and cp['classified'] == 694 and cp['unclassified'] == 180,
         'latest checkpoint exact measured frontier')
    original = previous.parent(baseline_raw, earlier_raw, ancestor_raw)
    inherited_delta = previous.read_measured(parent_raw, cp['delta_identity'], original)
    result = previous.materialize(original, inherited_delta)
    need(result['classified'] == 694 and result['unclassified'] == 180 and
         inherited_delta['newly_classified'] == 33, 'exact measured 694 parent frontier')
    for name, changes, witnesses in (('reference_delta', 25, 22), ('reference_chain', 17, 16),
                                     ('remaining_reference_chain', 33, 33)):
        need(len(result[name]['changes']) == changes and len(result[name]['witnesses']) == witnesses,
             'complete inherited reference rows and witnesses')
        if name in original:
            need(result[name] == original[name], 'entire earlier namespace unchanged')
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
    delta = dict(schema_version=1, status='PASS_694_PARENT_BOUND_SCRIPT_REFERENCE_CHAIN',
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
         delta['status'] == 'PASS_694_PARENT_BOUND_SCRIPT_REFERENCE_CHAIN', 'closed delta schema and status')
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
                evidence=[dict(script_reference_chain_witness=i) for i in change['witness_ids']])
        else:
            need(result['hits'][index] == old, 'all retained rows exactly immutable')
    result.update(classified=delta['classified'], unclassified=delta['unclassified'],
                  classifications=dict(collections.Counter(h['classification'] for h in result['hits'])),
                  script_reference_chain=copy.deepcopy(delta))
    need(d.compare_inventory(result['hits'], audit)['same_inventory'], 'all original hit identities retained')
    return result
