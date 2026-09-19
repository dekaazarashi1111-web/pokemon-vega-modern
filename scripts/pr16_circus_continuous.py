#!/usr/bin/env python3
"""既受入3勝を独立再実行せず、同一processで再入場から真正30連勝を目指す。"""
from pathlib import Path
import io
import json
import os
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_finish as f
import pr16_circus_continuous_probe as probe
need,identity,stable=probe.need,f.identity,f.stable
SELF='scripts/pr16_circus_continuous.py'
SOURCE='tools/mgba_pr16_circus_continuous.c'
PROBE='scripts/pr16_circus_continuous_probe.py'
TEST='tests/test_pr16_circus_continuous.py'
WORKFLOW='.github/workflows/pr16-circus-continuous.yml'
REPORT='content/modernization/pr16_circus_continuous.json'
REVIEW='content/modernization/pr16_circus_three_win_visual_review.json'
TASK='USER-20260919-CIRCUS-CONTINUOUS'
OUT=ROOT/'.local/pr16-circus-continuous'
PREVIOUS='content/modernization/pr16_circus_accuracy.json'
PREFIX='evidence/pr16_circus_accuracy/35425237415/drain-accurate-fire/native/circus-streak-batch-save.stderr'
HEADERS=(*f.HEADERS,'tools/mgba_pr16_circus_menu_identity.h','tools/mgba_pr16_circus_matchup.h',
    'tools/mgba_pr16_circus_drain.h','tools/mgba_pr16_circus_accuracy.h')
FILES=(SELF,SOURCE,PROBE,TEST,WORKFLOW,REVIEW,'scripts/pr16_circus_finish.py')


def policy_text(base,headers):
    need(base.count('slot=wx_move_slot(c);')==1,'continuous selector boundary')
    chunks=[]
    for path in HEADERS:
        text=headers[path]
        for include in ('mgba_pr16_circus_menu_identity.h','mgba_pr16_circus_matchup.h'):
            text=text.replace('#include "'+include+'"','/* 上で固定原本を展開済み。 */')
        chunks.append(text)
    text='\n'.join(chunks)
    need(text.count('read16(c,0x0203DB20U)')==4,'continuous local-battle policy boundaries')
    text=text.replace('read16(c,0x0203DB20U)','(read16(c,0x0203DB20U)%3U)')
    return ('#define CIRCUS_ACCURACY_VARIANT 1U\nstatic unsigned fp_move_slot(struct mCore *c);\n'
        +base.replace('slot=wx_move_slot(c);','slot=fp_move_slot(c);')+'\n'+text+'''
/* controllerの履歴だけを再入場境界で消去する。game ownerやRNGは触らない。 */
static void cp_policy_reset(void){
    su_memory=(struct su_memory){0};mt_memory=(struct mt_feedback){0};pv_done=0U;mt_shifts=0U;
}
''')


def verify_prefix(events,raw):
    old=[probe.strict(line[14:]) for line in raw.splitlines() if line.startswith(b'CIRCUS_STREAK ')]
    need(len(old)==17 and old[14]['label']=='returned','accepted prefix original absent')
    need(events[:15]==old[:15],'accepted three-win prefix changed inside new continuation')


def configure():
    for key,value in dict(SELF=SELF,HEADER=SOURCE,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=TASK,
        OUT=OUT,FILES=FILES,HEADERS=HEADERS).items():setattr(f,key,value)
    f.NEXT='新しい連続入場の原本を照合。真正30勝/90BP未達は最初の停止条件だけを修復する。30勝後の正規特性抑制は別ゲート。受入済み3勝/BP/Ring/cold-loadの単体caseは再実行せずP08も未完のまま保つ。'
    return f.configure()


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['continuous_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_three_win_acceptance']=dict(path=PREVIOUS,run_id=35425237415,job_id=105849912664,
        candidate=value['candidate'],wins=3,bp=9,later_launches=2,save_continue_verified=True,
        visual_review=REVIEW,accepted_independent_cases_replayed=0)
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    note='run35425237415/job105849912664: 実3勝・9BP・第2第3launch個体保持・owner64/party600・通常Save/fresh Continue・5画面を受入。残り3入力方策は未実行。新連続caseの不可避prefix3戦を独立受入caseの再実行と混同しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    (ROOT/REPORT).write_bytes(stable(value));r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=SOURCE
    r.checkpoint(state,loss,stop,f.NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。candidate310177固定、ROM変更0、ARM再link0、受入済み独立case再実行0。新case内prefix3戦の再実行は明示。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT);need(not (ROOT/REPORT).exists(),'continuous attempt already exists; inspect original')
    old=resume.load(ROOT,PREVIOUS);run=r.api('actions/runs/35425237415')
    need(run['status']=='completed' and run['conclusion']=='success' and old['classification']=='CIRCUS_THREE_WIN_ACCURACY_SAVE_CONTINUE_VERIFIED'
        and old['selected_policy']=='drain-accurate-fire' and len(old['attempts'])==1,'three-win acceptance differs')
    f.require_three(old['attempts'][0]['result'])
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'accepted text changed')
    review=resume.load(ROOT,REVIEW);artifact=r.api('actions/artifacts/'+str(review['artifact_id']))
    need(artifact['digest']=='sha256:'+review['artifact_sha256'],'visual artifact binding')
    raw=subprocess.check_output(['gh','api','repos/'+r.REPO+'/actions/artifacts/'+str(review['artifact_id'])+'/zip'],cwd=ROOT)
    need(identity(raw)['sha256']==review['artifact_sha256'],'visual ZIP binding')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name,bound in review['screens'].items():need(identity(z.read('finish/drain-accurate-fire/native/'+name))==bound,'visual source changed')
    value=dict(schema_version=1,classification='CIRCUS_CONTINUOUS_THIRTY_TARGET_PREPARED',candidate=old['candidate'],target_wins=30,
        inherited_three_win=dict(path=PREVIOUS,run_id=35425237415,job_id=105849912664,original_conclusion='success',visual_review=REVIEW),
        accepted_native_cases_replayed=0,accepted_prefix_battles_reexecuted_for_continuation=3,independent_arm_links_replayed=0,
        host_tests=r.tests([Path(TEST).name]),genuine_30_wins_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        scope_ja='同じprocessで受付→3戦→元party復元→再受付を最大10回。中断も勝数注入も行わず、最初の実敗北で停止。全連続区間後の通常Save/fresh Continueを検証。先頭3勝の原本15イベント完全一致を必須にする。')
    checkpoint(value,'PREPARED','実3勝/9BPのActionsと5画面を正式照合。次の未完は0から連続入場での真正30勝。新30戦caseを1processとして追加し、3勝単体を再実行しない。')


def reconstruct():configure();f.reconstruct()


def native():
    import pr16_streak_native as n
    b=configure();recipe=json.loads((n.INPUT/'report.json').read_bytes())
    def verify(value):
        need(value==recipe and identity((n.INPUT/'candidate.gba').read_bytes())==recipe['candidate']
            and recipe['candidate']['sha256']==probe.SHA,'continuous candidate identity')
        for path,bound in recipe['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'continuous source binding: '+path)
    n.reconstruct=lambda:verify(recipe);n.verify_recipe=verify;n.probe=probe
    original=probe.validate
    def validate(raw,err,code,case):
        result=original(raw,err,code,case);verify_prefix(probe.parse(err),(ROOT/PREFIX).read_bytes());return result
    probe.validate=validate
    policy=n.policy
    n.policy=lambda wx,br:policy_text(policy(wx,br),{p:(ROOT/p).read_text() for p in HEADERS})+'\n'+(ROOT/b.fade.WATCH).read_text()
    n.SELF=SELF;n.SOURCE=SOURCE;n.TEST=TEST;n.WORKFLOW=WORKFLOW;n.OUT=OUT/'native'
    n.EXTRA=n.EXTRA|set(FILES)|set(HEADERS)|{b.fade.WATCH,b.fade.SELF,PREVIOUS,PREFIX}
    result=n.run();need(result['status']=='PASS_CIRCUS_SCOPED_NATIVE','continuous lifecycle failed; inspect original')
    probe.require_target(result['results'][0]['result'])


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_CONTINUOUS_DIAGNOSTIC_OPEN'
    report=OUT/'native/report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['scoped_result']=json.loads((OUT/'native/streak.json').read_bytes())
            value['genuine_30_wins_verified']=value['scoped_result']['genuine_30_wins_verified']
            value['classification']='CIRCUS_GENUINE_30_WINS_90BP_SAVE_CONTINUE_VERIFIED' if value['genuine_30_wins_verified'] else 'CIRCUS_CONTINUOUS_FIRST_LOSS_SAVED_DIAGNOSTIC'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False;value['text_evidence']={}
    prefix='evidence/pr16_circus_continuous/'+os.environ['GITHUB_RUN_ID']+'/'
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name in ('report.json','events.json',probe.CASE+'.stdout',probe.CASE+'.stderr',probe.CASE+'.process.json','streak.json','reconstruction.json'):
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            name=prefix+p.relative_to(OUT).as_posix();target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    checkpoint(value,'RECORDED','連続10入場・実30勝・90BP・固有owner64・原party600・通常Save/fresh Continueを確認。正規特性抑制とP08は未完。'
        if value['genuine_30_wins_verified'] else '連続入場の今回原本を保存。真正30勝は未達のまま保持し、最初の実不一致から続ける。既受入3勝/9BPとcold-load成功は維持。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action=='pack':configure();f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
