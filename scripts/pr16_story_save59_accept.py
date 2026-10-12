#!/usr/bin/env python3
"""館内新廊下のSave59原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save59_measure as m
from pr16_story_after_maori import need,identity
SOURCE='22dfe546decd1240c897e53c6dfd0cf49375cdeb'
RUN,JOB,ARTIFACT=37157167167,111302817017,11286447464
ARCHIVE=dict(size=162390,sha256='544fdb90fef62c95522d974ae0244be64a7d040b881c90ff1ec70e0e3e977b82')
OUTPUT=dict(size=131088,sha256='b1acf753876e54805a82c8f23aeacd0e9d69824da50c5f0d504720227f0f4552')
PARTY='67cb7176527d2cd35141b4a6a89b22f0ec135c79dd452e5cffef43db8de39f26'
FLASH='3c1e0ebbf78f42685bf6c3ff5bb005a7962265313e14bc82fb27a983a4b3fc2c'
LEDGER='fd17077e18b3f159f176b300578a7a563adeb077729226917b9d0b2ac9a238c8';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save59_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE59_JA.md'
EVIDENCE='content/modernization/pr16_story_save59_evidence'
VISUAL='content/modernization/pr16_story_save59_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[7, 13], [7, 14], [7, 15], [7, 16], [6, 16], [5, 16], [5, 15], [5, 14], [5, 13], [5, 12], [5, 11], [5, 10], [5, 9], [5, 8], [5, 7]]
FLASH_PHASES=['7e26ee583bce507aa240d386845d4162169a6d60efe6b830205381e462f14bf4', 'e6c26e6c1cdb82288184230456cc8daca2bf3ce371e9459197fb180b3c360773', '0b2a5fcbde760e0e3e367f532e66b2260b960f90d8f172bb666825d90aeafc0d', '4a399f7ef535e9d7431c3643b7452897fa662617adbddfe0db2654406ee38b59', 'cb16caddcc051a05a90c042c0a0f79f0d6a833b5226751bc44343fd9ab70b1a8', '952ccf6b3ec28959894c3c8964e1d9941a00cf370ea5ec3ced738235ca27c2b4', '43f02823f18787207bfd495e2ddd56791591c3549de4bfb3481bb981d52fa9b2', 'aba6d1a1925a96350a29f1c71bcfbab4947e1bd24abc1f0847c4c2a35afc57ae', '6b1618a62d34216b43b3faf1f8f521931feb4b81c3c4891fdd75ab9df32628c1', 'cd20f474a2d507c28b8fb02dd10605265ced9fbe68250dc61126e76b39cd9ae6', '4fca3ab8893f0a6432f3a10d053e872a7a5b1340bf42a3d390f36be1545da4b2', '16213b373a212c2f373924fd6bd932d5f0f18a2a27bc61370a2afd0347c9573e', '48bed1dbfb18bce00199de1c67b1f6e6ada4cb15c4214b8cf260b67b99404ee3']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=(seed==m.a.OUTPUT and v['screen']==17))
    return parsed
def motion(i):
    if i<=3:return [7,13+i],1
    if i==4:return [7,16],3
    if i<=6:return [11-i,16],3
    if i==7:return [5,16],2
    if i<=16:return [5,23-i],2
    return [5,7],2

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==52 and len(bo)==2,'全54画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(95,4550)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間95/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.TRANSITION if i==16 else 134282949 if i==17 else m.m.BATTLE if 18<=i<=25 else m.m.FIELD
        need(o['map']==[1,59]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'通常14歩/新野生戦の位置・向き')
        need(o['callback2']==cb and o['field']is(i<16)and o['lock']==int(16<=i<26 or 27<=i<51),'field callback復帰と勝利残留wire falseを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(4 if i>=17 else 0)and o['battle_outcome']==int(i>=26),'野生1勝だけ。残留を追加勝利にしない')
        need(o['party_sha256']==(m.a.PARTY if i<25 else PARTY)and o['ledger_sha256']==(m.a.LEDGER if i<27 else LEDGER),'実PP1消費とRAM台帳の観測境界')
        need(o['save_counter']==(58 if i<46 else 59),'46counterは保存中、47成功')
        wanted=m.a.FLASH if i<34 else FLASH_PHASES[i-34]if i<47 else FLASH
        need(o['flash_sha256']==wanted,'全13部分write/47最終Flashを区別')
    need(len(set(FLASH_PHASES))==13 and FLASH not in FLASH_PHASES,'counter59の観測46も部分write')
    for o in bo:
        m.idle(o,59);need(o['map']==[1,59]and o['xy']==[5,7]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_WEST_HALL_SAVE59_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,ordinary_saves=1,save_counter=59,map=[1,59],map_name_ja='こころのやかた・入口階',xy=[5,7],facing=2,party_count=4,rp=0,travel_steps=14,turns=2,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,11],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],wild_species_name_ja='オタクン',wild_level=9,observed_move_uses=[0,0,0,1],move_commands=1,target_confirmations=0,move_commands_not_automatically_pp_uses=True,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[27],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=46,counter_change_not_save_completion=True,partial_write_observations=list(range(34,47)),stable_hash_not_alone_save_completion=True,save_success_text_observation=47,save_success_wording_observed=True,stable_field_observation=51,progress_inputs=95,continue_inputs=13,screen_count=54,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(55,12,11)],'実slot3 PP1消費だけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[55]=11;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags不変');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save58/59と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,58,s.LAYOUT);new,rb=s.bank(after,0xe000,59,s.LAYOUT);_,rc=s.bank(after,0,58,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save58全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[15,10,15,11]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==17904,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,52,66)],'aux1変数。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6966,1717),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=599,party_byte_deltas=pd,pp=[15,10,15,11],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==54,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][51]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is False,'通常14歩のみ。上階未到達')
    need(measured['battle']==dict(start=18,finish=26,trainer=False,outcome=1,move_commands=[0,0,0,1],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=24,move_slot=3)]),'選択1/相手確定0/実PP1の区別')
    need(measured['frontier']==dict(kind='new_battle',trigger=[5,7],map=[1,59],xy=[5,7],observation=26),'最初の新野生戦直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+27:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    for i,slot in [(22,0),(23,2),(24,3)]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',slot),'実技UI cursorだけ')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0051.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'人物と床の暗所field全byte一致')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['inert_warp8']['behavior']==8 and inspection['entry']['xy']==[30,10],'有効階段への静的経路と実到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result


