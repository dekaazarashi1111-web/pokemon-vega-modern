#!/usr/bin/env python3
"""未受入の通常new-gameだけを測定。購入/取消の受入原本は再実行しない。"""
from __future__ import annotations
import datetime
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_shop_cancel_actions as previous
import pr16_research_new_game as m
import pr16_research_purchase_actions as purchase
import pr16_research_retry as retry
import pr16_research_v1_corrupt_load as corrupt
d=previous.d;need=d.need;identity=d.identity
TASK='USER-20260926-RESEARCH-NEW-GAME'
SELF='scripts/pr16_research_new_game_actions.py'
MODEL='scripts/pr16_research_new_game.py'
TEST='tests/test_pr16_research_new_game.py'
WF='.github/workflows/pr16-research-new-game-20260926.yml'
CP='content/modernization/pr16_research_new_game_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_NEW_GAME_JA.md'
EVIDENCE='content/modernization/pr16_research_new_game_evidence'
OWN_SOURCE={SELF,MODEL,TEST,WF,m.C}


def unit(sources,old):
    deps={p:b for p,b in sources.items() if p not in {SELF,WF}}
    if old:
        unit_path=str(Path(old['manifest']).parent/'unit.json');v=d.read(ROOT/unit_path)
        need(v['tests']==52 and v['successful'] and v['errors']==v['failures']==v['skips']==0,'previous successful52')
        if v['dependencies']==deps:
            d.put('unit.json',v);(d.PUBLIC/'unit.txt').write_bytes((ROOT/Path(unit_path).with_name('unit.txt')).read_bytes())
            d.put('unit-reuse.json',{'run_id':old['run_id'],'new_unit_tests':0,'reused_unit_tests':52,'native_success_claimed':False})
            return 0
        changed=[p for p in sorted(set(deps)|set(v['dependencies'])) if deps.get(p)!=v['dependencies'].get(p)]
        d.put('unit-invalidation.json',{'previous_run':old['run_id'],'changed_dependencies':changed,'reason':'generation/source assertions depend on changed inputs'})
    spec=importlib.util.spec_from_file_location('new_game_tests',ROOT/TEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    (d.PUBLIC/'unit.txt').write_text(stream.getvalue());print(stream.getvalue(),flush=True)
    d.put('unit.json',{'dependencies':deps,'tests':r.testsRun,'errors':len(r.errors),'failures':len(r.failures),'skips':len(r.skipped),'successful':r.wasSuccessful()})
    need(r.wasSuccessful() and r.testsRun==52 and not r.skipped,'new52 oracle tests')
    return 52


def publish(cp,evidence,mode):
    from pr16_learnset_compact_record import publish_resume
    ok=bool(cp['accepted_cases'])
    summary=('通常new-gameを消去Flashからキー入力のみで開始し、初回Start Saveと独立Continue2回を受入。counter0→1→1→1、全ledger2048/Bag5pocket/party600/Flash128KiBを照合。' if ok else '通常new-gameの未完native停止を別原本で保存。初回保存のローカル診断と正式受入は区別する。')
    goal=('次は実RP稼得と通常進行からResearchショップへの接続、全catalog価格/日本語文言の監査。通常new-game1件・購入1件・取消1件、各oracleと旧host/phase0/V1/retryは影響なしに再実行しない。' if ok else '新規checkpointのnative停止原本とsourceを読む。最小修正後に未完caseのみ進め、購入/取消や旧nativeを反復しない。')
    if ok and not cp['actions_completion_confirmed']:goal='まず本runの終端・非force push・uploadを照合する。'+goal
    d.write(ROOT/CP,cp)
    text='# PR16 通常new-game・初回Save・独立Continue\n\n'+summary+'\n\n## 実行条件\n\n128KiB全FFのFlashから開始。元private seedはnative入力に使用しない。通常BOOT_TRACE先頭233区間/13490framesと600framesの静止だけを使用し、初期化関数の直接呼出・文字速度変更・進行/party/ledger注入・warp・register/stack fixtureは0。RTC準備はmGBAの付加16bytesだけでFlash全byte不変を照合し、7API書込barrierを最初のゲーム実行前に装着する。旧fixture付きfield trace helperは呼ばない。\n\n実scriptが終了したmap4/0の(10,2)、実player object(17,9)/西向き・移動停止を確認し、最初の通常Start Saveへ進む。starter取得前でparty count0。全台帳はVGS1/V2/2048、孵化mode1、ExpShare0、文字速度0、研究rank1/nextTransaction1/RP0、通常minuteとchecksum以外はsource初期値であることを独立に照合する。初回保存前Flash全FF/counter0、Save後counter1と実Flash変更、独立coreのContinue2回は全128KiB Flash不変・counter1・全Bag/party/ledger/位置保持を要求する。\n\n## 境界\n\n対象は通常new-gameの初回保存境界だけ。スターター取得、実RP稼得、通常進行からショップへの到達、全catalog、日本語画面の目視監査、Issue19全体/P08/releaseは未受入。候補は購入と同じ5d1fc9、ROM変更/ARM compile/link/旧受入再実行0。新C検査52件にはmain一意・注入API呼出禁止とtrace構文/正規化hashを含む。\n\n## 記録\n\nrun `'+str(cp['run_id'])+'` / source `'+cp['source_head']+'` / status `'+cp['status']+'` / 終端確認 `'+str(cp['actions_completion_confirmed'])+'`。manifest `'+cp['manifest']+'`。失敗原本はattempt_historyに保持し、途中の成功で全体を昇格しない。一般CIのaction_requiredは限定成功とは別である。\n\n## 次工程\n\n'+goal+'\n'
    (ROOT/GUIDE).write_text(text)
    state=d.read(ROOT/d.STATE)
    state['research_normal_new_game']={k:cp[k] for k in ('status','candidate','accepted_cases','failed_cases','run_id','actions_completion_confirmed')};state['research_normal_new_game']['path']=CP
    state['bp']['current_stop']=summary;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_NATURAL_SUPPLY_AND_CATALOG_NEXT' if ok else 'RESEARCH_NEW_GAME_NATIVE_REPAIR',goal_ja=goal,read_paths=[GUIDE,CP,MODEL,SELF,m.C,purchase.CP,purchase.GUIDE,'overlays/research_economy_v1/research_economy_v1.c','overlays/qol_production/qol_production.c'],stop_rule_ja='新規開始/初回保存だけの受入をstarter/実RP/自然供給/全catalogへ拡張しない。受入済みcase反復/merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='通常new-gameの実行/終端記録source。自己SHAはgit log。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':'success' if cp['actions_completion_confirmed'] else None}],'reason_ja':'scoped原本と終端を区別。一般CIは別状態。'}
    for path in OWN_SOURCE|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 通常new-game・初回Save・独立Continue\n- Version: research-new-game-{mode}-v1\n- Status: '+('DONE（初回保存限定、自然供給未完）' if ok else 'STOPPED（新native失敗原本保存）')+'\n- Summary: '+summary+'\n- Files changed: '+', '.join(sorted(OWN_SOURCE|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))+' と限定UTF8証拠。\n- Verify: ローカル新52oraclePASS。Actions新unit='+str(cp['new_unit_tests'])+'、native1process（成功時3cores）/guard7/host compile1。初期化/warp/文字速度/台帳/party注入0。ROM変更/ARM compile/link/旧受入再実行0。finalizeはunit/native/compile0。失敗='+str(cp['failed_cases'])+'。後続resume/task graph/scoped final-index/diff gate後にcommit。全体歴史private guard成功は主張しない。\n- Diagnosis: 正式測定前に同候補/消去Flashでinput-onlyローカル診断1process/1host compile、通常開始と初回Saveを確認。独立Continueは診断未実行。受入件数へ加算しない。\n- Commit: source='+os.environ['GITHUB_SHA']+'、同branch非force。自己SHAはgit log。\n- Network: GitHub固定artifact/PR/Actions。元ROM/save非tracked、履歴/baseline保全。merge/release0。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a') as f:f.write(log)
    d.write(d.OUT/'new-game-owned.json',sorted(evidence|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))
    d.put('record-summary.json',{k:cp[k] for k in ('status','run_id','accepted_cases','failed_cases','actions_completion_confirmed')})


def measure():
    os.chdir(ROOT);d.current();d.PUBLIC.mkdir(parents=True)
    old=d.read(ROOT/CP) if (ROOT/CP).exists() else None
    if old:need(old['failed_cases'] and not old['accepted_cases'],'do not repeat accepted native')
    previous_cp=d.read(ROOT/purchase.CP);need(previous_cp['actions_completion_confirmed'] and previous_cp['candidate']==m.CANDIDATE,'purchase baseline complete')
    terminal=previous.prior.terminal(previous_cp['finalize_run_id'],previous_cp['finalize_source_head'],purchase.WF)
    tracked=d.git('ls-files').decode().splitlines();need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')],'nested agent rules need review')
    paths=set(previous_cp['protected_bindings'])|set(previous_cp['source_bindings'])|{purchase.CP,purchase.GUIDE,purchase.WF,'docs/PR16_RESEARCH_PURCHASE_DIAGNOSTICS_JA.md'}
    paths|={p for p in tracked if p.startswith(purchase.EVIDENCE+'/') or p.startswith(EVIDENCE+'/')}
    protected=d.bindings(paths);sources=d.bindings(OWN_SOURCE|set(previous_cp['source_bindings']))
    history=[] if not old else old.get('attempt_history',[])+[{k:old[k] for k in ('run_id','source_head','status','manifest','measurement','accepted_cases','failed_cases')}]
    if old:
        oldrun=d.inputs.api('actions/runs/'+str(old['run_id']));need(oldrun['status']=='completed' and oldrun['conclusion']=='failure' and oldrun['head_sha']==old['source_head'],'previous native failure terminal preserved')
        d.put('previous-run.json',d.run_summary(oldrun))
    recent=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    d.put('latest-runs.json',[d.run_summary(r) for r in recent])
    d.put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':sources,'protected_bindings':protected,'previous_terminal':terminal,'accepted_case_reruns':0})
    units=unit(sources,old)
    runtime,data,seed,parent,artifacts=d.restore()
    current,_=retry.apply(parent,bytes.fromhex(d.read(ROOT/previous.prior.RETRY_RECIPE)['after']))
    recipe=d.read(ROOT/previous.prior.CORRUPT_RECIPE);candidate,_=corrupt.apply(current,bytes.fromhex(recipe['after'])[:corrupt.CODE['size']])
    need(identity(candidate)==m.CANDIDATE,'unchanged current candidate; no ARM build')
    rom=d.OUT/'new-game.gba';rom.write_bytes(candidate);save=b'\xff'*131072;target=d.OUT/'new-game.srm';target.write_bytes(save)
    generated=m.generate();source=d.OUT/'new-game.c';source.write_bytes(generated);exe=d.OUT/'new-game'
    d.put('inputs.json',{'candidate':identity(candidate),'erased_flash':identity(save),'normal_trace':m.trace(),'private_seed_used_as_native_input':False,'artifacts':artifacts,'generated_source':identity(generated),'rom_changes':0,'arm_compiles':0})
    command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    comp=subprocess.run(command,capture_output=True,timeout=120)
    (d.PUBLIC/'compile.stdout.txt').write_bytes(comp.stdout);(d.PUBLIC/'compile.stderr.txt').write_bytes(comp.stderr)
    d.put('compile.json',{'command':command,'returncode':comp.returncode,'executable':identity(exe.read_bytes()) if exe.exists() else None,'generated':identity(generated)})
    if comp.stderr:print(comp.stderr.decode(),flush=True)
    need(comp.returncode==0 and not comp.stderr,'strict driver compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)];guards={}
    for method in m.closed.GUARDS:
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        need(p.returncode==1 and not p.stdout and p.stderr==m.closed.DENIED,'seven barriers '+method);guards[method]={'returncode':p.returncode,'stderr':identity(p.stderr)}
    d.put('guards.json',guards)
    try:
        p=subprocess.run(prefix+[str(rom),str(target),m.CASE],capture_output=True,timeout=300);out,err=p.stdout,p.stderr;status={'returncode':p.returncode,'timeout':False}
    except subprocess.TimeoutExpired as exc:out,err=exc.stdout or b'',exc.stderr or b'';status={'returncode':None,'timeout':True}
    (d.PUBLIC/'native.stdout.txt').write_bytes(out);(d.PUBLIC/'native.stderr.txt').write_bytes(err)
    d.put('native-process.json',dict(status,stdout=identity(out),stderr=identity(err)))
    print(out.decode('utf-8'),flush=True)
    if err:print(err.decode('utf-8'),flush=True)
    accepted=None;failure=None
    try:
        need(status['returncode']==0 and not status['timeout'] and not err,'completed clean native process');accepted=m.validate(out)
    except (ValueError,KeyError,TypeError) as exc:failure={'exception_type':type(exc).__name__,'reason':str(exc)}
    d.put('measurement.json',{'accepted':accepted,'failure':failure,'candidate':m.CANDIDATE,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID'])})
    need(d.bindings(protected)==protected and d.bindings(sources)==sources,'historical/source preservation')
    need(identity(rom.read_bytes())==m.CANDIDATE and identity((data/'seed.srm').read_bytes())==identity(seed),'read-only originals')
    directory=EVIDENCE+'/'+os.environ['GITHUB_RUN_ID'];need(not (ROOT/directory).exists(),'immutable evidence');evidence={}
    for p in sorted(d.PUBLIC.iterdir()):
        need(p.is_file() and p.suffix in ('.json','.txt'),'public text only');raw=p.read_bytes();raw.decode();need(b'\0' not in raw and len(raw)<=2000000,'bounded text only')
        dest=ROOT/directory/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);evidence[str(dest.relative_to(ROOT))]=identity(raw)
    d.write(ROOT/directory/'manifest.json',evidence)
    cp={'schema_version':1,'task':TASK,'status':'PASS_NORMAL_NEW_GAME_PENDING_TERMINAL' if accepted else 'FAIL_NORMAL_NEW_GAME_RECORDED','source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,'accepted_cases':[m.CASE] if accepted else [],'failed_cases':[] if accepted else [m.CASE],'new_unit_tests':units,'native_processes':1,'fresh_cores':3 if accepted else None,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'arm_links':0,'rom_changes':0,'accepted_case_reruns':0,'source_bindings':sources,'protected_bindings':protected,'measurement':directory+'/measurement.json','manifest':directory+'/manifest.json','actions_completion_confirmed':False,'purchase_previously_accepted':True,'normal_new_game_accepted':bool(accepted),'natural_progress_accepted':False,'active_baseline_changed':False,'issue19_complete':False,'release_ready':False,'prior_terminal':terminal,'attempt_history':history}
    publish(cp,set(evidence)|{directory+'/manifest.json'},'measure')


def finalize():
    os.chdir(ROOT);d.current();d.PUBLIC.mkdir(parents=True);cp=d.read(ROOT/CP)
    need(cp['accepted_cases']==[m.CASE] and not cp['failed_cases'] and not cp['actions_completion_confirmed'],'finalize accepted exactly once')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected history')
    for p,b in cp['source_bindings'].items():
        if p!=WF:need(identity((ROOT/p).read_bytes())==b,'measured source unchanged '+p)
    cp['terminal']=previous.prior.terminal(cp['run_id'],cp['source_head'],WF)
    cp.update(status='PASS_NORMAL_NEW_GAME_SCOPED',actions_completion_confirmed=True,finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal-verification.json',cp['terminal']);publish(cp,set(),'finalize')


def guard():
    os.chdir(ROOT);cp=d.read(ROOT/CP);owned=set(d.read(d.OUT/'new-game-owned.json'))
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected paths')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard();subprocess.run(['git','diff','--cached','--check'],check=True)

if __name__=='__main__':
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['result']:
        cp=d.read(ROOT/CP);need(not cp['failed_cases'],'failed native retained; do not promote')
    else:raise SystemExit('measure | finalize | guard | result')
