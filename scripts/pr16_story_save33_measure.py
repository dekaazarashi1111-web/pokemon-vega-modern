#!/usr/bin/env python3
"""Save32より先の新しい通常入力だけ。最初の新戦闘または解禁後teleportでSave33を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save32_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='546c5e02e408bdf07a678580912df38e9159b16e'
OUT=ROOT/'.local/pr16-story-save33';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save33_measure.py','tests/test_pr16_story_save33_measure.py','.github/workflows/pr16-story-save33.yml'}
PP=[1,14,0,0]
PREP='content/modernization/pr16_story_save32_preparation.json'
ROUTE=[[21, 19], [22, 19], [23, 19], [23, 18], [23, 17], [23, 16], [23, 15], [23, 14], [23, 13], [22, 13], [21, 13], [21, 14], [20, 14], [19, 14]]
JUMPS=set()
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'Save32/同一candidateだけ')
    prep=json.loads((ROOT/PREP).read_bytes())
    need(prep['source_head']=='e8b5e13b4775188258420edbb5754ed919823458' and prep['run_id']==37121423789 and prep['inherited_cells']==164 and prep['new_cells']==756,'固定済未読地形の原本を再利用')
    cells={tuple(t['xy']):t for t in prep['allcells']}
    need(len(cells)==920 and len(prep['new_terrain'])==756,'全地形の保存原本')
    terrain=[cells[tuple(xy)]for xy in ROUTE]
    need(all(t['collision']==0 for t in terrain),'通常経路だけ')
    need(cells[23,14]['behavior']==42 and cells[23,14]['elevation']==0,'東岩階段だけ')
    need(terrain[0]['elevation']==3 and terrain[-1]['elevation']==4,'下層から上層')
    bank,_=a.parent.sectors.bank(seed,0,32,a.parent.sectors.LAYOUT)
    flags,variables=a.parent.sectors.legacy_state(seed,bank)
    ext=a.parent.s61e_record(seed[bank[13]+0x7d0:bank[13]+0xde6])
    need(bool(ext[(4367-2304)//8]&(1<<((4367-2304)%8))) and variables[0x71]==7 and variables[0]==0,'解禁後teleport分岐の開始状態')
    return dict(status='STATIC_SAVE32_EAST_STAIRS_ROUTE',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,terrain=terrain,expected_teleport=[8,10],native_teleport_accepted=False)

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save32実PPの範囲')
    for slot in (1,0):
        if used[slot]<PP[slot]:return slot
    raise ValueError('実PP枯渇。host回復しない')
def direction(before,after):
    delta=tuple(b-a for a,b in zip(before,after))
    if delta==(0,2):
        need((tuple(before),tuple(after))in JUMPS,'固定南段差1辺だけ');return 128
    need(delta in ((0,1),(0,-1),(1,0),(-1,0)),'通常は1tile隣接')
    return {(0,1):128,(0,-1):64,(1,0):16,(-1,0):32}[delta]

def start(o):
    m.idle(o,32);need(o['xy']==ROUTE[0] and o['facing']==4 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'Save32唯一の親')
def battle(s):
    first=len(s.observations)-1;used=[0]*4;decisions=[]
    need(s.last['callback2']==m.BATTLE,'新battle開始を観測してからだけ')
    for _ in range(120):
        o=s.last
        need(o['map']==[1,73] and o['save_counter']==32 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');m.idle(o,32)
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
    start(s.last);route=[ROUTE[0]];ledges=[]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before,'直前の実座標')
        jump=(tuple(before),tuple(target))in JUMPS
        middle=[before[0],before[1]+1]if jump else None
        for _ in range(3):
            o=s.step((direction(before,target),8),(0,48))
            allowed=[before,target]+([middle]if jump else [])+([[8,10]]if target==[19,14]else [])
            need(o['map']==[1,73] and o['xy']in allowed,'新しい固定辺/解禁後warpだけ')
            if jump and o['xy']==middle:
                for _ in range(3):
                    o=s.step((0,40));need(o['map']==[1,73] and o['xy']in (middle,target),'南段差の有限完了待ち')
                    if o['xy']==target:break
                need(o['xy']==target,'段差途中なら停止')
            if target==[19,14] and o['xy']in (target,[8,10]):
                for _ in range(12):
                    if o['callback2']==m.FIELD and o['lock']==0 and o['xy']==[8,10]:
                        m.idle(o,32);route.extend([target,[8,10]])
                        return route,None,dict(trigger=[19,14],destination=[8,10],observation=len(s.observations)-1)
                    need(o['callback2']!=m.BATTLE,'warp途中の未知battleは停止')
                    o=s.step((0,60));need(o['map']==[1,73] and o['xy']in (target,[8,10]),'解禁後warpの有限待ち')
                raise ValueError('解禁後teleportの有限上限')
            if o['lock'] or o['callback2']!=m.FIELD:
                for _ in range(6):
                    if o['callback2']==m.BATTLE:break
                    o=s.step((1,2),(0,180))
                return route,battle(s),None
            m.idle(o,32)
            if o['xy']==target:
                route.append(target);break
        else:raise ValueError('同方向3回停止。保存原本へ無条件再走しない')
    raise ValueError('未観測teleportを成功にしない')

def save(s):
    m.idle(s.last,32);target=s.last['xy']
    s.step((8,2),(0,60));s.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(8):
        o=s.step((0,120));need(o['xy']==target and o['map']==[1,73] and o['save_counter'] in (32,33),'新Save33だけ')
        if o['save_counter']==33 and o['callback2']==m.FIELD and o['lock']==0:break
    m.idle(o,33);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

def restore():
    ASSETS.mkdir()
    # ROM/runnerは既存Save24 artifact内で読取り。既存input Save24は展開しない。
    _,z=m.a.d.m.transport.archive(m.a.ARTIFACT,m.a.RUN,m.a.ARCHIVE,m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        for n,b in manifest.items():need(identity(z.read(n))==b,'親全member '+n)
        for n,b in [('candidate.gba',m.a.d.m.shared.plan.CANDIDATE),('runner',m.a.d.m.prior.parent.RUNNER)]:
            raw=z.read(n);need(identity(raw)==b,'固定既存 '+n);(ASSETS/n).write_bytes(raw);(ASSETS/n).chmod(0o555 if n=='runner'else 0o444)
    _,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    with z:
        bindings=json.loads(z.read('manifest.json'))
        need(len(bindings)==79 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save32原本79member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save32 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save32開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save32-record-terminal.json',inherited.terminal(37122527387,'8d97e9de625f4b28b9c1b6bc7a30e5582812eba6',111201313311,['success']*11))
        need(state['story_save32']['story_fast_save']==a.OUTPUT,'正式Save32親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,teleport=progress(s);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        m.idle(c.last,33);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=m.a.d.m.shared.trace(ART/'progress',a.OUTPUT);pb=m.a.d.m.shared.trace(ART/'continue',identity(saved))
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE33_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleport,story_event=None,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=False,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save32'])
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



