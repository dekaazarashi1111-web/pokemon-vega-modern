"""新money-rootだけのsource疎fixture反証。ROMを試験で開かない。"""
import copy,hashlib,json,unittest
from unittest import mock
import pr16_dex_hof_money_reward_roots as v
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
class MoneyRewardTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('新money source疎FIXTUREが必要')
  cls.raw,cls.parent,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,parent=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.parent if parent is None else parent,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def test_01_single_minimum_parent_unchanged(self):
  p=copy.deepcopy(self.parent);rows,proof=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in rows],[(v.HIT_CALL,v.HIT_CALL+6,v.KIND)])
  self.assertEqual(self.parent,p);self.assertFalse(proof['donor_eligible']);self.assertEqual(proof['count'],1)
 def test_02_complete_registered_caller(self):
  p=v._compose(self.raw)
  for a in(v.ENTRY,0x080250B8,0x080250C4,v.HOOK,0x080250F6,v.WRAPPER,v.CALC,0x0911A3C4,v.HIT_CALL,v.HIT_CALL+4):self.assertIn(a,p['visited'])
  self.assertEqual(p['steps'],30);self.assertEqual(p['visited'][-2:],[v.HIT_CALL,v.HIT_CALL+4]);self.assertNotIn(v.STOP,p['visited'])
 def test_03_literal_and_two_trainer_reads(self):
  p=v.compose_selected(self.raw)
  rows=[r for r in p['actual_role_reads']if r[1]==v.TRAINER]
  self.assertEqual(rows,[(0x080250BA,v.TRAINER,2,131),(0x0911A3C6,v.TRAINER,2,131)])
  self.assertEqual(p['actual_role_reads'][-1],(v.HIT_CALL+4,0x0911A3FC,4,v.FLAGS))
 def test_04_all_six_instruction_bytes_fetched(self):
  p=v._compose(self.raw);fetch={a+j for a,n in p['fetches']for j in range(n)}
  self.assertLessEqual(set(range(v.HIT_CALL,v.HIT_CALL+6)),fetch);self.assertEqual(v.HITS[0],v.HIT_CALL+1)
 def test_05_two_opaque_boundaries_exact(self):
  p=v.compose_selected(self.raw);g=p['conditional_call_groups']
  self.assertEqual([x['site']for x in g],[0x0911A3B6,v.HIT_CALL]);self.assertEqual(g[0]['return_value'],0)
  self.assertEqual(g[1]['return_value'],'unspecified_u32');self.assertFalse(p['calc_return_value_used'])
  self.assertEqual(p['actual_call_arguments'][1]['arguments'],[131])
 def test_06_minimum_live_projection(self):
  g=v.compose_selected(self.raw)['conditional_call_groups']
  self.assertEqual(g[0]['required_fields'],[dict(address=v.TRAINER,size=2)]);self.assertEqual(g[1]['required_fields'],[])
  self.assertTrue(g[0]['same_trainer_epoch_required']);self.assertFalse(g[1]['same_trainer_epoch_required'])
 def test_07_opaque_effects_not_proven(self):
  p=self.check()[1]
  for key in('hit_callee_effects_proven','actual_runtime_execution_observed','natural_battle_entry_reachability_claimed','full_script_prefix_executed','opaque_callee_effects_proven','universal_heap_or_irq_lifetime_proven','retirement_proven','indirect_reference_completeness_claimed','donor_leased'):self.assertFalse(p[key],key)
  for g in p['composition']['conditional_call_groups']:self.assertFalse(g['effects_discharged']);self.assertTrue(g['normal_abi_return_required'])
 def test_08_all_instruction_byte_mutations(self):
  for i in v.INS.values():
   for a in range(i.address,i.address+i.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a))
 def test_09_all_literal_byte_mutations(self):
  for a in v.WORDS:
   for j in range(4):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+j))
 def test_10_all_protected_bytes_reseal_rejected(self):
  for w in v.ALL_WINDOWS:
   for a in range(w['address'],w['address']+w['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);p=copy.deepcopy(self.parent);reseal(r,raw);reseal(p,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,parent=p)
 def test_11_source_identity_all_fields(self):
  for name,b in self.sources.items():
   for changed in(b+b'\n',b[:-1],b.decode()):
    with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={**self.sources,name:changed})
 def test_12_source_missing_extra(self):
  for name in self.sources:
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={k:b for k,b in self.sources.items()if k!=name})
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_13_source_reseal_rejected(self):
  for name in self.sources:
   b=self.sources[name]+b'\n';r=copy.deepcopy(self.review);r['source_bindings'][name].update(v.identity(b),git_blob_sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest())
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(review=r,sources={**self.sources,name:b})
 def test_14_closed_review_keys_and_version(self):
  for change in(lambda r:r.update(extra=True),lambda r:r.pop('root'),lambda r:r.update(schema_version=True),lambda r:r.update(schema_version=1.0)):
   self.reject_review(change)
 def test_15_every_root_field_fixed(self):
  for key in v.ROOT:self.reject_review(lambda r:r['root'].update({key:None}))
 def test_16_every_claim_fixed(self):
  for key,value in v.CLAIMS.items():
   self.reject_review(lambda r:r['claims'].update({key:not value if type(value)is bool else'changed'}))
 def test_17_every_contract_field_fixed(self):
  for key in v.CONTRACT:self.reject_review(lambda r:r['input_contract'].update({key:'changed'}))
 def test_18_every_profile_field_fixed(self):
  for key in v.PROFILE:self.reject_review(lambda r:r['finite_profile'].update({key:None}))
 def test_19_compose_profiles_exact(self):
  for changed in({'battle_outcome':0},{'trainer_id':True},{'trainer_id':131.0},{'facility_guard_return':1},{'calc_reward_return':0}):
   with self.subTest(changed=changed),self.assertRaises(ValueError):v.compose_selected(self.raw,profile={**v.PROFILE,**changed})
 def test_20_compose_contract_exact(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract={**v.CONTRACT,'extra':True})
 def test_21_witness_minimum_geometry(self):
  e=v.evidence_template(v.HITS[0]);self.assertEqual(v.witness_geometry(e),(v.HIT_CALL,6))
  self.assertEqual([(r['address'],r['size'])for r in e['complete_instructions']],[(v.HIT_CALL,4),(v.HIT_CALL+4,2)])
  for hit in(False,v.HIT_CALL,v.HITS[0]+1):
   with self.assertRaises(ValueError):v.evidence_template(hit)
 def test_22_witness_claims_cannot_expand(self):
  for key,value in v.CLAIMS.items():
   e=v.evidence_template(v.HITS[0]);e[key]=not value if type(value)is bool else'changed'
   with self.subTest(key=key),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_23_witness_geometry_cannot_expand(self):
  for change in(lambda e:e.update(extra=True),lambda e:e.update(root_verified=False),lambda e:e['classified_window'].update(size=4),lambda e:e['classified_window'].update(size=8),lambda e:e['hit'].update(address=v.HIT_CALL),lambda e:e['complete_instructions'][1].update(size=4)):
   e=v.evidence_template(v.HITS[0]);change(e)
   with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_24_every_parent_hit_field_fixed(self):
  for key in self.parent['hits'][0]:
   p=copy.deepcopy(self.parent);p['hits'][0][key]=None
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(parent=p)
 def test_25_parent_duplicate_missing(self):
  for rows in([],self.parent['hits']*2):
   with self.assertRaises(ValueError):self.check(parent={**self.parent,'hits':rows})
 def test_26_parent_unrelated_unchanged(self):
  p=copy.deepcopy(self.parent);p['hits'].append(dict(address=0x08000000,accepted=True));before=copy.deepcopy(p);self.check(parent=p);self.assertEqual(before,p)
 def test_27_windows_closed(self):
  self.reject_review(lambda r:r['windows'].reverse());self.reject_review(lambda r:r['windows'][0].update(size=8));self.reject_review(lambda r:r['windows'].pop())
 def test_28_current_diagnostic_separate(self):
  self.reject_review(lambda r:r.update(required_candidate=v.DIAGNOSTIC));self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
  with self.assertRaises(ValueError):self.check(parent={**self.parent,'candidate':v.DIAGNOSTIC})
 def test_29_wrapper_rejects_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_30_wrapper_current_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value=('regions','proof'))as inner:
   self.assertEqual(v.regions(*FIXTURE),('regions','proof'));inner.assert_called_once()
 def test_31_live_same_value_write_rejected(self):
  for offset in(0,1):
   with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0x0911A3B6:[(v.TRAINER+offset,1,131 if not offset else 0)]})
 def test_32_nonlive_write_per_boundary(self):
  for site in v.EXTERNAL:
   p=v.compose_selected(self.raw,opaque_writes={site:[(0x02015000,4,0xAABBCCDD),(v.OUTCOME,1,0)]});self.assertEqual(p['minimum_executed_bytes'],6)
 def test_33_trainer_epoch_before_use_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0x0911A3B6:{'trainer_context_epoch_changed':True}})
 def test_34_trainer_epoch_after_last_use_allowed(self):
  p=v.compose_selected(self.raw,epoch_events={v.HIT_CALL:{'trainer_context_epoch_changed':True}},opaque_writes={v.HIT_CALL:[(v.TRAINER,2,0)]});self.assertEqual(p['minimum_executed_bytes'],6)
 def test_35_unknown_sites_events_and_types_rejected(self):
  for kwargs in(dict(opaque_writes={1:[]}),dict(epoch_events={1:{}}),dict(epoch_events={v.HIT_CALL:{'extra':False}}),dict(epoch_events={v.HIT_CALL:{'trainer_context_epoch_changed':1}}),dict(opaque_writes=[]),dict(epoch_events=[])):
   with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v.compose_selected(self.raw,**kwargs)
 def test_36_writes_geometry_rejected(self):
  for row in((True,1,0),(-1,1,0),(0xFFFFFFFF,4,0),(0x02010000,0,0),(0x02010000,8,0),(0x02010000,1,256),(0x02010000,1,False)):
   with self.subTest(row=row),self.assertRaises(ValueError):v.preservation_contract([],writes=[row])
 def test_37_live_geometry_rejected(self):
  for live in(None,{},[(1,1)],[[True,1]],[[-1,1]],[[1,0]],[[0xFFFFFFFF,2]]):
   with self.subTest(live=live),self.assertRaises(ValueError):v.preservation_contract(live)
 def test_38_measurement_metadata_only(self):
  rows=v.measure(self.raw);self.assertEqual(rows,v.ALL_WINDOWS);self.assertEqual((len(rows),sum(x['size']for x in rows)),(9,90));self.assertTrue(all(set(x)=={'address','size','sha256'}for x in rows))
 def test_39_malformed_registration_before_composition(self):
  for address in(v.SLOT,v.HOOK,0x080250F8,v.WRAPPER,v.CALC):
   with mock.patch.object(v,'compose_selected')as compose:
    with self.assertRaises(ValueError):self.check(raw=Mutation(self.raw,address))
    compose.assert_not_called()
 def test_40_review_json_roundtrip(self):
  self.check(review=json.loads(json.dumps(self.review)));self.assertEqual(v.protected_windows(self.review),v.ALL_WINDOWS)
 def test_41_source_root_roles(self):
  p=self.check()[1]['source'];self.assertEqual((p['primary_opcode'],p['primary_slot'],p['hook_register']),(0x5D,v.SLOT,2));self.assertEqual(p['sources'],9)
 def test_42_no_flags_dereference_or_reward_store(self):
  p=v._compose(self.raw);self.assertFalse(any(a<=v.FLAGS<a+n for _,a,n,_ in p['reads']));self.assertNotIn(0x080251C8,p['visited']);self.assertNotIn(v.STOP,p['visited'])
