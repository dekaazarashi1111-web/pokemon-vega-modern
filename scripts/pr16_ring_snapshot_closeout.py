#!/usr/bin/env python3
"""Close out saved observation coverage/CI without an emulator or old tests."""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_snapshot_record as prior

BASE='2c9202b47409f0009f32eebda0424033402ae12a'
TASK='PR-P08-7-RING-SNAPSHOT-CLOSEOUT'
SELF='scripts/pr16_ring_snapshot_closeout.py'
TEST='tests/test_pr16_ring_snapshot_closeout.py'
WORKFLOW='.github/workflows/pr16-ring-snapshot-closeout.yml'
REPORT='content/modernization/pr16_ring_snapshot_closeout.json'
CODE=(SELF,TEST,WORKFLOW)
OUTPUTS=(REPORT,s.STATE,s.DOC,s.BACKLOG,*s.LOGS)
OUT=s.ROOT/'.local/pr16-ring-snapshot-closeout'
REFERENCE='https://github.com/mgba-emu/mgba/blob/0.10.3/src/arm/arm.c'


def coverage(analysis, rows):
    """Projection only: never run or strengthen the saved conditional model."""
    s.need(analysis['runtime_provenance_bound'] is True and analysis['observed_calls']==8
           and analysis['bound_calls']==8 and not analysis['rejected_calls'],'unverified input')
    for key in ('allocated_storage_extent_proven','synchrony_proven',
                'all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(analysis[key] is False,'unsupported prior claim')
    entries=[r for r in rows if r['kind']=='entry'];exits=[r for r in rows if r['kind']=='exit']
    s.need(len(entries)==len(exits)==len(analysis['bindings'])==8,'trace cardinality')
    for i,(entry,exit,bound) in enumerate(zip(entries,exits,analysis['bindings']),1):
        s.need(entry['ordinal']==exit['ordinal']==bound['ordinal']==i,'trace ordinal')
        s.need(entry['snapshot']==bound['snapshot'] and exit['returned'] is True
               and bound['actual_return_observed'] is True,'snapshot/return mismatch')
        s.need(bound['conditional_assumptions_not_discharged']==['normal_mapping_stable','synchronous'],
               'conditional assumptions removed')
        s.need(bound['route']=={'kind':'low_other','calls':[],'peak':24}
               and entry['snapshot']['selector']==0 and entry['snapshot']['record_base']==0,
               'coverage changed; update projection instead of generalizing')
    return {'observed_calls':8,'selectors':[0],'routes':['low_other'],
        'return_targets':sorted({b['return_target'] for b in analysis['bindings']}),
        'entry_sp_values':sorted({e['snapshot']['sp'] for e in entries}),
        'flag_ids':[e['snapshot']['id'] for e in entries],
        'observed_instructions':sum(e['steps'] for e in exits),
        'observed_peak_frame_bytes':24,'external1_calls_observed':0,
        'external2_calls_observed':0,'external3_calls_observed':0,
        'active_record_prefix_observed':False,'selector2_peak44_observed':False,
        'normal_mapping_proven':False,'synchrony_proven':False,
        'allocated_storage_extent_proven':False,'all_runtime_owners_excluded':False,
        'ring_acquisition_accepted':False,'release_ready':False}


def main():
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_compiled_record as guard
    s.need(os.environ['GITHUB_REPOSITORY']==s.REPO
           and os.environ['GITHUB_REF']=='refs/heads/'+s.BRANCH,'repo/ref')
    head=s.cmd('git','rev-parse','HEAD');s.need(head==os.environ['GITHUB_SHA'],'HEAD')
    s.assert_remote(head,attempts=3)
    prior.command('git','merge-base','--is-ancestor',BASE,head)
    s.need(not (s.ROOT/REPORT).exists(),'already closed; do not repeat')
    state=resume.validate(s.ROOT);p=s.load(prior.REPORT)
    saved.bindings_fresh(s.ROOT,p['source_bindings'])
    OUT.mkdir(parents=True,exist_ok=True)
    run=s.api('actions/runs/35060189419');job=s.api('actions/jobs/104678679467')
    s.need(run['head_sha']==p['source_head'] and run['id']==p['run_id']
           and run['status']=='completed' and run['conclusion']=='success'
           and job['run_id']==run['id'] and job['conclusion']=='success'
           and all(step['conclusion']=='success' for step in job['steps']),'observation Actions')
    archive=subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/artifacts/10431249360/zip'])
    s.need(s.identity(archive)=={'size':36647,'sha256':'49511c95fa064c87755203cd65c5b16e4c50ef5c949627aa38c5a7dc69fa3caa'},'artifact identity')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        s.need(len(z.infolist())==9 and len(set(z.namelist()))==9,'archive members')
        receipt=json.loads(z.read('recorded-result.json'));private_guard=json.loads(z.read('guard.json'))
        raw=z.read('trace.jsonl')
    s.need(receipt['commit']==BASE and receipt['source_head']==p['source_head']
           and receipt['status']=='PASS_RECORDED_NONFORCE_PUSHED','push receipt differs')
    s.need(private_guard['new_violations']==0 and private_guard['exact_output_match'] is True,
           'observation private guard failed')
    s.need(raw==(s.ROOT/prior.TRACE).read_bytes()
           and s.identity(raw)==p['analysis']['trace_identity'],'retained trace differs')
    projection=coverage(p['analysis'],[json.loads(line) for line in raw.splitlines()])
    with (OUT/'tests.txt').open('w') as stream:
        tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
            unittest.defaultTestLoader.discover(str(s.ROOT/'tests'),pattern=Path(TEST).name))
    s.need(tests.wasSuccessful() and not tests.skipped and tests.testsRun==8,'closeout tests')
    recent=s.api('actions/runs?head_sha='+BASE+'&per_page=10')
    inputs=(*CODE,prior.REPORT,prior.TRACE,prior.FIRST_REPORT,prior.FIRST_RAW)
    bindings={name:s.identity((s.ROOT/name).read_bytes()) for name in inputs}
    result={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),
        'classification':'SAVED_OBSERVATION_COVERAGE_AND_CI_NOT_NEW_NATIVE_ACCEPTANCE',
        'coverage':projection,'observed_run':{k:run[k] for k in ('id','head_sha','status','conclusion')},
        'observed_job_id':job['id'],'observation_commit':BASE,'observation_artifact_id':10431249360,
        'observation_archive':s.identity(archive),'observation_receipt':receipt,'observation_guard':private_guard,
        'source_bindings':bindings,'focused_tests':{'tests_run':8,'failures':0,'errors':0,'skipped':0},
        'new_emulator_processes':0,'accepted_native_cases_replayed':0,'candidate_reconstructions':0,
        'previous_session_native_processes':2,'rom_changes':0,'ring_acquisition_accepted':False,'release_ready':False,
        'actions_observed_at_observation_commit':[{k:r[k] for k in ('id','name','status','conclusion')} for r in recent['workflow_runs']],
        'external_reference_consulted_after_observer_implementation':REFERENCE}
    (s.ROOT/REPORT).write_bytes(s.stable(result))
    stop=('実FlagSet8件の保存証拠とrun35060189419/job104678679467 success・非force保存を照合。'
          '全8件selector=0/low_other、帰還先0x093775CC、観測peak24byte。'
          'selector1/2、external1/2/3、record保存prefixとpeak44は未観測。'
          'このCI整理はnative0、候補復元0、旧46tests/ABI再実行0。初回失敗を含む前工程native2は記録を保持。')
    next_step=('保存8件は再実行しない。次はRing実経路callerのselector1/2とactive record prefix、'
               'record allocation所有範囲・mapping/同期/IRQ/DMA条件を独立に解決する。'
               'selector0の実帰還証拠をexternal1/2/3やmap97/80 FINAL_LEAGUE_CLEAREDの取得へ一般化しない。'
               '旧18ownerは保持。Ring通常取得・装備実戦・通常保存、policy/Circus、P08は未完。受入済みBPは再実行しない。')
    state['ring_snapshot_closeout']={'path':REPORT,'source_head':head,'run_id':result['run_id']}
    state['latest_ring_diagnostic']=state['ring_snapshot_closeout'].copy()
    state['source_change_review_ja']=state['bp']['current_stop']=stop
    state['next_action']['goal_ja']=state['bp']['next_step']=next_step
    state['next_action']['read_paths']=[REPORT,prior.REPORT,prior.TRACE]
    state['observed_head']=head
    state['observed_head_semantics']='保存native観測のCI/coverage整理source HEAD。今回工程でnativeを再起動しない。'
    state['observed_head_checks']['reason_ja']='観測run35060189419はsuccess確認済み。記録commitの未実行CI/action_requiredはsuccessへ読み替えない。'
    state['session_execution_summary']={'new_emulator_processes':0,'rom_changes':0,
        'candidate_reconstructions':0,'accepted_standalone_replays':0,'previous_observation_processes':2,'scope_ja':stop}
    for name in (*CODE,REPORT):state['source_bindings'][name]=s.identity((s.ROOT/name).read_bytes())
    backlog=s.load(s.BACKLOG)
    next(r for r in backlog['remaining_conditions'] if r['id']=='NATURAL_CAPTURE_GEAR')['ring_snapshot_closeout']=REPORT
    (s.ROOT/s.STATE).write_bytes(s.stable(state));(s.ROOT/s.BACKLOG).write_bytes(s.stable(backlog))
    for mode in ('render','check'):prior.command(sys.executable,'scripts/pr16_resume.py',mode)
    stamp=datetime.now(timezone.utc).isoformat()
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        '- Status: DONE / 保存観測coverage・CI照合。Ring取得は未完。\n- Version: PR16 snapshot closeout\n'
        f'- Summary: {stop}\n- Verify: 新規projection8 tests、read-only resume check、task graph、最終index差分guard・diff。\n'
        f'- Evidence: {REPORT}; observed run35060189419 success / commit {BASE}。\n'
        '- Preserved: native0・候補復元0・ROM変更0・受入済み再実行0。BP原本とRing観測原本は不変。\n'
        f'- Files changed: {", ".join(CODE)}、coverage receipt、固定引継ぎMD/JSON、P08参照、両ログ。\n'
        f'- Network/reference: GitHub/Actions。観測器実装後のPC prefetch確認として {REFERENCE} を参照。外部コード転記なし。\n'
        '- Commit: 最新HEAD確認後、同branch非force push。全CI green/全体guard PASS・merge/release/baseline変更なし。\n'
        f'- Next: {next_step}\n')
    for name in s.LOGS:
        s.need(TASK not in (s.ROOT/name).read_text(),'duplicate log')
        with (s.ROOT/name).open('a') as stream:stream.write(entry)
    prior.command(sys.executable,'scripts/validate_task_graph.py')
    prior.command('git','add','--',*OUTPUTS)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*CODE,*OUTPUTS));guard.guard()
    saved.bindings_fresh(s.ROOT,bindings);prior.command('git','diff','--cached','--check')
    s.assert_remote(head,attempts=3)
    prior.command('git','config','user.name','github-actions[bot]')
    prior.command('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    prior.command('git','commit','-m',TASK+': 実観測の範囲と成功CIを固定・未観測経路を明記')
    commit=s.cmd('git','rev-parse','HEAD')
    prior.command('git','push','origin','HEAD:refs/heads/'+s.BRANCH);s.assert_remote(commit,attempts=12)
    for name in OUTPUTS:
        s.need(subprocess.check_output(['git','show','HEAD:'+name])==(s.ROOT/name).read_bytes(),'committed bytes')
    s.need(not s.cmd('git','status','--porcelain','--untracked-files=no'),'tracked residue')
    (OUT/'result.json').write_bytes(s.stable({'status':'PASS_NONFORCE_PUSHED','commit':commit,
        'new_emulator_processes':0,'tests':8,'ring_acquisition_accepted':False,'release_ready':False}))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)

if __name__=='__main__':main()
