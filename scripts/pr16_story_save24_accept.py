#!/usr/bin/env python3
"""保存済みSave24東通路原本の限定受入。native入力は再実行しない。"""
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save24_detour as d
from pr16_story_after_maori import need,identity
SOURCE='d983562695f17ecac20e1ede1a6916dc04392468'
RUN=37093559410
JOB=111118784339
ARTIFACT=11263343138
ARCHIVE=dict(size=17559812,sha256='6a0cff0cd7a5d4118fd090bd8588c9076f1525d689b7e53802cbea9bbe9d49b0')
OUTPUT=dict(size=131088,sha256='42a5fd672e8be714d40720a9fa4fece27e53293c0b0ca49a2ed0696e206455a0')
FLASH='99f7796e60018e11cf895d6f524f1c444408b5b3e6ef55305c30d63bde1ea9a7'
CP='content/modernization/pr16_story_save24_checkpoint.json'
GUIDE='docs/PR16_STORY_SAVE24_JA.md'
EVIDENCE='content/modernization/pr16_story_save24_evidence'
VISUAL='content/modernization/pr16_story_save24_visual_review.json'


def semantics(a,b):
    ao,bo=a['observations'],b['observations']
    need(len(ao)==20 and len(bo)==2 and (a['end']['inputs'],a['end']['frames'])==(56,2782) and
         (b['end']['inputs'],b['end']['frames'])==(13,1510),'全入力/frames/画面会計')
    coordinates=[[x,3] for x in range(20,32)]+[[31,3]]+[[31,4]]*7
    for i,o in enumerate(ao):
        need(o['map']==[1,73] and o['xy']==coordinates[i] and o['live_xy']==[x+7 for x in o['xy']] and
             o['facing']==(4 if i<12 else 1) and o['party_count']==4 and o['rp']==0 and
             o['battle_flags']==o['battle_outcome']==0 and o['callback2']==d.m.prior.parent.FIELD and
             o['party_sha256']==d.m.prior.parent.PARTY and o['ledger_sha256']==d.m.prior.parent.LEDGER,
             '東通路だけ、party/ledger不変、新戦闘なし')
        need(o['field'] is (i<=13 or i==19) and o['lock']==(0 if i<=13 or i==19 else 1),'Save UIと安定fieldを区別')
        need(o['save_counter']==(23 if i<19 else 24),'途中書込をSave完了にしない')
        if i<=16:need(o['flash_sha256']==d.m.prior.FLASH,'Save前の全Flash保持')
        if i in (17,18):need(o['flash_sha256'] not in (d.m.prior.FLASH,FLASH),'途中書込2枚')
        if i==19:need(o['flash_sha256']==FLASH,'Save24最終Flash')
    need(ao[17]['flash_sha256']!=ao[18]['flash_sha256'],'異なる部分書込み2枚')
    for o in bo:
        d.m.idle(o,d.TARGET,24)
        need(o['facing']==1 and o['battle_flags']==o['battle_outcome']==0 and o['flash_sha256']==FLASH,'独立Continue全状態')
    return dict(status='PASS_EAST_CORRIDOR_SAVE24_PERSISTENCE_SCOPED',map=[1,73],xy=[31,4],facing=1,
        save_counter=24,ordinary_saves=1,party_count=4,rp=0,arrival_observation=13,stable_save_observation=19,
        partial_write_observations=[17,18],save_success_wording_observed=False,
        save_acceptance_basis='NORMAL_SAVE_UI_THEN_STABLE_FIELD_COUNTER24_AND_INDEPENDENT_COMPLETE_SAVE_RTC',
        trainer_victories=0,wild_victories=0,escapes=0,captures=0,fixture_writes=0,teleport_accepted=False,
        cave_crossing_complete=False,national_dex_unlocked=False,hm05_taught_or_used=False,
        natural_growth_accepted=False,natural_evolution_accepted=False,full_story_accepted=False,
        release_ready=False,active_baseline_changed=False)


def verify(folder):
    folder=Path(folder)
    need(not (folder/'failure.json').exists(),'成功した東通路原本だけ')
    measured=json.loads((folder/'measurement.json').read_bytes())
    need(measured['source_head']==SOURCE and measured['run_id']==RUN and measured['output_save']==OUTPUT and
         measured['status']=='MEASURED_EAST_CORRIDOR_SAVE24_AWAITING_VISUAL_RECORD' and
         measured['native_processes']==2 and measured['screen_count']==22 and measured['teleport_accepted'] is False,
         '原本identityとscope')
    need(identity((folder/'candidate.gba').read_bytes())==d.m.shared.plan.CANDIDATE and
         identity((folder/'runner').read_bytes())==d.m.prior.parent.RUNNER,'候補/runner不変')
    parsed={}
    for lane,seed in [('progress',d.m.prior.OUTPUT),('continue',OUTPUT)]:
        parsed[lane]=d.m.shared.trace(folder/lane,seed)
        e=json.loads((folder/lane/'execution.json').read_bytes())
        need(e==dict(returncode=0,initial_save=seed,final_save=OUTPUT,native_end=parsed[lane]['end'],
                     observations=len(parsed[lane]['observations'])),'native正常終了と全原本会計')
        need(identity((folder/lane/'story.srm').read_bytes())==OUTPUT,'作業Save原本')
    result=semantics(parsed['progress'],parsed['continue'])
    for field,lane,index in [('arrival','progress',13),('final','progress',19),('continued','continue',1)]:
        need(measured[field]==parsed[lane]['observations'][index],'measurementと生trace全field '+field)
    boundary,ledger=d.m.boundary((folder/'input.srm').read_bytes(),(folder/'story-fast.srm').read_bytes(),(folder/'cold.srm').read_bytes())
    need(identity((folder/'story-fast.srm').read_bytes())==OUTPUT and json.loads(json.dumps(boundary))==measured['boundary'] and
         boundary['auxiliary_flag_deltas']==[] and boundary['auxiliary_var_deltas']==[(0x4021,26,38),(0x4022,1,3)] and
         (boundary['changed_bytes'],boundary['changed_ranges'])==(6937,1754),'観測された限定差分だけ')
    result.update(boundary=boundary,input_save=d.m.prior.OUTPUT,output_save=OUTPUT,candidate=d.m.shared.plan.CANDIDATE,
        progress_inputs=56,continue_inputs=13,progress_frames=2782,continue_frames=1510,screen_count=22,
        measurement_native_processes=2,record_native_processes=0,accepted_case_reruns=0,accepted_test_reruns=0,
        compiles=0,rom_changes=0)
    return result,ledger
