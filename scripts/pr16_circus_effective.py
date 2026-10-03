#!/usr/bin/env python3
"""2勝1敗の原本から、低HP相手への無効技連打だけを修復する。"""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_effective.py'
HEADER='tools/mgba_pr16_circus_effective.h'
TEST='tests/test_pr16_circus_effective.py'
FIXTURE='tests/fixtures/circus_effective_policy_fixture.c'
WORKFLOW='.github/workflows/pr16-circus-effective.yml'
POLICY='effective-v1'
TASK='USER-20260919-CIRCUS-EFFECTIVE-V1'


def adapt_policy(text):
    old='slot=wx_move_slot(c);'
    if text.count(old)!=1 or 'ef_move_slot' in text:
        raise ValueError('battle input policy anchor differs')
    return 'static unsigned ef_move_slot(struct mCore *c);\n'+text.replace(old,'slot=ef_move_slot(c);')


def prior_allowed(value,run):
    if value.get('classification')!='CIRCUS_THREE_WIN_DIAGNOSTIC_OPEN':
        raise ValueError('only an unaccepted failed attempt may continue')
    if value.get('input_policy_id')==POLICY:
        raise ValueError('same policy already executed; inspect original instead')
    if run.get('id')!=value.get('recording_run') or run.get('status')!='completed' or run.get('conclusion')!='failure':
        raise ValueError('previous Actions must be a completed failure')


def configure():
    import pr16_circus_three_win as base
    base.SELF=SELF;base.HEADER=HEADER;base.TEST=TEST;base.WORKFLOW=WORKFLOW
    base.rec.TASK=TASK
    return base


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();state=resume.validate(ROOT)
    old_raw=(ROOT/b.REPORT).read_bytes();old=json.loads(old_raw)
    prior=r.api('actions/runs/'+str(old['recording_run']));prior_allowed(old,prior)
    # 古い失敗はGitの正確なcommitと原stdout/stderr/reportで保持。上書きして成功へ変えない。
    for name,bound in old['text_evidence'].items():r.need(r.identity((ROOT/name).read_bytes())==bound,'previous evidence differs: '+name)
    previous=dict(run_id=old['recording_run'],original_conclusion=prior['conclusion'],
        checkpoint_head=r.command('git','rev-parse','HEAD'),checkpoint=dict(path=b.REPORT,**r.identity(old_raw)),
        input_policy_id=old.get('input_policy_id','damage-speed-v1'),text_evidence=old['text_evidence'],
        native_status=old['native']['status'],candidate=old['candidate'])
    value={k:v for k,v in old.items() if k not in ('native','text_evidence','host_tests','scoped_result','recording_run','visual_review_completed')}
    value['previous_attempts']=[*old.get('previous_attempts',[]),previous]
    value.update(classification='CIRCUS_EFFECTIVE_INPUT_POLICY_PENDING',input_policy_id=POLICY,
        current_attempt=dict(run_id=int(os.environ['GITHUB_RUN_ID']),trigger_head=os.environ['GITHUB_SHA']),
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        source_change_review_ja='ROM/fixture/チーム選択/受入validatorは不変。run35418010512の低HP Normalへの無効Shadow Ball7回を、使用可能なToxicへ切り替える。非無効技・状態技の選択は変えない。')
    runs=r.api('actions/runs?branch='+r.BRANCH+'&per_page=20')['workflow_runs']
    value['actions_reconciled']=[{k:row[k] for k in ('id','name','head_sha','status','conclusion')} for row in runs]
    value['host_tests']=r.tests([Path(TEST).name])
    b.OUT.mkdir(parents=True,exist_ok=True)
    # 原本の一般勝敗validatorは2勝1敗/17eventsの継続・復元を検証する。
    # 3勝validatorのfailureは維持し、成功2戦を独立再実行しない。
    import pr16_streak_probe as probe
    b.fade.install_probe(probe);probe.SHA=b.SHA
    evidence='evidence/pr16_circus_three_win/'+str(old['recording_run'])+'/'
    raw=(ROOT/(evidence+probe.CASE+'.stdout')).read_bytes()
    err=(ROOT/(evidence+probe.CASE+'.stderr')).read_bytes()
    process=json.loads((ROOT/(evidence+probe.CASE+'.process.json')).read_bytes())
    partial=probe.validate(raw,err,process['returncode'],probe.CASE)
    r.need(partial['wins']==2 and partial['losses']==1,'not the observed two-win failure')
    value['previous_partial_verified']=dict(run_id=old['recording_run'],result=partial,
        classification='TWO_WINS_AND_TWO_CONTINUATION_LAUNCHES_NOT_THREE_WIN_ACCEPTANCE',
        original_conclusion='failure',native_processes_replayed=0)
    value['diagnosis']=dict(frame=50972,enemy_hp=34,enemy_maxhp=171,enemy_types=[0,0],
        ineffective_move=247,ineffective_turns=7,available_status_move=92,
        reason_ja='HP1/4閾値がToxicを除外し、score0のShadow Ballを7回選択。選択方策のみを修復。')
    b.checkpoint(value,'run35418010512は実2勝・第2/第3launch個体保持・17events・Save/fresh Continueを検証したが最終戦敗北。低HPかつ無効技だけの場面を修復し、3勝の未完区間へ進む。','EFFECTIVE-START',[SELF,TEST,FIXTURE,HEADER,WORKFLOW])


def native():
    import pr16_streak_native as n
    b=configure();original=n.policy
    n.policy=lambda wx,br:adapt_policy(original(wx,br))+'\n'+(ROOT/'tools/mgba_pr16_circus_sustain.h').read_text()+'\n'
    n.EXTRA=n.EXTRA|{FIXTURE,SELF,TEST,HEADER,'scripts/pr16_circus_three_win.py','tools/mgba_pr16_circus_sustain.h','scripts/pr16_circus_sustain.py'}
    try:b.native()
    finally:n.policy=original


def finish():
    b=configure();original=b.checkpoint
    def checkpoint(value,stop,phase,extra):
        value['input_policy_id']=POLICY
        original(value,stop,phase,[*extra,FIXTURE,SELF,TEST,HEADER,WORKFLOW])
    b.checkpoint=checkpoint
    b.finish()


def pack():
    b=configure();b.pack()
    target=ROOT/'.local/pr16-three-win-evidence'
    manifest=target/'members.json';rows=json.loads(manifest.read_bytes())
    for name in (FIXTURE,'scripts/pr16_circus_three_win.py','scripts/pr16_streak_native.py',
                 'scripts/pr16_streak_probe.py','tools/mgba_pr16_streak_native.c','tools/mgba_pr16_circus_sustain.h','scripts/pr16_circus_sustain.py',b.rec.SELF):
        path=target/'source'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
        rows['source/'+name]=b.identity(path.read_bytes())
    manifest.write_bytes(b.stable(rows))


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in {'prepare','native','finish','pack','pipeline','reconstruct'}:
        raise SystemExit('command required')
    action=sys.argv[1]
    if action in {'pipeline','reconstruct'}:getattr(configure(),action)()
    else:globals()[action]()
