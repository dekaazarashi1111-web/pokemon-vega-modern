"""旧診断7件と、再hash済みmutationを含むfail-closed反証。"""
import copy,hashlib,json,pathlib,sys,unittest
import pr16_dex_hof_script_engine as v
FIXTURE=None  # 親が(raw,inherited,review,sources)を注入。import時I/O禁止。

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():
   a=obj['address']-0x8000000;n=obj['size'];obj['sha256']=hashlib.sha256(raw[a:a+n]).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)

class EngineTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('FIXTURE=(raw,inherited,review,sources) injection required')
  self.raw,self.inherited,self.review,self.sources=FIXTURE
 def check(self,review=None,raw=None,inherited=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject(self,edit):
  j=copy.deepcopy(self.review);edit(j)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(j)
 def mutate(self,address,size,value,edit=None):
  raw=bytearray(self.raw);start=address-0x8000000;self.assertNotEqual(bytes(raw[start:start+size]),value.to_bytes(size,'little'),'mutation must change actual bytes');raw[start:start+size]=value.to_bytes(size,'little');raw=bytes(raw);j=copy.deepcopy(self.review);inh=copy.deepcopy(self.inherited);reseal(j,raw);reseal(inh,raw)
  if edit:edit(j)
  with self.assertRaises(ValueError):self.check(j,raw,inh)
 def test_01_diagnostic_seven(self):self.assertEqual(len(self.check()[0]),7)
 def test_02_current_whole_binding_rejects_mismatched_candidate(self):
  with self.assertRaises(ValueError):v.regions(self.raw,dict(self.inherited,candidate=dict(size=0,sha256='0'*64)),self.review,self.sources)
 def test_03_wrong_special_slot(self):self.reject(lambda j:j['rows'][2]['root'].update(special_id=94))
 def test_04_symbol_name_cannot_be_root(self):self.reject(lambda j:j['rows'][2]['root'].update(kind='pinned_jp_symbol'))
 def test_05_no_rooted_path(self):self.reject(lambda j:j['rows'][2]['instruction_path'].pop(0))
 def test_06_skipped_instruction(self):self.reject(lambda j:j['rows'][2]['instruction_path'].pop(5))
 def test_07_bad_BL_target(self):self.reject(lambda j:next(p for p in j['rows'][2]['instruction_path']if 'target'in p).update(target=0x080003A4))
 def test_08_wrong_BX_mode_reset_pointer(self):
  self.mutate(0x08000244,4,0x080003A4,lambda j:next(p for p in j['consumer_literals']if p['label']=='startup_main_entry').update(value=0x080003A4))
 def test_09_changed_reset_branch_target(self):self.mutate(0x08000000,4,int.from_bytes(self.raw[:4],'little')^1)
 def test_10_changed_ARM_BX_register(self):self.mutate(0x08000230,4,0xE12FFF10)
 def test_11_changed_main_store_field(self):self.mutate(0x08000546,2,int.from_bytes(self.raw[0x546:0x548],'little')^64)
 def test_12_changed_main_load_field(self):self.mutate(0x08000530,2,int.from_bytes(self.raw[0x530:0x532],'little')^64)
 def test_13_wrong_main_callback_literal(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'][0].update(target=0x080F2ED5))
 def test_14_missing_task_transition(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'].pop())
 def test_15_wrong_task_stride_metadata(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'][-1].update(stride=36))
 def test_16_actual_task_field_store_mutated(self):self.mutate(0x080F305E,2,int.from_bytes(self.raw[0xF305E:0xF3060],'little')^64)
 def test_17_task_index_preservation_broken(self):self.mutate(0x080F2EE2,2,0x4688) # MOV r8,r1 instead of argument0
 def test_18_actual_task_stride_mutated(self):self.mutate(0x080F303A,2,int.from_bytes(self.raw[0xF303A:0xF303C],'little')^64)
 def test_19_same_task_table_value_changed(self):
  self.mutate(0x080F3054,4,0x030050F8,lambda j:j['rows'][0]['typed_indirect_edges'][-1]['table_literal'].update(value=0x030050F8))
 def test_20_wrong_switch_slot(self):self.reject(lambda j:j['rows'][2]['typed_indirect_edges'][0].update(index=15))
 def test_21_switch_halfword_size(self):
  def edit(j):
   pc=j['rows'][2]['typed_indirect_edges'][0]['from'];next(p for p in j['rows'][2]['instruction_path']if p['address']==pc)['size']=4
  self.reject(edit)
 def test_22_switch_bound_register_mutated(self):self.mutate(0x080FFE16,2,int.from_bytes(self.raw[0xFFE16:0xFFE18],'little')^256)
 def test_23_blanket_function_range(self):self.reject(lambda j:j['rows'][0].update(whole_function_range_classified=True))
 def test_24_literal_pool_as_code(self):self.reject(lambda j:j['rows'][1].update(literal_pool_included=True))
 def test_25_hit_identity_changed(self):self.reject(lambda j:j['rows'][1]['hit'].update(target=0x09FED001))
 def test_26_missing_hit_row(self):self.reject(lambda j:j['rows'].pop())
 def test_27_source_binding(self):
  s=dict(self.sources);s['pret-crt0.s']+=b'\n'
  with self.assertRaises(ValueError):self.check(sources=s)
 def test_28_boot_root_wrong_literal(self):self.reject(lambda j:j['rows'][1]['root']['slot'].update(address=0x08000240))
 def test_29_restore_only_still_unknown_hit(self):
  i=copy.deepcopy(self.inherited);next(x for x in i['hits']if x['address']==v.HITS[0])['accepted']=True
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_30_missing_main_source(self):self.reject(lambda j:j['source_bindings'].pop('vendor/upstream/pokefirered/src/main.c'))
 def test_31_missing_boot_window(self):self.reject(lambda j:j.update(consumer_windows=[w for w in j['consumer_windows']if w['label']!='reset_startup_arm']))
 def test_32_resealed_ARM_branch_as_mode_setup(self):self.mutate(0x08000204,4,0xEA000012)
 def test_33_resealed_ARM_store_as_mode_setup(self):self.mutate(0x08000210,4,0xE580001F)
 def test_34_conditional_ARM_mode_MOV(self):self.mutate(0x08000204,4,0x13A00012)
 def test_35_conditional_ARM_MSR(self):self.mutate(0x08000208,4,0x1129F000)
 def test_36_main_callback_value_clobber_after_load(self):self.mutate(0x08000532,2,0x2000)
 def test_37_main_callback_untracked_control_transfer(self):self.mutate(0x08000534,2,0x4708)
 def test_38_RunTasks_argument_clobber(self):self.mutate(0x08076D26,2,0x2000)
 def test_39_CreateTask_callback_argument_clobber(self):self.mutate(0x08076BB6,2,0x2200)
 def test_40_special_loaded_function_clobber(self):self.mutate(0x080697D0,2,0x2000)
 def test_41_main_setter_transfer_before_store(self):self.mutate(0x08000544,2,0x4708)
 def test_42_main_callback_wrong_null_branch(self):self.mutate(0x08000534,2,0xD000)
 def test_43_RunTasks_initial_index_clobber(self):self.mutate(0x08076D18,2,0x2000)
 def test_44_RunTasks_wrong_stride(self):self.mutate(0x08076D24,2,int.from_bytes(self.raw[0x76D24:0x76D26],'little')^64)
 def test_45_RunTasks_wrong_next_id_field(self):self.mutate(0x08076D2E,2,int.from_bytes(self.raw[0x76D2E:0x76D30],'little')^64)
 def test_46_CreateTask_wrong_stride(self):self.mutate(0x08076BC4,2,int.from_bytes(self.raw[0x76BC4:0x76BC6],'little')^64)
 def test_47_CreateTask_wrong_active_store(self):self.mutate(0x08076BE8,2,int.from_bytes(self.raw[0x76BE8:0x76BEA],'little')^64)
 def test_48_CreateTask_loop_bound(self):self.mutate(0x08076BFA,2,0x2E10)
 def test_49_finder_returns_wrong_index(self):self.mutate(0x08076D72,2,0x2000)
 def test_50_finder_bound_exceeds_sixteen_rows(self):self.mutate(0x08076D5A,2,0x2A10)
 def test_51_special_index_scale_clobber(self):self.mutate(0x080697C4,2,0x2000)
 def test_52_special_wrong_bound_condition(self):self.mutate(0x080697CE,2,int.from_bytes(self.raw[0x697CE:0x697D0],'little')^256)
 def test_53_special_selector_endian_shift(self):self.mutate(0x080691C4,2,int.from_bytes(self.raw[0x691C4:0x691C6],'little')^64)
 def test_54_script_context_argument_clobber(self):self.mutate(0x0806912C,2,0x2000)
 def test_55_script_function_pointer_clobber(self):self.mutate(0x0806912A,2,0x2100)
 def test_56_missing_finder_bound_window(self):self.reject(lambda j:j.update(consumer_windows=[w for w in j['consumer_windows']if w['label']!='FindFirstActiveTask_bounded_index']))
if __name__=='__main__':unittest.main(verbosity=2)
