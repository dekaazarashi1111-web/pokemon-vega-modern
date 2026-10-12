"""新background4最小payload型だけの反証。private ROM path/原payloadを含まない。"""
import copy,hashlib,json,unittest,struct,binascii
from unittest import mock
import pr16_dex_hof_animation_background_roots as v
FIXTURE=None
class Mutation:
 def __init__(self,raw,a):self.raw,self.offset=raw,a-0x8000000
 def __len__(self):return len(self.raw)
 def __getitem__(self,s):
  b=bytearray(self.raw[s])
  if s.start<=self.offset<s.stop:b[self.offset-s.start]^=1
  return bytes(b)
class BackgroundRootsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('新scope sparse FIXTUREと保存review読戻しが必要')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def check(self,raw=None,inherited=None,review=None,sources=None):return v._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def reject_review(self,change):
  r=copy.deepcopy(self.review);change(r)
  with self.assertRaises((ValueError,TypeError,KeyError)):self.check(review=r)
 def test_01_exact_four_minimums(self):
  before=copy.deepcopy(self.inherited);rs,p=self.check();self.assertEqual([(r.start,r.end,r.kind)for r in rs],[(h,h+4,v.KIND)for h in v.HITS]);self.assertEqual(before,self.inherited);self.assertEqual(p['count'],4);self.assertFalse(p['donor_eligible'])
 def test_02_saved_review_roundtrip(self):self.check(review=json.loads(json.dumps(self.review)))
 def test_03_whole_source_assets_independent(self):
  p=self.check()[1]['serialization'];self.assertEqual(sorted(a['source_tile_count']for a in p['assets']),[279,302,447]);self.assertTrue(all(a['whole_decoded_equal']and a['padding_excluded']for a in p['assets']))
 def test_04_no_move_index_translation(self):
  self.assertEqual(sorted(r['index']for r in v.ROOTS.values()),[386,678,874]);self.assertFalse(self.check()[1]['serialization']['public_move_index_translation_used'])
 def test_05_complete_source_prefixes(self):
  chunks,rows=v.serialize_animation_sources(self.sources);self.assertEqual([r['size']for r in rows],[9,32,126,7,7,2,1]);self.assertEqual(sum(r['size']for r in rows),184)
  for a,b in chunks.items():self.assertEqual(v.chunk(self.raw,a,len(b)),b)
 def test_06_complete_runtime_producers(self):
  p=self.check()[1]['composition'];self.assertEqual([r['instruction_steps']for r in p['cases']],[604,588,622]);self.assertEqual([len(r['conditional_call_groups'])for r in p['cases']],[6,5,5])
  for r in p['cases']:self.assertEqual(r['scheduler_invocations'],3);self.assertTrue(r['real_task_registration']);self.assertFalse(r['callback_or_bg_host_seeded']);self.assertTrue(r['nonlive_ram_erased_at_every_boundary'])
 def test_07_actual_source_byte_read(self):
  for case,root in v.ROOTS.items():
   p=v._compose(self.raw,case);site=0x8072f92 if case=='giga'else 0x8072f4e
   self.assertIn((site,root['command']+1,1,root['bg_id']),p['reads'])
 def test_08_real_task_and_bg_writer(self):
  for case,root in v.ROOTS.items():
   p=v._compose(self.raw,case);self.assertIn((0x8076bce,v.TASKS,4,0x8072ff5),p['writes']);self.assertIn((0x8073054,v.TASKS+8,2,root['bg_id']),p['reads'])
 def test_09_real_descriptor_image_read(self):
  for case,a in v.ASSETS.items():self.assertIn((0x80730e6,a['descriptor_address'],4,a['address']),v._compose(self.raw,case)['reads'])
 def test_10_all_instruction_bytes(self):
  for i in v.INS.values():
   for j in range(i.size):
    with self.subTest(address=i.address+j):self.assertNotEqual(v.chunk(Mutation(self.raw,i.address+j),i.address,i.size),v.encoded(i))
 def test_11_all_literal_bytes(self):
  for a,x in v.WORDS.items():
   for j in range(4):self.assertNotEqual(v.d.u32(Mutation(self.raw,a+j),a),x)
 def test_12_every_protected_byte_rejected(self):
  for w in v.FIXED_WINDOWS:
   for a in range(w['address'],w['address']+w['size']):
    with self.subTest(address=a),self.assertRaises(ValueError):v.d.signed(Mutation(self.raw,a),w)
 def test_13_every_protected_byte_reseal_rejected(self):
  for index,w in enumerate(v.FIXED_WINDOWS):
   for a in range(w['address'],w['address']+w['size']):
    raw=Mutation(self.raw,a);r=dict(self.review);r['windows']=[dict(x)for x in self.review['windows']];r['windows'][index]['sha256']=hashlib.sha256(v.chunk(raw,w['address'],w['size'])).hexdigest()
    with self.subTest(address=a),self.assertRaises(ValueError):self.check(raw=raw,review=r)
 def test_14_all_serializer_bytes_rejected(self):
  chunks,_=v.serialize_animation_sources(self.sources)
  for a,b in chunks.items():
   for j in range(len(b)):self.assertNotEqual(v.chunk(Mutation(self.raw,a+j),a,len(b)),b)
 def test_15_source_every_binding(self):
  for name,b in self.sources.items():
   s=dict(self.sources);s[name]=b+b'\n'
   with self.subTest(name=name),self.assertRaises(ValueError):v.sources_bind(self.review,s)
 def test_16_source_missing_extra(self):
  for name in self.sources:
   with self.subTest(name=name),self.assertRaises(ValueError):v.sources_bind(self.review,{k:b for k,b in self.sources.items()if k!=name})
  with self.assertRaises(ValueError):v.sources_bind(self.review,{**self.sources,'extra':b''})
 def test_17_source_hash_reseal_rejected(self):
  for name in self.sources:self.reject_review(lambda r:r['source_bindings'][name].update(sha256='0'*64))
 def test_18_png_crc_and_extent(self):
  for a in v.ASSETS.values():
   b=self.sources[a['source_png']]
   for corrupt in(b[:-1],b+b'\0',b[:30]+bytes([b[30]^1])+b[31:]):
    with self.assertRaises((ValueError,struct.error)):v.png_pixels(corrupt)
 def test_19_source_flags_closed(self):
  for a in v.ASSETS.values():
   with self.assertRaises(ValueError):v.encode_tiles(self.sources[a['source_png']],b'-gB4')
 def test_20_lz_header_failure(self):
  for a in v.ASSETS.values():
   with self.assertRaises(ValueError):v.d.decode_lz_at(Mutation(self.raw,a['address']),a['address'],16384)
 def test_21_lz_payload_source_match_rejects(self):
  for a in v.ASSETS.values():
   with self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,a['address']+a['size']//2),self.sources)
 def test_22_lz_extent_review_reseal_rejected(self):
  for k in v.ASSETS:self.reject_review(lambda r:r['assets'][k].update(size=r['assets'][k]['size']+1))
 def test_23_only_four_bytes_classified(self):
  for h in v.HITS:
   e=v.evidence_template(h);self.assertEqual(v.witness_geometry(e),(h,4));e['classified_window']['size']=8
   with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_24_whole_asset_geometry_rejected(self):
  for h in v.HITS:
   e=v.evidence_template(h);e['classified_window']={k:e['asset'][k]for k in('address','size')}
   with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_25_all_witness_claims_closed(self):
  for h in v.HITS:
   for k,x in v.CLAIMS.items():
    if type(x)is bool:
     e=v.evidence_template(h);e[k]=not x
     with self.subTest(hit=h,key=k),self.assertRaises(ValueError):v.witness_geometry(e)
 def test_26_nested_witness_fields_closed(self):
  for h in v.HITS:
   for change in(lambda e:e.update(extra=True),lambda e:e.update(root_verified=False),lambda e:e['root'].update(index=1),lambda e:e['asset'].update(bg_id=0),lambda e:e['input_contract'].update(extra='x')):
    e=v.evidence_template(h);change(e)
    with self.assertRaises(ValueError):v.witness_geometry(e)
 def test_27_review_schema_and_bool_closed(self):
  for change in(lambda r:r.update(extra=True),lambda r:r.update(schema_version=True),lambda r:r.pop('roots')):self.reject_review(change)
 def test_28_parent_unknown_rows_exact(self):
  for key,value in(('accepted',True),('accepted',0),('classification','DATA'),('owner_candidates',['x']),('size',True),('kind','POINTER'),('reason','other'),('target',0)):
   i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review);h=next(h for h in i['hits']if h['address']==v.HITS[0]);h[key]=value;r['hits'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(inherited=i,review=r)
 def test_29_parent_order_duplicate_missing(self):
  for change in(lambda i:i['hits'].reverse(),lambda i:i['hits'].append(copy.deepcopy(next(h for h in i['hits']if h['address']==v.HITS[0]))),lambda i:i.update(hits=[h for h in i['hits']if h['address']!=v.HITS[0]])):
   i=copy.deepcopy(self.inherited);change(i)
   with self.assertRaises(ValueError):self.check(inherited=i)
 def test_30_unrelated_rows_unchanged(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(dict(address=0x8000000,accepted=True));before=copy.deepcopy(i);self.check(inherited=i);self.assertEqual(i,before)
 def test_31_current_diagnostic_separated(self):
  self.reject_review(lambda r:r.update(diagnostic_input=v.CANDIDATE));self.reject_review(lambda r:r.update(required_candidate=v.DIAGNOSTIC))
  i=copy.deepcopy(self.inherited);i['candidate']=v.DIAGNOSTIC
  with self.assertRaises(ValueError):self.check(inherited=i)
 def test_32_public_wrapper_rejects_diagnostic(self):
  with mock.patch.object(v,'identity',return_value=v.DIAGNOSTIC),mock.patch.object(v,'_regions')as inner:
   with self.assertRaises(ValueError):v.regions(*FIXTURE)
   inner.assert_not_called()
 def test_33_public_wrapper_current_delegates(self):
  with mock.patch.object(v,'identity',return_value=v.CANDIDATE),mock.patch.object(v,'_regions',return_value=('r','p'))as inner:
   self.assertEqual(v.regions(*FIXTURE),('r','p'));inner.assert_called_once()
 def test_34_review_claims_closed(self):
  for k,x in v.CLAIMS.items():
   if type(x)is bool:self.reject_review(lambda r:r['claims'].update({k:not x}))
 def test_35_fixed_window_closure(self):
  for change in(lambda r:r['windows'].reverse(),lambda r:r['windows'].pop(),lambda r:r['windows'][0].update(size=1),lambda r:r['windows'][0].update(extra=True)):self.reject_review(change)
 def test_36_every_profile_value_closed(self):
  for k,x in v.PROFILE.items():
   p=copy.deepcopy(v.PROFILE);p[k]=not x if type(x)is bool else x+1
   with self.subTest(key=k),self.assertRaises(ValueError):v.compose_selected(self.raw,profile=p)
 def test_37_contract_closed(self):
  p=copy.deepcopy(v.CONTRACT);p['extra']='all effects succeed'
  with self.assertRaises(ValueError):v.compose_selected(self.raw,contract=p)
 def test_38_all_live_bytes_rejected(self):
  p=v.compose_selected(self.raw)
  for c in p['cases']:
   for g in c['conditional_call_groups']:
    for a,n in g['required_fields']:
     for off in range(n):
      with self.assertRaises(ValueError):v.preservation_contract(g['required_fields'],[(a+off,1,0)])
 def test_39_nonlive_writes_survive(self):
  p=v.compose_selected(self.raw,opaque_writes={0:[(0x2004000,4,0x12345678)],0x80730e0:[(0x2004004,4,0)]});self.assertEqual(len(p['cases']),3)
 def test_40_epoch_reuse_rejected(self):
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0:dict(task_epoch_changed=True)})
 def test_41_dead_task_epoch_not_frozen(self):
  p=v.compose_selected(self.raw,epoch_events={0x80730e0:dict(task_epoch_changed=True)});self.assertEqual(len(p['cases']),3)
 def test_42_unknown_site_or_epoch_rejected(self):
  for key in('opaque_writes','epoch_events'):
   with self.assertRaises(ValueError):v.compose_selected(self.raw,**{key:{0xdeadbeef:[]}})
  with self.assertRaises(ValueError):v.compose_selected(self.raw,epoch_events={0:dict(all_heap_changed=False)})
 def test_43_fade_output_not_ambient_seed(self):
  p=v.compose_selected(self.raw)
  for c in p['cases']:
   g=next(g for g in c['conditional_call_groups']if g['site']==0x807301c);self.assertEqual(g['target'],0x8070a08);self.assertEqual(g['conditional_outputs'],[dict(address=v.PALETTE+7,size=1,value=128)])
   self.assertTrue(any(g['frame_interval_completion_condition']and g['conditional_outputs']==[dict(address=v.PALETTE+7,size=1,value=0)]for g in c['conditional_call_groups']))
 def test_44_tilemap_return_is_explicit_unproven_boundary(self):
  for c in v.compose_selected(self.raw)['cases']:
   g=next(g for g in c['conditional_call_groups']if g['site']==0x80730e0);self.assertEqual(g['target'],0x800e574);self.assertFalse(g['effects_discharged']);self.assertEqual(g['required_fields'],[])
 def test_45_swi12_complete_opcode_mutated(self):
  for j in range(4):
   with self.assertRaises(ValueError):v.bind_semantics(Mutation(self.raw,0x81c7a8c+j),self.sources)
 def test_46_source_rows_and_cell_roots_not_swap(self):
  for k in v.ROOTS:self.reject_review(lambda r:r['roots'][k].update(command=r['roots'][k]['command']+1))
  for k in v.ASSETS:self.reject_review(lambda r:r['assets'][k].update(descriptor_address=r['assets'][k]['descriptor_address']+12))

 def test_47_png_resealed_geometry_and_filter(self):
  for a in v.ASSETS.values():
   b=bytearray(self.sources[a['source_png']]);b[19]^=1;b[29:33]=(binascii.crc32(b[12:29])&0xffffffff).to_bytes(4,'big')
   with self.assertRaises(ValueError):v.png_pixels(bytes(b))
 def test_48_read_callback_from_same_slot(self):
  for case in v.ROOTS:
   p=v._compose(self.raw,case)
   self.assertEqual([x for x in p['reads']if x[0]==0x8076d28],[(0x8076d28,v.TASKS,4,0x8072ff5)]*3)
