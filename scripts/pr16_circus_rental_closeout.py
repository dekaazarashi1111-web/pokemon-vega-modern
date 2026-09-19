#!/usr/bin/env python3
"""完了したrental runの原本を再検証し、pendingを解消する。native/ROM再実行なし。"""
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import os
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_loss_followup as ops
import pr16_resume as resume
need, identity, stable=ops.need,ops.identity,ops.stable
SELF='scripts/pr16_circus_rental_closeout.py'
TEST='tests/test_pr16_circus_rental_closeout.py'
WORKFLOW='.github/workflows/pr16-circus-rental-closeout.yml'
SPEC='content/modernization/pr16_circus_rental_closeout_spec.json'
REPORT='content/modernization/pr16_circus_rental_closeout.json'
PREVIOUS='content/modernization/pr16_circus_rental_resume.json'
OUT=ROOT/'.local/pr16-circus-rental-closeout'
FILES=(SELF,TEST,WORKFLOW,SPEC)


def verify_actions(spec, run, job):
    need(run['id']==spec['run_id'] and run['head_sha']==spec['tested_head']
         and run['head_branch']==ops.BRANCH and run['path']=='.github/workflows/pr16-circus-rental-resume.yml'
         and run['event']=='push' and run['run_attempt']==1,'run identity differs')
    need(run['repository']['full_name']==run['head_repository']['full_name']==ops.REPO,'wrong repository')
    need(job['id']==spec['job_id'] and job['run_id']==run['id'] and job['head_sha']==run['head_sha'],'job identity differs')
    for row in (run,job):
        need(row['status']=='completed' and row['conclusion']==spec['conclusion'],'unfinished/different conclusion')
    steps={s['name']:s for s in job['steps']}
    for name in ('成否を区別して固定引継ぎと両ログを非force保存','ROMとsaveを除外して証跡を収録'):
        need(steps[name]['status']=='completed' and steps[name]['conclusion']=='success','record/pack did not succeed')
    return dict(run={k:run[k] for k in ('id','head_sha','status','conclusion','path','event','run_attempt')},
                job={k:job[k] for k in ('id','run_id','head_sha','status','conclusion')})


def verify_evidence(source):
    """tracked textを全hash照合し、成功なら実outcome/owner/Saveを再解析する。"""
    need(source['physical_admission_accepted'] is False and source['suppression_accepted'] is False
         and source['release_ready'] is False,'unproved physical/release promotion')
    need(source['rom_changes']==source['accepted_native_cases_replayed']==0,'unexpected ROM change/native replay')
    # 旧new_arm_links=0は末端payloadだけの値。継承pipeline全体へ外挿しない。
    need(source['new_arm_links']==0,'terminal candidate link count differs')
    for path,bound in source['text_evidence'].items():
        need(identity(resume.safe_path(ROOT,path).read_bytes())==bound,'evidence changed: '+path)
    prefix='evidence/pr16_circus_rental_drought/'+str(source['recording_run'])+'/'
    native=source['native']
    need(native['candidate']==source['candidate'],'native candidate differs')
    result=dict(candidate=source['candidate'],native_report_status=native['status'],
                actual_new_processes=native['actual_new_processes'],
                successful_fresh_cores=native['successful_fresh_cores'],
                native_failures=native['failures'],genuine_30_wins_verified=False,
                inherited_pipeline_accounting=bootstrap_accounting(),
                standard_save_fresh_continue=False,physical_admission_accepted=False,
                suppression_accepted=False,release_ready=False)
    if native['status']=='PASS_CIRCUS_SCOPED_NATIVE':
        import pr16_circus_reentry_probe as probe
        probe.SHA=source['candidate']['sha256']
        base=ROOT/(prefix+'native/'+probe.CASE)
        process=json.loads(base.with_suffix('.process.json').read_bytes())
        need(process['timed_out'] is False and process['spawn_error'] is None,'process did not terminate normally')
        stdout=base.with_suffix('.stdout').read_bytes();stderr=base.with_suffix('.stderr').read_bytes()
        parsed=probe.validate(stdout,stderr,process['returncode'],probe.CASE)
        analyzed=probe.analyze(probe.parse(stderr),parsed)
        need(native['actual_new_processes']==1 and native['successful_fresh_cores']==2,'native process/core count differs')
        need(native['guard_checks']==['bus8','bus16','bus32','raw8','raw16','raw32','register'],'host write rejection set differs')
        result.update(lifecycle=parsed,scoped_result=analyzed,genuine_30_wins_verified=analyzed['genuine_30_wins_verified'],
                      standard_save_fresh_continue=True)
    if 'rental_drought_result' in source:
        result['rental_drought_result']=source['rental_drought_result']
        need(result['genuine_30_wins_verified']==source['rental_drought_result']['genuine_30_wins_verified'],
             'outer/independent native target differs')
        need(result['standard_save_fresh_continue']==source['rental_drought_result']['standard_save_fresh_continue'],
             'outer/independent Save scope differs')
    return result


def bootstrap_accounting():
    """既存shellの到達可能な再compileを記録。実行回数の未採取値を0にしない。"""
    source={
        'scripts/pr16_circus_three_win.py': ['fade.SETUP_WORKFLOW', 'fade.SETUP_STEPS'],
        '.github/workflows/pr16-circus-loss-followup.yml': ['pr16_p07_preserved_layer.py', 'pr16_evolution_learning_repair.py', 'pr16_circus_entry.py', 'pr16_circus_retention.py'],
        'scripts/pr16_circus_entry.py': ['parent.run()', 'compile_adapter('],
        'scripts/pr16_circus_retention.py': ['compile_runtime('],
        'scripts/pr16_ring_policy_successor.py': ['test_pr16_ring_policy_build.py', 'gift.run()', 'compile_runtime('],
    }
    bindings={}
    for path,terms in source.items():
        raw=(ROOT/path).read_bytes();text=raw.decode()
        for term in terms:need(term in text,'bootstrap callsite differs: '+path+' / '+term)
        bindings[path]=identity(raw)
    return dict(scope='runs35457143420/35457636604 inherited preparation shell',
                terminal_drought_payload_links=0, all_ancestor_arm_links_zero=False,
                ancestor_compile_reexecuted=True, exact_ancestor_execution_count=None,
                accepted_ring_host_test_command_reexecuted=True, native_accepted_standalone_replayed=0,
                interpretation_ja='旧new_arm_links/old_arm_links_replayed=0は末端Drought再構築の局所値。継承セットアップは旧親候補を再compileしRing host testsも実行していた。全体0の記述を訂正し、原本は変更しない。実行総数は採取されておらず捏造しない。',
                source_bindings=bindings)


def project(state, backlog, spec, evidence, actions, head):
    from copy import deepcopy
    s,b=deepcopy(state),deepcopy(backlog)
    gap=next(r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(gap['success_evidence'] is None and not gap.get('complete'),'physical gap already closed')
    gap.update(implementation_checkpoint=REPORT,implementation_status=spec['classification'],resume=spec['next_ja'])
    s['bp']['current_stop']=s['source_change_review_ja']=spec['stop_ja']
    s['bp']['next_step']=s['next_action']['goal_ja']=spec['next_ja']
    s['next_action']['id']='CIRCUS_RENTAL_NEXT_UNFINISHED_BOUNDARY'
    s['next_action']['read_paths']=[REPORT,PREVIOUS,'scripts/pr16_circus_rental_resume.py',resume.BACKLOG]
    s['circus_rental_closeout']=dict(path=REPORT,run_id=spec['run_id'],status=spec['classification'])
    s['circus_continuous_followup']=dict(path=REPORT,classification=spec['classification'],target_wins=30)
    resolved={a['id'] for a in actions if a['status']=='completed'}
    s['pending_runs']=[p for p in s['pending_runs'] if p['run_id'] not in resolved]
    need(not s['pending_runs'],'unresolved pending runs must be checked, not erased')
    s['observed_head']=head
    s['observed_date_jst']=datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
    s['observed_head_semantics']='完了済みnative runと原本を照合するcloseout source HEAD。記録専用Actionsはnativeを再実行しない。'
    s['observed_head_checks']=dict(scope_head=head,runs=actions,
        reason_ja='native runの最終結論を照合。action_required等はsuccessに改作しない。記録専用run自身はこのsnapshotに含めず、全CI greenもrelease完了も主張しない。')
    s['prior_actions_reconciled']=actions
    s['inherited_bootstrap_accounting_correction']=dict(path=REPORT,all_ancestor_arm_links_zero=False,
        note_ja='末端Drought再link0を全pipelineへ外挿した旧記述は誤り。旧親compile/Ring host testsの再実行を記録。新native前に保存済みbyte再構築へ切替。')
    s['logs_synchronized']=True
    note=spec['no_repeat_ja']
    if note not in s['do_not_repeat']:s['do_not_repeat'].insert(0,note)
    return s,b


def run():
    import pr16_ring_compiled_record as guard
    head=ops.scope();spec=resume.load(ROOT,SPEC)
    need(ops.command('git','rev-parse','HEAD^')==spec['recorded_head'],'closeout base advanced')
    need(set(ops.command('git','diff','--name-only',spec['recorded_head'],head).splitlines())==set(FILES),'closeout WIP scope')
    need(not (ROOT/REPORT).exists(),'closeout already recorded; do not duplicate')
    state=resume.validate(ROOT);source=resume.load(ROOT,PREVIOUS);backlog=resume.load(ROOT,resume.BACKLOG)
    need(source['recording_run']==spec['run_id'],'not the current native original')
    accepted=identity((ROOT/resume.CHECKPOINT).read_bytes())
    run=ops.api('actions/runs/'+str(spec['run_id']));job=ops.api('actions/jobs/'+str(spec['job_id']))
    metadata=verify_actions(spec,run,job);evidence=verify_evidence(source)
    need(evidence['candidate']==spec['candidate'] and evidence['genuine_30_wins_verified']==spec['genuine_30_wins_verified']
         and evidence['standard_save_fresh_continue']==spec['standard_save_fresh_continue'],'planned closeout differs from raw evidence')
    actions={run['id']:{k:run[k] for k in ('id','head_sha','status','conclusion')}}
    for item in state['pending_runs']:
        r=ops.api('actions/runs/'+str(item['run_id']));actions[r['id']]={k:r[k] for k in ('id','head_sha','status','conclusion')}
    for sha in (spec['tested_head'],spec['recorded_head']):
        runs=ops.api('actions/runs?head_sha='+sha+'&per_page=100')
        need(runs['total_count']<=100,'Actions pagination needed')
        for r in runs['workflow_runs']:actions[r['id']]={k:r[k] for k in ('id','head_sha','status','conclusion')}
    actions=list(actions.values());s,b=project(state,backlog,spec,evidence,actions,head)
    OUT.mkdir(parents=True,exist_ok=True)
    ops.OUT=OUT
    results=ops.tests([Path(TEST).name])
    value=dict(schema_version=1,classification=spec['classification'],source_head=head,
               verified_actions=metadata,observed_runs=actions,evidence=evidence,host_tests=results,
               native_processes_reexecuted=0,new_arm_links=0,rom_changes=0,
               execution_count_scope='この記録専用closeout runのみ。参照runの旧親再compileはevidence.inherited_pipeline_accountingを参照。',
               accepted_native_cases_replayed=0,formal_bp_checkpoint_unchanged=True,
               physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
               next_action_ja=spec['next_ja'])
    (ROOT/REPORT).write_bytes(stable(value));(ROOT/resume.BACKLOG).write_bytes(stable(b))
    for name in (*FILES,REPORT,*evidence['inherited_pipeline_accounting']['source_bindings']):s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    (ROOT/resume.STATE).write_bytes(stable(s));(ROOT/resume.DOC).write_text(resume.render(s))
    resume.validate(ROOT);checks=ops.tests(['test_pr16_resume.py'])
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    outputs=[REPORT,resume.STATE,resume.DOC,resume.BACKLOG,'design/run_log.md','design/version_log.md']
    stamp=datetime.now(timezone.utc).isoformat();tag='USER-20260920-CIRCUS-RENTAL-CLOSEOUT-RUN'+os.environ['GITHUB_RUN_ID']
    entry=('\n\n## '+stamp+' — '+tag+'\n- Timestamp: '+stamp+'\n- Task: '+tag+'\n- Status: DONE / 記録区切り。physical/P08/release未完。'
           '\n- Version: pr16-circus-rental-closeout\n- Summary: '+spec['stop_ja']+
           '\n- Files changed: '+', '.join([*FILES,*outputs])+'\n- Verify: '+str(results+checks)+
           '; 原本全hash・Actions最終結論・実勝敗/owner/Saveを照合。task graph、差分private guard新規違反0、diff checkをcommit前必須。'
           '\n- Evidence: '+REPORT+' / run'+str(spec['run_id'])+' / job'+str(spec['job_id'])+
           '\n- Commit: この記録を含む同branch非force commit。自己SHAはremote ref/receipt。'
           '\n- Network: GitHub/Actionsのみ。このcloseout自体は新規native0/ARM link0/ROM変更0。参照runの末端Drought再link0を総数0とした旧記録は訂正する。継承pipelineの旧親再compile/Ring host tests再実行あり、総実行回数未採取。原本は保持。旧failure/全体guard違反を成功に改作しない。'
           '\n- Next: '+spec['next_ja']+'\n')
    for name in ('design/run_log.md','design/version_log.md'):
        need(tag not in (ROOT/name).read_text(),'duplicate closeout log')
        with (ROOT/name).open('a') as f:f.write(entry)
    subprocess.run(['git','add','--',*outputs],cwd=ROOT,check=True)
    changed=set(ops.command('git','diff','--cached','--name-only',head).splitlines())
    need(changed==set(outputs),'closeout changed path boundary')
    guard.BASE=head;guard.OUT=OUT;guard.ALLOWED=changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);ops.scope()
    need(identity((ROOT/resume.CHECKPOINT).read_bytes())==accepted,'formal BP checkpoint changed')
    for k,v in [('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')]:
        subprocess.run(['git','config',k,v],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',tag+': 完了runを照合し固定引継ぎ・両ログを同期'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True)
    final=ops.scope()
    for name in outputs:need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed readback differs')
    need(not ops.command('git','status','--porcelain','--untracked-files=no'),'post-push source dirty')
    (OUT/'receipt.json').write_bytes(stable(dict(commit=final,source_head=head,tests=results+checks,
                                               run_id=int(os.environ['GITHUB_RUN_ID']),native_reexecuted=0)))
    print('RESULT=DONE VERIFY=PASS COMMIT='+final)

if __name__=='__main__':run()
