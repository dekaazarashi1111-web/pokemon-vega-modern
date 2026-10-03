#!/usr/bin/env python3
"""Save32原本の独立受入。入力/ROMを変更せずnative再走もしない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save32_measure as m
from pr16_story_after_maori import need,identity
SOURCE='9432cfd03ac1d93bd59d7db296ab49ff20d766d7'
RUN,JOB,ARTIFACT=37121677872,111198849680,11273920453
ARCHIVE=dict(size=323646,sha256='41b44ca50c8e92d6cb8bb037c89708a6aa1b44c43b1f4f3148735d55a1878cec')
OUTPUT=dict(size=131088,sha256='df4a9c40ce888a26f88493d69e7d37f9b0ea13b2fce793c4f2e34ac0380cd871')
PARTY='05a09e6f173b5c2938202d5bdb70a97c7a2daad30192aca74ba0d88d03883974'
FLASH='994de205183309f23e538c620da87f5ec265afd24855ea3792e35002526d90cf'
CP='content/modernization/pr16_story_save32_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE32_JA.md'
EVIDENCE='content/modernization/pr16_story_save32_evidence'
VISUAL='content/modernization/pr16_story_save32_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
PARTIES=[m.a.PARTY,'b7b5065bbef8aab00a72370bf9e4c70a296a98a7e711370cde51c55c90c84d8f','cbfd8184398800561c8114ec1f97acc94be63e2d753a563ba20ba7b3a11c07ce','cdee8aef8d5602bf8d7594d6974eb47ce9c0a91e7aaa61ae0f6922d28928019e','78a4f83043d21b9a965afaaaca468d58e4578a8bafff31ba51ebace9ffa57025',PARTY]
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations']
    need(len(ao)==62 and len(bo)==2,'全64画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(138,10046) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[14,14],[14,16],[14,17],[14,18],[14,18],[15,18],[15,18],[15,19],[15,19]]+[[x,19]for x in range(16,21)]+[[21,19]]*48
    for i,o in enumerate(ao):
        facing=1 if i in (0,1,2,3,6,7)else 4
        pi=0 if i<25 else 1 if i<31 else 2 if i<33 else 3 if i<40 else 4 if i<48 else 5
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==facing and o['party_count']==4 and o['rp']==0 and o['party_sha256']==PARTIES[pi],'全位置/RP/実HP・PP推移')
        need(o['callback2']==(m.m.BATTLE if 17<=i<=52 else m.m.FIELD) and o['lock']==(0 if i<14 or i in (53,61)else 1) and o['field'] is (i<14 or i in (53,61)),'視線/戦闘/通常保存を区別')
        need(o['battle_flags']==(0 if i<17 else 12) and o['battle_outcome']==(0 if i<50 else 1),'trainer1勝だけ。残留outcome追加なし')
        need(o['save_counter']==(31 if i<60 else 32),'Save32 counter境界')
        if i<57:need(o['flash_sha256']==m.a.FLASH,'通常Save前Flash不変')
        elif i<60:need(o['flash_sha256']not in (m.a.FLASH,FLASH),'途中write3状態')
        else:need(o['flash_sha256']==FLASH,'全Flash終端')
    need(len({ao[i]['flash_sha256']for i in (57,58,59)})==3,'別の部分write3状態')
    for o in bo:
        m.m.idle(o,32)
        need(o['xy']==[21,19] and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==ao[-1]['ledger_sha256'],'独立Continue全状態')
    return dict(status='PASS_CAVE_SOUTH_TRAINER353_SAVE32_SCOPED',trainer_victories=1,trainer_id=353,wild_victories=0,escapes=0,captures=0,
        ordinary_saves=1,save_counter=32,map=[1,73],xy=[21,19],facing=4,party_count=4,rp=0,encounter_transition=14,battle_start=17,battle_outcome_observation=50,victory_field_return=53,
        save_success_text_observation=60,stable_field_observation=61,partial_write_observations=[57,58,59],progress_inputs=138,continue_inputs=13,screen_count=64,native_processes=2,
        record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,
        trainer352_accepted=False,trainer353_accepted=True,teleport_accepted=False,east_stair_accepted=False,cave_crossing_complete=False,
        national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)
def flags_delta(a,b):
    delta=[(i*8+bit,(u>>bit)&1,(v>>bit)&1)for i,(u,v)in enumerate(zip(a,b))for bit in range(8)if (u^v)&(1<<bit)]
    need(len(a)==len(b) and delta==[(1280+353,0,1)],'trainer353の既定flagだけ')
    return delta

def boundary(before,after,cold,rom):
    s=parent.sectors
    need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save31/32とcold全Save/RTC')
    need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,31,s.LAYOUT);new,rb=s.bank(after,0,32,s.LAYOUT);_,rc=s.bank(after,0xe000,31,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save31bank全57344bytes不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,a,b)for i,(a,b)in enumerate(zip(x,y))if a!=b]
    need(changes==[(55,4,0),(86,68,66)] and identity(y)['sha256']==PARTY,'party差分はPP4→0とHP324→322だけ')
    modeled=bytearray(x)
    for expected,(pp,hp) in zip(PARTIES[1:],[(3,324),(3,322),(2,322),(1,322),(0,322)]):
        modeled[55]=pp;struct.pack_into('<H',modeled,86,hp);need(identity(modeled)['sha256']==expected,'全中間partyを保存親から独立再構成')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new)
    need(bag_a==bag_b and (money_a,money_b)==(12712,13128),'Bag不変・通常報酬416円だけ')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6])
    need(bool(ext[(4367-2304)//8]&(1<<((4367-2304)%8))),'flag4367受入済み状態保持')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,a,b)for i,(a,b)in enumerate(zip(va,vb))if a!=b]
    need(vd==[(0x4021,93,103),(0x4022,2,0)],'補助var2件のみ・story var維持')
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot
    w=ScriptWalker(RomImage('save32-trainer-owner',rom));w.add_root(ScriptRoot(0x093709a0,'cave_local7','object'));graph=w.walk()
    need(not graph['diagnostics'] and [r['value']for r in graph['references']if r['category']=='trainer' and r['access']=='battle']==[353],'実NPCのtrainer353正規owner')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==7 and va[0x72]==vb[0x72]==1,'全国図鑑未解禁/story維持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6973,1782),'全Save差分会計')
    return dict(party_changes=changes,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,reward=416,physical_flag_deltas=fd,
        auxiliary_var_deltas=vd,auxiliary_runtime_owners_resolved=False,old_bank_preserved_bytes=57344,pc_s61e_preserved=True,s61e_crc_verified=True,
        sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':7,'4072':1},badge_count=1,
        all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),trainer_owner=graph)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes())
    need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==64,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][61] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    decisions=[dict(observation=i,move_slot=3)if i in (24,32,39,47)else dict(observation=i,keep_current=True)for i in (24,32,36,39,44,47)]
    need(measured['battle']==dict(start=17,finish=53,trainer=True,outcome=1,used=[0,0,0,4],decisions=decisions),'れいとうビーム4回/交代拒否2回')
    need(measured['route']==m.ROUTE[:11] and measured['teleport']is None and measured['story_event']is None,'21,19で戦闘・東階段/teleport未到達')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection'] and inspection['route']==m.ROUTE,'保存静的原本と実測区別')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE)
    return result
