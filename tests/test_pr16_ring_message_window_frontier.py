"""成功済み契約を実行せず、限定採取の出自・data分離・重複拒否を検証する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_window_frontier as m

class FrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=m.saved_inputs()
    def mutate(self,change):
        c=copy.deepcopy(self.c);change(c)
        with self.assertRaises(ValueError):m.plan(c)
    def test_roots(self):self.assertEqual(m.plan(self.c)['direct_roots'],list(m.DIRECT))
    def test_one_word_only(self):self.assertEqual(m.plan(self.c)['table_word_bytes'],4)
    def test_no_replay(self):self.assertEqual(m.plan(self.c)['accepted_contract_cases_replayed'],0)
    def test_no_recursive_calls(self):self.assertIs(m.plan(self.c)['expand_direct_calls'],False)
    def test_candidate(self):self.mutate(lambda c:c['task_contracts'].update(candidate={}))
    def test_contract_count(self):self.mutate(lambda c:c['task_contracts'].update(contract_cases=1230))
    def test_return_count(self):self.mutate(lambda c:c['task_contracts'].update(conditional_return_cases=915))
    def test_stop_count(self):self.mutate(lambda c:c['task_contracts'].update(pending_stop_cases=316))
    def test_state2_sequence_count(self):self.mutate(lambda c:c['task_contracts'].update(same_ram_state2_sequences=95))
    def test_selector(self):self.mutate(lambda c:c['task_contracts']['pending_window_attribute'].update(needed_selector=1))
    def test_already_observed(self):self.mutate(lambda c:c['task_contracts']['pending_window_attribute'].update(table_word_observed=True))
    def test_palette(self):self.mutate(lambda c:c['task_contracts'].update(pending_palette_entry=0))
    def test_thunk(self):self.mutate(lambda c:c['task_contracts'].update(pending_frame_thunk=0))
    def test_callback(self):self.mutate(lambda c:c['task_contracts'].update(saved_frame_callback=0))
    def test_full_task_boundary(self):self.mutate(lambda c:c['task_contracts']['task_full_boundary'].update(liveness_proven=True))
    def test_no_acceptance_promotion(self):
        for k in m.FALSE:
            with self.subTest(key=k):self.mutate(lambda c:c['task_contracts'].__setitem__(k,True))
    def test_opcode_origin(self):
        for at in (0x08004930,0x08004932,0x08153068,0x08004840):
            with self.subTest(site=at):self.mutate(lambda c:next(n for n in c['nodes'] if n['address']==at).__setitem__('hex','0000'))
    def test_literal_origin(self):self.mutate(lambda c:next(n for n in c['nodes'] if n['address']==0x0800492c).__setitem__('literal_value',0))
    def test_call_origin(self):self.mutate(lambda c:next(n for n in c['nodes'] if n['address']==0x08004872).__setitem__('target',0))
    def test_even_mov_pc_target(self):self.assertEqual(m.table_target((0x08004958).to_bytes(4,'little')),0x08004958)
    def test_word_lengths(self):
        for n in (0,1,2,3,5,32):
            with self.subTest(size=n),self.assertRaises(ValueError):m.table_target(bytes(n))
    def test_word_type(self):
        with self.assertRaises(ValueError):m.table_target(bytearray(4))
    def test_target_ranges(self):
        for at in (0,0x02000000,0x0a000000,0xffffffff,0x08004959,m.TABLE,m.TABLE+30):
            with self.subTest(target=at),self.assertRaises(ValueError):m.table_target(at.to_bytes(4,'little'))
    def result(self):
        return {'initial_roots':sorted((*m.DIRECT,0x08004959)),'saved_roots_reused':[],
            'saved_nodes_redecoded':0,'direct_calls_recursively_expanded':0,
            'new_nodes':[dict(address=0x08004958,size=2,hex='7047',kind='indirect')]}
    def test_fresh_nodes(self):self.assertIn(0x08004958,m.validate_new(self.result(),self.c,0x08004958))
    def test_saved_decode_rejected(self):
        r=self.result();r['saved_nodes_redecoded']=1
        with self.assertRaises(ValueError):m.validate_new(r,self.c,0x08004958)
    def test_extra_roots_rejected(self):
        r=self.result();r['initial_roots'].append(0x08000001)
        with self.assertRaises(ValueError):m.validate_new(r,self.c,0x08004958)
    def test_data_decode_rejected(self):
        r=self.result();r['new_nodes'][0]['address']=m.TABLE
        with self.assertRaises(ValueError):m.validate_new(r,self.c,0x08004958)
    def test_old_node_rejected(self):
        r=self.result();r['new_nodes']=[self.c['nodes'][0]]
        with self.assertRaises(ValueError):m.validate_new(r,self.c,0x08004958)
    def test_duplicate_node_rejected(self):
        r=self.result();r['new_nodes']*=2
        with self.assertRaises(ValueError):m.validate_new(r,self.c,0x08004958)
    def test_wrong_byte_length(self):
        r=self.result();r['new_nodes'][0]['hex']='00'
        with self.assertRaises(ValueError):m.validate_new(r,self.c,0x08004958)

if __name__=='__main__':unittest.main()
