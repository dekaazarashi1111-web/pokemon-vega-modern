#!/usr/bin/env python3
"""紙取得後の復路9歩/通常下降のSave74原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save74_measure as m
from pr16_story_after_maori import need,identity
SOURCE='cd43872bf7177dd63cc1b9f3ff0a74d4b7b0a1ef'
RUN,JOB,ARTIFACT=37168945312,111337754901,11290343975
ARCHIVE=dict(size=136744,sha256='e4396b58ff042623896289fe25714a8dfde3129e9fac5a64c5931b58a4439fb7')
OUTPUT={'size': 131088, 'sha256': '34a689de13a412f4d81f396aef0ec90291050ff3334fec2b048b203f3a8bd76b'}
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='cb4901630f681830cc94894c05c23a02c951647f8208b7932b6fa16b2c47831b'
LEDGER='f652e630800f0b4c184ca57665b8ef265eac72072c3357a8705e65fb0729fe14';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save74_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE74_JA.md'
EVIDENCE='content/modernization/pr16_story_save74_evidence'
VISUAL='content/modernization/pr16_story_save74_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[16, 27], [17, 27], [17, 26], [17, 25], [18, 25], [18, 24], [18, 23], [19, 23], [20, 23], [20, 24]]
MOTION=[([1, 60], [16, 27], 1), ([1, 60], [16, 27], 4), ([1, 60], [17, 27], 4), ([1, 60], [17, 27], 2), ([1, 60], [17, 26], 2), ([1, 60], [17, 25], 2), ([1, 60], [17, 25], 4), ([1, 60], [18, 25], 4), ([1, 60], [18, 25], 2), ([1, 60], [18, 24], 2), ([1, 60], [18, 23], 2), ([1, 60], [18, 23], 4), ([1, 60], [19, 23], 4), ([1, 60], [20, 23], 4), ([1, 60], [20, 23], 1), ([1, 60], [20, 24], 1), ([1, 59], [20, 24], 1)]
FLASH_PHASES=['09463f6714b0845deba6178637e4dc12a5f9532240e53218d6c8ca240fce90b0', 'd97bb42d78f98b05b646e5949345378a235731f10e1d22e270657557d2016dd1', '0e8511cb75d13bbe89d076d1b1e35a1066fa9bc1b212e8a37083f6ec9e011970', '708d075427b28c834b88c230f454e73c334b2897c1a8c02cf6faeed057624d79', 'a21a22870ed26348891817ce533afc2e1a758296fcafe15d3d621c3a348cee0d', '476f9053215d41a390a181b8db862e89f7ed25f7987717edf85855fbaa60e2ce', 'a87fe8d088720afd8e72290595c2f1de52d161fa222367b4b43fda323c575c62', '8d33390c5920e15e8ff2c95621b05d3c7f83fb5ea5e26eefd8520e2d510b0b8e', '39ad8eb0df092ef2fec45851ff3e6ffc8e1f0d6a1b4e9e6e72893ccf0f03ab38', '6ea8d673f534a5925dc504c1b3b6d800248479f02fbbefe5654b9eaa03dcae86', '77bdb8a308c046428627dd3f16c808dcb81126339bb56b3bdc6900c80acc8b04', '5ca557aa4a0aa1220538842a12d2e169df8852d7c8c92dc3e57e7e9d449b76e6', 'f74099f004ca289214bef883541a2427f7c60f2ffda81ddfb1f44d705631c23b', 'cb4901630f681830cc94894c05c23a02c951647f8208b7932b6fa16b2c47831b', '48f19730bcee99631ed6487fb4d296026a9b3c37250b13fd1790eb0fcc1b5179']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==44 and len(bo)==2,'全46画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(78,3436)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新9歩/6turn/落下78+cold13入力')
    for i,o in enumerate(ao):
        where,xy,face=MOTION[min(i,16)]
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'紙像から初復路9歩/転換6/穴20,24→入口階20,24')
        field=i<15 or i in(16,43)
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'落下15/到着16/保存/安定field43')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.LEDGER,'全party600byte/HP/PP/RAM台帳保持')
        need(o['save_counter']==(73 if i<38 else 74),'38counterは保存中、39成功')
        wanted=m.a.FLASH if i<24 else FLASH_PHASES[i-24]if i<39 else FLASH
        need(o['flash_sha256']==wanted,'37最終hash一時一致、38再変化、39成功を区別')
    need(len(set(FLASH_PHASES))==15 and FLASH_PHASES[-2]==FLASH and FLASH_PHASES[-1]!=FLASH,'一時hash一致/新counterのみで完了扱いしない')
    for o in bo:
        m.idle(o,74);need(o['map']==[1,59]and o['xy']==[20,24]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_POST_LETTER_DESCENT_SAVE74_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=74,map=[1,59],map_name_ja='こころのやかた・入口階',xy=[20,24],facing=1,party_count=4,rp=0,travel_steps=9,turns=6,entry_warps=1,heart_mansion_entered=True,statue_paper_observed=True,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=True,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,dialogue_observations=[],descent_observation=16,
        lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=True,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=38,counter_change_not_save_completion=True,partial_write_observations=list(range(24,39)),transient_final_hash_observation=37,stable_hash_not_alone_save_completion=True,save_success_text_observation=39,save_success_wording_observed=True,stable_field_observation=43,progress_inputs=78,continue_inputs=13,screen_count=46,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,0,1)],'通常下階接続でphysical2056のみ。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save73/74と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,73,s.LAYOUT);new,rb=s.bank(after,0,74,s.LAYOUT);_,rc=s.bank(after,0xe000,73,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save73全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);need((eb[259]>>7)&1==1,'expanded4383保持');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,54,62),(0x4022,1,4)],'aux2変数だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6905,1698),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381,4383]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==46,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][43]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['battle']is None,'紙取得後の復路9歩と通常下降、新戦闘0')
    need(measured['frontier']==dict(kind='new_hole_descent',map=[1,59],xy=[20,24],observation=16),'最初の通常下降直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+17:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0043.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(all(x==frames[0]for x in frames),'下階最終field/cold全pixel一致')
    need((folder/'progress/screen-0016.ppm').read_bytes()!=frames[0],'到着16はmap名bannerあり')
    need(measured['hole_descent_observed']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙を保持した通常下降だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False,'保存済新9歩/穴ownerを実入力と照合')
    need(inspection['entry']==m.a.next_route()['upper_hole']and inspection['arrival']==m.a.next_route()['lower_landing'],'穴5→着地8。旧下階不発の逆接続とは別')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    lower=json.loads((ROOT/'content/modernization/pr16_story_save56_preparation.json').read_bytes());route=[[20,y]for y in range(24,34)]
    cells={tuple(c['xy']):c for c in lower['terrain']}
    for xy in route:
        c=cells[tuple(xy)];need((c['collision'],c['elevation'],c['behavior'])==(0,3,101 if xy==[20,33]else 8),'入口階中央廊下9歩/終端南出口だけ')
    exit_warp=lower['interior']['warps'][1];town=lower['town']['warps'][7]
    need(exit_warp==dict(id=1,xy=[20,33],elevation=3,target_warp=7,target_map=[3,2])and town==dict(id=7,xy=[15,19],elevation=0,target_warp=1,target_map=[1,59]),'保存済南出口/ミルシティwarp7。door自動1歩は未実測')
    return dict(status='STATIC_POST_LETTER_MANSION_EXIT_ONLY_NOT_NATIVE_ACCEPTED',map=[1,59],start=[20,24],facing=1,route=route,edges=9,target=[20,33],exit_warp=exit_warp,town_warp=town,destination_map=[3,2],town_warp_xy=[15,19],possible_auto_step_xy=[15,20],arrival_xy_native_accepted=False,terrain=[cells[tuple(xy)]for xy in route],paper_item=274,paper_quantity=1,paper_flag=4383,new_terrain_cells=0,new_map_views=0,new_rom_reads=0,native_route_accepted=False,mansion_exit_observed=False,stop_at_first_new_battle_event_or_exit=True)
