"""新しい吸収特性登録rootだけ。既accepted suiteは実行しない。"""
import copy,hashlib,json,unittest
import pr16_dex_hof_absorbing_ability_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,raw,address,value=None):self.raw=raw;self.address=address;self.value=value
 def __len__(self):return len(self.raw)
 def __getitem__(self,key):
  pos=self.address-0x08000000
  if isinstance(key,slice):
   start=0 if key.start is None else key.start;stop=len(self.raw)if key.stop is None else key.stop;out=bytearray(self.raw[key])
   if start<=pos<stop:out[pos-start]=(out[pos-start]^1)if self.value is None else self.value
   return bytes(out)
  out=self.raw[key];return ((out^1)if self.value is None else self.value)if key==pos else out
class AbsorbingAbilityRootsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('明示scoped fixtureが必要')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,fn):
  r=copy.deepcopy(self.review);fn(r)
  with self.assertRaises(ValueError):self.check(review=r)
 def test_01_minimum_only(self):
  rows,p=self.check();self.assertEqual(len(rows),1);self.assertEqual(v.witness_geometry(rows[0].evidence),(0x090B69A8,6));self.assertEqual(p['protected_bytes'],524)
 def test_02_two_complete_paths(self):
  p=self.check()[1]['composition'];self.assertEqual([x['instruction_steps']for x in p['cases']],[195,195]);self.assertEqual(p['opaque_calls'],0);self.assertEqual(p['minimum_executed_bytes'],6)
 def test_03_actual_coverage_union(self):
  cases=[v._compose(self.raw,a)for a in(32,10)];cover=set()
  for c in cases:
   for a,n in c['fetches']:cover.update(range(a,a+n))
  self.assertTrue(set(range(0x090B69A8,0x090B69AE))<=cover)
  self.assertNotIn(0x090B69AC,cases[0]['visited']);self.assertNotIn(0x090B69A8,cases[1]['visited'])
 def test_04_registered_caller_full_chain(self):
  for a in(32,10):
   c=v._compose(self.raw,a)
   for pc in(v.ENTRY,0x0911DC4C,v.HANDLER,0x090D3D2C,0x090D3D7E,0x090B667C,0x095D5874,0x0953410C,0x09533AD4,0x0953417C,0x090B6688,0x090B6980):self.assertIn(pc,c['visited'])
 def test_05_circus_flags_not_read(self):
  for ability in(32,10):
   c=v._compose(self.raw,ability)
   self.assertFalse(any(a<=0x0203DFBC<a+n for _,a,n,_ in c['reads']))
   self.assertNotIn(0x095D587C,c['visited'])
 def test_06_real_fifth_argument_read(self):
  c=v._compose(self.raw,32)
  self.assertIn((0x09533ADC,0x03006FD8,2,1),c['reads'])
  self.assertIn((0x090B668E,0x03006FA8,2,1),c['reads'])
 def test_07_independent_structs(self):
  s=v.source_layout(self.sources);self.assertEqual(s['battle_pokemon']['size'],88);self.assertEqual(s['new_battle_struct']['skip']['offset'],356);self.assertEqual(s['battle_struct']['offset'],19);self.assertEqual(s['battle_scripting']['offset'],23)
 def test_08_all_source_pins(self):
  for name in self.sources:
   s=dict(self.sources);s[name]+=b'\n'
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources=s)
 def test_09_source_missing_extra(self):
  for name in self.sources:
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={k:b for k,b in self.sources.items()if k!=name})
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_10_source_reseal_rejected(self):
  for name in self.sources:
   s=dict(self.sources);s[name]+=b'\n';r=copy.deepcopy(self.review);r['source_bindings'][name].update(v.identity(s[name]))
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(review=r,sources=s)
 def test_11_every_protected_byte(self):
  for w in v.ALL_WINDOWS:
   for a in range(w['address'],w['address']+w['size']):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_12_every_byte_reseal(self):
  for w in v.ALL_WINDOWS:
   for a in range(w['address'],w['address']+w['size']):
    raw=Mutation(self.raw,a);r=copy.deepcopy(self.review)
    for x in r['windows']:
     if x['address']<=a<x['address']+x['size']:x.update(v.identity(v.chunk(raw,x['address'],x['size'])))
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r)
 def test_13_unknown_field(self):self.reject_review(lambda r:r.update(extra=True))
 def test_14_wrong_schema(self):self.reject_review(lambda r:r.update(schema_version=True))
 def test_15_wrong_current_identity(self):self.reject_review(lambda r:r.update(required_candidate=v.DIAGNOSTIC))
 def test_16_wrong_diagnostic_identity(self):self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE))
 def test_17_parent_candidate(self):
  p=copy.deepcopy(self.inherited);p['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=p)
 def test_18_all_parent_hit_fields(self):
  for key in v.EXPECTED_HITS[0]:
   p=copy.deepcopy(self.inherited);p['hits'][0][key]=None
   with self.subTest(field=key),self.assertRaises(ValueError):self.check(inherited=p)
 def test_19_missing_hit(self):
  with self.assertRaises(ValueError):self.check(inherited=dict(candidate=v.CANDIDATE,hits=[]))
 def test_20_duplicate_hit(self):
  with self.assertRaises(ValueError):self.check(inherited=dict(candidate=v.CANDIDATE,hits=v.EXPECTED_HITS*2))
 def test_21_all_claim_fields(self):
  for key in v.CLAIMS:self.reject_review(lambda r,k=key:r['claims'].__setitem__(k,None))
 def test_22_all_root_fields(self):
  for key in v.ROOT:self.reject_review(lambda r,k=key:r['root'].__setitem__(k,None))
 def test_23_all_contract_fields(self):
  for key in v.CONTRACT:self.reject_review(lambda r,k=key:r['input_contract'].__setitem__(k,''))
 def test_24_all_profile_fields(self):
  for key in v.PROFILE:self.reject_review(lambda r,k=key:r['finite_profile'].__setitem__(k,None))
 def test_25_direct_profile_rejected(self):
  p=copy.deepcopy(v.PROFILE);p['battle_flags']=1<<26
  with self.assertRaises(ValueError):v.compose_selected(self.raw,profile=p)
 def test_26_direct_contract_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract={})
 def test_27_invalid_cases(self):
  for a in(0,1,31,115,False,True,32.0):
   with self.subTest(ability=a),self.assertRaises(ValueError):v._compose(self.raw,a)
 def test_28_all_future_live_fields(self):
  c=v.compose_selected(self.raw)['cases'][0]
  for group in c['future_live_checkpoints']:
   for field in group['required_fields']:
    for a in range(field['address'],field['address']+field['size']):
     with self.subTest(pc=group['pc'],address=a),self.assertRaises(ValueError):v.compose_selected(self.raw,intervening_writes={group['pc']:[(a,1,0)]})
 def test_29_nonlive_write_allowed(self):
  out=v.compose_selected(self.raw,intervening_writes={pc:[(0x02017000,4,123)]for pc in v.CHECKPOINTS})
  self.assertTrue(out['nonlive_ram_erased_at_each_checkpoint'])
 def test_30_epoch_rejections(self):
  for pc in v.CHECKPOINTS:
   for event in('battle_context_epoch_changed','newbs_epoch_changed','script_epoch_changed','stack_epoch_changed'):
    with self.subTest(pc=pc,event=event),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={pc:{event:True}})
 def test_31_false_epoch_allowed(self):self.assertEqual(v.compose_selected(self.raw,epoch_events={pc:{'stack_epoch_changed':False}for pc in v.CHECKPOINTS})['opaque_calls'],0)
 def test_32_unknown_checkpoint(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,intervening_writes={0:[]})
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0:{}})
 def test_33_unknown_epoch(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={v.CHECKPOINTS[0]:{'unknown':False}})
 def test_34_geometry_strict(self):
  e=v.evidence_template(v.HITS[0]);self.assertEqual(v.witness_geometry(e),(0x090B69A8,6))
  for key in e:
   bad=copy.deepcopy(e);bad[key]=None
   with self.subTest(field=key),self.assertRaises(ValueError):v.witness_geometry(bad)
 def test_35_geometry_never_full_function(self):
  for a,n in((0x090B667C,0x1000),(0x090B69A9,4),(0x090B69A8,4),(0x090B69A8,8)):
   e=v.evidence_template(v.HITS[0]);e['classified_window']=dict(address=a,size=n)
   with self.subTest(window=(a,n)),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_36_no_extra_window(self):self.reject_review(lambda r:r['windows'].append(dict(address=0x090B6CBC,size=4,sha256='0'*64)))
 def test_37_no_reordered_window(self):self.reject_review(lambda r:r['windows'].reverse())
 def test_38_semantics_minimum_geometry(self):
  self.assertEqual(v.INS[0x090B69A8].size,4);self.assertEqual(v.INS[0x090B69AC].size,2);self.assertEqual(v.INS[0x090B69AC].args,('cmp',1,11))
 def test_39_sparse_unrelated_byte_allowed(self):self.assertEqual(self.check(raw=Mutation(self.raw,0x090B6C00))[1]['count'],1)
 def test_40_struct_declaration_mutation(self):
  for key,old,new in(('cfru-include--pokemon.h',b'u16 species;',b'u32 species;'),('cfru-include--battle.h',b'u8 dynamicMoveType;',b'u16 dynamicMoveType;'),('cfru-include--battle.h',b'bool8 skipCertainSwitchInAbilities : 1;',b'bool8 skipCertainSwitchInAbilities : 2;')):
   s=dict(self.sources);self.assertIn(old,s[key])
   if key=='cfru-include--pokemon.h':
    left,right=s[key].split(b'struct BattlePokemon',1);s[key]=left+b'struct BattlePokemon'+right.replace(old,new,1)
   else:s[key]=s[key].replace(old,new,1)
   with self.subTest(field=old),self.assertRaises(ValueError):v.source_layout(s)
 def test_41_layout_unknown_type(self):
  with self.assertRaises(ValueError):v.layout('unknown field;',{})
 def test_42_layout_bad_array(self):
  with self.assertRaises(ValueError):v.layout('u8 field[0];',{})
 def test_43_measure_scoped_windows(self):self.assertEqual(v.measure(self.raw),v.ALL_WINDOWS)
 def test_44_source_project_refs(self):
  self.assertEqual({r['commit']for r in v.SOURCE_IDS.values()if r['repository']=='dekaazarashi1111-web/pokemon-vega-modern'},{'d68ae32ed8d55e30d342ab8187dda48e6e16eb59'})
 def test_45_no_decoder_no_rom_fixture_in_module(self):
  import inspect
  source=inspect.getsource(v);self.assertNotIn('decode_thumb',source);self.assertNotIn('.gba',source);self.assertNotIn('read_bytes(',source)
if __name__=='__main__':unittest.main()
