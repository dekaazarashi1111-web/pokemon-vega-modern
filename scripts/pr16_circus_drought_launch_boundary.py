#!/usr/bin/env python3
"""18戦目選出後の最初の新停止だけをreadonlyで固定する。"""
from pathlib import Path
import hashlib
import inspect
import json
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_drought_launch_boundary.py'
TEST='tests/test_pr16_circus_drought_launch_boundary.py'
HEADER='tools/mgba_pr16_circus_drought_launch_boundary.h'
WORKFLOW='.github/workflows/pr16-circus-drought-launch-boundary.yml'
REPORT='content/modernization/pr16_circus_drought_launch_boundary.json'
PRIOR='content/modernization/pr16_circus_drought_launch.json'
RAW='evidence/pr16_circus_drought_launch/35437062974/native/circus-continuous-30-save.stderr'
TASK='USER-20260919-CIRCUS-DROUGHT-LAUNCH-BOUNDARY'
OUT=ROOT/'.local/pr16-circus-drought-launch-boundary'
PRIOR_RUN=35437062974
LATEST_NONRESULT_RUN=35437460976
FAILED_RUN=35438144902
FAILED_JOB=105884235962
FAILED_ARTIFACT=10582383197
FAILED_HEAD='3fa90fab346223742c2f66dff6756e7f0d560078'
FAILED_DIGEST='sha256:07e2825828a5831ec1d9cdfc3a38d0b03eef3594d84eee00af9e82e3f619d1a5'
FAILED_REPORT='evidence/pr16_circus_drought_launch_boundary/35438144902/native/report.json'
NEXT='境界traceのcomplete/state/cursorとscript/task遷移に基づき、18戦目だけの最小修復を追加する。17勝prefix・受入済み単体・旧CPU診断・旧独立2linkは再実行せず、修復候補で18戦目launch以降の実勝敗・原party600/owner64・通常Save/fresh Continueへ進む。'


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def strict(raw):
    def pairs(items):
        value={}
        for k,v in items:
            need(k not in value,'duplicate JSON key');value[k]=v
        return value
    def bad(_):raise ValueError('nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)


def append_watch(text,header):
    marker='#define b_frame lb_frame'
    need(marker not in text and header.count(marker)==1,'launch boundary watcher duplicate')
    need(text.count('#define b_frame fw_frame')==1,'inherited frame watcher boundary')
    need(header.count('b_frame(c,keys);')==1 and header.count('#undef b_frame')==1,'readonly watcher call chain')
    return text+'\n'+header


def compose_boundary_watch(fade_text,header,chain):
    chained=chain(fade_text)
    need(chained!=fade_text and chained.count('wr_frame(c,keys);')==1,'fade watcher was not chained after Drought watcher')
    return append_watch(chained,header)


def validate_retry_failure(previous,failed,run,artifact):
    need(previous['classification']=='CIRCUS_DROUGHT_LAUNCH_BOUNDARY_OPEN'
        and previous['recording_run']==FAILED_RUN and previous['diagnostic_complete'] is False,
        'previous boundary setup result differs')
    need(failed['status']=='FAIL' and failed['actual_new_processes']==0
        and failed['successful_fresh_cores']==0 and failed['results']==[],
        'boundary setup failure unexpectedly ran native')
    need(failed['failures']==[{'stage':'setup-or-execution','error':'inherited frame watcher boundary'}],
        'boundary setup failure reason differs')
    need(run['id']==FAILED_RUN and run['head_sha']==FAILED_HEAD and run['status']=='completed'
        and run['conclusion']=='failure','boundary setup Actions result differs')
    need(artifact['id']==FAILED_ARTIFACT and artifact['workflow_run']['id']==FAILED_RUN
        and artifact['digest']==FAILED_DIGEST and artifact['expired'] is False,
        'boundary setup artifact differs')
    return dict(run_id=FAILED_RUN,job_id=FAILED_JOB,artifact_id=FAILED_ARTIFACT,
        head_sha=FAILED_HEAD,artifact_digest=FAILED_DIGEST,original_conclusion='failure',
        native_processes=0,accepted_native_cases_replayed=0,
        reason_ja='Drought watcherより前へ境界watcherを挿入し、fade連結後にだけ存在するb_frame=fw_frameを要求してsetup停止。ゲームは起動していない。')


def continuous_events(raw):
    prefix=b'CIRCUS_CONTINUOUS '
    return [strict(line[len(prefix):]) for line in raw.splitlines() if line.startswith(prefix)]


def boundary_rows(raw):
    prefix=b'CIRCUS_LAUNCH_BOUNDARY '
    return [strict(line[len(prefix):]) for line in raw.splitlines() if line.startswith(prefix)]


def same_without_frame(a,b):
    return {k:v for k,v in a.items() if k!='frame'}=={k:v for k,v in b.items() if k!='frame'}


def analyze_boundary(rows):
    need(type(rows) is list and 3<=len(rows)<=64,'launch boundary row bound')
    keys={'frame','keys','callback2','script','newbs','weather_state','complete','index','offset','weather','next_weather',
        'ready','brightness','phase','outcome','current','best','count','types','field_wait','tasks','weather_raw','owner'}
    for i,row in enumerate(rows):
        need(type(row) is dict and set(row)==keys,'launch boundary row schema')
        for k in keys-{'tasks','weather_raw','owner'}:need(type(row[k]) is int and 0<=row[k]<=0xffffffff,'launch boundary integer '+k)
        need(i==0 or row['frame']>rows[i-1]['frame'],'launch boundary frame order')
        for k,size in (('tasks',640),('weather_raw',160),('owner',64)):
            text=row[k];need(type(text) is str and len(text)==size*2 and all(c in '0123456789abcdef' for c in text),'launch boundary bytes '+k)
        need(row['current']==row['best']==17 and row['phase']==2 and row['count']==3 and row['outcome']==0,'launch owner/context changed')
        need(row['types']&0x04000000,'launch row is not Circus')
    chooser=next((r for r in rows if r['callback2']==0x0811F3A9 and r['script']==0x09FF4DAD and not r['newbs']),None)
    need(chooser is not None,'18th chooser boundary absent')
    field=next((r for r in rows if r['callback2']==0x08055E75 and not r['script'] and not r['newbs']),None)
    need(field is not None,'field drop boundary absent')
    final=rows[-1];need(final['callback2']==0x08055E75 and not final['script'] and not final['newbs'] and final['field_wait']==180,'field drop did not persist')
    need(field['frame']>=chooser['frame'],'field drop precedes chooser')
    completed=final['complete']==1 and final['weather_state']==5 and final['index']==32 and final['offset']==32
    return dict(
        classification='CIRCUS_DROUGHT_LAUNCH_COMPLETED_THEN_FIELD_DROP' if completed else 'CIRCUS_DROUGHT_LAUNCH_RETURNED_INCOMPLETE',
        rows=len(rows),chooser_frame=chooser['frame'],field_drop_frame=field['frame'],persistent_field_frames=180,
        transition_frames=field['frame']-chooser['frame'],weather_completed=completed,weather_state=final['weather_state'],
        complete=final['complete'],index=final['index'],offset=final['offset'],brightness=final['brightness'],ready=final['ready'],
        active_tasks=sum(1 for i in range(0,1280,80) if int(final['tasks'][i+8:i+10],16)==1),
        script_before=chooser['script'],script_after=final['script'],callback_before=chooser['callback2'],callback_after=final['callback2'],
        reason_ja=('Drought初期化は完了cursorまで到達した後、選出継続scriptが消えてfield callbackへ落ちた。次は完了後のscript/task継続だけを修復する。'
            if completed else 'Drought launch初期化が未完のまま有限loopを返し、選出継続scriptが消えてfield callbackへ落ちた。次は初期化完了条件だけを修復する。'),
        diagnostic_complete=True,native_lifecycle_accepted=False,standard_save_fresh_continue=False,genuine_30_wins_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)


def configure():
    import pr16_circus_drought_launch as base
    for key,value in dict(SELF=SELF,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=TASK,OUT=OUT,NEXT=NEXT).items():setattr(base,key,value)
    d,b=base.configure()
    d.FILES=tuple(dict.fromkeys((*d.FILES,SELF,TEST,HEADER,WORKFLOW,PRIOR,RAW)))
    d.c.FILES=d.FILES
    return base,d,b


def record(value,phase,stop,next_step=NEXT):
    import pr16_resume as resume
    base,d,b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value))
    ref=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_drought_launch_boundary']=loss['drought_launch_boundary']=ref
    state['circus_continuous_followup']=dict(ref,target_wins=30)
    state['prior_actions_reconciled']=value['actions_reconciled']
    note='run35437062974/job105881419750は17勝prefixと18戦目確認まで到達後、action/Saveなしでfield callback・script0へ落ちた。新候補の最初の停止として保持し、同じ18,000frame失敗待ちは再実行しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    setup_note='run35438144902/job105884235962はwatcher連結順のsetup失敗でnative process 0。ゲーム側結果ではなく、同じ前段挿入を再実行しない。fade連結後への境界watcher追加だけを再試行する。'
    if setup_note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,setup_note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER;r.TASK=TASK
    r.checkpoint(state,loss,stop,next_step,[REPORT,*d.FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。現候補1processの17勝不可避prefixのみ、入力不変のreadonly境界trace。受入済み単体0、ARM link追加0、ROM/save証跡0。')


def prepare():
    import pr16_resume as resume
    base,d,b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    previous=resume.load(ROOT,REPORT)
    need(FAILED_REPORT in previous.get('text_evidence',{}),'previous setup evidence reference absent')
    failed_raw=(ROOT/FAILED_REPORT).read_bytes()
    need(identity(failed_raw)==previous['text_evidence'][FAILED_REPORT],'previous setup native report drift')
    failed=json.loads(failed_raw)
    failed_run=r.api('actions/runs/'+str(FAILED_RUN));artifact=r.api('actions/artifacts/'+str(FAILED_ARTIFACT))
    setup_failure=validate_retry_failure(previous,failed,failed_run,artifact)
    prior=resume.load(ROOT,PRIOR);need(prior['recording_run']==PRIOR_RUN and prior['classification']=='CIRCUS_DROUGHT_LAUNCH_NATIVE_OPEN','prior launch result differs')
    need(prior['native']['status']=='FAIL' and prior['native']['actual_new_processes']==1 and not prior['launch_native_verified'],'prior launch was not the open failure')
    need(identity((ROOT/RAW).read_bytes())==prior['text_evidence'][RAW],'prior native stderr drift')
    run=r.api('actions/runs/'+str(PRIOR_RUN));nonresult=r.api('actions/runs/'+str(LATEST_NONRESULT_RUN))
    need(run['status']=='completed' and run['conclusion']=='failure','prior Actions result differs')
    need(nonresult['status']=='completed' and nonresult['conclusion']=='action_required','latest non-result Actions classification differs')
    value=dict(schema_version=1,classification='CIRCUS_DROUGHT_LAUNCH_BOUNDARY_RETRY_PREPARED',candidate=prior['candidate'],
        inherited_failure=dict(run_id=PRIOR_RUN,job_id=105881419750,artifact_id=10583081417,events=81,settled_wins=17,
            reached_eighteenth_confirmation=True,action_reached=False,standard_save_reached=False,original_conclusion='failure'),
        diagnostic_setup_failure=setup_failure,
        actions_reconciled=[{k:run[k] for k in ('id','head_sha','status','conclusion')},{k:nonresult[k] for k in ('id','head_sha','status','conclusion')},
            {k:failed_run[k] for k in ('id','head_sha','status','conclusion')}],
        scope_ja='同じ候補を1processだけ再構築し、不可避17勝prefix後の18戦目chooser→field落下を180frameで停止して読む。前回setup失敗と旧CPU600frame診断、受入済み単体、旧独立2linkは実行しない。',
        host_tests=r.tests([Path(TEST).name,'test_pr16_circus_drought_launch.py']),accepted_native_cases_replayed=0,
        unavoidable_prefix_battles=17,independent_arm_links_replayed=0,diagnostic_complete=False,native_lifecycle_accepted=False,
        standard_save_fresh_continue=False,genuine_30_wins_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        text_evidence=dict(previous.get('text_evidence',{})),evidence_transformations=dict(previous.get('evidence_transformations',{})))
    record(value,'PREPARED','run35438144902はwatcher連結順のsetup失敗/native0として固定。fade watcherをDrought watcherへ連結した後だけ境界watcherを追加し、同じゲーム境界を初回採取する。')


def reconstruct():
    base,d,b=configure();base.reconstruct()


def validate_trace():
    process=json.loads((OUT/'native/circus-continuous-30-save.process.json').read_bytes())
    need(process==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None),'launch boundary was not bounded diagnostic exit')
    raw=(OUT/'native/circus-continuous-30-save.stderr').read_bytes();need(b'read-only launch boundary witness collected' in raw,'launch boundary endpoint absent')
    need(not (OUT/'native/circus-continuous-30-save.stdout').read_bytes(),'diagnostic unexpectedly produced acceptance stdout')
    events=continuous_events(raw);old=continuous_events((ROOT/RAW).read_bytes())
    need(len(events)==len(old)==81,'launch boundary event count')
    need(events[:79]==old[:79],'accepted seventeen-win prefix changed')
    need(same_without_frame(events[79],old[79]) and same_without_frame(events[80],old[80]),'settled17/eighteenth confirmation semantics changed')
    need(events[-1]['label']=='confirmation' and events[-1]['battle']==17 and not any(e['label']=='action' and e['battle']==17 for e in events),'diagnostic crossed launch acceptance')
    result=analyze_boundary(boundary_rows(raw))
    report=json.loads((OUT/'native/report.json').read_bytes())
    need(report['status']=='FAIL' and report['actual_new_processes']==1 and report['successful_fresh_cores']==0,'diagnostic native report differs')
    result.update(native_report_status=report['status'],continuous_events=81,native_processes=1,accepted_prefix_events_identical=79,
        settled_and_confirmation_semantics_preserved=True,old_accepted_cases_replayed=0)
    return result


def native():
    base,d,b=configure();recipe=json.loads((OUT/'build.json').read_bytes());d.probe.SHA=recipe['candidate']['sha256']
    header=(ROOT/HEADER).read_text()
    import pr16_circus_win_return_trace as trace
    def boundary_watch(text):return compose_boundary_watch(text,header,trace.chained_watch)
    source=inspect.getsource(d.c.native);old="(ROOT/b.fade.WATCH).read_text()"
    need(source.count(old)==1,'inherited native watcher source boundary')
    source=source.replace(old,"boundary_watch((ROOT/b.fade.WATCH).read_text())")
    ns=dict(d.c.__dict__);ns['boundary_watch']=boundary_watch
    exec(compile(source,SELF+':launch-boundary','exec'),ns)
    try:ns['native']()
    except ValueError as error:need(str(error)=='continuous lifecycle failed; inspect original','unexpected boundary native failure: '+str(error))
    else:raise ValueError('readonly launch trace crossed the expected boundary')
    result=validate_trace();(OUT/'native/launch-boundary-trace.json').write_bytes(stable(result))
    print('READONLY_LAUNCH_BOUNDARY=PASS NATIVE_ACCEPTANCE=false')


def finish():
    value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_DROUGHT_LAUNCH_BOUNDARY_OPEN'
    trace=OUT/'native/launch-boundary-trace.json'
    if trace.exists():
        value['diagnostic']=validate_trace();value['classification']=value['diagnostic']['classification'];value['diagnostic_complete']=True
    value['recording_run']=int(os.environ['GITHUB_RUN_ID'])
    value.setdefault('text_evidence',{});value.setdefault('evidence_transformations',{})
    base,d,b=configure()
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.suffix not in {'.json','.txt','.stderr','.stdout'} or p.name.endswith('-receipt.json'):continue
        raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'text evidence only')
        name='evidence/pr16_circus_drought_launch_boundary/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
        value['evidence_transformations'][name]=base.inherited.export(name,raw,value['text_evidence'])
    next_step=NEXT
    if value.get('diagnostic_complete'):
        next_step=value['diagnostic']['reason_ja']+' 17勝prefixを固定したまま18戦目launch/以降の実勝敗・原party600/owner64・通常Save/fresh Continueを次候補で検証する。'
    record(value,'RECORDED','18戦目chooserからfield callback/script0へ落ちるreadonly境界を保存。weather完了='+str(value.get('diagnostic',{}).get('weather_completed'))+'。native/Save/30勝受入には昇格しない。',next_step)


def main():
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='prepare':prepare()
    elif action=='reconstruct':reconstruct()
    elif action=='native':native()
    elif action=='finish':finish()
    elif action=='pipeline':configure()[2].pipeline()
    elif action=='pack':configure()[1].c.f.pack()
    else:raise SystemExit('unknown command')

if __name__=='__main__':main()
