#!/usr/bin/env python3
"""動的Ranger会話とダグトリオ解放のSave100原本を独立受入。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save100_measure as m
from pr16_story_after_maori import need,identity
SOURCE='b83dcb3d7a0a5465606be442eb431c9d53e0acfe'
RUN,JOB,ARTIFACT=37198723726,111425819528,11302156714
ARCHIVE=dict(size=316179,sha256='2f336d128735e1a18da931eb69f069548bcfaec52d8481124a5b2ad2e645abc2')
OUTPUT=dict(size=131088,sha256='9a4185c74f4906eb05de0167f082fa70de166caf42c5aa6bf7a9fe85bfee77ff')
PARTY='a889748859f118b98c42e9ef5f0fd2847466d07383f5743946453c961261580d'
FLASH='fe2d8361bb9ac237c0ce25893b419fad607668d0df5bc072ae58ff1d400f0747'
LEDGER='454211fdc67ead3ae690f7fcd42789f53e709ba95eb037756e0afc5b8056c61a'
COLD_LEDGER='1a34e64cfee8f3793ea60b1736daa6df07d122390dcb69aacacf45cbffd0a229';SETTLED_COLD_LEDGER=COLD_LEDGER
CP='content/modernization/pr16_story_save100_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE100_JA.md'
EVIDENCE='content/modernization/pr16_story_save100_evidence'
VISUAL='content/modernization/pr16_story_save100_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace_rows=m.a.trace_rows
from pr16_story_save21_accept import screen_bytes
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=(seed==m.a.OUTPUT and v['screen']==10))
    return parsed
ROUTE=[[18,28],[19,28],[20,28]]
FLASH_PHASES=['f209cc023bfe354e216a2fb6dd243a19d021dcd874e49726b67931f393666bb2', '1d41c41556d3902926f49398dca84238937d3e84f09e34331f81c3dbe92afd6b', 'bcff6515d481e18b68a0d97f021668f326ca964aa0295205ff4194383c6e2080', '1d8683add9f59c683759b6316e780ec4de6397344a46801205ce9ca716a4605c', '0f4459efb2bcdcf3803fa5ff391c2efe30fda7e1d1730bf934d447a7d8944a91', 'd5d63dc87b2d4ef87ed8617752bd57f39e2d9f1fb6caf4059dbbe41feec67012', '7f6292ef8c868655297b61bd709a66cb37f24a66bde0a181796ddc076cc9d36b', '80cfc929bb6a2df76b72355e2e34cf0d4078ca986f88ef11bda4a24171f9f19b', 'c3b77ad09be1ed46971de8cbf56351a0961ff33231f9bce1070a482893bdf8ce', '139a94dc6052eb1bdcdc505275bd61f68ff5aace55a03f4a38d783c079d0e791', 'd0a5b3757b9bdb93e64637439ca8ef296833655cad109e8f735c0288d09f7dbc', '22895d367a48d02b14df0577cd3f0171323591d365b1291c4391dd4869a33b1e', 'fe2d8361bb9ac237c0ce25893b419fad607668d0df5bc072ae58ff1d400f0747', '18ad0874cae4ccca582a2bda5eed604a5d68b921885004b048ae2bcc8e7e75e4']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==52 and len(bo)==2,'全54画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(95,3812)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全95/cold13入力/3812/1510frames')
    for i,o in enumerate(ao):
        xy=[18,28]if i<2 else[19,28]if i==2 else[20,28]if i<11 else[5,16]if i==11 else[4,17]
        face=3 if i==0 else 4 if i<4 else 1 if i<12 else 3 if i<23 else 2
        field=i<6 or i in(25,51);where=[3,23]if i<11 else[3,2]
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'動的接近2歩/会話/warp/自動2歩と向き')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'5正面→6会話lock→25最初町field→26menu→51clearfield')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER,'progress全party/RAM保持。町新flagのpersistは別検証')
        need(o['save_counter']==(99 if i<46 else 100),'46counter100でも保存中')
        expected=m.a.FLASH if i<33 else FLASH_PHASES[i-33]if i<47 else FLASH
        need(o['flash_sha256']==expected,'全中間Flash/安定hashを分離')
    need(len(set(FLASH_PHASES))==14 and FLASH_PHASES[12]==FLASH and FLASH_PHASES[13]!=FLASH,'45の最終hash一時一致→46途中hash→47安定hash')
    need(ao[45]['save_counter']==99 and ao[46]['save_counter']==100 and not ao[47]['field'],'hash/counter単独で保存完了にしない')
    for o in bo:
        m.idle(o,100);need(o['map']==[3,2]and o['xy']==[4,17]and o['facing']==2 and o['field']is True and o['party_sha256']==PARTY and o['ledger_sha256']==COLD_LEDGER and o['flash_sha256']==FLASH,'独立Continue位置/party/SaveRTC/別RAMhash保持')
    return dict(status='PASS_RANGER_TOWN_RELEASE_SAVE100_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=100,map=[3,2],map_name_ja='ミルシティ',xy=[4,17],facing=2,party_count=4,rp=0,travel_steps=2,scripted_player_steps=2,scripted_steps_in_walk_counter=0,turns=2,warps=1,map_connections=0,ranger_interaction_accepted=True,ranger_actual_xy_before_talk=[20,29],player_before_talk=[20,28],player_facing_before_talk=1,dynamic_front_confirmed_observations=[4,5],talk_attempts=1,blind_static_north_A=False,ranger_script_capture_scene_accepted=True,player_capture_accepted=False,dugtrio_road_block_removed=True,town_chain_first_field=25,letter_handoff_previously_accepted=True,paper_quantity=0,museum_admission_var4061=1,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_pp_consumption=[0,0,0,0],healing_branch_taken=False,party_unchanged=True,party_bytes_preserved=600,friendship_wraps=0,happiness_counter=93,next_friendship_wrap_after_steps=35,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,progress_to_cold_ram_ledger_identical=False,ram_difference_owner_resolved=False,prior_ram53_42_owners_resolved=False,flag2056_runtime_owner_resolved=False,save_counter_changed_observation=46,counter_change_not_save_completion=True,first_final_flash_match_observation=45,final_flash_match_can_be_transient=True,stable_final_flash_observation=47,save_in_progress_observations=list(range(33,47)),save_success_text_observation=47,stable_field_observation=51,progress_field_screen_clear=True,progress_final_success_overlay_visible=False,progress_inputs=95,continue_inputs=13,screen_count=54,native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=1,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=COLD_LEDGER)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags保持');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save99/100と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,99,s.LAYOUT);new,rb=s.bank(after,0,100,s.LAYOUT);_,rc=s.bank(after,0xe000,99,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save99全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23114,'全Bag/5pocket/23114円保持・受付再走0');need(sum(q for item,q in ib['key_items']if item==274)==0,'封書引渡し後の空slot保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(259,224,240)],'S61E expanded4380だけset/CRC検証')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'前回clearの4372〜4378全保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==1 and(eb[259]>>4)&1==1 and(ea[256]&1)==(eb[256]&1)==1,'expanded4383/4382保持、4380新set、4352最終set維持');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,91,93),(0x4022,1,3),(0x4072,1,3)],'通常2歩だけのmod128/mod5と町連鎖4072=3。script自動2歩は歩数counterに加算されない')
    need(va[0x61]==vb[0x61]==1,'受付支払済4061保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==1 and vb[0x72]==3 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7145,1790),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=0,paper_delivered=True,paper_flag4382_preserved=True,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[],unresolved_variable_owners=[],resolved_walk_counter_variables=[0x4021,0x4022],auxiliary_runtime_owners_resolved=True,individual_random_branch_pc_trace_captured=False,museum_fee=0,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=dict(ef,**{'4352':1,'4380':1,'4382':1,'4383':1}),expanded_flag_deltas=[(4380,0,1)],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':3},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

FLOWER_TILES={(7,0),(9,0),(7,1),(8,2),(8,3),(8,7),(9,7),(8,8),(9,8),(7,9),(8,9)}
def screen_comparison(frames):
    def pixels(raw):
        need(raw[:15]==b'P6\n240 160\n255\n'and len(raw)==115215,'実PPM');return[raw[i:i+3]for i in range(15,len(raw),3)]
    ims=list(map(pixels,frames));counts=[]
    for i,j in[(0,1),(0,2),(1,2)]:
        diff=[(k%240,k//240)for k,(x,y)in enumerate(zip(ims[i],ims[j]))if x!=y];counts.append(len(diff))
        need(all((x//16,y//16)in FLOWER_TILES for x,y in diff),'差分は花animationの11tileだけ、主人公/通路/消失NPCの領域は保持')
    need(counts==[564,408,588],'progress/cold564/408、cold間588px。全pixel一致としない')
    return dict(progress_to_cold_changed_pixels=counts[:2],cold_changed_pixels=counts[2],allowed_animated_flower_tiles=sorted([list(x)for x in FLOWER_TILES]),all_pixels_identical=False,cold_pixels_identical=False,player_and_cleared_road_pixels_preserved=True)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'今回成功原本')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==54,'測定identity')
    parsed={}
    for lane,seed in[('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][51]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'通常歩行2だけ/新戦闘0。warpはNPCscript処理')
    f=measured['frontier'];need(f['kind']=='ranger_town_chain_first_field'and f['observation']==25 and f['event_start']==6 and f['approach_steps']==2 and f['xy']==[4,17]and f['map']==[3,2]and f['facing']==2,'連鎖の最初field')
    need(f['talk_attempts']==[dict(before=5,player=[20,28],facing=1,ranger=[20,29],consecutive_position_confirmed=True)],'通常Aは実NPC20,29の正面だけ')
    cal=json.loads((ROOT/m.PREP).read_bytes())['visual_locator'];coords=[[20,28],[20,28],[20,29],[20,29],[20,29],[20,29]]
    need(len(f['visual_observations'])==6,'会話前の全6画面')
    for i,row in enumerate(f['visual_observations']):
        o=parsed['progress']['observations'][i];raw=(folder/'progress'/f'screen-{i:04d}.ppm').read_bytes();found=m.locate(raw,o['xy'],cal)
        need(row==dict(observation=i,player=o['xy'],facing=o['facing'],ranger=found)and found['xy']==coords[i],'全6実画面のdynamic位置を再読/通常入力の再走なし')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+26:04d}.ppm').read_bytes())==i,'menu実cursor0→4')
    result['screen_comparison']=screen_comparison([(folder/n).read_bytes()for n in['progress/screen-0051.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']])
    need(measured['ranger_interaction_observed']is True and measured['ranger_approach_accepted']is False,'測定と独立受入を分離')
    need(json.loads((folder/'inspection.json').read_bytes())==measured['inspection']==m.inspect(rom,before),'全固定script/地形binding')
    commands=(folder/'progress/commands.txt').read_text();prefix=commands.split('observe 5\n')[0]
    need('key 1 'not in prefix and 'key 8 'not in prefix and 'key 64 'not in prefix,'実正面確認前A/menu/静的北なし')
    need('observe 5\nkey 1 2\nkey 0 60\nobserve 6\n'in commands,'正面直後の最初通常A')
    need('observe 25\nkey 8 2\n'in commands,'最初町fieldから通常保存、追加移動なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    need(result['boundary']['variable_deltas']==[(0x4021,91,93),(0x4022,1,3),(0x4072,1,3)],'通常2歩と完成stage3だけ')
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save100_next_route.json').read_bytes())
