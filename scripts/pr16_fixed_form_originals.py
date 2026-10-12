#!/usr/bin/env python3
"""Verify the exact four original fixed-form archives, including Git presence.

Recovery is explicit and digest-pinned. It does not run an emulator, edit raw
results, accept a case, or modify the active ROM baseline. A directory git-add
silently skips ignored ZIPs; callers must add these exact scanned paths with
`git add -f` and invoke --index before committing.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'content/modernization/pr16_fixed_form_acceptance_evidence'
# run, job, artifact, source HEAD, ZIP size, SHA256, Actions conclusion
PINS = (
    (34694218218, 103554787890, 10297554037, 'a9ec7ab9d93d8013139698242802826278aaf667', 802643, '45fbc581ec17cf7e0504d2c8d3150072e44a9099e4deed04da759d8b3a6328c7', 'failure'),
    (34694785866, 103556287612, 10297959447, '54625b020731f68d72643b65e60cbb91c2f0524e', 840801, '4af3705661914957c55fba282e66d3abcc73625cd5e2c82bde388e19bddc0a01', 'failure'),
    (34695030927, 103556933334, 10298660168, '2bb937f7c2c1bedf29531f70b88d59163f349c65', 530770, '4036ebbda5962133c616ce450f1e0a70d0a65aad54dac58e7654a9c37ca51f61', 'success'),
    (34695512247, 103558198010, 10298208423, '952b9fb2e2ee8b5951214eda7a7847c4ca1092d5', 854855, '0d31881c45e05e9aa4b3c122663ce3bfd7605ff4287299a602c48232dc893cc8', 'success'),
)


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def identity(raw: bytes) -> dict:
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def scan(archive: zipfile.ZipFile, depth: int = 0) -> None:
    infos = archive.infolist()
    names = [row.filename for row in infos]
    need(depth <= 1 and len(names) == len(set(names)) and len(names) < 1000, 'duplicate or unbounded ZIP')
    need(sum(row.file_size for row in infos) < 32000000, 'unbounded ZIP expansion')
    for info in infos:
        path = PurePosixPath(info.filename)
        need(not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename, 'unsafe ZIP path')
        need(not stat.S_ISLNK(info.external_attr >> 16), 'ZIP symlink')
        need(path.suffix.lower() not in {'.gba', '.sav', '.srm', '.bps', '.ips', '.ups', '.bin'}, 'ROM/save/private binary in evidence')
        data = archive.read(info)
        if path.suffix == '.zip':
            need(depth == 0 and path.name in {'sources.zip', 'entry-sources.zip', 'generated-controller.zip', 'owner-sources.zip'}, 'unexpected nested archive')
            with zipfile.ZipFile(io.BytesIO(data)) as nested:
                scan(nested, 1)
        elif path.suffix == '.ppm':
            need(depth == 0 and data.startswith(b'P6\n240 160\n255\n') and len(data) == 115215, 'invalid native screenshot')
        else:
            data.decode('utf-8-sig')
            need(b'\0' not in data, 'nontext evidence member')


def validate_archive(raw: bytes, pin: tuple) -> dict:
    run, _, _, head, size, digest, _ = pin
    need(identity(raw) == dict(size=size, sha256=digest), 'original ZIP identity differs: ' + str(run))
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        scan(archive)
        if run == 34695030927:
            prefix = 'pr16-fixed-form-owner-static/'
            result = json.loads(archive.read(prefix + 'owner-index.json'))
            need(result['tested_head'] == head and result['new_emulator_runs'] == 0 and result['rom_changes'] == 0, 'static source claims differ')
            source_bytes = archive.read(prefix + 'owner-sources.zip')
            need(identity(source_bytes) == result['source_zip'], 'static source ZIP differs')
            bindings = {row['path']: {k: row[k] for k in ('size', 'sha256')} for row in result['sources']}
        else:
            prefix = 'pr16-fixed-form-acceptance/'
            receipt = json.loads(archive.read(prefix + 'receipt.json'))
            result = json.loads(archive.read(prefix + 'result.json'))
            need(receipt['tested_head'] == head and receipt['p03_fixed_form_gap_closed'] is False, 'receipt source/claim differs')
            for name, bound in receipt['members'].items():
                need(identity(archive.read(prefix + name)) == bound, 'receipt member differs: ' + name)
            source_bytes = archive.read(prefix + 'sources.zip')
            bindings = result['sources']
        with zipfile.ZipFile(io.BytesIO(source_bytes)) as sources:
            need(set(sources.namelist()) == set(bindings), 'source member set differs')
            for name, bound in bindings.items():
                need(identity(sources.read(name)) == bound, 'source member digest differs: ' + name)
    return identity(raw)


def check(root: Path, index: bool = False) -> dict:
    verified = []
    for pin in PINS:
        path = f'{BASE}/{pin[0]}/original.zip'
        file = root / path
        need(not any(p.is_symlink() for p in (file, *file.parents)), 'symlink original')
        raw = file.read_bytes()
        bound = validate_archive(raw, pin)
        tracked = subprocess.check_output(['git', 'show', (':' if index else 'HEAD:') + path], cwd=root)
        need(tracked == raw, 'original is missing or differs in Git: ' + path)
        actions = json.loads((file.parent / 'actions.json').read_bytes())
        need(actions['run']['id'] == pin[0] and actions['run']['head_sha'] == pin[3], 'retained Actions run differs')
        need(actions['run']['conclusion'] == pin[6] and actions['artifact']['id'] == pin[2], 'retained Actions result differs')
        need(actions['artifact']['digest'] == 'sha256:' + pin[5], 'retained Actions digest differs')
        verified.append(dict(path=path, run_id=pin[0], **bound))
    return dict(schema_version=1, status='PASS_TRACKED_RAW_ORIGINALS', checked_surface='INDEX' if index else 'HEAD', originals=verified, new_emulator_runs=0, p03_fixed_form_gap_closed=False, release_ready=False)


def recover_prior(root: Path) -> None:
    repository = os.environ.get('GITHUB_REPOSITORY')
    need(repository == 'dekaazarashi1111-web/pokemon-vega-modern', 'unexpected recovery repository')
    def api(path: str) -> bytes:
        return subprocess.check_output(['gh', 'api', f'repos/{repository}/' + path], timeout=90)
    for pin in PINS[:3]:
        run_id, job_id, artifact_id, head, _, digest, conclusion = pin
        dest = root / BASE / str(run_id) / 'original.zip'
        need(dest.parent.is_dir() and not dest.exists(), 'recovery is create-only into existing evidence record')
        run = json.loads(api(f'actions/runs/{run_id}'))
        jobs = json.loads(api(f'actions/runs/{run_id}/jobs'))
        artifact = json.loads(api(f'actions/artifacts/{artifact_id}'))
        need(run['id'] == run_id and run['head_sha'] == head and run['conclusion'] == conclusion and run['run_attempt'] == 1, 'live Actions run differs')
        need(len(jobs['jobs']) == 1 and jobs['jobs'][0]['id'] == job_id and jobs['jobs'][0]['conclusion'] == conclusion, 'live Actions job differs')
        need(artifact['id'] == artifact_id and artifact['workflow_run']['head_sha'] == head and artifact['digest'] == 'sha256:' + digest and artifact['expired'] is False, 'live artifact differs')
        raw = api(f'actions/artifacts/{artifact_id}/zip')
        validate_archive(raw, pin)
        with dest.open('xb') as output:
            output.write(raw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recover-prior', action='store_true')
    parser.add_argument('--index', action='store_true')
    args = parser.parse_args()
    if args.recover_prior:
        recover_prior(ROOT)
    else:
        print(json.dumps(check(ROOT, args.index), sort_keys=True, indent=2))
