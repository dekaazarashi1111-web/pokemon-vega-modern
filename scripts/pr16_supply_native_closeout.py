#!/usr/bin/env python3
"""完了済Actions/保存証拠を照合するだけ。ROM生成・compile・nativeを呼ばない。"""
from __future__ import annotations
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
START='b464a4df505d26067c42550db90615eeb3655cdd'
TESTED='740ecf0a94de514fa735e4697f5d6129d45520e4'
RUN=35748601580
JOB=106816516184
TASK='USER-20260922-LEARNSET-SUPPLY-NATIVE'
BASE='content/modernization/'
CP=BASE+'pr16_learnset_supply_native_checkpoint.json'
ALIGN=BASE+'pr16_learnset_supply_alignment_checkpoint.json'
EVIDENCE=BASE+'pr16_learnset_supply_native_evidence'
REPORT=BASE+'pr16_learnset_supply_completed_actions.json'
STATE=BASE+'pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE='docs/PR16_LEARNSET_SUPPLY_JA.md'
WORK=ROOT/'.local/pr16-supply-native-closeout'
CODE={'scripts/pr16_supply_native_closeout.py','tests/test_pr16_supply_native_closeout.py',
      '.github/workflows/pr16-supply-native-closeout.yml'}
OWNED={REPORT,CP,ALIGN,STATE,DOC,GUIDE,'design/run_log.md','design/version_log.md'}
CANDIDATE={'size':33554432,'sha256':'6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2'}
PROOF={'id':10704202526,'name':'pr16-learnset-supply-rom-proof','size_in_bytes':89356,
       'digest':'sha256:199ed431af286ceb2881e9a1cb79174983652e531df568333468369e7f1af5d4'}
DATA={'id':10704282359,'name':'pr16-learnset-supply-aligned-data','size_in_bytes':50476,
      'digest':'sha256:a1130da2f577f4cd7f6a00e60ba67ae7658a8b6265bc3401a979c8758562ffc6'}
COMPILE_FAILURE={'id':10703297226,'name':'pr16-learnset-supply-rom-proof','size_in_bytes':78066,
                 'digest':'sha256:47f62a2f1591d5f59e7fbdd06e99c5f262dfd8a22322454c61b2961b44359027'}
RESULT=f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={START} SCOPE=DIRECT_ROM_NOT_GAMEPLAY\n'


def need(value,message):
    if not value:raise ValueError(message)


def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')


def validate_verification(v):
    need(v['source_head']==TESTED and type(v['run_id']) is int and v['run_id']==RUN,'native source/run')
    need(v['status']=='PASS_NEW_SUPPLY_FOUR_HOOKS' and v['scope']=='HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E','native scope')
    need(v['candidate']==CANDIDATE and v['candidate_crc32']=='00F31AF7','candidate identity')
    for key in ('physical_supply_verified','gameplay_e2e_accepted','issue19_complete','release_ready','active_baseline_changed'):
        need(v[key] is False,'scope escalation '+key)
    for key in ('accepted_native_reruns','accepted_tests_rerun','accepted_payload_regenerations',
                'accepted_source_regenerations','new_arm_compiles','new_arm_links','new_tests','placement_reproductions'):
        need(type(v[key]) is int and v[key]==0,'nonzero replay '+key)
    for key,count in (('samples',28),('native_processes',2),('inherited_tests',40),('new_original_span_fixtures',2)):
        need(type(v[key]) is int and v[key]==count,'verification count '+key)
    need(v['independent_process_results_equal'] is True and v['tested_candidate_unchanged'] is True,'native equality')
    results=v['native_results']
    need(len(results)==2 and results[0]==results[1],'two native results')
    r=results[0]
    need(r['scope']==v['scope'] and r['status']==v['status'] and r['candidate_sha256']==CANDIDATE['sha256'],'native result identity')
    for key,count in (('samples',28),('calls',10696),('readonly_checks',9512),('ordinary_allowed',10),
                      ('ordinary_denied',3574),('special_allowed',6),('special_denied',1002),
                      ('archive_pages',364),('archive_denied',392),('selection_checks',84),('real_flag_checks',56),
                      ('raw_boundary_filtered_samples',3),('page_four_nonempty',2)):
        need(type(r[key]) is int and r[key]==count,'native counter '+key)
    need(r['hook_calls']==[6972,812,196,812],'hook calls')
    for key in ('stored_four_moves_and_pp_preserved','buffer_canaries_preserved','new_code_pc_seen_for_every_hook_call'):
        need(r[key] is True,'native invariant '+key)
    need(r['physical_supply_verified'] is False and r['gameplay_e2e_accepted'] is False,'native scope escalation')
    p=v['placement_repair']
    need(p['prefix_bytes']==4 and p['origin']==0x09fff044 and p['load_address']==0x09fff048
         and p['placed_image']['size']==2788 and p['outside_repair_span_changes']==0 and p['hook_bytes_changed']==0,'placement boundary')


def validate_run(run,jobs):
    need(run['id']==RUN and run['head_sha']==TESTED and run['head_branch']=='codex/modernization-followup-20260908'
         and run['path']=='.github/workflows/pr16-learnset-supply-rom.yml'
         and run['status']=='completed' and run['conclusion']=='success','native completed run')
    need(len(jobs)==1 and jobs[0]['id']==JOB and jobs[0]['name']=='supply-rom'
         and jobs[0]['status']=='completed' and jobs[0]['conclusion']=='success','native completed job')
    steps=jobs[0]['steps']
    need(len(steps)>=9 and all(s['status']=='completed' and s['conclusion']=='success' for s in steps),'native completed steps')
    need(any(s['name']=='同branchへ非force commit/pushし最新refを照合' for s in steps),'native push step')


def bundle(artifact,head,run_id,text=False):
    from pr16_wiki_reconcile import fetch
    meta=fetch('actions/artifacts/'+str(artifact['id']))
    need(all(meta[k]==v for k,v in artifact.items()) and not meta['expired']
         and meta['workflow_run']['head_sha']==head and meta['workflow_run']['id']==run_id,'artifact metadata')
    raw=fetch('actions/artifacts/'+str(artifact['id'])+'/zip',binary=True)
    need(identity(raw)=={'size':artifact['size_in_bytes'],'sha256':artifact['digest'][7:]},'artifact ZIP identity')
    result={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        need(len(names)==len(set(names)) and len(names)<=128 and sum(i.file_size for i in z.infolist())<4000000,'artifact ZIP limits')
        for info in z.infolist():
            name=info.filename
            need(name not in ('.','..') and Path(name).name==name and '\\' not in name and not info.is_dir()
                 and (info.external_attr>>16)&0o170000!=0o120000 and info.file_size<1000000,'artifact ZIP path')
            content=z.read(name)
            if text:content.decode('utf-8');need(b'\0' not in content,'artifact text')
            result[name]=content
    return result


def record():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_payload_verify import current_pr
    from pr16_learnset_compact_record import publish_resume
    current_pr(os.environ['GITHUB_SHA'])
    need(not (ROOT/REPORT).exists(),'closeout already recorded')
    cp,alignment=load(ROOT/CP),load(ROOT/ALIGN)
    v=cp['verification'];validate_verification(v)
    for name,binding in v['source_bindings'].items():need(identity((ROOT/name).read_bytes())==binding,'changed native source '+name)
    run=fetch('actions/runs/'+str(RUN));payload=fetch('actions/runs/'+str(RUN)+'/jobs')
    jobs=payload['jobs'];need(payload['total_count']==len(jobs),'job pagination')
    validate_run(run,jobs)
    proof=bundle(PROOF,TESTED,RUN,text=True)
    need(set(proof)==set(cp['proof_bindings'])|{'result.txt'} and proof['result.txt'].decode()==RESULT,'proof/result set')
    for name,binding in cp['proof_bindings'].items():
        need(identity(proof[name])==binding and proof[name]==(ROOT/EVIDENCE/name).read_bytes(),'committed proof '+name)
    need(json.loads(proof['verification.json'])==v,'original verification projection')
    for seed,result in zip((11,29),v['native_results']):
        need(json.loads(proof[f'native{seed}.json'])==json.loads(proof[f'native{seed}.stdout.txt'])==result,'native original JSON')
        need(b'log_problem_count=0\n' in proof[f'native{seed}.stderr.txt'],'native logger errors')
    data=bundle(DATA,TESTED,RUN)
    need({n:identity(raw) for n,raw in data.items()}==v['data_files']==alignment['data_files'],'aligned artifact members')
    need(json.loads(data['link.json'])==alignment['link'] and alignment['candidate']==CANDIDATE,'aligned link')
    commit=fetch('git/commits/'+START)
    need([p['sha'] for p in commit['parents']]==[TESTED],'native record ancestry')
    failed=bundle(COMPILE_FAILURE,'da2485291a3d16991405e3e68faa6a6f625383e6',35747886574,text=True)
    failure=json.loads(failed['failure.json'])
    need(failure['run_id']=='35747886574' and 'command failed native-compile:' in failure['error']
         and 'native11.stdout.txt' not in failed,'compile failure boundary')
    compact={k:run[k] for k in ('id','head_sha','head_branch','path','event','status','conclusion','created_at','updated_at')}
    compact['jobs']=[{**{k:j[k] for k in ('id','name','status','conclusion')},
                      'steps':[{k:s[k] for k in ('name','status','conclusion')} for s in j['steps']]} for j in jobs]
    observed=fetch('actions/runs?head_sha='+TESTED+'&per_page=100')
    need(observed['total_count']==len(observed['workflow_runs']),'checks pagination')
    checks=[{k:r[k] for k in ('id','head_sha','path','event','status','conclusion')} for r in observed['workflow_runs']]
    report={'status':'COMPLETED_ACTIONS_AND_IMMUTABLE_EVIDENCE_RECONCILED','candidate':CANDIDATE,
            'candidate_crc32':'00F31AF7','completed_actions':compact,'record_commit':START,
            'native_proof_artifact':PROOF,'aligned_data_artifact':DATA,'observed_source_checks':checks,
            'source_head':os.environ['GITHUB_SHA'],'closeout_run_id':int(os.environ['GITHUB_RUN_ID']),
            'new_closeout_tests':12,'new_native_processes':0,'accepted_tests_rerun':0,'new_rom_materializations':0,
            'host_compile_failure':{'artifact':COMPILE_FAILURE,'raw_failure':failure,
                                    'raw_failure_binding':identity(failed['failure.json']),
                                    'stderr':failed['native-compile.stderr.txt'].decode(),
                                    'native_started':False,'fixed_in':TESTED},
            'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,
            'release_ready':False,'active_baseline_changed':False}
    write(ROOT/REPORT,report)
    for path,obj in ((CP,cp),(ALIGN,alignment)):
        obj.update(actions_completion_confirmed=True,completed_actions=compact,completion_reconciliation=REPORT,
                   record_commit=START,artifacts={'proof':PROOF,'aligned_data':DATA})
        if path==CP:obj['actions_completion']='COMPLETED_SUCCESS_WITH_RECORD_PUSH_AND_ARTIFACTS'
        write(ROOT/path,obj)
    state=load(ROOT/STATE)
    state['observed_head']=TESTED
    state['observed_head_semantics']='新供給4hook診断成功の入力HEAD。保存ELF配置修復はrun35747048291、28owner×2processはrun35748601580、記録commitは'+START+'。正式BP欄の候補/受入履歴は不変。'
    state['observed_head_checks']={'source_head':TESTED,'runs':checks,
        'reason_ja':'供給native run35748601580/job106816516184は検証・限定guard・同branch非force push・artifact公開までcompleted/success。完了抄録は'+REPORT+'。source checksの実測結果のみ保存し、全履歴guard/release/通常操作の完了とは扱わない。'}
    for name in ('learnset_supply_native','learnset_supply_alignment'):
        state[name].update(actions_completion_confirmed=True,completion_reconciliation=REPORT,record_commit=START)
    state['learnset_supply_alignment']['aligned_data_artifact']=DATA
    state['bp']['current_stop']+=' 完了Actions/原本artifact/記録commitの対応を追加照合済み。'
    state['next_action']['read_paths']=[GUIDE,REPORT,ALIGN,CP,'scripts/pr16_supply_elf_placement.py','scripts/pr16_supply_coverage_followup.py']
    need(all((ROOT/p).is_file() for p in state['next_action']['read_paths']),'resume navigation')
    state['do_not_repeat'].append('供給native完了照合: run35748601580は28owner/21392call/2process成功。配置16試験はrun35747048291、旧入力24試験も保存原本継承で再実行0。run35747886574はhost compile失敗のみ・native未起動。closeoutは新12件の証拠拒否試験だけでROM生成/native/既受入試験0。')
    state['logs_synchronized']=True
    publish_resume(state)
    with (ROOT/GUIDE).open('a',encoding='utf-8') as stream:
        stream.write('\n## 完了Actionsの固定照合\n\nrun35748601580/job106816516184はcompleted/success。記録commit `'+START+'`、照合正本 `'+REPORT+'`。保存aligned-data artifact10704282359を次工程で利用し、native2process/21392callを再実行しない。配置16試験はrun35747048291を継承。通常操作・新候補Wiki・物理供給の未完は変わらない。\n')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / completed Actionsと原本・再開HEADの照合\n- Version: learnset-supply-native-closeout-v1\n- Status: DONE（配置修復・4hook直接ROM診断・完了記録まで。Wiki/実操作は未完）\n- Summary: run{RUN}/job{JOB} completed/success、28owner×独立2process、21392call、通常Tutor許可/拒否20/7148、特殊Tutor許可/拒否12/2004、readonly19024回。原本JSON/ログ・全member hash・保存aligned-data・非force記録commit {START} を照合。古いobserved_head表記をnative実入力へ同期。\n- Files changed: 完了照合器/12証拠拒否試験/限定workflow、completed-actions JSON、配置/native checkpoint、固定MD/JSON、guide、両ログ。\n- Verify: 新closeout12試験・resume check・task graph・限定final index/private差分guardを通過してからcommit。native/ARM compile/link/ROM復元/既受入試験は今回0。配置16試験はrun35747048291、旧24試験も保存継承。host compile失敗run35747886574（native0）は原本付きで保存し、740ecf0でラッパーだけ修復した。26owner診断失敗1processと28owner成功2processを混同しない。\n- Commit: 本記録を含む同branch非force commit。検証入力HEAD='+os.environ['GITHUB_SHA']+'。自己SHAはgit logで照合。\n- Network: GitHub固定run/artifact照合のみ。ROM/Save/ELF/binaryをtrackedへ追加しない。正式BP/P08/旧Wiki/基準ROMは不変、merge/release/active baseline切替なし。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write(log)
    print(json.dumps({'status':report['status'],'native_run':RUN,'record_commit':START,'new_native_processes':0}))


def guard():
    import pr16_learnset_runtime_record as g
    g.START,g.CODE,g.OWNED=START,CODE,OWNED;g.guard()
    subprocess.run(['git','diff','--cached','--check',START],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(OWNED)))}
    if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('usage: supply_native_closeout.py record|guard|paths')
    actions[sys.argv[1]]()
