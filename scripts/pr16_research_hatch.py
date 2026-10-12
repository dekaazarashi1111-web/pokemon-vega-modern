#!/usr/bin/env python3
"""Issue19: 受入済み配布個体をfixtureへ結合し、未受入の研究孵化だけ測定。"""
from __future__ import annotations
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
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_research_hatch.py'
TEST='tests/test_pr16_research_hatch.py'
C='tools/mgba_pr16_research_hatch.c'
WF='.github/workflows/pr16-research-hatch-20260925.yml'
CODE={SELF,TEST,C,WF}
TASK='USER-20260925-RESEARCH-HATCH'
BASE='content/modernization/'
CP=BASE+'pr16_research_hatch_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_HATCH_JA.md'
SUPPLY_CP=BASE+'pr16_collection_gifts_checkpoint.json'
SUPPLY_EVIDENCE=BASE+'pr16_collection_gifts_evidence'
EVIDENCE=BASE+'pr16_research_hatch_evidence'
WORK=ROOT/'.local/pr16-research-hatch'
PROOF=WORK/'proof'
SHOTS=WORK/'screens'
CANDIDATE={'size':33554432,'sha256':'b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91'}
SPECIES=(1201,1204,1206,1208,1210,1212,1215,1394,1396,1407,1410,1414,1415,1417,1425)
NAMES=tuple('research-egg-'+str(s) for s in SPECIES)
SCOPE='RESEARCH_EGG_FIXTURE_WALK_HATCH_SAVE_CONTINUE'
NEXT=('Issue19: 研究タマゴ15種の保存個体fixtureからの実歩行・孵化後form/技・Save/fresh Continueを再実行しない。'
      '通常配布17件も保存受入を維持。次は未受入の釣り/隠し野生の特殊技順。'
      '1281は非学習ownerの既存方針で未受入。全供給/Issue19/release/active baseline切替は未完。')


def need(ok,text):
    if not ok:raise ValueError(text)


def pairs(items):
    result={}
    for k,v in items:
        need(k not in result,'duplicate JSON key '+k);result[k]=v
    return result


def load(path):return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs)
def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n')


def initial(rows):
    need(isinstance(rows,list) and 0<len(rows)<=128,'original row bounds')
    last=0
    for row in rows:
        need(isinstance(row,list) and len(row)==2 and all(type(x)is int for x in row),'original pair')
        move,level=row;need(0<move<1063 and last<=level<=100 and level>=1,'original order/ID');last=level
    raw=[m for m,l in rows if l<=1][-4:]
    unique=list(dict.fromkeys(raw));need(unique,'original initial moves nonempty')
    return unique+[0]*(4-len(unique))


def fixture(accepted,stderr):
    case=accepted['contract']['case'];sid=case['species'];name=case['name']
    need(type(sid)is int and sid in SPECIES and name=='research-egg-'+str(sid),'explicit research owner only')
    need(accepted['contract']['candidate']==CANDIDATE and case['is_egg']==1 and case['level']==1,'accepted egg candidate')
    moves=initial(case['original_rows']);need(moves==case['moves'],'bound original span not result-derived')
    pp=case['pp'];need(type(pp)is list and len(pp)==4 and all(type(p)is int and (1<=p<=64 if m else p==0) for m,p in zip(moves,pp)),'PP bounds')
    rows=re.findall(rb'^CF_PARTY stage=(fixture|claimed|saved|continued|cancelled) counter=(\d+) hex=([0-9a-f]+)$',stderr,re.M)
    need(len(rows)==stderr.count(b'CF_PARTY ')==5 and [x[0] for x in rows]==[b'fixture',b'claimed',b'saved',b'continued',b'cancelled'],'complete accepted lifecycle')
    raw=[bytes.fromhex(x[2].decode()) for x in rows]
    need(len(raw[0])==100 and all(len(x)==200 for x in raw[1:]) and raw[0]==raw[1][:100] and raw[1]==raw[2]==raw[3]==raw[4],'accepted party invariant')
    need(accepted['result']['status']=='PASS' and accepted['result']['party_identity']==identity(raw[3]),'accepted individual identity')
    child=raw[3][100:]
    need(struct.unpack_from('<H',child,32)[0]==sid and child[84]==1,'raw owner/level')
    need(list(struct.unpack_from('<4H',child,44))==moves and list(child[52:56])==pp and child[40]==0,'raw original slots/PP')
    need(0<child[41]<=255,'original unshortened cycles')
    owners=re.findall(rb'^CF_OWNER stage=(\w+) hex=([0-9a-f]{1024})$',stderr,re.M)
    need(len(owners)==stderr.count(b'CF_OWNER ')==5 and [x[0] for x in owners]==[x[0] for x in rows],'owner lifecycle')
    need(owners[1][1]==owners[2][1]==owners[3][1]==owners[4][1],'accepted owner persistence')
    import zlib
    owner=bytearray.fromhex(owners[3][1].decode());crc=struct.unpack_from('<I',owner,12)[0];owner[12:16]=bytes(4)
    need(struct.unpack_from('<IIHH',owner)==(0x31565343,0xcea9acbc,1,512) and zlib.crc32(owner)&0xffffffff==crc,'owner ABI/CRC')
    return dict(name=name,species=sid,moves=moves,pp=pp,cycles=child[41],party=raw[3].hex(),owner=owners[3][1].decode(),
                original_rows=case['original_rows'],origin_run=accepted['run_id'],origin_source=accepted['source_head'],
                source_stderr=identity(stderr),accepted_party=identity(raw[3]),gift_reexecuted=False,
                reconstructed_individual_fixture=True,genuine_saved_game_continuation=False)


def header(cases):
    arr=lambda xs:'{'+','.join(str(x)+'U' for x in xs)+'}'
    lines=['/* 保存受入原本fixtureと独立した原本習得span。cycle短縮なし。 */',
           'struct RHCase {const char *name; unsigned species,cycles,moves[4],pp[4]; unsigned char party[200],owner[512];};',
           'static const struct RHCase rh_cases[] = {']
    for v in cases:
        lines.append('{"'+v['name']+'",'+str(v['species'])+'U,'+str(v['cycles'])+'U,'+arr(v['moves'])+','+arr(v['pp'])+','+arr(bytes.fromhex(v['party']))+','+arr(bytes.fromhex(v['owner']))+'},')
    return '\n'.join(lines+['};',''])


def validate(out,err,case):
    r=json.loads(out,object_pairs_hook=pairs)
    fixed=dict(schema_version=1,status='PASS',scope=SCOPE,case=case['name'],candidate_sha256=CANDIDATE['sha256'],
               species=case['species'],level=1,moves=case['moves'],pp=case['pp'],cycles=case['cycles'],fresh_cores=2,
               host_write_barriers=7,guarded_phases=3,native_hatch_saves=1,manual_saves=1,saved_party_bytes=200,
               reconstructed_individual_fixture=True,continuous_gift_save_claimed=False,gift_reruns=0,
               issue19_complete=False,release_ready=False,warnings_errors=0)
    dynamic={'clock_start','steps','hatch_frames','hatch_state_mask','total_frames','save_counters','witness'}
    need(set(r)==set(fixed)|dynamic,'strict hatch result schema')
    for k,v in fixed.items():need(type(r[k])is type(v) and r[k]==v,'result '+k)
    need(all(type(x)is int for k in ('moves','pp') for x in r[k]),'slot integer types')
    need(all(type(r[k])is int for k in dynamic-{'witness','save_counters'}),'counter integer types')
    need(0<=r['clock_start']<256 and r['steps']==(case['cycles']+1)*256-r['clock_start']-1,'full physical cadence')
    need(0<r['hatch_frames']<9000 and 0<r['total_frames']<=600000 and r['hatch_state_mask']&((1<<6)|(1<<10))==((1<<6)|(1<<10)) and r['hatch_state_mask']<1<<16,'native hatch callback states')
    keys=('boundary','hatch_begin','nickname','hatch_end','saved','continued');t=r['witness']
    need(type(t)is dict and set(t)==set(keys) and all(type(t[k])is int for k in keys),'witness schema')
    need(0<t[keys[0]] and all(t[a]<t[b] for a,b in zip(keys,keys[1:])) and t['continued']==r['total_frames'],'native chronology')
    counters=r['save_counters'];need(type(counters)is list and len(counters)==4 and all(type(x)is int and x>=0 for x in counters),'save counter types')
    need(counters==[counters[0],counters[0]+1,counters[0]+2,counters[0]+2],'native hatch + manual Save + fresh Continue')
    rows=re.findall(rb'^RH_PARTY stage=(\w+) frame=(\d+) counter=(\d+) hex=([0-9a-f]{400})$',err,re.M)
    need(len(rows)==err.count(b'RH_PARTY ')==4 and [x[0] for x in rows]==[b'fixture',b'hatched',b'saved',b'continued'],'whole party raw evidence')
    need([int(x[2]) for x in rows]==counters and [int(x[1]) for x in rows][1:]==[t['hatch_end'],t['saved'],t['continued']] and int(rows[0][1])<t['boundary'],'raw chronology binding')
    raw=[bytes.fromhex(x[3].decode()) for x in rows]
    need(raw[0].hex()==case['party'] and raw[1]==raw[2]==raw[3],'original fixture and saved full party')
    for party in raw:
        child=party[100:];need(struct.unpack_from('<H',child,32)[0]==case['species'] and child[84]==1,'raw retained form/level')
        need(list(struct.unpack_from('<4H',child,44))==case['moves'] and list(child[52:56])==case['pp'] and child[40]==0,'raw retained order/PP')
        need(child[:8]==raw[0][100:108] and 0<struct.unpack_from('<H',child,86)[0]<=struct.unpack_from('<H',child,88)[0],'raw individual/HP')
        # 同行個体の自然ななつき度/チェックサム更新を禁止しない。
        for a,b in ((0,8),(32,41),(44,68),(84,100)):
            need(party[a:b]==raw[0][a:b],'companion identity/moves/health')
    mon=re.findall(rb'^RH_MON stage=(\w+) species=(\d+) level=(\d+) egg=(\d+) hp=(\d+) max=(\d+) pid=(\d+) ot=(\d+) cycles=(\d+)$',err,re.M)
    need(len(mon)==err.count(b'RH_MON ')==3 and [x[0] for x in mon]==[b'fixture',b'hatched',b'continued'],'native getter lifecycle')
    pid,ot=struct.unpack_from('<II',raw[0],100)
    for i,row in enumerate(mon):
        sid,level,egg,hp,maximum,pid_now,ot_now,cycles=map(int,row[1:])
        need((sid,level,egg,pid_now,ot_now)==(case['species'],1,int(i==0),pid,ot) and 0<hp<=maximum,'getter owner/identity/egg/HP')
        if i==0:need(cycles==case['cycles'],'getter original cycles')
    walk=re.findall(rb'^BREED research-hatch-walk map=35/0 xy=([23]),5 party=2 queue=0 clock=(\d+) steps=(\d+) frame=(\d+) cb=([0-9a-f]+)$',err,re.M)
    need(len(walk)==err.count(b'BREED research-hatch-walk ') and len(walk)>case['cycles'],'physical walk prefix witnesses')
    need([int(x[2]) for x in walk]==list(range(1,r['steps']+1,256)),'complete distinct walk prefix')
    need(all(int(a[3])<int(b[3]) for a,b in zip(walk,walk[1:])),'walk frame monotonicity')
    need(err.count(b'original core destroyed; new core boot and normal Continue\n')==1 and b'mGBA[' not in err and b'host write after observation barrier' not in err,'fresh core and write barriers')
    return dict(r,hatched_party_identity=identity(raw[1]),fixture_party_identity=identity(raw[0]))


def pending(accepted,contracts):
    need(set(accepted)<=set(contracts),'unknown accepted hatch case')
    for name,a in accepted.items():need(a['contract']==contracts[name] and a['result']['status']=='PASS','accepted hatch input impact review '+name)
    return [n for n in NAMES if n not in accepted]


def execute():
    import pr16_natural_supply as s
    import pr16_learnset_battle as battle
    import pr16_learnset_entry_repair as entry
    import pr16_learnset_wild_repair as wild
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    m,egg=s.m,s.egg
    head=current();need(not WORK.exists(),'fresh work only');PROOF.mkdir(parents=True);SHOTS.mkdir()
    old=load(ROOT/CP) if (ROOT/CP).exists() else {}
    protected=set(m.PROTECTED)|{SUPPLY_CP,s.CP,egg.CP,s.boundary.CP,s.boundary.n.CP,BASE+'pr16_exp_evolution_share_checkpoint.json'}
    v=dict(schema_version=1,task=TASK,status='RUNNING',source_head=head,run_id=int(os.environ['GITHUB_RUN_ID']),candidate=CANDIDATE,
           accepted=old.get('accepted',{}),failures={},new_unit_tests=0,native_processes=0,host_compiles=0,arm_compiles=0,rom_changes=0,
           accepted_case_reruns=0,gift_reruns=0,wiki_generations=0,actions_completion_confirmed=False,issue19_complete=False,release_ready=False,active_baseline_changed=False,
           source_bindings={p:identity((ROOT/p).read_bytes()) for p in CODE|{s.SELF,egg.SELF,egg.PARENT}},
           protected_bindings={p:identity((ROOT/p).read_bytes()) for p in protected},prior_runs=old.get('prior_runs',[])+([old['run_id']] if old else []))
    previous=m.PROOF;m.PROOF=PROOF
    try:
        fingerprint={p:identity((ROOT/p).read_bytes()) for p in (SELF,TEST,C)}
        if old.get('unit_binding')==fingerprint and old.get('unit_passed'):
            v.update(unit_binding=fingerprint,unit_passed=True,unit_origin=old['unit_origin'])
        else:
            _,err=m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_research_hatch','-v'],'unit')
            count=re.search(rb'Ran (\d+) tests? in ',err);need(count and b'\nOK\n' in err,'new pure unit pass')
            v.update(new_unit_tests=int(count[1]),unit_binding=fingerprint,unit_passed=True,unit_origin=v['run_id'])
        supply=load(ROOT/SUPPLY_CP);need(supply['actions_completion_confirmed'] and len(supply['accepted'])==17,'17 accepted supply, not rerun')
        terminal=fetch('actions/runs/36121938018')
        need(terminal['status']=='completed' and terminal['conclusion']=='success' and terminal['head_sha']=='2c3770116cc6d410189f260eb32cdf9d381dc163','latest collection closeout')
        v['inherited_terminal']={k:terminal[k] for k in ('id','head_sha','status','conclusion')}
        cases=[]
        for name in NAMES:
            accepted=supply['accepted'][name];folder=ROOT/SUPPLY_EVIDENCE/str(accepted['run_id']);origin=load(folder/'verification.json')
            path=folder/(name+'.stderr.txt');raw=path.read_bytes()
            need(identity(raw)==origin['proof_bindings'][path.name],'accepted source proof binding '+name)
            case=fixture(accepted,raw);cases.append(case)
        v['fixture_sources']=cases;write(PROOF/'fixture-sources.json',cases)
        cp=load(ROOT/s.boundary.n.CP);need(cp['candidate']==CANDIDATE and cp['actions_completion_confirmed'],'saved candidate')
        battle.WORK=WORK/'restore';battle.WORK.mkdir();parent=battle.restore();rom,recipe=entry.apply(parent);rom=wild.replay(rom,cp['wild_repair'])
        need(identity(rom)==CANDIDATE,'unchanged candidate');(WORK/'candidate.gba').write_bytes(rom);write(PROOF/'recipe.json',dict(entry=recipe,wild=cp['wild_repair']))
        table=struct.unpack_from('<I',rom,0x1cc)[0]-0x08000000;need(table==0x10421f4,'PP table root')
        for case in cases:need(case['pp']==[rom[table+12*x+4] if x else 0 for x in case['moves']],'original PP/candidate agreement')
        helper=s.hatch_source(s.hatch_cases({1:1,649:1}));generated={}
        def put(name,text):
            (WORK/name).write_text(text);generated[name]=identity(text.encode())
        for i,(source,target) in enumerate(egg.EMBEDDED):
            text,n=re.subn(r'\bint\s+main\s*\(','int rh_inherited_'+str(i)+'(',(ROOT/source).read_text());need(n==1,'embedded main');put(target,text)
        put('rh_helpers.c',egg.once(helper,'int main(int argc,char **argv)','int rh_unused_daycare_main(int argc,char **argv)'))
        put('rh_vectors.h',header(cases));(PROOF/'vectors.h').write_bytes((WORK/'rh_vectors.h').read_bytes())
        contracts={c['name']:dict(candidate=CANDIDATE,fixture=c,controller=identity((ROOT/C).read_bytes()),helpers=identity(helper.encode())) for c in cases}
        todo=pending(v['accepted'],contracts);need(todo,'complete only; no accepted repeats');v.update(contracts=contracts,pending_cases=todo,generated_sources=generated)
        dep=WORK/'native.d';v['host_compiles']+=1
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),C,'-lmgba','-o',str(WORK/'native')],'compile')
        need(not err,'host warnings')
        for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(name);p=(p if p.is_absolute() else ROOT/p).resolve()
            if p.parent==WORK:need(identity(p.read_bytes())==generated[p.name],'generated binding')
            else:v.setdefault('compiled_sources',{})[p.relative_to(ROOT).as_posix()]=identity(p.read_bytes())
        seed=(ROOT/m.SEED).read_bytes();stamp=(ROOT/m.SEED).stat().st_mtime_ns;need(identity(seed)==m.SEED_ID,'immutable seed')
        byname={x['name']:x for x in cases}
        for name in todo:
            fixture_path=WORK/(name+'.srm');fixture_path.write_bytes(seed);v['native_processes']+=1
            try:
                out,err=m.run([str(WORK/'native'),str(WORK/'candidate.gba'),str(fixture_path),CANDIDATE['sha256'],m.SEED_ID['sha256'],name,str(SHOTS/name)],name,900)
                result=validate(out,err,byname[name]);v['accepted'][name]=dict(run_id=v['run_id'],source_head=head,contract=contracts[name],result=result)
            except Exception as ex:
                v['failures'][name]=dict(type=type(ex).__name__,error=str(ex).replace(str(ROOT),'$REPO'));break
            write(PROOF/'verification.json',v)
        v['pending_cases']=[x for x in NAMES if x not in v['accepted']]
        need((ROOT/m.SEED).read_bytes()==seed and (ROOT/m.SEED).stat().st_mtime_ns==stamp and identity((WORK/'candidate.gba').read_bytes())==CANDIDATE,'inputs unchanged')
        need(v['protected_bindings']=={p:identity((ROOT/p).read_bytes()) for p in protected},'accepted originals unchanged')
        v['status']='PASS_RESEARCH_HATCH_SCOPED' if len(v['accepted'])==15 else 'PARTIAL_RESEARCH_HATCH'
        need(not v['failures'],'native failure retained')
    except Exception as ex:
        if v['status']=='RUNNING':v['status']='FAIL'
        v.update(error_type=type(ex).__name__,error=str(ex).replace(str(ROOT),'$REPO'));raise
    finally:
        v['screenshots']={p.name:identity(p.read_bytes()) for p in SHOTS.glob('*.ppm')}
        v['proof_bindings']={p.name:identity(p.read_bytes()) for p in PROOF.iterdir() if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=previous


def publish(v,completion=False):
    import pr16_natural_supply as s
    from pr16_learnset_compact_record import publish_resume
    good=list(v['accepted']);pending_names=[n for n in NAMES if n not in good];confirmed=v['actions_completion_confirmed']
    nextstep=NEXT if confirmed else ('15研究孵化の保存成功native/旧unit/host/ARMを再実行せず、Actions/artifact終端だけ照合。' if len(good)==15 else '研究孵化checkpointの失敗原本を確認し、未成功caseの境界だけ修復。受入済み配布/孵化/旧検証を再実行しない。')
    text=f'# PR16 Issue19: 研究タマゴ孵化後のform・技保持\n\n状態 `{v["status"]}`。限定受入 {len(good)}/15。Actions終端 `{confirmed}`。\n\nsource `{v["source_head"]}` / run `{v["run_id"]}`。候補 `{CANDIDATE["sha256"]}` / 33554432 bytes、ROM変更0。\n\n## 観測境界\n\n通常配布17件を再実行せず、その保存原本のcontinued party200byte/Collection owner512byteを新開始fixtureへ結合。これは元saveから連続再開した証明ではない。開始map/queueもfixture。原本50cycle等・技・PP・個体identityは変更せず、通常方向キーによる全歩行、実孵化callback/ニックネーム取消、form/技順/PP保持、native孵化登録Save1回、通常Save1回、fresh-core Continue後party200byteを検証する。\n\n7host書込API拒否・3guard区間。getterは区間外の読取り補助。同行個体の自然ななつき度/チェックサム変化は許容し、identity/技/HPは保持する。story/研究rank/連続配布からの到達・全Issue19・releaseは未受入。1281の原本除外方針を変更しない。\n\n| case | 原本4技 | cycle | 実歩数 | 実測run |\n| --- | --- | ---: | ---: | ---: |\n'
    for name,a in v['accepted'].items():
        r=a['result'];text+=f'| {name} | {r["moves"]} | {r["cycles"]} | {r["steps"]} | {a["run_id"]} |\n'
    text+=f'\n未成功 `{pending_names}`。今回新unit{v["new_unit_tests"]}、host compile{v["host_compiles"]}、native{v["native_processes"]}。旧配布/孵化/EXP/Bag/egg8/旧野生/ARM/Wiki再実行0。\n\n## 次\n\n{nextstep}\n'
    (ROOT/GUIDE).write_text(text);state=load(ROOT/s.m.STATE);now=datetime.datetime.now(datetime.timezone.utc)
    state['learnset_research_hatch']={k:v[k] for k in ('status','source_head','run_id','candidate','actions_completion_confirmed','issue19_complete')}
    state['learnset_research_hatch'].update(path=CP,accepted_cases=good,pending_cases=pending_names,fixture_only=True,gift_reruns=0)
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_date_jst']=(now+datetime.timedelta(hours=9)).date().isoformat()
    state['observed_head_semantics']='研究タマゴ原本個体fixtureの孵化後保持。通常配布の再実行/元saveの連続再開/全Issue19完成ではない。'
    state['observed_head_checks']=dict(scope_head=v['source_head'],runs=v.get('terminal_actions',[dict(id=v['run_id'],status='in_progress',conclusion=None)]),reason_ja='実測とActions終端を分離。一般CIのaction_requiredをsuccess扱いしない。')
    state['bp']['current_stop']=f'Issue19: 研究孵化 {len(good)}/15。{v["status"]}。全体未完。';state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='SPECIAL_WILD' if confirmed else 'RESEARCH_HATCH',goal_ja=nextstep,read_paths=[GUIDE,CP,SELF,TEST])
    for path in CODE|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    note=f'\n## {now.isoformat()}\n- Timestamp: {now.isoformat()}\n- Task: {TASK} / 研究タマゴの孵化後form・技保持\n- Version: issue19-research-hatch-v1\n- Status: '+('DONE（15case限定、全体未完）' if confirmed else 'STOPPED（保存原本から未完だけ継続）')+f'\n- Summary: 保存配布個体fixtureからの実歩行/孵化/Save/fresh Continue {len(good)}/15。元save連続再開と混同しない。原本cycleを短縮しない。\n- Files changed: 新driver/C/unit/限定Actions、checkpoint/guide/原本text、固定引継ぎMD/JSON、両ログ。\n- Verify: 新unit{v["new_unit_tests"]}、host{v["host_compiles"]}、native{v["native_processes"]}。Actions終端{confirmed}。終端専用={completion}、専用時native/unit/compile0。旧配布/孵化/ARM/Wiki不変。\n- Commit: 同branch非force push、reflected-head/remote照合。\n- Network: 固定GitHub/保存artifact/Actions。ROM・元seed非追跡。merge/release/baseline切替なし。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(note)


def record():
    from pr16_learnset_wiki_actions import current
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record exact source')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'no evidence overwrite');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_text();need('\0' not in text,'text only')
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'no private path');(dest/p.name).write_text(safe)
    v['public_evidence_bindings']={p.name:identity(p.read_bytes()) for p in dest.iterdir()};v['evidence_path']=dest.relative_to(ROOT).as_posix()
    write(ROOT/CP,v);publish(v)


def complete():
    from pr16_learnset_wiki_actions import current
    from pr16_wiki_reconcile import fetch
    current();v=load(ROOT/CP);need(len(v['accepted'])==15 and not v['failures'] and not v['actions_completion_confirmed'],'15 successes, terminal only')
    terminal=[]
    for rid in sorted(set(v['prior_runs']+[v['run_id']])):
        run=fetch('actions/runs/'+str(rid));need(run['status']=='completed' and run['path']==WF,'terminal scoped run')
        if rid==v['run_id']:
            need(run['head_sha']==v['source_head'] and run['conclusion']=='success','last run success')
            jobs=fetch('actions/runs/'+str(rid)+'/jobs?per_page=100');need(jobs['total_count']==len(jobs['jobs'])==1 and all(x['conclusion'] in ('success','skipped') for x in jobs['jobs'][0]['steps']),'all terminal steps')
        terminal.append({k:run[k] for k in ('id','head_sha','status','conclusion','path')})
    for path,binding in v['public_evidence_bindings'].items():need(identity((ROOT/v['evidence_path']/path).read_bytes())==binding,'recorded evidence unchanged')
    for path,binding in {**v['source_bindings'],**v['protected_bindings'],**v.get('compiled_sources',{})}.items():
        if path!=WF:need(identity((ROOT/path).read_bytes())==binding,'executed source unchanged '+path)
    v.update(actions_completion_confirmed=True,terminal_actions=terminal,completed_by_source=os.environ['GITHUB_SHA'])
    write(ROOT/CP,v);publish(v,True);PROOF.mkdir(parents=True,exist_ok=True)
    write(PROOF/'completion.json',dict(task=TASK,terminal_actions=terminal,native_processes=0,unit_tests=0,host_compiles=0,arm_compiles=0,rom_changes=0))


def owned():
    import pr16_natural_supply as s
    dest=ROOT/EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return {CP,GUIDE,s.m.STATE,s.m.DOC,'design/run_log.md','design/version_log.md'}|{p.relative_to(ROOT).as_posix() for p in dest.rglob('*') if p.is_file()}


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    actions=dict(execute=execute,record=record,complete=complete,guard=guard,paths=lambda:print('\n'.join(sorted(owned()))))
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
