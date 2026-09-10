#!/usr/bin/env python3
"""Seven unchanged domain validators, actual execution on the integrated ROM.

The candidate boundary composes the exact P07 layer and explicitly projects its
three moved table arguments. Original recipes, ABI preimages, all root checks,
result validators and the historic gate remain unchanged.
Report aggregation is NOT a PR merge or release decision.
"""
from copy import deepcopy
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import modernization_final_integration as prior
import pr16_integrated_native as native
import pr16_p07_preserved_layer as layer
need=layer.need
stable=layer.stable
WORK='.local/pr16-integrated-domains'
CONFIG=WORK+'/config.json'
ROM='.local/pr16-integrated-p07/candidate.gba'
REPORT='.local/pr16-integrated-p07/candidate.json'
SELF='scripts/pr16_integrated_domains.py'
OUT='.local/pr16-final-routes/domains'
DOMAINS=('p02','mega_shop','floette','p03','p04_mega_runtime','battle_policy','p05')
# Independently fixed by exact integration build 34504500198. Do not read the
# observed ROM pointers into expectations: a corrupt pointer must still fail.
P03_RELOCATIONS={
    'level-root': ('0x0958B95C', '0x095D5FF0'),
    'egg-root': ('0x09FF0BD4', '0x095D9EFC'),
    'egg-limit': (7507, 7696),
}


def candidate_p03_contract(parent):
    contract=deepcopy(parent)
    for key,(before,after) in P03_RELOCATIONS.items():
        need(type(contract['arguments'].get(key)) is type(before) and
             contract['arguments'][key]==before,'P03 parent relocation preimage differs: '+key)
        contract['arguments'][key]=after
    return contract


def validate_root_projection(report):
    need(report['candidate']=={'size':33554432,'sha256':native.ROM_SHA},'P03 projection candidate differs')
    need(report['parent']=={'size':33554432,'sha256':prior.SHA},'P03 projection parent differs')
    for key,name in (('level-root','level'),('egg-root','egg')):
        need(int(report['roots'][name],16)==int(P03_RELOCATIONS[key][1],16),'P03 projected table root differs: '+key)
    egg=next(r for r in report['allocation']['allocations'] if r['name']=='modernization-p07-preserved-egg')
    need(egg['size']==15396 and egg['size']//2-2==P03_RELOCATIONS['egg-limit'][1],
         'P03 projected egg scan limit differs')


def derived_config():
    cfg=prior.derived_config()
    cfg['execution']['state_root']=WORK+'/state'
    inherited=cfg['final_integration']
    parent_p03=deepcopy(cfg['p03_contract'])
    cfg['p03_contract']=candidate_p03_contract(parent_p03)
    paths=(*inherited['sources'],SELF,'scripts/pr16_p07_preserved_layer.py',
           'scripts/pr16_integrated_native.py','scripts/pr16_integration_continuation.py',
           'scripts/pr16_source_acceptance.py',layer.SRC,layer.SPEC)
    cfg['final_integration']={'stage':84,'integration_revision':'EXACT_P07_PRESERVED_LAYER',
        'rom':{'path':ROM,'size':33554432,'sha256':native.ROM_SHA},
        'parent_stage84':inherited,'parent_p03_contract':parent_p03,
        'p03_relocations':{k:{'before':v[0],'after':v[1]} for k,v in P03_RELOCATIONS.items()},'sources':{p:prior.identity(p) for p in sorted(set(paths))},
        'release_ready':False}
    need(tuple(cfg['execution']['domain_order'])==DOMAINS,'historical domain order changed')
    return cfg


def prepare():
    cfg=derived_config();prior.safe(WORK).mkdir(parents=True,exist_ok=True)
    layer.source.checked(ROOT/ROM,native.ROM_SHA)
    prior.safe(CONFIG).write_bytes(stable(cfg))
    return cfg


def load_engine():
    cfg=derived_config();need(prior.safe(CONFIG).read_bytes()==stable(cfg),'private configuration changed')
    engine=prior.load(prior.parent_adapter().ENGINE)
    original=engine._validate_runtime_candidate
    def validate_candidate(config,stage78,audit78):
        need(stable(config)==stable(cfg),'unexpected integrated domain configuration')
        stage80,audit80=original(config,stage78,audit78)
        stage84,_r84,_stage83=prior.rebuild(stage80)
        s=layer.source
        v4=s.checked(ROOT/'userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip',s.V4_SHA)
        species=s.checked(ROOT/'manifests/species_ids.csv',s.SPECIES_SHA)
        moves=s.checked(ROOT/'manifests/move_ids.csv',s.MOVES_SHA)
        selected,_=s.recover(v4,species,moves)
        layout=json.loads(s.checked(ROOT/layer.ALLOCATION,layer.ALLOCATION_SHA))
        candidate,report=layer.build(stage84,selected,layout)
        validate_root_projection(report)
        need(prior.identity(ROM)==cfg['final_integration']['rom'] and prior.safe(ROM).read_bytes()==candidate,
             'domain candidate differs from independent composition')
        recorded=json.loads(prior.safe(REPORT).read_bytes())
        need(all(stable(recorded[k])==stable(v) for k,v in report.items()),'domain recipe report differs')
        return candidate,{'stage':84,'integration_revision':'EXACT_P07_PRESERVED_LAYER',
            'task':'USER-MODERNIZATION-FINAL-INTEGRATION','rom':prior.identity(ROM),
            'parent':audit80,'recipe_report':report,
            'parent_allocation_content_hashes_reused_as_candidate':False,
            'acceptance_adapter_sources':cfg['final_integration']['sources']}
    engine._validate_runtime_candidate=validate_candidate
    return engine


def run_all():
    prepare();out=prior.safe(OUT);out.mkdir(parents=True,exist_ok=True)
    helper=prior.load(prior.parent_adapter().HELPER);helper._load_orchestrator=load_engine
    plan=helper.plan(prior.safe(CONFIG),'all');(out/'plan.json').write_bytes(stable(plan))
    need(plan['input_rom']==prior.identity(ROM),'plan targets old candidate')
    results=[];failures=[]
    for domain in DOMAINS:
        target=out/'records'/domain;target.mkdir(parents=True,exist_ok=True)
        try:
            result=helper.run_domain(prior.safe(CONFIG),domain,target)
            validation=helper.validate_domain(prior.safe(CONFIG),domain,target/'result.json')
            (target/'validation.json').write_bytes(stable(validation));results.append(result)
        except (ValueError,RuntimeError,OSError,KeyError,TypeError) as e:
            failures.append({'domain':domain,'error':str(e)})
            (target/'failure.json').write_bytes(stable(failures[-1]))
    aggregate=None
    if not failures:
        with prior.preserve_gate():aggregate=helper.merge(prior.safe(CONFIG),out/'records',out/'aggregate')
    report={'schema_version':1,'status':'FAIL' if failures else 'PASS_WITH_DECLARED_LIMITS',
        'candidate':prior.identity(ROM),'domain_results':results,'failures':failures,
        'aggregate':aggregate,'old_runs_relabelled':0,'domains':list(DOMAINS),
        'release_ready':False,'full_native_route_acceptance':False,'active_baseline_changed':False}
    (out/'result.json').write_bytes(stable(report));need(not failures,'integrated regression failed; inspect domain raw outputs')
    return report


if __name__=='__main__':
    try:print(json.dumps(run_all(),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
