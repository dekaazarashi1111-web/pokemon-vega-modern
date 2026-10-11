"""保存external2 byteと全u16・境界・stack副作用を独立式で検証する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_external2_abi as m

class External2Abi(unittest.TestCase):
    def setUp(self): self.prior = m.s.load(m.PRIOR)
    def reject(self):
        with self.assertRaises(ValueError): m.program(self.prior)
    def test_saved_program(self): self.assertEqual(m.program(self.prior)['sampled_instruction_bytes'], 56)
    def test_candidate_drift(self):
        self.prior['analysis']['candidate']['sha256'] = '0' * 64; self.reject()
    def test_target_drift(self):
        self.prior['analysis']['target'] += 2; self.reject()
    def test_opcode_drift(self):
        self.prior['analysis']['graph']['nodes'][1]['hex'] = '0000'; self.reject()
    def test_literal_drift(self):
        next(n for n in self.prior['analysis']['graph']['nodes'] if 'literal_value' in n)['literal_value'] += 1; self.reject()
    def test_range_hash_drift(self):
        self.prior['analysis']['sampled_ranges'][0]['sha256'] = '0' * 64; self.reject()
    def test_successor_drift(self):
        self.prior['analysis']['graph']['nodes'][0]['successors'] = []; self.reject()
    def test_write_annotation(self):
        self.prior['analysis']['graph']['nodes'][0]['memory_write'] = False; self.reject()
    def test_indirect_edge_drift(self):
        self.prior['analysis']['graph']['external_edges'][0]['register'] = 14; self.reject()
    def test_window_drift(self):
        self.prior['analysis']['graph']['window'] = 66; self.reject()
    def test_old_frontier_retained(self):
        self.prior['analysis']['remaining_unread_targets'].remove(self.prior['analysis']['old_unread_targets'][0]); self.reject()
    def test_no_acceptance_promotion(self):
        for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                    'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
            with self.subTest(key=key):
                value = copy.deepcopy(self.prior); value['analysis'][key] = True
                with self.assertRaises(ValueError): m.program(value)
    def test_exhaustive_all_u16_two_mode_classes(self):
        result = m.exhaustive()
        self.assertEqual(result['executed_input_cases'], 131072)
        self.assertEqual(result['true_counts'], [64944, 65388])
        self.assertEqual(result['covered_conditional_outcomes'], 10)
        self.assertEqual(len(result['covered_instruction_sites']), 28)
    def test_zero_mode_boundaries(self):
        for value, expected in ((0,0),(559,0),(560,1),(2047,1),(2048,0),(2079,0),(2080,1),(65535,1)):
            with self.subTest(value=value): self.assertEqual(m.execute(value, 0)['r0'], expected)
    def test_nonzero_mode_boundaries(self):
        for value, expected in ((0,0),(47,0),(48,1),(79,1),(80,0),(179,0),(180,1),(65535,1)):
            with self.subTest(value=value): self.assertEqual(m.execute(value, 1)['r0'], expected)
    def test_all_u8_modes_at_boundaries(self):
        for mode in range(256):
            for value in (0,47,48,79,80,179,180,559,560,2047,2048,2079,2080,65535):
                self.assertEqual(m.execute(value, mode)['r0'], m.formula(value, mode))
    def test_high_bits_ignored(self):
        for value in (0,48,560,2048,65535):
            for mode in (0,1,128,255):
                baseline = m.execute(value, mode)['r0']
                for high in (1,0x8000,0xffff):
                    self.assertEqual(m.execute(value | (high << 16), mode | 0xffffff00)['r0'], baseline)
    def test_preserved_registers(self):
        preserved = tuple(0x80000000 + r for r in range(8))
        result = m.execute(65535, 1, lr=0x09123457, preserved=preserved)
        self.assertEqual(result['r4_r11'], list(preserved)); self.assertEqual(result['lr'], 0x09123457)
    def test_only_stack_store_and_balanced_sp(self):
        result = m.execute(560, 0, sp=0x03007000, lr=0x08101235)
        self.assertEqual(result['memory_writes'], [{'site':m.START,'address':0x03006ffc,'size':4,'value':0x08101235}])
        self.assertEqual(result['stack_reads'], [{'site':m.START+60,'address':0x03006ffc,'size':4,'value':0x08101235}])
        self.assertEqual(result['local_sp_delta'], 0); self.assertEqual(result['exit_sp'], 0x03007000)
    def test_corrupted_slot_not_original_return(self):
        result = m.execute(560, 0, return_slot_override=0x00011235)
        self.assertNotEqual(result['branch_operand'], result['lr']); self.assertEqual(result['r0'], 1)
    def test_even_return_operand_selects_arm_not_executed(self):
        result = m.execute(0, 0, lr=0x08001234)
        self.assertEqual(result['selected_isa'], 'ARM'); self.assertFalse(result['branch_target_executed'])
    def test_u32_validation(self):
        for invalid in (-1,1<<32,True,1.0):
            for field in ('ident','mode','lr'):
                kwargs = {'ident':0,'mode':0,'lr':1}; kwargs[field] = invalid
                with self.assertRaises(ValueError): m.execute(**kwargs)
    def test_stack_validation(self):
        for sp in (0,3,-4,1<<32,True):
            with self.assertRaises(ValueError): m.execute(0,0,sp=sp)
    def test_analysis_saved_only_and_boundaries(self):
        result = m.analyze(self.prior, Path('.local/not-used'))
        self.assertEqual(result['priority_unread_targets'], [0x081138F9])
        self.assertEqual(result['candidate_reconstructions'], 0)
        self.assertEqual(result['new_graph_decodes'], 0)
        self.assertEqual(result['new_emulator_processes'], 0)
        self.assertEqual(result['prior_abi_classifications_replayed'], 0)
        self.assertFalse(result['external2_unconditional_return_proven'])
        self.assertFalse(result['saved_slot_preservation_proven']); self.assertFalse(result['ring_acquisition_accepted'])

if __name__ == '__main__': unittest.main()
