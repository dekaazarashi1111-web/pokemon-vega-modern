#!/usr/bin/env python3
"""失われた公開出力と今回の再計測原本を分離する、閉じた回復専用validator。"""
from __future__ import annotations

import copy
import json
import re
import stat
import sys
from pathlib import Path

import pr16_dex_hof_jp_item_chain as chain
import pr16_dex_hof_jp_item_text as field

ROOT = Path(__file__).resolve().parents[1]
DEV = 'content/modernization/pr16_dex_hof_jp_item_development.json'
DEV_IDENTITY = {'size': 864, 'sha256': 'a61f665cb45c3d9a5722f0d76562531c5caed92ff8c13f788a8224e40125d08f'}
DEVELOPMENT_PROOF = 'content/modernization/pr16_dex_hof_item_recovery_development_proof.json'
SCOPE_PROOF_IDENTITY = {'size': 346822, 'sha256': 'c177bbf108f93787eeffc795a726b8688dd759498423736aefb720cfac386b4a'}
INHERITED_SOURCE_HEAD = 'ea976a497522bbf966d1e0e6ef9f2875d1950d37'
INHERITED_MEASUREMENT_RUN = 37701354400
INHERITED_JOB = 113065287651
INHERITED_TESTS = 165
PRIOR_RECOVERY_HEAD = '7b24518c175583cfb1decc33fc5ab1c12b906762'
PRIOR_RECOVERY_RUN = 37703162164
PRIOR_RECOVERY_JOB = 113071177158
MAX_FILE_BYTES = 1_500_000
FILES = frozenset({'measurement.json', 'reference-chain.json', 'tests.json', 'provenance.json'})
INHERITED_CODE = frozenset({
    'scripts/pr16_dex_hof_jp_item_actions.py', '.github/workflows/pr16-dex-hof-jp-item-text.yml',
    'docs/PR16_DEX_HOF_JP_ITEM_TEXT_JA.md', DEV,
    'content/modernization/pr16_dex_hof_jp_item_sources.json',
    'scripts/pr16_dex_hof_jp_item_roots.py', 'scripts/pr16_dex_hof_jp_item_expand.py',
    'scripts/pr16_dex_hof_jp_item_text.py', 'scripts/pr16_dex_hof_jp_item_chain.py',
    'tests/test_pr16_dex_hof_jp_item_roots.py', 'tests/test_pr16_dex_hof_jp_item_expand.py',
    'tests/test_pr16_dex_hof_jp_item_text.py', 'tests/test_pr16_dex_hof_jp_item_chain.py',
    'tests/test_pr16_dex_hof_jp_item_actions.py',
})
SOURCE_CODE = INHERITED_CODE | frozenset({
    'scripts/pr16_dex_hof_item_recovery_actions.py',
    'scripts/pr16_dex_hof_item_recovery_validation.py',
    'tests/test_pr16_dex_hof_item_recovery_validation.py',
    '.github/workflows/pr16-dex-hof-item-recovery.yml',
    'docs/PR16_DEX_HOF_ITEM_RECOVERY_JA.md', DEVELOPMENT_PROOF,
})
need, identity = field.need, field.identity


def exact(left, right):
    """JSON型まで一致させ、bool/int・int/float・tuple/list別名を拒否する。"""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (all(type(key) is str for key in left) and set(left) == set(right) and
                all(exact(left[key], right[key]) for key in left))
    if type(left) is list:
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return type(left) in (str, int, bool, type(None)) and left == right


def _valid_identity(value):
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
    """公開各fileの上限はinclusive 1.5 MB。旧750 kB境界を使わない。"""
    need(type(raw) is bytes and 0 < len(raw) <= MAX_FILE_BYTES and raw.endswith(b'\n') and
         b'\0' not in raw and b'\r' not in raw, '非空UTF-8/LF、NULなし、最大1500000byte')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique_object,
                      parse_constant=_invalid_constant)


def _development():
    raw = (ROOT / DEV).read_bytes()
    need(exact(identity(raw), DEV_IDENTITY), '独立開発原本の全byte identityは固定')
    value = read_text(raw)
    need(value['status'] == 'PASS_NEW_SYNTHETIC_ITEM_DEVELOPMENT' and
         exact(value['candidate'], field.CANDIDATE) and
         exact(value['scope_proof_identity'], SCOPE_PROOF_IDENTITY) and
         type(value['unit_tests']) is int and value['unit_tests'] == INHERITED_TESTS and
         value['current_rom_measured'] is False, '独立fixtureは失われた実測原本ではない')
    return value


def _context(source_head, run_id, expected_bindings, recovery_test_count):
    need(type(source_head) is str and re.fullmatch(r'[0-9a-f]{40}', source_head) is not None and
         source_head not in (INHERITED_SOURCE_HEAD, PRIOR_RECOVERY_HEAD), '回復実行の新source HEAD')
    need(type(run_id) is int and run_id > 0 and run_id not in (INHERITED_MEASUREMENT_RUN, PRIOR_RECOVERY_RUN),
         '元failureとは別の新回復run')
    need(type(recovery_test_count) is int and recovery_test_count > 0,
         '新回復suiteの実試験数だけ')
    need(type(expected_bindings) is dict and set(expected_bindings) == SOURCE_CODE and
         all(type(path) is str and _valid_identity(value) for path, value in expected_bindings.items()),
         '凍結14sourceと新回復6sourceだけの厳密な期待binding')
    need(exact(expected_bindings[DEV], DEV_IDENTITY) and
         exact(expected_bindings[DEVELOPMENT_PROOF], SCOPE_PROOF_IDENTITY),
         '開発原本と独立proof fixtureの固定identityをsource bindingにも結ぶ')


def measured_report(proof, delta_raw, *, source_head, run_id, expected_bindings, recovery_test_count):
    """計測器が現在ROMから得たproofを入れる。旧Actions reportのschemaを再利用しない。"""
    _context(source_head, run_id, expected_bindings, recovery_test_count)
    return dict(
        schema_version=1, status='PASS_CURRENT_JP_ITEM_TEXT_RECOVERY',
        measurement_origin='current_recovery_run_rom_remeasurement',
        candidate=copy.deepcopy(field.CANDIDATE), source_head=source_head, run_id=run_id,
        recovery_test_count=recovery_test_count, inherited_scope_tests=INHERITED_TESTS,
        inherited_measurement_run=INHERITED_MEASUREMENT_RUN, inherited_source_head=INHERITED_SOURCE_HEAD,
        current_rom_reconstructions=1, cumulative_scope_rom_reconstructions=3,
        consumer_remeasurements=2, current_owner_count=115,
        classified=781, unclassified=93, newly_classified=1,
        inherited_classified=780, inherited_unclassified=94,
        formal_classified_before_recovery=780, formal_unclassified_before_recovery=94,
        all_prior_accepted_retained=True, old_scope_test_reruns=0,
        old_full_rom_scan_runs=0, old_native_cases_replayed=0, native_processes=0,
        donor_safe_bytes=0, formal_rom_changed=False, formal_save_changed=False,
        donor_eligible=False, donor_leased=False, original_failed_run_rewritten=False,
        reconstructed_text_promoted_as_original=False,
        # 内部producerのtrace tupleを公開JSON型へ一度だけ正規化する。
        # validatorのexactはtupleを許容しない。
        scope_proof=read_text(chain.canonical(proof)), delta_identity=identity(delta_raw),
        development_identity=copy.deepcopy(DEV_IDENTITY),
        source_bindings=copy.deepcopy(expected_bindings), public_source_bindings=field.source_manifest())


def test_summary(recovery_test_count):
    need(type(recovery_test_count) is int and recovery_test_count > 0, '新suite整数件数')
    return dict(status='PASS_NEW_JP_ITEM_RECOVERY_TESTS', recovery_test_count=recovery_test_count,
                inherited_scope_tests=INHERITED_TESTS, old_scope_test_reruns=0,
                failures=0, errors=0, skipped=0)


def provenance(report, *, inherited_log_identity, prior_recovery_log_identity):
    """元failure/継承試験/新原本の由来を分離し、失われたhashを創作しない。"""
    need(_valid_identity(inherited_log_identity), '元job全logの実取得identity')
    need(_valid_identity(prior_recovery_log_identity), '失敗回復job全logの実取得identity')
    return dict(
        schema_version=1, status='PASS_CURRENT_JP_ITEM_RECOVERY_PROVENANCE',
        original_failed_run=dict(
            source_head=INHERITED_SOURCE_HEAD, run_id=INHERITED_MEASUREMENT_RUN,
            job_id=INHERITED_JOB, run_conclusion='failure', measurement_step_outcome='success',
            export_step_outcome='failure', artifact_count=0, scope_tests=INHERITED_TESTS,
            old_export_max_bytes=750000, original_output_size_logged=False,
            original_output_hashes_available=False, job_log_identity=copy.deepcopy(inherited_log_identity)),
        prior_failed_recovery=dict(
            source_head=PRIOR_RECOVERY_HEAD, run_id=PRIOR_RECOVERY_RUN, job_id=PRIOR_RECOVERY_JOB,
            run_conclusion='failure', measurement_step='failure', original_artifact_missing=True,
            error_stage='prepublication_report_type_validation', current_rom_reconstructions=1,
            old_scope_test_reruns=0, job_log_identity=copy.deepcopy(prior_recovery_log_identity),
            stage_evidence='public_exception_source_frames_and_fixed_runner_control_flow',
            successful_measurement_claimed=False, scope_proof_original_available=False),
        inherited_scope=dict(tests=INHERITED_TESTS, reruns=0, source_head=INHERITED_SOURCE_HEAD,
                             run_id=INHERITED_MEASUREMENT_RUN, source_files_unchanged=14,
                             basis='unchanged_sources_and_original_success_step_and_job_log'),
        current_remeasurement=dict(
            source_head=report['source_head'], run_id=report['run_id'],
            candidate=copy.deepcopy(report['candidate']), current_rom_reconstructions=1,
            cumulative_scope_rom_reconstructions=3,
            consumer_remeasurements=2, measurement_canonical_identity=identity(chain.canonical(report)),
            delta_identity=copy.deepcopy(report['delta_identity']),
            origin='new_current_rom_measurement_not_recovered_original_output'),
        independent_development_fixture=dict(path=DEVELOPMENT_PROOF,
                                              identity=copy.deepcopy(SCOPE_PROOF_IDENTITY),
                                              is_current_rom_measurement=False,
                                              is_lost_output_original=False,
                                              reconstructed_measurement_size=770711,
                                              original_size_logged=False),
        original_failed_run_rewritten=False, reconstructed_text_is_original=False,
        reconstructed_text_used_as_current_rom_measurement=False)


def validate_report(report, delta_raw, parent, *, source_head, run_id,
                    expected_bindings, recovery_test_count):
    _context(source_head, run_id, expected_bindings, recovery_test_count)
    development = _development()
    need(type(report) is dict and 'scope_proof' in report, '回復専用report mapping')
    expected = measured_report(report['scope_proof'], delta_raw, source_head=source_head,
                               run_id=run_id, expected_bindings=expected_bindings,
                               recovery_test_count=recovery_test_count)
    need(exact(report, expected), '型厳密な閉report schema/counter/false/source identity')
    need(exact(identity(chain.canonical(report['scope_proof'])), development['scope_proof_identity']),
         'scope proof全体は固定独立DEV identityと一致')
    delta = read_text(delta_raw)
    chain.validate(parent, delta)
    need(exact(delta['proof'], report['scope_proof']), 'reportとchainの同一proof')
    need(exact([delta['classified'], delta['unclassified'], delta['newly_classified']], [781, 93, 1]),
         '正式780親から最小4byteの1件だけ')
    return True


def validate_output(directory, parent, *, source_head, run_id, expected_bindings,
                    recovery_test_count, inherited_log_identity, prior_recovery_log_identity, log=None):
    """4textだけを全て検証してから、公開前に全fileのbyte identityをlogへ出す。"""
    directory = Path(directory)
    need(not any(path.is_symlink() for path in (directory, *directory.parents)) and directory.is_dir(),
         '公開directoryと全親pathのsymlinkを拒否')
    need({path.name for path in directory.iterdir()} == FILES, '余剰・欠落・subdirなしの閉4text')
    raw_files, values = {}, {}
    for name in sorted(FILES):
        path = directory / name
        need(not path.is_symlink() and stat.S_ISREG(path.stat().st_mode), '公開fileはregular textのみ')
        need(0 < path.stat().st_size <= MAX_FILE_BYTES, '読取前に各fileの1500000byte上限')
        raw_files[name] = path.read_bytes()
        values[name] = read_text(raw_files[name])
    report = values['measurement.json']
    validate_report(report, raw_files['reference-chain.json'], parent, source_head=source_head,
                    run_id=run_id, expected_bindings=expected_bindings,
                    recovery_test_count=recovery_test_count)
    need(exact(values['tests.json'], test_summary(recovery_test_count)), '閉じた新suite試験summary')
    need(exact(values['provenance.json'], provenance(report, inherited_log_identity=inherited_log_identity,
                                                        prior_recovery_log_identity=prior_recovery_log_identity)),
         '元failure/165継承/今回新原本を厳密に分離した由来')
    identities = {name: identity(raw_files[name]) for name in sorted(FILES)}
    for name, value in identities.items():
        print(json.dumps(dict(status='PASS_JP_ITEM_RECOVERY_PUBLIC_FILE', file=name, **value),
                         sort_keys=True), file=sys.stdout if log is None else log)
    return identities
