#!/usr/bin/env python3
"""保存済みlive-frame辺の未読継続1根だけを採取・検証・記録する。"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[1]
TASK = 'PR-P08-7-RING-FLAGSET-CONTINUATION'
BASE_HEAD = '0565db05c3e244b3b214bbc8141bb6c4182c8649'
SELF = 'scripts/pr16_ring_flagset_continuation.py'
TEST = 'tests/test_pr16_ring_flagset_continuation.py'
WORKFLOW = '.github/workflows/pr16-ring-flagset-continuation.yml'
REPORT = 'content/modernization/pr16_ring_flagset_continuation.json'
ABI = 'content/modernization/pr16_ring_indirect_abi.json'
PATCH = 'content/modernization/pr16_ring_patch_owner.json'
PRIOR = 'content/modernization/pr16_ring_transitive_owner.json'
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
BACKLOG = 'content/modernization/p08_remaining_work.json'
CHECKPOINT = 'content/modernization/pr16_bp_chooser_checkpoint.json'
LOGS = ('design/run_log.md', 'design/version_log.md')
OUTPUTS = (REPORT, STATE, DOC, BACKLOG, *LOGS)
SOURCES = (SELF, TEST, WORKFLOW, ABI, PATCH, PRIOR,
           'scripts/pr16_ring_transitive_owner.py',
           'scripts/pr16_ring_compiled_owner.py',
           'overlays/save_migration/save_migration.c')
OUT = ROOT / '.local/pr16-ring-flagset-continuation'
TARGET = 0x0806DE7D
OWNER = 0x093789F3
ROM_BASE = 0x08000000
WINDOW = 256
LIMIT = 128
CANDIDATE = {'size': 33554432,
             'sha256': 'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b',
             'crc32': '3EB17B36'}
COUNTS = {'ABI_SAVED_LR_RETURN': 12, 'CALLSITE_R3_TRAMPOLINE': 2,
          'LITERAL_BRANCH_LIVE_FRAME': 1}
NEXT = ('0x0806DE7Dのcandidate byte採取は完了。同一入力で再採取せず、保存した継続graphのcall/returnと'
        '継承8byte frameを結合して残るownerを絞る。旧18未読targetは保持し、保存済みFlagGet graphと'
        '15間接辺分類を再実行しない。callsite限定解決を全callerへ昇格しない。'
        '全owner未除外のままRing story giftを新設しない。Ring正規取得・装備実戦・Save/fresh Continueは未受入。')


def need(value, message):
    if not value:
        raise ValueError(message)


def stable(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def safe(root, name):
    p = Path(name)
    need(not p.is_absolute() and '..' not in p.parts and '\\' not in name, 'unsafe path')
    path = root / p
    need(not any(q.is_symlink() for q in (path, *path.parents)), 'symlink rejected')
    return path


def bindings_fresh(root, bindings):
    need(isinstance(bindings, dict) and bindings, 'missing source bindings')
    for name, bound in bindings.items():
        need(identity(safe(root, name).read_bytes()) == bound, 'stale binding: ' + name)


def candidate_identity(raw):
    value = identity(raw)
    value['crc32'] = f'{zlib.crc32(raw) & 0xffffffff:08X}'
    need(value == CANDIDATE, 'candidate identity differs')
    return value


def saved_metadata(abi, patch, prior):
    need(all(v.get('candidate') == CANDIDATE for v in (abi, patch, prior)), 'saved candidate differs')
    a = abi['analysis']
    need(a['counts'] == COUNTS and a['classified_edges'] == 15, 'ABI classification differs')
    need(a['additional_unread_targets'] == [TARGET], 'continuation frontier differs')
    need(a['ring_acquisition_accepted'] is False and a['all_runtime_owners_excluded'] is False,
         'unsupported prior acceptance')
    matches = [e for e in a['edges'] if e['classification'] == 'LITERAL_BRANCH_LIVE_FRAME']
    need(len(matches) == 1, 'missing/duplicate live-frame edge')
    edge = matches[0]
    need(edge['owner'] == OWNER and edge['target'] == TARGET and edge['frame_bytes'] == 8
         and edge['entry_lr_saved_offsets'] == [-4], 'inherited frame differs')
    old = a['old_unread_targets']
    need(len(old) == len(set(old)) == 18 and TARGET not in old, 'old unread frontier differs')
    graphs = [*patch['frontier']['graphs'], *prior['native_owners'].values()]
    need(all(g['entry'] != TARGET for g in graphs), 'target already recorded')
    cached = {x for g in graphs for n in g['nodes'] for x in range(n['address'], n['address'] + n['size'])}
    need((TARGET & ~1) not in cached, 'target code already recorded')
    return copy.deepcopy(edge), sorted(old), graphs, cached


def validate_graph(graph, cached):
    need(graph['entry'] == TARGET and graph['window'] == WINDOW, 'wrong collection scope')
    need(graph['side_effects_excluded'] is False, 'unsupported side-effect claim')
    nodes = graph['nodes']
    need(1 <= len(nodes) <= LIMIT, 'instruction budget differs')
    starts = [n['address'] for n in nodes]
    need(starts == sorted(set(starts)) and starts[0] == TARGET & ~1, 'duplicate/unordered nodes')
    occupied = set()
    for node in nodes:
        at, size = node['address'], node['size']
        need(type(at) is int and not at & 1 and size in (2, 4), 'invalid instruction range')
        need(TARGET & ~1 <= at and at + size <= (TARGET & ~1) + WINDOW, 'escaped collection window')
        raw = bytes.fromhex(node['hex'])
        need(len(raw) == size and not occupied.intersection(range(at, at + size)), 'overlapping instruction')
        need(not any(x in cached for x in range(at, at + size)), 'recorded code would be rescanned')
        occupied.update(range(at, at + size))
        need(node['kind'] in ('ordinary', 'call', 'jump', 'conditional', 'indirect', 'return'), 'unknown node kind')
        if 'literal_address' in node:
            word = int.from_bytes(raw[:2], 'little')
            need(word & 0xf800 == 0x4800 and node['literal_address'] == ((at + 4) & ~3) + (word & 255) * 4,
                 'literal address differs')
    need(graph['memory_write_sites'] == [n['address'] for n in nodes if n['memory_write']], 'write sites differ')
    for edge in graph['external_edges']:
        need(edge['site'] in starts, 'orphan external edge')
        target = edge.get('target')
        need(target is None or (type(target) is int and target & 1
             and ROM_BASE <= (target & ~1) < ROM_BASE + CANDIDATE['size']), 'invalid external target')


def collect(raw, abi, patch, prior, decode):
    candidate_identity(raw)
    edge, old, graphs, cached = saved_metadata(abi, patch, prior)
    # 外部calleeを再帰しない。既存native_graph/decoderそのものは変更しない。
    graph = decode(raw, TARGET, window=WINDOW, limit=LIMIT)
    validate_graph(graph, cached)
    ranges = {}
    for node in graph['nodes']:
        at, size = node['address'], node['size']
        data = raw[at - ROM_BASE:at - ROM_BASE + size]
        need(data.hex() == node['hex'], 'sample differs from candidate bytes')
        ranges[(at, size)] = data
        if 'literal_address' in node:
            at = node['literal_address']
            need(ROM_BASE <= at <= ROM_BASE + len(raw) - 4, 'literal outside candidate')
            data = raw[at - ROM_BASE:at - ROM_BASE + 4]
            need(len(data) == 4 and int.from_bytes(data, 'little') == node['literal_value'], 'literal bytes differ')
            ranges[(at, 4)] = data
    entries = {g['entry'] for g in graphs}
    external = {e['target'] for e in graph['external_edges'] if e.get('target') is not None}
    additional = sorted(external - entries - set(old) - {TARGET})
    return {'classification': 'FLAGSET_CONTINUATION_BYTES_NOT_NATIVE_ACCEPTANCE',
            'candidate': CANDIDATE, 'target': TARGET, 'inherited_edge': edge,
            'graph': graph, 'sampled_ranges': [dict(address=a, hex=data.hex(), **identity(data))
                for (a, size), data in sorted(ranges.items())],
            'sampled_instruction_bytes': sum(n['size'] for n in graph['nodes']),
            'old_unread_targets': old, 'additional_unread_targets': additional,
            'remaining_unread_targets': sorted(set(old) | set(additional)),
            'reused_saved_entries': sorted(external & entries),
            'inherited_frame_return_verified': False,
            'stack_integrity_proven': False, 'all_callers_resolved': False,
            'ring_acquisition_accepted': False, 'all_runtime_owners_excluded': False,
            'release_ready': False, 'rom_changes': 0, 'new_emulator_processes': 0,
            'accepted_native_cases_replayed': 0, 'prior_abi_classifications_replayed': 0,
            'new_graph_decodes': 1, 'candidate_reconstructions': 1}


def read_inputs():
    values = [json.loads(safe(ROOT, p).read_bytes()) for p in (ABI, PATCH, PRIOR)]
    for value in values:
        bindings_fresh(ROOT, value['source_bindings'])
    need(values[0]['run_id'] == 34968485915 and values[0]['source_head'] ==
         '0449002040cefe9c7df01c2bf7804ea51fb16491', 'ABI provenance differs')
    saved_metadata(*values)
    return values


def api(path):
    import os
    import subprocess
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + os.environ['GITHUB_REPOSITORY'] + '/' + path]))


def preflight():
    import os
    import subprocess
    import pr16_resume as resume
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT / REPORT).exists(), 'already recorded; do not repeat')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'execution HEAD differs')
    need(subprocess.run(['git', 'merge-base', '--is-ancestor', BASE_HEAD, head]).returncode == 0, 'wrong ancestry')
    pr = api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head
         and pr['head']['ref'] == 'codex/modernization-followup-20260908'
         and pr['head']['repo']['full_name'] == os.environ['GITHUB_REPOSITORY'], 'PR boundary differs')
    s = resume.validate(ROOT)
    need(s['latest_native_run'] == 34946969126 and s['bp']['spending_accepted'], 'BP checkpoint changed')
    need('P05_NATIVE_RING_ACQUISITION_PHYSICAL' in s['remaining_physical_gap_ids'], 'Ring already accepted')
    read_inputs()
    reused = []
    for run_id, source in ((34968485915, '0449002040cefe9c7df01c2bf7804ea51fb16491'),
                           (34946969126, '0b7497b575a3180a045f2be377386490f192a012')):
        r = api('actions/runs/' + str(run_id))
        need(r['status'] == 'completed' and r['conclusion'] == 'success' and r['head_sha'] == source, 'prior Actions differs')
        reused.append({k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')})
    runs = api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=30')['workflow_runs']
    observed = [{k: r[k] for k in ('id', 'name', 'head_sha', 'status', 'conclusion')} for r in runs]
    value = {'head': head, 'reused_successful_actions': reused, 'actions_before': observed,
             'checkpoint': identity((ROOT / CHECKPOINT).read_bytes()),
             'source_bindings': {p: identity(safe(ROOT, p).read_bytes()) for p in SOURCES}}
    (OUT / 'preflight.json').write_bytes(stable(value))
    print('PASS_EXACT_HEAD_REUSED_ABI_AND_BP_NOT_REPLAYED')


def record(rom):
    import os
    import subprocess
    import sys
    import unittest
    from datetime import datetime, timezone
    import pr16_resume as resume
    import pr16_ring_transitive_owner as decoder
    before = json.loads((OUT / 'preflight.json').read_bytes())
    need(before['head'] == os.environ['GITHUB_SHA'], 'preflight HEAD differs')
    bindings_fresh(ROOT, before['source_bindings'])
    need(not (ROOT / REPORT).exists(), 'already recorded; do not repeat')
    raw = safe(ROOT, rom).read_bytes()
    result = collect(raw, *read_inputs(), decoder.native_graph)
    need(safe(ROOT, rom).read_bytes() == raw, 'candidate changed during read')
    value = {'schema_version': 1, 'task': TASK, 'source_head': before['head'],
             'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_status_at_record': 'in_progress',
             'analysis': result, 'source_bindings': before['source_bindings'],
             'reused_successful_actions': before['reused_successful_actions'],
             'actions_observed_before_record': before['actions_before']}
    (OUT / 'audit.json').write_bytes(stable(value))
    suite = unittest.TestSuite()
    for pattern in ('test_pr16_ring_flagset_continuation.py', 'test_pr16_resume.py'):
        suite.addTests(unittest.defaultTestLoader.discover('tests', pattern=pattern))
    with (OUT / 'tests.txt').open('w', encoding='utf-8') as stream:
        tested = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    tests = {'tests_run': tested.testsRun, 'failures': len(tested.failures), 'errors': len(tested.errors),
             'skips': len(tested.skipped), 'successful': tested.wasSuccessful() and not tested.skipped}
    (OUT / 'tests.json').write_bytes(stable(tests))
    need(tests['successful'], 'focused tests failed')
    value['focused_tests'] = tests
    (ROOT / REPORT).write_bytes(stable(value))
    s = resume.validate(ROOT)
    backlog = resume.load(ROOT, BACKLOG)
    gap = 'P05_NATIVE_RING_ACQUISITION_PHYSICAL'
    row = next(r for r in backlog['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
    need(gap in row['remaining_supply_gap_ids'] and row['selected_supply_entrypoints'][gap] is None, 'Ring owner changed')
    row['ring_flagset_continuation'] = REPORT
    s['ring_flagset_continuation'] = {'path': REPORT, 'source_head': before['head'],
        'run_id': value['run_id'], 'target': TARGET, 'new_graph_decodes': 1,
        'additional_unread_targets': result['additional_unread_targets'], 'ring_acquisition_accepted': False}
    stop = (f'未読だった0x0806DE7Dのみ同一candidateから{len(result["graph"]["nodes"])}命令/'
            f'{result["sampled_instruction_bytes"]}命令byteを採取。継承8byte frameとentry LR保存offset -4を保持。'
            f'旧18未読targetは不変、新規未読{len(result["additional_unread_targets"])}targetを明示。'
            'call/returnと継承frameの結合・stack integrity・全caller/全owner網羅性・Ring通常取得は未証明。'
            '保存済み15間接辺分類とBP正式受入run34946969126は再実行せず不変。')
    s['bp']['current_stop'] = s['source_change_review_ja'] = stop
    s['bp']['next_step'] = s['next_action']['goal_ja'] = NEXT
    s['next_action']['read_paths'] = [REPORT, SELF, ABI, PATCH, PRIOR]
    s['observed_head'] = before['head']
    s['observed_head_semantics'] = 'FlagSet継続1根のcandidate byteを採取したsource HEAD。完了commit/run結論はremote ref/Actionsで確認する。'
    s['observed_head_checks']['reason_ja'] = (f'新規限定採取run{value["run_id"]}は保存時in_progress。'
        '前回ABI run34968485915とBP run34946969126のcompleted/successを照合。'
        '開始HEADのPR checks action_requiredを成功へ読み替えず、最新Actions snapshotをreceiptへ保存。')
    s['session_execution_summary'] = {'new_emulator_processes': 0, 'rom_changes': 0,
        'candidate_reconstructions': 1, 'accepted_standalone_replays': 0,
        'scope_ja': '同一candidateの未読継続1根のみ採取。保存済み15間接辺分類/graph/受入済みnativeの単独再実行0。'}
    note = '0x0806DE7Dの1根byte採取は完了。同一candidate/sourceで再採取せず、保存した継続graphを再利用する。継承8byte frame・旧18未読target・全owner未除外を保持し、Ring通常取得の受入へ読み替えない。'
    if note not in s['do_not_repeat']:
        s['do_not_repeat'].append(note)
    for p in (SELF, TEST, WORKFLOW, REPORT):
        s['source_bindings'][p] = identity((ROOT / p).read_bytes())
    (ROOT / STATE).write_bytes(stable(s))
    (ROOT / BACKLOG).write_bytes(stable(backlog))
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'render'], check=True)
    subprocess.run([sys.executable, 'scripts/pr16_resume.py', 'check'], check=True)
    need(identity((ROOT / CHECKPOINT).read_bytes()) == before['checkpoint'], 'accepted checkpoint mutated')
    bindings_fresh(ROOT, before['source_bindings'])
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK} / FlagSet未読継続1根の採取\n'
        '- Status: DONE / 限定採取の実装・検証・記録。Ring正規取得は未完。\n- Version: PR16 FlagSet continuation bytes\n'
        '- Summary: ' + stop + '\n'
        f'- Verify: 新規異常系と固定resume {tests["tests_run"]} tests PASS、render/check PASS。task graph・最終index差分guard・diffを完了commit前の必須gateとする。\n'
        f'- Evidence: {REPORT}; source HEAD={before["head"]}; run={value["run_id"]}（保存時in_progress、最終結論はActionsで確認）。\n'
        '- Preserved: candidate SHA-256 ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b / CRC32 3EB17B36。候補変更/ROM編集/native/受入済み単独再実行/既存15辺再分類0。未読byte取得のため同一candidate再構築1。BP checkpoint全byte不変。\n'
        '- Files changed: 新規collector/tests/workflow/receipt、固定引継ぎMD/JSON、P08 Ring参照、両ログ。\n'
        '- Commit: この記録を含む同branchへの非force commit。自己SHAはremote refとresult artifactで確認。\n'
        '- Network: GitHub connector/Actionsと既存hash固定入力復元のみ。container直接Git取得はDNS失敗。外部技術資料の新規検索なし。\n'
        '- Boundary: 開始HEADの通常PR checks action_requiredを成功扱いしない。既存全体private guard違反は前後一致、新規差分違反0を要求。merge/release/baseline変更なし。\n'
        '- Next: ' + NEXT + '\n')
    for p in LOGS:
        need(TASK not in (ROOT / p).read_text(encoding='utf-8'), 'duplicate completion log')
        with (ROOT / p).open('a', encoding='utf-8') as stream:
            stream.write(entry)
    subprocess.run([sys.executable, 'scripts/validate_task_graph.py'], check=True)
    subprocess.run(['git', 'add', '--', *OUTPUTS], check=True)
    import pr16_ring_compiled_record as guard
    guard.BASE, guard.OUT = BASE_HEAD, OUT
    guard.ALLOWED = set((SELF, TEST, WORKFLOW, *OUTPUTS))
    guard.guard()
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    summary = {k: result[k] for k in ('target', 'sampled_instruction_bytes', 'old_unread_targets',
        'additional_unread_targets', 'new_graph_decodes', 'rom_changes', 'new_emulator_processes',
        'accepted_native_cases_replayed', 'ring_acquisition_accepted')}
    summary.update(instructions=len(result['graph']['nodes']), external_edges=result['graph']['external_edges'],
                   memory_write_sites=result['graph']['memory_write_sites'], tests=tests)
    (OUT / 'summary.json').write_bytes(stable(summary))
    print(json.dumps(summary))


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT / 'scripts'))
    if sys.argv[1:] == ['preflight']:
        preflight()
    elif len(sys.argv) == 3 and sys.argv[1] == 'record':
        record(sys.argv[2])
    else:
        raise SystemExit('usage: pr16_ring_flagset_continuation.py preflight|record <relative-candidate-path>')
