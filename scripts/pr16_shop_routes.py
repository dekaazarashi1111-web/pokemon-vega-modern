#!/usr/bin/env python3
"""Physical six P05 stone acquisitions, not natural capture or battle acceptance."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_breeding_delta as base
from tools.trainer_final.kanto_events import _stage_map_state
repaired=base.repaired
need=repaired.need
common=base.load().common
SELF='scripts/pr16_shop_routes.py'
SOURCE='tools/mgba_pr16_shop_routes.c'
TEST='tests/test_pr16_shop_routes.py'
WORKFLOW='.github/workflows/pr16-shop-routes.yml'
CATALOG='content/modernization/mega_shop_catalog.json'
CHECKPOINT='content/modernization/mega_shop_checkpoint.json'
OUT=ROOT/'.local/pr16-shop-routes'
SCOPE='PR16_PHYSICAL_MEGA_SHOP_ACQUISITION_SAVE'
CASES={'feraligatr':(1016,0),'eelektross':(1012,0),'pyroar':(1031,0),
       'meganium':(1029,0),'excadrill':(1014,0),'scovillain':(1035,0),
       'cancel-first':(1012,1),'cancel-page':(1035,2),
       'insufficient-bp':(1012,3),'missing-ring':(1012,4)}
TRACE=('interaction','menu','selection','returned','saved','reloaded','revisit')


def expected(name):
    need(name in CASES,'unknown physical shop case')
    item,action=CASES[name];initial=15 if action==3 else 64
    return dict(schema_version=1,status='PASS',scope=SCOPE,case=name,rom_sha256=repaired.ROM_SHA,
                item=item,catalog_index=item-999,result=0 if action==0 else 14 if action==3 else 3 if action==4 else 2,
                pages=0 if action in (1,4) else (item-999)//5,quantity=int(action==0),
                bp_before=initial,bp_after=initial-(16 if action==0 else 0),automatic_saves=int(action==0),
                manual_saves=1,fresh_cores=2,host_write_barriers=7,rtc_flash_bytes_preserved=131072,
                physical_host=[96,5,14,24,19],inventory_and_party_preserved=True,
                claim_catalogue_rechecked=action!=4,map_ring_bp_claims_are_fixtures=True,
                natural_capture_accepted=False,battle_connection_accepted=False,
                full_p05_acceptance=False,release_ready=False,warnings_errors=0)


def validate(raw,name,code):
    need(type(code) is int and code==0,'shop process did not exit integer zero')
    row=common.strict_json(raw);want=expected(name)
    need(type(row) is dict and set(row)==set(want)|{'witness','total_frames'},'shop result schema differs')
    for key,value in want.items():need(common.same_typed(row[key],value),'shop result differs: '+key)
    need(type(row['total_frames']) is int and 1<=row['total_frames']<=600000,'invalid shop frame count')
    trace=row['witness'];need(type(trace) is dict and set(trace)==set(TRACE),'shop witness schema differs')
    active=[k for k in TRACE if CASES[name][1]!=4 or k not in ('menu','selection','revisit')]
    for key,value in trace.items():
        need(type(value) is int and 0<=value<=row['total_frames'],'invalid shop witness')
        need((value>0)==(key in active),'shop operation/denial witness differs')
    need(all(trace[a]<trace[b] for a,b in zip(active,active[1:])),'shop physical sequence incomplete')
    return row


def oracle(raw):
    need(repaired.identity(raw)=={'size':33554432,'sha256':repaired.ROM_SHA},'shop candidate differs')
    cfg=json.loads((ROOT/'config/modernization_mega_shop.json').read_bytes())
    need(cfg['map']==dict(group=96,map=5,local_id=14,x=24,y=19,clone_local_id=3),'authored shop location differs')
    payload=json.loads((ROOT/CHECKPOINT).read_bytes())['payload'];at=payload['offset']
    need(raw[at:at+8]==b'VEGAMS68','physical shop payload header differs')
    code=raw[payload['code_offset']:payload['code_offset']+payload['code_size']]
    need(hashlib.sha256(code).hexdigest()==payload['code_sha256'],'shop transaction implementation differs')
    opener=struct.unpack_from('<I',raw,at+56)[0];script=struct.unpack_from('<I',raw,at+64)[0]
    need(payload['code_address']<=opener<payload['code_address']+len(code) and opener&1,'shop opener outside fixed code')
    state=_stage_map_state(raw,96,5);objects=[x for x in state['objects'] if x[0]==14]
    need(len(objects)==1 and state['counts']['objects']==15,'shop NPC graph differs')
    obj=objects[0];need(struct.unpack_from('<HH',obj,4)==(24,19) and struct.unpack_from('<I',obj,16)[0]==script,'NPC does not bind fixed physical shop')
    prefix=b'\x6a\x5a\x23'+struct.pack('<I',opener)
    need(raw[script-0x08000000:script-0x08000000+len(prefix)]==prefix,'NPC does not lock/face/open the production shop')
    rows=json.loads((ROOT/CATALOG).read_bytes())['entries']
    need(len(rows)==45,'shop catalogue count differs')
    for i,r in enumerate(rows):need((r['index'],r['item_id'],r['price_bp'],r['quantity'],r['claim_flag'])==(i,999+i,16,1,0x14A0+i),'shop catalogue transaction contract differs')
    return dict(candidate=repaired.identity(raw),physical_host=cfg['map'],object_record=obj.hex(),
                script=hex(script),script_prefix=prefix.hex(),opener=hex(opener),code_sha256=payload['code_sha256'],
                selected_catalogue=[rows[item-999] for item,action in CASES.values() if action==0],
                pages=9,eligible_entries=45,fixture_boundary='START_MAP_RING_BP_AND_CLEARED_CLAIMS_ONLY',
                natural_capture_accepted=False,battle_connection_accepted=False)


def run():
    m=base.load();out=m.prepare_output(OUT);(out/'result.json').unlink(missing_ok=True)
    s=repaired.layer.source;candidate=ROOT/repaired.ROM;seed=ROOT/m.SEED
    raw=s.checked(candidate,repaired.ROM_SHA);s.checked(seed,m.SEED_SHA)
    audit=oracle(raw);(out/'oracle.json').write_bytes(repaired.stable(audit))
    helper=s.checked(ROOT/base.PARENT_C,base.PARENT_C_SHA).decode()
    paths={SELF,SOURCE,TEST,WORKFLOW,CATALOG,CHECKPOINT,'config/modernization_mega_shop.json',
           'overlays/modernization_mega_shop/modernization_mega_shop.c',base.SELF,base.PARENT,base.PARENT_C,
           'scripts/pr16_repaired_acceptance.py','scripts/pr16_p07_preserved_layer.py',
           'scripts/pr16_integration_continuation.py','scripts/run_modernization_p03_fullslots_e2e.py',
           'tools/trainer_final/kanto_events.py','config/active_play_baseline.json','design/active_play_baseline.md',
           *(p for p,_ in m.EMBEDDED)}
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes());p02=next(d for d in cfg['domains'] if d['id']=='p02')
    for binding in (p02['runner'],*p02['dependencies']):
        need(common.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'shop embedded dependency differs')
        paths.add(binding['path'])
    bindings={p:common.identity(ROOT/p) for p in sorted(paths)}
    protected={str(p):common.identity(p) for p in (seed,candidate)};results=[];failures=[];guards=[]
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-shop-',dir=ROOT/'.local') as td:
            work=Path(td)
            for i,(src,target) in enumerate(m.EMBEDDED):
                (work/target).write_text(m.embed((ROOT/src).read_text(),'shop_embedded_'+str(i)))
            (work/'pr16_shop_breeding_helpers.c').write_text(m.embed(helper,'shop_breeding_helpers'))
            binary=work/'runner';_,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(ROOT/SOURCE),'-lmgba','-o',str(binary)],out/'compile',120)
            need(common.require_exited(process)==0,'shop C compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);guards.append(guard)
            def one(name):
                private=work/(name+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,process=common.capture([str(binary),str(candidate),str(private),repaired.ROM_SHA,m.SEED_SHA,name,str(out/name)],out/name,240)
                try:
                    row=validate(stdout,name,common.require_exited(process));need(b'mGBA[' not in stderr,'shop emulator warning')
                    return dict(name=name,result=row,process=process),None
                except (ValueError,RuntimeError,KeyError,TypeError) as exc:return None,dict(name=name,error=str(exc),process=process)
            with ThreadPoolExecutor(max_workers=2) as pool:
                for row,error in pool.map(one,CASES):
                    if row:results.append(row)
                    if error:failures.append(error)
    finally:
        need(protected=={p:common.identity(Path(p)) for p in protected},'shop original seed or candidate changed')
        need(bindings=={p:common.identity(ROOT/p) for p in bindings},'shop protected source/baseline changed')
    report=dict(schema_version=1,status='FAIL' if failures else 'PASS',scope=SCOPE,candidate=repaired.identity(raw),
                oracle=audit,sources=bindings,results=results,failures=failures,guard_checks=guards,
                actual_new_processes=len(CASES),successful_fresh_cores=sum(r['result']['fresh_cores'] for r in results),
                physical_six_stone_shop_routes_accepted=not failures,natural_capture_accepted=False,
                battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0)
    (out/'result.json').write_bytes(repaired.stable(report));need(not failures,'physical shop route failed; inspect raw stderr/screenshots')
    return report

if __name__=='__main__':
    try:print(json.dumps(run(),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError,struct.error) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(1)
