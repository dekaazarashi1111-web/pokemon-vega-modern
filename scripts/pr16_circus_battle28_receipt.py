#!/usr/bin/env python3
"""完了済みnative原本を再実行せず照合し、実結論と画面を固定引継ぎへ同期。"""
from __future__ import annotations
from datetime import datetime, timezone
import io
import os
from pathlib import Path
import subprocess
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_circus_battle28 as run
b=run.b
p=run.p
ROOT=b.ROOT
TASK='USER-20260920-CIRCUS-BATTLE28-RECEIPT'
RUN=35471833294
JOB=105974057584
HEAD='c7218dbf663df9c3b5be868712037e94c76d430d'
ART=10593200557
ARCHIVE=dict(size=1051654,sha256='8bbc05f958bcc47e09d337c6369dedd079bfd125d36d52ba7e2262ca0b21575a')
BASE='184190411de7cb4f098de904d3967e102f6f7d76'
SELF='scripts/pr16_circus_battle28_receipt.py'
WORKFLOW='.github/workflows/pr16-circus-battle28-receipt.yml'
REPORT='content/modernization/pr16_circus_battle28_receipt.json'
b.OUT=ROOT/'.local/pr16-circus-battle28-receipt'
need=b.need
VISUAL=[
    dict(name='circus-continuous-30-save-streak-131-outcome.ppm',identity=dict(size=115215,sha256='f4b25aab8153958bbb87b0aae80bb9cd9615b040cc8c4c45af6e265ee653c2b7'),review_ja='28戦目のoutcome=1に対応。相手表示が消え、こちらの個体はHP87/182で生存。'),
    dict(name='circus-continuous-30-save-streak-133-confirmation.ppm',identity=dict(size=115215,sha256='bf61f8cb99a024da4ebc8abe20ec9c41a0d34131056a67bffafd82b41230f73b'),review_ja='29戦目開始前は同じ選択3個体。通常選択UIで1〜3番目とConfirmを表示。型は対応するparty原本で確認。'),
    dict(name='circus-continuous-30-save-streak-138-saved.ppm',identity=dict(size=115215,sha256='5c36b9a57780673c6acb4ed576062e6e0d88d0c54bab0317128961ef2d1fdb98'),review_ja='通常Save後に受付前のフィールド画面へ復帰。保存成立は併記したcounter/owner原本で判定。'),
    dict(name='circus-continuous-30-save-streak-139-reloaded.ppm',identity=dict(size=115215,sha256='4034ee4630df5a9ddd25c876070ee97d5933f7bd540141101f5e2dd5842bc4b6'),review_ja='fresh coreの通常Continue後、受付前の同位置のフィールド画面。owner64/party600/inventoryは原本でも一致。'),
]


def verify():
    value=b.load(run.REPORT)
    need(value['recording_run']==RUN and value['source_head']==HEAD and value['workflow_source_head']==HEAD,'native report scope')
    need(type(value['lifecycle_verified']) is bool and type(value['genuine_30_wins_verified']) is bool,'acceptance flag types')
    remote,job,artifact=b.api('actions/runs/'+str(RUN)),b.api('actions/jobs/'+str(JOB)),b.api('actions/artifacts/'+str(ART))
    need(remote['status']=='completed' and remote['head_sha']==HEAD and remote['head_branch']==b.BRANCH,'native run scope')
    need(job['run_id']==RUN and job['status']=='completed' and job['conclusion']==remote['conclusion'],'native job scope')
    need(artifact['workflow_run']['id']==RUN and artifact['workflow_run']['head_sha']==HEAD and not artifact['expired']
         and artifact['digest']=='sha256:'+ARCHIVE['sha256'],'artifact scope')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ART)+'/zip'],cwd=ROOT)
    need(b.identity(raw)==ARCHIVE,'original archive identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist();need(len(names)==len(set(names)),'duplicate archive names')
        for name in names:
            path=Path(name)
            need(not path.is_absolute() and '..' not in path.parts and path.suffix in ('.json','.c','.h','.stdout','.stderr','.ppm'),'unexpected artifact member')
        native=b.probe.strict(archive.read('native-result.json'))
        for key,item in native.items():
            if key not in ('recording_source_head','text_evidence'):
                need(key in value and value[key]==item,'native/report differs: '+key)
        for name,bound in value['text_evidence'].items():
            raw=(ROOT/name).read_bytes();need(b.identity(raw)==bound,'tracked execution evidence changed')
            relative=name.split('/'+str(RUN)+'/',1)[1]
            need(archive.read(relative)==raw,'artifact/tracked evidence differs')
        source=(ROOT/(run.OLD_PREFIX+'original-generated/pr16_streak_policy.c')).read_text()
        expected=p.adapt(source,(ROOT/b.HEADER).read_text()).encode()
        need(archive.read('execution/policy.c')==expected,'compiled controller policy source differs')
        stderr=archive.read('execution/'+b.probe.CASE+'.stderr')
        need(p.prefix_proof(run.old_trace(),stderr)==value['prefix28'],'27-win prefix receipt')
        need(p.diagnostic(stderr)==value['partial_diagnostic'],'partial observation differs')
        if value['lifecycle_verified']:
            b.probe.SHA=b.SHA
            result=b.probe.validate(archive.read('execution/'+b.probe.CASE+'.stdout'),stderr,
                                    value['process']['returncode'],b.probe.CASE)
            need(result==value['result'],'lifecycle evidence differs')
        need(value['genuine_30_wins_verified']==(value.get('result',{}).get('wins')==30 and value['lifecycle_verified']),'30-win accounting')
        need(remote['conclusion']==('success' if value['genuine_30_wins_verified'] and not value['failures'] else 'failure'),'conclusion promotion')
        need(VISUAL,'visual review missing')
        for image in VISUAL:
            raw=archive.read('screens/'+image['name'])
            need(raw.startswith(b'P6\n240 160\n255\n') and b.identity(raw)==image['identity'],'reviewed screen differs')
    for name,bound in value['original']['host_dependencies'].items():
        need(b.identity((ROOT/name).read_bytes())==bound,'native host dependency changed')
    need(value['new_emulator_processes']==1 and value['arm_compiles']==value['arm_links']==value['rom_changes']==value['accepted_standalone_replays']==0,'execution counts')
    need(value['host_tests']==dict(tests_run=9,success=True,skipped=0),'nine source contracts')
    return value,dict(run_id=RUN,job_id=JOB,workflow_source_head=HEAD,status=remote['status'],conclusion=remote['conclusion'],
                     artifact_id=ART,archive=ARCHIVE,native_execution_head=value['native_execution_head'])


def main():
    need(ART>0 and BASE and ARCHIVE['size']>0,'unbound original')
    head=b.scope();state=b.resume.validate(ROOT);backlog=b.load(b.resume.BACKLOG)
    need(not (ROOT/REPORT).exists(),'receipt already recorded; do not repeat')
    b.OUT.mkdir(parents=True,exist_ok=True)
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,b.OUT,{SELF,WORKFLOW};guard.guard()
    value,observation=verify()
    old_identity=b.identity((ROOT/run.REPORT).read_bytes())
    value['workflow_observation']=observation
    value['visual_review_completed']=True
    value['visual_review']=VISUAL
    value['completion_receipt']=REPORT
    receipt=dict(schema_version=1,task=TASK,classification='NATIVE_ORIGINAL_RECONCILED_NO_REPLAY',native=observation,
                 report_path=run.REPORT,report_before=old_identity,candidate=value['candidate'],visual_review=VISUAL,
                 new_emulator_processes=0,arm_compiles=0,arm_links=0,accepted_standalone_replays=0,rom_changes=0,
                 genuine_30_wins_verified=value['genuine_30_wins_verified'],lifecycle_verified=value['lifecycle_verified'],
                 physical_admission_accepted=False,suppression_accepted=False,release_ready=False,source_head=head)
    stop,nxt=run.summary(value,'RECEIPT')
    need(value['lifecycle_verified'] and value['result']['wins']==28 and value['result']['losses']==1 and value['result']['events']==139,'observed 28-win receipt')
    nxt='29戦目の先発/通常交代を修復する。初回交代の163→71HPと終盤の相手2HP/こちら4HPを新原本で確認。28勝prefixと受入済みSave/Continueは単独再実行しない。ROM変更/連勝・RNG注入は禁止。'
    receipt['next_loss_diagnostic']=dict(battle=29,first_switch_frame=460169,first_switch_done=461643,target_hp_before=163,target_hp_after=71,last_action_frame=483459,own_hp=4,enemy_hp=2,observed_outcome_frame=483938,next_action_ja=nxt)
    state['next_action']['id']='CIRCUS_BATTLE29_LEAD'
    stop+=' 完了済みActionsの実結論・原artifact・画面・Git原本を新規native0で再照合。'
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['circus_battle28']['receipt']=REPORT
    state['next_action']['read_paths']=[run.REPORT,REPORT,*run.FILES,'content/modernization/pr16_saved_reconstruction.json',b.resume.BACKLOG]
    row=next(x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(row['success_evidence'] is None and not row.get('complete'),'suppression gap must remain open')
    row['battle28_receipt']=REPORT;row['resume']=nxt
    state['pending_runs']=[x for x in state['pending_runs'] if x['run_id']!=RUN]
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='原本照合記録前のremote HEAD。native workflow/native execution HEADと実結論はreceiptで個別固定。'
    state['observed_head_checks']=dict(scope_head=head,runs=[dict(id=RUN,head_sha=HEAD,status='completed',conclusion=observation['conclusion'])],
                                      reason_ja='完了済みCircus原本を直接照合。当記録run全体/全CI greenとは同一視しない。')
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    b.write(run.REPORT,b.stable(value));b.write(REPORT,b.stable(receipt));b.write(b.resume.BACKLOG,b.stable(backlog))
    for name in (run.REPORT,REPORT,SELF,WORKFLOW):state['source_bindings'][name]=b.identity((ROOT/name).read_bytes())
    if b.resume.BACKLOG in state['source_bindings']:state['source_bindings'][b.resume.BACKLOG]=b.identity((ROOT/b.resume.BACKLOG).read_bytes())
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    for label,args in [('resume',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_resume.py','-v']),
                       ('task-graph',[sys.executable,'scripts/validate_task_graph.py'])]:
        out,err,proc=b.capture(args,label);need(b.exited(proc)==0,label+' failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths=[run.REPORT,REPORT,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*b.LOGS]
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
           '- Status: DONE（原本照合と記録。製品全体・特性抑制・P08は未完）\n'
           '- Version: pr16-circus-battle28-receipt-v1\n- Summary: '+stop+'\n'
           '- Files changed: '+', '.join((SELF,WORKFLOW,*paths))+'\n'
           '- Verify: 固定Actions/job/artifact、生成C・tracked原本・27勝130events/byte prefix・通常Save/fresh Continue原本と画面、固定resume tests/task graph、index差分private guard/diff check。新規native0/ARM0/既受入単体再実行0。\n'
           '- Commit: 同branch非force commit。自己SHAはreceipt/remoteを参照。\n'
           '- Network: 完了済みGitHub Actions原本照合のみ。ROM/save/private入力の追加なし。\n'
           '- Next: '+nxt+'\n')
    for name in b.LOGS:
        path=ROOT/name;need(f'— {TASK}\n' not in path.read_text(),'duplicate receipt log')
        with path.open('a') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines())
    need(changed and changed<=set(paths),'unexpected staged paths')
    guard.BASE,guard.ALLOWED=head,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': DONE 28戦目handoff原本と完了Actions・固定引継ぎ・両ログを同期'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    commit=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty after push')
    for name in paths:
        need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed readback differs')
    (b.OUT/'push-receipt.json').write_bytes(b.stable(dict(task=TASK,commit=commit,run_id=int(os.environ['GITHUB_RUN_ID']),non_force_push=True,
                                                         native=observation,source_head=head)))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


if __name__=='__main__':main()
