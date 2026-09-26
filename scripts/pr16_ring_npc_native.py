#!/usr/bin/env python3
"""新規Ring NPCの実会話・保存再開だけを検証。既存の受入caseは実行しない。"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_ring_npc_native.py'
SOURCE='tools/mgba_pr16_ring_npc.c'
OUT=ROOT/'.local/pr16-ring-npc-native'
CASES={'gift-save-revisit':1,'locked-save-revisit':3,'full-save-revisit':4}
TRACE=('interaction','returned','repeat','repeat_returned','saved','reloaded','revisit','finished')
SCOPE='PR16_RING_NPC_GIFT_SAVE_CONTINUE'


def need(ok,message):
    if not ok: raise ValueError(message)


def identity(raw):
    return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()


def validate(row,name,sha,host):
    result=CASES[name];amount=int(result==1)
    fixed=dict(schema_version=1,status='PASS',scope=SCOPE,case=name,rom_sha256=sha,
        initial_result=result,revisit_result=2 if result==1 else result,ring_before=0,
        ring_after=amount,ring_after_continue=amount,manual_saves=1,automatic_saves=0,
        fresh_cores=2,host_write_barriers=7,physical_host=host,ring_is_fixture=False,
        initial_progression_map_capacity_are_fixtures=True,party_and_other_inventory_preserved=True,
        ordinary_battle_accepted=False,ring_full_acceptance=False,release_ready=False,warnings_errors=0)
    need(type(row) is dict and set(row)==set(fixed)|{'save_before','save_after','bp_before','bp_after','total_frames','witness'},'native Ring schema differs')
    for key,value in fixed.items():
        need(type(row[key]) is type(value) and row[key]==value,'native Ring '+key+' differs')
    for key in ('save_before','save_after','bp_before','bp_after','total_frames'):
        need(type(row[key]) is int and row[key]>=0,'invalid native counter '+key)
    need(row['save_after']==row['save_before']+1 and row['bp_before']==row['bp_after'],'native save/BP durability differs')
    trace=row['witness']
    need(type(trace) is dict and set(trace)==set(TRACE),'native witness schema differs')
    frames=[trace[k] for k in TRACE]
    need(all(type(f) is int and 0<f<=600000 for f in frames) and all(a<b for a,b in zip(frames,frames[1:]))
        and frames[-1]==row['total_frames'],'native Ring physical sequence differs')
    return row


def run():
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    import pr16_shop_routes as shop
    import pr16_ring_npc_successor as build
    m=shop.base.load();common=shop.common
    OUT.mkdir(parents=True,exist_ok=True)
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe native output')
    recipe=json.loads((build.OUT/'candidate.json').read_bytes())
    candidate=build.OUT/'candidate.gba';sha=recipe['candidate']['sha256']
    need(identity(candidate.read_bytes())==recipe['candidate'],'new Ring candidate differs')
    seed=ROOT/m.SEED;need(identity(seed.read_bytes())['sha256']==m.SEED_SHA,'native seed differs')
    group,number=recipe['map_key'];npc=recipe['map']['npc'];front=recipe['map']['front']
    host=[group,number,npc['local_id'],npc['x'],npc['y']]
    with (ROOT/'manifests/item_ids.csv').open(encoding='utf-8',newline='') as stream:
        keys=[int(r['id'],0) for r in csv.DictReader(stream) if r['pocket']=='POCKET_KEY_ITEMS' and int(r['id'],0)!=580]
    need(len(keys)>=30 and len(keys)==len(set(keys)),'key pocket fixture catalogue insufficient')
    header='/* Current candidate map and manifest fixtures; Ring is never injected. */\n'
    for key,value in dict(RN_GROUP=group,RN_MAP=number,RN_LOCAL_ID=npc['local_id'],RN_FRONT_X=front[0],RN_FRONT_Y=front[1]).items():
        header+=f'#define {key} {value}U\n'
    header+='#define RN_SHA "'+sha+'"\nstatic const unsigned rn_key_items[]={'+','.join(str(i)+'U' for i in keys)+'};\n'
    generated={'pr16_ring_npc_generated.h':header}
    sources={SELF,SOURCE,build.SELF,build.SOURCE,build.HEADER,'manifests/item_ids.csv',shop.SELF,shop.SOURCE,shop.base.PARENT,shop.base.PARENT_C}
    for i,(src,target) in enumerate(m.EMBEDDED):
        generated[target]=m.embed((ROOT/src).read_text(),'ring_embedded_'+str(i));sources.add(src)
    for src,target,label in ((shop.base.PARENT_C,'pr16_shop_breeding_helpers.c','ring_breeding'),(shop.SOURCE,'pr16_ring_shop_helpers.c','ring_shop')):
        generated[target]=m.embed((ROOT/src).read_text(),label)
    bindings={p:identity((ROOT/p).read_bytes()) for p in sorted(sources)}
    protected={p:identity(p.read_bytes()) for p in (candidate,seed)}
    result=dict(schema_version=1,status='NOT_RUN',candidate=recipe['candidate'],physical_host=host,
        sources=bindings,generated={p:identity(t.encode()) for p,t in generated.items()},results=[],failures=[],
        guard_checks=[],actual_new_processes=0,successful_fresh_cores=0,accepted_native_cases_replayed=0,
        ring_full_acceptance=False,ordinary_battle_accepted=False,release_ready=False)
    (OUT/'result.json').write_bytes(stable(result))
    try:
        with tempfile.TemporaryDirectory(prefix='pr16-ring-npc-',dir=ROOT/'.local') as td:
            work=Path(td)
            for name,text in generated.items():
                (work/name).write_text(text)
                dest=OUT/'generated'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
            binary=work/'runner'
            _,_,process=common.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(ROOT/SOURCE),'-lmgba','-o',str(binary)],OUT/'compile',120)
            need(common.require_exited(process)==0,'native Ring controller compile failed')
            for guard in m.GUARDS:
                stdout,stderr,process=common.capture([str(binary),'--guard-check',guard],OUT/('guard-'+guard),10)
                m.validate_guard(stdout,stderr,process);result['guard_checks'].append(guard)
            # New Ring cases only. Sequential executions make individual failures attributable.
            for name in CASES:
                private=work/(name+'.srm');shutil.copyfile(seed,private)
                result['actual_new_processes']+=1
                stdout,stderr,process=common.capture([str(binary),str(candidate),str(private),sha,m.SEED_SHA,name,str(OUT/name)],OUT/name,360)
                try:
                    need(common.require_exited(process)==0,'native Ring process failed')
                    row=validate(common.strict_json(stdout),name,sha,host)
                    need(b'mGBA[' not in stderr,'native Ring emulator warning')
                    result['results'].append(dict(case=name,native_result=row,process=process))
                    result['successful_fresh_cores']+=row['fresh_cores']
                except (ValueError,RuntimeError,KeyError,TypeError) as exc:
                    result['failures'].append(dict(case=name,error=str(exc),process=process))
                    # Do not repeat the same broken field/ABI path in other cases.
                    break
        need(protected=={p:identity(p.read_bytes()) for p in protected},'private source input changed')
        need(bindings=={p:identity((ROOT/p).read_bytes()) for p in bindings},'native source changed')
        result['status']='PASS_NPC_GIFT_SAVE_ONLY' if len(result['results'])==len(CASES) else 'FAIL'
    finally:
        (OUT/'result.json').write_bytes(stable(result))
    need(result['status']=='PASS_NPC_GIFT_SAVE_ONLY','Ring native failed; keep unaccepted and inspect originals')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sources','generated')},ensure_ascii=False))
    return result


if __name__=='__main__': run()
