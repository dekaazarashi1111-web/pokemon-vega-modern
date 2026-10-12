"""RFU新sourceだけの閉鎖型・意味変異・具体live契約反証。外部I/Oなし。"""
import copy
import hashlib
import unittest
from unittest.mock import patch
import pr16_dex_hof_new_code as v
FIXTURE = None
class Overlay:
 def __init__(self,raw,a,n,value):self.raw=raw;self.a=a-0x08000000;self.value=value.to_bytes(n,'little')
 def __len__(self):return len(self.raw)
 def __getitem__(self,key):
  if isinstance(key,int):return self[key:key+1][0]
  lo=key.start;hi=key.stop;b=bytearray(self.raw[key]);left=max(lo,self.a);right=min(hi,self.a+len(self.value))
  if left<right:b[left-lo:right-lo]=self.value[left-self.a:right-self.a]
  return bytes(b)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for item in obj.values():reseal(item,raw)
 elif isinstance(obj,list):
  for item in obj:reseal(item,raw)
class NewCodeTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit bounded in-memory FIXTURE required')
  self.raw,self.inherited,self.review,self.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,edit):
  r=copy.deepcopy(self.review);edit(r)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(review=r)
 def reject_evidence(self,edit):
  e=v.evidence_template();edit(e)
  with self.assertRaises((ValueError,TypeError,KeyError)):v.witness_geometry(e)
 def mutate(self,a,n,value):
  self.assertNotEqual(int.from_bytes(v.chunk(self.raw,a,n),'little'),value);raw=Overlay(self.raw,a,n,value);r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(raw=raw,review=r,inherited=i)
 def test_01_minimum_rooted_type(self):
  old=copy.deepcopy(self.inherited);rows,p=self.check();self.assertEqual(old,self.inherited)
  self.assertEqual([(r.start,r.end,r.kind)for r in rows],[(v.HIT-1,v.HIT+5,v.KIND)])
  self.assertTrue(p['composition']['constructor_returned']);self.assertTrue(p['composition']['actual_callback_load_and_interwork'])
 def test_02_exact_window(self):self.assertEqual(v.witness_geometry(v.evidence_template()),(0x080FC36A,6))
 def test_03_old_diagnostic_not_current(self):
  with patch.object(v,'identity',return_value=v.DIAGNOSTIC),patch.object(v,'_regions')as accept:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   accept.assert_not_called()
 def test_04_current_gate(self):
  with patch.object(v,'identity',return_value=v.CANDIDATE),patch.object(v,'_regions',return_value='sentinel')as accept:
   self.assertEqual(v.regions(*FIXTURE),'sentinel');accept.assert_called_once()
 def test_05_wrong_current_identity(self):
  i=copy.deepcopy(self.inherited);i['candidate']['sha256']='0'*64
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_06_owner_external(self):
  i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0]['owner_candidates']=['fake'];r['hit']['owner_candidates']=['fake']
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_07_unknown_only(self):
  for val in(True,0,1,None):
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0]['accepted']=val;r['hit']['accepted']=val
   with self.subTest(value=val),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_08_duplicate_hit(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(self.review['hit']))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_09_no_unrooted_boolean(self):
  for val in(False,1,None):self.reject_evidence(lambda e:e.update(root_verified=val))
 def test_10_no_fake_registration(self):self.reject_evidence(lambda e:e.update(same_registered_callback=False))
 def test_11_no_wider_geometry(self):self.reject_evidence(lambda e:e['instruction_window'].update(size=8))
 def test_12_no_literal_classification(self):self.reject_evidence(lambda e:e.update(literal_pool_included=True))
 def test_13_no_donor_promotion(self):self.reject_review(lambda r:r['claims'].update(donor_eligible=True))
 def test_14_no_natural_communication_claim(self):self.reject_review(lambda r:r['claims'].update(natural_wireless_lifecycle_proven=True))
 def test_15_no_runtime_claim(self):self.reject_review(lambda r:r['claims'].update(actual_runtime_execution_observed=True))
 def test_16_no_irq_lifetime_claim(self):self.reject_review(lambda r:r['claims'].update(universal_irq_lifetime_proven=True))
 def test_17_no_effect_promotion(self):self.reject_review(lambda r:r['claims'].update(opaque_callee_effects_proven=True))
 def test_18_no_indirect_complete_claim(self):self.reject_review(lambda r:r['claims'].update(indirect_reference_completeness_claimed=True))
 def test_19_no_missing_contract(self):self.reject_review(lambda r:r['input_contract'].pop('root'))
 def test_20_review_closed(self):self.reject_review(lambda r:r.update(trusted=True))
 def test_21_evidence_closed(self):self.reject_evidence(lambda e:e.update(trusted=True))
 def test_22_no_missing_window(self):self.reject_review(lambda r:r['windows'].pop())
 def test_23_no_duplicate_window(self):self.reject_review(lambda r:r['windows'].append(copy.deepcopy(r['windows'][0])))
 def test_24_no_reordered_windows(self):self.reject_review(lambda r:r['windows'].reverse())
 def test_25_exact_source_bytes(self):
  for key in v.SOURCE_IDS:
   s=dict(self.sources);s[key]+=b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_26_no_resealed_manifest(self):self.reject_review(lambda r:r['source_bindings']['pret-src-link_rfu_2.c'].update(sha256='0'*64))
 def test_27_all_semantic_halfwords_resealed(self):
  for i in v.INS.values():
   for off in range(0,i.size,2):
    a=i.address+off
    with self.subTest(address=a):self.mutate(a,2,int.from_bytes(v.chunk(self.raw,a,2),'little')^1)
  self.assertGreater(len(v.INS),180)
 def test_28_all_exact_literals_resealed(self):
  for a,old in v.LITERALS.items():
   with self.subTest(address=a):self.mutate(a,4,old^1)
 def test_29_exact_input_fields_and_bool_types(self):
  for key,old in v.inputs_template().items():
   changed=v.inputs_template();changed[key]=(1 if type(old)is bool else True if old==1 else old+1)
   with self.subTest(field=key),self.assertRaises(ValueError):v.compose_selected(self.raw,changed)
 def test_30_unknown_input_field(self):
  i=v.inputs_template();i['trust_callback']=True
  with self.assertRaises(ValueError):v.compose_selected(self.raw,i)
 def test_31_registration_null_rejected(self):
  with self.assertRaises(ValueError):v._compose(self.raw,v.inputs_template(),mutate_registered=lambda m:v.runtime.setmem(m.mem,v.LMAN+0x40,4,0))
 def test_32_registration_other_callback_rejected(self):
  with self.assertRaises(ValueError):v._compose(self.raw,v.inputs_template(),mutate_registered=lambda m:v.runtime.setmem(m.mem,v.LMAN+0x40,4,0x081357A7))
 def test_33_same_value_aba_requires_same_epoch(self):
  for kwargs in(dict(registry_reinitialized=True),dict(callback_replaced=True),dict(registry_reinitialized=0),dict(callback_replaced=0)):
   with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v.preservation_contract([],[],**kwargs)
 def test_34_every_live_field_write_rejected(self):
  p=v.compose_selected(self.raw)
  for call in p['conditional_calls']:
   for f in call['required_fields']:
    for off in (0,f['size']-1):
     with self.subTest(site=call['site'],address=f['address']+off),self.assertRaises(ValueError):v.preservation_contract(call['required_fields'],[(f['address']+off,1)])
 def test_35_nonlive_ram_all_erased(self):
  p=v.compose_selected(self.raw);self.assertTrue(p['nonlive_ram_erased_at_each_boundary']);self.assertTrue(p['projection_counterexamples']['all_other_ram_erased'])
  for c in p['conditional_calls']:self.assertTrue(v.preservation_contract(c['required_fields'],[(0x02010000,4)]))
 def test_36_conditional_eight_boundaries(self):
  p=v.compose_selected(self.raw);self.assertEqual(len(p['conditional_calls']),8)
  self.assertTrue(all(c['effects_discharged']is False and c['normal_abi_return_required']is True for c in p['conditional_calls']))
 def test_37_callback_field_is_live_after_registration(self):
  p=v.compose_selected(self.raw)
  for c in p['conditional_calls'][2:]:self.assertTrue(any(f['address']<=v.LMAN+0x40<v.LMAN+0x44<=f['address']+f['size']for f in c['required_fields']))
 def test_38_no_pre_registration_callback_requirement(self):
  p=v.compose_selected(self.raw)
  for c in p['conditional_calls'][:2]:self.assertFalse(any(f['address']<=v.LMAN+0x40<f['address']+f['size']for f in c['required_fields']))
 def test_39_real_parameter_values_and_branches(self):
  p=v.compose_selected(self.raw);self.assertTrue(p['actual_parameter_writes']);self.assertTrue(p['complete_bl_and_successor_executed'])
  e=p['events'][-1];self.assertEqual((e['target'],e['message'],e['parameter_count']),(0x080FC1E1,48,2))
 def test_40_unrelated_candidate_not_in_new_hits(self):self.assertEqual(v.HITS,(0x080FC36B,))
 def test_41_bool_schema_version_rejected(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_42_boolean_claims_reject_zero(self):self.reject_review(lambda r:r['claims'].update(donor_eligible=0))
 def test_43_field_geometry_bool_rejected(self):
  with self.assertRaises(ValueError):v.preservation_contract([dict(address=True,size=1,role='bad')],[])
 def test_44_write_geometry_bool_rejected(self):
  with self.assertRaises(ValueError):v.preservation_contract([],[(True,1)])
 def test_45_branch_choice_not_manual(self):
  m=v.Machine(self.raw)
  with self.assertRaises(ValueError):m.step(True)
 def effect(self,**kw):
  e=dict(writes=[],registry_reinitialized=False,callback_replaced=False,normal_abi_return=True);e.update(kw);return e
 def test_46_registration_aba_rejected_in_composition(self):
  for field in('registry_reinitialized','callback_replaced'):
   for value in(True,0,1):
    with self.subTest(field=field,value=value),self.assertRaises(ValueError):v.compose_selected(self.raw,boundary_effects={0x080FE424:self.effect(**{field:value})})
 def test_47_live_writes_rejected_in_composition(self):
  for call in v.compose_selected(self.raw)['conditional_calls']:
   for f in call['required_fields']:
    with self.subTest(site=call['site'],field=f),self.assertRaises(ValueError):v.compose_selected(self.raw,boundary_effects={call['site']:self.effect(writes=[(f['address'],1,0)])})
 def test_48_nonlive_writes_admitted_in_composition(self):
  for site in v.OPAQUE:
   p=v.compose_selected(self.raw,boundary_effects={site:self.effect(writes=[(0x02010000,4,123)])})
   self.assertTrue(p['complete_bl_and_successor_executed'])
 def test_49_nonreturning_boundary_rejected(self):
  for value in(False,1):
   with self.subTest(value=value),self.assertRaises(ValueError):v.compose_selected(self.raw,boundary_effects={0x080FE83C:self.effect(normal_abi_return=value)})
 def test_50_unknown_boundary_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,boundary_effects={0x080FC36A:self.effect()})
 def test_51_extra_boundary_claim_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,boundary_effects={0x080FE83C:self.effect(assume_safe=True)})
if __name__=='__main__':unittest.main()
