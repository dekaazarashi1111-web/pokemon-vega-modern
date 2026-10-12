#!/usr/bin/env python3
"""残る2地点の配置資料だけをhash付きで取り出す。ROM/既受入試験は実行しない。"""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import re
import sys
import traceback
import zipfile
import pr16_selected_pla1_reader as m
import pr16_wiki_r0_reconcile_actions as a

ROOT = Path(__file__).resolve().parents[1]
BASE = '7e6c9c986ccc55cf852b09e3e91888cc90278562'
BRANCH = 'codex/modernization-followup-20260908'
CODE = {'scripts/pr16_selected_asset_owner_catalog_actions.py','.github/workflows/pr16-selected-asset-owner-catalog.yml'}
PUBLIC = ROOT/'.local/pr16-selected-asset-owner-catalog/public'
TASK = 'USER-20261012-SELECTED-ASSET-OWNER-CATALOG'


def run():
    m.need(os.environ.get('GITHUB_REPOSITORY') == a.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/'+BRANCH
           and os.environ.get('GITHUB_RUN_ATTEMPT') == '1' and not PUBLIC.parent.exists(), '固定branch初回')
    head = a.git('rev-parse','HEAD').decode().strip()
    m.need(head == os.environ['GITHUB_SHA'] and set(a.git('diff','--name-only',BASE,head).decode().splitlines()) == CODE
           and not a.git('status','--porcelain','--untracked-files=no').strip(), '新catalog2fileだけ')
    PUBLIC.mkdir(parents=True)
    state = json.loads((ROOT/'content/modernization/pr16_wiki_first_execution_plan.json').read_bytes())
    m.need(state['next_action']['id'] == 'SAVE_CAPACITY_IPS_AND_DPE_ASSET_READERS','固定next')
    tracked = a.git('ls-files','--','config','scripts','pipeline','lib','src','state/source-lock.json').decode().splitlines()
    names = []
    for name in tracked:
        if name in CODE or Path(name).suffix not in ('.py','.json','.h','.c','.ld','.s','.S'):
            continue
        p = ROOT/name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 1000000:
            continue
        raw = p.read_bytes()
        if b'\0' in raw:
            continue
        text = raw.decode('utf-8')
        if re.search(r'dpe_payload|DPE-JP',text) or 'dpe' in Path(name).name.lower() or name == 'state/source-lock.json':
            names.append(name)
    m.need(0 < len(names) <= 200, '限定配置source数')
    all_names = a.git('ls-files','--','config','scripts','content/modernization','state').decode().splitlines()
    dpe_paths = [n for n in all_names if 'dpe' in n.lower()]
    bindings = {}
    with zipfile.ZipFile(PUBLIC/'owner-source-context.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in sorted(names):
            raw = (ROOT/name).read_bytes()
            m.need(raw == a.git('show',head+':'+name), 'tracked原本一致')
            bindings[name] = m.identity(raw)
            info = zipfile.ZipInfo(name,(2026,10,12,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,raw)
    result = dict(schema_version=1,task=TASK,status='READ_ONLY_OWNER_SOURCE_CATALOG',source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=bindings,dpe_related_paths=dpe_paths,
        candidate_reconstructions=0,accepted_tests_rerun=0,accepted_measurements_rerun=0,formal_classification_changes=0,
        donor_safe_bytes=0,actual_asset_reader_proven=False)
    (PUBLIC/'owner-source-index.json').write_bytes(m.encode(result))
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(), 'tracked不変')
    print('OWNER_SOURCE_PATHS='+json.dumps(names,ensure_ascii=False))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT=-')


if __name__ == '__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        (PUBLIC/'failure.json').write_bytes(m.encode(dict(status='NOT_ACCEPTED',type=type(exc).__name__,
            frames=[dict(file=Path(f.filename).name,line=f.lineno) for f in traceback.extract_tb(exc.__traceback__) if '/scripts/' in f.filename])))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL TYPE='+type(exc).__name__)
        sys.exit(1)
