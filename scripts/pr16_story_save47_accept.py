#!/usr/bin/env python3
"""Save47の504下段西通路・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save47_measure as m
from pr16_story_after_maori import need,identity
SOURCE='eabbb96a80487644d4a873eaea0a7b3a1a6a03b3'
RUN,JOB,ARTIFACT=37138339081,111247375971,11279895650
ARCHIVE=dict(size=518854,sha256='16992156ad670c7b385c5391506af7f6d1c54217166b5d1cfc5cc88db29d5efc')
OUTPUT=dict(size=131088,sha256='0ffabf8d049f74edaabdaf32a54872a267d9ea4c04f02845612295a9f30c6431')
PARTY='c6935d698a5dffdcbdb9c32ba7d4e1a97186e3c26b82aff545bf6f631a727f9e'
FLASH='d5a258b9169c6f7fb08675511f29e0c91fbd3c6c3e495e9259a7a2121c5edb06'
CP='content/modernization/pr16_story_save47_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE47_JA.md'
EVIDENCE='content/modernization/pr16_story_save47_evidence'
VISUAL='content/modernization/pr16_story_save47_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='9893bcce967f221d81a398053ea137368a84aae2486afc8b9a082703bbfcc344'
trace=m.a.trace

# 旧PPラベル矩形は現行のタイプ/分類アイコンを含み誤陰性。原測定は改作しない。
# 技名/種族名/PP数値に依存しない実パネル上枠と4枠cursorを別照合する。
PANEL='d88c81dac412d9318fe68d4f8b7a8033d4f0e0a0df838c670655a22b5ea0d82f'
MID_LEDGER='73baeaca6510a235caac9d8fb4e1796b74615148bb404eb9484ce912ad9831ca'
PARTIES=[m.a.PARTY,'7d0db2ce13fb899f3ba2aa9dfa40151a252875f9383625bfc5d81bfac46381ee','275f667c31bd04125fa2f50c14eac35adaaaa258af48859ced81a118c8f3e5f0','f82fd0f7526914700ddf014e823932dde6c0b47ff43e12d2207a3ab80b429a27',PARTY]
MOVE_UI=[35,42,49,57]
def classify_panel_digests(panel,arrows,shift):
    if panel==PANEL:
        need(len(arrows)==4,'技4枠cursor')
        choices=[i for i,x in enumerate(arrows)if x==m.m.ARROW]
        need(len(choices)==1,'実技cursor1つ');return 'moves',choices[0]
    if shift==m.m.SHIFT:return 'shift',None
    return 'other',None
def classify_panel(raw):
    return classify_panel_digests(m.m.digest(raw,[0,112,240,120]),[m.m.digest(raw,box)for box in m.m.BOXES],m.m.digest(raw,[200,74,231,105]))
def motion():
    route=[(m.ROUTE[0],3)];face=3;faces={16:4,32:3,64:2,128:1}
    for before,after in zip(m.ROUTE[:20],m.ROUTE[1:20]):
        nf=faces[m.direction(before,after)]
        if nf!=face:route.append((before,nf))
        route.append((after,nf));face=nf
    return route

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==88 and len(bo)==2,'全90画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(170,10390)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    points=motion();need(len(points)==28,'19移動/8方向転換')
    for i,o in enumerate(ao):
        xy,face=points[i]if i<28 else([11,5],4);field=i<27 or i in(63,87);cb=m.m.BATTLE if 29<=i<=62 else m.m.FIELD
        need(o['map']==[3,44]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'全北迂回/戦闘座標')
        need(o['callback2']==cb and o['lock']==int(not field)and o['field']is field,'trainer接近/戦闘/menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(0 if i<29 else 12)and o['battle_outcome']==int(i>=60),'新勝利1/RP0/party4')
        phase=sum(i>=j for j in(36,43,50,58));need(o['party_sha256']==PARTIES[phase],'通常技使用直後の全party hash')
        need(o['ledger_sha256']==(m.a.LEDGER if i<31 else MID_LEDGER if i<51 else LEDGER),'31/51のRAM ledger差を保持')
        need(o['save_counter']==(46 if i<83 else 47),'83counter47/84成功文言')
        if i<71:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<83:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'71〜82部分write')
        else:need(o['flash_sha256']==FLASH,'83安定Flash・84成功文言')
    need(len({o['flash_sha256']for o in ao[71:83]})==12,'12種類の部分write')
    for o in bo:
        m.idle(o,47);need(o['xy']==[11,5]and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態・残留勝利非再計上')
    return dict(status='PASS_ROUTE504_JUNE_SAVE47_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=47,map=[3,44],xy=[11,5],facing=4,party_count=4,rp=0,travel_steps=19,turns=8,north_detour_partial_accepted=True,final_elevation=3,cave_crossing_complete=True,lead_species=850,lead_hp=[294,294],lead_pp=[11,10,15,20],mewtwo_hp=[314,354],mewtwo_pp=[0,0,0,0],pp_recovery_accepted=False,normal_recovery_required=True,healing_site_reached=False,haxorus_move_ui_native_accepted=True,haxorus_observed_move_ui_slots=[0],haxorus_all_four_slots_native_accepted=False,observed_move_uses=[4,0,0,0],raw_controller_reported_move_uses=[0,0,0,0],controller_false_negative_observed=True,repaired_classifier_offline_only=True,trainer_name_ja='だいすきクラブのジュネ',defeated_opponents_ja=['ココガラ','アクタシ','ビッパ','ファマー'],opponent_count=4,reward_money=960,
        save_success_text_observation=84,save_success_wording_observed=True,stable_full_flash_observation=83,stable_hash_not_save_completion=True,save_counter_changed_observation=83,stable_field_observation=87,partial_write_observations=list(range(71,83)),party_changed_observations=[36,43,50,58],party_change_owner_resolved=True,ram_ledger_changed_observations=[31,51],ram_ledger_change_owner_resolved=False,
        progress_inputs=170,continue_inputs=13,screen_count=90,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'party全600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(52,15,11)],'ドラゴンクロー4回のPP差だけ')
    for n,h in enumerate(PARTIES):
        v=bytearray(x);v[52]=15-n;need(identity(bytes(v))['sha256']==h,'各実技直後のpartyはPP1減少だけ')
    return d

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120,'全legacy bitmap')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(fa,fb))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(1402,0,1)],'新trainerのphysicalflag1402だけ');return d

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save46/46とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,46,s.LAYOUT);new,rb=s.bank(after,0xe000,47,s.LAYOUT);_,rc=s.bank(after,0,46,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save46bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'party新旧hash');need(list(y[52:56])==[11,10,15,20] and list(y[152:156])==[0,0,0,0] and struct.unpack_from('<HH',y,86)==(294,294) and struct.unpack_from('<HH',y,186)==(314,354),'先頭/ミュウツーHP/PP不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==14264 and money_b==15224,'全Bag/HM05不変と通常賞金960円')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,22,40),(0x4022,1,0)],'補助var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6902,1708),'全Save差分会計')
    return dict(party_unchanged_bytes=599,party_byte_deltas=pd,party_change_owner_resolved=True,pp=[11,10,15,20],hp=[294,294],mewtwo_pp=[0,0,0,0],mewtwo_hp=[314,354],pp_recovery_accepted=False,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==90,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業Save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][87]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==m.ROUTE[:20],'最初の新戦闘まで19歩')
    need(measured['battle']==dict(start=29,finish=63,trainer=True,outcome=1,used=[0]*4,decisions=[dict(observation=i,keep_current=True)for i in(39,46,54)]),'誤陰性の原receiptを改作しない')
    need(measured['frontier']==dict(kind='new_battle',trigger=[11,5],map=[3,44],xy=[11,5],observation=63),'新trainerの通常勝利から保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+64:04d}.ppm').read_bytes())==i,'menu実cursor0→4')
    detected=[];shifts=[]
    for i in range(88):
        raw=(folder/'progress'/f'screen-{i:04d}.ppm').read_bytes();kind,cursor=classify_panel(raw)
        if kind=='moves':detected.append(i);need(cursor==0,'実4画面はslot0')
        if kind=='shift':shifts.append(i)
    need(detected==MOVE_UI and shifts==[39,46,54],'全88画面で4実技/3交代画面のみ')
    for i in MOVE_UI:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('other',None),'旧PPlabelの誤陰性を証拠化')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['candidate_levels']==[3]*88,'88vertex静的候補と19歩の実通過を区別')
    need(all(inspection[x]==0 for x in('new_map_views','new_terrain_cells','new_script_nodes')),'保存地形再採取0')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
