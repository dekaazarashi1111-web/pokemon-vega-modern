"""新しいgoto/FF09境界2件だけのJSON読戻しfixture・独立意味・再封印反証。"""
import copy, hashlib, json, unittest
from unittest import mock
import pr16_dex_hof_battle_tail_roots as v
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

class BattleTailRootTests(unittest.TestCase):
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
 def test_31_full_embargo_serialization(self):
  rows=v.bind_program(self.raw);embargo=[r for r in rows if 0x09007236<=r['address']<0x09007273]
  self.assertEqual(len(embargo),13);self.assertEqual(sum(r['size']for r in embargo),61)
  self.assertEqual(embargo[-1]['address'],v.HITS[1]-3)
 def test_32_recycle_prefix_serialization(self):
  rows=v.bind_program(self.raw);prefix=[r for r in rows if 0x09005D7F<=r['address']<0x09005D96]
  self.assertEqual(len(prefix),4);self.assertEqual(sum(r['size']for r in prefix),23)
 def test_33_notequals_taken_and_next(self):
  rows=[r for r in v.control_proof(self.raw)if r['command']==0x09005D80]
  self.assertEqual([(r['edge'],r['next_cursor'])for r in rows],[('taken',0x09005D96),('next',0x09005D8C)])
 def test_34_powder_third_selector(self):
  rows=[r for r in v.control_proof(self.raw)if r['command']==0x090071D3]
  self.assertEqual([(r['edge'],r['next_cursor'])for r in rows],[('taken',0x09007273),('next',0x090071DF)])
 def test_35_embargo_second_selector(self):
  rows=[r for r in v.control_proof(self.raw)if r['command']==0x090071C7]
  self.assertEqual(rows[0]['next_cursor'],0x09007236)
 def test_36_goto_has_no_fallthrough(self):
  rows=[r for r in v.control_proof(self.raw)if r['opcode']==40]
  self.assertEqual([(r['command'],r['edge'],r['next_cursor'])for r in rows],[(0x0900726E,'taken',0x081BA90A),(0x09005D91,'taken',0x081BA8E3)])
 def test_37_real_bank1_attacker_read(self):
  rows=v.pointer_read_proof(self.raw);row=next(r for r in rows if r['bank_operand']==1)
  self.assertEqual(row['resolver_slot'],0x09161414);self.assertEqual(row['bank_read_address'],0x02023CCB)
  self.assertEqual(row['distinct_bank_value_cases'],4);self.assertTrue(row['actual_resolver_table'])
 def test_38_bank0_separate_target_read(self):
  row=next(r for r in v.pointer_read_proof(self.raw)if r['bank_operand']==0)
  self.assertEqual(row['resolver_slot'],0x09161410);self.assertEqual(row['bank_read_address'],0x02023CCC)
 def test_39_no_unknown_resolver_substitution(self):
  for address in (0x09161414,0x090D3D84,0x090D3D86,0x090D3D88,0x090D3DA8):
   with self.subTest(address=address):self.resealed_reject(address)
 def test_40_geometry_exact_minimum(self):
  for hit in v.HITS:self.assertEqual(v.witness_geometry(v.evidence_template(hit)),(hit,4))
 def test_41_geometry_rejects_extra(self):
  e=v.evidence_template(v.HITS[0]);e['whole_range']=True
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_42_old_hits_stay_excluded(self):
  for old in(0x09003299,0x090071FF,0x0900723E):
   e=v.evidence_template(v.HITS[0]);e['hit']=old
   with self.subTest(hit=old),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_43_geometry_left_complete(self):
  for key,value in [('address',v.HITS[0]-2),('size',4),('opcode',29)]:
   e=v.evidence_template(v.HITS[0]);e['left_command'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_44_geometry_right_complete(self):
  for key,value in [('address',v.HITS[0]+1),('size',9),('opcode',255)]:
   e=v.evidence_template(v.HITS[0]);e['right_command'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_45_geometry_pointer_full_width(self):
  for row in(0,1):
   e=v.evidence_template(v.HITS[0]);e['whole_pointers'][row]['size']=2
   with self.subTest(row=row),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_46_geometry_roots_cannot_swap(self):
  e=v.evidence_template(v.HITS[0]);e['root']=v.ROOTS[231]
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_47_geometry_byte_roles_cannot_swap(self):
  e=v.evidence_template(v.HITS[0]);e['byte_roles'].reverse()
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_48_geometry_rejects_all_promotions(self):
  for key in v.CLAIMS:
   e=v.evidence_template(v.HITS[0]);e['claims'][key]=True
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_49_proof_retains_only_finite_control_summary(self):
  _,proof=self.check()
  for row in proof['native_selector_models']:self.assertEqual(set(row),{'command','opcode','edge','entry','next_cursor'})
 def test_50_every_actual_read_is_protected(self):
  allowed=set()
  for window in v.protected_windows(self.review):allowed.update(range(window['address'],window['address']+window['size']))
  parent=self.raw;observed=set()
  class Audit:
   def __len__(self):return len(parent)
   def __getitem__(self,s):
    self_slice=set(range(s.start+0x08000000,s.stop+0x08000000));observed.update(self_slice)
    if not self_slice<=allowed:raise AssertionError('保護窓外の読取り')
    return parent[s]
  self.check(raw=Audit());self.assertTrue(observed);self.assertLessEqual(observed,allowed)
 def test_51_bool_geometry_rejected(self):
  e=v.evidence_template(v.HITS[0]);e['effect']=True
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_52_no_blanket_or_lifetime_promotion(self):
  _,proof=self.check()
  for key in v.CLAIMS:self.assertIs(proof[key],False)
