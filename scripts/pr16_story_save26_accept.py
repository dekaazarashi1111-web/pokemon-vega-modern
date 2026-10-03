#!/usr/bin/env python3
"""Save26の保存原本を独立照合。native/既受入試験は再実行しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save26_measure as m
from pr16_story_after_maori import need,identity
SOURCE='3fde7851bff63efd661b0e5b9f6c6b488272fbb5'
RUN,JOB,ARTIFACT=37114774344,111179348370,11270502866
ARCHIVE=dict(size=212283,sha256='c2e3f92164eb2034e7647c46c8a672d1606b3979b4a058037e4549d753e7f1f3')
OUTPUT=dict(size=131088,sha256='e65fc5bb2c76d7cfcdd144c1a69451ad8508ff73ad82e4c7f24595d75200624d')
PARTY='d383efab4e3b8db8a7ae9faff78ae06db279d9e754282298e96b1b85a1d7c53a'
FLASH='8755b4268a772ef7efcc9dacbf96caee28f2580124daf8cf322d72d2c6c5bfe9'
CP='content/modernization/pr16_story_save26_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE26_JA.md'
EVIDENCE='content/modernization/pr16_story_save26_evidence'
VISUAL='content/modernization/pr16_story_save26_visual_review.json'
shared=m.a.m.a.d.m.shared
transport=m.a.m.a.d.m.transport
parent=m.a.m.a.d.m.prior.parent

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations']
    need(len(ao)==35 and len(bo)==2,'全37画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(84,4613) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[31,y]for y in range(7,13)]+[[31,12],[32,12],[33,12],[34,12],[34,12],[34,13],[34,14],[34,15],[34,15],[33,15]]+[[32,15]]*19
    for i,o in enumerate(ao):
        facing=1 if i<6 or 10<=i<14 else 4 if i<10 else 3
        callback=0x8055e69 if i==16 else m.m.BATTLE if 17<=i<=25 else m.m.FIELD
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==facing and
             o['party_count']==4 and o['rp']==0 and o['party_sha256']==(m.a.PARTY if i<24 else PARTY),'全位置/RP/party')
        need(o['callback2']==callback and o['lock']==(0 if i<16 or i in (26,34) else 1) and o['field'] is (i<16),
             '遭遇遷移/野生戦/保存/解錠。残留field:falseは勝利追加ではない')
        need(o['battle_flags']==(0 if i<17 else 4) and o['battle_outcome']==(0 if i<26 else 1),'野生1勝と残留outcome')
        need(o['save_counter']==(25 if i<33 else 26),'途中writeをSave26完了にしない')
        if i<30:need(o['flash_sha256']==m.a.FLASH,'通常Save前のFlash全byte不変')
        elif i<33:need(o['flash_sha256'] not in (m.a.FLASH,FLASH),'部分write3状態')
        else:need(o['flash_sha256']==FLASH,'Save26全Flash')
    need(len({ao[i]['flash_sha256']for i in (30,31,32)})==3,'別の部分write3状態')
    for o in bo:
        m.m.idle(o,26)
        need(o['xy']==[32,15] and o['facing']==3 and o['field'] is True and o['battle_flags']==o['battle_outcome']==0 and
             o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==ao[-1]['ledger_sha256'],'独立Continue全状態')
    return dict(status='PASS_CAVE_SOUTH_WILD_SAVE26_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,
        wild_species_ja='ディグダ',wild_level=6,ordinary_saves=1,save_counter=26,map=[1,73],xy=[32,15],facing=3,party_count=4,rp=0,
        encounter_transition=16,battle_start=17,victory_field_return=26,save_success_text_observation=33,stable_field_observation=34,
        partial_write_observations=[30,31,32],progress_inputs=84,continue_inputs=13,screen_count=37,native_processes=2,
        record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,
        hm05_taught_or_used=False,trainer352_accepted=False,trainer353_accepted=False,teleport_accepted=False,cave_crossing_complete=False,
        national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def boundary(before,after,cold,rom):
    s=parent.sectors
    need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save25/26とcold全Save/RTC')
    need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,25,s.LAYOUT);new,rb=s.bank(after,0,26,s.LAYOUT);_,rc=s.bank(after,0xe000,25,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'前Save25 bank全57344byte不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,a,b)for i,(a,b)in enumerate(zip(x,y))if a!=b]
    need(changes==[(54,2,1)] and identity(y)['sha256']==PARTY,'party差分は火炎放射PP1だけ')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new)
    need(bag_a==bag_b and money_a==money_b==12712,'全Bag/HM05/所持金不変')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6])
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new)
    vd=[(0x4000+i,a,b)for i,(a,b)in enumerate(zip(va,vb))if a!=b]
    need(fa==fb and vd==[(0x4021,40,53)],'全trainer/story flags不変、補助var4021だけ')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not ((fa[0x840//8]|fb[0x840//8])&1) and
         va[0x71]==vb[0x71]==6 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6906,1743),'全Save差分会計')
    return dict(party_changes=changes,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,
        physical_flag_deltas=[],auxiliary_var_deltas=vd,auxiliary_runtime_owners_resolved=False,old_bank_preserved_bytes=57344,
        pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,
        national_var404e=0,national_flag840=0,story_vars={'4071':6,'4072':1},badge_count=1,
        all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not (folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes())
    need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and
         measured['native_processes']==2 and measured['screen_count']==37,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed)
        e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][34] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['battle']==dict(start=17,finish=26,trainer=False,outcome=1,used=[0,0,1,0],decisions=[dict(observation=23,move_slot=2)]),
         '実技画面から火炎放射1回')
    need(measured['route']==m.ROUTE[:13] and measured['teleport'] is None,'野生開始は32,15。静的残経路は未到達')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE)
    return result
