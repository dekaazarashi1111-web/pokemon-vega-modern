#!/usr/bin/env python3
"""新scopeの固定親復元・symbol候補束縛・記録。ROM/旧reader/旧試験は実行しない。"""
from __future__ import annotations
import copy
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
import urllib.request
import pr16_capacity_08397492 as m
import pr16_weather_bubble_receipt as parent
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT = Path(__file__).resolve().parents[1]
START = '3240648d4982582c52abde102573ccb686fbec31'
TASK = 'USER-20261010-CAPACITY-08397492-BINDING'
STATE = 'content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE = 'docs/PR16_CAPACITY_08397492_JA.md'
REPORT = 'content/modernization/pr16_capacity_08397492_checkpoint.json'
CODE = {'scripts/pr16_capacity_08397492.py', 'scripts/pr16_capacity_08397492_actions.py',
        'tests/test_pr16_capacity_08397492.py', '.github/workflows/pr16-capacity-08397492.yml'}
LOGS = {'design/run_log.md', 'design/version_log.md'}
OUTPUTS = {STATE, GUIDE, REPORT, *LOGS}
FRONTIER = parent.EVIDENCE + '/unknown-frontier.json'
WORK = ROOT / '.local/pr16-capacity-08397492'


def write(path, value):
    a.changed_write(path, m.encode(value) if type(value) is dict else value)


def run():
    WORK.mkdir(parents=True, exist_ok=True)
    head = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(os.environ.get('GITHUB_REPOSITORY') == a.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/'+parent.BRANCH
           and os.environ.get('GITHUB_RUN_ATTEMPT') == '1', '指定repo/branchの初回runだけ')
    m.need(not (ROOT/REPORT).exists(), 'このbindingは記録済み。再走しない')
    observed = a.live(head)
    changed = set(a.git('diff', '--name-only', START, head).decode().splitlines())
    m.need(changed == CODE, '新scope source4個以外は保全')
    m.need(not a.git('status', '--porcelain', '--untracked-files=no').strip(), '開始tracked clean')
    # 新しい階層規約を見落としたまま書き込まない。
    relevant = {'scripts/AGENTS.md','tests/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md',
                'content/AGENTS.md','content/modernization/AGENTS.md','docs/AGENTS.md','design/AGENTS.md'}
    tracked = set(a.git('ls-files').decode().splitlines())
    m.need(not relevant & tracked, '追加AGENTSを読む必要がある')
    state = parent.read((ROOT/STATE).read_bytes())
    advanced_state = m.binding_state(state)
    m.need(state['next_action']['id'] == 'SAVE_CAPACITY_FROM_PRESERVED_08397492_FRONTIER'
           and state['owner_execution_plan']['wiki']['review_ready'] is True, '固定状態の現在scope')
    receipt = parent.read((ROOT/'content/modernization/pr16_wiki_r0_receipt.json').read_bytes())
    completed_r0 = publication.accepted_run(receipt['actions_run_id'],receipt['source_head'],
        ['R0の新しいfocused試験とtask graph','R0生成または提示receiptを検証して非force反映'])
    for name, meta in receipt['technical_resume_bindings'].items():
        m.need(m.exact(m.identity(parent.regular(ROOT,name)), meta), '受領済みtechnical親不変: '+name)
    stat_before = {n:((ROOT/n).stat().st_mtime_ns,m.identity((ROOT/n).read_bytes()))
                   for n in receipt['technical_resume_bindings']}
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_capacity_08397492.py')
    result = unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    m.need(result.wasSuccessful() and result.testsRun == 28 and not result.skipped, '新focused28試験')
    (WORK/'focused-tests.txt').write_text(log.getvalue())
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    # 保存原本からの復元だけ。既測定consumer/ROM/受入試験は呼ばない。
    audit = parent.restore_parent(ROOT)
    audit_id = m.identity(parent.previous.canonical(audit))
    cp = parent.read((ROOT/parent.CHECKPOINT).read_bytes())
    m.need(m.exact(audit_id,cp['full_audit_identity']), '784親全identity')
    frontier = parent.frontier(audit)
    selected = m.select_target(frontier)
    fraw = parent.regular(ROOT,FRONTIER)
    m.need(m.exact(frontier,parent.read(fraw)), '保存90行全体一致')
    source = m.SYMBOL_SOURCE
    url = 'https://raw.githubusercontent.com/'+source['repository']+'/'+source['commit']+'/'+source['path']
    with urllib.request.urlopen(url, timeout=90) as response:
        raw = response.read(source['size']+1)
    hints = m.bind_symbols(raw)
    m.need(stat_before == {n:((ROOT/n).stat().st_mtime_ns,m.identity((ROOT/n).read_bytes())) for n in stat_before},
           '親byte/mtime無変更')
    report = {'schema_version':1,'task':TASK,'status':'PASS_SAVED_FRONTIER_AND_SYMBOL_BINDING_ONLY',
        'source_head':head,'actions_run_id':int(os.environ['GITHUB_RUN_ID']),
        'actions_completion_confirmed':False,'completed_r0_receipt_actions':completed_r0,
        'candidate':copy.deepcopy(m.CANDIDATE),'inherited_classified':784,'inherited_unclassified':90,
        'parent_audit_identity':audit_id,'saved_frontier_identity':m.identity(fraw),
        'target':selected,'independent_public_symbol_source':copy.deepcopy(source),
        'symbol_candidates':hints,'claims':copy.deepcopy(m.CLAIMS),'focused_tests':28,
        'task_graph_passed':True,'parent_byte_mtime_unchanged':True,'observed_head_checks':observed,
        'code_bindings':{n:m.identity((ROOT/n).read_bytes()) for n in sorted(CODE)},
        'technical_parent_bindings':receipt['technical_resume_bindings'],
        'prior_attempts':[{'run_id':38064450846,'source_head':'98e771a6b9084a4fdebec6b698fb0d510a71e3a8','conclusion':'failure','completion_commit_created':False,'reason_ja':'nested technical_lanes.save_capacityへの記録adapter欠落を修正。検査条件を緩和せず5境界試験を追加。'}],
        'next_ja':'symbol近傍は候補だけ。独立公開sourceの宣言と全assetを固定し、実ROM table/literal/readerの全4byte消費へ結ぶ。型の証明なしに784/90/安全容量0を変更しない。旧Bubble/Blastoiseの再測定、全クリ走破は行わない。'}
    write(REPORT,report)
    guide = ('# 保存容量08397492：保存親と公開symbolの束縛\n\n'
        '**親の復元・新scopeの検証器は完了。asset/reader型の正式受入は未完です。**\n\n'
        f'入力HEAD `{head}`。新Actions `{report["actions_run_id"]}`。28境界試験とtask graph PASS。\n\n'
        'R0は提示・受領済み。Wiki候補6e88a021と容量解析候補0641af70を混同しません。'
        '容量の正式親は784分類/90未知/安全容量0のまま、保存済み原本とsourceをhash照合して復元しました。'
        '既受入のROM・reader・試験を再実行していません。\n\n'
        f'[機械可読checkpoint](../{REPORT}) のtargetは0x08397492の4byteだけです。'
        '独立固定公開TSVの全size/SHA-256/Git blobを確認し、前後labelを有限件だけ保存しました。'
        '近傍・参考size・次labelとの差をasset境界やconsumer証拠へ昇格しません。\n\n'
        '## 次の未完作業\n\n'+report['next_ja']+'\n\n'
        'controller6528byteの安全配置、保存入口ready、退避53300前Free、同期非再入、writer/loader等の本番接続と局所Save/fresh Continueは別の未完gateです。'
        '全クリ走破は対象外でPASSではありません。所有者調整承認0、正式ROM/Save101・baseline不変、merge/releaseなし。'
        '全体private guardと一般CIの既存失敗は、この限定検証のPASSへ読み替えません。\n')
    write(GUIDE,guide.encode())
    state = advanced_state
    state['next_action']={'id':'SAVE_CAPACITY_08397492_ASSET_AND_READER_PROOF',
        'goal_ja':report['next_ja'],'read_paths':[GUIDE,REPORT,'scripts/pr16_capacity_08397492.py',
            'scripts/pr16_weather_bubble_receipt.py','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'],
        'done_ja':'独立全assetと実consumerが一致する場合だけ最小型を受入。成立しない場合は診断と非主張を記録して次の安全容量手段を選ぶ。'}
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_CAPACITY_FRONTIER_BOUND_READER_PENDING'
    state['recording']['last_execution']={'task':TASK,'source_head':head,'actions_run_id':report['actions_run_id'],
        'actions_completion_confirmed':False,'focused_tests':28,'task_graph_passed':True,
        'accepted_tests_rerun':0,'rom_reconstructions':0,'new_native_processes':0}
    write(STATE,state)
    stamp=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 保存容量の固定親と08397492\n'
        '- Version: capacity-08397492-binding-v1\n- Status: DONE\n'
        '- Summary: 784/90の保存親を全identity照合で復元し08397492の唯一hitを束縛。固定公開symbol全4MiBのSHA/size/blobと有限近傍を別証拠化。型/容量は未受入のまま。\n'
        '- Files changed: 新しい有限検証器・28境界試験・実行器/workflow、新checkpoint/guide、現行状態JSON、両ログ。旧原本・Wiki・ROM・Save101・baseline不変。\n'
        '- Verify: 新28 tests/task graph/親byte-mtime/非force競合検査。旧試験・reader・ROM再構成・native各0。全体private guardは既存違反と新規違反を区別。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはGit履歴とActions resultから照合。\n'
        '- Network: 固定公開symbol、GitHub指定repoのPR/ref/Actions GETと同branch非force push。\n')
    for name in LOGS:
        before=(ROOT/name).read_bytes()
        m.need(('- Task: '+TASK+' /').encode() not in before,'同taskは記録済み')
        write(name,before+block.encode())
    publication.final_index(START,CODE|OUTPUTS,REPORT)
    m.need(a.git('ls-remote','origin','refs/heads/'+parent.BRANCH).decode().split()[0]==head,'push前競合')
    for args in [('config','user.name','github-actions[bot]'),
                 ('config','user.email','41898282+github-actions[bot]@users.noreply.github.com'),
                 ('commit','-m',TASK+': 保存親と固定symbolを検証しasset-reader未完を記録'),
                 ('push','origin','HEAD:'+parent.BRANCH)]:
        a.git(*args)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+parent.BRANCH).decode().split()[0]==pushed,'push後HEAD不一致')
    for name in OUTPUTS:
        m.need(a.git('show','HEAD:'+name)==(ROOT/name).read_bytes(),'HEAD読戻し: '+name)
    (WORK/'result.json').write_bytes(m.encode({'status':'DONE','commit':pushed,'source_head':head,'task':TASK}))
    print(json.dumps({'status':'DONE','commit':pushed,'target':m.TARGET,'classified':784,'unclassified':90,'donor_safe_bytes':0}))


if __name__=='__main__':
    run()
