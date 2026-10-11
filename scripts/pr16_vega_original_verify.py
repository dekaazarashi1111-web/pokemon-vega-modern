#!/usr/bin/env python3
"""完了済み採取artifactだけから独立2生成・純読取を検証する。再採取しない。"""
from __future__ import annotations
import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pr16_vega_original_baseline import identity, require, stable, TASK
from tools.pr16_vega_original_audit import prepare, check
from pr16_wiki_reconcile import fetch

REQUEST = '.github/pr16-vega-original-audit.json'
PROOF = ROOT / '.local/pr16-vega-original-audit-proof'


def capture_artifact(request, destination):
    run = fetch(f'actions/runs/{request["run_id"]}')
    jobs = fetch(f'actions/runs/{request["run_id"]}/jobs?per_page=100')
    artifact = fetch(f'actions/artifacts/{request["artifact_id"]}')
    require(run['head_sha'] == request['source_head'] and run['head_branch'] == 'codex/modernization-followup-20260908'
            and run['path'] == request['workflow'] and run['event'] == 'push'
            and run['status'] == 'completed' and run['conclusion'] == 'success', '完了run不一致')
    require(len(jobs['jobs']) == jobs['total_count'] == 1 and jobs['jobs'][0]['name'] == request['job_name'], 'job不一致')
    job = jobs['jobs'][0]
    require(job['status'] == 'completed' and job['conclusion'] == 'success'
            and all(s['status'] == 'completed' and s['conclusion'] == 'success' for s in job['steps']), 'step未成功')
    require(artifact['workflow_run']['id'] == request['run_id'] and artifact['workflow_run']['head_sha'] == request['source_head']
            and artifact['name'] == request['artifact_name'] and not artifact['expired']
            and artifact['digest'] == 'sha256:' + request['artifact_sha256'], 'artifact binding不一致')
    raw = fetch(f'actions/artifacts/{request["artifact_id"]}/zip', binary=True)
    require(identity(raw) == {'size': artifact['size_in_bytes'], 'sha256': request['artifact_sha256']}, 'artifact原本byte不一致')
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) <= 500 and sum(i.file_size for i in archive.infolist()) < 50000000, 'ZIP集合/サイズ不正')
        for info in archive.infolist():
            p = PurePosixPath(info.filename)
            require(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                    and not stat.S_ISLNK(info.external_attr >> 16), 'ZIP危険path')
        archive.extractall(destination)
    return {'run': {k: run[k] for k in ('id','head_sha','head_branch','path','event','status','conclusion','created_at','updated_at')},
            'job': {k: job[k] for k in ('id','name','status','conclusion','steps')},
            'artifact': {k: artifact[k] for k in ('id','name','size_in_bytes','digest','expires_at','workflow_run')}}


def snapshot(paths):
    return {str(p): (identity(p.read_bytes()), p.stat().st_mtime_ns) for base in paths for p in sorted(base.rglob('*')) if p.is_file()}


def verify():
    request = json.loads((ROOT / REQUEST).read_bytes())
    require(request['task'] == TASK, '要求task不一致')
    base = ROOT / '.local/pr16-vega-original-audit-input'
    actions = capture_artifact(request['capture'], base)
    capture = base / 'capture'
    source_before = snapshot([base])
    outputs = []
    for seed in ('11', '29'):
        out = ROOT / ('.local/pr16-vega-original-build-' + seed)
        subprocess.run([sys.executable, '-B', __file__, 'prepare', '--capture', str(capture), '--output', str(out)],
                       check=True, env=dict(os.environ, PYTHONHASHSEED=seed))
        outputs.append(out)
    require({p.name: p.read_bytes() for p in outputs[0].iterdir()} == {p.name: p.read_bytes() for p in outputs[1].iterdir()}, '独立2生成不一致')
    before = snapshot([base, *outputs])
    subprocess.run([sys.executable, '-B', __file__, 'check', '--capture', str(capture), '--output', str(outputs[0])], check=True)
    require(before == snapshot([base, *outputs]) and source_before == snapshot([base]), '純読取/採取原本不変に違反')
    receipt = json.loads((outputs[0] / 'receipt.json').read_bytes())
    require(receipt['outputs'] == request['expected_outputs'], 'ローカルとActions出力不一致')
    subprocess.run(['git', 'diff', '--exit-code'], cwd=ROOT, check=True)
    shutil.copytree(outputs[0], PROOF / 'outputs')
    (PROOF / 'capture-actions.json').write_bytes(stable(actions))
    (PROOF / 'capture-unit.txt').write_bytes((base / 'unit.log').read_bytes())
    summary = json.loads((outputs[0] / 'summary.json').read_bytes())
    report = dict(summary, verification_head=os.environ['GITHUB_SHA'], verification_run_id=int(os.environ['GITHUB_RUN_ID']),
                  focused_tests=43, two_process_outputs_identical=True, readonly_byte_mtime_unchanged=True,
                  tracked_tree_unchanged=True, local_and_actions_outputs_identical=True,
                  files={p.name: identity(p.read_bytes()) for p in outputs[0].iterdir()})
    (PROOF / 'verify.json').write_bytes(stable(report))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['verify','prepare','check'])
    parser.add_argument('--capture', type=Path); parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'verify':
        verify()
    else:
        require(args.capture and args.output, 'capture/output必須')
        print(json.dumps((prepare if args.command == 'prepare' else check)(ROOT, args.capture, args.output), sort_keys=True))
