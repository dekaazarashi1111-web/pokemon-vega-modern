"""有限登録root由来の新opcode列/goto境界だけの独立意味・再封印反証。"""
import copy, hashlib, json, unittest
from unittest import mock
import pr16_dex_hof_finite_producer_roots as v
FIXTURE = None

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

class FiniteProducerRootTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('有限窓の明示fixtureが必要')
  cls.raw,cls.inherited,r,cls.sources=FIXTURE;cls.review=json.loads(json.dumps(r))
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,
                    self.review if review is None else review,self.sources if sources is None else sources)
 def reject(self,change):
  review=copy.deepcopy(self.review);change(review)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=review)
 def resealed_reject(self,address):
  raw=Mutation(self.raw,address);review=copy.deepcopy(self.review);inherited=copy.deepcopy(self.inherited)
  reseal(review,raw);reseal(inherited,raw)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(raw=raw,review=review,inherited=inherited)
 def test_01_two_minimum_types(self):
  before=copy.deepcopy((self.inherited,self.review));regions,proof=self.check()
  self.assertEqual([(r.start,r.end-r.start,r.kind)for r in regions],[(h,4,v.KIND)for h in v.HITS])
  self.assertEqual(proof['typed_bytes'],8);self.assertEqual((self.inherited,self.review),before)
 def test_02_json_roundtrip(self):self.assertEqual(self.review,json.loads(json.dumps(FIXTURE[2])))
 def test_03_current_identity_rejects_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as classifier:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   classifier.assert_not_called()
 def test_04_current_identity_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value='受入')as classifier:
   self.assertEqual(v.regions(*FIXTURE),'受入');classifier.assert_called_once()
 def test_05_distinct_diagnostic(self):self.reject(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_06_closed_review(self):self.reject(lambda r:r.update(extra=1))
 def test_07_schema_bool_rejected(self):self.reject(lambda r:r.update(schema_version=True))
 def test_08_all_forbidden_claims(self):
  for key in v.CLAIMS:
   with self.subTest(key=key):self.reject(lambda r:r['claims'].update({key:True}))
 def test_09_extra_source(self):
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_10_missing_source(self):
  for key in self.sources:
   sources=dict(self.sources);del sources[key]
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(sources=sources)
 def test_11_whole_source_identity(self):
  for key in self.sources:
   sources=dict(self.sources);sources[key]+=b'\n'
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(sources=sources)
 def test_12_resealed_source_metadata(self):
  for key in self.sources:
   sources=dict(self.sources);sources[key]+=b'\n';review=copy.deepcopy(self.review)
   review['source_bindings'][key].update(v.identity(sources[key]))
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(review=review,sources=sources)
 def test_13_independent_common_root(self):self.reject(lambda r:r['common_root']['root_literals'][0].update(value=0))
 def test_14_common_path_deletion(self):self.reject(lambda r:r['common_root']['root_paths'].pop())
 def test_15_window_deletion(self):self.reject(lambda r:r['windows'].pop())
 def test_16_window_expansion(self):self.reject(lambda r:r['windows'][0].update(size=4096))
 def test_17_window_reorder(self):self.reject(lambda r:r['windows'].reverse())
 def test_18_window_raw_data_forbidden(self):self.reject(lambda r:r['windows'][0].update(raw='禁止'))
 def test_19_inherited_row_preserved(self):self.reject(lambda r:r['hits'][0].update(reason='変更'))
 def test_20_inherited_duplicates(self):
  inherited=copy.deepcopy(self.inherited);inherited['hits'].append(copy.deepcopy(inherited['hits'][0]))
  with self.assertRaises(ValueError):self.check(inherited=inherited)
 def test_21_unowned_unknown_only(self):
  for key,value in [('accepted',True),('accepted',0),('owner_candidates',['owner']),('classification','DATA'),('size',True)]:
   inherited=copy.deepcopy(self.inherited);review=copy.deepcopy(self.review)
   for row in inherited['hits']:
    if row['address']==v.HITS[0]:row[key]=value
   review['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=inherited,review=review)
 def test_22_wrong_parent_candidate(self):
  inherited=copy.deepcopy(self.inherited);inherited['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=inherited)
 def test_23_all_semantic_instruction_bytes(self):
  for instruction in v.INS.values():
   for offset in range(instruction.size):
    address=instruction.address+offset
    with self.subTest(address=address),self.assertRaises(ValueError):v.semantic_bindings(Mutation(self.raw,address))
 def test_24_all_semantic_instruction_bytes_resealed(self):
  for instruction in v.INS.values():
   for offset in range(instruction.size):
    with self.subTest(address=instruction.address+offset):self.resealed_reject(instruction.address+offset)
 def test_25_all_true_slot_literal_bytes(self):
  for address in v.WORDS:
   for offset in range(4):
    with self.subTest(address=address+offset),self.assertRaises(ValueError):v.semantic_bindings(Mutation(self.raw,address+offset))
 def test_26_all_slot_literal_bytes_resealed(self):
  for address in v.WORDS:
   for offset in range(4):
    with self.subTest(address=address+offset):self.resealed_reject(address+offset)
 def test_27_all_program_bytes(self):
  for address,name,_ in v.PROGRAM:
   for offset in range(v.GRAMMAR[name][1]):
    with self.subTest(address=address+offset),self.assertRaises(ValueError):v.bind_program(Mutation(self.raw,address+offset))
 def test_28_all_program_bytes_resealed(self):
  for address,name,_ in v.PROGRAM:
   for offset in range(v.GRAMMAR[name][1]):
    with self.subTest(address=address+offset):self.resealed_reject(address+offset)
 def test_29_all_current_move_producers(self):
  for move in v.MOVE_EFFECTS:
   address=0x090421F4+12*move
   with self.subTest(move=move),self.assertRaises(ValueError):v.bind_program(Mutation(self.raw,address))
 def test_30_current_move_producers_resealed(self):
  for move in v.MOVE_EFFECTS:
   with self.subTest(move=move):self.resealed_reject(0x090421F4+12*move)
 def test_31_heal_pulse_prefix(self):
  rows=v.bind_program(self.raw);rows=[r for r in rows if v.ROOTS[233]<=r['address']<0x090073A9]
  self.assertEqual(len(rows),6);self.assertEqual(sum(r['size']for r in rows),36)
 def test_32_topsy_turvy_prefix(self):
  rows=v.bind_program(self.raw);rows=[r for r in rows if v.ROOTS[234]<=r['address']<0x09007434]
  self.assertEqual(len(rows),13);self.assertEqual(sum(r['size']for r in rows),59)
 def test_33_selector_taken_next_are_distinct(self):
  controls=v.control_proof(self.raw)
  for a,taken,nxt in [(0x09007386,0x090073EE,0x09007392),(0x0900740D,0x09007434,0x09007419)]:
   rows=[r for r in controls if r['command']==a]
   self.assertEqual([(r['edge'],r['next_cursor'])for r in rows],[('taken',taken),('next',nxt)])
 def test_34_goto_has_no_fallthrough(self):
  rows=[r for r in v.control_proof(self.raw)if r['command']==0x0900742F]
  self.assertEqual([(r['edge'],r['next_cursor'])for r in rows],[('taken',0x081BA90A)])
 def test_35_all_four_opcode_bytes_actually_read(self):
  rows=v.dispatch_proof(self.raw);actual={a for r in rows for a in r['opcode_byte_reads']}
  self.assertTrue(set(range(v.HITS[0],v.HITS[0]+4))<=actual)
  self.assertEqual([r['opcode']for r in rows],[0xFF26,3,0xFF09])
  self.assertTrue(all(r['command_entry_condition']is True and r['handler_executed']is False for r in rows))
 def test_36_real_primary_secondary_slots(self):
  rows=v.dispatch_proof(self.raw)
  self.assertEqual([r['dispatch_slots']for r in rows],[[v.prior.PRIMARY+255*4,v.prior.SECONDARY+38*4],
   [v.prior.PRIMARY+3*4],[v.prior.PRIMARY+255*4,v.prior.SECONDARY+9*4]])
  self.assertEqual([r['cursor_at_handler']for r in rows],[0x0900739D,0x0900739E,0x090073A0])
 def test_37_counter_pointer_native_read(self):
  rows=v.pointer_read_proof(self.raw)
  self.assertEqual([(r['command'],r['pointer'])for r in rows],[(0x0900739F,0x090073D1),(0x09007434,0x09008E13)])
  self.assertTrue(all(r['pointer_bytes']==4 and r['distinct_bank_value_cases']==4 for r in rows))
 def test_38_geometry_exactly_eight_bytes(self):
  self.assertEqual([v.witness_geometry(v.evidence_template(h))for h in v.HITS],[(h,4)for h in v.HITS])
 def test_39_geometry_rejects_every_changed_field(self):
  for hit in v.HITS:
   original=v.evidence_template(hit)
   for key in original:
    evidence=copy.deepcopy(original);evidence[key]=None
    with self.subTest(hit=hit,key=key),self.assertRaises((ValueError,TypeError,KeyError)):v.witness_geometry(evidence)
 def test_40_each_opcode_role_must_match(self):
  for hit in v.HITS:
   for index in range(4):
    evidence=v.evidence_template(hit);evidence['byte_roles'][index]='unknown'
    with self.subTest(hit=hit,index=index),self.assertRaises(ValueError):v.witness_geometry(evidence)
 def test_41_independent_root_and_effect(self):
  for hit in v.HITS:
   for key in ('root','effect'):
    evidence=v.evidence_template(hit);evidence[key]^=1
    with self.subTest(hit=hit,key=key),self.assertRaises(ValueError):v.witness_geometry(evidence)
 def test_42_foreign_old_hit_forbidden(self):
  for hit in [0x09003299,0x090071FF,0x0900723E,0x09007271,0x09005D94,0x0818DD5D]:
   with self.subTest(hit=hit),self.assertRaises(ValueError):v.evidence_template(hit)
 def test_43_geometry_extra_key_forbidden(self):
  for hit in v.HITS:
   evidence=v.evidence_template(hit);evidence['extra']=True
   with self.assertRaises(ValueError):v.witness_geometry(evidence)
 def test_44_whole_pointer_resealed_claim_rejected(self):
  for hit in v.HITS:
   for p in range(len(v.evidence_template(hit)['whole_pointers'])):
    evidence=v.evidence_template(hit);evidence['whole_pointers'][p]['value']^=1
    with self.subTest(hit=hit,p=p),self.assertRaises(ValueError):v.witness_geometry(evidence)
 def test_45_whole_commands_not_typed(self):
  regions,_=self.check()
  for region in regions:
   self.assertEqual(region.end-region.start,4)
   self.assertFalse(any(region.start<=root<region.end for root in v.ROOTS.values()))
 def test_46_no_mutation_of_old_parent_rows(self):
  inherited=copy.deepcopy(self.inherited)
  inherited['hits'].append(dict(address=0x090071FF,accepted=True,classification='old',size=4,marker={'keep':[1,2]}))
  before=copy.deepcopy(inherited);regions,_=self.check(inherited=inherited)
  self.assertEqual(inherited,before);self.assertEqual(len(regions),2)
 def test_47_dispatch_rejects_every_opcode_byte(self):
  for a in [0x0900739C,0x0900739D,0x0900739E,0x0900739F,0x090073A0]:
   with self.subTest(address=a):self.resealed_reject(a)
 def test_48_review_must_retain_unknown_rows(self):
  self.reject(lambda r:r['hits'].reverse())
  self.reject(lambda r:r['hits'].pop())
 def test_49_source_shapes_are_fixed(self):
  self.assertEqual(v.GRAMMAR['attackstringnoprotean'],(0xFF26,2,()))
  self.assertEqual(v.GRAMMAR['ppreduce'],(3,1,()))
 def test_50_reachability_not_inferred(self):
  _,proof=self.check()
  for key in v.CLAIMS:self.assertIs(proof[key],False)
  self.assertEqual(proof['native_dispatch_models'],v.dispatch_proof(self.raw))
