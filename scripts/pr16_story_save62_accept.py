#!/usr/bin/env python3
"""館内コレクター210新1勝のSave62原本だけを独立受入。native/既受入試験再走0。"""
from __future__ import annotations
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save62_measure as m
from pr16_story_after_maori import need,identity
SOURCE='ec04bdcf827896ce22d2d0d39aaa9e3f63d88d20'
RUN,JOB,ARTIFACT=37159791919,111310675760,11286961947
ARCHIVE=dict(size=219383,sha256='9ed808bfc02e6531bcc2c4df59089f18e70154a82b4a0ff6f807630d76fb9364')
OUTPUT=dict(size=131088,sha256='6526b5a8cf179800096fda0721f2e1770818170c83e9b76da39957166d86e356')
PARTY='a7d3e16a14fc09aacf9790ec910f6985b3f786c99bd12c7618f0b196ab496ae1'
FLASH='99be33d5e06b87fc2bd576466c353ae87a799d15451f9457872ae4b49b976a46'
LEDGER='3b7c3d6b431f42e2ae6c168ac52757f06519652b3c6b803899890845413e6d14';COLD_LEDGER=LEDGER
CP='content/modernization/pr16_story_save62_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE62_JA.md'
EVIDENCE='content/modernization/pr16_story_save62_evidence'
VISUAL='content/modernization/pr16_story_save62_visual_review.json'
shared=m.a.shared;transport=m.a.transport;parent=m.a.parent
ROUTE=[[25, 6], [26, 6]]
FLASH_PHASES=['77ea7d48beddc06dff5c34330c9487e37ddf4476e99112c9cc0c41d7207b2433', '67acea094c865445a43d97bedd68da4950f0ed74d77d74b9032168d24fb91f41', '3f1188eaeb59673a09be75eeedc3793d9210c72ecab42cab8d0c1450b4d5d622', '49974686c367c4a4cf835977b4597dd9e8e8a5125f1b7bd9f8130d5300d5251a', 'ecc0dd02622bb2919322d428f54184ba9a7ae1f715e19ccbd09b15981f63d3f5', '9afc2ddcd0a0c1a3560b09cbedd4c4b8d469cccc12779b8fa2758f0b4e908f3e', '0a8f2b805668c99104d505a900a46b09c12918e1c00ef8369e3621c35881c531', '4a6976c0fce2861ed6970903d5139296e09f50fce50ee76cdc25c9c8cd54cfca', 'e815dce3355512d7d6f1129c6fd6fa461224073affd62efe60846b7f8398a650', '8e969966f27bb76c4046b3334bd0c6eec62a8c1d30fa5fb01baa0c595cc073ef', 'adac96c237e2e3c24a21198c52f62f541ffc78c39ead96226c09b8b3d4d09300', '5e33142186933ca7f306b24bd9d39979e86eb162776e36d482c73af36a18addd', '64282c238de2b47e95c855e4db3072fe4baffbb52cda8168da7bde2b3cfc86b7']
PARTIES=['10ee93eab5773960adc821c1df89e9041f2a0623bf3978a1c4ad1ca87b1385c8', 'a4d71bd835c9b72e97a1213a454f7f973b97d7d65fad9f7dcca39e97fc6212df', '63b114aa032ece9b1028be63b1e8fcbe911e708f3817c517e699b636cb9e2f0b', 'a7d3e16a14fc09aacf9790ec910f6985b3f786c99bd12c7618f0b196ab496ae1']
from pr16_story_save21_accept import screen_bytes
trace_rows=m.a.trace_rows
def trace(folder,seed):
    folder=Path(folder);parsed=trace_rows((folder/'stdout.txt').read_bytes(),(folder/'commands.txt').read_bytes(),seed)
    need(not(folder/'stderr.txt').read_bytes(),'native stderr')
    need({p.name for p in folder.glob('screen-*.ppm')}=={f"screen-{v['screen']:04d}.ppm"for v in parsed['screens']},'全画面集合')
    for v in parsed['screens']:screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=False)
    return parsed
def motion(i):return ([25,6]if i==0 else[26,6]),4

def semantics(pa,pb):
    ao,bo=pa['observations'],pb['observations'];need(len(ao)==54 and len(bo)==2,'全56画面')
    need((pa['end']['inputs'],pa['end']['frames'])==(101,7168)and(pb['end']['inputs'],pb['end']['frames'])==(13,1510),'新区間101/cold13入力だけ')
    for i,o in enumerate(ao):
        xy,face=motion(i);cb=m.m.BATTLE if 3<=i<=27 else m.m.FIELD
        need(o['map']==[1,59]and o['xy']==xy and o['live_xy']==[v+7 for v in xy]and o['facing']==face,'通常新1歩/新trainer戦の位置・向き')
        need(o['callback2']==cb and o['field']is(i in(0,28,53))and o['lock']==int(i not in(0,28,53)),'trainer台詞/戦闘/通常field復帰/保存を分離')
        need(o['party_count']==4 and o['rp']==0 and o['battle_flags']==(12 if i>=3 else 0)and o['battle_outcome']==int(i>=25),'trainer1勝だけ。敵3体/残留を追加勝利にしない')
        party=PARTIES[0 if i<11 else 1 if i<17 else 2 if i<23 else 3]
        need(o['party_sha256']==party and o['ledger_sha256']==(m.a.LEDGER if i<17 else LEDGER),'実PP3消費とRAM台帳の観測境界')
        need(o['save_counter']==(61 if i<48 else 62),'48counterは保存中、49成功')
        wanted=m.a.FLASH if i<36 else FLASH_PHASES[i-36]if i<49 else FLASH
        need(o['flash_sha256']==wanted,'全13部分write/49最終Flashを区別')
    need(len(set(FLASH_PHASES))==13 and FLASH not in FLASH_PHASES,'counter62の観測48も部分write')
    for o in bo:
        m.idle(o,62);need(o['map']==[1,59]and o['xy']==[26,6]and o['facing']==4 and o['field']is True and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==PARTY and o['ledger_sha256']==LEDGER and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_MANSION_COLLECTOR210_SAVE62_SCOPED',trainer_victories=1,wild_victories=0,escapes=0,captures=0,ordinary_saves=1,save_counter=62,map=[1,59],map_name_ja='こころのやかた・入口階',xy=[26,6],facing=4,party_count=4,rp=0,travel_steps=1,turns=0,entry_warps=0,heart_mansion_entered=True,statue_paper_observed=False,unread_floor_entered=False,inert_warp8_activation=False,darkness_observed=True,hm05_taught_or_used=False,
        lead_species=850,lead_hp=[288,294],lead_pp=[15,10,15,6],mewtwo_hp=[354,354],mewtwo_pp=[10,20,15,10],trainer_name_ja='ヒサテル',trainer_class_ja='ポケモンコレクター',trainer_id=210,physical_trainer_bit=1490,trainer_party=[['イシズマイ',11],['ビッパ',12],['コフキムシ',14]],reward_yen=840,observed_move_uses=[0,0,0,3],observed_pp_consumption=[0,0,0,3],move_commands=3,target_confirmations=0,keep_current_choices=2,move_commands_not_automatically_pp_uses=True,
        normal_recovery_repeated=False,normal_recovery_required=False,pp_recovery_accepted=True,exp_share_obtained=True,exp_share_equipped_or_growth_accepted=False,party_unchanged=False,ram_ledger_unchanged=False,ram_ledger_change_owner_resolved=False,ram_ledger_changed_observations=[17],party_byte41_runtime_owner_resolved=False,old_save52_cold_difference_owner_resolved=False,healing_ram_ledger_owner_resolved=False,
        save_counter_changed_observation=48,counter_change_not_save_completion=True,partial_write_observations=list(range(36,49)),stable_hash_not_alone_save_completion=True,save_success_text_observation=49,save_success_wording_observed=True,stable_field_observation=53,progress_inputs=101,continue_inputs=13,screen_count=56,native_processes=2,prior_failed_native_processes=0,total_new_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,progress_ram_ledger=LEDGER,cold_ram_ledger=LEDGER,double_target_separation_native_exercised=False,npc_runtime_identity_resolved=False,cold_field_all_pixels_identical=True)

def party_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==600,'全party600byte')
    d=[(i,u,v)for i,(u,v)in enumerate(zip(x,y))if u!=v];need(d==[(55,9,6)],'実slot3 PP3消費だけ。HP/EXP/持物保持')
    copy=bytearray(x);copy[55]=6;need(bytes(copy)==y and identity(bytes(copy))['sha256']==PARTY,'保存byteから新partyを独立再構成。実saveへ書かない');return d
def flags_delta(x,y):
    need(type(x)is bytes and type(y)is bytes and len(x)==len(y)==0x120,'全legacy bitmap')
    delta=[(8*i+j,(u>>j)&1,(v>>j)&1)for i,(u,v)in enumerate(zip(x,y))for j in range(8)if(u^v)&(1<<j)]
    need(delta==[(1490,0,1)],'trainer210物理bit1490だけ');return delta
def boundary(before,after,cold,rom):
    s=parent.sectors;need(identity(before)==m.a.OUTPUT and identity(after)==OUTPUT and after==cold,'Save61/62と全coldSaveRTC');need(identity(rom)==shared.plan.CANDIDATE,'同一ROM')
    old,ra=s.bank(before,0xe000,61,s.LAYOUT);new,rb=s.bank(after,0,62,s.LAYOUT);_,rc=s.bank(after,0xe000,61,s.LAYOUT);need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'旧Save61全bank57344byte保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656];pd=party_delta(x,y);need(identity(x)['sha256']==m.a.PARTY and identity(y)['sha256']==PARTY,'partyhash')
    for pp,wanted in zip([9,8,7,6],PARTIES):
        copy=bytearray(x);copy[55]=pp;need(identity(bytes(copy))['sha256']==wanted,'保存byteから全3段階PPpartyを再構成。実saveへ書かない')
    remap=rom[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==s.TABLE_SHA,'固定trainer remap')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]));need(mapping.get(210+0x500,210+0x500)==1490,'trainer210→物理1490')
    need(rom[154591088-0x08000000:154591102-0x08000000].hex()=='5c00d2000000b4976908d7976908','既読map1/59 local9 trainerbattle210静的owner')
    need(list(y[52:56])==[15,10,15,6]and list(y[152:156])==[10,20,15,10]and struct.unpack_from('<HH',y,86)==(288,294)and struct.unpack_from('<HH',y,186)==(354,354),'HP/PP保持を別確認')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'party4')
    ia,ma=parent.shared.bag(before,old);ib,mb=parent.shared.bag(after,new);need(ia==ib and(ma,mb)==(17904,18744),'全Bag保持と実賞金840円')
    for sid in range(5,14):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E全payload保持')
    eb=parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6]);fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);fd=flags_delta(fa,fb)
    vd=[(0x4000+i,u,v)for i,(u,v)in enumerate(zip(va,vb))if u!=v];need(vd==[],'全legacy variables保持')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and not((fa[0x840//8]|fb[0x840//8])&1)and va[0x71]==vb[0x71]==9 and va[0x72]==vb[0x72]==1 and va[0xac]==vb[0xac]==16,'全国図鑑/story/40ac保持')
    need(sum(bool(fb[i//8]&(1<<(i%8)))for i in range(2080,2088))==1,'badge1')
    changed=[i for i,(u,v)in enumerate(zip(before,after))if u!=v];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    need((len(changed),len(ranges))==(6975,1716),'全Save差分会計');need(list(before[old[1]+28:old[1]+36])==list(after[new[1]+28:new[1]+36])==[3,2,255,0,38,0,16,0],'respawn保持')
    return dict(party_preserved_bytes=599,party_byte_deltas=pd,pp=[15,10,15,6],hp=[288,294],mewtwo_pp=[10,20,15,10],mewtwo_hp=[354,354],lead_exp_unchanged=True,bag_unchanged=True,money_before=ma,money_after=mb,physical_flag_deltas=fd,flag2056_runtime_owner_resolved=False,variable_deltas=vd,auxiliary_runtime_owners_resolved=False,s61e_payload_deltas=[],expanded_flags={str(i):(eb[(i-2304)//8]>>((i-2304)%8))&1 for i in [4367,4368,4369,4370,4381]},old_bank_preserved_bytes=57344,pc_preserved=True,s61e_crc_verified=True,sector_checksum_checks=len(ra)+len(rb)+len(rc),national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':9,'4072':1},var40ac=16,badge_count=1,all_save_rtc_cold_identical=True,changed_bytes=len(changed),changed_ranges=len(ranges),last_heal_location=[3,2,255,0,38,0,16,0])

def verify(folder,before,rom):
    folder=Path(folder);need(not(folder/'failure.json').exists(),'成功原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes());need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and measured['native_processes']==2 and measured['screen_count']==56,'測定identity')
    parsed={}
    for lane,seed in [('progress',m.a.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=trace(folder/lane,seed);e=json.loads((folder/lane/'execution.json').read_bytes());need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],observations=len(parsed[lane]['observations'])),'両core正常終了');need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'両作業save一致')
    result=semantics(parsed['progress'],parsed['continue']);need(measured['final']==parsed['progress']['observations'][53]and measured['continued']==parsed['continue']['observations'][1],'全field原本')
    need(measured['teleport']==[]and measured['route']==ROUTE and measured['inner_floor_entered']is False,'通常新1歩のみ。上階未到達')
    need(measured['battle']==dict(start=3,finish=28,trainer=True,outcome=1,move_commands=[0,0,0,3],target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=[dict(observation=10,move_slot=3),dict(observation=13,keep_current=True),dict(observation=16,move_slot=3),dict(observation=19,keep_current=True),dict(observation=22,move_slot=3)]),'選択3/交代拒否2/実PP3の区別')
    need(measured['frontier']==dict(kind='new_battle',trigger=[26,6],map=[1,59],xy=[26,6],observation=28),'最初の新trainer戦直後保存')
    for i in range(5):need(m.menu_index((folder/'progress'/f'screen-{i+29:04d}.ppm').read_bytes())==i,'通常menu全cursor0→4')
    for i,slot in [(8,0),(9,2),(10,3),(16,3),(22,3)]:need(m.classify((folder/'progress'/f'screen-{i:04d}.ppm').read_bytes())==('moves',slot),'実技UI cursorだけ')
    frames=[(folder/n).read_bytes()for n in ['progress/screen-0028.ppm','progress/screen-0053.ppm','continue/screen-0000.ppm','continue/screen-0001.ppm']];need(frames[0]==frames[1]==frames[2]==frames[3],'人物と床の暗所field全byte一致')
    inspection=json.loads((folder/'inspection.json').read_bytes());need(inspection==measured['inspection']and inspection['route']==m.ROUTE and inspection['native_route_accepted']is False and inspection['inert_warp8']['behavior']==8 and inspection['entry']['xy']==[30,10],'有効階段への静的経路と実到達を分離')
    need(inspection['new_terrain_cells']==inspection['new_map_views']==inspection['new_script_nodes']==0,'既読再採取なし')
    result['boundary']=boundary(before,(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes(),rom);result.update(input_save=m.a.OUTPUT,output_save=OUTPUT,candidate=shared.plan.CANDIDATE);return result



def route_plan():
    """保存済み二階層の静的床を再利用。実通行/穴/階段作動を受入しない。"""
    from collections import deque
    names=['content/modernization/pr16_story_save56_preparation.json','content/modernization/pr16_story_save57_preparation.json']
    data=[json.loads((ROOT/n).read_bytes())for n in names];nodes={};warps={}
    for d in data:
        floor=d['interior']['map'][1]
        for c in d['terrain']:
            if c['collision']==0 and c['elevation']==3:nodes[(floor,*c['xy'])]=c
    for d in data:
        floor=d['interior']['map'][1]
        for w in d['interior']['warps']:
            key=(floor,*w['xy'])
            if key not in nodes or nodes[key]['behavior']==8:continue
            other=next((x for x in data if x['interior']['map']==w['target_map']),None)
            if other is None:continue
            dest=next(x for x in other['interior']['warps']if x['id']==w['target_warp'])
            warps[key]=(other['interior']['map'][1],*dest['xy'])
    start=(59,26,6);target=(60,16,27);queue=deque([start]);prev={start:None}
    while queue:
        key=queue.popleft();floor,x,y=key
        nexts=[(floor,x+1,y),(floor,x-1,y),(floor,x,y+1),(floor,x,y-1)]+([warps[key]]if key in warps else[])
        for nxt in nexts:
            if nxt in nodes and nxt not in prev:prev[nxt]=key;queue.append(nxt)
    need(target in prev,'静的二階層route候補');route=[];key=target
    while key is not None:route.append(list(key));key=prev[key]
    route.reverse();cross=[[a,b]for a,b in zip(route,route[1:])if a[0]!=b[0]]
    need(len(route)==93 and cross==[[[59,30,10],[60,32,10]],[[60,31,21],[59,31,22]],[[59,30,29],[60,33,29]]],'入口北東階段→上階穴→入口南東階段→紙裏の静的3接続')
    return dict(status='STATIC_TWO_FLOOR_ROUTE_ONLY_NOT_NATIVE_ACCEPTANCE',source_bindings={n:identity((ROOT/n).read_bytes())for n in names},start=[1,59,26,6],target=[1,60,16,27],statue=[1,60,16,28],route=route,edges=92,ordinary_tile_edges=89,interfloor_edges=cross,new_map_views=0,new_terrain_cells=0,native_route_accepted=False,dynamic_npcs_or_battles_resolved=False,behavior102_hole_activation_observed=False,shortcut_from_first_upper_stair_to_paper=False)
