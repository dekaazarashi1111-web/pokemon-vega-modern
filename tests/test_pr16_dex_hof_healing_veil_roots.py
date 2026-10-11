"""回復/壁の新登録根3境界だけの独立意味・再封印反証。"""
import copy, hashlib, json, unittest
from unittest import mock
import pr16_dex_hof_healing_veil_roots as v
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

class HealingVeilRootTests(unittest.TestCase):
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
 def test_01_three_minimum_types(self):
  before=copy.deepcopy((self.inherited,self.review));regions,proof=self.check()
  self.assertEqual([(r.start,r.end-r.start,r.kind)for r in regions],[(h,4,v.KIND)for h in v.HITS])
  self.assertEqual(proof['typed_bytes'],12);self.assertEqual((self.inherited,self.review),before)
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
 def test_31_full_source_prefix_lengths(self):
  rows=v.bind_program(self.raw)
  for seq,n in zip(v.SEQUENCES,(41,63,53,88)):
   got=[r for r in rows if r['address']in {a for a,_,_ in seq}]
   self.assertEqual(len(got),len(seq));self.assertEqual(sum(r['size']for r in got),n)
 def test_32_all_six_registered_moves(self):
  self.assertEqual(v.MOVE_EFFECTS,{0x28A:65,0x2A4:32,0x1E3:32,0x30A:32,0x323:32,0x344:32})
  self.assertEqual(v.WORDS[v.prior.EFFECTS+32*4],0x09003533)
  self.assertEqual(v.WORDS[v.prior.EFFECTS+65*4],0x09003BE5)
 def test_33_selector_taken_next_are_distinct(self):
  controls=v.control_proof(self.raw)
  for a,taken in [(0x09003BE6,0x09003C04),(0x0900354E,0x090035E2),(0x0900355A,0x09003681),(0x09003566,0x09003681)]:
   rows=[r for r in controls if r['command']==a]
   self.assertEqual([(r['edge'],r['next_cursor'])for r in rows],[('taken',taken),('next',a+12)])
   self.assertTrue(all(r['command_entry_condition']is True and r['natural_entry_proven']is False for r in rows))
 def test_34_goto_has_no_fallthrough(self):
  for a,to in [(0x09003BFF,0x081BA90A),(0x090036A1,0x090036AC)]:
   rows=[r for r in v.control_proof(self.raw)if r['command']==a]
   self.assertEqual([(r['edge'],r['next_cursor'])for r in rows],[('taken',to)])
 def test_35_actual_right_opcode_reads(self):
  rows=v.dispatch_proof(self.raw);actual={a for r in rows for a in r['opcode_byte_reads']}
  for h in v.HITS:self.assertTrue({h+2,h+3}<=actual)
  self.assertTrue(all(r['command_entry_condition']is True and r['handler_executed']is False and r['natural_entry_proven']is False for r in rows))
 def test_36_actual_e3_dispatch_slot(self):
  rows=[r for r in v.dispatch_proof(self.raw)if r['opcode']==0xE3]
  self.assertEqual([r['command']for r in rows],[0x09003607,0x090036C9])
  for r in rows:
   self.assertEqual(r['dispatch_slots'],[0x0903F7DC]);self.assertEqual(r['handler'],v.E3_ENTRY)
   self.assertEqual(r['cursor_at_handler'],r['command'])
 def test_37_counter_pointer_native_read(self):
  rows=v.pointer_read_proof(self.raw)
  self.assertEqual([(r['command'],r['pointer'],r['bank_operand'])for r in rows],
   [(0x09003C04,0x09008E11,1),(0x0900360D,0x090073D1,0),(0x090036CF,0x09003734,0)])
  self.assertTrue(all(r['pointer_bytes']==4 and r['distinct_bank_value_cases']==4 for r in rows))
  self.assertTrue(all(r['counter_branch_executed']is False and r['natural_entry_proven']is False for r in rows))
 def test_38_geometry_exactly_twelve_bytes(self):
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
  for hit in [0x09003299,0x090071FF,0x0900723E,0x09007271,0x09005D94,0x0900739D,0x09007432,0x0818DD5D]:
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
  self.assertEqual(inherited,before);self.assertEqual(len(regions),3)
 def test_47_every_source_instruction_boundary_resealed(self):
  for a,n,_ in v.PROGRAM:
   with self.subTest(address=a):self.resealed_reject(a)
 def test_48_review_must_retain_unknown_rows(self):
  self.reject(lambda r:r['hits'].reverse())
  self.reject(lambda r:r['hits'].pop())
 def test_49_new_source_shapes_are_fixed(self):
  self.assertEqual(v.GRAMMAR['jumpiffainted'],(0xE3,6,((1,1,'bank'),(2,4,'script_pointer'))))
  self.assertEqual(v.GRAMMAR['cureprimarystatus'],(0xFF02,7,((2,1,'bank'),(3,4,'script_pointer'))))
 def test_50_reachability_not_inferred(self):
  _,proof=self.check()
  for key in v.CLAIMS:self.assertIs(proof[key],False)
  self.assertEqual(proof['native_dispatch_models'],v.dispatch_proof(self.raw))
 def test_51_window_bool_size_rejected(self):
  review=copy.deepcopy(self.review)
  next(w for w in review['windows']if w['size']==1)['size']=True
  with self.assertRaises(ValueError):self.check(review=review)
 def test_52_hit_bool_size_rejected(self):
  self.reject(lambda r:r['hits'][0].update(size=True))
 def test_53_duplicate_window_rejected(self):
  self.reject(lambda r:r['windows'].append(copy.deepcopy(r['windows'][0])))
 def test_54_exact_full_pointer_geometry(self):
  for hit in v.HITS:
   e=v.evidence_template(hit);self.assertEqual(e['whole_pointers'][0]['address']+2,hit)
   self.assertEqual(e['left_command']['address']+e['left_command']['size'],hit+2)
   self.assertEqual(e['whole_pointers'][1]['address'],hit+8)
 def test_55_claims_bool_not_number(self):
  for key in v.CLAIMS:
   with self.subTest(key=key):self.reject(lambda r:r['claims'].update({key:0}))
 def test_56_minimum_window_end_byte_binding(self):
  for seq in v.SEQUENCES:
   a,name,_=seq[-1]
   with self.subTest(address=a):self.resealed_reject(a+v.GRAMMAR[name][1]-1)
 def test_57_e3_halfword_domain_and_all_cases(self):
  p=v.e3_proof(self.raw)
  self.assertEqual(p['hp_domain_count'],65536);self.assertEqual(p['machine_cases'],56)
  self.assertEqual({r['bank']for r in p['models']},{0,1,2,3})
  self.assertEqual({r['hp']for r in p['models']},{0,1,255,256,32767,32768,65535})
 def test_58_e3_full_pointer_only_taken(self):
  p=v.e3_proof(self.raw)
  for r in p['models']:
   self.assertEqual(r['full_pointer_read'],r['hp']==0)
   self.assertEqual(r['next_cursor'],0x081BA90A if r['hp']==0 else r['command']+6)
 def test_59_e3_target_bank_and_hp_location(self):
  p=v.e3_proof(self.raw)
  self.assertEqual((p['resolver_table_slot'],p['bank_read']),(0x09161410,0x02023CCC))
  self.assertEqual((p['hp_base'],p['hp_stride'],p['hp_offset'],p['hp_width']),(0x02023B44,88,40,2))
  for r in p['models']:self.assertEqual(r['hp_address'],0x02023B44+88*r['bank']+40)
 def test_60_e3_actual_redirect_registration(self):
  p=v.e3_proof(self.raw)
  self.assertEqual((p['primary_slot'],p['entry']),(0x0903F7DC,0x0802C514))
  self.assertEqual((p['legacy_resolver_entry'],p['redirect_literal'],p['actual_resolver_entry']),
   (0x08016634,0x08016638,0x090D3D2C))
  self.assertIs(p['public_us_address_alone_used_as_jp_evidence'],False)
 def test_61_e3_exact_external_writes(self):
  for r in v.e3_proof(self.raw)['models']:
   self.assertEqual(r['writes'],[dict(address=0x02023B24,size=1,value=r['bank']),
    dict(address=v.CURSOR,size=4,value=r['next_cursor'])])
 def test_62_e3_natural_claims_excluded(self):
  p=v.e3_proof(self.raw)
  for key in ['natural_reachability_claimed','prefix_execution_claimed','callasm_success_claimed','move_effect_success_claimed']:
   self.assertIs(p[key],False)
  self.assertEqual(len(p['entry_preconditions']),4)
 def test_63_e3_resealed_field_critical_bytes(self):
  for a in [0x0903F7DC,0x08016638,0x0802C530,0x0802C532,0x0802C52E,0x0802C522,
            0x0802C54A,0x0802C560,0x09003608,0x090036CA]:
   with self.subTest(address=a):self.resealed_reject(a)
 def test_64_sorted_closed_hit_projection(self):
  self.assertEqual(v.HITS,tuple(sorted(v.HITS)))
  self.assertEqual([h['address']for h in self.review['hits']],list(v.HITS))
 def test_65_address_keyed_evidence_matches_actual_commands(self):
  expected={0x0900360B:(32,0x09003533,0x09003607,0xE3,0x090073D1),
            0x090036CD:(32,0x09003533,0x090036C9,0xE3,0x09003734),
            0x09003C02:(65,0x09003BE5,0x09003BFF,40,0x09008E11)}
  commands={r['address']:r for r in v.bind_program(self.raw)}
  for hit,(effect,root,left,opcode,target)in expected.items():
   e=v.evidence_template(hit)
   self.assertEqual((e['effect'],e['root'],e['left_command']['address'],e['left_command']['opcode']),
                    (effect,root,left,opcode))
   self.assertEqual(e['whole_pointers'],[dict(address=hit-2,size=4,value=0x081BA90A),
                                       dict(address=hit+8,size=4,value=target)])
   for p in e['whole_pointers']:
    self.assertTrue(any(p=={k:f[k]for k in('address','size','value')}
     for c in (commands[left],commands[hit+2])for f in c['fields']if f['role']=='script_pointer'))
