"""新engine guardのみ。型の偽昇格・非zero注入・live契約・意味変異の反証。"""
import copy
import hashlib
import unittest
from unittest.mock import patch
import pr16_dex_hof_engine_roots as v
FIXTURE=None
class Overlay:
 def __init__(self,raw,address,size,value):self.raw=raw;self.start=address-0x08000000;self.value=value.to_bytes(size,'little')
 def __len__(self):return len(self.raw)
 def __getitem__(self,s):
  if isinstance(s,int):return self[s:s+1][0]
  b=bytearray(self.raw[s]);lo=max(s.start,self.start);hi=min(s.stop,self.start+len(self.value))
  if lo<hi:b[lo-s.start:hi-s.start]=self.value[lo-self.start:hi-self.start]
  return bytes(b)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for x in obj.values():reseal(x,raw)
 elif isinstance(obj,list):
  for x in obj:reseal(x,raw)
class EngineRootGuards(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit bounded in-memory FIXTURE required')
  self.raw,self.inherited,self.review,self.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,fn):
  r=copy.deepcopy(self.review);fn(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def reject_proof(self,fn):
  p=v.held_proof_template();fn(p)
  with self.assertRaises((ValueError,KeyError,TypeError)):v.validate_held_proof(p)
 def test_01_zero_classification_preserves_all_input_fields(self):
  before=copy.deepcopy(self.inherited);rows,p=self.check()
  self.assertEqual(rows,[]);self.assertEqual(self.inherited,before);self.assertEqual(p['count'],0)
  self.assertEqual(p['held_hits'],list(v.HITS));self.assertEqual(v.CLASSIFIED_HITS,())
 def test_02_no_typed_witness_any_payload(self):
  for x in({},None,v.held_proof_template(),self.review):
   with self.subTest(payload=type(x).__name__),self.assertRaises(ValueError):v.witness_geometry(x)
 def test_03_diagnostic_never_current_gate(self):
  with patch.object(v,'identity',return_value=v.DIAGNOSTIC),patch.object(v,'_regions')as accept:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   accept.assert_not_called()
 def test_04_current_gate_updates_only_gate_flag(self):
  expected=v.held_proof_template(True)
  original_identity=v.identity
  with patch.object(v,'identity',side_effect=lambda raw:v.CANDIDATE if raw is self.raw else original_identity(raw)):
   rows,p=v.regions(*FIXTURE);self.assertEqual(rows,[]);self.assertEqual(p,expected)
 def test_05_wrong_current_parent_rejected(self):
  i=copy.deepcopy(self.inherited);i['candidate']=copy.deepcopy(v.DIAGNOSTIC)
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_06_empty_or_single_hit_rejected(self):
  for hits in([],self.inherited['hits'][:1]):
   i=copy.deepcopy(self.inherited);i['hits']=hits
   with self.subTest(hits=len(hits)),self.assertRaises(ValueError):self.check(inherited=i)
 def test_07_duplicate_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(i['hits'][0]))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_08_reordered_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].reverse()
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_09_hit_must_remain_unknown(self):
  for field,value in(('accepted',True),('accepted',0),('accepted',1),('classification','ACCEPTED'),('owner_candidates',['synthetic']),('size',True),('size',8),('kind','POINTER')):
   i=copy.deepcopy(self.inherited);i['hits'][0][field]=value;r=v.make_review(None,i['hits'])
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_10_all_claim_promotion_rejected(self):
  for key,value in v.CLAIMS.items():
   if type(value)is bool:self.reject_review(lambda r,key=key:r['claims'].update({key:not value}))
 def test_11_bool_integer_claim_substitution_rejected(self):
  for key,value in v.CLAIMS.items():
   if type(value)is bool:self.reject_review(lambda r,key=key,value=value:r['claims'].update({key:int(value)}))
 def test_12_no_missing_or_extra_review_key(self):
  self.reject_review(lambda r:r.pop('input_contract'));self.reject_review(lambda r:r.update(trusted=True))
 def test_13_schema_bool_rejected(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_14_no_wider_geometry(self):self.reject_review(lambda r:r['windows'][0].update(size=r['windows'][0]['size']+2))
 def test_15_no_missing_duplicate_reordered_window(self):
  self.reject_review(lambda r:r['windows'].pop());self.reject_review(lambda r:r['windows'].append(r['windows'][0]));self.reject_review(lambda r:r['windows'].reverse())
 def test_16_source_set_exact(self):
  for key in v.SOURCE_IDS:
   s=dict(self.sources);s.pop(key)
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_17_source_bytes_and_blob_exact(self):
  for key in v.SOURCE_IDS:
   s=dict(self.sources);s[key]+=b'\n'
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_18_no_source_reseal(self):self.reject_review(lambda r:r['source_bindings']['pret-task.c'].update(sha256='0'*64))
 def test_19_all_instruction_halfwords_independent_encoder(self):
  for i in v.INS.values():
   for offset in range(0,i.size,2):
    a=i.address+offset;old=int.from_bytes(v.chunk(self.raw,a,2),'little');raw=Overlay(self.raw,a,2,old^1)
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)
  self.assertEqual(len(v.INS),371)
 def test_20_all_literal_words_independent_meaning(self):
  for a,old in v.LITERALS.items():
   with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Overlay(self.raw,a,4,old^1))
 def test_21_every_protected_byte_reseal_fails(self):
  for w in v.FIXED_WINDOWS:
   for offset in range(w['size']):
    a=w['address']+offset;old=v.chunk(self.raw,a,1)[0];raw=Overlay(self.raw,a,1,old^1)
    review=copy.deepcopy(self.review);inherited=copy.deepcopy(self.inherited);reseal(review,raw);reseal(inherited,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=review,inherited=inherited)
 def test_22_gpu_state7_not_injected(self):
  p=v.compose_selected(self.raw,'gpu');self.assertEqual(p['states'],list(range(8)));self.assertFalse(p['entry_independently_rooted']);self.assertFalse(p['classified'])
 def test_23_gpu_both_literal_roles_consumed_without_type(self):
  p=v.compose_selected(self.raw,'gpu');self.assertEqual([x['size']for x in p['hit_partition']],[1,3]);self.assertEqual(p['scalar_bytes_consumed'],4);self.assertEqual(p['callback_bytes_consumed'],4)
  self.assertTrue(p['scalar_shadow_written']and p['scalar_hardware_written']and p['callback_registered']);self.assertFalse(p['callback_dispatched'])
 def test_24_wireless_real_zero_and_dispatch_both_activities(self):
  for activity in(6,7):
   p=v.compose_selected(self.raw,'wireless',activity);self.assertTrue(p['actual_memset_zero_producer']);self.assertEqual(p['registered_task_dispatches'],3);self.assertEqual(p['states'],[0,1,2,3]);self.assertEqual(p['show_list_value'],0);self.assertFalse(p['hit_call_executed'])
 def test_25_no_unsupported_activity_or_bool(self):
  for a in(0,True,8,None):
   with self.subTest(activity=a),self.assertRaises(ValueError):v.compose_selected(self.raw,'wireless',a)
 def test_26_no_unknown_profile(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'sound_check_rooted')
 def test_27_no_manual_branch_selection(self):
  m=v.Machine(self.raw,0x08118BCC)
  with self.assertRaises(ValueError):m.step(True)
 def test_28_no_injected_nonzero_flag(self):
  with self.assertRaises(ValueError):v._compose(self.raw,'wireless',mutate_registered=lambda m:v.runtime.setmem(m.mem,v.DATA+19,1,1))
 def test_29_no_replaced_registered_callback(self):
  for target in(0,0x0809FF01):
   with self.subTest(target=target),self.assertRaises(ValueError):v._compose(self.raw,'wireless',mutate_registered=lambda m,target=target:v.runtime.setmem(m.mem,v.TASK,4,target))
 def test_30_all_live_field_edges_reject_in_contract(self):
  for p in v.CASE_PROOFS:
   for c in p['conditional_calls']:
    for f in c['required_fields']:
     for a in(f['address'],f['address']+f['size']-1):
      with self.subTest(site=c['site'],address=a),self.assertRaises(ValueError):v.preservation_contract(c['required_fields'],[(a,1)])
 def test_31_all_live_fields_reject_in_actual_composition(self):
  for p in v.CASE_PROOFS[:2]:
   for c in p['conditional_calls']:
    for f in c['required_fields']:
     effect=v.effect_template();effect['writes']=[(f['address'],1,0)]
     with self.subTest(kind=p['kind'],site=c['site'],field=f['address']),self.assertRaises(ValueError):v.compose_selected(self.raw,p['kind'],boundary_effects={c['site']:effect})
 def test_32_nonlive_ram_erasure_and_write_admitted(self):
  for p in v.CASE_PROOFS[:2]:
   for c in p['conditional_calls']:
    effect=v.effect_template();effect['writes']=[(0x02010000,4,42)]
    result=v.compose_selected(self.raw,p['kind'],boundary_effects={c['site']:effect});self.assertTrue(result['nonlive_ram_erased_at_each_boundary'])
 def test_33_epoch_reinit_aba_rejected(self):
  for key in('registry_reinitialized','callback_replaced'):
   for value in(True,0,1):
    effect=v.effect_template();effect[key]=value
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):v.compose_selected(self.raw,'wireless',boundary_effects={0x08118C82:effect})
 def test_34_normal_return_required(self):
  for value in(False,1):
   effect=v.effect_template();effect['normal_abi_return']=value
   with self.subTest(value=value),self.assertRaises(ValueError):v.compose_selected(self.raw,'gpu',boundary_effects={0x0809FF4E:effect})
 def test_35_unknown_effect_site_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'wireless',boundary_effects={0x08118D02:v.effect_template()})
 def test_36_unexecuted_effect_site_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'wireless',boundary_effects={0x0809FF4E:v.effect_template()})
 def test_37_unknown_effect_field_rejected(self):
  effect=v.effect_template();effect['assume_no_writes']=True
  with self.assertRaises(ValueError):v.compose_selected(self.raw,'wireless',boundary_effects={0x08118C82:effect})
 def test_38_bad_write_geometry(self):
  for write in((True,1,0),(0x02010000,True,0),(0x02010000,1,True),(0x02010000,8,0),(0x02010000,1,256)):
   effect=v.effect_template();effect['writes']=[write]
   with self.subTest(write=write),self.assertRaises(ValueError):v.compose_selected(self.raw,'wireless',boundary_effects={0x08118C82:effect})
 def test_39_fixed_proof_must_be_closed(self):
  self.reject_proof(lambda p:p.clear());self.reject_proof(lambda p:p.update(trusted=True));self.reject_proof(lambda p:p.pop('roots'))
 def test_40_no_classification_or_donor_promotion(self):
  self.reject_proof(lambda p:p.update(count=1));self.reject_proof(lambda p:p.update(hits=list(v.HITS)));self.reject_proof(lambda p:p.update(donor_eligible=True));self.reject_proof(lambda p:p.update(new_classified_bytes=4))
 def test_41_no_root_promotion(self):self.reject_proof(lambda p:p['observations'][0].update(entry_independently_rooted=True))
 def test_42_no_zero_path_promotion_to_universal_unreachability(self):self.reject_proof(lambda p:p.update(universal_unreachability_claimed=True))
 def test_43_no_hit_call_promotion(self):self.reject_proof(lambda p:p['observations'][1].update(hit_call_executed=True))
 def test_44_no_missing_or_changed_live_contract(self):
  self.reject_proof(lambda p:p['observations'][1]['conditional_calls'][0]['required_fields'].pop());self.reject_proof(lambda p:p['observations'][0]['conditional_calls'][0].update(effects_discharged=True))
 def test_45_no_current_flag_fabrication(self):
  self.reject_proof(lambda p:p.update(current_candidate_measured=True))
  with self.assertRaises(ValueError):v.held_proof_template(1)
 def test_46_inherited_unrelated_field_kept(self):
  inherited=copy.deepcopy(self.inherited);inherited['other_scope']={'preserve':[1,2,3]};before=copy.deepcopy(inherited);self.check(inherited=inherited);self.assertEqual(inherited,before)
 def test_47_guard_geometry_count_fixed(self):self.assertEqual(len(v.FIXED_WINDOWS),73);self.assertEqual(sum(w['size']for w in v.FIXED_WINDOWS),978)
 def test_48_no_opaque_zero_producer_shortcut(self):
  p=v.compose_selected(self.raw,'wireless');self.assertNotIn(0x08076BE2,[c['site']for c in p['conditional_calls']]);self.assertTrue(p['actual_memset_zero_producer'])
if __name__=='__main__':unittest.main()
