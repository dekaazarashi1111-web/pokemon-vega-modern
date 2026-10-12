"""順序付きstoreモデル、保存境界、3種類のalias反例を検証する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_external3_body_abi as m

class External3BodyAbi(unittest.TestCase):
    def setUp(self):self.prior=m.s.load(m.PRIOR)
    def reject(self):
        with self.assertRaises(ValueError):m.program(self.prior)
    def test_saved_program(self):self.assertEqual(m.program(self.prior)['sampled_instruction_bytes'],40)
    def test_candidate_drift(self):
        self.prior['analysis']['candidate']['sha256']='0'*64;self.reject()
    def test_opcode_drift(self):
        self.prior['analysis']['graph']['nodes'][1]['hex']='0000';self.reject()
    def test_range_hash_drift(self):
        self.prior['analysis']['sampled_ranges'][0]['sha256']='0'*64;self.reject()
    def test_successor_drift(self):
        self.prior['analysis']['graph']['nodes'][0]['successors']=[];self.reject()
    def test_write_annotation_drift(self):
        self.prior['analysis']['graph']['nodes'][1]['memory_write']=False;self.reject()
    def test_window_drift(self):
        self.prior['analysis']['graph']['window']=40;self.reject()
    def test_frontier_cannot_disappear(self):
        self.prior['analysis']['remaining_unread_targets'].remove(m.TAIL);self.reject()
    def test_no_overclaim(self):
        for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                    'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
            p=copy.deepcopy(self.prior);p['analysis'][key]=True
            with self.assertRaises(ValueError):m.program(p)
    def test_saved_prefix_contract(self):
        p=m.s.load(m.PREFIX)['analysis'];self.assertEqual(m.join(p)['frame_bytes_live'],20)
        p['continuation_contract']['r12']='not normalized'
        with self.assertRaises(ValueError):m.join(p)
    def test_nonalias_sweep(self):
        r=m.sweep();self.assertEqual(r['independent_local_boundary_cases'],65536)
        self.assertTrue(r['all_u8_modes_covered']);self.assertEqual(r['non_alias_record_address'],0x02010000)
    def test_mode_truncated_to_bit0_for_store(self):
        for mode in range(256):
            regs,mem=m.inputs(mode=mode,key=0x1234);r=m.execute(regs,mem)
            self.assertEqual(m.half(r['memory'],regs[2]),0x1234|((mode&1)<<15))
    def test_ordered_stores(self):
        regs,mem=m.inputs(index=1,key=0xffff,mode=0,value=0x1234)
        r=m.execute(regs,mem);e=regs[2]
        self.assertEqual([w['site'] for w in r['writes']],[m.START+o for o in m.WRITE_OFFSETS])
        self.assertEqual([w['size'] for w in r['writes']],[2,1,2,2])
        self.assertEqual([w['value'] for w in r['writes']],[65535,127,0x1234,2])
        self.assertEqual([w['address'] for w in r['writes']],[e,e+1,e+2,m.COUNTER])
    def test_counter_and_base_reload_order(self):
        regs,mem=m.inputs();r=m.execute(regs,mem)
        self.assertEqual([q['address'] for q in r['reads']],[m.COUNTER,regs[2]+1,m.COUNTER,m.BASE_PTR,m.COUNTER])
    def test_counter_alias_retargets_later_stores(self):
        r=m.alias_diagnostics()['record_aliases_counter']
        self.assertEqual([w['address'] for w in r['writes']],[m.COUNTER,m.COUNTER+5,m.COUNTER+6,m.COUNTER])
        self.assertFalse(r['observed']);self.assertFalse(r['single_record_address_formula_valid'])
    def test_base_pointer_alias_reloaded(self):
        r=m.alias_diagnostics()['record_aliases_base_pointer']
        self.assertEqual(r['writes'][2]['address'],0x03002002);self.assertFalse(r['observed'])
    def test_value_alias_changes_counter_increment(self):
        r=m.alias_diagnostics()['value_aliases_counter']
        self.assertEqual(r['writes'][2]['value'],21530);self.assertEqual(r['writes'][3]['value'],21531)
        self.assertFalse(r['observed'])
    def test_counter_wrap_and_untruncated_r0(self):
        regs,mem=m.inputs(index=65535,base=(0x02010000-4*65535)&m.MASK)
        r=m.execute(regs,mem);self.assertEqual(m.half(r['memory'],m.COUNTER),0)
        self.assertEqual(r['registers'][0],65536)
    def test_preserved_registers_and_live_frame(self):
        regs,mem=m.inputs();regs[8:12]=[0x88888888,9,10,11];r=m.execute(regs,mem)
        self.assertEqual(r['registers'][4:],regs[4:]);self.assertEqual(r['local_sp_delta'],0)
        self.assertFalse(r['boundary_executed'])
    def test_missing_or_unaligned_memory_rejected(self):
        regs,mem=m.inputs();del mem[m.COUNTER]
        with self.assertRaises(ValueError):m.execute(regs,mem)
        regs,mem=m.inputs();regs[2]+=1
        with self.assertRaises(ValueError):m.execute(regs,mem)
    def test_input_validation(self):
        for v in (-1,65536,True,1.0):
            with self.assertRaises(ValueError):m.inputs(index=v)
        regs,mem=m.inputs();regs[12]=True
        with self.assertRaises(ValueError):m.execute(regs,mem)
    def test_analysis_does_not_replay_prefix(self):
        r=m.analyze(self.prior,Path('.local/not-used'))
        self.assertTrue(r['saved_prefix_reused_not_executed']);self.assertEqual(r['inherited_frame_bytes_live'],20)
        self.assertEqual(r['priority_unread_targets'],[m.TAIL])
        self.assertFalse(r['non_alias_formula']['valid_without_alias_preconditions'])
        for key in ('new_emulator_processes','candidate_reconstructions','new_graph_decodes','prior_abi_classifications_replayed'):
            self.assertEqual(r[key],0)

if __name__=='__main__':unittest.main()
