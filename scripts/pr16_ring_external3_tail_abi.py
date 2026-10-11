#!/usr/bin/env python3
"""保存末尾3命令とprefix/body契約だけを結合。ROM・先行ABIは実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = '974726060048d3700ecccc77b78a4d78d9cf4649'
SLUG = 'pr16-ring-external3-tail-abi'
TASK = 'PR-P08-7-RING-EXTERNAL3-TAIL-ABI'
TITLE = 'external3保存末尾の帰還ABI・条件付き合成とframe破壊反例を検証'
SELF = 'scripts/pr16_ring_external3_tail_abi.py'
TEST = 'tests/test_pr16_ring_external3_tail_abi.py'
WORKFLOW = '.github/workflows/pr16-ring-external3-tail-abi.yml'
PRIOR = 'content/modernization/pr16_ring_external3_tail_bytes.json'
PREFIX = 'content/modernization/pr16_ring_external3_abi.json'
BODY = 'content/modernization/pr16_ring_external3_body_abi.json'
REPORT = 'content/modernization/pr16_ring_external3_tail_abi.json'
KEY = 'ring_external3_tail_abi'
SOURCES = (PREFIX, BODY)
EXTRA_CODE = ()
MIN_TESTS = 43
START, BODY_START, MASK = 0x08113960, 0x08113938, 0xffffffff
CODE = ('f0bc', '01bc', '0047')
FALSE_KEYS = ('callee_return_proven', 'callee_return_observed',
              'saved_slot_preservation_proven', 'return_pointer_non_alias_proven',
              'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready')
NO_REPEAT = ('external3末尾3命令/6byteと保存prefix/bodyの条件付き帰還合成は完了。'
    '末尾r0は保存LRで上書きされbodyのindex+1ではない。160単一bit破壊診断はnative観測ではない。'
    '同一入力の末尾再採取・先行ABI/BP再実行を避け、callerの実frame/record/global非aliasと旧18ownerだけを進める。')


def boundary_flags(a):
    for key in FALSE_KEYS:
        s.need(a[key] is False, '過大受入: ' + key)


def program(prior):
    s.need(prior['schema_version'] == 1 and prior['task'] == 'PR-P08-7-RING-EXTERNAL3-TAIL-BYTES', '先行schema/task差分')
    a = prior['analysis']; g = a['graph']
    s.need(a['candidate'] == s.CANDIDATE and a['target'] == a['next_saved_abi_target'] == START | 1, 'candidate/target差分')
    s.need(g['entry'] == START | 1 and g['window'] == 64 and g['window_identity'] == {
        'size': 64, 'sha256': 'cde9e48c9c4dcaf0f1a01a8ec14c28e4bde194c9cfce2f2f4e15b2c6b09615e9'}, '保存window差分')
    nodes = [dict(address=START+2*i, size=2, hex=h, kind='ordinary', memory_write=False,
                  successors=[START+2*i+2]) for i,h in enumerate(CODE[:2])]
    nodes.append(dict(address=START+4, size=2, hex=CODE[2], kind='indirect', register=0,
                      memory_write=False, successors=[]))
    edge = dict(site=START+4, kind='indirect', register=0, target=None)
    ranges = [dict(address=START+2*i, hex=h, **s.identity(bytes.fromhex(h))) for i,h in enumerate(CODE)]
    s.need(g['nodes'] == nodes and g['external_edges'] == [edge] and not g['memory_write_sites'], '命令/辺/書込差分')
    s.need(a['sampled_ranges'] == ranges and a['sampled_instruction_bytes'] == 6, '保存byte/hash差分')
    old = a['old_unread_targets']
    s.need(len(old) == len(set(old)) == 18 and START | 1 not in old
           and a['remaining_unread_targets'] == sorted(old) and g['deferred_unread_roots'] == sorted(old), '未読owner差分')
    s.need(g['deferred_roots_decoded'] == g['saved_instruction_bytes_redecoded'] == 0, '既読再decode')
    s.need(a['old_frontier_removed'] is False and not a['new_unread_targets']
           and not a['known_sampled_boundary_targets'] and a['unresolved_indirect_edges'] == [edge], '境界欠落')
    s.need(a['side_effects_excluded'] is False and g['side_effects_excluded'] is False, '副作用過大判定')
    boundary_flags(a)
    return a


def execute(registers, memory):
    """通常の整列memory上のPOP/POP/BXのみ。分岐先・bus alias・命令fetchは実行しない。"""
    s.need(len(registers) == 16 and all(type(v) is int and 0 <= v <= MASK for v in registers), 'register範囲')
    s.need(all(type(a) is int and 0 <= a <= MASK and type(v) is int and 0 <= v < 256
               for a,v in memory.items()), 'memory範囲')
    r = list(registers); before_sp = r[13]; reads = []
    s.need(before_sp % 4 == 0 and before_sp <= MASK-20, 'frame整列/overflow')
    for i,hx in enumerate(CODE):
        h = int.from_bytes(bytes.fromhex(hx), 'little'); at = START+2*i
        if h & 0xff00 == 0xbc00:
            for reg in range(8):
                if not h & (1 << reg):
                    continue
                addr = r[13]
                s.need(all(addr+j in memory for j in range(4)), '未提供保存slot')
                r[reg] = int.from_bytes(bytes(memory[addr+j] for j in range(4)), 'little')
                reads.append(dict(site=at, address=addr, register=reg, value=r[reg]))
                r[13] += 4
        else:
            s.need(h == 0x4700, '未対応末尾命令')
    word = r[0]; thumb = bool(word & 1)
    aligned = thumb or word % 4 == 0
    return {'registers_before_branch': r, 'reads': reads, 'sp_delta': r[13]-before_sp,
            'branch_word': word, 'branch_address': word & ~1 if aligned else None,
            'instruction_set': 'THUMB' if thumb else 'ARM', 'target_alignment_valid': aligned,
            'target_executability_proven': False, 'branch_target_executed': False,
            'memory_unchanged': True, 'local_memory_writes': 0}


def snapshot(words=(0x11111111,0x22222222,0x33333333,0x44444444,0x08101011), sp=0x03007eec):
    """末尾だけの独立診断入力。実callerやprefix到達を仮装しない。"""
    s.need(len(words) == 5 and all(type(w) is int and 0 <= w <= MASK for w in words), 'slot範囲')
    r = [0x500+i for i in range(16)]; r[13] = sp
    mem = {sp+4*i+j:b for i,w in enumerate(words) for j,b in enumerate(w.to_bytes(4,'little'))}
    return r, mem


def diagnostics():
    r, mem = snapshot(); original = execute(r, mem); changes = 0
    for byte in range(20):
        for bit in range(8):
            changed = dict(mem); changed[r[13]+byte] ^= 1 << bit
            result = execute(r, changed); dest = (4,5,6,7,0)[byte//4]
            expected = original['registers_before_branch'][dest] ^ (1 << (8*(byte%4)+bit))
            s.need(result['registers_before_branch'][dest] == expected and result['sp_delta'] == 20,
                   'slot破壊が帰還契約へ反映されない')
            for other in (0,4,5,6,7):
                if other != dest:
                    s.need(result['registers_before_branch'][other] == original['registers_before_branch'][other], '別slot汚染')
            changes += 1
    corrupt = dict(mem)
    corrupt.update({r[13]+16:0x21, r[13]+17:0x22})
    altered = execute(r, corrupt)
    return {'single_bit_frame_corruption_cases': changes, 'frame_bytes_covered': 20,
            'native_observation': False, 'prefix_or_body_executed': False,
            'saved_lr_halfword_corruption': {'original_branch_word': original['branch_word'],
                'changed_branch_word': altered['branch_word'], 'observed': False},
            'local_register_seed_is_fixture_not_runtime_evidence': True}


def join(prefix_report, body_report, tail):
    s.need(prefix_report['task'] == 'PR-P08-7-RING-EXTERNAL3-ABI'
           and body_report['task'] == 'PR-P08-7-RING-EXTERNAL3-BODY-ABI', '保存ABI task差分')
    p, b = prefix_report['analysis'], body_report['analysis']
    for a in (p,b):
        s.need(a['candidate'] == s.CANDIDATE and set(a['old_unread_targets']) == set(tail['old_unread_targets']), '保存ABI candidate/旧owner差分')
        boundary_flags(a)
    s.need(p['local_sp_delta'] == -20 and p['frame_bytes_live'] == 20
           and p['saved_register_order'] == [4,5,6,7,14] and p['external_calls'] == 0
           and p['local_explicit_nonstack_stores'] == 0, 'prefix frame差分')
    s.need(p['early_exit_target'] == START | 1 and p['early_exit_is_return_proven'] is False
           and p['return_value_proven'] is False, 'prefix帰還境界差分')
    s.need(b['inherited_frame_bytes_live'] == 20 and b['local_sp_delta'] == 0
           and b['next_unread_return_target'] == START | 1 and b['saved_prefix_reused_not_executed'] is True
           and b['inherited_contract'] == p['continuation_contract']
           and b['inherited_contract']['target'] == BODY_START | 1, 'body結合差分')
    s.need(b['ordered_store_widths'] == [2,1,2,2]
           and b['ordered_store_sites'] == [BODY_START+o for o in (2,20,32,38)]
           and b['non_alias_formula']['valid_without_alias_preconditions'] is False, '書込契約差分')
    s.need(p['prior_external_indirect_edges_preserved'] == b['prior_external_indirect_edges_preserved']
           == tail['prior_external_indirect_edges_preserved'], '先行間接辺欠落')
    s.need(p['hypothetical_stack_overwrites_counter']['observed'] is False
           and b['alias_diagnostics']['native_observation'] is False, '仮想診断の観測化')
    return {'classification': 'CONDITIONAL_RETURN_ONLY_WITH_VALID_INTACT_SAVED_FRAME',
        'saved_prefix_reused_not_executed': True, 'saved_body_reused_not_executed': True,
        'paths': ['saved_prefix_early_exit_to_tail', 'saved_prefix_body_fallthrough_to_tail'],
        'entry_sp_symbol': 'S', 'tail_entry_sp': 'S - 20', 'sp_after_tail': 'S',
        'local_sp_deltas': [-20,0,20], 'net_sp_delta_under_contract': 0,
        'restored_registers_under_frame_integrity': [4,5,6,7],
        'r0_after_tail': 'word[S - 4]; entry LR only if saved frame is intact',
        'branch_word_after_tail': 'word[S - 4]', 'body_tail_r0_is_function_return_value': False,
        'body_tail_r0_before_pop': b['non_alias_formula']['tail_r0'],
        'continuation_condition': p['continuation_condition'],
        'continuation_side_effects': {'ordered_store_widths': b['ordered_store_widths'],
            'reload_order': b['reload_order'], 'non_alias_formula': b['non_alias_formula'],
            'scope': 'SAVED_BODY_CONTRACT_BEFORE_TAIL_NOT_REEXECUTED'},
        'proof_obligations_ja': [
            'S-20..S-1が整列済みで読取可能な通常memoryで、保存r4-r7/LRがPUSH時のままである。',
            'bodyの全書込（再読取後の実addressとcounter書込を含む）が保存frameを破壊しない。',
            '保存LRがcallerの正しい戻り先で、instruction-set/整列/実行可能性が妥当である。',
            'entry値への式にはPUSH/frameとrecord/global入力の非aliasが別途必要。loaded値はPUSH後。',
            '単一record式にはcounter/base pointer非aliasが必要。数値address非重複だけではbus mirror非aliasを証明しない。'],
        'caller_frame_integrity_discharged': False, 'native_return_accepted': False}


def analyze(prior, out):
    a = program(prior); composition = join(s.load(PREFIX), s.load(BODY), a)
    result = {'classification': 'SAVED_EXTERNAL3_TAIL_ABI_AND_CONDITIONAL_PREFIX_BODY_COMPOSITION',
        'candidate': copy.deepcopy(s.CANDIDATE), 'instructions_verified': 3, 'instruction_bytes_verified': 6,
        'local_sp_delta': 20, 'inherited_frame_bytes_consumed': 20,
        'local_memory_writes': 0, 'tail_unchanged_registers_before_branch': [1,2,3,8,9,10,11,12,14],
        'conditional_composition': composition, 'diagnostics': diagnostics(),
        'old_unread_targets': a['old_unread_targets'], 'remaining_unread_targets': a['remaining_unread_targets'],
        'priority_unread_targets': [], 'next_saved_abi_target': None,
        'unresolved_indirect_edges': copy.deepcopy(a['unresolved_indirect_edges']),
        'conditional_tail_edge': {'site': START+4, 'register': 0,
            'expression': 'word[tail_entry_sp + 16]', 'entry_lr_requires_intact_saved_frame': True,
            'unconditional_target_resolved': False},
        'prior_external_indirect_edges_preserved': copy.deepcopy(a['prior_external_indirect_edges_preserved']),
        **{key: False for key in FALSE_KEYS}, 'side_effects_excluded': False,
        'rom_changes': 0, 'new_emulator_processes': 0, 'candidate_reconstructions': 0,
        'new_graph_decodes': 0, 'accepted_native_cases_replayed': 0, 'prior_abi_classifications_replayed': 0}
    return copy.deepcopy(result)


def summaries(a):
    return ('external3保存末尾3命令/6byteのPOP/POP/BX、SP+20、r4-r7復元と保存LR→r0→分岐を検証。'
        '保存prefix/bodyを条件付き合成し、保存frame160単一bit破壊反例を検証。ROM復元・既読ABI・BP再実行0。',
        '次は保存したexternal1/2/3契約と外側callerを結び、実frame/record/global非alias・帰還先条件を限定検証する。'
        '末尾byte/ABIと受入BPを再実行しない。旧18未読ownerを保持し、Ring通常取得・policy/Circus・P08最終判定は未完。')


if __name__ == '__main__':
    s.run(sys.modules[__name__])
