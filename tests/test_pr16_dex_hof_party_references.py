"""party型batchだけの新統合境界。"""
import copy,unittest
from unittest.mock import patch
import pr16_dex_hof_party_references as m
FIXTURE=None
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit fixture required')
  self.raw,self.latest,self.parent,self.sources=FIXTURE
 def check(self):return m.measured_regions(self.raw,self.latest,self.parent,self.sources)
 def test_exact_two_six_byte_types(self):
  r,p=self.check();self.assertEqual(sorted((x.start,x.end-x.start)for x in r),[(0x08120CBC,6),(0x08126B0A,6)]);self.assertEqual(p['new_code'],2);self.assertEqual(p['new_boundary'],0)
  for f in('natural_gameplay_reachability_claimed','universal_heap_or_irq_lifetime_claimed','donor_leased','indirect_reference_completeness_claimed'):self.assertFalse(p[f])
 def test_parent_count(self):
  self.parent=copy.deepcopy(self.parent);self.parent['classified']=732
  with self.assertRaises(ValueError):self.check()
 def test_unknown_count(self):
  self.parent=copy.deepcopy(self.parent);self.parent['unclassified']=142
  with self.assertRaises(ValueError):self.check()
 def test_whole_candidate(self):
  raw=bytearray(self.raw);raw[-1]^=1
  with self.assertRaises(ValueError):m.regions(bytes(raw),self.latest,self.parent,self.sources)
 def test_latest_candidate(self):
  latest=copy.deepcopy(self.latest);latest['candidate']={}
  with self.assertRaises(ValueError):m.regions(self.raw,latest,self.parent,self.sources)
 def test_missing_each_consumer(self):
  for module,_ in m.MODULES:
   with patch.object(module,'_regions',return_value=([],{})):
    with self.assertRaises(ValueError):self.check()
 def test_entire_reviews(self):
  for p in m.REVIEWS:
   with patch.dict(m.REVIEWS,{p:dict(size=1,sha256='wrong')}):
    with self.assertRaises(ValueError):m.read_review(p)
 def test_all_old_windows_preserved(self):
  rows=m.protected_windows()
  for w in m.previous.protected_windows():self.assertIn(w,rows)
  self.assertEqual([(x['address'],x['size'])for x in rows],sorted(set((x['address'],x['size'])for x in rows)))
 def test_parent_not_mutated(self):
  before=copy.deepcopy(self.parent);self.check();self.assertEqual(before,self.parent)
 def test_parent_new_hits_still_unknown(self):
  self.check()
  for a in m.EXPECTED_HITS:self.assertFalse(next(h for h in self.parent['hits']if h['address']==a)['accepted'])
 def test_arbitrary_promotion_rejected(self):
  h=next(h for h in self.parent['hits']if not h['accepted']and h['address']not in m.EXPECTED_HITS);old=m.takeitem._regions
  def extra(*a):
   r,p=old(*a);return r+[m.d.TypedRegion(h['address'],h['address']+h['size'],m.takeitem.KIND,{})],p
  with patch.object(m.takeitem,'_regions',side_effect=extra):
   with self.assertRaises(ValueError):self.check()
 def test_duplicate_witness_rejected(self):
  old=m.takeitem._regions
  def duplicate(*a):
   r,p=old(*a);return r+r,p
  with patch.object(m.takeitem,'_regions',side_effect=duplicate):
   with self.assertRaises(ValueError):self.check()
 def test_unit_projection_only_exact_original_candidate_and_hit(self):
  before=copy.deepcopy(self.parent)
  for module,_ in m.MODULES:
   fixture=m.consumer_test_parent(self.parent,module)
   self.assertEqual(set(fixture),{'candidate','hits'});self.assertEqual(fixture['candidate'],self.parent['candidate'])
   self.assertEqual(fixture['hits'],[h for h in self.parent['hits']if h['address']==module.HIT])
   fixture['candidate']['sha256']='changed';fixture['hits'][0]['accepted']=True
  self.assertEqual(before,self.parent)
 def test_unit_projection_cannot_hide_duplicate_hit_or_wrong_frontier(self):
  parent=copy.deepcopy(self.parent);parent['hits'].append(copy.deepcopy(next(h for h in parent['hits']if h['address']==m.takeitem.HIT)))
  with self.assertRaises(ValueError):m.consumer_test_parent(parent,m.takeitem)
  parent=copy.deepcopy(self.parent);parent['hits']=[h for h in parent['hits']if h['address']!=m.takeitem.HIT]
  with self.assertRaises(ValueError):m.consumer_test_parent(parent,m.takeitem)
  parent=copy.deepcopy(self.parent);parent['classified']=732
  with self.assertRaises(ValueError):m.consumer_test_parent(parent,m.takeitem)
class DiagnosticCatalogTests(unittest.TestCase):
 def setUp(self):
  self.original={'status':'synthetic','cases':[{'tutor_id':0,'conditional_calls':[{'callee':1,'fields':[1,2]},{'callee':2,'fields':[3]}]},{'tutor_id':1,'conditional_calls':[{'callee':1,'fields':[1,2]},{'callee':1,'fields':[1,2]}]}]}
  self.packed=m.pack_tutor_diagnostic(self.original)
 def test_exact_roundtrip_all_fields_order_duplicates(self):self.assertEqual(m.unpack_tutor_diagnostic(self.packed),self.original)
 def test_shared_definition_not_shared_call_execution(self):self.assertEqual(len(self.packed['conditional_call_catalog']),2);self.assertEqual([len(c['conditional_call_ids'])for c in self.packed['cases']],[2,2])
 def test_not_aliased_or_mutated(self):
  before=copy.deepcopy(self.original);self.packed['conditional_call_catalog'][0]['fields'].append(99);self.assertEqual(before,self.original)
 def test_wrong_encoding(self):
  self.packed['case_encoding']='other'
  with self.assertRaises(ValueError):m.unpack_tutor_diagnostic(self.packed)
 def test_boolean_index(self):
  self.packed['cases'][0]['conditional_call_ids'][0]=True
  with self.assertRaises(ValueError):m.unpack_tutor_diagnostic(self.packed)
 def test_negative_and_oversize_id(self):
  for value in(-1,2):
   p=copy.deepcopy(self.packed);p['cases'][0]['conditional_call_ids'][0]=value
   with self.assertRaises(ValueError):m.unpack_tutor_diagnostic(p)
 def test_missing_call_reference(self):
  self.packed['cases'][0]['conditional_call_ids']=[0]
  with self.assertRaises(ValueError):m.unpack_tutor_diagnostic(self.packed)
 def test_unreferenced_extra_definition(self):
  self.packed['conditional_call_catalog'].append({'extra':True})
  with self.assertRaises(ValueError):m.unpack_tutor_diagnostic(self.packed)
 def test_duplicate_definition(self):
  self.packed['conditional_call_catalog'].append(copy.deepcopy(self.packed['conditional_call_catalog'][0]))
  with self.assertRaises(ValueError):m.unpack_tutor_diagnostic(self.packed)
 def test_mixed_embedded_and_shared_form(self):
  self.packed['cases'][0]['conditional_calls']=[]
  with self.assertRaises(ValueError):m.unpack_tutor_diagnostic(self.packed)
 def test_empty_original_calls(self):
  self.original['cases'][0]['conditional_calls']=[]
  with self.assertRaises(ValueError):m.pack_tutor_diagnostic(self.original)
 def test_reordered_calls_preserved_not_sorted(self):
  self.original['cases'][0]['conditional_calls'].reverse();self.assertEqual(m.unpack_tutor_diagnostic(m.pack_tutor_diagnostic(self.original)),self.original)
 def test_altered_payload_stays_detectable(self):
  self.packed['conditional_call_catalog'][0]['callee']=9;self.assertNotEqual(m.canonical(m.unpack_tutor_diagnostic(self.packed)),m.canonical(self.original))
 def test_double_encoding_rejected(self):
  with self.assertRaises(ValueError):m.pack_tutor_diagnostic(self.packed)
if __name__=='__main__':unittest.main()
