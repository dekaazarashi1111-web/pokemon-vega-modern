"""control表/pending集合の境界検査。受入済みtext/nativeは実行しない。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_control_frontier as t


def fixture():
    nodes=[{'address':at,'hex':raw}for at,raw in t.PREFIX.items()]
    by={n['address']:n for n in nodes}
    by[0x08005880]['target']=0x08005884;by[0x08005882]['target']=0x08005acc
    by[0x08005886]['literal_value']=t.TABLE;by[0x0800588c]['kind']='indirect'
    nodes +=[{'address':at,'hex':raw,'kind':'call','target':target&~1}for at,raw,target in t.CALLS]
    nodes +=[{'address':0x09000000+2*i,'hex':'c046'}for i in range(5891-len(nodes))]
    a={'saved_node_count':5891,'new_node_count':0,'pending_direct_callees':list(t.DIRECT)}
    for k in ('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):a[k]=False
    return nodes,a


def table(value=0x08009000):return value.to_bytes(4,'little')*24


class ControlFrontierTests(unittest.TestCase):
    def reject(self,edit):
        n,a=fixture();edit(n,a)
        with self.assertRaises(ValueError):t.bind(n,a)
    def test_plan(self):
        n,a=fixture();p=t.bind(n,a);self.assertEqual(p['table']['size'],96);self.assertEqual(p['recursive_direct_layers'],0)
    def test_inputs_unchanged(self):
        n,a=fixture();old=copy.deepcopy((n,a));t.bind(n,a);self.assertEqual((n,a),old)
    def test_missing_node(self):self.reject(lambda n,a:n.pop())
    def test_duplicate_node(self):self.reject(lambda n,a:n.__setitem__(-1,copy.deepcopy(n[0])))
    def test_prior_count(self):self.reject(lambda n,a:a.update(saved_node_count=5890))
    def test_prior_new_count(self):self.reject(lambda n,a:a.update(new_node_count=1))
    def test_missing_callee(self):self.reject(lambda n,a:a['pending_direct_callees'].pop())
    def test_extra_callee(self):self.reject(lambda n,a:a['pending_direct_callees'].append(0x08008001))
    def test_prefix(self):self.reject(lambda n,a:n[0].update(hex='c046'))
    def test_branch(self):self.reject(lambda n,a:next(x for x in n if x['address']==0x08005880).update(target=0x08005882))
    def test_literal(self):self.reject(lambda n,a:next(x for x in n if x['address']==0x08005886).update(literal_value=t.TABLE+4))
    def test_indirect(self):self.reject(lambda n,a:next(x for x in n if x['address']==0x0800588c).update(kind='return'))
    def test_callsite(self):self.reject(lambda n,a:next(x for x in n if x['address']==t.CALLS[0][0]).update(target=0x08008000))
    def test_existing_root(self):self.reject(lambda n,a:n[-1].update(address=t.DIRECT[0]&~1))
    def test_ring(self):self.reject(lambda n,a:a.update(ring_acquisition_accepted=True))
    def test_release(self):self.reject(lambda n,a:a.update(release_ready=True))
    def test_live_table(self):self.reject(lambda n,a:a.update(actual_callback_table_observed=True))
    def test_live_bounds(self):self.reject(lambda n,a:a.update(all_live_slot_bounds_proven=True))
    def test_targets(self):
        values,roots=t.targets(table(),set());self.assertEqual(len(values),24);self.assertEqual(roots,[0x08009001])
    def test_short_table(self):
        with self.assertRaises(ValueError):t.targets(table()[:-1],set())
    def test_mutable_table(self):
        with self.assertRaises(ValueError):t.targets(bytearray(table()),set())
    def test_odd_target(self):
        with self.assertRaises(ValueError):t.targets(table(0x08009001),set())
    def test_outside_rom(self):
        with self.assertRaises(ValueError):t.targets(table(0x0a000000),set())
    def test_data_target(self):
        with self.assertRaises(ValueError):t.targets(table(),{0x08009001})


if __name__=='__main__':unittest.main()
