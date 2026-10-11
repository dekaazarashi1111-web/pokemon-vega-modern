#!/usr/bin/env python3
"""第10ディグダ配置変更のSave89原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save89_measure as m
from pr16_story_after_maori import need,identity
SOURCE='7f38199514ae1703a1c5a9fdce65179a5c5711fe'
RUN,JOB,ARTIFACT=37183787022,111381430465,11295599506
ARCHIVE={'size': 196409, 'sha256': '23e6029c833fde5eff4d78e5bfaf6dd1b42e8392cff9aee487b6cddcfca16774'}
OUTPUT={'size': 131088, 'sha256': '981089324f749ae85d82a42e41743fc529edf45c95ac510f3aef53fd1e0412b2'}
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='dd525704c9032639a95fd0da2d793384f3a8b618adfc47082dafa78f36d153ce'
LEDGER='25e14aa8952190dae350858541a406b7ddcb2a9539af79800a82581ac0819b8d';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save89_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE89_JA.md'
EVIDENCE='content/modernization/pr16_story_save89_evidence'
VISUAL='content/modernization/pr16_story_save89_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE+[[9,11]]
FLASH_PHASES=['68606b271949ad074c11918791fc740a92c578dc17d4372fc33776b0b61da234', '3509e16ecb322ce44b5c7f52d59da7be1798467698d5aae93ad37f703c4fc03c', 'c77807bc7466aeefe9a93fbc5000ff6bd2ff4365975c5ae7623f5c750eafe537', '57b473454f926fd41a214f6f71bd4915605d7902ee46b412948a44227342a592', '0182434bef5de91f1f44ed9166ce98cd231e2d716eb6c78d57f320672d00c963', '7bc42fa618ad9317f6b5dde204da5575a94ed4c17c6c804a9561253c872bb335', '7e11f70df1ee94f15c65b905f3ab08dfe4b6436980ab8f7c3227007b687a2e93', '1defe2f4a835efc1ecb9e08a0c08b70c45bf8a8916925f5b9ea5448f049b2d83', '63e7acea2e4462b3edeb41d40a961e6c73c81366bce6893f398ae2178fbc22cb', '299e2e2363259c449f178d8e69d8750e6b3c944914795bbc7b379a3e62d8821f', 'c7ec74b0de24b72361d26bb8c54e06fef285bfac4bb919ef461a9204b996525d']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==43 and len(bo)==2,'全45画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(82,3613)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新13歩/4旋回/第10ディグダ82+cold13入力')
    positions=[[6,7],[6,8],[6,9],[6,9],[5,9],[4,9],[3,9],[3,9],[3,10],[3,11],[3,11]]+[[x,11]for x in range(4,10)]
    need(len(positions)==17,'南2西3南2東6と途中3旋回')
    for i,o in enumerate(ao):
        xy=positions[i]if i<17 else[9,11];face=1 if i<3 else 3 if i<7 else 1 if i<10 else 4 if i<17 else 1;field=i<18 or i in(20,42)
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[x+7 for x in xy]and o['facing']==face,'13歩/3旋回と17の南旋回。local8へ踏み込まない')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'18台詞/19配置変更/20field/21menu/42field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持。旧raw41系列差分ownerとは別')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<14 else LEDGER),'14でRAM台帳変化。runtime owner未解明、旧差分とは別')
        need(o['save_counter']==(88 if i<38 else 89),'38counter89でも保存中、39成功/42field')
        wanted=m.a.FLASH if i<28 else FLASH_PHASES[i-28]if i<39 else FLASH
        need(o['flash_sha256']==wanted,'28〜38部分保存hash、38counter89、39最終hash/成功文言を区別')
    need(ao[37]['flash_sha256']!=FLASH and ao[37]['save_counter']==88 and ao[38]['flash_sha256']!=FLASH and ao[38]['save_counter']==89 and ao[39]['flash_sha256']==FLASH,'counter/hash単独で完了としない')
    for o in bo:
        m.idle(o,89);need(o['map']==[10,16]and o['xy']==[9,11]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame/全SaveRTC/party/終端RAM保持')
    return dict(status='PASS_TENTH_DIGLETT_EVENT_SAVE89_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=89,map=[10,16],map_name_ja='ミルジム',xy=[9,11],facing=1,party_count=4,rp=0,travel_steps=13,turns=4,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,tenth_diglett_event_accepted=True,second_diglett_previously_accepted=True,third_diglett_previously_accepted=True,fourth_diglett_previously_accepted=True,fifth_diglett_previously_accepted=True,sixth_diglett_previously_accepted=True,seventh_diglett_previously_accepted=True,trainer132_previously_accepted=True,trainer160_previously_accepted=True,tenth_diglett_local_id=8,removed_local_ids=[9],restored_local_ids=[10],interacted_local8_remains=True,all_changed_objects_visible=False,object_changes_bound_to_flags_and_source=True,gym_puzzle_completed=True,gym_leader_defeated=True,gym_exit_accepted=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[14],ram_difference_owner_resolved=False,old_save77_cold_difference_owner_resolved=False,old_save78_progress_difference_owner_resolved=False,old_save80_progress_difference_owner_resolved=False,old_save82_progress_difference_owner_resolved=False,old_save83_progress_difference_owner_resolved=False,old_save85_progress_difference_owner_resolved=False,old_save87_progress_difference_owner_resolved=False,save89_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=38,counter_change_not_save_completion=True,partial_write_observations=list(range(28,39)),precompletion_hash_temporarily_final_observation=None,last_partial_hash_observation=38,stable_hash_not_alone_save_completion=True,save_success_text_observation=39,save_success_wording_observed=True,stable_field_observation=42,progress_inputs=82,continue_inputs=13,screen_count=45,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'physical flags全保持/第10ディグダはexpandedだけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save88/89と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,88,s.LAYOUT);new,rb=s.bank(after,0xe000,89,s.LAYOUT);_,rc=s.bank(after,0,88,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save88全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23164,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,7,135),(259,165,164)],'S61Eの4375 set・4376 clearだけ')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4375,4378))for f in range(4372,4379)},'local9除去/local10復帰/local8保持/初回flag保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,26,39),(0x4022,3,1)],'aux4021/4022だけ変化。runtime ownerは未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7197,1843),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[[4375,0,1],[4376,1,0]],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,var40ac_before=16,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==45,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][42]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新13歩と第10ディグダ、新戦闘0')
    need(measured['frontier']==dict(kind='tenth_diglett_event',trigger=[9,12],map=[10,16],xy=[9,11],observation=20,local_id=8,facing=1),'最初の第10配置変更直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+21:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0042.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='6717474b50599125a3a8ec658368e4077697d6d10178068de2fd2dc2776fdbda','第10配置変更後field/freshContinue全pixel一致')
    need(measured['tenth_diglett_interacted']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常配置変更だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定第10ownerを実入力と照合')
    need(inspection['initial_flags']=={str(f):int(f in(4376,4378))for f in range(4372,4379)}and inspection['expected_flag_changes']==[[4375,0,1],[4376,1,0]]and inspection['instruction_count']==39 and inspection['text_count']==2,'第10限定39命令/2台詞')
    need(inspection['expected_object_changes']==[dict(local_id=9,operation='removeobject'),dict(local_id=10,operation='addobject')],'local9除去/local10復帰を保存flagと固定ownerで照合。全object画面内とは主張しない')
    canonical=(ROOT/'content/modernization/pr16_story_save88_next_route.json').read_bytes()
    need(planned['parent_route_binding']==identity(canonical+b'\n'),'測定preparationの親参照hashは読取copy末尾改行1byte付き。原本hashと区別')
    need(json.loads(canonical)==json.loads(canonical+b'\n')and json.loads(canonical)['route']==m.ROUTE,'親routeの意味は同一。ROM命令全byte検証は別途固定済み')
    result['preparation_parent_route_binding']=dict(repository_bytes=identity(canonical),local_read_copy=planned['parent_route_binding'],difference='one trailing LF in local read copy',semantic_equal=True,measurement_preparation_modified=False)
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save89_next_route.json').read_bytes())


