#!/usr/bin/env python3
"""Verify and retain the original fixed-toolchain P03 capacity run, without replay."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import urllib.request
import zipfile
import run_modernization_p03_breeding_capacity_e2e as suite

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
RUN = 34439826111
HEAD = '40dec97d5360422e66d02a3ae0261a00df566f86'
EVIDENCE = f'content/modernization/p08_breeding_capacity_evidence/{RUN}'
RECORD = 'content/modernization/p08_p03_breeding_capacity_acceptance.json'
ARTIFACT = 'p03-breeding-capacity-e2e'
STEPS = ('Install and verify fixed native toolchain',
         'Reject false positives and actual host-write attempts',
         'Rebuild unchanged Stage82 and run three fresh capacity cases',
         'Run actions/upload-artifact@v4')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def same(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in b)
    if isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def relative(name):
    require(type(name) is str and name and '\\' not in name, 'invalid evidence path')
    p = PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and str(p) == name and name != '.',
            'noncanonical evidence path')
    return name


def read(path):
    require(not path.is_symlink(), 'evidence symlink forbidden')
    return suite.common.strict_json(path.read_bytes())


def unpack(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        rows = archive.infolist()
        require(len(rows) <= 150 and sum(x.file_size for x in rows) <= 16 * 1024 * 1024,
                'unexpected artifact expansion')
        result, seen = {}, set()
        for row in rows:
            name = relative(row.filename.rstrip('/') if row.is_dir() else row.filename)
            require(name not in seen and not stat.S_ISLNK(row.external_attr >> 16),
                    'duplicate or symlink artifact member')
            seen.add(name)
            if not row.is_dir():
                result[name] = archive.read(row)
    return result


def receipt(value, code):
    require(same(value, {'schema_version': 1, 'returncode': code,
                        'timed_out': False, 'spawn_error': None}), 'process receipt differs')
    return suite.common.require_exited(value)


def actions(run, jobs, item, data):
    require(same(run['id'], RUN) and run['head_sha'] == HEAD and run['head_branch'] == BRANCH
            and run['repository']['full_name'] == REPO and run['path'] == suite.WORKFLOW
            and run['event'] == 'push' and same(run['run_attempt'], 1)
            and run['status'] == 'completed' and run['conclusion'] == 'success',
            'source run is not the exact successful original')
    require(type(jobs) is list and len(jobs) == 1, 'source job set differs')
    job = jobs[0]
    require(job['name'] == 'capacity' and same(job['run_id'], RUN) and job['head_sha'] == HEAD
            and job['status'] == 'completed' and job['conclusion'] == 'success', 'source job failed or mixed')
    names = [step['name'] for step in job['steps']]
    require(len(names) == len(set(names)) and all(x in names for x in STEPS)
            and all(x['status'] == 'completed' and x['conclusion'] == 'success' for x in job['steps']),
            'required native step missing, skipped or failed')
    require(item['name'] == ARTIFACT and item['expired'] is False
            and type(item['id']) is int and item['id'] > 0
            and same(item['size_in_bytes'], len(data))
            and item['digest'] == 'sha256:' + identity(data)['sha256']
            and same(item['workflow_run']['id'], RUN) and item['workflow_run']['head_sha'] == HEAD
            and item['archive_download_url'] == f'https://api.github.com/repos/{REPO}/actions/artifacts/{item["id"]}/zip',
            'artifact identity differs')


def sources():
    cfg = read(ROOT / 'config/modernization_stage79_cumulative_mgba.json')
    p02 = next(x for x in cfg['domains'] if x['id'] == 'p02')
    return {suite.SOURCE, suite.SELF, suite.TEST, suite.WORKFLOW,
            'config/modernization_stage79_cumulative_mgba.json', 'config/active_play_baseline.json',
            'infra/toolchain_manifest.json', 'infra/setup_github_actions.sh',
            'scripts/run_modernization_p03_fullslots_e2e.py',
            'tools/modernization_p03_native_pp_repair.py', 'overlays/qol_production/qol_production.c',
            *(x for x, _ in suite.EMBEDDED),
            *(x['path'] for x in (p02['runner'], *p02['dependencies']))}


def payload(files):
    def j(name):
        return suite.common.strict_json(files[name])
    prefixes = ('compile', 'host-toolchain', 'fixed-toolchain', 'linkage', *suite.CASES,
                *('guard-' + x for x in suite.GUARDS))
    names = {'source-head.txt', 'toolchain.txt', 'regression.txt', 'prepare.json',
             'runtime.txt', 'runtime/result.json'}
    names.update('runtime/' + p + s for p in prefixes for s in ('.stdout', '.stderr', '.process.json'))
    require(files.keys() == names and files['source-head.txt'] == (HEAD + '\n').encode(),
            'original member set or checkout differs')
    result = j('runtime/result.json')
    fixed = {'schema_version': 1, 'status': 'PASS', 'scope': suite.SCOPE,
             'acceptance_environment': 'FIXED_TOOLCHAIN', 'fixed_toolchain_verified': True,
             'rom': {'size': 33554432, 'sha256': suite.ROM_SHA},
             'seed': {'size': 131072, 'sha256': suite.SEED_SHA},
             'fresh_processes': 3, 'fresh_cores': 9, 'cache_reuse': 0,
             'protected_inputs': len(sources()) + 2, 'input_hash_and_mtime_unchanged': True,
             'full_p03_acceptance': False, 'release_ready': False}
    extra = {'sources', 'compile_command', 'compiler', 'native_libraries', 'guards', 'cases'}
    require(result.keys() == fixed.keys() | extra, 'aggregate schema differs')
    for key, value in fixed.items():
        require(same(result[key], value), 'aggregate differs: ' + key)
    require(type(result['sources']) is dict and result['sources'].keys() == sources(), 'source closure differs')
    for path, value in result['sources'].items():
        relative(path)
        require(same(suite.common.identity(ROOT / path), value), 'tested source changed: ' + path)
    for prefix in ('compile', 'host-toolchain', 'fixed-toolchain', 'linkage'):
        receipt(j('runtime/' + prefix + '.process.json'), 0)
        require(not files['runtime/' + prefix + '.stderr'], 'native/toolchain diagnostic: ' + prefix)
    require(not files['runtime/compile.stdout'], 'strict compilation emitted diagnostics')
    manifest = read(ROOT / 'infra/toolchain_manifest.json')['tools']
    host = files['runtime/host-toolchain.stdout'].decode()
    require(host == result['compiler'] and manifest['host_cc']['version_contains'] in host,
            'host compiler is not fixed toolchain')
    for name in ('toolchain.txt', 'runtime/fixed-toolchain.stdout'):
        text = files[name].decode()
        require(text.endswith('GitHub Actions toolchain: PASS\n'), 'fixed verification incomplete')
        for key in ('python', 'host_cc', 'arm_none_eabi_gcc', 'mgba'):
            require('[OK] ' + key + ': ' + manifest[key]['version'] in text, 'missing fixed tool: ' + key)
    require(re.search(rb'\nRan 35 tests in [0-9.]+s\n\nOK\n$', files['regression.txt']) is not None,
            'source regression incomplete')
    command = result['compile_command']
    require(type(command) is list and len(command) == 12
            and command[:7] == ['/usr/bin/cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Itools']
            and command[7].startswith('-I') and command[8:10] == [suite.SOURCE, '-o']
            and command[11] == '-lmgba', 'fixed compile command differs')
    libraries = result['native_libraries']
    require(type(libraries) is dict and libraries and b'not found' not in files['runtime/linkage.stdout'],
            'native library closure missing')
    for path, value in libraries.items():
        require(Path(path).is_absolute() and type(value) is dict and value.keys() == {'size', 'sha256'}
                and type(value['size']) is int and value['size'] > 0
                and re.fullmatch('[0-9a-f]{64}', value['sha256']) is not None, 'invalid library identity')
    require(type(result['cases']) is list and len(result['cases']) == 3, 'capacity cases missing')
    for name, row in zip(suite.CASES, result['cases']):
        require(row.keys() == {'case', 'process', 'result', 'stdout_sha256', 'stderr_sha256', 'save_after'}
                and row['case'] == name, 'case schema/order differs')
        proc = j('runtime/' + name + '.process.json')
        require(same(proc, row['process']), 'case original receipt differs')
        value = suite.validate_result(files['runtime/' + name + '.stdout'], name, receipt(proc, 0))
        require(same(value, row['result']), 'case result not original')
        for suffix in ('stdout', 'stderr'):
            require(identity(files['runtime/' + name + '.' + suffix])['sha256'] == row[suffix + '_sha256'],
                    'case raw bytes differ')
        err = files['runtime/' + name + '.stderr']
        require(b'mGBA[' not in err and err.count(b'capacity old core destroyed; fresh core ordinary Continue') == 2,
                'emulator diagnostic or missing cold restart')
        saved = row['save_after']
        require(saved.keys() == {'size', 'sha256'} and type(saved['size']) is int and saved['size'] >= 131072
                and re.fullmatch('[0-9a-f]{64}', saved['sha256']) is not None, 'invalid saved image receipt')
    require(type(result['guards']) is list and len(result['guards']) == 7, 'guard probes missing')
    for api, row in zip(suite.GUARDS, result['guards']):
        require(row.keys() == {'api', 'status', 'process'} and row['api'] == api
                and row['status'] == 'REJECTED_EXPECTED', 'guard identity differs')
        proc = j('runtime/guard-' + api + '.process.json')
        require(same(proc, row['process']), 'guard original differs')
        receipt(proc, 1)
        suite.validate_guard(files['runtime/guard-' + api + '.stdout'], files['runtime/guard-' + api + '.stderr'], proc)
    return result


def summary(result):
    return {'schema_version': 1, 'status': 'VERIFIED_WITH_DECLARED_LIMITS', 'source_run_id': RUN,
            'tested_code_commit': HEAD, 'candidate': result['rom'], 'evidence_root': EVIDENCE,
            'closed_conditions': ['Five physically generated eggs retain FIFO order through 512 overflow steps',
                'Normal dialogue fills the final two party slots',
                'Full party sends the next egg to PC first or last vacant slot without overwrites',
                'Full party and full PC preserve the pending egg; retry after Continue also preserves it',
                'Two normal saves and two new-core Continues preserve party, all 420 PC slots, queue and parents'],
            'cases': list(suite.CASES), 'fresh_processes_in_original': 3, 'fresh_cores_in_original': 9,
            'cached_passes_in_original': 0, 'new_mgba_processes_during_integration': 0,
            'parent_and_pc_fixture_only': True, 'full_p03_acceptance': False,
            'release_ready': False, 'active_stage62_baseline_changed': False}


def check():
    record = read(ROOT / RECORD)
    target = ROOT / EVIDENCE
    require(not target.is_symlink(), 'evidence directory symlink')
    names = {'actions-run.json', 'actions-jobs.json', 'actions-artifact.json', 'original.zip'}
    require({p.name for p in target.iterdir()} == names, 'evidence file set differs')
    require(all(p.is_file() and not p.is_symlink() for p in target.iterdir()), 'invalid evidence file')
    files = {name: identity((target / name).read_bytes()) for name in sorted(names)}
    data = (target / 'original.zip').read_bytes()
    actions(read(target / 'actions-run.json'), read(target / 'actions-jobs.json'), read(target / 'actions-artifact.json'), data)
    result = payload(unpack(data))
    require(same(record, summary(result) | {'files': files}), 'record changed or overclaims acceptance')
    return {'status': 'CHECK_PASS', 'source_run_id': RUN, 'physical_capacity_cases': 3,
            'new_mgba_processes_during_integration': 0, 'release_ready': False}


def get(suffix, binary=False):
    require(suffix.startswith(('runs/', 'artifacts/')) and '..' not in suffix, 'invalid Actions endpoint')
    request = urllib.request.Request(f'https://api.github.com/repos/{REPO}/actions/' + suffix,
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'P03-capacity-recorder'})
    request.add_unredirected_header('Authorization', 'Bearer ' + os.environ['GH_TOKEN'])
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    return data if binary else suite.common.strict_json(data)


def record():
    require(not (ROOT / RECORD).exists(), 'existing acceptance must not be overwritten')
    run = get(f'runs/{RUN}')
    jobs = get(f'runs/{RUN}/jobs?per_page=100')
    items = get(f'runs/{RUN}/artifacts?per_page=100')
    require(same(jobs['total_count'], len(jobs['jobs'])) and same(items['total_count'], len(items['artifacts'])),
            'incomplete Actions pagination')
    selected = [x for x in items['artifacts'] if x['name'] == ARTIFACT]
    require(len(selected) == 1, 'original artifact not unique')
    item = selected[0]
    data = get(f'artifacts/{item["id"]}/zip', True)
    actions(run, jobs['jobs'], item, data)
    result = payload(unpack(data))
    for path, value in result['sources'].items():
        require(same(identity(subprocess.check_output(['git', 'show', HEAD + ':' + path], cwd=ROOT)), value),
                'source not in original tested commit: ' + path)
    target = ROOT / EVIDENCE
    require(not target.exists(), 'existing evidence must not be overwritten')
    target.mkdir(parents=True)
    (target / 'original.zip').write_bytes(data)
    for name, value in (('actions-run.json', run), ('actions-jobs.json', jobs['jobs']), ('actions-artifact.json', item)):
        (target / name).write_text(json.dumps(value, indent=2) + '\n')
    result_record = summary(result) | {'files': {p.name: identity(p.read_bytes()) for p in sorted(target.iterdir())}}
    (ROOT / RECORD).write_text(json.dumps(result_record, indent=2) + '\n')
    verified = check()
    entry = ('\n## 2026-09-10 — P03 five-egg FIFO and party/PC capacity acceptance\n\n'
             f'Original Actions {RUN}, tested source {HEAD}: fixed toolchain; three new mGBA processes, '
             'nine cores, zero cache reuse; all three capacity routes passed. Normal deposit and walking fill '
             'the five-egg FIFO; 512 additional steps do not overwrite it. Real dialogue fills the party then '
             'uses the first/last PC vacancy, or preserves pending eggs when all 420 PC slots are full. '
             'Two normal saves/fresh-core Continues and the repeated full-PC refusal preserve exact party, '
             'PC, queue and parent bytes. Seven actual host-write denial probes pass; no ROM calls after '
             f'the fixture barrier. Original ZIP and Actions metadata: {EVIDENCE}. '
             'This integration performs no additional mGBA run. Parent/PC layout is an isolated fixture. '
             'Other P03/P05 routes, P06/P07 adoption and final release remain incomplete. '
             'Stage82 product bytes, Stage62 baseline, existing evidence and release_ready=false are unchanged.\n')
    for name in ('design/run_log.md', 'design/version_log.md', 'docs/P08_CURRENT_ACCEPTANCE.md'):
        with (ROOT / name).open('a') as stream:
            stream.write(entry)
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(record() if args.record else check(), sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print('P03 capacity evidence: FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
