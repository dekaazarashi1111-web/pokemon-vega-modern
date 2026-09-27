#!/usr/bin/env python3
"""新規starter進行だけを独立測定し、通常Saveをartifactへ保持する。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_story as m
import pr16_research_lifecycle_actions as d
TASK='USER-20260927-RESEARCH-STORY'
SELF='scripts/pr16_research_story_actions.py'
WF='.github/workflows/pr16-research-story.yml'
GUIDE='docs/PR16_RESEARCH_STORY_JA.md'
CP='content/modernization/pr16_research_story_checkpoint.json'
DEV='content/modernization/pr16_research_story_development'
OUT=ROOT/'.local/pr16-story-run'
PUBLIC=OUT/'public'
ART=OUT/'checkpoint'
OWN={'.github/workflows/pr16-research-story-context.yml','.github/workflows/pr16-research-story-install.yml','tools/mgba_pr16_research_story.c','scripts/pr16_research_story.py',SELF,'tests/test_pr16_research_story.py',WF,GUIDE,CP,d.STATE,d.DOC}|d.LOGS

def put(path,value):d.write(path,value)
def run(argv,where,stdin=None,timeout=180):
    result=subprocess.run(argv,cwd=where,input=stdin,capture_output=True,timeout=timeout)
    return result

def restore():
    d.OUT=OUT;d.PUBLIC=PUBLIC
    runtime,data,seed,parent,artifacts=d.restore()
    import pr16_research_retry as retry,pr16_research_v1_corrupt_load as v
    import pr16_research_shop_ui as patch
    def recipe(n):return d.read(ROOT/'content/modernization'/n)
    parent,_=retry.apply(parent,bytes.fromhex(recipe('pr16_research_retry_recipe.json')['after']))
    q=recipe('pr16_research_v1_corrupt_load_recipe.json');parent,_=v.apply(parent,bytes.fromhex(q['after'])[:v.CODE['size']])
    for n in ('pr16_research_map_view_recipe.json','pr16_research_counter_numeric_recipe.json','pr16_research_standard_list_ui_recipe.json'):
        q=recipe(n);m.need(m.identity(parent)==q['parent'],'recipe parent');parent=patch.edit(parent,q['patches']);m.need(m.identity(parent)==q['candidate'],'recipe whole candidate')
    candidate,recipe=patch.apply(parent);m.need(m.identity(candidate)==m.CANDIDATE,'fixed current story candidate')
    (data/'candidate.gba').write_bytes(candidate)
    put(PUBLIC/'inputs.json',dict(candidate=m.CANDIDATE,artifacts=artifacts,private_seed_used_as_native_input=False,arm_compiles=0,rom_changes=0))
    return runtime,data

def measure():
    os.chdir(ROOT);d.current();m.need(not (ROOT/CP).exists(),'recorded story must not be replayed')
    PUBLIC.mkdir(parents=True);ART.mkdir()
    state=d.read(ROOT/d.STATE);protected=dict(state['source_bindings'])
    m.need(d.bindings(set(protected))==protected,'all accepted bound sources remain unchanged')
    dev=ROOT/DEV
    manifest=d.read(dev/'manifest.json');m.need(d.bindings(set(manifest))==manifest,'original development source/trace/unit evidence')
    raw=(dev/'stdout.txt').read_bytes();baseline=m.observations(raw);commands=(dev/'commands.txt').read_text();m.commands(commands)
    # 59新oracleのローカル原本を再利用。今回の同一sourceに厳密に紐付ける。
    local=d.read(dev/'verification.json')
    m.need(d.bindings(set(local['source_bindings']))==local['source_bindings'],'exact 59-test code binding')
    unit=(dev/'unit.stderr.txt').read_bytes();m.need(local['unit_tests']==59 and unit.count(b' ... ok\n')==59 and b'\nOK\n' in unit and not (dev/'unit.stdout.txt').read_bytes(),'59 original new oracle tests')
    generated=m.generate();(PUBLIC/'generated.c.txt').write_bytes(generated)
    # guard実装は前回成功した7拒否原本と同一。無変更のguard subprocessは再起動しない。
    prior=ROOT/'content/modernization/pr16_research_natural_spending_evidence'
    old=(prior/'sources/ui.c.txt').read_text();new=generated.decode()
    def guard(s):return s[s.index('static void si_die('):s.index('static void si_flash(')]
    m.need(guard(old)==guard(new),'unchanged seven guard implementations')
    guards=d.read(prior/'guards.json')
    m.need(set(guards)=={'bus8','bus16','bus32','raw8','raw16','raw32','register'},'seven original denials')
    for row in guards.values():m.need(row==dict(returncode=1,stdout='',stderr='research-save-impact: host write after observation barrier\n'),'original guard denial')
    put(PUBLIC/'guard-reuse.json',dict(implementation=m.identity(guard(new).encode()),previous=str(prior.relative_to(ROOT))+'/guards.json',reused_guard_processes=7,new_guard_processes=0))
    runtime,data=restore();exe=OUT/'runner';source=OUT/'generated.c';source.write_bytes(generated)
    cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    p=run(cmd,ROOT,timeout=120)
    (PUBLIC/'compile.stdout.txt').write_bytes(p.stdout);(PUBLIC/'compile.stderr.txt').write_bytes(p.stderr)
    m.need(p.returncode==0 and not p.stdout and not p.stderr,'strict new host driver compile')
    put(PUBLIC/'compile.json',dict(returncode=p.returncode,generated=m.identity(generated),executable=m.identity(exe.read_bytes()),compiler=subprocess.check_output(['cc','--version']).decode()))
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    game=OUT/'new-game';game.mkdir();save=game/'story.srm';save.write_bytes(b'\xff'*131072)
    p=run(prefix+[str(data/'candidate.gba'),str(save),'new-game-story'],game,commands.encode(),timeout=240)
    (PUBLIC/'new-game.stdout.txt').write_bytes(p.stdout);(PUBLIC/'new-game.stderr.txt').write_bytes(p.stderr)
    put(PUBLIC/'new-game.execution.json',dict(returncode=p.returncode,stdout=m.identity(p.stdout),stderr=m.identity(p.stderr),save=m.identity(save.read_bytes())))
    m.need(p.returncode==0 and not p.stderr,'new story input process')
    first=m.observations(p.stdout,screens=game)
    m.need(first==baseline,'independent measurement exactly reproduces developed input trace and 18 screens')
    shutil.copy2(save,ART/'starter.srm');shutil.copy2(exe,ART/'runner')
    cold=OUT/'continue';cold.mkdir();cold_save=cold/'story.srm';cold_save.write_bytes(save.read_bytes());before=m.identity(cold_save.read_bytes())
    p=run(prefix+[str(data/'candidate.gba'),str(cold_save),'continue-story',before['sha256']],cold,b'quit\n',timeout=120)
    (PUBLIC/'continue.stdout.txt').write_bytes(p.stdout);(PUBLIC/'continue.stderr.txt').write_bytes(p.stderr)
    put(PUBLIC/'continue.execution.json',dict(returncode=p.returncode,stdout=m.identity(p.stdout),stderr=m.identity(p.stderr),input=before,output=m.identity(cold_save.read_bytes())))
    m.need(p.returncode==0 and not p.stderr,'independent new checkpoint Continue')
    second=m.observations(p.stdout,'continue-story',cold);result=m.retained(first,second)
    m.need(m.identity(save.read_bytes())==before,'original successful checkpoint file remains unchanged')
    for name,where in (('new-game',game),('continue',cold)):
        target=ART/name;target.mkdir()
        for p in where.glob('screen-*.ppm'):shutil.copy2(p,target/p.name)
    put(ART/'checkpoint.json',dict(schema_version=1,candidate=m.CANDIDATE,save=before,executable=m.identity(exe.read_bytes()),runtime_artifact=10898620034,data_artifact=10898510128,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),frame=first['end']['frames'],map=result['first_save']['map'],xy=result['first_save']['xy'],party_count=1,rp=0,save_counter=1,mode='continue-story',commands='quit\n',new_game_replay_required=False))
    m.need(d.bindings(set(protected))==protected,'protected originals unchanged after native')
    put(PUBLIC/'measurement.json',dict(**result,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),fresh_cores=2,native_processes=2,host_compiles=1,arm_compiles=0,rom_changes=0,accepted_case_reruns=0,reused_new_oracle_tests=59,new_guard_processes=0,reused_guard_processes=7,screen_count=len(first['screens'])+len(second['screens']),checkpoint=d.read(ART/'checkpoint.json'),protected_bindings=protected))
    print('PASS: natural starter story, first progress Save and independent Continue; no RP activity/release claim')

def record():
    os.chdir(ROOT);d.current();m.need(not (ROOT/CP).exists(),'no duplicate story acceptance')
    measured=d.read(PUBLIC/'measurement.json');state=d.read(ROOT/d.STATE)
    m.need(d.bindings(set(measured['protected_bindings']))==measured['protected_bindings'],'accepted sources before record')
    base='content/modernization/pr16_research_story_evidence/'+os.environ['GITHUB_RUN_ID'];evidence=ROOT/base;evidence.mkdir(parents=True)
    for p in PUBLIC.iterdir():
        if p.is_file():p.read_bytes().decode('utf-8');shutil.copy2(p,evidence/p.name)
    source=set(OWN)-{GUIDE,CP,d.STATE,d.DOC}-d.LOGS
    source|={str(p.relative_to(ROOT)) for p in (ROOT/DEV).iterdir() if p.is_file()}
    source|={str(p.relative_to(ROOT)) for p in evidence.iterdir()}
    cp=dict(measured,actions_completion_confirmed=False,status='PASS_NATURAL_STARTER_STORY_PENDING_TERMINAL',source_bindings=d.bindings(source),manifest=base+'/manifest.json',retained_artifact_name='pr16-research-story-checkpoint',retained_artifact_id=None,
            visual_review=DEV+'/visual-review.json',development=DEV+'/verification.json',next_input='continue-story only; use retained starter.srm, do not replay new-game-story',full_natural_research_activity_route_accepted=False)
    put(evidence/'manifest.json',d.bindings({str(p.relative_to(ROOT)) for p in evidence.iterdir()}))
    put(ROOT/CP,cp)
    goal='通常NewGame→自宅→屋外誘導→ヒイラギ研究所(map4/3)→リープン選択→通常Save→独立Continueを限定受入。研究活動の研究所(map96系)への通常ストーリー到達は未完。次は保存済みstarter.srmのContinueから実ストーリーを続ける。初期化/スターター/旧RP稼得支出/UI/BP/P08を再実行しない。'
    text='# PR16 通常NewGameからの自然進行\n\n## 今回の限定受入\n\n'+goal+'\n\n正本: `'+CP+'`。候補 `'+m.CANDIDATE['sha256']+'`、ROM変更0。正式測定はrun `'+os.environ['GITHUB_RUN_ID']+'` の2独立process/core。source `'+os.environ['GITHUB_SHA']+'`。Actionsの外部終端確認前であり全体完成ではない。\n\n## 実入力と継続点\n\n消去Flashから既存233区間を前提入力として使用し、未観測だった自宅退出、屋外NPCの研究所への誘導、スターター選択を追った。合計421入力/30656frames、通常Save1回でcounter0→1。map4/3 (8,5)、party1、RP0。実画面18枚をローカル開発原本と独立実測で完全一致確認し、別coreのContinue後にも実画面とparty600bytes/全Flash128KiB/場所/残高/counterを照合した。研究活動のRP研究所と序盤のヒイラギ研究所は別である。\n\n## 重複防止とartifact\n\n`pr16-research-story-checkpoint` に通常生成のstarter.srm、固定runner、checkpoint.json、実画面を保持する。固定runtimeはartifact10898620034、候補は保存recipeから復元する。checkpointのsave/executable/full candidate SHAを照合し、`continue-story` modeへ渡す。通常NewGame原本にはsave本体がなかったため今回の開発に前提入力が必要だったが、今後はこのSaveを使用しnew-game-storyを再実行しない。ROM/save/runner/画面はGit trackedに入れない。\n\n## 検証・境界\n\n新59oracle/拒否検査の原本とsource bindingをActionsで再利用。7host-write拒否も前回の同一実装/原本を再利用し再起動0。正式host compile1、native2。ARM compile/link0、ROM変更0、旧受入ケース再実行0。ローカル開発は非描画診断1と自然進行確認1で、正式受入件数には加算しない。非描画診断は最初のreset後にvideoを接続したrunnerの欠陥で、専用openerをreset前接続へ修正。ゲーム本体変更ではない。新oracleは黒画面/未対screen/未知call/注入/余分なRP/差し替えsave/過大受入を拒否する。\n\n一般CI action_required/歴史的private guardをsuccessへ読み替えない。merge/release/active baseline変更なし。\n'
    (ROOT/GUIDE).write_text(text)
    state['research_story']=dict(path=CP,status=cp['status'],candidate=m.CANDIDATE,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),natural_starter_accepted=True,natural_research_arrival_accepted=False,retained_artifact_name=cp['retained_artifact_name'])
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='NATURAL_STORY_FROM_STARTER_CONTINUE_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,DEV+'/commands.txt','docs/PR16_RESEARCH_NATURAL_SPENDING_JA.md','content/modernization/pr16_research_photo_checkpoint.json'],stop_rule_ja='まずstarter checkpoint artifactのsize/SHA/source/runを検証しContinueする。map4/3は序盤研究所であり、RP研究活動到達ではない。旧native/matrix/new-game prefixは影響なしに再実行しない。merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0,'自然starterは '+CP+'。元の通常NewGame保存試験を再オープンしない。次回はartifact starter.srmのContinueのみ。RP0/party1/map4/3保存をRP研究活動到達へ昇格しない。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='新しい自然starter進行の独立Actions実測source。自己記録commitではない。終端は次の外部API読取で確定する。'
    runs=d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=50');m.need(runs['total_count']==len(runs['workflow_runs'])<=50,'complete source run list')
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=[d.run_summary(r) for r in runs['workflow_runs']],reason_ja='未完/一般CI action_requiredを原値で保持。限定native成功と全体CI/releaseは別。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs['workflow_runs'] if r['status'] in ('queued','in_progress')]
    for p in source|{GUIDE,CP,base+'/manifest.json'}:state['source_bindings'][p]=m.identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 通常NewGameから自然スターター保存へ\n- Version: research-natural-starter-v1\n- Status: DONE（スターター保存・Continue限定、RP研究活動への到達未完）\n- Summary: 自宅→屋外NPC誘導→序盤研究所→リープン選択を421入力/30656framesで独立再現。party0→1、RP0、通常Save counter0→1、別core Continueで全party/Flash/場所/残高保持。次はartifact内の通常生成starter.srmから継続し前提入力を繰り返さない。\n- Files changed: 専用input-only C/generator/oracle/test、開発・正式原本text/引継ぎMD/JSON、両ログ。画面/save/runnerはartifactのみ。\n- Verify: 新59oracle原本/source一致PASS、7旧guard拒否原本/実装一致再利用PASS。正式host compile1/native2core/画面19。ARM/ROM変更0、旧受入ケース再実行0。render/check/task graph/scoped index/diff検査後にcommit。\n- Development: video接続順の非描画診断1と正常進行診断1。loader失敗の原本とmissing-headerのtool観測を区別して保存。最初のmissing-header stderrは未保存。正式native件数へ加算しない。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; 同branch非force push。終端確認は外部APIで別記録。\n- Network: GitHub固定artifact/Actions/APIのみ。merge/release/baseline変更0。一般CI action_required/歴史的全体guardを成功扱いしない。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a') as f:f.write(entry)
    paths=OWN|source|{base+'/manifest.json'};put(OUT/'owned.json',sorted(paths));print('PASS: scoped starter resume and append-only logs recorded')

def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    d.current();pr16_resume.validate(ROOT);g.START='a088b40b023a4f6471538ddb5885e42c6d76529a';g.CODE=set();g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)

def snapshot():
    owned=d.read(OUT/'owned.json');head=d.git('rev-parse','HEAD').decode().strip()
    with zipfile.ZipFile(ART/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in owned:
            b=d.git('show','HEAD:'+p);b.decode();z.writestr(p,b)
        z.writestr('record-head.txt',head+'\n')
    for p in PUBLIC.iterdir():
        if p.is_file():shutil.copy2(p,ART/p.name)

if __name__=='__main__':
    op=sys.argv[1:]
    if op==['measure']:measure()
    elif op==['record']:record()
    elif op==['guard']:guard()
    elif op==['snapshot']:snapshot()
    elif op==['paths']:print('\n'.join(d.read(OUT/'owned.json')))
    else:raise SystemExit('measure|record|guard|snapshot|paths')
