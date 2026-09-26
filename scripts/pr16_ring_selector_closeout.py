#!/usr/bin/env python3
"""selector/record工程の原Actions・artifact・commitを照合。既読ABI/nativeを再実行しない。"""
from __future__ import annotations
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

BASE='8b626df3ef87d4f96e55160a751f5940f6269efb'
TASK='PR-P08-7-RING-SELECTOR-CLOSEOUT'
SELF='scripts/pr16_ring_selector_closeout.py'
TEST='tests/test_pr16_ring_selector_closeout.py'
WORKFLOW='.github/workflows/pr16-ring-selector-closeout.yml'
REPORT='content/modernization/pr16_ring_selector_closeout.json'
CODE=(SELF,TEST,WORKFLOW)
OUTPUTS=(REPORT,s.STATE,s.DOC,s.BACKLOG,*s.LOGS)
OUT=s.ROOT/'.local/pr16-ring-selector-closeout'
ROWS=(
 {'run':35073059942,'job':104718887950,'artifact':10437157137,
  'head':'0a9e8c00fbb67cff4c626eca9c7ae770b143c4de','commit':'5a3a79347acd235250cd389a6d79b650902f93f6',
  'report':'content/modernization/pr16_ring_selector_owners.json','tests':15,
  'archive':{'size':947803,'sha256':'991b48dec27f930fb8e9085702902f330f962735e5a535994c4d200822e8736a'},
  'extra_members':['preflight.json','source-context.zip']},
 {'run':35074318490,'job':104722959596,'artifact':10437566950,
  'head':'d42165a1fdaf578805e64b247b1a833a0a7316bc','commit':BASE,
  'report':'content/modernization/pr16_ring_record_init.json','tests':24,
  'archive':{'size':4031,'sha256':'b6ee054208c564e3c2e89e71133d2fed601596def38b1efc698dc8e0b69a1a3a'},
  'extra_members':[]})
REFERENCE={'repo':'pret/pokefirered','ref':'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
 'paths':['src/event_data.c','src/quest_log.c'],
 'purpose_ja':'GetFlagAddr selector1/2とQuest Log再生/記録の比較。候補ROMへの同一性・到達性の根拠ではない。',
 'adopted_as_candidate_source':False,'external_code_copied':False}


def audit_archive(raw,row,report):
    s.need(s.identity(raw)==row['archive'],'artifact identity')
    expected={'analysis.json','guard.json','recorded-result.json','tests.json','tests.txt',*row['extra_members']}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        s.need(len(names)==len(set(names)) and set(names)==expected,'artifact members')
        s.need(all(Path(n).name==n for n in names) and sum(x.file_size for x in z.infolist())<8000000,'artifact bounds')
        data={name:z.read(name) for name in names}
    receipt=json.loads(data['recorded-result.json']);guard=json.loads(data['guard.json'])
    tests=json.loads(data['tests.json']);analysis=json.loads(data['analysis.json'])
    s.need(analysis==report['analysis'],'record/analysis mismatch')
    s.need(receipt['status']=='PASS_RECORDED_NONFORCE_PUSHED'
           and receipt['commit']==row['commit'] and receipt['source_head']==row['head']
           and receipt['run_id']==row['run']==report['run_id']
           and report['source_head']==row['head'],'receipt identity')
    s.need(tests==report['focused_tests']==receipt['tests'] and tests['tests_run']==row['tests']
           and tests['successful'] is True and (tests['failures'],tests['errors'],tests['skips'])==(0,0,0),'test receipt')
    s.need(guard['new_violations']==0 and guard['exact_output_match'] is True
           and guard['full_guard_before']==guard['full_guard_after']==1
           and guard['full_guard_pass_claimed'] is False,'guard boundary')
    for obj in (receipt,analysis):
        s.need(obj['new_emulator_processes']==0 and obj['ring_acquisition_accepted'] is False
               and obj['release_ready'] is False,'acceptance boundary')
    return {'run_id':row['run'],'job_id':row['job'],'artifact_id':row['artifact'],
        'archive_identity':s.identity(raw),'receipt':receipt,'guard':guard,'focused_tests':tests,
        'original_tests_text':data['tests.txt'].decode('utf-8'),
        'member_identities':{n:s.identity(b) for n,b in data.items()}}


def test_suite(pattern):
    with (OUT/(pattern+'.txt')).open('w',encoding='utf-8') as stream:
        t=unittest.TextTestRunner(stream=stream,verbosity=2).run(
            unittest.defaultTestLoader.discover(str(s.ROOT/'tests'),pattern=pattern))
    s.need(t.wasSuccessful() and not t.skipped,'focused tests failed')
    return {'tests_run':t.testsRun,'failures':len(t.failures),'errors':len(t.errors),'skipped':len(t.skipped)}


def main():
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_compiled_record as guard
    s.need(os.environ['GITHUB_REPOSITORY']==s.REPO and os.environ['GITHUB_REF']=='refs/heads/'+s.BRANCH,'repo/ref')
    head=s.cmd('git','rev-parse','HEAD');s.need(head==os.environ['GITHUB_SHA'],'HEAD')
    s.assert_remote(head,attempts=3)
    subprocess.run(['git','merge-base','--is-ancestor',BASE,head],check=True)
    s.need(not (s.ROOT/REPORT).exists(),'already closed; reuse original')
    state=resume.validate(s.ROOT);bp=s.identity((s.ROOT/s.CHECKPOINT).read_bytes())
    OUT.mkdir(parents=True,exist_ok=True)
    audits=[];reports=[]
    for row in ROWS:
        report=s.load(row['report']);reports.append(report)
        saved.bindings_fresh(s.ROOT,report['source_bindings'])
        run=s.api('actions/runs/'+str(row['run']));job=s.api('actions/jobs/'+str(row['job']))
        s.need(run['head_sha']==row['head'] and run['status']=='completed' and run['conclusion']=='success'
               and job['run_id']==row['run'] and job['status']=='completed' and job['conclusion']=='success'
               and all(x['conclusion']=='success' for x in job['steps']),'Actions not successful')
        raw=subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/artifacts/'+str(row['artifact'])+'/zip'])
        audit=audit_archive(raw,row,report)
        s.need(subprocess.check_output(['git','show',row['commit']+':'+row['report']])==(s.ROOT/row['report']).read_bytes(),'saved report changed')
        s.need(s.cmd('git','rev-parse',row['commit']+'^')==row['head'],'record parent mismatch')
        subprocess.run(['git','merge-base','--is-ancestor',row['commit'],head],check=True)
        audit['observed_run']={k:run[k] for k in ('id','head_sha','status','conclusion')};audits.append(audit)
    close_tests=test_suite(Path(TEST).name);s.need(close_tests['tests_run']==8,'closeout test count')
    recent=[];cache_jobs=[]
    for sha in dict.fromkeys([r['head'] for r in ROWS]+[r['commit'] for r in ROWS]+[head]):
        runs=s.api('actions/runs?head_sha='+sha+'&per_page=100')
        s.need(runs['total_count']<=100,'Actions pagination needed')
        for run in runs['workflow_runs']:
            recent.append({k:run[k] for k in ('id','name','head_sha','event','status','conclusion')})
            if run['path']=='.github/workflows/modernization-stage79-mgba.yml' and run['status']=='completed' and run['conclusion']=='success':
                jobs=s.api('actions/runs/'+str(run['id'])+'/jobs?per_page=100')['jobs']
                for job in jobs:
                    if not job['name'].startswith('domain ('):continue
                    step=next(x for x in job['steps'] if x['name']=='domainをmGBAで実行')
                    s.need(step['conclusion']=='skipped','accepted domain native replayed; record separately')
                    cache_jobs.append({'run_id':run['id'],'job_id':job['id'],'name':job['name'],
                                       'native_step_conclusion':step['conclusion']})
    bindings={p:s.identity((s.ROOT/p).read_bytes()) for p in (*CODE,*(r['report'] for r in ROWS),s.CHECKPOINT)}
    result={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),
        'classification':'SAVED_SELECTOR_RECORD_EVIDENCE_AND_CI_CLOSEOUT_NOT_NATIVE_ACCEPTANCE',
        'completed_milestones':audits,'focused_tests':close_tests,'source_bindings':bindings,
        'session_totals':{'new_focused_implementation_tests':39,'new_reference_sites':649,
            'saved_references_reused':15,'new_sampled_bytes':61024,'candidate_reconstructions':1,
            'new_emulator_processes':0,'accepted_native_cases_replayed':0,'rom_changes':0},
        'actions_observed':recent,'cached_stage79_native_steps':cache_jobs,
        'external_comparison_reference':REFERENCE,
        'network_log_correction_ja':'前工程SELECTOR-OWNERSのNetwork「外部技術資料なし」はセッション全体では不正確。'
            '上記pret sourceをGitHub接続から比較参照した。旧ログは保存し、この追記を訂正記録とする。',
        'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0,'rom_changes':0,'ring_acquisition_accepted':False,'release_ready':False}
    # Metadataの最新停止点だけ更新。受入原本と次に読む未完契約を変更しない。
    stop=('selector参照採取15tests/run35073059942とrecord初期化24tests/run35074318490は'
          '原Actions成功・artifact・保存commitと照合済み。2工程の新規参照649、保存再利用15、'
          '採取61024byte、候補復元計1、native/既読ABI/受入BP再実行0。'
          'record初期化はcaller提供域、mode2は容量とは別のLIMIT依存。制御域alias候補の実到達は未証明。')
    state['ring_selector_closeout']={'path':REPORT,'source_head':head,'run_id':result['run_id']}
    state['latest_ring_diagnostic']=state['ring_selector_closeout'].copy()
    state['source_change_review_ja']=state['bp']['current_stop']=stop
    state['next_action']['read_paths']=[REPORT,ROWS[1]['report'],ROWS[0]['report'],'scripts/pr16_ring_record_init.py']
    state['observed_head']=head
    state['observed_head_semantics']='2完了工程の証拠/CI照合source HEAD。完了commitはremote ref/Actionsで確認。'
    state['observed_head_checks']['reason_ja']='run35073059942/35074318490 success確認済み。記録commitのaction_requiredは未実行のまま保持しsuccessへ変更しない。'
    state['session_execution_summary']={**result['session_totals'],'scope_ja':stop}
    state['do_not_repeat'].append('selector採取・record初期化と今回closeoutの保存原本を再利用。受入済みnative/BP/既読ABIを再実行しない。')
    backlog=s.load(s.BACKLOG)
    next(x for x in backlog['remaining_conditions'] if x['id']=='NATURAL_CAPTURE_GEAR')['ring_selector_closeout']=REPORT
    (s.ROOT/REPORT).write_bytes(s.stable(result))
    for p in (*CODE,REPORT):state['source_bindings'][p]=s.identity((s.ROOT/p).read_bytes())
    (s.ROOT/s.STATE).write_bytes(s.stable(state));(s.ROOT/s.BACKLOG).write_bytes(s.stable(backlog))
    for mode in ('render','check'):subprocess.run([sys.executable,'scripts/pr16_resume.py',mode],check=True)
    resume_tests=test_suite('test_pr16_resume.py');s.need(resume_tests['tests_run']==24,'resume test count')
    (OUT/'resume-tests.json').write_bytes(s.stable(resume_tests))
    s.need(s.identity((s.ROOT/s.CHECKPOINT).read_bytes())==bp,'BP changed')
    stamp=datetime.now(timezone.utc).isoformat()
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        '- Status: DONE / 2工程の原本・CI照合。Ring通常取得は未受入。\n- Version: PR16 selector/record closeout\n'
        f'- Summary: {stop}\n- Verify: closeout8 tests、更新影響のresume24 tests、render/check、task graph、最終index guardとdiff。旧15/24 ABI testsは再実行しない。\n'
        f'- Evidence: {REPORT}; commits 5a3a79347acd / 8b626df3ef87; run35073059942 / run35074318490 success。\n'
        f'- Files changed: {", ".join(CODE)}、closeout JSON、固定MD/JSON、P08参照、両ログ。\n'
        '- Preserved: 本closeoutは候補復元0/native0/ROM変更0。BP受入原本、2工程の原本・失敗履歴は不変。\n'
        f'- Network/reference: GitHub/Actions。比較参照pret/pokefirered@{REFERENCE["ref"]} src/event_data.c / src/quest_log.c。外部コード転記・候補ROMへの同一性主張なし。\n'
        f'- Correction: {result["network_log_correction_ja"]}\n'
        '- Commit: task graph/最終index guard成功後、最新HEAD照合して同branch非force push。全体guard PASS・全CI green・merge/release/baseline変更を主張しない。\n'
        f'- Next: {state["next_action"]["goal_ja"]}\n')
    for p in s.LOGS:
        s.need(TASK not in (s.ROOT/p).read_text(),'duplicate log')
        with (s.ROOT/p).open('a',encoding='utf-8') as stream:stream.write(entry)
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],check=True)
    subprocess.run(['git','add','--',*OUTPUTS],check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*CODE,*OUTPUTS));guard.guard()
    saved.bindings_fresh(s.ROOT,bindings);subprocess.run(['git','diff','--cached','--check'],check=True)
    s.assert_remote(head,attempts=3)
    for k,v in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):
        subprocess.run(['git','config',k,v],check=True)
    subprocess.run(['git','commit','-m',TASK+': 2工程の成功CI・原本・次の未完契約を固定'],check=True)
    commit=s.cmd('git','rev-parse','HEAD')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+s.BRANCH],check=True);s.assert_remote(commit,attempts=12)
    for p in OUTPUTS:s.need(subprocess.check_output(['git','show','HEAD:'+p])==(s.ROOT/p).read_bytes(),'commit bytes')
    s.need(not s.cmd('git','status','--porcelain','--untracked-files=no'),'tracked residue')
    (OUT/'result.json').write_bytes(s.stable({'status':'PASS_NONFORCE_PUSHED','commit':commit,
        'closeout_tests':close_tests,'resume_tests':resume_tests,'new_emulator_processes':0,
        'ring_acquisition_accepted':False,'release_ready':False}))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)

if __name__=='__main__':main()
