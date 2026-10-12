#!/usr/bin/env python3
"""5ケース成功原本の記録専用。ROM/ARM/host compile/native/unit22は再実行しない。"""
from __future__ import annotations
import datetime, io, os, subprocess, sys, zipfile
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_lifecycle_v2 as v2
from pr16_learnset_compact_record import publish_resume
m=v2.m;d=v2.d;need=d.need;identity=d.identity
SELF='scripts/pr16_research_lifecycle_record.py'
TEST='tests/test_pr16_research_lifecycle_record.py'
WF='.github/workflows/pr16-research-lifecycle-record-20260926.yml'
RUN=36234024026
HEAD='17871a2bb5701a547594cd11b0ece35382ff0748'
ART=10903746636
BIND={'size':21244,'sha256':'e4f074ead5951f4c2976d9449848f38a55c22af8914f25fc1299ea4b62f08387'}
OUT=d.OUT;PUBLIC=d.PUBLIC
NEW={SELF,TEST,WF}


def public_member(name,raw):
    p=PurePosixPath(name)
    need(not p.is_absolute() and len(p.parts)==1 and '\\' not in name and '..' not in p.parts and name.endswith(('.txt','.json')),'safe bounded text member')
    text=raw.decode('utf-8');need('\0' not in text,'binary prohibited')
    if name=='previous-compile.stderr.txt':
        mapped=m.encode({'schema_version':1,'encoding':'utf-8','original_name':name,'original_binding':identity(raw),'text':text})
        return 'previous-compile.stderr.json',mapped
    return name,raw


def decode_public(raw):
    value=m.old.load(raw)
    need(set(value)=={'schema_version','encoding','original_name','original_binding','text'} and type(value['schema_version']) is int and value['schema_version']==1 and value['encoding']=='utf-8' and value['original_name']=='previous-compile.stderr.txt' and type(value['text']) is str,'exact reversible diagnostic schema')
    result=value['text'].encode('utf-8');need(identity(result)==value['original_binding'],'diagnostic reversible byte binding')
    return result


def measured_run():
    run=d.inputs.api('actions/runs/'+str(RUN));jobs=d.inputs.api('actions/runs/'+str(RUN)+'/jobs?per_page=5')['jobs']
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1,'preserved failed final whitespace check')
    need(len(jobs)==1 and jobs[0]['head_sha']==HEAD and [s['conclusion'] for s in jobs[0]['steps'][2:7]]==['success','success','success','failure','skipped'],'measurement/record/resume succeeded, final check failed, push skipped')
    return d.run_summary(run),jobs


def record():
    os.chdir(ROOT);d.current();need(not (ROOT/d.CP).exists(),'initial publication already exists')
    PUBLIC.mkdir(parents=True);run,jobs=measured_run()
    meta=d.inputs.api('actions/artifacts/'+str(ART));need(meta['workflow_run']['id']==RUN and meta['workflow_run']['head_sha']==HEAD and not meta['expired'],'measured artifact source')
    raw=d.inputs.api('actions/artifacts/'+str(ART)+'/zip',True);need(identity(raw)==BIND,'original complete archive')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist())==40 and len(set(z.namelist()))==40 and sum(e.file_size for e in z.infolist())==73102 and not any(e.is_dir() or e.external_attr>>28==10 for e in z.infolist()),'exact bounded archive')
        files={p:z.read(p) for p in z.namelist()}
    inv=m.old.load(files['invocation.json']);v=m.old.load(files['measurement.json'])
    need(inv['source_head']==v['source_head']==HEAD and v['run_id']==RUN and v['candidate']==d.bag.CANDIDATE and not v['failures'] and set(v['accepted'])==set(m.CASES),'closed five-case measurement')
    need(d.bindings(set(inv['source_bindings']))==inv['source_bindings'] and d.bindings(d.PROTECTED)==inv['protected_bindings'],'all measured source/protected identities unchanged')
    for case in m.CASES:
        result=m.validate(files[case+'.stdout.txt'],case)
        need(result==v['accepted'][case] and not files[case+'.stderr.txt'] and v['cases'][case]['returncode']==0 and not v['cases'][case]['timeout'],'native raw receipt '+case)
    for method in m.old.GUARDS:need(files[method+'.stdout.txt']==b'' and files[method+'.stderr.txt']==m.old.DENIED,'seven raw host-write denials')
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_lifecycle_record.py','-v'],capture_output=True,timeout=120)
    (PUBLIC/'record-unit.txt').write_bytes(unit.stdout+unit.stderr)
    need(unit.returncode==0 and (unit.stdout+unit.stderr).count(b' ... ok\n')==8,'eight new publication tests')
    directory=d.BASE+'/'+str(RUN);need(not (ROOT/directory).exists(),'immutable evidence publication')
    original={};published={}
    for name,value in files.items():
        mapped,content=public_member(name,value)
        if name=='previous-compile.stderr.txt':need(decode_public(content)==value,'lossless whitespace-preserving diagnostic')
        path=ROOT/directory/mapped;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        original[name]=identity(value);published[str(path.relative_to(ROOT))]=identity(content)
    extra={directory+'/publication.json':{'run':run,'jobs':jobs,'artifact_id':ART,'archive':BIND,'original_members':original,'published_members':published,'diagnostic_mapping':'UTF8 JSON string; exact roundtrip, no stripping; original ZIP unchanged'},directory+'/record-unit.txt':unit.stdout+unit.stderr}
    for path,value in extra.items():
        if isinstance(value,bytes):(ROOT/path).write_bytes(value)
        else:d.write(ROOT/path,value)
        published[path]=identity((ROOT/path).read_bytes())
    mp=directory+'/manifest.json';d.write(ROOT/mp,published)
    cp={'schema_version':1,'task':d.TASK,'status':'PASS_INITIAL_LIFECYCLE_5_SCOPED','candidate':d.bag.CANDIDATE,'source_head':HEAD,'run_id':RUN,'accepted_cases':list(m.CASES),'failed_cases':[],'accepted_native_cases':5,'fresh_cores':15,
        'measurement':directory+'/measurement.json','manifest':mp,'source_bindings':inv['source_bindings'],'protected_bindings':inv['protected_bindings'],'measurement_actions':run,
        'new_unit_tests':8,'reused_unit_tests':22,'native_processes_this_record':0,'native_processes_measured_once':5,'guard_processes_measured_once':7,'host_compiles_this_record':0,'arm_compiles':0,'accepted_case_reruns':0,
        'previous_compile_failure':v2.OLD_RUN,'record_run_id':int(os.environ['GITHUB_RUN_ID']),'record_source_head':os.environ['GITHUB_SHA'],'actions_completion_confirmed':False,
        'normal_new_game_or_transaction_ui_accepted':False,'v1_load_adapter_accepted':False,'phase0_failure_accepted':False,'release_ready':False,'active_baseline_changed':False,'issue19_complete':False}
    publish(cp,'record',set(published)|{mp})


def finalize():
    os.chdir(ROOT);d.current();PUBLIC.mkdir(parents=True)
    cp=d.read(ROOT/d.CP);need(not cp['actions_completion_confirmed'],'terminal receipt already accepted')
    run=d.inputs.api('actions/runs/'+str(cp['record_run_id']));jobs=d.inputs.api('actions/runs/'+str(cp['record_run_id'])+'/jobs?per_page=5')['jobs']
    need(run['head_sha']==cp['record_source_head'] and run['status']=='completed' and run['conclusion']=='success' and run['path']==WF and run['run_attempt']==1,'terminal record run')
    need(len(jobs)==1 and jobs[0]['conclusion']=='success' and all(s['conclusion']=='success' for s in jobs[0]['steps']),'all terminal record steps and nonforce push')
    manifest=d.read(ROOT/cp['manifest'])
    for p,b in manifest.items():need(identity((ROOT/p).read_bytes())==b,'immutable published evidence '+p)
    cp['actions_completion_confirmed']=True;cp['record_actions']=d.run_summary(run)
    path=d.BASE+'/record-terminal-'+str(run['id'])+'.json';d.write(ROOT/path,{'run':d.run_summary(run),'jobs':jobs,'new_native_processes':0,'new_unit_tests':0})
    publish(cp,'finalize',{path})


def publish(cp,mode,owned):
    d.write(ROOT/d.CP,cp)
    goal='研究保存初期化/V1 RAM移行の5ケースと15fresh coreを受入。次はphase0実失敗とV1 load adapter。成功済み5件/旧18境界/unit22は再実行しない。通常new-game/取引UI・全catalog・map3/19除外130行は別の未完境界。'
    state=d.read(ROOT/d.STATE);state['research_save_lifecycle']={'path':d.CP,'status':cp['status'],'candidate':cp['candidate'],'accepted_cases':cp['accepted_cases'],'run_id':cp['run_id'],'actions_completion_confirmed':cp['actions_completion_confirmed']}
    state['bp']['current_stop']=goal;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_PHASE0_FAILURE_AND_LOAD_NEXT',goal_ja=goal,read_paths=[d.GUIDE,d.CP,SELF,d.C,d.bag.SOURCE,d.save.CONFIG],stop_rule_ja='同一候補とsource/原本bindingを保持。RAMサービス試験を通常UI/new-game/V1保存loadへ昇格しない。phase!=0の既存故障flagをphase0故障と扱わない。既受入nativeの再実行禁止。merge/release/baseline切替禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='今回記録source HEAD。native測定は専用checkpointの17871a2b/run36234024026、自己commitはgit logで照合。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[cp['measurement_actions']]+([cp['record_actions']] if cp.get('record_actions') else []),'reason_ja':'native5件はPASS、元runは末尾空白diff check failureを保持。記録成功と全CI成功を区別する。'}
    guide='# PR16 研究保存lifecycle限定受入\n\n'+goal+'\n\n## 結果\n\n候補4aee03e8、測定source17871a2b、run36234024026。空/消去済み初期化、正常V1 RAM移行、V1 checksum不正拒否、V1 tail不正拒否の5件PASS。保存counterは成功系2→3→3→3、拒否系2→2→2→2。全64byte owner/Bag/party/2KiB ledgerと独立core Continue2回を照合。通常new-game全体、V1保存の通常load、phase0失敗、通常取引UIは未受入。\n\n## buildと履歴\n\n初回run36233675420はmainマクロ衝突のcompile failure、native0。次runは外側main宣言だけを生成時改名し旧runner/productionを不変にしてstrict compile成功。22unit原本をsource hash一致で再利用、native5/guard7を一度だけ実行。次run終端は過去compiler原本の末尾空白でdiff check failure。原本を削らずUTF8 JSON文字列へ可逆写像し、原本ZIP/hashを保持して記録する。公開写像8新unit、記録native/compile/ARM0。\n\n## 再開\n\n専用checkpointとmanifestに固定原本・全member/source hash・失敗runの状態を保持。Actions記録終端確認: '+str(cp['actions_completion_confirmed'])+'。BP/P08/特殊野生/active baselineは不変。\n'
    (ROOT/d.GUIDE).write_text(guide)
    for p in NEW|{d.CP,d.GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['source_bindings'].update(cp['source_bindings']);state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {d.TASK}\n- Version: research-lifecycle-record-{mode}-v1\n- Status: DONE（初期化/V1 RAM限定5境界、phase0故障/V1 loadは未完）\n- Summary: {goal}\n- Files changed: 専用build/validator/公開写像/8試験/Actions、原本とmanifest/checkpoint、固定引継ぎMD/JSON、guide、両ログ。\n- Verify: 測定native5/15cores/guard7はrun36234024026を再利用。unit22はrun36233675420を再利用。公開写像8新unitはrecordのみ。今回native0/compile0/ARM0。失敗原本をsuccessに改作せず保持。resume check/task graph/scoped final-index guard/diff check後にcommit。\n- Commit: 同branch非force push。source={os.environ["GITHUB_SHA"]}、自己SHAはgit log参照。\n- Network: 固定GitHub UTF8証拠artifactのみ。ROM/save非tracked、旧18/BP/P08/特殊野生/baseline不変、全CI成功を主張しない。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(log)
    d.write(OUT/'owned.json',sorted(owned|{d.CP,d.GUIDE,d.STATE,d.DOC}|d.LOGS));print(cp['status'],mode)


if __name__=='__main__':
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:d.guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(d.read(OUT/'owned.json')))
    else:raise SystemExit('usage: record|finalize|guard|paths')
