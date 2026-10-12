"""保存済み実graphを使う限定結合の正常系・改竄拒否。旧collector/15辺分類は呼ばない。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_frame_join as j


class FrameJoinTests(unittest.TestCase):
    def setUp(self):
        self.values = [json.loads((ROOT / p).read_bytes()) for p in
                       (j.saved.REPORT, j.saved.ABI, j.saved.PATCH, j.saved.PRIOR)]

    def analyze(self):
        return j.analyze(*self.values)

    def graph(self):
        return self.values[0]['analysis']['graph']

    def cached(self, entry):
        return next(g for g in self.values[2]['frontier']['graphs'] if g['entry'] == entry)

    def test_real_saved_join_is_conditional(self):
        r = self.analyze()
        self.assertEqual(r['call']['entry'], 0x0806DDB5)
        self.assertEqual(r['call']['unread_callee'], 0x09097105)
        self.assertEqual(r['call']['bl_return_thumb'], 0x0806DE81)
        self.assertEqual(r['conditional_return']['site'], 0x0806DE9A)
        self.assertTrue(r['conditional_return']['entry_lr_restored'])
        self.assertTrue(r['conditional_return']['r4_restored'])
        self.assertEqual(r['conditional_return']['sp_offset'], 0)
        self.assertEqual(len(r['conditional_return']['assumptions']), 3)

    def test_old_frontier_is_not_reduced(self):
        r = self.analyze()
        self.assertEqual(len(r['remaining_unread_targets']), 18)
        self.assertEqual(len(r['other_unread_targets']), 17)
        self.assertEqual(r['priority_unread_targets'], [0x09097105])
        self.assertEqual(r['remaining_unread_targets'], self.values[0]['analysis']['old_unread_targets'])
        self.assertEqual(r['additional_unread_targets'], [])

    def test_no_native_or_unconditional_claims(self):
        r = self.analyze()
        for key in ('inherited_frame_return_verified', 'stack_integrity_proven', 'all_callers_resolved',
                    'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready'):
            self.assertIs(r[key], False, key)
        self.assertIs(r['call']['callee_return_observed'], False)
        self.assertIs(r['call']['callee_return_proven'], False)
        for key in ('rom_changes', 'new_emulator_processes', 'candidate_reconstructions',
                    'new_graph_decodes', 'prior_abi_classifications_replayed', 'accepted_native_cases_replayed'):
            self.assertEqual(r[key], 0, key)

    def test_deterministic_and_inputs_unchanged(self):
        before = copy.deepcopy(self.values)
        self.assertEqual(j.stable(self.analyze()), j.stable(self.analyze()))
        self.assertEqual(self.values, before)

    def test_does_not_replay_old_classification_or_collector(self):
        with patch.object(j.abi, 'analyze', side_effect=AssertionError('old classifier replay')), \
             patch.object(j.saved, 'collect', side_effect=AssertionError('ROM collection replay')):
            self.analyze()

    def test_changed_candidate_rejected(self):
        self.values[0]['analysis']['candidate']['crc32'] = '00000000'
        with self.assertRaises(ValueError): self.analyze()

    def test_promoted_prior_acceptance_rejected(self):
        self.values[0]['analysis']['inherited_frame_return_verified'] = True
        with self.assertRaises(ValueError): self.analyze()

    def test_missing_saved_lr_rejected(self):
        self.values[0]['analysis']['inherited_edge']['entry_lr_saved_offsets'] = []
        with self.assertRaises(ValueError): self.analyze()

    def test_wrong_prologue_frame_rejected(self):
        g = self.cached(j.saved.OWNER)
        g['nodes'][0]['hex'] = '00b5'  # LRだけ保存する誤prologue。
        with self.assertRaises(ValueError): self.analyze()

    def test_changed_sample_bytes_rejected(self):
        self.graph()['nodes'][0]['hex'] = '00000000'
        with self.assertRaises(ValueError): self.analyze()

    def test_sample_hash_mismatch_rejected(self):
        self.values[0]['analysis']['sampled_ranges'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError): self.analyze()

    def test_sample_count_mismatch_rejected(self):
        self.values[0]['analysis']['sampled_instruction_bytes'] += 2
        with self.assertRaises(ValueError): self.analyze()

    def test_duplicate_nodes_rejected(self):
        self.graph()['nodes'].append(copy.deepcopy(self.graph()['nodes'][0]))
        with self.assertRaises(ValueError): self.analyze()

    def test_escaped_cfg_rejected(self):
        self.graph()['nodes'][3]['successors'][0] += 0x1000
        with self.assertRaises(ValueError): self.analyze()

    def test_external_metadata_mismatch_rejected(self):
        self.graph()['external_edges'][0]['target'] = j.saved.TARGET
        with self.assertRaises(ValueError): self.analyze()

    def test_wrong_bl_target_rejected(self):
        self.graph()['nodes'][0]['target'] += 2
        with self.assertRaises(ValueError): self.analyze()

    def test_veneer_cycle_rejected(self):
        g = self.cached(0x0806DDB5)
        g['nodes'][0]['literal_value'] = g['entry']
        g['resolved_veneer']['target'] = g['entry']
        with self.assertRaises(ValueError): self.analyze()

    def test_veneer_metadata_mismatch_rejected(self):
        self.cached(0x0806DDB5)['resolved_veneer']['target'] += 2
        with self.assertRaises(ValueError): self.analyze()

    def test_stale_source_binding_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'x.py').write_bytes(b'old\n')
            binding = {'x.py': j.identity((root / 'x.py').read_bytes())}
            (root / 'x.py').write_bytes(b'changed\n')
            with self.assertRaises(ValueError): j.saved.bindings_fresh(root, binding)

    def test_shared_callsites_are_saved_scope_only(self):
        r = self.analyze()
        self.assertIn({'owner': 0x0806DEC5, 'site': 0x0806DECC}, r['saved_graph_callsites_to_shared_veneer'])
        self.assertIn({'owner': 0x0806DE7D, 'site': 0x0806DE7C}, r['saved_graph_callsites_to_shared_veneer'])
        self.assertFalse(r['all_callers_resolved'])


if __name__ == '__main__':
    unittest.main()
