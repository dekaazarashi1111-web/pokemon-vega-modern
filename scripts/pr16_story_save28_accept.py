#!/usr/bin/env python3
"""Save28の正規teleport保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save28_measure as m
from pr16_story_after_maori import need,identity
SOURCE='1cc88ec763b69ada00bc4f5da4b5c632c5ccd9c8'
RUN,JOB,ARTIFACT=37117145212,111186021028,11271154923
ARCHIVE=dict(size=127600,sha256='43f98cdb2823fce7c34fbb76f439b3ffd26a900ddf9cee8c394567129a1b95ed')
OUTPUT=dict(size=131088,sha256='a5cfc5714bcc447550d78ff45f42c74109f12d607bad1d94dbf61fe96b06f4a4')
PARTY=m.a.PARTY
FLASH='aeeb39f7fba8d5e056afce8d1fa61ecc056fd590a4c092be4abf906ccbf2bc71'
CP='content/modernization/pr16_story_save28_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE28_JA.md'
EVIDENCE='content/modernization/pr16_story_save28_evidence'
VISUAL='content/modernization/pr16_story_save28_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
OLD_LEDGER='50ba3fdcc36f077af96d2d61a5f101e0d7302f080e3ed26b8eba59390b22ea83'
LEDGER='2547b0fee32fe13ebdf70bc2e29724ed30f1895e0448e3f5ea1a408fda604fae'
OWNER=dict(root=136398433,flag_id=4367,flag_value=0,condition=1,branch_taken=False,fallthrough_destination=[27,7],branch_destination=[8,10],expected_destination=[27,7])

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==15 and len(bo)==2,'全17画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(40,2462) and (pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    xy=[[19,13]]*2+[[19,14]]*2+[[27,7]]*11;faces=[3,1,2,3,3,3]+[1]*9
    for i,o in enumerate(ao):
        need(o['map']==[1,73] and o['xy']==xy[i] and o['live_xy']==[v+7 for v in xy[i]] and o['facing']==faces[i],'全移動/向き')
        need(o['callback2']==m.m.FIELD and o['lock']==(0 if i in (0,1,6,14)else 1) and o['field']is(i in (0,1,6,14)),'teleportと保存のlock/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY,'戦闘0/party全byte不変')
        need(o['save_counter']==(27 if i<13 else 28),'途中writeとSave28を区別')
        need(o['ledger_sha256']==(OLD_LEDGER if i<14 else LEDGER),'warm ledger更新時点。冷起動と終端を区別')
        if i<10:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<13:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'部分write3状態')
        else:need(o['flash_sha256']==FLASH,'Save28全Flash')
    need(len({ao[i]['flash_sha256']for i in(10,11,12)})==3,'別の部分write3状態')
    for o in bo:
        m.m.idle(o,28)
        need(o['xy']==[27,7] and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_CAVE_COORD19_TO27_SAVE28_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=28,map=[1,73],xy=[27,7],facing=1,party_count=4,rp=0,teleport_accepted=True,accepted_teleport=dict(trigger=[19,14],destination=[27,7],flag4367=0),west8_10_teleport_accepted=False,trigger_observation=2,destination_observation=4,unlocked_destination=6,save_success_text_observation=13,stable_field_observation=14,partial_write_observations=[10,11,12],progress_inputs=40,continue_inputs=13,screen_count=17,native_processes=2,failed_preflight_native_processes=0,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,development_controller_rechecks=16,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,trainer353_accepted=False,cave_crossing_complete=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save27/28とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,27,s.LAYOUT);new,rb=s.bank(after,0,28,s.LAYOUT);_,rc=s.bank(after,0xe000,27,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save27bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need(x==y and identity(y)['sha256']==PARTY,'party全600byte不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==12712,'全Bag/HM05/所持金')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);flag=(ext[(4367-2304)//8]>>((4367-2304)%8))&1;need(flag==0,'未解禁flag4367')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);need(fa==fb and va==vb,'全trainer/story flagsと全vars不変')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==0 and not(fa[0x840//8]&1) and va[0x71]==6 and va[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    raw=rom[0x214661:0x214661+30]
    need(struct.unpack_from('<BBHBBI',raw)==(0x69,0x2b,4367,6,1,0x08214675),'先頭lock/checkflag/goto_if1の独立実byte')
    need(struct.unpack_from('<BBBBHHBB',raw,10)==(0x3d,1,73,0x99,27,7,0x6d,2) and struct.unpack_from('<BBBBHHBB',raw,20)==(0x3d,1,73,0x99,8,10,0x6d,2),'両warp命令/未設定側27,7')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6916,1743),'全Save差分会計')
    return dict(party_unchanged_bytes=600,pp=[1,14,0,5],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=[],variable_deltas=[],flag4367=flag,old_bank_preserved_bytes=57344,pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':6,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==17,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=shared.trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][14] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==dict(trigger=[19,14],destination=[27,7],observation=6) and measured['owner']==OWNER==json.loads((folder/'coord-owner.json').read_bytes()),'実teleportと独立owner')
    for file,run in [('preflight-failure.json',37116752441),('preflight-failure-2.json',37116959565)]:
        e=json.loads((folder/file).read_bytes());need(e['native_processes']==0 and e['run_id']==run and e['status']=='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY','旧native0失敗を成功へ改作しない')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
