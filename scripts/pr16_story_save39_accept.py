#!/usr/bin/env python3
"""Save39の503西端から504東端・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save39_measure as m
from pr16_story_after_maori import need,identity
SOURCE='442449ed7b8eb4453820de744aa938a22309f411'
RUN,JOB,ARTIFACT=37128394742,111218333230,11276165710
ARCHIVE=dict(size=264597,sha256='78fb4fd98f03cb822947f2361747c56bbfa945cfc30b6bef1a19a24e85180dcb')
OUTPUT=dict(size=131088,sha256='2cc5e239b0e32951a9c5b68375b1b78318be6d5d11389a1e1a898f16b7bda720')
PARTY=m.a.PARTY
FLASH='f272d2c19377900b29ddafa91e3f172599293030658d31ef74e01d367c55f5cf'
CP='content/modernization/pr16_story_save39_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE39_JA.md'
EVIDENCE='content/modernization/pr16_story_save39_evidence'
VISUAL='content/modernization/pr16_story_save39_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='a42b7de819dcb559b39e870697fd51b376d8955e5025164a64d3355f4b02af8c'
COLD_LEDGER='95d109f9df4c120c3343661ca2c130f17047761f4ef8a01bc4b9e05456073a26'
trace=m.a.trace
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==37 and len(bo)==2,'全39画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(67,3224)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    motion=[[9,76]]*2+[[x,76]for x in range(8,-1,-1)]+[[71,9]]*26
    for i,o in enumerate(ao):
        xy=motion[i];field=i<12 or i==36
        need(o['map']==([3,21]if i<11 else[3,44])and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==(1 if i==0 else 3),'503西端→504東端の全座標')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if field else 1)and o['field']is field,'全menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER,'戦闘0/party/進行RAM ledger不変')
        need(o['save_counter']==(38 if i<31 else 39),'counter世代境界')
        if i<19:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i in range(19,30)or i==31:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'部分write12状態')
        else:need(o['flash_sha256']==FLASH,'30は一時一致、32以降だけ安定')
    need(len({ao[i]['flash_sha256']for i in list(range(19,30))+[31]})==12,'部分write12状態を分離')
    for o in bo:
        m.idle(o,39);need(o['map']==[3,44]and o['xy']==[71,9]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==COLD_LEDGER,'独立Continue全状態・RAM ledger差を明示')
    return dict(status='PASS_ROUTE503_TO_504_SAVE39_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=39,map=[3,44],xy=[71,9],facing=3,party_count=4,rp=0,outside_route503_reached=True,west_connection_accepted=True,route504_reached=True,cave_crossing_complete=True,save_success_text_observation=32,save_success_wording_observed=True,transient_final_hash_observation=30,transient_hash_reverted_observation=31,stable_full_flash_observation=32,stable_field_observation=36,partial_write_observations=list(range(19,30))+[31],progress_inputs=67,continue_inputs=13,screen_count=39,native_processes=2,prior_failed_native_processes=1,total_development_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=COLD_LEDGER,cold_ram_ledger_owner_resolved=False)

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120 and fa==fb,'全legacy flags不変')
    return []

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save38/39とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,38,s.LAYOUT);new,rb=s.bank(after,0xe000,39,s.LAYOUT);_,rc=s.bank(after,0,38,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save38bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need(x==y and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==13796,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);flag=(ext[(4367-2304)//8]>>((4367-2304)%8))&1;need(flag==1,'正規解禁flag4367保持')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,30,40)],'歩数補助var1件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==8 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6785,1672),'全Save差分会計')
    return dict(party_unchanged_bytes=600,pp=[1,5,0,0],hp=[320,354],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,flag4367=flag,old_bank_preserved_bytes=57344,pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':8,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==39,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][36] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==m.ROUTE and measured['battle']is None,'戦闘0/西接続だけ')
    need(measured['frontier']==dict(kind='west_connection',trigger=[-1,76],map=[3,44],xy=[71,9],observation=11),'通常connection実到達')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+12:04d}.ppm').read_bytes())==i,'実画面menu0→4を毎行確認')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_connection_accepted']is False,'静的候補を本nativeで初受入')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
