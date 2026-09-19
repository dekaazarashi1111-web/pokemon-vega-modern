#!/usr/bin/env python3
"""失敗原本を保持し、同一ROMの耐久/状態技方策だけで未受入3勝へ進む。"""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_sustain.py'
HEADER='tools/mgba_pr16_circus_sustain.h'
TEST='tests/test_pr16_circus_sustain.py'
FIXTURE='tests/fixtures/circus_sustain_policy_fixture.c'
WORKFLOW='.github/workflows/pr16-circus-sustain.yml'
POLICY='sustain-v1'
TASK='USER-20260919-CIRCUS-SUSTAIN-V1'


def adapt_policy(text):
    old='slot=wx_move_slot(c);'
    if text.count(old)!=1 or 'su_move_slot' in text:
        raise ValueError('battle input policy anchor differs')
    return 'static unsigned su_move_slot(struct mCore *c);\n'+text.replace(old,'slot=su_move_slot(c);')


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
    value.update(classification='CIRCUS_SUSTAIN_INPUT_POLICY_PENDING',input_policy_id=POLICY,
        current_attempt=dict(run_id=int(os.environ['GITHUB_RUN_ID']),trigger_head=os.environ['GITHUB_SHA']),
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        source_change_review_ja='ROM/fixture/受入validatorは不変。新controllerは耐久とタイプ重複、実PP/状態によるToxic/Seed/Confuse/Protect/Calm Mindを考慮。状態技試行を効果着弾の証拠にしない。')
    runs=r.api('actions/runs?branch='+r.BRANCH+'&per_page=20')['workflow_runs']
    value['actions_reconciled']=[{k:row[k] for k in ('id','name','head_sha','status','conclusion')} for row in runs]
    value['host_tests']=r.tests([Path(TEST).name])
    b.OUT.mkdir(parents=True,exist_ok=True)
    b.checkpoint(value,'前回run35415727687の0勝1敗をfailure原本として保持。耐久・技タイプ重複と実状態技を使う別入力方策を28条件で検証し、同一3b候補の未受入3勝へ進む。','SUSTAIN-START',[SELF,TEST,FIXTURE,HEADER,WORKFLOW])


def native():
    import pr16_streak_native as n
    b=configure();original=n.policy
    n.policy=lambda wx,br:adapt_policy(original(wx,br))
    n.EXTRA=n.EXTRA|{FIXTURE,SELF,TEST,HEADER,'scripts/pr16_circus_three_win.py'}
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
                 'scripts/pr16_streak_probe.py','tools/mgba_pr16_streak_native.c',b.rec.SELF):
        path=target/'source'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
        rows['source/'+name]=b.identity(path.read_bytes())
    manifest.write_bytes(b.stable(rows))


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in {'prepare','native','finish','pack','pipeline','reconstruct'}:
        raise SystemExit('command required')
    action=sys.argv[1]
    if action in {'pipeline','reconstruct'}:getattr(configure(),action)()
    else:globals()[action]()
