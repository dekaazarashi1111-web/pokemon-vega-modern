#!/usr/bin/env python3
"""trainer160通常勝利のSave83原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save83_measure as m
from pr16_story_after_maori import need,identity
SOURCE='73ed1d12284202767179653e77e642a92c2dbaf6'
RUN,JOB,ARTIFACT=37177597798,111363381549,11293763616
ARCHIVE=dict(size=306071,sha256='587f00bf6078a0e022171ddc8bf20282601c456e533165e1bfe76a70911780f5')
OUTPUT=dict(size=131088,sha256='157a945e7bdb3287b519c235ef95c12ddcefb14a62d479cf3a5f753e4f009523')
PARTY='28ca40b7dc0c1dae14aa85904af5ecb6eb427a233ed2ae82f24a5392a1294975'
FLASH='086d90a506d60b09c21b3c24bf3ccb0bbeafe2928ddbf390ed8b6876c2d69ac2'
LEDGER='e382ce75f68b45a15b115e180061d194a24c0697fd7824204bd61eea61ecd84d';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save83_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE83_JA.md'
EVIDENCE='content/modernization/pr16_story_save83_evidence'
VISUAL='content/modernization/pr16_story_save83_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=m.ROUTE[:6]
FLASH_PHASES=['27a4a1a0850f5eb5a6030c0afb5cdbee8e4d50ef9dc40006726ca14e61bad6df', '7fd767e4b150bd8d38ed81e08fc147eb8a2823cf914f1a470e3e86d4d03de028', '4d697e9a6546c088a43e5a2b7c49596ced0dca9f2e2df6638e80d1068261d404', '0e10a144e2a564fa92fbb7e0b7fbd745f9d76941c860fc5a50641042aeb983d4', 'b4ec3ac3b84b960ad68be51f09d70dffe8d7ab9971d4ec7333316c130ecbcd64', '7c3f26fe6bf7cda07388be8883ba7ad71a6c2adf0eb1254e460a981a0d6a6eb6', '0239a20fcb4baaba37f50e662e84ff9127813558ade51630abe04e5f253e28bd', '8997c7813e0d74df83608838791b8e499495fc8163bb82b5df5303211b1e3848', '054b2cb8e159e8841e1cbe4e09701cde106d3275db3aba5ca34dce939ff258a6', 'b50d35dc93551f682623015961eb3246b52291b164bd84ad69de74c496d6cc21']
trace=m.a.trace
trace_rows=m.a.trace_rows

PARTIES=['4b9010788bbab20cf9807e17c5f722c17bbbf2e608f24d9f06740ce758ebbae3', 'c133525c7e366e322b769f7bf951aa75e621cdaa795267501f55518203e19c22', '422554525f36c7a23e257cdc543de068464094fc75dcce12c13e21b22cae4525', '054fac4ad4b854660d4bd82958759412765981ed2e6a802edce4456892138c68', 'a72ed03be337daf251f0129bb164c42f3273a539eb347ef5d7a87c33b3aaa87b', '28ca40b7dc0c1dae14aa85904af5ecb6eb427a233ed2ae82f24a5392a1294975']
TRANSIENT_LEDGER='673526c8224d61667ac6c914e4d479e6fce8529e4d240c504f97cce8c4312388'
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==68 and len(bo)==2,'全70画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(132,9771)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新東5歩/trainer160/保存132+cold13入力')
    for i,o in enumerate(ao):
        xy=[6,7]if i<2 else[i+5,7]if i<=6 else[11,7];field=i<6 or i in(45,67);cb=m.m.BATTLE if 9<=i<=44 else m.m.FIELD
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==(2 if i==0 else 4),'東5歩と11,7東の戦闘/保存だけ。未入力の北4歩と区別')
        need(o['callback2']==cb and o['field']is field and o['lock']==int(not field),'視線/接近台詞/戦闘/保存とfieldを分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(12 if i>=9 else 0)and o['battle_outcome']==int(i>=42),'敵4体をtrainer1勝として計上')
        party=PARTIES[0 if i<16 else 1 if i<23 else 2 if i<24 else 3 if i<33 else 4 if i<40 else 5]
        ledger=m.a.COLD_LEDGER if i<17 else TRANSIENT_LEDGER if i<38 else LEDGER
        need(o['party_sha256']==party and o['ledger_sha256']==ledger,'DragonClaw2/BrickBreak2と1HP減の実party段階。RAM17/38差分owner未解明')
        need(o['save_counter']==(82 if i<62 else 83),'62counter83でも保存中。63成功/67fieldを分離')
        wanted=m.a.FLASH if i<53 else FLASH_PHASES[i-53]if i<63 else FLASH
        need(o['flash_sha256']==wanted,'全10部分保存。63最終hash/成功文言')
    need(len(set(FLASH_PHASES))==10 and FLASH not in FLASH_PHASES,'counter83だけで保存完了としない')
    for o in bo:
        m.idle(o,83);need(o['map']==[10,16]and o['xy']==[11,7]and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame後。勝利残留はreset')
    return dict(status='PASS_GYM_TRAINER160_SAVE83_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=83,map=[10,16],map_name_ja='ミルジム',xy=[11,7],facing=4,party_count=4,rp=0,travel_steps=5,turns=1,gym_entry_previously_accepted=True,fifth_diglett_previously_accepted=True,trainer132_previously_accepted=True,sixth_diglett_event_accepted=False,gym_puzzle_completed=False,gym_leader_defeated=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,
        trainer_id=160,physical_trainer_bit=1440,trainer_class_ja='たんぱんこぞう',trainer_name_ja='トラジ',trainer_party=[['ライノス',22],['レクオレ',23],['ファイマー',23],['リーティン',24]],reward_yen=384,lead_species=850,lead_hp=[287,294],lead_pp=[4,10,12,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[2,0,2,0],observed_pp_consumption=[2,0,2,0],move_commands=4,target_confirmations=0,keep_current_choices=3,move_commands_not_automatically_pp_uses=True,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,
        progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[17,38],ram_difference_owner_resolved=False,old_save77_cold_difference_owner_resolved=False,old_save78_progress_difference_owner_resolved=False,old_save80_progress_difference_owner_resolved=False,old_save82_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=62,counter_change_not_save_completion=True,partial_write_observations=list(range(53,63)),stable_hash_not_alone_save_completion=True,save_success_text_observation=63,save_success_wording_observed=True,stable_field_observation=67,progress_inputs=132,continue_inputs=13,screen_count=70,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False,npc_runtime_object_id_resolved=False,npc_south_adjacent_visible=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(52,6,4),(54,14,12),(86,32,31)],'実PP2byteとHP1byteだけ。EXP/持物保持')
    copy=bytearray(x);copy[52]=4;copy[54]=12;copy[86]=31;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d

def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(1440,0,1)],'trainer160物理bit1440だけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save82/83と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,82,s.LAYOUT);new,rb=s.bank(after,0xe000,83,s.LAYOUT);_,rc=s.bank(after,0,82,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save82全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    for (pp0,pp2,hp),wanted in zip([(6,14,288),(5,14,288),(5,14,287),(4,14,287),(4,13,287),(4,12,287)],PARTIES):
        copy=bytearray(x);copy[52],copy[54]=pp0,pp2;struct.pack_into('<H',copy,86,hp);need(identity(bytes(copy))['sha256']==wanted,'全PP/HP段階partyの独立再構成')
    remap=rom[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==s.TABLE_SHA,'固定trainer remap')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]));need(mapping.get(160+0x500,160+0x500)==1440,'trainer160→物理1440')
    need(rom[154587296-0x08000000:154587310-0x08000000].hex()=='5c00a0000000fd4f210823502108','既読gym local3 trainerbattle160 owner')
    need(list(y[52:56])==[4,10,12,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(287,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and (ma,mb)==(20280,20664),'全Bag/全5pocket保持と賞金384円');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'全S61E payload保持。今回switch入力なし')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4376,4378))for f in range(4372,4379)},'local10非表示/local9復帰/初回flag保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,111,115)],'aux4021だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==0,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and not(fb[2083//8]&(1<<(2083%8))),'badge1/ナギナタbadge未取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7168,1847),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=597,party_byte_deltas=pd,pp=[4,10,12,2],hp=[287,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists()and not(folder/'stopped.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==70,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][67]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE,'新東5歩だけ。北4歩未入力')
    need(measured['battle']=={'start': 9, 'finish': 45, 'trainer': True, 'outcome': 1, 'move_commands': [2, 0, 2, 0], 'target_confirmations': 0, 'actual_pp_uses_not_inferred': True, 'decisions': [{'observation': 15, 'move_slot': 0}, {'observation': 19, 'keep_current': True}, {'observation': 22, 'move_slot': 0}, {'observation': 28, 'keep_current': True}, {'observation': 32, 'move_slot': 2}, {'observation': 36, 'keep_current': True}, {'observation': 39, 'move_slot': 2}]},'選択4/交代拒否3/実PP4の区別')
    need(measured['frontier']==dict(kind='new_battle',trigger=[11,7],map=[10,16],xy=[11,7],observation=45),'最初のtrainer160新勝利直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+46:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    for i in [15,22,31]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',0),'実ドラゴンクローcursor')
    for i in [32,39]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',2),'3PP予約後かわらわりcursor2')
    for i in [19,28,36]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())[0]=='shift','実交代確認画面だけ取消')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0045.ppm','progress/screen-0067.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='0eb741d97a7960056dd6583c4d4009a0570c2d354b65d2058000ead0856cbb1a','trainer南隣/通常field/freshContinue全pixel一致')
    need(measured['trainer132_previously_accepted']is True and measured['sixth_diglett_interacted']is False and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持のtrainer160勝利だけ。第6未入力')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定第6ownerは未入力。新trainer160は実入力/保存bitと別照合')
    need(inspection['initial_flags']=={str(f):int(f in(4376,4378))for f in range(4372,4379)}and inspection['instruction_count']==39 and inspection['text_count']==2,'第6限定39命令/2台詞は静的のまま')
    need(inspection['expected_flag_changes']==[[4374,0,1],[4376,1,0]],'switch予測を観測差分にしない')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save83_next_route.json').read_bytes())



