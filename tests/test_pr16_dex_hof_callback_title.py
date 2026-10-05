"""新タイトルconsumerだけの反証。原本I/Oや旧suiteをimport時に実行しない。"""
import copy,hashlib,unittest
import pr16_dex_hof_callback_title as v
FIXTURE=None

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():
   a=obj['address']-0x08000000;obj['sha256']=hashlib.sha256(raw[a:a+obj['size']]).hexdigest()
  for val in obj.values():reseal(val,raw)
 elif isinstance(obj,list):
  for val in obj:reseal(val,raw)

class TitleCallbackTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit fixture injection required')
  self.raw,self.inherited,self.review,self.sources=FIXTURE
 def check(self,review=None,raw=None,inherited=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject(self,edit):
  review=copy.deepcopy(self.review);edit(review)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(review=review)
 def mutate(self,address,value,n=2,edit=None):
  raw=bytearray(self.raw);a=address-0x08000000;value=value.to_bytes(n,'little');self.assertNotEqual(raw[a:a+n],value);raw[a:a+n]=value;raw=bytes(raw)
  review=copy.deepcopy(self.review);inherited=copy.deepcopy(self.inherited);reseal(review,raw);reseal(inherited,raw)
  if edit:edit(review)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(review=review,raw=raw,inherited=inherited)
 def test_01_single_minimal_code_window(self):
  regions,proof=self.check();self.assertEqual((regions[0].start,regions[0].end),(0x08162BFC,0x08162C02));self.assertEqual(proof['count'],1);self.assertFalse(proof['full_story_reachability_claimed']);self.assertTrue(proof['berry_state_producer_and_selector_verified'])
 def test_02_same_existing_geometry(self):
  region=self.check()[0][0];self.assertEqual(v.geometry(region.evidence),(0x08162BFC,6))
 def test_03_current_wrapper_mandatory(self):
  if v.identity(self.raw)==v.CANDIDATE:self.assertEqual(v.regions(self.raw,self.inherited,self.review,self.sources)[1]['count'],1)
  else:
   with self.assertRaises(ValueError):v.regions(self.raw,self.inherited,self.review,self.sources)
 def test_04_inherited_candidate_not_self_attestation(self):
  inherited=copy.deepcopy(self.inherited);inherited['candidate']=v.identity(self.raw)
  if v.identity(self.raw)!=v.CANDIDATE:
   with self.assertRaises(ValueError):v.regions(self.raw,inherited,self.review,self.sources)
 def test_05_unknown_exact_identity(self):
  inherited=copy.deepcopy(self.inherited);next(h for h in inherited['hits']if h['address']==v.HITS[0])['accepted']=True
  with self.assertRaises(ValueError):self.check(inherited=inherited)
 def test_06_hit_target_not_rewritten(self):self.reject(lambda j:j['rows'][0]['hit'].update(target=0))
 def test_07_no_second_unknown(self):self.reject(lambda j:j['rows'].append(copy.deepcopy(j['rows'][0])))
 def test_08_actual_reset_root(self):self.reject(lambda j:j['rows'][0]['root'].update(kind='symbol_only'))
 def test_09_no_missing_segment(self):self.reject(lambda j:j['rows'][0]['paths'].pop(0))
 def test_10_no_skipped_instruction(self):self.reject(lambda j:j['rows'][0]['paths'][0]['instructions'].pop(6))
 def test_11_no_instruction_extent_inflation(self):self.reject(lambda j:j['rows'][0]['instruction_window'].update(size=8))
 def test_12_no_literal_pool(self):self.reject(lambda j:j['rows'][0].update(literal_pool_included=True))
 def test_13_no_whole_function(self):self.reject(lambda j:j['rows'][0].update(whole_function_range_classified=True))
 def test_14_source_change(self):
  src=dict(self.sources);src['pret-intro.c']+=b'\n'
  with self.assertRaises(ValueError):self.check(sources=src)
 def test_15_source_role_missing(self):self.reject(lambda j:j['source_bindings'].pop('pret-berry_fix_program.c'))
 def test_16_protected_semantic_read_missing(self):self.reject(lambda j:j.update(consumer_windows=[w for w in j['consumer_windows']if w['address']!=0x08078430]))
 def test_17_outer_title_callback_literal(self):self.mutate(0x080EEB3C,0x080780B1,4)
 def test_18_outer_title_callback_argument(self):self.mutate(0x080EEB2E,0x4903)
 def test_19_intro_heap_constructor_size(self):self.mutate(0x080ED998,0x28B8,4)
 def test_20_intro_heap_field_wrong(self):self.mutate(0x080ED9A4,0x6041)
 def test_21_intro_word_arg_slot(self):self.mutate(0x080ED988,0x2101)
 def test_22_intro_word_arg_store_stride(self):self.mutate(0x08076E98,0x0049)
 def test_23_intro_word_arg_read_stride(self):self.mutate(0x08076ED2,0x0052)
 def test_24_intro_roundtrip_halfword_shift(self):self.mutate(0x08076EE8,0x03C9)
 def test_25_intro_skip_target(self):self.mutate(0x080ED9E8,0x080EEAED,4)
 def test_26_intro_skip_uses_other_allocation(self):self.mutate(0x080ED9D6,0x1C28)
 def test_27_intro_exit_frees_same_allocation(self):self.mutate(0x080EEB1C,0x1C28)
 def test_28_title_task_data_same_stride(self):self.mutate(0x080783C6,0x0049)
 def test_29_scene_producer_wrong_value(self):self.mutate(0x080783FA,0x2104)
 def test_30_scene_state_offset(self):self.mutate(0x0807842E,0x8082)
 def test_31_scene_number_offset(self):self.mutate(0x08078430,0x8041)
 def test_32_scene_read_offset(self):self.mutate(0x0807840E,0x2202)
 def test_33_scene_index_scale(self):self.mutate(0x08078412,0x00C9)
 def test_34_scene_table_slot_value(self):self.mutate(0x08386914,0x0807875D,4)
 def test_35_berry_constructor_zero_origin(self):self.mutate(0x08162A76,0x2401)
 def test_36_berry_constructor_zero_clobber(self):self.mutate(0x08162AAA,0x2401)
 def test_37_berry_constructor_other_task_field(self):self.mutate(0x08162AC4,0x81CC)
 def test_38_berry_task_selector_other_field(self):self.mutate(0x08162B12,0x2102)
 def test_39_berry_state0_wrong_successor(self):self.mutate(0x08162B62,0x2002)
 def test_40_berry_state1_wrong_successor(self):self.mutate(0x08162B7A,0x2003)
 def test_41_berry_state2_wrong_successor(self):self.mutate(0x08162B98,0x2003)
 def test_42_berry_state4_wrong_successor(self):self.mutate(0x08162BC0,0x2006)
 def test_43_berry_state4_wrong_timer_origin(self):self.mutate(0x08162BB6,0x2401)
 def test_44_berry_state_store_other_field(self):self.mutate(0x08162CB4,0x8068)
 def test_45_berry_state_store_other_task_register(self):self.mutate(0x08162BA0,0x2500)
 def test_46_berry_selector_wrong_index(self):self.reject(lambda j:j['rows'][0]['berry_switch'].update(index=4))
 def test_47_berry_selector_wrong_bound(self):self.mutate(0x08162B16,0x2809)
 def test_48_berry_producer_slot_missing(self):self.mutate(0x08162B40,0x08162B84,4)
 def test_49_berry_counter_halfword_signedness(self):self.mutate(0x08162BF4,0x0C00)
 def test_50_complete_instruction_not_half_BL(self):self.reject(lambda j:next(p for p in j['rows'][0]['paths']if p['name']=='berry_consumer')['instructions'][-2].update(size=2))
 def test_51_literal_window_not_typed(self):self.reject(lambda j:j['rows'][0]['instruction_window'].update(address=0x08162C28))
 def test_52_actual_scheduler_calls(self):
  for a in(0x080ED8D2,0x08078336,0x08162AF6):
   with self.subTest(address=a):self.mutate(a,0x2000)
 def test_53_each_new_semantic_halfword_resealed(self):
  reads={}
  for f in(v.task_word_roundtrip,v.scene3_state,v.title_init_states,v.schedulers,v.berry_state_protocol):reads.update(f(self.raw))
  count=0
  for a,n in sorted(reads.items()):
   for at in range(a,a+n,2):
    original=int.from_bytes(self.raw[at-0x08000000:at-0x08000000+2],'little')
    with self.subTest(address=at):self.mutate(at,original^1)
    count+=1
  self.assertGreater(count,280)
 def test_54_output_has_all_protected_windows(self):
  e=self.check()[0][0].evidence;self.assertTrue(e['protected_windows']);self.assertFalse(e['literal_pool_included'])
 def test_55_title_init_state0_required(self):self.mutate(0x080782BA,0x3002)
 def test_56_main_callback_root_writer_still_bound(self):self.mutate(0x08000546,0x6088)

 def test_57_final_consumer_literal_protected(self):self.reject(lambda j:j.update(consumer_windows=[w for w in j['consumer_windows']if w['address']!=0x08162C28]))
 def test_58_path_instruction_protected(self):self.reject(lambda j:j.update(consumer_windows=[w for w in j['consumer_windows']if w['address']!=0x08162A80]))
 def test_59_common_dependency_window_protected(self):self.reject(lambda j:j['consumer_windows'].pop(0))

 def test_60_protected_union_keeps_every_dependency(self):
  windows=self.check()[0][0].evidence['protected_windows']
  for original in self.review['consumer_windows']+self.review['consumer_literals']:
   self.assertTrue(any(w['address']<=original['address'] and original['address']+original['size']<=w['address']+w['size'] for w in windows))
  self.assertTrue(all(a['address']+a['size']<b['address']for a,b in zip(windows,windows[1:])))
