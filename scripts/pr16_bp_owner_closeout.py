#!/usr/bin/env python3
"""固定source監査の原文保存と同一再開MD/JSON・両ログ同期。ROM/emulatorは実行しない。"""
from __future__ import annotations

import collections
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
START = '5a9d2f89461c286625581a5e7a1ef9344b0e647a'
TESTED = '9e435e551598c2b99046c7aaff1bff6da1721da3'
TASK = 'USER-20260913-BP-LOSS-RETURN-OWNER'
BASE = 'content/modernization/pr16_bp_loss_return_owner_evidence'
REPORT = 'content/modernization/pr16_bp_loss_return_owner.json'
OUT = ROOT / '.local/pr16-bp-owner-closeout'
LOGS = ('design/run_log.md', 'design/version_log.md')
CODES = ('scripts/pr16_bp_loss_return_owner.py', 'tests/test_pr16_bp_loss_return_owner.py',
         'scripts/pr16_restore_cfru_snapshot.py', 'tests/test_pr16_restore_cfru_snapshot.py',
         '.github/workflows/pr16-bp-loss-return-owner.yml')
SELF_PATHS = ('scripts/pr16_bp_owner_closeout.py', 'tests/test_pr16_bp_owner_closeout.py',
              '.github/workflows/pr16-bp-owner-closeout.yml')
MEMBERS = {'audit.stderr', 'audit.stdout', 'members.json', 'owner-excerpts.txt', 'owner-report.json',
           'reconciliation.json', 'source-restore.json', 'tested-head.txt', 'unit.stderr', 'unit.stdout'}
PINS = (
    (34757179781, 103723457110, 10317907932, '9251be475789df8b4ae2e8bba3dd8ff62d226a1f',
     100282, 'a2b6b24c7060f27c495cc9c7828249c37374fe0898ac7caf1732950fd497731d', 1, 16),
    (34757633314, 103724666041, 10318013148, TESTED,
     100623, '457a2d32eccd649e44de711cf1ccba95053d8643afa7c8e9aa5f0fc499deb90d', 2, 19),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def git(*args, env=None):
    return subprocess.check_output(['git', *args], cwd=ROOT, env=env)


def api(path):
    return subprocess.check_output(['gh', 'api', 'repos/' + REPO + '/' + path], cwd=ROOT)


def remote_head():
    return json.loads(api('git/ref/heads/' + BRANCH))['object']['sha']


def validate_artifact(raw, pin):
    run, job, artifact, head, size, sha, schema, tests = pin
    need(identity(raw) == dict(size=size, sha256=sha), 'artifact ZIP identity mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist()) == len(MEMBERS) and set(z.namelist()) == MEMBERS, 'unexpected artifact members')
        need(all(i.file_size < 2_000_000 and not (i.external_attr >> 16) & 0o170000 == 0o120000 for i in z.infolist()), 'unsafe artifact member')
        data = {n: z.read(n) for n in MEMBERS}
    for name, value in data.items():
        value.decode('utf-8')
        need(b'\0' not in value, 'binary artifact member')
        need(not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}', value), 'credential-like artifact member')
    manifest = json.loads(data['members.json'])
    need(set(manifest) == MEMBERS - {'members.json'}, 'incomplete artifact manifest')
    need(all(identity(data[n]) == v for n, v in manifest.items()), 'artifact member digest mismatch')
    need(data['tested-head.txt'].decode().strip() == head and data['audit.stderr'] == b'', 'wrong tested HEAD or audit stderr')
    unit = data['unit.stderr'].decode()
    need(re.findall(r'Ran (\d+) tests?', unit) == [str(tests)] and re.search(r'^OK$', unit, re.M), 'focused tests not passing')
    r = json.loads(data['owner-report.json'])
    need(r['schema_version'] == schema and r['classification'] == 'SOURCE_ONLY_OWNER_AUDIT_NOT_NATIVE_ACCEPTANCE', 'wrong audit schema or scope')
    need(r['fixed_source']['commit'] == 'e24a16fe39e27ae162faf5b78596d1f3df18489d', 'wrong CFRU commit')
    need(not r['native_bp_earning_accepted'] and not r['release_ready'], 'native acceptance overclaim')
    s = r['summary']
    need(s['new_emulator_processes'] == s['accepted_native_cases_replayed'] == 0 and not s['candidate_rom_changed'], 'audit changed native scope')
    w = r['matches']['CB2_WhiteOut']
    need(len(w) == 1 and w[0]['path'] == 'vendor/upstream/CFRU-JP/include/overworld.h'
         and w[0]['line'] == 97 and w[0]['text'] == 'void __attribute__((long_call)) CB2_WhiteOut(void);', 'WhiteOut declaration evidence changed')
    if schema == 2:
        need(s['source_scan_complete'] is True and s['owner_resolved'] is False
             and s['candidate_rom_owner_verified'] is False and s['callback_owner_candidates'] == [], 'declaration promoted to resolved owner')
    else:
        need(s['owner_resolved'] is True, 'historical false-positive original changed')
    restore = json.loads(data['source-restore.json'])
    need(restore['fsck_verified'] and restore['clean_source_verified'] and restore['locked_commit'] == r['fixed_source']['commit'], 'source restoration not proven')
    need(not restore['archived_worktree_used'] and not restore['archived_git_config_used'], 'archived worktree/config used')
    return data, r, restore


def put(name, raw, create_only=False):
    import pr16_resume as resume
    p = resume.safe_path(ROOT, name)
    p.parent.mkdir(parents=True, exist_ok=True)
    if create_only and p.exists():
        need(p.read_bytes() == raw, 'retained original differs: ' + name)
    else:
        p.write_bytes(raw)


def small_run(r):
    return {k: r[k] for k in ('id', 'name', 'path', 'head_sha', 'event', 'status', 'conclusion', 'created_at', 'updated_at')}


def retain():
    import pr16_resume as resume
    head = git('rev-parse', 'HEAD').decode().strip()
    need(head == os.environ['GITHUB_SHA'] and remote_head() == head, 'branch advanced before records')
    need(not git('status', '--porcelain', '--untracked-files=no').strip(), 'tracked worktree is dirty')
    pr = json.loads(api('pulls/16'))
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head and pr['head']['ref'] == BRANCH, 'PR state changed')
    old = resume.validate(ROOT)
    need(old['latest_native_run'] == 34749370272 and old['next_action']['id'] == 'BP_LOSS_RETURN_CALLBACK_OWNER', 'native stop advanced')
    need('source_owner_audit' not in old, 'source owner audit already recorded; do not duplicate')
    for name in (*CODES, 'state/source-lock.json', 'config/github_private_environment.json', 'scripts/build_battle_core.py'):
        need(git('show', TESTED + ':' + name) == (ROOT / name).read_bytes(), 'audited source changed: ' + name)
    rows = []
    for pin in PINS:
        run, job, artifact, tested, size, sha, schema, count = pin
        meta = json.loads(api('actions/runs/' + str(run)))
        job_meta = json.loads(api('actions/jobs/' + str(job)))
        a = json.loads(api('actions/artifacts/' + str(artifact)))
        need(meta['head_sha'] == tested and meta['path'] == '.github/workflows/pr16-bp-loss-return-owner.yml'
             and meta['status'] == 'completed' and meta['conclusion'] == 'success', 'audit Actions mismatch')
        need(job_meta['run_id'] == run and job_meta['conclusion'] == 'success', 'audit job mismatch')
        need(a['workflow_run']['id'] == run and a['workflow_run']['head_sha'] == tested and not a['expired']
             and a['size_in_bytes'] == size and a['digest'] == 'sha256:' + sha, 'artifact metadata mismatch')
        data, r, restored = validate_artifact(api('actions/artifacts/' + str(artifact) + '/zip'), pin)
        # Preserve all original payloads; wrap the whitespace-bearing excerpt losslessly.
        for name, raw in data.items():
            if name == 'owner-excerpts.txt':
                wrapped = dict(original_name=name, identity=identity(raw), utf8_text=raw.decode('utf-8'))
                need(wrapped['utf8_text'].encode('utf-8') == raw, 'excerpt roundtrip differs')
                put(BASE + '/' + str(run) + '/' + name + '.json', stable(wrapped), True)
            else:
                put(BASE + '/' + str(run) + '/' + name, raw, True)
        rows.append(dict(run_id=run, job_id=job, artifact_id=artifact, tested_head=tested,
                         zip=dict(size=size, sha256=sha), original_conclusion='success', schema_version=schema,
                         unit_tests=count, raw_owner_resolved=r['summary']['owner_resolved'],
                         owner_claim_accepted=False, originals=BASE + '/' + str(run), actions=small_run(meta)))
    snapshots = []
    for rid in (34752431199, 34756846108, 34757003759):
        snapshots.append(small_run(json.loads(api('actions/runs/' + str(rid)))))
    runs = json.loads(api('actions/runs?head_sha=' + head + '&per_page=100'))
    need(runs['total_count'] == len(runs['workflow_runs']) <= 100, 'incomplete current Actions snapshot')
    note = 'CFRU固定commitの独立復元・fsck/clean検証と19件のsource testsはPASS。WhiteOut参照はinclude/overworld.h:97の宣言1件のみ。旧schema1のowner_resolved=trueは宣言同居による誤判定で不採用。schema2はowner_resolved=false、候補ROM上ownerの固定とnative敗北復帰修復は未完。'
    report = dict(schema_version=1, task=TASK, classification='SOURCE_GATE_REPAIRED_NATIVE_RETURN_PENDING',
        source_restoration_and_classifier_fix_complete=True, candidate_rom_owner_verified=False,
        native_return_fix_complete=False, native_bp_earning_accepted=False, release_ready=False,
        rows=rows, failed_preflight_runs=snapshots, finding_ja=note, source_restore=restored,
        corrected_summary=r['summary'], source_bindings={n: identity((ROOT / n).read_bytes()) for n in CODES},
        record_source_head=head, record_workflow_run=int(os.environ['GITHUB_RUN_ID']),
        entry_head_actions=[small_run(x) for x in runs['workflow_runs']], final_record_commit_checks_claimed=False,
        retention_policy='9 raw text members plus lossless UTF-8 JSON wrapper for owner-excerpts.txt; original ZIP digests preserved',
        guard_report=BASE + '/guard-boundary.json', new_emulator_processes=0, accepted_native_cases_replayed=0,
        candidate_rom_changed=False, historical_native_run=34749370272)
    put(REPORT, stable(report))
    goal = '固定候補bffdのCB2_WhiteOut(08055F65)を設定する実callbackと、facility script 092CF669の復帰先をROM bytes・逆アセンブルで固定する。source-only監査の再実行ではなく候補bytesへ進み、安全な最小修復後だけ敗北帰還・元party600bytes/count復元を検証する。'
    old['bp']['current_stop'] += '\n\n' + note
    old['bp']['next_step'] = goal
    old['next_action']['goal_ja'] = goal
    old['next_action']['read_paths'] = list(dict.fromkeys([REPORT, 'scripts/build_battle_core.py', *old['next_action']['read_paths']]))
    old['next_action']['stop_rule_ja'] += ' run34757633314の固定source監査は完了し再実行しない。header宣言を分岐ownerと扱わず、run34757179781の旧owner=trueを修復根拠へ使わない。'
    old['source_owner_audit'] = dict(report=REPORT, run_id=PINS[-1][0], job_id=PINS[-1][1], tested_head=TESTED,
        source_gate_complete=True, owner_resolved=False, candidate_rom_owner_verified=False,
        native_return_fix_complete=False, new_emulator_processes=0, accepted_native_cases_replayed=0)
    old['observed_head'] = TESTED
    old['observed_head_semantics'] = 'このHEADはsource-only監査の対象。最新native診断HEAD・正式受入HEADとは異なり、現在branch HEADの代用品ではない。'
    old['observed_head_checks']['reason_ja'] += ' Source-only run34757633314/job103724666041は成功・19tests PASSだがowner未固定を確認した結果でありnative帰還の成功ではない。最終記録commitの全Checks完了は主張しない。'
    old['do_not_repeat'] = list(dict.fromkeys([note + ' 同一固定sourceの再scanや受入済み取消/Save/Continueの再実行は不要。', *old['do_not_repeat']]))
    for name in (*CODES, REPORT):
        old['source_bindings'][name] = identity((ROOT / name).read_bytes())
    old['logs_synchronized'] = old['p08_resume_synchronized'] = True
    backlog = resume.load(ROOT, resume.BACKLOG)
    for row in backlog['remaining_conditions']:
        if row['id'] in ('NATURAL_CAPTURE_GEAR', 'FINAL_NATIVE_ACCEPTANCE'):
            row['resume'] = 'Current resume: ' + resume.DOC + '. ' + old['bp']['current_stop'] + ' Next: ' + goal
    # Recheck immediately before changing canonical handoff files.
    need(remote_head() == head, 'branch advanced before handoff write')
    put(resume.BACKLOG, stable(backlog))
    put(resume.STATE, (json.dumps(old, ensure_ascii=False, indent=2) + '\n').encode())
    put(resume.DOC, resume.render(old).encode())
    resume.validate(ROOT)
    print('RETAINED_SOURCE_EVIDENCE_AND_SYNCED_FIXED_HANDOFF; NATIVE_RETURN_PENDING')


def logs():
    import pr16_resume as resume
    resume.validate(ROOT)
    unit = (OUT / 'unit.stderr').read_text()
    count = re.findall(r'Ran (\d+) tests?', unit)
    need(len(count) == 1 and re.search(r'^OK$', unit, re.M), 'closeout tests not passing')
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = (f'\n\n## {now} — {TASK}\n- Task: {TASK} / source復元阻害とowner誤判定の修正\n'
        '- Status: STOPPED / source復元・分類修正・原文保存はDONE。候補ROM上owner固定とnative敗北帰還修復は未完。\n'
        '- Summary: 初期HEAD5a9d2f8の再開入口・AGENTS・固定MD/JSON・Actionsを照合。archive内dirty worktree/configを使わず、hash固定Git objects/shallow境界から独立復元。full fsck/cleanを維持。宣言・コメント・文字列・別関数参照のowner誤判定を修正。\n'
        '- Evidence: run34757633314/job103724666041/HEAD9e435e551598c2b99046c7aaff1bff6da1721da3はsuccess、19tests PASS。ZIP100623bytes/SHA457a2d32eccd649e44de711cf1ccba95053d8643afa7c8e9aa5f0fc499deb90d、10text payloadを保存（excerptのみ末尾空白を保持する可逆JSON包み、他9件は原byte）。旧run34757179781のowner=trueも原文保持し不採用と明記。\n'
        '- Finding: 固定CFRUのWhiteOutはinclude/overworld.h:97の宣言1件だけ。candidate owner未確定をtrueに代作しない。過去native failure34749370272と復元未観測、BP未受入を維持。\n'
        f'- Verify: source19tests PASS; closeout focused {count[0]}tests PASS; resume check/task graph/git diff --check、index原文同一性とprivate guard差分境界を実行。guard原本は{BASE}/guard-boundary.json。全体guard既存違反と新規差分違反を分離。\n'
        '- Counts: 専用workflowの新規emulator0、受入取消/Save/Continue再実行0、候補ROM変更0、既存native受入変更0。push自動CIはActions一覧へ分離。\n'
        '- Next: bffd固定候補のWhiteOut設定元とfacility script復帰をROM bytesで固定し最小修復。その変更後のみnative敗北帰還/600bytes party復元を検証。完了source監査と同一native失敗を再実行しない。\n'
        '- Files changed: ' + ', '.join((*CODES, *SELF_PATHS, REPORT, BASE, resume.STATE, resume.DOC, resume.BACKLOG, *LOGS)) + '\n'
        f'- Commit: source {os.environ["GITHUB_SHA"]}; この追記を含むcommitはGit履歴が正本。version/product SHA変更なし。\n'
        '- Network利用: GitHub接続APIとActions ghでref/PR/Actions/artifactおよび固定state archiveを取得。非force fast-forwardのみ。merge/draft解除/release/baseline切替なし。\n')
    for name in LOGS:
        with resume.safe_path(ROOT, name).open('a', encoding='utf-8') as f:
            f.write(entry)
    print('APPENDED_BOTH_LOGS_WITH_NATIVE_RETURN_PENDING')


def stage_and_guard():
    import pr16_resume as resume
    import guard_private_files as g
    names = [resume.STATE, resume.DOC, resume.BACKLOG, REPORT, *LOGS]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT / BASE).rglob('*') if p.is_file()]
    subprocess.run(['git', 'add', '--', *names], cwd=ROOT, check=True)
    changed = [n for n in git('diff', '--cached', '--name-only', '-z', START).decode().split('\0') if n]
    allowed = set(names) | set(CODES) | set(SELF_PATHS)
    need(set(changed) <= allowed, 'unexpected cumulative session changes')
    for name in changed:
        raw = git('show', ':' + name)
        need(raw == (ROOT / name).read_bytes() and b'\0' not in raw, 'staged bytes differ or binary')
        raw.decode('utf-8')
        prior = subprocess.run(['git', 'show', START + ':' + name], cwd=ROOT, capture_output=True).stdout
        def bad(b):
            lines = b.decode('utf-8', errors='replace').splitlines()
            return collections.Counter(lines[i - 1] for i in g.document_user_path_lines(b))
        need(not (bad(raw) - bad(prior)), 'new private user path')
        need(Path(name).suffix not in g.BLOCKED_SUFFIXES and not any(name == p or name.startswith(p + '/') for p in g.BLOCKED_PARTS), 'private path')
    with tempfile.TemporaryDirectory(dir=OUT) as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / 'base.index'))
        subprocess.run(['git', 'read-tree', START], cwd=ROOT, env=env, check=True)
        cmd = [sys.executable, 'scripts/guard_private_files.py']
        before = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True)
        after = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    need(before.returncode in (0, 1) and (before.returncode, before.stdout, before.stderr) == (after.returncode, after.stdout, after.stderr), 'standard private guard result changed')
    guard_name = BASE + '/guard-boundary.json'
    report = dict(base=START, record_source_head=os.environ['GITHUB_SHA'],
        checked_changed_paths=sorted(n for n in changed if n != guard_name),
        full_index_guard_before=before.returncode, full_index_guard_after=after.returncode,
        exact_output_match=True, new_violations=0, full_guard_pass_claimed=after.returncode == 0,
        new_emulator_processes=0)
    put(guard_name, stable(report))
    subprocess.run(['git', 'add', '--', guard_name], cwd=ROOT, check=True)
    (OUT / 'guard-boundary.json').write_bytes(stable(report))
    print(stable(report).decode(), end='')


if __name__ == '__main__':
    need(len(sys.argv) == 2 and sys.argv[1] in ('retain', 'logs', 'stage_and_guard'), 'explicit closeout action required')
    OUT.mkdir(parents=True, exist_ok=True)
    globals()[sys.argv[1]]()
