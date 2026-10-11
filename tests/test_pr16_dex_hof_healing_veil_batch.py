"""新healing/veil serializerだけの合成契約。既accepted consumerの再走は行わない。"""
import copy,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_healing_veil_batch as m
FIXTURE=None
class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise unittest.SkipTest('new diagnostic/current fixture required')
  cls.raw,cls.latest,cls.parent,cls.sources=FIXTURE
 def run_scope(self,parent=None):return m.measured_regions(self.raw,self.latest,self.parent if parent is None else parent,self.sources)
 def test_exact_frozen_guard_batch(self):
  regions,proof=self.run_scope();self.assertEqual(len(regions),3)
  self.assertEqual((m.EXPECTED['classified'],m.EXPECTED['unclassified']),(756,118))
  self.assertEqual(len(proof['held_roots']),0);self.assertEqual(len(proof['consumers']),1)
  for key in('new_code','new_data','new_boundary'):self.assertEqual(proof[key],m.EXPECTED[key])
  self.assertFalse(proof['natural_gameplay_reachability_claimed']);self.assertFalse(proof['universal_heap_or_irq_lifetime_claimed'])
 def test_any_prior_or_promoted_parent_rejected(self):
  for classified in (619,735,741,743,747):
   parent=copy.deepcopy(self.parent);parent['classified']=classified;parent['unclassified']=874-classified
   with self.subTest(classified=classified),self.assertRaises(ValueError):self.run_scope(parent)
 def test_current_gate_rejects_diagnostic_or_changed_candidate(self):
  with patch.object(m,'identity',return_value={'size':1,'sha256':'different'}):
   with self.assertRaises(ValueError):m.regions(self.raw,self.latest,self.parent,self.sources)
 def test_all_retained_protected_windows(self):
  old={(w['address'],w['size']):w for w in m.previous.protected_windows()};now={(w['address'],w['size']):w for w in m.protected_windows()}
  self.assertTrue(all(now[k]==v for k,v in old.items()))
 def test_conflicting_shared_protection_rejected(self):
  old=m.previous.protected_windows()[0];changed=dict(old,sha256='conflict')
  with patch.object(m.MODULES[0][0],'protected_windows',return_value=[changed]):
   with self.assertRaises(ValueError):m.protected_windows()
 def test_original_parent_not_mutated(self):
  before=m.canonical(self.parent);self.run_scope();self.assertEqual(m.canonical(self.parent),before)
 def test_each_review_whole_binding(self):
  for _,path in m.ALL_MODULES:
   with self.subTest(path=path),patch.dict(m.REVIEWS,{path:{'size':1,'sha256':'forged'}}):
    with self.assertRaises(ValueError):m.read_review(path)
 def test_review_set_closed(self):self.assertEqual(set(m.REVIEWS),{p for _,p in m.ALL_MODULES})
 def test_each_projection_exact_deepcopy(self):
  for module,_ in m.ALL_MODULES:
   result=m.consumer_test_parent(self.parent,module);self.assertEqual(set(result),{'candidate','hits'})
   self.assertEqual([h['address']for h in result['hits']],m.hits(module));self.assertEqual(len(result['hits']),len(m.hits(module)))
   result['hits'][0]['reason']='local';self.assertNotEqual(result['hits'][0],next(h for h in self.parent['hits']if h['address']==m.hits(module)[0]))
 def test_projection_missing_rejected(self):
  p=dict(self.parent,hits=[])
  for module,_ in m.ALL_MODULES:
   with self.assertRaises(ValueError):m.consumer_test_parent(p,module)
 def test_projection_duplicate_rejected(self):
  for module,_ in m.ALL_MODULES:
   selected=[h for h in self.parent['hits']if h['address']in m.hits(module)];p=dict(self.parent,hits=selected+[selected[0]])
   with self.assertRaises(ValueError):m.consumer_test_parent(p,module)
 def test_sources_only_exact_public_subsets(self):
  for module,_ in m.ALL_MODULES:
   self.assertEqual(set(m.source_subset(module,self.sources)),set(module.SOURCE_IDS))
   with self.assertRaises(KeyError):m.source_subset(module,{})
 def test_all_fixtures_without_dropping_full_parent(self):
  tests=[SimpleNamespace()for _ in m.ALL_MODULES];m.install_fixtures(self.raw,self.latest,self.parent,self.sources,*tests)
  for (module,_),test in zip(m.ALL_MODULES,tests):self.assertEqual([h['address']for h in test.FIXTURE[1]['hits']],m.hits(module))
  self.assertEqual(len(self.parent['hits']),874);self.assertEqual((self.parent['classified'],self.parent['unclassified']),(753,121))
 def test_missing_fixture_rejected(self):
  with self.assertRaises(ValueError):m.install_fixtures(self.raw,self.latest,self.parent,self.sources)
 def test_guard_cannot_claim_new_type(self):
  with patch.object(m,'EXPECTED_HITS',[0x805D12F]):
   with self.assertRaises(ValueError):self.run_scope()
 def test_guard_cannot_claim_new_count(self):
  with patch.dict(m.EXPECTED,{'new_data':4}):
   with self.assertRaises(ValueError):self.run_scope()
 def test_changed_exact_category_count_rejected(self):
  with patch.object(m,'EXPECTED_CATEGORIES',{'invented':1}):
   with self.assertRaises(ValueError):self.run_scope()
 def test_source_review_current_bytes(self):
  for path,binding in m.REVIEWS.items():self.assertEqual(m.identity((m.ROOT/path).read_bytes()),binding)
 def test_each_missing_consumer_rejected(self):
  for module,_ in m.MODULES:
   with self.subTest(module=module.__name__),patch.object(module,'_regions',return_value=([],{})):
    with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_duplicate_minimum_witness_rejected(self):
  module,path=m.MODULES[0];regions,proof=module._regions(self.raw,self.parent,m.read_review(path),m.source_subset(module,self.sources))
  with patch.object(module,'_regions',return_value=(regions+[regions[0]],proof)):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_empty_frozen_hit_contract_rejected(self):
  with patch.object(m,'EXPECTED_HITS',[]):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_duplicate_frozen_hit_contract_rejected(self):
  with patch.object(m,'EXPECTED_HITS',m.EXPECTED_HITS+[m.EXPECTED_HITS[0]]):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_missing_frozen_hit_contract_rejected(self):
  with patch.object(m,'EXPECTED_HITS',m.EXPECTED_HITS[1:]):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_invalid_module_category_rejected(self):
  with patch.object(m.MODULES[0][0],'TYPE_CATEGORY','inferred'):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)

 def test_old_guard_not_repeated(self):self.assertEqual(m.GUARDS,())
 def test_additional_guard_rejected(self):
  with patch.object(m,'GUARDS',m.MODULES):
   with self.assertRaises(ValueError):self.run_scope()
 def test_accepted_projection_rejected(self):
  module=m.MODULES[0][0];p=copy.deepcopy(self.parent)
  next(h for h in p['hits']if h['address']==m.hits(module)[0])['accepted']=True
  with self.assertRaises(ValueError):m.consumer_test_parent(p,module)
 def test_duplicate_hit_list_rejected(self):
  module=m.MODULES[0][0]
  with patch.object(module,'HITS',m.hits(module)*2):
   with self.assertRaises(ValueError):m.hits(module)
 def test_mutating_consumer_rejected(self):
  module,path=m.MODULES[0];regions,proof=module._regions(self.raw,self.parent,m.read_review(path),m.source_subset(module,self.sources))
  def changed(raw,parent,review,sources):parent['unexpected']='mutation';return regions,proof
  with patch.object(module,'_regions',side_effect=changed):
   with self.assertRaises(ValueError):self.run_scope(copy.deepcopy(self.parent))
if __name__=='__main__':unittest.main()
