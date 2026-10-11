"""新suffixの独立oracle・全write比較・保存レジスタ拒否と限定79条件。"""
import copy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_state1_completion_contracts as t


class State1CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c,cls.a=t.inputs()

    def oracle(self,**kw):
        v=t.parameters(kw);seg=t.segments(self.c,self.a,v)
        e,ends=t.expected(seg,v);return e,ends,seg

    def test_default_phase_counts(self):
        e,p,_=self.oracle()
        self.assertEqual(p,{'frame':78,'fill':942,'interior':1050,'resource':1063})
        self.assertEqual(len(e.writes),1064)
        self.assertEqual(e.writes[-1],(t.w.task.tasks.TASKS+8,2,2))

    def test_interior_row_major_and_palette(self):
        e,p,_=self.oracle();inside=e.writes[p['fill']:p['interior']]
        self.assertEqual(inside[0],(t.w.TILEMAP+326,2,0x7009))
        self.assertEqual(inside[-1],(t.w.TILEMAP+570,2,0x7074))
        self.assertEqual([v for _,_,v in inside],list(range(0x7009,0x7075)))

    def test_two_queue_reservations(self):
        e,_,_=self.oracle()
        self.assertEqual(e.reservations,[{'index':0,'source':t.w.PIXELS,'destination':0x06000120,'length':3456},
            {'index':1,'source':t.w.TILEMAP,'destination':0x06000000,'length':2048}])

    def test_full_queue_has_no_dma_reservation(self):
        e,p,_=self.oracle(occupied=tuple(range(128)))
        self.assertEqual(e.reservations,[]);self.assertEqual(p['resource']-p['interior'],4)
        self.assertEqual(e.writes[-1][-1],2)

    def test_context_base_ten_bits(self):
        e,p,_=self.oracle(context_base=0xffff)
        self.assertEqual(e.writes[p['fill']][-1],0x7408)

    def test_window_rows_wrap_in_each_shape(self):
        for shape in range(4):
            e,p,_=self.oracle(shape=shape,left=31,top=31,width=2,height=2)
            expected=[t.w.TILEMAP+2*t.w.tile_index(x,y,shape)for y in(31,32)for x in(31,32)]
            self.assertEqual([at for at,_,_ in e.writes[p['fill']:p['interior']]],expected)

    def test_maximum_fill_bound(self):
        e,p,_=self.oracle(width=32,height=8)
        self.assertEqual(p['fill']-p['frame'],2048)

    def test_zero_dimensions_have_no_pixel_or_interior_writes(self):
        for kw in(dict(width=0),dict(height=0)):
            _,p,_=self.oracle(**kw);self.assertEqual(p['frame'],p['fill']);self.assertEqual(p['fill'],p['interior'])

    def test_unknown_options_rejected(self):
        with self.assertRaises(ValueError):t.parameters({'unknown':1})

    def test_unmodelled_display_and_background_rejected(self):
        for kw in(dict(display=1),dict(bg=4),dict(shape=4)):
            with self.subTest(kw=kw):
                with self.assertRaises(ValueError):t.parameters(kw)

    def test_wrong_state_and_task_rejected(self):
        for kw in(dict(state=0),dict(task_id=16),dict(task_id=-1)):
            with self.subTest(kw=kw):
                with self.assertRaises(ValueError):t.parameters(kw)

    def test_budget_dimension_rejected(self):
        for kw in(dict(width=33,height=8),dict(width=65),dict(height=9)):
            with self.subTest(kw=kw):
                with self.assertRaises(ValueError):t.parameters(kw)

    def test_state1_does_not_map_palette_slot(self):
        _,_,seg=self.oracle()
        addresses={at for at,_,_ in seg}
        self.assertIn(0x08001aec,addresses)
        self.assertNotIn(0x081534e4,addresses);self.assertNotIn(t.bios.SOURCE,addresses)

    def test_new_contract_matrix(self):
        rows=t.verify();self.assertEqual(len(rows),79)
        self.assertEqual(sum(row['returned']for row in rows),75)
        self.assertTrue(all(row['return_sp_r4_r11_proven']for row in rows if row['returned']))

    def test_all_task_ids_and_full_queue(self):
        rows=t.verify();full=[row for row in rows if row['case'].startswith('task')and row['case'].endswith('-full')]
        self.assertEqual({row['parameters']['task_id']for row in full},set(range(16)))
        self.assertTrue(all(row['task_state_after']==2 and not row['queue_reservations']for row in full))

    def test_four_new_partial_stops(self):
        rows=[row for row in t.verify()if not row['returned']]
        self.assertEqual([row['case']for row in rows],['interior-readonly','queue-lock-readonly','queue-mask-short','state-readonly'])
        self.assertEqual([row['write_count']for row in rows],[942,1050,1056,1063])
        self.assertTrue(all(row['task_state_after']==1 for row in rows))

    def test_matrix_memoized_once(self):
        self.assertIs(t.verify(),t.verify());self.assertEqual(t.verify.cache_info().misses,1)

    def fake(self):
        seg=[(0x02001000,b'abcd',True)];regs=list(range(16));regs[0]=t.w.b.vm.RETURN;regs[13]=t.w.b.vm.SP
        m=SimpleNamespace(mem={0x02001000+i:b for i,b in enumerate(b'abcd')},
            writable=set(range(0x02001000,0x02001004)),writes=[],r=regs,original=tuple(regs),nonstack_writes=lambda:[])
        return m,seg

    def test_final_memory_mutation_rejected(self):
        m,seg=self.fake();m.mem[0x02001001]=0
        with self.assertRaisesRegex(ValueError,'object'):t.check_effect(m,seg,[],True)

    def test_write_mutation_rejected(self):
        m,seg=self.fake();m.nonstack_writes=lambda:[(0x02001000,1,0)]
        with self.assertRaisesRegex(ValueError,'write差分'):t.check_effect(m,seg,[],True)

    def test_preserved_register_mutation_rejected(self):
        for reg in(*range(4,12),13):
            m,seg=self.fake();m.r[reg]^=1
            with self.subTest(reg=reg):
                with self.assertRaisesRegex(ValueError,'SP/r4'):t.check_effect(m,seg,[],True)

    def test_hidden_extra_write_rejected(self):
        m,seg=self.fake();m.writes=[(0x02002000,1,0)]
        with self.assertRaisesRegex(ValueError,'許可範囲外'):t.check_effect(m,seg,[],True)

    def test_native_acceptance_not_claimed(self):
        for row in t.verify():
            self.assertFalse(row['bios_execution_observed']);self.assertFalse(row['dma_execution_observed'])
            self.assertFalse(row['native_observation']);self.assertFalse(row['full_play_acceptance'])


if __name__=='__main__':unittest.main()
