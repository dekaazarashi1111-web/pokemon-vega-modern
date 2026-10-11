#!/usr/bin/env python3
"""新Blastoise asset実測の閉じた公開境界。内部producer型と公開JSON型を分離する。"""
from __future__ import annotations

import copy
import json
import re
import stat
import sys
from pathlib import Path

import pr16_dex_hof_blastoise_chain as chain
import pr16_dex_hof_blastoise_asset as field
import pr16_dex_hof_blastoise_sources as sources

ROOT = Path(__file__).resolve().parents[1]
DEV = 'content/modernization/pr16_dex_hof_blastoise_development.json'
DEVELOPMENT_PROOF = 'content/modernization/pr16_dex_hof_blastoise_development_proof.json'
PROOF = DEVELOPMENT_PROOF
SELF = 'scripts/pr16_dex_hof_blastoise_actions.py'
WF = '.github/workflows/pr16-dex-hof-blastoise-asset.yml'
GUIDE = 'docs/PR16_DEX_HOF_BLASTOISE_ASSET_JA.md'
SOURCE_CODE = frozenset({
    SELF, WF, GUIDE, DEV, DEVELOPMENT_PROOF,
    'scripts/pr16_dex_hof_blastoise_validation.py',
    'scripts/pr16_dex_hof_blastoise_sources.py',
    'scripts/pr16_dex_hof_blastoise_asset.py',
    'scripts/pr16_dex_hof_blastoise_chain.py',
    'tests/test_pr16_dex_hof_blastoise_sources.py',
    'tests/test_pr16_dex_hof_blastoise_asset.py',
    'tests/test_pr16_dex_hof_blastoise_chain.py',
    'tests/test_pr16_dex_hof_blastoise_actions.py',
    'tests/test_pr16_dex_hof_blastoise_validation.py',
})
MAX_FILE_BYTES = 1_500_000
FILES = frozenset({'measurement.json', 'reference-chain.json', 'tests.json', 'provenance.json'})
DEVELOPMENT_FIELDS = frozenset({
    'status', 'candidate', 'scope_proof_identity', 'unit_tests', 'current_rom_measured',
    'formal_classified', 'formal_unclassified', 'proposed_new_types',
    'old_scope_test_reruns', 'native_processes', 'donor_safe_bytes',
    'formal_rom_changed', 'formal_save_changed', 'source_head_before_development', 'scope_ja',
})
need, identity = field.need, field.identity


def exact(left, right):
    """公開型はbool/int、int/float、tuple/listも区別する。"""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (all(type(key) is str for key in left) and set(left) == set(right) and
                all(exact(left[key], right[key]) for key in left))
    if type(left) is list:
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return type(left) in (str, int, bool, type(None)) and left == right


def valid_identity(value):
    return (type(value) is dict and set(value) == {'size', 'sha256'} and
            type(value['size']) is int and value['size'] > 0 and
            type(value['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', value['sha256']) is not None)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'JSON重複keyを拒否')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('JSONの浮動小数点・非有限数を拒否: ' + value)


def read_text(raw):
    need(type(raw) is bytes and 0 < len(raw) <= MAX_FILE_BYTES and raw.endswith(b'\n') and
         b'\0' not in raw and b'\r' not in raw, '非空UTF-8/LF、NULなし、最大1500000byte')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                      parse_constant=_invalid_constant, parse_float=_invalid_constant)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def bindings():
    return {path: identity(read_regular(ROOT / path)) for path in sorted(SOURCE_CODE)}


def read_regular(path):
    """全祖先のsymlinkと非regular/過大fileを読取り前に拒否する。"""
    path = Path(path)
    need(not any(part.is_symlink() for part in (path, *path.parents)), '入力pathと全祖先symlink拒否')
    info = path.stat()
    need(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= MAX_FILE_BYTES,
         '非空regular入力の最大1500000byte')
    raw = path.read_bytes()
    need(0 < len(raw) <= MAX_FILE_BYTES, '実readにも最大1500000byteを適用')
    return raw


def development():
    """開発fixture2件は現ROM実測ではない。HEADに含まれる全byteを束縛する。"""
    raw = read_regular(ROOT / DEV)
    value = read_text(raw)
    proof_raw = read_regular(ROOT / DEVELOPMENT_PROOF)
    proof = read_text(proof_raw)
    need(type(value) is dict and set(value) == DEVELOPMENT_FIELDS and
         value.get('status') == 'PASS_BLASTOISE_DIAGNOSTIC_DEVELOPMENT' and
         exact(value.get('candidate'), field.CANDIDATE) and
         type(value.get('unit_tests')) is int and value['unit_tests'] > 0 and
         value.get('current_rom_measured') is False and
         exact(value.get('scope_proof_identity'), identity(proof_raw)) and
         proof_raw == chain.canonical(proof), '独立DEVとcanonical proof原本identity')
    need(exact([value[key] for key in ('formal_classified', 'formal_unclassified',
         'proposed_new_types', 'old_scope_test_reruns', 'native_processes', 'donor_safe_bytes')],
         [783, 91, 0, 0, 0, 0]) and value['formal_rom_changed'] is False and
         value['formal_save_changed'] is False, '独立DEVは正式783親のまま。実測・実行・donorへ昇格しない')
    need(type(value['source_head_before_development']) is str and
         re.fullmatch(r'[0-9a-f]{40}', value['source_head_before_development']) is not None and
         type(value['scope_ja']) is str and 0 < len(value['scope_ja']) <= 2000 and
         not any(ord(char) < 32 for char in value['scope_ja']), '独立DEVのsource HEADと説明')
    need(field.development_proofs() == proof, '独立PNG陽性と別ROM陰性を分離した固定開発原本')
    return value


def context(source_head, run_id, expected_bindings, test_count):
    need(type(source_head) is str and re.fullmatch(r'[0-9a-f]{40}', source_head) is not None,
         '今回実測source HEAD')
    need(type(run_id) is int and run_id > 0, '今回実測run正整数')
    need(type(test_count) is int and test_count > 0, '新suiteの正整数試験数')
    need(type(expected_bindings) is dict and set(expected_bindings) == SOURCE_CODE and
         all(type(path) is str and valid_identity(value) for path, value in expected_bindings.items()) and
         exact(expected_bindings, bindings()), '現checkoutの閉14source全byte identity')
    dev = development()
    need(test_count == dev['unit_tests'], '独立DEVの新suite件数と一致')
    return dev


def measured_report(proof, delta_raw, *, source_head, run_id, expected_bindings, test_count):
    context(source_head, run_id, expected_bindings, test_count)
    read_text(delta_raw)
    return dict(
        schema_version=1, status='PASS_CURRENT_BLASTOISE_CONSUMER_DIAGNOSTIC',
        measurement_origin='current_run_rom_measurement',
        candidate=copy.deepcopy(field.CANDIDATE), source_head=source_head, run_id=run_id,
        unit_tests=test_count, current_rom_reconstructions=1, current_owner_count=115,
        saved_hit_count=874, current_saved_hits_rebound=874,
        inherited_saved_inputs=62, inherited_reference_stages=30,
        inherited_changes=164, inherited_witnesses=154, classified=783, unclassified=91, newly_classified=0,
        inherited_classified=783, inherited_unclassified=91, all_prior_accepted_retained=True,
        old_scope_test_reruns=0, old_full_rom_scan_runs=0, old_native_cases_replayed=0,
        native_processes=0, donor_safe_bytes=0, formal_rom_changed=False, formal_save_changed=False,
        donor_eligible=False, donor_leased=False, release_ready=False,
        conditional_finite_type_only=True, actual_runtime_execution_observed=False,
        actual_bios_cpu_executed=False, actual_screen_rendered=False,
        # 内部trace tupleをここだけで正規化し、後段validatorはtupleを拒否する。
        scope_proof=read_text(chain.canonical(proof)), delta_identity=identity(delta_raw),
        development_identity=identity(read_regular(ROOT / DEV)),
        development_proof_identity=identity(read_regular(ROOT / DEVELOPMENT_PROOF)),
        source_bindings=copy.deepcopy(expected_bindings), public_source_bindings=copy.deepcopy(sources.SOURCE_IDS))


def test_summary(test_count):
    need(type(test_count) is int and test_count > 0, '新suite整数件数')
    return dict(status='PASS_NEW_BLASTOISE_SCOPE_TESTS', tests=test_count,
                old_scope_test_reruns=0, failures=0, errors=0, skipped=0)


def provenance(report):
    return dict(
        schema_version=1, status='PASS_CURRENT_BLASTOISE_ASSET_PROVENANCE',
        current_measurement=dict(source_head=report['source_head'], run_id=report['run_id'],
            candidate=copy.deepcopy(report['candidate']), current_rom_reconstructions=1,
            current_owner_count=115, saved_hit_count=874, current_saved_hits_rebound=874,
            measurement_canonical_identity=identity(chain.canonical(report)),
            delta_identity=copy.deepcopy(report['delta_identity'])),
        inherited_frontier=dict(classified=783, unclassified=91,
            restored_parent_identity=copy.deepcopy(chain.PARENT_AUDIT_ID),
            saved_input_identities=copy.deepcopy(chain.PARENT_INPUT_IDENTITIES),
            saved_input_count=62, reference_stages=30, changes=164, witnesses=154,
            old_scope_test_reruns=0),
        independent_development_fixture=dict(path=DEVELOPMENT_PROOF,
            identity=identity(read_regular(ROOT / DEVELOPMENT_PROOF)),
            is_current_rom_measurement=False,
            origin='separate_fixed_public_png_positive_and_local_6ff_diagnostic_fixtures'),
        actual_runtime_execution_observed=False, formal_rom_changed=False,
        formal_save_changed=False, donor_eligible=False, donor_leased=False)


def validate_report(report, delta_raw, parent, *, source_head, run_id, expected_bindings, test_count):
    dev = context(source_head, run_id, expected_bindings, test_count)
    need(type(report) is dict and 'scope_proof' in report, '閉report mapping')
    expected = measured_report(report['scope_proof'], delta_raw, source_head=source_head,
                               run_id=run_id, expected_bindings=expected_bindings, test_count=test_count)
    need(exact(report, expected), '型厳密な閉report schema/counter/false/source identity')
    need(field.validate_diagnostic_proof(report['scope_proof']) is True, '現実測は既定有限consumerと一致し、開発原本由来は別管理')
    delta = read_text(delta_raw)
    chain.validate(parent, delta)
    need(exact(delta['proof'], chain.zero_proof_template()), '診断deltaは0件で全親を保持')
    need(exact([delta['classified'], delta['unclassified'], delta['newly_classified']], [783, 91, 0]),
         '正式783親から分類0件、91未知を保持')
    return True


def write_output(directory, report, delta_raw, *, log=None):
    """実runner/試験で同じ4fileを生成。validatorより前に全hashを残す。"""
    directory = Path(directory)
    need(not any(path.is_symlink() for path in (directory, *directory.parents)), '書出し先symlink拒否')
    directory.mkdir()
    raw_files = {'measurement.json': json_bytes(report), 'reference-chain.json': delta_raw,
                 'tests.json': json_bytes(test_summary(report['unit_tests'])),
                 'provenance.json': json_bytes(provenance(report))}
    for name in sorted(FILES):
        (directory / name).write_bytes(raw_files[name])
    # 失敗時にもサイズ超過やserialization差を確認できる。内容自体はlogへ出さない。
    for name in sorted(FILES):
        print(json.dumps(dict(status='GENERATED_BLASTOISE_FILE_IDENTITY', file=name,
                              **identity((directory / name).read_bytes())), sort_keys=True),
              file=sys.stdout if log is None else log)
    return {name: identity(raw) for name, raw in raw_files.items()}


def validate_output(directory, parent, *, source_head, run_id, expected_bindings, test_count, log=None):
    directory = Path(directory)
    need(not any(path.is_symlink() for path in (directory, *directory.parents)) and directory.is_dir(),
         '公開directoryと全親pathのsymlink拒否')
    need({path.name for path in directory.iterdir()} == FILES, '余剰・欠落なしの閉4text')
    raw_files, values = {}, {}
    for name in sorted(FILES):
        path = directory / name
        need(not path.is_symlink() and stat.S_ISREG(path.stat().st_mode), 'regular flat textだけ')
        need(0 < path.stat().st_size <= MAX_FILE_BYTES, '読取前に各fileの1500000byte上限')
        raw_files[name] = path.read_bytes()
        values[name] = read_text(raw_files[name])
    report = values['measurement.json']
    validate_report(report, raw_files['reference-chain.json'], parent, source_head=source_head,
                    run_id=run_id, expected_bindings=expected_bindings, test_count=test_count)
    need(exact(values['tests.json'], test_summary(test_count)), '閉じた新suite summary')
    need(exact(values['provenance.json'], provenance(report)), '実測と独立開発の由来を厳密に分離')
    identities = {name: identity(raw_files[name]) for name in sorted(FILES)}
    for name, value in identities.items():
        print(json.dumps(dict(status='PASS_BLASTOISE_PUBLIC_FILE', file=name, **value), sort_keys=True),
              file=sys.stdout if log is None else log)
    return identities
