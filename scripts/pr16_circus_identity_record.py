#!/usr/bin/env python3
"""成功した個体追跡原本をsource-onlyで固定する。受入やROMを再実行しない。"""
from __future__ import annotations
import copy
from datetime import datetime,timezone,timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_identity as trace
import pr16_circus_first_record as first
need,identity,stable,load=trace.need,trace.identity,trace.stable,trace.strict
BASE='d3dfddc4b15d7dad9b0bd6733f865ed8e8cb16bb'
TASK='USER-20260919-CIRCUS-IDENTITY'
SELF='scripts/pr16_circus_identity_record.py'
TEST='tests/test_pr16_circus_identity_record.py'
WORKFLOW='.github/workflows/pr16-circus-identity-record.yml'
REPORT='content/modernization/pr16_circus_identity_checkpoint.json'
OUT=ROOT/'.local/pr16-circus-identity-record'
RAW=('evidence/pr16_circus_identity/original.stdout.txt','evidence/pr16_circus_identity/original.stderr.txt')
IMPL=(trace.SELF,trace.TEST,trace.WORKFLOW,SELF,TEST,WORKFLOW)
SPEC=dict(run_id=35378203102,job_id=105707865018,tested_head='3b967ba55ff6914263787a2273b7346faecf3792',
    workflow=trace.WORKFLOW,conclusion='success',artifact_id=10561465516,name='pr16-circus-identity',with_manifest=True,
    artifact_identity=dict(size=376771,sha256='085f33b1f5510a6281e0d85b541089d0d84a90df99e080955586c5877144f945'),
    required_success_steps=['個体継承契約20件のみ検証','受入済み候補を同SHAへ再構成しnativeは再実行しない',
        '個体bytesを限定観測し初戦ターン前で停止','ROM save credentialを除外して限定原本と修復用sourceを保持','Run actions/upload-artifact@v4'])
STOP=('個体追跡run35378203102で原因を限定。初回確定1311f→第2確認1782fの選択3体300bytesは完全一致。'
      '正規sp072→戦闘初期化の1936fに全3枠が0化され、3336fの実戦では別PID/speciesへ置換された。'
      'scriptはCircus初戦continuation 0x09FF4D16。既存retentionはFactory継続2scriptのみでCircusを除外している。'
      '新規1process/1core、7書込barrier、35限定event、警告0。初戦ターン/取消保存/Factory入口は再実行0。'
      '診断完了であり個体保持・固有連勝・30連勝抑制は未受入。')
NEXT=('保存した個体追跡を再実行せず、既存Factory predicateの返値を非該当時に保持するCircus専用wrapperを実装する。'
      '固定候補99cc0948のretention trampoline literalだけを検証付きで新wrapperへ接続し、'
      '3つのCircus launch continuation/marker/pending/facility番号で限定する。新候補で選択個体の実戦保持を検証。'
      'その後、Circus固有streakの正規勝敗更新・保存復帰・30連勝以上の来歴と正規sp072特性抑制へ進む。'
      'Factory連勝の代用、効果/施設番号/連勝/party/PC/LRのhost注入は禁止。'
      '無変更の初戦1ターン/取消保存/Factory入口/Ring/BP/P03/P06/P07/旧7関数/5335root走査を再実行しない。')


def verify_files(files):
    prefix='pr16-circus-identity/';stem=prefix+trace.CASE
    r=load(files[prefix+'report.json']);a=load(files[prefix+'identity.json'])
    need(r['source_head']==SPEC['tested_head'] and r['candidate']==dict(size=33554432,sha256=trace.SHA),'identity head/candidate')
    need(r['status']=='PASS_CIRCUS_SCOPED_NATIVE' and r['failures']==[] and r['requested_cases']==[trace.CASE],'identity run scope')
    need(r['guard_checks']==first.GUARDS and r['actual_new_processes']==r['successful_fresh_cores']==1 and r['accepted_native_cases_replayed']==0,'identity accounting')
    need(len(r['results'])==1,'exactly one observation required')
    row=r['results'][0];proc=load(files[stem+'.process.json'])
    need(proc==dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None) and proc==row['process'],'identity process')
    result=trace.validate(files[stem+'.stdout'],files[stem+'.stderr'],proc['returncode'],trace.CASE)
    need(row['result']==result,'identity stdout projection')
    events=trace.parse_events(files[stem+'.stderr']);derived=trace.analyze(events)
    need(load(files[prefix+'events.json'])==events and all(a[k]==v for k,v in derived.items()),'identity derivation differs')
    need(a['run_id']==SPEC['run_id'] and a['tested_head']==SPEC['tested_head'] and a['raw_stderr']==identity(files[stem+'.stderr']),'identity evidence binding')
    need(derived['classification']=='CIRCUS_RENTALS_REPLACED_AT_BATTLE_INIT' and derived['selected_to_second_all_300_bytes_equal'] is True,'diagnostic boundary moved')
    need(derived['event_count']==35 and derived['first_changed_event']['frame']==1936 and derived['action']['frame']==3336,'bounded trace changed')
    for key in ('physical_admission_accepted','suppression_accepted','release_ready'):need(r[key] is False and a[key] is False,'unproved acceptance')
    for name,bound in row['screens'].items():need(identity(files[prefix+name])==bound,'screen identity differs')
    for guard in first.GUARDS:
        g=prefix+'guard-'+guard
        need(load(files[g+'.process.json'])==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None),'write guard process')
        need(files[g+'.stdout']==b'' and files[g+'.stderr']==b'P03 archive: host write after observation barrier\n','write guard raw result')
    return r,a


def project(state,backlog,report):
    s,b=copy.deepcopy(state),copy.deepcopy(backlog)
    need(report['classification']=='CIRCUS_RENTALS_REPLACED_AT_BATTLE_INIT' and report['physical_admission_accepted'] is False,'diagnostic cannot close physical gate')
    rows=[r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION']
    need(len(rows)==1 and rows[0]['success_evidence'] is None,'physical authority changed')
    rows[0].update(implementation_checkpoint=REPORT,implementation_status=report['classification'],resume=NEXT)
    s['circus_rental_identity']=dict(path=REPORT,status=report['classification'],run_id=SPEC['run_id'],tested_head=SPEC['tested_head'],
        engineering_candidate=report['candidate'],diagnostic_complete=True,rental_identity_verified=False,physical_admission_accepted=False)
    s['bp']['current_stop']=s['source_change_review_ja']=STOP;s['bp']['next_step']=s['next_action']['goal_ja']=NEXT
    s['next_action']['id']='CIRCUS_SCOPED_RETENTION_REPAIR'
    s['next_action']['read_paths']=[REPORT,trace.SELF,'overlays/facility_party_retention/facility_party_retention.c',
        'scripts/pr16_bp_party_retention_successor.py','scripts/pr16_circus_entry.py','content/modernization/p08_remaining_work.json']
    s['remaining_sequence_ja']='個体追跡は保存済み→Circus限定保持修復→固有連勝の正規更新/永続化と30連勝抑制→影響範囲P08移送→release判定。'
    note='run35378203102の個体追跡は35event/3336framesで完了。初回選択→第2確認300bytes一致、1936fの戦闘初期化で全3枠を消去/再抽選。旧候補の同一診断を再実行せず、保持修復した後継候補へ進む。初戦ターンは再実行していない。'
    if note not in s['do_not_repeat']:s['do_not_repeat'].insert(0,note)
    return s,b


def run():
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    import pr16_circus_record as evidence
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'write scope')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout');ops.assert_remote(head)
    need(not (ROOT/REPORT).exists() and not ops.cmd('git','status','--porcelain','--untracked-files=no'),'record exists or tracked changes')
    resume.validate(ROOT);state=load((ROOT/resume.STATE).read_bytes());backlog=load((ROOT/resume.BACKLOG).read_bytes());OUT.mkdir(parents=True,exist_ok=True)
    protected={p:identity((ROOT/p).read_bytes()) for p in (resume.CHECKPOINT,first.REPORT,first.THUMB)}
    verified=evidence.verify_actions(SPEC,ops.api('actions/runs/'+str(SPEC['run_id'])),ops.api('actions/jobs/'+str(SPEC['job_id'])),ops.api('actions/artifacts/'+str(SPEC['artifact_id'])),ops.REPO,ops.BRANCH)
    raw=subprocess.check_output(['gh','api','repos/'+ops.REPO+'/actions/artifacts/'+str(SPEC['artifact_id'])+'/zip'],cwd=ROOT)
    files,manifest=first.unpack(raw,SPEC['artifact_identity']);r,a=verify_files(files)
    evidence.tests_pass(files['pr16-circus-identity-run/tests.stderr'],20)
    for name,bound in r['sources'].items():
        data=trace.instrument((ROOT/'tools/mgba_pr16_circus_native.c').read_text()).encode() if name=='.local/pr16-circus-identity-input.c' else (ROOT/name).read_bytes()
        need(identity(data)==bound,'original source changed: '+name)
    report=dict(schema_version=1,task=TASK,classification=a['classification'],candidate=r['candidate'],tested_head=SPEC['tested_head'],
        native_run_id=SPEC['run_id'],record_head=head,record_run_id=int(os.environ['GITHUB_RUN_ID']),verified_actions=verified,
        artifact_spec=SPEC,member_manifest=manifest,analysis=a,original_report=r,
        legacy_runner_scope_label_ja='original_report.scopeは旧helperの固定ラベル。実行ケース/原stdout/本分析が限定個体追跡を示す。初戦ターンは再実行していない。',
        diagnostic_complete=True,rental_identity_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        new_emulator_processes_in_record=0,accepted_native_cases_replayed=0,next_ja=NEXT)
    for dst,suffix in zip(RAW,('.stdout','.stderr')):
        p=ROOT/dst;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(files['pr16-circus-identity/'+trace.CASE+suffix])
    report['original_text']={n:identity((ROOT/n).read_bytes()) for n in RAW}
    s,b=project(state,backlog,report)
    s['observed_head']=head;s['observed_date_jst']=datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    s['observed_head_semantics']='個体追跡の記録source HEAD。実native tested HEADはCircus専用checkpointに固定。正式BP受入は維持。'
    recent=ops.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')['workflow_runs']
    s['observed_head_checks']=dict(scope_head=head,circus_identity=verified,recent=[{k:v[k] for k in ('id','head_sha','path','status','conclusion')} for v in recent],
        initial_head_checks=dict(head=BASE,runs=[dict(id=x,conclusion='action_required') for x in (35369093276,35369093259)]),
        reason_ja='個体追跡run35378203102/job105707865018は成功。開始HEAD通常CI2件はaction_required、記録runはcommit時実行中。全CI green/全受付受入とは主張しない。')
    s['session_execution_summary']=dict(new_emulator_processes=1,record_emulator_processes=0,accepted_standalone_replays=0,scope_ja='未確認だった個体継承だけ1件。初戦ターン前3336fで停止。')
    s['pending_runs']=[];s['logs_synchronized']=True
    (ROOT/REPORT).write_bytes(stable(report));(ROOT/resume.BACKLOG).write_bytes(stable(b))
    for name in (*IMPL,REPORT,*RAW):s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    (ROOT/resume.STATE).write_bytes(stable(s));(ROOT/resume.DOC).write_text(resume.render(s),encoding='utf-8');resume.validate(ROOT)
    tests=[]
    for pattern in (Path(TEST).name,'test_pr16_resume.py'):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (OUT/(pattern+'.txt')).open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(result.wasSuccessful() and result.testsRun>0 and not result.skipped,'record/resume tests')
        tests.append(dict(pattern=pattern,count=result.testsRun,success=True))
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    outputs=(REPORT,*RAW,resume.STATE,resume.DOC,resume.BACKLOG,*ops.LOGS);stamp=datetime.now(timezone.utc).isoformat()
    log=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Status: DONE / 個体置換原因の限定診断。保持修復は未完。\n'
         '- Version: pr16-circus-identity-diagnostic\n- Summary: '+STOP+'\n- Files changed: '+', '.join((*IMPL,*outputs))+'\n'
         '- Verify: 個体追跡契約20件PASS、7host-write guard、native原本1process/1core、35event/3336f、ZIP/member/source/process/stdout/stderr照合。記録/再開tests・task graph・最終index差分guard・diff checkをcommit前必須。\n'
         '- Evidence: '+REPORT+'; run35378203102/job105707865018; tested HEAD='+SPEC['tested_head']+'; artifact10561465516 SHA256='+SPEC['artifact_identity']['sha256']+'。原本の旧scopeラベルは改作せず実ケースと区別。表示名ではなく300bytes/PID/speciesを根拠とした。\n'
         '- Boundary: 初戦ターン/取消保存/Factory入口/旧7関数/5335root/Ring/BP/P03/P06/P07再実行0。ROM変更0、元受入checkpoint不変。physical1/P08 gates2/release_ready=false。\n'
         '- Commit: 本記録を同branchへ非force commit。自己SHAはremote ref/receiptに記録。\n'
         '- Network: GitHub connector/Actions原本のみ。記録工程はROM生成/private復元/native起動なし。ROM/save/credentialを追加しない。既存full guard違反は前後一致・新規違反0と区別。merge/release/baseline変更なし。\n- Next: '+NEXT+'\n')
    for name in ops.LOGS:
        need(TASK not in (ROOT/name).read_text(),'already logged')
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(log)
    need(protected=={p:identity((ROOT/p).read_bytes()) for p in protected},'accepted checkpoint changed')
    subprocess.run(['git','add','--',*IMPL,*outputs],cwd=ROOT,check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*IMPL,*outputs));guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);ops.assert_remote(head)
    for k,v in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):subprocess.run(['git','config',k,v],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': 選択300bytes一致と戦闘再抽選を原本照合し固定引継ぎへ記録'],cwd=ROOT,check=True)
    commit=ops.cmd('git','rev-parse','HEAD');subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True);ops.assert_remote(commit,attempts=12)
    for name in (*IMPL,*outputs):need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed output differs')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'tracked changes after push');resume.validate(ROOT)
    receipt=dict(status='PASS_CIRCUS_IDENTITY_RECORDED',commit=commit,source_head=head,run_id=int(os.environ['GITHUB_RUN_ID']),native_run_id=SPEC['run_id'],tests=tests,
        record_emulator_processes=0,accepted_native_cases_replayed=0,physical_admission_accepted=False,release_ready=False)
    (OUT/'receipt.json').write_bytes(stable(receipt));(OUT/'completion-log.txt').write_text(log)
    for name in (REPORT,resume.STATE,resume.DOC,resume.BACKLOG):
        p=OUT/'final'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    print(json.dumps(receipt,ensure_ascii=False));print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)

if __name__=='__main__':run()
