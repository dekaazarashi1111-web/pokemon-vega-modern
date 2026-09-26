#!/usr/bin/env python3
"""明示終了処理: 失敗原本の保存と同じMD/JSON・両ログの同期。emulator/ROM更新なし。"""
from __future__ import annotations
import collections
import csv
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_battle_return_checkpoint as c
import pr16_resume as resume
need,git,stable=c.need,c.git,c.stable
SELF='scripts/pr16_bp_battle_return_closeout.py'
TASK='USER-20260913-BP-FIRST-BATTLE'
LOGS=('design/run_log.md','design/version_log.md')
OUT=ROOT/'.local/pr16-bp-battle-return-closeout'
PATHS=(resume.STATE,resume.DOC,resume.BACKLOG,c.REPORT,c.ATTEMPTS,*LOGS,
       c.BASE+'/verification.json',c.BASE+'/actions-snapshot.json',c.BASE+'/reward-source-audit.json',
       *[c.BASE+'/original-'+str(p[0])+'.zip' for p in c.PINS],*[c.BASE+'/actions-'+str(p[0])+'.json' for p in c.PINS])
BINDINGS=(c.native.SELF,c.native.SOURCE,c.native.WORKFLOW,'tests/test_pr16_bp_battle_return.py',
          c.SELF,SELF,'tests/test_pr16_bp_battle_return_checkpoint.py',c.ATTEMPTS,
          'overlays/facility_runtime/facility_runtime.c','manifests/facility_rewards.csv',
          'overlays/factory_reward_runtime/factory_reward_runtime.c',
          'overlays/factory_repeat_reward_runtime/factory_repeat_reward_runtime.c')


def put(name,data,create_only=False):
    path=resume.safe_path(ROOT,name);path.parent.mkdir(parents=True,exist_ok=True)
    if create_only and path.exists():need(path.read_bytes()==data,'retained original differs: '+name)
    else:path.write_bytes(data)


def snapshot(head):
    data=c.parse(c.api('actions/runs?head_sha='+head+'&per_page=100'));rows=data['workflow_runs']
    need(len(rows)==data['total_count']<=100 and all(r['head_sha']==head for r in rows),'incomplete head Actions snapshot')
    return [{k:r[k] for k in ('id','name','path','head_sha','event','status','conclusion','created_at','updated_at')} for r in rows]


def reward_sources():
    paths=BINDINGS[-3:]
    rows={r['facility_reward_key']:r for r in csv.DictReader((ROOT/paths[0]).read_text().splitlines())}
    first=rows['FACILITY_REWARD_KEY_TRIAL_BP'];repeat=[rows['FACILITY_REWARD_KEY_TRIAL_REPEAT_BP'+str(i)] for i in (1,2)]
    need(first['amount']=='3' and all(r['status']=='ACTIVE' for r in [first,*repeat]),'reward manifest changed')
    need([r['amount'] for r in repeat]==['1','2'],'repeat manifest changed')
    first_src=(ROOT/paths[1]).read_text();repeat_src=(ROOT/paths[2]).read_text()
    need('FACTORY_REWARD_FIRST_CLAIM_MASK' in first_src and 'persist_standard_save()' in first_src,'first reward owner changed')
    need('u8 repeat_eligible = repeat_eligible_before_completion();' in repeat_src and 'FN_STAGE28_COMPLETE()' in repeat_src,'repeat reward owner changed')
    return dict(schema_version=1,classification='SOURCE_CONDITIONS_NOT_NATIVE_BP_ACCEPTANCE',
        sources={p:c.identity((ROOT/p).read_bytes()) for p in paths},
        stage28_first_bonus_bp=3,stage29_repeat_bonus_bp_options=[1,2],stage29_required_claim_mask_before_delegate=14,
        conditions_ja='Stage28は初回claim mask未充足時、XS5/S2のBag追加成功後に追加BP3とclaim bitsを保存。Stage29はdelegate前にmask0x0Eが揃う場合だけrepeat item/BP1または2を補償transactionとして追加。Bag失敗や保存失敗は別条件。',
        standard_save_calls_exist_in_reward_wrappers=True,
        actual_candidate_chain_observed_through='093C42C9 -> 092DE351 -> 092DDCE9 -> 092DDAA9 -> 092DD419 (Stage28 delegate)',
        full_candidate_completion_chain_resolved=False,final_native_bp_total_observed=False,
        reward_runtime_executed_in_failed_battle=False,new_emulator_processes=0,rom_changes=0,
        native_bp_earning_accepted=False,release_ready=False)


def documents(report,head,actions,pr):
    row=report['rows'][-1];r=row['native_result'];old=resume.load(ROOT,resume.STATE)
    need(old['latest_native_run'] in (34741232621,34749370272),'another native result must be reconciled')
    for path,bound in old['source_bindings'].items():need(c.identity((ROOT/path).read_bytes())==bound,'prior bound source changed: '+path)
    need(r['whiteout_callback2']==0x08055F65 and r['final_script_pointer']==0 and not r['native_afterbattle_observed'],'WhiteOut evidence binding changed')
    old['last_successful_native_diagnostic']=dict(run_id=34741232621,job_id=103681167660,tested_head='88e043592f07c80d1e4f582320bb955243986711',path='content/modernization/pr16_bp_progress_diagnostic.json',scope='FIRST_TURN_NOT_BP')
    diag=dict(schema_version=1,classification='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',
        **{k:row[k] for k in ('run_id','job_id','tested_head','zip','native_result','original_conclusion','first_unmatched_condition')},
        original_zip=c.BASE+'/original-34749370272.zip',verification=c.BASE+'/verification.json',
        raw_native_stdout_empty=True,raw_native_status='FAIL',
        observations_are_derived_from_failed_stderr_not_success_stdout=True,
        visual_review_ja='2026-09-13に原本PPMのbattle-outcome、forced-switch-return、facility-afterbattleを目視。最後は施設ではなく室内別マップ。battle-outcome画像自体には敗北文字列がまだ描画されていないため、敗北判定はoutcome=2/HP0のnative traceに基づく。switch画像は後の同名保存が残るため2回分の別画像があるとは主張しない。',
        native_screens=row['native_screens'],native_bp_earning_accepted=False,release_ready=False)
    put(c.REPORT,stable(diag))
    attempts=resume.load(ROOT,c.ATTEMPTS)
    matches=[a for a in attempts['attempts'] if a['run_id']==row['run_id']];need(len(matches)==1,'attempt identity absent or duplicated')
    matches[0].update(status_at_checkpoint='completed',conclusion_at_checkpoint='failure',native_result_verified=True,actual_native_processes=1,
        successful_fresh_cores=0,artifact_id=row['artifact_id'],zip=row['zip'],native_observations=c.REPORT,
        first_unmatched_condition=row['first_unmatched_condition'])
    attempts.update(next_ja='敗北後WhiteOut callbackと失われるfacility script復帰の所有者を候補ROMで固定し、最小修復後だけ影響区間を再検証する。現行bffdの同一敗北診断は再実行しない。',originals_verified=c.BASE+'/verification.json')
    put(c.ATTEMPTS,stable(attempts))
    goal='敗北後11405fのCB2_WhiteOut(08055F65)分岐と、11525fに092CF669から失われるscript復帰の所有者を固定候補ROMで追う。FacilityRuntime_AfterBattleへnativeに戻す最小修復を設計し、その変更後だけ敗北・元party復元を再検証する。'
    stop='run34749370272/job103703085018はfailure。初回turn3925f後、追加8turn/PP消費8回と瀕死交代2回、11261fでnative敗北outcome2を観測。11405fにCB2_WhiteOutへ移り、11525fでfacility script pointerが0へ。93925fまで元party復元なし、map4/0(8,5)、party3/snapshot1/marker2、BP0/save counter2。FacilityRuntime_AfterBattle帰還・勝利・BP稼得は未観測。'
    old.update(status=r['status'],observed_head=head,latest_native_run=row['run_id'],latest_native_job=row['job_id'],
        latest_native_tested_head=row['tested_head'],latest_native_evidence=c.REPORT,latest_native_scope=diag['classification'],
        pending_runs=[],pr_state=pr['state'],pr_draft=pr['draft'],pr_merged=pr['merged'],logs_synchronized=True,p08_resume_synchronized=True)
    old['bp'].update(current_stop=stop,next_step=goal,native_loss_observed=True,loss_frame=11261,
        loss_return_to_facility_observed=False,loss_party_restoration_verified=False,
        after_battle_launch='1戦敗北は実測済みだが施設へ戻らずsnapshot/marker/レンタルpartyが残存する。交換修正や勝利だけを先に進めて負例を隠さない。Trial reward0はID、基本9BP。manifest/Stage28追加BP3とStage29 repeat1/2の条件を読取照合したが、候補上の全completion chainと最終付与量は未確定。交換operand092CF729/092CF775のsingle-selection ABI修正は敗北復帰の後。初期chooser修正、受入取消/Save/Continueは再実施しない。')
    old['next_action'].update(id='BP_LOSS_RETURN_CALLBACK_OWNER',goal_ja=goal,
        read_paths=[c.REPORT,c.native.SOURCE,c.native.SELF,'overlays/facility_runtime/facility_runtime.c','scripts/build_facility_runtime.py',c.native.WORKFLOW,c.BASE+'/reward-source-audit.json'],
        success_observations=['native loss returns to facility script and calls AfterBattle','original 600 party bytes and count restored; snapshot/marker cleared','BP and full save counter unchanged in loss control','separate winner/exchange/reward acquisition acceptance remains pending'],
        stop_rule_ja='同一bffd・同一controllerの93925f敗北失敗を再実行しない。WhiteOut所有者とfacility return callback/scriptのcandidate bytesを読取監査してから最小修復する。勝敗/HP/RNGをhost注入せず、復元assertionやtimeoutを緩めない。失敗stdoutが空でPython JSON parse errorになっているが、根本のnative failureはstderr末尾のAfterBattle不達。')
    old['current_failed_native_attempt']=row
    old['do_not_repeat']=list(dict.fromkeys(['run34749370272の敗北→WhiteOut→party未復元はfailure原本で保持。同一sourceで再実行せず、native return修復後の影響区間だけ検証する。',*old['do_not_repeat']]))
    old['latest_native_summary_ja']='原本ZIP883756bytes/SHA9fa6bdf3dc7a4ad316788413b61687c90e23882c742ca938388f9e531ad9ed0c、82member/79source/24completion-chain source、生成C、7guard、raw stdout空/process exit1/stderr失敗を照合。新規実戦process1、成功fresh core0。観測抄録は失敗stderrから抽出したものと明記し、成功JSONへ代作しない。'
    old['prepared_native_probe']=dict(case=c.native.CASE,execution_status='FAILED_NATIVE_LOSS_RETURN_BLOCKED',source_only_tests=13,rom_changes=0,historical_cancel_replayed=False,run_id=row['run_id'],job_id=row['job_id'],tested_head=row['tested_head'])
    old['session_execution_summary']=dict(native_game_processes=1,failed_native_processes=1,successful_native_fresh_cores=0,accepted_cancel_replays=0,rom_source_changes=0,closeout_emulator_processes=0,native_bp_earning_accepted=False,scope_ja='追加BP専用診断のみ。pushで自動起動する既存CI/Stage79はActions一覧へ別記。')
    old['source_change_review_ja']='新C/Pythonだけで既存first-turn controllerを完全hash固定して派生。ROM/fixture/7write barrierと既存受入sourceは不変。native敗北後の未復元をassertion通り失敗として保持。コードが新callbackへ到達する事実と修復未完を分離し、原本JSON/statusを変更しない。'
    old['reward_source_conditions_audit']=c.BASE+'/reward-source-audit.json'
    old['observed_head_checks']=dict(status='NATIVE_FAILURE_GENERAL_CHECKS_SEPARATE',checked_head=head,native_tested_head=row['tested_head'],
        native_head_runs=actions['native_head_runs'],closeout_entry_runs=actions['closeout_entry_runs'],
        reason_ja='BP run34749370272/job103703085018はnative帰還/復元不達でfailure。source13件と7guard、原本再検証は別判定。初期HEADの5 Actionsと前回closeout成功を照合済み。一般CIのpending/failureをこの診断成功へ読み替えず、最終記録commitの全Checks完了も主張しない。')
    for path in BINDINGS:old['source_bindings'][path]=c.identity((ROOT/path).read_bytes())
    old['source_bindings'][c.BASE+'/reward-source-audit.json']=c.identity((ROOT/c.BASE/'reward-source-audit.json').read_bytes())
    backlog=resume.load(ROOT,resume.BACKLOG)
    for row in backlog['remaining_conditions']:
        if row['id'] in ('NATURAL_CAPTURE_GEAR','FINAL_NATIVE_ACCEPTANCE'):row['resume']='Current resume: '+resume.DOC+'. '+stop+' Next: '+goal
    put(resume.BACKLOG,stable(backlog));put(resume.STATE,(json.dumps(old,ensure_ascii=False,indent=2)+'\n').encode())
    put(resume.DOC,resume.render(old).encode());resume.validate(ROOT)


def retain():
    head=git(ROOT,'rev-parse','HEAD').decode().strip();need(head==os.environ.get('GITHUB_SHA'),'wrong checkout HEAD')
    for pin in c.PINS:
        meta=c.metadata(pin);raw=c.api('actions/artifacts/'+str(pin[2])+'/zip');c.verify(raw,pin,ROOT)
        put(c.BASE+'/original-'+str(pin[0])+'.zip',raw,True);put(c.BASE+'/actions-'+str(pin[0])+'.json',stable(meta))
    report=c.check(ROOT);put(c.BASE+'/verification.json',stable(report))
    put(c.BASE+'/reward-source-audit.json',stable(reward_sources()))
    actions=dict(observed_at=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),native_head_runs=snapshot(c.PINS[-1][3]),closeout_entry_runs=snapshot(head))
    put(c.BASE+'/actions-snapshot.json',stable(actions))
    pr=c.parse(c.api('pulls/16'))
    need(pr['state']=='open' and pr['draft'] is True and pr['merged'] is False and pr['head']['sha']==head and pr['head']['ref']=='codex/modernization-followup-20260908','PR/branch changed')
    documents(report,head,actions,pr)
    print(stable(dict(status='RETAINED_FAILURE_AND_FIXED_HANDOFF_SYNCED',new_emulator_processes=0,paths=list(PATHS))).decode(),end='')


def logs():
    resume.validate(ROOT);head=git(ROOT,'rev-parse','HEAD').decode().strip()
    unit=(OUT/'unit.stderr').read_text();matches=re.findall(r'Ran (\d+) tests?',unit)
    need(len(matches)==1 and re.search(r'^OK$',unit,re.M),'focused source/evidence/resume tests did not all pass')
    count=int(matches[0]);now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry=(f'\n\n## {now} — {TASK}\n- Task: {TASK} / 初回turnから1戦勝敗・施設帰還へ延長\n'
        '- Status: STOPPED / native敗北後WhiteOut・元party復元不達。原本保存と固定引継ぎ同期は完了。\n'
        '- Summary: 新C/Pythonを追加し、既存first-turn sourceをhash固定して派生。初期HEAD10e657fと正本・最新Actionsを照合し、受入済み取消の単独再実行0。ROM/source/baselineの変更0。\n'
        '- Native FAIL: run34749370272/job103703085018/HEAD96ad7823a147e1db6ea8f411c77650b27a4f3102。追加8turn/PP消費8回・瀕死交代2回後、11261fでoutcome2。11405fのCB2_WhiteOut(08055F65)から11525fでfacility scriptが0へ。93925f map4/0(8,5)、party3/snapshot1/marker2残存。BP0/save counter2。復元assertion/timeoutを緩めずfailure原本を保持。\n'
        '- Evidence: ZIP883756bytes/SHA9fa6bdf3dc7a4ad316788413b61687c90e23882c742ca938388f9e531ad9ed0c。82member/79source/24chain-source・Git tested HEAD・生成C・7guard・stdout空/process exit1/stderrを照合。観測抄録は失敗stderr由来と明記し、原本statusを成功へ書換えない。\n'
        '- Reward audit: Stage28初回追加BP3・Stage29事前claim mask0x0Eでrepeat BP1/2のsource条件を確認。基本9BPとの最終合計、全completion chain、稼得/消費のnative受入は未完。\n'
        f'- Verify: native controller compile -Werror PASS; source13 PASS; closeout focused {count} tests PASS; resume check/task graph/git diff --check PASS。index/HEAD原本byte同一検査。標準private guard既存結果は保持し、新規差分違反0を別検査。native帰還検査はFAILのまま。\n'
        '- Counts: 新規BP実戦process1、成功fresh core0、closeout emulator0。push自動CIはhead別Actions一覧へ分離。\n'
        '- Next: 5D launch/敗北callback/施設script復帰所有者を候補ROMで固定し最小修復。その変更後に敗北と元party600bytes復元を検証。現在の同一失敗を再実行しない。勝利・交換・3勝報酬・Save/Continue・稼得BP消費は後続。\n'
        '- Files changed: '+', '.join((c.native.SELF,c.native.SOURCE,c.native.WORKFLOW,c.SELF,SELF,'tests/test_pr16_bp_battle_return.py','tests/test_pr16_bp_battle_return_checkpoint.py',*PATHS))+'\n'
        f'- Commit: source {head}; この追記を含むcommitはGit履歴が正本（自己SHA循環は作らない）。\n'
        '- Network利用: GitHub repo/ref/PR/Actions/artifactを接続APIとActions ghで取得。既存private-environment releaseから固定inputを一時復元。新release/merge/draft解除/baseline切替なし。\n')
    for name in LOGS:
        with resume.safe_path(ROOT,name).open('a',encoding='utf-8') as f:f.write(entry)
    print('APPENDED_BOTH_LOGS_WITH_NATIVE_FAILURE_RETAINED')


def stage():
    need(not git(ROOT,'diff','--cached','--name-only').strip(),'pre-existing staged work')
    subprocess.run(['git','add','--',*PATHS],cwd=ROOT,check=True)


def guard():
    import guard_private_files as g
    base=os.environ['GITHUB_SHA'];changed=[p for p in git(ROOT,'diff','--cached','--name-only','-z',base).decode().split('\0') if p]
    need(set(changed)==set(PATHS),'unexpected closeout changed paths')
    for name in changed:
        raw=git(ROOT,'show',':'+name);need(raw==(ROOT/name).read_bytes(),'staged bytes differ')
        if name.endswith('.zip'):c.scan(raw);need(not g.blocked_zip_members(raw),'new archive private payload')
        else:
            raw.decode('utf-8');need(b'\0' not in raw,'new binary')
            prior=subprocess.run(['git','show',base+':'+name],cwd=ROOT,capture_output=True).stdout
            def bad(b):
                lines=b.decode('utf-8',errors='replace').splitlines()
                return collections.Counter(lines[i-1] for i in g.document_user_path_lines(b))
            need(not (bad(raw)-bad(prior)),'new user path violation')
        need(Path(name).suffix not in g.BLOCKED_SUFFIXES and not any(name==p or name.startswith(p+'/') for p in g.BLOCKED_PARTS),'new private path')
    with tempfile.TemporaryDirectory(dir=OUT) as tmp:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(tmp)/'base.index'));subprocess.run(['git','read-tree',base],cwd=ROOT,env=env,check=True)
        cmd=[sys.executable,'scripts/guard_private_files.py']
        before=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True);after=subprocess.run(cmd,cwd=ROOT,capture_output=True)
    need(before.returncode in (0,1) and (before.returncode,before.stdout,before.stderr)==(after.returncode,after.stdout,after.stderr),'standard guard results changed')
    report=dict(base=base,changed_paths=changed,full_index_guard_before=before.returncode,full_index_guard_after=after.returncode,exact_output_match=True,new_violations=0,full_guard_pass_claimed=after.returncode==0,new_emulator_processes=0)
    (OUT/'guard-boundary.json').write_bytes(stable(report));print(stable(report).decode(),end='')

if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('retain','logs','stage','guard'),'explicit closeout action required')
    globals()[sys.argv[1]]()
