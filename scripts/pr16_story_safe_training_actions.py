#!/usr/bin/env python3
"""Save7後継の新区間だけを測定・記録し、終端回収ではnativeを起動しない。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_safe_training as m
import pr16_research_story_route_actions as h
from pr16_learnset_compact_record import publish_resume
from pr16_home_recovery_collect import copy_immutable

d=h.d
TASK='USER-20260928-STORY-SAFE-TRAINING'
SELF='scripts/pr16_story_safe_training_actions.py'
WF='.github/workflows/pr16-story-safe-training.yml'
TWF='.github/workflows/pr16-story-safe-training-terminal.yml'
CONTEXT='.github/workflows/pr16-story-safe-training-context.yml'
CP=m.CP
DEVCP='content/modernization/pr16_story_safe_training_development_checkpoint.json'
GUIDE='docs/PR16_STORY_SAFE_TRAINING_JA.md'
OUT=ROOT/'.local/pr16-story-safe-training'
PUBLIC=OUT/'public'
ART=OUT/'checkpoint'
ARTNAME='pr16-story-safe-training-checkpoint'
CODE={SELF,WF,CONTEXT,m.SOURCE,m.TEST,m.DEV+'/commands.txt',m.DEV+'/continue-commands.txt',m.DEV+'/verification.json'}
GOAL='Save8のtraining.srm作業コピーから先だけ進める。リープンLv8/EXP331、次Lvまで88、HP24/24、PP35/30/25、手持ち1体、RP0、map4/0(8,3)。野生3勝でEXP61獲得、母親で2回回復し通常Save7→8と独立Continueを確認。ボールポケット空のため捕獲0。次は自然な用品入手/手持ち拡充または追加育成を進め、東側道路map3/19から通常ストーリーへ。マオリ勝利/研究施設自然到達/実渡航/全story/releaseは未完。完走316/cold34入力、旧Save7生成270/cold34、既受入nativeを再生しない。'
LOCAL_CODE={m.SOURCE:dict(size=13573,sha256='63623315572c36d3a871222fe919e2ef6cc97fca1172bb95bda7e491fb5800d2'),
            m.TEST:dict(size=10964,sha256='6946398f45077bca0e73a2f1833c8d8758aca1054f0e20d6fe82b9e79b821b35')}
LOCAL_UNIT=dict(size=10912,sha256='aa1490ed6800ecc1a0ab7579ed2d46e0c53a2491ea093d5d302b6fb32701413e')


def write(path,value):d.write(path,value)


def archive(number,run,size,sha):
    meta=d.inputs.api('actions/artifacts/'+str(number))
    m.need(meta['id']==number and not meta['expired'] and meta['workflow_run']['id']==run and
           meta['size_in_bytes']==size and meta['digest']=='sha256:'+sha,'fixed artifact metadata')
    raw=d.inputs.api('actions/artifacts/'+str(number)+'/zip',True)
    m.need(m.identity(raw)==dict(size=size,sha256=sha),'fixed whole archive')
    write(PUBLIC/f'artifact-{number}.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    return raw


def preserve():
    ART.mkdir(parents=True,exist_ok=True)
    for name in ('progress','continue'):
        folder=OUT/name
        if folder.exists():
            dest=ART/name;dest.mkdir(exist_ok=True)
            for p in folder.iterdir():
                if p.is_file() and p.suffix in ('.ppm','.srm'):shutil.copy2(p,dest/p.name)
    for name in ('candidate.gba','runner'):
        p=OUT/name
        if p.exists():copy_immutable(p,ART/name)
    for name in ('input.srm','training.srm','cold.srm'):
        p=OUT/'private'/name
        if p.exists():copy_immutable(p,ART/name)
    if PUBLIC.exists():
        dest=ART/'public';dest.mkdir(exist_ok=True)
        for p in PUBLIC.iterdir():
            if p.is_file():shutil.copy2(p,dest/p.name)


def invoke(runtime,name,seed,command):
    folder=OUT/name;folder.mkdir()
    working=folder/'story.srm';working.write_bytes(seed)
    (folder/'commands.txt').write_bytes(command)
    args=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(OUT/'runner'),
          str(OUT/'candidate.gba'),str(working),'continue-story',m.identity(seed)['sha256']]
    try:
        with (PUBLIC/(name+'.stdout.txt')).open('wb') as out,(PUBLIC/(name+'.stderr.txt')).open('wb') as err:
            p=subprocess.run(args,cwd=folder,input=command,stdout=out,stderr=err,timeout=300)
        raw=(PUBLIC/(name+'.stdout.txt')).read_bytes();errors=(PUBLIC/(name+'.stderr.txt')).read_bytes()
        write(PUBLIC/(name+'.execution.json'),dict(returncode=p.returncode,initial_save=m.identity(seed),
              final_save=m.identity(working.read_bytes()),stdout=m.identity(raw),stderr=m.identity(errors)))
        m.need(p.returncode==0 and not errors,'native failure: preserve without blind replay')
        return raw,working.read_bytes()
    finally:
        preserve()


def measure():
    os.chdir(ROOT);d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/CP).exists(),'one new interval only')
    state=h.source_check();parent=d.read(ROOT/m.PARENT);m.parent_boundary(parent)
    m.need(d.bindings(LOCAL_CODE)==LOCAL_CODE,'exact locally tested source, not only filenames')
    review_raw=(ROOT/m.DEV/'verification.json').read_bytes();expected=m.review(review_raw)
    PUBLIC.mkdir(parents=True);ART.mkdir();(OUT/'private').mkdir()
    source=d.bindings(CODE);protected=d.bindings(d.PROTECTED)
    write(PUBLIC/'invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
          source_bindings=source,protected_bindings=protected,accepted_case_reruns=0))
    command=(ROOT/m.DEV/'commands.txt').read_bytes();cold_command=(ROOT/m.DEV/'continue-commands.txt').read_bytes()
    for name,raw in (('commands.txt',command),('continue-commands.txt',cold_command)):
        m.commands(raw);m.need(m.identity(raw)==expected['files'][name],'fixed new commands only')
        (PUBLIC/name).write_bytes(raw)
    raw=archive(10948853813,36370422350,18792389,'11762d516aca1df0e607b1c2549c8b2be2d0c374522b762a6df325e2efc21f31')
    with h.safe_zip(raw,200000000) as z:
        for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('story.srm',m.INPUT_SAVE)):
            value=z.read(name);m.need(m.identity(value)==binding,'parent member '+name)
            target=OUT/'private/input.srm' if name=='story.srm' else OUT/name
            target.write_bytes(value);target.chmod(0o555 if name=='runner' else 0o444)
    raw=archive(10898620034,36218655601,102586759,'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d')
    runtime=OUT/'runtime';runtime.mkdir()
    with h.safe_zip(raw,300000000) as z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                target=runtime/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,
           sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed libmgba')
    seed=(OUT/'private/input.srm').read_bytes()
    first,saved=invoke(runtime,'progress',seed,command)
    (OUT/'private/training.srm').write_bytes(saved);preserve()
    m.need(m.identity(first)==expected['files']['progress.stdout.txt'] and m.identity(saved)==m.OUTPUT_SAVE,
           'all developed progress and successor bytes reproduce')
    second,continued=invoke(runtime,'continue',saved,cold_command)
    (OUT/'private/cold.srm').write_bytes(continued);preserve()
    (PUBLIC/'verification.json').write_bytes(review_raw)
    result=m.verify(first,second,command,cold_command,parent,review_raw,OUT/'progress',OUT/'continue')
    proof=m.saved_bytes(seed,saved,continued);write(PUBLIC/'save-byte-proof.json',proof)
    env=dict(os.environ,PR16_SAFE_TRAINING_EVIDENCE=str(PUBLIC),PR16_SAFE_TRAINING_PRIVATE=str(OUT/'private'),PR16_SAFE_TRAINING_SCREENS=str(OUT))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_safe_training.py','-v'],
                        cwd=ROOT,env=env,capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==93 and
           b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'93 focused positive/negative tests actually passed')
    m.need(d.bindings(CODE)==source and d.bindings(set(state['source_bindings']))==state['source_bindings'] and
           d.bindings(d.PROTECTED)==protected,'source/accepted evidence unchanged')
    for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER)):
        m.need(m.identity((OUT/name).read_bytes())==binding,'immutable input '+name)
    m.need(m.identity((OUT/'private/input.srm').read_bytes())==m.INPUT_SAVE,'original Save7 unchanged')
    write(PUBLIC/'measurement.json',dict(result=result,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
          source_bindings=source,protected_bindings=protected,focused_tests=93,new_native_processes=2,development_native_processes=2,
          development_focused_test_executions=93,development_unit_stderr=LOCAL_UNIT,development_source_bindings=LOCAL_CODE,
          accepted_case_reruns=0,host_compiles=0,arm_compiles=0,rom_changes=0,new_guard_processes=0,reused_runner_barriers=7,save_byte_proof=proof))
    preserve();print('PASS: new 316-input interval, 93 tests, two native processes, 70 screens, Save8/cold')


def checks(state,source):
    all_runs={}
    for item in state.get('pending_runs',[]):
        r=d.inputs.api('actions/runs/'+str(item['run_id']));all_runs[r['id']]=r
    heads={source,os.environ['GITHUB_SHA'],'6df52767eb86287bbad57c7bc91ae779a8c1e846',
           '5d1e34778923fda3d43e45f195367e87415ab2f1','7e3d82e8049e7ebef41d92fe49c38c09b1e02876','20b9280ff34cf0a7ec74ccdc5bc267f14b217391'}
    for head in sorted(heads):
        reply=d.inputs.api('actions/runs?head_sha='+head+'&per_page=100')
        m.need(reply['total_count']==len(reply['workflow_runs'])<=100,'complete scoped Actions list')
        for r in reply['workflow_runs']:all_runs[r['id']]=r
    summaries=[d.run_summary(all_runs[i]) for i in sorted(all_runs)]
    state['observed_head_checks']=dict(scope_head=source,runs=summaries,
        reason_ja='測定source・開始HEAD・作業checkpoint HEADと前回pendingを照合。一般CIのfailure/action_requiredをsuccessへ改作しない。自己run終端は別API回収。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in summaries if r['status'] in ('queued','in_progress')]
    write(PUBLIC/'observed-actions.json',state['observed_head_checks'])


def logs(terminal):
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    summary='通常野生3勝/EXP270→331/Lv7→8、捕獲0/トレーナー勝利0。母親2回回復、実Start→レポート確認→上書き→書込中→field復帰、Save7→8。能力4UIと全Save/RTCがcoldで一致。'
    verify='専用測定run全step・artifact ZIP・70画面原本・全Save・93検査原本・commit text照合。native/test再実行0。' if terminal else '新区間native2・316入力25208frames、cold34入力2808frames、70画面/4UI、全131088bytes、party589bytes・前回Save bank57344bytes保持、新93検査PASS。開発native2/93検査は別会計。'
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / Save7後の安全育成・Save8\n- Version: story-safe-training-v1'+('-terminal' if terminal else '')+f'\n- Status: DONE（育成区間限定。通常供給/研究施設/全story/releaseは未完）\n- Summary: {summary}\n- Files changed: 専用oracle/93検査/新入力原本/証拠/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/save/runner/画面は非tracked artifactのみ。\n- Verify: {verify} 旧受入の明示再実行0、compile/ROM改変0、task graph/resume/scoped index/diff確認後にcommit。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非force push。\n- Network: GitHub HEAD/Actions/artifactのみ。コンテナからgit cloneはDNS失敗のためconnector/専用Actionsを使用。merge/release/active baseline変更0。一般CI成功は主張しない。\n- Next: {GOAL}\n'
    for name in d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)


def publish(state,cp,owned,terminal=False):
    state['story_safe_training']=dict(path=CP,status=cp['status'],source_head=cp['source_head'],run_id=cp['run_id'],
        actions_completion_confirmed=cp['actions_completion_confirmed'],candidate=m.CANDIDATE,output_save=m.OUTPUT_SAVE,
        level=8,experience=331,trainer_victories=0,wild_victories=3,natural_research_arrival_accepted=False,retained_artifact_id=cp.get('retained_artifact_id'))
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=GOAL
    state['next_action']=dict(state['next_action'],id='STORY_SUPPLIES_AND_TRAINING_FROM_SAVE8_NEXT',goal_ja=GOAL,
        read_paths=[GUIDE,CP,m.SOURCE,m.TEST],stop_rule_ja='専用測定run/artifact終端を先に照合。後継training.srmのみ。316/cold34・親270/cold34を再生せず、失敗時も原本を保存して原因を限定。野生勝利をトレーナー勝利/研究到達へ昇格しない。')
    note='Save7後継の野生育成316入力/独立34入力は '+CP+'。Save8/EXP331/Lv8のtraining.srmから先だけ進める。捕獲0/ボールポケット空、マオリ勝利未完。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_head']=cp['source_head'];state['observed_head_semantics']='新区間を独立測定したsource HEAD。自己記録commitやactive baselineではない。'
    checks(state,cp['source_head']);state['logs_synchronized']=True
    write(ROOT/CP,cp)
    bound=owned|CODE|{CP}
    if (ROOT/TWF).exists():bound.add(TWF)
    for name in bound-{d.STATE,d.DOC}-d.LOGS:state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    publish_resume(state);logs(terminal)
    write(OUT/'guard-base.json',os.environ['GITHUB_SHA']);write(OUT/'owned.json',sorted(owned|{CP,d.STATE,d.DOC}|d.LOGS))


def record():
    os.chdir(ROOT);d.current();state=h.source_check();v=d.read(PUBLIC/'measurement.json')
    m.need(not (ROOT/CP).exists() and d.bindings(set(v['source_bindings']))==v['source_bindings'],'one immutable measured publication')
    checks(state,v['source_head'])
    base='content/modernization/pr16_story_safe_training_evidence/'+str(v['run_id'])
    dest=ROOT/base;dest.mkdir(parents=True);evidence=set()
    for p in PUBLIC.iterdir():
        if p.is_file():
            raw=p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'text evidence only')
            target=dest/p.name;target.write_bytes(raw);evidence.add(str(target.relative_to(ROOT)))
    write(dest/'manifest.json',d.bindings(evidence));evidence.add(base+'/manifest.json')
    cp=dict(v['result'],schema_version=1,source_head=v['source_head'],run_id=v['run_id'],source_bindings=v['source_bindings'],focused_tests=93,
        development_native_processes=2,development_focused_test_executions=93,actions_completion_confirmed=False,
        retained_artifact_name=ARTNAME,retained_artifact_id=None,parent_checkpoint=m.PARENT,parent_artifact=10948853813,runtime_artifact=10898620034,
        map=[4,0],xy=[8,3],rp=0,party_count=1,mode='continue-story',commands='quit\n',new_game_replay_required=False,
        evidence_manifest=base+'/manifest.json',accepted_case_reruns=0,host_compiles=0,arm_compiles=0,rom_changes=0,
        next_input='continue-story from training.srm; do not replay completed 316/cold34 input segment')
    cp['status']='PASS_STORY_SAFE_TRAINING_SAVE8_PENDING_TERMINAL';write(ART/'checkpoint.json',cp)
    guide='# PR16 Save7後の通常育成・実キーSave8\n\n'+GOAL+'\n\n## 実測した区切り\n\n低戦力でマオリへ再突入せず、道路の野生ヤヤコマLv2/スバメLv3/スバメLv4を倒して7+21+33=61EXP獲得。HP10/23の時点とLv8への上昇後に帰宅し、母親の通常回復を2回受けた。捕獲用ボールのポケットは空で、捕獲も手持ち追加も0。これを用品供給完了とはしない。\n\n## 保存と保持\n\n通常キーだけでStart→レポート→確認→上書き→書込中→field復帰、counter7→8。保存完了文言そのものの画面は未採取だが、書込中/前後Flash/14section counterと署名/前回bank保持、独立Continueの全Save/RTC131088bytesを照合。party600bytes中の成長関連11bytesだけ変化し、残り589bytes/個体識別/技/空partyを保持。前回Save7 bank全57344bytesを保持。\n\n## 表示とtelemetryの境界\n\nLv8の能力/情報/技/手持ち4UIはcoldと全byte一致。EXP331、次Lvまで88、HP24/24、PP35/30/25。レベル上昇中の特攻15と回復後summary16を同じ表示と偽らず、原本のまま残す。戦闘後のfield=false/flags4/outcome1は旧telemetryのまま保持し、callback/lock/実画面/保存/cold flags0を併用。町の初期研究室map4/3へ一度入退室しただけで研究活動施設への自然到達とはしない。\n\n## 再実行禁止と証拠\n\n新規316入力/25208framesと独立34入力/2808frames、全70画面、34目視anchor、93検査PASS。開発native2/検査93と正式native2/検査93を分離。ROM/runner/既受入source不変、compile/fixture/明示した旧native再実行0。Save7生成270/cold34や本区間を再生せず、後継training.srmからのみ続ける。ROM/save/runner/画面は非tracked artifactのみ。\n\n正式source `'+v['source_head']+'`、run `'+str(v['run_id'])+'`。終端は別のAPI回収で確認する。\n'
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    write(ROOT/DEVCP,dict(schema_version=1,status='FORMAL_MEASUREMENT_COMPLETE_TERMINAL_PENDING',superseded_by=CP,
        development_base_head='7e3d82e8049e7ebef41d92fe49c38c09b1e02876',source_bindings=LOCAL_CODE,
        development_native_processes=2,development_focused_tests=93,development_unit_stderr=LOCAL_UNIT,
        formal_run_id=v['run_id'],formal_source_head=v['source_head'],result=v['result'],save_byte_proof=v['save_byte_proof'],notes_ja=GOAL))
    publish(state,cp,evidence|{GUIDE,DEVCP})


def terminal():
    os.chdir(ROOT);d.current();state=h.source_check();cp=d.read(ROOT/CP)
    m.need(cp['actions_completion_confirmed'] is False,'terminal collection only once')
    PUBLIC.mkdir(parents=True);ART.mkdir()
    run=d.inputs.api('actions/runs/'+str(cp['run_id']))
    m.need(run['head_sha']==cp['source_head'] and run['path']==WF and run['status']=='completed' and
           run['conclusion']=='success' and run['run_attempt']==1,'successful measured run terminal')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=100')
    m.need(reply['total_count']==len(reply['jobs'])==1,'one required job');job=reply['jobs'][0]
    m.need(job['name']=='training' and job['status']=='completed' and job['conclusion']=='success' and len(job['steps'])>=10 and
           all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'all steps including upload/post are successful')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/artifacts?per_page=100')
    m.need(reply['total_count']==len(reply['artifacts'])==1,'one complete retained artifact');meta=reply['artifacts'][0]
    m.need(meta['name']==ARTNAME and not meta['expired'] and meta['workflow_run']['head_sha']==cp['source_head'],'retained artifact source')
    raw=archive(meta['id'],cp['run_id'],meta['size_in_bytes'],meta['digest'].removeprefix('sha256:'))
    expected=m.review((ROOT/m.DEV/'verification.json').read_bytes())
    with h.safe_zip(raw,200000000) as z:
        completion=z.read('completion-head.txt').decode().strip()
        m.need(len(completion)==40 and all(c in '0123456789abcdef' for c in completion),'completion commit')
        subprocess.run(['git','merge-base','--is-ancestor',completion,'HEAD'],check=True)
        m.need(d.read(ROOT/CP)==m.load(z.read('checkpoint.json')),'immutable measured checkpoint in ZIP')
        m.need(m.identity(z.read('candidate.gba'))==m.CANDIDATE and m.identity(z.read('runner'))==m.RUNNER,'same candidate/runner')
        proof=m.saved_bytes(z.read('input.srm'),z.read('training.srm'),z.read('cold.srm'))
        for name,binding in expected['files'].items():m.need(m.identity(z.read('public/'+name))==binding,'retained native original '+name)
        for name,command,seed in (('progress','commands.txt',m.INPUT_SAVE),('continue','continue-commands.txt',m.OUTPUT_SAVE)):
            parsed=m.trace(z.read('public/'+name+'.stdout.txt'),z.read('public/'+command),seed)
            for s in parsed['screens']:m.screen_bytes(z.read(name+f'/screen-{s["screen"]:04d}.ppm'),s)
        unit=z.read('public/unit.stderr.txt')
        m.need(unit.count(b' ... ok\n')==93 and b'\nOK\n' in unit and not z.read('public/unit.stdout.txt'),'retained 93 actual test originals')
        with h.safe_zip(z.read('record.zip'),100000000) as recorded:
            for name in recorded.namelist():m.need(d.git('show',completion+':'+name)==recorded.read(name),'committed text readback '+name)
    receipt=dict(source_head=cp['source_head'],run_id=cp['run_id'],completion_head=completion,run=d.run_summary(run),
        job={k:job[k] for k in ('id','name','status','conclusion','steps')},
        artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        save_byte_proof=proof,new_native_processes=0,new_test_executions=0)
    name='content/modernization/pr16_story_safe_training_terminal.json';write(ROOT/name,receipt)
    cp.update(status='PASS_STORY_SAFE_TRAINING_SAVE8_SCOPED',actions_completion_confirmed=True,
        retained_artifact_id=meta['id'],retained_artifact=receipt['artifact'],completion_head=completion,terminal_receipt=name)
    with (ROOT/GUIDE).open('a',encoding='utf-8') as f:f.write('\n## Actions終端確認済み\n\n全'+str(len(job['steps']))+'step成功。artifact `'+str(meta['id'])+'`、completion `'+completion+'`。全70画面/保存原本/93検査原本/commit textを照合。native/test再実行0。次は後継training.srmからのみ。\n')
    dev=d.read(ROOT/DEVCP);dev.update(status='FORMAL_TERMINAL_CONFIRMED',retained_artifact_id=meta['id'],actions_completion_confirmed=True);write(ROOT/DEVCP,dev)
    write(ART/'terminal.json',receipt);publish(state,cp,{name,GUIDE,DEVCP},True)


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    paths=d.read(OUT/'owned.json');subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    pr16_resume.validate(ROOT)
    g.START=d.read(OUT/'guard-base.json');g.CODE=set();g.OWNED=set(paths);g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


def snapshot():
    ART.mkdir(parents=True,exist_ok=True);paths=d.read(OUT/'owned.json')
    with zipfile.ZipFile(ART/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in paths:
            raw=d.git('show','HEAD:'+name);m.need(raw==(ROOT/name).read_bytes(),'committed readback')
            raw.decode('utf-8');m.need(b'\0' not in raw,'text only snapshot');z.writestr(name,raw)
    (ART/'completion-head.txt').write_bytes(d.git('rev-parse','HEAD'));preserve()


if __name__=='__main__':
    operations=dict(measure=measure,record=record,terminal=terminal,guard=guard,snapshot=snapshot,preserve=preserve)
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('measure|record|terminal|guard|snapshot|preserve')
    operations[sys.argv[1]]()
