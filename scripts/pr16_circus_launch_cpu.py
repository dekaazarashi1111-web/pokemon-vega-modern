#!/usr/bin/env python3
"""17勝目復帰を原本から確定し、18戦目の未完launchだけCPU読取で切り分ける。"""
from pathlib import Path
import io
import json
import os
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_drought_calls as inherited
OLD=inherited.REPORT
SELF='scripts/pr16_circus_launch_cpu.py'
TEST='tests/test_pr16_circus_launch_cpu.py'
WATCH='tools/mgba_pr16_circus_launch_cpu.h'
WORKFLOW='.github/workflows/pr16-circus-launch-cpu.yml'
REPORT='content/modernization/pr16_circus_launch_cpu.json'
TASK='USER-20260919-CIRCUS-LAUNCH-CPU'
OUT=ROOT/'.local/pr16-circus-launch-cpu'
RUN=35435801505
JOB=105878112448
ARTIFACT=10581864965
ARCHIVE=dict(size=1781827,sha256='f54d9cce0b2be27e13a75ca77c7604c0847a3bf85aa07fa160ff249e80414340')
SHA='98b9eea437e63fbbaf81b361cf36a11436b785f6946c60e9a6a51e19fe559aac'
RAW='evidence/pr16_circus_drought_calls/35435801505/native/circus-continuous-30-save.stderr'
need,identity,stable=inherited.need,inherited.identity,inherited.stable
NEXT='17勝後Drought復帰はnative完了cursor32/32・17勝記録・18戦目確認まで原本で確認済み。18戦目launchの新CPU原本から限定修復し、続く実戦・原party600/owner64・通常Save/fresh Continue・真正30勝へ進む。旧17勝診断・独立2link・受入単体は再実行しない。'


def parse(raw,prefix):
    return [json.loads(l[len(prefix):]) for l in raw.splitlines() if l.startswith(prefix)]


def prior_boundary(raw):
    rows=parse(raw,b'CIRCUS_CONTINUOUS ')
    need(len(rows)==81 and [r['label'] for r in rows[-3:]]==['outcome','settled','confirmation'],'17th return original events')
    need(rows[-3]['battle']==16 and rows[-3]['outcome']==1 and rows[-2]['battle']==16,'17th WIN/settled')
    owner=bytes.fromhex(rows[-2]['owner'])
    need(len(owner)==64 and int.from_bytes(owner[32:34],'little')==17 and owner[36]==1,'17th owner settlement')
    need(rows[-1]['battle']==17 and rows[-1]['script']==0x09FF4DAD and rows[-1]['outcome']==0,'18th confirmation')
    need(not any(r['label'] in ('saved','reloaded') for r in rows),'prior lifecycle unexpectedly completed')
    return dict(real_wins=17,settled_wins=17,next_confirmation=18,save_continue_verified=False)


def cpu_rows(raw):
    rows=parse(raw,b'CIRCUS_LAUNCH_CPU ')
    need([r['elapsed'] for r in rows]==[1,*range(30,601,30)],'launch CPU sample boundaries')
    for r in rows:
        need(type(r['current']) is int and r['current']==17 and r['outcome']==0,'launch owner/outcome')
        need(0x03000000<=r['sp']<=0x03008000 and r['types']&0x04000000,'launch stack/type')
        for key,size in [('weather',64),('drought',32),('tasks',640)]:
            need(len(bytes.fromhex(r[key]))==size,'launch raw '+key)
    return rows


def configure():
    for k in ('SELF','TEST','WORKFLOW','REPORT','TASK','OUT','NEXT'):
        setattr(inherited,k,globals()[k])
    d,b=inherited.configure()
    d.FILES=tuple(dict.fromkeys((*d.FILES,WATCH,OLD,RAW)))
    c=d.c;c.FILES=d.FILES
    def policy(base,headers):
        text=d.policy_text(base,headers)
        need(text.count('static void wr_frame(')==1,'Drought observer anchor')
        return text.replace('static void wr_frame(','static void dw_frame(')+'\n'+(ROOT/WATCH).read_text()
    c.policy_text=policy
    def prefix(events,raw):
        d.verify_prefix(events,raw)
        prior=parse((ROOT/RAW).read_bytes(),b'CIRCUS_CONTINUOUS ')
        need(events[:81]==prior,'18th confirmation prefix changed')
    c.verify_prefix=prefix
    return d,b


def record(value,phase,stop):
    import pr16_resume as resume
    d,b=configure();r=b.rec;state=resume.load(ROOT,resume.STATE);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value))
    ref=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_launch_followup']=loss['launch_followup']=ref
    state['circus_continuous_followup']=dict(ref,target_wins=30)
    state['prior_actions_reconciled']=value['actions_reconciled']
    note='run35435801505/job105878112448: candidate98b9eea4の独立2link/rollback成功。17勝後Drought native state5/complete1/cursor32/32、settled17と18戦目確認は観測。次launch黒画面でfailure、Save未到達。記録/両ログ/差分guard成功。17勝保存受入や30勝へ昇格せず、18戦目の未完部分だけ診断。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=WATCH;r.TASK=TASK
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*d.FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。ROM不変98b9eea4・ARM再link0・通常入力不変の読取専用CPU・受入独立case再実行0。診断成功とnative lifecycle成功を区別。')


def prepare():
    import pr16_resume as resume
    d,b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'diagnostic already exists; reconcile instead of repeat')
    old=resume.load(ROOT,OLD);need(old['candidate']['sha256']==SHA and old['recording_run']==RUN,'prior candidate/run')
    for p,bound in old['text_evidence'].items():need(identity((ROOT/p).read_bytes())==bound,'prior evidence drift')
    run=r.api('actions/runs/'+str(RUN));artifact=r.api('actions/artifacts/'+str(ARTIFACT))
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='31130b4c04effdb6beedd071a0111dbc4552d941','original failure')
    need(artifact['workflow_run']['id']==RUN and artifact['digest']=='sha256:'+ARCHIVE['sha256'],'artifact identity')
    archive=subprocess.check_output(['gh','api','repos/'+r.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    need(identity(archive)==ARCHIVE,'archive identity')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names=['finish/native/circus-continuous-30-save-'+p+'.ppm' for p in ('streak-79-outcome','streak-80-settled','streak-81-confirmation','failure')]
        screens={p:identity(z.read(p)) for p in names}
    raw=(ROOT/RAW).read_bytes();boundary=prior_boundary(raw);witness=d.return_witness(raw)
    value=dict(schema_version=1,classification='CIRCUS_18TH_LAUNCH_CPU_PREPARED',candidate=old['candidate'],
        actions_reconciled=[{k:run[k] for k in ('id','head_sha','status','conclusion')}],
        inherited_run=dict(id=RUN,job=JOB,artifact=ARTIFACT,archive=ARCHIVE),
        seventeenth_return=dict(**boundary,native_witness=witness,visual_review_completed=True,
            screens=screens,observation_ja='勝利画面→通常交換質問→18戦目選出確認までは復帰。その後は黒画面。保存画面なし。'),
        host_tests=r.tests([Path(TEST).name]),diagnostic_complete=False,independent_arm_links_replayed=0,
        accepted_native_cases_replayed=0,save_continue_verified=False,genuine_30_wins_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    record(value,'PREPARED','17勝後の修復自体はnative完了・勝数記録・画面復帰を原本照合。次の18戦目launch停止を読取CPUで限定診断する。候補は再linkせず固定再構成。')


def reconstruct():
    d,b=configure();d.c.f.reconstruct()
    import pr16_streak_native as n
    from pr16_circus_streak import bounded_patch
    recipe=json.loads((ROOT/OLD).read_bytes())['build'];raw=(n.INPUT/'candidate.gba').read_bytes()
    need(identity(raw)==recipe['parent'],'fixed parent reconstruction')
    new=bounded_patch(raw,recipe['patches']);need(identity(new)==recipe['candidate'] and recipe['candidate']['sha256']==SHA,'fixed candidate reconstruction')
    for p,bound in recipe['source_bindings'].items():need(identity((ROOT/p).read_bytes())==bound,'fixed source drift: '+p)
    recipe['source_bindings'].update({p:identity((ROOT/p).read_bytes()) for p in d.FILES})
    (n.INPUT/'candidate.gba').write_bytes(new);(n.INPUT/'report.json').write_bytes(stable(recipe))
    (OUT/'reconstruction.json').write_bytes(stable(dict(candidate=identity(new),rom_changes=0,arm_links_replayed=0)))


def native():
    d,b=configure();d.probe.SHA=SHA
    import pr16_circus_win_return_trace as trace
    ns=dict(d.c.__dict__);ns['chained_watch']=trace.chained_watch
    exec(compile(trace.chained_native_source(),SELF+':read-only','exec'),ns)
    try:ns['native']()
    except ValueError as error:need(str(error)=='continuous lifecycle failed; inspect original','unexpected CPU run failure: '+str(error))
    else:raise ValueError('diagnostic exit was not reached')
    p=OUT/'native';process=json.loads((p/(d.probe.CASE+'.process.json')).read_bytes())
    need(process==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None),'not bounded CPU exit')
    raw=(p/(d.probe.CASE+'.stderr')).read_bytes()
    need(b'bounded launch CPU diagnostic complete' in raw and not (p/(d.probe.CASE+'.stdout')).read_bytes(),'not CPU diagnostic')
    events=d.probe.parse(raw);d.c.verify_prefix(events,(ROOT/d.c.PREFIX).read_bytes());need(len(events)==81,'unexpected extra lifecycle')
    (OUT/'cpu-rows.json').write_bytes(stable(cpu_rows(raw)))
    print('READONLY_LAUNCH_CPU=PASS NATIVE_ACCEPTANCE=false')


def finish():
    d,b=configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_18TH_LAUNCH_CPU_OPEN'
    if (OUT/'cpu-rows.json').exists():
        value['cpu_rows']=cpu_rows((OUT/'native'/(d.probe.CASE+'.stderr')).read_bytes())
        value['diagnostic_complete']=True;value['classification']='CIRCUS_18TH_LAUNCH_CPU_READONLY_COMPLETE'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['text_evidence']={};value['evidence_transformations']={}
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.suffix not in {'.json','.txt','.stderr','.stdout'} or p.name.endswith('-receipt.json'):continue
        name='evidence/pr16_circus_launch_cpu/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
        value['evidence_transformations'][name]=inherited.export(name,p.read_bytes(),value['text_evidence'])
    record(value,'RECORDED','18戦目未完launchの600frame/21点CPU・weather・tasksの読取原本を保存。診断完了='+str(value['diagnostic_complete'])+'。ROM/ARM link変更なし、通常Save/fresh Continueは未受入。')


if __name__=='__main__':
    need(len(sys.argv)==2,'one command required');action=sys.argv[1]
    if action=='pipeline':configure()[1].pipeline()
    elif action=='pack':configure()[0].c.f.pack()
    elif action in ('prepare','reconstruct','native','finish'):globals()[action]()
    else:raise SystemExit('unknown command')
