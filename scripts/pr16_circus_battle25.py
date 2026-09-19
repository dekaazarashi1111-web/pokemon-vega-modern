#!/usr/bin/env python3
"""保存byte/固定hostソースで25戦目以降だけ入力変更。各境界を非force記録する。"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_circus_battle25_policy as policy
import pr16_circus_reentry_probe as probe
import pr16_resume as resume
need=policy.need
REPO='dekaazarashi1111-web/pokemon-vega-modern'
BRANCH='codex/modernization-followup-20260908'
TASK='USER-20260920-CIRCUS-BATTLE25'
BASE='0272b99f2e5b26e78aae35f9a6c21e8724586fd2'
RUN=35457636604
JOB=105935643398
ARTIFACT=10588831175
OLD_HEAD='69075ada3e54a3218a916b5b532f8883428c6bfa'
ZIP_ID=dict(size=2102798,sha256='2efd504a7fcd97934a781444352f0b9474da3679a3a184e8143381cefe9bd75f')
SHA='2b107e7ef897844eff810ff0b40f82543640488696e8295194ceb3b66fb2c183'
TARGET=dict(size=33554432,sha256=SHA)
SEED='.local/60_wild_species_root_repair.srm'
SEED_SHA='f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'
OLD='evidence/pr16_circus_rental_drought/35457636604/native/'
SELF='scripts/pr16_circus_battle25.py'
HEADER='tools/mgba_pr16_circus_battle25.h'
TEST='tests/test_pr16_circus_battle25.py'
WORKFLOW='.github/workflows/pr16-circus-battle25.yml'
FILES=(SELF,HEADER,TEST,WORKFLOW,'scripts/pr16_circus_battle25_policy.py')
REPORT='content/modernization/pr16_circus_battle25.json'
OUT=ROOT/'.local/pr16-circus-battle25'
EVIDENCE='evidence/pr16_circus_battle25/'
LOGS=('design/run_log.md','design/version_log.md')


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
def load(name):return probe.strict((ROOT/name).read_bytes())
def write(name,raw):
    path=resume.safe_path(ROOT,name);raw.decode();need(b'\0' not in raw,'text required')
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
def command(*args):return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def api(path):return json.loads(command('gh','api','repos/'+REPO+'/'+path))


def scope():
    need(os.environ.get('GITHUB_REPOSITORY')==REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH,'branch scope')
    head=command('git','rev-parse','HEAD');pr=api('pulls/16')
    need(pr['state']=='open' and pr['draft'] is True and not pr['merged'] and pr['head']['ref']==BRANCH and
         pr['head']['repo']['full_name']==REPO,'PR scope')
    need(command('git','ls-remote','--exit-code','origin','refs/heads/'+BRANCH).split()==[head,'refs/heads/'+BRANCH],'remote advanced')
    subprocess.run(['git','merge-base','--is-ancestor',BASE,head],cwd=ROOT,check=True)
    return head


def capture(args,label,timeout=120):
    folder=OUT/'execution';folder.mkdir(parents=True,exist_ok=True)
    proc=dict(schema_version=1,returncode=None,timed_out=False,spawn_error=None)
    stdout=stderr=b''
    try:
        done=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=timeout)
        stdout,stderr=done.stdout,done.stderr;proc['returncode']=done.returncode
    except subprocess.TimeoutExpired as error:
        proc['timed_out']=True;stdout=error.stdout or b'';stderr=error.stderr or b''
    except OSError as error:proc['spawn_error']=str(error)
    for suffix,raw in (('.stdout',stdout),('.stderr',stderr),('.process.json',stable(proc))):
        (folder/(label+suffix)).write_bytes(raw)
    return stdout,stderr,proc


def exited(proc):
    need(not proc['timed_out'] and proc['spawn_error'] is None and type(proc['returncode']) is int,'process did not exit')
    return proc['returncode']


def originals():
    run,job,artifact=api('actions/runs/'+str(RUN)),api('actions/jobs/'+str(JOB)),api('actions/artifacts/'+str(ARTIFACT))
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==OLD_HEAD,'old run scope')
    need(job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='failure','old job scope')
    need(artifact['workflow_run']['id']==RUN and artifact['workflow_run']['head_sha']==OLD_HEAD and
         not artifact['expired'] and artifact['digest']=='sha256:'+ZIP_ID['sha256'],'old artifact scope')
    raw=subprocess.check_output(['gh','api','repos/'+REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    need(identity(raw)==ZIP_ID,'original archive bytes')
    native=load(OLD+'report.json')
    original=OUT/'original';(original/'generated').mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist())==len(set(z.namelist())),'duplicate artifact member')
        need(z.read('finish/native/report.json')==(ROOT/(OLD+'report.json')).read_bytes(),'tracked native report differs')
        for name,bound in native['generated'].items():
            need(Path(name).name==name and Path(name).suffix in ('.c','.h'),'generated name')
            data=z.read('finish/native/generated/'+name);need(identity(data)==bound,'generated binding: '+name)
            data.decode();need(b'\0' not in data,'nontext generated source')
            (original/'generated'/name).write_bytes(data)
    for suffix in ('.stdout','.stderr'):
        shutil.copyfile(ROOT/(OLD+probe.CASE+suffix),original/(probe.CASE+suffix))
    bound={}
    for name,expected in native['sources'].items():
        # Includes are compiled directly; old Python builder modules are not imported/executed.
        if Path(name).suffix in ('.c','.h') or name in ('scripts/pr16_circus_continuous_probe.py','scripts/pr16_circus_reentry_probe.py'):
            need(identity(resume.safe_path(ROOT,name).read_bytes())==expected,'host dependency changed: '+name)
            bound[name]=expected
    need(identity((ROOT/'tools/mgba_pr16_circus_continuous.c').read_bytes())==native['generated']['controller.c'],'controller changed')
    probe.SHA=SHA
    old=probe.validate((original/(probe.CASE+'.stdout')).read_bytes(),(original/(probe.CASE+'.stderr')).read_bytes(),0,probe.CASE)
    need((old['wins'],old['losses'],old['bp_earned'])==(24,1,72),'old boundary')
    return dict(run_id=RUN,job_id=JOB,artifact_id=ARTIFACT,source_head=OLD_HEAD,archive=ZIP_ID,
                original_conclusion='failure',host_dependencies=bound,generated=native['generated'])


def tests():
    raw,err,proc=capture([sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_circus_battle25.py','-v'],'policy-tests')
    need(exited(proc)==0 and b'Ran 7 tests' in err and b'\nOK\n' in err,'policy contracts failed')
    return dict(tests_run=7,success=True,skipped=0)


def checkpoint(value,phase):
    head=scope();state=resume.validate(ROOT);backlog=resume.load(ROOT,resume.BACKLOG)
    need(state['latest_native_run']==34946969126 and state['release_ready'] is False,'formal BP boundary')
    rows=[x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION']
    need(len(rows)==1 and rows[0]['success_evidence'] is None and not rows[0].get('complete'),'physical gap changed')
    passed=value.get('genuine_30_wins_verified') is True
    lifecycle=value.get('lifecycle_verified') is True
    if passed:
        stop='同一2b107e7eで真正30勝・90BP・通常Save/fresh Continueを検証。最初の入力変更前113eventsとbyte列は旧24勝原本と完全一致。ROM変更/ARM compile/link0。実受付から特性抑制とP08は未完。'
        nxt='このrunの30勝原本と終端画面を照合し、同一候補の正規実受付から特性抑制を検証する。30勝を独立再実行しない。特性抑制後は変更影響台帳によるP08へ進む。'
    elif lifecycle:
        r=value['result'];stop=f"25戦目限定入力の同一候補で実{r['wins']}勝・{r['bp_earned']}BP、{r['battles']}戦目敗北後の通常Save/fresh Continueを検証。旧24勝prefixは完全一致。真正30勝は未達。"
        nxt=f"{REPORT}の新原本から{r['battles']}戦目の最初の失敗を修復。旧24勝と今回成功分の独立再実行は禁止。保存byteのみで候補を復元し、必要な継続prefixだけを通す。"
    elif phase=='START':
        stop='25戦目限定レンタル相性方策と記録7契約を検証し実装checkpointを保存。新nativeは未実行。旧24勝72BPの受入を保持、真正30勝は未受入。'
        nxt='進行中の同branch Actionsを照合する。同じrunを重複起動せず、25戦目通常入力の未完nativeを完了・原本と引継ぎを記録する。'
    else:
        stop='25戦目限定方策の試行原本を保存。検証未達を受入へ昇格しない。'+str(value.get('failures',[]))
        nxt=f'{REPORT}の失敗段階・実process数・prefix証拠を読んで未完段階だけ修復。旧builder/ARM/Ring host/受入単体を再実行しない。'
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['recording_source_head']=head
    ref=dict(path=REPORT,run_id=value['recording_run'],classification=value['classification'],candidate=TARGET)
    state['circus_battle25']=ref
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action']['id']='CIRCUS_SUPPRESSION_NATIVE' if passed else 'CIRCUS_BATTLE25_ORDINARY_POLICY'
    state['next_action']['read_paths']=[REPORT,*FILES,'content/modernization/pr16_saved_reconstruction.json',resume.BACKLOG]
    state['remaining_sequence_ja']=('正規実受付から特性抑制 → 変更影響範囲P08最終統合・release判断（公開操作は別指示）' if passed else
        '同一候補で真正30勝と保存 → 正規実受付から特性抑制 → 変更影響範囲P08（公開操作は別指示）')
    state['session_execution_summary']={k:value.get(k,0) for k in ('new_emulator_processes','arm_compiles','arm_links','accepted_standalone_replays')}
    state['session_execution_summary']['scope_ja']='保存byte復元と25戦目限定通常入力。24勝は継続prefixのみ。履歴bootstrap全体ARM数はunknownのまま。'
    note=f"{TASK} run{value['recording_run']}の原本と実停止を先に読む。旧run35457636604を30勝成功へ改作しない。保存JSON/固定生成Cを使用し旧親builder/ARM/Ring hostを呼ばない。"
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='当checkpoint記録前のremote HEAD。native sourceはreportのsource_head。正式BP受入HEADは不変。'
    state['observed_head_checks']=dict(scope_head=head,runs=[dict(id=RUN,head_sha=OLD_HEAD,status='completed',conclusion='failure')],
        reason_ja='旧30勝目標run35457636604はfailureのまま。今回runは記録時in_progressで全CI greenは主張しない。')
    state['pending_runs']=[dict(run_id=value['recording_run'],tested_head=value['source_head'],status='in_progress',scope='battle25-continuation')]
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    rows[0]['battle25_checkpoint']=REPORT;rows[0]['resume']=nxt
    if lifecycle:rows[0]['implementation_checkpoint']=REPORT;rows[0]['implementation_status']=value['classification']
    prefix=EVIDENCE+os.environ['GITHUB_RUN_ID']+'/'
    evidence={}
    # Public text only: generated controller/policy and execution receipts, not ROM/save/binary.
    for folder,label in ((OUT/'original/generated','original-generated/'),(OUT/'execution','execution/')):
        for path in sorted(folder.rglob('*')):
            if not path.is_file() or path.suffix not in ('.c','.h','.json','.stdout','.stderr'):continue
            name=prefix+label+path.relative_to(folder).as_posix();raw=path.read_bytes()
            write(name,raw);evidence[name]=identity(raw)
    value['text_evidence']=evidence
    write(REPORT,stable(value));write(resume.BACKLOG,stable(backlog))
    for name in (*FILES,REPORT,resume.BACKLOG,*evidence):state['source_bindings'][name]=identity((ROOT/name).read_bytes())
    write(resume.STATE,stable(state));write(resume.DOC,resume.render(state).encode())
    resume.validate(ROOT)
    out,err,proc=capture([sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_resume.py','-v'],'resume-'+phase)
    need(exited(proc)==0,'resume tests')
    out,err,proc=capture([sys.executable,'scripts/validate_task_graph.py'],'task-graph-'+phase)
    need(exited(proc)==0,'task graph')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry=(f'\n\n## {stamp} — {TASK}-{phase}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        f"- Status: {'DONE（入力実装とscoped検証・記録。全体受入は未完）' if lifecycle else 'WIP（未達段階はreport参照）'}\n"
        '- Version: pr16-circus-battle25-input-v1\n- Summary: '+stop+'\n'
        '- Files changed: '+', '.join((*FILES,REPORT,resume.STATE,resume.DOC,resume.BACKLOG,*evidence,*LOGS))+'\n'
        '- Verify: 方策/記録7契約、resume整合性/影響tests/task graph、index差分private guardとdiff check。native結果はreportの原本と実process数を参照。\n'
        '- Commit: 同branch非force commit。自己SHAはremote/receipt参照。\n'
        '- Network: GitHub固定run/artifact照合。入力/ROM/save/credentialの新規追跡なし。旧builder/ARM/Ring hostを実行しない。\n'
        '- Next: '+nxt+'\n')
    for name in LOGS:
        path=ROOT/name;need(f'{TASK}-{phase}\n' not in path.read_text(),'duplicate phase log')
        with path.open('a') as stream:stream.write(entry)
    paths=[REPORT,resume.STATE,resume.DOC,resume.BACKLOG,*evidence,*LOGS]
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(command('git','diff','--cached','--name-only',head).splitlines())
    need(changed and changed<=set(paths),'unexpected staged path')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=head,OUT,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': '+phase+' 25戦目限定入力と原本・固定引継ぎ・両ログを同期'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+BRANCH],cwd=ROOT,check=True)
    commit=scope();need(not command('git','status','--porcelain','--untracked-files=no'),'dirty after push')
    (OUT/('receipt-'+phase+'.json')).write_bytes(stable(dict(task=TASK,phase=phase,commit=commit,source_head=head,run_id=value['recording_run'],non_force_push=True)))
    print('RESULT='+phase+' TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


def prepare():
    scope();resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted; inspect original instead of replay')
    value=dict(schema_version=1,task=TASK,classification='BATTLE25_INPUT_IMPLEMENTED_NATIVE_PENDING',source_head=command('git','rev-parse','HEAD'),
        candidate=TARGET,original=originals(),host_tests=tests(),new_emulator_processes=0,arm_compiles=0,arm_links=0,
        accepted_standalone_replays=0,rom_changes=0,genuine_30_wins_verified=False,lifecycle_verified=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,failures=[],visual_review_completed=False,workflow_source_head=os.environ['GITHUB_SHA'],prior_setup_failures=[dict(run_id=35467548807,job_id=105962556068,source_head='f8d84b1ec0944921928cbb19b7d5f16837218da6',original_conclusion='failure',native_processes=0,artifact_id=10592095504,archive=dict(size=138612,sha256='c7fbd2f2c7aae3f69425813df1ca794d1d2f03cad52f55ea5fb6f0b36aee3cb1'),reason_ja='旧continuous probeはEnd/ABORT世代を扱えず、原本照合で停止。既存reentry probeへ接続し実原本全体を回帰検査。')])
    value['prior_setup_failures'].append(dict(run_id=35467683171,job_id=105962909421,source_head='c4ac48db61d6dcd5bb90fc4712dd548694cfff8e',original_conclusion='failure',native_processes=0,artifact_id=10591528567,archive=dict(size=139413,sha256='7639b0db1de7d7a53c29e48c7f609fb6ca1dbdc9f14c9d5bc3bab04882d46004'),reason_ja='pending_runsのtested_head/status必須キー不一致。記録producerの実生成式を回帰検査。'))
    checkpoint(value,'START')


def native():
    scope();resume.validate(ROOT);value=load(REPORT)
    need(value['new_emulator_processes']==0 and value['recording_run']==int(os.environ['GITHUB_RUN_ID']),'native already attempted')
    work=OUT/'work';work.mkdir(parents=True,exist_ok=True)
    protected={}
    try:
        # This interpreter must retain subprocess ability; reconstruction has its own hard process/network barrier.
        program="""import sys,json
from pathlib import Path
sys.path.insert(0,'scripts')
import pr16_saved_reconstruction as r
def offline(event,args):
    if event.startswith('socket.') or event in ('urllib.Request','http.client.connect'):raise RuntimeError('offline reconstruction')
sys.addaudithook(offline)
print(json.dumps(r.reconstruct(Path('.local/pr16-circus-battle25/runtime').resolve())))
"""
        raw,err,proc=capture([sys.executable,'-c',program],'reconstruct',120)
        need(exited(proc)==0 and not err,'saved byte reconstruction failed')
        value['reconstruction']=probe.strict(raw)
        candidate=OUT/'runtime/candidate.gba';seed=ROOT/SEED
        need(identity(candidate.read_bytes())==TARGET,'runtime candidate identity')
        need(not seed.is_symlink() and hashlib.sha256(seed.read_bytes()).hexdigest()==SEED_SHA,'fixed seed missing or changed')
        protected={str(p):identity(p.read_bytes()) for p in (candidate,seed)}
        for name,bound in value['original']['host_dependencies'].items():
            need(identity((ROOT/name).read_bytes())==bound,'native dependency drift: '+name)
        for name,bound in value['original']['generated'].items():
            data=(OUT/'original/generated'/name).read_bytes();need(identity(data)==bound,'original C changed')
            if name=='pr16_streak_policy.c':
                data=policy.adapt(data.decode(),(ROOT/HEADER).read_text()).encode()
                (OUT/'execution/policy.c').write_bytes(data)
            (work/name).write_bytes(data)
        value['generated']={n:identity((work/n).read_bytes()) for n in value['original']['generated']}
        exe=work/'runner'
        raw,err,proc=capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),str(work/'controller.c'),'-lmgba','-o',str(exe)],'compile')
        need(exited(proc)==0 and not err,'new host controller compile failed')
        value['host_compiles']=1;value['executable']=identity(exe.read_bytes())
        # Guard implementation/control/helpers are byte-identical. Reuse their seven original checks, not separate accepted native cases.
        value['guard_evidence_reused']=[OLD+'guard-'+g+'.process.json' for g in ('bus8','bus16','bus32','raw8','raw16','raw32','register')]
        for name in value['guard_evidence_reused']:
            need(exited(load(name))==1,'inherited guard not enforced')
        scratch=work/'scratch.srm';shutil.copyfile(seed,scratch)
        shots=OUT/'screens';shots.mkdir(exist_ok=True)
        value['new_emulator_processes']=1
        raw,err,proc=capture([str(exe),str(candidate),str(scratch),SHA,SEED_SHA,probe.CASE,str(shots/probe.CASE)],probe.CASE,900)
        value['process']=proc
        probe.SHA=SHA
        result=probe.validate(raw,err,exited(proc),probe.CASE)
        events=probe.parse(err);old_events=probe.parse((OUT/'original'/(probe.CASE+'.stderr')).read_bytes())
        value['prefix']=policy.prefix_proof((OUT/'original'/(probe.CASE+'.stderr')).read_bytes(),err,old_events,events)
        value['result']=result;value['analysis']=probe.analyze(events,result)
        value['analysis']['accepted_prefix_battles_reexecuted_for_continuation']=24
        value['lifecycle_verified']=True;value['genuine_30_wins_verified']=result['wins']==30
        value['classification']='CIRCUS_GENUINE_30_WINS_90BP_SAVE_CONTINUE' if result['wins']==30 else 'CIRCUS_BATTLE25_FIRST_LOSS_SCOPED_30_OPEN'
        for name,data in (('events.json',events),('prefix.json',value['prefix']),('analysis.json',value['analysis'])):
            (OUT/'execution'/name).write_bytes(stable(data))
        screens={}
        for path in sorted(shots.glob('*.ppm')):
            data=path.read_bytes();need(data.startswith(b'P6\n240 160\n255\n') and len(data)==115215,'native screenshot shape')
            screens[path.name]=identity(data)
        need(len(screens)>=4,'native screenshots missing');value['screens']=screens
    except Exception as error:
        value['failures'].append(dict(stage='native-or-setup',type=type(error).__name__,error=str(error)))
        value['classification']='BATTLE25_DIAGNOSTIC_OPEN'
    finally:
        for name,bound in protected.items():
            if identity(Path(name).read_bytes())!=bound:value['failures'].append(dict(stage='immutability',error=name))
        if value['failures']:value['genuine_30_wins_verified']=value['lifecycle_verified']=False
        (OUT/'native-result.json').write_bytes(stable(value))
    return value


def finish():
    path=OUT/'native-result.json';value=probe.strict(path.read_bytes()) if path.exists() else load(REPORT)
    if not path.exists():value['failures'].append(dict(stage='workflow-setup',error='native not started; inspect workflow logs'))
    checkpoint(value,'FINISH')


def pack():
    dst=OUT/'artifact';dst.mkdir(exist_ok=True)
    for path in sorted(OUT.rglob('*')):
        if not path.is_file() or path.is_relative_to(dst) or path.is_relative_to(OUT/'work') or path.is_relative_to(OUT/'runtime'):continue
        if path.suffix not in ('.json','.c','.h','.stdout','.stderr','.ppm'):continue
        raw=path.read_bytes()
        if path.suffix=='.ppm':need(raw.startswith(b'P6\n240 160\n255\n') and len(raw)==115215,'pack screenshot')
        else:
            raw.decode();need(b'\0' not in raw and len(raw)<4000000,'pack text')
            need(not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',raw),'pack credential')
        target=dst/path.relative_to(OUT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('prepare','native','finish','pack','result'),'command')
    if sys.argv[1]=='native':native()
    elif sys.argv[1]=='result':
        value=load(REPORT);need(value['genuine_30_wins_verified'] and not value['failures'],'genuine 30-win target remains open')
    else:globals()[sys.argv[1]]()
