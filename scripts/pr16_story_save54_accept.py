#!/usr/bin/env python3
"""Save54の通常受付回復・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save54_measure as m
from pr16_story_after_maori import need,identity
SOURCE='041077371f32b04015916058fe460e1ade4dd989'
RUN,JOB,ARTIFACT=37149491580,111280129663,11283366654
ARCHIVE=dict(size=239323,sha256='6db6c9ef736923cd4c2078aa5b78532d8f12318f35f8c22a816b53ceb5624e6a')
OUTPUT=dict(size=131088,sha256='bfdd4fb964fd8a3b526b919921b2400e3c1f44c02011208b03f0507606a496ad')
PARTY='de9715dca25c84f8e9949c8848fad1d85b883c514f77be14ccaa93d43b824d77'
FLASH='aaafea867467b71890719da352d51792b8b2ddbc7ad70d9d0a85b743b87c8dbe'
CP='content/modernization/pr16_story_save54_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE54_JA.md'
EVIDENCE='content/modernization/pr16_story_save54_evidence'
VISUAL='content/modernization/pr16_story_save54_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='3aef553d4f2dba8f52868966ed63e2e315f111535d017321afe1c0df1a7bd384'
trace=m.a.trace

ROUTE=[[7,8],[7,7],[7,6],[7,5],[7,4]]
COLD_LEDGER=LEDGER
PARTY_DELTA=[(52,11,15),(55,14,20),(152,0,10),(153,0,20),(154,0,15),(155,0,10),(186,50,98),(187,0,1)]
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==37 and len(bo)==2,'全39画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(66,3702)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    for i,o in enumerate(ao):
        xy=ROUTE[i]if i<5 else[7,4];field=i<=4 or i in(10,36)
        need(o['map']==[6,5]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==2,'室内4歩/受付位置だけ')
        need(o['callback2']==m.m.FIELD and o['lock']==int(not field)and o['field']is field,'受付/menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0,'戦闘0/RP0/party4')
        need(o['party_sha256']==(m.a.PARTY if i<8 else PARTY),'会話8でparty回復し以後不変')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<10 else LEDGER),'会話終了でRAM台帳が変化。runtime owner未解明')
        need(o['save_counter']==(53 if i<32 else 54),'counter32は保存途中、完了は33')
        if i<18:need(o['flash_sha256']==m.a.FLASH,'保存前Flash不変')
        elif i<33:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'18〜32は部分write')
        else:need(o['flash_sha256']==FLASH,'33成功/安定、36field')
    need(len({o['flash_sha256']for o in ao[18:33]})==15,'部分write全15種')
    for o in bo:
        m.idle(o,54);need(o['map']==[6,5]and o['xy']==[7,4]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全field/保存/RAM一致')
    return dict(status='PASS_MIRU_NORMAL_HEALING_SAVE54_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=54,map=[6,5],map_name_ja='ミルシティ・ポケモンセンター1F',xy=[7,4],facing=2,party_count=4,rp=0,travel_steps=4,turns=0,healing_site_reached=True,healer_conversation_started=True,normal_recovery_accepted=True,healer_owner_statically_identified=True,lead_species=850,lead_hp=[294,294],lead_pp=[15,10,15,20],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],pp_recovery_accepted=True,normal_recovery_required=False,haxorus_move_ui_native_accepted=True,haxorus_all_four_slots_native_accepted=False,repaired_classifier_native_exercised=False,double_target_separation_native_exercised=False,
        recovery_observation=8,conversation_end_observation=10,save_success_text_observation=33,save_success_wording_observed=True,stable_full_flash_observation=33,save_counter_changed_observation=32,counter_change_not_save_completion=True,stable_field_observation=36,partial_write_observations=list(range(18,33)),party_changed_observations=[8],party_unchanged=False,progress_ram_ledger_unchanged=False,ram_ledger_unchanged=False,cold_ram_ledger_differs=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,town_flag2194_owner_resolved=True,
        progress_inputs=66,continue_inputs=13,screen_count=39,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=COLD_LEDGER)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==PARTY_DELTA,'HP/PP回復の8byteだけ');return d

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120,'全legacy flag')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(fa,fb))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'新legacy flagなし');return d

def move_pp(rom,party):
    table,=struct.unpack_from('<I',rom,0x1cc);need(0x08000000<=table<0x0a000000 and table%4==0,'既存ABIのmove table pointer')
    rows=[]
    for slot in range(4):
        mon=party[100*slot:100*slot+100];need(mon[40]==0 and mon[80:84]==bytes(4),'PPbonus0/状態異常なし')
        moves=struct.unpack_from('<4H',mon,44)
        for i,mid in enumerate(moves):
            at=table-0x08000000+12*mid;need(0<=at<=len(rom)-12,'move row範囲');b=rom[at:at+12];pp=b[4]if mid else 0
            need(mon[52+i]==pp,'全実技PPが現候補tableの上限と一致');rows.append(dict(slot=slot,move_slot=i,move_id=mid,base_pp=pp,row_address=table+12*mid,row=identity(b)if mid else None))
        hp,maxhp=struct.unpack_from('<HH',mon,86);need(hp==maxhp and hp>0,'全員HP満タン')
    return rows

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save53/54とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,53,s.LAYOUT);new,rb=s.bank(after,0,54,s.LAYOUT);_,rc=s.bank(after,0xe000,53,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save53bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'party新旧hash');pp=move_pp(rom,y)
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==17040,'全Bag/HM05/所持金不変')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,110,114),(0x4022,2,1)],'室内通常移動var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story不変')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6936,1739),'全Save差分会計')
    need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn不変')
    return dict(last_heal_location=[3,2,255,0,38,0,16,0],party_preserved_bytes=592,party_byte_deltas=pd,party_change_owner_resolved=True,full_hp_pp_rows=pp,pp=[15,10,15,20],hp=[294,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],pp_recovery_accepted=True,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==39,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][36]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'通常室内4歩、戦闘なし')
    need(measured['frontier']==dict(kind='healer_conversation',map=[6,5],xy=[7,4],start_observation=5,observation=10,party_changed=True),'実受付の回復会話終了')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+11:04d}.ppm').read_bytes())==i,'通常menu実cursor0→4')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==ROUTE and inspection['native_route_accepted']is False,'静的を実通過と分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'静的原本再利用')
    need(inspection['healer_owner']==dict(local_id=3,xy=[7,2],script=135790449,shared_menu=135872070,heal_script=135872156,heal_special=0,special_instruction=135872182),'受付ownerのheal special0')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
