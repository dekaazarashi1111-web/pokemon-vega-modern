"""zero保存byteの改変拒否、境界、仮想call契約と副作用を限定検証する。"""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_zero_abi as abi
from pr16_ring_zero_abi import model


class ZeroABITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = json.loads((ROOT / abi.SAMPLE).read_bytes())
        cls.nodes, cls.literals, cls.edges = abi.audit_sample(cls.sample)

    def reject(self, edit):
        s = copy.deepcopy(self.sample)
        edit(s['analysis'])
        with self.assertRaises(ValueError): abi.audit_sample(s)

    def run_case(self, ident, selector=0, returns=None):
        return model.execute(self.nodes, self.literals, ident, selector, returns)

    def test_exact_code_and_frontier(self):
        self.assertEqual((len(self.nodes), len(self.literals), len(self.edges)), (54, 5, 6))
    def test_changed_byte_rejected(self):
        self.reject(lambda a: a['graph']['nodes'][0].update(hex='012c'))
    def test_false_return_claim_rejected(self):
        self.reject(lambda a: a.update(callee_return_proven=True))
    def test_false_native_claim_rejected(self):
        self.reject(lambda a: a.update(ring_acquisition_accepted=True))
    def test_candidate_rejected(self):
        self.reject(lambda a: a['candidate'].update(crc32='00000000'))
    def test_root_rejected(self):
        self.reject(lambda a: a['graph'].update(entry=model.ENTRY + 2))
    def test_window_rejected(self):
        self.reject(lambda a: a['graph'].update(window=130))
    def test_hidden_store_rejected(self):
        self.reject(lambda a: next(n for n in a['graph']['nodes'] if n['memory_write']).update(memory_write=False))
    def test_instruction_width_rejected(self):
        self.reject(lambda a: a['graph']['nodes'][0].update(size=4))
    def test_literal_rejected(self):
        self.reject(lambda a: next(n for n in a['graph']['nodes'] if 'literal_value' in n).update(literal_value=0))
    def test_sample_hash_rejected(self):
        self.reject(lambda a: a['sampled_ranges'][0].update(sha256='0' * 64))
    def test_dropped_frontier_rejected(self):
        self.reject(lambda a: a['graph']['external_edges'].pop())
    def test_changed_branch_metadata_rejected(self):
        self.reject(lambda a: a['graph']['nodes'][1].update(target=0x08000000))
    def test_changed_successor_rejected(self):
        self.reject(lambda a: a['graph']['nodes'][0].update(successors=[]))
    def test_changed_call_metadata_rejected(self):
        self.reject(lambda a: next(n for n in a['graph']['nodes'] if n['kind'] == 'call').update(target=0x08000000))
    def test_node_reordering_rejected(self):
        self.reject(lambda a: a['graph']['nodes'].reverse())
    def test_zero_is_not_yet_returned(self):
        r = self.run_case(0)
        self.assertEqual((r['boundary'], r['registers'][0], r['registers'][13]), (abi.ZERO_TAIL, 0, -24))
        self.assertEqual(r['calls'] + r['writes'] + r['reads'], [])
    def test_high_ids_stop_before_unread_special_path(self):
        for ident in (16384, 65535):
            r = self.run_case(ident)
            self.assertEqual((r['boundary'], r['registers'][0], r['registers'][4]), (abi.HIGH_TAIL, 16383, ident))
    def test_default_selector_has_no_pointer_return_yet(self):
        for selector in (0, 3, 255):
            r = self.run_case(2303, selector)
            self.assertEqual((r['boundary'], r['registers'][0], r['registers'][1]), (abi.COMMON_TAIL, model.SAVE_PTR, 287))
            self.assertEqual(r['writes'] + r['calls'], [])
    def test_external_call_is_not_executed_by_default(self):
        r = self.run_case(1, 1)
        self.assertEqual(r['boundary'], model.CALL1)
        self.assertFalse(r['calls'][0]['return_assumed'])
        self.assertEqual(r['calls'][0]['args'][:2], [1, 1])
        self.assertEqual(r['registers'][14], 0x0806DDED)
    def test_null_call1_does_not_write(self):
        r = self.run_case(8, 1, {model.CALL1: 0})
        self.assertEqual(r['writes'], [])
        self.assertEqual(r['boundary'], abi.COMMON_TAIL)
    def test_nonzero_call1_byte_copy_is_conditional(self):
        r = self.run_case(8, 1, {model.CALL1: ('call1_nonzero', 0)})
        self.assertEqual(r['writes'], [{'site': 0x0806DE02, 'address': ('save_base', 0xee1), 'width': 1,
            'value': {'read_width': 1, 'address': ('call1_nonzero', 0)}}])
        self.assertEqual(r['registers'][13], -24)
    def test_call2_result_is_low_byte_not_whole_word(self):
        r = self.run_case(2303, 2, {model.CALL2: 257})
        self.assertEqual(r['writes'], [{'site': 0x0806DE1E, 'address': model.HALFWORD, 'width': 2, 'value': 2303}])
        self.assertEqual(r['boundary'], model.CALL3)
        self.assertFalse(r['calls'][-1]['return_assumed'])
        self.assertEqual(r['calls'][-1]['args'], [1, 2303, {'read_width': 1, 'address': ('save_base', 0xfff)}])
    def test_call2_low_byte_zero_does_not_write(self):
        r = self.run_case(1, 2, {model.CALL2: 256})
        self.assertEqual((r['boundary'], r['writes']), (abi.COMMON_TAIL, []))
    def test_no_frame_restoration_claim(self):
        r = self.run_case(123, 1, {model.CALL1: 0})
        self.assertEqual([r['registers'][x] for x in (4, 5, 6, 13)], [123, 123 << 16, 123, -24])
        self.assertNotEqual(r['registers'][14], model.HELPER_LR)
    def test_unknown_call_contract_rejected(self):
        with self.assertRaises(ValueError): self.run_case(1, 2, {model.CALL3: 0})
    def test_u16_range_rejected(self):
        for ident in (-1, 65536, True):
            with self.assertRaises(ValueError): self.run_case(ident)
    def test_selector_range_rejected(self):
        with self.assertRaises(ValueError): self.run_case(1, 256)
    def test_missing_literal_rejected(self):
        with self.assertRaises(ValueError): model.execute(self.nodes, {}, 1)
    def test_unknown_opcode_rejected(self):
        nodes = dict(self.nodes); nodes[model.ENTRY & ~1] = bytes.fromhex('ffff')
        with self.assertRaises(ValueError): model.execute(nodes, self.literals, 0)
    def test_cycle_rejected(self):
        nodes = dict(self.nodes); nodes[model.ENTRY & ~1] = bytes.fromhex('fee7')
        with self.assertRaises(ValueError): model.execute(nodes, self.literals, 0)
    def test_unknown_flags_rejected(self):
        with self.assertRaises(ValueError): model.condition(8, (None, False, None, None))
    def test_signed_selector_comparison(self):
        self.assertTrue(model.condition(13, model.cmp_flags(0, 1)))
        self.assertFalse(model.condition(13, model.cmp_flags(255, 1)))
    def test_bl_destinations(self):
        self.assertEqual(model.bl_target(0x0806DDE8, bytes.fromhex('a5f04efd')), model.CALL1)
        self.assertEqual(model.bl_target(0x0806DE10, bytes.fromhex('fff784ff')), model.CALL2)
        self.assertEqual(model.bl_target(0x0806DE34, bytes.fromhex('a5f060fd')), model.CALL3)
    def test_modulo_and_slot_alias_counterexample(self):
        self.assertEqual(model.plus(('save_base', 0xffffffff), 1), ('save_base', 0))
        self.assertEqual(model.plus(0x0200F120, 0xee0), 0x02010018 - 24)
        self.assertEqual(model.HALFWORD + 24, 0x030050D4)
    def test_inputs_not_mutated(self):
        before = copy.deepcopy((self.sample, self.nodes, self.literals))
        self.run_case(1, 1, {model.CALL1: ('call1_nonzero', 0)})
        self.assertEqual(before, (self.sample, self.nodes, self.literals))


if __name__ == '__main__': unittest.main()
