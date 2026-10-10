#!/usr/bin/env python3
"""固定保存親の窓比較・独立総当たり・引継ぎ記録。明示許可されたbranchだけへ非force反映。"""
from __future__ import annotations
import copy
import datetime as dt
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_donor_window as m
import pr16_forest_wallpaper_receipt as r
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

START = 'afa285e11d86d85a314292c071be37d479431424'
TASK = 'USER-20261011-DONOR-WINDOW'
STATE = 'content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE = 'docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
EVIDENCE = 'content/modernization/pr16_donor_window_evidence'
REQUEST = EVIDENCE+'/completion-request.json'
COMPLETE = EVIDENCE+'/actions-completion.json'
TESTS = EVIDENCE+'/window-tests.txt'
WF = '.github/workflows/pr16-donor-window.yml'
CODE = {'scripts/pr16_donor_window.py','scripts/pr16_donor_window_actions.py','tests/test_pr16_donor_window.py',WF}
LOGS = {'design/run_log.md','design/version_log.md'}
OUTPUTS = {m.REPORT,m.PLAN,TESTS,STATE,GUIDE,*LOGS}
WORK = m.ROOT/'.local/pr16-donor-window'
PUBLIC = WORK/'public'
PHASE = 'preflight'


def write(name,value):
    a.changed_write(name,m.encode(value) if type(value) is dict else value)


def snapshot(names):
    return {n:((m.ROOT/n).stat().st_mtime_ns,m.identity(r.regular(m.ROOT,n))) for n in names}


def append_logs(task,summary,verification):
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {task} / 保存controller候補窓の有限比較\n'
        '- Version: donor-window-v1\n- Status: DONE（窓選定/証拠のみ。保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 窓比較器/新規試験/専用workflow、窓証拠/受領、固定Forest引継ぎMD/状態JSON、両ログ。\n'
        f'- Verify: {verification}\n'
        '- Boundary: 正式785分類/89未知・安全容量0。R0/旧受入/正式ROM/Save101/baseline不変。新native/ROM再構成/旧試験再走0、merge/releaseなし。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはActions resultとGit履歴で照合。自己SHAだけのcommitは作らない。\n'
        '- Network: 指定repoのPR/ref/Actions GETと公開text artifact受領、同branchへの非force pushのみ。外部入力の再採取なし。\n')
    for name in LOGS:
        old=r.regular(m.ROOT,name)
        m.need(('- Task: '+task+' /').encode() not in old,'同task重複記録')
        write(name,old+block.encode())


def publish(base,head,allowed,report,message):
    publication.final_index(base,allowed,report)
    m.need(not set(a.git('diff','--name-only','HEAD').decode().splitlines())-allowed,'無関係なtracked変更')
    for name in allowed:
        m.need(a.git('show',':'+name)==r.regular(m.ROOT,name),'最終index全byte')
    m.need(a.git('ls-remote','origin','refs/heads/'+r.BRANCH).decode().split()[0]==head,'push前競合')
    a.git('config','user.name','github-actions[bot]')
    a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',message)
    a.git('push','origin','HEAD:'+r.BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+r.BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:
        m.need(a.git('show','HEAD:'+name)==r.regular(m.ROOT,name),'commit全対象blob読戻し')
    return pushed


def measure(head,observed):
    global PHASE
    m.need(set(a.git('diff','--name-only',START,head).decode().splitlines())==CODE,'閉4source scope')
    m.need(not (m.ROOT/m.REPORT).exists() and not (m.ROOT/m.PLAN).exists(),'測定済みの重複実行禁止')
    state=r.read(r.regular(m.ROOT,STATE))
    m.need(state['next_action']['id']=='SAVE_CAPACITY_POST_FOREST_DONOR_WINDOW' and
           state['owner_execution_plan']['wiki']['review_ready'] is True,'固定nextとR0')
    PHASE='new-window-tests'
    text=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(m.ROOT/'tests'),pattern='test_pr16_donor_window.py')
    result=unittest.TextTestRunner(stream=text,verbosity=2).run(suite)
    (PUBLIC/'window-tests.txt').write_text(text.getvalue())
    m.need(result.wasSuccessful() and result.testsRun==49 and not result.skipped,'新49試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=m.ROOT,check=True,capture_output=True)
    PHASE='bound-saved-parent-and-finite-windows'
    cp=r.measurement(r.regular(m.ROOT,r.MEASUREMENT))
    bindings=r.sources(cp)
    protected=set(bindings)|{r.REPORT,r.EVIDENCE+'/reference-chain.json',r.EVIDENCE+'/unknown-frontier.json',
                            'CHATGPT_RESUME.md','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'}
    before=snapshot(protected)
    plan=m.from_saved()
    raw=m.encode(plan)
    frontier=r.read(r.regular(m.ROOT,r.EVIDENCE+'/unknown-frontier.json'))
    m.need(frontier['total']==89 and len(frontier['rows'])==89,'保存未知89行')
    oracle=[(sum(start<=x['hit']['target']<start+m.REQUIRED for x in frontier['rows']),start)
            for start in range(m.LO,m.HI-m.REQUIRED+1,m.ALIGNMENT)]
    minimum,start=min(oracle)
    m.need([minimum,start,len(oracle)]==[plan['minimum_unclassified_target_entries'],plan['selected']['start'],plan['examined_windows']],
           '実89行に対する独立全窓総当たり')
    from collections import Counter
    histogram=[dict(unclassified_target_entries=k,windows=v) for k,v in sorted(Counter(s for s,_ in oracle).items())]
    m.need(histogram==plan['score_histogram'],'全窓histogram独立一致')
    write(m.PLAN,raw);write(TESTS,text.getvalue().encode())
    saved=snapshot(protected|{m.PLAN,TESTS})
    subprocess.run(['python3','-B','scripts/pr16_donor_window.py','--check'],cwd=m.ROOT,check=True,capture_output=True)
    m.need(saved==snapshot(saved),'check全入力/output byte・mtime不変')
    selected=plan['selected'];targets=selected['unclassified_target_rows']
    first=(f"0x{targets[0]['address']:08X}" if targets else '未証明の計算/区間参照')
    goal=(f"候補窓[0x{selected['start']:08X},0x{selected['end_exclusive']:08X})の6528byteについて、"
        f"保存未知target {len(targets)}行（先頭{first}）のsource/asset identityと実consumerを限定して結ぶ。"
        '窓外targetからの跨りread・旧owner内originの除外・間接参照を残し、owner退役/部分移管を証明する。'
        '全874scan/Forest/Bubble/49窓試験の無変更再走は禁止。安全容量0を維持し、controller/heap/保存接続は別gate。')
    report=dict(schema_version=1,task=TASK,status='WINDOW_RANKING_COMPLETE_SAVE_INTEGRATION_PENDING',
        source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,
        actions_completion_path=COMPLETE,code_bindings={n:m.identity(r.regular(m.ROOT,n)) for n in sorted(CODE)},
        candidate=m.CANDIDATE,parent_audit_identity=m.PARENT_ID,plan_path=m.PLAN,plan_identity=m.identity(raw),
        new_unit_tests=49,randomized_oracle_examples=150,real_oracle_windows=len(oracle),
        read_only_check_passed=True,task_graph_passed=True,protected_inputs_unchanged=True,
        tests_identity=m.identity(text.getvalue().encode()),claims=copy.deepcopy(m.CLAIMS),
        selected=selected,observed_head_checks=observed,next_ja=goal)
    write(m.REPORT,report)
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    lane.update(status='FINITE_WINDOW_SELECTED_RETIREMENT_UNPROVEN',checkpoint_path=m.REPORT,
        classified=785,unclassified=89,donor_safe_bytes=0,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SELECTED_WINDOW_OWNER_COVERAGE',goal_ja=goal,
        read_paths=[GUIDE,m.REPORT,m.PLAN,'scripts/pr16_donor_window.py','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'],
        done_ja='選定窓の実owner/参照完全性/退役を有限根拠で証明する。target点の減少だけでleaseを発行しない。')
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_WINDOW_SELECTED_SAVE_INTEGRATION_PENDING'
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,actions_completion_path=COMPLETE,new_unit_tests=49,
        real_oracle_windows=len(oracle),read_only_check_passed=True,task_graph_passed=True,
        accepted_tests_rerun=0,new_native_processes=0,rom_reconstructions=0,classified=785,unclassified=89,donor_safe_bytes=0)
    write(STATE,state)
    old=r.regular(m.ROOT,GUIDE).decode()
    m.need('## 保存controllerの有限候補窓' not in old,'引継ぎ重複追記')
    old=old.replace('## 次の未完作業','## Forest受領時の停止点（履歴）',1)
    old+=(f'\n## 保存controllerの有限候補窓\n\n入力HEAD `{head}`。保存785/89親から全{len(oracle)}整列窓を比較し、'
          f"[0x{selected['start']:08X},0x{selected['end_exclusive']:08X})の6528byteを調査候補に固定しました。"
          f'窓内の未知target点は最小{minimum}行です。これは安全容量や退役証明ではありません。\n\n'
          f'[窓計画](../{m.PLAN}) / [検証checkpoint](../{m.REPORT})。新49試験、150組の総当たり対照、実{len(oracle)}窓の独立総当たり、'
          '決定的read-only check、task graphを検証。窓外targetからの跨りread、旧inventoryで除外された旧owner内origin、計算参照は未証明として保持。'
          '正式785/89/安全容量0、旧受入/R0/ROM/Save101は不変です。\n\n## 次の未完作業\n\n'+goal+'\n')
    write(GUIDE,old.encode())
    append_logs(TASK,f'{len(oracle)}整列窓を保存親から比較。未知target最小{minimum}行の候補窓を固定し、窓外/旧owner内origin/間接参照の未証明を明記。',
                f'新49 unit tests、150組対照、実{len(oracle)}窓独立総当たり、read-only byte/mtime、task graph PASS。最終index新規private違反0と既存全体guard失敗を分離。')
    PHASE='final-index-and-nonforce-push'
    m.need(snapshot(protected)==before,'旧原本不変')
    pushed=publish(START,head,CODE|OUTPUTS,m.REPORT,TASK+': 保存親から6528byte窓を選定・独立検証し未証明境界と次作業を記録')
    for name,dest in [(m.REPORT,'checkpoint.json'),(m.PLAN,'windows.json'),(GUIDE,'guide.md')]:
        (PUBLIC/dest).write_bytes(r.regular(m.ROOT,name))
    value=dict(status='DONE',task=TASK,commit=pushed,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        report_identity=m.identity(r.regular(m.ROOT,m.REPORT)),plan_identity=m.identity(raw),new_unit_tests=49,
        minimum_unclassified_target_entries=minimum,selected_start=selected['start'],selected_end=selected['end_exclusive'],
        claims=m.CLAIMS)
    (PUBLIC/'result.json').write_bytes(m.encode(value))
    return pushed


def receive(head,observed):
    global PHASE
    PHASE='completed-run-receipt'
    request=r.read(r.regular(m.ROOT,REQUEST));cp=r.read(r.regular(m.ROOT,m.REPORT))
    measured=request['measurement_commit']
    m.need(set(a.git('diff','--name-only',measured,head).decode().splitlines())=={REQUEST},'受領request以外の差分拒否')
    m.need(not (m.ROOT/COMPLETE).exists(),'二重受領拒否')
    m.need(cp['actions_run_id']==request['run_id'] and cp['source_head']==request['source_head'],'要求と測定identity')
    for name,meta in cp['code_bindings'].items():m.need(m.identity(r.regular(m.ROOT,name))==meta,'測定source不変')
    run=a.fetch('actions/runs/'+str(request['run_id']))
    for key,value in dict(id=request['run_id'],head_sha=request['source_head'],head_branch=r.BRANCH,
        path=WF,event='push',run_attempt=1,status='completed',conclusion='success').items():
        m.need(r.exact(run.get(key),value),'成功run '+key)
    m.need(run['repository']['full_name']==run['head_repository']['full_name']==r.REPO,'同repo')
    jobs=a.fetch('actions/runs/'+str(request['run_id'])+'/jobs?filter=latest&per_page=100')
    m.need(jobs['total_count']==len(jobs['jobs'])==1,'全job取得')
    job=jobs['jobs'][0]
    m.need(job['id']==request['job_id'] and job['name']=='donor-window' and job['status']=='completed' and
           job['conclusion']=='success' and job['head_sha']==request['source_head'],'成功job')
    expected=['Set up job','Run actions/checkout@v4','Run actions/setup-python@v5',
        'Finite saved-parent window proof and nonforce recording','Run actions/upload-artifact@v4',
        'Post Run actions/setup-python@v5','Post Run actions/checkout@v4','Complete job']
    m.need([s['name'] for s in job['steps']]==expected and all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),
           '全8step成功/skip拒否')
    artifact=a.fetch('actions/artifacts/'+str(request['artifact_id']))
    m.need(artifact['name']=='pr16-donor-window-public-text' and artifact['expired'] is False and
           artifact['workflow_run']['id']==request['run_id'] and artifact['workflow_run']['head_sha']==request['source_head'] and
           artifact['digest']=='sha256:'+request['artifact_sha256'] and artifact['size_in_bytes']==request['artifact_size'],'artifact identity')
    raw=a.fetch('actions/artifacts/'+str(request['artifact_id'])+'/zip',binary=True)
    m.need(m.identity(raw)==dict(size=request['artifact_size'],sha256=request['artifact_sha256']),'全ZIP hash')
    names={'window-tests.txt','windows.json','checkpoint.json','guide.md','result.json'}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos=archive.infolist()
        m.need(len(infos)==len(names) and {i.filename for i in infos}==names and
               all(not i.is_dir() and not i.flag_bits&1 and not stat.S_ISLNK(i.external_attr>>16) and i.file_size<=1000000 for i in infos),'閉5text ZIP')
        files={n:archive.read(n) for n in names}
    for name,path in [('window-tests.txt',TESTS),('windows.json',m.PLAN),('checkpoint.json',m.REPORT),('guide.md',GUIDE)]:
        m.need(files[name]==r.regular(m.ROOT,path),'公開原本全byte一致')
    result=r.read(files['result.json'])
    m.need(result['commit']==measured and result['source_head']==request['source_head'] and result['status']=='DONE' and
           result['report_identity']==m.identity(files['checkpoint.json']) and result['plan_identity']==m.identity(files['windows.json']) and
           r.exact(result['claims'],m.CLAIMS),'結果と公開commit/非主張')
    receipt=dict(schema_version=1,task=TASK+'-RECEIPT',status='COMPLETED_WINDOW_ACTIONS_RECEIVED',
        source_head=request['source_head'],measurement_commit=measured,run_id=request['run_id'],job_id=request['job_id'],
        artifact_id=request['artifact_id'],zip_identity=m.identity(raw),member_identities={n:m.identity(v) for n,v in files.items()},
        steps=[{k:s[k] for k in ('number','name','status','conclusion')} for s in job['steps']],
        measurement_replays=0,old_scope_test_reruns=0,claims=m.CLAIMS,observed_head_checks=observed)
    write(COMPLETE,receipt)
    state=r.read(r.regular(m.ROOT,STATE))
    m.need(state['recording']['last_execution']['actions_run_id']==request['run_id'],'固定状態が同測定')
    state['recording']['last_execution'].update(actions_completion_confirmed=True,actions_completion_path=COMPLETE,
        actions_completion_commit=measured,actions_completed_at=run['updated_at'])
    state['observed_head_checks']=observed
    write(STATE,state)
    append_logs(TASK+'-RECEIPT','窓選定Actionsの全job/8step、独立ZIP hash/全5member/公開commitを受領。測定checkpointは改作せず固定状態の完了flagを同期。',
                'run/job/artifact/全公開byte照合 PASS。測定/49試験再走0。最終index/private guardは既存違反と今回差分を分離。')
    PHASE='receipt-nonforce-push'
    pushed=publish(measured,head,{REQUEST,COMPLETE,STATE,*LOGS},COMPLETE,TASK+'-RECEIPT: 成功Actionsと全公開原本を受領し固定状態を同期')
    (PUBLIC/'receipt.json').write_bytes(r.regular(m.ROOT,COMPLETE))
    (PUBLIC/'result.json').write_bytes(m.encode(dict(status='DONE',commit=pushed,measurement_replays=0,old_scope_test_reruns=0)))
    return pushed


def main():
    m.need(os.environ.get('GITHUB_REPOSITORY')==r.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+r.BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同repo/branch/初回のみ')
    head=a.git('rev-parse','HEAD').decode().strip()
    m.need(head==os.environ['GITHUB_SHA'],'exact event HEAD')
    observed=a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    nested=a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
        'content/AGENTS.md','content/modernization/AGENTS.md',EVIDENCE+'/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    m.need(not nested.strip(),'追加AGENTSの確認が必要')
    m.need(not WORK.exists(),'作業重複禁止');PUBLIC.mkdir(parents=True)
    pushed=receive(head,observed) if (m.ROOT/REQUEST).exists() else measure(head,observed)
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        if PUBLIC.exists():
            (PUBLIC/'failure.json').write_bytes(m.encode(dict(status='FAILED_NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,
                frames=[dict(source=Path(f.filename).name,line=f.lineno,function=f.name) for f in traceback.extract_tb(exc.__traceback__) if '/scripts/' in f.filename])))
        print(f'RESULT=STOPPED TASK={TASK} VERIFY=FAIL COMMIT=- PHASE={PHASE}')
        sys.exit(1)
