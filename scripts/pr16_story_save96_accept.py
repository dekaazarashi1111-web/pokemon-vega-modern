#!/usr/bin/env python3
"""博物館初下降Save96の原本だけを独立受入。旧native/既受入試験は再走しない。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
# 旧受入sourceを変えず154固有moduleの歴史連鎖を読むための、この検証入口だけの有限上限。
# 既定1000はPython3.12のunittest fresh import時だけ不足。native呼出し/旧試験再走はない。
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save96_measure as m
from pr16_story_after_maori import need,identity
SOURCE='eea7968c2626dc7cc6746ade93a0c9421a95c395'
RUN,JOB,ARTIFACT=37192111310,111406308028,11299780050
ARCHIVE=dict(size=211079,sha256='015b6c4a6f325e486f503e6e4672324199e3ae89286bf523b6921f939cbd7f8f')
OUTPUT=dict(size=131088,sha256='1f1d30d7f8261ff8b03f0bf290aaa61d052709b6a0a1c259da13f16895cd4b81')
PARTY='565b246bde44f27bd3ae40958aaba32c96f8ed0287d5c5c053f38e9798491676'
FLASH='0f9c27f993d4c48547ed525f66651014238ad329223f205a1f6595768637cab5'
LEDGER='92c13d3a58d260cb18732410f1e97c7ef727fbf88e0539fb6e01d332658677ad';COLD_LEDGER=LEDGER;SETTLED_COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save96_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE96_JA.md'
EVIDENCE='content/modernization/pr16_story_save96_evidence'
VISUAL='content/modernization/pr16_story_save96_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
trace=m.a.trace;trace_rows=m.a.trace_rows;ROUTE=m.ROUTE
POSITIONS=[[4, 8], [4, 8], [4, 7], [4, 7], [5, 7], [6, 7], [6, 7], [6, 6], [6, 5], [6, 5], [7, 5], [8, 5], [9, 5], [10, 5], [11, 5], [11, 5], [11, 6], [11, 7], [11, 8], [8, 8]]
FLASH_PHASES=['112c0e0e9a33eafbb9e53446fee372f05d483f1a7a95bd980057af317b899dda', 'c96061b48ef2bf4a7c500b1c635ce921ad9668496cee8d536191948cb624c6d0', 'b03727be23cbbfe63be299afe6948c108b63dc3bc921e0091e4564ca95283412', 'c6b91d5feff2a5ee43d4c597d677fb841dd90a70392e779399e8eab5b347e25e', '610fb708477fea75ee0d1aedaafb6e4f57deb4a7d64258ac4d17b21947d75654', '833c5f36c51adeb4ddb13f277f0cf55e69023e96640cc73e4d0354765840de36', 'd6c1c7f0d57dcbcc772bf615fc9b16fe1c6d05b6b59aa56d32aef82f6c0e9b40', 'cb04895faf3f3b1ce538b43f843eb7a026e0c810201d0b0aaf9418edce2fe7b4', '2a302536a160eb6b60e9406e417d4dee09c3d8dbf1c9711950e2b2179200e4c2', '91da62a03f68a701b1d5f82f5258866689e081794251b1c5f754787e70e52690', '0dc675026398b03a2c89d40bb56e2d349cea1d3e94a04aae7d86cd62dcf52bf1', '1afafc4533dc201c9fc1042bddaade013f098d217d82c14af2c498da271c551c', '0f9c27f993d4c48547ed525f66651014238ad329223f205a1f6595768637cab5', 'de5df83f6c2bb0b9fd1456cc123c3f33226660cd76dae8ed3f6edbe5779bf322']
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==45 and len(bo)==2,'全47画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(83,3552)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新13歩/旋回5/西方向下降/83+cold13入力')
    for i,o in enumerate(ao):
        xy=POSITIONS[i]if i<20 else[8,8];where=[6,1]if i<19 else[6,0];field=i<20 or i==44
        facing=1 if i==0 or 15<=i<19 else 2 if i<3 or 6<=i<9 else 4 if i<19 else 3
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==facing,'新復路13歩/5旋回/西入力下降、1階8,8西。自動追加tile移動なし')
        need(o['callback2']==m.m.FIELD and o['field']is field and o['lock']==int(not field),'19最初の1階field→20menu→44clearfield')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0,'新戦闘0/party4/RP0')
        need(o['party_sha256']==PARTY==m.a.PARTY,'全party600byte保持')
        need(o['ledger_sha256']==LEDGER==m.a.COLD_LEDGER,'今回全RAM台帳保持。過去owner解明とは別')
        need(o['save_counter']==(95 if i<40 else 96),'40counter96でも保存中/別hash。41成功文言後確定')
        wanted=m.a.FLASH if i<27 else FLASH_PHASES[i-27]if i<41 else FLASH
        need(o['flash_sha256']==wanted,'27〜40保存中、39一時finalhash→40別hash→41安定finalhash')
    need(len(set(FLASH_PHASES))==14 and FLASH_PHASES[12]==FLASH and FLASH_PHASES[13]!=FLASH,'保存中に一度finalhashと一致しても完了にしない')
    need(ao[39]['save_counter']==95 and ao[40]['save_counter']==96 and not ao[41]['field'],'hash/counter/成功文言/fieldを分離')
    for o in bo:
        m.idle(o,96);need(o['map']==[6,0]and o['xy']==[8,8]and o['facing']==3 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continueと120frame/SaveRTC/party/RAM保持')
    return dict(status='PASS_MUSEUM_DESCENT_SAVE96_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=96,map=[6,0],map_name_ja='ミルシティ博物館1階',xy=[8,8],facing=3,party_count=4,rp=0,travel_steps=13,turns=5,blocked_movement_inputs=0,npc_wait_inputs=0,npc_wait_frames=0,directional_stair_activation_inputs=1,scripted_turns=0,warps=1,automatic_entry_step_observed=False,gym_leader_defeated=True,gym_puzzle_completed=True,gym_exit_accepted=True,museum_entry_accepted=True,museum_admission_accepted=True,museum_fee=0,museum_admission_var4061=1,museum_second_floor_accepted=True,museum_return_first_floor_accepted=True,gym_flags4372_to4378_all_clear=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,required_badge_flag=2083,required_badge_present=True,paper_item_id=274,paper_item_quantity=0,paper_expanded_flag=4383,paper_obtained=True,paper_consumed_or_delivered=True,letter_handoff_accepted=True,letter_delivered_flag4382=True,letter_delivered_flag4382_owner_resolved=True,lead_species=850,lead_hp=[277,294],lead_pp=[3,9,8,2],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],observed_move_uses=[0,0,0,0],observed_pp_consumption=[0,0,0,0],move_commands=0,target_confirmations=0,aerial_ace_pp_preserved=2,normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=True,progress_ram_ledger_unchanged=True,cold_ram_ledger_unchanged=True,ram_ledger_unchanged=True,ram_ledger_changed_observations=[],ram_difference_owner_resolved=False,old_save89_progress_difference_owner_resolved=False,party_byte41_runtime_owner_resolved=False,flag2056_runtime_owner_resolved=False,auxiliary_runtime_owners_resolved=False,save_counter_changed_observation=40,counter_change_not_save_completion=True,partial_write_observations=list(range(27,39))+[40],first_final_flash_observation=39,last_partial_hash_observation=40,stable_final_flash_observation=41,early_finalhash_not_completion=True,save_in_progress_observations=list(range(27,41)),stable_hash_not_alone_save_completion=True,save_success_text_observation=41,save_success_wording_observed=True,stable_field_observation=44,progress_field_screen_clear=True,progress_final_success_overlay_visible=False,progress_inputs=83,continue_inputs=13,screen_count=47,native_processes=2,prior_failed_native_processes=0,prior_pre_native_failed_attempts=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_initial_ram_ledger=m.a.COLD_LEDGER,progress_settled_ram_ledger=LEDGER,cold_initial_ram_ledger=LEDGER,cold_settled_ram_ledger=LEDGER,cold_field_all_pixels_identical=False,hm05_taught_or_used=False)
def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte/HP/PP/EXP/持物保持');return []
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2056,0,1)],'1階帰還physical2056だけset。runtime owner未解明');return d
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save95/96と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,95,s.LAYOUT);new,rb=s.bank(after,0,96,s.LAYOUT);_,rc=s.bank(after,0xe000,95,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save95全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    need(list(y[52:56])==[3,9,8,2]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(277,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and ma==mb==23114,'全Bag/5pocket/23114円保持・受付再走0');need(sum(q for item,q in ib['key_items']if item==274)==0,'封書引渡し後の空slot保持')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC全payload保持')
    need(before[old[13]:old[13]+0x7d0]==after[new[13]:new[13]+0x7d0]and before[old[13]+0xde6:old[13]+0xff4]==after[new[13]+0xde6:new[13]+0xff4],'PC終端とS61E外は保持')
    ea=parent.s61e_record(before[old[13]+0x7d0:old[13]+0xde6]);eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[(i,u,v)for i,(u,v)in enumerate(zip(ea,eb))if u!=v]
    need(ed==[],'S61E全payload保持/紙引渡し済み')
    ef={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)};need(ef=={str(f):0 for f in range(4372,4379)},'前回clearの4372〜4378全保持')
    need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==1 and(eb[259]>>4)&1==0,'expanded4383/4382保持、4380未完');fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,96,109),(0x4022,3,1)],'1階帰還aux2変数差分はowner未解明。受付4061=1保持')
    need(va[0x61]==vb[0x61]==1,'受付支払済4061保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==0 and vb[0xac]==0,'全国図鑑/story保持・40ac0保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==2 and(fb[2083//8]&(1<<(2083%8))),'badge2/ナギナタbadge保持')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7019,1748),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=600,party_byte_deltas=pd,pp=[3,9,8,2],hp=[277,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,paper_quantity=0,paper_delivered=True,paper_flag4382_preserved=True,paper_flag4383_preserved=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,resolved_admission_variables=[],unresolved_variable_owners=[0x4021,0x4022],auxiliary_runtime_owners_resolved=False,museum_fee=0,museum_admission_var4061=1,s61e_payload_deltas=ed,expanded_flags=ef,expanded_flag_deltas=[],old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=0,var40ac_before=0,var40ac_runtime_owner_resolved=False,badge_count=2,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def screen_comparison(frames):
    def pixels(raw):
        need(raw[:15]==b'P6\n240 160\n255\n' and len(raw)==115215,'実PPM');return [raw[i:i+3]for i in range(15,len(raw),3)]
    ims=list(map(pixels,frames));counts=[]
    for i,j in [(0,1),(0,2),(1,2)]:
        diff=[(k%240,k//240)for k,(x,y)in enumerate(zip(ims[i],ims[j]))if x!=y];counts.append(len(diff))
        need(all(18<=x<=29 and 0<=y<=22 for x,y in diff),'NPC1人の上端矩形内だけ。主人公/地形保持')
    need(counts==[202,60,142],'全field差分pixel会計。全画面一致にしない')
    return dict(progress_final_success_overlay_visible=False,progress_to_cold_changed_pixels=counts[:2],cold_changed_pixels=counts[2],npc_difference_rectangles=[[18,0,29,22]],all_pixels_identical=False)

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==47,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][44]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'新復路13歩/西階段だけ。戦闘/会話0')
    need(measured['frontier']==dict(kind='new_museum_return_first_floor',trigger=[11,8],map=[6,0],xy=[8,8],facing=3,observation=19),'初下降後の最初fieldで保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+20:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0044.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']]
    hashes=['1678565ff78e9a6c4136f1ad203260e9d445762ff36e75a4a2449d58ee201bc8', '87e5930f12514707d75c4393a65efbb0c94548b7c77f2cd59dbfe8b73b1caab8', '48b4c95c7d90fd370c987c89981bf176ff0ef423186c2249ac70f915f54dffa5']
    need([identity(x)['sha256']for x in frames]==hashes,'最終field/cold全3原画');result['screen_comparison']=screen_comparison(frames)
    need(measured['museum_return_first_floor_observed']is True and measured['museum_return_first_floor_accepted']is False and measured['paper_consumed_or_delivered']is True and measured['museum_admission_observed']is False,'測定時未受入原本を改作しない。封書会話/受付再走0')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']==m.inspect(rom,before),'静的復路と西方向階段/紙とbadge/支払済全byte')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result

def next_route():return json.loads((ROOT/'content/modernization/pr16_story_save96_next_route.json').read_bytes())
