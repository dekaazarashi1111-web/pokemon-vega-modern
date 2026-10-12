#!/usr/bin/env python3
"""Save91より先の新しい通常入力だけ。最初の博物館1階到着でSave92を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save91_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='cb123628924ea49d9799743a9fa32e54f266a947'
OUT=ROOT/'.local/pr16-story-save92';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save92_measure.py','tests/test_pr16_story_save92_measure.py','.github/workflows/pr16-story-save92.yml'}
PP=[3,9,8,2]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
PREP='content/modernization/pr16_story_save92_preparation.json'
CODE.add(PREP)
TERRAIN='content/modernization/pr16_story_save50_preparation.json'
ORIGIN=[3,2]
DESTINATION=[6,0]
START=[20,11]
classify=a.m.classify

def direction(before,after):
    delta=tuple(b-a for a,b in zip(before,after))
    need(delta in((0,1),(0,-1),(1,0),(-1,0)),'1tile隣接だけ')
    return {(0,1):128,(0,-1):64,(1,0):16,(-1,0):32}[delta]

def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_outcome']in(0,1),'町/博物館の操作可能fieldだけ')

def start(o):
    idle(o,91);need(o['map']==ORIGIN and o['xy']==START and o['facing']==1 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER,'Save91唯一の親')

ROUTE=[[20, 11], [20, 12], [20, 13], [20, 14], [20, 15], [20, 16], [20, 17], [20, 18], [20, 19], [20, 20], [20, 21], [20, 22], [21, 22], [22, 22], [23, 22], [23, 23], [23, 24], [23, 25], [23, 26], [22, 26], [21, 26], [20, 26], [19, 26], [19, 25]]
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save91/同一候補')
    planned=json.loads((ROOT/PREP).read_bytes());need(planned['route']==ROUTE and planned['candidate']==a.shared.plan.CANDIDATE and planned['input_save']==a.OUTPUT,'博物館入場23歩/Save91固定')
    canonical=(ROOT/'content/modernization/pr16_story_save91_next_route.json').read_bytes()
    need(planned['parent_route_binding']==identity(canonical) and json.loads(canonical)['route']==ROUTE,'親route exact byte')
    for row in planned['bindings']:need(raw[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'入場地形とwarp全byte')
    need(planned['warp_owner']['source']==dict(id=0,xy=[19,25],elevation=0,target_warp=1,target_map=[6,0]) and planned['warp_owner']['target']['xy']==[14,9],'町warp0→博物館warp1')
    need(planned['interaction']is None and all(c['collision']==0 for c in planned['terrain']if c['map']==ORIGIN and c['xy']!=[19,25]),'博物館入場だけ・NPCへ会話しない')
    tab,_=a.parent.sectors.bank(seed,0xe000,91,a.parent.sectors.LAYOUT);party=seed[tab[1]+56:tab[1]+656]
    need(identity(party)['sha256']==a.PARTY and list(party[52:56])==PP,'実party/PP保持')
    eb=a.parent.s61e_record(seed[tab[13]+0x7d0:tab[13]+0xde6]);flags={str(f):(eb[(f-2304)//8]>>((f-2304)%8))&1 for f in range(4372,4379)}
    need(flags==planned['initial_expanded_flags'],'町type3でジムreset済')
    blocked={tuple(o['xy'])for o in planned['town']['objects']if not o['flag']or not flags.get(str(o['flag']),0)}
    need(not any(tuple(xy)in blocked for xy in ROUTE),'有効objectを踏まない')
    legacy,vars=a.parent.sectors.legacy_state(seed,tab)
    for flag in [2083,1697,1412,1440]:need(legacy[flag//8]>>(flag%8)&1,'badge/leader/trainer勝利保持')
    bag,money=a.parent.shared.bag(seed,tab);need(money==23164 and sum(q for item,q in bag['key_items']if item==274)==1,'封書一個保持')
    return dict(status='STATIC_SAVE92_MUSEUM_ENTRY_ONLY',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,terrain=planned['terrain'],warp_owner=planned['warp_owner'],initial_flags=flags,binding_count=len(planned['bindings']),native_route_accepted=False)

def scope(o):
    need(o['map']in(ORIGIN,DESTINATION) and o['save_counter']==91 and o['party_count']==4 and o['rp']==0,'入場だけの新区間')
    need(o['callback2']not in(m.BATTLE,TRANSITION) and o['battle_flags']==o['battle_outcome']==0,'未知戦闘は決定せず停止')

def progress(s,inspection):
    start(s.last);route=[START]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before and s.last['map']==ORIGIN,'直前の町位置')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,48));scope(o)
            if target==[19,25] and(o['map']==DESTINATION or o['lock']or o['callback2']!=m.FIELD):break
            idle(o,91);need(o['map']==ORIGIN and o['xy']in(before,target),'1tile通常移動・未指定eventなし')
            if o['xy']==target:route.append(target);break
        else:return route,None,dict(kind='unpassed_edge',before=before,target=target,attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
    for attempt in range(8):
        o=s.last;scope(o)
        if o['map']==DESTINATION and o['callback2']==m.FIELD and o['lock']==0:break
        if o['map']==ORIGIN and o['callback2']==m.FIELD and o['lock']==0:
            need(o['xy']==[19,25],'入口warp以外は追加入力しない');s.step((64,8),(0,180))
        else:s.step((0,180))
    else:raise ValueError('有限入場warp待機上限')
    o=s.last;idle(o,91);need(o['map']==DESTINATION and o['xy']in([14,9],[14,8]),'博物館warp1/自動北1歩を実測')
    return route,None,dict(kind='new_museum_entry',trigger=[19,25],map=o['map'],xy=o['xy'],facing=o['facing'],observation=len(s.observations)-1),[]

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,91);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(91,92),'新Save92だけ')
        if o['save_counter']==92 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,92);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==55 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save91原本55member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save91 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save91開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save91-record-terminal.json',inherited.terminal(37186524023,'636f5f15f23a7bdc2b3400675f40286434e256b4',111389491487,['success']*11))
        need(state['story_save91']['story_fast_save']==a.OUTPUT,'正式Save91親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection)
        if frontier['kind']in('unpassed_edge',):
            result=s.quit();need(s.save.read_bytes()==seed,'未発火なら入力SaveRTC全保持/通常保存しない')
            write(ART/'stopped.json',dict(status='STOPPED_APPROACH_WITHOUT_NEW_EVENT',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,inspection=inspection,route=route,frontier=frontier,final=s.last,progress=result,native_processes=1,ordinary_saves=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0))
            return
        need(frontier['kind']in('new_museum_entry',),'最初の新境界だけ保存')
        if episode is not None:need(episode['trainer']and episode['outcome']==1,'trainer通常勝利だけ')
        final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,92);need(c.last['map']==final['map'] and c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE92_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=True,outside_route503_reached=True,inner_floor_entered=True,hole_descent_observed=False,hole_descent_previously_accepted=True,mansion_exit_previously_accepted=True,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,second_diglett_previously_accepted=True,third_diglett_previously_accepted=True,fourth_diglett_previously_accepted=True,fifth_diglett_previously_accepted=True,sixth_diglett_previously_accepted=True,seventh_diglett_previously_accepted=True,trainer132_previously_accepted=True,trainer160_previously_accepted=True,eighth_diglett_previously_accepted=True,leader417_previously_accepted=True,ninth_diglett_previously_accepted=True,tenth_diglett_previously_accepted=True,eleventh_diglett_previously_accepted=True,gym_leader_defeated=True,gym_exit_observed=True,gym_exit_accepted=True,museum_entry_observed=True,museum_entry_accepted=False,gym_entered=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,statue_paper_observed=True,paper_obtained=True,paper_consumed_or_delivered=False,paper_acceptance_pending=False,normal_recovery_required=False,pp_recovery_accepted=True,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save91'])
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











