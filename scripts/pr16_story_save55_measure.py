#!/usr/bin/env python3
"""Save54より先の新しい通常入力だけ。最初の新戦闘・story・未通過境界でSave55を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save54_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='f4f43a2672e5427988118267f46faac0b4623711'
OUT=ROOT/'.local/pr16-story-save55';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'content/modernization/pr16_story_save55_preparation.json','scripts/pr16_story_save55_measure.py','tests/test_pr16_story_save55_measure.py','.github/workflows/pr16-story-save55.yml'}
PP=[15,10,15,20]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
def event_input(o):
    cb=o['callback2']
    if cb==m.FIELD:return ((1,2),(0,180))
    if cb==TRANSITION:return ((0,60),)
    need(cb!=m.BATTLE and cb&1 and 0x08000000<=cb<0x0a000000 and o.get('lock')==1,'ROM内の待機callbackだけ・未知UIへ決定入力しない')
    return ((0,60),)
PREP='content/modernization/pr16_story_save55_preparation.json'
TERRAIN='content/modernization/pr16_story_save50_preparation.json'
ORIGIN=[6,5]
DESTINATION=[3,2]
START=[7,4]
classify=a.m.classify

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save54の実PP残量だけ')
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
    idle(o,54);need(o['map']==ORIGIN and o['xy']==START and o['facing']==2 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER,'Save54唯一の親')

ROUTE=[[7,y]for y in range(4,9)]
TOWN_ROUTE=[[x,16]for x in range(38,19,-1)]+[[20,y]for y in range(17,21)]+[[x,20]for x in range(19,15,-1)]
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save54/同一候補')
    p=json.loads((ROOT/PREP).read_bytes());old=json.loads((ROOT/'content/modernization/pr16_story_save53_owner.json').read_bytes())
    need(p['source_head']=='f4f43a2672e5427988118267f46faac0b4623711'and p['run_id']==37150727892 and p['candidate']==a.shared.plan.CANDIDATE and p['input_save']==a.OUTPUT,'新owner原本だけ')
    cells={tuple(c['xy']):c for c in old['previous_terrain']+old['terrain']}
    for xy in TOWN_ROUTE:
        t=cells[tuple(xy)];need(t['elevation']==3 and t['collision']==0 and t['behavior']in(0,33),'保存済平地の必須NPC経路')
    npc=[o for o in p['town']['objects']if o['local_id']==10];need(len(npc)==1 and npc[0]==dict(local_id=10,xy=[15,20],script=149023660,flag=4381),'レンジャーowner')
    refs=[x for x in p['graph']['references']if 'town_npc_10'in x['roots']]
    need({x['value']for x in refs if x['category']=='trainer'}=={329,330,331},'初期starter別通常trainer3候補')
    need(any(x['category']=='item'and x['value']==182 and x['access']=='use'and x['command']=='additem'for x in refs),'通常がくしゅうそうち1個')
    need(any(x['category']=='flag'and x['value']==4381 and x['access']=='set'for x in refs),'通常NPC離脱flag')
    tab,_=a.parent.sectors.bank(seed,0,54,a.parent.sectors.LAYOUT);flags,vars=a.parent.sectors.legacy_state(seed,tab)
    starter=vars[0x31];need(starter in(0,1,2),'保存starter3分岐だけ')
    party=seed[tab[1]+56:tab[1]+656];need(identity(party)['sha256']==a.PARTY and list(party[52:56])==PP and list(party[152:156])==[10,20,15,10],'回復済party/実PPだけ')
    return dict(status='STATIC_SAVE55_REQUIRED_RANGER_ROUTE_ONLY',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,town_route=TOWN_ROUTE,terrain=[cells[tuple(x)]for x in TOWN_ROUTE],exit_tile=next(c for c in p['new_terrain']if c['map']==[6,5]),ranger=npc[0],ranger_owner=refs,starter_var4031=starter,expected_trainer={0:331,1:330,2:329}[starter],rejected_optional_house=dict(map=[39,0],reason_ja='暫定gym名の静的候補はTM21の民家。必須経路へ採用しない。'),new_terrain_cells=0,new_map_views=0,new_script_nodes=0,native_route_accepted=False)

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
        need(o['map']in(ORIGIN,DESTINATION) and o['save_counter']==54 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');idle(o,54)
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
def event(s,route,trigger):
    o=s.last
    for _ in range(180):
        need(o['map']in(ORIGIN,DESTINATION)and o['save_counter']==54 and o['party_count']==4 and o['rp']==0,'通常event scope')
        if o['callback2']==m.BATTLE:
            episode=battle(s);return route+[s.last['xy']],episode,dict(kind='new_battle',trigger=trigger,map=s.last['map'],xy=s.last['xy'],observation=len(s.observations)-1),[]
        if o['callback2']==m.FIELD and o['lock']==0:
            idle(o,54);return route+[o['xy']],None,dict(kind='new_event',trigger=trigger,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
        o=s.step(*event_input(o))
    raise ValueError('有限必須event上限')

def progress(s,inspection):
    start(s.last);route=[START]
    # 回復受付には触れず、通常南移動と出口warpだけ。
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before and s.last['map']==ORIGIN,'直前室内位置')
        for attempt in range(3):
            o=s.step((128,8),(0,48));need(o['map']in(ORIGIN,DESTINATION)and o['callback2']!=m.BATTLE,'回復後出口だけ')
            if o['map']==DESTINATION:break
            if o['callback2']==m.FIELD and o['lock']==0:
                idle(o,54);need(o['xy']in(before,target),'室内1tileだけ')
                if o['xy']==target:route.append(target);break
            else:break
        else:return route,None,dict(kind='unpassed_edge',before=before,target=target,attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
        if o['map']==DESTINATION or o['lock']or o['callback2']!=m.FIELD:break
    for attempt in range(4):
        o=s.last
        if o['map']==DESTINATION and o['callback2']==m.FIELD and o['lock']==0:break
        need(o['map']in(ORIGIN,DESTINATION)and o['callback2']!=m.BATTLE and o['save_counter']==54,'exit warp待機')
        if o['map']==ORIGIN and o['callback2']==m.FIELD and o['lock']==0:
            need(o['xy']==[7,8],'出口arrow位置');s.step((128,8),(0,180))
        else:s.step((0,180))
    else:raise ValueError('有限exit warp上限')
    o=s.last;idle(o,54);need(o['map']==DESTINATION and o['xy']==[38,16],'外PC前だけ');route.append(o['xy'])
    for before,target in zip(TOWN_ROUTE,TOWN_ROUTE[1:]):
        need(s.last['xy']==before and s.last['map']==DESTINATION,'直前town位置')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,48));need(o['map']==DESTINATION,'未完town経路だけ')
            if o['callback2']!=m.FIELD or o['lock']:return event(s,route,target)
            idle(o,54);need(o['xy']in(before,target),'town1tile通常入力')
            if o['xy']==target:route.append(target);break
        else:return route,None,dict(kind='unpassed_edge',before=before,target=target,attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
    need(s.last['xy']==[16,20]and s.last['facing']==3,'レンジャー東隣・西向き')
    s.step((1,2),(0,180));need(s.last['lock']==1 or s.last['callback2']==m.BATTLE,'通常Aで必須NPC会話開始')
    return event(s,route,[15,20])

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,54);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(54,55),'新Save55だけ')
        if o['save_counter']==55 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,55);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==54 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save54原本54member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save54 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save54開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save54-record-terminal.json',inherited.terminal(37150128228,'1e4551b4da705a01da77fd53f109a182cf316c8a',111282060951,['success']*11))
        need(state['story_save54']['story_fast_save']==a.OUTPUT,'正式Save54親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,55);need(c.last['map']==final['map'] and c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE55_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=True,outside_route503_reached=True,ranger_encounter=frontier['kind']=='new_battle',normal_recovery_required=False,pp_recovery_accepted=True,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save54'])
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




