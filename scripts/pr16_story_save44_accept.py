#!/usr/bin/env python3
"""Save44のBag空/通常先頭交代と保存を独立照合。回復済みとは主張しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save44_measure as m
from pr16_story_after_maori import need,identity
SOURCE='aaf2d62ce3166349714eeeaff04e5f7ec630c3b1'
RUN,JOB,ARTIFACT=37135192951,111238199087,11278342404
ARCHIVE=dict(size=326897,sha256='c784ec6dfa7e27a489d5b837a8b2a632af12a46c65d3eb88214d94e7ad29fb21')
OUTPUT=dict(size=131088,sha256='c7a27be2dbcedecccc139899210415d391ee1946a70894836f80603d7cd86d1b')
PARTY='63612ff4fca6ddd0788e9182a56ba3f1570d485df671121fabaf4f5c78569726'
FLASH='157ded03414073eb890b30d2d7986ed621f9db890540ac30b3f455068e56ccd2'
LEDGER='4bc47968c1071a65f115cc64d8aa48dc2a37fcf75718360dd375f3dc7e8dfa0a'
CP='content/modernization/pr16_story_save44_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE44_JA.md'
EVIDENCE='content/modernization/pr16_story_save44_evidence'
VISUAL='content/modernization/pr16_story_save44_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent;trace=m.a.trace

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==43 and len(bo)==2,'全45画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(78,3928)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    for i,o in enumerate(ao):
        field=i in(0,17,42);cb=m.BAG_UI if i in(4,5,6)else m.PARTY_UI if 9<=i<=15 else m.m.FIELD
        need(o['map']==[3,44]and o['xy']==[39,12]and o['live_xy']==[46,19]and o['facing']==3,'全観測の同一座標・歩行0')
        need(o['callback2']==cb and o['lock']==int(not field)and o['field']is field,'通常Bag/party/menu/saveの境界')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/RP0/party4')
        need(o['party_sha256']==(m.a.PARTY if i<15 else PARTY),'通常swap15でだけpartyが変化')
        need(o['ledger_sha256']==(m.a.LEDGER if i<13 else LEDGER),'13並替選択の実RAM ledger。owner未解明')
        need(o['save_counter']==(43 if i<37 else 44),'counter44だけ。37はまだ部分write')
        if i<24:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<38:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'24〜37部分writeを成功としない')
        else:need(o['flash_sha256']==FLASH,'38成功文言/安定Flash→42field')
    need(len({o['flash_sha256']for o in ao[24:38]})==14,'14部分writeを区別')
    for o in bo:
        m.idle(o,44);need(o['facing']==3 and o['field']is True and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_NORMAL_PARTY_REORDER_SAVE44_SCOPED',save_counter=44,map=[3,44],xy=[39,12],facing=3,party_count=4,rp=0,trainer_victories=0,wild_victories=0,escapes=0,captures=0,travel_steps=0,item_uses=0,money_cost=0,ordinary_saves=1,party_order_changes=1,lead_species=850,lead_hp=[294,294],lead_pp=[15,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],pp_restored=False,normal_recovery_required=True,healing_site_reached=False,
        save_counter_changed_observation=37,stable_full_flash_observation=38,save_success_text_observation=38,save_success_wording_observed=True,stable_field_observation=42,partial_write_observations=list(range(24,38)),progress_inputs=78,continue_inputs=13,screen_count=45,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def boundary(before,after,cold,rom):
    need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save43/44と全SaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'固定ROM不変')
    s=parent.sectors;old,ra=s.bank(before,0xe000,43,s.LAYOUT);new,rb=s.bank(after,0,44,s.LAYOUT);_,rc=s.bank(after,0xe000,43,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save43bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    need(y==x[100:200]+x[:100]+x[200:]and identity(y)['sha256']==PARTY,'全600byteは個体100byteの順序交換だけ。PP/HP/EXP/技/所有者を変更しない')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ba,ma=parent.shared.bag(before,old);bb,mb=parent.shared.bag(after,new);need(ba==bb and ma==mb==14264,'全Bag/所持金不変')
    need(not any(i for i,q in ba['items'])and not any(i for i,q in ba['berries']),'回復品未所持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6])
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);need(fa==fb and va==vb,'全legacy flags/vars不変')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==9 and va[0x72]==1,'全国図鑑/story不変')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6885,1708),'全Save差分会計')
    return dict(party_permutation=[1,0,2,3,4,5],individual_bytes_preserved=True,unused_party_bytes_preserved=200,bag_unchanged=True,bag=bb,money_before=ma,money_after=mb,money_cost=0,item_consumption=0,pp_restored=False,hp_restored=False,physical_flag_deltas=[],variable_deltas=[],s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),ram_ledger_selection_owner_resolved=False)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ');measured=json.loads((folder/'measurement.json').read_bytes())
    need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==45,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業Save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][42]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['actions']==dict(bag_observations=[4,5,6],party_begin=9,swapped_observation=15,field_return=17,pp_restored=False,item_uses=0,money_cost=0,party_order_changes=1,travel_steps=0),'操作receipt全件')
    for i,cursor in [(1,0),(2,1),(3,2),(7,2),(8,1),(16,1),(18,1),(19,2),(20,3),(21,4)]:need(m.menu_index((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==cursor,'実menu全cursor')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['party_after_swap']==PARTY and inspection['no_pp_items']is True and inspection['pp_restored']is False and inspection['healing_site_reached']is False and inspection['static_south_map']['map']==[3,23],'既存Bag/party/静的南mapの限定scope')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
