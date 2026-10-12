"""TakeItem-only tests. Explicit bounded fixture; no private file I/O at import."""
import copy
import hashlib
import unittest
import pr16_dex_hof_party_takeitem as v
FIXTURE=None

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():
   a=obj['address']-0x08000000;obj['sha256']=hashlib.sha256(raw[a:a+obj['size']]).hexdigest()
  for x in obj.values():reseal(x,raw)
 elif isinstance(obj,list):
  for x in obj:reseal(x,raw)

class TakeItemTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit in-memory FIXTURE required')
  self.raw,self.inherited,self.review,self.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,edit):
  r=copy.deepcopy(self.review);edit(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def reject_evidence(self,edit):
  e=v.evidence_template();edit(e)
  with self.assertRaises((ValueError,KeyError,TypeError)):v.witness_geometry(e)
 def mutate(self,a,n,value):
  raw=bytearray(self.raw);pos=a-0x08000000;b=value.to_bytes(n,'little');self.assertNotEqual(raw[pos:pos+n],b);raw[pos:pos+n]=b
  r,i=copy.deepcopy(self.review),copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(raw=raw,review=r,inherited=i)
 def test_01_one_minimal_type_parent_unchanged(self):
  old=copy.deepcopy(self.inherited);rows,p=self.check();self.assertEqual([(r.start,r.end,r.kind) for r in rows],[(0x08120CBC,0x08120CC2,v.KIND)]);self.assertEqual(p['count'],1);self.assertEqual(old,self.inherited)
 def test_02_geometry_whole_bl_static_ldr(self):
  r=self.check()[0][0];self.assertEqual(v.witness_geometry(r.evidence),(0x08120CBC,6));self.assertEqual([i['size'] for i in r.evidence['instructions']],[4,2])
 def test_03_current_wrapper_rejects_diagnostic(self):
  if v.identity(self.raw)==v.CANDIDATE:self.assertEqual(v.regions(*FIXTURE)[1]['count'],1)
  else:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
 def test_04_candidate_fixed(self):
  i=copy.deepcopy(self.inherited);i['candidate']['sha256']='0'*64
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_05_owner_external_required(self):
  i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);next(h for h in i['hits'] if h['address']==v.HIT)['owner_candidates']=['fake'];r['hit']['owner_candidates']=['fake']
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_06_original_unknown_required(self):
  i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);next(h for h in i['hits'] if h['address']==v.HIT)['accepted']=True;r['hit']['accepted']=True
  with self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_07_duplicate_hit(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(self.review['hit']))
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_08_unrooted_geometry(self):self.reject_evidence(lambda e:e.update(root_verified=False))
 def test_09_half_bl(self):self.reject_evidence(lambda e:e['instructions'][0].update(size=2))
 def test_10_byte_tail(self):self.reject_evidence(lambda e:e['instructions'][1].update(size=1))
 def test_11_nonadjacent(self):self.reject_evidence(lambda e:e['instructions'][1].update(address=0x08120CC2))
 def test_12_no_observed_return(self):self.reject_evidence(lambda e:e['claims'].update(bl_return_observed=True))
 def test_13_no_whole_function(self):self.reject_evidence(lambda e:e['claims'].update(whole_function_range_classified=True))
 def test_14_no_pool(self):self.reject_evidence(lambda e:e.update(literal_pool_included=True))
 def test_15_no_other_task(self):self.reject_evidence(lambda e:e.update(same_selected_task=False))
 def test_16_no_result_substitution(self):self.reject_evidence(lambda e:e.update(producer_result=1))
 def test_17_no_bool_alias(self):self.reject_evidence(lambda e:e['root'].update(take_input=True))
 def test_18_no_extra_evidence(self):self.reject_evidence(lambda e:e.update(override=True))
 def test_19_no_extra_review(self):self.reject_review(lambda r:r.update(override=True))
 def test_20_no_natural_reachability(self):self.reject_review(lambda r:r['claims'].update(full_story_reachability_claimed=True))
 def test_21_no_getter12_effect_claim(self):self.reject_review(lambda r:r['claims'].update(field12_getter_effects_proven=True))
 def test_22_no_getter11_45_reuse(self):self.reject_review(lambda r:r['claims'].update(field11_45_proof_reused_for_field12=True))
 def test_23_no_donor(self):self.reject_review(lambda r:r['claims'].update(donor_eligible=True))
 def test_24_no_universal_epoch(self):self.reject_review(lambda r:r['claims'].update(universal_allocation_epoch_proven=True))
 def test_25_no_runtime_claim(self):self.reject_review(lambda r:r['claims'].update(runtime_execution_observed=True))
 def test_26_no_contract_removal(self):self.reject_review(lambda r:r['input_contract'].pop('setter'))
 def test_27_root_not_symbol(self):self.reject_review(lambda r:r['root'].update(kind='symbol_only'))
 def test_28_missing_window(self):self.reject_review(lambda r:r['windows'].pop())
 def test_29_duplicate_window(self):self.reject_review(lambda r:r['windows'].append(copy.deepcopy(r['windows'][0])))
 def test_30_reordered_windows(self):self.reject_review(lambda r:r['windows'].reverse())
 def test_31_extra_window_field(self):self.reject_review(lambda r:r['windows'][0].update(trusted=True))
 def test_32_whole_source_content(self):
  for key in v.SOURCE_IDS:
   s=dict(self.sources);s[key]+=b'\n'
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(sources=s)
 def test_33_source_manifest_not_selfsigned(self):self.reject_review(lambda r:r['source_bindings']['pret-party_menu.c'].update(sha256='0'*64))
 def test_34_missing_dependency(self):
  s=dict(self.sources);s.pop('runtime_review')
  with self.assertRaises(ValueError):self.check(sources=s)
 def test_35_every_semantic_halfword_resealed(self):
  cases={(a+o,min(2,n-o)) for a,n in v.WINDOWS.values() for o in range(0,n,2)}
  for a,n in sorted(cases):
   old=int.from_bytes(v.chunk(self.raw,a,n),'little')
   with self.subTest(address=a,size=n):self.mutate(a,n,old^1)
  self.assertGreater(len(cases),1500)
 def test_36_item_not_mail(self):self.mutate(0x08419DC4,4,0x081244D1)
 def test_37_take_not_give(self):self.mutate(0x08419DD4,4,0x08123EE1)
 def test_38_count3(self):self.mutate(0x08419EF8,1,2)
 def test_39_index1_take(self):self.mutate(0x08419EAD,1,4)
 def test_40_submenu_array_pointer(self):self.mutate(0x08419EDC,4,0x08419EAF)
 def test_41_callback_thumbbit(self):self.mutate(0x08419DD4,4,0x08124414)
 def test_42_same_task_selector(self):self.mutate(0x08123EDC,4,0x08124535)
 def test_43_nonmail_branch(self):
  a=0x081232AE;old=int.from_bytes(v.chunk(self.raw,a,2),'little');self.mutate(a,2,old^256)
 def test_44_success_constant2(self):
  i=v.party.Ins(0x08120E38,'imm',('mov',0,1));self.mutate(i.address,2,int.from_bytes(v.party.encoded(i),'little'))
 def test_45_setter_field12(self):
  i=v.party.Ins(0x08120E30,'imm',('mov',1,11));self.mutate(i.address,2,int.from_bytes(v.party.encoded(i),'little'))
 def test_46_event8(self):
  i=v.party.Ins(0x08120CAE,'imm',('mov',0,7));self.mutate(i.address,2,int.from_bytes(v.party.encoded(i),'little'))
 def test_47_same_selected_task_phase(self):
  c=self.check()[1]['composition'];self.assertEqual(c['selected_task'],0);self.assertEqual(c['outer_actions'],[0,3,2]);self.assertEqual(c['item_actions'],[4,5,9]);self.assertEqual(c['try_take_result'],2)
 def test_48_profile_item_domain(self):
  for value in (0,-1,65536,True,None):
   with self.subTest(value=value),self.assertRaises(ValueError):v.selected_profile(held_item=value)
 def test_49_profile_bag_success_domain(self):
  for value in (0,-1,256,True,None):
   with self.subTest(value=value),self.assertRaises(ValueError):v.selected_profile(bag_result=value)
 def test_50_conditions_not_integers(self):
  for key in ('normal_returns','fields_preserved','stack_nonalias'):
   for value in (False,1,None):
    with self.subTest(key=key,value=value),self.assertRaises(ValueError):v.selected_profile(**{key:value})
 def test_51_no_item_actual_result0(self):
  p=v.try_take_result(self.raw,0,1);self.assertEqual(p['result'],0);self.assertEqual(p['calls'],[0x08120E08]);self.assertFalse(p['setter_called'])
 def test_52_bag_failure_actual_result1(self):
  p=v.try_take_result(self.raw,1,0);self.assertEqual(p['result'],1);self.assertEqual(p['calls'],[0x08120E08,0x08120E1E]);self.assertFalse(p['setter_called'])
 def test_53_success_actual_result2(self):
  for item,bag in ((1,1),(65535,255),(42,2)):
   p=v.try_take_result(self.raw,item,bag);self.assertEqual(p['result'],2);self.assertTrue(p['setter_called'])
 def test_54_requires_setter_return(self):
  for x in (False,None,1):
   with self.subTest(x=x),self.assertRaises(ValueError):v.try_take_result(self.raw,1,1,x)
 def test_55_alternate_item_bag(self):
  c=v.compose_selected(self.raw,42,255);self.assertEqual(c['try_take_result'],2);self.assertEqual(c['profile']['held_item'],42)
 def test_56_field12_boundary_not_proven(self):
  c=self.check()[1]['composition'];calls=[r for r in c['conditional_calls'] if r['site'] in (0x0812329E,0x0812442C,0x08120E08)]
  self.assertEqual(len(calls),3);self.assertTrue(all(r['effects_discharged'] is False and r['return_value']==1 for r in calls))
 def test_57_no_hit_callee_execution(self):
  c=self.check()[1]['composition'];self.assertFalse(c['callee_at_hit_executed']);self.assertFalse(any(r['site']==0x08120CBC for r in c['conditional_calls']))
 def test_58_questlog_exact(self):
  c=self.check()[1]['composition'];r=[r for r in c['conditional_calls'] if r['site']==0x08120CB4]
  self.assertEqual(len(r),1);self.assertEqual(r[0]['target'],0x080A3554);self.assertEqual(r[0]['phase'],'helper');self.assertFalse(r[0]['effects_discharged'])
 def test_59_no_bytes_private_paths(self):
  def scan(obj):
   if isinstance(obj,dict):
    self.assertFalse(set(obj)&{'raw','rawhex','bytes','data','private_path','member_path'})
    for x in obj.values():scan(x)
   elif isinstance(obj,list):
    for x in obj:scan(x)
  scan(self.review);scan(self.check()[1]);scan(v.evidence_template())
 def test_60_diagnostic_distinct(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_61_external_effects_undischarged(self):
  calls=self.check()[1]['composition']['conditional_calls'];self.assertTrue(calls);self.assertTrue(all(r['normal_abi_return_required'] is True and r['effects_discharged'] is False and r['required_fields'] for r in calls))
 def test_62_root_actual_table(self):self.assertEqual(v.ALL_WORDS[0x0836B380],v.ROOT['entry']|1);self.assertEqual(v.ROOT['constructor'],0x0811F24C)
 def test_63_source_git_blobs(self):
  for key,b in self.sources.items():self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),v.SOURCE_IDS[key]['git_blob_sha'])
 def test_64_phase_projection_detects_live_write(self):
  p=v.runtime.ROOT+16
  for phase in v.PHASE_FIELDS:
   for f in v.live_projection(p,phase):
    with self.subTest(phase=phase,field=f['role']),self.assertRaises(ValueError):v.preservation_contract(p,phase,[(f['address'],1)])
 def test_65_unrelated_writes_do_not_freeze_all_ram(self):
  p=v.runtime.ROOT+16
  for phase in v.PHASE_FIELDS:self.assertTrue(v.preservation_contract(p,phase,[(0x0203E000,12)]))
 def test_66_other_task_data_not_frozen(self):
  p=v.runtime.ROOT+16;self.assertTrue(v.preservation_contract(p,'item_submenu',[(v.TASKS+40+8,32)]))
 def test_67_epoch_before_last_heap_read(self):
  p=v.runtime.ROOT+16
  for phase in ('root_setup','outer_builder','item_submenu','take_before_last_heap_read'):
   with self.subTest(phase=phase),self.assertRaises(ValueError):v.preservation_contract(p,phase,[],freed=(p,))
   with self.subTest(phase=phase),self.assertRaises(ValueError):v.preservation_contract(p,phase,[],heap_reinitialized=True)
 def test_68_no_heap_requirement_after_last_read(self):
  p=v.runtime.ROOT+16
  for phase in ('try_take','helper'):self.assertTrue(v.preservation_contract(p,phase,[(p,568)],freed=(p,),heap_reinitialized=True))
 def test_69_invalid_projection_domains(self):
  p=v.runtime.ROOT+16
  for kwargs in (dict(pointer=p+1),dict(phase='any'),dict(task_id=True),dict(task_admitted=1)):
   args=dict(pointer=p,phase='item_submenu',writes=[]);args.update(kwargs)
   with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v.preservation_contract(**args)

 def test_70_actual_two_selector_callback_cells(self):
  c=self.check()[1]['composition'];rows=[r for r in c['events'] if r['role']=='selector_callback']
  self.assertEqual([(r['callback_cell'],r['callback'],r['task_id']) for r in rows],[(0x08419DC4,0x08123E7D,0),(0x08419DD4,0x08124415,0)])
 def test_71_callback1_write_is_live_in_three_phases(self):
  p=v.runtime.ROOT+16
  for phase in ('root_setup','outer_builder','item_submenu'):
   rows=[r for r in v.live_projection(p,phase) if r['address']==v.MAIN and r['size']==4]
   self.assertEqual(len(rows),1)
   with self.subTest(phase=phase),self.assertRaises(ValueError):v.preservation_contract(p,phase,[(v.MAIN,4)])
 def test_72_actual_callback1_overwrite_diverts_before_callback2(self):
  p=v.callback1_counterexample(self.raw);self.assertFalse(p['alternate_body_executed'])
  self.assertEqual([(r['callback1'],r['first_callback_entry'],r['indirect_call']) for r in p['cases']],[(0,0x0811F3A8,0x08000536),(0x08124415,0x08124414,0x0800052C)])
 def test_73_callback1_preservation_cannot_be_removed(self):self.reject_review(lambda r:r['input_contract'].pop('main_callback1'))
 def test_74_selection_boundary_records_exact_five_outputs(self):
  p=v.runtime.ROOT+16;c=self.check()[1]['composition'];rows=[r for r in c['conditional_calls'] if r['target']==0x08122628]
  self.assertEqual(len(rows),2)
  expected=[(v.CURSOR+2,1,0),(v.CURSOR+3,1,0),(v.CURSOR+4,1,2),(v.CURSOR+11,1,1),(p+12,1,0)]
  for r in rows:self.assertEqual([(f['address'],f['size'],f['value']) for f in r['conditional_outputs']],expected);self.assertFalse(r['effects_discharged'])
 def test_75_each_selection_field_value_required(self):
  p=v.runtime.ROOT+16
  for j in range(5):
   spec=copy.deepcopy(v.SELECTION_OUTPUT_SPEC);spec[j]['value']^=1
   with self.subTest(field=j),self.assertRaises(ValueError):v.selection_initialization(p,1,3,spec)
 def test_76_each_selection_field_address_required(self):
  p=v.runtime.ROOT+16
  for j in range(5):
   spec=copy.deepcopy(v.SELECTION_OUTPUT_SPEC);spec[j]['offset']+=1
   with self.subTest(field=j),self.assertRaises(ValueError):v.selection_initialization(p,1,3,spec)
 def test_77_selection_cursor_zero_not_arbitrary_valid_index(self):
  for value in (1,2):
   spec=copy.deepcopy(v.SELECTION_OUTPUT_SPEC);spec[0]['value']=value
   with self.subTest(cursor=value),self.assertRaises(ValueError):v.selection_initialization(v.runtime.ROOT+16,1,3,spec)
 def test_78_selection_output_closed_schema(self):
  p=v.runtime.ROOT+16
  for kind,count,spec in ((True,3,v.SELECTION_OUTPUT_SPEC),(1,True,v.SELECTION_OUTPUT_SPEC),(1,3,v.SELECTION_OUTPUT_SPEC[:-1]),(1,3,list(reversed(v.SELECTION_OUTPUT_SPEC)))):
   with self.assertRaises(ValueError):v.selection_initialization(p,kind,count,spec)
 def test_79_selection_outputs_cannot_be_weakened(self):self.reject_review(lambda r:r['input_contract']['selection_window_outputs'][0].update(value=1))
 def test_80_actual_initial_cursor_one_changes_down_a_to_index2(self):
  selected=[]
  for initial in (0,1):
   mem={};p=v.runtime.ROOT+16
   for f in v.selection_initialization(p,1,3,v.SELECTION_OUTPUT_SPEC):v.runtime.setmem(mem,f['address'],f['size'],f['value'])
   v.runtime.setmem(mem,v.CURSOR+2,1,initial)
   for down in (True,False):
    v.runtime.setmem(mem,v.MAIN+46,2,0 if down else 1);v.runtime.setmem(mem,v.MAIN+48,2,128 if down else 0)
    m=v.Machine(self.raw,0x08110624,memory=mem,instructions=v.INS)
    while m.pc!=0xFFFFFFF0:
     if m.pc in (0x081103A8,0x08071A70):
      for r in (0,1,2,3,12):m.reg[r]=v.runtime.U
      m.pc=m.reg[14]&~1;m.flag_pc=None
     else:m.step()
    mem=m.mem
   selected.append(m.reg[0]);self.assertEqual(m.read(v.CURSOR+2,1),initial+1)
  self.assertEqual(selected,[1,2]);self.assertEqual([v.FIELDS['item_take'][2],v.FIELDS['item_cancel'][2]],[5,9])
