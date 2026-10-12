#!/usr/bin/env python3
"""許可branchで新しい転送境界だけを検証し、原本を保全して小さな通常commitへ記録する。"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import traceback
import unittest
import zipfile

import pr16_berry_transfer as m
import pr16_berry_origin_actions as old
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT = Path(__file__).resolve().parents[1]
BASE = '1309692f0282a020cda420872962edbae4c5e855'
BRANCH = 'codex/modernization-followup-20260908'
TASK = 'USER-20261011-BERRY-TRANSFER-BOUNDARY'
STATE = old.STATE
GUIDE = old.GUIDE
REPORT = 'content/modernization/pr16_berry_transfer_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_berry_transfer_evidence'
WF = '.github/workflows/pr16-berry-transfer.yml'
CODE = {WF, 'scripts/pr16_berry_transfer.py', 'scripts/pr16_berry_transfer_actions.py',
        'tests/test_pr16_berry_transfer.py'}
PROOFS = {EVIDENCE + '/' + n for n in ('transfer-boundary.json', 'binding-completion.json', 'transfer-tests.txt')}
LOGS = {'design/run_log.md', 'design/version_log.md'}
WORK = ROOT / '.local/pr16-berry-transfer'
PUBLIC = WORK / 'public'
PHASE = 'preflight'
ATTEMPT = {'rom_reconstructions': 0, 'native_processes': 0, 'accepted_test_reruns': 0, 'full_rom_scans': 0}
PUBLIC_PATHS = {**{n: v for n, v in m.parent.PUBLIC_PATHS.items() if n.startswith('src/')},
    'include/gba/multiboot.h': 'a8bc8fddfd820eda38ba8fba4fd1db917bccc1ae',
    'include/task.h': '2f9f1c0d8755572d5ccc5c4190339ffaca2d4bbf',
    'include/multiboot.h': 'ee0a34c83f6ca63295aa7e515fbf2dae3fac8176'}


def read(name):
    path = ROOT / name
    m.need(path.is_file() and not path.is_symlink(), '通常text: ' + name)
    return path.read_bytes()


def load(name):
    return json.loads(read(name))


def write(name, value):
    a.changed_write(name, m.encode(value) if isinstance(value, dict) else value)


def public(name, value):
    (PUBLIC / name).write_bytes(m.encode(value) if isinstance(value, dict) else value)


def snapshot(names):
    return {n: (m.identity(read(n)), (ROOT / n).stat().st_mtime_ns) for n in sorted(names)}


def receive_binding():
    source, published = '359d3fae20d5d0e25342c0e1b8daac921aa0e646', '4ed0e9e96aa8e5e1b8755225cc6565fd3e6d8e7f'
    receipt = publication.accepted_run(38099840927, source,
        ['Verify new berry origin binding without accepted replay', 'Run actions/upload-artifact@v4'])
    artifact = a.fetch('actions/artifacts/11687346108')
    m.need(artifact['name'] == 'pr16-berry-origin-public-text' and not artifact['expired'] and
           artifact['workflow_run']['id'] == 38099840927 and artifact['workflow_run']['head_sha'] == source and
           artifact['size_in_bytes'] == 98324 and artifact['digest'] ==
           'sha256:34127bc87ef8c9870b68dceace0e1672618720caa3f24a06693a535d1ed39610', 'Berry artifact identity')
    raw = a.fetch('actions/artifacts/11687346108/zip', binary=True)
    m.need(m.identity(raw) == {'size': 98324, 'sha256': artifact['digest'][7:]}, '全ZIP hash')
    members = old.zip_members(raw)
    m.need(set(members) == {'attempt.json', 'bounded-binding.json', 'binding-tests.txt',
        'pr16_berry_origin_checkpoint.json', 'prior-actions.json', 'result.json', 'scoped-context.zip'}, '全7member')
    context = old.zip_members(members['scoped-context.zip'])
    m.need(len(context) == 25, '全25保存text')
    for name, value in context.items():
        value.decode('utf-8')
        m.need(b'\0' not in value and a.git('show', published + ':' + name) == value, '公開commit全text')
    result = json.loads(members['result.json'])
    m.need(result['commit'] == published and result['source_head'] == source and
           members['pr16_berry_origin_checkpoint.json'] == read(old.REPORT) and
           members['bounded-binding.json'] == read(old.EVIDENCE + '/bounded-binding.json'), '保存測定原本')
    receipt.update(artifact={k: artifact[k] for k in ('id', 'name', 'digest', 'size_in_bytes')},
        members={n: m.identity(v) for n, v in members.items()},
        context_bindings={n: m.identity(v) for n, v in context.items()}, published_commit=published,
        actual_consumer_proven=False, formal_classification_changes=0, donor_safe_bytes=0,
        accepted_test_reruns=0, rom_reconstructions=0)
    return receipt


def sources_and_layout():
    data, bindings = {}, {}
    for name, blob in PUBLIC_PATHS.items():
        value = old.download('https://raw.githubusercontent.com/pret/pokefirered/' + m.parent.SOURCE + '/' + name, 100000)
        m.need(m.parent.blob(value) == blob, '固定公開source全blob: ' + name)
        data[name] = value
        bindings[name] = {'repository': 'pret/pokefirered', 'commit': m.parent.SOURCE,
                          'path': name, 'git_blob': blob, **m.identity(value)}
    spec = m.parent.SYMBOL_SOURCE
    raw = old.download('https://raw.githubusercontent.com/' + spec['repository'] + '/' + spec['commit'] + '/' + spec['path'], 5000000)
    m.need(m.identity(raw) == {k: spec[k] for k in ('size', 'sha256')} and m.parent.blob(raw) == spec['git_blob'], '固定JP symbol全hash')
    symbols = m.parse_symbols(raw)
    work = WORK / 'layout'; work.mkdir()
    (work / 'multiboot.h').write_bytes(data['include/gba/multiboot.h'])
    (work / 'task.h').write_bytes(data['include/task.h'])
    shim = b'typedef unsigned char u8, bool8; typedef signed char s8; typedef unsigned short u16; typedef short s16; typedef unsigned int u32;\n'
    (work / 'global.h').write_bytes(shim)
    values = ['sizeof(struct MultiBootParam)'] + [f'__builtin_offsetof(struct MultiBootParam,{n})' for n in m.FIELDS[1:-2]]
    values += ['sizeof(struct Task)', '__builtin_offsetof(struct Task,data)']
    source = ('#include "global.h"\n#include "multiboot.h"\n#include "task.h"\nconst unsigned int berry_layout[] = {' + ','.join(values) + '};\n').encode()
    # task.hもglobal.hをincludeするため、shim自体に通常のinclude guardを付ける。
    shim = b'#ifndef PR16_ABI_TYPES\n#define PR16_ABI_TYPES\n' + shim + b'#endif\n'
    (work / 'global.h').write_bytes(shim)
    (work / 'layout.c').write_bytes(source)
    command = ['arm-none-eabi-gcc', '-mcpu=arm7tdmi', '-mthumb', '-std=c11', '-Wall', '-Wextra', '-Werror',
               '-c', str(work / 'layout.c'), '-o', str(work / 'layout.o')]
    subprocess.run(command, check=True, capture_output=True)
    subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '--only-section=.rodata',
                    str(work / 'layout.o'), str(work / 'layout.bin')], check=True, capture_output=True)
    binary = (work / 'layout.bin').read_bytes()
    m.need(len(binary) == len(m.FIELDS) * 4, 'ARM layout閉extent')
    layout = m.layout_checked(dict(zip(m.FIELDS, struct.unpack('<' + 'I' * len(m.FIELDS), binary))))
    return symbols, layout, {'sources': bindings, 'public_symbol_source': spec,
        'abi_shim': m.identity(shim), 'abi_compile_source': m.identity(source), 'arm_rodata': m.identity(binary),
        'compiler_version': subprocess.check_output(['arm-none-eabi-gcc', '-dumpfullversion'], text=True).strip(),
        'shim_semantics_ja': '固定公開headerをARMv4Tで配置する型幅shim。ゲーム関数を再コンパイルした証拠ではない。'}


def append_logs(summary, count):
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    block = (f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / Berry実TaskからBIOS直前までの有限転送境界\n'
        '- Version: berry-transfer-boundary-v1\n- Status: DONE（新しい引数境界。payload reader/容量/保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 専用解釈/人工試験/Actions、転送境界・旧run受領text、固定入口/引継ぎMD/JSON、両ログ。\n'
        f'- Verify: 新{count}人工試験、実候補13有限profile、固定header ARM layout、旧run全7member/25text、保存後read-only、task graph PASS。\n'
        '- Boundary: 新scope候補復元1、native0、旧受入再走0、全ROM参照scan0。正式788/86・選定残7・安全容量0。BIOS/実リンク/子機/対象4byte read未受入。\n'
        '- Commit: この記録を含む単親通常commit。実SHAはActions resultとGit履歴で照合。\n'
        '- Network: 同repo PR/ref/Actions/artifactのGETと同branch非force push。固定公開source '
        'https://github.com/pret/pokefirered/tree/' + m.parent.SOURCE + ' と固定JPsymbol。'
        '参照語 Task_BerryFixMain / MultiBootStartMaster / MultiBoot。EN asset再取得・旧測定再実行なし。\n')
    for name in LOGS:
        previous = read(name)
        m.need(('- Task: ' + TASK + ' /').encode() not in previous, '同task二重記録拒否')
        write(name, previous + block.encode())


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY') == a.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT') == '1', '同branch初回のみ')
    m.need(not WORK.exists() and not (ROOT / REPORT).exists(), '新scopeのみ。成功測定再走禁止')
    PUBLIC.mkdir(parents=True)
    head = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(head == os.environ['GITHUB_SHA'], 'event HEAD')
    observed = a.live(head)
    m.need(not a.git('status', '--porcelain', '--untracked-files=no').strip(), 'tracked clean')
    m.need(set(a.git('diff', '--name-only', BASE, head).decode().splitlines()) == CODE, '新4sourceだけ')
    m.need(not a.git('ls-files', '--', *[p + '/AGENTS.md' for p in
        ('scripts', 'tests', 'docs', 'design', 'content', 'content/modernization', '.github', '.github/workflows')]).strip(), '追加AGENTS読取りが必要')
    state = load(STATE)
    lane = state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id'] == 'SAVE_CAPACITY_BERRY_ORIGIN_ACTUAL_OWNER_READER' and
           [lane[k] for k in ('classified', 'unclassified', 'donor_safe_bytes')] == [788, 86, 0] and
           lane['selected_unknown_origins'] == 7, '現nextと正式親')
    m.need(state['recording']['pending_berry_origin_run']['observed']['conclusion'] == 'success', '既観測runの再起動禁止')
    protected = set(load(old.REPORT)['evidence_bindings']) | {old.REPORT, old.PARENT, old.PROGRESS, old.SYMBOLS,
        'AGENTS.md', 'state/source-lock.json', 'config/active_play_baseline.json',
        'docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md', 'docs/PR16_WIKI_READABILITY_PRIORITY_JA.md',
        'docs/PR16_WIKI_READABILITY_STATUS_JA.md', 'scripts/pr16_berry_origin.py', 'scripts/pr16_berry_origin_actions.py',
        'scripts/pr16_dex_hof_runtime_sprite.py', 'scripts/pr16_dex_hof_lifetime_root.py',
        'scripts/pr16_dex_hof_capacity_actions.py', 'scripts/pr16_wiki_r0_publish.py', 'scripts/pr16_wiki_r0_reconcile_actions.py'}
    before = snapshot(protected)
    old_wiki = m.encode({k: state['owner_execution_plan'][k] for k in ('wiki', 'wiki_readability', 'owner_review', 'scope')})
    PHASE = 'new-tests'
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_pr16_berry_transfer.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    public('transfer-tests.txt', stream.getvalue().encode())
    m.need(result.wasSuccessful() and result.testsRun == 26 and not result.skipped, '新26人工試験')
    subprocess.run(['python3', '-B', 'scripts/validate_task_graph.py'], cwd=ROOT, check=True, capture_output=True)
    PHASE = 'receive-completed-binding-without-replay'
    receipt = receive_binding()
    PHASE = 'fixed-public-header-and-symbols'
    symbols, layout, sources = sources_and_layout()
    PHASE = 'one-new-scope-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT = WORK / 'candidate'; reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions'] = 1; public('attempt.json', ATTEMPT)
    with (WORK / 'private-reconstruction.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        raw, cp = reconstruction.reconstruct()
    m.need(cp['candidate'] == m.parent.CANDIDATE, '現候補/115owner配置')
    PHASE = 'actual-task-transfer-boundary'
    proof = m.measure(raw, symbols, layout, load(old.EVIDENCE + '/bounded-binding.json'))
    proof.update(source_identity=sources, placement_identity=m.identity(m.encode(cp['placement'])), **ATTEMPT)
    summary = ('実Taskのstart/size/masterpとMultiBootInit、timer179/180、StartMasterの8境界、client-ready/不成立の2境界を有限解釈。'
               '13,260byteを13,264byteへ切上げ、label外4byteを含むboot_endp=0x086C7D3Cを実命令で確認。'
               '実MultiBootMain→SWI25直前をmode1で束縛。対象4byteの実readは0なので型分類は増やさない。')
    goal = ('保存した実Task→MultiBootMain→SWI25直前の引数/13profileを再走せず、'
            'boot_srcp=0x086C496C、boot_endp=0x086C7D3Cを使うBIOS payload readerまたは子機配置後の実readerへ有限に結ぶ。'
            '対象0x086C51BFの全4byteとlabel外tail4byteを区別し、自然リンク/転送成功は未証明。'
            '正式788/86・選定残7・安全容量0。窓外跨りread/旧owner内origin/間接参照/退役移管/controller/heap/局所Save未完。')
    for name, value in [('transfer-boundary.json', proof), ('binding-completion.json', receipt), ('transfer-tests.txt', stream.getvalue().encode())]:
        write(EVIDENCE + '/' + name, value)
    saved = snapshot(PROOFS)
    m.need(load(EVIDENCE + '/transfer-boundary.json') == proof and saved == snapshot(PROOFS), '保存後read-only byte/mtime')
    m.need(before == snapshot(protected), '全旧原本byte/mtime')
    observed = a.live(head)
    report = {'schema_version': 1, 'task': TASK, 'source_head': head, 'status': proof['status'],
        'candidate': m.parent.CANDIDATE, 'actions_run_id': int(os.environ['GITHUB_RUN_ID']),
        'actions_completion_confirmed': False, 'source_bindings': {n: m.identity(read(n)) for n in sorted(CODE)},
        'preserved_inputs': {n: value[0] for n, value in before.items()},
        'evidence_bindings': {n: m.identity(read(n)) for n in sorted(PROOFS)},
        'new_unit_tests': result.testsRun, 'finite_profiles': proof['profile_count'],
        'read_only_check_passed': True, 'task_graph_passed': True, 'claims': m.CLAIMS,
        'formal_classified': 788, 'formal_unclassified': 86, 'selected_unknown_origins': 7,
        'donor_safe_bytes': 0, 'observed_head_checks': observed, 'next_ja': goal, **ATTEMPT}
    write(REPORT, report)
    lane.update(status=proof['status'], checkpoint_path=REPORT, next_ja=goal,
                scheduling_status='READY_FROM_PRESERVED_BIOS_BOUNDARY')
    state['next_action'] = {'id': 'SAVE_CAPACITY_BERRY_BIOS_PAYLOAD_READER', 'goal_ja': goal,
        'read_paths': [GUIDE, REPORT, EVIDENCE + '/transfer-boundary.json', old.PROGRESS],
        'done_ja': '実payload/子機readerの全4byte消費とownerを証明し、成功run外部受領後だけ正式型へ追加する。'}
    state['observed_head_checks'] = observed
    state['recording']['last_execution'] = {k: report[k] for k in ('task', 'source_head', 'actions_run_id',
        'actions_completion_confirmed', 'new_unit_tests', 'finite_profiles', 'read_only_check_passed', 'task_graph_passed', *ATTEMPT.keys())}
    state['recording'].update(task=TASK, source_head=head, status='BERRY_TASK_TO_BIOS_BOUNDARY_READER_PENDING',
        received_berry_binding_completion=EVIDENCE + '/binding-completion.json',
        pending_berry_transfer_run={'run_id': int(os.environ['GITHUB_RUN_ID']), 'source_head': head,
            'output_report': REPORT, 'status': 'COMPLETION_NOT_YET_OBSERVED', 'replay_forbidden': True})
    state['recording']['pending_berry_origin_run'].update(status='COMPLETION_BOUND_WITHOUT_TYPE_ACCEPTANCE',
        completion_evidence_path=EVIDENCE + '/binding-completion.json', acceptance_not_inferred=True)
    text = read('CHATGPT_RESUME.md').decode()
    left, remainder = text.split('## 次の未完作業\n', 1)
    _, right = remainder.split('\n所有者が閲覧版で', 1)
    text = left + '## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_BERRY_BIOS_PAYLOAD_READER。' + goal + \
        ' 固定JSONの read_paths とtechnical_lanes.save_capacityが正本。run38099840927は全member受領済みで再起動しない。\n\n所有者が閲覧版で' + right
    write('CHATGPT_RESUME.md', text.encode())
    state['bindings']['CHATGPT_RESUME.md'] = {'git_blob_sha': m.parent.blob(text.encode()), **m.identity(text.encode())}
    m.need(old_wiki == m.encode({k: state['owner_execution_plan'][k] for k in ('wiki', 'wiki_readability', 'owner_review', 'scope')}), 'Wiki/承認/安全方針不変')
    write(STATE, state)
    text = read(GUIDE).decode()
    m.need('## Berry実TaskからBIOS直前の転送境界' not in text, 'MD二重記録拒否')
    text = text.replace('## 次の未完作業', '## 以前の停止点（履歴）')
    text += '\n## Berry実TaskからBIOS直前の転送境界\n\n' + summary + '\n\n' + \
        f'[有限証拠](../{EVIDENCE}/transfer-boundary.json) / [checkpoint](../{REPORT}) / [旧run完了受領](../{EVIDENCE}/binding-completion.json)。' + \
        '新26人工試験・13profile・ARM header layout・保存後read-only・task graph。新scope候補復元1、native0、旧受入再走0。' + \
        'SetSceneは明示した同期ABI条件、serial値はfixture。BIOS本体/子機/自然接続/全4byte readは未受入。正式788/86・残7・安全容量0を維持。\n\n## 次の未完作業\n\n' + goal + '\n'
    write(GUIDE, text.encode())
    append_logs(summary, result.testsRun)
    PHASE = 'final-index-and-nonforce-push'
    allowed = CODE | PROOFS | LOGS | {STATE, GUIDE, REPORT, 'CHATGPT_RESUME.md'}
    publication.final_index(BASE, allowed, REPORT)
    m.need(before == snapshot(protected), 'push前全旧原本保全')
    m.need(a.git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == head, 'push直前HEAD競合')
    for name in allowed:
        m.need(a.git('show', ':' + name) == read(name), '最終index全byte')
    a.git('config', 'user.name', 'github-actions[bot]')
    a.git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit', '-m', TASK + ': 実TaskからBIOS直前の転送境界と引継ぎを保存')
    a.git('push', 'origin', 'HEAD:' + BRANCH)
    pushed = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(a.git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == pushed, 'push後HEAD')
    for name in allowed:
        m.need(a.git('show', 'HEAD:' + name) == read(name), 'commit全blob')
    for name in PROOFS | {REPORT}:
        public(name.rsplit('/', 1)[-1], read(name))
    with zipfile.ZipFile(PUBLIC / 'scoped-context.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed | protected) - LOGS):
            z.writestr(name, read(name))
    public('result.json', {'status': proof['status'], 'source_head': head, 'commit': pushed,
        'actions_run_id': int(os.environ['GITHUB_RUN_ID']), 'new_unit_tests': result.testsRun,
        'finite_profiles': proof['profile_count'], 'formal_classified': 788, 'formal_unclassified': 86,
        'selected_unknown_origins': 7, 'donor_safe_bytes': 0, **ATTEMPT})
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True, exist_ok=True)
        frames = [{'path': f.filename[len(str(ROOT)) + 1:], 'line': f.lineno}
                  for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT) + '/scripts/')]
        detail = str(exc).replace(str(ROOT), '.')[:300] if isinstance(exc, ValueError) else None
        public('failure.json', {'status': 'NOT_ACCEPTED', 'phase': PHASE, 'exception_type': type(exc).__name__,
                               'detail': detail, 'frames': frames, 'attempt': ATTEMPT})
        print('RESULT=BLOCKED TASK=' + TASK + ' VERIFY=FAIL PHASE=' + PHASE + ' TYPE=' + type(exc).__name__)
        sys.exit(1)
