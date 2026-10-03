#!/usr/bin/env python3
"""実1勝後の未完第2戦を破棄し、正規Continueと保存再開で独立検証。"""
from pathlib import Path
import inspect
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_interruption.py'
SOURCE='tools/mgba_pr16_circus_interruption.c'
PROBE='scripts/pr16_circus_interruption_probe.py'
TEST='tests/test_pr16_circus_interruption.py'
WORKFLOW='.github/workflows/pr16-circus-interruption.yml'
REPORT='content/modernization/pr16_circus_interruption.json'
TASK='USER-20260919-CIRCUS-INTERRUPTION-SETUP'
BASE_SOURCE='tools/mgba_pr16_streak_native.c'
POLICY_SOURCE='tools/mgba_pr16_circus_sustain.h'
OUT=ROOT/'.local/pr16-circus-interruption'


def need(value,message):
    if not value:raise ValueError(message)


def replace(text,old,new):
    need(text.count(old)==1 and new not in text,'interruption adaptation anchor differs')
    return text.replace(old,new)


def adapt_runner(text):
    text=replace(text,"scope='CIRCUS_DEDICATED_STREAK_BATCH_SAVE_NATIVE'","scope='CIRCUS_SECOND_BATTLE_INTERRUPTION_NATIVE'")
    anchor="            generated['controller.c']=(ROOT/SOURCE).read_text()"
    return replace(text,anchor,"            generated['pr16_streak_base.c']=m.embed((ROOT/BASE_SOURCE).read_text(),'interrupt_unexecuted_batch')\n"+anchor)


def adapt_summary(text):
    return replace(text,'native_processes=1,fresh_cores=2,accepted_native_cases_replayed=0,',
        'native_processes=1,fresh_cores=3,accepted_native_cases_replayed=0,')


def configure():
    import pr16_circus_three_win as b
    b.SELF=SELF;b.TEST=TEST;b.WORKFLOW=WORKFLOW;b.HEADER=SOURCE;b.rec.TASK=TASK
    b.OUT.mkdir(parents=True,exist_ok=True)
    return b


def checkpoint(value,stop,next_step,phase,extra):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['interruption_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    (ROOT/REPORT).write_bytes(b.stable(value))
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=SOURCE
    r.checkpoint(state,loss,stop,next_step,[REPORT,SELF,SOURCE,PROBE,TEST,WORKFLOW,*extra],phase,
        value['classification']+'。第1実勝利は新規中断ケースの前提。受入済み3勝単体再実行0、同一3b候補/ARM再link0、host注入は初期fixtureまで。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'interruption case already started; inspect evidence before continuing')
    prior=resume.load(ROOT,b.REPORT)
    run=r.api('actions/runs/'+str(prior['recording_run']))
    need(run['status']=='completed','previous native Actions incomplete')
    for path,bound in prior['text_evidence'].items():
        need(b.identity((ROOT/path).read_bytes())==bound,'previous native evidence changed')
    # 新規中断ケースの前提は実1勝。未完の3勝ケースを成功扱いにしない。
    import pr16_streak_probe as old_probe
    b.fade.install_probe(old_probe);old_probe.SHA=b.SHA
    prefix=ROOT/('evidence/pr16_circus_three_win/'+str(prior['recording_run']))
    raw=(prefix/(old_probe.CASE+'.stdout')).read_bytes();err=(prefix/(old_probe.CASE+'.stderr')).read_bytes()
    process=json.loads((prefix/(old_probe.CASE+'.process.json')).read_bytes())
    proof=old_probe.validate(raw,err,process['returncode'],old_probe.CASE)
    need(proof['wins']>=1 and run['conclusion']==('success' if proof['wins']==3 else 'failure'),'native predecessor differs')
    value=dict(schema_version=1,classification='CIRCUS_INTERRUPTION_NATIVE_PENDING',
        prerequisite_run=prior['recording_run'],prerequisite_checkpoint=r.command('git','rev-parse','HEAD'),
        prerequisite_result=proof,prerequisite_original_conclusion=run['conclusion'],
        three_win_accepted=proof['wins']==3,candidate=prior['candidate'],
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        host_write_policy_ja='初期fixture終了後はkey/frame/readのみ。第2戦中のcore破棄時にsavestate/RAM/party/ownerをhost復元しない。')
    value['host_tests']=r.tests([Path(TEST).name]);OUT.mkdir(parents=True,exist_ok=True)
    checkpoint(value,'先行原本の実2勝と3勝未完はそのまま保持。新規ケースで実1勝後の第2戦を中断し、未完戦を加算しない復旧と再保存を検証する。',
        '第2戦中断後にcurrent0/best1/ABORT一度/原party600/Factory104/BP0を確認し、通常Saveと別core Continueを検証。完了後は未完の実3勝、真正30連勝と正規特性抑制へ。','START',[])


def native():
    import pr16_streak_native as n
    import pr16_circus_sustain as sustain
    import pr16_circus_interruption_probe as probe
    b=configure();r=json.loads((n.INPUT/'report.json').read_bytes())
    def verify(recipe):
        need(recipe==r and b.identity((n.INPUT/'candidate.gba').read_bytes())==r['candidate']
            and r['candidate']['sha256']==probe.SHA,'interruption fixed candidate differs')
        for path,bound in r['source_bindings'].items():
            need(b.identity((ROOT/path).read_bytes())==bound,'interruption fixed source differs: '+path)
    old_adapt=n.adapt
    def adapter(text):
        # 固定旧runnerのnamespaceへはBASE_SOURCEが渡らないためtracked literalを使用。
        text=adapt_runner(old_adapt(text))
        return text.replace('(ROOT/BASE_SOURCE).read_text()',"(ROOT/"+repr(BASE_SOURCE)+").read_text()")
    def policy(wx,br):
        return sustain.adapt_policy(n.policy(wx,br))+'\n'+(ROOT/POLICY_SOURCE).read_text()+'\n'+(ROOT/b.fade.WATCH).read_text()
    namespace=dict(n.__dict__)
    namespace.update(SELF=SELF,SOURCE=SOURCE,TEST=TEST,WORKFLOW=WORKFLOW,OUT=OUT,probe=probe,
        reconstruct=lambda:verify(r),verify_recipe=verify,adapt=adapter,policy=policy,
        EXTRA=n.EXTRA|{BASE_SOURCE,POLICY_SOURCE,PROBE,SELF,TEST,SOURCE,b.fade.WATCH,b.fade.SELF,
            'scripts/pr16_circus_three_win.py','scripts/pr16_circus_sustain.py'})
    exec(compile(adapt_summary(inspect.getsource(n.run)),SELF+':native','exec'),namespace)
    result=namespace['run']()
    need(result['status']=='PASS_CIRCUS_SCOPED_NATIVE','interruption incomplete; inspect saved raw evidence')


def finish():
    b=configure();value=json.loads((ROOT/REPORT).read_bytes());extra=[]
    value['classification']='CIRCUS_INTERRUPTION_DIAGNOSTIC_OPEN'
    report=OUT/'report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['classification']='CIRCUS_INTERRUPTION_RECOVERY_SAVE_CONTINUE_VERIFIED'
            value['scoped_result']=json.loads((OUT/'streak.json').read_bytes())
    prefix='evidence/pr16_circus_interruption/'+os.environ['GITHUB_RUN_ID']+'/'
    import pr16_circus_interruption_probe as probe
    value['text_evidence']={}
    for p in [report,OUT/(probe.CASE+'.stdout'),OUT/(probe.CASE+'.stderr'),OUT/(probe.CASE+'.process.json'),OUT/'streak.json',b.OUT/'reconstruction.json']:
        if not p.exists():continue
        raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext interruption evidence')
        name=prefix+p.name;(ROOT/name).parent.mkdir(parents=True,exist_ok=True);(ROOT/name).write_bytes(raw)
        value['text_evidence'][name]=b.identity(raw);extra.append(name)
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False
    passed=value['classification'].endswith('_VERIFIED')
    stop=('実1勝後の未完第2戦をcore破棄。正規Continueでcurrent0/best1/ABORT一度/原party600/Factory104不変/BP0を確認し、通常Saveと3つ目のcoreでも64byteを保持。'
        if passed else '第2戦中断の新規native原本を保存。未観測・失敗を受入にせず、原本の実停止から修復する。')
    checkpoint(value,stop,'完了済みの中断/敗北ケースを独立再実行せず、未完の実3勝・9BP、続いて真正30連勝と正規特性抑制へ進む。失敗時は中断reportから最初の不一致だけを修復。','RECORDED',extra)


def pack():
    b=configure();b.pack()
    target=ROOT/'.local/pr16-three-win-evidence'
    manifest=target/'members.json';rows=json.loads(manifest.read_bytes())
    paths=[p for p in OUT.rglob('*') if p.is_file() and p.suffix in ('.json','.txt','.stdout','.stderr','.ppm','.c','.h')]
    for p in paths:
        need(not p.is_symlink() and p.stat().st_size<4000000,'unsafe interruption evidence')
        name='pr16-circus-interruption/'+p.relative_to(OUT).as_posix()
        q=target/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());rows[name]=b.identity(p.read_bytes())
    for name in (SELF,SOURCE,PROBE,TEST,WORKFLOW,REPORT,BASE_SOURCE,POLICY_SOURCE,
                 'scripts/pr16_streak_native.py','scripts/pr16_circus_three_win.py','scripts/pr16_circus_sustain.py'):
        p=target/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
        rows['source/'+name]=b.identity(p.read_bytes())
    manifest.write_bytes(b.stable(rows))


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in {'prepare','reconstruct','pipeline','native','finish','pack'},'command required')
    action=sys.argv[1]
    if action in {'pipeline','reconstruct'}:getattr(configure(),action)()
    else:globals()[action]()
