#!/usr/bin/env python3
"""館内新10歩と通行境界のSave60原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save60_measure as m
from pr16_story_after_maori import need,identity
SOURCE='782cf85e25dc2bb3e73134af027431be9724e084'
RUN,JOB,ARTIFACT=37157997847,111305340925,11286820207
ARCHIVE=dict(size=131705,sha256='48d6c06bd95ebead9c5dc0e7081277dfa660a3e6e869033e84b4b10c484a3670')
OUTPUT=dict(size=131088,sha256='40d65e6b41a49a59d295667ea30a88496da25c641ac8896059ed4d1fce196b0f')
PARTY='67cb7176527d2cd35141b4a6a89b22f0ec135c79dd452e5cffef43db8de39f26'
FLASH='9a1ca2afce539e0bdba811222d41383ed75115fb90d9e6a805b488fc43f7b5a1'
LEDGER='fd17077e18b3f159f176b300578a7a563adeb077729226917b9d0b2ac9a238c8';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save60_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE60_JA.md'
EVIDENCE='content/modernization/pr16_story_save60_evidence'
VISUAL='content/modernization/pr16_story_save60_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[5, 7], [5, 6], [6, 6], [7, 6], [8, 6], [9, 6], [10, 6], [11, 6], [12, 6], [13, 6], [14, 6]]
FLASH_PHASES=['e525f1e4f48eac47b6f7cd7d3431de681d1a97fbf36cc1bfd42e73a3d1fa2869', 'a454959d75616cd131a7b71e3102aed2a2d0bfced431a6efe7ec1ee868078399', 'c3f8a67b29b5307d2bc96f39af5ffab63cf24769495ae0b9e582939b0848f1ea', '42d934633b963703858c64a110fca88f96d35cd5d2d4cf557725d39a64a0e584', '2d21b9a62273b7931bfd00688dec5cfbdf8e202c60170bcff619f235582b3861', 'ebd2f168eacf5e6be4b0bf19c3933a14f0727af869743134e99424d37a51095a', '8d45a4a3234ed942e71ad000c42b432a9ee23f75f95a1559f5359733306ece07', 'b2d562b4ccc70359630cdb469a1b130f681e991d142823a8b31acb121567dad3', '5320e05ef3ea682c6804ce239cf2f9db50947d96e9fec1045d07334dc2be4dd3', '0898a2f424237904348b7bc9ae98d999b8aa1ed72e07b54c7e865cb56974f18d', '59b6183c13745bf28e129e3f91f1ac69cd3282833c16edf35f55c851156c8350', 'b9ef28b98dd138426ee7206fb4f1cd32f647ee652c52e1afac27053a0ef4bafe', '9947b39abed20523e0a717ecbc86aa877f855aa7050ae8bcb05673c6646b9cbf', '9a1ca2afce539e0bdba811222d41383ed75115fb90d9e6a805b488fc43f7b5a1', '661a76d36ce7fb40f61c1c3cbdaa71d32be904f9baee2e8604f3e5800411c8e4']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
def motion(i):
    if i==0:return [5,7],2
    if i==1:return [5,6],2
    if i==2:return [5,6],4
    if i<=11:return [i+3,6],4
    return [14,6],4

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==42 and len(bo)==2,'全44画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(75,3200)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間75/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i)
        need(o['map']==[1,59]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'新10歩/東不通3回の位置・向き')
        need(o['callback2']==m.m.FIELD and o['field']is(i<15 or i==41)and o['lock']==int(15<=i<41),'保存menu以外はidle field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.LEDGER,'全party/RAM台帳不変')
        need(o['save_counter']==(59 if i<36 else 60),'36counterは保存中、37成功')
        wanted=m.a.FLASH if i<22 else FLASH_PHASES[i-22]if i<37 else FLASH
        need(o['flash_sha256']==wanted,'35一時最終hash/36部分write/37最終Flashを区別')
    need(len(set(FLASH_PHASES))==15 and FLASH_PHASES[-2]==FLASH and FLASH_PHASES[-1]!=FLASH,'35hash一致は保存完了でない')
    for o in bo:
        m.idle(o,60);need(o['map']==[1,59]and o['xy']==[14,6]and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_DYNAMIC_EDGE_SAVE60_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=60,map=[1,59],map_name_ja='こころのやかた・入口階',xy=[14,6],facing=4,party_count=4,rp=0,travel_steps=10,turns=1,unpassed_edge_attempts=3,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,11],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],move_commands=0,target_confirmations=0,move_commands_not_automatically_pp_uses=True,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=True,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=36,counter_change_not_save_completion=True,partial_write_observations=list(range(22,35))+[36],early_final_hash_observation=35,stable_hash_not_alone_save_completion=True,save_success_text_observation=37,save_success_wording_observed=True,stable_field_observation=41,progress_inputs=75,continue_inputs=13,screen_count=44,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,
        nearby_moving_npc_observed=True,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=False,field_pixel_diff_bbox=[129,58,143,80],field_pixel_diff_count=211)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/PP/HP/EXP/持物不変');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags不変');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save59/60と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,59,s.LAYOUT);new,rb=s.bank(after,0,60,s.LAYOUT);_,rc=s.bank(after,0xe000,59,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save59全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[15,10,15,11]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==17904,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,66,76)],'aux1変数。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6959,1713),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[15,10,15,11],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def field_pixels(folder):
    folder=Path(folder)
    a=(folder/'progress/screen-0041.ppm').read_bytes();b=(folder/'continue/screen-0001.ppm').read_bytes()
    need((folder/'progress/screen-0014.ppm').read_bytes()==a and (folder/'continue/screen-0000.ppm').read_bytes()==b,'各core終端2枚はそれぞれ同一')
    x,y=a.split(b'\n',3)[3],b.split(b'\n',3)[3];need(len(x)==len(y)==240*160*3,'実PPM pixels')
    ds=[i for i in range(240*160)if x[i*3:i*3+3]!=y[i*3:i*3+3]]
    need(len(ds)==211 and [min(i%240 for i in ds),min(i//240 for i in ds),max(i%240 for i in ds)+1,max(i//240 for i in ds)+1]==[129,58,143,80],'周囲NPCの211pixel限定差分。player/床/暗所保持')
    return dict(different_pixels=len(ds),bbox=[129,58,143,80],all_pixels_identical=False,runtime_npc_identity_resolved=False)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==44,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][41]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is False and measured['battle']is None,'通常10歩のみ。上階未到達/新戦闘0')
    need(measured['frontier']==dict(kind='unpassed_edge',before=[14,6],target=[15,6],attempts=3,map=[1,59],xy=[14,6],observation=14),'最初の未通過edge直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+15:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    result['field_pixels']=field_pixels(folder)
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['inert_warp8']['behavior']==8 and inspection['entry']['xy']==[30,10],'有効階段への静的経路と実到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
