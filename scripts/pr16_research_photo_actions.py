#!/usr/bin/env python3
"""写真の未受入native境界だけを測り、成功原本と終端を別commitで同期する。"""
import datetime
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_photo as m
import pr16_research_lifecycle_actions as d
from pr16_research_phase0_load_actions import terminal
need,identity=m.need,m.identity
TASK='USER-20260927-RESEARCH-PHOTO'
WF='.github/workflows/pr16-research-photo-20260927.yml'
SELF='scripts/pr16_research_photo_actions.py'
CP='content/modernization/pr16_research_photo_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_PHOTO_JA.md'
BASE='content/modernization/pr16_research_photo_evidence'
PREVIOUS='content/modernization/pr16_research_catalog_checkpoint.json'
INITIAL='169b73df380b9a2a762c7cddeb4d22d69432a306'
OWN={WF,SELF,'scripts/pr16_research_photo.py',m.C,'tests/test_pr16_research_photo.py'}
IMAGES=d.OUT/'photo-screens'
GOAL='次は他5活動の実RP稼得と、通常進行によるResearch受付/ショップへの接続。写真0→6RP・取消/同日重複拒否/取引保存/独立Continue・写真3文言、catalog23商品/5画面と35会話ROM byteは受入原本を再利用。自然到達、他5活動、全会話native表示、releaseは未受入。'

def run_logged(name,args,timeout=180,cwd=ROOT):
    result=subprocess.run(args,cwd=cwd,capture_output=True,timeout=timeout)
    (d.PUBLIC/(name+'.stdout.txt')).write_bytes(result.stdout)
    (d.PUBLIC/(name+'.stderr.txt')).write_bytes(result.stderr)
    return result

def measure():
    d.current();need(not Path(CP).exists(),'既存写真原本の再実行禁止')
    d.PUBLIC.mkdir(parents=True);IMAGES.mkdir()
    previous=d.read(PREVIOUS)
    need(previous['catalog_accepted'] and previous['actions_completion_confirmed'] and not previous['failed_cases'],'catalog終端受入')
    need(d.bindings(previous['protected_bindings'])==previous['protected_bindings'],'旧受入保全')
    for path,binding in previous['source_bindings'].items():
        if path!='.github/workflows/pr16-research-supply-20260927.yml':
            need(identity(Path(path).read_bytes())==binding,'catalog source不変 '+path)
    prior_terminal=terminal(previous['finalize_run_id'],previous['finalize_source_head'],'.github/workflows/pr16-research-supply-20260927.yml')
    protected_paths=set(previous['protected_bindings'])|set(previous['source_bindings'])|{PREVIOUS,'docs/PR16_RESEARCH_CATALOG_JA.md'}
    protected_paths|={str(p) for p in Path('content/modernization/pr16_research_catalog_evidence').rglob('*') if p.is_file()}
    protected=d.bindings(protected_paths);sources=d.bindings(set(previous['source_bindings'])|OWN)
    stats=dict(new_unit_tests=0,host_compiles=0,native_processes=0,guard_processes=0,
               arm_compiles=0,arm_links=0,rom_changes=0,accepted_case_reruns=0)
    d.put('invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=sources,
        protected_bindings=protected,previous_terminal=prior_terminal,
        guard_reuse=dict(checkpoint=PREVIOUS,measurement=previous['measurement'],cases=7,
                        source_unchanged=True,reason='7 API拒否の受入は同一helper原本を再利用。新mainにもguardを有効化しhost書込みを拒否。')))
    result=dict(status='FAIL',counts=stats,failures=[])
    try:
        unit=run_logged('unit',[sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_photo.py','-v'])
        stats['new_unit_tests']=(unit.stdout+unit.stderr).count(b' ... ok\n')
        need(unit.returncode==0 and stats['new_unit_tests']==43,'新規43 oracle（全owner変異384を含む）')
        runtime,data,seed,parent,artifacts=d.restore()
        import pr16_research_retry as retry
        import pr16_research_v1_corrupt_load as corrupt
        candidate,_=retry.apply(parent,bytes.fromhex(d.read('content/modernization/pr16_research_retry_recipe.json')['after']))
        recipe=d.read('content/modernization/pr16_research_v1_corrupt_load_recipe.json')
        candidate,_=corrupt.apply(candidate,bytes.fromhex(recipe['after'])[:corrupt.CODE['size']])
        d.put('physical-binding.json',m.physical(candidate))
        rom=d.OUT/'photo-candidate.gba';rom.write_bytes(candidate)
        save=d.OUT/'photo.srm';fixture,receipt=m.fixture(seed);save.write_bytes(fixture)
        code=d.OUT/'photo.c';code.write_bytes(m.generate(seed));exe=d.OUT/'photo-runner'
        d.put('inputs.json',dict(candidate=identity(candidate),seed=identity(seed),fixture=receipt,runtime_artifacts=artifacts,
              generated_source=identity(code.read_bytes()),stopped_fixture='progress and stock warp to map96/37 (48,5); initial RP/lifetime/claim=0',
              after_barrier='physical keys and read-only observations only; no activity call/result/RP injection'))
        command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.',
                 '-I'+str(runtime/'include'),str(code),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
        stats['host_compiles']=1;compiled=run_logged('compile',command)
        need(compiled.returncode==0 and not compiled.stderr,'strict host build')
        d.put('compile.json',dict(command=command,compiler=subprocess.check_output(['cc','--version']).decode(),
                                 executable=identity(exe.read_bytes()),source=identity(code.read_bytes())))
        prefix=[str((runtime/'ld.so').resolve()),'--library-path',str((runtime/'lib').resolve()),str(exe.resolve())]
        stats['native_processes']=1
        process=run_logged('native',prefix+[str(rom.resolve()),str(save.resolve()),m.CASE],180,IMAGES)
        need(process.returncode==0 and not process.stderr,'新規native写真case')
        native=m.validate(process.stdout,fixture)
        need({p.name for p in IMAGES.iterdir()}==set(m.SCREENS),'全7画像、余剰/不足なし')
        for name,digest in m.SCREENS.items():
            raw=(IMAGES/name).read_bytes()
            need(raw.startswith(b'P6\n240 160\n255\n') and len(raw)==115215 and identity(raw)['sha256']==digest,'同一の目視済み画面 '+name)
        result.update(status='PASS',native=native,visual_review=dict(status='PASS',dialogues=3,
            note_ja='調査確認・6ポイント報酬・本日記録済みの3文言を目視。Actionsも同一画面hash。35会話全部とは主張しない。'))
    except Exception as exc:
        result['failures'].append(dict(type=type(exc).__name__,reason=str(exc)))
    result['local_diagnostics']=dict(host_compiles=4,native_processes=4,new_unit_tests=43,
        outcomes=['最初の2回は方向転換で既に背景eventが始まり、二重開始を前提としたstance検査が停止。画面を読んで入力driverだけ修正。',
                  '3回目は稼得/保存/重複拒否PASS。ただし報酬画面の採取がphase2保存完了前でpromptのままだったため、表示受入にはしない。',
                  '4回目は実保存counter+2を待って報酬を採取し、7画像/3文言と全観測の検査もPASS。'],
        production_changes=0,accepted_case_reruns=0)
    need(d.bindings(protected)==protected and d.bindings(sources)==sources,'全source/過去証拠不変')
    d.put('measurement.json',result)
    directory=BASE+'/'+os.environ['GITHUB_RUN_ID'];need(not Path(directory).exists(),'原本追記専用')
    manifest={}
    for source in sorted(d.PUBLIC.iterdir()):
        raw=source.read_bytes();raw.decode('utf-8');need(source.suffix in ('.json','.txt') and b'\0' not in raw and len(raw)<2000000,'tracked原本は有界UTF8だけ')
        dest=Path(directory)/source.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);manifest[str(dest)]=identity(raw)
    d.write(Path(directory)/'manifest.json',manifest)
    accepted=result['status']=='PASS'
    cp=dict(schema_version=1,task=TASK,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=m.CANDIDATE,
        source_bindings=sources,protected_bindings=protected,status='PASS_PHOTO_PENDING_TERMINAL' if accepted else 'FAIL_PHOTO_RECORDED',
        photo_accepted=accepted,actions_completion_confirmed=False,counts=stats,measurement=directory+'/measurement.json',
        manifest=directory+'/manifest.json',failed_cases=[] if accepted else [m.CASE],real_photo_earning_accepted=accepted,
        photo_dialogue_native_accepted=accepted,all_activities_accepted=False,natural_arrival_accepted=False,
        shop_connection_accepted=False,all_dialogue_native_display_accepted=False,release_ready=False,active_baseline_changed=False,
        prior_catalog=PREVIOUS)
    publish(cp,set(manifest)|{directory+'/manifest.json'},'measure')

def publish(cp,owned,mode):
    from pr16_learnset_compact_record import publish_resume
    d.write(CP,cp)
    goal=GOAL if cp['photo_accepted'] else '写真原本の失敗だけを診断し、成功したunit/nativeは再実行せず記録修復する。'+GOAL
    guide='# PR16 写真調査の実RP稼得\n\n'+cp['status']+'\n\n'+goal+'\n\n'
    guide+='## 限定受入\n\n正本PHOTOGRAPHYは6RP/日上限6。map96/37の実背景0(48,4)を物理キーで開始し、取消ではRP/Flash不変、確認で0→6RP・日内6・生涯6・claim4・取引ID2を得る。取引自身の実保存2回だけで永続化し、同日再実行、独立coreの通常Continue、再度の実行でも追加加算/保存は0。全Bag/party600/ledger2048（自然minuteのみ除外）とFlashを検査する。\n\n'
    guide+='進行と開始map(48,5)は停止fixture。RPを加算するhost関数は呼ばず、観測後の7 API書込みを拒否。最初のUPでeventが始まる場合は二重Aを送らない。prompt/6ポイント報酬/日上限の実3文言を目視し、7原本PPMのSHAをActionsと照合。保存中のpromptを報酬画面へ読み替えない。\n\n'
    guide+='## 実行数と原本\n\nsource `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'` / `'+cp['measurement']+'`。新規43検査（全64owner byte×6状態の変異384を含む）、host compile1、新native1（fresh core2）、ARM0。catalogの同一7 API拒否原本を再利用しguard再実行0。ローカル準備はcompile/native各4、43検査1回。2つのstance診断と1つの早すぎる画面採取を限定driverで修正、ROMは不変。終端同期はunit/native/compile0。\n\n'
    guide+='## 全体CIと残作業\n\n今回の限定PASSと一般CIは別。実装前source-validation run36251713025/job108430855211はP03 capacityの25検査中2errorで、固定証拠に対する `tested source changed: overlays/qol_production/qol_production.c` が原因だった。今回そのproduction sourceやP03証拠を改変しない。全CI成功/merge/releaseは主張しない。通常new-game、購入、取消、catalog、旧保存の受入原本を保全。写真以外5活動・自然到達・通常経路からショップ接続は別の未完境界。\n'
    Path(GUIDE).write_text(guide)
    state=d.read(d.STATE)
    state['research_photo']={k:cp[k] for k in ('status','source_head','run_id','photo_accepted','actions_completion_confirmed','candidate')}
    state['research_photo']['path']=CP
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_OTHER_ACTIVITIES_AND_NATURAL_CONNECTION_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,'scripts/pr16_research_photo.py',SELF,m.C,'docs/PR16_RESEARCH_CATALOG_JA.md',PREVIOUS,
                    'docs/PR16_RESEARCH_NEW_GAME_JA.md','content/modernization/pr16_research_new_game_checkpoint.json',
                    'overlays/research_economy_v1/research_economy_v1.c',m.catalog.MODEL])
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='写真限定記録source。自己SHAはgit log参照。'
    runs=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=12')['workflow_runs']
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=[d.run_summary(r) for r in runs],
        reason_ja='写真限定検証と全体CIを分離。既存P03 capacityのsource pin failure/承認待ちを全CI成功へ昇格しない。')
    for path in OWN|{CP,GUIDE}:state['source_bindings'][path]=identity(Path(path).read_bytes())
    note='写真の0→6RP/取消/同日重複拒否/取引保存/独立Continueと3文言は専用原本を再利用。全活動/自然到達/通常ショップ接続に昇格しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 写真実RP稼得\n- Version: research-photo-v1\n- Status: '+('DONE' if cp['photo_accepted'] else 'BLOCKED')+'（限定scope）\n- Summary: '+cp['status']+' / '+mode+'。0→6RP/同日重複拒否/取引保存2/独立Continueと写真3文言。自然到達/全活動/ショップ接続は未受入。\n- Files changed: 写真validator/native/43検査/Actions/専用MD/JSON/UTF8証拠、固定引継ぎ、両ログ。\n- Verify: 新規43検査、host1/native1（core2）/ARM0、7 guardは同一受入原本再利用。準備compile/native各4、stance2診断と早い画像1を修正。終端は再実行0。resume/task graph/index guardをcommit前に検査。\n- Commit: source='+os.environ['GITHUB_SHA']+'、同branch非force push。自己SHAはgit log参照。\n- Network: GitHub接続API/固定artifactのみ。ROM/save非tracked、active baseline不変。一般CI既存P03 pin failureは別件、release/mergeなし。\n'
    for path in sorted(d.LOGS):
        with Path(path).open('a') as stream:stream.write(log)
    d.write(d.OUT/'photo-owned.json',sorted(owned|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))

def finalize():
    d.current();d.PUBLIC.mkdir(parents=True);cp=d.read(CP)
    need(cp['photo_accepted'] and not cp['failed_cases'] and not cp['actions_completion_confirmed'],'成功原本を一度だけ終端同期')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'過去受入保全')
    for path,binding in cp['source_bindings'].items():
        if path!=WF:need(identity(Path(path).read_bytes())==binding,'測定source一致 '+path)
    cp['terminal']=terminal(cp['run_id'],cp['source_head'],WF)
    cp.update(status='PASS_PHOTO_REAL_EARNING_SCOPED',actions_completion_confirmed=True,
              finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal-verification.json',cp['terminal']);publish(cp,set(),'finalize')

def guard():
    cp=d.read(CP);need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'全旧証拠/source保全')
    owned=set(d.read(d.OUT/'photo-owned.json'));subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    allowed=OWN|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS
    changed=set(d.git('diff','--cached','--name-only',INITIAL).decode().splitlines())
    need(all(p in allowed or p.startswith(BASE+'/') for p in changed),'catalog終端HEADからの差分限定')
    for path in d.LOGS:need(Path(path).read_bytes().startswith(d.git('show',INITIAL+':'+path)),'両ログappend-only')
    subprocess.run(['git','diff','--cached','--check'],check=True)

if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['result']:need(not d.read(CP)['failed_cases'],'失敗原本の誤受入を拒否')
    else:raise SystemExit('measure | finalize | guard | result')
