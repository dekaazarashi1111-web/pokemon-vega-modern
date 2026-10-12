#!/usr/bin/env python3
"""Lv7自然習得新区間の実装保存・独立測定・終端回収。受入済み入力を再生しない。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_story_training as m
import pr16_research_story_route_actions as helper
from pr16_learnset_compact_record import publish_resume

d=helper.d
TASK='USER-20260928-RESEARCH-STORY-TRAINING'
SELF='scripts/pr16_research_story_training_actions.py'
WF='.github/workflows/pr16-research-story-training.yml'
TERMINAL_WF='.github/workflows/pr16-research-story-training-terminal.yml'
GUIDE='docs/PR16_RESEARCH_STORY_TRAINING_JA.md'
CP='content/modernization/pr16_research_story_training_checkpoint.json'
TERMINAL='content/modernization/pr16_research_story_training_terminal.json'
SESSION='content/modernization/pr16_research_story_training_session.json'
CONTEXT='.github/workflows/pr16-research-story-training-context.yml'
OUT=ROOT/'.local/pr16-story-training-run'
PUBLIC=OUT/'public';ART=OUT/'checkpoint'
ARTNAME='pr16-research-story-training-checkpoint'
CODE={SELF,m.SOURCE,m.TEST,m.BUILDER}
GOAL='野生ヒメグマ勝利1回・経験値41・Lv6→7・すいとる自然習得・Save counter4→5と独立Continueを限定受入。経験値245、HP13/23・麻痺・技PP31/30/25が保持。自宅local1はT17渡航の船運休で回復しない事実を実画面/全party/ROM pointer鎖に結合。次は原作Vega/stage16の母親previous_scriptと渡航ownerを照合し、正常回復との共存を最小差分で修正・検証してからtraining.srmで通常進行。研究施設到達は未完。旧194/367/301/114入力・starter/RP/UI/BP/P08は再生しない。'
EXPECTED_STEPS=['Set up job','Run actions/checkout@v4','Measure only new training interval and independent successor Continue','Record immutable evidence fixed resume and append-only logs','Task graph fixed resume and scoped final index','Non-force scoped completion commit','Preserve text completion snapshot','Preserve partial progress without replay','Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']
# Helpers operate on this new namespace only; no old measure/record/test entrypoint is called.
helper.m=m;helper.OUT=OUT;helper.PUBLIC=PUBLIC;helper.ART=ART
put=d.write


def local_verified():
    dev=ROOT/m.DEV;v=d.read(dev/'verification.json')
    for field in ('source_bindings','evidence_bindings','dependency_bindings'):
        m.need(d.bindings(set(v[field]))==v[field], 'new original '+field)
    unit=(dev/'unit.stderr.txt').read_bytes()
    m.need(v['unit_tests']==86 and unit.count(b' ... ok\n')==86 and b'\nOK\n' in unit and
           b'FAILED' not in unit and not (dev/'unit.stdout.txt').read_bytes(), '86 successful new-test originals')
    for name,cold in (('progress',False),('continue',True)):
        m.command_trace((dev/('continue-commands.txt' if cold else 'commands.txt')).read_text(),
                        (dev/(name+'.stdout.txt')).read_bytes(),cold)
    result=m.verify((dev/'progress.stdout.txt').read_bytes(),(dev/'continue.stdout.txt').read_bytes(),
                    d.read(ROOT/m.PARENT),v['output_save'])
    m.need(result==v['result'] and v['status']=='PASS_LOCAL_NATIVE_LV7_SAVE_NOT_ACTIONS_TERMINAL',
           'complete positive new interval')
    return v


def append_logs(summary,verify,version,status):
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 通常Lv7習得・回復不成立・保存継続\n- Version: {version}\n- Status: {status}\n- Summary: {summary}\n- Files changed: 専用oracle/86検査/入力原本/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/save/runner/画面は非tracked artifactのみ。\n- Verify: {verify}\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branchへ非force push。\n- Network: 固定GitHub HEAD/Actions/artifact/APIのみ。一般CI action_required・失敗は別記録。全体private guard成功、merge、release、active baseline変更を主張しない。\n'
    for name in d.LOGS:
        with (ROOT/name).open('a') as f:f.write(entry)


def own(paths):put(OUT/'owned.json',sorted(paths))


def checkpoint_source(names,installer):
    """展開された新UTF8 textだけを保存。native/unit/compile再実行0。"""
    d.current();state=helper.source_check();v=local_verified()
    goal='開発原本の194入力/56画面/通常Lv7/習得Saveは完走済み。86新検査は初回全成功。次はこの新区間だけのActions独立測定とtraining.srm artifact保持。正式runが既に存在したら原本回収のみ。'+GOAL
    state['research_story_training_development']=dict(path=m.DEV+'/verification.json',status=v['status'],
        local_native_processes=2,new_unit_tests=86,actions_completion_confirmed=False,natural_research_arrival_accepted=False)
    state['bp']['current_stop']='STORY_TRAINING_DEVELOPED_ACTIONS_NEXT';state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='STORY_TRAINING_INDEPENDENT_MEASUREMENT_NEXT',goal_ja=goal,
        read_paths=[GUIDE,m.DEV+'/verification.json',SELF,m.SOURCE,m.PARENT],
        stop_rule_ja='この194入力は開発完走済み。正式測定runがあれば回収だけにして再生しない。正式測定前に受入済みgrowth保存を復元し、新区間のみ測定する。旧受入を再実行せず、trainer勝利/研究到達へ昇格しない。')
    state['do_not_repeat'].insert(0,'自然習得開発原本 '+m.DEV+'/verification.json を保持。194入力/56画面/native2/新86検査。正式runができた後は新たな入力をtraining.srmから行い、成功した区間を再生しない。')
    for name in set(names)|{installer,SESSION,CONTEXT}:state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    append_logs(goal,'開発native2、進行194入力19042frames/cold34入力2572frames、56実画面（空白0）、4UI全byte一致。86新検査初回全PASS。source/evidence binding確認を再利用し、このinstallでnative/unit/compile再実行0。','research-story-training-source-v1','DONE（実装・新試験原本保存、正式終端は未確認）')
    own(set(names)|{d.STATE,d.DOC}|d.LOGS)
    put(OUT/'source-verification.json',dict(status='PASS_NEW_SOURCE_CHECKPOINT',source_head=os.environ['GITHUB_SHA'],
        native_processes=0,unit_test_runs=0,reused_new_unit_tests=86,accepted_case_reruns=0,result=v['result']))


def parent_input():
    parent=d.read(ROOT/m.PARENT);m.parent_boundary(parent)
    expected=parent['retained_artifact'];meta=d.inputs.api('actions/artifacts/10944976226')
    m.need(not meta['expired'] and all(meta[k]==expected[k] for k in ('id','name','size_in_bytes','digest','workflow_run')),
           'exact accepted parent artifact metadata')
    raw=d.inputs.api('actions/artifacts/10944976226/zip',True)
    m.need(m.identity(raw)==dict(size=1303767,sha256='be09450a6179b40ed1282b11a9f152d33dcb1d0863079d3bbe4b344929d0f0fa'),
           'exact accepted parent archive bytes')
    with helper.safe_zip(raw,20000000) as z:
        saved,runner=z.read('growth.srm'),z.read('runner')
        m.need(m.load(z.read('checkpoint.json'))==parent['checkpoint'] and
               m.identity(saved)==m.INPUT_SAVE and m.identity(runner)==m.RUNNER,'real parent Save and fixed runner')
    put(PUBLIC/'parent-artifact.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    return parent,saved,runner


def measure():
    os.chdir(ROOT);d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/CP).exists(),'new interval once, recover artifacts after interruption')
    state=helper.source_check();local=local_verified();PUBLIC.mkdir(parents=True);ART.mkdir()
    before=m.identity((ROOT/d.STATE).read_bytes())
    parent,saved,runner=parent_input()
    helper.old.OUT,helper.old.PUBLIC=OUT,PUBLIC
    runtime,data=helper.old.restore()  # Fixed accepted recipes, no compile/NewGame/old measure.
    candidate=data/'candidate.gba';m.need(m.identity(candidate.read_bytes())==m.CANDIDATE,'same whole candidate')
    diagnostic=m.diagnose(candidate.read_bytes(),(ROOT/m.BUILDER).read_text())
    m.need(diagnostic==d.read(ROOT/m.DEV/'diagnostic.json'),'readonly current-ROM diagnostic original')
    put(PUBLIC/'home-portal-diagnostic.json',diagnostic)
    executable=OUT/'runner';executable.write_bytes(runner);executable.chmod(0o755)
    dev=ROOT/m.DEV
    raw,working,where=helper.invoke(runtime,candidate,executable,'progress',saved,(dev/'commands.txt').read_bytes())
    shutil.copy2(working,ART/'training.srm')
    m.need(raw==(dev/'progress.stdout.txt').read_bytes() and m.identity(working.read_bytes())==m.OUTPUT_SAVE,
           'complete new native input/state/screens/Save agree with original')
    cold,cold_save,cold_where=helper.invoke(runtime,candidate,executable,'continue',working.read_bytes(),
                                          (dev/'continue-commands.txt').read_bytes())
    m.need(cold==(dev/'continue.stdout.txt').read_bytes(),'complete independent Continue original')
    result=m.verify(raw,cold,parent,m.identity(working.read_bytes()),where,cold_where)
    m.need(result==local['result'] and m.identity(cold_save.read_bytes())==m.OUTPUT_SAVE and
           m.identity(candidate.read_bytes())==m.CANDIDATE and m.identity(executable.read_bytes())==m.RUNNER,
           'whole state and fixed executable retained')
    helper.source_check();m.need(m.identity((ROOT/d.STATE).read_bytes())==before,'protected resume unchanged during native')
    checkpoint=dict(schema_version=1,candidate=m.CANDIDATE,save=m.OUTPUT_SAVE,executable=m.RUNNER,
        runtime_artifact=10898620034,data_artifact=10898510128,parent_artifact=10944976226,
        source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),frame=19042,
        map=[3,0],xy=[4,27],party_count=1,rp=0,save_counter=5,level=7,experience=245,hp=[13,23],status_condition_ja='まひ',natural_learned_move_ja='すいとる',
        native_bag_potion_count=0,mode='continue-story',commands='quit\n',new_game_replay_required=False,
        completed_training_segment_replay_required=False,natural_research_arrival_accepted=False)
    put(ART/'checkpoint.json',checkpoint)
    paths=CODE|{WF}|{str(p.relative_to(ROOT)) for p in dev.iterdir() if p.is_file()}
    put(PUBLIC/'measurement.json',dict(**result,checkpoint=checkpoint,source_head=os.environ['GITHUB_SHA'],
        run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=d.bindings(paths),
        protected_resume=dict(source_head=os.environ['GITHUB_SHA'],path=d.STATE,identity=before,path_count=len(state['source_bindings'])),
        native_processes=2,fresh_cores=2,local_development_native_processes=2,host_compiles=0,arm_compiles=0,
        rom_changes=0,accepted_case_reruns=0,new_game_replays=0,new_guard_processes=0,reused_fixed_runner_barriers=7,
        reused_new_oracle_tests=86,new_unit_test_runs=0))
    print('PASS: new natural training/consumption/Save and independent Continue only')


def record():
    os.chdir(ROOT);d.current();m.need(not (ROOT/CP).exists(),'immutable new checkpoint')
    state=helper.source_check();measured=d.read(PUBLIC/'measurement.json')
    m.need(d.bindings(set(measured['source_bindings']))==measured['source_bindings'],'same measured source')
    m.need(m.identity((ROOT/d.STATE).read_bytes())==measured['protected_resume']['identity'],'exact prior resume')
    base='content/modernization/pr16_research_story_training_evidence/'+os.environ['GITHUB_RUN_ID']
    dest=ROOT/base;dest.mkdir(parents=True)
    for path in PUBLIC.iterdir():
        if path.is_file():
            raw=path.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'text evidence only')
            shutil.copy2(path,dest/path.name)
    evidence={str(p.relative_to(ROOT)) for p in dest.iterdir()}
    put(dest/'manifest.json',d.bindings(evidence));evidence.add(base+'/manifest.json')
    # Full protected bindings remain at immutable source_head:STATE; do not duplicate 2,690 entries in the resume checkpoint.
    cp=dict(local_verified()['result'],status='PASS_NATURAL_LV7_ABSORB_SAVE_PENDING_TERMINAL',
        source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),checkpoint=measured['checkpoint'],
        actions_completion_confirmed=False,manifest=base+'/manifest.json',measurement=base+'/measurement.json',
        retained_artifact_name=ARTNAME,retained_artifact_id=None,development=m.DEV+'/verification.json',
        next_input='continue-story from training.srm; do not replay completed 194 inputs')
    put(ROOT/CP,cp)
    with (ROOT/GUIDE).open('a') as f:
        f.write('\n## Actions独立測定（この時点では終端確認待ち）\n\n'+GOAL+'\n\nsource `'+os.environ['GITHUB_SHA']+'`、run `'+os.environ['GITHUB_RUN_ID']+'`。194入力/49画面とcold34入力/7画面、全stdout・全Save/RTCが開発原本と一致。正式native2/開発native2は別会計。86新検査は原本source一致で再利用し、再実行0。\n')
    state['research_story_training']=dict(path=CP,status=cp['status'],run_id=cp['run_id'],source_head=cp['source_head'],
        candidate=m.CANDIDATE,actions_completion_confirmed=False,natural_research_arrival_accepted=False,
        retained_artifact_name=ARTNAME)
    state['research_story_training_development']['superseded_by']=CP
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=GOAL
    state['next_action']=dict(state['next_action'],id='HOME_RECOVERY_OWNER_BEFORE_STORY_NEXT',goal_ja=GOAL,
        read_paths=[GUIDE,CP,m.SOURCE],stop_rule_ja='先にこの新runの全必須step/後継Save artifactを外部照合する。完走194入力を繰り返さずtraining.srmだけから進める。trainer勝利/研究到達/配布へ昇格せず、merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0,'自然習得保存の完走194入力は '+CP+'。次はtraining.srmのmap3/0(4,27)/Lv7/経験値245/HP13/23・麻痺/道具0からだけ。旧受入は再生しない。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='Lv7自然習得新区間を独立測定したsource HEAD。成功終端は外部APIで別途確認する。自己記録commit/製品最終SHAではない。'
    helper.observe_checks(state,os.environ['GITHUB_SHA'])
    for name in CODE|{WF,GUIDE,CP}|evidence:state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    append_logs(GOAL,'正式native2、194入力19042frames/cold34入力2572frames、56実画面/4UI一致、全party600bytes/Flash128KiB/ledger/位置/RP0/counter5保持。86新検査原本再利用、compile/ROM変更/旧受入再実行0。','research-story-training-measure-v1','DONE（新区間測定、終端外部照合待ち）')
    own(evidence|{GUIDE,CP,d.STATE,d.DOC}|d.LOGS)


def terminal():
    os.chdir(ROOT);d.current();state=helper.source_check();cp=d.read(ROOT/CP)
    m.need(cp['status']=='PASS_NATURAL_LV7_ABSORB_SAVE_PENDING_TERMINAL' and cp['actions_completion_confirmed'] is False and
           str(cp['run_id'])==os.environ['EXPECTED_RUN'] and cp['source_head']==os.environ['EXPECTED_SOURCE'] and
           not (ROOT/TERMINAL).exists(),'one exact pending result, no native rerun')
    OUT.mkdir(parents=True);runid=cp['run_id'];source=cp['source_head']
    run=d.inputs.api('actions/runs/'+str(runid))
    m.need(run['head_sha']==source and run['head_branch']=='codex/modernization-followup-20260908' and
           run['path']==WF and run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,
           'external dedicated run completed successfully')
    listing=d.inputs.api('actions/runs/'+str(runid)+'/jobs?per_page=100')
    m.need(listing['total_count']==len(listing['jobs'])==1,'complete single-job page')
    job=listing['jobs'][0]
    m.need(job['name']=='training-story' and job['status']=='completed' and job['conclusion']=='success' and
           [x['name'] for x in job['steps']]==EXPECTED_STEPS and
           all(x['status']=='completed' and x['conclusion']=='success' for x in job['steps']), 'all 11 required steps success')
    listing=d.inputs.api('actions/runs/'+str(runid)+'/artifacts?per_page=100')
    m.need(listing['total_count']==len(listing['artifacts'])==1,'one retained checkpoint artifact')
    meta=listing['artifacts'][0]
    m.need(meta['name']==ARTNAME and not meta['expired'] and meta['workflow_run']['id']==runid and
           meta['workflow_run']['head_sha']==source,'same-run artifact')
    raw=d.inputs.api('actions/artifacts/'+str(meta['id'])+'/zip',True);archive=m.identity(raw)
    m.need(meta['size_in_bytes']==archive['size'] and meta['digest']=='sha256:'+archive['sha256'],'whole artifact digest')
    with helper.safe_zip(raw,24000000) as z:
        saved=m.load(z.read('checkpoint.json'));m.need(saved==cp['checkpoint'],'same captured checkpoint')
        for name in ('training.srm','progress/story.srm','continue/story.srm'):
            m.need(m.identity(z.read(name))==m.OUTPUT_SAVE,'whole ordinary Save+RTC '+name)
        m.need(m.identity(z.read('runner'))==m.RUNNER,'same retained runner')
        completion=z.read('completion-head.txt').decode().strip()
        subprocess.run(['git','merge-base','--is-ancestor',completion,'HEAD'],check=True)
        m.need(d.git('rev-parse',completion+'^').decode().strip()==source,'non-force completion parent')
        for name in z.namelist():
            if name.endswith('.ppm'):
                target=OUT/'screens'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
        result=m.verify(z.read('progress.stdout.txt'),z.read('continue.stdout.txt'),d.read(ROOT/m.PARENT),m.OUTPUT_SAVE,
                        OUT/'screens/progress',OUT/'screens/continue')
        m.need(result==local_verified()['result'],'complete positive and test originals')
        m.need(m.load(z.read('home-portal-diagnostic.json'))==d.read(ROOT/m.DEV/'diagnostic.json'),'immutable readonly owner diagnosis')
        for name in ('progress.stderr.txt','continue.stderr.txt','measure.stderr.txt'):
            m.need(not z.read(name),'no native/measurement errors')
        measured=m.load(z.read('measurement.json'))
        m.need(all(measured[k]==v for k,v in result.items()) and measured['source_head']==source and
               measured['run_id']==runid and measured['checkpoint']==saved,'exact independent measurement')
        m.need(d.bindings(set(measured['source_bindings']))==measured['source_bindings'],'measured source unchanged')
        original=d.git('show',source+':'+d.STATE)
        m.need(m.identity(original)==measured['protected_resume']['identity'] and
               len(m.load(original)['source_bindings'])==measured['protected_resume']['path_count'], 'immutable protected source reference')
        bindings=d.read(ROOT/cp['manifest']);m.need(d.bindings(set(bindings))==bindings,'committed evidence binding')
        for path,binding in bindings.items():
            m.need(m.identity(z.read(PurePosixPath(path).name))==binding and
                   z.read(PurePosixPath(path).name)==(ROOT/path).read_bytes(),'artifact equals committed evidence '+path)
        with helper.safe_zip(z.read('record.zip'),12000000) as record:
            m.need(record.read('record-head.txt').decode().strip()==completion,'completion text snapshot HEAD')
            snapshot_count=len(record.namelist())-1
            for name in record.namelist():
                if name=='record-head.txt':continue
                value=record.read(name);value.decode('utf-8')
                m.need(b'\0' not in value and value==d.git('show',completion+':'+name) and value==(ROOT/name).read_bytes(),
                       'committed UTF8 snapshot readback '+name)
    receipt=dict(schema_version=1,task=TASK,status=result['status'],source_head=source,completion_commit=completion,
        observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),run=d.run_summary(run),
        job={k:job[k] for k in ('id','name','status','conclusion','steps')},
        artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','created_at','expires_at','expired')},
        archive=archive,verified_real_screens=56,content_screens=56,verified_snapshot_text_files=snapshot_count,
        new_native_processes=0,new_unit_test_runs=0,new_compiles=0,reused_new_oracle_tests=86,accepted_case_reruns=0,
        all_required_steps_succeeded=True,all_committed_originals_match=True,natural_research_arrival_accepted=False,
        release_ready=False,active_baseline_changed=False)
    helper.observe_checks(state,source)
    recent=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')
    receipt['latest_branch_actions']=[d.run_summary(x) for x in recent['workflow_runs']]
    receipt['complete_repository_history_claimed']=False
    put(ROOT/TERMINAL,receipt)
    cp.update(status=result['status'],actions_completion_confirmed=True,retained_artifact_id=meta['id'],
              retained_artifact=receipt['artifact'],terminal_receipt=TERMINAL)
    put(ROOT/CP,cp)
    with (ROOT/GUIDE).open('a') as f:
        f.write(f'\n## 外部確認した成功終端\n\nrun `{runid}` / job `{job["id"]}` の全11必須stepがcompleted/success。完了commit `{completion}`。artifact `{meta["id"]}` は {archive["size"]} bytes / SHA-256 `{archive["sha256"]}`。56実画面、4組の同一UI、3コピーのSave/RTC、固定runner、全commit text原本を照合。上の確認待ちは測定時点の履歴で、現在は終端確認済み。原本は `{TERMINAL}`。終端処理のnative/compile/unit再実行0。\n\n次は `training.srm` を作業コピーにして固定candidate/runtime/runnerでContinueする。map3/0 (4,27)、party1/Lv7/HP13/23/EXP245・麻痺、RP0、counter5、すいとる25/25、キズぐすり0。194入力を再生しない。トレーナー戦は今回0・過去2名には未勝利であり、研究施設への自然到達も未完。\n')
    state['research_story_training'].update(status=result['status'],actions_completion_confirmed=True,
        retained_artifact_id=meta['id'],terminal_receipt=TERMINAL)
    state['bp']['current_stop']=result['status'];state['bp']['next_step']=GOAL
    state['next_action'].update(id='HOME_RECOVERY_OWNER_BEFORE_STORY_NEXT',goal_ja=GOAL,
        read_paths=[GUIDE,CP,TERMINAL,m.SOURCE],
        stop_rule_ja=f'run{runid}の全11必須stepとartifact{meta["id"]}は確認済み。training.srmのsize/SHAと固定candidate/runtime/runnerを確認してContinue。map3/0(4,27)/Lv7/EXP245/HP13/23・麻痺/counter5/すいとる25/25/道具0から先だけを進め、成功194入力と旧受入を再実行しない。trainer勝利/研究到達/配布へ昇格しない。merge/release/baseline変更禁止。')
    state['observed_head']=source
    state['observed_head_semantics']='Lv7自然習得新区間を独立測定したsource HEAD。全11必須step・後継Save/RTC・56画面・commit原本を '+TERMINAL+' で外部確認。自己記録commitや製品最終SHAではない。'
    state['pending_runs']=[x for x in state['pending_runs'] if x['run_id']!=runid]
    for name in (CP,GUIDE,TERMINAL,TERMINAL_WF):state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    append_logs(GOAL,f'run{runid}/job{job["id"]}全11step成功、artifact{meta["id"]}全ZIP/3Save/runner/56画面/{snapshot_count}text読戻しPASS。新86検査原本再利用、終端native/unit/compile再実行0。一般CIと全体private guardは別境界。','research-story-training-terminal-v1','DONE（新区間限定、通常研究施設到達は未完）')
    own({CP,GUIDE,TERMINAL,d.STATE,d.DOC}|d.LOGS)
    put(OUT/'terminal-verification.json',dict(status=result['status'],verified_source_head=source,
        verified_completion_commit=completion,run_id=runid,artifact=meta['id'],archive=archive,
        terminal_source_head=os.environ['GITHUB_SHA'],native_processes=0,unit_test_runs=0,compiles=0))
    print('PASS: external terminal and retained training Save, no replay')


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    d.current();pr16_resume.validate(ROOT)
    owned=set(d.read(OUT/'owned.json'))
    before=m.load(d.git('show',os.environ['GITHUB_SHA']+':'+d.STATE))['source_bindings']
    m.need(d.bindings(set(before)-owned)=={p:v for p,v in before.items() if p not in owned},'all unrelated accepted originals unchanged')
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    operations=dict(measure=measure,record=record,terminal=terminal,guard=guard,
                    snapshot=helper.snapshot,preserve=helper.preserve,
                    paths=lambda:print('\n'.join(d.read(OUT/'owned.json'))))
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('measure|record|terminal|guard|snapshot|preserve|paths')
    operations[sys.argv[1]]()
