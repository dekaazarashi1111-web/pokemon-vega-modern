#!/usr/bin/env python3
"""受入済みcold-load候補を再linkせず、未完3勝/9BPの決着区間を検証する。"""
from pathlib import Path
import hashlib
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_finish.py'
HEADER='tools/mgba_pr16_circus_finish.h'
TEST='tests/test_pr16_circus_finish.py'
WORKFLOW='.github/workflows/pr16-circus-finish.yml'
REPORT='content/modernization/pr16_circus_finish.json'
COLD='content/modernization/pr16_circus_coldboot.json'
TASK='USER-20260919-CIRCUS-FINISH'
SHA='3101772a3b91fe0461f200bbd3faf19f01064132bd3d8db9b0fe8f747445b399'
POLICY='confirmed-damage-finish-v1'
OUT=ROOT/'.local/pr16-circus-finish'
FILES=(SELF,HEADER,TEST,WORKFLOW)
HEADERS=('tools/mgba_pr16_circus_sustain.h','tools/mgba_pr16_circus_effective.h','tools/mgba_pr16_circus_pivot.h')
NEXT='実3勝/9BPの今回原本を照合し、未達なら最初の不一致だけを修復。成功後は真正30連勝・正規特性抑制へ進む。cold-load中断/旧敗北/BP/Ringの受入単体は再実行しない。'


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def adapt(text):
    old='slot=wx_move_slot(c);'
    need(text.count(old)==1 and 'fw_move_slot' not in text,'finish selector anchor changed')
    return 'static unsigned fw_move_slot(struct mCore *c);\n'+text.replace(old,'slot=fw_move_slot(c);')


def require_three(result):
    for key,value in dict(wins=3,losses=0,battles=3,events=17).items():
        need(type(result.get(key)) is int and result[key]==value,'three real wins required: '+key)
    return result


def configure():
    import pr16_circus_three_win as b
    b.SELF=SELF;b.TEST=TEST;b.WORKFLOW=WORKFLOW;b.HEADER=HEADER;b.rec.TASK=TASK
    b.OUT.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    return b


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['finish_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    (ROOT/REPORT).write_bytes(stable(value))
    state['circus_finish_followup']=dict(path=REPORT,classification=value['classification'],candidate=value['candidate'])
    note='run35422605107/job105842901422の実1勝→第2戦中断/ABORT一度/best1/owner64/原party600/自動Save2+通常Save1/3coreは成功原本で継承。次の3勝ケースを中断の再実行に戻さない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。candidate310177固定、既存ARM再link0、受入単体再実行0。新host契約と原本を保持し、結果注入なし。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'finish attempt already recorded; inspect it instead of replaying')
    cold=resume.load(ROOT,COLD)
    need(cold['classification']=='CIRCUS_COLD_LOAD_INTERRUPTION_BEST1_SAVE_CONTINUE_VERIFIED'
        and cold['recording_run']==35422605107 and cold['build']['candidate']['sha256']==SHA,'cold-load acceptance differs')
    run=r.api('actions/runs/35422605107')
    need(run['status']=='completed' and run['conclusion']=='success','cold-load Actions not successful')
    for path,bound in cold['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'cold raw changed')
    old=resume.load(ROOT,b.REPORT)
    need(old['recording_run']==35421235529 and old['classification']=='CIRCUS_THREE_WIN_DIAGNOSTIC_OPEN','failed three-win predecessor differs')
    prior=r.api('actions/runs/35421235529');need(prior['status']=='completed' and prior['conclusion']=='failure','three-win failure not final')
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'failed raw changed')
    value=dict(schema_version=1,classification='CIRCUS_FINISH_INPUT_PREPARED',candidate=cold['build']['candidate'],
        input_policy_id=POLICY,accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        cold_load_inherited=dict(run_id=35422605107,job_id=105842901422,original_conclusion='success',path=COLD),
        failed_three_win_inherited=dict(run_id=35421235529,original_conclusion='failure',wins=2,losses=1),
        actions_reconciled=[{k:run[k] for k in ('id','head_sha','status','conclusion')},
                            {k:prior[k] for k in ('id','head_sha','status','conclusion')}],
        host_tests=r.tests([Path(TEST).name]),physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        changed_scope_ja='ROM/fixture/最初の2戦は不変。第3戦のみ無効な攻撃だけのNormalへの先発交換と未確認SeedのProtectを避け、実タイプ/PP/毒/HPで決着と回復を選ぶ。')
    checkpoint(value,'PREPARED','最新cold-load中断復旧はActions成功として照合・継承。実2勝後の敗北原本はfailureのまま保持し、未完3勝/9BPだけの入力方策を追加。')


def reconstruct():
    b=configure();b.reconstruct()
    import pr16_streak_native as n
    from pr16_circus_streak import bounded_patch
    recipe=json.loads((ROOT/COLD).read_bytes())['build']
    raw=(n.INPUT/'candidate.gba').read_bytes();need(identity(raw)==recipe['parent'],'cold-load parent reconstruction differs')
    for path,bound in recipe['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'cold source changed: '+path)
    new=bounded_patch(raw,recipe['patches'])
    need(identity(new)==recipe['candidate'] and recipe['candidate']['sha256']==SHA,'cold-load candidate differs')
    for row in recipe['allocation']['allocations']:
        need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'allocation changed')
    (n.INPUT/'candidate.gba').write_bytes(new);(n.INPUT/'report.json').write_bytes(stable(recipe))
    (OUT/'reconstruction.json').write_bytes(stable(dict(candidate=recipe['candidate'],rom_changes=0,arm_links_replayed=0,
        inherited_build_run=35422605107,all_allocations_verified=True)))


def native():
    import pr16_streak_native as n
    b=configure();recipe=json.loads((n.INPUT/'report.json').read_bytes())
    def verify(value):
        need(value==recipe and identity((n.INPUT/'candidate.gba').read_bytes())==recipe['candidate']
            and recipe['candidate']['sha256']==SHA,'finish candidate identity')
        for path,bound in recipe['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'finish source binding: '+path)
    n.reconstruct=lambda:verify(recipe);n.verify_recipe=verify;n.probe.SHA=SHA;b.fade.install_probe(n.probe)
    old=n.probe.validate;n.probe.validate=lambda raw,err,code,case:require_three(old(raw,err,code,case))
    policy=n.policy
    n.policy=lambda wx,br:adapt(policy(wx,br))+'\n'+'\n'.join((ROOT/p).read_text() for p in HEADERS)+'\n'+(ROOT/HEADER).read_text()+'\n'+(ROOT/b.fade.WATCH).read_text()
    n.SELF=SELF;n.TEST=TEST;n.WORKFLOW=WORKFLOW;n.OUT=OUT/'native'
    n.EXTRA=n.EXTRA|set(FILES)|set(HEADERS)|{'tools/mgba_pr16_circus_matchup.h','tools/mgba_pr16_circus_menu_identity.h',b.fade.WATCH,b.fade.SELF}
    result=n.run();need(result['status']=='PASS_CIRCUS_SCOPED_NATIVE','three-win finish incomplete; inspect original')


def finish():
    b=configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_FINISH_DIAGNOSTIC_OPEN'
    report=OUT/'native/report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            require_three(value['native']['results'][0]['result'])
            value['classification']='CIRCUS_THREE_WIN_COLD_CANDIDATE_SAVE_CONTINUE_VERIFIED'
            value['scoped_result']=json.loads((OUT/'native/streak.json').read_bytes())
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False;value['text_evidence']={}
    prefix='evidence/pr16_circus_finish/'+os.environ['GITHUB_RUN_ID']+'/'
    for name in ('report.json','circus-streak-batch-save.stdout','circus-streak-batch-save.stderr','circus-streak-batch-save.process.json','streak.json'):
        p=OUT/'native'/name
        if p.exists():
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            target=ROOT/(prefix+name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);value['text_evidence'][prefix+name]=identity(raw)
    p=OUT/'reconstruction.json'
    if p.exists():
        raw=p.read_bytes();target=ROOT/(prefix+p.name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);value['text_evidence'][prefix+p.name]=identity(raw)
    passed=value['classification'].endswith('_VERIFIED')
    checkpoint(value,'RECORDED','cold-load候補で実3勝・第2第3launch個体保持・owner64・原party600・9BP・通常Save/別coreを検証。真正30連勝/抑制/P08は未完。'
        if passed else '未完3勝の新入力原本を保存。候補と失敗を受入に読み替えず、今回停止した最初の条件から修復する。中断復旧は再実行していない。')


def pack():
    import pr16_resume as resume
    target=ROOT/'.local/pr16-circus-finish-evidence';members={}
    def add(name,raw):
        need(len(raw)<4*1024*1024,'oversize evidence');p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);members[name]=identity(raw)
    for p in OUT.rglob('*'):
        if p.is_file() and p.suffix in {'.json','.txt','.stdout','.stderr','.c','.h','.ppm'}:
            need(not p.is_symlink(),'unsafe evidence');add('finish/'+p.relative_to(OUT).as_posix(),p.read_bytes())
    for name in (*FILES,*HEADERS,'tools/mgba_pr16_circus_matchup.h','tools/mgba_pr16_circus_menu_identity.h',
        'scripts/pr16_streak_native.py','scripts/pr16_streak_probe.py',REPORT,COLD,resume.STATE,resume.DOC,resume.BACKLOG,
        'design/run_log.md','design/version_log.md'):
        add('source/'+name,(ROOT/name).read_bytes())
    (target/'members.json').write_bytes(stable(members))


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action in {'prepare','reconstruct','native','finish','pack'}:globals()[action]()
    else:raise SystemExit('unknown command')
