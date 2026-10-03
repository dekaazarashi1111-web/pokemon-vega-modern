#!/usr/bin/env python3
"""Save34の西側北辺未通過・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save34_measure as m
from pr16_story_after_maori import need,identity
SOURCE='c181dc2610d01db9a29a9dc46edd6c8bb0ac0b46'
RUN,JOB,ARTIFACT=37123621651,111204455124,11274397555
ARCHIVE=dict(size=155597,sha256='ca68c211b1310c02031eee089a37506be85c7f56d7413fe5d5e805084ae42d38')
OUTPUT=dict(size=131088,sha256='c90cde2874e2c9a13b96c990c3907326bea066bb22a6bd61ae71b63ae5419692')
PARTY=m.a.PARTY
FLASH='a55791b29640039a7bafa37c5337fbabb962362d277bd2365ce7c42657402dcb'
CP='content/modernization/pr16_story_save34_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE34_JA.md'
EVIDENCE='content/modernization/pr16_story_save34_evidence'
VISUAL='content/modernization/pr16_story_save34_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
OLD_LEDGER='2ce3858d05996f0b5f6ccc31a82005673239225aa440a4babc87e3954255540b'
LEDGER='760ebe5defe9a83563038a5b280a7afd6a6f33df77423f2f6a1987944299fcbe'
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==18 and len(bo)==2,'全20画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(50,2766) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[8,10],[8,10],[9,10],[9,10],[9,9],[9,8]]+[[9,7]]*12
    faces=[3,4,4]+[2]*15
    for i,o in enumerate(ao):
        field=i<10 or i==17
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==faces[i],'全移動/向き・北辺未通過')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if field else 1) and o['field']is field,'通常保存のlock/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY,'戦闘0/party全byte不変')
        need(o['save_counter']==(33 if i<16 else 34),'sector counter先行を全保存完了にしない')
        need(o['ledger_sha256']==(OLD_LEDGER if i<4 else LEDGER),'warm ledger原本の観測境界。RP稼得へ昇格しない')
        if i<13:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<17:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'部分write4状態・counter34でも未完')
        else:need(o['flash_sha256']==FLASH,'Save34全Flash')
    need(len({ao[i]['flash_sha256']for i in(13,14,15,16)})==4,'別の部分write4状態')
    for o in bo:
        m.m.idle(o,34)
        need(o['xy']==[9,7] and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_CAVE_WEST_FRONTIER_SAVE34_SCOPED_NORTH_BLOCKED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=34,map=[1,73],xy=[9,7],facing=2,party_count=4,rp=0,
        north_edge_traversed=False,blocked_edge=dict(before=[9,7],target=[9,6],attempt_observations=[7,8,9]),dynamic8_5_native_arrival=False,trainer360_accepted=False,teleport_accepted=False,
        save_success_text_observation=None,save_success_wording_observed=False,save_completion_basis='FULL_FLASH_SECTOR_CHECKSUMS_FIELD_RETURN_AND_INDEPENDENT_CONTINUE',stable_field_observation=17,partial_write_observations=[13,14,15,16],progress_inputs=50,continue_inputs=13,screen_count=20,native_processes=2,
        record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,cave_crossing_complete=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save33/34とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,33,s.LAYOUT);new,rb=s.bank(after,0,34,s.LAYOUT);_,rc=s.bank(after,0xe000,33,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save33bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need(x==y and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==13128,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);flag=(ext[(4367-2304)//8]>>((4367-2304)%8))&1;need(flag==1,'正規解禁flag4367保持')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);need(fa==fb,'全trainer/story flags不変')
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,115,119),(0x4022,2,1)],'補助var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==0 and not(fa[0x840//8]&1) and va[0x71]==vb[0x71]==7 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6996,1788),'全Save差分会計')
    return dict(party_unchanged_bytes=600,pp=[1,14,0,0],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=[],variable_deltas=vd,auxiliary_runtime_owners_resolved=False,flag4367=flag,old_bank_preserved_bytes=57344,pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':7,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==20,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][17] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']is None and measured['route']==m.ROUTE[:5] and measured['battle']is None,'今回転送/戦闘なし・9,7まで')
    need(measured['frontier']==dict(kind='blocked_edge',before=[9,7],target=[9,6],attempt_observations=[7,8,9],claim='NOT_TRAVERSED_SAVE_FRONTIER_ONLY'),'停止辺の原本。到達へ昇格しない')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection'] and inspection['route']==m.ROUTE and inspection['native_arrival_accepted']is False,'静的動的tile ownerと実到達を区別')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
