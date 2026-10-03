#!/usr/bin/env python3
"""Save38より先の新しい通常入力だけ。最初の新戦闘・story・未通過境界でSave39を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save38_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='d1f1145f391f01f1d28dd4a4ee9c781829191b08'
OUT=ROOT/'.local/pr16-story-save39';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save39_measure.py','tests/test_pr16_story_save39_measure.py','.github/workflows/pr16-story-save39.yml','tests/test_pr16_story_save39_menu.py','content/modernization/pr16_story_save39_preparation.json'}
PP=[1,5,0,0]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
def event_input(o):
    cb=o['callback2']
    if cb==m.FIELD:return ((1,2),(0,180))
    if cb==TRANSITION:return ((0,60),)
    need(cb!=m.BATTLE and cb&1 and 0x08000000<=cb<0x0a000000 and o.get('lock')==1,'ROM内の待機callbackだけ・未知UIへ決定入力しない')
    return ((0,60),)
TERRAIN='content/modernization/pr16_story_save38_evidence/inspection.json'
ROUTE=[[x,76]for x in range(9,-2,-1)]
JUMPS=set()
ORIGIN=[3,21]
DESTINATION=[3,44]
def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_outcome']in(0,1),'503南部または西側接続の操作可能field')
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'Save38/同一candidateだけ')
    path=ROOT/'content/modernization/pr16_story_save39_preparation.json';prep=json.loads(path.read_bytes())
    need(prep['origin']['map']==ORIGIN and prep['destination']['map']==DESTINATION and prep['route']==ROUTE,'初回保存済map/connection原本')
    return dict(status='STATIC_ROUTE503_WEST_CONNECTION_CANDIDATE_ONLY',preparation=identity(path.read_bytes()),route=ROUTE,origin=prep['origin'],connection=prep['connection'],destination=prep['destination'],new_map_views=0,new_script_nodes=0,native_connection_accepted=False)

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save38実PPの範囲')
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
    idle(o,38);need(o['xy']==ROUTE[0] and o['facing']==1 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'Save38唯一の親')
def battle(s):
    first=len(s.observations)-1;used=[0]*4;decisions=[]
    need(s.last['callback2']==m.BATTLE,'新battle開始を観測してからだけ')
    for _ in range(120):
        o=s.last
        need(o['map']in(ORIGIN,DESTINATION) and o['save_counter']==38 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');idle(o,38)
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
        need(o['callback2'] in (m.FIELD,m.BATTLE,TRANSITION),'未知callbackは停止')
        s.step(*(((0,60),)if o['callback2']==TRANSITION else ((1,2),(0,180))))
    raise ValueError('有限戦闘上限。無条件再走禁止')
def progress(s):
    start(s.last);route=[ROUTE[0]]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before and s.last['map']==ORIGIN,'直前の503南部座標')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,300 if target==ROUTE[-1]else 48))
            need(o['map']in(ORIGIN,DESTINATION),'503南部/西側接続だけ')
            if o['callback2']==m.BATTLE or o['lock']or o['callback2']!=m.FIELD:
                for _ in range(100):
                    if o['callback2']==m.BATTLE:
                        episode=battle(s);return route+[target],episode,dict(kind='new_battle',trigger=target,map=s.last['map'],xy=s.last['xy'],observation=len(s.observations)-1),[]
                    if o['callback2']==m.FIELD and o['lock']==0:
                        idle(o,38);return route+[target],None,dict(kind='new_event',trigger=target,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
                    need(o['map']in(ORIGIN,DESTINATION)and o['save_counter']==38 and o['party_count']==4 and o['rp']==0,'通常接続のeventだけ')
                    o=s.step(*event_input(o))
                raise ValueError('新event有限上限')
            idle(o,38)
            if o['map']==DESTINATION:return route+[target],None,dict(kind='west_connection',trigger=target,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
            need(o['xy']in(before,target),'503南部1tile境界')
            if o['xy']==target:route.append(target);break
        else:raise ValueError('未通過辺・原本保持')
    raise ValueError('未観測connectionを受入にしない')

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,38);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(38,39),'新Save39だけ')
        if o['save_counter']==39 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,39);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==81 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save38原本81member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save38 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save38開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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

def failed_original():
    terminal=inherited.terminal(37128174890,'12e19241d0d7ce9b19ce1d92bce054c41dc2d602',111217684192,['success','success','success','failure','skipped','success','success','success'])
    _,z=a.transport.archive(11275619886,37128174890,dict(size=154409,sha256='0320468fdbe5a207d3a108c761ca0b35e84502056fa077412969e719bec21277'),'12e19241d0d7ce9b19ce1d92bce054c41dc2d602')
    with z:
        manifest=json.loads(z.read('manifest.json'));need(set(z.namelist())==set(manifest)|{'manifest.json'},'失敗原本全member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'失敗原本全byte '+n)
        execution=json.loads(z.read('progress/execution.json'));need(execution['initial_save']==execution['final_save']==a.OUTPUT,'未保存・Save38不変')
        need(menu_index(z.read('progress/screen-0012.ppm'))==0,'実初回menu検出')
        need(json.loads(z.read('inspection.json'))==json.loads((ROOT/'content/modernization/pr16_story_save39_preparation.json').read_bytes()),'初回map原本再採取0')
    log=h.d.inputs.api('actions/jobs/111217684192/logs',True).decode().splitlines();tests=[v.split('Z ',1)[-1]for v in log if ' ... ok'in v and 'test_pr16_story_save39_measure.'in v]
    need(len(tests)==11 and any('Ran 11 tests in 'in v for v in log),'既成功11controller原log継承')
    return dict(terminal=terminal,artifact=11275619886,execution=execution,controller_tests=tests,controller_tests_replayed=0,native_processes=1,reason_ja='西側接続は到達したが固定タイミング下4入力の1回が反映されずTrainerCardへ入った。未保存原本保持。レポートcursor画像を各行で確認する変更影響だけ回復。')

def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'新区間初回のみ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        write(ART/'first-failed-original.json',failed_original())
        write(ART/'save38-record-terminal.json',inherited.terminal(37127976842,'da0ef846e31c2dc787ce15d18bd7a22c8d619720',111217116055,['success']*11))
        need(state['story_save38']['story_fast_save']==a.OUTPUT,'正式Save38親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,39);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=a.trace(ART/'progress',a.OUTPUT);pb=a.trace(ART/'continue',identity(saved))
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE39_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=True,outside_route503_reached=True,west_connection_accepted=final['map']==DESTINATION,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save38'])
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




