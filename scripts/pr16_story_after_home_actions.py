#!/usr/bin/env python3
"""回復後の新入力だけを独立測定し、再実行せず終端を回収する。"""
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
import pr16_story_after_home as m
import pr16_research_story_route_actions as h
from pr16_learnset_compact_record import publish_resume
from pr16_home_recovery_collect import copy_immutable

d=h.d
TASK='USER-20260928-STORY-AFTER-HOME'
SELF='scripts/pr16_story_after_home_actions.py'
WF='.github/workflows/pr16-story-after-home.yml'
TWF='.github/workflows/pr16-story-after-home-terminal.yml'
CP='content/modernization/pr16_story_after_home_checkpoint.json'
DEVCP='content/modernization/pr16_story_after_home_development_checkpoint.json'
GUIDE='docs/PR16_STORY_AFTER_HOME_JA.md'
OUT=ROOT/'.local/pr16-story-after-home'
PUBLIC=OUT/'public'
ART=OUT/'checkpoint'
ARTNAME='pr16-story-after-home-checkpoint'
CODE={SELF,WF,m.SOURCE,m.TEST,m.DEV+'/commands.txt',m.DEV+'/continue-commands.txt'}
GOAL='Save7のstory.srm作業コピーから通常育成/手持ち拡充を進める。Lv7/EXP270、次Lvまで44EXP、HP23/23、技PP35/30/25、RP0、map4/0(8,5)。マオリ戦は敗北であり勝利0。同じ低戦力戦闘や完走270/cold34入力を無策に再生しない。北の伐採木で止まる経路を再探索せず、育成後は東側道路map3/19から自然ストーリー進行。研究施設自然到達/実渡航/全story/releaseは未完。'


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
    for name in ('recovery.srm','story.srm','cold.srm'):
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
    PUBLIC.mkdir(parents=True);ART.mkdir();(OUT/'private').mkdir()
    source=d.bindings(CODE)
    command=(ROOT/m.DEV/'commands.txt').read_bytes();cold_command=(ROOT/m.DEV/'continue-commands.txt').read_bytes()
    for name,raw in (('commands.txt',command),('continue-commands.txt',cold_command)):
        m.commands(raw);m.need(m.identity(raw)==m.ORIGINALS[name],'fixed new commands only')
    raw=archive(10947623338,36366801337,18389139,'fb3edef0cbb5dfdd8f388528c89d4d331da5e1eb03d877772b9087be05d807f6')
    with h.safe_zip(raw,180000000) as z:
        for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('recovery.srm',m.INPUT_SAVE)):
            value=z.read(name);m.need(m.identity(value)==binding,'parent member '+name)
            target=OUT/'private'/name if name.endswith('.srm') else OUT/name
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
    seed=(OUT/'private/recovery.srm').read_bytes()
    first,saved=invoke(runtime,'progress',seed,command)
    (OUT/'private/story.srm').write_bytes(saved);preserve()
    m.need(m.identity(first)==m.ORIGINALS['progress.stdout.txt'] and m.identity(saved)==m.OUTPUT_SAVE,
           'all developed progress and successor bytes reproduce')
    second,continued=invoke(runtime,'continue',saved,cold_command)
    (OUT/'private/cold.srm').write_bytes(continued);preserve()
    expected=m.expectations(first);write(PUBLIC/'expectations.json',expected)
    result=m.verify(first,second,command,cold_command,parent,expected,OUT/'progress',OUT/'continue')
    save_proof=m.saved_bytes(seed,saved,continued);write(PUBLIC/'save-byte-proof.json',save_proof)
    env=dict(os.environ,PR16_AFTER_HOME_EVIDENCE=str(PUBLIC),PR16_AFTER_HOME_PRIVATE=str(OUT/'private'))
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_after_home.py','-v'],
                        cwd=ROOT,env=env,capture_output=True,timeout=120)
    (PUBLIC/'unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==53 and
           b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'53 focused positive/negative tests actually passed')
    m.need(d.bindings(CODE)==source and d.bindings(set(state['source_bindings']))==state['source_bindings'],'source/accepted evidence unchanged')
    for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER)):
        m.need(m.identity((OUT/name).read_bytes())==binding,'immutable input '+name)
    m.need(m.identity((OUT/'private/recovery.srm').read_bytes())==m.INPUT_SAVE,'original Save unchanged')
    write(PUBLIC/'measurement.json',dict(result=result,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
          source_bindings=source,focused_tests=53,new_native_processes=2,development_native_processes=2,
          development_focused_test_executions=106,accepted_case_reruns=0,host_compiles=0,arm_compiles=0,rom_changes=0,
          new_guard_processes=0,reused_runner_barriers=7,save_byte_proof=save_proof))
    preserve();print('PASS: new interval only; 53 tests, two native processes, 110 screens, Save7/cold')


def checks(state,source):
    all_runs={}
    for item in state.get('pending_runs',[]):
        r=d.inputs.api('actions/runs/'+str(item['run_id']));all_runs[r['id']]=r
    for head in {source,'fce761581640b1d4361237838c661ca33e4b9b4a','a2b68477b144a529a48b4ad646ca26724d20aa1a'}:
        reply=d.inputs.api('actions/runs?head_sha='+head+'&per_page=100')
        m.need(reply['total_count']==len(reply['workflow_runs'])<=100,'complete scoped Actions list')
        for r in reply['workflow_runs']:all_runs[r['id']]=r
    summaries=[d.run_summary(all_runs[i]) for i in sorted(all_runs)]
    state['observed_head_checks']=dict(scope_head=source,runs=summaries,
        reason_ja='測定source・開始HEAD・context取得HEADと前回pendingを再照合。一般CI action_required/failureを成功へ改作しない。記録中の自己runの完了は外部APIで確認。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in summaries if r['status'] in ('queued','in_progress')]
    write(PUBLIC/'observed-actions.json',state['observed_head_checks'])


def logs(summary,terminal=False):
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 回復後の通常進行・実キーSave7\n- Version: story-after-home-v1'+('-terminal' if terminal else '')+f'\n- Status: DONE（新区間限定、トレーナー勝利/研究到達未完）\n- Summary: {summary}\n- Files changed: 専用oracle/53検査/新入力原本/証拠/checkpoint/guide、固定引継ぎMD/JSON、両ログ。ROM/save/runner/画面は非tracked artifactだけ。\n- Verify: '+('終端API/全必須step/外側ZIP/全Save/原本/commit整合。native/test再実行0。' if terminal else '新区間native2・270入力28012frames、cold34入力2852frames、110画面、4UI全byte、Save全131088bytes、party597bytes保持、53新検査PASS。開発native2・検査改良過程53件を2回(106)は別会計。')+f' 旧受入再実行0、compile/ROM変更0。task graph/resume/scoped index/diff確認後にcommit。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非force push。\n- Network: GitHub HEAD/Actions/artifactのみ。merge/release/active baseline変更0。全体CI成功とはしない。\n'
    for name in d.LOGS:
        with (ROOT/name).open('a') as f:f.write(entry)


def publish(state,cp,owned,terminal=False):
    state['story_after_home']=dict(path=CP,status=cp['status'],source_head=cp['source_head'],run_id=cp['run_id'],
          actions_completion_confirmed=cp['actions_completion_confirmed'],candidate=m.CANDIDATE,output_save=m.OUTPUT_SAVE,
          natural_research_arrival_accepted=False,trainer_victories=0,retained_artifact_id=cp.get('retained_artifact_id'))
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=GOAL
    state['next_action']=dict(state['next_action'],id='STORY_SAFE_TRAINING_FROM_SAVE7_NEXT',goal_ja=GOAL,
          read_paths=[GUIDE,CP,m.SOURCE,m.TEST],
          stop_rule_ja='先に専用測定run/artifactの終端を照合。新story.srmだけから再開。敗北を勝利へ、帰宅を研究到達へ昇格しない。旧受入と270/cold34入力を再生しない。')
    note='回復後の270入力/独立34入力は '+CP+' に保存。Save7/EXP270から先だけ進む。マオリ敗北/全滅帰宅を勝利扱いせず、育成不足を補う。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_head']=cp['source_head']
    state['observed_head_semantics']='新区間を独立測定したsource HEAD。記録用自己commitやactive baselineのSHAではない。'
    checks(state,cp['source_head']);state['logs_synchronized']=True
    write(ROOT/CP,cp)
    bound=owned|CODE|{CP}
    if (ROOT/TWF).exists():bound.add(TWF)
    for name in bound-{d.STATE,d.DOC}-d.LOGS:
        state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    publish_resume(state);logs(GOAL,terminal)
    write(OUT/'guard-base.json',os.environ['GITHUB_SHA'])
    write(OUT/'owned.json',sorted(owned|{CP,d.STATE,d.DOC}|d.LOGS))


def record():
    os.chdir(ROOT);d.current();state=h.source_check();v=d.read(PUBLIC/'measurement.json')
    m.need(not (ROOT/CP).exists() and d.bindings(set(v['source_bindings']))==v['source_bindings'],'one immutable measured publication')
    checks(state,v['source_head'])
    base='content/modernization/pr16_story_after_home_evidence/'+str(v['run_id'])
    dest=ROOT/base;dest.mkdir(parents=True)
    evidence=set()
    for p in PUBLIC.iterdir():
        if p.is_file():
            raw=p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'text evidence only')
            target=dest/p.name;target.write_bytes(raw);evidence.add(str(target.relative_to(ROOT)))
    write(dest/'manifest.json',d.bindings(evidence));evidence.add(base+'/manifest.json')
    cp=dict(v['result'],schema_version=1,source_head=v['source_head'],run_id=v['run_id'],source_bindings=v['source_bindings'],focused_tests=53,
       development_native_processes=2,actions_completion_confirmed=False,retained_artifact_name=ARTNAME,retained_artifact_id=None,
       parent_checkpoint=m.PARENT,parent_artifact=10947623338,runtime_artifact=10898620034,
       map=[4,0],xy=[8,5],rp=0,party_count=1,mode='continue-story',commands='quit\n',
       new_game_replay_required=False,completed_segment_replay_required=False,
       evidence_manifest=base+'/manifest.json',accepted_case_reruns=0,host_compiles=0,arm_compiles=0,rom_changes=0,
       next_input='continue-story from story.srm; do not replay 270/cold34 inputs')
    cp['status']='PASS_STORY_AFTER_HOME_LOSS_SAVE_PENDING_TERMINAL'
    write(ART/'checkpoint.json',cp)
    guide='# PR16 回復後の通常進行・実キーSave7\n\n'+GOAL+'\n\n## 実測した区切り\n\n回復済みSaveから東側道路(53,10)へ通常入力で進行。スバメLv3から逃走後、マオリのパモを倒してEXP25を獲得したがコフキムシLv8に敗北し56円を支払い、通常全滅帰宅した。新しいゲームの勝利/施設到達とはしない。通常回復後に実StartメニューからSave6→7、独立Continueで全Save/RTCと4UIが一致。EXP245→270、party600bytes中の変更はEXP2bytesとbyte41の85→86だけで他597bytes保持。\n\n## 旧telemetryを実ゲーム状態と混同しない\n\n戦闘後に旧battle_flags/outcomeが12/2で残り、field=falseとなる。原本/driverを改変せず、callback2とlock、実メニュー→レポート→確認→上書き→保存完了画面、counterとFlash、coldでのflags/outcome0を照合。補助save命令ではなく通常keyだけを使用した。観測6/30の黒画面は実マップ遷移/戦闘退出であり、受入anchorは空画面を拒否する。\n\n## 証拠と再実行禁止\n\n正式native2、開発native2は別会計。正式53新検査PASS。旧母親81、training194、growth367、route301、starter114入力の再生0。ROM/runner変更・compile・guard再起動0。原本の全SHAと19個の目視anchor、全110画面は固定。ROM/save/runner/画面は非tracked artifactのみ。\n\n正式source `'+v['source_head']+'`、run `'+str(v['run_id'])+'`。終端は別のAPI回収で確認する。\n'
    (ROOT/GUIDE).write_text(guide)
    dev=d.read(ROOT/DEVCP);dev['superseded_by']=CP;dev['formal_run_id']=v['run_id'];dev['status']='FORMAL_MEASUREMENT_COMPLETE_TERMINAL_PENDING';write(ROOT/DEVCP,dev)
    publish(state,cp,evidence|{GUIDE,DEVCP})


def terminal():
    os.chdir(ROOT);d.current();state=h.source_check();cp=d.read(ROOT/CP)
    m.need(cp['actions_completion_confirmed'] is False,'terminal collection only once')
    PUBLIC.mkdir(parents=True);ART.mkdir()
    run=d.inputs.api('actions/runs/'+str(cp['run_id']))
    m.need(run['head_sha']==cp['source_head'] and run['path']==WF and run['status']=='completed' and
           run['conclusion']=='success' and run['run_attempt']==1,'successful measured run terminal')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=100')
    m.need(reply['total_count']==len(reply['jobs'])==1,'one required job')
    job=reply['jobs'][0]
    m.need(job['name']=='story' and job['status']=='completed' and job['conclusion']=='success' and len(job['steps'])>=10 and
           all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'all steps including upload/post are successful')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/artifacts?per_page=100')
    m.need(reply['total_count']==len(reply['artifacts'])==1,'one complete retained artifact')
    meta=reply['artifacts'][0]
    m.need(meta['name']==ARTNAME and not meta['expired'] and meta['workflow_run']['head_sha']==cp['source_head'],'retained artifact source')
    raw=archive(meta['id'],cp['run_id'],meta['size_in_bytes'],meta['digest'].removeprefix('sha256:'))
    with h.safe_zip(raw,200000000) as z:
        completion=z.read('completion-head.txt').decode().strip()
        m.need(len(completion)==40 and all(c in '0123456789abcdef' for c in completion),'completion commit')
        subprocess.run(['git','merge-base','--is-ancestor',completion,'HEAD'],check=True)
        m.need(d.read(ROOT/CP)==m.load(z.read('checkpoint.json')),'immutable measured checkpoint in ZIP')
        m.need(m.identity(z.read('candidate.gba'))==m.CANDIDATE and m.identity(z.read('runner'))==m.RUNNER,'same candidate/runner')
        proof=m.saved_bytes(z.read('recovery.srm'),z.read('story.srm'),z.read('cold.srm'))
        for name in ('progress.stdout.txt','continue.stdout.txt'):
            m.need(m.identity(z.read('public/'+name))==m.ORIGINALS[name],'retained native original '+name)
        unit=z.read('public/unit.stderr.txt')
        m.need(unit.count(b' ... ok\n')==53 and b'\nOK\n' in unit and not z.read('public/unit.stdout.txt'),'retained 53 actual test originals')
        with h.safe_zip(z.read('record.zip'),100000000) as record_zip:
            for name in record_zip.namelist():
                m.need(d.git('show',completion+':'+name)==record_zip.read(name),'committed text readback '+name)
    receipt=dict(source_head=cp['source_head'],run_id=cp['run_id'],completion_head=completion,run=d.run_summary(run),
        job={k:job[k] for k in ('id','name','status','conclusion','steps')},
        artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        save_byte_proof=proof,new_native_processes=0,new_test_executions=0)
    name='content/modernization/pr16_story_after_home_terminal.json';write(ROOT/name,receipt)
    cp.update(status='PASS_STORY_AFTER_HOME_LOSS_SAVE_SCOPED',actions_completion_confirmed=True,
              retained_artifact_id=meta['id'],retained_artifact=receipt['artifact'],completion_head=completion,terminal_receipt=name)
    with (ROOT/GUIDE).open('a') as f:f.write('\n## Actions終端確認済み\n\n全'+str(len(job['steps']))+'step成功。artifact `'+str(meta['id'])+'`、completion `'+completion+'`。保存原本・全テスト原本・commit textを照合。native/test再実行0。次は後継story.srmからのみ。\n')
    dev=d.read(ROOT/DEVCP);dev['status']='FORMAL_TERMINAL_CONFIRMED';dev['retained_artifact_id']=meta['id'];dev['actions_completion_confirmed']=True;dev['notes_ja']=GOAL;write(ROOT/DEVCP,dev)
    write(ART/'terminal.json',receipt)
    publish(state,cp,{name,GUIDE,DEVCP},True)


def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    paths=d.read(OUT/'owned.json');subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    pr16_resume.validate(ROOT)
    g.START=d.read(OUT/'guard-base.json');g.CODE=set();g.OWNED=set(paths);g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


def snapshot():
    ART.mkdir(parents=True,exist_ok=True)
    paths=d.read(OUT/'owned.json')
    with zipfile.ZipFile(ART/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in paths:
            raw=d.git('show','HEAD:'+name);m.need(raw==(ROOT/name).read_bytes(),'committed readback')
            raw.decode('utf-8');m.need(b'\0' not in raw,'text only snapshot');z.writestr(name,raw)
    (ART/'completion-head.txt').write_bytes(d.git('rev-parse','HEAD'))
    preserve()


if __name__=='__main__':
    operations=dict(measure=measure,record=record,terminal=terminal,guard=guard,snapshot=snapshot,preserve=preserve)
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('measure|record|terminal|guard|snapshot|preserve')
    operations[sys.argv[1]]()
