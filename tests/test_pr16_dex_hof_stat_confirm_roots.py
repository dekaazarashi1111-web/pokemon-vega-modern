"""stat/確認text1境界の新scopeだけを検査。既存suite/nativeを再走しない。"""
import copy,hashlib,unittest
from unittest import mock
import pr16_dex_hof_stat_confirm_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,raw,address):self.raw,self.offset=raw,address-0x08000000
 def __len__(self):return len(self.raw)
 def __getitem__(self,s):
  data=bytearray(self.raw[s])
  if s.start<=self.offset<s.stop:data[self.offset-s.start]^=1
  return bytes(data)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)
class StatConfirmTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('保存reviewのJSON読戻しと新scope sparse FIXTUREが必要')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def test_01_exact_one_window_and_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);regions,p=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in regions],[(a,a+4,v.KIND)for a in v.HITS]);self.assertEqual(self.inherited,before)
  self.assertEqual(p['composition']['complete_consumed_bytes'],8);self.assertFalse(p['donor_eligible'])
 def test_02_serializer_full_two_texts(self):
  self.assertEqual([t['text_ja']for t in v.TEXTS],['とくぼう','けっ'])
  self.assertEqual([v.serialize(t['text_ja'],self.sources)[-1]for t in v.TEXTS],[255,255])
  self.assertEqual([len(v.serialize(t['text_ja'],self.sources))for t in v.TEXTS],[5,3])
  self.assertEqual(v.HITS[0]+3,v.TEXTS[1]['address'])
 def test_03_full_pointer_fields_and_real_call(self):
  self.assertEqual(v.LITERALS[0x08125B34],v.TEXTS[0]['address']);self.assertEqual(v.LITERALS[0x08121980],v.TEXTS[1]['address'])
  self.assertEqual(v.INS[0x0811F5A8].args,(0x081218E8,))
  self.assertEqual(v.ROOT['left']['effect_return'],15);self.assertEqual(v.ROOT['left']['index'],12)
 def test_04_positive_cases(self):
  p=self.check()[1]['composition'];self.assertEqual([c['steps']for c in p['cases']],[57,519]);self.assertEqual([c['read_bytes']for c in p['cases']],[5,3]);self.assertFalse(p['pointer_host_seeded'])
 def test_05_closed_case_domain(self):
  for case in (True,None,15,16,'other'):
   with self.subTest(case=case),self.assertRaises(ValueError):v._compose(self.raw,case)
 def test_06_all_instruction_bytes_mutation(self):
  for ins in v.INS.values():
   for a in range(ins.address,ins.address+ins.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_07_all_table_dispatch_field_bytes_mutation(self):
  for a,n,_ in [*v.CORE_FIELDS,*[(a,4,value)for a,value in v.LITERALS.items()]]:
   for j in range(n):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+j),self.sources)
 def test_08_all_text_bytes_mutation(self):
  for row in v.TEXTS:
   for a in range(row['address'],row['address']+row['size']):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_09_all_protected_bytes_resealed_mutation(self):
  for row in v.FIXED_WINDOWS:
   for a in range(row['address'],row['address']+row['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
 def test_10_source_identity(self):
  for key,data in self.sources.items():
   sources=dict(self.sources);sources[key]=data+b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=sources)
 def test_11_source_set_and_manifest_closed(self):
  for sources in ({**self.sources,'extra':b''},{k:b for k,b in self.sources.items()if k!='pret-charmap.txt'}):
   with self.assertRaises(ValueError):self.check(sources=sources)
  self.reject_review(lambda r:r['source_bindings']['BPRJ.ld'].update(size=0))
 def test_12_review_schema_and_unexpected_claim(self):
  self.reject_review(lambda r:r.update(extra=True));self.reject_review(lambda r:r.update(schema_version=True))
 def test_13_current_diagnostic_separated(self):
  self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
  i=copy.deepcopy(self.inherited);i['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_14_public_wrapper_rejects_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_15_public_current_wrapper_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value=('regions','proof'))as inner:
   self.assertEqual(v.regions(*FIXTURE),('regions','proof'));inner.assert_called_once()
 def test_16_witness_geometry_is_exact(self):
  for hit in v.HITS:
   e=v.evidence_template(hit);self.assertEqual(v.witness_geometry(e),(hit,4))
   for key,value in [('extra',True),('root_verified',False),('all_hit_bytes_consumed',False),('donor_eligible',True),('indirect_reference_completeness_claimed',True),('pointer_host_seeded',True),('full_story_reachability_claimed',True)]:
    bad=copy.deepcopy(e);bad[key]=value
    with self.subTest(hit=hit,key=key),self.assertRaises(ValueError):v.witness_geometry(bad)
   bad=copy.deepcopy(e);bad['classified_window']['size']=5
   with self.assertRaises(ValueError):v.witness_geometry(bad)
   bad=copy.deepcopy(e);bad['texts'][0]['size']+=1
   with self.assertRaises(ValueError):v.witness_geometry(bad)
 def test_17_no_root_table_or_extent_expansion(self):
  self.reject_review(lambda r:r['root']['left'].update(effect_return=16));self.reject_review(lambda r:r['root']['right'].update(text=0x083DDE03))
  self.reject_review(lambda r:r['windows'][0].update(size=r['windows'][0]['size']+2));self.reject_review(lambda r:r['windows'].reverse())
 def test_18_no_claim_overstatement(self):
  for key,value in v.CLAIMS.items():
   if type(value)is bool:
    with self.subTest(key=key):self.reject_review(lambda r:r['claims'].update({key:not value}))
 def test_19_parent_unknown_identity_closed(self):
  for key,value in [('accepted',True),('accepted',0),('classification','DATA'),('owner_candidates',['x']),('size',True),('kind','POINTER')]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][key]=value;r['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_20_duplicate_and_order_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(i['hits'][0]))
  with self.assertRaises(ValueError):self.check(inherited=i)
  self.reject_review(lambda r:r['texts'].reverse())
 def test_21_inherited_unrelated_preserved(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(dict(address=0x08000000,accepted=True));before=copy.deepcopy(i);self.check(inherited=i);self.assertEqual(i,before)
 def test_22_live_field_clobber_rejected(self):
  first=v._compose(self.raw,'right');live=v.engine.future_live(first['trace'],len(first['boundaries']))
  site=first['boundaries'][0][0];a,n=live[0][0]
  with self.assertRaises(ValueError):v.compose_selected(self.raw,{site:[(a,1,0)]})
 def test_23_nonlive_write_is_allowed(self):
  out=v.compose_selected(self.raw,{0x08121908:[(0x0202F000,4,123)]});self.assertEqual(out['complete_consumed_bytes'],8)
 def test_24_ephemeral_window_contract(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x08121908:{'window_invalidated':True}})
 def test_25_window_epoch_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x08005B2C:{'window_invalidated':True}})
 def test_26_unknown_sites_not_silently_ignored(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0:[(0x0202F000,1,0)]})
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0:{'window_invalidated':True}})
 def test_27_contract_injection_rejected(self):
  bad=copy.deepcopy(v.CONTRACT);bad['right_ja']='host pointer seed'
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract=bad)
  self.reject_review(lambda r:r['input_contract'].update(extra='unbounded'))
 def test_28_saved_json_shapes(self):
  self.assertIs(type(self.review['texts']),list);self.assertIs(type(self.review['hits']),list);self.assertIs(type(self.review['windows']),list)
  self.assertTrue(self.check()[1]['composition']['nonlive_ram_erased_at_each_boundary'])
 def test_29_byte_consumers_cannot_be_replaced(self):
  for side in ('left','right'):
   self.reject_review(lambda r:r['root'][side].update(byte_read=0))
 def test_30_spdef_effect15_independent_table_index(self):
  self.assertEqual(v.ROOT['left']['table']+4*(15-3),v.ROOT['left']['cell'])
  self.assertEqual(v.LITERALS[v.ROOT['left']['cell']],v.ROOT['left']['target'])
