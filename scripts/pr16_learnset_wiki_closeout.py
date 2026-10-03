#!/usr/bin/env python3
"""後継Wikiの完了Actionsと保存原本だけを照合。生成/ROM/native/受入36試験は呼ばない。"""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_wiki_actions as m
TASK='USER-20260923-LEARNSET-WIKI'
REPORT=m.BASE+'pr16_learnset_wiki_completed_actions.json'
WORK=ROOT/'.local/pr16-learnset-wiki-closeout'
CODE={'scripts/pr16_learnset_wiki_closeout.py','tests/test_pr16_learnset_wiki_closeout.py',
      '.github/workflows/pr16-learnset-wiki-closeout.yml'}
OWNED={REPORT,m.CP,m.GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}
need=m.need


def validate_completion(cp,run,jobs,artifact):
    need(run['id']==cp['run_id'] and run['head_sha']==cp['source_head']
         and run['head_branch']==m.BRANCH and run['repository']['full_name']=='dekaazarashi1111-web/pokemon-vega-modern','run identity')
    need(run['status']=='completed' and run['conclusion']=='success' and run['event']=='push'
         and run['path']=='.github/workflows/pr16-learnset-wiki-publish.yml','completed successful workflow')
    need(jobs['total_count']==len(jobs['jobs'])==1,'complete job listing')
    job=jobs['jobs'][0]
    need(job['run_id']==cp['run_id'] and job['head_sha']==cp['source_head'] and job['name']=='wiki-publish'
         and job['status']=='completed' and job['conclusion']=='success','completed successful job')
    optional='失敗時だけ公開処理のdiagnosticを保存'
    need(sum(s['name']==optional for s in job['steps'])==1,'optional diagnostic step identity')
    need(job['steps'] and all(s['status']=='completed' and s['conclusion']==('skipped' if s['name']==optional else 'success') for s in job['steps'])
         and any('非force commit/push' in s['name'] for s in job['steps'])
         and sum(s['name']=='Run actions/upload-artifact@v4' for s in job['steps'])==2,'required steps/push/uploads completed')
    need(artifact['name']=='pr16-learnset-wiki-proof' and artifact['expired'] is False
         and artifact['workflow_run']['id']==cp['run_id'] and artifact['workflow_run']['head_sha']==cp['source_head']
         and artifact['workflow_run']['head_branch']==m.BRANCH
         and re.fullmatch('sha256:[0-9a-f]{64}',artifact['digest']) is not None,'proof artifact binding')
    return {k:run[k] for k in ('id','head_sha','head_branch','path','event','status','conclusion','created_at','updated_at')} | {
        'jobs':[{k:job[k] for k in ('id','name','status','conclusion','steps')}]}


def record():
    head=m.current();cp=m.load(ROOT/m.CP)
    need(cp['status']=='PASS_SUCCESSOR_LEARNSET_WIKI' and cp['candidate']==m.CANDIDATE
         and cp['actions_completion_confirmed'] is False and not (ROOT/REPORT).exists(),'fresh completed-Wiki reconciliation')
    need(cp['focused_tests']==36 and cp['generator_tests']==28 and cp['registry_tests']==8
         and cp['counts']['routes']==128389 and cp['files']==4932,'accepted Wiki scope/count')
    run=m.fetch('actions/runs/'+str(cp['run_id']))
    jobs=m.fetch('actions/runs/'+str(cp['run_id'])+'/jobs?per_page=100')
    listing=m.fetch('actions/runs/'+str(cp['run_id'])+'/artifacts?per_page=100')
    need(listing['total_count']==len(listing['artifacts'])==2,'artifact listing completeness')
    artifacts={a['name']:a for a in listing['artifacts']}
    need(set(artifacts)=={'pr16-learnset-wiki-proof','pr16-learnset-wiki-tree'},'proof/tree artifact identity')
    artifact=artifacts['pr16-learnset-wiki-proof'];done=validate_completion(cp,run,jobs,artifact)
    tree=artifacts['pr16-learnset-wiki-tree']
    need(tree['expired'] is False and tree['workflow_run']['id']==cp['run_id']
         and tree['workflow_run']['head_sha']==cp['source_head'] and tree['workflow_run']['head_branch']==m.BRANCH
         and re.fullmatch('sha256:[0-9a-f]{64}',tree['digest']) is not None,'saved Wiki tree metadata')
    need(cp['focused_tests_executed']==0 and cp['new_publish_tests']==10 and cp['output_materializations']==1
         and cp['verification_run_id']==35756623313 and cp['verification_source_head']=='b8f8585da8c34652dd4fc59fec537f4c2e04df1c'
         and cp['inherited_completed_steps']['run_conclusion']=='failure'
         and cp['inherited_completed_steps']['verification_step_conclusion']=='success','publication vs inherited verification boundary')
    raw=m.fetch('actions/artifacts/'+str(artifact['id'])+'/zip',binary=True)
    need(m.w.identity(raw)=={'size':artifact['size_in_bytes'],'sha256':artifact['digest'][7:]},'outer proof digest')
    files={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist())==len(set(z.namelist())) and set(z.namelist())==set(cp['proof_bindings'])|{'result.txt'},'proof exact file set')
        for info in z.infolist():
            need(Path(info.filename).name==info.filename and not info.is_dir()
                 and info.external_attr>>28!=0xA and info.file_size<500000,'proof path/kind/size')
            data=z.read(info);data.decode('utf-8');need(b'\0' not in data,'proof text only');files[info.filename]=data
    for name,binding in cp['proof_bindings'].items():
        need(m.w.identity(files[name])==binding and (ROOT/m.EVIDENCE/name).read_bytes()==files[name],'immutable recorded proof: '+name)
    v=json.loads(files['verification.json'])
    need(all(cp[k]==value for k,value in v.items()),'checkpoint differs from raw verification')
    for key in ('accepted_tests_rerun','source_regenerations','new_native_runs','new_arm_compiles','rom_changes'):
        need(type(v[key]) is int and v[key]==0,'accepted scope rerun: '+key)
    for key in ('physical_supply_verified','gameplay_e2e_accepted','issue19_complete','active_baseline_changed','release_ready'):
        need(v[key] is False,'unaccepted scope promoted: '+key)
    match=re.fullmatch(r'RESULT=DONE TASK=USER-20260923-LEARNSET-WIKI VERIFY=PASS COMMIT=([0-9a-f]{40}) SCOPE=LEARNSET_WIKI_NOT_GAMEPLAY\n',files['result.txt'].decode())
    need(match is not None,'pushed result marker');child=match.group(1)
    commit=m.fetch('git/commits/'+child)
    need([p['sha'] for p in commit['parents']]==[cp['source_head']] and commit['message'].startswith(TASK+':'),'nonforce Wiki commit ancestry')
    subprocess.run(['git','merge-base','--is-ancestor',child,'HEAD'],cwd=ROOT,check=True)
    changed=set(m.git('diff','--name-only','-z',child,'HEAD').decode().strip('\0').split('\0'))
    need(changed==CODE,'record-only descendant scope')
    for bindings in (v['restoration']['source_bindings'],v['materialization_restoration']['source_bindings'],v['publisher_bindings']):
        for path,binding in bindings.items():
            need(m.w.identity((ROOT/path).read_bytes())==binding,'accepted source changed: '+path)
    for path,binding in v['protected_bindings'].items():
        need(m.w.identity((ROOT/path).read_bytes())==binding,'protected acceptance changed: '+path)
    unit=(WORK/'unit.txt').read_text()
    need(re.findall(r'Ran (\d+) tests?',unit)==['14'] and unit.rstrip().endswith('OK'),'new closeout 14 tests')
    source_runs=m.fetch('actions/runs?head_sha='+cp['source_head']+'&per_page=100')
    need(source_runs['total_count']==len(source_runs['workflow_runs']),'source checks pagination')
    observed=[{k:r[k] for k in ('id','head_sha','path','event','status','conclusion')} for r in source_runs['workflow_runs']]
    report={'status':'COMPLETED_WIKI_ACTIONS_AND_IMMUTABLE_PROOF_RECONCILED','source_head':cp['source_head'],
        'record_source_head':head,'record_commit':child,'candidate':m.CANDIDATE,'completed_actions':done,
        'artifact':{k:artifact[k] for k in ('id','name','size_in_bytes','digest')},
        'saved_tree_artifact':{k:tree[k] for k in ('id','name','size_in_bytes','digest')},
        'saved_tree_metadata_only':True,'saved_tree_content_binding':cp['tree_materialization_archive'],
        'verification_source_head':cp['verification_source_head'],'verification_run_id':cp['verification_run_id'],
        'proof_bindings':{n:m.w.identity(data) for n,data in files.items()},'observed_source_checks':observed,
        'new_closeout_tests':14,'closeout_unit':dict(m.w.identity(unit.encode()),text=unit),
        'inherited_wiki_tests':36,'inherited_publish_tests':10,'accepted_tests_rerun':0,'new_native_runs':0,
        'new_wiki_generations':0,'new_rom_materializations':0,'new_arm_compiles':0,
        'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,
        'active_baseline_changed':False,'release_ready':False,'closeout_run_id':int(os.environ['GITHUB_RUN_ID'])}
    m.write(ROOT/REPORT,report)
    cp.update(actions_completion_confirmed=True,actions_completion='完了run/job/必須step（失敗時専用stepはskipped）と原本artifact・非force反映commitを照合済み',
              completed_actions=done,record_commit=child,completion_reconciliation=REPORT,
              completion_record_source_head=head,proof_artifact=report['artifact'],tree_artifact=report['saved_tree_artifact'])
    m.write(ROOT/m.CP,cp)
    guide=ROOT/m.GUIDE
    with guide.open('a',encoding='utf-8') as f:
        f.write(f'\n## 完了Actions照合\n\nrun{cp["run_id"]} / source `{cp["source_head"]}` / 反映 `{child}` のrun・job・必須step成功（失敗時専用stepはskipped）、保存証拠hash、親子commitを照合。正本 `{REPORT}`。当回は新しい記録境界14試験だけで、受入済みWiki36試験/独立生成/ROM復元/nativeの再実行は0。\n')
    state=m.load(ROOT/m.STATE)
    state['learnset_candidate_wiki'].update(actions_completion_confirmed=True,record_commit=child,completion_reconciliation=REPORT)
    state['observed_head']=cp['source_head']
    state['observed_head_semantics']='後継技習得Wikiの反映source HEAD。生成・36試験は別source b8f8585d/run35756623313の成功stepを継承。反映Actions原本とcommitの照合済み。通常操作の受入ではない。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':observed,
        'reason_ja':'Wiki runの完了成功・原本証拠・非force反映commitを照合。各CIはsource HEADを明記し、後続記録HEADへ成功を流用しない。'}
    for path in CODE|{REPORT,m.CP,m.GUIDE}:
        state['source_bindings'][path]=m.w.identity((ROOT/path).read_bytes())
    state['do_not_repeat'].append('後継Wikiの完了Actions照合は '+REPORT+' に保存。36 Wiki試験/2生成/候補復元は当回再実行0。次は未受入の通常操作だけを対象にする。')
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 完了Actions原本の照合\n- Version: issue19-wiki-6e88a021-closeout-v1\n- Status: DONE（技習得Wiki記録限定）\n- Summary: run{cp["run_id"]}のrun/job/必須step成功（失敗時専用stepはskipped）、artifact外側digestと全member、反映commit {child}、受入source不変を照合。Wiki4932files/128389経路/36試験の受入は継承。\n- Files changed: closeout script/14試験/workflow、完了照合JSON、Wiki checkpoint/引継ぎMD/JSON/説明MD、両ログ。\n- Verify: 新しい記録境界14試験、resume/task graph/限定index guard。Wiki生成・旧36試験・原本採取・ROM復元・ARM・nativeの再実行0。\n- Commit: 同branch非forceの本記録commit。自己SHAはgit log/Actions resultと照合。\n- Network: 固定run/artifact/commit/source Checksと現在refのみ。全履歴guard PASS、製品受入、merge/release/baseline切替を主張しない。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a',encoding='utf-8') as f:f.write(log)
    print(json.dumps({'status':report['status'],'wiki_commit':child,'wiki_run':cp['run_id'],'accepted_tests_rerun':0}))


def guard():
    import pr16_learnset_runtime_record as g
    cp=m.load(ROOT/m.CP)
    g.START,g.CODE,g.OWNED=cp['record_commit'],CODE,OWNED
    g.guard();subprocess.run(['git','diff','--cached','--check',cp['record_commit']],cwd=ROOT,check=True)


if __name__=='__main__':
    try:
        need(len(sys.argv)==2,'usage record|guard|paths')
        {'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(CODE|OWNED)))}[sys.argv[1]]()
    except Exception as exc:
        WORK.mkdir(parents=True,exist_ok=True)
        m.write(WORK/'failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
              'run_id':os.environ.get('GITHUB_RUN_ID'),'error':str(exc).replace(str(ROOT),'$REPO')})
        raise
