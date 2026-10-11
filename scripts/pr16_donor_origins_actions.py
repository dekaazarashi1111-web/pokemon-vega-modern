#!/usr/bin/env python3
"""選定済みoriginの公開symbol束縛、新規検証と固定引継ぎを同branchへ通常記録。"""
from __future__ import annotations
import datetime as dt
import io
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest
import urllib.request
import zipfile
import pr16_donor_origins as m
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=Path(__file__).resolve().parents[1]
START='94d34060a3b3f471c44701d9e3adf8f7e28fec37'
TASK='USER-20261011-DONOR-ORIGIN-SYMBOLS'
BRANCH='codex/modernization-followup-20260908'
PLAN='content/modernization/pr16_donor_window_evidence/windows.json'
PARENT='content/modernization/pr16_donor_window_checkpoint.json'
READER='content/modernization/pr16_forest_wallpaper_reader_checkpoint.json'
STATE='content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE='docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
REPORT='content/modernization/pr16_donor_origins_checkpoint.json'
EVIDENCE='content/modernization/pr16_donor_origins_evidence'
MAP=EVIDENCE+'/symbol-frontier.json'
TESTS=EVIDENCE+'/symbol-tests.txt'
CODE={'scripts/pr16_donor_origins.py','scripts/pr16_donor_origins_actions.py',
      'tests/test_pr16_donor_origins.py','.github/workflows/pr16-donor-origins.yml'}
LOGS={'design/run_log.md','design/version_log.md'}
OUTPUTS={REPORT,MAP,TESTS,STATE,GUIDE,*LOGS}
WORK=ROOT/'.local/pr16-donor-origins'
PUBLIC=WORK/'public'
PHASE='preflight'


def regular(name):
    path=ROOT/name
    m.need(path.is_file() and not path.is_symlink(),'通常file: '+name)
    return path.read_bytes()


def write(name,value):
    a.changed_write(name,m.encode(value) if type(value) is dict else value)


def main():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH
           and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同repo/branch/初回のみ')
    head=a.git('rev-parse','HEAD').decode().strip()
    m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(set(a.git('diff','--name-only',START,head).decode().splitlines())==CODE,'新4source scope')
    m.need(not (ROOT/REPORT).exists() and not WORK.exists(),'測定済みscope再走禁止')
    nested=a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
        'content/AGENTS.md','content/modernization/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    m.need(not nested.strip(),'追加AGENTSの読取りが必要')
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    import json
    state=json.loads(regular(STATE))
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SELECTED_WINDOW_OWNER_COVERAGE'
           and state['owner_execution_plan']['wiki']['review_ready'] is True,'固定next/R0')
    m.need(m.blob(regular(PARENT))=='7dab425f0fc594f0c3c1c59979202087a14edaef','保存窓checkpoint原本')
    m.need(m.blob(regular(READER))=='e6a6d3306d43efef110b3dd79478b119643362ef','保存symbol出典checkpoint')
    protected={PLAN,PARENT,READER,'CHATGPT_RESUME.md','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md',
        'content/modernization/pr16_donor_window_evidence/actions-completion.json'}
    before={n:(m.identity(regular(n)),(ROOT/n).stat().st_mtime_ns) for n in protected}
    PUBLIC.mkdir(parents=True)
    PHASE='new-tests'
    text=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_donor_origins.py')
    tests=unittest.TextTestRunner(stream=text,verbosity=2).run(suite)
    (PUBLIC/'symbol-tests.txt').write_text(text.getvalue())
    m.need(tests.wasSuccessful() and tests.testsRun==20 and not tests.skipped,'新20試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE='fixed-public-symbols'
    symbol=json.loads(regular(READER))['symbol_source']
    # 保存済みの公開source identityへ固定。取得した内容をコードとして実行しない。
    url='https://raw.githubusercontent.com/'+symbol['repository']+'/'+symbol['commit']+'/'+symbol['path']
    with urllib.request.urlopen(url,timeout=90) as response:
        raw=response.read(symbol['size']+1)
    frontier=m.analyze(regular(PLAN),raw,symbol)
    encoded=m.encode(frontier)
    m.need(encoded==m.encode(m.analyze(regular(PLAN),raw,symbol)),'同入力決定的生成')
    write(MAP,encoded);write(TESTS,text.getvalue().encode())
    saved=(regular(MAP),(ROOT/MAP).stat().st_mtime_ns)
    m.need(regular(MAP)==m.encode(m.analyze(regular(PLAN),raw,symbol)),'read-only保存照合')
    m.need(saved==(regular(MAP),(ROOT/MAP).stat().st_mtime_ns),'check byte/mtime不変')
    m.need(before=={n:(m.identity(regular(n)),(ROOT/n).stat().st_mtime_ns) for n in protected},'全固定原本不変')
    PHASE='record'
    goal=('選定窓10originの公開JP symbol近傍を保存済み。先頭0x080A006Fについてsymbol-frontierの出典/行を読み、'
          '固定公開関数sourceと現候補0641af70の有限命令範囲を束縛し、実consumer/命令境界を確認する。'
          '近傍labelだけでownerやFALSE_POSITIVEに昇格しない。窓外跨りread/旧owner内origin/間接参照は残す。'
          '正式785/89・安全容量0。全874scan/Forest/Bubble/窓49試験/symbol20試験の無変更再走禁止。')
    report=dict(schema_version=1,task=TASK,status=frontier['status'],source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,
        candidate=dict(m.CANDIDATE),claims=dict(m.CLAIMS),map_path=MAP,map_identity=m.identity(encoded),
        source_bindings={n:m.identity(regular(n)) for n in sorted(CODE)},
        preserved_input_bindings={n:v[0] for n,v in sorted(before.items())},
        new_unit_tests=20,read_only_check_passed=True,deterministic_generation=True,
        protected_inputs_unchanged=True,task_graph_passed=True,observed_head_checks=observed,next_ja=goal)
    write(REPORT,report)
    state['owner_execution_plan']['technical_lanes']['save_capacity'].update(
        status='SELECTED_ORIGIN_SYMBOLS_BOUND_CONSUMERS_UNPROVEN',checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_FIRST_ORIGIN_SOURCE_AND_CONSUMER',goal_ja=goal,
        read_paths=[GUIDE,REPORT,MAP,'scripts/pr16_donor_origins.py','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'],
        done_ja='最初のoriginの現候補source/命令範囲/実consumerを有限根拠で束縛。symbol近傍だけの受入禁止。')
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_ORIGIN_SYMBOLS_BOUND_SAVE_INTEGRATION_PENDING'
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,new_unit_tests=20,accepted_tests_rerun=0,new_native_processes=0,
        rom_reconstructions=0,read_only_check_passed=True,task_graph_passed=True,classified=785,unclassified=89,donor_safe_bytes=0)
    write(STATE,state)
    old=regular(GUIDE).decode()
    m.need('## 選定10originの固定公開symbol近傍' not in old,'引継ぎ重複拒否')
    old=old.replace('## 次の未完作業','## 窓選定時の停止点（履歴）',1)
    first=frontier['origins'][0]
    label=first['preceding_label']
    label_text='未発見' if label is None else '/'.join(x['name'] for x in label['labels'])
    old+=(f'\n## 選定10originの固定公開symbol近傍\n\n入力HEAD `{head}`。保存済み10行と固定公開JP symbol全hashを照合しました。'
          f'先頭0x080A006Fの直前labelは `{label_text}` です。これは現ROMの関数/asset ownerや命令境界の証明ではありません。\n\n'
          f'[対応表](../{MAP}) / [checkpoint](../{REPORT})。新20試験、同入力決定性、読取専用byte/mtime、task graphを検証。'
          '正式785/89・安全容量0、旧窓計画/reader/R0/ROM/Save101不変。新native/ROM再構成/旧試験再走0。\n\n## 次の未完作業\n\n'+goal+'\n')
    write(GUIDE,old.encode())
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {TASK} / 選定10originの固定公開symbol束縛\n'
        '- Version: donor-origin-symbols-v1\n- Status: DONE（symbol対応付けのみ。実consumer/保存統合は未完）\n'
        '- Summary: 保存窓10originと公開JP symbol全identityを束縛。近傍labelをowner/extentへ昇格せず次のsource/consumer確認へ接続。\n'
        '- Files changed: 新symbol検証器/20試験/専用Actions実行器、checkpoint/対応表、固定引継ぎMD/JSON、両ログ。\n'
        '- Verify: 新20 tests、決定的生成、read-only byte/mtime、旧原本不変、task graph PASS。最終index新規private違反0と全体guard結果を別記録。\n'
        '- Boundary: 正式785/89・安全容量0、R0/旧受入/ROM/Save101/baseline不変。新native/ROM再構成/旧試験再走0。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはGit履歴/Actions resultを参照。\n'
        '- Network: 保存identityに固定した公開JP symbolのGET、指定repo PR/ref/Actions GET、同branch非force pushのみ。\n')
    for name in LOGS:
        old=regular(name);m.need(('- Task: '+TASK+' /').encode() not in old,'同task重複')
        write(name,old+block.encode())
    PHASE='final-index-and-nonforce-push'
    publication.final_index(START,CODE|OUTPUTS,REPORT)
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前競合')
    for name in CODE|OUTPUTS:m.need(a.git('show',':'+name)==regular(name),'最終index全byte')
    a.git('config','user.name','github-actions[bot]')
    a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 選定10originの公開symbol束縛を検証し未証明consumerを記録')
    a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in CODE|OUTPUTS:m.need(a.git('show','HEAD:'+name)==regular(name),'commit blob読戻し')
    for name in (REPORT,MAP): (PUBLIC/Path(name).name).write_bytes(regular(name))
    # 次の有限解析に必要なtracked textのみ。原本ROM/save/ZIPや環境値は含めない。
    context={*CODE,STATE,GUIDE,PLAN,PARENT,READER,'AGENTS.md','README.md','design/current_state.md',
        'design/agent_context_map.md','design/tasks_next.md','scripts/pr16_dex_hof_capacity_actions.py',
        'scripts/pr16_dex_hof_donor.py','scripts/pr16_dex_hof_blastoise_sources.py',
        'scripts/pr16_wiki_r0_reconcile_actions.py','scripts/pr16_wiki_r0_publish.py',
        'content/modernization/pr16_donor_window_evidence/actions-completion.json'}
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(context):z.writestr(name,regular(name))
    (PUBLIC/'result.json').write_bytes(m.encode(dict(status='DONE',task=TASK,commit=pushed,
        source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),new_unit_tests=20,claims=m.CLAIMS)))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        if PUBLIC.exists():
            (PUBLIC/'failure.json').write_bytes(m.encode(dict(status='FAILED_NOT_ACCEPTED',phase=PHASE,
                exception_type=type(exc).__name__,frames=[dict(source=Path(f.filename).name,line=f.lineno,function=f.name)
                    for f in traceback.extract_tb(exc.__traceback__) if '/scripts/' in f.filename])))
        print(f'RESULT=STOPPED TASK={TASK} VERIFY=FAIL COMMIT=- PHASE={PHASE}')
        sys.exit(1)
