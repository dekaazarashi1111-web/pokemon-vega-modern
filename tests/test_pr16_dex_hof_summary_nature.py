"""Summary nature限定consumerの負例。外部I/Oなし、明示fixtureだけ使用。"""
import copy,hashlib,unittest
from unittest.mock import patch
import pr16_dex_hof_summary_nature as v
FIXTURE=None
class Overlay:
 def __init__(self,raw,a,n,value):self.raw=raw;self.a=a-0x08000000;self.value=value.to_bytes(n,'little')
 def __len__(self):return len(self.raw)
 def __getitem__(self,key):
  if isinstance(key,int):return self[key:key+1][0]
  lo=0 if key.start is None else key.start;hi=len(self)if key.stop is None else key.stop
  b=bytearray(self.raw[key]);left=max(lo,self.a);right=min(hi,self.a+len(self.value))
  if left<right:b[left-lo:right-lo]=self.value[left-self.a:right-self.a]
  return bytes(b)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for item in obj.values():reseal(item,raw)
 elif isinstance(obj,list):
  for item in obj:reseal(item,raw)
class NatureTests(unittest.TestCase):
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
  self.assertNotEqual(int.from_bytes(v.chunk(self.raw,a,n),'little'),value)
  raw=Overlay(self.raw,a,n,value);r,i=copy.deepcopy(self.review),copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(raw=raw,review=r,inherited=i)
 def test_01_two_complete_strings_one_minimum_hit(self):
  old=copy.deepcopy(self.inherited);rows,p=self.check();self.assertEqual([(r.start,r.end,r.kind)for r in rows],[(v.HIT,v.HIT+4,v.KIND)]);self.assertEqual(old,self.inherited)
  self.assertEqual([(c['index'],c['nature_byte_reads'],c['includes_eos_read'])for c in p['composition']['cases']],[(5,5,True),(6,4,True)])
  self.assertEqual(p['composition']['complete_consumed_bytes'],9)
 def test_02_exact_crossing_geometry(self):self.assertEqual(v.witness_geometry(v.evidence_template()),(0x0842D18A,4))
 def test_03_diagnostic_cannot_pass_current_wrapper(self):
  with patch.object(v,'identity',return_value=v.DIAGNOSTIC),patch.object(v,'_regions')as accept:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   accept.assert_not_called()
 def test_04_current_candidate_fixed(self):
  i=copy.deepcopy(self.inherited);i['candidate']['sha256']='0'*64
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_05_owner_external(self):
  i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0]['owner_candidates']=['fake'];r['hit']['owner_candidates']=['fake']
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_06_unknown_only(self):
  i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0]['accepted']=True;r['hit']['accepted']=True
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_07_duplicate_hit(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(self.review['hit']))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_08_no_unrooted_evidence(self):self.reject_evidence(lambda e:e.update(root_verified=False))
 def test_09_no_one_sided_consumer(self):self.reject_evidence(lambda e:e.update(both_complete_text_consumers_verified=False))
 def test_10_no_table_type_expansion(self):self.reject_evidence(lambda e:e.update(pointer_table_rows_classified=True))
 def test_11_no_template_classification(self):self.reject_evidence(lambda e:e.update(template_prefix_classified=True))
 def test_12_no_whole_text_classification(self):self.reject_evidence(lambda e:e['classified_window'].update(address=0x0842D188,size=9))
 def test_13_no_partial_left(self):self.reject_evidence(lambda e:e['left'].update(size=4))
 def test_14_no_partial_right(self):self.reject_evidence(lambda e:e['right'].update(size=3))
 def test_15_no_natural_claim(self):self.reject_review(lambda r:r['claims'].update(full_story_reachability_claimed=True))
 def test_16_no_runtime_claim(self):self.reject_review(lambda r:r['claims'].update(actual_runtime_execution_observed=True))
 def test_17_no_donor_claim(self):self.reject_review(lambda r:r['claims'].update(donor_eligible=True))
 def test_18_no_pointer_interpretation(self):self.reject_review(lambda r:r['claims'].update(source_pointer_interpretation=True))
 def test_19_no_indirect_completeness(self):self.reject_review(lambda r:r['claims'].update(indirect_reference_completeness_claimed=True))
 def test_20_no_opaque_effect_promotion(self):self.reject_review(lambda r:r['claims'].update(opaque_callee_effects_proven=True))
 def test_21_no_missing_contract(self):self.reject_review(lambda r:r['input_contract'].pop('placeholder'))
 def test_22_no_missing_window(self):self.reject_review(lambda r:r['windows'].pop())
 def test_23_no_duplicate_window(self):self.reject_review(lambda r:r['windows'].append(copy.deepcopy(r['windows'][0])))
 def test_24_no_reordered_window(self):self.reject_review(lambda r:r['windows'].reverse())
 def test_25_no_extra_review(self):self.reject_review(lambda r:r.update(trusted=True))
 def test_26_no_extra_evidence(self):self.reject_evidence(lambda e:e.update(trusted=True))
 def test_27_fixed_whole_sources(self):
  for key in v.SOURCE_IDS:
   s=dict(self.sources);s[key]+=b'\n'
   with self.subTest(source=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_28_source_manifest_not_resealable(self):self.reject_review(lambda r:r['source_bindings']['pret-nature_names.h'].update(sha256='0'*64))
 def test_29_all_local_semantic_halfwords_resealed(self):
  cases={(i.address+o,2)for rows in v.BLOCKS.values()for i in rows for o in range(0,i.size,2)}
  for a,n in sorted(cases):
   with self.subTest(address=a):self.mutate(a,n,int.from_bytes(v.chunk(self.raw,a,n),'little')^1)
  self.assertGreater(len(cases),200)
 def test_30_every_local_literal_resealed(self):
  for a,old in v.LITERALS.items():
   with self.subTest(address=a):self.mutate(a,4,old^1)
 def test_31_template_must_select_zero(self):
  for a in v.TEMPLATES.values():self.mutate(a+1,1,1)
 def test_32_template_must_be_dynamic(self):
  for a in v.TEMPLATES.values():self.mutate(a,1,246)
 def test_33_complete_text_byte_identities(self):
  for row in v.TEXTS:
   for j in range(row['size']):
    a=row['address']+j
    with self.subTest(address=a):self.mutate(a,1,v.chunk(self.raw,a,1)[0]^1)
 def test_34_wrong_nature_selection(self):
  root,_=v.summary.root_at_setup(self.raw,8)
  for nature in (True,0,4,7,25):
   with self.subTest(nature=nature),self.assertRaises(ValueError):v._compose_from_root(self.raw,root,nature)
 def test_35_root_control_fields(self):
  root,_=v.summary.root_at_setup(self.raw,8);p=root.read(v.CELL,4)
  for off,n,val in((0x3220,1,9),(0x31C0,1,1),(0x31AC,1,1),(0x3024,4,1)):
   changed=copy.copy(root);changed.mem=dict(root.mem);v.runtime.setmem(changed.mem,p+off,n,val)
   with self.subTest(offset=off),self.assertRaises(ValueError):v._compose_from_root(self.raw,changed,5)
 def test_36_root_entry_must_be_actual_setup_call(self):
  root,_=v.summary.root_at_setup(self.raw,8);root.pc=0x08137CA0
  with self.assertRaises(ValueError):v._compose_from_root(self.raw,root,5)
 def test_37_placeholder_pointer_must_be_same(self):self.mutate(0x0842D200,4,0x0842D18D)
 def test_38_other_text_pointer_cannot_alias(self):self.mutate(0x0842D204,4,0x0842D188)
 def test_39_minimum_boundary_not_summary_code(self):self.reject_evidence(lambda e:e['classified_window'].update(address=0x081357A6,size=6))
 def test_40_no_universal_epoch_claim(self):self.reject_review(lambda r:r['claims'].update(universal_heap_or_irq_lifetime_proven=True))
 def test_41_no_ability_getter_contract(self):self.reject_review(lambda r:r['input_contract'].update(getter='reuse party ability getter'))
 def test_42_no_other_root_state(self):self.reject_review(lambda r:r['root'].update(setup_state=9))
 def test_43_current_wrapper_passes_only_declared_identity_gate(self):
  with patch.object(v,'identity',return_value=v.CANDIDATE),patch.object(v,'_regions',return_value='sentinel')as accept:
   self.assertEqual(v.regions(*FIXTURE),'sentinel');accept.assert_called_once()
 def test_44_declared_boundaries_remain_conditional(self):
  proof=self.check()[1]['composition']
  for case in proof['cases']:
   self.assertEqual(len(case['conditional_calls']),10)
   self.assertTrue(all(c['effects_discharged']is False and c['normal_abi_return_required']is True for c in case['conditional_calls']))
 def test_45_concrete_live_projection_havoc(self):
  proof=self.check()[1]['composition'];self.assertTrue(all(c['nonlive_ram_erased_at_each_boundary']is True for c in proof['cases']))
  counter=proof['projection_counterexamples'];self.assertEqual(counter['live_field_write_rejections'],45)
  for case in proof['cases']:
   for call in case['conditional_calls']:
    self.assertTrue(all(set(f)=={'address','size','role'}for f in call['required_fields']))
    self.assertTrue(any(f['role']=='active saved ABI stack'for f in call['required_fields']))
 def test_46_enemy_word_before_its_last_read(self):
  p=0x02000010
  for site in(0x08137CAE,0x0813810A,0x08042592,0x08137D60,0x08137D74,0x08137D86,0x08137D90):
   with self.subTest(site=site),self.assertRaises(ValueError):v.preservation_contract(p,site,[(p+0x3024,4)])
  self.assertTrue(v.preservation_contract(p,0x08137DBC,[(p+0x3024,4)]))
 def test_47_placeholder_zero_only_after_store(self):
  p=0x02000010
  self.assertTrue(v.preservation_contract(p,0x08042592,[(v.PLACEHOLDERS,4)]))
  with self.assertRaises(ValueError):v.preservation_contract(p,0x08137D60,[(v.PLACEHOLDERS,4)])
  self.assertTrue(v.preservation_contract(p,0x08137D60,[(v.PLACEHOLDERS+4,4)]))
 def test_48_active_saved_stack_and_output_locals(self):
  p=0x02000010;stack=range(0x03006FE0,0x03006FF0)
  with self.assertRaises(ValueError):v.preservation_contract(p,0x08137D74,[(0x03006FE4,4)],saved_stack=stack)
  self.assertTrue(v.preservation_contract(p,0x08137D74,[(0x03006F80,5)],saved_stack=stack))
 def test_49_epoch_aba_rejected(self):
  for kwargs in({'freed':(0x02000010,)},{'heap_reinitialized':True}):
   with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v.preservation_contract(0x02000010,0x08137D60,[],**kwargs)
 def test_50_wrong_or_boolean_boundary(self):
  for site in(True,0x08137D61):
   with self.assertRaises(ValueError):v.live_projection(0x02000010,site)
