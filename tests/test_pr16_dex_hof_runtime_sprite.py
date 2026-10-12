"""新連続経路だけ。既受入129model/56testを呼び出さない。"""
import copy,json,unittest
from unittest.mock import patch
import pr16_dex_hof_runtime_sprite as s
FIXTURE=None

class ProofTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise unittest.SkipTest('診断/Actionsが固定fixtureを注入する')
  cls.raw,cls.inherited,cls.review,cls.sources=FIXTURE
 def checked(self,raw=None,inherited=None,review=None,sources=None):
  return s._regions(self.raw if raw is None else raw,self.inherited if inherited is None else inherited,self.review if review is None else review,self.sources if sources is None else sources)
 def changed_seed(self,modifier):
  original=s.seed
  def seed(m):original(m);modifier(m)
  with patch.object(s,'seed',seed):return s.interpret(self.raw)
 def changed_hook(self,pc,modifier):
  hooks=dict(s.HOOKS);original=hooks[pc]
  def call(m,a):original(m,a);modifier(m)
  hooks[pc]=call
  with patch.object(s,'HOOKS',hooks):return s.interpret(self.raw)
 def test_new_conditional_region_exactly_one(self):
  rows,proof=self.checked();self.assertEqual(len(rows),1);self.assertEqual(proof['count'],1);self.assertEqual(proof['prior_models_rerun'],0)
  self.assertEqual((rows[0].start,rows[0].end),(0x080DF988,0x080DF98E));self.assertEqual(proof['instruction_count'],6194)
 def test_parent_input_not_modified(self):
  before=copy.deepcopy(self.inherited);self.checked();self.assertEqual(before,self.inherited)
 def test_current_wrapper_rejects_modified_whole_input(self):
  raw=bytearray(self.raw);raw[-1]^=1
  with self.assertRaises(ValueError):s.regions(bytes(raw),self.inherited,self.review,self.sources)
 def test_every_dependency_window_mutation_rejected(self):
  raw=bytearray(self.raw)
  for row in self.review['protected_windows']:
   a=row['address']-s.BASE
   with self.subTest(address=row['address'],size=row['size']):
    raw[a]^=1
    try:
     with self.assertRaises(ValueError):self.checked(raw=raw)
    finally:raw[a]^=1
 def test_source_mutations_rejected(self):
  for key,value in self.sources.items():
   changed=dict(self.sources);changed[key]=value[:-1]+bytes([value[-1]^1])
   with self.subTest(source=key),self.assertRaises(ValueError):self.checked(sources=changed)
 def test_missing_source_rejected(self):
  changed=dict(self.sources);changed.pop(next(iter(changed)))
  with self.assertRaises(ValueError):self.checked(sources=changed)
 def test_extra_source_rejected(self):
  with self.assertRaises(ValueError):self.checked(sources={**self.sources,'unbound':b''})
 def test_review_fields_cannot_be_relaxed(self):
  for key,value in [('safe_capacity_bytes',1),('donor_eligible',True),('natural_battle_reachability_claimed',True),('all_callees_concretely_executed',True),('newly_classified',2)]:
   r=copy.deepcopy(self.review);r['claims'][key]=value
   with self.subTest(claim=key),self.assertRaises(ValueError):self.checked(review=r)
 def test_review_precondition_cannot_be_deleted(self):
  r=copy.deepcopy(self.review);r['preconditions'].pop('external_helpers')
  with self.assertRaises(ValueError):self.checked(review=r)
 def test_review_contract_cannot_be_promoted(self):
  r=copy.deepcopy(self.review);r['external_contracts']['AllocZeroed_success_nonalias']['kind']='proven'
  with self.assertRaises(ValueError):self.checked(review=r)
 def test_model_trace_cannot_be_forged(self):
  r=copy.deepcopy(self.review);r['model']['instruction_count']+=1
  with self.assertRaises(ValueError):self.checked(review=r)
 def test_missing_protection_rejected(self):
  r=copy.deepcopy(self.review);r['protected_windows'].pop()
  with self.assertRaises(ValueError):self.checked(review=r)
 def test_duplicate_protection_rejected(self):
  r=copy.deepcopy(self.review);r['protected_windows'].append(r['protected_windows'][0])
  with self.assertRaises(ValueError):s.protected_windows(r)
 def test_parent_hit_must_be_unknown(self):
  changed=copy.deepcopy(self.inherited);next(h for h in changed['hits']if h['address']==s.HIT)['accepted']=True
  with self.assertRaises(ValueError):self.checked(inherited=changed)
 def test_parent_hit_must_be_unowned(self):
  changed=copy.deepcopy(self.inherited);next(h for h in changed['hits']if h['address']==s.HIT)['owner_candidates']=['invented']
  with self.assertRaises(ValueError):self.checked(inherited=changed)
 def test_duplicate_parent_hit_rejected(self):
  changed=copy.deepcopy(self.inherited);changed['hits'].append(copy.deepcopy(next(h for h in changed['hits']if h['address']==s.HIT)))
  with self.assertRaises(ValueError):self.checked(inherited=changed)
 def test_missing_parent_hit_rejected(self):
  changed=copy.deepcopy(self.inherited);changed['hits']=[h for h in changed['hits']if h['address']!=s.HIT]
  with self.assertRaises(ValueError):self.checked(inherited=changed)
 def test_complete_prefix_and_two_wait_entries(self):
  m=s.interpret(self.raw);pcs=[x['address']for x in m.trace]
  for pc in (0x08071D40,0x090C6654,0x08071D78,0x0807200C,0x090C5D08,0x080723D4,0x0807396C,0x08072D84,0x0807336C,0x080720C0,0x080DF984,0x080DF988,0x080DF98C):self.assertIn(pc,pcs)
  self.assertEqual(pcs.count(0x08071FA0),2);self.assertNotIn(0x08076D10,pcs)
 def test_registry_values_are_produced_after_empty_input(self):
  m=s.Machine(self.raw,s.CODE,s.WRITES,s.HOOKS);s.seed(m)
  self.assertEqual(m.read(0x03000AE8,2),65535);self.assertEqual(m.read(0x03000DE8,2),65535)
  m=s.interpret(self.raw)
  self.assertIn({'address':0x03000AE8,'size':2,'value':10027},m.writes)
  self.assertIn({'address':0x03000DE8,'size':2,'value':10027},m.writes)
  self.assertIsNone(m.live_alloc)
 def test_background_task_success_not_exhaustion_return_zero(self):
  m=s.interpret(self.raw);self.assertEqual(m.read(0x030050D4,1),1);self.assertEqual(m.read(0x030050D0,4),0x08072919)
 def test_missing_battle_input_rejected(self):
  with self.assertRaises(ValueError):self.changed_seed(lambda m:m.mem.pop(0x02023CCB))
 def test_wrong_move_rejected(self):
  with self.assertRaises(ValueError):self.changed_seed(lambda m:m.r.__setitem__(0,42))
 def test_sprite_exhaustion_rejected(self):
  with self.assertRaises(ValueError):self.changed_seed(lambda m:[m.seed(s.SPRITES+i*68+62,1,1)for i in range(64)])
 def test_tile_exhaustion_rejected(self):
  with self.assertRaises(ValueError):self.changed_seed(lambda m:[m.seed(0x02021AC4+i,1,255)for i in range(128)])
 def test_palette_exhaustion_rejected(self):
  with self.assertRaises(ValueError):self.changed_seed(lambda m:[m.seed(0x03000DE8+i*2,2,0)for i in range(16)])
 def test_task_exhaustion_rejected(self):
  with self.assertRaises(ValueError):self.changed_seed(lambda m:[m.seed(0x030050D0+i*40+4,1,1)for i in range(16)])
 def test_allocation_failure_rejected(self):
  hooks=dict(s.HOOKS)
  def fail(m,pc):m.r[0]=0
  hooks[0x08002BB0]=fail
  with patch.object(s,'HOOKS',hooks),self.assertRaises(ValueError):s.interpret(self.raw)
 def test_scratch_alias_rejected(self):
  with patch.object(s,'SCRATCH',s.CURSOR),self.assertRaises(ValueError):s.interpret(self.raw)
 def test_background_buffer_alias_rejected(self):
  with self.assertRaises(ValueError):self.changed_seed(lambda m:m.seed(0x02022B18,4,s.SPRITES-4096))
 def test_callee_saved_clobber_rejected(self):
  with self.assertRaises(ValueError):self.changed_hook(0x08047814,lambda m:m.r.__setitem__(4,m.r[4]^1))
 def test_return_address_clobber_rejected(self):
  with self.assertRaises(ValueError):self.changed_hook(0x08047814,lambda m:m.r.__setitem__(14,m.r[14]+2))
 def test_hidden_external_seed_write_rejected(self):
  with self.assertRaises(ValueError):self.changed_hook(0x08047814,lambda m:m.seed(s.CURSOR,4,1))
 def test_control_clobber_by_external_write_rejected(self):
  with self.assertRaises(ValueError):self.changed_hook(0x08047814,lambda m:m.write(s.CURSOR,4,0))
 def test_r12_clobbered_at_every_boundary(self):
  m=s.interpret(self.raw);self.assertTrue(m.contract_calls)
  self.assertEqual(m.read(s.SPRITES+136+28,4),s.prior.CALLBACK|1)
 def test_wrong_free_rejected(self):
  m=s.Machine(self.raw,(),(),{});m.live_alloc=(s.SCRATCH,32);m.r[0]=s.SCRATCH+4
  with self.assertRaises(ValueError):s.free(m,0x08002BC4)
 def test_complete_instruction_geometry(self):
  rows,_=self.checked();e=rows[0].evidence
  self.assertEqual(s.geometry(e),(0x080DF988,6));self.assertLessEqual(0x080DF988,s.HIT);self.assertLessEqual(s.HIT+4,0x080DF98E)
  for key,value in [('literal_pool_included',True),('full_story_reachability_claimed',True),('root_verified',False)]:
   changed=copy.deepcopy(e);changed[key]=value
   with self.subTest(field=key),self.assertRaises(ValueError):s.geometry(changed)
 def test_geometry_claims_remain_conditional(self):
  rows,_=self.checked();e=copy.deepcopy(rows[0].evidence);e['claims']['donor_eligible']=True
  with self.assertRaises(ValueError):s.geometry(e)
 def test_new_register_shift_semantics(self):
  for kind in (2,3,4):
   for amount in (0,1,31,32,33,255):
    for value in (0,1,0x80000000,0xFFFFFFFF):
     op=0x4000|(kind<<6)|(1<<3);raw=op.to_bytes(2,'little');m=s.Machine(raw,((s.BASE,s.BASE+2),),())
     m.r[0]=value;m.r[1]=amount;m.flags=[False,False,True,False];m.run(s.BASE,s.BASE+2)
     signed=value-(1<<32)if value&0x80000000 else value
     expected=value if amount==0 else ((value<<amount)&0xFFFFFFFF if kind==2 and amount<32 else 0)if kind==2 else (value>>amount if amount<32 else 0)if kind==3 else (signed>>min(amount,32))&0xFFFFFFFF
     with self.subTest(kind=kind,amount=amount,value=value):self.assertEqual(m.r[0],expected)
 def test_multiply_carry_dependency_rejected(self):
  raw=(0x4348).to_bytes(2,'little')+(0xD200).to_bytes(2,'little')
  m=s.Machine(raw,((s.BASE,s.BASE+4),),());m.r[:2]=[2,3]
  with self.assertRaises(ValueError):m.run(s.BASE,s.BASE+4)
 def test_multiply_compare_redefines_carry(self):
  raw=b''.join(v.to_bytes(2,'little')for v in(0x4348,0x2806,0xD200))
  m=s.Machine(raw,((s.BASE,s.BASE+6),),());m.r[:2]=[2,3];m.run(s.BASE,s.BASE+8)
  self.assertTrue(m.flags[2])
 def test_unknown_r12_consumption_rejected(self):
  raw=(0x4460).to_bytes(2,'little')
  m=s.Machine(raw,((s.BASE,s.BASE+2),),());m.r[12]=s.UNDEFINED_R12
  with self.assertRaises(ValueError):m.run(s.BASE,s.BASE+2)
 def test_unmodeled_code_is_not_silently_assumed(self):
  m=s.Machine(self.raw,(),(),{})
  with self.assertRaises(ValueError):m.run(0x08071D40,s.STOP)

if __name__=='__main__':unittest.main()
