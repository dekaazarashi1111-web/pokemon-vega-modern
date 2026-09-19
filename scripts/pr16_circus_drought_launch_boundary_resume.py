#!/usr/bin/env python3
"""境界診断scriptの意図したsource-binding差分だけを先行checkpointする。"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_drought_launch_boundary_resume.py'
TEST='tests/test_pr16_circus_drought_launch_boundary_resume.py'
WORKFLOW='.github/workflows/pr16-circus-drought-launch-boundary-resume.yml'
REPORT='content/modernization/pr16_circus_drought_launch_boundary_binding.json'
BOUNDARY_SCRIPT='scripts/pr16_circus_drought_launch_boundary.py'
BOUNDARY_TEST='tests/test_pr16_circus_drought_launch_boundary.py'
BASE_HEAD='1e43febe6da4e7ba74549a4905b8466da88bef3d'
RETRY_PARENT='725bbe8bdcc2149870dd78ce55406243fd71c86e'
BOUNDARY_BLOBS={
    BOUNDARY_SCRIPT:'823d241f654c999e247e69513ce727c9d589c323',
    BOUNDARY_TEST:'1709e29535063ec3de817c8331c47338ab513c50',
}
OLD_BINDINGS={
    BOUNDARY_SCRIPT:{'sha256':'a3b8ffe2a2c2d139b2fdbbbcc9e8bcf987755dab3c450856552ee7fa9e19427d','size':14439},
    BOUNDARY_TEST:{'sha256':'ccace74b3b7f9a73f44f2c9f64bdd0b7f61f8f5decfed903c6f6df612f98033b','size':3104},
}
STALE_RUN=35438563815
STALE_JOB=105885315243
STALE_HEAD=BASE_HEAD
RENDER_RUN=35438845025
RENDER_JOB=105886059983
RENDER_HEAD=RETRY_PARENT
TASK='USER-20260919-CIRCUS-DROUGHT-LAUNCH-BOUNDARY-BINDING'
NEXT='source bindingを厳格整合済みの同じ候補で、18戦目chooser→field落下のreadonly境界を1processだけ採取する。受入済み単体・旧CPU診断・旧独立2linkは再実行しない。'
NEW_FILES=(SELF,TEST,WORKFLOW)


def need(ok:Any,message:str)->None:
    if not ok:raise ValueError(message)


def identity(raw:bytes)->dict[str,Any]:
    return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def git_blob(raw:bytes)->str:
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def stable(value:Any)->bytes:
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def validate_commit_scope(head:str,parent:str,changed:list[str],added:list[str])->dict[str,Any]:
    need(len(head)==40 and all(c in '0123456789abcdef' for c in head),'invalid reconciliation HEAD')
    need(parent==RETRY_PARENT,'reconciliation retry parent drift')
    expected=sorted(NEW_FILES)
    need(sorted(changed)==expected,'reconciliation changed-file scope drift')
    need(sorted(added)==expected,'reconciliation files must be additions only')
    return {'source_head':head,'base_head':BASE_HEAD,'parent_head':parent,'changed_files':expected,'added_only':True}


def validate_stale_run(run:dict,jobs:dict,artifacts:dict)->dict[str,Any]:
    need(run.get('id')==STALE_RUN and run.get('head_sha')==STALE_HEAD
        and run.get('status')=='completed' and run.get('conclusion')=='failure','stale-binding run differs')
    rows=jobs.get('jobs');need(jobs.get('total_count')==1 and isinstance(rows,list) and len(rows)==1,'stale-binding jobs differ')
    job=rows[0];need(job.get('id')==STALE_JOB and job.get('conclusion')=='failure','stale-binding job differs')
    steps={row.get('number'):(row.get('name'),row.get('conclusion')) for row in job.get('steps',[])}
    need(steps.get(3)==('既存失敗原本とreadonly境界scopeを非force保存','failure'),'prepare failure step differs')
    for number in (4,5,6,7):need(steps.get(number,(None,None))[1]=='skipped','post-prepare step unexpectedly ran')
    need(artifacts.get('total_count')==0 and artifacts.get('artifacts')==[],'stale-binding run unexpectedly published artifact')
    return {'run_id':STALE_RUN,'job_id':STALE_JOB,'head_sha':STALE_HEAD,'original_conclusion':'failure',
        'prepare_failed':True,'native_processes':0,'accepted_native_cases_replayed':0,'artifacts':0,
        'reason_ja':'正本source_bindingsが意図した診断script変更を旧fingerprintとして検知し、prepareで停止。native/pipeline/finish/pack/artifactは未実行。'}


def validate_render_run(run:dict,jobs:dict,artifacts:dict)->dict[str,Any]:
    need(run.get('id')==RENDER_RUN and run.get('head_sha')==RENDER_HEAD
        and run.get('status')=='completed' and run.get('conclusion')=='failure','render-sync run differs')
    rows=jobs.get('jobs');need(jobs.get('total_count')==1 and isinstance(rows,list) and len(rows)==1,'render-sync jobs differ')
    job=rows[0];need(job.get('id')==RENDER_JOB and job.get('conclusion')=='failure','render-sync job differs')
    steps={row.get('number'):(row.get('name'),row.get('conclusion')) for row in job.get('steps',[])}
    need(steps.get(3)==('source binding差分を親HEADとblobで固定して先行保存','failure'),'render-sync failure step differs')
    for number in (4,5,6,7,8):need(steps.get(number,(None,None))[1]=='skipped','post-render-sync step unexpectedly ran')
    need(artifacts.get('total_count')==0 and artifacts.get('artifacts')==[],'render-sync run unexpectedly published artifact')
    return {'run_id':RENDER_RUN,'job_id':RENDER_JOB,'head_sha':RENDER_HEAD,'original_conclusion':'failure',
        'reconcile_failed':True,'native_processes':0,'accepted_native_cases_replayed':0,'artifacts':0,
        'reason_ja':'source binding更新後に生成MDを先に同期せず厳格resume.validateを実行し、Markdown driftで停止。native/pipeline/finish/pack/artifactは未実行。'}


def rebind(state:dict,actual:dict[str,bytes],additions:dict[str,bytes])->tuple[dict,dict[str,dict[str,Any]]]:
    value=deepcopy(state);bindings=value.get('source_bindings');need(isinstance(bindings,dict),'missing source bindings')
    changes={}
    for path in (BOUNDARY_SCRIPT,BOUNDARY_TEST):
        need(bindings.get(path)==OLD_BINDINGS[path],'old source binding differs: '+path)
        raw=actual[path];need(git_blob(raw)==BOUNDARY_BLOBS[path],'current Git blob differs: '+path)
        new=identity(raw);need(new!=OLD_BINDINGS[path],'source binding did not change: '+path)
        changes[path]={'before':OLD_BINDINGS[path],'after':new,'git_blob':BOUNDARY_BLOBS[path]}
        bindings[path]=new
    for path in NEW_FILES:
        need(path not in bindings,'reconciliation file already bound: '+path)
        raw=additions[path];bindings[path]=identity(raw)
        changes[path]={'before':None,'after':bindings[path],'git_blob':git_blob(raw)}
    return value,changes


def git_lines(*args:str)->list[str]:
    text=subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
    return [] if not text else text.splitlines()


def reconcile()->None:
    import pr16_resume as resume
    import pr16_circus_drought_launch_boundary as boundary
    _,_,b=boundary.configure();r=b.rec;r.scope()
    head=git_lines('rev-parse','HEAD')[0];parent=git_lines('rev-parse','HEAD^')[0]
    scope=validate_commit_scope(head,parent,git_lines('diff','--name-only',BASE_HEAD+'..HEAD'),
        git_lines('diff','--diff-filter=A','--name-only',BASE_HEAD+'..HEAD'))
    run=r.api('actions/runs/'+str(STALE_RUN));jobs=r.api('actions/runs/'+str(STALE_RUN)+'/jobs')
    artifacts=r.api('actions/runs/'+str(STALE_RUN)+'/artifacts')
    stale=validate_stale_run(run,jobs,artifacts)
    render_run=r.api('actions/runs/'+str(RENDER_RUN));render_jobs=r.api('actions/runs/'+str(RENDER_RUN)+'/jobs')
    render_artifacts=r.api('actions/runs/'+str(RENDER_RUN)+'/artifacts')
    render_failure=validate_render_run(render_run,render_jobs,render_artifacts)
    state=resume.load(ROOT,resume.STATE)
    actual={path:(ROOT/path).read_bytes() for path in (BOUNDARY_SCRIPT,BOUNDARY_TEST)}
    additions={path:(ROOT/path).read_bytes() for path in NEW_FILES}
    state,changes=rebind(state,actual,additions)
    note='run35438563815/job105885315243はsource binding旧fingerprint検知でprepare停止。native process 0、後続4step skipped、artifact 0。旧bindingをblob固定照合して先行checkpointした後だけ境界採取を再開する。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    render_note='run35438845025/job105886059983はsource binding更新後の生成MD未同期でreconcile停止。native process 0、後続5step skipped、artifact 0。state更新後にMD生成してから厳格validateする。'
    if render_note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,render_note)
    ref={'path':REPORT,'classification':'CIRCUS_DROUGHT_BOUNDARY_SOURCE_BINDING_RECONCILED','run_id':int(os.environ['GITHUB_RUN_ID'])}
    state['circus_drought_launch_boundary_binding']=ref
    state['prior_actions_reconciled']=[{k:row[k] for k in ('id','head_sha','status','conclusion')} for row in (run,render_run)]
    resume.dump(ROOT/resume.STATE,state)
    resume.safe_path(ROOT,resume.DOC).write_text(resume.render(state),encoding='utf-8')
    resume.validate(ROOT)
    value={'schema_version':1,'classification':ref['classification'],'recording_run':int(os.environ['GITHUB_RUN_ID']),
        'commit_scope':scope,'stale_binding_failure':stale,'render_sync_failure':render_failure,'source_binding_changes':changes,
        'strict_resume_validation_after_rebind':True,'native_processes':0,'accepted_native_cases_replayed':0,
        'independent_arm_links_replayed':0,'rom_or_save_evidence_published':False,'native_lifecycle_accepted':False,
        'standard_save_fresh_continue':False,'genuine_30_wins_verified':False,'physical_admission_accepted':False,
        'suppression_accepted':False,'release_ready':False}
    (ROOT/REPORT).write_bytes(stable(value))
    loss=resume.load(ROOT,r.REPORT)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=boundary.HEADER;r.TASK=TASK
    r.checkpoint(state,loss,
        '意図した境界script/testの旧source bindingだけをGit blob固定で更新。run35438563815とrun35438845025はsetup失敗/native0として保存し、ゲーム結果に数えない。',
        NEXT,[REPORT,SELF,TEST,WORKFLOW,BOUNDARY_SCRIPT,BOUNDARY_TEST],
        'RECORDED','CIRCUS_DROUGHT_BOUNDARY_SOURCE_BINDING_RECONCILED。親HEADと追加3ファイルを固定し、その他binding不変の厳格validateを再通過。native0/ROM・save証跡0。')


def main()->None:
    need(len(sys.argv)==2 and sys.argv[1]=='reconcile','reconcile command required')
    reconcile()


if __name__=='__main__':main()
