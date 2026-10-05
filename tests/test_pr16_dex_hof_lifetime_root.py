"""新局所callback証明だけを検証。旧受入suiteを再実行しない。"""
import copy,unittest
import pr16_dex_hof_lifetime_root as m
FIXTURE=None

class LifetimeRootTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise unittest.SkipTest('親runnerが新scope fixtureを明示供給する')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def test01_exact_partial_review(self):
  regions,proof=m._regions(self.raw,self.inherited,self.review,self.sources)
  self.assertEqual(regions,[]);self.assertEqual(proof['count'],0);self.assertEqual(proof['models'],129)
 def test02_all_slots_same_callback(self):
  for index in range(64):
   with self.subTest(slot=index):
    x=m.interpret_constructor(self.raw,index);self.assertEqual(x.r[0],m.SPRITES+68*index);self.assertEqual(x.r[1],m.CALLBACK|1)
 def test03_all_command_models(self):
  for index in range(64):
   with self.subTest(slot=index):
    x=m.interpret_command(self.raw,index);self.assertEqual(x.r[4],m.SPRITES+68*index);self.assertEqual(x.read(m.CURSOR,4),m.COMMAND+11)
 def test04_current_gate(self):
  inherited=copy.deepcopy(self.inherited);inherited['candidate']=m.CANDIDATE
  if m.ident(self.raw)==m.CANDIDATE:self.assertEqual(m.regions(self.raw,inherited,self.review,self.sources)[0],[])
  else:
   with self.assertRaisesRegex(ValueError,'current0641'):m.regions(self.raw,inherited,self.review,self.sources)
 def test05_unsupported_slots(self):
  for index in(-1,64,True,'0'):
   with self.subTest(slot=index),self.assertRaises(ValueError):m.interpret_constructor(self.raw,index)
 def test06_reject_new_acceptance(self):
  r=copy.deepcopy(self.review);r['claims']['newly_classified']=1
  with self.assertRaises(ValueError):m._regions(self.raw,self.inherited,r,self.sources)
 def test07_reject_root_claim(self):
  r=copy.deepcopy(self.review);r['claims']['full_root_to_hit_proven']=True
  with self.assertRaises(ValueError):m._regions(self.raw,self.inherited,r,self.sources)
 def test08_reject_donor_claim(self):
  r=copy.deepcopy(self.review);r['claims']['donor_eligible']=True
  with self.assertRaises(ValueError):m._regions(self.raw,self.inherited,r,self.sources)
 def test09_reject_removed_obligation(self):
  r=copy.deepcopy(self.review);r['unresolved_obligations'].pop()
  with self.assertRaises(ValueError):m._regions(self.raw,self.inherited,r,self.sources)
 def test10_reject_removed_window(self):
  r=copy.deepcopy(self.review);r['protected_windows'].pop()
  with self.assertRaises(ValueError):m._regions(self.raw,self.inherited,r,self.sources)
 def test11_reject_fake_trace(self):
  r=copy.deepcopy(self.review);r['models'][0]['instruction_count']-=1
  with self.assertRaises(ValueError):m._regions(self.raw,self.inherited,r,self.sources)
 def test12_reject_prior_accepted_hit(self):
  i=copy.deepcopy(self.inherited);next(x for x in i['hits']if x['address']==m.HIT)['accepted']=True
  with self.assertRaises(ValueError):m._regions(self.raw,i,self.review,self.sources)
 def test13_reject_owned_hit(self):
  i=copy.deepcopy(self.inherited);next(x for x in i['hits']if x['address']==m.HIT)['owner_candidates']=[1]
  with self.assertRaises(ValueError):m._regions(self.raw,i,self.review,self.sources)
 def test14_reject_missing_hit(self):
  i=copy.deepcopy(self.inherited);i['hits']=[x for x in i['hits']if x['address']!=m.HIT]
  with self.assertRaises(ValueError):m._regions(self.raw,i,self.review,self.sources)
 def test15_reject_duplicate_hit(self):
  i=copy.deepcopy(self.inherited);i['hits'].append(copy.deepcopy(next(x for x in i['hits']if x['address']==m.HIT)))
  with self.assertRaises(ValueError):m._regions(self.raw,i,self.review,self.sources)
 def test16_reject_source_change(self):
  for key in self.sources:
   with self.subTest(source=key):
    source=dict(self.sources);source[key]=source[key]+b'\n'
    with self.assertRaises(ValueError):m.bind_sources(source)
 def test17_reject_missing_extra_source(self):
  for remove in(True,False):
   source=dict(self.sources)
   if remove:source.pop(next(iter(source)))
   else:source['unknown.c']=b'no'
   with self.assertRaises(ValueError):m.bind_sources(source)
 def test18_mutate_all_dependency_windows(self):
  raw=bytearray(self.raw)
  for w in self.review['protected_windows']:
   with self.subTest(address=w['address'],size=w['size']):
    off=w['address']-m.BASE;raw[off]^=1
    with self.assertRaises(ValueError):m.fingerprint(raw,w)
    raw[off]^=1
 def test19_mutated_actual_callback(self):
  raw=bytearray(self.raw);raw[m.TEMPLATE+20-m.BASE]^=2
  with self.assertRaises(ValueError):m.interpret_constructor(raw)
 def test20_mutated_actual_dispatch(self):
  raw=bytearray(self.raw);raw[0x08371F8C+8-m.BASE]^=2
  with self.assertRaises(ValueError):m.finite_selection(raw)
 def test21_mutated_command_argv(self):
  raw=bytearray(self.raw);raw[m.COMMAND+6-m.BASE]=1
  with self.assertRaises(ValueError):m.interpret_command(raw)
 def test22_mutated_same_slot_stride(self):
  raw=bytearray(self.raw);raw[0x08006D8C-m.BASE]^=64
  with self.assertRaises(ValueError):m.interpret_constructor(raw,63)
 def test23_mutated_callback_store_field(self):
  raw=bytearray(self.raw);raw[0x08006C88-m.BASE]^=64
  with self.assertRaises(ValueError):m.interpret_constructor(raw)
 def test24_mutated_callback_load_field(self):
  raw=bytearray(self.raw);raw[0x08006DBE-m.BASE]^=64
  with self.assertRaises(ValueError):m.interpret_constructor(raw)
 def test25_reject_unbound_ram(self):
  x=m._seed(self.raw,0,True);x.mem.pop(0x02037E4E)
  with self.assertRaisesRegex(ValueError,'未束縛RAM'):x.run(0x080720C0,0x080DF98E)
 def test26_reject_opaque_call(self):
  x=m._seed(self.raw,0,False);x.code_ranges=tuple(v for v in x.code_ranges if v!=(0x081C9D98,0x081C9DF6))
  with self.assertRaisesRegex(ValueError,'未許可code'):x.run(0x08006D68,m.CALLBACK)
 def test27_reject_memory_alias(self):
  x=m._seed(self.raw,0,False);x.write_ranges=[(0x03007800,0x03007F00)]
  with self.assertRaisesRegex(ValueError,'許可域外write'):x.run(0x08006D68,m.CALLBACK)
 def test28_exhaustion_has_no_callback(self):
  x=m._seed(self.raw,0,False)
  for i in range(64):x.seed(m.SPRITES+i*68+62,1,1)
  x.run(0x08006D68,0x01000000)
  self.assertEqual(x.r[0],64);self.assertEqual(x.calls,[]);self.assertFalse(any(e['target']==m.CALLBACK for e in x.edges))
 def test29_finite_budget(self):
  x=m._seed(self.raw,0,False)
  with self.assertRaisesRegex(ValueError,'有限命令数'):x.run(0x08006D68,m.CALLBACK,limit=5)
 def test30_self_consistent_review_mutation_rejected(self):
  r=copy.deepcopy(self.review);raw=bytearray(self.raw);w=r['protected_windows'][0];raw[w['address']-m.BASE]^=1;w['sha256']=m.window(raw,w['address'],w['size'])['sha256']
  with self.assertRaisesRegex(ValueError,'独立固定'):m._regions(raw,self.inherited,r,self.sources)
 def test31_no_public_rawbytes(self):
  text=m.canonical(self.review).decode().lower()
  for forbidden in('rawhex','raw_bytes','rom_bytes','private-inputs','candidate.gba'):
   self.assertNotIn(forbidden,text)
 def test32_exact_minimal_hit_window(self):
  w=next(x for x in self.review['protected_windows']if x['address']==0x080DF988 and x['size']==6)
  self.assertLessEqual(w['address'],m.HIT);self.assertGreaterEqual(w['address']+w['size'],m.HIT+4)
 def test33_same_lifetime_no_task(self):
  x=m.interpret_command(self.raw)
  self.assertFalse(any(c['target']in(0x08076BB4,0x08076D10,0x08076CA0)for c in x.calls))
 def test34_frontier_unchanged(self):
  i=copy.deepcopy(self.inherited);r=copy.deepcopy(self.review)
  m._regions(self.raw,self.inherited,self.review,self.sources)
  self.assertEqual(i,self.inherited);self.assertEqual(r,self.review)
 def test35_bx_even_target_rejected(self):
  raw=(0x4700).to_bytes(2,'little')
  x=m.Machine(raw,[(m.BASE,m.BASE+2)],[]);x.r[0]=m.BASE+2
  with self.assertRaisesRegex(ValueError,'BXのThumb target bit'):x.run(m.BASE,m.BASE+2)
 def test36_bx_odd_target_preserves_thumb(self):
  raw=(0x4700).to_bytes(2,'little')
  x=m.Machine(raw,[(m.BASE,m.BASE+2)],[]);x.r[0]=m.BASE+3;x.run(m.BASE,m.BASE+2)
 def test37_thumb_mov_pc_even_target_is_not_bx(self):
  op=0x4400|(2<<8)|0x80|7
  x=m.Machine(op.to_bytes(2,'little'),[(m.BASE,m.BASE+2)],[]);x.r[0]=m.BASE+2;x.run(m.BASE,m.BASE+2)
 def test38_armv4t_pop_pc_even_target_keeps_thumb(self):
  op=0xBC00|0x100
  x=m.Machine(op.to_bytes(2,'little'),[(m.BASE,m.BASE+2)],[]);x.seed(x.r[13],4,m.BASE+2);x.run(m.BASE,m.BASE+2)
 def test39_reject_split_bl_code_window(self):
  raw=(0xF000).to_bytes(2,'little')+(0xF800).to_bytes(2,'little')
  x=m.Machine(raw,[(m.BASE,m.BASE+2)],[])
  with self.assertRaisesRegex(ValueError,'完全命令幅'):x.run(m.BASE,m.BASE+4)
 def test40_reject_unaligned_memory(self):
  x=m.Machine(bytes(16),[(m.BASE,m.BASE+16)],[(0x02000000,0x02000010)])
  for size in(2,4):
   with self.subTest(size=size),self.assertRaisesRegex(ValueError,'aligned'):x.read(m.BASE+1,size)
   with self.subTest(write=size),self.assertRaisesRegex(ValueError,'aligned'):x.write(0x02000001,size,0)
 def test41_reject_unsupported_memory_width(self):
  x=m.Machine(bytes(16),[(m.BASE,m.BASE+16)],[])
  with self.assertRaisesRegex(ValueError,'aligned'):x.read(m.BASE,3)
 def test42_reject_bl_second_halfword(self):
  raw=(0xF000).to_bytes(2,'little')+bytes(2)
  x=m.Machine(raw,[(m.BASE,m.BASE+4)],[])
  with self.assertRaisesRegex(ValueError,'完全ARMv4T BL'):x.run(m.BASE,m.BASE+4)
 def test43_reject_bx_blx_reserved_bit(self):
  op=0x4700|0x80
  x=m.Machine(op.to_bytes(2,'little'),[(m.BASE,m.BASE+2)],[]);x.r[0]=m.BASE+3
  with self.assertRaisesRegex(ValueError,'ARMv4T BX'):x.run(m.BASE,m.BASE+2)
 def test44_reject_high_register_pc_source(self):
  op=0x4400|(2<<8)|(15<<3)
  x=m.Machine(op.to_bytes(2,'little'),[(m.BASE,m.BASE+2)],[])
  with self.assertRaisesRegex(ValueError,'PC source operand'):x.run(m.BASE,m.BASE+2)
 def test45_reject_add_to_pc(self):
  op=0x4400|0x80|7
  x=m.Machine(op.to_bytes(2,'little'),[(m.BASE,m.BASE+2)],[]);x.r[0]=2
  with self.assertRaisesRegex(ValueError,'ADD PC'):x.run(m.BASE,m.BASE+2)
 def test46_prefix_alpha_real_callees(self):
  x=m.interpret_alpha(self.raw);self.assertEqual(x.read(m.CURSOR,4),0x081B498E);self.assertEqual(len(x.calls),2)
 def test47_prefix_alpha_no_hardware_write(self):
  x=m.interpret_alpha(self.raw)
  self.assertFalse(any(0x04000000<=w['address']<0x05000000 for w in x.writes))
 def test48_mutated_alpha_dispatch(self):
  raw=bytearray(self.raw);raw[0x08371F8C+12*4-m.BASE]^=2
  with self.assertRaises(ValueError):m.interpret_alpha(raw)
 def test49_proof_has_only_window_identity(self):
  _,p=m._regions(self.raw,self.inherited,self.review,self.sources)
  self.assertNotIn('protected_read_windows',p);self.assertEqual(p['protected_read_identity'],m.ident(m.canonical(self.review['protected_windows'])))
 def test50_reject_high_cmp_first_pc_operand(self):
  op=0x4400|(1<<8)|0x80|7
  x=m.Machine(op.to_bytes(2,'little'),[(m.BASE,m.BASE+2)],[])
  with self.assertRaisesRegex(ValueError,'CMP PC source operand'):x.run(m.BASE,m.BASE+2)
 def test51_preconditions_not_runtime_or_universal(self):
  p=self.review['preconditions'];self.assertFalse(p['entry_producers_proven']);self.assertFalse(p['arbitrary_entry_states_covered'])
  self.assertIn('no_IRQ_DMA',p['execution_mode']);self.assertEqual(p['initial_nzcv'],[False]*4)
  self.assertTrue(self.review['claims']['no_asynchronous_interference_assumed'])
 def test52_reject_weakened_preconditions(self):
  r=copy.deepcopy(self.review);r['preconditions']['arbitrary_entry_states_covered']=True
  with self.assertRaises(ValueError):m._regions(self.raw,self.inherited,r,self.sources)
 def test53_reject_transient_free_and_reuse(self):
  slot=m.SPRITES;writes=[{'address':slot+62,'size':1,'value':v}for v in(0,1,0,1)]
  with self.assertRaisesRegex(ValueError,'clear/reuse'):m.same_slot_lifetime(writes,slot)
 def test54_reject_overlapping_word_clear(self):
  slot=m.SPRITES;writes=[{'address':slot+62,'size':1,'value':1},{'address':slot+60,'size':4,'value':0},{'address':slot+62,'size':1,'value':1}]
  with self.assertRaisesRegex(ValueError,'clear/reuse'):m.same_slot_lifetime(writes,slot)
 def test55_require_actual_inuse_producer(self):
  with self.assertRaisesRegex(ValueError,'実inUse producer'):m.same_slot_lifetime([],m.SPRITES)
 def test56_real_lifetime_suffixes(self):
  for method in(m.interpret_constructor,m.interpret_command):
   x=method(self.raw);p=m.same_slot_lifetime(x.writes,m.SPRITES);self.assertFalse(p['clear_after_producer']);self.assertGreater(p['live_suffix_writes'],0)
if __name__=='__main__':unittest.main()
