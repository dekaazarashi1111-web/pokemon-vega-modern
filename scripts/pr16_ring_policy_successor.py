#!/usr/bin/env python3
"""Ring普通戦闘bridgeの固定親・既存ownerの最小コンパイル境界を照合。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SELF='scripts/pr16_ring_policy_successor.py'
OUT=ROOT/'.local/pr16-ring-policy-successor'
PARENT_SHA='72fbca91cd6ee1082198678ccaed76bcb76dfd19ce9f6f3c26309745b2f09ac0'
BASE=0x08000000
SYMBOLS=('VegaBattlePolicyBegin','cfru_integration_state','cfru_integration_select_mechanic',
         'cfru_integration_battle_end','HandleNewBattleRamClearBeforeBattle')


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):
    return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')


def calls(raw,start,end):
    from scripts.pr16_bp_party_retention_successor import decode_thumb_bl
    result=[]
    need(BASE<=start<end<=BASE+len(raw) and start%2==end%2==0,'invalid call search bound')
    for addr in range(start,end-2,2):
        data=raw[addr-BASE:addr-BASE+4];a,b=struct.unpack('<HH',data)
        if a&0xF800==0xF000 and b&0xF800==0xF800:
            result.append(dict(address=addr,target=decode_thumb_bl(addr,data),bytes=data.hex()))
    return result


def run():
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    import pr16_ring_npc_successor as gift
    import pr16_ring_npc_gift_record as record
    from scripts.build_battle_core import parse_offsets
    OUT.mkdir(parents=True,exist_ok=True)
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)),'unsafe policy output')
    prior=json.loads((ROOT/record.REPORT).read_bytes())
    for source in (gift.SELF,gift.SOURCE,gift.HEADER,'tools/mgba_pr16_ring_npc.c'):
        need(identity((ROOT/source).read_bytes())==prior['source_bindings'][source],'accepted gift owner changed')
    recipe=gift.run();raw=(gift.OUT/'candidate.gba').read_bytes()
    need(identity(raw)==recipe['candidate']==dict(size=33554432,sha256=PARENT_SHA),'gift parent changed')
    metadata=json.loads((ROOT/'build/stages/06_battle_core.json').read_bytes())
    symbols=metadata['upstream_runs'][0]['integration_symbols']
    need(symbols==metadata['upstream_runs'][1]['integration_symbols'],'T06 independent symbols differ')
    begin=symbols['VegaBattlePolicyBegin'];limit=symbols['VegaBattlePolicyEnd']
    need(begin==152200948 and 0<limit-begin<=1024,'known ordinary begin boundary changed')
    begin_calls=calls(raw,begin,limit)
    callers=[r for r in calls(raw,0x09000000,0x09200000) if r['target']==begin]
    need(len(callers)<=16,'ordinary begin call search exceeded bound')
    for row in callers:
        at=row['address']-BASE
        row['context_start']=row['address']-32
        row['context_hex']=raw[at-32:at+36].hex()
    bounded=raw[begin-BASE:limit-BASE]
    binary=OUT/'begin.bin';binary.write_bytes(bounded)
    dis=subprocess.check_output(['arm-none-eabi-objdump','-D','-b','binary','-m','arm','-M','force-thumb',
        '--adjust-vma='+hex(begin),str(binary)],text=True)
    (OUT/'original-begin.txt').write_text(dis.replace(str(binary),'ordinary-begin.bin'),encoding='utf-8')
    callees={}
    for target in sorted(set(r['target'] for r in begin_calls)):
        if 0x09000000<=target<0x09200000:
            callees[f'{target:08x}']=dict(address=target,first_64_hex=raw[target-BASE:target-BASE+64].hex())
    (OUT/'call-context.json').write_bytes(stable(dict(begin=begin,end=limit,begin_calls=begin_calls,callers=callers,callees=callees)))
    cache=ROOT/'build/battle-core'/metadata['fingerprint']
    linked=[]
    for index in (1,2):
        offset_file=cache/f'run-{index}'/'offsets.ini';object_file=cache/f'run-{index}'/'linked.o'
        entry=dict(index=index,offsets_available=offset_file.is_file(),object_available=object_file.is_file())
        if offset_file.is_file():
            data=offset_file.read_bytes();need(identity(data)['sha256']==metadata['upstream_runs'][index-1]['offsets']['sha256'],'offsets source digest changed')
            offsets=parse_offsets(data.decode('utf-8'))
            entry['symbols']={name:offsets.get(name) for name in SYMBOLS}
            entry['offsets_identity']=identity(data)
        linked.append(entry)
    result=dict(schema_version=1,status='BOUNDED_POLICY_OWNER_CONTEXT',source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        run_id=int(os.environ['GITHUB_RUN_ID']),parent=recipe['candidate'],original_begin=begin,
        begin_end=limit,begin_identity=identity(bounded),begin_calls=begin_calls,callers=callers,
        callees=callees,linked_cache=linked,metadata_keys=list(metadata),run_keys=list(metadata['upstream_runs'][0]),
        new_emulator_processes=0,accepted_native_cases_replayed=0,policy_candidate_built=False,
        ordinary_battle_accepted=False,release_ready=False)
    (OUT/'owner.json').write_bytes(stable(result));print(json.dumps(result,ensure_ascii=False))
    return result


if __name__=='__main__':run()
