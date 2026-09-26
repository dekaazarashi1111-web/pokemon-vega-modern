#!/usr/bin/env python3
"""実メニュー再解決を継承し、毒付き低HP相手へのSeedだけを修復。"""
from pathlib import Path
import json
import os
import struct
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_drain.py'
TEST='tests/test_pr16_circus_drain.py'
HEADER='tools/mgba_pr16_circus_drain.h'
WORKFLOW='.github/workflows/pr16-circus-drain.yml'
POLICY='toxic-drain-v1'
TASK='USER-20260919-CIRCUS-TOXIC-DRAIN'
FILES=(SELF,TEST,HEADER,WORKFLOW,'scripts/pr16_circus_matchup.py','tools/mgba_pr16_circus_matchup.h',
    'tools/mgba_pr16_circus_menu_identity.h','scripts/pr16_circus_menu_recovery.py')
OLD_RUN=35420622910


def need(value,message):
    if not value:raise ValueError(message)


def adapt(text):
    old='slot=mt_move_slot(c);'
    need(text.count(old)==1 and text.count('static unsigned mt_move_slot(struct mCore *c);')==1
         and 'cd_move_slot' not in text,'drain selector anchor changed')
    return text.replace('mt_move_slot','cd_move_slot')


def recovery_diagnosis(raw):
    rows=[json.loads(line[16:]) for line in raw.splitlines() if line.startswith(b'CIRCUS_RECOVERY ')]
    need(len(rows)==21 and [r['sequence'] for r in rows]==list(range(1,22)),'recovery trace sequence differs')
    need(all(r['owner']=='00'*64 for r in rows[:20]),'owner was already loaded during standard recovery')
    need([r['save_counter'] for r in rows[10:16]]==[2,2,3,3,4,4],'two recovery Saves were not observed')
    last=rows[-1];owner=bytearray.fromhex(last['owner']);crc=struct.unpack_from('<I',owner,12)[0];owner[12:16]=bytes(4)
    need(zlib.crc32(owner)&0xffffffff==crc and struct.unpack_from('<II',owner,16)==(1,0)
         and owner[24:40]==bytes(16),'terminal owner is not a new empty CRC-valid record')
    need(last['frame_boundary']==25805 and last['snapshot']==last['marker']==last['pending']==0
         and last['count']==1 and last['save_counter']==4,'terminal recovery differs')
    return dict(original_run=OLD_RUN,original_conclusion='failure',observations=len(rows),
        first_loaded_owner_frame=25805,empty_owner_during_recovery_saves=True,
        standard_save_counter_chain=[2,3,4],terminal_current=0,terminal_best=0,
        terminal_generation=1,terminal_session=0,accepted=False,independent_native_replays=0,
        next_ja='前段load内のFactory復旧が標準Saveを2回行う間、Circus owner64が未ロード。後段field hookでは初期化済み。save/load呼出順で既存ownerを保持・中断確定する修復が必要。')


def configure():
    import pr16_circus_matchup as m
    m.SELF=SELF;m.TEST=TEST;m.WORKFLOW=WORKFLOW;m.FIXTURE=TEST;m.POLICY=POLICY;m.TASK=TASK;m.HEADER=HEADER
    return m,m.parent().configure()


def prepare():
    m,b=configure();p=m.parent();r=b.rec
    old=json.loads((ROOT/b.REPORT).read_bytes())
    need(old['recording_run']==OLD_RUN and old['input_policy_id']=='menu-identity-v1','drain predecessor changed')
    original=b.checkpoint
    def checkpoint(value,stop,phase,extra):
        prefix=ROOT/('evidence/pr16_circus_three_win/'+str(OLD_RUN))
        stderr=(prefix/'circus-streak-batch-save.stderr').read_bytes()
        need(b'CIRCUS_MENU frame=46308 requested=0 resolved=1' in stderr
             and b'CIRCUS_MENU frame=55368 requested=0 resolved=2' in stderr,'menu identity repair not observed')
        value['classification']='CIRCUS_TOXIC_DRAIN_INPUT_PENDING'
        value['source_change_review_ja']='ROM/乱数/チーム/通常交代/勝敗判定は不変。第3戦で毒が実際にある低HP相手にSeedを選んだ場合のみ、PPのあるGiga Drainへ置換。'
        value['diagnosis']=dict(run_id=OLD_RUN,first_intervention_frame=48229,
            previous_move=73,replacement_move=202,enemy_hp=81,enemy_maxhp=171,
            reason_ja='敵は毒で減少中。Seedでターンを延ばす間に草が混乱と毒で163→63となり、最後の水ではProtectと毒で倒れた。追加の状態技ではなく攻撃で早期決着を試す。')
        path='evidence/pr16_circus_interruption/'+str(OLD_RUN)+'/circus-interrupt-second-battle.stderr'
        value['interruption_diagnosis']=recovery_diagnosis((ROOT/path).read_bytes())
        value['interruption_diagnosis']['source']=dict(path=path,**b.identity((ROOT/path).read_bytes()))
        original(value,'メニュー表示後の個体再解決は実3回成功。実3勝は未完。毒付き低HP相手への余分なSeedだけをGiga Drainへ修正。中断のowner消失原本は再実行せず、ロード前段の2回Saveを次の修復点として記録。',phase,[*extra,*FILES])
    b.checkpoint=checkpoint;p.prepare()


def native():
    import pr16_streak_native as n
    m,_=configure();original=m.adapt_policy
    m.adapt_policy=lambda text:adapt(original(text));n.EXTRA=n.EXTRA|set(FILES)
    try:m.native()
    finally:m.adapt_policy=original


def finish():
    m,b=configure();original=b.checkpoint
    b.checkpoint=lambda value,stop,phase,extra:original(value,stop,phase,[*extra,*FILES])
    m.finish()


def pack():
    m,b=configure();m.pack()
    target=ROOT/'.local/pr16-three-win-evidence';path=target/'members.json';members=json.loads(path.read_bytes())
    for name in FILES:
        p=target/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());members['source/'+name]=b.identity(p.read_bytes())
    path.write_bytes(b.stable(members))


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action in {'pipeline','reconstruct'}:getattr(configure()[1],action)()
    elif action in {'prepare','native','finish','pack'}:globals()[action]()
    else:raise SystemExit('unknown command')
