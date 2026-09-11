#!/usr/bin/env python3
"""Retain run 34589284710 and rebuild scoped acceptance; never start an emulator."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_purchased_gear as native
import pr16_purchased_gear_evidence as screens
import pr16_shop_display_checkpoint as display
prior=display.prior;need=prior.need;load=prior.load;stable=prior.stable;identity=prior.identity
RECORD=(34589284710,10194976718,580351,'6eba3f6c0947af2e2cb446552cc37ccf832665a8ac849a80e2f45bca986e6de9','4b5971179795bcdbbca1abf142387ef1bb6f1ce9','pr16-purchased-gear','pr16-purchased-gear','pr16-purchased-gear-evidence/')
DIRECTORY=Path('content/modernization/pr16_gear_evidence')/str(RECORD[0])
RECEIPT='content/modernization/pr16_gear_screen_acceptance.json'
RECIPE_SHA='e9db6aca3b6610a134074087e68339d9a78f273cd92f836f50b69badd7262b75'
# Reviewed all 58 originals in four contact sheets on 2026-09-11.
IMAGES_SHA='d594115c87f2ec3c7a05692a769cb36f3ef586d5e8f7ac065cef7f6328947934'


def install(root,path,data):
    target=root/path;need(not any(p.is_symlink() for p in (target,*target.parents)),'unsafe retained evidence destination')
    if target.exists():need(target.read_bytes()==data,'refuse retained original overwrite')
    else:
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(data)


def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+prior.REPO+'/'+path],timeout=120)
    run,aid,size,sha,head,_,_,_=RECORD
    r=load(api(f'actions/runs/{run}'));a=load(api(f'actions/artifacts/{aid}'));jobs=load(api(f'actions/runs/{run}/jobs?per_page=100'))
    prior.fields(a['workflow_run'],dict(id=run,head_sha=head))
    need(a['digest']=='sha256:'+sha and jobs['total_count']==len(jobs['jobs']),'gear origin digest/job pagination differs')
    meta={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
    meta.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
    prior.metadata(meta,RECORD);raw=api(f'actions/artifacts/{aid}/zip')
    need(identity(raw)==dict(size=size,sha256=sha),'gear ZIP differs from pinned Actions digest');display.archive(raw)
    install(root,DIRECTORY/'original.zip',raw);install(root,DIRECTORY/'actions.json',stable(meta))


def verify(files,root=ROOT):
    p='pr16-purchased-gear/';ev=RECORD[7]
    need(files[ev+'tested-head.txt']==(RECORD[4]+'\n').encode(),'tested HEAD differs')
    report=load(files[p+'result.json']);audit=load(files[p+'oracle.json'])
    prior.fields(report,dict(schema_version=2,status='PASS',scope=native.SCOPE,candidate=display.CANDIDATE,actual_new_processes=4,successful_fresh_cores=9,failures=[],guard_checks=prior.GUARDS,purchased_gear_to_battle_accepted=True,initial_map_party_ring_bp_policy_are_fixtures=True,ring_bp_natural_acquisition_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0))
    need(prior.same(report['oracle'],audit) and audit['candidate']==display.CANDIDATE,'natural oracle differs')
    need(identity(files[p+'candidate.json'])['sha256']==RECIPE_SHA,'candidate recipe differs')
    need(files[ev+'unit.log'].endswith(b'OK\n') and b'Ran 65 tests' in files[ev+'unit.log'],'targeted tests did not pass')
    snapshot=display.sources(files,ev,report,root,(native.SELF,native.SOURCE,native.TEST,native.WORKFLOW,screens.SELF,screens.TEST))
    need(len(snapshot)==37 and prior.same(load(files[ev+'source-bindings.json']),{k:identity(v) for k,v in snapshot.items()}),'source snapshot differs')
    m=native.shop.base.load();generated={}
    for i,(src,target) in enumerate(m.EMBEDDED):generated[target]=m.embed(snapshot[src].decode(),'gear_embedded_'+str(i)).encode()
    for src,target,label in ((native.shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','gear_breeding'),(native.shop.SOURCE,'pr16_capture_shop_helpers.c','gear_shop'),(native.parent.SOURCE,'pr16_gear_capture_helpers.c','gear_capture')):
        generated[target]=m.embed(snapshot[src].decode(),label).encode()
    generated['pr16_gear_route.h']=native.route_header(audit).encode()
    need(display.archive(files[p+'generated-controller.zip'])==generated|{'controller.c':snapshot[native.SOURCE]},'compiled controller differs')
    need(prior.same(report['generated'],{k:identity(v) for k,v in generated.items()}),'generated source bindings differ')
    prior.guards(files,p);need(native.common.require_exited(load(files[p+'compile.process.json']))==0,'compile failed')
    rows=[];bound={};need(len(report['results'])==4,'native case count differs')
    with tempfile.TemporaryDirectory(prefix='gear-screen-check-') as td:
        output=Path(td)
        for name in native.CASES:
            loc=p+name;process=load(files[loc+'.process.json'])
            value=native.validate(files[loc+'.stdout'],files[loc+'.stderr'],name,native.common.require_exited(process),audit)
            row=dict(name=name,result=value,process=process);need(prior.same(report['results'][len(rows)],row),'raw/report result differs');rows.append(row)
            for suffix in screens.required_screens(value):
                filename=name+'-'+suffix+'.ppm';(output/filename).write_bytes(files[p+filename])
            binding=screens.bind_screens(output,name,value)
            need(prior.same(binding,load(files[loc+'.screens.json'])),'screen sidecar differs');bound[name]=binding
    images={k.removeprefix(p):identity(v) for k,v in files.items() if k.endswith('.ppm')}
    need(len(images)==58 and identity(stable(images))['sha256']==IMAGES_SHA,'visually reviewed pixels differ')
    return dict(native_results=rows,screen_bindings=bound,reviewed_images=images,source_files=37,targeted_tests=65,
                actual_native_processes=4,actual_fresh_cores=9,mandatory_bound_screens=53,
                visual_review=dict(completed=True,images=58,images_sha256=IMAGES_SHA,scope='58 original shop/bag/give/walk/battle/return/reload frames; no apparent UI corruption',limitation='Static frames only, not a full animation review; mega-active is sampled before sprite refresh'),
                purchased_gear_to_battle_accepted=True,initial_map_party_ring_bp_policy_are_fixtures=True,
                ring_bp_natural_acquisition_accepted=False,ordinary_policy_selection_accepted=False,all_six_gear_routes_accepted=False,full_p05_acceptance=False,release_ready=False)


def build(root=ROOT):
    run,aid,size,sha,head,_,_,_=RECORD
    prior.metadata(load(prior.read(root,DIRECTORY/'actions.json')),RECORD)
    raw=prior.read(root,DIRECTORY/'original.zip');need(identity(raw)==dict(size=size,sha256=sha),'retained ZIP changed')
    return dict(schema_version=1,status='SCOPED_GEAR_SCREEN_ACCEPTED_PRODUCT_INCOMPLETE',candidate=display.CANDIDATE,
                original=dict(run_id=run,artifact_id=aid,tested_head=head,path=str(DIRECTORY/'original.zip'),size=size,sha256=sha),
                acceptance=verify(display.archive(raw),root),separate_prior_native_run=34587080329,
                prior_runs_added_to_current_count=False,new_emulator_runs_by_this_verifier=0,full_p05_acceptance=False,release_ready=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true');parser.add_argument('--write',action='store_true');args=parser.parse_args()
    if args.fetch:fetch()
    value=build()
    if args.write:install(ROOT,Path(RECEIPT),stable(value))
    else:need(prior.same(value,load(prior.read(ROOT,RECEIPT))),'saved scoped receipt differs')
    print(stable(dict(status=value['status'],run=RECORD[0],targeted_tests=65,native_processes=4,fresh_cores=9,reviewed_images=58,release_ready=False)).decode(),end='')
if __name__=='__main__':main()
