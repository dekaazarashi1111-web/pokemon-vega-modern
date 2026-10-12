#!/usr/bin/env python3
"""Save38の屋外503接続・trainer103勝利・保存原本を独立照合。native再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save38_measure as m
from pr16_story_after_maori import need,identity
SOURCE='1d3504839f4c1a86b054d3529f2c98a19ac40236'
RUN,JOB,ARTIFACT=37127609831,111216024409,11275249543
ARCHIVE=dict(size=347936,sha256='1d35ef01905047e71d8777cd491b3209e9dfc5f83508e23fd09f48e352915c6a')
OUTPUT=dict(size=131088,sha256='ca6b332ff001f757bde9d82baab19d4b6b8547488afefe62dc6ea408ced8b074')
PARTY='2177b4bbc36333b233a8a6e9d13eccb725421cd83f2ec641a1ec6d66a3f67d39'
FLASH='8fc73b5c83df1b89bfd840f5452cc95e21902f1a63247c0b7ee52d7acb693631'
CP='content/modernization/pr16_story_save38_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE38_JA.md'
EVIDENCE='content/modernization/pr16_story_save38_evidence'
VISUAL='content/modernization/pr16_story_save38_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
PARTIES=['ab2d5080e949385ad2880a3ab7f26222492b163f955fc30cbecebd0fd3b308c1', 'd15cb42da7cbda001eac236b97aef16b4fd3b988a8807ad0d20ecfa6a4f3c77f', '136b5fe5cabb557512906dbd879a15a469780abb91fe9100433d8b534596337f', '2177b4bbc36333b233a8a6e9d13eccb725421cd83f2ec641a1ec6d66a3f67d39']
LEDGERS=['f53f58f9f56b69943d14f92b8df3623be493d809276b0860da6d461fa3edc2f4', '3b1d1843f8274406fd4afdb3d1e6c43707e0115d1a11950895bc168b23dd301d', 'a42b7de819dcb559b39e870697fd51b376d8955e5025164a64d3355f4b02af8c']
LEDGER=LEDGERS[-1]
trace=m.a.trace
def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==60 and len(bo)==2,'全62画面/観測')
    need((pa['end']['inputs'],pa['end']['frames'])==(122,9119)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'全入力/frames')
    motion=[[6,4],[6,4],[6,5],[6,5],[5,5],[4,5],[4,5],[4,6]]
    for i,o in enumerate(ao):
        xy=motion[i]if i<8 else[9,76];face=3 if i in(0,3,4,5)else 1;field=i<8 or i in(39,59)
        pi=0 if i<18 else 1 if i<26 else 2 if i<33 else 3;li=0 if i<8 else 1 if i<29 else 2
        need(o['map']==([1,38]if i<8 else[3,21])and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'出口矢印→屋外到達の全座標')
        need(o['callback2']==(m.m.BATTLE if 10<=i<=38 else m.m.FIELD)and o['lock']==(0 if field else 1)and o['field']is field,'会話/戦闘/保存/field境界')
        need(o['party_count']==4 and o['rp']==0 and o['party_sha256']==PARTIES[pi]and o['ledger_sha256']==LEDGERS[li],'全party/ledger推移とRP0')
        need(o['battle_flags']==(0 if i<10 else 12)and o['battle_outcome']==(0 if i<36 else 1),'新trainer勝利1だけ・残留outcomeを再計上しない')
        need(o['save_counter']==(37 if i<55 else 38),'counter世代境界')
        if i<43:need(o['flash_sha256']==m.a.FLASH,'Save前の全Flash不変')
        elif i<55:need(o['flash_sha256']not in(m.a.FLASH,FLASH),'部分write12画面')
        else:need(o['flash_sha256']==FLASH,'55以降の安定全Flash')
    need(len({ao[i]['flash_sha256']for i in range(43,55)})==11 and ao[53]['flash_sha256']==ao[54]['flash_sha256'],'部分write11状態/12画面')
    for o in bo:
        m.idle(o,38);need(o['map']==[3,21]and o['xy']==[9,76]and o['facing']==1 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER,'独立Continue全状態')
    return dict(status='PASS_CAVE_OUTSIDE_ROUTE503_TRAINER103_SAVE38_SCOPED',trainer_victories=1,trainer_id=103,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=38,map=[3,21],xy=[9,76],facing=1,party_count=4,rp=0,cave_interior_crossing_complete=True,outside_route503_reached=True,cave_crossing_complete=True,trainer103_accepted=True,reward=220,move_selections=3,actual_pp_consumed=3,save_success_text_observation=56,save_success_wording_observed=True,stable_full_flash_observation=55,stable_field_observation=59,partial_write_observations=list(range(43,55)),progress_inputs=122,continue_inputs=13,screen_count=62,native_processes=2,prior_failed_native_processes=2,total_development_native_processes=4,preflight_failed_native_processes=0,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,hm05_taught_or_used=False,trainer352_accepted=False,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False)

def flags_delta(fa,fb):
    fd=[(i*8+bit,(u>>bit)&1,(v>>bit)&1)for i,(u,v)in enumerate(zip(fa,fb))for bit in range(8)if(u^v)&(1<<bit)]
    need(len(fa)==len(fb)==0x120 and fd==[(1383,0,1),(2056,1,0)],'trainer103勝利flagと補助flag2056解除だけ')
    return fd

def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'固定Save37/38とcold全Save/RTC');need(identity(rom)==shared.plan.CANDIDATE,'候補ROM不変')
    old,ra=s.bank(before,0xe000,37,s.LAYOUT);new,rb=s.bank(after,0,38,s.LAYOUT);_,rc=s.bank(after,0xe000,37,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save37bank全57344byte')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];need([(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v]==[(53,8,5)]and identity(y)['sha256']==PARTY,'party600byteはPP3だけ')
    for pp,expected in zip((7,6,5),PARTIES[1:]):
        modeled=bytearray(x);modeled[53]=pp;need(identity(bytes(modeled))['sha256']==expected,'中間party全byteモデル')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    bag_a,money_a=parent.shared.bag(before,old);bag_b,money_b=parent.shared.bag(after,new);need(bag_a==bag_b and(money_a,money_b)==(13576,13796),'全Bag/HM05不変と正規賞金220円')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload')
    ext=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);flag=(ext[(4367-2304)//8]>>((4367-2304)%8))&1;need(flag==1,'正規解禁flag4367保持')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[(0x4021,26,30),(0x4022,2,0),(0x40ae,79,91)],'補助var3件だけ・runtime owner未解決')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==8 and va[0x72]==vb[0x72]==1,'全国図鑑/story未解禁')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6840,1710),'全Save差分会計')
    return dict(party_changes=[[53,8,5]],pp=[1,5,0,0],hp=[320,354],bag_unchanged=True,hm05_owned=True,money_before=money_a,money_after=money_b,reward=220,physical_flag_deltas=fd,auxiliary_flag2056_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,flag4367=flag,old_bank_preserved_bytes=57344,pc_s61e_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':8,'4072':1},badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges))

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==62,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'全入力原本正常終端');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'Save作業原本')
    result=semantics(parsed['progress'],parsed['continue'])
    need(measured['final']==parsed['progress']['observations'][59] and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==m.ROUTE,'出口経路だけ')
    need(measured['battle']==dict(start=10,finish=39,trainer=True,outcome=1,used=[0,3,0,0],decisions=[dict(observation=17,move_slot=1),dict(observation=22,keep_current=True),dict(observation=25,move_slot=1),dict(observation=29,keep_current=True),dict(observation=32,move_slot=1)]),'技選択3/交代拒否2')
    for i in(17,25,32):need(m.m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',1),'はどうだん3回')
    for i in(22,29):need(m.m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('shift',None),'交代拒否2回')
    need(measured['frontier']==dict(kind='route503_exit_trainer',trigger=[4,6],map=[3,21],xy=[9,76],observation=39),'屋外到達/正規trainer後のfield')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_exit_accepted']is False,'静的候補を本nativeで初受入')
    graph=inspection['exit_npc_graph'];refs=[(r['value'],r['battle_type'])for r in graph['references']if r['category']=='trainer']
    need(graph['visited_script_count']==6 and len(graph['nodes'])==6 and not graph['diagnostics']and sorted(refs)==[(103,0),(1029,5)],'NPC10の初戦103と未受入再戦1029を区別')
    result['inspection_node_count_correction']=dict(measurement_declared_new_nodes=inspection['new_script_nodes'],actual_new_nodes=6,reason_ja='測定メタデータの0は継承値。保存graph6nodeが実採取。原本を改作せず訂正。')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom)
    result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result
