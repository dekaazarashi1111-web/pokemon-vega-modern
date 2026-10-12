#!/usr/bin/env python3
"""新しい保存境界だけを実行・記録。原本/旧受入/ROM/基準は変更しない。"""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_lifecycle as m
import pr16_research_bag_actions as inputs
import pr16_research_save_delegate as save
import pr16_research_bag_delegate as bag
need,identity=m.need,m.identity
TASK='USER-20260926-RESEARCH-LIFECYCLE'
SELF='scripts/pr16_research_lifecycle_actions.py'
C='tools/mgba_pr16_research_lifecycle.c'
WF='.github/workflows/pr16-research-lifecycle-20260926.yml'
TEST='tests/test_pr16_research_lifecycle.py'
CP='content/modernization/pr16_research_lifecycle_checkpoint.json'
BASE='content/modernization/pr16_research_lifecycle_evidence'
GUIDE='docs/PR16_RESEARCH_LIFECYCLE_JA.md'
STATE='content/modernization/pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
LOGS={'design/run_log.md','design/version_log.md'}
OUT=Path('.local/pr16-research-lifecycle');PUBLIC=OUT/'public'
SOURCES=(inputs.SOURCES-{inputs.WF})|{SELF,C,WF,TEST,'scripts/pr16_research_lifecycle.py','scripts/pr16_research_save_impact.py'}
PROTECTED={'content/modernization/pr16_bp_chooser_checkpoint.json','content/modernization/p08_remaining_work.json',
           'content/modernization/pr16_research_save_impact_checkpoint.json','content/modernization/pr16_special_wild_ui_checkpoint.json',
           'config/active_play_baseline.json','design/active_play_baseline.md','CHATGPT_RESUME.md'}


def read(path):return m.old.load(Path(path).read_bytes())
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(m.encode(value))
def put(name,value):write(PUBLIC/name,value)
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return {p:identity((ROOT/p).read_bytes()) for p in sorted(paths)}
def run_summary(run):return {k:run[k] for k in ('id','head_sha','head_branch','path','status','conclusion','run_attempt')}
def current():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern','same repository')
    p=inputs.api('pulls/16');need(p['draft'] and not p['merged'] and p['state']=='open' and p['head']['sha']==os.environ['GITHUB_SHA'] and p['head']['ref']=='codex/modernization-followup-20260908','exact open draft branch HEAD')
    return p


def restore():
    artifacts=[]
    for name,number,size,digest,count,total in inputs.SPECS:
        meta=inputs.api('actions/artifacts/'+str(number))
        need(not meta['expired'] and meta['size_in_bytes']==size and meta['digest']=='sha256:'+digest and meta['workflow_run']['id']==36218655601,'fixed input metadata')
        raw=inputs.api('actions/artifacts/'+str(number)+'/zip',True)
        need(identity(raw)=={'size':size,'sha256':digest},'fixed input archive bytes')
        dest=OUT/name;dest.mkdir()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            need(len(z.infolist())==count and len(set(z.namelist()))==count and sum(e.file_size for e in z.infolist())==total,'exact member bounds')
            for e in z.infolist():
                p=PurePosixPath(e.filename)
                need(not p.is_absolute() and '..' not in p.parts and '\\' not in e.filename and e.external_attr>>28!=10 and not e.is_dir(),'safe regular input')
                target=dest/str(p);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(e))
        artifacts.append({k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run')})
    runtime,data=OUT/'runtime',OUT/'data'
    original=(data/'candidate.gba').read_bytes();parent,sr=save.apply(original);candidate,br=bag.apply(parent)
    (data/'candidate.gba').write_bytes(candidate);put('save-recipe.json',sr);put('bag-recipe.json',br)
    seed=(data/'seed.srm').read_bytes();need(identity(seed)==m.old.SEED,'fixed seed')
    need(identity((runtime/'lib/libmgba.so').read_bytes())=={'size':1968536,'sha256':'0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'},'fixed mGBA library')
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    return runtime,data,seed,candidate,artifacts


def diagnose(candidate):
    """次の故障境界用の限定readonly読取。候補変更/再link/native実行なし。"""
    import struct
    rows=[]
    for start,size in ((0x1377660,52),(0x13bf630,80)):
        literals=[];calls=[]
        for at in range(start,start+size-2,2):
            h=struct.unpack_from('<H',candidate,at)[0]
            if h&0xf800==0x4800:
                loc=((0x08000000+at+4)&~3)+4*(h&255)
                if 0x08000000<=loc<0x0a000000:
                    value=struct.unpack_from('<I',candidate,loc-0x08000000)[0]
                    literals.append({'instruction':hex(0x08000000+at),'register':(h>>8)&7,'literal':hex(loc),'value':hex(value)})
            if h&0xf800==0xf000:
                h2=struct.unpack_from('<H',candidate,at+2)[0]
                if h2&0xf800==0xf800:
                    off=((h&2047)<<12)|((h2&2047)<<1)
                    if off&(1<<22):off-=1<<23
                    calls.append({'instruction':hex(0x08000000+at),'target':hex(0x08000000+at+4+off)})
        rows.append({'start':hex(0x08000000+start),'binding':identity(candidate[start:start+size]),'literal_candidates':literals,'direct_bl':calls})
    put('phase0-readonly.json',{'scope':'READONLY_LITERAL_BL_FRONTIER_NOT_FAULT_ACCEPTANCE','candidate':identity(candidate),'ranges':rows})


def measure():
    os.chdir(ROOT);current();need(not (ROOT/CP).exists(),'do not rerun a recorded initial matrix')
    PUBLIC.mkdir(parents=True)
    prior=read(ROOT/'content/modernization/pr16_research_save_impact_checkpoint.json')
    need(prior['accepted_native_cases']==18 and prior['actions_completion_confirmed'] and prior['candidate']==bag.CANDIDATE,'previous 18-case terminal checkpoint')
    need(identity((ROOT/bag.SOURCE).read_bytes())==prior['canonical_source']['binding'],'accepted canonical source')
    for p in SOURCES & set(prior['record_source_bindings']):
        need(identity((ROOT/p).read_bytes())==prior['record_source_bindings'][p],'accepted dependency unchanged '+p)
    nested=[p for p in git('ls-files').decode().splitlines() if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')]
    need(not nested,'nested agent rules require explicit review')
    bound=bindings(SOURCES);protected=bindings(PROTECTED)
    put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':bound,'protected_bindings':protected,'accepted_case_reruns':0,'arm_compiles':0})
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_lifecycle.py','-v'],capture_output=True,timeout=120)
    (PUBLIC/'unit.txt').write_bytes(unit.stdout+unit.stderr)
    need(unit.returncode==0 and (unit.stdout+unit.stderr).count(b' ... ok\n')==22,'22 new validator tests')
    runtime,data,seed,candidate,artifacts=restore();diagnose(candidate)
    put('inputs.json',{'candidate':identity(candidate),'seed':identity(seed),'artifacts':artifacts,'source_bindings':bound})
    exe=OUT/'runner';cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I'+str(runtime/'include'),C,'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    comp=subprocess.run(cmd,capture_output=True,timeout=120)
    (PUBLIC/'compile.stdout.txt').write_bytes(comp.stdout);(PUBLIC/'compile.stderr.txt').write_bytes(comp.stderr)
    put('compile.json',{'returncode':comp.returncode,'command':cmd,'compiler':subprocess.check_output(['cc','--version']).decode(),'executable':identity(exe.read_bytes()) if exe.exists() else None,'source_bindings':bound})
    need(comp.returncode==0 and not comp.stderr,'strict host compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    guards={}
    for method in m.old.GUARDS:
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10)
        (PUBLIC/(method+'.stdout.txt')).write_bytes(p.stdout);(PUBLIC/(method+'.stderr.txt')).write_bytes(p.stderr)
        guards[method]={'returncode':p.returncode,'stdout':identity(p.stdout),'stderr':identity(p.stderr)}
        need(p.returncode==1 and not p.stdout and p.stderr==m.old.DENIED,'new executable host guard '+method)
    put('guards.json',guards)
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
        except (ValueError,KeyError,TypeError) as exc:
            failures[case]={'exception_type':type(exc).__name__,'reason':str(exc)}
        print(case,'PASS' if case in results else 'FAIL',flush=True)
    need(bindings(SOURCES)==bound and bindings(PROTECTED)==protected,'no source/protected mutation')
    need(identity((data/'seed.srm').read_bytes())==identity(seed) and identity((data/'candidate.gba').read_bytes())==bag.CANDIDATE,'read-only input proof')
    put('measurement.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':bag.CANDIDATE,'cases':processes,'accepted':results,'failures':failures,
        'new_unit_tests':22,'native_processes':len(processes),'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0,'actions_completion_confirmed':False})


def record():
    os.chdir(ROOT);current();need(not (ROOT/CP).exists(),'initial record is immutable')
    invocation=read(PUBLIC/'invocation.json');v=read(PUBLIC/'measurement.json')
    need(invocation['source_head']==v['source_head']==os.environ['GITHUB_SHA'],'measurement HEAD')
    need(bindings(SOURCES)==invocation['source_bindings'] and bindings(PROTECTED)==invocation['protected_bindings'],'measurement source/protected identities')
    directory=BASE+'/'+os.environ['GITHUB_RUN_ID'];need(not (ROOT/directory).exists(),'immutable evidence directory')
    evidence={}
    for p in sorted(PUBLIC.iterdir()):
        need(p.is_file() and p.suffix in ('.json','.txt'),'public regular text only')
        raw=p.read_bytes();raw.decode('utf-8');need(b'\0' not in raw,'no binary evidence')
        target=ROOT/directory/p.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);evidence[str(target.relative_to(ROOT))]=identity(raw)
    write(ROOT/directory/'manifest.json',evidence)
    cp={'schema_version':1,'task':TASK,'status':'PASS_INITIAL_LIFECYCLE_5_SCOPED' if not v['failures'] else 'PARTIAL_INITIAL_LIFECYCLE',
        'candidate':bag.CANDIDATE,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'accepted_cases':list(v['accepted']),'failed_cases':list(v['failures']),'accepted_native_cases':len(v['accepted']),
        'measurement':directory+'/measurement.json','manifest':directory+'/manifest.json','source_bindings':invocation['source_bindings'],'protected_bindings':invocation['protected_bindings'],
        'new_unit_tests':22,'native_processes':len(v['cases']),'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0,
        'actions_completion_confirmed':False,'normal_new_game_or_transaction_ui_accepted':False,'v1_load_adapter_accepted':False,'phase0_failure_accepted':False,
        'release_ready':False,'active_baseline_changed':False,'issue19_complete':False}
    publish(cp,'measure',set(evidence)|{directory+'/manifest.json'})


def publish(cp,mode,evidence):
    from pr16_learnset_compact_record import publish_resume
    write(ROOT/CP,cp)
    goal=('初期化/V1移行の限定5件を原本から照合。成功済みを再実行せず、phase0実失敗とV1 load adapterの未検証経路へ進む。' if not cp['failed_cases'] else '初期化/V1移行の成功部分を保持し、専用checkpointの失敗原本を先に読む。成功ケースを再実行せず原因修正後の影響ケースだけを再開する。')
    goal+=' 通常新規ゲーム/取引UI・全catalog・map3/19除外130行・releaseは未完。'
    state=read(ROOT/STATE)
    state['research_save_lifecycle']={'path':CP,'status':cp['status'],'candidate':cp['candidate'],'accepted_cases':cp['accepted_cases'],'run_id':cp['run_id'],'actions_completion_confirmed':cp['actions_completion_confirmed']}
    state['bp']['current_stop']='研究保存初期化/V1移行の新規限定工程: '+str(cp['accepted_native_cases'])+'/5件を記録。旧18境界/野生/BP/P08は不変。'
    state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_LIFECYCLE_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,SELF,'scripts/pr16_research_lifecycle.py',C,bag.SOURCE,save.CONFIG],stop_rule_ja='候補4aee03e8と実行sourceを固定。受入済みケース・旧18境界・野生/BP/P08を再実行しない。fixtureサービス試験を通常UI/new-game/load-adapter受入へ昇格しない。merge/release/baseline切替禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='研究保存lifecycle記録のsource HEAD。自己commit SHAはgit logで照合。正式BP/P08の履歴を置換しない。'
    state['observed_head_checks']={'scope_head':os.environ['GITHUB_SHA'],'runs':[{'id':int(os.environ['GITHUB_RUN_ID']),'head_sha':os.environ['GITHUB_SHA'],'status':'in_progress','conclusion':None}],
        'reason_ja':'このrunの終端はまだ自己確定しない。専用checkpointに成功/失敗scopeを記録。一般CIのaction_requiredや実行中をsuccessにしない。'}
    guide='# PR16 研究保存lifecycle限定検証\n\nTask: `'+TASK+'`\n\n'+state['bp']['current_stop']+'\n\n'+goal+'\n\n## 受入境界\n\n固定候補4aee03e8の実schedulerから、空/消去済み研究ledgerまたはV1 RAM fixtureを投入し、無効activityの入口によって保存初期化/移行だけを通す。通常取引・新規ゲーム全体・V1セーブの通常loadとは区別する。正常系はphase0実Flash保存1回、破損V1は保存0回。別coreで通常Continueを2回行い、全owner/全Bag/手持ち/全ledger hash/保存counterを照合する。\n\n旧18取引、特殊野生2件、BP/P08、active baseline、旧失敗原本は変更しない。新ARM compileは0。phase0故障フラグはphase!=0だけを対象にするため、0を指定して故障済みとは主張しない。次の実失敗試験はreadonly呼出し境界から設計する。\n\n## 記録\n\nsource `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'`。成功ケース: '+', '.join(cp['accepted_cases'])+'。失敗ケース: '+', '.join(cp['failed_cases'])+'。Actions終端確認: '+str(cp['actions_completion_confirmed'])+'。\n'
    (ROOT/GUIDE).write_text(guide)
    for path in SOURCES|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 研究保存の初期化・V1移行限定工程\n- Version: research-lifecycle-{mode}-v1\n- Status: '+('DONE（限定scope、後続未完）' if not cp['failed_cases'] else 'STOPPED（成功部分保存、失敗原因を次に修正）')+f'\n- Summary: 候補4aee03e8を固定recipeから復元。新5ケースのうち{cp["accepted_native_cases"]}件を全owner/Bag/party/ledger/Flash counterで照合。一般UI/通常新規ゲーム/V1 load adapter/phase0失敗は未受入。\n- Files changed: 専用C/validator/22負の試験/Actions、UTF8原本とcheckpoint、固定引継ぎMD/JSON、専用guide、両ログ。\n- Verify: 新unit22、native5、guard7、host compile1、ARM0、既受入再実行0。source binding/原本hash/保全path一致。resume/task graph/最終index scoped private guard後にのみcommit。\n- Commit: 同branch非force push。source={os.environ["GITHUB_SHA"]}、自己SHAはgit log参照。\n- Network: 固定GitHub artifact/PR/Actions metadataのみ。ROM/save非tracked、旧18取引/BP/P08/野生/baseline不変。Actions終端と全CI成功を自己確定しない。\n'
    for path in LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as f:f.write(log)
    owned=evidence|{CP,GUIDE,STATE,DOC}|LOGS
    write(OUT/'owned.json',sorted(owned))
    print(m.encode({'status':cp['status'],'accepted':cp['accepted_cases'],'failed':cp['failed_cases']}).decode())


def guard():
    os.chdir(ROOT)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(read(OUT/'owned.json'));g.guard()
    need(bindings(PROTECTED)==read(ROOT/CP)['protected_bindings'],'protected inputs unchanged before commit')
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['paths']:print('\n'.join(read(OUT/'owned.json')))
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('usage: measure|record|paths|guard')
