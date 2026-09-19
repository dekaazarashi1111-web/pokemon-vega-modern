#!/usr/bin/env python3
"""中断消失のload/save呼出元を固定HEADのtracked sourceへ結び付ける。"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_load_order.py'
TEST='tests/test_pr16_circus_load_order.py'
WORKFLOW='.github/workflows/pr16-circus-load-order.yml'
REPORT='content/modernization/pr16_circus_load_order.json'
TASK='USER-20260919-CIRCUS-LOAD-ORDER'
OUT=ROOT/'.local/pr16-circus-load-order'
PATTERN=re.compile(r'SaveLoad|SaveWrite|Factory.*Recover|Recover.*Factory|[Ss]ave[_ -]?[Aa]dapter|0[xX]09405[dD]81|0[xX]9405[dD]81')


def allowed(name):
    p=PurePosixPath(name)
    return (not p.is_absolute() and '..' not in p.parts and len(p.parts)>1
        and p.parts[0] in {'scripts','tools','overlays','src','tests'} and p.suffix in {'.c','.h','.py','.S','.s'}
        and not any(x.lower() in {'private','vendor','upstream','.local','build'} for x in p.parts))


def selected(name,raw):
    if not allowed(name):return False
    if len(raw)>1024*1024 or b'\0' in raw:raise ValueError('invalid tracked text')
    text=raw.decode('utf-8')
    return bool(PATTERN.search(text) or name.startswith('overlays/circus_streak/')
                or name.startswith('overlays/save_migration/'))


def run():
    import pr16_resume as resume
    import pr16_circus_loss_followup as r
    r.scope();state=resume.validate(ROOT)
    if (ROOT/REPORT).exists():raise ValueError('source audit already recorded; consume its artifact instead')
    prior=resume.load(ROOT,'content/modernization/pr16_circus_three_win.json')
    if prior['recording_run']!=35421235529 or prior['input_policy_id']!='toxic-drain-v1':raise ValueError('current predecessor differs')
    current=r.api('actions/runs/35421235529')
    if current['status']!='completed' or current['conclusion']!='failure':raise ValueError('predecessor not completed failure')
    names=r.command('git','ls-files').splitlines();members={};matches=[];total=0
    for name in names:
        if not allowed(name):continue
        p=ROOT/name
        if p.is_symlink():raise ValueError('symlink source')
        raw=p.read_bytes()
        if not selected(name,raw):continue
        total+=len(raw)
        if total>24*1024*1024:raise ValueError('source audit budget exceeded')
        target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        members['source/'+name]=r.identity(raw)
        hits=[dict(line=i,text=line) for i,line in enumerate(raw.decode().splitlines(),1) if PATTERN.search(line)]
        matches.append(dict(path=name,identity=r.identity(raw),matches=hits))
    if len(members)<5:raise ValueError('save/load consumers missing')
    value=dict(schema_version=1,classification='CIRCUS_COLD_BOOT_LOAD_ORDER_SOURCE_BOUND_NATIVE_REPAIR_PENDING',
        source_head=r.command('git','rev-parse','HEAD'),source_files=len(members),source_bytes=total,matches=matches,
        original_trace_run=35420622910,latest_three_win_run=35421235529,latest_three_win_conclusion='failure',
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0,native_processes_executed=0,
        scope_ja='cold boot owner64未ロードの間にSave counter2→3→4。raw観測と固定sourceのload/save呼出順を結合。3勝は2勝1敗で未完、ここで成功へ改作しない。',
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    value['host_tests']=r.tests([Path(TEST).name]);(ROOT/REPORT).write_bytes(r.stable(value))
    loss=resume.load(ROOT,r.REPORT);loss['load_order_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.TASK=TASK
    r.checkpoint(state,loss,'cold bootのowner64消失と通常交代修復を原本に固定。既存load/save連鎖のtracked sourceをhash付きで収集し、初期化前の自動保存を修復する。',
        'load順序修復をC契約と2独立ARM linkで検証し、影響する中断復旧・保存だけをnative検証。実3勝/9BPは未完のまま保持。',
        [SELF,TEST,WORKFLOW,REPORT],'SOURCE-BOUND','source抽出の境界テストとresume/task graph/private新規差分guard。native再実行0。')
    for name in (REPORT,resume.STATE,resume.DOC,r.REPORT,'design/run_log.md','design/version_log.md',SELF,TEST,WORKFLOW):
        raw=(ROOT/name).read_bytes();p=OUT/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);members['source/'+name]=r.identity(raw)
    (OUT/'members.json').write_bytes(r.stable(members))


if __name__=='__main__':run()
