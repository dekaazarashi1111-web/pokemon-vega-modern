#!/usr/bin/env python3
"""入口階の新11歩とトレーナー165新1勝のSave69原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save69_measure as m
from pr16_story_after_maori import need,identity
SOURCE='33a239e90364383b14f2e46e3aedd21f93251514'
RUN,JOB,ARTIFACT=37164698519,111325123208,11289196478
ARCHIVE=dict(size=235373,sha256='7cedd812a27304dd26452aa508912d69192a845a940673cabae8fc86e2f7356f')
OUTPUT={'size': 131088, 'sha256': '9f17464ffd3b805b2d7b493298abbc1830b905b1cf0cef009feb5aa19e3c64a2'}
PARTY='e27e2261c383575dbbf7516bd46fa6f74c5c050be4c73d4b2a68c672c461f646'
FLASH='724a2154fa81b396ed17544d0a22e35ba794a2af851916f3ddf1b84dbfd51f75'
LEDGER='adb56ad9daf6dabdb059c94a1247bcef4ab57a7b7ff1e0b3358f64b3d66bf294';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save69_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE69_JA.md'
EVIDENCE='content/modernization/pr16_story_save69_evidence'
VISUAL='content/modernization/pr16_story_save69_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[31, 22], [30, 22], [29, 22], [28, 22], [27, 22], [26, 22], [26, 23], [26, 24], [26, 25], [26, 26], [26, 27], [26, 28]]
FLASH_PHASES=['f23bb466be3fa2afd56372ad31ea6fdd4785c3708f327363fe8517d324b13add', '993bc55279b1ed5439fe01cd2e5721e2bc4fd75f75778788d755871ca41f73bd', '07edcd12973cf11ccecc1e5511c7fdccce53f9a76ccb32b27b1ff2a7c196fd7c', '9113ee2ed2b56484c6c055fa17514afc06182586ec93c4001634d52d05b54bbe', 'df26f6e78b4f03c8f0570c42ec5cdcbf4c3143b27d751ff664885a9eece55f1f', 'c5a310e750ce5d72c28eb902d987056460cad33609c617b1ddfe3227902f7d22', '2d93907ed11234c6b693850bde230a78a57872407738a7d7245f050c5bd70a6a', 'd980bb227a27ffcb53dc12d75ca5b88c121042d68407b6b86bcae41985d2464d', '178d86723b91e96117380f3d4419ffc6d23b795b95ecfcac9ac6fa7bb4da6c67', 'aacc142d315b1c1ef54dc41c024955c6c649f4008ef2ce894a66003a49853c5f', '020d0a29bf57c547e735b3ac2ae22bf373da8676e9330aa954ad665926e7bdfd', '897275442c34e18d4ea6e71a4617fefd7280395bd8bfabb40fa79cb02633a672', '105e5531a87fbed21505466862b510b5c6fee0062195b9806aa4c342cd27b382']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
PARTIES=['4a89c06bcecc29825ff1e1c390d4ce15934fce1101ac71513ff385db7f64a82d', '55f1982fe205355fc09448dc61efcdf41d3488e6c81fdf4c6d088b53b73d29bf', '7383e9f759cb4b7703b97aca8c4ba32a62951793a4e242afafaba184d0256b87', 'e27e2261c383575dbbf7516bd46fa6f74c5c050be4c73d4b2a68c672c461f646']
TRANSIENT_LEDGER='8e3063a6892bc7cc742f68d8a546c344d8f758245584451be5168d61f64d3db3'
def motion(i):
    if i==0:return [31,22],1
    if i<=6:return [31 if i==1 else 32-i,22],3
    return [26,22 if i==7 else i+15 if i<=13 else 28],1

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==67 and len(bo)==2,'全69画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(127,8360)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間127/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.m.BATTLE if 15<=i<=40 else m.m.FIELD
        need(o['map']==[1,59]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'入口階新11歩/方向転換2/NPC接近/初trainer戦')
        need(o['callback2']==cb and o['field']is(i<13 or i in(41,66))and o['lock']==int(not(i<13 or i in(41,66))),'NPC台詞/新戦闘/通常field復帰/保存を分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(12 if i>=15 else 0)and o['battle_outcome']==int(i>=38),'trainer1勝だけ。敵3体/勝利残留を追加計上しない')
        party=PARTIES[0 if i<22 else 1 if i<29 else 2 if i<36 else 3]
        need(o['party_sha256']==party and o['ledger_sha256']==(m.a.LEDGER if i<5 else TRANSIENT_LEDGER if i<31 else LEDGER),'実PP3消費とRAM台帳5/31変化。owner未解明')
        need(o['save_counter']==(68 if i<61 else 69),'61counterは保存中、62成功')
        wanted=m.a.FLASH if i<49 else FLASH_PHASES[i-49]if i<62 else FLASH
        need(o['flash_sha256']==wanted,'全13部分write/62最終Flashを区別')
    need(len(set(FLASH_PHASES))==13 and FLASH not in FLASH_PHASES,'counter69の61も部分write')
    for o in bo:
        m.idle(o,69);need(o['map']==[1,59]and o['xy']==[26,28]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態。勝利残留はreset')
    return dict(status='PASS_MANSION_LOWER_TRAINER165_SAVE69_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=69,map=[1,59],map_name_ja='こころのやかた・入口階',xy=[26,28],facing=1,party_count=4,rp=0,travel_steps=11,turns=2,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,southeast_stair_observed=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[10,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],trainer_name_ja='リオン',trainer_class_ja='りかけいのおとこ',trainer_id=165,physical_trainer_bit=1445,trainer_party=[['ココガラ',10],['ビッパ',12],['ファマー',13]],reward_yen=312,observed_move_uses=[3,0,0,0],observed_pp_consumption=[3,0,0,0],move_commands=3,target_confirmations=0,keep_current_choices=2,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[5,31],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=61,counter_change_not_save_completion=True,partial_write_observations=list(range(49,62)),stable_hash_not_alone_save_completion=True,save_success_text_observation=62,save_success_wording_observed=True,stable_field_observation=66,progress_inputs=127,continue_inputs=13,screen_count=69,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,npc_south_adjacent_visible=True,cold_field_all_pixels_identical=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(52,13,10)],'実slot0 PP3消費だけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[52]=10;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d

def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(1445,0,1)],'trainer165物理bit1445だけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save68/69と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,68,s.LAYOUT);new,rb=s.bank(after,0xe000,69,s.LAYOUT);_,rc=s.bank(after,0,68,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save68全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    for pp,wanted in zip([13,12,11,10],PARTIES):
        copy=bytearray(x);copy[52]=pp;need(identity(bytes(copy))['sha256']==wanted,'保存byteから全3段階PPpartyを再構成。実saveへ書かない')
    remap=rom[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==s.TABLE_SHA,'固定trainer remap')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]));need(mapping.get(165+0x500,165+0x500)==1445,'trainer165→物理1445')
    need(rom[154587436-0x08000000:154587450-0x08000000].hex()=='5c00a5000000019869081a986908','既読map1/59 local10 trainerbattle165静的owner')
    need(list(y[52:56])==[10,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and(ma,mb)==(19104,19416),'全Bag保持と実賞金312円')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,10,20)],'aux4021だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6913,1702),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=599,party_byte_deltas=pd,pp=[10,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==69,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][66]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['southeast_stair_observed']is False and measured['hole_descent_observed']is False,'下階新11歩だけ。南東階段未到達/穴再走0')
    need(measured['battle']==dict(start=15,finish=41,trainer=True,outcome=1,move_commands=[3,0,0,0],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=21,move_slot=0),dict(observation=25,keep_current=True),dict(observation=28,move_slot=0),dict(observation=32,keep_current=True),dict(observation=35,move_slot=0)]),'選択3/交代拒否2/実PP3の区別')
    need(measured['frontier']==dict(kind='new_battle',trigger=[26,28],map=[1,59],xy=[26,28],observation=41),'最初の新trainer戦直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+42:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    for i in [21,28,35]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',0),'実ドラゴンクローUI cursor')
    for i in [25,32]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())[0]=='shift','実交代確認画面だけ取消')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0041.ppm','progress/screen-0066.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2]==frames[3],'NPC/人物/床の暗所field全byte一致')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['entry']['xy']==[30,29]and inspection['arrival']['xy']==[33,29],'静的16歩候補と実11歩でのtrainer割込みを分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    p=json.loads((ROOT/'content/modernization/pr16_story_save56_preparation.json').read_bytes());cells={tuple(x['xy']):x for x in p['terrain']}
    route=[[26,28],[25,28],[25,29],[25,30],[26,30],[27,30],[27,29],[28,29],[29,29],[30,29]]
    need(len(route)==10 and [26,29]not in route,'画面上の南隣NPCを回避する未通過9歩だけ')
    for xy in route:
        t=cells[tuple(xy)];need((t['collision'],t['elevation'],t['behavior'])==(0,3,108 if xy==[30,29]else 8),'保存済地形だけ')
    for before,after in zip(route,route[1:]):m.direction(before,after)
    npc=next(x for x in p['interior']['objects']if x['local_id']==10);node=next(x for x in p['instructions']if x['address']==154587436)
    need(npc==dict(local_id=10,xy=[26,31],script=154587436,flag=0)and node['hex']=='5c00a5000000019869081a986908','静的trainer165 owner。runtime object ID確定とは区別')
    return dict(status='STATIC_NPC_DETOUR_SOUTHEAST_FROM_SAVE69_ONLY',map=[1,59],start=[26,28],target=[30,29],route=route,edges=9,arrival_map=[1,60],arrival_xy=[33,29],arrival_auto_step_candidate=[34,29],paper_side_target=[1,60,16,27],npc_static_owner=npc,npc_instruction=node,npc_south_adjacent_visual_xy=[26,29],npc_runtime_identity_resolved=False,npc_visual_frame='continue/screen-0001.ppm',native_route_accepted=False,southeast_stair_observed=False,paper_observed=False,new_rom_reads=0,new_terrain_cells=0)
