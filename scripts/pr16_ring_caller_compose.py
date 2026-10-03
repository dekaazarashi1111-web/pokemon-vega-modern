#!/usr/bin/env python3
"""保存ABIのcallsite結合とcaller用十分条件。ROM/旧ABI/nativeは実行しない。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = 'ee3760e77cddc9628982115d97ab150de5ba7b5d'
SLUG = 'pr16-ring-caller-compose'
TASK = 'PR-P08-7-RING-CALLER-COMPOSE'
TITLE = '保存external1/2/3とFlagSet callerの結合・経路別frameと非alias十分条件'
SELF = 'scripts/pr16_ring_caller_compose.py'
TEST = 'tests/test_pr16_ring_caller_compose.py'
WORKFLOW = '.github/workflows/pr16-ring-caller-compose.yml'
PRIOR = 'content/modernization/pr16_ring_tail_ci_closeout.json'
REPORT = 'content/modernization/pr16_ring_caller_compose.json'
KEY = 'ring_caller_compose'
MIN_TESTS = 40
EXTRA_CODE = ()
REFERENCE = 'https://github.com/mgba-emu/mgba/blob/master/include/mgba/internal/gba/memory.h'
NO_REPEAT = ('保存external1/2/3とFlagSet callerの契約結合は完了。selector2のexternal3到達域は'
    '560..2047/2080..2303、最大frame44byte。新checkerのfixture PASSは実SP/base/LR/割込み状態の'
    '観測ではない。旧ABI/受入native/本工程同一fixtureを再実行せず、実caller snapshotとallocation/帰還先証拠、'
    '旧18ownerを進める。Ring通常取得は未受入。')
REPORT_HASHES = {
    'frame_join': '279cfedbac150421195f4ae1fbabdda45164032e6a0d3677f5f368450a96ebc4',
    'callee_abi': 'ec45ae731bee3d124e5c7fa1bf9919f4f03520d526af3906e34623da3bf92ac8',
    'helper_abi': '01e1428282d2271d352f8cb1644603d260a496f9e0861c976ed52b2232d2b928',
    'nonzero_abi': 'd9a12d15b936d850bf1a59371bafef92ca8efa718c24bcdae72b516634092d40',
    'zero_abi': '2d6d97fc1998409e2589620589eb3911d92cf979b6e1f3b30418730e5efa0f90',
    'common_tail_abi': 'ed344d342b1599eaf0ea51258fb61e2cf61b0defeed87b26c44fc96ec406e1e4',
    'epilogue_abi': 'a336594a386f5b9f69c2832e35646daad5ff8ca33f2ce4d83a219ed36207f5cc',
    'high_branch_abi': '2e9a6c05f49a16d1dd92a3939876436b8e25dc1ec5012c3b527e25fcbd845e78',
    'external1_abi': '6b85751600d2ac75f64bd24dc725bbd1b197ca4c99203faa1ee06c74f44be3c4',
    'external1_cont_abi': 'fe9fa33b50dece21cac9f2c9f04b5bd37916947d79a4443894198166d7d71be4',
    'external1_exit_abi': '1ee79e8e8305d50af84104dd9984502df656a5c3632c22efa81008ed28baa7c6',
    'external2_abi': '10171fb0872ab4ec7390ba828178c109ba4b0391c93d6f90a87785f49a46880c',
    'external3_abi': 'abb56976a0d74faeabbf3b80b63b58ec58b697ce932193c4593e5c7eb9943acc',
    'external3_body_abi': 'f2677bcd192914fc1f629811d48c470f570361686b96e1ee383be561b7618b0d',
    'external3_tail_abi': 'ffe7d250077f69858d56d331d567ec073484b761e9fa25c952b0b4e7e4d96664',
    'flagset_continuation': 'f42e0ce2a7716e99c01315ea6c8a5e47454437a20956c8836ab0335caba25c97',
    'zero_bytes': '053457495169b5628d8ff3c0c28c8a58e38053ffd66b4bf8547bae2b2cfb5036',
}
SOURCES = tuple('content/modernization/pr16_ring_' + n + '.json' for n in REPORT_HASHES)
FALSE_KEYS = ('callee_return_proven', 'callee_return_observed', 'saved_slot_preservation_proven',
              'return_pointer_non_alias_proven', 'all_runtime_owners_excluded',
              'ring_acquisition_accepted', 'release_ready')
# Normal mappingのcanonical領域だけ。mirror/MMIO/unaligned/非同期を書込安全へ昇格しない。
RAM = ((0x02000000, 0x02040000), (0x03000000, 0x03008000))
COUNT, LIMIT, COUNTER, CAPACITY = 0x0203AF10, 0x03005EDC, 0x0203AF96, 0x03002030
BASE_PTR, SAVE_PTR, SELECTOR, PENDING_ID = 0x0300202C, 0x03005048, 0x03005ED8, 0x030050BC
CONTROLS = ((COUNT, 2), (LIMIT, 2), (COUNTER, 2), (CAPACITY, 2), (BASE_PTR, 4))
CALLS = ((0x0806DDE8, 0x08113889, 0x0806DDED, 16),
         (0x0806DE10, 0x0806DD1D, 0x0806DE15, 4),
         (0x0806DE34, 0x081138F9, 0x0806DE39, 20))


def read_contracts():
    """保存原本のbyte/hashのみ確認。先行analyze/check/executeを呼ばない。"""
    result = {}
    for name, expected in REPORT_HASHES.items():
        path = 'content/modernization/pr16_ring_' + name + '.json'
        raw = (s.ROOT / path).read_bytes()
        s.need(hashlib.sha256(raw).hexdigest() == expected, '保存契約hash差分: ' + name)
        value = s.load(path)
        s.need(value['schema_version'] == 1 and value['analysis']['candidate'] == s.CANDIDATE,
               '保存schema/candidate差分')
        t = value['focused_tests']
        s.need(t['successful'] is True and t['tests_run'] > 0
               and t['failures'] == t['errors'] == t['skips'] == 0, '保存検証未完')
        result[name] = value
    return result


def uint(value, bits, label):
    s.need(type(value) is int and 0 <= value < 1 << bits, label + '範囲/型')
    return value


def interval(address, width, alignment=1):
    """半開区間。canonical通常RAM限定、wrap/mirror/bank跨ぎは拒否。"""
    uint(address, 32, 'address')
    s.need(type(width) is int and width > 0 and alignment in (1, 2, 4)
           and address % alignment == 0, 'width/整列')
    end = address + width
    s.need(any(lo <= address < end <= hi for lo, hi in RAM), '非canonical/wrap/bank跨ぎ')
    return (address, end)


def disjoint(a, b):
    return a[1] <= b[0] or b[1] <= a[0]


def selector2_ranges(false_ranges):
    """保存false区間の低域補集合。旧65536入力分類は再実行しない。"""
    s.need(false_ranges == [[0, 559], [2048, 2079]], 'external2 zero-mode区間差分')
    cursor, result = 1, []
    for first, last in false_ranges:
        if cursor < first:
            result.append([cursor, min(first - 1, 2303)])
        cursor = max(cursor, last + 1)
    if cursor <= 2303:
        result.append([cursor, 2303])
    return result


def route(ident, selector):
    uint(ident, 16, 'id'); uint(selector, 8, 'selector')
    if ident == 0:
        return {'kind': 'zero', 'calls': [], 'peak': 24}
    if 2304 <= ident <= 16383:
        return {'kind': 'helper_nonzero', 'calls': [], 'peak': 24}
    if ident >= 16384:
        return {'kind': 'high', 'calls': [], 'peak': 24}
    if selector == 1:
        return {'kind': 'low_selector1', 'calls': [1], 'peak': 40}
    if selector == 2:
        accepted = any(first <= ident <= last for first, last in selector2_ranges([[0, 559], [2048, 2079]]))
        return {'kind': 'low_selector2_true' if accepted else 'low_selector2_false',
                'calls': [2, 3] if accepted else [2], 'peak': 44 if accepted else 28}
    return {'kind': 'low_other', 'calls': [], 'peak': 24}


def join_contracts(reports):
    """既存報告間の新しいcallsite/frame/値契約結合。保存命令の再decodeはしない。"""
    a = {k: v['analysis'] for k, v in reports.items()}
    f, c, z = a['frame_join'], a['callee_abi'], a['zero_abi']
    s.need(f['inherited_edge']['frame_bytes'] == 8
           and c['prefix']['additional_frame_bytes'] == 16
           and c['prefix']['flagset_entry_sp_offset_before_helper'] == -24
           and z['flagset_entry_sp_offset_at_boundaries'] == -24, '外側frame契約差分')
    s.need(f['call']['bl_return_thumb'] == c['prefix']['callee_entry_lr_value']
           == a['epilogue_abi']['conditional_return_target'] == 0x0806DE81, '外側LR結合差分')
    s.need(a['epilogue_abi']['local_sp_delta'] == 16 and a['epilogue_abi']['r0_preserved'] is True
           and a['nonzero_abi']['saved_return_word_loaded_into_pc'] == 0x0806DE81,
           '外側末尾契約差分')
    s.need(f['conditional_return']['sp_offset'] == 0
           and f['conditional_return']['memory_write_sites'] == [0x0806DE92], 'FlagSet帰還差分')
    graphs = (a['flagset_continuation']['graph'], a['zero_bytes']['graph'])
    nodes = {n['address']: n for g in graphs for n in g['nodes']}
    s.need(nodes[0x0806DE92]['hex'] == '1170'
           and nodes[0x0806DE94]['hex'] == '0020', '保存caller書込/戻り値差分')
    bindings = []
    for i, (site, target, ret, frame) in enumerate(CALLS):
        stored = z['external_calls'][i]
        s.need((stored['site'], stored['target'], stored['return_thumb']) == (site, target, ret),
               'caller callsite差分')
        s.need(nodes[site]['kind'] == 'call' and nodes[site]['size'] == 4
               and nodes[site]['target'] | 1 == target
               and ret == (site + 4) | 1 and ret & ~1 in nodes, 'call/既存continuation不一致')
        bindings.append({'site': site, 'target': target, 'return_thumb': ret,
                         'args': stored['args'], 'entry_sp_offset': -24,
                         'local_frame_bytes': frame, 'deepest_sp_offset': -24-frame,
                         'saved_lr_sp_offset': -28, 'return_sp_offset': -24,
                         'continuation_saved_node': copy.deepcopy(nodes[ret & ~1]),
                         'return_condition': 'valid intact local frame and stable normal mapping; not a native observation'})
    e1, e2, e3 = a['external1_exit_abi'], a['external2_abi'], a['external3_tail_abi']
    s.need(e1['composition']['net_sp_delta_under_composition'] == 0 and e1['r0_preserved'] is True
           and e2['local_sp_delta'] == 0 and e2['local_peak_frame_bytes'] == 4
           and e3['conditional_composition']['net_sp_delta_under_contract'] == 0, 'local帰還結合差分')
    s.need(e3['conditional_composition']['body_tail_r0_is_function_return_value'] is False
           and a['external3_body_abi']['ordered_store_widths'] == [2, 1, 2, 2], 'external3効果差分')
    s.need(a['external1_cont_abi']['counter_write'] == e1['composition']['counter_write'], 'external1 counter差分')
    ranges = selector2_ranges(e2['zero_mode_false_ranges_inclusive'])
    s.need(ranges == [[560, 2047], [2080, 2303]], 'caller入力域結合差分')
    return {'classification': 'CALLSITE_BOUND_CONDITIONAL_FLAGSET_CONTRACT',
        'external_calls': bindings,
        'selector2_external3_id_ranges': ranges,
        'selector2_external3_id_count': sum(hi-lo+1 for lo, hi in ranges),
        'selector2_external3_mode': 1,
        'selector2_external3_header': '0x8000 | id (id <= 2303)',
        'selector2_external3_payload_range': [0, 255],
        'selector2_external3_payload_high_byte': 0,
        'active_prefix_index_max': 65534,
        'counter_after_active_prefix_range': [1, 65535],
        'counter_wrap_possible_under_active_prefix_and_nonalias': False,
        'peak_frame_bytes_by_route': {'zero': 24, 'helper_nonzero': 24, 'high': 24,
            'low_other': 24, 'low_selector1': 40, 'low_selector2_false': 28, 'low_selector2_true': 44},
        'external2_and_external3_frames_are_sequential_not_nested': True,
        'outer_return_thumb': 0x0806DE81,
        'flagset_final_write': {'site': 0x0806DE92, 'width': 1, 'condition': 'returned_pointer != 0',
            'value': 'read8(returned_pointer) | (1 << (id & 7))',
            'live_frame_sp_offsets': [-8, 0], 'retired_callee_frame_sp_offsets': [-24, -8]},
        'flagset_r0_on_conditional_return': 0, 'net_sp_delta_under_contract': 0,
        'external3_r0_after_tail': 0x0806DE39,
        'external3_r0_is_ignored_before_common_pointer_reconstruction': True,
        'old_abi_executed': False, 'native_observation': False}


def check_snapshot(snapshot):
    """明示snapshotの非alias十分条件だけ。実観測/allocated extent証明の代用にはしない。

    peak frameとの非重複はentry値の式を利用するための保守的条件。
    最終STRB時点に生きている保存frameは8byteだけ。拒否はバグ証明ではない。
    """
    s.need(type(snapshot) is dict and snapshot.get('normal_mapping_stable') is True
           and snapshot.get('synchronous') is True, 'memory mapping/同期条件が未提示')
    ident, selector = snapshot['id'], snapshot['selector']
    path = route(ident, selector); sp = uint(snapshot['sp'], 32, 'sp')
    frame = interval(sp - path['peak'], path['peak'], 4)
    lr = uint(snapshot['lr'], 32, 'lr')
    s.need(lr & 1 and 0x08000000 <= (lr & ~1) < 0x0A000000, '未対応LR ISA/code range')
    spans, writes = [], []
    def add(label, at, width, align=1):
        span = interval(at, width, align)
        s.need(disjoint(span, frame), label + ': peak frame alias')
        spans.append((label, span)); return span
    low = 1 <= ident <= 2303
    pointer = 0
    if low:
        add('save_ptr', SAVE_PTR, 4, 4); add('selector', SELECTOR, 1)
        base = uint(snapshot['save_base'], 32, 'save_base')
        interval(base, 1, 4)
        pointer = base + 0xEE0 + (ident >> 3)
        data = add('flag_byte', pointer, 1)
        # PUSH/record/counterによるreload値の変更を除外した式にだけ使用。
        s.need(all(disjoint(data, v) for name, v in spans if name != 'flag_byte'), 'flag/control alias')
    elif ident >= 16384:
        pointer = 0x02037014 + ((ident - 16384) >> 3)
        add('flag_byte', pointer, 1)
    elif ident >= 6400:
        pointer = 0x02036FEC; add('flag_byte', pointer, 1)
    elif ident >= 2304:
        pointer = 0x0203B0E8 + ((ident - 2304) >> 3); add('flag_byte', pointer, 1)
    active, match, record = False, False, None
    if 1 in path['calls'] or 3 in path['calls']:
        for number, (at, width) in enumerate(CONTROLS):
            add('control' + str(number), at, width, width)
        count, limit, index, capacity = (uint(snapshot[k], 16, k) for k in ('count', 'limit', 'index', 'capacity'))
        active = 0 < count < limit and index < capacity
        if active:
            base = uint(snapshot['record_base'], 32, 'record_base')
            interval(base, 1, 4)
            record = base + 4 * index
            span = add('record', record, 4, 4)
            s.need(all(disjoint(span, v) for name, v in spans if name != 'record'), 'record/control/data alias')
            word = uint(snapshot['record_word'], 32, 'record_word')
            if 1 in path['calls']:
                match = (word & 0x7FFF) == ident and ((word >> 15) & 1) == 1
                if match:
                    writes += [{'site': 0x081138E4, 'address': COUNTER, 'width': 2, 'value': index + 1},
                               {'site': 0x0806DE02, 'address': pointer, 'width': 1, 'value': (word >> 16) & 255}]
            else:
                value = uint(snapshot['flag_byte'], 8, 'flag_byte')
                # 保存bodyの4つの書込を順序つきで投影。旧命令は実行しない。
                header = 0x8000 | ident
                writes += [{'site': 0x0811393A, 'address': record, 'width': 2, 'value': (word & 0x8000) | ident},
                           {'site': 0x0811394C, 'address': record+1, 'width': 1, 'value': header >> 8},
                           {'site': 0x08113958, 'address': record+2, 'width': 2, 'value': value},
                           {'site': 0x0811395E, 'address': COUNTER, 'width': 2, 'value': index + 1}]
    if 3 in path['calls']:
        pending = add('pending_id', PENDING_ID, 2, 2)
        s.need(all(disjoint(pending, v) for name, v in spans if name != 'pending_id'), 'pending/control/data alias')
        writes.insert(0, {'site': 0x0806DE1E, 'address': PENDING_ID, 'width': 2, 'value': ident})
    # 保守的な全control/data非alias。実行順で無害なaliasまで拒否することを明示する。
    s.need(all(disjoint(x[1], y[1]) for i, x in enumerate(spans) for y in spans[i+1:]), '入力領域alias')
    if pointer:
        current = (snapshot['record_word'] >> 16) & 255 if match else uint(snapshot['flag_byte'], 8, 'flag_byte')
        writes.append({'site': 0x0806DE92, 'address': pointer, 'width': 1,
                       'value': current | (1 << (ident & 7))})
    return {'scope': 'SUFFICIENT_CONDITIONS_FOR_SUPPLIED_SNAPSHOT_NOT_RUNTIME_EVIDENCE',
        'route': path, 'frame': list(frame), 'active_prefix': active, 'external1_match': match,
        'return_pointer': pointer, 'writes': writes, 'flagset_return_word': lr,
        'flagset_r0': 0, 'sp_after_return': sp, 'frame_disjoint_under_supplied_conditions': True,
        'actual_runtime_inputs_bound': False, 'allocated_storage_extent_proven': False,
        'entry_lr_executability_proven': False, 'ring_acquisition_accepted': False}


def fixture(**changes):
    """独立診断入力。native registerの観測/書換えではない。"""
    value = dict(id=560, selector=2, sp=0x03007F00, lr=0x08101011,
        normal_mapping_stable=True, synchronous=True, save_base=0x02000000,
        record_base=0x02020000, count=1, limit=2, index=0, capacity=2,
        record_word=0, flag_byte=0x24)
    value.update(changes); return value


def analyze(prior, out):
    s.need(prior['task'] == 'PR-P08-7-RING-TAIL-CI-CLOSEOUT' and prior['run_id'] == 35055552309,
           '直前工程identity差分')
    pa = prior['analysis']
    s.need(pa['remaining_unread_targets'] == pa['old_unread_targets']
           and len(pa['old_unread_targets']) == 18, '旧owner台帳差分')
    for key in FALSE_KEYS:
        s.need(pa[key] is False, '旧受入境界差分')
    reports = read_contracts(); joined = join_contracts(reports)
    # 原runの成功を再照合するだけ。compile/ABI分類/native suiteは起動しない。
    verified = []
    for name in ('frame_join', 'zero_abi', 'external1_exit_abi', 'external2_abi', 'external3_tail_abi'):
        r = reports[name]; live = s.api('actions/runs/' + str(r['run_id']))
        s.need(live['head_sha'] == r['source_head'] and live['status'] == 'completed'
               and live['conclusion'] == 'success', '保存契約Actions未成功: ' + name)
        verified.append({'name': name, **{k: live[k] for k in ('id','head_sha','status','conclusion')}})
    return {'classification': 'SAVED_CALLER_COMPOSITION_AND_FAIL_CLOSED_SNAPSHOT_CHECKER',
        'candidate': copy.deepcopy(s.CANDIDATE), 'composition': joined,
        'saved_contract_reports': [{'path': path, 'sha256': REPORT_HASHES[name],
            'run_id': reports[name]['run_id'], 'source_head': reports[name]['source_head'],
            'reexecuted': False} for name, path in zip(REPORT_HASHES, SOURCES)],
        'saved_contract_actions_verified_without_replay': verified,
        'canonical_memory_model': {'ram_half_open': [list(x) for x in RAM],
            'reference': REFERENCE, 'runtime_normal_mapping_confirmed': False,
            'mirrors_mmio_wrap_unaligned_async_rejected': True,
            'sufficient_not_necessary_conditions': True,
            'peak_disjoint_required_for_entry_value_formulas': True},
        'runtime_obligations': ['actual FlagSet entry SP and saved LR bound to the same candidate/caller',
            'live count/limit/index/capacity/base_ptr/save_ptr/selector values and mapping stability',
            'record and save allocation extents; return LR target executability',
            'no asynchronous DMA/IRQ mutation while composing; actual path writes outside live frames',
            'old 18 owner coverage; Ring story supply/cancel/capacity/idempotence/native save/continue'],
        'old_unread_targets': copy.deepcopy(pa['old_unread_targets']),
        'remaining_unread_targets': copy.deepcopy(pa['remaining_unread_targets']),
        'unresolved_indirect_edges': copy.deepcopy(pa['unresolved_indirect_edges']),
        'prior_external_indirect_edges_preserved': copy.deepcopy(pa['prior_external_indirect_edges_preserved']),
        'conditional_call_edges_bound': 3, 'actual_runtime_inputs_bound': False,
        'caller_frame_integrity_discharged': False, 'side_effects_excluded': False,
        **{k: False for k in FALSE_KEYS}, 'rom_changes': 0, 'new_emulator_processes': 0,
        'candidate_reconstructions': 0, 'new_graph_decodes': 0,
        'accepted_native_cases_replayed': 0, 'prior_abi_classifications_replayed': 0}


def summaries(a):
    return ('保存17契約を実callsite3箇所へ結合。selector2到達ID1712件を2区間で導出し、'
        '最大44byte frame・external3 mode1/u8 payload・counter非wrap・FlagSet最終1byte書込を限定検証。'
        'canonical RAM/整列/wrap/alias/未提示同期条件を拒否するsnapshot checkerを実装。'
        'fixtureは実SP/base/LR証拠へ昇格せず、旧ABI/受入native再実行0。'
        '\n- Network補足: RAM境界の設計参考は ' + REFERENCE + ' 。共有runner定型の「外部技術資料なし」は本工程には適用しない。',
        '次は保存caller結合を再利用し、同一candidateの実FlagSet入口SP/LR・record/save/global snapshotと'
        'allocation/帰還先/同期条件をboundした限定証拠をcheckerへ渡す。fixtureでは受入しない。'
        '実caller不明のまま旧18ownerを除外しない。Ring通常取得・policy/Circus・P08最終判定は未完。')


if __name__ == '__main__':
    s.run(sys.modules[__name__])
