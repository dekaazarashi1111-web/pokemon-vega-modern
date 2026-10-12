#!/usr/bin/env python3
"""第4ディグダ配置変更のSave80原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save80_measure as m
from pr16_story_after_maori import need,identity
SOURCE='f508187e5b698a598eaffe0916a9d83c2a21753c'
RUN,JOB,ARTIFACT=37174872497,111355311681,11292349565
ARCHIVE={'size': 176497, 'sha256': 'e433d24c51758611f085eae80814a727740ceab682efabd1d6398dc7c70f83fb'}
OUTPUT={'size': 131088, 'sha256': '6083038273bdf89de7563800c91a215c861552e7fc4da71af7c4a3c3237580dc'}
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='37c0c025035e3bcf62613d8348243b8ea69a7076c93104e9dcc11be6a6db06d3'
LEDGER='e9f829d587b02ef89c69b1736e19875c43bf691510ae78054ddb668d18c59ba4';COLD_LEDGER='e9f829d587b02ef89c69b1736e19875c43bf691510ae78054ddb668d18c59ba4'
SETTLED_COLD_LEDGER='e9f829d587b02ef89c69b1736e19875c43bf691510ae78054ddb668d18c59ba4'
CP='content/modernization/pr16_story_save80_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE80_JA.md'
EVIDENCE='content/modernization/pr16_story_save80_evidence'
VISUAL='content/modernization/pr16_story_save80_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE+[[3,9]]
FLASH_PHASES=['dd1c2a057e19474f16d630e231f764044c3c00f7f03a9df8e172d50fc15f17d4', '858da8e631c2e462a17414f77bb135d212b8d696f5ceb51ddefff6200a945c65', '3c4b634deb9b87630b85a1945c584c8db91096c007e2cf3892e557257a5db18d', '931fc2933f0b3bc145d10ec4fc3e18e762fad5f41d8922b422de83f1ec336daf', '9261076e56110f326c6f09ccd486bf5e3124449820bbbfbc7b536bf9918645b3', '75efc687a1ab9e8afc0c1b5b29f3684d60d118ead18efad463064297f01f5723', '9a87ad606285fc16c1272a9a25b1a47e406fe3fb3cfa00d6b8995907cfe995ff', '0ed8004456a7995327f064891e6f79a72162212d99e990b60bc735f08bc70f3a', '1c4035816f4df6a9bbe03eea9754a3b4a606299e8c40eead8aeb075ef9b79127', 'b6050c3e75238fac53d12e1949177a9e3369e87c970093b3cd4e9f5b905ebe7f', '2201f88344773ab61b6cc2b58c7e5c044036ceca37f692b9b154d28bd5509345']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==39 and len(bo)==2,'全41画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(74,3389)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新10歩/3旋回/第4ディグダ74+cold13入力')
    positions=[[9,13],[9,12],[9,11],[9,11]]+[[x,11]for x in range(8,2,-1)]+[[3,11],[3,10],[3,9]]
    for i,o in enumerate(ao):
        xy=positions[i]if i<len(positions)else[3,9];field=i<=13 or i in(16,38);facing=2 if i<=2 or 10<=i<=12 else 3
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'新10歩と西/北/西3旋回だけ')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'14台詞/15配置変更/16field/17menu/38field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<19 else LEDGER),'19menu中RAM台帳変化を明示。今回/過去差分owner未解明')
        need(o['save_counter']==(79 if i<34 else 80),'34counterのみ/35成功/38fieldを分離')
        wanted=m.a.FLASH if i<24 else FLASH_PHASES[i-24]if i<35 else FLASH
        need(o['flash_sha256']==wanted,'24〜34保存中/34counter先行/35最終hashと成功表示')
    need(all(v!=FLASH for v in FLASH_PHASES)and ao[34]['flash_sha256']!=FLASH and ao[35]['flash_sha256']==FLASH,'最終hashだけで保存完了としない')
    for o in bo:
        m.idle(o,80);need(o['map']==[10,16]and o['xy']==[3,9]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame後を保存/party/RAM別々に確認')
    return dict(status='PASS_FOURTH_DIGLETT_EVENT_SAVE80_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=80,map=[10,16],map_name_ja='ミルジム',xy=[3,9],facing=3,party_count=4,rp=0,travel_steps=10,turns=3,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,fourth_diglett_event_accepted=True,second_diglett_previously_accepted=True,third_diglett_previously_accepted=True,fourth_diglett_local_id=9,removed_local_id=9,restored_local_ids=[5,8],all_changed_objects_visible=False,restored_local5_fully_visible=False,restored_local5_partially_visible=True,gym_puzzle_completed=False,gym_leader_defeated=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[dict(lane='progress',observation=19)],ram_difference_owner_resolved=False,old_save77_cold_difference_owner_resolved=False,old_save78_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=34,counter_change_not_save_completion=True,partial_write_observations=list(range(24,35)),stable_hash_not_alone_save_completion=True,save_success_text_observation=35,save_success_wording_observed=True,stable_field_observation=38,progress_inputs=74,continue_inputs=13,screen_count=41,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'physical flags全保持/第4ディグダはexpandedだけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save79/80と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,79,s.LAYOUT);new,rb=s.bank(after,0,80,s.LAYOUT);_,rc=s.bank(after,0xe000,79,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save79全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,87,135)],'S61Eの4372/4374 clear・4375 setだけ')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4375,4378))for f in range(4372,4379)},'local9非表示/local5/8復帰/初回flag保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,97,107)],'aux4021だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==0,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and not(fb[2083//8]&(1<<(2083%8))),'badge1/ナギナタbadge未取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7132,1831),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[[4372,1,0],[4374,1,0],[4375,0,1]],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==41,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][38]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新10歩と第4ディグダ、新戦闘0')
    need(measured['frontier']==dict(kind='fourth_diglett_event',trigger=[2,9],map=[10,16],xy=[3,9],observation=16,local_id=9,facing=3),'最初の第4配置変更直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+17:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0038.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='6cf7564de0f99970eb4386f6d1b2f5735d653844cc564169058524752d8b2272','第4配置変更後field/freshContinue全pixel一致')
    need(measured['fourth_diglett_interacted']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常配置変更だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定第4ownerを実入力と照合')
    need(inspection['initial_flags']=={str(f):int(f in(4372,4374,4378))for f in range(4372,4379)}and inspection['expected_flag_changes']==[[4372,1,0],[4374,1,0],[4375,0,1]]and inspection['instruction_count']==47 and inspection['text_count']==2,'第4限定47命令/2台詞')
    need(inspection['expected_object_changes']==[dict(local_id=9,operation='removeobject'),dict(local_id=5,operation='addobject'),dict(local_id=8,operation='addobject')],'local9除去とlocal5/8復帰の固定owner。画面下端のlocal5は保存flagでも照合')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save80_next_route.json').read_bytes())
