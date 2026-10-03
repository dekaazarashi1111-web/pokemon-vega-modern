#!/usr/bin/env python3
"""Save55のミルシティ通常レンジャー戦・贈与・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save55_measure as m
from pr16_story_after_maori import need,identity
SOURCE='3439daa92e993a3edb89f89d3a37a9bcbdba3e99'
RUN,JOB,ARTIFACT=37151051768,111284855297,11284146293
ARCHIVE=dict(size=639742,sha256='7c57c180c20427639f4dac4b3bd6302090f18a56a3d8416206803c2b16315804')
OUTPUT=dict(size=131088,sha256='f9f9638a49aa4b0f0553c3bfcbaeb736f49d4ae42e5b5ca2509c8aaad9f515a2')
PARTY='297d2affbcb7fd61776e48afb3df6a587beba85c83240c0d52a4210628d82a20'
FLASH='174ffa30735011b0de2428bb0a4a858ac77f6c91a687adc026e0ad0296f0dfda'
CP='content/modernization/pr16_story_save55_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE55_JA.md'
EVIDENCE='content/modernization/pr16_story_save55_evidence'
VISUAL='content/modernization/pr16_story_save55_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='77ccaa1d7ceee4a641d1094ab5b8f5caf44668ea125287542f3e2bed65a80e57'
COLD_LEDGER=LEDGER
trace=m.a.trace

PARTIES=['de9715dca25c84f8e9949c8848fad1d85b883c514f77be14ccaa93d43b824d77', 'f8f005402d47d7f1750852537dacbff869eff9e10dc7b9448e582c3c24421b7e', '3b1bed020006e4ec84984bfea0f1d798da58f5c75b416731aba44c1cefb16b20', 'd236b44995566cf4243d87243f25a51e1587416281a5b5265a6cb619151ce0cc', '5cf32c8028d7736b51e22ac7356c3de1e7aac2c4f1a6972f9e9b9b821b502748', 'cc29e9353f7bb9ed0cfa96e84f207a005fc12ea0af3c4a719f23479c362ea9a7', '7efb83c517cc5394d5f4b631a7c4d1e448edb05d995e076d3bc0eacce76ca3ac', 'e20113d1b94ff519556697e94a94559a4d82a8815bffd7440de30be45a569536', '297d2affbcb7fd61776e48afb3df6a587beba85c83240c0d52a4210628d82a20']
LEDGERS=['3aef553d4f2dba8f52868966ed63e2e315f111535d017321afe1c0df1a7bd384', 'd3da58d409c7bfc1482fe78066a4503f701af9ebbd1b0208666d625da48e7096', 'ddaeb6a1a7e1f563fb6678f94be802dc51ea0278357ef4ec8e451830a1e0910c', '78edb3185bb2da5dba4671b330dadee09c6a82d668c3246963887398df663ebe', '77ccaa1d7ceee4a641d1094ab5b8f5caf44668ea125287542f3e2bed65a80e57']
PARTY_DELTA=[(55,20,14),(86,38,32),(141,8,9),(241,106,107),(341,59,60)]
ROUTE=m.ROUTE+m.TOWN_ROUTE+[[16,20]]
def motion():
    points=[([7,4],2),([7,4],1)]+[([7,y],1)for y in range(5,9)]+[([38,16],1),([38,16],3)]
    points += [([x,16],3)for x in range(37,19,-1)]+[([20,16],1)]+[([20,y],1)for y in range(17,21)]+[([20,20],3)]+[([x,20],3)for x in range(19,15,-1)]
    need(len(points)==36,'30歩/4方向転換/出口warpの観測位置');return points

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==137 and len(bo)==2,'全139画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(268,18454)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    points=motion()
    for i,o in enumerate(ao):
        xy,face=points[i]if i<36 else([16,20],3 if i<112 else 1);field=i<36 or i in(112,136);where=[6,5]if i<6 else[3,2];cb=m.m.BATTLE if 46<=i<=96 else m.m.FIELD
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'通常室内出口/必須NPCまでの全位置と向き')
        need(o['callback2']==cb and o['lock']==int(not field)and o['field']is field,'会話/戦闘/menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(0 if i<46 else 12)and o['battle_outcome']==int(i>=94),'新trainer1勝/RP0/party4')
        phase=sum(i>=j for j in(17,54,62,69,70,77,85,92));need(o['party_sha256']==PARTIES[phase],'全party9phase。PPとHP/歩行byteを分離')
        phase=sum(i>=j for j in(41,63,83,103));need(o['ledger_sha256']==LEDGERS[phase],'RAM台帳4差分、owner未解明')
        need(o['save_counter']==(54 if i<131 else 55),'131counterは部分write。132安定でも保存中、133成功')
        if i<120:need(o['flash_sha256']==m.a.FLASH,'通常保存前Flash不変')
        elif i<132:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'120〜131部分write')
        else:need(o['flash_sha256']==FLASH,'132安定Flash/133成功/136field')
    need(len({o['flash_sha256']for o in ao[120:132]})==12,'部分write全12種')
    for o in bo:
        m.idle(o,55);need(o['map']==[3,2]and o['xy']==[16,20]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態。残留勝利非再計上')
    return dict(status='PASS_MIRU_RANGER_GIFT_SAVE55_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=55,map=[3,2],map_name_ja='ミルシティ・こころのやかた前',xy=[16,20],facing=1,party_count=4,rp=0,travel_steps=30,interior_steps=4,town_steps=26,turns=4,exit_warps=1,normal_recovery_repeated=False,lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,14],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],pp_recovery_accepted=True,normal_recovery_required=False,haxorus_move_ui_native_accepted=True,haxorus_observed_move_ui_slots=[0,2,3],haxorus_all_four_slots_native_accepted=False,repaired_classifier_native_exercised=True,double_target_separation_native_exercised=False,
        trainer_id=331,physical_flag=1611,reward_money=864,opponent_count=6,observed_move_uses=[0,0,0,6],move_commands=6,target_confirmations=0,move_commands_not_automatically_pp_uses=True,exp_share_obtained=True,exp_share_item_id=182,exp_share_quantity_change=[0,1],exp_share_equipped_or_growth_accepted=False,ranger_departure_flag4381=True,statue_backside_hint_observed=True,heart_mansion_entered=False,
        save_success_text_observation=133,save_success_wording_observed=True,stable_full_flash_observation=132,stable_hash_not_save_completion=True,save_counter_changed_observation=131,counter_change_not_save_completion=True,stable_field_observation=136,partial_write_observations=list(range(120,132)),party_changed_observations=[17,54,62,69,70,77,85,92],party_unchanged=False,party_byte41_runtime_owner_resolved=False,ram_ledger_changed_observations=[41,63,83,103],ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        progress_inputs=268,continue_inputs=13,screen_count=139,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=COLD_LEDGER)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600bytes')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==PARTY_DELTA,'PP6減/HP6減/offset41三件のみ')
    versions=[bytes(x)];v=bytearray(x)
    for i in(141,241,341):v[i]+=1
    versions.append(bytes(v))
    for changes in[[(55,19)],[(55,18)],[(86,37)],[(55,17)],[(55,16),(86,32)],[(55,15)],[(55,14)]]:
        for i,value in changes:v[i]=value
        versions.append(bytes(v))
    need([identity(v)['sha256']for v in versions]==PARTIES,'通常保存byteから全9party phaseを独立再構成。実saveへ書かない');return d

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120,'全legacy flags')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(fa,fb))for j in range(8)if(u^v)&(1<<j)];need(d==[(1611,0,1)],'trainer331通常勝利flagだけ');return d

def bag_delta(x,y):
    need(type(x)is dict and type(y)is dict and set(x)==set(y)=={'items','key_items','balls','machines','berries'},'全5pocket')
    for name in x:
        need(len(x[name])==len(y[name]),'pocket全枠')
        need(y[name]==([(182,1)]+x[name][1:]if name=='items'else x[name]),'items先頭へ通常報酬1個だけ')
    need(x['items'][0]==(0,0),'空slot0へ通常取得');return [(182,0,1)]

def extension_delta(x,y):
    a,b=parent.s61e_record(x),parent.s61e_record(y)
    d=[(i,u,v)for i,(u,v)in enumerate(zip(a,b))if u!=v];need(d==[(259,0,32)],'expanded4381の1bitだけ。CRCも独立検証')
    need(2304+259*8+5==4381,'owner setflag4381との物理対応');return d

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save54/55と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,54,s.LAYOUT);new,rb=s.bank(after,0xe000,55,s.LAYOUT);_,rc=s.bank(after,0,54,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save54全bank57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'party新旧hash')
    need(list(y[52:56])==[15,10,15,14]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PPを別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);bd=bag_delta(ia,ib);need((ma,mb)==(17040,17904),'通常864円')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload不変')
    x13=before[old[13]:old[13]+0xff4];y13=after[new[13]:new[13]+0xff4];need(x13[:0x7d0]==y13[:0x7d0]and x13[0xde6:]==y13[0xde6:],'PC末尾/extension後padding不変');ed=extension_delta(x13[0x7d0:0xde6],y13[0x7d0:0xde6]);eb=parent.s61e_record(y13[0x7d0:0xde6])
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb);vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,114,16),(0x4022,1,0),(0x40ac,0,16)],'aux/40ac三件、runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story変数不変')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and va[0x31]==vb[0x31]==0,'badge1/starter0')
    remap=dict(struct.unpack_from('<HH',rom,0x1303ca8+i*4)for i in range(372));need(remap.get(331+0x500,331+0x500)==1611,'同ROMtrainer331→physical1611')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6999,1764),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn不変')
    return dict(party_preserved_bytes=595,party_byte_deltas=pd,party_byte41_runtime_owner_resolved=False,pp=[15,10,15,14],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],bag_item_deltas=bd,all_other_bag_slots_unchanged=True,exp_share_obtained=True,exp_share_equipped=False,hm05_owned=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,ranger_flag4381_owner_resolved=True,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==139,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save同一')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][136]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE,'通常30歩/出口だけ')
    decisions=[dict(observation=i,move_slot=3)if i in(53,61,68,76,84,91)else dict(observation=i,keep_current=True)for i in(53,57,61,65,68,73,76,81,84,88,91)]
    need(measured['battle']==dict(start=46,finish=112,trainer=True,outcome=1,move_commands=[0,0,0,6],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=decisions),'選択6/相手確定0と実PP6を分離')
    need(measured['frontier']==dict(kind='new_battle',trigger=[15,20],map=[3,2],xy=[16,20],observation=112),'最初の新必須戦闘/報酬/会話直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+113:04d}.ppm').read_bytes())==i,'全menu実cursor0→4')
    panels=[];shifts=[]
    for i in range(137):
        kind,slot=m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())
        if kind=='moves':panels.append((i,slot))
        if kind=='shift':shifts.append(i)
    need(panels==[(51,0),(52,2),(53,3),(61,3),(68,3),(76,3),(84,3),(91,3)]and shifts==[57,65,73,81,88],'技panel8/交代拒否5。slot1/ダブルtarget未実証')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['town_route']==m.TOWN_ROUTE and inspection['native_route_accepted']is False,'静的と実到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0 and inspection['starter_var4031']==0 and inspection['expected_trainer']==331,'既読再採取なし/実starterowner')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
