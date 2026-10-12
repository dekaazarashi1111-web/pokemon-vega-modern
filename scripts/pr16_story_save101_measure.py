#!/usr/bin/env python3
"""Save100から解放後の西地域接続という宣言済milestoneまで。"""
from __future__ import annotations
import json,os,sys,struct
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save100_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='c2cf8d5d22ec13a4de7fc8fc427396bbc16d4ac1'
OUT=ROOT/'.local/pr16-story-save101';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
PREP='content/modernization/pr16_story_save101_preparation.json'
CODE={'scripts/pr16_story_save101_measure.py','tests/test_pr16_story_save101_measure.py','.github/workflows/pr16-story-save101.yml',PREP}
PP=[3,9,8,2];TRANSITION=134569577
ORIGIN=[3,2];DESTINATION=[3,24];START=[4,17];EDGE=[0,17];ARRIVAL=[53,13]
ROUTE=[[4,17],[3,17],[2,17],[1,17],[0,17]]
direction=a.m.direction
from pr16_story_milestones import MilestoneEpisode,DiagnosticStop
CODE|={'scripts/pr16_story_milestones.py','tests/test_pr16_story_milestones.py','docs/PR16_STORY_MILESTONE_CONTRACT_JA.md'}

def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_flags']==o['battle_outcome']==0,'町/西道路の操作可能fieldだけ')
def start(o):
    idle(o,100);need(o['map']==ORIGIN and o['xy']==START and o['facing']==2 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER,'正式Save100唯一の親')
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save100/同一候補')
    p=json.loads((ROOT/PREP).read_bytes());canonical=(ROOT/'content/modernization/pr16_story_save100_next_route.json').read_bytes()
    need(p['parent_route_binding']==identity(canonical)and p['route']==json.loads(canonical)['route']==ROUTE,'親計画最終改行込みbyte/4歩経路')
    need(p['candidate']==identity(raw)and p['input_save']==identity(seed),'ROM/save固定')
    for row in p['bindings']:need(raw[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'地形/object/connection全byte')
    need(p['connection_owner']==dict(source=dict(direction=3,offset=4,target_map=DESTINATION),reciprocal=dict(direction=4,offset=-4,target_map=ORIGIN),source_edge=EDGE,input_target=[-1,17],target_candidate=ARRIVAL,button=32,direction=3,classification='CONTIGUOUS_MAP_CONNECTION_NOT_WARP_EVENT',native_accepted=False),'方向3/offset4/逆offset-4通常接続')
    need(all(t['collision']==0 and t['behavior']==0 and t['elevation']==3 for t in p['terrain'])and len(p['terrain'])==6,'両端通常床behavior0/衝突0/矢印階段なし')
    need(p['route_coord_intersections']==[]and p['interaction']is None,'経路の未解明イベントなし')
    need(not any(w['xy']in ROUTE for w in p['town']['warps'])and not any(w['xy']==ARRIVAL for w in p['west']['warps']),'warp登録との区別')
    tab,_=a.parent.sectors.bank(seed,0,100,a.parent.sectors.LAYOUT);party=seed[tab[1]+56:tab[1]+656]
    need(identity(party)['sha256']==a.PARTY and list(party[52:56])==PP and struct.unpack_from('<HH',party,86)==(277,294),'実party/HP/PP')
    need(all(struct.unpack_from('<I',party,100*i+80)[0]==0 for i in range(4)),'4体status0')
    legacy,variables=a.parent.sectors.legacy_state(seed,tab);need((variables[0x21],variables[0x22],variables[0x61],variables[0x71],variables[0x72])==(93,3,1,9,3),'Save100歩数/解放後story')
    need(93+5<128,'friendship周期前の接続5歩')
    eb=a.parent.s61e_record(seed[tab[13]+0x7d0:tab[13]+0xde6]);need(eb[259]&0xd0==0xd0 and eb[256]&1,'4380/4382/4383と4352')
    blocked=[o for o in p['objects']['2']if o['xy']in ROUTE];need([o['local_id']for o in blocked]==[6]and blocked[0]['flag']==4380,'経路object6は解放済4380で非表示')
    return dict(status=p['status'],preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,terrain=p['terrain'],connection_owner=p['connection_owner'],milestone_contract=p['milestone_contract'],binding_count=len(p['bindings']),native_route_accepted=False)
def scope(o):
    need(o['map']in(ORIGIN,DESTINATION)and o['save_counter']==100 and o['party_count']==4 and o['rp']==0 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'西地域接続まで全party/flash保持')
    need(o['callback2']==m.FIELD and o['battle_flags']==o['battle_outcome']==0,'未知callback/戦闘は決定しない')
def progress(s,inspection):
    start(s.last);route=[START];episode=MilestoneEpisode(inspection['milestone_contract']);episode.begin(s.last)
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['map']==ORIGIN and s.last['xy']==before,'宣言済の町新区間だけ')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,48));scope(o);idle(o,100)
            need(o['map']==ORIGIN and o['xy']in(before,target),'1tile通常歩行・未指定eventなし')
            if o['xy']==target:route.append(target);break
        else:raise DiagnosticStop('unpassed_edge',dict(before=before,target=target,observation=len(s.observations)-1))
    edge_observation=len(s.observations)-1;need(s.last['xy']==EDGE and s.last['facing']==3,'西端着地/西向き実観測')
    for attempt in range(4):
        o=s.last;scope(o)
        if o['map']==DESTINATION and o['lock']==0:break
        if o['map']==ORIGIN and o['lock']==0:
            need(o['xy']==EDGE,'西端以外の入力禁止');s.step((32,8),(0,180))
        else:raise DiagnosticStop('unexpected_event',dict(observation=len(s.observations)-1))
    else:raise DiagnosticStop('connection_not_reached',dict(observation=len(s.observations)-1))
    o=s.last;scope(o);idle(o,100);need(o['map']==DESTINATION and o['xy']==ARRIVAL and o['facing']==3,'offset4の最初の道路field')
    milestone=episode.reach(o,dict(field_return=True,owners_resolved=True,observation_match=True,resources=dict(hp=277,pp=PP)),len(s.observations)-1)
    return route,episode.ledger,dict(kind='milestone_reached',milestone=milestone,source_edge=EDGE,edge_observation=edge_observation,map=o['map'],xy=o['xy'],facing=o['facing'],observation=len(s.observations)-1),[]

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,100);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(100,101),'新Save101だけ')
        if o['save_counter']==101 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,101);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==69 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save100原本69member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save100 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save100開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save100-record-terminal.json',inherited.terminal(37199540423,'4730763b5ba68e4e5c77b2c3b4226acf8b590d25',111428199096,['success']*11))
        need(state['story_save100']['story_fast_save']==a.OUTPUT,'正式Save100親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection)
        need(frontier['kind']=='milestone_reached'and episode==[]and not teleports,'宣言済地域milestoneだけ保存/診断停止は保存しない')
        final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,101);need(c.last['map']==final['map']and c.last['xy']==final['xy']and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE101_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,west_connection_observed=True,west_connection_accepted=False,milestone_reached=True,diagnostic_frontier_completed=False,ordinary_battle_checkpoint=False,native_battle_continuation_accepted=False,letter_handoff_previously_accepted=True,museum_exit_previously_accepted=True,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,artifact_excludes=['existing ROM','runner','runtime','input Save100'])
        write(ART/'measurement.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as e:
        for s in sessions:
            if not s.closed and s.process.poll() is None:
                try:s.quit()
                except Exception:s.process.terminate()
        write(ART/'failure.json',dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',type=type(e).__name__,message=str(e),milestone_reached=False,diagnostic_frontier_completed=False,native_processes=len(sessions),source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID'])))
        raise
    finally:
        for p in ART.rglob('*.srm'):
            if identity(p.read_bytes())==a.OUTPUT:p.unlink()
        need(all(p.suffix in{'.srm','.ppm','.txt','.json'}for p in ART.rglob('*')if p.is_file()),'新公開artifactの拡張子だけ')
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes())for p in sorted(ART.rglob('*'))if p.is_file()and p.name!='manifest.json'})
if __name__=='__main__':main()
