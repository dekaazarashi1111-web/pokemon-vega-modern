#!/usr/bin/env python3
"""博物館2階Save94の原本だけを独立受入。旧native/既受入試験は再走しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save94_measure as m
from pr16_story_after_maori import need,identity
SOURCE='b773e5611b374491a793985ef53c282912e35a5a'
RUN,JOB,ARTIFACT=37189671003,111399049470,11298740300
ARCHIVE=dict(size=212641,sha256='87fd0d3f983d81cfc9964bc7a143fdf2988d8abf84e0aa2d272e465d70078abb')
OUTPUT=dict(size=131088,sha256='a306d040197e63d32a3a3d3380041af66c05ec17b8dbe52225320dad4046bb4f')
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='596553b6532f0cfd8110b9cae03a626736a63a8d5813d2f9fe7176d4d31cbcab'
LEDGER='06f01776543e704eee7d3ca7a842f5d4ec48f44d9b80b2946254ffe2a9e45f0b';COLD_LEDGER=LEDGER;SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save94_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE94_JA.md'
EVIDENCE='content/modernization/pr16_story_save94_evidence'
VISUAL='content/modernization/pr16_story_save94_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace=m.a.trace;trace_rows=m.a.trace_rows;ROUTE=m.ROUTE
POSITIONS=[[14, 5], [14, 5], [13, 5], [12, 5], [11, 5], [10, 5], [9, 5], [8, 5], [8, 5], [8, 6], [8, 7], [8, 8], [11, 8]]
FLASH_PHASES=['ad05294de661e157638f9f284070c00de6af7e0d54c41f5f74bde6478cf073d3', 'dc10782b2fbbdc5eebb17490c80d5850b996b0239788c8b1b95a7084393ad986', '96755c0613616722dc4679673f1bdf3af9ff4b6dd71b17ec0819f6141fb2c5a5', '51335e0dd9f86e2970ad44a4256c78cda730a11d4554ab9e13eb38587d31076a', '308bdf21785e3975af3e2a652ee4fa55415e786bcd32d488b25a6d024fdc3e79', '038357157db7e6235de64f2f7de9bb1a30fe6bad18b0d272023c04cd021af67b', '7e071c304682ddef396d5e505894b9f493880d969b2c769df7b5188f312934fa', 'a9c90006338a769b37f34c4f4f193a3fddb60c0d413979a05c3469a5d932587a', 'c3cd6e6c44765c0da966bdc6440ff0b6cf5c266710af12369a54035494dcde39', 'f447dcefb98472106839876fddf1d7a1639945b85c65882502e97dd8b9a68d23', '3ece24d4cf01d8e8ce98dafa600296d93bf595a87c1af6887e3e8528e0309575', 'b4ccde9acd0f1c2347eaf680f5f8e8e99e6e5deaaf46c1b0af749a090d6dca22', '4152825d89ca8c40f845fff9114db3b83b0286f9e653091885e579d4ed2ed9c6', 'a90b38b3e4f4e4cb11df1a309cf047cf9fe8879f2cbd05064e230464a83d5f5b', '9370aa0ab354298a0c90dba81bd462531675dec35990cfde7eb908731b5c5817']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==39 and len(bo)==2,'全41画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(70,3190)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新9歩/旋回2/東方向階段/70+cold13入力')
    for i,o in enumerate(ao):
        xy=POSITIONS[i]if i<13 else[11,8];where=[6,0]if i<12 else[6,1];field=i<13 or i==38;facing=4 if i==0 or i>=12 else 3 if i<8 else 1
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'西6/南3/東入力warp・2階11,8東。自動追加tile移動なし')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'12到着→13menu→38field callback。38画面には成功overlayが残る')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<10 else LEDGER),'1階8,7の観測10でRAM ledger差分。owner未解明')
        need(o['save_counter']==(93 if i<34 else 94),'34counter94だが保存中→35成功文言/最終hash→38unlock')
        wanted=m.a.FLASH if i<20 else FLASH_PHASES[i-20]if i<35 else FLASH
        need(o['flash_sha256']==wanted,'20〜34部分保存/35最終hash。counter単独で完了としない')
    need(len(set(FLASH_PHASES))==15 and FLASH not in FLASH_PHASES and ao[34]['save_counter']==94 and not ao[35]['field'],'最後の部分hash/counterと成功文言を分離')
    for o in bo:
        m.idle(o,94);need(o['map']==[6,1]and o['xy']==[11,8]and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame/全SaveRTC/party/RAM保持')
    return dict(status='PASS_MUSEUM_SECOND_FLOOR_SAVE94_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=94,map=[6,1],map_name_ja='ミルシティ博物館2階',xy=[11,8],facing=4,party_count=4,rp=0,travel_steps=9,turns=2,directional_stair_activation_inputs=1,scripted_turns=0,warps=1,automatic_entry_step_observed=False,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,gym_flags4372_to4378_all_clear=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[10],ram_difference_owner_resolved=False,old_save89_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,flag2056_runtime_owner_resolved=False,auxiliary_runtime_owners_resolved=False,save_counter_changed_observation=34,counter_change_not_save_completion=True,partial_write_observations=list(range(20,35)),first_final_flash_observation=35,last_partial_hash_observation=34,save_in_progress_observations=list(range(20,35)),stable_hash_not_alone_save_completion=True,save_success_text_observation=35,save_success_wording_observed=True,stable_field_observation=38,progress_field_screen_clear=False,progress_final_success_overlay_visible=True,progress_inputs=70,continue_inputs=13,screen_count=41,native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=1,total_new_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=False,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,1,0)],'2階入場physical2056だけclear。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save93/94と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,93,s.LAYOUT);new,rb=s.bank(after,0,94,s.LAYOUT);_,rc=s.bank(after,0xe000,93,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save93全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23114,'全Bag/5pocket/23114円保持・受付再走0');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'S61E全payload保持/紙未引渡し')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'前回clearの4372〜4378全保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0 and(eb[259]>>4)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4001,2,0),(0x4021,74,83),(0x4022,1,0)],'2階入場3変数差分はowner未解明。受付4061=1保持')
    need(va[0x61]==vb[0x61]==1,'受付支払済4061保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7062,1772),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[],unresolved_variable_owners=[0x4001,0x4021,0x4022],auxiliary_runtime_owners_resolved=False,museum_fee=0,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==41,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][38]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新9歩/東方向階段だけ、戦闘/紙引渡し0')
    need(measured['frontier']==dict(kind='new_museum_second_floor',trigger=[8,8],map=[6,1],xy=[11,8],facing=4,observation=12),'最初の2階到着直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+13:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0038.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    hashes=['5b8d8ebdcdd6ec51525375d8b04633f9f1baa91d800a8c86f20670d587ef9d39','ee7aab20247f5f55c657deb5ab80c76f306b04b844b9456d5b4461e0fda24cab','05ed0ef72c0dfc74ae766049a8df865c3746e490387783013acde3aac1875658']
    need([identity(x)['sha256']for x in frames]==hashes and len(set(frames))==3,'38成功overlay残留/cold NPC領域差分。全pixel一致とは主張しない')
    def pixels(raw):
        need(raw[:15]==b'P6\n240 160\n255\n' and len(raw)==115215,'実PPM');return [raw[i:i+3]for i in range(15,len(raw),3)]
    x,y,z=map(pixels,frames);d0=[(i%240,i//240)for i,(a,b)in enumerate(zip(x,y))if a!=b];d1=[(i%240,i//240)for i,(a,b)in enumerate(zip(x,z))if a!=b];dc=[(i%240,i//240)for i,(a,b)in enumerate(zip(y,z))if a!=b]
    need((len(d0),len(d1),len(dc))==(19884,19904,263),'差分全pixel数')
    need(all((2<=x<=125 and 2<=y<=85)or(5<=x<=234 and 115<=y<=156)for x,y in d0+d1),'progress差分は表示cardと成功文言矩形内のみ')
    need(all(66<=x<=94 and 19<=y<=38 for x,y in dc),'cold差分はNPC領域だけ。主人公/地形外は同一')
    need(measured['museum_admission_observed']is False and measured['museum_admission_previously_accepted']is True and measured['paper_consumed_or_delivered']is False and measured['museum_second_floor_observed']is True and measured['museum_second_floor_accepted']is False,'測定原本は2階受入前。受付再走/紙引渡しなし')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']==m.inspect(rom,before),'静的階段と4061支払済の全byte')
    result['screen_comparison']=dict(progress_final_success_overlay_visible=True,progress_to_cold_changed_pixels=[19884,19904],cold_changed_pixels=263,cold_difference_rectangle=[66,19,94,38],all_pixels_identical=False)
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save94_next_route.json').read_bytes())
