#!/usr/bin/env python3
"""Verify pinned GitHub Actions originals and explicitly append Stage81 to P08.

No emulation or commit happens here. All metadata and sources are read from the
pinned GitHub runs before any persistent evidence is written. The caller runs
regressions and commits an explicit allowlist only after validation succeeds.
"""
from __future__ import annotations
import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.integrate_modernization_p08_representative_evidence import api
from tools import modernization_p08_stage81_evidence as evidence
from tools import modernization_p08_stage79_evidence as base


def provenance(suite, root=ROOT):
    run_id, head = ((evidence.P03_RUN, evidence.P03_HEAD) if suite == 'p03'
                    else (evidence.RUN, evidence.HEAD))
    run = api('/actions/runs/' + str(run_id))
    jobs = api(f'/actions/runs/{run_id}/jobs?per_page=100')
    artifacts = api(f'/actions/runs/{run_id}/artifacts?per_page=100')
    base.require(jobs['total_count'] == len(jobs['jobs']) and
                 artifacts['total_count'] == len(artifacts['artifacts']), 'incomplete provenance response')
    result = {
        'run': {'run_id': run['id'], 'head_sha': run['head_sha'], 'run_attempt': run['run_attempt'],
                'workflow_path': run['path'], 'repository': run['head_repository']['full_name'],
                'head_branch': run['head_branch'], 'status': run['status'], 'conclusion': run['conclusion']},
        'jobs': [{**{k: row[k] for k in ('id', 'name', 'run_id', 'head_sha', 'status', 'conclusion')},
                  'steps': [{k: step[k] for k in ('name', 'status', 'conclusion')} for step in row['steps']]}
                 for row in jobs['jobs']],
        'artifacts': [], 'sources': {},
    }
    for row in artifacts['artifacts']:
        base.require(row['expired'] is False, 'original artifact expired')
        result['artifacts'].append({**{k: row[k] for k in ('id', 'name', 'digest')},
                                   'run_id': row['workflow_run']['id'],
                                   'head_sha': row['workflow_run']['head_sha']})
    for path in (run['path'], *evidence.TOOLCHAIN):
        response = api('/contents/' + path + '?ref=' + head)
        base.require(response['encoding'] == 'base64' and response['path'] == path, 'original source response')
        raw = base64.b64decode(response['content'])
        base.require(raw == base.regular(root, path), 'original/current execution source differs: ' + path)
        result['sources'][path] = evidence.identity(raw)
    evidence.validate_actions(result, suite)
    return result


def download(name):
    request = urllib.request.Request(
        f'https://api.github.com/repos/{base.REPOSITORY}/actions/artifacts/{evidence.ARCHIVES[name][0]}/zip',
        headers={'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    # Authenticate GitHub only; signed artifact redirects must not inherit this credential.
    request.add_unredirected_header('Authorization', 'Bearer ' + os.environ['GH_TOKEN'])
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(2 * 1048576)
    evidence.unpack(raw, name)
    return raw


def write(relative, raw, root=ROOT):
    path = Path(relative)
    base.require(not path.is_absolute() and '..' not in path.parts, 'unsafe output path')
    current = root
    for part in path.parts[:-1]:
        current /= part
        base.require(not current.is_symlink(), 'symlink output parent')
        current.mkdir(exist_ok=True)
    target = root / path
    base.require(not target.is_symlink(), 'symlink output')
    target.write_bytes(raw)


def import_verified(archives, actions, root=ROOT):
    """Pure supplied-input entry for regression tests; production uses provenance()."""
    evidence.exact(sorted(archives), sorted(evidence.ARCHIVES), 'exact original archive set')
    evidence.exact(sorted(actions), ['p03', 'stage81'], 'exact provenance set')
    for suite, row in actions.items():
        evidence.validate_actions(row, suite)
    contents = {f'actions-{suite}.json': base.stable(row) for suite, row in actions.items()}
    for name, raw in archives.items():
        unpacked = evidence.unpack(raw, name)
        if name == 'p03-fullslots-e2e':
            evidence.validate_p03(unpacked)
        contents[name + '/source.zip'] = raw
        contents.update({name + '/' + key: value for key, value in unpacked.items()})
    # Validate all bytes before writing, and never retain unknown files in this namespace.
    target = root / evidence.DIRECTORY
    if target.exists():
        present = {str(p.relative_to(target)) for p in target.rglob('*') if p.is_file() or p.is_symlink()}
        base.require(present <= set(contents), 'unexpected previous evidence file')
    for name, raw in contents.items():
        write(evidence.DIRECTORY + '/' + name, raw, root)
    config = {'schema_version': 1, 'status': 'EXPLICITLY_ADOPTED_STAGE81_NATIVE_PP_EVIDENCE',
              'files': {name: evidence.identity(raw) for name, raw in sorted(contents.items())}}
    write(evidence.CONFIG, base.stable(config), root)
    evidence.build_extension(root)
    from scripts import check_modernization_p08_current_acceptance as acceptance
    outputs = {path: base.regular(root, path) for path in acceptance.DOCUMENTS}
    for path, raw in evidence.attach_outputs(outputs, root).items():
        write(path, raw, root)
    report = acceptance.build_report(root)
    write(acceptance.OUTPUT, base.stable(report), root)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives', type=Path, help='reuse already-downloaded exact <artifact-name>.zip files')
    args = parser.parse_args()
    actions = {suite: provenance(suite) for suite in ('stage81', 'p03')}
    archives = {name: (args.archives / (name + '.zip')).read_bytes() if args.archives else download(name)
                for name in evidence.ARCHIVES}
    report = import_verified(archives, actions)
    print(json.dumps({'status': 'PASS', 'candidate_stage': 81, 'candidate_sha256': evidence.adapter.SHA,
                      'original_native_successes': 15, 'original_expected_failure_controls': 2,
                      'fresh_processes_this_import': 0, 'release_ready': False,
                      'current_blocker_count': len(report['current_blockers'])}))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (base.EvidenceError, RuntimeError, ValueError, TypeError, KeyError, OSError) as error:
        print('P08 Stage81 integration failed: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
