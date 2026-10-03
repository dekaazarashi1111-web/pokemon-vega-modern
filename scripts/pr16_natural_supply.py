#!/usr/bin/env python3
"""未受入の通常配布・固定form初期技と原本初期技孵化。保存成功は再実行しない。"""
from __future__ import annotations
from contextlib import contextmanager
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_learnset_egg_gameplay as egg
import pr16_learnset_boundaries as boundary
m=egg.m
ROOT=egg.ROOT
need,identity,load,write=m.need,m.identity,m.load,m.write
TASK='USER-20260925-NATURAL-SUPPLY'
SELF='scripts/pr16_natural_supply.py'
TEST='tests/test_pr16_natural_supply.py'
C='tools/mgba_pr16_natural_gift.c'
WF='.github/workflows/pr16-natural-supply-20260925.yml'
CODE={SELF,TEST,C,WF}
CP=m.BASE+'pr16_natural_supply_checkpoint.json'
GUIDE='docs/PR16_NATURAL_SUPPLY_JA.md'
EVIDENCE=m.BASE+'pr16_natural_supply_evidence'
WORK=ROOT/'.local/pr16-natural-supply';PROOF=WORK/'proof'
CANDIDATE=boundary.CANDIDATE
SCOPE='ISSUE19_NATURAL_INITIAL_HATCH_SAVE_CONTINUE'
GIFT='floette-eternal-npc-initial'
HATCH={'caterpie-initial-hatch':(649,[33,81]),'leepun-initial-hatch':(1,[10,39])}
NAMES=(*HATCH,GIFT)
FLOETTE_ROWS=[(22,1),(33,1),(543,1),(219,10),(75,15),(547,18),(273,20),(345,22),(204,26),(235,33),(382,40),(738,50),(76,54)]
NEXT='Issue19: 自然配布/孵化の保存成功を再実行しない。限定3caseの終端確定後は未受入の他配布・form初期技、釣り/隠し野生の特殊技順を優先する。Floette12技の全供給/全owner/Issue19/release/baseline切替は未完。EXP進化共有3/EXP4/最初の拒否/アメ11/Bag23/egg8/旧野生/host/ARM/Wikiは変更影響なし。'


@contextmanager
def egg_contract(cases):
    """既存純変換/validatorの引数だけを隔離。旧execute/旧testは呼ばない。"""
    old=egg.CASES,egg.BY_NAME,egg.SCOPE,m.CANDIDATE
    egg.CASES=tuple(cases);egg.BY_NAME={c[0]:c for c in cases};egg.SCOPE=SCOPE;m.CANDIDATE=CANDIDATE
    try:yield
    finally:egg.CASES,egg.BY_NAME,egg.SCOPE,m.CANDIDATE=old


def hatch_cases(cycles):
    need(set(cycles)=={1,649} and all(type(x)is int and 1<=x<=40 for x in cycles.values()),'孵化周期の範囲')
    # 既習得/後世代の技を親へ入れず、両親の1技以外を初期値へ。親の捕獲は未受入。
    return [(name,(moves[0],0,0,0),(moves[0],0,0,0),0,0,sid,sid,cycles[sid],tuple(moves+[0,0])) for name,(sid,moves) in HATCH.items()]


def hatch_source(cases):
    with egg_contract(cases):text=egg.controller((ROOT/egg.PARENT).read_bytes())
    text=egg.once(text,'b_create(c,QOL_PLAYER_PARTY,25U,0x123456F0U,0x11223344U)','b_create(c,QOL_PLAYER_PARTY,v->mother_species,0x123456F0U,0x11223344U)')
    return text


def oracle(folder,floette,rom):
    rows,audit=boundary.n.sources(folder)
    for sid,moves in HATCH.values():need(boundary.n.initial(rows[sid],1)==moves+[0,0],'孵化原本初期技')
    cp=load(ROOT/m.BASE/'pr16_learnset_floette_checkpoint.json')
    raw=(floette/'floette.level_up.bin').read_bytes();need(identity(raw)==cp['summary']['files']['floette.level_up.bin'],'Floette原本hash')
    need(boundary.n.p.decode_span(raw,'level_up')==FLOETTE_ROWS,'Floette原本順序')
    gifted=boundary.n.initial(FLOETTE_ROWS,50);need(gifted==[204,235,382,738],'配布levelの原本window')
    # 孵化周期/性比/egg groupは習得技とは独立した候補既存データ。native結果から逆算しない。
    cycles={};stats={}
    for sid in (1,649):
        data=rom[0x1600000+32*sid:0x1600000+32*(sid+1)]
        need(len(data)==32 and 1<=data[17]<=40 and 1<=data[16]<=253,'候補の親/孵化データ')
        cycles[sid]=data[17];stats[str(sid)]={'row':identity(data),'egg_cycles':data[17],'gender_ratio':data[16],'egg_groups':list(data[20:22])}
    at=struct.unpack_from('<I',rom,0x1cc)[0]-0x08000000;need(at==0x10421f4,'PP root')
    pp={mid:(rom[at+mid*12+4] if mid else 0) for mid in {0,*gifted,10,39,33,81}}
    need(all(1<=v<=64 for k,v in pp.items() if k),'PP bounds')
    audit.update(floette_span=identity(raw),floette_rows=FLOETTE_ROWS,floette_initial=gifted,egg_stats=stats,pp=pp)
    return hatch_cases(cycles),pp,audit


def gift_geometry(rom):
    def ptr(at):
        need(0<=at<=len(rom)-4,'ROM pointer location');value=struct.unpack_from('<I',rom,at)[0]-0x08000000
        need(0<=value<len(rom),'ROM pointer target');return value
    header=ptr(ptr(ptr(0x54b0c)+96*4)+5*4);events=ptr(header+4);count=rom[events];objects=ptr(events+4)
    need(0<count<=64 and objects+24*count<=len(rom),'NPC object bounds')
    found=[rom[objects+24*i:objects+24*(i+1)] for i in range(count) if rom[objects+24*i]==15]
    need(len(found)==1 and struct.unpack_from('<HH',found[0],4)==(25,19),'実NPC local15/座標')
    script=struct.unpack_from('<I',found[0],16)[0];at=script-0x08000000
    need(0<=at<len(rom)-12 and rom[at:at+3]==b'\x6a\x5a\x23','実NPC lock/face/callnative')
    return {'map':[96,5],'local_id':15,'position':[25,19],'script':script,'script_bytes':rom[at:at+12].hex(),'object':found[0].hex()}


def gift_validate(out,err,pp):
    r=json.loads(out,object_pairs_hook=egg.strict_pairs)
    fixed={'schema_version':1,'status':'PASS','case':GIFT,'candidate_sha256':CANDIDATE['sha256'],'species':1029,'level':50,'moves':[204,235,382,738],'pp':[pp[x] for x in (204,235,382,738)],'fresh_cores':2,'denied_host_write_apis':7,'guarded_phases':3,'party_preserved_bytes':200,'initial_party_map_ring_flag_are_fixtures':True,'all_owners_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0}
    dynamic={'boundary','claimed','returned','saved','continued','repeat','save_counters','npc_script'}
    need(set(r)==set(fixed)|dynamic,'配布結果schema')
    for k,v in fixed.items():need(type(r[k])is type(v) and r[k]==v,'配布結果 '+k)
    keys=('boundary','claimed','returned','saved','continued','repeat')
    need(all(type(r[k])is int for k in keys) and 0<r[keys[0]] and all(r[a]<r[b] for a,b in zip(keys,keys[1:])) and r['repeat']<100000,'配布chronology')
    counters=r['save_counters'];need(type(counters)is list and len(counters)==5 and all(type(x)is int for x in counters),'Save counter型')
    need(counters==[counters[0],counters[0]+1,counters[0]+2,counters[0]+2,counters[0]+2],'native配布Save+通常Save/Continue/再受取不変')
    need(type(r['npc_script'])is int and 0x08000000<=r['npc_script']<0x0a000000,'NPC script')
    party=re.findall(rb'^SUPPLY_PARTY stage=(fixture|claimed|saved|continued|repeat) counter=(\d+) hex=([0-9a-f]+)$',err,re.M)
    need(len(party)==err.count(b'SUPPLY_PARTY ')==5 and [x[0] for x in party]==[b'fixture',b'claimed',b'saved',b'continued',b'repeat'],'配布party原本')
    need([int(x[1]) for x in party]==counters,'原本Save counter')
    raw=[bytes.fromhex(x[2].decode()) for x in party];need(len(raw[0])==100 and all(len(x)==200 for x in raw[1:]),'whole party')
    need(raw[0]==raw[1][:100] and raw[1]==raw[2]==raw[3]==raw[4],'元partyと配布保存不変')
    child=raw[1][100:];need(struct.unpack_from('<H',child,32)[0]==1029 and child[84]==50 and list(struct.unpack_from('<4H',child,44))==fixed['moves'] and list(child[52:56])==fixed['pp'] and child[40]==0,'独立raw配置/技/PP')
    need(b'mGBA[' not in err and err.count(b'original core destroyed; new core boot and normal Continue')==1 and b'host write after observation barrier' not in err,'core lifecycle/guard')
    return dict(r,party_identity=identity(raw[1]))


def pending(accepted,contracts):
    need(set(accepted)<=set(contracts),'未知の保存case')
    for name,row in accepted.items():need(row['contract']==contracts[name] and row['result']['status']=='PASS','受入入力の変更影響審査が必要')
    return [name for name in NAMES if name not in accepted]


def execute():
    from pr16_learnset_wiki_actions import current,acquire
    import pr16_learnset_battle as b
    import pr16_learnset_entry_repair as entry
    import pr16_learnset_wild_repair as wild
    head=current();need(not WORK.exists(),'同じ作業領域の再実行禁止');PROOF.mkdir(parents=True)
    old=load(ROOT/CP) if (ROOT/CP).exists() else {}
    protected=set(m.PROTECTED)|{egg.CP,boundary.CP,boundary.n.CP,m.BASE+'pr16_exp_evolution_share_checkpoint.json'}
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':CANDIDATE,'status':'RUNNING','accepted':old.get('accepted',{}),'results':[],'failures':{},'new_unit_tests':0,'native_processes':0,'host_compiles':0,'arm_compiles':0,'rom_changes':0,'accepted_case_reruns':0,'wiki_generations':0,'actions_completion_confirmed':False,'issue19_complete':False,'release_ready':False,'active_baseline_changed':False,'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE|{egg.SELF,egg.PARENT}},'protected_bindings':{p:identity((ROOT/p).read_bytes()) for p in protected},'prior_runs':old.get('prior_runs',[])+([old['run_id']] if old else [])}
    previous=m.PROOF;m.PROOF=PROOF
    try:
        _,err=m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_natural_supply','-v'],'unit')
        count=re.search(rb'Ran (\d+) tests? in ',err);need(count and b'\nOK\n' in err,'限定unit終端');v['new_unit_tests']=int(count[1])
        cp=load(ROOT/boundary.n.CP);need(cp['candidate']==CANDIDATE and cp['actions_completion_confirmed'],'保存候補の受入')
        b.WORK=WORK/'restore-root';b.WORK.mkdir();parent=b.restore();rom,recipe=entry.apply(parent);rom=wild.replay(rom,cp['wild_repair'])
        need(identity(rom)==CANDIDATE,'候補再構成');(WORK/'candidate.gba').write_bytes(rom);write(PROOF/'recipe.json',{'entry':recipe,'wild':cp['wild_repair']})
        for label,stem in [('payload','payload'),('floette','floette')]:
            source=load(ROOT/m.BASE/('pr16_learnset_'+stem+'_checkpoint.json'))
            acquire(source['payload_artifact'],source['source_head'],WORK/label,dict(source['summary']['files'],**{'receipt.json':source['proof_bindings']['receipt.json']}))
        cases,pp,audit=oracle(WORK/'payload',WORK/'floette',rom);geometry=gift_geometry(rom);audit['gift_geometry']=geometry;write(PROOF/'oracle.json',audit)
        text=hatch_source(cases);contracts={name:{'candidate':CANDIDATE,'fixture':list(case),'controller':identity(text.encode())} for name,case in zip(HATCH,cases)}
        contracts[GIFT]={'candidate':CANDIDATE,'source':identity((ROOT/C).read_bytes()),'helpers':identity(text.encode()),'oracle':audit['floette_span'],'geometry':geometry}
        # JSON往復でtuple/list差を正規化し、保存済み契約と一致させる。
        contracts=json.loads(json.dumps(contracts));todo=pending(v['accepted'],contracts);need(todo,'保存成功はcompleteだけを実行')
        for name,a in v['accepted'].items():
            directory=ROOT/EVIDENCE/str(a['run_id']);prior=load(directory/'verification.json')
            for suffix in ('.stdout.txt','.stderr.txt','.process.json'):
                leaf=name+suffix;need(identity((directory/leaf).read_bytes())==prior['proof_bindings'][leaf],'保存成功原本 '+leaf)
        v['selected_cases']=todo;v['contracts']=contracts;gen={}
        def put(name,text):
            (WORK/name).write_text(text);gen[name]=identity(text.encode())
        for i,(source,target) in enumerate(egg.EMBEDDED):
            embedded,n=re.subn(r'\bint\s+main\s*\(','int supply_inherited_'+str(i)+'(',(ROOT/source).read_text());need(n==1,'embedded main');put(target,embedded)
        put('controller.c',text);(PROOF/'executed-controller.c').write_text(text)
        put('supply_breeding_helpers.c',egg.once(text,'int main(int argc,char **argv)','int supply_breeding_main(int argc,char **argv)'))
        put('supply_gift_vectors.h','#define SUPPLY_NPC_SCRIPT '+str(geometry['script'])+'U\nstatic const unsigned supply_pp[4]={'+','.join(str(pp[x]) for x in (204,235,382,738))+'};\n')
        for kind,source in [('hatch',str(WORK/'controller.c')),('gift',C)]:
            if not any((n==GIFT)==(kind=='gift') for n in todo):continue
            v['host_compiles']+=1;dep=WORK/(kind+'.d')
            _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),source,'-lmgba','-o',str(WORK/kind)],'compile-'+kind)
            need(not err,'host compiler warning')
            for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
                path=Path(name);path=(path if path.is_absolute() else ROOT/path).resolve()
                if path.parent==WORK:need(identity(path.read_bytes())==gen[path.name],'generated source')
                else:v.setdefault('compiled_sources',{})[path.relative_to(ROOT).as_posix()]=identity(path.read_bytes())
        v['generated_sources']=gen;seed=(ROOT/m.SEED).read_bytes();stamp=(ROOT/m.SEED).stat().st_mtime_ns;need(identity(seed)==m.SEED_ID,'seed identity')
        for name in todo:
            fixture=WORK/(name+'.srm');fixture.write_bytes(seed);v['native_processes']+=1
            try:
                out,err=m.run([str(WORK/('gift' if name==GIFT else 'hatch')),str(WORK/'candidate.gba'),str(fixture),CANDIDATE['sha256'],m.SEED_ID['sha256'],name],name,900)
                if name==GIFT:result=gift_validate(out,err,pp)
                else:
                    with egg_contract(cases):result=egg.validate(out,err,name,pp)
                v['results'].append(result);v['accepted'][name]={'run_id':v['run_id'],'source_head':head,'contract':contracts[name],'result':result}
            except Exception as ex:v['failures'][name]={'type':type(ex).__name__,'error':str(ex).replace(str(ROOT),'$REPO')}
            write(PROOF/'verification.json',v)
        need((ROOT/m.SEED).read_bytes()==seed and (ROOT/m.SEED).stat().st_mtime_ns==stamp and identity((WORK/'candidate.gba').read_bytes())==CANDIDATE,'input不変')
        need(v['protected_bindings']=={p:identity((ROOT/p).read_bytes()) for p in protected},'既受入不変')
        v['status']='PASS_NATURAL_SUPPLY_SCOPED' if len(v['accepted'])==len(NAMES) else 'PARTIAL_NATURAL_SUPPLY'
        need(not v['failures'],'未成功caseを原本へ保存')
    except Exception as ex:
        if v['status']=='RUNNING':v['status']='FAIL'
        v.update(error_type=type(ex).__name__,error=str(ex).replace(str(ROOT),'$REPO'));raise
    finally:
        v['proof_bindings']={p.name:identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=previous


def owned():
    dest=ROOT/EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return {CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in dest.rglob('*') if p.is_file()}


def publish(v,completion=False):
    from pr16_learnset_compact_record import publish_resume
    good=list(v['accepted']);missing=[name for name in NAMES if name not in good]
    nextstep=('保存成功を再実行せず、completeでActions終端だけ照合。' if not missing and not v['actions_completion_confirmed'] else NEXT if not missing else '自然供給checkpointの失敗原本を確認し、未成功caseだけ修復。保存成功/旧受入は再実行しない。')
    (ROOT/GUIDE).write_text(f'# PR16 Issue19: 通常配布・初期技孵化\n\n状態 `{v["status"]}`、source `{v["source_head"]}`、run `{v["run_id"]}`。Actions終端 `{v["actions_completion_confirmed"]}`。\n\n候補 `{CANDIDATE["sha256"]}` を保存recipeから復元。ROM/ARM/既受入case再実行0。\n\nキャタピー649とVegaリープン1は親2体・開始地点だけfixture。通常育て屋へ預け、実歩行生成・受取・Save/fresh Continue・実歩行孵化・通常Save/fresh Continueを検証。期待初期技は公式/Vega採用原本の順序。旧条件付きegg8は再実行しない。\n\n永遠の花フラエッテ1029はmap96/5 local15の実NPCからLv50を受取。開始party/場所/Ring/未受領flagはfixtureで、Ringの通常取得やストーリー到達の受入ではない。原本末尾4技204/235/382/738・PP・既存party不変・Save/fresh Continue・再配布なしを照合。12技全体の通常供給受入ではない。\n\n保存成功 `{good}`。未成功 `{missing}`。今回unit {v["new_unit_tests"]}、host compile {v["host_compiles"]}、native process {v["native_processes"]}。終端記録専用の場合これらの再実行0。\n\n## 次\n\n{nextstep}\n')
    state=load(ROOT/m.STATE);stamp=datetime.datetime.now(datetime.timezone.utc)
    state['learnset_natural_supply']={k:v[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','issue19_complete')};state['learnset_natural_supply'].update(path=CP,accepted_cases=good,pending_cases=missing)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_date_jst']=stamp.astimezone(ZoneInfo('Asia/Tokyo')).date().isoformat()
    state['observed_head_semantics']='自然供給限定caseのsource/保存原本。旧受入・全体完成とは別。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':v.get('terminal_actions',[{'id':v['run_id'],'status':'in_progress','conclusion':None}]),'reason_ja':'保存成功/失敗とActions終端を区別。一般CI action_requiredを成功へ昇格しない。'}
    state['bp']['current_stop']=f'Issue19: 自然供給{len(good)}/{len(NAMES)}。{v["status"]}。全体未完。';state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='NATURAL_SUPPLY',goal_ja=nextstep,read_paths=[GUIDE,CP,SELF,TEST])
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=identity((ROOT/p).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    note=f'\n## {stamp.isoformat()}\n- Timestamp: {stamp.isoformat()}\n- Task: {TASK} / 通常配布・原本初期技孵化\n- Version: issue19-natural-supply-v1\n- Status: '+('DONE（限定3case、全体未完）' if not missing and v['actions_completion_confirmed'] else 'STOPPED（保存原本から未完のみ継続）')+f'\n- Summary: {len(good)}/3成功、未成功{missing}。親/場所/進行/Ringはfixture、取得・孵化・保存区間の7host書込APIを拒否。\n- Files changed: 専用driver/C/tests/workflow、checkpoint/guide/text証拠、固定引継ぎMD/JSON、両ログ。\n- Verify: unit {v["new_unit_tests"]} host {v["host_compiles"]} native {v["native_processes"]}。Actions終端={v["actions_completion_confirmed"]}。終端照合専用={completion}（専用時の全実行0）。ROM/ARM/旧受入case/Wiki再実行0。\n- Commit: 同branchへ非force push。reflected-head.txtとremoteを照合。\n- Network: GitHub固定source/artifact/Actions。source取得run36101411033/36101572572は検証ではなく転送のみ。原本再生成・merge/release/baseline切替なし。\n'
    for p in ('design/run_log.md','design/version_log.md'):
        with (ROOT/p).open('a') as f:f.write(note)


def record():
    from pr16_learnset_wiki_actions import current
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record source')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'原本上書き禁止');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_bytes().decode();need('\0' not in text,'binary proof')
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'user path');(dest/p.name).write_text(safe)
    v['public_evidence_bindings']={p.name:identity(p.read_bytes()) for p in dest.iterdir()};v['evidence_path']=dest.relative_to(ROOT).as_posix()
    write(ROOT/CP,v);publish(v)


def complete():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    current();v=load(ROOT/CP);need(v['accepted'] and not v['actions_completion_confirmed'],'完了照合の重複/成功なし')
    runs=[]
    for rid in sorted(set(v['prior_runs']+[v['run_id']])):
        r=fetch('actions/runs/'+str(rid));need(r['status']=='completed' and r['head_branch']==m.BRANCH and r['path']==WF,'run終端/branch/path')
        jobs=fetch('actions/runs/'+str(rid)+'/jobs?per_page=100');need(jobs['total_count']==len(jobs['jobs'])==1,'one full job')
        if rid==v['run_id']:need(r['head_sha']==v['source_head'] and r['conclusion']=='success' and all(x['conclusion'] in ('success','skipped') for x in jobs['jobs'][0]['steps']),'最終run全step成功')
        runs.append({k:r[k] for k in ('id','head_sha','status','conclusion','path')})
    for p,binding in v['public_evidence_bindings'].items():need(identity((ROOT/v['evidence_path']/p).read_bytes())==binding,'保存原本不変')
    for p,binding in (v['source_bindings']|v.get('compiled_sources',{})).items():
        if p!=WF:need(identity((ROOT/p).read_bytes())==binding,'実行source不変 '+p)
    need(set(v['accepted'])==set(NAMES),'未成功を完了扱いしない')
    v.update(actions_completion_confirmed=True,terminal_actions=runs,completed_by_source=os.environ['GITHUB_SHA'])
    write(ROOT/CP,v);publish(v,True);PROOF.mkdir(parents=True,exist_ok=True);write(PROOF/'completion.json',{'task':TASK,'terminal_actions':runs,'new_native_processes':0,'new_unit_tests':0,'host_compiles':0,'rom_changes':0})


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'complete':complete,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
