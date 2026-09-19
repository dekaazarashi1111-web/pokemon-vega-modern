#!/usr/bin/env python3
"""18戦目修復/実21勝を保存し、次の6体選出→field境界だけを読む。"""
from copy import deepcopy
from pathlib import Path
import inspect
import io
import zipfile
import json
import os
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_selection as s
need,identity,stable=s.need,s.identity,s.stable
SELF='scripts/pr16_circus_rental_boundary.py'
TEST='tests/test_pr16_circus_rental_boundary.py'
WATCH='tools/mgba_pr16_circus_rental_boundary.h'
FIXTURE='tests/fixtures/circus_drought_snapshot_fixture.c'
WORKFLOW='.github/workflows/pr16-circus-rental-boundary.yml'
REPORT='content/modernization/pr16_circus_rental_boundary.json'
PRIOR='content/modernization/pr16_circus_selection.json'
LEGACY='tests/test_pr16_circus_drought_launch.py'
RAW='evidence/pr16_circus_selection/35451609631/native/circus-continuous-30-save.stderr'
BASE='c037e2bfeb9bbb68ebaefef9b652800ff9e185ac'
RUN=35451609631
OUT=ROOT/'.local/pr16-circus-rental-boundary'
NEW=(SELF,TEST,WATCH,FIXTURE,WORKFLOW)
NEXT='18戦目起動・実21勝/63BP/元party600復元の受入範囲は維持し、22戦目の初回6体選出→field境界の新readonly原本から最初の停止だけ修復する。Save/fresh Continue/真正30勝/正規抑制は未受入。旧ARM link・旧境界・受入単体を再実行しない。'


def accepted_prefix(raw):
    import pr16_circus_continuous_probe as p
    events=p.parse(raw);old=p.parse((ROOT/s.RAW).read_bytes())
    need(len(events)==100 and events[:79]==old[:79],'unchanged seventeen-win prefix absent')
    for i in (79,80):need(s.boundary.same_without_frame(events[i],old[i]),'eighteenth boundary changed')
    s.selection_context(raw)
    need([e['label'] for e in events[-2:]]==['returned','selected'] and events[-1]['battle']==21,'new stop after twenty one')
    base=events[0];offset=1;observed=0
    def ids(raw):return sorted(raw[n:n+8]+raw[n+32:n+34] for n in range(0,300,100))
    for session in range(1,8):
        pick=events[offset];offset+=1;v=p.owner(bytes.fromhex(pick['owner']))
        need(pick['label']=='selected' and pick['battle']==observed and pick['count']==6 and pick['marker']==pick['snapshot']==1,'rental scope')
        need(v['current']==v['best']==observed and v['phase']==1 and v['session']==session,'session owner')
        order=pick['order'];need(len(set(order))==3 and min(order)>=1,'selected distinct three')
        pool=bytes.fromhex(pick['party']);chosen=b''.join(pool[100*(i-1):100*i] for i in order)
        for local in range(3):
            rows=events[offset:offset+4];offset+=4
            need([e['label'] for e in rows]==['confirmation','action','outcome','settled'],'battle lifecycle')
            confirm,action,outcome,settled=rows
            need(all(e['battle']==observed for e in rows),'battle ordinal')
            party=bytes.fromhex(confirm['party'])[:300]
            need(party==bytes.fromhex(action['party'])[:300] and (party==chosen if local==0 else ids(party)==ids(chosen)),'selected identity')
            need(confirm['script']==p.LAUNCH[local] and not confirm['newbs'] and action['script']==p.LAUNCH[local]+43 and action['newbs'] and action['types']&0x04000000,'actual launch')
            for e in rows[:3]:
                v=p.owner(bytes.fromhex(e['owner']))
                need(v['current']==v['best']==observed and v['prepared']==observed+1 and v['settled']==observed and v['phase']==2,'armed owner')
                need(e['count']==3 and e['snapshot']==1 and e['bp']==(session-1)*9,'active rental')
            need(outcome['outcome']==1,'not a real WIN');observed+=1
            v=p.owner(bytes.fromhex(settled['owner']))
            need(v['current']==v['best']==v['prepared']==v['settled']==observed and v['phase']!=2 and v['outcome']==1 and settled['outcome']==1 and not settled['newbs'],'unique settlement')
            need(settled['bp']==(session if local==2 else session-1)*9,'settlement reward')
            if local==2:need(settled['party']==base['party'] and settled['count']==1 and not any(settled[k] for k in ('marker','snapshot','pending')),'settlement original600')
        back=events[offset];offset+=1;v=p.owner(bytes.fromhex(back['owner']))
        need(back['label']=='returned' and back['battle']==observed and v['current']==v['best']==observed and v['phase']==0,'batch return')
        need(back['party']==base['party'] and back['count']==1 and not any(back[k] for k in ('snapshot','marker','pending','newbs')) and back['bp']==session*9,'original600 and reward')
    need(offset==99 and observed==21,'observed count')
    for e in events:need(e['factory']==base['factory'] and e['save_counter']==2,'Factory or automatic Save changed')
    return dict(classification='CIRCUS_SELECTION_EIGHTEENTH_LAUNCH_21_WINS_SCOPED_ACCEPTED',
        actual_wins=21,actual_losses=0,completed_batches=7,bp=63,events=100,unchanged_prefix_events=79,
        original_party_restorations=7,original_party_bytes=600,original_count=1,selection_context=s.selection_context(raw),
        new_stop_battle=22,standard_save_fresh_continue=False,genuine_30_wins_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)


def configure():
    for k,v in dict(SELF=SELF,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,OUT=OUT,NEXT=NEXT).items():setattr(s,k,v)
    d,b=s.configure();d.FILES=tuple(dict.fromkeys((*d.FILES,*NEW,LEGACY,PRIOR,RAW)))
    d.c.FILES=d.FILES;return d,b


def record(value,phase):
    import pr16_resume as resume
    d,b=configure();r=b.rec;state=resume.load(ROOT,resume.STATE);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value));ref=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_rental_boundary']=loss['rental_boundary']=ref
    state['circus_selection_scoped_acceptance']=dict(path=REPORT,run_id=RUN,wins=21,bp=63,save_continue_verified=False)
    state['circus_continuous_followup']=dict(ref,target_wins=30);state['prior_actions_reconciled']=value['actions_reconciled']
    note='run35451609631/job105919631301: 新候補7a5676f9の18戦目起動と実21勝/63BP/7回原party600復元を確認。22戦目6体選出後に停止、通常Save/fresh Continueなし。元人数1/現在3の読取実測も一致。成功prefixを独立再実行せず、新停止のreadonlyだけを進める。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=WATCH;r.TASK='USER-20260920-CIRCUS-RENTAL-BOUNDARY-RUN'+os.environ['GITHUB_RUN_ID']
    r.checkpoint(state,loss,'18戦目修復と実21勝/63BP/元party600復帰は限定受入。22戦目の新境界診断='+str(value.get('diagnostic_complete',False))+'。通常Save/fresh Continue/真正30勝は未達。',NEXT,
        [REPORT,*d.FILES,*value.get('text_evidence',{})],phase,'原100events/6画面hash照合・affected host契約・原人数1..6の実Save migration結合を検証。ROM変更0/旧ARM再link0/受入単体再実行0。')


VISUAL={'artifact_id': 10585799962, 'archive': {'size': 1906330, 'sha256': 'f68be3bc79db832c6ba80518da15eb8f13732da24693f3af25fe9557a64741e2'}, 'screens': {'finish/native/circus-continuous-30-save-streak-82-action.ppm': {'size': 115215, 'sha256': 'b3abe7b7a33000f4a5107c58256f187421e9139ac6a719b6ab455209fbf0bd49'}, 'finish/native/circus-continuous-30-save-streak-83-outcome.ppm': {'size': 115215, 'sha256': '5fc17c9c6297b53824a5210a9ca2d4f813c56db64ac5b7e5b17e80b569a475b2'}, 'finish/native/circus-continuous-30-save-streak-98-settled.ppm': {'size': 115215, 'sha256': '7f17ef80aa8ce4114c0a20c811d5e96956f67c83002013d557fa061da0c30c3b'}, 'finish/native/circus-continuous-30-save-streak-99-returned.ppm': {'size': 115215, 'sha256': '12e58b297a3ff40920b3cf2b6f3e35a994ecc2ca7edd4fcb3c36d0405fb375aa'}, 'finish/native/circus-continuous-30-save-streak-100-selected.ppm': {'size': 115215, 'sha256': '361bb1c093df78ba55b63315f64d2b3ec9d45677a7e370d53405102033e57a7e'}, 'finish/native/circus-continuous-30-save-failure.ppm': {'size': 115215, 'sha256': 'e57cd46081f89328205c488f943d14adb155dab3ce1984a6a6ef4e87ffcd29cd'}}, 'observation_ja': '18戦目の戦闘起動/勝利画面、21勝目の3連勝9BP受取と元party復帰、22戦目の6体選出画面を目視。22戦目選出後は黒画面停止。Save/Continue画面はない。'}


def prepare():
    import pr16_resume as resume
    d,b=configure();r=b.rec;head=r.scope();state=resume.validate(ROOT)
    need(r.command('git','rev-parse','HEAD^')==BASE and set(r.command('git','diff','--name-only',BASE,head).splitlines())==set(NEW),'rental continuation source scope')
    need(not (ROOT/REPORT).exists(),'rental diagnostic already attempted')
    prior=resume.load(ROOT,PRIOR);need(prior['recording_run']==RUN and prior['native']['actual_new_processes']==1 and prior['native']['status']=='FAIL','original native differs')
    need(identity((ROOT/RAW).read_bytes())==prior['text_evidence'][RAW],'original text identity')
    run=r.api('actions/runs/'+str(RUN));need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='ce19f6c05dab61f35bd82332d158b913985f837a','original Actions status')
    artifact=r.api('actions/artifacts/'+str(VISUAL['artifact_id']));need(artifact['digest']=='sha256:'+VISUAL['archive']['sha256'] and artifact['workflow_run']['id']==RUN,'visual artifact provenance')
    archive=subprocess.check_output(['gh','api','repos/'+r.REPO+'/actions/artifacts/'+str(VISUAL['artifact_id'])+'/zip'],cwd=ROOT);need(identity(archive)==VISUAL['archive'],'visual archive identity')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name,meta in VISUAL['screens'].items():need(identity(z.read(name))==meta,'reviewed screen identity')
    before=(ROOT/LEGACY).read_bytes();need(identity(before)==state['source_bindings'][LEGACY],'legacy contract preimage')
    old='CircusDroughtInitializeLaunch(&c, w, DroughtOriginal, DroughtInitVars, DroughtStep);'
    new='CircusDroughtInitializeSelection(&c, READ8(0x02023F89u), w, DroughtOriginal, DroughtInitVars, DroughtStep);'
    need(before.decode().count(old)==1,'legacy assertion anchor');(ROOT/LEGACY).write_text(before.decode().replace(old,new))
    value=dict(schema_version=1,classification='CIRCUS_RENTAL_BOUNDARY_PREPARED',accepted_prefix=accepted_prefix((ROOT/RAW).read_bytes()),
        inherited_candidate=prior['candidate'],visual_review=VISUAL,legacy_contract=dict(path=LEGACY,before=identity(before),after=identity((ROOT/LEGACY).read_bytes())),
        actions_reconciled=[{k:run[k] for k in ('id','head_sha','status','conclusion')}],host_tests=r.tests([Path(TEST).name]),
        diagnostic_complete=False,native_lifecycle_accepted=False,standard_save_fresh_continue=False,genuine_30_wins_verified=False,
        independent_arm_links_replayed=0,accepted_native_cases_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    record(value,'PREPARED')


def reconstruct():
    from pr16_circus_streak import bounded_patch
    import pr16_streak_native as n
    d,b=configure();d.c.f.reconstruct();prior=json.loads((ROOT/PRIOR).read_bytes());recipe=deepcopy(prior['build'])
    raw=(n.INPUT/'candidate.gba').read_bytes();need(identity(raw)==recipe['parent'],'saved selection parent')
    for path,meta in recipe['source_bindings'].items():
        actual=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT) if path==LEGACY else (ROOT/path).read_bytes()
        need(identity(actual)==meta,'saved selection source '+path)
    new=bounded_patch(raw,recipe['patches']);need(identity(new)==recipe['candidate']==prior['candidate'],'saved selection candidate')
    for row in recipe['allocation']['allocations']:need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'allocation identity')
    recipe['source_bindings'].update({p:identity((ROOT/p).read_bytes()) for p in d.FILES});recipe['inherited_independent_arm_links']=recipe['independent_arm_links'];recipe['independent_arm_links']=0
    recipe['reconstruction_source']=dict(path=PRIOR,recording_run=RUN,rom_changed_bytes=0,legacy_contract_only_rebound=True)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'build.json').write_bytes(stable(recipe));(n.INPUT/'candidate.gba').write_bytes(new);(n.INPUT/'report.json').write_bytes(stable(recipe))


def diagnose(raw):
    import pr16_circus_continuous_probe as p
    events=p.parse(raw);old=p.parse((ROOT/RAW).read_bytes());need(events==old,'100 events changed before new boundary')
    prefix=b'CIRCUS_RENTAL_BOUNDARY ';rows=[p.strict(l[len(prefix):]) for l in raw.splitlines() if l.startswith(prefix)]
    need(len(rows)==21 and [r['elapsed'] for r in rows]==[1,*range(30,601,30)],'readonly bounded samples')
    for r in rows:
        need(r['current']==21 and r['phase']==1 and r['count']==6 and r['saved_count']==1 and r['marker']==r['snapshot']==1 and not r['newbs'],'rental phase changed')
        need(type(r['frame']) is int and r['frame']>events[-1]['frame'],'sampling boundary')
        need(len(bytes.fromhex(r['tasks']))==640 and len(bytes.fromhex(r['weather_raw']))==160,'readonly raw ABI')
    need(b'read-only rental boundary collected' in raw,'diagnostic endpoint absent')
    return dict(classification='CIRCUS_RENTAL_BOUNDARY_READONLY_COMPLETE',points=21,elapsed_frames=600,rows=rows,native_lifecycle_accepted=False)


def native():
    import pr16_circus_win_return_trace as trace
    d,b=configure();d.probe.SHA=json.loads((OUT/'build.json').read_bytes())['candidate']['sha256']
    def watch(text):return s.boundary.compose_boundary_watch(text,(ROOT/'tools/mgba_pr16_circus_selection_context.h').read_text(),trace.chained_watch)+'\n'+(ROOT/WATCH).read_text()
    src=inspect.getsource(d.c.native);old='(ROOT/b.fade.WATCH).read_text()';need(src.count(old)==1,'watch source boundary')
    ns=dict(d.c.__dict__);ns['rental_watch']=watch
    exec(compile(src.replace(old,'rental_watch('+old+')'),SELF+':readonly','exec'),ns)
    try:ns['native']()
    except ValueError as error:need(str(error)=='continuous lifecycle failed; inspect original','unexpected diagnostic failure '+str(error))
    else:raise ValueError('diagnostic unexpectedly completed full lifecycle')
    folder=OUT/'native';process=json.loads((folder/(d.probe.CASE+'.process.json')).read_bytes())
    need(process==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None) and not (folder/(d.probe.CASE+'.stdout')).read_bytes(),'not bounded readonly exit')
    result=diagnose((folder/(d.probe.CASE+'.stderr')).read_bytes());(OUT/'diagnostic.json').write_bytes(stable(result))
    print('READONLY_RENTAL_DIAGNOSTIC=PASS NATIVE_ACCEPTANCE=false')


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_RENTAL_BOUNDARY_OPEN'
    for path,key in [('build.json','build'),('native/report.json','native'),('diagnostic.json','diagnostic')]:
        p=OUT/path
        if p.exists():value[key]=json.loads(s.launch.inherited.relative_text(p.read_bytes(),ROOT))
    if 'diagnostic' in value:value['diagnostic_complete']=True;value['classification']=value['diagnostic']['classification']
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['text_evidence']={};value['evidence_transformations']={}
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.suffix not in {'.json','.txt','.stderr','.stdout'} or p.name.endswith('-receipt.json'):continue
        name='evidence/pr16_circus_rental_boundary/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
        value['evidence_transformations'][name]=s.launch.inherited.export(name,p.read_bytes(),value['text_evidence'])
    record(value,'RECORDED')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');a=sys.argv[1]
    if a=='pipeline':configure()[1].pipeline()
    elif a=='pack':configure()[0].c.f.pack()
    elif a in ('prepare','reconstruct','native','finish'):globals()[a]()
    else:raise SystemExit('unknown command')
