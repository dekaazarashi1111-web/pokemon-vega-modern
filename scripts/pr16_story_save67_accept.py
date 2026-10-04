#!/usr/bin/env python3
"""上階接尾辞の新14歩と野生オタクン新1勝のSave67原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save67_measure as m
from pr16_story_after_maori import need,identity
SOURCE='f184a49f8a736ed83f5b29d208dfb72db9e50e4b'
RUN,JOB,ARTIFACT=37163246411,111320883103,11288432849
ARCHIVE=dict(size=157034,sha256='12d05e3effff6ae123a73e4cc60c19e342ae454ea21be51a4a9e1df53c2bbb84')
OUTPUT={'size': 131088, 'sha256': 'a4543c8c8d1b47668159adc71a0aff60f2bcf58ac91139d50d6eb201bd9677f5'}
PARTY='4a89c06bcecc29825ff1e1c390d4ce15934fce1101ac71513ff385db7f64a82d'
FLASH='aa5b263d7d213e086843a8f8848e0492ab4daab7b8c074e67ac566c8b971c2c6'
LEDGER='14b4dff184e6a5234a8341543ae33cdb3ae7cf2ff1be93c707d3a278aca4b242';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save67_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE67_JA.md'
EVIDENCE='content/modernization/pr16_story_save67_evidence'
VISUAL='content/modernization/pr16_story_save67_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[25, 12], [25, 13], [25, 14], [25, 15], [25, 16], [26, 16], [27, 16], [28, 16], [29, 16], [30, 16], [31, 16], [31, 17], [31, 18], [31, 19], [31, 20]]
FLASH_PHASES=['9750f7427fc6c216b0d8cdc29672b035e90c523d1e30ab7c98ab63484233244d', '1cf47bf6f73fd13b0a6b53f16793fa11418e60a9972b2e21e54270ad8ee3e1b1', '63af3f00174d94f1b0489905473c2956e1b48993eb165a3cbd94815373990d73', 'f2b235e70d8d77269af2c494a415a581d760f7bc48a37a852a0cf2b0b2fc5827', '333509aa1be9a60179c1e0e64a7ac8781ed8f17cc102bb47b40bb59d1cb639ed', '772565f599d8f71ad7824904a0d440ee910e6147b1515927eee5554dc65de837', 'b1431ebef88e2628c83624d0c38bef73c123a1cf3932f5f77f419ac798d97cda', '3b28b9223dfd362883499df49da6ec9bc6a5880f463504c2011e210b25f2978d', 'e5203fb31e5291510db6bc06f7dfe5a468aa956432d38704f40e2ca05db7694f', 'c20c42e5324ce5acf5458f2df640d6d544509b4366efe304037d4e2e708b8eb4', 'a257b97298d10a2daf3acef12f7a32572ef2352a9547370a5e6bc818f87ca071', '4ec1d89ad734c09e0826480df0d7a350cff6745139c747c86fb55129b6a868b5', '6d1b0ed2729066ab34bde20baa150012b6fe9cc8f5e825456804fd96c9092dde']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=(seed==m.a.OUTPUT and v['screen']==17))
    return parsed
MOTION=[([25, 12], 1), ([25, 13], 1), ([25, 14], 1), ([25, 15], 1), ([25, 16], 1), ([25, 16], 4), ([26, 16], 4), ([27, 16], 4), ([28, 16], 4), ([29, 16], 4), ([30, 16], 4), ([31, 16], 4), ([31, 16], 1), ([31, 17], 1), ([31, 18], 1), ([31, 19], 1), ([31, 20], 1)]
STEP_PARTY='eb0630121a03878b16eaf22be7830c0abe598c048a6df2e07bcf8b42a0c33e1b'
def motion(i):return MOTION[i]if i<len(MOTION)else ([31,20],1)

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==51 and len(bo)==2,'全53画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(93,4706)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間93/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.TRANSITION if i==16 else 134282949 if i==17 else m.m.BATTLE if 18<=i<=24 else m.m.FIELD
        need(o['map']==[1,60]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'上階接尾辞の新14歩/転換2/穴手前の野生戦')
        need(o['callback2']==cb and o['field']is(i<16)and o['lock']==int(16<=i<25 or 26<=i<50),'通常復帰と勝利残留wire field=falseの区別')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(4 if i>=17 else 0)and o['battle_outcome']==int(i>=25),'野生1勝だけ。残留を追加勝利にしない')
        need(o['party_sha256']==(m.a.PARTY if i<4 else STEP_PARTY if i<23 else PARTY)and o['ledger_sha256']==(m.a.LEDGER if i<3 else LEDGER),'field観測4の各partyoffset41+1と実PP1、RAM観測3変化を分離')
        need(o['save_counter']==(66 if i<45 else 67),'45counterは保存中、46成功')
        wanted=m.a.FLASH if i<33 else FLASH_PHASES[i-33]if i<46 else FLASH
        need(o['flash_sha256']==wanted,'全13書込中snapshot/46最終Flash')
    need(len(set(FLASH_PHASES))==13 and FLASH not in FLASH_PHASES,'45counter67でも部分write、46成功文言まで待つ')
    for o in bo:
        m.idle(o,67);need(o['map']==[1,60]and o['xy']==[31,20]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_UPPER_HOLE_APPROACH_SAVE67_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,ordinary_saves=1,save_counter=67,map=[1,60],map_name_ja='こころのやかた・上階',xy=[31,20],facing=1,party_count=4,rp=0,travel_steps=14,turns=2,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=True,hole_descent_observed=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[13,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],wild_species_name_ja='オタクン',wild_level=9,wild_gender_ja='♂',observed_move_uses=[1,0,0,0],observed_pp_consumption=[1,0,0,0],move_commands=1,target_confirmations=0,move_commands_not_automatically_pp_uses=True,selected_move_ja='ドラゴンクロー',aerial_ace_pp_preserved=2,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[3],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=45,counter_change_not_save_completion=True,partial_write_observations=list(range(33,46)),stable_hash_not_alone_save_completion=True,save_success_text_observation=46,save_success_wording_observed=True,stable_field_observation=50,progress_inputs=93,continue_inputs=13,screen_count=53,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(41,44,45),(52,14,13),(141,9,10),(241,107,108),(341,60,61)],'実slot0PP1と4体offset41+1。offset41 runtime owner未解明')
    copy=bytearray(x)
    for offset in [41,141,241,341]:copy[offset]+=1
    need(identity(bytes(copy))['sha256']==STEP_PARTY,'観測4からの中間partyを保存byteで独立再構成')
    copy[52]=13;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'新party全byteを再構成、実saveへ書かない');return d
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags保持');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save66/67と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,66,s.LAYOUT);new,rb=s.bank(after,0xe000,67,s.LAYOUT);_,rc=s.bank(after,0,66,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save66全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[13,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19104,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,124,10)],'aux4021だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6866,1681),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=595,party_byte_deltas=pd,pp=[13,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==53,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][50]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is True,'上階接尾辞新14歩だけ。穴未到達')
    need(measured['frontier']==dict(kind='new_battle',trigger=[31,20],map=[1,60],xy=[31,20],observation=25),'最初の上階野生1勝直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+26:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0050.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'上階/階段/暗所field全byte一致')
    need((folder/'progress/screen-0025.ppm').read_bytes()==frames[0],'野生戦直後/Save後/cold全field画像同一')
    need(measured['battle']==dict(start=18,finish=25,trainer=False,outcome=1,move_commands=[1,0,0,0],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=22,move_slot=0)])and measured['hole_descent_observed']is False,'選択1/実PP1、穴未到達')
    for i,slot in [(22,0)]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',slot),'技UI通常cursor')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['entry']['xy']==[31,21]and inspection['arrival']['xy']==[31,22],'15歩静的候補と実14歩/穴未到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    route=m.ROUTE[m.ROUTE.index([31,20]):]
    need(route==[[31,20],[31,21]],'穴への未通過最終1歩だけ')
    return dict(status='STATIC_HOLE_FINAL_EDGE_FROM_SAVE67_ONLY',map=[1,60],start=[31,20],target=[31,21],route=route,edges=1,native_route_accepted=False,hole_descent_observed=False,new_rom_reads=0,new_terrain_cells=0)
