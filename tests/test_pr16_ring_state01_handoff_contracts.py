"""state0→1→2の新しい連続経路だけを検査する。"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_state01_handoff_contracts as h

class Memory:
    def data(self,at,size):
        if at==0x02000000:return b'AB'[:size]
        if at==0x02000010:return b'CD'[:size]
        raise ValueError('unexpected test address')

class HandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 継承済み単独suiteを呼び出したら失敗。新しい連続経路の入力/期待式だけ使う。
        with patch.object(h.prior,'completion_contracts',side_effect=AssertionError('old state0 replay')) as p0, \
             patch.object(h.prior,'option_contracts',side_effect=AssertionError('old option replay')) as po, \
             patch.object(h.state1,'verify',side_effect=AssertionError('old state1 replay')) as p1:
            cls.rows=h.verify();cls.old_calls=p0.call_count+po.call_count+p1.call_count
        cls.by={r['case']:r for r in cls.rows}

    def test_21_sequences(self):self.assertEqual(len(self.rows),21)
    def test_all_task_slots(self):self.assertEqual({r['task_id']for r in self.rows},set(range(16)))
    def test_states_012(self):self.assertTrue(all(r['states']==[0,1,2]for r in self.rows))
    def test_registers_each_call(self):self.assertTrue(all(r['return_sp_r4_r11_proven']for r in self.rows))
    def test_zero_host_mutation(self):self.assertTrue(all(r['host_ram_mutations_between_callbacks']==0 for r in self.rows))
    def test_live_stack_scope(self):
        self.assertTrue(all(r['same_explicit_object_ram']and r['callback_stack_frames_independent']for r in self.rows))
        self.assertTrue(all(len(r['callback_stack_bytes'])==2 and max(r['callback_stack_bytes'])<=512 for r in self.rows))
    def test_not_native_or_dma(self):
        self.assertTrue(all(not r['native_observation']and not r['bios_execution_observed']and not r['dma_execution_observed']for r in self.rows))
    def test_free_queue_handoff(self):
        for i in range(16):
            r=self.by[f'task{i}-free'];self.assertEqual(r['state0_reserved_slots'],[0,1]);self.assertEqual(r['state1_reserved_slots'],[2,3])
    def test_no_capacity_still_reaches2(self):self.assertEqual(self.by['capacity-0']['queue_plan'],[None]*4)
    def test_one_capacity(self):
        r=self.by['capacity-1'];self.assertEqual(r['state0_reserved_slots'],[0]);self.assertEqual(r['state1_reserved_slots'],[])
    def test_two_capacity(self):
        r=self.by['capacity-2'];self.assertEqual(r['state0_reserved_slots'],[0,1]);self.assertEqual(r['state1_reserved_slots'],[])
    def test_three_capacity(self):
        r=self.by['capacity-3'];self.assertEqual(r['state0_reserved_slots'],[0,1]);self.assertEqual(r['state1_reserved_slots'],[2])
    def test_wrap(self):self.assertEqual(self.by['wrap127']['queue_plan'],[127,0,1,2])
    def test_state2_exact_frontier(self):
        r=self.by['task0-free']['next_state2_boundary']
        self.assertEqual(r['stop'],['未map read',0x0937858e]);self.assertEqual(r['read_fault'],dict(address=0x0203d000,size=4,site=0x0937858e))
    def test_state2_no_invented_completion(self):
        r=self.by['task0-free']['next_state2_boundary']
        self.assertEqual(r['nonstack_writes'],0);self.assertFalse(r['config_synthesized']or r['task_deleted']or r['busy_cleared'])
    def test_accepted_suites_not_called(self):self.assertEqual(self.old_calls,0)
    def test_handoff_exact_bytes(self):
        seg=[(0x02000000,b'AB',True),(0x02000010,b'CD',False)]
        h.check_handoff(seg,Memory(),seg)
    def test_handoff_byte_mutation_rejected(self):
        seg=[(0x02000000,b'AA',True)]
        with self.assertRaisesRegex(ValueError,'host RAM'):h.check_handoff(seg,Memory(),seg)
    def test_handoff_added_region_rejected(self):
        with self.assertRaises(ValueError):h.check_handoff([],Memory(),[(0x02000000,b'AB',True)])
    def test_handoff_permission_change_rejected(self):
        with self.assertRaises(ValueError):h.check_handoff([(0x02000000,b'AB',True)],Memory(),[(0x02000000,b'AB',False)])
    def test_handoff_order_change_rejected(self):
        seg=[(0x02000000,b'AB',True),(0x02000010,b'CD',False)]
        with self.assertRaises(ValueError):h.check_handoff(seg,Memory(),seg[::-1])
    def test_queue_invalid_arguments(self):
        for head,count in((-1,4),(128,4),(True,4),(0,5),(0,-1)):
            with self.assertRaises(ValueError):h.queue_slots(head,(),count)
        for occupied in((-1,),(128,),(True,)):
            with self.assertRaises(ValueError):h.queue_slots(0,occupied)
    def test_queue_holes_without_duplicates(self):
        self.assertEqual(h.queue_slots(126,(126,0,2)),[127,1,3,4])
        self.assertEqual(h.queue_slots(0,(),0),[])
    def test_final_image_records_all_phases(self):
        for r in self.rows:
            self.assertNotEqual(r['state1_input_sha256'],r['final_object_sha256'])
            self.assertEqual(len(r['combined_write_identity']['sha256']),64)
            self.assertGreater(r['state1_write_count'],r['state0_write_count'])

if __name__=='__main__':unittest.main()
