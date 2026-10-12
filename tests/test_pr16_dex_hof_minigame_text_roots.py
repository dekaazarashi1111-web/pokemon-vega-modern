"""minigame実special/task登録、完全text読取と最小3窓の反証。外部I/Oなし。"""
import copy,hashlib,json,unittest
from unittest.mock import patch
import pr16_dex_hof_minigame_text_roots as v
FIXTURE=None
class Overlay:
 def __init__(self,raw,a,n,value):self.raw=raw;self.a=a-0x08000000;self.value=value.to_bytes(n,'little')
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
class MinigameTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit bounded in-memory FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE;cls.regions,cls.proof=v._regions(*FIXTURE)
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,edit):
  r=copy.deepcopy(self.review);edit(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def reject_evidence(self,edit):
  for h in v.HITS:
   e=v.evidence_template(h);edit(e)
   with self.subTest(hit=h),self.assertRaises((ValueError,KeyError,TypeError)):v.witness_geometry(e)
 def mutate(self,a,n,value):
  raw=Overlay(self.raw,a,n,value);r,i=copy.deepcopy(self.review),copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(raw=raw,inherited=i,review=r)
 def test_01_exact_three_minimum_hits(self):self.assertEqual([(r.start,r.end,r.kind)for r in self.regions],[(h,h+4,v.KIND)for h in v.HITS])
 def test_02_all_five_complete_texts(self):
  p=self.proof['composition'];self.assertEqual((p['complete_consumed_bytes'],p['boundary_count']),(64,171));self.assertEqual([r['bytes_consumed']for r in p['cases']],[41,23]);self.assertTrue(p['includes_all_five_eos'])
 def test_03_both_real_task_constructors_return(self):
  for r in self.proof['composition']['cases']:self.assertTrue(r['constructor_returned']);self.assertEqual((r['registered_task_state'],r['window_id']),(1,0))
 def test_04_actual_memset_and_nonlive_replay(self):
  p=self.proof['composition'];self.assertTrue(p['actual_task_registration_and_zero_writer']);self.assertTrue(p['nonlive_ram_erased_at_each_boundary'])
 def test_05_current_not_diagnostic_gate(self):
  with patch.object(v,'identity',return_value=v.DIAGNOSTIC),patch.object(v,'_regions')as accept:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   accept.assert_not_called()
 def test_06_current_wrapper_gate(self):
  with patch.object(v,'identity',return_value=v.CANDIDATE),patch.object(v,'_regions',return_value='sentinel')as accept:self.assertEqual(v.regions(*FIXTURE),'sentinel');accept.assert_called_once()
 def test_07_wrong_candidate(self):
  i=copy.deepcopy(self.inherited);i['candidate']['sha256']='0'*64
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_08_accepted_hit_rejected(self):
  i,r=copy.deepcopy(self.inherited),copy.deepcopy(self.review);i['hits'][0]['accepted']=r['hits'][0]['accepted']=True
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_09_owner_hit_rejected(self):
  i,r=copy.deepcopy(self.inherited),copy.deepcopy(self.review);i['hits'][0]['owner_candidates']=r['hits'][0]['owner_candidates']=['fake']
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_10_duplicate_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(i['hits'][0])
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_11_missing_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].pop()
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_12_hit_order_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].reverse()
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_13_every_semantic_halfword_encoder(self):
  count=0
  for i in v.INS.values():
   self.assertEqual(v.chunk(self.raw,i.address,i.size),v.encoded(i))
   for offset in range(0,i.size,2):
    a=i.address+offset;raw=Overlay(self.raw,a,2,int.from_bytes(v.chunk(self.raw,a,2),'little')^1)
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)
    count+=1
  self.assertGreater(count,800)
 def test_14_every_literal_reseal_rejected(self):
  for a,value in v.LITERALS.items():
   with self.subTest(address=a):self.mutate(a,4,value^1)
 def test_15_all_registered_pointers_reseal_rejected(self):
  for a,value in v.POINTERS.items():
   with self.subTest(address=a):self.mutate(a,4,value^1)
 def test_16_all_text_bytes_reseal_rejected(self):
  for row in v.TEXTS:
   for off in range(row['size']):
    a=row['address']+off
    with self.subTest(address=a):self.mutate(a,1,v.chunk(self.raw,a,1)[0]^1)
 def test_17_every_protected_byte_rejected(self):
  for row in v.FIXED_WINDOWS:
   for off in range(row['size']):
    a=row['address']+off;raw=Overlay(self.raw,a,1,v.chunk(self.raw,a,1)[0]^1)
    with self.subTest(address=a),self.assertRaises(ValueError):v.d.signed(raw,row)
 def test_18_each_eos_rejected(self):
  for row in v.TEXTS:
   with self.subTest(text=row['address']):self.mutate(row['address']+row['size']-1,1,0)
 def test_19_title_pointer_not_table_approximation(self):self.mutate(0x0814BC80,4,0x083E1F1B)
 def test_20_first_jump_table_pointer(self):self.mutate(0x08437B58,4,0x083E1F29)
 def test_21_second_jump_table_pointer(self):self.mutate(0x08437B5C,4,0x083E1F33)
 def test_22_dodrio_table_pointer(self):self.mutate(0x08443224,4,0x083E2017)
 def test_23_dodrio_second_table_pointer(self):self.mutate(0x08443228,4,0x083E2021)
 def test_24_source_full_identity(self):
  for key in v.SOURCE_IDS:
   s=dict(self.sources);s[key]+=b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_25_source_missing(self):
  s=dict(self.sources);s.pop('pret-task.c')
  with self.assertRaises(ValueError):self.check(sources=s)
 def test_26_source_manifest_rejected(self):self.reject_review(lambda r:r['source_bindings']['pret-task.c'].update(sha256='0'*64))
 def test_27_review_extra_key(self):self.reject_review(lambda r:r.update(trusted=True))
 def test_28_review_window_missing(self):self.reject_review(lambda r:r['windows'].pop())
 def test_29_review_window_extra(self):self.reject_review(lambda r:r['windows'].append(r['windows'][0]))
 def test_30_review_window_reordered(self):self.reject_review(lambda r:r['windows'].reverse())
 def test_31_root_changed(self):self.reject_review(lambda r:r['root']['jump'].update(special=404))
 def test_32_consumer_changed(self):self.reject_review(lambda r:r['root'].update(byte_read=0x08008900))
 def test_33_no_native_claim(self):self.reject_review(lambda r:r['claims'].update(actual_runtime_execution_observed=True))
 def test_34_no_natural_play_claim(self):self.reject_review(lambda r:r['claims'].update(full_story_reachability_claimed=True))
 def test_35_no_lifetime_claim(self):self.reject_review(lambda r:r['claims'].update(universal_heap_or_irq_lifetime_proven=True))
 def test_36_no_indirect_completeness(self):self.reject_review(lambda r:r['claims'].update(indirect_reference_completeness_claimed=True))
 def test_37_no_donor_claim(self):self.reject_review(lambda r:r['claims'].update(donor_eligible=True))
 def test_38_no_opaque_proof_claim(self):self.reject_review(lambda r:r['claims'].update(opaque_callee_effects_proven=True))
 def test_39_no_padding_claim(self):self.reject_review(lambda r:r['claims'].update(padding_classified=True))
 def test_40_no_source_pointer_claim(self):self.reject_review(lambda r:r['claims'].update(source_pointer_interpretation=True))
 def test_41_no_whole_table_classification(self):self.reject_evidence(lambda e:e['classified_window'].update(size=64))
 def test_42_no_extra_evidence(self):self.reject_evidence(lambda e:e.update(trusted=True))
 def test_43_no_missing_root(self):self.reject_evidence(lambda e:e.update(root_verified=False))
 def test_44_no_partial_text(self):self.reject_evidence(lambda e:e.update(all_hit_bytes_consumed=False))
 def test_45_no_partial_eos(self):self.reject_evidence(lambda e:e.update(includes_complete_eos=False))
 def test_46_exact_geometry(self):self.assertEqual([v.witness_geometry(v.evidence_template(h))for h in v.HITS],[(h,4)for h in v.HITS])
 def test_47_other_hits_remain_unknown(self):
  for h in(0x083DF94F,0x083E112C,0x083E239B,0x083DDEFC,0x091492CA):
   with self.subTest(hit=h),self.assertRaises(ValueError):v.evidence_template(h)
 def test_48_exact_condition_contract(self):self.reject_review(lambda r:r['input_contract'].pop('window'))
 def test_49_compose_contract_not_arbitrary(self):
  c=copy.deepcopy(v.CONTRACT);c['entry']='anything'
  with self.assertRaises(ValueError):v._compose_case(self.raw,405,contract=c)
 def test_50_each_future_live_field_blocks_write(self):
  count=0
  for row in self.proof['composition']['conditional_call_groups']:
   fields=[(x['address'],x['size'])for x in row['required_fields']]
   for a,n in fields:
    with self.subTest(site=row['site'],address=a),self.assertRaises(ValueError):v.preserve(fields,[(a,n,0)])
    count+=1
  self.assertGreater(count,100)
 def test_51_nonlive_write_allowed(self):
  for row in self.proof['composition']['conditional_call_groups']:self.assertTrue(v.preserve([(x['address'],x['size'])for x in row['required_fields']],[(0x0203FFFC,4,1)]))
 def test_52_actual_nonlive_write_replay(self):self.assertEqual(v.compose_selected(self.raw,opaque_writes={0x0814BB0C:[(0x0203FFFC,4,123)]})['complete_consumed_bytes'],64)
 def test_53_actual_live_corruption_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0x0814BB0C:[(v.TASKS,4,0)]})
 def test_54_task_epoch_reinitialization_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x0814BB0C:dict(task_reinitialized=True)})
 def test_55_window_invalidated_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x0814BBA8:dict(window_invalidated=True)})
 def test_56_false_bool_not_zero(self):
  for k in('task_reinitialized','window_invalidated'):
   with self.subTest(effect=k),self.assertRaises(ValueError):v.preserve([],**{k:0})
 def test_57_unexecuted_effect_site_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0x08000000:[(0x0203FFFC,4,0)]})
 def test_58_unknown_epoch_effect_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x0814BB0C:dict(free_anything=True)})
 def test_59_outputs_separate_from_prior_live(self):
  for r in self.proof['composition']['conditional_call_groups']:
   old={a for x in r['required_fields']for a in range(x['address'],x['address']+x['size'])};new={a for x in r['produced_memory_ranges']for a in range(x['address'],x['address']+x['size'])};self.assertFalse(old&new);self.assertFalse(r['effects_discharged'])
 def test_60_source_numeric_records_not_save_acceptance(self):self.assertIn('not read from a save file',v.CONTRACT['records']);self.assertFalse(self.proof['actual_runtime_execution_observed'])
 def test_61_public_proof_is_bounded(self):self.assertLess(len(json.dumps(self.proof)),200000)
 def test_62_invalid_special(self):
  for special in(404,421,True):
   with self.subTest(special=special),self.assertRaises(ValueError):v._compose_case(self.raw,special)
 def test_63_projection_read_before_write(self):
  self.assertEqual(v.future_live([('write',100,4),('boundary',0,0),('read',100,2),('write',102,2),('read',102,2)],1),[[[100,2]]])
 def test_64_review_json_roundtrip(self):self.assertEqual(len(v._regions(self.raw,self.inherited,json.loads(json.dumps(self.review)),self.sources)[0]),3)
 def test_65_task_root_calls_have_exact_encoder(self):
  for a in(0x0814BAC0,0x0814BAC8,0x08156994,0x0815699C,0x0814BB14,0x081569EA):self.assertIn(a,v.INS);self.assertEqual(v.INS[a].kind,'call')
 def test_66_font_entry_condition_explicit(self):
  self.assertIn('03003DD0 already contains083E30E8',v.CONTRACT['font']);self.assertIn('initialization success are not proved',v.CONTRACT['font'])
 def test_67_font_condition_cannot_be_omitted(self):self.reject_review(lambda r:r['input_contract'].pop('font'))
 def test_68_text_control_entry_explicit(self):
  for a in('0300315C','0300315E','03003E90'):self.assertIn(a,v.CONTRACT['text_state'])
  self.assertNotIn(0x020379F3,[a for a,n,value in v.INITIAL_FIELDS])
 def test_69_text_control_condition_cannot_be_omitted(self):self.reject_review(lambda r:r['input_contract'].pop('text_state'))
 def test_70_missing_font_resource_blocks_actual_read(self):
  fields=tuple(r for r in v.INITIAL_FIELDS if r[0]!=0x03003DD0)
  with patch.object(v,'INITIAL_FIELDS',fields),self.assertRaises(ValueError):v._compose_case(self.raw,405)
