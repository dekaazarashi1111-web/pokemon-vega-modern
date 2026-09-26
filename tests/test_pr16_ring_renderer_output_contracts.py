"""renderer有限streamの順序・通常高速等価・queue差・部分停止・入力境界。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_renderer_output_contracts as t


class RendererOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis']
        cls.attr=t.validate_inputs(cls.nodes,cls.a,cls.context)
    def fixture(self,**kwargs):
        args=dict(font=2,fast=0,slot=0,occupied=());args.update(kwargs)
        return t.fixture(self.a,self.attr,**args)
    def reject(self,edit):
        a=copy.deepcopy(self.a);edit(a)
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes,a,self.context)
    def modify_printer(self,offset,value):
        at,segs=self.fixture();data=bytearray(segs[0][1]);data[offset:offset+len(value)]=value
        segs[0]=(segs[0][0],bytes(data),True);return at,segs
    def test_all_contracts(self):
        cases,groups,comparisons=t.evaluated()
        self.assertEqual(groups,{'fast':18,'normal':108,'inactive':36,'boundaries':6})
        self.assertEqual(len(cases.rows),168);self.assertEqual(sum(r['returned']for r in cases.rows),162)
        self.assertEqual(len(comparisons),18)
    def test_labels_unique(self):self.assertEqual(len({r['case']for r in t.evaluated()[0].rows}),168)
    def test_saved_top_level_executed(self):
        sites=t.evaluated()[0].sites
        self.assertIn(t.b.RUN&~1,sites);self.assertIn(t.b.IMPL&~1,sites)
    def test_normal_character_order(self):
        for font in(2,4,5):
            for slot in(0,31):
                for qi in range(3):
                    rows=[r for r in t.evaluated()[0].rows if r['case'].startswith(f'normal-{font}-{slot}-{qi}-')]
                    self.assertEqual([r['characters']for r in rows],[[c]for c in t.CHARS]+[[]])
                    self.assertEqual([r['terminated']for r in rows],[False]*5+[True])
    def test_fast_character_order(self):
        for r in t.evaluated()[0].rows:
            if r['case'].startswith('fast-'):
                self.assertEqual(r['characters'],list(t.CHARS));self.assertTrue(r['terminated'])
    def test_inactive_no_writes(self):
        rows=[r for r in t.evaluated()[0].rows if r['case'].startswith('inactive-')]
        self.assertEqual(len(rows),36)
        for r in rows:self.assertEqual(r['nonstack_write_count'],0);self.assertTrue(r['previously_inactive'])
    def test_queue_requests_differ(self):
        for row in t.evaluated()[2]:self.assertEqual((row['normal_queue_requests'],row['fast_queue_requests']),(5,1))
    def test_full_queue_reserves_nothing(self):
        rows=[r for r in t.evaluated()[2]if r['queue_fixture']==2]
        self.assertEqual(len(rows),6)
        for row in rows:self.assertEqual((row['normal_reservations'],row['fast_reservations']),(0,0))
    def test_queue_wrap_exact_indices(self):
        for qi,expected in((0,[127,0,1,2,3]),(1,[0,1,2,3,4])):
            rows=[r for r in t.evaluated()[0].rows if r['case'].startswith(f'normal-2-0-{qi}-')]
            self.assertEqual([v['index']for r in rows for v in r['queue_reservations']],expected)
    def test_no_queue_image_equality_claim(self):
        for r in t.evaluated()[2]:self.assertFalse(r['queue_image_equality_claimed']);self.assertFalse(r['actual_dma_observed'])
    def test_projection_objects(self):
        for r in t.evaluated()[2]:self.assertEqual({k:v['size']for k,v in r['projection'].items()},{'printer':32,'glyph':130,'pixels':288,'lookup':168})
    def test_no_stack_residue_needed_for_this_stream(self):
        for row in t.evaluated()[0].rows:self.assertEqual(row['stack_residues'],[])
    def test_live_stack_budget(self):self.assertLessEqual(max(r['maximum_stack_bytes']for r in t.evaluated()[0].rows),512)
    def test_partial_stops_no_false_return(self):
        rows=[r for r in t.evaluated()[0].rows if r['case'].startswith('boundary-')]
        self.assertEqual(len(rows),6)
        for r in rows:
            self.assertFalse(r['returned']);self.assertEqual(r['stop'],['未map read',0x08002f7c])
            self.assertGreater(r['nonstack_write_count'],84)
    def test_successor_readonly_preserved(self):
        at,segs=self.fixture();e,_=t.frame(self.a,segs,at,2,0);next_segs=t.successor(e,segs)
        self.assertEqual([r for r in next_segs if not r[2]],[r for r in segs if not r[2]])
    def test_successor_does_not_alias_input(self):
        at,segs=self.fixture();old=copy.deepcopy(segs);e,_=t.frame(self.a,segs,at,2,0)
        nxt=t.successor(e,segs);self.assertEqual(segs,old);self.assertNotEqual(nxt,segs)
    def test_unknown_font(self):
        with self.assertRaises(ValueError):self.fixture(font=3)
    def test_bool_font(self):
        with self.assertRaises(ValueError):self.fixture(font=True)
    def test_bool_fast(self):
        with self.assertRaises(ValueError):self.fixture(fast=True)
    def test_fast_range(self):
        with self.assertRaises(ValueError):self.fixture(fast=2)
    def test_slot_range(self):
        with self.assertRaises(ValueError):self.fixture(slot=32)
    def test_nonendpoint_slot(self):
        with self.assertRaises(ValueError):self.fixture(slot=1)
    def test_queue_list(self):
        with self.assertRaises(ValueError):self.fixture(occupied=[])
    def test_queue_other_pattern(self):
        with self.assertRaises(ValueError):self.fixture(occupied=(1,))
    def test_frame_unknown_font(self):
        at,segs=self.fixture()
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,3,0)
    def test_frame_fast_bool(self):
        at,segs=self.fixture()
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,2,True)
    def test_printer_font_mismatch(self):
        at,segs=self.modify_printer(5,b'\x04')
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,2,0)
    def test_printer_state_mismatch(self):
        at,segs=self.modify_printer(28,b'\x04')
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,2,0)
    def test_printer_active_mismatch(self):
        at,segs=self.modify_printer(27,b'\x02')
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,2,0)
    def test_stream_truncated(self):
        at,segs=self.fixture();segs=[(p,data[:-1]if p==t.b.TEMPLATE else data,w)for p,data,w in segs]
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,2,0)
    def test_stream_changed(self):
        at,segs=self.fixture();segs=[(p,bytes(len(data))if p==t.b.TEMPLATE else data,w)for p,data,w in segs]
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,2,0)
    def test_pointer_outside(self):
        at,segs=self.modify_printer(0,t.b.word(t.b.TEMPLATE+len(t.STREAM)))
        with self.assertRaises(ValueError):t.frame(self.a,segs,at,2,0)
    def test_image_length_boundary(self):
        at,segs=self.fixture();e=t.b.Expected(segs)
        with self.assertRaises(ValueError):t.image(e,at,4097)
    def test_image_unmapped(self):
        with self.assertRaises(ValueError):t.image(t.b.Expected([]),t.b.POOL,1)
    def test_ring_boundary(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_release_boundary(self):self.reject(lambda a:a.update(release_ready=True))
    def test_old_stack_boundary(self):self.reject(lambda a:a['stack_residue_contract'].update(zero_unmapped_stack_permitted=True))
    def test_neighbor_effect_boundary(self):self.reject(lambda a:a.update(fill_neighbor_nibble_effect_preserved=False))
    def test_speed_boundary(self):self.reject(lambda a:a.update(zero_step_scroll_indices=[]))
    def test_dma_boundary(self):self.reject(lambda a:a.update(dma_execution_observed=True))
    def test_original_data_unchanged(self):
        a=copy.deepcopy(self.a);t.validate_inputs(self.nodes,self.a,self.context);self.assertEqual(self.a,a)


if __name__=='__main__':unittest.main()
