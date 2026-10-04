#!/usr/bin/env python3
"""紙保持の新南9歩/館退出のSave75原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save75_measure as m
from pr16_story_after_maori import need,identity
SOURCE='0845c4282b2ad508dd7046b6d61d6cf139a59fd7'
RUN,JOB,ARTIFACT=37169799589,111340233315,11290759615
ARCHIVE=dict(size=159269,sha256='23c4f5700fb21060afedd06cba7a91987df309b209f34da5256f1b0f2ee67e96')
OUTPUT={'size': 131088, 'sha256': '6554c5f872f710b4dbef5a2db06fbf3d2b91ab3a2984008be53c7ce1ecf4ffb2'}
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='881a9df37f38b87ca54be0d25d1b323af815a2209a53110e3be18643f5da6b59'
LEDGER='6270e89696f6f9772615bafcb7f2c84ad3d0d37b78444c099e04d139a4e244b0';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save75_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE75_JA.md'
EVIDENCE='content/modernization/pr16_story_save75_evidence'
VISUAL='content/modernization/pr16_story_save75_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[20, 24], [20, 25], [20, 26], [20, 27], [20, 28], [20, 29], [20, 30], [20, 31], [20, 32], [20, 33]]
MOTION=[([1, 59], [20, 24], 1), ([1, 59], [20, 25], 1), ([1, 59], [20, 26], 1), ([1, 59], [20, 27], 1), ([1, 59], [20, 28], 1), ([1, 59], [20, 29], 1), ([1, 59], [20, 30], 1), ([1, 59], [20, 31], 1), ([1, 59], [20, 32], 1), ([1, 59], [20, 33], 1), ([3, 2], [15, 20], 1)]
FLASH_PHASES=['3032112a546c9ba643b95307779923d5ecf857f7e1bccc7d742c39212eb3af4a', '800c39b6cdc6ea99adef092532856f4ddc2859de1e79019df6820f9b83b7686d', 'f5b4e531a2f3b5ca3c11010bede46ef173897e329349325e86cc392e7592829e', '1a89ba417e5d9fc33eaef9cb0f1e69690f44a03e072dac37d32d04a65f8f811d', 'f552df3804d60e15db097e5bf95515f267997bfb7ae52cc76f9f61411d3b53e8', '10441892dd1f8c0609cccadc2e320c527cea49e2ffcf38e9098de62089288d4b', '7199366d30b366871b2943bd35c97179de6a729addb27507533f511b93ebba44', '6dbc24a4a2a4407af7a0be89253c52727454f07db5e2c7678d96c7b5145417b9', 'ecce2533ca13c030ec85b2e26965a3372603535d16892c343d6a61c112980af7', '8bff29415f2905dee8dff8e2f7401d3b057a4e3983fc3a960589689770df12f7', '8bff29415f2905dee8dff8e2f7401d3b057a4e3983fc3a960589689770df12f7']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==34 and len(bo)==2,'全36画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(63,2988)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新南9歩/退出63+cold13入力')
    for i,o in enumerate(ao):
        where,xy,face=MOTION[min(i,10)]
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'20,24から南9歩/出口追加入力/町15,20自動南1歩')
        field=i<=10 or i==33
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'9出口・10到着・11menu・33安定field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte/HP/PP保持')
        need(o['ledger_sha256']==(m.a.LEDGER if i<7 else LEDGER),'観測7/20,31のRAM台帳変化。owner未解明')
        need(o['save_counter']==(74 if i<29 else 75),'29counter/最終Flashでもまだ成功文言前')
        wanted=m.a.FLASH if i<18 else FLASH_PHASES[i-18]if i<29 else FLASH
        need(o['flash_sha256']==wanted,'27〜28の部分hash安定と29最終hashを区別')
    need(len(set(FLASH_PHASES))==10 and FLASH_PHASES[-2]==FLASH_PHASES[-1]!=FLASH,'2観測hash安定だけで保存完了にしない')
    for o in bo:
        m.idle(o,75);need(o['map']==[3,2]and o['xy']==[15,20]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_EXIT_SAVE75_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=75,map=[3,2],map_name_ja='ミルシティ',xy=[15,20],facing=1,party_count=4,rp=0,travel_steps=9,turns=0,entry_warps=1,heart_mansion_entered=True,statue_paper_observed=True,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,hole_descent_previously_accepted=True,mansion_exit_observed=True,exit_warp_input_count=1,automatic_town_south_step_observed=True,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,darkness_observed=True,darkness_cleared_on_exit=True,hm05_taught_or_used=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,dialogue_observations=[],exit_observation=10,
        lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[7],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=29,counter_change_not_save_completion=True,partial_write_observations=list(range(18,29)),transient_final_hash_observation=None,stable_partial_hash_observations=[27,28],final_flash_before_success_observation=29,stable_hash_not_alone_save_completion=True,save_success_text_observation=30,save_success_wording_observed=True,stable_field_observation=33,progress_inputs=63,continue_inputs=13,screen_count=36,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=False,cold_player_building_crop_identical=True,field_animation_and_npc_pixels_differ=True)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,1,0)],'通常退出でphysical2056解除のみ。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save74/75と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,74,s.LAYOUT);new,rb=s.bank(after,0xe000,75,s.LAYOUT);_,rc=s.bank(after,0,74,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save74全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);need((eb[259]>>7)&1==1,'expanded4383保持');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,62,71),(0x4022,4,3),(0x40ac,16,0)],'aux2変数と40acだけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==16 and vb[0xac]==0,'全国図鑑/story保持と40ac解除')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7003,1728),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381,4383]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=16,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==36,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][33]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['battle']is None,'新南9歩と館退出、新戦闘0')
    need(measured['frontier']==dict(kind='new_mansion_exit',map=[3,2],xy=[15,20],facing=1,observation=10),'最初の町到着後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+11:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0033.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==3,'町では動くNPC/水面に画面差。全pixel一致としない')
    need(all(m.m.digest(raw,[64,0,176,89])=='0134cf5820b5d1c4767f7b060fafa8b633463309d6f23836c8b4084a578fb3eb'for raw in frames),'プレイヤー/館外観112x89 crop全pixel一致')
    need((folder/'progress/screen-0010.ppm').read_bytes()!=frames[0],'到着10は町名bannerあり')
    need(measured['mansion_exit_observed']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常退出だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False,'保存済新南9歩/出口ownerを実入力と照合')
    need(inspection['entry']==m.a.next_route()['exit_warp']and inspection['arrival']==m.a.next_route()['town_warp'],'南出口1→町warp7と自動南1歩')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    # 次の目的地は未同定。保存済graphからitem/flag consumerを限定検索して先に固定する。
    return dict(status='PENDING_POST_LETTER_CONSUMER_INSPECTION_NO_NATIVE_ROUTE',map=[3,2],start=[15,20],facing=1,paper_item=274,paper_quantity=1,paper_flag=4383,mansion_exit_observed=True,arrival_xy_native_accepted=True,native_route_accepted=False,paper_consumed_or_delivered=False,new_rom_reads=0,new_terrain_cells=0,new_map_views=0,route=None,
        next_action_ja='保存済script graph/tableからitem274/flag4383のcheck/remove/clearと後続story4071=9/4072=1の入口を限定照合し、未読consumerだけ同一候補ROMで読む。受取人/町出口を推測せず、正規次イベントのownerと歩行経路を固定してからSave75以降の最初の新境界へ。旧館経路を再走しない。',
        read_paths=['content/modernization/pr16_story_save56_preparation.json','content/modernization/pr16_story_save57_preparation.json'],stop_at_first_new_battle_event_or_exit=True)
