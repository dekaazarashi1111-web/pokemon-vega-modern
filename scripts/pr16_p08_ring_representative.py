#!/usr/bin/env python3
"""共有save/load/battle変更の影響があるRing代表1件だけを最終候補で検証する。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import importlib.util
import io
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_circus_battle25 as b
import pr16_p08_impact as impact
s=impact.saved;need=s.need
TASK='USER-20260920-P08-RING'
BASE='dae8c14ea2180abefb8ce5a0d6483ca724d711ed'
SELF='scripts/pr16_p08_ring_representative.py'
TEST='tests/test_pr16_p08_ring_representative.py'
WORKFLOW='.github/workflows/pr16-p08-ring.yml'
FILES=(SELF,TEST,WORKFLOW)
REPORT='content/modernization/pr16_p08_ring_representative.json'
IMPACT='content/modernization/pr16_p08_candidate_impact.json'
OLD='content/modernization/pr16_ring_policy_acceptance.json'
GIFT='content/modernization/pr16_ring_npc_gift_checkpoint_20260918.json'
SOURCE='tools/mgba_pr16_ring_policy.c'
VALIDATOR='scripts/pr16_ring_policy_native.py'
ORIGINAL_HEAD='a54fe471c666c280f116b5cbfc3b1a6c821e5395'
ORIGINAL_RUN=35347587112
ORIGINAL_ARTIFACT=10547413771
ARCHIVE=dict(size=656588,sha256='113b5972602453eafdab47f57272f1d9fd0ab22d1efcd4d956651b2f84ad0f65')
OLD_SHA='4ea33fb8224b0b84493ccca6e90161da245705eb1eb0a3874691ab39cc3806cc'
CASE='ring-active'
HEADER='pr16_ring_policy_generated.h'
OUT=ROOT/'.local/pr16-p08-ring'


def validator():
    spec=importlib.util.spec_from_file_location('p08_ring_context_only',ROOT/VALIDATOR)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(module.SHA==OLD_SHA,'original validator identity context changed')
    module.SHA=impact.TARGET['sha256']
    return module


def adapt_header(raw):
    expected=('/* 固定候補のNPCと歩行経路。Ring/NEXTのfixtureなし。 */\n#define RP_SHA "'+OLD_SHA+'"\n'
        '#define RP_GROUP 96U\n#define RP_MAP 17U\n#define RP_LOCAL_ID 4U\n#define RP_X 12U\n'
        '#define RP_Y 39U\n#define RP_ORDINARY_ACTIVE_FLAGS 4U\n').encode()
    need(raw==expected,'unexpected original Ring header')
    return raw.replace(OLD_SHA.encode(),impact.TARGET['sha256'].encode(),1)


def validate_result(raw,stderr,process,audit):
    need(type(process.get('returncode')) is int and process['returncode']==0
         and process['timed_out'] is False and process['spawn_error'] is None,'new native process failed')
    need(audit['candidate']==impact.TARGET,'oracle candidate differs')
    row=validator().validate(s.strict(raw),stderr,CASE,audit)
    need(row['case']==CASE and row['fresh_cores']==3 and row['host_write_barriers']==7
         and row['manual_saves']==2,'representative native scope differs')
    return row


def source_check(native):
    bindings={}
    for path,expected in native['sources'].items():
        raw=s.safe(ROOT,path).read_bytes();need(s.identity(raw)==expected,'original source drift: '+path)
        bindings[path]=expected
    return bindings


def original():
    run=b.api('actions/runs/'+str(ORIGINAL_RUN));art=b.api('actions/artifacts/'+str(ORIGINAL_ARTIFACT))
    need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==ORIGINAL_HEAD,'old Ring Actions differs')
    need(not art['expired'] and art['workflow_run']['id']==ORIGINAL_RUN
         and art['digest']=='sha256:'+ARCHIVE['sha256'],'old Ring artifact differs')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ORIGINAL_ARTIFACT)+'/zip'],cwd=ROOT)
    need(s.identity(raw)==ARCHIVE,'old archive identity')
    dest=OUT/'original';dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist())==len(set(z.namelist())) and sum(x.file_size for x in z.infolist())<16*1024*1024,'invalid source archive')
        prefix='pr16-ring-policy-native/'
        data=z.read(prefix+'result.json');native=s.strict(data)
        need(native==b.load(OLD)['native'],'tracked Ring native differs from original')
        (dest/'native.json').write_bytes(data)
        bindings=source_check(native)
        for name,expected in native['generated'].items():
            need(Path(name).name==name and Path(name).suffix in ('.c','.h'),'unexpected generated member')
            data=z.read(prefix+'generated/'+name);need(s.identity(data)==expected,'generated binding differs')
            data.decode('utf-8');need(b'\0' not in data,'nontext generated member')
            (dest/name).write_bytes(data)
        guards={}
        for guard in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
            proc=s.strict(z.read(prefix+'guard-'+guard+'.process.json'))
            err=z.read(prefix+'guard-'+guard+'.stderr');out=z.read(prefix+'guard-'+guard+'.stdout')
            need(b.exited(proc)==1 and out==b'' and err==b'P03 archive: host write after observation barrier\n','old guard failed')
            guards[guard]=dict(process=proc,stderr=s.identity(err),stdout=s.identity(out))
    return dict(run_id=ORIGINAL_RUN,head_sha=ORIGINAL_HEAD,artifact_id=ORIGINAL_ARTIFACT,archive=ARCHIVE,
                sources=bindings,generated=native['generated'],guards=guards,
                exact_original_preserved=True,old_case_count=len(native['results']),old_cases_reexecuted=0)


def protected():
    return {p:s.identity(s.safe(ROOT,p).read_bytes()) for p in (OLD,GIFT,IMPACT,impact.NORMAL,impact.GETTER,'config/active_play_baseline.json')}


def checkpoint(value,phase):
    head=b.scope();state=b.resume.validate(ROOT);backlog=b.load(b.resume.BACKLOG)
    need(protected()==value['protected_originals'],'protected input changed')
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['phase']=phase
    prefix='evidence/pr16_p08_ring/'+str(value['recording_run'])+'/'+phase.lower()+'/'
    b.write(REPORT,b.stable(value));evidence=[]
    def save(name,data):
        path=prefix+name;b.write(path,data);evidence.append(path)
    save('result.json',b.stable(value))
    if phase=='FINISH':
        for src in sorted((OUT/'execution').glob('*')):
            if src.suffix in ('.json','.stdout','.stderr'):save('execution/'+src.name,src.read_bytes())
    good=value['native_verified']
    stop=('P08 Ring代表1件を46487d98で実行し、自然遭遇・Mega・PP消費・通常帰還・Save/fresh Continueの原本を保存。'
          '新native1/3fresh cores。完了Actionsと画面照合までは正式受入しない。' if good else
          'P08 Ring代表1件の新候補限定検証。開始/実停止を記録し、未観測・失敗を受入済みとしない。')
    nxt=('このP08 Ring runの完了Actions・原本と画面を照合し、P08_RING_ORDINARYの代表境界だけを閉じる。'
         '同じnativeを再実行せず、残るBP/P03保存/Circus退出後通常戦闘へ進む。' if good else
         'このP08 Ring runの完了原本を先に読む。native未実行なら同じ記録runのnative/finishへ。失敗なら停止点だけを修正し、受入済みの旧5case/30勝は再実行しない。')
    state['p08_ring_representative']=dict(path=REPORT,phase=phase,run_id=value['recording_run'],
        candidate=impact.TARGET,native_verified=good,representative_accepted=False)
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action'].update(id='P08_RING_REPRESENTATIVE_REVIEW' if good else 'P08_RING_REPRESENTATIVE_NATIVE',
        read_paths=[REPORT,SELF,IMPACT,OLD,b.resume.BACKLOG],stop_rule_ja=nxt)
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='P08 Ringの'+phase+'記録直前remote。native原本と正式受入は別境界。'
    state['pending_runs']=[dict(run_id=value['recording_run'],tested_head=value['workflow_source_head'],status='in_progress')]
    state['observed_head_checks']=dict(scope_head=head,run_id=value['recording_run'],
        verified_prior_run=35507102023,prior_conclusion='success',reason_ja='P08全ROM監査は完了success。本runは完了後に別途照合。')
    state['session_execution_summary']=dict(new_emulator_processes=value['new_emulator_processes'],
        arm_compiles=0,arm_links=0,accepted_standalone_replays=0,prefix_wins_reexecuted=0,
        scope_ja='保存byte候補の変更影響があるRing代表1件だけ。未影響caseの再実行0。')
    final=next(r for r in backlog['remaining_conditions'] if r['id']=='FINAL_NATIVE_ACCEPTANCE')
    final['ring_representative_evidence']=REPORT;final['resume']=nxt
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    b.write(b.resume.BACKLOG,b.stable(backlog))
    for path in (*FILES,REPORT,*evidence,b.resume.BACKLOG):state['source_bindings'][path]=s.identity((ROOT/path).read_bytes())
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    _,_,proc=b.capture([sys.executable,'scripts/validate_task_graph.py'],'task-graph-'+phase)
    need(b.exited(proc)==0,'task graph failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths=[REPORT,*evidence,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*b.LOGS]
    entry=(f'\n\n## {stamp} — {TASK}-{phase}\n- Timestamp: {stamp}\n- Task: {TASK}-{phase}\n'
           '- Status: '+('DONE（native原本保存、正式受入は別照合）' if good else 'IN_PROGRESS（未観測/実停止を保存）')+'\n'
           '- Version: pr16-p08-ring-v1\n- Summary: '+stop+'\n- Files changed: '+', '.join((*FILES,*paths))+'\n'
           '- Verify: 新規context契約・resume/MD/hash・task graph。保存byte候補identity、元25source/10generated/7guard継承。実行結果は'+REPORT+'。\n'
           '- Boundary: 新native='+str(value['new_emulator_processes'])+'、ARM0、旧30勝0。旧受入原本・P08影響台帳・active baseline不変。\n'
           '- Commit: 同branch非force commit/pushとremote読戻し。\n'
           '- Network: GitHub完了Actions/固定Ring artifactとhead照合、host mGBA依存のみ。旧ARM/全case buildは実行しない。\n- Next: '+nxt+'\n')
    for name in b.LOGS:
        need('— '+TASK+'-'+phase not in (ROOT/name).read_text(),'duplicate checkpoint')
        with (ROOT/name).open('a') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines())
    need(changed and changed<=set(paths),'staged scope')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=head,OUT,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': '+phase+' 新候補Ring代表1件・共有hook影響の原本保存'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    commit=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty after push')
    (OUT/('receipt-'+phase+'.json')).write_bytes(b.stable(dict(task=TASK,phase=phase,commit=commit,run_id=value['recording_run'],non_force_push=True)))
    print('RESULT='+('DONE' if good else phase)+' TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


def prepare():
    head=b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted; inspect saved original')
    need(set(b.command('git','diff','--name-only',BASE,head).splitlines())==set(FILES),'unreviewed source delta')
    prior=b.api('actions/runs/35507102023')
    need(prior['status']=='completed' and prior['conclusion']=='success' and prior['head_sha']=='29202a863b14da9956c1e3b0b306b56ba3f77dc4','P08 impact Actions incomplete')
    report=impact.checked(ROOT,IMPACT,dict(size=739897,sha256='9aeab30775211ba995a3d6dd589d697f70ed966bb34719aa1ea5e86548799142'))
    need(report['candidate']==impact.TARGET and report['full_rom_sparse_comparison'] and report['candidate_impacts']['RING']['changed_bytes']==11071,'Ring impact scope')
    original_info=original()
    _,_,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],'new-context-tests')
    need(b.exited(proc)==0,'new context tests failed')
    value=dict(schema_version=1,task=TASK,source_head=head,workflow_source_head=os.environ['GITHUB_SHA'],
        candidate=impact.TARGET,case=CASE,original=original_info,protected_originals=protected(),
        source_bindings={p:s.identity((ROOT/p).read_bytes()) for p in (*FILES,VALIDATOR,impact.SELF)},
        native_verified=False,representative_accepted=False,visual_review_completed=False,
        new_emulator_processes=0,host_compiles=0,fresh_cores=0,arm_compiles=0,arm_links=0,
        accepted_standalone_replays=0,prefix_wins_reexecuted=0,rom_changes=0,release_ready=False,failures=[])
    (OUT/'native-result.json').write_bytes(b.stable(value));checkpoint(value,'START')


def native():
    b.scope();b.resume.validate(ROOT);value=b.load(REPORT)
    need(value['new_emulator_processes']==0 and value['recording_run']==int(os.environ['GITHUB_RUN_ID']),'already attempted')
    work=OUT/'work';work.mkdir(parents=True,exist_ok=True)
    try:
        # 既に受入した監査を繰り返さず、同じ固定byteの入力materializationだけを行う。
        code="""from pathlib import Path
import sys
sys.path.insert(0,'scripts')
import pr16_p08_impact as m
sys.addaudithook(m.offline)
raw=m.saved.safe(m.ROOT,m.ANCHOR_PATH).read_bytes()
m.need(m.saved.identity(raw)==m.ANCHOR,'anchor differs')
for recipe in m.load_model(m.ROOT):
 m.need(m.saved.identity(raw)==recipe['parent'],'materialization parent')
 raw=m.saved.patch(raw,recipe['patches'])
 m.need(m.saved.identity(raw)==recipe['candidate'],'materialization candidate')
m.need(m.saved.identity(raw)==m.TARGET,'final input')
Path('.local/pr16-p08-ring/work/candidate.gba').write_bytes(raw)
print(m.saved.stable(m.saved.identity(raw)).decode())
"""
        _,_,proc=b.capture([sys.executable,'-c',code],'materialize',120);need(b.exited(proc)==0,'candidate materialization failed')
        candidate=work/'candidate.gba';raw=candidate.read_bytes();need(s.identity(raw)==impact.TARGET,'candidate differs')
        seed=s.safe(ROOT,b.SEED);seed_raw=seed.read_bytes();need(s.identity(seed_raw)['sha256']==b.SEED_SHA,'pinned seed differs')
        source_check(b.load(OLD)['native'])
        v=validator();audit=v.current_route(raw,b.load(GIFT)['builder'])
        old=b.load(OLD)['native'];expected=copy.deepcopy(old['oracle']);expected['candidate']=impact.TARGET
        flag=expected.pop('flag_contract');need(audit==expected,'candidate route/grass changed')
        audit['flag_contract']=flag;value['oracle']=audit
        generated={}
        for name,expected in value['original']['generated'].items():
            data=(OUT/'original'/name).read_bytes();need(s.identity(data)==expected,'saved generated bytes changed')
            if name==HEADER:data=adapt_header(data)
            (work/name).write_bytes(data);generated[name]=s.identity(data)
        value['generated']=generated
        exe=work/'runner';deps=work/'deps.d'
        _,err,proc=b.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),
                            '-MMD','-MF',str(deps),str(ROOT/SOURCE),'-lmgba','-o',str(exe)],'compile',120)
        need(b.exited(proc)==0 and err==b'','host controller compile failed');value['host_compiles']=1
        # compilerが実際に読んだtransitive textを旧成功headと突合する。未知includeを継承しない。
        files=shlex.split(deps.read_text().replace('\\\n',' ').split(':',1)[1]);depbindings={}
        for text in files:
            path=Path(text);path=path if path.is_absolute() else ROOT/path
            need(not any(p.is_symlink() for p in (path,*path.parents)),'symlink compiled input')
            path=path.resolve()
            if path.parent==work:
                need(path.name in generated and s.identity(path.read_bytes())==generated[path.name],'unbound generated include')
            else:
                name=path.relative_to(ROOT).as_posix();current=s.safe(ROOT,name).read_bytes()
                prior=subprocess.check_output(['git','show',ORIGINAL_HEAD+':'+name],cwd=ROOT)
                need(current==prior,'transitive controller source drift: '+name)
                depbindings[name]=s.identity(current)
        value['transitive_compiled_sources']=depbindings;value['executable']=s.identity(exe.read_bytes())
        scratch=work/'private.srm';scratch.write_bytes(seed_raw)
        shots=OUT/'screens';shots.mkdir(exist_ok=True)
        value['new_emulator_processes']=1
        (OUT/'native-result.json').write_bytes(b.stable(value))
        raw,err,proc=b.capture([str(exe),str(candidate),str(scratch),impact.TARGET['sha256'],b.SEED_SHA,CASE,str(shots/CASE)],CASE,600)
        value['process']=proc;row=validate_result(raw,err,proc,audit)
        need(candidate.read_bytes() and s.identity(candidate.read_bytes())==impact.TARGET and seed.read_bytes()==seed_raw,'original input changed')
        need(protected()==value['protected_originals'],'accepted original changed')
        value.update(native_verified=True,native_result=row,fresh_cores=row['fresh_cores'],failures=[])
    except Exception as error:
        value['failures'].append(dict(type=type(error).__name__,message=str(error)));raise
    finally:
        value['screens']={p.name:s.identity(p.read_bytes()) for p in sorted((OUT/'screens').glob('*.ppm'))}
        (OUT/'native-result.json').write_bytes(b.stable(value))


def finish():
    value=s.strict((OUT/'native-result.json').read_bytes())
    if not value['native_verified'] and not value['failures']:
        value['failures'].append(dict(type='WorkflowStopped',message='native step did not complete; see Actions'))
    checkpoint(value,'FINISH')


def pack():
    dst=OUT/'artifact';dst.mkdir(parents=True,exist_ok=True)
    for src in sorted(OUT.rglob('*')):
        if not src.is_file() or dst in src.parents or (OUT/'work') in src.parents or (OUT/'original') in src.parents:continue
        if src.suffix not in ('.json','.stdout','.stderr','.txt','.ppm'):continue
        raw=src.read_bytes()
        if src.suffix=='.ppm':
            magic,size,maximum,pixels=raw.split(b'\n',3)
            need((magic,size,maximum)==(b'P6',b'240 160',b'255') and len(pixels)==115200,'unexpected pixels')
        else:raw.decode();need(b'\0' not in raw,'nontext artifact')
        target=dst/src.relative_to(OUT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    for name in FILES:
        target=dst/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');b.OUT=OUT
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='native':native()
    elif sys.argv[1]=='finish':finish()
    elif sys.argv[1]=='pack':pack()
    elif sys.argv[1]=='result':need(b.load(REPORT)['native_verified'],'native failed; original retained')
    else:raise ValueError('unknown command')
