#!/usr/bin/env python3
"""P08差分監査の実行・証拠/引継ぎ保存。既受入nativeは一切再実行しない。"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_battle25 as b
import pr16_p08_impact as impact

TASK='USER-20260920-P08-IMPACT'
BASE='8359309e868213d2ffc86a1c56a11f41ed7dda0d'
SELF='scripts/pr16_p08_record.py'
TEST='tests/test_pr16_p08_impact.py'
WORKFLOW='.github/workflows/pr16-p08-impact.yml'
FILES=(SELF,impact.SELF,TEST,WORKFLOW)
REPORT='content/modernization/pr16_p08_candidate_impact.json'
OUT=ROOT/'.local/pr16-p08-impact'
need=impact.need


def execute():
    OUT.mkdir(parents=True,exist_ok=True);b.OUT=OUT
    head=b.scope();state=b.resume.validate(ROOT);backlog=b.load(b.resume.BACKLOG)
    need(set(b.command('git','diff','--name-only',BASE,head).splitlines())==set(FILES),'unreviewed P08 source delta')
    need(state['remaining_physical_gap_ids']==[] and state['remaining_p08_gate_ids']==['FINAL_NATIVE_ACCEPTANCE','RELEASE_DECISION'],
         'unexpected pending conditions')
    protected={p:b.identity((ROOT/p).read_bytes()) for p in (*impact.REPORTS.values(),impact.NORMAL,impact.GETTER,'config/active_play_baseline.json')}
    prior=b.api('actions/runs/35506654695');artifact=b.api('actions/artifacts/10603786970')
    need(prior['status']=='completed' and prior['conclusion']=='success'
         and prior['head_sha']=='5a1b35ad66c0a9a157274835987d9d7d20ba1f12','Circus acceptance not complete')
    need(artifact['workflow_run']['id']==prior['id'] and not artifact['expired']
         and artifact['digest']=='sha256:b90b6201532ed03c97ed43dc31958efd606dea381f5f9eb8e8fb2395beeca4e7',
         'Circus receipt artifact identity')
    for label,args,timeout in (
        ('new-impact-contracts',[sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],120),
        ('full-rom-offline',[sys.executable,impact.SELF,'reconstruct','--output',str(OUT/'runtime')],240)):
        _,_,proc=b.capture(args,label,timeout);need(b.exited(proc)==0,label+' failed')
    result=b.load('.local/pr16-p08-impact/runtime/impact.json')
    need(result['candidate']==impact.TARGET and result['full_rom_sparse_comparison'] is True
         and result['reconstruction']['whole_chain_rollback_matches_parent'] is True
         and result['offline_process_barrier_active'] is True and result['recipe_layers']==21
         and result['patch_operations']==432,'full-ROM impact proof failed')
    need(result['new_emulator_processes']==result['arm_compiles']==result['arm_links']==0,'unexpected native/build')
    need(result['candidate_impacts']['CIRCUS']['exact_candidate'] is True
         and result['candidate_impacts']['CIRCUS']['source_review']['mismatches']==0,'Circus source drift')
    run_id=int(os.environ['GITHUB_RUN_ID'])
    result.update(task=TASK,source_head=head,recording_run=run_id,
        circus_acceptance_run=dict(id=prior['id'],conclusion=prior['conclusion'],head_sha=prior['head_sha'],
                                   artifact_id=artifact['id'],digest=artifact['digest']),
        original_case_acceptance_unchanged=True,active_baseline_changed=False,
        old_accepted_native_replays=0,session_rom_changes=0,
        scope_ja='同じ46487d98候補を保存byteから前進/逆適用。新しい機能受入ではなく、旧受入から最終候補への影響範囲と必要最小回帰を固定。')
    result['source_bindings'].update({p:b.identity((ROOT/p).read_bytes()) for p in FILES})
    evidence='evidence/pr16_p08_impact/'+str(run_id)+'/impact.json'
    tests_evidence='evidence/pr16_p08_impact/'+str(run_id)+'/contracts.stderr'
    b.write(REPORT,b.stable(result));b.write(evidence,b.stable(result))
    b.write(tests_evidence,(OUT/'execution/new-impact-contracts.stderr').read_bytes())
    nxt=('P08影響台帳の4代表境界を対象に、まずBP帰還party/保存とRing通常戦闘を同じ46487d98候補で限定検証する。'
         'P03保存再開とCircus退出後通常戦闘も共有hook影響・未観測境界として残す。P07表・旧30勝・受入全件を再実行しない。')
    stop=('P08保存byte21層432patchの全ROM前進/逆適用、6受入候補からの正味差分、100allocator owner、'
          'source/runner/fixture binding照合を保存。P07の3content ownerは不変。Circus同一候補受入は保持。'
          '共有save/load/party/battle hookに影響があるためP08最終native/releaseは未完。')
    final=next(r for r in backlog['remaining_conditions'] if r['id']=='FINAL_NATIVE_ACCEPTANCE')
    need(not final.get('complete',False),'P08 already complete')
    final.update(change_impact_evidence=REPORT,candidate_sha256=impact.TARGET['sha256'],
                 required_representative_regression_ids=[r['id'] for r in result['required_representative_regressions']],
                 resume=nxt,status='EXACT_BYTE_IMPACT_VERIFIED_REPRESENTATIVE_NATIVE_PENDING')
    backlog['p08_candidate_impact']=dict(path=REPORT,byte_chain_verified=True,
        final_native_acceptance_complete=False,release_ready=False)
    state['p08_candidate_impact']=dict(path=REPORT,candidate=dict(**impact.TARGET,crc32=result['candidate_crc32']),
        source_head=head,run_id=run_id,exact_byte_chain_verified=True,final_native_acceptance_complete=False)
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action'].update(id='P08_SHARED_RUNTIME_REPRESENTATIVE_NATIVE',
        read_paths=[REPORT,impact.SELF,SELF,'scripts/pr16_ring_policy_native.py','scripts/pr16_bp_chooser_native.py',b.resume.BACKLOG],
        stop_rule_ja='このP08監査runの完了Actionsを先に照合。新nativeは共有hook影響の代表境界だけ。未影響の旧30勝/P07全表/受入単体群を再実行しない。')
    state['remaining_sequence_ja']='Circus正式受入完了 → P08 byte/owner影響監査完了 → 共有runtime代表回帰4境界 → 配布準備判断'
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='P08監査を実行した固定source HEAD。記録run自身の完了結論は次回Actions照合で確定する。'
    recent=b.api('actions/runs?branch='+b.BRANCH+'&per_page=30')['workflow_runs']
    state['observed_head_checks']=dict(scope_head=head,runs=[{k:r[k] for k in ('id','head_sha','path','status','conclusion')} for r in recent],
        reason_ja='Circus記録35506654695は完了success。P08記録run自身はこの時点でin_progress。source CIをnative成功に読み替えない。')
    state['pending_runs']=[dict(run_id=run_id,tested_head=os.environ['GITHUB_SHA'],status='in_progress',
                                reason_ja='この記録commitの後にartifact upload/Actions完了を確認する。')]
    state['session_execution_summary']=dict(new_emulator_processes=0,arm_compiles=0,arm_links=0,
        prefix_wins_reexecuted=0,accepted_standalone_replays=0,
        scope_ja='P08 exact-byte影響監査と新規22契約だけ。保存byte再構成はclean ROM二重buildとは別。')
    state['do_not_repeat'].insert(0,'P08の21層432patch全ROM監査はpr16_p08_candidate_impact.jsonに保存。同じ入力のARM/旧builder/旧nativeは再実行せず、未完4代表境界へ。')
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    b.write(b.resume.BACKLOG,b.stable(backlog))
    tracked=[*FILES,REPORT,evidence,tests_evidence,b.resume.BACKLOG]
    for path in tracked:state['source_bindings'][path]=b.identity((ROOT/path).read_bytes())
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode())
    b.resume.validate(ROOT)
    _,_,proc=b.capture([sys.executable,'scripts/validate_task_graph.py'],'task-graph')
    need(b.exited(proc)==0,'task graph failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths=[*tracked,b.resume.STATE,b.resume.DOC,*b.LOGS]
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
           '- Status: DONE（差分監査完了。P08最終native/releaseは未完）\n- Version: pr16-p08-impact-v1\n'
           '- Summary: '+stop+'\n- Files changed: '+', '.join(paths)+'\n'
           '- Verify: 新規22契約PASS、21層432patch/全ROM逆適用/疎差分一致、100allocation、resume正本/MD/hash整合、task graph PASS。\n'
           '- Boundary: 新native0、ARM0、旧30勝再実行0、製品SHA固定なし、active baseline変更なし。clean ROM二重build未実施。\n'
           '- Commit: 同branch非force commit/push、remote読戻し。\n'
           '- Network: 完了Circus記録Actions/固定artifact metadataと最新30Actionsの読取のみ。byte再構成中はprocess/network遮断。\n'
           '- Next: '+nxt+'\n')
    for path in b.LOGS:
        need('— '+TASK not in (ROOT/path).read_text(),'duplicate P08 receipt')
        with (ROOT/path).open('a') as stream:stream.write(entry)
    need(all(b.identity((ROOT/p).read_bytes())==v for p,v in protected.items()),'accepted original changed')
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines())
    need(changed and changed<=set(paths),'stage scope')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=head,OUT,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': 21層全ROM監査・owner影響と最小代表回帰を固定'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    committed=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty worktree')
    (OUT/'receipt.json').write_bytes(b.stable(dict(task=TASK,commit=committed,run_id=run_id,non_force_push=True)))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+committed)


def pack():
    dst=OUT/'artifact';dst.mkdir(parents=True,exist_ok=True)
    for src in OUT.rglob('*'):
        if not src.is_file() or dst in src.parents or src.suffix not in ('.json','.stdout','.stderr','.txt'):continue
        data=src.read_bytes();data.decode('utf-8');need(b'\0' not in data,'nontext audit artifact')
        target=dst/src.relative_to(OUT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    for path in (*FILES,REPORT):
        src=ROOT/path
        if src.is_file():
            target=dst/'source'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())


if __name__=='__main__':
    need(len(sys.argv)==2,'command required')
    if sys.argv[1]=='execute':execute()
    elif sys.argv[1]=='pack':pack()
    else:raise ValueError('unknown command')
