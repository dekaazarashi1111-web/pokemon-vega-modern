#!/usr/bin/env python3
"""Integrate original P03 breeding Actions evidence; default check is read-only."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tools')]
import run_modernization_p03_breeding_e2e as breeding

common = breeding.common
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
SOURCE_RUN = 34434453733
TESTED_HEAD = '8a2919f390902a3b991e13f3e252f47bd3d93261'
RECORD = 'content/modernization/p08_p03_breeding_acceptance.json'
EVIDENCE = 'content/modernization/p08_breeding_evidence/' + str(SOURCE_RUN)
ARTIFACT = 'p03-breeding-e2e'
REQUIRED_STEPS = (
    'Install and verify fixed native toolchain',
    'Reject invalid evidence and missing native observations',
    'Rebuild unchanged Stage82 and execute eight fresh physical breeding cases',
    'Run actions/upload-artifact@v4',
)
CLOSED = [
    'Two parents deposited through the real daycare dialogue and party menu',
    'Physical walking generates an egg; real outdoor NPC dialogue claims it',
    'Father-only, mother-only, both-parent and no-eligible-move inheritance',
    'Duplicate inherited moves are not added twice',
    'Light Ball on either parent grants Volt Tackle; absent item does not',
    'Egg and hatched individual each survive normal Save and fresh-core Continue',
    'Native unaccelerated hatching, nickname refusal, species and canonical PP',
]
REMAINING = [
    'Other breeding species/form/incense/Ditto combinations and full-party rejection',
    'Other untested P03 acquisition routes and final archive economy adoption',
    'Full P05 acceptance including natural ability acquisition, Mega and Circus',
    'Explicit P06/P07 adopted deltas, implementation and acceptance',
    'Final release acceptance and play-baseline promotion',
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(a, b):
    """Deep exact types, including dictionaries (JSON false is never integer 0)."""
    if type(a) is not type(b):
        return False
    if type(b) is dict:
        return set(a) == set(b) and all(same(a[k], b[k]) for k in b)
    if type(b) is list:
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def digest(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def relative(name):
    require(type(name) is str and name and '\\' not in name, 'invalid relative path')
    p = PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and str(p) == name
            and name != '.', 'noncanonical relative path')
    return p


def read(path):
    return common.strict_json(path.read_bytes())


def process(receipt, expected):
    require(same(receipt, {'schema_version': 1, 'returncode': expected,
                          'timed_out': False, 'spawn_error': None}), 'process receipt differs')
    return common.require_exited(receipt)


def archive_members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        rows = archive.infolist()
        require(len(rows) <= 200 and sum(row.file_size for row in rows) <= 16777216,
                'unexpected artifact size or member count')
        result = {}
        seen = set()
        for row in rows:
            name = row.filename.rstrip('/') if row.is_dir() else row.filename
            relative(name)
            require(name not in seen, 'duplicate artifact member')
            seen.add(name)
            require(not stat.S_ISLNK(row.external_attr >> 16), 'artifact symlink')
            if not row.is_dir():
                result[name] = archive.read(row)
        return result


def validate_actions(run, jobs, item, data):
    require(type(run['id']) is int and run['id'] == SOURCE_RUN
            and run['head_sha'] == TESTED_HEAD and run['head_branch'] == BRANCH
            and run['path'] == breeding.WORKFLOW and run['repository']['full_name'] == REPO
            and run['status'] == 'completed' and run['conclusion'] == 'success'
            and run['event'] == 'push' and type(run['run_attempt']) is int
            and run['run_attempt'] == 1, 'source Actions run not successful/exact')
    require(type(jobs) is list and len(jobs) == 1 and jobs[0]['name'] == 'breeding',
            'source job set differs')
    job = jobs[0]
    require(type(job['run_id']) is int and job['run_id'] == SOURCE_RUN
            and job['head_sha'] == TESTED_HEAD and job['status'] == 'completed'
            and job['conclusion'] == 'success', 'source job failed or mixed HEAD')
    names = [step['name'] for step in job['steps']]
    require(len(names) == len(set(names)) and all(name in names for name in REQUIRED_STEPS),
            'required native steps missing/duplicated')
    require(all(step['status'] == 'completed' and step['conclusion'] == 'success'
                for step in job['steps']), 'failed/skipped source step')
    require(item['name'] == ARTIFACT and item['expired'] is False
            and same(item['size_in_bytes'], len(data))
            and item['digest'] == 'sha256:' + digest(data)['sha256']
            and same(item['workflow_run']['id'], SOURCE_RUN)
            and item['workflow_run']['head_sha'] == TESTED_HEAD,
            'original artifact digest/size/run differs')
    require(type(item['id']) is int and item['id'] > 0
            and item['archive_download_url'] == 'https://api.github.com/repos/' + REPO
            + '/actions/artifacts/' + str(item['id']) + '/zip', 'artifact URL differs')


def required_sources():
    cfg = read(ROOT / 'config/modernization_stage79_cumulative_mgba.json')
    p02 = next(row for row in cfg['domains'] if row['id'] == 'p02')
    return {breeding.SOURCE, breeding.SELF, breeding.TEST, breeding.WORKFLOW,
            'config/modernization_stage79_cumulative_mgba.json', 'config/active_play_baseline.json',
            'infra/toolchain_manifest.json', 'infra/setup_github_actions.sh',
            'overlays/acquisition_runtime/acquisition_engine_adapter_rom.c',
            'scripts/run_modernization_p03_fullslots_e2e.py',
            'tools/modernization_p03_native_pp_repair.py',
            'tools/modernization_p03_archive_ui_repair.py', breeding.repair.ASM,
            *(source for source, _ in breeding.EMBEDDED),
            *(entry['path'] for entry in (p02['runner'], *p02['dependencies']))}


def validate_payload(members):
    def blob(name):
        return members[name]
    def j(name):
        return common.strict_json(blob(name))
    require(blob('source-head.txt') == (TESTED_HEAD + '\n').encode(), 'mixed source checkout')
    report = j('runtime/result.json')
    fixed = {'schema_version': 1, 'status': 'PASS', 'scope': breeding.SCOPE,
             'candidate': {'size': 33554432, 'sha256': breeding.repair.CANDIDATE_SHA},
             'seed': {'size': 131072, 'sha256': breeding.SEED_SHA},
             'fresh_mgba_processes': 8, 'fresh_core_instances': 24, 'cached_passes': 0,
             'all_breeding_paths_accepted': False, 'full_p03_acceptance': False, 'release_ready': False}
    require(set(report) == set(fixed) | {'sources', 'oracle', 'cases', 'host_write_guard_checks',
                                       'host_cc_version'}, 'aggregate schema differs')
    for key, value in fixed.items():
        require(same(report[key], value), 'aggregate differs: ' + key)
    require(type(report['sources']) is dict and set(report['sources']) == required_sources(),
            'source closure missing or expanded')
    for path, identity in report['sources'].items():
        relative(path)
        require(same(common.identity(ROOT / path), identity), 'tested source changed: ' + path)
    # Regenerate the guarded candidate entirely in memory. No ROM or input file is written.
    parent = ROOT / breeding.repair.parent.PARENT_PATH
    candidate81, _ = breeding.repair.parent.build(parent.read_bytes())
    candidate, recipe = breeding.repair.build(candidate81)
    require(same(digest(candidate), fixed['candidate'])
            and same(recipe, j('runtime/candidate.json'))
            and same(common.strict_json(json.dumps(breeding.audit_oracle(candidate)).encode()), report['oracle']), 'candidate recipe/oracle differs')
    process(j('runtime/compile.process.json'), 0)
    require(not blob('runtime/compile.stdout') and not blob('runtime/compile.stderr'),
            'native strict compilation diagnostic')
    process(j('runtime/host-toolchain.process.json'), 0)
    host = blob('runtime/host-toolchain.stdout').decode('utf-8')
    manifest = read(ROOT / 'infra/toolchain_manifest.json')
    require(not blob('runtime/host-toolchain.stderr') and host == report['host_cc_version']
            and manifest['tools']['host_cc']['version_contains'] in host, 'host toolchain differs')
    toolchain = blob('toolchain.txt').decode('utf-8')
    for tool in ('python', 'host_cc', 'arm_none_eabi_gcc', 'mgba'):
        require('[OK] ' + tool + ': ' + manifest['tools'][tool]['version'] in toolchain,
                'fixed toolchain identity missing: ' + tool)
    require(toolchain.endswith('GitHub Actions toolchain: PASS\n'), 'toolchain verification incomplete')
    regression = blob('regression.txt').decode('utf-8')
    require(re.search(r'\nRan 28 tests in [0-9.]+s\n\nOK\n$', regression) is not None,
            'source regression run incomplete')
    require(type(report['cases']) is list and len(report['cases']) == 8, 'case count differs')
    for name, row in zip(breeding.CASES, report['cases']):
        require(row['name'] == name and row['status'] == 'PASS', 'case order/identity differs')
        receipt = j('runtime/' + name + '.process.json')
        require(same(receipt, row['process']), 'process original differs')
        result = breeding.validate_result(blob('runtime/' + name + '.stdout'), name, process(receipt, 0))
        require(same(result, row['result']) and same(row['rom'], fixed['candidate']), 'case original/result differs')
        for suffix in ('stdout', 'stderr'):
            require(same(digest(blob('runtime/' + name + '.' + suffix)), row[suffix]), 'case byte identity differs')
        stderr = blob('runtime/' + name + '.stderr')
        require(b'mGBA[' not in stderr and stderr.count(b'original core destroyed; new core boot and normal Continue') == 2,
                'emulator diagnostic or missing cold restart')
    require(type(report['host_write_guard_checks']) is list and len(report['host_write_guard_checks']) == 7,
            'host-write guards missing')
    for api, row in zip(breeding.GUARDS, report['host_write_guard_checks']):
        require(row['api'] == api and row['status'] == 'REJECTED_EXPECTED', 'host-write guard identity differs')
        receipt = j('runtime/guard-' + api + '.process.json')
        require(same(receipt, row['process']), 'guard original process differs')
        process(receipt, 1)
        breeding.validate_guard(blob('runtime/guard-' + api + '.stdout'), blob('runtime/guard-' + api + '.stderr'), receipt)
    expected_members = {'source-head.txt', 'toolchain.txt', 'regression.txt', 'runtime.txt',
                        'runtime/result.json', 'runtime/candidate.json'}
    for name in ('compile', 'host-toolchain', *breeding.CASES, *('guard-' + g for g in breeding.GUARDS)):
        expected_members.update('runtime/' + name + suffix for suffix in ('.stdout', '.stderr', '.process.json'))
    require(set(members) == expected_members, 'extra/missing original artifact files')
    return report


def summary(report):
    return {'schema_version': 1, 'status': 'VERIFIED_WITH_DECLARED_LIMITS',
            'source_run_id': SOURCE_RUN, 'tested_code_commit': TESTED_HEAD,
            'candidate': report['candidate'], 'evidence_root': EVIDENCE,
            'physical_breeding_cases': list(breeding.CASES), 'fresh_mgba_processes_in_original': 8,
            'fresh_core_instances_in_original': 24, 'cached_passes_in_original': 0,
            'new_mgba_processes_during_integration': 0, 'closed_conditions': CLOSED,
            'remaining_conditions': REMAINING, 'parent_fixture_only': True,
            'all_breeding_paths_accepted': False, 'full_p03_acceptance': False,
            'release_ready': False, 'active_stage62_baseline_changed': False}


def check():
    record = read(ROOT / RECORD)
    target = ROOT / EVIDENCE
    files = {p.relative_to(target).as_posix(): common.identity(p) for p in sorted(target.rglob('*')) if p.is_file()}
    require(set(files) == {'actions-run.json', 'actions-jobs.json', 'actions-artifact.json', 'original.zip'},
            'evidence file set differs')
    require(same(record['files'], files), 'evidence original bytes changed')
    data = (target / 'original.zip').read_bytes()
    validate_actions(read(target / 'actions-run.json'), read(target / 'actions-jobs.json'),
                     read(target / 'actions-artifact.json'), data)
    report = validate_payload(archive_members(data))
    expected = summary(report) | {'files': files}
    require(same(record, expected), 'acceptance summary differs or overclaims completion')
    return {'status': 'CHECK_PASS', 'source_run_id': SOURCE_RUN, 'physical_breeding_cases': 8,
            'integration_new_mgba_processes': 0, 'release_ready': False}


def get(suffix, binary=False):
    require(suffix.startswith(('runs/', 'artifacts/')) and '..' not in suffix, 'unsafe Actions endpoint')
    request = urllib.request.Request('https://api.github.com/repos/' + REPO + '/actions/' + suffix,
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'P03-breeding-evidence-recorder'})
    request.add_unredirected_header('Authorization', 'Bearer ' + os.environ['GH_TOKEN'])
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    return data if binary else common.strict_json(data)


def record():
    run = get('runs/' + str(SOURCE_RUN))
    jobs_response = get('runs/' + str(SOURCE_RUN) + '/jobs?per_page=100')
    require(jobs_response['total_count'] == len(jobs_response['jobs']), 'incomplete job listing')
    artifacts = get('runs/' + str(SOURCE_RUN) + '/artifacts?per_page=100')
    require(artifacts['total_count'] == len(artifacts['artifacts']), 'incomplete artifact listing')
    selected = [item for item in artifacts['artifacts'] if item['name'] == ARTIFACT]
    require(len(selected) == 1, 'artifact not unique')
    item = selected[0]
    data = get('artifacts/' + str(item['id']) + '/zip', True)
    validate_actions(run, jobs_response['jobs'], item, data)
    report = validate_payload(archive_members(data))
    for path, identity in report['sources'].items():
        original = subprocess.check_output(['git', 'show', TESTED_HEAD + ':' + path], cwd=ROOT)
        require(same(digest(original), identity), 'source does not belong to tested commit: ' + path)
    target = ROOT / EVIDENCE
    require(not target.exists() and not (ROOT / RECORD).exists(), 'evidence/record already exists')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='breeding-evidence-', dir=target.parent) as tmp:
        staging = Path(tmp)
        for name, value in [('actions-run.json', run), ('actions-jobs.json', jobs_response['jobs']), ('actions-artifact.json', item)]:
            (staging / name).write_text(json.dumps(value, indent=2) + '\n')
        (staging / 'original.zip').write_bytes(data)
        files = {p.name: common.identity(p) for p in sorted(staging.iterdir())}
        result = summary(report) | {'files': files}
        shutil.copytree(staging, target)
    (ROOT / RECORD).write_text(json.dumps(result, indent=2) + '\n')
    checked = check()
    entry = ('\n## 2026-09-10 — USER-P03-BREEDING / Stage82 physical daycare and hatch\n\n'
             f'Original Actions run {SOURCE_RUN} at {TESTED_HEAD}: eight new mGBA processes, '
             '24 core instances and zero cache reuse passed. Real daycare deposit, walking generation, '
             'egg claim, parental inheritance and duplicate exclusion, Light Ball on either parent and '
             'its negative control, native unaccelerated hatch, and two normal Save/fresh-core Continue '
             'cycles per case are observed with seven host-write API barriers. Two manual saves plus '
             'one observed native hatch registration save are required, with exact byte snapshots. '
             f'P08 original ZIP and Actions identities are at {EVIDENCE}. Integration revalidates original '
             'bytes and does not count as another emulator run. No product ROM changed; Stage82 remains '
             f'{breeding.repair.CANDIDATE_SHA}. Parents and starting map are an isolated fixture, not a '
             'natural capture claim. Other breeding combinations/full-party routes, broader P03/P05, '
             'P06/P07 adoption and final release remain open. Stage62 and release_ready=false are unchanged.\n')
    for path in ('design/run_log.md', 'design/version_log.md'):
        with (ROOT / path).open('a') as stream:
            stream.write(entry)
    with (ROOT / 'docs/P08_CURRENT_ACCEPTANCE.md').open('a') as stream:
        stream.write('\n## Stage82：通常操作による繁殖・孵化の後続証跡\n\n'
            '旧スナップショットのbreeding_e2e=falseは旧runnerの範囲であり、後続の成功を未実施へ戻さない。'
            'Stage82の25習得画面と7領域はp08_stage82_archive_acceptance.json、'
            '今回の8条件はcontent/modernization/p08_p03_breeding_acceptance.jsonを参照する。'
            '通常の預入・歩行生成・受取・孵化、および孵化前後の保存／別core Continueを検証する。'
            '親の初期作成はfixtureであり、全種・全組合せ・満杯時等の受入は未完了。'
            '詳細はdocs/P03_BREEDING_E2E.md。\n\n'
            '```sh\npython3 scripts/record_modernization_p03_breeding.py\n```\n\n'
            '上記は読取専用の原本再検証。原本8プロセス／24 coreと統合時の新規実行0件を区別する。\n')
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(record() if args.record else check(), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print('P03 breeding evidence: FAIL: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
