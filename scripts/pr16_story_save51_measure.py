#!/usr/bin/env python3
"""Save50より先の新しい通常入力だけ。最初の新戦闘・story・未通過境界でSave51を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save50_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='9a562b2ad97280ec1d1e8f253540d7c67218f0f5'
OUT=ROOT/'.local/pr16-story-save51';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save51_measure.py','tests/test_pr16_story_save51_measure.py','.github/workflows/pr16-story-save51.yml'}
PP=[11,10,15,18]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
def event_input(o):
    cb=o['callback2']
    if cb==m.FIELD:return ((1,2),(0,180))
    if cb==TRANSITION:return ((0,60),)
    need(cb!=m.BATTLE and cb&1 and 0x08000000<=cb<0x0a000000 and o.get('lock')==1,'ROM内の待機callbackだけ・未知UIへ決定入力しない')
    return ((0,60),)
PREP='content/modernization/pr16_story_save50_evidence/inspection.json'
ORIGIN=[3,23]
DESTINATION=[3,2]
START=[22,18]
classify=a.m.classify

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save50の実PP残量だけ')
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
    idle(o,50);need(o['map']==ORIGIN and o['xy']==START and o['facing']==2 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'Save50唯一の親')

def inspect(raw,seed):
    import struct
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'Save50/同一candidateだけ')
    table,_=a.parent.sectors.bank(seed,0,50,a.parent.sectors.LAYOUT)
    party=seed[table[1]+56:table[1]+656]
    need(identity(party)['sha256']==a.PARTY and struct.unpack_from('<H',party,32)[0]==850 and list(party[52:56])==PP and list(party[152:156])==[0]*4,'現時点の実party/PP。host回復なし')
    prior=json.loads((ROOT/PREP).read_bytes());route=prior['route'][57:];levels=prior['candidate_levels'][57:]
    need(len(route)==48 and route[0]==START and route[-1]==[28,39]and levels[0]==4 and levels[-1]==3,'前回未通過47歩のみ')
    need(prior['target_xy']==[28,0]and prior['south_map']['map']==DESTINATION and prior['target_elevation']==3,'保存済南connectionだけ')
    return dict(status='STATIC_REUSED_ROUTE505_REMAINDER_ONLY',prior=identity((ROOT/PREP).read_bytes()),route=route,candidate_levels=levels,terrain=prior['terrain'][57:],target_xy=prior['target_xy'],target_elevation=3,south_map=prior['south_map'],new_terrain_cells=0,new_map_views=0,new_script_nodes=0,native_route_accepted=False)

class MoveBudget:
    """選択コマンドの上限と相手確定を分離。PP実消費は保存byteで別途検証。"""
    def __init__(self):self.commands=[0]*4;self.targets=0;self.pending=None
    def choose(self):return select(self.commands)
    def selected(self,slot,double):
        need(self.pending is None and slot==self.choose(),'選択順と二重予約を確認')
        self.commands[slot]+=1
        if double:self.pending=slot
    def target(self,cursor):
        need(self.pending is not None and cursor==self.pending,'直前選択に対応する相手確定だけ')
        slot=self.pending;self.pending=None;self.targets+=1;return slot
    def advance(self):self.pending=None

def battle(s):
    first=len(s.observations)-1;budget=MoveBudget();decisions=[]
    need(s.last['callback2']==m.BATTLE,'新battle開始を観測してからだけ')
    for _ in range(120):
        o=s.last
        need(o['map']in(ORIGIN,DESTINATION) and o['save_counter']==50 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');idle(o,50)
            return dict(start=first,finish=len(s.observations)-1,trainer=bool(o['battle_flags']&8),outcome=1,move_commands=budget.commands,target_confirmations=budget.targets,actual_pp_uses_not_inferred=True,decisions=decisions)
        need(o['battle_outcome'] in (0,1),'敗北等は停止')
        if o['callback2']==m.BATTLE:
            kind,cursor=classify(m.screen(s))
            if kind=='moves':
                if budget.pending is not None:
                    slot=budget.target(cursor);decisions.append(dict(observation=len(s.observations)-1,target_slot=slot))
                    s.step((1,2),(0,240));continue
                slot=budget.choose()
                for key in m.navigation(cursor,slot):s.step((key,1),(0,12))
                need(classify(m.screen(s))==('moves',slot),'実技cursor')
                decisions.append(dict(observation=len(s.observations)-1,move_slot=slot))
                budget.selected(slot,bool(o['battle_flags']&1));s.step((1,2),(0,240));continue
            budget.advance()
            if kind=='shift':
                decisions.append(dict(observation=len(s.observations)-1,keep_current=True));s.step((2,2),(0,180));continue
        need(o['callback2'] in (m.FIELD,m.BATTLE,TRANSITION),'未知callbackは停止')
        s.step(*(((0,60),)if o['callback2']==TRANSITION else ((1,2),(0,180))))
    raise ValueError('有限戦闘上限。無条件再走禁止')
def progress(s,inspection):
    start(s.last);route=[START];plan=inspection['route']
    for before,target in zip(plan,plan[1:]):
        need(s.last['xy']==before and s.last['map']==ORIGIN,'直前の505座標')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,48))
            need(o['map']==ORIGIN,'未通過505新区間だけ')
            if o['callback2']==m.BATTLE or o['lock']or o['callback2']!=m.FIELD:
                for _ in range(160):
                    if o['callback2']==m.BATTLE:
                        episode=battle(s);return route+[target],episode,dict(kind='new_battle',trigger=target,map=s.last['map'],xy=s.last['xy'],observation=len(s.observations)-1),[]
                    if o['callback2']==m.FIELD and o['lock']==0:
                        idle(o,50);return route+[target],None,dict(kind='new_event',trigger=target,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
                    need(o['map']==ORIGIN and o['save_counter']==50 and o['party_count']==4 and o['rp']==0,'通常505eventだけ')
                    o=s.step(*event_input(o))
                raise ValueError('新505event有限上限')
            idle(o,50);need(o['xy']in(before,target),'505通常1tile境界')
            if o['xy']==target:route.append(target);break
        else:return route,None,dict(kind='unpassed_edge',before=before,target=target,attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
    for attempt in range(3):
        o=s.step((128,8),(0,48))
        for _ in range(160):
            need(o['map']in(ORIGIN,DESTINATION)and o['save_counter']==50 and o['party_count']==4 and o['rp']==0,'南接続の新区間だけ')
            if o['callback2']==m.BATTLE:
                episode=battle(s);return route+[s.last['xy']],episode,dict(kind='new_battle',map=s.last['map'],xy=s.last['xy'],observation=len(s.observations)-1),[]
            if o['callback2']==m.FIELD and o['lock']==0:
                idle(o,50)
                if o['map']==DESTINATION:
                    need(o['xy']==inspection['target_xy'],'南接続先実位置');return route+[o['xy']],None,dict(kind='new_connection',map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
                need(o['xy']==plan[-1],'接続前は南端だけ');break
            o=s.step(*event_input(o))
        else:raise ValueError('南接続待機有限上限')
    return route,None,dict(kind='unpassed_connection',before=plan[-1],target=inspection['target_xy'],attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,50);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(50,51),'新Save51だけ')
        if o['save_counter']==51 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,51);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==168 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save50原本168member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save50 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save50開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save50-record-terminal.json',inherited.terminal(37144605978,'384ecdce0ab7aad6925c8a8a1ad01adab4c17f93',111265850823,['success']*11))
        need(state['story_save50']['story_fast_save']==a.OUTPUT,'正式Save50親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,51);need(c.last['map']==final['map'] and c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE51_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=True,outside_route503_reached=True,south_connection_observed=frontier['kind']=='new_connection',normal_recovery_required=True,pp_recovery_accepted=False,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save50'])
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




