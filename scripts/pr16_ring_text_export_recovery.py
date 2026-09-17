#!/usr/bin/env python3
"""保存済みRing結果を再実行せず照合し、上限内UTF-8分割exportを作る。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

BASE = 'a5573a9226b4f3f0f3dbbf1832c3c87e50a0bcb9'
SOURCE = 'a5f372e25eba83e5a09dead27bf8b287ce13fda2'
RUN = 35255462365
JOB = 105317869677
SLUG = 'pr16-ring-text-export-recovery'
TASK = 'PR-P08-7-RING-TEXT-EXPORT-RECOVERY'
TITLE = '保存済み混在列の記録を再実行なしで照合し分割exportを検証'
SELF = 'scripts/pr16_ring_text_export_recovery.py'
TEST = 'tests/test_pr16_ring_text_export_recovery.py'
WORKFLOW = '.github/workflows/pr16-ring-text-export-recovery.yml'
PRIOR = 'content/modernization/pr16_ring_text_audio_sequence.json'
REPORT = 'content/modernization/pr16_ring_text_export_recovery.json'
KEY = 'latest_ring_text_export_recovery'
MIN_TESTS = 22
EXTRA_CODE = ()
SOURCES = ('scripts/pr16_ring_text_audio_sequence.py',)
NO_REPEAT = ('run35255462365は49tests/333条件と非force記録が成功した後のexport失敗。'
             '原Actions failureを保持し、記録commit a5573a9を独立照合。混在列は再実行しない。'
             '分割exportは各member 2MB以下・全体hash照合。次は未結合text/live owner。')
MAX_MEMBER = 2_000_000
MAX_LOGICAL = 32_000_000
MAX_TOTAL = 128_000_000
CHARS = 65_536
SECRET = re.compile(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN [A-Z ]*PRIVATE KEY-----')


def need(ok, text):
    if not ok:
        raise ValueError(text)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def safe_name(name):
    need(type(name) is str and re.fullmatch(r'[A-Za-z0-9_./-]+', name) is not None, 'export path文字')
    p = PurePosixPath(name)
    need(not p.is_absolute() and all(x not in ('', '.', '..') for x in name.split('/')), 'export path境界')
    need(p.suffix in ('.json', '.py', '.md', '.txt'), 'text suffix境界')


def checked(raw, limit):
    need(type(raw) is bytes and len(raw) <= limit, 'text size境界')
    text = raw.decode('utf-8')
    need(b'\0' not in raw and SECRET.search(raw) is None, 'private/text境界')
    return text


def bundle(files, directory):
    """完全な入力を検査してから分割。tokenを分割で隠せない。既存出力へ上書きしない。"""
    need(type(files) is dict and files, 'empty export')
    need(sum(len(raw) for raw in files.values()) <= MAX_TOTAL, 'total size境界')
    texts = {}
    for name, raw in sorted(files.items()):
        safe_name(name)
        texts[name] = checked(raw, MAX_LOGICAL)
    directory = Path(directory)
    need(not directory.exists(), 'export already exists')
    directory.mkdir(parents=True)
    manifest = {'schema_version': 1, 'format': 'utf8-text-chunks-v1', 'files': {}}
    for index, (name, text) in enumerate(texts.items()):
        parts = [text[i:i + CHARS] for i in range(0, len(text), CHARS)] or ['']
        row = {'identity': identity(files[name]), 'parts': []}
        for part, value in enumerate(parts):
            path = f'file-{index:04d}-part-{part:04d}.json'
            raw = stable({'file': name, 'index': part, 'count': len(parts), 'text': value})
            checked(raw, MAX_MEMBER)
            (directory / path).write_bytes(raw)
            row['parts'].append({'path': path, 'identity': identity(raw)})
        manifest['files'][name] = row
    raw = stable(manifest)
    checked(raw, MAX_MEMBER)
    (directory / 'manifest.json').write_bytes(raw)
    need(unbundle(directory) == files, 'export byte roundtrip')
    return manifest


def unbundle(directory):
    directory = Path(directory)
    need(directory.is_dir() and not directory.is_symlink(), 'export directory境界')
    actual = {}
    for p in directory.iterdir():
        need(p.is_file() and not p.is_symlink() and p.suffix == '.json', 'export member境界')
        actual[p.name] = checked(p.read_bytes(), MAX_MEMBER)
    need('manifest.json' in actual, 'manifest欠落')
    manifest = json.loads(actual['manifest.json'])
    need(manifest.get('schema_version') == 1 and manifest.get('format') == 'utf8-text-chunks-v1', 'manifest schema')
    need(type(manifest.get('files')) is dict and manifest['files'], 'manifest files')
    expected = {'manifest.json'}
    files = {}
    for name, row in manifest['files'].items():
        safe_name(name)
        need(type(row['parts']) is list and row['parts'], 'parts欠落')
        text = []
        for index, part in enumerate(row['parts']):
            path = part['path']
            need(type(path) is str and re.fullmatch(r'file-\d{4}-part-\d{4}\.json', path) is not None, 'part path')
            need(path not in expected and path in actual, 'part重複/欠落')
            expected.add(path)
            raw = actual[path].encode('utf-8')
            need(identity(raw) == part['identity'], 'part hash不一致')
            data = json.loads(raw)
            need(data['file'] == name and type(data['index']) is int and data['index'] == index
                 and type(data['count']) is int and data['count'] == len(row['parts'])
                 and type(data['text']) is str, 'part順序/件数')
            text.append(data['text'])
        raw = ''.join(text).encode('utf-8')
        checked(raw, MAX_LOGICAL)
        need(identity(raw) == row['identity'], 'logical hash不一致')
        files[name] = raw
    need(expected == set(actual), '未宣言member')
    need(sum(len(raw) for raw in files.values()) <= MAX_TOTAL, 'total size境界')
    return files


def verify_receipt(prior, run, jobs, logs):
    need(run['id'] == RUN and run['head_sha'] == SOURCE and run['status'] == 'completed'
         and run['conclusion'] == 'failure', '原Actions identity/conclusion')
    need(prior['source_head'] == SOURCE and prior['run_id'] == RUN, '保存report identity')
    tests = {'tests_run': 49, 'failures': 0, 'errors': 0, 'skips': 0, 'successful': True}
    need(prior['focused_tests'] == tests, '保存tests')
    a = prior['analysis']
    need((a['contract_cases'], a['conditional_return_cases'], a['pending_stop_cases']) == (333, 303, 30), '保存cases')
    need(a['ring_acquisition_accepted'] is False and a['release_ready'] is False
         and a['rom_changes'] == 0 and a['new_emulator_processes'] == 0, '保存scope')
    need(len(jobs) == 1 and jobs[0]['id'] == JOB and jobs[0]['conclusion'] == 'failure', '原job')
    steps = {step['number']: step for step in jobs[0]['steps']}
    need(steps[3]['conclusion'] == 'success' and steps[4]['conclusion'] == 'failure'
         and steps[5]['conclusion'] == 'skipped', '検証/後処理の区別')
    needle = 'RESULT=DONE TASK=PR-P08-7-RING-TEXT-AUDIO-SEQUENCE VERIFY=PASS COMMIT=' + BASE
    need(logs.count(needle) == 1 and 'File "<stdin>", line 7' in logs and 'AssertionError' in logs, '原log証跡')
    receipts = []
    for line in logs.splitlines():
        start = line.find('{"status": "PASS_RECORDED_NONFORCE_PUSHED"')
        if start >= 0:
            receipts.append(json.loads(line[start:]))
    need(len(receipts) == 1, 'record receipt重複/欠落')
    receipt = receipts[0]
    need(receipt['commit'] == BASE and receipt['source_head'] == SOURCE and receipt['run_id'] == RUN
         and receipt['tests'] == tests and receipt['new_emulator_processes'] == 0
         and receipt['ring_acquisition_accepted'] is False and receipt['release_ready'] is False, 'record receipt不一致')
    return {'record_verified': True, 'original_conclusion': 'failure', 'original_run_id': RUN,
            'original_job_id': JOB, 'record_commit': BASE, 'saved_tests': tests,
            'accepted_cases_replayed': 0, 'failure_stage': 'post-record text export boundary',
            'original_failure_reclassified_as_success': False}


def recover_prior(prior, run):
    import pr16_ring_followup_v2 as s
    jobs = s.api(f'actions/runs/{RUN}/jobs')['jobs']
    logs = s.cmd('gh', 'api', f'repos/{s.REPO}/actions/jobs/{JOB}/logs')
    result = verify_receipt(prior, run, jobs, logs)
    need(s.cmd('git', 'rev-parse', BASE + '^') == SOURCE, 'record parent不一致')
    paths = sorted((PRIOR, s.STATE, s.DOC, s.BACKLOG, *s.LOGS))
    need(s.cmd('git', 'diff', '--name-only', SOURCE, BASE).splitlines() == paths, 'record paths不一致')
    import subprocess
    need(subprocess.check_output(['git', 'show', BASE + ':' + PRIOR], cwd=s.ROOT) == (s.ROOT / PRIOR).read_bytes(), '原report byte不一致')
    return result


def analyze(previous, out):
    import pr16_ring_followup_v2 as s
    import pr16_ring_text_audio_sequence as t
    import pr16_ring_flagset_continuation as saved
    s.need(previous['analysis']['candidate'] == s.CANDIDATE, 'candidate境界')
    saved.bindings_fresh(s.ROOT, previous['source_bindings'])
    recovery = recover_prior(previous, s.api(f'actions/runs/{RUN}'))
    nodes, _, context = t.saved_inputs()  # 保存decodeだけ。evaluated/contracts/nativeは呼ばない。
    analysis = {k: v for k, v in previous['analysis'].items() if k not in ('cases', 'executed_saved_sites')}
    files = {'saved-context.json': stable({'nodes': nodes, 'analysis': analysis, 'inherited_analysis': context}),
             PRIOR: (s.ROOT / PRIOR).read_bytes()}
    # 現にimport済みのtracked Pythonだけ。private root/全repo走査なし。
    paths = set()
    for module in tuple(sys.modules.values()):
        source = getattr(module, '__file__', None)
        if source:
            p = Path(source).resolve()
            if p.is_relative_to(s.ROOT):
                rel = p.relative_to(s.ROOT).as_posix()
                if rel.startswith(('scripts/', 'tools/')) and p.suffix == '.py':
                    paths.add(rel)
    for rel in sorted(paths | {SELF, TEST}):
        need(s.cmd('git', 'ls-files', '--error-unmatch', '--', rel) == rel, 'untracked source export')
        files[rel] = (s.ROOT / rel).read_bytes()
    manifest = bundle(files, out / 'export')
    result = {'classification': 'SAVED_RECORD_VERIFIED_EXPORT_SHARDED_WITHOUT_CASE_REPLAY',
              'candidate': dict(s.CANDIDATE), 'original_record': recovery,
              'export_logical_files': len(files), 'export_parts': sum(len(r['parts']) for r in manifest['files'].values()),
              'logical_files_over_old_limit': {p: identity(raw) for p, raw in files.items() if len(raw) > MAX_MEMBER},
              'export_manifest': identity((out / 'export' / 'manifest.json').read_bytes()),
              'saved_node_count': len(nodes), 'new_node_count': 0, 'saved_nodes_redecoded': 0,
              'saved_contract_cases': 333, 'new_contract_cases': 0,
              'accepted_standalone_contracts_replayed': 0, 'accepted_native_cases_replayed': 0,
              'candidate_reconstructions': 0, 'rom_changes': 0, 'new_emulator_processes': 0,
              'ring_acquisition_accepted': False, 'release_ready': False,
              'next_owner_work_pending': True,
              'boundary_ja': '元runのfailureは保持。上限を緩めず分割前後のUTF-8/hashを検査。Ring通常取得/実allocation/callbackは未受入。'}
    (out / 'analysis.json').write_bytes(stable(result))
    return result


def summaries(result):
    return ('混在列run35255462365の49tests/333条件とa5573a9の非force記録を再実行なしで独立照合。'
            f'{result["export_logical_files"]} textを{result["export_parts"]}分割し各2MB境界と全体hashを検証。元runのexport failureは保持。',
            '次は未結合text/live ownerの実到達・allocation・callback選択を保存callerから限定する。'
            '分割exportのsaved-context.json/保存7291命令を使い、混在列333条件・音声末端・renderer/cursor/glyph・受入済みBP/nativeを単独再実行しない。'
            '実画面/音声・全文法・Ring/policy/Circus/P08は未受入。')


if __name__ == '__main__':
    import pr16_ring_followup_v2 as s
    need(sys.argv[1:] == ['run'], 'runだけを許可')
    s.assert_remote(s.cmd('git', 'rev-parse', 'HEAD'), attempts=12)
    s.run(sys.modules[__name__])
