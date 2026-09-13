#!/usr/bin/env python3
"""Read native three-selection dataflow on unchanged bffd; NOT BP acceptance."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_chooser_native as previous
need,identity,stable=previous.need,previous.identity,previous.stable
SELF='scripts/pr16_bp_selection_native.py'
SOURCE='tools/mgba_pr16_bp_selection_native.c'
WORKFLOW='.github/workflows/pr16-bp-selection-native.yml'
OUT=ROOT/'.local/pr16-bp-selection-native'
CASE='three-selection-probe'
STATUS='DIAGNOSTIC_THREE_SELECTED_SECOND_CHOOSER_NOT_BP'
SHA=previous.layer.SHA


def validate(raw,stderr,code):
    need(type(code) is int and code==0,'native three-selection probe failed')
    row=previous.fixed.strict_json(raw)
    want=dict(schema_version=1,status=STATUS,scope='PR16_P05_THREE_SELECTION_DIAGNOSTIC',case=CASE,candidate_sha256=SHA,
        selected_count=3,party_count=3,original_snapshot_bytes_verified=600,bp_earned=0,battle_started=False,save_counter=2,
        manual_saves=0,fresh_cores=1,host_write_barriers=7,input_only_after_guard=True,fixture_same_as_accepted_cancel=True,
        native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False,warnings_errors=0)
    dynamic={'selected_frame','second_chooser_frame','total_frames'}
    need(type(row) is dict and set(row)==set(want)|dynamic,'selection schema differs')
    for key,value in want.items():need(type(row[key]) is type(value) and row[key]==value,'selection result differs: '+key)
    need(all(type(row[k]) is int for k in dynamic),'non-integer native witness')
    need(0<row['selected_frame']<row['second_chooser_frame']==row['total_frames']<=24000,'selection witness order differs')
    need(b'BP_CTRL label=fixture ' in stderr and b'BP_READ name=cfru_selected_order ' in stderr and b'mGBA[' not in stderr,'native diagnostic trace absent/warning')
    return row


def run():
    import pr16_purchased_gear as gear
    parent,shop,r,common=gear.parent,gear.shop,gear.r,gear.common
    m=shop.base.load();out=gear.evidence.prepare_output(ROOT,OUT)
    report=dict(schema_version=1,status='FAIL',scope='THREE_SELECTION_DIAGNOSTIC_NOT_EARNING',candidate=dict(size=33554432,sha256=SHA),
        actual_new_processes=0,successful_fresh_cores=0,results=[],failures=[],guard_checks=[],native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
    bindings={};protected={}
    try:
        need(identity((ROOT/previous.control.SOURCE).read_bytes())['sha256']==previous.C_SOURCE_SHA,'historical controller changed')
        recipe=previous.layer.run();candidate=previous.layer.OUT/'candidate.gba';seed=ROOT/m.SEED
        raw=r.layer.source.checked(candidate,SHA);r.layer.source.checked(seed,m.SEED_SHA)
        original=(parent.repair.OUTPUT/'candidate.gba').read_bytes();geometry=gear.oracle(original)
        report['candidate_recipe']=dict(candidate=recipe['candidate'],crc32=recipe['crc32'],change=recipe['change'])
        report['chooser_observation']=previous.chooser.prepare(raw,out,identity,need,stable)
        paths={SELF,SOURCE,WORKFLOW,previous.SELF,previous.layer.SELF,previous.control.SOURCE,
            shop.base.PARENT_C,shop.SOURCE,parent.SOURCE,gear.SOURCE,'tests/test_pr16_bp_selection_native.py',
            'overlays/factory_high_modes_v2/factory_high_modes_v2.h','overlays/factory_high_modes_v2/factory_high_modes_v2.c',
            'overlays/save_migration/save_migration.h','overlays/save_migration/save_migration.c',
            'config/factory_high_modes_v2.json','config/modernization_stage79_cumulative_mgba.json',
            'config/active_play_baseline.json','design/active_play_baseline.md',*(p for p,_ in m.EMBEDDED)}
        cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes());p02=next(d for d in cfg['domains'] if d['id']=='p02')
        for bound in (p02['runner'],*p02['dependencies']):
            need(common.identity(ROOT/bound['path'])=={k:bound[k] for k in ('size','sha256')},'embedded dependency differs');paths.add(bound['path'])
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                path=Path(name).resolve()
                if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
        bindings={p:identity((ROOT/p).read_bytes()) for p in sorted(paths)};report['sources']=bindings
        protected={str(p):identity(p.read_bytes()) for p in (seed,candidate,parent.repair.OUTPUT/'candidate.gba')}
        with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(paths):
                data=(ROOT/p).read_bytes();data.decode('utf-8');need(not (ROOT/p).is_symlink() and b'\0' not in data,'unsafe source');z.writestr(p,data)
        with tempfile.TemporaryDirectory(prefix='pr16-bp-selection-',dir=ROOT/'.local') as temp:
            work=Path(temp);generated={};transforms=[]
            for i,(src,target) in enumerate(m.EMBEDDED):generated[target]=m.embed((ROOT/src).read_text(),'selection_embedded_'+str(i))
            for src,target,label in ((shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','selection_breeding'),
                (shop.SOURCE,'pr16_capture_shop_helpers.c','selection_shop'),(parent.SOURCE,'pr16_gear_capture_helpers.c','selection_capture'),
                (gear.SOURCE,'pr16_bp_native_helpers.c','selection_gear')):
                text=(ROOT/src).read_text()
                if src==parent.SOURCE:
                    before=f'#define N_SHA "{previous.layer.parent_layer.route.SHA}"';after=f'#define N_SHA "{SHA}"'
                    text=previous.transform(text,before,after);transforms.append(dict(source=src,before=before,after=after))
                generated[target]=m.embed(text,label)
            controller=(ROOT/previous.control.SOURCE).read_text()
            controller,observation=previous.chooser.instrument(controller,previous.transform);transforms.extend(observation)
            before='script=%08x';after='context_header_raw=%08x';controller=previous.transform(controller,before,after)
            transforms.append(dict(source=previous.control.SOURCE,before=before,after=after,scope='READ_ONLY_LABEL_CORRECTION'))
            generated['pr16_bp_control_embedded.c']=m.embed(controller,'selection_historical_control')
            generated['controller.c']=(ROOT/SOURCE).read_text();generated['pr16_gear_route.h']=gear.route_header(geometry)
            for name,text in generated.items():(work/name).write_text(text)
            report['source_transformations']=transforms;report['generated']={name:identity(text.encode()) for name,text in generated.items()}
            with zipfile.ZipFile(out/'generated-controller.zip','w',zipfile.ZIP_DEFLATED) as z:
                for name,text in generated.items():z.writestr(name,text)
            binary=work/'runner'
            _,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(work/'controller.c'),'-lmgba','-o',str(binary)],out/'compile',120)
            need(common.require_exited(process)==0,'selection controller compile failed');report['executable']=identity(binary.read_bytes())
            for guard in previous.fixed.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10);m.validate_guard(stdout,stderr,process);report['guard_checks'].append(guard)
            scratch=work/(CASE+'.srm');shutil.copyfile(seed,scratch);report['actual_new_processes']+=1
            stdout,stderr,process=common.capture([str(binary),str(candidate),str(scratch),SHA,m.SEED_SHA,CASE,str(out/CASE)],out/CASE,900)
            row=validate(stdout,stderr,common.require_exited(process));report['results'].append(dict(result=row,process=process));report['successful_fresh_cores']=1
            need(len(list(out.glob('*.ppm')))>=10,'missing bounded native screenshots')
    except (ValueError,RuntimeError,KeyError,TypeError,OSError) as error:report['failures'].append(dict(stage='setup-or-execution',error=str(error)))
    finally:
        try:
            need(protected=={p:identity(Path(p).read_bytes()) for p in protected},'protected input changed')
            need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'protected source changed')
        except (ValueError,OSError) as error:report['failures'].append(dict(stage='immutability',error=str(error)))
        if not report['failures'] and report['actual_new_processes']==1 and len(report['results'])==1:report['status']=STATUS
        (out/'result.json').write_bytes(stable(report));members={p.name:identity(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
        (out/'receipt.json').write_bytes(stable(dict(schema_version=1,status=report['status'],tested_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),candidate=report['candidate'],members=members,native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)))
    return report

if __name__=='__main__':
    report=run();print(json.dumps({k:report[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures')}));sys.exit(0 if report['status']==STATUS else 1)
