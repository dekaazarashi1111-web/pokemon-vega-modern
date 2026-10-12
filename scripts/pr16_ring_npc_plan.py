#!/usr/bin/env python3
"""所有者指定のNPC配布方針を再開正本へ同期する。ROM/nativeは実行しない。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = '8f76f857c2f17f1be6f8c12653609c0272ad6d73'
TASK = 'USER-20260918-RING-NPC-PLAN'
SELF = 'scripts/pr16_ring_npc_plan.py'
TEST = 'tests/test_pr16_ring_npc_plan.py'
WORKFLOW = '.github/workflows/pr16-ring-npc-plan.yml'
DECISIONS = 'design/decisions.md'
GAP = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
POLICY = 'P05_ORDINARY_POLICY_SELECTION_PHYSICAL'
GOAL = (
    '既存方式でNPCを1人追加するか、進行に無関係と確認できたNPCの会話を差し替え、'
    '最終リーグクリア後にメガリング(item580)を通常のアイテム付与処理で1個渡す。'
    '既存のリング所持判定と通常戦闘のメガ許可判定を接続し、対応メガストーンを持たせたポケモンで'
    '既存の戦闘UIからメガ進化する。NPC受取→実戦→通常Save/fresh Continue後の再利用を先に通す。'
    '別の戦闘前policy選択画面を必須にせず、リング連動解禁と既存戦闘UIへの条件対応を台帳に記録する。'
    '旧story経路の全owner除外やフォント/音声/DMA/セーブ内部の網羅解析を、この実装の前提にしない。')
STOP = (
    '最初の区切りはNPCの安全な配置/会話差替えと正規受取を含む動く最小経路。'
    '新規UIや共通基盤を作り直さず、実際に再現した失敗箇所だけ限定修復する。'
    '取得条件FINAL_LEAGUE_CLEARED・施設禁止/他ギミックとの排他・既存使用回数制限は維持する。'
    'リングは主人公の所持品、ポケモンに持たせるのは対応メガストーン。'
    'BP/P03/P06/P07の受入済みは変更影響なしに再実行しない。'
    'リング連動に必要な通常戦闘の許可判定は同一範囲とし、Circus/最終統合/releaseへ広げない。'
    '未取得対照・付与失敗/二重受取・既存UIでの選択/取消・保存再開を実観測するまで、'
    'Ring/policyの未受入IDを閉じない。')
NO_REPEAT = (
    '2026-09-18所有者方針: 次作業はNPC配布と既存メガUI/所持判定の接続。'
    '以下の履歴にある「次の未読callee」や全owner不存在証明は既定の再開指示ではない。'
    '保存済み低level解析は破棄せず、正規NPC経路で再現した不具合の切分けに必要な箇所だけ参照する。'
    '合成RAM/fixture成功を通常取得に読み替えず、文書更新だけでROM/nativeを再実行しない。')
READ_PATHS = [
    'scripts/build_bp_shop_runtime.py',
    'config/modernization_p04_mega_runtime.json',
    'overlays/cfru/integration.c',
    'scripts/build_battle_core.py',
    'content/modernization/pr16_purchased_gear_acceptance.json',
    'content/modernization/pr16_ring_owner_resolution.json',
]
OBSERVATIONS = [
    '対象NPCのmap/local ID/座標/会話ownerと、進行イベント/共有スクリプト非破壊を確認',
    'FINAL_LEAGUE_CLEARED未達では付与/解禁されず、達成後は実会話でitem580を1個受取',
    '未取得対照、二重受取防止、付与失敗では取得済みにしないことを確認。取消経路がある場合は取消も確認',
    'リング所持を正本に通常戦闘を解禁。追加の永続フラグは必要性がある場合だけ既存save枠へ整合的に接続',
    '対応石を持つポケモンで既存技選択UIからメガ進化・技使用。未所持/不適合石/選択取消の不成立を確認',
    '施設禁止/他ギミック排他/使用回数を維持し、戦闘後に漏洩しない',
    '通常Save→fresh Continue後もリングを保持し、受取時だけの揮発RAM設定に依存せず次戦で利用可能',
    '変更影響台帳と受入条件の対応を記録。実観測前はRing/policy/Circus/P08未受入を維持',
]
POLICY_NOTE = (
    '2026-09-18所有者方針: 通常戦闘のリング連動解禁と既存戦闘UIの選択/不選択/取消を'
    'ordinary policy受入へ対応付ける。独立した戦闘前設定UIは必須にしない。'
    'cold Continue後は所持品から利用可否を再判定し、受取時の揮発NEXT設定だけで代用しない。'
    '仕様対応と証拠を記録するまで元IDは未完のまま保持する。')
STATE_KEYS = {
    'next_action', 'remaining_sequence_ja', 'do_not_repeat', 'ring_npc_plan',
    'handoff_maintenance_task', 'source_change_review_ja', 'session_execution_summary',
    'observed_head', 'observed_head_semantics', 'observed_date_jst', 'observed_head_checks',
}
ROW_KEYS = {
    'NATURAL_CAPTURE_GEAR': {'resume', 'reason_ja', 'ordinary_policy_plan_ja'},
    'FINAL_NATIVE_ACCEPTANCE': {'resume'},
}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def preserved(before: dict, after: dict, ledger_before: dict, ledger_after: dict) -> None:
    """許可した作業案内以外は全フィールドを比較する。受入/候補/履歴は変更不可。"""
    a, b = copy.deepcopy(before), copy.deepcopy(after)
    for key in STATE_KEYS:
        a.pop(key, None); b.pop(key, None)
    for value in (a, b):
        value['bp'].pop('current_stop', None)
        value['bp'].pop('next_step', None)
    need(a == b, '作業案内以外のstate変更')
    a, b = copy.deepcopy(ledger_before), copy.deepcopy(ledger_after)
    for value in (a, b):
        for row in value['remaining_conditions']:
            for key in ROW_KEYS.get(row['id'], set()):
                row.pop(key, None)
    need(a == b, 'P08受入/候補/残件の変更')


def replan(state: dict, backlog: dict) -> tuple[dict, dict]:
    """副作用なし。文書の方針変更であってnative受入の昇格ではない。"""
    need(state['branch'] == 'codex/modernization-followup-20260908', 'branch不一致')
    need(state['latest_native_run'] == 34946969126 and state['bp']['spending_accepted'] is True, 'BP受入境界')
    need(not state['release_ready'] and GAP in state['remaining_physical_gap_ids']
         and POLICY in state['remaining_physical_gap_ids'], '未受入境界')
    if 'ring_npc_plan' in state:
        need(state['ring_npc_plan']['decision_id'] == TASK and state['next_action']['goal_ja'] == GOAL, '既存方針と競合')
        return copy.deepcopy(state), copy.deepcopy(backlog)
    s, b = copy.deepcopy(state), copy.deepcopy(backlog)
    s['ring_npc_plan'] = {
        'decision_id': TASK, 'owner_instruction_at_utc': '2026-09-18T10:21:06Z',
        'based_on_head': BASE, 'status': 'PLAN_ONLY_NOT_IMPLEMENTED_OR_ACCEPTED',
        'preferred_route': 'SAFE_NPC_GIFT_EXISTING_ITEM_GATE_AND_BATTLE_UI',
        'item_id': 580, 'unlock': 'FINAL_LEAGUE_CLEARED',
        'ring_ownership_is_primary': True, 'new_battle_ui_required': False,
        'separate_prebattle_policy_ui_required': False,
        'exhaustive_old_owner_exclusion_required': False,
        'native_cases_replayed': 0, 'rom_changes': 0,
        'previous_stop_ja': state['bp']['current_stop'],
        'previous_next_action': copy.deepcopy(state['next_action']),
        'previous_observed_head_checks': copy.deepcopy(state['observed_head_checks']),
        'policy_acceptance_mapping_ja': POLICY_NOTE,
        'steps_ja': OBSERVATIONS,
    }
    s['bp']['current_stop'] = (
        '2026-09-18所有者指示でNPC配布優先へ方針変更。実装・ROM変更・native再実行は今回0。'
        '直前の351条件/40testsの内部解析成果は履歴として保持するが、その続きを取得機能の必須前提にしない。'
        'BP受入済みを保持し、Ring通常取得・通常戦闘への接続はまだ未受入。')
    s['bp']['next_step'] = GOAL
    s['next_action'].update(id=GAP, goal_ja=GOAL, stop_rule_ja=STOP,
                            read_paths=list(READ_PATHS), success_observations=list(OBSERVATIONS))
    s['remaining_sequence_ja'] = (
        'BP通常購入/保存再開は完了。次は安全なNPCからリングを通常受取し、既存戦闘UIまで通す。'
        'リング連動の通常戦闘許可と既存UIでpolicy条件を満たす対応を記録し、別の戦闘前UI新設は必須にしない。'
        'その後Circus実受付/実戦、P08最終候補固定・変更影響回帰・二重生成・配布判定。'
        'この方針変更だけではphysical3/P08 gates2を閉じない。')
    s['do_not_repeat'].insert(0, NO_REPEAT)
    s['handoff_maintenance_task'] = TASK
    s['source_change_review_ja'] = '所有者指定による次工程/読書順/停止条件の文書変更のみ。ゲーム実装・既存証拠・source bindingsは無変更。'
    s['session_execution_summary'] = dict(new_emulator_processes=0, rom_changes=0,
        candidate_reconstructions=0, accepted_standalone_replays=0,
        scope_ja='NPC配布優先への方針/正本同期のみ。受入済みnative/低level契約を再実行しない。')
    s['observed_head'] = BASE
    s['observed_date_jst'] = '2026-09-18'
    s['observed_head_semantics'] = '方針変更の照合元HEAD。新たなROM/native検証HEADではない。過去の各証拠のsource HEADは原本のまま保持。'
    found = set()
    for row in b['remaining_conditions']:
        if row['id'] == 'NATURAL_CAPTURE_GEAR':
            need(GAP in row['remaining_supply_gap_ids'] and POLICY in row['remaining_supply_gap_ids'], 'P05残件境界')
            row['resume'] = GOAL + ' ' + STOP
            row['reason_ja'] += ' ' + POLICY_NOTE + ' 旧map97/80の全owner解析完了をNPC配布実装の前提にしない。'
            row['ordinary_policy_plan_ja'] = POLICY_NOTE
            found.add(row['id'])
        elif row['id'] == 'FINAL_NATIVE_ACCEPTANCE':
            row['resume'] = (
                '先にNPCによるリング正規取得と既存メガUI/通常戦闘の許可接続、必要なpolicy条件、Circusを完了する。'
                'その後最終SHAを固定し変更ROM範囲/owner/runner/fixture/契約の台帳で既受入を移送する。'
                '影響のないBP/P03/P06/P07を再実行せず、方針変更だけで受入やreleaseへ昇格しない。')
            found.add(row['id'])
    need(found == set(ROW_KEYS), 'P08対象行不足')
    preserved(state, s, backlog, b)
    return s, b


def run() -> None:
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    need(os.environ.get('GITHUB_REPOSITORY') == ops.REPO
         and os.environ.get('GITHUB_REF') == 'refs/heads/' + ops.BRANCH, '実行環境境界')
    head = ops.cmd('git', 'rev-parse', 'HEAD')
    need(head == os.environ['GITHUB_SHA'], 'checkout不一致')
    ops.assert_remote(head, attempts=12)
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, head], cwd=ROOT, check=True)
    need(set(ops.cmd('git', 'diff', '--name-only', BASE, head).splitlines()) == {SELF, TEST, WORKFLOW}, '別変更と競合')
    need(not ops.cmd('git', 'status', '--porcelain', '--untracked-files=no'), '既存tracked差分')
    original = resume.validate(ROOT)
    ledger = resume.load(ROOT, resume.BACKLOG)
    need('ring_npc_plan' not in original, '方針記録済み。再実行不要')
    active = []
    for status in ('queued', 'in_progress'):
        active += ops.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&status='+status+'&per_page=100')['workflow_runs']
    need(not [r for r in active if '/pr16-ring-' in r['path'] and r['id'] != int(os.environ['GITHUB_RUN_ID'])], '別Ring工程が実行中')
    previous = ops.api('actions/runs/35330928644')
    need(previous['head_sha'] == 'a6c076976a7b02bd8599a17abbc42e8ae62e554b'
         and previous['conclusion'] == 'success' and previous['status'] == 'completed', '先行run境界')
    checks = ops.api('actions/runs?head_sha='+BASE+'&event=pull_request&per_page=100')['workflow_runs']
    checkpoint = (ROOT/resume.CHECKPOINT).read_bytes()
    state, backlog = replan(original, ledger)
    state['ring_npc_plan']['prior_run_observed'] = {k: previous[k] for k in ('id', 'head_sha', 'status', 'conclusion')}
    state['observed_head_checks'] = {
        'scope_head': BASE,
        'runs': [{k: r[k] for k in ('id','name','head_sha','status','conclusion')} for r in checks],
        'reason_ja': '方針変更前HEAD '+BASE+'のPR Checksを再照会。各結論はruns参照。'
            '先行run35330928644はsuccessへ完了したことを確認。新規native検証は0。'
            'action_required/過去failureを成功へ読み替えず、この文書変更を全CI greenとは主張しない。',
    }
    preserved(original, state, ledger, backlog)
    resume.dump(ROOT/resume.STATE, state)
    resume.dump(ROOT/resume.BACKLOG, backlog)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], cwd=ROOT, check=True)
    out = ROOT/'.local/pr16-ring-npc-plan'
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for pattern in ('test_pr16_ring_npc_plan.py', 'test_pr16_resume.py'):
        suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern=pattern)
        with (out/(pattern+'.txt')).open('w', encoding='utf-8') as stream:
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        row = dict(pattern=pattern, tests=result.testsRun, failures=len(result.failures),
                   errors=len(result.errors), skips=len(result.skipped), success=result.wasSuccessful())
        results.append(row)
        print(json.dumps(row))
        need(row['success'] and row['tests'] > 0 and row['skips'] == 0, 'focused tests失敗')
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], cwd=ROOT, check=True)
    need((ROOT/resume.CHECKPOINT).read_bytes() == checkpoint, 'BP原本変更')
    preserved(original, resume.load(ROOT, resume.STATE), ledger, resume.load(ROOT, resume.BACKLOG))
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    outputs = (resume.STATE, resume.DOC, resume.BACKLOG, *ops.LOGS, DECISIONS)
    decision = (f'\n\n## {stamp} — {TASK}\n'
        '- Owner request: 2026-09-18T10:21:06Z、次作業をNPC配布と既存メガUI接続へ書き換える。今回の許可範囲は案内/台帳/記録の同期。\n'
        '- Decision: '+GOAL+'\n- Boundaries: '+STOP+'\n'
        '- Policy mapping: '+POLICY_NOTE+'\n'
        '- Rationale: NPC追加の既存方式とitem580所持ゲート/戦闘UIを再利用。元story経路や共通基盤の網羅解析を機能実装の必須前提にしない。\n'
        '- Historical evidence: 旧停止点/次actionはresume JSONのring_npc_planへ保存。解析JSON、正式checkpoint、成功/失敗の原本、候補identityは無変更。\n'
        '- Status: 方針採用のみ。ゲーム実装/ROM変更/native実行0。physical3/P08 gates2は未完を維持。\n')
    count = sum(r['tests'] for r in results)
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n'
        f'- Task: {TASK} / 次作業をNPC配布と既存メガUI接続へ変更\n'
        '- Status: DONE / 引継ぎ方針更新のみ。Ringの実装・受入完了ではない。\n'
        '- Version: pr16-ring-npc-plan\n- Summary: '+GOAL+'\n'
        '- Files changed: '+', '.join((SELF, TEST, WORKFLOW, *outputs))+'\n'
        f'- Verify: 方針/非昇格と既存resumeのfocused {count} tests PASS、render/check、task graph、BP checkpoint byte不変。最終index guardとdiff checkはcommit前に必須。\n'
        '- Preserved: ROM変更0、候補再生成0、emulator0、受入済みnative/低level契約の再実行0。\n'
        f'- Commit: 本記録を含むcommit。照合元={BASE}、実行source={head}、run={os.environ["GITHUB_RUN_ID"]}。最終SHAはremote ref/Actionsで確認。\n'
        '- Network: GitHub connector/Actionsのref、PR、run/Checksのみ。private Release/外部技術資料の取得なし。\n'
        '- Boundary: 既存全体guardの前後一致と新規違反0を確認して非force反映。全体guard/全CI成功やmerge/release/baseline変更は主張しない。\n'
        '- Next: 安全なNPC配置/会話差替えから正規受取を実装し、既存UIでの実戦/保存再開まで通す。\n')
    for name, text in [(DECISIONS, decision), *[(n, entry) for n in ops.LOGS]]:
        path = ROOT/name
        need(TASK not in path.read_text(encoding='utf-8'), '記録重複')
        with path.open('a', encoding='utf-8') as stream:
            stream.write(text)
    subprocess.run(['git', 'add', '--', *outputs], cwd=ROOT, check=True)
    guard.BASE, guard.OUT, guard.ALLOWED = BASE, out, set((SELF, TEST, WORKFLOW, *outputs))
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, check=True)
    ops.assert_remote(head)
    for key, value in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):
        subprocess.run(['git','config',key,value], cwd=ROOT, check=True)
    subprocess.run(['git','commit','-m',TASK+': 次作業をNPC配布と既存メガUI接続へ変更'], cwd=ROOT, check=True)
    commit = ops.cmd('git','rev-parse','HEAD')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH], cwd=ROOT, check=True)
    ops.assert_remote(commit, attempts=12)
    for name in outputs:
        need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT) == (ROOT/name).read_bytes(), '記録byte不一致')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'), 'tracked差分残存')
    receipt = dict(status='PASS_PLAN_RECORDED_NONFORCE_PUSHED', task=TASK, commit=commit,
        source_head=head, run_id=int(os.environ['GITHUB_RUN_ID']), tests=results,
        outputs=list(outputs), new_emulator_processes=0, rom_changes=0,
        ring_acquisition_accepted=False, release_ready=False)
    (out/'recorded-result.json').write_bytes(ops.stable(receipt))
    print(json.dumps(receipt,ensure_ascii=False))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+commit)


if __name__ == '__main__':
    need(sys.argv[1:] == ['run'], 'runだけを許可')
    run()
