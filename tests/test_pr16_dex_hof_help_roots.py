"""新Help2件だけの根・最小byte型・producer・live・公開source反証。"""
import copy,json,unittest
from unittest import mock
import pr16_dex_hof_help_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,base,address):self.base,self.address=base,address
 def __len__(self):return len(self.base)
 def __getitem__(self,s):
  b=bytearray(self.base[s]);a=self.address-0x08000000
  if s.start<=a<s.stop:b[a-s.start]^=1
  return bytes(b)

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=v.identity(v.chunk(raw,obj['address'],obj['size']))['sha256']
  for x in obj.values():reseal(x,raw)
 elif isinstance(obj,list):
  for x in obj:reseal(x,raw)

class HelpRootsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit in-memory FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
  cls.proof=v.compose_selected(cls.raw)
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,fn):
  r=copy.deepcopy(self.review);fn(r)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(review=r)
 def reject_evidence(self,fn):
  e=v.evidence_template(v.HITS[0]);fn(e)
  with self.assertRaises((ValueError,TypeError,KeyError)):v.witness_geometry(e)
 def test_01_only_two_four_byte_data_windows(self):
  before=copy.deepcopy(self.inherited);rows,p=self.check()
  self.assertEqual([(x.start,x.end,x.kind)for x in rows],[(h,h+4,v.KIND)for h in v.HITS])
  self.assertEqual(p['count'],2);self.assertEqual(v.TYPE_CATEGORY,'data');self.assertEqual(before,self.inherited)
 def test_02_all_five_case_roots_composed(self):
  self.assertEqual([(c['context'],c['topic'])for c in self.proof['cases']],list(v.CASES));self.assertEqual(self.proof['total_frames'],37)
  for c in self.proof['cases']:
   sites={r['address']:r['count']for r in c['executed_root_sites']}
   for k in('context_store','installed_hook','hook_target','main_topic_producer','controller_initializer','selected_index_read','topic_store','submenu_pointer_read'):self.assertGreater(sites[v.ROOT[k]],0)
 def test_03_real_video_state_stores(self):
  for c in self.proof['cases']:
   self.assertEqual(c['help_state_after_frames'][:5],[1,2,3,4,5])
   actual=[e['value']for e in c['actual_producer_events']if e['role']=='actual_producer_store'and e['address']==v.VIDEO+21]
   self.assertEqual(actual,list(range(1,6)))
 def test_04_context_and_topic_not_host_injected(self):
  for c in self.proof['cases']:
   events=c['actual_producer_events']
   self.assertEqual([e['value']for e in events if e['site']==v.ROOT['context_store']],[c['context']])
   self.assertEqual([e['value']for e in events if e['site']==v.ROOT['topic_store']],[c['topic']])
   for r in c['conditional_call_catalog']:
    for o in r['conditional_outputs']:self.assertIn(o['address'],(v.MAIN+46,v.MAIN+48))
 def test_05_cursor_increment_is_actual_for_terms(self):
  for c in self.proof['cases']:
   writes=[e for e in c['actual_producer_events']if e['site']==v.ROOT['down_cursor_writer']]
   self.assertEqual([e['value']for e in writes],[1]if c['topic']==2 else[])
 def test_06_generated_list_A_read_selects_topic(self):
  for c in self.proof['cases']:
   e=next(e for e in c['actual_producer_events']if e['site']==v.ROOT['selected_index_read'])
   self.assertEqual(e['value'],c['topic']);self.assertEqual(e['address'],v.ITEMS+4+8*(c['topic']-1))
 def test_07_all_id_and_eos_bytes_consumed(self):
  cells=set()
  for c,r in zip(self.proof['cases'],v.LISTS):
   self.assertEqual(c['consumed_ranges'],[dict(address=r['address'],size=r['size'])]);self.assertEqual(c['byte_read_count'],2*r['size']-1)
   cells.update(range(r['address'],r['address']+r['size']))
  self.assertEqual(len(cells),20);self.assertTrue(all(set(range(h,h+4))<=cells for h in v.HITS))
 def test_08_actual_filter_not_arbitrary_false(self):
  self.assertIn(0x0812BF84,v.INS);self.assertNotIn(0x0812BF84,v.EXTERNAL.values());self.assertIn(0x0812BF58,v.INS)
  self.assertIn(0x0812BEB6,v.INS);self.assertIn(0x0812BEBE,v.INS)
 def test_09_opaque_outputs_separate_from_saved_memory(self):
  self.assertTrue(self.proof['nonlive_ram_erased_at_each_boundary'])
  for c in self.proof['cases']:
   for b in c['conditional_call_catalog']:
    self.assertFalse(b['effects_discharged']);self.assertTrue(b['normal_abi_return_required'])
    saved={a for r in b['required_fields']for a in range(r['address'],r['address']+r['size'])}
    produced={a for r in b['produced_memory_ranges']for a in range(r['address'],r['address']+r['size'])}
    self.assertFalse(saved&produced)
 def test_10_context_clobber_rejected(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0x0813C0DE:[(v.CONTEXT,2,0)]})
 def test_11_topic_clobber_rejected(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0x0812BDB4:[(v.HELP+1,1,0)]})
 def test_12_generated_list_clobber_rejected(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0x0813CDBA:[(v.ITEMS+4,4,0)]})
 def test_13_saved_stack_clobber_rejected(self):
  b=next(b for b in self.proof['cases'][0]['conditional_call_catalog']if b['site']==0x0813C0DE)
  a=next(r['address']for r in b['required_fields']if 0x03006000<=r['address']<0x03007000)
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={b['site']:[(a,1,0)]})
 def test_14_between_frame_context_clobber_rejected(self):
  with self.assertRaisesRegex(ValueError,'future-live'):v.compose_selected(self.raw,opaque_writes={0:[(v.CONTEXT,2,0)]})
 def test_15_nonlive_clobber_allowed(self):
  self.assertTrue(v.compose_selected(self.raw,opaque_writes={0x0813C0DE:[(0x02030000,4,1234)]})['all_hit_bytes_consumed'])
 def test_16_declared_input_outputs_not_preserved(self):
  p=v.compose_selected(self.raw,opaque_writes={0:[(v.MAIN+46,2,65535),(v.MAIN+48,2,65535)]});self.assertTrue(p['all_hit_bytes_consumed'])
 def test_17_valid_resource_epochs_explicit(self):
  for key in('help_globals_reinitialized','save_identity_changed','video_resources_invalidated'):
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'epochs'):v.compose_selected(self.raw,resource_events={0x0813C0DE:{key:True}})
 def test_18_normal_return_required(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,normal_returns=False)
 def test_19_resource_validity_required(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,resources_valid=False)
 def test_20_flag_profile_closed(self):
  for val in(1,True,None):
   with self.subTest(value=val),self.assertRaises(ValueError):v.compose_selected(self.raw,flag_result=val)
 def test_21_initial_environment_closed(self):
  x=list(v.INITIAL_FIELDS);x[0]=(v.VIDEO+21,1,5)
  with self.assertRaises(ValueError):v.compose_selected(self.raw,initial_fields=x)
 def test_22_input_schedule_closed(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,input_schedule=[(0,0),(0,0)])
 def test_23_case_domain_closed(self):
  for c,t in((6,0),(6,True),(12,2),(True,1)):
   with self.subTest(context=c,topic=t),self.assertRaises(ValueError):v._case(self.raw,c,t)
 def test_24_every_instruction_halfword_semantically_bound(self):
  for a in sorted({a for i in v.INS.values()for a in range(i.address,i.address+i.size,2)}):
   with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_25_all_literal_words_bound(self):
  for a in v.WORDS:
   with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_26_all_selected_list_and_table_bytes_bound(self):
  for r in v.LISTS:
   for a in[*range(r['address'],r['address']+r['size']),*range(r['table_cell'],r['table_cell']+4)]:
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_27_resealed_producer_mutations_rejected(self):
  for a in(v.ROOT['context_store'],v.ROOT['installed_hook'],v.ROOT['hook_target'],v.ROOT['down_cursor_writer'],v.ROOT['topic_store'],v.ROOT['submenu_pointer_read'],*v.HITS):
   raw=Mutation(self.raw,a);review=copy.deepcopy(self.review);inherited=copy.deepcopy(self.inherited);reseal(review,raw);reseal(inherited,raw)
   with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,inherited=inherited,review=review)
 def test_28_all_source_whole_identity_mutations_rejected(self):
  for k,b in self.sources.items():
   sources=dict(self.sources);sources[k]=b+b'\n'
   with self.subTest(source=k),self.assertRaises(ValueError):self.check(sources=sources)
 def test_29_missing_source_rejected(self):
  sources=dict(self.sources);sources.pop(next(iter(sources)))
  with self.assertRaises(ValueError):self.check(sources=sources)
 def test_30_extra_source_rejected(self):
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_31_public_enum_id_lists_independently_bound(self):v.sources_bind(self.review,self.sources,self.raw)
 def test_32_review_closed_schema(self):self.reject_review(lambda r:r.update(extra=1))
 def test_33_review_schema_bool_rejected(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_34_review_window_removal(self):self.reject_review(lambda r:r['windows'].pop())
 def test_35_review_window_reseal(self):self.reject_review(lambda r:r['windows'][0].update(sha256='0'*64))
 def test_36_review_window_extra_key(self):self.reject_review(lambda r:r['windows'][0].update(extra=True))
 def test_37_root_promotion_rejected(self):self.reject_review(lambda r:r['root'].update(extra=True))
 def test_38_source_binding_rewrite_rejected(self):self.reject_review(lambda r:r['source_bindings']['pret-main.c'].update(size=0))
 def test_39_public_list_change_rejected(self):self.reject_review(lambda r:r['id_lists'][0]['symbols'].pop())
 def test_40_natural_play_claim_rejected(self):self.reject_review(lambda r:r['claims'].update(full_story_reachability_claimed=True))
 def test_41_contract_drop_rejected(self):self.reject_review(lambda r:r['input_contract'].pop('input'))
 def test_42_diagnostic_current_conflation_rejected(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_43_inherited_current_identity_required(self):
  i=copy.deepcopy(self.inherited);i['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_44_duplicate_prior_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(i['hits'][0]))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_45_prior_hit_must_remain_unknown_owner_external(self):
  for key,value in[('accepted',True),('owner_candidates',['owner']),('size',True),('kind','POINTER'),('classification','DATA')]:
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][key]=value;r['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_46_review_original_row_exact(self):self.reject_review(lambda r:r['hits'][0].update(reason='other'))
 def test_47_current_whole_gate_rejects_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),self.assertRaises(ValueError):v.regions(*FIXTURE)
 def test_48_minimum_evidence_geometry(self):
  for h in v.HITS:self.assertEqual(v.witness_geometry(v.evidence_template(h)),(h,4))
 def test_49_whole_list_classification_rejected(self):self.reject_evidence(lambda e:e['classified_window'].update(size=20))
 def test_50_pointer_interpretation_rejected(self):self.reject_evidence(lambda e:e.update(source_pointer_interpretation=True))
 def test_51_unknown_natural_root_not_promoted(self):self.reject_evidence(lambda e:e.update(natural_screen_context_invocation_proven=True))
 def test_52_runtime_execution_not_promoted(self):self.reject_evidence(lambda e:e.update(actual_runtime_execution_observed=True))
 def test_53_donor_lease_not_promoted(self):self.reject_evidence(lambda e:e.update(donor_leased=True))
 def test_54_padding_not_promoted(self):self.reject_evidence(lambda e:e.update(padding_classified=True))
 def test_55_other_candidates_not_typed(self):
  self.assertEqual(v.HITS,(0x0841B41A,0x0841B44C))
  for h in(0x08428EA1,0x083E239B,0x0812DAEF):
   with self.assertRaises(ValueError):v.evidence_template(h)
 def test_56_windows_only_minimum_reads(self):
  self.assertEqual(sum(r['size']for r in v.FIXED_WINDOWS),1838);self.assertEqual(len(v.FIXED_WINDOWS),101)
 def test_57_all_boundary_fields_concrete(self):
  for c in self.proof['cases']:
   for b in c['conditional_call_catalog']:
    for x in b['required_fields']+b['produced_memory_ranges']:self.assertIs(type(x['address']),int);self.assertIs(type(x['size']),int);self.assertGreater(x['size'],0)
 def test_58_hook_flag_provenance_rejected(self):
  m=v.Machine(self.raw,0x0813C0B4,instructions=v.INS)
  with self.assertRaisesRegex(ValueError,'flag provenance'):m.step()
 def test_59_incomplete_projection_rejected(self):
  with self.assertRaisesRegex(ValueError,'projected'):v.future_live([],1)
 def test_60_closed_trace_events(self):
  with self.assertRaisesRegex(ValueError,'closed help effect trace'):v.future_live([('unknown',0,0)],0)
 def test_61_adrpc_uses_aligned_pc_plus_four(self):
  m=v.Machine(self.raw,0x092CFED0,instructions=v.INS);m.step()
  self.assertEqual(m.reg[1],0x092CFEDC);self.assertEqual(m.pc,0x092CFED2)
 def test_62_ldmia_reads_three_words_and_writes_back(self):
  mem={}
  for j,x in enumerate((111,222,333)):v.rt.setmem(mem,0x02024000+4*j,4,x)
  m=v.Machine(self.raw,0x0813CD96,{0:0x02024000},mem,instructions=v.INS);m.step()
  self.assertEqual(m.reg[5:8],[111,222,333]);self.assertEqual(m.reg[0],0x0202400C);self.assertEqual(m.pc,0x0813CD98)
 def test_63_hook_lsl_negative_tests_bit_one(self):
  for value,target in((0,0x092CFED0),(1,0x092CFED0),(2,0x092CFEE4),(3,0x092CFEE4)):
   m=v.Machine(self.raw,0x092CFECC,{3:value},instructions=v.INS);m.step();m.step()
   self.assertEqual(m.pc,target)
 def test_64_hook_cmp_flags_survive_literal_bx(self):
  for value,target in((0,0x0813C0BE),(1,0x0813C0B6)):
   m=v.Machine(self.raw,0x092CFEDE,{0:value},instructions=v.INS)
   for _ in range(4):m.step()
   self.assertEqual(m.pc,target)
 def test_65_removing_live_projection_cannot_fake_producer(self):
  first=v._case(self.raw,6,1)
  with self.assertRaises(ValueError):v._case(self.raw,6,1,[[]for _ in first['boundaries']])
