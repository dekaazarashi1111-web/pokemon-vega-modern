#!/usr/bin/env python3
"""新minigame実測の閉じた公開境界。内部producer型と公開JSON型を分離する。"""
from __future__ import annotations

import copy
import json
import re
import stat
import sys
from pathlib import Path

import pr16_dex_hof_jp_minigame_chain as chain
import pr16_dex_hof_jp_minigame_text as field

ROOT = Path(__file__).resolve().parents[1]
DEV = 'content/modernization/pr16_dex_hof_jp_minigame_development.json'
DEVELOPMENT_PROOF = 'content/modernization/pr16_dex_hof_jp_minigame_development_proof.json'
MANIFEST = 'content/modernization/pr16_dex_hof_jp_minigame_sources.json'
SELF = 'scripts/pr16_dex_hof_jp_minigame_actions.py'
WF = '.github/workflows/pr16-dex-hof-jp-minigame-text.yml'
GUIDE = 'docs/PR16_DEX_HOF_JP_MINIGAME_TEXT_JA.md'
SOURCE_CODE = frozenset({
    SELF, WF, GUIDE, DEV, DEVELOPMENT_PROOF, MANIFEST,
    'scripts/pr16_dex_hof_jp_minigame_validation.py',
    'scripts/pr16_dex_hof_jp_minigame_roots.py',
    'scripts/pr16_dex_hof_jp_minigame_text.py',
    'scripts/pr16_dex_hof_jp_minigame_chain.py',
    'tests/test_pr16_dex_hof_jp_minigame_roots.py',
    'tests/test_pr16_dex_hof_jp_minigame_text.py',
    'tests/test_pr16_dex_hof_jp_minigame_chain.py',
    'tests/test_pr16_dex_hof_jp_minigame_actions.py',
})
MAX_FILE_BYTES = 1_500_000
FILES = frozenset({'measurement.json', 'reference-chain.json', 'tests.json', 'provenance.json'})
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
    raise ValueError('JSON非有限数を拒否: ' + value)


def read_text(raw):
    need(type(raw) is bytes and 0 < len(raw) <= MAX_FILE_BYTES and raw.endswith(b'\n') and
         b'\0' not in raw and b'\r' not in raw, '非空UTF-8/LF、NULなし、最大1500000byte')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                      parse_constant=_invalid_constant)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def bindings():
    return {path: identity((ROOT / path).read_bytes()) for path in sorted(SOURCE_CODE)}


def development():
    """独立疎fixtureは現ROM実測ではない。HEADに含まれる全byteを束縛する。"""
    raw = (ROOT / DEV).read_bytes()
    value = read_text(raw)
    proof_raw = (ROOT / DEVELOPMENT_PROOF).read_bytes()
    proof = read_text(proof_raw)
    need(type(value) is dict and value.get('status') == 'PASS_NEW_SYNTHETIC_MINIGAME_DEVELOPMENT' and
         exact(value.get('candidate'), field.CANDIDATE) and
         type(value.get('unit_tests')) is int and value['unit_tests'] > 0 and
         value.get('current_rom_measured') is False and
         exact(value.get('scope_proof_identity'), identity(proof_raw)) and
         proof_raw == chain.canonical(proof), '独立DEVとcanonical proof原本identity')
    chain.validate_restricted_proof(proof)
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
    return dict(
        schema_version=1, status='PASS_CURRENT_ROOTED_MINIGAME_MINIMUM_TYPE',
        measurement_origin='current_run_rom_measurement',
        candidate=copy.deepcopy(field.CANDIDATE), source_head=source_head, run_id=run_id,
        unit_tests=test_count, current_rom_reconstructions=1, current_owner_count=115,
        saved_hit_count=874, classified=782, unclassified=92, newly_classified=1,
        inherited_classified=781, inherited_unclassified=93, all_prior_accepted_retained=True,
        old_scope_test_reruns=0, old_full_rom_scan_runs=0, old_native_cases_replayed=0,
        native_processes=0, donor_safe_bytes=0, formal_rom_changed=False, formal_save_changed=False,
        donor_eligible=False, donor_leased=False, release_ready=False,
        # 内部trace tupleをここだけで正規化し、後段validatorはtupleを拒否する。
        scope_proof=read_text(chain.canonical(proof)), delta_identity=identity(delta_raw),
        development_identity=identity((ROOT / DEV).read_bytes()),
        development_proof_identity=identity((ROOT / DEVELOPMENT_PROOF).read_bytes()),
        source_bindings=copy.deepcopy(expected_bindings), public_source_bindings=field.source_manifest())


def test_summary(test_count):
    need(type(test_count) is int and test_count > 0, '新suite整数件数')
    return dict(status='PASS_NEW_MINIGAME_SCOPE_TESTS', tests=test_count,
                old_scope_test_reruns=0, failures=0, errors=0, skipped=0)


def provenance(report):
    return dict(
        schema_version=1, status='PASS_CURRENT_MINIGAME_TEXT_PROVENANCE',
        current_measurement=dict(source_head=report['source_head'], run_id=report['run_id'],
            candidate=copy.deepcopy(report['candidate']), current_rom_reconstructions=1,
            current_owner_count=115, saved_hit_count=874,
            measurement_canonical_identity=identity(chain.canonical(report)),
            delta_identity=copy.deepcopy(report['delta_identity'])),
        inherited_frontier=dict(classified=781, unclassified=93,
            parent=dict(path=chain.PARENT, **copy.deepcopy(chain.PARENT_ID)),
            checkpoint=dict(path=chain.PARENT_CHECKPOINT, **copy.deepcopy(chain.PARENT_CHECKPOINT_ID)),
            old_scope_test_reruns=0),
        independent_development_fixture=dict(path=DEVELOPMENT_PROOF,
            identity=identity((ROOT / DEVELOPMENT_PROOF).read_bytes()),
            is_current_rom_measurement=False),
        actual_runtime_execution_observed=False, formal_rom_changed=False,
        formal_save_changed=False, donor_eligible=False, donor_leased=False)


def validate_report(report, delta_raw, parent, *, source_head, run_id, expected_bindings, test_count):
    dev = context(source_head, run_id, expected_bindings, test_count)
    need(type(report) is dict and 'scope_proof' in report, '閉report mapping')
    expected = measured_report(report['scope_proof'], delta_raw, source_head=source_head,
                               run_id=run_id, expected_bindings=expected_bindings, test_count=test_count)
    need(exact(report, expected), '型厳密な閉report schema/counter/false/source identity')
    need(exact(identity(chain.canonical(report['scope_proof'])), dev['scope_proof_identity']),
         '現proofは独立fixture全体identityと一致')
    delta = read_text(delta_raw)
    chain.validate(parent, delta)
    need(exact(delta['proof'], report['scope_proof']), 'reportとdeltaは同一scope')
    need(exact([delta['classified'], delta['unclassified'], delta['newly_classified']], [782, 92, 1]),
         '正式781親から4byteの1件だけ')
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
        print(json.dumps(dict(status='GENERATED_MINIGAME_FILE_IDENTITY', file=name,
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
        print(json.dumps(dict(status='PASS_MINIGAME_PUBLIC_FILE', file=name, **value), sort_keys=True),
              file=sys.stdout if log is None else log)
    return identities
