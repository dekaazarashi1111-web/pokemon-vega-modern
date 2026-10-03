#!/usr/bin/env python3
"""Save42の504橋下/階段/橋上・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save42_measure as m
from pr16_story_after_maori import need,identity
SOURCE='0dd57e34888b7d3de23bf5a42153a3f936a5f61d'
RUN,JOB,ARTIFACT=37132139175,111229185172,11277536596
ARCHIVE=dict(size=409650,sha256='04bb37913134e5b62c1bcb7004d4f14bd7c4b0c4591148a2b0f83ec0018ebaef')
OUTPUT=dict(size=131088,sha256='c1959acc33cd7592ff4c3202e5fc5f4397215315127ebe257cd27486997aa144')
PARTY=m.a.PARTY
FLASH='46d3183294fa743d88021058757975ae9e2b9c94fff7a88bee285e758d094faf'
CP='content/modernization/pr16_story_save42_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE42_JA.md'
EVIDENCE='content/modernization/pr16_story_save42_evidence'
VISUAL='content/modernization/pr16_story_save42_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='7a0eb126f868227ffd18a5a2c776246c41194f69d437a834570c1964e4a5f117'
trace=m.a.trace

def motion():
    route=[(m.ROUTE[0],3)];face=3
    faces={16:4,32:3,64:2,128:1}
    for before,after in zip(m.ROUTE,m.ROUTE[1:]):
        next_face=faces[m.direction(before,after)]
        if next_face!=face:route.append((before,next_face))
        route.append((after,next_face));face=next_face
    return route

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==55 and len(bo)==2,'全57画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(103,3980)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    points=motion();need(len(points)==30,'21移動と8方向転換')
    for i,o in enumerate(ao):
        xy,face=points[i]if i<30 else([47,13],3);field=i<30 or i==54
        need(o['map']==[3,44]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'橋下/階段/橋上の全座標')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if field else 1)and o['field']is field,'menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER,'全party/戦闘0/ledger不変')
        need(o['save_counter']==(41 if i<50 else 42),'counter42だけ')
        if i<37:need(o['flash_sha256']==m.a.FLASH,'Save前Flash全byte不変')
        elif i in list(range(37,49))+[50]:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'37〜48/50は部分write')
        else:need(o['flash_sha256']==FLASH,'49は一時一致、51成功文言以降だけ安定Flash')
    need(len({ao[i]['flash_sha256']for i in list(range(37,49))+[50]})==13,'13部分writeを分離')
    for o in bo:
        m.idle(o,42);need(o['xy']==[47,13]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_ROUTE504_UNDERPASS_STAIRS_UPPER_BRIDGE_SAVE42_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=42,map=[3,44],xy=[47,13],facing=3,party_count=4,rp=0,underpass_south_accepted=True,stairs_accepted=True,stairs=[[54,16],[54,15],[54,14]],upper_bridge_west_crossing_accepted=True,upper_bridge=[[49,13],[48,13],[47,13]],earlier_unpassed_edge=[[48,11],[47,11]],earlier_unpassed_edge_retried=False,cave_crossing_complete=True,
        save_success_text_observation=51,save_success_wording_observed=True,transient_final_hash_observation=49,transient_hash_reverted_observation=50,stable_full_flash_observation=51,save_counter_changed_observation=50,stable_field_observation=54,partial_write_observations=list(range(37,49))+[50],
        progress_inputs=103,continue_inputs=13,screen_count=57,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,
        hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120 and fa==fb,'全legacy flag不変');return []

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save41/42とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,41,s.LAYOUT);new,rb=s.bank(after,0,42,s.LAYOUT);_,rc=s.bank(after,0xe000,41,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save41bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need(x==y and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==13796,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,75,96),(0x4022,0,1)],'補助var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6871,1715),'全Save差分会計')
    return dict(party_unchanged_bytes=600,pp=[1,5,0,0],hp=[320,354],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==57,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業Save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][54]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['battle']is None and measured['route']==m.ROUTE,'新通常移動だけ・戦闘0')
    need(measured['frontier']==dict(kind='finite_route_frontier_no_event',map=[3,44],xy=[47,13],observation=29),'新22vertex区間を通常通過・最初の橋下失敗辺は再試行0')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+30:04d}.ppm').read_bytes())==i,'menu実cursor0→4の各行')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['stairs']==dict(xy=[54,15],elevation=0,collision=0,behavior=42)and inspection['candidate_levels']==[3]*12+[0]+[4]*9,'静的候補と実通過範囲を区別')
    need(all(inspection[x]==0 for x in('new_map_views','new_terrain_cells','new_script_nodes')),'保存済地形再採取0')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
