#!/usr/bin/env python3
"""Save31の保存原本を独立照合。native/既受入試験は再実行しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save31_measure as m
from pr16_story_after_maori import need,identity
SOURCE='accd52953d20245894396a0444d39f56b8d78a35'
RUN,JOB,ARTIFACT=37120372607,111195148880,11273187310
ARCHIVE=dict(size=166942,sha256='d5a5857b3fb520f5b12cd6825bf7d1760ac136dc35cc6d3cc021d3fd9a9938f3')
OUTPUT=dict(size=131088,sha256='f0d2c1afb303390fb415e52090379a234a813f1bd7854ea77d92f5cb7b50ac2f')
PARTY='89668f27bceb5f63f83fd29274c74307f2b3be9c4fa4b200c903283c835f0eee'
FLASH='3d66bdd9a78ec007445f60a2c0b2653aef549c760d1c4f455e2e2e5d77de85ee'
CP='content/modernization/pr16_story_save31_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE31_JA.md'
EVIDENCE='content/modernization/pr16_story_save31_evidence'
VISUAL='content/modernization/pr16_story_save31_visual_review.json'
shared=m.a.shared
transport=m.a.transport
parent=m.a.parent

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations']
    need(len(ao)==20 and len(bo)==2,'全22画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(52,3006) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[13,6],[13,7],[13,7],[14,7],[14,7],[14,8],[14,10],[14,11],[14,12]]+[[14,14]]*11
    for i,o in enumerate(ao):
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==(4 if i in (2,3) else 1) and
             o['party_count']==4 and o['rp']==0 and o['party_sha256']==PARTY,'全位置/RP/party')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if i<11 or i==19 else 1) and o['field'] is (i<11 or i==19),'通常段差2辺/story座標/保存/解錠')
        need(o['battle_flags']==o['battle_outcome']==0,'今回戦闘なし')
        need(o['save_counter']==(30 if i<17 else 31),'sector counter先行を全Save完了にしない')
        if i<14:need(o['flash_sha256']==m.a.FLASH,'通常Save前のFlash全byte不変')
        elif i<18:need(o['flash_sha256'] not in (m.a.FLASH,FLASH),'部分write4状態。counter31でも未完')
        else:need(o['flash_sha256']==FLASH,'Save31全Flash')
    need(len({ao[i]['flash_sha256']for i in (14,15,16,17)})==4,'別の部分write4状態')
    for o in bo:
        m.m.idle(o,31)
        need(o['xy']==[14,14] and o['facing']==1 and o['field'] is True and o['battle_flags']==o['battle_outcome']==0 and
             o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==ao[-1]['ledger_sha256'],'独立Continue全状態')
    return dict(status='PASS_CAVE_SOUTH_OWNER_SAVE31_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,
        ordinary_saves=1,save_counter=31,map=[1,73],xy=[14,14],facing=1,party_count=4,rp=0,
        ledge_observations=[6,9],story_coordinate_observation=9,save_success_text_observation=18,stable_field_observation=19,
        partial_write_observations=[14,15,16,17],counter31_partial_write_observation=17,progress_inputs=52,continue_inputs=13,screen_count=22,native_processes=2,
        record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,
        hm05_taught_or_used=False,trainer352_accepted=False,trainer353_accepted=False,teleport_accepted=False,cave_crossing_complete=False,
        south_ledges_accepted=True,story_flag4367_accepted=True,national_dex_unlocked=False,natural_growth_accepted=False,
        natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def story_extension(before,after):
    a,b=parent.s61e_record(before),parent.s61e_record(after)
    changes=[(i,u,v)for i,(u,v)in enumerate(zip(a,b))if u!=v]
    need(changes==[(257,65,193)],'拡張payloadはflag4367/index2063だけ0→1')
    need(not(a[(4367-2304)//8]&(1<<((4367-2304)%8))) and b[(4367-2304)//8]&(1<<((4367-2304)%8)),'正規ownerのflag4367')
    return dict(payload_changes=changes,flag4367=[0,1],s61e_crc_and_complement_checked=True,all_other_expanded_payload_preserved=True)

def boundary(before,after,cold,rom):
    s=parent.sectors
    need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save30/31とcold全Save/RTC')
    need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,30,s.LAYOUT);new,rb=s.bank(after,0xe000,31,s.LAYOUT);_,rc=s.bank(after,0,30,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'前Save30 bank全57344byte不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,a,b)for i,(a,b)in enumerate(zip(x,y))if a!=b]
    need(changes==[] and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new)
    need(bag_a==bag_b and money_a==money_b==12712,'全Bag/HM05/所持金不変')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC payload不変')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0] and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'section13の拡張領域以外不変')
    extension=story_extension(before[old[13]+0x7d0:old[13]+0xde6],after[new[13]+0x7d0:new[13]+0xde6])
    need(struct.unpack_from('<BBHBHHBB',rom,0x214656)==(0x69,0x29,4367,0x16,0x4071,7,0x6b,2),'観測に基づく正規owner全11byte。末尾は0x6b')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new)
    vd=[(0x4000+i,a,b)for i,(a,b)in enumerate(zip(va,vb))if a!=b]
    need(fa==fb and vd==[(0x4021,87,93),(0x4022,1,2),(0x4071,6,7)],'legacy flags不変、補助var2件と正規story var4071だけ')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not ((fa[0x840//8]|fb[0x840//8])&1) and
         va[0x71]==6 and vb[0x71]==7 and va[0x72]==vb[0x72]==1,'全国図鑑未解禁。正規story4071だけ6→7')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6960,1775),'全Save差分会計')
    return dict(party_changes=changes,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,
        legacy_flag_deltas=[],variable_deltas=vd,auxiliary_var_deltas=vd[:2],story_variable_deltas=vd[2:],auxiliary_runtime_owners_resolved=False,old_bank_preserved_bytes=57344,
        pc_preserved=True,story_extension=extension,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,
        national_var404e=0,national_flag840=0,story_vars={'4071':7,'4072':1},badge_count=1,
        all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not (folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes())
    need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and
         measured['native_processes']==2 and measured['screen_count']==22,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed)
        e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][19] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['battle'] is None and measured['teleport'] is None and measured['route']==m.ROUTE,'全南段差/owner経路・戦闘/teleportなし')
    need(measured['story_event']==dict(ledges=[dict(before=[14,8],after=[14,10],observation=6),dict(before=[14,12],after=[14,14],observation=9)],owner_candidate_reached=True,owner=0x08214656,runtime_story_unlock_accepted=False),'測定時は未受入のowner候補。保存byteの独立受入で確定')
    inspection=json.loads((folder/'inspection.json').read_bytes())
    need(inspection==measured['inspection'] and inspection['route']==m.ROUTE and inspection['owner_operands']==dict(first_opcode=105,setflag_opcode=41,flag=4367,setvar_opcode=22,variable=16497,value=7,release_opcode=107,end_opcode=2),'固定ROMの観測owner。staticを解禁扱いしない')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE)
    return result


