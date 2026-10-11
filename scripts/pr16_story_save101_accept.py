#!/usr/bin/env python3
"""解放後の西地域接続Save101原本を独立受入。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save101_measure as m
from pr16_story_after_maori import need,identity
SOURCE='b7e2946492948914f1bbd1079df195790d96a9e3'
RUN,JOB,ARTIFACT=37200922210,111432257138,11303305200
ARCHIVE=dict(size=217263,sha256='5b152b826e6ea90695dce99ba2744e1faa7958b4434da769e5f3a7a79f54e25b')
OUTPUT=dict(size=131088,sha256='814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149')
PARTY='a889748859f118b98c42e9ef5f0fd2847466d07383f5743946453c961261580d'
FLASH='8b44629f94877b5aac2e23ff15a903e66e19b74e236aa89e1f590849ed509b4d'
LEDGER='1a34e64cfee8f3793ea60b1736daa6df07d122390dcb69aacacf45cbffd0a229'
COLD_LEDGER='1a34e64cfee8f3793ea60b1736daa6df07d122390dcb69aacacf45cbffd0a229';SETTLED_COLD_LEDGER=COLD_LEDGER
CP='content/modernization/pr16_story_save101_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE101_JA.md'
EVIDENCE='content/modernization/pr16_story_save101_evidence'
VISUAL='content/modernization/pr16_story_save101_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace_rows=m.a.trace_rows
from pr16_story_save21_accept import screen_bytes
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
ROUTE=m.ROUTE
FLASH_PHASES=['f0974979e5a4be60a1c3a5c1410ad599ebf8939d4a9cf6284f2f568e751e1528', 'cbbcbadee1c881bc0668c15d4c9759ee81ea5e4d8d3f9a27911397da285857fe', '319e62ce587ff35d641512bda70dcb00d3d8635faf615801190b63f0daa9cc44', 'e89e2982be0794cc71eef3b9f99001884a81112fa67cb7d1ec10c69d25b6b01a', '62cd7b4903307b947c3b0ecb4836c60c756a3db240d5f5038ca99b3bf462d106', '3b79a6ccf705e693a2c9cf3501211ff5632cc8636505628d1901ca3ee7fd395e', 'b85a65d43fa328f08af40098b47b32a938c92d4dac91566b910838d45ff16c60', '6d479521f423dd396d5846ec94961db3fab1c23c9f986b51122813e28f2b3c49', 'f2211e002125254a7c92228a5e4efb6654b5469cbc190d8b2138f11aebae8802', '11204ab0eb72d70124d27694bd5812c67d6109a28d5aa397edae2c99b64f17f8', '085c8ab4d542df27a7a45731ed3d22239c9389898f50793ddfbd343c7550f995', 'daa1bd7a3415494da8bd2cda542733a3ed8939aa0d26a4bfa9f0388c2c21d717', 'e0353d9501ec2bd7cf90ee92d675818a50d1a9e21e464ae88db15df572bcc49b', '4762c1010807f3e2f5d37c3e1cca3e45056740521a8a601193873f72038c317d']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==33 and len(bo)==2,'全35画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(58,2854)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全58/cold13入力/2854/1510frames')
    for i,o in enumerate(ao):
        xy=[4,17]if i<2 else[5-i,17]if i<6 else[53,13];where=[3,2]if i<6 else[3,24];field=i<=6 or i==32
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==(2 if i==0 else 3),'4歩/1旋回/西connection5歩目')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'6新地域field→7menu→32clearfield')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER,'全party/RAM保持')
        need(o['save_counter']==(100 if i<27 else 101),'27counter101でも保存中')
        expected=m.a.FLASH if i<14 else FLASH_PHASES[i-14]if i<28 else FLASH
        need(o['flash_sha256']==expected,'全中間Flash/安定hash分離')
    need(len(set(FLASH_PHASES))==14 and FLASH not in FLASH_PHASES,'14途中hashは最終と不一致')
    need(not ao[27]['field']and ao[27]['flash_sha256']!=FLASH and not ao[28]['field']and ao[32]['field'],'counter/hash単独で保存完了にしない')
    for o in bo:
        m.idle(o,101);need(o['map']==[3,24]and o['xy']==[53,13]and o['facing']==3 and o['field']is True and o['party_sha256']==PARTY and o['ledger_sha256']==COLD_LEDGER and o['flash_sha256']==FLASH,'独立Continueの全状態')
    return dict(status='PASS_RELEASED_WEST_CONNECTION_SAVE101_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=101,map=[3,24],map_name_ja='506番道路',xy=[53,13],facing=3,party_count=4,rp=0,travel_steps=5,turns=1,warps=0,map_connections=1,west_connection_accepted=True,milestone_id='MILL_CITY_RELEASED_WEST_CONNECTION',milestone_kind='region_connection',diagnostic_frontier_completed=False,ordinary_battle_checkpoint=False,compact_battle_ledger=[],native_battle_continuation_accepted=False,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_pp_consumption=[0,0,0,0],healing_branch_taken=False,party_unchanged=True,party_bytes_preserved=600,friendship_wraps=0,happiness_counter=98,next_friendship_wrap_after_steps=30,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,progress_to_cold_ram_ledger_identical=True,prior_save100_ram_difference_owner_resolved=False,prior_ram53_42_owners_resolved=False,flag2056_runtime_owner_resolved=False,save_counter_changed_observation=27,counter_change_not_save_completion=True,stable_final_flash_observation=28,save_in_progress_observations=list(range(14,28)),save_success_text_observation=28,stable_field_observation=32,progress_inputs=58,continue_inputs=13,screen_count=35,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=COLD_LEDGER)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120 and x==y,'全legacy flags保持');return []
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save100/101と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,100,s.LAYOUT);new,rb=s.bank(after,0xe000,101,s.LAYOUT);_,rc=s.bank(after,0,100,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save100全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23114,'全Bag/5pocket/23114円保持・受付再走0');need(sum(q for item,q in ib['key_items']if item==274)==0,'封書引渡し後の空slot保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'S61E全payload保持/CRC検証')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'前回clearの4372〜4378全保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==1 and(eb[259]>>4)&1==1 and(ea[256]&1)==(eb[256]&1)==1,'expanded4383/4382/4380/4352保持');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,93,98)],'通常接続を含む5歩、mod5は3→3、story4072=3保持')
    need(va[0x61]==vb[0x61]==1,'受付支払済4061保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==3 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7128,1807),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=0,paper_delivered=True,paper_flag4382_preserved=True,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[],unresolved_variable_owners=[],resolved_walk_counter_variables=[0x4021,0x4022],auxiliary_runtime_owners_resolved=True,individual_random_branch_pc_trace_captured=False,museum_fee=0,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=dict(ef,**{'4352':1,'4380':1,'4382':1,'4383':1}),expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':3},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

FLOWER_TILES={(12,0),(12,1),(12,9),(13,2),(13,3),(13,7),(13,8),(13,9),(14,0),(14,7),(14,8)}
def screen_comparison(frames):
    def pixels(raw):
        need(raw[:15]==b'P6\n240 160\n255\n'and len(raw)==115215,'実PPM');return[raw[i:i+3]for i in range(15,len(raw),3)]
    ims=list(map(pixels,frames));counts=[]
    for i,j in[(0,1),(0,2),(1,2)]:
        diff=[(k%240,k//240)for k,(x,y)in enumerate(zip(ims[i],ims[j]))if x!=y];counts.append(len(diff))
        need(all((x//16,y//16)in FLOWER_TILES for x,y in diff),'差分は花animationの11tileだけ、主人公/通路/消失NPCの領域は保持')
    need(counts==[588,0,588],'progress/cold0は588px、cold1は全pixel一致。cold間588px')
    return dict(progress_to_cold_changed_pixels=counts[:2],cold_changed_pixels=counts[2],allowed_animated_flower_tiles=sorted([list(x)for x in FLOWER_TILES]),progress_equals_settled_cold=True,all_pixels_identical=False,cold_pixels_identical=False,player_and_cleared_road_pixels_preserved=True)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'今回成功原本')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==35,'測定identity')
    parsed={}
    for lane,seed in[('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][32]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']==[],'戦闘0/warp0/宣言済経路')
    f=measured['frontier'];need(f['kind']=='milestone_reached'and f['observation']==6 and f['edge_observation']==5 and f['xy']==[53,13]and f['map']==[3,24]and f['facing']==3,'西connection到達点')
    contract=measured['inspection']['milestone_contract'];ep=m.MilestoneEpisode(contract);ep.begin(parsed['progress']['observations'][0]);proof=ep.reach(parsed['progress']['observations'][6],dict(field_return=True,owners_resolved=True,observation_match=True,resources=dict(hp=277,pp=m.PP)),6)
    need(proof==f['milestone'],'到達点契約を独立照合')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+7:04d}.ppm').read_bytes())==i,'menu実cursor0→4')
    result['screen_comparison']=screen_comparison([(folder/n).read_bytes()for n in['progress/screen-0032.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']])
    need(measured['west_connection_observed']is True and measured['west_connection_accepted']is False and measured['native_battle_continuation_accepted']is False,'測定/独立受入/native連戦未実施を分離')
    need(json.loads((folder/'inspection.json').read_bytes())==measured['inspection']==m.inspect(rom,before),'全固定地形/connection binding')
    commands=(folder/'progress/commands.txt').read_text();prefix=commands.split('observe 6\n')[0]
    need(all('key '+str(key)+' 'not in prefix for key in[1,2,8,16,64,128]),'接続完了前は西/無入力だけ')
    need('observe 6\nkey 8 2\n'in commands,'新地域fieldから通常保存/追加移動なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save101_next_milestone.json').read_bytes())
