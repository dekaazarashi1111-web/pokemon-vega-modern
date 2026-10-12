#!/usr/bin/env python3
"""Save99から実画面で動的Ranger正面を確認し町の連続イベント最初のfieldまで。"""
from __future__ import annotations
import json,os,sys,struct
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save99_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='15b3f31edf44c7a5fd56b72f124f4f34693c2057'
OUT=ROOT/'.local/pr16-story-save100';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
PREP='content/modernization/pr16_story_save100_preparation.json'
CODE={'scripts/pr16_story_save100_measure.py','tests/test_pr16_story_save100_measure.py','.github/workflows/pr16-story-save100.yml',PREP}
PP=[3,9,8,2];TRANSITION=134569577
ORIGIN=[3,23];DESTINATION=[3,2];START=[18,28]
direction=a.m.direction
FACING={16:4,32:3,64:2,128:1}

def idle(o,counter):
    need(o['map']in(ORIGIN,DESTINATION)and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[x+7 for x in o['xy']]and o['battle_flags']==o['battle_outcome']==0,'道路/町の操作可能fieldだけ')
def start(o):
    idle(o,99);need(o['map']==ORIGIN and o['xy']==START and o['facing']==3 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH and o['ledger_sha256']==a.COLD_LEDGER,'正式Save99唯一の親')
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'正式Save99/同一候補')
    p=json.loads((ROOT/PREP).read_bytes());canonical=(ROOT/'content/modernization/pr16_story_save99_next_route.json').read_bytes()
    need(p['parent_route_binding']==identity(canonical),'親dynamic計画exact binding')
    need(p['candidate']==a.shared.plan.CANDIDATE and p['input_save']==a.OUTPUT,'ROM/save固定')
    for row in p['bindings']:need(raw[row['address']-0x8000000:row['address']-0x8000000+row['size']].hex()==row['hex'],'地形/object/会話/町自動script全byte')
    need(all(t['collision']==0 and t['elevation']==3 and t['behavior']in(0,33)for t in p['terrain']),'草/warp/階段なしの接近域')
    need(not any(c['xy']in[t['xy']for t in p['terrain']]for c in p['coord_events']),'接近域の座標eventなし')
    need(p['ranger']['local_id']==9 and p['ranger']['movement_ranges']==[2,2]and p['ranger']['script']==149013360,'実Ranger識別')
    refs=p['town_event_owner']['map_script_refs'];need(len(refs)==1 and refs[0]['value']==0x4072 and refs[0]['operand']==2,'warp直後の町自動event4072=2')
    tab,_=a.parent.sectors.bank(seed,0xe000,99,a.parent.sectors.LAYOUT);party=seed[tab[1]+56:tab[1]+656]
    need(identity(party)['sha256']==a.PARTY and list(party[52:56])==PP and all(struct.unpack_from('<I',party,100*i+80)[0]==0 for i in range(4)),'実party/PP/status0')
    legacy,variables=a.parent.sectors.legacy_state(seed,tab);need((variables[0x21],variables[0x22],variables[0x61],variables[0x71],variables[0x72])==(91,1,1,9,1),'歩数/入館/story親')
    eb=a.parent.s61e_record(seed[tab[13]+0x7d0:tab[13]+0xde6]);need((eb[259]>>7)&1==1 and(eb[259]>>6)&1==1 and(eb[259]>>4)&1==0,'4383/4382保持、4380未完')
    return dict(status=p['status'],preparation=identity((ROOT/PREP).read_bytes()),terrain=p['terrain'],visual_locator=p['visual_locator'],binding_count=len(p['bindings']),town_autostart_var4072=2,expected_completed_var4072=3,native_event_accepted=False)

def locate(raw,player,calibration):
    need(raw.startswith(b'P6\n240 160\n255\n')and len(raw)==115215,'240x160 RGB原画')
    data=raw[15:];colors={tuple(c)for c in calibration['colors']};points=[(i%240,i//240)for i in range(38400)if tuple(data[i*3:i*3+3])in colors]
    if not points:return None
    xs,ys=zip(*points);left,top,right,bottom=min(xs),min(ys),max(xs),max(ys)
    mask=sorted([[x-left,y-top]for x,y in points]);templates=[x['mask']for x in calibration['templates']];templates += [sorted([[11-x,y]for x,y in t])for t in templates]
    if right-left!=11 or mask not in templates or(left-114)%16 or(top-68)%16:return None
    xy=[player[0]+(left-114)//16,player[1]+(top-68)//16]
    need(16<=xy[0]<=20 and 25<=xy[1]<=29,'Rangerのrange2内だけ。紫hatの他NPCを同一視しない')
    return dict(xy=xy,bbox=[left,top,right,bottom],pixels=len(points),mask_sha256=identity(bytes(v for point in mask for v in point))['sha256'])
def scope(o):
    need(o['map']in(ORIGIN,DESTINATION)and o['save_counter']==99 and o['party_count']==4 and o['rp']==0 and o['party_sha256']==a.PARTY and o['flash_sha256']==a.FLASH,'最初のeventまでparty/HP/PP/flash保持')
    need(o['callback2']not in(m.BATTLE,TRANSITION)and o['battle_flags']==o['battle_outcome']==0,'未知戦闘は決定しない')
def next_tile(player,npc,allowed):
    # 安全床だけで、現在のNPC正面に隣接する最短経路を毎観測再計算。
    from collections import deque
    q=deque([tuple(player)]);seen={tuple(player):None};target=None
    while q:
        at=q.popleft()
        if sum(abs(a-b)for a,b in zip(at,npc))==1:target=at;break
        for dx,dy in [(1,0),(0,1),(-1,0),(0,-1)]:
            n=(at[0]+dx,at[1]+dy)
            if list(n)in allowed and list(n)!=npc and n not in seen:seen[n]=at;q.append(n)
    need(target is not None,'安全床からの動的隣接経路')
    if list(target)==player:return None
    while seen[target]!=tuple(player):target=seen[target]
    return list(target)
def progress(s,inspection):
    start(s.last);route=[START];observed=[];talk=[];steps=0;allowed=[t['xy']for t in inspection['terrain']];cal=inspection['visual_locator']
    for _ in range(160):
        o=s.last;scope(o);idle(o,99);need(o['map']==ORIGIN,'接近中は道路のみ')
        found=locate(m.screen(s),o['xy'],cal);observed.append(dict(observation=len(s.observations)-1,player=o['xy'],facing=o['facing'],ranger=found))
        if found is None:s.step((0,4));continue
        npc=found['xy'];target=next_tile(o['xy'],npc,allowed)
        if target is None:
            key=direction(o['xy'],npc)
            if o['facing']!=FACING[key]:
                before=o['xy'];s.step((key,1),(0,16));scope(s.last);need(s.last['xy']==before,'隣接NPCへの旋回は移動なし');continue
            # 連続2frameの同じgrid位置と正面で初めて通常A。推定初期座標を使わない。
            check=s.step((0,1));scope(check);idle(check,99);found2=locate(m.screen(s),check['xy'],cal)
            observed.append(dict(observation=len(s.observations)-1,player=check['xy'],facing=check['facing'],ranger=found2))
            if found2 is None or found2['xy']!=npc or check['xy']!=o['xy']or check['facing']!=FACING[key]:continue
            talk.append(dict(before=len(s.observations)-1,player=check['xy'],facing=check['facing'],ranger=npc,consecutive_position_confirmed=True))
            s.step((1,2),(0,60));scope(s.last)
            if s.last['lock']or s.last['map']==DESTINATION:break
            need(len(talk)<6,'A miss有限上限。新NPC会話を推定しない');continue
        need(steps<30,'friendship周期前の有限接近上限');before=o['xy'];key=direction(before,target)
        s.step((key,8),(0,48));scope(s.last);idle(s.last,99);need(s.last['xy']in(before,target),'単tile/旋回だけ。NPC移動は次画面で再観測')
        if s.last['xy']==target:route.append(target);steps+=1
    else:raise ValueError('動的NPC正面確認の有限上限')
    # 4382分岐は町へwarp後、自動4072=2の解放eventを継続する。
    event_start=len(s.observations)-1
    for _ in range(120):
        o=s.last;scope(o)
        if o['map']==DESTINATION and o['callback2']==m.FIELD and o['lock']==0:
            idle(o,99)
            return route,None,dict(kind='ranger_town_chain_first_field',map=o['map'],xy=o['xy'],facing=o['facing'],observation=len(s.observations)-1,event_start=event_start,visual_observations=observed,talk_attempts=talk,approach_steps=steps),[]
        need(o['map']in(ORIGIN,DESTINATION),'Ranger連鎖外へ進めない')
        # 固定scriptはmsgbox2/fade/movementのみ、選択肢/買物/戦闘なし。
        s.step(*(((1,2),(0,60))if o['callback2']==m.FIELD and o['lock']else((0,60),)))
    raise ValueError('Ranger/町自動script有限上限')

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,99);target=s.last['xy'];where=s.last['map'];s.step((8,2),(0,60))
    cursor=menu_index(m.screen(s));need(cursor==0,'cold開始の既定menu位置')
    for _ in range(8):
        if cursor==4:break
        previous=cursor;s.step((128,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor in(previous,previous+1),'1行ずつ実画面cursorを確認')
    need(cursor==4,'レポート選択確認後だけ決定');s.step((1,2),(0,60))
    s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==target and o['map']==where and o['save_counter']in(99,100),'新Save100だけ')
        if o['save_counter']==100 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,100);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==119 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save99原本119member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save99 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save99開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save99-record-terminal.json',inherited.terminal(37197809471,'8d12d98794bb91673597b074e2ea2be11665f5ae',111423190429,['success']*11))
        need(state['story_save99']['story_fast_save']==a.OUTPUT,'正式Save99親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        route,episode,frontier,teleports=progress(s,inspection)
        if frontier['kind']=='unpassed_edge':
            result=s.quit();need(s.save.read_bytes()==seed,'未通過なら入力SaveRTC全保持/通常保存しない')
            write(ART/'stopped.json',dict(status='STOPPED_APPROACH_WITHOUT_NEW_EVENT',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,inspection=inspection,route=route,frontier=frontier,final=s.last,progress=result,native_processes=1,ordinary_saves=0,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0));return
        need(frontier['kind']=='ranger_town_chain_first_field'and episode is None and not teleports,'Ranger連鎖の最初fieldだけ保存')
        final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,100);need(c.last['map']==final['map']and c.last['xy']==final['xy']and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE100_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,route=route,battle=episode,teleport=teleports,frontier=frontier,final=final,continued=c.last,progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,ranger_approach_observed=True,ranger_approach_accepted=False,ranger_interaction_observed=True,letter_handoff_previously_accepted=True,museum_exit_previously_accepted=True,national_dex_unlocked=False,natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,release_ready=False,artifact_excludes=['existing ROM','runner','runtime','input Save99'])
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
