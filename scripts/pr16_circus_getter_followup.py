#!/usr/bin/env python3
"""r3中継の限定修復→真正Save30 cache→抑制。各境界を非force記録する。"""
from __future__ import annotations
from datetime import datetime, timezone
import copy
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_circus_suppression as previous
import pr16_circus_getter_abi as g

b,c=previous.b,previous.c
ROOT=b.ROOT
OUT=ROOT/'.local/pr16-circus-getter'
CACHE=ROOT/'.local/pr16-circus-suppression/resume'
TASK='USER-20260920-CIRCUS-GETTER-ABI'
REPORT='content/modernization/pr16_circus_getter_followup.json'
PRIOR='content/modernization/pr16_circus_suppression.json'
FILES=('scripts/pr16_circus_getter_abi.py','scripts/pr16_circus_getter_followup.py',
       'tools/mgba_pr16_circus_getter_trace.h','tests/test_pr16_circus_getter_abi.py',
       '.github/workflows/pr16-circus-getter.yml')
RUN,JOB,ARTIFACT=35494023398,106033721719,10600576182
ARCHIVE=dict(size=2635482,sha256='b6eac53c9e54381fcdc66773cda12f60a522b67b65e9273332f94ba106ce2e03')
SOURCE='bacc3089488b2f67d6bc848140c6e8239de86d60'
START_HEAD='8628153d6a9463ef43eab41fc0e6309c8dba88be'
b.OUT=OUT;previous.OUT=OUT
need=g.need


def tests():
    raw,err,p=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_circus_getter_abi.py','-v'],'abi-contracts')
    need(b.exited(p)==0 and b'Ran 16 tests' in err and b'\nOK\n' in err,'new ABI contracts')
    return dict(tests_run=16,failures=0,errors=0,skips=0,successful=True)


def original_failure():
    old=b.load(PRIOR)
    run,job,artifact=b.api('actions/runs/'+str(RUN)),b.api('actions/jobs/'+str(JOB)),b.api('actions/artifacts/'+str(ARTIFACT))
    need(run['head_sha']==SOURCE and run['status']=='completed' and run['conclusion']=='failure','original run identity')
    need(job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='failure','original job identity')
    need(artifact['workflow_run']['id']==RUN and artifact['workflow_run']['head_sha']==SOURCE
         and not artifact['expired'] and artifact['digest']=='sha256:'+ARCHIVE['sha256'],'original artifact identity')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    need(b.identity(raw)==ARCHIVE,'original archive bytes')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist())==len(set(z.namelist())),'duplicate archive member')
        native=c.strict(z.read('native-result.json'))
        for key in ('candidate','process','draws','normal_save30','failures'):
            need(native[key]==old[key],'tracked original changed: '+key)
        need(b.exited(native['process'])==1 and not native['natural_calls'],'original stop changed')
        stderr=z.read('execution/'+c.CASE+'.stderr')
        need(b'mGBA[' not in stderr and c.rows(stderr,b'CIRCUS_SUPPRESSION_DRAW ')==native['draws'],'original draws/logs')
        need(c.rows(stderr,b'CIRCUS_SUPPRESSION_BOUND ')==[dict(attempts=64,suppression_accepted=False,normal_save30_preserved=True)],'actual stop is not draw bound')
    return dict(run_id=RUN,job_id=JOB,artifact_id=ARTIFACT,head_sha=SOURCE,
                status='completed',conclusion='failure',archive=ARCHIVE,
                diagnostic=g.diagnose_draws(old['draws']),normal_save30=old['normal_save30'])


def checkpoint(value,phase):
    head=b.scope();state=b.resume.validate(ROOT);backlog=b.load(b.resume.BACKLOG)
    need(state['latest_native_run']==34946969126 and not state['release_ready'],'formal BP/release boundary')
    row=next(x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(row['success_evidence'] is None and not row.get('complete'),'formal Circus already closed')
    rid=int(os.environ['GITHUB_RUN_ID']);value.update(recording_run=rid,recording_source_head=head)
    good=value.get('native_verified') is True
    if good:
        stop='５引数保持中継の新scoped候補で、真正Save30 cacheから自然getter30・正規抑制抽選/自然callee・勝敗帰還・通常Save/fresh Continueを検証。旧30勝原本は旧候補のまま。完了Actionsと画面の受入照合は未完。'
        nxt='getter followupの完了Actions/原本/画面を照合しCircus正式physical受入を整理する。新native/旧30勝/ARMの重複実行をしない。'
    elif phase=='START':
        stop='旧64抽選は全件単一global effectで打切り。getter中継が第４引数r3を破壊する不具合を５引数保持veneerで修復し、16契約を検証。真正Save30 cacheからだけ継続する。'
        nxt='進行中のgetter followup runを確認。cache欠落時も30勝bootstrapへfallbackせず、最初の未達だけ修復する。'
    else:
        stop='getter限定修復の実証と停止原本を記録。受入済み30勝/BPは不変。未観測を成功へ昇格しない。'+str(value.get('failures',[]))
        nxt='pr16_circus_getter_followup.jsonの最初の未達のみ修復する。真正Save30は固定cacheを使用し、30戦prefix/旧builder/ARM再compileを禁止。'
    state['circus_getter_followup']=dict(path=REPORT,run_id=rid,classification=value['classification'],candidate=value.get('candidate',g.PARENT))
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action']['id']='CIRCUS_GETTER_RECEIPT' if good else 'CIRCUS_GETTER_ABI_NATIVE'
    state['next_action']['read_paths']=[REPORT,*FILES,PRIOR,'content/modernization/pr16_circus_battle30_receipt.json',b.resume.BACKLOG]
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='この記録直前のremote HEAD。実native source/candidateはgetter report。旧候補の30勝を新候補の30勝へ読み替えない。'
    state['observed_head_checks']=dict(scope_head=head,runs=[dict(id=RUN,head_sha=SOURCE,status='completed',conclusion='failure')],reason_ja='旧suppressionの失敗をAPI/原本照合。今回Actionsの完了/全CI greenはこの記録時点では未主張。')
    state['pending_runs']=[dict(run_id=rid,tested_head=value['source_head'],status='in_progress',scope='circus-getter-abi')]
    state['session_execution_summary']={k:value.get(k,0) for k in ('new_emulator_processes','arm_compiles','arm_links','accepted_standalone_replays','prefix_wins_reexecuted')}
    state['session_execution_summary']['scope_ja']='真正Save30 cache限定。旧受入native/旧ARM再compile0。限定Thumb中継とBLのみ新候補へ適用。'
    note='getter followupの先行runを先に照合。真正Save30 cache以外から再開しない。30勝prefix/旧builder/ARM再compile/旧64抽選の反復禁止。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    row['getter_checkpoint']=REPORT;row['resume']=nxt
    prefix=f'evidence/pr16_circus_getter/{rid}/';evidence={}
    for path in sorted((OUT/'execution').rglob('*')):
        if not path.is_file() or path.suffix not in ('.json','.c','.h','.stdout','.stderr'):continue
        name=prefix+'execution/'+path.relative_to(OUT/'execution').as_posix()
        data=path.read_bytes();b.write(name,data);evidence[name]=b.identity(data)
    value['text_evidence']=evidence
    immutable=prefix+phase.lower()+'.json'
    b.write(REPORT,b.stable(value));b.write(immutable,b.stable(value));b.write(b.resume.BACKLOG,b.stable(backlog))
    for name in (*FILES,REPORT,immutable,*evidence):state['source_bindings'][name]=b.identity((ROOT/name).read_bytes())
    if b.resume.BACKLOG in state['source_bindings']:state['source_bindings'][b.resume.BACKLOG]=b.identity((ROOT/b.resume.BACKLOG).read_bytes())
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    for label,args in [('resume',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_resume.py','-v']),('task-graph',[sys.executable,'scripts/validate_task_graph.py'])]:
        raw,err,proc=b.capture(args,label+'-'+phase);need(b.exited(proc)==0,label+' failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths=[REPORT,immutable,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*evidence,*b.LOGS]
    entry=(f'\n\n## {stamp} — {TASK}-{phase}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        f'- Status: {"DONE" if good else "STOPPED"}（正式Circus受入/P08は未完）\n- Version: pr16-circus-getter-abi-v1\n'
        '- Summary: '+stop+'\n- Files changed: '+', '.join((*FILES,*paths))+'\n'
        '- Verify: 新規ABI16契約、固定resume、task graph、index差分private guard、diff check。実native/ROM/trace結果はreport原本に分離。\n'
        '- Commit: この記録を含む同branch非force commit。自己SHAはremote/receipt。\n'
        '- Network: GitHub固定Actions原本。固定CFRU e24a16feのsrc/frontier.c（GetCurrentBattleTowerStreak/LoadBattleCircusEffects）とsource-lockを照合。検索語sp072_LoadBattleCircusEffects。host mGBA依存のみ導入。ROM/save/private入力はGit/artifactへ追加しない。\n'
        '- Next: '+nxt+'\n')
    for name in b.LOGS:
        path=ROOT/name;need(f'{TASK}-{phase}\n' not in path.read_text(),'duplicate checkpoint log')
        with path.open('a') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines());need(changed and changed<=set(paths),'unexpected staged paths')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=head,OUT,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': '+phase+' ５引数中継・真正cache・原本・固定引継ぎ・両ログ'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    committed=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty after push')
    (OUT/('receipt-'+phase+'.json')).write_bytes(b.stable(dict(task=TASK,phase=phase,commit=committed,source_head=head,run_id=rid,non_force_push=True)))
    print('RESULT='+('DONE' if good else 'STOPPED')+' TASK='+TASK+' VERIFY=PASS COMMIT='+committed)


def prepare():
    head=b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'existing getter attempt: inspect first, never replay')
    subprocess.run(['git','merge-base','--is-ancestor',START_HEAD,head],cwd=ROOT,check=True)
    value=dict(schema_version=1,task=TASK,classification='CIRCUS_GETTER_ABI_IMPLEMENTED_NATIVE_OPEN',
        source_head=head,original_failure=original_failure(),original=previous.original(),host_tests=tests(),
        sources={p:b.identity((ROOT/p).read_bytes()) for p in FILES},candidate=g.PARENT,
        new_emulator_processes=0,arm_compiles=0,arm_links=0,accepted_standalone_replays=0,prefix_wins_reexecuted=0,
        rom_changes=0,native_verified=False,physical_admission_accepted=False,suppression_accepted=False,
        release_ready=False,visual_review_completed=False,failures=[])
    checkpoint(value,'START')


def build(parent,meta):
    from pr16_bp_party_retention_successor import existing_requests
    from tools.rom_allocator import build_allocation_report_from_csv
    allocation=meta['allocation'];old=g.old_veneer(parent,allocation)
    need(old['target']&0xffff not in (3,0xffff),'old target did not corrupt size condition')
    requests=existing_requests(allocation)
    for row in allocation['allocations']:
        need(b.identity(parent[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'parent owner hash')
    request=dict(name='pr16_circus_getter_preserve_r3',region='integration_modules',size=16,alignment=4,
                 owner=TASK,purpose='Circus getter five-argument preserving Thumb tail call',content_sha256='0'*64)
    preview=build_allocation_report_from_csv(ROOT/'config/rom_regions.csv',requests+[request])
    at=next(r['start'] for r in preview['allocations'] if r['name']==request['name'])
    new,changes=g.patch(parent,old,g.BASE+at)
    need(new==g.patch(parent,old,g.BASE+at)[0],'independent byte assembly')
    request.update(start=at,content_sha256=b.identity(new[at:at+16])['sha256'])
    # The BL belongs to the CFRU allocation; update only the owner actually containing it.
    touched=[]
    for row,req in zip(allocation['allocations'],requests):
        left,right=row['start'],row['end_exclusive']
        if new[left:right]!=parent[left:right]:
            need(left<=g.CALL-g.BASE<right,'unrelated prior allocation changed')
            req['content_sha256']=b.identity(new[left:right])['sha256'];touched.append(row['name'])
    final=build_allocation_report_from_csv(ROOT/'config/rom_regions.csv',requests+[request])
    need(final['summaries']['overlap_count']==0,'allocation overlap')
    for row in final['allocations']:
        need(b.identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'final allocation hash')
    return new,dict(parent=g.PARENT,candidate=b.identity(new),old_veneer=old,new_veneer=dict(address=g.BASE+at,bytes=new[at:at+16].hex()),
        patches=changes,allocation=final,changed_prior_allocations=touched,whole_rom_rollback_matches_parent=True,
        save_layout_changed=False,old_getter_runtime_unchanged=True,old_veneer_unchanged=True,
        arm_compiles=0,arm_links=0,accepted_30_relabelled=False)


def host_sources(value,rom):
    files={}
    for name,bound in value['original']['generated'].items():
        data=(OUT/'input/generated'/name).read_bytes();need(b.identity(data)==bound,'original generated source: '+name);files[name]=data
    files=c.adapt(files)
    control=files['controller.c'].decode()
    old='#include "mgba_pr16_circus_suppression.h"'
    need(control.count(old)==1,'suppression include')
    control=control.replace(old,'#include "mgba_pr16_circus_getter_trace.h"\n#include "getter_suppression.h"')
    anchor='#define SC_OWNER 0x0203DB00U'
    need(control.count(anchor)==1,'getter prototype location')
    control=control.replace(anchor,'static void cg_begin(struct mCore *c);\nstatic void cg_end(struct mCore *c);\n'+anchor)
    before='sc_event(c,"confirmation",sc_base+battle);sc_frozen(c);'
    need(control.count(before)==1,'confirmation trace boundary');control=control.replace(before,before+'cg_begin(c);')
    before='sc_frozen(c);sc_event(c,"action",sc_base+battle);++sc_battles;'
    need(control.count(before)==1,'action trace boundary');control=control.replace(before,'cg_end(c);'+before)
    files['controller.c']=control.encode()
    header=(ROOT/'tools/mgba_pr16_circus_suppression.h').read_text()
    before='    if(bootstrap){\n        char *prefix[7]={argv[0],argv[1],argv[2],argv[3],argv[4],"circus-continuous-30-save",argv[6]};\n        a_require(ss_prefix_main(7,prefix)==0 && sc_wins==30U && !sc_losses && sc_events==143U,"genuine prefix30 incomplete");\n        ss_copy(argv[2],argv[8]);ss_fresh_cores=2U;\n    }'
    need(header.count(before)==1,'bootstrap removal boundary')
    header=header.replace(before,'    a_require(!bootstrap,"getter successor forbids 30-win bootstrap");')
    # N_SHA is inherited through the legacy includes. Only this new main uses the successor identity.
    header='#undef N_SHA\n#define N_SHA "'+value['candidate']['sha256']+'"\n'+header
    files['getter_suppression.h']=header.encode()
    new=value['build']['new_veneer'];target=value['build']['old_veneer']['target']
    files['cg_addresses.h']=f'#define CG_TARGET 0x{target:08x}U\n#define CG_VENEER 0x{new["address"]:08x}U\n'.encode()
    c.SHA=value['candidate']['sha256']
    dispatchers=c.routes(rom,b.load('config/modernization_p05_stage77_suppression.json'))
    need(dispatchers==b.load(PRIOR)['dispatchers'],'unrelated Stage77 dispatchers changed')
    files['ss_routes.h']=c.route_header(dispatchers)
    return files


def native():
    head=b.scope();value=b.load(REPORT)
    need(value['recording_run']==int(os.environ['GITHUB_RUN_ID']) and value['new_emulator_processes']==0,'native already attempted')
    value['native_source_head']=head;protected={}
    work=OUT/'work';work.mkdir(parents=True,exist_ok=True)
    try:
        save=CACHE/'normal30.srm';provenance=c.strict((CACHE/'provenance.json').read_bytes())
        need(not save.is_symlink(),'cache symlink')
        value['cache']=g.validate_cache(provenance,save.read_bytes(),value['original_failure']['normal_save30'])
        protected[save]=b.identity(save.read_bytes())
        program="import sys,json;from pathlib import Path;sys.path.insert(0,'scripts');import pr16_saved_reconstruction as r\ndef offline(event,args):\n if event.startswith('socket.') or event in ('urllib.Request','http.client.connect'):raise RuntimeError('offline reconstruction')\nsys.addaudithook(offline)\nprint(json.dumps(r.reconstruct(Path('.local/pr16-circus-getter/runtime').resolve())))"
        raw,err,proc=b.capture([sys.executable,'-c',program],'reconstruct',120)
        need(b.exited(proc)==0 and not err,'saved-byte reconstruction')
        value['reconstruction']=c.strict(raw)
        parent_path=OUT/'runtime/candidate.gba';parent=parent_path.read_bytes();protected[parent_path]=b.identity(parent)
        candidate,proof=build(parent,c.strict((OUT/'runtime/report.json').read_bytes()))
        value['build']=proof;value['candidate']=proof['candidate'];value['rom_changes']=1
        path=work/'candidate.gba';path.write_bytes(candidate);protected[path]=b.identity(candidate)
        for name,bound in value['original']['host_dependencies'].items():
            need(b.identity((ROOT/name).read_bytes())==bound,'host dependency drift: '+name)
        files=host_sources(value,candidate)
        value['generated']={n:b.identity(raw) for n,raw in files.items()}
        for name,raw in files.items():
            (work/name).write_bytes(raw)
            dst=OUT/'execution/generated'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
        (OUT/'execution/build.json').write_bytes(b.stable(proof))
        exe=work/'runner';rel=lambda p:p.relative_to(ROOT).as_posix()
        raw,err,proc=b.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+rel(work),rel(work/'controller.c'),'-lmgba','-o',rel(exe)],'compile',120)
        need(b.exited(proc)==0 and not err,'host controller compile')
        value['host_compiles']=1;value['executable']=b.identity(exe.read_bytes())
        value['guard_evidence_reused']=[b.OLD+'guard-'+x+'.process.json' for x in ('bus8','bus16','bus32','raw8','raw16','raw32','register')]
        for name in value['guard_evidence_reused']:need(b.exited(b.load(name))==1,'inherited guard missing')
        scratch=work/'scratch.srm';shutil.copyfile(save,scratch)
        shots=OUT/'screens';shots.mkdir(exist_ok=True)
        value['new_emulator_processes']=1
        raw,err,proc=b.capture([rel(exe),rel(path),rel(scratch),value['candidate']['sha256'],g.SAVE['sha256'],c.CASE,rel(shots/c.CASE),'resume',rel(save)],c.CASE,1800)
        value['process']=proc
        if proc['spawn_error'] is not None:value['new_emulator_processes']=0
        value['draws']=c.rows(err,b'CIRCUS_SUPPRESSION_DRAW ')
        value['natural_calls']=c.rows(err,b'CIRCUS_SUPPRESSION_CALL ')
        value['getter_calls']=c.rows(err,b'CIRCUS_GETTER_ABI ')
        if raw.splitlines():value['raw_last_result']=c.strict(raw.splitlines()[-1])
        checkpoints=c.rows(err,b'CIRCUS_SUPPRESSION_CHECKPOINT ')
        need(checkpoints==[dict(normal_save30_sha256=g.SAVE['sha256'],bootstrap=False,prefix_wins_reexecuted=0,host_state_injection=False)],'cache-only native checkpoint')
        calls=value['getter_calls'];need(len(calls)==1 and calls[0]['result']==30 and calls[0]['owner_current']==30
            and calls[0]['args'][3]==calls[0]['r3_at_entry'] and calls[0]['sp_before']==calls[0]['sp_after']
            and calls[0]['host_writes']==calls[0]['host_calls']==0,'natural five-argument getter proof')
        need(value['draws'] and all(r['flags'].bit_count()==2 for r in value['draws']),'30-win two-effect draw contract')
        value['analysis']=c.validate_lifecycle(raw,err,b.exited(proc))
        need(value['raw_last_result']['prefix_wins_reexecuted']==0,'accepted30 replayed')
        value['native_verified']=True;value['classification']='CIRCUS_GETTER_ABI_SUPPRESSION_NATIVE_VERIFIED_VISUAL_OPEN'
    except Exception as error:
        value['failures'].append(dict(stage='getter-native-or-build',type=type(error).__name__,error=str(error)))
        value['classification']='CIRCUS_GETTER_ABI_DIAGNOSTIC_OPEN'
    finally:
        for path,bound in protected.items():
            if b.identity(path.read_bytes())!=bound:value['failures'].append(dict(stage='immutability',error=path.name))
        if value['failures']:value['native_verified']=False
        (OUT/'native-result.json').write_bytes(b.stable(value))


def finish():
    path=OUT/'native-result.json';value=c.strict(path.read_bytes()) if path.exists() else b.load(REPORT)
    if not path.exists():value['failures'].append(dict(stage='setup',error='cache/dependency step failed before native; no bootstrap fallback'))
    checkpoint(value,'FINISH')


def pack():
    previous.OUT=OUT;previous.CACHE=CACHE;previous.pack()


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('prepare','native','finish','pack','result'),'command')
    if sys.argv[1]=='result':
        value=b.load(REPORT);need(value['native_verified'] and not value['failures'],'suppression remains open')
    else:globals()[sys.argv[1]]()
