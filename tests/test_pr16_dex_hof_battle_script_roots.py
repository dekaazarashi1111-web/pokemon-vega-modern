"""effect231の新2hitだけ。JSON読戻しfixtureと意味再封印反証。"""
import copy,hashlib,json,unittest
from unittest import mock
import pr16_dex_hof_battle_script_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,raw,address):self.raw=raw;self.offset=address-0x08000000
 def __len__(self):return len(self.raw)
 def __getitem__(self,s):
  b=bytearray(self.raw[s])
  if s.start<=self.offset<s.stop:b[self.offset-s.start]^=1
  return bytes(b)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)
class BattleScriptRootTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit bounded-memory fixture required')
  cls.raw,cls.inherited,r,cls.sources=FIXTURE
  cls.review=json.loads(json.dumps(r))
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject(self,f):
  r=copy.deepcopy(self.review);f(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def test_01_two_minimum_types(self):
  old=copy.deepcopy(self.inherited);regions,p=self.check();self.assertEqual(self.inherited,old)
  self.assertEqual([(r.start,r.end-r.start,r.kind)for r in regions],[(h,4,v.KIND)for h in v.HITS]);self.assertEqual(p['typed_bytes'],8)
 def test_02_independent_minimum_geometry(self):
  for h in v.HITS:self.assertEqual(v.witness_geometry(v.evidence_template(h)),(h,4))
 def test_03_current_gate_rejects_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as p:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   p.assert_not_called()
 def test_04_current_gate_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value='accepted')as p:
   self.assertEqual(v.regions(*FIXTURE),'accepted');p.assert_called_once()
 def test_05_distinct_diagnostic(self):self.reject(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_06_closed_review(self):self.reject(lambda r:r.update(extra=1))
 def test_07_integer_schema(self):self.reject(lambda r:r.update(schema_version=True))
 def test_08_claims_cannot_promote_runtime(self):
  for name in v.CLAIMS:
   with self.subTest(name=name):self.reject(lambda r:r['claims'].update({name:True}))
 def test_09_no_extra_source(self):
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_10_whole_source_digests(self):
  for name in self.sources:
   s=dict(self.sources);s[name]+=b'\n'
   with self.subTest(name=name),self.assertRaises(ValueError):self.check(sources=s)
 def test_11_source_metadata_not_resealable(self):
  for name in v.SOURCE_IDS:
   with self.subTest(name=name):self.reject(lambda r:r['source_bindings'][name].update(sha256='0'*64))
 def test_12_common_proof_not_rewritten(self):self.reject(lambda r:r['common_root']['root_literals'][0].update(value=0))
 def test_13_window_deletion(self):self.reject(lambda r:r['windows'].pop())
 def test_14_window_expansion(self):self.reject(lambda r:r['windows'][0].update(size=4096))
 def test_15_window_reorder(self):self.reject(lambda r:r['windows'].reverse())
 def test_16_window_raw_fields_rejected(self):self.reject(lambda r:r['windows'][0].update(raw='forbidden'))
 def test_17_exact_inherited_hit(self):self.reject(lambda r:r['hits'][0].update(reason='changed'))
 def test_18_unknown_fields_cannot_promote(self):
  for key,val in [('accepted',True),('accepted',0),('owner_candidates',['owner']),('classification','DATA'),('size',True)]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][key]=val;r['hits'][0][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_19_duplicate_hit(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(i['hits'][0]))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_20_wrong_current_parent(self):
  i=copy.deepcopy(self.inherited);i['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_21_all_new_instruction_meanings(self):
  for instruction in v.INS.values():
   for off in range(instruction.size):
    raw=Mutation(self.raw,instruction.address+off)
    # digest guardを外しても独立semantic encoderが全byteを拒否する。
    with self.subTest(address=instruction.address+off,mode='independent_semantics'),self.assertRaises(ValueError):v.pointer_read_proof(raw)
    review=copy.deepcopy(self.review);inherited=copy.deepcopy(self.inherited)
    reseal(review,raw);reseal(inherited,raw)
    with self.subTest(address=instruction.address+off,mode='resealed_review'),self.assertRaises(ValueError):self.check(raw=raw,inherited=inherited,review=review)
 def test_22_all_true_pointer_words(self):
  for a in v.WORDS:
   for off in range(4):
    with self.subTest(address=a+off),self.assertRaises(ValueError):v.pointer_read_proof(Mutation(self.raw,a+off))
 def test_23_all_new_script_bytes(self):
  for a,name,_ in v.PROGRAM:
   for off in range(v.GRAMMAR[name][1]):
    with self.subTest(address=a+off),self.assertRaises(ValueError):v.bind_program(Mutation(self.raw,a+off))
 def test_24_all_move_effect_producers(self):
  for a,name,values in v.PROGRAM:
   if name=='jumpifmove':
    address=0x090421F4+12*values[2]
    with self.subTest(address=address),self.assertRaises(ValueError):v.bind_program(Mutation(self.raw,address))
 def test_25_resealed_semantics_still_rejected(self):
  for a in [v.HITS[0],v.HITS[1],0x091074E2,0x09107500,0x0911AF84,0x090D3D32,0x09161410,v.prior.EFFECTS+v.EFFECT*4,v.ROOT,v.ROOT+1,v.ROOT+13,0x0900723C]:
   raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
   with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
 def test_26_geometry_extra_field(self):
  e=v.evidence_template(v.HITS[0]);e['whole_range']=True
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_27_geometry_not_old_accepted_hit(self):
  e=v.evidence_template(v.HITS[0]);e['hit']=0x09003299
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_28_geometry_left_field(self):
  for key,value in [('address',v.HITS[0]-7),('size',9),('opcode',40)]:
   e=v.evidence_template(v.HITS[0]);e['left_command'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_29_geometry_right_field(self):
  for key,value in [('address',v.HITS[0]+1),('size',9),('opcode',255)]:
   e=v.evidence_template(v.HITS[0]);e['right_command'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_30_geometry_whole_pointer_not_upper_half(self):
  e=v.evidence_template(v.HITS[0]);e['whole_pointers'][0]['size']=2
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_31_geometry_cannot_claim_natural_reach(self):
  e=v.evidence_template(v.HITS[0]);e['claims']['natural_battle_entry_reachability_claimed']=True
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_32_geometry_byte_role_order(self):
  e=v.evidence_template(v.HITS[0]);e['byte_roles'].reverse()
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_33_actual_resolver_not_unknown_call(self):
  p=v.pointer_read_proof(self.raw);self.assertEqual(len(p),4)
  self.assertTrue(all(x['actual_resolver_table']and x['pointer_bytes']==4 for x in p))
 def test_34_two_registered_source_blocks(self):
  p=v.bind_program(self.raw);self.assertEqual(len(p),10)
  self.assertEqual(p[2]['fields'][-1]['value'],p[8]['address']);self.assertEqual(p[6]['address'],v.ROOT+61)
 def test_35_current_selector_different_moves(self):
  _,p=self.check();taken=[x for x in p['native_selector_models']if x['edge']=='taken'];self.assertEqual(len(taken),5);self.assertEqual(taken[1]['next_cursor'],0x09007236)
 def test_36_proof_has_no_native_trace(self):
  _,p=self.check()
  for m in p['native_selector_models']:self.assertEqual(set(m),{'command','opcode','edge','entry','next_cursor'})
 def test_37_json_roundtrip_fixture(self):self.assertEqual(self.review,json.loads(json.dumps(FIXTURE[2])))
 def test_38_no_blanket_root_classification(self):
  _,p=self.check();self.assertFalse(p['whole_script_range_classified']);self.assertFalse(p['attackcanceler_success_proven'])
