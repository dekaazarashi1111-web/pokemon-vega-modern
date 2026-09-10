#!/usr/bin/env python3
"""New executions on the exact integrated P07 ROM; never relabel old successes.

The original 46-case Stage82 runner/vectors stay immutable. Its transaction,
process, witness, and save validator is loaded in a separate namespace with one
explicit new ROM identity. New vectors are independently read from hash-fixed
physical tables, not from any runtime function under test.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
import pr16_p07_preserved_layer as layer
need=layer.need
identity=layer.identity
stable=layer.stable
ROM_SHA='beef0d6aaf5b9e1be04b3075a7e9a4f388110776763fa11c6a74fdc6a38310c7'
PARENT_VALIDATOR='scripts/run_modernization_p03_relearner_e2e.py'
PARENT_C='tools/mgba_modernization_p03_relearner_e2e.c'
PINS={PARENT_VALIDATOR:'51cd8dd85c7f5e6e28c1c435ce1fcca0bf3655f5620400c809339966d3cacc9b',
      PARENT_C:'79fa2dd982ef7a485d6d18cc0d4908c4a5eb438bf0bf1eccf5a227d92637e071',
      'tests/fixtures/p03_relearner_cases.json':'15e3a0d3e3da54db700fd226a558a598459fc026bd29013ca7af546821ad3d3b'}
SYMBOLS='generated/runtime/modernization_p03_stage73_consumer_runtime_symbols.json'
SPECS=(('taillow-memory-empty',10,13,0,1,2,457),
       ('taillow-memory-full',10,13,0,0,1,457),
       ('taillow-memory-cancel',10,13,0,3,1,457),
       ('taillow-egg-full',10,13,2,0,3,466),
       ('happiny-egg-first',364,10,2,1,2,461),
       ('happiny-egg-middle',364,10,2,0,1,464),
       ('happiny-egg-last',364,10,2,0,3,357),
       ('happiny-egg-cancel',364,10,2,3,1,357))


def validator():
    for path,sha in PINS.items():layer.source.checked(ROOT/path,sha)
    spec=importlib.util.spec_from_file_location('pr16_fresh_native_validator',ROOT/PARENT_VALIDATOR)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(module.ROM_SHA=='e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d','old candidate pin drift')
    # Only this isolated adapter targets the new, independently verified bytes.
    module.ROM_SHA=ROM_SHA
    return module


def u32(raw,off):return struct.unpack_from('<I',raw,off)[0]


def make_case(spec,pool,pp):
    name,sid,level,family,action,slot,target=spec
    known=[33,81,0,0] if action==1 else [33,81,45,52]
    before=[7,8,0,0] if action==1 else [7,8,9,10]
    candidates=list(dict.fromkeys(m for m in pool if m not in known))
    need(target in candidates and len(candidates)<=40,'target/candidate capacity differs: '+name)
    after=known.copy();after_pp=before.copy();bonuses=229
    if action<2:after[slot]=target;after_pp[slot]=pp;bonuses &= ~(3<<(slot*2))
    return dict(name=name,species=sid,level=level,family=family,action=action,slot=slot,
                index=candidates.index(target),dh=int(family==2),hof=int(family==2),herb=0,
                known=known,pp_before=before,pp_bonuses_before=229,candidates=candidates,
                expected=target,canonical_pp=pp if action<2 else 0,after=after,
                pp_after=after_pp,pp_bonuses_after=bonuses,denial_text=0)


def vectors(raw,api):
    need(identity(raw)=={'size':33554432,'sha256':ROM_SHA},'wrong integrated candidate')
    tables=layer.source.RomTables(raw,layer.COUNT,selected_species={10})
    symbols=json.loads((ROOT/SYMBOLS).read_text())['symbols']
    def exact(sid):
        index=int(symbols['Stage73_ExactEggIndex']['address'],16)-layer.BASE
        moves=int(symbols['Stage73_ExactEggMoves']['address'],16)-layer.BASE
        return layer.indexed(raw,index,moves,sid)
    def shared(sid):return layer.indexed(raw,layer.SHARED_INDEX,layer.SHARED_MOVES,sid)
    pools={(10,0):[m for m,lev in tables.level[10] if lev<=13]+layer.indexed(raw,layer.REMINDER_INDEX,layer.REMINDER_MOVES,10),
           (10,2):tables.egg[10]+shared(10),
           (364,2):exact(364)+[461,464,357]+shared(364)}
    need(457 in pools[10,0] and 466 in pools[10,2],'fixed V4 physical targets missing')
    need([69,215,217,716]==list(dict.fromkeys(m for m in exact(364)+shared(364) if m not in (33,81,45,52))),
         'Happiny P03 baseline differs from prior accepted vectors')
    move_table=u32(raw,0x1cc)-layer.BASE
    cases=[make_case(s,pools[s[1],s[3]],raw[move_table+s[-1]*12+4]) for s in SPECS]
    # Two unchanged exact-egg collision controls, not a rerun of all 46 cases.
    cases += [c for c in api.vectors() if c['name'] in ('egg-203-first','egg-203-last')]
    need(len(cases)==10 and len({c['name'] for c in cases})==10,'focused vector set differs')
    for c in cases:
        need(c['candidates'] and not set(c['known'])&set(c['candidates']),'known/duplicate move')
        need(len(c['candidates'])==len(set(c['candidates'])) and len(c['candidates'])<=40,'candidate overflow')
        need(c['index']<len(c['candidates']) and c['candidates'][c['index']]==c['expected'],'selection differs')
    return cases,{'source':'hash-fixed tables plus exact accepted P03 baseline vectors, no runtime calls',
                  'pools':{str(s)+'/'+str(f):v for (s,f),v in pools.items()},'symbols':identity((ROOT/SYMBOLS).read_bytes())}


def run(out,jobs=4):
    api=validator();out=api.prepare_output(out)
    need(os.environ.get('GITHUB_ACTIONS')=='true' and 1<=jobs<=4,'fixed Actions execution required')
    need(not any(os.environ.get(k) for k in ('C_INCLUDE_PATH','CPATH','LIBRARY_PATH','LD_LIBRARY_PATH')),'host toolchain override forbidden')
    candidate=ROOT/'.local/pr16-integrated-p07/candidate.gba';seed=ROOT/api.SEED
    raw=layer.source.checked(candidate,ROM_SHA);layer.source.checked(seed,api.SEED_SHA)
    cases,oracle=vectors(raw,api);(out/'vectors.json').write_bytes(stable({'cases':cases,'oracle':oracle}))
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_text())
    domain=next(d for d in cfg['domains'] if d['id']=='p02')
    sources=[PARENT_VALIDATOR,PARENT_C,'scripts/pr16_integrated_native.py','scripts/pr16_p07_preserved_layer.py',
             'tools/mgba_modernization_p03_archive_ui_e2e.c','tools/mgba_modernization_p03_fullslots_e2e.c',
             'tools/mgba_modernization_p03_learning_e2e.c','config/active_play_baseline.json','design/active_play_baseline.md',
             'infra/toolchain_manifest.json','infra/setup_github_actions.sh',SYMBOLS,*PINS]
    for binding in (domain['runner'],*domain['dependencies']):
        need(api.previous.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'inherited harness changed')
        sources.append(binding['path'])
    paths=sorted(set(sources));bindings={p:api.previous.identity(ROOT/p) for p in paths}
    protected={str(p):api.previous.identity(p) for p in (candidate,seed)}
    compiler,_,p=api.capture(['cc','--version'],out/'compiler',10);need(api.previous.require_exited(p)==0 and b'13.3.0' in compiler,'compiler differs')
    _,_,p=api.capture(['bash','infra/setup_github_actions.sh','--check'],out/'toolchain-check',120);need(api.previous.require_exited(p)==0,'toolchain check failed')
    results=[];failures=[];guards=[]
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-p07-native-',dir=ROOT/'.local') as name:
            work=Path(name)
            for src,dest,entry in [('tools/mgba_modernization_p03_fullslots_e2e.c','p03a_fullslots_embedded.c','old_fullslots_main'),
                                  ('tools/mgba_modernization_p03_learning_e2e.c','p03_learning_embedded.c','old_learning_main'),
                                  (domain['runner']['path'],'p03_p02_embedded.c','old_p02_main')]:
                (work/dest).write_text(api.previous.embed((ROOT/src).read_text(),entry))
            archive=(ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()
            need(archive.count('int main(int argc,char**argv)')==1,'archive main drift')
            (work/'p03r_archive_embedded.c').write_text(archive.replace('int main(int argc,char**argv)','int old_archive_main(int argc,char**argv)'))
            driver=(ROOT/PARENT_C).read_text()
            marker='c->setVideoBuffer(c,video,240);'
            need(driver.count(marker)==2,'renderer setup count differs')
            driver=driver.replace(marker,marker+'c->reset(c);')
            (work/'runner.c').write_text(driver);(out/'executed-driver.c').write_text(driver)
            (work/'p03r_vectors.h').write_text(api.header(cases));(out/'executed-vectors.h').write_text(api.header(cases))
            binary=work/'runner'
            _,_,p=api.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(work/'runner.c'),'-lmgba','-o',str(binary)],out/'compile',120)
            need(api.previous.require_exited(p)==0,'native C compile failed')
            for guard in api.GUARDS:
                stdout,stderr,p=api.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                need(api.previous.require_exited(p)==1 and not stdout and stderr==b'P03 archive: host write after observation barrier\n','write guard failed')
                guards.append(guard)
            def one(entry):
                i,c=entry;private=work/(c['name']+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,p=api.capture([str(binary),str(candidate),str(private),ROM_SHA,api.SEED_SHA,str(i)],out/c['name'],240)
                try:
                    value=api.validate_result(stdout,c,p,stderr)
                    return {'name':c['name'],'result':value,'process':p,'private_save_after':api.previous.identity(private)},None
                except (ValueError,OSError,KeyError,TypeError) as e:return None,{'name':c['name'],'error':str(e),'process':p}
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                for result,error in pool.map(one,enumerate(cases)):
                    if result:results.append(result)
                    if error:failures.append(error)
    finally:
        need(bindings=={p:api.previous.identity(ROOT/p) for p in paths},'protected source changed')
        need(protected=={p:api.previous.identity(Path(p)) for p in protected},'candidate or original seed changed')
    report={'schema_version':1,'status':'FAIL' if failures else 'PASS','scope':'P07_INTEGRATED_NATIVE_MEMORY_SAVE',
            'candidate':identity(raw),'source_bindings':bindings,'vectors':identity((out/'vectors.json').read_bytes()),
            'cases':results,'failures':failures,'host_write_guard_checks':guards,'new_processes':len(cases),
            'successful_processes':len(results),'successful_fresh_cores':len(results)*2,'old_runs_relabelled':0,
            'fixture_boundary':'species/moves/items/flags prepared before observations; no natural capture or breeding claim',
            'inherited_validator_new_identity_only':True,'full_p07_acceptance':False,'release_ready':False,'active_baseline_changed':False}
    (out/'result.json').write_bytes(stable(report));need(not failures,'native route failed; inspect exact raw outputs');return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.local/pr16-final-routes/native');p.add_argument('--jobs',type=int,default=4)
    args=p.parse_args()
    try:print(json.dumps(run(args.output,args.jobs),ensure_ascii=False))
    except (ValueError,OSError,KeyError,TypeError) as e:print(str(e),file=sys.stderr);raise SystemExit(1)
