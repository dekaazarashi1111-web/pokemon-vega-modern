#!/usr/bin/env python3
"""母親との自然会話→回復→Save→独立Continueの新規区間だけを検証する。"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path
from unittest.mock import patch
import pr16_home_recovery as owner
import pr16_research_story as story

ROOT=Path(__file__).resolve().parents[1]
DEV='content/modernization/pr16_home_recovery_native_development'
PARENT='content/modernization/pr16_research_story_training_checkpoint.json'
SOURCE='scripts/pr16_home_recovery_native.py'
TEST='tests/test_pr16_home_recovery_native.py'
CANDIDATE=owner.CANDIDATE
INPUT_SAVE=owner.INPUT_SAVE
OUTPUT_SAVE=dict(size=131088,sha256='0de597b9e95fd33d62de19610a166ed6dd650a5ba6a4309770083cefe9560773')
RUNNER=dict(size=73792,sha256='9c62d9664d50ea58a150b59b1c2d5465e6a50f5b0824ce4728f92656331ee14d')
BUILD_ARTIFACT=10946449847
BUILD_RUN=36364944598
BUILD_HEAD='4409a5dddf6c4f2f5d08833b35a470fdd544dde3'
BUILD_COMMIT='26e413850e149b9a311e3017ad841676c124e8c0'
BUILD_ARCHIVE=dict(size=18255261,sha256='4910b715c0e74a52564b6ad6dea3bc63061d60de8a9ec7abc01ee8095aaf1819')
AFTER_PARTY='9486f8b643dbf9c17352f8d78961b02d6711f6fac3b354f47e46e3be77e6f9e1'
AFTER_FLASH='0838cc9b71dfe1743770909abf0aa573cf2a773d2e9831526b526bf8db725f77'
need,identity=owner.need,owner.identity


def load(raw):
    return json.loads(raw,object_pairs_hook=story.unique)


def checksum(raw):
    h=2166136261
    for i,b in enumerate(raw):h=((h^(0 if 8<=i<12 else b))*16777619)&0xffffffff
    return h


def ledger(minute):
    """実観測SHAを全2048bytesのsource default/分時計から独立再構成。RAMへ書かない。"""
    need(type(minute) is int and minute in (31,32,33),'今回の3分境界だけ')
    value=bytearray(2048);value[:4]=b'VGS1';struct.pack_into('<HH',value,4,2,2048)
    for off,n in ((29,1),(0x73f,1),(0x740,64),(0x745,1),(0x746,minute),(0x763,1)):value[off]=n
    struct.pack_into('<I',value,8,checksum(value))
    return bytes(value)


def trace(raw,where=None):
    # 旧parserのcandidate指定のみを明示的に切替。旧source/原本/headerの書換えはしない。
    try:
        with patch.object(story,'CANDIDATE',CANDIDATE):result=story.observations(raw,'continue-story',where)
    except (KeyError,TypeError,IndexError) as exc:
        raise ValueError('不完全な原本schema') from exc
    for key in ('warnings_errors','host_write_barriers','guarded_host_writes','fixture_calls'):
        need(type(result['end'][key]) is int,'整数のbool別名を拒否: '+key)
    need(type(result['start']['host_write_barriers']) is int,'begin barrier型')
    need(result['end']['natural_research_arrival_accepted'] is False,'研究到達は未受入')
    for row in result['screens']:
        need(type(row['screen']) is int and type(row['frame']) is int,'screen整数型')
    return result


def command_trace(command,raw,cold=False):
    lines=story.commands(command);t=trace(raw);rows=[load(x) for x in raw.splitlines()]
    count=6 if cold else 18
    need([int(x.split()[1]) for x in lines if x.startswith('observe ')]==list(range(1,count+1)),'欠落のない観測順')
    need(lines.count('save')==(0 if cold else 1),'通常Save1回/cold0回')
    need(lines[-2:]==['observe 6','quit'] if cold else lines[-3:]==['save','observe 18','quit'],'明示終端')
    bootstrap=[(0,600),(8,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(0,180)]
    need([(r['key'],r['frames']) for r in t['inputs'][:12]]==bootstrap,'通常Continue protocol')
    need(rows[13].get('observe')==0 and rows[14].get('screen')==0,'起動直後の観測')
    cursor=15
    for line in lines:
        need(cursor<len(rows),'実行原本欠落');row=rows[cursor];p=line.split()
        if p[0]=='key':
            need('input' in row and (row['key'],row['frames'])==(int(p[1]),int(p[2])),'実入力原本不一致');cursor+=1
        elif p[0]=='observe':
            need(row.get('observe')==int(p[1]) and rows[cursor+1].get('screen')==int(p[1]),'観測と画面の対応');cursor+=2
        elif line=='save':
            start=cursor
            while cursor<len(rows) and 'input' in rows[cursor]:cursor+=1
            need(cursor-start==21 and rows[cursor].get('ordinary_save') is True,'通常UI Saveの21入力');cursor+=1
        else:need(line=='quit' and cursor==len(rows)-1 and row==t['end'],'一意終端');cursor+=1
    need(cursor==len(rows),'余剰操作')
    return t


def verify(raw,cold_raw,parent,output_save,visual,where=None,cold_where=None):
    first,second=trace(raw,where),trace(cold_raw,cold_where)
    command_trace((ROOT/DEV/'commands.txt').read_text(),raw)
    command_trace((ROOT/DEV/'continue-commands.txt').read_text(),cold_raw,True)
    need(parent['actions_completion_confirmed'] is True and parent['run_id']==36362293129 and
         parent['output_save']==INPUT_SAVE and parent['candidate']==owner.PARENT,'正式training入力のみ')
    need(parent['natural_research_arrival_accepted'] is False and parent['release_ready'] is False,'親の過大受入禁止')
    need(output_save==OUTPUT_SAVE,'全Save+RTC identity')
    need(first['start']['initial_save_sha256']==INPUT_SAVE['sha256'] and second['start']['initial_save_sha256']==OUTPUT_SAVE['sha256'],'正しいSave連鎖')
    a,b=first['observations'],second['observations']
    need([r['observe'] for r in a]==list(range(19)) and [r['observe'] for r in b]==list(range(7)),'全26画面')
    need((first['end']['inputs'],first['end']['frames'])==(81,6642) and (second['end']['inputs'],second['end']['frames'])==(34,2572),'新区間全入力会計')
    need(first['saves']==[dict(ordinary_save=True,before=5,after=6,frame=6642)] and not second['saves'],'Save5→6のみ')
    initial=parent['continued']
    for key in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256','ledger_sha256'):
        need(a[0][key]==initial[key],'親境界: '+key)
    need(type(visual['schema_version']) is int and visual['schema_version']==1 and visual['method']=='DIRECT_PIXEL_REVIEW_NO_OCR','実画面目視原本')
    need(set(visual['anchors'])=={'mother_offer','mother_rest','after_heal','party','information','stats','moves'},'全受入画面anchor')
    for anchor in visual['anchors'].values():
        i=anchor['observe'];need(type(i) is int and first['screens'][i]==dict(screen=i,frame=anchor['frame'],sha256=anchor['sha256']),'画面anchor一致')
    for i,row in enumerate(a):
        need(row['map']==([3,0] if i==0 else [4,0]) and row['xy']==([4,27] if i==0 else [4,8] if i==1 else [8,5]),'自然帰宅だけ')
        need(row['party_count']==1 and row['rp']==0 and row['save_counter']==(6 if i==18 else 5),'party/RP/counter')
        need(row['battle_flags']==row['battle_outcome']==0,'戦闘なし')
        need(row['party_sha256']==(initial['party_sha256'] if i<6 else AFTER_PARTY),'元会話中に回復し以後party保持')
        need(row['flash_sha256']==(initial['flash_sha256'] if i<18 else AFTER_FLASH),'最後の通常Saveだけ')
        need(row['ledger_sha256']==identity(ledger(31 if i<6 else 32))['sha256'],'進行ledger全byteは分時計だけ')
    need(all(a[i]['lock']==1 and a[i]['facing']==2 for i in range(3,11)),'母親との通常会話')
    for i in (2,11,17,18):need(a[i]['field'] and a[i]['lock']==0,'会話前後idle')
    for i,row in enumerate(b):
        for key in ('map','xy','live_xy','facing','party_count','save_counter','rp','party_sha256','flash_sha256'):
            need(row[key]==a[-1][key],'独立Continue保持: '+key)
        need(row['battle_flags']==row['battle_outcome']==0,'cold戦闘なし')
        need(row['ledger_sha256']==identity(ledger(32 if i<3 else 33))['sha256'],'cold ledger分時計32→33以外全byte保持')
    need(b[0]['field'] and b[-1]['field'] and b[-1]['lock']==0,'cold idle')
    for i,j in ((13,2),(14,3),(15,4),(16,5)):
        need(first['screens'][i]['sha256']==second['screens'][j]['sha256'],'4独立UI全byte一致')
    return dict(status='PASS_NATURAL_HOME_RECOVERY_SAVE_SCOPED',candidate=CANDIDATE,input_save=INPUT_SAVE,
      output_save=OUTPUT_SAVE,first_save=a[-1],continued=b[-1],ordinary_recovery_accepted=True,
      hp_before=[13,23],hp_after=[23,23],status_before=64,status_after=0,level=7,experience=245,
      moves_pp_before=[31,30,25],moves_pp_after=[35,30,25],natural_research_arrival_accepted=False,
      full_story_accepted=False,travel_native_accepted=False,release_ready=False,active_baseline_changed=False,
      new_native_processes=2,screen_count=26,independent_ui_pairs=4,ordinary_saves=1,save_counter=6,
      native_guarded_host_writes=0,fixture_calls=0,trainer_battles=0,wild_battles=0,
      cold_ledger_clock=dict(saved_minutes=32,final_live_minutes=33,changed_fields=['OWNER_MINUTES','LEDGER_CHECKSUM'],
                            other_ledger_bytes_preserved=True,flash_changed=False))


def saved_bytes(before,after,cold):
    """Flash内partyを観測全SHAで一意同定し、回復以外の597bytes保持を確認する。"""
    need(type(before) is bytes and type(after) is bytes and type(cold) is bytes,'immutable Save bytes')
    need(identity(before)==INPUT_SAVE and identity(after)==OUTPUT_SAVE and cold==after,'全Save/RTCの保持')
    for raw,minute in ((before,31),(after,32)):
        need(raw.count(b'VGS1')==1 and raw[0x1f064:0x1f864]==ledger(minute),'保存ledger全byteとclock')
    def party(raw,sha):
        offsets=[i for i in range(0,131072-600+1,4) if identity(raw[i:i+600])['sha256']==sha]
        need(len(offsets)==1,'Flashに実観測600bytesが一意存在')
        return offsets[0],raw[offsets[0]:offsets[0]+600]
    x,a=party(before,'1cc3c4629af1b2bcf170bd3ad128f913881b5a50e04ed93d186590db81cb4f58')
    y,b=party(after,AFTER_PARTY)
    delta=[dict(offset=i,before=v,after=w) for i,(v,w) in enumerate(zip(a,b)) if v!=w]
    need(delta==[dict(offset=52,before=31,after=35),dict(offset=80,before=64,after=0),dict(offset=86,before=13,after=23)],'party全600bytes中PP/麻痺/HPの3bytesだけ')
    need(a[84]==b[84]==7 and struct.unpack_from('<I',a,36)[0]==struct.unpack_from('<I',b,36)[0]==245,'Lv7/EXP245不変')
    return dict(party_size=600,before_flash_offset=x,after_flash_offset=y,changed_bytes=delta,
                other_party_bytes_preserved=597,all_flash_rtc_preserved_after_continue=True,
                input_ledger=identity(ledger(31)),saved_ledger=identity(ledger(32)),cold_live_ledger=identity(ledger(33)))
