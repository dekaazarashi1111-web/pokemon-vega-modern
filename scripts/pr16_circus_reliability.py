#!/usr/bin/env python3
"""8勝原本を維持し、9戦目以降の低差期待値で高命中を選ぶ。ROM変更なし。"""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_coverage as previous
c,probe=previous.c,previous.probe
need,identity,stable=c.need,c.identity,c.stable
SELF='scripts/pr16_circus_reliability.py'
HEADER='tools/mgba_pr16_circus_reliability.h'
TEST='tests/test_pr16_circus_reliability.py'
WORKFLOW='.github/workflows/pr16-circus-reliability.yml'
REPORT='content/modernization/pr16_circus_reliability.json'
OLD='content/modernization/pr16_circus_coverage.json'
RAW='evidence/pr16_circus_coverage/35427693324/native/'+probe.CASE
TASK='USER-20260919-CIRCUS-RELIABILITY'
OUT=ROOT/'.local/pr16-circus-reliability'
FILES=(SELF,HEADER,TEST,WORKFLOW,OLD,RAW+'.stdout',RAW+'.stderr',RAW+'.process.json',
       *previous.FILES,'scripts/pr16_circus_coverage.py')
NEXT='今回の新しい連続入場原本の最初の停止から続ける。8勝までの40イベントを固定し、9戦目以降は期待値差10%以内の高命中選択と実行技に対応するpaid無進展を使う。真正30勝/正規特性抑制/P08は実測でのみ閉じる。旧独立nativeは再実行しない。'
original_policy=previous.policy_text
original_prefix=previous.verify_prefix


def policy_text(base,headers):
    text=original_policy(base,headers)
    replacements=[
        ('uint64_t scores[4]={0};','uint64_t scores[4]={0};unsigned reliability[4]={0};'),
        ('scores[i]=score*wx_effect(type,t1)', 'reliability[i]=accuracy?accuracy:100U;\n        scores[i]=score*wx_effect(type,t1)'),
        ('unsigned actual=rr_pick(selected,rr_memory.blocked,scores);',
         'unsigned actual=rr_pick(selected,rr_memory.blocked,scores);\n    if(streak>=8U)actual=rl_pick(actual,rr_memory.blocked,scores,reliability);'),
        ('    return actual;\n}\n#endif\n#endif',
         '''    if(streak>=8U){
        fprintf(stderr,"CIRCUS_RELIABILITY frame=%u streak=%u selected=%u actual=%u blocked=%u accuracy=%u score=%llu own=",b_frames,streak,selected,actual,rr_memory.blocked,reliability[actual],(unsigned long long)scores[actual]);
        for(unsigned i=0;i<BATTLE_MON_SIZE;++i)fprintf(stderr,"%02x",read8(c,own+i));
        fprintf(stderr," foe=");for(unsigned i=0;i<BATTLE_MON_SIZE;++i)fprintf(stderr,"%02x",read8(c,foe+i));
        fprintf(stderr,"\\n");
    }
    return actual;
}
#endif
#endif''')]
    # 最後の置換はrr_move_slotだけ。過去headerのreturn actualには触れない。
    for old,new in replacements:
        if old.startswith('    return actual;'):
            need(text.endswith(old+'\n'),'reliability feedback tail differs');text=text[:-len(old)-1]+new+'\n'
        else:
            need(text.count(old)==1,'reliability anchor differs: '+old);text=text.replace(old,new)
    return (ROOT/HEADER).read_text()+'\n'+text


def verify_prefix(events,raw):
    original_prefix(events,raw)
    old=probe.parse((ROOT/(RAW+'.stderr')).read_bytes())
    need(len(old)==45 and old[39]['label']=='action' and old[39]['battle']==8,'eight-win prefix original absent')
    need(events[:40]==old[:40],'eight wins or ninth launch changed before reliability boundary')


def configure():
    for key,value in dict(SELF=SELF,PROBE=previous.PROBE,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=TASK,
        OUT=OUT,FILES=FILES,PREFIX=previous.PREFIX,probe=probe,policy_text=policy_text,verify_prefix=verify_prefix).items():setattr(c,key,value)
    return c.configure()


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['reliability_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_reliability_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30,
        previous_native_run=35427693324,previous_native_conclusion='failure',previous_observed_wins=8)
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    note='run35427693324/job105856400152は実8勝/18BP/9戦目敗北。45events/owner64/原party600/通常Save/fresh Continueはscoped PASS、真正30勝未達なのでActions failureを保持。新caseは第9戦actionまで40events完全一致を要求し、独立再実行しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['prior_actions_reconciled']=value['actions_reconciled']
    (ROOT/REPORT).write_bytes(stable(value));r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。候補310177固定・ROM変更0・ARM再link0・受入独立case再実行0。新caseのprefix8戦は不可避。高命中選択は9戦目以降のみ、実技をfeedbackへ記録。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'reliability attempt exists; inspect original instead of replaying')
    old=resume.load(ROOT,OLD);run=r.api('actions/runs/35427693324')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='6c0f61679c76acf8199b7f1fee6fbd0cb8709a56','previous Actions differs')
    need(old['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE' and old['recording_run']==35427693324
         and old['scoped_result']['wins']==8 and old['scoped_result']['losses']==1,'previous native differs')
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'previous raw changed: '+path)
    for path,bound in old['native']['build_recipe']['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'runtime source changed: '+path)
    actions=[{k:run[k] for k in ('id','head_sha','status','conclusion')}]
    pending=resume.load(ROOT,resume.STATE)['pending_runs']
    for entry in pending:
        if entry['run_id']!=run['id']:
            actual=r.api('actions/runs/'+str(entry['run_id']));actions.append({k:actual[k] for k in ('id','head_sha','status','conclusion')})
    value=dict(schema_version=1,classification='CIRCUS_RELIABILITY_PREPARED',candidate=old['candidate'],target_wins=30,
        actions_reconciled=actions,host_tests=r.tests([Path(TEST).name]),
        inherited_run=dict(run_id=35427693324,job_id=105856400152,original_conclusion='failure',wins=8,losses=1,independently_replayed=False),
        accepted_native_cases_replayed=0,accepted_prefix_battles_reexecuted_for_continuation=8,independent_arm_links_replayed=0,
        genuine_30_wins_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        input_policy_ja='再入場の汎用分離で欠落した命中安定性を、期待値差10%以内の汎用規則として9戦目から接続。PPなし/無効/blocked技を選び直さず、feedbackは実行技。',
        predecessor_visual_review=dict(artifact_id=10579915811,artifact_sha256='d36e82fddcebbfc71fbdbbda7ec5f23cd8fb700fcd06748b1da053832506ef40',
            screens=['streak-30-selected','streak-39-confirmation','streak-40-action','streak-41-outcome','streak-43-returned','streak-44-saved','streak-45-reloaded'],
            observation_ja='3入場目の6体選出/3体最終確認、第9戦、敗北後の受付前復帰・Save・Continueの描画を確認。画像だけから30勝や抑制の受入は行わない。'))
    checkpoint(value,'PREPARED','実8勝/18BP/通常Save/fresh Continueを失敗原本から照合。第9戦で命中85の126を反復したため、近接期待値の高命中技へ切り替える入力と実battle snapshotを追加。')


def reconstruct():configure();c.reconstruct()
def native():configure();c.native()


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_RELIABILITY_DIAGNOSTIC_OPEN'
    report=OUT/'native/report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['scoped_result']=json.loads((OUT/'native/streak.json').read_bytes())
            value['genuine_30_wins_verified']=value['scoped_result']['genuine_30_wins_verified']
            value['classification']='CIRCUS_RELIABILITY_GENUINE_30_WINS_90BP_VERIFIED' if value['genuine_30_wins_verified'] else 'CIRCUS_RELIABILITY_FIRST_LOSS_SAVE_VERIFIED_TARGET_OPEN'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False;value['text_evidence']={}
    prefix='evidence/pr16_circus_reliability/'+os.environ['GITHUB_RUN_ID']+'/'
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name in ('report.json','events.json',probe.CASE+'.stdout',probe.CASE+'.stderr',probe.CASE+'.process.json','streak.json','reconstruction.json'):
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            name=prefix+p.relative_to(OUT).as_posix();target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    result=value.get('scoped_result',{})
    checkpoint(value,'RECORDED','高命中選択後の連続入場を記録: 実勝数'+str(result.get('wins','未確定'))+'。勝敗/報酬/保存の実測と真正30勝ゲートを分離。最初の未解決停止から続ける。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action=='pack':configure();c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
