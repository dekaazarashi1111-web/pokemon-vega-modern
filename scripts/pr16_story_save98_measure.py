#!/usr/bin/env python3
"""Save97の町から新35歩と北connectionだけを通過し最初のfieldで通常Save98。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
# 受入済sourceを変えず、既存の有限import上限だけ継承する。
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save97_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='94fe5da3310b2373c0934405ab0156f1528054df'
OUT=ROOT/'.local/pr16-story-save98';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
PREP='content/modernization/pr16_story_save98_preparation.json'
CODE={'scripts/pr16_story_save98_measure.py','tests/test_pr16_story_save98_measure.py','.github/workflows/pr16-story-save98.yml',PREP}
PP=[3,9,8,2];TRANSITION=134569577
PARTY_AFTER_WALK='a889748859f118b98c42e9ef5f0fd2847466d07383f5743946453c961261580d'
RECOVERY='content/modernization/pr16_story_save98_party_recovery.json';CODE.add(RECOVERY)
ORIGIN=[3,2];DESTINATION=[3,23];START=[19,26];EDGE=[28,0];ARRIVAL=[28,39]
classify=a.m.classify
direction=a.m.direction
ROUTE=[[19, 26], [20, 26], [21, 26], [22, 26], [23, 26], [23, 25], [23, 24], [23, 23], [23, 22], [23, 21], [23, 20], [23, 19], [23, 18], [23, 17], [23, 16], [23, 15], [23, 14], [23, 13], [23, 12], [23, 11], [24, 11], [25, 11], [25, 10], [25, 9], [26, 9], [27, 9], [28, 9], [28, 8], [28, 7], [28, 6], [28, 5], [28, 4], [28, 3], [28, 2], [28, 1], [28, 0]]

def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_outcome']==0,'町/505番道路の操作可能fieldだけ')

def start(o):
    idle(o,97);need(o['map']==ORIGIN and o['xy']==START and o['facing']==1 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER,'Save97唯一の親')

def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save97/同一候補')
    planned=json.loads((ROOT/PREP).read_bytes());canonical=(ROOT/'content/modernization/pr16_story_save97_next_route.json').read_bytes()
    need(planned['parent_route_binding']==identity(canonical) and json.loads(canonical)['route']==ROUTE==planned['route'],'親route exact byte/新35歩')
    need(planned['candidate']==a.shared.plan.CANDIDATE and planned['input_save']==a.OUTPUT,'候補/開始save固定')
    for row in planned['bindings']:need(raw[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'地形/connection/table全byte')
    owner=planned['connection_owner'];need(owner==dict(source=dict(direction=2,offset=0,target_map=DESTINATION),reciprocal=dict(direction=1,offset=0,target_map=ORIGIN),source_edge=EDGE,input_target=[28,-1],target_candidate=ARRIVAL,button=64,direction=2,classification='CONTIGUOUS_MAP_CONNECTION_NOT_WARP_EVENT',native_accepted=False),'通常北connection/逆向き接続/offset0')
    need(planned['terrain'][-2:]==[dict(map=ORIGIN,xy=EDGE,collision=0,elevation=3,behavior=33),dict(map=DESTINATION,xy=ARRIVAL,collision=0,elevation=3,behavior=33)],'両側0x21床/衝突0。矢印や方向階段ではない')
    need(all(t['collision']==0 and t['behavior']in(0,33)for t in planned['terrain'])and planned['interaction']is None and planned['route_coord_intersections']==[],'安全な通常通路のみ/会話や座標eventなし')
    need(not any(o['xy']in ROUTE for o in planned['town']['objects'])and not any(o['xy']==ARRIVAL for o in planned['north']['objects']),'静的objectと重ならない。動的NPCはruntimeで停止')
    need(not any(w['xy']in ROUTE for w in planned['town']['warps'])and not any(w['xy']==ARRIVAL for w in planned['north']['warps']),'warp登録を出口扱いしない。通常map connection')
    tab,_=a.parent.sectors.bank(seed,0xe000,97,a.parent.sectors.LAYOUT);party=seed[tab[1]+56:tab[1]+656]
    need(identity(party)['sha256']==a.PARTY and list(party[52:56])==PP,'全party/HP/PP保持')
    eb=a.parent.s61e_record(seed[tab[13]+0x7d0:tab[13]+0xde6]);need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==1 and(eb[259]>>4)&1==0,'4383/4382保持、4380未完')
    legacy,vars=a.parent.sectors.legacy_state(seed,tab);need(vars[0x61]==1 and vars[0x71]==9 and vars[0x72]==1,'4061/4071/4072保持')
    for flag in [2083,1697,1412,1440]:need(legacy[flag//8]>>(flag%8)&1,'badge/leader/trainer勝利保持')
    bag,money=a.parent.shared.bag(seed,tab);need(money==23114 and sum(q for item,q in bag['key_items']if item==274)==0,'封書引渡し済み。再会話しない')
    recovery=json.loads((ROOT/RECOVERY).read_bytes());derived=bytearray(party)
    for offset,before,after in recovery['diagnostic_exact_preimage_deltas']:
        need(derived[offset]==before,'診断preimage before');derived[offset]=after
    need(identity(derived)['sha256']==PARTY_AFTER_WALK==recovery['observed_party_sha256']and recovery['runtime_owner_resolved']is False,'600bytes exact preimage。診断だけでfixture書込みしない')
    return dict(status='STATIC_SAVE98_TOWN_NORTH_CONNECTION_ONLY',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,terrain=planned['terrain'],connection_owner=owner,binding_count=len(planned['bindings']),native_route_accepted=False)

def scope(o):
    need(o['map']in(ORIGIN,DESTINATION)and o['save_counter']==97 and o['party_count']==4 and o['rp']==0 and o['party_sha256']in(a.PARTY,PARTY_AFTER_WALK)and o['flash_sha256']==a.FLASH,'初境界まで観測済party2種とflash保持')
    phase=PARTY_AFTER_WALK if o['map']==DESTINATION or o['xy']in ROUTE[6:]else a.PARTY
    need(o['party_sha256']==phase,'町23,24の6歩目以降だけ観測済3byte変化。位置限定')
    need(o['callback2']not in(m.BATTLE,TRANSITION)and o['battle_flags']==o['battle_outcome']==0,'未知戦闘は決定せず停止')

def progress(s,inspection):
    start(s.last);route=[START]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['map']==ORIGIN and s.last['xy']==before,'指定された町の未通過区間だけ')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,48));scope(o);idle(o,97)
            need(o['map']==ORIGIN and o['xy']in(before,target),'1tile通常移動/未指定eventなし')
            if o['xy']==target:route.append(target);break
        else:return route,None,dict(kind='unpassed_edge',before=before,target=target,attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
    # 35歩後の北端スクリーンと停止座標を確保し、通常北入力だけで接続を試す。
    edge_observation=len(s.observations)-1;need(s.last['xy']==EDGE and s.last['facing']==2,'通常北connection前の向き/着地確認')
    for attempt in range(4):
        o=s.last;scope(o)
        if o['map']==DESTINATION and o['callback2']==m.FIELD and o['lock']==0:break
        if o['map']==ORIGIN and o['callback2']==m.FIELD and o['lock']==0:
            need(o['xy']==EDGE,'北端以外で追加入力しない');s.step((64,8),(0,180))
        else:s.step((0,180))
    else:raise ValueError('有限north connection待機上限')
    o=s.last;scope(o);idle(o,97);need(o['map']==DESTINATION and o['xy']==ARRIVAL and o['facing']==2,'offset0の最初の道路fieldだけ')
    return route,None,dict(kind='new_town_north_connection',source_edge=EDGE,edge_observation=edge_observation,map=o['map'],xy=o['xy'],facing=o['facing'],observation=len(s.observations)-1),[]

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,97);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(97,98),'新Save98だけ')
        if o['save_counter']==98 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,98);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==61 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save97原本61member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save97 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save97開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save97-record-terminal.json',inherited.terminal(37194679580,'783714626e892c2b4e11305007da811755554814',111413969510,['success']*11))
        need(state['story_save97']['story_fast_save']==a.OUTPUT,'正式Save97親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection)
        if frontier['kind']=='unpassed_edge':
            result=s.quit();need(s.save.read_bytes()==seed,'未通過なら入力SaveRTC全保持/通常保存しない')
            write(ART/'stopped.json',dict(status='STOPPED_APPROACH_WITHOUT_NEW_EVENT',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,inspection=inspection,route=route,frontier=frontier,final=s.last,progress=result,native_processes=1,ordinary_saves=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0));return
        need(frontier['kind']=='new_town_north_connection'and episode is None and not teleports,'新北connectionだけ保存')
        final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,98);need(c.last['map']==final['map']and c.last['xy']==final['xy']and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE98_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,prior_failed_native_processes=1,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,town_north_connection_observed=True,town_north_connection_accepted=False,ranger_interaction_observed=False,letter_handoff_previously_accepted=True,museum_exit_previously_accepted=True,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,artifact_excludes=['existing ROM','runner','runtime','input Save97'])
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
