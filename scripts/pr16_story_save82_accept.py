#!/usr/bin/env python3
"""trainer132通常勝利のSave82原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save82_measure as m
from pr16_story_after_maori import need,identity
SOURCE='e98ad40624e04de8842dc19f5601ce28f125749e'
RUN,JOB,ARTIFACT=37176546268,111360218777,11292834696
ARCHIVE=dict(size=288486,sha256='b48fdb05b06fa6bfcd90b0921ca8b3db2574c1e214563170831f4fbdc5fa7208')
OUTPUT=dict(size=131088,sha256='ba090d0e6efe1f7d3effba4991973bd956574f18780fa7843ccf4910748ec8e9')
PARTY='4b9010788bbab20cf9807e17c5f722c17bbbf2e608f24d9f06740ce758ebbae3'
FLASH='a90ec93f42daa9a11b9d92ef8d49a099d03df08994db27d9648ccd629a2bba46'
LEDGER='6199945914d24e030f34c686f8669e1aa876204442debe8effd0276998871567';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save82_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE82_JA.md'
EVIDENCE='content/modernization/pr16_story_save82_evidence'
VISUAL='content/modernization/pr16_story_save82_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE
FLASH_PHASES=['0bfda578bd99feaf725ce2e8e680428a7e4b3b4c76382dcb634b83c4b45940d3', '58b706ba46c1316ea577a5d67367eb1c8a477e8c93b45851d6c8182b8e5936ad', '9b95020c205f250382d0547f3ace2c305dcc695676b5ee72e7753549f097eef1', '12016194de89e57e4a573186042f65d707b635a8a482b6b164a7b3e22e86dc9d', '499334b3090b46a9de7c780bed8adb99480ab057a047d19b692bd84cdc2971b1', '282515247b91ca456b914024e3fb1292b45d8486d8ca6b5b6901f5dc93ecd2ea', '1f869fe166428eeb788f33f0c6cc95295ca59a9f6b06abcebd0ca21a31a9bcad', '35950cb8830268ef54c632c78c995cfe54e4566796198cc8580f3d35ff56dff4', '374c2f45f6f2fb00e7790e27bc651c391bbd8ec86b9bc9b0cb2c201f5d93bea9', 'ea2c8b631ab28ecafa563fa272d54809366e4373312c58d40ef1aab9547d5ae9']
trace=m.a.trace
trace_rows=m.a.trace_rows

PARTIES=['39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82', '42f933505a76211e76fea233b3e4660c3c6740fac50948c7ae23573d04cd03b4', '550e4cff5c1e747fa0cf64f47e7ed1c5ca4faa0303e83f7b9480fdb4d870289b', 'bd6be190dc437624582fe59e9890bece60bd31f7a8e5c463f77180393d07e85b', '4b9010788bbab20cf9807e17c5f722c17bbbf2e608f24d9f06740ce758ebbae3']
TRANSIENT_LEDGER='8a5a8a26d6b86463419aa26785e697d2e783f5fafb11fe1adc51d4d0758006f7'
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==61 and len(bo)==2,'全63画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(118,9001)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新北2歩/trainer132/保存118+cold13入力')
    for i,o in enumerate(ao):
        xy=[6,9-i]if i<2 else[6,7];field=i<2 or i in(38,60);cb=m.m.BATTLE if 5<=i<=37 else m.m.FIELD
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==2,'北2歩と6,7北の戦闘/保存だけ')
        need(o['callback2']==cb and o['field']is field and o['lock']==int(not field),'視線/接近台詞/戦闘/保存とfieldを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(12 if i>=5 else 0)and o['battle_outcome']==int(i>=35),'敵4体をtrainer1勝として計上')
        party=PARTIES[0 if i<11 else 1 if i<18 else 2 if i<25 else 3 if i<33 else 4]
        ledger=m.a.COLD_LEDGER if i<13 else TRANSIENT_LEDGER if i<34 else LEDGER
        need(o['party_sha256']==party and o['ledger_sha256']==ledger,'ドラゴンクロー3/かわらわり1の実party段階、RAM13/34差分owner未解明')
        need(o['save_counter']==(81 if i<55 else 82),'55counter82でも保存中。56成功/60fieldを分離')
        wanted=m.a.FLASH if i<46 else FLASH_PHASES[i-46]if i<56 else FLASH
        need(o['flash_sha256']==wanted,'全10部分保存。56最終hash/成功文言')
    need(len(set(FLASH_PHASES))==10 and FLASH not in FLASH_PHASES,'counter82だけで保存完了としない')
    for o in bo:
        m.idle(o,82);need(o['map']==[10,16]and o['xy']==[6,7]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame後。勝利残留はreset')
    return dict(status='PASS_GYM_TRAINER132_SAVE82_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=82,map=[10,16],map_name_ja='ミルジム',xy=[6,7],facing=2,party_count=4,rp=0,travel_steps=2,turns=0,gym_entry_previously_accepted=True,fifth_diglett_previously_accepted=True,gym_puzzle_completed=False,gym_leader_defeated=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,
        trainer_id=132,physical_trainer_bit=1412,trainer_class_ja='やまおとこ',trainer_name_ja='ヤスハル',trainer_party=[['サイホーン',22],['ゴビット',23],['コジオ',23],['ワンリキー',24]],reward_yen=864,lead_species=850,lead_hp=[288,294],lead_pp=[6,10,14,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[3,0,1,0],observed_pp_consumption=[3,0,1,0],move_commands=4,target_confirmations=0,keep_current_choices=3,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,
        progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[13,34],ram_difference_owner_resolved=False,old_save77_cold_difference_owner_resolved=False,old_save78_progress_difference_owner_resolved=False,old_save80_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=55,counter_change_not_save_completion=True,partial_write_observations=list(range(46,56)),stable_hash_not_alone_save_completion=True,save_success_text_observation=56,save_success_wording_observed=True,stable_field_observation=60,progress_inputs=118,continue_inputs=13,screen_count=63,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False,npc_runtime_object_id_resolved=False,npc_west_adjacent_visible=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(52,9,6),(54,15,14)],'実PP2byteだけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[52]=6;copy[54]=14;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d

def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(1412,0,1)],'trainer132物理bit1412だけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save81/81と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,81,s.LAYOUT);new,rb=s.bank(after,0,82,s.LAYOUT);_,rc=s.bank(after,0xe000,81,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save81全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    for pp,wanted in zip([(9,15),(8,15),(7,15),(6,15),(6,14)],PARTIES):
        copy=bytearray(x);copy[52],copy[54]=pp;need(identity(bytes(copy))['sha256']==wanted,'全4実PP段階partyの独立再構成')
    remap=rom[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==s.TABLE_SHA,'固定trainer remap')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]));need(mapping.get(132+0x500,132+0x500)==1412,'trainer132→物理1412')
    need(rom[154584484-0x08000000:154584498-0x08000000].hex()=='5c0084000000384f21085d4f2108','既読gym local1 trainerbattle132 owner')
    need(list(y[52:56])==[6,10,14,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and (ma,mb)==(19416,20280),'全Bag/全5pocket保持と賞金864円');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'全S61E payload保持。今回switch入力なし')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4376,4378))for f in range(4372,4379)},'local10非表示/local9復帰/初回flag保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,110,111),(0x4022,2,0)],'aux4021/4022だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==0,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and not(fb[2083//8]&(1<<(2083%8))),'badge1/ナギナタbadge未取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7172,1846),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=598,party_byte_deltas=pd,pp=[6,10,14,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists()and not(folder/'stopped.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==63,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][60]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE,'新北2歩だけ')
    need(measured['battle']==dict(start=5,finish=38,trainer=True,outcome=1,move_commands=[3,0,1,0],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=10,move_slot=0),dict(observation=14,keep_current=True),dict(observation=17,move_slot=0),dict(observation=21,keep_current=True),dict(observation=24,move_slot=0),dict(observation=28,keep_current=True),dict(observation=32,move_slot=2)]),'選択4/交代拒否3/実PP4の区別')
    need(measured['frontier']==dict(kind='new_battle',trigger=[6,7],map=[10,16],xy=[6,7],observation=38),'最初のtrainer132新勝利直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+39:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    for i in [10,17,24,31]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',0),'実ドラゴンクローcursor')
    need(m.classify((folder/'progress/screen-0032.ppm').read_bytes())==('moves',2),'3PP予約後かわらわりcursor2')
    for i in [14,21,28]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())[0]=='shift','実交代確認画面だけ取消')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0038.ppm','progress/screen-0060.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='a1c2c5259752fe5be43e6ccfda455818b50fb6b8480caa28b3ae4574e0385277','trainer西隣/通常field/freshContinue全pixel一致')
    need(measured['fifth_diglett_previously_accepted']is True and measured['trainer132_approach_measured']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持のtrainer勝利だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定trainer132ownerを実入力/保存bitと照合')
    need(inspection['initial_flags']=={str(f):int(f in(4376,4378))for f in range(4372,4379)}and inspection['instruction_count']==5 and inspection['text_count']==3,'trainer132限定5命令/3台詞')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save82_next_route.json').read_bytes())


