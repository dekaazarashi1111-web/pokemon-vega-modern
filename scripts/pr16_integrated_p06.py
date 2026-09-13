#!/usr/bin/env python3
"""Re-execute all adopted P06 acceptance on the integrated P07 candidate.

Only the input path and expected candidate SHA change in a separately loaded
validator. Historical source files, ROMs, receipts and validators stay unchanged.
The generated path adapter, fresh raw outputs and original source hashes are
preserved. No old Stage84 result is counted as execution on the new candidate.
"""
from concurrent.futures import ThreadPoolExecutor
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_integrated_native as new
from pr16_source_acceptance import validate_summary_screenshots
import modernization_final_integration as prior
need=new.need
stable=new.stable
identity=new.identity
PINS={
 'scripts/run_modernization_p06_phase_e2e.py':'d47949154cd142c77408b06a3dba6eb1863f593d5d9b8d767d8ca20937ca3b46',
 'scripts/run_modernization_p06_decided_e2e.py':'9cb31857cd8ed7979c7aca846b3e178d58bdfdf84ddce2968d445e9ef635999e',
 'tools/mgba_modernization_p06_phase_e2e.c':'b985e956d4966db0eb57e5a7468f2d97b11b8410a4b262b4a404be5b8c1e83ca',
}
OLD_CHILD="ROOT/'.local/final-integration-candidate/candidate.gba'"
NEW_CHILD="ROOT/'.local/pr16-integrated-p07/candidate.gba'"
REVIEWED={
 'summary-220-0-skills.ppm':'673ac688398319aa7376851e443c7fabba9b76cac611b2c3207bb1472f2211e8',
 'summary-220-1-skills.ppm':'e2a809a96987af17a01d7cb606acd51334154cd6f64f53b114435f926f70db6d',
 'summary-373-0-skills.ppm':'1abb75d08d7f99f1d0de4719cf06a9ac4392b5037d41ad12ff9debc8f882ec28',
}


def path_adapter(source):
    need(source.count(OLD_CHILD)==1 and NEW_CHILD not in source,'native phase path adapter preimage differs')
    return source.replace(OLD_CHILD,NEW_CHILD,1)


def load_base():
    path=ROOT/'scripts/run_modernization_p06_decided_e2e.py'
    new.layer.source.checked(path,PINS[str(path.relative_to(ROOT))])
    spec=importlib.util.spec_from_file_location('pr16_p06_new_identity',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    need(m.FINAL_SHA==prior.SHA,'old P06 candidate binding changed')
    m.FINAL_SHA=new.ROM_SHA
    return m


def run(output):
    api=new.validator();out=api.prepare_output(output)
    for name,sha in PINS.items():new.layer.source.checked(ROOT/name,sha)
    candidate=ROOT/'.local/pr16-integrated-p07/candidate.gba'
    new.layer.source.checked(candidate,new.ROM_SHA)
    original84=identity((ROOT/'.local/final-integration-candidate/candidate.gba').read_bytes())
    prior.parent_adapter().prepare()
    base=load_base();parent=ROOT/base.PARENT;seed=ROOT/base.SEED
    new.layer.source.checked(parent,base.recipe.PARENT_SHA);new.layer.source.checked(seed,base.SEED_SHA)
    paths={*PINS,'scripts/pr16_integrated_p06.py','scripts/pr16_integrated_native.py',base.SOURCE,
           'config/active_play_baseline.json','design/active_play_baseline.md',*(p for p,_ in base.EMBED)}
    bindings={p:identity((ROOT/p).read_bytes()) for p in sorted(paths)}
    phase_source=path_adapter((ROOT/'scripts/run_modernization_p06_phase_e2e.py').read_text())
    (out/'executed-phase-path-adapter.py').write_text(phase_source)
    phase=types.ModuleType('pr16_p06_phase_new_identity');phase.__file__=str(ROOT/'scripts/run_modernization_p06_phase_e2e.py')
    exec(compile(phase_source,phase.__file__,'exec'),phase.__dict__)
    phase.base=base
    phase_result=phase.run(out/'phase')
    shots=validate_summary_screenshots(out/'phase')
    for name,sha in REVIEWED.items():need(shots[name]['sha256']==sha,'fresh Summary differs from reviewed display: '+name)
    results=[];errors=[];slot_out=out/'slots';slot_out.mkdir(parents=True,exist_ok=True)
    cap=base.capture_api
    protected={str(p):identity(p.read_bytes()) for p in (parent,candidate,seed)}
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-p06-slots-',dir=ROOT/'.local') as td:
            work=Path(td)
            for source,target in base.EMBED:(work/target).write_text(base.embed((ROOT/source).read_text(),'pr16_old_'+Path(target).stem))
            binary=work/'runner'
            _,_,proc=cap.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),base.SOURCE,'-lmgba','-o',str(binary)],slot_out/'compile',120)
            need(cap.require_exited(proc)==0,'P06 slot native compile failed')
            for guard in base.GUARDS:
                stdout,stderr,proc=cap.capture([str(binary),'--guard-check',guard],slot_out/('guard-'+guard),10)
                need(cap.require_exited(proc)==1 and not stdout and stderr==b'P03 archive: host write after observation barrier\n','P06 slot write guard failed')
            def one(case):
                s,a,m=case;label=f'{s}-{a}-{m}';private=work/(label+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,proc=cap.capture([str(binary),str(parent),str(candidate),str(private),base.recipe.PARENT_SHA,new.ROM_SHA,base.SEED_SHA,str(s),str(a),str(m)],slot_out/label,240)
                try:
                    need(b'mGBA[' not in stderr,'P06 emulator warning')
                    return base.validate(stdout,case,cap.require_exited(proc),new.ROM_SHA),None
                except (ValueError,RuntimeError,KeyError,TypeError) as e:return None,{'case':label,'error':str(e),'process':proc}
            with ThreadPoolExecutor(max_workers=4) as pool:
                for result,error in pool.map(one,base.CASES):
                    if result:results.append(result)
                    if error:errors.append(error)
    finally:
        need(protected=={p:identity(Path(p).read_bytes()) for p in protected},'P06 protected inputs changed')
        need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'P06 sources changed')
        need(identity((ROOT/'.local/final-integration-candidate/candidate.gba').read_bytes())==original84,'Stage84 parent overwritten')
    need(len(phase_result['cases'])==10 and phase_result['status']=='PASS','new P06 phase incomplete')
    report={'schema_version':1,'status':'FAIL' if errors else 'PASS','scope':'P06_ALL_THREE_ADOPTED_FIELDS_ON_INTEGRATED_CANDIDATE',
            'candidate':identity(candidate.read_bytes()),'historical_results_relabelled':0,'source_bindings':bindings,
            'phase_result':identity((out/'phase/result.json').read_bytes()),'fresh_phase_processes':10,
            'phase_candidate_processes':9,'unchanged_stage82_attack_controls':1,
            'slot_results':results,'slot_failures':errors,'fresh_slot_processes':8,'fresh_slot_cores':24,
            'fresh_summary_screenshots':shots,'reviewed_display_identity_preserved':True,
            'accepted_fields':3,'accepted_species':2,'release_ready':False,'active_baseline_changed':False}
    (out/'result.json').write_bytes(stable(report));need(not errors and len(results)==8,'P06 slot acceptance incomplete');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.local/pr16-final-routes/p06')
    try:print(json.dumps(run(p.parse_args().output),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
