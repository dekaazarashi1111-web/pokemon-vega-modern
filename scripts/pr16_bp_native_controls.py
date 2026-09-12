#!/usr/bin/env python3
"""Run only requested new native Factory cancellation controls.

No accepted fixed-form, generic FORM, P07, shop or capture cases are replayed.
PASS_SCOPED_CONTROL is not a positive BP reward or a closed P05 physical gap.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
import pr16_fixed_form_acceptance as fixed

ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_bp_native_controls.py'
SOURCE='tools/mgba_pr16_bp_native_controls.c'
TEST='tests/test_pr16_bp_native_controls.py'
WORKFLOW='.github/workflows/pr16-bp-native-controls.yml'
REQUEST='.github/pr16-bp-controls-run.json'
OUT=ROOT/'.local/pr16-bp-native-controls'
SHA=fixed.SHA
SCOPE='PR16_P05_NATIVE_BP_CANCELLATION_CONTROLS'
CASES=('reception-cancel-unchanged','rental-cancel-save-continue')
TRACE=('interaction','tier','mode','confirm','rentals','cancel','field','saved','reloaded')
need,identity,stable=fixed.need,fixed.identity,fixed.stable


def selected(names):
    need(type(names) is list and 1<=len(names)<=len(CASES),'explicit bounded BP case request required')
    need(all(type(n) is str and n in CASES for n in names),'unknown BP control')
    need(len(set(names))==len(names),'duplicate BP control would replay a process')
    return names


def expected(name):
    need(name in CASES,'unknown BP control')
    rental=name==CASES[1]
    return dict(schema_version=1,status='PASS_SCOPED_CONTROL',scope=SCOPE,case=name,candidate_sha256=SHA,
        native_reception=True,native_rental_selection_entry=rental,native_cancel=True,party_bytes_verified=600,
        party_and_inventory_preserved=True,bp_before=0,bp_after=0,bp_earned=0,manual_saves=int(rental),
        fresh_cores=1+int(rental),automatic_full_saves=0,input_only_after_guard=True,host_write_barriers=7,
        initial_map_progress_party_factory_ledger_are_fixtures=True,native_ledger_sector_writes_are_not_full_saves=True,
        physical_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False,warnings_errors=0)


def validate(raw,stderr,name,code):
    need(type(code) is int and code==0,'BP controller did not exit integer zero')
    row=fixed.strict_json(raw);want=expected(name)
    dynamic={'save_counter_before','save_counter_before_manual','save_counter_after','total_frames','witness'}
    need(type(row) is dict and set(row)==set(want)|dynamic,'BP result schema differs')
    for key,value in want.items():need(type(row[key]) is type(value) and row[key]==value,'BP control result differs: '+key)
    for key in dynamic-{'witness'}:need(type(row[key]) is int and 0<=row[key]<=0xffffffff,'invalid BP integer')
    need(1<=row['total_frames']<=600000,'BP frame budget differs')
    need(row['save_counter_before']==row['save_counter_before_manual'],'cancellation performed a full save')
    need(row['save_counter_after']==row['save_counter_before']+row['manual_saves'],'BP save accounting differs')
    w=row['witness'];need(type(w) is dict and set(w)==set(TRACE),'BP witness schema differs')
    need(all(type(v) is int and 0<=v<=row['total_frames'] for v in w.values()),'BP witness value differs')
    order=TRACE if name==CASES[1] else ('interaction','tier','cancel','field')
    need(all(w[k]==0 for k in set(TRACE)-set(order)),'unexpected lifecycle in reception-only control')
    need(w[order[0]]>0 and all(w[a]<w[b] for a,b in zip(order,order[1:])),'native BP lifecycle incomplete')
    need(w[order[-1]]==row['total_frames'],'terminal BP observation absent')
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'mGBA warning/error in BP control')
    need(b'BP_CTRL label=fixture ' in stderr and b'BP_CTRL label=returned ' in stderr,'native controller trace absent')
    return row


def oracle(raw):
    need(identity(raw)==dict(size=33554432,sha256=SHA),'exact BP candidate differs')
    from tools.trainer_final.kanto_events import _stage_map_state
    state=_stage_map_state(raw,96,5)
    rows=[obj for obj in state['objects'] if obj[0]==2]
    need(len(rows)==1,'Factory receptionist missing/duplicate')
    obj=rows[0];need(struct.unpack_from('<HH',obj,4)==(20,19),'Factory receptionist coordinate differs')
    script=struct.unpack_from('<I',obj,16)[0];at=script-0x08000000
    need(0<=at<len(raw)-8 and raw[at:at+3]==b'\x6a\x5a\x23' and raw[at+7]==0x27,'Factory lock/face/call/wait binding differs')
    native=struct.unpack_from('<I',raw,at+3)[0]
    need(native&1 and 0x08000000<=native<0x0a000000,'Factory native reception pointer differs')
    return dict(candidate=identity(raw),map=dict(group=96,map=5,local_id=2,x=20,y=19),
        object_record=obj.hex(),script=script,native_reception=native,script_prefix=raw[at:at+8].hex(),
        native_trial_selection_expected=True,positive_bp_earning_claimed=False)


def run(names,output=OUT):
    selected(names)
    sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
    import pr16_purchased_gear as gear
    parent,shop,r,common=gear.parent,gear.shop,gear.r,gear.common
    m=shop.base.load();out=gear.evidence.prepare_output(ROOT,output)
    report=dict(schema_version=1,status='FAIL',scope=SCOPE,candidate=dict(size=33554432,sha256=SHA),
        requested_cases=names,results=[],failures=[],guard_checks=[],actual_new_processes=0,successful_fresh_cores=0,
        native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False,old_runs_relabelled=0)
    protected={};bindings={}
    try:
        recipe=parent.repair.run();candidate=parent.repair.OUTPUT/'candidate.gba';seed=ROOT/m.SEED
        raw=r.layer.source.checked(candidate,SHA);r.layer.source.checked(seed,m.SEED_SHA)
        route=gear.oracle(raw);report['oracle']=oracle(raw);(out/'candidate.json').write_bytes(stable(recipe))
        paths={SELF,SOURCE,TEST,WORKFLOW,REQUEST,shop.base.PARENT_C,shop.SOURCE,parent.SOURCE,gear.SOURCE,
            'overlays/factory_high_modes_v2/factory_high_modes_v2.h','overlays/factory_high_modes_v2/factory_high_modes_v2.c',
            'overlays/save_migration/save_migration.h','overlays/save_migration/save_migration.c',
            'overlays/facility_runtime/facility_runtime.c','scripts/build_facility_runtime.py',
            'config/factory_high_modes_v2.json','config/modernization_stage79_cumulative_mgba.json',
            'config/active_play_baseline.json','design/active_play_baseline.md',*(p for p,_ in m.EMBEDDED)}
        cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())
        p02=next(d for d in cfg['domains'] if d['id']=='p02')
        for bound in (p02['runner'],*p02['dependencies']):
            need(common.identity(ROOT/bound['path'])=={k:bound[k] for k in ('size','sha256')},'embedded BP dependency differs')
            paths.add(bound['path'])
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).resolve()
                if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
        bindings={p:identity((ROOT/p).read_bytes()) for p in sorted(paths)}
        protected={str(p):identity(p.read_bytes()) for p in (seed,candidate)}
        report['sources']=bindings
        with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(paths):
                data=(ROOT/p).read_bytes();data.decode('utf-8');need(not (ROOT/p).is_symlink() and b'\0' not in data,'unsafe BP source snapshot');z.writestr(p,data)
        with tempfile.TemporaryDirectory(prefix='pr16-bp-controls-',dir=ROOT/'.local') as temp:
            work=Path(temp);generated={}
            for i,(src,target) in enumerate(m.EMBEDDED):generated[target]=m.embed((ROOT/src).read_text(),'bp_embedded_'+str(i))
            for src,target,label in ((shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','bp_breeding'),
                (shop.SOURCE,'pr16_capture_shop_helpers.c','bp_shop'),(parent.SOURCE,'pr16_gear_capture_helpers.c','bp_capture'),
                (gear.SOURCE,'pr16_bp_native_helpers.c','bp_gear')):
                generated[target]=m.embed((ROOT/src).read_text(),label)
            generated['pr16_gear_route.h']=gear.route_header(route)
            for name,text in generated.items():(work/name).write_text(text)
            report['generated']={name:identity(text.encode()) for name,text in generated.items()}
            with zipfile.ZipFile(out/'generated-controller.zip','w',zipfile.ZIP_DEFLATED) as z:
                for name,text in generated.items():z.writestr(name,text)
                z.writestr('controller.c',(ROOT/SOURCE).read_bytes())
            binary=work/'runner'
            _,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(ROOT/SOURCE),'-lmgba','-o',str(binary)],out/'compile',120)
            need(common.require_exited(process)==0,'BP native control C compile failed')
            report['executable']=identity(binary.read_bytes())
            for guard in fixed.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);report['guard_checks'].append(guard)
            for name in names:
                scratch=work/(name+'.srm');shutil.copyfile(seed,scratch);report['actual_new_processes']+=1
                stdout,stderr,process=common.capture([str(binary),str(candidate),str(scratch),SHA,m.SEED_SHA,name,str(out/name)],out/name,900)
                try:
                    row=validate(stdout,stderr,name,common.require_exited(process))
                    suffixes=['fixture','reception-tier','returned']
                    if name==CASES[1]:suffixes+=['reception-mode','reception-confirm','rental-party','fresh-continue']
                    screens={}
                    for suffix in suffixes:
                        p=out/(name+'-'+suffix+'.ppm');screens[p.name]=identity(gear.evidence.read_ppm(p))
                    report['results'].append(dict(name=name,result=row,process=process,screens=screens,visual_review_completed=False))
                    report['successful_fresh_cores']+=row['fresh_cores']
                except (ValueError,RuntimeError,KeyError,TypeError,OSError) as error:
                    report['failures'].append(dict(name=name,error=str(error),process=process))
    except (ValueError,RuntimeError,KeyError,TypeError,OSError) as error:
        report['failures'].append(dict(stage='setup-or-execution',error=str(error)))
    finally:
        try:
            need(protected=={p:identity(Path(p).read_bytes()) for p in protected},'BP original seed/candidate changed')
            need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'BP protected sources changed')
        except (ValueError,OSError) as error:report['failures'].append(dict(stage='immutability',error=str(error)))
        if not report['failures'] and report['actual_new_processes']==len(names) and len(report['results'])==len(names) and report['guard_checks']==list(fixed.GUARDS):
            report['status']='PASS_REQUESTED_NATIVE_BP_CONTROLS_PENDING_EARNING'
        (out/'result.json').write_bytes(stable(report))
        members={p.name:identity(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
        receipt=dict(schema_version=1,status=report['status'],tested_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            candidate=report['candidate'],members=members,native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
        (out/'receipt.json').write_bytes(stable(receipt))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',action='append',required=True);parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();result=run(selected(args.case),args.output)
    print(json.dumps(dict(status=result['status'],actual_new_processes=result['actual_new_processes'],accepted_controls=len(result['results']),physical_bp_earning_accepted=False)))
    sys.exit(0 if result['status'].startswith('PASS_') else 1)
