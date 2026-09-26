#!/usr/bin/env python3
"""未受入の通常load phase0だけを計測し、固定引継ぎと両ログへ記録。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_lifecycle_v2 as base
import pr16_research_phase0_load as m
import pr16_research_retry as retry
d=base.d;need=m.need;identity=m.identity
TASK='USER-20260926-RESEARCH-PHASE0-LOAD'
SELF='scripts/pr16_research_phase0_load_actions.py'
MODEL='scripts/pr16_research_phase0_load.py'
TEST='tests/test_pr16_research_phase0_load.py'
WF='.github/workflows/pr16-research-phase0-load-20260926.yml'
CP='content/modernization/pr16_research_phase0_load_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_PHASE0_LOAD_JA.md'
EVIDENCE='content/modernization/pr16_research_phase0_load_evidence'
PREVIOUS='content/modernization/pr16_research_v1_corrupt_load_checkpoint.json'
OWN_SOURCE={SELF,MODEL,TEST,WF,m.C}
RETRY_RECIPE='content/modernization/pr16_research_retry_recipe.json'
CORRUPT_RECIPE='content/modernization/pr16_research_v1_corrupt_load_recipe.json'


def terminal(runid,head,path):
    run=d.inputs.api('actions/runs/'+str(runid))
    jobs=d.inputs.api('actions/runs/'+str(runid)+'/jobs?per_page=10')
    need(run['head_sha']==head and run['path']==path and run['run_attempt']==1 and run['status']=='completed' and run['conclusion']=='success','exact successful terminal')
    need(len(jobs['jobs'])==1 and jobs.get('total_count',1)==1,'one scoped job')
    job=jobs['jobs'][0]
    need(job['status']=='completed' and job['conclusion']=='success' and all(s['conclusion']=='success' for s in job['steps']),'all steps including commit push upload completed')
    listing=d.inputs.api('actions/runs/'+str(runid)+'/artifacts?per_page=100')
    need(listing['total_count']==len(listing['artifacts'])==1,'one output artifact')
    artifacts=[{k:a[k] for k in ('id','name','size_in_bytes','digest','workflow_run')} for a in listing['artifacts']]
    return {'run':d.run_summary(run),'jobs':jobs['jobs'],'artifacts':artifacts,'native_reruns':0,'unit_reruns':0,'compiles':0}


def measure():
    os.chdir(ROOT);d.current();need(not (ROOT/CP).exists(),'record exists; do not repeat completed cases')
    d.PUBLIC.mkdir(parents=True)
    old=d.read(ROOT/PREVIOUS)
    need(old['actions_completion_confirmed'] and old['candidate']==m.CANDIDATE and len(old['accepted_cases'])==3 and not old['failed_cases'],'previous scoped load acceptance')
    prior_terminal=terminal(old['finalize_run_id'],old['finalize_source_head'],'.github/workflows/pr16-research-v1-corrupt-20260926.yml')
    tracked=d.git('ls-files').decode().splitlines()
    need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')],'nested rules need explicit review')
    protected_paths=set(old['protected_bindings'])|set(old['source_bindings'])|{PREVIOUS,'docs/PR16_RESEARCH_V1_CORRUPT_LOAD_JA.md',RETRY_RECIPE,CORRUPT_RECIPE,m.SOURCE}
    protected_paths|={p for p in tracked if p.startswith(('content/modernization/pr16_research_retry_evidence/','content/modernization/pr16_research_v1_load_root_evidence/'))}
    protected=d.bindings(protected_paths)
    # The entire generated runner dependency graph is fixed, not just its appended driver.
    sources=OWN_SOURCE|set(d.read(ROOT/'content/modernization/pr16_research_v1_corrupt_load_native.json')['source_bindings'])|{m.SOURCE,RETRY_RECIPE,CORRUPT_RECIPE}
    sources|={p for p in ('tools/mgba_qol_production_smoke.c','tools/mgba_battle_core_smoke.c','tools/mgba_ai_fixture_runner.c') if (ROOT/p).exists()}
    bound=d.bindings(sources)
    d.put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':bound,'protected_bindings':protected,'prior_terminal':prior_terminal,'accepted_case_reruns':0,'arm_compiles':0})
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],capture_output=True,timeout=120)
    unitraw=unit.stdout+unit.stderr;(d.PUBLIC/'unit.txt').write_bytes(unitraw)
    need(unit.returncode==0 and unitraw.count(b' ... ok\n')==43 and b'Ran 43 tests' in unitraw and unitraw.endswith(b'\nOK\n'),'43 new tests, canonical adapter compile included')
    runtime,data,seed,parent,artifacts=d.restore()
    saved_parent=identity((data/'candidate.gba').read_bytes())
    retry_candidate,_=retry.apply(parent,bytes.fromhex(d.read(ROOT/RETRY_RECIPE)['after']))
    recipe=d.read(ROOT/CORRUPT_RECIPE)
    candidate,_=m.parent.apply(retry_candidate,bytes.fromhex(recipe['after'])[:m.parent.CODE['size']])
    need(identity(candidate)==m.CANDIDATE,'same current candidate restored without compilation')
    rom=d.OUT/'phase0-load-candidate.gba';rom.write_bytes(candidate)
    generated=m.generate(seed);source=d.OUT/'phase0-load.c';source.write_bytes(generated);exe=d.OUT/'phase0-load-runner'
    d.put('inputs.json',{'candidate':identity(candidate),'seed':identity(seed),'artifacts':artifacts,'source_bindings':bound,'generated_source':identity(generated),'rom_changes':0,'arm_compiles':0,'arm_links':0})
    command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    comp=subprocess.run(command,capture_output=True,timeout=120)
    (d.PUBLIC/'compile.stdout.txt').write_bytes(comp.stdout);(d.PUBLIC/'compile.stderr.txt').write_bytes(comp.stderr)
    d.put('compile.json',{'command':command,'returncode':comp.returncode,'compiler':subprocess.check_output(['cc','--version']).decode(),'generated':identity(generated),'executable':identity(exe.read_bytes()) if exe.exists() else None})
    if comp.stderr:print(comp.stderr.decode(),flush=True)
    need(comp.returncode==0 and not comp.stderr,'strict new native driver compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    guards={}
    for method in m.old.old.GUARDS:
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        guards[method]={'returncode':p.returncode,'stdout':identity(p.stdout),'stderr':identity(p.stderr)}
        need(p.returncode==1 and not p.stdout and p.stderr==m.old.old.DENIED,'new runner write barrier '+method)
    d.put('guards.json',guards)
    baseline=d.read(ROOT/d.read(ROOT/'content/modernization/pr16_research_retry_checkpoint.json')['measurement'])['accepted']['retry-zero']['observations'][0]
    results={};failures={};processes={};fixtures={}
    for case in m.CASES:
        raw,receipt=m.fixture(seed,case);fixtures[case]=receipt;target=d.OUT/(case+'.srm');target.write_bytes(raw)
        started=time.monotonic()
        try:
            p=subprocess.run(prefix+[str(rom),str(target),case],capture_output=True,timeout=300)
            status={'returncode':p.returncode,'timeout':False};out,err=p.stdout,p.stderr
        except subprocess.TimeoutExpired as exc:
            status={'returncode':None,'timeout':True};out,err=exc.stdout or b'',exc.stderr or b''
        (d.PUBLIC/(case+'.stdout.txt')).write_bytes(out);(d.PUBLIC/(case+'.stderr.txt')).write_bytes(err)
        status.update(elapsed_seconds=round(time.monotonic()-started,3),stdout=identity(out),stderr=identity(err),private_save_after=identity(target.read_bytes()))
        processes[case]=status
        try:
            need(status['returncode']==0 and not status['timeout'] and not err,'clean completed native process')
            results[case]=m.validate(out,case,raw,baseline)
        except (ValueError,KeyError,TypeError) as exc:failures[case]={'exception_type':type(exc).__name__,'reason':str(exc)}
        print(case,'PASS' if case in results else 'FAIL',flush=True)
        if err:print(err.decode('utf-8'),flush=True)
    need(d.bindings(bound)==bound and d.bindings(protected)==protected,'all measured sources and historical evidence unchanged')
    need(identity((data/'seed.srm').read_bytes())==identity(seed) and identity((data/'candidate.gba').read_bytes())==saved_parent and identity(rom.read_bytes())==m.CANDIDATE,'input preservation and unchanged exact candidate')
    d.put('fixtures.json',fixtures)
    measurement={'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,'cases':processes,'accepted':results,'failures':failures,'new_unit_tests':43,'native_processes':len(processes),'fresh_cores_accepted':sum(v['fresh_cores'] for v in results.values()),'guard_processes':7,'host_compiles':2,'arm_compiles':0,'arm_links':0,'accepted_case_reruns':0,'rom_changes':0}
    d.put('measurement.json',measurement)
    # Failure originals are saved to the artifact; a failed native run is never published as accepted.
    need(not failures,'native failures preserved; do not promote or rerun successful cases')
    directory=EVIDENCE+'/'+os.environ['GITHUB_RUN_ID'];need(not (ROOT/directory).exists(),'immutable evidence directory')
    evidence={}
    for p in sorted(d.PUBLIC.iterdir()):
        need(p.is_file() and p.suffix in ('.json','.txt'),'bounded public text only')
        raw=p.read_bytes();raw.decode('utf-8');need(b'\0' not in raw,'no binary payload')
        target=ROOT/directory/p.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);evidence[str(target.relative_to(ROOT))]=identity(raw)
    d.write(ROOT/directory/'manifest.json',evidence)
    cp={'schema_version':1,'task':TASK,'status':'PASS_PHASE0_LOAD_PENDING_TERMINAL','source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,'accepted_cases':list(results),'failed_cases':[],'accepted_native_cases':2,'fresh_cores':8,'measurement':directory+'/measurement.json','manifest':directory+'/manifest.json','source_bindings':bound,'protected_bindings':protected,'prior_terminal':prior_terminal,'new_unit_tests':43,'native_processes':2,'guard_processes':7,'host_compiles':2,'arm_compiles':0,'arm_links':0,'accepted_case_reruns':0,'rom_changes':0,'availability_fixture_words_per_process':1,'availability_fixture_byte_writes_per_process':4,'guarded_host_writes':0,'ram_ledger_fixture_writes':0,'register_fixture_writes':0,'phase0_load_failure_accepted':True,'cold_recovery_accepted':True,'same_core_menu_retry_accepted':False,'actions_completion_confirmed':False,'physical_flash_fault_accepted':False,'normal_new_game_accepted':False,'transaction_ui_accepted':False,'active_baseline_changed':False,'issue19_complete':False,'release_ready':False}
    publish(cp,set(evidence)|{directory+'/manifest.json'})


def publish(cp,evidence):
    from pr16_learnset_compact_record import publish_resume
    summary='通常load内phase0の保存不可2経路（V1移行/未確定稼得回復）を受入。原本全2048byte・全Flashを保持して拒否、通常cold Continueで1回保存し2回の後続Continueで完全一致。'
    goal='次は通常new-game/取引UIの未受入境界を限定実装/検証する。phase0 load 2件/43unit、通常V1 3件/旧40unit、7retry、BP/P08/特殊野生は変更影響なく再実行しない。'
    if not cp['actions_completion_confirmed']:goal='まず本runの終端・push/uploadを照合する。'+goal
    d.write(ROOT/CP,cp)
    guide='# PR16 通常load内phase0保存不可とcold回復\n\n'+summary+'\n\n'+goal+'\n\n## 境界と受入\n\n通常起動の先行rootとContinue loadを分離。Research→Mirage→QOLの既存本番delegateを通し、phase0入口の可用性word `0x03005044` だけを1→0にする。停止fixture区間で4byteを書き、7 API barrierを即時再装着する。全EWRAM、当該word以外のIWRAM、16レジスタ/CPSR、128KiB Flashを前後比較。ledger/owner/PC/戻り値の注入なし。guard中のhost書込0であり、fixture書込0とは主張しない。\n\nV1移行とV2 prepared fishing稼得5点の2経路。実native return255、load result0、last_result13、counter2、blocked1を確認。全2048byteと128KiB Flashは原本どおり。保存可用性をhostで戻さずfresh通常起動で復帰し、counter2→3、保存1回、期待ledger全byte一致。稼得はbalance/lifetime/daily各5、pending全解除、二重加算0。他sector31 owner/Bag/party保持。実fieldと後続fresh Continue2回で全ledger・counter・owner・Bag・party一致。\n\n## 計測と保存\n\n候補 `'+m.CANDIDATE['sha256']+'` を保存済みrecipeから復元。ROM変更/ARM compile/link0、旧受入再実行0。新native2process/8fresh cores、7guard拒否probe、host compile2（新runner/単体canonical C）。Actionsで新unit43PASS。開発時ローカルpreflightも同じ43件PASS（受入前の開発検査）。ソース本体修正は不要だった。証拠manifestとsource/protected hashはcheckpoint参照。\n\n## 限界\n\nこの受入は可用性fixtureであり物理Flash故障ではない。同一coreの拒否後メニューretry、通常new-game/取引UI全体、全catalog、Issue19、releaseは未受入。候補/原本/active baseline/旧Wikiは不変、merge/releaseなし。一般CIのaction_requiredを全CI成功に読み替えない。\n\n## Actions\n\nsource `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'` / 終端確認 `'+str(cp['actions_completion_confirmed'])+'`。'+(' finalize run `'+str(cp['finalize_run_id'])+'`。' if 'finalize_run_id' in cp else '')+'\n'
    (ROOT/GUIDE).write_text(guide)
    state=d.read(ROOT/d.STATE)
    state['research_phase0_load']={k:cp[k] for k in ('status','candidate','accepted_cases','failed_cases','run_id','actions_completion_confirmed')};state['research_phase0_load']['path']=CP
    state['bp']['current_stop']=summary;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_NORMAL_NEW_GAME_TRANSACTION_UI_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,MODEL,SELF,m.C,PREVIOUS,'overlays/research_economy_v1/research_economy_v1.c','overlays/qol_production/qol_production.c'],stop_rule_ja='候補5d1fc9c4と受入済み2load/旧3loadを保持。未受入UIだけへ進み、merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='通常load phase0境界の記録source。自己SHAはgit log参照。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':'success' if cp['actions_completion_confirmed'] else None}],'reason_ja':'限定phase0 load受入。一般source-validationのaction_requiredを全CI成功にしない。'}
    for path in OWN_SOURCE|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 通常load内phase0保存不可とcold回復\n- Version: research-phase0-load-v1\n- Status: DONE（限定2境界、全UIは未受入）\n- Summary: '+summary+'\n- Files changed: 新runner/model/43tests/Actions、証拠/checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 新unit43PASS（canonical C compile1）、native2process/8cores、runner compile1、7guard拒否PASS。ローカル開発preflight43PASS。通常load拒否・回復・2回冪等Continue。ROM変更/ARM compile/link/旧受入再実行0。fixtureは可用性word1件4byte/各process、guarded host書込/ledger/PC/戻り値注入0。終端確認='+str(cp['actions_completion_confirmed'])+'、記録finalizeはnative/unit/compile0。resume/task graph/scoped final-index guard/diff-checkを同runで検査。全体歴史guard成功は主張しない。\n- Commit: 同branch非force。source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log。\n- Network: GitHub固定artifactとActions API。私有payload新規tracked0、merge/release/active baseline変更0。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a') as f:f.write(log)
    owned=evidence|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS
    d.write(d.OUT/'phase0-owned.json',sorted(owned));d.put('record-summary.json',{k:cp[k] for k in ('status','candidate','accepted_cases','failed_cases','actions_completion_confirmed')})


def finalize():
    os.chdir(ROOT);d.current();d.PUBLIC.mkdir(parents=True);cp=d.read(ROOT/CP)
    need(not cp['actions_completion_confirmed'],'already finalized; do not repeat')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'historical evidence preserved')
    for path,binding in cp['source_bindings'].items():
        if path!=WF:need(identity((ROOT/path).read_bytes())==binding,'measured source unchanged '+path)
    cp['terminal']=terminal(cp['run_id'],cp['source_head'],WF)
    cp.update(status='PASS_PHASE0_LOAD_SCOPED',actions_completion_confirmed=True,finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal-verification.json',cp['terminal']);publish(cp,set())


def guard():
    os.chdir(ROOT);cp=d.read(ROOT/CP);owned=set(d.read(d.OUT/'phase0-owned.json'))
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'all protected paths unchanged')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('measure | finalize | guard')
