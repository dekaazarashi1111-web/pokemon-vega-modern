#!/usr/bin/env python3
"""Save9後の通常ボール5個供給・二重受取防止・Save10だけを検証する。"""
from __future__ import annotations
from pathlib import Path
import struct
import pr16_story_save9 as prior
import pr16_story_journey_boundaries as journey

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts/pr16_story_save10.py'
TEST = 'tests/test_pr16_story_save10.py'
DEV = 'content/modernization/pr16_story_save10_development'
CP = 'content/modernization/pr16_story_save10_checkpoint.json'
PARENT = prior.CP
CANDIDATE, RUNNER, INPUT_SAVE = prior.CANDIDATE, prior.RUNNER, prior.OUTPUT_SAVE
OUTPUT_SAVE = dict(size=131088, sha256='c2c08321b12ef4b5039884d9e4155eb32a614415bb68a1497758cdedfb9000c0')
REVIEW = dict(size=9174, sha256='1b1fd015a8147fd7af80058c0967e995f226b4daafc0b994d6a7dda63c253937')
PARTY_BEFORE = prior.PARTY_AFTER
PARTY_AFTER = 'aa781c821ad1258389a36c35285964eca19ea6e29215057ffa8548e90a38ee8f'
FLASH_BEFORE = prior.FLASH_AFTER
FLASH_AFTER = '2087fd5a4476b1207c6939a0849c554d1a8b62b1d45c6d485a55a98d19fdfcc9'
LEDGER_AFTER = '00161c6c5b5681ba95befd0ca739efe9a7e8fe7c8a197dd32610e05d3aa92ebd'
CLAIMS = dict(poke_balls_received=5,poke_balls_before=0,poke_balls_after=5,ordinary_gift=True,
              repeat_gift_before_save=False,repeat_gift_after_continue=False,wild_victories=0,
              trainer_victories=0,losses=0,escapes=0,captures=0,experience_gained=0,ordinary_saves=1,
              natural_research_arrival=False,full_story=False,release_ready=False)
PAIRS = [[26,1],[27,2],[44,7],[48,7],[50,9],[51,10],[52,11],[45,4],[46,5],[47,6],[63,0],[63,12]]
need, identity, load = prior.need, prior.identity, prior.load
trace, commands, screen_bytes = prior.trace, prior.commands, prior.screen_bytes


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('status') == 'PASS_STORY_SAVE9_SCOPED' and
         parent.get('actions_completion_confirmed') is True and parent.get('run_id') == 36408354430 and
         parent.get('retained_artifact_id') == 10963436148 and parent.get('candidate') == CANDIDATE and
         parent.get('output_save') == INPUT_SAVE and type(parent.get('save_counter')) is int and
         parent['save_counter'] == 9 and type(parent.get('experience')) is int and parent['experience'] == 450 and
         parent.get('trainer_victories') == 0 and parent.get('natural_research_arrival_accepted') is False and
         parent.get('release_ready') is False, '終端確認済みSave9だけから開始')


def review(raw):
    need(type(raw) is bytes and identity(raw) == REVIEW, '直接目視原本の同定')
    value=load(raw)
    need(value['method']=='DIRECT_PIXEL_REVIEW_NO_OCR' and value['input_save']==INPUT_SAVE and
         value['output_save']==OUTPUT_SAVE and value['claims']==CLAIMS and value['full_image_pairs']==PAIRS,
         '目視の供給/保存scope')
    return value


def semantic(a,b,parent):
    parent_boundary(parent)
    ao,bo=a['observations'],b['observations']
    need(len(ao)==64 and len(bo)==13 and a['end']['inputs']==218 and a['end']['frames']==16486 and
         b['end']['inputs']==62 and b['end']['frames']==4608, '新区間218/cold62入力、77画面')
    for key in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(ao[0][key]==parent['continued'][key], 'Save9正式親の開始点: '+key)
    need(all(o['battle_flags']==o['battle_outcome']==0 and o['rp']==0 and o['party_count']==1 for o in ao+bo),
         '戦闘/捕獲/RP供給/手持ち増加はない')
    need(sum(journey.counts(ao).values())==sum(journey.counts(bo).values())==0, '境界集計で勝利等を作らない')
    need({tuple(o['map']) for o in ao}=={(4,0),(3,0),(4,3),(3,19),(32,2)},
         '初期研究室と民家のみ。対象研究施設や別道路へ昇格しない')
    need(all(o['party_sha256']==PARTY_BEFORE for o in ao[:22]) and
         all(o['party_sha256']==PARTY_AFTER for o in ao[22:]+bo), '徒歩の友情1byte以外は保存party不変')
    need(all(o['save_counter']==9 for o in ao[:62]) and
         all(o['flash_sha256']==FLASH_BEFORE for o in ao[:57]), '保存前は正式親Flashのまま')
    transient=[o['flash_sha256'] for o in ao[57:62]]
    need(len(set(transient))==5 and all(x not in (FLASH_BEFORE,FLASH_AFTER) for x in transient),
         '5つの書込途中Flashを保存完了としない')
    need(all(ao[i]['lock']==1 and ao[i]['callback2']==journey.FIELD_CALLBACK for i in range(54,63)),
         '通常レポート確認/上書き/書込/完了のUI境界')
    for o in ao[62:]+bo:
        need(o['save_counter']==10 and o['flash_sha256']==FLASH_AFTER and o['ledger_sha256']==LEDGER_AFTER and
             o['map']==[32,2] and o['xy']==[4,3] and o['live_xy']==[11,10] and o['facing']==1,
             '通常Save10と独立Continueの同じ停止位置')
    for o in (ao[0],ao[63],bo[0],bo[12]):
        need(o['field'] is True and o['lock']==0 and o['callback2']==journey.FIELD_CALLBACK, 'unlocked field境界')
    for i in (26,27,28,44,48):
        need(ao[i]['callback2']==135301605 and ao[i]['lock']==1, 'バッグ原本')
    for i in (1,2,3,7):
        need(bo[i]['callback2']==135301605 and bo[i]['lock']==1, 'coldバッグ原本')
    need(all(ao[i]['map']==[32,2] and ao[i]['lock']==1 for i in range(37,44)), '女性への通常贈与会話')
    return dict(first_save=ao[-1],continued=bo[-1],claims=CLAIMS)


def save_structure(before,after,cold):
    """再暗号化keyを解いて数量を比較。fixture/元saveの書換えはしない。"""
    need(all(type(v) is bytes and len(v)==131088 for v in (before,after,cold)), 'Save/RTCの長さ/種別')
    need(cold==after, '独立Continue後も全131088bytes保持')
    def sections(raw,bank,counter):
        result={}
        for off in range(bank,bank+0xe000,0x1000):
            sid,checksum,signature,count=struct.unpack_from('<HHII',raw,off+0xff4)
            need(sid not in result and 0<=sid<14 and signature==0x08012025 and count==counter,
                 '全14sectionの一意ID/署名/counter')
            result[sid]=off
        need(set(result)==set(range(14)), 'section欠落')
        return result
    sections(before,0,8);old=sections(before,0xe000,9)
    new=sections(after,0,10);sections(after,0xe000,9)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000], '前回Save9 bankの57344bytes保持')
    pa,pb=old[1]+0x38,new[1]+0x38
    x,y=before[pa:pa+600],after[pb:pb+600]
    need(struct.unpack_from('<I',before,old[1]+0x34)[0]==struct.unpack_from('<I',after,new[1]+0x34)[0]==1,
         '保存された手持ち数1')
    delta=[(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u!=v]
    need(delta==[(41,104,106)], '徒歩の友情+2以外599partybytesを保持')
    need(identity(x)['sha256']==PARTY_BEFORE and identity(y)['sha256']==PARTY_AFTER, '保存party同定')
    need(struct.unpack_from('<I',y,36)[0]==450 and y[84]==9 and struct.unpack_from('<I',y,80)[0]==0 and
         list(y[52:56])==[35,30,25,0] and struct.unpack_from('<7H',y,86)==(26,26,16,13,18,17,14),
         'EXP/レベル/HP/PP/全能力保持')
    def bag(raw,table):
        key=struct.unpack_from('<I',raw,table[0]+0xf20)[0]
        pockets={}
        for name,off,n in [('items',0x310,42),('key_items',0x3b8,30),('balls',0x430,13),
                           ('machines',0x464,58),('berries',0x54c,43)]:
            pockets[name]=[(struct.unpack_from('<HH',raw,table[1]+off+4*i)[0],
                            struct.unpack_from('<HH',raw,table[1]+off+4*i)[1]^(key&0xffff)) for i in range(n)]
        money=struct.unpack_from('<I',raw,table[1]+0x290)[0]^key
        return pockets,money
    ia,ma=bag(before,old);ib,mb=bag(after,new)
    need(ma==mb==2776, '所持金は2776のまま。購入や敗北としない')
    for pocket in ia:
        changes=[(i,u,v) for i,(u,v) in enumerate(zip(ia[pocket],ib[pocket])) if u!=v]
        need(changes==([(0,(0,0),(4,5))] if pocket=='balls' else []), '5pocketの通常供給差分: '+pocket)
    need(ia['balls']==[(0,0)]*13 and ib['balls']==[(4,5)]+[(0,0)]*12,
         'モンスターボールだけ0→5、残12枠は空')
    la,lb=before[0x1f064:0x1f864],after[0x1f064:0x1f864]
    for raw,minute in ((la,54),(lb,58)):
        need(raw[:4]==b'VGS1' and raw[0x746]==minute and
             struct.unpack_from('<I',raw,8)[0]==prior.prior.prior.ledger_checksum(raw), 'ledger時計/checksum')
    need([i for i in range(2048) if la[i]!=lb[i]]==[8,9,10,11,0x746], 'RP/他ledger owner保持')
    return dict(before_party_offset=pa,after_party_offset=pb,other_party_bytes_preserved=599,
                party_changed_bytes=[dict(offset=41,before=104,after=106)],previous_save_bank_preserved_bytes=57344,
                save_counters=[9,10,10],poke_ball_item_id=4,poke_balls_before=0,poke_balls_after=5,
                other_four_bag_pockets_unchanged=True,other_ball_slots_unchanged=True,
                money_before=2776,money_after=2776,experience_before=450,experience_after=450,
                experience_gained=0,level=9,saved_minutes_before=54,saved_minutes_after=58,
                all_save_rtc_preserved_after_continue=True)


def saved_bytes(before,after,cold):
    value=save_structure(before,after,cold)
    need(identity(before)==INPUT_SAVE and identity(after)==OUTPUT_SAVE, '固定前後Saveの全byte同定')
    return value


def verify(raw,cold_raw,command,cold_command,parent,review_raw,where,cold_where):
    expected=review(review_raw)
    a,b=trace(raw,command,INPUT_SAVE),trace(cold_raw,cold_command,OUTPUT_SAVE)
    result=semantic(a,b,parent)
    need(a['end']==expected['progress_end'] and b['end']==expected['continue_end'], '目視原本の終端')
    for folder,parsed in ((where,a),(cold_where,b)):
        need(isinstance(folder,Path) and folder.is_dir(), '77画面原本が必要')
        need({p.name for p in folder.glob('screen-*.ppm')}==
             {f'screen-{s["screen"]:04d}.ppm' for s in parsed['screens']}, '画面集合の過不足')
        for s in parsed['screens']:
            screen_bytes((folder/f'screen-{s["screen"]:04d}.ppm').read_bytes(),s)
    for x,y in PAIRS:
        need((where/f'screen-{x:04d}.ppm').read_bytes()==(cold_where/f'screen-{y:04d}.ppm').read_bytes(),
             '12組の全pixel比較: バッグ/再会話/情報/能力/技/field')
    p=(where/'screen-0049.ppm').read_bytes()[15:];q=(cold_where/'screen-0008.ppm').read_bytes()[15:]
    changed=[i//3 for i in range(0,len(p),3) if p[i:i+3]!=q[i:i+3]]
    need(len(changed)==358 and all(10<=i%240<=37 and 32<=i//240<=54 for i in changed),
         'party一覧の差分はsprite animation矩形だけ。全画面一致とはしない')
    for parsed,key in ((a,'anchors'),(b,'cold_anchors')):
        for item in expected[key]:
            need(parsed['screens'][item['screen']]['sha256']==item['sha256'], '直接目視anchor')
    for name,value in (('progress.stdout.txt',raw),('continue.stdout.txt',cold_raw),
                       ('commands.txt',command),('continue-commands.txt',cold_command)):
        need(identity(value)==expected['files'][name], '開発原本との完全一致: '+name)
    result.update(candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,ordinary_saves=1,
                  new_native_processes=2,screen_count=77,full_image_comparisons=12,party_list_full_image_equal=False,
                  poke_balls=5,poke_balls_received=5,gift_repeat_blocked_before_save=True,gift_repeat_blocked_after_cold=True,
                  trainer_victories=0,wild_victories=0,losses=0,captures=0,experience=450,experience_gained=0,
                  level=9,hp=[26,26],moves_pp=[35,30,25],money=2776,save_counter=10,
                  native_guarded_host_writes=0,fixture_calls=0,manual_save_keys_only=True,save_complete_text_observed=True,
                  natural_research_arrival_accepted=False,full_story_accepted=False,release_ready=False,
                  active_baseline_changed=False,accepted_case_reruns=0)
    return result
