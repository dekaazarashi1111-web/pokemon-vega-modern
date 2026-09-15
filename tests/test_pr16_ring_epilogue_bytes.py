"""合成byteだけを使う未読根採取の境界検査。私有ROM不要。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_epilogue_bytes as m

class EpilogueBytesTests(unittest.TestCase):
    def setUp(self):
        self.b = m.ROM_BASE
        self.raw = bytes(256)
        self.calls = []
        self.rows = {self.b: self.node(self.b, 'ordinary'), self.b+2: self.node(self.b+2, 'return')}

    def node(self, at, kind, **kw):
        return dict(address=at, size=2, hex='0000', kind=kind, memory_write=False, **kw)

    def decode(self, raw, at):
        self.calls.append(at)
        return copy.deepcopy(self.rows[at])

    def run_graph(self, **kw):
        args = dict(raw=self.raw, target=self.b+1, cached=set(), deferred=(), decode=self.decode)
        args.update(kw)
        return m.bounded(**args)

    def test_return_stops(self):
        g = self.run_graph()
        self.assertEqual(self.calls, [self.b,self.b+2])
        self.assertEqual(len(g['nodes']), 2)
        self.assertFalse(g['side_effects_excluded'])

    def test_saved_root_rejected_before_decode(self):
        with self.assertRaises(ValueError): self.run_graph(cached={self.b})
        self.assertEqual(self.calls, [])

    def test_saved_next_is_boundary(self):
        g = self.run_graph(cached={self.b+2})
        self.assertEqual(self.calls, [self.b])
        self.assertEqual(g['external_edges'][0]['target'], self.b+3)

    def test_deferred_root_rejected(self):
        with self.assertRaises(ValueError): self.run_graph(deferred=(self.b+1,))

    def test_deferred_next_is_not_decoded(self):
        g = self.run_graph(deferred=(self.b+3,))
        self.assertEqual(self.calls, [self.b])
        self.assertEqual(g['deferred_roots_decoded'], 0)

    def test_wide_instruction_crosses_saved(self):
        self.rows[self.b].update(size=4,hex='00000000')
        with self.assertRaises(ValueError): self.run_graph(cached={self.b+2})

    def test_wide_instruction_crosses_deferred(self):
        self.rows[self.b].update(size=4,hex='00000000')
        with self.assertRaises(ValueError): self.run_graph(deferred=(self.b+3,))

    def test_budget(self):
        with self.assertRaises(ValueError): self.run_graph(limit=1)

    def test_invalid_root_and_limits(self):
        for kw in ({'target':self.b},{'max_window':65},{'max_window':0},{'limit':33}):
            with self.subTest(kw=kw), self.assertRaises(ValueError): self.run_graph(**kw)

    def test_byte_mismatch(self):
        self.rows[self.b]['hex']='0100'
        with self.assertRaises(ValueError): self.run_graph()

    def test_unknown_kind(self):
        self.rows[self.b]['kind']='invented'
        with self.assertRaises(ValueError): self.run_graph()

    def test_call_not_followed(self):
        self.rows[self.b].update(kind='call', target=self.b+20)
        g = self.run_graph()
        self.assertNotIn(self.b+20, self.calls)
        self.assertEqual(g['external_edges'][0]['kind'], 'call')

    def test_odd_branch_rejected(self):
        self.rows[self.b].update(kind='jump', target=self.b+3)
        with self.assertRaises(ValueError): self.run_graph()

    def test_indirect_not_called(self):
        self.rows[self.b].update(kind='indirect',register=1)
        g=self.run_graph()
        self.assertEqual(self.calls,[self.b])
        self.assertIsNone(g['external_edges'][0]['target'])

    def test_external_range_rejected(self):
        self.rows[self.b].update(kind='jump',target=self.b+256)
        with self.assertRaises(ValueError): self.run_graph()

    def test_loop_is_finite(self):
        self.rows[self.b].update(kind='jump',target=self.b)
        self.assertEqual(len(self.run_graph()['nodes']),1)

    def test_literal_mismatch_rejected(self):
        self.raw = bytes.fromhex('0048') + bytes(254)
        self.rows[self.b].update(hex='0048',literal_address=self.b+4,literal_value=1)
        with self.assertRaises(ValueError): self.run_graph()

if __name__ == '__main__': unittest.main()
