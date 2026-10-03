#!/usr/bin/env python3
"""Persist exact natural-capture originals without inflating full P05 acceptance."""
from copy import deepcopy
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_shop_display_checkpoint as display
import pr16_natural_capture as native
prior=display.prior;need=prior.need;load=prior.load;identity=prior.identity;stable=prior.stable
SELF='scripts/pr16_natural_capture_checkpoint.py'
RECEIPT='content/modernization/pr16_natural_capture_acceptance.json'
DIRECTORY='content/modernization/pr16_natural_capture_evidence'
RECORDS={
 'geometry':(34575014339,10189282487,8329348,'f7963318257bd6127eaaf09a0f0e7e1124789d5100abf93ce11d668c5292331e','df5cad6e68e80053bec5eedc13d34c35f36c0c56','pr16-capture-geometry','pr16-capture-geometry','pr16-capture-geometry-evidence/'),
 'capture':(34575955233,10189661850,246689,'879ebf377e93d48bb28ed4572699352bb92923b6e3925e876ee09f7cde6ea361','68f9459630a2bf7215c58f12cb0557f57f15c6ff','pr16-natural-capture','pr16-natural-capture','pr16-natural-capture-evidence/'),
}
RECIPE_SHA='e9db6aca3b6610a134074087e68339d9a78f273cd92f836f50b69badd7262b75'
IMAGES={
 'cave-113-ball-pocket.ppm':'1a0dc757f85130e6eb44d8c59757709cb619bce756df4da88d4c0c99f607036e',
 'cave-113-ball-selected.ppm':'ed16dee4fd7719b2b553c722f96550abfe4928a8518d7c9269f040d07005d4ff',
 'cave-113-captured-field.ppm':'677374d88e992333f7cd18969ddf174e88e349e9972b67978302e9bc43addafa',
 'cave-113-fixture.ppm':'9b4c86d8b5501fe0f47326a8dc480ae0d7267160708e1e16a615003ccfeccec2',
 'cave-113-natural-target.ppm':'92a9771d7117b63d8231111fd7c160cf61a124d4c912c357870a03ad3020d1bb',
 'cave-113-reloaded.ppm':'677374d88e992333f7cd18969ddf174e88e349e9972b67978302e9bc43addafa',
 'cave-118-ball-pocket.ppm':'1a0dc757f85130e6eb44d8c59757709cb619bce756df4da88d4c0c99f607036e',
 'cave-118-ball-selected.ppm':'ed16dee4fd7719b2b553c722f96550abfe4928a8518d7c9269f040d07005d4ff',
 'cave-118-captured-field.ppm':'0f4c02de4470c75358e4bcc3883b97a7327cdb4d21bd827da3743bf5f5bd4fec',
 'cave-118-fixture.ppm':'65f7d69c80d64f25fd3f8ac7edcbf9a0bac49eba43c73a1471278124e0f61865',
 'cave-118-natural-target.ppm':'0916d70d1d43bd0e128c88d758af17785d2a958df38174f65ebb28ec017d7944',
 'cave-118-reloaded.ppm':'0f4c02de4470c75358e4bcc3883b97a7327cdb4d21bd827da3743bf5f5bd4fec',
}


def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+prior.REPO+'/'+path])
    def install(path,raw):
        p=root/path;need(not any(q.is_symlink() for q in (p,*p.parents)),'unsafe capture original destination')
        if p.exists():need(p.read_bytes()==raw,'refuse original replacement')
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    for record in RECORDS.values():
        run,aid,size,sha,head,_,_,_=record
        r=load(api(f'actions/runs/{run}'));a=load(api(f'actions/artifacts/{aid}'));jobs=load(api(f'actions/runs/{run}/jobs?per_page=100'))
        prior.fields(a['workflow_run'],dict(id=run,head_sha=head));need(a['digest']=='sha256:'+sha and jobs['total_count']==len(jobs['jobs']),'capture provenance incomplete')
        meta={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
        meta.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
        prior.metadata(meta,record);raw=api(f'actions/artifacts/{aid}/zip');need(identity(raw)==dict(size=size,sha256=sha),'downloaded capture original differs');display.archive(raw)
        p=Path(DIRECTORY)/str(run);install(p/'original.zip',raw);install(p/'actions.json',stable(meta))


def verify_geometry(files,root=ROOT):
    p='pr16-capture-geometry/';ev=RECORDS['geometry'][7]
    need(files[ev+'tested-head.txt']==(RECORDS['geometry'][4]+'\n').encode(),'geometry execution HEAD differs')
    report=load(files[p+'geometry.json']);prior.fields(report,dict(status='STATIC_GEOMETRY_NOT_NATIVE_CAPTURE',candidate=prior.CANDIDATE,new_emulator_runs=0,release_ready=False))
    snapshot=display.archive(files[ev+'tracked-sources.zip']);need(prior.same(load(files[ev+'source-bindings.json']),{k:identity(v) for k,v in snapshot.items()}),'geometry source archive inventory differs')
    for name in ('scripts/pr16_capture_geometry.py','tools/trainer_final/kanto_events.py','.github/workflows/pr16-capture-geometry.yml'):
        need(snapshot[name]==prior.read(root,name),'executed geometry source changed: '+name)
    need(len(report['maps'])==2,'geometry map count differs')
    for number,model in zip((113,118),report['maps'],strict=True):
        prior.fields(model,dict(group=1,map=number,native_encounter_accepted=False))
    return report


def verify_capture(files,geometry,root=ROOT):
    p='pr16-natural-capture/';ev=RECORDS['capture'][7]
    need(files[ev+'tested-head.txt']==(RECORDS['capture'][4]+'\n').encode(),'capture execution HEAD differs')
    report=load(files[p+'result.json']);audit=load(files[p+'oracle.json'])
    prior.fields(report,dict(schema_version=1,status='PASS',scope=native.SCOPE,candidate=display.CANDIDATE,failures=[],actual_new_processes=2,successful_fresh_cores=4,natural_capture_accepted=True,gear_acquisition_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0,guard_checks=prior.GUARDS))
    need(prior.same(report['oracle'],audit),'capture source oracle differs')
    prior.fields(audit,dict(candidate=display.CANDIDATE,target_injected=False,starting_map_lead_and_ball_are_fixtures=True))
    need(set(audit['cases'])==set(native.CASES),'capture oracle cases missing')
    for name,(number,start,end) in native.CASES.items():
        model=next(m for m in geometry['maps'] if m['map']==number);row=audit['cases'][name]
        need(identity(stable(model))==row['map_geometry'],'capture geometry differs from independent static run')
        prior.fields(row,dict(group=1,map=number));need(row['pair'] in model['walkable_pairs'] and row['pair']['start']==start and row['pair']['end']==end and row['pair']['behavior']==8,'capture pair differs')
    need(identity(files[p+'candidate.json'])['sha256']==RECIPE_SHA,'candidate no longer exact reviewed shop successor')
    snapshot=display.sources(files,ev,report,root,(native.SELF,native.SOURCE,native.TEST,native.WORKFLOW))
    need(prior.same(load(files[ev+'source-bindings.json']),{k:identity(v) for k,v in snapshot.items()}),'capture source archive inventory differs')
    need(b'Ran 34 tests' in files[ev+'unit.log'] and files[ev+'unit.log'].endswith(b'OK\n'),'capture rejection tests incomplete')
    prior.guards(files,p);need(native.common.require_exited(load(files[p+'compile.process.json']))==0,'capture compiler failed')
    need(len(report['results'])==2,'native capture raw count differs');rows=[]
    for name in native.CASES:
        base=p+name;process=load(files[base+'.process.json']);value=native.validate(files[base+'.stdout'],files[base+'.stderr'],name,native.common.require_exited(process),audit)
        row=dict(name=name,result=value,process=process);need(prior.same(report['results'][len(rows)],row),'capture raw/report differs');rows.append(row)
    for name,sha in IMAGES.items():need(identity(files[p+name])==dict(size=115215,sha256=sha),'reviewed capture pixels differ')
    return dict(status='SCOPED_NATURAL_CAPTURE_AND_COLD_SAVE_ACCEPTED',candidate=display.CANDIDATE,cases=rows,new_native_processes=2,new_native_cores=4,
                initial_fixtures=['map and position','species4 level100 lead','one Master Ball','remembered ball pocket'],
                target_mon_injected=False,rng_written=False,direct_wild_or_ball_function_called=False,
                reviewed_images=IMAGES,visual_review='NO_CAPTURE_UI_CORRUPTION_OBSERVED; MAP118_DARKNESS_MATCHES_FIXTURE_AND_RELOAD',
                data_validation_tests=34,gear_acquisition_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False,release_ready=False)


def build(root=ROOT):
    sets={};originals={}
    for label,record in RECORDS.items():
        run,aid,size,sha,head,_,_,_=record;p=Path(DIRECTORY)/str(run)
        prior.metadata(load(prior.read(root,p/'actions.json')),record);raw=prior.read(root,p/'original.zip');need(identity(raw)==dict(size=size,sha256=sha),'retained capture original differs')
        sets[label]=display.archive(raw);originals[label]=dict(run_id=run,artifact_id=aid,tested_head=head,path=str(p/'original.zip'),size=size,sha256=sha)
    geometry=verify_geometry(sets['geometry'],root);capture=verify_capture(sets['capture'],geometry,root)
    return dict(schema_version=1,status='SCOPED_NATURAL_CAPTURE_ACCEPTED_PRODUCT_INCOMPLETE',candidate=display.CANDIDATE,originals=originals,capture=capture,
                static_geometry=dict(new_emulator_runs=0,native_capture_accepted=False),natural_capture_accepted=True,new_emulator_runs=0,
                historical_successes_preserved_not_relabelled=True,full_p05_acceptance=False,release_ready=False)


def project(previous,root=ROOT):
    value=build(root);need(prior.same(value,load(prior.read(root,RECEIPT))),'saved capture receipt differs');out=deepcopy(previous)
    out['natural_capture_checkpoint']=dict(source_path=RECEIPT,candidate=display.CANDIDATE,natural_capture_accepted=True,new_native_processes=2,new_native_cores=4,
                                           fixture_boundary=value['capture']['initial_fixtures'],gear_acquisition_accepted=False,battle_connection_accepted=False,full_p05_acceptance=False)
    for row in out['remaining_conditions']:
        if row['id']=='NATURAL_CAPTURE_GEAR':
            row.update(reason_ja='同一ショップ修正版で洞窟2経路の自然歩行→シビルドン捕獲→通常保存→別コア再開は2件4コア成功。開始位置・先頭個体・ボールはfixture。石の実購入・表示・保存の既存成功も保持。通常取得から戦闘への接続、リング/BP/ボールの通常入手は未受入',
                       natural_capture_evidence=RECEIPT,natural_capture_required=False,gear_to_battle_required=True)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--write',action='store_true');args=p.parse_args()
    if args.fetch:fetch()
    value=build()
    if args.write:(ROOT/RECEIPT).write_bytes(stable(value))
    else:need(prior.same(value,load(prior.read(ROOT,RECEIPT))),'saved capture receipt differs')
    print(stable(dict(status=value['status'],candidate=display.CANDIDATE,new_native_processes=2,new_native_cores=4,new_emulator_runs=0,release_ready=False)).decode(),end='')
if __name__=='__main__':main()
