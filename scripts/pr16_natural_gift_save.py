#!/usr/bin/env python3
"""配布のcounter一増加という未検証前提を修正。保存済み孵化/20unitは不変。"""
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_natural_supply as s
need=s.need
SELF='scripts/pr16_natural_gift_save.py'
TEST='tests/test_pr16_natural_gift_save.py'
PRIOR=36102544792
BASE_RUN=s.m.run


def validate(out,err,pp):
    r=json.loads(out,object_pairs_hook=s.egg.strict_pairs)
    fixed={'schema_version':1,'status':'PASS','case':s.GIFT,'candidate_sha256':s.CANDIDATE['sha256'],'species':1029,'level':50,'moves':[204,235,382,738],'pp':[pp[x] for x in (204,235,382,738)],'fresh_cores':2,'denied_host_write_apis':7,'guarded_phases':3,'party_preserved_bytes':200,'initial_party_map_ring_flag_are_fixtures':True,'all_owners_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0,'gift_counter_steps':2}
    dynamic={'boundary','claimed','returned','saved','continued','repeat','save_counters','npc_script'}
    need(set(r)==set(fixed)|dynamic,'配布結果schema')
    for k,v in fixed.items():need(type(r[k])is type(v) and r[k]==v,'配布結果 '+k)
    keys=('boundary','claimed','returned','saved','continued','repeat')
    need(all(type(r[k])is int for k in keys) and 0<r[keys[0]] and all(r[a]<r[b] for a,b in zip(keys,keys[1:])) and r['repeat']<100000,'配布chronology')
    counters=r['save_counters'];need(type(counters)is list and len(counters)==5 and all(type(x)is int and x>=0 for x in counters),'Save counter型')
    need(counters==[counters[0],counters[0]+2,counters[0]+3,counters[0]+3,counters[0]+3],'配布二遷移/手動一遷移/Continue/再受取不変')
    need(type(r['npc_script'])is int and 0x08000000<=r['npc_script']<0x0a000000,'NPC script')
    transitions=re.findall(rb'^SUPPLY_GIFT_SAVE frame=(\d+) before=(\d+) after=(\d+) lock=(\d+) count=(\d+) pc=([0-9a-f]{8})$',err,re.M)
    need(len(transitions)==err.count(b'SUPPLY_GIFT_SAVE ')==2,'二遷移の全raw witness')
    last=r['boundary']
    for i,row in enumerate(transitions):
        f,before,after,lock,count=map(int,row[:5]);pc=int(row[5],16)
        need(last<f<r['returned'] and ((i==0 and f<r['claimed']) or (i==1 and f>=r['claimed'])) and before==counters[0]+i and after==before+1 and lock==1 and count==i+1 and (0x08000000<=pc<0x0a000000 or 0x03000000<=pc<0x03008000),'guarded配布中の一段ずつの遷移')
        last=f
    party=re.findall(rb'^SUPPLY_PARTY stage=(fixture|claimed|saved|continued|repeat) counter=(\d+) hex=([0-9a-f]+)$',err,re.M)
    need(len(party)==err.count(b'SUPPLY_PARTY ')==5 and [x[0] for x in party]==[b'fixture',b'claimed',b'saved',b'continued',b'repeat'],'配布party原本')
    need([int(x[1]) for x in party]==counters,'原本Save counter')
    raw=[bytes.fromhex(x[2].decode()) for x in party];need(len(raw[0])==100 and all(len(x)==200 for x in raw[1:]),'whole party')
    need(raw[0]==raw[1][:100] and raw[1]==raw[2]==raw[3]==raw[4],'元partyと配布保存不変')
    child=raw[1][100:];hp,maximum=struct.unpack_from('<HH',child,86)
    need(struct.unpack_from('<H',child,32)[0]==1029 and child[84]==50 and list(struct.unpack_from('<4H',child,44))==fixed['moves'] and list(child[52:56])==fixed['pp'] and child[40]==0 and 0<hp<=maximum,'独立raw配置/技/PP/HP')
    need(b'mGBA[' not in err and err.count(b'original core destroyed; new core boot and normal Continue')==1 and b'host write after observation barrier' not in err,'core lifecycle/guard')
    return dict(r,party_identity=s.identity(raw[1]),gift_counter_witnesses=[{'frame':int(x[0]),'before':int(x[1]),'after':int(x[2]),'pc':int(x[5],16)} for x in transitions])


def inherited():
    folder=s.ROOT/s.EVIDENCE/str(PRIOR);v=s.load(folder/'verification.json')
    need(v['source_head']=='e98e3a2581419a721e3e3ad7b0f351ba84371119' and v['new_unit_tests']==20 and v['status']=='PARTIAL_NATURAL_SUPPLY' and set(v['accepted'])==set(s.HATCH),'既存20unit/孵化2case原本')
    for path,binding in v['source_bindings'].items():
        if path not in (s.C,s.WF):need(s.identity((s.ROOT/path).read_bytes())==binding,'無関係source不変 '+path)
    for name in ('unit.process.json','unit.stdout.txt','unit.stderr.txt'):
        need(s.identity((folder/name).read_bytes())==v['proof_bindings'][name],'unit原本不変 '+name)
    need(s.load(folder/'unit.process.json')=={'returncode':0,'timed_out':False} and (folder/'unit.stderr.txt').read_bytes().count(b' ... ok\n')==20,'20unitの保存成功')
    return v



def flow(acquisition,claim):
    ensure=acquisition.split('static u8 ensure_save(void)',1)[1].split('static const AcqFossilRecipe',1)[0]
    pending=acquisition.split('VegaAcqPendingTransaction *VegaAcqEngine_GetPending(void)',1)[1].split('u8 VegaAcqEngine_IsUnlockSatisfied',1)[0]
    gift=claim.split('u16 FloetteGift_Claim(void)',1)[1]
    need('if (!ensure_save())' in pending and 'return &save_block()->pending;' in pending,'GetPending owns migration')
    need(ensure.index('if (!VegaAcqSaveValidate(save_block()))')<ensure.index('VegaAcqSaveMigrate(')<ensure.index('persist_standard_save() || !persist_save_sector()'),'旧内側save移行の事前保存')
    need(gift.index('pending = FN_ACQ_GET_PENDING();')<gift.index('if (!create_gift() || !deliver_gift(&token))')<gift.index('if (!persist_standard() || !persist_sector())'),'移行保存→配布→配布保存のsource順序')
    return {'pre_delivery_save':'GetPending -> ensure_save -> migrate inner acquisition save -> persist_standard_save','post_delivery_save':'FloetteGift_Claim -> create/deliver -> flags -> persist_standard','first_transition_party_count':1,'second_transition_party_count':2}


def source_contract():
    pins={'overlays/acquisition_runtime/acquisition_engine_adapter_rom.c':'df58c5897a1802e90695ef1afb21fc388a87b6dd','overlays/modernization_floette_gift/modernization_floette_gift.c':'e6d9cbbd2fb5595a1e7b5299c7a6d82fe889f9f0'}
    data={}
    for name,pin in pins.items():
        raw=(s.ROOT/name).read_bytes();need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==pin,'実runtime sourceのGit blob '+name);data[name]=raw
    return dict(flow(*[raw.decode() for raw in data.values()]),source_bindings={name:s.identity(raw) for name,raw in data.items()})

def scoped_run(command,name,*args,**kwargs):
    if name=='unit':
        inherited()
        s.write(s.PROOF/'gift-save-impact.json',{'prior_run':PRIOR,'prior_status':'PARTIAL_NATURAL_SUPPLY','prior_failed_boundary':'gift counter 2->4 before manual Save; old assumption 2->3','accepted_hatch_reruns':0,'inherited_unit_tests':20,'inherited_unit_reruns':0,'candidate_unchanged':s.CANDIDATE,'rom_changes':0,'policy':'GetPending migration save with party1, then delivery save with party2; host write barrier throughout','source_contract':source_contract(),'unit_reexecution_reason':'12 gift validator tests are impacted by corrected counter/party chronology; inherited 20 tests remain unexecuted'})
        command=[sys.executable,'-B','-m','unittest','tests.test_pr16_natural_gift_save','-v']
    return BASE_RUN(command,name,*args,**kwargs)


def configure():
    s.CODE.update((SELF,TEST));s.m.run=scoped_run;s.gift_validate=validate


if __name__=='__main__':
    configure();actions={'execute':s.execute,'record':s.record,'complete':s.complete,'guard':s.guard,'paths':lambda:print('\n'.join(sorted(s.owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
