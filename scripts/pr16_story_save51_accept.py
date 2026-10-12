#!/usr/bin/env python3
"""Save51の505番道路の通常迂回・ダブル戦・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save51_measure as m
from pr16_story_after_maori import need,identity
SOURCE='7bfc8f61d793c5533c0e6aed3e75dadd178fbac3'
RUN,JOB,ARTIFACT=37145425150,111268239135,11281768926
ARCHIVE=dict(size=534884,sha256='b69798df6353d1ef77547ba193b4ab6615485679472694ff2f4eb3a3439edfbe')
OUTPUT=dict(size=131088,sha256='8661346e2de9bc73fc61d5a63af5bd6acd10008486b54c66c9459820a5447d65')
PARTY='618111bab55403e03b9e9152dcbc9dd23a4c5209b535f02a430bbed890ebdf89'
FLASH='8a3c6a49e19ab8c6cbe7e057595548097bc9247a55d4f683411d61435fb275c9'
CP='content/modernization/pr16_story_save51_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE51_JA.md'
EVIDENCE='content/modernization/pr16_story_save51_evidence'
VISUAL='content/modernization/pr16_story_save51_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
LEDGER='3c7c0390aecb77137bdb2173342c2411ea37b67dd79abd6e1e9a2b0a16431c1c'
trace=m.a.trace

ROUTE=[[22, 18], [23, 18], [24, 18], [24, 17], [24, 16], [24, 15], [25, 15], [25, 14], [25, 13], [26, 13], [27, 13], [28, 13], [29, 13], [30, 13], [31, 13], [32, 13], [32, 14], [32, 15], [31, 15], [31, 16], [31, 17], [31, 18], [31, 19], [31, 20], [31, 21], [31, 22], [31, 23], [31, 24]]
PARTIES=['b47e28e6469b45faa0d9d3411a3cf32a2038705ef3229f63c166b422e1f899ef', 'db842b33c98bd34f606791ea1cad6ccf1405c6ddf5ecf33a27fba6fd30ca9cb7', '45f72714db65bd6c2f3186aa8bd9f9e1b9b2b5aecb1a26ffe35b521891c9821d', 'a628a4dc9d4010c608bb0b6e237eeed9bac0574cebba09b815fa0dcab3a55836', '618111bab55403e03b9e9152dcbc9dd23a4c5209b535f02a430bbed890ebdf89']
LEDGERS=['6a97fa4b4d5371ae679857475bd353b670f71120cfd5df103a2e4723255bd949', '7f9ff5a64edee1b4dff0d426af90e8157b0baf08279d05843ddddb7831bc8bc1', '3c7c0390aecb77137bdb2173342c2411ea37b67dd79abd6e1e9a2b0a16431c1c']
def motion():
    points=[(ROUTE[0],2)];face=2;faces={16:4,32:3,64:2,128:1}
    for before,after in zip(ROUTE,ROUTE[1:]):
        nf=faces[m.direction(before,after)]
        if nf!=face:points.append((before,nf))
        points.append((after,nf));face=nf
    return points

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==95 and len(bo)==2,'全97画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(184,10558)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    points=motion();need(len(points)==36,'27移動/8方向転換')
    for i,o in enumerate(ao):
        xy,face=points[i]if i<36 else([31,24],1);field=i<35 or i in(70,94);cb=m.m.BATTLE if 38<=i<=69 else m.m.FIELD
        need(o['map']==[3,23]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'全高台横断/階段/新戦闘の実位置')
        need(o['callback2']==cb and o['lock']==int(not field)and o['field']is field,'接近/戦闘/menu/保存/field境界')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(0 if i<38 else 12)and o['battle_outcome']==int(i>=67),'新single戦1勝のみ/RP0/party4')
        phase=sum(i>=j for j in(47,53,59,65));need(o['party_sha256']==PARTIES[phase],'実PP4消費の全party phase')
        phase=sum(i>=j for j in(42,63));need(o['ledger_sha256']==LEDGERS[phase],'全RAMledger差を保持、owner未解明')
        need(o['save_counter']==(50 if i<90 else 51),'90counter51と91成功文言を分離')
        if i<78:need(o['flash_sha256']==m.a.FLASH,'Save前Flash不変')
        elif i<90:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'78〜89部分write')
        else:need(o['flash_sha256']==FLASH,'90安定Flash/91成功/94field')
    need(len({o['flash_sha256']for o in ao[78:90]})==12,'12種類の書込中Flash')
    for o in bo:
        m.idle(o,51);need(o['map']==[3,23]and o['xy']==[31,24]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態、残留勝利非再計上')
    return dict(status='PASS_ROUTE505_WATAMI_SAVE51_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=51,map=[3,23],xy=[31,24],facing=1,party_count=4,rp=0,travel_steps=27,turns=8,route505_detour_partial_accepted=True,route505_south_connection_accepted=False,final_elevation=3,cave_crossing_complete=True,lead_species=850,lead_hp=[294,294],lead_pp=[11,10,15,14],mewtwo_hp=[50,354],mewtwo_pp=[0,0,0,0],pp_recovery_accepted=False,normal_recovery_required=True,healing_site_reached=False,haxorus_move_ui_native_accepted=True,haxorus_observed_move_ui_slots=[0,2,3],haxorus_all_four_slots_native_accepted=False,repaired_classifier_native_exercised=True,new_double_battle_ui_observed=False,double_target_separation_native_exercised=False,
        trainer_name_ja='スキーヤーのワタミ',trainer_id=1055,physical_flag=1407,reward_money=1400,defeated_opponents_ja=['ココガラ','イシズマイ','ビッパ','クヌギダマ'],opponent_count=4,observed_move_uses=[0,0,0,4],move_commands=4,target_confirmations=0,move_commands_not_automatically_pp_uses=True,mewtwo_struggle_uses=0,
        save_success_text_observation=91,save_success_wording_observed=True,stable_full_flash_observation=90,stable_hash_not_save_completion=True,save_counter_changed_observation=90,counter_change_not_save_completion=True,stable_field_observation=94,partial_write_observations=list(range(78,90)),party_changed_observations=[47,53,59,65],party_unchanged=False,party_byte41_runtime_owner_resolved=False,ram_ledger_changed_observations=[42,63],ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,
        progress_inputs=184,continue_inputs=13,screen_count=97,native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,save39_cold_ram_difference_owner_resolved=False)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600bytes')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(55,18,14)],'PP4減だけ')
    for pp,expected in zip(range(18,13,-1),PARTIES):
        v=bytearray(x);v[55]=pp;need(identity(bytes(v))['sha256']==expected,'元画面のPP推移とparty phase全byteを独立照合。実saveは書換えない')
    return d

def flags_delta(fa,fb):
    need(type(fa)is bytes and type(fb)is bytes and len(fa)==len(fb)==0x120,'全legacy flag')
    d=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(fa,fb))for j in range(8)if(u^v)&(1<<j)]
    need(d==[(1407,0,1)],'ワタミ勝利のphysicalflag1個だけ');return d

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save50/51とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0,50,s.LAYOUT);new,rb=s.bank(after,0xe000,51,s.LAYOUT);_,rc=s.bank(after,0,50,s.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'旧Save50bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'party新旧hash');need(list(y[52:56])==[11,10,15,14] and list(y[152:156])==[0,0,0,0] and struct.unpack_from('<HH',y,86)==(294,294) and struct.unpack_from('<HH',y,186)==(50,354),'先頭PP4消費/全員HP不変')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and money_a==15640 and money_b==17040,'全Bag/HM05不変と通常1400円')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload不変')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);ed=[]
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,37,63)],'補助var1件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6944,1717),'全Save差分会計')
    remap=dict(struct.unpack_from('<HH',rom,0x1303ca8+i*4)for i in range(372));need(remap.get(1055+0x500,1055+0x500)==1407,'新trainer1055→physical1407の同ROM対応')
    return dict(party_unchanged_bytes=599,party_byte_deltas=pd,party_change_owner_resolved=True,pp=[11,10,15,14],hp=[294,294],mewtwo_pp=[0,0,0,0],mewtwo_hp=[50,354],pp_recovery_accepted=False,bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,physical_flag_deltas=fd,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=ed,expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in range(4367,4371)},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==97,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save同一')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][94]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE,'通常27歩だけ')
    decisions=[dict(observation=i,move_slot=3)if i in(46,52,58,64)else dict(observation=i,keep_current=True)for i in(46,49,52,55,58,61,64)]
    need(measured['battle']==dict(start=38,finish=70,trainer=True,outcome=1,move_commands=[0,0,0,4],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=decisions),'技選択4/相手確定0と実PP4を別検証')
    need(measured['frontier']==dict(kind='new_battle',trigger=[31,24],map=[3,23],xy=[31,24],observation=70),'最初の新戦闘後ただちに保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+71:04d}.ppm').read_bytes())==i,'通常menu実cursor0→4')
    panels=[];shifts=[]
    for i in range(95):
        kind,slot=m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())
        if kind=='moves':panels.append((i,slot))
        if kind=='shift':shifts.append(i)
    need(panels==[(44,0),(45,2),(46,3),(52,3),(58,3),(64,3)]and shifts==[49,55,61],'技panel6/交代拒否3、slot1とダブルtarget native未確認')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route'][:28]==ROUTE and len(inspection['route'])==48 and inspection['native_route_accepted']is False,'保存済残47歩候補と実27歩を区別')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読terrain/map/scriptsを無再採取')
    need(inspection['candidate_levels'][:28]==[4]*16+[0]+[3]*11 and inspection['south_map']['map']==[3,2]and inspection['target_xy']==[28,0],'高台東階段の新通過だけ、南接続先は未踏')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
