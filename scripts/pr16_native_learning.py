#!/usr/bin/env python3
"""Actual P07 level gain and P03 evolution learning, input/save/cold Continue."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import re
import shutil
import struct
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_integrated_native as native
import run_modernization_p06_decided_e2e as base
need=native.need
stable=native.stable
SOURCE='tools/mgba_pr16_level_learning.c'
SELF='scripts/pr16_native_learning.py'
SCOPE='PR16_NATIVE_LEVEL_AND_EVOLUTION_LEARNING_SAVE'
CASES=(('taillow-level-empty',10,12,10,457,20,2,1),
       ('taillow-level-full',10,12,10,457,20,1,0),
       ('taillow-level-cancel',10,12,10,457,20,1,3),
       ('lucario-evolution-empty',12,10,13,366,20,2,1))
WITNESS=('bag_party','level','dialog','summary','selection','stop','evo_begin','evo_update','downs','field')


def expected(case):
    name,sid,level,target,move,pp,slot,action=case
    moves=[17 if sid==10 else 33,81,0,0] if action==1 else [17 if sid==10 else 33,81,45,52]
    pps=[7,8,0,0] if action==1 else [7,8,9,10]
    bonus=5 if action==1 else 229
    if action<2:moves[slot]=move;pps[slot]=pp;bonus &= ~(3<<(slot*2))
    return dict(schema_version=1,status='PASS',scope=SCOPE,case=name,rom_sha256=native.ROM_SHA,
                species_before=sid,species_after=target,level_before=level,level_after=level+1,
                move=move,pp=pp,action=action,slot=slot,moves_after=moves,pp_after=pps,
                pp_bonuses_after=bonus,save_counter_delta=1,party_mon_bytes_preserved=100,
                fresh_cores=2,host_write_barriers=3,normal_save_menu=True,cold_continue=True,
                mgba_version='0.10.2',warnings_errors=0,release_ready=False)


def validate(raw,case,process,stderr=b''):
    api=native.validator();need(api.previous.require_exited(process)==0,'learning native process did not exit zero')
    need(b'mGBA[' not in stderr,'learning emulator warning')
    value=json.loads(raw);want=expected(case)
    need(type(value) is dict and set(value)==set(want)|{'witness'},'learning result fields differ')
    for key,v in want.items():need(api.same_typed(value[key],v),'learning result differs: '+key)
    w=value['witness'];need(type(w) is dict and set(w)==set(WITNESS),'learning witness schema differs')
    need(all(type(v) is int and 0<=v<40000 for v in w.values()),'learning witness types/bounds differ')
    need(0<w['bag_party']<w['level']<w['field'],'normal level input ordering missing')
    if case[1]!=case[3]:need(w['level']<w['evo_begin']<=w['evo_update']<w['field'],'actual evolution witness missing')
    else:need(w['evo_begin']==w['evo_update']==0,'unexpected evolution')
    if case[-1]==1:need(all(w[k]==0 for k in ('dialog','summary','selection','stop','downs')),'empty path entered replacement')
    else:
        need(w['level']<w['dialog']<w['summary']<w['selection']<w['field'],'native replacement/cancel witness missing')
        need(w['downs']<=4,'cursor retries exceed four moves')
        if case[-1]==3:need(w['selection']<w['stop']<w['field'],'summary cancellation not confirmed')
        else:need(w['stop']==0,'unexpected learning refusal')
    return value


def check_sources(raw):
    rows=re.findall(r'\{"([a-z0-9-]+)",(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\}',(ROOT/SOURCE).read_text())
    need(tuple((row[0],*map(int,row[1:])) for row in rows)==CASES,'compiled cases differ from independent expectations')
    tables=native.layer.source.RomTables(raw,native.layer.COUNT,selected_species={10,12,13})
    need((17,13) in tables.level[10] and (457,13) in tables.level[10] and (366,0) in tables.level[13],'required accepted level/evolution rows absent')
    need(not any(lev==11 for _,lev in tables.level[12]),'Riolu fixture has another level-11 acquisition')
    table=struct.unpack_from('<I',raw,0x1cc)[0]-native.layer.BASE
    for case in CASES:need(raw[table+case[4]*12+4]==case[5],'canonical PP input differs')
    return {'taillow_preknown_same_level_move':17,'fixture_reason':'Wing Attack precedes the preserved move at lv13; already known before the observation barrier',
            'taillow_preserved_row':[10,457,13],'lucario_evolution_row':[13,366,0],
            'p02_evolution_contract':'content/modernization/p02_evolution_contract.json',
            'evolution_source':[12,1,13],'fixture_friendship':255,'candidate':native.identity(raw)}


def run(output=ROOT/'.local/pr16-final-routes/learning'):
    api=native.validator();out=api.prepare_output(output)
    candidate=ROOT/'.local/pr16-integrated-p07/candidate.gba';seed=ROOT/api.SEED
    raw=native.layer.source.checked(candidate,native.ROM_SHA);native.layer.source.checked(seed,api.SEED_SHA)
    preflight=check_sources(raw);(out/'source-preflight.json').write_bytes(stable(preflight))
    paths={SOURCE,SELF,'scripts/pr16_integrated_native.py','scripts/run_modernization_p06_decided_e2e.py',
           'content/modernization/p02_evolution_contract.json','config/active_play_baseline.json','design/active_play_baseline.md',*(p for p,_ in base.EMBED)}
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())
    p02=next(d for d in cfg['domains'] if d['id']=='p02')
    for binding in (p02['runner'],*p02['dependencies']):
        need(api.previous.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'pinned learning harness changed');paths.add(binding['path'])
    bindings={p:api.previous.identity(ROOT/p) for p in sorted(paths)}
    protected={str(p):api.previous.identity(p) for p in (candidate,seed)}
    results=[];failures=[]
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-level-',dir=ROOT/'.local') as name:
            work=Path(name)
            for source,target in base.EMBED:(work/target).write_text(base.embed((ROOT/source).read_text(),'pr16_embedded_'+Path(target).stem))
            binary=work/'runner';_,_,p=api.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),SOURCE,'-lmgba','-o',str(binary)],out/'compile',120)
            need(api.previous.require_exited(p)==0,'learning native compile failed')
            for guard in api.GUARDS:
                stdout,stderr,p=api.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                need(api.previous.require_exited(p)==1 and not stdout and stderr==b'P03 archive: host write after observation barrier\n','learning write guard failed')
            def one(pair):
                i,case=pair;private=work/(case[0]+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,p=api.capture([str(binary),str(candidate),str(private),native.ROM_SHA,api.SEED_SHA,str(i)],out/case[0],240)
                try:return validate(stdout,case,p,stderr),None
                except (ValueError,RuntimeError,KeyError,TypeError) as e:return None,{'case':case[0],'error':str(e),'process':p}
            with ThreadPoolExecutor(max_workers=4) as pool:
                for result,error in pool.map(one,enumerate(CASES)):
                    if result:results.append(result)
                    if error:failures.append(error)
    finally:
        need(protected=={p:api.previous.identity(Path(p)) for p in protected},'learning altered candidate or original save')
        need(bindings=={p:api.previous.identity(ROOT/p) for p in bindings},'learning altered protected source')
    report={'schema_version':1,'status':'FAIL' if failures else 'PASS','scope':SCOPE,
            'candidate':native.identity(raw),'source_bindings':bindings,'results':results,'failures':failures,
            'actual_new_processes':len(CASES),'successful_fresh_cores':len(results)*2,
            'old_runs_relabelled':0,'fixture_boundary':'normal Continue then deterministic party/Bag before observed input',
            'full_p03_acceptance':False,'full_p07_acceptance':False,'release_ready':False}
    (out/'result.json').write_bytes(stable(report));need(not failures,'native learning route failed; inspect exact outputs');return report


if __name__=='__main__':
    try:print(json.dumps(run(),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
