"""部分consumerの実値流れと、未証明rootの昇格拒否を検査する。"""
import copy,unittest
import pr16_dex_hof_battle_continuation as v
FIXTURE=None
class ContinuationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if FIXTURE is None:raise RuntimeError('現candidate、または明示旧診断fixtureを注入する')
  cls.raw,cls.sources=FIXTURE;cls.review=v.diagnostic(cls.raw,cls.sources)
 def mutate(self,a,z,value):
  raw=bytearray(self.raw);raw[a-v.d.BASE:a-v.d.BASE+z]=value.to_bytes(z,'little');return bytes(raw)
 def rejects_native(self,a,z,value,cursor=v.STATUS_COMMANDS[0]):
  with self.assertRaises(ValueError):v.interpret_status(self.mutate(a,z,value),cursor)
 def test_all_sixteen_finite_models(self):self.assertEqual(len(self.review['models']),16)
 def test_both_callees_interpreted(self):
  for m in self.review['models']:self.assertEqual([c['target']for c in m['calls']],[0x090D3D2C,0x090D6268])
 def test_entry_to_return_74_actual_instructions(self):
  for m in self.review['models']:self.assertEqual(len(m['instructions']),74)
 def test_one_cursor_write_no_hidden_memorywrite(self):
  for m in self.review['models']:self.assertEqual(m['writes'],[{'address':v.CURSOR,'size':4,'value':m['command']+10}])
 def test_all_twelve_stack_writes_recorded(self):
  for m in self.review['models']:self.assertEqual(len(m['stack_writes']),12)
 def test_callback_and_callee_save_preserved(self):
  for m in self.review['models']:self.assertTrue(m['callback_preserved']and m['callee_saved_registers_preserved'])
 def test_zero_classifications(self):self.assertEqual(v.validate_partial_review(self.raw,self.review),[])
 def test_ten_unproven_retained(self):self.assertEqual(self.review['unproven_hit_addresses'],list(v.UNPROVEN))
 def test_promotion_always_refused(self):
  with self.assertRaises(ValueError):v.regions(self.raw,self.review)
 def test_proof_cannot_relabel_as_full_root(self):
  j=copy.deepcopy(self.review);j['models'][0]['full_root_chain_proven']=True
  with self.assertRaises(ValueError):v.validate_partial_review(self.raw,j)
 def test_proof_cannot_relabel_new_classification(self):
  j=copy.deepcopy(self.review);j['newly_classified']=1
  with self.assertRaises(ValueError):v.validate_partial_review(self.raw,j)
 def test_wrong_current_rom_refused(self):
  with self.assertRaises(ValueError):v.current_partial_review(b'not a ROM',self.sources)
 def test_source_tampering(self):
  s=dict(self.sources);s['src/attackcanceler.c']+=b'\n'
  with self.assertRaises(ValueError):v.diagnostic(self.raw,s)
 def test_missing_source(self):
  s=dict(self.sources);s.pop('BPRJ.ld')
  with self.assertRaises(ValueError):v.diagnostic(self.raw,s)
 def test_entry_return_cannot_fake_advance(self):self.rejects_native(v.HANDLER,2,0x4770)
 def test_resolver_entry_return_rejected(self):self.rejects_native(0x090D3D2C,2,0x4770)
 def test_substitute_entry_return_rejected(self):self.rejects_native(0x090D6268,2,0x4770)
 def test_cursor_literal_redirect_to_callback(self):self.rejects_native(0x0910754C,4,v.CALLBACK)
 def test_cursor_literal_redirect_to_target(self):self.rejects_native(0x0910754C,4,v.TARGET)
 def test_bank_literal_redirect_to_cursor(self):self.rejects_native(0x090D3DA4,4,v.CURSOR)
 def test_status_base_redirect_to_callback(self):self.rejects_native(0x090D6290,4,v.CALLBACK)
 def test_wrong_advance(self):self.rejects_native(0x09107528,2,0x3309)
 def test_store_wrong_base(self):self.rejects_native(0x0910752A,2,0x6023)
 def test_missing_call_rejected(self):self.rejects_native(0x091074DC,4,0x46C046C0)
 def test_full_branch_field_required(self):self.rejects_native(v.STATUS_COMMANDS[0]+6,4,v.CURSOR)
 def test_bank_selector_change_rejected(self):self.rejects_native(v.STATUS_COMMANDS[0]+1,1,1)
 def test_dispatch_slot_change_rejected(self):self.rejects_native(v.PRIMARY+29*4,4,0x08021E51)
 def test_unknown_bank_refused(self):
  with self.assertRaises(ValueError):v.interpret_status(self.raw,v.STATUS_COMMANDS[0],4)
 def test_unknown_command_refused(self):
  with self.assertRaises(ValueError):v.interpret_status(self.raw,v.STATUS_COMMANDS[0]+1)
 def test_minimal_public_review_zero_regions(self):
  j=v.public_review(self.raw,self.sources);regions,proof=v.measured_partial(self.raw,j,self.sources)
  self.assertEqual(regions,[]);self.assertEqual(proof['count'],0)
 def test_minimal_public_window_binding_change(self):
  j=v.public_review(self.raw,self.sources);j['protected_windows'][0]['sha256']='0'*64
  with self.assertRaises(ValueError):v.measured_partial(self.raw,j,self.sources)
 def test_minimal_public_missing_stack_write_binding(self):
  j=v.public_review(self.raw,self.sources);j['models'][0]['stack_write_count']=0
  with self.assertRaises(ValueError):v.measured_partial(self.raw,j,self.sources)
 def test_minimal_public_execution_identity_change(self):
  j=v.public_review(self.raw,self.sources);j['models'][0]['execution_identity']['sha256']='0'*64
  with self.assertRaises(ValueError):v.measured_partial(self.raw,j,self.sources)
 def test_minimal_public_root_promotion_rejected(self):
  j=v.public_review(self.raw,self.sources);j['root_frontier']['common_attackcanceler_closed']=True
  with self.assertRaises(ValueError):v.measured_partial(self.raw,j,self.sources)
 def test_current_partial_rejects_wrong_rom(self):
  with self.assertRaises(ValueError):v.current_partial(b'not a ROM',{},self.sources)
if __name__=='__main__':unittest.main(verbosity=2)
