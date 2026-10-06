"""735親からSummaryの最小型だけを追加する新scope結合反証。"""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_summary_references as m
FIXTURE=None
class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise unittest.SkipTest('new diagnostic/current fixture required')
  cls.raw,cls.latest,cls.parent,cls.sources=FIXTURE
 def test_exact_two_minimum_types_only(self):
  regions,proof=m.measured_regions(self.raw,self.latest,self.parent,self.sources)
  selected=[h['address']for h in self.parent['hits']if not h['accepted']and any(m.d.contains(r.start,r.end,h['address'],h['size'])for r in regions)]
  self.assertEqual(selected,m.EXPECTED_HITS);self.assertEqual(len(regions),2)
  self.assertEqual(proof['new_code'],1);self.assertEqual(proof['new_data'],1)
  self.assertFalse(proof['natural_gameplay_reachability_claimed']);self.assertFalse(proof['universal_heap_or_irq_lifetime_claimed'])
 def test_older_parent_is_not_current_parent(self):
  parent=copy.deepcopy(self.parent);parent['classified']=733;parent['unclassified']=141
  with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,parent,self.sources)
 def test_current_gate_rejects_diagnostic_or_changed_candidate(self):
  with patch.object(m,'identity',return_value={'size':1,'sha256':'different'}):
   with self.assertRaises(ValueError):m.regions(self.raw,self.latest,self.parent,self.sources)
 def test_every_old_protected_window_retained(self):
  old={(w['address'],w['size']):w for w in m.previous.protected_windows()};now={(w['address'],w['size']):w for w in m.protected_windows()}
  self.assertTrue(all(now[k]==v for k,v in old.items()))
 def test_same_window_conflicting_identity_rejected(self):
  old=m.previous.protected_windows()[0];changed=dict(old,sha256='conflict')
  with patch.object(m.summary,'protected_windows',return_value=[changed]):
   with self.assertRaises(ValueError):m.protected_windows()
 def test_missing_consumer_cannot_reduce_expected_count(self):
  with patch.object(m.nature,'_regions',return_value=([],{})):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_duplicate_consumer_container_rejected(self):
  region=m.d.TypedRegion(m.EXPECTED_HITS[0]-1,m.EXPECTED_HITS[0]+5,m.summary.KIND,{})
  with patch.object(m.summary,'_regions',return_value=([region,region],{})):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_empty_review_binding_rejected(self):
  with patch.dict(m.REVIEWS,{m.SUMMARY:{'size':1,'sha256':'wrong'}}):
   with self.assertRaises(ValueError):m.read_review(m.SUMMARY)
 def test_original_parent_is_unchanged_by_measurement(self):
  before=m.canonical(self.parent);m.measured_regions(self.raw,self.latest,self.parent,self.sources);self.assertEqual(m.canonical(self.parent),before)
 def test_projection_only_has_independent_hit_and_candidate(self):
  result=m.consumer_test_parent(self.parent,m.summary);self.assertEqual(set(result),{'candidate','hits'});self.assertEqual(len(result['hits']),1)
  self.assertEqual(result['hits'][0],next(h for h in self.parent['hits']if h['address']==m.summary.HIT))
  result['hits'][0]['reason']='local';self.assertNotEqual(result['hits'][0],next(h for h in self.parent['hits']if h['address']==m.summary.HIT))
 def test_projection_rejects_missing_original_hit(self):
  p={'classified':735,'unclassified':139,'candidate':self.parent['candidate'],'hits':[]}
  with self.assertRaises(ValueError):m.consumer_test_parent(p,m.summary)
 def test_projection_rejects_duplicate_original_hit(self):
  h=next(h for h in self.parent['hits']if h['address']==m.summary.HIT);p=dict(self.parent,hits=[h,h])
  with self.assertRaises(ValueError):m.consumer_test_parent(p,m.summary)
 def test_source_subsets_exact_and_no_extra_private_source(self):
  for module,_ in m.MODULES:
   self.assertEqual(set(m.source_subset(module,self.sources)),set(module.SOURCE_IDS))
 def test_source_subset_missing_entry_rejected(self):
  with self.assertRaises(KeyError):m.source_subset(m.summary,{})
 def test_review_manifest_complete(self):
  self.assertEqual(set(m.REVIEWS),{p for _,p in m.MODULES})
  for p,binding in m.REVIEWS.items():self.assertEqual(m.identity((m.ROOT/p).read_bytes()),binding)
 def test_module_fixture_projection_does_not_drop_full_chain(self):
  from types import SimpleNamespace
  a,b=SimpleNamespace(),SimpleNamespace();m.install_fixtures(self.raw,self.latest,self.parent,self.sources,a,b)
  self.assertEqual(a.FIXTURE[1]['hits'][0]['address'],m.summary.HIT);self.assertEqual(b.FIXTURE[1]['hits'][0]['address'],m.nature.HIT)
  self.assertEqual(len(self.parent['hits']),874);self.assertEqual((self.parent['classified'],self.parent['unclassified']),(735,139))
if __name__=='__main__':unittest.main()
