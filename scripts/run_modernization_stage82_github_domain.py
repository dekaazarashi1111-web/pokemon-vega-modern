#!/usr/bin/env python3
"""Run the unchanged Stage79 seven-domain plan/execute/validate/merge on Stage82.

Validate Stage78/80 normally; compose exact Stage81 and Stage82 recipes at the
candidate boundary only. Do not replace runner/result/exit/cache validators.
Every state root is isolated, and the historical merged gate is restored.
"""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
SELF = 'scripts/run_modernization_stage82_github_domain.py'
BASE = 'config/modernization_stage79_cumulative_mgba.json'
HELPER = 'scripts/run_modernization_stage79_github_domain.py'
ENGINE = 'scripts/run_modernization_stage79_cumulative_mgba.py'
PP = 'tools/modernization_p03_native_pp_repair.py'
RECIPE = 'tools/modernization_p03_archive_ui_repair.py'
ASM = 'overlays/modernization_p03_archive_ui_repair/relearner_list.S'
WORK = '.local/stage82-archive-ui'
CONFIG, ROM, REPORT = (WORK+'/'+n for n in ('config.json','candidate.gba','candidate.json'))
GATE = 'content/modernization/stage79_cumulative_mgba_runtime_gate.json'
SHA = 'e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d'
PINS = {
 BASE: 'ee6c6326e0c96445b113e9cd0d73f5b3b7a1d5c907789e58d88ea3878abca5d6',
 HELPER: '40be67f28c55b9f338e8d671702e11e290362b0cf774dc6630330932c30a5f47',
 ENGINE: 'fc5eff879d6bfc9d0d9232162c47de26b44957bf8a897e19997afec6dbe793fb',
 PP: 'bfa4a1f2c8d470bafdb705d57fdd73a55a7885cfacb1dca6c392576a38f51e17',
}


def require(ok, message):
    if not ok: raise RuntimeError(message)


def stable(value):
    return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()


def safe(relative):
    p=Path(relative);require(not p.is_absolute() and '..' not in p.parts,'unsafe path')
    current=ROOT
    for part in p.parts:
        current/=part;require(not current.is_symlink(),'symlink path: '+relative)
    current.resolve().relative_to(ROOT.resolve())
    return current


def raw(relative): return safe(relative).read_bytes()


def identity(relative):
    data=raw(relative)
    return {'path':relative,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def load(relative):
    spec=importlib.util.spec_from_file_location(Path(relative).stem,safe(relative))
    require(spec is not None and spec.loader is not None,'cannot import source')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def rebuild(stage80):
    stage81,_=load(PP).build(stage80)
    child,report=load(RECIPE).build(stage81)
    require(hashlib.sha256(child).hexdigest()==SHA,'exact Stage82 candidate differs')
    return child,report


def derived_config():
    for path,sha in PINS.items():
        require(identity(path)['sha256']==sha,'historical contract/source changed: '+path)
    cfg=json.loads(raw(BASE));cfg['execution']['state_root']=WORK+'/state'
    cfg['stage82_archive_ui']={'stage':82,'rom':{'path':ROM,'size':33554432,'sha256':SHA},
        'sources':{p:identity(p) for p in (*PINS,RECIPE,ASM,SELF)},
        'full_p03_acceptance':False,'release_ready':False}
    return cfg


def prepare():
    safe(WORK).mkdir(parents=True,exist_ok=True)
    for path in (CONFIG,ROM,REPORT):safe(path).unlink(missing_ok=True)
    cfg=derived_config();child,report=rebuild(raw(load(PP).PARENT_PATH))
    safe(ROM).write_bytes(child);safe(REPORT).write_bytes(stable(report));safe(CONFIG).write_bytes(stable(cfg))
    return {'status':'PREPARED_NOT_EXECUTED','candidate':identity(ROM),'config':identity(CONFIG)}


def load_engine():
    cfg=derived_config();require(raw(CONFIG)==stable(cfg),'private config differs from exact unchanged contracts')
    engine=load(ENGINE);original=engine._validate_runtime_candidate
    def validate_child(config,stage78,audit78):
        require(stable(config)==stable(cfg),'unexpected Stage82 config')
        stage80,audit80=original(config,stage78,audit78)
        child,report=rebuild(stage80)
        require(identity(ROM)==cfg['stage82_archive_ui']['rom'] and raw(ROM)==child,'Stage82 bytes differ')
        require(raw(REPORT)==stable(report),'Stage82 classification report differs')
        return child,{'stage':82,'task':'USER-MODERNIZATION-P03-ARCHIVE-UI',
            'rom':identity(ROM),'repair_recipe':identity(RECIPE),'repair_report':identity(REPORT),
            'parent':audit80,'exact_stage81_parent_sha256':report['parent_sha256'],
            'patches':report['repairs'],'changed_bytes_from_parent':report['changed_byte_count'],
            'native_scheduler_metadata_offsets_preserved':True,'relocated_ui_layout':report['layout'],
            'parent_allocation_content_hashes_reused_as_candidate':False,
            'acceptance_adapter_sources':cfg['stage82_archive_ui']['sources']}
    engine._validate_runtime_candidate=validate_child
    return engine


@contextmanager
def preserve_gate():
    path=safe(GATE);before=path.read_bytes()
    try:yield
    finally:
        path.write_bytes(before);require(path.read_bytes()==before,'historical gate restore failed')


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    try:
        if args==['prepare']:
            print(stable(prepare()).decode(),end='');return 0
        require(args and args[0] in ('plan','run-domain','validate-domain','merge'),'expected prepare/plan/run-domain/validate-domain/merge')
        require('--config' not in args,'only the exact derived Stage82 config is accepted')
        helper=load(HELPER);helper._load_orchestrator=load_engine
        if args[0]=='merge':
            with preserve_gate():return helper.main(['--config',CONFIG,*args])
        return helper.main(['--config',CONFIG,*args])
    except (OSError,ValueError,RuntimeError) as e:
        print('ERROR: '+str(e),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
