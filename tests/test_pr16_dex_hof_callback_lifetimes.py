"""新lifetime局所証拠を正式分類へ誤昇格させない統合テスト。"""
import copy,unittest
from unittest.mock import patch
import pr16_dex_hof_callback_lifetimes as m
FIXTURE=None
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit whole-ROM fixture required')
  self.raw,self.latest,self.parent,self.sources=FIXTURE
 def check(self):return m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_positive_current_local_contract(self):
  regions,proof=self.check();self.assertEqual(len(regions),len(m.EXPECTED_HITS));self.assertEqual(proof['party']['newly_classified'],0);self.assertFalse(proof['party']['full_root_to_hit_lifetime_proven'])
 def test_exact_parent(self):
  old=self.parent;self.parent=copy.deepcopy(old);self.parent['classified']=728
  with self.assertRaises(ValueError):self.check()
 def test_whole_candidate_required(self):
  raw=bytearray(self.raw);raw[-1]^=1
  with self.assertRaises(ValueError):m.regions(raw,self.latest,self.parent,self.sources)
 def test_wrong_latest_candidate(self):
  latest=copy.deepcopy(self.latest);latest['candidate']={}
  with self.assertRaises(ValueError):m.regions(self.raw,latest,self.parent,self.sources)
 def test_no_synthetic_party_promotion(self):
  with patch.object(m.setup,'check_local',return_value={'newly_classified':1,'root_to_hit_lifetime_proven':True}):
   with self.assertRaises(ValueError):self.check()
 def test_no_synthetic_menu_promotion(self):
  with patch.object(m.menu,'check_local',return_value={'newly_classified':1,'full_root_to_hit_lifetime_proven':True}):
   with self.assertRaises(ValueError):self.check()
 def test_whole_review_identity(self):
  with patch.dict(m.REVIEWS,{m.MENU:dict(size=1,sha256='wrong')}):
   with self.assertRaises(ValueError):m.read_review(m.MENU)
 def test_new_protected_roles_nonempty_and_ordered(self):
  rows=m.protected_windows();self.assertTrue(rows);self.assertEqual([(r['address'],r['size'])for r in rows],sorted(set((r['address'],r['size'])for r in rows)))
 def test_no_parent_mutation(self):
  old=copy.deepcopy(self.parent);self.check();self.assertEqual(old,self.parent)
 def test_old_party_unknown_still_unknown(self):
  self.check()
  for hit in(0x08124573,0x08126B0B):self.assertFalse(next(h for h in self.parent['hits']if h['address']==hit)['accepted'])
if __name__=='__main__':unittest.main()
