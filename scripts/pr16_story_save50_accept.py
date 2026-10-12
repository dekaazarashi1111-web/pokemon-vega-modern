#!/usr/bin/env python3
"""Save50の505番道路の通常迂回・ダブル戦・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save50_measure as m
from pr16_story_after_maori import need,identity
SOURCE='68c53dd8bbd74ce07d71f32a21d657e80cd1457e'
RUN,JOB,ARTIFACT=37143645467,111263061326,11281112264
ARCHIVE=dict(size=853577,sha256='96d1c619b2d219f23ad2904bffae9288cc254326374a5afced2fa166868f0c4c')
OUTPUT=dict(size=131088,sha256='b586055a74bd6b826d7ea8150e25954a9452718ad5b46e4926f0d01f9088022e')
PARTY='b47e28e6469b45faa0d9d3411a3cf32a2038705ef3229f63c166b422e1f899ef'
FLASH='eba464bde22ba610c8e1c13d24fc3adf5d5644a8617842758eac6117e87a25f4'
CP='content/modernization/pr16_story_save50_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE50_JA.md'
EVIDENCE='content/modernization/pr16_story_save50_evidence'
VISUAL='content/modernization/pr16_story_save50_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='6a97fa4b4d5371ae679857475bd353b670f71120cfd5df103a2e4723255bd949'
trace=m.a.trace

ROUTE=[[33, 0], [32, 0], [31, 0], [30, 0], [29, 0], [28, 0], [27, 0], [26, 0], [26, 1], [26, 2], [26, 3], [26, 4], [26, 5], [26, 6], [26, 7], [26, 8], [25, 8], [25, 9], [24, 9], [23, 9], [22, 9], [21, 9], [20, 9], [19, 9], [18, 9], [17, 9], [17, 10], [16, 10], [15, 10], [14, 10], [13, 10], [13, 11], [13, 12], [12, 12], [12, 13], [12, 14], [12, 15], [11, 15], [11, 16], [11, 17], [11, 18], [11, 19], [12, 19], [12, 20], [13, 20], [14, 20], [15, 20], [16, 20], [17, 20], [18, 20], [18, 21], [19, 21], [20, 21], [21, 21], [22, 21], [22, 20], [22, 19], [22, 18]]
PARTIES=['c6935d698a5dffdcbdb9c32ba7d4e1a97186e3c26b82aff545bf6f631a727f9e', 'c7e0fffa174ecc89185bea98c81557495427bf7bbeec452365f0ae7a75daf627', '68b6f5bfb434ffe50be8820780d214a3dac139c8c75538e40055c8863a4d5fa7', '3b7dba8aa9a65891d3584f455ff504f7a8293a35c92f316aa67bf3714449a2ac', 'ac9cbbdeb1fed06af8997895d8b4b52391e3974c3ba9978b40118b74dd87d26e', 'b47e28e6469b45faa0d9d3411a3cf32a2038705ef3229f63c166b422e1f899ef']
LEDGERS=['9e4f38b66578ac978b454de0a9573e854c8449d017f5fd82ea4aa4c1ffb02606', '5717f5289f3ebe52897b15dbdb44f9a6260497a45098cf501c95e44913c4b27a', 'fbad8ac0a70af6c7c344231e087c90c4a836035c94c0e99fe6600f45dfc320e2', '2d9cf92da5d6e6d73eb4d2e6d3bf8cb25152c440f97e49916960940b10cb4d3b', '6a97fa4b4d5371ae679857475bd353b670f71120cfd5df103a2e4723255bd949']
MOVE_PANELS=[86,87,88,89,102,103,116,117]
COMMANDS=[88,102,116]
TARGETS=[89,103,117]
def motion():
    points=[(ROUTE[0],1)];face=1;faces={16:4,32:3,64:2,128:1}
    for before,after in zip(ROUTE,ROUTE[1:]):
        nf=faces[m.direction(before,after)]
        if nf!=face:points.append((before,nf))
        points.append((after,nf));face=nf
    return points

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==151 and len(bo)==2,'全153画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(296,15830)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    points=motion();need(len(points)==76,'57移動/18方向転換')
    for i,o in enumerate(ao):
        xy,face=points[i]if i<76 else([22,18],2);field=i<75 or i in(126,150);cb=m.m.BATTLE if 79<=i<=125 else m.m.FIELD
        need(o['map']==[3,23]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'全迂回/ダブル戦の実位置')
        need(o['callback2']==cb and o['lock']==int(not field)and o['field']is field,'接近/戦闘/menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(0 if i<79 else 13)and o['battle_outcome']==int(i>=122),'新ダブル戦1勝のみ/RP0/party4')
        phase=sum(i>=j for j in(24,95,110,111,122));need(o['party_sha256']==PARTIES[phase],'歩行/PP2消費/反動3回の全party hash')
        phase=sum(i>=j for j in(39,85,106,126));need(o['ledger_sha256']==LEDGERS[phase],'全RAM ledger変化を保持、owner未解決')
        need(o['save_counter']==(49 if i<146 else 50),'146counter50と147成功文言を分離')
        if i<134:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<146:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'134〜145部分write')
        else:need(o['flash_sha256']==FLASH,'146安定Flash/147成功/150field')
    need(len({o['flash_sha256']for o in ao[134:146]})==12,'12種類の書込中Flash')
    for o in bo:
        m.idle(o,50);need(o['map']==[3,23]and o['xy']==[22,18]and o['facing']==2 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態、残留勝利非再計上')
    return dict(status='PASS_ROUTE505_SENA_RANA_SAVE50_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=50,map=[3,23],xy=[22,18],facing=2,party_count=4,rp=0,travel_steps=57,turns=18,route505_detour_partial_accepted=True,route505_south_connection_accepted=False,final_elevation=4,cave_crossing_complete=True,lead_species=850,lead_hp=[294,294],lead_pp=[11,10,15,18],mewtwo_hp=[50,354],mewtwo_pp=[0,0,0,0],pp_recovery_accepted=False,normal_recovery_required=True,healing_site_reached=False,haxorus_move_ui_native_accepted=True,haxorus_observed_move_ui_slots=[0,2,3],haxorus_all_four_slots_native_accepted=False,repaired_classifier_native_exercised=True,new_double_battle_ui_observed=True,
        trainer_name_ja='センパイとコウハイのセナとラナ',trainer_id=1054,physical_flag=1406,reward_money=416,defeated_opponents_ja=['ココガラ','タマンチュラ','クヌギダマ','ビッパ'],opponent_count=4,observed_move_uses=[0,0,0,2],move_commands=3,target_confirmations=3,raw_controller_reported_move_uses=[0,0,0,6],double_target_miscount_preserved=True,third_move_not_executed_after_partner_KO=True,mewtwo_struggle_uses=3,mewtwo_recoil_hp_loss=264,
        save_success_text_observation=147,save_success_wording_observed=True,stable_full_flash_observation=146,stable_hash_not_save_completion=True,save_counter_changed_observation=146,counter_change_not_save_completion=True,stable_field_observation=150,partial_write_observations=list(range(134,146)),party_changed_observations=[24,95,110,111,122],party_unchanged=False,party_byte41_runtime_owner_resolved=False,ram_ledger_changed_observations=[39,85,106,126],ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,
        progress_inputs=296,continue_inputs=13,screen_count=153,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600bytes')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v]
    need(d==[(41,43,44),(55,20,18),(186,58,50),(187,1,0)],'歩行中byte41未解明、PP2減とHP314→50だけ')
    for (b41,pp,hp),expected in zip([(43,20,314),(44,20,314),(44,19,226),(44,19,138),(44,18,138),(44,18,50)],PARTIES):
        v=bytearray(x);v[41]=b41;v[55]=pp;struct.pack_into('<H',v,186,hp);need(identity(bytes(v))['sha256']==expected,'既存原本hashとの独立照合。実saveは書き換えない')
    return d

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120,'全legacy flag')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(fa,fb))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(1406,0,1)],'セナラナ勝利のphysicalflag1個だけ');return d

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save49/50とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,49,s.LAYOUT);new,rb=s.bank(after,0,50,s.LAYOUT);_,rc=s.bank(after,0xe000,49,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save49bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'party新旧hash');need(list(y[52:56])==[11,10,15,18] and list(y[152:156])==[0,0,0,0] and struct.unpack_from('<HH',y,86)==(294,294) and struct.unpack_from('<HH',y,186)==(50,354),'先頭PP2消費/ミュウツー反動3回')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==15224 and money_b==15640,'全Bag/HM05不変と通常416円')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,109,37),(0x4022,4,0)],'補助var2件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6948,1728),'全Save差分会計')
    remap=dict(struct.unpack_from('<HH',rom,0x1303ca8+i*4)for i in range(372));need(remap.get(1054+0x500,1054+0x500)==1406,'新trainer1054→physical1406の同ROM対応')
    return dict(party_unchanged_bytes=596,party_byte_deltas=pd,party_change_owner_resolved=False,pp=[11,10,15,18],hp=[294,294],mewtwo_pp=[0,0,0,0],mewtwo_hp=[50,354],pp_recovery_accepted=False,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==153,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][150]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE,'通常57歩だけ')
    need(measured['battle']==dict(start=79,finish=126,trainer=True,outcome=1,used=[0,0,0,6],decisions=[dict(observation=i,move_slot=3)for i in(88,89,102,103,116,117)]),'旧測定のtarget重複6申告を改作しない')
    need(measured['frontier']==dict(kind='new_battle',trigger=[22,18],map=[3,23],xy=[22,18],observation=126),'最初の新ダブル戦後ただちに保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+127:04d}.ppm').read_bytes())==i,'通常menu実cursor0→4')
    panels=[]
    for i in range(151):
        raw=(folder/'progress'/f'screen-{i:04d}.ppm').read_bytes();kind,slot=m.classify(raw)
        if kind=='moves':panels.append((i,slot))
        need(kind!='shift','このダブル戦に交代確認UIなし')
    need(panels==[(86,0),(87,2),(88,3),(89,3),(102,3),(103,3),(116,3),(117,3)],'実move panel8画面。選択とtargetが重複する既存分類の限界')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route'][:58]==ROUTE and len(inspection['route'])==105 and inspection['native_route_accepted']is False,'静的104歩候補と実57歩を区別')
    need(inspection['new_terrain_cells']==13 and inspection['new_map_views']==1 and inspection['new_script_nodes']==0 and len(inspection['additions'])==12,'新21行12cellと接続先1cellだけ')
    need(inspection['candidate_levels'][:58]==[3]*55+[0,4,4]and inspection['south_map']['map']==[3,2]and inspection['target_xy']==[28,0],'505新階段だけ受入、南接続先は未踏')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
