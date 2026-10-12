#!/usr/bin/env python3
"""未検索分岐形式と未読delegateを限定採取。命令候補を実到達へ昇格しない。"""
from __future__ import annotations
import array
import copy
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = '37e57f61bc891c5b8fb862b1b556a51276b957ea'
SLUG = 'pr16-ring-branch-frontier'
TASK = 'PR-P08-7-RING-BRANCH-FRONTIER'
TITLE = '未検索分岐・間接参照候補と6delegateの不足byteを固定'
SELF = 'scripts/pr16_ring_branch_frontier.py'
TEST = 'tests/test_pr16_ring_branch_frontier.py'
WORKFLOW = '.github/workflows/pr16-ring-branch-frontier.yml'
PRIOR = 'content/modernization/pr16_ring_control_closeout.json'
ROLES = 'content/modernization/pr16_ring_control_roles.json'
CALLERS = 'content/modernization/pr16_ring_record_callers.json'
OWNERS = 'content/modernization/pr16_ring_selector_owners.json'
REPORT = 'content/modernization/pr16_ring_branch_frontier.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 30
EXTRA_CODE = ()
SOURCES = (ROLES, CALLERS, OWNERS, 'scripts/pr16_ring_record_callers.py',
           'scripts/pr16_ring_selector_followup.py', 'scripts/pr16_ring_zero_bytes.py',
           '.github/workflows/pr16-ring-callee-bytes.yml')
NO_REPEAT = ('未検索Thumb短分岐/ADR・ARM B/BL/ADR・PC相対literal参照の探索と6delegateの不足byte採取は保存原本を再利用。'
             'canonical実行addressに限定した候補探索で、computed pointer/実到達/全caller不存在は未証明。')
ROM_BASE, ROM_SIZE = 0x08000000, 0x02000000
INITIALIZER = 0x08113984
DELEGATES = (0x081C9DF9, 0x0912C5FD, 0x0912C7ED, 0x0912C631, 0x0912C665, 0x09126EFD)
MAX_REFS = 128


def signed(value, width):
    return value - (1 << width) if value & (1 << (width-1)) else value


def canonical(value):
    """ROM wait-state aliasの数値正規化のみ。実行/アクセス成立の証明ではない。"""
    return ROM_BASE + ((value-ROM_BASE) % ROM_SIZE) if ROM_BASE <= value < 0x0E000000 else None


def thumb_branch(at, half):
    if half & 0xF800 == 0xE000:
        return (at+4+2*signed(half & 2047, 11)) & 0xFFFFFFFF, 'thumb_b', 14
    if half & 0xF000 == 0xD000 and (half >> 8) & 15 < 14:
        return (at+4+2*signed(half & 255, 8)) & 0xFFFFFFFF, 'thumb_b_cond', (half >> 8) & 15
    return None


def arm_branch(at, word):
    cond = word >> 28
    if cond < 15 and word & 0x0E000000 == 0x0A000000:
        return (at+8+4*signed(word & 0xFFFFFF, 24)) & 0xFFFFFFFF, ('arm_bl' if word & 0x01000000 else 'arm_b'), cond
    return None


def arm_adr(at, word):
    # immediate ADD/SUB Rd,PC,#imm、S=0だけ。条件とRdは候補に保持する。
    if word >> 28 == 15 or word & 0x0E1F0000 != 0x020F0000:
        return None
    op, rd = (word >> 21) & 15, (word >> 12) & 15
    if op not in (2, 4) or rd == 15:
        return None
    value, rotation = word & 255, ((word >> 8) & 15)*2
    value = ((value >> rotation) | (value << ((32-rotation) % 32))) & 0xFFFFFFFF
    return (at+8+(value if op == 4 else -value)) & 0xFFFFFFFF, rd


def arm_literal(at, word):
    # immediate, preindexed, word LDR, PC base, no writeback。
    if word >> 28 == 15 or word & 0x0F7F0000 != 0x051F0000:
        return None
    delta = word & 4095
    return (at+8+(delta if word & 0x00800000 else -delta)) & 0xFFFFFFFF, (word >> 12) & 15


def references(raw, target=INITIALIZER, max_refs=MAX_REFS):
    s.need(type(raw) is bytes and 0 < len(raw) <= ROM_SIZE and len(raw) % 2 == 0, '入力範囲/整列')
    s.need(type(target) is int and target % 4 == 0 and ROM_BASE <= target < ROM_BASE+ROM_SIZE, 'target範囲/整列')
    s.need(type(max_refs) is int and 0 < max_refs <= MAX_REFS, '参照上限')
    halves = array.array('H', raw)
    if sys.byteorder != 'little':
        halves.byteswap()
    found = []
    def add(at, size, kind, value, **more):
        if canonical(value & ~1) != target:
            return
        found.append({'site': at, 'kind': kind, 'target': target, 'value': value,
            'encoded': raw[at-ROM_BASE:at-ROM_BASE+size].hex(),
            'code_data_boundary_proven': False, 'runtime_reachable': False, **more})
        s.need(len(found) <= max_refs, '参照上限超過')
    def literal(at, size, pool, rd, kind):
        pos = canonical(pool)
        if pos is not None and pos % 4 == 0 and ROM_BASE <= pos <= ROM_BASE+len(raw)-4:
            value = struct.unpack_from('<I', raw, pos-ROM_BASE)[0]
            add(at, size, kind, value, literal_address=pool, register=rd)
    for i, half in enumerate(halves):
        at = ROM_BASE+2*i
        branch = thumb_branch(at, half)
        if branch:
            value, kind, cond = branch
            add(at, 2, kind, value, condition=cond)
        if half & 0xF800 == 0xA000:
            add(at, 2, 'thumb_adr_pointer', ((at+4) & ~3)+(half & 255)*4, register=(half >> 8) & 7)
        if half & 0xF800 == 0x4800:
            literal(at, 2, ((at+4) & ~3)+(half & 255)*4, (half >> 8) & 7, 'thumb_literal_pointer')
        if i % 2 or i+1 >= len(halves):
            continue
        word = half | (halves[i+1] << 16)
        branch = arm_branch(at, word)
        if branch:
            value, kind, cond = branch
            add(at, 4, kind, value, condition=cond)
        adr = arm_adr(at, word)
        if adr:
            add(at, 4, 'arm_adr_pointer', adr[0], register=adr[1], condition=word >> 28)
        load = arm_literal(at, word)
        if load:
            literal(at, 4, load[0], load[1], 'arm_literal_pc' if load[1] == 15 else 'arm_literal_pointer')
    return sorted(found, key=lambda r: (r['site'], r['kind']))


def add_windows(memory, windows):
    import pr16_ring_record_callers as previous
    for window in windows:
        data = bytes.fromhex(window['hex'])
        s.need(window['end']-window['start'] == len(data) and s.identity(data) == window['identity'], '保存window差分')
        previous.merge_bytes(memory, window['start'], data)


def analyze(prior, out):
    import pr16_ring_record_callers as previous
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    import zlib
    roles, callers, owners = (s.load(p) for p in (ROLES, CALLERS, OWNERS))
    for report in (roles, callers, owners):
        saved.bindings_fresh(s.ROOT, report['source_bindings'])
    s.need(roles['analysis']['unread_delegates'] == list(DELEGATES), 'delegate境界変更')
    memory = previous.saved_memory(owners)
    add_windows(memory, callers['analysis']['new_windows'])
    (out/'preflight.json').write_bytes(s.stable({'source_bindings': {p: s.identity((s.ROOT/p).read_bytes()) for p in SOURCES},
        'new_search_target': INITIALIZER, 'unread_delegates': list(DELEGATES)}))
    restore.OUT = out
    restore.restore()
    path = s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw = path.read_bytes()
    s.need(s.identity(raw) == {k: s.CANDIDATE[k] for k in ('size','sha256')}
           and f'{zlib.crc32(raw):08X}' == s.CANDIDATE['crc32'], 'candidate差分')
    refs = references(raw)
    focus = [(t & ~1, (t & ~1)+1024) for t in DELEGATES] + [(INITIALIZER-64, INITIALIZER+256)]
    points = previous.requested_points(refs, raw, focus=focus)
    reused = points & memory.keys()
    for at in reused:
        s.need(memory[at] == raw[at-ROM_BASE], '保存byteとcandidate差分')
    fresh = []
    for lo, hi in previous.ranges(points-memory.keys()):
        data = raw[lo-ROM_BASE:hi-ROM_BASE]
        fresh.append({'start': lo, 'end': hi, 'hex': data.hex(), 'identity': s.identity(data)})
    s.need(s.identity(path.read_bytes()) == s.identity(raw), 'candidate変更')
    result = {'classification': 'NEW_BRANCH_FORMS_AND_DELEGATE_BYTES_NOT_NATIVE_ACCEPTANCE',
        'candidate': copy.deepcopy(s.CANDIDATE), 'target': INITIALIZER, 'references': refs,
        'searched_forms': ['Thumb B/Bcond', 'Thumb ADR', 'ARM B/BL', 'ARM immediate ADR', 'Thumb/ARM PC-relative literal pointers'],
        'scan_execution_address_scope': 'canonical 0x08000000..0x09FFFFFF; literal values normalize ROM aliases only',
        'unsearched_forms': ['register-computed/table-dispatched targets', 'nonliteral loads', 'execution from RAM', 'execution at mirrored PC addresses'],
        'unread_delegates_sampled': list(DELEGATES), 'focus_ranges': focus, 'new_windows': fresh,
        'new_window_bytes': sum(w['end']-w['start'] for w in fresh),
        'saved_byte_ranges_reused': previous.ranges(reused), 'saved_bytes_reused': len(reused),
        'reused_reports': [OWNERS, CALLERS, ROLES, PRIOR],
        'old_unread_targets': copy.deepcopy(roles['analysis']['old_unread_targets']),
        'old_frontier_removed': False, 'all_callers_resolved': False, 'all_runtime_owners_excluded': False,
        'caller_pointer_size_limit_proven': False, 'selector1_runtime_observed': False, 'selector2_runtime_observed': False,
        'ring_acquisition_accepted': False, 'release_ready': False, 'rom_changes': 0,
        'new_emulator_processes': 0, 'accepted_native_cases_replayed': 0, 'prior_abi_classifications_replayed': 0,
        'candidate_reconstructions': 1, 'boundary_ja': '全ROM走査でも列挙した命令形式のbyte候補だけ。0候補はcaller不在証明ではない。'}
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(result):
    return (f'未検索の短分岐/ARM/PC相対参照は{len(result["references"])}候補。6delegate用に新規{result["new_window_bytes"]}byte、'
            f'保存{result["saved_bytes_reused"]}byte再利用。候補復元1、ROM変更/native/BP受入再実行0。'
            '実到達とcaller pointer/size/LIMITは未証明。',
            '保存branch-frontierから0x081C9DF9とI/O wrapperの5delegateを局所契約へ分解し、'
            '新候補の命令境界・実caller接続を絞る。byte再採取/既読BCD検証を繰り返さず、'
            'computed/RAM/mirrored-PC参照と旧18ownerを未完に保つ。Ring正規取得・装備実戦・保存は未受入。')


if __name__ == '__main__':
    s.need(sys.argv[1:] == ['run'], 'runだけを許可')
    s.run(sys.modules[__name__])
