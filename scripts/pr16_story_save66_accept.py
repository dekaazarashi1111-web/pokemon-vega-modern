#!/usr/bin/env python3
"""NPC北迂回の新13歩と野生オタクン新1勝のSave66原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save66_measure as m
from pr16_story_after_maori import need,identity
SOURCE='0c826eac9f4385d5187a2e14a1825c5960ba1770'
RUN,JOB,ARTIFACT=37162621003,111319019754,11288387069
ARCHIVE=dict(size=163102,sha256='6318e2e6100c3cb116b01359ea206bf0cc7f683e9d1140977b41d24a6404e3ed')
OUTPUT={'size': 131088, 'sha256': '5c415ce0cac66346d10309f6ec7b783fade9cdfb5902a5bf2c19845c930d50a5'}
PARTY='ce607f99b8ba62726c28348c16112fc626dfb228766c573a3f29c90ca7bfc388'
FLASH='9ddb277c622222958361bfcdbc66fb9d68d880f0d9bba4ca3d7590d35d8372b0'
LEDGER='bfc76622a67b361a2b4ba9c00ca8c9fabf90a54c1921884a3fea43b07ec86990';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save66_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE66_JA.md'
EVIDENCE='content/modernization/pr16_story_save66_evidence'
VISUAL='content/modernization/pr16_story_save66_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[26, 6], [26, 5], [25, 5], [24, 5], [23, 5], [23, 6], [23, 7], [23, 8], [23, 9], [23, 10], [23, 11], [24, 11], [25, 11], [25, 12]]
FLASH_PHASES=['2a94847a07666d547be3e4ef18f3571e683cb596519a0be68d36f167865183ab', 'fa7c73e27be3d30a389b3a2c757a4275e524ac5396fc16e37c1345a576ac171e', 'b7775059ab19025ef69b728bb5fcdb8c37ba8246befa49d9c5bf82389246083e', 'c3c435fff58266af0137236d44f457d6b034eed6cff642d9832a093641c52aec', 'ca8442add023ffb0fb0df822e24cefedaac57b3fcf94f062fc8126dc8e183fe7', '87d9461a5c9945329cd0d9a4ad23a32dfcd811993b90f81b6251b5862f53703c', '4029bea3a5af718adfe3ba0217b7bbc65cf2f5c6498023e3cc8616ed6d436cb9', '6acf3b21830f2aa22a31cb4a003dd5a6595d6d0e43ce259164c4a243e131b4ec', '6aad39a1aa6922038e8168cbb1298d2da7be2761b0ca160a5f8b93f3e27caa73', '9b2544956ca322fc99c90280bc877d6e442616549f62cc573b267a314030c7d9', '4e5cb423ea8a8426830643cbab40bfebf5013a890f09284142da2c9f7205a947', '9ddb277c622222958361bfcdbc66fb9d68d880f0d9bba4ca3d7590d35d8372b0', '2b1646d2ee78a8ff6c7bf981d566f629203537d92d38510f8115a7e6f449ec94']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=(seed==m.a.OUTPUT and v['screen']==19))
    return parsed
MOTION=[([26, 6], 3), ([26, 6], 2), ([26, 5], 2), ([26, 5], 3), ([25, 5], 3), ([24, 5], 3), ([23, 5], 3), ([23, 5], 1), ([23, 6], 1), ([23, 7], 1), ([23, 8], 1), ([23, 9], 1), ([23, 10], 1), ([23, 11], 1), ([23, 11], 4), ([24, 11], 4), ([25, 11], 4), ([25, 11], 1), ([25, 12], 1)]
def motion(i):return MOTION[i]if i<len(MOTION)else ([25,12],1)

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==53 and len(bo)==2,'全55画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(97,4818)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間97/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.TRANSITION if i==18 else 134282949 if i==19 else m.m.BATTLE if 20<=i<=26 else m.m.FIELD
        need(o['map']==[1,60]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'NPCを北迂回する新13歩/転換5/最初の野生戦')
        need(o['callback2']==cb and o['field']is(i<18)and o['lock']==int(18<=i<27 or 28<=i<52),'通常復帰と勝利残留wire field=falseの区別')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(4 if i>=19 else 0)and o['battle_outcome']==int(i>=27),'野生1勝だけ。残留を追加勝利にしない')
        need(o['party_sha256']==(m.a.PARTY if i<25 else PARTY)and o['ledger_sha256']==LEDGER==m.a.LEDGER,'DragonClaw実PP1消費とRAM台帳保持')
        need(o['save_counter']==(65 if i<47 else 66),'47counterは保存中、48成功')
        wanted=m.a.FLASH if i<35 else FLASH_PHASES[i-35]if i<48 else FLASH
        need(o['flash_sha256']==wanted,'全13書込中snapshot。46hash最終値でも47へ再変化')
    need(len(set(FLASH_PHASES))==13 and FLASH_PHASES[11]==FLASH and FLASH_PHASES[12]!=FLASH,'46hash一致を保存完了にしない。47counter変更後も48成功文言まで待つ')
    for o in bo:
        m.idle(o,66);need(o['map']==[1,60]and o['xy']==[25,12]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_NORTH_DETOUR_WILD_SAVE66_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,ordinary_saves=1,save_counter=66,map=[1,60],map_name_ja='こころのやかた・上階',xy=[25,12],facing=1,party_count=4,rp=0,travel_steps=13,turns=5,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[14,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],wild_species_name_ja='オタクン',wild_level=10,wild_gender_ja='♂',observed_move_uses=[1,0,0,0],observed_pp_consumption=[1,0,0,0],move_commands=1,target_confirmations=0,move_commands_not_automatically_pp_uses=True,selected_move_ja='ドラゴンクロー',aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=True,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=47,counter_change_not_save_completion=True,partial_write_observations=list(range(35,48)),precompletion_final_hash_observation=46,stable_hash_not_alone_save_completion=True,save_success_text_observation=48,save_success_wording_observed=True,stable_field_observation=52,progress_inputs=97,continue_inputs=13,screen_count=55,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(52,15,14)],'実slot0 PP1消費だけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[52]=14;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags保持');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save65/66と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,65,s.LAYOUT);new,rb=s.bank(after,0,66,s.LAYOUT);_,rc=s.bank(after,0xe000,65,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save65全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[14,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19104,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,111,124)],'aux4021だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6860,1673),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=599,party_byte_deltas=pd,pp=[14,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==55,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][52]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True,'NPC北迂回新13歩だけ。穴未到達')
    need(measured['frontier']==dict(kind='new_battle',trigger=[25,12],map=[1,60],xy=[25,12],observation=27),'最初の上階野生1勝直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+28:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0052.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'上階/階段/暗所field全byte一致')
    need((folder/'progress/screen-0027.ppm').read_bytes()==frames[0],'野生戦直後/Save後/cold全field画像同一')
    need(measured['battle']==dict(start=20,finish=27,trainer=False,outcome=1,move_commands=[1,0,0,0],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=24,move_slot=0)])and measured['hole_descent_observed']is False,'選択1/実PP1、穴未到達')
    for i,slot in [(24,0)]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',slot),'技UI通常cursor')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['entry']['xy']==[31,21]and inspection['arrival']['xy']==[31,22],'28歩静的候補と実13歩/穴未到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    route=m.ROUTE[m.ROUTE.index([25,12]):]
    need(len(route)==16 and route[0]==[25,12]and route[-1]==[31,21],'同じ候補の未通過15歩接尾辞だけ')
    return dict(status='STATIC_UPPER_SUFFIX_FROM_SAVE66_ONLY',map=[1,60],start=[25,12],target=[31,21],route=route,edges=15,excluded_npc_xy=[25,6],native_route_accepted=False,hole_descent_observed=False,new_rom_reads=0,new_terrain_cells=0)
