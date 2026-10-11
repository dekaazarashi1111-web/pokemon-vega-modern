"""Toxic Orb新scopeのみ。独立source sparse fixture、私有ROMを試験入力にしない。"""
import copy, hashlib, unittest
from unittest import mock
import pr16_dex_hof_toxic_orb_roots as v
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
class ToxicOrbTests(unittest.TestCase):
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
 def test_01_exact_six_bytes_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);regions,proof=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in regions],[(v.HIT_CALL,v.HIT_CALL+6,v.KIND)])
  self.assertEqual(before,self.inherited);self.assertFalse(proof['donor_eligible'])
 def test_02_source_structs_and_enums(self):
  p=self.check()[1]['source']['layout'];b=p['structs']['battle_pokemon'];n=p['structs']['new_battle_struct']
  self.assertEqual(b['size'],88);self.assertEqual([b['fields'][x]['offset']for x in('hp','item','ability','status1')],[40,46,56,76])
  self.assertEqual(n['size'],1368);self.assertEqual(n['fields']['endTurnBlockState']['offset'],327)
  self.assertEqual(n['fields']['ai.itemEffects']['offset'],665)
  self.assertEqual(p['enum_values'],dict(state=69,substate=2,request=40));self.assertFalse(p['source_comments_used'])
 def test_03_complete_hook_to_leaf_path(self):
  p=self.check()[1]['composition'];self.assertEqual(p['instruction_steps'],169)
  self.assertEqual(len(p['conditional_call_groups']),2);self.assertEqual(p['endpoint'],v.STOP)
  self.assertEqual(p['endpoint_arguments'],[2]);self.assertTrue(p['nonlive_ram_erased_at_each_boundary'])
  self.assertFalse(p['internal_active_bank_host_seeded']);self.assertFalse(p['internal_status_pointer_host_seeded'])
 def test_04_minimum_complete_thumb_geometry(self):
  e=v.evidence_template(v.HITS[0]);self.assertEqual(v.witness_geometry(e),(v.HIT_CALL,6))
  self.assertEqual([(i['address'],i['size'])for i in e['complete_instructions']],[(v.HIT_CALL,4),(v.HIT_CALL+4,2)])
  self.assertTrue(v.HIT_CALL<v.HITS[0]and v.HITS[0]+4>v.HIT_CALL+4)
 def test_05_real_registration_and_dispatch(self):
  p=v._compose(self.raw);self.assertEqual(p['visited'][0],v.HOOK)
  for a in(v.ENTRY,0x090F7F74,0x090F80D8,0x090F80EC,0x090F945E,0x090F949E,0x090FA774,v.HIT_CALL,0x090FB594):self.assertIn(a,p['visited'])
  self.assertNotIn(v.STOP,p['visited']);self.assertNotIn(v.HIT_CALL+4,p['visited'])
 def test_06_all_executed_model_instruction_bytes_rejected(self):
  for i in v.INS.values():
   for a in range(i.address,i.address+i.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_07_all_opaque_signature_bytes_rejected(self):
  for i in v.ABI_INS.values():
   for a in range(i.address,i.address+i.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_08_all_literal_registration_bytes_rejected(self):
  for a in v.WORDS:
   for j in range(4):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+j),self.sources)
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
   lambda e:e['classified_window'].update(size=4),lambda e:e['classified_window'].update(address=v.HITS[0]),
   lambda e:e['root'].update(state=68),lambda e:e['complete_instructions'][0].update(size=2),
   lambda e:e['input_contract'].update(extra='x')):
   bad=v.evidence_template(v.HITS[0]);change(bad)
   with self.assertRaises(ValueError):v.witness_geometry(bad)
 def test_19_review_claims_and_root_closed(self):
  for key,value in v.CLAIMS.items():
   if type(value)is bool:self.reject_review(lambda r:r['claims'].update({key:not value}))
  self.reject_review(lambda r:r['root'].update(state_cell=0x09166580))
 def test_20_parent_hit_every_field_preserved(self):
  for key in self.inherited['hits'][0]:
   p=copy.deepcopy(self.inherited);p['hits'][0][key]=None
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=p)
 def test_21_duplicate_missing_parent_hit_rejected(self):
  for change in(lambda p:p.update(hits=[]),lambda p:p['hits'].append(copy.deepcopy(p['hits'][0]))):
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
  contract=copy.deepcopy(v.CONTRACT);contract['minimum_ja']='whole functions'
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
   p=v.compose_selected(self.raw,opaque_writes={site:[(0x02015000,4,0xAABBCCDD)]})
   self.assertEqual(p['status'],'PASS_CONDITIONAL_TOXIC_ORB_ROOT')
 def test_28_active_bank_cannot_be_opaque_host_overwritten(self):
  for site in v.EXTERNAL:
   with self.subTest(site=site),self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={site:[(v.ACTIVE,1,2)]})
 def test_29_same_resource_epochs(self):
  for site in v.EXTERNAL:
   for event in('battle_context_epoch_changed','newbs_epoch_changed','stack_epoch_changed'):
    with self.subTest(site=site,event=event),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={site:{event:True}})
 def test_30_unknown_boundaries_and_events_rejected(self):
  for kwargs in(dict(opaque_writes={1:[]}),dict(epoch_events={1:{}}),
   dict(epoch_events={0x090F9496:{'extra':False}}),dict(epoch_events={0x090F9496:{'newbs_epoch_changed':1}})):
   with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v.compose_selected(self.raw,**kwargs)
 def test_31_write_geometry_closed(self):
  for write in((True,1,0),(0x02015000,0,0),(0x02015000,8,0),(0xFFFFFFFF,4,0),(0x02015000,1,256)):
   with self.subTest(write=write),self.assertRaises(ValueError):v.preservation_contract([],writes=[write])
 def test_32_source_current_item894_effect75(self):
  p=v.source_item(self.sources)
  self.assertEqual((p['canonical_id'],p['upstream_id'],p['hold_effect']),(894,680,75))
  self.assertEqual((p['item_stride'],p['field_offset'],p['field_address']),(40,14,v.ITEM_EFFECT_FIELD))
  self.assertFalse(p['observed_value_input']);self.assertEqual(v.PROFILE['held_item'],894)
 def test_33_item_lookup_and_record_are_executed(self):
  p=v._compose(self.raw)
  for a in(0x090D3FEC,0x090D4026,0x0910FDD0,0x0910FDE0,0x090D4114,0x090D4120):self.assertIn(a,p['visited'])
  self.assertIn((0x0910FDE0,v.ITEM_EFFECT_FIELD,1,75),p['reads'])
  self.assertIn((0x090D4120,v.NEW_CONTEXT+667,1,75),p['writes'])
  self.assertEqual(set(v.EXTERNAL),{0x090F9496,0x090FA7B4})
 def test_34_source_item_byte_resealed_rejected(self):
  raw=Mutation(self.raw,v.ITEM_EFFECT_FIELD);review=copy.deepcopy(self.review);reseal(review,raw)
  with self.assertRaises(ValueError):self.check(raw=raw,review=review)
 def test_35_measurement_is_metadata_only(self):
  rows=v.measure(self.raw);self.assertEqual(rows,v.ALL_WINDOWS)
  self.assertEqual((len(rows),sum(r['size']for r in rows)),(18,537))
  self.assertTrue(all(set(r)=={'address','size','sha256'}for r in rows))
 def test_36_malformed_hook_fails_before_composition(self):
  for a in(v.HOOK,0x08017A6C,0x09166584,v.ITEM_EFFECT_FIELD):
   with mock.patch.object(v,'compose_selected')as compose:
    with self.assertRaises(ValueError):self.check(raw=Mutation(self.raw,a))
    compose.assert_not_called()
 def test_37_actual_writer_values_and_emit_arguments(self):
  p=v._compose(self.raw);writes=p['writes'];bank=v.MONS+176
  for target,value in((v.ACTIVE,2),(v.ATTACKER,2),(v.TARGET,2),(v.LAST_ITEM,894),(bank+76,128)):
   self.assertTrue(any(a==target and x==value for _,a,_,x in writes))
  calls=p['calls'];self.assertEqual(calls[0]['arguments'],[2,2,0]);self.assertEqual(calls[1]['arguments'],[0,40,0,4])
  self.assertEqual(calls[1]['stack_data_pointer'],bank+76)
 def test_38_source_layout_ignores_offset_comments(self):
  sources={k:v for k,v in self.sources.items()}
  sources['cfru-include--pokemon.h']=sources['cfru-include--pokemon.h'].replace(b'/*0x28*/',b'/*0x99*/')
  self.assertEqual(v.source_layout(sources),v.source_layout(self.sources))
  with self.assertRaises(ValueError):self.check(sources=sources)
 def test_39_struct_drift_not_accepted(self):
  for name,old,new in(('cfru-include--battle.h',b'u8 endTurnBlockState;',b'u8 inserted; u8 endTurnBlockState;'),
   ('cfru-include--pokemon.h',b'u16 hp;',b'u32 hp;')):
   sources=dict(self.sources);sources[name]=sources[name].replace(old,new)
   with self.subTest(name=name),self.assertRaises(ValueError):v.source_layout(sources)
 def test_40_closed_layout_parser_and_integer_expression(self):
  for body in('long value;','u8 x[unknown];','u8 x:9;','u8 x; trailing','u8 x;u8 x;'):
   with self.subTest(body=body),self.assertRaises((ValueError,SyntaxError)):v.layout(body,{})
  for expr in('__import__("os")','a.b','-1','4/3','0/0'):
   with self.subTest(expr=expr),self.assertRaises((ValueError,SyntaxError)):v.cexpr(expr,{})
 def test_41_bitfield_and_pointer_arm32_layout(self):
  fields,size,align=v.layout('u8 a:7;u8 b:2;const u8 *p;u16 h[3];',{})
  self.assertEqual(fields['a'],dict(offset=0,bit=0,width_bits=7,type_size=1))
  self.assertEqual(fields['b']['offset'],1);self.assertEqual(fields['p']['offset'],4)
  self.assertEqual((size,align),(16,4))
 def test_42_double_bank_profile_consistent(self):
  self.assertEqual((v.PROFILE['battle_flags'],v.PROFILE['battlers_count'],v.PROFILE['turn_order_bank']),(1,4,2))
 def test_43_no_hit_callee_or_successor_effect_claim(self):
  p=self.check()[1];self.assertTrue(p['hit_callee_entered'])
  for k in('hit_callee_effects_proven','hit_callee_return_required','static_successor_executed','opaque_callee_effects_proven','full_story_reachability_claimed','indirect_reference_completeness_claimed','retirement_proven'):
   self.assertFalse(p[k])
 def test_44_unknown_live_projection_rejected(self):
  for live in(None,{},[(1,1)],[[True,1]],[[1,0]]):
   with self.subTest(live=live),self.assertRaises(ValueError):v.preservation_contract(live)
