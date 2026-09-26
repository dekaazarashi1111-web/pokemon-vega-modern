"""保存prefixから未読帰還を捏造しないための限定ABI回帰。"""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_callee_abi as m


class CalleeAbiTests(unittest.TestCase):
    def setUp(self):
        self.sample = json.loads((ROOT / m.SAMPLE).read_bytes())
        self.frame = json.loads((ROOT / m.FRAME).read_bytes())

    def reject(self, change):
        change(self.sample['analysis'])
        with self.assertRaises(ValueError):
            m.analyze(self.sample, self.frame)

    def test_live_frame_not_return(self):
        r = m.analyze(self.sample, self.frame)
        self.assertEqual(r['prefix']['additional_frame_bytes'], 16)
        self.assertEqual(r['prefix']['total_flagset_frame_bytes'], 24)
        self.assertEqual(r['prefix']['saved_register_slots'][-1],
            {'register': 14, 'callee_entry_sp_offset': -4, 'flagset_entry_sp_offset': -12})
        self.assertTrue(r['prefix']['local_push_does_not_overlap_inherited_slots'])
        self.assertEqual(r['prefix']['sampled_return_instructions'], 0)
        for k in ('callee_return_proven', 'callee_sp_restored', 'callee_r4_restored',
                  'stack_integrity_proven', 'inherited_frame_return_verified',
                  'all_callers_resolved', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
            self.assertIs(r[k], False)

    def test_code_pointer_not_data_pointer(self):
        r = m.analyze(self.sample, self.frame)
        self.assertEqual(r['conditional_exits'][1]['target'], m.ZERO)
        self.assertIn('not returned data pointer', r['conditional_exits'][1]['r0_role'])
        self.assertIs(r['return_pointer']['established'], False)
        self.assertIs(r['return_pointer']['non_alias_proven'], False)

    def test_three_unread_boundaries_old_ledger_unchanged(self):
        before = copy.deepcopy(self.sample)
        r = m.analyze(self.sample, self.frame)
        self.assertEqual(r['additional_unread_targets'], sorted([m.HELPER, m.NONZERO, m.ZERO]))
        self.assertEqual(r['priority_unread_targets'], [m.HELPER])
        self.assertEqual(r['old_unread_targets'], self.sample['analysis']['old_unread_targets'])
        self.assertEqual(len(r['remaining_unread_targets']), 21)
        self.assertEqual(before, self.sample)

    def test_uint16_normalization_all_low_bits(self):
        for value in range(65536):
            for high in (0, 0xabcd0000, 0xffff0000):
                r = m.normalize_argument(high | value)
                self.assertEqual(r, {'r0': value, 'r4': value, 'r5': value << 16, 'r6': value})

    def test_argument_domain_rejected(self):
        for value in (-1, 1 << 32, True, '1'):
            with self.assertRaises(ValueError):
                m.normalize_argument(value)

    def test_bad_candidate(self):
        self.reject(lambda a: a['candidate'].update(crc32='00000000'))

    def test_wrong_root(self):
        self.reject(lambda a: a.update(target=m.TARGET + 2))

    def test_saved_frame_cannot_shrink(self):
        self.frame['analysis']['inherited_edge']['frame_bytes'] = 4
        with self.assertRaises(ValueError):
            m.analyze(self.sample, self.frame)

    def test_prior_return_cannot_be_promoted(self):
        self.frame['analysis']['call']['callee_return_proven'] = True
        with self.assertRaises(ValueError):
            m.analyze(self.sample, self.frame)

    def test_old_target_not_removed(self):
        self.reject(lambda a: a['old_unread_targets'].remove(m.TARGET))

    def test_sample_acceptance_rejected(self):
        for key in ('callee_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
                    'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready', 'old_frontier_removed'):
            with self.subTest(key=key):
                s = copy.deepcopy(self.sample)
                s['analysis'][key] = True
                with self.assertRaises(ValueError):
                    m.analyze(s, self.frame)

    def test_sample_hash_drift(self):
        self.reject(lambda a: a['sampled_ranges'][0].update(sha256='0' * 64))

    def test_extra_sample_rejected(self):
        self.reject(lambda a: a['sampled_ranges'].append(copy.deepcopy(a['sampled_ranges'][0])))

    def test_missing_sample_rejected(self):
        self.reject(lambda a: a['sampled_ranges'].pop())

    def test_push_mutation_even_when_rehashed(self):
        def change(a):
            a['graph']['nodes'][0]['hex'] = '10b5'
            s = a['sampled_ranges'][0]
            s['hex'] = '10b5'
            s.update(m.identity(bytes.fromhex(s['hex'])))
        self.reject(change)

    def test_branch_target_mutation(self):
        self.reject(lambda a: a['graph']['nodes'][7].update(target=m.NONZERO + 2))

    def test_branch_missing_boundary(self):
        self.reject(lambda a: a['graph']['external_edges'].pop(1))

    def test_false_fallthrough_return(self):
        self.reject(lambda a: a['graph']['nodes'][-1].update(kind='return'))

    def test_helper_target_mutation(self):
        self.reject(lambda a: a['graph']['nodes'][5].update(target=m.HELPER + 2))

    def test_literal_mutation(self):
        self.reject(lambda a: a['graph']['nodes'][8].update(literal_value=m.ZERO + 2))

    def test_cfg_mutation(self):
        self.reject(lambda a: a['graph']['nodes'][7]['successors'].append(m.NONZERO & ~1))

    def test_memory_write_suppressed(self):
        self.reject(lambda a: a['graph']['nodes'][0].update(memory_write=False))

    def test_old_sample_not_reexecuted(self):
        r = m.analyze(self.sample, self.frame)
        for key in ('rom_changes', 'new_emulator_processes', 'candidate_reconstructions',
                    'new_graph_decodes', 'prior_abi_classifications_replayed', 'accepted_native_cases_replayed'):
            self.assertEqual(r[key], 0)


if __name__ == '__main__':
    unittest.main()
