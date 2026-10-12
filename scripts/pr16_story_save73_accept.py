#!/usr/bin/env python3
"""像のだいじなふうしょ取得のSave73原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save73_measure as m
from pr16_story_after_maori import need,identity
SOURCE='b8f41b6a86eb0f818500efcd371865416d47dd64'
RUN,JOB,ARTIFACT=37167891735,111334594492,11290362029
ARCHIVE=dict(size=121392,sha256='4cfa44f350645f267ca6ab9834cdace7299d6761bac35d0aea23d8823ba53313')
OUTPUT={'size': 131088, 'sha256': '1790277ae4ff1fbb3242a3e58578dfbc66aa98b9e274e42d9811ffb438eb22bb'}
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='b3369071368aadb11d67a05ed0b8de193d404fe8367dfd95a0fad2174b8bd243'
LEDGER='f652e630800f0b4c184ca57665b8ef265eac72072c3357a8705e65fb0729fe14';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save73_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE73_JA.md'
EVIDENCE='content/modernization/pr16_story_save73_evidence'
VISUAL='content/modernization/pr16_story_save73_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[16,27]]
FLASH_PHASES=['9111352a6303897bf7148e688e96458cb7f63f4b6dbc723cdd69e087310d0c3f', '49f44a02117f23388491584455dabaee27f8a091791f9c9b5c0d274eadcbf0cf', '7a7f78ec79b1ef64af39864a8ad973e7e394d42a8b8d330e5b7b9c0743fedae2', '725164d00a4d1de21b321bf18854ab2fe29d717c28022da1ebcaf4b3b0d925fe', 'f89fc8bbc1874f82c7d9c5cf2633e3ec62086e9b9a2c99965e5dfa2102955bed', '43cef6311dd62551e5af4540c422c5c17ca8248de8e69b888eb92541ff341ce4', 'e84d876df6c392a370ee66ba70fd9bcb62d501fb7ca62c4ca04a37a1866d26ae', '044fe797a0df2cc00a1c080fedc1b9ae03dea23986bee4fadf4d245b0ad569dd', '36f44b4f40ffe5bc769355dfddf36a0fa570ff45de2f0a48721d4f97223c68c6', '547573473df0058dc4e97d77765470cf6052e47065c4a39323956aeb89be1957', '21568a059d9905ad69295a4ea827dcb98b5765a1ed3539dcf3afa11f07acbf6c', '831dbc17bfdac0a0956c971aec8967efcf8a0cf1c35716b1c4e78b3eaf05de2a', 'b3369071368aadb11d67a05ed0b8de193d404fe8367dfd95a0fad2174b8bd243', 'fb55b7ad53a626cb0ae5f2628028b9975a4a9ef55db0988da24258c958b73cb0']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==30 and len(bo)==2,'全32画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(53,2958)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'像event53/cold13入力だけ')
    for i,o in enumerate(ao):
        need(o['map']==[1,60]and o['xy']==[16,27]and o['live_xy']==[23,34]and o['facing']==(3 if i==0 else 1),'像北隣で南向き1回だけ。歩行なし')
        field=i in(0,1,4,29)
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'像dialog/通常保存/安定fieldを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.LEDGER,'全party600byte/HP/PP/RAM台帳保持')
        need(o['save_counter']==(72 if i<25 else 73),'25counterは保存中、26成功')
        wanted=m.a.FLASH if i<12 else FLASH_PHASES[i-12]if i<26 else FLASH
        need(o['flash_sha256']==wanted,'部分writeと成功文言を区別。24一致後25再変化')
    need(len(set(FLASH_PHASES))==14 and FLASH_PHASES[12]==FLASH and FLASH_PHASES[13]!=FLASH,'24の一時的hash一致/25counter73でも保存中')
    for o in bo:
        m.idle(o,73);need(o['map']==[1,60]and o['xy']==[16,27]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_STATUE_LETTER_SAVE73_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=73,map=[1,60],map_name_ja='こころのやかた・上階',xy=[16,27],facing=1,party_count=4,rp=0,travel_steps=0,turns=1,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=True,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,dialogue_observations=[2,3],event_complete_observation=4,
        lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=True,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=25,counter_change_not_save_completion=True,partial_write_observations=list(range(12,26)),transient_final_hash_observation=24,stable_hash_not_alone_save_completion=True,save_success_text_observation=26,save_success_wording_observed=True,stable_field_observation=29,progress_inputs=53,continue_inputs=13,screen_count=32,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'全legacy flag保持');return d
def bag_delta(x,y):
    need(type(x)is dict and type(y)is dict and set(x)==set(y)=={'items','key_items','balls','machines','berries'},'全5pocket')
    changes=[]
    for name in x:
        need(len(x[name])==len(y[name]),'全pocket枠')
        changes += [(name,i,u,v)for i,(u,v)in enumerate(zip(x[name],y[name]))if u!=v]
    need(changes==[('key_items',4,(0,0),(274,1))],'大切なもの空slot4へ274一個だけ。他枠保持')
    need(sum(q for item,q in x['key_items']if item==274)==0 and sum(q for item,q in y['key_items']if item==274)==1,'未所持→一個、重複なし');return changes

def extension_delta(x,y):
    a,b=parent.s61e_record(x),parent.s61e_record(y)
    d=[(i,u,v)for i,(u,v)in enumerate(zip(a,b))if u!=v];need(d==[(259,32,160)],'expanded4383のみ、CRC/反転値も確認')
    need(2304+259*8+7==4383,'像setflag4383の保存bit対応');return d

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save72/73と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,72,s.LAYOUT);new,rb=s.bank(after,0xe000,73,s.LAYOUT);_,rc=s.bank(after,0,72,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save72全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);bd=bag_delta(ia,ib);need(ma==mb==19416,'所持金保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    x13=before[old[13]:old[13]+0xff4];y13=after[new[13]:new[13]+0xff4];need(x13[:0x7d0]==y13[:0x7d0]and x13[0xde6:]==y13[0xde6:],'PC末尾/extension外padding保持');ed=extension_delta(x13[0x7d0:0xde6],y13[0x7d0:0xde6]);eb=parent.s61e_record(y13[0x7d0:0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[],'全legacy変数保持。旧owner未解明を解決した意味ではない')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6849,1672),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=False,bag_item_deltas=bd,all_other_bag_slots_unchanged=True,paper_obtained=True,paper_flag4383_owner_resolved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381,4383]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==32,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][29]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['battle']is None,'像の新eventだけ。新戦闘/歩行0')
    need(measured['frontier']==dict(kind='new_statue_event',map=[1,60],xy=[16,27],facing=1,dialogue_observations=[2,3],observation=4),'像dialog二枚→解錠直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+5:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0001.ppm','progress/screen-0004.ppm','progress/screen-0029.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(all(v==frames[0]for v in frames),'像/主人公/暗所field全5画面byte一致')
    need(measured['paper_side_reached']is True and measured['statue_paper_observed']is False and measured['paper_acceptance_pending']is True and measured['statue_event_completed']is True,'measureのpendingを独立Bag/flag/目視で正式化する')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['start']==[16,27]and inspection['statue']==[16,28]and inspection['dialogue_callstd']==[2,4,9],'保存済像script/no-choiceと実event照合')
    need(inspection['planned']==m.a.next_route()and inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし/同じowner')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    upper=json.loads((ROOT/m.PREP).read_bytes());lower=json.loads((ROOT/'content/modernization/pr16_story_save56_preparation.json').read_bytes())
    route=[[16,27],[17,27],[17,26],[17,25],[18,25],[18,24],[18,23],[19,23],[20,23],[20,24]]
    cells={tuple(c['xy']):c for c in upper['terrain']}
    for xy in route:
        c=cells[tuple(xy)];need((c['collision'],c['elevation'],c['behavior'])==(0,3,102 if xy==[20,24]else 8),'新しい復路9歩と終端holeだけ')
    warp=upper['interior']['warps'][5];landing=lower['interior']['warps'][8]
    need(warp==dict(id=5,xy=[20,24],elevation=0,target_warp=8,target_map=[1,59])and landing==dict(id=8,xy=[20,24],elevation=3,target_warp=5,target_map=[1,60]),'上階hole102→下階warp8着地点。下階からの旧不発warpとは別')
    return dict(status='STATIC_POST_LETTER_HOLE_DESCENT_ONLY_NOT_NATIVE_ACCEPTED',map=[1,60],start=[16,27],facing=1,route=route,edges=9,target=[20,24],upper_hole=warp,lower_landing=landing,lower_map=[1,59],expected_landing=[20,24],terrain=[cells[tuple(xy)]for xy in route],paper_item=274,paper_quantity=1,paper_flag=4383,new_terrain_cells=0,new_map_views=0,new_rom_reads=0,native_route_accepted=False,hole_descent_observed=False,old_inert_warp8_repeated=False,stop_at_first_new_battle_event_or_descent=True)
