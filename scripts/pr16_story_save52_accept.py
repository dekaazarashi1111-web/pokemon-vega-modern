#!/usr/bin/env python3
"""Save52の505番道路の通常迂回・ダブル戦・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save52_measure as m
from pr16_story_after_maori import need,identity
SOURCE='2d43764b9253f306dcb8abcd23e040e7cecbd85f'
RUN,JOB,ARTIFACT=37146655614,111271886470,11282311020
ARCHIVE=dict(size=294099,sha256='8d6ec9ce3876183af50999c7ba1a0e1a51cf430cb86318ebb861270c96143fd0')
OUTPUT=dict(size=131088,sha256='f3fc9b1d3121b049900defb5c2f031a0b397a10b34fa3464d51f355a87833028')
PARTY='618111bab55403e03b9e9152dcbc9dd23a4c5209b535f02a430bbed890ebdf89'
FLASH='527249e77cb63b8d11110dba00ce7d10a8857913c4d3b42b853aad85b9a5c4c7'
CP='content/modernization/pr16_story_save52_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE52_JA.md'
EVIDENCE='content/modernization/pr16_story_save52_evidence'
VISUAL='content/modernization/pr16_story_save52_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='3c7c0390aecb77137bdb2173342c2411ea37b67dd79abd6e1e9a2b0a16431c1c'
trace=m.a.trace

ROUTE=[[31, 24], [31, 25], [32, 25], [32, 26], [32, 27], [32, 28], [32, 29], [32, 30], [32, 31], [32, 32], [32, 33], [32, 34], [31, 34], [30, 34], [29, 34], [28, 34], [28, 35], [28, 36], [28, 37], [28, 38], [28, 39], [28, 0]]
COLD_LEDGER='def3a8d727dc95294ed0908fa68914b62022587e25ef55d2fe352a942c1ec502'
def motion():
    points=[(ROUTE[0],1)];face=1;faces={16:4,32:3,64:2,128:1}
    for before,after in zip(ROUTE[:-2],ROUTE[1:-1]):
        nf=faces[m.direction(before,after)]
        if nf!=face:points.append((before,nf))
        points.append((after,nf));face=nf
    points.append((ROUTE[-1],1));return points

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==50 and len(bo)==2,'全52画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(94,3726)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    points=motion();need(len(points)==26,'20移動/4方向転換/南connection1')
    for i,o in enumerate(ao):
        xy,face=points[i]if i<26 else([28,0],1);field=i<=25 or i==49;where=[3,23]if i<25 else[3,2]
        need(o['map']==where and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'迂回20歩とミルシティ実接続')
        need(o['callback2']==m.m.FIELD and o['lock']==int(not field)and o['field']is field,'南connection/menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==o['battle_flags']==o['battle_outcome']==0,'戦闘0/RP0/party4')
        need(o['party_sha256']==PARTY==m.a.PARTY and o['ledger_sha256']==LEDGER==m.a.LEDGER,'全progress party/ledger不変')
        need(o['save_counter']==(51 if i<44 else 52),'43一時hash一致はcounter51、44counter52部分write')
        if i<33:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<43 or i==44:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'33〜42/44部分write')
        else:need(o['flash_sha256']==FLASH,'43一時一致と45成功/安定を区別')
    need(len({o['flash_sha256']for o in ao[33:45]})==12,'12種類の書込Flash、43一致は未完')
    for o in bo:
        m.idle(o,52);need(o['map']==[3,2]and o['xy']==[28,0]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==COLD_LEDGER,'独立Continue実状態。cold RAM台帳差を保存一致と混同しない')
    need(COLD_LEDGER!=LEDGER,'観測済みcold RAM台帳差を保持')
    return dict(status='PASS_MIRU_CITY_CONNECTION_SAVE52_SCOPED',trainer_victories=0,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=52,map=[3,2],map_name_ja='ミルシティ',xy=[28,0],facing=1,party_count=4,rp=0,travel_steps=21,route505_steps=20,turns=4,route505_detour_complete=True,route505_south_connection_accepted=True,final_elevation=3,cave_crossing_complete=True,lead_species=850,lead_hp=[294,294],lead_pp=[11,10,15,14],mewtwo_hp=[50,354],mewtwo_pp=[0,0,0,0],pp_recovery_accepted=False,normal_recovery_required=True,healing_site_reached=False,haxorus_move_ui_native_accepted=True,haxorus_all_four_slots_native_accepted=False,repaired_classifier_native_exercised=False,double_target_separation_native_exercised=False,avoided_optional_pair=True,grass_tiles_crossed=4,
        save_success_text_observation=45,save_success_wording_observed=True,stable_full_flash_observation=45,transient_final_flash_observation=43,stable_hash_not_save_completion=True,save_counter_changed_observation=44,counter_change_not_save_completion=True,stable_field_observation=49,partial_write_observations=list(range(33,43))+[44],party_changed_observations=[],party_unchanged=True,party_byte41_runtime_owner_resolved=False,progress_ram_ledger_changed_observations=[],progress_ram_ledger_unchanged=True,ram_ledger_unchanged=False,cold_ram_ledger_differs=True,cold_ram_ledger_change_owner_resolved=False,
        progress_inputs=94,continue_inputs=13,screen_count=52,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=COLD_LEDGER,save39_cold_ram_difference_owner_resolved=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600 and x==y,'全party600byte不変');return []

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120,'全legacy flag')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(fa,fb))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(2194,0,1)],'通常新接続のphysicalflag2194だけ、ownerは未解明');return d

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save51/52とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,51,s.LAYOUT);new,rb=s.bank(after,0,52,s.LAYOUT);_,rc=s.bank(after,0xe000,51,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save51bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'party新旧hash');need(list(y[52:56])==[11,10,15,14] and list(y[152:156])==[0,0,0,0] and struct.unpack_from('<HH',y,86)==(294,294) and struct.unpack_from('<HH',y,186)==(50,354),'全員HP/PP不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==money_b==17040,'全Bag/HM05不変と所持金不変')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,63,84),(0x4022,0,1),(0x40ae,91,80)],'新接続var3件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(7025,1743),'全Save差分会計')
    return dict(party_unchanged_bytes=600,party_byte_deltas=pd,party_change_owner_resolved=True,pp=[11,10,15,14],hp=[294,294],mewtwo_pp=[0,0,0,0],mewtwo_hp=[50,354],pp_recovery_accepted=False,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,new_connection_flag_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==52,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][49]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['battle']is None,'通常迂回20歩+南接続、戦闘なし')
    need(measured['frontier']==dict(kind='new_connection',map=[3,2],xy=[28,0],observation=25),'初めてのミルシティ接続後ただちに保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+26:04d}.ppm').read_bytes())==i,'通常menu実cursor0→4')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==ROUTE[:-1]and len(inspection['route'])==21 and inspection['native_route_accepted']is False,'静的候補を実通過と分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==inspection['new_object_attribute_bytes']==0,'既読terrain/map/scripts/属性の再採取0')
    need(inspection['candidate_levels']==[3]*21 and inspection['south_map']['map']==[3,2]and inspection['target_xy']==[28,0],'南接続の固定境界')
    need(inspection['grass_tiles']==[[32,27],[32,29],[32,30],[32,31]]and all(not m.excluded(tuple(xy),inspection['pair_objects'])for xy in ROUTE[:-1]),'視界過大近似を避ける実通路と草地4cell')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
