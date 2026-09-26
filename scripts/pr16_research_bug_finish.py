#!/usr/bin/env python3
"""受入後の補助export失敗を終端同期。51unit/2native/compileの再実行なし。"""
from __future__ import annotations
import datetime
import io
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_lifecycle_actions as d
from pr16_learnset_compact_record import publish_resume
need,identity=d.need,d.identity
TASK='USER-20260927-RESEARCH-ACTIVITIES'
START='5e428c2f09c14d4cf65b10c9da78d39ca47f8277'
OLD_RUN=36262152385
WF='.github/workflows/pr16-research-activities-20260927.yml'
SELF='scripts/pr16_research_bug_finish.py'
CP='content/modernization/pr16_research_bug_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_BUG_JA.md'
EVIDENCE='content/modernization/pr16_research_bug_evidence/closeout'
OUT=Path('.local/pr16-research-bug-finish');PUBLIC=OUT/'public'


def finish():
    os.chdir(ROOT);d.current();PUBLIC.mkdir(parents=True)
    cp=d.read(CP);need(cp['bug_accepted'] and cp['actions_completion_confirmed'] and cp['record_run_id']==OLD_RUN and not cp.get('post_push_failure_reconciled'),'existing accepted scope, one closeout only')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'accepted evidence protected')
    for p,b in cp['source_bindings'].items():
        if p!=WF:need(identity(Path(p).read_bytes())==b,'native/unit sources unchanged '+p)
    need(cp['counts']['new_scoped_tests']==51 and cp['counts']['accepted_native_processes']==2,'original counted acceptance')
    manifest=d.read(cp['manifest']);need(d.bindings(manifest)==manifest,'all recorded text evidence immutable')
    unit=d.read(cp['unit']);need(unit['returncode']==0 and unit['passed']==51 and unit['failures']==0 and d.bindings(unit['source_bindings'])==unit['source_bindings'],'original 51 tests unchanged')
    run=d.inputs.api('actions/runs/'+str(OLD_RUN));jobs=d.inputs.api('actions/runs/'+str(OLD_RUN)+'/jobs?per_page=100')
    need(run['head_sha']=='826fa3d262bd1a45dd7058a2e5bdf9aa0fcb06d2' and run['path']==WF and run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1,'retain original red workflow')
    need(jobs['total_count']==len(jobs['jobs'])==1,'one original job')
    steps=jobs['jobs'][0]['steps'];need([s['number'] for s in steps if s['conclusion']!='success']==[7],'only post-push export failed')
    need(all(s['conclusion']=='success' for s in steps if s['number'] in (3,4,5,6,8,9)),'native record/unit/guard/commit/push/artifact steps succeeded')
    meta=d.inputs.api('actions/artifacts/10912812143')
    need(meta['digest']=='sha256:fa60fb2f8010aa23b1bf3ffd02451437c2e12c283daa37f8d32658aad12c7d7f' and meta['size_in_bytes']==8675 and meta['workflow_run']['id']==OLD_RUN,'fixed closeout original metadata')
    raw=d.inputs.api('actions/artifacts/10912812143/zip',True)
    need(identity(raw)==dict(size=8675,sha256=meta['digest'].split(':')[1]),'fixed closeout original ZIP')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist())==9 and len(set(z.namelist()))==9 and all('/' not in e.filename and e.file_size<100000 for e in z.infolist()),'bounded flat proof files')
        need(z.read('unit.json')==Path(cp['unit']).read_bytes(),'identical successful unit receipt')
        proof=d.m.old.load(z.read('guard.json'))
    need(proof['status']=='PASS_SCOPED_FINAL_INDEX' and len(proof['changed_paths'])==21 and proof['new_private_violations']==0 and not proof['full_historical_guard_pass_claimed'],'original full-task guard receipt')
    receipt=dict(status='PASS_POST_PUSH_FAILURE_RECONCILED',accepted_commit=START,original_run=d.run_summary(run),original_jobs=jobs['jobs'],original_guard=proof,
        failure_ja='run36262152385のstep7のみ失敗。commit/push後にremote refは5e428c2fを確認済みだが、直後のPR API head一致検査で停止。HEAD反映遅延と整合するが、旧runをsuccessへ書き換えない。',
        resolution_ja='context輸出を次run冒頭の変更前HEADへ移動。現在ref/PRが同じことを確認し、受入試験/commitの再実行は禁止。',
        source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),unit_reruns=0,native_reruns=0,compiles=0)
    target=EVIDENCE+'/record-workflow-result.json';d.write(target,receipt);d.write(PUBLIC/'record-workflow-result.json',receipt)
    snapshot=Path('.local/pr16-research-activities/context/context.zip')
    need(snapshot.is_file(),'current clean-HEAD context export precedes synchronization')
    with zipfile.ZipFile(snapshot) as z:
        idx=d.m.old.load(z.read('index.json'));need(idx['source_head']==os.environ['GITHUB_SHA'],'new exported source HEAD')
        need(all(identity(z.read(p))=={'size':v['size'],'sha256':v['sha256']} for p,v in idx['files'].items()),'all current context hashes')
    cp.update(post_push_failure_reconciled=True,record_workflow_result=target,context_export_recovery=dict(source_head=os.environ['GITHUB_SHA'],binding=identity(snapshot.read_bytes()),files=len(idx['files'])),
              closeout_source_head=os.environ['GITHUB_SHA'],closeout_run_id=int(os.environ['GITHUB_RUN_ID']),closeout_execution=dict(unit_reruns=0,native_reruns=0,compiles=0))
    cp['source_bindings'][WF]=identity(Path(WF).read_bytes());cp['source_bindings'][SELF]=identity(Path(SELF).read_bytes());d.write(CP,cp)
    with Path(GUIDE).open('a') as f:f.write('\n## 受入commit後の補助処理の終端\n\n受入commit `'+START+'` は51検査・resume/task graph・今回18path/全作業21path guard・非force pushまで成功。記録run36262152385はその直後の補助context exportだけがPR APIのHEAD不一致で失敗した。旧runはfailureとして保存し、成功へ読み替えない。次run冒頭のclean HEADでcontext exportを実行し、原本・unit receipt・全変更guardを再利用して終端同期。unit/native/compile再実行0。`'+target+'` を参照。\n')
    state=d.read(d.STATE)
    ids={x['run_id'] for x in state['pending_runs']};old_pending=[d.run_summary(d.inputs.api('actions/runs/'+str(i))) for i in sorted(ids)]
    latest=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=24')['workflow_runs']
    checkfile=EVIDENCE+'/latest-actions.json';checks=dict(prior_pending=old_pending,runs=[d.run_summary(r) for r in latest]);d.write(checkfile,checks)
    state['research_bug'].update(post_push_failure_reconciled=True,record_workflow_result=target,closeout_source_head=os.environ['GITHUB_SHA'])
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='虫取り受入commit5e428c2f後の補助export失敗を再実測0で終端同期したsource。測定source5412cee1/run36261672837と分離。自己commit SHAはgit log参照。'
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=checks['runs'],reconciliation=checkfile,
        reason_ja='虫取りnative run36261672837成功、受入51検査/guard/push成功。記録run36262152385は後段context exportだけ失敗として保存し、次run冒頭へ移して修復。既存P03等の一般CI失敗/承認待ちとは別。全CI成功/merge/releaseは主張しない。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in latest if r['status'] in ('queued','in_progress') and r['id']!=int(os.environ['GITHUB_RUN_ID'])]
    for p in (WF,SELF,CP,GUIDE):state['source_bindings'][p]=identity(Path(p).read_bytes())
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 虫取り受入後の補助export終端\n- Version: research-bug-v1-closeout\n- Status: DONE（限定scope）\n- Summary: 受入commit5e428c2fの51検査/guard/非force pushを保全。旧記録run36262152385はpost-push context exportだけfailure。clean HEAD冒頭へ移動し原因と終端を明記。\n- Files changed: finish helper/workflow、虫取りcheckpoint/guide/終端JSON、固定引継ぎMD・JSON、両ログ。\n- Verify: 元51unit/2native/3cores/host1原本と21path guardをhash再利用。unit/native/compile再実行0。旧失敗step7を隠さない。現在HEAD context exportの全hash、commit前resume/task graph/scoped index guard。\n- Commit: accepted={START}、closeout source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log参照、同branch非force push。\n- Network: GitHub ref/PR/Actions原本のみ。元ROM/seed/旧受入/baseline不変。残4活動/自然到達/受付ショップ接続・全CI・releaseは未受入。\n'
    for p in d.LOGS:
        with Path(p).open('a') as f:f.write(log)
    d.write(OUT/'owned.json',sorted({CP,GUIDE,d.STATE,d.DOC,target,checkfile}|d.LOGS))


def guard():
    need(d.bindings(d.read(CP)['protected_bindings'])==d.read(CP)['protected_bindings'],'protected evidence unchanged')
    owned=set(d.read(OUT/'owned.json'));subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    g.START=START;g.CODE={SELF,WF};g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)
    d.write(PUBLIC/'summary.json',dict(status='PASS_BUG_CLOSEOUT',source_head=os.environ['GITHUB_SHA'],accepted_commit=START,new_tests=0,native_runs=0,compiles=0,changed=sorted(owned|{SELF,WF})))


if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['finish']:finish()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('finish | guard')
