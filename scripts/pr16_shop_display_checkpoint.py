#!/usr/bin/env python3
"""Retain rejected hypotheses and scoped repaired UI without promoting P05.

Original ZIPs are immutable. This rebuilds acceptance from exact successful
Actions provenance, raw process records, generated controllers and reviewed
images. No emulator is run by this receipt generator.
"""
from copy import deepcopy
import argparse
import io
from pathlib import Path
import struct
import subprocess
import sys
import zipfile
import zlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_completion_checkpoint as prior
import pr16_shop_display_native as native
need=prior.need;load=prior.load;identity=prior.identity;stable=prior.stable
SELF='scripts/pr16_shop_display_checkpoint.py'
RECEIPT='content/modernization/pr16_shop_display_acceptance.json'
DIRECTORY='content/modernization/pr16_shop_display_evidence'
RECORDS={
 'repaired':(34571394609,10187955840,1049695,'853db3d73ba2c89016787720f95a55150b41de009b0ca44ca3998472e225c45d','d33ce3a774f695cee0723e999c485818bec0ea4a','pr16-shop-display-repair','pr16-shop-display-repair','pr16-shop-display-repair-evidence/'),
 'top1':(34569993409,10187444217,296690,'cd82f52151604c997e6ed458c63c3fe65d8bc6992e955eeba192ec334b4f2b8d','203d2d64ac143c66e62e1c2430d685306d4feea6','pr16-shop-display-probe','pr16-shop-display-probe','pr16-shop-display-evidence/'),
}
CANDIDATE={'size':33554432,'sha256':'e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267'}
PATCHES=('parent-to-shop-display-repaired.bps','shop-display-repaired-to-parent.bps')
REVIEW='content/modernization/pr16_shop_display_visual_review.json'
REVIEW_SHA='38562425c105b5c5bdb3aa20159de80b42ddecf917f65df724e9074b50735dd3'


def archive(raw,depth=0,budget=None):
    need(depth<=2,'display evidence nesting exceeds two')
    if budget is None:budget=[64*1024*1024]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist();names=[e.filename for e in entries]
        need(len(entries)<2000 and len(names)==len(set(names)),'display evidence member count/duplicates')
        budget[0]-=sum(e.file_size for e in entries);need(budget[0]>=0,'display evidence expansion limit')
        result={}
        for e in entries:
            p=Path(e.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in e.filename and not e.is_dir(),'unsafe display ZIP path')
            need(((e.external_attr>>16)&0o170000)!=0o120000,'display evidence symlink')
            need(p.suffix.lower() not in ('.gba','.gb','.sav','.srm','.ss0','.state','.bin','.elf','.so'),'ROM/save/binary in display evidence')
            value=z.read(e);result[e.filename]=value
            if p.suffix.lower()=='.zip':archive(value,depth+1,budget)
            elif p.suffix.lower()=='.ppm':need(value.startswith(b'P6\n240 160\n255\n') and len(value)==115215,'invalid original screenshot')
            elif p.suffix.lower()=='.bps':
                need(p.name in PATCHES and 16<=len(value)<1048576 and value[:4]==b'BPS1','unexpected intermediate patch')
                need(zlib.crc32(value[:-4])&0xffffffff==struct.unpack_from('<I',value,len(value)-4)[0],'intermediate patch CRC differs')
            else:value.decode('utf8');need(b'\0' not in value,'binary disguised as source/log')
        return result


def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+prior.REPO+'/'+path])
    def install(path,raw):
        target=root/path;need(not any(p.is_symlink() for p in (target,*target.parents)),'unsafe display destination')
        if target.exists():need(target.read_bytes()==raw,'refuse display original overwrite')
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    for record in RECORDS.values():
        run,aid,size,sha,head,_,_,_=record
        r=load(api(f'actions/runs/{run}'));a=load(api(f'actions/artifacts/{aid}'));jobs=load(api(f'actions/runs/{run}/jobs?per_page=100'))
        prior.fields(a['workflow_run'],dict(id=run,head_sha=head))
        need(a['digest']=='sha256:'+sha and jobs['total_count']==len(jobs['jobs']),'incomplete/changed display Actions origin')
        meta={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
        meta.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
        prior.metadata(meta,record);raw=api(f'actions/artifacts/{aid}/zip');need(identity(raw)==dict(size=size,sha256=sha),'display original download differs');archive(raw)
        directory=Path(DIRECTORY)/str(run);install(directory/'original.zip',raw);install(directory/'actions.json',stable(meta))


def sources(files,prefix,report,root,required):
    snapshot=archive(files[prefix+'sources.zip'])
    for name,binding in report['sources'].items():
        need(prior.same(identity(snapshot[name]),binding),'display source snapshot hash differs')
        if not name.startswith('vendor/'):
            need(snapshot[name]==prior.read(root,name),'tested display dependency changed: '+name)
    for name in required:need(snapshot[name]==prior.read(root,name),'display workflow/adapter source differs: '+name)
    return snapshot


def guard_records(files,prefix):
    validator=native.shop.base.load()
    for name in prior.GUARDS:
        p=prefix+'guard-'+name
        validator.validate_guard(files[p+'.stdout'],files[p+'.stderr'],load(files[p+'.process.json']))


def verify_top1(files,root=ROOT):
    ev=RECORDS['top1'][7];p='pr16-shop-display-probe/'
    need(files[ev+'tested-head.txt']==(RECORDS['top1'][4]+'\n').encode(),'top-only probe HEAD differs')
    report=load(files[p+'result.json']);recipe=load(files[p+'recipe.json'])
    prior.fields(report,dict(status='DATA_PASS_VISUAL_REVIEW_REQUIRED',scope=native.probe.SCOPE,new_native_processes=6,new_native_cores=12,visual_accepted=False,final_candidate_changed=False,release_ready=False))
    prior.fields(recipe,dict(status='EXPERIMENTAL_NOT_ADOPTED',parent=prior.CANDIDATE,candidate=dict(size=33554432,sha256='070998bc6b0b5e2fd7fe07eb14cc99513c067e6a3013bd6a597300e99b25ea4a')))
    need(prior.same(report['recipe'],recipe) and len(report['results'])==6,'top-only recipe/count differs')
    rows=[]
    for variant in ('control','top1'):
        sha=prior.CANDIDATE['sha256'] if variant=='control' else recipe['candidate']['sha256']
        need(files[p+variant+'-controller.c']==native.probe.controller(sha).encode(),'top-only actual C differs')
        for name in native.CONTROLS:
            base=p+variant+'-'+name;process=load(files[base+'.process.json'])
            value=native.probe.validate(files[base+'.stdout'],name,native.shop.common.require_exited(process),sha)
            row=report['results'][len(rows)];need(prior.same(row,dict(variant=variant,case=name,result=value,process=process)),'top-only raw result differs')
            need(b'mGBA[' not in files[base+'.stderr'],'top-only warning/error');rows.append(row)
        guard_records(files,p+variant+'-')
    sources(files,ev,report,root,(native.probe.SELF,))
    return dict(status='DATA_PASS_VISUAL_REJECTED',new_processes=6,new_cores=12,adopted=False,conclusion='TOP_COORDINATE_ONLY_DID_NOT_FIX_WORLD_TILEMAP_OR_FRAME_OVERLAP')


def verify_repaired(files,root=ROOT):
    ev=RECORDS['repaired'][7];p='pr16-shop-display-native/'
    need(files[ev+'tested-head.txt']==(RECORDS['repaired'][4]+'\n').encode(),'safe renderer execution HEAD differs')
    report=load(files[p+'result.json']);recipe=load(files[p+'recipe.json'])
    prior.fields(report,dict(schema_version=1,status='DATA_AND_VRAM_PASS_VISUAL_REVIEW_REQUIRED',scope=native.SCOPE,candidate=CANDIDATE,parent=prior.CANDIDATE,failures=[],actual_new_processes=14,repaired_processes=11,repaired_cores=22,control_processes=3,control_cores=6,old_runs_relabelled=0,all_nine_catalogue_pages_observed=True,visual_review_complete=False,natural_capture_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False))
    need(prior.same(report['recipe'],recipe) and prior.same(load(files[ev+'candidate.json']),recipe),'safe renderer recipe copies differ')
    prior.fields(recipe,dict(parent=prior.CANDIDATE,candidate=CANDIDATE,independent_repair_builds=2,full_clean_rebuild_claimed=False,save_layout_changes=0,table_changes=0,economy_changes=0,active_baseline_changed=False,native_accepted=False,release_ready=False))
    need(prior.same(recipe['graphics_contract'],native.repair.validate_geometry(recipe['geometry'])),'safe renderer graphics contract differs')
    need(prior.same(recipe['source_changes'],[dict(before=a,after=b) for a,b in native.repair.CHANGES]),'safe renderer source delta differs')
    snapshot=sources(files,ev,report,root,(native.SELF,native.repair.SELF,native.TEST,native.WORKFLOW))
    need(prior.same(load(files[ev+'source-bindings.json']),{k:identity(v) for k,v in snapshot.items()}),'safe renderer source archive inventory differs')
    overlay=snapshot[native.probe.OVERLAY].decode()
    for before,after in native.repair.CHANGES:need(overlay.count(before)==1,'overlay preimage differs');overlay=overlay.replace(before,after,1)
    need(overlay.encode()==files[p+'renderer.c'] and identity(overlay.encode())==recipe['renderer_source'],'compiled repair overlay differs')
    for name,binding in recipe['source_bindings'].items():need(snapshot[name]==prior.read(root,name) and identity(snapshot[name])==binding,'repair builder source binding differs')
    for name,binding in recipe['patches'].items():need(name in PATCHES and identity(files[ev+name])==binding,'intermediate patch identity differs')
    need(set(recipe['patches'])==set(PATCHES),'forward/reverse patch missing')
    need(b'Ran 21 tests' in files[ev+'unit.log'] and files[ev+'unit.log'].endswith(b'OK\n'),'safe renderer contract tests did not complete')
    need(len(report['results'])==14,'safe renderer native count differs');rows=[]
    for variant in ('control','repaired'):
        control=variant=='control';sha=prior.CANDIDATE['sha256'] if control else CANDIDATE['sha256']
        need(files[p+variant+'-controller.c']==native.controller(sha,control).encode(),'executed graphics observer C differs')
        for name in (native.CONTROLS if control else native.CASES):
            base=p+variant+'-'+name;process=load(files[base+'.process.json']);value=native.validate(files[base+'.stdout'],name,native.shop.common.require_exited(process),sha,control)
            row=report['results'][len(rows)];need(prior.same(row,dict(variant=variant,case=name,result=value,process=process)),'graphics raw result differs')
            need(b'mGBA[' not in files[base+'.stderr'],'graphics emulator warning/error');rows.append(row)
        guard_records(files,p+variant+'-')
    return dict(status='SCOPED_SHOP_DATA_GRAPHICS_SAVE_ACCEPTED',candidate=CANDIDATE,repaired_processes=11,repaired_cores=22,original_corruption_controls=3,original_control_cores=6,all_nine_pages=True,
                repaired_world_difference_bytes=sum(row['result']['graphics']['world_difference_bytes'] for row in rows if row['variant']=='repaired'),
                cases=[row['result'] for row in rows if row['variant']=='repaired'],
                controls=[row['result']['graphics'] for row in rows if row['variant']=='control'],
                fixture_boundary='MAP_RING_BP_AND_CLEARED_CLAIMS_BEFORE_PHYSICAL_OBSERVATION',
                independent_repair_builds=2,full_clean_rebuild_claimed=False,patches=recipe['patches'],
                natural_capture_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False)


def build(root=ROOT):
    sets={};originals={};acceptance={}
    need(set(RECORDS)=={'top1','repaired'} and CANDIDATE is not None,'display acceptance not configured')
    for label,record in RECORDS.items():
        run,aid,size,sha,head,_,_,_=record;directory=Path(DIRECTORY)/str(run)
        prior.metadata(load(prior.read(root,directory/'actions.json')),record)
        raw=prior.read(root,directory/'original.zip');need(identity(raw)==dict(size=size,sha256=sha),'retained display original differs')
        sets[label]=archive(raw);originals[label]=dict(run_id=run,artifact_id=aid,tested_head=head,path=str(directory/'original.zip'),size=size,sha256=sha)
        acceptance[label]=(verify_top1 if label=='top1' else verify_repaired)(sets[label],root)
    review_raw=prior.read(root,REVIEW);need(identity(review_raw)['sha256']==REVIEW_SHA,'review record changed')
    reviewed=load(review_raw);need(set(reviewed)=={'top1','repaired'},'visual review missing')
    need(reviewed['top1']['status']=='REJECTED' and reviewed['repaired']['status']=='PASS','review scope differs')
    images={}
    for label,review in reviewed.items():
        members=review['images']
        need(members,'empty visual review')
        images[label]={}
        for name,sha in members.items():
            need(identity(sets[label][name])==dict(size=115215,sha256=sha),'reviewed raw pixels differ')
            images[label][name]=dict(size=115215,sha256=sha)
    return dict(schema_version=1,status='SCOPED_SHOP_REPAIR_ACCEPTED_FINAL_INTEGRATION_PENDING',historical_parent=prior.CANDIDATE,scoped_candidate=CANDIDATE,originals=originals,acceptance=acceptance,
                visual_review=dict(top1='REJECTED',repaired='PASS',images=images),shop_visual_acceptance=True,
                prior_original_rejection_preserved=True,historical_successes_preserved_not_relabelled=True,new_emulator_runs=0,
                final_integration_accepted=False,full_p05_acceptance=False,release_ready=False)


def project(previous,root=ROOT):
    receipt=build(root);need(prior.same(receipt,load(prior.read(root,RECEIPT))),'saved shop display receipt differs')
    out=deepcopy(previous)
    out['shop_display_repair_checkpoint']=dict(source_path=RECEIPT,parent=prior.CANDIDATE,candidate=CANDIDATE,repaired_native_processes=11,repaired_native_cores=22,original_corruption_controls=3,shop_visual_acceptance=True,final_integration_accepted=False,release_ready=False)
    if 'p05_route_checkpoint' in out:
        out['p05_route_checkpoint'].update(historical_candidate=prior.CANDIDATE,shop_display_successor_receipt=RECEIPT)
    out['next_integration_candidate']=dict(source_path=RECEIPT,candidate=CANDIDATE,builder=native.repair.SELF,scope='SHOP_RENDERER_REPAIR_ACCEPTED_OTHER_DOMAINS_RETAINED_ON_PARENT',full_candidate_regression_complete=False)
    for row in out['remaining_conditions']:
        if row['id']=='NATURAL_CAPTURE_GEAR':
            row.update(reason_ja='6種の石の実受付購入・取消・拒否・保存とショップ表示は後継候補で11件22コア成功。自然捕獲および通常取得から戦闘への接続は未完了。旧候補の表示不合格原本は保持',partial_data_evidence=RECEIPT,display_repair_required=False,display_repaired_candidate=CANDIDATE['sha256'])
        if row['id']=='FINAL_NATIVE_ACCEPTANCE':
            row.update(shop_display_successor=RECEIPT,pass_condition='Connect remaining physical routes and relevant regression to the exact shop-display successor; parent successes remain historical, not rerun claims')
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true');parser.add_argument('--write',action='store_true');args=parser.parse_args()
    if args.fetch:fetch()
    value=build();path=ROOT/RECEIPT
    if args.write:path.write_bytes(stable(value))
    else:need(prior.same(value,load(path.read_bytes())),'saved shop display receipt differs')
    print(stable(dict(status=value['status'],scoped_candidate=CANDIDATE,accepted_shop_processes=11,accepted_shop_cores=22,new_emulator_runs=0,release_ready=False)).decode(),end='')
if __name__=='__main__':main()
