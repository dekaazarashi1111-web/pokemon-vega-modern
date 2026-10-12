"""急所表の新scopeのみ。source-only sparse fixture、raw ROM保存なし。"""
import copy, hashlib, unittest
from unittest import mock
import pr16_dex_hof_critical_move_list_roots as v
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

class CriticalReaderTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('新scope sparse FIXTUREが必要')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,
   self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def test_01_exact_four_bytes_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);regions,proof=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in regions],[(v.HITS[0],v.HITS[0]+4,v.KIND)])
  self.assertEqual(before,self.inherited);self.assertFalse(proof['donor_eligible'])
 def test_02_independent_source_id_serialization(self):
  proof=self.check()[1]['serialization']
  self.assertEqual(proof['table_bytes'],64)
  self.assertEqual([r['halfword_count']for r in proof['tables']],[26,6])
  self.assertFalse(proof['observed_value_input']);self.assertFalse(proof['uniform_id_offset_used'])
 def test_03_full_reader_path_and_real_loaders(self):
  p=self.check()[1]['composition']
  self.assertEqual(p['instruction_steps'],340);self.assertEqual(len(p['conditional_call_groups']),6)
  self.assertEqual(p['complete_halfword_reads'],32);self.assertEqual(p['consumed_bytes'],64)
  self.assertTrue(p['includes_both_final_terminators']);self.assertTrue(p['nonlive_ram_erased_at_each_boundary'])
  self.assertFalse(p['internal_reader_arguments_host_seeded']);self.assertFalse(p['actual_runtime_execution_observed'])
  self.assertEqual(p['reader_calls'],[(0x090E45A8,1,v.ALWAYS),(0x090E45D8,1,v.HIGH)])
 def test_04_three_complete_halfwords_smallest_hit_geometry(self):
  e=v.evidence_template(v.HITS[0]);self.assertEqual(v.witness_geometry(e),(v.HITS[0],4))
  self.assertEqual([(f['address'],f['size'],f['covered_bytes'])for f in e['complete_halfword_fields']],[(v.HIGH+48,2,1),(v.HIGH+50,2,2),(v.ALWAYS,2,1)])
 def test_05_registered_entry_opaque_and_reader_only(self):
  p=v._compose(self.raw)
  self.assertEqual(p['visited'][0],v.ENTRY);self.assertNotIn(v.STOP,p['visited'])
  self.assertIn(0x090E45A8,p['visited']);self.assertIn(0x090E45D8,p['visited'])
  self.assertEqual(len(p['reads']),32)
 def test_06_all_instruction_bytes_rejected(self):
  for i in v.INS.values():
   for a in range(i.address,i.address+i.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_07_all_literal_registration_bytes_rejected(self):
  for a in v.WORDS:
   for j in range(4):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+j),self.sources)
 def test_08_all_table_bytes_rejected(self):
  for row in v.TABLE_WINDOWS:
   for a in range(row['address'],row['address']+row['size']):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_09_every_protected_byte_resealed_rejected(self):
  for row in v.ALL_WINDOWS:
   for a in range(row['address'],row['address']+row['size']):
    raw=Mutation(self.raw,a);review=copy.deepcopy(self.review);parent=copy.deepcopy(self.inherited)
    reseal(review,raw);reseal(parent,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=review,inherited=parent)
 def test_10_source_complete_identity(self):
  for name,b in self.sources.items():
   sources=dict(self.sources);sources[name]=b+b'\n'
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources=sources)
 def test_11_sources_missing_extra(self):
  for name in self.sources:
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={k:b for k,b in self.sources.items()if k!=name})
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_12_source_reseal_not_authorization(self):
  for name in self.sources:self.reject_review(lambda r:r['source_bindings'][name].update(sha256='0'*64))
 def test_13_closed_review_schema(self):
  self.reject_review(lambda r:r.update(extra=True));self.reject_review(lambda r:r.update(schema_version=True));self.reject_review(lambda r:r.pop('root'))
 def test_14_current_diagnostic_separation(self):
  self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE));self.reject_review(lambda r:r.update(required_candidate=v.DIAGNOSTIC))
  p=copy.deepcopy(self.inherited);p['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=p)
 def test_15_wrapper_rejects_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_16_wrapper_requires_current_identity(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value=('regions','proof'))as inner:
   self.assertEqual(v.regions(*FIXTURE),('regions','proof'));inner.assert_called_once()
 def test_17_witness_claims_closed(self):
  for key,value in v.CLAIMS.items():
   if type(value)is bool:
    bad=v.evidence_template(v.HITS[0]);bad[key]=not value
    with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(bad)
 def test_18_witness_geometry_closed(self):
  for change in(lambda e:e.update(extra=True),lambda e:e.update(root_verified=False),
   lambda e:e['classified_window'].update(size=6),lambda e:e['classified_window'].update(address=v.HITS[0]-1),
   lambda e:e['root'].update(opcode=3),lambda e:e['complete_halfword_fields'][0].update(covered_bytes=2),
   lambda e:e['input_contract'].update(extra='x')):
   bad=v.evidence_template(v.HITS[0]);change(bad)
   with self.assertRaises(ValueError):v.witness_geometry(bad)
 def test_19_review_claims_and_root_closed(self):
  for key,value in v.CLAIMS.items():
   if type(value)is bool:self.reject_review(lambda r:r['claims'].update({key:not value}))
  self.reject_review(lambda r:r['root'].update(dispatch_slot=v.SLOT+4))
 def test_20_parent_all_fields_exact(self):
  for key,value in(('accepted',True),('accepted',0),('classification','CODE'),('owner_candidates',['x']),('size',True),('kind','POINTER')):
   p=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);p['hits'][0][key]=value;r['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=p,review=r)
 def test_21_parent_duplicate_or_missing(self):
  for change in(lambda p:p['hits'].append(copy.deepcopy(p['hits'][0])),lambda p:p['hits'].pop()):
   p=copy.deepcopy(self.inherited);change(p)
   with self.assertRaises(ValueError):self.check(inherited=p)
 def test_22_unrelated_parent_retained(self):
  p=copy.deepcopy(self.inherited);p['hits'].append(dict(address=0x08000000,accepted=True));before=copy.deepcopy(p)
  self.check(inherited=p);self.assertEqual(before,p)
 def test_23_windows_closed(self):
  self.reject_review(lambda r:r['windows'].reverse());self.reject_review(lambda r:r['windows'][0].update(size=6))
 def test_24_profiles_closed(self):
  for key,value in v.PROFILE.items():
   p=copy.deepcopy(v.PROFILE);p[key]=not value if type(value)is bool else value+1
   with self.subTest(key=key),self.assertRaises(ValueError):v.compose_selected(self.raw,profile=p)
 def test_25_contract_closed(self):
  contract=copy.deepcopy(v.CONTRACT);contract['minimum_ja']='whole tables'
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract=contract)
  self.reject_review(lambda r:r['input_contract'].update(extra=True))
 def test_26_every_future_live_byte_rejected(self):
  for g in v.compose_selected(self.raw)['conditional_call_groups']:
   fields=[[r['address'],r['size']]for r in g['required_fields']]
   for a,n in fields:
    for j in range(n):
     with self.subTest(site=g['site'],address=a+j),self.assertRaises(ValueError):v.preservation_contract(fields,[(a+j,1,0)])
 def test_27_nonlive_mutation_each_boundary_allowed(self):
  for site in v.EXTERNAL:
   p=v.compose_selected(self.raw,opaque_writes={site:[(0x02011000,4,0xAABBCCDD)]})
   self.assertEqual(p['status'],'PASS_CONDITIONAL_CRITICAL_LIST_CONSUMER')
 def test_28_current_move_not_host_overwritten(self):
  for site in v.EXTERNAL:
   with self.subTest(site=site),self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={site:[(v.MOVE,2,1)]})
 def test_29_same_context_and_stack_epoch(self):
  for site in v.EXTERNAL:
   for event in('battle_context_epoch_changed','stack_epoch_changed'):
    with self.subTest(site=site,event=event),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={site:{event:True}})
 def test_30_unknown_boundaries_and_events_rejected(self):
  for kwargs in({'opaque_writes':{0:[(0x02011000,1,0)]}},{'epoch_events':{0:{}}},
   {'epoch_events':{0x090E4438:{'other':False}}},{'epoch_events':{0x090E4438:{'stack_epoch_changed':0}}}):
   with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v.compose_selected(self.raw,**kwargs)
 def test_31_write_geometry_closed(self):
  for write in((True,1,0),(0x02011000,0,0),(0x02011000,8,0),(0xFFFFFFFF,4,0),(0x02011000,1,256)):
   with self.subTest(write=write),self.assertRaises(ValueError):v.preservation_contract([],writes=[write])
 def test_32_reader_early_return_first_middle_last(self):
  tables,_=v.source_tables(self.sources)
  for a,b in tables.items():
   values=[int.from_bytes(b[j:j+2],'little')for j in range(0,len(b),2)]
   for index in (0,len(values)//2,len(values)-2):
    machine=v.Machine(self.raw,v.READER,{0:values[index],1:a},{},instructions=v.INS,trace=[]).run()
    self.assertEqual(machine.reg[0],1);self.assertEqual(len(machine.table_reads),index+1)
 def test_33_reader_terminator_comparison_precedes_member(self):
  machine=v.Machine(self.raw,v.READER,{0:v.TERMINATOR,1:v.HIGH},{},instructions=v.INS,trace=[]).run()
  self.assertEqual(machine.reg[0],0);self.assertEqual(len(machine.table_reads),26)
 def test_34_byte_consumption_order_and_no_extra_reads(self):
  reads=v._compose(self.raw)['reads']
  self.assertEqual([(a,n)for _,a,n,_ in reads],[(v.ALWAYS+2*j,2)for j in range(6)]+[(v.HIGH+2*j,2)for j in range(26)])
  self.assertEqual(reads[5][3],v.TERMINATOR);self.assertEqual(reads[-1][3],v.TERMINATOR)
 def test_35_measurement_is_metadata_only(self):
  rows=v.measure(self.raw);self.assertEqual(rows,v.ALL_WINDOWS)
  self.assertTrue(all(set(r)=={'address','size','sha256'}for r in rows))
 def test_36_incomplete_terminators_fail_before_composition(self):
  for a in(v.HIGH+50,v.ALWAYS+10):
   with mock.patch.object(v,'compose_selected')as compose:
    with self.assertRaises(ValueError):self.check(raw=Mutation(self.raw,a))
    compose.assert_not_called()
