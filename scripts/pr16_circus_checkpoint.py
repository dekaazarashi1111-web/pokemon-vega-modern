#!/usr/bin/env python3
"""Circus限定工程の共通source-only記録。検証/投影は各工程の厳密契約に委譲する。"""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_circus_checkpoint.py'
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from pr16_circus_identity import need,identity,stable,strict


def run(task):
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    import pr16_circus_record as evidence
    import pr16_circus_first_record as first
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'record write scope')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout');ops.assert_remote(head)
    subprocess.run(['git','merge-base','--is-ancestor',task.BASE,head],cwd=ROOT,check=True)
    need(not (ROOT/task.REPORT).exists() and not ops.cmd('git','status','--porcelain','--untracked-files=no'),'already recorded/dirty')
    state=resume.validate(ROOT);backlog=strict((ROOT/resume.BACKLOG).read_bytes());task.OUT.mkdir(parents=True,exist_ok=True)
    protected={p:identity((ROOT/p).read_bytes()) for p in (resume.CHECKPOINT,*task.PROTECTED)}
    spec=task.SPEC
    verified=evidence.verify_actions(spec,ops.api('actions/runs/'+str(spec['run_id'])),ops.api('actions/jobs/'+str(spec['job_id'])),ops.api('actions/artifacts/'+str(spec['artifact_id'])),ops.REPO,ops.BRANCH)
    raw=subprocess.check_output(['gh','api','repos/'+ops.REPO+'/actions/artifacts/'+str(spec['artifact_id'])+'/zip'],cwd=ROOT)
    files,manifest=first.unpack(raw,spec['artifact_identity']);native,analysis=task.verify_files(files)
    evidence.tests_pass(files[task.TEST_RESULT],task.NATIVE_TESTS)
    for name,bound in native['sources'].items():
        p=Path(name);need(not p.is_absolute() and '..' not in p.parts,'unsafe source binding')
        need(identity(task.source_bytes(name))==bound,'native source changed: '+name)
    for name,bound in native['build_recipe']['sources'].items():need(identity((ROOT/name).read_bytes())==bound,'builder source changed')
    report=task.make_report(native,analysis,files)
    report.update(schema_version=1,task=task.TASK,tested_head=spec['tested_head'],native_run_id=spec['run_id'],record_head=head,
        record_run_id=int(os.environ['GITHUB_RUN_ID']),verified_actions=verified,artifact_spec=spec,member_manifest=manifest,
        new_emulator_processes_in_record=0,accepted_native_cases_replayed=0,next_ja=task.NEXT)
    for name,member in task.RAW.items():
        p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(files[member])
    report['original_text']={n:identity((ROOT/n).read_bytes()) for n in task.RAW}
    s,b=task.project(state,backlog,report)
    for key in ('candidate','status','latest_native_run','latest_native_job','latest_native_tested_head','last_accepted_native_run','last_accepted_native_tested_head','release_ready','remaining_physical_gap_ids','remaining_p08_gate_ids'):
        need(s[key]==state[key],'formal acceptance authority changed: '+key)
    for old,new in zip(backlog['remaining_conditions'],b['remaining_conditions']):
        if old['id']!='PHYSICAL_CIRCUS_ADMISSION':need(old==new,'unrelated backlog changed')
    need(len(backlog['remaining_conditions'])==len(b['remaining_conditions']),'backlog membership changed')
    s['observed_head']=head;s['observed_date_jst']=datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    s['observed_head_semantics']='Circus限定工程の記録source HEAD。実native tested HEADは工程checkpointに固定。正式BP受入HEADは維持。'
    recent=ops.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')['workflow_runs']
    s['observed_head_checks']=dict(scope_head=head,scoped_native=verified,recent=[{k:v[k] for k in ('id','head_sha','path','status','conclusion')} for v in recent],
        initial_head_checks=state['observed_head_checks'].get('initial_head_checks'),
        reason_ja=task.CHECK_REASON+' 記録runはcommit時実行中。開始HEAD通常CI2件はaction_required。全CI green/全受付受入とは主張しない。')
    s['session_execution_summary']=dict(new_emulator_processes=task.SESSION_NATIVE,record_emulator_processes=0,accepted_standalone_replays=0,scope_ja=task.SESSION_SCOPE)
    s['pending_runs']=[];s['logs_synchronized']=True
    (ROOT/task.REPORT).write_bytes(stable(report));(ROOT/resume.BACKLOG).write_bytes(stable(b))
    for name in (*task.IMPL,task.REPORT,*task.RAW):s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    (ROOT/resume.STATE).write_bytes(stable(s));(ROOT/resume.DOC).write_text(resume.render(s),encoding='utf-8');resume.validate(ROOT)
    tests=[]
    for pattern in (Path(task.TEST).name,'test_pr16_resume.py'):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (task.OUT/(pattern+'.txt')).open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(result.wasSuccessful() and result.testsRun>0 and not result.skipped,'record/resume tests')
        tests.append(dict(pattern=pattern,count=result.testsRun,success=True))
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    outputs=(task.REPORT,*task.RAW,resume.STATE,resume.DOC,resume.BACKLOG,*ops.LOGS);stamp=datetime.now(timezone.utc).isoformat()
    log=(f'\n\n## {stamp} — {task.TASK}\n- Timestamp: {stamp}\n- Task: {task.TASK}\n- Status: DONE / '+task.DONE_SCOPE+'\n'
        '- Version: '+task.VERSION+'\n- Summary: '+task.STOP+'\n- Files changed: '+', '.join((*task.IMPL,*outputs))+'\n'
        '- Verify: '+task.VERIFY+' 原本ZIP/member/source/process/stdout/stderrを照合。記録/再開tests、task graph、最終index差分guard、diff checkをcommit前必須。\n'
        '- Evidence: '+task.REPORT+f'; run{spec["run_id"]}/job{spec["job_id"]}; tested HEAD='+spec['tested_head']+f'; artifact{spec["artifact_id"]} SHA256='+spec['artifact_identity']['sha256']+'。\n'
        '- Boundary: '+task.BOUNDARY+' physical1/P08 gates2/release_ready=falseを維持。\n'
        '- Commit: 本工程の検証/記録を同branchへ非force commit。自己SHAはremote ref/receipt。\n'
        '- Network: GitHub connector/Actions。記録工程は既存artifactのみ、ROM生成/private復元/native起動なし。ROM/save/credentialを新規追跡しない。既存full guard違反は前後一致・新規違反0と区別。merge/release/baseline変更なし。\n- Next: '+task.NEXT+'\n')
    for name in ops.LOGS:
        need(task.TASK not in (ROOT/name).read_text(),'completion already logged')
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(log)
    need(protected=={p:identity((ROOT/p).read_bytes()) for p in protected},'accepted/historical checkpoint changed')
    subprocess.run(['git','add','--',*task.IMPL,*outputs],cwd=ROOT,check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=task.BASE,task.OUT,set((*task.IMPL,*outputs));guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);ops.assert_remote(head)
    for k,v in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):subprocess.run(['git','config',k,v],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',task.TASK+': '+task.COMMIT_SUMMARY],cwd=ROOT,check=True)
    commit=ops.cmd('git','rev-parse','HEAD');subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True);ops.assert_remote(commit,attempts=12)
    for name in (*task.IMPL,*outputs):need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed output differs')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'tracked changes after push');resume.validate(ROOT)
    receipt=dict(status=task.RECEIPT_STATUS,commit=commit,source_head=head,run_id=int(os.environ['GITHUB_RUN_ID']),native_run_id=spec['run_id'],tests=tests,
        record_emulator_processes=0,accepted_native_cases_replayed=0,physical_admission_accepted=False,release_ready=False)
    (task.OUT/'receipt.json').write_bytes(stable(receipt));(task.OUT/'completion-log.txt').write_text(log)
    for name in (task.REPORT,resume.STATE,resume.DOC,resume.BACKLOG):
        p=task.OUT/'final'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    print(json.dumps(receipt,ensure_ascii=False));print('RESULT=DONE TASK='+task.TASK+' VERIFY=PASS COMMIT='+commit)
