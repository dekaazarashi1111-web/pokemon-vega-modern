#!/usr/bin/env python3
"""First formal measurement of the NEW Save18 interval, never old acceptance."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_ayame_accept as m
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
OUT=ROOT/'.local/pr16-story-ayame'
ART=OUT/'artifact'
WF='.github/workflows/pr16-story-ayame.yml'
CODE={WF,'scripts/pr16_story_ayame_chain.py','scripts/pr16_story_ayame_accept.py',
      'scripts/pr16_story_ayame_measure.py','tests/test_pr16_story_ayame_chain.py',
      'tests/test_pr16_story_ayame_accept.py',m.DEV+'/expected.json'}
PARENT=dict(size=18112423,sha256='e78ed5327d55427cca992406d43fa488f92065d11fe0bc0636493a83c97fb4db')


def invoke(runtime,lane,seed,command):
    m.commands(command)
    folder=ART/lane;folder.mkdir()
    save=folder/'story.srm';save.write_bytes(seed)
    (folder/'commands.txt').write_bytes(command)
    args=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(ART/'runner'),
          str(ART/'candidate.gba'),str(save),'continue-story',m.identity(seed)['sha256']]
    with (folder/'stdout.txt').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
        p=subprocess.run(args,input=command,cwd=folder,stdout=out,stderr=err,timeout=300)
    h.d.write(folder/'execution.json',dict(returncode=p.returncode,initial_save=m.identity(seed),
                                         final_save=m.identity(save.read_bytes())))
    m.need(p.returncode == 0 and not (folder/'stderr.txt').read_bytes(),'native failure: preserve, no automatic retry')
    return save.read_bytes()


def measure():
    os.chdir(ROOT);h.d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT'] == '1' and not (ROOT/m.CP).exists() and not OUT.exists(),
           'new unaccepted interval and fresh artifact only')
    state=h.source_check(); protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    plan=json.loads((ROOT/m.DEV/'expected.json').read_text())
    m.need(h.d.bindings(plan['locally_tested_sources']) == plan['locally_tested_sources'],'exact locally tested source bytes')
    bindings=h.d.bindings(CODE)
    command={'progress':zlib.decompress(base64.b85decode(plan['progress']['commands_zlib_b85'])),
             'continue':plan['continue']['commands_text'].encode()}
    for lane,data in command.items():
        m.commands(data);m.need(m.identity(data) == plan[lane]['commands'],'exact developed ordinary commands')
    ART.mkdir(parents=True)
    for test,count in (('chain',25),('accept',30)):
        p=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests',
                          '-p',f'test_pr16_story_ayame_{test}.py','-v'],capture_output=True,timeout=120)
        (ART/f'unit-{test}.stdout.txt').write_bytes(p.stdout);(ART/f'unit-{test}.stderr.txt').write_bytes(p.stderr)
        m.need(p.returncode == 0 and not p.stdout and p.stderr.count(b' ... ok\n') == count and
               b'\nOK\n' in p.stderr and b'skipped' not in p.stderr,'new scoped tests '+test)
    meta,z=transport.archive(11008723945,36510782954,PARENT,'0c5a118c855ee52eecbadaa7c4114d32a59e500f')
    with z:
        manifest=json.loads(z.read('manifest.json'))
        m.need(len(manifest) == 144 and set(z.namelist()) == set(manifest)|{'manifest.json'},'accepted parent member set')
        for name,binding in manifest.items():m.need(m.identity(z.read(name)) == binding,'parent member hash '+name)
        for name,target,binding in (('story-fast.srm','input.srm',m.INPUT_SAVE),('candidate.gba','candidate.gba',m.source.CANDIDATE),('runner','runner',m.shared.RUNNER)):
            data=z.read(name);m.need(m.identity(data) == binding,'fixed input '+name)
            (ART/target).write_bytes(data);(ART/target).chmod(0o555 if name == 'runner' else 0o444)
    h.d.write(ART/'parent.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    runtime=OUT/'runtime';runtime.mkdir()
    _,z=transport.archive(10898620034,36218655601,dict(size=102586759,
        sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'))
    with z:
        for name in z.namelist():
            if name == 'ld.so' or name.startswith('lib/'):
                p=runtime/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes()) == dict(size=1968536,
        sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA runtime')
    seed=(ART/'input.srm').read_bytes();saved=invoke(runtime,'progress',seed,command['progress'])
    (ART/'story-fast.srm').write_bytes(saved)
    m.need(m.identity(saved) == m.OUTPUT_SAVE,'completed Save18, not partial write, before cold')
    cold=invoke(runtime,'continue',saved,command['continue']);(ART/'cold.srm').write_bytes(cold)
    result,ledger=m.verify(ART)
    h.d.write(ART/'verification.json',result);h.d.write(ART/'save-byte-ledger.json',ledger)
    failure=plan['failure'];prefix=(ART/'progress/stdout.txt').read_bytes()[:failure['exact_prefix']['size']]
    m.need(m.identity(prefix) == failure['exact_prefix'],'entire failed observation prefix retained')
    original=prefix+failure['failed_progress_end_line'].encode()
    m.need(m.identity(original) == failure['failed_stdout'],'lossless text reconstruction against original failure hash')
    (ART/'failed-development-progress.stdout.txt').write_bytes(original)
    h.d.write(ART/'failure-receipt.json',failure)
    m.need(h.d.bindings(protected) == protected and h.d.bindings(CODE) == bindings,'protected and new source unchanged')
    for name,binding in (('input.srm',m.INPUT_SAVE),('candidate.gba',m.source.CANDIDATE),('runner',m.shared.RUNNER)):
        m.need(m.identity((ART/name).read_bytes()) == binding,'immutable original '+name)
    h.d.write(ART/'measurement.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=bindings,result=result,new_tests=55,development_native_processes=4,development_failed_native=2,
        formal_native_processes=2,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,
        save_byte_ledger=m.identity((ART/'save-byte-ledger.json').read_bytes())))
    h.d.write(ART/'manifest.json',{p.relative_to(ART).as_posix():m.identity(p.read_bytes()) for p in sorted(ART.rglob('*')) if p.is_file()})
    print('PASS new Save18: chain3/gym entry/heal/save/cold all131088; inputs381+23; screens145; new55; old rerun0')


if __name__=='__main__':measure()
