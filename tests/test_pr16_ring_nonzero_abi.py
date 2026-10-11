"""保存された1命令だけのABI検証。既存helper/nativeを再実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_nonzero_abi as a


class NonzeroAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = a.read_inputs()

    def inputs(self):
        return copy.deepcopy(self.saved)

    def reject(self, index, mutate):
        values = self.inputs()
        mutate(values[index]['analysis'])
        with self.assertRaises(ValueError):
            a.analyze(*values)

    def test_scoped_return_and_exact_bytes(self):
        r = a.analyze(*self.inputs())
        self.assertEqual((r['instructions_verified'], r['instruction_bytes_verified']), (1, 2))
        self.assertTrue(r['nonzero_callee_return_proven'])
        self.assertEqual(r['saved_return_word_loaded_into_pc'], 0x0806DE81)
        self.assertEqual(r['return_instruction_address'], 0x0806DE80)

    def test_derived_pop_mask(self):
        self.assertEqual(a.pop_registers(bytes.fromhex('70bd')), [4, 5, 6, 15])
        self.assertEqual(a.pop_registers(bytes.fromhex('01bd')), [0, 15])
        self.assertEqual(a.pop_registers(bytes.fromhex('00bd')), [15])

    def test_non_pop_pc_rejected(self):
        for text in ('', '70', '70bd70bd', 'bd70', '70bc', '70b5', '7047'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                a.pop_registers(bytes.fromhex(text))

    def test_symbolic_load_order_and_no_memory_mutation(self):
        memory = {-24: 'a', -20: 'b', -16: 'c', -12: 'saved_lr', -8: 'outer'}
        before = copy.deepcopy(memory)
        reg = {0: 'pointer', 14: 'live_lr'}
        result, sp, reads = a.symbolic_pop(bytes.fromhex('70bd'), -24, memory, reg)
        self.assertEqual(result, {0: 'pointer', 14: 'live_lr', 4: 'a', 5: 'b', 6: 'c', 15: 'saved_lr'})
        self.assertEqual(sp, -8)
        self.assertEqual([(r['register'], r['flagset_entry_sp_offset'], r['width']) for r in reads],
                         [(4, -24, 4), (5, -20, 4), (6, -16, 4), (15, -12, 4)])
        self.assertEqual(memory, before)
        self.assertEqual(reg, {0: 'pointer', 14: 'live_lr'})

    def test_misaligned_or_missing_stack_rejected(self):
        for sp, memory in ((-23, {}), (-24, {-24: 'a'}), (True, {})):
            with self.subTest(sp=sp), self.assertRaises(ValueError):
                a.symbolic_pop(bytes.fromhex('70bd'), sp, memory, {})

    def test_remaining_outer_frame_not_whole_flagset_return(self):
        r = a.analyze(*self.inputs())
        self.assertEqual((r['flagset_entry_sp_before'], r['flagset_entry_sp_after'], r['callee_entry_sp_after']), (-24, -8, 0))
        self.assertEqual(r['remaining_inherited_frame_bytes'], 8)
        self.assertTrue(r['inherited_saved_slots_unchanged'])
        self.assertFalse(r['inherited_frame_return_verified'])

    def test_lr_not_restored_but_pc_is_saved_lr(self):
        r = a.analyze(*self.inputs())
        self.assertFalse(r['lr_register_restored_from_stack'])
        self.assertEqual(r['lr_register_after'], 0x09097113)
        self.assertNotEqual(r['lr_register_after'], r['saved_return_word_loaded_into_pc'])

    def test_pointer_preserved_without_alias_promotion(self):
        r = a.analyze(*self.inputs())
        self.assertTrue(r['r0_helper_pointer_preserved'])
        self.assertEqual(r['pointer_dereferences'], 0)
        self.assertFalse(r['return_pointer']['non_alias_proven'])
        self.assertEqual(r['return_pointer']['prior_counterexample_preserved'], self.saved[1]['analysis']['return_pointer'])

    def test_all_old_targets_remain(self):
        r = a.analyze(*self.inputs())
        self.assertEqual(r['old_unread_targets'], self.saved[1]['analysis']['old_unread_targets'])
        self.assertEqual(len(r['remaining_unread_targets']), 19)
        self.assertEqual(r['additional_unread_targets'], [a.ZERO])
        self.assertEqual(r['priority_unread_targets'], [a.ZERO])
        self.assertIn(a.TARGET, r['scoped_resolved_additional_targets'])
        self.assertIn(0x09097105, r['remaining_unread_targets'])

    def test_no_acceptance_or_native_overclaim(self):
        r = a.analyze(*self.inputs())
        for k in ('nonzero_callee_return_observed', 'callee_return_proven', 'inherited_frame_return_verified',
                  'stack_integrity_proven', 'all_callers_resolved', 'all_runtime_owners_excluded',
                  'ring_acquisition_accepted', 'release_ready', 'helper_domain_reexecuted'):
            self.assertIs(r[k], False, k)
        for k in ('rom_changes', 'new_emulator_processes', 'candidate_reconstructions', 'new_graph_decodes',
                  'prior_abi_classifications_replayed', 'accepted_native_cases_replayed', 'memory_writes', 'external_calls'):
            self.assertEqual(r[k], 0, k)

    def test_input_immutability(self):
        values = self.inputs(); before = copy.deepcopy(values)
        r = a.analyze(*values)
        r['old_unread_targets'].clear()
        r['return_pointer']['prior_counterexample_preserved'].clear()
        self.assertEqual(values, before)

    def test_candidate_mutation(self):
        for i in range(3):
            with self.subTest(i=i):
                self.reject(i, lambda v: v['candidate'].update(size=1))

    def test_scope_mutation(self):
        for i in range(3):
            with self.subTest(i=i):
                self.reject(i, lambda v: v.update(classification='NATIVE_ACCEPTANCE'))

    def test_prior_acceptance_mutation(self):
        for key in ('old_frontier_removed', 'callee_return_proven', 'stack_integrity_proven',
                    'all_callers_resolved', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
            for i in range(3):
                with self.subTest(key=key, i=i):
                    self.reject(i, lambda v, key=key: v.update({key: True}))

    def test_frontier_mutation(self):
        self.reject(0, lambda v: v['old_unread_targets'].pop())
        self.reject(1, lambda v: v.update(additional_unread_targets=[a.TARGET]))
        self.reject(1, lambda v: v.update(priority_unread_targets=[a.ZERO]))
        self.reject(0, lambda v: v.update(priority_unread_targets=[a.ZERO]))

    def test_target_mutation(self):
        for i in range(3):
            with self.subTest(i=i):
                self.reject(i, lambda v: v.update(target=a.ZERO))

    def test_graph_boundary_mutation(self):
        for change in ({'entry': a.ZERO}, {'window': 1024}, {'side_effects_excluded': True}):
            with self.subTest(change=change):
                self.reject(0, lambda v, change=change: v['graph'].update(change))

    def test_extra_instruction_or_edge(self):
        self.reject(0, lambda v: v['graph']['nodes'].append(copy.deepcopy(v['graph']['nodes'][0])))
        self.reject(0, lambda v: v['graph']['external_edges'].append({'target': a.ZERO}))
        self.reject(0, lambda v: v['graph']['memory_write_sites'].append(a.TARGET & ~1))

    def test_instruction_metadata_mutations(self):
        for change in ({'hex': 'f0bd'}, {'size': 4}, {'kind': 'indirect'}, {'memory_write': True},
                       {'address': a.TARGET}, {'successors': [a.ZERO]}, {'literal_address': 1}):
            with self.subTest(change=change):
                self.reject(0, lambda v, change=change: v['graph']['nodes'][0].update(change))

    def test_sample_identity_mutations(self):
        self.reject(0, lambda v: v.update(sampled_instruction_bytes=14))
        for change in ({'hex': '70bc'}, {'size': 14}, {'sha256': '0'*64}, {'address': a.TARGET}):
            with self.subTest(change=change):
                self.reject(0, lambda v, change=change: v['sampled_ranges'][0].update(change))

    def test_helper_preservation_required(self):
        for key in ('helper_return_proven', 'helper_sp_preserved', 'helper_r4_r11_preserved',
                    'helper_lr_preserved', 'helper_memory_unchanged', 'helper_saved_slots_unchanged'):
            with self.subTest(key=key):
                self.reject(1, lambda v, key=key: v.update({key: False}))

    def test_helper_no_call_stack_and_observation_boundary(self):
        self.reject(1, lambda v: v.update(helper_stack_operations=1))
        self.reject(1, lambda v: v.update(helper_external_calls=1))
        self.reject(1, lambda v: v.update(helper_return_observed=True))

    def test_helper_return_address_binding(self):
        self.reject(1, lambda v: v['verification'].update(return_thumb=a.RETURN))
        self.reject(2, lambda v: v['helper'].update(bl_return_thumb=a.RETURN))
        self.reject(2, lambda v: v['helper'].update(target=a.TARGET))

    def test_exit_condition_must_match_both_reports(self):
        for index, key, val in ((0, 'target', a.ZERO), (0, 'condition', 'unconditional'),
                                (0, 'site', 0x09097116), (1, 'target', a.TARGET)):
            values = self.inputs()
            for r, k in ((values[1], 'conditional_exits_reused'), (values[2], 'conditional_exits')):
                r['analysis'][k][index][key] = val
            with self.subTest(index=index, key=key), self.assertRaises(ValueError):
                a.analyze(*values)

    def test_saved_register_and_offset_layout(self):
        for change in ({'register': 7}, {'flagset_entry_sp_offset': -8}, {'callee_entry_sp_offset': 0}):
            values = self.inputs()
            for frame in (values[1]['analysis']['caller_frame_after_helper'], values[2]['analysis']['prefix']):
                frame['saved_register_slots'][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                a.analyze(*values)

    def test_sp_premises(self):
        for key in ('additional_frame_bytes', 'total_flagset_frame_bytes',
                    'callee_entry_sp_offset_before_helper', 'flagset_entry_sp_offset_before_helper'):
            with self.subTest(key=key):
                self.reject(2, lambda v, key=key: v['prefix'].update({key: 0}))
        self.reject(1, lambda v: v['caller_frame_after_helper'].update(flagset_entry_sp_offset=-8))

    def test_outer_frame_and_saved_lr(self):
        self.reject(2, lambda v: v['prefix'].update(inherited_flagset_saved_offsets=[]))
        self.reject(1, lambda v: v['caller_frame_after_helper'].update(inherited_flagset_saved_offsets=[]))
        self.reject(2, lambda v: v['prefix'].update(local_push_does_not_overlap_inherited_slots=False))
        self.reject(2, lambda v: v['prefix'].update(callee_entry_lr_value=0x09097113))


if __name__ == '__main__':
    unittest.main()
