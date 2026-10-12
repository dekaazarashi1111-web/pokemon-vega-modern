"""未読callee採取の境界・拒否条件。native成功fixtureには使わない。"""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_callee_bytes as m


class CalleeBytesTests(unittest.TestCase):
    def graph(self):
        return {'entry': m.TARGET, 'window': m.WINDOW, 'side_effects_excluded': False,
                'nodes': [{'address': m.TARGET & ~1, 'size': 2, 'hex': '7047',
                           'kind': 'return', 'memory_write': False, 'successors': []}],
                'external_edges': [], 'memory_write_sites': []}

    def reject(self, change):
        g = self.graph()
        change(g)
        with self.assertRaises(ValueError):
            m.validate_graph(g, set())

    def test_scoped_graph(self):
        m.validate_graph(self.graph(), set())

    def test_wrong_root(self):
        self.reject(lambda g: g.update(entry=m.TARGET + 2))

    def test_wrong_window(self):
        self.reject(lambda g: g.update(window=m.WINDOW * 2))

    def test_no_side_effect_claim(self):
        self.reject(lambda g: g.update(side_effects_excluded=True))

    def test_duplicate(self):
        self.reject(lambda g: g['nodes'].append(copy.deepcopy(g['nodes'][0])))

    def test_bad_bytes(self):
        self.reject(lambda g: g['nodes'][0].update(hex='70'))

    def test_write_metadata(self):
        self.reject(lambda g: g['nodes'][0].update(memory_write=True))

    def test_unknown_node(self):
        self.reject(lambda g: g['nodes'][0].update(kind='unknown'))

    def test_old_code_rejected(self):
        with self.assertRaises(ValueError):
            m.validate_graph(self.graph(), {m.TARGET & ~1})

    def test_bad_literal(self):
        self.reject(lambda g: g['nodes'][0].update(literal_address=m.TARGET + 3))

    def test_even_external_target(self):
        self.reject(lambda g: g['external_edges'].append(
            {'site': m.TARGET & ~1, 'kind': 'call', 'target': 0x08000000}))

    def test_prior_is_unresolved(self):
        frame, cached = m.read_prior()
        self.assertEqual(frame['analysis']['priority_unread_targets'], [m.TARGET])
        self.assertNotIn(m.TARGET & ~1, cached)


if __name__ == '__main__':
    unittest.main()
