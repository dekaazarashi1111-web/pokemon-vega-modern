#!/usr/bin/env python3
"""母親回復の新規測定と、再測定しない終端回収・非force記録。"""
from __future__ import annotations
import datetime
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_home_recovery_native as m
import pr16_research_story_route_actions as h
from pr16_learnset_compact_record import publish_resume

d=h.d
TASK='USER-20260928-HOME-RECOVERY'
SELF='scripts/pr16_home_recovery_native_actions.py'
WF='.github/workflows/pr16-home-recovery-native.yml'
SOURCE_WF='.github/workflows/pr16-home-recovery-native-source.yml'
TERM_WF='.github/workflows/pr16-home-recovery-terminal.yml'
GUIDE='docs/PR16_HOME_RECOVERY_JA.md'
SOURCE_CP='content/modernization/pr16_home_recovery_checkpoint.json'
CP='content/modernization/pr16_home_recovery_native_checkpoint.json'
TERMINAL='content/modernization/pr16_home_recovery_native_terminal.json'
OUT=ROOT/'.local/pr16-home-native-run'
PUBLIC=OUT/'public'
ART=OUT/'checkpoint'
NAME='pr16-home-recovery-native-checkpoint'
CODE={SELF,m.SOURCE,m.TEST,WF,SOURCE_WF}
GOAL='母親との元会話でHP13/23→23/23・麻痺解消・ひっかくPP31→35、通常Save5→6と独立Continueのparty/Flash/4画面保持を限定受入。次はartifactのrecovery.srmを作業コピーとして通常ストーリーへ。map4/0 (8,5)、Lv7/EXP245、RP0、キズぐすり0。母親81入力と旧194/367/301/114入力・starter/RP/UI/BP/P08は再生しない。渡航16条件はstatic検証で、解禁後実渡航native・研究施設自然到達・全ストーリー・releaseは未完。'


def put(path,value):d.write(path,value)


def dev_verified():
    folder=ROOT/m.DEV;proof=d.read(folder/'verification.json')
    m.need(d.bindings(set(proof['source_bindings']))==proof['source_bindings'],'new oracle exact tested source')
    m.need(d.bindings(set(proof['evidence_bindings']))==proof['evidence_bindings'],'new oracle exact test originals')
    unit=(folder/'unit.stderr.txt').read_bytes()
    m.need(proof['unit_tests']==73 and unit.count(b' ... ok\n')==73 and b'\nOK\n' in unit and b'FAILED' not in unit and b'skipped' not in unit and not (folder/'unit.stdout.txt').read_bytes(),'73 new tests reused without rerun')
    result=m.verify((folder/'progress.stdout.txt').read_bytes(),(folder/'continue.stdout.txt').read_bytes(),d.read(ROOT/m.PARENT),m.OUTPUT_SAVE,d.read(folder/'visual-review.json'))
    m.need(result==d.read(folder/'result.json'),'all developed observations and clock boundaries')
    return proof


def archived(number,expected,maxsize):
    meta=d.inputs.api('actions/artifacts/'+str(number))
    m.need(meta['id']==number and meta['expired'] is False and meta['size_in_bytes']==expected['size'] and meta['digest']=='sha256:'+expected['sha256'],'pinned artifact metadata')
    raw=d.inputs.api('actions/artifacts/'+str(number)+'/zip',True)
    m.need(m.identity(raw)==expected,'whole artifact bytes')
    put(PUBLIC/(str(number)+'.json'),{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    return h.safe_zip(raw,maxsize),meta


def run_terminal(number,source,job_name):
    run=d.inputs.api('actions/runs/'+str(number))
    m.need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==source and run['head_branch']=='codex/modernization-followup-20260908' and run['run_attempt']==1,'successful exact source run')
    jobs=d.inputs.api('actions/runs/'+str(number)+'/jobs?per_page=100')
    m.need(jobs['total_count']==len(jobs['jobs'])==1,'one complete job')
    job=jobs['jobs'][0]
    m.need(job['name']==job_name and job['status']=='completed' and job['conclusion']=='success','job terminal')
    m.need(len(job['steps'])>7 and all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'every required step actually succeeded')
    return dict(run=d.run_summary(run),job_id=job['id'],steps=[{k:s[k] for k in ('name','number','status','conclusion')} for s in job['steps']])


def restore():
    proof=run_terminal(m.BUILD_RUN,m.BUILD_HEAD,'source');put(PUBLIC/'source-build-terminal.json',proof)
    z,meta=archived(m.BUILD_ARTIFACT,m.BUILD_ARCHIVE,40000000)
    m.need(meta['workflow_run']['id']==m.BUILD_RUN and meta['workflow_run']['head_sha']==m.BUILD_HEAD,'build artifact origin')
    with z:
        m.need(set(z.namelist())=={'candidate.gba','training.srm','runner','checkpoint.json','completion-head.txt','record.zip'},'closed build archive')
        m.need(z.read('completion-head.txt').decode().strip()==m.BUILD_COMMIT,'build non-force completion')
        cp=m.load(z.read('checkpoint.json'));m.need(cp==d.read(ROOT/SOURCE_CP),'exact source checkpoint')
        m.need(d.bindings(set(cp['source_bindings']))==cp['source_bindings'],'52 tested sources/evidence not changed')
        for name,want in [('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('training.srm',m.INPUT_SAVE)]:
            raw=z.read(name);m.need(m.identity(raw)==want,'fixed '+name);(OUT/name).write_bytes(raw)
    (OUT/'runner').chmod(0o755);(OUT/'candidate.gba').chmod(0o444)
    spec=dict(size=102586759,sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d')
    z,meta=archived(10898620034,spec,250000000)
    m.need(meta['workflow_run']['id']==36218655601,'fixed runtime origin')
    runtime=OUT/'runtime';runtime.mkdir()
    with z:
        m.need(len(z.namelist())==333 and sum(i.file_size for i in z.infolist())==240469427,'fixed runtime members')
        for n in z.namelist():
            p=runtime/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA bytes')
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    return runtime


def preserve():
    ART.mkdir(parents=True,exist_ok=True)
    for name in ('progress','continue'):
        where=OUT/name
        if where.exists():
            dest=ART/name;dest.mkdir(exist_ok=True)
            for p in where.iterdir():
                if p.is_file():shutil.copy2(p,dest/p.name)
    if PUBLIC.exists():shutil.copytree(PUBLIC,ART/'public',dirs_exist_ok=True)
    for name in ('runner','candidate.gba'):
        if (OUT/name).exists():
            from pr16_home_recovery_collect import copy_immutable
            copy_immutable(OUT/name,ART/name)


def invoke(runtime,name,saved,commands):
    where=OUT/name;where.mkdir();working=where/'story.srm';working.write_bytes(saved)
    (where/'commands.txt').write_bytes(commands)
    cmd=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(OUT/'runner'),str(OUT/'candidate.gba'),str(working),'continue-story',m.identity(saved)['sha256']]
    with (PUBLIC/(name+'.stdout.txt')).open('wb') as out,(PUBLIC/(name+'.stderr.txt')).open('wb') as err:
        p=subprocess.run(cmd,cwd=where,input=commands,stdout=out,stderr=err,timeout=180)
    raw=(PUBLIC/(name+'.stdout.txt')).read_bytes();errors=(PUBLIC/(name+'.stderr.txt')).read_bytes()
    put(PUBLIC/(name+'.execution.json'),dict(returncode=p.returncode,initial=m.identity(saved),final=m.identity(working.read_bytes()),stdout=m.identity(raw),stderr=m.identity(errors)))
    preserve();m.need(p.returncode==0 and not errors,'native failure retained; no blind replay')
    return raw,working,where


def measure():
    os.chdir(ROOT);d.current();m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/CP).exists(),'first new run only')
    state=h.source_check();dev_verified();PUBLIC.mkdir(parents=True);ART.mkdir()
    runtime=restore();saved=(OUT/'training.srm').read_bytes();dev=ROOT/m.DEV
    raw,first,where=invoke(runtime,'progress',saved,(dev/'commands.txt').read_bytes())
    m.need(raw==(dev/'progress.stdout.txt').read_bytes() and m.identity(first.read_bytes())==m.OUTPUT_SAVE,'ordinary source-compiled run exactly reproduces all new recovery observations')
    shutil.copy2(first,ART/'recovery.srm')
    cold,coldsave,coldwhere=invoke(runtime,'continue',first.read_bytes(),(dev/'continue-commands.txt').read_bytes())
    m.need(cold==(dev/'continue.stdout.txt').read_bytes(),'independent cold all observations reproduce')
    result=m.verify(raw,cold,d.read(ROOT/m.PARENT),m.identity(first.read_bytes()),d.read(dev/'visual-review.json'),where,coldwhere)
    proof=m.saved_bytes(saved,first.read_bytes(),coldsave.read_bytes());m.need(proof==d.read(dev/'save-byte-proof.json'),'entire Save/party delta/clock proof')
    for name,want in [('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('training.srm',m.INPUT_SAVE)]:m.need(m.identity((OUT/name).read_bytes())==want,'original remains unchanged: '+name)
    m.need(d.bindings(set(state['source_bindings']))==state['source_bindings'],'all accepted sources/evidence unchanged')
    put(PUBLIC/'save-byte-proof.json',proof)
    checkpoint=dict(schema_version=1,candidate=m.CANDIDATE,save=m.OUTPUT_SAVE,executable=m.RUNNER,runtime_artifact=10898620034,build_artifact=m.BUILD_ARTIFACT,parent_artifact=10946201851,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),frame=6642,map=[4,0],xy=[8,5],party_count=1,rp=0,save_counter=6,level=7,experience=245,hp=[23,23],status_condition=0,moves_pp=[35,30,25],native_bag_potion_count=0,mode='continue-story',commands='quit\n',new_game_replay_required=False,completed_recovery_replay_required=False,natural_research_arrival_accepted=False)
    put(ART/'checkpoint.json',checkpoint)
    put(PUBLIC/'measurement.json',dict(**result,checkpoint=checkpoint,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),host_compiles=0,arm_compiles=0,accepted_case_reruns=0,source_tests_reused=52,new_oracle_tests_reused=73,new_unit_executions=0,development_processes=2,formal_processes=2,binary_rewriting=False))
    preserve();print('PASS: natural mother recovery, ordinary Save5->6, independent Continue, no release/travel-native claim')


def observed_checks(state):
    runs=d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=50')
    m.need(runs['total_count']==len(runs['workflow_runs'])<=50,'complete current run list')
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=[d.run_summary(r) for r in runs['workflow_runs']],reason_ja='一般CI failure/action_required/実行中は原値のまま。専用回復受入やreleaseとは別。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs['workflow_runs'] if r['status'] in ('queued','in_progress')]


def publish(state,owned,status,terminal=False):
    state['home_recovery_native']=dict(path=CP,status=status,candidate=m.CANDIDATE,ordinary_recovery_accepted=True,natural_research_arrival_accepted=False,retained_artifact_name=NAME)
    state['bp']['current_stop']=status;state['bp']['next_step']=GOAL
    state['next_action']=dict(state['next_action'],id='STORY_AFTER_HOME_RECOVERY_SAVE_NEXT' if terminal else 'HOME_RECOVERY_TERMINAL_ONLY_NEXT',goal_ja=GOAL,read_paths=[GUIDE,CP,TERMINAL if terminal else SOURCE_CP,m.DEV+'/save-byte-proof.json'],stop_rule_ja='正式native runがある場合は全必須step/artifact/commitだけ回収し再生しない。終端確認後はrecovery.srmの作業コピーから新しい通常進行だけ。母親81入力/cold34入力/旧194/367/301/114を再生しない。merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0,'母親回復は '+CP+'。新候補でSave counter6。回復81/cold34入力は完走済み、次は終端回収またはrecovery.srmから新しい進行のみ。')
    for n in owned-{d.STATE,d.DOC}-d.LOGS:state['source_bindings'][n]=m.identity((ROOT/n).read_bytes())
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='回復専用source/終端収集の出発HEAD。通常Saveの候補SHAと製品baselineは区別する。'
    state['logs_synchronized']=True;observed_checks(state);publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 母親の通常回復と保存Continue\n- Version: home-recovery-native-v1\n- Status: DONE（回復区間限定、研究施設自然到達/実渡航/全体は未完）\n- Summary: {GOAL}\n- Files changed: 専用oracle/test/原本JSON/MD/固定引継ぎ/両ログ。binaryはartifactのみ。\n- Verify: source52 tests再利用、new oracle73 tests原本再利用。回復81inputs/6642frames+独立Continue34inputs/2572frames、26画面/4UI組、party600bytes中回復3bytesだけ/597bytes保持、全Save+RTC保持。RAM ledgerは分32→33/checksumだけで全2048byte SHA一致。\n- Accounting: この記録段階の追加native={0 if terminal or os.environ.get("PR16_HOME_COLLECTION_ONLY") == "1" else 2}、追加compile=0、旧受入再実行=0。開発探索2processは正式2processと別計上。初期の実行ファイル文字列更新方式は採用せず、正式はsourceから通常compileされたartifact runnerのみ。初回新oracle73件中3不具合を修正後73PASS。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={os.environ["GITHUB_RUN_ID"]}; same-branch non-force。\n- Network: fixed GitHub artifacts/API。全体private guard/一般CI全成功/merge/release/baseline切替は主張しない。\n'
    for n in d.LOGS:
        with (ROOT/n).open('a') as f:f.write(entry)


def record():
    os.chdir(ROOT);d.current();m.need(not (ROOT/CP).exists(),'no duplicate acceptance')
    state=h.source_check();measured=d.read(PUBLIC/'measurement.json')
    base='content/modernization/pr16_home_recovery_native_evidence/'+os.environ['GITHUB_RUN_ID'];target=ROOT/base;target.mkdir(parents=True)
    for p in PUBLIC.iterdir():
        if p.is_file():p.read_bytes().decode('utf-8');shutil.copy2(p,target/p.name)
    paths=CODE|{str(p.relative_to(ROOT)) for p in (ROOT/m.DEV).iterdir() if p.is_file()}|{str(p.relative_to(ROOT)) for p in target.iterdir()}
    cp=dict(measured,actions_completion_confirmed=False,retained_artifact_id=None,retained_artifact_name=NAME,source_bindings=d.bindings(paths),visual_review=m.DEV+'/visual-review.json',save_proof=base+'/save-byte-proof.json')
    put(ROOT/CP,cp)
    with (ROOT/GUIDE).open('a') as f:f.write('\n## 母親の自然回復・Save・独立Continue\n\n'+GOAL+'\n\n正式source `'+os.environ['GITHUB_SHA']+'` / run `'+os.environ['GITHUB_RUN_ID']+'`。81入力/19画面でSave5→6、別core34入力/7画面。全Save131088bytes SHA '+m.OUTPUT_SAVE['sha256']+'。600partybytes中ひっかくPP/麻痺/HPの3bytesだけが変化、残り597bytes不変。RAM ledger分32→33とチェックサムは全byte SHAから確認し、残高や他ownerの改変と区別した。終端artifact/全必須stepの外部確認は次段階。\n')
    owned=paths|{GUIDE,CP,d.STATE,d.DOC}|d.LOGS
    publish(state,owned,cp['status'])
    put(OUT/'owned.json',sorted(owned));put(OUT/'guard-base.json',m.BUILD_COMMIT)


def guard():
    import pr16_learnset_runtime_record as g
    paths=d.read(OUT/'owned.json');subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    g.START=d.read(OUT/'guard-base.json');g.CODE=set();g.OWNED=set(paths);g.guard()


def snapshot():
    paths=d.read(OUT/'owned.json')
    with zipfile.ZipFile(ART/'record.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n in paths:z.write(ROOT/n,n)
    (ART/'completion-head.txt').write_bytes(d.git('rev-parse','HEAD'))


def terminal():
    os.chdir(ROOT);d.current();state=h.source_check();cp=d.read(ROOT/CP)
    m.need(cp['actions_completion_confirmed'] is False,'terminal collection once only')
    PUBLIC.mkdir(parents=True);ART.mkdir()
    proof=run_terminal(cp['run_id'],cp['source_head'],'recovery')
    reply=d.inputs.api('actions/runs/'+str(cp['run_id'])+'/artifacts?per_page=100')
    m.need(reply['total_count']==len(reply['artifacts'])==1,'single full native artifact')
    meta=reply['artifacts'][0]
    m.need(meta['name']==NAME and meta['expired'] is False and meta['workflow_run']['head_sha']==cp['source_head'],'native artifact source/name')
    expected=dict(size=meta['size_in_bytes'],sha256=meta['digest'].removeprefix('sha256:'))
    z,again=archived(meta['id'],expected,50000000);m.need(meta==again,'artifact metadata stable')
    with z:
        completion=z.read('completion-head.txt').decode().strip();m.need(len(completion)==40,'completion SHA')
        subprocess.run(['git','merge-base','--is-ancestor',completion,'HEAD'],cwd=ROOT,check=True)
        m.need(m.load(z.read('checkpoint.json'))==cp['checkpoint'],'exact retained checkpoint')
        for n,want in [('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('recovery.srm',m.OUTPUT_SAVE),('progress/story.srm',m.OUTPUT_SAVE),('continue/story.srm',m.OUTPUT_SAVE)]:m.need(m.identity(z.read(n))==want,'native retained '+n)
        for name,count in [('progress',19),('continue',7)]:
            trace=m.trace(z.read('public/'+name+'.stdout.txt'))
            for image in trace['screens']:
                raw=z.read(name+'/screen-%04d.ppm'%image['screen']);m.need(m.identity(raw)==dict(size=115215,sha256=image['sha256']),'native actual retained screen')
            m.need(len(trace['screens'])==count and not z.read('public/'+name+'.stderr.txt'),'all screens/no error')
        result=m.verify(z.read('public/progress.stdout.txt'),z.read('public/continue.stdout.txt'),d.read(ROOT/m.PARENT),m.OUTPUT_SAVE,d.read(ROOT/m.DEV/'visual-review.json'))
        m.need(all(cp[k]==v for k,v in result.items()),'terminal result matches measured acceptance')
        with h.safe_zip(z.read('record.zip'),25000000) as record:
            for n,v in cp['source_bindings'].items():m.need(m.identity(record.read(n))==v and m.identity((ROOT/n).read_bytes())==v,'immutable tested/native text original '+n)
            m.need(record.read(CP)==(ROOT/CP).read_bytes(),'completion native checkpoint byte identity')
    proof.update(schema_version=1,completion_commit=completion,artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},new_native_processes=0,new_unit_executions=0,new_compiles=0,save_copies_verified=3,real_screens_verified=26,immutable_tested_bindings_verified=len(cp['source_bindings']),release_ready=False,active_baseline_changed=False)
    put(ROOT/TERMINAL,proof)
    cp['actions_completion_confirmed']=True;cp['retained_artifact_id']=meta['id'];cp['retained_artifact']=proof['artifact'];cp['terminal']=TERMINAL;cp['completion_commit']=completion
    put(ROOT/CP,cp)
    source=d.read(ROOT/SOURCE_CP);source['actions_completion_confirmed']=True;source['retained_artifact_id']=m.BUILD_ARTIFACT;source['completion_commit']=m.BUILD_COMMIT
    put(ROOT/SOURCE_CP,source)
    with (ROOT/GUIDE).open('a') as f:f.write('\n## 外部終端確認済み\n\nrun '+str(cp['run_id'])+'、job '+str(proof['job_id'])+'、全'+str(len(proof['steps']))+'必須step成功。completion '+completion+'。artifact '+str(meta['id'])+' の全ZIP/26実画面/3Save/runner/候補/commit textを検証。追加native/compile/unit0。これより上の終端待ちは記録時点の履歴。現在の再開点はrecovery.srmで、回復区間を再生しない。\n')
    owned={TERM_WF,GUIDE,CP,SOURCE_CP,TERMINAL,d.STATE,d.DOC}|d.LOGS
    publish(state,owned,cp['status'],True)
    put(OUT/'owned.json',sorted(owned));put(OUT/'guard-base.json',completion)
    put(ART/'terminal.json',proof)


if __name__=='__main__':
    m.need(len(sys.argv)==2 and sys.argv[1] in ('measure','record','guard','preserve','snapshot','terminal'),'closed action')
    globals()[sys.argv[1]]()
