#!/usr/bin/env python3
"""明示closeout専用。原本をcreate-only保持し、同じ引継ぎと両ログだけを同期する。"""
from __future__ import annotations
import collections
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_bp_progress_checkpoint as c
import pr16_resume as resume
need,git,stable=c.need,c.evidence.git,c.stable
TASK='USER-20260913-BP-REWARD-FIRST-TURN'
SELF='scripts/pr16_bp_progress_closeout.py'
ATTEMPTS='content/modernization/pr16_bp_progress_attempts.json'
LOGS=('design/run_log.md','design/version_log.md')
BINDINGS=(c.native.SELF,c.native.SOURCE,c.native.WORKFLOW,'tests/test_pr16_bp_battle_progress.py',c.SELF,SELF,'tests/test_pr16_bp_progress_checkpoint.py',ATTEMPTS)
PATHS=(resume.STATE,resume.DOC,resume.BACKLOG,c.REPORT,ATTEMPTS,*LOGS,c.BASE+'/verification.json',c.BASE+'/actions-snapshot.json',*[c.BASE+'/original-'+str(p[0])+'.zip' for p in c.PINS],*[c.BASE+'/actions-'+str(p[0])+'.json' for p in c.PINS])


def put(name,data,create_only=False):
    path=resume.safe_path(ROOT,name);path.parent.mkdir(parents=True,exist_ok=True)
    if create_only and path.exists():need(path.read_bytes()==data,'existing retained bytes differ: '+name)
    else:path.write_bytes(data)


def snapshot(api,head):
    rows=c.parse(api('actions/runs?head_sha='+head+'&per_page=100'))['workflow_runs']
    return [{k:r[k] for k in ('id','name','path','head_sha','event','status','conclusion','created_at','updated_at')} for r in rows]


def documents(report,head,actions,pr):
    latest=report['rows'][-1];r=latest['native_result'];old=resume.load(ROOT,resume.STATE)
    need(old['latest_native_run'] in (34739491272,34741232621),'another native update must be reconciled')
    for path,bound in old['source_bindings'].items():need(c.identity((ROOT/path).read_bytes())==bound,'old source changed: '+path)
    diag=dict(schema_version=1,classification='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',run_id=latest['run_id'],job_id=latest['job_id'],tested_head=latest['tested_head'],native_result=r,original_zip=c.BASE+'/original-34741232621.zip',zip=latest['zip'],verification=c.BASE+'/verification.json',original_failed_run=34741024241,static_reward_run=34740626514,reviewed_screens=latest['reviewed_screens'],visual_review_ja='元PPMを目視。技メニュー、技発動、敵技後HPを確認。3925fは次action callback到達で、最終画像のactionメニュー描画完了は主張しない。',completion_chain_fully_resolved=False,native_bp_earning_accepted=False,release_ready=False)
    put(c.REPORT,stable(diag))
    attempts=resume.load(ROOT,ATTEMPTS)
    if not any(a['run_id']==latest['run_id'] for a in attempts['attempts']):
        attempts['attempts'].append({k:latest[k] for k in ('run_id','job_id','artifact_id','tested_head','zip','original_conclusion','classification','new_emulator_processes','successful_fresh_cores')})
    attempts['latest_successful_diagnostic']=c.REPORT
    attempts['originals_verified']=c.BASE+'/verification.json'
    put(ATTEMPTS,stable(attempts))
    goal='実行動callback復帰3925fから1戦のnative勝敗・FacilityRuntime_AfterBattle帰還へ延長する。後発completion wrapperの加算条件と交換2か所のsingle-selection ABIを確認し、未観測区間に必要な範囲だけ修正する。'
    old.update(status=r['status'],observed_head=head,latest_native_run=latest['run_id'],latest_native_job=latest['job_id'],latest_native_tested_head=latest['tested_head'],latest_native_evidence=c.REPORT,latest_native_scope=diag['classification'],pending_runs=[],pr_state=pr['state'],pr_draft=pr['draft'],pr_merged=pr['merged'],logs_synchronized=True,p08_resume_synchronized=True)
    old['bp'].update(current_stop='run34741232621で実行動3260f→技メニュー3412f→技選択3413f→PP24から23へ減少3430f→次action callback3925fを観測。技247、敵HP167→139・自HP171→119、BP0、元party600bytes/Save counter2不変。初回turn診断は成功。勝利・施設帰還・BP獲得/消費は未観測。',next_step=goal,native_first_turn_observed=True,move_id=247,pp_before=24,pp_after=23,action_return_frame=3925,after_battle_launch='Trial reward0は報酬IDで0BPではない。正本と候補headerは3戦・基本9BP。実完了先093C42C9→092DE351→092DDCE9を追跡したがStage29以降を含む全wrapper加算/最終付与量は未確定。交換operand092CF729/092CF775はspecial2F→080CBF8D(7047)とwaitstateのまま。初期chooser092CF629の修正は再実施しない。3勝、初回/繰返し/負例、通常Save/fresh Continue、獲得BP消費は別途正式受入。')
    old['next_action'].update(id='BP_FIRST_BATTLE_RETURN_AND_EXCHANGE',goal_ja=goal,read_paths=[c.REPORT,c.native.SOURCE,c.native.SELF,'overlays/facility_runtime/facility_runtime.c','config/factory_high_modes_v2.json',c.native.WORKFLOW],success_observations=['native first battle win/loss and facility return without host outcome writes','full completion-wrapper reward conditions separately verified','narrow exchange single-selection ABI verified before repair','BP acquisition and consumption remain separate acceptance'],stop_rule_ja='3260f到達だけ、または初回turn3925fだけの同一診断を繰り返さず次の未観測区間へ進む。command12は描画より早いため実command14遷移まで観測。reward ID0を0BP扱いしない。最初の不一致をframe/callback/run/job付きで保持する。')
    old['do_not_repeat'].insert(3,'run34741232621の技選択・PP消費・次action callback3925fは、source影響なしに単独再実行しない。失敗run34741024241はfailureのまま保持する。')
    old['do_not_repeat']=list(dict.fromkeys(old['do_not_repeat']))
    old['latest_native_summary_ja']='原本ZIP786377bytes/SHA3deea9de7c0bf3eb154ab71de460a33e70a20e9d65c106a4d5bebbdf46c98e3e、76member/74source/10completion-chain source・生成controller・7guard・stdout/processを照合。fresh core1、3925frames、warning0。実行済み2試行(失敗1/成功1)。受入済み取消/Save/Continueの単独再実行0、原本再照合emulator0。'
    old['prepared_native_probe']=dict(case=c.native.CASE,execution_status='COMPLETED_DIAGNOSTIC_SUCCESS',source_only_tests=6,rom_changes=0,historical_cancel_replayed=False,run_id=latest['run_id'],job_id=latest['job_id'],tested_head=latest['tested_head'])
    old['session_execution_summary']=dict(native_game_processes=2,failed_native_processes=1,successful_native_fresh_cores=1,accepted_cancel_replays=0,rom_source_changes=0,closeout_emulator_processes=0,native_bp_earning_accepted=False)
    old['session_execution_summary']['scope_ja']='今回追加したBP専用診断の計数。pushで自動起動する既存CI/Stage79は別のhead別Actions一覧に記録し、追加BP受入へ読み替えない。'
    old['source_change_review_ja']='既存launch C/Pythonを完全hash固定して追加controllerを派生。失敗原本の3322f action画面から最初のAが早過ぎたことを確認し、新Cだけに実command14遷移待ちを追加。ROM/fixture/7barrierは不変。closeoutは全ZIP/sourceをGit tested HEADと照合し、引継ぎ/ログ/evidence以外の既存sourceを書き換えない。'
    old['reward_route_audit']=report['rows'][0]
    old['current_failed_native_attempt']=report['rows'][1]
    old['observed_head_checks']=dict(status='NATIVE_FIRST_TURN_SUCCESS_GENERAL_CHECKS_SEPARATE',checked_head=head,native_tested_head=latest['tested_head'],native_head_runs=actions['native_head_runs'],closeout_entry_runs=actions['closeout_entry_runs'],reason_ja='native34741232621/job103681167660は成功し原本とGit sourceを照合。一般CI/Stage79の状態はhead別Actions一覧に分離。実行中/action_required/failureを成功へ読み替えず、この記録commitの全Checks完了は主張しない。')
    for path in BINDINGS:old['source_bindings'][path]=c.identity((ROOT/path).read_bytes())
    backlog=resume.load(ROOT,resume.BACKLOG)
    for row in backlog['remaining_conditions']:
        if row['id'] in ('NATURAL_CAPTURE_GEAR','FINAL_NATIVE_ACCEPTANCE'):row['resume']='Current resume: '+resume.DOC+'. '+old['bp']['current_stop']+' Next: '+goal
    put(resume.BACKLOG,stable(backlog))
    put(resume.STATE,(json.dumps(old,ensure_ascii=False,indent=2)+'\n').encode())
    put(resume.DOC,resume.render(old).encode())
    resume.validate(ROOT)


def retain():
    head=git(ROOT,'rev-parse','HEAD').decode().strip();need(head==os.environ.get('GITHUB_SHA'),'checkout is not requested HEAD')
    for pin in c.PINS:
        meta,api=c.evidence.metadata(pin)
        raw=api('actions/artifacts/'+str(pin[2])+'/zip');c.verify(raw,pin,ROOT)
        put(c.BASE+'/original-'+str(pin[0])+'.zip',raw,True)
        minimal=dict(schema_version=1,run={k:meta['run'][k] for k in ('id','head_sha','run_attempt','status','conclusion','created_at','updated_at','event')},job={k:meta['jobs']['jobs'][0][k] for k in ('id','status','conclusion')},artifact={k:meta['artifact'][k] for k in ('id','name','size_in_bytes','digest','expired')})
        put(c.BASE+'/actions-'+str(pin[0])+'.json',stable(minimal))
    report=c.check(ROOT);put(c.BASE+'/verification.json',stable(report))
    actions=dict(observed_at=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),native_head_runs=snapshot(api,c.PINS[-1][3]),closeout_entry_runs=snapshot(api,head))
    put(c.BASE+'/actions-snapshot.json',stable(actions))
    pr=c.parse(api('pulls/16'))
    need(pr['state']=='open' and pr['draft'] is True and pr['merged'] is False and pr['head']['sha']==head and pr['head']['ref']=='codex/modernization-followup-20260908','PR/branch changed')
    documents(report,head,actions,pr)
    print(stable(dict(status='RETAINED_AND_RESUME_SYNCED',new_emulator_processes=0,latest_native_run=c.PINS[-1][0],paths=list(PATHS))).decode(),end='')


def logs():
    head=git(ROOT,'rev-parse','HEAD').decode().strip();now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry=(f'\n\n## {now} — {TASK}\n'
        f'- Task: {TASK} / 報酬・交換bindingと初回native turn\n'
        '- Status: DONE_SCOPED_FIRST_TURN_DIAGNOSTIC; BP_EARNING_PENDING\n'
        '- Summary: Trial reward ID0と付与基本量9を区別。候補header3戦/9BPと交換operand092CF729/092CF775のspecial2F→080CBF8D(7047)を照合。全completion wrapper加算条件は未確定。\n'
        '- Native: 成功run34741232621/job103681167660/HEAD88e043592f07c80d1e4f582320bb955243986711。技247/PP24→23、敵HP167→139、自HP171→119、次action callback3925f。BP0、元party600bytesとSave counter2不変、7barrier、warning0。勝利/施設帰還/稼得BP/消費は未観測。\n'
        '- Failure retained: run34741024241/job103680639752は技選択前3322fでnative move menu absent。旧Aが描画前だったため新Cのみ実command14遷移待ちに修正。failure原本を成功へ再分類しない。\n'
        '- Evidence: 静的34740626514、失敗34741024241、成功34741232621の原本ZIPを再ZIPせず保持。size/SHA256、全member、Git tested-head source、生成C、raw stdout/stderr/process、7guardを照合。verification.jsonとactions-*.jsonが正本。\n'
        '- Verify: native focused6・resume18・retention7、resume check、task graph、git diff --check。元の正式取消checkpointとfixed-form5件は読取確認のみ。index原本とHEAD原本を照合。標準private guard既存違反は保持し、新規差分0を別検査。全体guard PASSとは主張しない。\n'
        '- Execution: BP専用診断2process(失敗1/成功1core)、取消/Save/Continueの単独再実行0、closeout emulator0、ROM source変更0。自動CI/Stage79は別記録。\n'
        '- Files changed: 初回turn C/Python/tests/workflow、原本/検証/診断抄録/保持checker、同じ固定resume MD/JSON、P08再開文、両ログ。\n'
        '- Next: 1戦のnative勝敗・AfterBattle帰還、completion wrapper全加算と交換single-selection ABI。physical4/P08 gates2は未完のまま。\n'
        f'- Commit: この記録を含むcommit。照合入力HEAD={head}、closeout run={os.environ.get("GITHUB_RUN_ID") }。自己SHAを追って無限更新しない。\n'
        '- Network: GitHub connector/Actions API原本。PRopen/draft維持、merge/release/active baseline変更なし。\n')
    for name in LOGS:
        path=resume.safe_path(ROOT,name)
        if TASK not in path.read_text():
            with path.open('a',encoding='utf-8') as f:f.write(entry)
    resume.validate(ROOT)


def guard(base):
    import guard_private_files as g
    changed=[p for p in git(ROOT,'diff','--cached','--name-only','-z',base).decode().split('\0') if p]
    need(set(changed)==set(PATHS),'changed paths differ from explicit closeout set')
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
    out=ROOT/'.local/pr16-bp-progress-closeout';out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(tmp)/'base.index'))
        subprocess.run(['git','read-tree',base],cwd=ROOT,env=env,check=True)
        cmd=[sys.executable,'scripts/guard_private_files.py']
        before=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True);after=subprocess.run(cmd,cwd=ROOT,capture_output=True)
    need(before.returncode in (0,1) and (before.returncode,before.stdout,before.stderr)==(after.returncode,after.stdout,after.stderr),'standard guard results changed')
    report=dict(base=base,changed_paths=changed,full_index_guard_before=before.returncode,full_index_guard_after=after.returncode,exact_output_match=True,new_violations=0,full_guard_pass_claimed=after.returncode==0,new_emulator_processes=0)
    (out/'guard-boundary.json').write_bytes(stable(report));print(stable(report).decode(),end='')


if __name__=='__main__':
    need(sys.argv[1:] in (['retain'],['logs'],['stage'],['guard']),'explicit retain/logs/stage/guard required')
    command=sys.argv[1]
    if command=='retain':retain()
    elif command=='logs':logs()
    elif command=='stage':subprocess.run(['git','add','-f','--',*PATHS],cwd=ROOT,check=True)
    else:guard(os.environ['GITHUB_SHA'])
