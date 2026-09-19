#!/usr/bin/env python3
"""snapshot人数と選出人数を分離。保存済み失敗を再実行せず新候補の18戦目以降を検証。"""
from pathlib import Path
import inspect
import json
import os
import struct
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_drought_launch as launch
import pr16_circus_drought_launch_boundary as boundary
need,identity,stable=boundary.need,boundary.identity,boundary.stable
SELF='scripts/pr16_circus_selection.py'
TEST='tests/test_pr16_circus_selection.py'
HEADER='overlays/circus_streak/circus_drought_selection.h'
FIXTURE='tests/fixtures/circus_drought_selection_fixture.c'
WATCH='tools/mgba_pr16_circus_selection_context.h'
WORKFLOW='.github/workflows/pr16-circus-selection.yml'
REPORT='content/modernization/pr16_circus_selection.json'
SOURCE='overlays/circus_streak/circus_drought.c'
PRIOR=boundary.REPORT
RAW='evidence/pr16_circus_drought_launch_boundary/35450725433/native/circus-continuous-30-save.stderr'
OLD=boundary.PRIOR
BASE='e4683f6c947e9a10fb12568b5a9c55a128dafc72'
RUN=35450725433
OUT=ROOT/'.local/pr16-circus-selection'
NEW=(SELF,TEST,HEADER,FIXTURE,WATCH,WORKFLOW)
NEXT='新候補の18戦目以降の実勝敗/元party600と人数/owner64/通常Save/fresh Continueを原本と画像で確認。真正30勝が未達なら最初の新停止のみ修復し、達成後に正規特性抑制へ進む。旧境界/旧CPU/旧ARM2link/既受入単体は再実行しない。'


def repair(source):
    changes=[('#include "circus_drought_launch.h"','#include "circus_drought_selection.h"'),
        ('CircusDroughtInitializeLaunch(&c, w, DroughtOriginal, DroughtInitVars, DroughtStep);',
         'CircusDroughtInitializeSelection(&c, READ8(0x02023F89u), w, DroughtOriginal, DroughtInitVars, DroughtStep);')]
    for old,new in changes:
        need(source.count(old)==1,'selection source preimage differs');source=source.replace(old,new)
    return source


def diagnose(raw):
    events=boundary.continuous_events(raw);rows=boundary.boundary_rows(raw)
    need(len(events)==81 and len(rows)==9,'original event/transition count')
    need(events[0]['label']=='fixture' and events[0]['count']==1,'original party fixture differs')
    need(events[-1]['label']=='confirmation' and events[-1]['battle']==17 and events[-1]['count']==3,'original selected three absent')
    need(sum(r['label']=='outcome' and r['outcome']==1 for r in events)==17,'seventeen real WIN outcomes')
    for row in rows:
        need(row['script']==0x09FF4DAD and row['current']==17 and row['outcome']==0 and row['count']==3,'actual script/count boundary')
    pre,last=rows[-2:]
    for row in (pre,last):
        need(row['callback2']==0x08055E75 and row['ready']==1 and bytes.fromhex(row['weather_raw'])[14]==1,'native readiness boundary')
    need((pre['weather_state'],pre['complete'],pre['index'],pre['offset'])==(5,1,32,32),'before initializer differs')
    need((last['weather_state'],last['complete'],last['index'],last['offset'])==(2,0,1,1),'empty loader relapse differs')
    return dict(events=81,transition_rows=9,actual_wins=17,original_party_count=1,selected_party_count=3,
        source_script_preserved=True,script_zero_field_drop_rejected=True,weather_before=[5,1,32,32],weather_after=[2,0,1,1],
        source_run=RUN,native_processes=1,original_conclusion='failure',diagnostic_endpoint_not_reached=True,
        cause_ja='c.countの取得元はfactory.party_count=退場時復元用人数。fixtureの元1体はVegaFactoryEnterで保存され、選出3体とは別。旧launch count==3 guardが元1体を拒否しoriginal initAllへ落ちる。現在人数を別readで確認し、保存人数1..6の所有権は維持する。')


def configure():
    task='USER-20260920-CIRCUS-SELECTION-RUN'+os.environ.get('GITHUB_RUN_ID','0')
    for k,v in dict(SELF=SELF,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=task,OUT=OUT,NEXT=NEXT).items():setattr(launch,k,v)
    d,b=launch.configure();d.FILES=tuple(dict.fromkeys((*d.FILES,*NEW,SOURCE,PRIOR,RAW,OLD)))
    d.c.FILES=d.FILES
    return d,b


def record(value,phase,stop):
    import pr16_resume as resume
    d,b=configure();r=b.rec;state=resume.load(ROOT,resume.STATE);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value));ref=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_selection_followup']=loss['selection_followup']=ref
    state['circus_continuous_followup']=dict(ref,target_wins=30);state['prior_actions_reconciled']=value['actions_reconciled']
    note='run35450725433/job105917285879は保存candidate a2c612a2不変/旧ARM再link0の1process。81eventsと境界9行を採取したがscript0 endpoint前提が誤りnative未完。元party1/選出3の混同を修復し、同じ境界診断は再実行しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER;r.TASK=launch.TASK
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*d.FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。元party人数1..6と現在3体を分離、旧WINと保存owner不変。対象host契約/新ARM2link/全ROM rollback/新continuationのみ。')


def prepare():
    import pr16_resume as resume
    d,b=configure();r=b.rec;head=r.scope();state=resume.validate(ROOT)
    need(r.command('git','rev-parse','HEAD^')==BASE and set(r.command('git','diff','--name-only',BASE,head).splitlines())==set(NEW),'selection source scope differs')
    need(not (ROOT/REPORT).exists(),'selection already attempted')
    previous=resume.load(ROOT,PRIOR);need(previous['recording_run']==RUN and not previous['diagnostic_complete'],'prior boundary status differs')
    need(identity((ROOT/RAW).read_bytes())==previous['text_evidence'][RAW],'raw boundary identity differs')
    run=r.api('actions/runs/'+str(RUN));need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='7797170adc2224afc18a46bacad1c5e4dc4ca643','original Actions differs')
    diagnosis=diagnose((ROOT/RAW).read_bytes())
    before=(ROOT/SOURCE).read_bytes();need(identity(before)==state['source_bindings'][SOURCE],'runtime before differs')
    (ROOT/SOURCE).write_text(repair(before.decode()))
    value=dict(schema_version=1,classification='CIRCUS_SELECTION_COUNT_REPAIR_PREPARED',diagnosis=diagnosis,
        actions_reconciled=[{k:run[k] for k in ('id','head_sha','status','conclusion')}],
        source_change=dict(path=SOURCE,before=identity(before),after=identity((ROOT/SOURCE).read_bytes())),
        host_tests=r.tests([Path(TEST).name]),accepted_native_cases_replayed=0,independent_old_arm_links_replayed=0,
        native_lifecycle_accepted=False,standard_save_fresh_continue=False,genuine_30_wins_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    record(value,'PREPARED','18戦目の実境界はscript09ff4dad保持・state5から2へ再停止。元1体snapshotを選出3体と誤比較していたguardを、2つの読取人数を分離して修復。旧WINと原party/ledgerは不変。')


def reconstruct():
    d,b=configure();d.reconstruct()
    from pr16_circus_streak import bounded_patch
    import pr16_streak_native as n
    old=json.loads((ROOT/OLD).read_bytes())['build'];recipe=json.loads((OUT/'build.json').read_bytes())
    parent=(OUT/'parent.gba').read_bytes();prior=bounded_patch(parent,old['patches']);need(identity(prior)==old['candidate'],'launch parent reconstruction')
    new=(OUT/'candidate.gba').read_bytes();off=recipe['payload']['offset'];end=off+max(old['payload']['size'],recipe['payload']['size'])
    changed=[i for i,(a,b) in enumerate(zip(prior,new)) if a!=b]
    need(changed and all(off<=i<end or d.TABLE<=i<d.TABLE+4 for i in changed),'selection delta escaped payload/table')
    dis=(OUT/'compile-1/disassembly.txt').read_text();payload=bytes.fromhex(recipe['patches'][0]['after'])
    need(struct.pack('<I',0x02023F89) in payload,'active party read missing from generated ARM')
    need('DroughtOriginal' in dis and 'DroughtInitVars' in dis and 'DroughtStep' in dis,'native ABI delegates absent')
    recipe['supersedes']=dict(candidate=old['candidate'],changed_bytes=len(changed),allowed_union=dict(offset=off,size=end-off),old_arm_links_replayed=0)
    recipe['change_impact']['selection_count']=dict(saved_count='factory.party_count (1..6)',active_count_address=0x02023F89,active_count_required=3,save_owner_unchanged=True,original_win_predicate_unchanged=True)
    (OUT/'build.json').write_bytes(stable(recipe));(n.INPUT/'report.json').write_bytes(stable(recipe))


def selection_context(raw):
    prefix=b'CIRCUS_SELECTION_CONTEXT ';rows=[boundary.strict(l[len(prefix):]) for l in raw.splitlines() if l.startswith(prefix)]
    need(len(rows)==1,'selection context absent/duplicate');r=rows[0]
    expected=dict(saved_count=1,selected_count=3,marker=2,snapshot=1,outcome=0,script=0x09FF4DAD,current=17,phase=2)
    need(set(r)=={'frame',*expected} and type(r['frame']) is int and r['frame']>0,'selection context schema')
    for k,v in expected.items():need(type(r[k]) is int and r[k]==v,'selection context '+k)
    return r


def native():
    d,b=configure();recipe=json.loads((OUT/'build.json').read_bytes());d.probe.SHA=recipe['candidate']['sha256']
    import pr16_circus_win_return_trace as trace
    def selection_watch(text):return boundary.compose_boundary_watch(text,(ROOT/WATCH).read_text(),trace.chained_watch)
    src=inspect.getsource(d.c.native);anchor="(ROOT/b.fade.WATCH).read_text()";need(src.count(anchor)==1,'native watch anchor')
    ns=dict(d.c.__dict__);ns['selection_watch']=selection_watch
    exec(compile(src.replace(anchor,'selection_watch('+anchor+')'),SELF+':selection-watch','exec'),ns)
    failure=None
    try:ns['native']()
    except ValueError as error:
        need(str(error)=='genuine 30-win target remains open','selection native failed: '+str(error));failure=str(error)
    raw=(OUT/'native'/(d.probe.CASE+'.stderr')).read_bytes();events=d.probe.parse(raw);old=d.probe.parse((ROOT/RAW).read_bytes())
    need(events[:79]==old[:79],'seventeen real outcome prefix changed')
    for i in (79,80):need(boundary.same_without_frame(events[i],old[i]),'settled17/18 confirmation semantics changed')
    need(events[81]['label']=='action' and events[81]['battle']==17 and events[81]['script']==0x09FF4DD8 and events[81]['newbs'],'eighteenth launch absent')
    witness=selection_context(raw);d.return_witness(raw)
    summary=json.loads((OUT/'native/streak.json').read_bytes())
    need([r['label'] for r in events[-2:]]==['saved','reloaded'],'standard Save/fresh Continue absent')
    result=dict(classification='CIRCUS_SELECTION_LAUNCH_LIFECYCLE_VERIFIED',eighteenth_launch_verified=True,selection_context=witness,
        native_prefix_events_identical=79,standard_save_fresh_continue=True,genuine_30_wins_verified=summary['genuine_30_wins_verified'],
        actual_wins=summary['wins'],actual_losses=summary['losses'],target_failure=failure,original_party_bytes_verified=600,owner_bytes_verified=64)
    (OUT/'selection-result.json').write_bytes(stable(result))


def finish():
    d,b=configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_SELECTION_NATIVE_OPEN'
    for path,key in [('build.json','build'),('native/report.json','native'),('native/streak.json','scoped_result'),('selection-result.json','selection_result')]:
        p=OUT/path
        if p.exists():value[key]=json.loads(launch.inherited.relative_text(p.read_bytes(),ROOT))
    if 'build' in value:value['candidate']=value['build']['candidate']
    if 'selection_result' in value:
        result=value['selection_result'];value['classification']=result['classification'];value['native_lifecycle_accepted']=value['standard_save_fresh_continue']=True
        value['genuine_30_wins_verified']=result['genuine_30_wins_verified']
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['text_evidence']={};value['evidence_transformations']={}
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.suffix not in {'.json','.txt','.stderr','.stdout'} or p.name.endswith('-receipt.json'):continue
        name='evidence/pr16_circus_selection/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
        value['evidence_transformations'][name]=launch.inherited.export(name,p.read_bytes(),value['text_evidence'])
    record(value,'RECORDED','元人数/選出数分離の新候補と原本を保存。18戦目launchと通常Save/fresh Continue='+str(value['standard_save_fresh_continue'])+'、真正30勝='+str(value['genuine_30_wins_verified'])+'。画像・抑制・最終P08/releaseは未完。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure()[1].pipeline()
    elif action=='pack':configure()[0].c.f.pack()
    elif action in ('prepare','reconstruct','native','finish'):globals()[action]()
    else:raise SystemExit('unknown command')
