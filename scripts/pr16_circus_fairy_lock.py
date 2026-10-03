#!/usr/bin/env python3
"""確定済みgetter/抑制を再観測せず、同一ROM/Save30から残る帰還・保存を検証。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TASK='USER-20260920-CIRCUS-FAIRY-LOCK'
BASE='2fc3180a732c235f829a340ddf5a9d0ab19a200a'
RUN=35503514936
SOURCE='5618a38f6854aa4551e5c518509f5f97cf2a79b0'
PRIOR='content/modernization/pr16_circus_getter_followup.json'
REPORT='content/modernization/pr16_circus_suppression_lifecycle.json'
HEADER='tools/mgba_pr16_circus_fairy_lock.h'
SELF='scripts/pr16_circus_fairy_lock.py'
TEST='tests/test_pr16_circus_fairy_lock.py'
WORKFLOW='.github/workflows/pr16-circus-fairy-lock.yml'
FILES=(SELF,TEST,HEADER,WORKFLOW)
SHA='46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38'
ARCHIVE=dict(size=332538,sha256='c16ef7c1e05e5dad1ba4169016a9bbd863c97098eae9c2cb6c7d94d71d905eba')


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def exact(text,before,after):
    need(text.count(before)==1,'generated source boundary: '+before[:60])
    return text.replace(before,after)


def adapt(files):
    """選出/技/強制交代/勝敗処理を温存。既観測0..2抽選とCPU traceだけを省く。"""
    out=dict(files)
    policy=files['pr16_streak_policy.c'].decode()
    before='    unsigned streak=read16(c,0x0203DB20U);if(streak<15U)return;'
    out['pr16_streak_policy.c']=('#include "mgba_pr16_circus_fairy_lock.h"\n'+
        exact(policy,before,before+'\n    if(fl_observe(c,streak))return;')).encode()
    controller=files['controller.c'].decode()
    out['controller.c']=exact(controller,'#include "mgba_pr16_circus_getter_trace.h"',
        '/* run35503514936のgetter30原本を継承。新CPU traceは行わない。 */\n'
        'static void cg_begin(struct mCore *c){(void)c;}\nstatic void cg_end(struct mCore *c){(void)c;}').encode()
    text=files['getter_suppression.h'].decode()
    a=text.index('struct SSRoute ');z=text.index('static void ss_copy(',a)
    text=text[:a]+('/* 抑制predicate/delegate原本は同一candidateのrun35503514936から継承。 */\n'
        'static unsigned ss_fresh_cores;\n'
        'static const unsigned ss_predicates=0U,ss_delegates=0U,ss_trace_frames=0U;\n'
        'static const uint64_t ss_instructions=0U;\n')+text[z:]
    for before,after in (
        ('    if(ss_fast_frame)c->runFrame=ss_fast_frame;\n',''),
        ('for(unsigned attempt=0;attempt<64U;++attempt)','for(unsigned attempt=3U;attempt<4U;++attempt)'),
        ('if(!target){ss_close(c,&original);continue;}','bp_require(c,target && flags==0x80000200U,"known ordinary delay51 draw changed; no sweep fallback");'),
        ('g_shot("suppression-real-action");ss_fast_frame=c->runFrame;c->runFrame=ss_frame;','g_shot("suppression-real-action");'),
        ('c->runFrame=ss_fast_frame;sc_returned(c);','sc_returned(c);'),
        ('argv[5],hash,attempt+1U,','argv[5],hash,1U,'),
    ):text=exact(text,before,after)
    out['getter_suppression.h']=text.encode()
    return out


def validate_draws(values,old):
    need(len(values)==1 and len(old)==4,'single known draw only')
    row=values[0];prior=old[3]
    for key in ('attempt','delay','current','best','bp','counter','flags','types','newbs','target'):
        need(type(row.get(key)) is type(prior[key]) and row[key]==prior[key],'known draw differs: '+key)
    need(row['attempt']==3 and row['delay']==51 and row['flags']==0x80000200 and row['target'] is True,'known target')
    return True


def pipeline():
    import pr16_circus_getter_followup as p
    p.OUT=ROOT/'.local/pr16-circus-fairy-lock';p.b.OUT=p.OUT;p.previous.OUT=p.OUT
    return p,p.b,p.c


def validate_lifecycle(raw,stderr,code,prior):
    p,b,c=pipeline()
    from pr16_circus_continuous_probe import owner
    need(code==0 and b'mGBA[' not in stderr,'native process or logger failed')
    result=c.strict(raw.splitlines()[-1]);draws=c.rows(stderr,b'CIRCUS_SUPPRESSION_DRAW ')
    validate_draws(draws,prior['draws'])
    need(not c.rows(stderr,b'CIRCUS_GETTER_ABI ') and not c.rows(stderr,b'CIRCUS_SUPPRESSION_CALL '),'accepted CPU trace replayed')
    inherited=c.validate_calls(prior['natural_calls']);need(inherited['observed'],'inherited suppression absent')
    checks=dict(schema_version=1,case=c.CASE,candidate_sha256=SHA,status='PASS_CIRCUS_SUPPRESSION_LIFECYCLE',
        attempts=1,prefix_wins_reexecuted=0,fresh_cores=2,predicate_returns=0,suppressed_dispatches=0,
        trace_frames=0,trace_instructions=0,save_counter_before=3,save_counter_after=4,
        owner_bytes_verified=64,party_bytes_verified=600,host_write_barriers=7,input_only_after_guard=True,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,warnings_errors=0)
    for key,want in checks.items():need(type(result.get(key)) is type(want) and result[key]==want,'result '+key)
    events=c.rows(stderr,b'CIRCUS_CONTINUOUS ')
    need(sum(e['label']=='resume30' for e in events)==1 and events[0]['label']=='resume30','one genuine Continue')
    need([e['label'] for e in events[-3:]]==['returned','saved','reloaded'],'terminal lifecycle')
    before,returned,saved,loaded=events[0],*events[-3:];baseline=owner(bytes.fromhex(before['owner']))
    need(baseline['current']==baseline['best']==30 and baseline['phase']==0,'Save30 owner')
    need(before['bp']==90 and before['save_counter']==3 and before['count']==1,'Save30 counters')
    actions=[e for e in events if e['label']=='action'];outcomes=[e for e in events if e['label']=='outcome']
    need(1<=len(actions)==len(outcomes)<=3 and actions[0]['flags']==0x80000200,'actual first suppressed battle')
    wins=sum(e['outcome']==1 for e in outcomes);losses=sum(e['outcome']==2 for e in outcomes)
    need(wins+losses==len(outcomes) and losses<=1 and (losses or wins==3),'native outcomes')
    need(all(e['battle']==30+i for i,e in enumerate(actions)),'new battle ordering')
    bp=90+9*(wins//3)
    for e in (returned,saved,loaded):
        own=owner(bytes.fromhex(e['owner']))
        need(own['current']==(0 if losses else 30+wins) and own['best']==30+wins
            and own['phase']==0 and own['identity']==baseline['identity'],'earned owner lost')
        need(e['party']==before['party'] and e['factory']==before['factory'] and e['count']==1
            and e['bp']==bp and not any(e[k] for k in ('flags','newbs','snapshot','marker','pending')),'restoration/cleanup/BP')
    need(returned['owner']==saved['owner']==loaded['owner'] and saved['save_counter']==loaded['save_counter']==4,'Save/Continue64')
    need(all(e['save_counter']==3 for e in events[:-2]),'unexpected Save')
    need(result['new_battles']==len(outcomes) and result['new_wins']==wins and result['new_losses']==losses
        and result['bp_after']==bp and result['total_frames']==loaded['frame'],'result accounting')
    locked=c.rows(stderr,b'CIRCUS_FAIRY_LOCK_SKIP ')
    need(locked and all(x['streak']>=30 and x['flags']&0x4000 and x['types']&0x04000000
        and x['hp']>0 and x['host_writes']==0 and x['forced_switch_untouched'] is True for x in locked),'Fairy Lock input policy absent')
    need(any(e['battle']==31 and e['flags']==0x804000 for e in actions),'original Fairy Lock encounter differs')
    return dict(result=result,fairy_lock=locked,lifecycle_verified=True,inherited_suppression=inherited,
        inherited_run=RUN,inherited_candidate=prior['candidate'],new_cpu_trace_count=0,visual_review_completed=False,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False)


def checkpoint(value,phase):
    import os,subprocess,sys
    from datetime import datetime,timezone
    p,b,c=pipeline();head=b.scope();state=b.resume.validate(ROOT);backlog=b.load(b.resume.BACKLOG)
    row=next(x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(not row.get('complete') and row['success_evidence'] is None,'formal Circus boundary')
    good=value.get('native_verified') is True;rid=int(os.environ['GITHUB_RUN_ID'])
    value.update(recording_run=rid,recording_source_head=head)
    stop=('同一ROMの自然getter30/正規抑制calleeはrun35503514936で確認済み。'
        +'Fairy Lock中の任意交代だけを回避し、通常技・強制交代・自然勝敗を維持。')
    if good:stop+='真正Save30から通常帰還・party600/owner64・Save/fresh Continueまで検証完了。画面/完了Actionsの正式受入照合は未完。'
    elif phase=='FINISH':stop+='未達の原本を保存。'+str(value['failures'])
    else:stop+='新規契約PASS。delay51の一回だけから未完lifecycleを継続する。'
    nxt=('このrunの完了Actions・原本・画面を照合しCircus正式受入を接続する。新native再実行なし。' if good else
         'Fairy Lock followupの現在run/停止原本から最初の未達のみ修復。30勝/旧3抽選/getter・抑制CPU trace/ARMを繰り返さない。')
    state['circus_suppression_lifecycle']=dict(path=REPORT,run_id=rid,candidate=value['candidate'],native_verified=good)
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action']['id']='CIRCUS_SUPPRESSION_RECEIPT' if good else 'CIRCUS_FAIRY_LOCK_LIFECYCLE'
    state['next_action']['read_paths']=[REPORT,PRIOR,*FILES,b.resume.BACKLOG]
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='記録直前remote。scoped nativeは同一46487d98、正式BP/旧30勝candidateは変更しない。'
    state['observed_head_checks']=dict(scope_head=head,runs=value['predecessor_checks'],reason_ja='先行runの完了failure/原本とscoped getter・抑制成功を区別して照合。')
    state['pending_runs']=[dict(run_id=rid,tested_head=value['source_head'],status='in_progress',scope='circus-fairy-lock')]
    state['session_execution_summary']={k:value.get(k,0) for k in ('new_emulator_processes','arm_compiles','arm_links','accepted_standalone_replays','prefix_wins_reexecuted')}
    state['session_execution_summary']['scope_ja']='同一ROM・Save30。未完lifecycleの必要prefixだけ。既観測3抽選/CPU traceは省略。新ROM変更0。'
    note='run35503514936のgetter30/正規抑制は再観測不要。Fairy Lockは0x4000、任意交代を控える。次はlifecycle reportのみ。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    row['lifecycle_checkpoint']=REPORT;row['resume']=nxt
    prefix=f'evidence/pr16_circus_fairy_lock/{rid}/';evidence={}
    for path in sorted((p.OUT/'execution').rglob('*')):
        if not path.is_file() or path.suffix not in ('.json','.c','.h','.stdout','.stderr'):continue
        name=prefix+'execution/'+path.relative_to(p.OUT/'execution').as_posix();raw=path.read_bytes()
        b.write(name,raw);evidence[name]=identity(raw)
    value['text_evidence']=evidence;immutable=prefix+phase.lower()+'.json'
    b.write(REPORT,b.stable(value));b.write(immutable,b.stable(value));b.write(b.resume.BACKLOG,b.stable(backlog))
    for name in (*FILES,REPORT,immutable,*evidence):state['source_bindings'][name]=identity((ROOT/name).read_bytes())
    if b.resume.BACKLOG in state['source_bindings']:state['source_bindings'][b.resume.BACKLOG]=identity((ROOT/b.resume.BACKLOG).read_bytes())
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    for label,args in [('resume',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_resume.py','-v']),('task-graph',[sys.executable,'scripts/validate_task_graph.py'])]:
        _,_,proc=b.capture(args,label+'-'+phase);need(b.exited(proc)==0,label+' failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths=[*FILES,REPORT,immutable,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*evidence,*b.LOGS]
    entry=(f'\n\n## {stamp} — {TASK}-{phase}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        f'- Status: {"DONE" if good else "STOPPED"}（正式Circus/P08は別）\n- Version: pr16-circus-fairy-lock-v1\n'
        '- Summary: '+stop+'\n- Files changed: '+', '.join(paths)+'\n'
        f'- Verify: 新規host契約{value["host_tests"]["tests_run"]}件、resume/task graph/index差分private guard/diff check。旧20 ABI/20field/30勝再実行0。\n'
        '- Commit: 同branch非force commit、remote/receipt一致。\n'
        '- Network: 固定CFRU e24a16fe39e27ae162faf5b78596d1f3df18489d include/constants/battle.h、src/battle_util.c IsFairyLockActive、src/switching.cをGitHubで照合。検索語BATTLE_CIRCUS_FAIRY_LOCK / IsFairyLockActive。host mGBA依存のみ。秘密/ROM/Saveの追加なし。\n'
        '- Next: '+nxt+'\n')
    for name in b.LOGS:
        path=ROOT/name;need(f'{TASK}-{phase}\n' not in path.read_text(),'duplicate phase log')
        with path.open('a') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines());need(changed and changed<=set(paths),'stage scope')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=head,p.OUT,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': '+phase+' 通常交代方針・同一ROM・原本・引継ぎ・両ログ'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    committed=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty after push')
    (p.OUT/('receipt-'+phase+'.json')).write_bytes(b.stable(dict(task=TASK,phase=phase,commit=committed,run_id=rid,non_force_push=True)))
    print('RESULT='+('DONE' if good else 'STOPPED')+' TASK='+TASK+' VERIFY=PASS COMMIT='+committed)


def prepare():
    import io,os,re,subprocess,sys,zipfile
    p,b,c=pipeline();head=b.scope();p.OUT.mkdir(parents=True,exist_ok=True);b.resume.validate(ROOT)
    need(set(b.command('git','diff','--name-only',BASE,head).splitlines())==set(FILES),'unreviewed scope')
    old=b.load(PRIOR);need(old['recording_run']==RUN and old['candidate']['sha256']==SHA and not old['native_verified'],'prior stop')
    run=b.api('actions/runs/'+str(RUN));artifact=b.api('actions/artifacts/10602823295')
    need(run['head_sha']==SOURCE and run['status']=='completed' and run['conclusion']=='failure','prior Actions not complete')
    need(artifact['workflow_run']['id']==RUN and artifact['digest']=='sha256:'+ARCHIVE['sha256'] and not artifact['expired'],'artifact identity')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/10602823295/zip'],cwd=ROOT)
    need(identity(raw)==ARCHIVE,'archive bytes')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        original=c.strict(z.read('native-result.json'))
        for key in ('draws','getter_calls','natural_calls','build','failures'):need(original[key]==old[key],'tracked prior drift')
        err=z.read('execution/'+c.CASE+'.stderr')
        need(b'Circus tactical selected individual did not survive to action' in err,'different native stop')
    need(old['getter_calls'][0]['result']==30 and c.validate_calls(old['natural_calls'])['observed'],'scoped getter/suppression incomplete')
    validate_draws([old['draws'][3]],old['draws'])
    _,err,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],'fairy-contracts')
    need(b.exited(proc)==0 and b'\nOK\n' in err,'new contracts failed');count=int(re.search(rb'Ran (\d+) tests',err)[1])
    value=dict(schema_version=1,task=TASK,source_head=head,candidate=old['candidate'],native_verified=False,failures=[],
        predecessor_checks=[dict(id=RUN,head_sha=SOURCE,status='completed',conclusion='failure')],
        inherited=dict(run_id=RUN,path=PRIOR,archive=ARCHIVE,getter=old['getter_calls'],suppression=old['natural_calls'],draws=old['draws']),
        host_tests=dict(tests_run=count,failures=0,errors=0,skips=0,successful=True),
        new_emulator_processes=0,arm_compiles=0,arm_links=0,accepted_standalone_replays=0,prefix_wins_reexecuted=0,
        rom_changes=0,new_getter_traces=0,new_suppression_traces=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    checkpoint(value,'START')


def native():
    import os,shutil,sys
    p,b,c=pipeline();head=b.scope();value=b.load(REPORT);old=b.load(PRIOR)
    need(value['recording_run']==int(os.environ['GITHUB_RUN_ID']) and value['new_emulator_processes']==0,'already attempted')
    value['native_source_head']=head;work=p.OUT/'work';work.mkdir(parents=True,exist_ok=True);protected={}
    try:
        save=p.CACHE/'normal30.srm';provenance=c.strict((p.CACHE/'provenance.json').read_bytes())
        need(not save.is_symlink(),'cache symlink');value['cache']=p.g.validate_cache(provenance,save.read_bytes(),old['original_failure']['normal_save30'])
        protected[save]=identity(save.read_bytes())
        program="import sys;from pathlib import Path;sys.path.insert(0,'scripts');import pr16_saved_reconstruction as r\ndef offline(event,args):\n if event.startswith('socket.') or event in ('urllib.Request','http.client.connect'):raise RuntimeError('offline reconstruction')\nsys.addaudithook(offline)\nr.reconstruct(Path('.local/pr16-circus-fairy-lock/runtime').resolve())"
        _,err,proc=b.capture([sys.executable,'-c',program],'reconstruct',120);need(b.exited(proc)==0 and not err,'saved-byte reconstruction')
        parent_path=p.OUT/'runtime/candidate.gba';parent=parent_path.read_bytes();need(identity(parent)==old['build']['parent'],'parent identity');protected[parent_path]=identity(parent)
        candidate=bytearray(parent)
        for row in old['build']['patches']:
            at=row['offset'];before=bytes.fromhex(row['before']);after=bytes.fromhex(row['after'])
            need(len(before)==len(after) and bytes(candidate[at:at+len(before)])==before,'saved patch preimage')
            candidate[at:at+len(before)]=after
        candidate=bytes(candidate);need(identity(candidate)==old['candidate'],'same successor ROM identity')
        path=work/'candidate.gba';path.write_bytes(candidate);protected[path]=identity(candidate)
        files={}
        for name,bound in old['generated'].items():
            raw=(ROOT/f'evidence/pr16_circus_getter/{RUN}/execution/generated'/name).read_bytes()
            need(identity(raw)==bound,'generated predecessor drift: '+name);files[name]=raw
        for name,bound in old['original']['host_dependencies'].items():need(identity((ROOT/name).read_bytes())==bound,'host dependency drift')
        files=adapt(files);value['generated']={n:identity(raw) for n,raw in files.items()}
        for name,raw in files.items():
            (work/name).write_bytes(raw);dst=p.OUT/'execution/generated'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
        exe=work/'runner';rel=lambda q:q.relative_to(ROOT).as_posix()
        _,err,proc=b.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+rel(work),rel(work/'controller.c'),'-lmgba','-o',rel(exe)],'compile',120)
        need(b.exited(proc)==0 and not err,'host compile');value['host_compiles']=1;value['executable']=identity(exe.read_bytes())
        value['guard_evidence_reused']=old['guard_evidence_reused']
        for name in value['guard_evidence_reused']:need(b.exited(b.load(name))==1,'inherited guard missing')
        scratch=work/'scratch.srm';shutil.copyfile(save,scratch);shots=p.OUT/'screens';shots.mkdir(exist_ok=True)
        value['new_emulator_processes']=1
        raw,err,proc=b.capture([rel(exe),rel(path),rel(scratch),SHA,p.g.SAVE['sha256'],c.CASE,rel(shots/c.CASE),'resume',rel(save)],c.CASE,1800)
        value['process']=proc
        if proc['spawn_error'] is not None:value['new_emulator_processes']=0
        value['draws']=c.rows(err,b'CIRCUS_SUPPRESSION_DRAW ');value['fairy_lock']=c.rows(err,b'CIRCUS_FAIRY_LOCK_SKIP ')
        value['events']=c.rows(err,b'CIRCUS_CONTINUOUS ')
        if raw.splitlines():value['raw_last_result']=c.strict(raw.splitlines()[-1])
        value['analysis']=validate_lifecycle(raw,err,b.exited(proc),old);value['native_verified']=True
    except Exception as error:value['failures'].append(dict(stage='fairy-lock-lifecycle',type=type(error).__name__,error=str(error)))
    finally:
        for path,bound in protected.items():
            if identity(path.read_bytes())!=bound:value['failures'].append(dict(stage='immutability',error=path.name))
        if value['failures']:value['native_verified']=False
        (p.OUT/'native-result.json').write_bytes(b.stable(value))


def main(command):
    p,b,c=pipeline()
    if command=='prepare':prepare()
    elif command=='native':native()
    elif command=='finish':
        path=p.OUT/'native-result.json';value=c.strict(path.read_bytes()) if path.exists() else b.load(REPORT)
        if not path.exists():value['failures'].append(dict(stage='setup',error='no bootstrap fallback'))
        checkpoint(value,'FINISH')
    elif command=='pack':p.pack()
    elif command=='result':
        value=b.load(REPORT);need(value['native_verified'] and not value['failures'],'lifecycle remains open')
    else:raise ValueError('command required')


if __name__=='__main__':
    import sys
    need(len(sys.argv)==2,'command required');main(sys.argv[1])
