#!/usr/bin/env python3
"""保存782親にDiplomaの条件付きLZ10型4byteだけを追加する閉じた参照chain。"""
from __future__ import annotations

import collections
import copy
import importlib
import json

import pr16_dex_hof_credits_frontier as credits
import pr16_dex_hof_donor as d

previous = credits.previous
BASELINE = previous.BASELINE
BASELINE_ID = copy.deepcopy(previous.BASELINE_ID)
EARLIER = previous.EARLIER
EARLIER_ID = copy.deepcopy(previous.EARLIER_ID)
PARENT = credits.PARENT
PARENT_ID = copy.deepcopy(credits.PARENT_ID)
PARENT_CHECKPOINT = credits.CHECKPOINT
PARENT_CHECKPOINT_ID = copy.deepcopy(credits.CHECKPOINT_ID)
PARENT_AUDIT_ID = copy.deepcopy(credits.FULL_PARENT_ID)
PARENT_INPUTS = credits.INPUTS
PARENT_INPUT_IDENTITIES = copy.deepcopy(credits.INPUT_IDS)
INHERITED_NAMES = credits.NAMESPACES
NAMESPACE = 'diploma_reference_chain'
STATUS = 'PASS_782_PARENT_BOUND_DIPLOMA_REFERENCE_CHAIN'
KIND = 'rooted_diploma_lz10_minimum_asset'
HIT = 0x083DCAED
FIELDS = previous.FIELDS
FLAGS = previous.FLAGS
BATCH_FLAGS = previous.BATCH_FLAGS
TOP_FIELDS = frozenset(previous.TOP_FIELDS)
MAX_DELTA_BYTES = 2000000
need, identity = d.need, d.identity
canonical, valid_identity = previous.canonical, previous.valid_identity
exact = credits.exact


def _consumer():
    """親の復元は新consumerの実行・ROM入力から独立させる。"""
    return importlib.import_module('pr16_dex_hof_diploma_asset')


def _json_values(value):
    """公開境界は厳密なJSON値だけ。tuple、subclass、浮動小数点を認めない。"""
    need(type(value) in (dict, list, str, int, bool, type(None)),
         '閉じたJSON型だけ。bool/intやcontainerの別名を認めない')
    if type(value) is dict:
        need(all(type(key) is str for key in value), '全JSON keyは厳密な文字列')
        for child in value.values():
            _json_values(child)
    elif type(value) is list:
        for child in value:
            _json_values(child)


def parent(*args):
    """受入済み57保存原本だけを認証し、旧suite・ROM scan・nativeは呼ばない。"""
    result = credits.restore_parent(*args)
    validate_parent_state(result)
    return result


def validate_parent_state(audit):
    """全29namespace、旧accepted/source/claim、候補を親の完全identityで固定する。"""
    _json_values(audit)
    credits.validate_parent(audit)
    need(exact(credits.FULL_PARENT_ID, PARENT_AUDIT_ID) and
         all(audit.get(flag) is False for flag in FLAGS) and NAMESPACE not in audit,
         '782親全fieldと29段を保持し、新delta・lease権限を混入しない')


def zero_proof_template():
    """型が得られなかった場合も自己申告proofで昇格させない閉じた0件記録。"""
    return dict(status='NO_NEW_DIPLOMA_ASSET_TYPE', newly_classified=0,
                donor_safe_bytes=0, native_processes=0, old_full_rom_scan_runs=0)


def validate_restricted_proof(proof):
    """旧安全境界と原本非複製を維持し、全値の型も限定する。"""
    _json_values(proof)
    need(type(proof) is dict, 'proofは厳密なobject')
    previous.validate_restricted_proof(proof)
    forbidden = {*INHERITED_NAMES, NAMESPACE, 'baseline_audit', 'parent_audit', 'inherited_audit'}

    def visit(node):
        if type(node) is dict:
            need(not (set(node) & forbidden) and not {'hits', 'candidate'} <= set(node),
                 '全保存親・inventory・既受入namespaceをproofへ複製しない')
            for value in node.values():
                visit(value)
        elif type(node) is list:
            for value in node:
                visit(value)
    visit(proof)


def witness_geometry(row):
    """唯一の新型を独立consumerの閉schemaと最小4byte全体へ結ぶ。"""
    need(type(row) is dict and type(row.get('kind')) is str and row['kind'] == KIND,
         '登録済みDiploma型だけを受け付ける')
    evidence = row.get('evidence')
    validate_restricted_proof(evidence)
    consumer = _consumer()
    need(type(consumer.KIND) is str and consumer.KIND == KIND and
         type(consumer.HIT) is int and consumer.HIT == HIT,
         '独立consumerの型名と対象addressを固定')
    expected = consumer.evidence_template()
    _json_values(expected)
    need(type(expected) is dict and exact(evidence, expected), '独立型witnessの全fieldと厳密型')
    geometry = consumer.witness_geometry(evidence)
    need(type(geometry) in (tuple, list) and len(geometry) == 2 and
         all(type(value) is int for value in geometry) and tuple(geometry) == (HIT, 4),
         'Diploma型の範囲は厳密な整数4byte全体のみ')
    return HIT, 4


def build(audit, regions, proof):
    """0件または唯一の4byte型を追加し、全旧行と親を変更しない。"""
    validate_parent_state(audit)
    validate_restricted_proof(proof)
    need(type(regions) in (list, tuple) and len(regions) <= 1, '最小型は0個または1個だけ')
    changes, witnesses = [], []
    for region in regions:
        need(type(region) is d.TypedRegion and type(region.start) is int and
             type(region.end) is int and type(region.kind) is str and
             (region.start, region.end, region.kind) == (HIT, HIT + 4, KIND),
             '正確な4byte全体のTypedRegionだけ')
        validate_restricted_proof(region.evidence)
        row = dict(id=0, address=HIT, size=4, kind=KIND,
                   evidence=copy.deepcopy(region.evidence),
                   evidence_identity=identity(canonical(region.evidence)))
        witness_geometry(row)
        old = next(hit for hit in audit['hits'] if hit['address'] == HIT)
        changes.append(dict(**{key: old[key] for key in FIELDS},
                            classification='FALSE_POSITIVE_TYPED_REFERENCE_' + KIND.upper(),
                            accepted=True, witness_ids=[0]))
        witnesses.append(row)
    delta = dict(schema_version=1, status=STATUS,
        baseline=dict(path=BASELINE, **BASELINE_ID), parent=dict(path=PARENT, **PARENT_ID),
        candidate=copy.deepcopy(audit['candidate']), inherited_candidates=len(audit['hits']),
        inherited_classified=audit['classified'], inherited_unclassified=audit['unclassified'],
        changes=changes, witnesses=witnesses, classified=audit['classified'] + len(changes),
        unclassified=audit['unclassified'] - len(changes), newly_classified=len(changes),
        proof=copy.deepcopy(proof), proof_identity=identity(canonical(proof)),
        old_full_rom_scan_runs=0, native_processes=0, donor_safe_bytes=0,
        **{flag: False for flag in (*FLAGS, *BATCH_FLAGS)})
    validate(audit, delta)
    return delta


def validate(audit, delta):
    validate_parent_state(audit)
    _json_values(delta)
    need(type(delta) is dict and set(delta) == TOP_FIELDS, '余分・欠落を拒否する閉schema')
    need(type(delta['schema_version']) is int and delta['schema_version'] == 1 and
         type(delta['status']) is str and delta['status'] == STATUS,
         'Diploma専用statusと整数schema版')
    counters = ('inherited_candidates', 'inherited_classified', 'inherited_unclassified',
                'classified', 'unclassified', 'newly_classified', 'old_full_rom_scan_runs',
                'native_processes', 'donor_safe_bytes')
    need(all(type(delta[key]) is int and delta[key] >= 0 for key in counters),
         '全counterは非負整数。bool/float別名は拒否')
    validate_restricted_proof(delta['proof'])
    need(valid_identity(delta['proof_identity']) and
         identity(canonical(delta['proof'])) == delta['proof_identity'], 'proof完全identity')
    need(len(canonical(delta)) <= MAX_DELTA_BYTES, '旧原本を複製しない小delta')
    need(exact(delta['baseline'], dict(path=BASELINE, **BASELINE_ID)) and
         exact(delta['parent'], dict(path=PARENT, **PARENT_ID)), '独立baseline/親原本identity')
    need(exact(delta['candidate'], audit['candidate']) and
         (delta['inherited_candidates'], delta['inherited_classified'], delta['inherited_unclassified']) == (874, 782, 92),
         '正式candidateと874/782/92 frontier')
    need(all(delta[key] is False for key in (*FLAGS, *BATCH_FLAGS)) and
         delta['old_full_rom_scan_runs'] == delta['native_processes'] == delta['donor_safe_bytes'] == 0,
         'lease・全到達・全寿命・実行・安全容量を昇格しない')
    changes, witnesses = delta['changes'], delta['witnesses']
    need(type(changes) is list and type(witnesses) is list and
         len(changes) == len(witnesses) <= 1, '変更/witnessは同数の0件または1件だけ')
    if changes:
        need(_consumer().validate_scope_proof(delta['proof']) is True,
             '独立consumerの有限scope証明を自己申告proofで代用しない')
    else:
        need(exact(delta['proof'], zero_proof_template()), '0件診断は閉じた非昇格proofだけ')
    for row in witnesses:
        need(type(row) is dict and set(row) == {'id', 'address', 'size', 'kind', 'evidence', 'evidence_identity'} and
             all(type(row[key]) is int for key in ('id', 'address', 'size')) and
             type(row['kind']) is str and
             (row['id'], row['address'], row['size'], row['kind']) == (0, HIT, 4, KIND),
             '唯一のwitness行の閉schemaと厳密整数geometry')
        need(valid_identity(row['evidence_identity']) and
             identity(canonical(row['evidence'])) == row['evidence_identity'], 'witness完全identity')
        need(witness_geometry(row) == (row['address'], row['size']), '独立consumer最小型との結合')
    for row in changes:
        need(type(row) is dict and set(row) == {*FIELDS, 'classification', 'accepted', 'witness_ids'} and
             all(type(row[key]) is int for key in ('address', 'target', 'size')) and
             all(type(row[key]) is str for key in ('kind', 'sha256', 'classification')),
             '変更行の閉schemaと厳密型')
        old = next(hit for hit in audit['hits'] if hit['address'] == HIT)
        need(old['accepted'] is False and old['classification'] == 'UNCLASSIFIED' and
             row['address'] == HIT and row['size'] == 4 and all(row[key] == old[key] for key in FIELDS),
             '唯一の既存unknownの全identityだけを変更')
        need(row['accepted'] is True and type(row['witness_ids']) is list and
             len(row['witness_ids']) == 1 and type(row['witness_ids'][0]) is int and row['witness_ids'][0] == 0,
             '実在する唯一のwitnessを厳密に参照')
        need(row['classification'] == 'FALSE_POSITIVE_TYPED_REFERENCE_' + KIND.upper() and
             d.contains(witnesses[0]['address'], witnesses[0]['address'] + witnesses[0]['size'], row['address'], row['size']),
             '4byte全体が同型で包含される分類')
    need((delta['newly_classified'], delta['classified'], delta['unclassified']) ==
         (len(changes), 782 + len(changes), 92 - len(changes)), '0または1件の正確な加算')
    return len(changes)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'JSONの重複keyを拒否')
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError('JSONの非有限定数を拒否: ' + value)


def read_measured(raw, expected, audit):
    """独立envelopeの全byteを認証した後で閉schemaを検証する。"""
    need(valid_identity(expected) and type(raw) is bytes and identity(raw) == expected and
         0 < len(raw) <= MAX_DELTA_BYTES and raw.endswith(b'\n') and b'\r' not in raw,
         '独立計測deltaの全LF byteとidentity')
    delta = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    validate(audit, delta)
    return delta


def materialize(audit, delta):
    """全874行を計算時だけ再構成。sourceと全29既受入namespaceはdeep copy。"""
    validate(audit, delta)
    result = copy.deepcopy(audit)
    for row in delta['changes']:
        index = next(i for i, hit in enumerate(audit['hits']) if hit['address'] == row['address'])
        result['hits'][index] = dict(**{key: row[key] for key in FIELDS},
            classification=row['classification'], accepted=True,
            evidence=[{NAMESPACE + '_witness': 0}])
    result.update(classified=delta['classified'], unclassified=delta['unclassified'],
                  classifications=dict(collections.Counter(hit['classification'] for hit in result['hits'])))
    result[NAMESPACE] = copy.deepcopy(delta)
    need(d.compare_inventory(result['hits'], audit)['same_inventory'], '全874行の元identityを保持')
    need(all(exact(current, old) for current, old in zip(result['hits'], audit['hits'])
             if old['address'] != HIT), '他873行のaccepted/unknownと全fieldを保持')
    need(all(exact(result[key], value) for key, value in audit.items()
             if key not in {'hits', 'classified', 'unclassified', 'classifications'}),
         '旧全namespace・source・false claimをそのまま保持')
    return result
