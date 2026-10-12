#!/usr/bin/env python3
"""既存初戦原本を検証して記録する。ROM生成/native再実行/全受付受入は行わない。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_native as native
need,identity,stable,load=native.need,native.identity,native.stable,native.strict
BASE='935859389756c5d308f5348eb56972632f475ee1'
TASK='USER-20260918-CIRCUS-FIRST-BATTLE'
SELF='scripts/pr16_circus_first_record.py'
TEST='tests/test_pr16_circus_first_record.py'
WORKFLOW='.github/workflows/pr16-circus-first-record.yml'
REPORT='content/modernization/pr16_circus_first_battle_checkpoint.json'
THUMB='content/modernization/pr16_circus_thumb_checkpoint.json'
OUT=ROOT/'.local/pr16-circus-first-record'
RAW_BASE='evidence/pr16_circus_first_native'
RAW=(RAW_BASE+'/original.stdout.txt',RAW_BASE+'/original.stderr.txt')
IMPL=(native.SELF,native.TEST,native.WORKFLOW,SELF,TEST,WORKFLOW)
SPEC=dict(run_id=35367721416,job_id=105674099808,tested_head='c847b700d5b3af983c08a44d2278ab86d409eeb9',
    workflow=native.WORKFLOW,conclusion='success',artifact_id=10557022177,name='pr16-circus-native',with_manifest=True,
    artifact_identity=dict(size=258578,sha256='2d20f873c45ac26d8cd65d26b6b7a0fe18786be464f3a25b0c46d948aebc64cc'),
    required_success_steps=['新SHA結果契約と未完1件の選択16件のみを検証','固定Thumb修復候補をnative入力用に再構成（受入ケース再実行なし）',
        '受入済み2ケースは再実行せずThumb修復Circus初戦のみ検証','ROM save ELFを除外しnative原本と限定sourceを保持','Run actions/upload-artifact@v4'])
GUARDS=['bus8','bus16','bus32','raw8','raw16','raw32','register']
STOP=('Thumb修復候補99cc0948で未完だったCircus初戦1件が成功。新質問→レンタル選択→正規sp072抽選'
      '（field効果0x80）→戦闘→実入力の1ターンを4229framesで確認。新規emulator1、7書込barrier、警告0。'
      '取消保存/Factory入口2成功は非影響証明から継承し再実行0。画像16枚を確認したが、'
      '第2選択画面の先頭ゴースと実戦のポリゴンが異なる。600byte検査は元partyの退避像のみで、'
      '選択個体の実戦継承を保証しない。選択個体の経路とCircus固有連勝/永続化/30連勝抑制は未受入。')
NEXT=('保存した初戦成功・Thumb非影響証明を再利用し、まず第2選択→戦闘間の個体継承を限定追跡する。'
      '表示名だけで原因を断定せず、選択個体のspecies/personality/party bytesと既存prepare/retention ownerを照合し、'
      '必要な場合だけCircus専用経路を修復する。その後、固有streakの正規勝敗更新・保存復帰と30連勝以上の来歴、'
      '正規sp072の特性抑制を実装・検証する。Factory連勝を代用せず、効果/施設番号/連勝/PC/LRをhost注入しない。'
      '無変更の取消保存/Factory入口/初戦1ターン/Ring/BP/P03/P06/P07/旧7関数/5335root走査を再実行しない。')


def unpack(raw,bound):
    need(identity(raw)==bound,'artifact ZIP identity differs')
    files={};total=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(0<len(z.infolist())<500,'ZIP member count differs')
        for info in z.infolist():
            name=info.filename;p=PurePosixPath(name)
            need(name==p.as_posix() and not p.is_absolute() and '..' not in p.parts and '\\' not in name
                 and name not in files and not info.is_dir(),'unsafe/duplicate member path')
            need((info.external_attr>>16)&0o170000!=0o120000 and info.file_size<2000000,'unsafe member type/size')
            data=z.read(info);total+=len(data);need(total<8000000,'expanded ZIP bound')
            if p.suffix=='.ppm':
                need(data.startswith(b'P6\n240 160\n255\n') and len(data)==115215,'unexpected screenshot')
            else:
                need(p.suffix in {'.json','.txt','.stdout','.stderr','.log','.c','.h','.py','.yml','.ld','.S'},'private/non-text suffix')
                data.decode('utf-8');need(b'\0' not in data and not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',data),'unsafe text')
            files[name]=data
    manifest=load(files['members.json'])
    need(set(files)==set(manifest)|{'members.json'},'manifest coverage differs')
    for name,binding in manifest.items():need(identity(files[name])==binding,'member identity differs')
    return files,manifest


def validate_report(r,files):
    need(r['source_head']==SPEC['tested_head'] and r['candidate']==dict(size=33554432,sha256=native.SHA),'native head/candidate differs')
    need(r['status']=='PASS_CIRCUS_SCOPED_NATIVE' and r['scope']=='THUMB_REPAIRED_CIRCUS_FIRST_BATTLE_ONLY','native scope differs')
    need(r['requested_cases']==['circus-first-battle'] and r['failures']==[] and r['guard_checks']==GUARDS,'case/guard/failure scope differs')
    for key,expected in (('actual_new_processes',1),('successful_fresh_cores',1),('accepted_native_cases_replayed',0)):
        need(type(r[key]) is int and r[key]==expected,'native accounting differs: '+key)
    for key in ('physical_admission_accepted','suppression_accepted','release_ready'):need(r[key] is False,'unproved acceptance')
    need(len(r['results'])==1,'extra/missing native result')
    row=r['results'][0];stem='pr16-circus-native/circus-first-battle'
    proc=load(files[stem+'.process.json'])
    need(proc==dict(schema_version=1,returncode=0,timed_out=False,spawn_error=None) and row['process']==proc,'original process differs')
    result=native.validate(files[stem+'.stdout'],files[stem+'.stderr'],proc['returncode'],'circus-first-battle')
    need(result==row['result'] and row['case']=='circus-first-battle' and row['visual_review_completed'] is False,'result was relabelled')
    need(len(row['screens'])==16,'visual review coverage differs')
    for name,binding in row['screens'].items():need(identity(files['pr16-circus-native/'+name])==binding,'reviewed screenshot differs')
    for guard in GUARDS:
        prefix='pr16-circus-native/guard-'+guard
        need(load(files[prefix+'.process.json'])==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None),'guard did not fail closed')
        need(files[prefix+'.stdout']==b'' and files[prefix+'.stderr']==b'P03 archive: host write after observation barrier\n','guard original differs')
    return result


def project(state,backlog,report):
    s,b=copy.deepcopy(state),copy.deepcopy(backlog)
    need(report['physical_admission_accepted'] is False and report['release_ready'] is False and report['rental_identity_verified'] is False,'cannot promote limited native to full acceptance')
    rows=[r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION']
    need(len(rows)==1 and rows[0]['success_evidence'] is None,'physical gate authority moved')
    rows[0].update(implementation_checkpoint=REPORT,implementation_status=report['classification'],resume=NEXT)
    s['circus_first_battle_native']=dict(path=REPORT,status=report['classification'],run_id=SPEC['run_id'],tested_head=SPEC['tested_head'],
        engineering_candidate=report['candidate'],first_turn_verified=True,rental_identity_verified=False,physical_admission_accepted=False)
    s['bp']['current_stop']=s['source_change_review_ja']=STOP
    s['bp']['next_step']=s['next_action']['goal_ja']=NEXT;s['next_action']['id']='CIRCUS_RENTAL_IDENTITY_AND_STREAK'
    s['next_action']['read_paths']=[REPORT,THUMB,native.SOURCE,native.SELF,'scripts/pr16_circus_entry.py','content/modernization/p08_remaining_work.json']
    s['remaining_sequence_ja']='初戦1ターン成功は保存→選択個体の戦闘継承を確認/必要修復→固有連勝の正規更新/永続化と30連勝抑制→影響範囲P08移送→release判定。'
    note='run35367721416の初戦1ターン成功は同SHA/controllerなら再実行しない。画像16枚の選択ゴース/実戦ポリゴン差は未解決で、元party600byte退避検査と選択個体保持を混同しない。取消/Factory入口2件は旧失敗run内の成功原本とThumb全ROM非影響証明から継承する。'
    if note not in s['do_not_repeat']:s['do_not_repeat'].insert(0,note)
    for key in ('candidate','status','latest_native_run','latest_native_job','latest_native_tested_head','last_accepted_native_run',
                'last_accepted_native_tested_head','release_ready','remaining_physical_gap_ids','remaining_p08_gate_ids'):
        need(s[key]==state[key],'formal acceptance authority changed')
    for old,new in zip(backlog['remaining_conditions'],b['remaining_conditions']):
        if old['id']!='PHYSICAL_CIRCUS_ADMISSION':need(old==new,'unrelated P08 condition changed')
    return s,b


def run():
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    import pr16_circus_record as evidence
    import pr16_circus_thumb_record as thumb
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'write scope differs')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout differs');ops.assert_remote(head)
    subprocess.run(['git','merge-base','--is-ancestor',SPEC['tested_head'],head],cwd=ROOT,check=True)
    need(not (ROOT/REPORT).exists() and not ops.cmd('git','status','--porcelain','--untracked-files=no'),'already recorded or dirty worktree')
    resume.validate(ROOT);state=load((ROOT/resume.STATE).read_bytes());backlog=load((ROOT/resume.BACKLOG).read_bytes());OUT.mkdir(parents=True,exist_ok=True)
    protected={p:identity((ROOT/p).read_bytes()) for p in (resume.CHECKPOINT,THUMB,'content/modernization/pr16_circus_native_prefix_checkpoint.json')}
    run_meta=ops.api('actions/runs/'+str(SPEC['run_id']));job=ops.api('actions/jobs/'+str(SPEC['job_id']));artifact=ops.api('actions/artifacts/'+str(SPEC['artifact_id']))
    verified=evidence.verify_actions(SPEC,run_meta,job,artifact,ops.REPO,ops.BRANCH)
    raw=subprocess.check_output(['gh','api','repos/'+ops.REPO+'/actions/artifacts/'+str(SPEC['artifact_id'])+'/zip'],cwd=ROOT)
    files,manifest=unpack(raw,SPEC['artifact_identity']);r=load(files['pr16-circus-native/report.json']);result=validate_report(r,files)
    evidence.tests_pass(files['pr16-circus-native-run/tests.stderr'],16)
    for name,binding in r['sources'].items():need(identity((ROOT/name).read_bytes())==binding,'native source changed: '+name)
    t=load((ROOT/THUMB).read_bytes());thumb.validate_build(r['build_recipe'],t['proof'])
    for name,binding in r['build_recipe']['sources'].items():need(identity((ROOT/name).read_bytes())==binding,'build source changed')
    stem='pr16-circus-native/circus-first-battle'
    for dst,src in zip(RAW,(stem+'.stdout',stem+'.stderr')):
        p=ROOT/dst;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(files[src])
    visual=dict(reviewed=True,reviewer='ChatGPT image inspection',reviewed_screens=r['results'][0]['screens'],
        scope_ja='原本PPM16枚を全て画像として確認。新Circus質問、6体→3体選択、戦闘、技メニュー、PP消費と1ターン復帰を確認。',
        issue_ja='第2選択画面の先頭名はゴース、実戦先頭名はポリゴン。表示/再生成/個体選択経路の原因は未確定。選択個体保持の受入はしない。',
        selected_party_identity_verified=False,original_result_unchanged=True)
    report=dict(schema_version=1,task=TASK,classification='CIRCUS_FIRST_TURN_VERIFIED_RENTAL_IDENTITY_AND_STREAK_OPEN',
        candidate=r['candidate'],tested_head=SPEC['tested_head'],native_run_id=SPEC['run_id'],record_head=head,record_run_id=int(os.environ['GITHUB_RUN_ID']),
        verified_actions=verified,artifact_spec=SPEC,member_manifest=manifest,native_report_identity=identity(files['pr16-circus-native/report.json']),
        original_result=result,original_process=r['results'][0]['process'],original_sources=r['sources'],original_generated=r['generated'],
        original_text={n:identity((ROOT/n).read_bytes()) for n in RAW},visual_review=visual,
        inherited_prefix_proof=t['proof'],inherited_failed_run=35363580877,inherited_failed_run_relabelled=False,
        first_turn_verified=True,rental_identity_verified=False,circus_streak_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        native_processes_in_tested_run=1,new_emulator_processes_in_record=0,accepted_native_cases_replayed=0,next_ja=NEXT)
    s,b=project(state,backlog,report);s['observed_head']=head;s['observed_date_jst']=datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    s['observed_head_semantics']='初戦成功原本の記録source HEAD。実native tested HEADはCircus専用checkpointに固定。正式BP受入HEADは維持。'
    s['observed_head_checks']=dict(scope_head=head,circus_first_battle=verified,reason_ja='限定native成功原本を照合。記録runはcommit時in_progress。全CI green/受付全体受入とは主張しない。')
    s['session_execution_summary']=dict(new_emulator_processes=1,record_emulator_processes=0,accepted_standalone_replays=0,
        scope_ja='Thumb修復候補の未完初戦1件のみ。原本の600byte検証は初期party退避像であり選択個体の一致検証ではない。')
    s['pending_runs']=[];s['logs_synchronized']=True
    (ROOT/REPORT).write_bytes(stable(report));(ROOT/resume.BACKLOG).write_bytes(stable(b))
    for name in (*IMPL,native.SOURCE,REPORT,*RAW):s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    (ROOT/resume.STATE).write_bytes(stable(s));(ROOT/resume.DOC).write_text(resume.render(s),encoding='utf-8')
    resume.validate(ROOT)
    tests=[]
    for pattern in (Path(TEST).name,'test_pr16_resume.py'):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (OUT/(pattern+'.txt')).open('w') as stream:result_test=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(result_test.wasSuccessful() and result_test.testsRun>0 and not result_test.skipped,'record/resume tests failed')
        tests.append(dict(pattern=pattern,count=result_test.testsRun,success=True))
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    outputs=(REPORT,*RAW,resume.STATE,resume.DOC,resume.BACKLOG,*ops.LOGS);stamp=datetime.now(timezone.utc).isoformat()
    log=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        '- Status: DONE / 修復候補の初戦1ターン限定検証・記録。選択個体保持/固有連勝は未受入。\n'
        '- Version: pr16-circus-first-turn\n- Summary: '+STOP+'\n'
        '- Files changed: '+', '.join((*IMPL,*outputs))+'\n'
        '- Verify: native結果契約16件PASS、7host-write barrier、run35367721416/job105674099808成功。ZIP/member/source/process/stdout/stderrを照合し、PPM16枚を画像確認。記録/再開tests、task graph、最終index差分guard、diff checkをcommit前必須。\n'
        '- Evidence: '+REPORT+'; tested HEAD='+SPEC['tested_head']+'; artifact10557022177 SHA256='+SPEC['artifact_identity']['sha256']+'。原本stdout/stderrをtracked textで保持。画像上の個体名差は未解決として記録し、旧原本は改変しない。\n'
        '- Boundary: 新規native1/4229frames/効果0x80/警告0/保存0/BP0。取消保存・Factory入口2成功は継承、再実行0。正式BP/Ring/P03/P06/P07、physical1/P08 gates2、release_ready=falseを維持。\n'
        '- Commit: この記録と検証済みnative選択変更を含む同branchへの非force commit。自己SHAはremote ref/receipt。\n'
        '- Network: GitHub connector/Actions。記録工程では既存artifactのみ使用し、private入力復元/ROM生成/native起動なし。ROM/save/credentialを新規tracked/artifactへ含めない。既存full guard違反は前後出力一致・新規違反0で区別。merge/release/baseline変更なし。\n'
        '- Next: '+NEXT+'\n')
    for name in ops.LOGS:
        need(TASK not in (ROOT/name).read_text(),'completion already recorded')
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(log)
    need(protected=={p:identity((ROOT/p).read_bytes()) for p in protected},'accepted checkpoint changed')
    subprocess.run(['git','add','--',*IMPL,*outputs],cwd=ROOT,check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*IMPL,*outputs));guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);ops.assert_remote(head)
    for k,v in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):subprocess.run(['git','config',k,v],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': 初戦native成功・画像上の未解決差・固定引継ぎと両ログを確定'],cwd=ROOT,check=True)
    commit=ops.cmd('git','rev-parse','HEAD');subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True);ops.assert_remote(commit,attempts=12)
    for name in (*IMPL,*outputs):need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed output differs')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'post-push tracked changes');resume.validate(ROOT)
    receipt=dict(status='PASS_CIRCUS_FIRST_TURN_RECORDED',commit=commit,source_head=head,record_run_id=int(os.environ['GITHUB_RUN_ID']),native_run_id=SPEC['run_id'],tests=tests,
        candidate=r['candidate'],record_emulator_processes=0,accepted_native_cases_replayed=0,physical_admission_accepted=False,release_ready=False)
    (OUT/'receipt.json').write_bytes(stable(receipt));(OUT/'completion-log.txt').write_text(log)
    for name in (REPORT,resume.STATE,resume.DOC,resume.BACKLOG):
        p=OUT/'final'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    print(json.dumps(receipt,ensure_ascii=False));print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


if __name__=='__main__':run()
