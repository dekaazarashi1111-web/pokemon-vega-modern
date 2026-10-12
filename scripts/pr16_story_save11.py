#!/usr/bin/env python3
"""Save10からの最初の自然捕獲・Save11だけを受け入れる後継検証器。"""
from __future__ import annotations
from pathlib import Path
import struct
import pr16_story_save10 as prior

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts/pr16_story_save11.py'
TEST = 'tests/test_pr16_story_save11.py'
DEV = 'content/modernization/pr16_story_save11_development'
CP = 'content/modernization/pr16_story_save11_checkpoint.json'
PARENT = prior.CP
CANDIDATE, RUNNER, INPUT_SAVE = prior.CANDIDATE, prior.RUNNER, prior.OUTPUT_SAVE
OUTPUT_SAVE = dict(size=131088, sha256='dfe8188b695323c61fa79172df41a5b3c7eb8b6c56d54df2cf1bc67cac424eef')
REVIEW = dict(size=12121, sha256='683b0332ca3afa6b3c27f8fa4de0596d58ff321290a394aca0ba1c681658301a')
PARTY_AFTER = 'bad45c50b25eecf451c9bb6a4324b937b33bc6f2f3c5d9aa750e08c341b4ca99'
FLASH_AFTER = 'd9569eb7010b8ac256997c9f2cff56e818889ad6d00ba5ab0e916d2de4c42e5b'
LEDGER_AFTER = 'c6d0f39e9af97cee9cac4c999fdf2b17b5e84bc2055b54d8ba359b55c78e25f8'
FIELD, BATTLE, BAG, NAME = 134569589, 134285761, 135301605, 134871633
PARTY, INFO = 135394217, 135497357
CLAIMS = dict(captures=1, capture_attempts=2, failed_capture_attempts=1, poke_balls_before=5,
              poke_balls_after=3, wild_victories=0, trainer_victories=0, losses=0, escapes=0,
              experience_gained=0, ordinary_saves=1, natural_research_arrival=False,
              regional_pokedex_integration=False, full_story=False, release_ready=False)
PAIRS = [[49,1],[50,2],[51,3],[52,4],[53,5],[54,6],[55,7]]
need, identity, load = prior.need, prior.identity, prior.load
trace, commands, screen_bytes = prior.trace, prior.commands, prior.screen_bytes


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('status') == 'PASS_STORY_SAVE10_SCOPED' and
         parent.get('actions_completion_confirmed') is True and parent.get('run_id') == 36423498952 and
         parent.get('retained_artifact_id') == 10970079659 and parent.get('candidate') == CANDIDATE and
         parent.get('output_save') == INPUT_SAVE and type(parent.get('save_counter')) is int and
         parent['save_counter'] == 10 and parent.get('captures') == 0 and parent.get('poke_balls') == 5 and
         parent.get('trainer_victories') == 0 and parent.get('natural_research_arrival_accepted') is False and
         parent.get('release_ready') is False, '終端確認済みSave10だけから開始')


def review(raw):
    need(type(raw) is bytes and identity(raw) == REVIEW, '直接目視原本の同定')
    value = load(raw)
    need(value['method'] == 'DIRECT_PIXEL_REVIEW_NO_OCR' and value['input_save'] == INPUT_SAVE and
         value['output_save'] == OUTPUT_SAVE and value['claims'] == CLAIMS and value['full_image_pairs'] == PAIRS,
         '捕獲/失敗投球/保存のscope')
    return value


def capture_boundary(rows):
    """この1戦の開始・名前UI・field終端を結合。旧28境界試験は変更しない。"""
    need(type(rows) is list and len(rows) == 70, 'Save11の全70観測')
    for i, o in enumerate(rows):
        need(type(o) is dict and all(type(o.get(k)) is int for k in
             ('observe','frame','callback2','lock','battle_flags','battle_outcome','party_count')),
             '境界値の整数型。boolは不可')
        need(o['observe'] == i and o['frame'] >= (rows[i-1]['frame'] if i else 0), '欠落/重複/逆行禁止')
        expected = (0,0,1) if i < 10 else ((4,0,1) if i < 47 else (4,7,2))
        need((o['battle_flags'],o['battle_outcome'],o['party_count']) == expected,
             '初投失敗/名前確認/捕獲後残留を勝利や追加捕獲にしない')
        if i < 10 or i == 47:
            need(o['callback2'] == FIELD and o['lock'] == 0, '前後のfield境界')
        elif i < 47:
            need(o['callback2'] in (BATTLE,BAG,NAME) and o['lock'] == 1, '1つの野生戦闘だけ')
        else:
            need(o['callback2'] in (FIELD,PARTY,INFO,BAG) and o['lock'] == 1, '捕獲後はUI/保存だけ')
    need(rows[10]['callback2'] == BATTLE and all(rows[i]['callback2'] == NAME for i in (44,45,46)),
         '戦闘開始とニックネーム途中を終端扱いしない')
    return dict(start=10,end=47,kind='wild',outcome=7,captures=1,wild_victories=0,trainer_victories=0,
                losses=0,escapes=0,failed_capture_attempts=1)


def semantic(a, b, parent):
    parent_boundary(parent)
    ao, bo = a['observations'], b['observations']
    episode = capture_boundary(ao)
    need(len(bo) == 13 and a['end']['inputs'] == 176 and a['end']['frames'] == 12231 and
         b['end']['inputs'] == 50 and b['end']['frames'] == 3560, '新176/cold50入力・83画面')
    for key in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(ao[0][key] == parent['continued'][key], '正式Save10の開始点: '+key)
    need(all(o['map'] == ([32,2] if i < 4 else [3,19]) and o['rp'] == 0 for i,o in enumerate(ao)),
         '民家から501番道路だけ。研究施設到達はない')
    need(all(o['party_sha256'] == prior.PARTY_AFTER for o in ao[:24]) and
         all(o['party_sha256'] == PARTY_AFTER for o in ao[47:]+bo), '戦闘前と捕獲後のparty')
    need(all(o['save_counter'] == 10 for o in ao[:69]) and
         all(o['flash_sha256'] == prior.FLASH_AFTER for o in ao[:62]), '書込前はSave10原本')
    transient = [o['flash_sha256'] for o in ao[62:69]]
    need(len(set(transient)) == 7 and all(x not in (prior.FLASH_AFTER,FLASH_AFTER) for x in transient),
         '7つの書込途中FlashをSave11完了としない')
    need(all(o['callback2'] == FIELD and o['lock'] == 1 for o in ao[59:]), '通常レポートの境界')
    need(ao[-1]['field'] is False and ao[-1]['ledger_sha256'] == LEDGER_AFTER and
         bo[0]['ledger_sha256'] == LEDGER_AFTER, '保存完了メッセージとcold初期ledger')
    for o in [ao[-1]]+bo:
        need(o['save_counter'] == 11 and o['flash_sha256'] == FLASH_AFTER and o['map'] == [3,19] and
             o['xy'] == [15,10] and o['live_xy'] == [22,17] and o['facing'] == 3 and o['rp'] == 0,
             'Save11/coldの同じ停止点')
    need(all(o['battle_flags'] == o['battle_outcome'] == 0 and o['party_count'] == 2 for o in bo),
         'coldに戦闘残留/新捕獲/RPを作らない')
    for o in (bo[0],bo[-1]):
        need(o['field'] is True and o['callback2'] == FIELD and o['lock'] == 0, '独立Continueのfield復帰')
    need(all(ao[i]['callback2'] == BAG for i in (15,20,37,58)) and bo[11]['callback2'] == BAG,
         '投球前/失敗後/捕獲後/coldのバッグ')
    return dict(first_save=ao[-1],continued=bo[-1],claims=CLAIMS,capture_episode=episode)


def sections(raw, bank, counter):
    result = {}
    for off in range(bank,bank+0xe000,0x1000):
        sid,checksum,signature,count = struct.unpack_from('<HHII',raw,off+0xff4)
        need(sid not in result and 0 <= sid < 14 and signature == 0x08012025 and count == counter,
             '全14sectionの一意ID/署名/counter')
        result[sid] = off
    need(set(result) == set(range(14)), 'section欠落')
    return result


def bag(raw, table):
    key = struct.unpack_from('<I',raw,table[0]+0xf20)[0]
    pockets = {}
    for name,off,n in [('items',0x310,42),('key_items',0x3b8,30),('balls',0x430,13),
                       ('machines',0x464,58),('berries',0x54c,43)]:
        values = [struct.unpack_from('<HH',raw,table[1]+off+4*i) for i in range(n)]
        pockets[name] = [(item,count^(key&0xffff)) for item,count in values]
    return pockets,struct.unpack_from('<I',raw,table[1]+0x290)[0]^key


def save_structure(before, after, cold):
    """保存原本を読むだけ。セクタchecksum全種の一般検査は主張しない。"""
    need(all(type(v) is bytes and len(v) == 131088 for v in (before,after,cold)), 'Save/RTC長さ/型')
    need(after == cold, '独立Continue後も全131088bytes保持')
    old = sections(before,0,10); sections(before,0xe000,9)
    sections(after,0,10); new = sections(after,0xe000,11)
    need(before[:0xe000] == after[:0xe000], '前回Save10 bank57344bytesを保持')
    pa,pb = old[1]+0x38,new[1]+0x38
    x,y = before[pa:pa+600],after[pb:pb+600]
    need(struct.unpack_from('<I',before,old[1]+0x34)[0] == 1 and
         struct.unpack_from('<I',after,new[1]+0x34)[0] == 2, '手持ち1→2')
    need([(i,u,v) for i,(u,v) in enumerate(zip(x[:100],y[:100])) if u != v] == [(54,25,22),(86,26,16)],
         '先頭個体はHP/PPの2bytesだけ変更')
    need(all(struct.unpack_from('<H',x,100*i+32)[0] == 0 for i in range(1,6)) and
         x[200:] == y[200:], '未使用slotへの追加だけ。未使用slotの既存bytesをゼロへ改作しない')
    need(identity(x)['sha256'] == prior.PARTY_AFTER and identity(y)['sha256'] == PARTY_AFTER, '全600partybytes')
    for start,species,exp,level,moves,pps,stats in [
        (0,1,450,9,(10,39,71,0),[35,30,22,0],(16,26,16,13,18,17,14)),
        (100,1129,27,3,(64,45,0,0),[33,38,0,0],(4,15,10,6,8,6,7))]:
        mon = y[start:start+100]
        need(struct.unpack_from('<H',mon,32)[0] == species and struct.unpack_from('<I',mon,36)[0] == exp and
             mon[84] == level and struct.unpack_from('<I',mon,80)[0] == 0 and
             struct.unpack_from('<4H',mon,44) == moves and list(mon[52:56]) == pps and
             struct.unpack_from('<7H',mon,86) == stats, '両個体の種/経験値/技/PP/HP/全能力')
    ia,ma = bag(before,old); ib,mb = bag(after,new)
    need(ma == mb == 2776, '購入/敗北による所持金変化なし')
    need(ia['balls'] == [(4,5)]+[(0,0)]*12 and ib['balls'] == [(4,3)]+[(0,0)]*12,
         '二投分だけ消費5→3・他12slot不変')
    need(all(ia[k] == ib[k] for k in ia if k != 'balls'), '他4pocket不変')
    la,lb = before[0x1f064:0x1f864],after[0x1f064:0x1f864]
    for raw,clock in ((la,(58,0)),(lb,(0,1))):
        need(raw[:4] == b'VGS1' and tuple(raw[0x746:0x748]) == clock and
             struct.unpack_from('<I',raw,8)[0] == prior.prior.prior.prior.ledger_checksum(raw), 'ledger時計/checksum')
    need([i for i in range(2048) if la[i] != lb[i]] == [8,9,10,11,0x746,0x747], '他ledger owner/RP保持')
    return dict(save_counters=[10,11,11],previous_save_bank_preserved_bytes=57344,
                first_mon_changed_bytes=[dict(offset=54,before=25,after=22),dict(offset=86,before=26,after=16)],
                unused_party_bytes_preserved=400,party_count_before=1,party_count_after=2,
                poke_ball_item_id=4,poke_balls_before=5,poke_balls_after=3,money_before=ma,money_after=mb,
                experience_before=450,experience_after=450,experience_gained=0,captured_species_id=1129,
                captured_experience=27,captured_level=3,other_four_bag_pockets_unchanged=True,
                other_ball_slots_unchanged=True,all_save_rtc_preserved_after_continue=True)


def saved_bytes(before, after, cold):
    value = save_structure(before,after,cold)
    need(identity(before) == INPUT_SAVE and identity(after) == OUTPUT_SAVE, '固定前後Saveの全byte')
    return value


def verify(raw, cold_raw, command, cold_command, parent, review_raw, where, cold_where):
    expected = review(review_raw)
    a,b = trace(raw,command,INPUT_SAVE),trace(cold_raw,cold_command,OUTPUT_SAVE)
    result = semantic(a,b,parent)
    need(a['end'] == expected['progress_end'] and b['end'] == expected['continue_end'], '目視原本の終端')
    for folder,parsed in ((where,a),(cold_where,b)):
        need(isinstance(folder,Path) and folder.is_dir(), '83画面原本が必要')
        need({p.name for p in folder.glob('screen-*.ppm')} ==
             {f'screen-{s["screen"]:04d}.ppm' for s in parsed['screens']}, '画面集合の過不足')
        for s in parsed['screens']:
            screen_bytes((folder/f'screen-{s["screen"]:04d}.ppm').read_bytes(),s)
    for x,y in PAIRS:
        need((where/f'screen-{x:04d}.ppm').read_bytes() == (cold_where/f'screen-{y:04d}.ppm').read_bytes(),
             '7組の全画面一致・手持ち/両個体情報/能力/技')
    p=(where/'screen-0058.ppm').read_bytes()[15:]; q=(cold_where/'screen-0011.ppm').read_bytes()[15:]
    changes=[i//3 for i in range(0,len(p),3) if p[i:i+3] != q[i:i+3]]
    need(len(changes) == 80 and all(1 <= i%240 <= 11 and 65 <= i//240 <= 78 for i in changes),
         'バッグ左端80pixel差を全画面一致にしない')
    for parsed,key in ((a,'anchors'),(b,'cold_anchors')):
        for item in expected[key]:
            need(parsed['screens'][item['screen']]['sha256'] == item['sha256'], '直接目視anchor')
    for name,value in (('progress.stdout.txt',raw),('continue.stdout.txt',cold_raw),
                       ('commands.txt',command),('continue-commands.txt',cold_command)):
        need(identity(value) == expected['files'][name], '開発原本との全byte一致: '+name)
    result.update(candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,ordinary_saves=1,
                  new_native_processes=2,screen_count=83,full_image_comparisons=7,capture_attempts=2,
                  failed_capture_attempts=1,captures=1,poke_balls=3,trainer_victories=0,wild_victories=0,
                  losses=0,escapes=0,experience=450,experience_gained=0,level=9,hp=[16,26],
                  moves_pp=[35,30,22],captured_species_id=1129,captured_level=3,captured_experience=27,
                  captured_hp=[4,15],captured_moves_pp=[33,38],party_count=2,money=2776,save_counter=11,
                  native_guarded_host_writes=0,fixture_calls=0,manual_save_keys_only=True,
                  save_complete_text_observed=True,progress_final_unlocked_field=False,
                  cold_final_unlocked_field=True,natural_research_arrival_accepted=False,
                  regional_pokedex_integration_accepted=False,full_story_accepted=False,release_ready=False,
                  active_baseline_changed=False,accepted_case_reruns=0)
    return result
