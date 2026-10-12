#!/usr/bin/env python3
"""Save16→3戦→アヤメ回復Save17の読取専用oracle。旧受入は実行しない。"""
from __future__ import annotations
import json
from pathlib import Path
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
import pr16_story_after_maori as source
import pr16_story_fast_maori as shared
from pr16_story_after_home import commands, screen_bytes
need, identity = source.need, source.identity
TASK = 'USER-20260929-STORY-AFTER-MAORI'
DEV = 'content/modernization/pr16_story_after_maori_development'
CP = 'content/modernization/pr16_story_after_maori_checkpoint.json'
GUIDE = 'docs/PR16_STORY_AFTER_MAORI_JA.md'
OUTPUT_SAVE = dict(size=131088, sha256='6bd7a37962e31b3c3c553a882903c766b7146f016cdf00a62036273789ab6f2a')
PARTY = '4f9c2815292dc1b6a3d0cfded64f6fa6857a2169ca6db1e67b544f575cf25df8'
FLASH = 'a2857823f81bcc73d8b532a0229bc445db52625835dcc26a71d30bab9ed96b14'
FIELD, BATTLE, PARTY_UI = 134569589, 134285761, 135394217
EPISODES = [(14, 35, 39, 13), (47, 59, 61, 12), (69, 80, 82, 12)]
CHANGES = [(41, 0, 1), (52, 6, 10), (58, 0, 2), (141, 36, 37),
           (158, 0, 1), (160, 0, 1), (241, 100, 101), (341, 50, 51)]


def semantic(a, b):
    obs, cold = a['observations'], b['observations']
    need(len(obs) == 116 and len(cold) == 3, 'all 119 observations')
    for parsed, count, frames in ((a, 317, 28007), (b, 22, 1746)):
        e = parsed['end']
        need(e['inputs'] == count and e['frames'] == frames and e['host_write_barriers'] == 7 and
             e['warnings_errors'] == e['guarded_host_writes'] == e['fixture_calls'] == 0 and
             e['natural_research_arrival_accepted'] is False, 'native accounting and host barriers')
    for index, o in enumerate(obs + cold):
        need(all(type(o[k]) is int for k in ('observe', 'frame', 'callback2', 'lock', 'battle_flags',
             'battle_outcome', 'party_count', 'save_counter', 'rp', 'facing')), 'integers, never bool')
        need(o['party_count'] == 4 and o['rp'] == 0 and type(o['field']) is bool, 'four support slots, RP0')
    route = []
    for o in obs:
        if not route or route[-1] != o['map']:
            route.append(o['map'])
    need(route == [[3,19], [3,20], [3,11], [3,20], [3,1], [5,4]], 'ordinary map connection and gate route')
    starts = [i for i, o in enumerate(obs) if o['callback2'] == BATTLE and
              (i == 0 or obs[i-1]['callback2'] != BATTLE)]
    need(starts == [14, 47, 69], 'three episodes, not fainting or retained field outcomes')
    for start, outcome, end, flags in EPISODES:
        need(obs[start-1]['callback2'] == FIELD and obs[start-1]['lock'] == 1, 'native trainer approach')
        for i in range(start, end):
            o = obs[i]
            need((o['callback2'], o['lock'], o['battle_flags'], o['battle_outcome']) ==
                 (BATTLE, 1, flags, 0 if i < outcome else 1), 'battle start/outcome/locked tail')
        need((obs[end]['callback2'], obs[end]['lock'], obs[end]['battle_flags'], obs[end]['battle_outcome']) ==
             (FIELD, 0, flags, 1), 'victory requires unlocked field return')
    need([o['save_counter'] for o in obs] == [16] * 114 + [17] * 2, 'writing is not completed Save17')
    need(obs[0]['xy'] == [53,10] and obs[0]['facing'] == 2 and obs[0]['lock'] == 0 and
         obs[0]['callback2'] == FIELD and obs[0]['battle_flags'] == obs[0]['battle_outcome'] == 0,
         'exact accepted Save16 start, not old inputs')
    need(obs[113]['lock'] == 1 and obs[113]['flash_sha256'] not in (obs[0]['flash_sha256'], FLASH),
         'retain partial flash write, not a success anchor')
    for o in obs[114:] + cold:
        need(o['map'] == [5,4] and o['xy'] == [7,4] and o['live_xy'] == [14,11] and o['facing'] == 2 and
             o['save_counter'] == 17 and o['party_sha256'] == PARTY and o['flash_sha256'] == FLASH and
             o['ledger_sha256'] == obs[-1]['ledger_sha256'], 'complete persistence at Ayame Pokemon Center')
    need(all(o['callback2'] == FIELD and o['lock'] == 0 for o in obs[114:]), 'completed save in field')
    for i, o in enumerate(cold):
        need(o['battle_flags'] == o['battle_outcome'] == 0 and
             (o['callback2'], o['lock']) == ((PARTY_UI, 1) if i == 1 else (FIELD, 0)),
             'independent Continue, real party UI, then field; no rematch')
    return dict(trainer_victories=3, double_battles=1, wild_victories=0, captures=0, escapes=0,
        losses=0, ordinary_heals=1, ordinary_saves=1, save_counter=17, party_count=4, rp=0,
        route=route, episodes=[dict(start=x, outcome=y, unlocked_field=z, flags=f) for x,y,z,f in EPISODES],
        friendly_fire_preserved=True, save_success_text_frame_captured=False,
        natural_growth_accepted=False, natural_difficulty_accepted=False, evolution_accepted=False,
        natural_research_arrival_accepted=False, full_story_accepted=False, release_ready=False)


def save_structure(before, after, cold):
    need(all(type(v) is bytes and len(v) == 131088 for v in (before, after, cold)), 'Save/RTC bytes')
    need(after == cold, 'all 131088 bytes after independent Continue')
    old = shared.sections(before, 0, 16)
    shared.sections(before, 0xe000, 15)
    shared.sections(after, 0, 16)
    new = shared.sections(after, 0xe000, 17)
    need(before[:0xe000] == after[:0xe000], 'previous 57344-byte Save16 bank retained')
    x = before[old[1]+56:old[1]+656]
    y = after[new[1]+56:new[1]+656]
    changes = [(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u != v]
    need(changes == CHANGES and identity(y)['sha256'] == PARTY, 'exact eight party bytes: friendship/PP/native EVs')
    need(struct.unpack_from('<I', before, old[1]+52)[0] == struct.unpack_from('<I', after, new[1]+52)[0] == 4,
         'unchanged four slots')
    for i, (species, exp, hp) in enumerate(((150,1250000,354), (850,1250000,294),
                                          (151,1059860,342), (690,1000000,300))):
        mon = y[i*100:(i+1)*100]
        need(struct.unpack_from('<H', mon,32)[0] == species and struct.unpack_from('<I',mon,36)[0] == exp and
             mon[84] == 100 and struct.unpack_from('<I',mon,80)[0] == 0 and
             struct.unpack_from('<HH',mon,86) == (hp,hp), 'Lv100 support identity/EXP and full native recovery')
    need(x[400:] == y[400:], 'unused party bytes')
    items_a, money_a = shared.bag(before, old)
    items_b, money_b = shared.bag(after, new)
    need(items_a == items_b and (money_a,money_b) == (2936,3372), 'five pockets; prizes168+108+160')
    for sid in range(5,14):
        need(before[old[sid]:old[sid]+0xff4] == after[new[sid]:new[sid]+0xff4], 'PC section unchanged')
    need(before[old[0]+0x1b] == after[new[0]+0x1b] == 0, 'National Dex remains locked')
    flag_delta = []
    for i in range(0xa0):
        u,v = before[old[2]+i], after[new[2]+i]
        need(u & ~v == 0, 'no cleared story flag in inspected range')
        flag_delta.extend(i*8+j for j in range(8) if (u ^ v) & (1 << j))
    need(flag_delta == [175,190,702,913], 'three rooted trainer flags plus distinct non-trainer delta913')
    return dict(party_changed_bytes=[dict(offset=i,before=u,after=v) for i,u,v in changes],
        previous_bank_preserved_bytes=57344, pc_sections_preserved=list(range(5,14)),
        unused_party_bytes_preserved=200, all_five_bag_pockets_unchanged=True,
        money_before=money_a, money_after=money_b, prize_money=436, rooted_trainer_flags=[175,190,702],
        additional_flag_delta_not_counted_as_trainer=913, national_dex_magic=0,
        all_save_rtc_preserved_after_continue=True, general_sector_checksum_acceptance_claimed=False)


def owners(raw):
    from tools.t02.rom_inventory import RomImage, ScriptWalker, ScriptRoot, MAP_GROUPS_POINTER_SITE
    need(identity(raw) == source.CANDIDATE, 'unchanged exact ROM')
    r = RomImage('story-after-maori', raw)
    view = source.map_view(raw, r.u32(MAP_GROUPS_POINTER_SITE), 3, 20)
    specs = [(1,[34,17],154623651,[(702,7),(1342,4)]), (2,[33,17],154623651,[(702,7),(1342,4)]),
             (10,[43,11],154589367,[(190,0),(1107,5)]), (3,[65,10],154588091,[(175,0),(1095,5)])]
    result = []
    for local, xy, script, wanted in specs:
        rows = [o for o in view['objects'] if o['local_id'] == local]
        need(len(rows) == 1 and rows[0]['xy'] == xy and rows[0]['script'] == script, 'rooted trainer object')
        walker = ScriptWalker(r)
        walker.add_root(ScriptRoot(script, 'new-route-trainer-'+str(local), 'object'))
        graph = walker.walk()
        refs = sorted((x['value'],x['battle_type']) for x in graph['references'] if x.get('category') == 'trainer')
        need(refs == wanted and not graph['diagnostics'], 'story/rematch owners, no decode errors')
        result.append(dict(local_id=local, xy=xy, script=script, trainer_references=refs))
    return result


def verify(folder):
    folder = Path(folder)
    expected = json.loads((ROOT / DEV / 'expected.json').read_text())
    parsed = []
    for lane, seed in (('progress',source.INPUT_SAVE), ('continue',OUTPUT_SAVE)):
        cmd = (folder/lane/'commands.txt').read_bytes()
        stdout = (folder/lane/'stdout.txt').read_bytes()
        need(identity(cmd) == expected[lane]['commands'] and identity(stdout) == expected[lane]['stdout'],
             'whole developed command/trace bytes: '+lane)
        need(not (folder/lane/'stderr.txt').read_bytes(), 'native stderr empty')
        value = shared.trace(stdout,cmd,seed)
        for screen in value['screens']:
            screen_bytes((folder/lane/f"screen-{screen['screen']:04d}.ppm").read_bytes(),screen)
        parsed.append(value)
    result = semantic(*parsed)
    before = (folder/'input.srm').read_bytes()
    after = (folder/'story-fast.srm').read_bytes()
    cold = (folder/'cold.srm').read_bytes()
    need(identity(before) == source.INPUT_SAVE and identity(after) == OUTPUT_SAVE, 'fixed input/output bytes')
    result['save_structure'] = save_structure(before,after,cold)
    result['rom_owners'] = owners((folder/'candidate.gba').read_bytes())
    result.update(input_save=source.INPUT_SAVE, output_save=OUTPUT_SAVE, candidate=source.CANDIDATE,
                  progress_inputs=317, cold_inputs=22, progress_frames=28007, cold_frames=1746, screens=119)
    return result, shared.byte_ledger(before,after)
