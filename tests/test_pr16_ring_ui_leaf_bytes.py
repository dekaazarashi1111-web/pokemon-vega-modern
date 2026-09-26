"""未読3入口のplanとdata境界だけを検証。旧保存命令/nativeの単独再実行なし。"""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_ui_leaf_bytes as task


def fixture():
    a={'saved_node_count':3918,'new_node_count':0,'pending_direct_callees':list(task.DIRECT),
       'pending_continuations':[],'pending_effective_targets':[],
       'ring_acquisition_accepted':False,'release_ready':False,'actual_callback_table_observed':False,
       'all_live_slot_bounds_proven':False}
    nodes=[{'address':0x08040000+i*2}for i in range(3915)]
    nodes.extend({'address':at,'hex':raw,'kind':'call','target':target&~1}for at,raw,target in task.CALLS)
    return a,nodes


class PlanTests(unittest.TestCase):
    def bad(self,key,value):
        a,n=fixture();a[key]=value
        with self.assertRaises(ValueError):task.plan(a,n)
    def test_exact_three_roots(self):
        a,n=fixture();before=copy.deepcopy((a,n))
        self.assertEqual(task.plan(a,n),list(task.DIRECT));self.assertEqual((a,n),before)
    def test_old_count(self):self.bad('saved_node_count',3917)
    def test_not_a_contract_report(self):self.bad('new_node_count',1)
    def test_missing_direct(self):self.bad('pending_direct_callees',list(task.DIRECT[:2]))
    def test_changed_direct(self):self.bad('pending_direct_callees',[task.DIRECT[0]+2,*task.DIRECT[1:]])
    def test_changed_order(self):self.bad('pending_direct_callees',list(reversed(task.DIRECT)))
    def test_unexpected_continuation(self):self.bad('pending_continuations',[0x08000101])
    def test_unexpected_effective(self):self.bad('pending_effective_targets',[0x08000101])
    def test_scope_not_promoted(self):
        for k in ('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):
            with self.subTest(k=k):self.bad(k,True)
    def test_scope_not_truthy_integer(self):self.bad('ring_acquisition_accepted',0)
    def test_node_count(self):
        a,n=fixture()
        with self.assertRaises(ValueError):task.plan(a,n[:-1])
    def test_duplicate_node(self):
        a,n=fixture();n[1]=dict(n[0])
        with self.assertRaises(ValueError):task.plan(a,n)
    def test_call_bytes(self):
        a,n=fixture();n[-1]['hex']='00000000'
        with self.assertRaises(ValueError):task.plan(a,n)
    def test_call_kind(self):
        a,n=fixture();n[-2]['kind']='ordinary'
        with self.assertRaises(ValueError):task.plan(a,n)
    def test_call_target(self):
        a,n=fixture();n[-3]['target']+=2
        with self.assertRaises(ValueError):task.plan(a,n)
    def test_already_saved_root(self):
        a,n=fixture();n[0]['address']=task.DIRECT[0]&~1
        with self.assertRaises(ValueError):task.plan(a,n)


class DataTests(unittest.TestCase):
    def data(self):return {'tables':[{'start':0x08001224,'length':32}],
        'attribute_table':{'address':0x08001ac8,'count':10,'size':40},
        'dummy_template':{'address':0x081ce040,'size':8}}
    def test_explicit_ranges(self):
        a=self.data();r=task.data_ranges(a)
        self.assertIn((0x08001ac8,40),r);self.assertIn((0x081ce040,8),r)
        self.assertIn((0x08113810,20),r)
    def test_attribute_count(self):
        a=self.data();a['attribute_table']['count']=9
        with self.assertRaises(ValueError):task.data_ranges(a)
    def test_attribute_address(self):
        a=self.data();a['attribute_table']['address']+=4
        with self.assertRaises(ValueError):task.data_ranges(a)
    def test_dummy_size(self):
        a=self.data();a['dummy_template']['size']=4
        with self.assertRaises(ValueError):task.data_ranges(a)
    def test_non_rom_table(self):
        a=self.data();a['tables'][0]['start']=0x02000000
        with self.assertRaises(ValueError):task.data_ranges(a)
    def test_wrapping_table(self):
        a=self.data();a['tables'][0]={'start':0x09fffff0,'length':32}
        with self.assertRaises(ValueError):task.data_ranges(a)


if __name__=='__main__':unittest.main()
