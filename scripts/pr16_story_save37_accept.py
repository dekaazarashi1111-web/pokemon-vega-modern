#!/usr/bin/env python3
"""Save37の西側北辺未通過・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save37_measure as m
from pr16_story_after_maori import need,identity
SOURCE='7e5bc03a76de3b99c4f999c05c9fcf48963b0044'
RUN,JOB,ARTIFACT=37126025449,111211361589,11275371718
ARCHIVE=dict(size=186258,sha256='4e846024bfa840a09459bc5b7c166f4cf170a1844d43f117e6be0c1bc36abc2d')
OUTPUT=dict(size=131088,sha256='7942159bf82220a864a128c66f97aa3da6e2558b0f3e8181d410a925e145a301')
PARTY=m.a.PARTY
FLASH='b755dc1c587cdcbe0d5407a859a05fbe640b9dcb68a695e7267c73133d0fd180'
CP='content/modernization/pr16_story_save37_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE37_JA.md'
EVIDENCE='content/modernization/pr16_story_save37_evidence'
VISUAL='content/modernization/pr16_story_save37_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='f53f58f9f56b69943d14f92b8df3623be493d809276b0860da6d461fa3edc2f4'
trace=m.a.trace
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==31 and len(bo)==2,'全33画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(63,3048)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[6,y]for y in range(13,20)]+[[6,19],[5,19]]+[[6,4]]*22
    for i,o in enumerate(ao):
        field=i<10 or i==30
        need(o['map']==([1,73]if i<9 else [1,38])and o['xy']==xy[i]and o['live_xy']==[v+7 for v in xy[i]]and o['facing']==(1 if i<7 else 3),'洞窟南出口4,19→部屋1/38の通常warp')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if field else 1)and o['field']is field,'通常保存field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER,'戦闘0/party/ledger不変')
        need(o['save_counter']==(36 if i<25 else 37),'counter世代境界')
        if i<13:need(o['flash_sha256']==m.a.FLASH,'通常Save前Flash不変')
        elif i in range(13,24)or i==25:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'部分writeの明示12状態')
        else:need(o['flash_sha256']==FLASH,'24は書込中の一時全byte一致、26以降だけ安定')
    need(len({ao[i]['flash_sha256']for i in list(range(13,24))+[25]})==12,'部分write12状態を区別')
    for o in bo:
        m.idle(o,37);need(o['map']==[1,38]and o['xy']==[6,4]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_CAVE_SOUTH_EXIT_ROOM_SAVE37_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=37,map=[1,38],xy=[6,4],facing=3,party_count=4,rp=0,cave_interior_exit_accepted=True,cave_interior_crossing_complete=True,south_exit_room_reached=True,outside_route503_reached=False,cave_crossing_complete=False,save_success_text_observation=26,save_success_wording_observed=True,transient_final_hash_observation=24,transient_hash_reverted_observation=25,stable_full_flash_observation=26,stable_field_observation=30,partial_write_observations=list(range(13,24))+[25],progress_inputs=63,continue_inputs=13,screen_count=33,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def flags_delta(fa,fb):
    fd=[(i*8+bit,(u>>bit)&1,(v>>bit)&1)for i,(u,v)in enumerate(zip(fa,fb))for bit in range(8)if(u^v)&(1<<bit)]
    need(len(fa)==len(fb)==0x120 and fd==[(2056,0,1)],'出口部屋の補助flag2056だけ・runtime owner未解決')
    return fd

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save36/37とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,36,s.LAYOUT);new,rb=s.bank(after,0xe000,37,s.LAYOUT);_,rc=s.bank(after,0,36,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save36bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need(x==y and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==13576,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);flag=(ext[(4367-2304)//8]>>((4367-2304)%8))&1;need(flag==1,'正規解禁flag4367保持')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,19,26),(0x4022,0,2),(0x404d,20,21)],'補助var3件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==0 and not(fa[0x840//8]&1) and va[0x71]==vb[0x71]==8 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6917,1753),'全Save差分会計')
    return dict(party_unchanged_bytes=600,pp=[1,8,0,0],hp=[320,354],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,auxiliary_flag2056_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,flag4367=flag,old_bank_preserved_bytes=57344,pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':8,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==33,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][30] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==m.ROUTE and measured['battle']is None,'今回戦闘0/出口経路だけ')
    need(measured['frontier']==dict(kind='cave_exit',trigger=[4,19],map=[1,38],xy=[6,4],observation=9),'本区画出口の実到達')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_exit_accepted']is False,'静的候補を本nativeで初受入')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
