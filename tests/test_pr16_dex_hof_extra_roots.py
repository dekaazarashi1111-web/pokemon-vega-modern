"""新2根だけの閉鎖型・独立意味・実producerと最小live契約反証。"""
import copy,hashlib,unittest
from unittest import mock
import pr16_dex_hof_extra_roots as v
FIXTURE=None
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
class ExtraRootTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit bounded-memory FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
  cls.proof=v.compose_selected(cls.raw)
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,f):
  r=copy.deepcopy(self.review);f(r)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(review=r)
 def reject_evidence(self,hit,f):
  e=v.evidence_template(hit);f(e)
  with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_01_two_real_roots(self):
  old=copy.deepcopy(self.inherited);regions,proof=self.check();self.assertEqual(old,self.inherited)
  self.assertEqual([(r.start,r.end-r.start,r.kind)for r in regions],[(0x080B0112,6,v.KIND),(0x0814777A,8,v.KIND)])
  self.assertEqual(proof['count'],2)
 def test_02_only_full_thumb_geometry(self):
  self.assertEqual([v.witness_geometry(v.evidence_template(h))for h in v.HITS],[(0x080B0112,6),(0x0814777A,8)])
 def test_03_diagnostic_cannot_promote_current(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as p:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   p.assert_not_called()
 def test_04_current_gate_delegates_only_matching(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value='sentinel')as p:
   self.assertEqual(v.regions(*FIXTURE),'sentinel');p.assert_called_once()
 def test_05_separate_review_diagnostic(self):self.reject_review(lambda x:x.update(diagnostic_input=v.CANDIDATE))
 def test_06_inherited_current_required(self):
  i=copy.deepcopy(self.inherited);i['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_07_closed_review(self):self.reject_review(lambda x:x.update(extra=True))
 def test_08_integer_schema(self):self.reject_review(lambda x:x.update(schema_version=True))
 def test_09_exact_root_semantics(self):self.reject_review(lambda x:x['roots'][str(v.HITS[0])].update(command_offset=66))
 def test_10_exact_contract(self):self.reject_review(lambda x:x['input_contract'].pop('shockwave'))
 def test_11_windows_closed_geometry(self):self.reject_review(lambda x:x['windows'].pop())
 def test_12_window_cannot_reseal_unmodified(self):self.reject_review(lambda x:x['windows'][0].update(sha256='0'*64))
 def test_13_windows_order(self):self.reject_review(lambda x:x['windows'].reverse())
 def test_14_no_raw_window_field(self):self.reject_review(lambda x:x['windows'][0].update(raw='forbidden'))
 def test_15_duplicate_prior(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(i['hits'][0]))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_16_owner_unknown_unchanged(self):
  for key,value in [('accepted',True),('accepted',0),('owner_candidates',['new']),('size',True),('kind','POINTER'),('classification','CODE')]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][key]=value;r['hits'][0][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_17_original_row_exact(self):self.reject_review(lambda x:x['hits'][0].update(reason='changed'))
 def test_18_source_full_identities(self):
  for key,b in self.sources.items():
   source=dict(self.sources);source[key]=b+b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=source)
 def test_19_no_extra_source(self):
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_20_no_missing_source(self):
  s=dict(self.sources);s.pop(next(iter(s)))
  with self.assertRaises(ValueError):self.check(sources=s)
 def test_21_no_source_reseal(self):self.reject_review(lambda x:x['source_bindings']['pret-task.c'].update(size=0))
 def test_22_all_instruction_halfwords(self):
  for i in v.INS.values():
   for a in range(i.address,i.address+i.size,2):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_23_all_literal_word_bytes(self):
  for a in v.WORDS:
   for j in range(4):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+j))
 def test_24_all_source_script_and_warp_data_bytes(self):
  for r in v.DATA:
   for a in range(r['address'],r['address']+r['size']):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_25_resealed_actual_producers(self):
  for a in [0x08071E32,0x08071E40,0x08071FDC,0x08072208,0x08076BCE,0x08076BE8,0x080B01EC,0x08147476,0x081475CA,0x081476D4,0x081476E8,0x0814773E,*v.HITS]:
   raw=Mutation(self.raw,a);i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);reseal(i,raw);reseal(r,raw)
   with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,inherited=i,review=r)
 def test_26_script_prefix_is_not_operand(self):
  rows=v.parse_script(self.raw);self.assertEqual(len(rows),15);self.assertEqual(rows[-2]['address'],0x081B1006)
  self.assertEqual(sum(r['size']for r in rows[:-2]),65);self.assertEqual(rows[-2]['argument_count'],0)
 def test_27_prefix_every_opcode_rejected(self):
  for row in v.parse_script(self.raw):
   with self.subTest(address=row['address']),self.assertRaises(ValueError):v.parse_script(Mutation(self.raw,row['address']))
 def test_28_prefix_every_vararg_count_rejected(self):
  for row in v.parse_script(self.raw):
   if row['argument_count']is not None:
    with self.subTest(address=row['address']),self.assertRaises(ValueError):v.parse_script(Mutation(self.raw,row['address']+6))
 def test_29_script_real_table_cell_rejected(self):
  with self.assertRaises(ValueError):v.parse_script(Mutation(self.raw,0x0904AC50))
 def test_30_script_real_command_pointer_priority_rejected(self):
  for a in range(0x081B1007,0x081B100C):
   with self.subTest(address=a),self.assertRaises(ValueError):v.parse_script(Mutation(self.raw,a))
 def test_31_shockwave_real_state_and_segment_producers(self):
  p=self.proof['cases'][0];self.assertEqual((p['scheduler_frames'],p['completed_segments'],p['sprite_failure_calls'],p['successful_sprites'],p['task_state']),(64,5,43,0,3))
  self.assertTrue(p['actual_next_delay12_executed']);self.assertTrue(p['dispatcher_returned_with_balanced_stack']);self.assertTrue(p['real_create_task_executed']);self.assertTrue(p['opcode_dispatch_executed']);self.assertTrue(p['initial_task_called']);self.assertTrue(p['initial_free_task_data_poisoned'])
 def test_32_seagallop_real_timer_state_and_clamp(self):
  p=self.proof['cases'][1];self.assertEqual((p['setup_frames'],p['task_frames'],p['actual_timer']),(8,158,140));self.assertTrue(p['actual_destination_clamped'])
 def test_33_all_actual_boundaries_minimal_live(self):
  count=0
  for case in self.proof['cases']:
   for b in case['conditional_call_catalog']:
    for a,n in b['required_fields']:
     for address in {a,a+n-1}:
      with self.subTest(root=case['root'],site=b['site'],address=address),self.assertRaisesRegex(ValueError,'future-live'):v.preservation_contract(b['required_fields'],[(address,1,0)])
      count+=1
  self.assertGreater(count,1000)
 def test_34_nonlive_ram_per_boundary_allowed(self):
  for case in self.proof['cases']:
   for b in case['conditional_call_catalog']:self.assertTrue(v.preservation_contract(b['required_fields'],[(0x02030000,4,123)]))
 def test_35_nonlive_memory_actually_erased(self):
  for p in self.proof['cases']:self.assertTrue(p['nonlive_ram_erased_at_every_boundary'])
 def test_36_live_stack_clobber_composition(self):
  for case in self.proof['cases']:
   b=next(x for x in case['conditional_call_catalog']if x['site']and any(0x03006000<=a<0x03007000 for a,n in x['required_fields']))
   a=next(a for a,n in b['required_fields']if 0x03006000<=a<0x03007000)
   with self.subTest(root=case['root']),self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,case=case['root'],opaque_writes={b['site']:[(a,1,0)]})
 def test_37_live_task_between_frames_rejected(self):
  for case in ('shockwave','seagallop'):
   with self.subTest(root=case),self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,case=case,opaque_writes={0:[(v.TASKS+4,1,0)]})
 def test_38_nonlive_composition_allowed(self):
  proof=v.compose_selected(self.raw,opaque_writes={0:[(0x02030000,4,0xDEADBEEF)]});self.assertEqual(len(proof['cases']),2)
 def test_39_tilemap_epoch_until_last_bg_use(self):
  p=self.proof['cases'][1]
  b=next(x for x in p['conditional_call_catalog']if x['required_resource_epochs']and x['site'])
  epochs=dict(task_epoch_changed=False,main_epoch_changed=False,tilemap_epoch_changed=True)
  with self.assertRaisesRegex(ValueError,'tilemap'):v.compose_selected(self.raw,case='seagallop',epoch_events={b['site']:epochs})
 def test_40_task_epoch_between_frames_rejected(self):
  epochs=dict(task_epoch_changed=True,main_epoch_changed=False,tilemap_epoch_changed=False)
  with self.assertRaisesRegex(ValueError,'task epoch'):v.compose_selected(self.raw,case='shockwave',epoch_events={0:epochs})
 def test_41_main_epoch_between_frames_rejected(self):
  epochs=dict(task_epoch_changed=False,main_epoch_changed=True,tilemap_epoch_changed=False)
  with self.assertRaisesRegex(ValueError,'callback epoch'):v.compose_selected(self.raw,case='seagallop',epoch_events={0:epochs})
 def test_42_nonreturning_opaque_rejected(self):
  for value in(False,1,None):
   with self.subTest(value=value),self.assertRaises(ValueError):v.compose_selected(self.raw,normal_returns=value)
 def test_43_invalid_resource_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,resources_valid=False)
 def test_44_closed_finite_input_profiles(self):
  for case in v.PROFILE:
   for key,value in v.PROFILE[case].items():
    p=copy.deepcopy(v.PROFILE[case]);p[key]=False if type(value)is bool else value+1
    with self.subTest(root=case,key=key),self.assertRaises(ValueError):v.compose_selected(self.raw,case=case,profile=p)
 def test_45_no_caller_selector_injection(self):
  p=copy.deepcopy(v.PROFILE['shockwave']);p['task_state']=3
  with self.assertRaises(ValueError):v.compose_selected(self.raw,case='shockwave',profile=p)
 def test_46_effect_keys_must_be_executed_R1(self):
  for a in (0x080B0112,0x0814777A,0x0814777E,0x08071D5C):
   for key,value in [('opaque_writes',[]),('epoch_events',dict(task_epoch_changed=False,main_epoch_changed=False,tilemap_epoch_changed=False))]:
    with self.subTest(address=a,key=key),self.assertRaisesRegex(ValueError,'not an executed boundary'):v.compose_selected(self.raw,**{key:{a:value}})
 def test_47_other_root_effect_key_rejected_for_selected_case(self):
  with self.assertRaisesRegex(ValueError,'not an executed boundary'):v.compose_selected(self.raw,case='shockwave',opaque_writes={0x08147470:[]})
 def test_48_unknown_effect_key_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0x08000000:[]})
 def test_49_bool_effect_key_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={True:[]})
 def test_50_closed_epoch_event_fields(self):
  for events in ({'extra':True},dict(task_epoch_changed=0,main_epoch_changed=False,tilemap_epoch_changed=False)):
   with self.assertRaises(ValueError):v.compose_selected(self.raw,case='shockwave',epoch_events={0:events})
 def test_51_closed_memory_fields_and_write_width(self):
  for fields,writes in [([[True,1]],[]),([],[(1,True,0)]),([],[(1,3,0)]),([],[(1,1,256)])]:
   with self.assertRaises(ValueError):v.preservation_contract(fields,writes)
 def test_52_full_future_projection_required(self):
  first=v._case(self.raw,'shockwave')
  with self.assertRaises(ValueError):v._case(self.raw,'shockwave',projections=[[]for _ in first['projections']])
 def test_53_closed_trace_language(self):
  with self.assertRaises(ValueError):v.project([('trust',0)],0)
 def test_54_no_manual_branch_choice(self):
  m=v.Machine(self.raw,0x08071FCC,instructions=v.INS)
  with self.assertRaises(ValueError):m.step(True)
 def test_55_all_boolean_claim_promotion_rejected(self):
  for key,value in v.CLAIMS.items():
   if value is False:
    with self.subTest(claim=key):self.reject_review(lambda x:x['claims'].update({key:True}))
 def test_56_evidence_discriminator_closed(self):
  for h in v.HITS:
   self.reject_evidence(h,lambda e:e.update(extra=True));self.reject_evidence(h,lambda e:e['root'].update(kind='guessed'))
 def test_57_evidence_geometry_cannot_widen(self):
  for h in v.HITS:self.reject_evidence(h,lambda e:e['instruction_window'].update(size=100))
 def test_58_no_padding_or_other_hits_classified(self):
  for h in(0x0805D12F,0x08428EA1,0x083E239B,0x083E24C3,0x083E2563,0x083E258F,0x091494EA):
   with self.subTest(hit=h),self.assertRaises(ValueError):v.evidence_template(h)
 def test_59_proof_is_aggregated(self):
  for p in self.proof['cases']:
   self.assertEqual(sum(b['occurrences']for b in p['conditional_call_catalog']),p['boundary_count']);self.assertLess(len(p['conditional_call_catalog']),p['boundary_count']);self.assertNotIn('trace',p)
 def test_60_minimum_bounded_scope(self):
  self.assertEqual(v.HITS,(0x080B0113,0x0814777B));self.assertEqual(v.TYPE_CATEGORY,'code');self.assertEqual((len(v.FIXED_GEOMETRY),sum(n for a,n in v.FIXED_GEOMETRY)),(64,2144))
 def test_61_json_review_roundtrip_is_exact(self):
  import json
  r=json.loads(json.dumps(self.review));self.assertTrue(all(type(k)is str for k in r['roots']));self.check(review=r)
 def test_62_invalid_projection_address_rejected(self):
  for fields in ([[[-1,1]]],[[[0xFFFFFFFF,2]]]):
   with self.assertRaises(ValueError):v.preservation_contract(fields[0],[])
 def test_63_actual_next_delay_operand_rejected(self):
  with self.assertRaises(ValueError):v.parse_script(Mutation(self.raw,0x081B100E))
if __name__=='__main__':unittest.main()
