#!/usr/bin/env python3
"""Verify, or explicitly import, fixed native Mega lifecycle originals.

Checks never modify files or promote a release. Import copies only the pinned
ZIP and normalized Actions identities, then writes a scoped P08 supplement.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_modernization_p05_mega_lifecycle_e2e as runtime

REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
RUN = 34438575892
HEAD = '96c634134730f0c4f5aed989e7a4ed6b23c2c6d6'
JOB = 102748670155
ARTIFACT = 10137176189
ZIP_SIZE = 162216
ZIP_SHA = 'b1166c0d8cbd40487b300a3814851ad4e64fdb3fc190082df525f6241be37fe8'
WORKFLOW = '.github/workflows/p05-mega-lifecycle-e2e.yml'
TEST = 'tests/test_modernization_p05_mega_lifecycle_e2e.py'
DIRECTORY = f'content/modernization/p08_native_mega_evidence/{RUN}'
REPORT = 'content/modernization/p08_native_mega_acceptance.json'
STEPS = ('Fixed compiler and emulator', 'Regression contracts and exact candidate',
         'Fresh 42 processes and 48 cores without PASS cache', 'Preserve exact source and workflow',
         'Run actions/upload-artifact@v4')
need = runtime.need


def stable(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()


def load(raw):
    return json.loads(raw, object_pairs_hook=runtime.no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def regular(root, name):
    path = PurePosixPath(name)
    need(not path.is_absolute() and str(path) == name and '..' not in path.parts, 'unsafe relative path')
    current = root
    for part in path.parts:
        current = current / part
        need(not current.is_symlink(), 'symlink input: ' + name)
    need(current.is_file(), 'missing regular file: ' + name)
    return current.read_bytes()


def strict_subset(obj, expected, where):
    for key, value in expected.items():
        need(key in obj and type(obj[key]) is type(value) and obj[key] == value, where + ': ' + key)


def normalize_actions(run, job, artifact):
    return dict(repository=run['head_repository']['full_name'], head_branch=run['head_branch'],
                run_id=run['id'], run_attempt=run['run_attempt'], head_sha=run['head_sha'],
                workflow_path=run['path'], status=run['status'], conclusion=run['conclusion'],
                job_id=job['id'], job_run_id=job['run_id'], job_name=job['name'],
                job_status=job['status'], job_conclusion=job['conclusion'],
                artifact_id=artifact['id'], artifact_name=artifact['name'],
                artifact_digest=artifact['digest'], artifact_size=artifact['size_in_bytes'],
                artifact_run_id=artifact['workflow_run']['id'], artifact_head_sha=artifact['workflow_run']['head_sha'],
                steps=[{k: x[k] for k in ('name', 'status', 'conclusion')} for x in job['steps'] if x['name'] in STEPS])


def validate_actions(actions):
    expected = dict(repository=REPO, head_branch=BRANCH, run_id=RUN, run_attempt=1, head_sha=HEAD,
                    workflow_path=WORKFLOW, status='completed', conclusion='success', job_id=JOB,
                    job_run_id=RUN, job_name='native-mega-turn-revert-cold-save', job_status='completed',
                    job_conclusion='success', artifact_id=ARTIFACT, artifact_name='p05-native-mega-lifecycle',
                    artifact_digest='sha256:' + ZIP_SHA, artifact_size=ZIP_SIZE, artifact_run_id=RUN,
                    artifact_head_sha=HEAD)
    need(type(actions) is dict and set(actions) == set(expected) | {'steps'}, 'Actions schema')
    strict_subset(actions, expected, 'Actions identity')
    need(actions['steps'] == [dict(name=n, status='completed', conclusion='success') for n in STEPS], 'original required steps')


def unpack(raw):
    need(identity(raw) == dict(size=ZIP_SIZE, sha256=ZIP_SHA), 'pinned original ZIP differs')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        need(len(names) == len(set(names)), 'duplicate ZIP member')
        need(sum(i.file_size for i in infos) <= 8_000_000, 'oversized ZIP')
        for entry in infos:
            p = PurePosixPath(entry.filename)
            need(not entry.is_dir() and str(p) == entry.filename and not p.is_absolute() and '..' not in p.parts, 'unsafe ZIP entry')
            need((entry.external_attr >> 16) & 0o170000 != 0o120000, 'symlink ZIP entry')
        return {i.filename: archive.read(i) for i in infos}


def validate_payload(files, root=ROOT):
    need(files['native-exit-code.txt'] == b'0\n', 'native process exit')
    need(files['tested-head.txt'] == (HEAD + '\n').encode(), 'tested source HEAD')
    need(files['compile.stderr'] == b'' and files['job.stderr.log'] == b'', 'compile/wrapper stderr')
    need(b'Ran 52 tests in ' in files['unittest.stderr'] and files['unittest.stderr'].endswith(b'\nOK\n'), 'regression tests')
    for text in (b'[OK] host_cc: 13.3.0', b'[OK] mgba: 0.10.2', b'GitHub Actions toolchain: PASS'):
        need(text in files['fixed-toolchain.log'], 'fixed toolchain identity')
    need(b'13.3.0' in files['toolchain.stdout'], 'actual runner compiler')
    summary = load(files['result.json'])
    expected = dict(schema_version=1, status='PASS', scope=runtime.SCOPE, candidate_stage=82,
                    rom_sha256=runtime.ROM_SHA, seed_sha256=runtime.SEED_SHA, fresh_process_runs=42,
                    core_instances=48, cache_reuse=0, active_mega_cold_save_cases=6, nonactivation_controls=36,
                    natural_capture_or_facility_entry=False, full_p05_acceptance=False, release_ready=False)
    need(type(summary) is dict and set(summary) == set(expected) | {'cases', 'source_bindings', 'host_write_guards'}, 'summary schema')
    strict_subset(summary, expected, 'summary')
    need(summary['host_write_guards'] == list(runtime.GUARDS), 'guard coverage')
    need(stable(load(files['job.stdout.json'])) == stable(summary), 'job/result mismatch')
    rows = []
    for case, mode in runtime.PAIRS:
        rows.append(runtime.validate_case(files[f'{case}--{mode}.stdout'], case, mode, 0))
        need(len(files[f'{case}--{mode}.stderr']) > 0, 'native diagnostics missing')
    runtime.validate_matrix(rows)
    need(stable(rows) == stable(summary['cases']), 'original/result cases mismatch')
    for guard in runtime.GUARDS:
        need(files['guard-' + guard + '.stdout'] == b'' and files['guard-' + guard + '.stderr'] ==
             b'P05 scheduler: host write after fixture barrier\n', 'guard negative output')
    sources = load(files['source-archive.json'])
    need(set(sources) == set(summary['source_bindings']) | {TEST, WORKFLOW}, 'source archive coverage')
    for name, binding in sources.items():
        archived = files['sources/' + name]
        need(identity(archived) == binding, 'archived source hash: ' + name)
        need(regular(root, name) == archived, 'live source differs: ' + name)
        if name in summary['source_bindings']:
            need(summary['source_bindings'][name] == binding, 'runtime/archive binding: ' + name)
    return summary


def build_report(raw, actions, root=ROOT):
    validate_actions(actions)
    summary = validate_payload(unpack(raw), root)
    return dict(schema_version=1, status='PASS', scope=runtime.SCOPE, source_run_id=RUN, source_head_sha=HEAD,
                candidate_stage=82, candidate_rom_sha256=runtime.ROM_SHA, original_archive=identity(raw),
                actions_sha256=identity(stable(actions))['sha256'], evidence_directory=DIRECTORY,
                accepted_original_processes=42, accepted_original_core_instances=48,
                original_cache_reuse=0, new_emulator_runs_during_integration=0,
                native_mega_turn_revert_cold_save_cases=list(runtime.CASES),
                nonactivation_controls_per_species=list(runtime.MODES[1:]),
                closed_scope=['six_native_mega_ability_assignments', 'six_native_revert_save_cold_continue_lifecycles',
                              '36_nonactivation_controls'], source_bindings=summary['source_bindings'],
                remaining_scope=['natural_capture_and_gear_acquisition', 'physical_battle_circus_admission',
                                 'other_P03_and_P05_acceptance_paths', 'P06_P07_adopted_implementation', 'final_release_acceptance'],
                fixture_scope='pre-input species/gear/policy/opponent; no host writes during observation',
                limits=['base Eelektross already has Levitate', 'native Mega also changes stats; Fire Mane contrast is not ability-only'],
                active_baseline_stage=62, active_baseline_changed=False, full_p05_acceptance=False, release_ready=False)


def check(root=ROOT):
    raw = regular(root, DIRECTORY + '/original.zip')
    actions = load(regular(root, DIRECTORY + '/actions.json'))
    report = build_report(raw, actions, root)
    need(regular(root, REPORT) == stable(report), 'P08 report differs from verified original')
    return report


def import_evidence(raw, actions, root=ROOT):
    report = build_report(raw, actions, root)
    for name, data in ((DIRECTORY + '/original.zip', raw), (DIRECTORY + '/actions.json', stable(actions)), (REPORT, stable(report))):
        target = root
        for part in PurePosixPath(name).parts[:-1]:
            target /= part
            need(not target.is_symlink(), 'symlink destination')
            target.mkdir(exist_ok=True)
        target /= PurePosixPath(name).name
        need(not target.exists() and not target.is_symlink(), 'refuse existing evidence overwrite')
    (root / DIRECTORY / 'original.zip').write_bytes(raw)
    (root / DIRECTORY / 'actions.json').write_bytes(stable(actions))
    (root / REPORT).write_bytes(stable(report))
    return check(root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-archive', type=Path)
    parser.add_argument('--actions', type=Path)
    args = parser.parse_args(argv)
    if bool(args.import_archive) != bool(args.actions):
        parser.error('import requires both --import-archive and --actions')
    report = import_evidence(args.import_archive.read_bytes(), load(args.actions.read_bytes())) if args.import_archive else check()
    print(json.dumps({'status': report['status'], 'original_processes': 42, 'new_emulator_runs': 0,
                      'native_cold_save_cases': 6, 'release_ready': False}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
