#!/usr/bin/env python3
"""Save98からRangerへ。最初の新wild1戦または接近終端だけSave99。"""
from __future__ import annotations
import json,os,sys,struct
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save98_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='360c9f7f5eaab889f04850ea0d041b46c31326a8'
OUT=ROOT/'.local/pr16-story-save99';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
PREP='content/modernization/pr16_story_save99_preparation.json'
CODE={'scripts/pr16_story_save99_measure.py','tests/test_pr16_story_save99_measure.py','.github/workflows/pr16-story-save99.yml',PREP}
PP=[3,9,8,2];TRANSITION=134569577
ORIGIN=[3,23];START=[28,39];END=[18,28]
classify=a.m.classify;direction=a.m.direction
ROUTE=[[28, 39], [28, 38], [28, 37], [28, 36], [28, 35], [28, 34], [29, 34], [30, 34], [31, 34], [32, 34], [32, 33], [32, 32], [32, 31], [32, 30], [32, 29], [32, 28], [32, 27], [32, 26], [32, 25], [31, 25], [31, 24], [31, 23], [31, 22], [31, 21], [31, 20], [31, 19], [31, 18], [31, 17], [31, 16], [31, 15], [32, 15], [32, 14], [32, 13], [31, 13], [30, 13], [29, 13], [28, 13], [27, 13], [26, 13], [25, 13], [25, 14], [25, 15], [24, 15], [24, 16], [24, 17], [24, 18], [23, 18], [22, 18], [22, 19], [22, 20], [22, 21], [21, 21], [20, 21], [19, 21], [19, 22], [19, 23], [19, 24], [19, 25], [19, 26], [19, 27], [19, 28], [18, 28]]

def idle(o,counter):
    need(o['map']==ORIGIN and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_outcome']in(0,1),'505番道路の操作可能fieldだけ')
def start(o):
    idle(o,98);need(o['xy']==START and o['facing']==2 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER and o['battle_flags']==o['battle_outcome']==0,'正式Save98唯一の親')
def excluded(xy):
    return any(max(0,abs(xy[0]-ox)-1)+max(0,abs(xy[1]-27)-1)<=1 for ox in(28,29))
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save98/同一候補')
    planned=json.loads((ROOT/PREP).read_bytes());canonical=(ROOT/'content/modernization/pr16_story_save98_next_route.json').read_bytes()
    need(planned['parent_route_binding']==identity(canonical)and json.loads(canonical)['route']==ROUTE==planned['route'],'親route exact byte/新61歩候補')
    need(planned['candidate']==a.shared.plan.CANDIDATE and planned['input_save']==a.OUTPUT,'候補/開始save固定')
    for row in planned['bindings']:need(raw[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'地形/object/ROCK_STAIRS全byte')
    need(len(ROUTE)==62 and ROUTE[0]==START and ROUTE[-1]==END and all(not excluded(xy)for xy in ROUTE),'未戦闘pair1113の移動全範囲と全方向視線を避ける')
    need(all(c['collision']==0 and c['behavior']in(0,2,33,42)for c in planned['terrain'])and planned['interaction']is None and planned['route_coord_intersections']==[],'会話/座標eventなし。草は野生の可能性あり')
    need(not any(w['xy']in ROUTE for w in planned['north']['warps']),'warp着地/発火は今回対象外')
    need(planned['rock_stairs_owner']['crossings']==[dict(before=[32,15],stair=[32,14],after=[32,13],button=64),dict(before=[22,19],stair=[22,20],after=[22,21],button=128)],'ROCK_STAIRSの南北通過。warp/一方向ledgeではない')
    tab,_=a.parent.sectors.bank(seed,0,98,a.parent.sectors.LAYOUT);party=seed[tab[1]+56:tab[1]+656]
    need(identity(party)['sha256']==a.PARTY and list(party[52:56])==PP and struct.unpack_from('<4H',party,44)==(337,89,280,332),'実party/技/PP')
    need(all(struct.unpack_from('<I',party,100*i+80)[0]==0 for i in range(4)),'4体status0、毒歩行ダメージなし')
    legacy,variables=a.parent.sectors.legacy_state(seed,tab)
    need(variables[0x21]==30 and variables[0x22]==0 and 30+len(ROUTE)-1<128,'98歩のfriendship周期前に停止する有限61歩')
    for row in planned['trainer_flag_preflight']:need(bool(legacy[row['physical_flag']//8]>>(row['physical_flag']%8)&1)==row['won'],'1054/1055勝利済み、1113未勝利')
    need(variables[0x61]==1 and variables[0x71]==9 and variables[0x72]==1,'4061/4071/4072保持')
    eb=a.parent.s61e_record(seed[tab[13]+0x7d0:tab[13]+0xde6]);need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==1 and(eb[259]>>4)&1==0,'4383/4382保持、4380未完')
    bag,money=a.parent.shared.bag(seed,tab);need(money==23114 and sum(q for item,q in bag['key_items']if item==274)==0,'封書引渡し済/支払再走なし')
    return dict(status='STATIC_SAVE99_FIRST_WILD_OR_RANGER_APPROACH_ONLY',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,terrain=planned['terrain'],rock_stairs_owner=planned['rock_stairs_owner'],binding_count=len(planned['bindings']),native_route_accepted=False)

def scope(o):
    need(o['map']==ORIGIN and o['save_counter']==98 and o['party_count']==4 and o['rp']==0 and o['flash_sha256']==a.FLASH,'最初の新区間だけ/未保存flash保持')
    need(o['battle_flags']&9==0 and o['battle_outcome']in(0,1),'未知trainer/double/敗北を決定しない')
def walking(o):
    scope(o);need(o['party_sha256']==a.PARTY and o['battle_flags']==o['battle_outcome']==0,'歩行61歩以下/周期前/status0のparty保持だけ')
def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n for n in used),'選択回数4slot')
    for slot in(2,0,1):
        if(used[slot]+1)*3<=PP[slot]:return slot
    raise ValueError('保守的3PP予約不足。補充/未観測技を選ばない')
def battle(s):
    first=len(s.observations)-1;commands=[0]*4;decisions=[]
    need(s.last['callback2']==m.BATTLE and s.last['battle_flags']&9==0,'最初のsingle wildだけ')
    for _ in range(120):
        o=s.last;scope(o)
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'wild通常勝利1のみ');idle(o,98)
            return dict(start=first,finish=len(s.observations)-1,trainer=False,outcome=1,move_commands=commands,target_confirmations=0,actual_pp_uses_not_inferred=True,decisions=decisions)
        if o['callback2']==m.BATTLE:
            kind,cursor=classify(m.screen(s))
            if kind=='moves':
                slot=select(commands)
                for key in m.navigation(cursor,slot):s.step((key,1),(0,12))
                need(classify(m.screen(s))==('moves',slot),'実技cursor確認')
                decisions.append(dict(observation=len(s.observations)-1,move_slot=slot));commands[slot]+=1;s.step((1,2),(0,240));continue
            need(kind!='shift','single wildで交代質問は想定外')
        need(o['callback2']in(m.FIELD,m.BATTLE,TRANSITION),'未知callbackは決定せず停止')
        s.step(*(((0,60),)if o['callback2']==TRANSITION else((1,2),(0,180))))
    raise ValueError('wild1戦の有限入力上限')
def progress(s,inspection):
    start(s.last);route=[START]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['map']==ORIGIN and s.last['xy']==before,'指定された505新区間だけ')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,48));scope(o)
            if o['callback2']in(TRANSITION,m.BATTLE):
                need(target in[t['xy']for t in inspection['terrain']if t['behavior']==2]and o['xy']==target,'指定草tileの新wildだけ')
                for _ in range(20):
                    if o['callback2']==m.BATTLE:break
                    need(o['callback2']==TRANSITION,'wild移行中に未知callback');o=s.step((0,60));scope(o)
                else:raise ValueError('wild開始待機有限上限')
                episode=battle(s);return route+[target],episode,dict(kind='first_new_wild',trigger=target,map=s.last['map'],xy=s.last['xy'],observation=len(s.observations)-1),[]
            walking(o);idle(o,98);need(o['xy']in(before,target),'1tile通常移動。未認識NPC/境界には決定しない')
            if o['xy']==target:route.append(target);break
        else:return route,None,dict(kind='unpassed_edge',before=before,target=target,attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
    # Rangerはmovement2/range2で移動する。前方確認前のA入力は一切しない。
    return route,None,dict(kind='ranger_approach_no_interaction',map=s.last['map'],xy=s.last['xy'],facing=s.last['facing'],observation=len(s.observations)-1),[]

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,98);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(98,99),'新Save99だけ')
        if o['save_counter']==99 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,99);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==84 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save98原本84member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save98 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save98開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1'and not OUT.exists(),'新区間初回のみ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        write(ART/'save98-record-terminal.json',inherited.terminal(37196489863,'3060cd081007374a6ced4f7d1394ee10901ee576',111419360155,['success']*11))
        need(state['story_save98']['story_fast_save']==a.OUTPUT,'正式Save98親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection)
        if frontier['kind']=='unpassed_edge':
            result=s.quit();need(s.save.read_bytes()==seed,'未通過なら入力SaveRTC全保持/通常保存しない')
            write(ART/'stopped.json',dict(status='STOPPED_APPROACH_WITHOUT_NEW_EVENT',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,inspection=inspection,route=route,frontier=frontier,final=s.last,progress=result,native_processes=1,ordinary_saves=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0));return
        need(frontier['kind']in('first_new_wild','ranger_approach_no_interaction')and not teleports,'最初のwild1戦またはRanger接近終端だけ保存')
        final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,99);need(c.last['map']==final['map']and c.last['xy']==final['xy']and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE99_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,ranger_approach_observed=frontier['kind']=='ranger_approach_no_interaction',ranger_approach_accepted=False,ranger_interaction_observed=False,letter_handoff_previously_accepted=True,museum_exit_previously_accepted=True,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,artifact_excludes=['existing ROM','runner','runtime','input Save98'])
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
        need(all(p.suffix in{'.srm','.ppm','.txt','.json'}for p in ART.rglob('*')if p.is_file()),'新公開artifactの拡張子だけ')
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes())for p in sorted(ART.rglob('*'))if p.is_file()and p.name!='manifest.json'})
if __name__=='__main__':main()
