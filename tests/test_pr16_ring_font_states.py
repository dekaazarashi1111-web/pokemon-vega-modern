"""保存state分岐の根拠と拒否境界。旧font/ABI/native試験は起動しない。"""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_font_states as t


def fixture():
    nodes=[{'address':a,'hex':raw,'size':2,'kind':'ordinary'}for a,raw in t.PREFIX]
    by={n['address']:n for n in nodes}
    by[0x08005768]['target']=0x0800576c;by[0x0800576a]['target']=0x08005c54
    by[0x0800576e].update(literal_address=0x08005778,literal_value=t.TABLE)
    by[0x08005774].update(kind='indirect',register=0)
    a={'pending_boundaries':[{'site':0x08005774,'kind':'indirect_boundary'}],
        'selected_fonts':[{'selector':f}for f in (2,4,5)],'ring_acquisition_accepted':False,'initializer_runtime_observed':False}
    return nodes,a


def raw():return b''.join((0x08005800+4*i).to_bytes(4,'little')for i in range(7))


class FontStatesTests(unittest.TestCase):
    def plan(self):return t.table_plan(*fixture())
    def test_exact_seven_states(self):self.assertEqual(self.plan()['count'],7)
    def test_state_byte_offset(self):self.assertEqual(self.plan()['state_offset'],28)
    def test_not_native(self):self.assertIs(self.plan()['runtime_observed'],False)
    def test_changed_bound_rejected(self):
        n,a=fixture();n[1]['hex']='0728'
        with self.assertRaises(ValueError):t.table_plan(n,a)
    def test_changed_literal_rejected(self):
        n,a=fixture();n[5]['literal_value']+=4
        with self.assertRaises(ValueError):t.table_plan(n,a)
    def test_changed_branch_rejected(self):
        n,a=fixture();n[2]['target']+=2
        with self.assertRaises(ValueError):t.table_plan(n,a)
    def test_duplicate_node_rejected(self):
        n,a=fixture()
        with self.assertRaises(ValueError):t.table_plan(n+n[:1],a)
    def test_missing_pending_rejected(self):
        n,a=fixture();a['pending_boundaries']=[]
        with self.assertRaises(ValueError):t.table_plan(n,a)
    def test_unselected_font_rejected(self):
        n,a=fixture();a['selected_fonts'][0]['selector']=0
        with self.assertRaises(ValueError):t.table_plan(n,a)
    def test_native_claim_rejected(self):
        n,a=fixture();a['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):t.table_plan(n,a)
    def test_table_values_and_roots(self):
        row=t.table_values(raw(),self.plan());self.assertEqual(len(row['roots']),7)
        self.assertEqual(row['targets'][0],0x08005800);self.assertEqual(row['roots'][0],0x08005801)
    def test_short_table_rejected(self):
        with self.assertRaises(ValueError):t.table_values(raw()[:-1],self.plan())
    def test_long_table_rejected(self):
        with self.assertRaises(ValueError):t.table_values(raw()+bytes(4),self.plan())
    def test_odd_target_rejected(self):
        r=bytearray(raw());r[0]|=1
        with self.assertRaises(ValueError):t.table_values(bytes(r),self.plan())
    def test_nonrom_target_rejected(self):
        with self.assertRaises(ValueError):t.table_values(bytes(4)+raw()[4:],self.plan())
    def test_table_target_rejected(self):
        with self.assertRaises(ValueError):t.table_values(t.TABLE.to_bytes(4,'little')+raw()[4:],self.plan())
    def test_other_data_target_rejected(self):
        with self.assertRaises(ValueError):t.table_values(raw(),self.plan(),[0x08005800])
    def test_duplicate_targets_share_root(self):
        row=t.table_values(raw()[:4]*7,self.plan());self.assertEqual(len(row['roots']),1);self.assertEqual(len(row['targets']),7)
    def test_direct_callees_finite(self):
        self.assertEqual(t.direct_roots({'direct_calls_recursively_expanded':0,'pending_direct_callees':[0x08009001]},{}),[0x08009001])
    def test_recursive_replay_rejected(self):
        with self.assertRaises(ValueError):t.direct_roots({'direct_calls_recursively_expanded':1,'pending_direct_callees':[]},{})
    def test_known_root_rejected(self):
        with self.assertRaises(ValueError):t.direct_roots({'direct_calls_recursively_expanded':0,'pending_direct_callees':[0x08009001]},{0x08009000:{}})
    def test_assert_not_expanded(self):
        self.assertEqual(t.direct_roots({'direct_calls_recursively_expanded':0,'pending_direct_callees':[t.prior.ui.LOG|1]},{}),[])


if __name__=='__main__':unittest.main()
