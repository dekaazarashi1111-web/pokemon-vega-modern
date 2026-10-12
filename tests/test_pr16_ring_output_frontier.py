"""未読7calleeと3212byte data窓の範囲・前提検査。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_output_frontier as t


def inputs():
    data=b''.join(t.prior.b.word(v)for v in t.prior.CONTROL_TARGETS)
    a={'control_table':{'address':t.prior.prior.TABLE,'hex':data.hex(),'identity':t.s.identity(data),'targets':list(t.prior.CONTROL_TARGETS)},
        'selected_fonts':[{'selector':v}for v in(2,4,5)],'pending_direct_callees':list(t.prior.PENDING),
        'contract_cases':636,'new_node_count':0}
    for key in('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):a[key]=False
    n=[{'address':at,'literal_value':value}for at,value in t.LITERALS]
    n += [{'address':0x08008000+i*4,'kind':'call','target':v&~1}for i,v in enumerate(t.prior.PENDING)]
    n += [{'address':0x09000000+2*i}for i in range(6534-len(n))]
    return n,a


class OutputFrontierTests(unittest.TestCase):
    def reject(self,edit):
        n,a=inputs();edit(n,a)
        with self.assertRaises(ValueError):t.plan(n,a)
    def test_plan(self):
        n,a=inputs();p=t.plan(n,a);self.assertEqual(p['roots'],list(t.prior.PENDING));self.assertEqual(p['direct_recursive_layers'],0)
    def test_unchanged(self):
        n,a=inputs();old=copy.deepcopy((n,a));t.plan(n,a);self.assertEqual((n,a),old)
    def test_count(self):self.reject(lambda n,a:a.update(contract_cases=635))
    def test_new_count(self):self.reject(lambda n,a:a.update(new_node_count=1))
    def test_missing_node(self):self.reject(lambda n,a:n.pop())
    def test_duplicate_node(self):self.reject(lambda n,a:n.__setitem__(-1,n[0]))
    def test_literal_value(self):self.reject(lambda n,a:n[0].update(literal_value=0x08000000))
    def test_literal_missing(self):self.reject(lambda n,a:n[0].pop('literal_value'))
    def test_call_missing(self):self.reject(lambda n,a:next(x for x in n if x.get('kind')=='call').update(target=0x08008000))
    def test_saved_root(self):self.reject(lambda n,a:n[-1].update(address=t.prior.PENDING[0]&~1))
    def test_root_set(self):self.reject(lambda n,a:a['pending_direct_callees'].pop())
    def test_ring(self):self.reject(lambda n,a:a.update(ring_acquisition_accepted=True))
    def test_release(self):self.reject(lambda n,a:a.update(release_ready=True))
    def test_data_budget(self):self.assertEqual(sum(n for _,at,n in t.data_ranges()),3212)
    def test_data_names(self):self.assertEqual(len({name for name,at,n in t.data_ranges()}),44)
    def test_no_overlap(self):
        pts=[v for _,at,n in t.data_ranges()for v in range(at,at+n)];self.assertEqual(len(pts),len(set(pts)))
    def test_glyph_first(self):self.assertEqual(t.glyph_ranges(2,1)[0][1:],(0x081d6e14,32))
    def test_glyph_row_boundary(self):self.assertEqual(t.glyph_ranges(2,8)[0][1:],(0x081d6ff4,32))
    def test_glyph_fourth(self):self.assertEqual(t.glyph_ranges(4,247)[2][1:],(0x081e7003,1))
    def test_glyph_right_delta(self):
        rows=t.glyph_ranges(5,7);self.assertEqual(rows[1][1]-rows[0][1],256)
    def test_wrong_font(self):
        with self.assertRaises(ValueError):t.glyph_ranges(3,1)
    def test_wrong_char(self):
        with self.assertRaises(ValueError):t.glyph_ranges(2,2)
    def test_bool_char(self):
        with self.assertRaises(ValueError):t.glyph_ranges(2,True)
    def test_negative_char(self):
        with self.assertRaises(ValueError):t.glyph_ranges(2,-1)


if __name__=='__main__':unittest.main()
