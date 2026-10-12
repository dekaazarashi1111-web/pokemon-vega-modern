#!/usr/bin/env python3
"""Save43の504西上段/trainer114・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save43_measure as m
from pr16_story_after_maori import need,identity
SOURCE='7bccc0c52b4232e8c4f98a81e5ed86ff73c97c57'
RUN,JOB,ARTIFACT=37133664958,111233658951,11277619007
ARCHIVE=dict(size=543573,sha256='2a595f712c4779e6af3b921ef4ea4dae40d1296c1ede9d32e65bb5400b7c9af3')
OUTPUT=dict(size=131088,sha256='80d9c9387937173a62283f1164cb6ff035ebd39eaa38f78a779da92691ae788f')
PARTY='0724edad5126a1371abd014118267751edcde4c54b920da3549cc3828fa1e1a6'
FLASH='17ed011c15ba32229670c231290e77488547805e1bad2521df9fca840abb5056'
CP='content/modernization/pr16_story_save43_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE43_JA.md'
EVIDENCE='content/modernization/pr16_story_save43_evidence'
VISUAL='content/modernization/pr16_story_save43_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
PARTIES=[(0, '2177b4bbc36333b233a8a6e9d13eccb725421cd83f2ec641a1ec6d66a3f67d39'), (21, '2e155380a8551e54f912efbee4452ba25aac94dc75ca35d1c33863db2e1ba603'), (24, '228be34fa5c9f804b5e6e0112a96556da94e4e898f9ec4fd83ff25232a9ebdb3'), (26, '974aa4f4eb88d27a8ec840b49ebe6ca7b44b25aef6174374ce183ae685afb44c'), (33, '82dc3a57f7154c33bda6fe6c2b11c4c9a36a9da727b3925a6b6ed6ba0327eb17'), (38, 'c46da0bf1c02fac8b44e660e1656459a5696e9ebfdfb5b587e31cf6d5f36c086'), (42, 'bfcec3c220529b27c4b2074aa6070bc9c136682c15e6c01dff7f6fe549b7d381'), (49, 'a82890b0127ba0cd6c9b2be29ff0f46317b91c3d64ea8d5a44eb684f14690ed2'), (57, '0724edad5126a1371abd014118267751edcde4c54b920da3549cc3828fa1e1a6')]
LEDGERS=[(0, '7a0eb126f868227ffd18a5a2c776246c41194f69d437a834570c1964e4a5f117'), (7, 'b5733f59d5e57b7d1fadd5dd3ea1478a56fb62ae403fe7b5ceac1000c684fd7e'), (31, '7e02955b33acc483a931f330fd3ca887b65db838b39ebab795bab8fae61c7bc4'), (51, '7d8ac5c85ad718b9f0dd16de19bc3020c5ed2c448451bc32d0d6efd70f3dbaf3')]
LEDGER=LEDGERS[-1][1]
trace=m.a.trace

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==88 and len(bo)==2,'全90画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(170,12428)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[47,13],[46,13],[46,13],[46,12],[46,12]]+[[x,12]for x in range(45,39,-1)]+[[39,12]]*77
    for i,o in enumerate(ao):
        face=2 if i in(2,3)else 3;field=i<11 or i in(63,87)
        party=next(v for n,v in reversed(PARTIES)if i>=n);ledger=next(v for n,v in reversed(LEDGERS)if i>=n)
        need(o['map']==[3,44]and o['xy']==xy[i]and o['live_xy']==[v+7 for v in xy[i]]and o['facing']==face,'上段西進とtrainer視線の全座標')
        need(o['callback2']==(m.m.BATTLE if 14<=i<=62 else m.m.FIELD)and o['lock']==(0 if field else 1)and o['field']is field,'視線/戦闘/保存/field境界')
        need(o['party_count']==4 and o['rp']==0 and o['party_sha256']==party and o['ledger_sha256']==ledger,'実party/全RAM ledger・RP0')
        need(o['battle_flags']==(0 if i<14 else 12)and o['battle_outcome']==(0 if i<60 else 1),'trainer1勝だけ・残留outcomeは追加勝利ではない')
        need(o['save_counter']==(42 if i<83 else 43),'counter43だけ')
        if i<71:need(o['flash_sha256']==m.a.FLASH,'Save前Flash全byte不変')
        elif i<83:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'71〜82は部分write')
        else:need(o['flash_sha256']==FLASH,'83全Flash後84成功文言・87field')
    need(len({ao[i]['flash_sha256']for i in range(71,83)})==12,'12部分writeを分離')
    for o in bo:
        m.idle(o,43);need(o['xy']==[39,12]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_ROUTE504_UPPER_TRAINER114_SAVE43_SCOPED',trainer_victories=1,trainer_id=114,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=43,map=[3,44],xy=[39,12],facing=3,party_count=4,rp=0,upper_west_partial_accepted=True,west_descent_stairs_accepted=False,remaining_upper_route_accepted=False,cave_crossing_complete=True,
        encounter_transition=11,battle_start=14,battle_outcome_observation=60,victory_field_return=63,move_selections=6,actual_pp_consumed=[1,5,0,0],remaining_pp=[0,0,0,0],normal_recovery_required=True,
        save_success_text_observation=84,save_success_wording_observed=True,stable_full_flash_observation=83,save_counter_changed_observation=83,stable_field_observation=87,partial_write_observations=list(range(71,83)),
        progress_inputs=170,continue_inputs=13,screen_count=90,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,
        hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120,'全legacy flags')
    fd=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(fa,fb))for j in range(8)if(u^v)&(1<<j)]
    need(fd==[(1280+114,0,1)],'trainer114既定勝利flag1394だけ');return fd

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save42/43とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,42,s.LAYOUT);new,rb=s.bank(after,0xe000,43,s.LAYOUT);_,rc=s.bank(after,0,42,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save42bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v]
    need(changes==[(52,1,0),(53,5,0),(86,64,58)]and identity(y)['sha256']==PARTY,'party全600byte・PP0/HP314だけ')
    modeled=bytearray(x)
    for (_,expected),(off,val) in zip(PARTIES[1:],[(53,4),(86,59),(53,3),(53,2),(86,58),(53,1),(53,0),(52,0)]):
        modeled[off]=val;need(identity(bytes(modeled))['sha256']==expected,'保存親から全8中間partyを独立再構成')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and (money_a,money_b)==(13796,14264),'全Bag/HM05不変・通常報酬468円')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,96,104),(0x4022,1,0)],'補助var2件だけ・runtime owner未解決')
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot
    w=ScriptWalker(RomImage('save43-trainer114-owner',rom));w.add_root(ScriptRoot(154581891,'route504_local3','object'));graph=w.walk()
    trainers=[r['value']for r in graph['references']if r['category']=='trainer'and r['access']=='battle']
    need(not graph['diagnostics']and 114 in trainers,'保存map local3 scriptからtrainer114正規owner・新nodeだけ')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6881,1710),'全Save差分会計')
    return dict(party_changes=changes,trainer_owner=graph,pp=[0,0,0,0],hp=[314,354],reward_yen=468,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==90,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業Save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][87]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    decisions=[dict(observation=i,move_slot=slot)for i,slot in [(20,1),(25,1),(32,1),(41,1),(48,1),(56,0)]]
    decisions+= [dict(observation=i,keep_current=True)for i in(29,45,52)];decisions.sort(key=lambda x:x['observation'])
    need(measured['battle']==dict(start=14,finish=63,trainer=True,outcome=1,used=[1,5,0,0],decisions=decisions),'はどうだん5/サイコブレイク1・通常4体撃破/交代拒否3')
    for d in decisions:
        expected=('moves',d['move_slot'])if 'move_slot'in d else('shift',None)
        need(m.m.classify((folder/'progress'/f"screen-{d['observation']:04d}.ppm").read_bytes())==expected,'全選択実画面')
    need(measured['teleport']==[]and measured['route']==m.ROUTE[:10],'最初のtrainer114までだけ・下り階段未到達')
    need(measured['frontier']==dict(kind='new_battle',trigger=[39,12],map=[3,44],xy=[39,12],observation=63),'新戦闘後に停止')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+64:04d}.ppm').read_bytes())==i,'menu実cursor0→4の各行')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['stairs']==dict(xy=[26,11],elevation=0,collision=0,behavior=42)and inspection['candidate_levels']==[4]*27+[0,3],'静的候補と実通過範囲を区別')
    need(all(inspection[x]==0 for x in('new_map_views','new_terrain_cells','new_script_nodes')),'保存済地形再採取0')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
