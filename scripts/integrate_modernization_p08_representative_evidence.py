#!/usr/bin/env python3
"""Import pinned Actions originals and append representative evidence to P08.

This operation verifies retained executions. It never runs mGBA or promotes a
phase. Git commit/push is deliberately left to the caller after regression tests.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import modernization_p08_representative_evidence as evidence
from tools import modernization_p08_stage79_evidence as base


def api(path: str) -> dict:
    request = urllib.request.Request('https://api.github.com/repos/' + base.REPOSITORY + path,
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def provenance(suite: str, root: Path) -> dict:
    pin = evidence.SUITES[suite]
    run = api('/actions/runs/' + str(pin['run_id']))
    jobs = api('/actions/runs/' + str(pin['run_id']) + '/jobs?per_page=100')
    base.require(jobs['total_count'] == 1 and len(jobs['jobs']) == 1, 'exactly one original runtime job')
    job = jobs['jobs'][0]
    artifact = api('/actions/artifacts/' + str(pin['artifact_id']))
    base.require(not artifact['expired'], 'original artifact has expired')
    steps = []
    for name in pin['steps']:
        found = [row for row in job['steps'] if row['name'] == name]
        base.require(len(found) == 1, 'required execution step is not unique')
        steps.append({key: found[0][key] for key in ('name', 'status', 'conclusion')})
    result = {
        'repository': run['head_repository']['full_name'], 'head_branch': run['head_branch'],
        'run_id': run['id'], 'run_attempt': run['run_attempt'], 'head_sha': run['head_sha'],
        'workflow_path': run['path'], 'status': run['status'], 'conclusion': run['conclusion'],
        'artifact_id': artifact['id'], 'artifact_name': artifact['name'], 'artifact_digest': artifact['digest'],
        'artifact_run_id': artifact['workflow_run']['id'], 'artifact_head_sha': artifact['workflow_run']['head_sha'],
        'job_id': job['id'], 'job_name': job['name'], 'job_status': job['status'], 'job_conclusion': job['conclusion'],
        'required_steps': steps, 'verified_execution_sources': {},
    }
    for path in [evidence.workflow_path(suite), *evidence.TOOLCHAIN]:
        response = api('/contents/' + path + '?ref=' + urllib.parse.quote(pin['head_sha'], safe=''))
        base.require(response['encoding'] == 'base64' and response['path'] == path,
                     'original execution source response')
        raw = base64.b64decode(response['content'])
        base.require(raw == base.regular(root, path), 'execution source changed since runtime: ' + path)
        result['verified_execution_sources'][path] = evidence.identity(raw)
    evidence.validate_actions(result, suite)
    return result


def import_suite(suite: str, archive_path: Path, actions: dict, root: Path) -> dict:
    """No arbitrary archive paths are extracted; members are an exact fixed set."""
    pin = evidence.SUITES[suite]
    archive = archive_path.read_bytes()
    files = evidence.unpack(archive, suite)
    evidence.validate_actions(actions, suite)
    evidence.validate_payload(files, suite)
    directory = f'{evidence.DIRECTORY}/{suite}/{pin["run_id"]}'
    target = root / directory
    # Never follow existing symlink ancestors during writes.
    current = root
    for part in Path(directory).parts:
        current /= part
        base.require(not current.is_symlink(), 'symlink import destination')
        current.mkdir(exist_ok=True)
    files.update({'source.zip': archive, 'actions.json': base.stable(actions)})
    base.require(not (set(p.name for p in target.iterdir()) - set(files)), 'unexpected previous evidence files')
    for name, raw in files.items():
        path = target / name
        base.require(not path.is_symlink(), 'symlink evidence output')
        path.write_bytes(raw)
    return {'directory': directory, 'files': {name: evidence.identity(raw) for name, raw in sorted(files.items())}}


def update_handoffs(root: Path) -> dict:
    from scripts import check_modernization_p08_current_acceptance as acceptance
    outputs = {path: base.regular(root, path) for path in acceptance.DOCUMENTS}
    updated = evidence.attach_outputs(outputs, root)
    for path, raw in updated.items():
        (root / path).write_bytes(raw)
    report = acceptance.build_report(root)
    (root / acceptance.OUTPUT).write_bytes(base.stable(report))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', type=Path, required=True,
                        help='directory containing <suite>.zip downloaded from pinned artifact IDs')
    args = parser.parse_args()
    config = {'schema_version': 1, 'suites': {}}
    # Fetch and validate all metadata before changing any repository files.
    actions = {suite: provenance(suite, ROOT) for suite in evidence.SUITES}
    for suite in evidence.SUITES:
        config['suites'][suite] = import_suite(suite, args.archives / (suite + '.zip'), actions[suite], ROOT)
    (ROOT / evidence.CONFIG).write_bytes(base.stable(config))
    report = update_handoffs(ROOT)
    print(json.dumps({'status': 'PASS', 'retained_original_processes': 30, 'fresh_processes_this_import': 0,
                      'current_blocker_count': len(report['current_blockers']), 'release_ready': False}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (base.EvidenceError, ValueError, TypeError, KeyError, OSError) as error:
        print('P08 representative integration failed: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
