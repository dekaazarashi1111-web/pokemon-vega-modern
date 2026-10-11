#!/usr/bin/env python3
"""受入済み3b候補を再linkせず、別入力方策で実3勝と継続launchを検証。"""
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_loss_followup as rec
import pr16_circus_loss_weather as fade
need,identity,stable=rec.need,rec.identity,rec.stable
SELF='scripts/pr16_circus_three_win.py'
TEST='tests/test_pr16_circus_three_win.py'
WORKFLOW='.github/workflows/pr16-circus-three-win.yml'
HEADER='tools/mgba_pr16_circus_three_win.h'
REPORT='content/modernization/pr16_circus_three_win.json'
OUT=ROOT/'.local/pr16-circus-three-win'
SHA='3b5f919958bf72bad9aa5b466215f33311f9c8c19e1f7f409303416eab952d5d'


def three_wins(result):
    need(all(type(result.get(k)) is int and result[k]==v for k,v in dict(wins=3,losses=0,battles=3).items()),
         'three real wins required; loss case already accepted separately')
    return result


def checkpoint(value,stop,phase,extra):
    import pr16_resume as resume
    state=resume.validate(ROOT);loss=resume.load(ROOT,rec.REPORT)
    loss['three_win_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    (ROOT/REPORT).write_bytes(stable(value))
    rec.SELF=SELF;rec.TEST=TEST;rec.WORKFLOW=WORKFLOW;rec.HEADER=HEADER
    rec.checkpoint(state,loss,stop,'実3勝・第2/第3launchの同一個体・9BP・Save/Continueを検証し、完了した証拠を再実行しない。続いて中断復帰、真正30連勝と正規特性抑制へ進む。',
        [REPORT,HEADER,SELF,TEST,WORKFLOW,*extra],'THREE-WIN-'+phase,value['classification']+'。候補ROM変更0、既存2link再実行0、受入済み単体再実行0。')


def prepare():
    import pr16_resume as resume
    rec.scope();resume.validate(ROOT);need(not (ROOT/REPORT).exists(),'three-win case already started; do not replay')
    previous=resume.load(ROOT,fade.REPORT);need(previous['classification']=='CIRCUS_LOSS_FADE_SAVE_CONTINUE_VERIFIED_SCOPED','loss checkpoint absent')
    run=rec.api('actions/runs/35415331977')
    need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']=='b65c3db450b460a396d2e1f81d4bde81c6a8a718','loss Actions not complete')
    value=dict(schema_version=1,classification='CIRCUS_THREE_WIN_INPUT_POLICY_PENDING',candidate=dict(size=33554432,sha256=SHA),
        previous_loss_run=35415331977,previous_loss_checkpoint='21b96f4bc48569360a84a1c8978e13ca6d0291b0',
        previous_loss_visual_review=dict(reviewed=['streak-07-returned','streak-08-saved','streak-09-reloaded'],
          observation_ja='3画面とも受付前の同位置にプレイヤーとNPC列を確認。黒画面なし。保存後/Continue後の雨描画も正常。',
          scope_ja='実敗北・正規復帰・保存再開の一連動作を受入。フェード再試行分岐の実行回数自体は未計測。'),
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    value['host_tests']=rec.tests(['test_pr16_circus_three_win.py'])
    OUT.mkdir(parents=True,exist_ok=True)
    checkpoint(value,'Circus実敗北の9イベント/原party600/owner64/7guard/Save+fresh Continueはrun35415331977で受入。3画面も確認。3b候補を保持し、攻撃技と実能力の読取専用順位付けで未受入3勝・継続戦を開始。','START',[])


def reconstruct():
    import pr16_circus_retention as parent
    import pr16_streak_native as n
    from pr16_circus_streak import bounded_patch
    previous=json.loads((ROOT/fade.REPORT).read_bytes());r=previous['native']['build_recipe']
    need(r['candidate']==dict(size=33554432,sha256=SHA),'accepted candidate differs')
    raw=(parent.OUT/'candidate.gba').read_bytes();need(identity(raw)==r['parent'],'parent differs')
    new=bounded_patch(raw,r['patches']);need(identity(new)==r['candidate'],'fixed reconstruction differs')
    for path,bound in r['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'accepted source changed: '+path)
    n.INPUT.mkdir(parents=True,exist_ok=True);(n.INPUT/'candidate.gba').write_bytes(new);(n.INPUT/'report.json').write_bytes(stable(r))
    (OUT/'reconstruction.json').write_bytes(stable(dict(candidate=r['candidate'],rom_changes=0,arm_links_replayed=0)))
    return r


def native():
    import pr16_streak_native as n
    r=json.loads((n.INPUT/'report.json').read_bytes())
    def verify(recipe):
        need(recipe==r and identity((n.INPUT/'candidate.gba').read_bytes())==r['candidate'] and r['candidate']['sha256']==SHA,'fixed win input differs')
        for path,bound in r['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'fixed win binding: '+path)
    n.reconstruct=lambda:verify(r);n.verify_recipe=verify;n.probe.SHA=SHA;fade.install_probe(n.probe)
    original=n.probe.validate
    n.probe.validate=lambda raw,stderr,code,case:three_wins(original(raw,stderr,code,case))
    n.SELF=SELF;n.TEST=TEST;n.WORKFLOW=WORKFLOW;n.EXTRA=n.EXTRA|{HEADER,fade.SELF,fade.WATCH}
    policy=n.policy;n.policy=lambda wx,br:policy(wx,br)+'\n'+(ROOT/HEADER).read_text()+'\n'+(ROOT/fade.WATCH).read_text()
    result=n.run();need(result['status']=='PASS_CIRCUS_SCOPED_NATIVE','new three-win scenario incomplete; inspect original')


def finish():
    import pr16_streak_native as n
    value=json.loads((ROOT/REPORT).read_bytes());extra=[]
    value['classification']='CIRCUS_THREE_WIN_DIAGNOSTIC_OPEN'
    p=n.OUT/'report.json'
    if p.exists():
        value['native']=json.loads(p.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            three_wins(value['native']['results'][0]['result'])
            value['classification']='CIRCUS_THREE_WIN_CONTINUATIONS_9BP_SAVE_CONTINUE_VERIFIED'
            value['scoped_result']=json.loads((n.OUT/'streak.json').read_bytes())
    prefix='evidence/pr16_circus_three_win/'+os.environ['GITHUB_RUN_ID']+'/'
    value['text_evidence']={}
    for p in [p,n.OUT/(n.probe.CASE+'.stdout'),n.OUT/(n.probe.CASE+'.stderr'),n.OUT/(n.probe.CASE+'.process.json'),n.OUT/'streak.json',OUT/'reconstruction.json']:
        if not p.exists():continue
        raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
        path=prefix+p.name;dst=ROOT/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
        value['text_evidence'][path]=identity(raw);extra.append(path)
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False
    stop=('実3勝・第2/第3launch個体保持・固有owner64・原party600・9BP・通常Save/fresh Continueを検証。真正30連勝と特性抑制は未受入。'
        if value['classification'].endswith('_VERIFIED') else '3勝専用の新入力方策を実行し原本保存。途中敗北やlaunch停止を3勝に昇格せず、今回の実停止から修復を続ける。')
    checkpoint(value,stop,'RECORDED',extra)


def pipeline():
    import pr16_resume as resume
    state=resume.validate(ROOT);raw=(ROOT/fade.SETUP_WORKFLOW).read_bytes()
    need(identity(raw)==state['source_bindings'][fade.SETUP_WORKFLOW],'inherited setup differs')
    for i,label in enumerate(fade.SETUP_STEPS):
        shell=fade.step_shell(raw.decode(),label).replace('.local/pr16-circus-loss-followup','.local/pr16-circus-three-win')
        if i==2:
            need(shell.count('python3 scripts/pr16_circus_streak.py')==1,'reconstruction command boundary')
            shell=shell.replace('python3 scripts/pr16_circus_streak.py','python3 '+SELF+' reconstruct')
        if i==3:
            need(shell.count('python3 scripts/pr16_circus_loss_followup.py native')==1,'win command boundary')
            shell=shell.replace('python3 scripts/pr16_circus_loss_followup.py native','python3 '+SELF+' native')
        subprocess.run(['bash','-euo','pipefail','-c',shell],cwd=ROOT,check=True)


def pack():
    import pr16_resume as resume
    raw=(ROOT/fade.WORKFLOW).read_bytes();state=resume.validate(ROOT)
    need(identity(raw)==state['source_bindings'][fade.WORKFLOW],'artifact pack source differs')
    shell=fade.step_shell(raw.decode(),'ROM save credentialを除外して証跡を保存')
    shell=shell.replace("('pr16-circus-loss-weather',","('pr16-circus-three-win','pr16-circus-loss-weather',")
    shell=shell.replace("names=[","names="+repr([SELF,TEST,WORKFLOW,HEADER,REPORT])+"+[")
    shell=shell.replace('.local/pr16-weather-evidence','.local/pr16-three-win-evidence')
    subprocess.run(['bash','-euo','pipefail','-c',shell],cwd=ROOT,check=True)


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in {'prepare','reconstruct','native','finish','pipeline','pack'},'command required')
    globals()[sys.argv[1]]()
