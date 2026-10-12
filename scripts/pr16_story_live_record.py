#!/usr/bin/env python3
"""新live observerの原本を独立照合し固定再開/ログへ記録。native再走0。"""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as p
import pr16_story_live_observer as m
from pr16_story_after_maori import need,identity,write
from pr16_learnset_compact_record import publish_resume
SOURCE='7f879dd653b5833d4c5050f22b96ab4bd8c15685'
RUN,JOB,ARTIFACT=37203041912,111438456742,11303576858
SPEC=(ARTIFACT,RUN,19436,'e57ad91c7906bd0f3c81fd517e46a7fe48b410b81e150e012b9f9e45029a1303')
BASE=SOURCE;TASK='USER-20261004-STORY-LIVE'
OUT=ROOT/'.local/pr16-story-live-record';EVIDENCE='content/modernization/pr16_story_live_observer_evidence'
CP='content/modernization/pr16_story_live_observer_checkpoint.json';GUIDE='docs/PR16_STORY_LIVE_OBSERVER_ACCEPTANCE_JA.md'
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
LOGS={'design/run_log.md','design/version_log.md'}
NEXT='content/modernization/pr16_story_shiou_route_candidate.json'
CODE={'scripts/pr16_story_live_record.py','.github/workflows/pr16-story-live-record.yml',NEXT}

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def current():
    q=p.api('pulls/16');need(q['state']=='open' and q['draft'] and not q['merged'] and q['head']['sha']==os.environ['GITHUB_SHA'] and q['head']['ref']=='codex/modernization-followup-20260908','current sole draft branch')
def bindings(paths):return {x:identity((ROOT/x).read_bytes()) for x in sorted(paths)}
def terminal(run,source,job,count,conclusion):
    r=p.api('actions/runs/'+str(run));j=p.api('actions/jobs/'+str(job))
    need(r['head_sha']==source and r['status']=='completed' and r['conclusion']==conclusion and r['run_attempt']==1,'exact run terminal')
    need(j['run_id']==run and j['status']=='completed' and j['conclusion']==conclusion and len(j['steps'])==count,'exact job terminal')
    if conclusion=='success':need(all(x['conclusion']=='success' and x['status']=='completed' for x in j['steps']),'all required steps passed')
    return dict(run=r,job=j)

def verify_trace(folder,seed):
    rows=[json.loads(x) for x in(folder/'stdout.txt').read_text().splitlines()]
    begin=rows[0];need(begin==dict(begin='INDEPENDENT_CONTINUE',candidate_sha256=m.CANDIDATE,initial_save_sha256=p.SEED['sha256'],host_write_barriers=7),'fixed Continue only')
    inputs=[];obs=[];live=[];screens=[];frames=0;pending=None
    for row in rows[1:-1]:
        if 'input' in row:
            need(pending is None and row['input']==len(inputs) and row['frame']==frames,'input order');inputs.append((row['key'],row['frames']));frames+=row['frames']
        elif 'observe' in row:
            need(pending is None and row['observe']==len(obs) and row['frame']==frames,'observation order');obs.append(row);pending='live'
        elif 'live' in row:
            need(pending=='live','unique immediate live row');live.append(m.parse(row,obs[-1]));pending='screen'
        elif 'screen' in row:
            need(pending=='screen' and row['screen']==len(screens) and row['frame']==frames,'unique immediate screen');raw=(folder/f"screen-{row['screen']:04d}.ppm").read_bytes()
            need(identity(raw)['sha256']==row['sha256'] and len(raw)==115215 and raw.startswith(b'P6\n240 160\n255\n'),'complete rendered screen');screens.append(row);pending=None
        else:raise ValueError('unknown trace record')
    need(inputs==[(0,600),(8,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(0,180),(0,120)],'boot12 then no-input120 only')
    need(pending is None and len(obs)==len(live)==len(screens)==2 and frames==1510,'two same-frame observations')
    expected=dict(end='STORY_INPUT_CHECKPOINT',frames=1510,inputs=13,warnings_errors=0,host_write_barriers=7,guarded_host_writes=0,fixture_calls=0,natural_research_arrival_accepted=False)
    need(rows[-1]==expected and not(folder/'stderr.txt').read_bytes(),'clean exact native end')
    need((folder/'commands.txt').read_text()=='key 0 120\nobserve 1\nquit\n','no progression or save command')
    a,b=[p.validate_probe(seed,x) for x in live]
    need(obs[0]['party_sha256']==obs[1]['party_sha256'] and obs[0]['flash_sha256']==obs[1]['flash_sha256'],'party/flash preserved')
    differences={key:[[i,u,v] for i,(u,v) in enumerate(zip(live[0][key],live[1][key])) if u!=v] for key in m.SIZES}
    need(differences['save2']==[[17,16,18]] and differences['objects']==[[240,17,34],[248,1,2]],'observed clock and object bytes, not broad effect permission')
    need(all(not v for k,v in differences.items() if k not in ('save2','objects')),'all other read areas unchanged')
    execution=json.loads((folder/'execution.json').read_bytes());need(execution['initial_save']==execution['final_save']==p.SEED and execution['native_end']==expected and execution['returncode']==0 and execution['observations']==2,'physical Save101 remains original')
    return dict(status='PASS_READ_ONLY_LIVE_OBSERVER_SAVE101_ONLY',observations=2,screens=2,inputs=13,frames=1510,first=a,second=b,wait_byte_differences=differences,
                physical_checksums=14,record_native_processes=0,record_compiles=0,ordinary_saves=0,field_inputs=0,native_postbattle_adapter_accepted=False,native_battle_continuation_accepted=False,milestone_reached=False,full_story_accepted=False,release_ready=False)

def record():
    current();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists() and not(ROOT/CP).exists(),'one original-only record');OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    state=json.loads((ROOT/STATE).read_bytes());protected=bindings(set(state['source_bindings']))
    need(protected==state['source_bindings'],'old accepted sources unchanged')
    for name in p.CODE:need(git('show',SOURCE+':'+name)==(ROOT/name).read_bytes(),'measurement exact source '+name)
    done=terminal(RUN,SOURCE,JOB,8,'success');failure=terminal(37202842013,'df68c243ee8799e2cc3e5ddc70b6bf7aec66b8e4',111437881608,7,'failure')
    fz,_=p.archive((11303995788,37202842013,537,'338f8bd99043dd39b808f5aa5cc57a9b2a606da4a71074b56b4fd8dcc2bd2a23'))
    with fz:failure_detail=json.loads(fz.read('failure.json'))
    need(failure_detail['native_processes']==0 and failure_detail['type']=='HTTPError' and failure_detail['message']=='HTTP Error 404: Not Found','pre-native 404 original')
    original=OUT/'original';original.mkdir();z,meta=p.archive(SPEC)
    with z:
        mf=json.loads(z.read('manifest.json'));need(len(mf)==10 and set(z.namelist())==set(mf)|{'manifest.json'},'all ten original members')
        for name,b in mf.items():
            raw=z.read(name);need(identity(raw)==b,'original member '+name);dest=original/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    z,_=p.archive(p.SAVE101)
    with z:seed=z.read('story-fast.srm')
    result=verify_trace(original/'probe',seed)
    measured=json.loads((original/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['status']==result['status'] and measured['native_processes']==1 and measured['new_host_compiles']==1 and measured['host_tests_reused']==49,'scoped measurement accounting')
    unit=json.loads((ROOT/'content/modernization/pr16_story_live_observer_unit.json').read_bytes());need(bindings(unit['source_bindings'])==unit['source_bindings'] and unit['tests']==unit['passed']==49 and unit['stderr'].count(' ... ok\n')==49,'unchanged 49 host tests reused')
    evidence=ROOT/EVIDENCE;evidence.mkdir()
    for f in sorted(original.rglob('*')):
        if f.is_file() and f.suffix in{'.txt','.json'}:
            dest=evidence/f.relative_to(original);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes())
    write(evidence/'verification.json',result);write(evidence/'measurement-terminal.json',done);write(evidence/'pre-native-failure-terminal.json',failure);write(evidence/'pre-native-failure.json',failure_detail)
    visual=dict(scope='two current Save101 field screens',reviewed_screens=[0,1],all_screens_reviewed=True,player_at_route506_east_road=True,expected_clear_field=True,no_battle_or_heal_or_save_claim=True)
    write(evidence/'visual-review.json',visual)
    paths={f.relative_to(ROOT).as_posix() for f in evidence.rglob('*') if f.is_file()}
    cp=dict(schema_version=1,task=TASK,status=result['status'],measurement_source=SOURCE,run_id=RUN,job_id=JOB,
            artifact={k:meta[k] for k in('id','size_in_bytes','digest','workflow_run','expires_at')},verification=result,
            compiled_runner=json.loads((original/'compile.json').read_bytes()),source_bindings=bindings(p.CODE|CODE),evidence_bindings=bindings(paths),
            host_tests=49,successful_native_processes=1,pre_native_failed_processes=0,pre_native_failed_runs=[37202842013],record_native_processes=0,
            next_route_candidate=NEXT,native_postbattle_adapter_accepted=False,native_battle_continuation_accepted=False,release_ready=False)
    write(ROOT/CP,cp)
    with(ROOT/GUIDE).open('a')as f:f.write(f'# native読取の限定受入\n\nsource `{SOURCE}`、run `{RUN}` / job `{JOB}` の全8step成功。artifact `{ARTIFACT}`、19436bytes/SHA256 `{SPEC[3]}`、全10member/2実画面を独立照合。Save101のparty600bytes、legacy flags288bytes/vars256個、拡張1536bytes＋ball/coins6bytesが実RAMと一致。全Save/RTCは入力と同一。入力13は起動Continue12と無入力待機120framesだけ。通常歩行/戦闘/回復/Save0。新compile1/native1、記録native0、旧受入再走0。\n\n最初のrun37202842013は消失済み旧runtime artifact10898620034への404でcompile/native0。失敗原本を保持したまま、保存済みartifact11263910704と元と同じ公式Ubuntu `0.10.2+dfsg-1.1build3` headersへ修正。package側libmgbaと保存runtimeの全byte一致を要求した。\n\n120frames待機ではSaveBlock2のoffset17が16→18、object領域2bytesが変化した。現在の純粋戦闘adapterはSaveBlock2全byte不変を要求するので、このまま長時間戦闘に流用しない。時計ownerとNPCの観測を切り分けてから続行する。\n\n215歩の静的候補は新計画JSONへ保存。terrainはcollision0/elevation3、草14tileだが、trainer131/128/1065の視線候補と現在の物理flag、敵party/報酬/UI/回復ownerが未解決。runtime_authorized=false。診断停止をmilestone完成にしない。\n')
    old_goal=state['next_action']['goal_ja'];prefix='新read-only observerはSave101の実HP/PP/全party・進行byteをnative照合済み（run37203041912/artifact11303576858）。戦闘後/連戦nativeは未受入。SaveBlock2 offset17の時計差を全byte不変条件から分離するbounded owner検査と、215歩候補上trainer131/128/1065のowner・資源・UIを解決してから実行。'
    goal=prefix+old_goal
    state['story_live_observer']=dict(status=result['status'],checkpoint=CP,guide=GUIDE,run_id=RUN,job_id=JOB,artifact_id=ARTIFACT,verification=result,record_run_id=int(os.environ['GITHUB_RUN_ID']),next_route_candidate=NEXT,native_postbattle_adapter_accepted=False,native_battle_continuation_accepted=False)
    state['story_milestone_policy'].update(observer_adapter_pending=True,live_resource_observation_accepted=True,postbattle_adapter_pending=True,native_multi_battle_continuation_accepted=False)
    state['next_action'].update(goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md','docs/PR16_STORY_MILESTONE_CONTRACT_JA.md',NEXT,'content/modernization/pr16_story_save101_next_milestone.json','scripts/pr16_story_live_observer.py'])
    state['bp']['next_step']=goal;state['bp']['current_stop']='正式進行はSave101/506番道路53,13西のまま。新observerの実資源読取をnative確認。次シオウPokecenter。'
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['do_not_repeat'].append('run37203041912のSave101 observer probe（13入力/2画面/native1/compile1）と49host試験は原本再利用。歩行・戦闘・Saveは未実行。hash-only資源推測/全雑魚戦保存へ戻らない。')
    owned={CP,GUIDE,STATE,DOC,*LOGS}|paths
    state['source_bindings'].update(bindings((owned|p.CODE|CODE)-{STATE,DOC,*LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 実資源read-only observerと次施設の静的候補\n- Version: PR16-STORY-LIVE-OBSERVER-1\n- Status: DONE（実資源読取限定。戦闘後adapter/施設到達は未完）\n- Summary: Save101のHP277/294・PP3,9,8,2、party600bytes、legacy/expanded進行を同一frameのRAM/physical Save/画面へ接続。新runnerのContinueのみ。旧Save101は不変。\n- Files changed: live observer/session/probe/49host試験と原本、限定checkpoint/guide、215歩候補、固定resumeMD/JSON、両ログ。\n- Verify: run{RUN}/job{JOB}全8step成功、49host原本、10artifact member/2画面、compile1/native1/記録native0/旧native再走0。最初のrun37202842013は旧runtime404・compile/native0、原本保持。\n- Evidence nuance: no-input120framesでsave2[17]16→18、object2byte変化。時計と動的objectのownerを未許可story effectへ拡張しない。\n- Next: 215歩候補・草14tile、trainer131/128/1065、固定wild table、時計/friendship/報酬/戦闘UIとcounter会話を解決。通常戦ごとSaveなし。\n- Commit: measurement={SOURCE}; record source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非forcepush。\n- Network: 同repoGitHub/Actions/既存artifacts、元と同じ公式Ubuntu libmgba-dev packageのみ。ROM/runtime再配布・ROM変更・host補充・merge/release/baseline切替0。一般CI既知QOL不一致を成功へ変えない。\n'
    for name in LOGS:
        with(ROOT/name).open('a')as f:f.write(entry)
    need(bindings(protected)==protected,'all pre-existing accepted evidence unchanged')
    write(OUT/'owned.json',sorted(owned));write(receipts/'record.json',dict(status=result['status'],measurement_run=RUN,record_native_processes=0,owned=sorted(owned)))
    git('add','--',*sorted(owned))

def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for name in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+name)==(ROOT/name).read_bytes(),'all committed text '+name)
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot);need(len(sys.argv)==2 and sys.argv[1] in actions,'closed action');actions[sys.argv[1]]()
