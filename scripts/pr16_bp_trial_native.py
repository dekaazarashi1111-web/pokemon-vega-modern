#!/usr/bin/env python3
"""New native rental-cancel lifecycle on the explicitly repaired Trial successor.

Reuse the original controller as a hash-pinned source template, not its results.
Only the ROM pin and evidence scope are transformed; all game input logic,
observation barriers, cancellation and fresh-core assertions remain unchanged.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_bp_trial_successor as layer
import pr16_bp_native_controls as control
import pr16_fixed_form_acceptance as fixed
need,identity,stable=layer.need,layer.identity,layer.stable
SELF='scripts/pr16_bp_trial_native.py'
WORKFLOW='.github/workflows/pr16-bp-trial-native.yml'
TEST='tests/test_pr16_bp_trial_successor.py'
OUT=ROOT/'.local/pr16-bp-trial-native'
CASE='rental-cancel-save-continue'
SCOPE='PR16_P05_TRIAL_SUCCESSOR_NATIVE_CONTROL'
C_SOURCE_SHA='44e28abe05a7dcad0d430b8c48b5046cbf89c246f7235158a2e5451b29bb0f56'
PY_SOURCE_SHA='4282aa8a78e50d33837578846e531a32a517ae4a872db2271cff329993f67d93'


def expected():
    row=control.expected(CASE)
    row.update(scope=SCOPE,candidate_sha256=layer.SHA)
    return row


def validate(raw:bytes,stderr:bytes,code:int)->dict:
    need(type(code) is int and code==0,'successor controller did not exit integer zero')
    row=fixed.strict_json(raw);want=expected()
    dynamic={'save_counter_before','save_counter_before_manual','save_counter_after','total_frames','witness'}
    need(type(row) is dict and set(row)==set(want)|dynamic,'successor result schema differs')
    for key,value in want.items():
        need(type(row[key]) is type(value) and row[key]==value,'successor result differs: '+key)
    for key in dynamic-{'witness'}:need(type(row[key]) is int and 0<=row[key]<=0xffffffff,'invalid successor integer')
    need(1<=row['total_frames']<=600000,'frame budget differs')
    need(row['save_counter_before']==row['save_counter_before_manual'],'cancellation performed full save')
    need(row['save_counter_after']==row['save_counter_before']+1,'normal Save accounting differs')
    witness=row['witness'];need(type(witness) is dict and set(witness)==set(control.TRACE),'witness schema differs')
    need(all(type(v) is int and 0<=v<=row['total_frames'] for v in witness.values()),'invalid witness type/range')
    need(witness[control.TRACE[0]]>0 and all(witness[a]<witness[b] for a,b in zip(control.TRACE,control.TRACE[1:])),'incomplete native lifecycle')
    need(witness[control.TRACE[-1]]==row['total_frames'],'terminal observation absent')
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'mGBA warnings/errors')
    need(b'BP_CTRL label=fixture ' in stderr and b'BP_CTRL label=returned ' in stderr,'controller trace absent')
    return row


def transform(text:str,before:str,after:str)->str:
    need(text.count(before)==1 and after not in text,'declared source template preimage differs')
    return text.replace(before,after,1)


def run():
    import pr16_purchased_gear as gear
    parent,shop,r,common=gear.parent,gear.shop,gear.r,gear.common
    m=shop.base.load();out=gear.evidence.prepare_output(ROOT,OUT)
    report=dict(schema_version=1,status='FAIL',scope=SCOPE,candidate=dict(size=33554432,sha256=layer.SHA),
        requested_cases=[CASE],results=[],failures=[],guard_checks=[],actual_new_processes=0,successful_fresh_cores=0,
        native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False,old_runs_relabelled=0)
    protected={};bindings={}
    try:
        need(identity((ROOT/control.SOURCE).read_bytes())['sha256']==C_SOURCE_SHA,'prior C controller changed')
        need(identity((ROOT/control.SELF).read_bytes())['sha256']==PY_SOURCE_SHA,'prior result contract changed')
        recipe=layer.run();candidate=layer.OUT/'candidate.gba';seed=ROOT/m.SEED
        raw=r.layer.source.checked(candidate,layer.SHA);r.layer.source.checked(seed,m.SEED_SHA)
        original=(parent.repair.OUTPUT/'candidate.gba').read_bytes()
        need(raw==layer.replace_edge(original,layer.OFFSET,layer.BEFORE,layer.AFTER),'non-declared successor bytes')
        # Only generated walking-helper constants use the unchanged parent map geometry.
        # This is not a relabelled native or map probe run on the successor.
        geometry=gear.oracle(original)
        report['unchanged_parent_map_oracle']=control.oracle(original)
        report['declared_successor_change']=recipe['change']
        (out/'candidate.json').write_bytes(stable(recipe))
        paths={SELF,WORKFLOW,TEST,layer.SELF,layer.route.SELF,control.SELF,control.SOURCE,
            shop.base.PARENT_C,shop.SOURCE,parent.SOURCE,gear.SOURCE,
            'overlays/factory_high_modes_v2/factory_high_modes_v2.h','overlays/factory_high_modes_v2/factory_high_modes_v2.c',
            'overlays/save_migration/save_migration.h','overlays/save_migration/save_migration.c',
            'overlays/facility_runtime/facility_runtime.c','scripts/build_facility_runtime.py',
            'config/factory_high_modes_v2.json','config/modernization_stage79_cumulative_mgba.json',
            'config/active_play_baseline.json','design/active_play_baseline.md',*(p for p,_ in m.EMBEDDED)}
        cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes())
        p02=next(d for d in cfg['domains'] if d['id']=='p02')
        for bound in (p02['runner'],*p02['dependencies']):
            need(common.identity(ROOT/bound['path'])=={k:bound[k] for k in ('size','sha256')},'embedded dependency differs')
            paths.add(bound['path'])
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).resolve()
                if path.is_relative_to(ROOT) and path.suffix=='.py':paths.add(path.relative_to(ROOT).as_posix())
        bindings={p:identity((ROOT/p).read_bytes()) for p in sorted(paths)}
        protected={str(p):identity(p.read_bytes()) for p in (seed,candidate,parent.repair.OUTPUT/'candidate.gba')}
        report['sources']=bindings
        with zipfile.ZipFile(out/'sources.zip','w',zipfile.ZIP_DEFLATED) as z:
            for p in sorted(paths):
                data=(ROOT/p).read_bytes();data.decode('utf-8');need(not (ROOT/p).is_symlink() and b'\0' not in data,'unsafe source');z.writestr(p,data)
        with tempfile.TemporaryDirectory(prefix='pr16-trial-native-',dir=ROOT/'.local') as temp:
            work=Path(temp);generated={};transforms=[]
            for i,(src,target) in enumerate(m.EMBEDDED):generated[target]=m.embed((ROOT/src).read_text(),'trial_embedded_'+str(i))
            for src,target,label in ((shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','trial_breeding'),
                (shop.SOURCE,'pr16_capture_shop_helpers.c','trial_shop'),(parent.SOURCE,'pr16_gear_capture_helpers.c','trial_capture'),
                (gear.SOURCE,'pr16_bp_native_helpers.c','trial_gear')):
                text=(ROOT/src).read_text()
                if src==parent.SOURCE:
                    before=f'#define N_SHA "{layer.route.SHA}"';after=f'#define N_SHA "{layer.SHA}"'
                    text=transform(text,before,after);transforms.append(dict(source=src,before=before,after=after))
                generated[target]=m.embed(text,label)
            before=f'#define BP_SCOPE "{control.SCOPE}"';after=f'#define BP_SCOPE "{SCOPE}"'
            generated['controller.c']=transform((ROOT/control.SOURCE).read_text(),before,after)
            transforms.append(dict(source=control.SOURCE,before=before,after=after))
            generated['pr16_gear_route.h']=gear.route_header(geometry)
            for name,text in generated.items():(work/name).write_text(text)
            report['source_transformations']=transforms
            report['generated']={name:identity(text.encode()) for name,text in generated.items()}
            with zipfile.ZipFile(out/'generated-controller.zip','w',zipfile.ZIP_DEFLATED) as z:
                for name,text in generated.items():z.writestr(name,text)
            binary=work/'runner'
            _,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(work/'controller.c'),'-lmgba','-o',str(binary)],out/'compile',120)
            need(common.require_exited(process)==0,'successor controller compile failed');report['executable']=identity(binary.read_bytes())
            for guard in fixed.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);report['guard_checks'].append(guard)
            scratch=work/(CASE+'.srm');shutil.copyfile(seed,scratch);report['actual_new_processes']+=1
            stdout,stderr,process=common.capture([str(binary),str(candidate),str(scratch),layer.SHA,m.SEED_SHA,CASE,str(out/CASE)],out/CASE,900)
            row=validate(stdout,stderr,common.require_exited(process))
            screens={}
            for suffix in ('fixture','reception-tier','reception-mode','reception-confirm','rental-party','returned','fresh-continue'):
                p=out/(CASE+'-'+suffix+'.ppm');screens[p.name]=identity(gear.evidence.read_ppm(p))
            report['results'].append(dict(name=CASE,result=row,process=process,screens=screens,visual_review_completed=False))
            report['successful_fresh_cores']=row['fresh_cores']
    except (ValueError,RuntimeError,KeyError,TypeError,OSError) as error:
        report['failures'].append(dict(stage='setup-or-execution',error=str(error)))
    finally:
        try:
            need(protected=={p:identity(Path(p).read_bytes()) for p in protected},'protected input changed')
            need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'protected source changed')
        except (ValueError,OSError) as error:report['failures'].append(dict(stage='immutability',error=str(error)))
        if not report['failures'] and report['actual_new_processes']==1 and len(report['results'])==1 and report['guard_checks']==list(fixed.GUARDS):
            report['status']='PASS_TRIAL_SUCCESSOR_RENTAL_CANCEL_PENDING_EARNING'
        (out/'result.json').write_bytes(stable(report))
        members={p.name:identity(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()}
        receipt=dict(schema_version=1,status=report['status'],tested_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            candidate=report['candidate'],members=members,native_bp_earning_accepted=False,p05_native_bp_gap_closed=False,release_ready=False)
        (out/'receipt.json').write_bytes(stable(receipt))
    return report

if __name__=='__main__':
    result=run();print(json.dumps({k:result[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures')}))
    sys.exit(0 if result['status'].startswith('PASS_') else 1)
