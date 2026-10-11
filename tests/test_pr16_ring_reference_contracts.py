"""参照先oracleとobject/owned-frame境界。native/結合795契約をunitで重複実行しない。"""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_reference_contracts as m


def machine(*writes):return SimpleNamespace(writes=list(writes),low_sp=m.vm.SP-8)


class WriteBoundaryTests(unittest.TestCase):
    def test_owned_frame(self):self.assertEqual(m.outside_writes(machine((m.vm.SP-8,4,0)),[]),[])
    def test_below_live_frame(self):
        row=(m.vm.SP-12,4,0);self.assertEqual(m.outside_writes(machine(row),[]),[list(row)])
    def test_above_live_frame(self):
        row=(m.vm.SP,4,0);self.assertEqual(m.outside_writes(machine(row),[]),[list(row)])
    def test_cross_frame_boundary(self):
        row=(m.vm.SP-2,4,0);self.assertEqual(m.outside_writes(machine(row),[]),[list(row)])
    def test_object_write(self):self.assertEqual(m.outside_writes(machine((m.TASKS,4,0)),[(m.TASKS,640)]),[])
    def test_object_last_byte(self):self.assertEqual(m.outside_writes(machine((m.TASKS+639,1,0)),[(m.TASKS,640)]),[])
    def test_cross_object_boundary(self):
        row=(m.TASKS+639,2,0);self.assertEqual(m.outside_writes(machine(row),[(m.TASKS,640)]),[list(row)])
    def test_stack_cannot_be_object(self):
        with self.assertRaises(ValueError):m.outside_writes(machine(),[(m.vm.STACK_LO,4)])
    def test_empty_object_rejected(self):
        with self.assertRaises(ValueError):m.outside_writes(machine(),[(m.TASKS,0)])
    def test_invalid_slot255_detected(self):
        row=(m.TASKS+255*40+5,1,254)
        self.assertTrue(m.vm.STACK_LO<=row[0]<m.vm.SP-8)
        self.assertEqual(m.outside_writes(machine(row),[(m.TASKS,640)]),[list(row)])


class TaskOracleTests(unittest.TestCase):
    def test_empty_size(self):self.assertEqual(len(m.task_input([],[],0,0)),640)
    def test_active_not_added(self):self.assertEqual(m.task_expected([],[],0,0)[0][4],0)
    def test_empty_order(self):self.assertEqual(m.task_expected([],[],2,9)[2],[2])
    def test_empty_writes(self):self.assertEqual(m.task_expected([],[],2,9)[1],[(m.TASKS+85,1,254),(m.TASKS+86,1,255)])
    def test_before_head(self):self.assertEqual(m.task_expected([1,4],[10,50],0,0)[2],[0,1,4])
    def test_between(self):self.assertEqual(m.task_expected([1,4],[10,50],0,30)[2],[1,0,4])
    def test_after_tail(self):self.assertEqual(m.task_expected([1,4],[10,50],0,255)[2],[1,4,0])
    def test_stable_equal(self):self.assertEqual(m.task_expected([1,4,7],[10,50,50],0,50)[2],[1,4,7,0])
    def test_neighbor_writes(self):
        self.assertEqual(m.task_expected([1,4],[10,50],0,30)[1],[(m.TASKS+5,1,1),(m.TASKS+6,1,4),(m.TASKS+46,1,0),(m.TASKS+165,1,0)])
    def test_only_link_bytes_change(self):
        before=m.task_input([1,4],[10,50],0,30);after,_,_=m.task_expected([1,4],[10,50],0,30)
        self.assertEqual([i for i,(a,b)in enumerate(zip(before,after))if a!=b],[5,6,46,165])
    def test_target_bounds(self):
        for target in (-1,16,255,True):
            with self.assertRaises(ValueError):m.task_input([],[],target,0)
    def test_existing_target(self):
        with self.assertRaises(ValueError):m.task_input([1],[10],1,0)
    def test_duplicate_chain(self):
        with self.assertRaises(ValueError):m.task_input([1,1],[10,10],0,0)
    def test_unsorted_priority(self):
        with self.assertRaises(ValueError):m.task_input([1,4],[50,10],0,0)
    def test_chain_size_mismatch(self):
        with self.assertRaises(ValueError):m.task_input([1,4],[10],0,0)
    def test_bad_priority(self):
        for p in (-1,256,True):
            with self.assertRaises(ValueError):m.task_input([],[],0,p)
    def test_head_none(self):self.assertEqual(m.head_expected(m.task_input([],[],0,0)),16)
    def test_head_first(self):self.assertEqual(m.head_expected(m.task_input([4,1],[0,9],0,0)),4)
    def test_head_requires_exact_active(self):
        data=bytearray(m.task_input([4],[0],0,0));data[4*40+4]=2;self.assertEqual(m.head_expected(bytes(data)),16)
    def test_head_requires_marker(self):
        data=bytearray(m.task_input([4],[0],0,0));data[4*40+5]=255;self.assertEqual(m.head_expected(bytes(data)),16)
    def test_head_length(self):
        with self.assertRaises(ValueError):m.head_expected(bytes(639))


class ReferenceOracleTests(unittest.TestCase):
    def test_gender_zero(self):self.assertEqual(m.getter_expected(5,0),0x083dd1dd)
    def test_gender_nonzero(self):self.assertEqual(m.getter_expected(5,255),0x083dd1e0)
    def test_rival_explicit(self):self.assertEqual(m.getter_expected(6,0,49),m.SB1+0x3a4c)
    def test_rival_fallback(self):self.assertEqual(m.getter_expected(6,1,255),0x083dd20c)
    def test_save_pointer(self):self.assertEqual(m.getter_expected(1,sb2=0x02008000),0x02008000)
    def test_invalid_getter(self):
        for index in (-1,14,True):
            with self.assertRaises(ValueError):m.getter_expected(index)
    def test_invalid_gender(self):
        with self.assertRaises(ValueError):m.getter_expected(5,256)
    def test_fd_intermediate_terminator(self):
        self.assertEqual(m.expanded_fd_writes(100,bytes([17,255])),[(100,1,80),(101,1,17),(102,1,255),(102,1,96),(103,1,255)])
    def test_fd_empty_name(self):self.assertEqual(m.expanded_fd_writes(100,b'\xff'),[(100,1,80),(101,1,255),(101,1,96),(102,1,255)])
    def test_fd_unterminated(self):
        with self.assertRaises(ValueError):m.expanded_fd_writes(100,b'abc')
    def test_fd_early_terminator(self):
        with self.assertRaises(ValueError):m.expanded_fd_writes(100,b'\xff\xff')
    def test_window_count(self):self.assertEqual(len(m.text_windows()),11)
    def test_window_bytes(self):self.assertEqual(sum(t['length']for t in m.text_windows()),83)
    def test_windows_disjoint(self):
        rows=m.text_windows();self.assertTrue(all(a['start']+a['length']<=b['start']for a,b in zip(rows,rows[1:])))
    def test_windows_bounded(self):self.assertTrue(all(1<=r['length']<=32 for r in m.text_windows()))
    def test_no_resample_fallback(self):self.assertGreater(min(r['start']for r in m.text_windows()),0x083dd1dc)
    def test_old_context_rejected(self):
        with self.assertRaisesRegex(ValueError,'保存node件数'):m.verify([],{'cached_node_count':1752,'new_node_count':107})


if __name__=='__main__':unittest.main()
