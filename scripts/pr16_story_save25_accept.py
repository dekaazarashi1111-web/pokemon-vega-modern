#!/usr/bin/env python3
"""Save25保存済み原本の独立受入。native/旧試験の再実行0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save25_measure as m
from pr16_story_after_maori import need,identity
SOURCE='61d71820e6df2bc2a16f4fa9102f4aed18c1edaa'
RUN,JOB,ARTIFACT=37112730069,111173640445,11270560918
ARCHIVE=dict(size=223647,sha256='887b0cc82df68a993c74229dfe060ce647392deed55c3a3723e780782437c9d3')
OUTPUT=dict(size=131088,sha256='4a92a1d2a36c1b74fa7ba211a9b3a815d63c04582fd34b117a5c3af16828a68f')
PARTY='43e3d4ce485bbfd695efdd02d442aa6aaa85bd71a0637ce87837ec6f483cff69'
FLASH='229705ac328d5a4db804aee79d4897a72364db5bc444ddf6f7fcbcea91ce0a09'
CP='content/modernization/pr16_story_save25_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE25_JA.md'
EVIDENCE='content/modernization/pr16_story_save25_evidence'
VISUAL='content/modernization/pr16_story_save25_visual_review.json'
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations']
    need(len(ao)==40 and len(bo)==2,'全42画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(94,7489) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    hashes=[(0,m.a.d.m.prior.parent.PARTY),(12,'fabad4e4c7204ff11e5497e03cd58b2628a73c0b1afe795032579cdf27d73c7d'),
            (19,'240560353a8659bd48923555f47c27269a20d37f1dd009258eaff93a8dcb53fc'),(26,PARTY)]
    for i,o in enumerate(ao):
        xy=[31,4+i] if i<3 else [31,7]
        expected_party=next(value for n,value in reversed(hashes) if i>=n)
        need(o['map']==[1,73] and o['xy']==xy and o['live_xy']==[x+7 for x in xy] and
             o['facing']==1 and o['party_count']==4 and o['rp']==0 and o['party_sha256']==expected_party,'位置/RP/party全byte')
        need(o['callback2']==(m.BATTLE if 5<=i<=30 else m.FIELD) and
             o['lock']==(0 if i<3 or i in (31,39) else 1) and o['field'] is (i<3 or i in (31,39)),'戦闘/台詞/Saveとfield境界')
        need(o['battle_flags']==(0 if i<5 else 12) and o['battle_outcome']==(0 if i<28 else 1),'新勝利と残留outcomeを区別')
        need(o['save_counter']==(24 if i<38 else 25),'部分writeを成功にしない')
        if i<35:need(o['flash_sha256']==m.a.FLASH,'通常Save前の全Flash不変')
        elif i<38:need(o['flash_sha256'] not in (m.a.FLASH,FLASH),'部分書込3画面')
        else:need(o['flash_sha256']==FLASH,'Save25全Flash')
    need(len({ao[i]['flash_sha256'] for i in (35,36,37)})==3,'部分write3状態を保持')
    for o in bo:
        m.idle(o,25)
        need(o['xy']==[31,7] and o['facing']==1 and o['field'] is True and o['battle_flags']==o['battle_outcome']==0 and
             o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==ao[-1]['ledger_sha256'],'fresh Continue全状態')
    return dict(status='PASS_CAVE_TRAINER351_SAVE25_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,
                ordinary_saves=1,save_counter=25,trainer=351,physical_trainer_bit=1631,reward_yen=416,
                map=[1,73],xy=[31,7],facing=1,party_count=4,rp=0,battle_start=5,victory_outcome=28,unlocked_return=31,
                save_success_text_observation=38,stable_field_observation=39,partial_write_observations=[35,36,37],
                progress_inputs=94,continue_inputs=13,screen_count=42,native_processes=2,record_native_processes=0,
                accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,
                hm05_taught_or_used=False,teleport_accepted=False,cave_crossing_complete=False,national_dex_unlocked=False,
                natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)
def boundary(before,after,cold,rom):
    p=m.a.d.m.prior.parent;s=p.sectors
    need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save24/25と全cold/RTC一致')
    need(identity(rom)==m.a.d.m.shared.plan.CANDIDATE,'候補不変')
    old,ra=s.bank(before,0,24,s.LAYOUT);new,rb=s.bank(after,0xe000,25,s.LAYOUT);_,rc=s.bank(after,0,24,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'Save24 bank全57344byte不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,a,b) for i,(a,b) in enumerate(zip(x,y)) if a!=b]
    need(changes==[(54,5,2)] and identity(y)['sha256']==PARTY,'party600byte差分は火炎放射PP3だけ')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=p.shared.bag(before,old);bag_b,money_b=p.shared.bag(after,new)
    need(bag_a==bag_b and (money_a,money_b)==(12296,12712),'Bag/HM05保持・実報酬416')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    p.s61e_record(after[new[13]+0x7d0:new[13]+0xde6])
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new)
    fd=[(8*i+j,(a>>j)&1,(b>>j)&1)for i,(a,b)in enumerate(zip(fa,fb))for j in range(8)if (a^b)&(1<<j)]
    vd=[(0x4000+i,a,b)for i,(a,b)in enumerate(zip(va,vb))if a!=b]
    need(fd==[(1631,0,1)] and vd==[(0x4021,38,40),(0x4022,3,0)],'trainer bit1/補助var2だけ')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not ((fa[0x840//8]|fb[0x840//8])&1) and
         va[0x71]==vb[0x71]==6 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    remap=rom[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==s.TABLE_SHA,'既存remap固定')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]));need(mapping.get(351+0x500,351+0x500)==1631,'root trainerの保存bit')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6928,1746),'全Save差分会計')
    return dict(party_changes=changes,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,
                physical_flag_deltas=fd,auxiliary_var_deltas=vd,auxiliary_runtime_owners_resolved=False,old_bank_preserved_bytes=57344,
                pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),
                national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':6,'4072':1},badge_count=1,
                all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))
def verify(folder,before,rom):
    folder=Path(folder);need(not (folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes())
    need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and
         measured['native_processes']==2 and measured['screen_count']==42,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=m.a.d.m.shared.trace(folder/lane,seed)
        e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'原本正常終端')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'新Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][39] and measured['continued']==parsed['continue']['observations'][1],'全field原本照合')
    need(measured['battle']==dict(start=5,finish=31,trainer=True,outcome=1,used=[0,0,3,0],decisions=[
        dict(observation=11,move_slot=2),dict(observation=15,keep_current=True),dict(observation=18,move_slot=2),
        dict(observation=22,keep_current=True),dict(observation=25,move_slot=2)]),'実画面技3回/交代拒否2回')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=m.a.d.m.shared.plan.CANDIDATE)
    return result
