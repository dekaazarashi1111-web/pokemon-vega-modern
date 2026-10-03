#!/usr/bin/env python3
"""Save53の505番道路の通常迂回・ダブル戦・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save53_measure as m
from pr16_story_after_maori import need,identity
SOURCE='c7a396747031908a74cc8c9a63698e6c513dced8'
RUN,JOB,ARTIFACT=37148257409,111276541041,11283178064
ARCHIVE=dict(size=300967,sha256='58c4507d868e77fea5f0f1a28d12f15e61a4e8fd1b08db672b07f1a15fea2670')
OUTPUT=dict(size=131088,sha256='e22287b3ef44b53029d855aca7cac243f567af75fce21d557f28294c7f4c9a13')
PARTY='618111bab55403e03b9e9152dcbc9dd23a4c5209b535f02a430bbed890ebdf89'
FLASH='82aea0a10c4aa5a7941bddcc7bb99268b90513416ce8a9a7b6c99cbff4dee919'
CP='content/modernization/pr16_story_save53_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE53_JA.md'
EVIDENCE='content/modernization/pr16_story_save53_evidence'
VISUAL='content/modernization/pr16_story_save53_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='def3a8d727dc95294ed0908fa68914b62022587e25ef55d2fe352a942c1ec502'
trace=m.a.trace

ROUTE=[[28, 0], [29, 0], [30, 0], [31, 0], [32, 0], [32, 1], [32, 2], [32, 3], [32, 4], [32, 5], [32, 6], [32, 7], [32, 8], [32, 9], [32, 10], [32, 11], [32, 12], [32, 13], [32, 14], [32, 15], [32, 16], [33, 16], [34, 16], [35, 16], [36, 16], [37, 16], [38, 16], [7, 8]]
COLD_LEDGER=LEDGER
def motion():
    points=[(ROUTE[0],1)];face=1;faces={16:4,32:3,64:2,128:1}
    for before,after in zip(ROUTE[:-2],ROUTE[1:-1]):
        nf=faces[m.direction(before,after)]
        if nf!=face:points.append((before,nf))
        points.append((after,nf));face=nf
    points.extend([([38,15],2),([7,8],2)]);return points

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==58 and len(bo)==2,'全60画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(108,4248)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    points=motion();need(len(points)==32,'26歩/3方向転換/door/室内')
    for i,o in enumerate(ao):
        xy,face=points[i]if i<32 else([7,8],2);field=i<=29 or i in(31,57);where=[3,2]if i<31 else[6,5]
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'全移動/door/室内位置')
        need(o['callback2']==m.m.FIELD and o['lock']==int(not field)and o['field']is field,'door/menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0,'戦闘0/RP0/party4')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.COLD_LEDGER,'Save52 cold RAMから全party/ledger不変')
        need(o['save_counter']==(52 if i<53 else 53),'53はcounterだけ先に変化、書込中')
        if i<39:need(o['flash_sha256']==m.a.FLASH,'保存前不変')
        elif i<54:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'39〜53は部分write')
        else:need(o['flash_sha256']==FLASH,'54成功/安定、57field')
    need(len({o['flash_sha256']for o in ao[39:54]})==15,'部分write全15種')
    for o in bo:
        m.idle(o,53);need(o['map']==[6,5]and o['xy']==[7,8]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全field/保存/RAM一致')
    return dict(status='PASS_MIRU_HEALING_BUILDING_SAVE53_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=53,map=[6,5],map_name_ja='ミルシティ・ポケモンセンター1F',xy=[7,8],facing=2,party_count=4,rp=0,travel_steps=27,town_steps=26,turns=3,healing_building_entered=True,healing_site_reached=True,healer_conversation_started=False,healer_owner_statically_identified=True,lead_species=850,lead_hp=[294,294],lead_pp=[11,10,15,14],mewtwo_hp=[50,354],mewtwo_pp=[0]*4,pp_recovery_accepted=False,normal_recovery_required=True,haxorus_move_ui_native_accepted=True,haxorus_all_four_slots_native_accepted=False,repaired_classifier_native_exercised=False,double_target_separation_native_exercised=False,
        save_success_text_observation=54,save_success_wording_observed=True,stable_full_flash_observation=54,save_counter_changed_observation=53,counter_change_not_save_completion=True,stable_field_observation=57,partial_write_observations=list(range(39,54)),party_changed_observations=[],party_unchanged=True,progress_ram_ledger_unchanged=True,ram_ledger_unchanged=True,cold_ram_ledger_differs=False,old_save52_cold_difference_owner_resolved=False,town_flag2194_owner_resolved=True,
        progress_inputs=108,continue_inputs=13,screen_count=60,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=COLD_LEDGER)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte不変');return []

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120,'全legacy flag')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(fa,fb))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'新legacy flagなし、Save52の2194は保持');return d

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save51/52とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,52,s.LAYOUT);new,rb=s.bank(after,0xe000,53,s.LAYOUT);_,rc=s.bank(after,0,52,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save52bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'party新旧hash');need(list(y[52:56])==[11,10,15,14] and list(y[152:156])==[0,0,0,0] and struct.unpack_from('<HH',y,86)==(294,294) and struct.unpack_from('<HH',y,186)==(50,354),'全員HP/PP不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==17040,'全Bag/HM05不変と所持金不変')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,84,110),(0x4022,1,2)],'通常移動var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6989,1765),'全Save差分会計')
    need(list(before[old[1]+28:old[1]+36])==[3,1,255,0,16,0,13,0]and list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'setrespawn3の通常入館更新')
    return dict(last_heal_location_before=[3,1,255,0,16,0,13,0],last_heal_location_after=[3,2,255,0,38,0,16,0],respawn_update_accepted=True,party_unchanged_bytes=600,party_byte_deltas=pd,party_change_owner_resolved=True,pp=[11,10,15,14],hp=[294,294],mewtwo_pp=[0,0,0,0],mewtwo_hp=[50,354],pp_recovery_accepted=False,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,town_flag2194_owner_resolved=True,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==60,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][57]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'通常26歩+入館、戦闘なし')
    need(measured['frontier']==dict(kind='new_building',map=[6,5],xy=[7,8],observation=31),'新建物到着後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+32:04d}.ppm').read_bytes())==i,'通常menu実cursor0→4')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==ROUTE[:-1]and len(inspection['route'])==27 and inspection['native_route_accepted']is False,'静的を実通過と分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'静的原本を再利用')
    need(inspection['healer_owner']==dict(local_id=3,xy=[7,2],script=135790449,shared_heal_script=135872156,heal_special=0,special_instruction=135872182),'受付の到達可能なheal special0、会話は未実施')
    need(inspection['town_flag2194_owner']==dict(script=136400616,instruction=136400637,command='setworldmapflag'),'Save52のtown flag owner解決')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
