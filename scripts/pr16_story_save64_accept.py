#!/usr/bin/env python3
"""上階の新14歩と野生バーニン新1勝のSave64原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save64_measure as m
from pr16_story_after_maori import need,identity
SOURCE='22b20697f6c99fad2884c32874138b65ab42e8c5'
RUN,JOB,ARTIFACT=37161289889,111315087287,11286858775
ARCHIVE=dict(size=165037,sha256='317a4664070804c7a70ce265418401c08ba67e282f47ddf208cece07cd977187')
OUTPUT={'size': 131088, 'sha256': '7cab241382223fc8ddbd2d659f8c29619c5b9b0ff5fd6d24e9269b4f366833d0'}
PARTY='bf61401033e3310a274cbc93075a1495b383eeef7cc6fee61cdbe8309357bab5'
FLASH='105d20a8c20d421c0f6def0cf6f60900751e99068189e684b2d94faf96ed4948'
LEDGER='83cfd306095082a9c7e787e4fd549b1072b4272e7a8169a3923f0e459d6d87d0';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save64_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE64_JA.md'
EVIDENCE='content/modernization/pr16_story_save64_evidence'
VISUAL='content/modernization/pr16_story_save64_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[32, 10], [33, 10], [34, 10], [34, 9], [34, 8], [34, 7], [34, 6], [33, 6], [32, 6], [31, 6], [30, 6], [29, 6], [28, 6], [27, 6], [26, 6]]
FLASH_PHASES=['ce65db7cbc633434865b7e156ceaeee2526ea6358459804fe126db3b6798eec6', '59503c8ef5c8bc8c2ba490c197ff9762a9eb415d2a018e8d913b9a64c39b0457', 'c886ed6cde98d052cb26afe53b21cc6132facff44559d1f54522a8fe158bd8eb', 'c9020dd5db4e78722118ff072577e23bd2df595d35f07118c494687410020d31', '501aa7c5f3b0e86bb8ce803160145b045732cff49202e4dcfd5d8fbe8cec42f8', 'cf39b5a8d5c6aed6c28f02c865bd4c99f21faa13dec2e06ee8844ec60bc9272c', '6f454c52e716c84743d8c2bd77fdcf195219158104be17cad8863414e6324ef0', '58720587d2704cb20367f6f0d57ce59358ea56a21acc231e0882ad7e3194b734', '72be475fa65d87da34cbb5f616d5793d343fe8fd47a6a6021b5f7f978939b339', '467308bb76e4464ec2ac483594ec10a246e1237dee711befcabd7910f758504b', '789ccd2466bf7acbebd6077841ad8c6fdbab4c1a4eba60e0634285d03a43899d', '93c95840b86720d7ea17c9a380b6d9691bf923b647defe5ca374a9e3537eea87', '5d68fd6954fd0ecbb112ddc4a4042376946a69b7638d8b9797cdaec09995aa6a']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=(seed==m.a.OUTPUT and v['screen']==17))
    return parsed
def motion(i):
    if i<=2:return [32+i,10],4
    if i<=7:return [34,10 if i==3 else 13-i],2
    if i<=16:return [34 if i==8 else 42-i,6],3
    return [26,6],3

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==52 and len(bo)==2,'全54画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(95,4550)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間95/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.TRANSITION if i==16 else 134282949 if i==17 else m.m.BATTLE if 18<=i<=25 else m.m.FIELD
        need(o['map']==[1,60]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'上階新14歩/方向転換2/初野生戦の位置・向き')
        need(o['callback2']==cb and o['field']is(i<16)and o['lock']==int(16<=i<26 or 27<=i<51),'野生戦後のfield callback復帰と勝利残留wire falseを区別')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(4 if i>=17 else 0)and o['battle_outcome']==int(i>=26),'野生1勝だけ。残留を追加勝利にしない')
        need(o['party_sha256']==(m.a.PARTY if i<25 else PARTY)and o['ledger_sha256']==LEDGER==m.a.LEDGER,'実PP1消費/RAM台帳不変')
        need(o['save_counter']==(63 if i<46 else 64),'46counterは保存中、47成功')
        wanted=m.a.FLASH if i<34 else FLASH_PHASES[i-34]if i<47 else FLASH
        need(o['flash_sha256']==wanted,'全13部分write/47最終Flashを区別')
    need(len(set(FLASH_PHASES))==13 and FLASH not in FLASH_PHASES,'counter64の46も部分write')
    for o in bo:
        m.idle(o,64);need(o['map']==[1,60]and o['xy']==[26,6]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_UPPER_WILD_SAVE64_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,ordinary_saves=1,save_counter=64,map=[1,60],map_name_ja='こころのやかた・上階',xy=[26,6],facing=3,party_count=4,rp=0,travel_steps=14,turns=2,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,5],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],wild_species_name_ja='バーニン',wild_level=11,wild_gender_ja='♂',observed_move_uses=[0,0,0,1],observed_pp_consumption=[0,0,0,1],move_commands=1,target_confirmations=0,move_commands_not_automatically_pp_uses=True,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=True,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=46,counter_change_not_save_completion=True,partial_write_observations=list(range(34,47)),stable_hash_not_alone_save_completion=True,save_success_text_observation=47,save_success_wording_observed=True,stable_field_observation=51,progress_inputs=95,continue_inputs=13,screen_count=54,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(55,6,5)],'実slot3 PP1消費だけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[55]=5;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags保持');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save63/64と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,63,s.LAYOUT);new,rb=s.bank(after,0,64,s.LAYOUT);_,rc=s.bank(after,0xe000,63,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save63全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[15,10,15,5]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==18744,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,97,111),(0x4022,3,0)],'aux2変数。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6899,1681),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=599,party_byte_deltas=pd,pp=[15,10,15,5],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==54,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][51]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True,'上階新14歩だけ。穴未到達')
    need(measured['frontier']==dict(kind='new_battle',trigger=[26,6],map=[1,60],xy=[26,6],observation=26),'最初の上階野生1勝直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+27:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0051.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'上階/階段/暗所field全byte一致')
    need((folder/'progress/screen-0026.ppm').read_bytes()==frames[0],'野生戦直後/Save後/cold全field画像同一')
    need(measured['battle']==dict(start=18,finish=26,trainer=False,outcome=1,move_commands=[0,0,0,1],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=24,move_slot=3)])and measured['hole_descent_observed']is False,'選択1/実PP1、穴未到達')
    for i,slot in [(22,0),(23,2),(24,3)]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',slot),'技UI通常cursor')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['entry']['xy']==[31,21]and inspection['arrival']['xy']==[31,22],'40歩静的候補と実14歩/穴未到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_neighbor():
    p=json.loads((ROOT/'content/modernization/pr16_story_save57_preparation.json').read_bytes())
    o=next(x for x in p['interior']['objects']if x['local_id']==7)
    need(o==dict(local_id=7,xy=[25,6],script=154587024,flag=0),'上階west隣接の保存済static object')
    i=next(x for x in p['instructions']if x['address']==154587024)
    need(i['hex']=='5c009b000000549869086c986908','trainerbattle155の既読ROM命令')
    return dict(status='STATIC_ADJACENT_TRAINER155_CANDIDATE_NOT_NATIVE_ID',map=[1,60],player_xy=[26,6],facing=3,object=o,instruction=i,trainer_id=155,next_ordinary_input='A once, then stop at the first new event or battle and save',runtime_identity_resolved=False,new_rom_reads=0)
