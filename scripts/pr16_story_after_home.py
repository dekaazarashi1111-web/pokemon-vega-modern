#!/usr/bin/env python3
"""回復後の新区間を検証。敗北を勝利にせず、実キーSaveとcold境界を照合。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
DEV = 'content/modernization/pr16_story_after_home_development'
PARENT = 'content/modernization/pr16_home_recovery_native_checkpoint.json'
SOURCE = 'scripts/pr16_story_after_home.py'
TEST = 'tests/test_pr16_story_after_home.py'
CANDIDATE = dict(size=33554432, sha256='06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5')
INPUT_SAVE = dict(size=131088, sha256='0de597b9e95fd33d62de19610a166ed6dd650a5ba6a4309770083cefe9560773')
OUTPUT_SAVE = dict(size=131088, sha256='226865775c9a9eae143eaeac65354170e9d8868469cbd528af852ce05412c8a3')
RUNNER = dict(size=73792, sha256='9c62d9664d50ea58a150b59b1c2d5465e6a50f5b0824ce4728f92656331ee14d')
PARTY_BEFORE = '9486f8b643dbf9c17352f8d78961b02d6711f6fac3b354f47e46e3be77e6f9e1'
PARTY_AFTER = 'e2f52f3035f57334def4f412aa8c8c757a1b63fc3e7d52bbfe2ee34f28b1eaa8'
FLASH_BEFORE = '0838cc9b71dfe1743770909abf0aa573cf2a773d2e9831526b526bf8db725f77'
FLASH_AFTER = '9e2d05c9b0ef1aa59b6b48401d3d25793b5e5f2aad244365a3a991fa97745fa9'
BOOT = [(0,600),(8,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(0,180)]
OBS_INTS = {'observe','frame','facing','lock','callback2','party_count','save_counter','rp','battle_flags','battle_outcome'}
OBS_HASH = {'party_sha256','flash_sha256','ledger_sha256'}
OBS_KEYS = OBS_INTS | OBS_HASH | {'field','map','xy','live_xy'}
END_KEYS = {'end','frames','inputs','warnings_errors','host_write_barriers','guarded_host_writes','fixture_calls','natural_research_arrival_accepted'}
PPM_HEADER = b'P6\n240 160\n255\n'


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def unique(pairs):
    result = {}
    for key,value in pairs:
        need(key not in result, '重複JSON key')
        result[key] = value
    return result


def load(raw):
    try:
        return json.loads(raw, object_pairs_hook=unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError('非有限JSON')))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('UTF-8 JSON原本') from exc


def integer(value, low=0, high=1800000):
    return type(value) is int and low <= value <= high


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def commands(raw):
    need(type(raw) is bytes and 0 < len(raw) < 40000 and raw.endswith(b'\n'), '入力原本bytes/終端')
    try:
        lines = raw.decode('ascii').splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError('ASCII入力') from exc
    need(lines[-1] == 'quit' and lines.count('quit') == 1, '一意quit')
    obs = 0
    for line in lines[:-1]:
        p = line.split(' ')
        if len(p) == 3 and p[0] == 'key':
            need(p[1] in {'0','1','2','8','16','32','64','128'} and
                 p[2].isdigit() and str(int(p[2])) == p[2] and 1 <= int(p[2]) <= 600, '単一実key/frames')
        else:
            obs += 1
            need(line == 'observe '+str(obs), '昇順observeだけ。fixture/save helper禁止')
    return lines


def trace(raw, command, cold=False):
    """保存helperを使わず入力↔JSONLを一対一照合。旧field判定を書換えない。"""
    need(type(cold) is bool and type(raw) is bytes and 0 < len(raw) < 400000 and raw.endswith(b'\n'), '原本/種別')
    lines = commands(command)
    rows = [load(x) for x in raw.splitlines()]
    need(all(type(r) is dict for r in rows) and len(rows) >= 16, '行object/schema')
    start = rows[0]
    expected_seed = OUTPUT_SAVE if cold else INPUT_SAVE
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


def screen_bytes(value, record, blank_allowed=False):
    need(type(value) is bytes and len(value) == len(PPM_HEADER)+240*160*3 and value.startswith(PPM_HEADER), '実PPM形式')
    need(identity(value)['sha256'] == record['sha256'], '全画面bytes SHA')
    need(blank_allowed or len(set(value[len(PPM_HEADER):])) > 1, '受入anchorの空画面禁止')


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('actions_completion_confirmed') is True and
         parent.get('run_id') == 36366801337 and parent.get('retained_artifact_id') == 10947623338 and
         parent.get('candidate') == CANDIDATE and parent.get('output_save') == INPUT_SAVE and
         parent.get('natural_research_arrival_accepted') is False and parent.get('release_ready') is False,
         '終端確認済み回復Saveだけ')


def ledger_checksum(raw):
    n = 2166136261
    for i,v in enumerate(raw):
        n = ((n ^ (0 if 8 <= i < 12 else v))*16777619) & 0xffffffff
    return n


def saved_bytes(before, after, cold):
    need(all(type(x) is bytes for x in (before,after,cold)), 'immutable Save bytes')
    need(identity(before) == INPUT_SAVE and identity(after) == OUTPUT_SAVE and cold == after, 'Save+RTC全131088bytes')
    def party(raw, sha):
        hits = [i for i in range(0,131072-600+1,4) if identity(raw[i:i+600])['sha256'] == sha]
        need(len(hits) == 1, 'Flash内600partybytes一意')
        return hits[0],raw[hits[0]:hits[0]+600]
    x,a = party(before,PARTY_BEFORE); y,b = party(after,PARTY_AFTER)
    delta = [dict(offset=i,before=v,after=w) for i,(v,w) in enumerate(zip(a,b)) if v != w]
    need(delta == [dict(offset=36,before=245,after=14),dict(offset=37,before=0,after=1),dict(offset=41,before=85,after=86)],
         '獲得EXPとbyte41以外の597bytes保持')
    need(struct.unpack_from('<I',b,36)[0] == 270 and b[84] == 7 and
         struct.unpack_from('<I',b,80)[0] == 0 and struct.unpack_from('<HH',b,86) == (23,23) and
         list(b[52:55]) == [35,30,25], 'Lv/EXP/HP/状態/PP')
    la,lb = before[0x1f064:0x1f864],after[0x1f064:0x1f864]
    for raw,minutes in ((la,32),(lb,39)):
        need(raw[:4] == b'VGS1' and raw[0x746] == minutes and
             struct.unpack_from('<I',raw,8)[0] == ledger_checksum(raw), 'ledger分時計/checksum')
    need([i for i in range(2048) if la[i] != lb[i]] == [8,9,10,11,0x746], '他ledger owner不変')
    return dict(before_party_offset=x,after_party_offset=y,party_changed_bytes=delta,other_party_bytes_preserved=597,
                experience_before=245,experience_after=270,hp=[23,23],level=7,moves_pp=[35,30,25],
                saved_minutes_before=32,saved_minutes_after=39,all_save_rtc_preserved_after_continue=True)


def verify(raw, cold_raw, command, cold_command, parent, expected, where=None, cold_where=None):
    parent_boundary(parent)
    a,b = trace(raw,command),trace(cold_raw,cold_command,True)
    ao,bo = a['observations'],b['observations']
    need(len(ao) == 101 and len(bo) == 9 and a['end']['inputs'] == 270 and a['end']['frames'] == 28012 and
         b['end']['inputs'] == 34 and b['end']['frames'] == 2852, '新区間270/cold34入力と110画面')
    need(set(expected) == {'schema_version','method','files','anchors','ui_pairs','blank_transition_observations','claims'}, '目視原本schema')
    need(type(expected['schema_version']) is int and expected['schema_version'] == 1 and
         expected['method'] == 'DIRECT_PIXEL_REVIEW_NO_OCR', '目視原本')
    need(expected['claims'] == dict(trainer_victories=0,trainer_losses=1,wild_escapes=1,opponents_defeated=1,
         experience_gained=25,research_arrival=False,full_story=False,release_ready=False), '勝利等への昇格禁止')
    boundary = parent['continued']
    for k in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(ao[0][k] == boundary[k], '親の停止点保持: '+k)
    need(ao[0]['ledger_sha256'] == parent['first_save']['ledger_sha256'], '保存済み32分から起動。前回coldの揮発33分とは区別')
    need(bo[0]['ledger_sha256'] == ao[-1]['ledger_sha256'], '保存済み39分から再起動')
    need(ao[38]['map'] == [3,19] and ao[38]['xy'] == [52,13] and ao[40]['xy'] == [53,10], '東側道路の新到達位置')
    need(ao[25]['battle_flags'] == 4 and ao[29]['battle_outcome'] == 4, '野生遭遇→逃走')
    need(ao[42]['battle_flags'] == 12 and ao[66]['battle_outcome'] == 2 and ao[71]['map'] == [4,0], 'トレーナー敗北→帰宅')
    for i,row in enumerate(ao):
        need(row['party_count'] == 1 and row['rp'] == 0 and row['save_counter'] == (6 if i < 99 else 7), 'party/RP/通常Save6→7')
        need(row['flash_sha256'] == (FLASH_BEFORE if i < 99 else FLASH_AFTER), '実UI承諾後だけFlash変更')
    need(ao[-1]['lock'] == 0 and ao[-1]['callback2'] == 134569589 and ao[-1]['field'] is False and
         ao[-1]['battle_flags'] == 12 and ao[-1]['battle_outcome'] == 2, '旧battle telemetryを消さず記録')
    for row in bo:
        for k in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
            need(row[k] == ao[-1][k], '独立Continueの保存保持: '+k)
        need(row['battle_flags'] == row['battle_outcome'] == 0, 'coldで揮発battle情報消去')
    need(bo[0]['field'] and bo[-1]['field'] and bo[-1]['lock'] == 0, 'cold idle')
    need(ao[-1]['party_sha256'] == PARTY_AFTER, '全party保持')
    need(expected['ui_pairs'] == [[89,3],[91,5],[92,6],[93,7]], '独立4UI対応')
    for i,j in expected['ui_pairs']:
        need(a['screens'][i]['sha256'] == b['screens'][j]['sha256'], '独立4UI全byte一致')
    need(expected['blank_transition_observations'] == [6,30], '既知2枚の遷移黒画面だけ')
    need(set(expected['anchors']) == {f'observe_{i}' for i in ANCHORS}, '全anchor集合')
    need(set(expected['files']) == set(ORIGINALS), '全原本集合')
    for label,entry in expected['anchors'].items():
        need(set(entry) == {'observe','frame','sha256','note_ja'} and type(entry['observe']) is int and
             0 <= entry['observe'] <= 100, 'anchor schema')
        i = entry['observe']
        need(a['screens'][i] == dict(screen=i,frame=entry['frame'],sha256=entry['sha256']), '実画面anchor一致: '+label)
    for t,folder,is_cold in ((a,where,False),(b,cold_where,True)):
        if folder is None: continue
        folder = Path(folder)
        need({p.name for p in folder.glob('screen-*.ppm')} == {f'screen-{r["screen"]:04d}.ppm' for r in t['screens']}, '全画面集合')
        for r in t['screens']:
            i = r['screen']; blank = not is_cold and i in (6,30)
            need(not blank or t['observations'][i]['lock'] == 1, '黒画面はscript遷移中だけ')
            screen_bytes((folder/f'screen-{i:04d}.ppm').read_bytes(),r,blank)
    for name,data in (('progress.stdout.txt',raw),('continue.stdout.txt',cold_raw),('commands.txt',command),('continue-commands.txt',cold_command)):
        need(identity(data) == expected['files'][name] == ORIGINALS[name], '開発と独立測定の全原本一致: '+name)
    return dict(status='PASS_STORY_AFTER_HOME_LOSS_SAVE_SCOPED',candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,
                first_save=ao[-1],continued=bo[-1],new_native_processes=2,screen_count=110,independent_ui_pairs=4,
                ordinary_saves=1,save_counter=7,experience=270,level=7,hp=[23,23],moves_pp=[35,30,25],
                trainer_victories=0,trainer_losses=1,wild_escapes=1,opponents_defeated=1,
                natural_research_arrival_accepted=False,full_story_accepted=False,release_ready=False,active_baseline_changed=False,
                manual_save_keys_only=True,legacy_field_telemetry_preserved=True,fixture_calls=0,native_guarded_host_writes=0)

# 開発2processで目視確認した原本の完全SHA。Actions生成値を期待値に自己代入しない。
ORIGINALS = {
 'commands.txt': dict(size=3529,sha256='4fa2db3ee24d2f93596ac5a8884f2ce5721fee211af82eebe515538a8ac26947'),
 'continue-commands.txt': dict(size=283,sha256='7e0b801addf81efac500dc02ead4709547e59a15dc7fa61361cbc5160df9e98e'),
 'progress.stdout.txt': dict(size=69240,sha256='9c0eb0eeb2212b1d12b3f5591fb4a892a45b2c9e54cac85fcbadd99a65dcedf9'),
 'continue.stdout.txt': dict(size=6903,sha256='d01accb9b20b9d966592a2a39a9d4be23c2aa4dd1e469b6fcc8a9d903164fa43')}
ANCHORS = {25:'野生スバメLv3の実遭遇。',29:'うまくにげきれた。勝利ではない。',42:'じゅくがえりマオリの通常戦闘。',56:'パモ撃破。トレーナー戦全体の勝利ではない。',57:'経験値25獲得。',58:'次のコフキムシLv8。',66:'戦えるポケモンがいない。',68:'賞金56円を支払い。',71:'通常全滅帰宅。',86:'回復済み帰宅idle。旧battle flagは残存。',89:'手持ち1匹、Lv7、HP23/23。',91:'種族・ID・出会い情報保持。',92:'EXP270、HP23/23。',93:'3技PP35/30/25、4枠目空。',96:'レポートを選択。',97:'通常Saveの確認。',98:'上書き確認。',99:'実Save成功表示、counter7。',100:'通常会話/Save UIを閉じた停止点。'}


def expectations(raw):
    """既知SHAの同一原本から目視anchorを取り出す。新規測定結果の盲目的採用禁止。"""
    need(identity(raw) == ORIGINALS['progress.stdout.txt'], '目視済み開発原本の全SHA')
    screens = {r['screen']:r for r in [load(x) for x in raw.splitlines()] if 'screen' in r}
    return dict(schema_version=1,method='DIRECT_PIXEL_REVIEW_NO_OCR',files=ORIGINALS,
       anchors={f'observe_{i}':dict(observe=i,frame=screens[i]['frame'],sha256=screens[i]['sha256'],note_ja=note) for i,note in ANCHORS.items()},
       ui_pairs=[[89,3],[91,5],[92,6],[93,7]],blank_transition_observations=[6,30],
       claims=dict(trainer_victories=0,trainer_losses=1,wild_escapes=1,opponents_defeated=1,experience_gained=25,
                   research_arrival=False,full_story=False,release_ready=False))
