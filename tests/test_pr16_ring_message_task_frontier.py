"""登録task一根の保存出自と新規窓のfail-closed検査。旧391条件は起動しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_message_task_frontier as m


class FrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = m.prior.saved_inputs()[0]
        cls.summary = m.s.load(m.PRIOR)['analysis']
        cls.plan = m.plan(cls.nodes, cls.summary)

    def reject_node(self, at, key, value):
        rows = copy.deepcopy(self.nodes)
        next(r for r in rows if r['address'] == at)[key] = value
        with self.assertRaises(ValueError): m.plan(rows, self.summary)

    def test_exact_callback_and_window(self):
        self.assertEqual(self.plan['new_root'], 0x08068c31)
        self.assertEqual(self.plan['code_window'], [0x08068c30, 0x08068ccc])
        self.assertEqual(self.plan['maximum_bytes'], 156)

    def test_upstream_chain(self):
        self.assertEqual([r['site'] for r in self.plan['saved_call_chain']],
            [0x0806b0da, 0x08068d0a, 0x08068d98, 0x08068cd2])

    def test_initializer_is_not_runtime(self):
        self.assertFalse(self.plan['initializer_runtime_observed'])
        self.assertFalse(self.plan['runtime_reachability_proven'])
        self.assertEqual(len(self.plan['initializer_nodes']), 5)

    def test_priority_and_busy_byte(self):
        self.assertEqual(self.plan['task_priority'], 80)
        self.assertEqual(self.plan['message_busy_address'], 0x02036fd0)

    def test_duplicate_saved_node(self):
        with self.assertRaises(ValueError): m.plan(self.nodes + [self.nodes[0]], self.summary)

    def test_missing_saved_node(self):
        with self.assertRaises(ValueError): m.plan(self.nodes[:-1], self.summary)

    def test_callback_literal(self): self.reject_node(0x08068cce, 'literal_value', m.CALLBACK + 2)
    def test_callback_literal_opcode(self): self.reject_node(0x08068cce, 'hex', '0448')
    def test_priority_opcode(self): self.reject_node(0x08068cd0, 'hex', '5121')
    def test_upstream_target(self): self.reject_node(0x0806b0da, 'target', 0x08068d88)
    def test_producer_opcode(self): self.reject_node(0x08068d0a, 'hex', '00000000')
    def test_registration_target(self): self.reject_node(0x08068cd2, 'target', 0x08076bb6)
    def test_initializer_target(self): self.reject_node(0x080f8a2c, 'target', 0x08002c1e)
    def test_busy_literal(self): self.reject_node(0x08068d00, 'literal_value', 0x02036fd1)
    def test_font_table_literal(self): self.reject_node(0x080f8a2a, 'literal_value', 0x083e30ec)

    def test_prior_candidate_and_counts(self):
        for key, value in (('candidate', {}), ('contract_cases', 390), ('pending_registered_task_callback', 0)):
            with self.subTest(key=key):
                d = copy.deepcopy(self.summary); d[key] = value
                with self.assertRaises(ValueError): m.plan(self.nodes, d)

    def test_prior_no_native_promotion(self):
        for key in ('ring_acquisition_accepted', 'release_ready', 'actual_callback_table_observed', 'initializer_runtime_observed'):
            with self.subTest(key=key):
                d = copy.deepcopy(self.summary); d[key] = True
                with self.assertRaises(ValueError): m.plan(self.nodes, d)

    def test_no_resample(self):
        rows = copy.deepcopy(self.nodes); rows[0]['address'] = m.LO
        with self.assertRaises(ValueError): m.plan(rows, self.summary)


class BoundsTests(unittest.TestCase):
    def good(self):
        return {'initial_roots': [m.CALLBACK], 'saved_roots_reused': [],
            'saved_nodes_redecoded': 0, 'direct_calls_recursively_expanded': 0,
            'wave_limit_reached': False, 'deferred_by_wave_limit': [],
            'new_nodes': [{'address': m.LO, 'size': 2, 'hex': '00b5', 'kind': 'ordinary'}]}

    def reject(self, key, value):
        r = self.good(); r[key] = value
        with self.assertRaises(ValueError): m.validate_new(r, set())

    def test_valid_single_node(self): self.assertEqual(m.validate_new(self.good(), set()), {m.LO, m.LO + 1})
    def test_wrong_root(self): self.reject('initial_roots', [m.CALLBACK + 2])
    def test_saved_root(self): self.reject('saved_roots_reused', [m.CALLBACK])
    def test_redecode(self): self.reject('saved_nodes_redecoded', 1)
    def test_recursive_call(self): self.reject('direct_calls_recursively_expanded', 1)
    def test_deferred_wave(self): self.reject('deferred_by_wave_limit', [m.CALLBACK + 2])
    def test_wave_limit(self): self.reject('wave_limit_reached', True)
    def test_no_nodes(self): self.reject('new_nodes', [])

    def test_bad_instruction_bounds(self):
        for key, value in (('address', m.LO + 1), ('address', m.HI), ('size', 6), ('hex', '00')):
            with self.subTest(key=key, value=value):
                r = self.good(); r['new_nodes'][0][key] = value
                with self.assertRaises(ValueError): m.validate_new(r, set())

    def test_saved_byte_overlap(self):
        with self.assertRaises(ValueError): m.validate_new(self.good(), {m.LO + 1})

    def test_duplicate_node(self):
        r = self.good(); r['new_nodes'] *= 2
        with self.assertRaises(ValueError): m.validate_new(r, set())

    def test_literal_outside_or_unaligned(self):
        for at in (m.LO - 4, m.LO + 1, m.HI):
            with self.subTest(address=at):
                r = self.good(); r['new_nodes'][0]['literal_address'] = at
                with self.assertRaises(ValueError): m.validate_new(r, set())


if __name__ == '__main__': unittest.main()
