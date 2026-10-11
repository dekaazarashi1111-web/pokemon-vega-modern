#!/usr/bin/env python3
"""未読3delegate/月表と未検索mirrored-PC参照だけを固定する。実到達は主張しない。"""
from __future__ import annotations
import array
import copy
import hashlib
import struct
import sys
from pathlib import Path

BASE = '04a56ac7d3c499ae0d63ebf09c9e119ee90d23df'
SLUG = 'pr16-ring-unread-frontier'
TASK = 'PR-P08-7-RING-UNREAD-FRONTIER'
TITLE = '未読3delegate・月表・mirrored-PC参照の限定追跡を保存'
SELF = 'scripts/pr16_ring_unread_frontier.py'
TEST = 'tests/test_pr16_ring_unread_frontier.py'
WORKFLOW = '.github/workflows/pr16-ring-unread-frontier.yml'
PRIOR = 'content/modernization/pr16_ring_session_closeout.json'
FRONTIER = 'content/modernization/pr16_ring_branch_frontier.json'
CONTRACTS = 'content/modernization/pr16_ring_delegate_contracts.json'
REPORT = 'content/modernization/pr16_ring_unread_frontier.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 42
EXTRA_CODE = ()
SOURCES = (FRONTIER, CONTRACTS, 'content/modernization/pr16_ring_selector_owners.json',
    'content/modernization/pr16_ring_record_callers.json', 'scripts/pr16_ring_branch_frontier.py',
    'scripts/pr16_ring_record_callers.py', 'scripts/pr16_ring_zero_bytes.py',
    '.github/workflows/pr16-ring-callee-bytes.yml')
NO_REPEAT = ('未読3delegate/月表の不足byteとmirrored-PC命令候補は保存原本を再利用する。'
    'canonical-PC探索、7delegate局所契約、BP/nativeを再実行しない。実caller/pointer/size/LIMITは未証明。')
ROM_BASE, ROM_SIZE = 0x08000000, 0x02000000
MIRRORS = (0x0A000000, 0x0C000000)
TARGET = 0x08113984
EXTERNALS = (0x0912C4A9, 0x0912C555, 0x09099E05)
MONTH = (0x09169530, 0x09169560)
FOCUS = ((0x0912C4A8, 0x0912C5FC), (0x09099E04, 0x0909A204), MONTH)
MAX_REFS, MAX_BYTES = 128, 32768


def need(ok, text):
    if not ok:
        raise ValueError(text)


def canonical(value):
    return ROM_BASE + ((value - ROM_BASE) % ROM_SIZE) if ROM_BASE <= value < 0x0E000000 else None


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def mirror_references(raw, target=TARGET, max_refs=MAX_REFS):
    """物理byteを二つの未検索PC帯で解釈。dataをcodeと認定せず候補のみ返す。"""
    need(type(raw) is bytes and 0 < len(raw) <= ROM_SIZE and len(raw) % 2 == 0, '入力範囲/整列')
    need(type(target) is int and target % 4 == 0 and ROM_BASE <= target < ROM_BASE + ROM_SIZE, 'target範囲')
    need(type(max_refs) is int and 0 < max_refs <= MAX_REFS, '候補上限')
    halves = array.array('H', raw)
    if sys.byteorder != 'little':
        halves.byteswap()
    found = []
    def add(offset, pc, size, kind, value, **details):
        value &= 0xFFFFFFFF
        if canonical(value & ~1) == target:
            found.append({'site': ROM_BASE + offset, 'execution_address': pc, 'target': target,
                'value': value, 'kind': kind, 'encoded': raw[offset:offset + size].hex(),
                'runtime_reachable': False, 'code_data_boundary_proven': False, **details})
            need(len(found) <= max_refs, '候補上限超過')
    def literal(offset, pc, size, pool, rd, kind, **details):
        physical = canonical(pool & 0xFFFFFFFF)
        if physical is not None and physical % 4 == 0 and ROM_BASE <= physical <= ROM_BASE + len(raw) - 4:
            value = struct.unpack_from('<I', raw, physical - ROM_BASE)[0]
            add(offset, pc, size, kind, value, literal_address=pool & 0xFFFFFFFF,
                physical_literal_address=physical, register=rd, **details)
    for i, half in enumerate(halves):
        offset = i * 2
        # Thumb PC相対形式。BLはARMv4Tの前後halfword対だけを候補化する。
        for base in MIRRORS:
            pc = base + offset
            if half & 0xF800 == 0xE000:
                add(offset, pc, 2, 'thumb_b', pc + 4 + 2 * signed(half & 2047, 11), condition=14)
            elif half & 0xF000 == 0xD000 and ((half >> 8) & 15) < 14:
                add(offset, pc, 2, 'thumb_b_cond', pc + 4 + 2 * signed(half & 255, 8), condition=(half >> 8) & 15)
            elif half & 0xF800 == 0xF000 and i + 1 < len(halves) and halves[i + 1] & 0xF800 == 0xF800:
                delta = ((half & 2047) << 12) | ((halves[i + 1] & 2047) << 1)
                add(offset, pc, 4, 'thumb_bl', pc + 4 + signed(delta, 23))
            elif half & 0xF800 == 0xA000:
                add(offset, pc, 2, 'thumb_adr', ((pc + 4) & ~3) + (half & 255) * 4, register=(half >> 8) & 7)
            elif half & 0xF800 == 0x4800:
                literal(offset, pc, 2, ((pc + 4) & ~3) + (half & 255) * 4, (half >> 8) & 7, 'thumb_literal')
        if i % 2 or i + 1 >= len(halves):
            continue
        word = half | (halves[i + 1] << 16)
        cond = word >> 28
        if cond == 15:
            continue
        for base in MIRRORS:
            pc = base + offset
            if word & 0x0E000000 == 0x0A000000:
                add(offset, pc, 4, 'arm_bl' if word & 0x01000000 else 'arm_b',
                    pc + 8 + 4 * signed(word & 0xFFFFFF, 24), condition=cond)
            if word & 0x0E1F0000 == 0x020F0000:
                op, rd = (word >> 21) & 15, (word >> 12) & 15
                if op in (2, 4) and rd != 15:
                    imm, rot = word & 255, ((word >> 8) & 15) * 2
                    imm = ((imm >> rot) | (imm << ((32 - rot) % 32))) & 0xFFFFFFFF
                    add(offset, pc, 4, 'arm_adr', pc + 8 + (imm if op == 4 else -imm), register=rd, condition=cond)
            if word & 0x0F7F0000 == 0x051F0000:
                pool = pc + 8 + ((word & 4095) if word & 0x00800000 else -(word & 4095))
                rd = (word >> 12) & 15
                literal(offset, pc, 4, pool, rd, 'arm_literal_pc' if rd == 15 else 'arm_literal', condition=cond)
    return sorted(found, key=lambda r: (r['site'], r['execution_address'], r['kind']))


def ranges(points):
    result = []
    for at in sorted(points):
        if result and result[-1][1] == at:
            result[-1][1] += 1
        else:
            result.append([at, at + 1])
    return result


def collect_unread(raw, memory, focus):
    """保存済byteを差分照合し、未知byteだけを返す。全ROMの再採取は禁止。"""
    need(type(raw) is bytes and 0 < len(raw) <= ROM_SIZE, 'ROM入力')
    points = set()
    for lo, hi in focus:
        need(type(lo) is int and type(hi) is int and ROM_BASE <= lo < hi <= ROM_BASE + len(raw), '窓範囲')
        need(hi - lo <= 2048, '個別窓上限')
        points.update(range(lo, hi))
        need(len(points) <= MAX_BYTES, '総byte上限')
    reused = points & memory.keys()
    need(all(memory[at] == raw[at - ROM_BASE] for at in reused), '保存byteと候補の不一致')
    fresh = []
    for lo, hi in ranges(points - memory.keys()):
        data = raw[lo - ROM_BASE:hi - ROM_BASE]
        fresh.append({'start': lo, 'end': hi, 'hex': data.hex(), 'identity': identity(data)})
    return fresh, ranges(reused), len(reused)


def decode_month_table(raw):
    need(type(raw) is bytes and len(raw) == 48, '月表48byte必須')
    return list(struct.unpack('<12I', raw))


def analyze(prior, out):
    import zlib
    import pr16_ring_followup_v2 as s
    import pr16_ring_record_callers as previous
    import pr16_ring_branch_frontier as frontier
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    reports = {p: s.load(p) for p in (FRONTIER, CONTRACTS, frontier.OWNERS, frontier.CALLERS)}
    for report in reports.values():
        saved.bindings_fresh(s.ROOT, report['source_bindings'])
    need(reports[CONTRACTS]['analysis']['unread_external_targets'] == list(EXTERNALS), '未読境界差分')
    need(prior['analysis']['next_unread_contracts']['initializer'] == TARGET, 'initializer差分')
    memory = previous.saved_memory(reports[frontier.OWNERS])
    for path in (frontier.CALLERS, FRONTIER):
        frontier.add_windows(memory, reports[path]['analysis']['new_windows'])
    restore.OUT = out
    restore.restore()
    candidate = s.ROOT / '.local/pr16-bp-party-retention-successor/candidate.gba'
    raw = candidate.read_bytes()
    need(identity(raw) == {k: s.CANDIDATE[k] for k in ('size', 'sha256')}
        and f'{zlib.crc32(raw):08X}' == s.CANDIDATE['crc32'], '候補identity差分')
    refs = mirror_references(raw)
    focus = list(FOCUS)
    for ref in refs:
        at = ref['site']
        focus.append((max(ROM_BASE, at - 32), min(ROM_BASE + ROM_SIZE, at + 96)))
    windows, reused_ranges, reused_count = collect_unread(raw, memory, focus)
    table = raw[MONTH[0] - ROM_BASE:MONTH[1] - ROM_BASE]
    need(identity(candidate.read_bytes()) == identity(raw), '候補の変更')
    result = {'classification': 'UNREAD_DELEGATES_MONTH_TABLE_AND_MIRROR_CANDIDATES_NOT_NATIVE_ACCEPTANCE',
        'candidate': copy.deepcopy(s.CANDIDATE), 'target': TARGET, 'execution_pc_bases': list(MIRRORS),
        'references': refs, 'unread_external_targets_sampled': list(EXTERNALS), 'focus_ranges': focus,
        'new_windows': windows, 'new_window_bytes': sum(w['end'] - w['start'] for w in windows),
        'saved_byte_ranges_reused': reused_ranges, 'saved_bytes_reused': reused_count,
        'month_table': {'start': MONTH[0], 'end': MONTH[1], 'identity': identity(table),
            'u32_le_values': decode_month_table(table), 'validated_as_calendar': False},
        'searched_forms': ['mirrored Thumb B/Bcond/BL/ADR/literal', 'mirrored ARM B/BL/immediate ADR/literal'],
        'unsearched_forms': ['register-computed/table-dispatched targets', 'nonliteral loads', 'execution from RAM'],
        'old_unread_targets': copy.deepcopy(prior['analysis']['old_unread_targets']),
        'old_frontier_removed': False, 'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
        'caller_pointer_size_limit_proven': False, 'selector1_runtime_observed': False, 'selector2_runtime_observed': False,
        'ring_acquisition_accepted': False, 'release_ready': False, 'rom_changes': 0,
        'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0, 'prior_abi_classifications_replayed': 0,
        'candidate_reconstructions': 1,
        'boundary_ja': '二つのROM alias帯に置いたPCの命令候補だけ。実行可否/実到達/RAM caller/全owner除外は未証明。'}
    (out / 'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(result):
    return (f'未読3delegate/月表の新規{result["new_window_bytes"]}byteとmirrored-PC参照{len(result["references"])}候補を固定。'
        f'保存{result["saved_bytes_reused"]}byteを再利用。候補復元1、ROM変更/native/BP再実行0。月表は値を採取しただけでcalendar契約未受入。',
        '保存した0x0912C4A9/0x0912C555/0x09099E05と12word月表を局所契約へ分解する。'
        'mirrored候補があればcode/data境界から追い、computed/RAM caller・initializer pointer/size/LIMITを未完に保つ。'
        '採取/旧7delegate/BPを再実行しない。旧18owner、Ring正規取得・装備実戦・保存、policy/Circus/P08は未完。')


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:] == ['run'], 'runのみ許可')
    support.run(sys.modules[__name__])
