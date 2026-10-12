#!/usr/bin/env python3
"""PR16の限定引継ぎ生成/整合性検査。ROM・network・emulatorは使用しない。"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
TASK = 'USER-20260913-RESUME-OPTIMIZATION'
MARKER = '<!-- pr16-stable-resume-route -->'
ROUTE_PATHS = ('AGENTS.md', 'README.md', 'design/current_state.md', 'design/agent_context_map.md')
HISTORY_PATHS = ('docs/PR16_BP_TRIAL_RESUME_20260913_JA.md', 'docs/PR16_NATIVE_SUPPLY_RESUME_20260912_JA.md')


def require(value: Any, message: str) -> None:
    if not value:
        raise ValueError(message)


def safe_path(root: Path, name: str) -> Path:
    rel = Path(name)
    require(isinstance(name, str) and not rel.is_absolute() and '..' not in rel.parts and '\\' not in name, 'unsafe path')
    path = root / rel
    require(path.is_relative_to(root), 'outside root')
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlink path')
    return path


def load(root: Path, name: str) -> dict:
    value = json.loads(safe_path(root, name).read_text(encoding='utf-8'))
    require(isinstance(value, dict), f'{name}: expected object')
    return value


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def pending_ids(backlog: dict) -> tuple[list[str], list[str]]:
    physical, gates = [], []
    for row in backlog['remaining_conditions']:
        if row.get('complete') is True:
            continue
        physical.extend(row.get('remaining_supply_gap_ids', []))
        physical.extend(row.get('remaining_physical_gap_ids', []))
        if row['id'] == 'PHYSICAL_CIRCUS_ADMISSION':
            physical.append(row['id'])
        if row.get('phase') == 'P08':
            gates.append(row['id'])
    return sorted(set(physical)), sorted(set(gates))


def render(s: dict) -> str:
    bp, c, action, protocol = s['bp'], s['candidate'], s['next_action'], s['session_protocol']
    latest_label = '最新scoped受入' if s['latest_native_scope'] == 'SCOPED_ACCEPTANCE' else '最新診断'
    lines = [
        '# PR #16 固定再開メモ', '',
        '> 入口は常に `CHATGPT_RESUME.md`。この文書と対応JSONだけが最新の再開点。',
        '> ファイル名の日付は固定識別子。セッションごとに別名コピーを作らない。',
        '> この文書は `python3 scripts/pr16_resume.py render` で生成する。直接二重編集しない。', '',
        '## いまの停止点と次の1手', '', bp['current_stop'], '',
        f"**次: {action['goal_ja']}**", '', action['stop_rule_ja'], '',
        f"branch: `{s['branch']}` / PR #{s['pr_number']}（記録時 {s['pr_state']}, draft={str(s['pr_draft']).lower()}）。", '',
        f"証拠のsource HEAD: `{s['observed_head']}`。", s['observed_head_semantics'], '',
        '## 最短の再開手順', '', protocol['start_ja'], '',
        'まず `AGENTS.md` → この文書 → `'+STATE+'` を読む。',
        '受入判定・ROM変更前に `'+CHECKPOINT+'` と `'+BACKLOG+'` を照合する。',
        '次の実装で読むのは次のファイルから。環境の問題がある時だけ `docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md` を追加する。', '',
        *['- `'+x+'`' for x in action['read_paths']], '',
        protocol['freshness_ja'], '', protocol['reuse_ja'], '',
        '## 正式受入と診断を混同しない', '',
        f"正式BP checkpoint: run `{s['last_accepted_native_run']}` / HEAD `{s['last_accepted_native_tested_head']}`。",
        s['accepted_scope_summary_ja'], '',
        f"{latest_label}: run `{s['latest_native_run']}` / job `{s['latest_native_job']}` / HEAD `{s['latest_native_tested_head']}`。",
        f"照合抄録: `{s['latest_native_evidence']}`。", s['latest_native_summary_ja'], '',
        action['host_write_policy_ja'], '',
        '## 候補identityと残件', '',
        f"SHA-256 `{c['sha256']}` / {c['size']} bytes / CRC32 `{c['crc32']}`。{s['candidate_scope_ja']}", '',
        '正式physical残件（台帳から照合）:', '',
        *['- `'+x+'`' for x in s['remaining_physical_gap_ids']], '',
        'P08ゲート:', '', *['- `'+x+'`' for x in s['remaining_p08_gate_ids']], '',
        bp['after_battle_launch'], '',
        s['remaining_sequence_ja'], '',
        '## 再実行・過大主張の禁止', '', *['- '+x for x in s['do_not_repeat']], '',
        '## 次セッションへ残す更新手順', '', protocol['write_ja'], '',
        '```bash', 'python3 scripts/pr16_resume.py render', 'python3 scripts/pr16_resume.py check',
        'python3 -m unittest discover -s tests -p test_pr16_resume.py -v', '```', '',
        '`check`は読取専用。hashの変更だけで証拠を追認しない。対象sourceが変わった場合は適用範囲を再評価する。',
        protocol['concurrency_ja'], '', protocol['end_ja'], '',
        '## 履歴の位置づけ', '', s['read_policy']['history_rule_ja'], '',
        *['- `'+x+'`' for x in s['read_policy']['history_only']], '',
        'PR本文は更新失敗の履歴があり、再開入口に使わない。受付取消checkpointの `next` も受入時点の履歴であり、次の作業順はこの文書を優先する。', '',
        '## Checks・releaseの境界', '', s['observed_head_checks']['reason_ja'], '',
        'merge・draft解除・active baseline切替・release公開はこの引継ぎ作業に含めない。受入済み原本、既存公開方針、過去guard結果は変更しない。', ''
    ]
    return '\n'.join(lines)


def validate_spending(root: Path, d: dict, s: dict, control: dict) -> None:
    """3勝単体受入とは別に、通常購入と再起動後の原本を要求する。"""
    r = d['native_result']
    require(r['scope'] == 'PR16_P05_NATIVE_BP_SPENDING_PHYSICAL'
            and r['status'] == 'PASS_NATIVE_BP_SPENDING_SAVE_CONTINUE', 'spending scope/status differs')
    exact = {
        'base_reward_bp': 9, 'active_repeat_reward_bp': 3, 'reward_wrapper_saves': 3,
        'bp_before_purchase': 12, 'bp_after_purchase': 8, 'bp_after_continue': 8,
        'item_id': 195, 'catalog_index': 0, 'price_bp': 4, 'purchase_result': 0,
        'item_count_before': 0, 'item_count_after_purchase': 1, 'item_count_after_continue': 1,
        'save_counter_before_purchase': 5, 'save_counter_after_purchase': 6,
        'save_counter_after_manual': 7, 'save_counter_after_continue': 7,
        'physical_shop_local_id': 3, 'automatic_saves': 1, 'manual_saves': 1,
        'fresh_cores': 2, 'p05_native_bp_spending_closed': True,
    }
    for key, expected in exact.items():
        require(type(r[key]) is type(expected) and r[key] == expected, 'spending '+key+' differs')
    frames = [r[k] for k in ('reward_complete_frame', 'reward_settled_frame',
        'reward_field_frame', 'shop_interaction_frame', 'shop_menu_frame',
        'purchase_frame', 'manual_save_frame', 'continue_frame')]
    require(all(type(f) is int for f in frames) and all(a < b for a, b in zip(frames, frames[1:]))
            and frames[-1] == r['total_frames'], 'spending frame chain differs')
    require(control['physical_bp_spending_accepted'] is True
            and control['spending_success_evidence'] == s['latest_native_evidence'], 'P08 spending evidence differs')
    original = d['verification']['raw_result']
    raw = safe_path(root, original['path']).read_bytes()
    require(len(raw) == original['size'] and hashlib.sha256(raw).hexdigest() == original['sha256'], 'spending raw identity differs')
    row = json.loads(raw)
    projected = dict(row, first_battle_outcome=row['battle_outcome'],
        native_battle_wins_observed=sum(row[k] == 1 for k in
            ('battle_outcome', 'second_battle_outcome', 'third_battle_outcome')))
    require(projected == r, 'spending raw projection differs')
    require(d['verification']['native_validator_passed'] is True
            and d['verification']['visual_review']['completed'] is True, 'spending verification incomplete')
    require(d['process']['raw_native_fresh_cores'] == 2, 'spending fresh core accounting differs')
    for key in ('bp_before_purchase', 'bp_after_purchase', 'bp_after_continue',
                'item_count_after_purchase', 'item_count_after_continue'):
        require(s['bp'][key] == r[key], 'spending state '+key+' differs')


def validate(root: Path, *, check_doc: bool = True) -> dict:
    s = load(root, STATE)
    require(s['schema_version'] == 2, 'unsupported resume schema')
    require(s['stable_entrypoint'] == 'CHATGPT_RESUME.md' and s['current_resume_doc'] == DOC, 'resume routing differs')
    require(s['current_checkpoint'] == CHECKPOINT, 'acceptance authority differs')
    require(s['branch'] == 'codex/modernization-followup-20260908' and s['pr_number'] == 16, 'wrong PR/branch')
    c = s['candidate']
    require(re.fullmatch('[0-9a-f]{64}', c['sha256']) and re.fullmatch('[0-9A-F]{8}', c['crc32']), 'invalid ROM identity')
    require(type(c['size']) is int and c['size'] > 0, 'invalid ROM size')
    require(re.fullmatch('[0-9a-f]{40}', s['observed_head']), 'invalid observed source HEAD')
    checkpoint, backlog = load(root, CHECKPOINT), load(root, BACKLOG)
    require(s['last_accepted_native_run'] == checkpoint['latest_native_run'], 'last accepted run differs')
    require(s['last_accepted_native_tested_head'] == checkpoint['latest_native_head'], 'accepted HEAD differs')
    require(s['latest_native_job'] == checkpoint['latest_native_job'], 'accepted job differs')
    require(isinstance(checkpoint['candidate'], dict) and all(checkpoint['candidate'][k] == c[k] for k in ('sha256', 'size', 'crc32')), 'candidate differs from checkpoint')
    require(s['bp']['cancellation_save_continue_accepted'] is checkpoint['native_rental_cancel_save_continue_accepted'], 'cancel acceptance differs')
    require(s['bp']['earning_and_spending_accepted'] is (checkpoint['native_bp_earning_accepted'] and checkpoint['native_bp_spending_accepted']), 'BP acceptance differs')
    require(s['bp']['earning_accepted'] is checkpoint['native_bp_earning_accepted'], 'earning acceptance differs')
    require(s['bp']['spending_accepted'] is checkpoint['native_bp_spending_accepted'], 'spending acceptance differs')
    physical, gates = pending_ids(backlog)
    for key, expected in [('remaining_physical_gap_ids', physical), ('remaining_p08_gate_ids', gates)]:
        require(isinstance(s[key], list) and len(s[key]) == len(set(s[key])) and sorted(s[key]) == expected, key+' differs from P08')
    require(all(backlog['next_integration_candidate']['candidate'][k] == c[k] for k in ('sha256', 'size', 'crc32')), 'candidate differs from P08')
    require(checkpoint['physical_gap_count'] == len(physical), 'checkpoint physical gap count differs')
    p05_control = backlog['p05_native_bp_control_checkpoint']
    require(p05_control['physical_bp_earning_accepted'] is checkpoint['native_bp_earning_accepted'], 'P08 BP earning acceptance differs')
    for key in ('release_ready', 'merge_performed', 'active_baseline_changed'):
        require(type(s[key]) is bool, key+' must be boolean')
    require(s['release_ready'] is backlog['release_ready'], 'release status differs')
    if physical or gates:
        require(not s['release_ready'], 'pending gates overstated')
    if physical:
        require(not c['final_product_sha_fixed'] and not c['full_candidate_regression_complete'], 'physical gaps overstated')
    d = load(root, s['latest_native_evidence'])
    require(s['latest_native_scope'] == d['classification'] and d['classification'] in ('DIAGNOSTIC_ONLY_NOT_ACCEPTANCE', 'SCOPED_ACCEPTANCE'), 'evidence scope differs')
    if d['classification'] == 'SCOPED_ACCEPTANCE':
        require(d['run_id'] == checkpoint['latest_native_run'], 'acceptance missing from checkpoint')
    require(s['latest_native_run'] == d['run_id'] and s['latest_native_job'] == d['job_id'], 'latest run/job differs')
    require(s['latest_native_tested_head'] == d['tested_head'], 'diagnostic HEAD differs')
    r = d['native_result']
    spending = d.get('scope') == 'PR16_P05_NATIVE_BP_SPENDING_PHYSICAL'
    require(r['candidate_sha256'] == c['sha256'] and s['status'] == r['status'], 'diagnostic identity/status differs')
    if 'candidate' in d:
        require(isinstance(d['candidate'], dict) and all(d['candidate'][k] == c[k] for k in ('sha256', 'size', 'crc32')), 'evidence candidate differs')
    for key in ('battle_started', 'bp_earned', 'selected_frame', 'second_chooser_frame'):
        if key in s['bp']:
            require(type(s['bp'][key]) is type(r[key]) and s['bp'][key] == r[key], 'diagnostic '+key+' differs')
    if d['classification'] == 'DIAGNOSTIC_ONLY_NOT_ACCEPTANCE':
        require(r['native_bp_earning_accepted'] is False and r['p05_native_bp_gap_closed'] is False and r['release_ready'] is False, 'diagnostic claims acceptance')
    else:
        require(checkpoint['native_bp_earning_accepted'] is True, 'scoped acceptance missing BP earning checkpoint')
        require(checkpoint['native_bp_spending_accepted'] is spending, 'scoped acceptance BP spending checkpoint differs')
        require(checkpoint['p05_native_bp_gap_closed'] is True, 'scoped acceptance missing P05 BP gap closure')
        require(p05_control['earning_success_evidence'] == s['latest_native_evidence'], 'P08 BP earning evidence differs')
        require(backlog['next_integration_candidate']['source_path'] == s['latest_native_evidence'], 'P08 candidate evidence differs')
        for key, expected in (
            ('native_three_win_reward_accepted', True),
            ('native_bp_earning_accepted', True),
            ('native_bp_spending_accepted', spending),
            ('native_exchange_accepted', False),
            ('p05_native_bp_gap_closed', True),
            ('release_ready', False),
            ('merge_performed', False),
            ('active_baseline_changed', False),
        ):
            require(d[key] is expected, 'scoped acceptance '+key+' differs')
        for key, expected in (
            ('battle_started', True),
            ('first_battle_outcome', 1),
            ('second_battle_outcome', 1),
            ('third_battle_outcome', 1),
            ('native_battle_wins_observed', 3),
            ('bp_before_reward', 0),
            ('bp_after_reward', 9),
            ('bp_delta', 9),
            ('bp_earned', 9),
            ('special_result', 9),
            ('reward_final_streak', 3),
            ('reward_final_pending', 0),
            ('reward_final_marker', 0),
            ('reward_final_snapshot_valid', 0),
            ('original_party_restored_bytes', 600),
            ('host_write_barriers', 7),
            ('input_only_after_guard', True),
            ('warnings_errors', 0),
            ('manual_saves', 1 if spending else 0),
            ('native_three_win_reward_accepted', True),
            ('native_bp_earning_accepted', True),
            ('native_bp_spending_accepted', spending),
            ('native_exchange_accepted', False),
            ('p05_native_bp_gap_closed', True),
            ('release_ready', False),
        ):
            require(type(r[key]) is type(expected) and r[key] == expected, 'scoped acceptance '+key+' differs')
        process = d['process']
        require(process['returncode'] == 0 and process['timed_out'] is False and process['spawn_error'] is None, 'scoped acceptance process failed')
        require(process['actual_new_processes'] == 1 and process['successful_fresh_cores'] == 1, 'scoped acceptance process count differs')
        prefix = d['accepted_prefix']
        require(prefix['same_candidate'] is True and prefix['accepted_native_cases_replayed'] == 0, 'scoped acceptance prefix differs')
        guard = d['verification']['artifact_guard']
        require(guard['tracked_snapshot_utf8_only'] is True and guard['credential_pattern_hits'] == 0 and guard['rom_save_patch_bytes_published'] is False, 'scoped acceptance artifact guard differs')
        for state_key, result_key in (
            ('bp_before_reward', 'bp_before_reward'),
            ('bp_after_reward', 'bp_after_reward'),
            ('bp_delta', 'bp_delta'),
            ('bp_earned', 'bp_earned'),
            ('native_battle_wins_observed', 'native_battle_wins_observed'),
            ('reward_complete_frame', 'reward_complete_frame'),
            ('original_party_restored_bytes', 'original_party_restored_bytes'),
        ):
            require(type(s['bp'][state_key]) is type(r[result_key]) and s['bp'][state_key] == r[result_key], 'scoped acceptance state '+state_key+' differs')
        require(s['bp']['native_three_win_reward_accepted'] is True, 'scoped acceptance state flag differs')
        if spending:
            validate_spending(root, d, s, p05_control)
    require(re.fullmatch('[A-Z0-9_]+', s['next_action']['id']) and s['next_action']['goal_ja'], 'invalid next action')
    require(s['bp']['next_step'] == s['next_action']['goal_ja'], 'next-action mirrors differ')
    require(s['source_bindings'], 'missing source bindings')
    for name, meta in s['source_bindings'].items():
        raw = safe_path(root, name).read_bytes()
        require(len(raw) == meta['size'] and hashlib.sha256(raw).hexdigest() == meta['sha256'], 'stale source: '+name)
    require(isinstance(s['pending_runs'], list), 'pending runs must be explicit')
    for item in s['pending_runs']:
        require(type(item['run_id']) is int and re.fullmatch('[0-9a-f]{40}', item['tested_head']) and item['status'] in ('queued','in_progress'), 'invalid pending run')
    for name in s['next_action']['read_paths']:
        require(safe_path(root, name).is_file(), 'missing next-action source: '+name)
    if check_doc:
        require(safe_path(root, DOC).read_text(encoding='utf-8') == render(s), 'Markdown drift: run render')
    return s


def install_routing(root: Path) -> None:
    """明示install時だけ案内を追加。既存本文・受入台帳の条件は保存する。"""
    s = load(root, STATE)
    touched = ROUTE_PATHS + HISTORY_PATHS + (BACKLOG,)
    # 既存の不一致を更新処理で隠さない。全対象を変更前に照合する。
    for name in touched:
        if name in s['source_bindings']:
            raw = safe_path(root, name).read_bytes()
            expected = s['source_bindings'][name]
            require(len(raw) == expected['size'] and hashlib.sha256(raw).hexdigest() == expected['sha256'],
                    'stale routing input: '+name)
    for name in ROUTE_PATHS + HISTORY_PATHS:
        p = safe_path(root, name)
        text = p.read_text(encoding='utf-8')
        if MARKER in text:
            continue
        note = ('> **履歴資料。現在の再開入口ではありません。**' if name in HISTORY_PATHS else '> **PR #16再開時の専用入口（一般タスク選択より優先）**')
        block = '\n'+MARKER+'\n'+note+'\n> repository rootの `CHATGPT_RESUME.md` を読み、そこから指定された固定MD/JSONを使う。\n> 日付の新旧やこの下の過去checkpointから現在地を推測しない。`AGENTS.md` の安全・検証規約は引き続き適用する。\n<!-- /pr16-stable-resume-route -->\n'
        title, sep, rest = text.partition('\n')
        p.write_text(title+sep+block+rest, encoding='utf-8')
    backlog = load(root, BACKLOG)
    for row in backlog['remaining_conditions']:
        if row['id'] in ('NATURAL_CAPTURE_GEAR', 'FINAL_NATIVE_ACCEPTANCE'):
            row['resume'] = 'Current resume: '+DOC+'. '+s['bp']['current_stop']+' Next: '+s['bp']['next_step']
    backlog['current_resume_doc'] = DOC
    safe_path(root, BACKLOG).write_text(json.dumps(backlog, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    for name in touched:
        if name in s['source_bindings']:
            raw = safe_path(root, name).read_bytes()
            s['source_bindings'][name] = dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    s['p08_resume_synchronized'] = True
    dump(safe_path(root, STATE), s)
    safe_path(root, DOC).write_text(render(s), encoding='utf-8')


def record_logs(root: Path, source_head: str, timestamp: str) -> None:
    """CIのfocused検証成功後に明示実行。履歴は追記のみ。自己commit SHAを追わない。"""
    validate(root)
    require(re.fullmatch('[0-9a-f]{40}', source_head), 'invalid source HEAD')
    require(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', timestamp), 'invalid timestamp')
    common = (f'\n\n## {timestamp} — {TASK}\n'
        f'- Task: {TASK} / 固定再開入口・正本同期・再読削減\n'
        '- Status: DONE\n'
        '- Summary: CHATGPT_RESUME.mdを不変入口にし、現行MDをJSONから生成。最新3体選択診断を正式受入と分離して反映。旧入口に履歴案内を追加し、P08再開文だけを同期。\n'
        '- Files changed: CHATGPT_RESUME.md、現行resume MD/JSON、診断抄録、scripts/pr16_resume.py、tests/test_pr16_resume.py、専用workflow、AGENTS/README/current_state/context_map、旧MDの案内、p08_remaining_work.json、両ログ。\n'
        '- Verify: focused unittest、pr16_resume.py check、validate_task_graph.py、git diff --check PASS。標準private guardの既存違反と新規差分はworkflowのguard-boundary.jsonで別記。全体guard PASSとは主張しない。\n'
        '- Native: 原本47member/71sourceを再照合、新規emulator0、ROM/save変更0、追加BP受入0。\n'
        f'- Commit: この記録を含むcommit。検証入力HEAD={source_head}。自己SHAを文書へ追記して無限更新しない。\n'
        '- Network: GitHub connectorのbranch/PR/run/artifactを照会。run34734806603、artifact10310995889。private Release取得なし。\n'
        '- Boundary: 未merge/draft維持、release/active baseline変更なし。正式残件physical4/P08ゲート2。\n')
    for name in ('design/run_log.md', 'design/version_log.md'):
        p = safe_path(root, name)
        with p.open('r', encoding='utf-8') as f:
            existing = f.read()
        if TASK not in existing:
            with p.open('a', encoding='utf-8') as f:
                f.write(common)
    s = load(root, STATE)
    s['logs_synchronized'] = True
    dump(safe_path(root, STATE), s)
    safe_path(root, DOC).write_text(render(s), encoding='utf-8')



def guard_index(root: Path, base: str) -> None:
    """標準guardを変更せず、基点/最終indexと今回の追加違反を別計上する。"""
    import collections
    import importlib.util
    import os
    import subprocess
    import sys
    import tempfile
    require(re.fullmatch('[0-9a-f]{40}', base), 'invalid guard base')
    spec = importlib.util.spec_from_file_location('guard_private_files', root/'scripts/guard_private_files.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    def git(*args, env=None):
        return subprocess.check_output(['git', *args], cwd=root, env=env)
    paths = git('diff', '--cached', '--name-only', '-z', base).decode().split('\0')
    paths = [p for p in paths if p]
    allowed = set(ROUTE_PATHS + HISTORY_PATHS + (STATE, DOC, BACKLOG, 'CHATGPT_RESUME.md',
        'content/modernization/pr16_bp_selection_diagnostic.json', 'scripts/pr16_resume.py',
        'tests/test_pr16_resume.py', '.github/workflows/pr16-resume-maintenance.yml',
        'design/run_log.md', 'design/version_log.md'))
    require(set(paths) <= allowed, 'unexpected changed path; no overwrite or acceptance edit allowed')
    violations = []
    for name in paths:
        after = git('show', ':'+name)
        before_proc = subprocess.run(['git','show',base+':'+name],cwd=root,capture_output=True)
        before = before_proc.stdout if before_proc.returncode == 0 else b''
        after.decode('utf-8')
        require(b'\0' not in after and Path(name).suffix in ('.md','.json','.py','.yml'), 'non-text maintenance file')
        def bad_lines(raw):
            lines = raw.decode('utf-8', errors='replace').splitlines()
            return collections.Counter(lines[n-1] for n in guard.document_user_path_lines(raw))
        if bad_lines(after) - bad_lines(before):
            violations.append(name)
        if Path(name).suffix.lower() in guard.BLOCKED_SUFFIXES or any(name == part or name.startswith(part+'/') for part in guard.BLOCKED_PARTS):
            violations.append(name)
    out = root/'.local/pr16-resume'
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp)/'baseline.index'))
        git('read-tree',base,env=env)
        command = [sys.executable, str(root/'scripts/guard_private_files.py')]
        before = subprocess.run(command,cwd=root,env=env,capture_output=True)
        after = subprocess.run(command,cwd=root,capture_output=True)
    report = {'schema_version':1,'base':base,'changed_path_count':len(paths),
        'full_index_guard_before_returncode':before.returncode,
        'full_index_guard_after_returncode':after.returncode,
        'new_changed_path_violations':len(violations),
        'full_guard_pass_claimed':after.returncode == 0,
        'historical_results_relabelled':False,'rom_changes':0,'new_emulator_processes':0}
    dump(out/'guard-boundary.json', report)
    require(before.returncode in (0,1) and after.returncode in (0,1), 'guard execution failed')
    require(not violations, 'new private guard violation in maintenance diff')
    require(before.returncode != 0 or after.returncode == 0, 'full guard regressed')
    print(json.dumps(report,sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'render', 'install-routing', 'record-logs', 'guard'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--source-head')
    parser.add_argument('--timestamp')
    parser.add_argument('--base')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == 'render':
            s = validate(root, check_doc=False)
            safe_path(root, DOC).write_text(render(s), encoding='utf-8')
        elif args.command == 'install-routing':
            install_routing(root)
        elif args.command == 'guard':
            require(args.base, 'guard requires --base')
            guard_index(root, args.base)
        elif args.command == 'record-logs':
            require(args.source_head and args.timestamp, 'record-logs requires source HEAD and timestamp')
            record_logs(root, args.source_head, args.timestamp)
        validate(root)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.exit(1, f'RESUME_FAIL: {exc}\n')
    print('RESUME_PASS: fixed entry, evidence scope, candidate, backlog, sources and Markdown')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
