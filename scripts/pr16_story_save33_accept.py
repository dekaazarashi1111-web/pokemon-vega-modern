#!/usr/bin/env python3
"""Save33の正規teleport保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save33_measure as m
from pr16_story_after_maori import need,identity
SOURCE='73741f547eba9bb5519afb22c37d524416a9beb9'
RUN,JOB,ARTIFACT=37122926665,111202448744,11273622658
ARCHIVE=dict(size=215872,sha256='bb0733bdf3894d364fbaf96eba893d9f5b9d79797da136aad57cf01292b0ae24')
OUTPUT=dict(size=131088,sha256='ceb55e1df60f35b69f4854017afa19d703df987c602c3a0f6b0090c2323e0685')
PARTY=m.a.PARTY
FLASH='a3b80c00146ed207a952fb769081092b14d581a4816f9004f9210063f1e5ff07'
CP='content/modernization/pr16_story_save33_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE33_JA.md'
EVIDENCE='content/modernization/pr16_story_save33_evidence'
VISUAL='content/modernization/pr16_story_save33_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='2ce3858d05996f0b5f6ccc31a82005673239225aa440a4babc87e3954255540b'
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==29 and len(bo)==2,'全31画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(69,3454) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[21,19],[22,19],[23,19],[23,19],[23,18],[23,17],[23,16],[23,15],[23,14],[23,13],[23,13],[22,13],[21,13],[21,13],[21,14],[21,14],[20,14],[19,14]]+[[8,10]]*11
    faces=[4,4,4,2,2,2,2,2,2,2,3,3,3,1,1,3,3,3,1]+[3]*10
    for i,o in enumerate(ao):
        field=i<17 or i in(19,28)
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==faces[i],'全移動/向き・東階段/転送')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if field else 1) and o['field']is field,'teleportと保存のlock/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY,'戦闘0/party全byte不変')
        need(o['save_counter']==(32 if i<26 else 33),'sector counter先行を全保存完了にしない')
        need(o['ledger_sha256']==LEDGER,'ledger全観測不変')
        if i<23:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<27:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'部分write4状態・counter33でも未完')
        else:need(o['flash_sha256']==FLASH,'Save33全Flash')
    need(len({ao[i]['flash_sha256']for i in(23,24,25,26)})==4,'別の部分write4状態')
    for o in bo:
        m.m.idle(o,33)
        need(o['xy']==[8,10] and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_CAVE_UNLOCKED_TELEPORT_SAVE33_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=33,map=[1,73],xy=[8,10],facing=3,party_count=4,rp=0,
        east_stair_accepted=True,stair_observation=8,upper_stair_observation=9,teleport_accepted=True,accepted_teleport=dict(trigger=[19,14],destination=[8,10],flag4367=1),west8_10_teleport_accepted=True,
        trigger_observation=17,destination_observation=18,unlocked_destination=19,save_success_text_observation=27,stable_field_observation=28,partial_write_observations=[23,24,25,26],progress_inputs=69,continue_inputs=13,screen_count=31,native_processes=2,
        record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,trainer360_accepted=False,cave_crossing_complete=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save32/33とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,32,s.LAYOUT);new,rb=s.bank(after,0xe000,33,s.LAYOUT);_,rc=s.bank(after,0,32,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save32bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need(x==y and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==13128,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);flag=(ext[(4367-2304)//8]>>((4367-2304)%8))&1;need(flag==1,'正規解禁flag4367保持')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);need(fa==fb,'全trainer/story flags不変')
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,103,115),(0x4022,0,2)],'補助var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==0 and not(fa[0x840//8]&1) and va[0x71]==vb[0x71]==7 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    raw=rom[0x214661:0x214661+30]
    need(struct.unpack_from('<BBHBBI',raw)==(0x69,0x2b,4367,6,1,0x08214675),'先頭lock/checkflag/goto_if1の独立実byte')
    need(struct.unpack_from('<BBBBHHBB',raw,10)==(0x3d,1,73,0x99,27,7,0x6d,2) and struct.unpack_from('<BBBBHHBB',raw,20)==(0x3d,1,73,0x99,8,10,0x6d,2),'両warp命令/設定済側8,10')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6970,1779),'全Save差分会計')
    return dict(party_unchanged_bytes=600,pp=[1,14,0,0],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=[],variable_deltas=vd,auxiliary_runtime_owners_resolved=False,flag4367=flag,old_bank_preserved_bytes=57344,pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':7,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==31,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][28] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==dict(trigger=[19,14],destination=[8,10],observation=19) and measured['route']==m.ROUTE+[[8,10]] and measured['battle']is None and measured['story_event']is None,'東階段/実teleportだけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection'] and inspection['route']==m.ROUTE and inspection['expected_teleport']==[8,10],'保存静的原本と実測区別')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
