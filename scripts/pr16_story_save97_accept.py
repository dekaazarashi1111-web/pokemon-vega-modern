#!/usr/bin/env python3
"""博物館退出Save97の原本だけを独立受入。旧native/既受入試験は再走しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
# 旧受入sourceを変えず154固有moduleの歴史連鎖を読むための、この検証入口だけの有限上限。
# 既定1000はPython3.12のunittest fresh import時だけ不足。native呼出し/旧試験再走はない。
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save97_measure as m
from pr16_story_after_maori import need,identity
SOURCE='4c61d6e9eaf5fe7fa64e8d477017448342d9819a'
RUN,JOB,ARTIFACT=37193900573,111411662442,11300361541
ARCHIVE=dict(size=235132,sha256='23b0b7b2e418218aab229e6dbeca030a03571ec701422df9692418c6d3dc84d7')
OUTPUT=dict(size=131088,sha256='4871ba79e718ea8dc8bc701394846ce1b393cd41a5961564ed4d670437a52139')
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='c62fab36bfc00014d0fe0e10aa9e598184e5a56a23115699985ef636827726d1'
LEDGER='6338b56b0cf486cddb468ef4eb0bbd7525d0f8d79f9d0ca6852b5aa7aea66619';COLD_LEDGER=LEDGER;SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save97_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE96_JA.md'
EVIDENCE='content/modernization/pr16_story_save97_evidence'
VISUAL='content/modernization/pr16_story_save97_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace=m.a.trace;trace_rows=m.a.trace_rows;ROUTE=m.ROUTE
POSITIONS=[[8, 8], [8, 8], [8, 7], [8, 6], [8, 5], [8, 5], [9, 5], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [14, 5], [14, 6], [14, 7], [14, 8], [14, 9], [19, 26]]
FLASH_PHASES=['1115b678298ea519b558489715bf86eecc726d9d1d927272ebf10e8079c25585', '5e7ca961c3ba678ce2a3dd80aae0a8ab5e94f9701e4660e6e4b116721b0f8ed9', '2a508a5b325bf3547dfb429e95d95a359358a44987c95f3ab82808d1ffc88784', '2f265ec9a4226378f762aa9587f2b0f8f983d813fe545dd16c442d9729701a94', 'd2ab3b007b432d27c8eb4eee73e0ce78e978a119da63d71249553733d8b500e6', '2fb8cecf641a2852d65d7a0295d046876d72d0a34bbe280288f91695df17ac8a', '0e6ab479ad160ef81ac27a5043d4bd05a456d0ca70959e2cd463fcecb9834af3', 'daa2d8efd55ca034e5a092c35cacfda5610c82f83f44d7f2b488512160c31f19', '183f88797ec55f3fb7adc0d9dec4e9025dc3500995d1d49a92c88b698a06d277', 'dcbb64047b2ea13475d0c6a069b6d330a19ffa350bdb2ed642065c2c3a2a6d78', 'bb666342d4ead2a8e71daaa8c7f342f24b16de59fe5197b41414b67e2d4e0f0c', 'aff34ef0edfea7879a6928ae238f1b8b0c5a7f98282aa2f3e82c3a948db21bda', '5bd274dcf0ad567f938b635ae6c6b996831e3eb70696c4e5cc5ef4d392740f34', '9d6ff2e327402a601ee0b362c36be54a8450b4f77d2398fd58e0d33b0787d50a']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==44 and len(bo)==2,'全46画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(80,3470)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新13歩/旋回3/南矢印/80+cold13入力')
    for i,o in enumerate(ao):
        xy=POSITIONS[i]if i<18 else[19,26];where=[6,0]if i<17 else[3,2];field=i<18 or i==43
        facing=3 if i==0 else 2 if i<5 else 4 if i<12 else 1
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'13歩/3旋回/南矢印、町19,26南。warp19,25から自動南1歩')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'17最初町field→18menu→43clearfield')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<5 else LEDGER),'観測5旋回でRAM変化。owner未解明、以後/cold保持')
        need(o['save_counter']==(96 if i<38 else 97),'38counter97でも保存中/別hash。39成功文言後確定')
        wanted=m.a.FLASH if i<25 else FLASH_PHASES[i-25]if i<39 else FLASH
        need(o['flash_sha256']==wanted,'25〜38保存中、39安定最終hash/成功文言')
    need(len(set(FLASH_PHASES))==14 and FLASH not in FLASH_PHASES,'今回最終hashの先行一致なし。過去Save96先行一致の履歴を消さない')
    need(ao[38]['save_counter']==97 and ao[38]['flash_sha256']!=FLASH and not ao[39]['field'],'counter/最終hash/成功文言/fieldを分離')
    for o in bo:
        m.idle(o,97);need(o['map']==[3,2]and o['xy']==[19,26]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continueと120frame/SaveRTC/party/settledRAM保持')
    return dict(status='PASS_MUSEUM_EXIT_SAVE97_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=97,map=[3,2],map_name_ja='ミルシティ',xy=[19,26],facing=1,party_count=4,rp=0,travel_steps=13,turns=3,blocked_movement_inputs=0,npc_wait_inputs=0,npc_wait_frames=0,directional_stair_activation_inputs=0,directional_exit_activation_inputs=1,scripted_turns=0,warps=1,automatic_entry_step_observed=True,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,museum_return_first_floor_accepted=True,museum_exit_accepted=True,gym_flags4372_to4378_all_clear=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=0,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=True,letter_handoff_accepted=True,letter_delivered_flag4382=True,letter_delivered_flag4382_owner_resolved=True,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[5],ram_difference_owner_resolved=False,old_save89_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,flag2056_runtime_owner_resolved=False,auxiliary_runtime_owners_resolved=False,save_counter_changed_observation=38,counter_change_not_save_completion=True,partial_write_observations=list(range(25,39)),first_final_flash_observation=39,last_partial_hash_observation=38,stable_final_flash_observation=39,early_finalhash_not_completion=False,save_in_progress_observations=list(range(25,39)),stable_hash_not_alone_save_completion=True,save_success_text_observation=39,save_success_wording_observed=True,stable_field_observation=43,progress_field_screen_clear=True,progress_final_success_overlay_visible=False,progress_inputs=80,continue_inputs=13,screen_count=46,native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=1,total_new_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=False,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,1,0)],'退出physical2056だけclear。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save96/97と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,96,s.LAYOUT);new,rb=s.bank(after,0xe000,97,s.LAYOUT);_,rc=s.bank(after,0,96,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save96全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23114,'全Bag/5pocket/23114円保持・受付再走0');need(sum(q for item,q in ib['key_items']if item==274)==0,'封書引渡し後の空slot保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'S61E全payload保持/紙引渡し済み')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'前回clearの4372〜4378全保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==1 and(eb[259]>>4)&1==0,'expanded4383/4382保持、4380未完');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,109,122),(0x4022,1,4)],'退出aux2変数差分はowner未解明。受付4061=1保持')
    need(va[0x61]==vb[0x61]==1,'受付支払済4061保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7043,1752),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=0,paper_delivered=True,paper_flag4382_preserved=True,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[],unresolved_variable_owners=[0x4021,0x4022],auxiliary_runtime_owners_resolved=False,museum_fee=0,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def screen_comparison(frames):
    def pixels(raw):
        need(raw[:15]==b'P6\n240 160\n255\n' and len(raw)==115215,'実PPM');return [raw[i:i+3]for i in range(15,len(raw),3)]
    ims=list(map(pixels,frames));counts=[]
    for i,j in [(0,1),(0,2),(1,2)]:
        diff=[(k%240,k//240)for k,(x,y)in enumerate(zip(ims[i],ims[j]))if x!=y];counts.append(len(diff))
        need(all((0<=x<=15 and 83<=y<=102)or(64<=x<=143 and 137<=y<=159)for x,y in diff),'左端NPCと花animationの矩形内だけ。主人公/博物館形状保持')
    need(counts==[768,626,752],'field差分pixel会計。全画面一致にしない')
    return dict(progress_final_success_overlay_visible=False,progress_to_cold_changed_pixels=counts[:2],cold_changed_pixels=counts[2],npc_difference_rectangles=[[0,83,15,102]],animated_flower_rectangles=[[64,137,143,159]],all_pixels_identical=False)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==46,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][43]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新13歩/南矢印だけ。戦闘/会話0')
    need(measured['frontier']==dict(kind='new_museum_exit',trigger=[14,9],map=[3,2],xy=[19,26],facing=1,observation=17),'初退出後の最初fieldで保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+18:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0043.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need([identity(x)['sha256']for x in frames]==['00f2e4d455f1700a39df6d470b00ce9ba6604f9899ad4586ec9f93df311fcb1e', '806c0de71fab28fd5a4ea6581940354f93e63488d5a938c685f2ecfa586eb3a1', 'a48e4406fd3f39b85a5bbcd8c7acf76bb2b0de23d0471b4d42b6d40d701e00e4'],'最終field/cold全3原画');result['screen_comparison']=screen_comparison(frames)
    need(measured['museum_exit_observed']is True and measured['museum_exit_accepted']is False and measured['paper_consumed_or_delivered']is True and measured['museum_admission_observed']is False,'測定時未受入原本を改作しない。封書会話/受付再走0')
    need(measured['prior_failed_native_processes']==1 and measured['prior_pre_native_failed_attempts']==1,'初回controller1失敗/native出口1失敗を成功へ換算しない')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']==m.inspect(rom,before),'静的13歩と出口behavior/方向/支払済全byte')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def failed_exit(folder):
    folder=Path(folder);p=trace(folder/'progress',m.a.OUTPUT);o=p['observations'];e=json.loads((folder/'progress/execution.json').read_bytes());f=json.loads((folder/'failure.json').read_bytes())
    need(len(o)==24 and p['end']['inputs']==58 and p['end']['frames']==3734 and e['initial_save']==e['final_save']==m.a.OUTPUT and e['returncode']==0,'失敗native1/58入力24画面。Save96全byte保持')
    need(f['native_processes']==1 and f['message']=='有限退出warp待機上限'and f['run_id']==37193632724 and f['source_head']=='c404c3b02f51e3d27029aebe9f8ad4e24ce4d6d3','元失敗を保持')
    need(all(x['map']==[6,0]and x['save_counter']==96 and x['field']is True and x['party_sha256']==PARTY and x['flash_sha256']==m.a.FLASH and x['battle_flags']==x['battle_outcome']==0 for x in o),'保存/戦闘/退出0')
    need(all(x['xy']==[13,9]and x['facing']==1 for x in o[15:]),'通常床13,9から南8回でも非発火')
    need(not list(folder.rglob('*.srm')),'未変更入力Save96は再配布しない')
    return dict(status='FAILED_EXIT_RETAINED_NOT_ACCEPTED',native_processes=1,inputs=58,frames=3734,observations=24,ordinary_saves=0,save_rtc_unchanged=True)

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save97_next_route.json').read_bytes())
