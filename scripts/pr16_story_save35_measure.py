#!/usr/bin/env python3
"""Save34より先の新しい通常入力だけ。最初の新戦闘・story・未通過境界でSave35を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save34_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='80b95391eb2783ab0598f8639e9931a339d2088e'
OUT=ROOT/'.local/pr16-story-save35';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save35_measure.py','tests/test_pr16_story_save35_measure.py','tests/test_pr16_story_save35_transition.py','.github/workflows/pr16-story-save35.yml'}
PP=[1,14,0,0]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
def event_input(o):
    need(o['callback2']in(m.FIELD,TRANSITION),'未知callbackを広く許可しない')
    return ((0,60),)if o['callback2']==TRANSITION else ((1,2),(0,180))
PREP='content/modernization/pr16_story_save34_preparation.json'
TERRAIN='content/modernization/pr16_story_save32_preparation.json'
ROUTE=[[9, 7], [9, 8], [9, 9], [9, 10], [8, 10], [27, 7], [26, 7], [25, 7], [24, 7], [23, 7], [22, 7], [21, 7], [20, 7], [19, 7], [18, 7], [18, 6], [18, 5], [17, 5], [16, 5], [16, 4], [15, 4], [14, 4], [13, 4], [13, 5], [13, 6], [12, 6], [11, 6], [10, 6], [9, 6], [8, 6], [8, 5], [7, 5]]
JUMPS=set()
TELEPORT=([8,10],[27,7])
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'Save34/同一candidateだけ')
    prep=json.loads((ROOT/PREP).read_bytes());terrain=json.loads((ROOT/TERRAIN).read_bytes())
    need(prep['source_head']=='9b4354510b2f511043075548967ad36e4a506b06' and prep['run_id']==37123370663 and prep['inherited_cells']==920 and prep['new_terrain_cells']==0,'保存済map-load原本だけを再利用')
    need(prep['inherited_preparation']==identity((ROOT/TERRAIN).read_bytes()),'旧920地形とのhash結合')
    cells={tuple(t['xy']):t for t in terrain['allcells']}
    need(len(cells)==920 and all(cells[tuple(xy)]['collision']==0 for xy in ROUTE if xy!=[8,5]),'動的8,5以外は保存済通常床')
    need(cells[13,5]['elevation']==0 and cells[13,5]['behavior']==42,'西岩階段の保存原本')
    instructions=prep['instructions'];root=[x for x in instructions if x['node']==136398393]
    need([x['hex']for x in root]==['2b0211','070100462108','2b0f11','07014c462108','02'],'map-loadの実flag4367分岐')
    dynamic=[x for x in instructions if x['node']==136398412]
    need([x['hex']for x in dynamic]==['a20800050081020000','03'],'8,5のmetatile0281/collision0だけ')
    bank,_=a.parent.sectors.bank(seed,0,34,a.parent.sectors.LAYOUT)
    _,variables=a.parent.sectors.legacy_state(seed,bank);ext=a.parent.s61e_record(seed[bank[13]+0x7d0:bank[13]+0xde6])
    need(bool(ext[(4367-2304)//8]&(1<<((4367-2304)%8))) and variables[0x71]==7 and variables[0]==0,'正規開通flagと次event前状態')
    owner=json.loads((ROOT/'content/modernization/pr16_story_cave_route_checkpoint.json').read_bytes())['result']['reverse_teleport']
    need(owner['address']==136398463 and owner['target_map']==[1,73] and owner['xy']==[27,7],'8,10戻り転送保存owner')
    need(not any(x==[9,7]and y==[9,6]for x,y in zip(ROUTE,ROUTE[1:])),'未通過北辺は反復しない')
    return dict(status='STATIC_OPENED_WEST_DETOUR_NOT_REACHABILITY_PROOF',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,terrain=[cells[tuple(xy)]for xy in ROUTE],dynamic_tile=dict(xy=[8,5],metatile=641,collision=0,flag=4367,script=136398412),return_teleport=owner,native_arrival_accepted=False,new_terrain_cells=0,new_script_nodes=0)

def select(used):
    need(len(used)==4 and all(type(n)is int and 0<=n<=PP[i]for i,n in enumerate(used)),'Save34実PPの範囲')
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
    m.idle(o,34);need(o['xy']==ROUTE[0] and o['facing']==2 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'Save34唯一の親')
def battle(s):
    first=len(s.observations)-1;used=[0]*4;decisions=[]
    need(s.last['callback2']==m.BATTLE,'新battle開始を観測してからだけ')
    for _ in range(120):
        o=s.last
        need(o['map']==[1,73] and o['save_counter']==34 and o['rp']==0 and o['party_count']==4,'新戦闘scope')
        if o['callback2']==m.FIELD and o['lock']==0:
            need(o['battle_outcome']==1,'通常勝利1のみ');m.idle(o,34)
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
    start(s.last);route=[ROUTE[0]];teleports=[]
    for before,target in zip(ROUTE,ROUTE[1:]):
        if (before,target)==TELEPORT:continue # 正規scriptによる非隣接移動は直前の入力で待つ
        need(s.last['xy']==before,'直前の実座標')
        attempts=[]
        for _ in range(3):
            o=s.step((direction(before,target),8),(0,48));attempts.append(len(s.observations)-1)
            allowed=[before,target]+([TELEPORT[1]]if target==TELEPORT[0]else [])
            need(o['map']==[1,73] and o['xy']in allowed,'固定通常辺と保存ownerの戻り転送だけ')
            if target==TELEPORT[0] and o['xy']in TELEPORT:
                for _ in range(16):
                    if o['callback2']==m.FIELD and o['lock']==0 and o['xy']==TELEPORT[1]:
                        m.idle(o,34);route.extend(TELEPORT);teleports.append(dict(trigger=TELEPORT[0],destination=TELEPORT[1],observation=len(s.observations)-1));break
                    need(o['callback2']!=m.BATTLE,'warp途中の未知battleは停止')
                    o=s.step((0,60));need(o['map']==[1,73] and o['xy']in TELEPORT,'戻り転送の有限待ち')
                else:raise ValueError('戻り転送の有限上限。無条件再走しない')
                break
            if o['lock'] or o['callback2']!=m.FIELD:
                for _ in range(80):
                    if o['callback2']==m.BATTLE:return route,battle(s),dict(kind='new_battle',trigger=target),teleports
                    if o['callback2']==m.FIELD and o['lock']==0:
                        m.idle(o,34);return route,None,dict(kind='story_event',trigger=target,xy=o['xy'],observation=len(s.observations)-1),teleports
                    need(o['callback2']in(m.FIELD,TRANSITION) and o['map']==[1,73] and 0<=o['xy'][0]<40 and 0<=o['xy'][1]<23,'洞窟scriptの有限UIだけ')
                    o=s.step(*event_input(o))
                raise ValueError('新eventの有限待ち上限。無条件再走しない')
            m.idle(o,34)
            if o['xy']==target:route.append(target);break
        else:return route,None,dict(kind='blocked_edge',before=before,target=target,attempt_observations=attempts,claim='NOT_TRAVERSED_SAVE_FRONTIER_ONLY'),teleports
    return route,None,dict(kind='route_endpoint',xy=s.last['xy'],observation=len(s.observations)-1),teleports

def save(s):
    m.idle(s.last,34);target=s.last['xy']
    s.step((8,2),(0,60));s.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==[1,73] and o['save_counter'] in (34,35),'新Save35だけ')
        if o['save_counter']==35 and o['callback2']==m.FIELD and o['lock']==0:break
    m.idle(o,35);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==35 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save34原本35member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save34 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save34開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
    meta,z=a.transport.archive(11273509448,37124366728,dict(size=149927,sha256='49e568d4e5d9bff6e6435a988c8956e6ecd16eb69bed361093edd3e385878bcb'),'f98a120aea81a8f333a0449a66f0700103e3313f')
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==31 and set(z.namelist())==set(manifest)|{'manifest.json'},'失敗32member保全')
        for n,b in manifest.items():need(identity(z.read(n))==b,'未保存失敗member '+n)
        failure=json.loads(z.read('failure.json'));trace=[json.loads(x)for x in z.read('progress/stdout.txt').decode().splitlines()]
        obs=[x for x in trace if 'observe'in x]
        need(failure['native_processes']==1 and failure['message']=='洞窟scriptの有限UIだけ','実行済み失敗を成功へ改作しない')
        need(len(obs)==24 and obs[-1]['xy']==[16,5] and obs[-1]['callback2']==TRANSITION and all(x['flash_sha256']==a.FLASH and x['save_counter']==34 for x in obs),'未保存/全Flash不変で回収可能な新Saveなし')
        need(trace[-1]['inputs']==56 and trace[-1]['guarded_host_writes']==0 and not any(n.endswith('.srm')for n in manifest),'Save34から未受入区間だけ回復')
    log=h.d.inputs.api('actions/jobs/111206585603/logs',True).decode().splitlines()
    tests=[x.split('Z ',1)[-1]for x in log if ' ... ok'in x and 'test_pr16_story_save35_measure.'in x]
    need(len(tests)==19 and any('Ran 19 tests in 'in x for x in log),'不変19controller成功step原本継承')
    return dict(run_id=37124366728,job_id=111206585603,source_head='f98a120aea81a8f333a0449a66f0700103e3313f',artifact_id=11273509448,conclusion='failure',native_processes=1,inputs=56,screen_count=24,save_completed=False,controller_tests_passed=19,controller_tests_replayed=0,failed_callback=TRANSITION,recovery='CHANGED_TRANSITION_CONTROLLER_FROM_UNCHANGED_SAVE34_ONLY',failure=failure,test_lines=tests)

def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'新区間初回のみ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        write(ART/'save34-record-terminal.json',inherited.terminal(37123931026,'a4c565b152c26e00e5a68b381a9a564a389a45f9',111205330968,['success']*11))
        need(state['story_save34']['story_fast_save']==a.OUTPUT,'正式Save34親')
        write(ART/'failed-original.json',failed_original())
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        m.idle(c.last,35);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        pa=m.a.d.m.shared.trace(ART/'progress',a.OUTPUT);pb=m.a.d.m.shared.trace(ART/'continue',identity(saved))
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE35_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(pa['screens'])+len(pb['screens']),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=False,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save34'])
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




