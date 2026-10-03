#!/usr/bin/env python3
"""Save20後のHM05拒否・503番道路新1勝・電話イベント・Save21限定oracle。"""
from __future__ import annotations
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_hm05_accept as parent
from pr16_story_hm05_accept import (need,identity,load,integer,digest,commands,screen_bytes,
    BOOT,OBS_INTS,OBS_HASH,OBS_KEYS,END_KEYS,CANDIDATE,RUNNER,inflate,source,shared,sectors,s61e_record)
TASK='USER-20260930-STORY-SAVE21'
DEV='content/modernization/pr16_story_save21_development'
CP='content/modernization/pr16_story_save21_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE21_JA.md'
INPUT_SAVE=parent.OUTPUT_SAVE
OUTPUT_SAVE=dict(size=131088,sha256='c9cb14fa73a38e105a0e6553f7fc1dc82c9bdd182e0409e28022c8ffe44b3d20')
FIELD,BATTLE=parent.FIELD,parent.BATTLE
PARTY='2f97dcf5846ac8375f80e8b0a357ed6a3f6e17d5c6a4861b01a9fdb7798a2dab'
FLASH='0c89e42976fc91c7a76be3d055bdd053f235b03c8e6b677ae805fec76e96b6d5'
LEDGER='6209190e76a87dda213464e48d9f187744c5605069dd0f1f9f629330d9670aed'
ANCHORS=dict(progress=[0,5,7,8,10,16,18,19,22,24,25,26,28,29,31,32,34,35,37,38,40,41,42,43,44,45,46,47,49,50,51,52,53,54],
             **{'continue':[0,2,3,4]})


def decode_plan(plan):
    need(type(plan) is dict and plan.get('task')==TASK and plan.get('input_save')==INPUT_SAVE and
         plan.get('output_save')==OUTPUT_SAVE and plan.get('candidate')==CANDIDATE,'Save20からSave21だけ')
    result={}
    for lane in ('progress','continue'):
        value=inflate(plan[lane]['commands_zlib_b85'],40000);commands(value)
        need(identity(value)==plan[lane]['commands'],'入力全byte '+lane);result[lane]=value
    need(result['continue']==inflate(plan['continue']['development_commands_zlib_b85'],40000)[:-5]+
         b'key 0 180\nkey 2 2\nkey 0 240\nobserve 5\nquit\n','開発cold原本の後だけmenu閉じ')
    return result


def coordinate_boundary(o,seed):
    if o['live_xy']==[v+7 for v in o['xy']]:return
    # coordイベントはlive y=17で開始。save座標の同期遅れ7枚だけを保持し、解錠/到達にしない。
    frames=[13516,13866,13988,14120,14252,14434,14556]
    n=o['observe'];need(seed==INPUT_SAVE and type(n) is int and 40<=n<=46,'今回の7枚だけ')
    expected=dict(frame=frames[n-40],map=[3,21],xy=[24 if n==46 else 23,20],
        live_xy=[31 if n==46 else 30,24],facing=3 if n==46 else 1,callback2=FIELD,
        lock=1,field=False,save_counter=20,party_count=4,rp=0,battle_flags=12,battle_outcome=1,
        party_sha256=PARTY,flash_sha256=parent.FLASH,ledger_sha256=LEDGER)
    need(all(type(o.get(k)) is type(v) and o[k]==v for k,v in expected.items()),
         'coord会話中のSave/live座標遅れを他場面へ一般化しない')


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


def semantic(a,b,development=False):
    need(type(development) is bool,'明示開発mode')
    ao,bo=a['observations'],b['observations']
    need(len(ao)==55 and len(bo)==(5 if development else 6) and
         (a['end']['inputs'],a['end']['frames'])==(181,16528) and
         (b['end']['inputs'],b['end']['frames'])==((30,2338) if development else (33,2760)),
         '新区間だけの実入力/frame/全画面')
    need(all(o['party_count']==4 and o['rp']==0 for o in ao+bo),'party4/RP0')
    route=[]
    for o in ao:
        if not route or route[-1]!=o['map']:route.append(o['map'])
    need(route==[[5,4],[3,1],[3,21]],'Save20から503番道路だけ')
    need(ao[0]['xy']==[7,4] and ao[0]['field'] is True and ao[0]['lock']==0 and
         ao[0]['party_sha256']==parent.PARTY and ao[0]['flash_sha256']==parent.FLASH,'正確なSave20親')
    # 実case/party UIと拒否画面は別途hash付き目視anchorへ結合する。学習成功へ昇格しない。
    need([ao[i]['callback2'] for i in (5,7,8,10)]==[135471253,135394217,135394217,FIELD] and
         all(o['party_sha256']==parent.PARTY for o in ao[:23]) and ao[10]['lock']==0,
         'HM05の通常UI拒否、party全byte不変、field復帰')
    need(all(o['battle_flags']==o['battle_outcome']==0 for o in ao[:19]),'前半に戦闘追加なし')
    need([i for i,o in enumerate(ao) if o['callback2']==BATTLE]==[i for i in range(19,38) if i!=24] and
         ao[24]['callback2']==135394217 and ao[24]['lock']==1,'戦闘中の交代UI取消を新戦闘に数えない')
    need(all(o['battle_flags']==12 and o['lock']==1 and o['battle_outcome']==(0 if i<35 else 1)
         for i,o in enumerate(ao) if 19<=i<=37),'単一trainer戦。KO/敗北/逃走を勝利にしない')
    need(ao[38]['callback2']==FIELD and ao[38]['lock']==0 and ao[38]['field'] is True and
         all(o['battle_flags']==12 and o['battle_outcome']==1 for o in ao[38:]),'決着後のflags残留を重複計上しない')
    need(all(o['callback2']==FIELD for o in ao[38:]),'以降に未観測戦闘なし')
    for o in ao[40:47]:coordinate_boundary(o,INPUT_SAVE)
    need(ao[39]['lock']==0 and all(o['lock']==1 and o['field'] is False for o in ao[40:47]) and
         ao[47]['xy']==[24,17] and ao[47]['live_xy']==[31,24] and ao[47]['lock']==0 and ao[47]['field'] is True,
         '電話会話/自動移動中とfield復帰の境界')
    need(all(o['save_counter']==20 and o['flash_sha256']==parent.FLASH for o in ao[:51]),'保存前Flash不変')
    need(all(o['save_counter']==20 and o['lock']==1 and o['flash_sha256'] not in (parent.FLASH,FLASH)
             for o in ao[51:53]),'書込途中2枚を完成にしない')
    need(all(o['save_counter']==21 and o['flash_sha256']==FLASH and o['party_sha256']==PARTY and
         o['ledger_sha256']==LEDGER and o['callback2']==FIELD and o['lock']==0 and o['field'] is True and
         o['map']==[3,21] and o['xy']==[24,17] and o['facing']==3 for o in ao[53:]),'通常Save21安定境界')
    for o in bo:
        need(o['map']==[3,21] and o['xy']==[24,17] and o['facing']==3 and o['save_counter']==21 and
             o['party_sha256']==PARTY and o['flash_sha256']==FLASH and o['ledger_sha256']==LEDGER and
             o['battle_flags']==o['battle_outcome']==0,'独立Continue全保存境界')
    need(bo[0]['field'] is True and bo[0]['lock']==0 and bo[2]['callback2']==135394217 and
         bo[3]['callback2']==134777933 and bo[4]['callback2']==FIELD and bo[4]['lock']==1,'独立party/card/未閉menu')
    if not development:need(bo[5]['callback2']==FIELD and bo[5]['field'] is True and bo[5]['lock']==0,'正式coldはmenu終了後fieldまで')
    return dict(status='DEVELOPMENT_NOT_ACCEPTED' if development else 'PASS_ROUTE503_PHONE_SAVE21_SCOPED',
        battles=[dict(start=19,party_menu=24,resolved=35,field_return=38,flags=12,outcome=1)],
        trainer_victories=1,wild_escapes=0,wild_victories=0,captures=0,losses=0,
        ordinary_hm05_grants=0,hm05_attempt_rejected=True,hm05_taught_or_used=False,
        hm05_four_slots_incompatible_displayed=True,hm05_mew_rejection_explicit=True,
        hm05_root_cause_resolved=False,hm05_compatibility_fixed=False,ordinary_heals=0,
        phone_event_observed=True,story_var4071_before=5,story_var4071_after=6,
        ordinary_saves=1,save_counter=21,final_save_observation=ao[-1],continued=bo[-1],
        save_success_wording_frame_captured=False,development_cold_menu_end_accepted=False,
        legacy_field_predicate_preserved=True,natural_growth_accepted=False,natural_evolution_accepted=False,
        national_dex_unlocked=False,natural_research_arrival_accepted=False,full_story_accepted=False,release_ready=False)


def save_structure(before,after,cold):
    need(all(type(x) is bytes and len(x)==131088 for x in (before,after,cold)) and after==cold,'全Save/RTC冷起動不変')
    old,ra=sectors.bank(before,0,20,sectors.LAYOUT);new,rb=sectors.bank(after,0xe000,21,sectors.LAYOUT)
    _,rc=sectors.bank(after,0,20,sectors.LAYOUT)
    need(before[:0xe000]==after[:0xe000],'Save20 bank全57344bytes不変')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u!=v]
    need(changes==[(52,10,5),(86,98,93),(258,1,2),(358,1,2)] and identity(y)['sha256']==PARTY,
         'party600bytes: Psystrike PP10→5、HP354→349、EV欄2bytesだけ')
    need(struct.unpack_from('<I',before,old[1]+52)[0]==struct.unpack_from('<I',after,new[1]+52)[0]==4,'4slots')
    for i,(species,exp,hp,maxhp) in enumerate(((150,1250000,349,354),(850,1250000,294,294),(151,1059860,342,342),(690,1000000,300,300))):
        mon=y[i*100:(i+1)*100]
        need(struct.unpack_from('<H',mon,32)[0]==species and struct.unpack_from('<I',mon,36)[0]==exp and
             mon[84]==100 and struct.unpack_from('<I',mon,80)[0]==0 and struct.unpack_from('<HH',mon,86)==(hp,maxhp),
             '支援species/EXP/Lv100。自然成長や全回復へ昇格しない')
    need(y[244:256]==bytes(12) and y[344:356]==bytes(12),'Mew/Bibarelの4技/PPは拒否後も空')
    a,ma=shared.bag(before,old);b,mb=shared.bag(after,new)
    expected={k:list(v) for k,v in a.items()};expected['machines'][:2]=[(343,1),(303,1)]
    need(a['machines'][:2]==[(303,1),(343,1)] and b==expected and (ma,mb)==(6016,6256),
         '通常case表示でHM05/TM15順序交換だけ。全item/count不変、通常賞金240円')
    for sid in range(5,13):need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'boxed PC全section')
    x13=before[old[13]:old[13]+0xff4];y13=after[new[13]:new[13]+0xff4]
    need(x[400:]==y[400:] and x13[:0x7d0]==y13[:0x7d0] and x13[0xde6:]==y13[0xde6:],'未使用party/PC/tail')
    ea,eb=s61e_record(x13[0x7d0:0xde6]),s61e_record(y13[0x7d0:0xde6])
    ed=[(i,u,v) for i,(u,v) in enumerate(zip(ea,eb)) if u!=v]
    need(ed==[(257,1,65)],'拡張flag4366/2062のみ。S61E CRC/反転値')
    fa,va=sectors.legacy_state(before,old);fb,vb=sectors.legacy_state(after,new)
    fd=[(8*i+j,(u>>j)&1,(v>>j)&1) for i,(u,v) in enumerate(zip(fa,fb)) for j in range(8) if (u^v)&(1<<j)]
    vd=[(0x4000+i,u,v) for i,(u,v) in enumerate(zip(va,vb)) if u!=v]
    need(fd==[(1381,0,1)] and vd==[(0x4021,24,92),(0x4022,0,2),(0x4071,5,6)],'全legacy差分')
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==va[0x4e]==vb[0x4e]==0 and
         not ((fa[0x840//8]|fb[0x840//8])&1) and va[0x72]==vb[0x72]==1,'全国図鑑未解禁/var4072不変')
    need(bool(fa[2080//8]&(1<<(2080%8))) and bool(fb[2080//8]&(1<<(2080%8))),'badge1保全')
    return dict(party_changed_bytes=changes,party_exp_species_level_unchanged=True,
        party_ev_delta_scope='slots2/3のEV欄offset58:1→2。EV因果全ケース/自然育成の受入ではない。',
        money_before=ma,money_after=mb,all_bag_slots_preserved=False,inventory_items_counts_preserved=True,
        machine_slot_sort_before=[[303,1],[343,1]],machine_slot_sort_after=[[343,1],[303,1]],
        all_other_bag_slots_preserved=True,hm05_retained=True,
        physical_flag_deltas=fd,legacy_var_deltas=vd,s61e_payload_deltas=ed,
        s61e_flag4366_index2062_set=True,s61e_crc_and_complement_verified=True,
        sector_checksum_checks=42,sector_reports=dict(input20=ra,output21=rb,retained20=rc),
        previous_bank_preserved_bytes=57344,pc_full_sections_preserved=list(range(5,13)),
        pc_chunk13_payload_preserved_bytes=2000,unused_party_bytes_preserved=200,
        national_dex_magic=0,national_var404e=0,national_flag840=0,badge_count=1,all_save_rtc_preserved_after_continue=True)


def owners(raw):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,MAP_GROUPS_POINTER_SITE
    need(identity(raw)==CANDIDATE,'固定ROM')
    r=RomImage('save21',raw);groups=r.u32(MAP_GROUPS_POINTER_SITE);view=source.map_view(raw,groups,3,21)
    obj=[o for o in view['objects'] if o['local_id']==3]
    need(obj==[dict(local_id=3,xy=[13,12],script=154580387,flag=0)],'トシヒデの実object')
    walker=ScriptWalker(r);walker.add_root(ScriptRoot(obj[0]['script'],'trainer101','object'))
    trainer=walker.walk();need(not trainer['diagnostics'],'trainer root完全decode')
    need([q['value'] for q in trainer['references'] if q['category']=='trainer' and q['access']=='battle' and
          q['instruction_address']==obj[0]['script'] and q['battle_type']==0]==[101],'通常101。rematch1027を受入にしない')
    events=r.u32(view['header']+4);need(r.u8(events+2)==4,'coord全4件')
    coordptr=r.u32(events+12);coords=[]
    for i in range(4):
        row=r.raw(coordptr+i*16,16);x,y,elev,unused,var,value,pad,target=struct.unpack('<HHBBHHHI',row)
        coords.append(dict(x=x,y=y,elevation=elev,var=var,value=value,script=target))
    need(coords==[dict(x=21+i,y=17,elevation=3,var=0x4071,value=5,script=0x08e1aca0+96*i) for i in range(4)],
         '実coord条件。現区間はx23/live y17。未実行x21/22/24を到達済みにしない')
    walker=ScriptWalker(r);walker.add_root(ScriptRoot(coords[2]['script'],'phone-x23','coord'));phone=walker.walk()
    need(not phone['diagnostics'] and len(phone['nodes'])==2,'電話の到達root2nodes完全decode')
    need([(q['instruction_address'],q['operand']) for q in phone['references'] if q['category']=='var' and
          q['access']=='write' and q['value']==0x4071]==[(149007489,6)],'電話eventのvar4071=6 owner')
    need([(q['instruction_address'],q['value']) for q in phone['references'] if q['category']=='flag' and
          q['access']=='set']==[(149007781,4366)],'NPC非表示flag4366 owner')
    remap=raw[0x1303ca8:0x1303ca8+1488];need(identity(remap)['sha256']==sectors.TABLE_SHA,'固定remap表')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]))
    need(mapping.get(101+0x500,101+0x500)==1381,'通常101のphysical bit1381')
    pointer=struct.unpack_from('<I',raw,0xdb224)[0];need(pointer==0x083c4b28,'checksum table owner')
    sectors.layout_table(raw[pointer-0x08000000:pointer-0x08000000+56])
    return dict(map=[3,21],trainer_object=obj[0],trainer_graph=trainer,trainer_physical_mapping=[[101,1381]],
        coord_table=coords,observed_coord_index=2,phone_graph=phone,expanded_flag=dict(source_id=4366,index=2062,payload_offset=257,bit=6),
        unexecuted_rematches_accepted=False,other_coord_paths_accepted=False,hm05_compatibility_root_cause_resolved=False)


def verify(folder,development=False):
    folder=Path(folder);plan=load((ROOT/DEV/'expected.json').read_bytes());cmds=decode_plan(plan);parsed={}
    for lane,seed in (('progress',INPUT_SAVE),('continue',OUTPUT_SAVE)):
        command=(folder/lane/'commands.txt').read_bytes();stdout=(folder/lane/'stdout.txt').read_bytes()
        expected=inflate(plan[lane]['development_commands_zlib_b85'],40000) if development else cmds[lane]
        need(command==expected and not (folder/lane/'stderr.txt').read_bytes(),'実入力/stderr '+lane)
        if lane=='progress' or development:need(identity(stdout)==plan[lane]['development_stdout'],'開発stdout全byte '+lane)
        else:
            n=plan[lane]['development_prefix']['size'];need(identity(stdout[:n])==plan[lane]['development_prefix'],'開発cold原本prefix全byte保持')
        parsed[lane]=trace(stdout,command,seed);screens=parsed[lane]['screens']
        need({p.name for p in (folder/lane).glob('screen-*.ppm')}=={f"screen-{s['screen']:04d}.ppm" for s in screens},'全画面集合')
        for s in screens:screen_bytes((folder/lane/f"screen-{s['screen']:04d}.ppm").read_bytes(),s,blank_allowed=True)
        execution=load((folder/lane/'execution.json').read_bytes())
        need(execution['returncode']==0 and execution['initial_save']==seed and execution['final_save']==OUTPUT_SAVE and
             type(execution['native_processes']) is int and execution['native_processes']==1 and execution['automatic_retry'] is False,'実process会計')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT_SAVE,'process終端save全byte')
    review=plan['visual_review'];need(len(review)==38 and len({(x['lane'],x['observe']) for x in review})==38,'38目視anchor')
    for lane,ids in ANCHORS.items():need(sorted(x['observe'] for x in review if x['lane']==lane)==ids,'anchor全集合')
    for x in review:
        s=parsed[x['lane']]['screens'][x['observe']];need(s['sha256']==x['sha256'],'目視と正式pixel結合')
        screen_bytes((folder/x['lane']/f"screen-{x['observe']:04d}.ppm").read_bytes(),s)
    before=(folder/'input.srm').read_bytes();after=(folder/'story-fast.srm').read_bytes();cold=(folder/'cold.srm').read_bytes()
    need(identity(before)==INPUT_SAVE and identity(after)==OUTPUT_SAVE and after==cold,'親Save20/後継Save21全byte')
    result=semantic(parsed['progress'],parsed['continue'],development)
    need(identity((folder/'runner').read_bytes())==RUNNER,'固定runner')
    result.update(save_structure=save_structure(before,after,cold),rom_owners=owners((folder/'candidate.gba').read_bytes()),
        input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,candidate=CANDIDATE,progress_inputs=181,cold_inputs=30 if development else 33,
        progress_frames=16528,cold_frames=2338 if development else 2760,screens=60 if development else 61,
        visual_review_anchors=38,accepted_case_reruns=0,compiles=0,rom_changes=0)
    return result,shared.byte_ledger(before,after)
