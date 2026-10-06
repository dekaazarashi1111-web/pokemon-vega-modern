"""Dancer新scopeのみ。source-only fixtureと全保護窓/reseal/live/epoch反証。"""
import copy,hashlib,pathlib,unittest
from unittest import mock
import pr16_dex_hof_dancer_roots as v
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
class DancerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('source-only FIXTURE required')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,parent=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if parent is None else parent,self.review if review is None else review,self.sources if sources is None else sources)
 def reject(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def initial_change_reject(self,a,n,val):
  original=v.memory
  def changed(hp):
   m=original(hp);v.rt.setmem(m,a,n,val);return m
  with mock.patch.object(v,'memory',side_effect=changed),self.assertRaises(ValueError):v.compose(self.raw,1)
 def test_01_exact_minimum_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);regions,proof=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in regions],[(v.MINIMUM,v.MINIMUM+6,v.KIND)])
  self.assertEqual(before,self.inherited);self.assertFalse(proof['donor_eligible']);self.assertFalse(proof['owner_transfer_proven'])
 def test_02_full_source_struct_layout(self):
  s=v.source_semantics(self.sources)
  self.assertEqual(s['dancer_fields'],dict(MoveBounceInProgress=dict(offset=352,bit=0,width_bits=2,type_size=1),
   DancerBankCount=dict(offset=334,size=1),DancerInProgress=dict(offset=354,bit=3,width_bits=1,type_size=1),
   DancerTurnOrder=dict(offset=376,size=4),CurrentTurnAttacker=dict(offset=335,bit=0,width_bits=4,type_size=1),
   CurrentTurnTarget=dict(offset=335,bit=4,width_bits=4,type_size=1)))
  self.assertEqual(s['battle_pokemon'],dict(size=88,ability=dict(offset=56,size=2),hp=dict(offset=40,size=2)))
  self.assertEqual(s['dancer_state'],48);self.assertFalse(s['source_comments_used'])
 def test_03_canonical_alias_not_upstream_or_observation(self):
  s=v.source_semantics(self.sources);self.assertEqual((s['upstream_ability'],s['canonical_ability']),(216,217))
  self.assertEqual(s['ability_macro'],'direct_gBattleMons_field');self.assertIn('short_circuited',s['ability_on_field'])
  self.assertIn('ability_ids.csv',v.SOURCE_IDS);self.assertIn('scripts--build_id_spaces.py',v.SOURCE_IDS)
 def test_04_source_canonical_drift_rejected_without_hash_authority(self):
  src=dict(self.sources);src['ability_ids.csv']=src['ability_ids.csv'].replace(b'ABILITY_KEY_DANCER,217,',b'ABILITY_KEY_DANCER,216,')
  with self.assertRaises(ValueError):v.source_semantics(src)
 def test_05_source_layout_drift_rejected_without_hash_authority(self):
  src=dict(self.sources);src['cfru-include--battle.h']=src['cfru-include--battle.h'].replace(b'u8 DancerBankCount;',b'u16 DancerBankCount;')
  with self.assertRaises(ValueError):v.source_semantics(src)
 def test_06_source_enum_drift_rejected_without_hash_authority(self):
  src=dict(self.sources);src['cfru-cmd49.c']=src['cfru-cmd49.c'].replace(b'\tATK49_DANCER,',b'\tATK49_EXTRA,\n\tATK49_DANCER,')
  with self.assertRaises(ValueError):v.source_semantics(src)
 def test_07_all_flag_bits_serialized(self):
  self.assertEqual(v.fixed_parts()[v.BIT_TABLE],b''.join((1<<i).to_bytes(4,'little')for i in range(32)))
  s=v.source_semantics(self.sources);self.assertEqual(s['bit_table_fields'],32);self.assertEqual(s['description_index'],31)
 def test_08_two_profiles_cover_complete_BL_and_LDR(self):
  p=v.compose_selected(self.raw);a,b=p['cases']
  self.assertEqual([c['instruction_steps']for c in p['cases']],[529,530])
  self.assertEqual([c['endpoint']for c in p['cases']],[0x090E20B8,0x090E20B0])
  self.assertEqual([len(c['conditional_call_groups'])for c in p['cases']],[9,9])
  self.assertIn(v.MINIMUM,a['visited']);self.assertNotIn(v.MINIMUM+4,a['visited'])
  self.assertIn(v.MINIMUM,b['visited']);self.assertIn(v.MINIMUM+4,b['visited'])
  self.assertEqual((p['minimum_byte_coverage'],p['hit_byte_coverage']),(6,4))
 def test_09_complete_registered_chain(self):
  c=v.compose(self.raw,1)
  for a in(v.PRODUCER,v.ENTRY,0x095D5A9C,0x095343A4,0x090DF7A8,0x090DF866,0x090E010A,0x090E205A,0x090E2092,v.MINIMUM,0x090E2E94,0x090E2EB0):self.assertIn(a,c['visited'])
  self.assertEqual(v.WORDS[0x09163CE4],0x090E010A);self.assertEqual(v.WORDS[0x0903F574],v.ENTRY|1)
 def test_10_real_producer_and_no_positive_seed(self):
  self.assertEqual(v.rt.getmem(v.memory(1),v.CIRCUS,4),0)
  for c in v.compose_selected(self.raw)['cases']:
   self.assertEqual(c['producer_writes'],[(0x091034A4,v.CIRCUS,4,0x80000000)])
   self.assertFalse(c['positive_circus_flag_host_seeded']);self.assertTrue(c['dancer_state_host_initial_condition'])
 def test_11_direct_ability_and_actual_battler_writer(self):
  c=v.compose(self.raw,1)
  self.assertIn(dict(pc=0x090E015A,address=v.MONS+88*2+56,size=2),c['dancer_reads'])
  self.assertEqual(c['dancer_writes'],[(0x090E2090,v.ATTACKER,1,2)])
  self.assertFalse(v.CLAIMS['get_bank_ability_substituted'])
 def test_12_first_activation_is_short_circuited_not_assumed(self):
  c=v.compose(self.raw,1)
  self.assertFalse(c['ability_on_field_executed']);self.assertFalse(c['first_dancer_initialization_executed'])
  self.assertNotIn(0x090E12E6,c['visited']);self.assertNotIn(0x090E12F0,c['visited'])
  self.assertFalse(v.CLAIMS['ability_on_field_success_assumed']);self.assertFalse(v.CLAIMS['dancer_initialization_producer_proven'])
 def test_13_target_hp_read_in_both_cases(self):
  for hp in(0,1):self.assertIn(dict(pc=0x090E2EB0,address=v.MONS+88+40,size=2),v.compose(self.raw,hp)['dancer_reads'])
 def test_14_get_base_target_actual_api_and_limits(self):
  c=v.compose(self.raw,1);g=c['conditional_call_groups'][-1]
  self.assertEqual((g['site'],g['target'],g['role']),(0x090E2E94,0x090D5014,'GetBaseMoveTarget'))
  self.assertFalse(g['callee_effects_proven']);self.assertNotIn(g['target'],c['visited'])
  self.assertFalse(c['actual_runtime_execution_observed']);self.assertNotIn(0x090E20B4,c['visited'])
 def test_15_every_instruction_byte_rejected(self):
  for ins in v.INS.values():
   for a in range(ins.address,ins.address+ins.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a))
 def test_16_every_metadata_and_bit_byte_rejected(self):
  for a,b in v.fixed_parts().items():
   if a in v.INS:continue
   for j in range(len(b)):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind(Mutation(self.raw,a+j))
 def test_17_all_protected_bytes_reseal_rejected(self):
  count=0
  for w in v.ALL_WINDOWS:
   for a in range(w['address'],w['address']+w['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review);p=copy.deepcopy(self.inherited);reseal(r,raw);reseal(p,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,parent=p,review=r)
    count+=1
  self.assertEqual(count,978)
 def test_18_all_source_whole_file_mutations_rejected(self):
  for name,b in self.sources.items():
   src={**self.sources,name:b+b'\n'}
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources=src)
 def test_19_source_missing_extra_rejected(self):
  for name in self.sources:
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={k:b for k,b in self.sources.items()if k!=name})
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_20_source_reseal_cannot_authorize(self):
  for name in self.sources:
   for key,value in[('sha256','0'*64),('git_blob_sha','0'*40),('commit','0'*40),('source','other'),('repository','other/repo')]:
    with self.subTest(source=name,key=key):self.reject(lambda r:r['source_bindings'][name].update({key:value}))
 def test_21_closed_schema(self):
  self.reject(lambda r:r.update(extra=True));self.reject(lambda r:r.update(schema_version=True));self.reject(lambda r:r.pop('root'))
 def test_22_current_diagnostic_separation(self):
  self.reject(lambda r:r.update(required_candidate=v.DIAGNOSTIC));self.reject(lambda r:r.update(diagnostic_input=v.CANDIDATE))
  p=copy.deepcopy(self.inherited);p['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(parent=p)
 def test_23_regions_rejects_diagnostic_before_delegate(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_24_regions_requires_current_identity(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value='ok')as inner:
   self.assertEqual(v.regions(*FIXTURE),'ok');inner.assert_called_once()
 def test_25_claims_are_closed(self):
  for k,x in v.CLAIMS.items():
   self.reject(lambda r:r['claims'].update({k:not x}));e=v.evidence_template(v.HIT);e[k]=not x
   with self.subTest(claim=k),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_26_geometry_and_instruction_roles_closed(self):
  e=v.evidence_template(v.HIT);self.assertEqual(v.witness_geometry(e),(v.MINIMUM,6))
  self.assertEqual(e['complete_instructions'][1],dict(address=v.MINIMUM+4,size=2,kind='spmem',load=True,register=3,stack_offset=36))
  for change in(lambda e:e['classified_window'].update(size=4),lambda e:e['classified_window'].update(address=v.HIT),lambda e:e.update(extra=True),lambda e:e['complete_instructions'][1].update(kind='mov'),lambda e:e['positive_profiles'].pop()):
   e=v.evidence_template(v.HIT);change(e)
   with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_27_root_and_contract_closed(self):
  self.reject(lambda r:r['root'].update(state=12));self.reject(lambda r:r['root'].update(hit_successor=0));self.reject(lambda r:r['input_contract'].update(extra=True))
 def test_28_parent_hit_all_fields_preserved(self):
  for k,x in[('accepted',True),('accepted',0),('classification','code'),('owner_candidates',['x']),('size',True),('target',0)]:
   p=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);p['hits'][0][k]=x;r['hits'][0][k]=x
   with self.subTest(key=k),self.assertRaises(ValueError):self.check(parent=p,review=r)
 def test_29_parent_missing_duplicate_rejected(self):
  for f in(lambda p:p['hits'].pop(),lambda p:p['hits'].append(copy.deepcopy(p['hits'][0]))):
   p=copy.deepcopy(self.inherited);f(p)
   with self.assertRaises(ValueError):self.check(parent=p)
 def test_30_unrelated_hit_never_changed(self):
  p=copy.deepcopy(self.inherited);p['hits'].append(dict(address=0x09099D3D,accepted=False));before=copy.deepcopy(p);self.check(parent=p);self.assertEqual(before,p)
 def test_31_windows_order_content_closed(self):
  self.reject(lambda r:r['windows'].reverse());self.reject(lambda r:r['windows'][0].update(size=1));self.reject(lambda r:r['windows'].pop())
 def test_32_profiles_are_strict_and_closed(self):
  for k,x in v.PROFILE.items():
   p=copy.deepcopy(v.PROFILE);p[k]=not x if type(x)is bool else x+[2]if type(x)is list else x+1
   with self.subTest(field=k),self.assertRaises(ValueError):v.compose(self.raw,1,profile=p)
  for hp in(-1,2,True,False,0.0,1.0,'1'):
   with self.assertRaises(ValueError):v.compose(self.raw,hp)
 def test_33_contract_cannot_change(self):
  c=copy.deepcopy(v.CONTRACT);c['dancer_ja']='pretend initial activation succeeded'
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract=c)
 def test_34_every_future_live_byte_refuted(self):
  for hp in(0,1):
   for g in v.compose(self.raw,hp)['conditional_call_groups']:
    live=[[x['address'],x['size']]for x in g['required_fields']]
    for a,n in live:
     for j in range(n):
      with self.subTest(hp=hp,site=g['site'],address=a+j),self.assertRaises(ValueError):v.preserve(live,[(a+j,1,0)])
 def test_35_each_boundary_live_write_replay_refuted(self):
  for hp in(0,1):
   for g in v.compose(self.raw,hp)['conditional_call_groups']:
    self.assertTrue(g['required_fields']);a=g['required_fields'][0]['address'];key=g['site'],g['target']
    with self.subTest(hp=hp,site=key),self.assertRaises(ValueError):v.compose(self.raw,hp,opaque_writes={key:[(a,1,0)]})
 def test_36_nonlive_writes_are_erased(self):
  for g in v.compose(self.raw,1)['conditional_call_groups']:
   key=g['site'],g['target'];r=v.compose(self.raw,1,opaque_writes={key:[(0x02000000,4,123)]})
   self.assertEqual(r['endpoint'],0x090E20B8);self.assertTrue(r['nonlive_ram_erased_at_every_boundary'])
 def test_37_all_epochs_each_boundary_refuted(self):
  for hp in(0,1):
   for g in v.compose(self.raw,hp)['conditional_call_groups']:
    key=g['site'],g['target']
    for event in('circus_flags_epoch_changed','battle_context_epoch_changed','stack_epoch_changed'):
     with self.subTest(hp=hp,site=key,event=event),self.assertRaises(ValueError):v.compose(self.raw,hp,epoch_events={key:{event:True}})
 def test_38_unknown_boundary_condition_rejected(self):
  for kwargs in({'opaque_writes':{(0,1):[]}}, {'epoch_events':{(0,1):{}}}):
   with self.assertRaises(ValueError):v.compose(self.raw,1,**kwargs)
  for event in({'other':True},{'stack_epoch_changed':1},{'stack_epoch_changed':None}):
   with self.assertRaises(ValueError):v.preserve([],events=event)
 def test_39_opaque_write_invalid_geometry(self):
  for write in[(-1,1,0),(2**32-1,2,0),(0,True,0),(0,3,0),(0,1,256),(0,1,-1),(True,1,0),(0,1,False),(0.0,1,0)]:
   with self.subTest(write=write),self.assertRaises(ValueError):v.preserve([],writes=[write])
 def test_40_live_invalid_geometry(self):
  for live in[[[0,0]],[[-1,2]],[[2**32-1,2]],[[True,1]],[[0,True]],[(0,1)],[[0,1,2]]]:
   with self.assertRaises(ValueError):v.preserve(live)
 def test_41_initial_positive_circus_seed_rejected(self):self.initial_change_reject(v.CIRCUS,4,0x80000000)
 def test_42_dancer_progress_off_not_fake_success(self):self.initial_change_reject(v.CONTEXT+354,1,0)
 def test_43_dancer_count_done_rejected(self):self.initial_change_reject(v.CONTEXT+334,1,4)
 def test_44_dancer_count_out_of_bounds_rejected(self):self.initial_change_reject(v.CONTEXT+334,1,5)
 def test_45_dancer_ability_upstream216_rejected(self):self.initial_change_reject(v.MONS+88*2+56,2,216)
 def test_46_dancer_dead_rejected(self):self.initial_change_reject(v.MONS+88*2+40,2,0)
 def test_47_dancer_absent_rejected(self):self.initial_change_reject(v.ABSENT,1,4)
 def test_48_dancer_same_original_attacker_rejected(self):self.initial_change_reject(v.CONTEXT+335,1,18)
 def test_49_partner_mismatch_rejected(self):self.initial_change_reject(v.CONTEXT+335,1,17)
 def test_50_single_battle_cannot_fake_partner_path(self):self.initial_change_reject(v.FLAGS,4,0x04000000)
 def test_51_new_context_pointer_drift_rejected(self):self.initial_change_reject(v.NEWBS,4,v.CONTEXT+8)
 def test_52_turnorder_unbound_bank_rejected(self):self.initial_change_reject(v.CONTEXT+376,1,4)
 def test_53_current_target_out_of_bounds_rejected(self):self.initial_change_reject(v.CONTEXT+335,1,0x40)
 def test_54_current_move_argument_mismatch_rejected(self):self.initial_change_reject(v.CURRENT_MOVE,2,2)
 def test_55_wrong_opcode_state_rejected(self):self.initial_change_reject(v.SCRIPTING+20,1,12)
 def test_56_source_only_unbound_rom_fails_closed(self):
  with self.assertRaises(ValueError):v.chunk(self.raw,0x08000000,2)
 def test_57_current_rom_measurement_not_claimed(self):
  proof=self.check()[1];self.assertTrue(proof['current_candidate_measurement_required'])
  self.assertFalse(proof['natural_battle_entry_proven']);self.assertFalse(proof['universal_heap_or_irq_lifetime_proven'])
  self.assertFalse(proof['indirect_reference_completeness_proven']);self.assertFalse(proof['retirement_proven'])
 def test_58_no_accepted_root_module_import_or_rom_io(self):
  text=pathlib.Path(v.__file__).read_text()
  self.assertNotIn('import pr16_dex_hof_moveend_wrapper_roots',text)
  self.assertNotIn('decode_thumb',text);self.assertNotIn("open(",text)
 def test_59_base_target_future_fields_preserved(self):
  g=v.compose(self.raw,1)['conditional_call_groups'][-1];live={a for row in g['required_fields']for a in range(row['address'],row['address']+row['size'])}
  for a in(v.NEWBS,v.CONTEXT+335,v.MONS+88+40):self.assertIn(a,live)
 def test_60_sparse_matches_all_immutable_window_hashes(self):
  self.assertEqual(v.measure(self.raw),v.ALL_WINDOWS);self.assertEqual(len(v.ALL_WINDOWS),35)
  for w in v.ALL_WINDOWS:self.assertEqual(v.identity(v.chunk(self.raw,w['address'],w['size'])),{k:w[k]for k in('size','sha256')})
