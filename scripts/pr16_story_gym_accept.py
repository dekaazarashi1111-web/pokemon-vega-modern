#!/usr/bin/env python3
"""Save18→アヤメジム→Save19の新区間専用・読取専用受入判定。"""
from __future__ import annotations
import base64
import json
from pathlib import Path
import struct
import sys
import zlib
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_story_after_maori as source
import pr16_story_fast_maori as shared
import pr16_story_ayame_persistence_audit as sectors
from pr16_story_ayame_accept import s61e_record
from pr16_story_after_home import commands, screen_bytes
need, identity = source.need, source.identity
TASK = 'USER-20260929-STORY-GYM'
DEV = 'content/modernization/pr16_story_gym_development'
CP = 'content/modernization/pr16_story_gym_checkpoint.json'
GUIDE = 'docs/PR16_STORY_GYM_JA.md'
FIELD, BATTLE, PARTY_UI, CARD_UI = 134569589, 134285761, 135394217, 134777933
INPUT_SAVE = dict(size=131088,sha256='dc1f690f0616affc61b6d45632924e4c81995c91c7c1939994f37bbe8527432d')
OUTPUT_SAVE = dict(size=131088,sha256='dd7adddc09555c2232299075bba657e9e7261ad3b868d9cabb5f0edccc8ed06d')
PARTY = '97526a22c416b307b0cc2dadd43a6eaa4651b81e3dc9c39aba6b669db7903a88'
FLASH = 'e1cccf4b1786e7d1990f26182b54328476065e0072255dcc813e006cbc23e15a'
LEDGER = '7bf08f5a0b53094c03f93682c08d6292b609bf7b7f485e2bb4c6763b0b5e2522'
FLAG_DELTA = [(46,0,1),(146,1,0),(596,0,1),(1200,0,1),(1422,0,1),(1694,0,1),(2080,0,1)]
VAR_DELTA = [(0x4021,5,46),(0x4022,2,3),(0x406c,0,1),(0x4071,3,5),(0x4072,0,1)]
ANCHORS = dict(progress=[0,9,16,29,34,49,51,52,72,73,75,81,92,99,141,146,151,152,154,160,162,170,203,215,217,219,225,227,228,229,230],
               **{'continue':[0,3,9,11]})


def decode_plan(plan):
    need(type(plan) is dict and plan.get('task') == TASK and plan.get('input_save') == INPUT_SAVE and
         plan.get('output_save') == OUTPUT_SAVE and plan.get('candidate') == source.CANDIDATE,
         '今回の正式親Save18と開発Save19だけ')
    encoded = plan['progress']['commands_zlib_b85']
    need(type(encoded) is str and 0 < len(encoded) < 40000, '圧縮入力の上限')
    decoder = zlib.decompressobj()
    raw = decoder.decompress(base64.b85decode(encoded),40001)
    need(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail, '一意の完全圧縮入力')
    result = {'progress':raw,'continue':plan['continue']['commands_text'].encode('ascii')}
    for lane, data in result.items():
        commands(data)
        need(identity(data) == plan[lane]['commands'], '入力本文全byte照合: '+lane)
    return result


def episodes(obs):
    """KO/交代UI/残留outcomeと、2回の独立したtrainer勝利を区別する。"""
    need(type(obs) is list and len(obs) > 2, '全観測列')
    found, active = [], None
    fields = ('observe','frame','callback2','lock','battle_flags','battle_outcome','party_count','save_counter','rp')
    for i,o in enumerate(obs):
        need(type(o) is dict and all(type(o.get(k)) is int for k in fields), '整数観測fields')
        need(o['observe'] == i and o['frame'] >= 0 and (i == 0 or obs[i-1]['frame'] < o['frame']), '観測順序')
        cb, outcome = o['callback2'], o['battle_outcome']
        need(cb in (FIELD,BATTLE,PARTY_UI) and o['lock'] in (0,1), '既知callback/lock')
        if cb == BATTLE:
            need(o['map'] == [6,2] and o['save_counter'] == 18 and o['party_count'] == 4 and
                 o['rp'] == 0 and o['battle_flags'] == 12 and o['lock'] == 1 and outcome in (0,1), '通常ジムtrainer戦')
            if active is None:
                need(len(found) < 2 and outcome == 0 and i > 0 and obs[i-1]['callback2'] == FIELD and
                     obs[i-1]['lock'] == 1 and (not found or found[-1]['unlocked'] is not None), '新戦闘のapproach/reset')
                active = dict(start=i,victory=None,field_return=None,unlocked=None,party_ui=[])
            if outcome == 1 and active['victory'] is None: active['victory'] = i
            need(outcome == 1 or active['victory'] is None, '勝利後のoutcome再resetを拒否')
        elif cb == PARTY_UI:
            need(active is not None and active['victory'] is None and outcome == 0 and o['lock'] == 1 and
                 o['battle_flags'] == 12 and o['map'] == [6,2], '戦闘中交代UIだけ')
            active['party_ui'].append(i)
        else:
            if active is not None:
                need(active['victory'] is not None and outcome == 1, 'KOだけではfield復帰を受入しない')
                active['field_return'] = i; found.append(active); active = None
            if found and found[-1]['unlocked'] is None:
                need(outcome == 1 and o['map'] == [6,2], '勝利後の報酬会話を最後まで保持')
                if o['lock'] == 0: found[-1]['unlocked'] = i
    need(active is None and len(found) == 2 and all(e['unlocked'] is not None for e in found), '2勝・各field復帰/解錠')
    return found


def completion(last,cold):
    need(type(last) is dict and type(cold) is list and len(cold) == 12, '保存終端と独立Continue全UI')
    for o in [last]+cold:
        need(all(type(o.get(k)) is int for k in ('save_counter','callback2','lock','party_count','rp','facing','battle_flags','battle_outcome')), '終端の整数型')
        need(o['save_counter'] == 19 and o['map'] == [5,4] and o['xy'] == [7,4] and o['live_xy'] == [14,11]
             and o['facing'] == 2 and o['party_count'] == 4 and o['rp'] == 0, 'Save19/アヤメPC/4体/RP0')
        need(o['party_sha256'] == PARTY and o['flash_sha256'] == FLASH and o['ledger_sha256'] == LEDGER, '保存済みparty/Flash/ledger')
    need((last['callback2'],last['lock']) == (FIELD,0) and last.get('field') is True and
         (last['battle_flags'],last['battle_outcome']) == (12,1), '書込み完了後のfield')
    for i,o in enumerate(cold):
        cb = PARTY_UI if i == 3 else CARD_UI if i == 9 else FIELD
        lock = 0 if i in (0,5,11) else 1
        need((o['callback2'],o['lock']) == (cb,lock) and o['battle_flags'] == o['battle_outcome'] == 0,
             '独立Continueの手持ち/カードUIとfield、戦闘残留なし')


def semantic(progress,cold):
    a,b = progress['observations'],cold['observations']
    need(len(a) == 231, '開発全231観測を保持')
    for p,frames,inputs in ((progress,57403,464),(cold,2492,34)):
        e=p['end']
        need(e['frames'] == frames and e['inputs'] == inputs and e['host_write_barriers'] == 7 and
             e['warnings_errors'] == e['guarded_host_writes'] == e['fixture_calls'] == 0 and
             e['natural_research_arrival_accepted'] is False, '通常入力と禁止書込みの実行会計')
    found=episodes(a)
    need(found == [dict(start=16,victory=49,field_return=52,unlocked=52,party_ui=[29,30,31,32,33,40]),
                   dict(start=92,victory=141,field_return=152,unlocked=162,party_ui=[])], 'ハヤカ/アマナの実測境界')
    route=[]
    for o in a:
        need(o['party_count'] == 4 and o['rp'] == 0, '元の4体/RP0')
        if not route or route[-1] != o['map']:route.append(o['map'])
    need(route == [[5,4],[3,1],[6,2],[3,1],[5,4]], '正式PC→ジム→通常退出→PC')
    need(a[0]['battle_flags'] == a[0]['battle_outcome'] == 0 and a[0]['lock'] == 0 and
         a[0]['party_sha256'] == '3385eede5f229e69f3aa73f289f3af0d1827c2c1570b07ce6e6b0f0eb3234cc8', '正式Save18開始')
    need([o['save_counter'] for o in a] == [18]*229+[19]*2, '書込み中counter18をSave19にしない')
    for i in (227,228):
        need(a[i]['lock'] == 1 and a[i]['flash_sha256'] != FLASH, '途中書込み観測の保持')
    for i,xy,lock in ((72,[5,2],1),(75,[5,2],0),(81,[6,5],0),(162,[6,5],0),(203,[32,25],0),(219,[7,4],0)):
        need(a[i]['xy'] == xy and a[i]['lock'] == lock and a[i]['callback2'] == FIELD, '通常script/移動/回復anchor')
    completion(a[229],b);completion(a[230],b)
    return dict(episodes=found,route=route,trainer_victories=2,gym_leader_victory_accepted=True,badge_count=1,
        prize_money=1836,ordinary_heals=1,ordinary_saves=1,save_counter=19,
        wild_battles=0,losses=0,captures=0,escapes=0,save_success_text_frame_captured=False,
        party_ui_is_not_new_battle=True,retained_outcome_is_not_new_victory=True,
        natural_growth_accepted=False,natural_difficulty_accepted=False,evolution_accepted=False,
        national_dex_unlocked=False,natural_research_arrival_accepted=False,full_story_accepted=False,
        release_ready=False,active_baseline_changed=False)


def state_delta(old,new):
    fa,va=old;fb,vb=new
    need(type(fa) is bytes and type(fb) is bytes and len(fa) == len(fb) == 0x120 and
         len(va) == len(vb) == 256 and all(type(v) is int for v in (*va,*vb)), 'legacy全flags/vars')
    flags=[(8*i+j,(u>>j)&1,(v>>j)&1) for i,(u,v) in enumerate(zip(fa,fb)) for j in range(8) if (u^v)&(1<<j)]
    variables=[(0x4000+i,u,v) for i,(u,v) in enumerate(zip(va,vb)) if u!=v]
    need(flags == FLAG_DELTA and variables == VAR_DELTA, '実測全legacy差分。badge/trainer以外を隠さない')
    need(va[0x4e] == vb[0x4e] == 0 and not ((fa[0x840//8]|fb[0x840//8])&1), '全国図鑑owner未解禁')
    return dict(physical_flag_deltas=flags,legacy_var_deltas=variables,national_var404e=0,national_flag840=0)


def expanded_boundary(before,after):
    a,b=s61e_record(before),s61e_record(after)
    changes=[(i,u,v) for i,(u,v) in enumerate(zip(a,b)) if u!=v]
    need(changes == [(0,0,64),(257,0,1),(319,0,32)], 'S61E全payload差分3bytesだけ')
    return dict(payload_deltas=changes,crc32_and_complement_verified=True,expanded_vars_ball_coins_unchanged=True)


def bag_boundary(a,b,money_a,money_b):
    need(set(a) == set(b) == {'items','key_items','balls','machines','berries'}, '全5pocket')
    for pocket in ('items','balls','berries'):need(a[pocket] == b[pocket], '消費品/ball/berry不変')
    need(a['key_items'] == [(361,1)]+[(0,0)]*29 and
         b['key_items'] == [(361,1),(347,1),(348,1),(364,1)]+[(0,0)]*26, '大切なものの通常報酬')
    need(a['machines'] == [(0,0)]*58 and b['machines'] == [(303,1)]+[(0,0)]*57, 'TM15の通常収納')
    need(type(money_a) is int and type(money_b) is int and (money_a,money_b) == (3940,5776), '賞金336+1500円だけ')
    return dict(money_before=3940,money_after=5776,key_items_added=[347,348,364],machine_added=303,
                other_pockets_unchanged=True,hm05_acquired=False,auxiliary_item364_owner_claimed=False)


def save_structure(before,after,cold):
    need(all(type(v) is bytes and len(v) == 131088 for v in (before,after,cold)), '全Save/RTC')
    need(after == cold, 'cold後の全131088bytes不変')
    old,ra=sectors.bank(before,0,18,sectors.LAYOUT)
    new,rb=sectors.bank(after,0xe000,19,sectors.LAYOUT)
    _,rc=sectors.bank(after,0,18,sectors.LAYOUT)
    need(before[:0xe000] == after[:0xe000], '前Save18 bank全57344bytes保持')
    x=before[old[1]+56:old[1]+656];y=after[new[1]+56:new[1]+656]
    changes=[(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u!=v]
    need(changes == [(41,1,4),(141,38,42),(241,101,104),(341,53,57)] and identity(y)['sha256'] == PARTY, '歩行友情4bytesのみ')
    need(struct.unpack_from('<I',before,old[1]+52)[0] == struct.unpack_from('<I',after,new[1]+52)[0] == 4, '元の4slots')
    for i,(species,exp,hp) in enumerate(((150,1250000,354),(850,1250000,294),(151,1059860,342),(690,1000000,300))):
        mon=y[i*100:(i+1)*100]
        need(struct.unpack_from('<H',mon,32)[0] == species and struct.unpack_from('<I',mon,36)[0] == exp and
             mon[84] == 100 and struct.unpack_from('<I',mon,80)[0] == 0 and
             struct.unpack_from('<HH',mon,86) == (hp,hp), '支援個体のspecies/EXP/Lv100/通常全回復')
    a,ma=shared.bag(before,old);b,mb=shared.bag(after,new);bag=bag_boundary(a,b,ma,mb)
    need(x[400:] == y[400:], '未使用party200bytes保持')
    for sid in range(5,13):
        need(before[old[sid]:old[sid]+0xff4] == after[new[sid]:new[sid]+0xff4], 'boxed PC全section')
    a13=before[old[13]:old[13]+0xff4];b13=after[new[13]:new[13]+0xff4]
    need(a13[:0x7d0] == b13[:0x7d0] and a13[0xde6:] == b13[0xde6:], 'boxed payloadと拡張外tail保持')
    ext=expanded_boundary(a13[0x7d0:0xde6],b13[0x7d0:0xde6])
    need(before[old[0]+0x1b] == after[new[0]+0x1b] == 0, 'NationalDex magic0')
    state=state_delta(sectors.legacy_state(before,old),sectors.legacy_state(after,new))
    return dict(party_changed_bytes=changes,bag=bag,state=state,s61e=ext,sector_checksum_checks=42,
        sector_checksum_scope='今回読込Save18と後継Save19/保持Save18のROM宣言payloadのみ。S61Eは別CRC。',
        sector_reports=dict(input18=ra,output19=rb,retained18=rc),previous_bank_preserved_bytes=57344,
        pc_full_sections_preserved=list(range(5,13)),pc_chunk13_payload_preserved_bytes=2000,
        unused_party_bytes_preserved=200,national_dex_magic=0,all_save_rtc_preserved_after_continue=True)


def owners(raw):
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot,MAP_GROUPS_POINTER_SITE
    need(identity(raw) == source.CANDIDATE, '固定candidate・ROM変更なし')
    r=RomImage('gym',raw);groups=r.u32(MAP_GROUPS_POINTER_SITE)
    gym=source.map_view(raw,groups,6,2)
    roots=[o for o in gym['objects'] if o['local_id'] in (1,2)]
    need(roots == [dict(local_id=1,xy=[6,4],script=142951328,flag=0),
                   dict(local_id=2,xy=[1,6],script=154585820,flag=0)], '現候補の実ジムobjects')
    w=ScriptWalker(r)
    for o in roots:w.add_root(ScriptRoot(o['script'],'gym-object'+str(o['local_id']),'object'))
    g=w.walk();need(not g['diagnostics'], 'ジムscriptの完全decode')
    battles=sorted((q['value'],q['battle_type']) for q in g['references'] if q['category'] == 'trainer' and q['access'] == 'battle')
    need(battles == [(142,0),(414,1)], 'trainerflag操作を実戦に計上しない')
    need(any(q['category'] == 'flag' and q['value'] == 0x820 and q['access'] == 'set' for q in g['references']), '通常badge1 owner')
    rewards=sorted(q['value'] for q in g['references'] if q['category'] == 'item' and q['command'] == 'additem')
    need(rewards == [303,347,348], '現ROMのジム報酬owner')
    events=r.u32(gym['header']+4);bg=r.u32(events+16)
    window=[r.u32(bg+i*12+8) for i in range(r.u8(events+3))
            if (r.u16(bg+i*12),r.u16(bg+i*12+2)) == (5,1)]
    need(window == [0x08409eba], '実background座標5,1から窓scriptへ')
    w=ScriptWalker(r);w.add_root(ScriptRoot(window[0],'window5,1','background'));switch=w.walk()
    need(not switch['diagnostics'] and any(q['category'] == 'flag' and q['value'] == 4360 and q['access'] == 'set' for q in switch['references']), '窓5,1の通常スイッチ')
    town=source.map_view(raw,groups,3,1);p=town['scripts']
    need(p == 138453136 and r.u8(p+5) == 2, '通常町map条件event')
    table=r.u32(p+6)
    need((r.u16(table),r.u16(table+2),r.u32(table+4)) == (0x4071,4,138453924), 'ジム後モスギスevent条件')
    w=ScriptWalker(r);w.add_root(ScriptRoot(138453924,'town-4071=4','map'));dialog=w.walk()
    need(not dialog['diagnostics'] and any(q['category'] == 'var' and q['value'] == 0x4071 and q['access'] == 'write' and q['operand'] == 5 for q in dialog['references']), '通常モスギス会話完了stage5')
    remap=raw[0x1303ca8:0x1303ca8+1488]
    need(identity(remap)['sha256'] == sectors.TABLE_SHA, '現ROM trainer remap表')
    words=struct.unpack('<744H',remap);mapping=dict(zip(words[::2],words[1::2]))
    physical=[(t,mapping.get(t+0x500,t+0x500)) for t in (142,414)]
    need(physical == [(142,1422),(414,1694)], '実戦IDから保存physical bitへ結合')
    pointer=struct.unpack_from('<I',raw,0xdb224)[0]
    need(pointer == 0x083c4b28, 'ROM section table owner')
    sectors.layout_table(raw[pointer-0x08000000:pointer-0x08000000+56])
    return dict(gym_objects=roots,trainer_battles=battles,trainer_physical_mapping=physical,
        badge_flag=2080,direct_reward_item_ids=rewards,window_root=0x08409eba,window_flag=4360,
        town_event_root=138453924,town_condition=[0x4071,4],town_completion=[0x4071,5],
        auxiliary_item364_owner_claimed=False,all_unexecuted_trainerflag_branches_accepted=False)


def verify(folder):
    folder=Path(folder);plan=json.loads((ROOT/DEV/'expected.json').read_text());cmds=decode_plan(plan);parsed={}
    for lane,seed in (('progress',INPUT_SAVE),('continue',OUTPUT_SAVE)):
        cmd=(folder/lane/'commands.txt').read_bytes();stdout=(folder/lane/'stdout.txt').read_bytes()
        need(cmd == cmds[lane] and identity(stdout) == plan[lane]['stdout'], '開発入力/全stdoutの同一再現')
        need(not (folder/lane/'stderr.txt').read_bytes(), 'native stderr空')
        p=shared.trace(stdout,cmd,seed);parsed[lane]=p
        need({x.name for x in (folder/lane).glob('screen-*.ppm')} == {f"screen-{s['screen']:04d}.ppm" for s in p['screens']}, '全画面集合')
        for s in p['screens']:screen_bytes((folder/lane/f"screen-{s['screen']:04d}.ppm").read_bytes(),s)
    reviews=plan['visual_review']
    need(type(reviews) is list and len(reviews) == 35 and len({(r['lane'],r['observe']) for r in reviews}) == 35, '重複しない35画面review')
    for lane,ids in ANCHORS.items():
        need(sorted(r['observe'] for r in reviews if r['lane'] == lane) == ids, '実レビューanchor集合')
    for r in reviews:
        need(parsed[r['lane']]['screens'][r['observe']]['sha256'] == r['sha256'], '目視reviewを正式同一pixelへ結合')
    result=semantic(parsed['progress'],parsed['continue'])
    before=(folder/'input.srm').read_bytes();after=(folder/'story-fast.srm').read_bytes();cold=(folder/'cold.srm').read_bytes()
    need(identity(before) == INPUT_SAVE and identity(after) == OUTPUT_SAVE, '正式親と自然後継の全byte')
    result.update(save_structure=save_structure(before,after,cold),rom_owners=owners((folder/'candidate.gba').read_bytes()),
        input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,candidate=source.CANDIDATE,
        progress_inputs=464,cold_inputs=34,progress_frames=57403,cold_frames=2492,screens=243,
        visual_review_anchors=35,accepted_case_reruns=0,rom_changes=0,compiles=0)
    return result,shared.byte_ledger(before,after)


if __name__ == '__main__':
    need(len(sys.argv) == 2, '既存の新区間artifactフォルダを指定')
    result,_=verify(sys.argv[1]);print(json.dumps(result,ensure_ascii=False,indent=2))
