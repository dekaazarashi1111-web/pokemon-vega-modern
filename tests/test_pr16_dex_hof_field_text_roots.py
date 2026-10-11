"""Bagの実登録/producer/byte consumer、最小型と保護境界の負例。I/Oなし。"""
import copy,hashlib,unittest
from unittest.mock import patch
import pr16_dex_hof_field_text_roots as v
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
  for item in obj.values():reseal(item,raw)
 elif isinstance(obj,list):
  for item in obj:reseal(item,raw)
class BagTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('explicit bounded in-memory FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
  cls.regions,cls.proof=v._regions(*FIXTURE)
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,edit):
  r=copy.deepcopy(self.review);edit(r)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(review=r)
 def reject_evidence(self,edit):
  for h in v.HITS:
   e=v.evidence_template(h);edit(e)
   with self.subTest(hit=h),self.assertRaises((ValueError,TypeError,KeyError)):v.witness_geometry(e)
 def mutate(self,a,n,value):
  raw=Overlay(self.raw,a,n,value);r,i=copy.deepcopy(self.review),copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(raw=raw,review=r,inherited=i)
 def test_01_one_only_minimum_window(self):
  self.assertEqual([(r.start,r.end,r.kind)for r in self.regions],[(h,h+4,v.KIND)for h in v.HITS]);self.assertEqual(self.inherited,FIXTURE[1])
 def test_02_exact_real_producer_and_byte_reads(self):
  p=self.proof['composition'];self.assertEqual((p['frames'],p['producer_events'],p['boundary_count'],p['complete_consumed_bytes']),(4,33,129,8));self.assertEqual(p['actual_byte_read'],0x0800580E);self.assertTrue(p['includes_both_eos'])
 def test_03_nonlive_erasure_replayed(self):self.assertTrue(self.proof['composition']['nonlive_ram_erased_at_each_boundary'])
 def test_04_same_current_not_diagnostic(self):
  with patch.object(v,'identity',return_value=v.DIAGNOSTIC),patch.object(v,'_regions')as accept:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   accept.assert_not_called()
 def test_05_current_wrapper_gate(self):
  with patch.object(v,'identity',return_value=v.CANDIDATE),patch.object(v,'_regions',return_value='sentinel')as accept:self.assertEqual(v.regions(*FIXTURE),'sentinel');accept.assert_called_once()
 def test_06_current_identity_required(self):
  i=copy.deepcopy(self.inherited);i['candidate']['sha256']='0'*64
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_07_accepted_hit_rejected(self):
  i,r=copy.deepcopy(self.inherited),copy.deepcopy(self.review);i['hits'][0]['accepted']=r['hits'][0]['accepted']=True
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_08_owner_hit_rejected(self):
  i,r=copy.deepcopy(self.inherited),copy.deepcopy(self.review);i['hits'][0]['owner_candidates']=r['hits'][0]['owner_candidates']=['fake']
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_09_duplicate_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(i['hits'][0])
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_10_missing_hit_rejected(self):
  i=copy.deepcopy(self.inherited);i['hits'].pop()
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_11_unregistered_bag_root_rejected(self):self.reject_review(lambda r:r['root'].update(entry=0x0806EC3C))
 def test_12_missing_actual_count_writer_rejected(self):self.reject_review(lambda r:r['root'].update(action_count_writer=0x0810A4DE))
 def test_13_text_pointer_promotion_rejected(self):self.reject_review(lambda r:r['claims'].update(source_pointer_interpretation=True))
 def test_14_no_natural_play_claim(self):self.reject_review(lambda r:r['claims'].update(full_story_reachability_claimed=True))
 def test_15_no_native_observation_claim(self):self.reject_review(lambda r:r['claims'].update(actual_runtime_execution_observed=True))
 def test_16_no_full_epoch_claim(self):self.reject_review(lambda r:r['claims'].update(universal_heap_or_irq_lifetime_proven=True))
 def test_17_no_donor_claim(self):self.reject_review(lambda r:r['claims'].update(donor_eligible=True))
 def test_18_no_padding_claim(self):self.reject_review(lambda r:r['claims'].update(padding_classified=True))
 def test_19_no_opaque_proof_claim(self):self.reject_review(lambda r:r['claims'].update(opaque_callee_effects_proven=True))
 def test_20_no_indirect_completeness(self):self.reject_review(lambda r:r['claims'].update(indirect_reference_completeness_claimed=True))
 def test_21_no_missing_allocation_precondition(self):self.reject_review(lambda r:r['input_contract'].pop('allocation'))
 def test_22_no_missing_lifetime_contract(self):self.reject_review(lambda r:r['input_contract'].pop('lifetime'))
 def test_23_no_missing_window(self):self.reject_review(lambda r:r['windows'].pop())
 def test_24_no_added_window(self):self.reject_review(lambda r:r['windows'].append(r['windows'][0]))
 def test_25_no_window_reorder(self):self.reject_review(lambda r:r['windows'].reverse())
 def test_26_source_byte_binding(self):
  for key in v.SOURCE_IDS:
   s=dict(self.sources);s[key]+=b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_27_source_manifest_binding(self):self.reject_review(lambda r:r['source_bindings']['pret-item_menu.c'].update(sha256='0'*64))
 def test_28_closed_review(self):self.reject_review(lambda r:r.update(trusted=True))
 def test_29_closed_evidence(self):self.reject_evidence(lambda e:e.update(trusted=True))
 def test_30_no_whole_string_classification(self):self.reject_evidence(lambda e:e['classified_window'].update(address=0x083E2630,size=55))
 def test_31_padding_and_sorting_hits_remain_unknown(self):
  for hit in(0x083E239B,0x083E24C3,0x083E2563,0x083E258F,0x09149270,0x09149286):
   with self.subTest(hit=hit),self.assertRaises(ValueError):v.evidence_template(hit)
 def test_32_no_unrooted_evidence(self):self.reject_evidence(lambda e:e.update(root_verified=False))
 def test_33_no_partial_consumption(self):self.reject_evidence(lambda e:e.update(all_hit_bytes_consumed=False))
 def test_34_no_skipped_eos(self):self.reject_evidence(lambda e:e.update(includes_complete_eos=False))
 def test_35_no_other_consumer(self):self.reject_evidence(lambda e:e.update(actual_byte_consumer=0x08008900))
 def test_36_every_semantic_halfword_independent_encoder(self):
  count=0
  for i in v.INS.values():
   self.assertEqual(v.chunk(self.raw,i.address,i.size),v.encoded(i))
   for off in range(0,i.size,2):
    a=i.address+off;value=int.from_bytes(v.chunk(self.raw,a,2),'little')^1;raw=Overlay(self.raw,a,2,value)
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(raw)
    count+=1
  self.assertGreater(count,1000)
 def test_37_every_literal_resealed_rejected(self):
  for a,value in v.LITERALS.items():
   with self.subTest(address=a):self.mutate(a,4,value^1)
 def test_38_all_text_bytes_resealed_rejected(self):
  for row in v.TEXTS:
   for off in range(row['size']):
    a=row['address']+off
    with self.subTest(address=a):self.mutate(a,1,v.chunk(self.raw,a,1)[0]^1)
 def test_39_all_protected_bytes_identity_rejection(self):
  for row in v.FIXED_WINDOWS:
   for off in range(row['size']):
    a=row['address']+off;raw=Overlay(self.raw,a,1,v.chunk(self.raw,a,1)[0]^1)
    with self.subTest(address=a),self.assertRaises(ValueError):v.d.signed(raw,row)
 def test_40_startmenu_registration_not_resealable(self):self.mutate(0x0836B388,4,0x0806EC3D)
 def test_41_context_registration_not_resealable(self):self.mutate(0x08413DDC,4,0x0810A6E1)
 def test_42_action_order_not_resealable(self):self.mutate(0x08413DC0,4,0x04030100)
 def test_43_use_pointer_not_resealable(self):self.mutate(0x08413D60,4,0x083DD7EA)
 def test_44_toss_pointer_not_resealable(self):self.mutate(0x08413D68,4,0x083DD7E6)
 def test_45_both_target_eos_not_resealable(self):
  for a in (0x083DD7E9,0x083DD7ED):
   with self.subTest(eos=a):self.mutate(a,1,0)
 def test_46_each_future_live_field_blocks_writes(self):
  count=0
  for row in self.proof['composition']['conditional_call_groups']:
   windows=[(w['address'],w['size'])for w in row['required_fields']]
   for a,n in windows:
    with self.subTest(site=row['site'],address=a),self.assertRaises(ValueError):v.preserve(windows,[(a,n,0)])
    count+=1
  self.assertGreater(count,200)
 def test_47_nonlive_write_allowed(self):
  for row in self.proof['composition']['conditional_call_groups']:
   windows=[(w['address'],w['size'])for w in row['required_fields']];self.assertTrue(v.preserve(windows,[(0x0203FFFC,4,0)]))
 def test_48_free_even_same_pointer_rejected(self):
  with self.assertRaises(ValueError):v.preserve([],freed=[v.ALLOC])
 def test_49_heap_reinitialize_rejected(self):
  with self.assertRaises(ValueError):v.preserve([],heap_reinitialized=True)
 def test_50_window_epoch_invalidated_rejected(self):
  with self.assertRaises(ValueError):v.preserve([],window_invalidated=True)
 def test_51_epoch_bool_not_integer(self):
  for key in('heap_reinitialized','window_invalidated'):
   with self.subTest(key=key),self.assertRaises(ValueError):v.preserve([],**{key:0})
 def test_52_projection_read_before_write(self):
  tr=[('write',100,4),('boundary',0,0),('read',100,2),('write',102,2),('read',102,2),('boundary',1,0),('read',110,1)]
  self.assertEqual(v.future_live(tr,2),[[[100,2],[110,1]],[[110,1]]])
 def test_53_actual_nonlive_write_replay(self):
  p=v.compose_selected(self.raw,opaque_writes={0x08108AFA:[(0x0203FFFC,4,123)]});self.assertEqual(p['complete_consumed_bytes'],8)
 def test_54_actual_live_corruption_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0x08108AFA:[(0x0203AC88,4,0)]})
 def test_55_actual_epoch_invalidated_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x08108AFA:dict(freed=[v.ALLOC])})
 def test_56_modified_environment_contract_rejected(self):
  c=copy.deepcopy(v.CONTRACT);c['allocation']='anything'
  with self.assertRaises(ValueError):v._compose(self.raw,contract=c)
 def test_57_proof_public_size(self):
  import json
  self.assertLess(len(json.dumps(self.proof,ensure_ascii=False,indent=2).encode()),450000)
 def test_58_same_single_witness_geometry(self):
  self.assertEqual([v.witness_geometry(v.evidence_template(h))for h in v.HITS],[(h,4)for h in v.HITS])
 def test_59_generated_outputs_not_prior_preservation(self):
  for row in self.proof['composition']['conditional_call_groups']:
   req={w['address']+j for w in row['required_fields']for j in range(w['size'])}
   prod={w['address']+j for w in row['produced_memory_ranges']for j in range(w['size'])}
   out={w['address']+j for w in row['conditional_outputs']for j in range(w['size'])}
   self.assertFalse(req&prod);self.assertFalse(req&out);self.assertTrue(prod<=out)
  alloc=next(r for r in self.proof['composition']['conditional_call_groups']if r['site']==0x08108AF4)
  self.assertEqual(sum(w['size']for w in alloc['produced_memory_ranges']),16);self.assertEqual(len(alloc['conditional_outputs']),16)
 def test_60_generated_output_clobber_rejected(self):
  for row in self.proof['composition']['conditional_call_groups']:
   windows=[(w['address'],w['size'])for w in row['required_fields']+row['produced_memory_ranges']]
   for w in row['produced_memory_ranges']:
    with self.subTest(site=row['site'],address=w['address']),self.assertRaises(ValueError):v.preserve(windows,[(w['address'],w['size'],0)])
 def test_61_actual_output_clobber_replay_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0x08108B2A:[(v.ALLOC+10,1,0)]})
 def test_62_glyph_width_is_abstract_output_not_preserved_value(self):
  rows=[r for r in self.proof['composition']['conditional_call_groups']if r['target']in(0x08006304,0x08006354)]
  self.assertTrue(rows)
  for row in rows:
   self.assertIn(dict(address=0x03003E60,size=1,value='unspecified'),row['conditional_outputs'])
   self.assertFalse(any(w['address']<=0x03003E60<w['address']+w['size']for w in row['required_fields']))
  self.assertEqual(self.proof['composition']['complete_consumed_bytes'],8)
 def test_63_empty_nonlive_ram_replay_still_consumes(self):
  self.assertTrue(self.proof['composition']['nonlive_ram_erased_at_each_boundary'])
 def test_64_normal_return_required(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,normal_returns=False)
 def test_65_initial_profile_not_replaceable(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,initial_fields=[])
 def test_66_opaque_site_typo_is_not_ignored(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0xDEADBEEF:[(0x0203FFFC,4,123)]})
 def test_67_epoch_site_typo_is_not_ignored(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0xDEADBEEF:dict(freed=[v.ALLOC])})
 def test_68_actual_output_fields_fail_closed(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0x08108AF4:[(v.TASKS+4,1,1)]})
 def test_69_no_template_or_table_classification(self):
  for h in(0x08413DC0,0x08413D60,0x083DD7E6,0x083DD7EA):
   with self.subTest(address=h),self.assertRaises(ValueError):v.evidence_template(h)
 def test_70_hit_all_boundary_bytes_actually_read(self):
  record=v._compose(self.raw);seen={a for a,n in record['reads']if n==1}
  self.assertTrue(all(a in seen for h in v.HITS for a in range(h,h+4)))
 def test_71_no_whole_object_preservation(self):
  groups=self.proof['composition']['conditional_call_groups']
  self.assertTrue(all(not any(w['address']==v.ALLOC and w['size']>=20 for w in g['required_fields'])for g in groups))
 def test_72_preexisting_table_name_is_not_root(self):
  self.reject_evidence(lambda e:e['root'].update(entry=e['root']['context_producer']))
 def test_73_unknown_epoch_effect_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x08108AFA:dict(unknown_effect=True)})
 def test_74_malformed_freed_identity_rejected(self):
  for value in(None,'same address',True,[True]):
   with self.subTest(value=value),self.assertRaises(ValueError):v.preserve([],freed=value)
 def test_75_invalid_write_geometry_rejected(self):
  for write in((-1,1,0),(0x0203FFFC,0,0),(0x0203FFFC,1,None),(0xFFFFFFFF,4,0)):
   with self.subTest(write=write),self.assertRaises(ValueError):v.preserve([],[write])
 def test_76_neighbor_allocation_free_allowed(self):self.assertTrue(v.preserve([],freed=[v.ALLOC+100]))
if __name__=='__main__':unittest.main()
