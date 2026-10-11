#!/usr/bin/env python3
"""封書badge gateと新ジム入口のSave77原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save77_measure as m
from pr16_story_after_maori import need,identity
SOURCE='4f11ebcc0481013051cf83c092fabc7737915b2f'
RUN,JOB,ARTIFACT=37172406819,111347883827,11291697564
ARCHIVE=dict(size=145360,sha256='89e54745a9599cc5f81ae8bca48dcb5f0e30da85e4dd7536121bd8bced5fb321')
OUTPUT=dict(size=131088,sha256='11632f541a4c8b6a7782c32b5e30b0c4c9414a8cc4323da0e263e6454cc867e6')
PARTY='39106a1e9a02c23433b376ad2a467b39df00d08854d241472355e0f6b337eb82'
FLASH='d3de224f91333e022626261d482a066f56985f988c9c8eac14d039738f6b68de'
LEDGER='6270e89696f6f9772615bafcb7f2c84ad3d0d37b78444c099e04d139a4e244b0';COLD_LEDGER=LEDGER
SETTLED_COLD_LEDGER='6027627107d4372b8f105caf2e5afbeafe1fe86b6d34bfb2a1931e0e3628f5bf'
CP='content/modernization/pr16_story_save77_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE77_JA.md'
EVIDENCE='content/modernization/pr16_story_save77_evidence'
VISUAL='content/modernization/pr16_story_save77_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[6,18],[6,17],[6,16],[6,15],[6,15]]
FLASH_PHASES=['949e3305af83244747e32e9cc4ee9fe5a7b0ce962298ccf78415b657157e56a5', 'ce6e0be6c6df86d1f957ed2f2eea769014af4927b465e60984535361449aade2', 'e6c31bd4710989114847de9dc084aee47778aefbe6435c930965cd4bab19aee1', '0eeb353ed3a038bd8765390029b6000c9ec7bdd5f100482742c11d116d5b23d6', '2d909618e95e4a4b06dd1b42108ccc5d32706042ca69772092e2a9ef14879b37', 'e00f02a738d046ab3e2e8e56a7ea3cd287b7beb61eb44663c375673df11966ea', 'b6e63d6bc866112200e2860255e1816a0ab76130f297ae7d4bdeae4aa5bc1814', '787e6365f7a4e99af21efa5d01177185881cff421192f6155fcebc40c7cbfe5b', 'b4bf5734e5dfdf1ba694cce955d26b3349452dd292d27987b314684df4282c69', 'd3de224f91333e022626261d482a066f56985f988c9c8eac14d039738f6b68de', '87897a717a83284fec68574d8e04e223b7f5fededb623f3d4b72c0ea5f6c6067', 'd3de224f91333e022626261d482a066f56985f988c9c8eac14d039738f6b68de']
trace=m.a.trace
trace_rows=m.a.trace_rows

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==29 and len(bo)==2,'全31画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(54,2860)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新北3歩/初ディグダ54+cold13入力')
    for i,o in enumerate(ao):
        xy=[6,18-min(i,3)];field=i<=3 or i in(6,28)
        need(o['map']==[10,16]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==2,'新北3歩のみ/北向き')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'4台詞/5配置変更/6field/7menu/28field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.LEDGER,'progress全party600byte/全RAM台帳保持')
        need(o['save_counter']==(76 if i<24 else 77),'24counterでも保存文言未完')
        wanted=m.a.FLASH if i<14 else FLASH_PHASES[i-14]if i<26 else FLASH
        need(o['flash_sha256']==wanted,'23最終hash先行→24一時別hash→25成功/最終hash')
    need(FLASH_PHASES[9]==FLASH_PHASES[11]==FLASH and FLASH_PHASES[10]!=FLASH,'最終hash先行だけで保存完了としない')
    for i,o in enumerate(bo):
        m.idle(o,77);need(o['map']==[10,16]and o['xy']==[6,15]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==(LEDGER if i==0 else SETTLED_COLD_LEDGER)and o['flash_sha256']==FLASH,'独立Continue・120frame後RAM hash差分を明示')
    return dict(status='PASS_FIRST_DIGLETT_EVENT_SAVE77_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=77,map=[10,16],map_name_ja='ミルジム',xy=[6,15],facing=2,party_count=4,rp=0,travel_steps=3,turns=0,gym_entry_previously_accepted=True,first_diglett_event_accepted=True,first_diglett_local_id=5,first_diglett_hidden=True,gym_puzzle_completed=False,gym_leader_defeated=False,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=False,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[288,294],lead_pp=[9,10,15,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[dict(lane='continue',observation=1)],cold_ram_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,save_counter_changed_observation=24,counter_change_not_save_completion=True,partial_write_observations=list(range(14,25)),early_final_hash_observation=23,transient_after_counter_observation=24,stable_hash_not_alone_save_completion=True,save_success_text_observation=25,save_success_wording_observed=True,stable_field_observation=28,progress_inputs=54,continue_inputs=13,screen_count=31,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=SETTLED_COLD_LEDGER,double_target_separation_native_exercised=False,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'physical flags全保持/初ディグダはexpandedだけ');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save76/77と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,76,s.LAYOUT);new,rb=s.bank(after,0xe000,77,s.LAYOUT);_,rc=s.bank(after,0,76,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save76全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[9,10,15,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==19416,'全Bag/全5pocketと所持金保持');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(258,7,23),(259,160,164)],'S61Eの4372/4378だけset')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):int(f in(4372,4378))for f in range(4372,4379)},'初ディグダだけ消え初回済み')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,85,88),(0x4022,2,0)],'aux2変数だけ。runtime owner未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==0,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1 and not(fb[2083//8]&(1<<(2083%8))),'badge1/ナギナタbadge未取得')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7112,1787),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[9,10,15,2],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[[4372,0,1],[4378,0,1]],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])


def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==31,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][28]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新北3歩と初ディグダ、新戦闘0')
    need(measured['frontier']==dict(kind='first_diglett_event',trigger=[6,14],map=[10,16],xy=[6,15],observation=6,local_id=5,facing=2),'最初の配置変更直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+7:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0028.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='0226b4086a011a251a7853b5524f66acb67db263f3bd2497702b0a893ae082b7','初ディグダ消失後field/freshContinue全pixel一致')
    need(measured['first_diglett_interacted']is True and measured['paper_obtained']is True and measured['paper_consumed_or_delivered']is False,'紙保持の通常配置変更だけ')
    inspection=json.loads((folder/'inspection.json').read_bytes());planned=json.loads((ROOT/m.PREP).read_bytes())
    need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['interaction']==planned['interaction'],'固定初回ownerを実入力と照合')
    need(inspection['initial_flags']=={str(f):0 for f in range(4372,4379)}and inspection['expected_flag_changes']==[[4372,0,1],[4378,0,1]]and inspection['instruction_count']==29 and inspection['text_count']==2,'初回限定29命令/2台詞')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():
    return json.loads((ROOT/'content/modernization/pr16_story_save77_next_route.json').read_bytes())
