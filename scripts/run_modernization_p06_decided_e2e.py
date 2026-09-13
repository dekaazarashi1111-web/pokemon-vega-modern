#!/usr/bin/env python3
"""既決P06差分の生成、既存/新規個体の通常操作・保存互換を検証する。"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import modernization_p06_decided_adjustments as recipe
import run_modernization_p03_fullslots_e2e as capture_api

SCOPE = 'P06_DECIDED_SLOTS_NATIVE_CANDY_CROSS_ROM_COLD_SAVE'
SOURCE = 'tools/mgba_modernization_p06_decided_e2e.c'
SELF = 'scripts/run_modernization_p06_decided_e2e.py'
WORKFLOW = '.github/workflows/p06-decided-e2e.yml'
SEED = '.local/60_wild_species_root_repair.srm'
SEED_SHA = 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
PARENT = '.local/stage82-archive-ui/candidate.gba'
CASES = [(s,a,m) for s in (220,373) for a in (0,1) for m in (0,1)]
GUARDS = ('bus8','bus16','bus32','raw8','raw16','raw32','register')
# H/A/B/S/C/D: values in the accepted stable species rows, not ABI query output.
BASES = {220:[55,100,50,120,60,50],373:[106,75,65,116,58,72]}
ABILITIES_BEFORE = {220:[25,23],373:[74,39]}
ABILITIES_AFTER = {220:[131,120],373:[74,39]}
EMBED = [('tools/mgba_modernization_p03_archive_ui_e2e.c','p06_archive_embedded.c'),
         ('tools/mgba_modernization_p03_fullslots_e2e.c','p03a_fullslots_embedded.c'),
         ('tools/mgba_modernization_p03_learning_e2e.c','p03_learning_embedded.c'),
         ('tools/mgba_modernization_p02_stage71_acceptance_smoke.c','p03_p02_embedded.c')]
need = recipe.require


def stats(species: int, level: int, candidate: bool, personality: int, ivs: list, evs: list) -> list[int]:
    bases = BASES[species].copy()
    if candidate and species == 373:
        bases[1] = 45
    n = personality % 25
    output = []
    for i,base in enumerate(bases):
        value = (2*base+ivs[i]+evs[i]//4)*level//100
        if i == 0:
            value += level+10
        else:
            value += 5
            if n//5 != n%5:
                if i-1 == n//5:
                    value = value*110//100
                elif i-1 == n%5:
                    value = value*90//100
        output.append(value)
    return output


FINAL_SHA = '55cf145e7dd1c8e2568fe9c733b597f8c4bc3d31b7d6fa233a7b4821d1b62c3b'


def validate(raw: bytes, case: tuple[int,int,int], returncode: int, candidate_sha: str=recipe.CANDIDATE_SHA) -> dict:
    need(candidate_sha in (recipe.CANDIDATE_SHA, FINAL_SHA), 'unrecognized candidate identity')
    need(type(returncode) is int and returncode == 0,'process exit is not integer zero')
    s,slot,mode=case
    need(case in CASES,'unknown case')
    value=recipe.strict_json(raw)
    expected={'schema_version':1,'status':'OBSERVED','scope':SCOPE,'parent_sha256':recipe.PARENT_SHA,
              'candidate_sha256':candidate_sha,'species':s,'slot':slot,'mode':mode,
              'ability_before':(ABILITIES_AFTER if mode else ABILITIES_BEFORE)[s][slot],
              'ability_loaded':ABILITIES_AFTER[s][slot],'ability_final':ABILITIES_AFTER[s][slot],
              'initial_level':48,'final_level':49,'save_counter_delta':2,'normal_save_menu':True,
              'fresh_core_count':3,'cross_rom_100_bytes_equal':True,'candidate_cold_100_bytes_equal':True,
              'slot_preserved':True,'host_write_barriers':5,'native_creation_is_fixture':True,
              'ability_read_uses_native_abi':True,'full_p06_acceptance':False,'release_ready':False,'warnings_errors':0}
    dynamic={'personality','ivs','evs','initial_stats','loaded_stats','final_stats','bag_party_frame',
             'level_up_frame','field_frame','before_mon_hex','after_mon_hex'}
    need(type(value) is dict and set(value)==set(expected)|dynamic,'result schema differs')
    for key,want in expected.items():
        need(capture_api.same_typed(value[key],want),'result differs: '+key)
    pid=value['personality'];need(type(pid) is int and 0<=pid<2**32,'invalid personality')
    for key,limit in [('ivs',31),('evs',252)]:
        a=value[key];need(type(a) is list and len(a)==6 and all(type(n) is int and 0<=n<=limit for n in a),key+' differs')
    # CreateMon's fixed-IV fixture is zero-IV/zero-EV; native PID is read, never changed after creation.
    need(value['ivs']==[0]*6 and value['evs']==[0]*6,'fixture IV/EV changed')
    initial=stats(s,48,bool(mode),pid,value['ivs'],value['evs']);final=stats(s,49,True,pid,value['ivs'],value['evs'])
    for key,want in [('initial_stats',initial),('loaded_stats',initial),('final_stats',final)]:
        need(capture_api.same_typed(value[key],want),'independent stat formula mismatch: '+key)
    times=[value[k] for k in ('bag_party_frame','level_up_frame','field_frame')]
    need(all(type(v) is int and 0<v<15000 for v in times) and times[0]<times[1]<times[2], 'native route ordering differs')
    mons=[]
    for key,level,want_stats in [('before_mon_hex',48,initial),('after_mon_hex',49,final)]:
        text=value[key];need(type(text) is str and re.fullmatch('[0-9a-f]{200}',text) is not None,'mon byte snapshot differs')
        mon=bytes.fromhex(text);mons.append(mon)
        need(struct.unpack_from('<I',mon,0)[0]==pid,'PID snapshot differs')
        need(struct.unpack_from('<H',mon,32)[0]==s and mon[84]==level,'snapshot species/level differs')
        need(list(struct.unpack_from('<6H',mon,88))==want_stats,'snapshot stat bytes differ')
        need(list(struct.unpack_from('<4H',mon,44))==[33,81,407,52] and mon[52:56]==bytes([10]*4),'retained move/PP snapshot differs')
    need(mons[0][:8]==mons[1][:8] and mons[0][68:72]==mons[1][68:72], 'saved individual/IV/slot bytes changed')
    return value


def embed(text: str, entry: str) -> str:
    pattern=r'\bint\s+main\s*\('
    need(len(re.findall(pattern,text))==1,'embedded main is not unique')
    return re.sub(pattern,'int '+entry+'(',text,count=1)


def output_dir(path: Path) -> Path:
    path=path.absolute();relative=path.resolve().relative_to((ROOT/'.local').resolve())
    need(bool(relative.parts),'cannot use .local root as output')
    q=path
    while q!=ROOT:
        need(not q.is_symlink(),'symlink output');q=q.parent
    path.mkdir(parents=True,exist_ok=True)
    # Remove only owned products. Workflow stdout/fixed-toolchain logs are not ours.
    labels=['compile','cc-version','mgba-version']+['guard-'+x for x in GUARDS]+[f'{s}-{a}-{m}' for s,a,m in CASES]
    names=['result.json','candidate.json']+[label+suffix for label in labels for suffix in ('.stdout','.stderr','.process.json')]
    for name in names:
        p=path/name;need(not p.is_symlink(),'symlink output file');p.unlink(missing_ok=True)
    return path


def run(parent: Path, output: Path, jobs: int=4, candidate_stage: int=83) -> dict:
    need(type(candidate_stage) is int and candidate_stage in (83,84), 'unsupported candidate stage')
    parent=parent.resolve()
    need(not parent.is_relative_to(output.resolve()),'parent must not be inside owned output')
    out=output_dir(output)
    need(type(jobs) is int and 1<=jobs<=4,'jobs must be 1..4')
    parent=parent.resolve();seed=ROOT/SEED
    parent_id=recipe.identity(parent.read_bytes());seed_id=recipe.identity(seed.read_bytes())
    need(parent_id=={'size':33554432,'sha256':recipe.PARENT_SHA},'fixed Stage82 parent differs')
    need(seed_id=={'size':131072,'sha256':SEED_SHA},'seed differs')
    child,report=recipe.build(parent.read_bytes())
    if candidate_stage == 84:
        import modernization_empty_move_pp_repair as empty_pp
        child,repair_report=empty_pp.build(child)
        need(recipe.identity(child)=={'size':33554432,'sha256':FINAL_SHA}, 'fixed final candidate differs')
        report={'candidate':repair_report['candidate'],'p06_adoption':report,'stage84_repair':repair_report}
    candidate_sha=report['candidate']['sha256']
    (out/'candidate.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    cfgpath='config/modernization_stage79_cumulative_mgba.json'
    domain=next(d for d in recipe.strict_json((ROOT/cfgpath).read_bytes())['domains'] if d['id']=='p02')
    names={SOURCE,SELF,WORKFLOW,'tools/modernization_p06_decided_adjustments.py',recipe.CONTRACT,cfgpath,
           'scripts/run_modernization_p03_fullslots_e2e.py','scripts/run_modernization_stage82_github_domain.py',
           'tests/test_modernization_p06_decided_e2e.py','tests/fixtures/p06_decided_native_template.json',
           'config/active_play_baseline.json','infra/toolchain_manifest.json','infra/setup_github_actions.sh'}
    if candidate_stage == 84:
        names.add('tools/modernization_empty_move_pp_repair.py')
    names.update(p for p,_ in EMBED)
    for row in (domain['runner'],*domain['dependencies']):
        need(recipe.identity((ROOT/row['path']).read_bytes())=={k:row[k] for k in ('size','sha256')},'historical harness differs: '+row['path'])
        names.add(row['path'])
    spec=recipe.specification();names.update(s['path'] for s in spec['sources'].values());names.add(spec['historical_contract']['path'])
    names.update(('manifests/species_ids.csv','manifests/ability_ids.csv'))
    bindings={p:recipe.identity(recipe.safe_read(ROOT,p)) for p in sorted(names)}
    results=[]
    try:
        with tempfile.TemporaryDirectory(prefix='p06-decided-',dir=ROOT/'.local') as td:
            work=Path(td);childpath=work/'candidate.gba';childpath.write_bytes(child);childpath.chmod(0o444)
            for source,target in EMBED:
                (work/target).write_text(embed((ROOT/source).read_text(),'p06_old_'+Path(target).stem))
            binary=work/'runner'
            cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),SOURCE,'-lmgba','-o',str(binary)]
            _,_,p=capture_api.capture(cmd,out/'compile',120);need(capture_api.require_exited(p)==0,'C compilation failed')
            compiler,_,p=capture_api.capture(['cc','--version'],out/'cc-version',10);need(capture_api.require_exited(p)==0,'compiler query failed')
            mgba,_,p=capture_api.capture(['pkg-config','--modversion','mgba'],out/'mgba-version',10)
            # libmGBA 0.10.2 Ubuntu package has no .pc file; use dpkg on the fixed runner.
            if capture_api.require_exited(p)!=0:
                mgba,_,p=capture_api.capture(['dpkg-query','-W','-f=${Version}', 'libmgba-dev'],out/'mgba-version',10)
            need(capture_api.require_exited(p)==0 or os.environ.get('P06_LOCAL_DIAGNOSTIC')=='1','mGBA identity query failed')
            for guard in GUARDS:
                stdout,stderr,p=capture_api.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                need(capture_api.require_exited(p)==1 and not stdout and stderr==b'P03 archive: host write after observation barrier\n','host write guard failed')
            def one(case):
                s,a,m=case;label=f'{s}-{a}-{m}';private=work/(label+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,p=capture_api.capture([str(binary),str(parent),str(childpath),str(private),recipe.PARENT_SHA,candidate_sha,SEED_SHA,str(s),str(a),str(m)],out/label,240)
                need(b'mGBA[' not in stderr,'emulator warning/error')
                return validate(stdout,case,capture_api.require_exited(p),candidate_sha)
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                results=list(pool.map(one,CASES))
            need(recipe.identity(childpath.read_bytes())==report['candidate'],'candidate changed during tests')
    finally:
        need(recipe.identity(parent.read_bytes())==parent_id,'parent modified')
        need(recipe.identity(seed.read_bytes())==seed_id,'seed modified')
        for name,bind in bindings.items():
            need(recipe.identity(recipe.safe_read(ROOT,name))==bind,'source changed: '+name)
    need([(x['species'],x['slot'],x['mode']) for x in results]==CASES,'missing/duplicate test case')
    formal=bool(os.environ.get('GITHUB_ACTIONS')=='true' and b'13.3.0' in compiler and b'0.10.2' in mgba)
    need(os.environ.get('GITHUB_ACTIONS')!='true' or formal,'fixed GitHub compiler/emulator identity differs')
    result={'schema_version':1,'status':'PASS','scope':SCOPE,'validation_class':'FIXED_GITHUB' if formal else 'LOCAL_DIAGNOSTIC',
            'candidate_stage':candidate_stage,'parent':parent_id,'candidate':report['candidate'],'source_bindings':bindings,
            'fresh_process_runs':8,'core_instances':24,'cache_reuse':0,'source_decided_species_count':2,
            'existing_save_cases':4,'new_mon_cases':4,'guards':list(GUARDS),'cases':results,
            'full_p06_acceptance':False,'release_ready':False,'active_baseline_changed':False}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    return result


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',type=Path,default=ROOT/PARENT)
    parser.add_argument('--output-directory',type=Path,default=ROOT/'.local/p06-decided')
    parser.add_argument('--jobs',type=int,default=4)
    parser.add_argument('--candidate-stage',type=int,choices=(83,84),default=83)
    args=parser.parse_args(argv)
    try:
        print(json.dumps(run(args.parent,args.output_directory,args.jobs,args.candidate_stage),ensure_ascii=False,sort_keys=True,indent=2))
        return 0
    except (OSError,ValueError,KeyError,RuntimeError) as e:
        print('P06 ERROR: '+str(e),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
