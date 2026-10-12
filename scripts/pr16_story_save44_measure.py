#!/usr/bin/env python3
"""Save43より先の新しい通常入力だけ。道具/手持ち確認と通常並替・Save44だけ。PP回復や新戦闘は主張しない。"""
from __future__ import annotations
import json,os,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save43_accept as a
import pr16_story_save24_record as inherited
from pr16_story_after_maori import need,identity,write,map_view,unpack
from pr16_story_after_maori_session import Session
import pr16_story_save25_measure as m
h=m.h
BASE='a738314f2c7f31766902cd452ca7f591473fb28c'
OUT=ROOT/'.local/pr16-story-save44';ART=OUT/'artifact';ASSETS=OUT/'private-inputs'
CODE={'scripts/pr16_story_save44_measure.py','tests/test_pr16_story_save44_measure.py','.github/workflows/pr16-story-save44.yml'}
ORIGIN=[3,44]
PARTY_UI=135394217
BAG_UI=135301605
PP=[15,10,15,20]
CP='content/modernization/pr16_story_save44_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE44_JA.md'
PREP='content/modernization/pr16_story_save40_preparation.json'
def idle(o,counter):
    need(o['map']==ORIGIN and o['xy']==[39,12] and o['callback2']==m.FIELD and o['lock']==0 and o['party_count']==4 and o['rp']==0 and o['save_counter']==counter and o['live_xy']==[46,19] and o['battle_flags']==o['battle_outcome']==0,'同じ座標/戦闘なしfieldだけ')
def swap_bytes(party):
    need(type(party)is bytes and len(party)==600,'600byte partyだけ')
    return party[100:200]+party[:100]+party[200:]
def inspect(raw,seed):
    need(identity(raw)==a.shared.plan.CANDIDATE and identity(seed)==a.OUTPUT,'Save43/同一candidateだけ')
    table,checks=a.parent.sectors.bank(seed,0xe000,43,a.parent.sectors.LAYOUT)
    bag,money=a.parent.shared.bag(seed,table)
    need(money==14264 and all(i==0 and q==0 for i,q in bag['items']) and all(i==0 and q==0 for i,q in bag['berries']),'道具/きのみ空。host補充しない')
    party=seed[table[1]+56:table[1]+656]
    need(identity(party)['sha256']==a.PARTY,'全party固定')
    mons=[dict(slot=i,species=struct.unpack_from('<H',party,100*i+32)[0],moves=list(struct.unpack_from('<4H',party,100*i+44)),pp=list(party[100*i+52:100*i+56]),hp=list(struct.unpack_from('<HH',party,100*i+86)))for i in range(4)]
    need(mons[0]['species']==150 and mons[0]['pp']==[0]*4 and mons[0]['hp']==[314,354],'枯渇した主力の実状態')
    need(mons[1]['species']==850 and mons[1]['moves']==[337,89,280,332]and mons[1]['pp']==PP and mons[1]['hp']==[294,294],'既存控えの実PP/HP')
    prep=json.loads((ROOT/PREP).read_bytes());need(len(prep['allcells'])==1440,'地形原本を再利用')
    # まだ進入しない南側接続先だけ追加読取。warp到達や回復受入を主張しない。
    from tools.t02.rom_inventory import RomImage,MAP_GROUPS_POINTER_SITE
    ri=RomImage('save44-recovery-candidate',raw);groups=ri.u32(MAP_GROUPS_POINTER_SITE)
    south=map_view(raw,groups,3,23)
    return dict(status='SAVE43_BAG_PARTY_AND_RECOVERY_CANDIDATES_ONLY',bag=bag,money=money,party=mons,party_before=a.PARTY,party_after_swap=identity(swap_bytes(party))['sha256'],no_pp_items=True,pp_restored=False,healing_site_reached=False,static_south_map=south,existing_route504_cells_reused=1440,new_native_route_accepted=False)
def guard_ui(o,callback,party):
    need(o['map']==ORIGIN and o['xy']==[39,12]and o['live_xy']==[46,19]and o['save_counter']==43 and o['rp']==0 and o['party_count']==4 and o['battle_flags']==o['battle_outcome']==0 and o['flash_sha256']==a.FLASH and o['party_sha256']==party and o['callback2']==callback,'通常UIのみ。保存/戦闘/partyの予期しない変更なし')
def menu_to(s,target):
    cursor=menu_index(m.screen(s))
    for _ in range(7):
        if cursor==target:return cursor
        key=128 if cursor<target else 64;previous=cursor
        s.step((key,2),(0,20));cursor=menu_index(m.screen(s))
        need(cursor==previous+(1 if key==128 else -1),'main menu実cursorを1行ずつ照合')
    raise ValueError('main menu有限上限')
def progress(s,inspection):
    idle(s.last,43);need(s.last['party_sha256']==a.PARTY and s.last['flash_sha256']==a.FLASH,'Save43親')
    s.step((8,2),(0,60));menu_to(s,2);s.step((1,2),(0,180));guard_ui(s.last,BAG_UI,a.PARTY)
    bag_observations=[len(s.observations)-1]
    # 通常Bagのポケット移動だけ。道具選択/使用/捨てるは行わない。
    for _ in range(2):
        s.step((16,2),(0,90));guard_ui(s.last,BAG_UI,a.PARTY);bag_observations.append(len(s.observations)-1)
    s.step((2,2),(0,180));guard_ui(s.last,m.FIELD,a.PARTY)
    # Bag終了は通常menuへ戻る。実cursorからpartyを選ぶ。
    menu_to(s,1);s.step((1,2),(0,180));guard_ui(s.last,PARTY_UI,a.PARTY)
    party_begin=len(s.observations)-1
    # Save13で確認済みの通常いれかえ操作。現在は2番目のオノノクスを先頭へ。
    for key,frames in [(128,20),(1,120),(128,20),(1,90),(64,20)]:
        s.step((key,2),(0,frames));guard_ui(s.last,PARTY_UI,a.PARTY)
    s.step((1,2),(0,180));guard_ui(s.last,PARTY_UI,inspection['party_after_swap']);swapped=len(s.observations)-1
    s.step((2,2),(0,120));guard_ui(s.last,m.FIELD,inspection['party_after_swap'])
    s.step((2,2),(0,120));idle(s.last,43)
    need(s.last['party_sha256']==inspection['party_after_swap'],'通常並替の全600byte一致')
    return dict(bag_observations=bag_observations,party_begin=party_begin,swapped_observation=swapped,field_return=len(s.observations)-1,pp_restored=False,item_uses=0,money_cost=0,party_order_changes=1,travel_steps=0)

MENU_ARROW='7705d612f1603802f40ea0b7f47bb5bad299300872da8d93ed06212eb9a4a353'
REPORT_LABEL='713a5de624898bc4f1fa230a1c3a4c33a1eb79c627e2394c798e46698597f5f4'
def menu_index_from_digests(arrows,label):
    need(label==REPORT_LABEL and len(arrows)==7,'通常メニューのレポートlabelを確認')
    choices=[i for i,x in enumerate(arrows)if x==MENU_ARROW];need(len(choices)==1,'通常メニューcursorは1個');return choices[0]
def menu_index(raw):
    return menu_index_from_digests([m.digest(raw,[176,10+i*15,182,19+i*15])for i in range(7)],m.digest(raw,[184,66,233,81]))
def save(s):
    idle(s.last,43);s.step((8,2),(0,60));menu_to(s,4)
    s.step((1,2),(0,60));s.step((1,2),(0,60));s.step((1,2),(0,180))
    for _ in range(40):
        o=s.step((0,30));need(o['xy']==[39,12]and o['map']==ORIGIN and o['save_counter']in(43,44),'新Save44だけ')
        if o['save_counter']==44 and o['callback2']==m.FIELD and o['lock']==0:break
    idle(o,44);need(o['flash_sha256']!=a.FLASH,'通常保存完了');return o

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
        need(len(bindings)==105 and set(z.namelist())==set(bindings)|{'manifest.json'},'全Save43原本105member')
        for n,b in bindings.items():need(identity(z.read(n))==b,'Save43 member '+n)
        raw=z.read('story-fast.srm');need(identity(raw)==a.OUTPUT,'Save43開始点固定');(ASSETS/'input.srm').write_bytes(raw);(ASSETS/'input.srm').chmod(0o444)
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
        write(ART/'save43-record-terminal.json',inherited.terminal(37134410241,'19e979ba428a69fc5b3acbee8e004657bb350be8',111235875067,['success']*11))
        need(state['story_save43']['story_fast_save']==a.OUTPUT,'正式Save43親')
        runtime=restore();seed=(ASSETS/'input.srm').read_bytes()
        inspection=inspect((ASSETS/'candidate.gba').read_bytes(),seed);write(ART/'inspection.json',inspection)
        s=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',seed,ART/'progress');sessions.append(s)
        actions=progress(s,inspection);final=save(s);result=s.quit();saved=s.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        c=Session(runtime,ASSETS/'candidate.gba',ASSETS/'runner',saved,ART/'continue');sessions.append(c)
        idle(c.last,44);need(c.last['xy']==final['xy'] and c.last['party_sha256']==final['party_sha256'],'cold位置/party')
        c.step((0,120));cold=c.quit();(ART/'cold.srm').write_bytes(c.save.read_bytes());need(saved==c.save.read_bytes(),'全Save/RTC')
        need(h.d.bindings(protected)==protected,'全受入source不変')
        report=dict(status='MEASURED_SAVE44_AWAITING_VISUAL_AND_INDEPENDENT_ACCEPTANCE',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            input_save=a.OUTPUT,output_save=identity(saved),inspection=inspection,actions=actions,final=final,continued=c.last,
            progress=result,independent_continue=cold,screen_count=len(s.observations)+len(c.observations),native_processes=2,
            accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,rom_changes=0,fixture_writes=0,ordinary_saves=1,
            party_order_changes=1,pp_restored=False,normal_recovery_required=True,healing_site_reached=False,full_story_accepted=False,release_ready=False,
            artifact_excludes=['existing ROM','runner','runtime','input Save43'])
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




