#!/usr/bin/env python3
"""館内新廊下のSave57原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save57_measure as m
from pr16_story_after_maori import need,identity
SOURCE='c246f9c79b3513f01f1dbe5a987b685f8653fddc'
RUN,JOB,ARTIFACT=37154941204,111296302107,11284919827
ARCHIVE=dict(size=164504,sha256='dd16a6b510145b130ed5a0632373b7ee972b30732234ce9a6351e46c1d3f22c8')
OUTPUT=dict(size=131088,sha256='082a6789ed90223995bd007efaa43337c8aca352d85f1a33068a6fae11b1b9ca')
PARTY='03f463a9079a0d8b7abeec5d0154843fe882b74c32a75ab539846ebea1e915ec'
FLASH='7bbf21f45e173e8697c6b2d433aa92ea29faf203de8063725e038a2916213695'
LEDGER='939b183a3db45a9fedd87e87814bbb94e1cd42a8510dc3d3083d0ce96d9ff1d4';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save57_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE57_JA.md'
EVIDENCE='content/modernization/pr16_story_save57_evidence'
VISUAL='content/modernization/pr16_story_save57_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[20, 25], [19, 25], [19, 24], [19, 23], [19, 22], [19, 21], [19, 20], [19, 19], [19, 18], [19, 17], [19, 16], [19, 15], [19, 14], [19, 13]]
FLASH_PHASES=['e47f32fadb05cb10a658efeb2bf1c4bcd3547512d6da1474ff0c6fe500e00ee8', '59421383dbc1d085daabe48e9fe4f91f6e48233fffe3420605df40b351433175', '838b92a681854450fb2e5ca3e03db02073392bcaa83b62ec1f8588fabfde4694', 'c9623dbc2585c34cf623d2e588d784102ac6215aa68a4d7c9f07c7dcad237056', 'd7c6fc7adcac5bab3a87f21f846ad555ee47fa8af35dceb1783a51935d37c3c2', 'c24c8184c28093dc32d579a023987ab7c5874116ac62cb52d4af781f53a947e5', 'f038c10854af5bcf8dbc2c519f77b4987cb53b4dd6671873862945a8d9fb7348', '724b033e81918e322aec23af8de5520bbb8a4d85ea1c2634d7c2f74883cededf', '7f04d7be55c3ece96918d4f5dc00df5bfc8ea29f7ed887bfb9bb0281b387b7b9', 'a10e707bd6d43a6e4fd08c4bb10874669934a06d3a17775f858986f0b8cc0d4b', 'ea09742a8daaca2be8d6fe6e0fc15be3d3a7ae85c08b0482e44842ef016ec04b', 'c1de1e3e48c6ab690a6891806665284b80646dc83927271ecf713d57b568f09a', '9c8eb75644de6ecf6f4446a6349fddbd005eaee24692bb595f361aec9732c266']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=(seed==m.a.OUTPUT and v['screen']==16))
    return parsed
def motion(i):
    if i<4:return [([20,25],2),([20,25],3),([19,25],3),([19,25],2)][i]
    return([19,max(13,28-i)],2)
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==51 and len(bo)==2,'全53画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(93,4494)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間93/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.TRANSITION if i==15 else 134282949 if i==16 else m.m.BATTLE if 17<=i<=24 else m.m.FIELD
        need(o['map']==[1,59]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'通常13歩/新野生戦の位置・向き')
        need(o['callback2']==cb and o['field']is(i<15)and o['lock']==int(15<=i<25 or 26<=i<50),'field callback復帰と勝利残留wire falseを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(4 if i>=16 else 0)and o['battle_outcome']==int(i>=25),'野生1勝だけ。残留を追加勝利にしない')
        need(o['party_sha256']==(m.a.PARTY if i<24 else PARTY)and o['ledger_sha256']==(m.a.LEDGER if i<3 else LEDGER),'実PP1消費とRAM台帳の観測境界')
        need(o['save_counter']==(56 if i<45 else 57),'45counterは保存中、46成功')
        wanted=m.a.FLASH if i<33 else FLASH_PHASES[i-33]if i<46 else FLASH
        need(o['flash_sha256']==wanted,'全13部分write/46最終Flashを区別')
    need(len(set(FLASH_PHASES))==13 and FLASH not in FLASH_PHASES,'counter57の観測45も部分write')
    for o in bo:
        m.idle(o,57);need(o['map']==[1,59]and o['xy']==[19,13]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_WILD_SAVE57_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,ordinary_saves=1,save_counter=57,map=[1,59],map_name_ja='こころのやかた・入口階',xy=[19,13],facing=2,party_count=4,rp=0,travel_steps=13,turns=2,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,13],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],wild_species_name_ja='バーニン',wild_level=9,observed_move_uses=[0,0,0,1],move_commands=1,target_confirmations=0,move_commands_not_automatically_pp_uses=True,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[3],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=45,counter_change_not_save_completion=True,partial_write_observations=list(range(33,46)),stable_hash_not_alone_save_completion=True,save_success_text_observation=46,save_success_wording_observed=True,stable_field_observation=50,progress_inputs=93,continue_inputs=13,screen_count=53,native_processes=2,prior_failed_native_processes=1,total_new_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(55,14,13)],'実slot3 PP1消費だけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[55]=13;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags不変');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save56/57と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,56,s.LAYOUT);new,rb=s.bank(after,0xe000,57,s.LAYOUT);_,rc=s.bank(after,0,56,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save56全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[15,10,15,13]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==17904,'全Bag/全5pocketと所持金保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,25,38),(0x4022,4,0)],'aux2変数。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7030,1731),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=599,party_byte_deltas=pd,pp=[15,10,15,13],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==53,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][50]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is False,'通常13歩のみ。上階未到達')
    need(measured['battle']==dict(start=17,finish=25,trainer=False,outcome=1,move_commands=[0,0,0,1],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=23,move_slot=3)]),'選択1/相手確定0/実PP1の区別')
    need(measured['frontier']==dict(kind='new_battle',trigger=[19,13],map=[1,59],xy=[19,13],observation=25),'最初の新野生戦直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+26:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    for i,slot in [(21,0),(22,2),(23,3)]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',slot),'実技UI cursorだけ')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0050.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2],'人物と床の暗所field全byte一致')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['inert_warp8']['behavior']==8 and inspection['entry']['xy']==[30,10],'有効階段への静的経路と実到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    prior=json.loads((folder/'prior-inert-warp-failure.json').read_bytes());need(prior['artifact_id']==11285188296 and prior['execution']['observations']==3 and prior['execution']['native_end']['inputs']==16 and prior['execution']['final_save']==m.a.OUTPUT,'旧誤仮定の未保存失敗を保持')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
