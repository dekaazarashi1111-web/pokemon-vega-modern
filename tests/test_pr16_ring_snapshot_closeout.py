"""New coverage projection tests only; never rerun native/old ABI/old fixtures."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_snapshot_closeout as c


def sample():
    a={'runtime_provenance_bound':True,'observed_calls':8,'bound_calls':8,'rejected_calls':[],
       'bindings':[]}
    for k in ('allocated_storage_extent_proven','synchrony_proven','all_runtime_owners_excluded',
              'ring_acquisition_accepted','release_ready'):a[k]=False
    rows=[]
    for i in range(1,9):
        snap={'selector':0,'record_base':0,'sp':0x3007dcc,'id':1000+i}
        a['bindings'].append({'ordinal':i,'snapshot':snap,'actual_return_observed':True,
             'conditional_assumptions_not_discharged':['normal_mapping_stable','synchronous'],
             'route':{'kind':'low_other','calls':[],'peak':24},'return_target':0x93775cc})
        rows.extend([{'kind':'entry','ordinal':i,'snapshot':copy.deepcopy(snap)},
                     {'kind':'exit','ordinal':i,'returned':True,'steps':81}])
    return a,rows


class CoverageTests(unittest.TestCase):
    def setUp(self):self.a,self.rows=sample()
    def reject(self):
        with self.assertRaises(ValueError):c.coverage(self.a,self.rows)
    def test_only_projection(self):
        p=c.coverage(self.a,self.rows)
        self.assertEqual(p['observed_instructions'],648)
        self.assertFalse(p['active_record_prefix_observed'])
        self.assertFalse(p['selector2_peak44_observed'])
        self.assertFalse(p['synchrony_proven'])
    def test_missing_call(self):self.rows.pop();self.reject()
    def test_wrong_snapshot(self):self.rows[0]['snapshot']['id']=7;self.reject()
    def test_no_runtime_provenance(self):self.a['runtime_provenance_bound']=False;self.reject()
    def test_acceptance_not_promoted(self):self.a['ring_acquisition_accepted']=True;self.reject()
    def test_selector2_cannot_be_silently_projected(self):
        self.a['bindings'][0]['snapshot']['selector']=2
        self.rows[0]['snapshot']['selector']=2;self.reject()
    def test_unreturned_call(self):self.rows[1]['returned']=False;self.reject()
    def test_no_input_mutation(self):
        before=copy.deepcopy((self.a,self.rows));c.coverage(self.a,self.rows)
        self.assertEqual((self.a,self.rows),before)

if __name__=='__main__':unittest.main()
