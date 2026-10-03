#!/usr/bin/env python3
"""保存external2全28命令のu16分類・stack帰還を限定検証。ROM/既読ABIは実行しない。"""
from __future__ import annotations
import copy
from functools import lru_cache
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = '0476b02407d6d86ea62e38cb834b34df7b9db012'
SLUG = 'pr16-ring-external2-abi'
TASK = 'PR-P08-7-RING-EXTERNAL2-ABI'
TITLE = 'external2全u16分類と条件付きstack帰還ABIを保存byteで検証'
SELF = 'scripts/pr16_ring_external2_abi.py'
TEST = 'tests/test_pr16_ring_external2_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-external2-abi.yml'
PRIOR = 'content/modernization/pr16_ring_external2_bytes.json'
REPORT = 'content/modernization/pr16_ring_external2_abi.json'
KEY = 'ring_external2_abi'
SOURCES = ()
EXTRA_CODE = ()
MIN_TESTS = 24
START = 0x0806DD1C
MASK = 0xffffffff
REFERENCE = 'https://sourceware.org/cgen/gen-doc/arm-thumb-insn.html'
NO_REPEAT = 'external2 0x0806DD1Dの保存28命令/56byteは全u16×2mode分類と局所stack帰還ABIを検証済み。同一入力の再採取/単独ABI再実行をしない。外側callee・保存slot/返却pointer非alias・Ring通常取得の受入へ昇格せず、次は0x081138F9の1根だけ進める。'
CODE = dict(zip([*range(0, 36, 2), *range(44, 64, 2)],
    ('00b5','0004','020c','101c','0906','0029','0ed1','0548','8242','05d9',
     '0449','5018','0004','000c','1f28','0cd8','0020','0be0','2f2a','f7d9',
     '5038','0004','000c','6328','f2d9','0120','02bc','0847')))
LITERALS = {START + 36: 559, START + 40: 0xfffff800}
EDGES = [{'site': START + 62, 'kind': 'indirect', 'register': 1, 'target': None}]


def target(at, half):
    bits = 8 if half & 0xf000 == 0xd000 else 11
    offset = half & ((1 << bits) - 1)
    if offset & (1 << (bits - 1)): offset -= 1 << bits
    return at + 4 + 2 * offset


def expected_nodes():
    rows = []
    for offset, hx in CODE.items():
        at = START + offset; h = int.from_bytes(bytes.fromhex(hx), 'little')
        row = dict(address=at, size=2, hex=hx, kind='ordinary', memory_write=(offset == 0), successors=[at + 2])
        if h & 0xf800 == 0x4800:
            address = ((at + 4) & ~3) + (h & 255) * 4
            row.update(literal_address=address, literal_value=LITERALS[address])
        elif h & 0xf000 == 0xd000:
            row.update(kind='conditional', target=target(at, h), successors=sorted({at + 2, target(at, h)}))
        elif h & 0xf800 == 0xe000:
            row.update(kind='jump', target=target(at, h), successors=[target(at, h)])
        elif h == 0x4708:
            row.update(kind='indirect', register=1, successors=[])
        rows.append(row)
    return rows


def expected_ranges():
    ranges = {START + offset: bytes.fromhex(hx) for offset, hx in CODE.items()}
    ranges.update({address: value.to_bytes(4, 'little') for address, value in LITERALS.items()})
    return [dict(address=address, hex=raw.hex(), **s.identity(raw)) for address, raw in sorted(ranges.items())]


def program(prior):
    s.need(prior['task'] == 'PR-P08-7-RING-EXTERNAL2-BYTES', '先行task差分')
    a = prior['analysis']; g = a['graph']
    s.need(a['candidate'] == s.CANDIDATE and a['target'] == a['next_saved_abi_target'] == START | 1, 'candidate/target差分')
    s.need(g['entry'] == START | 1 and g['window'] == 64 and g['window_identity'] ==
           {'size': 64, 'sha256': 'b96d5214fc806b6a7da5d8d70234aefa6945d60c591223a31902844f065a529a'}, 'window差分')
    s.need(g['nodes'] == expected_nodes() and g['external_edges'] == EDGES
           and g['memory_write_sites'] == [START], '保存命令/辺/副作用差分')
    s.need(a['sampled_ranges'] == expected_ranges() and a['sampled_instruction_bytes'] == 56, '保存byte/hash差分')
    s.need(g['saved_instruction_bytes_redecoded'] == g['deferred_roots_decoded'] == 0, '再decode')
    old, remaining = set(a['old_unread_targets']), set(a['remaining_unread_targets'])
    s.need(len(old) == 18 and old <= remaining and 0x081138F9 in remaining
           and START | 1 not in remaining and a['new_unread_targets'] == [], 'frontier差分')
    for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[key] is False, '過大受入')
    return a


def execute(ident, mode, sp=0x03007F00, lr=0x08100001, preserved=(4,5,6,7,8,9,10,11), return_slot_override=None):
    """保存code専用。stackは有効な1wordと仮定し、branch先は実行しない。"""
    s.need(all(type(x) is int and 0 <= x <= MASK for x in (ident, mode, lr)), 'u32範囲')
    s.need(type(sp) is int and 4 <= sp <= MASK and sp % 4 == 0, 'stack範囲/整列')
    s.need(len(preserved) == 8 and all(type(x) is int and 0 <= x <= MASK for x in preserved), '保存register範囲')
    s.need(return_slot_override is None or (type(return_slot_override) is int and 0 <= return_slot_override <= MASK), 'slot範囲')
    r = [0] * 16; r[0] = ident; r[1] = mode; r[4:12] = preserved; r[13] = sp; r[14] = lr
    pc, compare = START, None
    coverage, branches, reads, writes = [], [], [], []
    slot = None
    for _ in range(40):
        s.need(pc - START in CODE and pc not in coverage, '未知命令/循環')
        at = pc; h = int.from_bytes(bytes.fromhex(CODE[pc - START]), 'little'); pc += 2; coverage.append(at)
        if h == 0xb500:
            r[13] -= 4; slot = lr; writes.append({'site': at, 'address': r[13], 'size': 4, 'value': lr})
        elif h == 0xbc02:
            r[1] = slot if return_slot_override is None else return_slot_override
            reads.append({'site': at, 'address': r[13], 'size': 4, 'value': r[1]}); r[13] += 4
        elif h == 0x4708:
            return {'r0': r[0], 'r1': r[1], 'r2': r[2], 'r4_r11': r[4:12], 'lr': r[14],
                'exit_sp': r[13], 'local_sp_delta': r[13] - sp, 'branch_operand': r[1],
                'selected_isa': 'THUMB' if r[1] & 1 else 'ARM', 'branch_target_executed': False,
                'coverage': coverage, 'branches': branches, 'stack_reads': reads, 'memory_writes': writes}
        elif h & 0xf800 in (0x0000, 0x0800):
            value = r[(h >> 3) & 7]; shift = (h >> 6) & 31
            r[h & 7] = (value << shift) & MASK if h & 0xf800 == 0 else value >> (shift or 32)
            compare = None
        elif h & 0xf800 == 0x1800:
            rhs = (h >> 6) & 7 if h & 0x400 else r[(h >> 6) & 7]
            s.need(h & 0x200 == 0, '未対応SUB形式')
            r[h & 7] = (r[(h >> 3) & 7] + rhs) & MASK; compare = None
        elif h & 0xf800 == 0x4800:
            address = ((at + 4) & ~3) + (h & 255) * 4
            r[(h >> 8) & 7] = LITERALS[address]
        elif h & 0xf800 == 0x2800:
            compare = (r[(h >> 8) & 7], h & 255)
        elif h & 0xffc0 == 0x4280:
            compare = (r[h & 7], r[(h >> 3) & 7])
        elif h & 0xf800 == 0x3800:
            r[(h >> 8) & 7] = (r[(h >> 8) & 7] - (h & 255)) & MASK; compare = None
        elif h & 0xf800 == 0x2000:
            r[(h >> 8) & 7] = h & 255; compare = None
        elif h & 0xf000 == 0xd000:
            s.need(compare is not None, '比較flags不明')
            left, right = compare; cond = (h >> 8) & 15
            s.need(cond in (1, 8, 9), '未対応条件')
            taken = {1: left != right, 8: left > right, 9: left <= right}[cond]
            branches.append((at, taken))
            if taken: pc = target(at, h)
        elif h & 0xf800 == 0xe000:
            pc = target(at, h)
        else:
            raise ValueError('未対応命令')
    raise ValueError('命令budget超過')


def formula(ident, mode):
    value = ident & 65535
    return int(value >= 560 and not 2048 <= value <= 2079) if mode & 255 == 0 else int(value >= 48 and not 80 <= value <= 179)


@lru_cache(maxsize=1)
def exhaustive():
    counts, coverage, branches, max_steps = [], set(), set(), 0
    for mode in (0, 1):
        true_count = 0
        for value in range(65536):
            r = execute(value, mode)
            s.need(r['r0'] == formula(value, mode) and r['r2'] == value and r['r4_r11'] == list(range(4,12)), '分類/register差分')
            s.need(r['local_sp_delta'] == 0 and r['branch_operand'] == r['lr'] == 0x08100001
                   and len(r['memory_writes']) == len(r['stack_reads']) == 1, 'stack帰還差分')
            true_count += r['r0']; coverage.update(r['coverage']); branches.update(r['branches']); max_steps = max(max_steps, len(r['coverage']))
        counts.append(true_count)
    conditional = {n['address'] for n in expected_nodes() if n['kind'] == 'conditional'}
    s.need(coverage == {START + offset for offset in CODE} and branches == {(at,taken) for at in conditional for taken in (False,True)}, 'CFG未被覆')
    s.need(counts == [64944, 65388], '分類件数差分')
    return {'u16_inputs_per_mode_class': 65536, 'mode_classes': [0, 1], 'mode_classes_meaning': ['low_u8_zero', 'low_u8_nonzero'],
        'executed_input_cases': 131072, 'true_counts': counts, 'false_counts': [65536 - n for n in counts],
        'covered_instruction_sites': sorted(coverage), 'covered_conditional_outcomes': len(branches), 'max_instructions_per_case': max_steps}


def analyze(prior, out):
    a = program(prior); cases = exhaustive()
    return {'classification': 'EXTERNAL2_U16_PREDICATE_AND_CONDITIONAL_LOCAL_RETURN_ABI',
        'candidate': copy.deepcopy(s.CANDIDATE), 'instructions_verified': 28, 'instruction_bytes_verified': 56,
        'exhaustive': copy.deepcopy(cases), 'input_normalization': {'r0': 'low_u16', 'r1': 'low_u8_zero_vs_nonzero'},
        'zero_mode_false_ranges_inclusive': [[0,559],[2048,2079]],
        'nonzero_mode_false_ranges_inclusive': [[0,47],[80,179]],
        'result_range': [0,1], 'local_sp_delta': 0, 'local_peak_frame_bytes': 4,
        'preserved_registers': [*range(4,12),14], 'local_nonstack_writes': 0, 'external_calls': 0,
        'stack_effect': {'store_site': START, 'read_site': START + 60, 'address': 'entry_sp - 4', 'size': 4, 'stored_value': 'entry_lr'},
        'return_boundary': {'site': START + 62, 'register': 1, 'value_under_stable_stack': 'entry_lr', 'target_executed': False},
        'model_preconditions_ja': ['entry_spが4byte整列しentry_sp-4のwordが有効な読書き領域である。',
            '局所PUSHからPOPまでstack wordが外部書込で破壊されない。', '帰還先とISAの妥当性、caller/外側frame非aliasは別途検証する。'],
        'external2_local_return_under_model_preconditions': True, 'external2_unconditional_return_proven': False,
        'old_unread_targets': a['old_unread_targets'], 'remaining_unread_targets': a['remaining_unread_targets'],
        'priority_unread_targets': [0x081138F9], 'unresolved_indirect_edges': a['unresolved_indirect_edges'],
        'prior_external1_indirect_edges_preserved': a['prior_external1_indirect_edges_preserved'],
        'callee_return_proven': False, 'callee_return_observed': False, 'saved_slot_preservation_proven': False,
        'return_pointer_non_alias_proven': False, 'all_runtime_owners_excluded': False, 'ring_acquisition_accepted': False,
        'release_ready': False, 'rom_changes': 0, 'new_emulator_processes': 0, 'candidate_reconstructions': 0,
        'new_graph_decodes': 0, 'accepted_native_cases_replayed': 0, 'prior_abi_classifications_replayed': 0,
        'agent_reference_review': {'url': REFERENCE, 'query': 'direct open; Thumb LSL/LSR/CMP/BHI/BLS/PUSH/POP/BX',
            'scope_ja': '命令意味の事前照合。Actionsはこの外部資料を取得しない。'}}


def summaries(a):
    return (f'external2保存28命令/56byteを全u16×2mode={a["exhaustive"]["executed_input_cases"]}入力で検証。'
        '全命令/条件分岐両側を被覆し、返値0/1・r4-r11/LR保持・局所SP差分0・外部call0・非stack書込0をモデル条件付きで確認。'
        '既読ABI/native/候補復元0。エージェント側命令仕様照合: '+REFERENCE+'（Actions中の外部資料取得なし）。',
        '次は未読外部callee0x081138F9の1根だけ限定採取。external2は再採取/単独ABI再実行せず保存結果を再利用する。'
        '旧18owner・外側calleeの帰還/保存slot/返却pointer非alias・Ring通常取得・policy/Circus・P08最終判定は未完。')

if __name__ == '__main__':
    sys.modules.setdefault('pr16_ring_external2_abi', sys.modules[__name__])
    s.run(sys.modules[__name__])
