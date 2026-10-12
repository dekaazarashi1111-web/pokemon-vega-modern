#!/usr/bin/env python3
"""Save21後の503新5勝→ちえのどうくつ北入口→Save22だけを検証する。"""
from __future__ import annotations
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save21_accept as parent
from pr16_story_save21_accept import (need,identity,load,integer,digest,commands,screen_bytes,
    CANDIDATE,RUNNER,inflate,source,shared,sectors,s61e_record,FIELD,BATTLE)
TASK='USER-20260930-STORY-SAVE22'
DEV='content/modernization/pr16_story_save22_development'
CP='content/modernization/pr16_story_save22_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE22_JA.md'
INPUT_SAVE=parent.OUTPUT_SAVE
OUTPUT_SAVE=dict(size=131088,sha256='bb3b6159ab12358fd051b88a592c99807b2bc14b1f9f41e952daf7a4d1a4529e')
PARTY='1db2d393d7bc515b5e3c675ee8b3c8b061b78792f18c3878a38b2edf23d7356c'
FLASH='d66139084f59fbe1cbba7ec85b8560568db06b7db92ff554668286a60f5bdc0c'
LEDGER='27f6e575912fb552fe1c4c5f7a9649c7b7e8090cbb1bfd24b7b9fccc46ff152a'
COLD_SUFFIX=b'key 0 600\nkey 2 2\nkey 0 300\nobserve 4\nkey 2 2\nkey 0 300\nobserve 5\nquit\n'
EPISODES=[(4,18,19,20,0),(24,35,36,37,1),(38,46,47,48,0),(50,61,62,63,0),(66,77,78,79,0)]
TRAINERS=[(6,102,1382,'アミカ',240),(9,108,1388,'コウガ',132),(7,94,1374,'アイク',2600),
          (5,1362,1376,'ルチア',2600),(1,97,1377,'ヘイスケ',468)]
PARTY_DELTAS=[(52,5,1),(53,20,14),(54,15,5),(55,10,5),(86,93,68),(141,42,43),(341,58,59)]
FLAG_DELTAS=[(1374,0,1),(1376,0,1),(1377,0,1),(1382,0,1),(1388,0,1),(2056,0,1),(2217,0,1)]
VAR_DELTAS=[(0x4021,92,23),(0x4022,2,3),(0x404d,8,20)]
ANCHORS={'progress':[0,4,5,6,8,13,14,15,16,18,19,20,24,25,28,31,33,34,35,36,37,38,39,46,47,48,
    50,51,54,55,56,58,61,62,63,65,66,67,68,69,72,74,76,77,78,79,80,81,82,83,84,85,86],
    'continue':[0,1,2,3]}


def plan():
    return load((ROOT/DEV/'expected.json').read_bytes())


def decode_plan(p):
    need(type(p) is dict and p.get('task')==TASK and p.get('input_save')==INPUT_SAVE and
         p.get('output_save')==OUTPUT_SAVE and p.get('candidate')==CANDIDATE,'Save21→Save22だけ')
    result={}
    for lane in ('progress','continue'):
        v=p[lane];command=inflate(v['commands_zlib_b85'],40000);commands(command)
        need(identity(command)==v['commands'],'固定入力全byte '+lane)
        raw=inflate(v['development_stdout_zlib_b85']);dev=inflate(v['development_commands_zlib_b85'],40000)
        need(identity(raw)==v['development_stdout'] and identity(dev)==v['development_commands'],'開発原本全byte '+lane)
        result[lane]=command
    need(result['progress']==inflate(p['progress']['development_commands_zlib_b85'],40000),'進行入力を採り直さない')
    need(result['continue']==inflate(p['continue']['development_commands_zlib_b85'],40000)[:-5]+COLD_SUFFIX,
         '未閉cardの後だけ退出入力。開発prefix不変')
    raw=inflate(p['continue']['development_stdout_zlib_b85']);prefix=raw[:raw.rfind(b'\n',0,-1)+1]
    need(identity(prefix)==p['continue']['development_prefix'],'cold終端行以外の原本全byte')
    return result


def trace(raw,command,seed):
    need(seed in (INPUT_SAVE,OUTPUT_SAVE),'別Saveのtraceへ一般化しない')
    value=parent.trace(raw,command,seed)
    for o in value['observations']:
        need(o['live_xy']==[v+7 for v in o['xy']],'今回は全観測で座標一致。旧電話/warp例外は使わない')
    return value


def semantic(a,b,development=False):
    need(type(development) is bool,'明示開発mode')
    ao,bo=a['observations'],b['observations']
    need(len(ao)==87 and len(bo)==(4 if development else 6) and
         (a['end']['inputs'],a['end']['frames'])==(397,41557) and
         (b['end']['inputs'],b['end']['frames'])==((30,2260) if development else (35,3464)),
         '新区間の入力/frames/全画面だけ')
    need(all(o['party_count']==4 and o['rp']==0 for o in ao+bo),'4slots/RP0')
    need(all(o['map']==[3,21] for o in ao[:80]) and all(o['map']==[1,36] for o in ao[80:]),'503→洞窟北入口だけ')
    need(ao[0]['xy']==[24,17] and ao[0]['field'] is True and ao[0]['lock']==0 and
         ao[0]['party_sha256']==parent.PARTY and ao[0]['flash_sha256']==parent.FLASH,'唯一のSave21親')
    battle_indices=set();episodes=[]
    for start,resolved,reward,returned,lock in EPISODES:
        for i in range(start,returned):
            o=ao[i];battle_indices.add(i)
            need(o['callback2']==(135394217 if i==8 else BATTLE) and o['lock']==1 and
                 o['battle_flags']==12 and o['battle_outcome']==(0 if i<resolved else 1),'単一trainer戦と交代UIの連続性')
        o=ao[returned]
        need(o['callback2']==FIELD and o['lock']==lock and o['field'] is (lock==0) and
             o['battle_flags']==12 and o['battle_outcome']==1,'決着後field callback。37は次trainer接近中で未解錠')
        need(reward==resolved+1,'勝利/賞金画面の別anchor')
        episodes.append(dict(start=start,resolved=resolved,reward=reward,field_callback=returned,
            field_lock=lock,unlocked_return_snapshot=lock==0,flags=12,outcome=1))
    for i,o in enumerate(ao):
        if i not in battle_indices:
            need(o['callback2']==FIELD and o['battle_flags']==(0 if i<4 else 12) and
                 o['battle_outcome']==(0 if i<4 else 1),'field残留を追加勝利/未復帰にしない')
    need(ao[80]['xy']==[4,6] and ao[80]['facing']==2 and ao[80]['field'] is True and ao[80]['lock']==0,
         'warp後の北入口実到達。奥の洞窟/階段は未到達')
    need(all(o['save_counter']==21 and o['flash_sha256']==parent.FLASH for o in ao[:84]),'Save前Flash全保持')
    need(all(o['save_counter']==21 and o['lock']==1 and o['flash_sha256'] not in (parent.FLASH,FLASH)
             for o in ao[84:86]),'書込途中2枚を完了にしない')
    final=ao[86]
    need(all(type(final.get(k)) is type(v) and final[k]==v for k,v in dict(map=[1,36],xy=[4,6],facing=2,
        callback2=FIELD,field=True,lock=0,save_counter=22,party_sha256=PARTY,flash_sha256=FLASH,ledger_sha256=LEDGER).items()),
         '通常Save22の完了field境界')
    for o in bo:
        need(o['map']==[1,36] and o['xy']==[4,6] and o['facing']==2 and o['save_counter']==22 and
             o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER and
             o['battle_flags']==o['battle_outcome']==0,'cold全保存状態')
    need(bo[0]['callback2']==FIELD and bo[0]['field'] is True and bo[0]['lock']==0 and
         bo[1]['callback2']==135394217 and all(o['callback2']==134777933 and o['lock']==1 and o['field'] is False for o in bo[2:4]),
         '独立Continue/party/card。開発card終端は未受入')
    if not development:
        need(bo[4]['callback2']==FIELD and bo[4]['lock']==1 and bo[4]['field'] is False and
             bo[5]['callback2']==FIELD and bo[5]['lock']==0 and bo[5]['field'] is True,'正式coldはcard/menuを閉じfieldまで')
    return dict(status='DEVELOPMENT_NOT_ACCEPTED' if development else 'PASS_ROUTE503_FIVE_TRAINERS_CHIE_ENTRANCE_SAVE22_SCOPED',
        battles=episodes,trainer_victories=5,wild_victories=0,wild_escapes=0,captures=0,losses=0,
        trainer_rewards=[dict(name_ja=t[3],trainer=t[1],yen=t[4]) for t in TRAINERS],total_reward=6040,
        ordinary_saves=1,save_counter=22,final_save_observation=final,continued=bo[-1],
        ordinary_heals=0,hm05_taught_or_used=False,hm05_root_cause_resolved=False,fixture_writes=0,
        northern_cave_entrance_reached=True,inner_cave_reached=False,all_five_returns_unlocked_snapshots=False,
        development_cold_card_end_accepted=False,save_success_wording_frame_captured=False,
        natural_growth_accepted=False,natural_evolution_accepted=False,national_dex_unlocked=False,
        natural_research_arrival_accepted=False,full_story_accepted=False,release_ready=False)


def save_structure(before,after,cold):
    need(identity(before)==INPUT_SAVE and identity(after)==OUTPUT_SAVE and after==cold,'固定Save21/22と全Save/RTC冷起動不変')
    old,ra=sectors.bank(before,0xe000,21,sectors.LAYOUT);new,rb=sectors.bank(after,0,22,sectors.LAYOUT)
    _,rc=sectors.bank(after,0xe000,21,sectors.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'Save21 bank全57344bytes不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u!=v]
    need(changes==PARTY_DELTAS and identity(y)['sha256']==PARTY,'party600bytesの全7byte差分。4技/EXP/装備不変')
    need(struct.unpack_from('<I',before,old[1]+52)[0]==struct.unpack_from('<I',after,new[1]+52)[0]==4,'4slots')
    for i,(species,exp,hp,maxhp) in enumerate(((150,1250000,324,354),(850,1250000,294,294),(151,1059860,342,342),(690,1000000,300,300))):
        mon=y[i*100:(i+1)*100]
        need(struct.unpack_from('<H',mon,32)[0]==species and struct.unpack_from('<I',mon,36)[0]==exp and
             mon[84]==100 and struct.unpack_from('<I',mon,80)[0]==0 and struct.unpack_from('<HH',mon,86)==(hp,maxhp),'支援個体の種族/EXP/Lv100/状態/HP')
    need(y[244:256]==bytes(12) and y[344:356]==bytes(12),'Mew/Bibarelの4技/PPは空のまま')
    a,ma=shared.bag(before,old);b,mb=shared.bag(after,new)
    need(a==b and (ma,mb)==(6256,12296) and a['machines'][:2]==[(343,1),(303,1)],'全Bag slot不変/HM05保持/新5勝6040円')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'boxed PC全section')
    x13=before[old[13]:old[13]+0xff4];y13=after[new[13]:new[13]+0xff4]
    need(x[400:]==y[400:] and x13[:0x7d0]==y13[:0x7d0] and x13[0xde6:]==y13[0xde6:],'未使用party/PC/tail')
    need(s61e_record(x13[0x7d0:0xde6])==s61e_record(y13[0x7d0:0xde6]),'S61E全payload保持/CRC/反転値')
    fa,va=sectors.legacy_state(before,old);fb,vb=sectors.legacy_state(after,new)
    fd=[(8*i+j,(u>>j)&1,(v>>j)&1) for i,(u,v) in enumerate(zip(fa,fb)) for j in range(8) if (u^v)&(1<<j)]
    vd=[(0x4000+i,u,v) for i,(u,v) in enumerate(zip(va,vb)) if u!=v]
    need(fd==FLAG_DELTAS and vd==VAR_DELTAS,'全legacy差分。trainer5bit・洞窟flag2bitと補助var3件')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and
         not ((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==6 and va[0x72]==vb[0x72]==1,'NationalDex未解禁/4071・4072保持')
    need(sum(bool(fa[i//8]&(1<<(i%8))) for i in range(2080,2088))==
         sum(bool(fb[i//8]&(1<<(i%8))) for i in range(2080,2088))==1,'badge1だけ保全')
    return dict(party_changed_bytes=changes,party_exp_species_level_moves_held_items_unchanged=True,
        other_party_byte_scope_ja='slot1/3のoffset41が各+1。なつき度owner/全因果の受入にはしない。',
        money_before=ma,money_after=mb,all_bag_slots_preserved=True,hm05_retained=True,
        physical_flag_deltas=fd,legacy_var_deltas=vd,s61e_payload_deltas=[],s61e_crc_and_complement_verified=True,
        auxiliary_flag2056_and_vars_runtime_owners_claimed=False,sector_checksum_checks=42,
        sector_reports=dict(input21=ra,output22=rb,retained21=rc),previous_bank_preserved_bytes=57344,
        pc_full_sections_preserved=list(range(5,13)),pc_chunk13_payload_preserved_bytes=2000,unused_party_bytes_preserved=200,
        national_dex_magic=0,national_var404e=0,national_flag840=0,story_vars={'4071':6,'4072':1},badge_count=1,
        all_save_rtc_preserved_after_continue=True)


def owners(raw):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,MAP_GROUPS_POINTER_SITE,_decode_map_scripts
    need(identity(raw)==CANDIDATE,'固定ROM')
    r=RomImage('save22',raw);groups=r.u32(MAP_GROUPS_POINTER_SITE);route=source.map_view(raw,groups,3,21)
    cave=source.map_view(raw,groups,1,36)
    locations=[([21,27],154580515),([10,31],154581291),([14,35],154626579),([13,40],154626899),([12,49],154627027)]
    remap=raw[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==sectors.TABLE_SHA,'固定trainer remap表')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]));result=[]
    for (local,tid,physical,name,yen),(xy,address) in zip(TRAINERS,locations):
        obj=[o for o in route['objects'] if o['local_id']==local]
        need(obj==[dict(local_id=local,xy=xy,script=address,flag=0)],'新trainerの実object')
        w=ScriptWalker(r);w.add_root(ScriptRoot(address,'trainer-'+str(tid),'object'));g=w.walk()
        need(not g['diagnostics'] and len(g['nodes'])==6,'新trainer root完全decode')
        refs=[q for q in g['references'] if q['category']=='trainer' and q['access']=='battle' and q['instruction_address']==address]
        need(len(refs)==1 and refs[0]['value']==tid and refs[0]['battle_type']==0 and
             mapping.get(tid+0x500,tid+0x500)==physical,'通常trainerと保存physical bit。rematchを受入しない')
        result.append(dict(object=obj[0],trainer=tid,physical_bit=physical,name_ja=name,reward_yen=yen,graph=g))
    need(route['warps'][0]==dict(id=0,xy=[15,56],elevation=0,target_warp=1,target_map=[1,36]) and
         cave['warps'][1]==dict(id=1,xy=[4,6],elevation=3,target_warp=0,target_map=[3,21]),'往路実warp/対応出口table')
    roots,_,rows=_decode_map_scripts(r,r.u32(cave['header']+8),'map:1:36')
    need(rows==[dict(type=3,pointer=135682164,table_address=135682158)] and len(roots)==1,'洞窟headerのtype3 owner')
    w=ScriptWalker(r);w.add_root(roots[0]);g=w.walk()
    need(not g['diagnostics'] and len(g['nodes'])==1 and
         [(q['instruction_address'],q['value']) for q in g['references'] if q['category']=='fly_flag' and q['access']=='set_world_map']==[(135682164,2217)],
         '世界地図flag2217の直接owner。fly使用/奥の到達とは別')
    pointer=struct.unpack_from('<I',raw,0xdb224)[0];need(pointer==0x083c4b28,'checksum table owner')
    sectors.layout_table(raw[pointer-0x08000000:pointer-0x08000000+56])
    return dict(trainers=result,outbound_warp=route['warps'][0],paired_exit=cave['warps'][1],cave_script=g,
        trainer_roots=5,trainer_nodes=30,cave_nodes=1,graph_diagnostics=0,inner_cave_arrival_accepted=False,
        return_warp_executed=False,rematches_accepted=False,world_map_flag2217_owner_verified=True,
        flag2056_runtime_owner_resolved=False,auxiliary_vars_runtime_owners_resolved=False)


def verify(folder,development=False):
    folder=Path(folder);p=plan();cmds=decode_plan(p);parsed={}
    for lane,seed in (('progress',INPUT_SAVE),('continue',OUTPUT_SAVE)):
        command=(folder/lane/'commands.txt').read_bytes();stdout=(folder/lane/'stdout.txt').read_bytes()
        expected=inflate(p[lane]['development_commands_zlib_b85'],40000) if development else cmds[lane]
        need(command==expected and not (folder/lane/'stderr.txt').read_bytes(),'実入力/stderr '+lane)
        if lane=='progress' or development:need(identity(stdout)==p[lane]['development_stdout'],'開発stdout全byte '+lane)
        else:
            n=p[lane]['development_prefix']['size'];need(identity(stdout[:n])==p[lane]['development_prefix'],'開発cold prefix全byte不変')
        parsed[lane]=trace(stdout,command,seed);screens=parsed[lane]['screens']
        need({q.name for q in (folder/lane).glob('screen-*.ppm')}=={f"screen-{s['screen']:04d}.ppm" for s in screens},'全画面集合')
        for s in screens:screen_bytes((folder/lane/f"screen-{s['screen']:04d}.ppm").read_bytes(),s,blank_allowed=True)
        e=load((folder/lane/'execution.json').read_bytes())
        need(e.get('returncode')==0 and type(e.get('returncode')) is int and e.get('initial_save')==seed and e.get('final_save')==OUTPUT_SAVE and
             type(e.get('native_processes')) is int and e['native_processes']==1 and e.get('automatic_retry') is False,'実process会計')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT_SAVE,'各process終端Save全byte')
    review=p['visual_review'];need(len(review)==sum(map(len,ANCHORS.values())) and len({(x['lane'],x['observe']) for x in review})==len(review),'目視anchor全集合')
    for lane,ids in ANCHORS.items():need(sorted(x['observe'] for x in review if x['lane']==lane)==ids,'全必須anchor')
    for x in review:
        s=parsed[x['lane']]['screens'][x['observe']];need(s['sha256']==x['sha256'] and bool(x['note_ja']),'目視と正式pixel結合')
        screen_bytes((folder/x['lane']/f"screen-{x['observe']:04d}.ppm").read_bytes(),s)
    before=(folder/'input.srm').read_bytes();after=(folder/'story-fast.srm').read_bytes();cold=(folder/'cold.srm').read_bytes()
    result=semantic(parsed['progress'],parsed['continue'],development)
    need(identity((folder/'runner').read_bytes())==RUNNER,'固定runner')
    result.update(save_structure=save_structure(before,after,cold),rom_owners=owners((folder/'candidate.gba').read_bytes()),
        input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,candidate=CANDIDATE,progress_inputs=397,cold_inputs=30 if development else 35,
        progress_frames=41557,cold_frames=2260 if development else 3464,screens=91 if development else 93,
        visual_review_anchors=len(review),accepted_case_reruns=0,compiles=0,rom_changes=0)
    return result,shared.byte_ledger(before,after)
