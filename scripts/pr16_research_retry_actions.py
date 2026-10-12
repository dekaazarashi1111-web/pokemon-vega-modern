#!/usr/bin/env python3
"""再試行の限定実装/検証/記録。終端確認時は実測を一切再実行しない。"""
from __future__ import annotations
import datetime
import difflib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_retry as m
import pr16_research_lifecycle_v2 as base
from pr16_learnset_compact_record import publish_resume
d=base.d;need=m.need;identity=m.identity
TASK='USER-20260926-RESEARCH-RETRY'
SELF='scripts/pr16_research_retry_actions.py'
WF='.github/workflows/pr16-research-retry-20260926.yml'
C='tools/mgba_pr16_research_retry.c'
TEST='tests/test_pr16_research_retry.py'
DIAG='content/modernization/pr16_research_retry_local_diagnostic.json'
CP='content/modernization/pr16_research_retry_checkpoint.json'
RECIPE='content/modernization/pr16_research_retry_recipe.json'
GUIDE='docs/PR16_RESEARCH_RETRY_JA.md'
EVIDENCE='content/modernization/pr16_research_retry_evidence'
OUT=d.OUT;PUBLIC=d.PUBLIC
SOURCES=base.SOURCES|{SELF,WF,C,TEST,DIAG,'scripts/pr16_research_retry.py'}
PROTECTED=d.PROTECTED|{'content/modernization/pr16_research_lifecycle_checkpoint.json',
                       'content/modernization/pr16_research_phase0_checkpoint.json'}


def command(label,cmd,timeout=120):
    p=subprocess.run(cmd,capture_output=True,timeout=timeout)
    (PUBLIC/(label+'.stdout.txt')).write_bytes(p.stdout)
    (PUBLIC/(label+'.stderr.txt')).write_bytes(p.stderr)
    d.put(label+'.json',{'command':cmd,'returncode':p.returncode,'stdout':identity(p.stdout),'stderr':identity(p.stderr)})
    if p.stderr:print(p.stderr.decode(),flush=True)
    need(p.returncode==0 and not p.stderr,'clean '+label)


def generated_driver(candidate):
    path=base.generate();text=path.read_text();token='int main(int argc,char**argv){'
    need(text.count(token)==1,'single legacy lifecycle main')
    return ('#define RT_ROM "'+candidate['sha256']+'"\n'+text.replace(token,'int lifecycle_accepted_main(int argc,char**argv){')+'\n'+(ROOT/C).read_text()).encode()


def reuse_diagnostic():
    value=d.read(ROOT/DIAG)
    need(value['status']=='BUG_REPRODUCED_NOT_ACCEPTANCE' and value['returncode']==0 and not value['stderr_utf8'],'recorded successful bug reproduction')
    need(value['parent']==m.bag.CANDIDATE and value['seed']==m.lc.old.SEED and value['entire_private_flash_after']==value['seed'],'bound parent/no flash commit')
    need(identity(generated_driver(m.bag.CANDIDATE))==value['generated'] and identity((ROOT/C).read_bytes())==value['retry_c'],'same diagnostic generated source')
    need(d.bindings(value['source_bindings'])==value['source_bindings'],'diagnostic included dependencies')
    raw=value['stdout_utf8'].encode();need(identity(raw)==value['stdout'],'diagnostic original bytes')
    rows=[m.lc.old.load(x) for x in raw.decode().splitlines()]
    need(len(rows)==11 and rows[6]['result']==7 and rows[6]['saves']==1 and rows[6]['native_result']==255,'actual first failure')
    need(rows[9]['result']==5 and rows[9]['saves']==0 and rows[9]['counter_delta']==0 and rows[8]['recovery_blocked']==0,'actual silent retry loss')
    need(rows[-1]=={'status':'BUG_REPRODUCED','scope':'PARENT_EMPTY_RETRY_NO_PERSIST','same_core_calls':2},'diagnostic closed scope')
    d.put('diagnostic-reuse.json',{'path':DIAG,'binding':identity((ROOT/DIAG).read_bytes()),'source_head':value['source_head'],'new_native_runs':0,'new_compiles':0})


def measure():
    os.chdir(ROOT);d.current();need(not (ROOT/CP).exists(),'recorded matrix must not be repeated')
    nested=[p for p in d.git('ls-files').decode().splitlines() if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','overlays','content','docs','design')]
    need(not nested,'nested AGENTS require review before edits')
    old=d.read(ROOT/'content/modernization/pr16_research_phase0_checkpoint.json')
    need(old['actions_completion_confirmed'] and old['accepted_native_cases']==3 and old['candidate']==m.bag.CANDIDATE,'prior phase0 terminal scope')
    PUBLIC.mkdir(parents=True);bound=d.bindings(SOURCES);protected=d.bindings(PROTECTED)
    d.put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':bound,'protected_bindings':protected})
    reuse_diagnostic()
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_retry.py','-v'],capture_output=True,timeout=120)
    (PUBLIC/'unit.txt').write_bytes(unit.stdout+unit.stderr)
    need(unit.returncode==0 and (unit.stdout+unit.stderr).count(b' ... ok\n')==29,'29 new focused tests including canonical C stub branches')
    runtime,data,seed,parent,artifacts=d.restore()
    original=(ROOT/m.SOURCE).read_bytes();fixed=m.correct_source(original)
    tu=m.translation_unit(fixed);source=OUT/'retry-isolated.c';source.write_bytes(tu)
    script=OUT/'retry-isolated.ld';script.write_text(m.linker_script())
    (PUBLIC/'canonical.patch.txt').write_text(''.join(difflib.unified_diff(original.decode().splitlines(True),fixed.decode().splitlines(True),fromfile=m.SOURCE,tofile=m.SOURCE)))
    (PUBLIC/'isolated-source.c.txt').write_bytes(tu);(PUBLIC/'isolated-link.ld.txt').write_text(m.linker_script())
    obj=OUT/'retry-isolated.o';elf=OUT/'retry-isolated.elf';binary=OUT/'retry-isolated.bin'
    command('arm-compile',['clang-17','--target=thumbv4t-none-eabi','-mcpu=arm7tdmi','-mthumb','-Oz','-ffreestanding','-fno-builtin','-fomit-frame-pointer','-fno-unwind-tables','-Wall','-Wextra','-Werror','-c',str(source),'-o',str(obj)])
    command('arm-link',['ld.lld-17','-T',str(script),str(obj),'-o',str(elf)])
    command('arm-objcopy',['llvm-objcopy-17','-O','binary',str(elf),str(binary)])
    command('arm-disassembly',['llvm-objdump-17','-d',str(elf)])
    code=binary.read_bytes();candidate,recipe=m.apply(parent,code)
    recipe.update(source_before=identity(original),source_after=identity(fixed),translation_unit=identity(tu),
                  compiler=subprocess.check_output(['clang-17','--version']).decode(),linker=subprocess.check_output(['ld.lld-17','--version']).decode(),
                  object=identity(obj.read_bytes()),elf=identity(elf.read_bytes()),arm_compiles=1,arm_links=1)
    d.put('recipe.json',recipe);(data/'retry.gba').write_bytes(candidate)
    generated=generated_driver(recipe['candidate']);runner_source=OUT/'retry.c';runner_source.write_bytes(generated)
    exe=OUT/'retry-runner'
    command('host-compile',['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(runner_source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)])
    d.put('runner.json',{'generated':identity(generated),'executable':identity(exe.read_bytes()),'compiler':subprocess.check_output(['cc','--version']).decode()})
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)];guards={}
    for method in m.lc.old.GUARDS:
        r=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        (PUBLIC/(method+'.stdout.txt')).write_bytes(r.stdout);(PUBLIC/(method+'.stderr.txt')).write_bytes(r.stderr)
        guards[method]={'returncode':r.returncode,'stdout':identity(r.stdout),'stderr':identity(r.stderr)}
        need(r.returncode==1 and not r.stdout and r.stderr==m.lc.old.DENIED,'seven host write barriers '+method)
    d.put('guards.json',guards);accepted={};failures={};processes={}
    for case in m.CASES:
        save=OUT/(case+'.srm');save.write_bytes(seed);start=time.monotonic()
        try:
            r=subprocess.run(prefix+[str(data/'retry.gba'),str(save),case],capture_output=True,timeout=180)
            status={'returncode':r.returncode,'timeout':False};out,err=r.stdout,r.stderr
        except subprocess.TimeoutExpired as exc:
            status={'returncode':None,'timeout':True};out,err=exc.stdout or b'',exc.stderr or b''
        (PUBLIC/(case+'.stdout.txt')).write_bytes(out);(PUBLIC/(case+'.stderr.txt')).write_bytes(err)
        status.update(elapsed_seconds=round(time.monotonic()-start,3),stdout=identity(out),stderr=identity(err),private_save=identity(save.read_bytes()))
        processes[case]=status
        try:
            need(status['returncode']==0 and not status['timeout'] and not err,'successful clean native process')
            accepted[case]=m.validate(out,case,recipe['candidate'])
        except (ValueError,KeyError,TypeError) as exc:failures[case]={'type':type(exc).__name__,'reason':str(exc)}
        print(case,'PASS' if case in accepted else 'FAIL',err.decode(),flush=True)
    need(d.bindings(SOURCES)==bound and d.bindings(PROTECTED)==protected,'input sources and protected history unchanged')
    need(identity((data/'candidate.gba').read_bytes())==m.bag.CANDIDATE and (data/'retry.gba').read_bytes()==candidate and (data/'seed.srm').read_bytes()==seed,'read-only bound inputs/candidate')
    value={'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':recipe['candidate'],'artifacts':artifacts,'accepted':accepted,'failures':failures,'cases':processes,'new_unit_tests':29,'host_compiles':2,'arm_compiles':1,'arm_links':1,'native_processes':7,'guard_processes':7,'new_retry_cases':3,'affected_regression_cases':4,'unaffected_accepted_native_reruns':0,'local_parent_diagnostic_runs':0}
    d.put('measurement.json',value)
    record(fixed,recipe,value,bound,protected)


def record(fixed,recipe,value,bound,protected):
    owned=set();members={};basepath=EVIDENCE+'/'+str(value['run_id'])
    for path in sorted(PUBLIC.iterdir()):
        raw=path.read_bytes();text=raw.decode('utf-8');need(b'\0' not in raw,'public UTF8 text only')
        name=basepath+'/'+path.name
        if any(line.rstrip()!=line for line in text.splitlines()):
            name+='.json';d.write(ROOT/name,{'encoding':'utf-8','binding':identity(raw),'text':text})
        else:
            dest=ROOT/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        members[name]={'original':identity(raw),'stored':identity((ROOT/name).read_bytes())};owned.add(name)
    manifest=basepath+'/manifest.json';d.write(ROOT/manifest,{'source_head':value['source_head'],'members':members});owned.add(manifest)
    complete=not value['failures'] and len(value['accepted'])==len(m.CASES)
    if complete:(ROOT/m.SOURCE).write_bytes(fixed);owned.add(m.SOURCE)
    d.write(ROOT/RECIPE,recipe);owned.add(RECIPE)
    cp={'schema_version':1,'task':TASK,'status':'PASS_RETRY_MATRIX_PENDING_ACTIONS_TERMINAL' if complete else 'PARTIAL_RETRY_MATRIX',
        'source_head':value['source_head'],'run_id':value['run_id'],'candidate':value['candidate'],'parent':m.bag.CANDIDATE,
        'accepted_cases':sorted(value['accepted']),'failed_cases':sorted(value['failures']),'actions_completion_confirmed':False,
        'canonical_correction_published':complete,'canonical_source':{'path':m.SOURCE,'binding':identity((ROOT/m.SOURCE).read_bytes())},
        'source_bindings':bound,'protected_bindings':protected,'recipe':RECIPE,'manifest':manifest,'measurement':basepath+'/measurement.json',
        'new_unit_tests':29,'host_compiles_measured_once':2,'arm_compiles_measured_once':1,'native_processes_measured_once':7,
        'guard_processes_measured_once':7,'parent_diagnostic':DIAG,'parent_diagnostic_reexecuted':False,
        'unaffected_accepted_native_reruns':0,'normal_ui_accepted':False,'v1_load_adapter_accepted':False,
        'physical_flash_fault_accepted':False,'active_baseline_changed':False,'release_ready':False,'issue19_complete':False}
    publish(cp,owned,'修正版の同一core再試行3ケースと影響のある拒否/回復4controlを実測。成功 '+str(len(value['accepted']))+' / 7。')


def publish(cp,owned,summary):
    d.write(ROOT/CP,cp)
    goal=('測定runの終端を原本照合してから、' if not cp['actions_completion_confirmed'] else '')+'未検証のV1通常load adapterを進める。失敗ケースがある場合はその原本と原因だけを先に扱う。受入済み再試行/29unit/旧18取引/BP/P08/特殊野生は影響なしに再実行しない。'
    state=d.read(ROOT/d.STATE)
    state['research_same_core_retry']={'path':CP,'status':cp['status'],'candidate':cp['candidate'],'accepted_cases':cp['accepted_cases'],'run_id':cp['run_id'],'actions_completion_confirmed':cp['actions_completion_confirmed']}
    state['bp']['current_stop']=summary;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_V1_LOAD_ADAPTER_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,RECIPE,DIAG,SELF,C,'scripts/pr16_research_retry.py',m.SOURCE],
        stop_rule_ja='固定候補/source/原本hashを保持。旧候補の受入を新候補へ再ラベルしない。失敗と未実行を成功へ昇格しない。merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='再試行記録source。自己commit SHAはgit log参照。BP/P08履歴とは別scope。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':cp.get('terminal_conclusion')}],'reason_ja':'再試行専用runだけ。全CI成功の主張ではない。'}
    guide='# PR16 研究保存・同一core再試行\n\n'+summary+'\n\n'+goal+'\n\n## 原因と修正\n\n旧4aee03e8候補では空ledger初期化のphase0保存失敗後、V2 RAMだけが残る。同一coreの再試行はSAVE_EMPTYを通らず、保存なしでblockedを解除する。旧候補のnative原本は '+DIAG+'。ローカル実測1process/1coreでありActions実測とは区別し、再実行しない。\n\ncanonical ensure_save_idleは初期化前の2048byteを既存rollback領域に保存し、失敗時に全復元する。V1と初期化の失敗経路を共有し、同じcanonical関数本文だけをThumb ARM7TDMIで既存188byte窓へlinkする。新規ROM/RAM配置なし。窓外全byteとrollbackを確認する。\n\n## 検証scope\n\nzero/erased/V1について保存不可を2回連続で実行し、入力全復元・128KiB Flash不変・blocked保持を検査。可用性fixtureだけを戻して同じcoreで再試行し、実保存1回/counter+1、その次は追加保存0回を確認。実DestroyTaskで各callbackを終了し、通常schedulerへの復帰まで観測する。fresh通常Continueを2回行い全ledger/owner/Bag/手持ちを照合。7host書込みAPIを観測中禁止。\n\n変更影響のあるV1 checksum/tail拒否、既存V2 idle/blocked解除を4controlとして検証。29unitには同じcanonical関数のstub境界試験を含む。stubは実Flash受入ではない。旧18境界/BP/P08/特殊野生の原本は不変、新候補の全取引受入へ再ラベルしない。物理Flash装置故障、V1通常load、通常new-game/取引UI、全catalog、map3/19除外130行、Issue19全体/releaseは未完。\n\n## 記録\n\nsource `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'` / 候補 `'+cp['candidate']['sha256']+'`。\n受入: '+', '.join(cp['accepted_cases'])+'。失敗: '+', '.join(cp['failed_cases'])+'。Actions終端確認: '+str(cp['actions_completion_confirmed'])+'。\n'
    (ROOT/GUIDE).write_text(guide)
    for path in SOURCES|{CP,GUIDE,RECIPE,m.SOURCE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: research-retry-v1\n- Status: '+cp['status']+'（限定scope、V1 load/UI等は未完）\n- Summary: '+summary+'\n- Files changed: retry source/runner/29tests/Actions、canonical C、188byte recipe、原本UTF8証拠/checkpoint、固定引継ぎMD/JSON、guide、両ログ。\n- Verify: 測定は29unit（canonical stub host compile1含む）、ARM compile1/link1、native runner host compile1、guard7/native7。終端記録は全て再実行0。旧候補diagnosticはローカル1process/1core/host compile1を原本再利用。ローカルC縮小検討compile5attemptとtask thunk組立1は受入ではない。影響なしの旧18/BP/P08/特殊野生native再実行0。最終index/限定guard、resume check/task graph後のみcommit。\n- Commit: 同branch非force push。source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log参照。\n- Network: 固定GitHub artifactとUbuntu toolchain配布のみ。ROM/save/binaryは非tracked、保全path不変。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as f:f.write(log)
    d.write(OUT/'owned.json',sorted(owned|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))


def finalize():
    os.chdir(ROOT);d.current();PUBLIC.mkdir(parents=True,exist_ok=True);cp=d.read(ROOT/CP)
    need(not cp['actions_completion_confirmed'] and cp['canonical_correction_published'] and not cp['failed_cases'],'only unconfirmed successful matrix')
    need(cp['accepted_cases']==sorted(m.CASES),'all seven cases already measured')
    run=d.inputs.api('actions/runs/'+str(cp['run_id']));jobs=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=10')
    need(run['head_sha']==cp['source_head'] and run['path']==WF and run['run_attempt']==1 and run['status']=='completed' and run['conclusion']=='success','exact terminal measurement run')
    need(len(jobs['jobs'])==1 and all(j['status']=='completed' and j['conclusion']=='success' and all(s['conclusion']=='success' for s in j['steps']) for j in jobs['jobs']),'all measurement/push/upload steps succeeded')
    need(d.bindings(PROTECTED)==cp['protected_bindings'],'protected history retained')
    for path,binding in cp['source_bindings'].items():
        if path not in (WF,m.SOURCE):need(identity((ROOT/path).read_bytes())==binding,'measurement source unchanged '+path)
    need(identity((ROOT/m.SOURCE).read_bytes())==cp['canonical_source']['binding'],'published canonical source')
    manifest=d.read(ROOT/cp['manifest'])
    for path,binding in manifest['members'].items():need(identity((ROOT/path).read_bytes())==binding['stored'],'immutable evidence '+path)
    value=d.read(ROOT/cp['measurement']);need(sorted(value['accepted'])==cp['accepted_cases'] and not value['failures'],'same recorded outcomes')
    cp.update(status='PASS_SAME_CORE_RETRY_SCOPED',actions_completion_confirmed=True,terminal_conclusion='success',record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']))
    terminal=EVIDENCE+'/'+str(cp['run_id'])+'/terminal.json';d.write(ROOT/terminal,{'run':d.run_summary(run),'jobs':jobs['jobs'],'new_native_runs':0,'new_unit_runs':0,'new_arm_compiles':0});cp['terminal']=terminal
    d.put('terminal-verification.json',d.read(ROOT/terminal))
    publish(cp,{terminal},'同一core再試行3ケースと影響限定4controlを受入。測定run全step/push/uploadのsuccessを原本確認。今回のnative/unit/compile再実行0。')


def guard():
    os.chdir(ROOT);cp=d.read(ROOT/CP);owned=set(d.read(OUT/'owned.json'))
    need(d.bindings(PROTECTED)==cp['protected_bindings'],'protected files')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('measure | finalize | guard')
