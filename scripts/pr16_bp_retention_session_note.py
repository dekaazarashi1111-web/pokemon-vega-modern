#!/usr/bin/env python3
"""2026-09-14再開時の未反映・ツール停止を記録する。ROM解析/入力復元/実装反映なし。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TASK = 'USER-20260914-BP-RETENTION-RESUME-NOTE'
ENTRY = 'aece42964c1ff7b9c2bfd3d3c10bdd863d95febd'
SELF = 'scripts/pr16_bp_retention_session_note.py'
TEST = 'tests/test_pr16_bp_retention_session_note.py'
WORKFLOW = '.github/workflows/pr16-bp-retention-session-note.yml'
NOTE = ('2026-09-14再開: target呼出位置/ABIの追加検証コードをローカル作成し、新規8testsはPASS。'
        'ただしGitHub create_treeによるコード・workflow追加1回がOpenAI安全性チェックでブロックされ、'
        'branchへ未反映。追加Actions/target照合/runtime接続/native保持検証は未実行。'
        'GitHub権限不足ではない。同一要求を別経路で反復せず、今回は停止記録だけを更新。')
GOAL = ('保存済みWIP48a36caとowner run34785149994を再利用し、未完のtarget呼出位置/ABI照合・'
        '最小successor接続・修復後native個体保持検証を進める。ローカル8testsをtarget照合や'
        '反映済み実装と混同しない。同一tool-blocked要求や既存host4/ownerの単独再実行をせず、'
        '保持確認前に2/3戦目・BP報酬へ進まない。')


def update(source: dict, progress: dict, receipt: dict) -> tuple[dict, dict]:
    """以前の成功/失敗原本を保持し、新しい停止記録だけを追加する。"""
    s, v = copy.deepcopy(source), copy.deepcopy(progress)
    if any(r.get('task') == TASK for r in v.get('followup_attempts', [])):
        raise ValueError('already recorded; do not repeat')
    if receipt.get('task') != TASK or receipt.get('remote_implementation_applied') is not False:
        raise ValueError('not an unapplied session record')
    v.setdefault('followup_attempts', []).append(copy.deepcopy(receipt))
    s['bp']['current_stop'] = NOTE + '\n\n既存native診断: ' + s['latest_native_summary_ja']
    s['bp']['next_step'] = s['next_action']['goal_ja'] = GOAL
    s['party_retention_latest_attempt'] = copy.deepcopy(receipt)
    s['observed_head_checks'] = dict(reason_ja='entry aece429の最新Actionsは本セッション記録のactions_beforeに原値で保存。'
        'action_requiredをSUCCESSへ変更しない。source-only記録の検証とtarget/native検証は別。')
    rule = '2026-09-14ローカルABI案8testsは未反映。target照合/native保持の成功として採用せず、ブロック要求を反復しない。'
    if rule not in s['do_not_repeat']:
        s['do_not_repeat'].append(rule)
    return s, v


def parent():
    sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
    import pr16_bp_party_retention_record as p
    p.ENTRY, p.TASK = ENTRY, TASK
    p.OUT = ROOT / '.local/pr16-bp-retention-session-note'
    p.OUT.mkdir(parents=True, exist_ok=True)
    return p


def record():
    p = parent()
    head = p.git('rev-parse', 'HEAD', text=True).strip()
    p.need(head == os.environ['GITHUB_SHA'] == p.current(), 'concurrent record')
    pr = p.api('pulls/16')
    p.need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head,
           'PR state differs')
    source = p.resume.validate(ROOT)
    progress = p.resume.load(ROOT, p.VERIFIED)
    rows = p.api('actions/runs?head_sha=' + ENTRY + '&per_page=100')
    p.need(rows['total_count'] == len(rows['workflow_runs']), 'incomplete entry Actions')
    latest = {}
    for workflow, run in [('pr16-bp-party-retention.yml', 34785149994),
                          ('pr16-bp-exchange-identity.yml', 34774194505)]:
        r = p.api('actions/workflows/' + workflow + '/runs?branch=codex%2Fmodernization-followup-20260908&per_page=1')['workflow_runs'][0]
        p.need(r['id'] == run and r['conclusion'] == 'success', 'new original needs reconciliation')
        latest[workflow] = p.small(r)
    active = []
    for status in ('in_progress', 'queued'):
        rows_active = p.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&status=' + status + '&per_page=100')
        p.need(rows_active['total_count'] == len(rows_active['workflow_runs']), 'incomplete active Actions')
        active.extend(p.small(r) for r in rows_active['workflow_runs'])
    receipt = dict(task=TASK, entry_head=ENTRY, recording_source_head=head,
        task_status='BLOCKED', remote_implementation_applied=False,
        local_draft_test_count=8, local_draft_test_result='PASS_LOCAL_ONLY_NOT_TARGET_VERIFICATION',
        local_draft_sources={
            'scripts/pr16_bp_party_retention_abi.py': dict(size=9684, sha256='5dfa9c74d483a793ba41884366b63c7c54916ce813016ea1fa4acecc8d9deacd'),
            'tests/test_pr16_bp_party_retention_abi.py': dict(size=3250, sha256='0c785bde0bf07e1612688b528ea7cdb3c6f52e2563c374e1f423b81415ae13a4'),
            '.github/workflows/pr16-bp-retention-abi.yml': dict(size=7285, sha256='070f761f712a7478286cfa43dd7380b2ff53052941314f0e246125a97adaa7a3')},
        blocker=dict(kind='OPENAI_TOOL_SAFETY_BLOCK', tool='GitHub.create_tree', attempts_this_session=1,
            github_permission_missing=False, excerpt='このツールの呼び出しは、OpenAI の安全性チェックによってブロックされました。送信内容を再度確認してください。'),
        new_native_processes=0, accepted_native_cases_replayed=0, candidate_changed=False,
        runtime_connected=False, native_retention_verified=False, release_ready=False,
        actions_before=dict(entry_head_runs=[p.small(r) for r in rows['workflow_runs']], latest=latest,
            active_runs=active, pr_open_draft=True, recording_run_id=int(os.environ['GITHUB_RUN_ID'])))
    s, v = update(source, progress, receipt)
    p.write(p.VERIFIED, p.stable(v))
    for name in (p.VERIFIED, SELF, TEST, WORKFLOW):
        s['source_bindings'][name] = p.ident((ROOT / name).read_bytes())
    b = p.resume.load(ROOT, p.resume.BACKLOG)
    for row in b['remaining_conditions']:
        if row['id'] in ('NATURAL_CAPTURE_GEAR', 'FINAL_NATIVE_ACCEPTANCE'):
            row['resume'] = 'Current resume: ' + p.resume.DOC + '. ' + NOTE + ' Next: ' + GOAL
    p.write(p.resume.BACKLOG, p.stable(b))
    s['logs_synchronized'] = s['p08_resume_synchronized'] = True
    p.write(p.resume.STATE, p.stable(s))
    p.write(p.resume.DOC, p.resume.render(s).encode())
    stamp = datetime.now(timezone.utc).isoformat()
    text = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Version: PR16 resume note\n'
        f'- Task: {TASK} / 未反映ABI案と再開停止の記録\n- Status: BLOCKED\n- Summary: {NOTE}\n'
        '- Files changed: 記録script/tests/workflow、既存WIP JSON、固定引継ぎMD/JSON、P08再開文、両ログ、blockers。target/runtimeファイルは未変更。\n'
        '- Verify: ローカルABI案8tests PASS（未反映・Actions未実行）。記録回帰/resume check/tests、task graph、diff/index guard差分をpublish gateとする。\n'
        '- Native: 今回0process、受入case再実行0、candidate変更0、target ABI/保持は未検証。\n'
        f'- Commit: この記録を含むcommit。entry={ENTRY}、記録入力HEAD={head}。非force push結果はworkflow result.jsonとremote refで確認。\n'
        '- Network: GitHub connectorのread・owner artifact取得・create_tree拒否。記録Actionsはmetadataのみ照会。private入力復元なし。\n'
        '- Block reason: OpenAIツール安全性チェック。GitHub権限エラーではない。追加コード要求1回を拒否、同じ要求の再試行なし。\n'
        '- Error excerpt: このツールの呼び出しは、OpenAI の安全性チェックによってブロックされました。\n'
        '- Question for human: 権限確認の再依頼は不要。正式受入・旧失敗原本を変更しない。\n'
        '- Boundary: BP未受入、physical4/P08ゲート2、PR open/draft、baseline維持。merge/releaseなし。\n'
        f'- Next step: {GOAL}\n')
    for name in p.LOGS:
        old = (ROOT / name).read_bytes()
        p.need(TASK.encode() not in old, 'already logged')
        p.write(name, old + text.encode())
    (p.OUT / 'session.json').write_bytes(p.stable(receipt))
    p.check()


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('record', 'check', 'publish'):
        raise SystemExit('record/check/publish required')
    if sys.argv[1] == 'record':
        record()
    else:
        getattr(parent(), sys.argv[1])()
