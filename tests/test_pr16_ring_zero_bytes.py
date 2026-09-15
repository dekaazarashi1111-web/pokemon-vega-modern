"""実ROM不要。zero一根の範囲/重複/曖昧decodeをfail closedで検査する。"""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('zero_bytes', Path(__file__).resolve().parents[1] / 'scripts/pr16_ring_zero_bytes.py')
z = importlib.util.module_from_spec(spec)
spec.loader.exec_module(z)


class ZeroBytesTests(unittest.TestCase):
    def graph(self):
        return {'entry': z.TARGET, 'window': 128, 'side_effects_excluded': False,
            'nodes': [{'address': z.TARGET & ~1, 'size': 2, 'hex': '70bd', 'kind': 'return',
                       'memory_write': False, 'successors': []}], 'memory_write_sites': [], 'external_edges': []}

    def reject(self, edit, cached=()):
        g = self.graph()
        edit(g)
        with self.assertRaises(ValueError):
            z.validate_graph(g, set(cached))

    def test_valid(self):
        self.assertEqual(z.validate_graph(self.graph(), set()), set(range(z.TARGET & ~1, (z.TARGET & ~1) + 2)))
    def test_already_read_root(self):
        with self.assertRaises(ValueError): z.window_for({z.TARGET & ~1})
    def test_stops_before_known_code(self):
        self.assertEqual(z.window_for({(z.TARGET & ~1) + 16}), 16)
    def test_odd_boundary(self):
        with self.assertRaises(ValueError): z.window_for({z.TARGET})
    def test_wrong_root(self):
        self.reject(lambda g: g.update(entry=z.TARGET + 2))
    def test_wrong_window(self):
        self.reject(lambda g: g.update(window=130))
    def test_no_nodes(self):
        self.reject(lambda g: g.update(nodes=[]))
    def test_duplicate_nodes(self):
        self.reject(lambda g: g['nodes'].append(copy.deepcopy(g['nodes'][0])))
    def test_odd_instruction(self):
        self.reject(lambda g: g['nodes'][0].update(address=z.TARGET))
    def test_bad_size(self):
        self.reject(lambda g: g['nodes'][0].update(size=3))
    def test_size_mismatch(self):
        self.reject(lambda g: g['nodes'][0].update(hex='70'))
    def test_unknown_kind(self):
        self.reject(lambda g: g['nodes'][0].update(kind='unknown'))
    def test_write_summary(self):
        self.reject(lambda g: g['nodes'][0].update(memory_write=True))
    def test_side_effect_overclaim(self):
        self.reject(lambda g: g.update(side_effects_excluded=True))
    def test_orphan_edge(self):
        self.reject(lambda g: g['external_edges'].append({'site': z.TARGET + 100, 'target': z.TARGET}))
    def test_even_external_edge(self):
        self.reject(lambda g: g['external_edges'].append({'site': z.TARGET & ~1, 'target': 0x08000000}))
    def test_wrong_literal(self):
        self.reject(lambda g: g['nodes'][0].update(literal_address=0x08000000, literal_value=0))
    def test_no_input_mutation(self):
        g = self.graph(); before = copy.deepcopy(g)
        z.validate_graph(g, set())
        self.assertEqual(g, before)


if __name__ == '__main__':
    unittest.main()
