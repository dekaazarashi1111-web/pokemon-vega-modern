#!/usr/bin/env python3
"""上階穴への新1歩と通常落下のSave68原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save68_measure as m
from pr16_story_after_maori import need,identity
SOURCE='765a16442d7cbac2223e5c4913c31cd90da3b574'
RUN,JOB,ARTIFACT=37163733877,111322303638,11287919858
ARCHIVE=dict(size=109087,sha256='443d3cb41be7f3773e9fea0ac3f33813b57b1847ccde1bd912ec3bac351156e4')
OUTPUT={'size': 131088, 'sha256': 'f54e7eca96b2808752f7c5c3e6701cca162b569ab16394b50307717b58ec868e'}
PARTY='4a89c06bcecc29825ff1e1c390d4ce15934fce1101ac71513ff385db7f64a82d'
FLASH='67706c57f0826987c6fb18b0722f1b4661665a4e38ab0d517b7bce1dc0647ea6'
LEDGER='14b4dff184e6a5234a8341543ae33cdb3ae7cf2ff1be93c707d3a278aca4b242';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save68_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE68_JA.md'
EVIDENCE='content/modernization/pr16_story_save68_evidence'
VISUAL='content/modernization/pr16_story_save68_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[31, 20], [31, 22]]
FLASH_PHASES=['8ee218f175ec6546177fa8cc3918ea4fa62d2d1588b25df5c2c1d69d218c6f24', '6bc84e9aba1ab2d4245015f21883fda10ea866e2a30f3ef7eab69e882e32a031', '3af65ad23e1a9780d04085e9eea06642f10107677b15523163961db529471ee3', '4ef1550ac9efa961429c6f88b58652a65a29aff38be58f1446f3cd0ddc0dc1ee', '65333e346fd9d13240378d47c5b0f290be44b1e6196f61875c9030891f6eb6f4', '2aa7a1ca26a84a7012f729a83078aad3a0dba301ae8044aa95c4759cd96da67f', '9dd8c9ca891ce95657cb9067e43abd4024aad5c95193646a9e5256e2213bfd96', 'bdfbdeccd07397a3df889c056b2a66bb7e81cf3a2407ca8bde1d11832ef6cfd7', 'd64580a3899e389169228d71b9c092b66066f43486e8b4a46abd051b50686f98', '9645d14d60e9309bffd2db45a20f4991c2fef247ed11c579d034f902a31cfe53', '244e790698a042a53ec823e17b628f300fbcd1f70aa12cb8375e6c758dab4e09', '67706c57f0826987c6fb18b0722f1b4661665a4e38ab0d517b7bce1dc0647ea6', '804965aaa0fb66173ceeaff232b7c32f324b9f122571261d32b3d744d13c1fb2']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
def motion(i):return ([1,60],[31,20])if i==0 else ([1,60],[31,21])if i==1 else ([1,59],[31,22])

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==27 and len(bo)==2,'全29画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(47,2562)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新落下47/cold13入力だけ')
    for i,o in enumerate(ao):
        where,xy=motion(i)
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==1,'上階穴へ南1歩→入口階31,22の実落下')
        need(o['callback2']==m.m.FIELD and o['field']is(i in(0,2,26))and o['lock']==int(i not in(0,2,26)),'落下lock/到着/通常保存/安定fieldを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.LEDGER,'全party600byte/全RAM台帳保持')
        need(o['save_counter']==(67 if i<22 else 68),'22counterは保存中、23成功')
        wanted=m.a.FLASH if i<10 else FLASH_PHASES[i-10]if i<23 else FLASH
        need(o['flash_sha256']==wanted,'21一時最終hash/22部分write/23最終Flashを区別')
    need(len(set(FLASH_PHASES))==13 and FLASH_PHASES[-2]==FLASH and FLASH_PHASES[-1]!=FLASH,'21hash一致は保存完了ではない')
    for o in bo:
        m.idle(o,68);need(o['map']==[1,59]and o['xy']==[31,22]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_HOLE_DESCENT_SAVE68_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=68,map=[1,59],map_name_ja='こころのやかた・入口階',xy=[31,22],facing=1,party_count=4,rp=0,travel_steps=1,turns=0,entry_warps=1,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=True,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[13,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=True,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=22,counter_change_not_save_completion=True,partial_write_observations=list(range(10,23)),precompletion_final_hash_observation=21,stable_hash_not_alone_save_completion=True,save_success_text_observation=23,save_success_wording_observed=True,stable_field_observation=26,progress_inputs=47,continue_inputs=13,screen_count=29,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True,arrival_banner_present=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,0,1)],'下階落下に伴うphysical2056だけ。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save67/68と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,67,s.LAYOUT);new,rb=s.bank(after,0,68,s.LAYOUT);_,rc=s.bank(after,0xe000,67,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save67全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[13,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19104,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[],'全legacy variables保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6868,1677),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[13,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==29,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][26]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True and measured['battle']is None,'新1歩と通常穴落下。新戦闘0')
    need(measured['frontier']==dict(kind='new_hole_descent',map=[1,59],xy=[31,22],observation=2),'最初の穴落下直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+3:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0026.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'上階/階段/暗所field全byte一致')
    need((folder/'progress/screen-0002.ppm').read_bytes()!=frames[0],'到着2はmap名bannerあり。最終画面と同一とは主張しない')
    need(measured['hole_descent_observed']is True,'穴behavior102の通常落下を初実測')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['entry']['xy']==[31,21]and inspection['arrival']['xy']==[31,22],'静的穴ownerと通常落下を照合')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    p=json.loads((ROOT/'content/modernization/pr16_story_save62_evidence/route-plan.json').read_bytes());full=p['route'];first=full.index([59,31,22]);last=full.index([59,30,29]);route=[v[1:]for v in full[first:last+1]]
    need(len(route)==17 and full[last+1]==[60,33,29],'保存済下階16歩と南東階段だけ。紙まで接続は未実測')
    return dict(status='STATIC_LOWER_SOUTHEAST_STAIR_FROM_SAVE68_ONLY',map=[1,59],start=[31,22],target=[30,29],route=route,edges=16,arrival_map=[1,60],arrival_xy=[33,29],paper_side_target=[1,60,16,27],native_route_accepted=False,southeast_stair_observed=False,paper_observed=False,new_rom_reads=0,new_terrain_cells=0)
