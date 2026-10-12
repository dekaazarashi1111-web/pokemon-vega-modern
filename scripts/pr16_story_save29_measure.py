#!/usr/bin/env python3
"""Save28より先の新しい通常入力だけ。最初の新戦闘/西岩階段でSave29を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save28_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='1ef950e14fdef75b2ca15a2986d7e59be2f6f616'
OUT=ROOT/'.local/pr16-story-save29';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save29_measure.py','tests/test_pr16_story_save29_measure.py','tests/test_pr16_story_save29_owner.py','.github/workflows/pr16-story-save29.yml'}
PP=[1,14,0,5]
ROUTE=[[x,7]for x in range(27,17,-1)]+[[18,6],[18,5],[18,4]]+[[x,4]for x in range(17,12,-1)]+[[13,5],[13,6]]
def owner_operands(values):
    need(len(values)==8 and all(type(v)is int for v in values),'8つの実operand')
    op0,op1,flag,op2,var,value,release,end=values
    need((op1,flag,op2,var,value,end)==(0x29,4367,0x16,0x4071,7,2),'setflag4367/setvar4071=7/endの独立byte')
    return dict(first_opcode=op0,setflag_opcode=op1,flag=flag,setvar_opcode=op2,variable=var,value=value,release_opcode=release,end_opcode=end)
def inspect(raw,seed):
    from pr16_story_after_maori import unpack
    import pr16_story_cave_route as owner
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'Save28/同一candidateだけ')
    checkpoint=h.d.read(ROOT/'content/modernization/pr16_story_cave_route_checkpoint.json')['result']
    rows=owner.coords(raw,137444032)
    need(rows==checkpoint['coordinate_events'],'保存済みcoord原本を再利用')
    roots=rows[3:9]
    need(all(r['script']==0x08214656 and r['trigger_var']==0x4071 and r['trigger_value']==6 and r['elevation']==3 for r in roots),'西側story owner')
    operands=owner_operands(unpack(raw,0x08214656,'BBHBHHBB'))
    bank,_=a.parent.sectors.bank(seed,0,28,a.parent.sectors.LAYOUT)
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
    need(all(t['collision']==0 for t in terrain) and [t['elevation']for t in terrain]==[4]*18+[0,3],'西高台→岩階段→下層の新経路')
    need(terrain[-2]['behavior']==42,'高さ0の正規岩階段')
    need([r['xy']for r in rows if r['xy']in ROUTE]==[[27,7]],'開始点以外にcoord再踏なし')
    return dict(status='NEW_WEST_ROUTE_PREFLIGHT',owner_operands=operands,route=ROUTE,terrain=terrain,story_owner=dict(root=0x08214656,coords=[r['xy']for r in roots],flag=4367,variable=0x4071,value=7),runtime_story_unlock_accepted=False)

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save28実PPの範囲')
    for slot in (3,1,0):
        if used[slot]<PP[slot]:return slot
    raise ValueError('実PP枯渇。host回復しない')
def direction(before,after):
    delta=tuple(b-a for a,b in zip(before,after));need(delta in ((0,1),(0,-1),(1,0),(-1,0)),'1tile隣接のみ')
    return {(0,1):128,(0,-1):64,(1,0):16,(-1,0):32}[delta]
def start(o):
    m.idle(o,28);need(o['xy']==ROUTE[0] and o['facing']==1 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'Save28唯一の親')
def battle(s):
    first=len(s.observations)-1;used=[0]*4;decisions=[]
    need(s.last['callback2']==m.BATTLE,'新battle開始を観測してからだけ')
    for _ in range(120):
        o=s.last
        need(o['map']==[1,73] and o['save_counter']==28 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');m.idle(o,28)
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
            need(o['map']==[1,73] and o['xy']in (before,target),'指定1tileの実座標')
            if o['lock'] or o['callback2']!=m.FIELD:
                for _ in range(6):
                    if o['callback2']==m.BATTLE:break
                    o=s.step((1,2),(0,180))
                return route,battle(s),None
            m.idle(o,28)
            if o['xy']==target:route.append(target);break
        else:raise ValueError('同方向3回停止。静的候補を盲反復しない')
    return route,None,None

def save(s):
    m.idle(s.last,28);target=s.last['xy']
    s.step((8,2),(0,60));s.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(8):
        o=s.step((0,120));need(o['xy']==target and o['map']==[1,73] and o['save_counter'] in (28,29),'新Save29だけ')
        if o['save_counter']==29 and o['callback2']==m.FIELD and o['lock']==0:break
    m.idle(o,29);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==36 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save28原本')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save28 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save28開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save28-record-terminal.json',inherited.terminal(37117631601,'3900c985f1901d9e0a674cc6254b2b6af2923bd0',111187403209,['success']*10))
        need(state['story_save28']['story_fast_save']==a.OUTPUT,'正式Save28親')
        _,failed=a.transport.archive(11272197339,37118280803,dict(size=1626,sha256='bbda0747f8f9046a52f5f1eae7346f8be74c229dddf52f534e4341129ca2a398'),'4fe06a3b1a7a09279c591fe4619e6328c8f55ac4')
        with failed:
            fm=json.loads(failed.read('manifest.json'));need(set(fm)=={'failure.json','save28-record-terminal.json'},'前回native前だけ')
            for name,binding in fm.items():need(identity(failed.read(name))==binding,'前回失敗member')
            f=json.loads(failed.read('failure.json'));need(f['native_processes']==0 and f['message']=='正規lock/setflag/setvar/release/end','先頭/末尾opcodeを未観測で仮定した失敗')
            write(ART/'preflight-failure.json',f)
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,teleport=progress(s);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        m.idle(c.last,29);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=m.a.d.m.shared.trace(ART/'progress',a.OUTPUT);pb=m.a.d.m.shared.trace(ART/'continue',identity(saved))
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE29_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleport,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=False,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save28'])
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

