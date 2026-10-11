#!/usr/bin/env python3
"""採掘の新規3ケースだけをsource固定Actionsで測定。旧受入は再実行しない。"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_mining as b
import pr16_research_lifecycle_actions as d
import pr16_research_map_view as view
need,identity=b.need,b.identity
SELF='scripts/pr16_research_mining_capture.py'
WF='.github/workflows/pr16-research-mining-20260927.yml'
OUT=Path('.local/pr16-research-mining-capture')
PUBLIC=OUT/'public'


def capture():
    os.chdir(ROOT);d.current()
    need(not Path('content/modernization/pr16_research_mining_checkpoint.json').exists(),'recorded cases must not be rerun')
    need(not PUBLIC.exists(),'fresh bounded capture directory')
    PUBLIC.mkdir(parents=True);d.PUBLIC.mkdir(parents=True)
    cp=d.read('content/modernization/pr16_research_bug_checkpoint.json')
    need(cp['actions_completion_confirmed'] and cp['status']=='PASS_BUG_REAL_EARNING_SCOPED','accepted bug predecessor')
    own={SELF,WF,'scripts/pr16_research_mining.py',b.C,'tests/test_pr16_research_mining.py'}
    need(d.bindings(cp['source_bindings'])==cp['source_bindings'],'accepted dependencies unchanged')
    sources=d.bindings(set(cp['source_bindings'])|own)
    protected=d.bindings(d.PROTECTED|{'content/modernization/pr16_research_map_view_checkpoint.json','content/modernization/pr16_research_photo_checkpoint.json','content/modernization/pr16_research_bug_checkpoint.json'})
    result=dict(schema_version=1,environment='GitHub Actions; new measurement, not recovered local evidence',
        source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=sources,protected_bindings=protected,candidate=b.CANDIDATE,cases={},failures={},
        local_development='content/modernization/pr16_research_mining_local_development.json',
        counts=dict(rom_changes=0,arm_compiles=0,host_compiles=0,native_processes=0,accepted_case_reruns=0,accepted_native_processes=0,failed_native_processes=0),
        visual_review_pending=False,visual_method='original PPM hash equality to four locally vision-reviewed dialogue captures',all_activities_accepted=False,natural_arrival_accepted=False,release_ready=False)
    try:
        runtime,data,seed,candidate,artifacts=d.restore()
        import pr16_research_retry as retry
        import pr16_research_v1_corrupt_load as corrupt
        candidate,_=retry.apply(candidate,bytes.fromhex(d.read('content/modernization/pr16_research_retry_recipe.json')['after']))
        recipe=d.read('content/modernization/pr16_research_v1_corrupt_load_recipe.json')
        candidate,_=corrupt.apply(candidate,bytes.fromhex(recipe['after'])[:corrupt.CODE['size']])
        candidate,repair=view.apply(candidate)
        fixture,receipt=b.prior.photo.fixture(seed)
        result.update(physical=b.physical(candidate),fixture=receipt,runtime_artifacts=artifacts,reconstruction=repair)
        rom=OUT/'candidate.gba';rom.write_bytes(candidate)
        code=OUT/'runner.c';code.write_bytes(b.generate(seed));exe=OUT/'runner'
        command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.',
                 '-I'+str(runtime/'include'),str(code),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
        result['counts']['host_compiles']=1
        p=subprocess.run(command,capture_output=True,timeout=120)
        result['compile']=dict(returncode=p.returncode,stdout=p.stdout.decode(),stderr=p.stderr.decode(),
            generated_source=identity(code.read_bytes()),compiler=subprocess.check_output(['cc','--version']).decode(),command=command)
        need(p.returncode==0 and not p.stderr,'strict host compile')
        prefix=[str((runtime/'ld.so').resolve()),'--library-path',str((runtime/'lib').resolve()),str(exe.resolve())]
        for case in b.CASES:
            save=OUT/(case+'.srm');save.write_bytes(fixture)
            images=OUT/case;images.mkdir();start=time.monotonic()
            result['counts']['native_processes']+=1
            try:
                p=subprocess.run(prefix+[str(rom.resolve()),str(save.resolve()),case],cwd=images,capture_output=True,timeout=180)
                out,err=p.stdout,p.stderr;execution=dict(returncode=p.returncode,timeout=False)
            except subprocess.TimeoutExpired as exc:
                out,err=exc.stdout or b'',exc.stderr or b'';execution=dict(returncode=None,timeout=True)
            entry=dict(stdout=out.decode(),stderr=err.decode(),stdout_identity=identity(out),stderr_identity=identity(err),
                execution=execution,elapsed_seconds=round(time.monotonic()-start,3),generated_source=identity(code.read_bytes()))
            entry['screens']={p.name:identity(p.read_bytes()) for p in sorted(images.iterdir()) if p.suffix=='.ppm'}
            result['cases'][case]=entry
            try:
                need(execution['returncode']==0 and not execution['timeout'] and not err,'clean native process')
                entry['validated']=b.validate(out,case,fixture)
                need(entry['screens']=={r['screen']:{'size':115215,'sha256':r['sha256']} for r in entry['validated']['screens']},'exact full image inventory')
                result['counts']['accepted_native_processes']+=1
            except (ValueError,KeyError,TypeError) as exc:
                result['failures'][case]=dict(type=type(exc).__name__,reason=str(exc));result['counts']['failed_native_processes']+=1
            print(case,'PASS' if case not in result['failures'] else 'FAIL',flush=True)
        need(identity(rom.read_bytes())==b.CANDIDATE,'candidate unchanged')
        need(identity((data/'seed.srm').read_bytes())==identity(seed),'seed unchanged')
    except Exception as exc:
        result['failures']['preflight']=dict(type=type(exc).__name__,reason=str(exc))
    need(d.bindings(sources)==sources and d.bindings(protected)==protected,'source and accepted evidence unchanged')
    d.write(PUBLIC/'measurement.json',result)
    if not result['failures']:
        env=dict(os.environ,PR16_MINING_MEASUREMENT=str((PUBLIC/'measurement.json').resolve()))
        unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_mining.py','-v'],env=env,capture_output=True,timeout=120)
        count=(unit.stdout+unit.stderr).count(b' ... ok\n')
        result['unit']=dict(returncode=unit.returncode,passed=count,stdout=unit.stdout.decode(),stderr=unit.stderr.decode(),native_processes=0,compiles=0)
        if unit.returncode!=0 or count!=64:result['failures']['unit']={'reason':'64 new scoped tests required'}
    result['status']='PASS_MINING_MEASUREMENT_SCOPED' if not result['failures'] else 'FAIL_RECORDED'
    d.write(PUBLIC/'measurement.json',result)
    need(not result['failures'],'new measurement failure retained in artifact')


if __name__=='__main__':capture()
