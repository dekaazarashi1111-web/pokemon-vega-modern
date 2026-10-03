#!/usr/bin/env python3
"""First Actions measurement of the new Maori interval; never replays old acceptance."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_fast_maori as m
import pr16_research_story_route_actions as transport
OUT=ROOT/'.local/pr16-story-fast-maori'
ART=OUT/'artifact'
WF='.github/workflows/pr16-story-fast-maori.yml'
SELF='scripts/pr16_story_fast_maori_measure.py'
CODE={m.SOURCE,m.TEST,SELF,WF,m.DEV+'/commands.txt',m.DEV+'/continue-commands.txt',m.DEV+'/measurement.json'}
LOCAL={m.SOURCE:dict(size=12364,sha256='3add6d4ff7d2a0840085a398cfa3164bc4c11d11ceb5ef92caa26ab11c4bfa80'),
       m.TEST:dict(size=8337,sha256='020fd8cbe7d465949740fa200dfcfee20aefa3587ce2b744c07816f5bb203f8b')}
ARCHIVES=[(10999218544,36487441645,18749112,'963867cd062156378135838c420091a0b553fab77a5732c77e80e15e47483c3e'),
 (11005890195,36500700863,486268,'051cf9d3746ebd5bc6a6b28a225d791b30f8bb1acca6ed214ccb91ed9854b4b5'),
 (10898620034,36218655601,102586759,'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d')]


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def bindings(paths):return {p:m.identity((ROOT/p).read_bytes()) for p in sorted(paths)}


def archive(spec):
    number,run,size,sha=spec
    meta=transport.d.inputs.api('actions/artifacts/'+str(number))
    m.need(not meta['expired'] and meta['id']==number and meta['workflow_run']['id']==run and
           meta['size_in_bytes']==size and meta['digest']=='sha256:'+sha,'pinned artifact metadata')
    raw=transport.d.inputs.api('actions/artifacts/'+str(number)+'/zip',True)
    m.need(m.identity(raw)==dict(size=size,sha256=sha),'complete artifact digest')
    write(ART/f'artifact-{number}.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    return transport.safe_zip(raw,300000000)


def invoke(runtime,lane,seed,command):
    folder=ART/lane;folder.mkdir();working=folder/'story.srm';working.write_bytes(seed)
    (folder/'commands.txt').write_bytes(command)
    argv=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(ART/'runner'),
          str(ART/'candidate.gba'),str(working),'continue-story',m.identity(seed)['sha256']]
    with (folder/'stdout.txt').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
        result=subprocess.run(argv,input=command,cwd=folder,stdout=out,stderr=err,timeout=300)
    write(folder/'execution.json',dict(returncode=result.returncode,initial_save=m.identity(seed),
                                     final_save=m.identity(working.read_bytes())))
    m.need(result.returncode==0 and not (folder/'stderr.txt').read_bytes(),'native failure; preserve and stop, no blind retry')
    return working.read_bytes()


def measure():
    os.chdir(ROOT)
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists(),'new interval only, never rerun accepted checkpoint')
    m.need(bindings(LOCAL)==LOCAL,'byte-identical locally tested implementation')
    state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_text())
    protected=bindings(set(state['source_bindings'])|{'AGENTS.md','CHATGPT_RESUME.md','state/source-lock.json','config/active_play_baseline.json'})
    source=bindings(CODE);ART.mkdir(parents=True)
    with archive(ARCHIVES[0]) as z:
        for name,wanted in [('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('training.srm',m.prior.OUTPUT_SAVE)]:
            raw=z.read(name);m.need(m.identity(raw)==wanted,'Save14 member identity '+name)
            target=ART/('original-save14.srm' if name=='training.srm' else name)
            target.write_bytes(raw);target.chmod(0o555 if name=='runner' else 0o444)
    with archive(ARCHIVES[1]) as z:
        seed=z.read('story-fast.srm');progression=z.read('progression.srm')
        m.need(m.identity(seed)==m.INPUT_SAVE,'accepted split story-fast only')
        m.need(m.identity(progression)==dict(size=131088,sha256='617e59ce2ab6b4e32767917f0184db48d9473755e350b1c24b64abe9025f14a0'),'progression copy preserved')
        (ART/'input.srm').write_bytes(seed);(ART/'input.srm').chmod(0o444)
        (ART/'progression.srm').write_bytes(progression);(ART/'progression.srm').chmod(0o444)
    runtime=OUT/'runtime';runtime.mkdir()
    with archive(ARCHIVES[2]) as z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                target=runtime/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'unchanged libmgba')
    saved=invoke(runtime,'progress',seed,(ROOT/m.DEV/'commands.txt').read_bytes())
    (ART/'story-fast.srm').write_bytes(saved)
    m.need(m.identity(saved)==m.OUTPUT_SAVE,'new Save16 matches developed original before cold startup')
    cold=invoke(runtime,'continue',saved,(ROOT/m.DEV/'continue-commands.txt').read_bytes())
    (ART/'cold.srm').write_bytes(cold)
    result,ledger=m.verify(ART);write(ART/'verification.json',result);write(ART/'save-byte-ledger.json',ledger)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_story_fast_maori.py','-v'],cwd=ROOT,capture_output=True,timeout=120)
    (ART/'unit.stdout.txt').write_bytes(unit.stdout);(ART/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode==0 and not unit.stdout and unit.stderr.count(b' ... ok\n')==44 and b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr,'44 focused tests, no skip')
    m.need(bindings(protected)==protected and bindings(CODE)==source,'accepted sources and new source remain unchanged')
    for name,wanted in [('candidate.gba',m.CANDIDATE),('runner',m.RUNNER),('input.srm',m.INPUT_SAVE),('original-save14.srm',m.prior.OUTPUT_SAVE)]:
        m.need(m.identity((ART/name).read_bytes())==wanted,'immutable original after execution')
    write(ART/'measurement.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
          source_bindings=source,result=result,focused_tests=44,development_focused_tests=44,
          development_native_processes=2,formal_native_processes=2,accepted_case_reruns=0,
          protected_source_count=len(protected),save_byte_ledger=m.identity((ART/'save-byte-ledger.json').read_bytes())))
    write(ART/'manifest.json',{p.relative_to(ART).as_posix():m.identity(p.read_bytes()) for p in sorted(ART.rglob('*')) if p.is_file()})
    print('PASS new Maori trainer1 escape1 Save16 cold/all131088 bytes; 48 screens; focused44; accepted replay0')

if __name__=='__main__':measure()
