#!/usr/bin/env python3
"""完了済み記録runの外部終端を確定。native/compile/unitを再実行しない。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_lifecycle_actions as d
from pr16_learnset_compact_record import publish_resume
need,identity=d.need,d.identity
START='24f8bbeb9440c7ed6a9d765ece157ada0ca62781'
SOURCE='22ace1e6c69aa5b488a2c83bd4468ddb5dcaa581'
RUN,JOB,ART=36317871935,108615900385,10931352419
TASK='USER-20260927-RESEARCH-NATURAL-SPENDING'
SELF='scripts/pr16_research_natural_spending_terminal.py'
WF='.github/workflows/pr16-research-natural-spending-terminal.yml'
CP='content/modernization/pr16_research_natural_spending_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_NATURAL_SPENDING_JA.md'
RESULT='content/modernization/pr16_research_natural_spending_terminal.json'
OWNED={CP,GUIDE,RESULT,d.STATE,d.DOC}|d.LOGS
CODE={SELF,WF}
OUT=ROOT/'.local/pr16-natural-terminal'

def record():
    d.current();s=d.read(ROOT/d.STATE);cp=d.read(ROOT/CP)
    need(not (ROOT/RESULT).exists() and cp['actions_completion_confirmed'] is False,'no duplicate terminal recording')
    need(cp['source_head']==SOURCE and cp['recording_run_id']==RUN
         and cp['status']=='PASS_NATURALLY_EARNED_RP_SPENDING_AND_SHOP_UI_SCOPED','exact accepted checkpoint')
    need(d.bindings(set(s['source_bindings']))==s['source_bindings'],'all existing resume sources unchanged')
    for label in ('source_bindings','protected_bindings'):
        need(d.bindings(set(cp[label]))==cp[label],'original '+label)
    run=d.inputs.api('actions/runs/'+str(RUN));job=d.inputs.api('actions/jobs/'+str(JOB))
    need(run['head_sha']==SOURCE and run['run_attempt']==1 and run['head_branch']=='codex/modernization-followup-20260908'
         and run['path']=='.github/workflows/pr16-research-natural-spending-record.yml'
         and run['status']=='completed' and run['conclusion']=='success','run terminal')
    need(job['run_id']==RUN and job['head_sha']==SOURCE and job['status']=='completed' and job['conclusion']=='success','job terminal')
    required={'Verify complete UTF-8 source and original text transfer','Verify original local native evidence without replay',
              'Task graph resume and final scoped index','Non-force scoped completion commit','Text-only completion context',
              'Run actions/upload-artifact@v4'}
    steps={v['name']:v for v in job['steps']}
    need(required<=set(steps) and all(steps[n]['status']=='completed' and steps[n]['conclusion']=='success' for n in required),'all completion steps succeeded')
    artifact=d.inputs.api('actions/artifacts/'+str(ART))
    need(not artifact['expired'] and artifact['workflow_run']['id']==RUN and artifact['workflow_run']['head_sha']==SOURCE
         and artifact['size_in_bytes']==1274341 and artifact['digest']=='sha256:f8fe2da54f623ad5afb03450a135b7fc2f068c1028887023b96a94bb8c524270','fixed completion artifact')
    old=[]
    for pending in s['pending_runs']:
        r=d.inputs.api('actions/runs/'+str(pending['run_id']))
        need(r['status']=='completed' and r['head_sha']==pending['tested_head'],'previous run terminal/source mismatch');old.append(d.run_summary(r))
    # The current job only records an already completed result. It is not a new native acceptance run.
    latest=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=15')['workflow_runs']
    receipt=dict(schema_version=1,status='PASS_EXTERNAL_TERMINAL_RECONCILIATION',record_commit=START,
        source_head=SOURCE,recording_run=d.run_summary(run),recording_job={k:job[k] for k in ('id','run_id','head_sha','status','conclusion','steps')},
        artifact={k:artifact[k] for k in ('id','name','size_in_bytes','digest','workflow_run')},
        previous_pending_runs=old,latest_actions=[d.run_summary(r) for r in latest],
        new_native_processes=0,new_arm_compiles=0,new_host_compiles=0,new_unit_executions=0,
        accepted_case_reruns=0,actions_completion_confirmed=True,natural_story_progress_accepted=False,
        geographic_route_from_earning_to_shop_accepted=False,release_ready=False,active_baseline_changed=False,
        terminal_writer=dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),status_at_record='in_progress',role='record_only_not_new_acceptance'))
    OUT.mkdir(parents=True,exist_ok=True);d.write(ROOT/RESULT,receipt)
    cp.update(actions_completion_confirmed=True,external_terminal_receipt=RESULT,recording_run_terminal='completed/success',
              actions_completion_semantics='recording run externally confirmed completed/success; original native venue remains local, not Actions native')
    d.write(ROOT/CP,cp)
    with (ROOT/GUIDE).open('a',encoding='utf-8') as f:
        f.write('\n## 外部からの終端確定\n\n完了commit `'+START+'`。記録run36317871935/job108615900385の全必須stepとartifactをcompleted/successで確認。旧pending runもAPIで照合済み。正本 `'+RESULT+'`。今回の追記は記録だけで、native/compile/120unit/23patchの再実行は0。上の「次の読取で確定」は記録時点の説明として残し、現在は終端確定済み。一般CIは実際のconclusionを保持する。通常ストーリー・採掘地点から研究所への自然移動は未受入のまま。\n')
    s['research_natural_spending']['actions_completion_confirmed']=True
    s['research_natural_spending']['terminal_receipt']=RESULT
    s['pending_runs']=[]
    s['observed_head']=START
    s['observed_head_semantics']='検証済み完了commit24f8bbeb。記録run36317871935はcompleted/successを外部照合済み。現終端writerは新受入/実測でない記録専用。'
    s['observed_head_checks']=dict(scope_head=SOURCE,runs=old,reason_ja='前回の全pendingを終端照合。記録runはsuccess。一般CIの実際のconclusionを保持し、すべてsuccessとは主張しない。')
    s['last_external_terminal']=dict(path=RESULT,accepted_record_commit=START,run_id=RUN,job_id=JOB,status='completed',conclusion='success')
    s['do_not_repeat'].insert(0,'自然RP支出の記録run36317871935終端と全必須stepはsuccess確定。24f8bbebの120検証/23patch/5開発native/最終12画面を再実行せず次の通常進行境界へ進む。')
    for p in CODE|{CP,GUIDE,RESULT}:s['source_bindings'][p]=identity((ROOT/p).read_bytes())
    s['logs_synchronized']=True;publish_resume(s)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    text=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 外部Actions終端確定\n- Version: research-natural-spending-terminal-v1\n- Status: DONE（自然RP支出/shop UI限定。通常進行は次の未完境界）\n- Summary: 完了commit {START}、run{RUN}/job{JOB}の全必須step successと固定artifactを外部APIで確認。全旧pendingを終端化し、固定引継ぎMD/JSON/専用checkpointを同期。\n- Verify: 新native/ARM/host/unitと旧受入再実行は0。全既存source/protected binding不変、task graph/resume/final-index guard後だけcommit。一般CIやhistorical guard全成功を主張しない。\n- Commit: source={os.environ["GITHUB_SHA"]}; terminal writer={os.environ["GITHUB_RUN_ID"]}; 同branch非force。自己SHAはremoteで確認。\n- Files changed: 終端記録器/Actions、終端JSON/checkpoint/専用MD、固定引継ぎMD/JSON、両ログ追記。\n- Network: GitHub PR/run/job/artifact metadataのみ。artifact再download、入力ROM/save再生成、merge/release/baseline変更なし。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(text)
    d.write(OUT/'summary.json',receipt);print('PASS: completed recording run reconciled; no native or unit replay')

def guard():
    d.current()
    import pr16_resume
    import pr16_learnset_runtime_record as g
    pr16_resume.validate(ROOT);g.START=START;g.OWNED=OWNED;g.CODE=CODE;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)

def snapshot():
    with zipfile.ZipFile(OUT/'context.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        m=dict(source_head=d.git('rev-parse','HEAD').decode().strip(),files={})
        for p in sorted(OWNED|CODE):
            raw=d.git('show','HEAD:'+p);raw.decode('utf-8');need(b'\0' not in raw,'text snapshot')
            z.writestr(p,raw);m['files'][p]=identity(raw)
        z.writestr('context-manifest.json',json.dumps(m,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(sorted(OWNED)))
    elif sys.argv[1:]==['snapshot']:snapshot()
    else:raise SystemExit('record|guard|paths|snapshot')
