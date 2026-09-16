"""保存helperの全u16・命令改変拒否・callee境界保持。native実行なし。"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_ring_helper_abi as a


def caller_fixture(sample):
    """projection単体検査用。run本体はsource hash付き実callerを別途照合する。"""
    s = sample['analysis']
    value = {'schema_version': 1, 'task': 'PR-P08-7-RING-CALLEE-ABI', 'analysis': {
        'classification': 'LIVE_FRAME_CALLEE_PREFIX_NOT_RETURN_PROOF', 'candidate': copy.deepcopy(a.CANDIDATE),
        'helper': {'site': 0x0909710E, 'target': a.TARGET, 'bl_return_thumb': a.RETURN_LR, 'return_proven': False},
        'prefix': {'argument_r0_r4_r6': 'entry_r0 & 0xffff', 'total_flagset_frame_bytes': 24,
            'flagset_entry_sp_offset_before_helper': -24, 'inherited_flagset_saved_offsets': [-8, -4],
            'saved_register_slots': [{'register': r, 'callee_entry_sp_offset': -16 + 4 * i,
                'flagset_entry_sp_offset': -24 + 4 * i} for i, r in enumerate((4, 5, 6, 14))]},
        'old_unread_targets': copy.deepcopy(s['old_unread_targets']),
        'additional_unread_targets': copy.deepcopy(s['prior_additional_unread_targets']),
        'remaining_unread_targets': copy.deepcopy(s['remaining_unread_targets']),
        'conditional_exits': [{'target': a.NONZERO}, {'target': a.ZERO}]}}
    for key in ('callee_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
                'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready', 'old_frontier_removed'):
        value['analysis'][key] = False
    return value


class HelperAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = json.loads((ROOT / a.SAMPLE).read_bytes())
        cls.words, cls.pools = a.validate_sample(cls.sample)

    def test_saved_bytes_and_literals(self):
        self.assertEqual(len(self.words), 29)
        self.assertEqual(len(self.pools), 5)

    def test_all_65536_values_and_coverage(self):
        result = a.exhaustive(self.words, self.pools)
        self.assertEqual(result['domain']['values_checked'], 65536)
        self.assertEqual(result['instructions_covered'], 29)
        self.assertEqual(result['zero_returns'], 51456)
        self.assertEqual(result['nonzero_returns'], 14080)
        self.assertEqual(result['distinct_nonzero_addresses'], 513)
        self.assertEqual(result['max_instructions_per_call'], 24)
        self.assertEqual(result['return_table_sha256'], '438b997f59ca7328b88a65dbeb4af3e74b78c1f066f89a124c6a707f27ac2fe0')

    def test_boundary_return_values(self):
        for value, expected in {0: 0, 0x8ff: 0, 0x900: 0x0203B0E8, 0x907: 0x0203B0E8,
            0x908: 0x0203B0E9, 0x18ff: 0x0203B2E7, 0x1900: 0x02036FEC,
            0x3fff: 0x02036FEC, 0x4000: 0, 0xffff: 0}.items():
            with self.subTest(value=value):
                self.assertEqual(a.execute(self.words, self.pools, value)['registers'][0], expected)

    def test_carry_input_is_irrelevant(self):
        for value in (0, 0x8ff, 0x900, 0x18ff, 0x1900, 0x3fff, 0x4000, 0xffff):
            self.assertEqual(a.execute(self.words, self.pools, value, carry=0),
                             a.execute(self.words, self.pools, value, carry=1))

    def test_preservation_not_a_single_sentinel(self):
        for value in (0, 0x900, 0x18ff, 0x1900, 0x4000):
            for sp in (0x02036FEC, 0x03007FF0):
                regs = [(0xffffffff - i * 0x01010101) for i in range(16)]
                regs[0], regs[13], regs[14] = value, sp, a.RETURN_LR
                before = list(regs)
                result = a.execute(self.words, self.pools, value, regs)
                self.assertEqual(regs, before)
                for r in a.PRESERVED: self.assertEqual(result['registers'][r], before[r])
                self.assertEqual(result['written_registers'], [0, 1, 2, 3, 12])
                self.assertEqual(result['memory_writes'], [])
                self.assertEqual(result['return_thumb'], a.RETURN_LR)

    def test_reject_non_u16_inputs(self):
        for value in (-1, 65536, 0x10000900, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError): a.execute(self.words, self.pools, value)
                with self.assertRaises(ValueError): a.specification(value)

    def test_reject_unknown_instruction(self):
        words = (0xffff, *self.words[1:])
        with self.assertRaises(ValueError): a.execute(words, self.pools, 0)

    def test_reject_store_instruction(self):
        words = (0x6000, *self.words[1:])
        with self.assertRaises(ValueError): a.execute(words, self.pools, 0)

    def test_reject_high_register_stack_lr_pc_writes(self):
        for encoding in (0x469d, 0x469e, 0x469f):
            with self.subTest(encoding=encoding):
                with self.assertRaises(ValueError): a.execute((encoding, *self.words[1:]), self.pools, 0)

    def test_reject_unknown_literal(self):
        with self.assertRaises(ValueError): a.execute(self.words, (), 0)

    def test_reject_loop_without_return(self):
        with self.assertRaises(ValueError): a.execute((0xe7fe,), (), 0)

    def test_reject_all_instruction_mutations_even_with_new_hash(self):
        for i in range(29):
            with self.subTest(instruction=i):
                s = copy.deepcopy(self.sample)
                n = s['analysis']['graph']['nodes'][i]
                raw = (int.from_bytes(bytes.fromhex(n['hex']), 'little') ^ 1).to_bytes(2, 'little')
                n['hex'] = raw.hex()
                slot = next(r for r in s['analysis']['sampled_ranges'] if r['address'] == n['address'])
                slot.update(hex=raw.hex(), sha256=hashlib.sha256(raw).hexdigest())
                with self.assertRaises(ValueError): a.validate_sample(s)

    def test_reject_all_literal_mutations_even_with_new_hash(self):
        for address in a.LITERALS:
            with self.subTest(literal=address):
                s = copy.deepcopy(self.sample)
                slot = next(r for r in s['analysis']['sampled_ranges'] if r['address'] == address)
                raw = (int.from_bytes(bytes.fromhex(slot['hex']), 'little') ^ 1).to_bytes(4, 'little')
                slot.update(hex=raw.hex(), sha256=hashlib.sha256(raw).hexdigest())
                with self.assertRaises(ValueError): a.validate_sample(s)

    def test_reject_broken_hash(self):
        s = copy.deepcopy(self.sample); s['analysis']['sampled_ranges'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError): a.validate_sample(s)

    def test_reject_missing_duplicate_and_extra_samples(self):
        for mode in ('missing', 'duplicate', 'extra'):
            s = copy.deepcopy(self.sample); samples = s['analysis']['sampled_ranges']
            if mode == 'missing': samples.pop()
            else:
                entry = copy.deepcopy(samples[-1])
                if mode == 'extra': entry['address'] += 4
                samples.append(entry)
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError): a.validate_sample(s)

    def test_reject_cfg_return_target_and_write_metadata(self):
        for index, key, value in ((7, 'target', 0), (23, 'register', 0), (28, 'successors', []),
                                  (0, 'memory_write', True), (0, 'kind', 'call')):
            s = copy.deepcopy(self.sample); s['analysis']['graph']['nodes'][index][key] = value
            with self.subTest(index=index, key=key):
                with self.assertRaises(ValueError): a.validate_sample(s)

    def test_reject_external_edge(self):
        s = copy.deepcopy(self.sample); s['analysis']['graph']['external_edges'] = [{'site': a.START, 'target': a.NONZERO}]
        with self.assertRaises(ValueError): a.validate_sample(s)

    def test_reject_candidate_change(self):
        s = copy.deepcopy(self.sample); s['analysis']['candidate']['crc32'] = '00000000'
        with self.assertRaises(ValueError): a.validate_sample(s)

    def test_reject_unsupported_prior_claims(self):
        for key in ('helper_return_proven', 'stack_integrity_proven', 'all_callers_resolved',
                    'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready', 'old_frontier_removed'):
            s = copy.deepcopy(self.sample); s['analysis'][key] = True
            with self.subTest(key=key):
                with self.assertRaises(ValueError): a.validate_sample(s)

    def test_pointer_nonalias_is_not_unconditional(self):
        pointer = a.specification(0x1900)
        self.assertTrue(a.pointer_address_overlaps_saved_frame(pointer, pointer + 24))
        self.assertFalse(a.pointer_address_overlaps_saved_frame(pointer, pointer))
        self.assertFalse(a.pointer_address_overlaps_saved_frame(pointer, 0x03007FF0))
        self.assertFalse(a.pointer_address_overlaps_saved_frame(0, 24))

    def test_reject_invalid_stack_model(self):
        for sp in (0, 20, 25, 0x100000000):
            with self.assertRaises(ValueError): a.pointer_address_overlaps_saved_frame(0x02036FEC, sp)

    def test_projection_keeps_unread_callee_and_old_frontier(self):
        result = a.analyze(self.sample, caller_fixture(self.sample))
        self.assertTrue(result['helper_return_proven'])
        self.assertFalse(result['helper_return_observed'])
        self.assertTrue(result['helper_saved_slots_unchanged'])
        self.assertEqual(result['old_unread_targets'], self.sample['analysis']['old_unread_targets'])
        self.assertEqual(result['additional_unread_targets'], sorted([a.NONZERO, a.ZERO]))
        self.assertEqual(result['priority_unread_targets'], [a.NONZERO])
        self.assertEqual(len(result['remaining_unread_targets']), 20)
        for key in ('callee_return_proven', 'inherited_frame_return_verified', 'stack_integrity_proven',
                    'all_callers_resolved', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'release_ready', 'old_frontier_removed'):
            self.assertIs(result[key], False)
        self.assertFalse(result['return_pointer']['non_alias_proven'])
        self.assertFalse(result['return_pointer']['downstream_access_width_known'])
        self.assertEqual(result['candidate_reconstructions'], 0)
        self.assertEqual(result['new_graph_decodes'], 0)
        self.assertEqual(result['accepted_native_cases_replayed'], 0)

    def test_reject_caller_argument_frame_return_and_frontier_drift(self):
        for key, value in (('argument_r0_r4_r6', 'unconstrained u32'), ('total_flagset_frame_bytes', 8),
                           ('flagset_entry_sp_offset_before_helper', 0)):
            caller = caller_fixture(self.sample); caller['analysis']['prefix'][key] = value
            with self.subTest(key=key):
                with self.assertRaises(ValueError): a.analyze(self.sample, caller)
        caller = caller_fixture(self.sample); caller['analysis']['helper']['bl_return_thumb'] += 2
        with self.assertRaises(ValueError): a.analyze(self.sample, caller)
        caller = caller_fixture(self.sample); caller['analysis']['old_unread_targets'].pop()
        with self.assertRaises(ValueError): a.analyze(self.sample, caller)

    def test_reject_saved_slot_and_exit_drift(self):
        caller = caller_fixture(self.sample)
        caller['analysis']['prefix']['saved_register_slots'][0]['flagset_entry_sp_offset'] += 4
        with self.assertRaises(ValueError): a.analyze(self.sample, caller)
        caller = caller_fixture(self.sample)
        caller['analysis']['conditional_exits'][0]['target'] = a.TARGET
        with self.assertRaises(ValueError): a.analyze(self.sample, caller)

    def test_reject_caller_overclaim(self):
        for key in ('callee_return_proven', 'all_runtime_owners_excluded', 'ring_acquisition_accepted', 'old_frontier_removed'):
            caller = caller_fixture(self.sample); caller['analysis'][key] = True
            with self.subTest(key=key):
                with self.assertRaises(ValueError): a.analyze(self.sample, caller)


if __name__ == '__main__':
    unittest.main()
