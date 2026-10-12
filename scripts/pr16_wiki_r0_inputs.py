#!/usr/bin/env python3
"""R0入力の有限監査。保存ROM・旧生成器・nativeを実行しない。"""
from __future__ import annotations
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DECISION = 'OWNER-20261010-WIKI-FIRST'
TASK = 'USER-20261010-WIKI-R0-INPUTS'
START = '2e8c649fe3ff4a7e38881cbb7fb6c24cb7acaea9'
BRANCH = 'codex/modernization-followup-20260908'
STATE = 'content/modernization/pr16_wiki_first_execution_plan.json'
POLICY = 'docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md'
MANIFEST = 'content/modernization/pr16_wiki_r0_input_manifest.json'
GUIDE = 'docs/PR16_WIKI_R0_INPUTS_JA.md'
OLD = 'docs/wiki/p08-candidate-46487d98'
NEW = 'docs/wiki/issue19-candidate-6e88a021'
CANDIDATES = {
    OLD: {'sha256': '46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38', 'size': 33554432, 'crc32': 'CC068B4A'},
    NEW: {'sha256': '6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2', 'size': 33554432, 'crc32': '00F31AF7'},
}
DOMAINS = {'species': 1671, 'moves': 1063, 'abilities': 318, 'items': 1044}
OLD_DATA = tuple('data/' + n + '.jsonl' for n in (*DOMAINS, 'megas', 'z_moves', 'evolutions')) + ('data/vega_balance.json', 'data/provenance.json')
NEW_DATA = ('data/routes_index.json', 'data/conditions_index.json', 'data/supply.jsonl')
CODE = {'scripts/pr16_wiki_r0_inputs.py', 'tests/test_pr16_wiki_r0_inputs.py', '.github/workflows/pr16-wiki-r0-inputs.yml'}
OUTPUTS = {STATE, POLICY, MANIFEST, GUIDE, 'design/run_log.md', 'design/version_log.md'}
CHECKPOINTS = tuple('content/modernization/pr16_learnset_' + n + '_checkpoint.json' for n in ('wiki', 'successor', 'payload', 'floette', 'supply_alignment'))
CONTEXT = {'scripts/pr16_candidate_wiki_inputs.py', 'scripts/pr16_candidate_wiki_catalog.py', 'scripts/pr16_candidate_wiki_render.py', 'scripts/pr16_learnset_wiki.py', 'scripts/pr16_learnset_wiki_actions.py', 'scripts/pr16_learnset_supply_rom.py', 'scripts/pr16_learnset_supply_alignment.py', 'content/modernization/pr16_p08_candidate_transfer.json', 'config/active_play_baseline.json'}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def encode(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def load(raw: bytes) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, '重複JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def read(root: Path, name: str) -> bytes:
    p = PurePosixPath(name)
    need(isinstance(name, str) and name == p.as_posix() and not p.is_absolute()
         and '..' not in p.parts and '\\' not in name, '相対path不正')
    path = root
    for part in p.parts:
        path = path / part
        need(not path.is_symlink(), 'symlink禁止: ' + name)
    need(path.is_file(), '入力欠落: ' + name)
    raw = path.read_bytes()
    raw.decode('utf-8')
    need(b'\0' not in raw, 'binary入力禁止: ' + name)
    return raw


def rows(raw: bytes, count: int) -> list[dict]:
    values = [load(line) for line in raw.splitlines() if line.strip()]
    need(len(values) == count and all(isinstance(r, dict) for r in values), 'record件数/型不一致')
    need(all(type(r.get('id')) is int for r in values) and [r['id'] for r in values] == list(range(count)), 'ID集合/順序不一致')
    keys = [r.get('key') for r in values]
    need(all(isinstance(k, str) and k for k in keys) and len(set(keys)) == count, 'stable key不一致')
    need(all(isinstance(r.get('name'), str) and r['name'] for r in values), '表示名不一致')
    return values


def bound(root: Path, folder: str, index: dict, name: str) -> bytes:
    raw = read(root, folder + '/' + name)
    need(index['files'].get(name) == identity(raw), '旧manifestとhash不一致: ' + folder + '/' + name)
    return raw


def inspect(root: Path, source_head: str) -> tuple[dict, dict[str, bytes]]:
    """純読取。異なる候補を統合受入せず、次に必要な証明を具体化する。"""
    need(bool(re.fullmatch('[0-9a-f]{40}', source_head)), 'source HEAD不正')
    exported = {}
    indexes = {}
    bindings = {}
    for folder, candidate in CANDIDATES.items():
        name = folder + '/data/index.json'
        raw = read(root, name)
        index = load(raw)
        need(index['candidate'] == candidate, '候補identity不一致: ' + folder)
        need(isinstance(index.get('files'), dict) and index['files'], 'manifest files欠落')
        indexes[folder] = index
        exported[name] = raw
        bindings[name] = identity(raw)
    data = {}
    for folder, names in ((OLD, OLD_DATA), (NEW, NEW_DATA)):
        for name in names:
            raw = bound(root, folder, indexes[folder], name)
            full = folder + '/' + name
            exported[full] = raw
            bindings[full] = identity(raw)
            data[full] = raw
    domain_summary = {}
    for domain, count in DOMAINS.items():
        records = rows(data[OLD + '/data/' + domain + '.jsonl'], count)
        domain_summary[domain] = {'count': count, 'id_key_sha256': identity(encode([[r['id'], r['key']] for r in records]))['sha256'], 'record_keys': sorted(records[0])}
        if domain == 'species':
            for r in records:
                stats = r['base_stats']
                need(isinstance(stats, dict) and len(stats) == 7 and 'total' in stats, '6種族値/BST schema')
                fields = set(stats) - {'total'}
                need(all(type(stats[k]) is int and 0 <= stats[k] <= 255 for k in fields), '種族値型')
                need(type(stats['total']) is int and sum(stats[k] for k in fields) == stats['total'], 'BST不一致')
            domain_summary[domain]['base_stat_keys'] = sorted(records[0]['base_stats'])
    new_counts = indexes[NEW]['counts']
    need(new_counts['species'] == DOMAINS['species'] and new_counts['moves'] == DOMAINS['moves'], '後継ID件数不一致')
    need(new_counts['active_side_change'] == 0 and new_counts['owner_overlay_rows'] == 0, '非承認採用を検出')
    cp_summaries = {}
    for name in CHECKPOINTS:
        raw = read(root, name)
        exported[name] = raw
        bindings[name] = identity(raw)
        cp = load(raw)
        cp_summaries[name] = {k: cp[k] for k in ('status', 'candidate', 'candidate_crc32', 'source_head', 'run_id', 'parent_candidate', 'repair_parent', 'data_files', 'actions_completion_confirmed') if k in cp}
    for name in sorted(CONTEXT):
        # contextだけは任意。監査必須入力をoptionalへ読み替えない。
        if (root / name).is_file():
            exported[name] = read(root, name)
    table_provenance = load(data[OLD + '/data/provenance.json'])
    result = {
        'schema_version': 1, 'decision_id': DECISION, 'source_head': source_head,
        'status': 'PASS_BOUND_INPUT_INVENTORY_NOT_REVIEW_READY',
        'review_revision': 'R0', 'review_ready': False, 'selected_review_candidate': None,
        'candidates': CANDIDATES, 'input_bindings': bindings, 'numeric_domains': domain_summary,
        'successor_counts': new_counts, 'numeric_table_provenance': table_provenance,
        'successor_index_metadata': {k: v for k, v in indexes[NEW].items() if k not in {'files', 'source_bindings'}},
        'checkpoint_summaries': cp_summaries,
        'successor_data_paths': sorted(n for n in indexes[NEW]['files'] if n.startswith('data/')),
        'remaining_gates': [
            '旧能力/技/特性/進化/機構tableと後継候補の非変更rangeまたは同一semantic hashを結合する。',
            '正式registryの1671 ID/stable keyと後継ownerの実対応を照合し、現在の習得経路だけを採用する。',
            '候補識別子付き別R0へ比較/個別/逆引き/メガ/Gmax/Z/供給/限界を生成し、リンク・決定性・check無書込を検証する。',
        ],
        'accepted_tests_rerun': 0, 'rom_reconstructions': 0, 'native_processes': 0,
        'story_pass_claimed': False, 'release_ready': False, 'active_baseline_changed': False,
    }
    return result, exported


def guide(report: dict) -> bytes:
    text = '# Wiki R0 入力監査と継続点\n\n'
    text += '**入力監査だけが完了。R0は未完成・閲覧依頼前です。**\n\n'
    text += f'決定 `{DECISION}` / 入力HEAD `{report["source_head"]}`。現在の作業選択は [固定状態JSON](../{STATE}) のみを正とします。\n\n'
    text += f'[入力manifest](../{MANIFEST}) で既存Wikiの機械可読入力を元のsize/SHA-256へ結合しました。旧Wiki生成器・受入済み試験・ROM再構成・nativeは実行していません。\n\n'
    text += '| 入力 | identity | 採用範囲 |\n| --- | --- | --- |\n'
    text += f'| 旧P08 | `{CANDIDATES[OLD]["sha256"]}` | 能力・技・特性等の数値原本。後継ROMでの意味同値は未証明。 |\n'
    text += f'| Issue19後継 | `{CANDIDATES[NEW]["sha256"]}` | 後継の現役習得経路。旧P07履歴と混在させない。 |\n\n'
    text += '## 次の具体作業\n\n' + '\n'.join(str(i + 1) + '. ' + value for i, value in enumerate(report['remaining_gates'])) + '\n\n'
    text += '保存容量784分類/90未知/安全容量0は保留正本のまま。全クリ走破は対象外でありPASSではありません。数値同値が未証明のためreview_readyはfalse、所有者承認・配布・baseline切替を追加しません。\n'
    return text.encode('utf-8')


def write_changed(root: Path, name: str, raw: bytes) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != raw:
        path.write_bytes(raw)


def append_once(root: Path, name: str, task: str, block: str) -> bool:
    raw = read(root, name)
    marker = ('- Task: ' + task + ' /').encode('utf-8')
    count = raw.count(marker)
    need(count <= 1, '重複log task: ' + name)
    if count:
        return False
    with (root / name).open('ab') as stream:
        stream.write(block.encode('utf-8'))
    return True


def record(root: Path, report: dict, test_count: int) -> None:
    state = load(read(root, STATE))
    need(state['decision_id'] == DECISION and state['owner_execution_plan']['wiki']['review_ready'] is False, '再開方針/既公開R0を改作しない')
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    policy_task = 'USER-20261010-WIKI-FIRST-POLICY'
    policy_log = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {policy_task} / 未実施の両ログ追記\n- Version: wiki-first-policy-record-v1\n- Status: DONE\n- Summary: 決定 {DECISION}（2026-10-10T10:56:56Z）、既反映commit {START} の記録を重複なく追記。方針は再策定しない。\n- Files changed: design/run_log.md、design/version_log.md、固定状態JSON。\n- Verify: 同task記録の0/1確認、append-only検証。旧受入/native/ROM再構成0。\n- Commit: この追記を含む同branch通常commit。自己SHAはGit履歴/Actions resultで照合。\n- Network: GitHub最新ref/PR/Actions照会。以前中止された自動方針反映コードは使用しない。\n'
    for name in ('design/run_log.md', 'design/version_log.md'):
        append_once(root, name, policy_task, policy_log)
    write_changed(root, MANIFEST, encode(report))
    write_changed(root, GUIDE, guide(report))
    state['recording']['legacy_log_append'].update(status='DONE', task=policy_task, recorded_source_head=report['source_head'], next_ja='方針決定の追記完了。同taskを重複追記しない。')
    state['recording']['status'] = 'POLICY_LOGS_RECORDED_WIKI_INPUT_INVENTORY_COMPLETE'
    wiki = state['owner_execution_plan']['wiki']
    wiki.update(status='INPUTS_BOUND_RECONCILIATION_PENDING', input_manifest_path=MANIFEST, source_head=report['source_head'], verification_evidence_path=MANIFEST)
    wiki['limitations'] = report['remaining_gates']
    state['next_action'] = {'id': 'WIKI_R0_RECONCILE_NUMERIC_SUCCESSOR_IDENTITY', 'goal_ja': report['remaining_gates'][0], 'read_paths': [POLICY, GUIDE, MANIFEST, 'scripts/pr16_wiki_r0_inputs.py'], 'done_ja': '能力等の数値と後継習得の同一候補対応を証明後、比較可能なR0を別出力へ生成・検証する。'}
    state['recording']['last_execution'] = {'task': TASK, 'source_head': report['source_head'], 'run_id': os.environ.get('GITHUB_RUN_ID'), 'focused_tests': test_count, 'accepted_tests_rerun': 0, 'rom_changes': 0, 'native_processes': 0, 'wiki_review_ready': False, 'actions_completion_confirmed': False}
    # 固定方針へ短い現在地を追記。旧技術resume/そのhashは変更しない。
    policy = read(root, POLICY)
    marker = b'<!-- wiki-r0-input-progress -->'
    if marker not in policy:
        policy += ('\n\n<!-- wiki-r0-input-progress -->\n## R0入力監査の現在地\n\n入力の固定・検証器は実装済み。[入力監査と次の証明](PR16_WIKI_R0_INPUTS_JA.md)を参照。閲覧版の完成ではなく、現在の選択は固定状態JSONを確認する。\n<!-- /wiki-r0-input-progress -->\n').encode('utf-8')
        write_changed(root, POLICY, policy)
    binding = identity(policy)
    binding['git_blob_sha'] = hashlib.sha1(b'blob ' + str(len(policy)).encode() + b'\0' + policy).hexdigest()
    state['bindings'][POLICY] = binding
    write_changed(root, STATE, encode(state))
    log = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 旧数値と後継習得の入力監査\n- Version: wiki-r0-inputs-v1\n- Status: DONE（入力監査限定、R0未完成）\n- Summary: 旧/後継Wikiを区別して候補identity・重要入力hash・数値ID/stable key・件数を検証。候補間の意味同値を未証明のまま明示し、実装済み検証器/入力manifest/限定text snapshotを保存。\n- Files changed: R0入力検証器/試験/限定Actions、入力manifest、引継ぎMD/JSON、両ログ。\n- Verify: 新{test_count}試験、入力hash/ID検査、決定的出力比較、check無書込、task graph、最終index境界。旧受入/旧Wiki生成/ROM/nativeの再実行0。\n- Commit: この記録を含む同branch非force commit。自己SHAはGit履歴/Actions resultで照合。\n- Network: GitHub checkout/ref/PR/Actionsのみ。原本や秘密情報を取得/追加公開しない。全体CI green・R0 READY・保存修復・releaseを主張しない。\n'
    for name in ('design/run_log.md', 'design/version_log.md'):
        append_once(root, name, TASK, log)


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def guard() -> None:
    import guard_private_files as private
    actual = {p for p in git('diff', '--cached', '--name-only', '-z', START).decode().split('\0') if p}
    need(actual == CODE | OUTPUTS, '最終index範囲不一致: ' + str(actual ^ (CODE | OUTPUTS)))
    subprocess.run(['git', 'merge-base', '--is-ancestor', START, 'HEAD'], cwd=ROOT, check=True)
    for name in sorted(actual):
        raw = git('show', ':' + name)
        raw.decode('utf-8'); need(b'\0' not in raw, '新binary禁止')
        before = subprocess.run(['git', 'show', START + ':' + name], cwd=ROOT, capture_output=True).stdout
        def violations(value):
            lines = value.decode('utf-8', errors='replace').splitlines()
            return Counter(lines[n - 1] for n in private.document_user_path_lines(value))
        need(not violations(raw) - violations(before), '新private path禁止: ' + name)
        if name.startswith('design/'):
            need(raw.startswith(before), 'append-only違反')
    for path in (OLD, NEW, 'docs/wiki/stage61', 'config/active_play_baseline.json', 'content/modernization/pr16_native_supply_resume_20260913.json', 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'):
        need(not git('diff', '--cached', '--name-only', START, '--', path).strip(), '保全対象の変更: ' + path)
    subprocess.run(['git', 'diff', '--cached', '--check', START], cwd=ROOT, check=True)
    print(json.dumps({'status': 'PASS_SCOPED_FINAL_INDEX', 'paths': len(actual), 'new_private_violations': 0, 'full_historical_guard_pass_claimed': False}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'check', 'snapshot', 'record', 'guard'])
    parser.add_argument('--source-head', default=os.environ.get('GITHUB_SHA'))
    parser.add_argument('--tests', type=int, default=0)
    args = parser.parse_args()
    if args.command == 'guard':
        guard(); return
    report, exported = inspect(ROOT, args.source_head)
    if args.command == 'check':
        need(read(ROOT, MANIFEST) == encode(report) and read(ROOT, GUIDE) == guide(report), '出力不一致')
    elif args.command == 'build':
        write_changed(ROOT, MANIFEST, encode(report)); write_changed(ROOT, GUIDE, guide(report))
    elif args.command == 'record':
        need(args.tests > 0, '新試験件数が必要'); record(ROOT, report, args.tests)
    else:
        path = ROOT / '.local/pr16-wiki-r0-inputs/context.zip'
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, raw in sorted(exported.items()):
                z.writestr(name, raw)
            z.writestr('context-manifest.json', encode({'source_head': args.source_head, 'files': {n: identity(b) for n, b in sorted(exported.items())}}))
    print(json.dumps({'status': report['status'], 'inputs': len(report['input_bindings']), 'review_ready': False, 'source_head': args.source_head}, ensure_ascii=False))


if __name__ == '__main__':
    main()
