#!/usr/bin/env python3
"""南隣NPC迂回9歩と南東階段初接続のSave70原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save70_measure as m
from pr16_story_after_maori import need,identity
SOURCE='6f4a3adcfe115f28851bd9f9b9dd2209a37dc36d'
RUN,JOB,ARTIFACT=37165369734,111327062964,11288833014
ARCHIVE=dict(size=138756,sha256='5a1e40adc7cff652e1a1ee03d6f4ea58615ce732609c6a217cf7e8ca3970d4ea')
OUTPUT={'size': 131088, 'sha256': '94fd92a46700adcf4b5b1f8ddb811ad54ee080f488e60e844a08fe475139411a'}
PARTY='e27e2261c383575dbbf7516bd46fa6f74c5c050be4c73d4b2a68c672c461f646'
FLASH='5ec429f1d65411260fc9b3e4ca1b230a95bc3ec22a53ffd310c422d626a6ec66'
LEDGER='7db04a6f1f9a485025a6ab8122e21b7b697d5ce286258eb80454067113f37af0';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save70_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE70_JA.md'
EVIDENCE='content/modernization/pr16_story_save70_evidence'
VISUAL='content/modernization/pr16_story_save70_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[26, 28], [25, 28], [25, 29], [25, 30], [26, 30], [27, 30], [27, 29], [28, 29], [29, 29], [30, 29], [33, 29]]
FLASH_PHASES=['cedacb8aaf3148b9f6ba69a60684039d899bc793ba2c7c9f617f499a9343ddf4', '3e5ed206579febe0d45403553f914d8ea7787a6b5790fb992e5acdc36705803b', '3e3b56b1d24e6d576aff02052d10bfa15174a9e5db09e6af4f2d8378a08ca95a', 'c499db8b38b14f07445142604c63a0332c858eb89a632b2c7a076f85cd5f9c09', '42d3df9b13dfcbd5bd2cee1452001e31ae555c9861fa0252e0e1e5d66f192916', 'c6af40e649b26d499cac4e4cd647db999db85db49b8e5f87adee8defa446faef', '811f53a3a1739ef8d6bf5c0723e904ed04bfdadd7424c7dc889a8b5be944b0c9', '5f5a076af79b13a0781ee83b8fe5b04cf22ed17b76fbf9d56682600958a61639', '8a2518a407124c54907045b0eaebc4eb676a8bbe14c842d0e99900bb82830d46', 'bc51b5740e2d27a991449167c56f07ccc6ba9b74ccc30b78f2e8521a2389aa72', '8a55509e66fb48333ea595c6b70572f0b407015cb4ca7a8b6efceca62fdb4560', 'e2fcf6688cee026f4ca30c5152bb1fc8626f6e09b4f47ecffed2c2012a792226', 'f1f6ae0204f72e2ec086ff464d1113ea7c1e89479c5ff3db4db814c97260c517', '70d72c0b52cd1985ed65b4929fee941e79d51cd16fb2e1f891aff5e6baf23fb0', 'b1aa6420eb195df4f87aee6536e62754823b586e5e32985dcd15a65bbafbb463']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
MOTION=[([26,28],1),([26,28],3),([25,28],3),([25,28],1),([25,29],1),([25,30],1),([25,30],4),([26,30],4),([27,30],4),([27,30],2),([27,29],2),([27,29],4),([28,29],4),([29,29],4),([30,29],4),([33,29],4)]
def motion(i):return MOTION[min(i,15)]

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==43 and len(bo)==2,'全45画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(77,3388)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新迂回77/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i)
        need(o['map']==([1,59]if i<15 else [1,60])and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'下階NPC迂回9歩/転換5/東入力で階段→上階33,29東')
        need(o['callback2']==m.m.FIELD and o['field']is(i<=15 or i==42)and o['lock']==int(16<=i<=41),'階段到着/通常保存/安定fieldを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==(m.a.LEDGER if i<22 else LEDGER),'全party600byte/HP/PP保持。RAM台帳22変化はowner未解明')
        need(o['save_counter']==(69 if i<37 else 70),'37counterは保存中、38成功')
        wanted=m.a.FLASH if i<23 else FLASH_PHASES[i-23]if i<38 else FLASH
        need(o['flash_sha256']==wanted,'全15部分write/38最終Flashを区別')
    need(len(set(FLASH_PHASES))==15 and FLASH not in FLASH_PHASES,'counter70の37も部分write')
    for o in bo:
        m.idle(o,70);need(o['map']==[1,60]and o['xy']==[33,29]and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_SOUTHEAST_STAIR_SAVE70_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=70,map=[1,60],map_name_ja='こころのやかた・上階',xy=[33,29],facing=4,party_count=4,rp=0,travel_steps=9,turns=5,entry_warps=1,stair_activation_east_inputs=1,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=True,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[10,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[22],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=37,counter_change_not_save_completion=True,partial_write_observations=list(range(23,38)),stable_hash_not_alone_save_completion=True,save_success_text_observation=38,save_success_wording_observed=True,stable_field_observation=42,progress_inputs=77,continue_inputs=13,screen_count=45,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True,arrival_banner_present=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,1,0)],'上階接続でphysical2056のみ1→0。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save69/70と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,69,s.LAYOUT);new,rb=s.bank(after,0,70,s.LAYOUT);_,rc=s.bank(after,0xe000,69,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save69全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[10,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,20,29),(0x4022,0,4)],'aux2変数だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6851,1668),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[10,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==45,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][42]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['battle']is None,'新NPC迂回9歩と通常南東階段。新戦闘0')
    need(measured['frontier']==dict(kind='new_southeast_stair',map=[1,60],xy=[33,29],observation=15),'最初の南東階段到着直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+16:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0042.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'上階/階段/暗所field全byte一致')
    need((folder/'progress/screen-0015.ppm').read_bytes()!=frames[0],'到着15はmap名bannerあり。最終画面と同一とは主張しない')
    need(measured['southeast_stair_observed']is True and measured['hole_descent_observed']is False,'南東階段behavior108の初接続。穴再走0')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['entry']['xy']==[30,29]and inspection['arrival']['xy']==[33,29],'保存済階段ownerと通常移動を照合')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    p=json.loads((ROOT/'content/modernization/pr16_story_save62_evidence/route-plan.json').read_bytes());full=p['route'];first=full.index([60,33,29]);route=[v[1:]for v in full[first:]]
    need(len(route)==26 and route[-1]==[16,27]and all(v[0]==60 for v in full[first:]),'保存済上階南側25歩と紙側だけ。未実測')
    upper=json.loads((ROOT/'content/modernization/pr16_story_save57_preparation.json').read_bytes());cells={tuple(x['xy']):x for x in upper['terrain']}
    for xy in route:
        c=cells[tuple(xy)];need((c['collision'],c['elevation'],c['behavior'])==(0,3,111 if xy==[33,29]else 8),'始点階段/通常床だけ。保存済地形を再採取しない')
    for before,after in zip(route,route[1:]):m.direction(before,after)
    return dict(status='STATIC_UPPER_SOUTH_PAPER_APPROACH25_FROM_SAVE70_ONLY',map=[1,60],start=[33,29],target=[16,27],statue=[16,28],route=route,edges=25,native_route_accepted=False,southeast_stair_already_observed=True,paper_observed=False,new_rom_reads=0,new_terrain_cells=0)
