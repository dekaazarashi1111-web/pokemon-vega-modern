#!/usr/bin/env python3
"""高さ不一致で未保存停止した新区間を、東通路の通常Save24で区切る。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save24_measure as m
from pr16_story_after_maori import need,identity,write,unpack
from pr16_story_after_maori_session import Session
h=m.h
BASE='85e1e7d2b23e3da797639a365251f671015b0bb8'
TASK='USER-20261003-CAVE-EAST-SAVE24'
OUT=ROOT/'.local/pr16-story-save24-detour'
ART=OUT/'artifact'
CODE={'scripts/pr16_story_save24_detour.py','tests/test_pr16_story_save24_detour.py',
      '.github/workflows/pr16-story-save24-detour.yml','tests/test_pr16_story_save24_terrain.py'}
ROUTE=[[x,3] for x in range(20,32)]+[[31,4]]
TARGET=[31,4]
FAILED_RUN=37092974275
FAILED_JOB=111117037718
FAILED_ARTIFACT=11263731555
FAILED_ARCHIVE=dict(size=17471160,sha256='69a54c9403f7b882252147deb95932decc3b1f60e8ed8baa638b318667b9569b')


def recover_failed():
    run=h.d.inputs.api('actions/runs/'+str(FAILED_RUN));jobs=h.d.inputs.api('actions/runs/'+str(FAILED_RUN)+'/jobs?per_page=100')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==BASE and run['run_attempt']==1 and
         jobs['total_count']==len(jobs['jobs'])==1 and jobs['jobs'][0]['id']==FAILED_JOB,'元failure原本')
    steps=jobs['jobs'][0]['steps']
    need([s['conclusion'] for s in steps]==['success','success','success','failure','skipped','success','success','success'],
         '32試験成功・native未保存停止・upload成功を分離')
    meta,z=m.transport.archive(FAILED_ARTIFACT,FAILED_RUN,FAILED_ARCHIVE,BASE)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(len(manifest)==23 and set(z.namelist())==set(manifest)|{'manifest.json'},'失敗原本全23member')
        for name,binding in manifest.items():need(identity(z.read(name))==binding,'失敗原本全byte '+name)
        need(identity(z.read('input.srm'))==identity(z.read('progress/story.srm'))==m.prior.OUTPUT,'未保存・Save23全byte不変')
        raw=z.read('progress/stdout.txt');cmd=z.read('progress/commands.txt')
        parsed=m.prior.parent.parent.trace(raw,cmd,m.prior.OUTPUT)
        ao=parsed['observations'];need(len(ao)==13 and (parsed['end']['inputs'],parsed['end']['frames'])==(36,1870),
            '失敗原本会計')
        need(all(o['xy']==[27,4] and o['facing']==1 and o['field'] is True and o['lock']==0 for o in ao[9:]),
            '南3回が同位置で停止')
        for name in ['failure.json','manifest.json','progress/commands.txt','progress/stdout.txt','progress/execution.json']:
            dest=ART/'failed-attempt'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
    receipt=dict(run=h.d.run_summary(run),job=jobs['jobs'][0],
        artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')},
        stopped_xy=[27,4],blocked_attempt_xy=[27,5],ordinary_saves=0,output_save=m.prior.OUTPUT,
        original_tests=32,original_test_reruns=0,original_inputs=36,original_frames=1870,native_processes=1,
        unchanged_save_requires_reload=True,not_an_accepted_interval_replay=True)
    write(ART/'failed-attempt-receipt.json',receipt)
    return receipt


def floor_allowed(row):
    return row['collision']==0 and row['elevation']==3 and row['behavior'] in (0,8,0x2b,0x61)


def terrain(raw):
    need(identity(raw)==m.shared.plan.CANDIDATE,'固定候補')
    width,height,_,blocks,primary,secondary=unpack(raw,137190172,'IIIIII')
    need((width,height)==(40,23),'同一map1/73 layout')
    attrs=unpack(raw,secondary+20,'I')[0]
    cells=unpack(raw,blocks,'H'*(width*height))
    rows=[]
    for xy in ROUTE+[[27,4],[27,5],[23,14]]:
        x,y=xy;cell=cells[y*width+x];tile=cell&0x3ff
        attrptr=(unpack(raw,primary+20,'I')[0]+tile*4) if tile<0x280 else attrs+(tile-0x280)*4
        attr=unpack(raw,attrptr,'I')[0]
        rows.append(dict(xy=xy,elevation=cell>>12,collision=(cell>>10)&3,metatile=tile,behavior=attr&0x1ff))
    need(all(floor_allowed(x) for x in rows[:len(ROUTE)]),
         '新経路は同じ高さ3の通常floorだけ')
    need(rows[-3]==dict(xy=[27,4],elevation=3,collision=0,metatile=0x305,behavior=8) and
         rows[-2]==dict(xy=[27,5],elevation=4,collision=0,metatile=0x289,behavior=0x32) and
         rows[-1]==dict(xy=[23,14],elevation=0,collision=0,metatile=0x91,behavior=0x2a),'旧候補に高さ/方向境界・別階段')
    return dict(scope='STATIC_DIRECTION_ELEVATION_AND_NATIVE_BLOCK_NOT_FULL_PATH_ACCEPTANCE',map=[1,73],rows=rows,
        primary_reference='https://github.com/pret/pokefirered/blob/master/include/constants/metatile_behaviors.h',
        conclusion_ja='27,4→27,5は高さ3→4かつ北側進入不可。runtimeで3回停止した証拠と整合。collision-only候補を可達性に昇格しない。23,14岩階段からの先は未測定。')


def walk(session):
    m.idle(session.last,[20,3]);steps=[]
    for before,after in zip(ROUTE,ROUTE[1:]):
        key=m.shared.direction(before,after)
        for _ in range(3):
            o=session.step((key,8),(0,32))
            need(o['map']==[1,73] and o['xy'] in (before,after),'東通路の1tileだけ')
            m.idle(o,o['xy'])
            need(o['battle_flags']==o['battle_outcome']==0 and o['flash_sha256']==m.prior.FLASH,'新戦闘/保存は別境界')
            if o['xy']==after:
                steps.append(dict(from_xy=before,to_xy=after,observation=len(session.observations)-1));break
        else:raise ValueError('新経路停止。盲目的再試行禁止')
    m.idle(o,TARGET)
    return o,steps


def save(session):
    m.idle(session.last,TARGET)
    session.step((8,2),(0,60))
    session.step(*([(128,1),(0,5)]*4),(1,2),(0,60))
    session.step((1,2),(0,60));session.step((1,2),(0,180))
    for _ in range(5):
        o=session.step((0,240))
        need(o['map']==[1,73] and o['xy']==TARGET and o['save_counter'] in (23,24),'東通路Save24だけ')
        if o['save_counter']==24 and o['field'] is True and o['lock']==0:break
    m.idle(o,TARGET,24);need(o['flash_sha256']!=m.prior.FLASH,'通常Save完了')
    return o


def main():
    os.chdir(ROOT);h.d.current()
    need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not OUT.exists(),'新区間初回だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE|m.CODE)
    ART.mkdir(parents=True);sessions=[]
    try:
        failure=recover_failed()
        m.OUT=OUT;m.ART=ART;runtime=m.restore()
        terrain_result=terrain((ART/'candidate.gba').read_bytes());write(ART/'terrain.json',terrain_result)
        seed=(ART/'input.srm').read_bytes()
        progress=Session(runtime,ART/'candidate.gba',ART/'runner',seed,ART/'progress');sessions.append(progress)
        arrival,steps=walk(progress);final=save(progress)
        result_progress=progress.quit();saved=progress.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        cold=Session(runtime,ART/'candidate.gba',ART/'runner',saved,ART/'continue');sessions.append(cold)
        m.idle(cold.last,TARGET,24)
        need(all(cold.last[k]==final[k] for k in ('facing','party_sha256','flash_sha256','ledger_sha256')),'独立Continue保持')
        cold.step((0,120));m.idle(cold.last,TARGET,24)
        result_cold=cold.quit();(ART/'cold.srm').write_bytes(cold.save.read_bytes())
        pa=m.shared.trace(ART/'progress',m.prior.OUTPUT);pb=m.shared.trace(ART/'continue',identity(saved))
        bound,ledger=m.boundary(seed,saved,cold.save.read_bytes());write(ART/'save-byte-ledger.json',ledger)
        need(h.d.bindings(protected)==protected,'受入済み全sources/原本/基準保全')
        report=dict(schema_version=1,task=TASK,status='MEASURED_EAST_CORRIDOR_SAVE24_AWAITING_VISUAL_RECORD',
            source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=m.prior.OUTPUT,
            candidate=m.shared.plan.CANDIDATE,output_save=identity(saved),arrival=arrival,final=final,continued=cold.last,
            route=steps,escapes=[],progress=result_progress,independent_continue=result_cold,boundary=bound,
            source_bindings=h.d.bindings(CODE|m.CODE),native_processes=2,compiles=0,rom_changes=0,accepted_case_reruns=0,
            accepted_test_reruns=0,ordinary_saves=1,teleport_accepted=False,national_dex_unlocked=False,
            hm05_taught_or_used=False,full_story_accepted=False,cave_crossing_complete=False,release_ready=False,
            active_baseline_changed=False,visual_review_completed=False,screen_count=len(pa['screens'])+len(pb['screens']),
            recovered_failure=failure,terrain=terrain_result)
        write(ART/'measurement.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as exc:
        for s in sessions:
            if not s.closed and s.process.poll() is None:
                try:s.quit()
                except Exception:s.process.terminate()
        write(ART/'failure.json',dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',exception_type=type(exc).__name__,
            native_processes=len(sessions),source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID'])))
        raise
    finally:
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes()) for p in sorted(ART.rglob('*'))
            if p.is_file() and p.relative_to(ART).as_posix()!='manifest.json'})


if __name__=='__main__':main()
