#!/usr/bin/env python3
"""未読0x0806DE63だけを採取。既読命令/別の未読根をdecodeしない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_support as s

BASE = '1bf021c2c9526fce56b0533b962d4e6b5f4ce084'
SLUG = 'pr16-ring-epilogue-bytes'
TASK = 'PR-P08-7-RING-EPILOGUE-BYTES'
TITLE = '未読帰還末尾1根の限定採取と保存'
SELF = 'scripts/pr16_ring_epilogue_bytes.py'
TEST = 'tests/test_pr16_ring_epilogue_bytes.py'
WORKFLOW = '.github/workflows/pr16-ring-epilogue-bytes.yml'
PRIOR = 'content/modernization/pr16_ring_common_tail_abi.json'
REPORT = 'content/modernization/pr16_ring_epilogue_bytes.json'
KEY = 'ring_epilogue_bytes'
MIN_TESTS = 17
EXTRA_CODE = (s.SELF,)
TARGET = 0x0806DE63
ROM_BASE = 0x08000000
DEFERRED = (0x0806DE51, 0x08113889, 0x0806DD1D, 0x081138F9)
SAMPLE = 'content/modernization/pr16_ring_common_tail_bytes.json'
SOURCES = (SAMPLE, 'scripts/pr16_ring_common_tail_bytes.py', 'scripts/pr16_ring_zero_bytes.py',
           'scripts/pr16_ring_callee_bytes.py', 'scripts/pr16_ring_transitive_owner.py',
           'scripts/pr16_ring_flagset_continuation.py', '.github/workflows/pr16-ring-callee-bytes.yml')
NO_REPEAT = '0x0806DE63帰還末尾1根は採取保存済み。同一candidateで再採取せず保存byteだけでABIを検証する。既読prefix/BP再実行0を保持。'


def bounded(raw, target, cached, deferred, decode, max_window=64, limit=32):
    """採取だけの有限CFG。未知/別根/保存命令はdecode前に境界化する。"""
    s.need(type(target) is int and target & 1 and ROM_BASE <= target < ROM_BASE + len(raw), 'root不正')
    s.need(type(max_window) is int and 0 < max_window <= 64 and max_window % 2 == 0, 'window不正')
    s.need(type(limit) is int and 0 < limit <= 32, 'budget不正')
    start = target & ~1
    s.need(start not in cached, '既読root')
    stops = {p & ~1 for p in deferred}
    s.need(start not in stops, '別根と重複')
    end = min([start + max_window, ROM_BASE + len(raw)] + [x for x in cached if start < x < start + max_window])
    s.need(end > start and (end - start) % 2 == 0, '末尾境界不正')
    nodes, used, edges, pending = {}, set(), [], [start]
    while pending:
        at = pending.pop()
        if at in nodes:
            continue
        s.need(start <= at < end and at not in stops | cached | used, 'decode境界逸脱')
        s.need(len(nodes) < limit, '命令数上限')
        n = copy.deepcopy(decode(raw, at))
        s.need(n['address'] == at and n['size'] in (2, 4), 'decode位置/幅不一致')
        span = set(range(at, at + n['size']))
        s.need(at + n['size'] <= end and not span & (used | cached | stops), '命令境界重複')
        data = raw[at-ROM_BASE:at-ROM_BASE+n['size']]
        s.need(data.hex() == n['hex'] and type(n['memory_write']) is bool, '保存byte/注釈不一致')
        kind = n['kind']
        s.need(kind in ('ordinary','call','jump','conditional','indirect','return'), 'kind不明')
        successors = []
        def link(dest, edge_kind, always_external=False):
            s.need(type(dest) is int and dest % 2 == 0 and ROM_BASE <= dest < ROM_BASE + len(raw), '分岐先不正')
            if not always_external and start <= dest < end and dest not in stops and dest not in cached:
                successors.append(dest)
            else:
                edges.append({'site': at, 'kind': edge_kind, 'target': dest | 1,
                    'resolved_to_code_address_only': True,
                    'stop_reason': 'SAVED_OR_DEFERRED_OR_WINDOW_BOUNDARY_NOT_DECODED'})
        if kind in ('call','jump','conditional'):
            link(n['target'], kind, kind == 'call')
        if kind == 'indirect':
            s.need(type(n['register']) is int and 0 <= n['register'] <= 15, '間接register不正')
            edges.append({'site': at, 'kind': kind, 'register': n['register'], 'target': None})
        if kind not in ('return','indirect','jump'):
            link(at + n['size'], 'window_fallthrough')
        if 'literal_address' in n:
            addr = n['literal_address']
            h = int.from_bytes(data[:2], 'little')
            s.need(h & 0xf800 == 0x4800 and addr == ((at+4)&~3)+(h&255)*4, 'literal位置不一致')
            s.need(ROM_BASE <= addr <= ROM_BASE + len(raw) - 4, 'literal範囲外')
            s.need(int.from_bytes(raw[addr-ROM_BASE:addr-ROM_BASE+4], 'little') == n['literal_value'], 'literal不一致')
        n['successors'] = sorted(set(successors))
        nodes[at] = n
        used.update(span)
        pending.extend(n['successors'])
    return {'entry': target, 'window': end-start,
        'window_identity': s.identity(raw[start-ROM_BASE:end-ROM_BASE]),
        'nodes': [nodes[x] for x in sorted(nodes)], 'external_edges': sorted(edges, key=lambda e:(e['site'],e['kind'])),
        'memory_write_sites': sorted(at for at,n in nodes.items() if n['memory_write']),
        'deferred_unread_roots': list(deferred), 'deferred_roots_decoded': 0,
        'saved_instruction_bytes_redecoded': 0, 'side_effects_excluded': False}


def collect(target, deferred, extra_samples, out):
    import pr16_ring_common_tail_bytes as previous
    import pr16_ring_transitive_owner as decoder
    import pr16_ring_flagset_continuation as saved
    _, cached = previous.inputs()  # 保存byte集合を読むだけ。decode/ABI/nativeは実行しない。
    for path in (SAMPLE, *extra_samples):
        for n in s.load(path)['analysis']['graph']['nodes']:
            cached.update(range(n['address'], n['address'] + n['size']))
    s.need(target & ~1 not in cached, '採取済みtarget')
    previous.OUT = out
    previous.restore()
    rom = s.ROOT / '.local/pr16-bp-party-retention-successor/candidate.gba'
    raw = rom.read_bytes()
    saved.candidate_identity(raw)
    graph = bounded(raw, target, cached, deferred, decoder.thumb_instruction)
    ranges = previous.sample_ranges(raw, graph)
    s.need(rom.read_bytes() == raw, 'candidate変更')
    return graph, ranges


def analyze(prior, out):
    a = prior['analysis']
    s.need(a['continuation_thumb'] == TARGET and a['continuation_is_return'] is False, '次根不一致')
    s.need(len(set(a['old_unread_targets'])) == 18, '旧18target不一致')
    graph, ranges = collect(TARGET, DEFERRED, (), out)
    return {'classification': 'EPILOGUE_BYTES_NOT_RETURN_PROOF', 'candidate': copy.deepcopy(s.CANDIDATE),
        'target': TARGET, 'graph': graph, 'sampled_ranges': ranges,
        'sampled_instruction_bytes': sum(n['size'] for n in graph['nodes']),
        'old_unread_targets': a['old_unread_targets'], 'old_frontier_removed': False,
        'other_unread_roots_preserved': list(DEFERRED),
        'remaining_unread_targets': sorted(set(a['old_unread_targets']) | set(DEFERRED)),
        'callee_return_proven': False, 'callee_return_observed': False,
        'saved_slot_preservation_proven': False, 'return_pointer_non_alias_proven': False,
        'all_runtime_owners_excluded': False, 'ring_acquisition_accepted': False, 'release_ready': False,
        'rom_changes': 0, 'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0,
        'prior_abi_classifications_replayed': 0, 'new_graph_decodes': 1, 'candidate_reconstructions': 1}


def summaries(a):
    return (f'未読帰還末尾0x0806DE63だけを{len(a["graph"]["nodes"])}命令/{a["sampled_instruction_bytes"]}byte採取保存。'
        '命令byteと境界の採取工程のみ完了。帰還ABI/保存slot不変/非aliasは未証明。旧18targetと別分岐・外部call3本、BP受入を保持。',
        '保存済みpr16_ring_epilogue_bytes.jsonの命令だけで復元/帰還ABIを検証する。0x0806DE51と外部call3本は未解決。'
        '同じ末尾の再採取、既読共通末尾/zero/helper/FlagSet/FlagGet/BPの単独再実行をしない。Ring通常取得受入へ昇格しない。')


if __name__ == '__main__':
    s.run(sys.modules[__name__])
