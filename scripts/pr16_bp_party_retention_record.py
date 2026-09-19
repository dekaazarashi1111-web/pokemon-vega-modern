#!/usr/bin/env python3
"""成功済みhost/owner監査とBLOCKEDなWIPだけを記録。ROM解析・native実行なし。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
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
import pr16_resume as resume
TASK='USER-20260914-BP-PARTY-RETENTION'
ENTRY='c0dc2ccee1e0253a0c8d8604c6a7312f04a133a3'
TESTED='48a36caf3361b1d167c302174eb2c4c4121c7508'
RUN=34785149994
ARTIFACT=10325794218
ZIP_ID=dict(size=216630,sha256='e25867d0a3167922e51d87b3e2767a7f61c614ffc8a92d174a825db38ce582f2')
BRANCH='codex/modernization-followup-20260908'
VERIFIED='content/modernization/pr16_bp_party_retention_wip.json'
SELF='scripts/pr16_bp_party_retention_record.py'
TEST='tests/test_pr16_bp_party_retention_record.py'
WORKFLOW='.github/workflows/pr16-bp-party-retention-record.yml'
OUT=ROOT/'.local/pr16-bp-party-retention-record'
LOGS=('design/run_log.md','design/version_log.md','design/blockers.md')
WIP_FILES=('overlays/facility_party_retention/facility_party_retention.c','tests/test_pr16_bp_party_retention.py',
           'scripts/pr16_bp_party_retention_owner.py','.github/workflows/pr16-bp-party-retention.yml')
NOTE='WIP: 次戦限定predicateとhost4回帰はPASS、固定candidateのowner監査run34785149994もSUCCESS。target呼出位置/ABIの確定・runtime接続・修復後native保持検証は未完。追加コード反映2回がOpenAIのツール安全性確認でブロックされたため、以後は解析/接続を停止して記録のみ実施。GitHub権限不足ではない。'
need=resume.require

def stable(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def ident(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def git(*args,**kw):return subprocess.check_output(['git',*args],cwd=ROOT,**kw)
def api(path):return json.loads(subprocess.check_output(['gh','api','repos/'+os.environ['GITHUB_REPOSITORY']+'/'+path]))
def current():return api('git/ref/heads/'+BRANCH)['object']['sha']
def small(r):return {k:r[k] for k in ('id','name','head_sha','path','status','conclusion','event')}
def write(name,raw):
    p=resume.safe_path(ROOT,name);raw.decode('utf-8');need(b'\0' not in raw,'nontext write')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)

def verify_artifact(raw):
    need(ident(raw)==ZIP_ID,'owner artifact digest')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        rows=z.infolist();need(len(rows)<40 and sum(i.file_size for i in rows)<2000000,'bounded owner artifact')
        names=[i.filename for i in rows]
        need(len(names)==len(set(names)) and all('/' not in n and '\\' not in n and n not in ('.','..') for n in names),'flat artifact only')
        members={n:z.read(n) for n in names}
    receipt=json.loads(members['members.json'])
    need(set(members)==set(receipt)|{'members.json'},'owner member set')
    for n,meta in receipt.items():need(ident(members[n])==meta,'owner member digest: '+n)
    owner=json.loads(members['owner.json'])
    need(owner['status']=='OWNER_ABI_AUDIT_NOT_NATIVE_ACCEPTANCE','owner status')
    need(owner['candidate']==dict(size=33554432,sha256='7f32ba99ad34cd0320559a8dc6990876084f371c8bfae769c7482090c7be90cd'),'candidate changed')
    need(owner['new_emulator_processes']==owner['accepted_native_cases_replayed']==0,'unexpected native replay')
    need(owner['native_bp_earning_accepted'] is False and owner['release_ready'] is False,'acceptance inflated')
    text=members['unit.stderr'].decode('utf-8')
    need(text.count(' ... ok')==4 and 'Ran 4 tests in ' in text and text.endswith('\nOK\n'),'host tests not PASS')
    before=json.loads(members['actions-before.json']);need(before['tested_head']==TESTED,'owner tested head')
    return dict(owner_status=owner['status'],candidate=owner['candidate'],member_hashes=receipt,
                host_tests=dict(count=4,result='PASS',transcript=text),actions_before=before)

def update_state(source,progress):
    s=copy.deepcopy(source)
    need('party_retention_wip' not in s,'WIP already recorded; do not repeat')
    need(s['next_action']['id']=='BP_EXCHANGE_PARTY_RETENTION_REPAIR','next task changed')
    s['party_retention_wip']=dict(evidence=VERIFIED,status='BLOCKED_RUNTIME_NOT_CONNECTED',tested_head=TESTED,owner_run=RUN)
    s['bp']['current_stop']=NOTE+'\n\n既存native診断: '+s['bp']['current_stop']
    goal='保存済みWIPとowner監査を再利用し、未接続のtarget呼出位置/ABI照合・最小successor接続・修復後native個体保持検証を完了する。既存host4回帰/owner監査の単独再実行や同じtool-blocked要求の反復は行わず、保持確認前に2/3戦目・BP報酬へ進まない。'
    s['next_action']['goal_ja']=s['bp']['next_step']=goal
    s['next_action']['read_paths']=[VERIFIED,*WIP_FILES,*s['next_action']['read_paths']]
    s['do_not_repeat'].append('WIP48a36ca/owner run34785149994を再利用。host predicate PASSはruntime修復やnative保持成功を意味しない。対象コード変更時だけ対応回帰を再実行。')
    s.update(observed_head=TESTED,observed_head_semantics='WIPとsource-only owner監査の固定HEAD。latest_native_*と正式受入は以前の原本を維持。',pending_runs=[],logs_synchronized=True,p08_resume_synchronized=True)
    s['observed_head_checks']=dict(reason_ja='WIP48a36caの8 Actionsは照合時SUCCESS。entry c0dcのPR 2件はaction_required履歴のまま保持。今回owner監査はnative0、runtime保持修復は未完。詳細: '+VERIFIED)
    s['party_retention_session_summary']=dict(task_status='BLOCKED',host_tests=4,owner_audit='PASS',new_native_processes=0,accepted_native_cases_replayed=0,runtime_connected=False,candidate_changed=False)
    return s

def record():
    OUT.mkdir(parents=True,exist_ok=False)
    head=git('rev-parse','HEAD',text=True).strip();need(head==os.environ['GITHUB_SHA']==current(),'concurrent HEAD')
    before=resume.validate(ROOT);pr=api('pulls/16')
    need(pr['state']=='open' and pr['draft'] and not pr['merged'] and pr['head']['sha']==head,'PR boundary')
    run=api('actions/runs/'+str(RUN))
    need(run['head_sha']==TESTED and run['conclusion']=='success' and run['status']=='completed' and run['path']==WIP_FILES[3],'owner run identity')
    rows=api('actions/runs/'+str(RUN)+'/artifacts')['artifacts'];a=next(x for x in rows if x['id']==ARTIFACT)
    need(not a['expired'] and a['name']=='pr16-bp-party-retention' and a['size_in_bytes']==ZIP_ID['size'] and a['digest']=='sha256:'+ZIP_ID['sha256'],'artifact metadata')
    raw=subprocess.check_output(['gh','api','repos/'+os.environ['GITHUB_REPOSITORY']+'/actions/artifacts/'+str(ARTIFACT)+'/zip'])
    evidence=verify_artifact(raw)
    for name in WIP_FILES:need((ROOT/name).read_bytes()==git('show',TESTED+':'+name),'WIP changed: '+name)
    runs=api('actions/runs?head_sha='+TESTED+'&per_page=100')
    need(runs['total_count']==len(runs['workflow_runs']),'Actions pagination')
    need(len(runs['workflow_runs'])==8 and all(r['conclusion']=='success' for r in runs['workflow_runs']),'WIP checks changed')
    v=dict(schema_version=1,task=TASK,task_status='BLOCKED',classification='WIP_NOT_RUNTIME_FIX_NOT_NATIVE_ACCEPTANCE',
           tested_head=TESTED,owner_run=small(run),owner_artifact_id=ARTIFACT,owner_artifact_zip=ZIP_ID,owner_evidence=evidence,
           tested_head_checks=[small(r) for r in runs['workflow_runs']],
           sources={n:ident((ROOT/n).read_bytes()) for n in (*WIP_FILES,SELF,TEST,WORKFLOW)},
           runtime_connected=False,native_retention_verified=False,new_native_processes=0,accepted_native_cases_replayed=0,
           candidate_changed=False,native_bp_earning_accepted=False,release_ready=False,
           blocker=dict(kind='OPENAI_TOOL_SAFETY_BLOCK',attempts=2,github_permission_missing=False,
               excerpt='リクエストの安全性を確認できなかったため、このツールの呼び出しは OpenAI によってブロックされました。',
               response='追加解析/接続を停止。別経路で再試行せず、成功済み証拠とWIPのみを記録。'),summary_ja=NOTE)
    write(VERIFIED,stable(v));s=update_state(before,v)
    for name in (*WIP_FILES,SELF,TEST,WORKFLOW,VERIFIED):s['source_bindings'][name]=ident((ROOT/name).read_bytes())
    b=resume.load(ROOT,resume.BACKLOG)
    for item in b['remaining_conditions']:
        if item['id'] in ('NATURAL_CAPTURE_GEAR','FINAL_NATIVE_ACCEPTANCE'):
            item['resume']='Current resume: '+resume.DOC+'. '+NOTE+' Next: '+s['next_action']['goal_ja']
    write(resume.BACKLOG,stable(b));write(resume.STATE,stable(s));write(resume.DOC,resume.render(s).encode())
    stamp=datetime.now(timezone.utc).isoformat()
    note=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Version: PR16 party retention WIP\n'
          f'- Task: {TASK} / 次戦で交換個体が失われる問題の修復\n- Status: BLOCKED\n'
          '- Summary: '+NOTE+'\n'
          f'- Verify: host4tests PASS、owner Actions run{RUN} SUCCESS、artifact{ARTIFACT}の全member hashを照合。記録回帰・resume tests/check・task graph・diff/index guard差分をpublish gateとする。native保持検証は未実行。\n'
          '- Files changed: predicate/C、host tests、owner script/workflow（WIP48a36ca）。今回は記録script/tests/workflow、WIP evidence JSON、固定引継ぎMD/JSON、P08 resume、両ログとblockers。\n'
          f'- Commit: 実装WIP={TESTED}。記録はこの追記を含むcommit。入力HEAD={head}。非force push後のhashはworkflow result.jsonとremote refで照合。\n'
          '- Network: GitHub connector/API・既存Actions artifactのみ。記録工程はROM/私有入力を開かず、native実行なし。\n'
          '- Blocker/Error excerpt: OpenAIツール安全性確認が追加コード反映2回をブロック。GitHubアクセス不足ではない。\n'
          '- Boundary: candidate7f32/CRC0D5D9178、正式physical4/P08 gate2、BP未受入、PR open/draft、baselineを維持。merge/releaseなし。受入済みcaseの再実行0（選択工程）。自動起動既存CIは別記。\n'
          '- Question for human: 権限確認の再依頼は不要。停止した要求は反復しない。\n'
          '- Next step: '+s['next_action']['goal_ja']+'\n')
    for name in LOGS:
        old=resume.safe_path(ROOT,name).read_bytes();need(TASK.encode() not in old,'already logged')
        write(name,old+note.encode())
    check()

def check():
    s=resume.validate(ROOT);v=resume.load(ROOT,VERIFIED)
    need(v['task_status']=='BLOCKED' and v['tested_head']==TESTED,'WIP status')
    for k in ('runtime_connected','native_retention_verified','candidate_changed','native_bp_earning_accepted','release_ready'):need(v[k] is False,'overclaim: '+k)
    for name,meta in v['sources'].items():need(ident((ROOT/name).read_bytes())==meta,'source binding: '+name)
    for key in ('status','candidate','latest_native_run','latest_native_job','latest_native_evidence','latest_native_tested_head','last_accepted_native_run','last_accepted_native_tested_head','remaining_physical_gap_ids','remaining_p08_gate_ids'):
        old=json.loads(git('show',TESTED+':'+resume.STATE));need(s[key]==old[key],'native/history changed: '+key)
    for k,val in old['bp'].items():
        if k not in ('current_stop','next_step'):need(s['bp'][k]==val,'BP acceptance changed: '+k)
    for name in LOGS:need(TASK in (ROOT/name).read_text(),'log missing')
    return v

def publish():
    v=check();head=git('rev-parse','HEAD',text=True).strip();need(head==os.environ['GITHUB_SHA']==current(),'concurrent publish')
    writes={VERIFIED,resume.STATE,resume.DOC,resume.BACKLOG,*LOGS}
    actual=set(git('diff','--name-only',text=True).splitlines())|set(git('ls-files','--others','--exclude-standard',text=True).splitlines())
    need(actual==writes,'write allowlist')
    for name in LOGS:need((ROOT/name).read_bytes().startswith(git('show',head+':'+name)),'append-only logs')
    git('add','--',*sorted(writes));git('diff','--cached','--check')
    with tempfile.TemporaryDirectory() as tmp:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(tmp)/'baseline.index'));git('read-tree',ENTRY,env=env)
        base=subprocess.run([sys.executable,'scripts/guard_private_files.py'],cwd=ROOT,env=env,capture_output=True)
    final=subprocess.run([sys.executable,'scripts/guard_private_files.py'],cwd=ROOT,capture_output=True)
    need(base.returncode in (0,1) and final.returncode==base.returncode and final.stdout==base.stdout and not base.stderr and not final.stderr,'new private guard violation')
    import guard_private_files as guard
    for name in git('diff','--name-only',ENTRY,'--',text=True).splitlines():
        p=resume.safe_path(ROOT,name);raw=p.read_bytes();raw.decode('utf-8')
        need(b'\0' not in raw and p.suffix.lower() not in guard.BLOCKED_SUFFIXES,'nontext/private path')
        need(not any(name==x or name.startswith(x+'/') for x in guard.BLOCKED_PARTS),'private path')
        need(not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',raw),'credential-like text')
        if p.suffix.lower() in guard.DOCUMENT_SUFFIXES:
            old=subprocess.run(['git','show',ENTRY+':'+name],cwd=ROOT,capture_output=True)
            need(guard.document_user_path_lines(raw)==guard.document_user_path_lines(old.stdout if old.returncode==0 else b''),'new machine path')
    boundary=dict(baseline_head=ENTRY,returncode=final.returncode,whole_guard_passed=final.returncode==0,new_violations=0,stdout=ident(final.stdout))
    content={n:ident((ROOT/n).read_bytes()) for n in writes};need(current()==head,'concurrent commit')
    git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('commit','-m',TASK+': BLOCKED WIP・host4/owner成功証拠と固定引継ぎ・ログを記録')
    new=git('rev-parse','HEAD',text=True).strip();need(git('rev-parse','HEAD^',text=True).strip()==head,'parent differs')
    for n,meta in content.items():need(ident(git('show',new+':'+n))==meta,'committed blob differs')
    need(current()==head,'concurrent push');git('push','origin','HEAD:refs/heads/'+BRANCH)
    need(current()==new and not git('status','--porcelain','--untracked-files=no'),'remote readback')
    (OUT/'result.json').write_bytes(stable(dict(record_status='PASS_COMMITTED_NONFORCE_PUSHED',task_status='BLOCKED',task=TASK,parent=head,commit=new,branch=BRANCH,guard=boundary,files=content,new_native_processes=0,release_ready=False)))
    print('RESULT=BLOCKED TASK='+TASK+' VERIFY=PASS_RECORD_ONLY COMMIT='+new)

if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('record','check','publish'),'explicit mode required');globals()[sys.argv[1]]()
