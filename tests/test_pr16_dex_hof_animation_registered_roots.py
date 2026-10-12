"""登録animation2最小型の新scope試験。旧suite/native/全ROM scanは行わない。"""
import copy,hashlib,unittest
from unittest import mock
import pr16_dex_hof_animation_registered_roots as v
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

class AnimationRegisteredTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('保存review JSON読戻しと新scope sparse FIXTUREが必要')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):
  return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,KeyError,TypeError)):self.check(review=r)
 def test_01_exact_two_minimums_parent_unchanged(self):
  before=copy.deepcopy(self.inherited);regions,proof=self.check()
  self.assertEqual([(r.start,r.end,r.kind)for r in regions],[(h-1,h+5,v.KIND)for h in v.HITS]);self.assertEqual(before,self.inherited)
  self.assertFalse(proof['donor_eligible']);self.assertEqual(proof['count'],2)
 def test_02_full_source_serialization(self):
  p=self.check()[1]['serialization'];self.assertEqual(p['complete_field_count'],173);self.assertEqual(p['complete_serialized_bytes'],320)
  self.assertEqual(p['source_numeric_or_equ_fields'],156);self.assertEqual(p['actual_registered_pointer_fields'],17)
  self.assertEqual(p['actual_registration_indices'],[879,926,927]);self.assertFalse(p['public_table_index_translation_used'])
 def test_03_actual_producer_paths(self):
  proof=self.check()[1]['composition'];self.assertEqual([c['instruction_steps']for c in proof['cases']],[95,347]);self.assertEqual([len(c['conditional_call_groups'])for c in proof['cases']],[3,11])
  for c in proof['cases']:self.assertFalse(c['callback_pointer_host_seeded']);self.assertTrue(c['nonlive_ram_erased_at_each_boundary']);self.assertFalse(c['hit_callee_executed'])
 def test_04_same_slot_actual_writer_read(self):
  m=v._compose(self.raw,'star')
  self.assertIn((0x08006C86,0x09038704,4,0x090C4B91),m['consumer_reads'])
  self.assertIn((0x08006C88,v.SPRITES+28,4,0x090C4B91),m['consumer_writes'])
  self.assertIn((0x08006DBE,v.SPRITES+28,4,0x090C4B91),m['consumer_reads'])
  self.assertIn(0x081C7ACC,m['visited'])
 def test_05_actual_all_arg_writers(self):
  for case,count,argindex,value in(('single',1,0,0),('star',6,2,1)):
   m=v._compose(self.raw,case);site=0x080721F6 if case=='single'else 0x08072102
   writes=[w for w in m['consumer_writes']if w[0]==site]
   self.assertEqual([w[1]for w in writes],[v.ARGS+2*j for j in range(count)])
   self.assertEqual(writes[argindex][3],value)
   self.assertIn((0x090BF788,v.ARGS+2*argindex,2,value),m['consumer_reads'])
 def test_06_minimum_geometry_complete_bl_and_ldr(self):
  for hit in v.HITS:
   e=v.evidence_template(hit);self.assertEqual(v.witness_geometry(e),(hit-1,6));ins=e['complete_instructions']
   self.assertEqual([i['kind']for i in ins],['call','literal']);self.assertEqual([i['size']for i in ins],[4,2]);self.assertEqual([i['address']for i in ins],[hit-1,hit+3])
 def test_07_hit_and_successor_are_not_executed(self):
  for case,root in v.ROOTS.items():
   m=v._compose(self.raw,case);self.assertNotIn(root['stop'],m['visited']);self.assertNotIn(root['static_successor'],m['visited'])
   self.assertEqual(m['registers'][:2],[0,1]if case=='single'else[1,1])
 def test_08_all_instruction_bytes_mutated(self):
  for ins in v.INS.values():
   for a in range(ins.address,ins.address+ins.size):
    with self.subTest(address=a),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a),self.sources)
 def test_09_all_literal_dispatch_fields_mutated(self):
  for a in v.WORDS:
   for j in range(4):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+j),self.sources)
 def test_10_all_serializer_fields_mutated(self):
  for a,n in v.REQUIRED_WINDOWS.items():
   for j in range(n):
    with self.subTest(address=a+j),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a+j),self.sources)
 def test_11_all_oam_bytes_mutated(self):
  self.assertEqual(len(v.encode_oam(self.sources)),8)
  self.assertEqual(sum(w for _,w,_ in v.OAM_FIELDS),64)
  for j in range(8):
   with self.subTest(byte=j),self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,0x08370AC0+j),self.sources)
 def test_12_every_protected_byte_resealed_rejected(self):
  for row in v.FIXED_WINDOWS:
   for a in range(row['address'],row['address']+row['size']):
    raw=Mutation(self.raw,a);review=copy.deepcopy(self.review);inherited=copy.deepcopy(self.inherited);reseal(review,raw);reseal(inherited,raw)
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=review,inherited=inherited)
 def test_13_each_source_full_identity(self):
  for name,b in self.sources.items():
   sources=dict(self.sources);sources[name]=b+b'\n'
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources=sources)
 def test_14_source_missing_extra(self):
  for name in self.sources:
   with self.subTest(source=name),self.assertRaises(ValueError):self.check(sources={k:b for k,b in self.sources.items()if k!=name})
  with self.assertRaises(ValueError):self.check(sources={**self.sources,'extra':b''})
 def test_15_source_binding_reseal_does_not_authorize(self):
  for name in self.sources:self.reject_review(lambda r:r['source_bindings'][name].update(sha256='0'*64))
 def test_16_review_schema_closed(self):
  self.reject_review(lambda r:r.update(extra=True));self.reject_review(lambda r:r.update(schema_version=True));self.reject_review(lambda r:r.pop('roots'))
 def test_17_current_diagnostic_exact_separation(self):
  self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE));self.reject_review(lambda r:r.update(required_candidate=v.DIAGNOSTIC))
  i=copy.deepcopy(self.inherited);i['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_18_public_wrapper_rejects_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_19_public_wrapper_current_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value=('regions','proof'))as inner:
   self.assertEqual(v.regions(*FIXTURE),('regions','proof'));inner.assert_called_once()
 def test_20_witness_claims_reject_overstatement(self):
  for hit in v.HITS:
   e=v.evidence_template(hit)
   for key,value in v.CLAIMS.items():
    if type(value)is bool:
     bad=copy.deepcopy(e);bad[key]=not value
     with self.subTest(hit=hit,key=key),self.assertRaises(ValueError):v.witness_geometry(bad)
 def test_21_witness_all_nested_geometry_closed(self):
  for hit in v.HITS:
   for change in(lambda e:e.update(extra=True),lambda e:e.update(root_verified=False),lambda e:e['classified_window'].update(size=4),lambda e:e['root'].update(callback=e['root']['callback']+2),lambda e:e['complete_instructions'][1].update(size=4),lambda e:e['input_contract'].update(extra='x')):
    bad=v.evidence_template(hit);change(bad)
    with self.assertRaises(ValueError):v.witness_geometry(bad)
 def test_22_review_claims_closed(self):
  for key,value in v.CLAIMS.items():
   if type(value)is bool:
    with self.subTest(key=key):self.reject_review(lambda r:r['claims'].update({key:not value}))
 def test_23_no_public_index_substitution(self):
  self.reject_review(lambda r:r['roots']['single'].update(table_indices=[808]))
  self.reject_review(lambda r:r['roots']['star'].update(table_indices=[855,856]))
  self.assertEqual(v.WORDS[0x08071D74],0x0904A6D4)
 def test_24_parent_unknowns_exact(self):
  for key,value in(('accepted',True),('accepted',0),('classification','CODE'),('owner_candidates',['x']),('size',True),('kind','POINTER')):
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][key]=value;r['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_25_parent_hit_order_duplicate_missing(self):
  for change in(lambda i:i['hits'].reverse(),lambda i:i['hits'].append(copy.deepcopy(i['hits'][0])),lambda i:i['hits'].pop()):
   i=copy.deepcopy(self.inherited);change(i)
   with self.assertRaises(ValueError):self.check(inherited=i)
 def test_26_unrelated_parent_unchanged(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(dict(address=0x08000000,accepted=True));before=copy.deepcopy(i);self.check(inherited=i);self.assertEqual(before,i)
 def test_27_protected_windows_order_size_closed(self):
  self.reject_review(lambda r:r['windows'].reverse());self.reject_review(lambda r:r['windows'][0].update(size=r['windows'][0]['size']+2))
 def test_28_every_profile_value_closed(self):
  for key,value in v.PROFILE.items():
   profile=copy.deepcopy(v.PROFILE);profile[key]=not value if type(value)is bool else value+1
   with self.subTest(key=key),self.assertRaises(ValueError):v.compose_selected(self.raw,profile=profile)
 def test_29_contract_closed(self):
  contract=copy.deepcopy(v.CONTRACT);contract['minimum_ja']='all calls succeed'
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract=contract)
  self.reject_review(lambda r:r['input_contract'].update(extra=True));self.reject_review(lambda r:r['finite_profile'].update(sprite_slot=63))
 def test_30_all_opaque_live_bytes_rejected(self):
  p=v.compose_selected(self.raw)
  for c in p['cases']:
   for g in c['conditional_call_groups']:
    fields=[[r['address'],r['size']]for r in g['required_fields']]
    for a,n in fields:
     for j in range(n):
      with self.subTest(site=g['site'],address=a+j),self.assertRaises(ValueError):v.preservation_contract(fields,[(a+j,1,0)])
 def test_31_each_opaque_site_nonlive_allowed(self):
  for site,_ in v.EXTERNAL:
   p=v.compose_selected(self.raw,opaque_writes={site:[(0x02011000,4,0xAABBCCDD)]})
   self.assertEqual(p['status'],'PASS_TWO_REGISTERED_ANIMATION_MINIMUMS')
 def test_32_live_callback_pointer_clobber_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={0x08006C9C:[(v.SPRITES+28,4,0x090C4B91)]})
 def test_33_actual_arg_clobber_rejected(self):
  for site,address in((0x08072208,v.ARGS),(0x08072154,v.ARGS+4)):
   with self.subTest(site=site),self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={site:[(address,2,1)]})
 def test_34_live_sprite_epoch_rejected(self):
  p=v.compose_selected(self.raw)
  for c in p['cases']:
   for g in c['conditional_call_groups']:
    if g['sprite_epoch_required']:
     with self.subTest(site=g['site']),self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={g['site']:{'sprite_epoch_changed':True}})
 def test_35_nonlive_epoch_allowed(self):
  for site in(0x08072208,0x090C5BCE,0x090C5BE4,0x08072154):
   self.assertEqual(v.compose_selected(self.raw,epoch_events={site:{'sprite_epoch_changed':True}})['status'],'PASS_TWO_REGISTERED_ANIMATION_MINIMUMS')
 def test_36_closed_boundary_event_domains(self):
  for kwargs in({'opaque_writes':{0:[(0x02011000,1,0)]}},{'epoch_events':{0:{}}},{'epoch_events':{0x08072208:{'other':False}}},{'epoch_events':{0x08072208:{'sprite_epoch_changed':0}}}):
   with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):v.compose_selected(self.raw,**kwargs)
 def test_37_closed_write_geometry(self):
  for write in((True,1,0),(0x02011000,0,0),(0x02011000,8,0),(0xFFFFFFFF,4,0),(0x02011000,1,256)):
   with self.subTest(write=write),self.assertRaises(ValueError):v.preservation_contract([],writes=[write])
 def test_38_case_domain_and_hit_domain(self):
  for case in(True,None,0,'other'):
   with self.assertRaises(ValueError):v._compose(self.raw,case)
  for hit in(True,0,0x090C4BC0,0x090C5BFC):
   with self.assertRaises(ValueError):v.evidence_template(hit)
 def test_39_shift_branch_flag_provenance(self):
  for flags,expected in((0,0x1008),(1,0x1004)):
   ins={0x1000:v.party.Ins(0x1000,'shift',('lsl',2,2,31)),0x1002:v.party.Ins(0x1002,'branch',(5,0x1008))}
   m=v.Machine(self.raw,0x1000,{2:flags},instructions=ins);m.step();self.assertEqual(bool(m.flags[0]),bool(flags))
   m.step();self.assertEqual(m.pc,expected)
 def test_40_unknown_flags_do_not_choose_branch(self):
  ins={0x1000:v.party.Ins(0x1000,'branch',(5,0x1004))};m=v.Machine(self.raw,0x1000,instructions=ins)
  with self.assertRaises(ValueError):m.step()
 def test_41_sbc_and_shift_zero_preserve_cmp_carry(self):
  ins={i.address:i for i in v.party.block(0x1000,[('compare',1,0),('alu_ext','sbc',1,1),('literal',3,0x08071D74),('shift','lsl',0,4,0),('alu_ext','neg',1,1)])}
  for value,result in((0,0),(1,0),(2,1),(3,1)):
   m=v.Machine(self.raw,0x1000,{0:value,1:1,4:0},instructions=ins)
   for _ in range(5):m.step()
   self.assertEqual(m.reg[1],result)
 def test_42_minimum_reseal_cannot_expand(self):
  for hit in v.HITS:
   e=v.evidence_template(hit);e['classified_window']['address']=hit;e['classified_window']['size']=4
   with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_43_serializer_layout_no_extra_commands(self):
  self.reject_review(lambda r:r['serializer_layout'][0].update(command_count=23));self.reject_review(lambda r:r['serializer_layout'].reverse())
  chunks,rows=v.serialize_animation_sources(self.sources);self.assertEqual([len(r['commands'])for r in rows],[22,23,1,1]);self.assertEqual(sum(len(b)for b in chunks.values()),332)
 def test_44_fixed_footprint_new_scope_only(self):
  self.assertEqual(len(v.INS),390);self.assertEqual(len(v.FIXED_WINDOWS),35);self.assertEqual(sum(w['size']for w in v.FIXED_WINDOWS),1286)
  self.assertEqual(v.TYPE_CATEGORY,'code');self.assertEqual(v.KINDS,(v.KIND,));self.assertEqual(v.HELD_HITS,())
 def test_45_parent_all_fields_resealed_do_not_change(self):
  for key,value in(('target',0),('reason','other'),('sha256','0'*64)):
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);i['hits'][0][key]=value;r['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_46_consumer_callbacks_cannot_be_replaced(self):
  for a in(0x09032235,0x09038704):
   for j in range(4):
    raw=Mutation(self.raw,a+j);r=copy.deepcopy(self.review);reseal(r,raw)
    with self.subTest(address=a+j),self.assertRaises(ValueError):self.check(raw=raw,review=r)
 def test_47_expected_hit_inventory_is_fixed(self):
  self.assertEqual(self.review['hits'],v.EXPECTED_HITS)
  self.assertEqual([r['address']for r in v.EXPECTED_HITS],list(v.HITS))
  self.assertEqual([r['root']['hit']for r in[v.evidence_template(h)for h in v.HITS]],list(v.HITS))
 def test_48_nonread_inuse_clear_is_epoch_destruction(self):
  for site in(0x090C4B9E,0x090C4BB6):
   for address,n,value in((v.SPRITES+62,1,0),(v.SPRITES+60,4,0)):
    with self.subTest(site=site),self.assertRaises(ValueError):v.compose_selected(self.raw,opaque_writes={site:[(address,n,value)]})
 def test_49_live_inuse_nonlive_upper_bits_allowed(self):
  self.assertEqual(v.compose_selected(self.raw,opaque_writes={0x090C4BB6:[(v.SPRITES+62,1,129)]})['status'],'PASS_TWO_REGISTERED_ANIMATION_MINIMUMS')
