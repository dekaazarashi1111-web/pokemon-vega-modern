"""Tutor専用有限phase/意味mutation試験。旧suite・nativeを再実行しない。"""
import copy
import unittest
import pr16_dex_hof_party_tutor as v
FIXTURE=None

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=v.identity(v.chunk(raw,obj['address'],obj['size']))['sha256']
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)

class PartyTutorTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit in-memory FIXTURE required')
  self.raw,self.inherited,self.review,self.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,
   self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,edit):
  r=copy.deepcopy(self.review);edit(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def reject_geometry(self,edit):
  e=v.evidence_template();edit(e)
  with self.assertRaises((ValueError,KeyError,TypeError)):v.witness_geometry(e)
 def test_01_exact_one_six_byte_type(self):
  before=copy.deepcopy(self.inherited);rows,p=self.check()
  self.assertEqual([(x.start,x.end,x.kind) for x in rows],[(v.HIT-1,v.HIT+5,v.KIND)])
  self.assertEqual(v.witness_geometry(rows[0].evidence),(v.HIT-1,6));self.assertEqual(self.inherited,before);self.assertEqual(p['count'],1)
 def test_02_all_normal_tutor_cases_reach_real_hit(self):
  _,p=self.check();self.assertEqual([x['tutor_id'] for x in p['cases']],list(range(15)))
  for c in p['cases']:
   self.assertEqual(c['reached_call'],v.HIT-1);self.assertEqual(c['task_id'],0);self.assertFalse(c['actual_stringcopy_at_hit_executed'])
   self.assertEqual([x['callback'] for x in c['phases'][1:]],v.ROOT['registered_callbacks'])
   self.assertEqual([x['next_callback'] for x in c['phases'][1:5]],v.ROOT['registered_callbacks'][1:])
 def test_03_actual_special_constructor_and_task_chain(self):
  c=v.finite_case(self.raw);self.assertEqual(c['phases'][0],dict(role='actual_state20_task_admission',task_id=0,field0=0x08120319))
  self.assertTrue({'script_read_actual_special397','A_confirm_current_slot0','replaceNo','stopYes','four_move_slots_full'}<={x['role'] for x in c['conditional_calls']})
  self.assertTrue(c['main_and_task_registration_consumers_executed'])
 def test_04_unclosed_other_helper_callees_are_explicit(self):
  calls=v.finite_case(self.raw)['conditional_calls']
  for target in (0x0809A3E8,0x0812640C,0x09FFF6D0,0x0803F354,0x0803E008):
   selected=[x for x in calls if x['callee']==target];self.assertTrue(selected)
   self.assertTrue(all(x['actual_effect_discharged'] is False and x['normal_return_assumed'] is True and x['protected_fields'] for x in selected))
  self.assertFalse(v.CLAIMS['ordinary_adapter_proof_promoted_to_entire_helper'])
 def test_05_text_and_input_return_contracts(self):
  calls=v.finite_case(self.raw)['conditional_calls']
  self.assertEqual([x['return_condition'] for x in calls if x['callee']==0x08110BF8],[1,0])
  self.assertEqual([x['return_condition'] for x in calls if x['callee']==0x08120B60],[0,0])
  self.assertTrue(all(x['return_condition']==0 for x in calls if x['callee'] in (0x080C0918,0x080C08D8)))
 def test_06_normal_tutor_boundary_rejects_alternate_ids(self):
  for t in (-1,15,63,64,True,1.0):
   with self.subTest(tutor=t),self.assertRaises(ValueError):v.finite_case(self.raw,tutor_id=t)
 def test_07_yes_no_order_is_required(self):
  for q in ((0,0),(1,1),(-1,0),(-2,0),(True,False),()):
   with self.subTest(inputs=q),self.assertRaises(ValueError):v.finite_case(self.raw,inputs=q)
 def test_08_fade_link_text_compat_known_full_conditions(self):
  for key,value in [('fade',128),('link',1),('text',1),('compatible',0),('known',1),('full',1),('full',False),('fields_preserved',False)]:
   with self.subTest(field=key),self.assertRaises(ValueError):v.finite_case(self.raw,**{key:value})
 def test_09_old_diagnostic_cannot_be_accepted_current(self):
  if v.identity(self.raw)==v.CANDIDATE:self.assertEqual(v.regions(*FIXTURE)[1]['count'],1)
  else:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
 def test_10_wrong_parent_candidate_rejected(self):
  i=copy.deepcopy(self.inherited);i['candidate']['sha256']='0'*64
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_11_unknown_external_hit_is_mandatory(self):
  for key,value in [('accepted',True),('owner_candidates',['owner']),('size',True),('kind','POINTER')]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review)
   next(x for x in i['hits'] if x['address']==v.HIT)[key]=value;r['hit'][key]=value
   with self.subTest(field=key),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_12_duplicate_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(self.review['hit']))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_13_missing_dependency_rejected(self):self.reject_review(lambda r:r['windows'].pop())
 def test_14_wider_boundary_rejected(self):self.reject_geometry(lambda e:e['instruction_window'].update(size=8))
 def test_15_odd_fragment_only_rejected(self):self.reject_geometry(lambda e:e['instruction_window'].update(address=v.HIT,size=4))
 def test_16_half_BL_rejected(self):self.reject_geometry(lambda e:e['instructions'][0].update(size=2))
 def test_17_successor_without_root_rejected(self):self.reject_geometry(lambda e:e.pop('root'))
 def test_18_dynamic_BL_return_claim_rejected(self):self.reject_geometry(lambda e:e['claims'].update(bl_return_observed=True))
 def test_19_whole_function_claim_rejected(self):self.reject_geometry(lambda e:e['claims'].update(whole_function_range_classified=True))
 def test_20_adapter_promotion_rejected(self):self.reject_review(lambda r:r['claims'].update(ordinary_adapter_proof_promoted_to_entire_helper=True))
 def test_21_drop_external_condition_rejected(self):self.reject_review(lambda r:r['input_contract'].pop('callee_frame'))
 def test_22_unknown_schema_key_rejected(self):self.reject_review(lambda r:r.update(rawhex='forbidden'))
 def test_23_bool_schema_version_rejected(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_24_diagnostic_current_metadata_conflation_rejected(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_25_source_and_review_identity_mutations(self):
  for name in v.SOURCE_IDS:
   src=dict(self.sources);data=bytearray(src[name]);data[len(data)//2]^=1;src[name]=bytes(data)
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources=src)
 def test_26_semantic_mutations_resealed_every_instruction_halfword(self):
  raw=bytearray(self.raw)
  for a in sorted({a for i in v.INS.values() for a in range(i.address,i.address+i.size,2)}):
   off=a-0x08000000;raw[off]^=1;r,i=copy.deepcopy(self.review),copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
   try:
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
   finally:raw[off]^=1
 def test_27_literal_semantic_mutations_resealed(self):
  raw=bytearray(self.raw)
  for a in v.LITERALS:
   off=a-0x08000000;raw[off]^=1;r,i=copy.deepcopy(self.review),copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
   try:
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
   finally:raw[off]^=1
 def test_28_bad_window_record_rejected(self):
  for edit in (lambda r:r['windows'][0].update(address=True),lambda r:r['windows'][0].update(sha256='Z'*64),lambda r:r['windows'][0].update(size=1),lambda r:r['windows'][0].update(extra=1)):self.reject_review(edit)
 def test_29_task_control_projection_rejects_overwrite(self):
  p=v.runtime.ROOT+v.runtime.HEADER
  for phase in ('choose','replace_text','replace_input','stop_text','stop_input'):
   for a,n in ((v.TASKS,4),(v.TASKS+4,1),(v.TASKS+5,2),(v.PARTY+9,1),(v.PARTY+14,2),(0x02036FF6,2),(0x03003134,4)):
    with self.subTest(phase=phase,address=a),self.assertRaises(ValueError):v.projection_preserved(p,phase,[(a,n)])
 def test_30_dead_unrelated_task_data_remains_mutable(self):
  p=v.runtime.ROOT+v.runtime.HEADER;self.assertTrue(v.projection_preserved(p,'stop_input',[(v.TASKS+8,32),(0x02028000,4)]))
 def test_31_setup_epoch_free_reset_rejected(self):
  p=v.runtime.ROOT+v.runtime.HEADER
  for extra in (dict(freed=(p,)),dict(heap_reinitialized=True)):
   with self.assertRaises(ValueError):v.projection_preserved(p,'setup',[],**extra)
 def test_32_post_setup_type_does_not_require_unused_allocation(self):
  p=v.runtime.ROOT+v.runtime.HEADER;self.assertTrue(v.projection_preserved(p,'stop_input',[],freed=(p,),heap_reinitialized=True));self.assertIn('resources',v.CONTRACT['callee_frame'])
 def test_33_minimal_window_has_only_complete_instruction_partition(self):
  e=v.evidence_template();self.assertEqual(sum(i['size'] for i in e['instructions']),6);self.assertFalse(e['literal_pool_included'])
  self.assertEqual(e['instructions'][0]['target'],0x08008900);self.assertEqual(e['instructions'][1]['literal'],0x08126B44)
 def test_34_no_current_or_donor_or_irq_claim(self):
  for key in ('runtime_execution_observed','all_heap_lifetimes_proven','irq_noninterference_proven','all_opaque_callee_effects_proven','donor_eligible','indirect_reference_complete'):self.assertIs(v.CLAIMS[key],False)
 def test_35_source_ids_include_all_fixed_review_bindings(self):
  self.assertTrue(set(v.PRIOR_REFS)<=set(v.SOURCE_IDS))
  for name in v.PRIOR_REFS:self.assertEqual(self.review['inherited_reviews'][name]['sha256'],v.SOURCE_IDS[name]['sha256'])
 def test_36_review_has_no_private_payload(self):
  import json
  text=json.dumps(self.review)
  for forbidden in ('private-inputs','rawhex','rom_bytes','candidate.gba'):self.assertNotIn(forbidden,text)

 def test_37_state20_admission_lives_through_remaining_setup(self):
  c=v.finite_case(self.raw);seen=False
  for row in c['conditional_calls']:
   if row['phase']=='setup' and row['task_membership_required']:
    seen=True;self.assertTrue(any(x['address']==v.TASKS and x['size']==8 for x in row['protected_fields']))
  self.assertTrue(seen)
  with self.assertRaises(ValueError):v.projection_preserved(v.runtime.ROOT+v.runtime.HEADER,'setup',[(v.TASKS,4)],task_live=True)
 def test_38_fade_guard_live_between_calls(self):
  with self.assertRaises(ValueError):v.projection_preserved(v.runtime.ROOT+v.runtime.HEADER,'choose',[(0x020379F3,1)])

 def test_39_callback1_projection_rejects_all_phase_callee_writes(self):
  p=v.runtime.ROOT+v.runtime.HEADER
  for phase in ('constructor','setup','choose','replace_text','replace_input','stop_text','stop_input'):
   for a,n in ((0x03003130,4),(0x03003131,1)):
    with self.subTest(phase=phase,address=a),self.assertRaises(ValueError):v.projection_preserved(p,phase,[(a,n)])
 def test_40_every_callee_boundary_preserves_zero_callback1(self):
  for row in v.finite_case(self.raw)['conditional_calls']:
   with self.subTest(phase=row['phase'],callsite=row['callsite']):
    self.assertTrue(any(x['address']==0x03003130 and x['size']==4 and 'zero' in x['role'] for x in row['protected_fields']))
 def test_41_actual_main_callee_mutation_diverts_first_dispatch(self):
  # 同じ実main consumerへ入り、最初の外部gate内でcallback1だけを書換える反証。
  # 正常ABI復帰だけでは足りず、追加したcell保存が必要なことを示す。
  def first_dispatch(corrupt):
   mem={};v.runtime.setmem(mem,0x03003130,4,0);v.runtime.setmem(mem,0x03003134,4,0x0811F3A9)
   m=v.TutorMachine(self.raw,0x08000510,memory=mem,instructions=v.INS)
   mutation=[]
   while m.pc!=0x081C7AC8:
    if m.pc in (0x080F6168,0x0813C034):
     if corrupt and m.pc==0x080F6168:
      mutation.append((0x03003130,4));m.write(0x03003130,4,0x08128155)
     m.reg[0]=0;m.reg[1:4]=[v.runtime.U]*3;m.pc=m.reg[14]&~1
    else:m.step()
   return m.reg[0],m.calls[-1][0],mutation
  normal,normal_site,_=first_dispatch(False);changed,changed_site,writes=first_dispatch(True)
  self.assertEqual(normal,0x0811F3A9);self.assertEqual(changed,0x08128155)
  self.assertNotEqual(normal_site,changed_site)
  with self.assertRaises(ValueError):v.projection_preserved(v.runtime.ROOT+v.runtime.HEADER,'choose',writes)
 def test_42_callback1_condition_cannot_be_dropped(self):
  self.reject_review(lambda r:r['input_contract'].pop('main_callback1'))
