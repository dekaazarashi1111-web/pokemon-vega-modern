"""新規storage consumerのみの再hash反証。fixtureは外から注入する。"""
import copy,hashlib,unittest
try:import pr16_dex_hof_consumer_engine as v
except ModuleNotFoundError:import validate_engine as v
FIXTURE=None

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():
   a=obj['address']-0x8000000;obj['sha256']=hashlib.sha256(raw[a:a+obj['size']]).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)

class EngineTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('FIXTURE=(raw,inherited,review,sources) required; no import time ROM read')
  self.raw,self.inherited,self.review,self.sources=FIXTURE
 def check(self,j=None,raw=None,inh=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inh is None else inh,self.review if j is None else j,self.sources if sources is None else sources)
 def reject(self,edit):
  j=copy.deepcopy(self.review);edit(j)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(j)
 def mutate(self,address,size,value,edit=None):
  raw=bytearray(self.raw);a=address-0x8000000;new=value.to_bytes(size,'little');self.assertNotEqual(raw[a:a+size],new);raw[a:a+size]=new;raw=bytes(raw)
  j=copy.deepcopy(self.review);inh=copy.deepcopy(self.inherited);reseal(j,raw);reseal(inh,raw)
  if edit:edit(j)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(j,raw,inh)
 def test_01_diagnostic_one(self):
  regions,meta=self.check();self.assertEqual(len(regions),1);self.assertEqual(meta['count'],1);self.assertFalse(meta['full_story_reachability_claimed'])
 def test_02_current_whole_identity_required(self):
  with self.assertRaises(ValueError):v.regions(self.raw,dict(self.inherited,candidate=dict(size=0,sha256='0'*64)),self.review,self.sources)
 def test_03_exact_special_id(self):self.reject(lambda j:j['rows'][0]['root'].update(special_id=61))
 def test_04_exact_root_entry(self):self.reject(lambda j:j['rows'][0]['root'].update(entry=0x0808C820))
 def test_05_no_symbol_only_root(self):self.reject(lambda j:j['rows'][0]['root'].update(kind='pinned_jp_symbol'))
 def test_06_root_path_required(self):self.reject(lambda j:j['rows'][0]['instruction_path'].pop(0))
 def test_07_skip_path_instruction(self):self.reject(lambda j:j['rows'][0]['instruction_path'].pop(2))
 def test_08_unknown_hit_identity(self):self.reject(lambda j:j['rows'][0]['hit'].update(target=0x09FED001))
 def test_09_unknown_status_required(self):
  inh=copy.deepcopy(self.inherited);next(x for x in inh['hits']if x['address']==v.HITS[0])['accepted']=True
  with self.assertRaises(ValueError):self.check(inh=inh)
 def test_10_owner_range_insufficient(self):
  inh=copy.deepcopy(self.inherited);next(x for x in inh['hits']if x['address']==v.HITS[0])['owner_candidates']=['owner'];j=copy.deepcopy(self.review);j['rows'][0]['hit']['owner_candidates']=['owner']
  with self.assertRaises(ValueError):self.check(j,inh=inh)
 def test_11_no_blanket_range(self):self.reject(lambda j:j['rows'][0].update(whole_function_range_classified=True))
 def test_12_no_literal_pool(self):self.reject(lambda j:j['rows'][0].update(literal_pool_included=True))
 def test_13_minimal_window_exact(self):self.reject(lambda j:j['rows'][0]['instruction_window'].update(size=8))
 def test_14_missing_new_window(self):self.reject(lambda j:j.update(consumer_windows=[w for w in j['consumer_windows']if w['label']!='storage_task_setter']))
 def test_15_missing_constructor_window(self):self.reject(lambda j:j.update(consumer_windows=[w for w in j['consumer_windows']if w['label']!='storage_constructor_body']))
 def test_16_missing_new_source(self):self.reject(lambda j:j['source_bindings'].pop('vendor/upstream/pokefirered/src/pokemon_storage_system_tasks.c'))
 def test_17_source_content_change(self):
  sources=dict(self.sources);sources[v.SOURCE_LOCAL]+=b'\n'
  with self.assertRaises(ValueError):self.check(sources=sources)
 def test_18_missing_callback_transition(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'].pop(4))
 def test_19_rewrite_to_different_task_callback(self):
  self.reject(lambda j:next(e for e in j['rows'][0]['typed_indirect_edges']if e['kind']=='callback_edge'and e['callee']==0x0808CA34).update(to=0x0808CA5C))
 def test_20_wrong_hook_register(self):self.reject(lambda j:next(e for e in j['rows'][0]['typed_indirect_edges']if e['kind']=='hook_edge').update(register=2))
 def test_21_hook_even_target(self):self.reject(lambda j:next(e for e in j['rows'][0]['typed_indirect_edges']if e['kind']=='hook_edge').update(target=0x09378A5A))
 def test_22_switch_index(self):self.reject(lambda j:next(e for e in j['rows'][0]['typed_indirect_edges']if e['kind']=='switch_edge').update(index=5))
 def test_23_returned_task_id_clobber(self):self.mutate(0x0808C86E,2,0x2000)
 def test_24_task_id_store_wrong_field(self):self.mutate(0x0808C870,2,v.half(self.raw,0x0808C870)^64)
 def test_25_setter_wrong_id_field(self):self.mutate(0x0808CA3C,2,v.half(self.raw,0x0808CA3C)^64)
 def test_26_setter_argument_clobber(self):self.mutate(0x0808CA3E,2,0x2000)
 def test_27_setter_wrong_stride(self):self.mutate(0x0808CA42,2,v.half(self.raw,0x0808CA42)^64)
 def test_28_setter_wrong_task_field(self):self.mutate(0x0808CA46,2,v.half(self.raw,0x0808CA46)^64)
 def test_29_constructor_other_global(self):self.mutate(0x0808C848,4,0x02039700,lambda j:next(w for w in j['consumer_literals']if w['label']=='storage_constructor_gStorage').update(value=0x02039700))
 def test_30_setter_other_global(self):self.mutate(0x0808CA58,4,0x02039700,lambda j:next(w for w in j['consumer_literals']if w['label']=='storage_setter_gStorage').update(value=0x02039700))
 def test_31_setter_other_table(self):self.mutate(0x0808CA54,4,0x030050F8,lambda j:next(w for w in j['consumer_literals']if w['label']=='storage_setter_gTasks').update(value=0x030050F8))
 def test_32_wrong_main_callback(self):self.mutate(0x0808C898,4,0x0808CA5D,lambda j:next(w for w in j['consumer_literals']if w['label']=='storage_constructor_main_target').update(value=0x0808CA5D))
 def test_33_wrong_main_dispatch_target(self):self.mutate(0x0808C804,2,v.half(self.raw,0x0808C804)^1)
 def test_34_each_new_consumer_halfword_resealed(self):
  for label,(a,n)in v.NEW_WINDOWS.items():
   for pc in range(a,a+n,2):
    with self.subTest(label=label,address=hex(pc)):self.mutate(pc,2,v.half(self.raw,pc)^1)
 def test_35_hook_pointer_register_resealed(self):self.mutate(0x0808CD4A,2,0x4710)
 def test_36_switch_bounding_register(self):self.mutate(0x0808D7CE,2,v.half(self.raw,0x0808D7CE)^256)
 def test_37_CreateTask_id_return_regression(self):self.mutate(0x08076BEA,2,0x2000)
 def test_38_RunTasks_pointer_clobber(self):self.mutate(0x08076D28,2,0x2100)
 def test_39_slot_rehash_wrong_target(self):self.mutate(0x08163068+4*60,4,0x0808C821,lambda j:j['rows'][0]['root']['slot'].update(value=0x0808C821))
 def test_40_duplicate_source_binding(self):self.reject(lambda j:j['source_bindings'].update(extra=next(iter(j['source_bindings'].values()))))
if __name__=='__main__':unittest.main(verbosity=2)
