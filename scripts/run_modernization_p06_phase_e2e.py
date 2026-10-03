#!/usr/bin/env python3
"""Native P06 passive effects / Summary, complementing existing stat-save evidence."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import run_modernization_p06_decided_e2e as base
api=base.capture_api
need=base.need
SCOPE='P06_ADOPTED_NATIVE_SUMMARY_AND_BATTLE'
SOURCE='tools/mgba_modernization_p06_phase_e2e.c'
SELF='scripts/run_modernization_p06_phase_e2e.py'
WORKFLOW='.github/workflows/pr16-integration-continuation.yml'
CASES=('summary-220-0','summary-220-1','summary-373-0','cursed-body','cursed-slot-control','frisk-item','frisk-no-item','frisk-slot-control','attack-before','attack-after')
INTS=('species','slot','personality','ability','party_attack','battle_attack','frames','key_presses','menu_frame','event_frame','turns','player_hp','enemy_hp','enemy_initial_hp','player_pp','enemy_pp','disabled_move','disable_timer','reveal_item','summary_page')
FLAGS=('ended','summary_equal','mon_equal')

def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def stable(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()

def validate_picture(raw):
    header=b'P6\n240 160\n255\n'
    need(raw.startswith(header) and len(raw)==len(header)+240*160*3,'invalid native screenshot dimensions/length')
    pixels=raw[len(header):]
    colors=len({pixels[i:i+3] for i in range(0,len(pixels),3)})
    need(colors>=16,'native screenshot is blank or renderer was not attached')
    return {'width':240,'height':160,'distinct_colors':colors,**identity(raw)}


def validate(raw,index,exit_code):
    need(type(index) is int and 0<=index<len(CASES),'unknown native case')
    need(type(exit_code) is int and exit_code==0,'native process failed')
    value=api.strict_json(raw)
    expected={'schema_version':1,'status':'OBSERVED','scope':SCOPE,'rom_sha256':base.recipe.PARENT_SHA if index==8 else base.FINAL_SHA,'case':CASES[index],
              'host_write_guard':True,'fixture_boundary':'BEFORE_FIRST_OBSERVED_FRAME','full_p06_acceptance':False,'release_ready':False,'warnings_errors':0}
    need(type(value) is dict and set(value)==set(expected)|set(INTS)|set(FLAGS)|{'ability_name_hex','ability_description_hex'},'native schema differs')
    for k,v in expected.items():need(api.same_typed(value[k],v),'native value differs: '+k)
    for k in INTS:need(type(value[k]) is int and 0<=value[k]<2**32,'native integer differs: '+k)
    for k in FLAGS:need(type(value[k]) is bool,'native boolean differs: '+k)
    for k,n in [('ability_name_hex',18),('ability_description_hex',46)]:need(type(value[k]) is str and re.fullmatch('[0-9a-f]{'+str(n)+'}',value[k]) is not None,'native buffer differs: '+k)
    species=373 if index==2 or index>=8 else 220;slot=1 if index in (1,4,5,6) else 0
    ability=base.ABILITIES_AFTER[species][slot]
    need(value['species']==species and value['slot']==slot and value['ability']==ability,'wrong adopted species/slot/ability')
    attack=base.stats(species,48,index!=8,value['personality'],[0]*6,[0]*6)[1]
    need(value['party_attack']==attack,'independent Attack formula differs')
    need(0<value['menu_frame']<=value['frames']<=24000 and value['key_presses']>0 and value['ended'],'native path did not reach its endpoint')
    if index<3:
        need(value['summary_equal'] and value['mon_equal'] and value['summary_page']==1,'native Summary changed mon or displayed incorrect ability')
        need(bytes.fromhex(value['ability_name_hex'])[0] not in (0,255),'empty displayed ability')
    else:
        need(value['battle_attack']==attack and value['player_hp']>0 and value['enemy_hp']>0,'native battle import/HP differs')
        if index==3:need(value['disabled_move']==44 and 0<value['disable_timer']<=8 and 0<value['event_frame']<=value['frames'] and value['turns']>0,'Cursed Body did not disable the actual incoming move')
        if index==4:need(value['disabled_move']==0 and value['disable_timer']==0 and value['turns']==4 and value['enemy_pp']==16,'wrong-slot Cursed Body control differs')
        if index==5:need(value['reveal_item']==13 and 0<value['event_frame']<value['menu_frame'],'Frisk did not reveal the actual held item at entry')
        if index in (6,7):need(value['reveal_item']==0 and value['event_frame']==0,'Frisk negative control revealed an item')
        if index>=8:need(value['turns']==1 and value['player_pp']==19 and value['enemy_pp']==19 and value['enemy_hp']<value['enemy_initial_hp'],'normal Attack turn did not finish')
    return value


def validate_attack_pair(before,after):
    for k in ('species','slot','personality','ability','enemy_initial_hp','player_hp','turns','player_pp','enemy_pp'):
        need(api.same_typed(before[k],after[k]),'parent/candidate fixture differs: '+k)
    old=before['enemy_initial_hp']-before['enemy_hp'];new=after['enemy_initial_hp']-after['enemy_hp']
    need(0<new<old and after['party_attack']<before['party_attack'],'adopted Attack reduction not reflected in native damage')
    return {'parent_damage':old,'candidate_damage':new,'parent_attack':before['party_attack'],'candidate_attack':after['party_attack']}


def run(out,jobs=4):
    out=out.absolute();rel=out.resolve().relative_to((ROOT/'.local').resolve());need(rel.parts and not any(p.is_symlink() for p in (out,*out.parents)),'unsafe output')
    out.mkdir(parents=True,exist_ok=True);need(type(jobs) is int and 1<=jobs<=4,'jobs must be 1..4')
    parent=ROOT/base.PARENT;child=ROOT/'.local/final-integration-candidate/candidate.gba';seed=ROOT/base.SEED
    inputs={str(p.relative_to(ROOT)):identity(p.read_bytes()) for p in (parent,child,seed)}
    need(identity(parent.read_bytes())=={'size':33554432,'sha256':base.recipe.PARENT_SHA},'Stage82 parent differs')
    need(identity(child.read_bytes())=={'size':33554432,'sha256':base.FINAL_SHA},'Stage84 candidate differs')
    need(identity(seed.read_bytes())=={'size':131072,'sha256':base.SEED_SHA},'test seed differs')
    cfg=base.recipe.strict_json((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())
    domain=next(d for d in cfg['domains'] if d['id']=='p02')
    names={SOURCE,SELF,WORKFLOW,'scripts/run_modernization_p06_decided_e2e.py','scripts/run_modernization_p03_fullslots_e2e.py','tools/modernization_p06_decided_adjustments.py','config/active_play_baseline.json','infra/toolchain_manifest.json','infra/setup_github_actions.sh'}
    names.update(p for p,_ in base.EMBED)
    for d in (domain['runner'],*domain['dependencies']):
        need(identity((ROOT/d['path']).read_bytes())=={k:d[k] for k in ('size','sha256')},'inherited harness differs: '+d['path']);names.add(d['path'])
    bindings={name:identity((ROOT/name).read_bytes()) for name in sorted(names)}
    results=[];failures=[]
    try:
        with tempfile.TemporaryDirectory(prefix='p06-phase-',dir=ROOT/'.local') as td:
            work=Path(td)
            for source,target in base.EMBED:(work/target).write_text(base.embed((ROOT/source).read_text(),'phase_old_'+Path(target).stem))
            binary=work/'runner';cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),SOURCE,'-lmgba','-o',str(binary)]
            _,_,p=api.capture(cmd,out/'compile',120);need(api.require_exited(p)==0,'C compilation failed; inspect compile.stderr')
            compiler,_,p=api.capture(['cc','--version'],out/'cc-version',10);need(api.require_exited(p)==0,'compiler identity failed')
            mgba,_,p=api.capture(['dpkg-query','-W','-f=${Version}','libmgba-dev'],out/'mgba-version',10);need(api.require_exited(p)==0,'mGBA identity failed')
            need(os.environ.get('GITHUB_ACTIONS')=='true' and b'13.3.0' in compiler and b'0.10.2' in mgba,'fixed GitHub toolchain required')
            for guard in base.GUARDS:
                stdout,stderr,p=api.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                need(api.require_exited(p)==1 and not stdout and stderr==b'P03 archive: host write after observation barrier\n','host-write guard failed: '+guard)
            def one(index):
                label=CASES[index];private=work/(label+'.srm');shutil.copyfile(seed,private);rom=parent if index==8 else child
                stdout,stderr,p=api.capture([str(binary),str(rom),str(private),inputs[str(rom.relative_to(ROOT))]['sha256'],base.SEED_SHA,str(index),str(out/label)],out/label,300)
                try:
                    need(b'mGBA[' not in stderr,'emulator warning/error')
                    value=validate(stdout,index,api.require_exited(p))
                    if index<3:validate_picture((out/(label+'-skills.ppm')).read_bytes())
                    return value,None
                except (OSError,ValueError,RuntimeError,KeyError,TypeError) as e:return None,{'case':label,'reason':str(e)}
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                for result,error in pool.map(one,range(len(CASES))):
                    if result:results.append(result)
                    if error:failures.append(error)
    finally:
        for name,bind in inputs.items():need(identity((ROOT/name).read_bytes())==bind,'input modified: '+name)
        for name,bind in bindings.items():need(identity((ROOT/name).read_bytes())==bind,'source modified: '+name)
    report={'schema_version':1,'status':'FAIL' if failures else 'PASS','scope':SCOPE,'inputs':inputs,'source_bindings':bindings,'cases':results,'failures':failures,'fresh_process_runs':10,'guards':list(base.GUARDS),'full_p06_acceptance':False,'release_ready':False,'active_baseline_changed':False}
    if not failures:
        need([r['case'] for r in results]==list(CASES),'missing/duplicate case')
        try:report['native_attack_comparison']=validate_attack_pair(results[8],results[9])
        except (ValueError,RuntimeError) as e:report['status']='FAIL';failures.append({'case':'attack-comparison','reason':str(e)})
    shots=sorted(out.glob('*.ppm'));report['screenshots']={p.name:identity(p.read_bytes()) for p in shots}
    (out/'result.json').write_bytes(stable(report));need(not failures,'native P06 case failed; inspect result.json and raw process output');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-directory',type=Path,default=ROOT/'.local/pr16-continuation/p06-phase');p.add_argument('--jobs',type=int,default=4)
    args=p.parse_args()
    try:print(json.dumps(run(args.output_directory,args.jobs),ensure_ascii=False))
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
