#!/usr/bin/env python3
"""Save37より先の新しい通常入力だけ。最初の新戦闘・story・未通過境界でSave38を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save37_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='0d952edaa33d312c21137e1c83432775d182d3ca'
OUT=ROOT/'.local/pr16-story-save38';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save38_measure.py','tests/test_pr16_story_save38_measure.py','.github/workflows/pr16-story-save38.yml','tests/test_pr16_story_save38_door.py','content/modernization/pr16_story_save38_preparation.json','tests/test_pr16_story_save38_event.py'}
PP=[1,8,0,0]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
def event_input(o):
    cb=o['callback2']
    if cb==m.FIELD:return ((1,2),(0,180))
    if cb==TRANSITION:return ((0,60),)
    need(cb!=m.BATTLE and cb&1 and 0x08000000<=cb<0x0a000000 and o.get('lock')==1,'ROM内の待機callbackだけ・未知UIへ決定入力しない')
    return ((0,60),)
PREP='content/modernization/pr16_story_save34_preparation.json'
TERRAIN='content/modernization/pr16_story_save32_preparation.json'
ROUTE=[[6,4],[6,5],[5,5],[4,5],[4,6]]
JUMPS=set()
ORIGIN=[1,38]
DESTINATION=[3,21]
def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_outcome']in(0,1),'南出口部屋または503番道路の操作可能field')
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'Save37/同一candidateだけ')
    prep_path=ROOT/'content/modernization/pr16_story_save38_preparation.json'
    prep=json.loads(prep_path.read_bytes());room=prep['origin'];dest=prep['destination'];warp=prep['exit_warp']
    need(room['map']==ORIGIN and dest['map']==DESTINATION and prep['route']==ROUTE,'失敗原本の保存済接続owner')
    need(warp['xy']==[4,6]and warp['target_map']==DESTINATION and warp['target_warp']==1,'通常南出口warp')
    need(all(room['collision_grid'][y][x]in '.W' for x,y in ROUTE),'保存済部屋候補')
    from tools.t02.rom_inventory import RomImage,ScriptWalker,ScriptRoot
    npc=[o for o in dest['objects']if o['local_id']==10 and o['xy']==[13,76]]
    need(len(npc)==1,'出口正面NPC10の固定owner')
    walker=ScriptWalker(RomImage('route503-exit-npc',raw));walker.add_root(ScriptRoot(npc[0]['script'],'route503_npc10','object'));graph=walker.walk()
    return dict(status='STATIC_ROUTE503_CONNECTION_CANDIDATE_ONLY',exit_npc=npc[0],exit_npc_graph=graph,preparation=identity(prep_path.read_bytes()),route=ROUTE,origin=room,exit_warp=warp,destination=dest,destination_source=prep['destination_source'],new_map_views=0,new_script_nodes=0,native_exit_accepted=False,door_exit_input=dict(from_xy=[4,6],direction='south',key=128))
def door_input(o):
    idle(o,37);need(o['map']==ORIGIN and o['xy']==[4,6]and o['facing']==1,'実出口矢印tileから南へ1回だけ');return ((128,8),(0,300))

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save37実PPの範囲')
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
    idle(o,37);need(o['xy']==ROUTE[0] and o['facing']==3 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'Save37唯一の親')
def battle(s):
    first=len(s.observations)-1;used=[0]*4;decisions=[]
    need(s.last['callback2']==m.BATTLE,'新battle開始を観測してからだけ')
    for _ in range(120):
        o=s.last
        need(o['map']==DESTINATION and o['save_counter']==37 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');idle(o,37)
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
def exit_event_input(o):
    need(o['map']==DESTINATION and o['xy']==[9,76]and o['save_counter']==37 and o['party_count']==4 and o['rp']==0,'503出口NPC会話の範囲')
    return event_input(o)
def progress(s):
    start(s.last);route=[ROUTE[0]]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before and s.last['map']==ORIGIN,'直前の出口部屋座標')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,300 if target==ROUTE[-1]else 48))
            if target==ROUTE[-1]and(o['map']==DESTINATION or o['xy']==target):
                if o['map']==ORIGIN and o['callback2']==m.FIELD and o['lock']==0:o=s.step(*door_input(o))
                for _ in range(100):
                    if o['map']==DESTINATION and o['callback2']==m.BATTLE:
                        episode=battle(s);idle(s.last,37)
                        return route+[target],episode,dict(kind='route503_exit_trainer',trigger=target,map=s.last['map'],xy=s.last['xy'],observation=len(s.observations)-1),[]
                    if o['map']==DESTINATION and o['callback2']==m.FIELD and o['lock']==0:
                        idle(o,37);return route+[target],None,dict(kind='route503_exit',trigger=target,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
                    need(o['map']in(ORIGIN,DESTINATION),'通常出口とそのNPCだけ')
                    o=s.step(*(exit_event_input(o)if o['map']==DESTINATION else((0,60),)))
                raise ValueError('出口NPCイベント有限上限。無条件再走しない')
            need(o['map']==ORIGIN and o['xy']in(before,target),'通常部屋内の固定辺');idle(o,37)
            if o['xy']==target:route.append(target);break
        else:raise ValueError('通常部屋歩行の未通過辺。繰返さず原本を保持')
    raise ValueError('未観測exitを成功へ昇格しない')

def save(s):
    idle(s.last,37);target=s.last['xy'];where=s.last['map']
    s.step((8,2),(0,60));s.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter'] in (37,38),'新Save38だけ')
        if o['save_counter']==38 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,38);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==48 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save37原本48member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save37 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save37開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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

def controller_receipts():
    result=[]
    for job,source,suite,count in [(111214539355,'096b25e970312a189d5bb45e439a70cdfca73ca4','test_pr16_story_save38_measure',10),(111215039388,'de044e9f81d4506d36c7398a840252edb62fb327','test_pr16_story_save38_door',3)]:
        path='tests/'+suite+'.py';need(h.d.git('show',source+':'+path)==(ROOT/path).read_bytes(),'controller試験source不変')
        lines=h.d.inputs.api('actions/jobs/'+str(job)+'/logs',True).decode().splitlines()
        tests=[v.split('Z ',1)[-1]for v in lines if ' ... ok'in v and suite+'.'in v]
        need(len(tests)==count and any(f'Ran {count} tests in 'in v for v in lines)and any(v.endswith(' OK')for v in lines),'既存試験成功だけ継承')
        result.append(dict(job=job,source=source,count=count,test_lines=tests,replayed_tests=0))
    return result

def failed_original():
    terminal=inherited.terminal(37127113183,'096b25e970312a189d5bb45e439a70cdfca73ca4',111214539355,['success','success','success','failure','skipped','success','success','success'])
    _,z=a.transport.archive(11275422186,37127113183,dict(size=99253,sha256='b7d8eb05a146d394d66a00232b20fceae72886238e8a0842ce70418ce1f037e8'),'096b25e970312a189d5bb45e439a70cdfca73ca4')
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==31 and set(z.namelist())==set(manifest)|{'manifest.json'},'失敗全31member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'失敗原本全byte '+n)
        failure=json.loads(z.read('failure.json'));execution=json.loads(z.read('progress/execution.json'))
        need(failure['native_processes']==1 and execution['initial_save']==execution['final_save']==a.OUTPUT,'未保存の初回だけ・Save37親を保持')
        obs=[json.loads(l)for l in z.read('progress/stdout.txt').decode().splitlines()if '"observe"'in l]
        need(len(obs)==24 and all(o['map']==ORIGIN and o['xy']==[4,6]and o['lock']==0 and o['save_counter']==37 for o in obs[7:]),'矢印出口tileで待機しただけ・外未到達')
        need(json.loads(z.read('inspection.json'))==json.loads((ROOT/'content/modernization/pr16_story_save38_preparation.json').read_bytes()),'新地形は既採取原本を利用')
    return dict(terminal=terminal,artifact=11275422186,failure=failure,execution=execution,reason_ja='南出口矢印tileは待機で遷移せず、南への通常入力が必要。未保存区間の変更影響に限る回復。',native_processes=1,accepted_case_reruns=0,accepted_test_reruns=0)

def second_failed_original():
    terminal=inherited.terminal(37127420854,'6440c70c8dd20442d67f5de89e0c9d93f12acafc',111215461690,['success','success','success','failure','skipped','success','success','success'])
    _,z=a.transport.archive(11275593672,37127420854,dict(size=151666,sha256='c9beb864b9a8a0962414918ec231abf744eaf46c2241d339b999f254904bf544'),'6440c70c8dd20442d67f5de89e0c9d93f12acafc')
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==35 and set(z.namelist())==set(manifest)|{'manifest.json'},'第二失敗全35member')
        for n,b in manifest.items():need(identity(z.read(n))==b,'第二失敗原本全byte '+n)
        failure=json.loads(z.read('failure.json'));execution=json.loads(z.read('progress/execution.json'))
        need(failure['native_processes']==1 and execution['initial_save']==execution['final_save']==a.OUTPUT,'未保存・Save37全byte保持')
        obs=[json.loads(l)for l in z.read('progress/stdout.txt').decode().splitlines()if '"observe"'in l]
        need(len(obs)==25 and all(o['map']==DESTINATION and o['xy']==[9,76]and o['lock']==1 and o['save_counter']==37 for o in obs[8:]),'出口到達後のNPC会話待ち・未保存')
    return dict(terminal=terminal,artifact=11275593672,failure=failure,execution=execution,reason_ja='追加南入力で屋外到達したが出口NPC会話で停止。正規会話/戦闘を含む変更影響区間だけ回復。',native_processes=1,accepted_case_reruns=0,accepted_test_reruns=0)

def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'新区間初回のみ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        write(ART/'second-failed-original.json',second_failed_original())
        write(ART/'first-failed-original.json',failed_original())
        write(ART/'preflight-failure.json',inherited.terminal(37127280308,'de044e9f81d4506d36c7398a840252edb62fb327',111215039388,['success','success','failure','skipped','skipped','failure','success','success']))
        write(ART/'controller-receipts.json',controller_receipts())
        write(ART/'save37-record-terminal.json',inherited.terminal(37126518059,'db7fbddd8929cf457be95b19d22be5831d22d2eb',111212777875,['success']*11))
        need(state['story_save37']['story_fast_save']==a.OUTPUT,'正式Save37親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,38);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=a.trace(ART/'progress',a.OUTPUT);pb=a.trace(ART/'continue',identity(saved))
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE38_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=True,outside_route503_reached=True,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save37'])
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




