#!/usr/bin/env python3
"""実Task境界を再走せず受領し、新しい子機entryだけをnativeで有限観測する。"""
from __future__ import annotations
import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_berry_child as m
import pr16_berry_transfer_actions as prior
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT = Path(__file__).resolve().parents[1]
BASE = 'bd33727e5f3b7a04b0dfc309b2e10509fe1d2a35'
TASK = 'USER-20261011-BERRY-CHILD-ENTRY'
STATE, GUIDE, BRANCH = prior.STATE, prior.GUIDE, prior.BRANCH
REPORT = 'content/modernization/pr16_berry_child_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_berry_child_evidence'
CODE = {'scripts/pr16_berry_child.py', 'scripts/pr16_berry_child_actions.py',
        'tests/test_pr16_berry_child.py', 'tools/mgba_pr16_berry_child.c', '.github/workflows/pr16-berry-child.yml'}
LOGS = prior.LOGS
WORK = ROOT / '.local/pr16-berry-child'
PUBLIC = WORK / 'public'
PHASE = 'preflight'
ATTEMPT = {'rom_reconstructions': 0, 'native_processes': 0, 'accepted_test_reruns': 0,
           'accepted_reader_replays': 0, 'full_rom_scans': 0}
read, load, write, snapshot = prior.read, prior.load, prior.write, prior.snapshot


def public(name, value):
    (PUBLIC / name).write_bytes(m.encode(value) if isinstance(value, dict) else value)


def receive_transfer():
    source = '1b5288ca1e5f8f93bd6bcaa6c96883c413e23a9b'
    receipt = publication.accepted_run(38107409211, source,
        ['Berry実TaskからBIOS直前だけを検証して保存', 'Run actions/upload-artifact@v4'])
    artifact = a.fetch('actions/artifacts/11689504152')
    m.need(not artifact['expired'] and artifact['name'] == 'pr16-berry-transfer-public-text' and
           artifact['workflow_run']['id'] == 38107409211 and artifact['workflow_run']['head_sha'] == source and
           artifact['size_in_bytes'] == 192618 and artifact['digest'] ==
           'sha256:eece9414529296f643a89926a98de2a7182b05cfd321b635c56e75b3cc8541a8', 'transfer artifact全identity')
    raw = a.fetch('actions/artifacts/11689504152/zip', binary=True)
    m.need(m.identity(raw) == {'size': 192618, 'sha256': artifact['digest'][7:]}, 'transfer全ZIP hash')
    members = prior.old.zip_members(raw)
    m.need(set(members) == {'attempt.json', 'binding-completion.json', 'pr16_berry_transfer_checkpoint.json',
        'result.json', 'scoped-context.zip', 'transfer-boundary.json', 'transfer-tests.txt'}, '全7公開member')
    context = prior.old.zip_members(members['scoped-context.zip'])
    m.need(len(context) == 31, '全31公開text')
    for name, value in context.items():
        value.decode();m.need(b'\0' not in value and a.git('show', BASE + ':' + name) == value, '公開commit/context完全束縛')
    result = json.loads(members['result.json'])
    m.need(result['commit'] == BASE and result['source_head'] == source and
           members['pr16_berry_transfer_checkpoint.json'] == read(prior.REPORT) and
           members['transfer-boundary.json'] == read(prior.EVIDENCE + '/transfer-boundary.json'), '保存転送証拠の受領')
    receipt.update(published_commit=BASE, artifact={k: artifact[k] for k in ('id', 'name', 'digest', 'size_in_bytes')},
        members={n: m.identity(v) for n, v in members.items()}, context_bindings={n: m.identity(v) for n, v in context.items()},
        accepted_test_reruns=0, native_processes=0, rom_reconstructions=0, formal_classification_changes=0)
    return receipt


def command(args, timeout=300):
    result = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, timeout=timeout)
    if result.returncode or result.stderr:
        public('command-failure.json', {'phase': PHASE, 'tool': Path(str(args[0])).name,
            'exit_code': result.returncode, 'diagnostic': result.stderr.decode(errors='replace').replace(str(ROOT), '.')[-2000:]})
    m.need(result.returncode == 0 and not result.stderr, '新scope command失敗')
    return result.stdout


def append_logs(summary, goal):
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    block = (f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / Berry子機entryの条件付きnative reader\n'
        '- Version: berry-child-entry-v1\n- Status: STOPPED（新しい有限entry観測を保存。正式型受領/実転送/保存統合は別gate）\n'
        f'- Summary: {summary}\n- Files changed: 新しい子機native/validator/20人工試験/Actions、公開text証拠、固定MD/JSON、両ログ。\n'
        '- Verify: 新20人工試験、固定mGBA ABI/実行lib hash、native1、候補全SHA不変、保存後read-only、task graph、限定最終index。\n'
        '- Boundary: 新scope候補復元1、受入済み26試験/13profile/旧nativeの再走0。現Task転送runの全7member/31textを受領。'
        '配置はfixture、実リンク/元BIOS/Ruby実cart/自然画面到達の成功を主張しない。正式788/86・残7・安全容量0。\n'
        f'- Next: {goal}\n- Commit: この記録を含む同branch単親通常commit。実SHAはActions resultとGit履歴で照合。\n'
        '- Network: 同repo PR/ref/Actions/artifact GET、既存再構成入力、同branch非force push。固定ABI参照 '
        'https://github.com/mgba-emu/mgba/blob/0.10.2/include/mgba/core/core.h 。source/full image/ROM/saveを新規公開しない。\n')
    for name in LOGS:
        previous = read(name);m.need(('- Task: ' + TASK + ' /').encode() not in previous, '同task二重追記禁止')
        write(name, previous + block.encode())


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY') == a.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT') == '1', '同branch初回のみ')
    m.need(not WORK.exists() and not (ROOT / REPORT).exists(), '新しい子機scopeのみ')
    PUBLIC.mkdir(parents=True)
    head = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(head == os.environ['GITHUB_SHA'], 'event HEAD');a.live(head)
    m.need(not a.git('status', '--porcelain', '--untracked-files=no').strip() and
           set(a.git('diff', '--name-only', BASE, head).decode().splitlines()) == CODE, '新5sourceだけ')
    m.need(not a.git('ls-files', '--', *[n + '/AGENTS.md' for n in ('tools', 'scripts', 'tests', 'docs', 'design',
        '.github', '.github/workflows', 'content', 'content/modernization')]).strip(), '追加AGENTSの読取りが必要')
    state = load(STATE);lane = state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id'] == 'SAVE_CAPACITY_BERRY_BIOS_PAYLOAD_READER' and
           [lane[k] for k in ('classified', 'unclassified', 'selected_unknown_origins', 'donor_safe_bytes')] == [788, 86, 7, 0], '現在の未完lane')
    cp = load(prior.REPORT)
    protected = set(cp['source_bindings']) | set(cp['evidence_bindings']) | set(cp['preserved_inputs']) | {prior.REPORT}
    for key in ('source_bindings', 'evidence_bindings', 'preserved_inputs'):
        m.need(all(m.identity(read(n)) == want for n, want in cp[key].items()), '全継承入力のidentity')
    before = snapshot(protected)
    wiki = m.encode({k: state['owner_execution_plan'][k] for k in ('wiki', 'wiki_readability', 'owner_review', 'scope')})
    PHASE = 'new-child-unit-tests'
    stream = io.StringIO();suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_pr16_berry_child.py')
    tests = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    public('child-tests.txt', stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun == 20 and not tests.skipped, '新20人工試験')
    subprocess.run(['python3', '-B', 'scripts/validate_task_graph.py'], cwd=ROOT, check=True, capture_output=True)
    PHASE = 'completed-transfer-receipt-without-replay'
    receipt = receive_transfer()
    PHASE = 'new-native-build'
    version = command(['dpkg-query', '-W', '-f=${Version}', 'libmgba-dev']).decode().strip()
    library = Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes()
    header = Path('/usr/include/mgba/core/core.h').read_bytes()
    m.need(version == '0.10.2+dfsg-1.1build3' and m.identity(library) == m.LIBRARY and
           m.parent.parent.blob(header) == 'd3f2b4e044e71f78d666ebfe7db2389a10f13a9c', '固定mGBA libraryと7API ABI')
    binary = WORK / 'native'
    command(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', ROOT / 'tools/mgba_pr16_berry_child.c', '-lmgba', '-lm', '-o', binary])
    PHASE = 'one-new-child-scope-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT = WORK / 'candidate';reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions'] = 1;public('attempt.json', ATTEMPT)
    with (WORK / 'private-reconstruction.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        raw, candidate = reconstruction.reconstruct()
    m.need(m.identity(raw) == candidate['candidate'] == m.parent.parent.CANDIDATE, '現候補全SHA/配置')
    path = WORK / 'candidate.gba';path.write_bytes(raw)
    PHASE = 'bounded-child-entry-native'
    ATTEMPT['native_processes'] = 1;public('attempt.json', ATTEMPT)
    native = json.loads(command([binary, path], timeout=120));public('native.json', native)
    m.need(path.read_bytes() == raw, '全ROM file不変')
    proof = m.bind(raw, native, load(prior.EVIDENCE + '/transfer-boundary.json'))
    proof.update(library=m.LIBRARY, library_package_version=version, abi_header=m.identity(header),
        native_binary=m.identity(binary.read_bytes()), **ATTEMPT)
    total = proof['reader']['target_bytes_issued'];full = proof['reader']['all_four_bytes_issued']
    summary = (f'現Taskが渡す13456byteを子機RAMへ事前配置し、ARM header entryから{native["steps"]}stepをnativeで有限観測。'
        f'対象0x086C51BFに対応する0x02000913の{total}/4byteが実命令発行spanに含まれた。'
        f'停止理由={native["stop_reason"]}、PC={native["stop_pc"]:#010x}。entry後host書込7APIを拒否。')
    goal = ('今回の子機native/20試験を再走せず成功run全memberを受領し、条件付き実readerの全4byte来歴と正式型追加を照合する。'
            if full else '保存した子機entryの発行span・停止PC/registerを継承し、未発行byteへ続く実callee/配置/入力条件だけを有限に接続する。成功した親13profileと今回の同一entryを再走しない。')
    goal += ' 実BIOS転送/自然リンク/元cart/全間接参照/容量移管/heap/controller/局所Saveは未完。正式788/86・残7・安全容量0。'
    names = {'child-reader.json': proof, 'native.json': native, 'transfer-completion.json': receipt,
             'child-tests.txt': stream.getvalue().encode()}
    proofs = {EVIDENCE + '/' + name for name in names}
    for name, value in names.items():write(EVIDENCE + '/' + name, value)
    saved = snapshot(proofs)
    m.need(load(EVIDENCE + '/child-reader.json') == proof and snapshot(proofs) == saved, '保存後read-only')
    m.need(before == snapshot(protected), '全受入済み原本byte/mtime')
    observed = a.live(head)
    report = {'schema_version': 1, 'task': TASK, 'source_head': head, 'status': proof['status'],
        'actions_run_id': int(os.environ['GITHUB_RUN_ID']), 'actions_completion_confirmed': False,
        'candidate': candidate['candidate'], 'new_unit_tests': tests.testsRun, 'target_bytes_issued': total,
        'source_bindings': {n: m.identity(read(n)) for n in sorted(CODE)},
        'preserved_inputs': {n: row[0] for n, row in before.items()},
        'evidence_bindings': {n: m.identity(read(n)) for n in sorted(proofs)},
        'formal_classified': 788, 'formal_unclassified': 86, 'selected_unknown_origins': 7, 'donor_safe_bytes': 0,
        'read_only_check_passed': True, 'task_graph_passed': True, 'next_ja': goal, 'observed_head_checks': observed, **ATTEMPT}
    write(REPORT, report)
    action = 'SAVE_CAPACITY_BERRY_CHILD_READER_RECEIPT' if full else 'SAVE_CAPACITY_BERRY_CHILD_ENTRY_CONTINUATION'
    lane.update(status=proof['status'], checkpoint_path=REPORT, next_ja=goal, scheduling_status='READY_FROM_SAVED_CHILD_ENTRY')
    state['next_action'] = {'id': action, 'goal_ja': goal, 'read_paths': [GUIDE, REPORT, EVIDENCE + '/child-reader.json'],
        'done_ja': '子機/転送の実readerと対象全4byteを束縛し、完了runを別途受領後だけ型台帳を更新する。'}
    state['observed_head_checks'] = observed
    state['recording']['last_execution'] = {k: report[k] for k in ('task', 'source_head', 'actions_run_id',
        'actions_completion_confirmed', 'new_unit_tests', 'target_bytes_issued', 'read_only_check_passed', 'task_graph_passed', *ATTEMPT.keys())}
    state['recording'].update(task=TASK, source_head=head, status=proof['status'],
        received_berry_transfer_completion=EVIDENCE + '/transfer-completion.json',
        pending_berry_child_run={'run_id': int(os.environ['GITHUB_RUN_ID']), 'source_head': head, 'output_report': REPORT,
                               'status': 'COMPLETION_NOT_YET_OBSERVED', 'replay_forbidden': True})
    state['recording']['pending_berry_transfer_run'].update(status='COMPLETION_BOUND_WITHOUT_REPLAY',
        completion_evidence_path=EVIDENCE + '/transfer-completion.json')
    text = read('CHATGPT_RESUME.md').decode();left, remainder = text.split('## 次の未完作業\n', 1)
    _, right = remainder.split('\n所有者が閲覧版で', 1)
    text = left + '\n## 次の未完作業\n\n現在の next_action は ' + action + '。' + summary + ' ' + goal + \
        ' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で' + right
    write('CHATGPT_RESUME.md', text.encode())
    state['bindings']['CHATGPT_RESUME.md'] = {'git_blob_sha': m.parent.parent.blob(text.encode()), **m.identity(text.encode())}
    m.need(wiki == m.encode({k: state['owner_execution_plan'][k] for k in ('wiki', 'wiki_readability', 'owner_review', 'scope')}), 'Wiki/未承認/安全方針保全')
    write(STATE, state)
    guide = read(GUIDE).decode().replace('## 次の未完作業', '## 以前の停止点（履歴）')
    m.need('## Berry子機entryの条件付きnative' not in guide, '同一引継ぎ二重追記禁止')
    guide += f'\n## Berry子機entryの条件付きnative\n\n{summary}\n\n[子機reader証拠](../{EVIDENCE}/child-reader.json) / [checkpoint](../{REPORT}) / [親転送run受領](../{EVIDENCE}/transfer-completion.json)。'
    guide += '\n\n配置はfixture。mGBA builtin BIOSであり、元BIOSや実Ruby/Sapphire cart/自然リンク/実転送成功ではない。新20試験・native1・候補復元1、旧26試験/13profile/native再走0。正式型と安全容量は増やさない。\n\n## 次の未完作業\n\n' + goal + '\n'
    write(GUIDE, guide.encode());append_logs(summary, goal)
    PHASE = 'final-index-and-nonforce-push'
    allowed = CODE | proofs | LOGS | {REPORT, STATE, GUIDE, 'CHATGPT_RESUME.md'}
    publication.final_index(BASE, allowed, REPORT)
    m.need(before == snapshot(protected), 'push前旧原本保全')
    m.need(a.git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == head, 'push直前HEAD')
    a.git('config', 'user.name', 'github-actions[bot]');a.git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit', '-m', TASK + ': 子機entryの実発行境界と次の未完作業を保存')
    a.git('push', 'origin', 'HEAD:' + BRANCH)
    pushed = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(a.git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == pushed, 'push後HEAD')
    for name in allowed:m.need(a.git('show', 'HEAD:' + name) == read(name), '全commit blob')
    for name in proofs | {REPORT}:public(name.rsplit('/', 1)[-1], read(name))
    with zipfile.ZipFile(PUBLIC / 'scoped-context.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted((allowed | protected) - LOGS):archive.writestr(name, read(name))
    public('result.json', {'status': proof['status'], 'source_head': head, 'commit': pushed,
        'actions_run_id': int(os.environ['GITHUB_RUN_ID']), 'new_unit_tests': tests.testsRun,
        'target_bytes_issued': total, 'formal_classified': 788, 'formal_unclassified': 86,
        'selected_unknown_origins': 7, 'donor_safe_bytes': 0, **ATTEMPT})
    print(f'RESULT=STOPPED TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__ == '__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True, exist_ok=True)
        frames = [{'path': f.filename[len(str(ROOT)) + 1:], 'line': f.lineno}
                  for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT) + '/scripts/')]
        public('failure.json', {'status': 'NOT_ACCEPTED', 'phase': PHASE, 'exception_type': type(exc).__name__,
            'detail': str(exc).replace(str(ROOT), '.')[:300] if isinstance(exc, ValueError) else None,
            'frames': frames, 'attempt': ATTEMPT})
        print('RESULT=BLOCKED TASK=' + TASK + ' VERIFY=FAIL PHASE=' + PHASE + ' TYPE=' + type(exc).__name__)
        sys.exit(1)
