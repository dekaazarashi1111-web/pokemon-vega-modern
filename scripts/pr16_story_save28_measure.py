#!/usr/bin/env python3
"""Save27から南1tileの新coord teleport。実script条件と通常Save28を限定測定。"""
from __future__ import annotations
import json,os,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save27_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
m=a.m.m;h=m.h
BASE='a3e55510d6695e6252950154473d68cfeceab49f'
OUT=ROOT/'.local/pr16-story-save28';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save28_measure.py','tests/test_pr16_story_save28_measure.py','.github/workflows/pr16-story-save28.yml'}
START=[19,13];TRIGGER=[19,14];ROOT_ADDRESS=0x08214661

def decode(raw,flag):
    need(type(raw)is bytes and len(raw)==30 and type(flag)is int and flag in (0,1),'正規30byte/flag値')
    need(raw[:4]==bytes([0x2b,0x0f,0x11,0x06]) and raw[4]==1 and struct.unpack_from('<I',raw,5)[0]==ROOT_ADDRESS+20,'checkflag4367/true分岐')
    need(raw[9]==0x69 and raw[18:20]==bytes([0x6d,2]),'false側lock/release/end')
    def dest(i):
        op,bank,number,warp,x,y,release,end=struct.unpack_from('<BBBBHHBB',raw,i)
        need((op,bank,number,warp,release,end)==(0x3d,1,73,0x99,0x6d,2),'同洞窟の正規warpteleportだけ')
        need([x,y]in ([27,7],[8,10]),'既知destinationだけ');return [x,y]
    no,yes=dest(10),dest(20);need(no!=yes,'2枝を混同しない')
    return dict(root=ROOT_ADDRESS,flag_id=4367,flag_value=flag,false_destination=no,true_destination=yes,expected_destination=yes if flag else no)

def scope(o):
    need(o['map']==[1,73] and o['xy']in (START,TRIGGER,[27,7],[8,10]) and o['save_counter']==27 and o['party_count']==4 and o['rp']==0 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['battle_flags']==o['battle_outcome']==0,'teleport限定/戦闘やhost変更なし')

def progress(s,target):
    m.idle(s.last,27);scope(s.last);need(s.last['xy']==START and s.last['facing']==3,'Save27唯一の親')
    for _ in range(3):
        o=s.step((128,8),(0,32));scope(o)
        if o['xy']!=START or o['lock'] or o['callback2']!=m.FIELD:break
    else:raise ValueError('南1tileに進めない。盲反復禁止')
    for _ in range(40):
        scope(o)
        if o['xy']==target and o['callback2']==m.FIELD and o['lock']==0:
            m.idle(o,27);return dict(trigger=TRIGGER,destination=target,observation=len(s.observations)-1)
        o=s.step((0,30))
    raise ValueError('有限teleport待機で未到達。原本保持し再走しない')

def save(s):
    m.idle(s.last,27);target=s.last['xy']
    s.step((8,2),(0,60));s.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(8):
        o=s.step((0,120));need(o['xy']==target and o['map']==[1,73] and o['save_counter']in(27,28),'Save28保存境界')
        if o['save_counter']==28 and o['callback2']==m.FIELD and o['lock']==0:break
    m.idle(o,28);need(o['flash_sha256']!=a.FLASH and o['party_sha256']==a.PARTY,'通常保存/party不変');return o
def restore():
    ASSETS.mkdir()
    # ROM/runnerは既存Save24 artifact内で読取り。既存input Save24は展開しない。
    _,z=a.transport.archive(m.a.ARTIFACT,m.a.RUN,m.a.ARCHIVE,m.a.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        for n,b in manifest.items():need(identity(z.read(n))==b,'親全member '+n)
        for n,b in [('candidate.gba',m.a.d.m.shared.plan.CANDIDATE),('runner',m.a.d.m.prior.parent.RUNNER)]:
            raw=z.read(n);need(identity(raw)==b,'固定既存 '+n);(ASSETS/n).write_bytes(raw);(ASSETS/n).chmod(0o555 if n=='runner'else 0o444)
    _,z=a.transport.archive(a.ARTIFACT,a.RUN,a.ARCHIVE,a.SOURCE)
    with z:
        bindings=json.loads(z.read('manifest.json'))
        need(len(bindings)==52 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save27原本')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save27 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save27開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
    runtime=OUT/'runtime';runtime.mkdir()
    _,z=a.transport.archive(11263910704,37094769974,dict(size=102440293,sha256='661ad2b88d25607d81ac46141f85cd42f2fcf88db4f306e1601257f3277e099f'),'1c7b23e4a6a5708cebdb2713c97f553b47ac616b')
    with z:
        bindings=json.loads(z.read('runtime/manifest.json'));need(len(bindings)>5,'runtime全member一覧')
        for n,b in bindings.items():
            name=m.runtime_member('runtime/'+n);raw=z.read('runtime/'+name);need(identity(raw)==b,'保持runtime全byte '+name)
            p=runtime/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    need(identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'同一mGBA')
    return runtime

def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'新区間初回だけ')
    need(state['story_save27']['story_fast_save']==a.OUTPUT,'正式Save27親')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        write(ART/'save27-record-terminal.json',inherited.terminal(37116490265,'dacc10021fcb1a2d76e318113871b5e698878023',111184208479,['success']*10))
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes();rom=(ASSETS/'candidate.gba').read_bytes()
        bank,_=a.parent.sectors.bank(seed,0xe000,27,a.parent.sectors.LAYOUT)
        ext=a.parent.s61e_record(seed[bank[13]+0x7d0:bank[13]+0xde6]);flag=(ext[(4367-2304)//8]>>((4367-2304)%8))&1
        owner=decode(rom[ROOT_ADDRESS-0x8000000:ROOT_ADDRESS-0x8000000+30],flag);write(ART/'coord-owner.json',owner)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        teleport=progress(s,owner['expected_destination']);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        m.idle(c.last,28);need(c.last['xy']==final['xy'] and c.last['party_sha256']==a.PARTY,'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=a.shared.trace(ART/'progress',a.OUTPUT);pb=a.shared.trace(ART/'continue',identity(saved));need(h.d.bindings(protected)==protected,'受入source不変')
        report=dict(status='MEASURED_COORD_TELEPORT_SAVE28_AWAITING_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,output_save=identity(saved),owner=owner,teleport=teleport,final=final,continued=c.last,progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,wild_victories=0,trainer_victories=0,cave_crossing_complete=False,full_story_accepted=False,release_ready=False,artifact_excludes=['existing ROM','runner','runtime','input Save27'])
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
        need(all(p.suffix in {'.srm','.ppm','.txt','.json'}for p in ART.rglob('*')if p.is_file()),'新公開artifact種別')
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes())for p in sorted(ART.rglob('*'))if p.is_file()and p.name!='manifest.json'})
if __name__=='__main__':main()
