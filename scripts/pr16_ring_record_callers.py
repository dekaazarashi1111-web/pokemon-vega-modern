#!/usr/bin/env python3
"""未読caller/RTC候補のbyte境界を採取。code/data・実到達は別工程。"""
from __future__ import annotations
import array
import copy
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = '9d0910f84f6fdda11649c3f8db5bb3e156a4a90e'
SLUG = 'pr16-ring-record-callers'
TASK = 'PR-P08-7-RING-RECORD-CALLERS'
TITLE = 'initializer実caller候補と外部calleeの未読byteだけを固定'
SELF = 'scripts/pr16_ring_record_callers.py'
TEST = 'tests/test_pr16_ring_record_callers.py'
WORKFLOW = '.github/workflows/pr16-ring-record-callers.yml'
PRIOR = 'content/modernization/pr16_ring_record_init.json'
OWNERS = 'content/modernization/pr16_ring_selector_owners.json'
REPORT = 'content/modernization/pr16_ring_record_callers.json'
KEY = 'ring_record_callers'
MIN_TESTS = 18
EXTRA_CODE = ()
SOURCES = (OWNERS, 'scripts/pr16_ring_selector_followup.py', 'scripts/pr16_ring_zero_bytes.py',
           '.github/workflows/pr16-ring-callee-bytes.yml')
NO_REPEAT = ('initializer/外部callee6根のBL・pointer参照と不足byteは保存原本を再利用する。'
             'selectorの既存literal採取/initializer ABI/BP/nativeは再実行しない。'
             '採取されたcall候補は実到達やRing取得受入を意味しない。')
ROM_BASE = 0x08000000
TARGETS = (0x08113984, 0x09126CB4, 0x09127060, 0x09099E16, 0x091270E4, 0x09127148)
FOCUS = ((0x09126CB4, 0x09126DF0), (0x09127060, 0x091270E4), (0x09099E16, 0x09099E96))
MAX_REFS, MAX_BYTES = 256, 40000


def bl_target(at, hi, lo):
    """ARMv4T Thumb BLだけ。BLX/Thumb2 B.Wを受理しない。"""
    if hi & 0xf800 != 0xf000 or lo & 0xf800 != 0xf800:
        return None
    offset = ((hi & 2047) << 12) | ((lo & 2047) << 1)
    if hi & 1024:
        offset -= 1 << 23
    return (at + 4 + offset) & 0xffffffff


def references(raw, targets, max_refs=MAX_REFS):
    s.need(type(raw) is bytes and len(raw) % 2 == 0, '入力型/整列')
    s.need(targets and len(targets) == len(set(targets)), '空/重複target')
    s.need(all(type(t) is int and ROM_BASE <= t < 0x0a000000 and t % 2 == 0 for t in targets), 'target範囲')
    s.need(type(max_refs) is int and 0 < max_refs <= MAX_REFS, '参照上限')
    words = array.array('H', raw)
    if sys.byteorder != 'little':
        words.byteswap()
    found = []
    def add(site, target, kind, encoded):
        found.append({'site': site, 'target': target, 'kind': kind, 'encoded': encoded,
                      'runtime_reachable': False, 'code_data_boundary_proven': False})
        s.need(len(found) <= max_refs, '参照上限超過')
    targets = set(targets)
    for i in range(len(words)-1):
        if words[i] & 0xf800 != 0xf000:
            continue
        at = ROM_BASE + i*2
        target = bl_target(at, words[i], words[i+1])
        if target in targets:
            add(at, target, 'thumb_bl_candidate', raw[i*2:i*2+4].hex())
    for target in sorted(targets):
        for value in (target, target | 1):
            needle = struct.pack('<I', value)
            pos = raw.find(needle)
            while pos >= 0:
                if pos % 4 == 0:
                    add(ROM_BASE+pos, target, 'aligned_pointer_candidate', f'0x{value:08X}')
                pos = raw.find(needle, pos+1)
    return sorted(found, key=lambda r: (r['site'], r['kind'], r['target']))


def merge_bytes(memory, at, data):
    s.need(type(at) is int and type(data) is bytes and ROM_BASE <= at <= at+len(data) <= 0x0a000000, '保存範囲')
    for n, byte in enumerate(data, at):
        s.need(n not in memory or memory[n] == byte, '保存byte矛盾')
        memory[n] = byte


def ranges(points):
    result = []
    for at in sorted(set(points)):
        if result and result[-1][1] == at:
            result[-1][1] += 1
        else:
            result.append([at, at+1])
    return result


def requested_points(refs, raw, focus=FOCUS):
    """対象前後と、その限定領域のPC相対literalのみ。一段で打ち切る。"""
    size = len(raw)
    spans = list(focus) + [(r['site']-96, r['site']+128) for r in refs]
    points = set()
    for lo, hi in spans:
        s.need(type(lo) is int and type(hi) is int and lo < hi, 'window不正')
        points.update(range(max(ROM_BASE, lo), min(ROM_BASE+size, hi)))
    s.need(len(points) <= MAX_BYTES, 'window上限')
    literals = set()
    for at in sorted(points):
        if at % 2 or at+1 not in points:
            continue
        h = struct.unpack_from('<H', raw, at-ROM_BASE)[0]
        if h & 0xf800 == 0x4800:
            pool = ((at+4) & ~3) + (h & 255)*4
            if ROM_BASE <= pool <= ROM_BASE+size-4:
                literals.update(range(pool, pool+4))
    points |= literals
    s.need(len(points) <= MAX_BYTES, 'literal追加上限')
    return points


def saved_memory(owners):
    import pr16_ring_selector_followup as previous
    memory = {}
    for window in owners['analysis']['new_windows']:
        data = bytes.fromhex(window['hex'])
        s.need(len(data) == window['end']-window['start'] and s.identity(data) == window['identity'], '保存window identity')
        merge_bytes(memory, window['start'], data)
    # 採取済み命令とliteralを再利用するだけ。以前のanalyze/native_graphは呼ばない。
    for name, binding in owners['analysis']['saved_evidence_bindings'].items():
        path = Path(name)
        s.need(not path.is_absolute() and '..' not in path.parts and path.suffix == '.json', '保存path不正')
        raw = (s.ROOT/path).read_bytes()
        s.need(s.identity(raw) == binding, '保存証拠変更')
        previous.node_bytes(json.loads(raw), memory)
    return memory


def analyze(prior, out):
    import pr16_ring_zero_bytes as restore
    import pr16_ring_flagset_continuation as saved
    import zlib
    owners = s.load(OWNERS)
    saved.bindings_fresh(s.ROOT, owners['source_bindings'])
    memory = saved_memory(owners)
    fixed = {p: s.identity((s.ROOT/p).read_bytes()) for p in SOURCES}
    (out/'preflight.json').write_bytes(s.stable({'source_bindings': fixed, 'targets': TARGETS,
        'purpose_ja': '実caller候補・外部calleeの未採取byte。selector literalや受入nativeは再実行しない。'}))
    restore.OUT = out
    restore.restore()
    path = s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw = path.read_bytes()
    s.need(s.identity(raw) == {k: s.CANDIDATE[k] for k in ('size','sha256')}
           and f'{zlib.crc32(raw):08X}' == s.CANDIDATE['crc32'], 'candidate差分')
    refs = references(raw, TARGETS)
    points = requested_points(refs, raw)
    reused = points & memory.keys()
    for at in reused:
        s.need(memory[at] == raw[at-ROM_BASE], '保存byteとcandidate差分')
    fresh = []
    for lo, hi in ranges(points - memory.keys()):
        data = raw[lo-ROM_BASE:hi-ROM_BASE]
        fresh.append({'start': lo, 'end': hi, 'hex': data.hex(), 'identity': s.identity(data)})
    s.need(s.identity(path.read_bytes()) == s.identity(raw), 'candidate変更')
    result = {'classification': 'BOUNDED_NEW_CALLER_BYTES_NOT_NATIVE_OR_CODE_REACHABILITY',
        'candidate': copy.deepcopy(s.CANDIDATE), 'targets': list(TARGETS), 'references': refs,
        'target_counts': {f'0x{t:08X}': sum(r['target']==t for r in refs) for t in TARGETS},
        'focus_ranges': list(FOCUS), 'new_windows': fresh,
        'new_window_bytes': sum(w['end']-w['start'] for w in fresh),
        'saved_byte_ranges_reused': ranges(reused), 'saved_bytes_reused': len(reused),
        'saved_owner_report': OWNERS, 'old_unread_targets': copy.deepcopy(prior['analysis']['old_unread_targets']),
        'old_frontier_removed': False, 'all_callers_resolved': False,
        'selector1_runtime_observed': False, 'selector2_runtime_observed': False,
        'allocated_storage_extent_proven': False, 'all_runtime_owners_excluded': False,
        'ring_acquisition_accepted': False, 'release_ready': False, 'rom_changes': 0,
        'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0,
        'prior_abi_classifications_replayed': 0, 'candidate_reconstructions': 1,
        'boundary_ja': 'BL/pointerのbyte一致は命令境界/実到達の証明ではない。0参照を不存在としない。'}
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(result):
    return (f'initializer/外部callee6根の未読caller候補{len(result["references"])}件、'
            f'新規{result["new_window_bytes"]}byte採取、保存{result["saved_bytes_reused"]}byte再利用。'
            'selector literal/initializer ABI/受入BP/native再実行0。コード境界と実到達は未証明。',
            '保存したrecord caller証拠から0x08113984 callerのpointer/size/LIMITとselector設定を結合し、'
            '0x09126CB4/0x09127060/0x09099E16の実作用とcallersを検証する。再採取せず、'
            'RTC aliasの存在と通常story到達を分離する。旧18owner・Ring取得/装備実戦/保存は未完。')


if __name__ == '__main__':
    s.need(sys.argv[1:] == ['run'], 'runだけを許可')
    s.run(sys.modules[__name__])
