#!/usr/bin/env python3
"""New native executions on the frozen evolution-repaired candidate.

Candidate paths/identity and the independently reconstructed recipe are the
only projections. Hash-pinned parent validators, vectors, process-exit checks,
UI witnesses and save guards remain enforced; parent successes are not reused.
"""
from pathlib import Path
import argparse
import json
import sys
import types
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_evolution_learning_repair as repair
import pr16_p07_preserved_layer as layer
need=layer.need
stable=layer.stable
identity=layer.identity
ROM_SHA='635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e'
OLD='.local/pr16-integrated-p07/candidate.gba'
ROM='.local/pr16-evolution-repair/candidate.gba'
REPORT='.local/pr16-evolution-repair/composed.json'
SELF='scripts/pr16_repaired_acceptance.py'
OUT=ROOT/'.local/pr16-evolution-evidence/acceptance'
PINS={
 'pr16_integrated_native':('af368c60c5eb4bdfbf4eb65cae801e032b0ecebb496aafab2f7b3b3bd8ce028f',1),
 'pr16_native_learning':('49ed90c17d79876ff971b5cd1e9d74fb788ada2d7a44dfc8b926bfb8904d28b1',1),
 'pr16_integrated_p06':('9d2194d8f536fd08bddee6cdeb1143fa8c8d7e7b529225afbd6fa418108c6ac9',2),
 'pr16_integrated_domains':('2da5be92e1601fdd383b57fc39f480d92cba8da82998bcc3a5b6e7008993b0d3',1),
}


def substituted_source(name):
    sha,count=PINS[name]
    text=layer.source.checked(ROOT/'scripts'/f'{name}.py',sha).decode()
    need(text.count(OLD)==count and ROM not in text,'candidate path projection differs: '+name)
    text=text.replace(OLD,ROM)
    if name=='pr16_integrated_domains':
        changes={"REPORT='.local/pr16-integrated-p07/candidate.json'":'REPORT='+repr(REPORT),
                 "WORK='.local/pr16-integrated-domains'":"WORK='.local/pr16-evolution-domains'",
                 "OUT='.local/pr16-final-routes/domains'":"OUT='.local/pr16-evolution-evidence/acceptance/domains'",
                 'candidate,report=layer.build(stage84,selected,layout)':'candidate,report=compose_candidate(stage84,selected,layout)'}
        for old,new in changes.items():
            need(text.count(old)==1 and new not in text,'domain projection preimage differs')
            text=text.replace(old,new,1)
    return text


def load(name,output=None):
    text=substituted_source(name)
    if output is not None:
        output.mkdir(parents=True,exist_ok=True)
        (output/(name+'.py')).write_text(text)
    module=types.ModuleType('repaired_'+name)
    module.__file__=str(ROOT/'scripts'/f'{name}.py')
    exec(compile(text,module.__file__,'exec'),module.__dict__)
    return module


def native_module(output=None):
    m=load('pr16_integrated_native',output)
    need(m.ROM_SHA==repair.PARENT_SHA,'native parent identity changed')
    m.ROM_SHA=ROM_SHA
    return m


def compose_candidate(stage84,selected,layout):
    parent,p07=layer.build(stage84,selected,layout)
    candidate,fixed=repair.build(parent,p07['allocation'])
    need(identity(candidate)=={'size':33554432,'sha256':ROM_SHA},'repaired candidate identity differs')
    report={**p07,'candidate':identity(candidate),'crc32':fixed['crc32'],
            'allocation':fixed['allocation'],'evolution_repair':fixed,'release_ready':False,'native_acceptance':False}
    return candidate,report


def compose_record():
    s=layer.source
    stage84=s.checked(ROOT/'.local/final-integration-candidate/candidate.gba',s.ROM_SHA)
    selected,_=s.recover(s.checked(ROOT/'userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip',s.V4_SHA),
                        s.checked(ROOT/'manifests/species_ids.csv',s.SPECIES_SHA),s.checked(ROOT/'manifests/move_ids.csv',s.MOVES_SHA))
    layout=json.loads(s.checked(ROOT/layer.ALLOCATION,layer.ALLOCATION_SHA))
    candidate,report=compose_candidate(stage84,selected,layout)
    need(s.checked(ROOT/ROM,ROM_SHA)==candidate,'separate repaired build differs from composed recipe')
    (ROOT/REPORT).write_bytes(stable(report))
    return report


def domain_module(output=None):
    m=load('pr16_integrated_domains',output)
    m.native=native_module(output)
    m.compose_candidate=compose_candidate
    original=m.derived_config
    def config():
        c=original()
        c['final_integration']['integration_revision']='EXACT_P07_PLUS_NATIVE_EVOLUTION_REPAIR'
        for p in (SELF,repair.SELF,repair.ASM):c['final_integration']['sources'][p]=m.prior.identity(p)
        return c
    m.derived_config=config
    return m


def run(domain):
    need(domain in ('learning','memory','p06','domains'),'unknown repaired acceptance domain')
    out=OUT/domain
    # Actual source snapshots are separate from the fixed parent source files.
    adapters=OUT/'executed-adapters';native=native_module(adapters)
    raw=layer.source.checked(ROOT/ROM,ROM_SHA)
    parent=ROOT/OLD;layer.source.checked(parent,repair.PARENT_SHA)
    protected={str(p):identity(p.read_bytes()) for p in (parent,ROOT/ROM)}
    bindings={str(p.relative_to(ROOT)):identity(p.read_bytes()) for p in
              (ROOT/SELF,ROOT/repair.SELF,ROOT/repair.ASM,*(ROOT/'scripts'/f'{p}.py' for p in PINS))}
    try:
        if domain=='learning':
            m=load('pr16_native_learning',adapters);m.native=native
            result=m.run(out)
        elif domain=='memory':result=native.run(out)
        elif domain=='p06':
            m=load('pr16_integrated_p06',adapters);m.new=native
            result=m.run(out)
        else:
            compose_record();m=domain_module(adapters);result=m.run_all()
    finally:
        need(protected=={p:identity(Path(p).read_bytes()) for p in protected},'repaired acceptance changed candidate or parent')
        need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'repaired acceptance changed source')
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/(domain+'-binding.json')).write_bytes(stable({'candidate':identity(raw),'parent_sha256':repair.PARENT_SHA,
            'source_bindings':bindings,'old_runs_relabelled':0,'release_ready':False,'domain':domain}))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('domain',choices=('learning','memory','p06','domains'))
    try:print(json.dumps(run(p.parse_args().domain),ensure_ascii=False))
    except (ValueError,OSError,RuntimeError,KeyError,TypeError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
