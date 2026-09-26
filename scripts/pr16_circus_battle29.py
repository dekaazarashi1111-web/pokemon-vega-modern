#!/usr/bin/env python3
"""前runの28勝prefixを再利用し、29戦目以降の未完nativeを1回だけ進める。"""
from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_circus_battle25 as b
import pr16_circus_battle29_policy as p
TASK='USER-20260920-CIRCUS-BATTLE29'
REPORT='content/modernization/pr16_circus_battle29.json'
OLD_REPORT='content/modernization/pr16_circus_battle28.json'
OLD_PREFIX='evidence/pr16_circus_battle28/35471833294/'
FILES=('scripts/pr16_circus_battle29.py','scripts/pr16_circus_battle29_policy.py',
       'tests/test_pr16_circus_battle29.py','.github/workflows/pr16-circus-battle29.yml')
RUN=35471833294
ART=10593200557
WORKFLOW_HEAD='c7218dbf663df9c3b5be868712037e94c76d430d'
ARCHIVE=dict(size=1051654,sha256='8bbc05f958bcc47e09d337c6369dedd079bfd125d36d52ba7e2262ca0b21575a')
ROOT=b.ROOT
b.REPORT=REPORT
b.TASK=TASK
b.policy=SimpleNamespace(adapt=p.adapt,prefix_proof=p.parent.previous.prefix_proof)
need=b.need


def old_trace():return (ROOT/(OLD_PREFIX+'execution/'+b.probe.CASE+'.stderr')).read_bytes()


def previous_attempt():
    old=b.load(OLD_REPORT)
    receipt=b.load('content/modernization/pr16_circus_battle28_receipt.json')
    need(old['recording_run']==RUN and old['new_emulator_processes']==1 and old['lifecycle_verified']
         and old['candidate']==b.TARGET and not old['failures'] and old['visual_review_completed']
         and old['result']['wins']==28 and old['result']['losses']==1,'previous scoped 28-win acceptance')
    need(receipt['native']['run_id']==RUN and receipt['lifecycle_verified'] and not receipt['genuine_30_wins_verified'],
         'completed original receipt absent')
    run,job,artifact=b.api('actions/runs/'+str(RUN)),b.api('actions/jobs/105974057584'),b.api('actions/artifacts/'+str(ART))
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==WORKFLOW_HEAD,'previous run scope')
    need(job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='failure','previous job scope')
    need(artifact['workflow_run']['id']==RUN and artifact['digest']=='sha256:'+ARCHIVE['sha256'],'previous artifact scope')
    return dict(run_id=RUN,job_id=job['id'],artifact_id=ART,archive=ARCHIVE,workflow_source_head=WORKFLOW_HEAD,
                report_path=OLD_REPORT,report_identity=b.identity((ROOT/OLD_REPORT).read_bytes()),
                original_conclusion='failure',diagnostic=p.original(old_trace()),
                scoped_28_win_save_continue_accepted=True,
                reason_ja='通常先発維持の変更は29戦目の最初のactionから。28勝・29戦目actionの134eventsは継続prefixとして完全保持。')


def summary(value,phase):
    if value.get('genuine_30_wins_verified'):
        return ('同一2b107e7eで真正30勝90BP・元party600/owner64・通常Save/fresh Continueを検証。'
                '受入28勝と29戦目actionまで134events/最初の変更前byte列は完全一致。ROM変更/ARM0。',
                'このrunの原本・終端画面を照合して正規実受付から特性抑制へ進む。30勝単独再実行は禁止。P08移送・releaseは未完。')
    if value.get('lifecycle_verified'):
        r=value['result']
        return (f"先発維持修正後、実{r['wins']}勝/{r['bp_earned']}BPと通常Save/fresh Continueをscoped検証。真正30勝は未達。",
                f"{REPORT}の新たな最初の実敗北を修復する。受入単体・旧ARM・Ring hostを再実行しない。")
    if phase=='START':
        return ('28勝81BPと通常Save/fresh Continueの受入原本を保持。29戦目で健康な水先発を氷技のある水対面から'
                '無条件に交代させない通常入力修正を実装し、新規8契約を検証。新nativeは未実行。',
                '進行中の29戦目Actionsだけを照合する。重複起動せず、完了後に原本・固定引継ぎ・両ログを記録する。')
    d=value.get('partial_diagnostic',{})
    return (f"29戦目の通常先発維持の原本を保存。観測勝数{d.get('settled_wins','未採取')}。Save/Continue受入とは区別。"+str(value.get('failures',[])),
            f'{REPORT}の失敗段階と134event prefix証拠を読んで未完段階のみ修復。同じ失敗/旧builder/ARM/Ring host/受入単体を再実行しない。')


def checkpoint(value,phase):
    head=b.scope();state=b.resume.validate(ROOT);backlog=b.load(b.resume.BACKLOG)
    need(state['latest_native_run']==34946969126 and not state['release_ready'],'formal BP boundary')
    checkpoint=b.load('content/modernization/pr16_bp_chooser_checkpoint.json')
    need(checkpoint['accepted_case_count']==3 and checkpoint['candidate']['sha256']==state['candidate']['sha256'],'BP canonical checkpoint')
    row=next(x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(row['success_evidence'] is None and not row.get('complete'),'Circus suppression still open')
    stop,nxt=summary(value,phase);run_id=int(os.environ['GITHUB_RUN_ID'])
    value.update(recording_run=run_id,recording_source_head=head)
    state['circus_battle29']=dict(path=REPORT,run_id=run_id,classification=value['classification'],candidate=b.TARGET)
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action']['id']='CIRCUS_SUPPRESSION_NATIVE' if value.get('genuine_30_wins_verified') else 'CIRCUS_BATTLE29_RISK'
    state['next_action']['read_paths']=[REPORT,*FILES,'content/modernization/pr16_saved_reconstruction.json',b.resume.BACKLOG]
    state['remaining_sequence_ja']=('正規実受付から特性抑制 → 変更影響範囲P08（公開操作は別指示）' if value.get('genuine_30_wins_verified') else
                                  '同一候補で真正30勝と保存 → 正規実受付から特性抑制 → 変更影響範囲P08（公開操作は別指示）')
    state['session_execution_summary']={k:value.get(k,0) for k in ('new_emulator_processes','arm_compiles','arm_links','accepted_standalone_replays')}
    state['session_execution_summary']['new_emulator_processes']+=1 # この依頼の完了済み28戦目run
    state['session_execution_summary']['scope_ja']='この依頼の28戦目run(1)＋当runの実起動数。保存byte/固定生成Cを再利用。28勝は次の未完部分への連続prefixのみ。歴史的ARM総数unknownは維持。'
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='当checkpoint前のremote HEAD。実native sourceはreport。正式BP受入HEADは不変。'
    state['observed_head_checks']=dict(scope_head=head,runs=[dict(id=RUN,head_sha=WORKFLOW_HEAD,status='completed',conclusion='failure')],
        reason_ja='前runの28勝とSave成功を保持。29戦目実敗北のためrun結論はfailure。今回runは記録時in_progress。全CI greenは主張しない。')
    state['pending_runs']=[dict(run_id=run_id,tested_head=value['source_head'],status='in_progress',scope='battle29-risk')]
    note=f'{TASK} run{run_id}の新原本を先に読む。旧run35471833294の28勝/29戦目実敗北を30勝へ改作しない。受入単体/旧ARM/Ring host再実行は禁止。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    row['battle29_checkpoint']=REPORT;row['resume']=nxt
    if value.get('lifecycle_verified'):row['implementation_checkpoint']=REPORT;row['implementation_status']=value['classification']
    evidence={};prefix='evidence/pr16_circus_battle29/'+str(run_id)+'/'
    for path in sorted((b.OUT/'execution').rglob('*')):
        if not path.is_file() or path.suffix not in ('.c','.h','.json','.stdout','.stderr'):continue
        name=prefix+'execution/'+path.relative_to(b.OUT/'execution').as_posix()
        raw=path.read_bytes();b.write(name,raw);evidence[name]=b.identity(raw)
    value['text_evidence']=evidence
    b.write(REPORT,b.stable(value));b.write(b.resume.BACKLOG,b.stable(backlog))
    for name in (*FILES,REPORT,*evidence):state['source_bindings'][name]=b.identity((ROOT/name).read_bytes())
    if b.resume.BACKLOG in state['source_bindings']:state['source_bindings'][b.resume.BACKLOG]=b.identity((ROOT/b.resume.BACKLOG).read_bytes())
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    for label,args in [('resume',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_resume.py','-v']),
                       ('task-graph',[sys.executable,'scripts/validate_task_graph.py'])]:
        out,err,proc=b.capture(args,label+'-'+phase);need(b.exited(proc)==0,label+' failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry=(f'\n\n## {stamp} — {TASK}-{phase}\n- Timestamp: {stamp}\n- Task: {TASK} / 29戦目の通常先発維持\n'
        f"- Status: {'DONE' if value.get('lifecycle_verified') else 'STOPPED'}（全体受入は未完）\n"
        '- Version: pr16-circus-battle29-risk-v1\n- Summary: '+stop+'\n'
        '- Files changed: '+', '.join((*FILES,REPORT,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*evidence,*b.LOGS))+'\n'
        '- Verify: 新規8契約、固定resume整合性/影響tests、task graph、index差分private guard/diff check。native成否/実process数はreport。旧7契約・受入単体は再実行しない。\n'
        '- Commit: 同branch非force。自己SHAはremote/receipt。\n'
        '- Network: GitHub前run/job/artifactと旧24勝原本の固定照合。host mGBA依存のみ。旧builder/ARM/Ring hostなし。\n'
        '- Next: '+nxt+'\n')
    for name in b.LOGS:
        path=ROOT/name;need(f'{TASK}-{phase}\n' not in path.read_text(),'duplicate phase')
        with path.open('a') as stream:stream.write(entry)
    paths=[REPORT,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*evidence,*b.LOGS]
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines())
    need(changed and changed<=set(paths),'unexpected staged paths')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=head,b.OUT,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': '+phase+' 29戦目先発維持・原本・固定引継ぎ・両ログを同期'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    commit=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty tracked files')
    (b.OUT/('receipt-'+phase+'.json')).write_bytes(b.stable(dict(task=TASK,phase=phase,commit=commit,source_head=head,run_id=run_id,non_force_push=True)))
    print('RESULT='+('DONE' if value.get('lifecycle_verified') else 'STOPPED')+' TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


def prepare():
    head=b.scope();b.resume.validate(ROOT);b.OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted; inspect original instead of replay')
    import pr16_ring_compiled_record as source_guard
    source_guard.BASE='4432f1f52ad6075cfb54fbb1903eab950a573e92'
    source_guard.OUT=b.OUT;source_guard.ALLOWED=set(FILES);source_guard.guard()
    prior=previous_attempt()
    out,err,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_circus_battle29.py','-v'],'risk-tests')
    need(b.exited(proc)==0 and b'Ran 8 tests' in err and b'\nOK\n' in err,'risk contracts')
    value=dict(schema_version=1,task=TASK,classification='CIRCUS_BATTLE29_RISK_IMPLEMENTED_NATIVE_PENDING',source_head=head,
        workflow_source_head=os.environ['GITHUB_SHA'],candidate=b.TARGET,previous_attempt=prior,original=b.originals(),
        host_tests=dict(tests_run=8,success=True,skipped=0),new_emulator_processes=0,arm_compiles=0,arm_links=0,
        accepted_standalone_replays=0,rom_changes=0,genuine_30_wins_verified=False,lifecycle_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,failures=[],visual_review_completed=False)
    checkpoint(value,'START')


def native():
    execution_head=b.scope()
    value=b.native()
    value['native_execution_head']=execution_head
    path=b.OUT/'execution'/(b.probe.CASE+'.stderr')
    if path.exists():
        raw=path.read_bytes()
        try:
            value['partial_diagnostic']=p.parent.diagnostic(raw)
            value['prefix29']=p.prefix_proof(old_trace(),raw)
            (b.OUT/'execution/prefix29.json').write_bytes(b.stable(value['prefix29']))
        except Exception as error:value['failures'].append(dict(stage='prefix29',type=type(error).__name__,error=str(error)))
    if value['failures']:value['lifecycle_verified']=value['genuine_30_wins_verified']=False
    value['classification']=('CIRCUS_GENUINE_30_WINS_90BP_SAVE_CONTINUE' if value['genuine_30_wins_verified'] else
                             'CIRCUS_BATTLE29_LOSS_SAVE_SCOPED_30_OPEN' if value['lifecycle_verified'] else 'CIRCUS_BATTLE29_DIAGNOSTIC_OPEN')
    (b.OUT/'native-result.json').write_bytes(b.stable(value))


def finish():
    path=b.OUT/'native-result.json';value=b.probe.strict(path.read_bytes()) if path.exists() else b.load(REPORT)
    if not path.exists():value['failures'].append(dict(stage='workflow-setup',error='native not started'))
    checkpoint(value,'FINISH')


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('prepare','native','finish','pack','result'),'command')
    if sys.argv[1]=='pack':b.OUT.mkdir(parents=True,exist_ok=True);b.pack()
    elif sys.argv[1]=='result':
        value=b.load(REPORT);need(value['genuine_30_wins_verified'] and not value['failures'],'genuine 30-win target remains open')
    else:globals()[sys.argv[1]]()
