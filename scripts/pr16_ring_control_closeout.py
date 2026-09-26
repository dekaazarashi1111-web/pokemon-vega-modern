#!/usr/bin/env python3
"""今回2工程の原本/Actions/非force保存を照合。ROM・局所ABIを再実行しない。"""
from __future__ import annotations
import copy
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE='314c49d97312ebdc56fb3cfd608719b784a84b88'
SLUG='pr16-ring-control-closeout'
TASK='PR-P08-7-RING-CONTROL-CLOSEOUT'
TITLE='caller採取と制御役割の成功原本・保存commit・未完境界を固定'
SELF='scripts/pr16_ring_control_closeout.py'
TEST='tests/test_pr16_ring_control_closeout.py'
WORKFLOW='.github/workflows/pr16-ring-control-closeout.yml'
PRIOR='content/modernization/pr16_ring_control_roles.json'
REPORT='content/modernization/pr16_ring_control_closeout.json'
# 共通記録器に最新診断の入口を更新させる。古い工程のキーは履歴として保持。
KEY='latest_ring_diagnostic'
MIN_TESTS=18
EXTRA_CODE=()
ROWS=(
 {'run':35082799310,'job':104750531087,'artifact':10440808215,'tests':20,
  'head':'fd4ba2041e61d425bec24d107d4abe08f7b94f38','commit':'781fd40d23c75bcc11f9d51320d90f5ebcee7e0f',
  'base':'9d0910f84f6fdda11649c3f8db5bb3e156a4a90e',
  'report':'content/modernization/pr16_ring_record_callers.json','task':'PR-P08-7-RING-RECORD-CALLERS',
  'archive':{'size':28805,'sha256':'d2773d8c499f8bf5caa63f7be68b5f468cb9c1742374778133ec18d1c538fbff'},
  'extra':['preflight.json']},
 {'run':35084187651,'job':104755013673,'artifact':10440984849,'tests':35,
  'head':'8050cb1a2cd17f127922483247c34829aa92e287','commit':BASE,
  'base':'781fd40d23c75bcc11f9d51320d90f5ebcee7e0f',
  'report':PRIOR,'task':'PR-P08-7-RING-CONTROL-ROLES',
  'archive':{'size':3963,'sha256':'25e94409344ad57d724e12e1e78d3106bf242758ebbc1fe6ce7f3ac6ecdf3981'},
  'extra':[]})
SOURCES=tuple(r['report'] for r in ROWS)
NO_REPEAT=('run35082799310のcaller採取20testsとrun35084187651のrole35testsは成功原本/保存commitまで照合済み。'
           '今回closeoutを含め保存原本を再利用し、同条件のbyte採取/ABI/nativeを再実行しない。')


def read_archive(raw,row):
    s.need(s.identity(raw)==row['archive'],'archive identity')
    expected={'analysis.json','guard.json','recorded-result.json','tests.json','tests.txt',*row['extra']}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        s.need(len(names)==len(set(names)) and set(names)==expected,'archive members')
        s.need(all(Path(n).name==n for n in names) and sum(i.file_size for i in z.infolist())<=2000000,'archive bounds')
        s.need(all((i.external_attr>>16)&0o170000 != 0o120000 for i in z.infolist()),'archive symlink')
        data={n:z.read(n) for n in names}
    for raw_member in data.values():
        raw_member.decode('utf-8')
        s.need(b'\0' not in raw_member and not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN [A-Z ]*PRIVATE KEY-----',raw_member),'unsafe text')
    return data


def audit(data,row,report):
    receipt=json.loads(data['recorded-result.json']);analysis=json.loads(data['analysis.json'])
    tests=json.loads(data['tests.json']);guard=json.loads(data['guard.json'])
    s.need(analysis==report['analysis'],'analysis mismatch')
    s.need(receipt['status']=='PASS_RECORDED_NONFORCE_PUSHED' and receipt['task']==row['task']
           and receipt['source_head']==report['source_head']==row['head']
           and receipt['commit']==row['commit'] and receipt['run_id']==report['run_id']==row['run'],'receipt identity')
    s.need(tests==receipt['tests']==report['focused_tests'] and tests['tests_run']==row['tests']
           and tests['successful'] is True and (tests['failures'],tests['errors'],tests['skips'])==(0,0,0),'tests mismatch')
    s.need(receipt['outputs']==[row['report'],s.STATE,s.DOC,s.BACKLOG,*s.LOGS],'output scope')
    s.need(guard['base']==row['base'] and guard['new_violations']==0 and guard['exact_output_match'] is True
           and guard['full_guard_before']==guard['full_guard_after']==1 and guard['full_guard_pass_claimed'] is False,'guard boundary')
    for obj in (analysis,receipt):
        s.need(obj['new_emulator_processes']==0 and obj['ring_acquisition_accepted'] is False and obj['release_ready'] is False,'acceptance boundary')
    s.need(analysis['candidate']==s.CANDIDATE and analysis['rom_changes']==0
           and analysis['accepted_native_cases_replayed']==0 and analysis['prior_abi_classifications_replayed']==0,'analysis scope')
    return {'run_id':row['run'],'job_id':row['job'],'artifact_id':row['artifact'],'archive_identity':row['archive'],
        'receipt':receipt,'guard':guard,'focused_tests':tests,'original_tests_text':data['tests.txt'].decode(),
        'member_identities':{n:s.identity(b) for n,b in data.items()}}


def successful_actions(run,job,row):
    s.need(run['id']==row['run'] and run['head_sha']==row['head'] and run['status']=='completed' and run['conclusion']=='success','run not successful')
    s.need(job['id']==row['job'] and job['run_id']==row['run'] and job['status']=='completed' and job['conclusion']=='success'
           and job['steps'] and all(x['conclusion']=='success' for x in job['steps']),'job not successful')


def analyze(prior,out):
    import pr16_ring_flagset_continuation as saved
    head=s.cmd('git','rev-parse','HEAD');audits=[]
    for row in ROWS:
        report=s.load(row['report']);saved.bindings_fresh(s.ROOT,report['source_bindings'])
        run=s.api('actions/runs/'+str(row['run']));job=s.api('actions/jobs/'+str(row['job']))
        successful_actions(run,job,row)
        meta=s.api('actions/artifacts/'+str(row['artifact']))
        s.need(meta['id']==row['artifact'] and not meta['expired'] and meta['workflow_run']['id']==row['run']
               and meta['workflow_run']['head_sha']==row['head'] and meta['digest']=='sha256:'+row['archive']['sha256'],'artifact metadata')
        raw=subprocess.check_output(['gh','api','repos/'+s.REPO+'/actions/artifacts/'+str(row['artifact'])+'/zip'],cwd=s.ROOT)
        proof=audit(read_archive(raw,row),row,report)
        s.need(subprocess.check_output(['git','show',row['commit']+':'+row['report']],cwd=s.ROOT)==(s.ROOT/row['report']).read_bytes(),'saved report changed')
        s.need(s.cmd('git','rev-parse',row['commit']+'^')==row['head'],'record parent mismatch')
        subprocess.run(['git','merge-base','--is-ancestor',row['commit'],head],cwd=s.ROOT,check=True)
        proof['observed_run']={k:run[k] for k in ('id','head_sha','status','conclusion')};audits.append(proof)
    recent=[];cached=[]
    for sha in dict.fromkeys([ROWS[0]['base'],head]+[r[k] for r in ROWS for k in ('head','commit')]):
        runs=s.api('actions/runs?head_sha='+sha+'&per_page=100')
        s.need(runs['total_count']<=100,'Actions pagination needed')
        for run in runs['workflow_runs']:
            recent.append({k:run[k] for k in ('id','name','head_sha','event','status','conclusion')})
            if run['path']=='.github/workflows/modernization-stage79-mgba.yml' and run['status']=='completed' and run['conclusion']=='success':
                jobs=s.api('actions/runs/'+str(run['id'])+'/jobs?per_page=100')
                s.need(jobs['total_count']<=100,'jobs pagination needed')
                for job in jobs['jobs']:
                    if not job['name'].startswith('domain ('):continue
                    step=next(x for x in job['steps'] if x['name']=='domainをmGBAで実行')
                    s.need(step['conclusion']=='skipped','automatic native replay: separate reconciliation required')
                    cached.append({'run_id':run['id'],'job_id':job['id'],'name':job['name'],'native_step_conclusion':step['conclusion']})
    result={'classification':'SAVED_CALLER_CONTROL_EVIDENCE_AND_CI_CLOSEOUT_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'completed_milestones':audits,
        'actions_observed':recent,'cached_stage79_native_steps':cached,
        'session_totals':{'new_implementation_tests':55,'caller_reference_candidates':116,
            'new_sampled_bytes':18308,'saved_bytes_reused':570,'bcd_vectors':2048,
            'tick_and_init_prefix_cases':257,'candidate_reconstructions':1,
            'new_emulator_processes':0,'accepted_native_cases_replayed':0,'rom_changes':0},
        'next_unread_contracts':{'initializer_callers':prior['analysis']['initializer_caller_boundary'],
            'delegates':prior['analysis']['unread_delegates']},
        'old_unread_targets':copy.deepcopy(prior['analysis']['old_unread_targets']),
        'old_frontier_removed':False,'all_runtime_owners_excluded':False,
        'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0,'rom_changes':0,'ring_acquisition_accepted':False,'release_ready':False}
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(result):
    return ('caller採取20tests/run35082799310と制御役割35tests/run35084187651は原Actions成功・artifact・保存commitまで照合済み。'
            '新規18308byte/116参照、保存570byte再利用。BCD2048vector、tick/init257条件を検証。'
            '候補復元計1、native/旧ABI/BP受入再実行0。0x09099E16のtail先は未読0x081C9DF9。Ring実到達は未証明。',
            '保存caller/role/closeoutを再利用し、0x08113984への未検索Thumb短分岐/ARM/間接参照、'
            '0x081C9DF9とI/O wrapper未読5calleeから実callerのpointer/size/LIMIT・selector1/2の通常story実到達を絞る。'
            '同一byteのBCD/selector利用をRTC同時衝突や全owner不存在へ読み替えない。'
            '旧18owner、Ring正規取得・装備実戦・保存、policy/Circus/P08は未完。')


if __name__=='__main__':
    s.need(sys.argv[1:]==['run'],'runだけを許可');s.run(sys.modules[__name__])
