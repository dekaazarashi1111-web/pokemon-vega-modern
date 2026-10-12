#!/usr/bin/env python3
"""Ranger接近Save99を原本から独立受入。移動NPCと会話到達を分離。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save99_measure as m
from pr16_story_after_maori import need,identity
SOURCE='625a1e1aecfa41860a2018e854114c15d246905a'
RUN,JOB,ARTIFACT=37197174924,111421350168,11301562515
ARCHIVE=dict(size=606235,sha256='33b59f66e11a2db147def8160de679dc2b7363fc05fa13b531deaeaa584db509')
OUTPUT=dict(size=131088,sha256='18de364bd911a9470965cf571e10aab899e8f4236bcaef327586e965b3a02b6b')
PARTY='a889748859f118b98c42e9ef5f0fd2847466d07383f5743946453c961261580d'
FLASH='d8bb1774fec52205b9a1d2bce9f2c4de974e80c31c621134e8d6154732e33b7c'
LEDGER='454211fdc67ead3ae690f7fcd42789f53e709ba95eb037756e0afc5b8056c61a';COLD_LEDGER=LEDGER;SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save99_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE99_JA.md'
EVIDENCE='content/modernization/pr16_story_save99_evidence'
VISUAL='content/modernization/pr16_story_save99_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace=m.a.trace;trace_rows=m.a.trace_rows;ROUTE=m.ROUTE
POSITIONS=[[28, 39], [28, 38], [28, 37], [28, 36], [28, 35], [28, 34], [28, 34], [29, 34], [30, 34], [31, 34], [32, 34], [32, 34], [32, 33], [32, 32], [32, 31], [32, 30], [32, 29], [32, 28], [32, 27], [32, 26], [32, 25], [32, 25], [31, 25], [31, 25], [31, 24], [31, 23], [31, 22], [31, 21], [31, 20], [31, 19], [31, 18], [31, 17], [31, 16], [31, 15], [31, 15], [32, 15], [32, 15], [32, 14], [32, 13], [32, 13], [31, 13], [30, 13], [29, 13], [28, 13], [27, 13], [26, 13], [25, 13], [25, 13], [25, 14], [25, 15], [25, 15], [24, 15], [24, 15], [24, 16], [24, 17], [24, 18], [24, 18], [23, 18], [22, 18], [22, 18], [22, 19], [22, 20], [22, 21], [22, 21], [21, 21], [20, 21], [19, 21], [19, 21], [19, 22], [19, 23], [19, 24], [19, 25], [19, 26], [19, 27], [19, 28], [19, 28], [18, 28]]
FACING=[2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 3, 3, 1, 1, 1, 1, 3, 3, 3, 1, 1, 1, 1, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 3, 3]
FLASH_PHASES=['53d76013241375877ecdf5f3d3c67b1e3b3aa261fe3c8d1ee6fb842795e640de', '9639416b0848eba380d15f9f4829bbf30cc243d640bf24c04ce9b11304475418', '3ca6aa87fee5b3fff9209acc63d9dbc9f3805d54b2df739e449a095b1c38e822', 'f82dba249759a06da60ce75701073f52a747db55efa2bfc0ab9f46276aaa72b9', '2d1d3b08b2e73cb98cfb62e78b97ee49bacabb34712ca3f76bfc4e8fcaac8c9c', '15256f001eb3cd991549439c414de8ba2ae72c902d273468ca74327a39b30937', '154a27ce57f33db59d214cc07bde894e737a347219be98d4ab47a6dab7947d07', '3c127c2b51706bd3be4a8f125893798857e997f6e42628b31ff4a6f444b937e9', '348220e70566eb912dcc855e51da2c949e5928584ca159640e6fc9a7d1083bec', '57c570bbda3a30a4da2d5a9067a4fe6bafbbc6868ed71e15030047091d30aa43', '5c142330cf5fd3f67d71da3ba44b19f555508d19fa3aae0cdb8a6a817a8b5a30', '49dd331ed09ea28bced330511291d288f9760e441c3c01de70ac09b550749351', 'd5f336b986e9c6f133b8c06d2b2cd3e7524f3846f4a9d586be507c6e5ec235f7']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==102 and len(bo)==2,'全104画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(197,6612)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'61歩/15旋回/197+cold13入力')
    moved=[POSITIONS[0]]+[p for i,p in enumerate(POSITIONS[1:],1)if p!=POSITIONS[i-1]]
    need(moved==ROUTE and len(POSITIONS)-len(moved)==15,'61単tileと15旋回。無入力自動歩行/blocked0')
    for i,o in enumerate(ao):
        xy=POSITIONS[i]if i<77 else[18,28];facing=FACING[i]if i<77 else 3;field=i<77 or i==101
        need(o['map']==[3,23]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'全61歩/15旋回と保存時位置')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'76接近終端→77menu→101clearfield')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'草通過で新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY,'61歩/4021wrap前で全party保持')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<53 else LEDGER),'53のRAMledger差分owner未解明。以後/cold保持')
        need(o['save_counter']==(98 if i<96 else 99),'96counter99でも保存中/部分hash')
        wanted=m.a.FLASH if i<84 else FLASH_PHASES[i-84]if i<97 else FLASH
        need(o['flash_sha256']==wanted,'84〜96部分保存/97最終hash成功文言')
    need(len(set(FLASH_PHASES))==13 and FLASH not in FLASH_PHASES,'途中hash/最終hashを分離')
    need(ao[96]['save_counter']==99 and ao[96]['flash_sha256']!=FLASH and not ao[97]['field'],'counter単独を保存完了扱いしない')
    for o in bo:
        m.idle(o,99);need(o['map']==[3,23]and o['xy']==[18,28]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全SaveRTC/party/settledRAM保持')
    return dict(status='PASS_RANGER_APPROACH_SAVE99_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=99,map=[3,23],map_name_ja='505番道路',xy=[18,28],facing=3,party_count=4,rp=0,travel_steps=61,turns=15,blocked_movement_inputs=0,npc_wait_inputs=0,rock_stair_crossings=2,rock_stair_behavior=42,directional_stair_warps=0,one_way_ledge_jumps=0,warps=0,map_connections=0,ranger_approach_accepted=True,ranger_interaction_accepted=False,ranger_adjacent_at_stop=False,ranger_visual_observations=[dict(lane='progress',observation=101,xy=[20,28]),dict(lane='continue',observation=0,xy=[20,28]),dict(lane='continue',observation=1,xy=[20,29])],letter_handoff_accepted=True,paper_consumed_or_delivered=True,paper_item_quantity=0,museum_fee=0,museum_admission_var4061=1,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_pp_consumption=[0,0,0,0],move_commands=0,party_unchanged=True,party_bytes_preserved=600,party_changed_observations=[],walk_counter_owner_resolved=True,friendship_wraps=0,happiness_counter=91,next_friendship_wrap_after_steps=37,progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_changed_observations=[53],ram_difference_owner_resolved=False,flag2056_runtime_owner_resolved=False,save_counter_changed_observation=96,counter_change_not_save_completion=True,partial_write_observations=list(range(84,97)),first_final_flash_observation=97,save_success_text_observation=97,save_success_wording_observed=True,stable_field_observation=101,progress_field_screen_clear=True,progress_final_success_overlay_visible=False,progress_inputs=197,continue_inputs=13,screen_count=104,native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=0,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=False,progress_to_cold_pixels_identical=False,wild_controller_native_exercised=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte');need(x==y,'周期前61歩の全party600byte保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags保持');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save98/99と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,98,s.LAYOUT);new,rb=s.bank(after,0xe000,99,s.LAYOUT);_,rc=s.bank(after,0,98,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save98全bank57344byte保持')
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
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,30,91),(0x4022,0,1)],'61歩とmod128/mod5の歩数owner。受付4061=1保持')
    need(va[0x61]==vb[0x61]==1,'受付支払済4061保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7160,1788),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=0,paper_delivered=True,paper_flag4382_preserved=True,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[],unresolved_variable_owners=[],resolved_walk_counter_variables=[0x4021,0x4022],auxiliary_runtime_owners_resolved=True,individual_random_branch_pc_trace_captured=False,museum_fee=0,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

NPC_RECT=[145,67,158,102]
def screen_comparison(frames):
    def pixels(raw):
        need(raw[:15]==b'P6\n240 160\n255\n'and len(raw)==115215,'実PPM');return[raw[i:i+3]for i in range(15,len(raw),3)]
    ims=list(map(pixels,frames));counts=[]
    for i,j in[(0,1),(0,2),(1,2)]:
        diff=[(k%240,k//240)for k,(x,y)in enumerate(zip(ims[i],ims[j]))if x!=y];counts.append(len(diff))
        need(all(145<=x<=158 and 67<=y<=102 for x,y in diff),'差分は移動Rangerの2tile sprite内だけ。主人公/地形保持')
    need(counts==[132,410,376],'progress/cold132/410px、cold間376pxはRanger移動')
    return dict(progress_final_success_overlay_visible=False,progress_to_cold_changed_pixels=counts[:2],cold_changed_pixels=counts[2],ranger_sprite_rectangle=NPC_RECT,all_pixels_identical=False,cold_pixels_identical=False,dynamic_ranger_movement_observed=True)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'初回成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==104,'測定identity')
    parsed={}
    for lane,seed in[('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][101]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'61歩のみ。新戦闘/会話0')
    need(measured['frontier']==dict(kind='ranger_approach_no_interaction',map=[3,23],xy=[18,28],facing=3,observation=76),'Ranger接近終端。隣接前方ではない')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+77:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in['progress/screen-0101.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    result['screen_comparison']=screen_comparison(frames)
    need(measured['ranger_approach_observed']is True and measured['ranger_approach_accepted']is False and measured['ranger_interaction_observed']is False,'原本の測定/受入を分離。会話0')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']==m.inspect(rom,before),'固定ROCK_STAIRSと南北条件全byte')
    commands=(folder/'progress/commands.txt').read_text().split('observe 76\n')[0];need('key 1 'not in commands and 'key 2 'not in commands and 'key 8 'not in commands,'接近まで通常方向入力だけ/会話なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    need(result['boundary']['variable_deltas']==[(0x4021,30,91),(0x4022,0,1)]and(30+61)%128==91 and(0+61)%5==1,'61歩の独立owner算術照合')
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save99_next_route.json').read_bytes())
