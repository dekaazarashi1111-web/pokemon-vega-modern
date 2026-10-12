#!/usr/bin/env python3
"""完了済みSave10測定を保存ZIPから記録回復。native/test再実行は禁止。"""
from __future__ import annotations
import importlib
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save10_actions as a
m,d,h=a.m,a.d,a.h
SELF='scripts/pr16_story_save10_record.py'
WF='.github/workflows/pr16-story-save10-record.yml'
ARTNAME='pr16-story-save10-record'
SOURCE='02e451790c9b05d29861d29c3578ffca787061e6'
RUN=36423498952
ARTIFACT=10970079659
PATCH_FROM="    note='Save10の218/cold62と77画面・32検査は保存原本から照合し、通常進行の再開時に再実行しない。28境界検査も影響なしに再実行しない。前回未保存WIPの敗北は保持。'\n"
PATCH_TO="    state['bp']['next_step']=state['next_action']['goal_ja']\n"+PATCH_FROM


def configure():
    a.CODE|={SELF,WF}


def original():
    run=d.inputs.api('actions/runs/'+str(RUN));reply=d.inputs.api('actions/runs/'+str(RUN)+'/jobs?per_page=100')
    m.need(run['head_sha']==SOURCE and run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1,'failed record run retained, not success relabel')
    m.need(reply['total_count']==len(reply['jobs'])==1,'one measured job');job=reply['jobs'][0]
    steps={s['name']:s['conclusion'] for s in job['steps']}
    for name in ('Resume and immutable input boundary','New 218-input interval and independent cold62 only','Preserve pre-native failure and record Save10 evidence','Preserve partial originals without rerun','Run actions/upload-artifact@v4','Post Run actions/checkout@v4'):
        m.need(steps[name]=='success','required completed original step '+name)
    m.need(steps['Task graph and scoped final index']=='failure' and steps['Non-force commit and remote readback']=='skipped','failure occurred before commit, after measured success')
    raw=a.archive(ARTIFACT,RUN,17781137,'2d9b381ca9b4e162a784a621b7335f396e281e9b171a34d0892765e18fdeee63')
    with h.safe_zip(raw,200000000) as z:
        m.need(len(z.namelist())==103,'exact original member set size')
        v=m.load(z.read('public/measurement.json'));cp=m.load(z.read('checkpoint.json'))
        m.need(v['source_head']==SOURCE and v['run_id']==RUN and v['focused_tests']==32 and cp['source_head']==SOURCE,'measurement identity')
        for name,binding in v['source_bindings'].items():
            m.need(m.identity(d.git('show',SOURCE+':'+name))==binding,'measured source bytes at immutable HEAD')
            m.need(m.identity((ROOT/name).read_bytes())==binding,'no changed measured code before recovery')
        for name,binding in (('candidate.gba',m.CANDIDATE),('runner',m.RUNNER)):
            m.need(m.identity(z.read(name))==binding,'immutable candidate/runner')
        for name in z.namelist():
            if name.startswith(('public/','progress/','continue/')):
                target=a.OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
            elif name in ('input.srm','training.srm','cold.srm'):
                target=a.OUT/'private'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(name))
        read=lambda name:(a.PUBLIC/name).read_bytes()
        result=m.verify(read('progress.stdout.txt'),read('continue.stdout.txt'),read('commands.txt'),read('continue-commands.txt'),d.read(ROOT/m.PARENT),read('verification.json'),a.OUT/'progress',a.OUT/'continue')
        proof=m.saved_bytes(z.read('input.srm'),z.read('training.srm'),z.read('cold.srm'))
        m.need(result==v['result'] and proof==v['save_byte_proof'],'exact saved measurement and byte proof')
        unit=read('unit.stderr.txt');m.need(unit.count(b' ... ok\n')==32 and b'\nOK\n' in unit and b'skipped' not in unit and not read('unit.stdout.txt'),'32 passed test originals, no rerun')
    receipt=dict(run=d.run_summary(run),job=job,artifact=d.read(a.PUBLIC/f'artifact-{ARTIFACT}.json'),source_head=SOURCE,successful_native_measurement=True,whole_run_success=False,failure_reason='next-action mirrors differ',new_native_processes=0,new_test_executions=0)
    a.write(a.PUBLIC/'record-failure-recovery.json',receipt)
    return v,cp,receipt


def collect():
    os.chdir(ROOT);d.current();state=h.source_check();m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists(),'collect once, no accepted replay')
    a.PUBLIC.mkdir(parents=True);a.ART.mkdir();v,cp,receipt=original()
    path=ROOT/a.SELF;before=path.read_text();m.need(before.count(PATCH_FROM)==1 and PATCH_TO not in before,'exact publisher mirror patch only')
    path.write_text(before.replace(PATCH_FROM,PATCH_TO),encoding='utf-8')
    importlib.reload(a);configure()
    # record用sourceだけを変更。native検証器/32検査/入力/目視原本/ROMは不変。
    for name,binding in v['source_bindings'].items():
        if name!=a.SELF:m.need(m.identity((ROOT/name).read_bytes())==binding,'no native-impact changes')
    a.write(a.PUBLIC/'publisher-fix.json',dict(path=a.SELF,before=m.identity(before.encode()),after=m.identity(path.read_bytes()),reason_ja='bp.next_stepをnext_action.goal_jaの最終値から設定。pending時の接頭辞も一致させる。native/32検査のsourceは変更しない。'))
    base='content/modernization/pr16_story_save10_evidence/'+str(RUN);dest=ROOT/base;dest.mkdir(parents=True);owned={a.SELF}
    evidence=set()
    for p in a.PUBLIC.iterdir():
        if p.is_file():
            raw=p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'text evidence only');(dest/p.name).write_bytes(raw);evidence.add(base+'/'+p.name)
    a.write(dest/'manifest.json',d.bindings(evidence));owned|=evidence|{base+'/manifest.json'}
    cp.update(status='PASS_STORY_SAVE10_PENDING_RECORD_TERMINAL',actions_completion_confirmed=False,retained_artifact_id=ARTIFACT,retained_artifact=receipt['artifact'],measurement_run_conclusion='failure',measurement_native_step_conclusion='success',record_failure_preserved=True,record_recovery_run_id=int(os.environ['GITHUB_RUN_ID']),record_recovery_source_head=os.environ['GITHUB_SHA'],record_recovery_artifact_name=ARTNAME,record_source_bindings=d.bindings(a.CODE),record_new_native_processes=0,record_new_test_executions=0,evidence_manifest=base+'/manifest.json')
    a.write(a.ART/'checkpoint.json',cp)
    guide='# Save10: 通常ボール供給・保存再開\n\n'+a.GOAL+'\n\n## 原本と回復\n\n測定source `'+SOURCE+'`、run '+str(RUN)+'。測定/新規32検査/証拠生成/原本uploadは成功したが、引継ぎ2か所の次工程mirror不一致でcommit前に停止。run全体のfailureは保持する。artifact '+str(ARTIFACT)+'の77画面・Save/RTC・測定結果・32検査原本を読み、ゲームやtestを再実行せず記録側だけを修正した。開発2process/32検査、正式2process/32検査、回復native0/test0。\n\nSave10 SHA-256 `'+m.OUTPUT_SAVE['sha256']+'`、131088bytes。保存前0→5個、再会話/独立Continue後も5個。他4bag pocket/残12ボール枠/2776円は不変。Save9 bank57344bytes保持、徒歩友情104→106以外599partybytes保持。Save10/cold全600partybytes・131088Save/RTC一致。12組の全画面一致。手持ち一覧だけ358pixelのsprite animation差を明示し、全画面一致とはしない。通常Save完了画面の地名は501番道路。贈与瞬間の空textに道具名を創作しない。\n\n初期研究室での図鑑評価は研究活動施設自然到達ではない。捕獲/トレーナー勝利/全story/release未受入。前回未保存の敗北WIPを成功へ改作せず保持。次は本Save10の作業コピーのみを使い、218/cold62や既受入区間を再生しない。一般CIの既存capacity原本failureは未解決。\n\n記録回復runのpush/upload終端は別のAPI照合で確定する。\n'
    (ROOT/a.GUIDE).write_text(guide,encoding='utf-8')
    a.write(ROOT/a.WORK,dict(schema_version=1,status='MEASURED_ORIGINALS_RECOVERED_RECORD_TERMINAL_PENDING',superseded_by=m.CP,formal_run_id=RUN,formal_source_head=SOURCE,whole_measurement_run_success=False,native_measurement_success=True,retained_artifact_id=ARTIFACT,record_recovery_run_id=cp['record_recovery_run_id'],development_native_processes=2,development_focused_tests=32,formal_native_processes=2,formal_focused_tests=32,recovery_native_processes=0,recovery_test_executions=0,prior_wip='docs/PR16_STORY_SAVE10_WIP_JA.md',prior_wip_accepted=False))
    owned|=a.boundary_terminal()|{a.GUIDE,a.WORK}
    state['story_journey_sequence'].update(actions_completion_confirmed=True,retained_artifact_id=10969625772)
    a.publish(state,cp,owned,False)
    for name in d.LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write('- Record recovery: measured run36423498952 is failure at resume mirror after native/32-test success. artifact10970079659 retained. This recovery executed native0/test0; original 2/32 are inherited, not rerun. Fixed only publisher next-action mirror.\n')
    a.preserve()


def terminal():
    os.chdir(ROOT);d.current();state=h.source_check();cp=d.read(ROOT/m.CP);configure()
    m.need(cp['status']=='PASS_STORY_SAVE10_PENDING_RECORD_TERMINAL' and cp['actions_completion_confirmed'] is False and cp['retained_artifact_id']==ARTIFACT,'pending recorded original')
    a.PUBLIC.mkdir(parents=True);a.ART.mkdir()
    run=d.inputs.api('actions/runs/'+str(cp['record_recovery_run_id']));reply=d.inputs.api('actions/runs/'+str(run['id'])+'/jobs?per_page=100')
    m.need(run['head_sha']==cp['record_recovery_source_head'] and run['path']==WF and run['status']=='completed' and run['conclusion']=='success' and run['run_attempt']==1,'record recovery completed successfully')
    m.need(reply['total_count']==len(reply['jobs'])==1,'one recovery job');job=reply['jobs'][0]
    m.need(job['name']=='record' and job['conclusion']=='success' and all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'all recovery steps incl push/upload/post')
    reply=d.inputs.api('actions/runs/'+str(run['id'])+'/artifacts?per_page=100');m.need(reply['total_count']==len(reply['artifacts'])==1,'one recovery artifact');meta=reply['artifacts'][0]
    m.need(meta['name']==ARTNAME and meta['workflow_run']['head_sha']==run['head_sha'],'record artifact identity')
    raw=a.archive(meta['id'],run['id'],meta['size_in_bytes'],meta['digest'].removeprefix('sha256:'))
    with h.safe_zip(raw,200000000) as z:
        m.need(m.load(z.read('checkpoint.json'))==cp,'checkpoint from actual recovery upload')
        completion=z.read('completion-head.txt').decode().strip();m.need(len(completion)==40 and all(x in '0123456789abcdef' for x in completion),'completion SHA')
        subprocess.run(['git','merge-base','--is-ancestor',completion,'HEAD'],check=True)
        with h.safe_zip(z.read('record.zip'),100000000) as r:
            for name in r.namelist():m.need(d.git('show',completion+':'+name)==r.read(name),'exact committed recovery text')
    measured=d.inputs.api('actions/runs/'+str(RUN));m.need(measured['conclusion']=='failure','original run failure remains visible')
    receipt=dict(run=d.run_summary(run),job=job,artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},completion_head=completion,measurement_run=d.run_summary(measured),native_measurement_accepted_from_successful_step=True,measurement_whole_run_success=False,new_native_processes=0,new_test_executions=0)
    name='content/modernization/pr16_story_save10_terminal.json';a.write(ROOT/name,receipt)
    cp.update(status='PASS_STORY_SAVE10_SCOPED',actions_completion_confirmed=True,completion_head=completion,terminal_receipt=name,record_recovery_artifact=receipt['artifact'])
    with (ROOT/a.GUIDE).open('a',encoding='utf-8') as f:f.write('\n## 正式終端\n\n記録回復run '+str(run['id'])+' の全'+str(len(job['steps']))+'step成功。completion `'+completion+'`、記録artifact '+str(meta['id'])+'。元測定runのfailureは保持。ゲーム再開用原本はartifact10970079659のtraining.srm。終端回収native0/test0。\n')
    work=d.read(ROOT/a.WORK);work.update(status='FORMAL_TERMINAL_CONFIRMED',actions_completion_confirmed=True,record_recovery_success=True);a.write(ROOT/a.WORK,work)
    a.write(a.ART/'terminal.json',receipt);a.publish(state,cp,{name,a.GUIDE,a.WORK},True)


if __name__=='__main__':
    configure()
    operations=dict(collect=collect,terminal=terminal,guard=a.guard,snapshot=a.snapshot,preserve=a.preserve)
    if len(sys.argv)!=2 or sys.argv[1] not in operations:raise SystemExit('collect|terminal|guard|snapshot|preserve')
    operations[sys.argv[1]]()
