#!/usr/bin/env python3
"""新8歩と北東階段による上階初到達のSave63原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save63_measure as m
from pr16_story_after_maori import need,identity
SOURCE='a4995895e0933dc8728a53258fed3057b10ba128'
RUN,JOB,ARTIFACT=37160910114,111313959362,11287229492
ARCHIVE=dict(size=134168,sha256='d3705b4666e2cdf3e8416a2ed2262d3e9e154a3434d312960bec42e6f9ebd900')
OUTPUT={'size': 131088, 'sha256': '76dacf781f2e6cf3f44521223cf0c9228e9ca7e04ce26fadeabceba4c1777c87'}
PARTY='a7d3e16a14fc09aacf9790ec910f6985b3f786c99bd12c7618f0b196ab496ae1'
FLASH='4f5ac2439890bb49ab55d992a17a622219aa29f9c00a39d84cca8543190f904d'
LEDGER='83cfd306095082a9c7e787e4fd549b1072b4272e7a8169a3923f0e459d6d87d0';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save63_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE63_JA.md'
EVIDENCE='content/modernization/pr16_story_save63_evidence'
VISUAL='content/modernization/pr16_story_save63_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[26, 6], [27, 6], [28, 6], [28, 7], [28, 8], [28, 9], [28, 10], [29, 10], [30, 10], [32, 10]]
FLASH_PHASES=['558a468ca7c8bc4df30ad246ad50f2f6114c5888c8d1d764ae3cb6fdfd45f420', 'f510104b6ed9ccf08068e616d041b650659d2e007a8818f3a8626d908e7b37b0', 'fddd9ded6e2f35172bc19f30e13b1f915deb38fb358a9641b2d61fe58b1de035', '703340cbd6ec3d5dbf7480356bb5e0d61dd860b2ea82144cf63629908706dbff', '61f6f95aaf17d91bcf85a062742998bf72190d651cd510b1ff4d3e967ed2ffd3', 'be5dd2dc81bc28bb1ae17d0c715665301fe4c14e905caf3db10356257f4eb928', '3ffcd0c7db32629205080b8c0c9da1cc687832e2cdf135e69b51a5486e41dde6', 'aeb0b8f8a580cea97a1616352c20218e6197d76c3d36ed544970f5fa8e74d35d', '6fefec3110996965d8b80efe9d8e12c9556be96c4cd8e3c6c607562f7bc0d263', '019a3f5d2545d9b8179d026ca812f96ebeda8135bd983e7ac5d3d98d967de7d4', 'c8466f6ec733877ee76c0aa5db2f3b88645edae63f5c70a23c1a22d55e594a39', '1aaf31475a0adef56d668ba1f13d845f69180e2dbe5dfe275f474807d86cb2c0', '417daefe305f1720ab7ae9f36da33cff19720ada1102e80d97cc207805981be9', '4f5ac2439890bb49ab55d992a17a622219aa29f9c00a39d84cca8543190f904d', 'e1b8b18aa746e213aa1309e2d688432a1c6f978fcbfbe8dad573c827f19b835b']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
def motion(i):
    if i<=2:return [26+i,6],4
    if i<=7:return [28,6 if i==3 else i+3],1
    if i<=10:return [28 if i==8 else i+20,10],4
    return [32,10],4

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==39 and len(bo)==2,'全41画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(69,3164)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間69/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i)
        need(o['map']==([1,59]if i<11 else[1,60])and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'新8歩/方向転換2/実北東階段warpの位置・向き')
        need(o['callback2']==m.m.FIELD and o['field']is(i<12 or i==38)and o['lock']==int(12<=i<38),'上階到達と保存UI/安定fieldを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==(m.a.LEDGER if i<36 else LEDGER),'全party不変、RAM台帳は保存成功表示中36だけ変化')
        need(o['save_counter']==(62 if i<33 else 63),'33counterは保存中、34成功')
        wanted=m.a.FLASH if i<19 else FLASH_PHASES[i-19]if i<34 else FLASH
        need(o['flash_sha256']==wanted,'32一時最終hash/33部分write/34最終Flashを区別')
    need(len(set(FLASH_PHASES))==15 and FLASH_PHASES[-2]==FLASH and FLASH_PHASES[-1]!=FLASH,'32hash一致は保存完了でない')
    for o in bo:
        m.idle(o,63);need(o['map']==[1,60]and o['xy']==[32,10]and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_UPPER_STAIR_SAVE63_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=63,map=[1,60],map_name_ja='こころのやかた・上階',xy=[32,10],facing=4,party_count=4,rp=0,travel_steps=8,turns=2,entry_warps=1,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,6],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,move_commands_not_automatically_pp_uses=True,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[36],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=33,counter_change_not_save_completion=True,partial_write_observations=list(range(19,32))+[33],early_final_hash_observation=32,stable_hash_not_alone_save_completion=True,save_success_text_observation=34,save_success_wording_observed=True,stable_field_observation=38,progress_inputs=69,continue_inputs=13,screen_count=41,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True,arrival_banner_present=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/PP/HP/EXP/持物不変');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,1,0)],'map移動に伴うphysical2056解除だけ。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save62/63と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,62,s.LAYOUT);new,rb=s.bank(after,0xe000,63,s.LAYOUT);_,rc=s.bank(after,0,62,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save62全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[15,10,15,6]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==18744,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,89,97),(0x4022,0,3)],'aux2変数。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6890,1674),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[15,10,15,6],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==41,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][38]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['battle']is None,'新8歩/通常階段だけ。新戦闘0')
    need(measured['frontier']==dict(kind='new_floor_entry',map=[1,60],xy=[32,10],observation=11),'最初の新上階entry直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+12:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0038.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'上階/階段/暗所field全byte一致')
    need((folder/'progress/screen-0011.ppm').read_bytes()!=frames[0],'到着11はmap名bannerあり。終端と同一画像とは主張しない')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['inert_warp8']['behavior']==8 and inspection['entry']['xy']==[30,10],'旧着地点不発と有効階段の到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
