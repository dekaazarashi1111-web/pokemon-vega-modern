#!/usr/bin/env python3
"""博物館入場Save92の原本だけを独立受入。旧native/既受入試験は再走しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save92_measure as m
from pr16_story_after_maori import need,identity
SOURCE='afe866267733b0b48d0f971f52b971d03aa6f2bc'
RUN,JOB,ARTIFACT=37187019619,111390998562,11297164221
ARCHIVE=dict(size=263493,sha256='c2597abb5dac65d37d1011066547495d5fac963ea76275186100d2f48f2184e9')
OUTPUT=dict(size=131088,sha256='79864ff24d80a3b1cee73166bffb95f5795e2450f54582bad67ac6c024e2f9bf')
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='dc32963ad23faab6b69e447e91372fbd1022c009a206415a842cac20d3316f02'
LEDGER='9ec11aa0a1bdb1cd0f3249e05c96218f562911b9089f274134863b5fa143844f';COLD_LEDGER=LEDGER;SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save92_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE92_JA.md'
EVIDENCE='content/modernization/pr16_story_save92_evidence'
VISUAL='content/modernization/pr16_story_save92_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace=m.a.trace;trace_rows=m.a.trace_rows;ROUTE=m.ROUTE
POSITIONS=[[20, 11], [20, 12], [20, 13], [20, 14], [20, 15], [20, 16], [20, 17], [20, 18], [20, 19], [20, 20], [20, 21], [20, 22], [20, 22], [21, 22], [22, 22], [23, 22], [23, 22], [23, 23], [23, 24], [23, 25], [23, 26], [23, 26], [22, 26], [21, 26], [20, 26], [19, 26], [19, 25], [14, 9]]
FLASH_PHASES=['04e68d6d7c559933dfd3fbfc169f44fe40864da1e020f6c82072d658350e91e4', '3103cdb054fafb4edc64f54e9e2affd0c380357c1dd142b06369e9e175249ea9', 'dde53b26597b5844327456f5711153ea2ba3199e66e05cbb53eadc8e6cf58867', '9c458b69ff0e934d5a3582bf5d8893740d43bf873980386a903cc92c7567dec6', '59e7d02820795cecf9230f835657c5d551a10ef92327cc69b22d140586dc352d', '3aca087fad91a948bb445dbe72ef8c6d801041b291170ea042eebca123dc82e6', '0e9902965b1946c7149447f204c66427d2a18bacc00e6a4444af057711295035', 'ed9456280a813b6100e1e50a7de120872dea85e29bffbbd969b94198612b0caf', '8c340f44157ccb0499ff296351475a54e47c7d35fc95ff645daf7d2d98bd46e3', 'ad7abb6191c79c64185af64a47620ba052120f606ac3e628d9fa18c5ddbcd197', 'f84837b7781085180a653b50e74b285df468c73a5ace8d4c63cd6b6723f9383e', '1050a30efd96ef6b8cb1b967efaac700f1ea9b600a466f1e3af8586ef4f9954d', '1050a30efd96ef6b8cb1b967efaac700f1ea9b600a466f1e3af8586ef4f9954d']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==53 and len(bo)==2,'全55画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(98,3992)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新23歩/旋回3/warp1/98+cold13入力')
    for i,o in enumerate(ao):
        xy=POSITIONS[i]if i<28 else[14,9];where=[3,2]if i<27 else[6,0];field=i<26 or i in(27,52)
        facing=1 if i<12 or 16<=i<21 else 4 if i<16 else 3 if i<26 else 2
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'23歩/3旋回/入場warp1・14,9北。自動北1歩なし')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'26入場遷移→27博物館field→28menu→52field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<5 else LEDGER),'20,16の観測5でRAM ledger差分。owner未解明')
        need(o['save_counter']==(91 if i<48 else 92),'48counter92/成功文言→52field')
        wanted=m.a.FLASH if i<35 else FLASH_PHASES[i-35]if i<48 else FLASH
        need(o['flash_sha256']==wanted,'35〜47部分書込、46/47同hashでも保存中、48最終hashと成功文言')
    need(ao[46]['flash_sha256']==ao[47]['flash_sha256']!=FLASH and ao[47]['save_counter']==91 and ao[48]['save_counter']==92 and not ao[48]['field'],'途中同hash/counter単独で完了としない')
    for o in bo:
        m.idle(o,92);need(o['map']==[6,0]and o['xy']==[14,9]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame/全SaveRTC/party/RAM保持')
    return dict(status='PASS_MUSEUM_ENTRY_SAVE92_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=92,map=[6,0],map_name_ja='ミルシティ博物館1階',xy=[14,9],facing=2,party_count=4,rp=0,travel_steps=23,turns=3,warps=1,automatic_entry_step_observed=False,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_second_floor_accepted=False,gym_flags4372_to4378_all_clear=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[5],ram_difference_owner_resolved=False,old_save89_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,flag2056_runtime_owner_resolved=False,auxiliary_runtime_owners_resolved=False,save_counter_changed_observation=48,counter_change_not_save_completion=True,partial_write_observations=list(range(35,48)),first_final_flash_observation=48,last_partial_hash_observation=47,save_in_progress_observations=list(range(35,48)),stable_hash_not_alone_save_completion=True,save_success_text_observation=48,save_success_wording_observed=True,stable_field_observation=52,progress_inputs=98,continue_inputs=13,screen_count=55,native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,0,1)],'博物館入場physical2056だけset。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save91/92と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,91,s.LAYOUT);new,rb=s.bank(after,0,92,s.LAYOUT);_,rc=s.bank(after,0xe000,91,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save91全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23164,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'S61E全payload保持/紙未引渡し')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'前回clearの4372〜4378全保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,49,71),(0x4022,1,3),(0x404d,33,7)],'入場時3変数差分を全件台帳化。runtime ownerは未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7105,1806),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==55,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][52]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE[:-1]and measured['battle']is None,'新23歩/旋回3/warp1、新戦闘0。warp tileは遷移観測で別確認')
    need(measured['frontier']==dict(kind='new_museum_entry',trigger=[19,25],map=[6,0],xy=[14,9],facing=2,observation=27),'最初の博物館到着直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+28:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0052.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='4f96e2e75a5080cc97e88e3edc4c1e4fe1b3217e9498cde38a962cb6a91ae420','独立Continue/120frame後も全38400pixel一致')
    need(measured['museum_entry_observed']is True and measured['museum_entry_accepted']is False and measured['paper_consumed_or_delivered']is False,'測定原本は受入前・紙保持')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['warp_owner']==planned['warp_owner'],'固定warpを実入力と照合')
    need(inspection['initial_flags']=={str(f):0 for f in range(4372,4379)}and inspection['binding_count']==54,'入場地形54範囲')
    canonical=(ROOT/'content/modernization/pr16_story_save91_next_route.json').read_bytes()
    need(planned['parent_route_binding']==identity(canonical)and json.loads(canonical)['route']==m.ROUTE,'親route原本exact byte identity/意味一致')
    for row in planned['bindings']:need(rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'入場地形/warp全byte')
    result['preparation_parent_route_binding']=dict(repository_bytes=identity(canonical),measurement_preparation_modified=False,exact_bytes=True)
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save92_next_route.json').read_bytes())
