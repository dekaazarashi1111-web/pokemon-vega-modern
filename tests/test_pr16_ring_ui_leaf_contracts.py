"""新規heap分割・実描画境界の契約と故障注入。旧733条件/nativeは実行しない。"""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_ui_leaf_contracts as task
b=task.base


class ContractTests(unittest.TestCase):
    def group(self,name,count,returned=None):
        rows=task.run_group(name)
        self.assertEqual(len(rows),count)
        self.assertEqual(len({r['case']for r in rows}),count)
        self.assertTrue(all(r['returned']==r['return_sp_r4_r11_proven']for r in rows))
        if returned is not None:self.assertTrue(all(r['returned']is returned for r in rows))
        return rows
    def test_split_contiguous_heap(self):self.group('split',306,True)
    def test_split_release_coalescing(self):self.group('split_release',90,True)
    def test_split_partial_write_boundaries(self):self.group('split_partial',30,False)
    def test_assert_prefix_not_return(self):self.group('assert_prefix',10,False)
    def test_window_split(self):self.group('window_split',9,True)
    def test_init_window_two_allocations(self):self.group('init_window',3,True)
    def test_actual_renderer_missing_data(self):self.group('render_missing',128,False)
    def test_actual_renderer_table_bounds(self):self.group('render_table_bounds',30,False)
    def test_arm_callback_not_stubbed(self):self.group('render_arm_reject',3,False)
    def test_groups_are_cached_without_replay(self):
        first=task.run_group('window_split')
        self.assertIs(first,task.run_group('window_split'))
    def test_unknown_group_fails_closed(self):
        with self.assertRaisesRegex(ValueError,'契約group'):task.run_group('native-success')
    def test_saved_pending_scope(self):
        nodes,_,a=task.saved_inputs()
        self.assertEqual(len(nodes),3955)
        self.assertEqual(a['pending_direct_callees'],[task.LOG|1,task.FATAL|1])
        self.assertIs(a['actual_callback_table_observed'],False)
        self.assertIs(a['ring_acquisition_accepted'],False)


class ModelTests(unittest.TestCase):
    def test_arena_is_contiguous(self):
        segs,pos=task.arena([(1,16),(0,64),(1,0)])
        self.assertEqual(pos,[b.HEAP,b.HEAP+32,b.HEAP+112])
        self.assertEqual(len(segs[-1][1]),128)
        e=task.Expected(segs)
        self.assertEqual([e.read(p+12,4)for p in pos],[pos[1],pos[2],pos[0]])
        self.assertEqual([e.read(p+8,4)for p in pos],[pos[2],pos[0],pos[1]])
    def test_arena_size_limit(self):
        segs,_=task.arena([(0,4096)])
        self.assertEqual(len(segs[-1][1]),4112)
    def test_arena_rejects_count(self):
        for blocks in ([],None,[(0,32)]*5):
            with self.subTest(blocks=blocks),self.assertRaises(ValueError):task.arena(blocks)
    def test_arena_rejects_non_binary_active(self):
        for active in (-1,2,True,1.0):
            with self.subTest(active=active),self.assertRaises(ValueError):task.arena([(active,32)])
    def test_arena_rejects_invalid_size(self):
        for size in (-4,1,3,4097,8192,True,4.0):
            with self.subTest(size=size),self.assertRaises(ValueError):task.arena([(0,size)])
    def test_split_preserves_nonheader_payload(self):
        segs,_=task.arena([(0,128)])
        before=task.Expected(segs);e=task.Expected(segs);pointer=e.split(b.HEAP,31)
        self.assertEqual(pointer,b.HEAP+16)
        for p in range(pointer,pointer+32):self.assertEqual(e.mem[p],before.mem[p])
        for p in range(pointer+48,b.HEAP+144):self.assertEqual(e.mem[p],before.mem[p])
        self.assertEqual(e.read(b.HEAP+4,4),32)
        self.assertEqual(e.read(b.HEAP+48+4,4),80)
    def test_split_rejects_non_u32(self):
        for request in (-1,1<<32,True,1.0):
            with self.subTest(request=request),self.assertRaisesRegex(ValueError,'request u32'):
                task.Expected(task.arena([(0,64)])[0]).split(b.HEAP,request)
    def test_nosplit_is_outside_new_model(self):
        e=task.Expected(task.arena([(0,32)])[0])
        with self.assertRaisesRegex(ValueError,'今回split条件だけ'):e.split(b.HEAP,32)
    def test_exhaustion_is_not_success(self):
        segs,pos=task.arena([(1,32),(1,16)])
        e=task.Expected(segs);self.assertIsNone(e.split(b.HEAP,1))
        self.assertEqual(e.writes,[(b.GLOBALS,4,pos[0]),(b.GLOBALS+4,4,pos[0]),(b.GLOBALS+4,4,pos[1])])
    def test_images_preserve_permissions_and_contents(self):
        segs,_=task.arena([(0,128)]);e=task.Expected(segs);e.split(b.HEAP,32)
        out=task.images(e,segs)
        self.assertEqual([(p,len(d),w)for p,d,w in out],[(p,len(d),w)for p,d,w in segs])
        for p,data,_ in out:self.assertEqual(data,bytes(e.mem[p+i]for i in range(len(data))))
    def test_render_rejects_slot(self):
        for slot in (-1,32,255,True):
            with self.subTest(slot=slot),self.assertRaises(ValueError):task.render_segments(slot,0)
    def test_render_rejects_selector(self):
        for selector in (-1,256,True):
            with self.subTest(selector=selector),self.assertRaises(ValueError):task.render_segments(0,selector)
    def test_render_rejects_fast(self):
        for fast in (-1,2,True):
            with self.subTest(fast=fast),self.assertRaises(ValueError):task.render_segments(0,0,fast)
    def test_render_table_is_bounded_readonly(self):
        for table in (b'',bytes(49),bytearray(12),'x'):
            with self.subTest(table=table),self.assertRaises(ValueError):task.render_segments(0,0,table=table)
        segs=task.render_segments(31,255,1,table=bytes(24),pointer=task.TABLE)
        self.assertEqual(segs[-1],(task.TABLE,bytes(24),False))
        self.assertEqual(segs[1][1][31*32+5],255)
        self.assertEqual(segs[1][1][31*32+27],1)


class FaultInjectionTests(unittest.TestCase):
    def fixture(self):
        nodes,_,_=task.saved_inputs();segs,_=task.arena([(0,128)])
        e=task.Expected(segs);pointer=e.split(b.HEAP,32)
        return nodes,segs,e,pointer
    def test_wrong_split_active_opcode_rejected(self):
        nodes,segs,e,pointer=self.fixture();mutated=copy.deepcopy(nodes)
        target=next(n for n in mutated if n['address']==0x0800292e)
        self.assertEqual(target['hex'],'0024');target['hex']='0124'
        with self.assertRaisesRegex(ValueError,'正確順序write差分'):
            b.Cases(mutated).run('mutated-split-active',b.ALLOC2,segs,(32,),e.writes,pointer)
    def test_wrong_expected_write_order_rejected(self):
        nodes,segs,e,pointer=self.fixture();writes=list(e.writes)
        writes[-1],writes[-2]=writes[-2],writes[-1]
        with self.assertRaisesRegex(ValueError,'正確順序write差分'):
            b.Cases(nodes).run('bad-write-order',b.ALLOC2,segs,(32,),writes,pointer)
    def test_wrong_return_pointer_rejected(self):
        nodes,segs,e,pointer=self.fixture()
        with self.assertRaisesRegex(ValueError,'戻値差分'):
            b.Cases(nodes).run('bad-return',b.ALLOC2,segs,(32,),e.writes,pointer+4)
    def test_unknown_callback_cannot_return(self):
        nodes,_,_=task.saved_inputs()
        segs=task.render_segments(0,0,table=b.word(task.UNKNOWN)+bytes(8),pointer=task.TABLE)
        with self.assertRaisesRegex(ValueError,'保存node境界で停止'):
            b.Cases(nodes).run('not-success-stub',b.RUN,segs)


if __name__=='__main__':unittest.main()
