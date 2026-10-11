"""helper一根限定と再採取・過大主張の拒否。ROM/nativeは実行しない。"""
import copy
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / 'scripts/pr16_ring_helper_bytes.py'
S = importlib.util.spec_from_file_location('helper_bytes', P)
a = importlib.util.module_from_spec(S)
S.loader.exec_module(a)


class HelperGraphTests(unittest.TestCase):
    def graph(self):
        return {'entry': a.TARGET, 'window': a.WINDOW, 'side_effects_excluded': False,
            'nodes': [{'address': a.TARGET & ~1, 'size': 2, 'hex': '7047', 'kind': 'return', 'memory_write': False}],
            'memory_write_sites': [], 'external_edges': []}

    def test_valid_bounded_return(self):
        a.validate_graph(self.graph(), set())

    def test_reject_old_target(self):
        g = self.graph(); g['entry'] = 0x09097105
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_reject_cached_overlap(self):
        with self.assertRaises(ValueError): a.validate_graph(self.graph(), {a.TARGET & ~1})

    def test_reject_out_of_window(self):
        g = self.graph(); n = copy.deepcopy(g['nodes'][0]); n['address'] += a.WINDOW; g['nodes'].append(n)
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_reject_duplicate(self):
        g = self.graph(); g['nodes'] *= 2
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_reject_bad_byte_count(self):
        g = self.graph(); g['nodes'][0]['hex'] = '70'
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_reject_unreported_write(self):
        g = self.graph(); g['nodes'][0]['memory_write'] = True
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_reject_orphan_edge(self):
        g = self.graph(); g['external_edges'] = [{'site': 0, 'target': 0x08000001}]
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_reject_arm_external_target(self):
        g = self.graph(); g['external_edges'] = [{'site': a.TARGET & ~1, 'target': 0x08000000}]
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_reject_false_side_effect_exclusion(self):
        g = self.graph(); g['side_effects_excluded'] = True
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_reject_wrong_literal_operand(self):
        g = self.graph(); g['nodes'][0]['literal_address'] = 0x091281D4
        with self.assertRaises(ValueError): a.validate_graph(g, set())

    def test_prior_frontier_and_source_bindings(self):
        prior, cached = a.inputs()
        self.assertEqual(prior['analysis']['priority_unread_targets'], [a.TARGET])
        self.assertEqual(len(prior['analysis']['old_unread_targets']), 18)
        self.assertNotIn(a.TARGET & ~1, cached)


if __name__ == '__main__':
    unittest.main()
