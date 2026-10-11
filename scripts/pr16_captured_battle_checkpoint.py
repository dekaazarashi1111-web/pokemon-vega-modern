#!/usr/bin/env python3
"""Rebuild scoped capture-to-battle proof from immutable originals, never a release."""
from copy import deepcopy
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_captured_battle as native
base=native.retained;display=base.display;prior=base.prior;need=base.need;load=base.load;stable=base.stable;identity=base.identity
DIRECTORY='content/modernization/pr16_captured_battle_evidence'
RECEIPT='content/modernization/pr16_captured_battle_acceptance.json'
RECORD=(34577360374,10190213997,306904,'7880bc04b85d0d0a6e681138b879a7af3818c31dc85d9289650d9b60aa119d0c','1c8b61e9f9f156c541adb984cd38309611b50030','pr16-captured-battle','pr16-captured-battle','pr16-captured-battle-evidence/')
IMAGES={
 'cave-113-captured-battle-field.ppm':'677374d88e992333f7cd18969ddf174e88e349e9972b67978302e9bc43addafa',
 'cave-113-captured-battle-reloaded.ppm':'677374d88e992333f7cd18969ddf174e88e349e9972b67978302e9bc43addafa',
 'cave-113-captured-native-turn.ppm':'3e2b8f8b9d2018ec4d177dde6c29d2484a3a9c138cc2979ab2f35c70df17260a',
 'cave-113-captured-party-menu.ppm':'fb2e6383bd9ff66553bbc7f7f203616bb5fb0843be6e8ade824c6176aa0d1bcd',
 'cave-113-captured-sent-out.ppm':'756d60e7c1e07e545a7c1ba67cf934a4a00495e7e9e2a789450b76fa40982c2c',
 'cave-113-captured-shift-choice.ppm':'3b798b969547b63fa118af370664d214489567fadca2b6befa465f996d0e2e21',
 'cave-118-captured-battle-field.ppm':'0f4c02de4470c75358e4bcc3883b97a7327cdb4d21bd827da3743bf5f5bd4fec',
 'cave-118-captured-battle-reloaded.ppm':'0f4c02de4470c75358e4bcc3883b97a7327cdb4d21bd827da3743bf5f5bd4fec',
 'cave-118-captured-native-turn.ppm':'0ed5fd1be23f293655817dd686a8158e669dd511af197ab8b7e4864de60ac423',
 'cave-118-captured-party-menu.ppm':'e04935d7040815a4069829a9c8ac6659afcf9563a1916e065ad3bd433e91d4ad',
 'cave-118-captured-sent-out.ppm':'08c204f6f92e79602774e46457ca1b145c2b90f5299dce6647cd51bb4433f108',
 'cave-118-captured-shift-choice.ppm':'4235b8df49413cf62a5229b7ae7d23f171173b47f88484ca4786dda3d3eb0bba',
}


def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+prior.REPO+'/'+path])
    run,aid,size,sha,head,_,_,_=RECORD
    r=load(api(f'actions/runs/{run}'));a=load(api(f'actions/artifacts/{aid}'));jobs=load(api(f'actions/runs/{run}/jobs?per_page=100'))
    prior.fields(a['workflow_run'],dict(id=run,head_sha=head));need(a['digest']=='sha256:'+sha and jobs['total_count']==len(jobs['jobs']),'captured-battle Actions provenance incomplete')
    meta={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
    meta.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
    prior.metadata(meta,RECORD);raw=api(f'actions/artifacts/{aid}/zip');need(identity(raw)==dict(size=size,sha256=sha),'captured-battle download differs');display.archive(raw)
    for name,data in [('original.zip',raw),('actions.json',stable(meta))]:
        p=root/DIRECTORY/str(run)/name;need(not any(q.is_symlink() for q in (p,*p.parents)),'unsafe captured-battle destination')
        if p.exists():need(p.read_bytes()==data,'refuse captured-battle original overwrite')
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)


def verify(files,root=ROOT):
    p='pr16-captured-battle/';ev=RECORD[7];need(files[ev+'tested-head.txt']==(RECORD[4]+'\n').encode(),'captured-battle execution HEAD differs')
    report=load(files[p+'result.json']);audit=load(files[p+'oracle.json'])
    prior.fields(report,dict(schema_version=1,status='PASS',scope=native.SCOPE,candidate=display.CANDIDATE,new_native_processes=2,successful_fresh_cores=6,failures=[],guard_checks=prior.GUARDS,captured_to_native_battle_accepted=True,gear_acquisition_accepted=False,full_p05_acceptance=False,release_ready=False,old_runs_relabelled=0))
    old_record=base.RECORDS['capture'];old_raw=prior.read(root,Path(base.DIRECTORY)/str(old_record[0])/'original.zip');need(identity(old_raw)==dict(size=old_record[2],sha256=old_record[3]),'parent captured-only original differs')
    old=display.archive(old_raw)
    need(prior.same(audit,load(old['pr16-natural-capture/oracle.json'])) and prior.same(report['oracle'],audit),'captured-battle exact native table oracle differs')
    need(identity(files[p+'candidate.json'])['sha256']==base.RECIPE_SHA,'captured-battle candidate recipe differs')
    need(files[p+'controller.c']==native.controller().encode() and identity(files[p+'controller.c'])==report['controller'],'executed captured-battle controller differs')
    snapshot=display.sources(files,ev,report,root,(native.SELF,native.SOURCE,native.TEST,native.WORKFLOW,native.capture.SELF,native.capture.SOURCE))
    need(prior.same(load(files[ev+'source-bindings.json']),{k:identity(v) for k,v in snapshot.items()}),'captured-battle source archive inventory differs')
    need(b'Ran 44 tests' in files[ev+'unit.log'] and files[ev+'unit.log'].endswith(b'OK\n'),'captured-battle rejection tests incomplete')
    prior.guards(files,p);need(native.common.require_exited(load(files[p+'compile.process.json']))==0,'captured-battle compile failed')
    need(len(report['results'])==2,'captured-battle raw count differs');rows=[]
    for name in native.capture.CASES:
        loc=p+name;process=load(files[loc+'.process.json']);value=native.validate(files[loc+'.stdout'],files[loc+'.stderr'],name,native.common.require_exited(process),audit)
        row=dict(name=name,result=value,process=process);need(prior.same(report['results'][len(rows)],row),'captured-battle raw/report differs');rows.append(row)
    images=base.IMAGES|IMAGES
    for name,sha in images.items():need(identity(files[p+name])==dict(size=115215,sha256=sha),'reviewed captured-battle image differs')
    return dict(status='SCOPED_CAPTURE_SWITCH_NATIVE_TURN_AND_TWO_COLD_SAVES_ACCEPTED',candidate=display.CANDIDATE,cases=rows,new_native_processes=2,new_native_cores=6,
                capture_only_prior_run_preserved_not_relabelled=True,initial_fixtures=['map and position','species4 level100 lead','one Master Ball','remembered ball pocket'],
                reviewed_images=images,visual_review='PARTY_SELECTION_SENDOUT_NATIVE_TURN_FIELD_AND_RELOAD_REVIEWED; NO_UI_CORRUPTION_OBSERVED',
                captured_to_native_battle_accepted=True,gear_acquisition_accepted=False,full_p05_acceptance=False,release_ready=False)


def build(root=ROOT):
    base.build(root);run,aid,size,sha,head,_,_,_=RECORD;directory=Path(DIRECTORY)/str(run)
    prior.metadata(load(prior.read(root,directory/'actions.json')),RECORD);raw=prior.read(root,directory/'original.zip');need(identity(raw)==dict(size=size,sha256=sha),'retained captured-battle original differs')
    accepted=verify(display.archive(raw),root)
    return dict(schema_version=1,status='SCOPED_CAPTURED_BATTLE_ACCEPTED_PRODUCT_INCOMPLETE',candidate=display.CANDIDATE,acceptance=accepted,
                original=dict(run_id=run,artifact_id=aid,tested_head=head,path=str(directory/'original.zip'),size=size,sha256=sha),
                capture_only_receipt=base.RECEIPT,new_emulator_runs=0,full_p05_acceptance=False,release_ready=False)


def project(previous,root=ROOT):
    value=build(root);need(prior.same(value,load(prior.read(root,RECEIPT))),'saved captured-battle receipt differs');out=deepcopy(previous)
    out['captured_battle_checkpoint']=dict(source_path=RECEIPT,candidate=display.CANDIDATE,new_native_processes=2,new_native_cores=6,captured_to_native_battle_accepted=True,gear_to_battle_accepted=False,full_p05_acceptance=False)
    if 'natural_capture_checkpoint' in out:out['natural_capture_checkpoint'].update(historical_capture_only=True,captured_battle_successor_receipt=RECEIPT)
    for row in out['remaining_conditions']:
        if row['id']=='NATURAL_CAPTURE_GEAR':
            row.update(reason_ja='シビルドンの自然歩行→捕獲→通常保存/再開→次の自然遭遇→実メニュー交代→通常技のPP消費→離脱→再保存/第3コア再開は2件6コア成功。先行捕獲だけの2件4コアは別原本。石の実購入/表示/保存の既存成功も保持。通常取得した道具の装備から戦闘までの接続は未受入',
                       captured_battle_evidence=RECEIPT,captured_to_battle_required=False,gear_to_battle_required=True,
                       resume='Use retained capture and shop originals. Next connect actual gear acquisition/equipment to battle; do not rerun capture as missing or inject target/gear after observation starts.')
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--write',action='store_true');args=p.parse_args()
    if args.fetch:fetch()
    value=build()
    if args.write:(ROOT/RECEIPT).write_bytes(stable(value))
    else:need(prior.same(value,load(prior.read(ROOT,RECEIPT))),'saved captured-battle receipt differs')
    print(stable(dict(status=value['status'],candidate=display.CANDIDATE,new_native_processes=2,new_native_cores=6,new_emulator_runs=0,release_ready=False)).decode(),end='')
if __name__=='__main__':main()
