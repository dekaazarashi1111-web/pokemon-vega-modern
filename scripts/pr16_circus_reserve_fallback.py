#!/usr/bin/env python3
"""最新原本を保持し、実対面変更後の未完nativeだけを1回実行・非force記録。"""
from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_circus_battle25 as b
import pr16_circus_reserve_fallback_policy as p

TASK='USER-20260920-CIRCUS-RESERVE'
REPORT='content/modernization/pr16_circus_reserve_fallback.json'
OLD_REPORT='content/modernization/pr16_circus_battle29_recheck.json'
OLD_PREFIX='evidence/pr16_circus_battle29_recheck/35477541574/execution/'
BASE='9b028ecea4e41728e79a6d8531d931a6e1ae51c4'
RUN=35477541574
JOB=105989277934
ART=10594548366
OLD_HEAD='35fcac915e6f40150abc06c299f68c19823f0264'
ARCHIVE=dict(size=1051266,sha256='58682849ae9df9086be4907d54c02675f8296d7ef51ce56a141635590871c702')
FILES=('scripts/pr16_circus_reserve_fallback.py','scripts/pr16_circus_reserve_fallback_policy.py',
       'tests/test_pr16_circus_reserve_fallback.py','.github/workflows/pr16-circus-reserve-fallback.yml')
ROOT=b.ROOT
b.REPORT,b.TASK=REPORT,TASK
b.policy=SimpleNamespace(adapt=p.adapt,prefix_proof=b.policy.prefix_proof)
need=b.need


def previous():
    old=b.load(OLD_REPORT)
    need(old['recording_run']==RUN and old['source_head']==OLD_HEAD and old['candidate']==b.TARGET
         and old['new_emulator_processes']==1 and old['result']['wins']==28
         and old['result']['losses']==1 and not old['lifecycle_verified']
         and old['failures']==[dict(stage='prefix29-recheck',type='ValueError',error='healthy hold was not repeatedly reevaluated')],
         'previous result or failure changed')
    run,job,artifact=b.api('actions/runs/'+str(RUN)),b.api('actions/jobs/'+str(JOB)),b.api('actions/artifacts/'+str(ART))
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==OLD_HEAD,'previous run')
    need(job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='failure','previous job')
    need(artifact['workflow_run']['id']==RUN and artifact['size_in_bytes']==ARCHIVE['size']
         and artifact['digest']=='sha256:'+ARCHIVE['sha256'],'previous artifact')
    raw=(ROOT/(OLD_PREFIX+b.probe.CASE+'.stderr')).read_bytes()
    return dict(run_id=RUN,job_id=JOB,artifact_id=ART,workflow_source_head=OLD_HEAD,archive=ARCHIVE,
                report_path=OLD_REPORT,report_identity=b.identity((ROOT/OLD_REPORT).read_bytes()),
                original_conclusion='failure',review=p.original(raw))


def summary(value,phase):
    if value.get('genuine_30_wins_verified'):
        return ('同一2b107e7eで真正30勝90BP・元party600/owner64・通常Save/fresh Continueを検証。'
                '28勝＋29戦目action134eventsと水対面6turnを保持し、次の実対面から通常控え選択を補完。ROM変更/ARM0。',
                'このrunの原本と終端画面を照合し、正規実受付から特性抑制へ進む。30勝単独再実行は禁止。P08移送・releaseは未完。')
    if value.get('lifecycle_verified'):
        r=value['result']
        return (f"控え代替選択後の実{r['wins']}勝/{r['bp_earned']}BPと通常Save/fresh Continueをscoped検証。真正30勝は未達。",
                f'{REPORT}の新たな最初の実敗北だけを修復。受入単体・旧ARM・Ring hostは再実行しない。')
    if phase=='START':
        return ('run35477541574の原本を照合。水対面は6turnで終了し468129は別個体type0/0。旧検証器の予測誤りとfailureを保持。'
                '要求技のない控え選択を実HP/PP/相性で補完する新規10契約を検証。新nativeは未実行。',
                '進行中のreserve-fallback Actionsだけを照合。重複起動せず、完了後に新原本・固定引継ぎ・両ログを記録する。')
    return ('控え代替選択の試行原本を保存。未検証を受入にしない。'+str(value.get('failures',[])),
            f'{REPORT}の失敗段階と実対面prefixを確認し、その未完段階だけ修復する。旧失敗・受入単体・旧ARMを再実行しない。')


def checkpoint(value,phase):
    head=b.scope();state=b.resume.validate(ROOT);backlog=b.load(b.resume.BACKLOG)
    formal=b.load('content/modernization/pr16_bp_chooser_checkpoint.json')
    need(state['latest_native_run']==34946969126 and formal['accepted_case_count']==3
         and formal['candidate']['sha256']==state['candidate']['sha256'] and not state['release_ready'],'formal scope')
    row=next(x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(row['success_evidence'] is None and not row.get('complete'),'suppression still open')
    stop,nxt=summary(value,phase);rid=int(os.environ['GITHUB_RUN_ID'])
    value.update(recording_run=rid,recording_source_head=head)
    state['circus_reserve_fallback']=dict(path=REPORT,run_id=rid,classification=value['classification'],candidate=b.TARGET)
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action']['id']='CIRCUS_SUPPRESSION_NATIVE' if value.get('genuine_30_wins_verified') else 'CIRCUS_RESERVE_FALLBACK'
    state['next_action']['read_paths']=[REPORT,*FILES,'content/modernization/pr16_saved_reconstruction.json',b.resume.BACKLOG]
    state['remaining_sequence_ja']=('正規実受付から特性抑制 → 変更影響範囲P08（公開操作は別指示）' if value.get('genuine_30_wins_verified') else
                                  '同一候補で真正30勝と保存 → 正規実受付から特性抑制 → 変更影響範囲P08（公開操作は別指示）')
    state['session_execution_summary']={k:value.get(k,0) for k in ('new_emulator_processes','arm_compiles','arm_links','accepted_standalone_replays')}
    state['session_execution_summary']['scope_ja']='当runの実起動数。保存byte/固定生成C再利用。28勝は未完部分への連続prefixで受入単体0。履歴ARM総数unknownは維持。'
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='当checkpoint前のremote HEAD。native sourceはreport。正式BP受入は変更なし。'
    state['observed_head_checks']=dict(scope_head=head,runs=[dict(id=RUN,head_sha=OLD_HEAD,status='completed',conclusion='failure')],
        reason_ja='前runの6回再評価/28勝/Save実測と検証器failureを保持。今回runは記録中。全CI greenは主張しない。')
    state['pending_runs']=[dict(run_id=rid,tested_head=value['source_head'],status='in_progress',scope='reserve-fallback')]
    note=f'{TASK} run{rid}の新原本を先に読む。run{RUN}のfailureを改作しない。控え方策/通常入力のみ。旧ARM/受入単体/Ring host再実行は禁止。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    row['reserve_fallback_checkpoint']=REPORT;row['resume']=nxt
    if value.get('lifecycle_verified'):row['implementation_checkpoint']=REPORT;row['implementation_status']=value['classification']
    evidence={};prefix=f'evidence/pr16_circus_reserve_fallback/{rid}/'
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
    entry=(f'\n\n## {stamp} — {TASK}-{phase}\n- Timestamp: {stamp}\n- Task: {TASK} / 実対面変更後の控え選択\n'
        f"- Status: {'DONE' if value.get('lifecycle_verified') else 'STOPPED'}（Circus/P08全体は未完）\n"
        '- Version: pr16-circus-reserve-v1\n- Summary: '+stop+'\n'
        '- Files changed: '+', '.join((*FILES,REPORT,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*evidence,*b.LOGS))+'\n'
        '- Verify: 新規10契約、固定resume整合性/影響tests、task graph、index差分private guard/diff check。native成否/実process数はreport。\n'
        '- Commit: 同branch非force。自己SHAはremote/receipt。\n'
        '- Network: GitHub前run/job/artifact原本照合、host mGBA依存のみ。旧builder/ARM/Ring hostなし。\n'
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
    subprocess.run(['git','commit','-m',TASK+': '+phase+' 実対面・原本・固定引継ぎ・両ログを同期'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    commit=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty tracked files')
    (b.OUT/('receipt-'+phase+'.json')).write_bytes(b.stable(dict(task=TASK,phase=phase,commit=commit,source_head=head,run_id=rid,non_force_push=True)))
    print('RESULT='+('DONE' if value.get('lifecycle_verified') else 'STOPPED')+' TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


def prepare():
    head=b.scope();b.resume.validate(ROOT);b.OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted; inspect original instead of replay')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,b.OUT,set(FILES);guard.guard()
    prior=previous()
    out,err,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_circus_reserve_fallback.py','-v'],'reserve-tests')
    need(b.exited(proc)==0 and b'Ran 10 tests' in err and b'\nOK\n' in err,'reserve contracts')
    value=dict(schema_version=1,task=TASK,classification='CIRCUS_RESERVE_IMPLEMENTED_NATIVE_PENDING',source_head=head,
        workflow_source_head=os.environ['GITHUB_SHA'],candidate=b.TARGET,previous_attempt=prior,original=b.originals(),
        host_tests=dict(tests_run=10,success=True,skipped=0),new_emulator_processes=0,arm_compiles=0,arm_links=0,
        accepted_standalone_replays=0,rom_changes=0,genuine_30_wins_verified=False,lifecycle_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,failures=[],visual_review_completed=False)
    checkpoint(value,'START')


def native():
    execution_head=b.scope();value=b.native();value['native_source_head']=execution_head
    if (b.OUT/'execution'/(b.probe.CASE+'.stderr')).exists():
        try:
            value['matchup_prefix']=p.prefix_proof((ROOT/(OLD_PREFIX+b.probe.CASE+'.stderr')).read_bytes(),
                (b.OUT/'execution'/(b.probe.CASE+'.stderr')).read_bytes())
            (b.OUT/'execution/matchup-prefix.json').write_bytes(b.stable(value['matchup_prefix']))
        except Exception as error:value['failures'].append(dict(stage='matchup-prefix',type=type(error).__name__,error=str(error)))
    if value['failures']:value['lifecycle_verified']=value['genuine_30_wins_verified']=False
    value['classification']=('CIRCUS_GENUINE_30_WINS_90BP_SAVE_CONTINUE' if value['genuine_30_wins_verified'] else
                             'CIRCUS_RESERVE_LOSS_SAVE_SCOPED_30_OPEN' if value['lifecycle_verified'] else 'CIRCUS_RESERVE_DIAGNOSTIC_OPEN')
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
