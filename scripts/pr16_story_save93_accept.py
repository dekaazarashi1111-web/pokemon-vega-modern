#!/usr/bin/env python3
"""博物館50円受付Save93の原本だけを独立受入。旧native/既受入試験は再走しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save93_admission_measure as m
from pr16_story_after_maori import need,identity
SOURCE='2718151982e8cdd82768c720b05c852ccdbb7d1b'
RUN,JOB,ARTIFACT=37188523239,111395599488,11298425525
ARCHIVE=dict(size=203718,sha256='99507ee5a36eff68e1e85dab0e31edf9b90a7cfa9c5dd089f849be685b91f08a')
OUTPUT=dict(size=131088,sha256='93cdaccd2cd5cb969a9d4bc78187b25b62fd0f9b05924f2c2bd0ad26ed73d255')
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='cb04954429a5aae6f988c86d3fba2b41237b67a50bf67d92843844969c8980d3'
LEDGER='9ec11aa0a1bdb1cd0f3249e05c96218f562911b9089f274134863b5fa143844f';COLD_LEDGER=LEDGER;SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save93_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE93_JA.md'
EVIDENCE='content/modernization/pr16_story_save93_evidence'
VISUAL='content/modernization/pr16_story_save93_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace=m.a.trace;trace_rows=m.a.trace_rows;ROUTE=m.ROUTE
FLASH_PHASES=['88bbd589802afd07bfb580465a037f8b572bb79c96f8f73f6ef79e13e9a6df3a', '5ab131e7398d067503d2cae38f1fad173410cf32fc21e7676c0da468e4e40cee', 'e7bddf10676709e08ba2a8bd0cb8981afb7824b17e483a3b102446825fd86d79', 'ccce0c31f7c62213ef9ab9efa4ddb95ad552d7ea440dee2082def48653c970ae', '013f0e6dd009f565c6c1380a3f82c542817997def302e6a3f808dd97f13b7468', '0ab4c969fe3d87ffa0bf6819690c7ce58370f1c1887955e8eacc7210fc4267eb', '953c2d98cb5d3851dc02717da9941d1ffa2208f47b131037b86a8eb5a00ed1e8', 'a96f1dd8ab3cbde4fc73a0804ee68667e6d247369f685b732e22aa9b4f2a8cab', '4bdf5f85e02adfe192d029987521b66382c617a8bafd4b354736916f0f8635be', '61b44e5ecd9787cfb47de08328c04c5c01278d164c9f4df814bb7e6c34f9bfcd', 'cf90b9bede64534ff7c807acdb5da7dc4871170e907539f028157d83919e36ca', 'cd06d7361264ef202bedc3e6f66289ce135a6d8cb0cc88b5831d8d0018ff205a', '3249a11e50184a757e5656b0401de5a2581a25f2558aa530282c54155753964d', 'cb04954429a5aae6f988c86d3fba2b41237b67a50bf67d92843844969c8980d3', '4d2ab7271e68760b61485eda57f93ae6512a613e18238a2df5cf022d6d8b2611']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==34 and len(bo)==2,'全36画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(60,3156)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'北4歩/50円受付60+cold13入力')
    for i,o in enumerate(ao):
        xy=[14,9-i]if i<4 else[14,5];field=i<4 or i in(7,33);facing=2 if i<4 else 4
        need(o['map']==[6,0]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'北4歩/受付時東向き・自動tile移動なし')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'4自動受付→7field→8menu→33field')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.COLD_LEDGER,'全party600byteと今回RAM ledger保持。過去owner未解明')
        need(o['save_counter']==(92 if i<29 else 93),'29counter93はまだ保存中→30成功文言→33field')
        wanted=m.a.FLASH if i<15 else FLASH_PHASES[i-15]if i<30 else FLASH
        need(o['flash_sha256']==wanted,'15〜29書込中。28最終hash一時一致→29再差分→30成功/最終hash')
    need(ao[28]['flash_sha256']==FLASH!=ao[29]['flash_sha256']and ao[28]['save_counter']==92 and ao[29]['save_counter']==93 and not ao[30]['field'],'最終hash先行/counter単独で完了としない')
    for o in bo:
        m.idle(o,93);need(o['map']==[6,0]and o['xy']==[14,5]and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue/120frame/全SaveRTC/party/RAM保持')
    return dict(status='PASS_MUSEUM_ADMISSION_SAVE93_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=93,map=[6,0],map_name_ja='ミルシティ博物館1階',xy=[14,5],facing=4,party_count=4,rp=0,travel_steps=4,turns=0,scripted_turns=1,warps=0,automatic_entry_step_observed=False,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=50,museum_admission_var4061=1,museum_second_floor_accepted=False,gym_flags4372_to4378_all_clear=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=1,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=False,letter_delivered_flag4382=False,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=True,ram_ledger_changed_observations=[],ram_difference_owner_resolved=False,old_save89_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,flag2056_runtime_owner_resolved=False,auxiliary_runtime_owners_resolved=False,save_counter_changed_observation=29,counter_change_not_save_completion=True,partial_write_observations=list(range(15,30)),first_final_flash_observation=28,last_partial_hash_observation=29,save_in_progress_observations=list(range(15,30)),stable_hash_not_alone_save_completion=True,save_success_text_observation=30,save_success_wording_observed=True,stable_field_observation=33,progress_inputs=60,continue_inputs=13,screen_count=36,native_processes=2,prior_failed_native_processes=1,prior_pre_native_failed_attempts=0,total_new_native_processes=3,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=True,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[],'全legacy flags保持。旧2056差分owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save92/93と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0,92,s.LAYOUT);new,rb=s.bank(after,0xe000,93,s.LAYOUT);_,rc=s.bank(after,0,92,s.LAYOUT);need(before[:0xe000]==after[:0xe000],'旧Save92全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==23164 and mb==23114 and ma-mb==50,'全Bag/5pocket保持・通常受付50円だけ');need(sum(q for item,q in ib['key_items']if item==274)==1,'だいじなふうしょ一個保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'S61E全payload保持/紙未引渡し')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'前回clearの4372〜4378全保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0,'expanded4383保持/引渡し4382未set');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4001,0,2),(0x4021,71,74),(0x4022,3,1),(0x4061,0,1)],'受付4001/4061のownerはscript一致、4021/4022は未解明')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7046,1785),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=1,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[0x4001,0x4061],unresolved_variable_owners=[0x4021,0x4022],auxiliary_runtime_owners_resolved=False,museum_fee=50,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==36,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][33]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新北4歩/50円受付、warp/戦闘/紙引渡し0')
    need(measured['frontier']==dict(kind='new_museum_admission',trigger=[14,5],map=[6,0],xy=[14,5],facing=4,dialogue_observations=[4,5,6],observation=7),'最初の受付完了直後だけ保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+8:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0033.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    need(len(set(frames))==1 and identity(frames[0])['sha256']=='10d7485c536a81fe0bba9c3703bdefac2a2fe9bda8e08917623954f689dbc43d','独立Continue/120frame後も全38400pixel一致')
    need(measured['museum_admission_observed']is True and measured['museum_admission_accepted']is False and measured['paper_consumed_or_delivered']is False and measured['museum_second_floor_observed']is False,'測定原本は受付受入前・紙保持・2階未到達')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']==m.inspect(rom,before),'固定coord/50円/4061ownerの全byte')
    owner=json.loads((ROOT/m.PREP).read_bytes());inst={r['address']:r['hex']for r in owner['instructions']}
    need(inst[0x817f237]=='1601400200'and inst[0x817f2b3]=='913200000000'and inst[0x817f2c6]=='1661400100','4001=2/50円除去/4061=1をROM命令先頭から証明')
    # The failed native attempt is diagnostic, never accepted or silently erased.
    failed=json.loads((folder/'failed-attempt.json').read_bytes());need(failed['accepted']is False and failed['native_processes']==1 and failed['execution']['initial_save']==failed['execution']['final_save']==m.a.OUTPUT,'失敗native1は未保存/全Save92保持')
    result['admission_owner']=dict(preparation=identity((ROOT/m.PREP).read_bytes()),coord=owner['coord'],instruction_count=56,resolved_vars=[0x4001,0x4061],money_removed=50,static_to_native_verified=True)
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save93_next_route.json').read_bytes())
