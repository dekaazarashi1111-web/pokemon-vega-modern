"""保存末尾の局所診断・証拠改変拒否・条件付き合成。先行ABIは呼ばない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pr16_ring_external3_tail_abi as m


class TailMachineTests(unittest.TestCase):
    def setUp(self):
        self.regs, self.mem = m.snapshot()
        self.result = m.execute(self.regs, self.mem)

    def test_pop_order(self):
        self.assertEqual([r['register'] for r in self.result['reads']], [4,5,6,7,0])

    def test_restored_values(self):
        self.assertEqual(self.result['registers_before_branch'][4:8], [0x11111111,0x22222222,0x33333333,0x44444444])

    def test_sp_consumes_twenty(self):
        self.assertEqual(self.result['sp_delta'], 20)
        self.assertEqual(self.result['registers_before_branch'][13], self.regs[13]+20)

    def test_r0_not_body_index_plus_one(self):
        for body_r0 in (1,2,65535,65536):
            regs = list(self.regs); regs[0] = body_r0
            self.assertEqual(m.execute(regs,self.mem)['registers_before_branch'][0], 0x08101011)

    def test_other_registers_unchanged_at_branch(self):
        for reg in (1,2,3,8,9,10,11,12,14):
            self.assertEqual(self.result['registers_before_branch'][reg], self.regs[reg])

    def test_little_endian(self):
        regs, mem = m.snapshot((0x12345678,0xabcdef01,0x87654321,0x01020304,0x08123457))
        self.assertEqual(m.execute(regs,mem)['registers_before_branch'][4], 0x12345678)
        self.assertEqual(mem[regs[13]], 0x78)

    def test_read_addresses_and_sites(self):
        self.assertEqual([r['address'] for r in self.result['reads']], [self.regs[13]+4*i for i in range(5)])
        self.assertEqual([r['site'] for r in self.result['reads']], [m.START]*4+[m.START+2])

    def test_memory_immutable(self):
        before = dict(self.mem); m.execute(self.regs,self.mem)
        self.assertEqual(before,self.mem)
        self.assertTrue(self.result['memory_unchanged'])
        self.assertEqual(self.result['local_memory_writes'],0)

    def test_register_input_immutable(self):
        before = list(self.regs); m.execute(self.regs,self.mem)
        self.assertEqual(before,self.regs)

    def test_thumb_branch_is_boundary_not_execution(self):
        self.assertEqual(self.result['branch_word'],0x08101011)
        self.assertEqual(self.result['branch_address'],0x08101010)
        self.assertEqual(self.result['instruction_set'],'THUMB')
        self.assertFalse(self.result['branch_target_executed'])
        self.assertFalse(self.result['target_executability_proven'])

    def test_aligned_arm_boundary(self):
        regs,mem = m.snapshot((0,1,2,3,0x08101010)); result=m.execute(regs,mem)
        self.assertEqual(result['instruction_set'],'ARM')
        self.assertEqual(result['branch_address'],0x08101010)
        self.assertTrue(result['target_alignment_valid'])
        self.assertFalse(result['branch_target_executed'])

    def test_misaligned_arm_not_promoted(self):
        regs,mem = m.snapshot((0,1,2,3,0x08101012)); result=m.execute(regs,mem)
        self.assertFalse(result['target_alignment_valid'])
        self.assertIsNone(result['branch_address'])
        self.assertFalse(result['target_executability_proven'])

    def test_missing_frame_byte_rejected(self):
        for offset in range(20):
            mem=dict(self.mem); del mem[self.regs[13]+offset]
            with self.assertRaises(ValueError): m.execute(self.regs,mem)

    def test_unaligned_sp_rejected(self):
        for offset in (1,2,3):
            regs=list(self.regs); regs[13]+=offset
            with self.assertRaises(ValueError): m.execute(regs,self.mem)

    def test_wrapping_sp_rejected(self):
        regs,mem=m.snapshot(sp=0xfffffff0)
        with self.assertRaises(ValueError): m.execute(regs,mem)

    def test_register_width_and_type_rejected(self):
        for value in (-1,1<<32,True,'1'):
            regs=list(self.regs); regs[3]=value
            with self.assertRaises(ValueError): m.execute(regs,self.mem)

    def test_register_count_rejected(self):
        with self.assertRaises(ValueError): m.execute(self.regs[:-1],self.mem)

    def test_memory_byte_range_rejected(self):
        for value in (-1,256,True,'0'):
            mem=dict(self.mem); mem[self.regs[13]]=value
            with self.assertRaises(ValueError): m.execute(self.regs,mem)

    def test_memory_address_range_rejected(self):
        for addr in (-1,1<<32,'0'):
            mem=dict(self.mem); mem[addr]=0
            with self.assertRaises(ValueError): m.execute(self.regs,mem)

    def test_extreme_saved_words(self):
        for value in (0,1,0x7fffffff,0x80000000,0xffffffff):
            regs,mem=m.snapshot((value,)*5); result=m.execute(regs,mem)
            for reg in (0,4,5,6,7): self.assertEqual(result['registers_before_branch'][reg],value)

    def test_each_bit_of_all_five_slots_matters(self):
        result=m.diagnostics()
        self.assertEqual(result['single_bit_frame_corruption_cases'],160)
        self.assertEqual(result['frame_bytes_covered'],20)

    def test_lr_halfword_corruption_is_counterexample(self):
        d=m.diagnostics()['saved_lr_halfword_corruption']
        self.assertEqual(d['original_branch_word'],0x08101011)
        self.assertEqual(d['changed_branch_word'],0x08102221)
        self.assertFalse(d['observed'])

    def test_diagnostics_not_native_or_prior_abi(self):
        d=m.diagnostics()
        self.assertFalse(d['native_observation'])
        self.assertFalse(d['prefix_or_body_executed'])
        self.assertTrue(d['local_register_seed_is_fixture_not_runtime_evidence'])


class SavedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior=m.s.load(m.PRIOR); cls.prefix=m.s.load(m.PREFIX); cls.body=m.s.load(m.BODY)

    def altered(self, change):
        prior=copy.deepcopy(self.prior); change(prior['analysis'])
        with self.assertRaises((ValueError,KeyError)): m.program(prior)

    def test_exact_saved_program(self):
        self.assertEqual(m.program(self.prior)['sampled_instruction_bytes'],6)

    def test_changed_opcode_rejected(self):
        self.altered(lambda a:a['graph']['nodes'][0].update(hex='f0bd'))

    def test_changed_instruction_address_rejected(self):
        self.altered(lambda a:a['graph']['nodes'][1].update(address=m.START+4))

    def test_changed_successor_rejected(self):
        self.altered(lambda a:a['graph']['nodes'][0].update(successors=[]))

    def test_changed_bx_register_rejected(self):
        self.altered(lambda a:a['graph']['nodes'][2].update(register=1))

    def test_changed_hash_rejected(self):
        self.altered(lambda a:a['sampled_ranges'][0].update(sha256='0'*64))

    def test_changed_window_rejected(self):
        self.altered(lambda a:a['graph']['window_identity'].update(sha256='0'*64))

    def test_dropped_owner_rejected(self):
        self.altered(lambda a:a['remaining_unread_targets'].pop())

    def test_duplicate_owner_rejected(self):
        self.altered(lambda a:a['old_unread_targets'].__setitem__(0,a['old_unread_targets'][1]))

    def test_redecode_rejected(self):
        self.altered(lambda a:a['graph'].update(saved_instruction_bytes_redecoded=1))

    def test_candidate_mismatch_rejected(self):
        self.altered(lambda a:a['candidate'].update(sha256='0'*64))

    def test_overacceptance_rejected(self):
        for key in m.FALSE_KEYS:
            self.altered(lambda a,k=key:a.update({k:True}))

    def test_saved_contracts_compose_conditionally(self):
        result=m.join(self.prefix,self.body,m.program(self.prior))
        self.assertEqual(result['local_sp_deltas'],[-20,0,20])
        self.assertEqual(result['net_sp_delta_under_contract'],0)
        self.assertEqual(len(result['paths']),2)
        self.assertFalse(result['body_tail_r0_is_function_return_value'])
        self.assertFalse(result['caller_frame_integrity_discharged'])

    def test_wrong_frame_rejected(self):
        p=copy.deepcopy(self.prefix); p['analysis']['saved_register_order']=[4,5,6,7,0]
        with self.assertRaises(ValueError): m.join(p,self.body,m.program(self.prior))

    def test_wrong_inherited_argument_rejected(self):
        b=copy.deepcopy(self.body); b['analysis']['inherited_contract']['r2']='unknown'
        with self.assertRaises(ValueError): m.join(self.prefix,b,m.program(self.prior))

    def test_store_width_change_rejected(self):
        b=copy.deepcopy(self.body); b['analysis']['ordered_store_widths']=[2,2,2,2]
        with self.assertRaises(ValueError): m.join(self.prefix,b,m.program(self.prior))

    def test_unconditional_nonalias_formula_rejected(self):
        b=copy.deepcopy(self.body); b['analysis']['non_alias_formula']['valid_without_alias_preconditions']=True
        with self.assertRaises(ValueError): m.join(self.prefix,b,m.program(self.prior))

    def test_prior_indirect_edges_preserved(self):
        a=copy.deepcopy(m.program(self.prior)); a['prior_external_indirect_edges_preserved'].pop()
        with self.assertRaises(ValueError): m.join(self.prefix,self.body,a)

    def test_analyze_does_not_modify_evidence(self):
        before=copy.deepcopy(self.prior); result=m.analyze(self.prior,None)
        result['old_unread_targets'].clear()
        self.assertEqual(before,self.prior)

    def test_no_native_replay_or_unconditional_acceptance(self):
        result=m.analyze(self.prior,None)
        for key in m.FALSE_KEYS: self.assertIs(result[key],False)
        for key in ('rom_changes','new_emulator_processes','candidate_reconstructions',
                    'new_graph_decodes','accepted_native_cases_replayed','prior_abi_classifications_replayed'):
            self.assertEqual(result[key],0)
        self.assertEqual(result['remaining_unread_targets'],self.prior['analysis']['remaining_unread_targets'])
        self.assertEqual(result['unresolved_indirect_edges'],self.prior['analysis']['unresolved_indirect_edges'])
        self.assertFalse(result['conditional_tail_edge']['unconditional_target_resolved'])


if __name__ == '__main__':
    unittest.main()
