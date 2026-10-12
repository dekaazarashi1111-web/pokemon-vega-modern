"""全review封筒・原本維持・追加root role集合の新規境界試験。"""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_dex_hof_remaining_references as m
import pr16_dex_hof_remaining_chain as chain
class EnvelopeTests(unittest.TestCase):
 def test_exact_review_and_33_original_unknowns(self):
  r=m.read_review();self.assertEqual(len(r['expected_hit_addresses']),33)
  inherited=chain.parent((ROOT/chain.BASELINE).read_bytes(),(ROOT/chain.EARLIER).read_bytes(),(ROOT/chain.PARENT).read_bytes())
  unknown={h['address']for h in inherited['hits']if not h['accepted']}
  self.assertTrue(set(r['expected_hit_addresses'])<=unknown)
 def test_changed_whole_review(self):
  with tempfile.TemporaryDirectory()as td,patch.object(m,'ROOT',Path(td)):
   p=Path(td)/m.REVIEW;p.parent.mkdir(parents=True);p.write_bytes(b'{}\n')
   with self.assertRaises(ValueError):m.read_review()
 def test_wrong_candidate_cannot_reach_sources(self):
  with self.assertRaises(ValueError):m.regions(b'not-current',{'candidate':m.CANDIDATE},{'candidate':m.CANDIDATE},{})
 def test_closed_review_schema(self):
  with self.assertRaises(ValueError):m.measured_regions(b'',{},dict(classified=661,unclassified=213),{},{},{})
 def test_exact_prior_frontier(self):
  with self.assertRaises(ValueError):m.measured_regions(b'',{},dict(classified=660,unclassified=214),{},m.read_review(),{})
 def test_protected_window_dedup(self):
  w=dict(address=m.d.BASE+100,size=4,sha256='synthetic')
  windows=m.protected_windows({'a':w,'b':dict(w)})
  self.assertEqual(sum(x==w for x in windows),1)
 def test_conflicting_protected_windows(self):
  w=dict(address=m.d.BASE+100,size=4,sha256='synthetic')
  with self.assertRaises(ValueError):m.protected_windows({'a':w,'b':dict(w,sha256='other')})
 def test_zero_or_outside_protected_role(self):
  for w in [dict(address=m.d.BASE,size=0,sha256='x'),dict(address=0x02000000,size=4,sha256='x')]:
   with self.subTest(window=w),self.assertRaises(ValueError):m.protected_windows({'a':w})
 def test_missing_virtual_source_binding(self):
  r={'owners':{'test':{'sources':[dict(path='vendor/upstream/pokefirered/missing.c',size=1,sha256='x',git_blob_sha='y')]}}}
  with self.assertRaises(ValueError):m.owned_sources(r,{})
 def test_changed_project_source(self):
  with tempfile.TemporaryDirectory()as td,patch.object(m,'ROOT',Path(td)):
   (Path(td)/'test.c').write_bytes(b'x\n')
   r={'owners':{'test':{'sources':[dict(path='test.c',size=1,sha256='x',git_blob_sha='y')]}}}
   with self.assertRaises(ValueError):m.owned_sources(r,{})
if __name__=='__main__':unittest.main()
