#!/usr/bin/env python3
"""Save27の保存原本を独立照合。native/既受入試験は再実行しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save27_measure as m
from pr16_story_after_maori import need,identity
SOURCE='77b229ce45d6dc8140c8f8f75ad91652492fad85'
RUN,JOB,ARTIFACT=37116043940,111182955509,11271451341
ARCHIVE=dict(size=240649,sha256='e394284e2e9bcfa26cbbd357d44d7ce65ba218c89a00e5aeffdd4a3d86925b64')
OUTPUT=dict(size=131088,sha256='fb3c41c4178a04cee89301c74ecf2a646dc4d5633eefa8086664ca0057d7b1d4')
PARTY='cfb0b8b6fda99569e3cd08f0f8c414473a6691ae0f05889396bcba9073edb851'
FLASH='97dbfb3a2819068995cdd87849d1ef88dfccf23ee90f350e84508b20031e2d70'
CP='content/modernization/pr16_story_save27_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE27_JA.md'
EVIDENCE='content/modernization/pr16_story_save27_evidence'
VISUAL='content/modernization/pr16_story_save27_visual_review.json'
shared=m.a.shared
transport=m.a.transport
parent=m.a.parent

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations']
    need(len(ao)==36 and len(bo)==2,'全38画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(86,4653) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[x,15]for x in range(32,22,-1)]+[[23,15],[23,14],[23,13],[23,13],[22,13],[21,13],[20,13]]+[[19,13]]*19
    for i,o in enumerate(ao):
        facing=2 if 10<=i<=12 else 3
        callback=0x8055e69 if i==17 else m.m.BATTLE if 18<=i<=26 else m.m.FIELD
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==facing and
             o['party_count']==4 and o['rp']==0 and o['party_sha256']==(m.a.PARTY if i<25 else PARTY),'全位置/RP/party')
        need(o['callback2']==callback and o['lock']==(0 if i<17 or i in (27,35) else 1) and o['field'] is (i<17),
             '遭遇遷移/野生戦/保存/解錠。残留field:falseは勝利追加ではない')
        need(o['battle_flags']==(0 if i<18 else 4) and o['battle_outcome']==(0 if i<27 else 1),'野生1勝と残留outcome')
        need(o['save_counter']==(26 if i<34 else 27),'途中writeをSave27完了にしない')
        if i<31:need(o['flash_sha256']==m.a.FLASH,'通常Save前のFlash全byte不変')
        elif i<34:need(o['flash_sha256'] not in (m.a.FLASH,FLASH),'部分write3状態')
        else:need(o['flash_sha256']==FLASH,'Save27全Flash')
    need(len({ao[i]['flash_sha256']for i in (31,32,33)})==3,'別の部分write3状態')
    for o in bo:
        m.m.idle(o,27)
        need(o['xy']==[19,13] and o['facing']==3 and o['field'] is True and o['battle_flags']==o['battle_outcome']==0 and
             o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==ao[-1]['ledger_sha256'],'独立Continue全状態')
    return dict(status='PASS_CAVE_ROCK_STAIRS_WILD_SAVE27_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,
        wild_species_ja='ダンゴロ',wild_level=7,ordinary_saves=1,save_counter=27,map=[1,73],xy=[19,13],facing=3,party_count=4,rp=0,
        encounter_transition=17,battle_start=18,victory_field_return=27,save_success_text_observation=34,stable_field_observation=35,
        partial_write_observations=[31,32,33],progress_inputs=86,continue_inputs=13,screen_count=38,native_processes=2,
        record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,
        hm05_taught_or_used=False,trainer352_accepted=False,trainer353_accepted=False,teleport_accepted=False,cave_crossing_complete=False,
        national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def boundary(before,after,cold,rom):
    s=parent.sectors
    need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save26/27とcold全Save/RTC')
    need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,26,s.LAYOUT);new,rb=s.bank(after,0xe000,27,s.LAYOUT);_,rc=s.bank(after,0,26,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'前Save26 bank全57344byte不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,a,b)for i,(a,b)in enumerate(zip(x,y))if a!=b]
    need(changes==[(54,1,0)] and identity(y)['sha256']==PARTY,'party差分は火炎放射PP1だけ')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new)
    need(bag_a==bag_b and money_a==money_b==12712,'全Bag/HM05/所持金不変')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6])
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new)
    vd=[(0x4000+i,a,b)for i,(a,b)in enumerate(zip(va,vb))if a!=b]
    need(fa==fb and vd==[(0x4021,53,68)],'全trainer/story flags不変、補助var4021だけ')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not ((fa[0x840//8]|fb[0x840//8])&1) and
         va[0x71]==vb[0x71]==6 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6952,1755),'全Save差分会計')
    return dict(party_changes=changes,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,
        physical_flag_deltas=[],auxiliary_var_deltas=vd,auxiliary_runtime_owners_resolved=False,old_bank_preserved_bytes=57344,
        pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,
        national_var404e=0,national_flag840=0,story_vars={'4071':6,'4072':1},badge_count=1,
        all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not (folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes())
    need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and
         measured['native_processes']==2 and measured['screen_count']==38,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed)
        e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][35] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['battle']==dict(start=18,finish=27,trainer=False,outcome=1,used=[0,0,1,0],decisions=[dict(observation=24,move_slot=2)]),
         '実技画面から火炎放射1回')
    need(measured['route']==m.ROUTE[:15] and measured['teleport'] is None,'野生開始は19,13。静的残経路は未到達')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE)
    return result

