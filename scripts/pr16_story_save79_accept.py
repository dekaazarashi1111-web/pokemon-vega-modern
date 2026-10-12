#!/usr/bin/env python3
"""第3ディグダ配置変更のSave79原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save79_measure as m
from pr16_story_after_maori import need,identity
SOURCE='3a728e7cee7fd19ec21a86264b6e211c7bbe55a1'
RUN,JOB,ARTIFACT=37174296972,111353581646,11292333576
ARCHIVE=dict(size=160894,sha256='9c0aeb948cc228dd0da14c7b45194a677a0c680110857bdcf1e7463ee35a776b')
OUTPUT=dict(size=131088,sha256='88040caadde36a1cbad95bb8e558650089d868d742bba16809a3a32f8ae7553b')
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='be676050be404f65f800e54ed50f6464efd4e91ec14e6f3ec729aecae29a5298'
LEDGER='6027627107d4372b8f105caf2e5afbeafe1fe86b6d34bfb2a1931e0e3628f5bf';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER='6027627107d4372b8f105caf2e5afbeafe1fe86b6d34bfb2a1931e0e3628f5bf'
CP='content/modernization/pr16_story_save79_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE79_JA.md'
EVIDENCE='content/modernization/pr16_story_save79_evidence'
VISUAL='content/modernization/pr16_story_save79_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[x,13]for x in range(4,10)]+[[9,13]]
FLASH_PHASES=['3a347b107e2d56dacbcdd07fdd5c9c7528c0374c3dfeb4e22de6735b2fd4b935', '4921f83dc6df1c413bc89203bfc9399dc544e57565a104f24713c56280dbec36', '1dab1b8f4d3202954d989f6ac57e416f26cc0c9bb62d42ed65ad547005072d23', '863a9b5202c6e6f1bcfb3d32a5a453ff19494a8f8e8afefccfdf0614d21d95da', '3b84b698ded269846fb4e767c527b2ad58ca8da66d32c67ce5b531134c05efd3', '917fb3f781c795634e9c1f4d20d29e1edf25909e188a52d8ade45c9f25618c42', '4fe4638428aa8cefd462f696ebdd6c6d4d7c07f6931cd3d13d895bb693211e84', '0f4958ec67c7c86547d3b1386440b55ac8e77039e16d6fed012540bdbc1a90f4', 'e3a967009794ca4e9d97096c39ac2fc463dcab0c6afa8ecaf01f66bd8bf0d4c3', 'be676050be404f65f800e54ed50f6464efd4e91ec14e6f3ec729aecae29a5298']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==33 and len(bo)==2,'全35画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(62,3053)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新東5歩/2旋回/第3ディグダ62+cold13入力')
    for i,o in enumerate(ao):
        xy=[4 if i<2 else i+3,13]if i<7 else[9,13];field=i<=7 or i in(10,32);facing=4 if 1<=i<=6 else 2
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'新東5歩と東/北旋回だけ')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'8台詞/9配置変更/10field/11menu/32field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==LEDGER==m.a.COLD_LEDGER,'今回の全progress RAM台帳保持。過去差分owner未解明')
        need(o['save_counter']==(78 if i<28 else 79),'28counterと成功/32fieldを分離')
        wanted=m.a.FLASH if i<18 else FLASH_PHASES[i-18]if i<28 else FLASH
        need(o['flash_sha256']==wanted,'18〜27保存中/27最終hash先行/28counterと成功表示')
    need(all(v!=FLASH for v in FLASH_PHASES[:-1])and FLASH_PHASES[-1]==FLASH,'最終hashだけで保存完了としない')
    for o in bo:
        m.idle(o,79);need(o['map']==[10,16]and o['xy']==[9,13]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame後を保存/party/RAM別々に確認')
    return dict(status='PASS_THIRD_DIGLETT_EVENT_SAVE79_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=79,map=[10,16],map_name_ja='ミルジム',xy=[9,13],facing=2,party_count=4,rp=0,travel_steps=5,turns=2,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,third_diglett_event_accepted=True,second_diglett_previously_accepted=True,third_diglett_local_id=8,removed_local_ids=[5,8],restored_local_id=9,all_changed_objects_visible=True,gym_puzzle_completed=False,gym_leader_defeated=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=True,ram_ledger_changed_observations=[],ram_difference_owner_resolved=False,old_save77_cold_difference_owner_resolved=False,old_save78_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=28,counter_change_not_save_completion=True,partial_write_observations=list(range(18,28)),stable_hash_not_alone_save_completion=True,save_success_text_observation=28,save_success_wording_observed=True,stable_field_observation=32,progress_inputs=62,continue_inputs=13,screen_count=35,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'physical flags全保持/第3ディグダはexpandedだけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save78/79と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,78,s.LAYOUT);new,rb=s.bank(after,0xe000,79,s.LAYOUT);_,rc=s.bank(after,0,78,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save78全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,135,87)],'S61Eの4372/4374 set・4375 clearだけ')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4372,4374,4378))for f in range(4372,4379)},'local5/8非表示/local9復帰/初回flag保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,92,97)],'aux4021だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==0,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and not(fb[2083//8]&(1<<(2083%8))),'badge1/ナギナタbadge未取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7068,1804),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[[4372,0,1],[4374,0,1],[4375,1,0]],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==35,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][32]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新東5歩と第3ディグダ、新戦闘0')
    need(measured['frontier']==dict(kind='third_diglett_event',trigger=[9,12],map=[10,16],xy=[9,13],observation=10,local_id=8,facing=2),'最初の第3配置変更直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+11:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0032.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='ddc347f0efd5005845f5c48311265624b48c38ce9c14db42a62215e0ab196645','第3配置変更後field/freshContinue全pixel一致')
    need(measured['third_diglett_interacted']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常配置変更だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定第3ownerを実入力と照合')
    need(inspection['initial_flags']=={str(f):int(f in(4375,4378))for f in range(4372,4379)}and inspection['expected_flag_changes']==[[4372,0,1],[4374,0,1],[4375,1,0]]and inspection['instruction_count']==43 and inspection['text_count']==2,'第3限定43命令/2台詞')
    need(inspection['expected_object_changes']==[dict(local_id=5,operation='removeobject'),dict(local_id=8,operation='removeobject'),dict(local_id=9,operation='addobject')],'画面内local5/8除去とlocal9復帰の固定owner')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save79_next_route.json').read_bytes())
