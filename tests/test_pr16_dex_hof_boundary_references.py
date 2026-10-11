"""異種boundary・型分類・自然到達・容量保証の区別を検査する。"""
import copy,unittest
from unittest.mock import patch
import pr16_dex_hof_boundary_references as m
FIXTURE=None
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit whole-ROM fixture required')
  self.raw,self.latest,self.parent,self.sources=FIXTURE
 def check(self):return m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_exact_mixed_boundary_type(self):
  regions,proof=self.check();self.assertEqual(proof['new_boundary'],1);self.assertEqual(proof['new_code'],0);self.assertEqual(len(regions),1);self.assertEqual(regions[0].kind,m.mystery.KIND)
  for flag in('natural_gameplay_reachability_claimed','universal_heap_or_irq_lifetime_claimed','donor_leased','indirect_reference_completeness_claimed'):self.assertFalse(proof[flag])
 def test_exact_732_parent(self):
  self.parent=copy.deepcopy(self.parent);self.parent['classified']=729
  with self.assertRaises(ValueError):self.check()
 def test_exact_142_frontier(self):
  self.parent=copy.deepcopy(self.parent);self.parent['unclassified']=145
  with self.assertRaises(ValueError):self.check()
 def test_whole_candidate_required(self):
  raw=bytearray(self.raw);raw[-1]^=1
  with self.assertRaises(ValueError):m.regions(bytes(raw),self.latest,self.parent,self.sources)
 def test_wrong_latest_candidate(self):
  latest=copy.deepcopy(self.latest);latest['candidate']={}
  with self.assertRaises(ValueError):m.regions(self.raw,latest,self.parent,self.sources)
 def test_missing_boundary_not_silently_accepted(self):
  with patch.object(m.mystery,'_regions',return_value=([],{})):
   with self.assertRaises(ValueError):self.check()
 def test_whole_review_identity(self):
  for path in m.REVIEWS:
   with self.subTest(path=path),patch.dict(m.REVIEWS,{path:dict(size=1,sha256='wrong')}):
    with self.assertRaises(ValueError):m.read_review(path)
 def test_old_windows_are_retained(self):
  rows=m.protected_windows();old=m.previous.protected_windows();self.assertTrue(rows);self.assertEqual([(r['address'],r['size'])for r in rows],sorted(set((r['address'],r['size'])for r in rows)))
  for row in old:self.assertIn(row,rows)
 def test_no_parent_mutation(self):
  old=copy.deepcopy(self.parent);self.check();self.assertEqual(old,self.parent)
 def test_parent_unknown_not_mutated(self):
  self.check();self.assertFalse(next(h for h in self.parent['hits']if h['address']==m.EXPECTED_HITS[0])['accepted'])
 def test_no_arbitrary_type_promotion(self):
  hit=next(h for h in self.parent['hits']if not h['accepted']and h['address']not in m.EXPECTED_HITS)
  forged=m.d.TypedRegion(hit['address'],hit['address']+hit['size'],m.mystery.KIND,{})
  old=m.mystery._regions
  def extra(*args):
   r,p=old(*args);return [*r,forged],p
  with patch.object(m.mystery,'_regions',side_effect=extra):
   with self.assertRaises(ValueError):self.check()
 def test_duplicate_boundary_not_counted_twice(self):
  old=m.mystery._regions
  def duplicate(*args):
   r,p=old(*args);return r+r,p
  with patch.object(m.mystery,'_regions',side_effect=duplicate):
   with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main()
