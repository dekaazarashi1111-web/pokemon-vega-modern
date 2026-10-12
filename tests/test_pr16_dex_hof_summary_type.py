"""Summary新範囲のみ。実根・最小型・意味mutation・最小live射影の反証。"""
import copy
import unittest
from unittest import mock
import pr16_dex_hof_summary_type as v
FIXTURE=None

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=v.identity(v.chunk(raw,obj['address'],obj['size']))['sha256']
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)

class SummaryMinimumTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit in-memory FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
  cls.machine,cls.composition=v._checked_compose(cls.raw)
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,edit):
  r=copy.deepcopy(self.review);edit(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def reject_evidence(self,edit):
  e=v.evidence_template();edit(e)
  with self.assertRaises((ValueError,KeyError,TypeError)):v.witness_geometry(e)
 def test_01_one_six_byte_classification(self):
  old=copy.deepcopy(self.inherited);rows,p=self.check()
  self.assertEqual([(r.start,r.end,r.kind) for r in rows],[(v.HIT-1,v.HIT+5,v.KIND)])
  self.assertEqual(v.witness_geometry(rows[0].evidence),(v.HIT-1,6));self.assertEqual(self.inherited,old);self.assertEqual(p['count'],1)
 def test_02_actual_installed_hook_not_old_direct_registration(self):
  e=next(e for e in self.composition['events'] if e['role']=='installed_summary_task_admission')
  self.assertEqual(e['callback'],0x09378491);self.assertEqual(v.ALL_WORDS[0x09378544],0x08135029)
  self.assertEqual(v.INS[0x09378558].args,(3,));self.assertEqual(v.ROOT['installed_task_literal'],0x08137570)
 def test_03_exact_hook_predicate_argument_and_conditional_return(self):
  rows=[r for r in self.composition['conditional_call_catalog'] if r['site']==0x093784A0]
  self.assertTrue(rows);self.assertTrue(all(r['return_value']==0 and not r['effects_discharged'] for r in rows))
 def test_04_actual_alloczero_requests_and_distinct_objects(self):
  a=self.composition['allocations'];self.assertEqual([r['requested'] for r in a],[12980,40]);self.assertNotEqual(a[0]['pointer'],a[1]['pointer'])
 def test_05_zero_fill_real_argument_count_and_conditional_output(self):
  r=[r for r in self.composition['conditional_call_catalog'] if r['site']==0x08002B18]
  self.assertEqual(sorted(q['conditional_outputs'][0]['size'] for q in r),[40,12980]);self.assertTrue(all(not q['effects_discharged'] for q in r))
 def test_06_complete_actual_cpuset_stub_semantics(self):
  self.assertEqual([(i.kind,i.args) for i in v.BIOS_SEMANTICS],[('swi',(11,)),('bx',(14,))])
 def test_07_old_party_copy_precedes_cleanup_and_new_admission(self):
  names=[x['role'] for x in self.composition['events']]
  self.assertLess(names.index('party_exit_callback_copied'),names.index('installed_summary_task_admission'))
 def test_08_two_right_flip_tasks_actually_destroyed(self):
  e=self.composition['events'];a=[x for x in e if x['role']=='temporary_flip_admission'];z=[x for x in e if x['role']=='temporary_flip_completed']
  self.assertEqual([x['page'] for x in a],[1,2]);self.assertEqual([x['page'] for x in z],[1,2]);self.assertTrue(all(x['task_id']!=self.composition['selected_task'] for x in a))
 def test_09_same_input_task_replaced(self):
  e=next(x for x in self.composition['events'] if x['role']=='same_input_task_replaced');self.assertEqual(e['task_id'],self.composition['selected_task']);self.assertEqual(e['site'],0x08135302)
 def test_10_frominfo_only_required_prefix(self):
  self.assertEqual(self.composition['frominfo_preceding_states'],[0,1,2]);self.assertEqual(self.composition['reached_instruction'],v.HIT-1)
  self.assertFalse(self.composition['callee_at_hit_executed']);self.assertNotIn(0x081357AC,v.INS)
 def test_11_setup8_prefix_shared_for_nature(self):
  m,p=v.root_at_setup(self.raw,8);a=m.read(v.SUMMARY,4)
  self.assertEqual(m.pc,0x081364A0);self.assertEqual([m.read(a+x,1) for x in (0x31B4,0x31C0,0x31AC,0x3220)],[0,0,0,8]);self.assertEqual(m.read(a+0x3024,4),0)
 def test_12_current_candidate_gate_rejects_diagnostic_without_whole_rehash(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),self.assertRaises(ValueError):v.regions(*FIXTURE)
 def test_13_wrong_parent_candidate(self):
  i=copy.deepcopy(self.inherited);i['candidate']['sha256']='0'*64
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_14_original_unknown_owner_external_required(self):
  for k,val in [('accepted',True),('owner_candidates',['owner']),('kind','POINTER'),('size',True)]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][k]=val;r['hit'][k]=val
   with self.subTest(k=k),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_15_duplicate_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(self.review['hit']))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_16_dropped_dependency(self):self.reject_review(lambda r:r['windows'].pop())
 def test_17_window_shape(self):self.reject_review(lambda r:r['windows'][0].update(extra=1))
 def test_18_window_geometry(self):self.reject_review(lambda r:r['windows'][0].update(address=True))
 def test_19_window_digest_format(self):self.reject_review(lambda r:r['windows'][0].update(sha256='Z'*64))
 def test_20_closed_schema(self):self.reject_review(lambda r:r.update(unapproved=1))
 def test_21_boolean_schema(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_22_diagnostic_current_conflation(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_23_drop_abi_contract(self):self.reject_review(lambda r:r['input_contract'].pop('callee_frame'))
 def test_24_drop_installed_root(self):self.reject_evidence(lambda e:e['root'].pop('installed_task'))
 def test_25_four_odd_bytes_not_complete_instructions(self):self.reject_evidence(lambda e:e['instruction_window'].update(address=v.HIT,size=4))
 def test_26_half_bl_rejected(self):self.reject_evidence(lambda e:e['instructions'][0].update(size=2))
 def test_27_wider_function_not_classified(self):self.reject_evidence(lambda e:e['instruction_window'].update(size=8))
 def test_28_no_target_return_observation(self):self.reject_evidence(lambda e:e['claims'].update(bl_return_observed=True))
 def test_29_no_natural_universal_reachability(self):self.reject_evidence(lambda e:e['claims'].update(full_story_reachability_claimed=True))
 def test_30_no_opaque_effect_promotion(self):self.reject_evidence(lambda e:e['claims'].update(all_opaque_effects_proven=True))
 def test_31_no_resource_lifetime_promotion(self):self.reject_evidence(lambda e:e['claims'].update(universal_allocation_epoch_proven=True))
 def test_32_no_donor_lease(self):self.reject_evidence(lambda e:e['claims'].update(donor_leased=True))
 def test_33_source_identity_mutations(self):
  for name in v.SOURCE_IDS:
   sources=dict(self.sources);b=bytearray(sources[name]);b[len(b)//2]^=1;sources[name]=bytes(b)
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources=sources)
 def test_34_every_instruction_halfword_semantic_mutation(self):
  raw=bytearray(self.raw)
  for a in sorted({a for i in [*v.INS.values(),*v.BIOS_SEMANTICS] for a in range(i.address,i.address+i.size,2)}):
   off=a-0x08000000;raw[off]^=1
   try:
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)
   finally:raw[off]^=1
 def test_35_every_literal_and_dispatch_cell_semantic_mutation(self):
  raw=bytearray(self.raw)
  for a in v.ALL_WORDS:
   off=a-0x08000000;raw[off]^=1
   try:
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)
   finally:raw[off]^=1
 def test_36_resealed_critical_instruction_mutations_rejected(self):
  for a in (0x0812353C,0x081202D0,0x08134D08,0x08137558,0x093784AC,0x09378558,0x08135168,0x081352D6,0x08135302,0x08135684,0x08135968,v.HIT-1,v.HIT+3,0x081C7A88):
   raw=bytearray(self.raw);raw[a-0x08000000]^=1;r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
   with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
 def test_37_resealed_actual_installed_pointer_rejected(self):
  raw=bytearray(self.raw);a=0x08137570;raw[a-0x08000000:a-0x08000000+4]=(0x08135029).to_bytes(4,'little');r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
  with self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
 def test_38_hook_nonzero_not_silently_promoted(self):
  for value in (1,-1,True):
   with self.subTest(value=value),self.assertRaises(ValueError):v.compose_selected(self.raw,hook_result=value)
 def test_39_normal_return_condition_mandatory(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,normal_returns=False)
 def test_40_zero_fill_condition_mandatory(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,zero_fill=False)
 def test_41_live_preservation_condition_mandatory(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,fields_preserved=False)
 def test_42_each_boundary_has_concrete_live_projection(self):
  p=self.composition;self.assertTrue(p['live_projection_replay_checked']);self.assertTrue(p['live_projection_catalog'])
  for row in p['conditional_call_catalog']:
   fields=p['live_projection_catalog'][row['preserve_projection']];self.assertTrue(fields)
   for a,n in fields:self.assertIs(type(a),int);self.assertGreater(n,0)
   self.assertFalse(row['effects_discharged']);self.assertTrue(row['normal_return_assumed'])
 def test_43_all_nonlive_ram_can_be_clobbered(self):
  self.assertIsInstance(self.machine.mem[0x0203C013],v.runtime.Unknown)
 def test_44_nonlive_explicit_write_allowed_through_actual_replay(self):
  p=v.compose_selected(self.raw,opaque_writes={0x081350CC:[(0x02028000,4,0x13579)]});self.assertEqual(p['reached_instruction'],v.HIT-1);self.assertTrue(p['live_projection_replay_checked'])
 def test_45_live_pointer_write_rejected_through_actual_replay(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0x081350CC:[(v.SUMMARY,4,0)]})
 def test_46_live_task_function_write_rejected_through_actual_replay(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0x081350CC:[(v.TASKS,4,0)]})
 def test_47_live_nature_enemy_field_rejected_in_shared_prefix(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v._checked_compose(self.raw,stop_setup=8,opaque_writes={0x0813648C:[(0x02000010+0x3024,4,1)]})
 def test_48_declared_outputs_are_producers_not_preservation(self):
  p=self.composition
  for r in p['conditional_call_catalog']:
   for a,n in r['produced_memory_ranges']:
    self.assertTrue(all(v.runtime.disjoint(a,n,b,m) for b,m in p['live_projection_catalog'][r['preserve_projection']]))
 def test_49_new_summary_epoch_cannot_free_and_restore(self):
  with self.assertRaisesRegex(ValueError,'epoch'):v.compose_selected(self.raw,epoch_events={0x0813647A:{'freed':[0x02000010]}})
 def test_50_heap_reset_epoch_rejected(self):
  with self.assertRaisesRegex(ValueError,'epoch'):v.compose_selected(self.raw,epoch_events={0x0813647A:{'heap_reinitialized':True}})
 def test_51_old_party_free_after_copy_is_allowed(self):
  p=v.compose_selected(self.raw,epoch_events={0x0811F878:{'freed':[0x02000010]}});self.assertEqual(p['reached_instruction'],v.HIT-1)
 def test_52_no_literal_pool_in_type(self):
  e=v.evidence_template();self.assertFalse(e['literal_pool_included']);self.assertNotEqual(v.ALL_WORDS[0x081357D0],v.HIT)
 def test_53_setup_prefix_invalid_state_rejected(self):
  for state in (-1,16,True,1.5):
   with self.subTest(state=state),self.assertRaises(ValueError):v._compose(self.raw,stop_setup=state)
