"""737親の独立fieldと必要最小consumerを結ぶ新scopeの反証。"""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_remaining_consumers as m
FIXTURE=None
class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise unittest.SkipTest('new diagnostic/current fixture required')
  cls.raw,cls.latest,cls.parent,cls.sources=FIXTURE
 def test_exact_frozen_batch_and_minimum_geometry(self):
  regions,proof=m.measured_regions(self.raw,self.latest,self.parent,self.sources)
  selected=[h['address']for h in self.parent['hits']if not h['accepted']and any(m.d.contains(r.start,r.end,h['address'],h['size'])for r in regions)]
  self.assertEqual(selected,m.EXPECTED_HITS);self.assertEqual(len(regions),len(m.EXPECTED_HITS))
  for key in('new_code','new_data','new_boundary'):self.assertEqual(proof[key],m.EXPECTED[key])
  self.assertFalse(proof['natural_gameplay_reachability_claimed']);self.assertFalse(proof['universal_heap_or_irq_lifetime_claimed'])
 def test_previous735_parent_rejected(self):
  parent=copy.deepcopy(self.parent);parent['classified']=735;parent['unclassified']=139
  with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,parent,self.sources)
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
 def test_each_missing_consumer_rejected(self):
  for module,_ in m.MODULES:
   with self.subTest(module=module.__name__),patch.object(module,'_regions',return_value=([],{})):
    with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_duplicate_minimum_witness_rejected(self):
  module,path=m.MODULES[0];regions,proof=module._regions(self.raw,self.parent,m.read_review(path),m.source_subset(module,self.sources))
  with patch.object(module,'_regions',return_value=(regions+[regions[0]],proof)):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_original_parent_not_mutated(self):
  before=m.canonical(self.parent);m.measured_regions(self.raw,self.latest,self.parent,self.sources);self.assertEqual(m.canonical(self.parent),before)
 def test_each_review_whole_binding(self):
  for _,path in m.MODULES:
   with self.subTest(path=path),patch.dict(m.REVIEWS,{path:{'size':1,'sha256':'forged'}}):
    with self.assertRaises(ValueError):m.read_review(path)
 def test_review_set_closed(self):self.assertEqual(set(m.REVIEWS),{p for _,p in m.MODULES})
 def test_each_projection_exact_deepcopy(self):
  for module,_ in m.MODULES:
   result=m.consumer_test_parent(self.parent,module);self.assertEqual(set(result),{'candidate','hits'})
   self.assertEqual([h['address']for h in result['hits']],m.hits(module));self.assertEqual(len(result['hits']),len(m.hits(module)))
   result['hits'][0]['reason']='local';self.assertNotEqual(result['hits'][0],next(h for h in self.parent['hits']if h['address']==m.hits(module)[0]))
 def test_projection_missing_rejected(self):
  p=dict(self.parent,hits=[])
  for module,_ in m.MODULES:
   with self.assertRaises(ValueError):m.consumer_test_parent(p,module)
 def test_projection_duplicate_rejected(self):
  for module,_ in m.MODULES:
   selected=[h for h in self.parent['hits']if h['address']in m.hits(module)];p=dict(self.parent,hits=selected+[selected[0]])
   with self.assertRaises(ValueError):m.consumer_test_parent(p,module)
 def test_sources_only_exact_public_subsets(self):
  for module,_ in m.MODULES:
   self.assertEqual(set(m.source_subset(module,self.sources)),set(module.SOURCE_IDS))
   with self.assertRaises(KeyError):m.source_subset(module,{})
 def test_all_fixtures_without_dropping_full_parent(self):
  tests=[SimpleNamespace()for _ in m.MODULES];m.install_fixtures(self.raw,self.latest,self.parent,self.sources,*tests)
  for (module,_),test in zip(m.MODULES,tests):self.assertEqual([h['address']for h in test.FIXTURE[1]['hits']],m.hits(module))
  self.assertEqual(len(self.parent['hits']),874);self.assertEqual((self.parent['classified'],self.parent['unclassified']),(737,137))
 def test_missing_fixture_rejected(self):
  with self.assertRaises(ValueError):m.install_fixtures(self.raw,self.latest,self.parent,self.sources)
 def test_empty_frozen_hit_contract_rejected(self):
  with patch.object(m,'EXPECTED_HITS',[]):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_duplicate_frozen_hit_contract_rejected(self):
  with patch.object(m,'EXPECTED_HITS',m.EXPECTED_HITS+[m.EXPECTED_HITS[0]]):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_missing_frozen_hit_contract_rejected(self):
  with patch.object(m,'EXPECTED_HITS',m.EXPECTED_HITS[1:]):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_changed_exact_category_count_rejected(self):
  with patch.object(m,'EXPECTED_CATEGORIES',{}):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_invalid_module_category_rejected(self):
  with patch.object(m.MODULES[0][0],'TYPE_CATEGORY','inferred'):
   with self.assertRaises(ValueError):m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_duplicate_hit_list_rejected(self):
  module=m.MODULES[0][0]
  with patch.object(module,'HITS',m.hits(module)*2):
   with self.assertRaises(ValueError):m.hits(module)
 def test_source_review_current_bytes(self):
  for path,binding in m.REVIEWS.items():self.assertEqual(m.identity((m.ROOT/path).read_bytes()),binding)
if __name__=='__main__':unittest.main()
