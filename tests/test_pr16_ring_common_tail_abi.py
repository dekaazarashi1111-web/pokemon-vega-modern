"""共通末尾だけの正負境界。既読ABI/nativeは実行しない。"""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('common_tail_abi_tested', ROOT / 'scripts/pr16_ring_common_tail_abi.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def sample_fixture():
    # 採取JSONのschemaを用いた合成入力。candidate原本の代わりには使用しない。
    nodes = a.expected_nodes()
    return {'schema_version': 1, 'task': 'PR-P08-7-RING-COMMON-TAIL-BYTES',
        'run_id': 35007034033, 'source_head': 'b0fbc529b66f6043ccbcde0d08da8f3678247181',
        'analysis': {'classification': 'COMMON_TAIL_BYTES_NOT_ABI_PROOF',
            'candidate': copy.deepcopy(a.CANDIDATE), 'target': a.TARGET,
            'graph': {'entry': a.TARGET, 'window': 56,
                'window_identity': {'size': 56, 'sha256': '9f4637a8de6ad0f4ad5f8ccd27393d7397b06338db5ec2d227c8043047d4dd33'},
                'nodes': nodes,
                'external_edges': [{'site': 0x0806DE60, 'kind': 'window_fallthrough',
                    'target': a.EXIT, 'resolved_to_code_address_only': True,
                    'stop_reason': 'DEFERRED_UNREAD_ROOT_NOT_DECODED'}],
                'deferred_unread_roots': list(a.OTHER_ROOTS), 'deferred_roots_decoded': 0,
                'memory_write_sites': [], 'side_effects_excluded': False},
            'sampled_ranges': [{'address': at, 'hex': raw, **a.identity(bytes.fromhex(raw))} for at, raw in a.EXPECTED],
            'sampled_instruction_bytes': 12, 'old_unread_targets': list(range(18)),
            'remaining_unread_targets': [*range(18), a.TARGET, *a.OTHER_ROOTS],
            'old_frontier_removed': False, **{k: False for k in a.NO_PROOF}}}


class MachineTests(unittest.TestCase):
    def run_model(self, word=0x02000000, index=0, pointer=a.SAVED_WORD_ADDRESS):
        r = [0x11110000 + k * 0x100 for k in range(16)]
        r[0], r[1] = pointer, index
        self.before = list(r)
        self.memory = {pointer: word}
        return a.execute(a.expected_nodes(), r, self.memory)

    def test_exact_operations(self):
        expected = [('movs', 3, 238), ('lsls', 3, 3, 4), ('adds', 1, 1, 3),
                    ('ldr', 0, 0, 0), ('b', 0x0806DE60), ('adds', 0, 0, 1)]
        self.assertEqual([a.decode(at, bytes.fromhex(h)) for at, h in a.EXPECTED], expected)

    def test_b_displacement_is_pc_plus_four(self):
        self.assertEqual(a.decode(0x0806DE44, b'\x0c\xe0'), ('b', 0x0806DE60))
        self.assertEqual(a.decode(0x100, b'\xfe\xe7'), ('b', 0x100))

    def test_pointer_expression(self):
        self.assertEqual(self.run_model(index=287)['registers'][0], 0x02000fff)

    def test_intermediate_registers(self):
        r = self.run_model(index=287)['registers']
        self.assertEqual((r[1], r[3]), (4095, 3808))

    def test_preserved_registers(self):
        result = self.run_model()['registers']
        for index in [2, *range(4, 15)]:
            self.assertEqual(result[index], self.before[index])

    def test_sp_and_lr_not_restored_or_rewritten(self):
        result = self.run_model()
        self.assertEqual(result['registers'][13:15], self.before[13:15])
        self.assertEqual(result['local_sp_delta'], 0)

    def test_exact_six_instruction_path(self):
        self.assertEqual(self.run_model()['visited'], [0x0806DE3C, 0x0806DE3E, 0x0806DE40, 0x0806DE42, 0x0806DE44, 0x0806DE60])

    def test_stops_before_unread_epilogue(self):
        result = self.run_model()
        self.assertEqual(result['registers'][15], 0x0806DE62)
        self.assertEqual(result['continuation_thumb'], 0x0806DE63)
        self.assertNotIn(0x0806DE62, result['visited'])

    def test_one_word_read_no_write_or_pointer_dereference(self):
        result = self.run_model(word=0xffffffff)
        self.assertEqual(result['word_reads'], [a.SAVED_WORD_ADDRESS])
        self.assertEqual(result['word_writes'], [])
        self.assertEqual(self.memory, {a.SAVED_WORD_ADDRESS: 0xffffffff})

    def test_generic_entry_register_not_assumed_global(self):
        result = self.run_model(pointer=0x02000000, word=5, index=7)
        self.assertEqual(result['registers'][0], 3820)
        self.assertEqual(result['word_reads'], [0x02000000])

    def test_both_additions_wrap_u32(self):
        result = self.run_model(word=0xffffffff, index=0xffffffff)
        self.assertEqual(result['registers'][0], 3806)
        self.assertEqual(result['registers'][1], 3807)

    def test_final_carry(self):
        self.assertEqual(self.run_model(word=0xfffffff0)['nzcv'], [0, 0, 1, 0])

    def test_signed_overflow(self):
        self.assertEqual(self.run_model(word=0x7ffffff0)['nzcv'], [1, 0, 0, 1])

    def test_zero_and_carry(self):
        self.assertEqual(self.run_model(word=(-3808) & a.MASK)['nzcv'], [0, 1, 1, 0])

    def test_negative_without_overflow(self):
        self.assertEqual(self.run_model(word=0x80000000)['nzcv'], [1, 0, 0, 0])

    def test_zero_pointer_result_is_not_return_proof(self):
        result = self.run_model(word=(-3808) & a.MASK)
        self.assertEqual(result['registers'][0], 0)
        self.assertEqual(result['continuation_thumb'], a.EXIT)

    def test_unaligned_word_rejected(self):
        with self.assertRaises(ValueError):
            self.run_model(pointer=a.SAVED_WORD_ADDRESS + 1)

    def test_unprovided_word_rejected(self):
        r = [0] * 16
        r[0] = a.SAVED_WORD_ADDRESS
        with self.assertRaises(ValueError):
            a.execute(a.expected_nodes(), r, {})

    def test_non_u32_word_rejected(self):
        for value in (-1, 1 << 32, True, '0'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_model(word=value)

    def test_non_u32_register_rejected(self):
        for value in (-1, 1 << 32, True, '0'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_model(index=value)

    def test_register_length_rejected(self):
        with self.assertRaises(ValueError):
            a.execute(a.expected_nodes(), [0] * 15, {0: 0})

    def test_invalid_flags_rejected(self):
        with self.assertRaises(ValueError):
            a.execute(a.expected_nodes(), [0] * 16, {0: 0}, (0, 0, 2, 0))

    def test_unknown_or_return_instruction_rejected(self):
        for raw in (b'\x10\xb5', b'\x70\x47', b'\x00\xd0', b'\x01\x20\x00\x00'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                a.decode(0x100, raw)

    def test_extra_unread_instruction_rejected(self):
        nodes = a.expected_nodes() + [{'address': 0x0806DE62, 'hex': '70bd'}]
        with self.assertRaises(ValueError):
            a.execute(nodes, [0] * 16, {0: 0})

    def test_changed_branch_or_instruction_rejected(self):
        for field, value in (('hex', '0de0'), ('target', 0x0806DE62), ('successors', [0x0806DE62])):
            nodes = a.expected_nodes()
            nodes[4][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                a.execute(nodes, [0] * 16, {0: 0})


class SampleBoundaryTests(unittest.TestCase):
    def test_synthetic_schema_valid(self):
        self.assertEqual(a.validate_sample(sample_fixture())['sampled_instruction_bytes'], 12)

    def test_candidate_mismatch(self):
        sample = sample_fixture()
        sample['analysis']['candidate']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            a.validate_sample(sample)

    def test_source_run_mismatch(self):
        for field, value in (('run_id', 1), ('source_head', '0' * 40)):
            sample = sample_fixture()
            sample[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                a.validate_sample(sample)

    def test_each_overclaim_rejected(self):
        for key in a.NO_PROOF:
            sample = sample_fixture()
            sample['analysis'][key] = True
            with self.subTest(key=key), self.assertRaises(ValueError):
                a.validate_sample(sample)

    def test_sample_hash_mismatch(self):
        sample = sample_fixture()
        sample['analysis']['sampled_ranges'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            a.validate_sample(sample)

    def test_window_identity_mismatch(self):
        sample = sample_fixture()
        sample['analysis']['graph']['window_identity']['size'] = 64
        with self.assertRaises(ValueError):
            a.validate_sample(sample)

    def test_extra_root_or_local_store_rejected(self):
        for field, value in (('deferred_roots_decoded', 1), ('memory_write_sites', [0x0806DE42]), ('side_effects_excluded', True)):
            sample = sample_fixture()
            sample['analysis']['graph'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                a.validate_sample(sample)

    def test_instruction_order_and_size_rejected(self):
        sample = sample_fixture()
        sample['analysis']['graph']['nodes'].reverse()
        with self.assertRaises(ValueError):
            a.validate_sample(sample)
        sample = sample_fixture()
        sample['analysis']['sampled_instruction_bytes'] = 14
        with self.assertRaises(ValueError):
            a.validate_sample(sample)

    def test_boundary_target_mismatch(self):
        sample = sample_fixture()
        sample['analysis']['graph']['external_edges'][0]['target'] = 0x0806DE51
        with self.assertRaises(ValueError):
            a.validate_sample(sample)

    def test_old_frontier_drop_rejected(self):
        sample = sample_fixture()
        sample['analysis']['old_unread_targets'].pop()
        with self.assertRaises(ValueError):
            a.validate_sample(sample)


class SavedInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Actionsのexact checkoutにある保存原本。ローカル合成fixtureに置き換えない。
        cls.values = a.inputs()
        cls.analysis = a.analyze(*cls.values)
        cls.report = {'analysis': cls.analysis, 'run_id': 1, 'source_head': a.BASE}

    def test_actual_receipt_and_source_bindings(self):
        self.assertEqual(self.values[0]['run_id'], 35007034033)
        self.assertEqual(a.validate_sample(self.values[0])['graph']['nodes'], a.expected_nodes())

    def test_only_new_tail_cases_covered(self):
        self.assertEqual(self.analysis['verification']['new_tail_low_id_cases'], 11515)
        self.assertEqual(self.analysis['verification']['instructions_covered'], 6)
        for key in ('prior_helper_domain_reexecuted', 'zero_prefix_reexecuted', 'external_callees_executed'):
            self.assertIs(self.analysis['verification'][key], False)

    def test_six_saved_slot_alias_counterexamples(self):
        examples = self.analysis['return_pointer_alias_counterexamples']
        self.assertEqual([e['saved_slot_offset'] for e in examples], [-24, -20, -16, -12, -8, -4])
        for e in examples:
            self.assertEqual(e['computed_pointer'], e['flagset_entry_sp'] + e['saved_slot_offset'])
        self.assertIs(self.analysis['counterexamples_are_hypothetical_not_observed_corruption'], True)

    def test_no_callee_return_or_native_acceptance(self):
        for key in a.NO_PROOF:
            self.assertIs(self.analysis[key], False)
        self.assertEqual(self.analysis['local_pop_or_return_instructions'], 0)
        self.assertEqual(self.analysis['local_sp_delta'], 0)
        self.assertEqual(self.analysis['flagset_entry_sp_offset_at_boundary_under_saved_assumptions'], -24)

    def test_all_frontiers_preserved_next_only_unread_epilogue(self):
        self.assertEqual(self.analysis['remaining_unread_targets'], self.values[0]['analysis']['remaining_unread_targets'])
        self.assertEqual(self.analysis['priority_unread_targets'], [0x0806DE63])
        self.assertEqual(len(self.analysis['old_unread_targets']), 18)

    def test_saved_entry_register_assumption_mismatch(self):
        values = copy.deepcopy(self.values)
        values[1]['analysis']['low_input_scope']['common_boundary_registers_under_preserving_call_assumption']['r1'] = 'id'
        with self.assertRaises(ValueError):
            a.validate_links(*values)

    def test_saved_frame_mismatch(self):
        values = copy.deepcopy(self.values)
        values[2]['analysis']['prefix']['saved_register_slots'][0]['flagset_entry_sp_offset'] = -20
        with self.assertRaises(ValueError):
            a.validate_links(*values)

    def test_projection_does_not_mutate_inputs_or_other_gaps(self):
        state, backlog = a.load(a.STATE), a.load(a.BACKLOG)
        original_state, original_backlog = copy.deepcopy(state), copy.deepcopy(backlog)
        s, b = a.project(state, backlog, self.report)
        self.assertEqual((state, backlog), (original_state, original_backlog))
        row = next(r for r in b['remaining_conditions'] if r['id'] == 'NATURAL_CAPTURE_GEAR')
        self.assertEqual(row.pop('ring_common_tail_abi'), a.REPORT)
        self.assertEqual(b, backlog)
        for key in ('candidate', 'latest_native_run', 'remaining_physical_gap_ids', 'current_checkpoint'):
            self.assertEqual(s[key], state[key])
        bp = copy.deepcopy(s['bp'])
        for key in ('current_stop', 'next_step'):
            bp[key] = state['bp'][key]
        self.assertEqual(bp, state['bp'])

    def test_projection_rejects_ring_overclaim(self):
        report = copy.deepcopy(self.report)
        report['analysis']['ring_acquisition_accepted'] = True
        with self.assertRaises(ValueError):
            a.project(a.load(a.STATE), a.load(a.BACKLOG), report)

    def test_projection_rejects_closed_gap(self):
        state = a.load(a.STATE)
        state['remaining_physical_gap_ids'].remove(a.GAP)
        with self.assertRaises(ValueError):
            a.project(state, a.load(a.BACKLOG), self.report)

    def test_zero_private_or_native_execution(self):
        for key in ('rom_changes', 'candidate_reconstructions', 'new_emulator_processes',
                    'new_graph_decodes', 'prior_abi_classifications_replayed', 'accepted_native_cases_replayed'):
            self.assertEqual(self.analysis[key], 0)


if __name__ == '__main__':
    unittest.main()
