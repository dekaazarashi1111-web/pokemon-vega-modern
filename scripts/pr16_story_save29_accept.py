#!/usr/bin/env python3
"""Save29の保存原本を独立照合。native/既受入試験は再実行しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save29_measure as m
from pr16_story_after_maori import need,identity
SOURCE='33e1b9337469170adfca8af14ec4b3f298135b75'
RUN,JOB,ARTIFACT=37118447519,111189690507,11271899477
ARCHIVE=dict(size=232451,sha256='bb04e57ceb77be61b068e30e9dc88a343feb9754a7dec7c5066182ff4501f22f')
OUTPUT=dict(size=131088,sha256='780c27a138bc0795e2f30c328f69a77ded3569a9960318a61f0dc3d431f56a83')
PARTY='89668f27bceb5f63f83fd29274c74307f2b3be9c4fa4b200c903283c835f0eee'
FLASH='a37d081bc885c94a15de81127556f17b9997931d61cc1d1709b2a28e390a8457'
CP='content/modernization/pr16_story_save29_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE29_JA.md'
EVIDENCE='content/modernization/pr16_story_save29_evidence'
VISUAL='content/modernization/pr16_story_save29_visual_review.json'
shared=m.a.shared
transport=m.a.transport
parent=m.a.parent

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations']
    need(len(ao)==37 and len(bo)==2,'全39画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(88,4808) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[27,7]]*2+[[x,7]for x in range(26,17,-1)]+[[18,7],[18,6],[18,5],[18,4],[18,4]]+[[17,4]]*21
    for i,o in enumerate(ao):
        facing=1 if i==0 else 2 if 11<=i<=14 else 3
        callback=0x8055e69 if i==16 else m.m.BATTLE if 17<=i<=27 else m.m.FIELD
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==facing and
             o['party_count']==4 and o['rp']==0 and o['party_sha256']==(m.a.PARTY if i<25 else PARTY),'全位置/RP/party')
        need(o['callback2']==callback and o['lock']==(0 if i<16 or i in (28,36) else 1) and o['field'] is (i<16),
             '遭遇遷移/野生戦/保存/解錠。残留field:falseは勝利追加ではない')
        need(o['battle_flags']==(0 if i<17 else 4) and o['battle_outcome']==(0 if i<28 else 1),'野生1勝と残留outcome')
        need(o['save_counter']==(28 if i<35 else 29),'途中writeをSave29完了にしない')
        if i<32:need(o['flash_sha256']==m.a.FLASH,'通常Save前のFlash全byte不変')
        elif i<35:need(o['flash_sha256'] not in (m.a.FLASH,FLASH),'部分write3状態')
        else:need(o['flash_sha256']==FLASH,'Save29全Flash')
    need(len({ao[i]['flash_sha256']for i in (32,33,34)})==3,'別の部分write3状態')
    for o in bo:
        m.m.idle(o,29)
        need(o['xy']==[17,4] and o['facing']==3 and o['field'] is True and o['battle_flags']==o['battle_outcome']==0 and
             o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==ao[-1]['ledger_sha256'],'独立Continue全状態')
    return dict(status='PASS_CAVE_WEST_HIGH_WILD_SAVE29_SCOPED',trainer_victories=0,wild_victories=1,escapes=0,captures=0,
        wild_species_ja='ディグダ',wild_level=8,ordinary_saves=1,save_counter=29,map=[1,73],xy=[17,4],facing=3,party_count=4,rp=0,
        encounter_transition=16,battle_start=17,victory_field_return=28,save_success_text_observation=35,stable_field_observation=36,
        partial_write_observations=[32,33,34],progress_inputs=88,continue_inputs=13,screen_count=39,native_processes=2,
        record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,
        hm05_taught_or_used=False,trainer352_accepted=False,trainer353_accepted=False,teleport_accepted=False,cave_crossing_complete=False,
        national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def boundary(before,after,cold,rom):
    s=parent.sectors
    need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save28/29とcold全Save/RTC')
    need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,28,s.LAYOUT);new,rb=s.bank(after,0xe000,29,s.LAYOUT);_,rc=s.bank(after,0,28,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'前Save28 bank全57344byte不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,a,b)for i,(a,b)in enumerate(zip(x,y))if a!=b]
    need(changes==[(55,5,4)] and identity(y)['sha256']==PARTY,'party差分はれいとうビームPP5→4だけ')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new)
    need(bag_a==bag_b and money_a==money_b==12712,'全Bag/HM05/所持金不変')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6])
    need(not(ext[(4367-2304)//8]&(1<<((4367-2304)%8))),'flag4367まだ未解禁')
    need(struct.unpack_from('<BBHBHHBB',rom,0x214656)==(0x69,0x29,4367,0x16,0x4071,7,0x6b,2),'観測に基づく正規owner全11byte。末尾は0x6b')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new)
    vd=[(0x4000+i,a,b)for i,(a,b)in enumerate(zip(va,vb))if a!=b]
    need(fa==fb and vd==[(0x4021,68,81)],'全trainer/story flags不変、補助var4021だけ')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not ((fa[0x840//8]|fb[0x840//8])&1) and
         va[0x71]==vb[0x71]==6 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6949,1760),'全Save差分会計')
    return dict(party_changes=changes,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,
        physical_flag_deltas=[],auxiliary_var_deltas=vd,auxiliary_runtime_owners_resolved=False,old_bank_preserved_bytes=57344,
        pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,
        national_var404e=0,national_flag840=0,story_vars={'4071':6,'4072':1},badge_count=1,
        all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not (folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes())
    need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and
         measured['native_processes']==2 and measured['screen_count']==39,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed)
        e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][36] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['battle']==dict(start=17,finish=28,trainer=False,outcome=1,used=[0,0,0,1],decisions=[dict(observation=24,move_slot=3)]),
         '実技画面かられいとうビーム1回')
    need(measured['route']==m.ROUTE[:13] and measured['teleport'] is None,'野生開始は17,4。静的残経路は未到達')
    inspection=json.loads((folder/'inspection.json').read_bytes())
    need(inspection==measured['inspection'] and inspection['route']==m.ROUTE and inspection['owner_operands']==dict(first_opcode=105,setflag_opcode=41,flag=4367,setvar_opcode=22,variable=16497,value=7,release_opcode=107,end_opcode=2),'固定ROMの観測owner。staticを解禁扱いしない')
    old=json.loads((folder/'preflight-failure.json').read_bytes());need(old['native_processes']==0 and old['run_id']==37118280803,'初回preflight失敗保持')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE)
    return result

