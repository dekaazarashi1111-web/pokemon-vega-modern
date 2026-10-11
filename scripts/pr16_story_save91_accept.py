#!/usr/bin/env python3
"""ミルジム退出のSave91原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save91_measure as m
from pr16_story_after_maori import need,identity
SOURCE='50150f7670e8bd7095066d6ff302d3da7bd40b75'
RUN,JOB,ARTIFACT=37185860784,111387490615,11295979806
ARCHIVE={'size': 196440, 'sha256': '29aa44b30e138cdb9706f4023e415913d04eb29cf2ec537ae7ba2de0816152ed'}
OUTPUT={'size': 131088, 'sha256': 'e61573b32ff8f319ee36fe0d4e29981a4d213ea764078bd290bf92fed622278b'}
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='00832ef6c9c07e2bbe5ae6c6982ad7a3bcb678925425e8c686ceff82a4f302b6'
LEDGER='25e14aa8952190dae350858541a406b7ddcb2a9539af79800a82581ac0819b8d';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save91_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE91_JA.md'
EVIDENCE='content/modernization/pr16_story_save91_evidence'
VISUAL='content/modernization/pr16_story_save91_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE
FLASH_PHASES=['37e47d509f2899f71cfb0484b6d9047de1278e09316fcdff0958c698e6b9d9a7', '6ed42bfb9c2e310cfde65f24d9ea76436ee3ee48cef82bac291d8fe06746eac7', 'f8e1cc92b2e8fc6cee4ccf807af8dfd83e2740395ae404193bf609dde821b56d', 'd04523fcbca42f68fb7b4aab5f8bf66b860d06c9bf37d55f9d8345eea6037e35', '7d8ac84b3f31a7081727208defaf2ed8dd8cc9570aa6d152c0bc0903f18bc4c1', 'edbd8a3d498a08585ed13dddc5b08386e33f2e650840c5ebec746c96ae62805e', '2972fbdf36e20b19aafb0431431db2794948fcda6dc12ce7920cd5d04e647f2f', 'f05c9bc6daf705f178f06a2a0bd8c829e2348c9ce85aa2432f2ca0a08ca1fc5b', '46b56b5e4c3d7b41568c120fb4e081b621ea91118237bf0f9cb4eaf6819330b3']
trace=m.a.trace
trace_rows=m.a.trace_rows


POSITIONS=[[9,11],[9,12],[9,13],[9,13],[8,13],[7,13],[6,13],[6,13],[6,14],[6,15],[6,16],[6,17],[6,18]]
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==37 and len(bo)==2,'全39画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(69,3156)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新10歩/旋回2/warp1/69+cold13入力')
    for i,o in enumerate(ao):
        xy=POSITIONS[i]if i<13 else[20,11];where=[10,16]if i<13 else[3,2];field=i<14 or i==36
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy] and o['facing']==(3 if 3<=i<=6 else 1),'10歩/2旋回/退出warp1・町20,11南')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'13初町field→14menu→36field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==m.a.COLD_LEDGER==LEDGER,'今回RAM全保持。過去差分ownerとは別')
        need(o['save_counter']==(90 if i<32 else 91),'30/31最終hashでもcounter90、32counter91空欄、33成功/36field')
        wanted=m.a.FLASH if i<21 else FLASH_PHASES[i-21]if i<30 else FLASH
        need(o['flash_sha256']==wanted,'21〜29部分hash、30/31保存中文字/最終hash、32counter91/空欄、33成功文言')
    need(ao[29]['flash_sha256']!=FLASH and ao[30]['flash_sha256']==FLASH and ao[31]['save_counter']==90 and ao[32]['save_counter']==91 and not ao[32]['field'],'counter/hash単独で完了としない')
    for o in bo:
        m.idle(o,91);need(o['map']==[3,2]and o['xy']==[20,11]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame/全SaveRTC/party/RAM保持')
    return dict(status='PASS_GYM_EXIT_SAVE91_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=91,map=[3,2],map_name_ja='ミルシティ',xy=[20,11],facing=1,party_count=4,rp=0,travel_steps=10,turns=2,warps=1,automatic_exit_step_observed=True,gym_entry_previously_accepted=True,eleventh_diglett_previously_accepted=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,gym_reset_owner_resolved=True,gym_flags4372_to4378_all_clear=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=True,ram_ledger_changed_observations=[],ram_difference_owner_resolved=False,old_save89_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,flag2056_runtime_owner_resolved=False,auxiliary_runtime_owners_resolved=False,save_counter_changed_observation=32,counter_change_not_save_completion=True,partial_write_observations=list(range(21,30)),first_final_flash_observation=30,last_partial_hash_observation=29,save_in_progress_observations=list(range(21,32)),counter_transition_blank_observation=32,stable_hash_not_alone_save_completion=True,save_success_text_observation=33,save_success_wording_observed=True,stable_field_observation=36,progress_inputs=69,continue_inputs=13,screen_count=39,native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=1,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=False,cold_player_and_gym_crop_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,1,0)],'ジム入場でsetされたphysical2056だけclear。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save90/91と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,90,s.LAYOUT);new,rb=s.bank(after,0xe000,91,s.LAYOUT);_,rc=s.bank(after,0,90,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save90全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23164,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,87,7),(259,164,160)],'S61Eの町type3map-scriptの4372/4374/4378 clearだけ')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'町type3map-scriptで4372〜4378全clear')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,39,49),(0x40aa,2049,0),(0x40ac,16,0),(0x40ad,4,0),(0x40ae,15,80)],'退出時5変数差分を全件台帳化。runtime ownerは未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==16 and vb[0xac]==0,'全国図鑑/story保持・40ac16→0')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7185,1833),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[[4372,1,0],[4374,1,0],[4378,1,0]],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=16,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def exit_owner(rom):
    p=json.loads((ROOT/'content/modernization/pr16_story_save91_exit_owner.json').read_bytes())
    for row in [p['header_scripts_pointer'],p['map_script_table'],*p['instructions']]:need(rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'町退出後のmap-script exact byte')
    need(p['header_scripts_pointer']==dict(address=137447176,size=4,hex='34041708') and p['map_script_table']['hex'].startswith('03e84e2108'),'町header→type3→0x08214ee8')
    need([x['hex']for x in p['instructions']]==['2a1411','2a1511','2a1611','2a1711','2a1811','2a1911','2a1a11','d09208','02'],'七つのclearflag/flyflag/endの固定owner')
    return dict(type3_root=p['type3_root'],instruction_count=9,expanded_flag_changes=p['actual_expanded_flag_changes'],runtime_legacy_owners_resolved=False)
def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==39,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][36]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新10歩/旋回2/warp1、新戦闘0')
    need(measured['frontier']==dict(kind='new_gym_exit',trigger=[6,18],map=[3,2],xy=[20,11],facing=1,observation=13),'最初の町到着直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+14:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0036.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==3,'町NPC/花animationのため全pixel一致とはしない')
    need(all(m.m.digest(frame,[80,0,176,96])=='65789efc76537a2196ded499e60113148a4a3eec464b079e75f07f35d0032021'for frame in frames),'固定ジム背景/主人公領域9216pixel保持')
    need(measured['gym_exit_observed']is True and measured['gym_exit_accepted']is False and measured['paper_consumed_or_delivered']is False,'測定原本は受入前・紙保持')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['warp_owner']==planned['warp_owner'],'固定warpを実入力と照合')
    need(inspection['initial_flags']=={str(f):int(f in(4372,4374,4378))for f in range(4372,4379)}and inspection['binding_count']==28,'第11switch後退出地形28範囲')
    canonical=(ROOT/'content/modernization/pr16_story_save90_next_route.json').read_bytes()
    need(planned['parent_route_binding']==identity(canonical)and json.loads(canonical)['route']==m.ROUTE,'親route原本のexact byte identity/意味一致')
    for row in planned['bindings']:need(rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'退出地形/warp全byte')
    failed=json.loads((folder/'failed-attempt.json').read_bytes());need(failed['failure']['native_processes']==0 and failed['native_inputs']==0 and failed['source']=='38c2c0f931d3c8c17e0ded5eb8192501d8857145','初回pre-native失敗を成功へ読み替えない')
    result['preparation_parent_route_binding']=dict(repository_bytes=identity(canonical),measurement_preparation_modified=False,exact_bytes=True)
    result['exit_owner']=exit_owner(rom)
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save91_next_route.json').read_bytes())
