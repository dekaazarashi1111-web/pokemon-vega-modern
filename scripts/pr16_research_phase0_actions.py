#!/usr/bin/env python3
"""既存native保存不可のphase0のみ。旧5/18境界、unit30を再実行しない。"""
from __future__ import annotations
import datetime,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_lifecycle_v2 as base
import pr16_research_phase0 as p
from pr16_learnset_compact_record import publish_resume
d=base.d;need=d.need;identity=d.identity
SELF='scripts/pr16_research_phase0_actions.py'
WF='.github/workflows/pr16-research-phase0-20260926.yml'
C='tools/mgba_pr16_research_phase0.c'
TEST='tests/test_pr16_research_phase0.py'
CP='content/modernization/pr16_research_phase0_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_PHASE0_JA.md'
EVIDENCE='content/modernization/pr16_research_phase0_evidence'
SOURCES=base.SOURCES|{SELF,WF,C,TEST,'scripts/pr16_research_phase0.py'}
PROTECTED=d.PROTECTED|{d.CP}
OUT=d.OUT;PUBLIC=d.PUBLIC
TASK='USER-20260926-RESEARCH-PHASE0'


def measure():
    os.chdir(ROOT);d.current();need(not (ROOT/CP).exists(),'phase0 already recorded: do not rerun')
    accepted=d.read(ROOT/d.CP)
    need(accepted['accepted_native_cases']==5 and accepted['actions_completion_confirmed'] and accepted['candidate']==d.bag.CANDIDATE,'prior five-case terminal receipt')
    need(d.bindings(set(accepted['source_bindings']))==accepted['source_bindings'],'accepted lifecycle dependencies unchanged')
    PUBLIC.mkdir(parents=True);bound=d.bindings(SOURCES);protected=d.bindings(PROTECTED)
    d.put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'sources':bound,'protected':protected})
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_phase0.py','-v'],capture_output=True,timeout=120)
    (PUBLIC/'unit.txt').write_bytes(unit.stdout+unit.stderr)
    if unit.returncode:print((unit.stdout+unit.stderr).decode(),flush=True)
    need(unit.returncode==0 and (unit.stdout+unit.stderr).count(b' ... ok\n')==18,'18 new phase0 tests')
    runtime,data,seed,candidate,artifacts=d.restore()
    ranges=[]
    for address,size,digest in p.RANGES:
        part=candidate[address-0x08000000:address-0x08000000+size]
        need(identity(part)=={'size':size,'sha256':digest},'exact native failure path range')
        ranges.append({'address':hex(address),'binding':identity(part)})
    d.put('native-path.json',{'candidate':identity(candidate),'ranges':ranges,'fixture_address':'0x03005044','fixture_initial':1,'fixture_input':0,'observed_return_pc':'0x0937767a','expected_native_return':255,'rom_changes':0,'physical_flash_fault_accepted':False})
    generated=base.generate();text=p.generate(generated.read_text(),(ROOT/C).read_text());generated.write_text(text)
    d.put('phase-generation.json',{'generated':identity(generated.read_bytes()),'sources':bound,'observer':'read_register r0 at native return; no host write during observation'})
    exe=OUT/'phase0-runner';cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(generated),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    comp=subprocess.run(cmd,capture_output=True,timeout=120)
    d.put('compile.json',{'command':cmd,'returncode':comp.returncode,'stdout':comp.stdout.decode(),'stderr':comp.stderr.decode(),'executable':identity(exe.read_bytes()) if exe.exists() else None})
    if comp.stderr:print(comp.stderr.decode(),flush=True)
    need(comp.returncode==0 and not comp.stderr,'strict new host compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)];guards={}
    for method in p.m.GUARDS:
        r=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        guards[method]={'returncode':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode()}
        need(r.returncode==1 and not r.stdout and r.stderr==p.m.DENIED,'seven new binary host-write barriers')
    d.put('guards.json',guards)
    success={};failed={};processes={}
    for case in p.CASES:
        target=OUT/(case+'.srm');target.write_bytes(seed);start=time.monotonic()
        try:
            r=subprocess.run(prefix+[str(data/'candidate.gba'),str(target),case],capture_output=True,timeout=180)
            status={'returncode':r.returncode,'timeout':False};out,err=r.stdout,r.stderr
        except subprocess.TimeoutExpired as exc:
            status={'returncode':None,'timeout':True};out,err=exc.stdout or b'',exc.stderr or b''
        (PUBLIC/(case+'.stdout.txt')).write_bytes(out)
        d.put(case+'.process.json',dict(status,stderr=err.decode(),stdout=identity(out),elapsed_seconds=round(time.monotonic()-start,3),private_flash=identity(target.read_bytes()[:len(seed)])))
        processes[case]=dict(status,stdout=identity(out),stderr=identity(err))
        try:
            need(status['returncode']==0 and not status['timeout'] and not err,'clean native process')
            need(target.read_bytes()[:len(seed)]==seed,'entire original 128KiB Flash unchanged')
            success[case]=p.validate(out,case)
        except (ValueError,KeyError,TypeError) as exc:failed[case]={'reason':str(exc),'type':type(exc).__name__}
        print(case,'PASS' if case in success else 'FAIL',err.decode(),flush=True)
    need(d.bindings(SOURCES)==bound and d.bindings(PROTECTED)==protected,'read-only source/protected inputs')
    need(identity((data/'candidate.gba').read_bytes())==d.bag.CANDIDATE and (data/'seed.srm').read_bytes()==seed,'read-only candidate and seed')
    d.put('measurement.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':d.bag.CANDIDATE,'artifact_inputs':artifacts,'accepted':success,'failed':failed,'processes':processes,'new_unit_tests':18,'native_processes':3,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0})


def record():
    os.chdir(ROOT);d.current();need(not (ROOT/CP).exists(),'new immutable phase0 record')
    inv=d.read(PUBLIC/'invocation.json');v=d.read(PUBLIC/'measurement.json')
    need(inv['source_head']==v['source_head']==os.environ['GITHUB_SHA'] and d.bindings(SOURCES)==inv['sources'] and d.bindings(PROTECTED)==inv['protected'],'exact measured source')
    directory=EVIDENCE+'/'+os.environ['GITHUB_RUN_ID'];need(not (ROOT/directory).exists(),'immutable evidence directory')
    manifest={}
    for file in sorted(PUBLIC.iterdir()):
        raw=file.read_bytes();text=raw.decode('utf-8');need('\0' not in text and file.suffix in ('.json','.txt'),'only public UTF8 evidence')
        name=file.name
        if any(line!=line.rstrip() for line in raw.splitlines()):
            name+='.json';raw=p.lc.encode({'original_name':file.name,'original_binding':identity(raw),'encoding':'utf-8','text':text})
        target=ROOT/directory/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);manifest[str(target.relative_to(ROOT))]=identity(raw)
    mp=directory+'/manifest.json';d.write(ROOT/mp,manifest)
    cp={'schema_version':1,'task':TASK,'status':'PASS_PHASE0_NATIVE_UNAVAILABLE_3_SCOPED' if not v['failed'] else 'PARTIAL_PHASE0_NATIVE_UNAVAILABLE','candidate':d.bag.CANDIDATE,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'accepted_cases':sorted(v['accepted']),'failed_cases':sorted(v['failed']),'accepted_native_cases':len(v['accepted']),
        'measurement':directory+'/measurement.json','manifest':mp,'sources':inv['sources'],'protected':inv['protected'],'new_unit_tests':18,'native_processes':3,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0,'actions_completion_confirmed':False,
        'native_save_unavailable_phase0_accepted':not v['failed'],'physical_flash_fault_accepted':False,'same_core_retry_accepted':False,'v1_load_adapter_accepted':False,'normal_ui_accepted':False,'release_ready':False,'active_baseline_changed':False,'issue19_complete':False}
    publish(cp,'record',set(manifest)|{mp})


def finalize():
    os.chdir(ROOT);d.current();PUBLIC.mkdir(parents=True);cp=d.read(ROOT/CP)
    need(not cp['actions_completion_confirmed'],'phase0 terminal already recorded')
    run=d.inputs.api('actions/runs/'+str(cp['run_id']));jobs=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=5')['jobs']
    need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==cp['source_head'] and run['path']==WF and run['run_attempt']==1,'actual terminal phase0 success')
    need(len(jobs)==1 and jobs[0]['conclusion']=='success' and all(x['conclusion']=='success' for x in jobs[0]['steps']),'all measured run steps and nonforce push')
    for path,b in d.read(ROOT/cp['manifest']).items():need(identity((ROOT/path).read_bytes())==b,'immutable measurement original')
    need(d.bindings(PROTECTED)==cp['protected'],'all prior accepted checkpoints unchanged')
    cp['actions_completion_confirmed']=True;cp['measurement_actions']=d.run_summary(run)
    path=EVIDENCE+'/terminal-'+str(run['id'])+'.json';d.write(ROOT/path,{'run':d.run_summary(run),'jobs':jobs,'new_native_processes':0,'new_unit_tests':0,'new_compiles':0})
    publish(cp,'finalize',{path})


def publish(cp,mode,owned):
    d.write(ROOT/CP,cp)
    goal='初期化/V1 RAM正常・破損拒否5件に加え、phase0既存native保存不可'+str(cp['accepted_native_cases'])+'/3件を記録。次は同一coreの失敗後再試行とV1通常load adapter。特にEMPTY失敗後はV2 RAMを残してblockedとなるため、再試行時の永続化をまだ保証していない。受入済み5/18/phase0成功ケースを再実行しない。'
    if cp['failed_cases']:goal='まずphase0 checkpointの失敗原本を修正し、失敗ケースだけ再開。'+goal
    state=d.read(ROOT/d.STATE);state['research_phase0']={'path':CP,'status':cp['status'],'accepted_cases':cp['accepted_cases'],'run_id':cp['run_id'],'actions_completion_confirmed':cp['actions_completion_confirmed']}
    state['bp']['current_stop']=goal;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_RETRY_AND_V1_LOAD_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,d.GUIDE,d.CP,SELF,'scripts/pr16_research_phase0.py',C,d.bag.SOURCE,d.save.CONFIG],stop_rule_ja='候補4aee03e8/source/原本を固定。保存不可RAM fixtureを実Flash装置故障・同一core retry・通常new-game/UIに昇格しない。旧5/18/特殊野生/BP/P08再実行禁止。merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='今回phase0記録source。測定HEAD/runは専用checkpoint、自己commitはgit log参照。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[cp.get('measurement_actions',{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'in_progress','conclusion':None})],'reason_ja':'限定phase0のみ。終端確認前にsuccessを自己確定せず、一般CI全体成功は主張しない。'}
    guide='# PR16 phase0保存不可の限定検証\n\n'+goal+'\n\n## 実行境界\n\n候補4aee03e8の変更なし。native trampolineのliteral0x09378b28が指す0x03005044を、観測開始前だけ1から0へ設定する。既存engine0x080db356のcmp/bneが保存不可分岐へ進み、QOL wrapperへ返るPC0x0937767aのr0=255をreadonly観測する。research fault flagをphase0の故障として偽装しない。7 API host-write guardは観測中有効。\n\n3ケースは空/消去済み初期化とV1 RAM移行。phase0試行1回、native失敗1回、保存counter増分0、全128KiB Flash不変、Bag/手持ち不変を検査する。V1は全2KiB rollback、新規はRAM V2を残してblocked=1。独立coreで通常Continue2回、全ledger/owner/Bag/手持ちが旧保存と一致する。\n\n## 未受入\n\n物理Flash装置故障、途中書込、同一core再試行、通常V1ファイルのload adapter、新規ゲーム全体・通常取引UIは別境界。EMPTY失敗後の同一core再試行は優先して調べる。今回の新規18unit/3native/7guard/host compile1/ARM0、旧5+18native再実行0。BP/P08/特殊野生/active baselineは不変。\n\n## 原本\n\nsource `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'`。成功: '+', '.join(cp['accepted_cases'])+'。失敗: '+', '.join(cp['failed_cases'])+'。終端確認: '+str(cp['actions_completion_confirmed'])+'。\n'
    (ROOT/GUIDE).write_text(guide)
    for path in SOURCES|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: research-phase0-{mode}-v1\n- Status: {cp["status"]}（限定scope）\n- Summary: {goal}\n- Files changed: 新phase0 C/validator/18負の試験/Actions、UTF8原本とcheckpoint、固定引継ぎMD/JSON、専用guide、両ログ。\n- Verify: measure時のみ新unit18/native3/9cores/guard7/host compile1、finalize時は追加実行0。ARM0、旧5+18native/旧unit30の再実行0。全Flash不変/全owner/Bag/party/ledger/counter/実native戻り値255を照合。resume/task graph/最終index scoped private guard/diff check後のみcommit。\n- Commit: 同branch非force push。source={os.environ["GITHUB_SHA"]}、自己SHAはgit log参照。\n- Network: 固定GitHub artifact/PR/Actionsのみ。ROM/save非tracked。全CI成功・通常UI・物理Flash故障・同一core retry・Issue19全体完了を主張しない。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as f:f.write(log)
    d.write(OUT/'owned.json',sorted(owned|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS));print(cp['status'],cp['accepted_cases'],cp['failed_cases'])


def guard():
    os.chdir(ROOT);import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    need(d.bindings(PROTECTED)==d.read(ROOT/CP)['protected'],'prior accepted checkpoints/source remain unchanged')
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    mode=sys.argv[1:]
    if mode==['measure']:measure();record()
    elif mode==['finalize']:finalize()
    elif mode==['guard']:guard()
    elif mode==['paths']:print('\n'.join(d.read(OUT/'owned.json')))
    else:raise SystemExit('usage: measure|finalize|guard|paths')
