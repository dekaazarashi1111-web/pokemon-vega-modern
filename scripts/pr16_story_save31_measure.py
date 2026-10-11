#!/usr/bin/env python3
"""Save30より先の新しい通常入力だけ。最初の新戦闘/南story座標でSave31を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save30_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='294191a3e8c1d83b83ee4121d53215492c1637b4'
OUT=ROOT/'.local/pr16-story-save31';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save31_measure.py','tests/test_pr16_story_save31_measure.py','.github/workflows/pr16-story-save31.yml'}
PP=[1,14,0,4]
ROUTE=[[13,6],[13,7],[14,7],[14,8],[14,10],[14,11],[14,12],[14,14]]
JUMPS={((14,8),(14,10)),((14,12),(14,14))}
def owner_operands(values):
    need(len(values)==8 and all(type(v)is int for v in values),'8つの実operand')
    op0,op1,flag,op2,var,value,release,end=values
    need((op1,flag,op2,var,value,end)==(0x29,4367,0x16,0x4071,7,2),'setflag4367/setvar4071=7/endの独立byte')
    return dict(first_opcode=op0,setflag_opcode=op1,flag=flag,setvar_opcode=op2,variable=var,value=value,release_opcode=release,end_opcode=end)
def inspect(raw,seed):
    from pr16_story_after_maori import unpack
    import pr16_story_cave_route as owner
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'Save30/同一candidateだけ')
    checkpoint=h.d.read(ROOT/'content/modernization/pr16_story_cave_route_checkpoint.json')['result']
    rows=owner.coords(raw,137444032)
    need(rows==checkpoint['coordinate_events'],'保存済みcoord原本を再利用')
    roots=rows[3:9]
    need(all(r['script']==0x08214656 and r['trigger_var']==0x4071 and r['trigger_value']==6 and r['elevation']==3 for r in roots),'西側story owner')
    operands=owner_operands(unpack(raw,0x08214656,'BBHBHHBB'))
    bank,_=a.parent.sectors.bank(seed,0,30,a.parent.sectors.LAYOUT)
    flags,variables=a.parent.sectors.legacy_state(seed,bank)
    ext=a.parent.s61e_record(seed[bank[13]+0x7d0:bank[13]+0xde6])
    need(not(ext[(4367-2304)//8]&(1<<((4367-2304)%8))) and variables[0x71]==6,'未解禁開始点')
    width,height,_,blocks,primary,secondary=unpack(raw,137190172,'IIIIII')
    need((width,height)==(40,23),'固定map寸法')
    cells=unpack(raw,blocks,'H'*(width*height));terrain=[]
    for x,y in ROUTE:
        cell=cells[y*width+x];tile=cell&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
        behavior=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I')[0]&511
        terrain.append(dict(xy=[x,y],elevation=cell>>12,collision=(cell>>10)&3,behavior=behavior))
    need(all(t['collision']==0 and t['elevation']==3 for t in terrain),'下層の通常経路だけ')
    ledges=[]
    for before,after in sorted(JUMPS):
        x,y=before[0],before[1]+1;cell=cells[y*width+x];tile=cell&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
        behavior=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I')[0]&511
        need(((cell>>10)&3,behavior)==(1,59),'保存済み南段差候補behavior59')
        ledges.append(dict(xy=[x,y],collision=1,behavior=behavior,native_traversal_accepted=False))
    need([r['xy']for r in rows if r['xy']in ROUTE]==[[14,14]],'終端だけに正規story owner')
    nearby=[]
    for y in range(4,17):
        row=[]
        for x in range(8,20):
            cell=cells[y*width+x];tile=cell&1023;base,index=(primary,tile)if tile<0x280 else(secondary,tile-0x280)
            behavior=unpack(raw,unpack(raw,base+20,'I')[0]+index*4,'I')[0]&511
            row.append(dict(xy=[x,y],elevation=cell>>12,collision=(cell>>10)&3,behavior=behavior))
        nearby.append(row)
    return dict(ledges=ledges,lower_corridor_terrain=nearby,status='NEW_SOUTH_OWNER_PREFLIGHT' ,owner_operands=operands,route=ROUTE,terrain=terrain,story_owner=dict(root=0x08214656,coords=[r['xy']for r in roots],flag=4367,variable=0x4071,value=7),runtime_story_unlock_accepted=False)

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save30実PPの範囲')
    for slot in (3,1,0):
        if used[slot]<PP[slot]:return slot
    raise ValueError('実PP枯渇。host回復しない')
def direction(before,after):
    delta=tuple(b-a for a,b in zip(before,after))
    if delta==(0,2):
        need((tuple(before),tuple(after))in JUMPS,'固定南段差2辺だけ');return 128
    need(delta in ((0,1),(0,-1),(1,0),(-1,0)),'通常は1tile隣接')
    return {(0,1):128,(0,-1):64,(1,0):16,(-1,0):32}[delta]

def start(o):
    m.idle(o,30);need(o['xy']==ROUTE[0] and o['facing']==1 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'Save30唯一の親')
def battle(s):
    first=len(s.observations)-1;used=[0]*4;decisions=[]
    need(s.last['callback2']==m.BATTLE,'新battle開始を観測してからだけ')
    for _ in range(120):
        o=s.last
        need(o['map']==[1,73] and o['save_counter']==30 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');m.idle(o,30)
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
            need(o['map']==[1,73] and o['xy']in ([before,middle,target]if jump else [before,target]),'新しい固定辺内だけ')
            if jump and o['xy']==middle:
                for _ in range(3):
                    o=s.step((0,40))
                    need(o['map']==[1,73] and o['xy']in (middle,target),'南段差の有限完了待ち')
                    if o['xy']==target:break
                need(o['xy']==target,'段差途中なら停止')
            if target==[14,14] and o['xy']==target:
                for _ in range(5):
                    if o['callback2']==m.FIELD and o['lock']==0:break
                    if o['callback2']==m.BATTLE:break
                    o=s.step((0,60))
            if o['lock'] or o['callback2']!=m.FIELD:
                for _ in range(6):
                    if o['callback2']==m.BATTLE:break
                    o=s.step((1,2),(0,180))
                return route,battle(s),dict(ledges=ledges,owner_candidate_reached=False)
            m.idle(o,30)
            if o['xy']==target:
                route.append(target)
                if jump:ledges.append(dict(before=before,after=target,observation=len(s.observations)-1))
                break
        else:raise ValueError('同方向3回停止。保存原本へ無条件再走しない')
    s.step((0,120));m.idle(s.last,30)
    return route,None,dict(ledges=ledges,owner_candidate_reached=True,owner=0x08214656,runtime_story_unlock_accepted=False)

def save(s):
    m.idle(s.last,30);target=s.last['xy']
    s.step((8,2),(0,60));s.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(8):
        o=s.step((0,120));need(o['xy']==target and o['map']==[1,73] and o['save_counter'] in (30,31),'新Save31だけ')
        if o['save_counter']==31 and o['callback2']==m.FIELD and o['lock']==0:break
    m.idle(o,31);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==33 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save30原本')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save30 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save30開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save30-record-terminal.json',inherited.terminal(37120155157,'34f54573124705f69963d7f6345f9ba7a472838e',111194534482,['success']*11))
        need(state['story_save30']['story_fast_save']==a.OUTPUT,'正式Save30親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,story=progress(s);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        m.idle(c.last,31);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=m.a.d.m.shared.trace(ART/'progress',a.OUTPUT);pb=m.a.d.m.shared.trace(ART/'continue',identity(saved))
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE31_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=None,story_event=story,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=False,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save30'])
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


