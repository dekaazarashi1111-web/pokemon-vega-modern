#!/usr/bin/env python3
"""Issue19の完了Actions原本だけを照合・記録する。生成/旧受入は再実行しない。"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from tools.pr16_learnset_baseline import TASK, LOCK, CODE, KINDS, file_identity, require, sha
from tools.modernization_identity import stable_json
from pr16_resume import STATE, DOC, render
from pr16_wiki_reconcile import fetch

REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
REQUEST = '.github/pr16-learnset-baseline-record.json'
CHECKPOINT = 'content/modernization/pr16_learnset_baseline_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_learnset_baseline_evidence'
GUIDE = 'docs/PR16_LEARNSET_BASELINE_RESET_JA.md'
COPIED = ('receipt.json', 'official_index.json', 'vega_original_pending.json',
          'owner_approved_overlay.json', 'adjudication.json')
PROOF = ('verify.json', 'unit.log', 'build11.json', 'build29.json', 'check.json')
PHASE = 'official-source-isolation-20260921'


def validate_run(run: dict, jobs: dict, artifacts: dict, request: dict) -> dict:
    rid, head = request['run_id'], request['source_head']
    require(run['id'] == rid and run['head_sha'] == head and run['head_branch'] == BRANCH, 'run/HEAD/branch不一致')
    require(run['repository']['full_name'] == REPO and run['event'] == 'push'
            and run['path'] == '.github/workflows/pr16-learnset-baseline.yml', 'workflow/repo/event不一致')
    require(run['status'] == 'completed' and run['conclusion'] == 'success', '未完了/失敗runは受入しない')
    require(jobs['total_count'] == len(jobs['jobs']) == 1, 'job未処理ページ/欠落')
    job = jobs['jobs'][0]
    require(job['run_id'] == rid and job['head_sha'] == head and job['name'] == 'baseline-verify'
            and job['status'] == 'completed' and job['conclusion'] == 'success', 'job不一致')
    require(job['steps'] and all(s['status'] == 'completed' and s['conclusion'] == 'success'
                               for s in job['steps']), '未成功stepあり')
    require(any('upload-artifact' in s['name'] for s in job['steps']), 'upload完了step欠落')
    require(artifacts['total_count'] == len(artifacts['artifacts']), 'artifact未処理ページ')
    found = [a for a in artifacts['artifacts'] if a['name'] == 'pr16-learnset-baseline-verified']
    require(len(found) == 1, 'artifact欠落/重複')
    a = found[0]; bound = a['workflow_run']
    require(a['id'] == request['artifact_id'] and a['digest'] == 'sha256:' + request['artifact_sha256']
            and a['expired'] is False and bound['id'] == rid and bound['head_sha'] == head
            and bound['head_branch'] == BRANCH, 'artifact identity不一致')
    return a


def validate_report(report: dict, receipt: dict, request: dict) -> None:
    require(report['status'] == 'PASS_OFFICIAL_SOURCE_ISOLATION' and report['task'] == TASK, '証拠scope不一致')
    require(report['source_head'] == request['source_head'] and report['run_id'] == request['run_id'], '証拠HEAD/run不一致')
    require(report['focused_tests'] == 39, '39試験欠落')
    for key in ('two_process_builds_identical', 'readonly_check_byte_mtime_unchanged',
                'tracked_tree_unchanged', 'local_and_actions_output_identical'):
        require(report[key] is True, '検証未成功: ' + key)
    for key in ('rom_changes', 'new_native_runs', 'accepted_native_reruns'):
        require(type(report[key]) is int and report[key] == 0, 'source限定境界違反')
    require(report['issue19_complete'] is False and report['release_ready'] is False, '全体受入への昇格禁止')
    require(receipt['official_records'] == 1299 and receipt['official_routes'] == 118524
            and receipt['route_kinds'] == KINDS and receipt['source_semantic_differences'] == 0, '原本coverage不一致')
    require(receipt['vega_pending_species'] == 181 and receipt['vega_baseline_rows_imported'] == 0
            and receipt['owner_overlay_rows'] == 0 and receipt['p07_historical_rows_preserved'] == 1572, 'layer境界不一致')
    require(receipt['activation_gate']['ready'] is False and receipt['rom_changed'] is False
            and receipt['release_ready'] is False and receipt['spec_only_routes'] == 159
            and receipt['spec_only_species'] == 103, 'runtime/例外境界への昇格禁止')


def read_proof(raw: bytes, request: dict) -> dict[str, bytes]:
    require(sha(raw) == request['artifact_sha256'], 'ZIP digest不一致')
    kept = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        require(len(names) == len(set(names)) <= 32, 'ZIP重複/上限違反')
        for info in z.infolist():
            p = PurePosixPath(info.filename)
            require(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                    and not stat.S_ISLNK(info.external_attr >> 16), 'ZIP path/symlink違反')
        for name in PROOF:
            require(name in names and z.getinfo(name).file_size < 100000, '証拠欠落/上限違反')
            kept[name] = z.read(name)
        report = json.loads(kept['verify.json'])
        require(set(report['files']) == set(COPIED) | {'official_baseline.jsonl', 'historical_layers.json'}, '7出力以外の証拠集合')
        for name, identity in report['files'].items():
            require(Path(name).name == name, '生成物name不正')
            path = 'outputs/' + name
            require(path in names and z.getinfo(path).file_size == identity['size'] <= 250000000, '生成物size不一致')
            digest, size = hashlib.sha256(), 0
            with z.open(path) as stream:
                for block in iter(lambda: stream.read(1048576), b''):
                    digest.update(block); size += len(block)
            require({'size': size, 'sha256': digest.hexdigest()} == identity, '生成物SHA不一致')
            if name in COPIED:
                kept[path] = z.read(path)
    require(set('outputs/' + n for n in COPIED) <= set(kept), 'compact原本欠落')
    receipt = json.loads(kept['outputs/receipt.json'])
    validate_report(report, receipt, request)
    require(json.loads(kept['build11.json']) == json.loads(kept['build29.json'])
            == json.loads(kept['check.json']) == receipt, '2生成/check/receipt不一致')
    require(receipt['outputs'] == {k: v for k, v in report['files'].items() if k != 'receipt.json'}, '出力集合不一致')
    log = kept['unit.log'].decode('utf-8')
    require(re.findall(r'^Ran (\d+) tests? in ', log, re.M) == ['39'] and re.search(r'\nOK\s*$', log), '試験原本未成功')
    for data in kept.values():
        data.decode('utf-8'); require(b'\0' not in data, 'NUL禁止')
    return kept


def synchronize(state: dict, checkpoint: dict) -> dict:
    require('learnset_baseline' not in state, '既に記録済み。受入の反復は禁止')
    result = copy.deepcopy(state)
    goal = 'Issue #19: Vega元来181種の凍結ROM/atwiki原本とdexNo・SpeciesID・keyを結合し、方法別習得表を確定する。公式1299件の受入済み隔離生成は影響なしに再実行しない。'
    result['next_action'] = {
        'id': 'LEARNSET_VEGA_ORIGINAL_SOURCE', 'goal_ja': goal,
        'read_paths': [GUIDE, CHECKPOINT, LOCK, 'tools/pr16_learnset_baseline.py',
                       'config/species_surface.json', 'scripts/build_species_surface.py'],
        'stop_rule_ja': '原本衝突/未知move/未承認例外は台帳で停止。旧Wiki/候補/受入原本を保持。Vega原本・consumer切替・後継ROM/Wiki・影響nativeが揃うまでIssue19全体を完了扱いしない。',
        'host_write_policy_ja': '入力ZIP/ROM/saveはGit管理外の読み取り専用原本。今回のsource-only受入をゲーム内受入へ昇格しない。',
    }
    result['bp']['next_step'] = goal
    result['bp']['current_stop'] = 'Issue19の公式原本隔離を完了。1299件/118524経路、39境界試験、Actions独立2生成/純読取checkを原本照合済み。Vega元来181種とruntime切替は未完。候補ROM・旧Wiki・native受入は変更なし。'
    result.setdefault('observed_head_history', []).append({'head': state['observed_head'],
        'semantics': state['observed_head_semantics'], 'reason_ja': 'Issue19公式原本隔離の検証HEADへ表示を更新。旧Wiki証拠は保持。'})
    result['observed_head'] = checkpoint['source_head']
    result['observed_head_semantics'] = '完了Actionsの公式隔離検証入力HEAD。branchの最新HEAD/native受入HEADとは別。反映commitはgit log、原本run/artifactはlearnset_baselineを参照。'
    result['observed_head_checks'].setdefault('reason_history_ja', []).append(state['observed_head_checks']['reason_ja'])
    result['observed_head_checks']['reason_ja'] = '既存runsは過去scopeとして保持。Issue19の39試験・独立2生成・純読取・tracked不変はlearnset_baselineの完了run原本を参照。全native再受入ではない。'
    result['learnset_baseline'] = checkpoint
    result['pending_runs'] = [r for r in state['pending_runs'] if r['run_id'] != checkpoint['run_id']]
    result['remaining_sequence_ja'] = 'Issue19公式原本隔離済み → Vega元来181種/例外判断 → runtime全consumer/後継ROM・Wiki/影響native → Issue18に残る限定監査 → 別承認後のclean-ROM二重生成/BPS/release。'
    result['do_not_repeat'].append('Issue19公式隔離: source/code hash不変なら39試験・CSV全件照合・二重生成は完了artifactを再利用。旧P07履歴1572件を新baseline/空overlayへ再投入しない。')
    result['logs_synchronized'] = True
    return result


def validate_recording_log(raw: bytes) -> None:
    text = raw.decode('utf-8')
    require(re.findall(r'^Ran (\d+) tests? in ', text, re.M) == ['12']
            and re.search(r'\nOK\s*$', text), '記録12試験の成功原本が必要')


def record() -> None:
    request = json.loads((ROOT / REQUEST).read_bytes())
    require(request['task'] == TASK and request['mode'] == 'record-completed', '記録要求不正')
    recording_log = (ROOT / '.local/pr16-learnset-baseline-record/unit.log').read_bytes()
    validate_recording_log(recording_log)
    proof_request = request['verification']
    rid = proof_request['run_id']
    run = fetch(f'actions/runs/{rid}')
    jobs = fetch(f'actions/runs/{rid}/jobs?per_page=100')
    artifacts = fetch(f'actions/runs/{rid}/artifacts?per_page=100')
    artifact = validate_run(run, jobs, artifacts, proof_request)
    files = read_proof(fetch(f'actions/artifacts/{artifact["id"]}/zip', binary=True), proof_request)
    receipt = json.loads(files['outputs/receipt.json'])
    require(receipt['source_lock'] == {'path': LOCK, **file_identity(ROOT / LOCK)}, 'source-lockが変化')
    require(receipt['code_identity'] == {p: file_identity(ROOT / p) for p in CODE}, '生成器が変化')
    for path, identity in json.loads((ROOT / LOCK).read_bytes())['repository_sources'].items():
        require(file_identity(ROOT / path) == identity, '依存sourceが変化: ' + path)
    state = json.loads((ROOT / STATE).read_bytes())
    require(state['branch'] == BRANCH and not state['pr_merged'] and not state['active_baseline_changed'], 'branch/受入境界不一致')
    checkpoint = {'schema_version': 1, 'task': TASK, 'phase': PHASE,
        'status': 'ACCEPTED_OFFICIAL_SOURCE_ISOLATION_ONLY', 'issue19_complete': False,
        'source_head': proof_request['source_head'], 'run_id': rid,
        'job_id': jobs['jobs'][0]['id'], 'run_status': 'completed', 'run_conclusion': 'success',
        'artifact': {'id': artifact['id'], 'sha256': proof_request['artifact_sha256'],
                     'size': artifact['size_in_bytes'], 'expires_at': artifact['expires_at']},
        'source_receipt': f'{EVIDENCE}/receipt.json', 'official_index': f'{EVIDENCE}/official_index.json',
        'adjudication': f'{EVIDENCE}/adjudication.json', 'verification': f'{EVIDENCE}/verify.json',
        'official_records': 1299, 'official_routes': 118524, 'focused_tests': 39,
        'recording_tests': 12, 'rom_changes': 0, 'new_native_runs': 0,
        'p07_history_preserved': 1572, 'owner_overlay_rows': 0,
        'remaining': receipt['activation_gate']['blockers'], 'release_ready': False}
    files['recording-unit.log'] = recording_log
    files['actions.json'] = stable_json({
        'run': {k: run[k] for k in ('id', 'head_sha', 'head_branch', 'status', 'conclusion', 'event', 'path', 'created_at', 'updated_at')},
        'job': {k: jobs['jobs'][0][k] for k in ('id', 'run_id', 'head_sha', 'name', 'status', 'conclusion', 'steps')},
        'artifact': {k: artifact[k] for k in ('id', 'name', 'size_in_bytes', 'digest', 'created_at', 'expires_at', 'expired', 'workflow_run')},
    })
    checkpoint['proof_bindings'] = {Path(n).name: {'size': len(v), 'sha256': sha(v)} for n, v in sorted(files.items())}
    result = synchronize(state, checkpoint)
    destination = ROOT / EVIDENCE
    require(not destination.exists() and not (ROOT / CHECKPOINT).exists(), '記録先を上書きしない')
    destination.mkdir()
    for name, data in files.items():
        (destination / Path(name).name).write_bytes(data)
    (ROOT / CHECKPOINT).write_bytes(stable_json(checkpoint))
    note = '\n\n## Issue19公式原本隔離の完了checkpoint\n\n' + f'公式1299件/118524経路・39境界試験・独立2生成/純読取checkをrun `{rid}` で検証し、全stepとartifactを完了照合済み。正本は `{CHECKPOINT}`。Vega元来181種/例外/runtime切替/後継ROM・Wiki/nativeは未完。旧候補と受入済み原本は不変。\n'
    with (ROOT / GUIDE).open('a', encoding='utf-8') as f: f.write(note)
    routing = ('\n\n## Issue19の実装・検証正本\n\n'
        + f'実装手順は `{GUIDE}`、工程の受入範囲と未完項目は `{CHECKPOINT}`。'
        + '最新の次工程は固定再開MD/JSONを優先し、予約時点の説明と混同しない。\n')
    with (ROOT / 'CHATGPT_RESUME.md').open('a', encoding='utf-8') as f: f.write(routing)
    for name in (*CODE, LOCK, REQUEST, CHECKPOINT, GUIDE, 'CHATGPT_RESUME.md',
                 'scripts/pr16_learnset_baseline_record.py', 'tests/test_pr16_learnset_baseline_record.py',
                 '.github/workflows/pr16-learnset-baseline-record.yml'):
        result['source_bindings'][name] = file_identity(ROOT / name)
    (ROOT / STATE).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / DOC).write_text(render(result))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    entry = (f'\n\n## {now} — Issue19公式原本隔離の完了記録\n'
        f'- Task: {TASK}\n- Version: {PHASE}\n- Status: DONE（公式原本隔離のみ。Issue19全体は未完）\n'
        '- Summary: 1299件/118524経路を無損失隔離。参考1377件/125746経路と5 CSVの意味差分0。Vega181種と旧P07 1572行/空overlayを分離。ID1063の159経路/103種とキャタピー訂正は明示例外台帳へ。\n'
        '- Files changed: 新規生成器/CLI/39境界試験/source-lock、限定Actions、公式index/例外/完了原本、固定入口/引継ぎMD・JSON、両ログ。\n'
        '- Verify: ローカルとActionsの独立2生成hash一致・実CLI checkのbyte/mtime不変。記録12境界試験、resume/task graph/diff/changed-final-index guard。既存native受入の再実行0。\n'
        f'- Commit: 本記録を含むcommit。検証source HEAD={proof_request["source_head"]}。\n'
        f'- Network: GitHub connector/Actions、完了run{rid}/artifact{artifact["id"]}のSHA・全stepをGET照合。入力assetは固定hashのmodernization ZIPのみ。\n'
        '- Network（参照閲覧）: https://w.atwiki.jp/altair1/pages/19.html は原作Vega図鑑入口として確認。個別習得表の採用0。\n'
        '- Boundary: ROM/ARM/native変更0、旧Wiki/受入原本/active baseline不変、merge/releaseなし。初回ローカル試作では分類206枠を181実対象へ訂正後に再生成し、失敗をPASSへ転用していない。\n')
    for name in ('design/run_log.md', 'design/version_log.md'):
        require(PHASE not in (ROOT / name).read_text(), '二重追記禁止')
        with (ROOT / name).open('a', encoding='utf-8') as f: f.write(entry)
    print(json.dumps(checkpoint, ensure_ascii=False, sort_keys=True))


def guard(base: str) -> None:
    import guard_private_files as private
    require(re.fullmatch('[0-9a-f]{40}', base), 'guard base不正')
    def git(*args): return subprocess.check_output(['git', *args], cwd=ROOT)
    paths = [p for p in git('diff', '--cached', '--name-only', '-z', base).decode().split('\0') if p]
    allowed = {STATE, DOC, GUIDE, CHECKPOINT, LOCK, REQUEST, 'CHATGPT_RESUME.md',
               'design/run_log.md', 'design/version_log.md', *CODE,
               'scripts/pr16_learnset_baseline_record.py', 'tests/test_pr16_learnset_baseline_record.py',
               'tests/test_pr16_learnset_baseline.py', '.github/pr16-learnset-baseline-run.json',
               '.github/workflows/pr16-learnset-baseline.yml', '.github/workflows/pr16-learnset-baseline-record.yml'}
    violations = []
    for name in paths:
        require(name in allowed or name in {EVIDENCE + '/' + n for n in (*COPIED, *PROOF, 'recording-unit.log', 'actions.json')}, 'guard対象外path: ' + name)
        data = git('show', ':' + name)
        data.decode('utf-8'); require(b'\0' not in data, 'binaryをstageしない')
        require(Path(name).suffix in {'.py', '.md', '.json', '.yml', '.log'}, 'text拡張子以外')
        before = subprocess.run(['git', 'show', base + ':' + name], cwd=ROOT, capture_output=True).stdout
        def bad(raw):
            lines = raw.decode('utf-8', errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(raw))
        if bad(data) - bad(before): violations.append(name)
    require(not violations, '新規private path違反: ' + ','.join(violations))
    print(json.dumps({'status':'PASS_CHANGED_FINAL_INDEX','base':base,'paths':len(paths),
        'new_violations':0,'full_historical_guard_pass_claimed':False,'rom_changes':0},sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('record', 'guard'))
    parser.add_argument('--base')
    args = parser.parse_args()
    if args.command == 'record': record()
    else: guard(args.base)
