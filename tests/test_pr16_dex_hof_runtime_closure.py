"""実consumer型と自然到達・容量保証を混同しない新統合テスト。"""
import copy,unittest
from unittest.mock import patch
import pr16_dex_hof_runtime_closure as m
FIXTURE=None
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit whole-ROM fixture required')
  self.raw,self.latest,self.parent,self.sources=FIXTURE
 def check(self):return m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_positive_local_consumer_contract(self):
  regions,proof=self.check();self.assertEqual(proof['new_code'],len(m.EXPECTED_HITS));self.assertFalse(proof['natural_gameplay_reachability_claimed']);self.assertFalse(proof['universal_heap_or_irq_lifetime_claimed']);self.assertFalse(proof['donor_leased'])
 def test_exact_parent(self):
  self.parent=copy.deepcopy(self.parent);self.parent['classified']=728
  with self.assertRaises(ValueError):self.check()
 def test_whole_candidate_required(self):
  raw=bytearray(self.raw);raw[-1]^=1
  with self.assertRaises(ValueError):m.regions(raw,self.latest,self.parent,self.sources)
 def test_wrong_latest_candidate(self):
  latest=copy.deepcopy(self.latest);latest['candidate']={}
  with self.assertRaises(ValueError):m.regions(self.raw,latest,self.parent,self.sources)
 def test_missing_consumer_never_silently_reduces_expected(self):
  with patch.object(m.direct,'_regions',return_value=([],{})):
   with self.assertRaises(ValueError):self.check()
 def test_whole_review_identity(self):
  for path in m.REVIEWS:
   with self.subTest(path=path),patch.dict(m.REVIEWS,{path:dict(size=1,sha256='wrong')}):
    with self.assertRaises(ValueError):m.read_review(path)
 def test_new_protected_roles_nonempty_and_ordered(self):
  rows=m.protected_windows();self.assertTrue(rows);self.assertEqual([(r['address'],r['size'])for r in rows],sorted(set((r['address'],r['size'])for r in rows)))
 def test_all_inherited_party_boundaries_are_protected_from_audio_roles(self):
  import pr16_dex_hof_callback_party as a
  import pr16_dex_hof_callback_party_task as b
  import pr16_dex_hof_lifetime_setup as c
  import pr16_dex_hof_lifetime_menu as d
  windows=m.protected_windows();roles=[]
  for module in (a,b,c,d):
   roles.extend((ins.address,ins.size)for rows in module.BLOCKS.values()for ins in rows)
   roles.extend((address,4)for address in module.LITERALS)
  roles.extend((address,4)for address in c.TABLE)
  roles.extend((address,size)for address,size,_ in a.DATA_FIELDS.values())
  self.assertGreater(len(roles),3224)
  for address,size in roles:
   self.assertTrue(any(w['address']<=address and address+size<=w['address']+w['size']for w in windows),(address,size))
 def test_no_parent_mutation(self):
  old=copy.deepcopy(self.parent);self.check();self.assertEqual(old,self.parent)
 def test_parent_unknowns_not_mutated_in_place(self):
  self.check()
  for hit in m.EXPECTED_HITS:self.assertFalse(next(h for h in self.parent['hits']if h['address']==hit)['accepted'])
 def test_no_arbitrary_type_promotion(self):
  hit=next(h for h in self.parent['hits']if not h['accepted']and h['address']not in m.EXPECTED_HITS)
  forged=m.d.TypedRegion(hit['address'],hit['address']+hit['size'],'rooted_thumb_instruction_stream',{})
  old=m.direct._regions
  def extra(*args):
   r,p=old(*args);return [*r,forged],p
  with patch.object(m.direct,'_regions',side_effect=extra):
   with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main()
