#!/usr/bin/env python3
"""研究wildの未受入2経路を実装・実測し、成功/失敗原本を毎回checkpoint保存する。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_bug as b
import pr16_research_lifecycle_actions as d
import pr16_research_map_view as view
need,identity=b.need,b.identity
START='67387dec640536bf12e20736e6803cf8771863b8'
TASK='USER-20260927-RESEARCH-WILD'
SELF='scripts/pr16_research_wild_capture.py'
C='tools/mgba_pr16_research_wild.c'
WF='.github/workflows/pr16-research-wild-20260927.yml'
CODE={SELF,C,WF}
CP='content/modernization/pr16_research_wild_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_WILD_JA.md'
MINING='content/modernization/pr16_research_mining_checkpoint.json'
OUT=Path('.local/pr16-research-wild');PUBLIC=OUT/'public'
METHODS=('fishing','ecology')


def measure():
    os.chdir(ROOT);d.current();need(not OUT.exists(),'fresh bounded execution')
    PUBLIC.mkdir(parents=True);d.OUT=OUT/'restore';d.PUBLIC=d.OUT/'public';d.PUBLIC.mkdir(parents=True)
    cp=d.read(MINING)
    need(cp['actions_completion_confirmed'] and cp['candidate']==b.CANDIDATE,'accepted current predecessor')
    need(d.bindings(cp['source_bindings'])==cp['source_bindings'],'accepted source unchanged')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'accepted evidence unchanged')
    tracked=d.git('ls-files').decode().splitlines()
    need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')],'nested rule review')
    if Path(CP).exists():
        prior=d.read(CP);need(not prior.get('actions_completion_confirmed',False),'accepted research wild may not rerun')
    sources=d.bindings(set(cp['source_bindings'])|CODE)
    protected=d.bindings(set(cp['protected_bindings'])|{MINING,'scripts/pr16_research_followup_20260927.py','tests/test_pr16_research_followup_20260927.py','content/modernization/pr16_research_remaining_evidence/36273404788/source-contract.json'})
    result=dict(schema_version=1,task=TASK,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=sources,protected_bindings=protected,candidate=b.CANDIDATE,cases={},failures={},
                counts=dict(host_compiles=0,arm_compiles=0,native_processes=0,guard_processes=0,accepted_case_reruns=0,rom_changes=0),actions_completion_confirmed=False,native_acceptance=False,natural_arrival_accepted=False,all_activities_accepted=False)
    try:
        runtime,data,seed,candidate,artifacts=d.restore()
        import pr16_research_retry as retry
        import pr16_research_v1_corrupt_load as corrupt
        candidate,_=retry.apply(candidate,bytes.fromhex(d.read('content/modernization/pr16_research_retry_recipe.json')['after']))
        recipe=d.read('content/modernization/pr16_research_v1_corrupt_load_recipe.json')
        candidate,_=corrupt.apply(candidate,bytes.fromhex(recipe['after'])[:corrupt.CODE['size']]);candidate,reconstruction=view.apply(candidate)
        need(identity(candidate)==b.CANDIDATE,'unchanged candidate reconstruction')
        fixture,receipt=b.photo.fixture(seed);result.update(fixture=receipt,runtime_artifacts=artifacts,reconstruction=reconstruction)
        rom=OUT/'candidate.gba';rom.write_bytes(candidate);source=b.generate(seed).decode();token='int main(int argc,char**argv){'
        need(source.count(token)==1,'one inherited main, never executed')
        source=source.replace(token,'int accepted_bug_main(int argc,char**argv){')+'\n'+Path(C).read_text()
        code=OUT/'runner.c';code.write_text(source);exe=OUT/'runner'
        command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(code),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
        result['counts']['host_compiles']=1;p=subprocess.run(command,capture_output=True,timeout=120)
        result['compile']=dict(returncode=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode(),generated_source=identity(code.read_bytes()),command=command,compiler=subprocess.check_output(['cc','--version']).decode())
        need(p.returncode==0 and not p.stderr,'strict new host compile')
        prefix=[str((runtime/'ld.so').resolve()),'--library-path',str((runtime/'lib').resolve()),str(exe.resolve())]
        result['guards']={}
        for method in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
            p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=10);result['counts']['guard_processes']+=1
            result['guards'][method]=dict(returncode=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode())
            need(p.returncode==1 and not p.stdout and p.stderr==b'research-save-impact: host write after observation barrier\n','new executable write guard '+method)
        for method in METHODS:
            save=OUT/(method+'.srm');save.write_bytes(fixture);images=PUBLIC/method;images.mkdir();start=time.monotonic();result['counts']['native_processes']+=1
            try:
                p=subprocess.run(prefix+[str(rom.resolve()),str(save.resolve()),method],cwd=images,capture_output=True,timeout=240)
                out,err=p.stdout,p.stderr;execution=dict(returncode=p.returncode,timeout=False)
            except subprocess.TimeoutExpired as exc:
                out,err=exc.stdout or b'',exc.stderr or b'';execution=dict(returncode=None,timeout=True)
            entry=dict(stdout=out.decode(),stderr=err.decode(),stdout_identity=identity(out),stderr_identity=identity(err),execution=execution,elapsed_seconds=round(time.monotonic()-start,3),private_save=identity(save.read_bytes()),generated_source=identity(code.read_bytes()),screens={p.name:identity(p.read_bytes()) for p in sorted(images.glob('*.ppm'))})
            result['cases'][method]=entry
            if execution['returncode']!=0 or execution['timeout'] or err:result['failures'][method]=dict(reason='native process did not satisfy strict success',execution=execution)
            print('NEW_NATIVE',method,'MEASURED_PENDING_ORACLE' if method not in result['failures'] else 'FAILED',flush=True)
        need(identity(rom.read_bytes())==b.CANDIDATE and identity((data/'seed.srm').read_bytes())==identity(seed),'input bytes preserved')
    except Exception as exc:
        result['failures']['preflight']=dict(type=type(exc).__name__,reason=str(exc))
    need(d.bindings(sources)==sources and d.bindings(protected)==protected,'all source and accepted evidence preserved')
    d.write(PUBLIC/'measurement.json',result)
    base='content/modernization/pr16_research_wild_evidence/'+str(result['run_id'])
    d.write(base+'/measurement.json',result)
    for method,entry in result['cases'].items():
        Path(base+'/'+method+'.stdout.txt').write_text(entry['stdout']);Path(base+'/'+method+'.stderr.txt').write_text(entry['stderr'])
    status='STOPPED_RESEARCH_WILD_NATIVE' if result['failures'] else 'RESEARCH_WILD_MEASURED_ORACLE_REVIEW_PENDING'
    checkpoint=dict(status=status,task=TASK,measurement=base+'/measurement.json',source_head=result['source_head'],run_id=result['run_id'],candidate=b.CANDIDATE,counts=result['counts'],failures=result['failures'],source_bindings=sources,protected_bindings=protected,actions_completion_confirmed=False,native_acceptance=False,accepted_cases=[])
    d.write(CP,checkpoint)
    goal='研究wild専用Cを実装し、釣り/生態の通常Bag→逃走→捕獲→取引保存Continueを新規実測。'+('失敗原本から未完境界だけ修正する。' if result['failures'] else '実測原本に独立oracle/負例検査と画像照合を追加し、完了Actionsを照合して限定受入する。')+'旧受入済み写真/虫取り/採掘/BP/P08/special-wildケースは再実行しない。ゲームコーナー/通常進行の受付ショップ接続/未確認文言は未完。'
    Path(GUIDE).write_text('# PR16 研究wild実稼得\n\n'+goal+'\n\n状態: `'+CP+'`\n原本: `'+base+'/measurement.json`\n\n開始map/lead/道具/進行はfixture。RNG・敵・結果・RPは注入しない。barrier後は通常入力のみ。取引2saveだけのfresh Continueを対象とし、手動Saveで保存欠陥を隠さない。\n\nこの記録時点では自己Actions未終端・独立oracle未完であり、新しいnative受入は0。`counts`と`failures`を正本とする。成功したscopeも受入確定前に無意味に再実行しない。\n',encoding='utf-8')
    state=d.read(d.STATE);state['research_wild']=dict(path=CP,status=status,measurement=base+'/measurement.json',source_head=result['source_head'],run_id=result['run_id'],native_acceptance=False)
    state['bp']['current_stop']=status;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_WILD_NATIVE_REPAIR_OR_ACCEPT',goal_ja=goal,read_paths=[GUIDE,CP,base+'/measurement.json',C,SELF,'content/research_economy_v1/canonical_model.json'])
    runs=d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=20')['workflow_runs']
    d.write(base+'/actions.json',[d.run_summary(r) for r in runs])
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='研究wild新規実測のsource。自己Actionsの終端と独立oracleは未確認として保存。'
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=[d.run_summary(r) for r in runs],reconciliation=base+'/actions.json',reason_ja='native実測失敗/成功と一般CIを分離。自己runの終端は後続で確認。')
    state['pending_runs']=[dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs if r['status'] in ('queued','in_progress')]
    for p in CODE|{CP,GUIDE,base+'/measurement.json'}:state['source_bindings'][p]=identity(Path(p).read_bytes())
    now=datetime.datetime.now(datetime.timezone.utc);state['observed_date_jst']=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat();state['logs_synchronized']=True
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    log=f'\n## {now.isoformat()}\n- Timestamp: {now.isoformat()}\n- Task: {TASK}\n- Version: research-wild-native-v1\n- Status: STOPPED（実装/実測を保存、受入未確定）\n- Summary: {goal}\n- Files changed: 専用C/実測script/workflow、実測原本/checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n- Verify: counts={result["counts"]}; failures={result["failures"]}; 新受入0、旧受入native再実行0。source/evidence/ROM/seedのSHA照合。resume/task graph/scoped guard後だけcommit。\n- Commit: source={os.environ["GITHUB_SHA"]}; run={result["run_id"]}; 自己SHAはgit log参照。同branch非force push。\n- Network: 固定GitHub artifacts/HEAD/PR/Actionsだけ。merge/release/baseline変更なし。\n'
    for p in d.LOGS:
        with Path(p).open('a',encoding='utf-8') as f:f.write(log)
    owned={str(p) for p in Path(base).iterdir()}|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS
    d.write(OUT/'owned.json',sorted(owned));print('CHECKPOINT',status,'COUNTS',result['counts'],'FAILURES',result['failures'],flush=True)


def guard():
    import pr16_learnset_runtime_record as g
    cp=d.read(CP);need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'accepted protected bytes')
    need(d.bindings(cp['source_bindings'])==cp['source_bindings'],'exact measured source')
    owned=set(d.read(OUT/'owned.json'));subprocess.run(['git','add','--',*sorted(owned)],check=True)
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    changed=set(d.git('diff','--cached','--name-only',START).decode().splitlines());need(changed<=owned|CODE,'complete explicit task scope')
    g.START=START;g.CODE=changed-owned;g.OWNED=owned;g.guard();subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('measure | guard')
