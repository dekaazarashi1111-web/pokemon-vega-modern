"""controlの正確期待値・保存表・明示RAM fixtureの境界検査。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_control_contracts as t


def inputs():
    def row(at,data):return {'address':at,'hex':data.hex(),'identity':t.s.identity(data)}
    a={'control_table':row(t.prior.TABLE,b''.join(t.b.word(v)for v in t.CONTROL_TARGETS)),
        'state_table':row(0x0800577c,bytes(28)),
        'dispatch_tables':[row(0x0800582c,bytes(32)),row(0x08005ae4,bytes(24))],
        'tables':[row(0x083e30e8,bytes(192))],
        'selected_fonts':[{'selector':v}for v in (2,4,5)],'pending_direct_callees':list(t.PENDING)}
    a['control_table']['targets']=list(t.CONTROL_TARGETS)
    for key in('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):a[key]=False
    return [{'address':0x08000000+2*i}for i in range(6534)],a


class ControlContractTests(unittest.TestCase):
    def reject(self,edit):
        n,a=inputs();edit(n,a)
        with self.assertRaises(ValueError):t.validate_inputs(n,a)
    def test_valid_saved_inputs(self):
        n,a=inputs();self.assertEqual(t.validate_inputs(n,a)[0],t.prior.TABLE)
    def test_inputs_unchanged(self):
        n,a=inputs();old=copy.deepcopy((n,a));t.validate_inputs(n,a);self.assertEqual((n,a),old)
    def test_missing_node(self):self.reject(lambda n,a:n.pop())
    def test_duplicate_node(self):self.reject(lambda n,a:n.__setitem__(-1,n[0]))
    def test_nonlist_nodes(self):
        n,a=inputs()
        with self.assertRaises(ValueError):t.validate_inputs(tuple(n),a)
    def test_table_hash(self):self.reject(lambda n,a:a['control_table'].update(hex='00'*96))
    def test_table_length(self):self.reject(lambda n,a:a['control_table'].update(hex='00'*95))
    def test_table_address(self):self.reject(lambda n,a:a['control_table'].update(address=t.prior.TABLE+4))
    def test_table_targets(self):self.reject(lambda n,a:a['control_table']['targets'].pop())
    def test_font_set(self):self.reject(lambda n,a:a['selected_fonts'].pop())
    def test_missing_callee(self):self.reject(lambda n,a:a['pending_direct_callees'].pop())
    def test_ring_boundary(self):self.reject(lambda n,a:a.update(ring_acquisition_accepted=True))
    def test_release_boundary(self):self.reject(lambda n,a:a.update(release_ready=True))
    def test_table_not_live(self):self.reject(lambda n,a:a.update(actual_callback_table_observed=True))
    def test_live_bounds(self):self.reject(lambda n,a:a.update(all_live_slot_bounds_proven=True))
    def test_color_fixture_fields(self):
        _,a=inputs();at,p,segs=t.fixture(a,colors=(0x12,0x34));self.assertEqual(p[12:14],b'\x12\x34');self.assertEqual(segs[0][1],bytes(p))
    def test_color_fixture_last_slot(self):
        _,a=inputs();at,p,segs=t.fixture(a,full=True,slot=31,colors=(1,2));self.assertEqual(at,t.b.POOL+992);self.assertEqual(segs[0][1][992:],bytes(p))
    def test_color_fixture_bad_length(self):
        with self.assertRaises(ValueError):t.fixture(inputs()[1],colors=(1,))
    def test_color_fixture_bad_value(self):
        with self.assertRaises(ValueError):t.fixture(inputs()[1],colors=(256,1))
    def test_color_fixture_bool(self):
        with self.assertRaises(ValueError):t.fixture(inputs()[1],colors=(True,1))
    def test_lookup_count_and_extent(self):
        w=t.lookup_writes(1,2,3);self.assertEqual(len(w),84);self.assertEqual(w[:3],[(t.LOOKUP+162,2,2),(t.LOOKUP+164,2,1),(t.LOOKUP+166,2,3)])
        self.assertEqual(w[-1][0],t.LOOKUP+160)
    def test_lookup_low_high_nibbles(self):
        w=t.lookup_writes(1,2,3)[3:];self.assertEqual([v for _,_,v in w[:4]],[0x2222,0x1222,0x3222,0x2122]);self.assertEqual(w[-1][2],0x3333)
    def test_lookup_all_same(self):self.assertTrue(all(v==0x7777 for _,_,v in t.lookup_writes(7,7,7)[3:]))
    def test_lookup_nibble_reject(self):
        with self.assertRaises(ValueError):t.lookup_writes(16,0,0)
    def test_lookup_negative_reject(self):
        with self.assertRaises(ValueError):t.lookup_writes(-1,0,0)
    def test_lookup_bool_reject(self):
        with self.assertRaises(ValueError):t.lookup_writes(True,0,0)
    def printer(self):
        p=bytearray(32);p[12:14]=b'\xab\xcd';return p
    def test_fg_preserves_low(self):self.assertEqual(t.color_writes(0x2000000,self.printer(),1,b'\x37')[:2],[(0x200000c,1,0x7b),(0x2000000,4,t.b.TEMPLATE+3)])
    def test_bg_preserves_shadow(self):self.assertEqual(t.color_writes(0x2000000,self.printer(),2,b'\x37')[0],(0x200000d,1,0xc7))
    def test_shadow_preserves_bg(self):self.assertEqual(t.color_writes(0x2000000,self.printer(),3,b'\x37')[0],(0x200000d,1,0x7d))
    def test_three_color_order(self):
        w=t.color_writes(0x2000000,self.printer(),4,b'\x27\x18\x39');self.assertEqual([w[i][2]for i in(0,2,4)],[0x7b,0xc8,0x98]);self.assertEqual(len(w),90)
    def test_partial_color_stores(self):self.assertEqual(len(t.color_writes(0x2000000,self.printer(),4,b'\x07',expand=False)),2)
    def test_missing_color_rejected(self):
        with self.assertRaises(ValueError):t.color_writes(0x2000000,self.printer(),4,b'\x07')
    def test_long_color_rejected(self):
        with self.assertRaises(ValueError):t.color_writes(0x2000000,self.printer(),1,b'\x07\x08')
    def test_color_payload_type(self):
        with self.assertRaises(ValueError):t.color_writes(0x2000000,self.printer(),1,bytearray([7]))
    def test_control_not_color(self):
        with self.assertRaises(ValueError):t.color_writes(0x2000000,self.printer(),5,b'\x07')
    def test_prefix_no_subtype(self):
        p=self.printer();p[21]=128
        self.assertEqual(t.prefix(0x2000000,p,2,flags=4,subtype=False),[(0x200001e,1,1),(0x2000000,4,t.b.TEMPLATE+1)])


if __name__=='__main__':unittest.main()
