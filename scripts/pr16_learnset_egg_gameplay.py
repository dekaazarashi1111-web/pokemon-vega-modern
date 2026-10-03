#!/usr/bin/env python3
"""Issue19 changed egg pools: ordinary daycare, hatch, egg/hatched Save/Continue.

Only parent individuals/map are fixtures. Accepted old ROM probes, Bag, battle,
Wiki and ARM builds are not executed. Explicit source rows are the move oracle.
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
TASK='USER-20260923-LEARNSET-EGG-GAMEPLAY'
WORK=ROOT/'.local/pr16-learnset-egg-gameplay'
PROOF=WORK/'proof'
CP=BASE+'pr16_learnset_egg_gameplay_checkpoint.json'
GUIDE='docs/PR16_LEARNSET_EGG_GAMEPLAY_JA.md'
EVIDENCE=BASE+'pr16_learnset_egg_gameplay_evidence'
SELF='scripts/pr16_learnset_egg_gameplay.py'
TEST='tests/test_pr16_learnset_egg_gameplay.py'
WORKFLOW='.github/workflows/pr16-learnset-egg-gameplay.yml'
CODE={SELF,TEST,WORKFLOW}
PARENT='tools/mgba_modernization_p03_breeding_e2e.c'
PARENT_HASH='a99cafd942f958c932709bed6099695f067dc292401b3bfb91e60afe4d6823de'
SCOPE='ISSUE19_CONDITIONAL_EGG_DAYCARE_HATCH_SAVE_CONTINUE'
# name, father moves, mother moves, father/mother held items, mother species,
# child species, egg cycles, expected ordered four moves. Not a ROM-call oracle.
CASES=(
 ('lightball-father',(175,440,33,0),(273,45,0,0),202,0,25,24,10,(84,175,273,344)),
 ('lightball-mother',(175,33,0,0),(273,440,0,0),0,202,25,24,10,(84,175,273,344)),
 ('no-lightball-removed',(344,440,33,0),(344,440,45,0),0,0,25,24,10,(39,84,0,0)),
 ('lightball-only-removed',(440,33,0,0),(45,440,0,0),202,0,25,24,10,(39,84,344,0)),
 ('duplicate-full-control',(175,273,0,0),(175,273,0,0),0,0,25,24,10,(39,84,175,273)),
 ('mother-incense-eligible',(84,39,0,0),(69,461,464,357),0,862,365,364,40,(1,539,69,0)),
 ('father-incense-removed',(84,39,0,0),(461,464,357,0),862,0,365,364,40,(1,539,0,0)),
 ('no-incense-control',(84,39,0,0),(461,464,357,0),0,0,365,365,40,(204,343,539,549)),
)
BY_NAME={v[0]:v for v in CASES}
LEVELS={24:[39,84],364:[1,539],365:[1,111,186,204,343,539,549]}
EGGS={24:[175,217,252,268,273,321,549],364:[69,215,217,716],365:[]}
EMBEDDED=(('tools/mgba_modernization_p03_archive_ui_e2e.c','p03b_archive_embedded.c'),
 ('tools/mgba_modernization_p03_fullslots_e2e.c','p03a_fullslots_embedded.c'),
 ('tools/mgba_modernization_p03_learning_e2e.c','p03_learning_embedded.c'),
 ('tools/mgba_modernization_p02_stage71_acceptance_smoke.c','p03_p02_embedded.c'))
WITNESS=('deposit_menu','first_deposit','second_deposit','generated','claim_menu','claimed','egg_saved','egg_reloaded','hatch_begin','nickname','hatch_end','hatch_saved','hatch_reloaded')
NEXT='Issue19: 条件付きタマゴの8ケースは保存原本/最新Actionsから判定し、成功ケースを繰り返さない。次はBag一覧/summary撮影の限定修復と、未受入consumerの変更影響を絞る。Bag23/通常戦闘/Wiki/4hook/ARM/PLA1/PLC2の再実行禁止。'
need=m.need
identity=m.identity
write=m.write
load=m.load


def once(text,before,after):
    need(text.count(before)==1,'controller preimage not unique')
    return text.replace(before,after,1)


def controller(raw):
    need(hashlib.sha256(raw).hexdigest()==PARENT_HASH,'pinned daycare controller changed')
    text=raw.decode();pattern=r'static const struct BCase b_cases\[\] = \{\n.*?\n\};'
    blocks=re.findall(pattern,text,re.S);need(len(blocks)==1,'case block differs')
    arr=lambda v:'{'+','.join(map(str,v))+'}'
    rows=['    {"'+n+'", '+arr(f)+', '+arr(moves)+','+str(fi)+','+str(mi)+','+arr(child)+','+str(ms)+','+str(cs)+','+str(cycles)+'},'
          for n,f,moves,fi,mi,ms,cs,cycles,child in CASES]
    changes=[(blocks[0],'static const struct BCase b_cases[] = {\n'+'\n'.join(rows)+'\n};'),
      ('unsigned father[4], mother[4], father_item, mother_item, child[4];','unsigned father[4], mother[4], father_item, mother_item, child[4], mother_species, child_species, cycles;'),
      ('#define B_SCOPE "P03_DAYCARE_INHERITANCE_HATCH_SAVE_RELOAD"','#define B_SCOPE "'+SCOPE+'"'),
      ('#define B_ROM_SHA "e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d"','#define B_ROM_SHA "'+m.CANDIDATE['sha256']+'"'),
      ('static void b_create(struct mCore *c,unsigned dst,unsigned pid,unsigned ot)','static void b_create(struct mCore *c,unsigned dst,unsigned species,unsigned pid,unsigned ot)'),
      ('BATTLE_CORE_CREATE_MON,dst,25U,20U,31U','BATTLE_CORE_CREATE_MON,dst,species,20U,31U'),
      ('b_data(c,dst,11U)==25U','b_data(c,dst,11U)==species'),
      ('b_create(c,QOL_PLAYER_PARTY,0x123456F0U,0x11223344U)','b_create(c,QOL_PLAYER_PARTY,25U,0x123456F0U,0x11223344U)'),
      ('b_create(c,QOL_PLAYER_PARTY+100U,0x34567801U,0x99887766U)','b_create(c,QOL_PLAYER_PARTY+100U,v->mother_species,0x34567801U,0x99887766U)'),
      ('b_data(c,B_CHILD,11U)==24U','b_data(c,B_CHILD,11U)==v->child_species'),
      ('initial_cycles==10U,"Pichu native egg cycles changed"','initial_cycles==v->cycles,"source-bound egg cycles changed"'),
      ('z<8192U && !b_hatched','z<12288U && !b_hatched'),
      ('printf("\\"child_species\\":24,\\"child_level\\":1,\\"moves\\":");','printf("\\"child_species\\":%u,\\"child_level\\":1,\\"moves\\":",v->child_species);'),
      ('#include "p03b_archive_embedded.c"','#include "p03b_archive_embedded.c"\n#include <mgba/core/version.h>'),
      ('if(argc!=6)return 2;','if(argc!=6)return 2;\n    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version mismatch");')]
    for before,after in changes:text=once(text,before,after)
    need(text.count('a_guard(c);')==raw.decode().count('a_guard(c);'),'observation guard changed')
    return text


def source_moves(raw,sid,family):
    if family=='egg':
        need(len(raw)>=2 and len(raw)%2==0,'egg span alignment')
        values=[x[0] for x in struct.iter_unpack('<H',raw)]
        need(values[0]==20000+sid,'egg source owner')
        values=values[1:]
        if values and values[-1]==65535:values.pop()
    else:
        need(family=='level_up' and raw.endswith(b'\0\0\xff') and len(raw)%3==0,'level source terminator')
        pairs=list(struct.iter_unpack('<HB',raw[:-3]));need(all(1<=l<=100 for _,l in pairs),'source level bounds')
        values=[x for x,level in pairs if level==1]
    need(all(type(x) is int and 1<=x<1063 for x in values),'source active move bounds')
    return values


def inherited(case,levels,eggs):
    _,father,mother,fi,mi,_,child,_,_=case
    out=list(dict.fromkeys(levels))[-4:]
    for move in (*father,*mother):
        if move and move in eggs and move not in out:out=(out+[move])[-4:]
    if child==24 and 202 in (fi,mi) and 344 not in out:out=(out+[344])[-4:]
    return tuple((out+[0]*4)[:4])


def oracle(folder,rom):
    idx={}
    for line in (folder/'consumer-index.jsonl').read_bytes().splitlines():
        row=json.loads(line);key=row['species_id'],row['consumer'];need(key not in idx,'duplicate source owner');idx[key]=row
    sources={}
    for sid in LEVELS:
        for family,expected in (('level_up',LEVELS[sid]),('egg',EGGS[sid])):
            row=idx[sid,family];need(row['status']=='PAYLOAD_PREPARED_NOT_INSTALLED','unselected owner')
            span=row['payload'];name=span['file'];need(Path(name).name==name,'source span path')
            pool=(folder/name).read_bytes();at,size=span['offset'],span['size']
            need(type(at) is int and type(size) is int and 0<=at<=at+size<=len(pool),'source span bounds')
            raw=pool[at:at+size];need(source_moves(raw,sid,family)==expected,'independent source rows changed')
            sources[str(sid)+'/'+family]={'row':row,'pool':identity(pool),'span':identity(raw),'moves':expected}
    pp_root=struct.unpack_from('<I',rom,0x1cc)[0]-0x08000000
    need(pp_root==0x10421f4,'canonical PP root changed')
    pp={0:0}
    for move in {move for c in CASES for move in c[-1] if move}:pp[move]=rom[pp_root+move*12+4];need(0<pp[move]<=64,'canonical PP bounds')
    for c in CASES:need(inherited(c,LEVELS[c[6]],EGGS[c[6]])==c[-1],'explicit case/source/condition disagreement')
    need(344 not in EGGS[24] and 440 not in EGGS[24] and all(x not in EGGS[364] for x in (461,464,357)),'conditional/historical leakage')
    return {'source_spans':sources,'canonical_pp':pp,'light_ball_item':202,'luck_incense_item':862,'conditional_not_flattened':True},pp


def expected(name,pp):
    need(name in BY_NAME,'unknown case');_,_,_,fi,mi,_,sid,cycles,moves=BY_NAME[name]
    return {'schema_version':1,'status':'PASS','scope':SCOPE,'case':name,'rom_sha256':m.CANDIDATE['sha256'],
      'child_species':sid,'child_level':1,'moves':list(moves),'pp':[pp[x] for x in moves],'father_item':fi,'mother_item':mi,
      'ordinary_deposit':True,'ordinary_claim':True,'native_hatch':True,'egg_and_hatched_save_reload':True,'parent_queue_byte_identity':True,
      'fresh_cores':3,'manual_save_counter_delta':2,'native_hatch_save_counter_delta':1,'total_save_counter_delta':3,'host_write_barriers':7,
      'rtc_flash_bytes_preserved':131072,'initial_egg_cycles':cycles,'parent_fixture_only':True,'all_breeding_paths_accepted':False,
      'full_p03_acceptance':False,'release_ready':False,'warnings_errors':0}


def strict_pairs(pairs):
    out={}
    for key,value in pairs:need(key not in out,'duplicate JSON key');out[key]=value
    return out


def validate(stdout,stderr,name,pp):
    need(b'mGBA[' not in stderr and stderr.count(b'original core destroyed; new core boot and normal Continue')==2,'core lifecycle/warning evidence')
    r=json.loads(stdout,object_pairs_hook=strict_pairs);e=expected(name,pp)
    dynamic={'generation_steps','hatch_clock_start','hatch_steps','hatch_callback_frames','hatch_state_mask','total_frames','witness'}
    need(set(r)==set(e)|dynamic,'native result schema')
    for key,value in e.items():
        need(type(r[key]) is type(value) and r[key]==value,'native result '+key)
        if isinstance(value,list):need(all(type(x) is int for x in r[key]),'native array types '+key)
    for key in dynamic-{'witness'}:need(type(r[key]) is int and 0<=r[key]<=600000,'native counter '+key)
    need(1<=r['generation_steps']<=4096 and 0<=r['hatch_clock_start']<=255,'generation/hatch clock')
    need(r['hatch_steps']==(e['initial_egg_cycles']+1)*256-r['hatch_clock_start']-1,'physical hatch cadence')
    need(1<=r['hatch_callback_frames']<=9000 and r['hatch_state_mask']<1<<16 and r['hatch_state_mask']&(1<<10) and r['hatch_state_mask']&(1<<6),'native hatch/nickname missing')
    w=r['witness'];need(set(w)==set(WITNESS) and all(type(w[k]) is int and 1<=w[k]<=r['total_frames'] for k in WITNESS),'witness counters')
    need(all(w[a]<w[b] for a,b in zip(WITNESS,WITNESS[1:])),'ordinary daycare/save/hatch/continue order')
    return r


def execute():
    from pr16_learnset_wiki_actions import current,acquire
    import pr16_learnset_battle as b
    head=current();need(not WORK.exists() and not (ROOT/CP).exists(),'accepted/partial egg results must not be rerun wholesale')
    PROOF.mkdir(parents=True);oldproof=m.PROOF;m.PROOF=PROOF
    protected=(*m.PROTECTED,m.CP,b.CP,BASE+'pr16_learnset_battle_completed_actions.json')
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'status':'RUNNING','candidate':m.CANDIDATE,
       'scope':SCOPE,'native_processes':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0,'accepted_test_reruns':0,'bag_reruns':0,'battle_reruns':0,
       'wiki_generations':0,'issue19_complete':False,'release_ready':False,'results':[],'failures':[],
       'protected_bindings':{p:identity((ROOT/p).read_bytes()) for p in protected},'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE|{PARENT}},'next_step_ja':NEXT}
    try:
        m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_egg_gameplay','-v'],'unit');v['new_unit_tests']=18
        b.WORK=WORK/'restore-root';b.WORK.mkdir();rom=b.restore();need(identity(rom)==m.CANDIDATE,'candidate restore identity')
        cp=load(ROOT/BASE/'pr16_learnset_payload_checkpoint.json');members=dict(cp['summary']['files'],**{'receipt.json':cp['proof_bindings']['receipt.json']})
        acquire(cp['payload_artifact'],cp['source_head'],WORK/'payload',members)
        audit,pp=oracle(WORK/'payload',rom);write(PROOF/'oracle.json',audit);v['oracle']=audit
        gen={}
        for i,(source,target) in enumerate(EMBEDDED):
            raw=(ROOT/source).read_text();text,n=re.subn(r'\bint\s+main\s*\(','int issue19_egg_old_'+str(i)+'(',raw);need(n==1,'embedded main')
            (WORK/target).write_text(text);gen[target]=identity(text.encode())
        text=controller((ROOT/PARENT).read_bytes());c=WORK/'controller.c';c.write_text(text);gen[c.name]=identity(text.encode());(PROOF/'executed-controller.c').write_text(text)
        exe=WORK/'runner';dep=WORK/'dependencies.d'
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),str(c),'-lmgba','-o',str(exe)],'compile')
        need(not err,'compiler warning');v['host_compiles']=1;v['generated_sources']=gen;v['compiled_sources']={}
        for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(name);p=(p if p.is_absolute() else ROOT/p).resolve()
            if p.parent==WORK:need(identity(p.read_bytes())==gen[p.name],'generated dependency binding')
            else:v['compiled_sources'][p.relative_to(ROOT).as_posix()]=identity(p.read_bytes())
        seed=(ROOT/m.SEED).read_bytes();need(identity(seed)==m.SEED_ID,'seed identity');seed_stamp=(ROOT/m.SEED).stat().st_mtime_ns
        def one(case):
            name=case[0];fixture=WORK/(name+'.srm');fixture.write_bytes(seed)
            try:
                out,err=m.run([str(exe),str(b.WORK/'candidate.gba'),str(fixture),m.CANDIDATE['sha256'],m.SEED_ID['sha256'],name],name,900)
                return name,validate(out,err,name,pp),None
            except Exception as e:return name,None,{'case':name,'type':type(e).__name__,'error':str(e).replace(str(ROOT),'$REPO')}
        v['native_processes']=len(CASES);write(PROOF/'verification.json',v)
        with ThreadPoolExecutor(max_workers=2) as pool:
            for fut in as_completed([pool.submit(one,c) for c in CASES]):
                name,result,error=fut.result()
                if error:v['failures'].append(error)
                else:v['results'].append(result)
                write(PROOF/'verification.json',v)
        need(identity((b.WORK/'candidate.gba').read_bytes())==m.CANDIDATE and (ROOT/m.SEED).read_bytes()==seed and (ROOT/m.SEED).stat().st_mtime_ns==seed_stamp,'readonly ROM/seed changed')
        need(v['protected_bindings']=={p:identity((ROOT/p).read_bytes()) for p in protected},'accepted checkpoint/baseline changed')
        v['results'].sort(key=lambda r:r['case']);v['fresh_cores']=sum(r['fresh_cores'] for r in v['results']);v['accepted_cases']=len(v['results'])
        need(not v['failures'] and v['accepted_cases']==len(CASES),'scoped native cases failed; preserve successes and retry only changed failures')
        v['status']='PASS_SCOPED'
    except Exception as e:
        v.update(status='FAIL',error_type=type(e).__name__,error=str(e).replace(str(ROOT),'$REPO'));raise
    finally:
        v['proof_bindings']={p.name:identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=oldproof


def owned():return CODE|{CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in (ROOT/EVIDENCE).rglob('*') if p.is_file()}


def record():
    from pr16_learnset_wiki_actions import current
    from pr16_learnset_compact_record import publish_resume
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'recording source mismatch')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'duplicate public evidence');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_bytes().decode();need('\0' not in text,'tracked binary evidence')
        safe='\n'.join(s.rstrip() for s in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'public user path');(dest/p.name).write_text(safe)
    v.update(public_evidence_path=dest.relative_to(ROOT).as_posix(),public_evidence_bindings={p.name:identity(p.read_bytes()) for p in dest.iterdir()},actions_completion_confirmed=False)
    write(ROOT/CP,v);good=v['status']=='PASS_SCOPED'
    guide=f'# Issue19: 条件付きタマゴの通常操作\n\n候補 `{m.CANDIDATE["sha256"]}`、run{v["run_id"]} / source `{v["source_head"]}`。状態 `{v["status"]}`。\n\n育て屋へ親2体を通常会話で預ける→実歩行で生成→通常受取→タマゴSave/fresh Continue→実歩行/通常孵化→孵化後Save/fresh Continue。親個体・開始地点はfixtureであり自然捕獲は主張しない。\n\n## 限定変更影響\n\nPichuのLight Ball父/母・未所持・旧440除外・重複と4枠、Happinyの母/父incense・旧461/464/357除外・未所持Chansey分岐の8ケース。期待技は保存済み原本spanから固定し、タマゴ技関数の返り値をoracleにしない。344を通常タマゴ表へ平坦化しない。\n\n追加unit {v.get("new_unit_tests",0)}件、native {v["native_processes"]}process、成功{len(v["results"])}ケース。成功時各3fresh core、7観測barrier、手動Save2回+自然孵化登録1回、子/親/queue bytesを照合。全孵化経路/全owner/Issue19全体/releaseの受入ではない。\n\n正本 `{CP}`。失敗は削除せず同run原本から読む。Actions終端は後続の記録限定照合で確定。\n\n## 次\n\n{NEXT if good else "checkpointの失敗case/errorを修復し、保存された成功caseは再実行しない。"}\n'
    (ROOT/GUIDE).write_text(guide);state=load(ROOT/m.STATE)
    state['learnset_egg_gameplay']={k:v[k] for k in ('status','source_head','run_id','candidate','native_processes','issue19_complete','release_ready','actions_completion_confirmed')};state['learnset_egg_gameplay']['path']=CP
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'in_progress','conclusion':None}],'reason_ja':'実測原本と実行中Actionsを区別。push/upload後の終端は後続の完了照合まで未確定。'}
    state['observed_head']=v['source_head'];state['observed_head_semantics']='条件付きタマゴの通常操作を追加検証したsource。反映HEAD/Actions終端は後続で照合。'
    state['bp']['current_stop']='Issue19: Bag23/通常戦闘の受入を保持。条件付きタマゴ8ケースは'+v['status']+'。'
    nextstep=NEXT if good else '条件付きタマゴcheckpointの失敗原本を確認し、未受入caseだけ修復。成功case/Bag/戦闘/Wiki/ARMは再実行しない。'
    state['bp']['next_step']=nextstep;state['next_action']=dict(state['next_action'],id='LEARNSET_EGG_REVIEW' if good else 'LEARNSET_EGG_PENDING',goal_ja=nextstep,read_paths=[GUIDE,CP])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: issue19-conditional-egg-gameplay-v1\n- Status: '+('DONE（8ケースの区切り、全体未完）' if good else 'BLOCKED（失敗と成功原本を別々に保存）')+f'\n- Summary: 原本spanに固定したLight Ball/incense/旧技除外/重複/4枠8ケース。通常育て屋・実歩行生成/孵化・タマゴと孵化後Save/fresh Continue。\n- Files changed: 専用source投影/validator/18境界試験/限定Actions、checkpointとtext原本、guide・固定引継ぎMD/JSON・両ログ。\n- Verify: run{v["run_id"]} status {v["status"]}、unit {v.get("new_unit_tests",0)}、native {v["native_processes"]}process、成功{len(v["results"])}。受入Bag/戦闘/ARM/Wiki再実行0・ROM変更0。\n- Commit: 同branchへ非force pushしreflected-head.txtにremote照合結果を保存。\n- Network: 固定artifact/保存候補復元のみ。原本ROM/saveを新規追跡しない。全履歴guard/全体releaseの完了は主張しない。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(log)


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA']
    # Source files were committed in the source HEAD; final worktree diff is records only.
    g.CODE=set();g.OWNED=owned()-CODE;g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths required');actions[sys.argv[1]]()
