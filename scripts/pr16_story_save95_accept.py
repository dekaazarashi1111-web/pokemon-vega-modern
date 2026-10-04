#!/usr/bin/env python3
"""封書引渡しSave95の原本だけを独立受入。旧native/既受入試験は再走しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save95_measure as m
from pr16_story_after_maori import need,identity
SOURCE='c334efffedc30d4b2a0ceae7782c382dbc4e8f5c'
RUN,JOB,ARTIFACT=37190913464,111402700990,11298657664
ARCHIVE=dict(size=303237,sha256='184fef2f402dd439ce195d49cf586b144191c9060a5ede59b96afca5c4cccf5a')
OUTPUT=dict(size=131088,sha256='7a23bd41f4c9131b3abc4dee4d9efd974ca9e9a681bf78cc835f4c0e3e240fa4')
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='ddfcb32dc6826ab2b2f7525af6a6911a3ebe18659bc6f368bbfdca4c9a1841c6'
LEDGER='92c13d3a58d260cb18732410f1e97c7ef727fbf88e0539fb6e01d332658677ad';COLD_LEDGER=LEDGER;SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save95_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE95_JA.md'
EVIDENCE='content/modernization/pr16_story_save95_evidence'
VISUAL='content/modernization/pr16_story_save95_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace=m.a.trace;trace_rows=m.a.trace_rows;ROUTE=m.ROUTE
POSITIONS=[[11, 8], [11, 8], [11, 7], [11, 6], [11, 5], [11, 5], [10, 5], [10, 5], [9, 5], [8, 5], [7, 5], [6, 5], [6, 5], [6, 6], [6, 7], [6, 7], [5, 7], [4, 7], [4, 7], [4, 8]]
FLASH_PHASES=['d70a3ced1239d837e1fb27102caf4e94f9c1c2a6546eb4e4f1dda7f0c81ea63a', '234aa9d9f4ff3c15a16c07ca7161e6d55f5fde526196966ef14221d3d811b530', '31eef7d82c78ea1548d7d70eadbf00982445eee1b5d63a6fb8d2f1bfc265aaa6', '4f34981a9072e2f7fec0722c8f38c4ee96be29f0d0e69da43297f64d431b4b04', 'fd4ed479eeacee7a880f91e2ca3baa7eb6c826ca24538a3afbbb19eab48cb95a', 'a6ebc387791a675f2f386569e36199f9b2ed15849b052998fb16b06b87b5a80f', 'ddb4d4dce1187617fb76f2b30810d7500decd70f4fefb1d6f7db99bb9fabb305', '50cfd7c75490132353476de0450880466526ea591288ba9be884d116e7df483d', '3f3f963826cf9b85b57e803a50351650d7da2890f1e2405734cd56fb7b29452b', '9df8cd35a3c491b4f4da06446150f408cd8d2aa7d2002a848696db35ae079ac3', '0b7b1f611a91795e1a15e5789c5eac6f0d206e8d399562a49dcb86a88946d0c5', '8e52b9a4d10ee66a412ff37cf0d341c6baa4988c81247809be4a2da9ab201510', 'a885020d30f0535093bba259d362cda21704457819f44494f29b5e6801483c25', '23caca824fd9dd675c52e804baa5a726783a37352710f066b58b0c9c5277b0a5']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==64 and len(bo)==2,'全66画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(118,6422)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新13歩/5旋回/障害待ち1/118+cold13入力')
    for i,o in enumerate(ao):
        xy=POSITIONS[i]if i<20 else[4,8];field=i<23 or i in(38,63);facing=4 if i==0 else 2 if i<5 else 3 if i<12 else 1 if i<15 else 3 if i<18 else 1
        need(o['map']==[6,1]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'13歩と5旋回、7の一時通行待ち。館内6/1から出ない')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'23〜37会話/38最初field/39menu/63保存後field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==(m.a.COLD_LEDGER if i<32 else LEDGER),'会話中の観測32でRAM台帳変化。owner未解明')
        need(o['save_counter']==(94 if i<59 else 95),'59counter95でも途中hash/保存中。60成功文言/最終hash')
        wanted=m.a.FLASH if i<46 else FLASH_PHASES[i-46]if i<60 else FLASH
        need(o['flash_sha256']==wanted,'46〜59部分write/60最終hash、counter単独で完了扱いしない')
    need(len(set(FLASH_PHASES))==14 and FLASH not in FLASH_PHASES and ao[59]['save_counter']==95 and not ao[60]['field'],'保存中/成功文言/fieldを分離')
    for o in bo:
        m.idle(o,95);need(o['map']==[6,1]and o['xy']==[4,8]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continueと120frameの全SaveRTC/party/RAM保持')
    return dict(status='PASS_LETTER_HANDOFF_SAVE95_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=95,map=[6,1],map_name_ja='ミルシティ博物館2階',xy=[4,8],facing=1,party_count=4,rp=0,travel_steps=13,turns=5,blocked_movement_inputs=1,npc_wait_inputs=3,npc_wait_frames=90,directional_stair_activation_inputs=0,scripted_turns=0,warps=0,automatic_entry_step_observed=False,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,gym_flags4372_to4378_all_clear=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=0,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=True,letter_handoff_accepted=True,letter_delivered_flag4382=True,letter_delivered_flag4382_owner_resolved=True,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=False,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=False,ram_ledger_changed_observations=[32],ram_difference_owner_resolved=False,old_save89_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,flag2056_runtime_owner_resolved=False,auxiliary_runtime_owners_resolved=False,save_counter_changed_observation=59,counter_change_not_save_completion=True,partial_write_observations=list(range(46,60)),first_final_flash_observation=60,last_partial_hash_observation=59,save_in_progress_observations=list(range(46,60)),stable_hash_not_alone_save_completion=True,save_success_text_observation=60,save_success_wording_observed=True,stable_field_observation=63,progress_field_screen_clear=True,progress_final_success_overlay_visible=False,progress_inputs=118,continue_inputs=13,screen_count=66,native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=0,total_new_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=False,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'今回physical全保持。過去2056ownerは未解明');return d
def bag_delta(x,y):
    need(type(x)is dict and type(y)is dict and set(x)==set(y)=={'items','key_items','balls','machines','berries'},'全5pocket')
    changes=[]
    for name in x:
        need(len(x[name])==len(y[name]),'全pocket枠')
        changes += [(name,i,u,v)for i,(u,v)in enumerate(zip(x[name],y[name]))if u!=v]
    need(changes==[('key_items',4,(274,1),(0,0))],'大切なものslot4の274一個だけ消費。他枠保持')
    need(sum(q for item,q in x['key_items']if item==274)==1 and sum(q for item,q in y['key_items']if item==274)==0,'一個→未所持、通常引渡し一回');return changes

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save94/95と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,94,s.LAYOUT);new,rb=s.bank(after,0xe000,95,s.LAYOUT);_,rc=s.bank(after,0,94,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save94全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);bd=bag_delta(ia,ib);need(ma==mb==23114,'23114円保持/受付再走0')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[(259,160,224)],'expanded4382だけset。remove274のscript ownerと対応')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'前回clearの4372〜4378全保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==1 and(eb[259]>>4)&1==0,'expanded4383保持/引渡し4382set/4380未完');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,83,96),(0x4022,0,3)],'aux4021/4022差分owner未解明。4061=1保持')
    need(va[0x61]==vb[0x61]==1,'受付支払済4061保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7064,1772),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=False,bag_item_deltas=bd,all_other_bag_slots_unchanged=True,paper_quantity=0,paper_delivered=True,paper_flag4382_owner_resolved=True,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[],unresolved_variable_owners=[0x4021,0x4022],auxiliary_runtime_owners_resolved=False,museum_fee=0,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[(4382,0,1)],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def screen_comparison(frames):
    def pixels(raw):
        need(raw[:15]==b'P6\n240 160\n255\n' and len(raw)==115215,'実PPM');return [raw[i:i+3]for i in range(15,len(raw),3)]
    ims=list(map(pixels,frames));counts=[]
    for i,j in [(0,1),(0,2),(1,2)]:
        diff=[(k%240,k//240)for k,(x,y)in enumerate(zip(ims[i],ims[j]))if x!=y];counts.append(len(diff))
        need(all((48<=x<=63 and 45<=y<=70)or(101<=x<=132 and 83<=y<=102)or(193<=x<=206 and 1<=y<=38)for x,y in diff),'差分は左右移動local2と他2人NPCの矩形内。主人公/地形保持')
    need(counts==[744,920,1023],'全field差分pixel会計。全画面一致にしない')
    return dict(progress_final_success_overlay_visible=False,progress_to_cold_changed_pixels=counts[:2],cold_changed_pixels=counts[2],npc_difference_rectangles=[[48,45,63,70],[101,83,132,102],[193,1,206,38]],all_pixels_identical=False)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==66,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][63]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新13歩/通常会話だけ。戦闘0')
    need(measured['frontier']==dict(kind='new_letter_handoff_event',map=[6,1],xy=[4,8],facing=1,npc_wait_observations=[19,20,21],dialogue_observations=list(range(23,38)),observation=38),'NPC視覚2回連続確認→全15dialog→最初fieldで保存')
    need([m.npc_in_front((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())for i in range(19,23)]==[False,False,True,True],'NPCが正面に来るまでAなし・90frameだけ待機')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+39:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0063.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    hashes=['b3b0b74f729bcfd390c07bfa4662d01638aa92e0565d1a7a1f598ffb0a52b1e1', '8e7b24c4539c2b1644f41c4eb70e44e862e47dbd1cc9848a39b38a03f797a1eb', 'a7362f9f90c5aeb4f18b064ed8d2162e80d2ea6c288aa71a85d94293f303877b']
    need([identity(x)['sha256']for x in frames]==hashes,'最終field/cold全3原画')
    result['screen_comparison']=screen_comparison(frames)
    need(measured['letter_handoff_event_completed']is True and measured['letter_handoff_accepted']is False and measured['paper_consumed_or_delivered']is False and measured['paper_acceptance_pending']is True,'未受入測定原本を改作しない。独立Bag/flag/画面から後継受入')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']==m.inspect(rom,before),'静的local2/全地形/紙とbadge/支払済全byte')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save95_next_route.json').read_bytes())
