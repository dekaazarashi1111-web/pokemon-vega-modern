#!/usr/bin/env python3
"""Verify immutable fixed-toolchain relearner originals; never run an emulator."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

import run_modernization_p03_relearner_e2e as suite

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = 34446029812
HEAD = '3c894515d6d73a21fde48228853eef38501933ef'
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
DIRECTORY = f'content/modernization/p08_relearner_evidence/{RUN_ID}'
MANIFEST = 'content/modernization/p08_p03_relearner_acceptance.json'
SOURCES = frozenset('''
.github/workflows/p03-relearner-e2e.yml
config/active_play_baseline.json
config/modernization_p03_stage74_supply.json
config/modernization_stage79_cumulative_mgba.json
config/move_memory.json
design/active_play_baseline.md
generated/runtime/modernization_p03_stage73_consumer_runtime_symbols.json
infra/setup_github_actions.sh
infra/toolchain_manifest.json
overlays/modernization_p03_archive_ui_repair/relearner_list.S
overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.c
overlays/move_memory/move_memory.c
scripts/run_modernization_p03_fullslots_e2e.py
scripts/run_modernization_p03_relearner_e2e.py
tests/fixtures/p03_relearner_cases.json
tests/test_modernization_p03_relearner_e2e.py
tools/mgba_ai_fixture_runner.c
tools/mgba_battle_core_smoke.c
tools/mgba_modernization_p02_stage71_acceptance_smoke.c
tools/mgba_modernization_p03_archive_ui_e2e.c
tools/mgba_modernization_p03_fullslots_e2e.c
tools/mgba_modernization_p03_learning_e2e.c
tools/mgba_modernization_p03_relearner_e2e.c
tools/mgba_qol_production_smoke.c
tools/modernization_p03_archive_ui_repair.py
tools/modernization_p03_native_pp_repair.py
'''.split())
require = suite.require
strict_json = suite.previous.strict_json
same = suite.same_typed


def identity(data: bytes) -> dict:
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def archive_members(data: bytes) -> dict[str, bytes]:
    require(0 < len(data) <= 20_000_000, 'archive size outside limit')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            require(len(infos) <= 220, 'too many archive members')
            names = [i.filename for i in infos]
            require(len(set(names)) == len(names), 'duplicate archive member')
            require(sum(i.file_size for i in infos) <= 40_000_000, 'archive expansion limit')
            for i in infos:
                p = PurePosixPath(i.filename)
                require(len(p.parts) == 1 and not p.is_absolute() and '\\' not in i.filename,
                        'unsafe archive path')
                require(p.suffix in {'.log', '.txt', '.json', '.stdout', '.stderr'}, 'unexpected archive payload')
                require(not i.is_dir() and (i.external_attr >> 16) & 0o170000 != 0o120000, 'archive symlink/directory')
            return {i.filename: z.read(i) for i in infos}
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError('invalid evidence archive') from exc


def verify(data: bytes, run: dict, jobs: dict, artifact: dict, root: Path = ROOT) -> dict:
    """Validate original bytes, typed contracts, source closure and Actions identity."""
    for key, expected in {'id': RUN_ID, 'head_sha': HEAD, 'head_branch': BRANCH,
                          'status': 'completed', 'conclusion': 'success', 'event': 'push',
                          'run_attempt': 1, 'path': suite.WORKFLOW}.items():
        require(same(run.get(key), expected), 'Actions run mismatch: ' + key)
    require(run['repository']['full_name'] == REPO and run['head_repository']['full_name'] == REPO,
            'cross-repository evidence forbidden')
    require(run['repository']['id'] == 1358127462 and run['head_repository']['id'] == 1358127462,
            'repository identity changed')
    require(type(artifact['id']) is int and artifact['id'] > 0, 'artifact id required')
    require(artifact['name'] == 'p03-relearner-e2e', 'wrong artifact name')
    require(artifact['digest'] == 'sha256:' + identity(data)['sha256'], 'original archive digest mismatch')
    require(same(artifact['size_in_bytes'], len(data)), 'original archive size mismatch')
    for key, value in {'id': RUN_ID, 'head_sha': HEAD, 'head_branch': BRANCH,
                       'repository_id': 1358127462, 'head_repository_id': 1358127462}.items():
        require(same(artifact['workflow_run'].get(key), value), 'artifact run mismatch: ' + key)
    require(same(jobs.get('total_count'), 1) and len(jobs['jobs']) == 1, 'one complete runtime job required')
    job = jobs['jobs'][0]
    for key, value in {'run_id': RUN_ID, 'head_sha': HEAD, 'name': 'relearner',
                       'status': 'completed', 'conclusion': 'success'}.items():
        require(same(job.get(key), value), 'Actions job mismatch: ' + key)
    required_steps = {'Fixed toolchain', 'Fail-closed regressions',
                      'Fresh UI, PP Ups, gate and cold-save executions', 'Run actions/upload-artifact@v4'}
    require(required_steps <= {s['name'] for s in job['steps']}, 'missing required job step')
    require(all(s['status'] == 'completed' and s['conclusion'] == 'success' for s in job['steps']),
            'failed or skipped Actions step')
    files = archive_members(data)
    cases = suite.vectors()
    prefixes = [c['name'] for c in cases] + ['guard-' + a for a in suite.GUARDS] + ['compile', 'compiler-version', 'fixed-toolchain']
    names = {p + suffix for p in prefixes for suffix in ('.stdout', '.stderr', '.process.json')}
    names |= {'result.json', 'toolchain.log', 'regression.log', 'prepare.log', 'job.stdout.log', 'job.stderr.log', 'tested-head.txt'}
    require(set(files) == names, 'original member set differs')
    require(files['tested-head.txt'].decode().strip() == HEAD, 'original checkout differs')
    report = strict_json(files['result.json'])
    expected = {'schema_version': 1, 'status': 'PASS', 'scope': suite.SCOPE,
                'evidence_kind': 'FIXED_TOOLCHAIN_EXECUTION_NOT_YET_P08_ACCEPTED',
                'candidate_stage': 82, 'candidate_sha256': suite.ROM_SHA, 'mgba_version': '0.10.2',
                'source_mtimes_unchanged': True, 'fresh_successful_mgba_processes': 46,
                'fresh_core_instances': 92, 'cache_reuse': 0, 'product_rom_modified': False,
                'active_baseline_changed': False, 'full_p03_acceptance': False,
                'full_p05_acceptance': False, 'release_ready': False,
                'seed': {'size': 131072, 'sha256': suite.SEED_SHA},
                'fixture_scope': 'species/moves/flags/items configured before observation; no natural acquisition claim'}
    for key, value in expected.items():
        require(same(report.get(key), value), 'original scope/identity mismatch: ' + key)
    require(set(report['source_bindings']) == SOURCES, 'incomplete source closure')
    for path, binding in report['source_bindings'].items():
        p = root / path
        require(not any(q.is_symlink() for q in (p, *p.parents)), 'source symlink forbidden')
        require(same(identity(p.read_bytes()), binding), 'source changed since original run: ' + path)
    compiler = files['compiler-version.stdout'].decode().strip()
    require(report['compiler'] == compiler and compiler.splitlines()[0].endswith(' 13.3.0'), 'GCC 13.3.0 required')
    for prefix in ('compiler-version', 'compile', 'fixed-toolchain'):
        require(suite.previous.require_exited(strict_json(files[prefix + '.process.json'])) == 0, 'toolchain/compile failure')
    require(not files['compile.stderr'] and not files['fixed-toolchain.stderr'], 'unexpected toolchain/compiler diagnostics')
    require(b'Ran 56 tests' in files['regression.log'] and files['regression.log'].rstrip().endswith(b'OK'), 'regression success absent')
    require(type(report['cases']) is list and len(report['cases']) == 46, '46 original cases required')
    for row, case in zip(report['cases'], cases):
        n = case['name']
        require(row['name'] == n and row['status'] == 'PASS', 'case list/order mismatch')
        proc = strict_json(files[n + '.process.json'])
        require(same(proc, row['process']), 'process summary differs from original')
        result = suite.validate_result(files[n + '.stdout'], case, proc, files[n + '.stderr'])
        require(same(result, row['result']), 'result summary differs from original')
        for suffix in ('stdout', 'stderr'):
            require(same(identity(files[n + '.' + suffix]), row[suffix]), 'case output identity changed')
        save = row['private_save_after']
        require(same(save['size'], 131088) and re.fullmatch(r'[0-9a-f]{64}', save['sha256']) is not None, 'save receipt invalid')
    require([r['api'] for r in report['host_write_guard_checks']] == list(suite.GUARDS), 'seven real guards required')
    for row in report['host_write_guard_checks']:
        prefix = 'guard-' + row['api']
        proc = strict_json(files[prefix + '.process.json'])
        require(same(proc, row['process']) and row['status'] == 'REJECTED_EXPECTED', 'guard receipt differs')
        require(suite.previous.require_exited(proc) == 1 and files[prefix + '.stdout'] == b'' and
                files[prefix + '.stderr'] == b'P03 archive: host write after observation barrier\n', 'real write barrier failure')
    require(sorted(files['job.stderr.log'].decode().splitlines()) == sorted('PASS ' + c['name'] for c in cases),
            'runtime driver did not finish all cases cleanly')
    summary = strict_json(files['job.stdout.log'])
    require(same(summary, {k: v for k, v in report.items() if k not in ('cases', 'source_bindings')}), 'driver summary differs')
    return {'schema_version': 1, 'status': 'PASS', 'scope': suite.SCOPE,
            'source_run_id': RUN_ID, 'source_head_sha': HEAD, 'artifact_id': artifact['id'],
            'original_archive': identity(data), 'original_member_count': len(files),
            'evidence_directory': DIRECTORY, 'source_bindings': report['source_bindings'],
            'candidate_stage': 82, 'candidate_rom_sha256': suite.ROM_SHA,
            'accepted_original_processes': 46, 'accepted_original_core_instances': 92,
            'normal_relearner_cases': 17, 'egg_relearner_cases': 29,
            'accepted_case_names': [c['name'] for c in cases], 'original_cache_reuse': 0,
            'new_emulator_runs_during_integration': 0, 'host_write_denial_probes': 7,
            'compiler_first_line': compiler.splitlines()[0], 'mgba_version': '0.10.2',
            'fixture_scope': report['fixture_scope'], 'active_baseline_stage': 62,
            'active_baseline_changed': False, 'product_rom_modified': False,
            'full_p03_acceptance': False, 'full_p05_acceptance': False, 'release_ready': False,
            'remaining_scope': ['other P03 routes and archive economy adoption',
                                'natural acquisition and physical Battle Circus entry',
                                'P06/P07 implementation acceptance tracked separately', 'final release acceptance']}


def build(directory: Path = ROOT / DIRECTORY) -> dict:
    require(not any(p.is_symlink() for p in (directory, *directory.parents)), 'evidence directory symlink')
    names = ('original.zip', 'actions-run.json', 'actions-jobs.json', 'actions-artifact.json')
    blobs = {}
    for name in names:
        p = directory / name
        require(p.is_file() and not p.is_symlink(), 'missing or unsafe evidence: ' + name)
        blobs[name] = p.read_bytes()
    result = verify(blobs['original.zip'], *(strict_json(blobs[n]) for n in names[1:]))
    result['metadata_bindings'] = {n: identity(blobs[n]) for n in names[1:]}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='write the reviewed scoped P08 supplement')
    args = parser.parse_args()
    try:
        result = build()
        p = ROOT / MANIFEST
        if args.write:
            require(not p.exists(), 'refusing to replace existing acceptance')
            p.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
        else:
            require(same(strict_json(p.read_bytes()), result), 'recorded P08 acceptance differs')
        print(json.dumps({'status': 'PASS', 'source_run_id': RUN_ID, 'accepted_original_processes': 46,
                          'new_emulator_runs': 0, 'release_ready': False}, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
