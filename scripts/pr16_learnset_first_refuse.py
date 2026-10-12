#!/usr/bin/env python3
"""Issue19: 戦闘EXPの最初の質問でB拒否。旧4成功を不変のまま継承。"""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_exp_health_policy as health_policy
x=health_policy.x
need,identity,load,write=x.need,x.identity,x.load,x.write
ROOT=x.ROOT
TASK='USER-20260925-LEARNSET-FIRST-REFUSE'
SELF='scripts/pr16_learnset_first_refuse.py'
C='tools/mgba_pr16_learnset_first_refuse.c'
TEST='tests/test_pr16_learnset_first_refuse.py'
WF='.github/workflows/pr16-learnset-first-refuse.yml'
CP=x.m.BASE+'pr16_learnset_first_refuse_checkpoint.json'
GUIDE='docs/PR16_LEARNSET_FIRST_REFUSE_JA.md'
EVIDENCE=x.m.BASE+'pr16_learnset_first_refuse_evidence'
WORK=ROOT/'.local/pr16-learnset-first-refuse'
PROOF=WORK/'proof'
OLD_CP=x.CP
OLD_GUIDE=x.GUIDE
OLD_C=x.C
CASES=(('butterfree-exp-first-refuse',43,1,1,1,(53,89,33,45)),)
CODE={SELF,C,TEST,WF,x.SELF,OLD_C,health_policy.SELF,health_policy.g.SELF,health_policy.g.TRACE}
NEXT='Issue19: 最初の質問でB拒否/中止確認/Save/fresh Continueは限定受入済み。旧EXP4境界と今回成功を再実行せず、次は戦闘EXP進化/共有を限定追加する。その後は未受入の自然配布/孵化/form、釣り/隠し野生の特殊技順。アメ11/Bag23/egg8/野生初期技/EXP空き枠/旧host・ARM・Wikiは変更影響なし。全owner/Issue19/release/baseline切替は未完。'
STATUS='PASS_BATTLE_EXP_FIRST_REFUSAL'
BASE_RUN=x.m.run


def vectors(pp):
    return [dict(name=CASES[0][0],level=43,mode=1,slot=1,min_delta=1,
                 moves=[53,89,33,45],points=[pp[53],min(8,pp[89]),min(9,pp[33]),min(10,pp[45])])]


def validate(out,err,case,rows,pp):
    r=json.loads(out,object_pairs_hook=x.n.p.strict)
    fixed={'schema_version':1,'status':'PASS','case':CASES[0][0],'candidate_sha256':x.CANDIDATE['sha256'],
           'level_before':43,'level_after':44,'guarded_phases':3,'denied_host_write_apis':7,'fresh_cores':2,
           'save_counters':[2,3,3],'party_preserved_bytes':100,'initial_party_exp_stats_progress_are_fixtures':True,
           'all_owners_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0,
           'summaries':0,'selections':0,'summary_frame':0,'selection_frame':0,'summary_never_opened':True,
           'refusal_opcode':90,'stop_opcode':91}
    ints={'enemy_species','enemy_level','xp_before','xp_threshold','xp_after','boundary','encounter','pp_spent',
          'level_frame','returned','turns','walking_steps','enemy_hp_before','enemy_hp_min','outcome',
          'first_refusal_pulses','stop_confirmation_pulses','first_refusal_frame','stop_confirmation_frame'}
    need(set(r)==set(fixed)|ints|{'moves_after','pp_after'},'exact first-refusal schema')
    need(case==vectors(pp)[0],'fixed first-refusal vector')
    for k,v in fixed.items():need(type(r[k]) is type(v) and r[k]==v,'result field '+k)
    need(all(type(r[k]) is int for k in ints),'integer witness fields')
    for k in ('moves_after','pp_after'):
        need(type(r[k]) is list and len(r[k])==4 and all(type(v) is int for v in r[k]),'four integer slots')
    eligible=[mid for mid,lv in rows if 43<lv<=44]
    need(eligible==[497] and r['moves_after']==case['moves'],'original single refused move; stored four unchanged')
    need(r['pp_after'][1:]==case['points'][1:] and 0<r['pp_after'][0]<case['points'][0],'unused PP retained; attack PP spent')
    need(r['xp_before']==44**3-1 and r['xp_threshold']==44**3 and 44**3<=r['xp_after']<45**3,'native EXP curve')
    need(0<r['boundary']<r['encounter']<r['pp_spent']<=r['level_frame']<r['first_refusal_frame']<r['stop_confirmation_frame']<r['returned']<100000,'first/stop native chronology')
    need(1<=r['turns']<=8 and case['points'][0]-r['pp_after'][0]<=2*r['turns'] and 0<r['walking_steps']<=400,'ordinary input bounds')
    need(0<r['enemy_species']<1671 and 1<=r['enemy_level']<=100 and r['enemy_hp_before']>0 and r['enemy_hp_min']==0 and r['outcome']==1,'ordinary victory')
    pattern=rb'^FIRST_REFUSAL frame=(\d+) script=([0-9a-f]{8}) opcode=(\d+) key=(\d+) pending=(\d+)$'
    events=re.findall(pattern,err,re.M)
    need(len(events)==err.count(b'FIRST_REFUSAL '),'malformed question evidence')
    decoded=[(int(f),int(s,16),int(op),int(key),int(move)) for f,s,op,key,move in events]
    need(2<=len(decoded)<=16 and all(0x08000000<=s<0x0a000000 and move==497 for _,s,_,_,move in decoded),'question pointer/pending bounds')
    ask=[d for d in decoded if d[2]==90];stop=[d for d in decoded if d[2]==91]
    need(decoded==ask+stop and all(a[0]<b[0] for a,b in zip(decoded,decoded[1:])),'first question then stop, strictly ordered')
    need(1<=len(ask)<=8 and 1<=len(stop)<=8 and all(d[3]==2 for d in ask) and all(d[3]==1 for d in stop),'B first refusal and A confirmation only')
    need(len({d[1] for d in ask})==len({d[1] for d in stop})==1 and ask[0][1]!=stop[0][1],'two distinct native questions')
    need(len(ask)==r['first_refusal_pulses'] and len(stop)==r['stop_confirmation_pulses'] and ask[0][0]==r['first_refusal_frame'] and stop[0][0]==r['stop_confirmation_frame'] and stop[-1][0]<r['returned'],'raw/published question witness')
    need(b'BOUNDARY_SELECTION' not in err and b'FORBIDDEN' not in err,'summary/write evidence forbidden')
    parties=re.findall(rb'^NATURAL_PARTY stage=(fixture|returned|saved|continued) counter=(\d+) hex=([0-9a-f]{200})$',err,re.M)
    need([p[0] for p in parties]==[b'fixture',b'returned',b'saved',b'continued'] and [int(p[1]) for p in parties]==[2,2,3,3],'Save/Continue lifecycle')
    data=[bytes.fromhex(p[2].decode()) for p in parties]
    need(data[0][:8]==data[1][:8] and data[0]!=data[1] and data[1]==data[2]==data[3],'same individual and persisted native change')
    need(err.count(b'original core destroyed; new core normal Continue\n')==1,'fresh core')
    hp=health_policy.health(err,43,1);need(hp['status']=='PASS','healthy Save/Continue')
    return dict(r,eligible_original_moves=eligible,fixture=case,initial_party=identity(data[0]),persisted_party=identity(data[1]),native_health=hp,first_question_events=[list(d) for d in decoded])


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':command=[sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_first_refuse','-v']
    return BASE_RUN(command,name,*args,**kwargs)


def configure():
    x.CP,x.GUIDE,x.EVIDENCE,x.WORK,x.PROOF=CP,GUIDE,EVIDENCE,WORK,PROOF
    x.C,x.CODE,x.CASES,x.TASK,x.WF=C,CODE,CASES,TASK,WF
    x.vectors,x.validate,x.publish=vectors,validate,publish
    x.m.PROTECTED=tuple(dict.fromkeys((*x.m.PROTECTED,OLD_CP,OLD_GUIDE,OLD_C)))
    x.m.run=scoped_run


def execute():
    from pr16_wiki_reconcile import fetch
    old=load(ROOT/OLD_CP)
    need(old['status']=='PASS_BATTLE_EXP_BOUNDARIES' and old['actions_completion_confirmed'] and old['candidate']==x.CANDIDATE and len(old['accepted'])==4,'four accepted healthy boundaries')
    need(not (ROOT/CP).exists() or not load(ROOT/CP)['accepted'],'accepted first refusal: complete only; native/unit replay forbidden')
    for path in (x.SELF,OLD_C,health_policy.SELF,health_policy.g.SELF,health_policy.g.TRACE):
        need(identity((ROOT/path).read_bytes())==old['source_bindings'].get(path,old.get('compiled_sources',{}).get(path)),'accepted helper changed '+path)
    try:x.execute()
    finally:
        p=PROOF/'verification.json'
        if p.exists():
            v=load(p)
            if v['status']=='PASS_BATTLE_EXP_BOUNDARIES':v['status']=STATUS
            elif v['status']=='PARTIAL_BATTLE_EXP_BOUNDARIES':v['status']='PARTIAL_BATTLE_EXP_FIRST_REFUSAL'
            v['inherited_boundary_checkpoint']={'path':OLD_CP,'identity':identity((ROOT/OLD_CP).read_bytes()),'accepted_cases':sorted(old['accepted']),'native_reruns':0}
            # 最新Actionsを限定原本と別に記録。一般CIのaction_requiredを成功にしない。
            try:
                listing=fetch('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')
                v['observed_recent_actions']=[{k:r[k] for k in ('id','name','head_sha','path','status','conclusion')} for r in listing['workflow_runs']]
            except Exception as exc:v['recent_actions_query_error']=type(exc).__name__
            write(p,v)


def publish(v):
    from pr16_learnset_compact_record import publish_resume
    accepted=bool(v['accepted']);done=accepted and v['actions_completion_confirmed']
    next_step=NEXT if done else ('native成功を再実行せずcompleteでActions終端・push・artifact原本だけ照合する。' if accepted else '今回失敗原本を保持し、最初の質問での拒否だけ修復する。旧EXP4成功/アメ11/Bag23/egg8は再実行しない。')
    (ROOT/GUIDE).write_text('# PR16 Issue19: 最初の質問での拒否\n\n'+f"状態 `{v['status']}`。入力HEAD `{v['source_head']}`、run `{v['run_id']}`。Actions終端確認 `{v['actions_completion_confirmed']}`。\n\n"+
        f"候補 `{x.CANDIDATE['sha256']}` は保存recipeを復元。ROM変更0、ARM0、旧4境界native再実行0。\n\n"+
        'battle script 0x5aを観測して通常B、0x5bで通常A中止確認。技一覧summaryへ入った場合は失敗。Lv43→44、拒否技497、保存4技と未使用PP、攻撃PP消費、正常HP、Save counter2→3→3と100byteをfresh coreまで照合する。開始個体/EXP/能力/進行はfixture。\n\n'+
        f"新unit {v['new_unit_tests']}、host compile {v['host_compiles']}、新native process {v['native_processes']}。受入case {list(v['accepted'])}。失敗 {v['failures']}。原本 `{EVIDENCE}/{v['run_id']}`。終端照合時のunit/native/host再実行は0。\n\n"+
        '旧受入の `pr16_learnset_boundaries_checkpoint.json` とguideは不変。first-question refusalをsummary-B拒否で代用せず、今回1caseを全owner/進化/共有EXP/自然供給の証明にしない。\n\n## 次の未完工程\n\n'+next_step+'\n')
    state=load(ROOT/x.m.STATE)
    state['learnset_first_refusal']={k:v[k] for k in ('status','source_head','run_id','actions_completion_confirmed','new_unit_tests','host_compiles','native_processes','issue19_complete','release_ready')}
    state['learnset_first_refusal'].update(path=CP,accepted_cases=list(v['accepted']),accepted_native_reruns=0)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='最初の質問でB拒否の限定追加。旧4境界は不変。native成功とActions終端を区別。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'completed' if done else 'in_progress','conclusion':'success' if done else None}],'reason_ja':'限定nativeと一般CIを分離。最新観測はcheckpointのobserved_recent_actions。'}
    state['bp']['current_stop']=f"Issue19: 最初の質問でB拒否 {v['status']}。Actions終端確認={done}。旧EXP4成功は不変、全体未完。"
    state['bp']['next_step']=next_step
    state['next_action']=dict(state['next_action'],id='LEARNSET_EXP_FIRST_REFUSAL',goal_ja=next_step,read_paths=[GUIDE,CP,SELF,TEST])
    for path in CODE|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    message='旧EXP4境界と最初の質問での拒否は各checkpointの保存成功を再実行しない。未受入の戦闘EXP進化/共有以降だけ追加する。'
    if message not in state['do_not_repeat']:state['do_not_repeat'].append(message)
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 最初の質問でB拒否\n- Version: issue19-first-refusal-v1\n- Status: '+('DONE' if done else 'STOPPED' if accepted else 'BLOCKED')+f"\n- Summary: {v['status']}。B拒否→A中止確認、summary非到達、正常HP/保存4技/PP/Save/fresh Continueの限定1case。旧4成功と履歴を保全。全owner/Issue19未完。\n- Files changed: 専用driver/C/tests/workflow・CP/guide/原本、固定MD/JSON、両ログ。\n- Verify: 新unit{v['new_unit_tests']}、host compile{v['host_compiles']}、native{v['native_processes']}。旧受入native/unit、ARM、ROM変更、Wiki生成0。Actions終端確認={done}。complete時は再実行0。\n- Commit: 同branchへ非force pushしremoteとreflected-head.txtを照合。\n- Network: GitHub固定source/保存artifact/Actions。事前source転送WIP 5078bd7/run36070267613（native/unit0）。参照: CFRU-JP e24a16fe39e27ae162faf5b78596d1f3df18489d battle_script_macros.s, assembly/data/battle_script_commands_table.s, include/new/ram_locs_battle.h。source-lock変更なし。merge/release/baseline切替なし。\n"
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(note)


def complete():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();v=load(ROOT/CP)
    need(v['status']==STATUS and not v['actions_completion_confirmed'] and set(v['accepted'])=={CASES[0][0]},'pending first-refusal success')
    run=fetch('actions/runs/'+str(v['run_id']))
    need(run['head_sha']==v['source_head'] and run['head_branch']=='codex/modernization-followup-20260908' and run['path']==WF and run['status']=='completed' and run['conclusion']=='success','source Actions terminal')
    jobs=fetch('actions/runs/'+str(v['run_id'])+'/jobs?per_page=100')
    need(jobs['total_count']==len(jobs['jobs'])==1,'one native source job');job=jobs['jobs'][0]
    need(job['conclusion']=='success' and all(s['conclusion'] in ('success','skipped') for s in job['steps']),'native record/push/upload success')
    meta=fetch('actions/runs/'+str(v['run_id'])+'/artifacts?per_page=100')
    need(meta['total_count']==len(meta['artifacts'])==1,'one proof artifact');a=meta['artifacts'][0]
    need(a['name']=='pr16-learnset-first-refuse-proof' and not a['expired'] and a['workflow_run']['head_sha']==v['source_head'],'proof source')
    raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True)
    need(identity(raw)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'archive identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist())==len(set(z.namelist())) and all('/' not in i.filename and i.file_size<2_000_000 for i in z.infolist()),'bounded unique text members')
        saved=json.loads(z.read('verification.json'))
        need(saved['candidate']==v['candidate'] and saved['accepted']==v['accepted'] and saved['source_head']==v['source_head'] and saved['run_id']==v['run_id'] and saved['status']==STATUS,'source proof identity')
        for leaf,binding in saved['proof_bindings'].items():need(identity(z.read(leaf))==binding,'original proof '+leaf)
        for suffix in ('.stdout.txt','.stderr.txt','.process.json'):
            leaf=CASES[0][0]+suffix;need(z.read(leaf)==(ROOT/EVIDENCE/str(v['run_id'])/leaf).read_bytes(),'saved native original unchanged')
        reflected=z.read('reflected-head.txt').decode().strip()
        need(re.fullmatch('[0-9a-f]{40}',reflected) and subprocess.run(['git','merge-base','--is-ancestor',reflected,'HEAD'],cwd=ROOT).returncode==0,'reflection ancestor')
    v['actions_completion_confirmed']=True
    v['completed_actions']={'run_id':v['run_id'],'job_id':job['id'],'reflected_head':reflected,'artifact':{k:a[k] for k in ('id','name','size_in_bytes','digest')},'verified_at_head':os.environ['GITHUB_SHA'],'native_reruns':0,'unit_reruns':0,'host_compiles':0,'arm_compiles':0}
    write(ROOT/CP,v);publish(v);PROOF.mkdir(parents=True,exist_ok=True);write(PROOF/'completed-actions.json',v['completed_actions'])


if __name__=='__main__':
    configure()
    actions={'execute':execute,'record':x.record,'complete':complete,'guard':x.guard,'paths':lambda:print('\n'.join(sorted(x.owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
