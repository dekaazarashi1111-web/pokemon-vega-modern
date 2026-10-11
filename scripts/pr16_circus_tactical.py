#!/usr/bin/env python3
"""15勝原本を維持し、16戦目以降に通常メニューで控えへ交代する。ROM変更なし。"""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_reliability as previous
c,probe=previous.c,previous.probe
need,identity,stable=c.need,c.identity,c.stable
SELF='scripts/pr16_circus_tactical.py'
HEADER='tools/mgba_pr16_circus_tactical.h'
TEST='tests/test_pr16_circus_tactical.py'
WORKFLOW='.github/workflows/pr16-circus-tactical.yml'
REPORT='content/modernization/pr16_circus_tactical.json'
OLD='content/modernization/pr16_circus_reliability.json'
RAW='evidence/pr16_circus_reliability/35428983641/native/'+probe.CASE
TASK='USER-20260919-CIRCUS-TACTICAL'
OUT=ROOT/'.local/pr16-circus-tactical'
FILES=(SELF,HEADER,TEST,WORKFLOW,OLD,RAW+'.stdout',RAW+'.stderr',RAW+'.process.json',
       *previous.FILES,'scripts/pr16_circus_reliability.py')
NEXT='今回の連続入場原本の最初の停止から続ける。15勝と16戦目actionまで74イベントを固定。16戦目以降だけ場のtype/攻撃技種から通常交代し、メニュー後のPID/OT/speciesを再解決する。真正30勝/正規特性抑制/P08は実測でのみ閉じ、旧独立nativeを再実行しない。'
original_policy=previous.policy_text
original_prefix=previous.verify_prefix


def policy_text(base,headers):
    text=original_policy(base,headers)
    old='    unsigned streak=read16(c,0x0203DB20U),selected=streak<3U?fp_move_slot(c):wx_move_slot(c);'
    need(text.count(old)==1,'tactical move selection boundary')
    return ('static void tp_consider(struct mCore *c);\n'
        +text.replace(old,'    tp_consider(c);\n'+old)+'\n'+(ROOT/HEADER).read_text())


def verify_prefix(events,raw):
    original_prefix(events,raw)
    old=probe.parse((ROOT/(RAW+'.stderr')).read_bytes())
    need(len(old)==79 and old[73]['label']=='action' and old[73]['battle']==15,'fifteen-win prefix original absent')
    need(events[:74]==old[:74],'fifteen wins or sixteenth launch changed before tactical boundary')


def configure():
    for key,value in dict(SELF=SELF,PROBE=previous.previous.PROBE,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=TASK,
        OUT=OUT,FILES=FILES,PREFIX=previous.previous.PREFIX,probe=probe,policy_text=policy_text,verify_prefix=verify_prefix).items():setattr(c,key,value)
    return c.configure()


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['tactical_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_tactical_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30,
        previous_native_run=35428983641,previous_native_conclusion='failure',previous_observed_wins=15)
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    note='run35428983641/job105859956663は実15勝/45BP/16戦目敗北。79events/owner64/原party600/通常Save/fresh Continueはscoped PASS、真正30勝未達でActions failureを保持。新caseでは16戦目actionまで74events完全一致を要求し、受入単体を独立再実行しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['prior_actions_reconciled']=value['actions_reconciled']
    (ROOT/REPORT).write_bytes(stable(value));r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。候補310177固定・ROM変更0・ARM再link0・受入独立case再実行0。新caseのprefix15戦は不可避。通常交代は16戦目以降のみ、PID/OT/speciesをUI再整列後に再解決。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'reliability attempt exists; inspect original instead of replaying')
    old=resume.load(ROOT,OLD);run=r.api('actions/runs/35428983641')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='a5ee6ad4af9ac7763287da2c839771ed1b367b8d','previous Actions differs')
    need(old['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE' and old['recording_run']==35428983641
         and old['scoped_result']['wins']==15 and old['scoped_result']['losses']==1,'previous native differs')
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'previous raw changed: '+path)
    for path,bound in old['native']['build_recipe']['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'runtime source changed: '+path)
    actions=[{k:run[k] for k in ('id','head_sha','status','conclusion')}]
    pending=resume.load(ROOT,resume.STATE)['pending_runs']
    for entry in pending:
        if entry['run_id']!=run['id']:
            actual=r.api('actions/runs/'+str(entry['run_id']));actions.append({k:actual[k] for k in ('id','head_sha','status','conclusion')})
    value=dict(schema_version=1,classification='CIRCUS_TACTICAL_PREPARED',candidate=old['candidate'],target_wins=30,
        actions_reconciled=actions,host_tests=r.tests([Path(TEST).name]),
        inherited_run=dict(run_id=35428983641,job_id=105859956663,original_conclusion='failure',wins=15,losses=1,independently_replayed=False),
        accepted_native_cases_replayed=0,accepted_prefix_battles_reexecuted_for_continuation=15,independent_arm_links_replayed=0,
        genuine_30_wins_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        input_policy_ja='15勝の入力を完全保持し、以降は場の単type火水草に対する有効攻撃技、Ghost攻撃のみの相手にDark技を持つ控えを通常交代選択。控えは生存HP/PP/技種で順位付けし、技種を実種族typeと断定しない。1対面1回・1戦最大6回の追加交代、通常技は既存高命中/paid feedbackを維持。',
        predecessor_visual_review=dict(artifact_id=10580580034,artifact_sha256='06582be41632e57846e8168127883114723968f42c9c71b0b13127c4b057b598',
            screens=['streak-74-action','streak-75-outcome','streak-77-returned','streak-78-saved','streak-79-reloaded'],
            observation_ja='第16戦の実actionと敗北、元partyで受付前復帰、通常Saveとfresh Continueの同位置描画を確認。30勝/特性抑制受入には使わない。'))
    checkpoint(value,'PREPARED','実15勝/45BP/通常Save/fresh Continueを照合。第16戦は水先発の毒/混乱消耗と炎対面に草のみ残る順序を記録。15勝を保持し、16戦目以降だけ通常交代の選択と実個体照合を追加。')


def reconstruct():configure();c.reconstruct()
def native():configure();c.native()


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_TACTICAL_DIAGNOSTIC_OPEN'
    report=OUT/'native/report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['scoped_result']=json.loads((OUT/'native/streak.json').read_bytes())
            value['genuine_30_wins_verified']=value['scoped_result']['genuine_30_wins_verified']
            value['classification']='CIRCUS_TACTICAL_GENUINE_30_WINS_90BP_VERIFIED' if value['genuine_30_wins_verified'] else 'CIRCUS_TACTICAL_FIRST_LOSS_SAVE_VERIFIED_TARGET_OPEN'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False;value['text_evidence']={}
    prefix='evidence/pr16_circus_tactical/'+os.environ['GITHUB_RUN_ID']+'/'
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name in ('report.json','events.json',probe.CASE+'.stdout',probe.CASE+'.stderr',probe.CASE+'.process.json','streak.json','reconstruction.json'):
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            name=prefix+p.relative_to(OUT).as_posix();target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    result=value.get('scoped_result',{})
    checkpoint(value,'RECORDED','通常交代追加後の連続入場を記録: 実勝数'+str(result.get('wins','未確定'))+'。勝敗/報酬/保存の実測と真正30勝ゲートを分離。最初の未解決停止から続ける。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action=='pack':configure();c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
