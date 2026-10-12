#!/usr/bin/env python3
"""Save11からの母親による2体回復・Save12だけを受け入れる後継検証器。"""
from __future__ import annotations
from pathlib import Path
import struct
import pr16_story_save11 as prior
from pr16_story_after_home import ledger_checksum

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts/pr16_story_save12.py'
TEST = 'tests/test_pr16_story_save12.py'
DEV = 'content/modernization/pr16_story_save12_development'
CP = 'content/modernization/pr16_story_save12_checkpoint.json'
PARENT = prior.CP
CANDIDATE, RUNNER, INPUT_SAVE = prior.CANDIDATE, prior.RUNNER, prior.OUTPUT_SAVE
OUTPUT_SAVE = dict(size=131088, sha256='22072b86a414a01f35c7925492698f52e390032edd014d5243853e54e64f2a6d')
REVIEW = dict(size=13390, sha256='8c3c2700be745f4b355978c3bc45fffe4d3a815bf4a4019030c28460c80cd822')
PARTY_WALK = '545520907fd8bc911a32d54363a8de631012cf43ab6032605416957bcf11476a'
PARTY_AFTER = 'f773bc85cc09a4b6d584a18d3730d2130f6b58bdadf783a25f399d2ddee03b0c'
FLASH_AFTER = '6dc92eb655b78401c2ca11293504d706368750178fc9be2c6a23ddddf80ce02f'
LEDGER_AFTER = 'f089601d810f37bfd3a30d3bd6f71df61b64b19da845f9f750a1ff7971516d08'
FIELD, PARTY, INFO = prior.FIELD, prior.PARTY, prior.INFO
CLAIMS = dict(mother_heal_visits=1, healed_party_members=2, ordinary_saves=1,
              wild_victories=0, trainer_victories=0, losses=0, escapes=0, captures=0,
              experience_gained=0, natural_research_arrival=False,
              regional_pokedex_integration=False, full_story=False, release_ready=False)
PAIRS = [[32+i,1+i] for i in range(7)]
PARTY_CHANGES = [(41,106,108),(54,22,25),(86,16,26),(141,50,51),(152,33,35),(153,38,40),(186,4,15)]
need, identity, load = prior.need, prior.identity, prior.load
trace, commands, screen_bytes = prior.trace, prior.commands, prior.screen_bytes
sections, bag = prior.sections, prior.bag


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('status') == 'PASS_STORY_SAVE11_SCOPED' and
         parent.get('actions_completion_confirmed') is True and parent.get('run_id') == 36430188567 and
         parent.get('retained_artifact_id') == 10973111478 and parent.get('candidate') == CANDIDATE and
         parent.get('output_save') == INPUT_SAVE and type(parent.get('save_counter')) is int and
         parent['save_counter'] == 11 and parent.get('party_count') == 2 and parent.get('poke_balls') == 3 and
         parent.get('trainer_victories') == 0 and parent.get('natural_research_arrival_accepted') is False and
         parent.get('release_ready') is False, '終端確認済みSave11だけから開始')


def review(raw):
    need(type(raw) is bytes and identity(raw) == REVIEW, '57画面の直接目視原本の同定')
    value = load(raw)
    need(value['method'] == 'DIRECT_PIXEL_REVIEW_NO_OCR' and value['input_save'] == INPUT_SAVE and
         value['output_save'] == OUTPUT_SAVE and value['claims'] == CLAIMS and value['full_image_pairs'] == PAIRS,
         '母親回復/通常保存だけのscope')
    return value


def semantic(a, b, parent):
    parent_boundary(parent)
    ao, bo = a['observations'], b['observations']
    need(len(ao) == 48 and len(bo) == 9 and a['end']['inputs'] == 153 and a['end']['frames'] == 10399 and
         b['end']['inputs'] == 40 and b['end']['frames'] == 3054, '新153/cold40入力・57画面')
    for obs in (ao,bo):
        for i,o in enumerate(obs):
            need(type(o) is dict and all(type(o.get(k)) is int for k in
                 ('observe','frame','callback2','lock','battle_flags','battle_outcome','party_count','rp','save_counter')),
                 '整数型。boolは不可')
            need(o['observe'] == i and o['frame'] >= (obs[i-1]['frame'] if i else 0), '欠落/重複/逆行禁止')
            need(o['battle_flags'] == o['battle_outcome'] == o['rp'] == 0 and o['party_count'] == 2,
                 '歩行/回復のみ。戦闘・捕獲・研究到達の加算なし')
            need(type(o['field']) is bool and o['field'] == (o['callback2'] == FIELD and o['lock'] == 0),
                 'UI/dialogとunlocked fieldを区別')
    for key in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(ao[0][key] == parent['continued'][key], '正式Save11の開始点: '+key)
    for i,o in enumerate(ao):
        expected_map = [3,19] if i < 8 else ([3,0] if i < 14 else [4,0])
        expected_party = prior.PARTY_AFTER if i < 11 else (PARTY_WALK if i < 27 else PARTY_AFTER)
        expected_cb = PARTY if i in (15,32) else (INFO if 16 <= i <= 21 or 33 <= i <= 38 else FIELD)
        expected_lock = 0 if i <= 14 or i in (23,31,47) else 1
        need(o['map'] == expected_map and o['party_sha256'] == expected_party and
             o['callback2'] == expected_cb and o['lock'] == expected_lock,
             '歩行のなつき度→母親会話の回復→情報/保存画面を分離')
    need(all(o['save_counter'] == 11 for o in ao[:46]) and
         all(o['flash_sha256'] == prior.FLASH_AFTER for o in ao[:42]), '書込前はSave11原本')
    transient = [o['flash_sha256'] for o in ao[42:46]]
    need(len(set(transient)) == 4 and all(x not in (prior.FLASH_AFTER,FLASH_AFTER) for x in transient),
         '4つの書込途中Flashを完了としない')
    need(ao[46]['lock'] == 1 and ao[46]['field'] is False and ao[47]['field'] is True,
         '保存完了テキストとfield復帰は別境界')
    for o in ao[46:]+bo:
        need(o['save_counter'] == 12 and o['flash_sha256'] == FLASH_AFTER and o['ledger_sha256'] == LEDGER_AFTER and
             o['map'] == [4,0] and o['xy'] == [8,5] and o['live_xy'] == [15,12] and o['facing'] == 2 and
             o['party_sha256'] == PARTY_AFTER, 'Save12/coldの同一停止点')
    for i,o in enumerate(bo):
        need(o['callback2'] == (FIELD if i in (0,8) else PARTY if i == 1 else INFO) and
             o['lock'] == (0 if i in (0,8) else 1), '独立Continueの手持ち/両個体情報/field境界')
    return dict(first_save=ao[46],progress_field=ao[47],continued=bo[-1],claims=CLAIMS)


def save_structure(before, after, cold):
    """保存原本を読むだけ。一般section checksum全種の受入は主張しない。"""
    need(all(type(v) is bytes and len(v) == 131088 for v in (before,after,cold)), 'Save/RTC長さ/型')
    need(after == cold, '独立Continue後も全131088bytes保持')
    old = sections(before,0xe000,11); sections(before,0,10)
    sections(after,0xe000,11); new = sections(after,0,12)
    need(before[0xe000:0x1c000] == after[0xe000:0x1c000], '前回Save11 bank57344bytes保持')
    pa,pb = old[1]+0x38,new[1]+0x38
    x,y = before[pa:pa+600],after[pb:pb+600]
    need(struct.unpack_from('<I',before,old[1]+0x34)[0] ==
         struct.unpack_from('<I',after,new[1]+0x34)[0] == 2, '手持ち2体不変')
    need([(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u != v] == PARTY_CHANGES,
         'なつき度2bytesと回復HP/PP5bytesだけ')
    walked = bytearray(x); walked[41]=108; walked[141]=51
    need(identity(bytes(walked))['sha256'] == PARTY_WALK, '歩行だけの中間partyを独立に解決')
    need(x[200:] == y[200:] and identity(x)['sha256'] == prior.PARTY_AFTER and
         identity(y)['sha256'] == PARTY_AFTER, '未使用400bytes/両個体identity保持')
    for start,species,exp,level,moves,pps,stats in [
        (0,1,450,9,(10,39,71,0),[35,30,25,0],(26,26,16,13,18,17,14)),
        (100,1129,27,3,(64,45,0,0),[35,40,0,0],(15,15,10,6,8,6,7))]:
        mon = y[start:start+100]
        need(struct.unpack_from('<H',mon,32)[0] == species and struct.unpack_from('<I',mon,36)[0] == exp and
             mon[84] == level and struct.unpack_from('<I',mon,80)[0] == 0 and
             struct.unpack_from('<4H',mon,44) == moves and list(mon[52:56]) == pps and
             struct.unpack_from('<7H',mon,86) == stats, '両個体の種/経験値/技/満PP/全快HP/能力')
    ia,ma = bag(before,old); ib,mb = bag(after,new)
    need(ma == mb == 2776 and ia == ib and ia['balls'] == [(4,3)]+[(0,0)]*12,
         '全5bag pocket/ボール3/2776円は不変')
    la,lb = before[0x1f064:0x1f864],after[0x1f064:0x1f864]
    for raw,clock in ((la,(0,1)),(lb,(3,1))):
        need(raw[:4] == b'VGS1' and tuple(raw[0x746:0x748]) == clock and
             struct.unpack_from('<I',raw,8)[0] == ledger_checksum(raw), 'ledger時計/checksum')
    need([i for i in range(2048) if la[i] != lb[i]] == [8,9,10,11,0x746], '他ledger owner/RP保持')
    return dict(save_counters=[11,12,12],previous_save_bank_preserved_bytes=57344,
                party_changed_bytes=[dict(offset=i,before=u,after=v) for i,u,v in PARTY_CHANGES],
                walking_friendship_changed_offsets=[41,141],healing_changed_offsets=[54,86,152,153,186],
                unused_party_bytes_preserved=400,party_count_before=2,party_count_after=2,
                poke_balls_before=3,poke_balls_after=3,money_before=ma,money_after=mb,
                experience_before=[450,27],experience_after=[450,27],experience_gained=0,
                all_five_bag_pockets_unchanged=True,all_save_rtc_preserved_after_continue=True)


def saved_bytes(before, after, cold):
    value = save_structure(before,after,cold)
    need(identity(before) == INPUT_SAVE and identity(after) == OUTPUT_SAVE, '固定前後Saveの全byte')
    return value


def verify(raw, cold_raw, command, cold_command, parent, review_raw, where, cold_where):
    expected = review(review_raw)
    a,b = trace(raw,command,INPUT_SAVE),trace(cold_raw,cold_command,OUTPUT_SAVE)
    result = semantic(a,b,parent)
    need(a['end'] == expected['progress_end'] and b['end'] == expected['continue_end'], '目視原本の終端')
    for folder,parsed,key in ((where,a,'anchors'),(cold_where,b,'cold_anchors')):
        need(isinstance(folder,Path) and folder.is_dir(), '57画面原本が必要')
        need({p.name for p in folder.glob('screen-*.ppm')} ==
             {f'screen-{s["screen"]:04d}.ppm' for s in parsed['screens']}, '画面集合の過不足')
        need(len(expected[key]) == len(parsed['screens']), '全画面の直接目視anchor')
        for s,item in zip(parsed['screens'],expected[key]):
            screen_bytes((folder/f'screen-{s["screen"]:04d}.ppm').read_bytes(),s)
            need(all(s[k] == item[k] for k in ('screen','frame','sha256')), '直接目視の番号/frame/byte同定')
    for x,y in PAIRS:
        need((where/f'screen-{x:04d}.ppm').read_bytes() == (cold_where/f'screen-{y:04d}.ppm').read_bytes(),
             '7組の全画面一致・手持ち/両個体情報/能力/技')
    for name,value in (('progress.stdout.txt',raw),('continue.stdout.txt',cold_raw),
                       ('commands.txt',command),('continue-commands.txt',cold_command)):
        need(identity(value) == expected['files'][name], '開発原本との全byte一致: '+name)
    result.update(candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,ordinary_saves=1,
                  new_native_processes=2,screen_count=57,full_image_comparisons=7,mother_heal_visits=1,
                  healed_party_members=2,captures=0,poke_balls=3,trainer_victories=0,wild_victories=0,
                  losses=0,escapes=0,experience=[450,27],experience_gained=0,level=[9,3],hp=[[26,26],[15,15]],
                  moves_pp=[[35,30,25],[35,40]],party_count=2,money=2776,save_counter=12,
                  native_guarded_host_writes=0,fixture_calls=0,manual_save_keys_only=True,
                  save_complete_text_observed=True,progress_final_unlocked_field=True,
                  cold_final_unlocked_field=True,natural_research_arrival_accepted=False,
                  regional_pokedex_integration_accepted=False,full_story_accepted=False,release_ready=False,
                  active_baseline_changed=False,accepted_case_reruns=0)
    return result
