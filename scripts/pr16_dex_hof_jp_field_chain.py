#!/usr/bin/env python3
"""保存済み779親からJP badge文の4byteだけを追加する閉じた参照chain。"""
from __future__ import annotations

import collections
import copy
import json

import pr16_dex_hof_donor as d
import pr16_dex_hof_jp_field_text as consumer
import pr16_dex_hof_registered_ui_batch_chain as previous

BASELINE = previous.BASELINE
BASELINE_ID = copy.deepcopy(previous.BASELINE_ID)
EARLIER = previous.EARLIER
EARLIER_ID = copy.deepcopy(previous.EARLIER_ID)
PARENT = 'content/modernization/pr16_dex_hof_registered_ui_batch_evidence/reference-chain.json'
PARENT_ID = {'size': 339411, 'sha256': '217052875ea454411851c20ac9fa8a60f3910fa2c3819e4e372cdf4f544af501'}
PARENT_CHECKPOINT = 'content/modernization/pr16_dex_hof_registered_ui_batch_checkpoint.json'
PARENT_CHECKPOINT_ID = {'size': 305095, 'sha256': 'e0115e1a47dfb5db7f0730c3fa3acae69c8bb75f0ec2d6182bf8757d2077b7da'}
PARENT_AUDIT_ID = {'size': 4433327, 'sha256': '80bbcb126b5e4fe387624e7a8a0f081ff55df3a2a47bb1dc5f0217ede05149d4'}
PARENT_INPUTS = (*previous.PARENT_INPUTS, PARENT, PARENT_CHECKPOINT)
PARENT_INPUT_IDENTITIES = {**copy.deepcopy(previous.PARENT_INPUT_IDENTITIES),
                           PARENT: dict(PARENT_ID), PARENT_CHECKPOINT: dict(PARENT_CHECKPOINT_ID)}
INHERITED_NAMES = (*previous.INHERITED_NAMES, previous.NAMESPACE)
NAMESPACE = 'jp_field_reference_chain'
STATUS = 'PASS_779_PARENT_BOUND_JP_FIELD_REFERENCE_CHAIN'
KIND = 'rooted_jp_field_badge_minimum_text'
HIT = 0x083DDEE1
FIELDS = previous.FIELDS
FLAGS = previous.FLAGS
BATCH_FLAGS = previous.BATCH_FLAGS
TOP_FIELDS = frozenset(previous.TOP_FIELDS)
MAX_DELTA_BYTES = 2000000
need, identity = d.need, d.identity
canonical, valid_identity = previous.canonical, previous.valid_identity


def witness_geometry(row):
    """新型の最小4byteだけを専用consumerの閉じたwitnessへ結ぶ。"""
    need(type(row) is dict and row.get('kind') == KIND and consumer.KIND == KIND and
         consumer.HIT == HIT, '独立JP field型と対象addressだけを登録')
    geometry = consumer.witness_geometry(row.get('evidence'))
    need(type(geometry) in (tuple, list) and len(geometry) == 2 and
         all(type(value) is int for value in geometry) and tuple(geometry) == (HIT, 4),
         'JP field型の範囲は厳密な整数4byteのみ')
    return HIT, 4


def parent(*args):
    """全51保存原本を認証する。旧suite・ROM scan・nativeは実行しない。"""
    need(len(args) == len(PARENT_INPUTS) == 51, '全51個の独立親入力')
    need(all(type(raw) is bytes and raw.endswith(b'\n') and b'\r' not in raw for raw in args),
         '親入力は全byteを保持したLF形式')
    need(tuple(PARENT_INPUT_IDENTITIES) == PARENT_INPUTS and
         all(identity(raw) == PARENT_INPUT_IDENTITIES[path] for path, raw in zip(PARENT_INPUTS, args)),
         '全51原本の順序と完全identity一致')
    checkpoint = json.loads(args[-1])
    need(checkpoint['delta_identity'] == PARENT_ID and
         (checkpoint['classified'], checkpoint['unclassified'], checkpoint['newly_classified']) == (779, 95, 3),
         '独立checkpointの正式779/95と3件delta')
    original = previous.parent(*args[:-2])
    inherited_delta = previous.read_measured(args[-2], checkpoint['delta_identity'], original)
    result = previous.materialize(original, inherited_delta)
    need((result['classified'], result['unclassified'], len(result['hits'])) == (779, 95, 874),
         '874全inventoryと正式779親')
    need(len(INHERITED_NAMES) == 26 and
         sum(len(result[name]['changes']) for name in INHERITED_NAMES) == 160 and
         sum(len(result[name]['witnesses']) for name in INHERITED_NAMES) == 150 and
         (len(result[previous.NAMESPACE]['changes']), len(result[previous.NAMESPACE]['witnesses'])) == (3, 3),
         '全26段160変更150witnessをそのまま保持')
    need(all(result[name] == original[name] for name in previous.INHERITED_NAMES),
         'それ以前の全namespaceは原本の全fieldと一致')
    song = inherited_delta['proof']['song']
    need(checkpoint['combined_song_models'] == song['combined_song_models'] == 133 and
         checkpoint['retained_sample_witnesses'] == song['retained_sample_witnesses'] == 50 and
         song['all133_models_exact'] is True and song['all50_sample_identities_exact'] is True,
         '全133曲モデルと50sample identityを保持')
    validate_parent_state(result)
    return result


def parent_audits(*args):
    """779親と既存容量計算が使う以前の各親を別名で返す。"""
    latest = parent(*args)
    inherited = previous.parent_audits(*args[:-2])
    inherited['registered_ui_batch_parent'] = inherited.pop('parent_audit')
    return dict(parent_audit=latest, **inherited)


def validate_parent_state(audit):
    """親の全fieldを固定し、旧accepted・source・安全claimの変更を拒否。"""
    need(type(audit) is dict and identity(canonical(audit)) == PARENT_AUDIT_ID,
         '全fieldが独立779親identityと一致')
    need(all(audit.get(flag) is False for flag in FLAGS) and NAMESPACE not in audit,
         '親にlease権限や新deltaを追加しない')


def validate_restricted_proof(proof):
    """旧規則を保ち、新たな安全昇格・旧原本複製も拒否する。"""
    previous.validate_restricted_proof(proof)
    false_claims = {'opaque_callee_effects_proven', 'field_move_function_called',
                    'field_function_called', 'pointer_host_seeded', 'text_pointer_host_seeded',
                    'existing_execution_replayed', 'full_candidate_regression_complete',
                    'release_ready', 'rom_mutation_performed'}
    zero_claims = {'old_full_rom_scan_runs', 'native_processes', 'rom_writes', 'save_writes'}
    def visit(node):
        if type(node) is dict:
            need(previous.NAMESPACE not in node, '最新UI親もproofへ複製しない')
            for key, value in node.items():
                if key in false_claims:
                    need(value is False, '未証明effect・seed・実行・releaseを昇格しない')
                if key in zero_claims:
                    need(type(value) is int and value == 0, '旧再実行とROM/save変更は0')
                visit(value)
        elif type(node) in (list, tuple):
            for value in node:
                visit(value)
    visit(proof)


def build(audit, regions, proof):
    """0件診断か唯一の4byte型だけを追加し、旧全行を保存する。"""
    validate_parent_state(audit)
    need(type(regions) in (list, tuple) and len(regions) <= 1, '0または1個の最小型だけ')
    changes, witnesses = [], []
    for region in regions:
        need(type(region) is d.TypedRegion and type(region.start) is int and
             type(region.end) is int and (region.start, region.end, region.kind) == (HIT, HIT + 4, KIND),
             '正確な4byte TypedRegionだけ')
        row = dict(id=0, address=region.start, size=4, kind=region.kind,
                   evidence=copy.deepcopy(region.evidence), evidence_identity=identity(canonical(region.evidence)))
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
    need(type(delta) is dict and set(delta) == TOP_FIELDS, '余分・欠落を拒否する閉schema')
    need(type(delta['schema_version']) is int and delta['schema_version'] == 1 and
         delta['status'] == STATUS, 'JP field専用statusと整数schema版')
    counters = ('inherited_candidates', 'inherited_classified', 'inherited_unclassified',
                'classified', 'unclassified', 'newly_classified', 'old_full_rom_scan_runs',
                'native_processes', 'donor_safe_bytes')
    need(all(type(delta[key]) is int and delta[key] >= 0 for key in counters),
         'counterは非負整数でbool/float別名を認めない')
    validate_restricted_proof(delta['proof'])
    need(valid_identity(delta['proof_identity']) and
         identity(canonical(delta['proof'])) == delta['proof_identity'], 'proof完全identity')
    need(len(canonical(delta)) <= MAX_DELTA_BYTES, '旧原本を複製しない小delta')
    need(canonical(delta['baseline']) == canonical(dict(path=BASELINE, **BASELINE_ID)) and
         canonical(delta['parent']) == canonical(dict(path=PARENT, **PARENT_ID)), '独立baseline/親原本identity')
    need(canonical(delta['candidate']) == canonical(audit['candidate']) and
         (delta['inherited_candidates'], delta['inherited_classified'], delta['inherited_unclassified']) == (874, 779, 95),
         '正式candidateと874/779/95 frontier')
    need(all(delta[key] is False for key in (*FLAGS, *BATCH_FLAGS)) and
         delta['old_full_rom_scan_runs'] == delta['native_processes'] == delta['donor_safe_bytes'] == 0,
         'lease・全到達・全寿命・実行・安全容量を昇格しない')
    changes, witnesses = delta['changes'], delta['witnesses']
    need(type(changes) is list and type(witnesses) is list and
         len(changes) == len(witnesses) <= 1, '変更/witnessは同数の0件または1件だけ')
    for row in witnesses:
        need(type(row) is dict and set(row) == {'id', 'address', 'size', 'kind', 'evidence', 'evidence_identity'} and
             all(type(row[key]) is int for key in ('id', 'address', 'size')) and
             (row['id'], row['address'], row['size'], row['kind']) == (0, HIT, 4, KIND),
             '唯一のwitness行の閉schemaと厳密整数geometry')
        validate_restricted_proof(row['evidence'])
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
         (len(changes), 779 + len(changes), 95 - len(changes)), '0または1件の正確な加算')
    return len(changes)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'JSONの重複keyを拒否')
        result[key] = value
    return result


def read_measured(raw, expected, audit):
    """独立envelopeの全byteを認証してから閉schemaを検証する。"""
    need(valid_identity(expected) and type(raw) is bytes and identity(raw) == expected and
         0 < len(raw) <= MAX_DELTA_BYTES and raw.endswith(b'\n') and b'\r' not in raw,
         '独立計測deltaの全LF byteとidentity')
    delta = json.loads(raw, object_pairs_hook=_unique_object)
    validate(audit, delta)
    return delta


def materialize(audit, delta):
    """874行を計算時だけ再構成。sourceと全既受入namespaceはdeep copy。"""
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
    return result


def validate_materialized(parent_audit, full):
    """追加deltaが実際に作れる全field以外を容量判定へ渡さない。"""
    validate_parent_state(parent_audit)
    need(type(full) is dict, '完全なmaterialized mapping')
    expected = materialize(parent_audit, full[NAMESPACE]) if NAMESPACE in full else parent_audit
    need(identity(canonical(full)) == identity(canonical(expected)), '親と新deltaだけから全fieldを導出')
    return full
