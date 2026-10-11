"""新規有限採取だけの計画・metadata・既知BIOS分類検査。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_audio_tail_bytes as t

class AudioTailBytesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis']
        raw=bytearray(t.TABLE-t.leaf.ROM_BASE+30)
        raw[-30:]=b''.join(i.to_bytes(2,'little')for i in range(15))
        at=t.BIOS-t.leaf.ROM_BASE;raw[at:at+4]=bytes.fromhex('0bdf7047');cls.raw=bytes(raw)
    def reject(self,mutate):
        a=copy.deepcopy(self.a);mutate(a)
        with self.assertRaises(ValueError):t.plan(self.nodes,a,self.context)
    def test_exact_roots(self):self.assertEqual(t.plan(self.nodes,self.a,self.context)['roots'],list(t.ROOTS))
    def test_finite_frequency_indices(self):self.assertEqual(t.plan(self.nodes,self.a,self.context)['frequency_window']['selected_indices'],list(range(1,16)))
    def test_no_recursive_calls(self):self.assertEqual(t.plan(self.nodes,self.a,self.context)['direct_recursive_layers'],0)
    def test_count_mutation(self):self.reject(lambda a:a.update(contract_cases=341))
    def test_prevent_repeat_sample(self):self.reject(lambda a:a.update(frequency_table_observed=True))
    def test_pending_mutation(self):self.reject(lambda a:a.update(pending_direct_callees=[]))
    def test_native_not_promoted(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_dma_not_promoted(self):self.reject(lambda a:a.update(dma_execution_observed=True))
    def test_candidate_mutation(self):self.reject(lambda a:a['candidate'].update(crc32='00000000'))
    def test_callsite_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x081c1738)['target']=0
        with self.assertRaises(ValueError):t.plan(nodes,self.a,self.context)
    def test_literal_mutation(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x081c1568)['literal_value']=0
        with self.assertRaises(ValueError):t.plan(nodes,self.a,self.context)
    def test_frequency_values(self):self.assertEqual(t.frequency_window(self.raw)['values'],list(range(15)))
    def test_frequency_identity(self):
        r=t.frequency_window(self.raw);self.assertEqual(r['identity'],t.s.identity(bytes.fromhex(r['hex'])))
    def test_table_length_not_claimed(self):self.assertFalse(t.frequency_window(self.raw)['actual_table_length_proven'])
    def test_all_modes_not_claimed(self):self.assertFalse(t.frequency_window(self.raw)['all_selected_indices_valid_proven'])
    def test_index_zero_not_sampled(self):
        r=t.frequency_window(self.raw);self.assertFalse(r['index_zero_sampled']);self.assertEqual(r['index_zero_address'],t.TABLE-2)
    def test_frequency_truncation(self):
        with self.assertRaises(ValueError):t.frequency_window(self.raw[:-1])
    def test_bios_prefix(self):
        r=t.bios_prefix(self.raw);self.assertTrue(r['first_is_swi']);self.assertEqual(r['swi_number'],11);self.assertTrue(r['second_is_bx_lr'])
    def test_bios_unexecuted(self):
        r=t.bios_prefix(self.raw);self.assertFalse(r['executed']);self.assertFalse(r['return_proven'])
    def test_unknown_bios_remains_unknown(self):
        raw=bytearray(self.raw);at=t.BIOS-t.leaf.ROM_BASE;raw[at:at+4]=bytes(4)
        r=t.bios_prefix(bytes(raw));self.assertFalse(r['first_is_swi']);self.assertIsNone(r['swi_number'])
    def test_known_bios_call_classification(self):
        row={'kind':'unread_call','site':8,'target':t.BIOS|1}
        result=t.classify_pending([row],[],set(),[t.bios_prefix(self.raw)])[0]
        self.assertEqual(result['kind'],'bios_swi_boundary');self.assertEqual(result['original_kind'],'unread_call')
    def test_decoder_rejection_classification(self):
        row={'kind':'decoder_rejection','site':t.BIOS,'encoded':'0bdf'}
        result=t.classify_pending([], [row],set(),[t.bios_prefix(self.raw)])[0]
        self.assertEqual(result['kind'],'bios_swi_boundary');self.assertFalse(result['return_proven'])
    def test_other_pending_preserved(self):
        row={'kind':'unread_call','site':8,'target':t.BIOS+9}
        self.assertEqual(t.classify_pending([row],[],set(),[t.bios_prefix(self.raw)]),[row])
    def test_indirect_not_resolved(self):
        row={'kind':'indirect_boundary','site':8,'register':3}
        self.assertEqual(t.classify_pending([row],[],set(),[t.bios_prefix(self.raw)]),[row])
    def test_known_native_node_resolves_direct_only(self):
        row={'kind':'unread_call','site':8,'target':13}
        self.assertEqual(t.classify_pending([row],[],{12},[]),[])
    def test_promoted_bios_rejected(self):
        bios=t.bios_prefix(self.raw);bios['executed']=True
        with self.assertRaises(ValueError):t.classify_pending([{'kind':'unread_call','site':8,'target':t.BIOS|1}],[],set(),[bios])
    def test_pending_input_unchanged(self):
        old=copy.deepcopy(self.a['pending_boundaries']);t.classify_pending(old,[],set(),[self.a['bios_prefix']])
        self.assertEqual(old,self.a['pending_boundaries'])
    def test_plan_input_unchanged(self):
        a=copy.deepcopy(self.a);t.plan(self.nodes,a,self.context);self.assertEqual(a,self.a)

if __name__=='__main__':unittest.main()
