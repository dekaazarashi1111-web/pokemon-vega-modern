#!/usr/bin/env python3
"""メニュー開閉での個体再解決を修復し、独立した中断復旧の読取traceを追加。"""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_menu_recovery.py'
TEST='tests/test_pr16_circus_menu_recovery.py'
WORKFLOW='.github/workflows/pr16-circus-menu-recovery.yml'
HEADER='tools/mgba_pr16_circus_menu_identity.h'
FIXTURE='tests/fixtures/circus_menu_identity_fixture.c'
TRACE='tools/mgba_pr16_circus_recovery_trace.c'
MATCHUP='tools/mgba_pr16_circus_matchup.h'
POLICY='menu-identity-v1'
TASK='USER-20260919-CIRCUS-MENU-IDENTITY'
OLD_RUN=35420040412
FILES=(SELF,TEST,WORKFLOW,HEADER,FIXTURE,TRACE,MATCHUP)
MENU_CODE='''    b_frames_run(c,0U,60U);
    /* メニュー表示時のparty並替えに追従。battle前slotをUIへ流用しない。 */
    uint32_t menu_pid[3],menu_ot[3];uint16_t menu_species[3];
    for(unsigned i=0;i<3U;++i){uint32_t q=QOL_PLAYER_PARTY+100U*i;
        menu_pid[i]=read32(c,q);menu_ot[i]=read32(c,q+4U);menu_species[i]=read16(c,q+0x20U);}
    unsigned menu_slot=mi_find(read8(c,QOL_PLAYER_PARTY_COUNT),menu_pid,menu_ot,menu_species,pid,ot,species);
    bp_require(c,menu_slot<3U,"Circus menu selected individual absent or ambiguous");
    fprintf(stderr,"CIRCUS_MENU frame=%u requested=%u resolved=%u pid=%u ot=%u species=%u\\n",b_frames,target,menu_slot,pid,ot,species);
    wx_cursor(c,menu_slot);'''


def need(value,message):
    if not value:raise ValueError(message)


def repair_menu(text):
    anchor='    b_frames_run(c,0U,60U);wx_cursor(c,target);'
    include='#include <stdint.h>'
    need(text.count(anchor)==text.count(include)==1 and 'mi_find' not in text,'menu repair preimage differs')
    return text.replace(include,include+'\n#include "mgba_pr16_circus_menu_identity.h"').replace(anchor,MENU_CODE)


def prior_partial(stderr,reference):
    def events(raw):return [json.loads(row[14:]) for row in raw.splitlines() if row.startswith(b'CIRCUS_STREAK ')]
    rows,old=events(stderr),events(reference)
    need(len(rows)==12 and rows==old[:12],'first two wins/third launch prefix differs')
    need([row['outcome'] for row in rows if row['label']=='outcome']==[1,1],'not two real wins')
    need(b'Circus matchup actual selected individual/type absent' in stderr
        and b'CIRCUS_MATCHUP {"label":"begin","frame":46098,"from":1,"target":0' in stderr,
        'not the observed third battle menu stop')
    return dict(real_wins=2,third_launch_verified=True,third_outcome_observed=False,
        original_conclusion='failure',stop_frame=64472,menu_begin_frame=46098,
        diagnosis_ja='メニュー表示は先頭Miltank、次Grass。戦闘前target0をUI0へ流用して先発を選んだ。表示後partyをPID/OT/種族で再解決する。')


def menu():
    import pr16_circus_matchup as m
    m.SELF=SELF;m.TEST=TEST;m.WORKFLOW=WORKFLOW;m.FIXTURE=FIXTURE;m.POLICY=POLICY;m.TASK=TASK
    return m


def interruption():
    import pr16_circus_interruption as ip
    ip.SELF=SELF;ip.TEST=TEST;ip.WORKFLOW=WORKFLOW;ip.SOURCE=TRACE
    ip.TASK=TASK+'-RECOVERY-TRACE'
    return ip


def prepare():
    import pr16_resume as resume
    m=menu();b=m.parent().configure();r=b.rec;r.scope();state=resume.validate(ROOT)
    raw=(ROOT/b.REPORT).read_bytes();old=json.loads(raw)
    run=r.api('actions/runs/'+str(OLD_RUN))
    need(old['recording_run']==OLD_RUN and old['input_policy_id']=='matchup-feedback-v1'
        and old['classification']=='CIRCUS_THREE_WIN_DIAGNOSTIC_OPEN' and old['native']['actual_new_processes']==1
        and run['status']=='completed' and run['conclusion']=='failure','menu predecessor differs')
    for name,bound in old['text_evidence'].items():need(b.identity((ROOT/name).read_bytes())==bound,'original evidence differs')
    prefix='evidence/pr16_circus_three_win/'+str(OLD_RUN)+'/'
    evidence=(ROOT/(prefix+'circus-streak-batch-save.stderr')).read_bytes()
    reference=(ROOT/'evidence/pr16_circus_three_win/35418424222/circus-streak-batch-save.stderr').read_bytes()
    diagnosis=prior_partial(evidence,reference)
    source=ROOT/MATCHUP;before=b.identity(source.read_bytes())
    need(before==state['source_bindings'][MATCHUP],'menu source changed')
    source.write_text(repair_menu(source.read_text()))
    value={k:v for k,v in old.items() if k not in ('native','text_evidence','host_tests','scoped_result','recording_run','visual_review_completed','pivot','matchup')}
    value['previous_attempts']=[*old.get('previous_attempts',[]),dict(run_id=OLD_RUN,input_policy_id=old['input_policy_id'],
        original_conclusion='failure',checkpoint_head=r.command('git','rev-parse','HEAD'),checkpoint=dict(path=b.REPORT,**b.identity(raw)),
        text_evidence=old['text_evidence'],native_status=old['native']['status'],candidate=old['candidate'],diagnosis=diagnosis)]
    value.update(classification='CIRCUS_MENU_IDENTITY_INPUT_PENDING',input_policy_id=POLICY,
        current_attempt=dict(run_id=int(os.environ['GITHUB_RUN_ID']),trigger_head=os.environ['GITHUB_SHA']),
        source_change_review_ja='入力方策は不変。通常PARTYを開いた後の配列並替えだけに追従。PID/OT/種族の一意一致と選択後実個体を両方検証。',
        menu_repair=dict(path=MATCHUP,before=before,after=b.identity(source.read_bytes())),diagnosis=diagnosis,
        accepted_native_cases_replayed=0,independent_arm_links_replayed=0)
    value['host_tests']=r.tests([Path(TEST).name]);b.OUT.mkdir(parents=True,exist_ok=True)
    (ROOT/b.REPORT).write_bytes(b.stable(value));loss=resume.load(ROOT,r.REPORT)
    loss['three_win_followup']=dict(path=b.REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=MATCHUP;r.TASK=TASK
    r.checkpoint(state,loss,'実2勝と第3戦launchは原本に保持。第3戦の任意交代でUI並替え前slotを使った停止を、メニュー表示後の個体再解決へ修復。',
        '未完の実3勝/9BP/通常保存を検証し、同じ候補で中断ownerが失われる時点を読取専用で追跡。勝敗・抑制・release条件は緩めない。',
        [b.REPORT,*FILES],'PREPARED','6全順列・PID/OT/種族・欠落/重複を拒否。原本12イベント一致。入力列は正常なメニュー解決点まで不変。')


def native():
    import pr16_streak_native as n
    n.EXTRA=n.EXTRA|set(FILES)
    menu().native()


def finish():
    m=menu();b=m.parent().configure();original=b.checkpoint
    def checkpoint(value,stop,phase,extra):original(value,stop,phase,[*extra,*FILES])
    b.checkpoint=checkpoint;m.finish()


def prepare_trace():
    import pr16_resume as resume
    ip=interruption();b=ip.configure();r=b.rec;r.scope();resume.validate(ROOT)
    raw=(ROOT/ip.REPORT).read_bytes();value=json.loads(raw)
    need(value['recording_run']==OLD_RUN and value['classification']=='CIRCUS_INTERRUPTION_DIAGNOSTIC_OPEN'
         and value['native']['actual_new_processes']==1,'interruption predecessor differs')
    for name,bound in value['text_evidence'].items():need(b.identity((ROOT/name).read_bytes())==bound,'interruption original changed')
    prefix='evidence/pr16_circus_interruption/'+str(OLD_RUN)+'/'
    stderr=(ROOT/(prefix+'circus-interrupt-second-battle.stderr')).read_bytes()
    need(b'original core destroyed; new core boot and normal Continue' in stderr
        and b'Circus interruption must abort once and preserve real best1' in stderr
        and b'bp=0 save=4' in stderr,'not the original recovered field/owner mismatch')
    value['previous_attempts']=[*value.get('previous_attempts',[]),dict(run_id=OLD_RUN,original_conclusion='failure',
        checkpoint_head=r.command('git','rev-parse','HEAD'),checkpoint=b.identity(raw),text_evidence=value['text_evidence'],
        native_processes=1,last_real_wins=1,observed_after_continue_save_counter=4,
        scope_ja='field/count1/snapshot0まで復旧したがowner条件で停止。owner原byteは未採取、best1成功や原因の断定はしない。')]
    value['classification']='CIRCUS_INTERRUPTION_READONLY_RECOVERY_TRACE_PENDING'
    value['trace_observer']=dict(source=TRACE,input_changes=0,frame_delegations_per_call=1,
        bounded_rows=512,scope_ja='新coreから各runFrameを一度だけ実行した後にowner64/party600/Factory104/Save counterを読取。')
    for k in ('native','scoped_result','text_evidence','recording_run'):value.pop(k,None)
    ip.checkpoint(value,'中断の正規Continue後にowner条件停止とSave counter4を確認。入力・勝敗・復旧条件を変更せず、frame委譲後の読取traceで失われる時点を限定する。',
        '復旧traceから最初のowner/sector変化を特定し、必要なゲーム側修復と影響テストへ。3勝結果は別記録を継承し、影響なしに再実行しない。','START',list(FILES))


def native_trace():
    import pr16_streak_native as n
    n.EXTRA=n.EXTRA|set(FILES)
    interruption().native()


def finish_trace():interruption().finish()


def pack(trace=False):
    if trace:
        ip=interruption();ip.pack();b=ip.configure()
    else:
        m=menu();m.pack();b=m.parent().configure()
    target=ROOT/'.local/pr16-three-win-evidence';manifest=target/'members.json';members=json.loads(manifest.read_bytes())
    for name in FILES:
        p=target/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());members['source/'+name]=b.identity(p.read_bytes())
    manifest.write_bytes(b.stable(members))


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action in {'pipeline','reconstruct'}:getattr(menu().parent().configure(),action)()
    elif action=='pack-trace':pack(True)
    elif action in {'prepare','native','finish','pack','prepare-trace','native-trace','finish-trace'}:globals()[action.replace('-','_')]()
    else:raise SystemExit('unknown command')
