#!/usr/bin/env python3
"""Retain actual P05 route originals without hiding the visual rejection.

The first shop run passes data/persistence checks, but screenshots show damaged
backgrounds after menu closure. It is NOT a completed shop/UI/P05 acceptance.
"""
from copy import deepcopy
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_completion_checkpoint as prior
import pr16_shop_routes as shop
need=prior.need
SELF='scripts/pr16_p05_route_checkpoint.py'
DIRECTORY='content/modernization/pr16_p05_route_evidence'
RECEIPT='content/modernization/pr16_p05_route_acceptance.json'
RECORDS={
 'roots':(34567225043,10186464456,7506357,'059ab4dee4ce06dce0456984f64cc11da1bbe60053ec17ae88c133d54e715b2e','ca9a0489bbd2bd68d84b9f208f42bb9b83025308','pr16-p05-root-continuation','pr16-p05-root-continuation',''),
 'shop':(34568373963,10186871315,428590,'b99594606925f7d5e0b1ea41e54650e8ac8224ac153420a60d3053f0c912e684','cd0f07c9c190b9e5a84f36ef3addd9e18259e3c7','pr16-shop-routes','pr16-shop-routes-acceptance','pr16-shop-evidence/')}


def archive(raw,depth=0,budget=None):
    # The exact roots source snapshot expands to 33,128,534 bytes. A separate
    # bounded reader preserves that original; historical 30 MB guards stay intact.
    need(depth<=2,'P05 archive nesting exceeds two')
    if budget is None:budget=[64*1024*1024]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist();need(len(entries)<2000,'too many P05 ZIP members')
        names=[e.filename for e in entries];need(len(names)==len(set(names)),'duplicate P05 ZIP member')
        budget[0]-=sum(e.file_size for e in entries);need(budget[0]>=0,'P05 archive expansion budget exceeded')
        result={}
        for e in entries:
            p=Path(e.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in e.filename and not e.is_dir(),'unsafe P05 ZIP path')
            need(((e.external_attr>>16)&0o170000)!=0o120000,'P05 symlink member')
            need(p.suffix.lower() not in ('.gba','.gb','.sav','.srm','.ss0','.state','.bin','.elf','.so'),'ROM/save/binary in P05 evidence')
            value=z.read(e);result[e.filename]=value
            if p.suffix.lower()=='.zip':archive(value,depth+1,budget)
            elif p.suffix.lower()=='.ppm':need(value.startswith(b'P6\n240 160\n255\n') and len(value)==115215,'unexpected screenshot format')
            else:value.decode('utf8');need(b'\0' not in value,'binary disguised as text')
        return result


def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+prior.REPO+'/'+path])
    def install(path,raw):
        target=root/path;need(not any(p.is_symlink() for p in (target,*target.parents)),'unsafe P05 destination')
        if target.exists():need(target.read_bytes()==raw,'refuse P05 original overwrite')
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    for record in RECORDS.values():
        run,aid,size,sha,head,_,_,_=record
        r=prior.load(api(f'actions/runs/{run}'));a=prior.load(api(f'actions/artifacts/{aid}'));jobs=prior.load(api(f'actions/runs/{run}/jobs?per_page=100'))
        prior.fields(a['workflow_run'],dict(id=run,head_sha=head))
        need(a['digest']=='sha256:'+sha and jobs['total_count']==len(jobs['jobs']),'changed/incomplete P05 Actions origin')
        meta={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
        meta.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
        prior.metadata(meta,record);raw=api(f'actions/artifacts/{aid}/zip')
        need(prior.identity(raw)==dict(size=size,sha256=sha),'P05 download identity differs');archive(raw)
        directory=Path(DIRECTORY)/str(run);install(directory/'original.zip',raw);install(directory/'actions.json',prior.stable(meta))


def source_snapshot(files,zip_name,bindings_name,root,checked):
    snapshot=archive(files[zip_name]);bindings=prior.load(files[bindings_name])
    need(set(snapshot)==set(bindings),'P05 source snapshot members differ')
    for name,binding in bindings.items():need(prior.same(prior.identity(snapshot[name]),binding),'P05 source snapshot hash differs')
    for name in checked:need(snapshot[name]==prior.read(root,name),'tested P05 source changed: '+name)
    return snapshot


def verify_roots(files,root=ROOT):
    need(files['tested-head.txt']==(RECORDS['roots'][4]+'\n').encode(),'roots execution HEAD differs')
    value=prior.load(files['p05-roots.json'])
    prior.fields(value,dict(status='STATIC_PARTIAL_DIAGNOSTICS_NOT_NATIVE_ACCEPTANCE',candidate=prior.CANDIDATE,new_emulator_runs=0,release_ready=False,rom_changed=False))
    graph=value['roots'];wild=value['wild']
    prior.fields(graph,dict(supplied_roots=5340,decoded_roots=5334,visited_scripts=10205,all_roots_decoded=False,no_match_proves_absence=False,physical_admission_accepted=False))
    need(len(graph['invalid_roots'])==6 and all(r['label'].startswith('map:12:7:') for r in graph['invalid_roots']),'root diagnostic identity differs')
    need(graph['diagnostics']==[dict(address=156560604,kind='unknown_opcode',opcode=240)],'unknown command diagnostic differs')
    prior.fields(wild,dict(expected_legacy_header_count=265,inspected_headers=265,complete_valid_catalogue=False,natural_acquisition_accepted=False))
    candidates=wild['target_candidates']
    need([(r['species'],r['group'],r['map'],r['header'],r['slot'],r['first_coordinate_owner']) for r in candidates]==[(411,1,113,73,6,True),(411,1,118,90,4,True)],'rooted candidate identity differs')
    need(wild['diagnostics']==[dict(error='info pointer outside ROM',group=96,header=139,info=1819541504,map=8,method='fishing')],'wild diagnostic differs')
    source_snapshot(files,'tracked-source-context.zip','tracked-source-bindings.json',root,('scripts/pr16_p05_root_diagnostics.py','scripts/pr16_receiver_audit.py'))
    need(b'Ran 16 tests' in files['unit.stderr'] and files['unit.stderr'].endswith(b'OK\n'),'roots unit completion differs')
    return dict(status=value['status'],decoded_roots=5334,unresolved_roots=graph['invalid_roots'],script_diagnostics=graph['diagnostics'],wild_diagnostics=wild['diagnostics'],capture_candidates=candidates,new_emulator_runs=0,physical_admission_accepted=False)


def verify_shop(files,root=ROOT):
    prefix='pr16-shop-routes/';ev=RECORDS['shop'][7]
    need(files[ev+'tested-head.txt']==(RECORDS['shop'][4]+'\n').encode(),'shop execution HEAD differs')
    report=prior.load(files[prefix+'result.json'])
    prior.fields(report,dict(status='PASS',scope=shop.SCOPE,candidate=prior.CANDIDATE,failures=[],actual_new_processes=10,successful_fresh_cores=20,physical_six_stone_shop_routes_accepted=True,natural_capture_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0,guard_checks=prior.GUARDS))
    need(len(report['results'])==len(shop.CASES),'shop result count differs');rows=[]
    for name,row in zip(shop.CASES,report['results'],strict=True):
        p=prefix+name;process=prior.load(files[p+'.process.json'])
        result=shop.validate(files[p+'.stdout'],name,shop.common.require_exited(process))
        need(row['name']==name and prior.same(row['result'],result) and prior.same(row['process'],process),'shop raw result/report differs')
        need(b'mGBA[' not in files[p+'.stderr'],'shop emulator warning');rows.append(result)
    for guard in prior.GUARDS:
        p=prefix+'guard-'+guard;shop.base.load().validate_guard(files[p+'.stdout'],files[p+'.stderr'],prior.load(files[p+'.process.json']))
    snapshot=source_snapshot(files,ev+'sources.zip',ev+'source-bindings.json',root,(shop.SELF,shop.SOURCE,shop.TEST,shop.WORKFLOW))
    for name,binding in report['sources'].items():need(prior.same(prior.identity(snapshot[name]),binding),'shop executed dependency differs')
    need(b'Ran 9 tests' in files[ev+'unit.log'] and files[ev+'unit.log'].endswith(b'OK\n'),'shop unit completion differs')
    images={name:prior.identity(files[prefix+name]) for name in ('eelektross-fixture.ppm','eelektross-selected-page.ppm','eelektross-returned.ppm','cancel-first-returned.ppm','cancel-page-returned.ppm','insufficient-bp-returned.ppm','missing-ring-returned.ppm')}
    return dict(status='DATA_PATH_PASS_VISUAL_REJECTED',new_native_processes=10,fresh_cores=20,cases=rows,
                purchase_cancel_inventory_bp_save_pass=True,shop_visual_acceptance=False,
                visual_review=dict(status='REJECTED',reason='MENU_AND_POST_CLOSE_BACKGROUND_CORRUPTION',images=images,
                                   control='missing-ring does not open the shop list and its returned background remains intact'),
                fixture_boundary='MAP_RING_BP_AND_CLEARED_CLAIMS_BEFORE_OBSERVATION_ONLY',
                natural_capture_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False)


def build(root=ROOT):
    results={};originals={}
    for label,record in RECORDS.items():
        run,aid,size,sha,head,_,_,_=record;directory=Path(DIRECTORY)/str(run)
        prior.metadata(prior.load(prior.read(root,directory/'actions.json')),record)
        raw=prior.read(root,directory/'original.zip');need(prior.identity(raw)==dict(size=size,sha256=sha),'retained P05 original differs')
        results[label]=(verify_roots if label=='roots' else verify_shop)(archive(raw),root)
        originals[label]=dict(run_id=run,artifact_id=aid,tested_head=head,path=str(directory/'original.zip'),size=size,sha256=sha)
    return dict(schema_version=1,status='PARTIAL_P05_DATA_PASS_DISPLAY_REPAIR_REQUIRED',candidate=prior.CANDIDATE,originals=originals,acceptance=results,new_emulator_runs=0,historical_originals_preserved=True,shop_visual_acceptance=False,full_p05_acceptance=False,release_ready=False)


def project(previous,root=ROOT):
    receipt=build(root);need(prior.same(receipt,prior.load(prior.read(root,RECEIPT))),'current P05 receipt differs')
    out=deepcopy(previous);out['p05_route_checkpoint']=dict(source_path=RECEIPT,native_processes=10,native_cores=20,shop_data_path_pass=True,shop_visual_acceptance=False,release_ready=False)
    for row in out['remaining_conditions']:
        if row['id']=='NATURAL_CAPTURE_GEAR':
            row.update(reason_ja='6種の石の実受付購入・取消・拒否・保存10件20コアはデータ判定成功。ただしメニューと終了後の背景に表示崩れがあり、修正・再試験が必要。自然捕獲および取得から戦闘への接続は未完了',partial_data_evidence=RECEIPT,display_repair_required=True)
        if row['id']=='PHYSICAL_CIRCUS_ADMISSION':
            row.update(resume='P05 root diagnostic run 34567225043 retained: 6 invalid roots and one unknown command remain; shared var 0x403A alone is not physical Circus entry',diagnostic_evidence=RECEIPT)
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true');parser.add_argument('--write',action='store_true');args=parser.parse_args()
    if args.fetch:fetch()
    value=build();path=ROOT/RECEIPT
    if args.write:path.write_bytes(prior.stable(value))
    else:need(prior.same(value,prior.load(path.read_bytes())),'stored P05 receipt differs')
    print(json.dumps(dict(status=value['status'],retained_native_processes=10,retained_native_cores=20,shop_visual_acceptance=False,new_emulator_runs=0,release_ready=False)))
if __name__=='__main__':main()
