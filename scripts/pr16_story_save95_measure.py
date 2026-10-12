#!/usr/bin/env python3
"""Save94より先の新しい通常入力だけ。最初の紙引渡し完了でSave95を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save94_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='12313bd71b0ee17292127a24ab34edfcf60c5fcc'
OUT=ROOT/'.local/pr16-story-save95';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save95_measure.py','tests/test_pr16_story_save95_measure.py','.github/workflows/pr16-story-save95.yml'}
PP=[3,9,8,2]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
PREP='content/modernization/pr16_story_save95_preparation.json'
CODE.add(PREP)
NPC_VISUAL='content/modernization/pr16_story_save95_npc_visual.json';CODE.add(NPC_VISUAL)
TERRAIN='content/modernization/pr16_story_save50_preparation.json'
ORIGIN=[6,1]
DESTINATION=[6,1]
START=[11,8]
classify=a.m.classify

def direction(before,after):
    delta=tuple(b-a for a,b in zip(before,after))
    need(delta in((0,1),(0,-1),(1,0),(-1,0)),'1tile隣接だけ')
    return {(0,1):128,(0,-1):64,(1,0):16,(-1,0):32}[delta]

def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_outcome']in(0,1),'博物館1階/2階の操作可能fieldだけ')

def start(o):
    idle(o,94);need(o['map']==ORIGIN and o['xy']==START and o['facing']==4 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER,'Save94唯一の親')

ROUTE=[[11, 8], [11, 7], [11, 6], [11, 5], [10, 5], [9, 5], [8, 5], [7, 5], [6, 5], [6, 6], [6, 7], [5, 7], [4, 7], [4, 8]]
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save94/同一候補')
    planned=json.loads((ROOT/PREP).read_bytes());canonical=(ROOT/'content/modernization/pr16_story_save94_next_route.json').read_bytes()
    need(planned['parent_route_binding']==identity(canonical) and planned['route']==ROUTE==json.loads(canonical)['route'],'親route全byteと新13歩だけ')
    need(planned['candidate']==a.shared.plan.CANDIDATE and planned['input_save']==a.OUTPUT,'Save94からだけ')
    for row in planned['bindings']:need(raw[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'地形/local2/script/textの全byte')
    need(planned['interaction']==dict(xy=[4,8],facing=1,button=1) and planned['consumer_local_id']==2 and planned['consumer_xy']==[4,9] and planned['consumer_root']==149013250,'local2北隣から南向き通常会話')
    need(all(c['collision']==0 for c in planned['terrain']),'新13歩は通行可能tileだけ')
    blocked={tuple(o['xy'])for o in planned['museum']['objects']if not o['flag']}
    need(not any(tuple(xy)in blocked for xy in ROUTE),'固定NPC tileを踏まない。runtime移動は別観測')
    ins=planned['letter_owner']['instructions'];need({x['opcode']for x in ins}=={2,6,9,15,33,41,43,69,71,90,106,108},'全5nodeは既知message/item/flagだけ')
    need({x['hex']for x in ins if x['opcode']==9}=={'0902'},'全callstdは通常message、選択肢なし')
    need(planned['script_boundaries']==dict(remove_item=dict(address=149013345,item=274,quantity=1),set_flag=dict(address=149013350,flag=4382),national_dex_unlock_present=False),'引渡しremove274x1/set4382のみ')
    tab,_=a.parent.sectors.bank(seed,0,94,a.parent.sectors.LAYOUT);party=seed[tab[1]+56:tab[1]+656]
    need(identity(party)['sha256']==a.PARTY and list(party[52:56])==PP,'実party/PP保持')
    eb=a.parent.s61e_record(seed[tab[13]+0x7d0:tab[13]+0xde6]);need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==0 and(eb[259]>>4)&1==0,'紙4383有/引渡し4382無/完了4380無')
    legacy,vars=a.parent.sectors.legacy_state(seed,tab);need(vars[0x61]==1,'受付支払済4061=1。受付再走なし')
    for flag in [2083,1697,1412,1440]:need(legacy[flag//8]>>(flag%8)&1,'badge/leader/trainer勝利保持')
    bag,money=a.parent.shared.bag(seed,tab);need(money==23114 and sum(q for item,q in bag['key_items']if item==274)==1,'封書一個保持')
    return dict(status='STATIC_SAVE95_LETTER_HANDOFF_ONLY',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,terrain=planned['terrain'],interaction=planned['interaction'],script_boundaries=planned['script_boundaries'],binding_count=len(planned['bindings']),native_route_accepted=False,letter_handoff_accepted=False)

def scope(o):
    need(o['map']==ORIGIN and o['save_counter']==94 and o['party_count']==4 and o['rp']==0 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'紙引渡しまでparty/flash保持')
    need(o['callback2']==m.FIELD and o['battle_flags']==o['battle_outcome']==0,'未知callback/戦闘は決定せず停止')

def event_scope(o):
    scope(o);need(o['xy']==[4,8] and o['live_xy']==[11,15] and o['facing']==1,'local2北隣/南向きだけ')

def npc_in_front(raw):
    need(raw[:15]==b'P6\n240 160\n255\n' and len(raw)==115215,'既存240x160実PPMだけ')
    v=json.loads((ROOT/NPC_VISUAL).read_bytes());need(v['target_origin']==[112,80] and v['shape']==[16,24] and len(v['sparse_pixels'])==128,'原画由来local2内部128pixel')
    ox,oy=v['target_origin']
    def matches(mirror):
        for x,y,rgb in v['sparse_pixels']:
            px=ox+(15-x if mirror else x);at=15+3*((oy+y)*240+px)
            if raw[at:at+3]!=bytes(rgb):return False
        return True
    return matches(False) or matches(True)

def wait_for_npc(s):
    waited=[];stable=0
    for _ in range(240):
        event_scope(s.last);need(s.last['lock']==0,'会話前fieldのみ')
        matched=npc_in_front(m.screen(s));stable=stable+1 if matched else 0
        if stable==2:return waited
        waited.append(len(s.observations)-1);s.step((0,30))
    raise ValueError('local2の正面spriteを連続確認できないため停止。盲目的Aなし')

def progress(s,inspection):
    start(s.last);route=[START]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before,'直前の2階位置')
        for attempt in range(3):
            o=s.step((direction(before,target),8),(0,48));scope(o);idle(o,94)
            need(o['xy']in(before,target),'1tile通常移動・未指定eventなし')
            if o['xy']==target:route.append(target);break
        else:return route,None,dict(kind='unpassed_edge',before=before,target=target,attempts=3,map=o['map'],xy=o['xy'],observation=len(s.observations)-1),[]
    event_scope(s.last);need(s.last['lock']==0,'南向き確認後だけ通常会話')
    npc_wait=wait_for_npc(s)
    o=s.step((1,2),(0,180));event_scope(o);need(o['lock']==1,'最初のlocal2会話を観測')
    dialogue=[]
    for _ in range(40):
        event_scope(o)
        if o['lock']==0:
            idle(o,94)
            return route,None,dict(kind='new_letter_handoff_event',map=ORIGIN,xy=[4,8],facing=1,npc_wait_observations=npc_wait,dialogue_observations=dialogue,observation=len(s.observations)-1),[]
        need(o['lock']==1 and m.screen(s).startswith(b'P6\n240 160\n255\n'),'固定message scriptの実画面/lock確認後だけ1ページ進める')
        dialogue.append(len(s.observations)-1);o=s.step((1,2),(0,180))
    raise ValueError('40ページ有限上限。未知UIへ継続入力/自動再走しない')

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,94);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(94,95),'新Save95だけ')
        if o['save_counter']==95 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,95);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==56 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save94原本56member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save94 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save94開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save94-record-terminal.json',inherited.terminal(37190224812,'037236ba10f1e531eeade211f69e6732734d2ae4',111400657915,['success']*11))
        need(state['story_save94']['story_fast_save']==a.OUTPUT,'正式Save94親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection)
        if frontier['kind']in('unpassed_edge',):
            result=s.quit();need(s.save.read_bytes()==seed,'未発火なら入力SaveRTC全保持/通常保存しない')
            write(ART/'stopped.json',dict(status='STOPPED_APPROACH_WITHOUT_NEW_EVENT',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,inspection=inspection,route=route,frontier=frontier,final=s.last,progress=result,native_processes=1,ordinary_saves=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0))
            return
        need(frontier['kind']in('new_letter_handoff_event',),'最初の新境界だけ保存')
        if episode is not None:need(episode['trainer']and episode['outcome']==1,'trainer通常勝利だけ')
        final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,95);need(c.last['map']==final['map'] and c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE95_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=True,outside_route503_reached=True,inner_floor_entered=True,hole_descent_observed=False,hole_descent_previously_accepted=True,mansion_exit_previously_accepted=True,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,second_diglett_previously_accepted=True,third_diglett_previously_accepted=True,fourth_diglett_previously_accepted=True,fifth_diglett_previously_accepted=True,sixth_diglett_previously_accepted=True,seventh_diglett_previously_accepted=True,trainer132_previously_accepted=True,trainer160_previously_accepted=True,eighth_diglett_previously_accepted=True,leader417_previously_accepted=True,ninth_diglett_previously_accepted=True,tenth_diglett_previously_accepted=True,eleventh_diglett_previously_accepted=True,gym_leader_defeated=True,gym_exit_observed=True,gym_exit_accepted=True,museum_entry_observed=True,museum_entry_accepted=True,museum_second_floor_observed=False,museum_second_floor_accepted=True,letter_handoff_event_completed=True,letter_handoff_accepted=False,museum_admission_observed=False,museum_admission_previously_accepted=True,gym_entered=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,statue_paper_observed=True,paper_obtained=True,paper_consumed_or_delivered=False,paper_acceptance_pending=True,normal_recovery_required=False,pp_recovery_accepted=True,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save94'])
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











