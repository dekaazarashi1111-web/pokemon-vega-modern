#!/usr/bin/env python3
"""Circus実受付候補の生成・新規script契約を固定引継ぎへ記録する。native受入とは別。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_record as evidence
need,identity,stable,load=evidence.need,evidence.identity,evidence.stable,evidence.load
BASE='ac3245c1fbeb078d6f13433d6b303e780e887739'
TASK='USER-20260918-CIRCUS-ENTRY'
SELF='scripts/pr16_circus_entry_record.py'
TEST='tests/test_pr16_circus_entry_record.py'
WORKFLOW='.github/workflows/pr16-circus-entry-record.yml'
SPEC='content/modernization/pr16_circus_entry_record_spec.json'
REPORT='content/modernization/pr16_circus_entry_checkpoint.json'
OUT=ROOT/'.local/pr16-circus-entry-record'
IMPL=('overlays/circus_admission/circus_script.c','scripts/pr16_circus_entry.py',
      'tests/test_pr16_circus_entry.py','tests/test_pr16_circus_entry_binding.py','.github/workflows/pr16-circus-entry.yml')
STOP=('既存Codex受付のFactory行き4-byte pointerに任意Circus分岐を追加した限定候補を生成。'
      '既存Factory本体/CFRU ownerは不変。専用のscript結果adapterと複製Trialの3戦闘開始点へ'
      '未消費pending番号3選択→正規sp072反復→5Dを接続。23件の新規host/script契約、'
      '独立ARM link2回・限定patch2回一致、全allocation hash/2範囲外不変/重複0を検証。'
      '実受付native・保存復帰・Circus固有連勝の正規更新/永続化・抑制抽選は未受入。')
NEXT=('保存した候補生成原本を再利用し、新しい実受付の取消・レンタル選択・戦闘開始を入力だけで検証する。'
      '追加質問の影響を受けるFactory入口に限り対照を行い、party/BP/Bag/通常Save/fresh Continueを確認する。'
      'Factoryの連勝値とCircus固有streak ownerは別物。固有streakの正規更新・永続化を接続した上で'
      '連勝30以上の来歴と正規sp072の特性抑制を別に検証する。効果bit/施設番号/PC/LRをhost注入しない。'
      '受入済みRing/BP/P03/P06/P07の無変更native、旧7関数/link/5335 root走査は再実行しない。')


def validate_build(report, spec):
    need(report['status']=='BUILT_CIRCUS_RECEPTION_NATIVE_PENDING','wrong build scope')
    need(report['source_head']==spec['tested_head'] and report['run_id']==spec['run_id'],'build run/head differs')
    need(report['parent']==evidence.PARENT and report['candidate']['size']==33554432,'wrong parent/candidate size')
    need(report['candidate']['sha256']!=report['parent']['sha256'],'candidate was not changed')
    for key in ('new_emulator_processes','accepted_native_cases_replayed'):evidence.exact(report[key],0,'unexpected native replay')
    for key in ('physical_admission_accepted','suppression_accepted','release_ready'):evidence.exact(report[key],False,'unproved acceptance')
    for key in ('independent_new_adapter_links','independent_scoped_patches'):evidence.exact(report[key],2,'independent build count differs')
    for key in ('old_trial_script_unchanged','old_cfru_owners_unchanged'):evidence.exact(report[key],True,'unapproved parent edit')
    need(report['inherited_link_run']==35353620141 and report['inherited_root_scan_repeated'] is False,'retained link boundary differs')
    need(len(report['launch_sites'])==3 and all(r['draw']==0x0910333D and r['size']==43 for r in report['launch_sites']),'launch sequence differs')
    need(len(set(r['original'] for r in report['launch_sites']))==3,'duplicate launch site')
    need(report['gateway']['address']==0x093CDA9C and report['gateway']['before']=='90933c09','gateway preimage differs')
    need(report['allocation']['summaries']['overlap_count']==0 and len(report['existing_allocations_rehashed'])==1,'allocation ownership differs')
    allocations=report['allocation']['allocations']
    target=[r for r in allocations if r['name']=='pr16_circus_reception_runtime']
    need(len(target)==1 and target[0]['start']==report['payload_offset'] and target[0]['start']%16==0,'payload placement differs')
    need(target[0]['end_exclusive']-target[0]['start']==report['payload_offset']+report['payload']['size']-target[0]['start']<8192 and target[0]['content_sha256']==report['payload']['sha256'],'payload identity differs')


def project(state, backlog, report):
    s,b=copy.deepcopy(state),copy.deepcopy(backlog)
    need(report['physical_admission_accepted'] is False and report['release_ready'] is False,'physical gap cannot be closed by build')
    rows=[r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION']
    need(len(rows)==1 and rows[0]['success_evidence'] is None,'Circus already accepted')
    rows[0].update(implementation_checkpoint=REPORT,implementation_status=report['classification'],resume=NEXT)
    s['circus_entry_implementation']={'path':REPORT,'status':report['classification'],'tested_head':report['tested_head'],
        'run_id':report['build_run_id'],'engineering_candidate':report['build']['candidate'],'product_release_adopted':False,
        'script_connection_built':True,'physical_admission_accepted':False}
    s['bp']['current_stop']=s['source_change_review_ja']=STOP
    s['bp']['next_step']=s['next_action']['goal_ja']=NEXT
    s['next_action']['read_paths']=[REPORT,'scripts/pr16_circus_entry.py','overlays/circus_admission/circus_script.c',
        'content/modernization/pr16_circus_admission_checkpoint.json','content/modernization/p08_remaining_work.json']
    s['next_action']['host_write_policy_ja']='新しい実受付のguard開始後は入力/frames/readのみ。施設番号/効果/連勝/party/PC/LRのhost注入は禁止。初期配置fixtureと実入場/正規連勝を区別する。'
    s['remaining_sequence_ja']='Circus受付候補生成まで完了→新規取消/入場/戦闘/保存native→Circus固有streak正規更新/永続化と抑制→影響台帳P08移送→release判定。'
    s['session_execution_summary']=dict(new_emulator_processes=0,accepted_standalone_replays=0,
        engineering_candidate_changes=1,record_scope_rom_changes=0,source_tests=23,
        scope_ja='今回の専用build工程。自動Stage79 CIを新規Circus native受入に数えない。')
    s['do_not_repeat'].insert(0,'Circus実受付候補の23件/独立2link/限定2patchと原本を再利用。失敗run35359098745のmetadata名誤仮定とrun35359681701のveneer整列を再発させない。無変更の旧7関数/link/5335root/nativeは再実行しない。')
    for key in ('candidate','status','latest_native_run','latest_native_job','latest_native_tested_head',
                'last_accepted_native_run','last_accepted_native_tested_head','release_ready','remaining_physical_gap_ids','remaining_p08_gate_ids'):
        need(s[key]==state[key],'formal acceptance authority changed')
    for old,new in zip(backlog['remaining_conditions'],b['remaining_conditions']):
        if old['id']!='PHYSICAL_CIRCUS_ADMISSION':need(old==new,'unrelated condition changed')
    return s,b


def run():
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'write scope differs')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout differs');ops.assert_remote(head)
    subprocess.run(['git','merge-base','--is-ancestor',BASE,head],cwd=ROOT,check=True)
    need(not (ROOT/REPORT).exists(),'already recorded; reuse saved checkpoint')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'dirty tracked source')
    OUT.mkdir(parents=True,exist_ok=True)
    state=resume.validate(ROOT);backlog=resume.load(ROOT,resume.BACKLOG)
    bp=identity((ROOT/resume.CHECKPOINT).read_bytes());spec=load((ROOT/SPEC).read_bytes())
    bundles={};metadata={}
    for key,item in spec['artifacts'].items():
        subprocess.run(['git','merge-base','--is-ancestor',item['tested_head'],head],cwd=ROOT,check=True)
        files,manifest,verified=evidence.checked(item,ops)
        bundles[key]=files;metadata[key]=dict(spec=item,verified=verified,member_manifest=manifest)
    build=load(bundles['build']['pr16-circus-entry/report.json']);validate_build(build,spec['artifacts']['build'])
    evidence.verify_sources(ROOT,build['sources'])
    evidence.tests_pass(bundles['build']['pr16-circus-entry-run/tests.stderr'],23)
    failures=[]
    for key,phrase in (('failed_metadata',"KeyError: 'script_facility_cancel'"),('failed_alignment','ValueError: script adapter entry drift')):
        raw=bundles[key]['pr16-circus-entry-run/build.stderr'];last=raw.decode().splitlines()[-1]
        need(last==phrase,'original failure cause differs')
        failures.append(dict(run_id=spec['artifacts'][key]['run_id'],conclusion='failure',original_identity=identity(raw),last_line=last,
                             original_available_in_fixed_artifact=True,relabelled_as_success=False))
    report=dict(schema_version=1,task=TASK,classification='CIRCUS_SCRIPT_WIRED_CANDIDATE_BUILT_NATIVE_OPEN',
        tested_head=spec['artifacts']['build']['tested_head'],build_run_id=spec['artifacts']['build']['run_id'],
        record_source_head=head,record_run_id=int(os.environ['GITHUB_RUN_ID']),build=build,verified_artifacts=metadata,
        failed_attempts=failures,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        changed_native_inputs=True,accepted_native_cases_replayed=0,build_native_processes=0,
        input_impact_ja='新Circus受付/3戦闘開始と共有gateway質問のみ。Factory本体/既受入Ring/CFRU ownerは不変。入口対照のみ新変更影響あり。',
        remaining_ja=NEXT,source_bindings={p:identity((ROOT/p).read_bytes()) for p in (*IMPL,SELF,TEST,WORKFLOW,SPEC)})
    s,b=project(state,backlog,report)
    s['observed_head']=head;s['observed_date_jst']=datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    s['observed_head_semantics']='Circus実受付候補生成を記録するsource HEAD。正式BP受入HEADではない。完了SHAはremote ref/記録receiptで確認。'
    s['observed_head_checks']=dict(scope_head=head,verified_artifacts={k:v['verified'] for k,v in metadata.items()},
        reason_ja='専用build原本の成功と先行2失敗を照合。記録runはcommit時in_progress。全CI green/新native受入とは主張しない。')
    s['pending_runs']=[];s['logs_synchronized']=True
    (ROOT/REPORT).write_bytes(stable(report));(ROOT/resume.BACKLOG).write_bytes(stable(b))
    for name in (*IMPL,SELF,TEST,WORKFLOW,SPEC,REPORT):s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    (ROOT/resume.STATE).write_bytes(stable(s));(ROOT/resume.DOC).write_text(resume.render(s),encoding='utf-8')
    resume.validate(ROOT);need(bp==identity((ROOT/resume.CHECKPOINT).read_bytes()),'formal BP checkpoint changed')
    results=[]
    for pattern in (Path(TEST).name,'test_pr16_resume.py'):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (OUT/(pattern+'.txt')).open('w',encoding='utf-8') as stream:t=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(t.wasSuccessful() and t.testsRun>0 and not t.skipped,'record/resume tests failed');results.append(dict(pattern=pattern,count=t.testsRun,success=True))
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    outputs=(REPORT,resume.STATE,resume.DOC,resume.BACKLOG,*ops.LOGS)
    stamp=datetime.now(timezone.utc).isoformat()
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / Circus実受付候補生成\n'
        '- Status: DONE / 候補生成・限定script契約まで。実入場nativeは未受入。\n'
        '- Version: pr16-circus-entry-candidate\n- Summary: '+STOP+'\n'
        '- Files changed: '+', '.join((*IMPL,SELF,TEST,WORKFLOW,SPEC,*outputs))+'\n'
        '- Verify: 新規23件PASS原本、ARM link2回一致、限定patch2回一致、全allocation hash/重複0/2範囲外不変。記録/再開tests、task graph、差分guard、diff checkをcommit前必須。\n'
        f'- Evidence: build run{report["build_run_id"]}; tested_head={report["tested_head"]}; candidate={build["candidate"]["sha256"]}; {REPORT}。元Actions/job/artifact ZIP/member/sourceを照合。\n'
        '- History: run35359098745は存在しないscript名をmetadataへ要求し停止。実CommitSelection拒否edge/Abort ownerで解決。run35359681701はveneer整列で入口4byteずれを検出して停止。16byte割当で解決。失敗原本と最終原因行/hashを保持。\n'
        '- Boundary: 新候補は検証用でrelease採用/active baseline変更なし。専用工程emulator0、受入済みnative手動再実行0。自動Stage79結果を新Circus受入へ流用しない。\n'
        '- Preserved: 正式BP checkpoint不変、Ring/BP/P03/P06/P07受入、physical1/P08 gates2、release_ready=falseを保持。\n'
        f'- Commit: 同branchへ非force push。record source={head}; record run={os.environ["GITHUB_RUN_ID"]}。自己SHAはreceipt/remote refで確認。\n'
        '- Network: GitHub connector/Actionsと既存hash固定入力のみ。新ROM/save/ELF/private ZIPをtrackedへ追加しない。\n'
        '- Next: '+NEXT+'\n')
    for name in ops.LOGS:
        p=ROOT/name;need(('Task: '+TASK+' / Circus実受付候補生成\n') not in p.read_text(),'duplicate completion log')
        with p.open('a',encoding='utf-8') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*outputs],cwd=ROOT,check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*IMPL,SELF,TEST,WORKFLOW,SPEC,*outputs))
    guard.guard();subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);ops.assert_remote(head)
    for k,v in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):subprocess.run(['git','config',k,v],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': 実受付候補生成・23件契約・失敗修復を検証し固定引継ぎへ記録'],cwd=ROOT,check=True)
    commit=ops.cmd('git','rev-parse','HEAD');subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True);ops.assert_remote(commit,attempts=12)
    for name in outputs:need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed output differs')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'post-push tracked source dirty');resume.validate(ROOT)
    receipt=dict(status='PASS_CIRCUS_ENTRY_CANDIDATE_RECORDED',commit=commit,source_head=head,record_run_id=int(os.environ['GITHUB_RUN_ID']),
        branch=ops.BRANCH,tests=results,physical_admission_accepted=False,release_ready=False,formal_bp_checkpoint_unchanged=True,
        output_identities={n:identity((ROOT/n).read_bytes()) for n in outputs})
    (OUT/'receipt.json').write_bytes(stable(receipt));(OUT/'completion-log.txt').write_text(entry)
    for name in (REPORT,resume.STATE,resume.DOC,resume.BACKLOG):
        p=OUT/'final'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    print(json.dumps(receipt,ensure_ascii=False))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


if __name__=='__main__':run()
