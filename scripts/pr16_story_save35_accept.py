#!/usr/bin/env python3
"""Save35の戻り転送・野生勝利・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save35_measure as m
from pr16_story_after_maori import need,identity
SOURCE='95edb59bcf19a560f81355aa446c3cf57bf95a62'
RUN,JOB,ARTIFACT=37124732153,111207625688,11274735081
ARCHIVE=dict(size=365141,sha256='df1e104b934c21c0577822e864eac2c42e67e38f7cb78e953f432b357215162b')
OUTPUT=dict(size=131088,sha256='df15c94737ee6511a80173215ab0edbfb3927161c7b6dbb59f9c403b4a197d98')
PARTY='b2d6497ab4a173e3090263d4032da00ca031597421323ea4a5bccc8c5f1f8cdb'
FLASH='f7a1a913619649158944ae98f16155664e0bd6010e31da2e8e220a0e56fade9f'
CP='content/modernization/pr16_story_save35_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE35_JA.md'
EVIDENCE='content/modernization/pr16_story_save35_evidence'
VISUAL='content/modernization/pr16_story_save35_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
OLD_LEDGER='760ebe5defe9a83563038a5b280a7afd6a6f33df77423f2f6a1987944299fcbe'
LEDGER='b59689eb217ecd784ea044c8aa35d51e25ece66cc4a8b254541176ba6e29a591'
PARTIES=[m.a.PARTY,'4478e580801ddc23af8da2929d5800bcfd39f85cf05c389bda548a2cc8e23caa','c8bd14cc7e041f524b644297e7fb6fba58d6fdf5ea9c19f9820154251d257528',PARTY]
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==58 and len(bo)==2,'全60画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(115,5965) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[9,7],[9,7],[9,8],[9,9],[9,10],[9,10],[8,10],[27,7],[27,7]]+[[x,7]for x in range(26,17,-1)]+[[18,7],[18,6],[18,5],[18,5],[17,5]]+[[16,5]]*35
    for i,o in enumerate(ao):
        facing=2 if i==0 or 18<=i<=20 else 1 if 1<=i<=4 or i==7 else 3
        pi=0 if i<14 else 1 if i<32 else 2 if i<35 else 3
        cb=m.TRANSITION if i==23 else 134282949 if i==24 else m.m.BATTLE if 25<=i<=37 else m.m.FIELD
        lock=1 if i in(6,7)or 23<=i<=37 or 39<=i<=56 else 0
        field=i<23 and i not in(6,7)
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==facing,'全移動/向き/戻り転送')
        need(o['callback2']==cb and o['lock']==lock and o['field']is field,'通常遷移/野生戦/残留field bool/保存の区別')
        need(o['party_count']==4 and o['rp']==0 and o['party_sha256']==PARTIES[pi],'実party全byte推移')
        need(o['battle_flags']==(0 if i<24 else 4) and o['battle_outcome']==(0 if i<38 else 1),'野生1勝のみ・残留追加なし')
        need(o['save_counter']==(34 if i<53 else 35),'counter先行を全保存完了にしない')
        need(o['ledger_sha256']==(OLD_LEDGER if i<34 else LEDGER),'warm ledgerの観測境界・RP稼得ではない')
        if i<42:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<54:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'部分write12状態')
        else:need(o['flash_sha256']==FLASH,'Save35全Flash')
    need(len({ao[i]['flash_sha256']for i in range(42,54)})==12,'別の部分write12状態')
    for o in bo:
        m.m.idle(o,35);need(o['xy']==[16,5] and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_CAVE_RETURN_WILD_SAVE35_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,ordinary_saves=1,save_counter=35,map=[1,73],xy=[16,5],facing=3,party_count=4,rp=0,
        return_teleport_accepted=True,west_stair_accepted=False,dynamic8_5_native_arrival=False,trainer360_accepted=False,
        move_selections=2,actual_pp_consumed=1,flinch_observation=32,save_success_text_observation=54,save_success_wording_observed=True,save_completion_basis='FULL_FLASH_SECTOR_CHECKSUMS_SUCCESS_TEXT_FIELD_RETURN_AND_INDEPENDENT_CONTINUE',stable_field_observation=57,partial_write_observations=list(range(42,54)),progress_inputs=115,continue_inputs=13,screen_count=60,native_processes=2,
        prior_failed_native_processes=2,total_development_native_processes=4,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,cave_crossing_complete=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save34/35とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,34,s.LAYOUT);new,rb=s.bank(after,0xe000,35,s.LAYOUT);_,rc=s.bank(after,0,34,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save34bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v]
    need(changes==[(41,6,7),(53,14,13),(86,66,64),(241,104,105)] and identity(y)['sha256']==PARTY,'全partyは4byte差分だけ・HP322→320/PP14→13')
    modeled=bytearray(x)
    for expected,changes_step in zip(PARTIES[1:],[[(41,7),(241,105)],[(86,64)],[(53,13)]]):
        for i,v in changes_step:modeled[i]=v
        need(identity(bytes(modeled))['sha256']==expected,'保存親から中間partyを独立全byte再構成')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==13128,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);flag=(ext[(4367-2304)//8]>>((4367-2304)%8))&1;need(flag==1,'正規解禁flag4367保持')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);need(fa==fb,'全trainer/story flags不変')
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,119,7),(0x4022,1,0)],'補助var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==0 and not(fa[0x840//8]&1) and va[0x71]==vb[0x71]==7 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6941,1770),'全Save差分会計')
    return dict(party_changes=changes,party_growth_byte_changes=[[41,6,7],[241,104,105]],growth_byte_runtime_owners_resolved=False,pp=[1,13,0,0],hp=[320,354],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=[],variable_deltas=vd,auxiliary_runtime_owners_resolved=False,flag4367=flag,old_bank_preserved_bytes=57344,pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':7,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==60,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][57] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[dict(trigger=[8,10],destination=[27,7],observation=8)] and measured['route']==m.ROUTE[:18],'戻り転送と17,5までの完歩')
    need(measured['battle']==dict(start=25,finish=38,trainer=False,outcome=1,used=[0,2,0,0],decisions=[dict(observation=31,move_slot=1),dict(observation=34,move_slot=1)]),'技選択2回・ひるみを実消費2へ昇格しない')
    need(measured['frontier']==dict(kind='new_battle',trigger=[16,5]),'野生戦だけ・8,5未到達')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection'] and inspection['route']==m.ROUTE and inspection['native_arrival_accepted']is False,'動的tileの静的ownerと実到達は区別')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
