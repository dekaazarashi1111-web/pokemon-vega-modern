#!/usr/bin/env python3
"""One new boot observation; retain evidence, fixed handoff and non-force commit."""
from __future__ import annotations
from datetime import datetime, timezone
import json
import io
import zipfile
import os
from pathlib import Path
import subprocess
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
import pr16_ring_caller_snapshot as a

BASE='97529e38a046ae6d9a76db7660172db5defb254f'
TASK='PR-P08-7-RING-CALLER-SNAPSHOT'
SELF='scripts/pr16_ring_snapshot_record.py'
TEST='tests/test_pr16_ring_caller_snapshot.py'
WORKFLOW='.github/workflows/pr16-ring-caller-snapshot.yml'
REPORT='content/modernization/pr16_ring_caller_snapshot.json'
TRACE='content/modernization/pr16_ring_caller_snapshot_evidence/trace.jsonl'
FIRST_RAW=str(Path(TRACE).with_name('attempt1-stdout.txt'))
FIRST_REPORT=str(Path(TRACE).with_name('attempt1.json'))
OUT=s.ROOT/'.local/pr16-ring-caller-snapshot'
CODE=(SELF,a.SELF,a.SOURCE,TEST,WORKFLOW)
OUTPUTS=(REPORT,TRACE,FIRST_RAW,FIRST_REPORT,s.STATE,s.DOC,s.BACKLOG,*s.LOGS)
SOURCES=(*CODE,a.PRIOR,a.compose.SELF,s.SELF,'scripts/pr16_resume.py',
         'scripts/pr16_ring_compiled_record.py','scripts/guard_private_files.py',
         'scripts/pr16_ring_common_tail_bytes.py','scripts/pr16_ring_zero_bytes.py',
         '.github/workflows/pr16-ring-callee-bytes.yml','infra/toolchain_manifest.json',
         'config/github_private_environment.json',s.CHECKPOINT)


def command(*args):
    subprocess.run(args,cwd=s.ROOT,check=True)



FIRST_HEAD='80019e2ba09342a642abbabb592245a7a98bb905'
FIRST_RUN,FIRST_JOB,FIRST_ARTIFACT=35059235641,104675829781,10432365087
FIRST_ZIP_SHA='77fa7da259535201e5558bfccf02e296f7a134b2b359e8c1280ddd23bea87842'
FIRST_MEMBERS={
    'native.stderr.txt':(0,'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'),
    'preflight.json':(5394,'6f7b78cfe3f711836ecfd935aa70d43276ca22fadaf59e429a049ac102337771'),
    'process.json':(380,'9563c2d47bd418a8e4a7ab22139c4f0b40e519003a3d8d5d746832181bb085f8'),
    'tests.txt':(4677,'bea7962d1f9c36a32df6636ae033ad18540d7471a633e07c6087ec2ceffdfe9b'),
    'trace.jsonl':(673936,'eb8e2f9a552192b8435a40236d57fee0283a013a0ede78aa6584dd3a6e5dda83')}


def preserve_first():
    """Pin failed transport/NO_HIT evidence; do not replay or promote failure."""
    run=s.api('actions/runs/'+str(FIRST_RUN));job=s.api('actions/jobs/'+str(FIRST_JOB))
    s.need(run['head_sha']==FIRST_HEAD and run['status']=='completed'
           and run['conclusion']=='failure' and job['run_id']==FIRST_RUN
           and job['conclusion']=='failure','first failure identity')
    steps={r['number']:r for r in job['steps']}
    s.need(steps[3]['conclusion']==steps[4]['conclusion']=='success'
           and steps[5]['conclusion']=='failure','first failure stage differs')
    artifact=s.api('actions/artifacts/'+str(FIRST_ARTIFACT))
    s.need(artifact['workflow_run']['id']==FIRST_RUN
           and artifact['workflow_run']['head_sha']==FIRST_HEAD
           and not artifact['expired'],'first artifact provenance')
    raw=subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/artifacts/'
                                 +str(FIRST_ARTIFACT)+'/zip'],cwd=s.ROOT)
    s.need(s.identity(raw)=={'size':13451,'sha256':FIRST_ZIP_SHA},'first ZIP changed')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        s.need(len(archive.infolist())==5 and set(archive.namelist())==set(FIRST_MEMBERS),
               'first archive membership')
        members={name:archive.read(name) for name in FIRST_MEMBERS}
    for name,data in members.items():
        size,sha=FIRST_MEMBERS[name]
        s.need(s.identity(data)=={'size':size,'sha256':sha},'first member changed')
        data.decode('utf8');s.need(b'\0' not in data,'first export not text')
    before=json.loads(members['preflight.json']);process=json.loads(members['process.json'])
    s.need(before['head']==FIRST_HEAD and before['run_id']==FIRST_RUN,'first preflight identity')
    for name,binding in before['source_bindings'].items():
        data=subprocess.check_output(['git','show',FIRST_HEAD+':'+name],cwd=s.ROOT)
        s.need(s.identity(data)==binding,'first source binding differs')
    expected={k:s.CANDIDATE[k] for k in ('size','sha256')}
    s.need(process['returncode']==0 and not process['timed_out']
           and process['actual_new_processes']==process['fresh_cores_started']==1
           and process['rom_before']==process['rom_after']==expected,'first native process differs')
    rows=[json.loads(line) for line in members['trace.jsonl'].decode().splitlines()
          if line.startswith('{')]
    s.need(len(rows)==1 and rows[0]['kind']=='summary' and rows[0]['hits']==0
           and rows[0]['search_steps']==rows[0]['search_limit']==240000000
           and rows[0]['unobserved_title_frames']==1200,'first diagnostic scope differs')
    value={'classification':'FAILED_TRANSPORT_WITH_BOUNDED_NO_HIT_NOT_ABSENCE_PROOF',
           'run_id':FIRST_RUN,'job_id':FIRST_JOB,'source_head':FIRST_HEAD,
           'run_conclusion':'failure','artifact_id':FIRST_ARTIFACT,'archive':s.identity(raw),
           'members':{p:s.identity(v) for p,v in members.items()},'process':process,
           'focused_tests':before['tests'],'raw_stdout_path':FIRST_RAW,
           'summary_projected_for_diagnosis_only':rows[0],
           'failure':'mGBA default logger mixed non-JSON lines into stdout; strict parser rejected it',
           'revision':'redirect logger to stderr and observe the previously unobserved reset prefix with corrected keypad sequence',
           'new_emulator_processes':1,'candidate_reconstructions':1,
           'unchanged_native_retry':False,'actual_caller_observed':False,
           'ring_acquisition_accepted':False,'release_ready':False}
    (OUT/'attempt1-stdout.txt').write_bytes(members['trace.jsonl'])
    (OUT/'attempt1.json').write_bytes(s.stable(value))
    return value


def preflight():
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    s.need(os.environ['GITHUB_REPOSITORY']==s.REPO
           and os.environ['GITHUB_REF']=='refs/heads/'+s.BRANCH,'repository/branch')
    head=s.cmd('git','rev-parse','HEAD')
    s.need(head==os.environ['GITHUB_SHA'],'checkout HEAD')
    s.assert_remote(head,attempts=3)
    command('git','merge-base','--is-ancestor',BASE,head)
    s.need(not (s.ROOT/REPORT).exists(),'already recorded: reuse evidence instead of replay')
    state=resume.validate(s.ROOT)
    s.need(state['bp']['spending_accepted'] is True and s.GAP in state['remaining_physical_gap_ids'],
           'accepted/unfinished boundary changed')
    prior=s.load(a.PRIOR);saved.bindings_fresh(s.ROOT,prior['source_bindings'])
    s.need(prior['analysis']['candidate']==s.CANDIDATE,'saved candidate differs')
    observed=[]
    for rid,sha in ((prior['run_id'],prior['source_head']),
                    (34946969126,'0b7497b575a3180a045f2be377386490f192a012')):
        run=s.api('actions/runs/'+str(rid))
        s.need(run['head_sha']==sha and run['status']=='completed'
               and run['conclusion']=='success','prior Actions not successful')
        observed.append({k:run[k] for k in ('id','head_sha','status','conclusion')})
    OUT.mkdir(parents=True,exist_ok=True)
    preserve_first()
    bindings={p:s.identity((s.ROOT/p).read_bytes()) for p in SOURCES}
    suite=unittest.defaultTestLoader.discover(str(s.ROOT/'tests'),pattern=Path(TEST).name)
    with (OUT/'tests.txt').open('w') as stream:
        tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    s.need(tests.wasSuccessful() and not tests.skipped and tests.testsRun>=46,'focused tests')
    recent=s.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=10')
    value={'head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':bindings,
           'checkpoint':s.identity((s.ROOT/s.CHECKPOINT).read_bytes()),
           'tests':{'tests_run':tests.testsRun,'failures':0,'errors':0,'skipped':0},
           'prior_actions_verified_without_replay':observed,
           'actions_observed_before_record':[{k:r[k] for k in
               ('id','name','head_sha','status','conclusion')} for r in recent['workflow_runs']]}
    (OUT/'preflight.json').write_bytes(s.stable(value))
    print('PREFLIGHT_PASS_NO_ACCEPTED_REPLAYS',head)


def restore():
    import pr16_ring_common_tail_bytes as old
    old.OUT=OUT
    old.restore()  # hash-locked reconstruction only; no old byte or native test


def record():
    import pr16_resume as resume
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_compiled_record as guard
    before=json.loads((OUT/'preflight.json').read_bytes());head=before['head']
    s.need(head==os.environ['GITHUB_SHA'] and not (s.ROOT/REPORT).exists(),'repeated/stale run')
    s.assert_remote(head,attempts=3);saved.bindings_fresh(s.ROOT,before['source_bindings'])
    result=a.capture(OUT)
    s.need(result['new_emulator_processes']==1 and result['fresh_cores']==1
           and result['accepted_native_cases_replayed']==0 and result['rom_changes']==0
           and result['ring_acquisition_accepted'] is False and result['release_ready'] is False,
           'native diagnostic scope changed')
    target=s.ROOT/TRACE;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes((OUT/'trace.jsonl').read_bytes())
    for name,source in ((FIRST_RAW,'attempt1-stdout.txt'),(FIRST_REPORT,'attempt1.json')):
        (s.ROOT/name).write_bytes((OUT/source).read_bytes())
    value={'schema_version':1,'task':TASK,'source_head':head,'run_id':before['run_id'],
           'run_status_at_record':'in_progress','analysis':result,
           'previous_failed_attempt':dict(path=FIRST_REPORT,run_id=FIRST_RUN),
           'session_execution':{'new_emulator_processes':2,'fresh_cores':2,'candidate_reconstructions':2,
                                'accepted_native_cases_replayed':0,'rom_changes':0},
           'raw_trace':dict(path=TRACE,**s.identity(target.read_bytes())),
           'source_bindings':before['source_bindings'],'focused_tests':before['tests'],
           'prior_actions_verified_without_replay':before['prior_actions_verified_without_replay'],
           'actions_observed_before_record':before['actions_observed_before_record']}
    (s.ROOT/REPORT).write_bytes(s.stable(value))
    state=resume.validate(s.ROOT);backlog=s.load(s.BACKLOG)
    row=next(r for r in backlog['remaining_conditions'] if r['id']=='NATURAL_CAPTURE_GEAR')
    s.need(s.GAP in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][s.GAP] is None,
           'Ring gap/entry must remain unaccepted')
    stop=(f'読取専用boot観測器と異常系{before["tests"]["tests_run"]} testsを実装。'
          f'同一candidateの新規1 processでFlagSet入口を{result["observed_calls"]}回観測、'
          f'{result["bound_calls"]}回の実SP/LR・保存slot/flag/record/counterを保存caller条件式と照合。'
          '初回run35059235641は0hit・stdout混入による記録失敗として原本を保持。合計新規2 process、受入済み再実行0。'
          'これはboot caller診断でmap97/80のRing通常取得ではない。'
          'allocation所有範囲・通常mapping・同期/DMA保証は未証明。旧18ownerと正式BP受入を保持。')
    next_step=('保存済みboot trace/実caller照合を再実行せず再利用する。'
               '次はmap97/80 FINAL_LEAGUE_CLEAREDの実経路callerとrecord allocation所有範囲を限定し、'
               '同期/IRQ/DMA条件を独立証拠で解決する。boot callerやfixtureだけで旧18ownerを除外しない。'
               'Ring正規取得owner確定後に取得・装備実戦・通常保存へ進む。BP受入済み試験は再実行しない。')
    if not result['bound_calls']:
        next_step=('保存traceのrejected_calls/NO_HIT理由を先に検討し、同一probeの無変更再実行はしない。'+next_step)
    state['ring_caller_snapshot']={'path':REPORT,'source_head':head,'run_id':before['run_id']}
    state['latest_ring_diagnostic']=state['ring_caller_snapshot'].copy()
    row['ring_caller_snapshot']=REPORT
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=next_step
    state['next_action']['read_paths']=[REPORT,a.SELF,a.PRIOR]
    state['observed_head']=head
    state['observed_head_semantics']='boot実caller限定診断のsource HEAD。latest_native_*は既存の正式BP checkpoint照合欄を保持し、最新Ring診断はlatest_ring_diagnosticに分離。'
    state['observed_head_checks']['reason_ja']=(f'先行caller/BP Actions成功を照合。今回run{before["run_id"]}は記録時in_progress。'
        '観測器工程の成功はRing受入ではない。action_requiredをsuccessへ読み替えない。')
    state['session_execution_summary']={'new_emulator_processes':2,'fresh_cores':2,
        'rom_changes':0,'candidate_reconstructions':2,'accepted_standalone_replays':0,
        'scope_ja':stop}
    state['do_not_repeat'].append('boot FlagSet caller snapshotは保存原本を再利用。同一観測器・同一candidateの無変更再実行をしない。fixture/bootをRing物理受入へ昇格しない。')
    for p in (*CODE,REPORT,TRACE,FIRST_RAW,FIRST_REPORT):state['source_bindings'][p]=s.identity((s.ROOT/p).read_bytes())
    (s.ROOT/s.STATE).write_bytes(s.stable(state));(s.ROOT/s.BACKLOG).write_bytes(s.stable(backlog))
    for mode in ('render','check'):command(sys.executable,'scripts/pr16_resume.py',mode)
    s.need(s.identity((s.ROOT/s.CHECKPOINT).read_bytes())==before['checkpoint'],'BP checkpoint modified')
    stamp=datetime.now(timezone.utc).isoformat()
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        '- Status: DONE / 読取専用観測・保存照合工程。Ring通常取得・同期/allocation証明は未完。\n'
        '- Version: PR16 Ring actual boot caller snapshot\n'
        f'- Summary: {stop}\n- Verify: focused tests {before["tests"]["tests_run"]} PASS、C warnings-as-errors compile、'
        '有限新規native観測、原ROM前後hash、read-only render/check、task graph、最終index差分guard、diff。\n'
        f'- Evidence: {REPORT}; {TRACE}; source={head}; run={before["run_id"]}（記録時in_progress）。\n'
        '- Preserved: ROM変更0、受入済みnative/既読ABI再実行0、正式BP checkpoint不変。初回失敗を含む新規boot診断2 process/2 cores、候補復元2。\n'
        f'- Files changed: {", ".join(CODE)}, report/trace、固定MD/JSON、P08参照、両ログ。\n'
        '- Preparation: 97529e38のsource-only workspace取得を再利用。ROM/save原本をtracked/artifactへ追加しない。\n'
        '- Commit: 現HEAD競合を検査後、同branchへ通常commit/非force push。自己SHAはremote receipt参照。\n'
        '- Network: GitHub connector/Actions、既存hash固定private環境。外部技術資料なし。\n'
        '- Boundary: 既存全体guard違反は前後一致/新規0で照合。全体guard PASS・全CI green・merge/release/baseline変更を主張しない。\n'
        f'- Next: {next_step}\n')
    for p in s.LOGS:
        s.need(TASK not in (s.ROOT/p).read_text(),'duplicate log entry')
        with (s.ROOT/p).open('a') as stream:stream.write(entry)
    command(sys.executable,'scripts/validate_task_graph.py')
    command('git','add','--',*OUTPUTS)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*CODE,*OUTPUTS));guard.guard()
    command('git','diff','--cached','--check');saved.bindings_fresh(s.ROOT,before['source_bindings'])
    s.assert_remote(head,attempts=3)
    command('git','config','user.name','github-actions[bot]')
    command('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    command('git','commit','-m',TASK+': 実caller限定観測・条件付き照合と引継ぎを保存')
    commit=s.cmd('git','rev-parse','HEAD')
    command('git','push','origin','HEAD:refs/heads/'+s.BRANCH);s.assert_remote(commit,attempts=12)
    for p in OUTPUTS:
        s.need(subprocess.check_output(['git','show','HEAD:'+p],cwd=s.ROOT)==(s.ROOT/p).read_bytes(),'committed bytes differ')
    s.need(not s.cmd('git','status','--porcelain','--untracked-files=no'),'tracked residue')
    receipt={'status':'PASS_RECORDED_NONFORCE_PUSHED','commit':commit,'source_head':head,
        'run_id':before['run_id'],'tests':before['tests'],'observed_calls':result['observed_calls'],
        'bound_calls':result['bound_calls'],'new_emulator_processes':1,'session_new_emulator_processes':2,
        'first_failed_run':FIRST_RUN,'accepted_native_cases_replayed':0,
        'ring_acquisition_accepted':False,'release_ready':False}
    (OUT/'recorded-result.json').write_bytes(s.stable(receipt));print(json.dumps(receipt))

if __name__=='__main__':
    s.need(len(sys.argv)==2 and sys.argv[1] in ('preflight','restore','record'),'phase required')
    {'preflight':preflight,'restore':restore,'record':record}[sys.argv[1]]()
