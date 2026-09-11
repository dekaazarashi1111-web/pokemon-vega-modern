#!/usr/bin/env python3
"""Source-proven Happiny incense/egg routes on the unchanged PR16 candidate.

Five NEW physical daycare/egg/hatch/save executions. Parent individuals and
starting map are fixtures; no natural parent capture is claimed. Historical
Pichu controllers, results and original evidence are never changed/relabelled.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
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
import pr16_breeding_delta as prior
repaired=prior.repaired
need=repaired.need
SELF='scripts/pr16_happiny_breeding.py'
TEST='tests/test_pr16_happiny_breeding.py'
WORKFLOW='.github/workflows/pr16-happiny-breeding.yml'
OUT=ROOT/'.local/pr16-happiny-breeding'
SCOPE='PR16_P07_HAPPINY_INCENSE_PHYSICAL_BREEDING'
INCENSE=862
FATHER_SPECIES=25
MOTHER_SPECIES=365
CYCLES=40
# name, male Pikachu moves, female Chansey moves, father/mother item,
# expected child species, independently expected final four level-one/egg moves.
CASES=(
 ('mother-incense-first',(84,39,0,0),(461,1,0,0),0,INCENSE,364,(1,539,461,0)),
 ('father-incense-middle',(84,39,0,0),(464,1,0,0),INCENSE,0,364,(1,539,464,0)),
 ('three-retained-full',(84,39,0,0),(461,464,357,0),0,INCENSE,364,(539,461,464,357)),
 ('incense-no-eligible',(84,39,0,0),(1,111,0,0),0,INCENSE,364,(1,539,0,0)),
 ('no-incense-chansey',(84,39,0,0),(461,464,357,0),0,0,365,(204,343,539,549)),
)
CASE_BY_NAME={v[0]:v for v in CASES}
SOURCE_ROWS=[(461,3852,'12'),(464,3856,'16'),(357,3859,'19')]
EXPECTED_OLD_EGG=[69,215,217,716]


def validator_source():
    raw=repaired.layer.source.checked(ROOT/prior.PARENT,prior.PARENT_SHA)
    return prior.replace_once(raw.decode(),
        "result['hatch_steps'] == 11 * 256 - result['hatch_clock_start'] - 1",
        "result['hatch_steps'] == (expected['initial_egg_cycles'] + 1) * 256 - result['hatch_clock_start'] - 1")


def configure(pp):
    m=types.ModuleType('pr16_happiny_parent');m.__file__=str(ROOT/prior.PARENT)
    exec(compile(validator_source(),m.__file__,'exec'),m.__dict__)
    m.repair=types.SimpleNamespace(CANDIDATE_SHA=repaired.ROM_SHA);m.SCOPE=SCOPE
    m.CASES={name:(list(child),[pp[x] for x in child],fi,mi) for name,_,_,fi,mi,_,child in CASES}
    old_expected=m.expected_result
    def expected(name):
        result=old_expected(name)
        result.update(child_species=CASE_BY_NAME[name][5],initial_egg_cycles=CYCLES)
        return result
    m.expected_result=expected
    return m


def controller_source():
    text=repaired.layer.source.checked(ROOT/prior.PARENT_C,prior.PARENT_C_SHA).decode()
    prefix='static const struct BCase b_cases[] = {'
    matches=list(re.finditer(re.escape(prefix)+r'\n.*?\n};',text,re.S))
    need(len(matches)==1,'Happiny controller case block differs')
    arr=lambda a:'{'+','.join(map(str,a))+'}'
    rows=['    {"'+n+'", '+arr(f)+', '+arr(m)+','+str(fi)+','+str(mi)+','+arr(child)+','+str(sid)+'},'
          for n,f,m,fi,mi,sid,child in CASES]
    changes=[
      (matches[0].group(),prefix+'\n'+'\n'.join(rows)+'\n};'),
      ('unsigned father[4], mother[4], father_item, mother_item, child[4];',
       'unsigned father[4], mother[4], father_item, mother_item, child[4], child_species;'),
      ('#define B_ROM_SHA "e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d"',
       '#define B_ROM_SHA "'+repaired.ROM_SHA+'"'),
      ('#define B_SCOPE "P03_DAYCARE_INHERITANCE_HATCH_SAVE_RELOAD"','#define B_SCOPE "'+SCOPE+'"'),
      ('static void b_create(struct mCore *c,unsigned dst,unsigned pid,unsigned ot)',
       'static void b_create(struct mCore *c,unsigned dst,unsigned species,unsigned pid,unsigned ot)'),
      ('BATTLE_CORE_CREATE_MON,dst,25U,20U,31U','BATTLE_CORE_CREATE_MON,dst,species,20U,31U'),
      ('b_data(c,dst,11U)==25U','b_data(c,dst,11U)==species'),
      ('b_create(c,QOL_PLAYER_PARTY,0x123456F0U,0x11223344U)',
       'b_create(c,QOL_PLAYER_PARTY,25U,0x123456F0U,0x11223344U)'),
      ('b_create(c,QOL_PLAYER_PARTY+100U,0x34567801U,0x99887766U)',
       'b_create(c,QOL_PLAYER_PARTY+100U,365U,0x34567801U,0x99887766U)'),
      ('b_data(c,B_CHILD,11U)==24U','b_data(c,B_CHILD,11U)==v->child_species'),
      ('initial_cycles==10U,"Pichu native egg cycles changed"',
       'initial_cycles==40U,"Happiny/Chansey native egg cycles changed"'),
      ('z<8192U && !b_hatched','z<12288U && !b_hatched'),
      ('printf("\\"child_species\\":24,\\"child_level\\":1,\\"moves\\":");',
       'printf("\\"child_species\\":%u,\\"child_level\\":1,\\"moves\\":",v->child_species);'),
    ]
    for old,new in changes:text=prior.replace_once(text,old,new)
    return text


def source_rows(selected):
    actual=[r for r in selected[repaired.layer.LAYER] if r['species_id']==364 and r['route']=='egg']
    expected=[dict(form_key='',move_id=move,move_key='MOVE_KEY_VEGA_'+str(move),route='egg',
                   source_class='CURRENT_PRESERVED',source_csv_line=line,source_member='egg_moves_final.csv',
                   source_parameters={'order':order},species_id=364,species_key='SPECIES_KEY_HAPPINY')
              for move,line,order in SOURCE_ROWS]
    need(actual==expected,'exact retained Happiny source rows differ')
    return expected


def oracle(raw,parent,selected):
    layer=repaired.layer;s=layer.source
    need(repaired.identity(raw)=={'size':33554432,'sha256':repaired.ROM_SHA},'wrong candidate')
    need(repaired.identity(parent)=={'size':33554432,'sha256':s.ROM_SHA},'wrong Stage84 parent')
    rows=source_rows(selected);ids={25,364,365}
    old=s.RomTables(parent,layer.COUNT,selected_species=ids)
    new=s.RomTables(raw,layer.COUNT,selected_species=ids)
    need(old.egg[364]==EXPECTED_OLD_EGG and new.egg[364]==EXPECTED_OLD_EGG+[461,464,357],
         'physical Happiny egg delta differs')
    need(old.egg[365]==new.egg[365]==[281],'no-incense Chansey egg pool changed')
    level={sid:[m for m,lev in new.level[sid] if lev<=1] for sid in (364,365)}
    need(level=={364:[1,539],365:[1,111,186,204,343,539,549]},'child starting learnsets differ')
    need(all(old.level[sid]==new.level[sid] for sid in (364,365)),'ordinary levels changed')
    table=struct.unpack_from('<I',raw,0x1bc)[0]-layer.BASE
    need(table==struct.unpack_from('<I',parent,0x1bc)[0]-layer.BASE==0x1576c74,'BaseStats root differs')
    parents={}
    for sid in ids:
        at=table+32*sid
        need(raw[at:at+32]==parent[at:at+32],'breeding species BaseStats changed')
        parents[sid]={'gender':raw[at+16],'cycles':raw[at+17],'groups':list(raw[at+20:at+22])}
    need(parents[25]['gender']<0xF0 and parents[365]['gender']==254 and
         6 in parents[25]['groups'] and parents[365]['groups']==[6,6], 'parents are not compatible male/female fixtures')
    need(parents[364]['cycles']==parents[365]['cycles']==CYCLES,'native egg cycle oracle differs')
    # Canonical manifest, not the differently-numbered upstream ITEM_LUCK_INCENSE alias.
    import csv
    items=list(csv.DictReader((ROOT/'manifests/item_ids.csv').open(encoding='utf-8-sig')))
    incense=[r for r in items if r['item_key']=='ITEM_KEY_LUCK_INCENSE']
    need(len(incense)==1 and int(incense[0]['id'])==INCENSE,'canonical incense ID differs')
    pp_root=struct.unpack_from('<I',raw,0x1cc)[0]-layer.BASE
    need(pp_root==struct.unpack_from('<I',parent,0x1cc)[0]-layer.BASE==0x10421F4,'canonical PP root differs')
    pp={0:0}
    for move in {m for case in CASES for m in case[-1] if m}:
        pp[move]=raw[pp_root+12*move+4]
        need(1<=pp[move]<=64 and pp[move]==parent[pp_root+12*move+4],'canonical PP differs')
    return {'source_rows':rows,'candidate_child_level_one':level,'parent_species':parents,
            'incense_item':INCENSE,'old_egg':old.egg[364],'new_egg':new.egg[364],
            'no_incense_child_species':365,'no_incense_egg':new.egg[365],
            'canonical_pp':pp,'scope':'source-proven retained delta, no new adoption'},pp


def run():
    base=prior.load();out=base.prepare_output(OUT);(out/'result.json').unlink(missing_ok=True)
    s=repaired.layer.source;candidate=ROOT/repaired.ROM;seed=ROOT/base.SEED
    raw=s.checked(candidate,repaired.ROM_SHA);s.checked(seed,base.SEED_SHA)
    parent=s.checked(ROOT/'.local/final-integration-candidate/candidate.gba',s.ROM_SHA)
    selected,_=s.recover(s.checked(ROOT/'userfile/imports/Pokemon-Vega_MOVE-DISTRIBUTION-V4_IMPLEMENTATION-READY.zip',s.V4_SHA),
                         s.checked(ROOT/'manifests/species_ids.csv',s.SPECIES_SHA),s.checked(ROOT/'manifests/move_ids.csv',s.MOVES_SHA))
    audit,pp=oracle(raw,parent,selected);m=configure(pp);text=controller_source()
    (out/'executed-controller.c').write_text(text);(out/'executed-validator.py').write_text(validator_source())
    (out/'oracle.json').write_bytes(repaired.stable(audit))
    paths={SELF,TEST,WORKFLOW,prior.SELF,prior.PARENT,prior.PARENT_C,
           'scripts/pr16_repaired_acceptance.py','scripts/pr16_p07_preserved_layer.py',
           'scripts/pr16_integration_continuation.py','scripts/run_modernization_p03_fullslots_e2e.py',
           'config/active_play_baseline.json','design/active_play_baseline.md','manifests/item_ids.csv',
           *(p for p,_ in m.EMBEDDED)}
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())
    p02=next(d for d in cfg['domains'] if d['id']=='p02')
    for binding in (p02['runner'],*p02['dependencies']):
        need(m.common.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'pinned controller dependency changed')
        paths.add(binding['path'])
    bindings={p:m.common.identity(ROOT/p) for p in sorted(paths)}
    protected={str(p):m.common.identity(p) for p in (seed,candidate)}
    results=[];failures=[];guards=[]
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-happiny-',dir=ROOT/'.local') as td:
            work=Path(td)
            for i,(src,target) in enumerate(m.EMBEDDED):
                (work/target).write_text(m.embed((ROOT/src).read_text(),'happiny_embedded_'+str(i)))
            c=work/'controller.c';c.write_text(text);binary=work/'runner'
            _,_,process=m.common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(c),'-lmgba','-o',str(binary)],out/'compile',120)
            need(m.common.require_exited(process)==0,'Happiny C compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=m.common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);guards.append(guard)
            def one(case):
                name=case[0];private=work/(name+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,process=m.common.capture([str(binary),str(candidate),str(private),repaired.ROM_SHA,m.SEED_SHA,name],out/name,1200)
                try:
                    value=m.validate_result(stdout,name,m.common.require_exited(process))
                    need(b'mGBA[' not in stderr,'emulator warning')
                    return {'name':name,'result':value,'process':process},None
                except (ValueError,RuntimeError,TypeError,KeyError) as exc:
                    return None,{'name':name,'error':str(exc),'process':process}
            with ThreadPoolExecutor(max_workers=2) as pool:
                for result,error in pool.map(one,CASES):
                    if result:results.append(result)
                    if error:failures.append(error)
    finally:
        need(protected=={p:m.common.identity(Path(p)) for p in protected},'candidate or original seed changed')
        need(bindings=={p:m.common.identity(ROOT/p) for p in bindings},'protected source/baseline changed')
    report={'schema_version':1,'status':'FAIL' if failures else 'PASS','scope':SCOPE,'candidate':repaired.identity(raw),
            'sources':bindings,'oracle':audit,'results':results,'failures':failures,'guard_checks':guards,
            'actual_new_processes':len(CASES),'successful_fresh_cores':len(results)*3,'old_runs_relabelled':0,
            'happiny_retained_incense_routes_accepted':not failures,'all_breeding_paths_accepted':False,
            'full_p03_acceptance':False,'full_p07_acceptance':False,'release_ready':False}
    (out/'result.json').write_bytes(repaired.stable(report))
    need(not failures,'Happiny physical route failed; inspect the original stdout/stderr')
    return report

if __name__=='__main__':
    try:print(json.dumps(run(),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError,struct.error) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(1)
