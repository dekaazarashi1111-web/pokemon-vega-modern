#!/usr/bin/env python3
"""Actual daycare/hatch/cold-save coverage for the source-proven P07 Pichu row.

The eight Stage82 originals stay immutable. These are five NEW executions on
635fd890, including duplicate, conditional-Light-Ball and unchanged controls.
Parents/starting map are fixtures; all subsequent daycare steps are ordinary.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import types
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_repaired_acceptance as repaired
need=repaired.need
SELF='scripts/pr16_breeding_delta.py'
TEST='tests/test_pr16_breeding_delta.py'
WORKFLOW='.github/workflows/pr16-breeding-delta.yml'
PARENT='scripts/run_modernization_p03_breeding_e2e.py'
PARENT_SHA='c293ceec2e3a72094300bbf0d6764c5a4017f6db4a1cf138d8ccf647cbbc9e75'
PARENT_C='tools/mgba_modernization_p03_breeding_e2e.c'
PARENT_C_SHA='a99cafd942f958c932709bed6099695f067dc292401b3bfb91e60afe4d6823de'
SCOPE='PR16_P07_PICHU_PRESERVED_EGG_PHYSICAL_BREEDING'
OUT=ROOT/'.local/pr16-breeding-delta'
# Independent oracle: (name, father's moves, mother's moves, items, child moves).
CASES=(
 ('vega-father',(440,33,0,0),(45,52,0,0),0,0,(39,84,440,0)),
 ('vega-mother',(33,52,0,0),(440,45,0,0),0,0,(39,84,440,0)),
 ('vega-both',(440,33,0,0),(440,45,0,0),0,0,(39,84,440,0)),
 ('vega-lightball-full',(175,440,33,0),(273,45,0,0),202,0,(175,440,273,344)),
 ('no-eligible-control',(33,52,0,0),(45,81,0,0),0,0,(39,84,0,0)),
)
OLD_EGG=[175,217,252,268,273,321,549]


def load():
    repaired.layer.source.checked(ROOT/PARENT,PARENT_SHA)
    spec=importlib.util.spec_from_file_location('pr16_breeding_delta_parent',ROOT/PARENT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    # The isolated parent validator reads only this new identity, not its build.
    m.repair=types.SimpleNamespace(CANDIDATE_SHA=repaired.ROM_SHA)
    m.SCOPE=SCOPE
    return m


def replace_once(text,old,new):
    need(text.count(old)==1 and new not in text,'breeding projection preimage differs')
    return text.replace(old,new,1)


def controller_source():
    text=repaired.layer.source.checked(ROOT/PARENT_C,PARENT_C_SHA).decode()
    prefix='static const struct BCase b_cases[] = {'
    pattern=re.escape(prefix)+r'\n.*?\n};'
    matches=list(re.finditer(pattern,text,re.S));need(len(matches)==1,'breeding case block is not unique')
    rows=[]
    for name,father,mother,fi,mi,child in CASES:
        arr=lambda a:'{'+','.join(map(str,a))+'}'
        rows.append('    {"'+name+'", '+arr(father)+', '+arr(mother)+','+str(fi)+','+str(mi)+','+arr(child)+'},')
    text=replace_once(text,matches[0].group(),prefix+'\n'+'\n'.join(rows)+'\n};')
    text=replace_once(text,'#define B_ROM_SHA "e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d"',
                      '#define B_ROM_SHA "'+repaired.ROM_SHA+'"')
    text=replace_once(text,'#define B_SCOPE "P03_DAYCARE_INHERITANCE_HATCH_SAVE_RELOAD"',
                      '#define B_SCOPE "'+SCOPE+'"')
    return text


def source_row(selected):
    rows=[r for r in selected[repaired.layer.LAYER] if r['species_id']==24 and r['route']=='egg']
    expected={'form_key':'','move_id':440,'move_key':'MOVE_KEY_VEGA_440',
              'route':'egg','source_class':'CURRENT_PRESERVED','source_csv_line':273,
              'source_member':'egg_moves_final.csv','source_parameters':{'order':'20'},
              'species_id':24,'species_key':'SPECIES_KEY_PICHU'}
    need(rows==[expected],'Pichu accepted preservation source differs')
    return expected


def oracle(raw,parent,selected):
    layer=repaired.layer;s=layer.source
    need(repaired.identity(raw)=={'size':33554432,'sha256':repaired.ROM_SHA},'new candidate differs')
    need(repaired.identity(parent)=={'size':33554432,'sha256':s.ROM_SHA},'Stage84 parent differs')
    row=source_row(selected)
    before=s.RomTables(parent,layer.COUNT,selected_species={24})
    after=s.RomTables(raw,layer.COUNT,selected_species={24})
    need(before.egg[24]==OLD_EGG and after.egg[24]==OLD_EGG+[440],'only the adopted egg delta may differ')
    need(before.level[24]==after.level[24] and [(m,l) for m,l in after.level[24] if l<=1]==[(39,1),(84,1)],
         'Pichu ordinary level-one rows changed')
    pp={0:0}
    targets={m for case in CASES for m in case[-1] if m}
    root=struct.unpack_from('<I',raw,0x1cc)[0]-layer.BASE
    oldroot=struct.unpack_from('<I',parent,0x1cc)[0]-layer.BASE
    need(root==oldroot==0x10421F4,'move PP table changed')
    for move in targets:
        pp[move]=raw[root+move*12+4]
        need(pp[move]==parent[oldroot+move*12+4] and 1<=pp[move]<=64,'canonical PP changed')
    need({m:pp[m] for m in (39,84,175,273,344)}=={39:30,84:30,175:15,273:10,344:15},'old canonical PP differs')
    return {'source':row,'old_egg':OLD_EGG,'new_egg':after.egg[24],
            'level_one':[[39,1],[84,1]],'canonical_pp':pp,
            'conditional_light_ball_item':202,'conditional_move':344},pp


def configure(pp):
    m=load()
    m.CASES={name:(list(child),[pp[x] for x in child],fi,mi) for name,_,_,fi,mi,child in CASES}
    return m


def run():
    base=load();out=base.prepare_output(OUT)
    # Invalidate stale result before input/source/compiler errors.
    (out/'result.json').unlink(missing_ok=True)
    candidate=ROOT/repaired.ROM;seed=ROOT/base.SEED
    raw=repaired.layer.source.checked(candidate,repaired.ROM_SHA)
    repaired.layer.source.checked(seed,base.SEED_SHA)
    source=repaired.layer.source
    parent=source.checked(ROOT/'.local/final-integration-candidate/candidate.gba',source.ROM_SHA)
    selected,_=source.recover(source.checked(ROOT/'userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip',source.V4_SHA),
                              source.checked(ROOT/'manifests/species_ids.csv',source.SPECIES_SHA),
                              source.checked(ROOT/'manifests/move_ids.csv',source.MOVES_SHA))
    audit,pp=oracle(raw,parent,selected);m=configure(pp)
    text=controller_source();(out/'executed-controller.c').write_text(text)
    (out/'oracle.json').write_bytes(repaired.stable(audit))
    paths={SELF,TEST,WORKFLOW,PARENT,PARENT_C,'scripts/pr16_repaired_acceptance.py',
           'scripts/pr16_p07_preserved_layer.py','scripts/pr16_integration_continuation.py',
           'scripts/run_modernization_p03_fullslots_e2e.py','config/active_play_baseline.json',
           'design/active_play_baseline.md',*(p for p,_ in m.EMBEDDED)}
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())
    p02=next(d for d in cfg['domains'] if d['id']=='p02')
    for binding in (p02['runner'],*p02['dependencies']):
        need(m.common.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'pinned controller dependency changed')
        paths.add(binding['path'])
    bindings={p:m.common.identity(ROOT/p) for p in sorted(paths)}
    protected={str(p):m.common.identity(p) for p in (seed,candidate)}
    results=[];failures=[];guards=[]
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-breed-',dir=ROOT/'.local') as td:
            work=Path(td)
            for i,(src,target) in enumerate(m.EMBEDDED):
                (work/target).write_text(m.embed((ROOT/src).read_text(),'pr16_breed_embedded_'+str(i)))
            c=work/'controller.c';c.write_text(text);binary=work/'runner'
            _,_,process=m.common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(c),'-lmgba','-o',str(binary)],out/'compile',120)
            need(m.common.require_exited(process)==0,'breeding delta compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=m.common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);guards.append(guard)
            def one(case):
                name=case[0];private=work/(name+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,process=m.common.capture([str(binary),str(candidate),str(private),repaired.ROM_SHA,m.SEED_SHA,name],out/name,900)
                try:
                    result=m.validate_result(stdout,name,m.common.require_exited(process))
                    need(b'mGBA[' not in stderr,'native emulator warning')
                    return {'name':name,'result':result,'process':process},None
                except (ValueError,RuntimeError,TypeError,KeyError) as exc:
                    return None,{'name':name,'error':str(exc),'process':process}
            with ThreadPoolExecutor(max_workers=2) as pool:
                for result,error in pool.map(one,CASES):
                    if result:results.append(result)
                    if error:failures.append(error)
    finally:
        need(protected=={p:m.common.identity(Path(p)) for p in protected},'candidate/original seed changed')
        need(bindings=={p:m.common.identity(ROOT/p) for p in bindings},'source/baseline changed')
    report={'schema_version':1,'status':'FAIL' if failures else 'PASS','scope':SCOPE,
            'candidate':repaired.identity(raw),'sources':bindings,'oracle':audit,'results':results,
            'failures':failures,'guard_checks':guards,'actual_new_processes':len(CASES),
            'successful_fresh_cores':len(results)*3,'old_runs_relabelled':0,
            'all_breeding_paths_accepted':False,'full_p03_acceptance':False,'full_p07_acceptance':False,'release_ready':False}
    (out/'result.json').write_bytes(repaired.stable(report))
    need(not failures,'physical breeding delta failed; inspect raw originals')
    return report

if __name__=='__main__':
    try:print(json.dumps(run(),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError,struct.error) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(1)
