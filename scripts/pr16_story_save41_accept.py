#!/usr/bin/env python3
"""Save41の504西段差/橋下・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save41_measure as m
from pr16_story_after_maori import need,identity
SOURCE='8c012df44845e982acef17db79396be6dd03dc14'
RUN,JOB,ARTIFACT=37130788526,111225303265,11277075434
ARCHIVE=dict(size=315975,sha256='ed8e6939b07adb649f61516fedbe5050a250d2f72875ac75014f7ac3781c129d')
OUTPUT=dict(size=131088,sha256='a70b790da5894eac9f67e2a324c68e3513d86330491ef9451ffca06c792f0140')
PARTY=m.a.PARTY
FLASH='06edc61e9e70e9931ae4bd2930fafa707f4d9f1bbea7a6539260136f74f57802'
CP='content/modernization/pr16_story_save41_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE41_JA.md'
EVIDENCE='content/modernization/pr16_story_save41_evidence'
VISUAL='content/modernization/pr16_story_save41_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGERS=['8d9929bc88d9ea0adcd06aff00a88aafbe57a707af12fb94fd4cc065c521f41d','7a0eb126f868227ffd18a5a2c776246c41194f69d437a834570c1964e4a5f117']
LEDGER=LEDGERS[-1]
trace=m.a.trace

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==42 and len(bo)==2,'全44画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(77,3252)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    motion=m.ROUTE[:12]+[[48,10],[48,11]]
    for i,o in enumerate(ao):
        xy=motion[i]if i<14 else[48,11];face=1 if i in(12,13)else 3;field=i<17 or i==41
        need(o['map']==[3,44]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'西段差/橋下/未通過の全座標')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if field else 1)and o['field']is field,'menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGERS[0 if i<5 else 1],'全party不変/戦闘0/ledger推移')
        need(o['save_counter']==(40 if i<36 else 41),'counter41だけ')
        if i<24:need(o['flash_sha256']==m.a.FLASH,'Save前Flash全byte不変')
        elif i<37:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'24〜36は未完の部分write')
        else:need(o['flash_sha256']==FLASH,'37成功文言以降だけ安定Flash')
    need(len({o['flash_sha256']for o in ao[24:37]})==13,'13部分writeを分離')
    for o in bo:
        m.idle(o,41);need(o['xy']==[48,11]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_ROUTE504_WEST_LEDGE_UNDERPASS_SAVE41_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=41,map=[3,44],xy=[48,11],facing=3,party_count=4,rp=0,west_ledge_accepted=True,west_ledge=[[58,10],[56,10]],unpassed_edge=[[48,11],[47,11]],unpassed_edge_attempts=3,bridge_west_edge_passed=False,cave_crossing_complete=True,
        save_success_text_observation=37,save_success_wording_observed=True,stable_full_flash_observation=37,save_counter_changed_observation=36,stable_field_observation=41,partial_write_observations=list(range(24,37)),
        progress_inputs=77,continue_inputs=13,screen_count=44,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,
        hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120 and fa==fb,'全legacy flag不変');return []

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save40/41とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,40,s.LAYOUT);new,rb=s.bank(after,0xe000,41,s.LAYOUT);_,rc=s.bank(after,0,40,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save40bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need(x==y and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==13796,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,63,75),(0x4022,3,0)],'補助var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6866,1695),'全Save差分会計')
    return dict(party_unchanged_bytes=600,pp=[1,5,0,0],hp=[320,354],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==44,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業Save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][41]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['battle']is None and measured['route']==m.ROUTE[:13],'新通常移動だけ・戦闘0')
    need(measured['frontier']==dict(kind='unpassed_edge',before=[48,11],target=[47,11],attempts=3,map=[3,44],xy=[48,11],observation=16),'橋下の西辺3試行を未通過として保持')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+17:04d}.ppm').read_bytes())==i,'menu実cursor0→4の各行')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['ledge']==dict(xy=[57,10],elevation=0,collision=1,behavior=57),'静的候補と実通過範囲を区別')
    need(all(inspection[x]==0 for x in('new_map_views','new_terrain_cells','new_script_nodes')),'保存済地形再採取0')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
