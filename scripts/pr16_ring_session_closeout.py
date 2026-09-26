#!/usr/bin/env python3
"""2実装工程の成功原本・保存commit・未完境界を照合。探索/ABI/nativeの再実行なし。"""
from __future__ import annotations
import copy
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE='f57fcf3d10662fc302ea4ed8f2548e4570251896'
SLUG='pr16-ring-session-closeout'
TASK='PR-P08-7-RING-SESSION-CLOSEOUT'
TITLE='分岐frontierと7delegateの成功原本・未完契約・非再実行記録を確定'
SELF='scripts/pr16_ring_session_closeout.py'
TEST='tests/test_pr16_ring_session_closeout.py'
WORKFLOW='.github/workflows/pr16-ring-session-closeout.yml'
FRONTIER='content/modernization/pr16_ring_branch_frontier.json'
PRIOR='content/modernization/pr16_ring_delegate_contracts.json'
REPORT='content/modernization/pr16_ring_session_closeout.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=18
EXTRA_CODE=()
SOURCES=(FRONTIER,PRIOR,'scripts/pr16_ring_control_closeout.py')
ROWS=({'run': 35086278411, 'job': 104761735917, 'artifact': 10442551182, 'tests': 30, 'head': '82614a5fabc17ba3de1d22b990c272b2ac6b25e8', 'commit': 'd059ce8696dce5f220790721eb495c7ae38de8cf', 'base': '37e57f61bc891c5b8fb862b1b556a51276b957ea', 'report': 'content/modernization/pr16_ring_branch_frontier.json', 'task': 'PR-P08-7-RING-BRANCH-FRONTIER', 'archive': {'size': 7097, 'sha256': '07aefc3352ee190042049bcc02032230b4e19acf9eb1056adf72adf913183282'}, 'extra': ['preflight.json']}, {'run': 35087488359, 'job': 104765650607, 'artifact': 10443061273, 'tests': 36, 'head': '935e9116d3f2bff62b00b95eebe7e7bafb372068', 'commit': 'f57fcf3d10662fc302ea4ed8f2548e4570251896', 'base': 'd059ce8696dce5f220790721eb495c7ae38de8cf', 'report': 'content/modernization/pr16_ring_delegate_contracts.json', 'task': 'PR-P08-7-RING-DELEGATE-CONTRACTS', 'archive': {'size': 4004, 'sha256': '1942a182acff72bfb309fb55334dc35126fda201544add7067186e33e38ad2ca'}, 'extra': []})
NO_REPEAT=('今回frontier30testsと7delegate36testsは成功Actions・原artifact・保存commitまで照合済み。'
           '新規66tests/限定8191vectorの実装成果を再利用し、同一探索・byte採取・ABI・受入BP/nativeを繰り返さない。')
VECTOR_KEYS=('fill_vectors','reset_vectors','gate_vectors','status_prefix_vectors','reader_vectors','date_vectors')
ZERO_KEYS=('rom_changes','new_emulator_processes','accepted_native_cases_replayed','prior_abi_classifications_replayed')
FALSE_KEYS=('ring_acquisition_accepted','release_ready','all_callers_resolved','all_runtime_owners_excluded',
            'caller_pointer_size_limit_proven','selector1_runtime_observed','selector2_runtime_observed','old_frontier_removed')


def integer(value):
    s.need(type(value) is int and value>=0,'counter type/range')
    return value


def totals(frontier,contracts):
    for obj in (frontier,contracts):
        s.need(obj['candidate']==s.CANDIDATE,'candidate mismatch')
        for key in ZERO_KEYS: s.need(integer(obj[key])==0,'execution replay or ROM change')
        for key in FALSE_KEYS: s.need(obj[key] is False,'acceptance/absence overclaim')
    s.need(frontier['target']==0x08113984 and frontier['references']==[],'reference boundary changed')
    s.need(integer(frontier['candidate_reconstructions'])==1 and integer(contracts['candidate_reconstructions'])==0,'reconstruction scope')
    s.need(len(frontier['old_unread_targets'])==18 and len(set(frontier['old_unread_targets']))==18
           and contracts['old_unread_targets']==frontier['old_unread_targets'],'old frontier changed')
    s.need(contracts['unread_external_targets']==[0x0912C4A9,0x0912C555,0x09099E05],'unread delegates changed')
    counts=contracts['counts']
    s.need(tuple(integer(counts[k]) for k in VECTOR_KEYS)==(2584,256,256,256,3072,1767),'vector totals changed')
    s.need(contracts['readers']['physical_hardware_behavior_proven'] is False
           and contracts['readers']['supplied_io_stream_only'] is True
           and contracts['date_validator']['all_months_or_leap_years_proven'] is False,'model boundary')
    s.need(integer(frontier['new_window_bytes'])==3326 and integer(frontier['saved_bytes_reused'])==622,'sample totals changed')
    return {'new_implementation_tests':66,'new_reference_candidates':0,'new_sampled_bytes':3326,'saved_bytes_reused':622,
        'bounded_delegate_vectors':sum(counts[k] for k in VECTOR_KEYS), 'delegate_vector_counts':{k:counts[k] for k in VECTOR_KEYS},
        'candidate_reconstructions':1,'new_emulator_processes':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0,'rom_changes':0}


def verify_cached_jobs(jobs):
    s.need(jobs['total_count']<=100 and len(jobs['jobs'])==jobs['total_count'],'jobs pagination')
    rows=[]
    for job in jobs['jobs']:
        if not job['name'].startswith('domain ('):continue
        s.need(job['status']=='completed' and job['conclusion']=='success','domain not successful')
        steps=[x for x in job['steps'] if x['name']=='domainをmGBAで実行']
        s.need(len(steps)==1 and steps[0]['conclusion']=='skipped','automatic native replay')
        rows.append({'job_id':job['id'],'name':job['name'],'native_step_conclusion':'skipped'})
    s.need(len(rows)==7 and len({r['name'] for r in rows})==7,'seven domains required')
    return rows


def analyze(prior,out):
    import pr16_ring_control_closeout as old
    import pr16_ring_flagset_continuation as saved
    head=s.cmd('git','rev-parse','HEAD'); audits=[]
    for row in ROWS:
        report=s.load(row['report']);saved.bindings_fresh(s.ROOT,report['source_bindings'])
        run=s.api('actions/runs/'+str(row['run']));job=s.api('actions/jobs/'+str(row['job']))
        old.successful_actions(run,job,row)
        meta=s.api('actions/artifacts/'+str(row['artifact']))
        s.need(meta['id']==row['artifact'] and not meta['expired'] and meta['workflow_run']['id']==row['run']
               and meta['workflow_run']['head_sha']==row['head'] and meta['digest']=='sha256:'+row['archive']['sha256'],'artifact metadata')
        raw=subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/artifacts/'+str(row['artifact'])+'/zip'],cwd=s.ROOT)
        proof=old.audit(old.read_archive(raw,row),row,report)
        s.need(subprocess.check_output(['git','show',row['commit']+':'+row['report']],cwd=s.ROOT)==(s.ROOT/row['report']).read_bytes(),'saved report changed')
        s.need(s.cmd('git','rev-parse',row['commit']+'^')==row['head'],'record parent mismatch')
        subprocess.run(['git','merge-base','--is-ancestor',row['commit'],head],cwd=s.ROOT,check=True)
        proof['observed_run']={k:run[k] for k in ('id','head_sha','status','conclusion')};audits.append(proof)
    recent=[];cached=[]
    for sha in dict.fromkeys([ROWS[0]['base'],head]+[r[k] for r in ROWS for k in ('head','commit')]):
        runs=s.api('actions/runs?head_sha='+sha+'&per_page=100')
        s.need(runs['total_count']<=100,'Actions pagination')
        for run in runs['workflow_runs']:
            recent.append({k:run[k] for k in ('id','name','head_sha','event','status','conclusion')})
            if run['path']=='.github/workflows/modernization-stage79-mgba.yml' and run['status']=='completed' and run['conclusion']=='success':
                jobs=s.api('actions/runs/'+str(run['id'])+'/jobs?per_page=100')
                cached.extend({'run_id':run['id'],**row} for row in verify_cached_jobs(jobs))
    frontier=s.load(FRONTIER)['analysis']; contracts=prior['analysis']
    result={'classification':'FRONTIER_AND_DELEGATE_ORIGINALS_VERIFIED_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'completed_milestones':audits,'session_totals':totals(frontier,contracts),
        'actions_observed':recent,'cached_stage79_native_steps':cached,
        'next_unread_contracts':{'external_targets':contracts['unread_external_targets'],
            'month_table':contracts['date_validator']['month_table_extent_required'],
            'initializer':frontier['target'],'unsearched_forms':frontier['unsearched_forms'],
            'actual_caller_pointer_size_limit_proven':False},
        'old_unread_targets':copy.deepcopy(contracts['old_unread_targets']),
        'old_frontier_removed':False,'all_runtime_owners_excluded':False,'all_callers_resolved':False,
        'candidate_reconstructions':0,'new_emulator_processes':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0,'rom_changes':0,'ring_acquisition_accepted':False,'release_ready':False}
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return ('branch-frontier30testsと7delegate36testsを成功Actions・原artifact・保存commitまで照合。'
            '新規3326byte/保存622byte、未検索形式の参照候補0。限定8191vectorを記録。候補復元計1、ROM変更/native/BP受入再実行0。'
            '0候補を全caller不在、供給bit列をhardware受入へ読み替えない。Ring取得は未受入。',
            '保存7delegate契約を再利用し、0x0912C4A9/0x0912C555/0x09099E05とmonth table0x09169530..0x09169560、'
            'initializer0x08113984のcomputed/RAM/mirrored-PC caller・pointer/size/LIMITを追う。'
            '既読byte/ABI/BPを再実行しない。旧18ownerとRing正規取得・装備実戦・保存、policy/Circus/P08は未完。')


if __name__=='__main__':
    s.need(sys.argv[1:]==['run'],'runだけを許可');s.run(sys.modules[__name__])
