"""新runtime scopeの反証。旧suiteを再走しない。"""
import copy,unittest
from unittest.mock import patch
import pr16_dex_hof_runtime_party as v
FIXTURE=None
SOURCES=None
class RuntimeTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit whole input fixture')
  self.raw,self.review=FIXTURE
 def test_01_exact_semantics(self):self.assertEqual(v.binding(self.raw,self.review)['instructions'],227)
 def test_02_all_new_halfword_mutations_resealed(self):
  for rows in v.BLOCKS.values():
   for ins in rows:
    for a in range(ins.address,ins.address+ins.size,2):
     raw=bytearray(self.raw);raw[a-0x08000000]^=1
     with self.assertRaises(ValueError):v.binding(raw,v.make_review(raw))
 def test_03_all_literal_mutations_resealed(self):
  for a in v.LITERALS:
   raw=bytearray(self.raw);raw[a-0x08000000]^=1
   with self.assertRaises(ValueError):v.binding(raw,v.make_review(raw))
 def test_04_omitted_window(self):
  r=copy.deepcopy(self.review);r['instruction_windows'].pop('alloc_split')
  with self.assertRaises(ValueError):v.binding(self.raw,r)
 def test_05_unknown_field(self):
  r=copy.deepcopy(self.review);r['invented']=True
  with self.assertRaises(ValueError):v.binding(self.raw,r)
 def test_06_classification_promotion_rejected(self):
  r=copy.deepcopy(self.review);r['classifications_added']=1
  with self.assertRaises(ValueError):v.binding(self.raw,r)
 def test_07_donor_promotion_rejected(self):
  r=copy.deepcopy(self.review);r['donor_eligible']=True
  with self.assertRaises(ValueError):v.binding(self.raw,r)
 def test_08_runtime_promotion_rejected(self):
  r=copy.deepcopy(self.review);r['whole_runtime_lifetime_proven']=True
  with self.assertRaises(ValueError):v.binding(self.raw,r)
 def test_09_geometry_all_lengths(self):self.assertEqual(v.geometry_theorem()['payload_sizes_checked'],28527)
 def test_10_split_boundaries(self):
  for extra in range(0,40,4):
   _,_,r=v.allocate_case(self.raw,[(0,v.REQUEST+extra)]);self.assertEqual(r['split'],extra>=32)
 def test_11_existing_live_nonalias(self):
  m,size,r=v.allocate_case(self.raw,[(1,32),(0,1024),(1,12)])
  self.assertEqual(r['return_pointer'],v.ROOT+64)
 def test_12_insufficient_free_rejected(self):
  with self.assertRaisesRegex(ValueError,'free fit'):v.allocate_case(self.raw,[(0,v.REQUEST-4)])
 def test_13_oom_assert_not_invented_return(self):
  mem,_=v.heap_fixture([(1,v.REQUEST)])
  with self.assertRaisesRegex(ValueError,'outside closed model'):v.execute(self.raw,0x08002B9C,{0:v.REQUEST},mem)
 def test_14_alignment(self):
  for n in range(565,573):
   _,_,r=v.allocate_case(self.raw,[(0,1024)],n);self.assertEqual(r['requested'],(n+3)&~3)
 def test_15_bad_header_magic_rejected(self):
  mem,size=v.heap_fixture([(0,1024)]);v.setmem(mem,v.ROOT+2,2,0)
  with self.assertRaises(ValueError):v.well_formed(mem,size)
 def test_16_bad_next_cycle_rejected(self):
  mem,size=v.heap_fixture([(0,1024),(1,4)]);v.setmem(mem,v.ROOT+12,4,v.ROOT)
  with self.assertRaises(ValueError):v.well_formed(mem,size)
 def test_17_bad_size_escape_rejected(self):
  mem,size=v.heap_fixture([(0,1024)]);v.setmem(mem,v.ROOT+4,4,v.LIMIT)
  with self.assertRaises(ValueError):v.well_formed(mem,size)
 def test_18_bad_root_cell_rejected(self):
  mem,size=v.heap_fixture([(0,1024)]);v.setmem(mem,v.ROOT_CELL,4,v.HEAP_CELL)
  with self.assertRaises(ValueError):v.well_formed(mem,size)
 def test_19_actual_aba_counterexample(self):
  r=v.epoch_counterexample(self.raw);self.assertTrue(r['same_pointer']);self.assertTrue(r['same_header']);self.assertTrue(r['same_callback_fields']);self.assertFalse(r['same_epoch'])
 def test_20_free_before_copy_rejected(self):
  p=v.ROOT+16
  with self.assertRaisesRegex(ValueError,'ends epoch'):v.projection_preserved(p,'mail_exit',[],freed=[p])
 def test_21_reset_before_copy_rejected(self):
  with self.assertRaisesRegex(ValueError,'reset'):v.projection_preserved(v.ROOT+16,'mail_exit',[],heap_reinitialized=True)
 def test_22_free_after_copy_permitted(self):self.assertTrue(v.projection_preserved(v.ROOT+16,'after_mail_copy',[(v.ROOT,16)],freed=[v.ROOT+16]))
 def test_23_old_object_reuse_after_copy_permitted(self):self.assertTrue(v.projection_preserved(v.ROOT+16,'after_mail_copy',[(v.ROOT,1024)],heap_reinitialized=True))
 def test_24_main_callback_clobber_after_copy_rejected(self):
  with self.assertRaises(ValueError):v.projection_preserved(v.ROOT+16,'after_mail_copy',[(0x03003134,4)])
 def test_25_object_fields_clobber_before_copy_rejected(self):
  for off in (0,4):
   with self.assertRaises(ValueError):v.projection_preserved(v.ROOT+16,'mail_exit',[(v.ROOT+16+off,4)])
 def test_26_other_heap_payload_allowed(self):self.assertTrue(v.projection_preserved(v.ROOT+16,'mail_exit',[(v.ROOT+1024,100)]))
 def test_27_task_data_allowed(self):self.assertTrue(v.projection_preserved(v.ROOT+16,'menu',[(v.TASKS+8,32)]))
 def test_28_selected_task_active_clobber_rejected(self):
  with self.assertRaises(ValueError):v.projection_preserved(v.ROOT+16,'menu',[(v.TASKS+4,1)])
 def test_29_all_16_free_slots_admitted(self):self.assertEqual(v.task_admission_effects(self.raw)['cases'],17)
 def test_30_full_task_list_rejected(self):
  with self.assertRaisesRegex(ValueError,'free slot'):v.admit_party_task(self.raw,v.task_fixture([(i,i) for i in range(16)]))
 def test_31_broken_task_membership_rejected(self):
  mem=v.task_fixture([(0,1),(1,2)]);v.setmem(mem,v.TASKS+6,1,255)
  with self.assertRaisesRegex(ValueError,'connected'):v.admit_party_task(self.raw,mem)
 def test_32_duplicate_task_head_rejected(self):
  mem=v.task_fixture([(0,1),(1,2)]);v.setmem(mem,v.TASKS+45,1,254)
  with self.assertRaisesRegex(ValueError,'head'):v.task_chain(mem)
 def test_33_unknown_write_rejected(self):
  with self.assertRaises(ValueError):v.projection_preserved(v.ROOT+16,'menu',[(None,4)])
 def test_34_stack_alias_is_not_proved_by_geometry(self):self.assertIn('stack valid and nonalias',v.geometry_theorem()['preconditions'])
 def test_35_frontier_retains_unknown_callees(self):
  p=v.minimal_frontier();self.assertFalse(p['classification_ready_here']);self.assertTrue(any(r['status']=='conditional_callee_frontier' for r in p['setup_success_calls']))
 def test_36_public_source_mismatch_rejected(self):
  with self.assertRaises(ValueError):v.source_proof(b'fabricated source')
 def test_37_missing_cmp_provenance_rejected(self):
  m=v.Machine(self.raw,0x0800296E);m.flags=(0,True,True,False)
  with self.assertRaisesRegex(ValueError,'flag provenance'):m.step()
 def test_38_free_foreign_pointer_rejected(self):
  with self.assertRaises(ValueError):v.execute(self.raw,0x08002BC4,{0:v.HEAP_CELL},{})
 def test_39_no_false_region(self):
  raw=bytearray(self.raw);raw[-1]^=1
  with self.assertRaisesRegex(ValueError,'current candidate'):v.regions(bytes(raw),{'candidate':v.CANDIDATE},self.review,SOURCES)

 def test_40_mail_copy_frees_before_consumer(self):
  p=v.mail_copy_and_consumer(self.raw);self.assertTrue(p['actual_free_executed']);self.assertFalse(p['freed_object_needed_at_hit']);self.assertEqual(p['getmondata_field_at_hit'],64)
 def test_41_mail_phase_keeps_unproved_conditions(self):
  p=v.mail_copy_and_consumer(self.raw);self.assertEqual(len(p['conditional_calls']),4);self.assertTrue(all(not x['discharged'] for x in p['conditional_calls']))
 def test_42_mail_target_literal_mutation(self):
  raw=bytearray(self.raw);raw[0x0812455C-0x08000000]^=1
  with self.assertRaises(ValueError):v.mail_copy_and_consumer(raw)
 def test_43_mail_action_root_mutation(self):
  raw=bytearray(self.raw);raw[0x08419DEC-0x08000000]^=1
  with self.assertRaises(ValueError):v.mail_copy_and_consumer(raw)
 def test_44_mail_copy_field_mutation(self):
  raw=bytearray(self.raw);raw[0x081202CA-0x08000000]^=1
  with self.assertRaises(ValueError):v.mail_copy_and_consumer(raw)
 def test_45_callback2_consumer_field_mutation(self):
  raw=bytearray(self.raw);raw[0x08000530-0x08000000]^=1
  with self.assertRaises(ValueError):v.binding(raw,v.make_review(raw))
 def test_46_envelope_type_promote_width_rejected(self):
  r=copy.deepcopy(self.review);r['read_mail_type']['maximum_target_access_width_proven']=True
  with self.assertRaises(ValueError):v.binding(self.raw,r)
 def test_47_envelope_arbitrary_root_rejected(self):
  r=copy.deepcopy(self.review);r['read_mail_type']['root_table']['address']+=4
  with self.assertRaises(ValueError):v.binding(self.raw,r)
 def test_48_inherited_review_identity_mutation_rejected(self):
  r=copy.deepcopy(self.review);r['inherited_reviews']=copy.deepcopy(r['inherited_reviews']);r['inherited_reviews']['party_review']['sha256']='0'*64
  with self.assertRaises(ValueError):v.binding(self.raw,r)

 def fixture_inherited(self):
  return {'candidate':v.CANDIDATE,'hits':[dict(v.window(self.raw,h,4),accepted=False,owner_candidates=[]) for h in (0x08124573,0x08126B0B)]}
 def test_49_new_single_registered_type_synthetic_accounting(self):
  regions,p=v._regions(self.raw,self.fixture_inherited(),self.review,SOURCES);self.assertEqual(len(regions),1);self.assertEqual(p['newly_classified'],1);self.assertFalse(p['universal_allocation_epoch_proven']);self.assertFalse(p['maximum_target_access_width_proven']);self.assertEqual(p['retained_unknown_hits'],[0x08126B0B])
 def test_50_type_refuses_already_accepted(self):
  inherited=self.fixture_inherited();inherited['hits'][0]['accepted']=True
  with self.assertRaises(ValueError):v._regions(self.raw,inherited,self.review,SOURCES)
 def test_51_type_refuses_owner_internal(self):
  inherited=self.fixture_inherited();inherited['hits'][0]['owner_candidates']=['owner']
  with self.assertRaises(ValueError):v._regions(self.raw,inherited,self.review,SOURCES)
 def test_52_inherited_review_wrong_bytes(self):
  src=dict(SOURCES);src['party_review']=src['party_review']+b' '
  with self.assertRaisesRegex(ValueError,'immutable'):v.compose_prior(self.raw,self.review,src)
 def test_53_root_table_resealed_mutation(self):
  raw=bytearray(self.raw);raw[0x0836B380-0x08000000]^=1
  with self.assertRaises(ValueError):v.compose_prior(raw,v.make_review(raw),SOURCES)
 def test_54_action_default_hook_resealed_mutation(self):
  raw=bytearray(self.raw);raw[0x09097AA8-0x08000000]^=1
  with self.assertRaises(ValueError):v.compose_prior(raw,v.make_review(raw),SOURCES)
 def test_55_task_constructor_argument_mutation(self):
  raw=bytearray(self.raw);raw[0x0812780C-0x08000000]^=1
  with self.assertRaises(ValueError):v.compose_prior(raw,v.make_review(raw),SOURCES)
 def test_56_false_hit_envelope(self):
  inherited=self.fixture_inherited();inherited['hits'][0]['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'ReadMail hit'):v._regions(self.raw,inherited,self.review,SOURCES)
 def test_57_extra_no_classification_for_tutor(self):
  regions,p=v._regions(self.raw,self.fixture_inherited(),self.review,SOURCES);self.assertEqual(p['newly_typed_hits'],[0x08124573]);self.assertEqual(regions[0].end-regions[0].start,6)

 def test_58_reject_arm_interwork_value(self):
  m=v.Machine(self.raw,0x081C7AC8,{0:0x08124560})
  with self.assertRaisesRegex(ValueError,'Thumb'):m.step()
 def test_59_reject_misaligned_memory(self):
  m=v.Machine(self.raw,0x08002B9C)
  with self.assertRaisesRegex(ValueError,'aligned'):m.read(v.ROOT+1,4)
  with self.assertRaisesRegex(ValueError,'aligned'):m.write(v.ROOT+1,2,0)
