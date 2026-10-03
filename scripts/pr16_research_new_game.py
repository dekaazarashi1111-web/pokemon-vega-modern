#!/usr/bin/env python3
"""通常new-gameのinput-only生成と閉じた全ledger/保存受入validator。"""
from __future__ import annotations
import re
import struct
from pathlib import Path
import pr16_research_phase0_load as common
need,identity,exact=common.need,common.identity,common.exact
old=common.old; closed=old.old
ROOT=Path(__file__).resolve().parents[1]
C='tools/mgba_pr16_research_new_game.c'
CASE='ordinary-new-game-first-save-two-continues'
SCOPE='ORDINARY_NEW_GAME_FIRST_SAVE_AND_TWO_FRESH_CONTINUES'
STAGES=('new_game_field','first_saved','continued','continued_again')
CANDIDATE=common.CANDIDATE
ERASED=identity(b'\xff'*131072)
TRACE='tools/mgba_ai_fixture_runner.c'


def trace(text=None):
    text=(ROOT/TRACE).read_text() if text is None else text
    marker='static const struct Segment BOOT_TRACE[] = {'
    need(text.count(marker)==1,'one boot trace')
    body=text.split(marker)[1].split('};',1)[0]
    body=re.sub(r'/\*.*?\*/','',body,flags=re.S)
    body=re.sub(r'\bA\((\d+)\)',r'{2,1},{\1,0}',body)
    entries=re.findall(r'\{\s*(\d+)\s*,\s*(\d+)\s*\}',body)
    remainder=re.sub(r'\{\s*\d+\s*,\s*\d+\s*\}','',body)
    need(not remainder.strip(' \r\n\t,') and len(entries)>=233,'closed trace syntax/extent')
    rows=[(int(f),int(k)) for f,k in entries[:233]]
    need(all(0<f<=600 and k in (0,1,2,8,16,32,64,128) for f,k in rows),'bounded normal keys')
    raw=b''.join(struct.pack('<IH',f,k) for f,k in rows)
    return {'trace_segments':233,'trace_frames':sum(f for f,_ in rows),'trace_sha256':identity(raw)['sha256']}


def initial_ledger(minute):
    closed.integer(minute,0,10,'bounded natural minute')
    b=bytearray(2048);b[:8]=b'VGS1\x02\0\0\x08';b[29]=1
    b[0x73f],b[0x740],b[0x745],b[0x746],b[0x763]=1,64,1,minute,1
    return old.seal(b)


def generate():
    # 旧mainを非実行関数へ改名するだけ。既受入fixtureは呼び出さない。
    first=(ROOT/'tools/mgba_pr16_research_save_impact.c').read_text()
    second=(ROOT/'tools/mgba_pr16_research_lifecycle.c').read_text()
    token='int main(int argc,char**argv){'
    marker='#define main research_impact_legacy_main\n#include "mgba_pr16_research_save_impact.c"\n#undef main\n'
    need(first.count(token)==1 and second.count(marker)==1 and second.count(token)==1,'one inherited declaration/include')
    text=first.replace(token,'int accepted_save_impact_main(int argc,char**argv){')+'\n'+second.replace(marker,'').replace(token,'int accepted_lifecycle_main(int argc,char**argv){')
    text=text.replace('#include "../overlays/research_economy_v1/research_economy_v1.h"','#include "overlays/research_economy_v1/research_economy_v1.h"')
    t=trace();header='#define NG_ROM "'+CANDIDATE['sha256']+'"\n#define NG_ERASED "'+ERASED['sha256']+'"\n#define NG_TRACE_HASH "'+t['trace_sha256']+'"\n#define NG_TRACE_FRAMES '+str(t['trace_frames'])+'U\n'
    return (header+text+'\n'+(ROOT/C).read_text()).encode()


def result():
    return {'status':'PASS','scope':SCOPE,'case':CASE,'candidate_sha256':CANDIDATE['sha256'],'fresh_cores':3,'manual_saves':1,'automatic_saves':0,'host_write_barriers':7,'guarded_host_writes':0,'fixture_calls':0,'ram_fixture_writes':0,'register_fixture_writes':0,'text_speed_writes':0,'normal_new_game_accepted':True,'starter_acquisition_accepted':False,'research_natural_supply_accepted':False,'warnings_errors':0}


def field(stage):
    return {'field_event':stage,'map_group':4,'map_num':0,'x':10,'y':2,'live_x':17,'live_y':9,'facing':3,'player_active':True,'script_locked':False,'text_speed':0}


def validate(raw):
    need(0<len(raw)<=22000,'bounded observations')
    rows=[closed.load(line) for line in raw.decode().splitlines()]
    need(len(rows)==18,'four complete stages and boot/result')
    exact(rows[0],dict(trace(),new_game_boot='erased-flash-input-only',settle_frames=600,initial_save_sha256=ERASED['sha256']),'blank input/normal trace')
    exact(rows[-1],result(),'scoped new-game result')
    first=None;first_flash=None;events=[];ledgers=[];flashes=[]
    for i,stage in enumerate(STAGES):
        pos,ev,le,flash=rows[1+4*i:5+4*i]
        exact(pos,field(stage),'normal position '+stage)
        need(set(ev)==old.lc.EVENT_FIELDS and ev['event']==stage,'closed ordered inventory stage')
        for k,v in {'counter':int(i>0),'party_count':0,'item_quantity':0}.items():need(type(ev[k]) is int and ev[k]==v,'first-save '+k)
        for k in ('inventory_sha256','other_inventory_sha256','party_sha256'):
            closed.digest(ev[k])
            if first:need(ev[k]==first[k],'unchanged '+k)
        need(ev['inventory_sha256']==ev['other_inventory_sha256'],'item4 remains absent')
        need(isinstance(ev['owner'],str) and re.fullmatch('[0-9a-f]{128}',ev['owner']),'complete owner')
        owner=bytes.fromhex(ev['owner']);expected=initial_ledger(owner[7]);need(owner==expected[0x73f:0x77f],'exact source-default owner')
        unrelated=bytearray(expected);unrelated[4:6]=bytes(2);unrelated[8:12]=bytes(4);unrelated[0x73f:0x77f]=bytes(64)
        exact(le,{'ledger_event':stage,'version':2,'size':2048,'checksum_valid':True,'ledger_sha256':identity(expected)['sha256'],'unrelated_ledger_sha256':identity(unrelated)['sha256'],'migration_dirty':0,'recovery_blocked':0},'all2048 source-default ledger '+stage)
        need(set(flash)=={'flash_event','size','sha256'} and flash['flash_event']==stage and type(flash['size']) is int and flash['size']==131072,'complete Flash stage');closed.digest(flash['sha256'])
        if not i:need(flash['sha256']==ERASED['sha256'],'no save during intro')
        elif i==1:need(flash['sha256']!=ERASED['sha256'],'actual first Save');first_flash=flash['sha256']
        else:need(flash['sha256']==first_flash,'all Flash bytes retained without Continue save')
        first=first or ev;events.append(ev);ledgers.append(le);flashes.append(flash)
    return dict(rows[-1],boot=rows[0],observations=events,ledger_observations=ledgers,flash_observations=flashes,stdout=identity(raw))
