#!/usr/bin/env python3
"""完了済みP08 BP原本と目視済み29画面だけを受入。新規nativeは0。"""
from __future__ import annotations
import copy
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_p08_checkpoint as cp
import pr16_p08_bp_loss_policy as bp
import pr16_p08_ring_recovery as e
need=e.need
SELF='scripts/pr16_p08_bp_acceptance.py'
REPORT='content/modernization/pr16_p08_bp_acceptance.json'
RUN=35511250297
JOB=106079428228
HEAD='2b3fba89ee99e4d1360687f22d4cfb562fd0ec77'
ARTIFACT=10606160536
ARCHIVE=dict(size=190645,sha256='c317dde4081bb2e056cb7796598907cea6fc47253e1fdf49b81f265aa1df015f')
OUT=ROOT/'.local/pr16-p08-bp-accept'


def verified(v):
    need(v['candidate']==bp.m.TARGET and v['workflow_source_head']==HEAD and v['source_head']==HEAD
         and v['recording_run']==RUN and v['task']=='USER-20260920-P08-BPLOSS','BP native provenance')
    need(v['native_verified'] is True and v['representative_accepted'] is False and v['visual_review_completed'] is False
         and v['failures']==[] and v['release_ready'] is False,'BP native scope')
    for k,want in dict(new_emulator_processes=1,host_compiles=1,fresh_cores=2,arm_compiles=0,arm_links=0,
        accepted_standalone_replays=0,prefix_wins_reexecuted=0,rom_changes=0).items():
        need(type(v[k]) is int and v[k]==want,'BP native accounting: '+k)
    need(len(v['screens'])==29,'reviewed BP screen inventory')


def accept(files):
    b=cp.b;b.OUT=OUT;b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'BP already accepted: do not duplicate')
    run=b.api('actions/runs/'+str(RUN));job=b.api('actions/jobs/'+str(JOB));art=b.api('actions/artifacts/'+str(ARTIFACT))
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='success','BP complete run')
    need(job['run_id']==RUN and job['head_sha']==HEAD and job['status']=='completed' and job['conclusion']=='success'
         and all(x['conclusion']=='success' for x in job['steps']),'BP complete job')
    need(not art['expired'] and art['workflow_run']['id']==RUN and art['digest']=='sha256:'+ARCHIVE['sha256'],'BP artifact metadata')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    members=e.archive_members(raw,ARCHIVE);v=e.strict(members['native-result.json']);verified(v)
    current=b.load(bp.REPORT)
    for key in ('native_result','screens','source_bindings','generated','protected_originals','previous_trial'):
        need(current[key]==v[key],'BP tracked recording differs: '+key)
    for path,expected in {**v['source_bindings'],**v['protected_originals'],**v['transitive_compiled_sources']}.items():
        need(e.identity((ROOT/path).read_bytes())==expected,'BP source/protected drift: '+path)
    stdout=members['execution/'+bp.m.CASE+'.stdout'];stderr=members['execution/'+bp.m.CASE+'.stderr']
    proc=e.strict(members['execution/'+bp.m.CASE+'.process.json'])
    need(bp.VALIDATE(stdout,stderr,proc)==v['native_result'],'BP native raw projection')
    proof=bp.policy_proof(members['previous.stderr'],stderr)
    need(proof==e.strict(members['policy-proof.json']),'BP changed input proof differs')
    for name,meta in v['screens'].items():
        image=members['screens/'+name]
        need(e.identity(image)==meta and image.startswith(b'P6\n240 160\n255\n') and len(image)==115215,'reviewed BP image differs')
    review=dict(reviewer='ChatGPT',reviewed_at_utc='2026-09-20',artifact_id=ARTIFACT,archive=ARCHIVE,
        reviewed_screen_count=29,screen_identities=v['screens'],visual_review_completed=True,
        observations_ja=['受付・3体選択・再確認・実戦技選択を確認。入口には「サーカスに さんかしますか／いいえ ファクトリーへ」の文言も存在し、その画像をFactory固有文言の証拠にしない。',
                        'まもるを含む通常技UI、瀕死交代、敗北後field、通常Save後field、fresh Continue後fieldを確認。',
                        'battle-allocatedとforced-switch-startの黒画面は遷移中画像として保持し、画面だけで成否を判定しない。',
                        '共有loss callback 09ff59bd・party600・Factory106・在庫・BP0・counter2→3はraw native記録で照合。'],
        initial_map_party_inventory_are_fixtures=True)
    result=copy.deepcopy(v)
    result.update(task='USER-20260920-P08-BP-ACCEPT',source_report=bp.REPORT,
        source_report_identity=e.identity((ROOT/bp.REPORT).read_bytes()),
        original_run_id=RUN,original_job_id=JOB,original_source_head=HEAD,original_conclusion='success',
        artifact_id=ARTIFACT,archive=ARCHIVE,visual_review=review,policy_proof=proof,
        representative_accepted=True,visual_review_completed=True,original_native_processes=1,original_fresh_cores=2,
        new_emulator_processes=0,fresh_cores=0,host_compiles=0,workflow_source_head=os.environ['GITHUB_SHA'])
    stop='P08 BP代表をrun35511250297成功・29画面・raw native原本で正式受入。元party600/Factory106/在庫復元と通常Save/fresh Continue、旧入力76058byte一致を保持。受入回収native0。'
    nxt='P08共有Save/load（わざメモリー満杯置換1件）→Circus退出後通常戦闘へ。BP/Ring/旧3勝/30勝は再実行しない。'
    cp.save(REPORT,result,files,OUT,'ACCEPT',stop,'P08_SHARED_SAVE_LOAD',nxt,[bp.REPORT,'content/modernization/pr16_p08_candidate_impact.json'])
    return b.scope()
