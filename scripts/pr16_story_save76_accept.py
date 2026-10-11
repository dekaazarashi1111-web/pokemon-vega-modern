#!/usr/bin/env python3
"""封書badge gateと新ジム入口のSave76原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save76_measure as m
from pr16_story_after_maori import need,identity
SOURCE='3f7692f280ac745d17f810bb9c46abed5324c789'
RUN,JOB,ARTIFACT=37171285056,111344567528,11291861689
ARCHIVE=dict(size=200160,sha256='4d00a7de3010a72f5ecdb55f75ee1c4d0163ad6fb7b2ed4f57674648bb2f66f3')
OUTPUT={'size': 131088, 'sha256': '10c7d4b96e2b36db13158ba3a8d8929caabac28275e98e01a93c586b0315d836'}
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='8cbab58a6c8107826bd0fa85bb0233862d909aaaa2b19d1500ac2e1a8f38761c'
LEDGER='6270e89696f6f9772615bafcb7f2c84ad3d0d37b78444c099e04d139a4e244b0';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save76_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE76_JA.md'
EVIDENCE='content/modernization/pr16_story_save76_evidence'
VISUAL='content/modernization/pr16_story_save76_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[15, 20], [16, 20], [17, 20], [18, 20], [19, 20], [20, 20], [20, 19], [20, 18], [20, 17], [20, 16], [20, 15], [20, 14], [20, 13], [20, 12], [20, 11]]
MOTION=[([3, 2], [15, 20], 1), ([3, 2], [15, 20], 4), ([3, 2], [16, 20], 4), ([3, 2], [17, 20], 4), ([3, 2], [18, 20], 4), ([3, 2], [19, 20], 4), ([3, 2], [20, 20], 4), ([3, 2], [20, 20], 2), ([3, 2], [20, 19], 2), ([3, 2], [20, 18], 2), ([3, 2], [20, 17], 2), ([3, 2], [20, 16], 2), ([3, 2], [20, 15], 2), ([3, 2], [20, 14], 2), ([3, 2], [20, 13], 2), ([3, 2], [20, 12], 2), ([3, 2], [20, 11], 2), ([3, 2], [20, 10], 2), ([10, 16], [6, 18], 2)]
FLASH_PHASES=['584dee00632628af046562c246b0b12d315a4163543609e3fbb0d2d6a9eaf33a', 'b28ad3aca178b0e9ed4c94011e49aef59f95a0da3956d5265dbcf33625dbd20b', '8d3960512d573d6a806d15f60796080c253cd26e02118abd50390dbbbd90ec5d', '56c3931677fc859233d02af04c8a2c794593ea0f0c3ab77c23f43d1d5d3098bc', '5bb0dcb457fe56f691e8261656e69c2e2b5867fde25a94739742f3575644f098', 'da648bba88e0ab79fc4861b7cbac6cbbe4025da20e330eb1b69b60a4084c58ab', 'b657e751b6b071ba50788c49675c3fd21e1717a82737b461316cce2b0c2bec14', 'a2a8f2950dafd619b04fcb33c6fff950c1eca7608b91945194e2a0ac89bbb801', '8cbab58a6c8107826bd0fa85bb0233862d909aaaa2b19d1500ac2e1a8f38761c', 'b26cf7f5244efdbdbd38a48f49b56c83c35ea56634259fb82d86ae997bc446fd', '8cbab58a6c8107826bd0fa85bb0233862d909aaaa2b19d1500ac2e1a8f38761c']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==41 and len(bo)==2,'全43画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(77,3398)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新町歩行/ジム入口77+cold13入力')
    for i,o in enumerate(ao):
        where,xy,face=MOTION[min(i,18)]
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'14平地+北扉/2回旋回、ジム6,18北への通常進行')
        field=i<=16 or i in(18,40)
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'17扉/18到着/19menu/40安定field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.LEDGER,'全party600byte/全RAM台帳保持')
        need(o['save_counter']==(75 if i<35 else 76),'35counterでも保存文言未完')
        wanted=m.a.FLASH if i<26 else FLASH_PHASES[i-26]if i<37 else FLASH
        need(o['flash_sha256']==wanted,'34最終hash先行→35一時別hash→36成功/最終hash')
    need(FLASH_PHASES[8]==FLASH_PHASES[10]==FLASH and FLASH_PHASES[9]!=FLASH,'最終hash先行だけで保存完了としない')
    for o in bo:
        m.idle(o,76);need(o['map']==[10,16]and o['xy']==[6,18]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_LETTER_GATE_GYM_ENTRY_SAVE76_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=76,map=[10,16],map_name_ja='ミルジム',xy=[6,18],facing=2,party_count=4,rp=0,travel_steps=15,turns=2,entry_warps=1,gym_entered=True,gym_entry_observation=18,automatic_north_step_observed=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,ram_ledger_unchanged=True,ram_ledger_changed_observations=[],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=35,counter_change_not_save_completion=True,partial_write_observations=list(range(26,36)),early_final_hash_observation=34,transient_after_counter_observation=35,stable_hash_not_alone_save_completion=True,save_success_text_observation=36,save_success_wording_observed=True,stable_field_observation=40,progress_inputs=77,continue_inputs=13,screen_count=43,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,0,1)],'ジム入場でphysical2056 setのみ。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save75/76と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,75,s.LAYOUT);new,rb=s.bank(after,0,76,s.LAYOUT);_,rc=s.bank(after,0xe000,75,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save75全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,71,85),(0x4022,3,2),(0x404d,44,33)],'aux3変数だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==0,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and not(fb[2083//8]&(1<<(2083%8))),'badge1/ナギナタbadge未取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6985,1743),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381,4383]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==43,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][40]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'14平地歩と扉warp、新戦闘0')
    need(measured['frontier']==dict(kind='new_gym_entry',map=[10,16],xy=[6,18],facing=2,observation=18),'最初のジム到着後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+19:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0040.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='24e4b55b590ee5e8196148d7f7491256b8116a68b365a02e612c7e4297c23cfe','ジムfield/freshContinue全pixel一致')
    need(measured['gym_entered']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常ジム入場だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False,'固定新入口ownerを実入力と照合')
    planned=json.loads((ROOT/m.PREP).read_bytes());need(inspection['entry']==planned['route_owner']['town_warp']and inspection['arrival']==planned['route_owner']['arrival'],'町20,10→gym warp1')
    need(inspection['new_terrain_cells']==0 and inspection['consumer']==[6,1]and inspection['consumer_local_id']==2 and inspection['required_badge_flag']==2083 and inspection['required_badge_present']is False,'消費者/gate照合とnative引渡しは分離')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save76_gym_route.json').read_bytes())
