#!/usr/bin/env python3
"""未受入の実ショップ取消だけを検証・保存。以前の受入は再実行しない。"""
from __future__ import annotations
import datetime
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_ui_boundary_actions as host
import pr16_research_shop_cancel as m
import pr16_research_retry as retry
prior=host.prior;d=host.d;need=host.need;identity=host.identity
TASK='USER-20260926-RESEARCH-SHOP-CANCEL'
SELF='scripts/pr16_research_shop_cancel_actions.py'
MODEL='scripts/pr16_research_shop_cancel.py'
TEST='tests/test_pr16_research_shop_cancel.py'
WF='.github/workflows/pr16-research-shop-cancel-20260926.yml'
CP='content/modernization/pr16_research_shop_cancel_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_SHOP_CANCEL_JA.md'
EVIDENCE='content/modernization/pr16_research_shop_cancel_evidence'
OWN_SOURCE={SELF,MODEL,TEST,WF,m.C}


def publish(cp,evidence):
    from pr16_learnset_compact_record import publish_resume
    summary='実ResearchショップのB取消/末尾取消と通常Save→独立Continue2回を受入。進行・100RP・stock warpはfixture、購入/new-game全体は未受入。'
    goal='次は通常new-game→初回Save/Continueと実ショップの選択/購入/不足/保存境界。取消2経路/native1件/新oracle20件、host49件、既受入phase0/V1/retryは影響なしに再実行しない。'
    if not cp['actions_completion_confirmed']:goal='まず本runの終端・非force push・uploadを照合する。'+goal
    d.write(ROOT/CP,cp)
    text='# PR16 実ショップ取消・通常Save/Continue\n\n'+summary+'\n\n## 実経路\n\n現候補のmap98/3背景0、(2,1)の実script pointerを確認。初期進行/残高はprivate seedのledgerだけのfixture。停止区間でstock warp4呼出とfield callback1wordを設定し(2,2)へ入る。以後7 API書込barrierを装着し、通常方向/A/B入力だけで実menu task/windowの生成、B取消、再受付と全表示ページの末尾取消、task/window解放、idle field復帰を確認。shop dispatch・結果・PCの観測中注入なし。停止fixtureのregister/stack書込が0とは主張しない。\n\n取消両経路で128KiB Flash全byte/counter不変、全Bag5pocket/party600byte不変、ledger全2048byteは通常minuteとそのchecksum以外不変。研究ownerは100RP/rank1/nextTransaction1のまま、稼得/消費/pending/claim変更0。通常Start Save1回/counter+1、独立coreのContinue2回でledger/Bag/party保持とUI揮発状態resetを確認。\n\n## 計測\n\n新native1process/3cores、7guard拒否probe、host compile1、oracle20PASS。旧受入再実行/ARM compile/link/ROM変更0。候補 `'+m.CANDIDATE['sha256']+'` を既存recipeから復元。失敗試行があれば別原本として保存し成功に読み替えない。画面の目視監査・全catalog価格/日本語文言・購入成功・通常進行からの到達・実RP稼得・通常new-gameは未受入。\n\n## 次工程\n\n'+goal+'\n\nrun `'+str(cp['run_id'])+'` / source `'+cp['source_head']+'` / 終端確認 `'+str(cp['actions_completion_confirmed'])+'`。manifest/source/protected bindingsはcheckpoint参照。一般CIのaction_requiredは全CI成功に読み替えない。\n'
    (ROOT/GUIDE).write_text(text)
    state=d.read(ROOT/d.STATE)
    state['research_shop_cancel']={k:cp[k] for k in ('status','candidate','accepted_cases','run_id','actions_completion_confirmed')};state['research_shop_cancel']['path']=CP
    state['bp']['current_stop']=summary;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_NEW_GAME_AND_PURCHASE_UI_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,MODEL,SELF,m.C,host.CP,m.prior.SOURCE,'overlays/qol_production/qol_production.c'],stop_rule_ja='取消のnative受入を購入/new-game/自然進行へ拡張しない。受入反復/merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='実ショップ取消の実行/終端記録source。自己SHAはgit log。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':'success' if cp['actions_completion_confirmed'] else None}],'reason_ja':'限定native取消のみ。一般CI action_requiredは別状態。'}
    for path in OWN_SOURCE|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 実ショップ取消と通常Save/Continue\n- Version: research-shop-cancel-v1\n- Status: DONE（取消限定、購入/new-game未受入）\n- Summary: '+summary+'\n- Files changed: '+', '.join(sorted(OWN_SOURCE|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))+'、限定public証拠。\n- Verify: oracle20PASS、native1process/3cores、7guard拒否、strict host compile1。全Flash取消不変/全Bag/party/ledger対照、通常Save1回/Continue2回。既受入再実行/ROM変更/ARM compile/link0。終端記録でnative/unit/compile再実行0。終端確認='+str(cp['actions_completion_confirmed'])+'。resume/task graph/scoped final-index guard/diff-checkは同run後続gate。全体歴史private guard成功は主張しない。\n- Commit: source='+os.environ['GITHUB_SHA']+'、同branch非force。自己SHAはgit log。\n- Network: GitHub固定artifact/Actions API。私有入力は.localのみ、新規tracked binary0。merge/release/active baseline変更0。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a') as f:f.write(log)
    owned=evidence|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS;d.write(d.OUT/'shop-cancel-owned.json',sorted(owned))
    d.put('record-summary.json',{k:cp[k] for k in ('status','run_id','accepted_cases','actions_completion_confirmed')})


def unit(sources):
    unit_sources={p:v for p,v in sources.items() if p not in {SELF,WF,m.C}}
    reused=os.environ.get('REUSE_UNIT_RUN','')
    if reused:
        need(reused.isdecimal(),'exact previous run id')
        run=d.inputs.api('actions/runs/'+reused);listing=d.inputs.api('actions/runs/'+reused+'/artifacts?per_page=10')
        need(run['status']=='completed' and run['conclusion']=='failure' and run['path']==WF and len(listing['artifacts'])==1,'prior failed scoped run')
        meta=listing['artifacts'][0];raw=d.inputs.api('actions/artifacts/'+str(meta['id'])+'/zip',True)
        need(identity(raw)=={'size':meta['size_in_bytes'],'sha256':meta['digest'].removeprefix('sha256:')},'exact previous artifact')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            prior_unit=m.prior.old.old.load(z.read('unit.json'));text=z.read('unit.txt')
        need(prior_unit['unit_sources']==unit_sources and prior_unit['tests']==20 and prior_unit['successful'] and prior_unit['failures']==prior_unit['errors']==prior_unit['skips']==0,'unchanged successful oracle20')
        (d.PUBLIC/'unit.txt').write_bytes(text);d.put('unit.json',prior_unit)
        d.put('unit-reuse.json',{'run':d.run_summary(run),'artifact':meta,'new_unit_tests':0,'reused_unit_tests':20,'original_conclusion_preserved':'failure'})
        return
    spec=importlib.util.spec_from_file_location('new_shop_cancel_tests',ROOT/TEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    (d.PUBLIC/'unit.txt').write_text(stream.getvalue());print(stream.getvalue(),flush=True)
    d.put('unit.json',{'unit_sources':unit_sources,'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),'successful':r.wasSuccessful()})
    need(r.wasSuccessful() and r.testsRun==20 and not r.skipped,'new scoped20 tests')


def measure():
    os.chdir(ROOT);d.current();d.PUBLIC.mkdir(parents=True);need(not (ROOT/CP).exists(),'already measured; no repeat')
    old=d.read(ROOT/host.CP);need(old['actions_completion_confirmed'] and old['new_unit_tests']==49,'host baseline accepted')
    terminal=prior.terminal(old['finalize_run_id'],old['finalize_source_head'],host.WF)
    tracked=d.git('ls-files').decode().splitlines();need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')],'nested rules require review')
    protected_paths=set(old['protected_bindings'])|set(old['source_bindings'])|{host.CP,host.GUIDE,host.WF}
    protected_paths|={p for p in tracked if p.startswith(host.EVIDENCE+'/')}
    protected=d.bindings(protected_paths)
    source_paths=OWN_SOURCE|set(d.read(ROOT/prior.CP)['source_bindings'])|{prior.SELF,host.SELF,prior.RETRY_RECIPE,prior.CORRUPT_RECIPE,'scripts/pr16_research_lifecycle_v2.py'}
    sources=d.bindings(source_paths)
    d.put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':sources,'protected_bindings':protected,'prior_terminal':terminal})
    unit(sources)
    runtime,data,seed,parent,artifacts=d.restore()
    current,_=retry.apply(parent,bytes.fromhex(d.read(ROOT/prior.RETRY_RECIPE)['after']))
    recipe=d.read(ROOT/prior.CORRUPT_RECIPE);candidate,_=m.prior.parent.apply(current,bytes.fromhex(recipe['after'])[:m.prior.parent.CODE['size']])
    need(identity(candidate)==m.CANDIDATE,'same current candidate; no ARM build')
    rom=d.OUT/'shop-cancel.gba';rom.write_bytes(candidate);save,fixture=m.fixture(seed);target=d.OUT/'shop-cancel.srm';target.write_bytes(save)
    source=d.OUT/'shop-cancel.c';generated=m.generate(seed);source.write_bytes(generated);exe=d.OUT/'shop-cancel'
    d.put('inputs.json',{'candidate':identity(candidate),'fixture':fixture,'artifacts':artifacts,'generated_source':identity(generated),'rom_changes':0,'arm_compiles':0})
    command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    comp=subprocess.run(command,capture_output=True,timeout=120)
    (d.PUBLIC/'compile.stdout.txt').write_bytes(comp.stdout);(d.PUBLIC/'compile.stderr.txt').write_bytes(comp.stderr)
    d.put('compile.json',{'command':command,'returncode':comp.returncode,'executable':identity(exe.read_bytes()) if exe.exists() else None,'generated':identity(generated)})
    if comp.stderr:print(comp.stderr.decode(),flush=True)
    need(comp.returncode==0 and not comp.stderr,'strict new driver compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)];guards={}
    for method in m.prior.old.old.GUARDS:
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        need(p.returncode==1 and not p.stdout and p.stderr==m.prior.old.old.DENIED,'seven barriers '+method);guards[method]={'returncode':p.returncode,'stderr':identity(p.stderr)}
    d.put('guards.json',guards)
    try:
        p=subprocess.run(prefix+[str(rom),str(target),m.CASE],capture_output=True,timeout=300);out,err=p.stdout,p.stderr;status={'returncode':p.returncode,'timeout':False}
    except subprocess.TimeoutExpired as exc:out,err=exc.stdout or b'',exc.stderr or b'';status={'returncode':None,'timeout':True}
    (d.PUBLIC/'native.stdout.txt').write_bytes(out);(d.PUBLIC/'native.stderr.txt').write_bytes(err)
    d.put('native-process.json',dict(status,stdout=identity(out),stderr=identity(err)))
    print(out.decode('utf-8'),flush=True)
    if err:print(err.decode('utf-8'),flush=True)
    need(status['returncode']==0 and not status['timeout'] and not err,'completed clean native process')
    accepted=m.validate(out);d.put('measurement.json',accepted)
    need(d.bindings(protected)==protected and d.bindings(sources)==sources,'historical/current source preservation')
    need(identity(rom.read_bytes())==m.CANDIDATE and identity((data/'seed.srm').read_bytes())==identity(seed),'original inputs unchanged')
    directory=EVIDENCE+'/'+os.environ['GITHUB_RUN_ID'];need(not (ROOT/directory).exists(),'immutable evidence');evidence={}
    for p in sorted(d.PUBLIC.iterdir()):
        need(p.is_file() and p.suffix in ('.json','.txt'),'public text only');raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'no binary payload')
        dest=ROOT/directory/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);evidence[str(dest.relative_to(ROOT))]=identity(raw)
    d.write(ROOT/directory/'manifest.json',evidence)
    cp={'schema_version':1,'task':TASK,'status':'PASS_NATIVE_SHOP_CANCEL_PENDING_TERMINAL','source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,'accepted_cases':[m.CASE],'failed_cases':[],'new_unit_tests':20,'native_processes':1,'fresh_cores':3,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'arm_links':0,'rom_changes':0,'accepted_case_reruns':0,'source_bindings':sources,'protected_bindings':protected,'measurement':directory+'/measurement.json','manifest':directory+'/manifest.json','actions_completion_confirmed':False,'transaction_cancel_ui_accepted':True,'transaction_ui_accepted':False,'normal_new_game_accepted':False,'purchase_accepted':False,'natural_progress_accepted':False,'active_baseline_changed':False,'issue19_complete':False,'release_ready':False,'prior_terminal':terminal}
    publish(cp,set(evidence)|{directory+'/manifest.json'})


def finalize():
    os.chdir(ROOT);d.current();d.PUBLIC.mkdir(parents=True);cp=d.read(ROOT/CP);need(not cp['actions_completion_confirmed'],'already finalized')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected history')
    for path,b in cp['source_bindings'].items():
        if path!=WF:need(identity((ROOT/path).read_bytes())==b,'measured source unchanged '+path)
    cp['terminal']=prior.terminal(cp['run_id'],cp['source_head'],WF);cp.update(status='PASS_NATIVE_SHOP_CANCEL_SCOPED',actions_completion_confirmed=True,finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal-verification.json',cp['terminal']);publish(cp,set())


def guard():
    os.chdir(ROOT);cp=d.read(ROOT/CP);owned=set(d.read(d.OUT/'shop-cancel-owned.json'));need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected paths')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard();subprocess.run(['git','diff','--cached','--check'],check=True)

if __name__=='__main__':
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('measure | finalize | guard')
