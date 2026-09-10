#!/usr/bin/env python3
"""Seven unchanged domain validators, actual execution on the integrated ROM.

Only the candidate boundary composes the exact P07 layer. Original Stage79/82/84
recipes, ABI preimages, result validators and historic gate remain unchanged.
Report aggregation is NOT a PR merge or release decision.
"""
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


def derived_config():
    cfg=prior.derived_config()
    cfg['execution']['state_root']=WORK+'/state'
    inherited=cfg['final_integration']
    paths=(*inherited['sources'],SELF,'scripts/pr16_p07_preserved_layer.py',
           'scripts/pr16_integrated_native.py','scripts/pr16_integration_continuation.py',
           'scripts/pr16_source_acceptance.py',layer.SRC,layer.SPEC)
    cfg['final_integration']={'stage':84,'integration_revision':'EXACT_P07_PRESERVED_LAYER',
        'rom':{'path':ROM,'size':33554432,'sha256':native.ROM_SHA},
        'parent_stage84':inherited,'sources':{p:prior.identity(p) for p in sorted(set(paths))},
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
