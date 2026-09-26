#!/usr/bin/env python3
"""未受入3活動の限定実装用。旧nativeを起動せず、停止点を同一branchへ保存する。"""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
TASK = 'USER-20260927-RESEARCH-REMAINING'
START = '1e66d9ac887879b4b840f3339e1cb1878d4816c2'
SELF = 'scripts/pr16_research_followup_20260927.py'
WF = '.github/workflows/pr16-research-followup-20260927.yml'
TEST = 'tests/test_pr16_research_followup_20260927.py'
GUIDE = 'docs/PR16_RESEARCH_REMAINING_JA.md'
CODE = {SELF, WF, TEST}
OUT = Path('.local/pr16-research-followup')
CP = 'content/modernization/pr16_research_mining_checkpoint.json'
CANDIDATE = {'size': 33554432, 'sha256': '26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da'}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def activity_contract(model):
    """既存accepted simple-eventと未受入existing-hookを混ぜない。"""
    need(type(model) is dict and type(model.get('activities')) is list, 'activity model')
    rows = model['activities']
    need(len(rows) == 6, 'closed six activity model')
    expected = [('FISHING', 0, 4, 24, 'KANTO_EARLY_ACCESS'),
                ('ECOLOGY_RESEARCH', 1, 10, 50, 'KANTO_EARLY_ACCESS'),
                ('GAME_CORNER', 2, 3, 18, 'KANTO_CERT_2')]
    result = []
    for row, (name, index, points, cap, unlock) in zip(rows[:3], expected):
        need(type(row) is dict, 'activity row')
        need(row.get('activity') == name and type(row.get('index')) is int and row['index'] == index, 'ordered unique activity')
        need(type(row.get('points_awarded')) is int and row['points_awarded'] == points, 'exact RP')
        need(type(row.get('daily_cap')) is int and row['daily_cap'] == cap, 'exact daily cap')
        need(row.get('implementation_mode') == 'EXISTING_HOOK' and row.get('unlock_key') == unlock, 'native hook policy')
        result.append(dict(row))
    need([r.get('activity') for r in rows[3:]] == ['BUG_CATCHING', 'MINING', 'PHOTOGRAPHY'], 'accepted simple events unchanged')
    return result


def inventories(tracked):
    """既知のsource領域だけ。原本やROMやsaveの本文は輸出しない。"""
    roots = ('scripts/', 'tools/', 'config/', 'content/research_economy_v1/', 'overlays/research_economy_v1/')
    terms = ('fishing', 'natural_capture', 'captured_battle', 'special_wild', 'selector', 'game_corner', 'arcade', 'research_economy', 'research_catalog')
    return sorted(p for p in tracked if p.startswith(roots) and Path(p).suffix in {'.py', '.c', '.h', '.json'} and any(t in p.lower() for t in terms))


def inventory():
    import pr16_research_lifecycle_actions as d
    from pr16_learnset_compact_record import publish_resume
    os.chdir(ROOT)
    d.current()
    need(not OUT.exists(), 'fresh execution; do not repeat completed inventory')
    OUT.mkdir(parents=True)
    cp = d.read(CP)
    need(cp['actions_completion_confirmed'] and cp['status'] == 'PASS_MINING_REAL_EARNING_SCOPED' and cp['candidate'] == CANDIDATE, 'accepted mining boundary')
    need(d.bindings(cp['source_bindings']) == cp['source_bindings'], 'accepted source unchanged')
    need(d.bindings(cp['protected_bindings']) == cp['protected_bindings'], 'accepted evidence unchanged')
    tracked = d.git('ls-files').decode().splitlines()
    nested = [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts', 'tools', 'tests', 'content', 'docs', 'design')]
    need(not nested, 'nested rules require review')
    terminal = d.inputs.api('actions/runs/' + str(cp['record_run_id']))
    need(terminal['status'] == 'completed' and terminal['conclusion'] == 'success' and terminal['head_sha'] == cp['record_source_head'], 'previous record terminal success')
    model = d.read('content/research_economy_v1/canonical_model.json')
    contract = activity_contract(model)
    unit = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', Path(TEST).name, '-v'], capture_output=True, timeout=60)
    need(unit.returncode == 0 and (unit.stdout + unit.stderr).count(b' ... ok\n') == 10, 'ten new scoped source tests')
    run = int(os.environ['GITHUB_RUN_ID'])
    base = 'content/modernization/pr16_research_remaining_evidence/' + str(run)
    rows = {}
    for p in inventories(tracked):
        data = Path(p).read_bytes()
        text = data.decode('utf-8')
        lines = text.splitlines()
        symbols = [{'line': i, 'text': line[:220]} for i, line in enumerate(lines, 1)
                   if re.search(r'^(?:def |(?:static )?(?:struct mCore\s*\*|void|bool|int|u8|u16|u32|unsigned|uint\w+_t)\s*\w+\s*\()', line)
                   or re.search(r'FISHING|HIDDEN|GAME_CORNER|REGISTERED_ITEM|KEY_SELECT|fishing|hidden|payout', line)]
        rows[p] = dict(identity(data), lines=len(lines), symbols=symbols[:100])
    runs = d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')['workflow_runs']
    result = dict(schema_version=1, task=TASK, status='SOURCE_CONTRACT_READY_NATIVE_OPEN', source_head=os.environ['GITHUB_SHA'], run_id=run,
                  candidate=CANDIDATE, previous_record=d.run_summary(terminal), activity_contract=contract, source_inventory=rows,
                  source_bindings=d.bindings(CODE), accepted_case_reruns=0, native_processes=0, arm_compiles=0, host_compiles=0,
                  new_scoped_tests=10, all_activities_accepted=False, release_ready=False)
    d.write(base + '/source-contract.json', result)
    d.write(base + '/actions.json', [d.run_summary(r) for r in runs])
    d.write(base + '/unit.json', dict(returncode=unit.returncode, stdout=unit.stdout.decode(), stderr=unit.stderr.decode(), native_processes=0))
    # 保存したsource索引は準備checkpointであり、実RPの受入証拠にしない。
    goal = '未受入3活動のsource契約・前回採掘記録終端を保存済み。PR16_RESEARCH_REMAINING_JA.mdから釣り/生態/ゲームコーナーのnative経路を実装する。SOURCE_CONTRACT_READY_NATIVE_OPENはnative未受入。旧写真/虫取り/採掘を無変更再実行しない。通常進行の受付/ショップ接続・残るnative文言も未完。'
    Path(GUIDE).write_text('# PR16 残る研究活動の実装\n\n' + goal + '\n\nsource契約と検証: `' + base + '/source-contract.json`。新規10検査、native/ARM/host compile 0。\n\n釣り4RP/日24、生態10RP/日50、ゲームコーナー3RP/日18。入力/進行fixtureと実捕獲・配当を区別する。RP・結果・乱数・捕獲状態をbarrier後に注入しない。旧checkpointと候補26dac23cを保持する。\n', encoding='utf-8')
    state = d.read(d.STATE)
    state['research_remaining'] = dict(path=base + '/source-contract.json', status=result['status'], source_head=result['source_head'], run_id=run, new_scoped_tests=10, native_processes=0)
    state['bp']['current_stop'] = result['status']
    state['bp']['next_step'] = goal
    state['next_action'] = dict(state['next_action'], id='RESEARCH_REMAINING_NATIVE_IMPLEMENTATION', goal_ja=goal, read_paths=[GUIDE, base + '/source-contract.json', CP, 'content/research_economy_v1/canonical_model.json', 'overlays/research_economy_v1/research_economy_v1.c'])
    state['observed_head'] = os.environ['GITHUB_SHA']
    state['observed_head_semantics'] = '未受入研究3活動source契約の実行source。前回採掘record run36267783546の終端成功を照合。自己runは未終端として記録する。'
    state['observed_head_checks'] = dict(scope_head=os.environ['GITHUB_SHA'], runs=[d.run_summary(r) for r in runs], reconciliation=base + '/actions.json', reason_ja='前回記録成功と新source契約を分離。自己runの終端は後続で確認。')
    state['pending_runs'] = [dict(run_id=r['id'], tested_head=r['head_sha'], status=r['status']) for r in runs if r['status'] in ('queued', 'in_progress')]
    for p in CODE | {GUIDE, base + '/source-contract.json'}:
        state['source_bindings'][p] = identity(Path(p).read_bytes())
    now = datetime.datetime.now(datetime.timezone.utc)
    state['observed_date_jst'] = now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['logs_synchronized'] = True
    publish_resume(state)
    log = f'\n## {now.isoformat()}\n- Timestamp: {now.isoformat()}\n- Task: {TASK} / 未受入研究3活動の専用実装開始\n- Version: research-remaining-source-v1\n- Status: STOPPED（source契約完成、native実装継続）\n- Summary: 前回採掘記録run36267783546の終端successを照合。釣り/生態/ゲームコーナーの専用source契約と10新規負例検査、対象source索引を実装・保存。実RPの新受入は0。\n- Files changed: 専用script/test/workflow、source-contract/actions/unit、固定引継ぎMD/JSON、専用guide、両ログ。\n- Verify: 新10tests PASS。native/ARM/host compile/受入済み再実行0。既存source/evidence hash不変。最終resume/task graph/scoped guardをcommit前に実行。\n- Commit: source={os.environ["GITHUB_SHA"]};自己SHAはgit log参照。同branchへ非force push。\n- Network: GitHub PR/HEAD/Actions APIのみ。merge/release/baseline変更なし。\n'
    for p in d.LOGS:
        with Path(p).open('a', encoding='utf-8') as f:
            f.write(log)
    owned = {base + '/' + n for n in ('source-contract.json', 'actions.json', 'unit.json')} | {GUIDE, d.STATE, d.DOC} | d.LOGS
    d.write(OUT / 'owned.json', sorted(owned))


def guard():
    import pr16_research_lifecycle_actions as d
    import pr16_learnset_runtime_record as g
    cp = d.read(CP)
    need(d.bindings(cp['source_bindings']) == cp['source_bindings'], 'accepted source unchanged')
    need(d.bindings(cp['protected_bindings']) == cp['protected_bindings'], 'accepted evidence unchanged')
    owned = set(d.read(OUT / 'owned.json'))
    subprocess.run(['git', 'add', '--', *sorted(owned)], check=True)
    g.START = os.environ['GITHUB_SHA']; g.CODE = set(); g.OWNED = owned; g.guard()
    changed = set(d.git('diff', '--cached', '--name-only', START).decode().splitlines())
    need(changed <= owned | CODE, 'explicit complete task scope')
    g.START = START; g.CODE = changed - owned; g.OWNED = owned; g.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)


if __name__ == '__main__':
    os.chdir(ROOT)
    if sys.argv[1:] == ['inventory']:
        inventory()
    elif sys.argv[1:] == ['guard']:
        guard()
    else:
        raise SystemExit('inventory | guard')
