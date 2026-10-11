#!/usr/bin/env python3
"""二originの正式受領と完了読戻し。旧測定・ROMを再実行しない有限Actions。"""
from __future__ import annotations
import datetime as dt
import io
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_typed_origins_receipt as m
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=m.ROOT
START=m.MEASURED
TASK='USER-20261011-TYPED-ORIGINS-RECEIPT'
COMPLETE_TASK='USER-20261011-TYPED-ORIGINS-COMPLETION'
STATE='content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE='docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
WINDOW='content/modernization/pr16_donor_window_evidence/windows.json'
REQUEST='content/modernization/pr16_typed_origins_receipt_request.json'
COMPLETE=m.EVIDENCE+'/actions-completion.json'
WF='.github/workflows/pr16-typed-origins-receipt.yml'
CODE={'scripts/pr16_typed_origins_receipt.py','scripts/pr16_typed_origins_receipt_actions.py',
      'tests/test_pr16_typed_origins_receipt.py',WF}
LOGS={'design/run_log.md','design/version_log.md'}
OUTPUTS={m.REPORT,m.EVIDENCE+'/reference-chain.json',m.EVIDENCE+'/unknown-frontier.json',
         m.EVIDENCE+'/measurement-actions.json',m.EVIDENCE+'/receipt-tests.txt',
         m.EVIDENCE+'/window-progress.json',STATE,GUIDE,*LOGS}
WORK=ROOT/'.local/pr16-typed-origins-receipt'
PUBLIC=WORK/'public'
PHASE='preflight'


def read(name):return m.regular(ROOT,name)


def write(name,value):a.changed_write(name,m.encode(value) if type(value) is dict else value)


def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()


def snapshot(names):
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(set(names)-LOGS):z.writestr(name,read(name))


def append_logs(task,summary,verify):
    now=stamp()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {task} / 二origin正式型受領\n'
        '- Version: typed-origins-receipt-v1\n- Status: DONE（限定型受領。保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 二origin受領器/試験/専用Actions、受領証拠、固定引継ぎMD/JSON、両ログ。\n'
        f'- Verify: {verify}\n'
        '- Boundary: 正式787分類/87未知・安全容量0。自然entry/IRQ/GPU flush/浮動callee本体/全alias不在は非主張。'
        '旧原本/他872行/全旧namespace/R0/ROM/Save101/baseline不変。ROM再構成/native/旧reader/旧試験再走0。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはGit履歴とActions resultに保存。\n'
        '- Network: 同repo PR/ref/Actions/artifactのGETと同branch非force pushのみ。外部source/ROMの再採取なし。\n')
    for name in LOGS:
        old=read(name);m.need(('- Task: '+task+' /').encode() not in old,'同task重複禁止');write(name,old+block.encode())


def publish(base,head,allowed,report,task):
    publication.final_index(base,allowed,report)
    m.need(a.git('ls-remote','origin','refs/heads/'+m.BRANCH).decode().split()[0]==head,'push前HEAD競合')
    for name in allowed:m.need(a.git('show',':'+name)==read(name),'最終index全byte')
    a.git('config','user.name','github-actions[bot]')
    a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',task+': 二originの正式型受領・証拠と引継ぎを記録')
    a.git('push','origin','HEAD:'+m.BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+m.BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'commit blob読戻し')
    return pushed


def build(head,observed):
    global PHASE
    m.need(set(a.git('diff','--name-only',START,head).decode().splitlines())==CODE,'新4source scope')
    m.need(not (ROOT/m.REPORT).exists() and not (ROOT/REQUEST).exists(),'正式受領済み再走禁止')
    state=m.read(read(STATE));m.need(state['next_action']['id']=='SAVE_CAPACITY_TWO_TYPED_ORIGINS_RECEIPT','現行next')
    PHASE='receive-completed-measurement'
    metadata=m.metadata(a.fetch('actions/runs/'+str(m.RUN)),
        a.fetch('actions/runs/'+str(m.RUN)+'/jobs?filter=latest&per_page=100'),a.fetch('actions/artifacts/'+str(m.ARTIFACT)))
    raw=a.fetch('actions/artifacts/'+str(m.ARTIFACT)+'/zip',binary=True)
    files,context=m.unpack(raw)
    for name,data in context.items():m.need(data==read(name)==a.git('show',START+':'+name),'context全16byte: '+name)
    cp_raw,proof_raw=files['pr16_typed_origins_checkpoint.json'],files['reader-profiles.json']
    cp,_,_=m.measurement(cp_raw,proof_raw);bindings=m.sources(cp)
    for name,meta in bindings.items():m.need(m.exact(m.identity(a.git('show',START+':'+name)),meta),'固定測定commit source')
    metadata.update(member_identities={n:m.identity(v) for n,v in sorted(files.items())},
        context_identities={n:m.identity(v) for n,v in sorted(context.items())},measurement_replays=0,
        rom_reconstructions=0,native_processes=0,old_scope_test_reruns=0)
    protected={*bindings,*context,WINDOW,'content/modernization/pr16_forest_wallpaper_receipt.json',
        'content/modernization/pr16_donor_origins_evidence/symbol-frontier.json'}-{STATE,GUIDE}
    before={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in protected}
    PHASE='new-receipt-tests'
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_typed_origins_receipt.py'))
    (PUBLIC/'receipt-tests.txt').write_text(stream.getvalue())
    m.need(tests.wasSuccessful() and tests.testsRun==63 and not tests.skipped,'新63受領試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE='restore-saved-parent-and-apply-two-delta'
    parent=m.restore_785_raw();delta=m.build(parent,cp_raw,proof_raw);full=m.materialize(parent,delta,cp_raw,proof_raw)
    unknown=m.frontier(full)
    m.need(m.encode(delta)==m.encode(m.build(parent,cp_raw,proof_raw)),'同入力差分決定性')
    window=m.read(read(WINDOW));selected=window['selected']
    m.need(m.exact([selected[k] for k in ('start','end_exclusive','size','unclassified_target_entries')],
                  [0x09FED0C4,0x09FEEA44,6528,10]),'保存した選定窓のみ。最適化再走なし')
    unknown_by_address={r['hit']['address']:r['hit'] for r in unknown['rows']}
    remaining=[row for row in selected['unclassified_target_rows'] if row['address'] not in m.HITS]
    m.need(len(remaining)==8 and [r['address'] for r in selected['unclassified_target_rows'][:2]]==list(m.HITS),'選定10件から受領2件だけを除外')
    for row in remaining:m.need(all(m.exact(v,unknown_by_address[row['address']][k]) for k,v in row.items()),'残8件の全元field不変')
    progress=dict(schema_version=1,status='SAVED_WINDOW_PROGRESS_NOT_A_LEASE',window_path=WINDOW,
        window_identity=m.identity(read(WINDOW)),selected_range={k:selected[k] for k in ('start','end_exclusive','size')},
        inherited_unclassified=10,newly_classified_addresses=list(m.HITS),remaining_count=8,remaining_rows=remaining,
        next_address=remaining[0]['address'],formal_classified=787,formal_unclassified=87,donor_safe_bytes=0,
        optimization_reruns=0,full_rom_scans=0,retirement_or_transfer_complete=False,
        outside_target_excludes_access=False,intra_donor_origins_covered=False,indirect_reference_completeness_claimed=False)
    next_address=f'0x{progress["next_address"]:08X}'
    goal=(f'正式787/87・安全容量0の保存親から、同じ6528byte選定窓の残8origin（次は{next_address}）を進める。'
        '保存symbol-frontierと固定公開source/asset identityから現候補の有限consumer範囲を束縛する。近傍labelだけで型分類しない。'
        '窓外跨りread/旧owner内origin/間接参照/退役・移管/保存controller・heap・局所Save/fresh Continueは未完。'
        '新二originの3reader/20試験/63受領試験、全874scan、Forest/Bubble/窓最適化をsource不変なら再走しない。')
    for name,value in [(m.EVIDENCE+'/reference-chain.json',delta),(m.EVIDENCE+'/unknown-frontier.json',unknown),
                       (m.EVIDENCE+'/measurement-actions.json',metadata),(m.EVIDENCE+'/window-progress.json',progress)]:write(name,value)
    write(m.EVIDENCE+'/receipt-tests.txt',stream.getvalue().encode())
    evidence=OUTPUTS-{m.REPORT,STATE,GUIDE,*LOGS}
    report=dict(schema_version=1,task=TASK,status=delta['status'],source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,measurement_actions=metadata,measurement_source_bindings=bindings,
        candidate=m.CANDIDATE,classified=787,unclassified=87,donor_safe_bytes=0,claims=delta['claims'],
        parent_audit_identity=m.PARENT_ID,delta_identity=m.identity(m.encode(delta)),full_audit_identity=m.identity(m.encode(full)),
        unknown_identity=m.identity(m.encode(unknown)),new_unit_tests=63,newly_classified=2,unchanged_hit_rows=872,
        all_old_namespaces_preserved=True,measurement_replays=0,rom_reconstructions=0,native_processes=0,old_scope_test_reruns=0,
        read_only_check_passed=True,task_graph_passed=True,window_progress_path=m.EVIDENCE+'/window-progress.json',
        receipt_code_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        evidence_bindings={n:m.identity(read(n)) for n in sorted(evidence)},observed_head_checks=observed,next_ja=goal)
    write(m.REPORT,report)
    PHASE='read-only-restoration-and-record'
    saved={n:(read(n),(ROOT/n).stat().st_mtime_ns) for n in evidence|{m.REPORT}}
    restored=m.restore_parent();m.need(m.exact(restored,full),'保存正式787親の完全復元')
    m.need(saved=={n:(read(n),(ROOT/n).stat().st_mtime_ns) for n in saved},'復元checkのbyte/mtime不変')
    m.need(before=={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in before},'全旧原本byte/mtime不変')
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    lane.update(status=delta['status'],checkpoint_path=m.REPORT,classified=787,unclassified=87,donor_safe_bytes=0,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SELECTED_WINDOW_NEXT_ASSET_BINDING',goal_ja=goal,
        read_paths=[GUIDE,m.REPORT,m.EVIDENCE+'/window-progress.json',m.EVIDENCE+'/unknown-frontier.json',
                    'content/modernization/pr16_donor_origins_evidence/symbol-frontier.json','scripts/pr16_typed_origins_receipt.py'],
        done_ja='選定窓の次originを固定source/assetと現候補の実consumerへ有限scopeで結ぶ。容量0の境界を保持。')
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_TWO_ORIGINS_FORMALLY_ACCEPTED_787_87'
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,new_unit_tests=63,newly_classified=2,accepted_tests_rerun=0,
        new_native_processes=0,rom_reconstructions=0,read_only_check_passed=True,task_graph_passed=True,
        classified=787,unclassified=87,donor_safe_bytes=0)
    state['recording']['pending_receipt_run']=dict(run_id=int(os.environ['GITHUB_RUN_ID']),source_head=head,
        output_report=m.REPORT,status='COMPLETION_NOT_YET_OBSERVED',replay_forbidden=True)
    write(STATE,state)
    text=read(GUIDE).decode();m.need('## 二originの正式型受領' not in text,'引継ぎ重複禁止')
    text=text.replace('## 次の未完作業','## 以前の停止点（履歴）')
    text+=(f'\n## 二originの正式型受領\n\n測定run {m.RUN} / job {m.JOB} の全9step成功、artifact {m.ARTIFACT} の全ZIP/9memberと'
        '同梱16sourceを公開commitへ照合しました。測定原本のpending表記は改作せず、別receiptで完了を受領しています。\n\n'
        '0x080A006Fはaligned literal末尾1byte+Thumb callback先頭3byte、0x081C96E9はBL末尾3byte+ADD先頭1byteです。'
        '実LDR/GPU u16 buffer store/callback書込帰還と、同期callee帰還条件のinstruction fetchだけを正式分類へ移しました。'
        '自然entry/IRQ/GPU flush/浮動callee本体/全alias不在は受入していません。\n\n'
        f'[正式receipt](../{m.REPORT}) / [二件差分](../{m.EVIDENCE}/reference-chain.json) / '
        f'[未知87行](../{m.EVIDENCE}/unknown-frontier.json) / [選定窓の残8origin](../{m.EVIDENCE}/window-progress.json)。'
        '785/89から787/87へ二件だけ追加し、他872行と全旧namespaceを保全。新63受領試験、決定性、保存後読取専用復元、task graphを検証。'
        '旧測定/reader/旧試験/native/ROM再構成は0。安全容量0、保存controller/heap/保存接続は未完です。\n\n'
        '受領Actions自身の完了は、runが実際に完了した後の外部読戻しで別記録します。生成中のrunを成功と先取りしません。\n\n'
        '## 次の未完作業\n\n'+goal+'\n')
    write(GUIDE,text.encode())
    append_logs(TASK,'成功測定の全9member/同梱16file/sourceを受領。二件だけ正式785/89→787/87。選定窓は再最適化せず残8件へ射影。',
        '新63 tests PASS、全874行の二件差分/他872行/全旧namespace、決定性、保存後read-only byte/mtime、task graph PASS。全体guardと新規private違反は別記録。')
    pushed=publish(START,head,CODE|OUTPUTS,m.REPORT,TASK)
    for name in (m.REPORT,m.EVIDENCE+'/measurement-actions.json',m.EVIDENCE+'/window-progress.json'):
        (PUBLIC/Path(name).name).write_bytes(read(name))
    snapshot(CODE|OUTPUTS|{WINDOW,'content/modernization/pr16_donor_origins_evidence/symbol-frontier.json',m.CHECKPOINT,m.PROOF,
        'scripts/pr16_forest_wallpaper_receipt.py','scripts/pr16_typed_origins.py'})
    return dict(status='DONE',task=TASK,source_head=head,commit=pushed,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        new_unit_tests=63,classified=787,unclassified=87,donor_safe_bytes=0,old_scope_test_reruns=0,measurement_replays=0,
        rom_reconstructions=0,native_processes=0)


def complete(head,observed):
    global PHASE
    PHASE='receive-receipt-actions-completion'
    request=m.read(read(REQUEST))
    base=request['receipt_commit']; source=request['receipt_source_head']; run_id=request['run_id']; artifact_id=request['artifact_id']
    m.need(set(a.git('diff','--name-only',base,head).decode().splitlines())=={REQUEST},'外部受領requestだけ。競合は自動破棄しない')
    m.need(not (ROOT/COMPLETE).exists(),'完了受領済み再走禁止')
    run=a.fetch('actions/runs/'+str(run_id))
    for k,v in dict(id=run_id,head_sha=source,head_branch=m.BRANCH,path=WF,event='push',run_attempt=1,status='completed',conclusion='success').items():
        m.need(m.exact(run.get(k),v),'受領Actions '+k)
    m.need(run['repository']['full_name']==run['head_repository']['full_name']==m.REPO,'同repo')
    jobs=a.fetch('actions/runs/'+str(run_id)+'/jobs?filter=latest&per_page=100')
    m.need(jobs['total_count']==len(jobs['jobs'])==1,'全受領job')
    steps=jobs['jobs'][0]['steps']
    m.need(jobs['jobs'][0]['conclusion']=='success' and all(s['status']=='completed' and s['conclusion']=='success' for s in steps),'全受領step成功')
    m.need(any(s['name']=='Receive saved typed origins or record completed receipt' for s in steps) and
        any(s['name']=='Run actions/upload-artifact@v4' for s in steps),'必要な受領/upload step')
    artifact=a.fetch('actions/artifacts/'+str(artifact_id));zip_id=request['zip_identity']
    m.need(artifact['name']=='pr16-typed-origins-receipt-public-text' and artifact['expired'] is False and
        artifact['workflow_run']['id']==run_id and artifact['workflow_run']['head_sha']==source and
        artifact['size_in_bytes']==zip_id['size'] and artifact['digest']=='sha256:'+zip_id['sha256'],'受領artifact identity')
    raw=a.fetch('actions/artifacts/'+str(artifact_id)+'/zip',binary=True);m.need(m.exact(m.identity(raw),zip_id),'受領ZIP全hash')
    files=m.zip_members(raw,{'pr16_typed_origins_receipt.json','measurement-actions.json','window-progress.json','receipt-tests.txt','scoped-context.zip','result.json'})
    result=m.read(files['result.json']);m.need(result['status']=='DONE' and result['commit']==base and result['source_head']==source and
        result['actions_run_id']==run_id and result['new_unit_tests']==63,'受領result/公開commit')
    with zipfile.ZipFile(io.BytesIO(files['scoped-context.zip'])) as z:
        names=z.namelist();m.need(len(names)==len(set(names)),'受領context重複なし')
    context=m.zip_members(files['scoped-context.zip'],set(names))
    for name,data in context.items():m.need(data==a.git('show',base+':'+name)==read(name),'受領context全byte')
    report=m.read(read(m.REPORT));m.need(report['source_head']==source and report['actions_run_id']==run_id and
        m.exact(report['claims'],dict(m.CLAIMS,formal_classification_accepted=True)),'正式receipt/非主張')
    proof=dict(schema_version=1,status='COMPLETED_TYPED_ORIGINS_RECEIPT_ACTIONS_RECEIVED',source_head=head,
        received_run=dict(id=run_id,source_head=source,status='completed',conclusion='success'),
        receipt_commit=base,artifact_id=artifact_id,zip_identity=zip_id,
        member_identities={n:m.identity(v) for n,v in sorted(files.items())},
        context_identities={n:m.identity(v) for n,v in sorted(context.items())},
        steps=[{k:s[k] for k in ('number','name','status','conclusion')} for s in steps],
        classified=787,unclassified=87,donor_safe_bytes=0,old_scope_test_reruns=0,measurement_replays=0,
        rom_reconstructions=0,native_processes=0,observed_head_checks=observed,observed_at=stamp())
    write(COMPLETE,proof)
    state=m.read(read(STATE));state['recording']['received_typed_origins_completion']=COMPLETE
    pending=state['recording'].pop('pending_receipt_run')
    m.need(pending['run_id']==run_id and pending['source_head']==source,'保存pending対応')
    state['recording']['last_execution']=dict(task=COMPLETE_TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,received_completed_run=run_id,accepted_tests_rerun=0,new_native_processes=0,
        rom_reconstructions=0,classified=787,unclassified=87,donor_safe_bytes=0)
    state['observed_head_checks']=observed;write(STATE,state)
    text=read(GUIDE).decode();marker='## 二origin受領Actionsの完了読戻し'
    m.need(marker not in text,'完了記録重複なし')
    text=text.replace('## 次の未完作業',marker+f'\n\n正式受領run {run_id} の全job/step成功、公開commit `{base}`、artifact全memberと同梱sourceを別途照合しました。'
        f'[完了receipt](../{COMPLETE})。63受領試験/旧reader/ROMを再走せず、測定原本も正式receipt原本も改作していません。\n\n## 次の未完作業')
    write(GUIDE,text.encode())
    append_logs(COMPLETE_TASK,f'正式受領run {run_id} / commit {base}の完了を別receiptに記録。',
        '全job/step/upload/ZIP全hash/全member/公開commit source PASS。既成功63試験を再走せず原本byteを照合。新規private guardは別記録。')
    pushed=publish(base,head,{REQUEST,COMPLETE,STATE,GUIDE,*LOGS},COMPLETE,COMPLETE_TASK)
    (PUBLIC/'completion.json').write_bytes(read(COMPLETE))
    return dict(status='DONE',task=COMPLETE_TASK,source_head=head,commit=pushed,received_run=run_id,
        classified=787,unclassified=87,donor_safe_bytes=0,old_scope_test_reruns=0,measurement_replays=0,
        rom_reconstructions=0,native_processes=0)


def main():
    m.need(os.environ.get('GITHUB_REPOSITORY')==m.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+m.BRANCH and
        os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同repo/branch初回のみ')
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    nested=a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
        'content/AGENTS.md','content/modernization/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    m.need(not nested.strip(),'追加AGENTS読取りが必要')
    m.need(not WORK.exists(),'同work再走禁止');PUBLIC.mkdir(parents=True)
    result=complete(head,observed) if (ROOT/REQUEST).exists() else build(head,observed)
    (PUBLIC/'result.json').write_bytes(m.encode(result))
    print(f'RESULT=DONE TASK={result["task"]} VERIFY=PASS COMMIT={result["commit"]}')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        if PUBLIC.exists():
            (PUBLIC/'failure.json').write_bytes(m.encode(dict(status='FAILED_NOT_ACCEPTED',phase=PHASE,
                exception_type=type(exc).__name__,frames=[dict(source=Path(f.filename).name,line=f.lineno,function=f.name)
                    for f in traceback.extract_tb(exc.__traceback__) if '/scripts/' in f.filename],
                measurement_replays=0,rom_reconstructions=0,native_processes=0)))
        print(f'RESULT=STOPPED TASK={TASK} VERIFY=FAIL COMMIT=- PHASE={PHASE}');sys.exit(1)
