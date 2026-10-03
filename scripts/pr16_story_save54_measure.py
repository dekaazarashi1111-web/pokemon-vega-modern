#!/usr/bin/env python3
"""Save53より先の新しい通常入力だけ。最初の新戦闘・story・未通過境界でSave54を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save53_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='bdba440a5a434288595b2bcb33b5896ff72be796'
OUT=ROOT/'.local/pr16-story-save54';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'content/modernization/pr16_story_save54_preparation.json','scripts/pr16_story_save54_measure.py','tests/test_pr16_story_save54_measure.py','.github/workflows/pr16-story-save54.yml'}
PP=[11,10,15,14]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
def event_input(o):
    cb=o['callback2']
    if cb==m.FIELD:return ((1,2),(0,180))
    if cb==TRANSITION:return ((0,60),)
    need(cb!=m.BATTLE and cb&1 and 0x08000000<=cb<0x0a000000 and o.get('lock')==1,'ROM内の待機callbackだけ・未知UIへ決定入力しない')
    return ((0,60),)
PREP='content/modernization/pr16_story_save54_preparation.json'
TERRAIN='content/modernization/pr16_story_save50_preparation.json'
ORIGIN=[6,5]
DESTINATION=[6,5]
START=[7,8]
classify=a.m.classify

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save53の実PP残量だけ')
    for slot in (3,0,2,1):
        if used[slot]<PP[slot]:return slot
    raise ValueError('実PP枯渇。host回復しない')

def direction(before,after):
    delta=tuple(b-a for a,b in zip(before,after))
    need(delta in((0,1),(0,-1),(1,0),(-1,0)),'1tile隣接だけ')
    return {(0,1):128,(0,-1):64,(1,0):16,(-1,0):32}[delta]

def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_outcome']in(0,1),'505/南接続先の操作可能fieldだけ')

def start(o):
    idle(o,53);need(o['map']==ORIGIN and o['xy']==START and o['facing']==2 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER,'Save53唯一の親')

ROUTE=[[7,y]for y in range(8,3,-1)]
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save53/同一候補')
    prep=json.loads((ROOT/PREP).read_bytes());need(prep['source_head']=='bdba440a5a434288595b2bcb33b5896ff72be796'and prep['run_id']==37149252523 and prep['candidate']==a.shared.plan.CANDIDATE and prep['input_save']==a.OUTPUT,'保存済5cellsのみ')
    need(prep['route']==ROUTE and prep['interior']['map']==ORIGIN,'室内4歩だけ')
    cells={tuple(c['xy']):c for c in prep['terrain']}
    for xy in ROUTE[1:]:
        t=cells[tuple(xy)];need(t['elevation']==3 and t['collision']==0 and t['behavior']==0,'平坦な室内経路だけ')
    need(cells[(7,3)]==dict(xy=[7,3],elevation=0,collision=1,behavior=128),'受付カウンター')
    need(any(x['category']=='special'and x['value']==0 and x['instruction_address']==135872182 and x['roots']==['candidate_npc_3']for x in prep['healer']),'受付local3のheal special0')
    return dict(status='STATIC_SAVE54_HEALER_PATH_ONLY',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,terrain=prep['terrain'],healer_owner=dict(local_id=3,xy=[7,2],script=135790449,shared_menu=135872070,heal_script=135872156,heal_special=0,special_instruction=135872182),new_terrain_cells=0,new_map_views=0,new_script_nodes=0,native_route_accepted=False)

def conversation_scope(o):
    need(o['map']==ORIGIN and o['xy']==[7,4]and o['live_xy']==[14,11]and o['facing']==2 and o['party_count']==4 and o['rp']==0 and o['save_counter']==53 and o['battle_flags']==o['battle_outcome']==0 and o['callback2']==m.FIELD,'受付会話の範囲だけ')
    need(o['flash_sha256']==a.FLASH,'通常保存前にFlash変更なし')

def progress(s,inspection):
    start(s.last);route=[START]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before,'直前室内座標')
        for attempt in range(3):
            o=s.step((64,8),(0,48));idle(o,53)
            need(o['xy']in(before,target)and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'4歩はparty/Flash不変')
            if o['xy']==target:route.append(target);break
        else:return route,None,dict(kind='unpassed_edge',before=before,target=target,attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
    conversation_scope(s.last);o=s.step((1,2),(0,180));conversation_scope(o)
    need(o['lock']==1,'通常Aで受付script開始');start_index=len(s.observations)-1
    # owner graphの先頭選択=回復。通常Aだけ、party書換えなし。最初のscript終了で止める。
    for _ in range(60):
        conversation_scope(o)
        if o['lock']==0:
            idle(o,53);return route,None,dict(kind='healer_conversation',map=o['map'],xy=o['xy'],start_observation=start_index,observation=len(s.observations)-1,party_changed=o['party_sha256']!=a.PARTY),[]
        o=s.step((1,2),(0,180))
    raise ValueError('有限受付会話上限。自動再走なし')

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,53);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(53,54),'新Save54だけ')
        if o['save_counter']==54 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,54);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==75 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save53原本75member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save53 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save53開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save53-record-terminal.json',inherited.terminal(37148761559,'8fa4d19c42eb0771a41b0d0f89b673f4e51ab8de',111278022912,['success']*11))
        need(state['story_save53']['story_fast_save']==a.OUTPUT,'正式Save53親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,54);need(c.last['map']==final['map'] and c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE54_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=True,outside_route503_reached=True,healer_conversation_started=frontier['kind']=='healer_conversation',normal_recovery_required=True,pp_recovery_accepted=False,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save53'])
        # native完了receiptを独立episode parserより先に固定。新eventの座標を旧episodeへ誤適用しない。
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




