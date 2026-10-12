#!/usr/bin/env python3
"""4勝後の敗北原本を再実行せず照合し、未完連続戦の無進展入力だけを修復。"""
from pathlib import Path
import io
import importlib.util
import json
import os
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_continuous as c
import pr16_circus_reentry_probe as probe
need,identity,stable=c.need,c.identity,c.stable
SELF='scripts/pr16_circus_reentry.py'
PROBE='scripts/pr16_circus_reentry_probe.py'
HEADER='tools/mgba_pr16_circus_reentry.h'
TEST='tests/test_pr16_circus_reentry.py'
WORKFLOW='.github/workflows/pr16-circus-reentry.yml'
REPORT='content/modernization/pr16_circus_reentry.json'
REVIEW='content/modernization/pr16_circus_reentry_visual_review.json'
OLD='content/modernization/pr16_circus_continuous.json'
RAW='evidence/pr16_circus_continuous/35426278164/native/'+probe.CASE
TASK='USER-20260919-CIRCUS-REENTRY'
OUT=ROOT/'.local/pr16-circus-reentry'
FILES=(SELF,PROBE,HEADER,TEST,WORKFLOW,REVIEW,OLD,RAW+'.stdout',RAW+'.stderr',RAW+'.process.json',
    'scripts/pr16_circus_continuous.py','scripts/pr16_circus_continuous_probe.py',
    'scripts/pr16_circus_finish.py','tools/mgba_pr16_circus_continuous.c','tests/test_pr16_circus_continuous.py')
NEXT='今回の連続入場原本で最初の未達条件から続ける。4勝後敗北の原本はfailureのまま、正規LOSS→ABORT/保存をhostで再照合済み。真正30勝後の正規特性抑制とP08は別ゲート。受入済み単体caseと旧敗北nativeは再実行しない。'
# configure後の別名importでも、可変共有moduleからwrapperを再継承しない。
_spec=importlib.util.spec_from_file_location('reentry_original_continuous',ROOT/'scripts/pr16_circus_continuous.py')
_original=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_original)
original_policy=_original.policy_text
original_prefix=_original.verify_prefix


def policy_text(base,headers):
    text=original_policy(base,headers)
    need(text.count('slot=fp_move_slot(c);')==1,'reentry input selection anchor')
    return ('static unsigned rr_move_slot(struct mCore *c);\n'
        +text.replace('slot=fp_move_slot(c);','slot=rr_move_slot(c);')+'\n'+(ROOT/HEADER).read_text())


def verify_prefix(events,raw):
    old=probe.parse(raw)
    need(len(old)==27 and old[19]['label']=='settled' and old[19]['battle']==3,'four-win original boundary')
    need(events[:20]==old[:20],'four-win prefix changed in new continuation')


def configure():
    for key,value in dict(SELF=SELF,PROBE=PROBE,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=TASK,
            OUT=OUT,FILES=FILES,PREFIX=RAW+'.stderr',probe=probe,policy_text=policy_text,verify_prefix=verify_prefix).items():
        setattr(c,key,value)
    return c.configure()


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['reentry_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_reentry_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30,
        previous_native_run=35426278164,previous_native_conclusion='failure',previous_observed_wins=4)
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    note='run35426278164/job105852678835は実4勝→5戦目敗北→LOSS/End(0)→ABORT/current0/best4/9BP/owner64/原party600/Save/別coreの27イベントを保存。旧validator誤拒否は新host世代検査で照合し、旧Actions failureを変更しない。独立native再実行不要。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    (ROOT/REPORT).write_bytes(stable(value));r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。既存候補310177固定、ROM変更0、ARM再link0、旧原本再実行0。新30戦caseのみprefix4戦が必要。hostでは実outcome/世代差/CRC/原本64を独立に検査。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'reentry attempt exists; inspect original instead of replaying')
    old=resume.load(ROOT,OLD);run=r.api('actions/runs/35426278164')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='30478777dc36f13f452b13b53980e60c97ef6a18'
         and old['classification']=='CIRCUS_CONTINUOUS_DIAGNOSTIC_OPEN','original diagnostic differs')
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'original raw changed: '+path)
    for path,bound in old['native']['build_recipe']['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'runtime source changed: '+path)
    process=resume.load(ROOT,RAW+'.process.json')
    need(type(process['returncode']) is int and process['returncode']==0 and process['timed_out'] is False
         and process['spawn_error'] is None,'original native process failed before complete trace')
    raw=(ROOT/(RAW+'.stdout')).read_bytes();err=(ROOT/(RAW+'.stderr')).read_bytes()
    result=probe.validate(raw,err,0,probe.CASE);events=probe.parse(err);audit=probe.analyze(events,result)
    original_prefix(events,(ROOT/'evidence/pr16_circus_accuracy/35425237415/drain-accurate-fire/native/circus-streak-batch-save.stderr').read_bytes())
    need((result['wins'],result['losses'],result['battles'])==(4,1,5) and not audit['genuine_30_wins_verified'],'original real outcome differs')
    review=resume.load(ROOT,REVIEW);artifact=r.api('actions/artifacts/'+str(review['artifact_id']))
    need(artifact['digest']=='sha256:'+review['artifact_sha256'],'old diagnostic visual artifact differs')
    zipped=subprocess.check_output(['gh','api','repos/'+r.REPO+'/actions/artifacts/'+str(review['artifact_id'])+'/zip'],cwd=ROOT)
    need(identity(zipped)['sha256']==review['artifact_sha256'],'old diagnostic ZIP differs')
    with zipfile.ZipFile(io.BytesIO(zipped)) as z:
        for path,bound in review['screens'].items():need(identity(z.read(path))==bound,'old diagnostic screen differs')
    value=dict(schema_version=1,classification='CIRCUS_REENTRY_PAID_PROGRESS_PREPARED',candidate=old['candidate'],target_wins=30,
        inherited_run=dict(run_id=35426278164,job_id=105852678835,original_conclusion='failure',source_path=OLD),
        source_only_reanalysis=dict(native_processes=0,result=audit,original_result=result,visual_review=REVIEW,
            rule_ja='実outcome2を先に要求。Settle直後ならREADY/LOSS/+1世代、End直後ならIDLE/ABORT/+2世代。復帰時は必ずIDLE/ABORTで実4勝bestを保持。'),
        host_tests=r.tests([Path(TEST).name]),accepted_native_cases_replayed=0,accepted_prefix_battles_reexecuted_for_continuation=3,unchanged_observed_prefix_battles_required=4,
        independent_arm_links_replayed=0,genuine_30_wins_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        input_policy_ja='最初の4勝の20イベントは完全一致。以後、同じ個体対面で実PP消費後も相手HP減少がない攻撃を2回観測した場合だけ、別の有効攻撃を通常入力で選ぶ。特性抑制の実証には数えない。')
    checkpoint(value,'PREPARED','実4勝後敗北の27イベントを新validatorで非再実行照合。正規End(0)のABORTを世代差まで検査し、5戦目の無進展攻撃だけに入力fallbackを追加。真正30勝は未完。')


def reconstruct():configure();c.reconstruct()

def native():configure();c.native()


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_REENTRY_DIAGNOSTIC_OPEN'
    report=OUT/'native/report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['scoped_result']=json.loads((OUT/'native/streak.json').read_bytes())
            value['genuine_30_wins_verified']=value['scoped_result']['genuine_30_wins_verified']
            value['classification']='CIRCUS_REENTRY_GENUINE_30_WINS_90BP_VERIFIED' if value['genuine_30_wins_verified'] else 'CIRCUS_REENTRY_FIRST_LOSS_SAVE_VERIFIED_TARGET_OPEN'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False;value['text_evidence']={}
    prefix='evidence/pr16_circus_reentry/'+os.environ['GITHUB_RUN_ID']+'/'
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name in ('report.json','events.json',probe.CASE+'.stdout',probe.CASE+'.stderr',probe.CASE+'.process.json','streak.json','reconstruction.json'):
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            name=prefix+p.relative_to(OUT).as_posix();target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    checkpoint(value,'RECORDED','真正30勝/90BP/通常Save/fresh Continueを記録。正規特性抑制とP08は未完。' if value['genuine_30_wins_verified']
        else '無進展入力修復後の連続case原本を保存。旧実4勝後敗北の再解析と新実測を分離し、真正30勝は未達のまま最初の不一致を次へ引き継ぐ。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action=='pack':configure();c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
