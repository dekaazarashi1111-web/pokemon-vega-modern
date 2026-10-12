#!/usr/bin/env python3
"""明示許可されたPR16の同branchへ、検証済み閲覧資料と記録だけを非force反映する。"""
from __future__ import annotations
from collections import Counter
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile
import pr16_wiki_readability as w

REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
START = '268c6f18411f3893ea5f8676c8ddc3e081b29897'
STATE = 'content/modernization/pr16_wiki_first_execution_plan.json'
PROOF = 'content/modernization/pr16_wiki_readability_verification.json'
RECEIPT = 'content/modernization/pr16_wiki_readability_receipt.json'
PRESENTATION = 'content/modernization/pr16_wiki_readability_presentation.json'
GUIDE = 'docs/PR16_WIKI_READABILITY_STATUS_JA.md'
LOGS = {'design/run_log.md', 'design/version_log.md'}
CODE = {'scripts/pr16_wiki_readability.py', 'scripts/pr16_wiki_readability_publish.py', 'tests/test_pr16_wiki_readability.py', '.github/workflows/pr16-wiki-readability.yml'}
WORK = w.ROOT/'.local/pr16-wiki-readability'


def git(*args):
    return subprocess.run(['git', *args], cwd=w.ROOT, check=True, capture_output=True).stdout


def api(path):
    req = urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path, headers={'Authorization': 'Bearer '+os.environ['GITHUB_TOKEN'], 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write(name, raw):
    path = w.ROOT/name
    w.need(not path.is_symlink(), '記録symlink禁止')
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != raw:
        path.write_bytes(raw)


def preflight(source):
    w.need(os.environ['GITHUB_REPOSITORY'] == REPO and os.environ['GITHUB_REF'] == 'refs/heads/'+BRANCH, 'repo/ref境界')
    w.need(git('rev-parse', 'HEAD').decode().strip() == source, 'checkout identity')
    git('merge-base', '--is-ancestor', START, source)
    w.need(git('ls-remote', 'origin', 'refs/heads/'+BRANCH).decode().split()[0] == source, 'live HEAD競合')
    pr = api('pulls/16')
    w.need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == source and pr['head']['ref'] == BRANCH and pr['head']['repo']['full_name'] == REPO, 'PR同一性/状態')
    nested = git('ls-files', '--', 'scripts/AGENTS.md', 'tests/AGENTS.md', 'docs/AGENTS.md', 'docs/wiki/AGENTS.md', w.OUT+'/AGENTS.md', 'content/AGENTS.md', 'content/modernization/AGENTS.md', 'design/AGENTS.md', '.github/AGENTS.md', '.github/workflows/AGENTS.md')
    w.need(not nested.strip(), '追加AGENTSを先に読む必要あり')
    git('diff', '--exit-code', w.BASE_COMMIT, 'HEAD', '--', w.BASE, 'docs/wiki/p08-candidate-46487d98', 'docs/wiki/issue19-candidate-6e88a021', 'docs/wiki/stage61')
    runs = api('actions/runs?head_sha='+source+'&per_page=100')
    w.need(runs['total_count'] <= len(runs['workflow_runs']), 'Actions未取得ページ')
    return {'source_head': source, 'scope': 'ALL_EVENTS_FOR_EXACT_HEAD_AT_OBSERVATION', 'all_ci_green_claimed': False, 'runs': [{k: r.get(k) for k in ('id', 'name', 'head_sha', 'event', 'status', 'conclusion')} for r in runs['workflow_runs']]}


def append(task, summary, verify, status='DONE', skip_existing=False):
    now = stamp()
    text = (f'\n## {now}\n- Timestamp: {now}\n- Task: {task} / Wiki閲覧改善\n- Version: wiki-r0.1-6e88a021\n- Status: {status}\n- Summary: {summary}\n- Files changed: 閲覧生成器/限定試験/専用Actions、別出力R0.1、固定入口/引継ぎMD/状態JSON、検証証拠、両ログ。原本・旧Wiki・ゲームは不変。\n- Verify: {verify}\n- Commit: この記録を含む同branchの単親通常commit。実SHAはActions resultとGit履歴で照合。\n- Network: GitHubの指定repo/PR/HEAD/Actions読取と同branchへの非force pushのみ。ROM/native再走0。\n').encode()
    for name in sorted(LOGS):
        before = w.read(w.ROOT, name)
        exists = ('- Task: '+task+' /').encode() in before
        if exists and skip_existing:
            continue
        w.need(not exists, '同task追記済み・再走禁止')
        write(name, before+text)


def bind_entry(state):
    for name in ('CHATGPT_RESUME.md', GUIDE):
        raw = w.read(w.ROOT, name)
        state['bindings'][name] = w.identity(raw) | {'git_blob_sha': git('hash-object', name).decode().strip()}


def guide(proof, presented=False, commit=None):
    status = '公開・提示受領済み。次は保存したBerry現owner/readerの未完scope。' if presented else '生成・限定検証済み。固定公開commitと実物レビュー・提示・完了Actionsの受領はまだ。'
    return ('# Wiki R0.1 閲覧改善の固定引継ぎ\n\n'+status+'\n\n[閲覧入口](wiki/r0.1-6e88a021/README.md) / [ベガ比較](wiki/r0.1-6e88a021/VEGA_BALANCE_INDEX.md) / [全種族](wiki/r0.1-6e88a021/POKEMON_INDEX.md) / [技](wiki/r0.1-6e88a021/MOVE_INDEX.md) / [特性](wiki/r0.1-6e88a021/ABILITY_INDEX.md)。\n\n[検証](../'+PROOF+') / [全member manifest](wiki/r0.1-6e88a021/data/index.json) / [固定状態JSON](../'+STATE+')。\n\n役割候補は全種族の判断用表示から除外。リーテイルLv46こうごうせいを含む全習得/逆引き/条件byteとゲーム情報は不変。技術JSONは詳細へ折り畳み、4主要一覧を人向けに整理。\n\nファイル数 '+str(proof['files'])+'、展開size '+str(proof['bytes'])+'、検証リンク '+str(proof['links'])+'。ZIP `'+proof['package']['name']+'`、size '+str(proof['package']['size'])+'、SHA-256 `'+proof['package']['sha256']+'`。資料限定、展開/全member hash/内部リンク/決定性を確認済み。\n\n入力R0 commit `'+w.BASE_COMMIT+'`、生成source `'+proof['source_head']+'`、公開commit `'+str(commit or '提示受領時に束縛')+'`。Actions run '+str(proof['actions_run_id'])+' の `pr16-wiki-readability-package` artifactを使うか、READMEの限定packageコマンドで再現する。外側artifact ZIPには内側の閲覧ZIPが含まれる。\n\n参考JSON内の旧repository pathは来歴で、旧機械読取原本/実行環境を資料ZIPへ同梱しない。全習得のMarkdown閲覧導線は内部完結。説明は完全な実効果仕様ではない。\n\n旧R0/原本/受入証拠は不変。全クリ対象外（PASSではない）、保存安全性は未完。正式788分類/86未知・選定残7・安全容量0を保持。全体private guardの既存違反や無関係なCI失敗は解消と主張しない。未承認バランス変更、merge、release、baseline切替なし。\n').encode()


def final_index(base, allowed, state, proof, proof_path):
    git('add', '--', *sorted(allowed))
    result = subprocess.run(['python3', '-B', 'scripts/guard_private_files.py'], cwd=w.ROOT, capture_output=True)
    guard = {'executed': True, 'passed': result.returncode == 0, 'exit_code': result.returncode, 'historical_violations_not_rewritten': True, 'raw_private_log_published': False}
    proof['full_index_private_guard'] = guard
    state['recording']['wiki_readability_execution']['full_index_private_guard'] = guard
    write(proof_path, w.encode(proof))
    write(STATE, w.encode(state))
    git('add', '--', STATE, proof_path)
    actual = {n for n in git('diff', '--cached', '--name-only', '-z', base).decode().split('\0') if n}
    w.need(actual == allowed, '最終index許可範囲の不一致')
    import guard_private_files as private
    for name in sorted(actual):
        raw = git('show', ':'+name)
        raw.decode()
        w.need(b'\0' not in raw, '新binary禁止')
        old = subprocess.run(['git', 'show', base+':'+name], cwd=w.ROOT, capture_output=True).stdout
        def violations(value):
            lines = value.decode(errors='replace').splitlines()
            return Counter(lines[n-1] for n in private.document_user_path_lines(value))
        w.need(not violations(raw)-violations(old), '変更pathへのprivate記載追加')
        if name in LOGS:
            w.need(raw.startswith(old), 'append-only違反')
    git('diff', '--cached', '--check', base)
    (WORK/'proof/index.json').write_bytes(w.encode({'status': 'PASS_SCOPED_INDEX', 'paths': len(actual), 'full_index_private_guard': guard}))


def publish(source, task):
    w.need(git('ls-remote', 'origin', 'refs/heads/'+BRANCH).decode().split()[0] == source, 'push直前HEAD競合')
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    git('commit', '-m', task+': 閲覧改善の限定検証・固定状態・両ログを保存')
    git('push', 'origin', 'HEAD:'+BRANCH)
    commit = git('rev-parse', 'HEAD').decode().strip()
    w.need(git('ls-remote', 'origin', 'refs/heads/'+BRANCH).decode().split()[0] == commit, 'push後HEAD不一致')
    for name in (STATE, GUIDE):
        w.need(git('show', commit+':'+name) == w.read(w.ROOT, name), 'commit blob読戻し不一致')
    result = {'status': 'PUBLISHED', 'source_head': source, 'commit': commit, 'task': task, 'force': False}
    (WORK/'proof/result.json').write_bytes(w.encode(result))
    print(f'RESULT=DONE TASK={task} VERIFY=PASS COMMIT={commit}')
    return commit


def build(source, observed):
    w.need(not (w.ROOT/w.OUT).exists(), 'R0.1は既に実在。成功生成を再走しない')
    state = json.loads(w.read(w.ROOT, STATE))
    wk = state['owner_execution_plan']['wiki_readability']
    w.need(state['next_action']['id'] == 'WIKI_READABILITY_FIX' and not wk['ready'], '閲覧改善の優先状態不一致')
    files, manifest = w.generate(w.ROOT, source)
    w.validate_links(files)
    w.write_files(w.ROOT, files)
    proof = w.check(w.ROOT)
    package = w.package(w.ROOT, WORK/'package/wiki-r0.1-6e88a021.zip')
    tests = json.loads((WORK/'proof/unit-result.json').read_bytes())
    w.need(tests['tests'] > 0 and tests['failures'] == tests['errors'] == tests['skipped'] == 0, '限定試験未成功')
    proof.update(source_head=source, actions_run_id=int(os.environ['GITHUB_RUN_ID']), actions_completion_confirmed=False, focused_tests=tests['tests'], package=package, accepted_test_reruns=0, native_processes=0, rom_reconstructions=0, historical_snapshots_preserved=True, task_graph_passed=True, code_bindings={n: w.identity(w.read(w.ROOT, n)) for n in sorted(CODE)})
    berry = api('actions/runs/38099840927')
    w.need(berry['head_sha'] == '359d3fae20d5d0e25342c0e1b8daac921aa0e646', '保留Berry run identity')
    berry_record = {k: berry[k] for k in ('id', 'head_sha', 'status', 'conclusion')}
    state['recording']['pending_berry_origin_run'].update(status='COMPLETED_RESULT_OBSERVED' if berry['status'] == 'completed' else 'COMPLETION_NOT_YET_OBSERVED', observed=berry_record, acceptance_not_inferred=True)
    proof['prior_berry_run_observed_without_rerun'] = berry_record
    wk.update(status='VERIFIED', ready=False, source_head=source, entry_path=w.OUT+'/README.md', input_manifest_path=w.OUT+'/data/index.json', verification_evidence_path=PROOF, package=package | {'actions_run_id': proof['actions_run_id'], 'artifact_name': 'pr16-wiki-readability-package', 'artifact_upload_confirmed': False}, core_game_semantic_sha256=proof['core_game_semantic_sha256'], tree_sha256=proof['tree_sha256'])
    for key in wk['completion_gates']:
        wk['completion_gates'][key] = key not in {'human_md_tables_reviewed', 'published_and_presented'}
    wk['next_ja'] = '公開commitと完了Actions/packageを取得し、4主要MDとリーテイルを実物確認、固定入口とZIPを会話で提示してpresentation証拠を記録する。生成/native/受入試験は再走しない。'
    state['next_action']['goal_ja'] = wk['next_ja']
    state['next_action']['read_paths'] = [GUIDE, PROOF, w.OUT+'/README.md']
    state['observed_head_checks'] = observed
    state['recording']['wiki_readability_execution'] = {'task': 'USER-20261011-WIKI-READABILITY-BUILD', 'source_head': source, 'actions_run_id': proof['actions_run_id'], 'focused_tests': tests['tests'], 'accepted_test_reruns': 0, 'native_processes': 0, 'rom_reconstructions': 0, 'all_ci_green_claimed': False}
    state['recording']['status'] = 'WIKI_READABILITY_VERIFIED_PRESENTATION_PENDING'
    append('USER-20261011-WIKI-READABILITY-PRIORITY', '所有者2026-10-11T01:23:24Zの方針変更の未追記事務記録を補完。決定の再策定やWiki完成宣言ではない。', '既存task markerを各ログで検索し未追記分だけ追加。', skip_existing=True)
    state['recording']['wiki_readability_priority_update']['legacy_log_append'].update(status='DONE', next_ja='事務追記済み。同taskを再追記しない。')
    write(GUIDE, guide(proof))
    entry = w.read(w.ROOT, 'CHATGPT_RESUME.md')
    marker = '\n## 閲覧改善の実装・検証記録\n\n[固定引継ぎ](docs/PR16_WIKI_READABILITY_STATUS_JA.md) を参照。現在状態は同じJSONのwiki_readabilityに記録し、生成成功と実物提示の受領を区別する。\n'
    w.need(marker.encode() not in entry, '入口記録済み')
    write('CHATGPT_RESUME.md', entry+marker.encode())
    bind_entry(state)
    append('USER-20261011-WIKI-READABILITY-BUILD', f'R0.1 {proof["files"]}資料、主要4表と全詳細、役割要約の共通除去、参考JSON隔離、実在ZIPを生成。全習得/条件/逆引きとゲーム情報不変。提示受領は未完。', f'限定{tests["tests"]}試験、task graph、{proof["links"]}リンク、決定性/check byte+mtime、ZIP展開/member/hash PASS。新native/ROM再構成/旧受入再走0。')
    write(PROOF, w.encode(proof))
    write(STATE, w.encode(state))
    allowed = CODE | LOGS | {GUIDE, STATE, PROOF, 'CHATGPT_RESUME.md'} | {w.OUT+'/'+n for n in files}
    final_index(START, allowed, state, proof, PROOF)
    commit = publish(source, 'USER-20261011-WIKI-READABILITY-BUILD')
    (WORK/'proof/verification.json').write_bytes(w.read(w.ROOT, PROOF))
    (WORK/'proof/package.json').write_bytes(w.encode(package | {'wiki_commit': commit}))


def receive(source, observed):
    p = json.loads(w.read(w.ROOT, PRESENTATION))
    proof = json.loads(w.read(w.ROOT, PROOF))
    state = json.loads(w.read(w.ROOT, STATE))
    wk = state['owner_execution_plan']['wiki_readability']
    w.need(not wk['ready'] and wk['status'] == 'VERIFIED', '提示受領済み/生成未完')
    w.need(p['presented_to_owner'] is True and p['human_md_reviewed'] is True and p['owner_approval_granted'] is False, '実物提示/承認区分')
    w.need(p['entry_path'] == w.OUT+'/README.md' and p['build_run_id'] == proof['actions_run_id'] and p['package_sha256'] == proof['package']['sha256'], '提示版identity')
    git('merge-base', '--is-ancestor', p['wiki_commit'], 'HEAD')
    w.need(not git('diff', '--name-only', p['wiki_commit'], 'HEAD', '--', w.OUT).strip(), '提示Wiki変更あり')
    files, manifest = w.read_output(w.ROOT)
    w.need(w.identity(files['data/index.json'])['sha256'] == p['manifest_sha256'], '提示manifest不一致')
    run = api('actions/runs/'+str(p['build_run_id']))
    w.need(run['status'] == 'completed' and run['conclusion'] == 'success' and run['head_sha'] == proof['source_head'], '生成Actions未成功')
    jobs = api('actions/runs/'+str(p['build_run_id'])+'/jobs?per_page=100')
    w.need(jobs['total_count'] == len(jobs['jobs']) and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in jobs['jobs']), '生成job未成功')
    artifact = api('actions/artifacts/'+str(p['artifact_id']))
    w.need(artifact['workflow_run']['id'] == p['build_run_id'] and artifact['name'] == 'pr16-wiki-readability-package' and not artifact['expired'], 'package artifact identity')
    value = {'schema_version': 1, 'status': 'PASS_PUBLISHED_PRESENTED_R0_1', 'presentation': p, 'build_actions': {'id': run['id'], 'status': run['status'], 'conclusion': run['conclusion'], 'source_head': run['head_sha']}, 'files': len(files), 'generated_again': False, 'accepted_test_reruns': 0, 'native_processes': 0, 'all_ci_green_claimed': False, 'source_head': source}
    wk.update(status='READY_FOR_REVIEW', ready=True, presented_to_owner=True, published_commit=p['wiki_commit'], presentation_evidence=PRESENTATION, receipt_path=RECEIPT, next_ja='閲覧版固定・提示済み。保存した最新Berry現owner/readerの未完scopeへ戻る。')
    wk['package'].update(artifact_upload_confirmed=True, artifact_id=p['artifact_id'], artifact_digest=artifact.get('digest'))
    wk['completion_gates'] = {key: True for key in wk['completion_gates']}
    state['next_action'] = wk['paused_technical_next_action']
    state['owner_execution_plan']['phase'] = 'SAVE_CAPACITY_INTEGRATION'
    state['owner_execution_plan']['technical_lanes']['save_capacity']['scheduling_status'] = 'READY_FROM_PRESERVED_BERRY_FRONTIER'
    state['owner_execution_plan']['owner_review']['reference_revision'] = 'R0.1'
    state['observed_head_checks'] = observed
    state['recording']['wiki_readability_execution'] = {'task': 'USER-20261011-WIKI-READABILITY-RECEIPT', 'source_head': source, 'actions_run_id': int(os.environ['GITHUB_RUN_ID']), 'completed_build_run': run['id'], 'accepted_test_reruns': 0, 'generated_again': False, 'all_ci_green_claimed': False}
    state['recording']['status'] = 'R0_1_PUBLISHED_PRESENTED_BERRY_OWNER_READER_NEXT'
    write(GUIDE, guide(proof, True, p['wiki_commit']))
    write('CHATGPT_RESUME.md', ('# ChatGPTの固定再開入口\n\n対象はPR #16 / `'+BRANCH+'`。毎回リモート最新HEADとPR状態を確認し、そのrefを読む。過去SHAへ戻さない。\n\n## 正本と現在地\n\n1. [AGENTS.md](AGENTS.md) の安全・検証・Git規約。\n2. [固定状態JSON]('+STATE+') の next_action と owner_execution_plan。\n3. [Wiki R0.1の完了証拠と入口]('+GUIDE+')。\n4. [閲覧改善の範囲/完成条件](docs/PR16_WIKI_READABILITY_PRIORITY_JA.md) と [継続する長期方針](docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md)。\n\nR0.1は別出力として実装・限定検証・パッケージ生成/展開確認・公開・実物提示受領まで完了。旧R0は不変。成功済みの生成/28試験/nativeを変更影響なしに再実行しない。実在入口/公開commit/ZIP hashはwiki_readabilityに保持する。\n\n## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_BERRY_ORIGIN_ACTUAL_OWNER_READER。保存した0x086C51BF近傍の限定identity、公開assetとのlocale差、consumer frontierから現ownerと実readerを有限範囲で結ぶ。固定JSONの read_paths と technical_lanes.save_capacity を参照する。正式788分類/86未知・選定残7・安全容量0。古い784/90や08397492へ戻らない。保留run38099840927は記録済みobserved結果を照合し、成功測定を再起動しない。結果照会と型分類/受入を混同しない。\n\n所有者が閲覧版で案を検討する間も、実作業セッションでは保存容量→CI整合→追加機構の技術確認を継続する。未承認バランス案や新メガ/Gmax/Zの対象・性能は決めない。無人バックグラウンド実行の約束ではない。\n\n## 毎回の終了\n\n同じ状態JSONと固定引継ぎMDへ実完了・根拠・残件・最新Actions・具体nextを保存する。両ログはappend-only、同taskを重複しない。限定検証と最終index private guardの結果を区別し、全体CI greenを推測しない。小さな単親通常commitを明示許可された同branchへ非force反映し、push前後HEAD/対象blobを照合する。原本ROM/Save101と受入証拠を保持。全クリ対象外（PASSではない）、保存安全性は必須。merge・draft解除・公開release・active baseline切替は別許可なしに実行しない。\n').encode())
    bind_entry(state)
    append('USER-20261011-WIKI-READABILITY-RECEIPT', '固定公開R0.1/実物4主要MD/リーテイル/資料ZIPと完了Actionsを照合して会話提示を受領。全閲覧改善gate完了。正式788/86・選定残7・安全容量0のBerry未完へ復帰。', '生成run completed/success、公開member hash/集合・提示manifest/package/外部artifact identity・task graph PASS。生成/28試験/native再走0。')
    write(RECEIPT, w.encode(value))
    write(STATE, w.encode(state))
    allowed = LOGS | {PRESENTATION, RECEIPT, STATE, GUIDE, 'CHATGPT_RESUME.md'}
    final_index(p['wiki_commit'], allowed, state, value, RECEIPT)
    publish(source, 'USER-20261011-WIKI-READABILITY-RECEIPT')
    (WORK/'proof/receipt.json').write_bytes(w.read(w.ROOT, RECEIPT))


def main():
    (WORK/'proof').mkdir(parents=True, exist_ok=True)
    source = os.environ['GITHUB_SHA']
    observed = preflight(source)
    if (w.ROOT/PRESENTATION).exists():
        receive(source, observed)
    else:
        build(source, observed)


if __name__ == '__main__':
    try:
        main()
    finally:
        (WORK/'proof').mkdir(parents=True, exist_ok=True)
        names = CODE | {STATE, PROOF, RECEIPT, PRESENTATION, GUIDE, 'CHATGPT_RESUME.md', 'AGENTS.md', w.OUT+'/data/index.json', w.OUT+'/README.md', w.OUT+'/VEGA_BALANCE_INDEX.md', w.OUT+'/POKEMON_INDEX.md', w.OUT+'/MOVE_INDEX.md', w.OUT+'/ABILITY_INDEX.md', w.OUT+'/pokemon/3.md'}
        with zipfile.ZipFile(WORK/'context.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(names):
                if (w.ROOT/name).is_file():
                    archive.writestr(name, w.read(w.ROOT, name))
