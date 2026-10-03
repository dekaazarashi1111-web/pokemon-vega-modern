#!/usr/bin/env python3
"""Restore exact accepted integration inputs; never alter original bytes or guards.

The current acceptance projector validates original ZIPs, not just a success flag.
Call this explicit input-recovery step before it in a fresh GitHub checkout.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import record_modernization_final_acceptance as record

ROOT=Path(__file__).resolve().parents[1]
REPO='dekaazarashi1111-web/pokemon-vega-modern'


def install(path:Path, raw:bytes, expected=None):
    record.need(not any(p.is_symlink() for p in (path,*path.parents)),'symlink recovery target')
    if expected is not None:record.need(record.identity(raw)==expected,'recovery input identity differs: '+path.name)
    if path.exists():
        record.need(path.is_file() and path.read_bytes()==raw,'refuse original overwrite: '+path.name)
        return False
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw)
    return True


def fetch(endpoint):
    result=subprocess.run(['gh','api',f'repos/{REPO}/{endpoint}'],check=True,capture_output=True,timeout=180)
    record.need(len(result.stdout)<8_000_000,'recovery input too large')
    return result.stdout


def restore(root=ROOT,get=fetch):
    target=root/record.DIRECTORY
    restored=0
    for name,suffix in [('actions-run.json',''),('actions-jobs.json','/jobs?per_page=100'),('actions-artifacts.json','/artifacts?per_page=100')]:
        path=target/name
        if path.exists():record.read(root,path.relative_to(root))
        else:restored+=install(path,get(f'actions/runs/{record.RUN}'+suffix))
    for name,(aid,size,sha) in record.ARTIFACTS.items():
        path=target/(name+'.zip');expected={'size':size,'sha256':sha}
        raw=record.read(root,path.relative_to(root)) if path.exists() else get(f'actions/artifacts/{aid}/zip')
        restored+=install(path,raw,expected)
    # Existing strict verifier checks metadata, every ZIP/member/process/source,
    # the exact Stage84 hash and the intentionally limited acceptance scope.
    receipt=record.build(root)
    if (root/record.RECEIPT).exists():
        record.need(record.same(record.load(record.read(root,record.RECEIPT)),receipt),'tracked receipt differs from originals')
    return {'status':'PASS','source_run_id':record.RUN,'restored_files':restored,'verified_artifacts':9,
            'originals_overwritten':0,'new_emulator_runs':0,'release_ready':False}

if __name__=='__main__':
    try:print(json.dumps(restore(),sort_keys=True))
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print('restore integration originals: '+str(error),file=sys.stderr);raise SystemExit(1)
