#!/usr/bin/env python3
"""Issue19: 未受入の戦闘EXP進化承認/取消と控え共有を独立追記する。"""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_learnset_boundaries as x
need,identity,load,write=x.need,x.identity,x.load,x.write
ROOT=x.ROOT
TASK='USER-20260925-LEARNSET-EXP-EVOLUTION-SHARE'
SELF='scripts/pr16_exp_evolution_share.py'
C='tools/mgba_pr16_exp_evolution_share.c'
TEST='tests/test_pr16_exp_evolution_share.py'
WF='.github/workflows/pr16-exp-evolution-share.yml'
CP=x.m.BASE+'pr16_exp_evolution_share_checkpoint.json'
GUIDE='docs/PR16_EXP_EVOLUTION_SHARE_JA.md'
EVIDENCE=x.m.BASE+'pr16_exp_evolution_share_evidence'
WORK=ROOT/'.local/pr16-exp-evolution-share';PROOF=WORK/'proof'
OLD_CP,OLD_GUIDE=x.CP,x.GUIDE
FIRST_CP=x.m.BASE+'pr16_learnset_first_refuse_checkpoint.json'
FIRST_GUIDE='docs/PR16_LEARNSET_FIRST_REFUSE_JA.md'
CASES=(('metapod-exp-evolve',9,0,1,1,(53,106,0,0)),
       ('metapod-exp-cancel',9,1,1,1,(53,106,0,0)),
       ('butterfree-exp-share',43,2,1,1,(53,89,0,0)))
CODE={SELF,C,TEST,WF,x.SELF,'tools/pr16_exp_multilevel_trace.h',x.n.__file__.replace(str(ROOT)+'/', ''),x.n.p.__file__.replace(str(ROOT)+'/', '')}
STATUS='PASS_BATTLE_EXP_EVOLUTION_SHARE'
NEXT='Issue19: 戦闘EXP進化承認/B取消と控え共有EXP・通常Save/fresh Continueの3caseは限定受入済み。保存成功を再実行せず、次は未受入の自然配布/孵化/form、続いて釣り/隠し野生の特殊技順。旧EXP4/最初の質問拒否/アメ11/Bag23/egg8/野生初期技/旧host・ARM・Wikiは変更影響なし。全owner/Issue19/release/baseline切替は未完。'
BASE_RUN=x.m.run;BASE_SOURCES=x.n.sources
STAGES=('fixture','returned','saved','continued')


def vectors(pp):
    return [dict(name=name,level=level,mode=mode,slot=slot,min_delta=delta,moves=list(moves),
                 points=[pp[mid] if i==0 else min(7+i,pp[mid]) if mid else 0 for i,mid in enumerate(moves)])
            for name,level,mode,slot,delta,moves in CASES]


def original_sources(folder):
    """採用済みpayloadを読み、進化技をROM結果から逆算しない。"""
    rows,audit=BASE_SOURCES(folder);cp=load(ROOT/x.m.BASE/'pr16_learnset_payload_checkpoint.json')
    raw=(folder/'evolution.bin').read_bytes();need(identity(raw)==cp['summary']['files']['evolution.bin'],'evolution source hash')
    index={}
    for line in (folder/'consumer-index.jsonl').read_bytes().splitlines():
        r=json.loads(line);key=r['species_id'],r['consumer'];need(key not in index,'unique original consumer');index[key]=r
    spans={}
    for sid in (413,414):
        need(rows[sid]==x.n.p.LEVELS[sid],'fixed original level rows')
        r=index[sid,'evolution'];span=r['payload'];at,size=span['offset'],span['size']
        need(r['species_key']==x.n.p.SPECIES[sid] and r['status']=='PAYLOAD_PREPARED_NOT_INSTALLED' and span['file']=='evolution.bin','selected original evolution owner')
        need(type(at)is int and type(size)is int and 0<=at<=at+size<=len(raw),'evolution span bounds')
        decoded=x.n.p.decode_span(raw[at:at+size],'evolution');need(decoded==x.n.p.EVOLUTIONS[sid],'original evolution rows')
        spans[str(sid)]={'row':r,'span':identity(raw[at:at+size]),'decoded':decoded}
    audit['evolution']={'file':identity(raw),'spans':spans};return rows,audit


def expected(case,level,pp,spent,rows,reserve=False):
    need(type(level)is int and case['level']+1<=level<100,'native level delta')
    need(type(spent)is int and (spent==0 if reserve else 0<spent<case['points'][0]),'attack/reserve PP use')
    points=case['points'][:];points[0]-=spent
    eligible=[mid for mid,lv in (rows if case['mode']==2 else x.n.p.LEVELS[413]) if case['level']<lv<=level]
    if case['mode']==0:eligible+=x.n.p.EVOLUTIONS[414]
    moves,points,trace=x.n.p.simulate(case['moves'],points,eligible,0,case['slot'],pp)
    need(trace['selections']==0,'scope must not enter full-slot summary')
    return moves,points,eligible


def party_evidence(err,count):
    pattern=rb'^ESHARE_PARTY stage=(fixture|returned|saved|continued) count=(\d+) counter=(\d+) hex=([0-9a-f]+)$'
    records=re.findall(pattern,err,re.M)
    need(len(records)==err.count(b'ESHARE_PARTY ')==4,'exact party evidence')
    need([a.decode() for a,_,_,_ in records]==list(STAGES) and [int(c) for _,_,c,_ in records]==[2,2,3,3],'Save lifecycle')
    data=[]
    for _,n,_,hexed in records:
        need(int(n)==count and len(hexed)==200*count,'all party bytes present');data.append(bytes.fromhex(hexed.decode()))
    need(data[0]!=data[1] and data[1]==data[2]==data[3],'native change and full party persistence')
    for i in range(count):need(data[0][100*i:100*i+8]==data[1][100*i:100*i+8],'individual identity preserved')
    pattern=(rb'^ESHARE_MON stage=(fixture|returned|saved|continued) index=(\d+) species=(\d+) level=(\d+) xp=(\d+) hp=(\d+) maxhp=(\d+) held=(\d+) bonus=(\d+) moves=(\d+,\d+,\d+,\d+) pp=(\d+,\d+,\d+,\d+)$')
    records=re.findall(pattern,err,re.M)
    need(len(records)==err.count(b'ESHARE_MON ')==4*count,'all-mon observations')
    seen={}
    for stage,index,*values in records:
        key=stage.decode(),int(index);need(key not in seen and key[0] in STAGES and 0<=key[1]<count,'unique mon phase')
        names=('species','level','xp','hp','maxhp','held','bonus');v=dict(zip(names,map(int,values[:7])))
        v['moves']=[int(i) for i in values[7].split(b',')];v['pp']=[int(i) for i in values[8].split(b',')]
        b=data[STAGES.index(key[0])][100*key[1]:100*(key[1]+1)]
        need(b[84]==v['level'] and struct.unpack_from('<HH',b,86)==(v['hp'],v['maxhp']),'raw party/observation health agreement')
        need(0<v['hp']<=v['maxhp']<999 and v['held']==v['bonus']==0,'native health/owner slots')
        if key[0]=='fixture':need(v['hp']==v['maxhp'],'native generated starting health')
        seen[key]=v
    for i in range(count):need(seen['returned',i]==seen['saved',i]==seen['continued',i],'all field/getter persistence')
    return data,seen


def validate(out,err,case,rows,pp):
    r=json.loads(out,object_pairs_hook=x.n.p.strict);share=case['mode']==2;count=2 if share else 1;sid=414 if share else 413
    need(case in vectors(pp),'declared fixed vector')
    fixed={'schema_version':1,'status':'PASS','case':case['name'],'candidate_sha256':x.CANDIDATE['sha256'],
           'species_before':sid,'species_after':414 if case['mode']==0 else sid,'party_count':count,'level_before':case['level'],
           'guarded_phases':3,'denied_host_write_apis':7,'fresh_cores':2,'save_counters':[2,3,3],'party_preserved_bytes':100*count,
           'initial_party_exp_stats_progress_share_are_fixtures':True,'all_owners_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0}
    ints={'enemy_species','enemy_level','xp_before','xp_after','level_after','reserve_level_after','reserve_xp_after','boundary','encounter','pp_spent','level_frame','reserve_level_frame','returned','turns','walking_steps','enemy_hp_before','enemy_hp_min','outcome','evolution_begin','evolution_update','evolution_input_pulses','active_party_index_samples','reserve_battle_entries'}
    arrays={'moves_after','pp_after','reserve_moves_after','reserve_pp_after'}
    need(set(r)==set(fixed)|ints|arrays,'exact evolution/share schema')
    for k,v in fixed.items():need(type(r[k]) is type(v) and r[k]==v,'fixed '+k)
    need(all(type(r[k])is int for k in ints),'integer witnesses')
    for k in arrays:need(type(r[k])is list and len(r[k])==4 and all(type(v)is int for v in r[k]),'four integer slots')
    spent=case['points'][0]-r['pp_after'][0];moves,points,eligible=expected(case,r['level_after'],pp,spent,rows)
    need(r['moves_after']==moves and r['pp_after']==points,'lead original learning/PP')
    need(r['xp_before']==(case['level']+1)**3-1 and r['level_after']**3<=r['xp_after']<(r['level_after']+1)**3,'lead cubic EXP')
    need(0<r['boundary']<r['encounter']<r['pp_spent']<=r['level_frame']<r['returned']<100000,'battle/EXP chronology')
    need(1<=r['turns']<=8 and spent<=2*r['turns'] and 0<r['walking_steps']<=400,'normal input bounds')
    need(0<r['enemy_species']<1671 and 1<=r['enemy_level']<=100 and r['enemy_hp_before']>0 and r['enemy_hp_min']==0 and r['outcome']==1,'native victory')
    need(r['active_party_index_samples']>0 and r['reserve_battle_entries']==0,'lead-only participation')
    data,mon=party_evidence(err,count)
    for i in range(count):
        first=mon['fixture',i];need(first['species']==sid and first['level']==case['level'] and first['xp']==r['xp_before'] and first['moves']==case['moves'] and first['pp']==case['points'],'initial fixture binding')
    last=mon['returned',0];need((last['species'],last['level'],last['xp'],last['moves'],last['pp'])==(r['species_after'],r['level_after'],r['xp_after'],moves,points),'lead raw/output binding')
    events=re.findall(rb'^ESHARE_EVOLUTION phase=(begin|update) frame=(\d+) callback=([0-9a-f]{8})$',err,re.M)
    pulses=re.findall(rb'^ESHARE_EVOLUTION_INPUT frame=(\d+) key=(\d+)$',err,re.M)
    need(len(events)==err.count(b'ESHARE_EVOLUTION phase=') and len(pulses)==err.count(b'ESHARE_EVOLUTION_INPUT '),'complete evolution raw evidence')
    if share:
        rm,rp,religible=expected(case,r['reserve_level_after'],pp,0,ROWS if False else rows,True)
        need(r['reserve_moves_after']==rm and r['reserve_pp_after']==rp,'nonparticipant original learning/PP')
        lv=r['reserve_level_after'];need(lv**3<=r['reserve_xp_after']<(lv+1)**3 and r['encounter']<r['reserve_level_frame']<r['returned'],'reserve EXP chronology')
        last=mon['returned',1];need((last['species'],last['level'],last['xp'],last['moves'],last['pp'])==(414,lv,r['reserve_xp_after'],rm,rp),'reserve raw/output binding')
        need(not events and not pulses and r['evolution_begin']==r['evolution_update']==r['evolution_input_pulses']==0,'no evolution in sharing case')
    else:
        religible=[];need(r['reserve_moves_after']==r['reserve_pp_after']==[0]*4 and r['reserve_level_after']==r['reserve_xp_after']==r['reserve_level_frame']==0,'no phantom reserve')
        need(events==[(b'begin',str(r['evolution_begin']).encode(),b'080cee71'),(b'update',str(r['evolution_update']).encode(),b'080cf869')],'exact native evolution callbacks')
        need(r['level_frame']<r['evolution_begin']<r['evolution_update']<r['returned'],'evolution after battle EXP')
        need(0<len(pulses)==r['evolution_input_pulses']<=1000,'evolution input witnesses')
        frames=[int(f) for f,_ in pulses];need(frames==sorted(set(frames)) and r['evolution_update']<=frames[0]<=frames[-1]<r['returned'],'evolution key chronology')
        need(all(int(key)==(2 if case['mode']==1 else 1) for _,key in pulses),'normal accept/cancel key')
    need(err.count(b'original core destroyed; new core normal Continue\n')==1 and b'FORBIDDEN' not in err and b'BOUNDARY_SELECTION' not in err,'fresh core/guard/summary')
    return dict(r,fixture=case,eligible_original_moves=eligible,reserve_eligible_original_moves=religible,initial_party=identity(data[0]),persisted_party=identity(data[1]),mon_observations={stage:[mon[stage,i] for i in range(count)] for stage in STAGES})


def scoped_run(command,name,*args,**kwargs):
    if name=='unit':command=[sys.executable,'-B','-m','unittest','tests.test_pr16_exp_evolution_share','-v']
    return BASE_RUN(command,name,*args,**kwargs)


def configure():
    x.CP,x.GUIDE,x.EVIDENCE,x.WORK,x.PROOF=CP,GUIDE,EVIDENCE,WORK,PROOF
    x.C,x.CODE,x.CASES,x.TASK,x.WF=C,CODE,CASES,TASK,WF
    x.vectors,x.validate,x.publish=vectors,validate,publish
    x.m.PROTECTED=tuple(dict.fromkeys((*x.m.PROTECTED,OLD_CP,OLD_GUIDE,FIRST_CP,FIRST_GUIDE,'tools/mgba_pr16_learnset_boundaries.c','tools/mgba_pr16_learnset_first_refuse.c')))
    x.m.run=scoped_run;x.n.sources=original_sources


def execute():
    old=load(ROOT/OLD_CP);first=load(ROOT/FIRST_CP)
    need(old['actions_completion_confirmed'] and len(old['accepted'])==4 and old['candidate']==x.CANDIDATE,'old EXP four completed')
    need(first['actions_completion_confirmed'] and len(first['accepted'])==1 and first['candidate']==x.CANDIDATE,'first refusal completed')
    if (ROOT/CP).exists():need(len(load(ROOT/CP)['accepted'])<len(CASES),'all saved successes: completion only')
    try:x.execute()
    finally:
        path=PROOF/'verification.json'
        if path.exists():
            v=load(path)
            v['status']={ 'PASS_BATTLE_EXP_BOUNDARIES':STATUS,'PARTIAL_BATTLE_EXP_BOUNDARIES':'PARTIAL_BATTLE_EXP_EVOLUTION_SHARE'}.get(v['status'],v['status'])
            v['inherited_acceptances']={p:{'identity':identity((ROOT/p).read_bytes()),'accepted_cases':sorted(load(ROOT/p)['accepted']),'native_reruns':0} for p in (OLD_CP,FIRST_CP)}
            try:
                from pr16_wiki_reconcile import fetch
                runs=fetch('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')['workflow_runs']
                v['observed_recent_actions']=[{k:r[k] for k in ('id','name','head_sha','path','status','conclusion')} for r in runs]
            except Exception as exc:v['actions_observation_error']=type(exc).__name__
            write(path,v)


def publish(v):
    from pr16_learnset_compact_record import publish_resume
    missing=[c[0] for c in CASES if c[0] not in v['accepted']];done=not missing and v['actions_completion_confirmed']
    next_step=NEXT if done else ('保存3case成功を再実行せずcompleteでActions終端・push・artifactだけ照合する。' if not missing else '今回の失敗原本を保持し未受入caseだけ修復する。保存成功caseと旧EXP4/最初の質問拒否/アメ11/Bag23/egg8は再実行しない。')
    (ROOT/GUIDE).write_text('# PR16 Issue19: 戦闘EXP進化と控え共有\n\n'+f"状態 `{v['status']}`。入力HEAD `{v['source_head']}`、run `{v['run_id']}`。Actions終端確認 `{v['actions_completion_confirmed']}`。\n\n"+
        f"候補 `{x.CANDIDATE['sha256']}` / 33554432 bytesは保存recipeを復元。ROM変更0、ARM0、旧受入native再実行0。\n\n"+
        'Metapodの戦闘EXP進化承認とB取消、2体Butterfreeの控え共有EXPを別processで検証。原本413/414のlevel/evolution表から期待技を求める。共有の開始flag・個体・EXP・能力・進行はfixtureであり、自然供給や通常UIでのEXP共有有効化の受入ではない。戦闘/進化・Save・fresh Continueの3区間で7書込APIを拒否。出場indexを毎frame観測し控え非出場、攻撃PPのみ消費、HP<=最大HP、全100/200byte保存を確認する。\n\n'+
        f"新unit {v['new_unit_tests']}、host compile {v['host_compiles']}、新native {v['native_processes']}。保存成功 {list(v['accepted'])}。未成功 {missing}。原本 `{EVIDENCE}/{v['run_id']}`。\n\n## 次の未完工程\n\n"+next_step+'\n')
    state=load(ROOT/x.m.STATE)
    state['learnset_exp_evolution_share']={k:v[k] for k in ('status','source_head','run_id','actions_completion_confirmed','new_unit_tests','host_compiles','native_processes','issue19_complete','release_ready')}
    state['learnset_exp_evolution_share'].update(path=CP,accepted_cases=list(v['accepted']),pending_cases=missing,accepted_native_reruns=0)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='戦闘EXP進化承認/取消と控え共有の限定追加。旧受入は不変。native原本とActions終端を区別。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'completed' if done else 'in_progress','conclusion':'success' if done else None}],'reason_ja':'一般CI action_requiredを成功に昇格しない。最新観測はcheckpointのobserved_recent_actions。'}
    state['bp']['current_stop']=f"Issue19: 戦闘EXP進化/共有 {len(v['accepted'])}/3。{v['status']}。Actions終端={done}、全体未完。";state['bp']['next_step']=next_step
    state['next_action']=dict(state['next_action'],id='LEARNSET_EXP_EVOLUTION_SHARE',goal_ja=next_step,read_paths=[GUIDE,CP,SELF,TEST])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    message='戦闘EXP進化/共有の保存成功を再実行しない。未受入caseのみ選び、全成功後のcompleteは記録だけ。'
    if message not in state['do_not_repeat']:state['do_not_repeat'].append(message)
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();status='DONE' if done else 'STOPPED' if not missing else 'BLOCKED'
    note=f"\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 戦闘EXP進化承認・取消・控え共有\n- Version: issue19-exp-evolution-share-v1\n- Status: {status}\n- Summary: {v['status']}、限定{len(v['accepted'])}/3。開始fixtureと通常入力区間を分離。全owner/Issue19未完。\n- Files changed: 専用driver/C/tests/workflow、CP/guide/証拠、固定MD/JSON、両ログ。\n- Verify: 新unit{v['new_unit_tests']} host compile{v['host_compiles']} native{v['native_processes']}。Actions終端={done}。記録終端照合のunit/native/host再実行0。ROM変更/ARM/変更影響なしの旧受入再実行0。\n- Commit: 同branchへの非force push。reflected-head.txtとremote ref照合。\n- Network: GitHub固定source/保存artifact/Actions。原本再採取・Wiki生成・release・baseline切替なし。一般CIのaction_requiredは限定nativeと別記録。\n"
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as out:out.write(note)


def complete():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();v=load(ROOT/CP);need(v['status']==STATUS and len(v['accepted'])==len(CASES) and not v['actions_completion_confirmed'],'saved full native success required')
    for path,binding in (v['source_bindings']|v.get('compiled_sources',{})).items():
        if path!=WF:need(identity((ROOT/path).read_bytes())==binding,'native source changed '+path)
    run=fetch('actions/runs/'+str(v['run_id']));need(run['head_sha']==v['source_head'] and run['head_branch']=='codex/modernization-followup-20260908' and run['path']==WF and run['status']=='completed' and run['conclusion']=='success','Actions terminal')
    jobs=fetch('actions/runs/'+str(v['run_id'])+'/jobs?per_page=100');need(jobs['total_count']==len(jobs['jobs'])==1,'one job');job=jobs['jobs'][0]
    need(job['conclusion']=='success' and all(s['conclusion'] in ('success','skipped') for s in job['steps']),'push/upload success')
    meta=fetch('actions/runs/'+str(v['run_id'])+'/artifacts?per_page=100');need(meta['total_count']==len(meta['artifacts'])==1,'one proof artifact');a=meta['artifacts'][0]
    need(a['name']=='pr16-exp-evolution-share-proof' and not a['expired'] and a['workflow_run']['head_sha']==v['source_head'],'proof source')
    raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True);need(identity(raw)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'archive identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist())==len(set(z.namelist())) and all('/' not in i.filename and i.file_size<2000000 for i in z.infolist()),'bounded unique text')
        saved=json.loads(z.read('verification.json'));need(saved['accepted']==v['accepted'] and saved['status']==STATUS and saved['candidate']==x.CANDIDATE,'raw success identity')
        for leaf,binding in saved['proof_bindings'].items():need(identity(z.read(leaf))==binding,'original proof '+leaf)
        for name,accepted in v['accepted'].items():
            if accepted['run_id']==v['run_id']:
                for suffix in ('.stdout.txt','.stderr.txt','.process.json'):
                    leaf=name+suffix;need(z.read(leaf)==(ROOT/EVIDENCE/str(v['run_id'])/leaf).read_bytes(),'saved native original')
        reflected=z.read('reflected-head.txt').decode().strip();need(re.fullmatch('[0-9a-f]{40}',reflected) and subprocess.run(['git','merge-base','--is-ancestor',reflected,'HEAD'],cwd=ROOT).returncode==0,'reflection ancestor')
    v['actions_completion_confirmed']=True
    v['completed_actions']={'run_id':v['run_id'],'job_id':job['id'],'reflected_head':reflected,'artifact':{k:a[k] for k in ('id','name','size_in_bytes','digest')},'verified_at_head':os.environ['GITHUB_SHA'],'native_reruns':0,'unit_reruns':0,'host_compiles':0,'arm_compiles':0}
    write(ROOT/CP,v);publish(v);PROOF.mkdir(parents=True,exist_ok=True);write(PROOF/'completed-actions.json',v['completed_actions'])


if __name__=='__main__':
    configure();actions={'execute':execute,'record':x.record,'complete':complete,'guard':x.guard,'paths':lambda:print('\n'.join(sorted(x.owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
