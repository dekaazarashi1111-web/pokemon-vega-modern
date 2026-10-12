"""保存前半のみ。未読境界へ進めず分岐/正規化/stack aliasを検証する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_external3_abi as m

class External3Abi(unittest.TestCase):
    def setUp(self):self.prior=m.s.load(m.PRIOR)
    def reject(self):
        with self.assertRaises(ValueError):m.program(self.prior)
    def test_saved_program(self):self.assertEqual(m.program(self.prior)['sampled_instruction_bytes'],64)
    def test_candidate_drift(self):
        self.prior['analysis']['candidate']['sha256']='0'*64;self.reject()
    def test_opcode_drift(self):
        self.prior['analysis']['graph']['nodes'][1]['hex']='0000';self.reject()
    def test_literal_drift(self):
        next(n for n in self.prior['analysis']['graph']['nodes'] if 'literal_value' in n)['literal_value']+=1;self.reject()
    def test_range_hash_drift(self):
        self.prior['analysis']['sampled_ranges'][0]['sha256']='0'*64;self.reject()
    def test_successor_drift(self):
        self.prior['analysis']['graph']['nodes'][0]['successors']=[];self.reject()
    def test_write_annotation_drift(self):
        self.prior['analysis']['graph']['nodes'][0]['memory_write']=False;self.reject()
    def test_tail_boundary_drift(self):
        self.prior['analysis']['graph']['external_edges'][0]['target']+=2;self.reject()
    def test_window_drift(self):
        self.prior['analysis']['graph']['window']=66;self.reject()
    def test_frontier_cannot_disappear(self):
        self.prior['analysis']['remaining_unread_targets'].remove(m.TAIL);self.reject()
    def test_no_overclaim(self):
        for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                    'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
            p=copy.deepcopy(self.prior);p['analysis'][key]=True
            with self.assertRaises(ValueError):m.program(p)
    def test_boundary_and_normalization_sweep(self):
        self.assertEqual(m.sweep(),{'gate_boundary_cases':2401,'normalization_cases':65536,
            'covered_instruction_count':32,'conditional_outcomes':6,'new_emulator_processes':0})
    def test_lazy_zero_count_only_reads_count(self):
        mem=m.snapshot(count=0);keep={m.COUNT, m.COUNT+1}
        r=m.execute(0,0,0,{at:b for at,b in mem.items() if at in keep})
        self.assertEqual(r['boundary'],m.TAIL);self.assertEqual(len(r['reads']),1)
    def test_count_unsigned_above_limit(self):
        r=m.execute(0,0,0,m.snapshot(count=65535,limit=32768))
        self.assertEqual(r['boundary'],m.TAIL);self.assertEqual(len(r['reads']),2)
    def test_index_capacity_gate(self):
        r=m.execute(0,0,0,m.snapshot(index=32768,capacity=32767))
        self.assertEqual(r['boundary'],m.TAIL);self.assertEqual(len(r['reads']),4)
    def test_continuation_register_contract(self):
        r=m.execute(0xabcdef03,0x1234ffff,0xfff00001,m.snapshot(index=1,capacity=2,record=0x8888))
        regs=r['registers'];self.assertEqual(r['boundary'],m.CONT)
        self.assertEqual([regs[i] for i in (0,1,2,3,4,5,6,7,12)],
                         [0x8000,0x7fff,0x02010004,0x8888,0x02010000,m.BASE_PTR,m.COUNTER,3,1])
        self.assertEqual(r['local_sp_delta'],-20);self.assertFalse(r['boundary_executed'])
    def test_push_order_and_no_other_writes(self):
        r=m.execute(0,0,0,m.snapshot(),sp=0x03007000,lr=0x09123457,preserved=(100,200,300,400))
        self.assertEqual([w['register'] for w in r['writes']],[4,5,6,7,14])
        self.assertEqual([w['value'] for w in r['writes']],[100,200,300,400,0x09123457])
        self.assertEqual([w['address'] for w in r['writes']],[0x03006fec+4*i for i in range(5)])
    def test_push_alias_diagnostic_not_observation(self):
        r=m.alias_diagnostic();self.assertEqual(r['index_after_push'],0x0810)
        self.assertEqual(r['alias_boundary'],m.TAIL);self.assertFalse(r['observed'])
    def test_unprovided_memory_rejected(self):
        mem=m.snapshot();del mem[m.COUNT]
        with self.assertRaises(ValueError):m.execute(0,0,0,mem)
    def test_input_and_stack_validation(self):
        for invalid in (-1,1<<32,True,1.2):
            with self.assertRaises(ValueError):m.execute(invalid,0,0,m.snapshot())
        for sp in (0,19,22,1<<32,True):
            with self.assertRaises(ValueError):m.execute(0,0,0,m.snapshot(),sp=sp)
    def test_wrapped_pointer_is_model_only(self):
        r=m.execute(0,0,0,m.snapshot(index=1,capacity=2,base=0xfffffffc))
        self.assertEqual(r['registers'][2],0);self.assertEqual(r['boundary'],m.CONT)
    def test_analysis_saved_only(self):
        r=m.analyze(self.prior,Path('.local/not-used'))
        self.assertEqual(r['priority_unread_targets'],[m.CONT,m.TAIL])
        self.assertEqual(r['frame_bytes_live'],20)
        for key in ('new_graph_decodes','candidate_reconstructions','new_emulator_processes','prior_abi_classifications_replayed'):
            self.assertEqual(r[key],0)
        for key in ('early_exit_is_return_proven','return_value_proven','saved_slot_preservation_proven','ring_acquisition_accepted'):
            self.assertFalse(r[key])

if __name__=='__main__':unittest.main()
