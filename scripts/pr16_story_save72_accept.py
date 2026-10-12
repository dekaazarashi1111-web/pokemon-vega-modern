#!/usr/bin/env python3
"""上階南側残り11歩と紙像北隣初到着のSave72原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save72_measure as m
from pr16_story_after_maori import need,identity
SOURCE='bca05f1af107d3e479b869dae961402eb6c8ed0a'
RUN,JOB,ARTIFACT=37166930840,111331674186,11289800679
ARCHIVE=dict(size=134329,sha256='422cd5eae0908f59c33f0a113e510e04eec9ac9ac0fe6bc010dfb8a9e0bd2a43')
OUTPUT={'size': 131088, 'sha256': '851c87f8a8006eaecdcb6ea28ee9f097fbcab4ba0c7f5b626afb6edbec40fa49'}
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='6c93aedc4e46ab50e38d082843b12574186f2713e74cb9e8ea799e68c5ac3d67'
LEDGER='f652e630800f0b4c184ca57665b8ef265eac72072c3357a8705e65fb0729fe14';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save72_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE72_JA.md'
EVIDENCE='content/modernization/pr16_story_save72_evidence'
VISUAL='content/modernization/pr16_story_save72_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[23, 31], [22, 31], [21, 31], [20, 31], [19, 31], [18, 31], [17, 31], [17, 30], [17, 29], [17, 28], [17, 27], [16, 27]]
FLASH_PHASES=['d15002f290d0ede1915c3bfdc27b03a94e4c0b6a2f7aefe8715c2575a3bdd1e5', '83182afca1d19963e54e23a1d363f5c7b827a4165ff82f4e530bc22b0a38051c', '1062badd4523ae781f48980c6ca7379fe09e7ed59b75f27650fb1e258de58988', '8ba79dcf3d20be84f8ab399a4e17005b9091c6c6d3b76809ad100c757f0decd6', 'a3cb968f35d6d72983d735062e0f95e0d78bf1256e20310a2837a25f909b2a89', 'd4be2372f6bca53639bd94eacb89e4249ab23261cdf910058e142d1f73c21066', 'f1d530918ffc6c879c06e66bb17c6df5f7a66371261194de22fc4b103d228788', 'da748e95e56b4bd356b8403fb4b88ef360d8303d7bf9e8a60139aeeeeabcab0f', 'd23001eb04e6ac1562628eaf9858737b71abbb52ef6aaccc746f650dd9e232fa', '5305e0e819a36b4e9cbd7ffad9bb1b301500d752651873e6762b3f139d074159', '63ba9a7241e1b3e245fee542f188e3740fa6ffb27c65c380ac013e886f091113', '73a1e25a7d094e9448b7de975e999216bae29cbeb9417aeeee3837cd9fd6785c', 'eed1ac16eefb3547d675f9b6f73b0a964b84a06129e2e986933f90c9968f8345', 'a50774e4e09b10d65800fd61fc55fc5faaad6f1fc391da7431f87a78b55f0e5c', '28eeb3d56b0f6c73a9faa4144368d999a9b457e44833a775843a03f6a523d7a8']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
def motion(i):
    if i<=6:return [23-i,31],3
    if i<=11:return [17,31 if i==7 else 38-i],2
    return [17 if i==12 else 16,27],3

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==41 and len(bo)==2,'全43画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(73,3144)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新11歩73/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i)
        need(o['map']==[1,60]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'上階南側残り11歩/転換2/像の北隣16,27西')
        need(o['callback2']==m.m.FIELD and o['field']is(i<=13 or i==40)and o['lock']==int(14<=i<=39),'像北隣到着/通常保存/安定fieldを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==(m.a.LEDGER if i<10 else LEDGER),'全party600byte/HP/PP保持。RAM台帳10変化のowner未解明')
        need(o['save_counter']==(71 if i<35 else 72),'35counterは保存中、36成功')
        wanted=m.a.FLASH if i<21 else FLASH_PHASES[i-21]if i<36 else FLASH
        need(o['flash_sha256']==wanted,'全15部分write/36最終Flashを区別')
    need(len(set(FLASH_PHASES))==15 and FLASH not in FLASH_PHASES,'counter72の35も部分write')
    for o in bo:
        m.idle(o,72);need(o['map']==[1,60]and o['xy']==[16,27]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_PAPER_SIDE_SAVE72_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=72,map=[1,60],map_name_ja='こころのやかた・上階',xy=[16,27],facing=3,party_count=4,rp=0,travel_steps=11,turns=2,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,paper_side_reached=True,statue_visual_observed=True,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[10],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=35,counter_change_not_save_completion=True,partial_write_observations=list(range(21,36)),stable_hash_not_alone_save_completion=True,save_success_text_observation=36,save_success_wording_observed=True,stable_field_observation=40,progress_inputs=73,continue_inputs=13,screen_count=43,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'全legacy flag保持');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save71/72と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,71,s.LAYOUT);new,rb=s.bank(after,0,72,s.LAYOUT);_,rc=s.bank(after,0xe000,71,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save71全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,43,54),(0x4022,0,1)],'aux2変数だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6843,1666),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==43,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][40]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['battle']is None,'上階新11歩。新戦闘0')
    need(measured['frontier']==dict(kind='new_paper_side_arrival',map=[1,60],xy=[16,27],observation=13),'像北隣初到着直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+14:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0013.ppm','progress/screen-0040.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2]==frames[3],'像/主人公/暗所field全byte一致')
    need(measured['paper_side_reached']is True and measured['statue_paper_observed']is False and measured['southeast_stair_observed']is False and measured['hole_descent_observed']is False,'像側到着と紙の未取得を分離')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['target']==[16,27]and inspection['statue']==[16,28],'保存済未通過11歩と通常移動を照合')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    upper=json.loads((ROOT/m.PREP).read_bytes());bg=next(x for x in upper['bgs']if x['xy']==[16,28]);need(bg==dict(map=[1,60],index=0,xy=[16,28],elevation=0,kind=0,value=149012422),'保存済像background owner')
    instructions={i['address']:i for i in upper['instructions']}
    expected={149012431:'210c800100',149012452:'2b1f11',149012461:'4612010100',149012477:'4412010100',149012505:'291f11'}
    for address,raw in expected.items():need(instructions[address]['hex']==raw,'向き比較/flag4383/checkspace274/additem274/setflag4383の保存済命令')
    return dict(status='STATIC_STATUE_INTERACTION_FROM_SAVE72_ONLY',map=[1,60],start=[16,27],facing=3,statue=[16,28],route=[[16,27]],edges=0,turn_direction='south',turn_key=128,target_facing=1,interact_key=1,background=bg,script=149012422,conditional_variable=32780,conditional_value=1,item_id=274,item_quantity=1,expanded_flag=4383,instruction_evidence={str(k):instructions[k]for k in expected},native_route_accepted=False,paper_observed=False,item_obtained=False,new_rom_reads=0,new_terrain_cells=0)
