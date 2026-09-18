#!/usr/bin/env python3
"""正規Ring受取の新しい通常戦闘suffixのみ検証。旧独立caseは再実行しない。"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_ring_policy_native.py'
SOURCE='tools/mgba_pr16_ring_policy.c'
OUT=ROOT/'.local/pr16-ring-policy-native'
SHA='4ea33fb8224b0b84493ccca6e90161da245705eb1eb0a3874691ab39cc3806cc'
SCOPE='PR16_RING_GIFT_COLD_ORDINARY_MEGA'
# (Ring正規受取の有無, 装備石, 実START入力回数)
CASES={'ring-active':(1,1012,1),'ring-unowned':(0,1012,1),
       'ring-wrong-stone':(1,1014,1),'ring-no-toggle':(1,1012,0),'ring-cancel-toggle':(1,1012,2)}
TRACE=('interaction','received','bag','equipped','saved','reloaded','walking','encounter',
       'move_menu','spent','field','saved_again','reloaded_again')
DYNAMIC={'personality','enemy_species','enemy_level','move','pp_before','pp_after','outcome',
         'walking_steps','save_before','save_after','bp_before','bp_after','total_frames','witness'}
EVENT=re.compile(rb'^RING_ENCOUNTER species=(\d+) level=(\d+) flags=([0-9a-f]{8}) mode=(\d+) used=(\d+) frame=(\d+)$',re.M)


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')


def expected(name):
    need(name in CASES,'unknown Ring policy case')
    ring,item,toggles=CASES[name];active=name=='ring-active'
    return dict(schema_version=1,status='PASS',scope=SCOPE,case=name,rom_sha256=SHA,
        species=411,item=item,mega_species=1634 if active else 411,ability=313 if active else 26,
        toggles=toggles,ring_before=0,ring_after=ring,ring_after_continue=ring,policy_mode=ring,
        usage_observed=int(active),manual_saves=2,automatic_saves=0,fresh_cores=3,
        host_write_barriers=7,ring_is_fixture=False,policy_is_fixture=False,
        initial_map_progress_party_stone_are_fixtures=True,cold_reload_before_encounter=True,
        physical_give=True,held_stone_not_consumed=True,party_inventory_bp_persisted=True,
        ordinary_battle_accepted=False,release_ready=False,warnings_errors=0)


def validate(row,stderr,name,audit):
    fixed=expected(name)
    need(type(row) is dict and set(row)==set(fixed)|DYNAMIC,'Ring policy result schema differs')
    for key,value in fixed.items():
        need(type(row[key]) is type(value) and row[key]==value,'Ring policy '+key+' differs')
    need(all(type(row[k]) is int and row[k]>=0 for k in DYNAMIC-{'witness'}),'Ring policy counters invalid')
    need(0<=row['personality']<=0xffffffff and 0<row['total_frames']<=600000,'Ring identity/frame bounds')
    need(1<=row['move']<=2048 and 1<=row['pp_before']<=64 and 0<=row['pp_after']<row['pp_before']
         and row['pp_before']-row['pp_after']<=2 and row['outcome'] in (1,4),'Ring native move/exit differs')
    need(row['save_after']==row['save_before']+2 and row['bp_after']==row['bp_before'],'Ring save/BP durability differs')
    need(1<=row['walking_steps']<=len(audit['paths']['grass'])+1024,'Ring walking bounds differ')
    trace=row['witness'];need(type(trace) is dict and set(trace)==set(TRACE)|{'toggle','mega'},'Ring witness schema')
    need(all(type(v) is int and 0<=v<=row['total_frames'] for v in trace.values()),'Ring witness counter invalid')
    need(trace['interaction']>0 and all(trace[a]<trace[b] for a,b in zip(TRACE,TRACE[1:]))
         and trace['reloaded_again']==row['total_frames'],'Ring gift/Give/cold battle/save order differs')
    if CASES[name][2]:need(trace['move_menu']<trace['toggle']<trace['spent'],'Ring toggle not in real move UI')
    else:need(trace['toggle']==0,'Ring no-toggle contains toggle')
    if name=='ring-active':need(trace['toggle']<trace['mega']<trace['spent'],'Ring Mega not before native move')
    else:need(trace['mega']==0,'Ring negative control activated Mega')
    need(type(stderr) is bytes and b'mGBA[' not in stderr,'Ring emulator warning')
    events=EVENT.findall(stderr);need(len(events)==1,'Ring original encounter missing or duplicated')
    sp,level,flags,mode,used,frame=events[0]
    observed=(int(sp),int(level),int(flags,16),int(mode),int(used),int(frame))
    need(observed==(row['enemy_species'],row['enemy_level'],4,CASES[name][0],0,trace['encounter']),
         'Ring ordinary encounter/policy original differs')
    need(any(s['species']==observed[0] and s['min']<=observed[1]<=s['max'] for s in audit['table']['slots']),
         'Ring enemy does not belong to audited native grass')
    return row


def select_cases(names):
    result=list(CASES) if names is None else list(names)
    need(result and len(result)==len(set(result)) and set(result)<=set(CASES),'invalid/duplicate Ring cases')
    return result


def grass_owner(catalogue):
    rows=[r for r in catalogue['headers'] if (r['group'],r['map'])==(96,17)
          and r['first_coordinate_owner'] is True]
    need(len(rows)==1,'current Ring grass owner missing or duplicated')
    owner=rows[0];table=owner['tables']['land']
    need(type(table['rate']) is int and table['rate']>0 and len(table['slots'])==12,'current Ring grass table invalid')
    for slot in table['slots']:
        need(all(type(slot[k]) is int for k in ('species','min','max')) and 1<=slot['species']<2048
             and 1<=slot['min']<=slot['max']<=100,'current Ring grass slot invalid')
    return owner


def flag_contract(text):
    values={};lines={}
    for line in text.splitlines():
        match=re.match(r'^\s*#define\s+(BATTLE_TYPE_(?:IS_MASTER|MASTER|LINK))\s+(.+)$',line)
        if not match:continue
        name,value=match.groups();value=re.split(r'//|/\*',value,maxsplit=1)[0].strip()
        number=re.fullmatch(r'\(?\s*(0[xX][0-9a-fA-F]+|[0-9]+)[uUlL]*\s*(?:<<\s*([0-9]+))?\s*\)?',value)
        need(number is not None,'battle flag macro is not a bounded integer expression')
        value=int(number[1],0) << (int(number[2]) if number[2] else 0)
        need(name not in values or values[name]==value,'conflicting battle flag macro')
        values[name]=value;lines[name]=line
    masters=[values[name] for name in ('BATTLE_TYPE_IS_MASTER','BATTLE_TYPE_MASTER') if name in values]
    need(masters and set(masters)=={4} and values.get('BATTLE_TYPE_LINK')==2,'master/link flag ABI differs')
    return dict(master=4,link=2,definitions=lines,
        stage_ja='自然遭遇の既存action controller入力待ち。開始時flagsとは別にmaster bitが立つ。')


def pinned_flags():
    candidates=[ROOT/'vendor/upstream/CFRU-JP/include/constants/battle.h',
                ROOT/'vendor/upstream/CFRU-JP/include/battle.h']
    candidates=[p for p in candidates if p.is_file()]
    need(candidates,'pinned battle header missing')
    texts=[p.read_text(encoding='utf-8') for p in candidates]
    result=flag_contract('\n'.join(texts))
    result['headers']={p.relative_to(ROOT).as_posix():identity(p.read_bytes()) for p in candidates}
    return result


def current_route(raw,parent):
    # 旧gear probeの固定SHAや旧受入を上書きしない。generic decoderへ渡す前に新候補を固定する。
    need(identity(raw)==dict(size=33554432,sha256=SHA),'current Ring route candidate differs')
    need(parent['map_key']==[96,17] and parent['map']['front']==[12,39], 'current Ring route front differs')
    from scripts import pr16_capture_geometry as geometry
    from scripts import pr16_p05_root_diagnostics as roots
    from scripts.pr16_purchased_gear import path as walk_path
    town=geometry.geometry(raw,96,5);grass=geometry.geometry(raw,96,17)
    need((grass['width'],grass['height'])==(24,40),'current Ring grass dimensions differ')
    paths=dict(town=walk_path(town,[24,20],[23,0]),grass=walk_path(grass,[12,39],[14,30]))
    need(paths['grass']==parent['paths']['to_grass'],'current Ring path differs from accepted gift geometry')
    need(any(p['start']==[14,30] and p['end']==[15,30] and p['behavior']==2
             for p in grass['walkable_pairs']),'current Ring grass pair not audited')
    owner=grass_owner(roots.wild_catalogue(raw))
    return dict(candidate=identity(raw),paths=paths,grass_header=owner['header'],table=owner['tables']['land'],
        geometry={str(i):identity(stable(g)) for i,g in ((5,town),(17,grass))},
        unused_embedded_town_route=True,ring_is_fixture=False,policy_is_fixture=False,
        new_emulator_processes=0,ordinary_battle_accepted=False)


def run(names=None):
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    import pr16_shop_routes as shop
    import pr16_purchased_gear as gear
    import pr16_ring_policy_successor as build
    import pr16_ring_npc_successor as gift
    m=shop.base.load();common=shop.common;names=select_cases(names)
    OUT.mkdir(parents=True,exist_ok=True);need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe native Ring output')
    recipe=json.loads((build.OUT/'candidate.json').read_bytes())
    candidate=build.OUT/'candidate.gba';raw=candidate.read_bytes()
    need(identity(raw)==recipe['candidate']==dict(size=33554432,sha256=SHA),'Ring policy candidate differs')
    parent=json.loads((gift.OUT/'candidate.json').read_bytes());need(parent['candidate']==recipe['parent'],'Ring gift parent differs')
    prior=json.loads((ROOT/'content/modernization/pr16_ring_npc_gift_checkpoint_20260918.json').read_bytes())
    for name,binding in prior['native']['sources'].items():
        need(identity((ROOT/name).read_bytes())==binding,'accepted shared gift owner changed: '+name)
    seed=ROOT/m.SEED;need(identity(seed.read_bytes())['sha256']==m.SEED_SHA,'Ring seed differs')
    audit=current_route(raw,parent);audit['flag_contract']=pinned_flags()
    group,number=parent['map_key'];npc=parent['map']['npc'];front=parent['map']['front'];host=[group,number,npc['local_id'],npc['x'],npc['y']]
    need(host==[96,17,4,12,38] and front==[12,39],'Ring physical owner differs')
    header='/* 固定候補のNPCと歩行経路。Ring/NEXTのfixtureなし。 */\n#define RP_SHA "'+SHA+'"\n'
    for key,value in dict(RP_GROUP=group,RP_MAP=number,RP_LOCAL_ID=npc['local_id'],RP_X=front[0],RP_Y=front[1]).items():header+=f'#define {key} {value}U\n'
    header+='#define RP_ORDINARY_ACTIVE_FLAGS '+str(audit['flag_contract']['master'])+'U\n'
    generated={'pr16_ring_policy_generated.h':header,'pr16_gear_route.h':gear.route_header(audit)}
    paths={SELF,SOURCE,build.SELF,build.SOURCE,build.HEADER,gift.SELF,gift.SOURCE,gift.HEADER,
           gear.SELF,gear.SOURCE,'scripts/pr16_capture_geometry.py','scripts/pr16_p05_root_diagnostics.py','overlays/cfru/integration.h','overlays/cfru/runtime.h',
           shop.SELF,shop.SOURCE,shop.base.PARENT,shop.base.PARENT_C,gear.parent.SELF,gear.parent.SOURCE}
    for i,(src,target) in enumerate(m.EMBEDDED):generated[target]=m.embed((ROOT/src).read_text(),'ring_policy_embedded_'+str(i));paths.add(src)
    for src,target,label in ((shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','ring_policy_breeding'),
                            (shop.SOURCE,'pr16_capture_shop_helpers.c','ring_policy_shop'),
                            (gear.parent.SOURCE,'pr16_gear_capture_helpers.c','ring_policy_capture'),
                            (gear.SOURCE,'pr16_ring_gear_helpers.c','ring_policy_gear')):
        generated[target]=m.embed((ROOT/src).read_text(),label)
    bindings={p:identity((ROOT/p).read_bytes()) for p in sorted(paths)}
    protected={p:identity(p.read_bytes()) for p in (candidate,seed)}
    result=dict(schema_version=1,status='NOT_RUN',candidate=recipe['candidate'],parent=recipe['parent'],
        physical_host=host,oracle=audit,sources=bindings,generated={p:identity(t.encode()) for p,t in generated.items()},
        requested_cases=names,results=[],failures=[],guard_checks=[],actual_new_processes=0,
        successful_fresh_cores=0,accepted_native_cases_replayed=0,ordinary_battle_accepted=False,
        ring_full_acceptance=False,release_ready=False)
    (OUT/'result.json').write_bytes(stable(result))
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-ring-policy-',dir=ROOT/'.local') as td:
            work=Path(td)
            for name,text in generated.items():
                (work/name).write_text(text);dest=OUT/'generated'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
            binary=work/'runner'
            _,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(ROOT/SOURCE),'-lmgba','-o',str(binary)],OUT/'compile',120)
            need(common.require_exited(process)==0,'Ring policy controller compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],OUT/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);result['guard_checks'].append(guard)
            for name in names:
                private=work/(name+'.srm');shutil.copyfile(seed,private);result['actual_new_processes']+=1
                stdout,stderr,process=common.capture([str(binary),str(candidate),str(private),SHA,m.SEED_SHA,name,str(OUT/name)],OUT/name,600)
                try:
                    need(common.require_exited(process)==0,'Ring policy native process failed')
                    row=validate(common.strict_json(stdout),stderr,name,audit)
                    result['results'].append(dict(case=name,native_result=row,process=process));result['successful_fresh_cores']+=row['fresh_cores']
                except (ValueError,RuntimeError,KeyError,TypeError) as exc:
                    result['failures'].append(dict(case=name,error=str(exc),process=process));break
                finally:(OUT/'result.json').write_bytes(stable(result))
        need(protected=={p:identity(p.read_bytes()) for p in protected},'Ring original input changed')
        need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'Ring source changed during native run')
        result['status']='PASS_RING_ORDINARY_SUFFIX_ONLY' if len(result['results'])==len(names) else 'FAIL'
    finally:(OUT/'result.json').write_bytes(stable(result))
    need(result['status']=='PASS_RING_ORDINARY_SUFFIX_ONLY','Ring native failed; preserve originals without acceptance')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sources','generated','oracle')},ensure_ascii=False))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cases',nargs='+',choices=CASES)
    run(parser.parse_args().cases)
