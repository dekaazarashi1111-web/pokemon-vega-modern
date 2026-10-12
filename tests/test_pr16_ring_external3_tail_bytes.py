"""未読末尾の採取scopeと保存境界を検証。候補の復元はmockする。"""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_external3_tail_bytes as m

class External3TailCollection(unittest.TestCase):
    def setUp(self): self.prior = m.s.load(m.PRIOR)
    def test_saved_prior_contract(self):
        self.assertEqual(m.validate_prior(self.prior)['priority_unread_targets'][0], m.TARGET)
    def test_candidate_drift(self):
        self.prior['analysis']['candidate']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): m.validate_prior(self.prior)
    def test_wrong_task(self):
        self.prior['task'] = 'wrong'
        with self.assertRaises(ValueError): m.validate_prior(self.prior)
    def test_wrong_priority(self):
        self.prior['analysis']['priority_unread_targets'][0] = 0x0806DD1D
        with self.assertRaises(ValueError): m.validate_prior(self.prior)
    def test_old_owner_cannot_disappear(self):
        self.prior['analysis']['remaining_unread_targets'].remove(self.prior['analysis']['old_unread_targets'][0])
        with self.assertRaises(ValueError): m.validate_prior(self.prior)
    def test_target_must_be_unread(self):
        self.prior['analysis']['remaining_unread_targets'].remove(m.TARGET)
        with self.assertRaises(ValueError): m.validate_prior(self.prior)
    def test_no_acceptance_promotion(self):
        for key in ('callee_return_proven', 'callee_return_observed', 'saved_slot_preservation_proven',
                    'return_pointer_non_alias_proven', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
            value = copy.deepcopy(self.prior); value['analysis'][key] = True
            with self.assertRaises(ValueError): m.validate_prior(value)
    def test_live_frame_preserved(self):
        self.prior['analysis']['inherited_frame_bytes_live'] = 0
        with self.assertRaises(ValueError): m.validate_prior(self.prior)
    def test_diagnostic_not_observation(self):
        self.prior['analysis']['alias_diagnostics']['native_observation'] = True
        with self.assertRaises(ValueError): m.validate_prior(self.prior)
    def test_new_edge_old_frontier(self):
        a = self.prior['analysis']; target = 0x08001235
        r = m.frontier(a, {'external_edges': [{'target': target}]}, set())
        self.assertIn(target, r['new_unread_targets'])
        self.assertTrue(set(a['old_unread_targets']) <= set(r['remaining_unread_targets']))
        self.assertNotIn(m.TARGET, r['remaining_unread_targets'])
    def test_saved_edge_not_reopened(self):
        target = 0x081138F1
        r = m.frontier(self.prior['analysis'], {'external_edges': [{'target': target}]}, {target})
        self.assertEqual(r['known_sampled_boundary_targets'], [target]);self.assertNotIn(target, r['remaining_unread_targets'])
    def test_indirect_edge_retained(self):
        edge = {'site': m.TARGET & ~1, 'kind': 'indirect', 'register': 1, 'target': None}
        r = m.frontier(self.prior['analysis'], {'external_edges': [edge]}, set())
        self.assertEqual(r['unresolved_indirect_edges'], [edge])
    def graph(self):
        return {'entry': m.TARGET, 'nodes': [{'address': m.TARGET & ~1, 'size': 2}],
            'external_edges': [], 'saved_instruction_bytes_redecoded': 0, 'deferred_roots_decoded': 0}
    def test_single_sampler_no_prior_execution(self):
        with patch.object(m.sampler, 'collect', return_value=(self.graph(), [])) as collect:
            result = m.analyze(copy.deepcopy(self.prior), Path('.local/not-used'))
        self.assertEqual(collect.call_count, 1);self.assertEqual(collect.call_args.args[0], m.TARGET)
        self.assertEqual(set(collect.call_args.args[1]), set(self.prior['analysis']['old_unread_targets']))
        self.assertIn(m.previous.REPORT, collect.call_args.args[2])
        self.assertEqual(result['candidate_reconstructions'], 1);self.assertEqual(result['prior_abi_classifications_replayed'], 0)
        self.assertFalse(result['side_effects_excluded'])
        self.assertEqual(result['prior_external_indirect_edges_preserved'], self.prior['analysis']['prior_external_indirect_edges_preserved'] + self.prior['analysis']['unresolved_indirect_edges'])
    def test_redecoded_scope_rejected(self):
        graph = self.graph(); graph['saved_instruction_bytes_redecoded'] = 2
        with patch.object(m.sampler, 'collect', return_value=(graph, [])):
            with self.assertRaises(ValueError): m.analyze(self.prior, Path('.local/not-used'))

if __name__ == '__main__': unittest.main()
