#!/usr/bin/env python3
"""Save23の先だけを通常入力で測定。座標teleport→Save24→独立Continue。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save23_accept as prior
import pr16_story_save23_measure as shared
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
from pr16_story_after_maori_session import Session
from pr16_story_after_maori import need,identity,write
BASE='796fda7efd1ace9bc1cbcf2555c77983d6402b73'
TASK='USER-20261003-CAVE-TELEPORT-SAVE24'
OUT=ROOT/'.local/pr16-story-save24'
ART=OUT/'artifact'
CODE={'scripts/pr16_story_save24_measure.py','tests/test_pr16_story_save24_measure.py',
      '.github/workflows/pr16-story-save24.yml'}
ROUTE=[[x,3] for x in range(20,28)]+[[27,y] for y in range(4,8)]
TARGET=[19,14]


def idle(o,xy=None,counter=23):
    need(o['map']==[1,73] and (xy is None or o['xy']==xy) and o['field'] is True and o['lock']==0 and
         o['callback2']==prior.parent.FIELD and o['save_counter']==counter and o['party_count']==4 and o['rp']==0 and
         o['party_sha256']==prior.parent.PARTY and o['ledger_sha256']==prior.parent.LEDGER and
         o['live_xy']==[x+7 for x in o['xy']] and
         (o['battle_flags'],o['battle_outcome']) in ((0,0),(0,4)),
         '同一party/ledger/RP0・操作可能field・未決着戦闘なし')


def flee(session):
    """野生戦だけを通常Runで1回離脱。攻撃/道具/逃走失敗の盲反復はしない。"""
    o=session.last
    need(o['battle_flags']==0 and o['battle_outcome']==0 and o['lock']==1,'野生開始だけ')
    # Bは紹介文を送るが技を選ばない。新しい戦闘の初期menuからRunへ。
    for _ in range(3):
        o=session.step((2,2),(0,240))
        need(o['party_sha256']==prior.parent.PARTY and o['battle_flags']==0 and o['battle_outcome']==0,
             '逃走前の攻撃/party変化は禁止')
    need(o['callback2']==prior.parent.BATTLE,'野生battle callback')
    session.step((128,1),(0,12),(16,1),(0,12),(1,2),(0,360))
    for _ in range(6):
        o=session.last
        if o['callback2']==prior.parent.FIELD and o['field'] is True and o['lock']==0:
            break
        need(o['battle_flags']==0 and o['battle_outcome'] in (0,4) and
             o['party_sha256']==prior.parent.PARTY,'野生1回の無損傷逃走のみ')
        o=session.step((2,2),(0,180))
    need(o['battle_outcome']==4,'逃走4を勝利へ昇格しない')
    idle(o)
    return o


def teleport(session):
    idle(session.last,[20,3])
    steps=[];escapes=[]
    for before,after in zip(ROUTE,ROUTE[1:]):
        key=shared.direction(before,after)
        for attempt in range(3):
            o=session.step((key,8),(0,300 if after==[27,7] else 32))
            if after!=[27,7] and (o['field'] is not True or o['lock']!=0):
                for _ in range(3):
                    if o['callback2']==prior.parent.BATTLE or (o['field'] is True and o['lock']==0):break
                    need(o['map']==[1,73] and o['xy'] in (before,after),'歩行後の限定待機')
                    o=session.step((0,300))
            if o['callback2']==prior.parent.BATTLE:
                escapes.append(dict(start=len(session.observations)-1,xy=o['xy']))
                o=flee(session);escapes[-1]['returned']=len(session.observations)-1
            if after==[27,7] and o['xy'] in ([27,7],TARGET):
                for _ in range(4):
                    if o['xy']==TARGET and o['field'] is True and o['lock']==0:break
                    need(o['map']==[1,73] and o['xy'] in ([27,7],TARGET),'限定teleport待機')
                    o=session.step((0,300))
                idle(o,TARGET);steps.append(dict(from_xy=before,to_xy=TARGET,trigger_xy=after,observation=len(session.observations)-1))
                need(o['flash_sha256']==prior.FLASH,'teleportまでSave書込み0')
                return o,steps,escapes
            need(o['map']==[1,73] and o['xy'] in (before,after),'別の座標/warpなら停止')
            idle(o,o['xy'])
            need(o['flash_sha256']==prior.FLASH,'未保存prefixを保持')
            if o['xy']==after:
                steps.append(dict(from_xy=before,to_xy=after,observation=len(session.observations)-1));break
        else:raise ValueError('通常歩行が3試行で進まない')
    raise ValueError('正規teleport未観測')


def ordinary_save(session):
    idle(session.last,TARGET)
    session.step((8,2),(0,60))
    session.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    session.step((1,2),(0,60))
    session.step((1,2),(0,180))
    for _ in range(5):
        o=session.step((0,240))
        need(o['map']==[1,73] and o['xy']==TARGET and o['save_counter'] in (23,24),'Save24だけ')
        if o['save_counter']==24 and o['field'] is True and o['lock']==0:break
    idle(o,TARGET,24)
    need(o['flash_sha256']!=prior.FLASH,'新しい通常Save')
    return o


def flag_vars(fa,va,fb,vb):
    need(type(fa) is bytes and type(fb) is bytes and len(fa)==len(fb)==0x120 and
         len(va)==len(vb)==256 and all(type(x) is int for x in (*va,*vb)),'全legacy arrays')
    flags=[(8*i+j,(a>>j)&1,(b>>j)&1) for i,(a,b) in enumerate(zip(fa,fb)) for j in range(8) if (a^b)&(1<<j)]
    variables=[(0x4000+i,a,b) for i,(a,b) in enumerate(zip(va,vb)) if a!=b]
    need(all(k==2056 for k,_,_ in flags),'補助flag2056以外を解禁しない')
    need(all(k in (0x4021,0x4022,0x404d) for k,_,_ in variables),'限定aux varsのみ')
    need(va[0x4e]==vb[0x4e]==0 and not ((fa[0x840//8]|fb[0x840//8])&1) and
         va[0x71]==vb[0x71]==6 and va[0x72]==vb[0x72]==1,'全国図鑑/story gate不変')
    return dict(auxiliary_flag_deltas=flags,auxiliary_var_deltas=variables,national_dex_magic=0,
        national_var404e=0,national_flag840=0,story_vars={'4071':6,'4072':1},
        auxiliary_runtime_owners_resolved=False)


def boundary(before,after,cold):
    s=prior.parent.sectors
    need(identity(before)==prior.OUTPUT and len(after)==131088 and after==cold,'固定Save23とcold全Save/RTC')
    old,ra=s.bank(before,0xe000,23,s.LAYOUT);new,rb=s.bank(after,0,24,s.LAYOUT);_,rc=s.bank(after,0xe000,23,s.LAYOUT)
    need(before[0xe000:0x1c000]==after[0xe000:0x1c000],'Save23 bank全57344bytes不変')
    pa=before[old[1]+56:old[1]+656];pb=after[new[1]+56:new[1]+656]
    need(pa==pb and identity(pb)['sha256']==prior.parent.PARTY,'全party600bytes保全')
    need(before[old[1]+52:old[1]+56]==after[new[1]+52:new[1]+56]==struct.pack('<I',4),'4slots')
    a,ma=prior.parent.shared.bag(before,old);b,mb=prior.parent.shared.bag(after,new)
    need(a==b and ma==mb==12296,'全Bag/HM05/所持金不変')
    for sid in range(5,14):
        need(before[old[sid]:old[sid]+0xff4]==after[new[sid]:new[sid]+0xff4],'PC/S61E不変')
    fa,va=s.legacy_state(before,old);fb,vb=s.legacy_state(after,new);result=flag_vars(fa,va,fb,vb)
    need(before[old[0]+0x1b]==after[new[0]+0x1b]==0,'全国図鑑magic')
    prior.parent.s61e_record(after[new[13]+0x7d0:new[13]+0xde6])
    result.update(party_bytes_preserved=600,bag_unchanged=True,money=mb,hm05_owned=True,hm05_taught_or_used=False,
        sector_checksums=len(ra)+len(rb)+len(rc),pc_and_s61e_sections_unchanged=list(range(5,14)),
        s61e_crc_and_inverse_checked=True,save23_bank_preserved_bytes=57344,complete_save_rtc_cold_identical=True)
    changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b];ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([i,i+1])
    ledger=dict(changed_bytes=len(changed),ranges=[dict(start=a,end=b,before_hex=before[a:b].hex(),after_hex=after[a:b].hex()) for a,b in ranges])
    result.update(changed_bytes=len(changed),changed_ranges=len(ranges))
    return result,ledger


def restore():
    meta,z=transport.archive(prior.ARTIFACT,prior.RUN,prior.ARCHIVE,prior.SOURCE)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==34 and set(z.namelist())==set(manifest)|{'manifest.json'},'固定Save23全member')
        for name,binding in manifest.items():need(identity(z.read(name))==binding,'親全byte '+name)
        for name,target,binding in [('story-fast.srm','input.srm',prior.OUTPUT),
            ('candidate.gba','candidate.gba',shared.plan.CANDIDATE),('runner','runner',prior.parent.RUNNER)]:
            raw=z.read(name);need(identity(raw)==binding,'固定親 '+name)
            (ART/target).write_bytes(raw);(ART/target).chmod(0o555 if name=='runner' else 0o444)
    write(ART/'parent.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    runtime=OUT/'runtime';runtime.mkdir()
    _,z=transport.archive(10898620034,36218655601,dict(size=102586759,sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'))
    with z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                p=runtime/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    need(identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'固定mGBA')
    return runtime


def main():
    os.chdir(ROOT);h.d.current()
    need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'新規初回のみ。自動再走禁止')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE)
    need(state['story_save23']['story_fast_save']==prior.OUTPUT and
         state['story_cave_route']['native_accepted'] is False,'唯一の親と未受入teleport')
    route=h.d.read(ROOT/'content/modernization/pr16_story_cave_route_checkpoint.json')
    need(route['result']['static_route']==ROUTE and route['result']['next_teleport']['xy']==TARGET,'保存済み静的証拠を再利用')
    ART.mkdir(parents=True);sessions=[]
    try:
        runtime=restore();seed=(ART/'input.srm').read_bytes()
        progress=Session(runtime,ART/'candidate.gba',ART/'runner',seed,ART/'progress');sessions.append(progress)
        arrival,steps,escapes=teleport(progress)
        final=ordinary_save(progress)
        result_progress=progress.quit();saved=progress.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        cold=Session(runtime,ART/'candidate.gba',ART/'runner',saved,ART/'continue');sessions.append(cold)
        idle(cold.last,TARGET,24)
        need(all(cold.last[k]==final[k] for k in ('facing','party_sha256','flash_sha256','ledger_sha256')),'独立Continue保持')
        cold.step((0,120));idle(cold.last,TARGET,24)
        result_cold=cold.quit();(ART/'cold.srm').write_bytes(cold.save.read_bytes())
        parsed_a=shared.trace(ART/'progress',prior.OUTPUT);parsed_b=shared.trace(ART/'continue',identity(saved))
        bound,ledger=boundary(seed,saved,cold.save.read_bytes());write(ART/'save-byte-ledger.json',ledger)
        need(h.d.bindings(protected)==protected,'既受入sources/証拠/progression/基準不変')
        report=dict(schema_version=1,task=TASK,status='MEASURED_COORD_TELEPORT_SAVE24_AWAITING_VISUAL_RECORD',
            source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=prior.OUTPUT,
            candidate=shared.plan.CANDIDATE,output_save=identity(saved),arrival=arrival,final=final,continued=cold.last,
            route=steps,escapes=escapes,progress=result_progress,independent_continue=result_cold,boundary=bound,
            source_bindings=h.d.bindings(CODE),native_processes=2,compiles=0,rom_changes=0,accepted_case_reruns=0,
            accepted_test_reruns=0,ordinary_saves=1,national_dex_unlocked=False,hm05_taught_or_used=False,
            full_story_accepted=False,cave_crossing_complete=False,release_ready=False,active_baseline_changed=False,
            visual_review_completed=False,screen_count=len(parsed_a['screens'])+len(parsed_b['screens']))
        write(ART/'measurement.json',report)
        print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as exc:
        for session in sessions:
            if not session.closed and session.process.poll() is None:
                try:session.quit()
                except Exception:session.process.terminate()
        write(ART/'failure.json',dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',
            exception_type=type(exc).__name__,native_processes=len(sessions),source_head=os.environ['GITHUB_SHA'],
            run_id=int(os.environ['GITHUB_RUN_ID'])))
        raise
    finally:
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes()) for p in sorted(ART.rglob('*'))
            if p.is_file() and p.name!='manifest.json'})


if __name__=='__main__':main()
