#!/usr/bin/env python3
"""新Save17区間だけを初回Actions測定。完了済み19試験は原本を再利用。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
import pr16_story_after_maori as s
import pr16_story_after_maori_accept as m
import pr16_research_story_route_actions as h
ART = s.ART
WF = '.github/workflows/pr16-story-after-maori.yml'
SELF = 'scripts/pr16_story_after_maori_measure.py'
CODE = {SELF, WF, 'scripts/pr16_story_after_maori.py', 'scripts/pr16_story_after_maori_accept.py',
        'scripts/pr16_story_after_maori_session.py', 'tests/test_pr16_story_after_maori.py',
        'tests/test_pr16_story_after_maori_accept.py'} | {m.DEV+'/'+n for n in
        ('expected.json','failure-receipt.json','progress-commands.txt','continue-commands.txt')}


def archive(number, run, expected, head=None):
    api = h.d.inputs.api
    meta = api('actions/artifacts/'+str(number))
    m.need(meta['id'] == number and meta['expired'] is False and meta['workflow_run']['id'] == run and
           meta['size_in_bytes'] == expected['size'] and meta['digest'] == 'sha256:'+expected['sha256'] and
           (head is None or meta['workflow_run']['head_sha'] == head), 'fixed artifact metadata')
    raw = api('actions/artifacts/'+str(number)+'/zip', True)
    m.need(m.identity(raw) == expected, 'complete outer artifact digest')
    return meta, h.safe_zip(raw, 300000000)


def old_tests_receipt():
    """同一sourceの完了済み19試験だけ回収。失敗したinspectionは成功にしない。"""
    expected = dict(size=4191197, sha256='d03946ec7e0c8da00afb82fe4299e3006d1bcded659156aa0e6e5c97a0218581')
    meta, z = archive(11008805462,36508880929,expected,'9bb7577150c23926369f41fcc6538d92eda17614')
    with z:
        unit = z.read('unit.stderr.txt')
        m.need(not z.read('unit.stdout.txt') and m.identity(unit) == dict(size=1764,
            sha256='d0576459c9c4071c22a0c0db9c6ecfda7288ba5c5188d8bc417faa1e5e65202e') and
            unit.count(b' ... ok\n') == 19 and b'\nOK\n' in unit, 'original nineteen tests only')
    jobs = h.d.inputs.api('actions/runs/36508880929/jobs?per_page=100')
    m.need(jobs['total_count'] == 1 and len(jobs['jobs']) == 1 and
           jobs['jobs'][0]['id'] == 109216400418 and jobs['jobs'][0]['conclusion'] == 'failure', 'retain original failed run')
    steps = jobs['jobs'][0]['steps']
    m.need(any(x['name'] == 'Exact locally tested source and new tests' and x['conclusion'] == 'success'
               and x['status'] == 'completed' for x in steps), 'specific successful test step')
    (ART/'prior-19-unit.stderr.txt').write_bytes(unit)
    s.write(ART/'prior-19-receipt.json',dict(run_id=36508880929,job_id=109216400418,
        run_conclusion='failure',reused_successful_step='Exact locally tested source and new tests',
        original_tests=19,rerun_tests=0,artifact=meta))


def invoke(runtime, lane, seed, command):
    m.commands(command)  # Validate ALL commands before starting the process, including the 600-frame bound.
    folder = ART/lane
    folder.mkdir()
    working = folder/'story.srm'
    working.write_bytes(seed)
    (folder/'commands.txt').write_bytes(command)
    argv = [str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(ART/'runner'),
            str(ART/'candidate.gba'),str(working),'continue-story',m.identity(seed)['sha256']]
    with (folder/'stdout.txt').open('wb') as out, (folder/'stderr.txt').open('wb') as err:
        result = subprocess.run(argv,input=command,cwd=folder,stdout=out,stderr=err,timeout=300)
    s.write(folder/'execution.json',dict(returncode=result.returncode,initial_save=m.identity(seed),
            final_save=m.identity(working.read_bytes())))
    m.need(result.returncode == 0 and not (folder/'stderr.txt').read_bytes(),
           'native failure: preserve evidence and stop; no blind retry')
    return working.read_bytes()


def measure():
    os.chdir(ROOT)
    h.d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT'] == '1' and not (ROOT/m.CP).exists() and not ART.exists(),
           'new unaccepted interval and fresh evidence directory only')
    state = h.source_check()
    protected = h.d.bindings(set(state['source_bindings']) | h.d.PROTECTED)
    expected = json.loads((ROOT/m.DEV/'expected.json').read_text())
    m.need(h.d.bindings(expected['locally_tested_sources']) == expected['locally_tested_sources'],
           'exact local tested bytes, no tool transcription drift')
    bindings = h.d.bindings(CODE)
    for lane in ('progress','continue'):
        m.commands((ROOT/m.DEV/(lane+'-commands.txt')).read_bytes())
    # The inspector owns ART creation. No preflight mkdir or unit output may pre-create ART.
    s.inspect()
    old_tests_receipt()
    runtime = s.OUT/'runtime'
    runtime.mkdir()
    meta, z = archive(10898620034,36218655601,dict(size=102586759,
         sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'))
    with z:
        for name in z.namelist():
            if name == 'ld.so' or name.startswith('lib/'):
                target = runtime/name
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755)
    (runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes()) == dict(size=1968536,
           sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed runtime')
    seed = (ART/'input.srm').read_bytes()
    saved = invoke(runtime,'progress',seed,(ROOT/m.DEV/'progress-commands.txt').read_bytes())
    (ART/'story-fast.srm').write_bytes(saved)
    m.need(m.identity(saved) == m.OUTPUT_SAVE, 'Save17 matches development before independent cold start')
    cold = invoke(runtime,'continue',saved,(ROOT/m.DEV/'continue-commands.txt').read_bytes())
    (ART/'cold.srm').write_bytes(cold)
    result, ledger = m.verify(ART)
    s.write(ART/'verification.json',result)
    s.write(ART/'save-byte-ledger.json',ledger)
    failure = json.loads((ROOT/m.DEV/'failure-receipt.json').read_text())
    prefix = (ART/'progress/stdout.txt').read_bytes()[:failure['failed_stdout']['size']]
    m.need(m.identity(prefix) == failure['failed_stdout'], 'corrected trace retains entire failed development prefix')
    s.write(ART/'development-failure-receipt.json',dict(original_receipt=failure,
        prefix_verified_against_formal=True,failed_native_replayed=False))
    unit = subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests',
        '-p','test_pr16_story_after_maori_accept.py','-v'],cwd=ROOT,capture_output=True,timeout=120)
    (ART/'unit.stdout.txt').write_bytes(unit.stdout)
    (ART/'unit.stderr.txt').write_bytes(unit.stderr)
    m.need(unit.returncode == 0 and not unit.stdout and unit.stderr.count(b' ... ok\n') == 34 and
           b'\nOK\n' in unit.stderr and b'skipped' not in unit.stderr, '34 focused tests without skips')
    m.need(h.d.bindings(protected) == protected and h.d.bindings(CODE) == bindings, 'accepted/new sources unchanged')
    for name, wanted in [('input.srm',s.INPUT_SAVE),('candidate.gba',s.CANDIDATE),('runner',m.shared.RUNNER)]:
        m.need(m.identity((ART/name).read_bytes()) == wanted, 'immutable original '+name)
    s.write(ART/'measurement.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=bindings,result=result,focused_tests=34,reused_prior_tests=19,prior_test_reruns=0,
        development_native_processes=3,development_failed_native=1,formal_native_processes=2,
        accepted_case_reruns=0,compile_count=0,save_byte_ledger=m.identity((ART/'save-byte-ledger.json').read_bytes())))
    s.write(ART/'manifest.json',{p.relative_to(ART).as_posix():m.identity(p.read_bytes())
                               for p in sorted(ART.rglob('*')) if p.is_file()})
    print('PASS Save16 -> trainer3 -> Ayame heal Save17 -> cold/all131088bytes; screens119; new34; old replay0')


if __name__ == '__main__':
    measure()
