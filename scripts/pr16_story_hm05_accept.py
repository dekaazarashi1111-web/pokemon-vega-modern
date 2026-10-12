#!/usr/bin/env python3
"""Save19→通常HM05取得→Save20専用。旧受入の実行/判定/ROMは変更しない。"""
from __future__ import annotations
import base64
import json
from pathlib import Path
import struct
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_gym_accept as gym
import pr16_story_after_maori as source
import pr16_story_fast_maori as shared
import pr16_story_ayame_persistence_audit as sectors
from pr16_story_ayame_accept import s61e_record
from pr16_story_after_home import (need,identity,load,integer,digest,commands,screen_bytes,
    BOOT,OBS_INTS,OBS_HASH,OBS_KEYS,END_KEYS,CANDIDATE,RUNNER)
TASK='USER-20260929-STORY-HM05'
DEV='content/modernization/pr16_story_hm05_development'
CP='content/modernization/pr16_story_hm05_checkpoint.json'
GUIDE='docs/PR16_STORY_HM05_JA.md'
INPUT_SAVE=gym.OUTPUT_SAVE
OUTPUT_SAVE=dict(size=131088,sha256='2ed14acca7a475598bde7098f68f4c8a8f0fb131ad8f2bc8ad6e4b508c1d08e5')
FIELD,BATTLE,LOADING=gym.FIELD,gym.BATTLE,135048649
PARTY='099deb42752e42d8ad72cb39cb511c51e82db51e52dad079eaeaeb4f095b02ed'
FLASH='52a063df6eb537fc5ecbf7a7f7a66049f3f81bbbaa95f1c94c4db8909a16fd89'
LEDGER='29f171fbd51589dafa45e81b066b1b6f90deeded7c4c6b74dee2706c63c85bcb'
COLD_LEDGER='696a9901628fbf9a1637a8db9388670438aae018ba9244a1cf817525319268d7'
ANCHORS=dict(progress=[0,10,12,19,21,22,25,26,30,31,32,34,35,37,38,39,41,43,45,49,50,55,57,58,60,62,64,68,69,70],
             **{'continue':[0,2,5,7,8]})


def inflate(encoded,limit=400000):
    need(type(encoded) is str and 0<len(encoded)<limit,'圧縮textの上限')
    try:
        dec=zlib.decompressobj();value=dec.decompress(base64.b85decode(encoded),limit+1)
    except (ValueError,zlib.error) as exc:raise ValueError('圧縮text形式') from exc
    need(len(value)<=limit and dec.eof and not dec.unused_data and not dec.unconsumed_tail,'単一完全text stream')
    return value


def decode_plan(plan):
    need(type(plan) is dict and plan.get('task')==TASK and plan.get('input_save')==INPUT_SAVE and
         plan.get('output_save')==OUTPUT_SAVE and plan.get('candidate')==CANDIDATE,'Save19親/Save20後継だけ')
    result={}
    for lane in ('progress','continue'):
        value=inflate(plan[lane]['commands_zlib_b85'],40000);commands(value)
        need(identity(value)==plan[lane]['commands'],'入力全byte '+lane);result[lane]=value
    return result


def coordinate_boundary(o,seed):
    if o['live_xy']==[v+7 for v in o['xy']]:return
    # Save座標は転送先、live objectは転送元のままの黒画面1枚。field受入には使わない。
    need(seed==INPUT_SAVE and all(o.get(k)==v for k,v in dict(observe=1,frame=1530,
        map=[3,1],xy=[16,12],live_xy=[14,15],facing=1,callback2=LOADING,lock=0,
        field=False,save_counter=19,party_count=4,rp=0,battle_flags=0,battle_outcome=0,
        party_sha256=gym.PARTY,flash_sha256=gym.FLASH,ledger_sha256=gym.LEDGER).items()),
        '座標不一致は宣言済みload中1枚だけ。field/他map/他Saveへの一般化禁止')


def trace(raw, command, seed):
    """保存helperを使わず入力↔JSONLを一対一照合。旧field判定を書換えない。"""
    need(type(seed) is dict and set(seed) == {'size','sha256'} and type(seed['size']) is int and seed['size'] == 131088 and digest(seed['sha256']) and type(raw) is bytes and 0 < len(raw) < 400000 and raw.endswith(b'\n'), '原本/種別')
    lines = commands(command)
    rows = [load(x) for x in raw.splitlines()]
    need(all(type(r) is dict for r in rows) and len(rows) >= 16, '行object/schema')
    start = rows[0]
    expected_seed = seed
    need(set(start) == {'begin','candidate_sha256','initial_save_sha256','host_write_barriers'} and
         start['begin'] == 'INDEPENDENT_CONTINUE' and start['candidate_sha256'] == CANDIDATE['sha256'] and
         start['initial_save_sha256'] == expected_seed['sha256'] and
         type(start['host_write_barriers']) is int and start['host_write_barriers'] == 7, '開始境界')
    cursor, frame, input_count = 1, 0, 0
    observations, screens = [], []

    def take_key(key, frames):
        nonlocal cursor, frame, input_count
        need(cursor < len(rows), '入力行欠落')
        r = rows[cursor]
        need(set(r) == {'input','frame','key','frames'} and all(integer(v) for v in r.values()) and
             r == dict(input=input_count, frame=frame, key=key, frames=frames), '実入力/frame原本不一致')
        frame += frames; input_count += 1; cursor += 1
        need(frame <= 1800000, 'frame上限')

    def take_observe(n):
        nonlocal cursor
        need(cursor+1 < len(rows), '画面対欠落')
        r,screen = rows[cursor:cursor+2]
        need(set(r) == OBS_KEYS and all(integer(r[k], high=0xffffffff) for k in OBS_INTS) and
             all(digest(r[k]) for k in OBS_HASH) and type(r['field']) is bool, '観測schema')
        for k in ('map','xy','live_xy'):
            need(type(r[k]) is list and len(r[k]) == 2 and all(integer(v,high=65535) for v in r[k]), '座標schema')
        need(r['observe'] == n and r['frame'] == frame and r['lock'] in (0,1) and r['party_count'] <= 6,
             '観測frame/lock/party')
        coordinate_boundary(r,seed)
        need(set(screen) == {'screen','frame','sha256'} and type(screen['screen']) is int and
             type(screen['frame']) is int and screen['screen'] == n and screen['frame'] == frame and
             digest(screen['sha256']), '画面と観測の同frame')
        observations.append(r); screens.append(screen); cursor += 2

    for k,f in BOOT:
        take_key(k,f)
    take_observe(0)
    for line in lines[:-1]:
        p = line.split()
        if p[0] == 'key':
            take_key(int(p[1]),int(p[2]))
        else:
            take_observe(int(p[1]))
    need(cursor == len(rows)-1, '余剰行/隠し保存')
    end = rows[cursor]
    need(set(end) == END_KEYS and end['end'] == 'STORY_INPUT_CHECKPOINT' and
         all(integer(end[k]) for k in END_KEYS-{'end','natural_research_arrival_accepted'}) and
         end['frames'] == frame and end['inputs'] == input_count and end['host_write_barriers'] == 7 and
         end['warnings_errors'] == end['guarded_host_writes'] == end['fixture_calls'] == 0 and
         end['natural_research_arrival_accepted'] is False, '終端/書込禁止/過大受入')
    return dict(start=start, observations=observations, screens=screens, end=end)


def episodes(obs):
    need(type(obs) is list and len(obs)==71,'今回の全71観測')
    result=[];active=None
    for i,o in enumerate(obs):
        need(type(o) is dict and all(type(o.get(k)) is int for k in OBS_INTS) and
             o['observe']==i and (i==0 or obs[i-1]['frame']<o['frame']),'観測整数/順序')
        cb=o['callback2'];outcome=o['battle_outcome'];flags=o['battle_flags']
        need(cb in (FIELD,BATTLE,LOADING),'この新区間のcallback')
        if cb==BATTLE:
            need(o['map']==[3,20] and o['save_counter']==19 and o['party_count']==4 and o['rp']==0 and
                 o['lock']==1 and flags in (4,12) and outcome in ((0,1) if flags==12 else (0,4)),
                 'trainer勝利と野生離脱だけ。捕獲/敗北は別scope')
            if active is None:
                need(outcome==0 and i>0 and obs[i-1]['callback2']==FIELD,'新戦闘reset')
                active=dict(start=i,resolved=None,field_return=None,flags=flags,outcome=1 if flags==12 else 4)
            need(active['flags']==flags and (outcome==active['outcome'] or active['resolved'] is None),'戦闘type/解決後reset')
            if outcome==active['outcome'] and active['resolved'] is None:active['resolved']=i
        elif active is not None:
            need(cb==FIELD and o['lock']==0 and active['resolved'] is not None and outcome==active['outcome'],
                 '未解決/未解錠を勝利・離脱へ昇格しない')
            active['field_return']=i;result.append(active);active=None
    need(active is None and result==[
        dict(start=12,resolved=19,field_return=22,flags=12,outcome=1),
        dict(start=25,resolved=30,field_return=32,flags=12,outcome=1),
        dict(start=42,resolved=45,field_return=46,flags=4,outcome=4),
        dict(start=49,resolved=50,field_return=51,flags=4,outcome=4)],'新2勝/野生2離脱の独立4区間だけ')
    return result


def semantic(a,b,development=False):
    need(type(development) is bool,'明示開発mode')
    ao,bo=a['observations'],b['observations'];battle=episodes(ao)
    need(a['end']['inputs']==248 and a['end']['frames']==23900 and
         b['end']['inputs']==(56 if development else 59) and b['end']['frames']==(3268 if development else 3690) and
         len(bo)==(10 if development else 11),'実入力/frame/画面会計')
    need(ao[0]['map']==[5,4] and ao[0]['xy']==[7,4] and ao[0]['field'] is True and
         ao[0]['party_sha256']==gym.PARTY and ao[0]['flash_sha256']==gym.FLASH and
         ao[0]['battle_flags']==ao[0]['battle_outcome']==0,'受入済みSave19からだけ')
    need(ao[1]['callback2']==LOADING and ao[1]['field'] is False and ao[2]['callback2']==FIELD and
         ao[2]['map']==[3,1] and ao[2]['live_xy']==[23,24],'load途中を実到達と区別')
    need(all(o['party_count']==4 and o['rp']==0 for o in ao+bo),'4slots/RP0')
    route=[]
    for o in ao:
        if not route or route[-1]!=o['map']:route.append(o['map'])
    need(route==[[5,4],[3,1],[3,20],[3,11],[3,20],[3,11],[3,20],[3,1],[5,4]],'通常往復routeだけ')
    need(all(o['map']==[3,20] and o['xy']==[7,5] and o['facing']==2 for o in ao[34:42]) and
         ao[34]['lock']==ao[41]['lock']==0 and all(o['lock']==1 for o in ao[35:41]),'HM05 NPC通常会話区間')
    need(ao[57]['party_sha256']!=ao[58]['party_sha256'] and
         all(o['party_sha256']==PARTY for o in ao[58:]+bo),'通常PC回復と保存600bytes')
    need(all(o['save_counter']==19 and o['flash_sha256']==gym.FLASH for o in ao[:64]),'保存前Flash不変')
    need(all(o['save_counter']==19 and o['flash_sha256'] not in (gym.FLASH,FLASH) and o['lock']==1 for o in ao[64:69]),
         '5枚の部分書込みを完了にしない')
    need(all(o['save_counter']==20 and o['flash_sha256']==FLASH and o['callback2']==FIELD and
         o['lock']==0 and o['map']==[5,4] and o['xy']==[7,4] for o in ao[69:]),'Save20安定保存境界')
    # 旧si_fieldの追加条件(q/p)は変更せずfalseを保全。normal menu保存/coldが独立証明。
    need(ao[-1]['field'] is False and ao[-1]['ledger_sha256']==LEDGER,'旧field観測を改竄しない')
    for o in bo:
        need(o['map']==[5,4] and o['xy']==[7,4] and o['facing']==2 and o['save_counter']==20 and
             o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['battle_flags']==o['battle_outcome']==0,
             '独立coldの保存境界')
    need(bo[0]['field'] is True and bo[0]['lock']==0 and bo[0]['ledger_sha256']==COLD_LEDGER and
         all(o['ledger_sha256']==LEDGER for o in bo[1:]),'cold最初のledgerとUI後のledgerを混同しない')
    need([bo[i]['callback2'] for i in (2,5,7,8)]==[135301605,135471253,135394217,134777933],
         '実Bag/HMケース/party/card callbacks')
    if not development:need(bo[-1]['callback2']==FIELD and bo[-1]['field'] is True and bo[-1]['lock']==0,
                            '正式coldはmenu閉じ後field解錠まで')
    return dict(status='DEVELOPMENT_NOT_ACCEPTED' if development else 'PASS_HM05_SAVE20_SCOPED',
        battles=battle,trainer_victories=2,wild_escapes=2,wild_victories=0,captures=0,losses=0,
        ordinary_item343_grants=1,ordinary_heals=1,ordinary_saves=1,save_counter=20,
        final_save_observation=ao[-1],continued=bo[-1],legacy_field_predicate_preserved=True,
        save_success_wording_frame_captured=False,hm05_taught_or_used=False,natural_growth_accepted=False,
        natural_evolution_accepted=False,national_dex_unlocked=False,natural_research_arrival_accepted=False,
        full_story_accepted=False,release_ready=False)


def save_structure(before,after,cold):
    need(all(type(x) is bytes and len(x)==131088 for x in (before,after,cold)) and after==cold,'全Save/RTC冷起動不変')
    old,ra=sectors.bank(before,0xe000,19,sectors.LAYOUT);new,rb=sectors.bank(after,0,20,sectors.LAYOUT)
    _,rc=sectors.bank(after,0xe000,19,sectors.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'Save19 bank全57344bytes不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u!=v]
    need(changes==[(41,4,6),(258,0,1),(341,57,58),(358,0,1)] and identity(y)['sha256']==PARTY,
         'party全600bytes: 友情2bytes/EV欄offset58の2bytesだけ')
    need(struct.unpack_from('<I',before,old[1]+52)[0]==struct.unpack_from('<I',after,new[1]+52)[0]==4,'4slots')
    for i,(species,exp,hp) in enumerate(((150,1250000,354),(850,1250000,294),(151,1059860,342),(690,1000000,300))):
        mon=y[i*100:(i+1)*100]
        need(struct.unpack_from('<H',mon,32)[0]==species and struct.unpack_from('<I',mon,36)[0]==exp and
             mon[84]==100 and struct.unpack_from('<I',mon,80)[0]==0 and struct.unpack_from('<HH',mon,86)==(hp,hp),
             '支援species/EXP/Lv100/全回復。不自然育成を合格にしない')
    a,ma=shared.bag(before,old);b,mb=shared.bag(after,new)
    need(ma==5776 and mb==6016,'通常賞金128+112円のみ')
    for pocket in a:
        expected=list(a[pocket])
        if pocket=='machines':
            need(expected[1]==(0,0) and not any(item==343 for item,count in expected),'HM05未所持の親')
            expected[1]=(343,1)
        need(b[pocket]==expected,'Bag全slot境界 '+pocket)
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'boxed PC全section')
    x13=before[old[13]:old[13]+0xff4];y13=after[new[13]:new[13]+0xff4]
    need(x[400:]==y[400:] and x13[:0x7d0]==y13[:0x7d0] and x13[0xde6:]==y13[0xde6:],'未使用party/PC/tail')
    need(s61e_record(x13[0x7d0:0xde6])==s61e_record(y13[0x7d0:0xde6]),'S61E payload不変/CRC/反転値')
    fa,va=sectors.legacy_state(before,old);fb,vb=sectors.legacy_state(after,new)
    fd=[(8*i+j,(u>>j)&1,(v>>j)&1) for i,(u,v) in enumerate(zip(fa,fb)) for j in range(8) if (u^v)&(1<<j)]
    vd=[(0x4000+i,u,v) for i,(u,v) in enumerate(zip(va,vb)) if u!=v]
    need(fd==[(1371,0,1),(1396,0,1)] and vd==[(0x4021,46,24),(0x4022,3,0)],'全legacy差分')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and
         not ((fa[0x840//8]|fb[0x840//8])&1) and va[0x71]==vb[0x71]==5 and va[0x72]==vb[0x72]==1,
         '全国図鑑未解禁/story stage維持')
    need(bool(fa[2080//8]&(1<<(2080%8))) and bool(fb[2080//8]&(1<<(2080%8))),'badge1保全')
    return dict(party_changed_bytes=changes,party_exp_species_level_unchanged=True,
        party_ev_delta_scope='slots2/3のEV欄offset58:0→1。EV因果全ケース/自然育成の受入ではない。',
        money_before=ma,money_after=mb,machine_slot_delta=[1,[0,0],[343,1]],all_other_bag_slots_preserved=True,
        physical_flag_deltas=fd,legacy_var_deltas=vd,s61e_payload_unchanged=True,s61e_crc_and_complement_verified=True,
        sector_checksum_checks=42,sector_reports=dict(input19=ra,output20=rb,retained19=rc),
        previous_bank_preserved_bytes=57344,pc_full_sections_preserved=list(range(5,13)),
        pc_chunk13_payload_preserved_bytes=2000,unused_party_bytes_preserved=200,
        national_dex_magic=0,national_var404e=0,national_flag840=0,badge_count=1,all_save_rtc_preserved_after_continue=True)


def owners(raw):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,MAP_GROUPS_POINTER_SITE
    need(identity(raw)==CANDIDATE,'固定ROM')
    r=RomImage('hm05',raw);groups=r.u32(MAP_GROUPS_POINTER_SITE);view=source.map_view(raw,groups,3,20)
    roots=[o for o in view['objects'] if o['local_id'] in (5,8,9)]
    need(roots==[dict(local_id=5,xy=[7,4],script=138584742,flag=0),
                 dict(local_id=8,xy=[22,6],script=154626195,flag=0),
                 dict(local_id=9,xy=[31,11],script=154582147,flag=0)],'実map objects')
    owners=[]
    for o in roots:
        walker=ScriptWalker(r);walker.add_root(ScriptRoot(o['script'],'route502-'+str(o['local_id']),'object'))
        graph=walker.walk();need(not graph['diagnostics'],'ROM root完全decode')
        refs=graph['references']
        if o['local_id']==5:
            items=[(q['command'],q['value'],q['instruction_address']) for q in refs if q['category']=='item']
            need(items==[('checkitem',343,138584744),('checkitemspace',343,138584768),('additem',343,138584784)],
                 'HM05通常grant owner')
        else:
            normal=[q['value'] for q in refs if q['category']=='trainer' and q['access']=='battle' and
                    q['instruction_address']==o['script'] and q['battle_type']==0]
            need(normal==([91] if o['local_id']==8 else [116]),'通常戦と未実行rematchを区別')
        owners.append(dict(object=o,references=refs,unexecuted_branches_accepted=False))
    remap=raw[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==sectors.TABLE_SHA,'固定remap表')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]))
    physical=[(t,mapping.get(t+0x500,t+0x500)) for t in (91,116)]
    need(physical==[(91,1371),(116,1396)],'通常2勝の保存physical bit')
    pointer=struct.unpack_from('<I',raw,0xdb224)[0];need(pointer==0x083c4b28,'section checksum table owner')
    sectors.layout_table(raw[pointer-0x08000000:pointer-0x08000000+56])
    return dict(map=[3,20],owners=owners,trainer_physical_mapping=physical,hm05_item_id=343,
                hm05_taught_or_used=False,unexecuted_rematches_accepted=False)


def verify(folder,development=False):
    folder=Path(folder);plan=load((ROOT/DEV/'expected.json').read_bytes());cmds=decode_plan(plan);parsed={}
    for lane,seed in (('progress',INPUT_SAVE),('continue',OUTPUT_SAVE)):
        command=(folder/lane/'commands.txt').read_bytes();stdout=(folder/lane/'stdout.txt').read_bytes()
        expected=inflate(plan[lane]['development_commands_zlib_b85'],40000) if development else cmds[lane]
        need(command==expected and not (folder/lane/'stderr.txt').read_bytes(),'実入力/stderr '+lane)
        if lane=='progress':need(identity(stdout)==plan[lane]['stdout'],'progress全stdout')
        elif development:need(identity(stdout)==plan[lane]['development_stdout'],'開発cold全stdout')
        else:
            n=plan[lane]['development_prefix']['size']
            need(identity(stdout[:n])==plan[lane]['development_prefix'],'開発cold原本prefix全byte保持')
        parsed[lane]=trace(stdout,command,seed)
        screens=parsed[lane]['screens']
        need({p.name for p in (folder/lane).glob('screen-*.ppm')}=={f"screen-{s['screen']:04d}.ppm" for s in screens},'全画面集合')
        for s in screens:screen_bytes((folder/lane/f"screen-{s['screen']:04d}.ppm").read_bytes(),s,blank_allowed=True)
    review=plan['visual_review'];need(len(review)==35 and len({(x['lane'],x['observe']) for x in review})==35,'35目視anchor')
    for lane,ids in ANCHORS.items():need(sorted(x['observe'] for x in review if x['lane']==lane)==ids,'anchor全集合')
    for x in review:
        s=parsed[x['lane']]['screens'][x['observe']];need(s['sha256']==x['sha256'],'目視と正式pixel結合')
        screen_bytes((folder/x['lane']/f"screen-{x['observe']:04d}.ppm").read_bytes(),s)
    before=(folder/'input.srm').read_bytes();after=(folder/'story-fast.srm').read_bytes();cold=(folder/'cold.srm').read_bytes()
    need(identity(before)==INPUT_SAVE and identity(after)==OUTPUT_SAVE and after==cold,'親Save19/後継Save20全byte')
    result=semantic(parsed['progress'],parsed['continue'],development)
    result.update(save_structure=save_structure(before,after,cold),rom_owners=owners((folder/'candidate.gba').read_bytes()),
        input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,candidate=CANDIDATE,progress_inputs=248,cold_inputs=56 if development else 59,
        progress_frames=23900,cold_frames=3268 if development else 3690,screens=81 if development else 82,
        visual_review_anchors=35,accepted_case_reruns=0,compiles=0,rom_changes=0)
    return result,shared.byte_ledger(before,after)
