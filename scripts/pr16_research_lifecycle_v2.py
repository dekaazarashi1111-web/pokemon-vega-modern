#!/usr/bin/env python3
"""初回compile失敗から再開。成功22unitは固定原本で再利用しnativeだけを新規実行。"""
from __future__ import annotations
import datetime, io, os, subprocess, sys, time, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_lifecycle_actions as d
m=d.m;need=d.need;identity=d.identity
SELF='scripts/pr16_research_lifecycle_v2.py'
WF='.github/workflows/pr16-research-lifecycle-v2-20260926.yml'
SOURCES=d.SOURCES|{SELF,WF}
OLD_RUN=36233675420
OLD_HEAD='c9fdadf38fb7f0707e39ef57204f1603da52d584'
ART=10903790971
ART_BIND={'size':8428,'sha256':'2ff2cec1dc794b47b74ec6dbb541ef1581f677cce9b0bbee0c3c27c6ea1ea835'}
OUT=d.OUT;PUBLIC=d.PUBLIC


def reuse():
    run=d.inputs.api('actions/runs/'+str(OLD_RUN));jobs=d.inputs.api('actions/runs/'+str(OLD_RUN)+'/jobs?per_page=5')
    need(run['head_sha']==OLD_HEAD and run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1,'retain failed compile run')
    need(len(jobs['jobs'])==1 and jobs['jobs'][0]['steps'][2]['conclusion']=='failure' and jobs['jobs'][0]['steps'][6]['conclusion']=='skipped','compile failure / no push')
    meta=d.inputs.api('actions/artifacts/'+str(ART));need(meta['workflow_run']['id']==OLD_RUN and meta['workflow_run']['head_sha']==OLD_HEAD and not meta['expired'],'original artifact source')
    raw=d.inputs.api('actions/artifacts/'+str(ART)+'/zip',True);need(identity(raw)==ART_BIND,'original artifact exact bytes')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(set(z.namelist())=={'bag-recipe.json','compile.json','compile.stderr.txt','compile.stdout.txt','inputs.json','invocation.json','phase0-readonly.json','save-recipe.json','unit.txt'} and len(z.infolist())==9,'pre-native artifact members')
        files={p:z.read(p) for p in z.namelist()}
    invocation=m.old.load(files['invocation.json']);need(invocation['source_head']==OLD_HEAD,'old unit source')
    for p,b in invocation['source_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'all original unit/source dependencies unchanged '+p)
    unit=files['unit.txt'];need(unit.count(b' ... ok\n')==22 and b'\nOK\n' in unit and b'FAILED' not in unit,'22 successful unit original')
    comp=m.old.load(files['compile.json']);need(comp['returncode']!=0 and comp['executable'] is None,'no native executable produced')
    need(b'"main" redefined' in files['compile.stderr.txt'] and b'redefinition' in files['compile.stderr.txt'],'rooted compile failure')
    (PUBLIC/'reused-unit.txt').write_bytes(unit);(PUBLIC/'previous-compile.stderr.txt').write_bytes(files['compile.stderr.txt'])
    d.put('reuse.json',{'run':d.run_summary(run),'jobs':jobs['jobs'],'artifact':ART,'archive':ART_BIND,'original_member_bindings':{p:identity(v) for p,v in files.items()},'original_source_bindings':invocation['source_bindings'],'new_unit_tests':0,'reused_unit_tests':22,'previous_native_processes':0,'previous_host_compiles':1})


def generate():
    old=(ROOT/d.bag.HARNESS).read_text();new=(ROOT/d.C).read_text()
    token='int main(int argc,char**argv){'
    marker='#define main research_impact_legacy_main\n#include "mgba_pr16_research_save_impact.c"\n#undef main\n'
    need(old.count(token)==1 and new.count(marker)==1,'exact generation boundaries')
    # The nested AI fixture has its own main macro. Rename only the outer C
    # declaration after its include chain, never redefine the preprocessor macro.
    generated=old.replace(token,'int research_impact_legacy_main(int argc,char**argv){')+'\n'+new.replace(marker,'')
    path=OUT/'lifecycle.c';path.write_text(generated)
    # The relative overlay header from tools needs the repository root include path.
    generated=generated.replace('#include "../overlays/research_economy_v1/research_economy_v1.h"','#include "overlays/research_economy_v1/research_economy_v1.h"')
    path.write_text(generated)
    d.put('generation.json',{'method':'ONE_OUTER_MAIN_DECLARATION_RENAME_AND_TEMPLATE_INCLUDE_EXPANSION','inputs':d.bindings({d.C,d.bag.HARNESS}),'generated':identity(path.read_bytes()),'production_changes':0,'accepted_old_runner_changes':0})
    return path


def measure():
    os.chdir(ROOT);d.current();need(not (ROOT/d.CP).exists(),'initial matrix already recorded; never rerun')
    PUBLIC.mkdir(parents=True);reuse()
    prior=d.read(ROOT/'content/modernization/pr16_research_save_impact_checkpoint.json')
    need(prior['accepted_native_cases']==18 and prior['actions_completion_confirmed'] and identity((ROOT/d.bag.SOURCE).read_bytes())==prior['canonical_source']['binding'],'preserved 18-case source/checkpoint')
    bound=d.bindings(SOURCES);protected=d.bindings(d.PROTECTED)
    d.put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':bound,'protected_bindings':protected})
    runtime,data,seed,candidate,artifacts=d.restore();d.diagnose(candidate)
    generated=generate();exe=OUT/'runner'
    cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(generated),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    p=subprocess.run(cmd,capture_output=True,timeout=120)
    (PUBLIC/'compile.stdout.txt').write_bytes(p.stdout);(PUBLIC/'compile.stderr.txt').write_bytes(p.stderr)
    d.put('compile.json',{'command':cmd,'returncode':p.returncode,'executable':identity(exe.read_bytes()) if exe.exists() else None,'source_bindings':bound,'generated_source':identity(generated.read_bytes())})
    if p.stderr:print(p.stderr.decode(),flush=True)
    need(p.returncode==0 and not p.stderr,'strict generated host compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    guards={}
    for method in m.old.GUARDS:
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        (PUBLIC/(method+'.stdout.txt')).write_bytes(p.stdout);(PUBLIC/(method+'.stderr.txt')).write_bytes(p.stderr)
        guards[method]={'returncode':p.returncode,'stdout':identity(p.stdout),'stderr':identity(p.stderr)}
        need(p.returncode==1 and not p.stdout and p.stderr==m.old.DENIED,'new executable host guard '+method)
    d.put('guards.json',guards)
    results={};failures={};processes={}
    for case in m.CASES:
        target=OUT/(case+'.srm');target.write_bytes(seed);start=time.monotonic()
        try:
            p=subprocess.run(prefix+[str(data/'candidate.gba'),str(target),case],capture_output=True,timeout=180)
            status={'returncode':p.returncode,'timeout':False};out,err=p.stdout,p.stderr
        except subprocess.TimeoutExpired as exc:
            status={'returncode':None,'timeout':True};out,err=exc.stdout or b'',exc.stderr or b''
        (PUBLIC/(case+'.stdout.txt')).write_bytes(out);(PUBLIC/(case+'.stderr.txt')).write_bytes(err)
        status.update(elapsed_seconds=round(time.monotonic()-start,3),stdout=identity(out),stderr=identity(err),private_save=identity(target.read_bytes()))
        processes[case]=status
        try:
            need(status['returncode']==0 and not status['timeout'] and not err,'clean successful process')
            results[case]=m.validate(out,case)
        except (ValueError,KeyError,TypeError) as exc:failures[case]={'exception_type':type(exc).__name__,'reason':str(exc)}
        print(case,'PASS' if case in results else 'FAIL',err.decode(),flush=True)
    need(d.bindings(SOURCES)==bound and d.bindings(d.PROTECTED)==protected,'source/protected unchanged')
    need(identity((data/'seed.srm').read_bytes())==identity(seed) and identity((data/'candidate.gba').read_bytes())==d.bag.CANDIDATE,'read-only input bytes')
    d.put('measurement.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':d.bag.CANDIDATE,'artifacts':artifacts,'cases':processes,'accepted':results,'failures':failures,'new_unit_tests':0,'reused_unit_tests':22,'native_processes':5,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0})


def publish(cp,scope,owned):
    from pr16_learnset_compact_record import publish_resume
    d.write(ROOT/d.CP,cp)
    goal=scope+' 次は失敗原本の原因、または未検証のphase0実失敗/V1 load adapterを進める。成功済みケースと旧18境界/BP/P08/特殊野生を再実行しない。通常新規ゲーム/取引UI、全catalog、map3/19除外130行、Issue19全体/releaseは未完。'
    state=d.read(ROOT/d.STATE)
    state['research_save_lifecycle']={'path':d.CP,'status':cp['status'],'candidate':cp['candidate'],'accepted_cases':cp['accepted_cases'],'run_id':cp['run_id'],'actions_completion_confirmed':cp['actions_completion_confirmed']}
    state['bp']['current_stop']=scope;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_LIFECYCLE_NEXT',goal_ja=goal,read_paths=[d.GUIDE,d.CP,SELF,d.C,'scripts/pr16_research_lifecycle.py',d.bag.SOURCE,d.save.CONFIG],stop_rule_ja='固定候補/source/原本hashを保持。未実行を成功へ昇格しない。既受入nativeとunitを再実行しない。merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='研究保存lifecycle記録source。自己commitはgit log参照。正式BP/P08の履歴を置換しない。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':cp.get('terminal_conclusion')}], 'reason_ja':'限定工程のみ。全CI成功を主張しない。元compile failure36233675420を保持。'}
    guide='# PR16 研究保存lifecycle\n\n'+scope+'\n\n'+goal+'\n\n## 方法\n\n固定候補4aee03e8に空/消去済み/V1研究ledger RAM fixtureを投入し、無効activity入口から初期化/移行だけを通す。成功時phase0実Flash保存1回、破損V1拒否時0回。独立coreで通常Continueを2回行い、全owner/Bag/手持ち/ledger/保存counterを照合する。通常new-gameやV1保存の通常load、phase0失敗ではない。\n\n既存runner内のmainマクロと衝突した初回run36233675420はnative0・compile1のfailure。22unitの原本と全依存source hashを再利用。生成時は旧runnerの外側main宣言だけ改名し、template includeを展開する。旧runner/production/候補は不変。\n\n## 記録\n\nsource `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'`。受入: '+', '.join(cp['accepted_cases'])+'。失敗: '+', '.join(cp['failed_cases'])+'。終端確認: '+str(cp['actions_completion_confirmed'])+'。\n'
    (ROOT/d.GUIDE).write_text(guide)
    for p in SOURCES|{d.CP,d.GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {d.TASK}\n- Version: research-lifecycle-v2\n- Status: '+cp['status']+'（限定scope、後続未完）\n- Summary: '+scope+'\n- Files changed: 専用runner/validator/生成build/Actions、原本hash/UTF8証拠/checkpoint、固定引継ぎMD/JSON、guide、両ログ。\n- Verify: 初回22unit原本を再利用、今回新unit0。初回compile失敗1/native0、今回host compile1/native5/guard7/ARM0。既受入18境界native再実行0。resume check/task graph/限定final index guard後にcommit。\n- Commit: 同branch非force push。source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log参照。\n- Network: 固定GitHub artifactのみ。ROM/save非tracked、保全path不変。通常UI/new-game/V1 load/phase0失敗は未受入。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(log)
    d.write(OUT/'owned.json',sorted(owned|{d.CP,d.GUIDE,d.STATE,d.DOC}|d.LOGS))


def record():
    os.chdir(ROOT);d.current();need(not (ROOT/d.CP).exists(),'do not overwrite initial record')
    inv=d.read(PUBLIC/'invocation.json');v=d.read(PUBLIC/'measurement.json')
    need(d.bindings(SOURCES)==inv['source_bindings'] and d.bindings(d.PROTECTED)==inv['protected_bindings'],'measured source bindings')
    directory=d.BASE+'/'+os.environ['GITHUB_RUN_ID'];need(not (ROOT/directory).exists(),'immutable original evidence')
    manifest={}
    for p in sorted(PUBLIC.iterdir()):
        raw=p.read_bytes();raw.decode('utf-8');need(b'\0' not in raw and p.suffix in ('.txt','.json'),'UTF8 evidence only')
        target=ROOT/directory/p.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);manifest[str(target.relative_to(ROOT))]=identity(raw)
    mp=directory+'/manifest.json';d.write(ROOT/mp,manifest)
    cp={'schema_version':1,'task':d.TASK,'status':'PASS_INITIAL_LIFECYCLE_5_SCOPED' if not v['failures'] else 'PARTIAL_INITIAL_LIFECYCLE','candidate':d.bag.CANDIDATE,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'accepted_cases':sorted(v['accepted']),'failed_cases':sorted(v['failures']),'accepted_native_cases':len(v['accepted']),'measurement':directory+'/measurement.json','manifest':mp,'source_bindings':inv['source_bindings'],'protected_bindings':inv['protected_bindings'],
        'new_unit_tests':0,'reused_unit_tests':22,'native_processes':5,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0,'actions_completion_confirmed':False,
        'normal_new_game_or_transaction_ui_accepted':False,'v1_load_adapter_accepted':False,'phase0_failure_accepted':False,'release_ready':False,'active_baseline_changed':False,'issue19_complete':False,'previous_compile_failure':OLD_RUN}
    publish(cp,'研究保存の初期化/V1 RAM移行: '+str(len(v['accepted']))+'/5件の原本を記録。',set(manifest)|{mp})
    print(cp['status'],cp['accepted_cases'],cp['failed_cases'])


if __name__=='__main__':
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:d.guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(d.read(OUT/'owned.json')))
    else:raise SystemExit('usage: measure|record|guard|paths')
