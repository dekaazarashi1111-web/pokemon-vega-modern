#!/usr/bin/env python3
"""保存済みbindingから未実行境界だけ再開。既存ログ・ROM・ARM成功を再実行しない。"""
from copy import deepcopy
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_drought_launch_boundary as boundary
need,identity,stable=boundary.need,boundary.identity,boundary.stable
SELF='scripts/pr16_circus_boundary_continue.py'
TEST='tests/test_pr16_circus_boundary_continue.py'
WORKFLOW='.github/workflows/pr16-circus-boundary-continue.yml'
BINDING='content/modernization/pr16_circus_drought_launch_boundary_binding.json'
BASE='c96d14f8342fef6a99f349fa9cdbafea9020f8ad'
PRIOR_RUN=35450224019
PRIOR_JOB=105915967201
PRIOR_HEAD='602abf6c601c39e3f912cde24c84d58ac960220a'
FILES=(SELF,TEST,WORKFLOW,BINDING,'scripts/pr16_circus_drought_launch_boundary.py','tests/test_pr16_circus_drought_launch_boundary.py')
if not hasattr(boundary,'_continue_original_configure'):
    boundary._continue_original_configure=boundary.configure
_original_configure=boundary._continue_original_configure
_provenance=None


def task_for_run(run):
    need(type(run) is str and run.isascii() and run.isdecimal() and int(run)>0,'invalid run identity')
    return 'USER-20260920-CIRCUS-BOUNDARY-CONTINUE-RUN'+run


def prior_result(run,jobs,binding):
    need(run.get('id')==PRIOR_RUN and run.get('head_sha')==PRIOR_HEAD and run.get('status')=='completed'
         and run.get('conclusion')=='failure','prior run differs')
    rows=jobs.get('jobs');need(jobs.get('total_count')==1 and isinstance(rows,list) and len(rows)==1,'prior jobs differ')
    job=rows[0];need(job.get('id')==PRIOR_JOB and job.get('conclusion')=='failure','prior job differs')
    steps={s['number']:s['conclusion'] for s in job.get('steps',[])}
    need(steps.get(3)=='success' and steps.get(4)=='failure' and all(steps.get(i)=='skipped' for i in range(5,9)),
         'prior execution boundary differs')
    need(binding.get('recording_run')==PRIOR_RUN and binding.get('parent_loss_reference_bound') is True
         and binding.get('classification')=='CIRCUS_DROUGHT_BOUNDARY_SOURCE_BINDING_RECONCILED','binding checkpoint differs')
    return dict(run_id=PRIOR_RUN,job_id=PRIOR_JOB,head_sha=PRIOR_HEAD,checkpoint_commit=BASE,
        original_conclusion='failure',binding_checkpoint_succeeded=True,native_processes=0,
        reason_ja='binding checkpointは成功。次のprepareが旧PREPAREDタグと衝突して停止。native/pipeline/finishは未実行。既存記録を保持し新run固有タグで未完部分だけ進む。')


def configure():
    boundary.SELF=SELF;boundary.TEST=TEST;boundary.WORKFLOW=WORKFLOW
    boundary.TASK=task_for_run(os.environ.get('GITHUB_RUN_ID','1'))
    base,d,b=_original_configure()
    d.FILES=tuple(dict.fromkeys((*d.FILES,*FILES)));d.c.FILES=d.FILES
    return base,d,b


def record(value,phase,stop,next_step=boundary.NEXT):
    import pr16_resume as resume
    _,d,b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    if _provenance is not None:
        value['resume_setup_failure']=deepcopy(_provenance)
        value['actions_reconciled'].append(dict(id=PRIOR_RUN,head_sha=PRIOR_HEAD,status='completed',conclusion='failure'))
    need('resume_setup_failure' in value,'missing continuation provenance')
    value['independent_arm_links_replayed']=0
    if phase=='RECORDED':
        native=boundary.OUT/'native/report.json'
        if native.exists():value['native_attempt']=json.loads(native.read_bytes())
        if not value.get('diagnostic_complete'):
            stop='境界診断は未完。今回試行の原本だけを保存し、採取済みやnative受入とは扱わない。'
            next_step='今回runのnative_attempt/失敗原本から最初の未完原因だけを修復する。旧binding成功と受入済み単体と旧ARM linkは再実行しない。'
    (ROOT/boundary.REPORT).write_bytes(stable(value))
    ref=dict(path=boundary.REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_drought_launch_boundary']=loss['drought_launch_boundary']=ref
    state['circus_continuous_followup']=dict(ref,target_wins=30)
    state['prior_actions_reconciled']=value['actions_reconciled']
    note=f'run{PRIOR_RUN}/job{PRIOR_JOB}: binding保存{BASE[:7]}は成功、旧タグ再利用のprepareは失敗/native0。既存ログ削除・成功binding単独再実行・旧ARM再linkをせず、run固有タグで未採取境界のみ進める。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=boundary.HEADER;r.TASK=boundary.TASK
    r.checkpoint(state,loss,stop,next_step,[boundary.REPORT,*d.FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。新run固有タグ/親binding原本を検証。保存patch再構成・ARM再link0・受入単体再実行0。readonly境界とnative受入を区別。')


def prepare():
    global _provenance
    import pr16_resume as resume
    _,_,b=configure();r=b.rec;head=r.scope()
    need(r.command('git','rev-parse','HEAD^')==BASE,'continuation parent moved')
    changed=r.command('git','diff','--name-only',BASE,head).splitlines()
    need(set(changed)=={SELF,TEST,WORKFLOW},'continuation source scope differs')
    state=resume.validate(ROOT)
    need(all(path not in state['source_bindings'] for path in (SELF,TEST,WORKFLOW)),'continuation already bound')
    _provenance=prior_result(r.api('actions/runs/'+str(PRIOR_RUN)),r.api('actions/runs/'+str(PRIOR_RUN)+'/jobs'),resume.load(ROOT,BINDING))
    boundary.prepare()


def restore_candidate(raw,recipe,actual):
    """保存patchだけを適用。原本sourceの不一致を黙って再bindしない。"""
    from pr16_circus_streak import bounded_patch
    need(identity(raw)==recipe['parent'],'saved candidate parent differs')
    for name,meta in recipe['source_bindings'].items():need(identity(actual[name])==meta,'saved candidate source differs: '+name)
    new=bounded_patch(raw,recipe['patches'])
    need(identity(new)==recipe['candidate'],'saved candidate identity differs')
    for row in recipe['allocation']['allocations']:
        need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'saved allocation differs')
    return new


def reconstruct():
    _,d,b=configure();d.c.f.reconstruct()
    import pr16_streak_native as n
    prior=json.loads((ROOT/boundary.PRIOR).read_bytes());recipe=deepcopy(prior['build'])
    raw=(n.INPUT/'candidate.gba').read_bytes()
    new=restore_candidate(raw,recipe,{p:(ROOT/p).read_bytes() for p in recipe['source_bindings']})
    need(identity(new)==prior['candidate'],'launch candidate differs')
    recipe['source_bindings'].update({p:identity((ROOT/p).read_bytes()) for p in d.FILES})
    recipe['inherited_independent_arm_links']=recipe['independent_arm_links'];recipe['independent_arm_links']=0
    recipe['independent_old_arm_links_replayed']=0
    recipe['reconstruction_source']=dict(path=boundary.PRIOR,recording_run=prior['recording_run'],candidate_unchanged=True)
    boundary.OUT.mkdir(parents=True,exist_ok=True)
    (boundary.OUT/'build.json').write_bytes(stable(recipe))
    (boundary.OUT/'reconstruction.json').write_bytes(stable(dict(candidate=identity(new),rom_changes=0,arm_links_replayed=0,
        source_recipe=identity(stable(prior['build'])),source_binding_count=len(prior['build']['source_bindings']),all_allocations_verified=True)))
    (n.INPUT/'candidate.gba').write_bytes(new);(n.INPUT/'report.json').write_bytes(stable(recipe))
    print('SAVED_CANDIDATE_RECONSTRUCTED=PASS ARM_LINKS_REPLAYED=0')


def main():
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    boundary.configure=configure;boundary.record=record
    configure()
    if action=='prepare':prepare()
    elif action=='reconstruct':reconstruct()
    elif action=='native':boundary.native()
    elif action=='finish':boundary.finish()
    elif action=='pipeline':configure()[2].pipeline()
    elif action=='pack':configure()[1].c.f.pack()
    else:raise SystemExit('unknown command')


if __name__=='__main__':main()
