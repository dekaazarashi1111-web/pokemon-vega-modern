#!/usr/bin/env python3
"""交換個体追跡のActions原本だけを照合・記録。emulator実行なし。"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_exchange_identity as native
import pr16_bp_selection_native as launch
import pr16_resume as resume

TASK='USER-20260914-BP-EXCHANGE-IDENTITY'
ENTRY='565597ae307cb81f3b4878a6c58e278b5f9a9dfb'
TESTED='e9793dfda49ec3044b662aefd7bb0093182dce3a'
RUN=34774194505
JOB=103769160925
BRANCH='codex/modernization-followup-20260908'
SELF='scripts/pr16_bp_exchange_identity_record.py'
TEST='tests/test_pr16_bp_exchange_identity_record.py'
WORKFLOW='.github/workflows/pr16-bp-exchange-identity-record.yml'
EVIDENCE='content/modernization/pr16_bp_exchange_identity_evidence'
VERIFIED='content/modernization/pr16_bp_exchange_identity_verified.json'
OUT=ROOT/'.local/pr16-bp-exchange-identity-record'
LOGS=('design/run_log.md','design/version_log.md')
need=native.need

def stable(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def ident(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def git(*args,**kw):return subprocess.check_output(['git',*args],cwd=ROOT,**kw)
def api(path):return json.loads(subprocess.check_output(['gh','api','repos/'+os.environ['GITHUB_REPOSITORY']+'/'+path]))
def current():return api('git/ref/heads/'+BRANCH)['object']['sha']
def write(name,raw):
    p=resume.safe_path(ROOT,name);raw.decode('utf-8');need(b'\0' not in raw,'NUL in tracked text')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
def small(r):return {k:r[k] for k in ('id','name','head_sha','path','status','conclusion','event')}

def unpack(raw):
    out={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist())<256 and sum(i.file_size for i in z.infolist())<32000000,'artifact expansion bound')
        for info in z.infolist():
            name=info.filename;p=Path(name)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in name and name not in out,'unsafe/duplicate artifact path')
            need(not info.is_dir() and info.file_size<8000000,'artifact member bound')
            data=z.read(info)
            if p.suffix not in ('.zip','.ppm'):
                data.decode('utf-8');need(b'\0' not in data,'binary text artifact')
            out[name]=data
    return out

def verify_members(members):
    root='pr16-bp-exchange-identity/'
    receipt=native.strict(members[root+'receipt.json'])
    need(receipt['tested_head']==TESTED and receipt['status']==native.STATUS,'receipt identity')
    for name,meta in receipt['members'].items():
        need(ident(members[root+name])==meta,'artifact receipt member: '+name)
    r=native.strict(members[root+'result.json'])
    need(r['status']==native.STATUS and r['failures']==[] and r['actual_new_processes']==r['successful_fresh_cores']==1,'native process outcome')
    need(set(r['guard_checks'])=={'bus8','bus16','bus32','raw8','raw16','raw32','register'} and len(r['guard_checks'])==7,'seven barriers absent')
    for label in ('compile',native.CASE,*('guard-'+g for g in r['guard_checks'])):
        process=native.strict(members[root+label+'.process.json'])
        expected_code=1 if label.startswith('guard-') else 0
        need(process==dict(schema_version=1,returncode=expected_code,timed_out=False,spawn_error=None),'process/guard proof differs: '+label)
    row=native.strict(members[root+native.CASE+'.stdout'])
    old=launch.SHA
    try:
        launch.SHA=native.previous.SHA
        need(native.validate(members[root+native.CASE+'.stdout'],members[root+native.CASE+'.stderr'],0)==row,'raw validation')
    finally:launch.SHA=old
    need(r['results'][0]['result']==row,'report/raw result differs')
    analysis=native.analyze(members[root+native.CASE+'.stderr'],row)
    need(analysis==native.strict(members[root+'identity.json']),'identity derivation differs')
    for name,meta in r['sources'].items():need(ident((ROOT/name).read_bytes())==meta,'native source changed: '+name)
    with zipfile.ZipFile(io.BytesIO(members[root+'generated-controller.zip'])) as z:
        need(z.read('controller.c').decode()==native.assemble_controller(),'generated observer differs')
        for name,meta in r['generated'].items():need(ident(z.read(name))==meta,'generated source binding')
    oldrow=resume.load(ROOT,'content/modernization/pr16_bp_win_exchange_evidence/native-result.json')
    need({k:v for k,v in row.items() if k not in ('status','scope','case')}==
         {k:v for k,v in oldrow.items() if k not in ('status','scope','case')},'unchanged prefix/input frames diverged')
    return receipt,r,row,analysis

def record():
    OUT.mkdir(parents=True,exist_ok=False)
    head=git('rev-parse','HEAD',text=True).strip()
    need(head==os.environ['GITHUB_SHA']==current(),'concurrent record HEAD')
    s=resume.validate(ROOT);pr=api('pulls/16')
    need(pr['state']=='open' and pr['draft'] and not pr['merged'] and pr['head']['sha']==head,'PR boundary')
    run=api('actions/runs/'+str(RUN));job=api('actions/jobs/'+str(JOB))
    need(run['head_sha']==TESTED and run['status']=='completed' and run['conclusion']=='success' and run['path']==native.WORKFLOW,'native run identity')
    need(job['run_id']==RUN and job['conclusion']=='success','native job identity')
    latest=api('actions/workflows/pr16-bp-exchange-identity.yml/runs?branch=codex%2Fmodernization-followup-20260908&per_page=1')['workflow_runs']
    need(len(latest)==1 and latest[0]['id']==RUN,'newer native run must be reconciled')
    artifacts=api('actions/runs/'+str(RUN)+'/artifacts')['artifacts']
    found=[a for a in artifacts if a['name']=='pr16-bp-exchange-identity' and not a['expired']]
    need(len(found)==1,'native artifact unavailable')
    a=found[0];raw=subprocess.check_output(['gh','api','repos/'+os.environ['GITHUB_REPOSITORY']+'/actions/artifacts/'+str(a['id'])+'/zip'])
    need(ident(raw)==dict(size=a['size_in_bytes'],sha256=a['digest'].removeprefix('sha256:')),'download digest differs')
    members=unpack(raw);receipt,report,row,analysis=verify_members(members)
    root='pr16-bp-exchange-identity/'
    save={
        'native-result.json':members[root+native.CASE+'.stdout'],
        'native.stderr.txt':members[root+native.CASE+'.stderr'],
        'native-process.json':members[root+native.CASE+'.process.json'],
        'runner-result.json':members[root+'result.json'],
        'receipt.json':members[root+'receipt.json'],
        'identity.json':members[root+'identity.json'],
        'unit-tests.txt':members['pr16-bp-exchange-identity-run/unit.stderr'],
        'actions-before.json':members['pr16-bp-exchange-identity-run/actions-before.json'],
    }
    runs={}
    for sha in (ENTRY,TESTED,head):
        batch=api('actions/runs?head_sha='+sha+'&per_page=100')
        need(batch['total_count']==len(batch['workflow_runs']),'paged Actions metadata')
        runs[sha]=[small(v) for v in batch['workflow_runs']]
    preflight=api('actions/runs/34774090333')
    need(preflight['conclusion']=='failure' and preflight['head_sha']=='bffc355c66e86ebbbef701a8de1e87136b8d2fa5','preflight failure identity')
    save['actions.json']=stable(dict(heads=runs,native=small(run),preflight=dict(small(preflight),new_native_processes=0,artifact_id=10322588475,artifact_sha256='1aa106f4841dd7334447258858ea7f1eedc716d2ba1d6b658cf1a5007b1880c9',reason='historical failure was incorrectly required to be success; fixed before native execution')))
    for name,data in save.items():write(EVIDENCE+'/'+name,data)
    v=dict(schema_version=1,classification='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',run_id=RUN,job_id=JOB,tested_head=TESTED,
           original_conclusion='success',artifact_id=a['id'],artifact_zip=ident(raw),native_result=row,identity=analysis,
           sources=report['sources'],evidence_files={EVIDENCE+'/'+name:ident(data) for name,data in save.items()},
           accepted_native_cases_replayed=0,new_native_processes=1,rom_changes=0,
           native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
    write(VERIFIED,stable(v))
    retained=analysis['exchanged_individual_retained'] and analysis['all_three_individuals_retained']
    decision=('次戦まで交換個体と3個体の保持を確認。' if retained else '交換確定後から次戦までにparty個体が変化し、交換個体保持は不成立。')
    decision+=f" {analysis['snapshot_count']}個の同時600byte/個体snapshotを照合。交換確定{row['exchange_commit_frame']}f、次戦action{row['next_battle_action_frame']}f。"
    decision+=' PID/OT/species/movesを比較し、次戦active battlerと実partyの一致も検証。frame境界観測でありCPU関数entry/returnの証明ではない。'
    if not retained:
        change=analysis['first_changed'];need(change is not None,'missing replacement boundary')
        decision+=f" 次戦chooser{analysis['next_chooser']['frame']}fでは600byte一致。最初の変化は{change['frame']}f、callback2=0x{change['callback2']:08X}/script=0x{change['script']:08X}で3個体がゼロ。actionで88byte差・新規3個体を確認。保持修復は未完。"
    goal=('同一成功prefixを延長し、未観測の2/3戦目・3勝completionと正確なBP報酬を観測する。' if retained else
          '次戦初期化callback2=0x0800FEC5/script=0x092CF6A5のownerをsource/ABIと照合し、17755f保持→17770f消去→17786f新規3個体となる再生成を最小修復successorで防ぐ。保持確認前に2/3戦目・BP報酬へ進まない。')
    s.update(status=native.STATUS,observed_head=TESTED,latest_native_run=RUN,latest_native_job=JOB,latest_native_tested_head=TESTED,
             latest_native_evidence=VERIFIED,latest_native_scope='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',latest_native_summary_ja=decision,
             observed_head_semantics='今回のnative追跡を実行した固定source HEAD。記録commit/現在HEADはAPIで別途照合する。',
             observed_head_checks=dict(reason_ja=f'個体追跡run{RUN}/job{JOB} SUCCESS。事前照合停止run34774090333はfailure（native0）のまま保持。全Actionsは{EVIDENCE}/actions.json。全体CIやrelease受入を意味しない。'),
             pending_runs=[],logs_synchronized=True,p08_resume_synchronized=True)
    s['bp'].update(current_stop=decision,next_step=goal,next_battle_exchanged_individual_identity_verified=retained,
                   exchange_identity_audit_completed=True,next_battle_party_retained=retained,
                   after_battle_launch=decision+' BP稼得/消費、3勝、Save/fresh Continueの新規受入はしていない。')
    s['next_action'].update(id='BP_SECOND_THIRD_BATTLES_REWARD' if retained else 'BP_EXCHANGE_PARTY_RETENTION_REPAIR',
        goal_ja=goal,read_paths=[VERIFIED,EVIDENCE+'/identity.json',EVIDENCE+'/native.stderr.txt',native.SELF,native.SOURCE,
        'overlays/facility_runtime/facility_runtime.c','scripts/pr16_bp_exchange_successor.py'],
        success_observations=['交換個体を保持した次戦party/battler','native 2/3戦目と正確な3勝BP報酬'],
        stop_rule_ja='今回の読取専用診断・初勝利・交換の単独再実行はしない。新規修復/報酬ケースへ同一prefixを延長する時だけ使用する。取消Save/Continue等の受入済みケース、P03/P06/P07等は影響なしにつき再実行しない。')
    s['do_not_repeat'].append(f'個体追跡run{RUN}の原本を再利用。追跡完了と個体保持/BP受入を混同しない。')
    s['recording_workflow']=dict(run_id=int(os.environ['GITHUB_RUN_ID']),source_head=head,status_at_snapshot='in_progress',note_ja='記録workflowの終端/commitはAPIとartifact result.jsonで照合。native未完run0。')
    for name in (native.SELF,native.SOURCE,native.TEST,native.WORKFLOW,SELF,TEST,WORKFLOW,VERIFIED,EVIDENCE+'/identity.json'):
        s['source_bindings'][name]=ident((ROOT/name).read_bytes())
    b=resume.load(ROOT,resume.BACKLOG)
    b['next_integration_candidate'].update(scope='NATIVE_EXCHANGE_IDENTITY_DIAGNOSTIC_BP_PENDING',source_path=VERIFIED)
    for item in b['remaining_conditions']:
        if item['id'] in ('NATURAL_CAPTURE_GEAR','FINAL_NATIVE_ACCEPTANCE'):
            item['resume']='Current resume: '+resume.DOC+'. '+decision+' Next: '+goal
    write(resume.BACKLOG,stable(b));write(resume.STATE,stable(s))
    subprocess.run([sys.executable,'scripts/pr16_resume.py','render'],cwd=ROOT,check=True)
    from datetime import datetime,timezone
    stamp=datetime.now(timezone.utc).isoformat()
    note=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Version: PR16 exchange individual boundary audit\n'
          f'- Task: {TASK} / 次戦までの交換個体連鎖を読取専用で実装・検証・記録\n- Status: DONE\n'
          '- Summary: '+decision+'\n'
          f'- Native: run{RUN}/job{JOB}; source HEAD={TESTED}; candidate7f32/CRC0D5D9178。原本の全prefix/result frameはrun34770280751と同一。\n'
          '- Verify: 新規identity11tests、原本全member/source/生成C/7barrier/native結果の厳密照合。記録tests・resume tests・resume check・task graph・diff check・最終index guard差分を完了ゲートとする。\n'
          '- History: 事前照合run34774090333は過去loss-return原本をsuccessと誤指定して停止、native0。元failureを維持した比較へ修正。native主processは本task1、受入済みcase再実行0、ROM変更0。\n'
          '- Files changed: 新規identity runner/C/tests/workflow、記録script/tests/workflow、verified/evidence、固定引継ぎMD/JSON、P08診断resume、両ログ。\n'
          f'- Commit: この記録を含むcommit。入力HEAD={head}。非force push後のhashはworkflow result.jsonとremote refから読戻す。\n'
          '- Network: GitHub connector/APIでHEAD/PR/Actions/artifact照合。Actions内でpinned private inputsを再構築。追跡/記録成果は許可済み工程textのみ。\n'
          '- Boundary: 正式physical4/P08 gate2・BP未受入を維持。PR draft/open、baseline維持、merge/releaseなし。全体private guardの既存違反はbaseline/index差分として記録し全体PASSとはしない。\n'
          '- Next: '+goal+'\n')
    for name in LOGS:
        old=(ROOT/name).read_text();need(TASK not in old,'already recorded');write(name,(old+note).encode())
    check()

def check():
    v=resume.load(ROOT,VERIFIED);s=resume.validate(ROOT)
    need(v['run_id']==RUN and v['job_id']==JOB and v['tested_head']==TESTED and v['classification']=='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE','record identity')
    for name,meta in v['evidence_files'].items():need(ident((ROOT/name).read_bytes())==meta,'saved evidence differs')
    for name,meta in v['sources'].items():need(ident((ROOT/name).read_bytes())==meta,'saved native source differs')
    row=resume.load(ROOT,EVIDENCE+'/native-result.json')
    need(native.analyze((ROOT/(EVIDENCE+'/native.stderr.txt')).read_bytes(),row)==v['identity'],'saved analysis differs')
    need(row==v['native_result'] and s['bp']['exchange_identity_audit_completed'] is True,'saved native result differs')
    need(len(s['remaining_physical_gap_ids'])==4 and len(s['remaining_p08_gate_ids'])==2,'formal gaps changed')
    for k in ('native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready'):need(v[k] is False,'acceptance inflated')
    return v

def publish():
    v=check();head=git('rev-parse','HEAD',text=True).strip();need(head==os.environ['GITHUB_SHA']==current(),'concurrent publish HEAD')
    writes=set(v['evidence_files'])|{VERIFIED,resume.STATE,resume.DOC,resume.BACKLOG,*LOGS}
    actual=set(git('diff','--name-only',text=True).splitlines())|set(git('ls-files','--others','--exclude-standard',text=True).splitlines())
    need(actual==writes,'untracked/changed allowlist')
    for name in LOGS:need((ROOT/name).read_bytes().startswith(git('show',head+':'+name)),'append-only logs')
    git('add','--',*sorted(writes));git('diff','--cached','--check')
    need(set(git('diff','--cached','--name-only',text=True).splitlines())==writes,'index scope')
    with tempfile.TemporaryDirectory() as tmp:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(tmp)/'baseline.index'));git('read-tree',ENTRY,env=env)
        baseline=subprocess.run([sys.executable,'scripts/guard_private_files.py'],cwd=ROOT,env=env,capture_output=True)
    final=subprocess.run([sys.executable,'scripts/guard_private_files.py'],cwd=ROOT,capture_output=True)
    need(baseline.returncode in (0,1) and final.returncode==baseline.returncode and final.stdout==baseline.stdout and not baseline.stderr and not final.stderr,'new global private guard violations')
    import guard_private_files as guard
    for name in git('diff','--name-only',ENTRY,'--',text=True).splitlines():
        p=ROOT/name;raw=p.read_bytes();raw.decode('utf-8')
        need(not p.is_symlink() and b'\0' not in raw and p.suffix.lower() not in guard.BLOCKED_SUFFIXES,'private/nontext change')
        need(not any(name==x or name.startswith(x+'/') for x in guard.BLOCKED_PARTS),'private path change')
        need(not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',raw),'credential-like text')
        if p.suffix.lower() in guard.DOCUMENT_SUFFIXES:
            old=subprocess.run(['git','show',ENTRY+':'+name],cwd=ROOT,capture_output=True)
            need(guard.document_user_path_lines(raw)==guard.document_user_path_lines(old.stdout if old.returncode==0 else b''),'new machine path')
    boundary=dict(baseline_head=ENTRY,returncode=final.returncode,whole_guard_passed=final.returncode==0,new_violations=0,stdout=ident(final.stdout))
    (OUT/'guard-boundary.json').write_bytes(stable(boundary))
    content={n:ident((ROOT/n).read_bytes()) for n in writes}
    need(current()==head,'concurrent commit HEAD')
    git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('commit','-m',TASK+': 次戦個体連鎖の実測検証と固定引継ぎ・両ログ記録を完了')
    new=git('rev-parse','HEAD',text=True).strip();need(git('rev-parse','HEAD^',text=True).strip()==head,'parent differs')
    for name,meta in content.items():need(ident(git('show',new+':'+name))==meta,'committed blob differs')
    need(current()==head,'concurrent push HEAD');git('push','origin','HEAD:refs/heads/'+BRANCH)
    need(current()==new and not git('status','--porcelain','--untracked-files=no'),'remote readback differs')
    (OUT/'result.json').write_bytes(stable(dict(status='PASS_RECORDED_COMMITTED_NONFORCE_PUSHED',task=TASK,parent=head,commit=new,branch=BRANCH,native_run=RUN,native_job=JOB,new_native_processes=0,accepted_native_cases_replayed=0,guard=boundary,files=content,release_ready=False)))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+new)

if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('record','check','publish'),'explicit mode required');globals()[sys.argv[1]]()
