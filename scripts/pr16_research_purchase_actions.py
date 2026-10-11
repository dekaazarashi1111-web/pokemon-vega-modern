#!/usr/bin/env python3
"""未受入の実選択/購入/不足だけを実行し、失敗も別原本として保存する。"""
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
import pr16_research_purchase as m
import pr16_research_retry as retry
import pr16_research_v1_corrupt_load as corrupt
d=previous.d;need=d.need;identity=d.identity
TASK='USER-20260926-RESEARCH-PURCHASE'
SELF='scripts/pr16_research_purchase_actions.py'
MODEL='scripts/pr16_research_purchase.py'
TEST='tests/test_pr16_research_purchase.py'
WF='.github/workflows/pr16-research-purchase-20260926.yml'
CP='content/modernization/pr16_research_purchase_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_PURCHASE_JA.md'
EVIDENCE='content/modernization/pr16_research_purchase_evidence'
OWN_SOURCE={SELF,MODEL,TEST,WF,m.C}


def unit(sources,old):
    deps={p:b for p,b in sources.items() if p not in {SELF,WF,m.C}}
    if old:
        unit_path=str(Path(old['manifest']).parent/'unit.json');v=d.read(ROOT/unit_path)
        need(v['dependencies']==deps and v['tests']==42 and v['successful'] and v['errors']==v['failures']==v['skips']==0,'reuse only exact successful42')
        d.put('unit.json',v);(d.PUBLIC/'unit.txt').write_bytes((ROOT/Path(unit_path).with_name('unit.txt')).read_bytes())
        d.put('unit-reuse.json',{'run_id':old['run_id'],'new_unit_tests':0,'reused_unit_tests':42,'native_success_claimed':False})
        return 0
    spec=importlib.util.spec_from_file_location('new_purchase_tests',ROOT/TEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    (d.PUBLIC/'unit.txt').write_text(stream.getvalue());print(stream.getvalue(),flush=True)
    d.put('unit.json',{'dependencies':deps,'tests':r.testsRun,'errors':len(r.errors),'failures':len(r.failures),'skips':len(r.skipped),'successful':r.wasSuccessful()})
    need(r.wasSuccessful() and r.testsRun==42 and not r.skipped,'new42 oracle tests')
    return 42


def publish(cp,evidence,mode):
    from pr16_learnset_compact_record import publish_resume
    ok=bool(cp['accepted_cases'])
    summary=('実Researchショップの行選択/確認拒否、10RP購入、残高不足拒否と取引直後の独立Continueを受入。通常Saveと続く独立Continue2回も保持。進行/10RP/warpはfixture。' if ok else '実Researchショップ購入の新driverは未受入。停止原本を保存し、成功済みoracle42は同一依存なら再利用する。')
    goal=('次は通常new-game→初回Save/Continue。購入/不足native1件・42oracle・旧取消/host49/phase0/V1/retryは影響なしに再実行しない。' if ok else '専用checkpointの失敗原本と実停止を先に読む。最小原因修正後、未完nativeだけを再開し、受入済み取消や旧host/ARMは再実行しない。')
    if ok and not cp['actions_completion_confirmed']:goal='まず本runの終端・非force push・uploadを照合する。'+goal
    d.write(ROOT/CP,cp)
    guide='# PR16 実Researchショップ選択・購入・残高不足\n\n'+summary+'\n\n## 境界と限定\n\n現候補の実背景scriptと全23行catalog368byteのhashを固定し、catalog0/item4/価格10RP/数量5を実ROMから照合する。初期進行と10RPはprivate seedのledger限定fixture、停止状態でstock warp4呼出とfield callback1wordのみ設定。以後7APIのwrite barrier下で通常キー入力だけを使う。観測中にshop dispatch/購入結果/PC/在庫/残高を書き込まない。\n\n実行順は行選択→購入確認のB拒否→再選択→A購入→手動Saveより前の独立Continue→再選択→残高0で不足拒否→通常Start Save→独立Continue2回。購入時の取引保存2回と手動Save1回を区別する。拒否/不足は128KiB Flash全byte・counter不変、購入は対象item+5以外の全Bag5pocket/party600byte不変。全ledger2048byteをminute/checksum以外対照し、全owner64byteの残高10→0/nextTransaction1→2/claim/pendingを閉じて検証する。\n\nこれはcatalog0の限定受入であり、全catalog価格/日本語画面の目視監査・通常new-game・実RP稼得・自然進行からの到達を証明しない。ROM変更/ARM compile/link/旧受入再実行0。旧取消・旧失敗原本・P08・baselineを変更しない。\n\n## 原本\n\nrun `'+str(cp['run_id'])+'` / source `'+cp['source_head']+'`。status `'+cp['status']+'`、終端確認 `'+str(cp['actions_completion_confirmed'])+'`。成功 '+str(cp['accepted_cases'])+'、失敗 '+str(cp['failed_cases'])+'。manifest `'+cp['manifest']+'`。過去失敗は `attempt_history` に別identityで保持。一般CIのaction_requiredを全CI成功へ読み替えない。\n\n## 次工程\n\n'+goal+'\n'
    (ROOT/GUIDE).write_text(guide)
    state=d.read(ROOT/d.STATE)
    state['research_purchase']={k:cp[k] for k in ('status','candidate','accepted_cases','failed_cases','run_id','actions_completion_confirmed')};state['research_purchase']['path']=CP
    state['bp']['current_stop']=summary;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_NORMAL_NEW_GAME_NEXT' if ok else 'RESEARCH_PURCHASE_NATIVE_REPAIR',goal_ja=goal,read_paths=[GUIDE,CP,MODEL,SELF,m.C,previous.CP,'overlays/research_economy_v1/research_economy_v1.c','overlays/qol_production/qol_production.c'],stop_rule_ja='catalog0の実購入だけの受入を全catalog/自然進行/new-gameへ拡張しない。未完nativeを先に読む。受入反復/merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='実ショップ購入の実行/終端記録source。自己SHAはgit log。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':'success' if cp['actions_completion_confirmed'] else None}],'reason_ja':'scoped原本だけを判定。記録中runの最終結論を自己確定しない。一般CIは別状態。'}
    for path in OWN_SOURCE|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 実Research購入・残高不足の保存境界\n- Version: research-purchase-{mode}-v1\n- Status: '+('DONE（限定受入、通常new-game未完）' if ok else 'STOPPED（新native失敗原本保存）')+'\n- Summary: '+summary+'\n- Files changed: '+', '.join(sorted(OWN_SOURCE|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))+' と限定UTF8証拠。\n- Verify: ローカル新oracle42PASS。今回Actions新unit='+str(cp['new_unit_tests'])+'、native process='+str(cp['native_processes'])+'、成功時fresh cores=4、guard7、host compile1。ROM変更/ARM compile/link/旧受入再実行0。失敗='+str(cp['failed_cases'])+'。finalizeはunit/native/compile再実行0。後続resume/task graph/scoped final-index/diff gate後にcommit。全体歴史private guard成功は主張しない。\n- Commit: source='+os.environ['GITHUB_SHA']+'、同branch非force。自己SHAはgit log。\n- Network: GitHub固定artifact/PR/Actions照合。元ROM/saveは非tracked。受入済み原本・baseline保全。merge/release0。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a') as f:f.write(log)
    d.write(d.OUT/'purchase-owned.json',sorted(evidence|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))
    d.put('record-summary.json',{k:cp[k] for k in ('status','run_id','accepted_cases','failed_cases','actions_completion_confirmed')})


def measure():
    os.chdir(ROOT);d.current();d.PUBLIC.mkdir(parents=True)
    old=d.read(ROOT/CP) if (ROOT/CP).exists() else None
    if old:need(old['failed_cases'] and not old['accepted_cases'],'do not repeat accepted native')
    previous_cp=d.read(ROOT/previous.CP);need(previous_cp['actions_completion_confirmed'] and previous_cp['candidate']==m.CANDIDATE,'cancel baseline complete')
    terminal=previous.prior.terminal(previous_cp['finalize_run_id'],previous_cp['finalize_source_head'],previous.WF)
    tracked=d.git('ls-files').decode().splitlines();need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')],'nested agent rules need review')
    paths=set(previous_cp['protected_bindings'])|set(previous_cp['source_bindings'])|{previous.CP,previous.GUIDE,previous.WF}
    paths|={p for p in tracked if p.startswith(previous.EVIDENCE+'/') or p.startswith(EVIDENCE+'/')}
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
    at=m.CATALOG['address']-0x08000000;need(identity(candidate[at:at+m.CATALOG['size']])=={k:m.CATALOG[k] for k in ('size','sha256')},'actual full catalog')
    rom=d.OUT/'purchase.gba';rom.write_bytes(candidate);save,fixture=m.fixture(seed);target=d.OUT/'purchase.srm';target.write_bytes(save)
    generated=m.generate(seed);source=d.OUT/'purchase.c';source.write_bytes(generated);exe=d.OUT/'purchase'
    d.put('inputs.json',{'candidate':identity(candidate),'fixture':fixture,'catalog':m.CATALOG,'artifacts':artifacts,'generated_source':identity(generated),'rom_changes':0,'arm_compiles':0})
    command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    comp=subprocess.run(command,capture_output=True,timeout=120)
    (d.PUBLIC/'compile.stdout.txt').write_bytes(comp.stdout);(d.PUBLIC/'compile.stderr.txt').write_bytes(comp.stderr)
    d.put('compile.json',{'command':command,'returncode':comp.returncode,'executable':identity(exe.read_bytes()) if exe.exists() else None,'generated':identity(generated)})
    if comp.stderr:print(comp.stderr.decode(),flush=True)
    need(comp.returncode==0 and not comp.stderr,'strict driver compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)];guards={}
    for method in m.prior.prior.old.old.GUARDS:
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        need(p.returncode==1 and not p.stdout and p.stderr==m.prior.prior.old.old.DENIED,'seven barriers '+method);guards[method]={'returncode':p.returncode,'stderr':identity(p.stderr)}
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
        need(status['returncode']==0 and not status['timeout'] and not err,'completed clean native process');accepted=m.validate(out,save)
    except (ValueError,KeyError,TypeError) as exc:failure={'exception_type':type(exc).__name__,'reason':str(exc)}
    d.put('measurement.json',{'accepted':accepted,'failure':failure,'candidate':m.CANDIDATE,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID'])})
    need(d.bindings(protected)==protected and d.bindings(sources)==sources,'historical/source preservation')
    need(identity(rom.read_bytes())==m.CANDIDATE and identity((data/'seed.srm').read_bytes())==identity(seed),'read-only originals')
    directory=EVIDENCE+'/'+os.environ['GITHUB_RUN_ID'];need(not (ROOT/directory).exists(),'immutable evidence');evidence={}
    for p in sorted(d.PUBLIC.iterdir()):
        need(p.is_file() and p.suffix in ('.json','.txt'),'public text only');raw=p.read_bytes();raw.decode();need(b'\0' not in raw and len(raw)<=2000000,'bounded text only')
        dest=ROOT/directory/p.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);evidence[str(dest.relative_to(ROOT))]=identity(raw)
    d.write(ROOT/directory/'manifest.json',evidence)
    cp={'schema_version':1,'task':TASK,'status':'PASS_NATIVE_PURCHASE_PENDING_TERMINAL' if accepted else 'FAIL_NATIVE_PURCHASE_RECORDED','source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,'accepted_cases':[m.CASE] if accepted else [],'failed_cases':[] if accepted else [m.CASE],'new_unit_tests':units,'native_processes':1,'fresh_cores':4 if accepted else None,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'arm_links':0,'rom_changes':0,'accepted_case_reruns':0,'source_bindings':sources,'protected_bindings':protected,'measurement':directory+'/measurement.json','manifest':directory+'/manifest.json','actions_completion_confirmed':False,'purchase_accepted':bool(accepted),'normal_new_game_accepted':False,'natural_progress_accepted':False,'active_baseline_changed':False,'issue19_complete':False,'release_ready':False,'prior_terminal':terminal,'attempt_history':history}
    publish(cp,set(evidence)|{directory+'/manifest.json'},'measure')


def finalize():
    os.chdir(ROOT);d.current();d.PUBLIC.mkdir(parents=True);cp=d.read(ROOT/CP)
    need(cp['accepted_cases']==[m.CASE] and not cp['failed_cases'] and not cp['actions_completion_confirmed'],'finalize accepted exactly once')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected history')
    for p,b in cp['source_bindings'].items():
        if p!=WF:need(identity((ROOT/p).read_bytes())==b,'measured source unchanged '+p)
    cp['terminal']=previous.prior.terminal(cp['run_id'],cp['source_head'],WF)
    cp.update(status='PASS_NATIVE_PURCHASE_SCOPED',actions_completion_confirmed=True,finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal-verification.json',cp['terminal']);publish(cp,set(),'finalize')


def guard():
    os.chdir(ROOT);cp=d.read(ROOT/CP);owned=set(d.read(d.OUT/'purchase-owned.json'))
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
