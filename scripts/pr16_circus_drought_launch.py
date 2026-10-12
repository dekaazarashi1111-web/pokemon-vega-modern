#!/usr/bin/env python3
"""選出復帰のoutcome0を限定許可し、旧WIN・実関数境界と保存ownerを維持。"""
from pathlib import Path
import io
import json
import os
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_drought_calls as inherited
OLD=inherited.REPORT
INHERITED=(inherited.SELF,inherited.TEST,inherited.WORKFLOW)
SELF='scripts/pr16_circus_drought_launch.py'
TEST='tests/test_pr16_circus_drought_launch.py'
HEADER='overlays/circus_streak/circus_drought_launch.h'
FIXTURE='tests/fixtures/circus_drought_launch_fixture.c'
WORKFLOW='.github/workflows/pr16-circus-drought-launch.yml'
REPORT='content/modernization/pr16_circus_drought_launch.json'
CPU='content/modernization/pr16_circus_launch_cpu.json'
ROWS='evidence/pr16_circus_launch_cpu/35436330902/cpu-rows.json'
RAW='evidence/pr16_circus_drought_calls/35435801505/native/circus-continuous-30-save.stderr'
TASK='USER-20260919-CIRCUS-DROUGHT-LAUNCH'
OUT=ROOT/'.local/pr16-circus-drought-launch'
RUN=35436330902
ARTIFACT=10582825654
ARCHIVE=dict(size=1674561,sha256='a8790cca69386158c0e4182fda80fedb073a1ed852d6271b1d487efcb1bcdcc9')
need,identity,stable=inherited.need,inherited.identity,inherited.stable
NEXT='新候補で18戦目の正規launch・以降の実勝敗・原party600/owner64・通常Save/fresh Continueを確認。真正30勝未達は最初の新停止だけを修復し、達成後に正規特性抑制へ進む。旧CPU診断/旧独立2link/受入単体の再実行は禁止。'


def diagnose(rows):
    need([r['elapsed'] for r in rows]==[1,*range(30,601,30)],'CPU source points')
    for r in rows:
        need(r['current']==17 and r['outcome']==0 and r['script']==0x09FF4DAD and r['types']&0x04000000,'launch boundary')
    tail=rows[1:]
    for r in tail:
        w=bytes.fromhex(r['weather']);d=bytes.fromhex(r['drought']);tasks=bytes.fromhex(r['tasks'])
        need(len(w)==64 and len(d)==32 and len(tasks)==640,'CPU byte shape')
        need(w[14]==1 and w[16]==1 and w[20:22]==b'\x02\0' and w[24:27]==b'\x0c\x0c\0' and d[21:23]==b'\1\1','empty Drought cursor')
        active=[int.from_bytes(tasks[i:i+4],'little') for i in range(0,640,40) if tasks[i+4]==1]
        need(active.count(0x0807951D)==1 and active.count(0x0807D465)==1,'native weather/script tasks')
    samples=sum(0x0807A374<=r['pc']<=0x0807A3BC or 0x0807AD1E<=r['pc']<=0x0807AE20 for r in tail)
    need(samples>=16,'native busy-loop PC source')
    return dict(points=21,elapsed_frames=600,native_loop_points=samples,script=0x09FF4DAD,outcome=0,current=17,
                state=2,cursor=[1,1],complete=0,reason_ja='選出画面→field復帰でも空loaderが再初期化される。WIN専用条件がoutcome0/chooser scriptを除外していた。')


def repair(source):
    edits=[('#include "circus_drought.h"','#include "circus_drought_launch.h"'),
           ('c.outcome == 1u && c.callback','c.outcome <= 1u && c.callback'),
           ('CircusDroughtInitialize(&c, w,','CircusDroughtInitializeLaunch(&c, w,')]
    for old,new in edits:
        need(source.count(old)==1,'launch repair preimage: '+old);source=source.replace(old,new)
    return source


def configure():
    for k in ('SELF','TEST','WORKFLOW','REPORT','TASK','OUT','NEXT'):setattr(inherited,k,globals()[k])
    d,b=inherited.configure();d.FILES=tuple(dict.fromkeys((*d.FILES,*INHERITED,HEADER,FIXTURE,CPU,ROWS,OLD,RAW)))
    d.c.FILES=d.FILES
    return d,b


def record(value,phase,stop):
    import pr16_resume as resume
    d,b=configure();r=b.rec;state=resume.load(ROOT,resume.STATE);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value));ref=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_drought_launch_followup']=loss['drought_launch_followup']=ref
    state['circus_continuous_followup']=dict(ref,target_wins=30);state['prior_actions_reconciled']=value['actions_reconciled']
    note='run35436330902/job105879496730はROM98b9eea4不変・ARM再link0で18戦目のCPU21点/600frame診断SUCCESS。outcome0/script09ff4dad・weather12/state2/empty cursor1/1・native busy loopを確認。診断を保存/30勝受入に変えず、同一診断は再実行しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER;r.TASK=TASK
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*d.FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。旧WIN predicate不変・選出復帰3script/outcome0を別guardで追加。host scope/native ABI/生成ARM/独立2link/旧allocation不変/通常入力だけの新continuation。')


def prepare():
    import pr16_resume as resume
    d,b=configure();r=b.rec;r.scope();state=resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'launch repair already attempted')
    prior=resume.load(ROOT,CPU);need(prior['recording_run']==RUN and prior['diagnostic_complete'],'CPU diagnostic not complete')
    for p,bound in prior['text_evidence'].items():need(identity((ROOT/p).read_bytes())==bound,'CPU source drift')
    run=r.api('actions/runs/'+str(RUN));artifact=r.api('actions/artifacts/'+str(ARTIFACT))
    need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']=='6455fa59f6ac4888007fd947d0e35712734c8f13','CPU Actions not successful')
    need(artifact['workflow_run']['id']==RUN and artifact['digest']=='sha256:'+ARCHIVE['sha256'],'CPU artifact')
    raw=subprocess.check_output(['gh','api','repos/'+r.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT);need(identity(raw)==ARCHIVE,'CPU ZIP')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(z.read('finish/cpu-rows.json')==(ROOT/ROWS).read_bytes(),'CPU rows not original')
        shot='finish/native/'+d.probe.CASE+'-launch-cpu-wait-600.ppm';screens={shot:identity(z.read(shot))}
    diagnosis=diagnose(json.loads((ROOT/ROWS).read_bytes()))
    old=resume.load(ROOT,OLD);sites=old['build']['launch_sites']
    need([s['new'] for s in sites]==[0x09FF4CEB,0x09FF4D4C,0x09FF4DAD] and all(s['size']==43 and s['selector']==sites[0]['selector'] and s['draw']==sites[0]['draw'] for s in sites),'three native chooser continuations differ')
    before=(ROOT/d.SOURCE).read_bytes();need(identity(before)==state['source_bindings'][d.SOURCE],'source binding drift')
    (ROOT/d.SOURCE).write_text(repair(before.decode()))
    value=dict(schema_version=1,classification='CIRCUS_DROUGHT_LAUNCH_REPAIR_PREPARED',diagnosis=diagnosis,
        actions_reconciled=[{k:run[k] for k in ('id','head_sha','status','conclusion')}],
        inherited_diagnostic=dict(run_id=RUN,job_id=105879496730,artifact_id=ARTIFACT,archive=ARCHIVE,screens=screens,visual_review_ja='600frame後も黒画面。選出確認の後にDrought初期化がstate2で停止し、戦闘action/Saveに未到達。'),
        source_change=dict(path=d.SOURCE,before=identity(before),after=identity((ROOT/d.SOURCE).read_bytes())),
        host_tests=r.tests([Path(TEST).name,'test_pr16_circus_drought.py','test_pr16_circus_drought_calls.py']),
        win_return_native_verified=False,launch_native_verified=False,standard_save_fresh_continue=False,genuine_30_wins_verified=False,
        accepted_native_cases_replayed=0,independent_old_arm_links_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    record(value,'PREPARED','18戦目の新停止をCPU原本で確定。戦闘開始前の正規選出3経路だけ空Drought loader修復を追加し、旧WIN/LOSS/Factory/保存ownerは維持。新候補を独立2linkと未完continuationで検証。')


def reconstruct():
    d,b=configure();d.reconstruct()
    from pr16_circus_streak import bounded_patch
    import pr16_streak_native as n
    old=json.loads((ROOT/OLD).read_bytes())['build'];recipe=json.loads((OUT/'build.json').read_bytes())
    prior=bounded_patch((OUT/'parent.gba').read_bytes(),old['patches']);need(identity(prior)==old['candidate'],'previous candidate reconstruction')
    new=(OUT/'candidate.gba').read_bytes();off=recipe['payload']['offset'];end=off+max(old['payload']['size'],recipe['payload']['size'])
    changed=[i for i,(a,b) in enumerate(zip(prior,new)) if a!=b]
    need(changed and all(off<=i<end or d.TABLE<=i<d.TABLE+4 for i in changed),'launch delta escaped payload/table')
    recipe['supersedes']=dict(candidate=old['candidate'],changed_bytes=len(changed),allowed_union=dict(offset=off,size=end-off),old_arm_links_replayed=0)
    recipe['change_impact']['launch_scope']=dict(outcome=0,scripts=[0x09FF4CEB,0x09FF4D4C,0x09FF4DAD],party_count=3,original_win_predicate_unchanged=True)
    (OUT/'build.json').write_bytes(stable(recipe));(n.INPUT/'report.json').write_bytes(stable(recipe))


def native():
    d,b=configure();d.native()
    events=d.probe.parse((OUT/'native'/(d.probe.CASE+'.stderr')).read_bytes());old=d.probe.parse((ROOT/RAW).read_bytes())
    need(events[:79]==old[:79],'seventeen real outcomes changed')
    for i in (79,80):need({k:v for k,v in events[i].items() if k!='frame'}=={k:v for k,v in old[i].items() if k!='frame'},'settled17/18th confirmation changed')
    action=events[81];need(action['label']=='action' and action['battle']==17 and action['script']==0x09FF4DD8 and action['newbs'],'18th real launch missing')
    result=json.loads((OUT/'return-result.json').read_bytes());result.update(classification='CIRCUS_DROUGHT_LAUNCH_SAVE_CONTINUE_NATIVE_VERIFIED',eighteenth_native_launch_verified=True,
        native_prefix_events_identical=79,settled_and_confirmation_semantics_preserved=True,launch_frame=action['frame'])
    (OUT/'launch-result.json').write_bytes(stable(result))


def finish():
    d,b=configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_DROUGHT_LAUNCH_NATIVE_OPEN'
    for path,key in [('build.json','build'),('native/report.json','native'),('native/streak.json','scoped_result'),('launch-result.json','launch_result')]:
        p=OUT/path
        if p.exists():value[key]=json.loads(inherited.relative_text(p.read_bytes(),ROOT))
    if 'build' in value:value['candidate']=value['build']['candidate']
    if 'launch_result' in value:
        value['classification']=value['launch_result']['classification'];value['win_return_native_verified']=value['launch_native_verified']=value['standard_save_fresh_continue']=True
        value['genuine_30_wins_verified']=value['launch_result']['genuine_30_wins_verified']
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['text_evidence']={};value['evidence_transformations']={}
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.suffix not in {'.json','.txt','.stderr','.stdout'} or p.name.endswith('-receipt.json'):continue
        name='evidence/pr16_circus_drought_launch/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
        value['evidence_transformations'][name]=inherited.export(name,p.read_bytes(),value['text_evidence'])
    record(value,'RECORDED','選出復帰修復の原本と新候補差分を保存。18戦目native launch/通常Save/fresh Continue='+str(value['launch_native_verified'])+'、真正30勝='+str(value['genuine_30_wins_verified'])+'。画像・正規特性抑制・P08は別ゲート。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure()[1].pipeline()
    elif action=='pack':configure()[0].c.f.pack()
    elif action in ('prepare','reconstruct','native','finish'):globals()[action]()
    else:raise SystemExit('unknown command')
