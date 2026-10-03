"""保存UI/heapの境界と合成契約。既存nativeや旧単独ABIを再実行しない。"""
from __future__ import annotations
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_ui_contracts as task


class ContractTests(unittest.TestCase):
    def group(self,name,*,returned=None):
        rows=task.run_group(name)
        self.assertTrue(rows)
        self.assertEqual(len({r['case']for r in rows}),len(rows))
        self.assertTrue(all(r['return_sp_r4_r11_proven']==r['returned']for r in rows))
        if returned is not None:self.assertTrue(all(r['returned']is returned for r in rows))
        return rows
    def test_deactivate(self):self.group('deactivate',returned=True)
    def test_full_pool(self):self.group('full_pool',returned=True)
    def test_nosplit_allocation(self):self.group('allocate',returned=True)
    def test_allocation_partial_stops(self):self.group('allocation_stops',returned=False)
    def test_free_and_coalescing(self):self.group('free_heap',returned=True)
    def test_invalid_free_stops(self):self.group('free_stops',returned=False)
    def test_empty_initialization(self):self.group('init_empty',returned=True)
    def test_initialization_shortage(self):
        rows=self.group('init_stops')
        self.assertTrue(any(r['returned']for r in rows))
        self.assertTrue(any(not r['returned']for r in rows))
    def test_window_allocation(self):self.group('add_window',returned=True)
    def test_window_allocation_stops(self):
        rows=self.group('add_stops')
        self.assertTrue(any(r['returned']for r in rows))
        self.assertTrue(any(not r['returned']for r in rows))
    def test_window_removal(self):self.group('remove_window')
    def test_free_all(self):self.group('free_all',returned=True)
    def test_real_text_hook(self):
        rows=self.group('run_text')
        self.assertTrue(any(r['returned']for r in rows))
        self.assertTrue(any(r['stop']==['保存node境界で停止',task.THUNK]for r in rows))
    def test_word_boundaries(self):
        self.assertEqual(task.word(0),bytes(4))
        self.assertEqual(task.word(0xffffffff),b'\xff'*4)
    def test_word_rejects_non_u32(self):
        for value in (-1,1<<32,True,1.0,'1',None):
            with self.subTest(value=value),self.assertRaises(ValueError):task.word(value)
    def test_template_layout(self):
        self.assertEqual(task.template(3,(254,255)),bytes((3,3,5,254,255,7,9,0)))
    def test_template_rejects_bg(self):
        for bg in (-1,256,True,None):
            with self.subTest(bg=bg),self.assertRaises(ValueError):task.template(bg)
    def test_template_rejects_dimensions(self):
        for dims in ((0,),(),(0,0,0),(-1,0),(0,256),(True,0)):
            with self.subTest(dims=dims),self.assertRaises(ValueError):task.template(dims=dims)
    def test_pool_last_slot(self):
        data=task.window_pool(31,bg=3,pointer=0x02010010)
        self.assertEqual(len(data),384)
        self.assertEqual([data[12*i]for i in range(32)],[3]*31+[255])
        self.assertEqual(data[-4:],task.word(0x02010010))
    def test_full_pool_image(self):
        data=task.window_pool(None,bg=254)
        self.assertEqual([data[12*i]for i in range(32)],[254]*32)
    def test_pool_rejects_unallocated_index(self):
        for slot in (-1,32,255,True):
            with self.subTest(slot=slot),self.assertRaises(ValueError):task.window_pool(slot)
    def test_heap_header_layout(self):
        raw=task.header(1,32,0x02010000,0x02010100)
        self.assertEqual(len(raw),16)
        self.assertEqual(raw[:4],b'\x01\x00\xa3\xa3')
        self.assertEqual(raw[4:],task.word(32)+task.word(0x02010000)+task.word(0x02010100))
    def test_heap_rejects_invalid_header(self):
        for active,magic in ((-1,0xa3a3),(65536,0xa3a3),(True,0xa3a3),(1,-1),(1,65536)):
            with self.subTest(active=active,magic=magic),self.assertRaises(ValueError):
                task.header(active,32,0,0,magic)
    def test_heap_rejects_unbounded_count(self):
        for blocks in ([],[(0,32,0xa3a3)]*9,None):
            with self.subTest(blocks=blocks),self.assertRaises(ValueError):task.heap_segments(blocks)
    def test_heap_links_are_explicit(self):
        rows=task.heap_segments([(1,32,0xa3a3),(0,64,0xa3a3)])
        self.assertEqual(len(rows),4)
        self.assertEqual(rows[2][0],task.HEAP)
        self.assertEqual(rows[2][1][8:],task.word(task.HEAP+256)*2)
        self.assertEqual(rows[3][1][8:],task.word(task.HEAP)*2)
    def test_unknown_group_fails_closed(self):
        with self.assertRaises(ValueError):task.run_group('unbound-native')
    def test_saved_scope(self):
        nodes,_,a=task.saved_inputs()
        self.assertEqual(len(nodes),3918)
        self.assertEqual(a['pending_direct_callees'],[task.SPLIT|1,task.ASSERT|1,task.THUNK|1])
        self.assertIs(a['actual_callback_table_observed'],False)
        self.assertIs(a['ring_acquisition_accepted'],False)
    def test_cached_groups_do_not_replay(self):
        rows=task.run_group('full_pool')
        self.assertIs(task.run_group('full_pool'),rows)


if __name__=='__main__':unittest.main()
