#!/usr/bin/env python3
"""Issue19: 原本に固定した通常level-up/進化UIの限定実測と追記記録。

ふしぎなアメは通常Bag入口を通す。初期個体生成/戦闘EXPとは区別する。
保存済みROMだけを復元し、旧host/ARM/native/Wiki生成は呼ばない。
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_learnset_gameplay as m
BASE=m.BASE
TASK='USER-20260923-LEARNSET-PROGRESSION'
SELF='scripts/pr16_learnset_progression.py'
C='tools/mgba_pr16_learnset_progression.c'
TEST='tests/test_pr16_learnset_progression.py'
WORKFLOW='.github/workflows/pr16-learnset-progression.yml'
CODE={SELF,C,TEST,WORKFLOW}
CP=BASE+'pr16_learnset_progression_checkpoint.json'
GUIDE='docs/PR16_LEARNSET_PROGRESSION_JA.md'
EVIDENCE=BASE+'pr16_learnset_progression_evidence'
WORK=ROOT/'.local/pr16-learnset-progression'
PROOF=WORK/'proof'
SCOPE='ISSUE19_CANDY_LEVELUP_EVOLUTION_SAVE_CONTINUE'
NEXT='Issue19: 保存された通常Bagアメlevel-up/進化の成功ケースは再実行しない。未成功caseだけ修復し、完了後は自然生成の初期技・戦闘EXP由来level-upの変更影響へ。Bag23/通常戦闘/条件付きタマゴ8/代表画面/Wiki/旧4hook/ARM/PLA1/PLC2は不変・再実行しない。全owner/Issue19/release/baseline切替は未完。'
need=m.need
identity=m.identity
load=m.load
write=m.write
LEVELS={649:[(33,1),(81,1),(535,9)],413:[(106,1)],414:[(16,1),(33,1),(81,1),(106,1),(535,1),(48,4),(93,8),(77,12),(78,12),(79,12),(60,16),(18,20),(373,24),(219,28),(375,32),(554,36),(537,40),(497,44)]}
EVOLUTIONS={649:[],413:[106],414:[16]}
SPECIES={649:'SPECIES_KEY_CATERPIE',413:'SPECIES_KEY_METAPOD',414:'SPECIES_KEY_BUTTERFREE'}
# name, owner, old level, target owner, 0=replace/1=refuse/2=summary cancel,
# selected slot, 0=no evolution/1=cancel evolution/2=accept evolution, fixture moves.
CASES=(
 ('caterpie-empty',649,8,649,0,1,1,(33,81,0,0)),
 ('caterpie-replace',649,8,649,0,1,1,(33,81,45,52)),
 ('caterpie-refuse',649,8,649,1,1,1,(33,81,45,52)),
 ('caterpie-summary-cancel',649,8,649,2,1,1,(33,81,45,52)),
 ('caterpie-known',649,8,649,0,1,1,(33,535,45,52)),
 ('caterpie-below-level',649,7,649,0,1,1,(33,81,0,0)),
 ('caterpie-evolve-metapod',649,8,413,0,1,2,(33,81,0,0)),
 ('metapod-evolve-butterfree',413,9,414,0,1,2,(106,0,0,0)),
 ('butterfree-three-moves',414,11,414,0,1,0,(33,81,0,0)),
 ('butterfree-known-first',414,11,414,0,1,0,(77,81,0,0)),
 ('butterfree-refuse-three',414,11,414,1,1,0,(33,81,45,52)),
)
EMBEDDED=(('tools/mgba_modernization_p03_archive_ui_e2e.c','pr16_progression_archive.c'),
 ('tools/mgba_modernization_p03_fullslots_e2e.c','p03a_fullslots_embedded.c'),
 ('tools/mgba_modernization_p03_learning_e2e.c','p03_learning_embedded.c'),
 ('tools/mgba_modernization_p02_stage71_acceptance_smoke.c','p03_p02_embedded.c'))
WITNESS={'party','dialog','summary','selection','stop','begin','update','field','dialogs','selections','stops'}


def decode_span(raw,family):
    if family=='level_up':
        need(len(raw)>=3 and len(raw)%3==0 and raw[-3:]==b'\0\0\xff','level span terminator/alignment')
        pairs=list(struct.iter_unpack('<HB',raw[:-3]))
        need(all(0<mid<1063 and 1<=lv<=100 for mid,lv in pairs),'active level bounds')
        need(all(a[1]<=b[1] for a,b in zip(pairs,pairs[1:])),'source level ordering')
        return pairs
    need(family=='evolution' and len(raw)%2==0,'evolution span alignment')
    moves=[x[0] for x in struct.iter_unpack('<H',raw)]
    need(all(0<mid<1063 for mid in moves),'active evolution bounds')
    return moves


def simulate(known,pp,moves,mode,slot,canonical):
    need(len(known)==len(pp)==4 and mode in (0,1,2) and 0<=slot<4,'learning simulation shape')
    out=list(known);points=list(pp);trace={'dialogs':0,'selections':0,'stops':0}
    for mid in moves:
        need(type(mid) is int and 0<mid<1063 and 0<canonical[mid]<=64,'source move/PP')
        if mid in out:continue
        if 0 in out:at=out.index(0)
        else:
            trace['dialogs']+=1
            if mode in (0,2):trace['selections']+=1
            if mode in (1,2):trace['stops']+=1;continue
            at=slot
        out[at]=mid;points[at]=canonical[mid]
    return out,points,trace


def vectors(canonical):
    result=[]
    for name,sid,lv,target,mode,slot,evo,known in CASES:
        pp=[min(i+7,canonical[mid]) if mid else 0 for i,mid in enumerate(known)]
        regular=[mid for mid,level in LEVELS[sid] if level==lv+1]
        evolution=EVOLUTIONS[target] if evo==2 else []
        after,after_pp,counts=simulate(known,pp,regular+evolution,mode,slot,canonical)
        result.append(dict(name=name,species=sid,level=lv,target=target,mode=mode,slot=slot,evolution=evo,
            known=list(known),pp=pp,after=after,after_pp=after_pp,regular_moves=regular,evolution_moves=evolution,**counts))
    return result


def oracle(folder,rom):
    cp=load(ROOT/BASE/'pr16_learnset_payload_checkpoint.json');files=cp['summary']['files']
    index={}
    for name in ('consumer-index.jsonl','level_up.bin','evolution.bin'):
        need(identity((folder/name).read_bytes())==files[name],'locked source hash '+name)
    for raw in (folder/'consumer-index.jsonl').read_bytes().splitlines():
        r=json.loads(raw);key=r['species_id'],r['consumer'];need(key not in index,'duplicate source owner');index[key]=r
    audit={}
    for sid,key in SPECIES.items():
        for family,expected in (('level_up',LEVELS[sid]),('evolution',EVOLUTIONS[sid])):
            row=index[sid,family];need(row['species_key']==key and row['status']=='PAYLOAD_PREPARED_NOT_INSTALLED','unselected source owner')
            span=row['payload'];need(span['file']==family+'.bin','unexpected source file')
            data=(folder/span['file']).read_bytes();at,size=span['offset'],span['size']
            need(type(at) is int and type(size) is int and 0<=at<=at+size<=len(data),'source span bounds')
            raw=data[at:at+size];need(decode_span(raw,family)==expected,'explicit original rows changed')
            audit[str(sid)+'/'+family]={'row':row,'file':identity(data),'span':identity(raw),'decoded':expected}
    need(identity(rom)==m.CANDIDATE,'candidate identity')
    at=struct.unpack_from('<I',rom,0x1cc)[0]-0x08000000
    need(at==0x10421f4 and at+1063*12<=len(rom),'canonical PP root')
    pp={mid:rom[at+mid*12+4] for mid in range(1063)}
    vv=vectors(pp)
    for v in vv:need(all(0<pp[mid]<=64 for mid in v['known']+v['regular_moves']+v['evolution_moves'] if mid),'canonical PP bounds')
    return vv,{'source_spans':audit,'payload_source_head':cp['source_head'],'payload_artifact':cp['payload_artifact'],
       'source_expected_not_rom_call_oracle':True,'ordinary_and_evolution_rows_separate':True,
       'candy_only_not_battle_exp':True,'initial_party_creation_is_fixture':True}


def header(vv):
    arr=lambda a:'{'+','.join(map(str,a))+'}'
    rows=[]
    for v in vv:
        fields=[json.dumps(v['name'])]+[str(v[k]) for k in ('species','level','target','mode','slot','evolution')]
        fields += [arr(v[k]) for k in ('known','pp','after','after_pp')]
        fields += [str(v[k]) for k in ('dialogs','selections','stops')]
        rows.append('  {'+','.join(fields)+'},')
    return 'static const struct PCase P_CASES[] = {\n'+'\n'.join(rows)+'\n};\n'


def strict(pairs):
    value={}
    for k,v in pairs:need(k not in value,'duplicate native JSON key');value[k]=v
    return value


def expected(v):
    return {'schema_version':1,'status':'PASS','scope':SCOPE,'case':v['name'],'rom_sha256':m.CANDIDATE['sha256'],
       'species_before':v['species'],'species_after':v['target'],'level_before':v['level'],'level_after':v['level']+1,
       'moves_before':v['known'],'pp_before':v['pp'],'moves_after':v['after'],'pp_after':v['after_pp'],
       'save_counters':[2,3,3],'fresh_cores':2,'guarded_phases':3,'denied_host_write_apis':7,'party_bytes_preserved':100,
       'candy_consumed_and_persisted':True,'initial_party_item_progress_are_fixtures':True,'initial_creation_accepted':False,
       'battle_exp_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0,'mgba_version':'0.10.2'}


def validate(out,err,v):
    need(b'mGBA[' not in err and err.count(b'original core destroyed; new core normal Continue\n')==1,'native warning/core lifecycle')
    r=json.loads(out,object_pairs_hook=strict);e=expected(v);need(set(r)==set(e)|{'witness'},'native schema differs')
    for k,wanted in e.items():
        need(type(r[k]) is type(wanted) and r[k]==wanted,'native field '+k)
        if isinstance(wanted,list):need(all(type(x) is int for x in r[k]),'native array type '+k)
    t=r['witness'];need(set(t)==WITNESS and all(type(x) is int and 0<=x<=24000 for x in t.values()),'witness shape/bounds')
    need(0<t['party']<t['field'],'ordinary Bag/party/field missing')
    for k in ('dialogs','selections','stops'):need(t[k]==v[k],'UI count '+k)
    for count,first in (('dialogs','dialog'),('selections','selection'),('stops','stop')):
        need(bool(t[first])==bool(t[count]),'UI first/count inconsistency')
        if t[first]:need(t['party']<t[first]<t['field'],'UI/field order')
    if v['selections']:need(t['dialog']<=t['summary']<=t['selection']<t['field'],'summary order')
    else:need(t['summary']==0,'unexpected summary')
    if v['stops']:need(t['stop']>=(t['selection'] if v['mode']==2 else t['dialog']),'stop confirmation order')
    if v['evolution']:need(t['party']<t['begin']<t['update']<t['field'],'evolution scene order')
    else:need(t['begin']==t['update']==0,'unexpected evolution')
    if v['evolution'] and t['selection']:need(t['selection']<t['begin'],'ordinary learn/evolution ordering')
    # The native C prints four observed slots for fixture, post-scene, saved and continued.
    rows=re.findall(rb'^PROGRESSION observed species=(\d+) level=(\d+) slot=(\d+) move=(\d+) expected=(\d+) pp=(\d+) expected_pp=(\d+)$',err,re.M)
    need(len(rows)==16,'missing per-slot before/after/save/continue observations')
    for stage in range(4):
        for slot in range(4):
            sid,lv,at,mid,wanted,pp,wanted_pp=map(int,rows[stage*4+slot]);pre=stage==0
            need((sid,lv,at,mid,wanted,pp,wanted_pp)==(v['species'] if pre else v['target'],v['level']+int(not pre),slot,
                (v['known'] if pre else v['after'])[slot],(v['known'] if pre else v['after'])[slot],
                (v['pp'] if pre else v['after_pp'])[slot],(v['pp'] if pre else v['after_pp'])[slot]),'actual slot measurement mismatch')
    return r


def pending(vv,previous):
    if not previous:return vv,[]
    need(previous['candidate']==m.CANDIDATE,'prior candidate changed')
    saved={r['case']:r for r in previous['results']};need(len(saved)==len(previous['results']),'duplicate prior case')
    known={v['name']:v for v in vv};need(set(saved)<=set(known),'removed accepted case')
    for name,r in saved.items():
        need({k:r[k] for k in expected(known[name])}==expected(known[name]),'accepted vector changed; impact review required')
    return [v for v in vv if v['name'] not in saved],list(saved.values())


def reconcile_prior_actions():
    from pr16_wiki_reconcile import fetch
    cp=load(ROOT/BASE/'pr16_learnset_impact_completed_actions.json')
    result=[]
    for label,row in cp['completed'].items():
        run=fetch('actions/runs/'+str(row['run_id']))
        need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==row['source_head'] and run['path']==row['workflow'],'accepted Actions changed '+label)
        result.append({k:run[k] for k in ('id','path','head_sha','status','conclusion')})
    listing=fetch('actions/runs?branch='+m.BRANCH+'&per_page=100')
    recent=[{k:r[k] for k in ('id','path','head_sha','status','conclusion')} for r in listing['workflow_runs']]
    latest={}
    for r in recent:latest.setdefault(r['path'],r)
    for old in result:
        new=latest.get(old['path'],old)
        need(new['id']<=old['id'],'newer accepted-scope run requires reconciliation before native')
    return {'accepted_completed_runs':result,'recent_first_page':recent,'pagination_complete_claimed':False,
       'initial_head_ci_action_required_not_native_failure':35840463023}


def execute():
    from pr16_learnset_wiki_actions import current,acquire
    import pr16_learnset_battle as b
    head=current();need(not WORK.exists(),'working proof already exists')
    previous=load(ROOT/CP) if (ROOT/CP).exists() else None
    need(not previous or previous['status']!='PASS_SCOPED','accepted progression rerun prohibited')
    PROOF.mkdir(parents=True);oldproof=m.PROOF;m.PROOF=PROOF
    protected=(*m.PROTECTED,m.CP,b.CP,BASE+'pr16_learnset_egg_gameplay_checkpoint.json',BASE+'pr16_learnset_impact_completed_actions.json')
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,
       'status':'RUNNING','scope':SCOPE,'native_processes':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0,'accepted_test_reruns':0,
       'wiki_generations':0,'issue19_complete':False,'release_ready':False,'active_baseline_changed':False,'results':[],'failures':[],
       'protected_bindings':{p:identity((ROOT/p).read_bytes()) for p in protected},'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE},
       'next_step_ja':NEXT,'new_unit_tests':0,'inherited_unit_tests':0,'inherited_case_ids':[]}
    try:
        v['prior_actions']=reconcile_prior_actions()
        testhash=identity((ROOT/TEST).read_bytes())
        if previous and previous.get('tests_passed') and previous['source_bindings'][TEST]==testhash:
            v.update(tests_passed=True,inherited_unit_tests=previous['new_unit_tests']+previous['inherited_unit_tests'])
        else:
            _,err=m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_progression','-v'],'unit')
            match=re.search(rb'Ran (\d+) tests? in ',err);need(match and b'\nOK\n' in err,'unit completion')
            v.update(tests_passed=True,new_unit_tests=int(match[1]))
        b.WORK=WORK/'restore-root';b.WORK.mkdir();rom=b.restore()
        cp=load(ROOT/BASE/'pr16_learnset_payload_checkpoint.json');members=dict(cp['summary']['files'],**{'receipt.json':cp['proof_bindings']['receipt.json']})
        acquire(cp['payload_artifact'],cp['source_head'],WORK/'payload',members)
        vv,audit=oracle(WORK/'payload',rom);write(PROOF/'oracle.json',audit);write(PROOF/'vectors.json',vv)
        todo,inherited=pending(vv,previous);v['results']=inherited;v['inherited_case_ids']=[r['case'] for r in inherited]
        v['previous_checkpoint']=identity((ROOT/CP).read_bytes()) if previous else None
        need(todo,'no unfinished case')
        gen={}
        for i,(source,target) in enumerate(EMBEDDED):
            raw=(ROOT/source).read_text();text,n=re.subn(r'\bint\s+main\s*\(','int issue19_progression_old_'+str(i)+'(',raw);need(n==1,'embedded main mismatch')
            (WORK/target).write_text(text);gen[target]=identity(text.encode())
        text=header(vv);(WORK/'pr16_progression_vectors.h').write_text(text);gen['pr16_progression_vectors.h']=identity(text.encode())
        (PROOF/'executed-vectors.h').write_text(text)
        exe=WORK/'runner';dep=WORK/'dependencies.d'
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),C,'-lmgba','-o',str(exe)],'compile')
        need(not err,'compiler warning');v['host_compiles']=1;v['generated_sources']=gen;v['compiled_sources']={}
        for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(name);p=(p if p.is_absolute() else ROOT/p).resolve()
            if p.parent==WORK:need(identity(p.read_bytes())==gen[p.name],'generated dependency binding')
            else:v['compiled_sources'][p.relative_to(ROOT).as_posix()]=identity(p.read_bytes())
        seed=(ROOT/m.SEED).read_bytes();stamp=(ROOT/m.SEED).stat().st_mtime_ns;need(identity(seed)==m.SEED_ID,'seed identity')
        def one(case):
            name=case['name'];fixture=WORK/(name+'.srm');fixture.write_bytes(seed)
            try:
                out,err=m.run([str(exe),str(b.WORK/'candidate.gba'),str(fixture),m.CANDIDATE['sha256'],m.SEED_ID['sha256'],str(vv.index(case))],name,480)
                return validate(out,err,case),None
            except Exception as e:return None,{'case':name,'type':type(e).__name__,'error':str(e).replace(str(ROOT),'$REPO')}
        v['native_processes']=len(todo);write(PROOF/'verification.json',v)
        with ThreadPoolExecutor(max_workers=2) as pool:
            for f in as_completed([pool.submit(one,c) for c in todo]):
                result,error=f.result()
                if error:v['failures'].append(error)
                else:v['results'].append(result)
                write(PROOF/'verification.json',v)
        v['results'].sort(key=lambda r:r['case']);v['accepted_cases']=len(v['results']);v['fresh_cores']=sum(r['fresh_cores'] for r in v['results'] if r['case'] not in v['inherited_case_ids'])
        need(identity((b.WORK/'candidate.gba').read_bytes())==m.CANDIDATE and (ROOT/m.SEED).read_bytes()==seed and (ROOT/m.SEED).stat().st_mtime_ns==stamp,'readonly inputs changed')
        need(v['protected_bindings']=={p:identity((ROOT/p).read_bytes()) for p in protected},'accepted scope changed')
        need(not v['failures'] and v['accepted_cases']==len(vv),'unfinished native cases; preserve successful cases')
        v['status']='PASS_SCOPED'
    except Exception as e:
        v.update(status='FAIL',error_type=type(e).__name__,error=str(e).replace(str(ROOT),'$REPO'));raise
    finally:
        v['proof_bindings']={p.name:identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=oldproof


def owned():
    # Previous evidence files remain unchanged and must not be staged again.
    run=os.environ.get('GITHUB_RUN_ID','')
    dest=ROOT/EVIDENCE/run
    return CODE|{CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in dest.rglob('*') if p.is_file()}


def record():
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record source mismatch')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'duplicate public evidence');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_bytes().decode();need('\0' not in text,'binary proof')
        safe='\n'.join(s.rstrip() for s in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'private user path');(dest/p.name).write_text(safe)
    old=load(ROOT/CP) if (ROOT/CP).exists() else None
    v.update(public_evidence_path=dest.relative_to(ROOT).as_posix(),public_evidence_bindings={p.name:identity(p.read_bytes()) for p in dest.iterdir()},actions_completion_confirmed=False,
        previous_attempts=(old.get('previous_attempts',[])+[{'run_id':old['run_id'],'source_head':old['source_head'],'status':old['status'],'evidence':old['public_evidence_path']}]) if old else [])
    write(ROOT/CP,v);good=v['status']=='PASS_SCOPED'
    guide=f'# Issue19: 通常アメlevel-up・進化・保存再開\n\n候補 `{m.CANDIDATE["sha256"]}`、run{v["run_id"]} / source `{v["source_head"]}`。状態 `{v["status"]}`。\n\n11ケース: キャタピーの空き枠/置換/拒否/summary取消/既習得/閾値未満、キャタピー→トランセルとトランセル→バタフリー、バタフリー同level3行/先頭既習得/3行拒否。原本level/evolution spanを別々に照合し通常習得後の進化技順を検査。通常Bagアメ消費→習得/進化→通常Save→新coreのContinueで全100bytes・PP・道具消費を保持。\n\n開始個体/進行/道具はfixture。ふしぎなアメによるlevel-upは実操作だが戦闘EXP由来level-upや野生/配布の初期技生成ではない。3観測区間は7API書込barrier。区間外GetMonDataのCPU復元付き測定をnative gameplayの追加入口へ読み替えない。\n\n新unit {v["new_unit_tests"]} / 継承unit {v["inherited_unit_tests"]}、新native {v["native_processes"]}、今回成功fresh core {v.get("fresh_cores",0)}、累計成功{len(v["results"])}ケース。失敗原本と成功原本を保持し成功caseの単純再実行禁止。正本 `{CP}`。Actions終端は後続の記録限定照合で確定。\n\n## 次\n\n{NEXT}\n'
    (ROOT/GUIDE).write_text(guide);state=load(ROOT/m.STATE)
    state['learnset_progression']={k:v[k] for k in ('status','source_head','run_id','candidate','native_processes','issue19_complete','release_ready','actions_completion_confirmed')};state['learnset_progression'].update(path=CP,accepted_cases=[r['case'] for r in v['results']])
    state['observed_head']=v['source_head'];state['observed_head_semantics']='通常アメlevel-up/進化の追加実操作source。最終Actionsは後続で照合。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'in_progress','conclusion':None}],'reason_ja':'実測原本とpush/upload後のActions終端は別。未終端を成功にしない。'}
    state['bp']['current_stop']='Issue19: Bag23/戦闘/タマゴ8/代表画面を保持。通常アメlevel-up・進化11case '+v['status']+'、成功'+str(len(v['results']))+'。'
    state['bp']['next_step']=NEXT;state['next_action']=dict(state['next_action'],id='LEARNSET_PROGRESSION_COMPLETION' if good else 'LEARNSET_PROGRESSION_FAILURES_ONLY',goal_ja=NEXT,read_paths=[GUIDE,CP])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['do_not_repeat'].append('run'+str(v['run_id'])+'のprogression成功caseを保存し、後継は失敗caseだけ。新候補変更なしのBag23/戦闘/タマゴ8/代表画像/ARM/旧hostは再実行しない。')
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 通常アメlevel-up・進化UI\n- Version: issue19-progression-v1\n- Status: '+('DONE（限定11case、全体未完）' if good else 'BLOCKED（成功caseを保存し失敗だけ継続）')+f'\n- Summary: 原本spanに固定した通常level-up・既習得/拒否/取消・同level複数行と進化技。Save/fresh Continueで100bytes・PP・消費保持。\n- Files changed: 専用C/validator/新境界試験/限定Actions、checkpoint・text原本、専用guide・固定引継ぎMD/JSON・両ログ。\n- Verify: run{v["run_id"]} {v["status"]}、新unit {v["new_unit_tests"]} / 継承{v["inherited_unit_tests"]}、新native {v["native_processes"]}、累計成功{len(v["results"])}。ARM/ROM変更/Wiki/受入済みnative再実行0。\n- Commit: 同branchへ非force pushしreflected-head.txtにremote照合結果。\n- Network: 固定artifact/保存候補復元・最新Actions照合。初期個体生成/戦闘EXP/全owner/Issue19/releaseは未完。原本ROM/save新規追跡なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(log)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned()-CODE;g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths required');actions[sys.argv[1]]()
