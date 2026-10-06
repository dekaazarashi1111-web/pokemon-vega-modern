"""追加field-moveの名前・追加表だけによる誤採用を拒否する新scope試験。"""
import copy
import hashlib
import unittest
from unittest import mock
import pr16_dex_hof_field_move_roots as v
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

class FieldMoveHeldTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('明示的bounded-memory FIXTUREが必要')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def test_01_no_classification_and_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);regions,p=self.check()
  self.assertEqual(regions,[]);self.assertEqual(v.HITS,v.HELD_HITS);self.assertEqual(v.CLASSIFIED_HITS,());self.assertEqual(v.TYPE_CATEGORY,'guard');self.assertEqual(p['count'],0)
  self.assertEqual(p['retained_unknown_hits'],[0x091494EA]);self.assertEqual(self.inherited,before)
 def test_02_known_actual_literal_gap(self):
  p=self.check()[1]['root_findings']
  self.assertEqual(p['actual_description_table'],0x08419B0C)
  self.assertEqual(p['extended_description_table'],0x09169064)
  self.assertNotEqual(p['actual_description_table'],p['extended_description_table'])
 def test_03_stock_finite_equality_partition(self):
  p=self.check()[1]['producer_projection'];classes=p['classes']
  self.assertEqual(len(classes),13);self.assertEqual(p['possible_actions'],list(range(18,30)))
  self.assertEqual(p['other_class_size']+12,65536);self.assertFalse(p['required_actions_generated'])
 def test_04_all_uint16_values_partition_once(self):
  rows=v.producer_projection()['classes'][:-1]
  for move in range(65536):
   matches=[r for r in rows if r['move']==move]
   self.assertLessEqual(len(matches),1)
   for row in matches:self.assertTrue(set(row['actions']).isdisjoint((31,32)))
 def test_05_real_text_boundary_has_both_strings(self):
  self.assertEqual([(r['address'],r['size'])for r in v.TEXTS],[(0x091494E1,12),(0x091494ED,11)])
  self.assertEqual(v.encode_text(v.TEXTS[0]['text'])[-1],255)
  h=self.review['hits'][0];self.assertEqual(h['address'],v.TEXTS[0]['address']+9)
  self.assertEqual(h['address']+h['size'],v.TEXTS[1]['address']+1)
 def test_06_no_witness_even_root_verified_injected(self):
  for e in ({},{'root_verified':True},{'classified_window':{'address':0x091494EA,'size':4}}):
   with self.assertRaises(ValueError):v.witness_geometry(e)
  proof=self.check()[1];self.assertTrue(v.validate_held_proof(proof))
  for key,value in [('count',1),('hits',list(v.HITS)),('held_hits',[]),('root_verified',True),('all_possible_roots_absent_proven',True),('extended_code_globally_unreachable_proven',True),('full_story_reachability_claimed',True),('extra',True)]:
   bad=copy.deepcopy(proof);bad[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):v.validate_held_proof(bad)
  with self.assertRaises(ValueError):v.validate_held_proof(proof,True)
  with self.assertRaises(ValueError):v.validate_held_proof(proof,1)
 def test_07_diagnostic_rejected_at_public_entry(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_08_current_identity_gate_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value=([],v.held_proof_template()))as inner:
   rows,proof=v.regions(*FIXTURE);self.assertEqual(rows,[]);self.assertTrue(v.validate_held_proof(proof,True));inner.assert_called_once()
 def test_09_diagnostic_not_promoted_in_review(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_10_wrong_parent_candidate_rejected(self):
  inherited=copy.deepcopy(self.inherited);inherited['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=inherited)
 def test_11_closed_review(self):self.reject_review(lambda r:r.update(assumed_root=True))
 def test_12_integer_schema(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_13_no_source_name_to_root_promotion(self):self.reject_review(lambda r:r['claims'].update(root_verified=True))
 def test_14_no_table_presence_to_consumption_promotion(self):self.reject_review(lambda r:r['claims'].update(complete_consumer_byte_reads_proven=True))
 def test_15_no_dead_code_or_global_absence_claim(self):
  for k in ('all_possible_roots_absent_proven','extended_code_globally_unreachable_proven','indirect_reference_completeness_claimed'):
   with self.subTest(key=k):self.reject_review(lambda r:r['claims'].update({k:True}))
 def test_16_no_runtime_lifetime_or_donor_promotion(self):
  for k in ('actual_runtime_execution_observed','full_story_reachability_claimed','universal_allocation_epoch_proven','all_opaque_effects_proven','irq_noninterference_proven','donor_eligible','donor_leased'):
   with self.subTest(key=k):self.reject_review(lambda r:r['claims'].update({k:True}))
 def test_17_no_window_expansion(self):self.reject_review(lambda r:r['windows'][0].update(size=r['windows'][0]['size']+2))
 def test_18_no_window_reorder(self):self.reject_review(lambda r:r['windows'].reverse())
 def test_19_no_raw_window_field(self):self.reject_review(lambda r:r['windows'][0].update(raw='forbidden'))
 def test_20_every_instruction_byte_mutation(self):
  for ins in v.INS.values():
   for a in range(ins.address,ins.address+ins.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_21_every_literal_byte_mutation(self):
  for a in v.WORDS:
   for offset in range(4):
    with self.subTest(address=a+offset),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+offset))
 def test_22_every_protected_byte_mutation(self):
  for row in v.FIXED_WINDOWS:
   for a in range(row['address'],row['address']+row['size']):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_23_all_byte_resealed_mutations_rejected(self):
  for row in v.FIXED_WINDOWS:
   for a in range(row['address'],row['address']+row['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
 def test_24_sources_full_byte_identity(self):
  for key,data in self.sources.items():
   s=dict(self.sources);s[key]=data+b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_25_sources_closed(self):
  for s in ({**self.sources,'extra':b''},{k:v for k,v in self.sources.items()if k!='cfru-hooks'}):
   with self.assertRaises(ValueError):self.check(sources=s)
 def test_26_source_manifest_cannot_reseal(self):self.reject_review(lambda r:r['source_bindings']['cfru-hooks'].update(size=0))
 def test_27_duplicate_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(i['hits'][0]))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_28_nonunknown_hit_rejected_even_same_review(self):
  for key,value in [('accepted',True),('accepted',0),('owner_candidates',['claimed']),('classification','DATA'),('size',True),('kind','POINTER')]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][key]=value;r['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_29_stock_table_cannot_be_replaced_in_metadata(self):self.reject_review(lambda r:r['root_findings'].update(actual_description_table=0x09169064))
 def test_30_no_invented_epoch_contract(self):self.reject_review(lambda r:r['limits'].update(heap_epoch='assumed live'))
 def test_31_saved_json_array_shapes_accepted(self):
  self.assertIs(type(self.review['texts']),list);self.assertIs(type(self.review['hits']),list)
  self.assertEqual(self.check()[0],[])
 def test_32_extra_inherited_hit_preserved(self):
  i=copy.deepcopy(self.inherited);i['hits'].append({'address':0x083DD7E7,'accepted':True});before=copy.deepcopy(i)
  self.assertEqual(self.check(inherited=i)[0],[]);self.assertEqual(i,before)
