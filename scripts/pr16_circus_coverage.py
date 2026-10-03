#!/usr/bin/env python3
"""受入済み初回3勝を保持し、再入場後の編成と汎用攻撃入力を限定修復。"""
from pathlib import Path
import importlib.util
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_continuous as c
import pr16_circus_reentry_probe as probe
need,identity,stable=c.need,c.identity,c.stable
SELF='scripts/pr16_circus_coverage.py'
PROBE='scripts/pr16_circus_reentry_probe.py'
HEADER='tools/mgba_pr16_circus_coverage.h'
FEEDBACK='tools/mgba_pr16_circus_reentry.h'
TEST='tests/test_pr16_circus_coverage.py'
WORKFLOW='.github/workflows/pr16-circus-coverage.yml'
REPORT='content/modernization/pr16_circus_coverage.json'
OLD='content/modernization/pr16_circus_reentry.json'
RAW='evidence/pr16_circus_reentry/35427049942/native/'+probe.CASE
PREFIX='evidence/pr16_circus_accuracy/35425237415/drain-accurate-fire/native/circus-streak-batch-save.stderr'
TASK='USER-20260919-CIRCUS-COVERAGE'
OUT=ROOT/'.local/pr16-circus-coverage'
FILES=(SELF,PROBE,HEADER,FEEDBACK,TEST,WORKFLOW,OLD,RAW+'.stdout',RAW+'.stderr',RAW+'.process.json',
    'scripts/pr16_circus_reentry.py','scripts/pr16_circus_continuous.py','scripts/pr16_circus_continuous_probe.py',
    'scripts/pr16_circus_finish.py','tools/mgba_pr16_circus_continuous.c',PREFIX)
NEXT='今回の連続入場の実停止から続ける。受入初回3勝の15イベントを固定し、再入場は補助技一律加点を外した異種攻撃編成と汎用攻撃/paid無進展回避へ分離。真正30勝後の正規特性抑制とP08は未完。旧nativeは再実行しない。'
# configure後の別名importでも、可変共有moduleからwrapperを再継承しない。
_spec=importlib.util.spec_from_file_location('reentry_original_continuous',ROOT/'scripts/pr16_circus_continuous.py')
_original=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_original)
original_policy=_original.policy_text
original_prefix=_original.verify_prefix


def policy_text(base,headers):
    text=original_policy(base,headers)
    anchor='read16(c,mon+0x58U),read16(c,mon+0x5CU),read16(c,mon+0x62U),utility);'
    need(text.count(anchor)==1,'coverage rental ranking anchor')
    text=text.replace(anchor,anchor.replace('utility);','cv_utility(read16(c,0x0203DB20U),utility));'))
    need(text.count('slot=fp_move_slot(c);')==1,'coverage input selection anchor')
    feedback=(ROOT/FEEDBACK).read_text()
    old='unsigned selected=fp_move_slot(c),streak=read16(c,0x0203DB20U);'
    new='unsigned streak=read16(c,0x0203DB20U),selected=streak<3U?fp_move_slot(c):wx_move_slot(c);'
    need(feedback.count(old)==1 and feedback.count('if(streak<4U)return selected;')==1,'coverage feedback boundary')
    feedback=feedback.replace(old,new).replace('if(streak<4U)return selected;','if(streak<3U)return selected;')
    feedback=feedback.replace('受入prefix4戦の入力は完全に維持。','受入prefix3戦の入力は完全に維持。')
    return ((ROOT/HEADER).read_text()+'\nstatic unsigned rr_move_slot(struct mCore *c);\n'
        +text.replace('slot=fp_move_slot(c);','slot=rr_move_slot(c);')+'\n'+feedback)


def verify_prefix(events,raw):
    original_prefix(events,raw)


def configure():
    for key,value in dict(SELF=SELF,PROBE=PROBE,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=TASK,
            OUT=OUT,FILES=FILES,PREFIX=PREFIX,probe=probe,policy_text=policy_text,verify_prefix=verify_prefix).items():
        setattr(c,key,value)
    return c.configure()


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['coverage_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_coverage_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30,
        previous_native_run=35427049942,previous_native_conclusion='failure',previous_observed_wins=4)
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    note='run35427049942/job105854709530は4勝後敗北だが正規LOSS/ABORT/owner64/原party600/9BP/通常Save/fresh Continueのscoped validatorはPASS。30勝ゲート未達なのでActions failureを維持。旧入力fallbackの独立再実行は禁止。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    (ROOT/REPORT).write_bytes(stable(value));r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。既存候補310177固定、ROM変更0、ARM再link0、旧原本再実行0。新30戦caseのみprefix3戦が必要。hostでは実outcome/世代差/CRC/原本64を独立に検査。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'coverage attempt exists; inspect original instead of replaying')
    old=resume.load(ROOT,OLD);run=r.api('actions/runs/35427049942')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='351d61df39371b9167498534d2c5dce81c59131f'
         and old['classification']=='CIRCUS_REENTRY_FIRST_LOSS_SAVE_VERIFIED_TARGET_OPEN','previous attempt differs')
    need(old['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE' and old['native']['actual_new_processes']==1
         and old['scoped_result']['wins']==4 and old['scoped_result']['losses']==1,'previous native lifecycle differs')
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'original raw changed: '+path)
    for path,bound in old['native']['build_recipe']['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'runtime source changed: '+path)
    value=dict(schema_version=1,classification='CIRCUS_COVERAGE_GENERAL_REENTRY_PREPARED',candidate=old['candidate'],target_wins=30,
        inherited_run=dict(run_id=35427049942,job_id=105854709530,original_conclusion='failure',source_path=OLD,
            lifecycle_verification=old['native']['status'],wins=4,losses=1,independently_replayed=False),
        host_tests=r.tests([Path(TEST).name]),accepted_native_cases_replayed=0,accepted_prefix_battles_reexecuted_for_continuation=3,
        independent_arm_links_replayed=0,genuine_30_wins_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        input_policy_ja='初回3勝の15イベントを完全保持。再入場後は一律補助技2倍加点を外し、既存異種攻撃選択で3体を通常入力選択。以後の技選択は汎用攻撃scoreとPP消費/相手HP無進展回避を使用し、初回チーム専用のpivot/role条件を流用しない。')
    checkpoint(value,'PREPARED','実4勝後敗北の修復済みscoped検証を再実行せず継承。再入場後の補助技一律加点と初回限定方策の流用を切り離し、通常入力だけを修復。真正30勝は未完。')


def reconstruct():configure();c.reconstruct()

def native():configure();c.native()


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_COVERAGE_DIAGNOSTIC_OPEN'
    report=OUT/'native/report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['scoped_result']=json.loads((OUT/'native/streak.json').read_bytes())
            value['genuine_30_wins_verified']=value['scoped_result']['genuine_30_wins_verified']
            value['classification']='CIRCUS_COVERAGE_GENUINE_30_WINS_90BP_VERIFIED' if value['genuine_30_wins_verified'] else 'CIRCUS_COVERAGE_FIRST_LOSS_SAVE_VERIFIED_TARGET_OPEN'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False;value['text_evidence']={}
    prefix='evidence/pr16_circus_coverage/'+os.environ['GITHUB_RUN_ID']+'/'
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name in ('report.json','events.json',probe.CASE+'.stdout',probe.CASE+'.stderr',probe.CASE+'.process.json','streak.json','reconstruction.json'):
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            name=prefix+p.relative_to(OUT).as_posix();target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    checkpoint(value,'RECORDED','真正30勝/90BP/通常Save/fresh Continueを記録。正規特性抑制とP08は未完。' if value['genuine_30_wins_verified']
        else '再入場編成/汎用入力修復後の連続case原本を保存。実測勝数と全battle lifecycleを分離し、真正30勝未達は最初の不一致を次へ引き継ぐ。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action=='pack':configure();c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
