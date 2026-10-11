"""Frontier新scope: independent source-only fixture、最小hit、全byte/reseal/epoch反証。"""
import copy,hashlib,json,unittest
from unittest import mock
import pr16_dex_hof_frontier_records_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,raw,address):self.raw,self.offset=raw,address-0x08000000
 def __len__(self):return len(self.raw)
 def __getitem__(self,s):
  b=bytearray(self.raw[s])
  if s.start<=self.offset<s.stop:b[self.offset-s.start]^=1
  return bytes(b)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for z in obj.values():reseal(z,raw)
 elif isinstance(obj,list):
  for z in obj:reseal(z,raw)
class FrontierTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('source-only FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
  cls.first=v._compose(cls.raw);cls.live=v.live.future_live(cls.first['trace'],len(cls.first['boundaries']))
  cls.access=v.future_access_projection(cls.first['trace'],len(cls.first['boundaries']))
  cls.replay=v._compose(cls.raw,cls.live,future_access=cls.access)
  cls.proof=v.compose_selected(cls.raw)
 def check(self,raw=None,parent=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if parent is None else parent,self.review if review is None else review,self.sources if sources is None else sources)
 def reject(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def seed_reject(self,a,n,val):
  original=v.memory
  def changed():
   m=original();v.rt.setmem(m,a,n,val);return m
  with mock.patch.object(v,'memory',side_effect=changed),self.assertRaises(ValueError):v.compose_selected(self.raw)
 def test_01_minimum_fourbyte_only_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);regions,proof=self.check();self.assertEqual(before,self.inherited)
  self.assertEqual(len(regions),1);self.assertEqual(v.witness_geometry(regions[0].evidence),(v.HIT,4))
  self.assertEqual(proof['count'],1);self.assertFalse(proof['donor_eligible'])
 def test_02_complete_current_max_and_eos(self):
  self.assertEqual(self.proof['text_reads'],[(a+j,1)for a in v.TARGETS for j in range(len(v.TEXT_PARTS[a]))])
  self.assertEqual(self.proof['complete_consumed_bytes'],15)
  self.assertEqual(v.TEXT_PARTS[v.TARGETS[0]].count(254),1);self.assertTrue(self.proof['includes_both_eos'])
 def test_03_real_task_writer_reader(self):
  self.assertIn((0x08076BCE,v.TASKS,4,v.TASK|1),self.first['writes'])
  self.assertEqual(self.first['task_dispatch'],[(v.TASKS,0)])
  self.assertIn(0x08076CB8,self.first['visited'])
  self.assertLess(self.first['visited'].index(0x08076BCE),self.first['visited'].index(0x08076D28))
 def test_04_real_main_setter_state_zero(self):
  self.assertIn((0x08000546,v.MAIN+4,4,v.CB|1),self.first['writes'])
  self.assertIn((0x08000550,v.STATE,1,0),self.first['writes'])
  self.assertEqual(self.first['main_dispatch'],[(v.MAIN+4,v.CB|1)]*8)
 def test_05_state0_to7_no_host_seed(self):
  self.assertEqual(v.rt.getmem(v.memory(),v.STATE,1),165)
  self.assertEqual(self.first['states'],list(range(8)))
  self.assertEqual([x[3]for x in self.first['writes']if x[0]==0x09103F22],list(range(1,8)))
  self.assertFalse(self.proof['state7_host_seeded'])
 def test_06_all_selected_caller_prefix_and_clean_windows(self):
  self.assertEqual(self.first['clean_windows'],list(range(21)))
  self.assertEqual(self.first['printers'],[(0x09103870,5,v.TARGETS[0]),(0x09103886,6,v.TARGETS[1])])
  self.assertIn(0x091037D8,self.first['visited']);self.assertIn(0x09103EAE,self.first['visited'])
 def test_07_actual_current_printer_and_font0(self):
  for a in(0x0812ED24,0x08002CF0,0x09378A30,0x08002E5E,0x08005348,0x0800580E,0x0800584C,0x08002DAE):self.assertIn(a,self.first['visited'])
  self.assertNotIn(0x080053B4,self.first['visited'])
 def test_08_nonlive_erasure_same_trace(self):
  for k in('steps','visited','states','writes','reads','printers','clean_windows','task_dispatch','main_dispatch','boundaries'):self.assertEqual(self.first[k],self.replay[k])
  self.assertTrue(self.proof['nonlive_ram_erased_at_every_boundary'])
 def test_09_all_instruction_bytes_independent_encoder(self):
  for i in v.INS.values():
   for a in range(i.address,i.address+i.size):
    with self.subTest(a=hex(a)),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a))
 def test_10_all_source_scalar_table_text_bytes_bound(self):
  for a,b in v.fixed_parts().items():
   if a in v.INS:continue
   for j in range(len(b)):
    with self.subTest(a=hex(a+j)),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a+j))
 def test_11_all_protected_bytes_and_self_consistent_reseal_rejected(self):
  total=0
  for w in v.ALL_WINDOWS:
   for a in range(w['address'],w['address']+w['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);p=copy.deepcopy(self.inherited);reseal(r,raw);reseal(p,raw)
    with self.subTest(a=hex(a)),self.assertRaises(ValueError):self.check(raw=raw,parent=p,review=r)
    total+=1
  self.assertEqual(total,sum(w['size']for w in v.ALL_WINDOWS))
 def test_12_sources_full_identity(self):
  for key in self.sources:
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(sources={**self.sources,key:self.sources[key]+b'\n'})
 def test_13_source_set_missing_extra(self):
  for key in self.sources:
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(sources={k:b for k,b in self.sources.items()if k!=key})
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_14_source_metadata_reseal_rejected(self):
  for name in self.sources:
   for key in('sha256','git_blob_sha','commit','source','repository','url'):
    self.reject(lambda r:r['source_bindings'][name].update({key:'changed'}))
 def test_15_review_closed(self):
  self.reject(lambda r:r.update(extra=True));self.reject(lambda r:r.update(schema_version=True));self.reject(lambda r:r.pop('root'))
 def test_16_source_layout_windows_and_height_caveat(self):
  x=v.source_semantics(self.sources);self.assertEqual(x['frontier_struct_size'],20)
  self.assertEqual(x['window_count'],21);self.assertEqual(x['window_template_serialized_bytes'],176)
  self.assertEqual((x['font0_height_observed_resource_condition'],x['font0_height_public_english_source']),(12,13))
  self.assertFalse(x['font0_height_independent_source_value']);self.assertFalse(x['static_decode_used_as_semantic_source'])
 def test_17_current_diagnostic_distinct(self):
  self.reject(lambda r:r.update(required_candidate=v.DIAGNOSTIC));self.reject(lambda r:r.update(diagnostic_input=v.CANDIDATE))
  p=copy.deepcopy(self.inherited);p['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(parent=p)
 def test_18_regions_full_identity_gate_before_delegate(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as f:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   f.assert_not_called()
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value='ok')as f:self.assertEqual(v.regions(*FIXTURE),'ok')
 def test_19_all_claims_closed_in_review_witness(self):
  for k,x in v.CLAIMS.items():
   self.reject(lambda r:r['claims'].update({k:not x}));e=v.evidence_template(v.HIT);e[k]=not x
   with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_20_geometry_closed(self):
  for field,val in [('size',15),('address',v.TARGETS[0]),('size',True)]:
   e=v.evidence_template(v.HIT);e['classified_window'][field]=val
   with self.assertRaises(ValueError):v.witness_geometry(e)
  for h in(v.HIT+1,True,str(v.HIT)):
   with self.assertRaises(ValueError):v.evidence_template(h)
 def test_21_parent_rows_all_fields_and_duplicates(self):
  for k,x in [('accepted',True),('accepted',0),('classification','data'),('owner_candidates',['x']),('size',True),('target',0)]:
   p=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);p['hits'][0][k]=x;r['hits'][0][k]=x
   with self.subTest(key=k),self.assertRaises(ValueError):self.check(parent=p,review=r)
  for action in(lambda p:p['hits'].pop(),lambda p:p['hits'].append(copy.deepcopy(p['hits'][0]))):
   p=copy.deepcopy(self.inherited);action(p)
   with self.assertRaises(ValueError):self.check(parent=p)
 def test_22_unrelated_hit_untouched(self):
  p=copy.deepcopy(self.inherited);p['hits'].append(dict(address=0x09099D3D,accepted=False));before=copy.deepcopy(p);self.check(parent=p);self.assertEqual(before,p)
 def test_23_window_order_and_size_closed(self):
  self.reject(lambda r:r['windows'].reverse());self.reject(lambda r:r['windows'][0].update(size=1));self.reject(lambda r:r['windows'].pop())
 def test_24_profiles_closed(self):
  for k,x in v.PROFILE.items():
   p=copy.deepcopy(v.PROFILE);p[k]=not x if type(x)is bool else x+1
   with self.subTest(k=k),self.assertRaises(ValueError):v.compose_selected(self.raw,profile=p)
  c=copy.deepcopy(v.CONTRACT);c['task_ja']='pretend whole prefix successful'
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract=c)
 def test_25_every_future_live_byte_preserved(self):
  for g,fields in zip(self.replay['groups'],self.live):
   for a,n in fields:
    for j in range(n):
     with self.subTest(boundary=g['index'],a=hex(a+j)),self.assertRaises(ValueError):v.preserve(fields,[(a+j,1,0)],required_epochs=g['required_epochs'])
 def test_26_each_boundary_live_write_replay_rejected(self):
  for g in self.replay['groups']:
   if not g['required_fields']:continue
   key=(g['site'],g['target']);a=g['required_fields'][0]['address']
   with self.subTest(boundary=g['index']),self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={key:[(a,1,0)]})
 def test_27_each_boundary_nonlive_write_is_erased(self):
  keys=set(self.first['boundaries']);changes={k:[(0x02018000,4,0xDEADBEEF)]for k in keys}
  actual=v.compose_selected(self.raw,opaque_writes=changes)
  self.assertEqual(actual['text_reads'],self.proof['text_reads']);self.assertEqual(actual['visited_identity'],self.proof['visited_identity'])
 def test_28_every_required_resource_epoch_rejected(self):
  seen=set()
  for g in self.replay['groups']:
   for event in g['required_epochs']:
    key=(g['site'],g['target']);unique=(key,event)
    if unique in seen:continue
    seen.add(unique)
    with self.subTest(key=key,event=event),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={key:{event:True}})
 def test_29_generation_and_retirement_epoch_scope(self):
  by={g['role']:g for g in self.replay['groups']}
  for role in('ScriptReadHalfword','Calloc20'):self.assertFalse(by[role]['same_allocation_epoch_required'])
  self.assertFalse(by['InitWindows']['same_window_epoch_required']);self.assertFalse(by['ResetTasks']['same_task_slot_epoch_required'])
  self.assertTrue(by['same_slot_RunTasks_API']['same_task_slot_epoch_required']);self.assertTrue(by['CopyGlyphToWindow']['same_printer_epoch_required'])
  self.assertFalse(by['GetFontAttribute_spacing']['same_printer_epoch_required'])
 def test_30_irrelevant_old_epochs_do_not_block(self):
  events={(0x0910364E,0x08002BB0):{'allocation_epoch_changed':True},(0x09103FB8,0x08003AF0):{'window_epoch_changed':True},(0x09103EFE,0x08076B54):{'task_slot_epoch_changed':True}}
  actual=v.compose_selected(self.raw,epoch_events=events);self.assertEqual(actual['text_reads'],self.proof['text_reads'])
 def test_31_epoch_access_includes_future_writes(self):
  trace=[('boundary',0,0),('write',0x02010000,4),('read',0x02010000,4)]
  self.assertEqual(v.live.future_live(trace,1),[[]]);self.assertEqual(v.future_access_projection(trace,1),[[[0x02010000,4]]])
 def test_32_unknown_boundaries_events_invalid_writes_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={(1,2):[(0,1,0)]})
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={(0x0910364E,0x08002BB0):{'extra':True}})
  for write in[(-1,1,0),(1<<32,1,0),(0,1,256),(0,3,0),(True,1,0)]:
   with self.assertRaises(ValueError):v.preserve([],writes=[write])
 def test_33_real_context_wrong_var_palette_font_rejected(self):
  for a,n,val in[(0x02036FEC,2,1),(0x020379F3,1,128),(0x03003DD0,4,0),(v.MAIN,4,0x09103E5D)]:self.seed_reject(a,n,val)
 def test_34_stale_state_seed_cannot_replace_real_producer(self):
  original=v.memory
  def seeded():
   m=original();v.rt.setmem(m,v.STATE,1,7);return m
  with mock.patch.object(v,'memory',side_effect=seeded):actual=v.compose_selected(self.raw)
  self.assertEqual(actual['state_sequence'],list(range(8)))
 def test_35_actual_runtime_and_donor_limits(self):
  for k in('actual_runtime_execution_observed','full_natural_event_prefix_proven','all_opaque_callee_effects_proven','universal_heap_or_irq_lifetime_proven','full_graphics_success_proven','donor_eligible','retirement_proven'):self.assertFalse(v.CLAIMS[k])
 def test_36_fixture_reconstructs_only_source_parts(self):
  # The workflow injects a complete current ROM into self.raw. Sparse fixture
  # closure belongs to this independently source-generated object only.
  class SourceSparse:
   def __init__(self):
    self.cells={a+j:value for a,b in v.fixed_parts().items()for j,value in enumerate(b)}
   def __len__(self):return v.CANDIDATE['size']
   def __getitem__(self,s):
    if not isinstance(s,slice)or s.step is not None:raise ValueError('slice only')
    addresses=range(0x08000000+s.start,0x08000000+s.stop)
    if any(a not in self.cells for a in addresses):raise ValueError('unbound source-only slice')
    return bytes(self.cells[a]for a in addresses)
  raw=SourceSparse()
  self.assertLess(len(raw.cells),3000)
  for a,b in v.fixed_parts().items():self.assertEqual(v.chunk(raw,a,len(b)),b)
  with self.assertRaises(ValueError):v.chunk(raw,0x08010000,4)
 def test_37_each_boundary_independent_nonlive_erasure(self):
  # Disable erasure everywhere except each selected boundary, using each
  # first-pass memory's populated keys. No ROM scan or branch reseeding.
  all_ram=v.live.coalesce({a+j for kind,a,n in self.first['trace']if kind in('read','write')for j in range(n)})
  for i in range(len(self.live)):
   partial=[all_ram]*len(self.live);partial[i]=self.live[i]
   c=v._compose(self.raw,partial,future_access=self.access)
   with self.subTest(boundary=i):self.assertEqual(c['visited'],self.first['visited']);self.assertEqual(c['reads'],self.first['reads'])
 def test_38_group_compression_preserves_all_boundaries(self):
  self.assertEqual(sum(g['count']for g in self.proof['conditional_call_groups']),len(self.first['boundaries']))
  self.assertNotIn('visited',self.proof);self.assertEqual(self.proof['boundary_count'],131)
  ordered=[{k:v for k,v in g.items()if k!='index'}for g in self.replay['groups']]
  self.assertEqual(self.proof['ordered_boundary_group_identity'],v.identity(json.dumps(ordered,sort_keys=True,separators=(',',':')).encode()))
 def test_39_copy_window_after_last_printer_use(self):
  copies=[g for g in self.replay['groups']if g['role']=='CopyWindowToVram']
  self.assertEqual([g['index']for g in copies],[118,130])
  for g in copies:
   self.assertNotIn('printer_epoch_changed',g['required_epochs'])
   self.assertIn('window_epoch_changed',g['required_epochs'])
   self.assertIn('stack_epoch_changed',g['required_epochs'])
  key=(0x08002DAE,0x08003EEC)
  c=v.compose_selected(self.raw,epoch_events={key:{'printer_epoch_changed':True}})
  self.assertEqual(c['text_reads'],self.proof['text_reads'])
  self.assertEqual(c['visited_identity'],self.proof['visited_identity'])
  for epoch in('window_epoch_changed','stack_epoch_changed'):
   with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={key:{epoch:True}})
  for target,site in((0x080062B4,0x08005AFE),(0x08002FE4,0x08005B2C)):
   groups=[g for g in self.replay['groups']if g['site']==site and g['target']==target]
   self.assertTrue(groups)
   self.assertTrue(all('printer_epoch_changed'in g['required_epochs']for g in groups))
   with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={(site,target):{'printer_epoch_changed':True}})
if __name__=='__main__':unittest.main()
