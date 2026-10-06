"""登録event根と選択producer/EOS byte消費の新scope専用負例。ROM I/Oなし。"""
import copy,hashlib,unittest
from unittest.mock import patch
import pr16_dex_hof_event_text_roots as v
FIXTURE=None

class Overlay:
 def __init__(self,raw,address,size,value):self.raw=raw;self.a=address-0x08000000;self.value=value.to_bytes(size,'little')
 def __len__(self):return len(self.raw)
 def __getitem__(self,key):
  if isinstance(key,int):return self[key:key+1][0]
  lo,hi=key.start,key.stop;b=bytearray(self.raw[key]);left=max(lo,self.a);right=min(hi,self.a+len(self.value))
  if left<right:b[left-lo:right-lo]=self.value[left-self.a:right-self.a]
  return bytes(b)

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)

class EventTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit bounded in-memory FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
  cls.regions,cls.proof=v._regions(*FIXTURE)
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,edit):
  review=copy.deepcopy(self.review);edit(review)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(review=review)
 def reject_witness(self,edit):
  evidence=v.evidence_template(v.HITS[0]);edit(evidence)
  with self.assertRaises((ValueError,TypeError,KeyError)):v.witness_geometry(evidence)
 def test_one_exact4byte_data(self):self.assertEqual([(r.start,r.end-r.start,r.kind)for r in self.regions],[(v.HITS[0],4,v.KIND)])
 def test_both_eos_consumed(self):self.assertEqual([p['byte_reads']for p in self.proof['composition']['invocations']],[25,78])
 def test_result8_and0(self):self.assertEqual(self.proof['composition']['source_prefix_conditions'],[8,0])
 def test_real_prefix_paths(self):self.assertEqual([p['instructions']for p in self.proof['root_paths']],[29,13])
 def test_structural_prefix_limit(self):self.assertTrue(self.proof['structural_prefix_only']);self.assertFalse(self.proof['prefix_handler_runtime_effects_proven'])
 def test_renderer_and_natural_limit(self):self.assertFalse(self.proof['full_renderer_claimed']);self.assertFalse(self.proof['full_story_reachability_claimed'])
 def test_no_donor(self):self.assertFalse(self.proof['donor_leased']);self.assertFalse(self.proof['donor_eligible'])
 def test_minimum_evidence(self):self.assertEqual(len(v.FIXED_WINDOWS),34);self.assertEqual(sum(w['size']for w in v.FIXED_WINDOWS),756)
 def test_semantic_encoder(self):
  for i in v.INS.values():self.assertEqual(v.chunk(self.raw,i.address,i.size),v.encoded(i))
 def test_each_instruction_halfword_rejected(self):
  for ins in v.INS.values():
   for j in range(0,ins.size,2):
    a=ins.address+j;value=int.from_bytes(v.chunk(self.raw,a,2),'little')^1
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Overlay(self.raw,a,2,value))
 def test_each_required_byte_rejected(self):
  for window in v.FIXED_WINDOWS:
   for j in range(window['size']):
    a=window['address']+j;value=v.chunk(self.raw,a,1)[0]^1
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=Overlay(self.raw,a,1,value))
 def test_each_literal_rejected(self):
  for a,value in v.LITERALS.items():
   with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Overlay(self.raw,a,4,value^4))
 def test_all103_text_bytes_reseal_rejected(self):
  for text in v.TEXTS:
   for j in range(text['size']):
    a=text['address']+j;raw=Overlay(self.raw,a,1,v.chunk(self.raw,a,1)[0]^1);review=copy.deepcopy(self.review);reseal(review,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=review)
 def test_root_pointer_reseal_rejected(self):
  for row in v.TEXTS[0]['root_chain']:
   raw=Overlay(self.raw,row['address'],1,v.chunk(self.raw,row['address'],1)[0]^1);review=copy.deepcopy(self.review);reseal(review,raw)
   with self.subTest(role=row['role']),self.assertRaises(ValueError):self.check(raw=raw,review=review)
 def test_schema_boolean_rejected(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_extra_review_rejected(self):self.reject_review(lambda r:r.update(unchecked=True))
 def test_missing_review_rejected(self):self.reject_review(lambda r:r.pop('texts'))
 def test_review_claim_lift_rejected(self):self.reject_review(lambda r:r['claims'].update(full_story_reachability_claimed=True))
 def test_prefix_claim_lift_rejected(self):self.reject_review(lambda r:r['claims'].update(prefix_handler_runtime_effects_proven=True))
 def test_review_contract_lift_rejected(self):self.reject_review(lambda r:r['input_contract'].update(special='unconditional'))
 def test_root_owner_substitution_rejected(self):self.reject_review(lambda r:r['texts'][0].update(owner_id='OBJECT:98/18:0'))
 def test_root_script_substitution_rejected(self):self.reject_review(lambda r:r['texts'][0].update(target_script_root=0x09430A5C))
 def test_path_entry_substitution_rejected(self):self.reject_review(lambda r:r['texts'][0]['path'][0].update(address=0x081802BC))
 def test_path_drop_rejected(self):self.reject_review(lambda r:r['texts'][0]['path'].pop(1))
 def test_path_branch_substitution_rejected(self):self.reject_review(lambda r:r['texts'][0]['path'][11].update(address=0x0818024C))
 def test_wrong_standard_rejected(self):self.reject_review(lambda r:r['texts'][0]['loadword_and_callstd'].update(pointer=v.TEXTS[1]['address']))
 def test_text_extent_rejected(self):self.reject_review(lambda r:r['texts'][0].update(size=28))
 def test_result_substitution_rejected(self):self.reject_review(lambda r:r['texts'][0].update(special_result=0))
 def test_window_drop_rejected(self):self.reject_review(lambda r:r['windows'].pop())
 def test_window_expansion_rejected(self):self.reject_review(lambda r:r['windows'][0].update(size=4096))
 def test_accepted_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'][0]['accepted']=True;r=copy.deepcopy(self.review);r['hits']=copy.deepcopy(i['hits'])
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_owned_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'][0]['owner_candidates']=['x'];r=copy.deepcopy(self.review);r['hits']=copy.deepcopy(i['hits'])
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_duplicate_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits']*=2
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_missing_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits']=[]
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_wrong_hit_size_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'][0]['size']=8;r=copy.deepcopy(self.review);r['hits']=copy.deepcopy(i['hits'])
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_wrong_hit_kind_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'][0]['kind']='pointer';r=copy.deepcopy(self.review);r['hits']=copy.deepcopy(i['hits'])
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_current_identity_mismatch_rejected(self):self.reject_review(lambda r:r.update(required_candidate=v.DIAGNOSTIC))
 def test_diagnostic_identity_mismatch_rejected(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_whole_current_api_gate(self):
  with patch.object(v,'identity',return_value=v.DIAGNOSTIC):
   with self.assertRaises(ValueError):v.regions(self.raw,self.inherited,self.review,self.sources)
 def test_whole_current_api_enters_proof(self):
  with patch.object(v,'identity',return_value=v.CANDIDATE),patch.object(v,'_regions',return_value='entry')as target:
   self.assertEqual(v.regions(self.raw,self.inherited,self.review,self.sources),'entry');target.assert_called_once()
 def test_source_mutation_rejected(self):
  for key in self.sources:
   s=dict(self.sources);s[key]=s[key]+b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_source_missing_rejected(self):
  s=dict(self.sources);s.pop('pret-scrcmd.c')
  with self.assertRaises(ValueError):self.check(sources=s)
 def test_source_extra_rejected(self):
  s=dict(self.sources);s['extra']=b''
  with self.assertRaises(ValueError):self.check(sources=s)
 def test_source_review_reseal_rejected(self):self.reject_review(lambda r:r['source_bindings']['pret-scrcmd.c'].update(sha256='0'*64))
 def test_witness_exact(self):self.assertEqual(v.witness_geometry(v.evidence_template(v.HITS[0])),(v.HITS[0],4))
 def test_witness_extra_rejected(self):self.reject_witness(lambda r:r.update(extra=True))
 def test_witness_claim_rejected(self):self.reject_witness(lambda r:r.update(actual_runtime_execution_observed=True))
 def test_witness_extent_rejected(self):self.reject_witness(lambda r:r['classified_window'].update(size=103))
 def test_witness_address_rejected(self):self.reject_witness(lambda r:r['classified_window'].update(address=v.HITS[0]+1))
 def test_witness_type_rejected(self):self.reject_witness(lambda r:r['classified_window'].update(address=str(v.HITS[0])))
 def test_witness_text_rejected(self):self.reject_witness(lambda r:r['texts'][0].update(address=0x0943C03C))
 def test_witness_root_rejected(self):self.reject_witness(lambda r:r['root'].update(group=98))
 def test_nonhit_witness_rejected(self):
  with self.assertRaises(ValueError):v.evidence_template(0x0816791B)
 def test_message_busy_rejected(self):
  with self.assertRaises(ValueError):v.consume_selected(self.raw,v.TEXTS[0],message_state=2)
 def test_boolean_message_state_rejected(self):
  with self.assertRaises(ValueError):v.consume_selected(self.raw,v.TEXTS[0],message_state=False)
 def test_result_override_rejected(self):
  with self.assertRaises(ValueError):v.consume_selected(self.raw,v.TEXTS[0],result=0)
 def test_false_completion_rejected(self):
  with self.assertRaises(ValueError):v.consume_selected(self.raw,v.TEXTS[0],completes=False)
 def test_context_seed_rejected(self):
  with self.assertRaises(ValueError):v.consume_selected(self.raw,v.TEXTS[0],context_override={v.CTX+100:v.TEXTS[0]['address']})
 def test_init_root_gate(self):
  text=copy.deepcopy(v.TEXTS[0]);text['target_script_root']+=1
  with self.assertRaises(ValueError):v.conditional_prefix(self.raw,text)
 def test_mutated_eos_target_rejected(self):
  raw=Overlay(self.raw,0x08008B7C,4,0x08008C22)
  with self.assertRaises(ValueError):v.consume_selected(raw,v.TEXTS[0])
 def test_wrong_data0_slot_rejected(self):
  raw=Overlay(self.raw,v.TEXTS[0]['loadword_and_callstd']['address']+1,1,1)
  with self.assertRaises(ValueError):v.consume_selected(raw,v.TEXTS[0])
 def test_wrong_standard_slot_rejected(self):
  raw=Overlay(self.raw,0x08163768,4,0x08192DA6)
  with self.assertRaises(ValueError):v.consume_selected(raw,v.TEXTS[0])
 def test_lost_null_fallback_rejected(self):
  raw=Overlay(self.raw,0x08192DA6,1,1)
  with self.assertRaises(ValueError):v.consume_selected(raw,v.TEXTS[0])
 def test_all_proof_claims_closed(self):
  for key,value in v.CLAIMS.items():self.assertEqual(self.proof[key],value)

 def test_structural_prefix_has_no_context_writer(self):
  with patch.object(v.rt,'setmem',side_effect=AssertionError('prefix must not produce runtime context')):
   p=v.conditional_prefix(self.raw,v.TEXTS[0])
  self.assertEqual(p['context_writes'],0);self.assertFalse(p['runtime_reachability_proven'])
 def test_suffix_context_limit(self):
  self.assertTrue(self.proof['valid_suffix_context_is_entry_condition']);self.assertFalse(self.proof['registered_root_runtime_execution_proven'])
 def test_root_scope_lift_rejected(self):self.reject_witness(lambda r:r.update(root_verification_scope='runtime_arrival'))
