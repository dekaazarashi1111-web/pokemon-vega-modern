"""新Hall PC根だけを反証。原本I/O・旧suite実行はimport時に行わない。"""
import copy,hashlib,unittest
import pr16_dex_hof_space_roots as v
FIXTURE=None

def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():
   a=obj['address']-0x08000000;n=obj['size'];obj['sha256']=hashlib.sha256(raw[a:a+n]).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)

class RemainingEngineTests(unittest.TestCase):
 def setUp(self):
  if FIXTURE is None:raise RuntimeError('explicit fixture injection required')
  self.raw,self.inherited,self.review,self.sources=FIXTURE
 def check(self,j=None,r=None,inh=None,src=None):return v._regions(self.raw if r is None else r,self.inherited if inh is None else inh,self.review if j is None else j,self.sources if src is None else src)
 def reject(self,edit):
  j=copy.deepcopy(self.review);edit(j)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(j)
 def mutate(self,a,n,value,edit=None):
  raw=bytearray(self.raw);i=a-0x08000000;value=value.to_bytes(n,'little');self.assertNotEqual(raw[i:i+n],value);raw[i:i+n]=value;raw=bytes(raw)
  j=copy.deepcopy(self.review);inh=copy.deepcopy(self.inherited);reseal(j,raw);reseal(inh,raw)
  if edit:edit(j)
  with self.assertRaises((ValueError,KeyError,StopIteration)):self.check(j,raw,inh)
 def test_01_new_hofpc_window_only(self):
  rows,proof=self.check();self.assertEqual(proof['count'],1);self.assertEqual((rows[0].start,rows[0].end),(0x080F3C3E,0x080F3C44))
 def test_02_current_identity_is_mandatory(self):
  inherited=copy.deepcopy(self.inherited);inherited['candidate']=dict(size=0,sha256='0'*64)
  with self.assertRaises(ValueError):v.regions(self.raw,inherited,self.review,self.sources)
 def test_03_exact_frontier_original(self):
  j=copy.deepcopy(self.inherited);next(r for r in j['hits']if r['address']==v.HITS[0])['accepted']=True
  with self.assertRaises(ValueError):self.check(inh=j)
 def test_04_changed_original_hit(self):self.reject(lambda j:j['rows'][0]['hit'].update(target=0x09FED000))
 def test_05_wrong_root_index(self):self.reject(lambda j:j['rows'][0]['root'].update(special_id=262))
 def test_06_symbol_not_root(self):self.reject(lambda j:j['rows'][0]['root'].update(kind='pinned_symbol'))
 def test_07_missing_root(self):self.reject(lambda j:j['rows'][0]['instruction_path'].pop(0))
 def test_08_skipped_instruction(self):self.reject(lambda j:j['rows'][0]['instruction_path'].pop(8))
 def test_09_whole_function_not_classified(self):self.reject(lambda j:j['rows'][0].update(whole_function_range_classified=True))
 def test_10_no_literal_as_code(self):self.reject(lambda j:j['rows'][0].update(literal_pool_included=True))
 def test_11_no_extra_unknown(self):self.reject(lambda j:j['rows'].append(copy.deepcopy(j['rows'][0])))
 def test_12_no_extra_instruction_extent(self):self.reject(lambda j:j['rows'][0]['instruction_window'].update(size=8))
 def test_13_missing_store_edge(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'].pop())
 def test_14_wrong_task_id_register(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'][-1].update(task_register=5))
 def test_15_wrong_stride(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'][-1].update(stride=36))
 def test_16_callback_pointer_loaded_into_wrong_register(self):self.mutate(0x080F3AB8,2,0x4903)
 def test_17_callback_store_wrong_field(self):self.mutate(0x080F3ABA,2,0x6048)
 def test_18_task_index_from_wrong_argument(self):self.mutate(0x080F3A08,2,0x0608)
 def test_19_task_index_clobber(self):self.mutate(0x080F3A0A,2,0x2600)
 def test_20_task_index_coefficient(self):self.mutate(0x080F3AB2,2,0x0109)
 def test_21_task_table_wrong_value_even_resealed(self):
  self.mutate(0x080F3AC4,4,0x030050F8,lambda j:j['rows'][0]['typed_indirect_edges'][-1]['table_literal'].update(value=0x030050F8))
 def test_22_callback_wrong_value_even_resealed(self):self.mutate(0x080F3AC8,4,0x080F3CC1)
 def test_23_constructor_scheduler_wrong_literal(self):self.mutate(0x080F3A00,4,0x080F2D3D,lambda j:next(w for w in j['consumer_literals']if w['label']=='hof_pc_constructor_idle_target').update(value=0x080F2D3D))
 def test_24_constructor_argument_clobber(self):self.mutate(0x080F39E6,2,0x2000)
 def test_25_idle_scheduler_call_broken(self):self.mutate(0x080F2D22,2,0x2000)
 def test_26_missing_idle_window(self):self.reject(lambda j:j.update(consumer_windows=[w for w in j['consumer_windows']if w['label']!='hof_pc_idle_scheduler']))
 def test_27_wrong_switch_bound(self):self.mutate(0x080F38E4,2,0x2804)
 def test_28_wrong_switch_slot(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'][2].update(index=4))
 def test_29_task_entry_must_be_registered(self):self.reject(lambda j:j['rows'][0]['typed_indirect_edges'][-1].update(task_entry=0x080F2ED4))
 def test_30_hall_source_identity(self):
  sources=dict(self.sources);sources['pret-hall_of_fame.c']+=b'\n'
  with self.assertRaises(ValueError):self.check(src=sources)
 def test_31_source_role_missing(self):self.reject(lambda j:j.update(source_bindings={k:v for k,v in j['source_bindings'].items()if v['local']!='pret-hall_of_fame.c'}))
 def test_32_call_only_halfword(self):self.reject(lambda j:next(p for p in j['rows'][0]['instruction_path']if p['address']==0x080F3C3E).update(size=2))
 def test_33_hit_window_resealed_data_write_not_BL(self):self.mutate(0x080F3C3E,2,0x6000)
 def test_34_success_predecessor_required(self):self.reject(lambda j:j['rows'][0]['instruction_path'].remove(next(p for p in j['rows'][0]['instruction_path']if p['address']==0x080F3AB8)))
 def test_35_each_new_consumer_halfword_resealed(self):
  # Every scheduler/constructor instruction, including former hash-only tails, must be semantically constrained.
  count=0
  for a in list(range(0x080F39DA,0x080F39F2,2))+list(range(0x080F2D20,0x080F2D3A,2)):
   value=int.from_bytes(self.raw[a-0x08000000:a-0x08000000+2],'little')
   with self.subTest(address=a):self.mutate(a,2,value^1)
   count+=1
  self.assertEqual(count,25)

 def test_36_current_wrapper_accepts_only_actual_current_fixture(self):
  if v.identity(self.raw)==v.CANDIDATE:self.assertEqual(v.regions(self.raw,self.inherited,self.review,self.sources)[1]['count'],1)
  else:
   self.assertNotEqual(v.identity(self.raw),v.CANDIDATE)
   with self.assertRaises(ValueError):v.regions(self.raw,self.inherited,self.review,self.sources)
 def test_37_resealed_ASR_is_not_LSR(self):
  original=int.from_bytes(self.raw[0xF3A0A:0xF3A0C],'little');self.mutate(0x080F3A0A,2,(original&0x07FF)|0x1000)
