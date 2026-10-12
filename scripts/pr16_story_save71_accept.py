#!/usr/bin/env python3
"""上階南側14歩と野生バーニン新1勝のSave71原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save71_measure as m
from pr16_story_after_maori import need,identity
SOURCE='deed3d77e27ed77136e4d34ffd355304ddc0953c'
RUN,JOB,ARTIFACT=37166304017,111329784622,11289573274
ARCHIVE=dict(size=154287,sha256='661336664f67be87322885ef11e015b433664c875ffdc9dffee746dbd51a6c62')
OUTPUT={'size': 131088, 'sha256': '87f67074b6d470df8260e15d2bd58566f949a6297318a1e7a9ee3d9b80cbb6fd'}
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='e25689466f7cd3ccf8a949853c06d4ee4e5acdec3be414a47a9383fd0db3bdb0'
LEDGER='7db04a6f1f9a485025a6ab8122e21b7b697d5ce286258eb80454067113f37af0';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save71_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE71_JA.md'
EVIDENCE='content/modernization/pr16_story_save71_evidence'
VISUAL='content/modernization/pr16_story_save71_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[33, 29], [34, 29], [34, 30], [34, 31], [33, 31], [32, 31], [31, 31], [30, 31], [29, 31], [28, 31], [27, 31], [26, 31], [25, 31], [24, 31], [23, 31]]
FLASH_PHASES=['a0e4ee98cde2e534fa2258dcc00a49f1ba2c821f6366ff5468740a3759e2f497', 'e24d08bc293a1edb18d1de9d5fafde2368e2dc2527cb7e27cd9503072307cd69', '8c122827f7b9a9e43b7695ae316710bcab27e000807ee45c2d6b8ee66ff235b2', '0a2fb65f8d0b1e07eb5e070181428ecbc8602fddb2ee44ceb7af160baf6ec1ab', '6390fc12d4868c775185d3887ed313a6fe559034a86f3e4092c8c2945ef3d500', '2cd125284641fb76de032316ce86a96846f69897534666150e0aba6008d72921', 'acd61b789b61dc6ed905606aff673ff9de2a60cbd938e95416ed95c0e6017ca2', 'c3c6e1b4fb8946084db6c79bcea2a230cddfeb52869da2339faa2bf6515bcb55', '5a4eedff9f5287f66b4caf1326048f8f9e1906eb207923dec6bf43f76084f8c6', '8bc3d9879e7d54984163ebb515ff066e8aec406a6a081bd8814898319aa69601', '98f571c531ac9756840aa9ce8b81df03fe46e1144880868ad8b627884cab7579', 'e25689466f7cd3ccf8a949853c06d4ee4e5acdec3be414a47a9383fd0db3bdb0', 'c550b545cfb824a68c7e40cc2b60682262c5fc5697180fc1c99c219da251052c']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=(folder.name=='progress' and v['screen']==17))
    return parsed
def motion(i):
    if i==0:return [33,29],4
    if i==1:return [34,29],4
    if i<=4:return [34,29 if i==2 else i+27],1
    return [34 if i==5 else 39-i if i<=16 else 23,31],3

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==51 and len(bo)==2,'全53画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(93,4706)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間93/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.TRANSITION if i==16 else 134282949 if i==17 else m.m.BATTLE if 18<=i<=24 else m.m.FIELD
        need(o['map']==[1,60]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'上階南側14歩/方向転換2/野生戦境界')
        need(o['callback2']==cb and o['field']is(i<16)and o['lock']==int(16<=i<=24 or 26<=i<=49),'field wire falseの勝利残留を非復帰扱いしない。callback/lock/実画面で確認')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(4 if i>=17 else 0)and o['battle_outcome']==int(i>=25),'wild新1勝だけ。残留を追加勝利にしない')
        need(o['party_sha256']==(m.a.PARTY if i<23 else PARTY)and o['ledger_sha256']==LEDGER==m.a.LEDGER,'実PP1消費。全RAM台帳は同一')
        need(o['save_counter']==(70 if i<45 else 71),'45counterは保存中、46成功')
        wanted=m.a.FLASH if i<33 else FLASH_PHASES[i-33]if i<46 else FLASH
        need(o['flash_sha256']==wanted,'44が最終hashと一致しても保存中。45部分writeへ戻り46成功')
    need(FLASH_PHASES[11]==FLASH and FLASH_PHASES[12]!=FLASH,'最終hashの先行一致44とcounter71の45は完了ではない')
    for o in bo:
        m.idle(o,71);need(o['map']==[1,60]and o['xy']==[23,31]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態。勝利残留reset')
    return dict(status='PASS_MANSION_UPPER_SOUTH_WILD_SAVE71_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,ordinary_saves=1,save_counter=71,map=[1,60],map_name_ja='こころのやかた・上階',xy=[23,31],facing=3,party_count=4,rp=0,travel_steps=14,turns=2,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,southeast_stair_previously_accepted=True,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],wild_name_ja='バーニン',wild_level=13,observed_move_uses=[1,0,0,0],observed_pp_consumption=[1,0,0,0],move_commands=1,target_confirmations=0,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=True,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=45,counter_change_not_save_completion=True,partial_write_observations=list(range(33,46)),early_final_hash_while_saving_observation=44,stable_hash_not_alone_save_completion=True,save_success_text_observation=46,save_success_wording_observed=True,stable_field_observation=50,progress_inputs=93,continue_inputs=13,screen_count=53,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True,transient_black_frame_observation=17,post_battle_field_wire_false_with_field_callback=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(52,10,9)],'実slot0 PP1消費だけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[52]=9;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d

def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'全legacy flag保持。野生戦をtrainer bitへ誤計上しない');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save70/71と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,70,s.LAYOUT);new,rb=s.bank(after,0xe000,71,s.LAYOUT);_,rc=s.bank(after,0,70,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save70全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,29,43),(0x4022,4,0)],'aux2変数だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6877,1684),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=599,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==53,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][50]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['southeast_stair_observed']is False and measured['hole_descent_observed']is False and measured['paper_side_reached']is False,'上階新14歩。紙側11歩残り/旧階段再走0')
    need(measured['battle']==dict(start=18,finish=25,trainer=False,outcome=1,move_commands=[1,0,0,0],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=22,move_slot=0)]),'実wild1勝/技選択1/実PP1の区別')
    need(measured['frontier']==dict(kind='new_battle',trigger=[23,31],map=[1,60],xy=[23,31],observation=25),'最初の野生戦後すぐ通常保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+26:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    need(m.classify((folder/'progress/screen-0022.ppm').read_bytes())==('moves',0),'実ドラゴンクローUI cursor')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0025.ppm','progress/screen-0050.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2]==frames[3],'野生戦後と通常保存後とcold暗所field全byte一致')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['target']==[16,27]and inspection['statue']==[16,28],'25歩静的計画と14歩での野生戦割込みを分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    route=m.ROUTE[m.ROUTE.index([23,31]):]
    need(len(route)==12 and route[-1]==[16,27],'上階南側残り未通過11歩だけ')
    upper=json.loads((ROOT/m.PREP).read_bytes());cells={tuple(x['xy']):x for x in upper['terrain']}
    for xy in route:
        c=cells[tuple(xy)];need((c['collision'],c['elevation'],c['behavior'])==(0,3,8),'保存済通常床だけ')
    for before,after in zip(route,route[1:]):m.direction(before,after)
    return dict(status='STATIC_UPPER_SOUTH_PAPER_APPROACH11_FROM_SAVE71_ONLY',map=[1,60],start=[23,31],target=[16,27],statue=[16,28],route=route,edges=11,native_route_accepted=False,southeast_stair_already_observed=True,paper_observed=False,new_rom_reads=0,new_terrain_cells=0)
