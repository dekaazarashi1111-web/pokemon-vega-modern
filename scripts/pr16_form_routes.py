#!/usr/bin/env python3
"""Physical Rotom service acceptance; fixed inputs are not natural acquisition."""
from concurrent.futures import ThreadPoolExecutor
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
SELF='scripts/pr16_form_routes.py'
SOURCE='tools/mgba_pr16_form_routes.c'
TEST='tests/test_pr16_form_routes.py'
WORKFLOW='.github/workflows/pr16-form-routes.yml'
MODEL='content/collection_supply_v1/canonical_model.json'
MODEL_SHA='fb8066c0a8140da079b1e947cdfb6c76e987cf0c2514456a86868ec554f061d0'
OUT=ROOT/'.local/pr16-form-routes'
SCOPE='PR16_PHYSICAL_ROTOM_HOST_PARTY_FORM_SAVE'
CASES=('heat-roundtrip','wash-roundtrip','frost-roundtrip','fan-roundtrip','mow-roundtrip',
       'compact-removal','full-denied','root-cancel','forms-cancel','party-cancel')
SIGNATURES=(315,56,59,373,401)
PP=(5,5,5,15,5)
TRACE=('interaction','root','service','party','selection','returned','saved','reloaded')


def expected(name):
    need(name in CASES,'unknown physical form case')
    i=CASES.index(name);rounds=2 if i<5 else 1
    full=i==6;compact=i==5
    return dict(schema_version=1,status='PASS',scope=SCOPE,case=name,rom_sha256=repaired.ROM_SHA,
                species=742,moves=[84,109,86,33 if full else 0],pp=[7,8,9,6 if full else 0],
                pp_bonuses=229 if full else 57 if compact else 37,
                signature_pp=PP[i] if i<5 else 5,result=1 if full else 20 if i==9 else 2 if i in (7,8) else 0,
                rounds=rounds,fresh_cores=rounds+1,automatic_saves=rounds if i<6 else 0,
                manual_saves=rounds,physical_host=[1,36,6,3],host_index=3,selected_party_slot=1 if i<7 else 6,
                host_write_barriers=7,rtc_flash_bytes_preserved=131072,test_mode=False,
                party_byte_preserved_on_reload=True,nonselected_preserved=True,
                starting_progress_individual_map_are_fixtures=True,release_ready=False,warnings_errors=0)


def validate(raw,name,code):
    need(type(code) is int and code==0,'form process did not exit integer zero')
    row=common.strict_json(raw);want=expected(name)
    need(type(row) is dict and set(row)==set(want)|{'traces','total_frames'},'form result schema differs')
    for key,value in want.items():need(common.same_typed(row[key],value),'form result differs: '+key)
    need(type(row['total_frames']) is int and 1<=row['total_frames']<=600000,'invalid form frame count')
    traces=row['traces'];need(type(traces) is list and len(traces)==want['rounds'],'form round count differs')
    i=CASES.index(name);active=[k for k in TRACE if not (k=='service' and i==7 or k=='party' and i in (7,8) or k=='selection' and i in (7,8,9))]
    last=0
    for trace in traces:
        need(type(trace) is dict and set(trace)==set(TRACE),'form witness schema differs')
        for k in TRACE:
            need(type(trace[k]) is int and 0<=trace[k]<=row['total_frames'],'invalid form witness')
            need((trace[k]>0)==(k in active),'form cancellation/operation witness differs')
        need(last<trace['interaction'],'form rounds overlap')
        need(all(trace[a]<trace[b] for a,b in zip(active,active[1:])),'physical form sequence incomplete')
        last=trace['reloaded']
    return row


def oracle(raw):
    s=repaired.layer.source;model=json.loads(s.checked(ROOT/MODEL,MODEL_SHA))
    need(model['service_form_indices'][:5]==list(range(37,42)),'physical form menu ordering differs')
    host=model['hosts'][3];need(host['service_id']==3 and host['physical']==dict(elevation=3,host_key='RAID_HOST_TOHOKU_SKY',map_group=1,map_num=36,service='FORM',x=6,y=3),'authored form host differs')
    for index,row in enumerate(model['forms'][37:42]):
        need(row['base_species']==742 and row['target_species']==894+index and row['unlock_id']==6 and row['method_id']==4,'Rotom service row differs')
    state=_stage_map_state(raw,1,36);data=bytes.fromhex(state['bg_hex']);matches=[]
    for offset in range(0,len(data),12):
        x,y,elev,kind=struct.unpack_from('<hhBB',data,offset)
        if (x,y,elev)==(6,3,3):matches.append((kind,struct.unpack_from('<I',data,offset+8)[0]))
    need(len(matches)==1 and matches[0][0]==0,'authored form BG event is not unique/type 0')
    address=matches[0][1];at=address-0x08000000
    need(0<=at<=len(raw)-32,'physical form script pointer invalid')
    prefix=bytes.fromhex('6a160480030023115b4009')
    need(raw[at:at+len(prefix)]==prefix,'authored BG does not lock/set host 3/call actual service')
    pp_root=struct.unpack_from('<I',raw,0x1cc)[0]-0x08000000
    need(pp_root==0x10421f4,'canonical PP table differs')
    need(tuple(raw[pp_root+12*m+4] for m in SIGNATURES)==PP,'Rotom signature canonical PP differs')
    return dict(candidate=repaired.identity(raw),authored_host=host,form_rows=model['forms'][37:42],
                bg_script_address=hex(address),bg_script_prefix=prefix.hex(),signature_moves=list(SIGNATURES),
                signature_pp=list(PP),starting_progress_and_individual_fixture=True)


def run():
    m=base.load();out=m.prepare_output(OUT);(out/'result.json').unlink(missing_ok=True)
    s=repaired.layer.source;candidate=ROOT/repaired.ROM;seed=ROOT/m.SEED
    raw=s.checked(candidate,repaired.ROM_SHA);s.checked(seed,m.SEED_SHA)
    audit=oracle(raw);(out/'oracle.json').write_bytes(repaired.stable(audit))
    helper=s.checked(ROOT/base.PARENT_C,base.PARENT_C_SHA).decode()
    dependencies={SELF,SOURCE,TEST,WORKFLOW,MODEL,base.SELF,base.PARENT,base.PARENT_C,
                  'scripts/pr16_repaired_acceptance.py','scripts/pr16_p07_preserved_layer.py',
                  'scripts/pr16_integration_continuation.py','scripts/run_modernization_p03_fullslots_e2e.py',
                  'tools/trainer_final/kanto_events.py','config/active_play_baseline.json','design/active_play_baseline.md',
                  *(p for p,_ in m.EMBEDDED)}
    cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes());p02=next(d for d in cfg['domains'] if d['id']=='p02')
    for binding in (p02['runner'],*p02['dependencies']):
        need(common.identity(ROOT/binding['path'])=={k:binding[k] for k in ('size','sha256')},'form embedded dependency differs')
        dependencies.add(binding['path'])
    bindings={p:common.identity(ROOT/p) for p in sorted(dependencies)}
    protected={str(p):common.identity(p) for p in (seed,candidate)};results=[];failures=[];guards=[]
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-form-',dir=ROOT/'.local') as td:
            work=Path(td)
            for i,(src,target) in enumerate(m.EMBEDDED):
                (work/target).write_text(m.embed((ROOT/src).read_text(),'form_embedded_'+str(i)))
            (work/'pr16_form_breeding_helpers.c').write_text(m.embed(helper,'form_breeding_helpers'))
            binary=work/'runner';_,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(ROOT/SOURCE),'-lmgba','-o',str(binary)],out/'compile',120)
            need(common.require_exited(process)==0,'form C compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);guards.append(guard)
            def one(name):
                private=work/(name+'.srm');shutil.copyfile(seed,private)
                stdout,stderr,process=common.capture([str(binary),str(candidate),str(private),repaired.ROM_SHA,m.SEED_SHA,name,str(out/name)],out/name,240)
                try:
                    row=validate(stdout,name,common.require_exited(process));need(b'mGBA[' not in stderr,'form emulator warning')
                    return dict(name=name,result=row,process=process),None
                except (ValueError,RuntimeError,KeyError,TypeError) as exc:return None,dict(name=name,error=str(exc),process=process)
            with ThreadPoolExecutor(max_workers=2) as pool:
                for row,error in pool.map(one,CASES):
                    if row:results.append(row)
                    if error:failures.append(error)
    finally:
        need(protected=={p:common.identity(Path(p)) for p in protected},'form original seed or candidate changed')
        need(bindings=={p:common.identity(ROOT/p) for p in bindings},'form protected source/baseline changed')
    report=dict(schema_version=1,status='FAIL' if failures else 'PASS',scope=SCOPE,candidate=repaired.identity(raw),
                oracle=audit,sources=bindings,results=results,failures=failures,guard_checks=guards,
                actual_new_processes=len(CASES),successful_fresh_cores=sum(r['result']['fresh_cores'] for r in results),
                physical_rotom_service_accepted=not failures,other_form_and_egg_supply_accepted=False,
                full_p03_acceptance=False,release_ready=False,old_runs_relabelled=0)
    (out/'result.json').write_bytes(repaired.stable(report));need(not failures,'physical form route failed; inspect original stderr/screenshots')
    return report

if __name__=='__main__':
    try:print(json.dumps(run(),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,KeyError,TypeError,struct.error) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(1)
