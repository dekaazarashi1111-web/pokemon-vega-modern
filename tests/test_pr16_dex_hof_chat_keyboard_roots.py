"""chat1hitの新scopeだけ。実constructor/登録/serializer/consumerを反証する。"""
import copy,hashlib,unittest
from unittest import mock
import pr16_dex_hof_chat_keyboard_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,raw,address):self.raw,self.offset=raw,address-0x08000000
 def __len__(self):return len(self.raw)
 def __getitem__(self,s):
  data=bytearray(self.raw[s])
  if s.start<=self.offset<s.stop:data[self.offset-s.start]^=1
  return bytes(data)
def reseal(obj,raw):
 if isinstance(obj,dict):
  if {'address','size','sha256'}<=obj.keys():obj['sha256']=hashlib.sha256(v.chunk(raw,obj['address'],obj['size'])).hexdigest()
  for value in obj.values():reseal(value,raw)
 elif isinstance(obj,list):
  for value in obj:reseal(value,raw)
class ChatKeyboardTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('保存reviewのJSON読戻しと新scope sparse FIXTUREが必要')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def test_01_one_four_byte_region_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);rows,p=self.check();self.assertEqual([(r.start,r.end,r.kind)for r in rows],[(0x083E112C,0x083E1130,v.KIND)]);self.assertEqual(self.inherited,before);self.assertFalse(p['donor_eligible'])
 def test_02_complete_serializer_two_texts(self):
  self.assertEqual([t['text_ja']for t in v.TEXTS],['かきくけこ','さしすせそ'])
  for t in v.TEXTS:
   b=v.serialize(t['text_ja'],self.sources);self.assertEqual(len(b),6);self.assertEqual(b[-1],255);self.assertNotIn(255,b[:-1]);self.assertEqual(v.identity(b),{k:t[k]for k in('size','sha256')})
 def test_03_callback_same_slot(self):
  events=self.check()[1]['composition']['root_events'];self.assertIn(('main_store',v.MAIN+4,0x08128E19),events);self.assertEqual(events.count(('main_read',v.MAIN+4,0x08128E19)),7);self.assertEqual(events.count(('main_bx',0x08128E19)),7)
 def test_04_subtask_same_slot(self):
  events=self.check()[1]['composition']['root_events'];self.assertIn(('subtask_store',v.DISPLAY,0x0812A5C1),events);self.assertEqual(events.count(('subtask_read',v.DISPLAY,0x0812A5C1)),6);self.assertEqual(events.count(('subtask_bx',0x0812A5C1,v.DISPLAY+5)),6)
 def test_05_page_and_state_real_writes(self):
  events=self.check()[1]['composition']['root_events'];self.assertIn(('page_store',v.WORK+16,0),events);self.assertIn(('state_store',v.DISPLAY+5,0),events);self.assertEqual([e[2]for e in events if e[0]=='state_read'],list(range(6)))
 def test_06_complete_table_loop_not_host_pointer(self):
  events=self.check()[1]['composition']['root_events'];self.assertEqual([e for e in events if e[0]=='text_table_read'],[('text_table_read',k,0x0841A12C+4*k,0x083E1123+6*k)for k in range(3)])
 def test_07_real_printer_and_all_12_reads(self):
  first=v._compose(self.raw);self.assertEqual(first['reads'],[(t['address']+k,1)for t in v.TEXTS for k in range(6)]);self.assertEqual(first['steps'],2927);self.assertEqual(v.ROOT['actual_byte_reader'],0x0800580E)
 def test_08_every_instruction_byte(self):
  for ins in v.INS.values():
   for a in range(ins.address,ins.address+ins.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_09_every_table_and_dispatch_field_byte(self):
  for a,n,_ in [*v.CORE_FIELDS,*[(a,4,value)for a,value in v.LITERALS.items()]]:
   for k in range(n):
    with self.subTest(address=a+k),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+k),self.sources)
 def test_10_every_complete_text_byte(self):
  for t in v.TEXTS:
   for a in range(t['address'],t['address']+t['size']):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_11_all_protected_bytes_resealed(self):
  for row in v.FIXED_WINDOWS:
   for a in range(row['address'],row['address']+row['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);reseal(r,raw);reseal(i,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,inherited=i)
 def test_12_each_source_mutation_and_reseal(self):
  for name,data in self.sources.items():
   sources={**self.sources,name:data+b'\n'};r=copy.deepcopy(self.review);r['source_bindings'][name].update(v.identity(sources[name]))
   with self.subTest(name=name),self.assertRaises(ValueError):self.check(review=r,sources=sources)
 def test_13_source_set_closed(self):
  for sources in ({**self.sources,'extra':b''},{k:b for k,b in self.sources.items()if k!='pret-charmap.txt'}):
   with self.assertRaises(ValueError):self.check(sources=sources)
 def test_14_whole_current_identity_gate(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_15_current_wrapper_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value=('regions','proof'))as inner:self.assertEqual(v.regions(*FIXTURE),('regions','proof'));inner.assert_called_once()
 def test_16_candidate_and_diagnostic_never_interchange(self):
  self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE));self.reject_review(lambda r:r.update(required_candidate=v.DIAGNOSTIC));i=copy.deepcopy(self.inherited);i['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_17_every_review_claim_boolean(self):
  for key,value in v.CLAIMS.items():
   if type(value)is bool:
    with self.subTest(key=key):self.reject_review(lambda r:r['claims'].update({key:not value}))
 def test_18_every_fixture_condition(self):
  for key,value in v.FIXTURE_CONDITIONS.items():
   fixture={**v.FIXTURE_CONDITIONS,key:value+1}
   with self.subTest(key=key),self.assertRaises(ValueError):v.compose_selected(self.raw,fixture=fixture)
   self.reject_review(lambda r:r['fixture_conditions'].update({key:value+1}))
 def test_19_fixture_type_and_extra_fields(self):
  for fixture in ({**v.FIXTURE_CONDITIONS,'multiplayer_id':False},{**v.FIXTURE_CONDITIONS,'text_pointer':v.TEXTS[0]['address']}):
   with self.assertRaises(ValueError):v.compose_selected(self.raw,fixture=fixture)
 def test_20_schema_and_manifest_order(self):
  self.reject_review(lambda r:r.update(extra=True));self.reject_review(lambda r:r.update(schema_version=True));self.reject_review(lambda r:r['windows'].reverse());self.reject_review(lambda r:r['texts'].reverse())
 def test_21_witness_exact_geometry(self):
  e=v.evidence_template(v.HITS[0]);self.assertEqual(v.witness_geometry(e),(v.HITS[0],4))
  for key,value in [('root_verified',False),('all_hit_bytes_consumed',False),('pointer_host_seeded',True),('donor_eligible',True),('full_story_reachability_claimed',True),('extra',True)]:
   bad={**e,key:value}
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(bad)
  bad=copy.deepcopy(e);bad['classified_window']['size']=12
  with self.assertRaises(ValueError):v.witness_geometry(bad)
 def test_22_all_root_fields_closed(self):
  for key,value in v.ROOT.items():
   if type(value)is int:
    with self.subTest(key=key):self.reject_review(lambda r:r['root'].update({key:value+2}))
  self.reject_review(lambda r:r['root'].update(selected_indexes=[0,1]));self.reject_review(lambda r:r['root'].update(selected_cells=[0x0841A12C,0x0841A130]))
 def test_23_unknown_hit_full_identity(self):
  for key,value in [('accepted',True),('accepted',0),('classification','DATA'),('owner_candidates',['x']),('size',True),('size',12),('kind','POINTER')]:
   r=copy.deepcopy(self.review);i=copy.deepcopy(self.inherited);r['hits'][0][key]=value;i['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(review=r,inherited=i)
 def test_24_duplicate_and_missing_hits(self):
  for hits in ([],self.inherited['hits']*2):
   i={**self.inherited,'hits':hits}
   with self.assertRaises(ValueError):self.check(inherited=i)
 def test_25_unrelated_parent_retained(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(dict(address=0x08000000,accepted=True));before=copy.deepcopy(i);self.check(inherited=i);self.assertEqual(i,before)
 def test_26_live_page_field_clobber(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,{0x08128DB0:[(v.WORK+16,1,1)]})
 def test_27_live_callback_slot_clobber(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,{0x08000512:[(v.MAIN+4,4,0)]})
 def test_28_live_subtask_slot_clobber(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,{0x08000512:[(v.DISPLAY,4,0)]})
 def test_29_live_state_field_clobber(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,{0x0812A5C4:[(v.DISPLAY+5,1,5)]})
 def test_30_nonlive_memory_writes_allowed(self):
  self.assertEqual(v.compose_selected(self.raw,{0x08000512:[(0x02027000,4,123)]})['complete_consumed_bytes'],12)
 def test_31_work_epoch_invalidation(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x08128DB0:{'freed':[v.WORK]}})
 def test_32_display_epoch_invalidation(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x0812A5C4:{'freed':[v.DISPLAY]}})
 def test_33_heap_epoch_invalidation(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x0812A5C4:{'heap_reinitialized':True}})
 def test_34_window_epoch_invalidation(self):
  for site in(0x0812A462,0x0812B130,0x08005B2C):
   with self.subTest(site=site),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={site:{'window_invalidated':True}})
 def test_35_unknown_site_or_epoch_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0:[(0x02027000,1,0)]})
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0:{'freed':[v.WORK]}})
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x0812A5C4:{'unknown':True}})
 def test_36_contract_mutation(self):
  for key in v.CONTRACT:
   with self.subTest(key=key),self.assertRaises(ValueError):v.compose_selected(self.raw,contract={**v.CONTRACT,key:'host seed'})
  self.reject_review(lambda r:r['input_contract'].update(extra=True))
 def test_37_all_boundaries_project_nonlive_away(self):
  p=v.compose_selected(self.raw);self.assertTrue(p['nonlive_ram_erased_at_each_boundary']);self.assertTrue(p['conditional_call_groups']);self.assertTrue(all(g['normal_abi_return_required']and not g['effects_discharged']for g in p['conditional_call_groups']))
 def test_38_graphics_prefix_is_conditional(self):
  groups=v.compose_selected(self.raw)['conditional_call_groups'];self.assertTrue(any(g['target']==0x0812B414 and not g['effects_discharged']for g in groups));self.assertFalse(v.CLAIMS['all_prefix_natural_execution_claimed'])
 def test_39_us_stringcopy_not_inserted_into_jp_print(self):
  a,ss=v.NEW_BLOCK_SPECS['print_keyboard_page'];self.assertNotIn(['call',0x08008900],ss);self.assertIn(['call',0x0812ED24],ss);self.assertIn(['spmem',False,1,8],ss)
 def test_40_full_root_encoder_blocks(self):
  self.assertEqual(len(v.NEW_BLOCK_SPECS),33)
  for a,ss in v.NEW_BLOCK_SPECS.values():
   rows=v.party.block(a,ss);data=b''.join(v.encoded(i)for i in rows);self.assertEqual(data,v.chunk(self.raw,a,len(data)))
 def test_41_saved_json_shapes(self):
  self.assertIs(type(self.review['texts']),list);self.assertIs(type(self.review['windows']),list);self.assertIs(type(self.review['hits']),list);self.assertEqual(self.review['fixture_conditions'],v.FIXTURE_CONDITIONS)
 def test_42_text_extent_not_broadened(self):
  self.reject_review(lambda r:r['texts'][0].update(size=7));self.reject_review(lambda r:r['windows'][0].update(size=r['windows'][0]['size']+2));self.assertEqual(v.HELD_HITS,())
