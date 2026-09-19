#!/usr/bin/env python3
"""第3戦の通常交代を追加し、先発を温存する。ROM/RAM注入はしない。"""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_pivot.py'
HEADER='tools/mgba_pr16_circus_pivot.h'
TEST='tests/test_pr16_circus_pivot.py'
FIXTURE='tests/fixtures/circus_pivot_policy_fixture.c'
WORKFLOW='.github/workflows/pr16-circus-pivot.yml'
POLICY='pivot-v1'
TASK='USER-20260919-CIRCUS-PIVOT-V1'


def adapt_policy(text):
    old='slot=wx_move_slot(c);'
    if text.count(old)!=1 or 'pv_move_slot' in text:
        raise ValueError('battle input policy anchor differs')
    return 'static unsigned pv_move_slot(struct mCore *c);\n'+text.replace(old,'slot=pv_move_slot(c);')


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
    value.update(classification='CIRCUS_PIVOT_INPUT_POLICY_PENDING',input_policy_id=POLICY,
        current_attempt=dict(run_id=int(os.environ['GITHUB_RUN_ID']),trigger_head=os.environ['GITHUB_SHA']),
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        source_change_review_ja='同一ROM/同一チーム/勝敗validatorを維持。第3戦でNormal相手への初回だけ通常PARTY入力でToxic/Shadow Ball持ちに交代。前2勝の入力は不変。入力数は技選択と任意交代を分離して記録。')
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
    value['diagnosis']=dict(previous_run=old['recording_run'],
        reason_ja='無効技修復で第3戦の先頭Normalを倒したが、先に2体を失い次のWaterで敗北。第3戦開始時の通常交代で残り2体を温存する。')
    b.checkpoint(value,'run35418424222は無効Shadow BallをToxicへ切替えて相手を倒したが、次の相手で敗北。第3戦だけ通常PARTY入力による1回の任意交代を追加し、実3勝へ進む。','PIVOT-START',[SELF,TEST,FIXTURE,HEADER,WORKFLOW])


def native():
    import pr16_streak_native as n
    b=configure();original=n.policy
    n.policy=lambda wx,br:adapt_policy(original(wx,br))+'\n'+(ROOT/'tools/mgba_pr16_circus_sustain.h').read_text()+'\n'+(ROOT/'tools/mgba_pr16_circus_effective.h').read_text()+'\n'
    n.EXTRA=n.EXTRA|{FIXTURE,SELF,TEST,HEADER,'scripts/pr16_circus_three_win.py','tools/mgba_pr16_circus_sustain.h','scripts/pr16_circus_sustain.py','tools/mgba_pr16_circus_effective.h','scripts/pr16_circus_effective.py'}
    validate=n.probe.validate
    n.probe.validate=lambda raw,stderr,code,case:validate_pivot(validate(raw,stderr,code,case),stderr,n.OUT)
    try:b.native()
    finally:n.policy=original;n.probe.validate=validate


def pivot_events(stderr):
    prefix='CIRCUS_PIVOT '
    rows=[json.loads(line[len(prefix):]) for line in stderr.decode().splitlines() if line.startswith(prefix)]
    if len(rows)!=2 or [r['label'] for r in rows]!=['begin','done']:
        raise ValueError('exactly one completed voluntary pivot required')
    first,last=rows
    keys={'label','frame','from','target','pid','ot','species'}
    if any(set(r)!=keys for r in rows):raise ValueError('pivot event keys differ')
    if not (type(first['frame']) is int and type(last['frame']) is int and 0<first['frame']<last['frame']):
        raise ValueError('pivot frame chain differs')
    for key in ('from','target','pid','ot','species'):
        if type(first[key]) is not int or type(last[key]) is not int or first[key]!=last[key]:raise ValueError('pivot identity differs')
    if not (0<=first['from']<3 and 0<=first['target']<3 and first['from']!=first['target'] and 0<first['species']<=65535 and 0<=first['pid']<=0xFFFFFFFF and 0<=first['ot']<=0xFFFFFFFF):
        raise ValueError('pivot party slots differ')
    return dict(voluntary_switches=1,events=rows,
        turns_semantics='native result.turns counts move commands; voluntary switch is recorded separately',
        switches_semantics='native result.switches/forced_identity_checks count forced replacements')


def validate_pivot(row,stderr,out):
    proof=pivot_events(stderr)
    events=[json.loads(line[14:]) for line in stderr.decode().splitlines() if line.startswith('CIRCUS_STREAK ')]
    action=next(r for r in events if r['label']=='action' and r['battle']==2)
    outcome=next(r for r in events if r['label']=='outcome' and r['battle']==2)
    if not (action['frame']<=proof['events'][0]['frame']<proof['events'][1]['frame']<outcome['frame']):
        raise ValueError('pivot occurred outside third battle')
    if row['switches']!=row['forced_identity_checks']:raise ValueError('forced replacement accounting differs')
    (out/'pivot-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
    return row


def finish():
    b=configure();original=b.checkpoint
    def checkpoint(value,stop,phase,extra):
        value['input_policy_id']=POLICY
        p=ROOT/'.local/pr16-streak-native/pivot-proof.json'
        if p.exists():
            name='evidence/pr16_circus_three_win/'+os.environ['GITHUB_RUN_ID']+'/pivot-proof.json'
            (ROOT/name).parent.mkdir(parents=True,exist_ok=True);(ROOT/name).write_bytes(p.read_bytes())
            value['pivot']=json.loads(p.read_bytes());value['text_evidence'][name]=b.identity(p.read_bytes());extra=[*extra,name]
        original(value,stop,phase,[*extra,FIXTURE,SELF,TEST,HEADER,WORKFLOW])
    b.checkpoint=checkpoint
    b.finish()


def pack():
    b=configure();b.pack()
    target=ROOT/'.local/pr16-three-win-evidence'
    manifest=target/'members.json';rows=json.loads(manifest.read_bytes())
    for name in (FIXTURE,'scripts/pr16_circus_three_win.py','scripts/pr16_streak_native.py',
                 'scripts/pr16_streak_probe.py','tools/mgba_pr16_streak_native.c','tools/mgba_pr16_circus_sustain.h','scripts/pr16_circus_sustain.py','tools/mgba_pr16_circus_effective.h','scripts/pr16_circus_effective.py',b.rec.SELF):
        path=target/'source'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
        rows['source/'+name]=b.identity(path.read_bytes())
    manifest.write_bytes(b.stable(rows))


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in {'prepare','native','finish','pack','pipeline','reconstruct'}:
        raise SystemExit('command required')
    action=sys.argv[1]
    if action in {'pipeline','reconstruct'}:getattr(configure(),action)()
    else:globals()[action]()
