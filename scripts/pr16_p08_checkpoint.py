#!/usr/bin/env python3
"""P08限定原本・再開点・両ログを非force保存。既存byteをtrimしない。"""
from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_circus_battle25 as b
import pr16_p08_ring_recovery as e
need=e.need
SELF='scripts/pr16_p08_checkpoint.py'


def save(report,value,files,out,phase,stop,next_id,next_step,read_paths):
    """native成功と正式受入を分離し、原本byte/index/HEADを読戻す。"""
    b.OUT=out;head=b.scope();state=b.resume.validate(ROOT)
    task=value['task'];run=int(os.environ['GITHUB_RUN_ID'])
    need(phase in ('START','FINISH','ACCEPT'),'checkpoint phase')
    need(value['release_ready'] is False and value['rom_changes']==0,'checkpoint scope')
    value.update(recording_run=run,recording_source_head=head,phase=phase)
    folder='evidence/pr16_p08/'+task.lower()+'/'+str(run)+'/'+phase.lower()+'/'
    originals={}
    for path in sorted((out/'execution').glob('*')):
        if path.is_file():
            originals[path.name]=e.envelope(path.read_bytes())
            need(e.unwrap(originals[path.name])==path.read_bytes(),'execution byte roundtrip')
    paths=[]
    if originals:
        path=folder+'execution.json';b.write(path,e.stable(originals));paths.append(path)
    snapshot=folder+'result.json';b.write(snapshot,e.stable(value));paths.append(snapshot)
    b.write(report,e.stable(value));paths.insert(0,report)
    backlog=b.load(b.resume.BACKLOG)
    final=next(x for x in backlog['remaining_conditions'] if x['id']=='FINAL_NATIVE_ACCEPTANCE')
    need(final['candidate_sha256']==value['candidate']['sha256'],'target drift')
    if value.get('representative_accepted'):
        need(phase=='ACCEPT' and value.get('native_verified') is True
             and value.get('visual_review_completed') is True,'unverified acceptance')
        complete=set(final.get('completed_representative_regression_ids',[]));complete.add(value['regression_id'])
        final['completed_representative_regression_ids']=[x for x in final['required_representative_regression_ids'] if x in complete]
    final['remaining_representative_regression_ids']=[x for x in final['required_representative_regression_ids']
        if x not in final.get('completed_representative_regression_ids',[])]
    final.setdefault('representative_evidence',{})[value['regression_id']]=report
    final.update(resume=next_step,status='REPRESENTATIVE_BOUNDARIES_PROGRESS_RECORDED')
    b.write(b.resume.BACKLOG,e.stable(backlog));paths.append(b.resume.BACKLOG)
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='本checkpoint直前のremote。native実測・記録job完了・正式受入を別々に保持する。'
    state['observed_head_checks']=dict(scope_head=head,run_id=run,phase=phase,
        native_verified=value.get('native_verified',False),reason_ja='本run完了は次にActionsで別照合する。')
    state['pending_runs']=[dict(run_id=run,tested_head=value['workflow_source_head'],status='in_progress')]
    state.setdefault('p08_representatives',{})[value['regression_id']]=dict(path=report,run_id=run,phase=phase,
        native_verified=value.get('native_verified',False),representative_accepted=value.get('representative_accepted',False))
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=next_step
    state['next_action'].update(id=next_id,read_paths=list(dict.fromkeys([report,*read_paths,b.resume.BACKLOG])),stop_rule_ja=next_step)
    state['session_execution_summary']={k:value.get(k,0) for k in ('new_emulator_processes','fresh_cores','arm_compiles','arm_links','accepted_standalone_replays','prefix_wins_reexecuted')}
    state['session_execution_summary']['scope_ja']='変更影響のあるP08代表境界のみ。旧受入の独立再実行とROM変更なし。'
    state['remaining_sequence_ja']='P08未完代表境界 → 最終候補移送 → clean-ROM独立生成/配布準備判断。公開・merge・baseline切替は別指示。'
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    for path in (*files,*paths):state['source_bindings'][path]=e.identity((ROOT/path).read_bytes())
    b.write(b.resume.STATE,e.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    _,_,proc=b.capture([sys.executable,'scripts/validate_task_graph.py'],'task-graph-'+phase)
    need(b.exited(proc)==0,'task graph failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ');paths += [b.resume.STATE,b.resume.DOC,*b.LOGS]
    status='DONE' if value.get('native_verified') else ('IN_PROGRESS' if phase=='START' else 'STOPPED')
    entry=('\n\n## '+stamp+' — '+task+'-'+phase+'\n- Timestamp: '+stamp+'\n- Task: '+task+'-'+phase+
        '\n- Status: '+status+'\n- Version: pr16-p08-representative-v1\n- Summary: '+stop+
        '\n- Files changed: '+', '.join((*files,*paths))+
        '\n- Verify: 限定契約/resume/生成MD/hash/task graph、原本byte包絡とindex/HEAD読戻し。native件数・成否は'+report+'。'+
        '\n- Boundary: ARM0、旧受入の独立再実行0、ROM変更0。全体private guard既存違反は差分照合し全体PASSと主張しない。'+
        '\n- Commit: このcommitを同branchへ非force pushしremote読戻し。\n- Network: GitHub固定run/job/artifactとremote照合。\n- Next: '+next_step+'\n')
    for path in b.LOGS:
        need('— '+task+'-'+phase not in (ROOT/path).read_text(),'duplicate checkpoint log')
        with (ROOT/path).open('a') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines());need(changed and changed<=set(paths),'staged scope')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=head,out,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    for path in paths:need(subprocess.check_output(['git','show',':'+path],cwd=ROOT)==(ROOT/path).read_bytes(),'index readback')
    b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',task+': '+phase+' 原本byte・検証境界・再開点を同期'],cwd=ROOT,check=True)
    commit=b.command('git','rev-parse','HEAD')
    for path in paths:need(subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT)==(ROOT/path).read_bytes(),'HEAD readback')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    need(b.scope()==commit and not b.command('git','status','--porcelain','--untracked-files=no'),'remote/clean mismatch')
    (out/('receipt-'+phase+'.json')).write_bytes(e.stable(dict(task=task,phase=phase,commit=commit,non_force_push=True,run_id=run)))
    print('RESULT='+status+' TASK='+task+' VERIFY=PASS COMMIT='+commit)


def pack(out,files):
    dst=out/'artifact';dst.mkdir(parents=True,exist_ok=True)
    for src in sorted(out.rglob('*')):
        if not src.is_file() or dst in src.parents or any(p in src.relative_to(out).parts for p in ('work','original')):continue
        if src.suffix not in ('.json','.stdout','.stderr','.txt','.ppm'):continue
        raw=src.read_bytes()
        if src.suffix=='.ppm':need(raw.startswith(b'P6\n240 160\n255\n') and len(raw)==115215,'screen format')
        else:raw.decode();need(b'\0' not in raw,'nontext artifact')
        path=dst/src.relative_to(out);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    for name in files:
        path=dst/'source'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
