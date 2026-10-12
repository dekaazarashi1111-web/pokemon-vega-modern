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
RETRY_PARENT='3827258983b6a3a467af0ef584c408ae3bc4ef8b'
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
RENDER_HEAD='725bbe8bdcc2149870dd78ce55406243fd71c86e'
PATH_RUN=35439014239
PATH_JOB=105886489666
PATH_HEAD=RETRY_PARENT
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


def validate_reconcile_failure(run:dict,jobs:dict,artifacts:dict,run_id:int,job_id:int,head:str,reason:str)->dict[str,Any]:
    need(run.get('id')==run_id and run.get('head_sha')==head
        and run.get('status')=='completed' and run.get('conclusion')=='failure','reconcile run differs')
    rows=jobs.get('jobs');need(jobs.get('total_count')==1 and isinstance(rows,list) and len(rows)==1,'reconcile jobs differ')
    job=rows[0];need(job.get('id')==job_id and job.get('conclusion')=='failure','reconcile job differs')
    steps={row.get('number'):(row.get('name'),row.get('conclusion')) for row in job.get('steps',[])}
    need(steps.get(3)==('source binding差分を親HEADとblobで固定して先行保存','failure'),'reconcile failure step differs')
    for number in (4,5,6,7,8):need(steps.get(number,(None,None))[1]=='skipped','post-reconcile step unexpectedly ran')
    need(artifacts.get('total_count')==0 and artifacts.get('artifacts')==[],'reconcile run unexpectedly published artifact')
    return {'run_id':run_id,'job_id':job_id,'head_sha':head,'original_conclusion':'failure',
        'reconcile_failed':True,'native_processes':0,'accepted_native_cases_replayed':0,'artifacts':0,'reason_ja':reason}


def validate_render_run(run:dict,jobs:dict,artifacts:dict)->dict[str,Any]:
    return validate_reconcile_failure(run,jobs,artifacts,RENDER_RUN,RENDER_JOB,RENDER_HEAD,
        'source binding更新後に生成MDを先に同期せず厳格resume.validateを実行し、Markdown driftで停止。native/pipeline/finish/pack/artifactは未実行。')


def validate_path_run(run:dict,jobs:dict,artifacts:dict)->dict[str,Any]:
    return validate_reconcile_failure(run,jobs,artifacts,PATH_RUN,PATH_JOB,PATH_HEAD,
        'source binding/生成MDは整合したが、親loss JSONに参照を結び付けず不変だったためcheckpoint必須差分検査で停止。commit/push/native/artifactなし。')


def bind_checkpoint_reports(state:dict,loss:dict,ref:dict)->tuple[dict,dict]:
    """親正本にも意味のある参照を記録し、必須差分guardは変更しない。"""
    need(ref.get('path')==REPORT and ref.get('classification')=='CIRCUS_DROUGHT_BOUNDARY_SOURCE_BINDING_RECONCILED'
         and type(ref.get('run_id')) is int and ref['run_id']>0,'binding reference differs')
    state_copy=deepcopy(state);loss_copy=deepcopy(loss)
    need(loss_copy.get('drought_launch_boundary_binding')!=ref,'binding checkpoint already recorded')
    state_copy['circus_drought_launch_boundary_binding']=deepcopy(ref)
    loss_copy['drought_launch_boundary_binding']=deepcopy(ref)
    return state_copy,loss_copy


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
    runs=[];failures=[]
    for run_id,validator in ((STALE_RUN,validate_stale_run),(RENDER_RUN,validate_render_run),(PATH_RUN,validate_path_run)):
        run=r.api('actions/runs/'+str(run_id));jobs=r.api('actions/runs/'+str(run_id)+'/jobs')
        artifacts=r.api('actions/runs/'+str(run_id)+'/artifacts')
        runs.append(run);failures.append(validator(run,jobs,artifacts))
    state=resume.load(ROOT,resume.STATE)
    actual={path:(ROOT/path).read_bytes() for path in (BOUNDARY_SCRIPT,BOUNDARY_TEST)}
    additions={path:(ROOT/path).read_bytes() for path in NEW_FILES}
    state,changes=rebind(state,actual,additions)
    for failure in failures:
        note=f"run{failure['run_id']}/job{failure['job_id']}は前処理失敗/native0。"+failure['reason_ja']+' 同一失敗は再実行しない。'
        if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    ref={'path':REPORT,'classification':'CIRCUS_DROUGHT_BOUNDARY_SOURCE_BINDING_RECONCILED','run_id':int(os.environ['GITHUB_RUN_ID'])}
    loss=resume.load(ROOT,r.REPORT)
    state,loss=bind_checkpoint_reports(state,loss,ref)
    state['prior_actions_reconciled']=[{k:row[k] for k in ('id','head_sha','status','conclusion')} for row in runs]
    resume.dump(ROOT/resume.STATE,state)
    resume.safe_path(ROOT,resume.DOC).write_text(resume.render(state),encoding='utf-8')
    resume.validate(ROOT)
    value={'schema_version':1,'classification':ref['classification'],'recording_run':int(os.environ['GITHUB_RUN_ID']),
        'commit_scope':scope,'stale_binding_failure':failures[0],'render_sync_failure':failures[1],
        'checkpoint_path_failure':failures[2],'source_binding_changes':changes,
        'strict_resume_validation_after_rebind':True,'parent_loss_reference_bound':True,
        'native_processes':0,'accepted_native_cases_replayed':0,
        'independent_arm_links_replayed':0,'rom_or_save_evidence_published':False,'native_lifecycle_accepted':False,
        'standard_save_fresh_continue':False,'genuine_30_wins_verified':False,'physical_admission_accepted':False,
        'suppression_accepted':False,'release_ready':False}
    (ROOT/REPORT).write_bytes(stable(value))
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=boundary.HEADER;r.TASK=TASK
    r.checkpoint(state,loss,
        '境界script/testの旧source bindingをblob固定照合し、親loss JSONにも結果参照を結合。3件の前処理失敗をnative0のまま保存。必須差分guardは維持。',
        NEXT,[REPORT,SELF,TEST,WORKFLOW,BOUNDARY_SCRIPT,BOUNDARY_TEST],
        'RECORDED','source binding・生成MD・親loss参照を整合。限定host回帰と厳格resume validate、最終index guardを通過して非force保存。native0/ROM・save証跡0。')


def main()->None:
    need(len(sys.argv)==2 and sys.argv[1]=='reconcile','reconcile command required')
    reconcile()


if __name__=='__main__':main()
