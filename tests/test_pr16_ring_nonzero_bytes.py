"""未読14byte限定採取の境界・異常系。ROMや既受入の実行はしない。"""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_nonzero_bytes as a


def graph():
    return {'entry': a.TARGET, 'window': a.WINDOW, 'side_effects_excluded': False,
        'nodes': [{'address': a.TARGET & ~1, 'size': 2, 'hex': '7047', 'kind': 'return', 'memory_write': False}],
        'memory_write_sites': [], 'external_edges': []}


class NonzeroBytesTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(a.validate_graph(graph(), set()), set(range(a.TARGET & ~1, (a.TARGET & ~1) + 2)))

    def reject(self, change):
        g = graph(); change(g)
        with self.assertRaises(ValueError):
            a.validate_graph(g, set())

    def test_wrong_root(self):
        self.reject(lambda g: g.update(entry=0x0806DDBD))

    def test_wrong_window(self):
        self.reject(lambda g: g.update(window=1024))

    def test_side_effect_overclaim(self):
        self.reject(lambda g: g.update(side_effects_excluded=True))

    def test_empty(self):
        self.reject(lambda g: g.update(nodes=[]))

    def test_duplicate(self):
        self.reject(lambda g: g['nodes'].append(copy.deepcopy(g['nodes'][0])))

    def test_odd_address(self):
        self.reject(lambda g: g['nodes'][0].update(address=a.TARGET))

    def test_prior_code_rejected(self):
        with self.assertRaises(ValueError):
            a.validate_graph(graph(), {a.TARGET & ~1})

    def test_callee_prefix_excluded(self):
        self.reject(lambda g: g['nodes'].append(dict(address=0x09097104, size=2, hex='70b5', kind='ordinary', memory_write=True)))

    def test_crossing_instruction(self):
        self.reject(lambda g: g['nodes'].append(dict(address=0x09097102, size=4, hex='00f000f8', kind='call', memory_write=False)))

    def test_short_hex(self):
        self.reject(lambda g: g['nodes'][0].update(hex='70'))

    def test_unknown_kind(self):
        self.reject(lambda g: g['nodes'][0].update(kind='guessed'))

    def test_hidden_write(self):
        self.reject(lambda g: g['nodes'][0].update(memory_write=True))

    def test_orphan_edge(self):
        self.reject(lambda g: g['external_edges'].append(dict(site=0x09097104, target=None)))

    def test_even_target(self):
        self.reject(lambda g: g['external_edges'].append(dict(site=a.TARGET & ~1, target=0x0806DDBC)))

    def test_ram_target(self):
        self.reject(lambda g: g['external_edges'].append(dict(site=a.TARGET & ~1, target=0x02000001)))

    def test_unresolved_edge_retained(self):
        g = graph(); g['external_edges'] = [dict(site=a.TARGET & ~1, target=None)]
        a.validate_graph(g, set())

    def test_zero_side_representable_not_followed(self):
        g = graph(); g['external_edges'] = [dict(site=a.TARGET & ~1, target=0x0806DDBD)]
        a.validate_graph(g, set())


if __name__ == '__main__':
    unittest.main()
