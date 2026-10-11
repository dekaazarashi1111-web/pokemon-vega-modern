#!/usr/bin/env python3
"""Berry近傍originの新規限定測定。旧受入を保全し、text証拠だけを同branchへ保存。"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
from pathlib import PurePosixPath
import subprocess
import sys
import traceback
import unittest
import urllib.request
import zipfile

import pr16_berry_origin as m
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT = m.ROOT
BRANCH = 'codex/modernization-followup-20260908'
TASK = 'USER-20261011-BERRY-ORIGIN-BINDING'
STATE = 'content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE = 'docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
REPORT = 'content/modernization/pr16_berry_origin_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_berry_origin_evidence'
WF = '.github/workflows/pr16-berry-origin.yml'
CODE = {WF, 'scripts/pr16_berry_origin.py', 'scripts/pr16_berry_origin_actions.py', 'tests/test_pr16_berry_origin.py'}
LOGS = {'design/run_log.md', 'design/version_log.md'}
PROOFS = {EVIDENCE + '/' + n for n in ('bounded-binding.json', 'prior-actions.json', 'binding-tests.txt')}
PARENT = 'content/modernization/pr16_sound_origin_reader_receipt.json'
PROGRESS = 'content/modernization/pr16_sound_origin_reader_evidence/window-progress.json'
SYMBOLS = 'content/modernization/pr16_donor_origins_evidence/symbol-frontier.json'
WORK = ROOT / '.local/pr16-berry-origin'
PUBLIC = WORK / 'public'
PHASE = 'preflight'
ATTEMPT = {'rom_reconstructions': 0, 'native_processes': 0, 'accepted_test_reruns': 0, 'full_rom_scans': 0}


def read(name):
    path = ROOT / name
    m.need(path.is_file() and not path.is_symlink(), '通常textファイル: ' + name)
    return path.read_bytes()


def load(name):
    return json.loads(read(name))


def write(name, value):
    a.changed_write(name, m.encode(value) if isinstance(value, dict) else value)


def public(name, value):
    (PUBLIC / name).write_bytes(m.encode(value) if isinstance(value, dict) else value)


def snapshot(names):
    return {n: (m.identity(read(n)), (ROOT/n).stat().st_mtime_ns) for n in sorted(names)}


def download(url, limit):
    with urllib.request.urlopen(url, timeout=90) as response:
        raw = response.read(limit + 1)
    m.need(len(raw) <= limit, '固定公開入力サイズ上限')
    return raw


def zip_members(raw, maximum=2000000):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        m.need(len(names) == len(set(names)), 'ZIP重複member')
        m.need(sum(i.file_size for i in z.infolist()) <= maximum, 'ZIP展開サイズ上限')
        result = {}
        for item in z.infolist():
            p = PurePosixPath(item.filename)
            m.need(not p.is_absolute() and '..' not in p.parts and '\\' not in item.filename and
                   not item.is_dir() and (item.external_attr >> 16) & 0o170000 != 0o120000, 'ZIP安全な通常member')
            result[item.filename] = z.read(item)
    return result


def receive_sound():
    receipt = publication.accepted_run(38098087251, '491440bf01119783ae6be79a1029c94f8f254ffc',
        ['Verify sound reader or receive completed measurement without replay', 'Run actions/upload-artifact@v4'])
    artifact = a.fetch('actions/artifacts/11686777768')
    m.need(artifact['name'] == 'pr16-sound-origin-reader-public-text' and not artifact['expired'] and
           artifact['size_in_bytes'] == 75035 and artifact['digest'] ==
           'sha256:711677b494b1c616944866c6c886d8f4f72bc577be46084318439dbc73bfb4a8' and
           artifact['workflow_run']['id'] == 38098087251, '音声受領artifact全identity')
    raw = a.fetch('actions/artifacts/11686777768/zip', binary=True)
    m.need(m.identity(raw) == {'size': 75035, 'sha256': artifact['digest'][7:]}, '音声受領ZIP全hash')
    members = zip_members(raw)
    m.need(set(members) == {'actions-completion.json', 'pr16_sound_origin_reader_receipt.json', 'reference-chain.json',
                           'result.json', 'scoped-context.zip', 'unknown-frontier.json', 'window-progress.json'}, '全7member')
    context = zip_members(members['scoped-context.zip'])
    m.need(len(context) == 17, '全17保存text')
    for name, data in context.items():
        data.decode('utf-8')
        m.need(b'\0' not in data and a.git('show', m.BASE_HEAD + ':' + name) == data, '公開commit全text読戻し')
    result = json.loads(members['result.json'])
    m.need(result['commit'] == m.BASE_HEAD and result['formal_classified'] == 788 and
           result['formal_unclassified'] == 86 and result['donor_safe_bytes'] == 0 and
           members['pr16_sound_origin_reader_receipt.json'] == read(PARENT), '保存受領原本')
    receipt.update(artifact={k: artifact[k] for k in ('id', 'name', 'digest', 'size_in_bytes')},
                   members={n: m.identity(v) for n, v in members.items()},
                   context_bindings={n: m.identity(v) for n, v in context.items()},
                   published_commit=m.BASE_HEAD, accepted_test_reruns=0, native_replays=0, rom_reconstructions=0)
    return receipt


def sources():
    data, bindings = {}, {}
    for path, fixed_blob in m.PUBLIC_PATHS.items():
        if fixed_blob is None:
            meta = json.loads(download('https://api.github.com/repos/pret/pokefirered/contents/' + path + '?ref=' + m.SOURCE, 200000))
            m.need(meta['type'] == 'file' and meta['path'] == path and 192 <= meta['size'] <= 131072, '固定commitのasset metadata')
            fixed_blob = meta['sha']
        raw = download('https://raw.githubusercontent.com/pret/pokefirered/' + m.SOURCE + '/' + path, 1000000)
        m.need(m.blob(raw) == fixed_blob, '固定公開source全blob: ' + path)
        data[path] = raw
        bindings[path] = {'repository': 'pret/pokefirered', 'commit': m.SOURCE, 'path': path,
                          'git_blob': fixed_blob, **m.identity(raw)}
    spec = m.SYMBOL_SOURCE
    raw = download('https://raw.githubusercontent.com/' + spec['repository'] + '/' + spec['commit'] + '/' + spec['path'], 5000000)
    m.need(m.identity(raw) == {k: spec[k] for k in ('size', 'sha256')} and m.blob(raw) == spec['git_blob'], '固定JPsymbol全identity')
    names = {'gMultiBootProgram_BerryGlitchFix_Start', 'gMultiBootProgram_BerryGlitchFix_End',
             'Task_BerryFixMain', 'CB2_InitBerryFixProgram', 'MultiBootStartMaster', 'MultiBootMain', 'MultiBootInit'}
    symbols = m.parse_symbols(raw, names)
    required = symbols['found']
    m.need(required['gMultiBootProgram_BerryGlitchFix_Start']['address'] == m.START and
           required['gMultiBootProgram_BerryGlitchFix_End']['address'] == m.END, '選定JPsymbol両端')
    return data, bindings, symbols


def append_logs(summary, verify):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    block = (f'\n## {now}\n- Timestamp: {now}\n- Task: {TASK} / 選定Berry近傍の限定identityとlocale差検証\n'
             '- Version: berry-origin-binding-v1\n- Status: DONE（限定測定。型分類・保存統合は未完）\n'
             f'- Summary: {summary}\n- Files changed: 専用検証器/20試験/Actions、限定text証拠、固定引継ぎMD/JSON、両ログ。\n'
             f'- Verify: {verify}\n- Boundary: 正式788分類/86未知、選定残7、安全容量0。旧受入/旧原本/R0/ROM/Save101/baseline不変。'
             '全story/全alias/退役・移管/保存controller受入は非主張。\n'
             '- Commit: この記録を含む単親通常commit。実SHAはGit履歴とActions resultへ記録。\n'
             '- Network: 同repo PR/ref/Actions/artifactのGETと同branch非force push。固定公開source '
             'https://github.com/pret/pokefirered/tree/' + m.SOURCE + ' および固定JPsymbol。'
             '検索語 gMultiBootProgram_BerryGlitchFix_Start / mb_berry_fix。JP近傍長と公開asset長の相違を未照合のまま同一視しない。\n')
    for name in LOGS:
        previous = read(name)
        m.need(('- Task: ' + TASK + ' /').encode() not in previous, '同task二重追記禁止')
        write(name, previous + block.encode())


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY') == a.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT') == '1', '同branch初回のみ')
    m.need(not WORK.exists(), '新しいscopeのみ'); PUBLIC.mkdir(parents=True)
    head = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(head == os.environ['GITHUB_SHA'], 'event HEAD')
    observed = a.live(head)
    m.need(not a.git('status', '--porcelain', '--untracked-files=no').strip(), 'tracked clean')
    m.need(set(a.git('diff', '--name-only', m.BASE_HEAD, head).decode().splitlines()) == CODE, '新4sourceだけ')
    m.need(not (ROOT/REPORT).exists(), '保存済み限定測定は再走しない')
    nested = a.git('ls-files', '--', *[p + '/AGENTS.md' for p in
        ('scripts', 'tests', 'docs', 'design', 'content', 'content/modernization', '.github', '.github/workflows')])
    m.need(not nested.strip(), '追加AGENTS読取りが必要')
    state, parent, progress = load(STATE), load(PARENT), load(PROGRESS)
    lane = state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id'] == 'SAVE_CAPACITY_SELECTED_WINDOW_NEXT_ASSET_BINDING' and
           [lane[k] for k in ('classified', 'unclassified', 'donor_safe_bytes')] == [788, 86, 0] and
           progress['remaining_count'] == 7 and progress['next_address'] == m.HIT, '現行nextと正式親境界')
    for name, wanted in parent['evidence_bindings'].items():
        m.need(m.identity(read(name)) == wanted, '音声受入証拠保全: ' + name)
    selected = next(r for r in load(SYMBOLS)['origins'] if r['hit']['address'] == m.HIT)
    m.need(selected['preceding_label']['address'] == m.START and selected['following_label']['address'] == m.END and
           {k: selected['hit'][k] for k in ('size', 'sha256')} == m.HIT_ID, '保存symbol近傍/hit')
    protected = set(parent['evidence_bindings']) | {PARENT, PROGRESS, SYMBOLS, 'CHATGPT_RESUME.md', 'AGENTS.md',
        'docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md', 'state/source-lock.json', 'config/active_play_baseline.json',
        parent['measurement_checkpoint'], parent['measurement_proof'],
        'content/modernization/pr16_donor_window_evidence/windows.json', 'scripts/pr16_dex_hof_capacity_actions.py'}
    before = snapshot(protected)
    PHASE = 'new-scoped-tests'
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern='test_pr16_berry_origin.py'))
    public('binding-tests.txt', stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun == 20 and not tests.skipped, '新20境界試験')
    subprocess.run(['python3', '-B', 'scripts/validate_task_graph.py'], cwd=ROOT, check=True, capture_output=True)
    PHASE = 'receive-successful-sound-receipt-without-replay'
    prior = receive_sound()
    PHASE = 'fixed-public-sources'
    data, bindings, symbols = sources()
    PHASE = 'one-new-scope-candidate-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT = WORK/'candidate'; reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions'] = 1; public('attempt.json', ATTEMPT)
    with (WORK/'private-reconstruction.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        raw, cp = reconstruction.reconstruct()
    m.need(cp['candidate'] == m.CANDIDATE, '候補/既存配置owner')
    region = m.bind_hit(raw)
    PHASE = 'bounded-asset-locale-and-consumer-frontier'
    comparison = m.compare_regions(region, data['data/mb_berry_fix.gba'], m.HIT-m.START)
    values = {'asset_start': m.START, 'asset_end': m.END, 'asset_size': m.END-m.START,
              'payload_start': m.START+192, 'payload_size': m.END-m.START-192}
    consumers = {}
    for name, symbol in symbols['found'].items():
        if name.startswith('gMultiBootProgram_'):
            continue
        start, end = symbol['address'] & ~3, symbol['following_distinct_address']
        if end is None or not 0 < end-start <= 8192:
            consumers[name] = {'symbol': symbol, 'bounded_region_measured': False}
            continue
        code = m.section(raw, 0x08000000, start, end-start)
        consumers[name] = {'symbol': symbol, 'region_start': start, 'region_end_exclusive': end,
                          'region_identity': m.identity(code), 'bounded_region_measured': True,
                          'literal_shapes': m.literal_occurrences(code, start, values),
                          'current_function_owner_proven': False, 'actual_consumer_proven': False}
    status = 'BERRY_NEIGHBORHOOD_BOUND_PUBLIC_ASSET_' + ('EQUAL_READER_PENDING' if comparison['whole_asset_equal'] else 'DIFFERS_OWNER_PENDING')
    proof = {'schema_version': 1, 'status': status, 'candidate': m.CANDIDATE,
             'saved_symbol_neighborhood': selected, 'public_sources': bindings, 'public_symbol_source': m.SYMBOL_SOURCE,
             'symbols': symbols, 'region': {'start': m.START, 'end_exclusive': m.END, **m.identity(region)},
             'origin': {'address': m.HIT, **m.HIT_ID}, 'comparison': comparison,
             'current_header_shape': m.arm_header(region), 'public_header_shape': m.arm_header(data['data/mb_berry_fix.gba']),
             'overlapping_thumb_shapes': m.thumb_shapes(region, m.START, m.HIT), 'consumer_frontier': consumers,
             'placement_identity': m.identity(m.encode(cp['placement'])),
             'formal_classified': 788, 'formal_unclassified': 86, 'selected_unknown_origins': 7,
             'donor_safe_bytes': 0, 'actual_consumer_proven': False, 'formal_classification_changes': 0,
             'indirect_reference_completeness_claimed': False, 'retirement_or_transfer_complete': False, **ATTEMPT}
    m.need(m.encode(proof) == m.encode(json.loads(m.encode(proof))), '決定的JSON往復')
    for name, value in [('bounded-binding.json', proof), ('prior-actions.json', prior), ('binding-tests.txt', stream.getvalue().encode())]:
        write(EVIDENCE+'/'+name, value)
    saved = snapshot(PROOFS)
    m.need(load(EVIDENCE+'/bounded-binding.json') == proof and saved == snapshot(PROOFS), '保存後check byte/mtime不変')
    m.need(before == snapshot(protected), '旧原本byte/mtime不変')
    goal = ('保存したBerry近傍の限定identity・公開assetとのlocale差・consumer frontierから、'
            '0x086C51BFの現ownerと実readerを有限範囲で結ぶ。公開EN assetや近傍JPsymbolを現ownerと同一視しない。'
            '今回の候補復元/限定測定/20試験と旧受入は再走せず、実readerの新scopeだけを検証する。'
            '正式788/86・選定残7・安全容量0。窓外跨りread/旧owner内origin/間接参照/退役・移管/保存controller/heap/局所Saveは未完。')
    report = {'schema_version': 1, 'task': TASK, 'status': status, 'source_head': head, 'candidate': m.CANDIDATE,
              'actions_run_id': int(os.environ['GITHUB_RUN_ID']), 'actions_completion_confirmed': False,
              'source_bindings': {n: m.identity(read(n)) for n in sorted(CODE)},
              'preserved_inputs': {n: value[0] for n, value in before.items()},
              'evidence_bindings': {n: m.identity(read(n)) for n in sorted(PROOFS)},
              'new_unit_tests': 20, 'read_only_check_passed': True, 'task_graph_passed': True,
              'formal_classified': 788, 'formal_unclassified': 86, 'selected_unknown_origins': 7,
              'donor_safe_bytes': 0, 'formal_classification_changes': 0, 'actual_consumer_proven': False,
              'received_prior_run': prior['id'], 'observed_head_checks': observed, 'next_ja': goal, **ATTEMPT}
    write(REPORT, report)
    lane.update(status=status, checkpoint_path=REPORT, next_ja=goal)
    state['next_action'] = {'id': 'SAVE_CAPACITY_BERRY_ORIGIN_ACTUAL_OWNER_READER', 'goal_ja': goal,
                           'read_paths': [GUIDE, REPORT, EVIDENCE+'/bounded-binding.json', PROGRESS, SYMBOLS],
                           'done_ja': '現ownerと実readerを証明し、完了runの外部受領後のみ型分類を更新する。'}
    state['observed_head_checks'] = observed
    state['recording']['last_execution'] = {k: report[k] for k in ('task', 'source_head', 'actions_run_id',
        'actions_completion_confirmed', 'new_unit_tests', 'read_only_check_passed', 'task_graph_passed',
        'formal_classified', 'formal_unclassified', 'donor_safe_bytes', *ATTEMPT.keys())}
    state['recording'].update(status='R0_READY_BERRY_ORIGIN_BOUNDED_IDENTITY_READER_PENDING',
        received_sound_receipt_completion=EVIDENCE+'/prior-actions.json',
        pending_berry_origin_run={'run_id': int(os.environ['GITHUB_RUN_ID']), 'source_head': head,
                                 'output_report': REPORT, 'status': 'COMPLETION_NOT_YET_OBSERVED', 'replay_forbidden': True})
    write(STATE, state)
    text = read(GUIDE).decode(); m.need('## Berry近傍の限定identityと公開locale差' not in text, 'MD二重追記禁止')
    text = text.replace('## 次の未完作業', '## 以前の停止点（履歴）')
    summary = (f'保存JPsymbol間{len(region)}byteと現候補全SHA/配置owner/対象4byteを束縛。'
               f'固定公開assetは{len(data["data/mb_berry_fix.gba"])}byte、全asset一致={comparison["whole_asset_equal"]}。'
               '長さ差・同位置差・局所一致・header/Thumb形・実consumer候補の有限literalを記録。形だけでは分類しない。')
    text += ('\n## Berry近傍の限定identityと公開locale差\n\n' + summary + '\n\n'
             f'[限定証拠](../{EVIDENCE}/bounded-binding.json) / [checkpoint](../{REPORT}) / '
             f'[直前受領Actions完了](../{EVIDENCE}/prior-actions.json)。新20人工境界試験・task graph・'
             '決定的保存後read-only検査・旧原本保全。新scope候補復元1、native0、旧受入再走0。'
             '正式788/86・選定残7・安全容量0。公開assetをJP/現候補と盲目的に同一視せず、実owner/readerは未完。\n\n'
             '## 次の未完作業\n\n' + goal + '\n')
    write(GUIDE, text.encode())
    append_logs(summary, '新20試験、対象全4byte/全候補SHA/既存owner配置、固定公開source全blob、全7ZIP/17text原本、JSON往復、保存後read-only、task graph PASS。')
    PHASE = 'final-index-and-nonforce-push'
    allowed = CODE | PROOFS | LOGS | {STATE, GUIDE, REPORT}
    publication.final_index(m.BASE_HEAD, allowed, REPORT)
    m.need(a.git('ls-remote', 'origin', 'refs/heads/'+BRANCH).decode().split()[0] == head, 'push直前HEAD競合')
    for name in allowed: m.need(a.git('show', ':'+name) == read(name), '最終index全byte')
    a.git('config', 'user.name', 'github-actions[bot]')
    a.git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit', '-m', TASK+': 限定測定と引継ぎを保存')
    a.git('push', 'origin', 'HEAD:'+BRANCH)
    pushed = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(a.git('ls-remote', 'origin', 'refs/heads/'+BRANCH).decode().split()[0] == pushed, 'push後HEAD')
    for name in allowed: m.need(a.git('show', 'HEAD:'+name) == read(name), 'commit全blob読戻し')
    for name in PROOFS | {REPORT}: public(name.rsplit('/',1)[-1], read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed | protected) - LOGS): z.writestr(name, read(name))
    public('result.json', {'status': 'DONE_BOUNDED_BINDING_READER_PENDING', 'source_head': head, 'commit': pushed,
        'actions_run_id': int(os.environ['GITHUB_RUN_ID']), 'formal_classified': 788, 'formal_unclassified': 86,
        'selected_unknown_origins': 7, 'donor_safe_bytes': 0, 'new_unit_tests': 20, **ATTEMPT})
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True, exist_ok=True)
        frames = [{'path': f.filename[len(str(ROOT))+1:], 'line': f.lineno} for f in traceback.extract_tb(exc.__traceback__)
                  if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json', {'status': 'NOT_ACCEPTED', 'phase': PHASE, 'exception_type': type(exc).__name__,
                               'frames': frames, 'attempt': ATTEMPT})
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__)
        sys.exit(1)
