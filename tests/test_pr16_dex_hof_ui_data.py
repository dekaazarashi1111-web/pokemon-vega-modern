"""新Fame Checker型だけの根・最小境界・意味・live反証。"""
import copy,unittest
from unittest import mock
import pr16_dex_hof_ui_data as v
FIXTURE=None
class Mutation:
 def __init__(self,base,address,value=None):self.base,self.address,self.value=base,address,value
 def __len__(self):return len(self.base)
 def __getitem__(self,s):
  b=bytearray(self.base[s]);a=self.address-0x08000000
  if s.start<=a<s.stop:b[a-s.start]=b[a-s.start]^1 if self.value is None else self.value
  return bytes(b)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=v.identity(v.chunk(raw,obj['address'],obj['size']))['sha256']
  for item in obj.values():reseal(item,raw)
 elif isinstance(obj,list):
  for item in obj:reseal(item,raw)
class UiDataTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit in-memory FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
  cls.machine,cls.first=v._compose(cls.raw)
  cls.proof=v.compose_selected(cls.raw)
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,edit):
  r=copy.deepcopy(self.review);edit(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def reject_evidence(self,edit):
  e=v.evidence_template();edit(e)
  with self.assertRaises((ValueError,KeyError,TypeError)):v.witness_geometry(e)
 def test_01_minimum_code_and_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);rows,p=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in rows],[(v.HIT-1,v.HIT+5,v.KIND)])
  self.assertEqual(v.witness_geometry(rows[0].evidence),(v.HIT-1,6));self.assertEqual(self.inherited,before);self.assertEqual(p['count'],1)
 def test_02_actual_registration_and_state_production(self):
  events=self.proof['events'];self.assertEqual([e['state']for e in events if e['role']=='main_dispatched_setup'],list(range(7)))
  self.assertEqual(next(e for e in events if e['role']=='actual_callback_registered')['callback'],0x0812CBE1)
 def test_03_actual_record_produces_person(self):
  e=[e for e in self.proof['events']if e['role']=='actual_person_slot_writer']
  self.assertEqual(e,[{'role':'actual_person_slot_writer','site':0x0812E788,'index':0,'slot':0}])
 def test_04_real_alloc_requests_disjoint(self):
  rows=self.proof['allocations'];self.assertEqual([r['size']for r in rows],[36,2048,4096,2048,136])
  for i,a in enumerate(rows):
   for b in rows[i+1:]:self.assertTrue(v.runtime.disjoint(a['pointer'],a['size'],b['pointer'],b['size']))
 def test_05_six_explicit_sprite_successes(self):
  outs=[o for r in self.proof['conditional_call_catalog']for o in r['conditional_outputs']if 'sprite_id'in o]
  self.assertEqual([o['sprite_id']for o in outs],list(range(6)))
 def test_06_stop_before_target(self):
  self.assertEqual(self.proof['stopped_at'],v.HIT-1);self.assertFalse(self.proof['callee_at_hit_executed']);self.assertNotIn(0x0812D8DC,v.INS)
 def test_07_external_constructor_precondition_explicit(self):
  self.assertTrue(v.CLAIMS['external_constructor_invocation_is_precondition']);self.assertFalse(v.CLAIMS['item_menu_invocation_proven']);self.assertFalse(v.CLAIMS['full_story_reachability_claimed'])
 def test_08_nonlive_replay_and_live_ranges(self):
  self.assertTrue(self.proof['live_projection_replay_checked'])
  for row in self.proof['conditional_call_catalog']:
   self.assertFalse(row['effects_discharged']);self.assertTrue(row['normal_return_assumed']);self.assertTrue(row['preserve_projection'])
   for a,n in row['preserve_projection']:self.assertIs(type(a),int);self.assertGreater(n,0)
 def test_09_outputs_disjoint_from_preserved_fields(self):
  for row in self.proof['conditional_call_catalog']:
   for a,n in row['produced_memory_ranges']:
    for b,m in row['preserve_projection']:self.assertTrue(v.runtime.disjoint(a,n,b,m))
 def test_10_declared_live_pointer_counterexample(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0x0812CD88:[(v.CELL,4,0)]})
 def test_11_declared_live_record_counterexample(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0x0812CD88:[(0x02022000+0x3A54,2,0)]})
 def test_12_main_callback_live_counterexample(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0x0812CC38:[(v.MAIN+4,4,0)]})
 def test_13_saved_stack_live_counterexample(self):
  row=next(r for r in self.proof['conditional_call_catalog']if r['site']==0x0812CBC6)
  a=next(a for a,n in row['preserve_projection']if 0x03006000<=a<0x03007000)
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={row['site']:[(a,1,0)]})
 def test_14_nonlive_write_is_allowed(self):
  p=v.compose_selected(self.raw,opaque_writes={0x0812CD88:[(0x02030000,4,0x9876)]});self.assertEqual(p['stopped_at'],v.HIT-1)
 def test_15_object_free_before_final_read_rejected(self):
  with self.assertRaisesRegex(ValueError,'epoch'):v.compose_selected(self.raw,epoch_events={0x0812CD88:{'freed':[self.proof['allocations'][0]['pointer']]}})
 def test_16_heap_reinit_rejected(self):
  with self.assertRaisesRegex(ValueError,'epoch'):v.compose_selected(self.raw,epoch_events={0x0812CD88:{'heap_reinitialized':True}})
 def test_17_bg_buffers_not_required_after_last_use(self):
  p=v.compose_selected(self.raw,epoch_events={0x0812CD88:{'freed':[r['pointer']for r in self.proof['allocations'][1:4]]}})
  self.assertEqual(p['stopped_at'],v.HIT-1)
 def test_18_buffer_epoch_required_at_copy(self):
  with self.assertRaisesRegex(ValueError,'epoch'):v.compose_selected(self.raw,epoch_events={0x0812CD4E:{'freed':[self.proof['allocations'][1]['pointer']]}})
 def test_19_normal_returns_required(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,normal_returns=False)
 def test_20_zero_fill_required(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,zero_fill=False)
 def test_21_valid_resources_required(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,resources_valid=False)
 def test_22_other_record_profile_not_accepted(self):
  for x in (0,2,True):
   with self.subTest(value=x),self.assertRaises(ValueError):v.compose_selected(self.raw,save_flags=x)
 def test_23_nonnull_callback1_not_assumed_away(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,main_callback1=1)
 def test_24_every_instruction_halfword_semantic_mutation(self):
  for a in sorted({a for i in [*v.INS.values(),*v.summary.BIOS_SEMANTICS]for a in range(i.address,i.address+i.size,2)}):
   with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_25_all_literal_cells_and_fields_mutation(self):
  for a in [*v.WORDS,0x084218EE,0x08421B50]:
   with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_26_resealed_registration_producer_minimum_mutations(self):
  for a in (0x0812CBA6,0x0812CBCC,0x08000546,0x0812CDB2,0x0812E788,0x0812CD8E,0x0812DAEE,0x0812DAF2):
   raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
   with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
 def test_27_source_identity_mutations(self):
  for name,b in self.sources.items():
   src=dict(self.sources);src[name]=b+b'\n'
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources=src)
 def test_28_review_closed_schema(self):self.reject_review(lambda r:r.update(extra=1))
 def test_29_boolean_schema(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_30_missing_window(self):self.reject_review(lambda r:r['windows'].pop())
 def test_31_window_shape(self):self.reject_review(lambda r:r['windows'][0].update(extra=1))
 def test_32_window_geometry(self):self.reject_review(lambda r:r['windows'][0].update(address=True))
 def test_33_window_hash_format(self):self.reject_review(lambda r:r['windows'][0].update(sha256='Z'*64))
 def test_34_review_claim_promotion(self):self.reject_review(lambda r:r['claims'].update(item_menu_invocation_proven=True))
 def test_35_contract_drop(self):self.reject_review(lambda r:r['input_contract'].pop('liveness'))
 def test_36_diagnostic_current_conflation(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_37_inherited_identity_wrong(self):
  i=copy.deepcopy(self.inherited);i['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_38_hit_must_remain_unknown(self):
  for k,x in [('accepted',True),('owner_candidates',['owner']),('kind','POINTER'),('size',True)]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][k]=x;r['hit'][k]=x
   with self.subTest(key=k),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_39_duplicate_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(i['hits'][0]))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_40_current_gate_does_not_classify_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),self.assertRaises(ValueError):v.regions(*FIXTURE)
 def test_41_geometry_half_bl_rejected(self):self.reject_evidence(lambda e:e['instructions'][0].update(size=2))
 def test_42_geometry_odd_bytes_not_instructions(self):self.reject_evidence(lambda e:e['instruction_window'].update(address=v.HIT,size=4))
 def test_43_geometry_no_whole_function(self):self.reject_evidence(lambda e:e['instruction_window'].update(size=100))
 def test_44_no_return_claim(self):self.reject_evidence(lambda e:e['claims'].update(bl_return_observed=True))
 def test_45_no_natural_play_claim(self):self.reject_evidence(lambda e:e['claims'].update(full_story_reachability_claimed=True))
 def test_46_no_effect_claim(self):self.reject_evidence(lambda e:e['claims'].update(opaque_callee_effects_proven=True))
 def test_47_no_donor_lease(self):self.reject_evidence(lambda e:e['claims'].update(donor_leased=True))
 def test_48_ui_data_other_candidates_not_typed(self):
  self.assertEqual(v.HITS,(0x0812DAEF,));self.assertEqual(v.TYPE_CATEGORY,'code');self.assertEqual(v.witness_geometry(v.evidence_template()),(0x0812DAEE,6))
