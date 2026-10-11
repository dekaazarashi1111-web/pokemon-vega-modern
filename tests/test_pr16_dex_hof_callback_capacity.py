"""新728親容量束縛の拒否試験。旧partial-space suiteは再走しない。"""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pr16_dex_hof_callback_capacity as m
import pr16_dex_hof_callback_chain as chain
class CapacityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  args=[(m.ROOT/p).read_bytes()for p in chain.PARENT_INPUTS]
  cls.parent=chain.parent(*args);cls.baseline=chain.previous.parent(*args[:-2])
 def evaluate(self,full=None,parent=None,baseline=None):
  return m.current_report(self.parent if full is None else full,parent_audit=self.parent if parent is None else parent,baseline_audit=self.baseline if baseline is None else baseline)
 def test_exact_728_parent_no_synthetic_extra_classification(self):
  r=self.evaluate();self.assertEqual(r['successor_plan']['parent_unknown_count'],146);self.assertEqual(r['successor_plan']['current_unknown_count'],146);self.assertEqual(r['successor_plan']['total_unprotected_bytes'],0);self.assertFalse(r['successor_plan']['lease_eligible']);self.assertFalse(r['successor_plan']['lease_authorized'])
 def test_all115_owners_and6528_unchanged(self):
  r=self.evaluate();self.assertEqual(r['successor_plan']['owner_count'],115);self.assertEqual(r['controller']['total_allocated_bytes'],6528);self.assertEqual(r['other_known_capacity']['sum_upper_bound_bytes'],1315)
 def test_parent_whole_candidate(self):
  p=copy.deepcopy(self.parent);p['candidate']={}
  with self.assertRaises(ValueError):self.evaluate(parent=p)
 def test_parent_unknown_fields(self):
  for key,value in [('target',1),('sha256','bad'),('reason','changed')]:
   p=copy.deepcopy(self.parent);next(h for h in p['hits']if not h['accepted'])[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.evaluate(parent=p)
 def test_parent_accepted_evidence_cannot_be_replaced(self):
  p=copy.deepcopy(self.parent);next(h for h in p['hits']if h['accepted'])['evidence']=[]
  with self.assertRaises(ValueError):self.evaluate(full=p,parent=p)
 def test_parent_counter(self):
  p=copy.deepcopy(self.parent);p['unclassified']=145
  with self.assertRaises(ValueError):self.evaluate(parent=p)
 def test_base_parent_still_exact(self):
  p=copy.deepcopy(self.baseline);p['classified']=728
  with self.assertRaises(ValueError):self.evaluate(baseline=p)
 def test_retained_accepted_cannot_change(self):
  f=copy.deepcopy(self.parent);next(h for h in f['hits']if h['accepted'])['sha256']='changed'
  with self.assertRaises(ValueError):self.evaluate(full=f)
 def test_lease_flag_cannot_promote(self):
  f=copy.deepcopy(self.parent);f['donor_leased']=True
  with self.assertRaises(ValueError):self.evaluate(full=f)
 def test_parent_input_full_hash(self):
  with patch.dict(m.INPUTS,{m.FRONTIER:dict(size=1,sha256='bad')}):
   with self.assertRaises(ValueError):self.evaluate()
 def test_parent_input_lf_and_not_symlink(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp)
   for path in m.INPUTS:
    q=root/path;q.parent.mkdir(parents=True,exist_ok=True);q.symlink_to(m.ROOT/path)
   with self.assertRaises(ValueError):m.read_inputs(root)
 def test_point_projection_is_not_safe_capacity(self):
  r=self.evaluate();self.assertEqual(r['successor_point_only_projection']['largest_gap_bytes'],1553);self.assertFalse(r['successor_point_only_projection']['safe_to_lease']);self.assertEqual(r['successor_plan']['total_unprotected_bytes'],0)
if __name__=='__main__':unittest.main()
