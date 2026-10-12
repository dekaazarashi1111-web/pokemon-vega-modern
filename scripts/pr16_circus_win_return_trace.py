#!/usr/bin/env python3
"""入力不変で実17戦目勝利後を読む。診断完了とnative受入を厳密に分ける。"""
from pathlib import Path
import json
import inspect
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_taunt as previous
c,probe=previous.c,previous.probe
need,identity,stable=c.need,c.identity,c.stable
SELF='scripts/pr16_circus_win_return_trace.py'
HEADER='tools/mgba_pr16_circus_win_return_trace.h'
TEST='tests/test_pr16_circus_win_return_trace.py'
WORKFLOW='.github/workflows/pr16-circus-win-return-trace.yml'
REPORT='content/modernization/pr16_circus_win_return_trace.json'
OLD='content/modernization/pr16_circus_taunt.json'
RAW='evidence/pr16_circus_taunt/35430246002/native/'+probe.CASE
TASK='USER-20260919-CIRCUS-WIN-RETURN-TRACE-WATCHCALL'
OUT=ROOT/'.local/pr16-circus-win-return-trace'
COMPILE_FAILURE='evidence/pr16_circus_win_return_trace/35431032216/native/compile.stderr'
COMPILE_REPORT='evidence/pr16_circus_win_return_trace/35431032216/native/report.json'
FILES=(SELF,HEADER,TEST,WORKFLOW,COMPILE_FAILURE,COMPILE_REPORT,OLD,RAW+'.stdout',RAW+'.stderr',RAW+'.process.json',*previous.FILES,'scripts/pr16_circus_taunt.py')
NEXT='実17戦目勝利後のreadonly weather/script待ち原本を参照。敗北限定の既存FadeInFromBlack再開guardとの条件差を確認し、実WINかつ両待機task・正規script・armed Circus・有効ledgerに限定したruntime修復と独立2link/変更範囲台帳を進める。固定candidateでの同じ診断・旧単体nativeは繰り返さない。'
original_policy=previous.policy_text


def policy_text(base,headers):return original_policy(base,headers)+'\n'+(ROOT/HEADER).read_text()
def verify_prefix(events,raw):
    previous.verify_prefix(events,raw)
    old=probe.parse((ROOT/(RAW+'.stderr')).read_bytes())
    need(len(old)==80 and old[78]['label']=='outcome' and old[78]['battle']==16 and old[78]['outcome']==1,'seventeenth native WIN absent')
    need(events[:79]==old[:79],'observed seventeen battles changed before readonly trace')


def waiting_witness(rows):
    need(rows and len(rows)<49,'win wait trace missing/bounded')
    final=rows[-1]
    expected=dict(callback2=0x08055E75,script=0x09FF4D77,ready=0,phase=2,newbs=0,marker=2,snapshot=1,
        waiting=180,count=3,outcome=1,current=16,best=16)
    for k,v in expected.items():need(type(final[k]) is int and final[k]==v,'win wait '+k+' differs')
    need(final['types']&0x04000000,'not real Circus')
    raw=bytes.fromhex(final['tasks']);need(len(raw)==640,'task ABI')
    active=[int.from_bytes(raw[i:i+4],'little') for i in range(0,640,40) if raw[i+4]==1]
    need(active.count(0x0807951D)==1 and active.count(0x0807D465)==1,'weather/script waiters absent or ambiguous')
    first=next((r for r in rows if r['waiting']==30),None)
    need(first and final['frame']-first['frame']==150 and all(first[k]==final[k] for k in expected if k!='waiting'),'wait did not persist')
    return dict(real_winning_battles_observed=17,settled_wins_before_stop=16,completed_batches=5,bp=45,
        source_condition='WIN_WITH_WEATHER_AND_SCRIPT_WAITERS_READY_ZERO',first_frame=first['frame'],last_frame=final['frame'],
        consecutive_wait_frames=180,weather_waiter=0x0807951D,script_waiter=0x0807D465,
        diagnostic_complete=True,native_lifecycle_accepted=False,save_continue_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)


def configure():
    for k,v in dict(SELF=SELF,PROBE=previous.previous.previous.previous.PROBE,TEST=TEST,WORKFLOW=WORKFLOW,
        REPORT=REPORT,TASK=TASK,OUT=OUT,FILES=FILES,PREFIX=previous.previous.previous.previous.PREFIX,
        probe=probe,policy_text=policy_text,verify_prefix=verify_prefix).items():setattr(c,k,v)
    return c.configure()


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['win_return_trace']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_win_return_trace']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    note='run35430246002/job105863397028は15勝prefix不変・実16戦目WIN/settled16・17戦目WIN後black画面/phase2のまま停止。saved/reloadedなし、16勝保存成功や30勝へ昇格しない。actions failure原本を保持し、直後のreadonly traceだけを追加する。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    (ROOT/REPORT).write_bytes(stable(value));r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。診断は通常入力を変更せずbus読取のみ。候補310177不変・ARM link0・受入済み独立case再実行0。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    prior=resume.load(ROOT,REPORT);failed=resume.load(ROOT,COMPILE_REPORT);prior_run=r.api('actions/runs/35431032216')
    need(prior['recording_run']==35431032216 and prior['diagnostic_complete'] is False and failed['actual_new_processes']==0
        and prior_run['status']=='completed' and prior_run['conclusion']=='failure','compile-only preimage differs')
    need('error: "b_frame" redefined' in (ROOT/COMPILE_FAILURE).read_text(),'compile diagnostic absent')
    old=resume.load(ROOT,OLD);run=r.api('actions/runs/35430246002')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='9f0e5078ee54ff9d2df3f18682f0457b95296eff','original Actions differs')
    need(old['native']['status']=='FAIL' and old['native']['actual_new_processes']==1 and not old['native']['results'],'original terminal failure differs')
    for p,bound in old['text_evidence'].items():need(identity((ROOT/p).read_bytes())==bound,'trace preimage changed: '+p)
    events=probe.parse((ROOT/(RAW+'.stderr')).read_bytes());verify_prefix(events,(ROOT/c.PREFIX).read_bytes())
    need(events[-1]['label']=='timeout' and events[-1]['owner']==events[-2]['owner'] and not events[-1]['newbs'],'original win did not remain armed')
    value=dict(schema_version=1,classification='CIRCUS_WIN_RETURN_READONLY_PREPARED',candidate=old['candidate'],
        inherited_run=dict(run_id=35430246002,job_id=105863397028,original_conclusion='failure',saved=False),
        compile_failure_preserved=dict(run_id=35431032216,job_id=105865517281,native_processes=0,original_conclusion='failure',path=COMPILE_REPORT,compiler=COMPILE_FAILURE),
        host_tests=r.tests([Path(TEST).name]),accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        diagnostic_complete=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        original_visual_review=dict(artifact_id=10580033276,artifact_sha256='adb7dd1548ab76c4e18023d8a62148f11d9ad7666b072c0eb95ce89804631ec1',
            screens=['streak-74-action','streak-75-outcome','streak-76-settled','streak-78-action','streak-79-outcome','streak-80-timeout'],
            observation_ja='16戦目勝利/通常交換選択、17戦目勝利、その後の黒画面停止を目視。通常Save/Continueには到達していない。'))
    checkpoint(value,'PREPARED','Taunt先発で16戦目を突破。17戦目も実WINだがcallback08055e75/script09ff4d77/phase2で黒画面停止。guardは敗北のみを許可しているため、同じ待機task条件か読取専用に確認する。')


def reconstruct():configure();c.reconstruct()
def validate_trace():
    process=json.loads((OUT/'native'/ (probe.CASE+'.process.json')).read_bytes())
    need(process==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None),'not bounded diagnostic exit')
    raw=(OUT/'native'/(probe.CASE+'.stderr')).read_bytes()
    need(b'read-only win return witness collected' in raw and not (OUT/'native'/(probe.CASE+'.stdout')).read_bytes(),'not diagnostic-only result')
    events=probe.parse(raw);verify_prefix(events,(ROOT/c.PREFIX).read_bytes())
    need(len(events)==79,'new accepted lifecycle was unexpectedly executed')
    return waiting_witness([probe.strict(l[18:]) for l in raw.splitlines() if l.startswith(b'CIRCUS_WIN_RETURN ')])
def chained_native_source():
    source=inspect.getsource(c.native)
    old="(ROOT/b.fade.WATCH).read_text()"
    need(source.count(old)==1,'inherited native watcher boundary')
    return source.replace(old,"chained_watch((ROOT/b.fade.WATCH).read_text())")
def chained_watch(text):
    need(text.count('b_frame(c,keys);')==1 and text.count('#define b_frame fw_frame')==1,'inherited loss watcher boundary')
    return text.replace('b_frame(c,keys);','wr_frame(c,keys);')
def native():
    configure();ns=dict(c.__dict__);ns['chained_watch']=chained_watch
    exec(compile(chained_native_source(),SELF+':watch-call','exec'),ns)
    try:ns['native']()
    except ValueError as error:
        need(str(error)=='continuous lifecycle failed; inspect original','unexpected native failure: '+str(error))
    else:raise ValueError('readonly trace did not reach specified boundary')
    result=validate_trace();(OUT/'native/win-return-trace.json').write_bytes(stable(result))
    print('READONLY_DIAGNOSTIC=PASS NATIVE_ACCEPTANCE=false')


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_WIN_RETURN_READONLY_DIAGNOSTIC_OPEN'
    p=OUT/'native/win-return-trace.json'
    if p.exists():
        value['diagnostic']=validate_trace();value['diagnostic_complete']=True;value['classification']='CIRCUS_WIN_RETURN_READONLY_WAIT_CONFIRMED'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['text_evidence']={}
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name in ('report.json','events.json',probe.CASE+'.stdout',probe.CASE+'.stderr',probe.CASE+'.process.json','win-return-trace.json','reconstruction.json'):
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            name='evidence/pr16_circus_win_return_trace/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
            target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    checkpoint(value,'RECORDED','実17戦目WIN後の読取専用traceを記録。'+('ready0とweather/script両waiterが180frames残存。既存loss限定guardのWIN欠落を確認。' if value['diagnostic_complete'] else '期待した待機条件を確認できず未完。')+'native/save/30勝/正規特性抑制受入とは区別する。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action=='pack':configure();c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
