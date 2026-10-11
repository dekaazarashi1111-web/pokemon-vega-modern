"""694親・固定review・有限窓の閉じた封筒を反証する。"""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_script_references as m
import pr16_dex_hof_script_chain as chain
class EnvelopeTests(unittest.TestCase):
 def test_exact_review_original_unknowns(self):
  r=m.read_review();self.assertGreater(len(r['expected_hit_addresses']),0)
  a=chain.parent(*[(ROOT/p).read_bytes()for p in(chain.BASELINE,chain.EARLIER,chain.ANCESTOR,chain.PARENT,chain.PARENT_CHECKPOINT)])
  unknown={h['address']for h in a['hits']if not h['accepted']}
  self.assertTrue(set(r['expected_hit_addresses'])<=unknown)
  self.assertEqual(len(r['expected_hit_addresses']),len(set(r['expected_hit_addresses'])))
 def test_changed_whole_review(self):
  with tempfile.TemporaryDirectory()as td,patch.object(m,'ROOT',Path(td)):
   p=Path(td)/m.REVIEW;p.parent.mkdir(parents=True);p.write_bytes(b'{}\n')
   with self.assertRaises(ValueError):m.read_review()
 def test_wrong_candidate_cannot_reach_sources(self):
  with self.assertRaises(ValueError):m.regions(b'not-current',{'candidate':m.CANDIDATE},{'candidate':m.CANDIDATE},{})
 def test_closed_review_schema(self):
  with self.assertRaises(ValueError):m.measured_regions(b'',{},dict(classified=694,unclassified=180),{},{})
 def test_exact_prior_frontier(self):
  with self.assertRaises(ValueError):m.measured_regions(b'',{},dict(classified=661,unclassified=213),{},m.read_review())
 def test_protected_window_dedup(self):
  w=dict(address=m.d.BASE+100,size=4,sha256='synthetic')
  self.assertEqual(sum(x==w for x in m.protected_windows({'a':w,'b':dict(w)})),1)
 def test_conflicting_protected_windows(self):
  w=dict(address=m.d.BASE+100,size=4,sha256='synthetic')
  with self.assertRaises(ValueError):m.protected_windows({'a':w,'b':dict(w,sha256='other')})
 def test_zero_or_outside_protected_role(self):
  for w in [dict(address=m.d.BASE,size=0,sha256='x'),dict(address=0x02000000,size=4,sha256='x')]:
   with self.subTest(window=w),self.assertRaises(ValueError):m.protected_windows({'a':w})
if __name__=='__main__':unittest.main()
