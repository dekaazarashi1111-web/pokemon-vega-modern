#!/usr/bin/env python3
"""登録message task一根だけを採取し、保存callerとwindow初期化境界を固定する。"""
from __future__ import annotations
import ast
import copy
import sys
import pr16_ring_message_owner_contracts as prior
import pr16_ring_text_export_recovery as export
import pr16_ring_followup_v2 as s

BASE = '0804354fa5944a3d98a07a0b03c31c3e2a3fc218'
SLUG = 'pr16-ring-message-task-frontier'
TASK = 'PR-P08-7-RING-MESSAGE-TASK-FRONTIER'
TITLE = '登録message taskの未読byteと保存上流caller・初期化境界を固定'
SELF = 'scripts/pr16_ring_message_task_frontier.py'
TEST = 'tests/test_pr16_ring_message_task_frontier.py'
WORKFLOW = '.github/workflows/pr16-ring-message-task-frontier.yml'
PRIOR = prior.REPORT
REPORT = 'content/modernization/pr16_ring_message_task_frontier.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 20
EXTRA_CODE = ()
SOURCES = tuple(dict.fromkeys((prior.SELF, prior.PRIOR, *prior.SOURCES,
    'scripts/pr16_ring_remaining_frontier.py', 'scripts/pr16_ring_owner_frontier.py',
    'scripts/pr16_ring_transitive_owner.py', 'scripts/pr16_ring_zero_bytes.py',
    '.github/workflows/pr16-ring-callee-bytes.yml')))
NO_REPEAT = ('登録message task08068C31の限定採取と保存caller照合は保存原本を再利用。'
    '次は保存taskの状態遷移/終了/不足境界を上流と結合。登録を実行、初期化表をlive初期化へ読み替えない。'
    '旧391条件/速度採取/renderer/audio/BP/nativeを単独再実行しない。')
CALLBACK = 0x08068c31
LO, HI = CALLBACK & ~1, 0x08068ccc
INITIALIZER = 0x080f8a29
need = s.need


def plan(nodes, summary):
    by = {n['address']: n for n in nodes}
    need(len(by) == len(nodes) == 7309, '保存7309命令')
    need(summary['candidate'] == s.CANDIDATE and summary['contract_cases'] == 391, '先行identity/条件数')
    need(summary['pending_registered_task_callback'] == CALLBACK, '登録先変更')
    for key in ('ring_acquisition_accepted', 'release_ready', 'actual_callback_table_observed', 'initializer_runtime_observed'):
        need(summary[key] is False, '未受入境界 ' + key)
    expected = ((0x0806b0da, 'fdf70ffe', 0x08068cfc),
        (0x08068d0a, '00f03df8', 0x08068d88),
        (0x08068d98, 'fff798ff', 0x08068ccc),
        (0x08068cd2, '0df06fff', 0x08076bb4),
        (0x080f8a2c, '0af7f6f8', 0x08002c1c))
    for at, raw, target in expected:
        n = by.get(at, {})
        need(n.get('hex') == raw and n.get('kind') == 'call' and n.get('target') == target, '保存caller ' + hex(at))
    need(by[0x08068cce]['hex'] == '0348' and by[0x08068cce]['literal_value'] == CALLBACK, 'callback literal')
    need(by[0x08068cd0]['hex'] == '5021', 'task priority')
    need(by[0x08068d00]['literal_value'] == 0x02036fd0, '上流busy byte')
    need(by[0x080f8a2a]['literal_value'] == 0x083e30e8, '保存font初期化表')
    need(not any(LO <= at < HI for at in by), '既読taskの再採取禁止')
    entries = (0x08068cfd, 0x08068d89, 0x08068ccd, INITIALIZER)
    return {'new_root': CALLBACK, 'code_window': [LO, HI], 'maximum_bytes': HI - LO,
        'saved_call_chain': [dict(site=at, target=target | 1) for at, _, target in expected[:4]],
        'saved_inbound_calls': {str(t): [n['address'] for n in nodes if n.get('kind') == 'call' and n.get('target') == (t & ~1)] for t in entries},
        'initializer_nodes': [copy.deepcopy(by[p]) for p in (0x080f8a28, 0x080f8a2a, 0x080f8a2c, 0x080f8a30, 0x080f8a32)],
        'message_busy_address': 0x02036fd0, 'task_priority': 80,
        'runtime_reachability_proven': False, 'initializer_runtime_observed': False,
        'boundary_ja': '保存callerの接続だけ。未保存caller不存在/通常story到達/live window初期化は証明しない。'}


def validate_new(result, known):
    need(result['initial_roots'] == [CALLBACK] and not result['saved_roots_reused'], '新規task一根')
    need(result['saved_nodes_redecoded'] == result['direct_calls_recursively_expanded'] == 0, '旧命令/再帰禁止')
    need(not result['wave_limit_reached'] and not result['deferred_by_wave_limit'], 'task窓予算')
    nodes = result['new_nodes']; starts = [n['address'] for n in nodes]
    need(0 < len(nodes) <= 78 and starts == sorted(set(starts)) and starts[0] == LO, 'task node集合')
    occupied = set()
    for n in nodes:
        at, size = n['address'], n['size']; span = set(range(at, at + size))
        need(type(at) is int and at % 2 == 0 and size in (2, 4) and LO <= at < at + size <= HI, 'task命令境界')
        need(not span & (occupied | set(known)), 'task命令重複'); occupied |= span
        need(len(bytes.fromhex(n['hex'])) == size, 'task命令長')
        if 'literal_address' in n:
            need(LO <= n['literal_address'] <= HI - 4 and n['literal_address'] % 4 == 0, 'task literal境界')
    return occupied


def source_export(paths):
    """追跡済みPython依存だけをexport。ROM/save/config/環境値は収録しない。"""
    tracked = set(s.cmd('git', 'ls-files', '--', 'scripts/*.py', 'tests/*.py').splitlines())
    todo = [p for p in paths if p.endswith('.py')]; files = {}
    while todo:
        p = todo.pop()
        if p in files: continue
        need(p in tracked and p.startswith(('scripts/', 'tests/')), 'export追跡source境界')
        raw = (s.ROOT / p).read_bytes(); tree = ast.parse(raw.decode('utf-8')); files[p] = raw
        for node in ast.walk(tree):
            names = [n.name for n in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else []
            for name in names:
                if name and name.startswith('pr16_'):
                    dependency = 'scripts/' + name.split('.')[0] + '.py'
                    if dependency in tracked and dependency not in files: todo.append(dependency)
    return files


def analyze(previous, out):
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_remaining_frontier as walk
    import pr16_ring_owner_frontier as old
    nodes, a, inherited, owner = prior.saved_inputs()
    owner_plan = plan(nodes, previous['analysis'])
    _, memory, _, _ = prior.prior.saved_inputs()
    memory = dict(memory)
    for n in nodes:
        for i, value in enumerate(bytes.fromhex(n['hex'])): memory[n['address'] + i] = value
        if 'literal_address' in n:
            for i, value in enumerate(n['literal_value'].to_bytes(4, 'little')): memory[n['literal_address'] + i] = value
    paths = tuple(dict.fromkeys((SELF, TEST, WORKFLOW, PRIOR, *SOURCES)))
    (out / 'preflight.json').write_bytes(s.stable({'plan': owner_plan,
        'source_bindings': {p: s.identity((s.ROOT / p).read_bytes()) for p in paths}}))
    restored = any(at not in memory for at in range(LO, HI))
    if restored:
        restore.OUT = out; restore.restore()
        candidate = s.ROOT / '.local/pr16-bp-party-retention-successor/candidate.gba'
        raw = candidate.read_bytes(); saved.candidate_identity(raw)
    else:
        buf = bytearray(s.CANDIDATE['size'])
        for at, value in memory.items():
            if 0x08000000 <= at < 0x0a000000: buf[at - 0x08000000] = value
        raw = bytes(buf)
    def decode(data, at):
        need(LO <= at <= HI - 2, 'task窓外decode')
        n = decoder.thumb_instruction(data, at)
        need(at + n['size'] <= HI, 'task命令窓終端')
        if 'literal_address' in n: need(LO <= n['literal_address'] <= HI - 4, 'task literal窓外')
        return n
    def inspect(data, roots, known, decode_fn):
        rows = []; fresh = []; points = set(); cache = dict(known)
        for root in roots:
            need(LO <= root & ~1 < HI, 'task継続窓外')
            r = old.inspect_frontier(data, [root], cache, decode_fn, window=min(128, HI - (root & ~1)))
            rows.extend(r['roots']); fresh.extend(r['new_nodes']); points.update(r['points'])
            cache.update({n['address']: n for n in r['new_nodes']})
        return {'roots': rows, 'new_nodes': sorted(fresh, key=lambda n: n['address']), 'points': sorted(points)}
    result = walk.bounded_walk(raw, [CALLBACK], old.cache_nodes([{'nodes': nodes}]), decode, inspect,
        max_nodes=78, max_bytes=156, max_roots=8, max_rounds=8)
    points = result.pop('points'); validate_new(result, {p for n in nodes for p in range(n['address'], n['address'] + n['size'])})
    need(all(LO <= p < HI for p in points), '採取point境界')
    windows, reused = old.new_windows(raw, points, memory)
    if restored: need(s.identity(candidate.read_bytes()) == s.identity(raw), 'candidate不変')
    result.update({'classification': 'MESSAGE_TASK_BYTES_AND_SAVED_CALLERS_NOT_NATIVE_ACCEPTANCE',
        'candidate': dict(s.CANDIDATE), 'owner_plan': owner_plan, 'new_windows': windows,
        'new_node_count': len(result['new_nodes']), 'saved_node_count': len(nodes) + len(result['new_nodes']),
        'new_window_bytes': sum(w['end'] - w['start'] for w in windows), 'saved_bytes_reused': reused,
        'candidate_reconstructions': int(restored), 'rom_changes': 0, 'new_emulator_processes': 0,
        'accepted_native_cases_replayed': 0, 'accepted_standalone_contracts_replayed': 0, 'full_rom_scans': 0,
        'task_state_transitions_proven': False, 'task_runtime_observed': False,
        'initializer_runtime_observed': False, 'actual_callback_table_observed': False,
        'ring_acquisition_accepted': False, 'release_ready': False,
        'boundary_ja': '新taskのbyteと上流保存callerのみ。呼出先効果/状態遷移/通常story/画面は次の限定検証。'})
    files = source_export((SELF, TEST, prior.SELF, prior.TEST, s.SELF, export.SELF, *SOURCES))
    files['saved-context.json'] = s.stable({'nodes': [*nodes, *result['new_nodes']], 'analysis': a,
        'inherited_analysis': inherited, 'owner_analysis': owner, 'message_summary': previous['analysis'], 'task_frontier': result})
    manifest = export.bundle(files, out / 'export')
    result['export_manifest'] = s.identity((out / 'export/manifest.json').read_bytes())
    result['export_logical_files'] = len(manifest['files'])
    (out / 'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(r):
    return (f'登録task08068C31の新規{r["new_node_count"]}命令/{r["new_window_bytes"]}byteを限定保存。上流保存callerと初期化の未観測境界を固定。旧391条件/native再実行0。',
        '次は保存task callbackの状態遷移・待機/終了・task削除・不足時の部分writeを上流callerと結合検証する。'
        '必要な未読calleeだけを限定し、通常story到達/live window・gFonts初期化は未受入のまま。今回採取/旧391条件/BP/nativeを単独再実行しない。')


if __name__ == '__main__':
    need(sys.argv[1:] == ['run'], 'runだけを許可')
    s.assert_remote(s.cmd('git', 'rev-parse', 'HEAD'), attempts=12)
    s.run(sys.modules[__name__])
