#!/usr/bin/env python3
"""館内新廊下のSave56原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save56_measure as m
from pr16_story_after_maori import need,identity
SOURCE='e622b26e0c00a1572e4d879c7ea0bb5c17ed0c01'
RUN,JOB,ARTIFACT=37152942259,111290374509,11284293358
ARCHIVE=dict(size=137517,sha256='4038800d9f5a1a74ad338b368bb51481b82bd9b58ac848046a30152586029a80')
OUTPUT=dict(size=131088,sha256='cf11b02c2152e238bf0f56fd2dadc3b30038ea6c45b105ca616ad4dc2ce93386')
PARTY=m.a.PARTY
FLASH='d4c94975ac367ab15605e500dd2867245984070e3d5c300759c94c5fb1f3dbab'
LEDGER=m.a.LEDGER;COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save56_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE56_JA.md'
EVIDENCE='content/modernization/pr16_story_save56_evidence'
VISUAL='content/modernization/pr16_story_save56_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent;trace=m.a.trace
ROUTE=[[16,20],[15,20]]+m.INTERIOR_ROUTE
FLASH_PHASES=['cfd408ce397c65ffd33eedcc6a5153eadb9a4e9b7fbf54f0840e4c3617541023', 'e3544e55e2b488c4eae3a03e9acb3e638253de605e67b2193817aab82cf15722', '2c9509be5e1fc76d1b3c7696f15a528e1d6280b9f3167d80464b6f7428509480', 'd65a2111e544338862332a91c4316b057f8902346f60123c30413603e1eac50f', 'cee9199677b72e28e94566645ac9e5f8814d9bd93e058c53ff9ee1bef8827f32', '91125dbdb69a8031794185295dba6c9806e4e98bb73a64a89f098b386bce7e38', '11fec72de2efbf33b04fe51593883eadaac45827dbb0855dda116b6d626b1f3a', 'f222d727917ea51b47bf694124e41c5117c53881cf114a4657d8ca2dbae879d6', '53454d59f37c46c7902302b7a97f79f572182ea82cb4a047fce7ed878427e919', '559b470236485de7703030c21fcd9e12def054fea21c8163bbcc9ea2a611a043', '2ab44170c62f32e5553fb0673c53a52a729eaf0c9590960152714246934d58ac', 'd4c94975ac367ab15605e500dd2867245984070e3d5c300759c94c5fb1f3dbab', 'd4c94975ac367ab15605e500dd2867245984070e3d5c300759c94c5fb1f3dbab', 'eafa0d22872d08f7813862f077b1ceeb43d68a9e5fbb69754b7f6903ff3b813e']
def motion(i):
    if i<6:return [([16,20],1),([16,20],3),([15,20],3),([15,20],2),([20,33],0),([20,33],2)][i]
    return([20,max(25,38-i)],2)
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==39 and len(bo)==2,'全41画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(70,3208)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間70/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);where=[3,2]if i<4 else[1,59];field=i<14 and i!=4 or i==38;cb=134569997 if i==4 else m.m.FIELD
        need(o['map']==where and o['xy']==xy and o['live_xy']==([0,0]if i==4 else[v+7 for v in xy])and o['facing']==face,'入口transition/通常8歩の位置・向き')
        need(o['callback2']==cb and o['field']is field and o['lock']==int(14<=i<38),'入館/暗所field/menu/保存境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0,'新戦闘0/RP0/party4')
        need(o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER,'全party/RAM台帳保持')
        need(o['save_counter']==(55 if i<34 else 56),'34counterは保存中、35成功')
        wanted=m.a.FLASH if i<21 else FLASH_PHASES[i-21]if i<35 else FLASH
        need(o['flash_sha256']==wanted,'32/33最終hash似でも34で再変化。35成功まで完了にしない')
    need(FLASH_PHASES[11]==FLASH_PHASES[12]==FLASH and FLASH_PHASES[13]!=FLASH,'hash一致だけでは保存完了としない実例')
    for o in bo:
        m.idle(o,56);need(o['map']==[1,59]and o['xy']==[20,25]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continueの全field状態')
    return dict(status='PASS_HEART_MANSION_ENTRY_SAVE56_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=56,map=[1,59],map_name_ja='こころのやかた・入口階',xy=[20,25],facing=2,party_count=4,rp=0,travel_steps=10,town_steps=2,interior_steps=8,turns=2,entry_warps=1,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,next_warp=dict(xy=[20,24],target_map=[1,60],target_warp=5),darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,14],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=True,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=34,counter_change_not_save_completion=True,final_looking_hash_observations=[32,33],subsequent_transient_flash_observation=34,stable_hash_not_save_completion=True,save_success_text_observation=35,save_success_wording_observed=True,stable_field_observation=38,progress_inputs=70,continue_inputs=13,screen_count=41,native_processes=2,prior_failed_native_processes=1,total_new_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy flags')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&1<<j]
    need(d==[(2056,0,1),(2221,0,1)],'館初入館の2flagだけ。2056runtime owner未解明');return d

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save55/56と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,55,s.LAYOUT);new,rb=s.bank(after,0,56,s.LAYOUT);_,rc=s.bank(after,0xe000,55,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save55全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[15,10,15,14]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==17904,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,16,25),(0x4022,0,4),(0x404d,21,44)],'aux3変数。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    prep=json.loads((ROOT/m.PREP).read_bytes());need(any(ref['category']=='fly_flag'and ref['value']==2221 and ref['instruction_address']==142978050 for ref in prep['graph']['references']),'新2221flagと館map3 script setworldmapflagを照合')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6874,1708),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[15,10,15,14],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,mansion_flag2221_owner_resolved=True,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==41,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][38]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'通常入館10歩/戦闘0')
    need(measured['frontier']==dict(kind='unread_floor_boundary',map=[1,59],xy=[20,25],next_warp=dict(id=8,xy=[20,24],elevation=3,target_warp=5,target_map=[1,60]),observation=13),'未読階層の手前保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+14:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0038.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'暗い館の可視範囲/人物を含む全field画面がcold120frame後も同じ')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['interior_route']==m.INTERIOR_ROUTE and inspection['native_route_accepted']is False,'静的と実到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    prior=json.loads((folder/'prior-entry-failure.json').read_bytes());need(prior['artifact_id']==11285040773 and prior['execution']['observations']==6 and prior['execution']['native_end']['inputs']==21 and prior['execution']['final_save']==m.a.OUTPUT,'未保存入口失敗を保持')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
