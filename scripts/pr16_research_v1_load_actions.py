#!/usr/bin/env python3
"""V1通常ロードだけを測定し、成功/失敗原本と再開地点を同branchへ記録。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_retry_actions as r
import pr16_research_v1_load as m
from pr16_learnset_compact_record import publish_resume
d=r.d;need=m.need;identity=m.identity
TASK='USER-20260926-RESEARCH-V1-LOAD'
SELF='scripts/pr16_research_v1_load_actions.py'
WF='.github/workflows/pr16-research-v1-load-20260926.yml'
C='tools/mgba_pr16_research_v1_load.c'
MODEL='scripts/pr16_research_v1_load.py'
TEST='tests/test_pr16_research_v1_load.py'
CP='content/modernization/pr16_research_v1_load_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_V1_LOAD_JA.md'
EVIDENCE='content/modernization/pr16_research_v1_load_evidence'
SOURCES=r.SOURCES|{SELF,WF,C,MODEL,TEST,'overlays/qol_production/qol_production.c','overlays/mirage_production/mirage_production.c'}
PROTECTED=r.PROTECTED|{r.CP,r.RECIPE,r.GUIDE,r.DIAG,r.m.SOURCE}
OUT=d.OUT;PUBLIC=d.PUBLIC


def measure():
    os.chdir(ROOT);d.current();need(not (ROOT/CP).exists(),'do not rerun recorded V1 matrix')
    prior=d.read(ROOT/r.CP);need(prior['actions_completion_confirmed'] and not prior['failed_cases'] and prior['candidate']==m.CANDIDATE,'completed same-core retry first')
    protected=d.bindings(PROTECTED|set(p for p in d.git('ls-files').decode().splitlines() if p.startswith(r.EVIDENCE+'/')))
    bound=d.bindings(SOURCES);PUBLIC.mkdir(parents=True)
    d.put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':bound,'protected_bindings':protected})
    manifest=d.read(ROOT/prior['manifest'])
    for path,binding in manifest['members'].items():need(identity((ROOT/path).read_bytes())==binding['stored'],'prior immutable evidence '+path)
    baseline=d.read(ROOT/prior['measurement'])['accepted']['retry-zero']['observations'][0]
    d.put('baseline-reuse.json',{'path':prior['measurement'],'binding':identity((ROOT/prior['measurement']).read_bytes()),'observation':baseline,'new_native_runs':0})
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_v1_load.py','-v'],capture_output=True,timeout=120)
    (PUBLIC/'unit.txt').write_bytes(unit.stdout+unit.stderr)
    need(unit.returncode==0 and (unit.stdout+unit.stderr).count(b' ... ok\n')==26,'26 new V1 fixture/oracle tests')
    runtime,data,seed,parent,artifacts=d.restore()
    recipe=d.read(ROOT/r.RECIPE);candidate,rebuilt=r.m.apply(parent,bytes.fromhex(recipe['after']))
    need(identity(candidate)==m.CANDIDATE and rebuilt['after']==recipe['after'],'reuse exact compiled 188byte recipe; no ARM rebuild')
    rom=data/'v1-load.gba';rom.write_bytes(candidate)
    d.put('candidate-reuse.json',{'candidate':identity(candidate),'recipe':r.RECIPE,'recipe_binding':identity((ROOT/r.RECIPE).read_bytes()),'new_arm_compiles':0,'new_arm_links':0,'rom_changes':0})
    fixtures={};receipts={}
    for case in m.CASES:fixtures[case],receipts[case]=m.fixture(seed,case)
    d.put('fixtures.json',receipts)
    text=r.base.generate().read_text();token='int main(int argc,char**argv){';need(text.count(token)==1,'unique lifecycle main')
    header='#define VL_ROM "'+m.CANDIDATE['sha256']+'"\nstatic const char* const VL_FIXTURES[]={'+','.join('"'+receipts[c]['fixture']['sha256']+'"' for c in m.CASES)+'};\n'
    generated=(header+text.replace(token,'int prior_lifecycle_main(int argc,char**argv){')+'\n'+(ROOT/C).read_text()).encode()
    source=OUT/'v1-load.c';source.write_bytes(generated);exe=OUT/'v1-load'
    r.command('host-compile',['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)])
    d.put('runner.json',{'generated':identity(generated),'executable':identity(exe.read_bytes()),'compiler':subprocess.check_output(['cc','--version']).decode()})
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    guards={}
    for method in m.old.GUARDS:
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        (PUBLIC/(method+'.stdout.txt')).write_bytes(p.stdout);(PUBLIC/(method+'.stderr.txt')).write_bytes(p.stderr)
        guards[method]={'returncode':p.returncode,'stdout':identity(p.stdout),'stderr':identity(p.stderr)}
        need(p.returncode==1 and not p.stdout and p.stderr==m.old.DENIED,'seven host write barriers '+method)
    d.put('guards.json',guards);accepted={};failures={};processes={}
    for case in m.CASES:
        save=OUT/(case+'.srm');save.write_bytes(fixtures[case]);start=time.monotonic()
        try:
            p=subprocess.run(prefix+[str(rom),str(save),case],capture_output=True,timeout=240)
            status={'returncode':p.returncode,'timeout':False};out,err=p.stdout,p.stderr
        except subprocess.TimeoutExpired as exc:
            status={'returncode':None,'timeout':True};out,err=exc.stdout or b'',exc.stderr or b''
        (PUBLIC/(case+'.stdout.txt')).write_bytes(out);(PUBLIC/(case+'.stderr.txt')).write_bytes(err)
        status.update(elapsed_seconds=round(time.monotonic()-start,3),stdout=identity(out),stderr=identity(err),private_save=identity(save.read_bytes()))
        processes[case]=status
        try:
            need(status['returncode']==0 and not status['timeout'] and not err,'successful clean native process')
            accepted[case]=m.validate(out,case,fixtures[case],baseline)
        except (ValueError,KeyError,TypeError) as exc:failures[case]={'type':type(exc).__name__,'reason':str(exc)}
        print(case,'PASS' if case in accepted else 'FAIL',err.decode(),flush=True)
    need(d.bindings(protected)==protected and d.bindings(SOURCES)==bound,'all protected history/source unchanged')
    need(rom.read_bytes()==candidate and (data/'seed.srm').read_bytes()==seed,'candidate and original seed read-only')
    value={'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,'artifacts':artifacts,
           'accepted':accepted,'failures':failures,'cases':processes,'new_unit_tests':26,'host_compiles':1,'arm_compiles':0,'arm_links':0,
           'native_processes':3,'guard_processes':7,'accepted_case_reruns':0,'rom_changes':0,'fixture_ram_writes':0}
    d.put('measurement.json',value)
    basepath=EVIDENCE+'/'+str(value['run_id']);owned=set();members={}
    for path in sorted(PUBLIC.iterdir()):
        raw=path.read_bytes();text=raw.decode('utf-8');need(b'\0' not in raw and 'ledger_hex' not in text,'public text only, no private save payload')
        name=basepath+'/'+path.name
        if any(line.rstrip()!=line for line in text.splitlines()):
            name+='.json';d.write(ROOT/name,{'encoding':'utf-8','binding':identity(raw),'text':text})
        else:
            dest=ROOT/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        members[name]={'original':identity(raw),'stored':identity((ROOT/name).read_bytes())};owned.add(name)
    manifest=basepath+'/manifest.json';d.write(ROOT/manifest,{'source_head':value['source_head'],'members':members});owned.add(manifest)
    cp={'schema_version':1,'task':TASK,'source_head':value['source_head'],'run_id':value['run_id'],'candidate':m.CANDIDATE,
        'accepted_cases':sorted(accepted),'failed_cases':sorted(failures),'actions_completion_confirmed':False,
        'status':'PASS_V1_LOAD_PENDING_TERMINAL' if not failures else 'PARTIAL_V1_LOAD_PENDING_TERMINAL',
        'measurement':basepath+'/measurement.json','fixtures':basepath+'/fixtures.json','manifest':manifest,
        'source_bindings':bound,'protected_bindings':protected,'new_unit_tests':26,'host_compiles_measured_once':1,
        'native_processes_measured_once':3,'guard_processes_measured_once':7,'arm_compiles':0,'arm_links':0,'rom_changes':0,
        'accepted_case_reruns':0,'v1_load_valid_accepted':m.CASES[0] in accepted,'normal_load_rejections_accepted':all(c in accepted for c in m.CASES[1:]),
        'phase0_load_failure_accepted':False,'normal_new_game_accepted':False,'transaction_ui_accepted':False,
        'physical_flash_fault_accepted':False,'active_baseline_changed':False,'issue19_complete':False,'release_ready':False}
    publish(cp,owned,'通常cold boot/ContinueのV1移行・破損拒否3ケースを測定。成功 '+str(len(accepted))+' / 3。')


def publish(cp,owned,summary):
    d.write(ROOT/CP,cp)
    if cp['failed_cases']:goal='失敗した '+', '.join(cp['failed_cases'])+' の原本とload chainを最初に切り分ける。成功case/26unit/ARM/同一core再試行7caseは影響なく再実行しない。'
    else:goal='次はV1通常load内のphase0保存不可境界と回復、その後通常new-game/取引UIを進める。受入済み3load/7retry/旧18取引、BP/P08/特殊野生は影響なく再実行しない。'
    if not cp['actions_completion_confirmed']:goal='まず本測定runの終端とpush/upload結果を照合する。'+goal
    state=d.read(ROOT/d.STATE)
    state['research_v1_normal_load']={'path':CP,'status':cp['status'],'candidate':cp['candidate'],'accepted_cases':cp['accepted_cases'],'failed_cases':cp['failed_cases'],'run_id':cp['run_id'],'actions_completion_confirmed':cp['actions_completion_confirmed']}
    state['bp']['current_stop']=summary;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_V1_LOAD_FAILURE_NEXT' if not cp['failed_cases'] else 'RESEARCH_V1_LOAD_DIAGNOSE_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,cp['measurement'],cp['fixtures'],SELF,C,MODEL,r.CP,r.RECIPE,r.m.SOURCE],
        stop_rule_ja='候補58079dfbとsource/原本hashを保持。未成功loadを受入へ昇格しない。既存原本/ROM/save/baselineは保全し、merge/release禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='V1通常load記録source。自己commit SHAはgit log参照。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':cp.get('terminal_conclusion')}],'reason_ja':'V1通常load専用run。全CI成功ではない。'}
    guide='# PR16 V1実保存の通常ロード\n\n'+summary+'\n\n'+goal+'\n\n## 検証境界\n\n固定seedのコピー内のsector31 +0x64、2048byte ledgerだけをV1に変換し、checksum破損/193byte予約tail破損も別fixtureで作る。stock保存sectorと他ownerは変更0。歴史的なユーザーV1 saveそのものではなく、独立生成した私有Flash fixtureである。保存payload/ROM/binaryはGitへ入れない。\n\n起動から通常Start/A/Continueで進める間、7host書込みAPIを禁止し、CPUのPC/SP/LR/r0は読取だけ。RAM ledger/owner/引数/戻り値/PCの注入0。0x080DB4E4の既存wrapperからResearch→Mirage→QOLの実load各1回、phase0実保存と戻り値/counterを観測する。既存188byte修正候補をrecipeで復元しARM再compile/link0、ROM変更0。\n\n正常V1は全ledger移行内容/実Flash/他private ownerと通常field到達を比較し、2回のfresh Continueで全ledger/owner/Bag/手持ち/counterの不変を確認する。破損2例はadapter戻り境界までで、全ledger入力保持・128KiB Flash不変・エラー伝播を検証する。破損後のメニューUI全体は未受入。通常new-game/取引UI、load内保存不可、物理Flash故障、全catalog/Issue19/releaseは未完。\n\n## 実行と記録\n\nsource `'+cp['source_head']+'`、run `'+str(cp['run_id'])+'`。26unit、host compile1、guard7、native3。終端記録は全再実行0。受入: '+', '.join(cp['accepted_cases'])+'。失敗: '+', '.join(cp['failed_cases'])+'。終端確認: '+str(cp['actions_completion_confirmed'])+'。候補 `'+m.CANDIDATE['sha256']+'`。\n'
    (ROOT/GUIDE).write_text(guide)
    for path in SOURCES|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: research-v1-load-v1\n- Status: '+cp['status']+'（限定scope、未受入境界はguide参照）\n- Summary: '+summary+'\n- Files changed: V1 fixture/oracle/26tests、通常load runner/Actions、原本/checkpoint、専用guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 測定26unit/host compile1/guard7/native3、既存188byte recipeをhash照合して再利用（ARM compile/link0、ROM変更0）。終端記録はunit/host/ARM/native全0。BP/P08/特殊野生/旧18取引/再試行7受入のnative再実行0。最終resume/task graph/index限定guard/diff-check後にcommit。失敗はfailed_casesと原本のまま保持。\n- Commit: 同branch非force、source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log参照。\n- Network: 固定GitHub artifactだけ。私有seed/元ZIP保全。新規toolchain配布なし。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as f:f.write(log)
    d.write(OUT/'owned.json',sorted(owned|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))


def finalize():
    os.chdir(ROOT);d.current();PUBLIC.mkdir(parents=True);cp=d.read(ROOT/CP)
    need(not cp['actions_completion_confirmed'],'already finalized; no repetition')
    run=d.inputs.api('actions/runs/'+str(cp['run_id']));jobs=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=10')
    conclusion='failure' if cp['failed_cases'] else 'success'
    need(run['head_sha']==cp['source_head'] and run['path']==WF and run['run_attempt']==1 and run['status']=='completed' and run['conclusion']==conclusion,'exact terminal load measurement')
    need(len(jobs['jobs'])==1 and jobs['jobs'][0]['status']=='completed' and jobs['jobs'][0]['conclusion']==conclusion,'exact job conclusion')
    for step in jobs['jobs'][0]['steps']:
        expected='failure' if cp['failed_cases'] and step['name']=='失敗を成功扱いしない' else 'success'
        need(step['conclusion']==expected,'actual step conclusion '+step['name'])
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected history')
    for path,binding in cp['source_bindings'].items():
        if path!=WF:need(identity((ROOT/path).read_bytes())==binding,'unchanged measured source '+path)
    manifest=d.read(ROOT/cp['manifest'])
    for path,binding in manifest['members'].items():need(identity((ROOT/path).read_bytes())==binding['stored'],'original evidence retained '+path)
    value=d.read(ROOT/cp['measurement']);need(sorted(value['accepted'])==cp['accepted_cases'] and sorted(value['failures'])==cp['failed_cases'],'no acceptance promotion')
    cp.update(status='PASS_V1_LOAD_SCOPED' if not cp['failed_cases'] else 'PARTIAL_V1_LOAD_RECORDED',actions_completion_confirmed=True,
        terminal_conclusion=conclusion,record_source_head=os.environ['GITHUB_SHA'],record_run_id=int(os.environ['GITHUB_RUN_ID']))
    path=EVIDENCE+'/'+str(cp['run_id'])+'/terminal.json';d.write(ROOT/path,{'run':d.run_summary(run),'jobs':jobs['jobs'],'new_native_runs':0,'new_unit_runs':0,'new_host_compiles':0,'new_arm_compiles':0});cp['terminal']=path
    d.put('terminal-verification.json',d.read(ROOT/path));publish(cp,{path},'通常V1 loadの成功 '+str(len(cp['accepted_cases']))+' / 3 と測定run終端 '+conclusion+' を原本確認。記録時のnative/unit/compile再実行0。')


def guard():
    os.chdir(ROOT);cp=d.read(ROOT/CP);owned=set(d.read(OUT/'owned.json'));need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected files')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('measure | finalize | guard')
