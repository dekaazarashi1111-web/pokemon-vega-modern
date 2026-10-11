#!/usr/bin/env python3
"""完了済み共有Save/load原本と6画面を受入。旧ケース・新native再実行なし。"""
from __future__ import annotations
import copy
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_p08_checkpoint as cp
import pr16_p08_memory_representative as m
import pr16_p08_ring_recovery as e
need=e.need
SELF='scripts/pr16_p08_memory_acceptance.py'
REPORT='content/modernization/pr16_p08_memory_acceptance.json'
RUN=35511721939
JOB=106080666506
HEAD='33bb7bce407e839fbf1931ee8968ca55fce82077'
ARTIFACT=10605273037
ARCHIVE=dict(size=64166,sha256='cdca1664fa720ee1ee18107a4d8134836877ee971908f5138b8bafcd04875bfa')
OUT=ROOT/'.local/pr16-p08-memory-accept'


def verify(v):
    need(v['candidate']==m.TARGET and v['workflow_source_head']==HEAD and v['recording_run']==RUN
         and v['task']=='USER-20260920-P08-MEMORY','memory provenance')
    need(v['native_verified'] is True and v['representative_accepted'] is False and v['visual_review_completed'] is False
         and v['failures']==[] and v['release_ready'] is False,'memory scope')
    for key,want in dict(new_emulator_processes=1,fresh_cores=2,host_compiles=1,arm_compiles=0,arm_links=0,
        accepted_standalone_replays=0,prefix_wins_reexecuted=0,rom_changes=0).items():
        need(type(v[key]) is int and v[key]==want,'memory accounting: '+key)
    need(set(v['screens'])=={m.CASE+'-'+name+'.ppm' for name in ('fixture','memory-list','replacement-summary','learned-field','normal-save','fresh-continue')},'reviewed memory inventory')


def accept(files):
    b=cp.b;b.OUT=OUT;b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'memory already accepted')
    run=b.api('actions/runs/'+str(RUN));job=b.api('actions/jobs/'+str(JOB));art=b.api('actions/artifacts/'+str(ARTIFACT))
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='success','memory complete run')
    need(job['run_id']==RUN and job['head_sha']==HEAD and job['status']=='completed' and job['conclusion']=='success'
         and all(s['conclusion']=='success' for s in job['steps']),'memory complete job')
    need(not art['expired'] and art['workflow_run']['id']==RUN and art['digest']=='sha256:'+ARCHIVE['sha256'],'memory artifact metadata')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    members=e.archive_members(raw,ARCHIVE);v=e.strict(members['native-result.json']);verify(v);current=b.load(m.REPORT)
    for key in ('native_result','screens','source_bindings','generated','protected_originals','physical_case','byte_witness'):
        need(current[key]==v[key],'memory tracked projection: '+key)
    for path,expected in {**v['source_bindings'],**v['protected_originals'],**v['transitive_compiled_sources']}.items():
        need(e.identity((ROOT/path).read_bytes())==expected,'memory source/protected drift: '+path)
    stdout=members['execution/'+m.CASE+'.stdout'];stderr=members['execution/'+m.CASE+'.stderr'];proc=e.strict(members['execution/'+m.CASE+'.process.json'])
    need(m.validate(stdout,stderr,proc)==v['native_result'] and m.bytes_proof(stderr)==v['byte_witness'],'memory original raw projection')
    for name,expected in v['screens'].items():
        image=members['screens/'+name]
        need(e.identity(image)==expected and image.startswith(b'P6\n240 160\n255\n') and len(image)==115215,'memory reviewed image differs')
    review=dict(reviewer='ChatGPT',reviewed_at_utc='2026-09-20',artifact_id=ARTIFACT,archive=ARCHIVE,
        reviewed_screen_count=6,screen_identities=v['screens'],visual_review_completed=True,
        observations_ja=['スバメのわざメモリー候補一覧と、満杯4技の置換Summaryに「かっくう」PP20/20を確認。',
                        '初期field・習得後field・通常Save後field・fresh Continue後fieldを確認。同一見た目から内部保存を推測せず、party100byte・PP・counter2→3をrawで照合。'],
        initial_map_party_progress_are_fixtures=True)
    result=copy.deepcopy(v);result.update(task='USER-20260920-P08-MEMORY-ACCEPT',source_report=m.REPORT,
        source_report_identity=e.identity((ROOT/m.REPORT).read_bytes()),original_run_id=RUN,original_job_id=JOB,
        original_source_head=HEAD,original_conclusion='success',artifact_id=ARTIFACT,archive=ARCHIVE,visual_review=review,
        representative_accepted=True,visual_review_completed=True,original_native_processes=1,original_fresh_cores=2,
        new_emulator_processes=0,fresh_cores=0,host_compiles=0,workflow_source_head=os.environ['GITHUB_SHA'])
    cp.save(REPORT,result,files,OUT,'ACCEPT','共有Save/load代表をrun35511721939成功・6画面・raw nativeで受入。満杯置換/party100/PP/通常Save/fresh Continueを保持。受入回収native0。',
        'P08_CIRCUS_POST_EXIT_ORDINARY','残るCircus退出後Save30からの通常戦闘calleeだけを検証。旧30勝/施設受入/Ring/BP/他メモリー経路は再実行しない。',[m.REPORT,'content/modernization/pr16_p08_candidate_impact.json'])
    return b.scope()
