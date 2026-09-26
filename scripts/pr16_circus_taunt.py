#!/usr/bin/env python3
"""15勝原本を維持し、第16戦からTaunt先発と対状態技入力を追加。ROM変更なし。"""
from pathlib import Path
import json
import os
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_tactical as previous
c,probe=previous.c,previous.probe
need,identity,stable=c.need,c.identity,c.stable
SELF='scripts/pr16_circus_taunt.py'
HEADER='tools/mgba_pr16_circus_taunt.h'
TEST='tests/test_pr16_circus_taunt.py'
WORKFLOW='.github/workflows/pr16-circus-taunt.yml'
REPORT='content/modernization/pr16_circus_taunt.json'
OLD='content/modernization/pr16_circus_tactical.json'
RAW='evidence/pr16_circus_tactical/35429677248/native/'+probe.CASE
TASK='USER-20260919-CIRCUS-TAUNT'
OUT=ROOT/'.local/pr16-circus-taunt'
FILES=(SELF,HEADER,TEST,WORKFLOW,OLD,RAW+'.stdout',RAW+'.stderr',RAW+'.process.json',
       *previous.FILES,'scripts/pr16_circus_tactical.py')
NEXT='実15勝の71eventsを保持し、第16戦から同じ選出3体のTaunt先発と最大2回の対状態技入力を検証する。新原本で真正30勝が未達なら最初の停止だけを修復する。30勝後の正規特性抑制/P08は別ゲート。旧独立nativeを再実行しない。'
original_policy=previous.policy_text
# 今回は第16戦の選出順も変えるため74イベントではなく、検証済み15勝の71イベントを固定。
original_prefix=previous.previous.verify_prefix


def policy_text(base,headers):
    text=original_policy(base,headers)
    changes=[
        ('uint64_t scores[6]={0U};unsigned used=0U;uint32_t covered=0U;',
         'uint64_t scores[6]={0U},planned_scores[3]={0U};unsigned used=0U,planned[3],capable[6]={0U};uint32_t covered=0U;'),
        ('if(read8(c,mon+0x34U+j) && (move==92U || move==73U))utility=1U;}',
         'if(read8(c,mon+0x34U+j) && (move==92U || move==73U))utility=1U;\n            if(move==269U && read8(c,mon+0x34U+j))capable[i]=1U;}'),
        ('''        fprintf(stderr,"CIRCUS_SUSTAIN_TEAM index=%u original_slot=%u score=%llu\\n",n,best,(unsigned long long)top);
        wx_cursor(c,best);sp_entry(c,n,best);
    }
}''','''        planned[n]=best;planned_scores[n]=top;
    }
    unsigned lead=ta_lead(read16(c,0x0203DB20U),planned,capable);
    bp_require(c,lead<3U,"Circus Taunt selection permutation");
    unsigned order[3],j=0U;order[j++]=lead;
    for(unsigned i=0;i<3U;++i)if(i!=lead)order[j++]=i;
    for(unsigned n=0;n<3U;++n){unsigned k=order[n],best=planned[k];
        fprintf(stderr,"CIRCUS_SUSTAIN_TEAM index=%u original_slot=%u score=%llu\\n",n,best,(unsigned long long)planned_scores[k]);
        wx_cursor(c,best);sp_entry(c,n,best);
    }
}'''),
        ('    bp_require(c,actual<4U,"Circus reentry selected slot");',
         '    actual=ta_move(c,actual);\n    bp_require(c,actual<4U,"Circus reentry selected slot");')]
    for old,new in changes:
        need(text.count(old)==1,'Taunt boundary differs: '+old[:70]);text=text.replace(old,new)
    return ('static unsigned ta_lead(unsigned,const unsigned[3],const unsigned[6]);\n'
        'static unsigned ta_move(struct mCore *c,unsigned);\n'+text+'\n'+(ROOT/HEADER).read_text())


def verify_prefix(events,raw):
    original_prefix(events,raw)
    old=probe.parse((ROOT/(RAW+'.stderr')).read_bytes())
    need(len(old)==79 and old[70]['label']=='returned' and old[70]['battle']==15,'fifteen-win return original absent')
    need(events[:71]==old[:71],'fifteen earned wins or returned party changed before Taunt boundary')


def configure():
    for key,value in dict(SELF=SELF,PROBE=previous.previous.previous.PROBE,TEST=TEST,WORKFLOW=WORKFLOW,REPORT=REPORT,TASK=TASK,
        OUT=OUT,FILES=FILES,PREFIX=previous.previous.previous.PREFIX,probe=probe,policy_text=policy_text,verify_prefix=verify_prefix).items():setattr(c,key,value)
    return c.configure()


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    loss['taunt_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_taunt_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30,
        previous_native_run=35429677248,previous_native_conclusion='failure',previous_observed_wins=15)
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    note='run35429677248/job105861895032は実15勝/45BP/16戦目敗北。79events/owner64/原party600/通常Save/fresh Continueはscoped PASS、真正30勝未達でActions failureを保持。新caseでは15勝後returnまで71events完全一致を要求し、受入単体を独立再実行しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['prior_actions_reconciled']=value['actions_reconciled']
    (ROOT/REPORT).write_bytes(stable(value));r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。候補310177固定・ROM変更0・ARM再link0・受入独立case再実行0。新caseのprefix15戦は不可避。第16戦の選出順と状態技対策のみ変更。3個体の構成を保持しTaunt持ちを先頭へ移動。PP消費を着弾や特性抑制の受入にしない。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'Taunt attempt exists; inspect original instead of replaying')
    old=resume.load(ROOT,OLD);run=r.api('actions/runs/35429677248')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='ddf42eb59a637c075be0051fb0f73b411f286bd2','previous Actions differs')
    need(old['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE' and old['recording_run']==35429677248
         and old['scoped_result']['wins']==15 and old['scoped_result']['losses']==1,'previous native differs')
    for path,bound in old['text_evidence'].items():need(identity((ROOT/path).read_bytes())==bound,'previous raw changed: '+path)
    for path,bound in old['native']['build_recipe']['source_bindings'].items():need(identity((ROOT/path).read_bytes())==bound,'runtime source changed: '+path)
    actions=[{k:run[k] for k in ('id','head_sha','status','conclusion')}]
    pending=resume.load(ROOT,resume.STATE)['pending_runs']
    for entry in pending:
        if entry['run_id']!=run['id']:
            actual=r.api('actions/runs/'+str(entry['run_id']));actions.append({k:actual[k] for k in ('id','head_sha','status','conclusion')})
    value=dict(schema_version=1,classification='CIRCUS_TAUNT_PREPARED',candidate=old['candidate'],target_wins=30,
        actions_reconciled=actions,host_tests=r.tests([Path(TEST).name]),
        inherited_run=dict(run_id=35429677248,job_id=105861895032,original_conclusion='failure',wins=15,losses=1,independently_replayed=False),
        accepted_native_cases_replayed=0,accepted_prefix_battles_reexecuted_for_continuation=15,independent_arm_links_replayed=0,
        genuine_30_wins_verified=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        input_policy_ja='15勝後returnまで入力保持。第6入場から既存rankの3体を維持してTaunt持ちのみ先頭へ移す。相手の使用可能状態技2個以上・HP1/4超で最大2回Tauntを通常入力し、PP消費後は3入力間隔を空ける。PP消費は着弾証明ではなく、最終勝敗/owner/保存の厳密検査を受入根拠にする。',
        predecessor_visual_review=dict(artifact_id=10580182476,artifact_sha256='17ae5af7b590581850862001fbb2c75b857526f99f45df85157076b929222d11',
            screens=['streak-74-action','streak-75-outcome','streak-77-returned','streak-78-saved','streak-79-reloaded'],
            observation_ja='第16戦の実actionと敗北、受付前への元party復帰・Save・fresh Continueの同位置描画を確認。通常交代2回後に相手残HP7で敗北。30勝/特性抑制の受入にはしない。'))
    checkpoint(value,'PREPARED','通常交代2回の実個体照合と15勝/45BP/保存復元を照合。第16戦は最後の敵HP7で敗北。正規選出3体は維持してTaunt持ちを先発へ移し、未使用状態技の最大2回入力を追加。')


def reconstruct():configure();c.reconstruct()
def native():configure();c.native()


def finish():
    configure();value=json.loads((ROOT/REPORT).read_bytes());value['classification']='CIRCUS_TAUNT_DIAGNOSTIC_OPEN'
    report=OUT/'native/report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['scoped_result']=json.loads((OUT/'native/streak.json').read_bytes())
            value['genuine_30_wins_verified']=value['scoped_result']['genuine_30_wins_verified']
            value['classification']='CIRCUS_TAUNT_GENUINE_30_WINS_90BP_VERIFIED' if value['genuine_30_wins_verified'] else 'CIRCUS_TAUNT_FIRST_LOSS_SAVE_VERIFIED_TARGET_OPEN'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False;value['text_evidence']={}
    prefix='evidence/pr16_circus_taunt/'+os.environ['GITHUB_RUN_ID']+'/'
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name in ('report.json','events.json',probe.CASE+'.stdout',probe.CASE+'.stderr',probe.CASE+'.process.json','streak.json','reconstruction.json'):
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
            name=prefix+p.relative_to(OUT).as_posix();target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw);value['text_evidence'][name]=identity(raw)
    result=value.get('scoped_result',{})
    checkpoint(value,'RECORDED','Taunt先発・対状態技入力後の連続入場を記録: 実勝数'+str(result.get('wins','未確定'))+'。勝敗/報酬/保存の実測と真正30勝ゲートを分離。最初の未解決停止から続ける。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action=='pack':configure();c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
