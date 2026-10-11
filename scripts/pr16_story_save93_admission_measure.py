#!/usr/bin/env python3
"""Save92より先の新しい通常入力だけ。新しい博物館受付50円を通常入力で完了しSave93を作る。"""
from __future__ import annotations
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save92_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='6a02e79f4b88685e8de8199edde4b335cb6a30e9'
OUT=ROOT/'.local/pr16-story-save93';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save93_admission_measure.py','tests/test_pr16_story_save93_admission.py','.github/workflows/pr16-story-save93.yml'}
PP=[3,9,8,2]
TRANSITION=134569577 # 失敗原本の16,5で観測した野生戦直前callbackだけ
PREP='content/modernization/pr16_story_save93_admission_owner.json'
CODE.add(PREP)
TERRAIN='content/modernization/pr16_story_save50_preparation.json'
ORIGIN=[6,0]
DESTINATION=[6,0]
START=[14,9]
classify=a.m.classify

def direction(before,after):
    delta=tuple(b-a for a,b in zip(before,after))
    need(delta in((0,1),(0,-1),(1,0),(-1,0)),'1tile隣接だけ')
    return {(0,1):128,(0,-1):64,(1,0):16,(-1,0):32}[delta]

def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_outcome']in(0,1),'博物館1階/2階の操作可能fieldだけ')

def start(o):
    idle(o,92);need(o['map']==ORIGIN and o['xy']==START and o['facing']==2 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER,'Save92唯一の親')

ROUTE=[[14, 9], [14, 8], [14, 7], [14, 6], [14, 5]]
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save92/同一候補')
    p=json.loads((ROOT/PREP).read_bytes());need(p['expected']['route']==ROUTE and p['coord']['xy']==[14,5] and p['coord']['script']==135787062 and p['coord']['variable']==0x4061 and p['coord']['value']==0,'14,5の未払coord event')
    for row in [p['coord']]+p['instructions']+p['movements']:
        b=bytes.fromhex(row['hex']);need(raw[row['address']-0x8000000:row['address']-0x8000000+len(b)]==b,'受付owner全byte')
    for ptr,row in p['texts'].items():
        b=bytes.fromhex(row['hex']);need(raw[int(ptr)-0x8000000:int(ptr)-0x8000000+len(b)]==b,'受付dialog全byte')
    instructions={row['address']:row['hex'] for row in p['instructions']}
    need(instructions[0x817f2b3]=='913200000000' and instructions[0x817f2c6]=='1661400100' and instructions[0x817f258]=='0905','50円除去/4061set/yes-noのowner')
    tab,_=a.parent.sectors.bank(seed,0,92,a.parent.sectors.LAYOUT);party=seed[tab[1]+56:tab[1]+656]
    need(identity(party)['sha256']==a.PARTY and list(party[52:56])==PP,'party600byte保持')
    legacy,vars=a.parent.sectors.legacy_state(seed,tab);need(vars[0x61]==0,'博物館未払4061=0')
    bag,money=a.parent.shared.bag(seed,tab);need(money==23164 and sum(q for item,q in bag['key_items']if item==274)==1,'支払前23164円/紙保持')
    return dict(status='STATIC_SAVE93_MUSEUM_ADMISSION_ONLY',preparation=identity((ROOT/PREP).read_bytes()),route=ROUTE,coord=p['coord'],expected=p['expected'],instruction_count=len(p['instructions']),native_route_accepted=False)

def scope(o):
    need(o['map']==ORIGIN and o['callback2']==m.FIELD and o['party_count']==4 and o['save_counter']==92 and o['rp']==0 and o['battle_flags']==o['battle_outcome']==0 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['live_xy']==[x+7 for x in o['xy']],'受付だけ・戦闘/warp/party/保存変化なし')

def admission(s):
    dialogue=[];o=s.last
    for _ in range(12):
        scope(o);need(o['xy']in([14,5],[15,5],[14,4],[15,4]),'固定受付scriptの移動scope')
        if o['lock']==0:
            idle(o,92);return dict(kind='new_museum_admission',trigger=[14,5],map=o['map'],xy=o['xy'],facing=o['facing'],dialogue_observations=dialogue,observation=len(s.observations)-1)
        need(o['lock']==1 and m.screen(s).startswith(b'P6\n240 160\n255\n'),'既知50円yes/no受付だけを1ページずつ確認')
        dialogue.append(len(s.observations)-1);o=s.step((1,2),(0,180))
    raise ValueError('受付12ページ有限上限。未知継続や自動再走なし')

def progress(s,inspection):
    start(s.last);route=[START]
    for before,target in zip(ROUTE,ROUTE[1:]):
        need(s.last['xy']==before,'新北4歩だけ')
        o=s.step((64,8),(0,48));scope(o)
        if target==[14,5]:
            need(o['xy']==target and o['lock']==1 and o['facing']==4,'原失敗で確認した自動受付開始')
            route.append(target);return route,None,admission(s),[]
        idle(o,92);need(o['xy']==target and o['facing']==2,'受付以前は通常北1歩');route.append(target)
    raise ValueError('受付eventなしでは保存しない')

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,92);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(92,93),'新Save93だけ')
        if o['save_counter']==93 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,93);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==70 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save92原本70member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save92 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save92開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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

def prior_failure():
    terminal=inherited.terminal(37188126911,'6a02e79f4b88685e8de8199edde4b335cb6a30e9',111394391365,['success','success','success','failure','skipped','success','success','success'])
    meta,z=a.transport.archive(11298047173,37188126911,dict(size=22915,sha256='9978589e20a53c5303e6dd56a9313e9167d4d3760f1f17c1bbff204e41f3c3e6'),'6a02e79f4b88685e8de8199edde4b335cb6a30e9')
    with z:
        mf=json.loads(z.read('manifest.json'));need(len(mf)==12 and set(z.namelist())==set(mf)|{'manifest.json'},'初回失敗全12member')
        for name,b in mf.items():need(identity(z.read(name))==b,'初回失敗member '+name)
        e=json.loads(z.read('progress/execution.json'));need(e['initial_save']==e['final_save']==a.OUTPUT and e['observations']==5 and e['native_end']['inputs']==20,'初回native1/未保存/入力全保持')
        failure=json.loads(z.read('failure.json'));need(failure['native_processes']==1 and failure['message']=='博物館1階/2階の操作可能fieldだけ','未知自動受付で安全停止')
    write(ART/'failed-attempt.json',dict(terminal=terminal,artifact_id=11298047173,archive=dict(size=22915,sha256='9978589e20a53c5303e6dd56a9313e9167d4d3760f1f17c1bbff204e41f3c3e6'),failure=failure,execution=e,accepted=False,native_processes=1,accepted_case_reruns=0,reason_ja='原計画がcoord14,5/var4061の50円受付を未登録。新ROM根拠で受付だけへ縮小し、その未完区間を修正検証。元38成功controllerは原log継承。'))

def main():
    h.d.current();state=h.source_check();need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'新区間初回のみ')
    protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        write(ART/'save92-record-terminal.json',inherited.terminal(37187614083,'82f22a40ecc60f5f26468531d10ca25b0db3ee7c',111392808208,['success']*11))
        need(state['story_save92']['story_fast_save']==a.OUTPUT,'正式Save92親')
        prior_failure()
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection)
        if frontier['kind']in('unpassed_edge',):
            result=s.quit();need(s.save.read_bytes()==seed,'未発火なら入力SaveRTC全保持/通常保存しない')
            write(ART/'stopped.json',dict(status='STOPPED_APPROACH_WITHOUT_NEW_EVENT',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,inspection=inspection,route=route,frontier=frontier,final=s.last,progress=result,native_processes=1,ordinary_saves=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0))
            return
        need(frontier['kind']in('new_museum_admission',),'最初の新境界だけ保存')
        if episode is not None:need(episode['trainer']and episode['outcome']==1,'trainer通常勝利だけ')
        final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,93);need(c.last['map']==final['map'] and c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE93_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            cave_crossing_complete=True,outside_route503_reached=True,inner_floor_entered=True,hole_descent_observed=False,hole_descent_previously_accepted=True,mansion_exit_previously_accepted=True,gym_entry_previously_accepted=True,first_diglett_previously_accepted=True,second_diglett_previously_accepted=True,third_diglett_previously_accepted=True,fourth_diglett_previously_accepted=True,fifth_diglett_previously_accepted=True,sixth_diglett_previously_accepted=True,seventh_diglett_previously_accepted=True,trainer132_previously_accepted=True,trainer160_previously_accepted=True,eighth_diglett_previously_accepted=True,leader417_previously_accepted=True,ninth_diglett_previously_accepted=True,tenth_diglett_previously_accepted=True,eleventh_diglett_previously_accepted=True,gym_leader_defeated=True,gym_exit_observed=True,gym_exit_accepted=True,museum_entry_observed=True,museum_entry_accepted=True,museum_second_floor_observed=False,museum_second_floor_accepted=False,museum_admission_observed=True,museum_admission_accepted=False,gym_entered=True,letter_consumer_resolved=True,letter_handoff_requires_badge=True,statue_paper_observed=True,paper_obtained=True,paper_consumed_or_delivered=False,paper_acceptance_pending=False,normal_recovery_required=False,pp_recovery_accepted=True,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save92'])
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











