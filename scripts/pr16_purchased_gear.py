#!/usr/bin/env python3
"""Physical purchase/Give/walking/Mega/save; initial ring/BP/party are fixtures."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_natural_capture as parent
import pr16_gear_route_probe as probe
need=parent.need;r=parent.r;common=parent.common;shop=parent.shop
SELF='scripts/pr16_purchased_gear.py';SOURCE='tools/mgba_pr16_purchased_gear.c'
TEST='tests/test_pr16_purchased_gear.py';WORKFLOW='.github/workflows/pr16-purchased-gear.yml'
OUT=ROOT/'.local/pr16-purchased-gear';SHA=parent.SHA
SCOPE='PR16_PURCHASE_GIVE_WALK_MEGA_COLD_SAVE'
CASES={'eelektross-active':1,'eelektross-no-toggle':0,'eelektross-cancel-toggle':2,'eelektross-cold-policy-reset':1}
TRACE=('interaction','purchased','bag','equipped','saved','reloaded','boundary','encounter','move_menu','spent','field','saved_again','reloaded_again')
DYNAMIC={'personality','enemy_species','enemy_level','move','pp_before','pp_after','outcome','walking_steps','total_frames','witness'}
EVENT=re.compile(rb'^GEAR_ENCOUNTER species=(\d+) level=(\d+) flags=([0-9a-f]{8}) frame=(\d+)$',re.M)


def expected(name):
    need(name in CASES,'unknown purchased gear case');active=name=='eelektross-active';cold=name=='eelektross-cold-policy-reset'
    return dict(schema_version=2,status='PASS',scope=SCOPE,case=name,rom_sha256=SHA,
        species=411,item=1012,mega_species=1634 if active else 411,ability=313 if active else 26,toggles=CASES[name],
        bp_before=64,bp_after=48,automatic_saves=1,manual_saves=2,fresh_cores=3 if cold else 2,cold_reload_before_encounter=cold,host_write_barriers=7,
        party_inventory_bp_persisted=True,physical_give=True,physical_map_transition=True,held_stone_not_consumed=True,
        initial_map_party_ring_bp_policy_are_fixtures=True,ring_bp_natural_acquisition_accepted=False,
        full_p05_acceptance=False,release_ready=False,warnings_errors=0)


def path(model,start,target):
    """Deterministic path through audited non-event ground/grass at one elevation."""
    cells={}
    for pair in model['walkable_pairs']:
        if pair['behavior'] not in (0,2):continue
        for xy in (pair['start'],pair['end']):
            xy=tuple(xy);value=(pair['elevation'],pair['behavior'])
            need(xy not in cells or cells[xy]==value,'inconsistent path cell')
            cells[xy]=value
    start,target=tuple(start),tuple(target)
    need(start in cells and target in cells,'physical path endpoint not audited')
    pending=deque([start]);before={start:None}
    while pending:
        here=pending.popleft()
        if here==target:break
        x,y=here
        for there in ((x,y-1),(x+1,y),(x-1,y),(x,y+1)):
            if there not in cells or cells[there][0]!=cells[here][0] or there in before:continue
            before[there]=here;pending.append(there)
    need(target in before,'no bounded physical path to grass')
    result=[];at=target
    while at!=start:result.append(list(at));at=before[at]
    return list(reversed(result))


def oracle(raw):
    graph=probe.inspect(raw,max_depth=1);need(not graph['errors'],'route probe has unresolved map errors')
    maps={(v['group'],v['map']):v for v in graph['maps']};town=maps[(96,5)];grass=maps[(96,17)]
    connections=[v for v in town['connections'] if v['direction']==2]
    need(connections==[dict(direction=2,offset=12,target_group=96,target_map=17)],'north map connection differs')
    need((town['geometry']['width'],town['geometry']['height'],grass['geometry']['width'],grass['geometry']['height'])==(48,40,24,40),'physical map dimensions differ')
    owners=[v for v in graph['reachable_wild_tables'] if (v['group'],v['map'])==(96,17) and v['first_coordinate_owner']]
    need(len(owners)==1,'natural grass owner ambiguous');owner=owners[0];table=owner['tables']['land']
    need(table['rate']>0 and len(table['slots'])==12,'grass table invalid')
    paths=dict(town=path(town['geometry'],[24,20],[23,0]),grass=path(grass['geometry'],[11,39],[14,30]))
    need(any(v['start']==[14,30] and v['end']==[15,30] and v['behavior']==2 for v in grass['geometry']['walkable_pairs']),'encounter grass pair not audited')
    return dict(candidate=r.identity(raw),paths=paths,connection=connections[0],grass_header=owner['header'],table=table,
                geometry={str(n):r.identity(r.stable(m['geometry'])) for n,m in ((5,town),(17,grass))},
                initial_map_party_ring_bp_policy_are_fixtures=True,no_post_observation_host_writes=True,
                natural_ring_bp_acquisition_accepted=False)


def route_header(audit):
    text='/* Generated from fixed current-ROM collision, elevation and event data. */\n'
    for key in ('town','grass'):
        rows=audit['paths'][key];need(0<len(rows)<=2048,'route size invalid')
        text+='static const unsigned k_'+key+'_path[][2]={'+','.join('{%dU,%dU}'%tuple(row) for row in rows)+'};\n'
    return text


def validate(raw,stderr,name,code,audit):
    need(type(code) is int and code==0,'gear controller did not exit integer zero')
    value=common.strict_json(raw);want=expected(name)
    need(type(value) is dict and set(value)==set(want)|DYNAMIC,'gear result schema differs')
    for key,target in want.items():need(common.same_typed(value[key],target),'gear result differs: '+key)
    need(all(type(value[k]) is int for k in DYNAMIC-{'witness'}),'gear counters are not integers')
    need(0<=value['personality']<=0xffffffff and 1<=value['total_frames']<=600000,'gear identity/frame bounds differ')
    need(len(audit['paths']['town'])+2<=value['walking_steps']<=2048,'gear walking count outside bound')
    need(1<=value['move']<=2048 and 1<=value['pp_before']<=64 and 0<=value['pp_after']<value['pp_before'] and value['pp_before']-value['pp_after']<=2 and value['outcome'] in (1,4),'gear native turn values invalid')
    trace=value['witness'];need(type(trace) is dict and set(trace)==set(TRACE)|{'toggle','mega'},'gear witness schema differs')
    need(all(type(v) is int and 0<=v<=value['total_frames'] for v in trace.values()),'gear witness values invalid')
    sequence=TRACE if value['cold_reload_before_encounter'] else tuple(k for k in TRACE if k!='reloaded')
    if not value['cold_reload_before_encounter']:need(trace['reloaded']==0,'same-session case fabricated an intermediate cold Continue')
    need(trace['interaction']>0 and all(trace[a]<trace[b] for a,b in zip(sequence,sequence[1:])) and trace['reloaded_again']==value['total_frames'],'gear physical purchase/equip/walk/save order differs')
    if CASES[name]:need(trace['move_menu']<trace['toggle']<trace['spent'],'gear toggle is not physical move menu input')
    else:need(trace['toggle']==0,'no-toggle control contains a toggle')
    if name=='eelektross-active':need(trace['toggle']<trace['mega']<trace['spent'],'gear native Mega sequence absent')
    else:need(trace['mega']==0,'gear negative control activated Mega')
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'gear emulator warning or nonbyte stderr')
    events=EVENT.findall(stderr);need(len(events)==1,'gear natural encounter original missing/duplicated')
    species,level,flags,frame=events[0];species,level,flags,frame=int(species),int(level),int(flags,16),int(frame)
    need(not(flags&8) and (species,level,frame)==(value['enemy_species'],value['enemy_level'],trace['encounter']),'gear encounter is not matching wild encounter')
    need(any(v['species']==species and v['min']<=level<=v['max'] for v in audit['table']['slots']),'gear opponent not in first native grass table')
    return value


def run():
    m=shop.base.load();out=m.prepare_output(OUT);(out/'result.json').unlink(missing_ok=True)
    recipe=parent.repair.run();candidate=parent.repair.OUTPUT/'candidate.gba';raw=r.layer.source.checked(candidate,SHA)
    seed=ROOT/m.SEED;r.layer.source.checked(seed,m.SEED_SHA);audit=oracle(raw);header=route_header(audit)
    (out/'oracle.json').write_bytes(r.stable(audit));(out/'candidate.json').write_bytes(r.stable(recipe));(out/'pr16_gear_route.h').write_text(header)
    paths={SELF,SOURCE,TEST,WORKFLOW,parent.SELF,parent.SOURCE,'scripts/pr16_gear_route_probe.py',parent.repair.SELF,parent.repair.probe.SELF,
           shop.SELF,shop.SOURCE,shop.base.PARENT_C,shop.base.SELF,shop.base.PARENT,
           'scripts/pr16_capture_geometry.py','scripts/pr16_p05_root_diagnostics.py','scripts/pr16_receiver_audit.py',
           'scripts/pr16_repaired_acceptance.py','scripts/pr16_p07_preserved_layer.py','scripts/pr16_integration_continuation.py',
           'scripts/pr16_evolution_learning_repair.py','scripts/run_modernization_p03_fullslots_e2e.py',
           'config/active_play_baseline.json','design/active_play_baseline.md','overlays/cfru/integration.c','overlays/cfru/integration.h','tools/modernization_p04_mega_runtime.py','config/modernization_p04_mega_runtime.json',*(p for p,_ in m.EMBEDDED)}
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes());p02=next(d for d in cfg['domains'] if d['id']=='p02')
    for binding in (p02['runner'],*p02['dependencies']):
        need(common.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'gear dependency differs');paths.add(binding['path'])
    bindings={p:common.identity(ROOT/p) for p in sorted(paths)}
    protected={str(p):common.identity(p) for p in (seed,candidate)};guards=[];results=[];failures=[];generated={}
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-purchased-gear-',dir=ROOT/'.local') as td:
            work=Path(td)
            for i,(src,target) in enumerate(m.EMBEDDED):generated[target]=m.embed((ROOT/src).read_text(),'gear_embedded_'+str(i))
            for src,target,label in ((shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','gear_breeding'),(shop.SOURCE,'pr16_capture_shop_helpers.c','gear_shop'),(parent.SOURCE,'pr16_gear_capture_helpers.c','gear_capture')):
                generated[target]=m.embed((ROOT/src).read_text(),label)
            generated['pr16_gear_route.h']=header
            for name,text in generated.items():(work/name).write_text(text)
            import zipfile
            with zipfile.ZipFile(out/'generated-controller.zip','w',zipfile.ZIP_DEFLATED) as z:
                for name,text in generated.items():z.writestr(name,text)
                z.writestr('controller.c',(ROOT/SOURCE).read_bytes())
            binary=work/'runner'
            _,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(ROOT/SOURCE),'-lmgba','-o',str(binary)],out/'compile',120)
            need(common.require_exited(process)==0,'gear controller compile failed')
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
        need(protected=={p:common.identity(Path(p)) for p in protected},'gear original input changed')
        need(bindings=={p:common.identity(ROOT/p) for p in bindings},'gear source/baseline changed')
    report=dict(schema_version=2,status='FAIL' if failures else 'PASS',scope=SCOPE,candidate=r.identity(raw),oracle=audit,
        sources=bindings,generated={p:r.identity(s.encode()) for p,s in generated.items()},guard_checks=guards,results=results,failures=failures,
        actual_new_processes=len(CASES),successful_fresh_cores=sum(v['result']['fresh_cores'] for v in results),
        purchased_gear_to_battle_accepted=not failures,initial_map_party_ring_bp_policy_are_fixtures=True,
        ring_bp_natural_acquisition_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0)
    (out/'result.json').write_bytes(r.stable(report));need(not failures,'purchased gear failed; inspect raw originals');return report

if __name__=='__main__':
    try:print(json.dumps(run()))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
