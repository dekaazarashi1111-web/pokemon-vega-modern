#!/usr/bin/env python3
"""Save25より先の新しい通常入力だけ。最初の新戦闘/teleportでSave26を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save25_accept as a
import pr16_story_save25_record as record25
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
m=a.m;h=m.h
BASE='60ae5072084d01c2da52ee7620d6108e4f9d401a'
OUT=ROOT/'.local/pr16-story-save26';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save26_measure.py','tests/test_pr16_story_save26_measure.py','.github/workflows/pr16-story-save26.yml'}
PP=[1,14,2,5]
ROUTE=[[31,y]for y in range(7,13)]+[[x,12]for x in range(32,35)]+[[34,y]for y in range(13,16)]+[[x,15]for x in range(33,22,-1)]+[[23,14],[23,13]]+[[x,13]for x in range(22,18,-1)]+[[19,14]]
def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save25実PPの範囲')
    for slot in (2,3,1,0):
        if used[slot]<PP[slot]:return slot
    raise ValueError('実PP枯渇。host回復しない')
def direction(before,after):
    delta=tuple(b-a for a,b in zip(before,after));need(delta in ((0,1),(0,-1),(1,0),(-1,0)),'1tile隣接のみ')
    return {(0,1):128,(0,-1):64,(1,0):16,(-1,0):32}[delta]
def start(o):
    m.idle(o,25);need(o['xy']==ROUTE[0] and o['facing']==1 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'Save25唯一の親')
def battle(s):
    first=len(s.observations)-1;used=[0]*4;decisions=[]
    need(s.last['callback2']==m.BATTLE,'新battle開始を観測してからだけ')
    for _ in range(120):
        o=s.last
        need(o['map']==[1,73] and o['save_counter']==25 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');m.idle(o,25)
            return dict(start=first,finish=len(s.observations)-1,trainer=bool(o['battle_flags']&8),outcome=1,used=used,decisions=decisions)
        need(o['battle_outcome'] in (0,1),'敗北等は停止')
        if o['callback2']==m.BATTLE:
            kind,cursor=m.classify(m.screen(s))
            if kind=='moves':
                slot=select(used)
                for key in m.navigation(cursor,slot):s.step((key,1),(0,12))
                need(m.classify(m.screen(s))==('moves',slot),'実技cursor')
                decisions.append(dict(observation=len(s.observations)-1,move_slot=slot))
                s.step((1,2),(0,240));used[slot]+=1;continue
            if kind=='shift':
                decisions.append(dict(observation=len(s.observations)-1,keep_current=True));s.step((2,2),(0,180));continue
        need(o['callback2'] in (m.FIELD,m.BATTLE),'未知callbackは停止')
        s.step((1,2),(0,180))
    raise ValueError('有限戦闘上限。無条件再走禁止')
def progress(s):
    start(s.last);route=[ROUTE[0]]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before,'直前の実座標')
        for _ in range(3):
            o=s.step((direction(before,target),8),(0,32))
            if target==[19,14] and o['xy']in ([27,7],[8,10]):
                for _ in range(10):
                    if o['callback2']==m.FIELD and o['lock']==0:break
                    o=s.step((0,120))
                m.idle(o,25);return route,None,dict(trigger=target,destination=o['xy'],observation=len(s.observations)-1)
            need(o['map']==[1,73] and o['xy']in (before,target),'指定1tileの実座標')
            if o['lock'] or o['callback2']!=m.FIELD:
                for _ in range(6):
                    if o['callback2']==m.BATTLE:break
                    o=s.step((1,2),(0,180))
                return route,battle(s),None
            m.idle(o,25)
            if o['xy']==target:route.append(target);break
        else:raise ValueError('同方向3回停止。静的候補を盲反復しない')
    return route,None,None

def save(s):
    m.idle(s.last,25);target=s.last['xy']
    s.step((8,2),(0,60));s.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(8):
        o=s.step((0,120));need(o['xy']==target and o['map']==[1,73] and o['save_counter'] in (25,26),'新Save26だけ')
        if o['save_counter']==26 and o['callback2']==m.FIELD and o['lock']==0:break
    m.idle(o,26);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

def restore():
    ASSETS.mkdir()
    # ROM/runnerは既存Save24 artifact内で読取り。既存input Save24は展開しない。
    _,z=m.a.d.m.transport.archive(m.a.ARTIFACT,m.a.RUN,m.a.ARCHIVE,m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        for n,b in manifest.items():need(identity(z.read(n))==b,'親全member '+n)
        for n,b in [('candidate.gba',m.a.d.m.shared.plan.CANDIDATE),('runner',m.a.d.m.prior.parent.RUNNER)]:
            raw=z.read(n);need(identity(raw)==b,'固定既存 '+n);(ASSETS/n).write_bytes(raw);(ASSETS/n).chmod(0o555 if n=='runner'else 0o444)
    _,z=m.a.d.m.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    with z:
        bindings=json.loads(z.read('manifest.json'))
        need(len(bindings)==55 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save25原本')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save25 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save25開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
    runtime=OUT/'runtime';runtime.mkdir()
    _,z=m.a.d.m.transport.archive(11263910704,37094769974,dict(size=102440293,sha256='661ad2b88d25607d81ac46141f85cd42f2fcf88db4f306e1601257f3277e099f'),'1c7b23e4a6a5708cebdb2713c97f553b47ac616b')
    with z:
        bindings=json.loads(z.read('runtime/manifest.json'));need(len(bindings)>5,'runtime全member一覧')
        for n,b in bindings.items():
            name=m.runtime_member('runtime/'+n);raw=z.read('runtime/'+name);need(identity(raw)==b,'保持runtime全byte '+name)
            p=runtime/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    need(identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'同一mGBA')
    return runtime

def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'新区間初回のみ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        terminal=record25.inherited.terminal(37113873113,'dbb50b3c13ce33d7a8576d9a24178af9e056a49a',111176793864,['success']*10)
        write(ART/'save25-record-terminal.json',terminal)
        prep=h.d.read(ROOT/'content/modernization/pr16_story_save25_preparation.json')
        need(prep['route'][3:]==ROUTE,'33点静的候補再利用。実通行とは別')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,teleport=progress(s);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        m.idle(c.last,26);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=m.a.d.m.shared.trace(ART/'progress',a.OUTPUT);pb=m.a.d.m.shared.trace(ART/'continue',identity(saved))
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE26_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),route=route,battle=episode,teleport=teleport,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=False,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save25'])
        write(ART/'measurement.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as e:
        for s in sessions:
            if not s.closed and s.process.poll() is None:
                try:s.quit()
                except Exception:s.process.terminate()
        write(ART/'failure.json',dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',type=type(e).__name__,message=str(e),native_processes=len(sessions),source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID'])))
        raise
    finally:
        for p in ART.rglob('*.srm'):
            if identity(p.read_bytes())==a.OUTPUT:p.unlink()
        need(all(p.suffix in {'.srm','.ppm','.txt','.json'}for p in ART.rglob('*')if p.is_file()),'新公開artifactの拡張子だけ')
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes())for p in sorted(ART.rglob('*'))if p.is_file()and p.name!='manifest.json'})
if __name__=='__main__':main()
