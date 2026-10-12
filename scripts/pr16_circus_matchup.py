#!/usr/bin/env python3
"""過去の失敗を保持し、実PPフィードバックと通常交代で未完3勝を進める。"""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_matchup.py'
HEADER='tools/mgba_pr16_circus_matchup.h'
TEST='tests/test_pr16_circus_matchup.py'
FIXTURE='tests/fixtures/circus_matchup_fixture.c'
WORKFLOW='.github/workflows/pr16-circus-matchup.yml'
POLICY='matchup-feedback-v1'
TASK='USER-20260919-CIRCUS-MATCHUP-V1'
PIVOT_SOURCE='scripts/pr16_circus_pivot.py'
HEADERS=('tools/mgba_pr16_circus_sustain.h','tools/mgba_pr16_circus_effective.h','tools/mgba_pr16_circus_pivot.h')


def need(value,message):
    if not value:raise ValueError(message)


def parent():
    import pr16_circus_pivot as p
    for name in ('SELF','HEADER','TEST','FIXTURE','WORKFLOW','POLICY','TASK'):setattr(p,name,globals()[name])
    return p


def adapt_policy(text):
    old='slot=wx_move_slot(c);'
    need(text.count(old)==1 and 'mt_move_slot' not in text,'matchup input anchor differs')
    return 'static unsigned mt_move_slot(struct mCore *c);\n'+text.replace(old,'slot=mt_move_slot(c);')


def events(stderr):
    from pr16_circus_interruption_probe import strict
    rows=[strict(line[15:]) for line in stderr.splitlines() if line.startswith(b'CIRCUS_MATCHUP ')]
    need(0<len(rows)<=12 and len(rows)%2==0,'bounded matchup switches required')
    keys={'label','frame','from','target','pid','ot','species','type'}
    previous=0
    for i in range(0,len(rows),2):
        first,last=rows[i:i+2]
        need(set(first)==set(last)==keys and first['label']=='begin' and last['label']=='done','matchup pair schema')
        for row in (first,last):
            need(all(type(row[k]) is int for k in keys-{'label'}),'matchup integer types')
            need(previous<row['frame'] and 0<=row['from']<3 and 0<=row['target']<3
                 and row['from']!=row['target'] and 0<row['species']<=65535
                 and 0<=row['pid']<=0xffffffff and 0<=row['ot']<=0xffffffff and row['type'] in (10,12),'matchup event bounds')
            previous=row['frame']
        need(all(first[k]==last[k] for k in keys-{'label','frame'}),'matchup selected individual mismatch')
    lifecycle=[strict(line[14:]) for line in stderr.splitlines() if line.startswith(b'CIRCUS_STREAK ')]
    action=next(e for e in lifecycle if e['label']=='action' and e['battle']==2)
    outcome=next(e for e in lifecycle if e['label']=='outcome' and e['battle']==2)
    need(action['frame']<=rows[0]['frame']<rows[-1]['frame']<outcome['frame'],'matchup outside third battle')
    return dict(voluntary_matchup_switches=len(rows)//2,events=rows,
        accounting_ja='stdoutのswitches/forced_identity_checksは強制交代。最初のpivot1回とmatchup任意交代は個別原本で数える。')


INTERRUPTION='scripts/pr16_circus_interruption.py'
INTERRUPTION_TASK='USER-20260919-CIRCUS-INTERRUPTION-SETUP'


def repair_interruption_text(text):
    old="TASK='USER-20260919-CIRCUS-INTERRUPTION'"
    new="TASK='"+INTERRUPTION_TASK+"'"
    anchor='    return b\n\n\ndef checkpoint('
    inserted='    b.OUT.mkdir(parents=True,exist_ok=True)\n'+anchor
    need(text.count(old)==1 and text.count(anchor)==1 and new not in text and inserted not in text,
        'interruption setup repair preimage differs')
    return text.replace(old,new).replace(anchor,inserted)


def repair_interruption():
    import pr16_resume as resume
    import pr16_circus_interruption as ip
    import pr16_circus_loss_followup as r
    r.scope();state=resume.validate(ROOT)
    raw=(ROOT/ip.REPORT).read_bytes();value=json.loads(raw)
    need(value['recording_run']==35419491330 and value['classification']=='CIRCUS_INTERRUPTION_DIAGNOSTIC_OPEN'
         and 'native' not in value and value['text_evidence']=={},'not the unexecuted setup failure')
    run=r.api('actions/runs/35419491330')
    need(run['status']=='completed' and run['conclusion']=='failure','setup Actions not a completed failure')
    source=ROOT/INTERRUPTION
    need(r.identity(source.read_bytes())==state['source_bindings'][INTERRUPTION],'interruption source preimage changed')
    before=r.identity(source.read_bytes());source.write_text(repair_interruption_text(source.read_text()))
    diagnostic=dict(schema_version=1,run_id=35419491330,job_id=105834335146,original_conclusion='failure',
        native_processes_executed=0,artifact_id=10577695453,
        artifact_sha256='c59f90fa96befa9deda814ea30e0c1fcd3755aa092deb6ea0bd8d4595c3dd6e0',
        excerpt_source='GitHub Actions job log 105834335146 at 2026-09-19T03:47:09.9134225Z',
        original_log_excerpt='bash: line 3: .local/pr16-circus-three-win/toolchain.log: No such file or directory',
        checkpoint_head=r.command('git','rev-parse','HEAD'),checkpoint=r.identity(raw),
        repaired_path=INTERRUPTION,source_before=before,source_after=r.identity(source.read_bytes()),
        scope_ja='setup出力先mkdir欠落のみ修復。前回はcompiler/候補復元/nativeの実行前に停止。native検証条件・入力controller・ROMは変更しない。')
    path='evidence/pr16_circus_interruption/35419491330/setup-diagnostic.json'
    (ROOT/path).parent.mkdir(parents=True,exist_ok=True);(ROOT/path).write_bytes(r.stable(diagnostic))
    value['previous_attempts']=[diagnostic]
    value['classification']='CIRCUS_INTERRUPTION_SETUP_REPAIRED_NATIVE_PENDING'
    value['host_tests_after_setup_repair']=r.tests(['test_pr16_circus_interruption.py',Path(TEST).name])
    (ROOT/ip.REPORT).write_bytes(r.stable(value))
    loss=resume.load(ROOT,r.REPORT)
    loss['interruption_followup']=dict(path=ip.REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    r.SELF=SELF;r.HEADER=ip.SOURCE;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.TASK=INTERRUPTION_TASK
    r.checkpoint(state,loss,'中断run35419491330はsetup出力先欠落でnative未実行。原本と失敗を保持し、mkdirのみ修復して未観測の中断復旧を実行する。',
        '新規中断ケースの原本を保存後、同じ候補を再構築せず第3戦入力方策を検証する。完了条件未達は残件のまま保持。',
        [INTERRUPTION,ip.REPORT,ip.SOURCE,ip.PROBE,SELF,HEADER,TEST,FIXTURE,WORKFLOW,path,PIVOT_SOURCE,*HEADERS],
        'REPAIRED','14中断hostテストと100条件を含む新方策テスト、scope/private差分guard、元ソースhashを照合。既受入native0再実行。')


def prepare():
    p=parent();b=p.configure();original=b.checkpoint
    def checkpoint(value,stop,phase,extra):
        value['classification']='CIRCUS_MATCHUP_INPUT_POLICY_PENDING'
        value['source_change_review_ja']='同一候補/同一チーム/第1第2戦の入力は不変。第3戦のみToxicの実PP消費を最大4回で管理、SeedのPP未消費を未実行扱い、草対炎/炎対水/双方毒の低HP通常交代、対水GigaDrainを追加。'
        value['diagnosis']=dict(previous_run=value['previous_partial_verified']['run_id'],
            reason_ja='先行pivotは通常交代と個体一致を実証したが、未実行/ProtectされたToxicを打切り、草が炎に倒された。結果/能力や連勝は変更せず入力選択を修復。')
        path=ROOT/'content/modernization/pr16_circus_interruption.json'
        if path.exists():
            v=json.loads(path.read_bytes());value['interruption_checkpoint_inherited']=dict(path=str(path.relative_to(ROOT)),classification=v['classification'],run_id=v['recording_run'],native_replays=0)
        original(value,'通常交代は原本で確認済み。実PPのフィードバックと相性を読取専用で組み合わせ、未完の実3勝/9BPへ進む。中断ケースは原本を継承して独立再実行しない。',phase,[*extra,PIVOT_SOURCE,*HEADERS])
    b.checkpoint=checkpoint;p.prepare()


def native():
    import pr16_streak_native as n
    p=parent();b=p.configure();old=n.policy
    n.policy=lambda wx,br:adapt_policy(old(wx,br))+'\n'+'\n'.join((ROOT/name).read_text() for name in HEADERS)+'\n'
    n.EXTRA=n.EXTRA|{SELF,HEADER,TEST,FIXTURE,PIVOT_SOURCE,*HEADERS,
        'scripts/pr16_circus_interruption_probe.py','scripts/pr16_circus_three_win.py'}
    original=n.probe.validate
    def validate(raw,stderr,code,case):
        result=original(raw,stderr,code,case)
        p.validate_pivot(result,stderr,n.OUT)
        (n.OUT/'matchup-proof.json').write_bytes(b.stable(events(stderr)))
        return result
    n.probe.validate=validate
    try:b.native()
    finally:n.policy=old;n.probe.validate=original


def finish():
    p=parent();b=p.configure();original=b.checkpoint
    def checkpoint(value,stop,phase,extra):
        path=ROOT/'.local/pr16-streak-native/matchup-proof.json'
        if path.exists():
            name='evidence/pr16_circus_three_win/'+os.environ['GITHUB_RUN_ID']+'/matchup-proof.json'
            (ROOT/name).parent.mkdir(parents=True,exist_ok=True);(ROOT/name).write_bytes(path.read_bytes())
            value['matchup']=json.loads(path.read_bytes());value['text_evidence'][name]=b.identity(path.read_bytes());extra=[*extra,name]
        original(value,stop,phase,[*extra,PIVOT_SOURCE,*HEADERS,'scripts/pr16_circus_interruption_probe.py'])
    b.checkpoint=checkpoint;p.finish()


def pack():
    p=parent();b=p.configure();p.pack()
    target=ROOT/'.local/pr16-three-win-evidence';manifest=target/'members.json';rows=json.loads(manifest.read_bytes())
    for name in (PIVOT_SOURCE,*HEADERS,'scripts/pr16_circus_interruption_probe.py'):
        q=target/'source'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/name).read_bytes());rows['source/'+name]=b.identity(q.read_bytes())
    manifest.write_bytes(b.stable(rows))


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in {'repair-interruption','prepare','native','finish','pack','pipeline','reconstruct'},'command required')
    action=sys.argv[1]
    if action in {'pipeline','reconstruct'}:getattr(parent().configure(),action)()
    else:globals()[action.replace('-','_')]()
