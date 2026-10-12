#!/usr/bin/env python3
"""第6ディグダ配置変更のSave84原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save84_measure as m
from pr16_story_after_maori import need,identity
SOURCE='ca2b55818b9ebd8b936b912b30c6ae1d2c4cd6b4'
RUN,JOB,ARTIFACT=37178451752,111365910830,11294830074
ARCHIVE={'size': 146258, 'sha256': '0ed33bdf10932f62481ccbc22ce7e976bc08cf83073b6213423c43d2f68d545f'}
OUTPUT={'size': 131088, 'sha256': '882a52243dfb4d0faf4fa7d1e828197cf198b135c07c7698b3cfaaede360b8ac'}
PARTY='28ca40b7dc0c1dae14aa85904af5ecb6eb427a233ed2ae82f24a5392a1294975'
FLASH='6c8a3b2579bc775d8f6926a45b4a8b5d9f6a0036af0fc63fce4882b795f70d4a'
LEDGER='e382ce75f68b45a15b115e180061d194a24c0697fd7824204bd61eea61ecd84d';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save84_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE84_JA.md'
EVIDENCE='content/modernization/pr16_story_save84_evidence'
VISUAL='content/modernization/pr16_story_save84_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE+[[11,3]]
FLASH_PHASES=['5903f199d8452f08df9f6f58935fee1562937164b2b9d81851c9c393274ac704', 'c90de2c52a4586afad7b6d69dc1068e46970abadf20c23c69804e033347ebbcd', '264a39c4be01f7c9d3155145ac7fce9fdb6dcb4b855e73f9ee3ba48d1465bde0', '040178ff5a1b42a526a801c414588035eb122ff19c1f9e6f85b00f1c4902cf4d', '3b47a2b8fb99c65816877a4f7cd98bfca773cc5f96070a7b716f5edf9a1deeaa', '62a08319db1436ee3db2d92a48bf507e1303ffdfd29492d267e4cbb0b0467095', '6177eedb7b011755b5d136c4422bf6e0eb4e083035bef276a4ce047de729be9a', '1358f94e92d397bb80f815766359081f984fb0aa10f855f198a73a474d4bd2e1', '34bac0484a204df0372199ed1d639e92653ee4d2eba2537c9bd7050a7f30d390']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==32 and len(bo)==2,'全34画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(60,2997)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新北4歩/2旋回/第6ディグダ60+cold13入力')
    positions=[[11,7],[11,7],[11,6],[11,5],[11,4],[11,3]]
    for i,o in enumerate(ao):
        xy=positions[i]if i<len(positions)else[11,3];field=i<=6 or i in(9,31);facing=4 if i==0 else 2 if i<=5 else 3
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'新北4歩と北/西2旋回だけ')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'7台詞/8配置変更/9field/10menu/31field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==m.a.COLD_LEDGER==LEDGER,'今回RAM台帳全保持。過去差分owner解明とは別')
        need(o['save_counter']==(83 if i<27 else 84),'26最終hashのみ/27counterと成功/31fieldを分離')
        wanted=m.a.FLASH if i<17 else FLASH_PHASES[i-17]if i<26 else FLASH
        need(o['flash_sha256']==wanted,'17〜25部分保存/26最終hashでも保存中/27成功表示')
    need(all(v!=FLASH for v in FLASH_PHASES)and ao[26]['flash_sha256']==FLASH and ao[26]['save_counter']==83,'最終hashだけで保存完了としない')
    for o in bo:
        m.idle(o,84);need(o['map']==[10,16]and o['xy']==[11,3]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame後を保存/party/RAM別々に確認')
    return dict(status='PASS_SIXTH_DIGLETT_EVENT_SAVE84_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=84,map=[10,16],map_name_ja='ミルジム',xy=[11,3],facing=3,party_count=4,rp=0,travel_steps=4,turns=2,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,sixth_diglett_event_accepted=True,second_diglett_previously_accepted=True,third_diglett_previously_accepted=True,fourth_diglett_previously_accepted=True,fifth_diglett_previously_accepted=True,trainer132_previously_accepted=True,trainer160_previously_accepted=True,sixth_diglett_local_id=11,removed_local_id=8,restored_local_ids=[10],interacted_local11_remains=True,all_changed_objects_visible=False,object_changes_bound_to_flags_and_source=True,gym_puzzle_completed=False,gym_leader_defeated=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[287,294],lead_pp=[4,10,12,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=True,ram_ledger_changed_observations=[],ram_difference_owner_resolved=False,old_save77_cold_difference_owner_resolved=False,old_save78_progress_difference_owner_resolved=False,old_save80_progress_difference_owner_resolved=False,old_save82_progress_difference_owner_resolved=False,old_save83_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=27,counter_change_not_save_completion=True,partial_write_observations=list(range(17,27)),stable_hash_not_alone_save_completion=True,save_success_text_observation=27,save_success_wording_observed=True,stable_field_observation=31,progress_inputs=60,continue_inputs=13,screen_count=34,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'physical flags全保持/第6ディグダはexpandedだけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save83/84と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,83,s.LAYOUT);new,rb=s.bank(after,0,84,s.LAYOUT);_,rc=s.bank(after,0xe000,83,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save83全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[4,10,12,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(287,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==20664,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,7,71),(259,165,164)],'S61Eの4374 set・4376 clearだけ')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4374,4378))for f in range(4372,4379)},'local8非表示/local10復帰/local11保持/初回flag保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,115,119),(0x4022,0,4)],'aux4021/4022だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==0,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and not(fb[2083//8]&(1<<(2083%8))),'badge1/ナギナタbadge未取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7162,1849),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[4,10,12,2],hp=[287,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[[4374,0,1],[4376,1,0]],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==34,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][31]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新北4歩と第6ディグダ、新戦闘0')
    need(measured['frontier']==dict(kind='sixth_diglett_event',trigger=[10,3],map=[10,16],xy=[11,3],observation=9,local_id=11,facing=3),'最初の第6配置変更直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+10:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0031.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='90ffde3da9e78c606a4222cb70cfff4a1cf8897142f98f6c0228267d8a86e0bc','第6配置変更後field/freshContinue全pixel一致')
    need(measured['sixth_diglett_interacted']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常配置変更だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定第6ownerを実入力と照合')
    need(inspection['initial_flags']=={str(f):int(f in(4376,4378))for f in range(4372,4379)}and inspection['expected_flag_changes']==[[4374,0,1],[4376,1,0]]and inspection['instruction_count']==39 and inspection['text_count']==2,'第6限定39命令/2台詞')
    need(inspection['expected_object_changes']==[dict(local_id=8,operation='removeobject'),dict(local_id=10,operation='addobject')],'local8除去/local10復帰を保存flagと固定ownerで照合。全object画面内とは主張しない')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save84_next_route.json').read_bytes())

