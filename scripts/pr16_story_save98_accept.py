#!/usr/bin/env python3
"""町北connection Save98の独立受入。失敗原本と歩行owner証拠を保存。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save98_measure as m
from pr16_story_after_maori import need,identity
SOURCE='9b85267460cd408236d11e36f0926c40910ee418'
RUN,JOB,ARTIFACT=37195535335,111416503730,11300996343
ARCHIVE=dict(size=349489,sha256='cec6d1ff249b110924b24ff9e1130b199752bd84b509e00f5b65cdd27cd919f7')
OUTPUT=dict(size=131088,sha256='af8190f911ef0e182b22860531c8d0f1a160a57556600a16044edcfca8553cec')
PARTY='a889748859f118b98c42e9ef5f0fd2847466d07383f5743946453c961261580d'
FLASH='4fe01d76fcabc9e13ef688bb45fff03687e1b902361c6216e459435da866f630'
LEDGER='59e3a1446f04d74258924f78a9142bf690ee04f0a8d7da17917ebd5dd436f904';COLD_LEDGER=LEDGER;SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save98_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE98_JA.md'
EVIDENCE='content/modernization/pr16_story_save98_evidence'
VISUAL='content/modernization/pr16_story_save98_visual_review.json'
OWNER='content/modernization/pr16_story_save98_walk_owner.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace=m.a.trace;trace_rows=m.a.trace_rows;ROUTE=m.ROUTE
POSITIONS=[[19, 26], [19, 26], [20, 26], [21, 26], [22, 26], [23, 26], [23, 26], [23, 25], [23, 24], [23, 23], [23, 22], [23, 21], [23, 20], [23, 19], [23, 18], [23, 17], [23, 16], [23, 15], [23, 14], [23, 13], [23, 12], [23, 11], [23, 11], [24, 11], [25, 11], [25, 11], [25, 10], [25, 9], [25, 9], [26, 9], [27, 9], [28, 9], [28, 9], [28, 8], [28, 7], [28, 6], [28, 5], [28, 4], [28, 3], [28, 2], [28, 1], [28, 0], [28, 39]]
FACING=[1, 4, 4, 4, 4, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 2, 2, 2, 4, 4, 4, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
FLASH_PHASES=['5a7ca01cd6c1f4fa417dddc306daf75664f28558f023efba13bc5026bdcd4939', '7f98f7bb7089a50cc7171941e203f94587d9fe8d1379d248c994f49cd59713e3', 'ae90ee96e0f0fc61b057f2bd43c496c8290e6c2f20b735d79309ed1942921bc9', '9d8b8f8ebc320db355d5acb8a2fb2506a7b16d3ad368851be8d39fb1c9cca41a', '64b3f930bfd6514984a4994790ea38107e06f992feb2356691fdc72f3e56d355', '16935e9693ec7e6a654bac781e62497149cfcfea89aba204433dce9d6deeed36', '7505f4e95bf1f1ef3b228d921d556e79217f8b8574b019fe957b453ed55ca77d', '0acdc8c5f8387750e0d9893a7f8f1c24489ef840e6e6d76c6de3aee1c7eeba1f', '76a5ee9559e003e5032da5bc42da6024d3925d0766eb0d5b6ca05b39414ef107', 'fca6d0948ad0f9c7287ae087f9e34fcfa90ad179568b097ee8bb76e401f22cf7', '235a09c88ff5866479f0c6cb7b3d457d75497f7ddfc6f09159d79ebabc24c01e', '5eea849c32bbbe5e5481dd8860e25c01e043278c89ad5d147bfe2992d55f1947']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==67 and len(bo)==2,'全69画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(128,4810)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新35歩/旋回6/北connection1歩/128+cold13入力')
    for i,o in enumerate(ao):
        xy=POSITIONS[i]if i<43 else[28,39];where=[3,2]if i<42 else[3,23];field=i<43 or i==66;facing=FACING[i]if i<43 else 2
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'新35歩/6旋回、28,0から通常北connectionで28,39北')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'42最初道路field→43menu→66clearfield')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==(m.a.PARTY if i<8 else PARTY),'6歩目の128step周期からfriendship3byteだけ変化')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<42 else LEDGER),'connection42でRAM ledger変化。全体ownerは未解明、以後/cold保持')
        need(o['save_counter']==(97 if i<62 else 98),'62counter98/最終hashでも成功文言は63')
        wanted=m.a.FLASH if i<50 else FLASH_PHASES[i-50]if i<62 else FLASH
        need(o['flash_sha256']==wanted,'50〜61部分保存、62安定最終hash、63成功文言')
    need(len(set(FLASH_PHASES))==12 and FLASH not in FLASH_PHASES,'部分hashと最終hashを区別')
    need(ao[62]['save_counter']==98 and ao[62]['flash_sha256']==FLASH and not ao[62]['field']and not ao[63]['field'],'counter/hash単独を保存成功にしない。62blank→63成功→66clearfield')
    for o in bo:
        m.idle(o,98);need(o['map']==[3,23]and o['xy']==[28,39]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame/SaveRTC/party/settledRAM保持')
    return dict(status='PASS_TOWN_NORTH_CONNECTION_SAVE98_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=98,map=[3,23],map_name_ja='505番道路',xy=[28,39],facing=2,party_count=4,rp=0,travel_steps=35,connection_steps=1,turns=6,blocked_movement_inputs=0,npc_wait_inputs=0,directional_stair_activation_inputs=0,directional_exit_activation_inputs=0,warps=0,map_connections=1,town_north_connection_accepted=True,automatic_entry_step_observed=False,ranger_interaction_accepted=False,letter_handoff_accepted=True,paper_consumed_or_delivered=True,paper_item_quantity=0,museum_exit_previously_accepted=True,museum_fee=0,museum_admission_var4061=1,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_pp_consumption=[0,0,0,0],party_unchanged=False,party_bytes_preserved=597,party_changed_observations=[8],party_byte41_common_mechanism_resolved=True,individual_random_branch_pc_trace_captured=False,prior_raw_unresolved_notes_preserved=True,progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[42],ram_difference_owner_resolved=False,flag2056_runtime_owner_resolved=False,auxiliary_common_mechanism_resolved=True,save_counter_changed_observation=62,counter_change_not_save_completion=True,partial_write_observations=list(range(50,62)),first_final_flash_observation=62,stable_final_flash_observation=62,early_finalhash_not_completion=True,save_in_progress_observations=list(range(50,62)),blank_before_success_observation=62,stable_hash_not_alone_save_completion=True,save_success_text_observation=63,save_success_wording_observed=True,stable_field_observation=66,progress_field_screen_clear=True,progress_final_success_overlay_visible=False,progress_inputs=128,continue_inputs=13,screen_count=69,native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=1,total_new_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=True,progress_to_cold_pixels_identical=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(41,48,49),(141,13,14),(241,111,112)],'friendshipの3byte各+1だけ。HP/PP/EXP/持物保持');return d
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'全legacy flags保持。physical2056と過去owner未解明は別');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save97/98と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,97,s.LAYOUT);new,rb=s.bank(after,0,98,s.LAYOUT);_,rc=s.bank(after,0xe000,97,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save97全bank57344byte保持')
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
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,122,30),(0x4022,4,0)],'36歩とmod128/mod5の歩数owner。受付4061=1保持')
    need(va[0x61]==vb[0x61]==1,'受付支払済4061保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7074,1780),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=597,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=0,paper_delivered=True,paper_flag4382_preserved=True,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[],unresolved_variable_owners=[],resolved_walk_counter_variables=[0x4021,0x4022],auxiliary_runtime_owners_resolved=True,individual_random_branch_pc_trace_captured=False,museum_fee=0,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

SNOW_RECTS=[[53,15,58,20],[27,131,32,136],[222,52,226,55],[152,103,156,106],[147,33,151,36],[67,70,71,73]]
def screen_comparison(frames):
    def pixels(raw):
        need(raw[:15]==b'P6\n240 160\n255\n'and len(raw)==115215,'実PPM');return [raw[i:i+3]for i in range(15,len(raw),3)]
    ims=list(map(pixels,frames));counts=[]
    for i,j in[(0,1),(0,2),(1,2)]:
        diff=[(k%240,k//240)for k,(x,y)in enumerate(zip(ims[i],ims[j]))if x!=y];counts.append(len(diff))
        need(all(any(x0<=x<=x1 and y0<=y<=y1 for x0,y0,x1,y1 in SNOW_RECTS)for x,y in diff),'snow粒子6矩形だけ。主人公/地形/overlay保持')
    need(counts==[128,128,0],'progress/cold差128px、cold間全pixel一致')
    return dict(progress_final_success_overlay_visible=False,progress_to_cold_changed_pixels=counts[:2],cold_changed_pixels=counts[2],snow_particle_rectangles=SNOW_RECTS,all_pixels_identical=False,cold_pixels_identical=True)

def walk_owner(rom,boundary_result):
    proof=json.loads((ROOT/OWNER).read_bytes());need(proof['candidate']==identity(rom),'歩行owner固定ROM')
    for row in proof['bindings']:need(rom[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'歩数/field offset全ROMbyte')
    need(proof['common_mechanism_resolved']is True and proof['individual_random_branch_pc_trace_captured']is False and proof['every_historical_occurrence_traced']is False,'共通機構解決と個々の乱数trace未採取を区別')
    need(proof['fields']['mon_data32']=='FRIENDSHIP'and proof['mechanism']['happiness']['function']==0x806cf40 and proof['mechanism']['poison']['function']==0x806cf90,'固定owner')
    need((122+36)%128==30 and(4+36)%5==0 and boundary_result['variable_deltas']==[(0x4021,122,30),(0x4022,4,0)],'全36歩を独立算術照合')
    need(boundary_result['party_byte_deltas']==[(41,48,49),(141,13,14),(241,111,112)],'native通常saveで診断preimage3byteを確認')
    return dict(proof=OWNER,common_mechanism_resolved=True,save98_party_field_owner_resolved=True,save98_auxiliary_variable_owners_resolved=True,individual_random_branch_pc_trace_captured=False,every_historical_occurrence_traced=False,rom_bindings=len(proof['bindings']))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==69,'測定identity')
    parsed={}
    for lane,seed in[('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][66]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新35歩/通常connectionだけ。戦闘/会話0')
    need(measured['frontier']==dict(kind='new_town_north_connection',source_edge=[28,0],edge_observation=41,map=[3,23],xy=[28,39],facing=2,observation=42),'北端41の実画面を確保して42最初道路fieldだけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+43:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in['progress/screen-0066.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need([identity(x)['sha256']for x in frames]==['0dd28350b03b243c2799b3c1fc26a9c8a31da7c3ef7f104e7b42f5f9a06ae037', '8060223adc49b81dec6613449f9e574c0085be5faaa720cb064b9f117fe0c92b', '8060223adc49b81dec6613449f9e574c0085be5faaa720cb064b9f117fe0c92b'],'最終field/cold全3原画');result['screen_comparison']=screen_comparison(frames)
    need(measured['town_north_connection_observed']is True and measured['town_north_connection_accepted']is False and measured['ranger_interaction_observed']is False,'測定時未受入原本を改作しない。Ranger会話0')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']==m.inspect(rom,before),'静的35歩/方向/通常connection全byte')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result['walk_owner']=walk_owner(rom,result['boundary']);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def failed_approach(folder):
    folder=Path(folder);p=trace(folder/'progress',m.a.OUTPUT);o=p['observations'];e=json.loads((folder/'progress/execution.json').read_bytes());f=json.loads((folder/'failure.json').read_bytes())
    need(len(o)==9 and p['end']['inputs']==28 and p['end']['frames']==1838 and e['initial_save']==e['final_save']==m.a.OUTPUT and e['returncode']==0,'失敗native1/28入力9画面。Save97全byte保持')
    need(f['native_processes']==1 and f['message']=='初境界まで全partyとflash保持'and f['run_id']==37195233466 and f['source_head']=='c8312b3a0d7ddacb42825f9a60140612bce34eb3','元失敗を保持')
    for i,x in enumerate(o):need(x['map']==[3,2]and x['xy']==POSITIONS[i]and x['save_counter']==97 and x['field']is True and x['party_sha256']==(m.a.PARTY if i<8 else PARTY)and x['flash_sha256']==m.a.FLASH and x['battle_flags']==x['battle_outcome']==0,'新6歩目のparty変化で停止。保存/戦闘/接続0')
    need(not list(folder.rglob('*.srm')),'未変更入力Save97は再配布しない')
    return dict(status='FAILED_PARTY_GUARD_RETAINED_NOT_ACCEPTED',native_processes=1,inputs=28,frames=1838,observations=9,ordinary_saves=0,save_rtc_unchanged=True)

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save98_next_route.json').read_bytes())
