#!/usr/bin/env python3
"""Save46の504下段西通路・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save46_measure as m
from pr16_story_after_maori import need,identity
SOURCE='78a91fbec8fa40863524b49e501ed204558a5031'
RUN,JOB,ARTIFACT=37137181984,111243980063,11278684880
ARCHIVE=dict(size=453767,sha256='f5fe71c1e324674f8adc69d94c39d8462da87dce46db41106074d0e64e1eddb1')
OUTPUT=dict(size=131088,sha256='d4a2e1f06ecbb1dee1bd54bda6962c1993b51711a09607954fe7b67d1c568e47')
PARTY='7ab38bcb049fbbb3cef9b67c0939a31a446b06157271da9d74bf899b471c034a'
FLASH='7065023f11ebeb0848e69593d0a9ce93e96d5bfdb49d8cb3211446b2b6d752a8'
CP='content/modernization/pr16_story_save46_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE46_JA.md'
EVIDENCE='content/modernization/pr16_story_save46_evidence'
VISUAL='content/modernization/pr16_story_save46_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='d522ec8b2bf900af66d25b3c57b30c06498b37b8db79a057f83384303bc66cac'
trace=m.a.trace

def motion():
    route=[(m.ROUTE[0],1)];face=1
    faces={16:4,32:3,64:2,128:1}
    for before,after in zip(m.ROUTE,m.ROUTE[1:]):
        next_face=faces[m.direction(before,after)]
        if next_face!=face:route.append((before,next_face))
        route.append((after,next_face));face=next_face
    return route

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==58 and len(bo)==2,'全60画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(109,4148)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    points=motion();need(len(points)==33,'27移動と5方向転換')
    for i,o in enumerate(ao):
        xy,face=points[i]if i<33 else([3,12],3);field=i<33 or i==57
        need(o['map']==[3,44]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'下段西通路の全座標')
        need(o['callback2']==m.m.FIELD and o['lock']==int(not field)and o['field']is field,'menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0,'戦闘0/RP0/party4')
        need(o['party_sha256']==(m.a.PARTY if i<7 else PARTY),'歩行5歩目のparty2byte差を区別')
        need(o['ledger_sha256']==(m.a.LEDGER if i<13 else LEDGER),'途中RAM ledger差を保持・owner未解決')
        need(o['save_counter']==(45 if i<53 else 46),'53counter46/54成功文言')
        if i<40:need(o['flash_sha256']==m.a.FLASH,'Save前Flash全byte不変')
        elif i<53:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'40〜52部分write')
        else:need(o['flash_sha256']==FLASH,'53安定Flash・54成功文言')
    need(len({ao[i]['flash_sha256']for i in range(40,53)})==12 and ao[51]['flash_sha256']==ao[52]['flash_sha256'],'12種類/13観測の部分writeを分離')
    for o in bo:
        m.idle(o,46);need(o['xy']==[3,12]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_ROUTE504_LOWER_WEST_SAVE46_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=46,map=[3,44],xy=[3,12],facing=3,party_count=4,rp=0,travel_steps=27,turns=5,lower_west_crossing_accepted=True,final_elevation=3,cave_crossing_complete=True,lead_species=850,lead_hp=[294,294],lead_pp=[15,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],pp_recovery_accepted=False,normal_recovery_required=True,healing_site_reached=False,haxorus_move_ui_native_accepted=False,
        save_success_text_observation=54,save_success_wording_observed=True,stable_full_flash_observation=53,stable_hash_not_save_completion=True,save_counter_changed_observation=53,stable_field_observation=57,partial_write_observations=list(range(40,53)),party_changed_observation=7,party_change_owner_resolved=False,ram_ledger_changed_observation=13,ram_ledger_change_owner_resolved=False,
        progress_inputs=109,continue_inputs=13,screen_count=60,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'party全600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v]
    need(d==[(141,7,8),(241,105,106)],'通常歩行で観測された2byteだけ・owner未解決')
    return d

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120 and fa==fb,'全legacy flag不変');return []

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save45/46とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,45,s.LAYOUT);new,rb=s.bank(after,0,46,s.LAYOUT);_,rc=s.bank(after,0xe000,45,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save45bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'party新旧hash');need(list(y[52:56])==[15,10,15,20] and list(y[152:156])==[0,0,0,0] and struct.unpack_from('<HH',y,86)==(294,294) and struct.unpack_from('<HH',y,186)==(314,354),'先頭/ミュウツーHP/PP不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==14264,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,123,22),(0x4022,4,1)],'補助var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6892,1708),'全Save差分会計')
    return dict(party_unchanged_bytes=598,party_byte_deltas=pd,party_change_owner_resolved=False,pp=[15,10,15,20],hp=[294,294],mewtwo_pp=[0,0,0,0],mewtwo_hp=[314,354],pp_recovery_accepted=False,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==60,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業Save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][57]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['battle']is None and measured['route']==m.ROUTE,'新通常移動だけ・戦闘0')
    need(measured['frontier']==dict(kind='finite_route_frontier_no_event',map=[3,44],xy=[3,12],observation=32),'新28vertex/27歩で下段西通路を通常通過')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+33:04d}.ppm').read_bytes())==i,'menu実cursor0→4の各行')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['stairs']==dict(xy=[26,11],elevation=0,collision=0,behavior=42)and inspection['candidate_levels']==[3]*28,'静的候補と実通過範囲を区別')
    need(all(inspection[x]==0 for x in('new_map_views','new_terrain_cells','new_script_nodes')),'保存済地形再採取0')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
