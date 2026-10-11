"""保存cursor/scrollと明示stack条件、独立pixel期待値・queue境界の限定検証。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_cursor_scroll_contracts as t


class CursorScrollTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes,_,cls.context=t.saved_inputs();cls.a=t.s.load(t.PRIOR)['analysis']
    def reject(self,edit):
        a=copy.deepcopy(self.a);edit(a)
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes,a,self.context)
    def test_all_contracts(self):
        cases,groups=t.evaluated()
        self.assertEqual(groups,{'scroll':200,'scroll_state':144,'cursor':48,'erase':18,'cursor_state':144,'stack_residue':34,'boundaries':3})
        self.assertEqual(len(cases.rows),591);self.assertEqual(sum(r['returned']for r in cases.rows),588)
    def test_unique_cases(self):self.assertEqual(len({r['case']for r in t.evaluated()[0].rows}),591)
    def test_live_stack_budget(self):self.assertLessEqual(max(r['maximum_stack_bytes']for r in t.evaluated()[0].rows),512)
    def test_stack_dimensions_at_actual_store(self):
        for row in t.evaluated()[0].rows:
            if row['dimension_writes']:self.assertEqual(row['dimension_writes'][0][2],0x00180018)
    def test_stack_residue_same_pixel_queue_result(self):
        rows=[r for r in t.evaluated()[0].rows if r['case'].startswith("('stack_residue',")]
        self.assertEqual(len(rows),34);self.assertEqual(len({r['write_sha256']for r in rows}),1)
        self.assertEqual(len({r['final_object_sha256']for r in rows}),1)
    def test_dimensions_all_bits(self):
        for dims in((0,0),(1,1),(2,3),(31,32),(255,255)):
            for residue in(0,0xffffffff,*(1<<i for i in range(32))):
                self.assertEqual(t.initialized_dimensions(residue,dims),(dims[0]*8)|(dims[1]*8<<16))
    def test_dimensions_bool(self):
        with self.assertRaises(ValueError):t.initialized_dimensions(True,(2,3))
    def test_dimensions_overflow(self):
        with self.assertRaises(ValueError):t.initialized_dimensions(1<<32,(2,3))
    def test_dimensions_negative(self):
        with self.assertRaises(ValueError):t.initialized_dimensions(-1,(2,3))
    def test_dimension_count(self):
        with self.assertRaises(ValueError):t.initialized_dimensions(0,(1,))
    def test_dimension_u8(self):
        with self.assertRaises(ValueError):t.initialized_dimensions(0,(256,1))
    def test_buffer_count(self):self.assertEqual(len(t.pixel_buffer((2,3))),192)
    def test_zero_buffer(self):self.assertEqual(t.pixel_buffer((0,3)),b'')
    def test_negative_buffer(self):
        with self.assertRaises(ValueError):t.pixel_buffer((-1,3))
    def test_scroll_zero_identity(self):
        data=t.pixel_buffer((2,3));writes=t.scroll_writes(data,(2,3),0,0,0xa5)
        self.assertEqual(b''.join(w[2].to_bytes(4,'little')for w in writes),data)
    def test_scroll_all_fill(self):self.assertEqual({v for _,_,v in t.scroll_writes(t.pixel_buffer((2,3)),(2,3),0,24,0xa5)},{0xa5a5a5a5})
    def test_scroll_unsupported_direction(self):self.assertEqual(t.scroll_writes(t.pixel_buffer((1,1)),(1,1),255,1,0),[])
    def test_scroll_descending_order(self):self.assertEqual([at for at,_,_ in t.scroll_writes(bytes(32),(1,1),1,1,0)],list(range(t.PIXELS+28,t.PIXELS-1,-4)))
    def test_scroll_cross_tile_source(self):
        data=t.pixel_buffer((2,3));self.assertEqual(t.scroll_writes(data,(2,3),0,8,0)[0][2],int.from_bytes(data[64:68],'little'))
    def test_scroll_short_buffer(self):
        with self.assertRaises(ValueError):t.scroll_writes(bytes(31),(1,1),0,1,0)
    def test_scroll_amount_overflow(self):
        with self.assertRaises(ValueError):t.scroll_writes(bytes(32),(1,1),0,256,0)
    def test_fill_odd_neighbor_not_normalized(self):
        writes,data=t.fill_writes(bytes([0xa0])*288,(3,3),(1,0),0x55)
        self.assertEqual(writes[0],(t.PIXELS,1,0x50));self.assertEqual(data[t.prior.pixel_offset(10,0,3)],0xf5)
    def test_fill_outside(self):self.assertEqual(t.fill_writes(bytes(288),(3,3),(255,255),0xff),( [],bytes(288)))
    def test_fill_short_buffer(self):
        with self.assertRaises(ValueError):t.fill_writes(bytes(287),(3,3),(0,0),0)
    def test_copy_outside(self):self.assertEqual(t.copy_writes(self.a,bytes(288),(3,3),(255,255),0,0),[])
    def test_copy_unknown_style(self):
        with self.assertRaises(ValueError):t.copy_writes(self.a,bytes(288),(3,3),(0,0),2,0)
    def test_copy_unknown_frame(self):
        with self.assertRaises(ValueError):t.copy_writes(self.a,bytes(288),(3,3),(0,0),0,4)
    def test_copy_short_buffer(self):
        with self.assertRaises(ValueError):t.copy_writes(self.a,bytes(287),(3,3),(0,0),0,0)
    def test_ring_boundary(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_release_boundary(self):self.reject(lambda a:a.update(release_ready=True))
    def test_scroll_hash(self):self.reject(lambda a:a['scroll_table'].update(hex='00'*8))
    def test_scroll_definition(self):
        def edit(a):a['scroll_table'].update(hex='00'*8,identity=t.s.identity(bytes(8)))
        self.reject(edit)
    def test_prefix_changed(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x0800439e)['hex']='c046'
        with self.assertRaises(ValueError):t.validate_inputs(nodes,self.a,self.context)
    def test_mask_changed(self):
        nodes=copy.deepcopy(self.nodes);next(n for n in nodes if n['address']==0x0800438e)['literal_value']=0
        with self.assertRaises(ValueError):t.validate_inputs(nodes,self.a,self.context)
    def test_attribute_hash(self):
        ctx=copy.deepcopy(self.context);next(r for r in ctx['tables']if r['start']==t.b.engine.TABLE)['identity']['size']=0
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes,self.a,ctx)
    def test_node_count(self):
        with self.assertRaises(ValueError):t.validate_inputs(self.nodes[:-1],self.a,self.context)
    def test_no_implicit_stack_zero(self):
        m=t.Machine(self.nodes,[]);m.r[13]-=4
        with self.assertRaises(ValueError):m.read(m.r[13],4)
    def test_declared_residue_live_read(self):
        m=t.Machine(self.nodes,[],residues=((72,0x12345678),));m.r[13]-=72
        self.assertEqual(m.read(t.b.vm.SP-72,4),0x12345678)
    def test_declared_residue_nonlive_read(self):
        m=t.Machine(self.nodes,[],residues=((72,0x12345678),))
        with self.assertRaises(ValueError):m.read(t.b.vm.SP-72,4)
    def test_undeclared_stack_offset(self):
        with self.assertRaises(ValueError):t.Machine(self.nodes,[],residues=((76,0),))
    def test_two_stack_residues(self):
        with self.assertRaises(ValueError):t.Machine(self.nodes,[],residues=((72,0),(48,0)))
    def test_residue_overflow(self):
        with self.assertRaises(ValueError):t.Machine(self.nodes,[],residues=((72,1<<32),))
    def test_stack_object_overlap(self):
        with self.assertRaises(ValueError):t.Machine(self.nodes,[(t.b.vm.SP-72,bytes(4),False)])
    def test_originals_unchanged(self):
        a=copy.deepcopy(self.a);t.validate_inputs(self.nodes,self.a,self.context);self.assertEqual(self.a,a)


if __name__=='__main__':unittest.main()
