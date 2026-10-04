#!/usr/bin/env python3
"""第8ディグダ配置変更のSave86原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save86_measure as m
from pr16_story_after_maori import need,identity
SOURCE='948cdf5ba094404c8c27e0464a7089aa280730ee'
RUN,JOB,ARTIFACT=37180080594,111370697900,11294997639
ARCHIVE={'size': 144536, 'sha256': 'c6a02d02c46e1ec2e3c5edff5f4a5dd93300809a354a9ceb8b6ccbebba4a9871'}
OUTPUT={'size': 131088, 'sha256': 'd1ea60da2a4b4ea00fa6a6d70fde1c9be74b5c92fd90fc780b47737761041715'}
PARTY='2b8f524dec01ca4a817a9e6a494b3402ed1583ab86c8618bce4d5efb13fe87e2'
FLASH='531851e8e206ce96751f1dae700188840198e14a956f2f2c8f2486a3ee43b5a3'
LEDGER='40086ba99a8d004ff07a5c5e800898c46003af5de36a8f922f8051485e701ad1';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save86_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE86_JA.md'
EVIDENCE='content/modernization/pr16_story_save86_evidence'
VISUAL='content/modernization/pr16_story_save86_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE+[[6,7]]
FLASH_PHASES=['e1a62ed65347d536c0222b42c1327ca1b22ee2bb0d03d91dba3801b364b039f5', '14ec8b944b799d2352f86dacf3c3170614c47a94312a4abe6831e263acb03c5c', '0307a52c53d46d306556c0b0c89a47d860718a58e916d9cf746cb1e792b29bcd', '98b818e8104e7dfa97026b2bb3325acbee036bd222874bf6647af9794d8b8966', 'e4f08daa4aa1bfd16927453ab087787a81513429b8d190a5da8eabe4633ae008', 'bb1cac9c915eca2127749f96c76571b27d0e2b30463b478be099c35b3dc96076', 'de58bc102a5279673521c096a01f15901bcac46ba16a6ac9f19647b64a7be373', '877026723bdd0a102f04f9e8eac140fce43d3e512c0e64cd1f76629c41e3234a', '119df13a58233c7a8cca572de0895ff4da5317fecdc8f998d0319dc56b222afb']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==26 and len(bo)==2,'全28画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(48,2692)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'移動0/旋回0/第8ディグダ48+cold13入力')
    for i,o in enumerate(ao):
        field=i in(0,3,25)
        need(o['map']==[10,16]and o['xy']==[6,7]and o['live_xy']==[13,14]and o['facing']==1,'同じ6,7南の通常Aだけ。方向入力なし')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'1台詞/2配置変更/3field/4menu/25field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'今回全party600byte保持。旧Save85の差分owner解明とは別')
        need(o['ledger_sha256']==m.a.COLD_LEDGER==LEDGER,'今回RAM台帳全保持。過去差分owner解明とは別')
        need(o['save_counter']==(85 if i<21 else 86),'20最終hash/21counterと空白text/22成功文言/25fieldを分離')
        wanted=m.a.FLASH if i<11 else FLASH_PHASES[i-11]if i<20 else FLASH
        need(o['flash_sha256']==wanted,'11〜19部分保存/20最終hashでも保存中/21text空白/22成功表示')
    need(all(v!=FLASH for v in FLASH_PHASES)and ao[20]['flash_sha256']==FLASH and ao[20]['save_counter']==85,'最終hashだけで保存完了としない')
    for o in bo:
        m.idle(o,86);need(o['map']==[10,16]and o['xy']==[6,7]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame後を保存/party/RAM別々に確認')
    return dict(status='PASS_EIGHTH_DIGLETT_EVENT_SAVE86_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=86,map=[10,16],map_name_ja='ミルジム',xy=[6,7],facing=1,party_count=4,rp=0,travel_steps=0,turns=0,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,eighth_diglett_event_accepted=True,second_diglett_previously_accepted=True,third_diglett_previously_accepted=True,fourth_diglett_previously_accepted=True,fifth_diglett_previously_accepted=True,sixth_diglett_previously_accepted=True,seventh_diglett_previously_accepted=True,trainer132_previously_accepted=True,trainer160_previously_accepted=True,eighth_diglett_local_id=10,removed_local_ids=[6,11],restored_local_ids=[5],interacted_local10_remains=True,all_changed_objects_visible=False,object_changes_bound_to_flags_and_source=True,gym_puzzle_completed=False,gym_leader_defeated=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[287,294],lead_pp=[4,10,12,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=True,ram_ledger_changed_observations=[],ram_difference_owner_resolved=False,old_save77_cold_difference_owner_resolved=False,old_save78_progress_difference_owner_resolved=False,old_save80_progress_difference_owner_resolved=False,old_save82_progress_difference_owner_resolved=False,old_save83_progress_difference_owner_resolved=False,old_save85_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=21,counter_change_not_save_completion=True,partial_write_observations=list(range(11,20)),stable_hash_not_alone_save_completion=True,save_success_text_observation=22,save_success_wording_observed=True,stable_field_observation=25,progress_inputs=48,continue_inputs=13,screen_count=28,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'physical flags全保持/第8ディグダはexpandedだけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save85/86と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,85,s.LAYOUT);new,rb=s.bank(after,0,86,s.LAYOUT);_,rc=s.bank(after,0xe000,85,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save85全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[4,10,12,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(287,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==20664,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,23,39),(259,164,166)],'S61Eの4373/4377 set・4372 clearだけ')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4373,4377,4378))for f in range(4372,4379)},'local6/11非表示/local5復帰/local10保持/初回flag保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[],'全legacy vars保持。過去aux4021/4022のruntime ownerは未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==0,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and not(fb[2083//8]&(1<<(2083%8))),'badge1/ナギナタbadge未取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7161,1847),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[4,10,12,2],hp=[287,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[[4372,1,0],[4373,0,1],[4377,0,1]],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==28,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][25]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'移動0歩と第8ディグダ、新戦闘0')
    need(measured['frontier']==dict(kind='eighth_diglett_event',trigger=[6,8],map=[10,16],xy=[6,7],observation=3,local_id=10,facing=1),'最初の第8配置変更直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+4:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0025.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='6ede6470f49f890c6b3437a36891a6c192268bb59d63eb93afb12809cda5b4f8','第8配置変更後field/freshContinue全pixel一致')
    need(measured['eighth_diglett_interacted']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常配置変更だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定第8ownerを実入力と照合')
    need(inspection['initial_flags']=={str(f):int(f in(4372,4378))for f in range(4372,4379)}and inspection['expected_flag_changes']==[[4372,1,0],[4373,0,1],[4377,0,1]]and inspection['instruction_count']==43 and inspection['text_count']==2,'第8限定43命令/2台詞')
    need(inspection['expected_object_changes']==[dict(local_id=6,operation='removeobject'),dict(local_id=11,operation='removeobject'),dict(local_id=5,operation='addobject')],'local6/11除去/local5復帰を保存flagと固定ownerで照合。全object画面内とは主張しない')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save86_next_route.json').read_bytes())

