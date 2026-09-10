#!/usr/bin/env python3
"""Compose exact Stage82 and the source-decided P06 delta at the candidate boundary.

The Stage79 runner/result/exit/cache/merge validators remain unchanged.
All seven domains run against Stage83, never against relabelled parent bytes.
"""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import modernization_p06_decided_adjustments as delta
SELF='scripts/run_modernization_stage83_github_domain.py'
ADAPTER82='scripts/run_modernization_stage82_github_domain.py'
WORKFLOW='.github/workflows/modernization-stage83-mgba.yml'
RECIPE='tools/modernization_p06_decided_adjustments.py'
BASE='config/modernization_stage79_cumulative_mgba.json'
HELPER='scripts/run_modernization_stage79_github_domain.py'
ENGINE='scripts/run_modernization_stage79_cumulative_mgba.py'
WORK='.local/stage83-decided-species'
CONFIG,ROM,REPORT=(WORK+'/'+n for n in ('config.json','candidate.gba','candidate.json'))
GATE='content/modernization/stage79_cumulative_mgba_runtime_gate.json'
SHA=delta.CANDIDATE_SHA

def require(ok,message):
    if not ok:raise RuntimeError(message)

def stable(value):return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()

def safe(name):
    p=Path(name);require(not p.is_absolute() and '..' not in p.parts,'unsafe path')
    q=ROOT
    for part in p.parts:
        q/=part;require(not q.is_symlink(),'symlink path')
    q.resolve().relative_to(ROOT.resolve());return q

def raw(name):return safe(name).read_bytes()

def identity(name):
    b=raw(name);return {'path':name,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def load(name):
    spec=importlib.util.spec_from_file_location(Path(name).stem,safe(name))
    require(spec is not None and spec.loader is not None,'cannot import source')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def parent_adapter():
    require(identity(ADAPTER82)['sha256']=='beb315a986f5ed5acdd6d973a5d44ad5c306f5f260d5e5553b1faccb5e41287d','Stage82 acceptance adapter changed')
    return load(ADAPTER82)

def rebuild(stage80):
    parent,report82=parent_adapter().rebuild(stage80)
    child,report=delta.build(parent)
    require(hashlib.sha256(child).hexdigest()==SHA,'Stage83 recipe output differs')
    return child,report,report82

def derived_config():
    a=parent_adapter();a.derived_config() # validates all historical source pins
    cfg=delta.strict_json(raw(BASE));cfg['execution']['state_root']=WORK+'/state'
    spec=delta.specification()
    names={*a.PINS,a.RECIPE,a.ASM,ADAPTER82,RECIPE,delta.CONTRACT,SELF,WORKFLOW,
           'manifests/species_ids.csv','manifests/ability_ids.csv',spec['historical_contract']['path']}
    names.update(s['path'] for s in spec['sources'].values())
    cfg['stage83_decided_species']={'stage':83,'rom':{'path':ROM,'size':33554432,'sha256':SHA},
        'sources':{p:identity(p) for p in sorted(names)},'full_p06_acceptance':False,'release_ready':False}
    return cfg

def prepare():
    safe(WORK).mkdir(parents=True,exist_ok=True)
    for p in (CONFIG,ROM,REPORT):safe(p).unlink(missing_ok=True)
    cfg=derived_config();a=parent_adapter()
    child,report,_=rebuild(raw(a.load(a.PP).PARENT_PATH))
    safe(ROM).write_bytes(child);safe(REPORT).write_bytes(stable(report));safe(CONFIG).write_bytes(stable(cfg))
    return {'status':'PREPARED_NOT_EXECUTED','candidate':identity(ROM),'config':identity(CONFIG)}

def load_engine():
    cfg=derived_config();require(raw(CONFIG)==stable(cfg),'private config differs')
    engine=load(ENGINE);original=engine._validate_runtime_candidate
    def validate_child(config,stage78,audit78):
        require(stable(config)==stable(cfg),'unexpected Stage83 config')
        stage80,audit80=original(config,stage78,audit78)
        child,report,report82=rebuild(stage80)
        require(identity(ROM)==cfg['stage83_decided_species']['rom'] and raw(ROM)==child,'Stage83 bytes differ')
        require(raw(REPORT)==stable(report),'Stage83 report differs')
        return child,{'stage':83,'task':'USER-MODERNIZATION-P06-DECIDED-DELTAS','rom':identity(ROM),
            'repair_recipe':identity(RECIPE),'repair_report':identity(REPORT),
            'parent':{'stage':82,'rom':report['parent'],'parent':audit80,'recipe_report':report82},
            'adopted_species_count':2,'field_change_count':3,'changed_bytes_from_parent':3,
            'parent_allocation_content_hashes_reused_as_candidate':False,
            'acceptance_adapter_sources':cfg['stage83_decided_species']['sources']}
    engine._validate_runtime_candidate=validate_child
    return engine

@contextmanager
def preserve_gate():
    p=safe(GATE);b=p.read_bytes();st=p.stat()
    try:yield
    finally:
        if p.read_bytes()!=b:p.write_bytes(b)
        os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns))
        require(p.read_bytes()==b,'historical gate restore failed')

def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    try:
        if args==['prepare']:
            print(stable(prepare()).decode(),end='');return 0
        require(args and args[0] in ('plan','run-domain','validate-domain','merge'),'unknown mode')
        require('--config' not in args,'only exact derived config is accepted')
        helper=load(HELPER);helper._load_orchestrator=load_engine
        if args[0]=='merge':
            with preserve_gate():return helper.main(['--config',CONFIG,*args])
        return helper.main(['--config',CONFIG,*args])
    except (OSError,KeyError,ValueError,RuntimeError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
