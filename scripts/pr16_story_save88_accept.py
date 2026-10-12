#!/usr/bin/env python3
"""第9ディグダ配置変更のSave88原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save88_measure as m
from pr16_story_after_maori import need,identity
SOURCE='c22d8263667b722e35eaeba739457207e80d6b32'
RUN,JOB,ARTIFACT=37182824895,111378647442,11295552942
ARCHIVE={'size': 200272, 'sha256': '5484c7fb1fb3044f7ac37c5b6f6a5b4f223c8977ccaa0a247a04bcb03e9d6dfe'}
OUTPUT={'size': 131088, 'sha256': 'a99af1391ac7bd9a05cffa8487d868aff2c6e31a48aea2a27c1c2a90ebeb1b0c'}
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='1af6eae7f161a4433be52ad6998e9b8fb4a87c276bf9d5b6c1cb3ef79d02a126'
LEDGER='3a31eca68c049166e0aed0585c4bd44619b108ceea489c5e954f2dc34c916251';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save88_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE88_JA.md'
EVIDENCE='content/modernization/pr16_story_save88_evidence'
VISUAL='content/modernization/pr16_story_save88_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE+[[6,7]]
FLASH_PHASES=['e00df3b300f843268155119fabe8c77834474f33b2fdeedf636efdcadba0960e', '893a920b3ede356ffb4921b35a6b99b01c905a50cfb734d0fdd9a0d3f7e0c9ee', '50dc48e6c278d79d8d082b4aa6313071b2c3451cb6159a5774b7d3928ab2097b', '1be4523f47902239327012d84db871808fd1769236ec3e7a16277242203063e3', '7e211e192cab048f9386aca4c7d0f06211c8f4d9a29b13b0fe9a48c1b215ebf9', 'cbd908c31b4a9164229d8d81622385070236f90b233468c7c61f75a37e03ab39', 'ead41fdb2adaf382360eb368adeb940e28027b0ff1c3d9ce394b55ff4e52f55a', '0cdf41274d2a82535121e498a1ca4b2c9891e4e48fda3e9e792e904911202a51', '2b2be28863217670f5e16ae19509d8477664c5eff406d44bff32876208330827', '1af6eae7f161a4433be52ad6998e9b8fb4a87c276bf9d5b6c1cb3ef79d02a126', 'da288c730ad3dd8da5d3c2ebaf7218e287eb82e0906be9d9858d06cf32bd29f9']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==43 and len(bo)==2,'全45画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(82,3613)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新13歩/4旋回/第9ディグダ82+cold13入力')
    positions=[[7,3],[7,3]]+[[x,3]for x in range(8,12)]+[[11,3]]+[[11,y]for y in range(4,8)]+[[11,7]]+[[x,7]for x in range(10,5,-1)]
    need(len(positions)==17,'東4南4西5と途中3旋回')
    for i,o in enumerate(ao):
        xy=positions[i]if i<17 else[6,7];face=3 if i==0 else 4 if i<6 else 1 if i<11 else 3 if i<17 else 1;field=i<18 or i in(20,42)
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[x+7 for x in xy]and o['facing']==face,'13歩/3旋回と17の南旋回。local10へ踏み込まない')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'18台詞/19配置変更/20field/21menu/42field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持。旧raw41系列差分ownerとは別')
        need(o['ledger_sha256']==m.a.COLD_LEDGER==LEDGER,'今回RAM保持。過去RAM差分ownerとは別')
        need(o['save_counter']==(87 if i<38 else 88),'38counter88でも保存中、39成功/42field')
        wanted=m.a.FLASH if i<28 else FLASH_PHASES[i-28]if i<39 else FLASH
        need(o['flash_sha256']==wanted,'37最終hash、38一時別hash/counter88、39最終hash再確定を区別')
    need(ao[37]['flash_sha256']==FLASH and ao[37]['save_counter']==87 and ao[38]['flash_sha256']!=FLASH and ao[38]['save_counter']==88 and ao[39]['flash_sha256']==FLASH,'counter/hash単独で完了としない')
    for o in bo:
        m.idle(o,88);need(o['map']==[10,16]and o['xy']==[6,7]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame/全SaveRTC/party/RAM保持')
    return dict(status='PASS_NINTH_DIGLETT_EVENT_SAVE88_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=88,map=[10,16],map_name_ja='ミルジム',xy=[6,7],facing=1,party_count=4,rp=0,travel_steps=13,turns=4,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,ninth_diglett_event_accepted=True,second_diglett_previously_accepted=True,third_diglett_previously_accepted=True,fourth_diglett_previously_accepted=True,fifth_diglett_previously_accepted=True,sixth_diglett_previously_accepted=True,seventh_diglett_previously_accepted=True,trainer132_previously_accepted=True,trainer160_previously_accepted=True,ninth_diglett_local_id=10,removed_local_ids=[10],restored_local_ids=[6,11],interacted_local10_remains=False,all_changed_objects_visible=False,object_changes_bound_to_flags_and_source=True,gym_puzzle_completed=True,gym_leader_defeated=True,gym_exit_accepted=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=True,ram_ledger_changed_observations=[],ram_difference_owner_resolved=False,old_save77_cold_difference_owner_resolved=False,old_save78_progress_difference_owner_resolved=False,old_save80_progress_difference_owner_resolved=False,old_save82_progress_difference_owner_resolved=False,old_save83_progress_difference_owner_resolved=False,old_save85_progress_difference_owner_resolved=False,old_save87_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=38,counter_change_not_save_completion=True,partial_write_observations=list(range(28,39)),precompletion_hash_temporarily_final_observation=37,transient_hash_observation=38,stable_hash_not_alone_save_completion=True,save_success_text_observation=39,save_success_wording_observed=True,stable_field_observation=42,progress_inputs=82,continue_inputs=13,screen_count=45,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'physical flags全保持/第9ディグダはexpandedだけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save87/86と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,87,s.LAYOUT);new,rb=s.bank(after,0,88,s.LAYOUT);_,rc=s.bank(after,0xe000,87,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save87全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23164,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,39,7),(259,166,165)],'S61Eの4373/4377 clear・4376 setだけ')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4376,4378))for f in range(4372,4379)},'local10除去/local6/11復帰/初回flag保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,13,26),(0x4022,0,3)],'aux4021/4022だけ変化。runtime ownerは未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7192,1843),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[[4373,1,0],[4376,0,1],[4377,1,0]],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,var40ac_before=16,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==45,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][42]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新13歩と第9ディグダ、新戦闘0')
    need(measured['frontier']==dict(kind='ninth_diglett_event',trigger=[6,8],map=[10,16],xy=[6,7],observation=20,local_id=10,facing=1),'最初の第9配置変更直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+21:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0042.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='fe62a4b7b3368b04c6cec36a3e38d4e9f0e267ff9643000f2b4f2b7cbaf2745a','第9配置変更後field/freshContinue全pixel一致')
    need(measured['ninth_diglett_interacted']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常配置変更だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定第9ownerを実入力と照合')
    need(inspection['initial_flags']=={str(f):int(f in(4373,4377,4378))for f in range(4372,4379)}and inspection['expected_flag_changes']==[[4373,1,0],[4376,0,1],[4377,1,0]]and inspection['instruction_count']==47 and inspection['text_count']==2,'第9限定47命令/2台詞')
    need(inspection['expected_object_changes']==[dict(local_id=10,operation='removeobject'),dict(local_id=6,operation='addobject'),dict(local_id=11,operation='addobject')],'local10除去/local6/11復帰を保存flagと固定ownerで照合。全object画面内とは主張しない')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save88_next_route.json').read_bytes())

