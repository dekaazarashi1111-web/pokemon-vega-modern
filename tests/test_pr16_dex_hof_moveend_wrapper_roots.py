"""新moveend scope。全source/byte/reseal・二profile・全future-live/epochを反証する。"""
import copy,hashlib,unittest
from unittest import mock
import pr16_dex_hof_moveend_wrapper_roots as v
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
  for val in obj.values():reseal(val,raw)
 elif isinstance(obj,list):
  for val in obj:reseal(val,raw)
class MoveEndTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('source-only FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,parent=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if parent is None else parent,self.review if review is None else review,self.sources if sources is None else sources)
 def reject(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def test_01_exact_minimum_and_parent_preserved(self):
  before=copy.deepcopy(self.inherited);regions,proof=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in regions],[(v.MINIMUM,v.MINIMUM+6,v.KIND)])
  self.assertEqual(before,self.inherited);self.assertFalse(proof['donor_eligible']);self.assertFalse(proof['dancer_classified'])
 def test_02_source_layout_without_comment_offsets(self):
  r=v.source_semantics(self.sources)
  self.assertEqual(r['move_bounce_field'],dict(offset=352,bit=0,width_bits=2,type_size=1))
  self.assertEqual(r['state_field'],dict(offset=20,size=1));self.assertEqual(r['dynamic_move_type'],dict(offset=19,size=1))
  self.assertFalse(r['source_comments_used']);self.assertEqual(r['attacker_invisible_state'],12)
 def test_03_full_bit_table_source_serialization(self):
  r=v.source_semantics(self.sources);self.assertEqual(r['bit_table_fields'],32)
  self.assertEqual(r['description_index'],31);self.assertEqual(r['description_symbol'],'gText_BattleCircusDescriptionAbilitySuppression')
  self.assertEqual(v.fixed_parts()[v.BIT_TABLE],b''.join((1<<i).to_bytes(4,'little')for i in range(32)))
 def test_04_two_complementary_profiles(self):
  r=v.compose_selected(self.raw)
  self.assertEqual([c['instruction_steps']for c in r['cases']],[454,450]);self.assertEqual([len(c['conditional_call_groups'])for c in r['cases']],[8,8])
  a,b=r['cases'];self.assertIn(v.MINIMUM,a['visited']);self.assertNotIn(v.MINIMUM+4,a['visited'])
  self.assertNotIn(v.MINIMUM,b['visited']);self.assertIn(v.MINIMUM+4,b['visited'])
  self.assertEqual(r['minimum_byte_coverage'],6);self.assertEqual(r['hit_byte_coverage'],4)
 def test_05_actual_producer_not_host_positive_seed(self):
  self.assertEqual(v.rt.getmem(v.memory(0),v.CIRCUS,4),0)
  for c in v.compose_selected(self.raw)['cases']:
   self.assertEqual(c['producer_writes'],[(0x091034A4,v.CIRCUS,4,0x80000000)])
   self.assertFalse(c['positive_circus_flag_host_seeded']);self.assertTrue(c['nonlive_ram_erased_at_every_boundary'])
 def test_06_complete_registered_roots(self):
  for status in(0,0x40):
   r=v._compose(self.raw,status);self.assertEqual(r['visited'][0],v.PRODUCER)
   for a in(v.ENTRY,0x095D5A9C,0x095343A4,0x090DF7A8,0x090DF866,0x090DFB9C):self.assertIn(a,r['visited'])
   self.assertEqual(r['bit_reads'],[v.BIT_TABLE+4*i for i in range(32)])
 def test_07_no_callee_effect_claim(self):
  c=v.compose(self.raw,0x40);self.assertEqual(c['endpoint'],0x090E298A);self.assertNotIn(0x090E298A,c['visited'])
  self.assertFalse(c['actual_runtime_execution_observed']);self.assertFalse(v.CLAIMS['all_opaque_callee_effects_proven'])
 def test_08_every_instruction_byte_rejected(self):
  for ins in v.INS.values():
   for a in range(ins.address,ins.address+ins.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a))
 def test_09_every_metadata_byte_rejected(self):
  for a in v.WORDS:
   for j in range(4):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a+j))
 def test_10_every_bit_table_byte_rejected(self):
  for a in range(v.BIT_TABLE,v.BIT_TABLE+128):
   with self.subTest(address=a),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a))
 def test_11_every_protected_byte_reseal_rejected(self):
  count=0
  for w in v.ALL_WINDOWS:
   for a in range(w['address'],w['address']+w['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);p=copy.deepcopy(self.inherited);reseal(r,raw);reseal(p,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r,parent=p)
    count+=1
  self.assertEqual(count,774)
 def test_12_source_every_whole_file_mutation_rejected(self):
  for name,b in self.sources.items():
   src=dict(self.sources);src[name]=b+b'\n'
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources=src)
 def test_13_source_missing_extra_rejected(self):
  for name in self.sources:
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={k:b for k,b in self.sources.items()if k!=name})
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_14_source_reseal_not_authority(self):
  for name in self.sources:self.reject(lambda r:r['source_bindings'][name].update(sha256='0'*64))
 def test_15_source_blob_and_ref_pinned(self):
  for name in self.sources:
   for key,value in [('git_blob_sha','0'*40),('commit','0'*40),('source','other'),('repository','other/repo')]:
    with self.subTest(source=name,key=key):self.reject(lambda r:r['source_bindings'][name].update({key:value}))
 def test_16_closed_schema(self):
  self.reject(lambda r:r.update(extra=True));self.reject(lambda r:r.update(schema_version=True));self.reject(lambda r:r.pop('root'))
 def test_17_current_diagnostic_separation(self):
  self.reject(lambda r:r.update(required_candidate=v.DIAGNOSTIC));self.reject(lambda r:r.update(diagnostic_input=v.CANDIDATE))
  p=copy.deepcopy(self.inherited);p['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(parent=p)
 def test_18_current_identity_wrapper_rejects_old(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_19_current_identity_wrapper_accepts_parent_checked(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value='ok')as inner:
   self.assertEqual(v.regions(*FIXTURE),'ok');inner.assert_called_once()
 def test_20_all_claims_closed(self):
  for k,x in v.CLAIMS.items():
   self.reject(lambda r:r['claims'].update({k:not x}))
   e=v.evidence_template(v.HIT);e[k]=not x
   with self.subTest(claim=k),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_21_complete_geometry(self):
  self.assertEqual(v.witness_geometry(v.evidence_template(v.HIT)),(v.MINIMUM,6))
  for change in(lambda e:e['classified_window'].update(size=4),lambda e:e['classified_window'].update(address=v.HIT),lambda e:e.update(extra=True),lambda e:e['complete_instructions'][1].update(size=1),lambda e:e['positive_profiles'].pop()):
   e=v.evidence_template(v.HIT);change(e)
   with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_22_root_and_contract_closed(self):
  self.reject(lambda r:r['root'].update(producer_slot=0));self.reject(lambda r:r['root'].update(state=13));self.reject(lambda r:r['input_contract'].update(extra=True))
 def test_23_unknown_parent_fields_preserved(self):
  for k,x in(('accepted',True),('accepted',0),('classification','code'),('owner_candidates',['x']),('size',True),('target',0)):
   p=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);p['hits'][0][k]=x;r['hits'][0][k]=x
   with self.subTest(k=k),self.assertRaises(ValueError):self.check(parent=p,review=r)
 def test_24_parent_duplicate_missing(self):
  for f in(lambda p:p['hits'].pop(),lambda p:p['hits'].append(copy.deepcopy(p['hits'][0]))):
   p=copy.deepcopy(self.inherited);f(p)
   with self.assertRaises(ValueError):self.check(parent=p)
 def test_25_unrelated_hit_unchanged(self):
  p=copy.deepcopy(self.inherited);p['hits'].append(dict(address=0x090E20AB,accepted=False));old=copy.deepcopy(p);self.check(parent=p);self.assertEqual(old,p)
 def test_26_windows_closed(self):
  self.reject(lambda r:r['windows'].reverse());self.reject(lambda r:r['windows'][0].update(size=1));self.reject(lambda r:r['windows'].pop())
 def test_27_all_profile_fields_closed(self):
  for k,x in v.PROFILE.items():
   p=copy.deepcopy(v.PROFILE);p[k]=not x if type(x)is bool else x+1
   with self.subTest(key=k),self.assertRaises(ValueError):v.compose(self.raw,0,profile=p)
  for status in(-1,1,128):
   with self.assertRaises(ValueError):v.compose(self.raw,status)
 def test_28_contract_closed(self):
  c=copy.deepcopy(v.CONTRACT);c['producer_ja']='seed positive flag'
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract=c)
 def test_29_each_future_live_byte_rejected(self):
  for status in(0,0x40):
   for g in v.compose(self.raw,status)['conditional_call_groups']:
    live=[[x['address'],x['size']]for x in g['required_fields']]
    for a,n in live:
     for j in range(n):
      with self.subTest(status=status,site=g['site'],a=a+j),self.assertRaises(ValueError):v.preserve(live,[(a+j,1,0)])
 def test_30_each_boundary_replay_rejects_live_write(self):
  for status in(0,0x40):
   for g in v.compose(self.raw,status)['conditional_call_groups']:
    self.assertTrue(g['required_fields']);a=g['required_fields'][0]['address'];key=g['site'],g['target']
    with self.subTest(status=status,key=key),self.assertRaises(ValueError):v.compose(self.raw,status,opaque_writes={key:[(a,1,0)]})
 def test_31_nonlive_writes_allowed(self):
  for status in(0,0x40):
   for g in v.compose(self.raw,status)['conditional_call_groups']:
    key=g['site'],g['target'];self.assertEqual(v.compose(self.raw,status,opaque_writes={key:[(0x02000000,4,123)]})['endpoint'],0x090E298A if status else 0x090DFBBA)
 def test_32_all_epochs_all_boundaries_rejected(self):
  for g in v.compose(self.raw,0)['conditional_call_groups']:
   key=g['site'],g['target']
   for event in('circus_flags_epoch_changed','battle_context_epoch_changed','stack_epoch_changed'):
    with self.subTest(key=key,event=event),self.assertRaises(ValueError):v.compose(self.raw,0,epoch_events={key:{event:True}})
 def test_33_unknown_boundary_and_events_rejected(self):
  with self.assertRaises(ValueError):v.compose(self.raw,0,opaque_writes={(0,0):[]})
  with self.assertRaises(ValueError):v.compose(self.raw,0,epoch_events={v.BRIDGE:{'extra':True}})
  with self.assertRaises(ValueError):v.compose(self.raw,0,epoch_events={v.BRIDGE:{'stack_epoch_changed':1}})
 def test_34_forbidden_host_flag_injection_rejected(self):
  with self.assertRaises(ValueError):v.compose(self.raw,0,opaque_writes={v.BRIDGE:[(v.CIRCUS,4,0x80000000)]})
  p=copy.deepcopy(v.PROFILE);p['initial_circus_flags']=0x80000000
  with self.assertRaises(ValueError):v.compose(self.raw,0,profile=p)
 def test_35_all_rom_reads_source_bound(self):
  self.assertEqual(self.check()[1]['protected_bytes'],774)
  self.assertEqual(v.measure(self.raw),v.ALL_WINDOWS)
  self.assertIn(0x09167440,v.WORDS)
 def test_36_source_macro_masks(self):
  m=v.source_semantics(self.sources)['masks'];self.assertEqual(m['STATUS3_SEMI_INVULNERABLE'],0x130480C0);self.assertEqual(m['BATTLE_CIRCUS_ABILITY_SUPPRESSION'],1<<31)
 def test_37_positive_flag_clear_before_wrapper_rejected(self):
  with self.assertRaises(ValueError):v.compose(self.raw,0,opaque_writes={v.BRIDGE:[(v.CIRCUS,4,0)]})
 def test_38_register_unknown_flag_branch_rejected(self):
  m=v.machine_engine.Machine(self.raw,0x095D5AA2,{},v.memory(0),instructions=v.INS)
  with self.assertRaises(ValueError):m.step()
 def test_39_dancer_not_accepted(self):
  self.assertEqual(v.HELD_HITS,(0x090E20AB,));self.assertNotIn(0x090E20AA,v.INS)
  with self.assertRaises(ValueError):v.evidence_template(0x090E20AB)
 def test_40_source_table_mutation_with_identity_reseal_rejected(self):
  s=dict(self.sources);s['pret-util.c']=s['pret-util.c'].replace(b'1 << 31',b'1 << 30');r=copy.deepcopy(self.review);r['source_bindings']['pret-util.c'].update(v.identity(s['pret-util.c']))
  with self.assertRaises(ValueError):self.check(sources=s,review=r)
 def test_41_producer_and_consumer_stack_nonalias(self):
  self.assertLess(v.CONTEXT+352,v.BATTLE_CONTEXT);self.assertLess(v.BATTLE_CONTEXT+202,v.SCRIPT)
  for g in v.compose(self.raw,0)['conditional_call_groups']:
   self.assertTrue(g['normal_abi_return_required']);self.assertFalse(g['callee_effects_proven'])
 def test_42_snapshot_scope_not_natural(self):
  for key in('natural_battle_entry_proven','natural_moveend_reachability_proven','all_state_producers_proven','universal_heap_or_irq_lifetime_proven','retirement_proven','indirect_reference_completeness_proven'):self.assertFalse(v.CLAIMS[key])
 def test_43_read_order_emits_only_actual_flag(self):
  for status in(0,0x40):
   r=v._compose(self.raw,status)
   self.assertLess(r['visited'].index(0x091034A4),r['visited'].index(v.ENTRY));self.assertEqual(r['boundaries'].count(v.BRIDGE),1)
 def test_44_code_evidence_has_no_raw_bytes(self):
  import json
  text=json.dumps(self.check()[1]);self.assertNotIn('raw_hex',text);self.assertNotIn('private-inputs',text)
 def test_45_invalid_opaque_geometry_rejected(self):
  for row in[(-1,1,0),(2**32-1,4,0),(2**32,1,0),(True,1,0),(0,True,0),(0,3,0),(0,1,True),(0,1,256)]:
   with self.subTest(row=row),self.assertRaises(ValueError):v.preserve([],writes=[row])
 def test_46_status_scalar_type_closed(self):
  for status in(False,True,0.0,64.0,'0',None):
   with self.subTest(status=status),self.assertRaises(ValueError):v.compose(self.raw,status)
 def test_47_live_projection_geometry_closed(self):
  for live in(None,{},[[-1,1]],[[2**32-1,4]],[[True,1]],[[0,True]],[[0,0]]):
   with self.subTest(live=live),self.assertRaises(ValueError):v.preserve(live)
