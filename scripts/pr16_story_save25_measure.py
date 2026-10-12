#!/usr/bin/env python3
"""Save24から次の戦闘/通常保存境界。既存ROM/runtimeを再配布しない。"""
from __future__ import annotations
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save24_accept as a
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
h=a.d.m.h
BASE='25049912ce5828ba55f9cda5a60c494ae1cabb45'
OUT=ROOT/'.local/pr16-story-save25'
ART=OUT/'artifact'
ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save25_measure.py','tests/test_pr16_story_save25_runtime.py','.github/workflows/pr16-story-save25.yml'}
FIELD,BATTLE=a.d.m.prior.parent.FIELD,a.d.m.prior.parent.BATTLE
BOXES=[[8,124,15,133],[80,124,87,133],[8,140,15,149],[80,140,87,149]]
ARROW='22ab531022beb9a9b67dd304093319ca979fb20a328514d93cb777cd5d943571'
LEFT='b9550e4b4c7c09ca38da37fa483f58b07c52a2d340866e11b81917a6e6545f21'
RIGHT='05a6aeca958d0f835b489535aa4e52242ce194d855e527f3ad454ccba06ae8ee'
SHIFT='900b3160f2258bba6ac4aaf45e648bb4aa74c8ab851ed9b34b953b2404bad6e1'
def pixels(raw):
    parts=raw.split(b'\n',3)
    need(parts[:3]==[b'P6',b'240 160',b'255'] and len(parts[3])==115200,'厳密な全PPM画面')
    return parts[3]
def crop(raw,box):
    data=pixels(raw);x0,y0,x1,y1=box
    need(0<=x0<x1<=240 and 0<=y0<y1<=160,'範囲付き矩形')
    return b''.join(data[(y*240+x0)*3:(y*240+x1)*3] for y in range(y0,y1))
def digest(raw,box):return hashlib.sha256(crop(raw,box)).hexdigest()
def classify(raw):
    if digest(raw,[16,120,77,152])==LEFT and digest(raw,[88,120,152,152])==RIGHT:
        choices=[i for i,box in enumerate(BOXES) if digest(raw,box)==ARROW]
        need(len(choices)==1,'技UI選択cursor1つ')
        return 'moves',choices[0]
    if digest(raw,[200,74,231,105])==SHIFT:return 'shift',None
    return 'other',None
def navigation(current,target):
    need(type(current) is int and type(target) is int and 0<=current<4 and 0<=target<4,'4技cursor')
    keys=[]
    if current//2!=target//2:keys.append(128 if target//2 else 64)
    if current%2!=target%2:keys.append(16 if target%2 else 32)
    return keys
def idle(o,counter=24):
    need(o['map']==[1,73] and o['callback2']==FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and
         o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']] and o['battle_outcome'] in (0,1),
         '洞窟の操作可能field。残留field boolを勝利と混同しない')
def screen(s):return (s.folder/f"screen-{len(s.observations)-1:04d}.ppm").read_bytes()
def battle(s):
    start=len(s.observations)-1;used=[0,0,0,0];decisions=[]
    for _ in range(120):
        o=s.last
        need(o['map']==[1,73] and o['save_counter']==24 and o['rp']==0 and o['party_count']==4,'戦闘scope')
        if o['callback2']==FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'勝利1のみ');idle(o)
            return dict(start=start,finish=len(s.observations)-1,trainer=bool(o['battle_flags']&8),outcome=1,used=used,decisions=decisions)
        need(o['battle_outcome'] in (0,1),'敗北等は停止')
        if o['callback2']==BATTLE:
            kind,cursor=classify(screen(s))
            if kind=='moves':
                target=2 if used[2]<5 else 3 if used[3]<5 else 1
                need(used[target]<[1,14,5,5][target],'Save24原本PP範囲')
                for key in navigation(cursor,target):s.step((key,1),(0,12))
                need(classify(screen(s))==('moves',target),'実cursor移動後照合')
                decisions.append(dict(observation=len(s.observations)-1,move_slot=target))
                s.step((1,2),(0,240));used[target]+=1;continue
            if kind=='shift':
                decisions.append(dict(observation=len(s.observations)-1,keep_current=True))
                s.step((2,2),(0,180));continue
        need(o['callback2'] in (FIELD,BATTLE),'未知party/menu callbackは停止')
        s.step((1,2),(0,180))
    raise ValueError('有限観測上限。自動再走禁止')
def progress(s):
    idle(s.last);need(s.last['xy']==[31,4] and s.last['party_sha256']==a.d.m.prior.parent.PARTY,'唯一のSave24親')
    route=[]
    for y in range(5,13):
        before=[31,y-1];target=[31,y]
        for _ in range(3):
            o=s.step((128,8),(0,32))
            need(o['map']==[1,73] and o['xy'] in (before,target),'東通路1tileだけ')
            if o['lock'] or o['callback2']!=FIELD:
                for _ in range(3):
                    if o['callback2']==BATTLE:break
                    o=s.step((1,2),(0,180))
                return route,battle(s)
            idle(o)
            if o['xy']==target:route.append(target);break
        else:raise ValueError('同方向3回停止。盲反復禁止')
    return route,None
def save(s):
    idle(s.last);target=s.last['xy']
    s.step((8,2),(0,60));s.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(8):
        o=s.step((0,120))
        need(o['xy']==target and o['map']==[1,73] and o['save_counter'] in (24,25),'新Save25だけ')
        if o['save_counter']==25 and o['callback2']==FIELD and o['lock']==0:break
    idle(o,25);need(o['flash_sha256']!=a.FLASH,'通常保存完了')
    return o
def runtime_member(name):
    need(type(name) is str and name.startswith('runtime/'),'固定runtime prefix')
    name=name[len('runtime/'):]
    need(not name.startswith('/') and '..' not in name.split('/') and chr(92) not in name,'安全なmember path')
    need(name=='ld.so' or name.startswith('lib/'),'runtime実ファイルだけ')
    return name
def restore():
    ASSETS.mkdir()
    _,z=a.d.m.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        for n,b in manifest.items():need(identity(z.read(n))==b,'親全member '+n)
        for n,dest,b in [('story-fast.srm','input.srm',a.OUTPUT),('candidate.gba','candidate.gba',a.d.m.shared.plan.CANDIDATE),('runner','runner',a.d.m.prior.parent.RUNNER)]:
            raw=z.read(n);need(identity(raw)==b,'固定親 '+n);(ASSETS/dest).write_bytes(raw)
            (ASSETS/dest).chmod(0o555 if n=='runner' else 0o444)
    runtime=OUT/'runtime';runtime.mkdir()
    _,z=a.d.m.transport.archive(11263910704,37094769974,dict(size=102440293,sha256='661ad2b88d25607d81ac46141f85cd42f2fcf88db4f306e1601257f3277e099f'),'1c7b23e4a6a5708cebdb2713c97f553b47ac616b')
    with z:
        bindings=json.loads(z.read('runtime/manifest.json'))
        need(len(bindings)>5,'保持されたruntime全member一覧')
        for n,b in bindings.items():
            name=runtime_member('runtime/'+n);raw=z.read('runtime/'+name)
            need(identity(raw)==b,'runtime全member byte '+name)
            p=runtime/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    need(identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'固定mGBA')
    return runtime
def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'初回新入力のみ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode=progress(s);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,25);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=a.d.m.shared.trace(ART/'progress',a.OUTPUT);pb=a.d.m.shared.trace(ART/'continue',identity(saved))
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_EAST_FIRST_BOUNDARY_SAVE25_AWAITING_RECORD',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
                    input_save=a.OUTPUT,output_save=identity(saved),route=route,battle=episode,final=final,continued=c.last,
                    progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,
                    accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
                    teleport_accepted=False,cave_crossing_complete=False,full_story_accepted=False,release_ready=False,
                    artifact_excludes=['existing ROM','runner','runtime','input Save24'])
        write(ART/'measurement.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as e:
        for s in sessions:
            if not s.closed and s.process.poll() is None:
                try:s.quit()
                except Exception:s.process.terminate()
        write(ART/'failure.json',dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',type=type(e).__name__,message=str(e),native_processes=len(sessions),
                                    source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID'])))
        raise
    finally:
        # 公開artifactは新しい保存物と画面/textのみ。失敗で不変の旧Save24は再配布しない。
        for p in ART.rglob('*.srm'):
            if identity(p.read_bytes())==a.OUTPUT:p.unlink()
        allowed={'.srm','.ppm','.txt','.json'}
        need(all(p.suffix in allowed for p in ART.rglob('*') if p.is_file()),'公開artifact拡張子allowlist')
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes()) for p in sorted(ART.rglob('*')) if p.is_file() and p.name!='manifest.json'})
if __name__=='__main__':main()
