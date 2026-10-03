#!/usr/bin/env python3
"""Save8からの新区間のみ。野生勝利と逃走、Save9を独立に検証する。"""
from __future__ import annotations
from pathlib import Path
import struct
import pr16_story_safe_training as prior

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'scripts/pr16_story_save9.py'
TEST = 'tests/test_pr16_story_save9.py'
DEV = 'content/modernization/pr16_story_save9_development'
CP = 'content/modernization/pr16_story_save9_checkpoint.json'
PARENT = prior.CP
CANDIDATE, RUNNER, INPUT_SAVE = prior.CANDIDATE, prior.RUNNER, prior.OUTPUT_SAVE
OUTPUT_SAVE = dict(size=131088, sha256='524df8da2e6e45b6a1d9dc0446e600740a79ff772c56a8423413994c09b32063')
REVIEW = dict(size=7824, sha256='ac26d18c1234b46fe4822a19001949a6bfc90c1d77fef2eecc00dabba7a45555')
PARTY_BEFORE = prior.PARTY_AFTER
PARTY_AFTER = '77a075eb001496518841e791429aff628229638fe2b98d48efcf5af0657af23c'
FLASH_BEFORE = prior.FLASH_AFTER
FLASH_AFTER = 'b2681be93885914568b9ad1d7eefff5521332547da50f890b5c4be9e008099c4'
CLAIMS = dict(wild_victories=3,wild_escapes=2,trainer_victories=0,losses=0,captures=0,
              experience_gained=119,mother_heal_visits=2,ordinary_saves=1,
              research_arrival=False,full_story=False,release_ready=False)
PAIRS = [[54,1],[55,2],[56,3],[57,4]]
need, identity, load = prior.need, prior.identity, prior.load
trace, commands, screen_bytes = prior.trace, prior.commands, prior.screen_bytes


def parent_boundary(parent):
    need(type(parent) is dict and parent.get('actions_completion_confirmed') is True and
         parent.get('run_id') == 36374575742 and parent.get('retained_artifact_id') == 10950920338 and
         parent.get('candidate') == CANDIDATE and parent.get('output_save') == INPUT_SAVE and
         type(parent.get('save_counter')) is int and parent['save_counter'] == 8 and
         type(parent.get('experience')) is int and parent['experience'] == 331 and
         parent.get('trainer_victories') == 0 and parent.get('natural_research_arrival_accepted') is False and
         parent.get('release_ready') is False, '終端確認済みSave8のみ。旧入力は再生しない')


def review(raw):
    need(type(raw) is bytes and identity(raw) == REVIEW, '直接目視原本を固定。未確認の成功を追認しない')
    value=load(raw)
    need(value['method'] == 'DIRECT_PIXEL_REVIEW_NO_OCR' and value['input_save'] == INPUT_SAVE and
         value['output_save'] == OUTPUT_SAVE and value['claims'] == CLAIMS and value['ui_pairs'] == PAIRS,
         '目視scope/保存/UI対応')
    return value


def semantic(a,b,parent):
    parent_boundary(parent)
    ao,bo=a['observations'],b['observations']
    need(len(ao)==68 and len(bo)==6 and a['end']['inputs']==363 and a['end']['frames']==31080 and
         b['end']['inputs']==34 and b['end']['frames']==2808, '新区間363/cold34入力、74画面')
    for key in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
        need(ao[0][key]==parent['continued'][key], '親Save8開始点: '+key)
    need(ao[0]['field'] is True and ao[0]['lock']==0 and ao[0]['battle_flags']==ao[0]['battle_outcome']==0,
         'fresh開始')
    need(all(o['rp']==0 and o['party_count']==1 for o in ao+bo), 'RP/捕獲/手持ち増加なし')
    need(all(o['map'] in ([4,0],[3,0],[3,19]) for o in ao), '研究施設/初期研究室到達へ昇格しない')
    need(all(o['battle_flags'] in (0,4) and o['battle_outcome'] in (0,1,4) for o in ao),
         'トレーナー戦/敗北はない')
    starts=[];last=False
    for o in ao:
        active=o['lock']==1 and o['battle_flags']==4 and o['battle_outcome']==0
        if active and not last: starts.append(o['observe'])
        last=active
    need(starts==[7,17,26,39,48], '野生5遭遇の開始境界')
    for index in (16,24,47):
        o=ao[index]
        need(o['callback2']==134569589 and o['lock']==0 and o['battle_outcome']==1, '3勝後のfield復帰')
    for before,escape,returned in ((24,27,28),(47,49,50)):
        need(ao[escape]['battle_outcome']==4 and ao[escape]['callback2']==134285761 and
             ao[returned]['battle_outcome']==4 and ao[returned]['callback2']==134569589 and
             ao[returned]['lock']==0, '2回の通常逃走。勝利ではない')
        need(all(o['party_sha256']==ao[before]['party_sha256'] for o in ao[before:returned+1]),
             '逃走前後600partybytes。EXP/HP/PPの偽加算なし')
    need(ao[34]['party_sha256']!=ao[35]['party_sha256'] and ao[51]['party_sha256']!=ao[52]['party_sha256'],
         '母親回復2回')
    need(all(o['save_counter']==8 and o['flash_sha256']==FLASH_BEFORE for o in ao[:61]),
         '最初の保存確認までは元Save8のまま')
    need(all(o['save_counter']==8 for o in ao[61:65]) and ao[65]['save_counter']==9,
         '書込中counterの境界')
    transient=[o['flash_sha256'] for o in ao[61:66]]
    need(len(set(transient))==5 and all(x not in (FLASH_BEFORE,FLASH_AFTER) for x in transient),
         'counter9の先行変化だけを保存完了としない')
    for index in range(58,67):
        need(ao[index]['lock']==1 and ao[index]['callback2']==134569589, '実レポートUIのlock/callback')
    for o in ao[66:]:
        need(o['save_counter']==9 and o['flash_sha256']==FLASH_AFTER, '書込完了表示と最終Flash')
    need(ao[67]['lock']==0 and ao[67]['callback2']==134569589 and
         ao[67]['battle_flags']==4 and ao[67]['battle_outcome']==4 and ao[67]['field'] is False,
         '保存後field復帰。旧telemetryの残留値を改作しない')
    need(all(o['party_sha256']==PARTY_AFTER for o in ao[52:]+bo), '回復/保存/Continueの全600partybytes')
    for o in bo:
        need(o['map']==[4,0] and o['xy']==[8,5] and o['live_xy']==[15,12] and o['facing']==2 and
             o['save_counter']==9 and o['flash_sha256']==FLASH_AFTER and o['battle_flags']==o['battle_outcome']==0,
             'cold境界と保存保持')
    need(all(bo[i]['field'] is True and bo[i]['lock']==0 for i in (0,5)), 'cold fieldで開始/終了')
    for x,y in PAIRS:
        need(ao[x]['callback2']==bo[y]['callback2'] and ao[x]['lock']==bo[y]['lock']==1, '4実UIのcallback')
    return dict(first_save=ao[-1],continued=bo[-1],claims=CLAIMS)


def save_structure(before,after,cold):
    """全体SHAから独立した保存構造/成長差分。私有byteを結果JSONへ出さない。"""
    need(all(type(v) is bytes and len(v)==131088 for v in (before,after,cold)), 'Save/RTCの長さ/種別')
    need(cold==after, '独立Continue後の全131088bytes')
    def sections(raw,bank,counter):
        rows={}
        for offset in range(bank,bank+0xe000,0x1000):
            sid,checksum,signature,count=struct.unpack_from('<HHII',raw,offset+0xff4)
            need(sid not in rows and 0<=sid<14 and signature==0x08012025 and count==counter,
                 '全14sectionの一意ID/署名/counter')
            rows[sid]=offset
        need(set(rows)==set(range(14)), '全14section')
        return rows
    old=sections(before,0,8);new=sections(after,0xe000,9);sections(after,0,8)
    need(before[:0xe000]==after[:0xe000], '前回Save8 bankの57344bytesを保持')
    pa,pb=old[1]+0x38,new[1]+0x38
    x,y=before[pa:pa+600],after[pb:pb+600]
    need(struct.unpack_from('<I',before,old[1]+0x34)[0]==struct.unpack_from('<I',after,new[1]+0x34)[0]==1,
         '保存された手持ち数1')
    wanted=[(36,75,194),(41,96,104),(60,0,1),(84,8,9),(86,24,26),(88,24,26),
            (90,15,16),(92,12,13),(94,17,18),(96,16,17),(98,13,14)]
    delta=[(i,u,v) for i,(u,v) in enumerate(zip(x,y)) if u!=v]
    need(delta==wanted, '自然成長の11bytes以外を保持')
    need(x[:36]==y[:36] and x[42:56]==y[42:56] and x[100:]==y[100:], '個体識別/技/空party保持')
    need(identity(x)['sha256']==PARTY_BEFORE and identity(y)['sha256']==PARTY_AFTER, '保存partyの同定')
    need(struct.unpack_from('<I',x,36)[0]==331 and struct.unpack_from('<I',y,36)[0]==450 and y[84]==9 and
         struct.unpack_from('<I',y,80)[0]==0 and list(y[52:56])==[35,30,25,0] and
         struct.unpack_from('<7H',y,86)==(26,26,16,13,18,17,14), '保存EXP/Lv/状態/PP/全能力')
    la,lb=before[0x1f064:0x1f864],after[0x1f064:0x1f864]
    for raw,minute in ((la,46),(lb,54)):
        need(raw[:4]==b'VGS1' and raw[0x746]==minute and
             struct.unpack_from('<I',raw,8)[0]==prior.prior.ledger_checksum(raw), 'ledger時計/checksum')
    need([i for i in range(2048) if la[i]!=lb[i]]==[8,9,10,11,0x746], '他ledger owner保持')
    return dict(before_party_offset=pa,after_party_offset=pb,party_changed_bytes=[
        dict(offset=i,before=u,after=v) for i,u,v in delta],other_party_bytes_preserved=589,
        previous_save_bank_preserved_bytes=57344,save_counters=[8,9,9],experience_before=331,
        experience_after=450,experience_gained=119,level_before=8,level_after=9,
        all_save_rtc_preserved_after_continue=True,saved_minutes_before=46,saved_minutes_after=54)


def saved_bytes(before,after,cold):
    proof=save_structure(before,after,cold)
    need(identity(before)==INPUT_SAVE and identity(after)==OUTPUT_SAVE, '固定された前後Save全byte')
    return proof


def verify(raw,cold_raw,command,cold_command,parent,review_raw,where,cold_where):
    expected=review(review_raw)
    a,b=trace(raw,command,INPUT_SAVE),trace(cold_raw,cold_command,OUTPUT_SAVE)
    result=semantic(a,b,parent)
    need(a['end']==expected['progress_end'] and b['end']==expected['continue_end'], '目視原本の実終端')
    for folder,parsed in ((where,a),(cold_where,b)):
        need(isinstance(folder,Path) and folder.is_dir(), '全画面原本必須')
        need({p.name for p in folder.glob('screen-*.ppm')}==
             {f'screen-{s["screen"]:04d}.ppm' for s in parsed['screens']}, '全74画面の一意集合')
        for s in parsed['screens']:
            screen_bytes((folder/f'screen-{s["screen"]:04d}.ppm').read_bytes(),s)
    for x,y in PAIRS:
        need((where/f'screen-{x:04d}.ppm').read_bytes()==(cold_where/f'screen-{y:04d}.ppm').read_bytes(),
             '4UIの全byteが独立Continueで一致')
    for anchor in expected['anchors']:
        need(a['screens'][anchor['screen']]['sha256']==anchor['sha256'], '直接目視anchorと画面原本')
    for name,value in (('progress.stdout.txt',raw),('continue.stdout.txt',cold_raw),
                       ('commands.txt',command),('continue-commands.txt',cold_command)):
        need(identity(value)==expected['files'][name], '目視済み新区間との同一性: '+name)
    result.update(candidate=CANDIDATE,input_save=INPUT_SAVE,output_save=OUTPUT_SAVE,
        new_native_processes=2,ordinary_saves=1,independent_ui_pairs=4,screen_count=74,
        trainer_victories=0,wild_victories=3,wild_escapes=2,losses=0,captures=0,mother_heal_visits=2,
        experience=450,experience_gained=119,level=9,hp=[26,26],moves_pp=[35,30,25],save_counter=9,
        native_guarded_host_writes=0,fixture_calls=0,manual_save_keys_only=True,
        save_complete_text_observed=True,natural_research_arrival_accepted=False,
        full_story_accepted=False,release_ready=False,active_baseline_changed=False,
        completed_segment_replay_required=False)
    return result
