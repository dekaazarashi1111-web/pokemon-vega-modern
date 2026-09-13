#!/usr/bin/env python3
"""Guarded natural walking/capture/cold-save, not gear or full P05 acceptance."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_shop_display_repair as repair
import pr16_capture_geometry as geometry
import pr16_p05_root_diagnostics as diagnostics
shop=repair.probe.shop;r=shop.repaired;need=r.need;common=shop.common
SELF='scripts/pr16_natural_capture.py'
SOURCE='tools/mgba_pr16_natural_capture.c'
TEST='tests/test_pr16_natural_capture.py'
WORKFLOW='.github/workflows/pr16-natural-capture.yml'
SHA='e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267'
SCOPE='PR16_NATURAL_WALK_CAPTURE_COLD_SAVE'
OUT=ROOT/'.local/pr16-natural-capture'
CASES={'cave-113':(113,[2,1],[3,1]),'cave-118':(118,[11,4],[12,4])}
TRACE=('walking','encounter','bag','caught','saved','reloaded')
DYNAMIC={'level','personality','walking_steps','encounters','escaped','total_frames','witness'}
EVENT=re.compile(rb'^NATURAL_ENCOUNTER number=(\d+) step=(\d+) species=(\d+) level=(\d+) flags=([0-9a-f]{8}) frame=(\d+)$',re.M)


def expected(name):
    need(name in CASES,'unknown natural-capture case')
    return dict(schema_version=1,status='PASS',scope=SCOPE,case=name,rom_sha256=SHA,species=411,map=CASES[name][0],
        bag_openings=1,outcome=7,manual_saves=1,fresh_cores=2,host_write_barriers=7,ball_consumed=1,
        party_and_inventory_persisted=True,map_lead_ball_are_fixtures=True,target_and_rng_injected=False,
        natural_capture_accepted=True,gear_acquisition_accepted=False,battle_connection_accepted=False,
        full_p05_acceptance=False,release_ready=False,warnings_errors=0)


def oracle(raw):
    need(r.identity(raw)==dict(size=33554432,sha256=SHA),'natural capture candidate differs')
    catalogue=diagnostics.wild_catalogue(raw);rows={}
    for name,(number,start,end) in CASES.items():
        owners=[h for h in catalogue['headers'] if h['group']==1 and h['map']==number and h['first_coordinate_owner']]
        need(len(owners)==1,'natural target map first header is ambiguous')
        table=owners[0]['tables']['land'];need('slots' in table and any(s['species']==411 for s in table['slots']),'first native land table lacks target')
        model=geometry.geometry(raw,1,number)
        pairs=[p for p in model['walkable_pairs'] if p['start']==start and p['end']==end]
        need(len(pairs)==1 and pairs[0]['behavior']==8,'audited cave walking pair differs')
        rows[name]=dict(group=1,map=number,header=owners[0]['header'],table=table,pair=pairs[0],
                        map_geometry=r.identity(r.stable(model)))
    return dict(candidate=r.identity(raw),cases=rows,unrelated_catalogue_diagnostics=catalogue['diagnostics'],
                unrelated_catalogue_complete=catalogue['complete_valid_catalogue'],target_injected=False,
                starting_map_lead_and_ball_are_fixtures=True)


def validate(raw,stderr,name,code,audit):
    need(type(code) is int and code==0,'natural capture did not exit integer zero')
    value=common.strict_json(raw);want=expected(name)
    need(type(value) is dict and set(value)==set(want)|DYNAMIC,'natural-capture result schema differs')
    for key,target in want.items():need(common.same_typed(value[key],target),'natural-capture result differs: '+key)
    for key in DYNAMIC-{'witness'}:need(type(value[key]) is int,'noninteger natural-capture counter: '+key)
    need(1<=value['walking_steps']<=2048 and 1<=value['encounters']<=64 and value['escaped']==value['encounters']-1,'natural walking/escape evidence incomplete')
    need(1<=value['level']<=100 and 0<=value['personality']<=0xffffffff and 1<=value['total_frames']<=600000,'natural individual/frame values invalid')
    trace=value['witness'];need(type(trace) is dict and set(trace)==set(TRACE),'natural-capture witness keys differ')
    need(all(type(trace[k]) is int and 1<=trace[k]<=value['total_frames'] for k in TRACE),'natural-capture witness unbounded')
    need(all(trace[a]<trace[b] for a,b in zip(TRACE,TRACE[1:])),'natural walk/capture/save sequence incomplete')
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'natural-capture emulator warning or nonbyte stderr')
    events=[dict(number=int(n),step=int(s),species=int(p),level=int(l),flags=int(f,16),frame=int(t)) for n,s,p,l,f,t in EVENT.findall(stderr)]
    need(len(events)==value['encounters'],'natural encounter log/count differs')
    slots=audit['cases'][name]['table']['slots'];previous_step=0;previous_frame=trace['walking']-1
    for index,event in enumerate(events):
        need(event['number']==index+1 and previous_step<event['step']<=value['walking_steps'] and previous_frame<event['frame']<=trace['encounter'],'natural encounter sequence differs')
        need(not(event['flags']&8),'encounter was a trainer battle')
        need(any(s['species']==event['species'] and s['min']<=event['level']<=s['max'] for s in slots),'encounter not present in first native land table')
        need((event['species']==411)==(index==len(events)-1),'target was skipped or not the captured final encounter')
        previous_step=event['step'];previous_frame=event['frame']
    need(events[-1]['level']==value['level'] and events[-1]['step']==value['walking_steps'] and events[-1]['frame']==trace['encounter'],'target identity/witness differs')
    return value


def run():
    m=shop.base.load();out=m.prepare_output(OUT);(out/'result.json').unlink(missing_ok=True)
    recipe=repair.run();candidate=repair.OUTPUT/'candidate.gba';raw=r.layer.source.checked(candidate,SHA)
    seed=ROOT/m.SEED;r.layer.source.checked(seed,m.SEED_SHA);audit=oracle(raw)
    (out/'oracle.json').write_bytes(r.stable(audit));(out/'candidate.json').write_bytes(r.stable(recipe))
    paths={SELF,SOURCE,TEST,WORKFLOW,repair.SELF,repair.probe.SELF,shop.SELF,shop.SOURCE,shop.base.PARENT_C,shop.base.SELF,
           shop.base.PARENT,'scripts/pr16_capture_geometry.py','scripts/pr16_p05_root_diagnostics.py','scripts/pr16_receiver_audit.py',
           'scripts/pr16_repaired_acceptance.py','scripts/pr16_p07_preserved_layer.py','scripts/pr16_integration_continuation.py',
           'scripts/pr16_evolution_learning_repair.py','scripts/run_modernization_p03_fullslots_e2e.py',
           'config/active_play_baseline.json','design/active_play_baseline.md',*(p for p,_ in m.EMBEDDED)}
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes());p02=next(d for d in cfg['domains'] if d['id']=='p02')
    for binding in (p02['runner'],*p02['dependencies']):
        need(common.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'capture controller dependency differs');paths.add(binding['path'])
    bindings={p:common.identity(ROOT/p) for p in sorted(paths)}
    protected={str(p):common.identity(p) for p in (seed,candidate)};guards=[];results=[];failures=[]
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-natural-capture-',dir=ROOT/'.local') as td:
            work=Path(td)
            for i,(src,target) in enumerate(m.EMBEDDED):(work/target).write_text(m.embed((ROOT/src).read_text(),'capture_embedded_'+str(i)))
            (work/'pr16_shop_breeding_helpers.c').write_text(m.embed((ROOT/shop.base.PARENT_C).read_text(),'capture_breeding_helpers'))
            (work/'pr16_capture_shop_helpers.c').write_text(m.embed((ROOT/shop.SOURCE).read_text(),'capture_shop_helpers'))
            binary=work/'runner'
            _,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(ROOT/SOURCE),'-lmgba','-o',str(binary)],out/'compile',120)
            need(common.require_exited(process)==0,'natural-capture controller compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10);m.validate_guard(stdout,stderr,process);guards.append(guard)
            def one(name):
                private=work/(name+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,process=common.capture([str(binary),str(candidate),str(private),SHA,m.SEED_SHA,name,str(out/name)],out/name,900)
                try:return dict(name=name,result=validate(stdout,stderr,name,common.require_exited(process),audit),process=process),None
                except (ValueError,RuntimeError,KeyError,TypeError) as exc:return None,dict(name=name,error=str(exc),process=process)
            with ThreadPoolExecutor(max_workers=2) as pool:
                for result,error in pool.map(one,CASES):
                    if result:results.append(result)
                    if error:failures.append(error)
    finally:
        need(protected=={p:common.identity(Path(p)) for p in protected},'natural-capture original input changed')
        need(bindings=={p:common.identity(ROOT/p) for p in bindings},'natural-capture source/baseline changed')
    report=dict(schema_version=1,status='FAIL' if failures else 'PASS',scope=SCOPE,candidate=r.identity(raw),oracle=audit,
                sources=bindings,guard_checks=guards,results=results,failures=failures,actual_new_processes=len(CASES),
                successful_fresh_cores=sum(v['result']['fresh_cores'] for v in results),natural_capture_accepted=not failures,
                gear_acquisition_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0)
    (out/'result.json').write_bytes(r.stable(report));need(not failures,'natural capture failed; inspect raw process, stderr and screenshots')
    return report

if __name__=='__main__':
    try:print(json.dumps(run(),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
