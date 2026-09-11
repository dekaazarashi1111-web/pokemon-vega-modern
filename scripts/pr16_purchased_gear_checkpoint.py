#!/usr/bin/env python3
"""Rebuild scoped purchased-stone/Mega acceptance from actual retained originals."""
from copy import deepcopy
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_purchased_gear as native
import pr16_gear_originals as history
import pr16_captured_battle_checkpoint as captured
prior=history.prior;display=history.display;need=prior.need;load=prior.load;stable=prior.stable;identity=prior.identity
DIRECTORY=history.DIRECTORY
RECEIPT='content/modernization/pr16_purchased_gear_acceptance.json'
RECORD=(34587080329,10194085202,571143,'a571a83ab85d8fa8710f445d9f61aa65c8c796523f821bfdc84d73ff9d0cc7a2','6dec0d4e58ffa0c7751be1e05bdd864f87d023bd','pr16-purchased-gear','pr16-purchased-gear','pr16-purchased-gear-evidence/')
RECIPE_SHA='e9db6aca3b6610a134074087e68339d9a78f273cd92f836f50b69badd7262b75'
# All 58 raw images reviewed in four case contact sheets. The first Mega
# species-detection frame precedes sprite refresh; native-turn shows its form.
REVIEWED_IMAGES_SHA='d594115c87f2ec3c7a05692a769cb36f3ef586d5e8f7ac065cef7f6328947934'

def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+prior.REPO+'/'+path])
    run,aid,size,sha,head,_,_,_=RECORD
    r=load(api(f'actions/runs/{run}'));a=load(api(f'actions/artifacts/{aid}'));jobs=load(api(f'actions/runs/{run}/jobs?per_page=100'))
    prior.fields(a['workflow_run'],dict(id=run,head_sha=head));need(a['digest']=='sha256:'+sha and jobs['total_count']==len(jobs['jobs']),'gear success provenance differs')
    meta={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
    meta.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
    prior.metadata(meta,RECORD);raw=api(f'actions/artifacts/{aid}/zip');need(identity(raw)==dict(size=size,sha256=sha),'gear success download differs');display.archive(raw)
    for name,data in [('original.zip',raw),('actions.json',stable(meta))]:
        p=root/DIRECTORY/str(run)/name;need(not any(q.is_symlink() for q in (p,*p.parents)),'unsafe gear success destination')
        if p.exists():need(p.read_bytes()==data,'refuse gear success overwrite')
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

def verify(files,root=ROOT):
    p='pr16-purchased-gear/';ev=RECORD[7]
    need(files[ev+'tested-head.txt']==(RECORD[4]+'\n').encode(),'gear success execution HEAD differs')
    report=load(files[p+'result.json']);audit=load(files[p+'oracle.json'])
    prior.fields(report,dict(schema_version=2,status='PASS',scope=native.SCOPE,candidate=display.CANDIDATE,actual_new_processes=4,successful_fresh_cores=9,failures=[],guard_checks=prior.GUARDS,purchased_gear_to_battle_accepted=True,initial_map_party_ring_bp_policy_are_fixtures=True,ring_bp_natural_acquisition_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0))
    need(prior.same(report['oracle'],audit) and audit['candidate']==display.CANDIDATE,'gear natural oracle mismatch')
    need(identity(files[p+'candidate.json'])['sha256']==RECIPE_SHA,'gear candidate recipe differs')
    need(files[ev+'unit.log'].endswith(b'OK\n') and b'Ran 51 tests' in files[ev+'unit.log'],'gear rejection-test execution absent')
    snapshot=display.sources(files,ev,report,root,(native.SELF,native.SOURCE,native.TEST,native.WORKFLOW))
    need(len(snapshot)==35 and prior.same(load(files[ev+'source-bindings.json']),{k:identity(v) for k,v in snapshot.items()}),'gear source inventory differs')
    m=native.shop.base.load();generated={}
    for i,(src,target) in enumerate(m.EMBEDDED):generated[target]=m.embed(prior.read(root,src).decode(),'gear_embedded_'+str(i)).encode()
    for src,target,label in ((native.shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','gear_breeding'),(native.shop.SOURCE,'pr16_capture_shop_helpers.c','gear_shop'),(native.parent.SOURCE,'pr16_gear_capture_helpers.c','gear_capture')):
        generated[target]=m.embed(prior.read(root,src).decode(),label).encode()
    generated['pr16_gear_route.h']=native.route_header(audit).encode()
    actual=display.archive(files[p+'generated-controller.zip'])
    need(actual == generated|{'controller.c':prior.read(root,native.SOURCE)},'actual compiled gear controller differs')
    need(prior.same(report['generated'],{k:identity(v) for k,v in generated.items()}),'generated controller bindings differ')
    prior.guards(files,p);need(native.common.require_exited(load(files[p+'compile.process.json']))==0,'gear compile did not exit zero')
    rows=[];need(len(report['results'])==4,'gear case count differs')
    for name in native.CASES:
        loc=p+name;process=load(files[loc+'.process.json']);value=native.validate(files[loc+'.stdout'],files[loc+'.stderr'],name,native.common.require_exited(process),audit)
        row=dict(name=name,result=value,process=process);need(prior.same(report['results'][len(rows)],row),'gear raw/report mismatch');rows.append(row)
    images={k.removeprefix(p):identity(v) for k,v in files.items() if k.endswith('.ppm')}
    need(len(images)==58 and identity(stable(images))['sha256']==REVIEWED_IMAGES_SHA,'reviewed gear pixels differ')
    return dict(status='SCOPED_PURCHASE_GIVE_WALK_MEGA_REVERT_COLD_SAVE_ACCEPTED',candidate=display.CANDIDATE,cases=rows,new_native_processes=4,new_native_cores=9,
                source_files=35,reviewed_images=images,visual_review='58 ORIGINALS REVIEWED: SHOP/BAG/GIVE/WALK/BATTLE/RETURN/RELOAD; NO APPARENT UI CORRUPTION',
                initial_fixtures=['starting map and position','level100 Eelektross','ring','64 BP','initial empty item pocket','volatile next-battle Mega policy'],
                policy_scope='THREE SAME-SESSION CASES WITH INITIAL POLICY; ONE COLD-LOAD STANDARD-POLICY CONTROL; NO POST-BARRIER RECONFIGURATION',
                purchased_gear_to_battle_accepted=True,ring_bp_natural_acquisition_accepted=False,ordinary_policy_selection_accepted=False,all_six_species_gear_routes_accepted=False,full_p05_acceptance=False,release_ready=False)

def build(root=ROOT):
    captured.build(root);history.build(root)
    run,aid,size,sha,head,_,_,_=RECORD;directory=Path(DIRECTORY)/str(run)
    prior.metadata(load(prior.read(root,directory/'actions.json')),RECORD);raw=prior.read(root,directory/'original.zip');need(identity(raw)==dict(size=size,sha256=sha),'retained gear success differs')
    return dict(schema_version=1,status='SCOPED_PURCHASED_GEAR_ACCEPTED_PRODUCT_INCOMPLETE',candidate=display.CANDIDATE,acceptance=verify(display.archive(raw),root),
                original=dict(run_id=run,artifact_id=aid,tested_head=head,path=str(directory/'original.zip'),size=size,sha256=sha),
                historical_originals_receipt=history.RECEIPT,captured_battle_receipt=captured.RECEIPT,new_emulator_runs=0,full_p05_acceptance=False,release_ready=False)

def project(previous,root=ROOT):
    value=build(root);need(prior.same(value,load(prior.read(root,RECEIPT))),'saved gear receipt differs');out=deepcopy(previous)
    out['purchased_gear_checkpoint']=dict(source_path=RECEIPT,candidate=display.CANDIDATE,new_native_processes=4,new_native_cores=9,purchased_gear_to_battle_accepted=True,ring_bp_natural_acquisition_accepted=False,ordinary_policy_selection_accepted=False,full_p05_acceptance=False)
    if 'captured_battle_checkpoint' in out:out['captured_battle_checkpoint'].update(historical_capture_scope=True,purchased_gear_successor_receipt=RECEIPT)
    for row in out['remaining_conditions']:
        if row['id']=='NATURAL_CAPTURE_GEAR':
            row.update(reason_ja='自然捕獲個体の実戦2件6コアを保持。シビルドナイトの実受付購入→Bagで持たせる→通常歩行/自然遭遇→メガ切替/未切替/取消→技使用→復帰→通常保存/別コア再開は新規4件9コア成功。開始個体・リング・BP・許可policyはfixture。リング/BPと戦闘モード自体の通常供給、他の採用取得経路の対応整理は未受入',purchased_gear_evidence=RECEIPT,captured_to_battle_required=False,gear_to_battle_required=False,ring_bp_natural_supply_required=True,ordinary_policy_selection_required=True,
                       resume='Keep successful Eelektross purchased-stone route; do not redo it as missing. Resolve native ring/BP and configured-mode supply/accepted scope. Do not inject policy after cold Continue or globally enable Mega. Physical Circus remains separate.')
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--write',action='store_true');args=p.parse_args()
    if args.fetch:fetch()
    value=build()
    if args.write:(ROOT/RECEIPT).write_bytes(stable(value))
    else:need(prior.same(value,load(prior.read(ROOT,RECEIPT))),'gear success receipt differs')
    print(stable(dict(status=value['status'],candidate=display.CANDIDATE,new_native_processes=4,new_native_cores=9,new_emulator_runs=0,release_ready=False)).decode(),end='')
if __name__=='__main__':main()
