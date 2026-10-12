"""新規変換表・音声root集合を旧保存範囲と区別する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_output_leaf_bytes as t


def inputs():
    n=[{'address':at,'hex':raw}for at,raw in t.PREFIX.items()];n[0]['literal_value']=t.TABLE
    n +=[{'address':0x08008000+i*4,'kind':'call','target':v&~1}for i,v in enumerate(t.ROOTS)]
    n +=[{'address':0x09000000+2*i}for i in range(6983-len(n))]
    a={'saved_node_count':6983,'data_window_bytes':3212,'pending_direct_callees':list(t.ROOTS),
        'output_data':[{'start':at,'length':size}for _,at,size in t.prior.data_ranges()]}
    for key in('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):a[key]=False
    return n,a


class OutputLeafTests(unittest.TestCase):
    def reject(self,edit):
        n,a=inputs();edit(n,a)
        with self.assertRaises(ValueError):t.plan(n,a)
    def test_plan(self):
        n,a=inputs();p=t.plan(n,a);self.assertEqual(p['translation_table'],{'start':0x081cdf40,'length':256})
    def test_no_recursive_calls(self):self.assertEqual(t.plan(*inputs())['direct_recursive_layers'],0)
    def test_immutable(self):
        n,a=inputs();old=copy.deepcopy((n,a));t.plan(n,a);self.assertEqual((n,a),old)
    def test_missing_node(self):self.reject(lambda n,a:n.pop())
    def test_extra_node(self):self.reject(lambda n,a:n.append({'address':0x08002000}))
    def test_duplicate(self):self.reject(lambda n,a:n.__setitem__(-1,n[0]))
    def test_wrong_count(self):self.reject(lambda n,a:a.update(saved_node_count=6982))
    def test_wrong_data_count(self):self.reject(lambda n,a:a.update(data_window_bytes=3211))
    def test_missing_root(self):self.reject(lambda n,a:a['pending_direct_callees'].pop())
    def test_extra_root(self):self.reject(lambda n,a:a['pending_direct_callees'].append(0x08008001))
    def test_missing_prefix(self):self.reject(lambda n,a:n[0].pop('hex'))
    def test_changed_prefix(self):self.reject(lambda n,a:n[0].update(hex='c046'))
    def test_changed_literal(self):self.reject(lambda n,a:n[0].update(literal_value=t.TABLE+4))
    def test_missing_literal(self):self.reject(lambda n,a:n[0].pop('literal_value'))
    def test_window_count(self):self.reject(lambda n,a:a['output_data'].pop())
    def test_existing_table(self):self.reject(lambda n,a:a['output_data'][0].update(start=t.TABLE,length=256))
    def test_overlap_first(self):self.reject(lambda n,a:a['output_data'][0].update(start=t.TABLE-1,length=2))
    def test_overlap_last(self):self.reject(lambda n,a:a['output_data'][0].update(start=t.TABLE+255,length=2))
    def test_known_root(self):self.reject(lambda n,a:n[-1].update(address=t.ROOTS[0]&~1))
    def test_missing_call(self):self.reject(lambda n,a:next(x for x in n if x.get('kind')=='call').update(target=0x08008000))
    def test_ring(self):self.reject(lambda n,a:a.update(ring_acquisition_accepted=True))
    def test_release(self):self.reject(lambda n,a:a.update(release_ready=True))
    def test_live_table(self):self.reject(lambda n,a:a.update(actual_callback_table_observed=True))
    def test_live_bounds(self):self.reject(lambda n,a:a.update(all_live_slot_bounds_proven=True))


if __name__=='__main__':unittest.main()
