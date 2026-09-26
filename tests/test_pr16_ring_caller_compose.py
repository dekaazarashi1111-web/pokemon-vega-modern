"""新caller結合の異常系と十分条件。受入済みnative/先行ABIは実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_caller_compose as task


class ContractJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = task.read_contracts()

    def test_three_callsite_returns_bound_to_saved_nodes(self):
        a = task.join_contracts(self.reports)
        self.assertEqual([x['return_thumb'] for x in a['external_calls']],
                         [0x0806DDED, 0x0806DE15, 0x0806DE39])
        self.assertEqual([x['saved_lr_sp_offset'] for x in a['external_calls']], [-28]*3)

    def test_peak_is_max_not_sum_of_sequential_calls(self):
        a = task.join_contracts(self.reports)
        self.assertEqual(a['peak_frame_bytes_by_route']['low_selector2_true'], 44)
        self.assertTrue(a['external2_and_external3_frames_are_sequential_not_nested'])
        self.assertEqual([x['deepest_sp_offset'] for x in a['external_calls']], [-40, -28, -44])

    def test_external2_intersection_without_exhaustive_replay(self):
        a = task.join_contracts(self.reports)
        self.assertEqual(a['selector2_external3_id_ranges'], [[560, 2047], [2080, 2303]])
        self.assertEqual(a['selector2_external3_id_count'], 1712)

    def test_caller_narrows_external3_payload_and_counter(self):
        a = task.join_contracts(self.reports)
        self.assertEqual(a['selector2_external3_payload_range'], [0, 255])
        self.assertEqual(a['active_prefix_index_max'], 65534)
        self.assertFalse(a['counter_wrap_possible_under_active_prefix_and_nonalias'])
        self.assertEqual(a['external3_r0_after_tail'], 0x0806DE39)
        self.assertTrue(a['external3_r0_is_ignored_before_common_pointer_reconstruction'])

    def test_final_write_lifetime_is_eight_not_twentyfour(self):
        a = task.join_contracts(self.reports)
        self.assertEqual(a['flagset_final_write']['live_frame_sp_offsets'], [-8, 0])
        self.assertEqual(a['flagset_final_write']['retired_callee_frame_sp_offsets'], [-24, -8])
        self.assertEqual(a['flagset_final_write']['width'], 1)
        self.assertEqual(a['flagset_r0_on_conditional_return'], 0)
        self.assertFalse(a['native_observation'])

    def test_wrong_caller_return_is_rejected(self):
        bad = copy.deepcopy(self.reports)
        bad['zero_abi']['analysis']['external_calls'][0]['return_thumb'] += 2
        with self.assertRaises(ValueError): task.join_contracts(bad)

    def test_unknown_continuation_node_is_rejected(self):
        bad = copy.deepcopy(self.reports)
        bad['zero_bytes']['analysis']['graph']['nodes'] = [
            x for x in bad['zero_bytes']['analysis']['graph']['nodes'] if x['address'] != 0x0806DE38]
        with self.assertRaises(ValueError): task.join_contracts(bad)

    def test_changed_local_frame_is_rejected(self):
        bad = copy.deepcopy(self.reports)
        bad['external2_abi']['analysis']['local_peak_frame_bytes'] = 8
        with self.assertRaises(ValueError): task.join_contracts(bad)

    def test_body_r0_must_not_be_called_function_return(self):
        bad = copy.deepcopy(self.reports)
        bad['external3_tail_abi']['analysis']['conditional_composition']['body_tail_r0_is_function_return_value'] = True
        with self.assertRaises(ValueError): task.join_contracts(bad)

    def test_saved_contract_drift_rejected_without_running_prior_code(self):
        with patch.object(task, 'REPORT_HASHES', {'frame_join': '0'*64}):
            with self.assertRaises(ValueError): task.read_contracts()


class RouteAndIntervalTests(unittest.TestCase):
    def test_selector2_boundary_partition(self):
        expected = {1:False, 559:False, 560:True, 2047:True, 2048:False,
                    2079:False, 2080:True, 2303:True}
        for ident, active in expected.items():
            with self.subTest(ident=ident):
                self.assertEqual(3 in task.route(ident, 2)['calls'], active)

    def test_helper_and_high_do_not_inherit_low_selector_calls(self):
        for ident in (0, 2304, 6399, 6400, 16383, 16384, 65535):
            with self.subTest(ident=ident):
                self.assertEqual(task.route(ident, 2)['calls'], [])
                self.assertEqual(task.route(ident, 2)['peak'], 24)

    def test_other_selector_values_do_not_call_externals(self):
        for selector in (0, 3, 255): self.assertEqual(task.route(580, selector)['calls'], [])

    def test_non_u16_id_or_non_u8_selector_rejected(self):
        for ident, selector in ((-1, 0), (65536, 0), (True, 1), (1, -1), (1, 256), (1, True)):
            with self.subTest(ident=ident, selector=selector):
                with self.assertRaises(ValueError): task.route(ident, selector)

    def test_canonical_bank_boundaries_and_adjacency(self):
        self.assertEqual(task.interval(0x0203FFFC, 4, 4), (0x0203FFFC, 0x02040000))
        self.assertEqual(task.interval(0x03007FFF, 1), (0x03007FFF, 0x03008000))
        self.assertTrue(task.disjoint((10, 14), (14, 18)))
        self.assertFalse(task.disjoint((10, 14), (13, 18)))

    def test_mirrors_mmio_wrap_and_misalignment_are_not_linear_ram(self):
        for args in ((0x02040000,1), (0x03008000,1), (0x04000000,1),
                     (0x0203FFFF,2), (0xFFFFFFFF,2), (0x02000001,4,4),
                     (0x02000000,0), (True,1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError): task.interval(*args)

    def test_unknown_external2_ranges_rejected(self):
        with self.assertRaises(ValueError): task.selector2_ranges([[0, 47], [80, 179]])


class SnapshotTests(unittest.TestCase):
    def check(self, **changes):
        return task.check_snapshot(task.fixture(**changes))

    def test_selector2_active_trace_and_flagset_effect(self):
        a = self.check(id=560)
        self.assertEqual(a['frame'], [0x03007ED4, 0x03007F00])
        self.assertEqual([w['width'] for w in a['writes']], [2, 2, 1, 2, 2, 1])
        self.assertEqual([w['site'] for w in a['writes']],
                         [0x0806DE1E, 0x0811393A, 0x0811394C, 0x08113958, 0x0811395E, 0x0806DE92])
        # first STRH preserves the old header bit, later STRB sets mode=1.
        self.assertEqual(a['writes'][1]['value'], 560)
        self.assertEqual(a['writes'][2]['value'], 0x82)
        self.assertEqual(a['writes'][3]['value'], 0x24)
        self.assertEqual(a['writes'][-1]['value'], 0x25)

    def test_selector2_old_header_highbit_and_id_highbyte(self):
        a = self.check(id=2303, record_word=0x8000)
        self.assertEqual(a['writes'][1]['value'], 0x88FF)
        self.assertEqual(a['writes'][2]['value'], 0x88)
        self.assertEqual(a['writes'][-1]['value'], 0xA4)

    def test_selector2_false_does_not_need_record_inputs(self):
        x = task.fixture(id=559)
        for key in ('count','limit','index','capacity','record_base','record_word'): del x[key]
        a = task.check_snapshot(x)
        self.assertEqual(a['route']['peak'], 28)
        self.assertEqual(len(a['writes']), 1)
        self.assertEqual(a['writes'][0]['site'], 0x0806DE92)

    def test_inactive_external3_still_writes_pending_id_and_flag(self):
        for change in ({'count':0}, {'count':2,'limit':2}, {'index':2,'capacity':2}):
            with self.subTest(change=change):
                a = self.check(**change)
                self.assertFalse(a['active_prefix'])
                self.assertEqual([w['site'] for w in a['writes']], [0x0806DE1E, 0x0806DE92])

    def test_selector1_match_copies_payload_then_sets_flag(self):
        a = self.check(id=580, selector=1, record_word=0x12A58244)
        self.assertTrue(a['external1_match'])
        self.assertEqual(a['route']['peak'], 40)
        self.assertEqual([w['site'] for w in a['writes']], [0x081138E4,0x0806DE02,0x0806DE92])
        self.assertEqual([w['value'] for w in a['writes']], [1,0xA5,0xB5])

    def test_selector1_key_or_mode_mismatch_has_no_copy_or_counter(self):
        for word in (580, 0x8245):
            with self.subTest(word=word):
                a = self.check(id=580, selector=1, record_word=word)
                self.assertFalse(a['external1_match'])
                self.assertEqual(len(a['writes']), 1)

    def test_selector1_early_exit_needs_no_record_address(self):
        x = task.fixture(selector=1, count=0)
        del x['record_base']; del x['record_word']
        self.assertFalse(task.check_snapshot(x)['active_prefix'])

    def test_zero_has_no_memory_write_or_global_requirements(self):
        a = task.check_snapshot(dict(id=0,selector=2,sp=0x03007F00,lr=0x08101011,
                                    normal_mapping_stable=True,synchronous=True))
        self.assertEqual(a['writes'], [])
        self.assertEqual(a['return_pointer'], 0)
        self.assertEqual(a['sp_after_return'], 0x03007F00)

    def test_saved_helper_and_high_return_regions_reused(self):
        pairs = ((2304,0x0203B0E8),(6399,0x0203B2E7),(6400,0x02036FEC),
                 (16383,0x02036FEC),(16384,0x02037014),(65535,0x02038813))
        for ident, ptr in pairs:
            with self.subTest(ident=ident): self.assertEqual(self.check(id=ident)['return_pointer'], ptr)

    def test_count_index_upper_boundary_does_not_wrap(self):
        # This explicit record lies at the end of EWRAM, away from globals and save data.
        a = self.check(index=65534,capacity=65535,record_base=0x02000000,save_base=0x03000000)
        self.assertEqual(next(w['value'] for w in a['writes'] if w['site']==0x0811395E),65535)
        self.assertFalse(self.check(index=65535,capacity=65535)['active_prefix'])

    def test_unknown_sync_or_mapping_conditions_rejected(self):
        for key in ('synchronous','normal_mapping_stable'):
            for value in (False, None, 1):
                with self.subTest(key=key,value=value):
                    with self.assertRaises(ValueError): self.check(**{key:value})

    def test_unsupported_lr_is_not_called_executable_return(self):
        for lr in (0x08101010, 0x02010001, 0x0A000001, -1, True):
            with self.subTest(lr=lr):
                with self.assertRaises(ValueError): self.check(lr=lr)
        self.assertFalse(self.check()['entry_lr_executability_proven'])

    def test_stack_wrap_mirror_alignment_and_global_overlap_rejected(self):
        for sp in (20,0x03008004,0x03007F02,task.COUNTER+24,task.PENDING_ID+24):
            with self.subTest(sp=sp):
                with self.assertRaises(ValueError): self.check(sp=sp)

    def test_record_mirror_and_address_wrap_rejected(self):
        for base in (0x02040000,0xFFFFFFFC,0x02020002):
            with self.subTest(base=base):
                with self.assertRaises(ValueError): self.check(record_base=base)

    def test_record_alias_to_frame_rejected(self):
        with self.assertRaises(ValueError): self.check(record_base=0x03007EFC)

    def test_record_alias_to_counter_rejected(self):
        with self.assertRaises(ValueError): self.check(record_base=task.COUNTER-2)

    def test_record_alias_to_base_reload_rejected(self):
        with self.assertRaises(ValueError): self.check(record_base=task.BASE_PTR)

    def test_record_alias_to_save_pointer_rejected(self):
        with self.assertRaises(ValueError): self.check(record_base=task.SAVE_PTR)

    def test_record_alias_to_flag_byte_rejected(self):
        with self.assertRaises(ValueError): self.check(id=576,record_base=0x02000F28)

    def test_flag_byte_alias_to_live_or_retired_frame_rejected_for_entry_formula(self):
        for offset in (-4,-24):
            with self.subTest(offset=offset):
                with self.assertRaises(ValueError):
                    self.check(id=576,save_base=0x03007F00+offset-0xEE0-(576>>3))

    def test_pending_write_cannot_rebind_record_or_save_flag(self):
        with self.assertRaises(ValueError): self.check(record_base=task.PENDING_ID)
        with self.assertRaises(ValueError): self.check(id=576,save_base=task.PENDING_ID-0xEE0-(576>>3))

    def test_payload_overflow_and_boolean_count_rejected(self):
        for changes in ({'flag_byte':256},{'count':True},{'index':65536},{'record_word':1<<32}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError): self.check(**changes)

    def test_snapshot_inputs_not_mutated_or_promoted_to_native(self):
        x = task.fixture(); before = copy.deepcopy(x); a = task.check_snapshot(x)
        self.assertEqual(x, before)
        self.assertFalse(a['actual_runtime_inputs_bound'])
        self.assertFalse(a['ring_acquisition_accepted'])
        self.assertFalse(a['allocated_storage_extent_proven'])


if __name__ == '__main__':
    unittest.main()
