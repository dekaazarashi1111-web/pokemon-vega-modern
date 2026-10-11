#!/usr/bin/env python3
"""上階りかけい155新1勝のSave65原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save65_measure as m
from pr16_story_after_maori import need,identity
SOURCE='edc783a132db676ca3ddda135b6cc570e1340a20'
RUN,JOB,ARTIFACT=37161669046,111316205366,11287846702
ARCHIVE=dict(size=220212,sha256='3ff9d889180cded9202f5e1cfda7cff67a571bb7cc5577de135440cf9a419915')
OUTPUT={'size': 131088, 'sha256': 'c3d67760ba4c452c48abddbf423ea9bd5a052e38227fee85e47e299a60a45dda'}
PARTY='7ab89e79a8082b624a45cedab488c92da9b79bcad5e0b22d97e5349dfe430ea3'
FLASH='6263a67ba3f40840228166c5f61b8de30430c02ec383b0aee716628e04dc058f'
LEDGER='bfc76622a67b361a2b4ba9c00ca8c9fabf90a54c1921884a3fea43b07ec86990';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save65_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE65_JA.md'
EVIDENCE='content/modernization/pr16_story_save65_evidence'
VISUAL='content/modernization/pr16_story_save65_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[26, 6], [26, 6]]
FLASH_PHASES=['1787f6f4ed55bb0840edcb1d784d089264f83d66f40f33efce89aaee148c4956', '3b52baf5f115813d139d4f3e8ffd693a1a1d21f65e29aad2e87f64f0563d799d', '8fbd866363e20996a8eb4501e967af25ebac45a6b35dbcaddb7028930098077f', '4c7f33c83dfecdeaf3e6b7b47bd54f816ef8470d83eba19b56dfbc2b49677029', 'bd5473443fda8dab916b7eb4c4b29ce352865232c6556f18dace6b0af1360125', '81d0694df26ac29d9c5dd01abd524c9bae7766e4e2f1c3c0c057d36db9f0ee67', '549c965e2a2efc69960a5545f4ea9bacc812721833c5603f7fcd879b4adf8e5f', '41e5f7454d0d491022fb12fedf3f54e690d39c9b2f3cd353a20f7589e9a42ac1', '227ae6b31d9f10999cfedf48a2efa9c492c6aecc44ca737ac4141ef4a08c2de6', 'e63c434076eeeb35c209d5d11542ab387154c0984b3bfd27d6f1236bd9fe94c1', 'c934f4f142588e5b327dedfb9b2f2f6cbb1f4baf645111835007f10f98148381', '59f470ee6cfeab3c660b6205fc2f3a60b701ae9c71cad87fc6f38895a9624843', '9e6e945ea75c95bff3d94f90afad6cbe056d4362510ec8cd46b9ff0d2e2b268f']
PARTIES=['bf61401033e3310a274cbc93075a1495b383eeef7cc6fee61cdbe8309357bab5', '359426669811831ea339855facfbabb4cd4eea1d9be022b0c9cd226e971faa68', '413c41baee9f8fcc859ad1b4a061b415a0b8cdd64af239fa0a6767a8d6538fa2', '7ab89e79a8082b624a45cedab488c92da9b79bcad5e0b22d97e5349dfe430ea3']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
TRANSIENT_LEDGER='e729b1ba5f9862d11cd7c40de2907bb3dd1def1bb20901d0decaf3865f1291e5'
def motion(i):return [26,6],3

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==53 and len(bo)==2,'全55画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(99,6992)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新会話99/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.m.BATTLE if 2<=i<=26 else m.m.FIELD
        need(o['map']==[1,60]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'同位置/西向き、歩行0/隣接NPC会話')
        need(o['callback2']==cb and o['field']is(i in(0,27,52))and o['lock']==int(i not in(0,27,52)),'trainer台詞/新戦闘/通常field復帰/保存を分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(12 if i>=2 else 0)and o['battle_outcome']==int(i>=24),'trainer1勝だけ。敵3体/残留を追加勝利にしない')
        party=PARTIES[0 if i<10 else 1 if i<16 else 2 if i<22 else 3]
        need(o['party_sha256']==party and o['ledger_sha256']==(m.a.LEDGER if i<6 else TRANSIENT_LEDGER if i<27 else LEDGER),'実PP3消費とRAM台帳6/27変化')
        need(o['save_counter']==(64 if i<47 else 65),'47counterは保存中、48成功')
        wanted=m.a.FLASH if i<35 else FLASH_PHASES[i-35]if i<48 else FLASH
        need(o['flash_sha256']==wanted,'全13部分write/48最終Flashを区別')
    need(len(set(FLASH_PHASES))==13 and FLASH not in FLASH_PHASES,'counter65の観測47も部分write')
    for o in bo:
        m.idle(o,65);need(o['map']==[1,60]and o['xy']==[26,6]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_ADJACENT_TRAINER155_SAVE65_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=65,map=[1,60],map_name_ja='こころのやかた・上階',xy=[26,6],facing=3,party_count=4,rp=0,travel_steps=0,turns=0,initial_adjacent_a_inputs=1,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],trainer_name_ja='カケル',trainer_class_ja='りかけいのおとこ',trainer_id=155,physical_trainer_bit=1435,trainer_party=[['コイキング',12],['ウパー',14],['クヌギダマ',15]],reward_yen=360,observed_move_uses=[0,0,0,3],observed_pp_consumption=[0,0,0,3],move_commands=3,target_confirmations=0,keep_current_choices=2,move_commands_not_automatically_pp_uses=True,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[6,27],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=47,counter_change_not_save_completion=True,partial_write_observations=list(range(35,48)),stable_hash_not_alone_save_completion=True,save_success_text_observation=48,save_success_wording_observed=True,stable_field_observation=52,progress_inputs=99,continue_inputs=13,screen_count=55,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(55,5,2)],'実slot3 PP3消費だけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[55]=2;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    delta=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(delta==[(1435,0,1)],'trainer155物理bit1435だけ');return delta
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save64/65と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,64,s.LAYOUT);new,rb=s.bank(after,0xe000,65,s.LAYOUT);_,rc=s.bank(after,0,64,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save64全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    for pp,wanted in zip([5,4,3,2],PARTIES):
        copy=bytearray(x);copy[55]=pp;need(identity(bytes(copy))['sha256']==wanted,'保存byteから全3段階PPpartyを再構成。実saveへ書かない')
    remap=rom[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==s.TABLE_SHA,'固定trainer remap')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]));need(mapping.get(155+0x500,155+0x500)==1435,'trainer155→物理1435')
    need(rom[154587024-0x08000000:154587038-0x08000000].hex()=='5c009b000000549869086c986908','既読map1/60 local7 trainerbattle155静的owner')
    need(list(y[52:56])==[15,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and(ma,mb)==(18744,19104),'全Bag保持と実賞金360円')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[],'全legacy variables保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6856,1665),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=599,party_byte_deltas=pd,pp=[15,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==55,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][52]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True,'A1回会話/歩行0。上階/穴未到達')
    need(measured['battle']==dict(start=2,finish=27,trainer=True,outcome=1,move_commands=[0,0,0,3],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=9,move_slot=3),dict(observation=12,keep_current=True),dict(observation=15,move_slot=3),dict(observation=18,keep_current=True),dict(observation=21,move_slot=3)]),'選択3/交代拒否2/実PP3の区別')
    need(measured['frontier']==dict(kind='new_battle',trigger=[25,6],map=[1,60],xy=[26,6],observation=27),'最初の新trainer戦直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+28:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    for i,slot in [(7,0),(8,2),(9,3),(15,3),(21,3)]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',slot),'実技UI cursorだけ')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0027.ppm','progress/screen-0052.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2]==frames[3],'人物と床の暗所field全byte一致')
    need(measured['hole_descent_observed']is False,'穴未到達')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==[[26,6]]and inspection['native_route_accepted']is False and inspection['neighbor']['trainer_id']==155,'隣接NPC静的候補と実戦を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result



def next_route():
    """目の前のNPC占有tileを除いた静的未通過候補。実通行は別受入。"""
    from collections import deque
    p=json.loads((ROOT/'content/modernization/pr16_story_save57_preparation.json').read_bytes())
    nodes={tuple(c['xy']):c for c in p['terrain']if c['collision']==0 and c['elevation']==3}
    blocked=(25,6);start=(26,6);target=(31,21);q=deque([start]);prev={start:None}
    while q:
        x,y=q.popleft()
        for n in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
            if n in nodes and n!=blocked and n not in prev:prev[n]=(x,y);q.append(n)
    need(target in prev,'NPC占有tileを迂回する静的床候補')
    route=[];n=target
    while n is not None:route.append(list(n));n=prev[n]
    route.reverse();need(len(route)==29 and route[:6]==[[26,6],[26,5],[25,5],[24,5],[23,5],[23,6]],'新北迂回5歩から未通過上階接尾辞へ')
    need([25,6]not in route and nodes[target]['behavior']==102,'NPCのtileへ移動を強要せず未通過穴へ')
    return dict(status='STATIC_NPC_AVOIDING_UPPER_ROUTE_ONLY',map=[1,60],start=[26,6],target=[31,21],route=route,edges=28,excluded_npc_xy=[25,6],native_route_accepted=False,hole_descent_observed=False,new_rom_reads=0,new_terrain_cells=0)
