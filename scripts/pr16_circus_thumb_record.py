#!/usr/bin/env python3
"""Thumb修復を限定適用し、独立build/非影響証明後だけ記録・非force pushする。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
BASE='15d278dbf030ac20c91cc84217fb8ebb0d79eb08'
TASK='USER-20260918-CIRCUS-THUMB'
SELF='scripts/pr16_circus_thumb_record.py'
TEST='tests/test_pr16_circus_thumb_record.py'
WORKFLOW='.github/workflows/pr16-circus-thumb.yml'
PATCH='.chatgpt/patches/circus-thumb.patch'
REPORT='content/modernization/pr16_circus_thumb_checkpoint.json'
PREFIX='content/modernization/pr16_circus_native_prefix_checkpoint.json'
OUT=ROOT/'.local/pr16-circus-thumb-run'
IMPL=('scripts/pr16_circus_entry.py','scripts/pr16_circus_thumb.py','tests/test_pr16_circus_thumb.py',SELF,TEST,WORKFLOW)
STOP=('Circus初戦のThumb呼出し不具合を修復。既存2ownerへ関数型付きbx r3 thunkを接続し、'
      '独立2compile/link・2限定patchの一致を確認。304byte adapter以外を変えず、旧adapterを戻した'
      'ROM全体SHAが取消/Factory成功候補022bd5e6と完全一致することを検証。'
      '取消保存/Factory入口の成功2ケースは継承し再実行0。初戦nativeとCircus固有連勝/永続化/抑制は未受入。')
NEXT=('Thumb修復候補と非影響証明を再利用し、circus-first-battleだけを新SHA/新checkpointへ結合して'
      '入力のみで検証する。成功済みcircus-cancel-save-continueとfactory-fallback-cancelは再実行しない。'
      '初戦到達後にCircus固有streakの正規更新・永続化と30連勝以上の来歴、正規sp072の特性抑制を接続・検証する。'
      'Factory連勝をCircus固有連勝へ読み替えず、効果bit/施設番号/PC/LRをhost注入しない。'
      '無変更のRing/BP/P03/P06/P07/旧7関数/5335root走査は再実行しない。')


def need(value, message):
    if not value:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def validate_build(build, proof):
    import pr16_circus_thumb as thumb
    need(build['status']=='BUILT_CIRCUS_RECEPTION_NATIVE_PENDING','unexpected build status')
    need(build['candidate']==proof['candidate'] and build['candidate']['size']==33554432,'candidate differs')
    need(proof['status']=='PASS_ADAPTER_ONLY_PREFIX_INHERITANCE','missing unchanged-prefix proof')
    need(proof['previous']==dict(size=33554432,sha256=thumb.PREVIOUS_SHA),'prefix identity differs')
    need(proof['restored_whole_rom_sha256']==thumb.PREVIOUS_SHA,'whole-ROM rollback proof differs')
    at=(build['entries']['selector']&~1)-0x08000000
    need(proof['allowed_range']==[at,at+thumb.ADAPTER_SIZE] and at==build['payload_offset']+64,'change boundary differs')
    need(type(proof['changed_bytes']) is int and 0<proof['changed_bytes']<=thumb.ADAPTER_SIZE,'changed byte count differs')
    need(proof['inherited_cases']==['circus-cancel-save-continue','factory-fallback-cancel'],'inherited cases differ')
    for key in ('physical_admission_accepted','suppression_accepted','release_ready'):
        need(build[key] is False,'build overclaims acceptance')
    for key in ('physical_admission_accepted','suppression_accepted'):
        need(proof[key] is False,'proof overclaims acceptance')
    need(type(proof['accepted_native_cases_replayed']) is int and proof['accepted_native_cases_replayed']==0,'prefix replayed')
    for key in ('accepted_native_cases_replayed','new_emulator_processes'):
        need(type(build[key]) is int and build[key]==0,'build replayed native')
    for key in ('independent_new_adapter_links','independent_scoped_patches'):
        need(type(build[key]) is int and build[key]==2,'independent compile/patch count differs')
    need(build['old_trial_script_unchanged'] is True and build['old_cfru_owners_unchanged'] is True,'existing owner changed')
    need(build['inherited_root_scan_repeated'] is False and build['inherited_link_run']==35353620141,'repeated old audit')
    need(build['allocation']['summaries']['overlap_count']==0,'allocation overlap')


def project(state, backlog, checkpoint):
    s,b=copy.deepcopy(state),copy.deepcopy(backlog)
    need(checkpoint['physical_admission_accepted'] is False and checkpoint['release_ready'] is False,'cannot close physical gate')
    rows=[r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION']
    need(len(rows)==1 and rows[0]['success_evidence'] is None,'Circus physical authority moved')
    rows[0].update(implementation_checkpoint=REPORT,implementation_status=checkpoint['classification'],resume=NEXT)
    s['circus_thumb_implementation']=dict(path=REPORT,status=checkpoint['classification'],
        tested_head=checkpoint['tested_head'],run_id=checkpoint['build_run_id'],
        engineering_candidate=checkpoint['build']['candidate'],product_release_adopted=False,
        inherited_prefix_cases=checkpoint['proof']['inherited_cases'],physical_admission_accepted=False)
    s['bp']['current_stop']=s['source_change_review_ja']=STOP
    s['bp']['next_step']=s['next_action']['goal_ja']=NEXT
    s['next_action']['id']='CIRCUS_FIRST_BATTLE_THUMB_NATIVE'
    s['next_action']['read_paths']=[REPORT,PREFIX,'scripts/pr16_circus_native.py','tools/mgba_pr16_circus_native.c',
        'content/modernization/pr16_circus_admission_checkpoint.json','content/modernization/p08_remaining_work.json']
    s['remaining_sequence_ja']='取消/保存/Factory入口2件継承→Thumb修復初戦native→Circus固有streak正規更新/永続化と30連勝抑制→P08影響範囲移送→release判断。'
    note='run35363580877は取消保存・Factory入口の2成功とThumb初戦失敗の混在原本。run全体をsuccessへ読み替えない。304byte adapter以外の全ROM一致証明がある間は成功2ケースを再実行しない。run35365722696のbridge停止は既存全体private guardであり、認可不足やpatch不成立ではない。'
    if note not in s['do_not_repeat']:s['do_not_repeat'].insert(0,note)
    for key in ('candidate','status','latest_native_run','latest_native_job','latest_native_tested_head',
                'last_accepted_native_run','last_accepted_native_tested_head','release_ready','remaining_physical_gap_ids','remaining_p08_gate_ids'):
        need(s[key]==state[key],'formal BP/P08 acceptance changed')
    for old,new in zip(backlog['remaining_conditions'],b['remaining_conditions']):
        if old['id']!='PHYSICAL_CIRCUS_ADMISSION':need(old==new,'unrelated condition changed')
    return s,b


def apply():
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'write scope differs')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout differs');ops.assert_remote(head)
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'dirty tracked source')
    need(not (ROOT/REPORT).exists(),'already recorded; reuse checkpoint')
    resume.validate(ROOT)
    source=ROOT/'scripts/pr16_circus_entry.py';raw=source.read_bytes()
    need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='13a8bc8bf5ddf25b5095e5ec9a8301100040ce86','builder preimage changed')
    patch=(ROOT/PATCH).read_bytes()
    need(identity(patch)['sha256']=='ecbf683e4b75f79696677ae24fbee668fda6f64e4f525ff0a207ffa103ae1a9e','patch identity changed')
    subprocess.run(['git','apply','--check',PATCH],cwd=ROOT,check=True)
    subprocess.run(['git','apply',PATCH],cwd=ROOT,check=True)
    need(ops.cmd('git','diff','--name-only')=='scripts/pr16_circus_entry.py','patch changed unexpected paths')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'source-patch.json').write_bytes(stable(dict(request_head=head,patch=identity(patch),
        old_source=identity(raw),tested_source=identity(source.read_bytes()),
        provenance_ja='exact request HEADに固定済みpatchを適用したworktreeを検証し、成功後だけ同branchへcommitする。')))


def record():
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    import pr16_circus_thumb as thumb
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'write scope differs')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout differs');ops.assert_remote(head)
    need(ops.cmd('git','diff','--name-only')=='scripts/pr16_circus_entry.py','unexpected worktree edits')
    load=lambda path:json.loads((ROOT/path).read_bytes())
    state=load(resume.STATE);backlog=load(resume.BACKLOG);bp=identity((ROOT/resume.CHECKPOINT).read_bytes())
    build=load('.local/pr16-circus-entry/report.json');proof=load('.local/pr16-circus-entry/thumb-inheritance.json')
    validate_build(build,proof)
    source=load('.local/pr16-circus-thumb-run/source-patch.json')
    need(build['source_head']==head and build['run_id']==int(os.environ['GITHUB_RUN_ID']),'build source/run differs')
    need(source['request_head']==head and source['tested_source']==identity((ROOT/'scripts/pr16_circus_entry.py').read_bytes()),'tested worktree differs')
    for name,binding in build['sources'].items():need(identity((ROOT/name).read_bytes())==binding,'build source changed')
    prefix=load(PREFIX)
    need(prefix['run_id']==35363580877 and prefix['run_conclusion']=='failure' and prefix['candidate']==proof['previous'],'original prefix authority differs')
    need([r['case'] for r in prefix['accepted_cases']]==proof['inherited_cases'],'prefix case authority differs')
    checkpoint=dict(schema_version=1,task=TASK,classification='THUMB_ADAPTER_REPAIRED_PREFIX_INHERITED_NATIVE_OPEN',
        tested_head=head,build_run_id=int(os.environ['GITHUB_RUN_ID']),tested_worktree=source,
        build=build,proof=proof,prefix_checkpoint=PREFIX,prefix_run=35363580877,
        original_prefix_conclusion='failure',failed_bridge_run=35365722696,failed_bridge_conclusion='failure',
        source_bindings={n:identity((ROOT/n).read_bytes()) for n in IMPL},
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        accepted_native_cases_replayed=0,next_ja=NEXT)
    s,b=project(state,backlog,checkpoint)
    s['observed_head']=head;s['observed_date_jst']=datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    s['observed_head_semantics']='Thumb修復検証の要求HEAD。source-patch identityを適用したworktreeを検証。完了SHAはremote ref/receiptで確認。正式BP受入HEADではない。'
    s['observed_head_checks']=dict(scope_head=head,circus_thumb_run=int(os.environ['GITHUB_RUN_ID']),
        reason_ja='Thumb修復の新規契約・独立2compile/link・全ROM非影響証明を完了。記録runはcommit時in_progress。初戦nativeや全CI greenは未主張。')
    s['pending_runs']=[];s['logs_synchronized']=True
    s['session_execution_summary']=dict(new_emulator_processes=0,accepted_standalone_replays=0,independent_adapter_links=2,
        independent_scoped_patches=2,scope_ja='Thumb修復のみ。既存Circus取消/Factory入口は旧原本と全ROM一致証明から継承。')
    (ROOT/REPORT).write_bytes(stable(checkpoint));(ROOT/resume.BACKLOG).write_bytes(stable(b))
    for name in (*IMPL,REPORT,PREFIX):s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    (ROOT/resume.STATE).write_bytes(stable(s));(ROOT/resume.DOC).write_text(resume.render(s),encoding='utf-8')
    resume.validate(ROOT);need(bp==identity((ROOT/resume.CHECKPOINT).read_bytes()),'formal BP changed')
    tests=[]
    for pattern in (Path(TEST).name,'test_pr16_resume.py'):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (OUT/(pattern+'.txt')).open('w') as stream:t=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(t.wasSuccessful() and t.testsRun>0 and not t.skipped,'targeted tests failed');tests.append(dict(pattern=pattern,count=t.testsRun,success=True))
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    outputs=(REPORT,resume.STATE,resume.DOC,resume.BACKLOG,*ops.LOGS)
    stamp=datetime.now(timezone.utc).isoformat()
    log=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / Circus Thumb実行不具合修復\n'
        '- Status: DONE / Thumb修復build・prefix非影響証明まで。初戦native・固有連勝は未受入。\n'
        '- Version: pr16-circus-thumb-successor\n- Summary: '+STOP+'\n'
        '- Files changed: '+', '.join((*IMPL,*outputs))+'\n'
        '- Verify: 新規Thumb/記録契約、resume検証、task graph、diff checkをPASS。独立2compile/link・2patch一致、ELF関数型/Thumb bit/命令列、全allocation hashと重複0、旧adapter復元による全ROM SHA一致を確認。\n'
        f'- Evidence: request HEAD={head}; build run={os.environ["GITHUB_RUN_ID"]}; candidate={build["candidate"]["sha256"]}; {REPORT}。検証対象worktreeのpatch/source hashを保存。\n'
        '- History: run35363580877の2成功と1失敗を混同しない。run35365722696は認可・patch適用・task graphに成功、既存全体private guardで停止しnative0/push0。全体guard自体を変更/無効化せず、基点と最終index出力一致・追加違反0をcommit条件とする。\n'
        '- Native: 新規emulator0、既受入取消保存/Factory入口再実行0。正式BP/Ring/P03/P06/P07原本不変。\n'
        '- Commit: この記録と検証済み実装を含む同branchへの非force commit。自己SHAは外部ref/receipt。\n'
        '- Network: GitHub connector/Actionsとhash固定private Release。ROM/save/private archive/credentialは新規tracked/artifactへ含めない。merge/release/baseline変更なし。\n'
        '- Next: '+NEXT+'\n')
    for name in ops.LOGS:
        need(TASK not in (ROOT/name).read_text(),'completion already recorded')
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(log)
    subprocess.run(['git','rm','--',PATCH],cwd=ROOT,check=True)
    subprocess.run(['git','add','--',*IMPL,*outputs],cwd=ROOT,check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*IMPL,*outputs))
    guard.guard();subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);ops.assert_remote(head)
    for k,v in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):subprocess.run(['git','config',k,v],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': Thumb修復・prefix非影響証明・固定引継ぎと両ログを検証確定'],cwd=ROOT,check=True)
    commit=ops.cmd('git','rev-parse','HEAD');subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True);ops.assert_remote(commit,attempts=12)
    for name in (*IMPL,*outputs):need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed bytes differ')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'post-push tracked changes');resume.validate(ROOT)
    receipt=dict(status='PASS_THUMB_REPAIR_RECORDED',commit=commit,request_head=head,run_id=int(os.environ['GITHUB_RUN_ID']),tests=tests,
        candidate=build['candidate'],proof=proof,formal_bp_unchanged=True,physical_admission_accepted=False,release_ready=False)
    (OUT/'receipt.json').write_bytes(stable(receipt));(OUT/'completion-log.txt').write_text(log)
    for name in (REPORT,resume.STATE,resume.DOC,resume.BACKLOG):
        dest=OUT/'final'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    print(json.dumps(receipt,ensure_ascii=False));print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('apply','record'),'expected apply or record')
    (apply if sys.argv[1]=='apply' else record)()
