#!/usr/bin/env python3
"""Save7後継の通常育成: 新入力原本を検証し、旧受入区間は実行しない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import pr16_story_after_home as prior

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts/pr16_story_safe_training.py'
TEST = 'tests/test_pr16_story_safe_training.py'
DEV = 'content/modernization/pr16_story_safe_training_development'
CP = 'content/modernization/pr16_story_safe_training_checkpoint.json'
PARENT = 'content/modernization/pr16_story_after_home_checkpoint.json'
CANDIDATE = prior.CANDIDATE
INPUT_SAVE = prior.OUTPUT_SAVE
RUNNER = prior.RUNNER
BOOT = prior.BOOT
OBS_INTS, OBS_HASH, OBS_KEYS, END_KEYS = prior.OBS_INTS, prior.OBS_HASH, prior.OBS_KEYS, prior.END_KEYS
need, identity, load = prior.need, prior.identity, prior.load
integer, digest, commands, screen_bytes = prior.integer, prior.digest, prior.commands, prior.screen_bytes


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('actions_completion_confirmed') is True and
         parent.get('run_id') == 36370422350 and parent.get('retained_artifact_id') == 10948853813 and
         parent.get('candidate') == CANDIDATE and parent.get('output_save') == INPUT_SAVE and
         parent.get('save_counter') == 7 and parent.get('experience') == 270 and
         parent.get('trainer_victories') == 0 and parent.get('natural_research_arrival_accepted') is False and
         parent.get('release_ready') is False, '終端確認済みSave7のみ。敗北は勝利へ昇格しない')


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
        need(r['live_xy'] == [v+7 for v in r['xy']], '保存座標とlive座標')
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

OUTPUT_SAVE = dict(size=131088, sha256='f53ac305f8a02040744ffa26794451574d1c5df1b43765bf4229ba5454e034ba')
REVIEW = dict(size=6839, sha256='220a35ceab7112f00b41673bd9ea3e46a5e574ea3c9015809ec734560cffc8aa')
PARTY_BEFORE = 'e2f52f3035f57334def4f412aa8c8c757a1b63fc3e7d52bbfe2ee34f28b1eaa8'
PARTY_AFTER = '1622f3df0e0511fdf4152841b2b6f43cb8feb891bb9d5ee78c679534bff17847'
FLASH_BEFORE = '9e2d05c9b0ef1aa59b6b48401d3d25793b5e5f2aad244365a3a991fa97745fa9'
FLASH_AFTER = 'c2972bb9107df695d5442edbdb1445c1afed53e940dc442ade31af1db4fe7a7f'
CLAIMS = dict(wild_victories=3,trainer_victories=0,losses=0,captures=0,experience_gained=61,
              ordinary_saves=1,mother_heal_visits=2,research_arrival=False,full_story=False,release_ready=False)


def review(raw):
    need(type(raw) is bytes and identity(raw) == REVIEW, '固定済み直接目視原本。未確認結果を追認しない')
    r = load(raw)
    need(r['schema_version'] == 1 and r['method'] == 'DIRECT_PIXEL_REVIEW_NO_OCR' and
         r['input_save'] == INPUT_SAVE and r['output_save'] == OUTPUT_SAVE and
         r['claims'] == CLAIMS and r['ui_pairs'] == [[53,1],[54,2],[55,3],[56,4]], '目視scope/保存/UI対応')
    return r


def semantic(a, b, parent):
    """画面SHAだけに依存せず、入力由来の状態遷移と保存境界を独立照合する。"""
    parent_boundary(parent)
    ao, bo = a['observations'], b['observations']
    need(len(ao) == 64 and len(bo) == 6 and a['end']['inputs'] == 316 and a['end']['frames'] == 25208 and
         b['end']['inputs'] == 34 and b['end']['frames'] == 2808, '新区間316/cold34入力と70画面')
    for k in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(ao[0][k] == parent['continued'][k], '親Save7開始点: '+k)
    need(ao[0]['field'] is True and ao[0]['battle_flags'] == ao[0]['battle_outcome'] == 0, 'fresh開始')
    need(all(o['rp'] == 0 and o['party_count'] == 1 for o in ao+bo), 'RP/捕獲/手持ち増加なし')
    need(all(o['battle_flags'] in (0,4) and o['battle_outcome'] in (0,1) for o in ao), 'トレーナー戦/敗北なし')
    starts = []
    last = None
    for o in ao:
        active = o['lock'] == 1 and o['battle_flags'] == 4 and o['battle_outcome'] == 0
        if active and not last:
            starts.append(o['observe'])
        last = active
    need(starts == [10,20,39], '新規野生3戦の開始境界')
    for i in (19,25,48):
        o=ao[i]
        need(o['callback2'] == 134569589 and o['lock'] == 0 and o['battle_outcome'] == 1, '実戦後field復帰')
    need(all(o['map'] in ([4,0],[4,3],[3,0],[3,19]) for o in ao), '研究活動施設到達へ昇格しない')
    need(all(o['save_counter'] == 7 and o['flash_sha256'] == FLASH_BEFORE for o in ao[:62]), '保存前Flash不変')
    need(ao[62]['save_counter'] == 7 and ao[62]['flash_sha256'] not in (FLASH_BEFORE,FLASH_AFTER), '実レポート書込途中')
    need(ao[63]['save_counter'] == 8 and ao[63]['flash_sha256'] == FLASH_AFTER and ao[63]['lock'] == 0 and
         ao[63]['callback2'] == 134569589, '実レポート終了後Save8')
    for i in (52,59,60,61,62):
        need(ao[i]['lock'] == 1 and ao[i]['callback2'] == 134569589, '通常Start/レポートUI')
    need(ao[32]['party_sha256'] != ao[34]['party_sha256'] and ao[50]['party_sha256'] != ao[51]['party_sha256'], '母親回復2回')
    need(all(o['party_sha256'] == PARTY_AFTER for o in ao[51:]+bo), '回復後/Save/Continue全600partybytes')
    for o in bo:
        need(o['map'] == [4,0] and o['xy'] == [8,3] and o['save_counter'] == 8 and
             o['flash_sha256'] == FLASH_AFTER and o['battle_flags'] == o['battle_outcome'] == 0, 'cold境界不変')
    need(bo[0]['field'] is True and bo[-1]['field'] is True and bo[-1]['lock'] == 0, 'cold field再開と終了')
    for x,y in ((53,1),(54,2),(55,3),(56,4)):
        need(ao[x]['callback2'] == bo[y]['callback2'] and ao[x]['lock'] == bo[y]['lock'] == 1, '実UI callback対応')
    return dict(first_save=ao[-1],continued=bo[-1],claims=CLAIMS)


def saved_bytes(before, after, cold):
    need(all(type(v) is bytes for v in (before,after,cold)), 'immutable Save bytes')
    need(identity(before) == INPUT_SAVE and identity(after) == OUTPUT_SAVE and cold == after, 'Save/RTC全131088bytes')
    # 記録されたsection1のparty位置と全600bytesを独立して確認する。
    pa,pb=0x16038,0x9038
    x,y=before[pa:pa+600],after[pb:pb+600]
    need(identity(x)['sha256'] == PARTY_BEFORE and identity(y)['sha256'] == PARTY_AFTER, 'Save内party同定')
    delta=[dict(offset=i,before=u,after=v) for i,(u,v) in enumerate(zip(x,y)) if u != v]
    wanted=[(36,14,75),(41,86,96),(59,0,2),(84,7,8),(86,23,24),(88,23,24),
            (90,14,15),(92,11,12),(94,15,17),(96,14,16),(98,12,13)]
    need(delta == [dict(offset=i,before=u,after=v) for i,u,v in wanted], '自然成長の11bytes以外を保持')
    need(x[:36] == y[:36] and x[42:56] == y[42:56] and x[100:] == y[100:], '個体識別/技/空party保持')
    need(struct.unpack_from('<I',x,36)[0] == 270 and struct.unpack_from('<I',y,36)[0] == 331 and
         y[84] == 8 and struct.unpack_from('<I',y,80)[0] == 0 and list(y[52:56]) == [35,30,25,0] and
         struct.unpack_from('<7H',y,86) == (24,24,15,12,17,16,13), '保存Lv/EXP/状態/PP/全能力')
    need(before[0xe000:0x1c000] == after[0xe000:0x1c000], '前回Save7 bankの全57344bytes不変')
    def sections(raw, start, counter):
        rows=[struct.unpack_from('<HHII',raw,i+0xff4) for i in range(start,start+0xe000,0x1000)]
        need(sorted(r[0] for r in rows) == list(range(14)) and
             all(r[2] == 0x08012025 and r[3] == counter for r in rows), '全14sectionの署名と同一counter')
    sections(before,0xe000,7);sections(after,0,8);sections(after,0xe000,7)
    la,lb=before[0x1f064:0x1f864],after[0x1f064:0x1f864]
    for raw,minute in ((la,39),(lb,46)):
        need(raw[:4] == b'VGS1' and raw[0x746] == minute and
             struct.unpack_from('<I',raw,8)[0] == prior.ledger_checksum(raw), 'ledger時計/checksum')
    need([i for i in range(2048) if la[i] != lb[i]] == [8,9,10,11,0x746], '他ledger owner不変')
    return dict(before_party_offset=pa,after_party_offset=pb,party_changed_bytes=delta,other_party_bytes_preserved=589,
                previous_save_bank_preserved_bytes=57344,experience_before=270,experience_after=331,experience_gained=61,
                level_before=7,level_after=8,hp=[24,24],moves_pp=[35,30,25],
                saved_minutes_before=39,saved_minutes_after=46,save_counters=[7,8,8],all_save_rtc_preserved_after_continue=True)


def verify(raw, cold_raw, command, cold_command, parent, review_raw, where, cold_where):
    expected=review(review_raw)
    a,b=trace(raw,command,INPUT_SAVE),trace(cold_raw,cold_command,OUTPUT_SAVE)
    result=semantic(a,b,parent)
    need(a['end'] == expected['progress_end'] and b['end'] == expected['continue_end'], '記録された実終端')
    for folder,parsed in ((where,a),(cold_where,b)):
        need(isinstance(folder,Path) and folder.is_dir(), '全画面原本必須')
        need({p.name for p in folder.glob('screen-*.ppm')} == {f'screen-{s["screen"]:04d}.ppm' for s in parsed['screens']}, '全画面の一意集合')
        for s in parsed['screens']:
            screen_bytes((folder/f'screen-{s["screen"]:04d}.ppm').read_bytes(),s)
    for x,y in expected['ui_pairs']:
        need((where/f'screen-{x:04d}.ppm').read_bytes() == (cold_where/f'screen-{y:04d}.ppm').read_bytes(), '4UI全byte独立Continue一致')
    # SHAは目視済みの開発原本へ結ぶ最終条件。構造/遷移/画面検査の代用ではない。
    for name,value in (('progress.stdout.txt',raw),('continue.stdout.txt',cold_raw),('commands.txt',command),('continue-commands.txt',cold_command)):
        need(identity(value) == expected['files'][name], '目視済み新区間原本: '+name)
    result.update(candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,new_native_processes=2,
                  ordinary_saves=1,independent_ui_pairs=4,screen_count=70,trainer_victories=0,wild_victories=3,
                  experience=331,level=8,hp=[24,24],moves_pp=[35,30,25],save_counter=8,
                  native_guarded_host_writes=0,fixture_calls=0,manual_save_keys_only=True,
                  natural_research_arrival_accepted=False,full_story_accepted=False,release_ready=False,
                  active_baseline_changed=False,completed_segment_replay_required=False)
    return result
