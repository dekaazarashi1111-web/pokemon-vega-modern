#!/usr/bin/env python3
"""Thumb修復後の未完Circus初戦1ケースだけを実行する。旧controllerはhelperとしてのみ再利用。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_circus_native.py'
SOURCE='tools/mgba_pr16_circus_native.c'
TEST='tests/test_pr16_circus_native.py'
WORKFLOW='.github/workflows/pr16-circus-native.yml'
OUT=ROOT/'.local/pr16-circus-native'
SHA='99cc09484a9c6bd787fb4b0631970396b4ae5ec2abc902ea8fdec932130b6c0b'
CASES=('circus-cancel-save-continue','factory-fallback-cancel','circus-first-battle')
RUN_CASES=(CASES[2],)
TRACE=('gateway','rentals','cancel','field','saved','reloaded','selected','second','confirm','draw','action','turn')


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()


def strict(raw):
    def pairs(items):
        result={}
        for k,v in items:
            need(k not in result,'duplicate native result key');result[k]=v
        return result
    def bad(v):raise ValueError('nonfinite native JSON: '+v)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)


def validate(raw,stderr,code,case):
    need(case in CASES and type(code) is int and code==0,'native Circus process failed')
    r=strict(raw);factory=case==CASES[1];battle=case==CASES[2];saved=not factory and not battle
    want=dict(schema_version=1,status='PASS_CIRCUS_SCOPED_NATIVE',case=case,candidate_sha256=SHA,
        new_circus_question=True,factory_fallback=factory,rental_entry=not factory,battle_started=battle,cancelled=not battle,
        party_bytes_verified=600,save_counter_before=2,save_counter_after=3 if saved else 2,
        manual_saves=1 if saved else 0,fresh_cores=2 if saved else 1,host_write_barriers=7,
        input_only_after_guard=True,initial_fixture_is_not_admission=True,bp_earned=0,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,warnings_errors=0)
    dynamic={'effect_flags','total_frames','witness'}
    need(type(r) is dict and set(r)==set(want)|dynamic,'native Circus schema differs')
    for key,value in want.items():need(type(r[key]) is type(value) and r[key]==value,'native Circus contract differs: '+key)
    need(type(r['total_frames']) is int and 0<r['total_frames']<=120000,'native frame bound')
    flags=r['effect_flags'];need(type(flags) is int and 0<=flags<=0xffffffff,'effect flag type/range')
    need((flags>0 and not flags&(flags-1) and not flags&0xfff00000) if battle else flags==0,'effect draw scope differs')
    w=r['witness'];need(type(w) is dict and set(w)==set(TRACE),'native witness schema differs')
    need(all(type(v) is int and 0<=v<=r['total_frames'] for v in w.values()),'witness type/range')
    seq=('gateway','cancel','field') if factory else (('gateway','rentals','selected','second','confirm','draw','action','turn') if battle else ('gateway','rentals','cancel','field','saved','reloaded'))
    need(w[seq[0]]>0 and w[seq[-1]]==r['total_frames'],'native lifecycle endpoints differ')
    for a,b in zip(seq,seq[1:]):need(w[a]<=w[b] if (a,b) in (('confirm','draw'),('draw','action')) else w[a]<w[b],'native lifecycle order differs')
    need(all(w[k]==0 for k in set(TRACE)-set(seq)),'unrequested native stage reported')
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'mGBA warned')
    for label in ('fixture','circus-question',*(['circus-action'] if battle else ['returned'])):
        need(('CIRCUS label='+label+' ').encode() in stderr,'native original trace absent')
    return r


def requested_cases():
    need(RUN_CASES==(CASES[2],),'accepted prefix must not be replayed')
    return RUN_CASES


def run():
    cases=requested_cases()
    sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
    import pr16_purchased_gear as gear
    import pr16_bp_chooser_native as previous
    import pr16_circus_entry as entry
    parent,shop,r,common=gear.parent,gear.shop,gear.r,gear.common
    m=shop.base.load();out=gear.evidence.prepare_output(ROOT,OUT)
    report=dict(schema_version=1,status='FAIL',scope='THUMB_REPAIRED_CIRCUS_FIRST_BATTLE_ONLY',source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        candidate=dict(size=33554432,sha256=SHA),requested_cases=list(cases),actual_new_processes=0,successful_fresh_cores=0,
        results=[],failures=[],guard_checks=[],accepted_native_cases_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    protected={};bindings={}
    try:
        recipe=strict((entry.OUT/'report.json').read_bytes());need(recipe['candidate']==report['candidate'],'built native candidate differs')
        saved=strict((ROOT/'content/modernization/pr16_circus_thumb_checkpoint.json').read_bytes())
        from pr16_circus_thumb_record import validate_build
        validate_build(recipe,saved['proof'])
        for name in ('scripts/pr16_circus_entry.py','scripts/pr16_circus_thumb.py'):
            need(identity((ROOT/name).read_bytes())==saved['source_bindings'][name],'repaired adapter source changed')
        need(recipe['candidate']==saved['build']['candidate'] and recipe['payload']==saved['build']['payload'],'saved build identity differs')
        need(identity((ROOT/previous.control.SOURCE).read_bytes())['sha256']==previous.C_SOURCE_SHA,'historical helper changed')
        candidate=entry.OUT/'candidate.gba';seed=ROOT/m.SEED
        raw=r.layer.source.checked(candidate,SHA);r.layer.source.checked(seed,m.SEED_SHA)
        original=(parent.repair.OUTPUT/'candidate.gba').read_bytes();geometry=gear.oracle(original)
        report['build_recipe']=recipe
        report['chooser_bindings']=previous.chooser.prepare(raw,out,identity,need,stable)
        paths={SELF,SOURCE,TEST,WORKFLOW,previous.control.SOURCE,'tools/mgba_pr16_bp_selection_native.c','tools/mgba_pr16_bp_battle_progress.c',
            shop.base.PARENT_C,shop.SOURCE,parent.SOURCE,gear.SOURCE,*[p for p,_ in m.EMBEDDED],
            'config/modernization_stage79_cumulative_mgba.json','config/active_play_baseline.json','design/active_play_baseline.md',
            'overlays/factory_high_modes_v2/factory_high_modes_v2.h','overlays/save_migration/save_migration.h'}
        cfg=json.loads((ROOT/'config/modernization_stage79_cumulative_mgba.json').read_bytes());p02=next(d for d in cfg['domains'] if d['id']=='p02')
        for bound in (p02['runner'],*p02['dependencies']):
            need(common.identity(ROOT/bound['path'])=={k:bound[k] for k in ('size','sha256')},'fixed helper dependency differs');paths.add(bound['path'])
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                p=Path(name).resolve()
                if p.is_relative_to(ROOT) and p.suffix=='.py':paths.add(p.relative_to(ROOT).as_posix())
        bindings={n:identity((ROOT/n).read_bytes()) for n in sorted(paths)};report['sources']=bindings
        protected={str(p):identity(p.read_bytes()) for p in (seed,candidate,parent.repair.OUTPUT/'candidate.gba')}
        with tempfile.TemporaryDirectory(prefix='pr16-circus-native-',dir=ROOT/'.local') as temporary:
            work=Path(temporary);generated={};transforms=[]
            for i,(src,target) in enumerate(m.EMBEDDED):generated[target]=m.embed((ROOT/src).read_text(),'circus_base_'+str(i))
            for src,target,label in ((shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','circus_breeding'),
                (shop.SOURCE,'pr16_capture_shop_helpers.c','circus_shop'),(parent.SOURCE,'pr16_gear_capture_helpers.c','circus_capture'),
                (gear.SOURCE,'pr16_bp_native_helpers.c','circus_gear')):
                text=(ROOT/src).read_text()
                if src==parent.SOURCE:
                    before=f'#define N_SHA "{previous.layer.parent_layer.route.SHA}"';after=f'#define N_SHA "{SHA}"'
                    text=previous.transform(text,before,after);transforms.append(dict(source=src,before=before,after=after))
                generated[target]=m.embed(text,label)
            controller=(ROOT/previous.control.SOURCE).read_text()
            controller,observation=previous.chooser.instrument(controller,previous.transform);transforms.extend(observation)
            before='script=%08x';after='context_header_raw=%08x';controller=previous.transform(controller,before,after)
            transforms.append(dict(source=previous.control.SOURCE,before=before,after=after,scope='READ_ONLY_LABEL_CORRECTION'))
            generated['pr16_bp_control_embedded.c']=m.embed(controller,'circus_historical_control')
            generated['pr16_circus_selection_helpers.c']=m.embed((ROOT/'tools/mgba_pr16_bp_selection_native.c').read_text(),'circus_historical_selection')
            generated['pr16_circus_turn_helpers.c']=(ROOT/'tools/mgba_pr16_bp_battle_progress.c').read_text()
            generated['pr16_gear_route.h']=gear.route_header(geometry)
            addresses=dict(CF_BRIDGE=recipe['entries']['bridge'],CF_SCRIPT=recipe['entries']['circus'],CF_LAUNCH=recipe['launch_sites'][0]['new'])
            generated['pr16_circus_addresses.h']=''.join('#define '+k+' '+hex(v)+'U\n' for k,v in addresses.items())
            generated['controller.c']=(ROOT/SOURCE).read_text()
            for name,text in generated.items():
                (work/name).write_text(text);dst=out/'generated'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(text)
            report['generated']={n:identity(t.encode()) for n,t in generated.items()};report['transformations']=transforms
            binary=work/'runner'
            _,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(work/'controller.c'),'-lmgba','-o',str(binary)],out/'compile',120)
            need(common.require_exited(process)==0,'Circus native controller compile failed');report['executable']=identity(binary.read_bytes())
            for guard in previous.fixed.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],out/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);report['guard_checks'].append(guard)
            for case in cases:
                scratch=work/(case+'.srm');shutil.copyfile(seed,scratch);report['actual_new_processes']+=1
                stdout,stderr,process=common.capture([str(binary),str(candidate),str(scratch),SHA,m.SEED_SHA,case,str(out/case)],out/case,900)
                row=validate(stdout,stderr,common.require_exited(process),case)
                screens={p.name:identity(gear.evidence.read_ppm(p)) for p in sorted(out.glob(case+'-*.ppm'))}
                need(len(screens)>=4,'bounded Circus screenshots absent')
                report['results'].append(dict(case=case,result=row,process=process,screens=screens,visual_review_completed=False))
                report['successful_fresh_cores']+=row['fresh_cores']
    except (ValueError,RuntimeError,KeyError,TypeError,OSError) as error:report['failures'].append(dict(stage='setup-or-execution',error=str(error)))
    finally:
        try:
            need(protected=={p:identity(Path(p).read_bytes()) for p in protected},'protected native input changed')
            need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'protected source changed')
        except (ValueError,OSError) as error:report['failures'].append(dict(stage='immutability',error=str(error)))
        if not report['failures'] and report['actual_new_processes']==len(cases) and len(report['results'])==len(cases):report['status']='PASS_CIRCUS_SCOPED_NATIVE'
        (out/'report.json').write_bytes(stable(report))
    return report


if __name__=='__main__':
    report=run();print(json.dumps({k:report[k] for k in ('status','actual_new_processes','successful_fresh_cores','failures')},ensure_ascii=False))
    sys.exit(0 if report['status']=='PASS_CIRCUS_SCOPED_NATIVE' else 1)
