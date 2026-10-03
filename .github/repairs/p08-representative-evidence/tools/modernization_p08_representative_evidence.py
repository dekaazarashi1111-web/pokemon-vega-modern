"""Verify immutable P03/P05 representative E2E originals without promoting phases.

Archive pins identify three existing fresh-run suites. Reading them is not a new
mGBA execution. Stage79/historical evidence remains a separate, unchanged layer.
"""
from __future__ import annotations

import io
from pathlib import Path
import stat
from typing import Any
import zipfile

from scripts import run_modernization_p03_learning_e2e as learning
from scripts import run_modernization_p05_scheduler_e2e as scheduler
from scripts import run_modernization_p05_controller_witness as witness
from tools import modernization_p08_stage79_evidence as base

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'config/modernization_p08_representative_evidence.json'
DIRECTORY = 'content/modernization/p08_representative_evidence'
KEYS = {'current_representative_e2e', 'representative_evidence_binding'}
ROM = 'build/stages/80_modernization_runtime_boundary_repair.gba'
SEED = '.local/60_wild_species_root_repair.srm'
TOOLCHAIN = ('infra/setup_github_actions.sh', 'infra/toolchain_manifest.json')
SUITES = {
    'p03_learning': {
        'run_id': 34347153852, 'head_sha': 'fdac91af6288953e740d4ceb5bc2cc25e3690cf7',
        'artifact_id': 10102197760, 'artifact_name': 'p03-learning-e2e',
        'zip_sha256': '87b95f9b6fb518f1f41d07001d5e8638b9147c029e26120b3344a63fa08355d9',
        'result_sha256': '96f691f9284918e085a6fa0d096cf1b728f7d76637c612dc4369f99cd4a3ba57',
        'job_id': 102451363915, 'job_name': 'learning-save-reload',
        'steps': ['固定mGBA toolchain', '結果契約の回帰検証', '新規2 processで通常習得・保存・Continueを実行'],
        'count': 2, 'scope': learning.SCOPE,
    },
    'p05_scheduler': {
        'run_id': 34351006779, 'head_sha': '14a61c80b69d2adb2f9f9adf513fd143d86b8728',
        'artifact_id': 10103780162, 'artifact_name': 'p05-scheduler-e2e',
        'zip_sha256': '5f0f90fd30eeda524c4449c4a995d04fa520f0f0bf954dce8e9aa6b9eae0fe54',
        'result_sha256': '69ca747203911a0eba2f8493054c2c2cb37647beb0ab404fbdfce3d3462d0ad1',
        'job_id': 102463985972, 'job_name': 'six-abilities-first-turn',
        'steps': ['Fixed emulator toolchain', 'Result and execution regression tests', 'Fresh 24-process scheduler matrix and seven write guards'],
        'count': 24, 'scope': scheduler.SCOPE,
    },
    'p05_controller': {
        'run_id': 34354997505, 'head_sha': 'faeca48f4e29f2c61083d79dbd19f87053914db3',
        'artifact_id': 10105374554, 'artifact_name': 'p05-controller-witness',
        'zip_sha256': '1024340a3d3a9d1c1502594b2c4cf94d8903e5a4ae8b4c6aa0c7c79c8b4dac63',
        'result_sha256': 'c900416ac43c3f287ab8ded23a33a225039af4a003d7e18625b19425a5f834d9',
        'job_id': 102477295025, 'job_name': 'dragonize-controller-turn',
        'steps': ['固定mGBA toolchain', '受動observer・結果契約・失敗時保存の回帰検証', '同一Stage80で新規4 processを実行'],
        'count': 4, 'scope': witness.SCOPE,
    },
}


def identity(raw: bytes) -> dict[str, Any]:
    return {'size': len(raw), 'sha256': base.sha(raw)}


def exact(actual: Any, expected: Any, label: str) -> None:
    # JSON comparison preserves boolean-vs-integer distinctions recursively.
    base.require(base.stable(actual) == base.stable(expected), label)


def labels(suite: str) -> list[str]:
    if suite == 'p03_learning':
        return ['learn', 'below-level']
    if suite == 'p05_scheduler':
        return [f'{case}--{mode}' for case, mode in scheduler.PAIRS]
    if suite == 'p05_controller':
        return list(witness.CASES)
    raise base.EvidenceError('unregistered representative suite')


def archive_members(suite: str) -> set[str]:
    names = {'result.json', 'tested-head.txt', 'compile.stdout', 'compile.stderr',
             'job.stdout.json', 'job.stderr.log'}
    names.update(f'{label}.{stream}' for label in labels(suite) for stream in ('stdout', 'stderr'))
    if suite == 'p05_scheduler':
        names.update(f'guard-{guard}.{stream}' for guard in scheduler.GUARDS for stream in ('stdout', 'stderr'))
    if suite == 'p05_controller':
        names.update(f'{label}.process.json' for label in ['compile', *labels(suite)])
    return names


def unpack(raw: bytes, suite: str) -> dict[str, bytes]:
    pin = SUITES[suite]
    base.require(base.sha(raw) == pin['zip_sha256'], f'{suite}: original ZIP digest')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        base.require(len(names) == len(set(names)) and set(names) == archive_members(suite),
                     f'{suite}: complete unique archive member set')
        for item in archive.infolist():
            base.require(not item.is_dir() and not stat.S_ISLNK(item.external_attr >> 16)
                         and item.file_size < 1_000_000, f'{suite}: unsafe archive member')
        return {name: archive.read(name) for name in sorted(names)}


def validate_payload(files: dict[str, bytes], suite: str) -> dict[str, Any]:
    """Contract checks also run after ZIP and per-file identity verification."""
    pin = SUITES[suite]
    exact(sorted(files), sorted(archive_members(suite)), 'payload member set')
    exact(files['tested-head.txt'].decode('ascii'), pin['head_sha'] + '\n', 'tested HEAD')
    report = witness.strict_json(files['result.json'])
    exact(witness.strict_json(files['job.stdout.json']), report, 'job/result JSON disagreement')
    for name in ('compile.stdout', 'compile.stderr', 'job.stderr.log'):
        base.require(files[name] == b'', f'{suite}: unexpected {name}')
    for key, value in dict(schema_version=1, status='PASS', scope=pin['scope'],
                           fresh_process_runs=pin['count'], cached_results_reused=0,
                           release_ready=False, active_baseline_changed=False).items():
        exact(report.get(key), value, f'{suite}: {key}')
    exact(report.get('rom'), witness.ROM_ID, 'candidate ROM identity')
    if suite != 'p05_controller':
        exact(report.get('seed'), {'size': 131072, 'sha256': scheduler.SEED_SHA}, 'private seed identity')
    for key in ('full_p03_acceptance', 'full_p05_acceptance', 'breeding_e2e',
                'natural_ability_acquisition_e2e', 'natural_battle_circus_entry_e2e'):
        if key in report:
            exact(report[key], False, f'unsupported broad claim: {key}')
    rows = report['cases']
    names = [row['mode'] if suite == 'p03_learning' else
             row['case'] + '--' + row['mode'] if suite == 'p05_scheduler' else row['case'] for row in rows]
    exact(names, labels(suite), 'complete unique ordered case set')
    parsed = []
    for label, row in zip(names, rows):
        exact(row.get('returncode'), 0, 'strict integer process exit')
        raw = files[label + '.stdout']
        witness.strict_json(raw)
        if suite == 'p03_learning':
            result = learning.validate_result(raw, row['mode'], row['returncode'])
        elif suite == 'p05_scheduler':
            result = scheduler.validate_result(raw, row['case'], row['mode'], row['returncode'])
        else:
            result = witness.validate_result(raw, row['case'], row['returncode'])
            process = witness.strict_json(files[label + '.process.json'])
            exact(process.get('returncode'), 0, 'actual process exit')
            exact(process.get('timed_out'), False, 'actual process timeout')
            base.require(set(process) == {'command', 'returncode', 'timed_out'}, 'process launch error')
            command = process['command']
            base.require(isinstance(command, list) and len(command) == 4
                         and command[2:] == [witness.ROM_ID['sha256'], label], 'case command binding')
        exact(result, row['runner_result'], 'raw/result disagreement')
        for stream in ('stdout', 'stderr'):
            exact(identity(files[f'{label}.{stream}']), row[stream], 'raw stream binding')
        parsed.append(result)
    if suite == 'p05_scheduler':
        scheduler.validate_matrix(parsed)
        exact(report['write_guard_negative_checks'], list(scheduler.GUARDS), 'write guard set')
        for guard in scheduler.GUARDS:
            base.require(files[f'guard-{guard}.stdout'] == b'' and
                         files[f'guard-{guard}.stderr'] == b'P05 scheduler: host write after fixture barrier\n',
                         'negative host-write guard original')
    if suite == 'p05_controller':
        compile_process = witness.strict_json(files['compile.process.json'])
        exact(compile_process.get('returncode'), 0, 'compiler exit')
        exact(compile_process.get('timed_out'), False, 'compiler timeout')
        base.require(set(compile_process) == {'command', 'returncode', 'timed_out'}, 'compiler launch error')
        command = compile_process['command']
        base.require(command[:8] == ['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Itools', witness.SOURCE]
                     and command[8:10] == ['-lmgba', '-o'] and len(command) == 11, 'strict compiler command')
        for label in names:
            exact(witness.strict_json(files[label + '.process.json'])['command'][0], command[-1], 'compiled executable')
    return report


def workflow_path(suite: str) -> str:
    return '.github/workflows/' + SUITES[suite]['artifact_name'] + '.yml'


def validate_actions(actions: dict[str, Any], suite: str) -> None:
    pin = SUITES[suite]
    expected = {
        'repository': base.REPOSITORY, 'head_branch': base.BRANCH,
        'run_id': pin['run_id'], 'run_attempt': 1, 'head_sha': pin['head_sha'],
        'workflow_path': workflow_path(suite), 'status': 'completed', 'conclusion': 'success',
        'artifact_id': pin['artifact_id'], 'artifact_name': pin['artifact_name'],
        'artifact_digest': 'sha256:' + pin['zip_sha256'], 'artifact_run_id': pin['run_id'],
        'artifact_head_sha': pin['head_sha'], 'job_id': pin['job_id'], 'job_name': pin['job_name'],
        'job_status': 'completed', 'job_conclusion': 'success',
    }
    for key, value in expected.items():
        exact(actions.get(key), value, f'{suite}: Actions provenance {key}')
    steps = actions['required_steps']
    exact([step['name'] for step in steps], pin['steps'], 'required workflow step set')
    for step in steps:
        exact(step, {'name': step['name'], 'status': 'completed', 'conclusion': 'success'}, 'required step did not succeed')
    exact(sorted(actions['verified_execution_sources']), sorted([workflow_path(suite), *TOOLCHAIN]),
          'workflow/toolchain provenance set')


def build_extension(root: Path = ROOT) -> dict[str, Any]:
    sources: dict[str, Any] = {}
    def read(path: str, expected: dict | None = None) -> bytes:
        raw = base.regular(root, path)
        if expected is not None:
            exact(identity(raw), expected, f'file identity: {path}')
        sources[path] = identity(raw)
        return raw
    config = witness.strict_json(read(CONFIG))
    exact(config.get('schema_version'), 1, 'representative registration schema')
    exact(sorted(config['suites']), sorted(SUITES), 'registered suites')
    read(ROM, witness.ROM_ID)
    read(SEED, {'size': 131072, 'sha256': scheduler.SEED_SHA})
    summaries = []
    for suite, pin in SUITES.items():
        record = config['suites'][suite]
        directory = f'{DIRECTORY}/{suite}/{pin["run_id"]}'
        exact(record['directory'], directory, 'registered evidence directory')
        payload = unpack(read(directory + '/source.zip'), suite)
        exact(base.sha(payload['result.json']), pin['result_sha256'], 'immutable result digest')
        exact(sorted(record['files']), sorted(set(payload) | {'actions.json', 'source.zip'}), 'registered file coverage')
        for name, expected in record['files'].items():
            raw = read(directory + '/' + name, expected)
            if name in payload:
                base.require(raw == payload[name], f'original archive member drift: {suite}/{name}')
        actions = witness.strict_json(base.regular(root, directory + '/actions.json'))
        validate_actions(actions, suite)
        report = validate_payload(payload, suite)
        for path, expected in report['source_bindings'].items():
            read(path, expected)
        for path, expected in actions['verified_execution_sources'].items():
            read(path, expected)
        summaries.append({
            'id': suite, 'scope': pin['scope'], 'status': 'PASS', 'run_id': pin['run_id'],
            'head_sha': pin['head_sha'], 'artifact_id': pin['artifact_id'],
            'original_zip_sha256': pin['zip_sha256'], 'result_path': directory + '/result.json',
            'result_sha256': pin['result_sha256'], 'retained_original_fresh_process_runs': pin['count'],
            'original_cached_results_reused': 0,
        })
    return {
        'schema_version': 1, 'status': 'PASS', 'scope': 'REPRESENTATIVE_E2E_ONLY_NOT_PHASE_ACCEPTANCE',
        'candidate_rom': dict(path=ROM, **witness.ROM_ID), 'suites': summaries,
        'retained_original_fresh_process_runs': sum(row['count'] for row in SUITES.values()),
        'fresh_process_runs_this_validation': 0, 'heavy_execution_performed': False,
        'representative_coverage': {'p03_normal_learning_and_fresh_core_reload': True,
                                    'p05_six_abilities_turn_matrix': True,
                                    'p05_dragonize_controller_turn_witness': True},
        'unclaimed_coverage': {'p03_all_learning_routes': False, 'p03_breeding_e2e': False,
                               'p05_natural_ability_acquisition_e2e': False,
                               'p05_natural_battle_circus_entry_e2e': False,
                               'full_p03_acceptance': False, 'full_p05_acceptance': False,
                               'release_ready': False},
        'phase_completion_promoted': False, 'active_baseline_changed': False,
        'source_bindings': sources,
    }


def attach_outputs(outputs: dict[str, bytes], root: Path = ROOT) -> dict[str, bytes]:
    # Historical build fixtures have no registration. Current acceptance requires it.
    if not (root / CONFIG).exists():
        return outputs
    extension = build_extension(root)
    result = {}
    for path, raw in outputs.items():
        document = witness.strict_json(raw)
        original = {key: value for key, value in document.items() if key not in KEYS}
        base.require(original.get('release_ready') is False and 'current_cumulative_runtime' in original,
                     'representative evidence requires existing Stage79 layer')
        binding = {'stage79_document_sha256': base.sha(base.stable(original)),
                   'extension_sha256': base.sha(base.stable(extension))}
        result[path] = base.stable(dict(original, current_representative_e2e=extension,
                                       representative_evidence_binding=binding))
    return result


def validate_document(document: dict[str, Any], extension: dict[str, Any]) -> None:
    original = {key: value for key, value in document.items() if key not in KEYS}
    exact(document.get('current_representative_e2e'), extension, 'stale representative evidence layer')
    exact(document.get('representative_evidence_binding'),
          {'stage79_document_sha256': base.sha(base.stable(original)),
           'extension_sha256': base.sha(base.stable(extension))}, 'representative evidence binding')
