import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_mystery_failure as f
class MysteryFailure(unittest.TestCase):
 def test_exact_stack_and_message_boundaries(self):
  p=f.proof();self.assertEqual(p['stack_contract'],dict(mode=0,inner_return_offset=8,inner_return=0x0937767B,outer_return_offset=16,outer_return=0x08143287));self.assertEqual(p['mystery_menu']['message_patch'],0x08143288);self.assertEqual(p['mystery_menu']['new_keys'],0x0300315E)
 def test_existing_bounded_error_and_codec(self):
  p=f.proof();self.assertEqual(p['error_text']['address'],0x083E045B);self.assertEqual(p['error_text']['size'],23);self.assertEqual(p['retained_codec']['size'],5022);self.assertEqual((f.BASE,f.END),(0x09FC1D38,0x09FC22EC))
 def test_no_mutable_latch_or_destructive_call(self):
  s=(ROOT/f.SOURCE).read_text();self.assertNotIn('.bss',s);self.assertNotIn('.data',s)
  for x in ('str ','strb ','strh ','0x080F','0x080C6480'):self.assertNotIn(x,s)
  self.assertIn('ldr r1,[sp,#8]',s);self.assertIn('ldr r1,[sp,#16]',s);self.assertIn('.word 0x095FFEF1',s)
 def test_special_tail_continuation(self):
  s=(ROOT/f.SOURCE).read_text().split('VegaDexMysterySaveMessageTail:',1)[1];self.assertIn('cmp r0,#1',s);self.assertIn('.word 0x081432A1',s);self.assertIn('.word 0x08142C09',s);self.assertNotIn('push',s);self.assertNotIn('pop',s)
 def test_documented_caller_preserved(self):
  p=f.proof();self.assertEqual(len(p['windows']),7);self.assertTrue(all(x['size']>0 and len(x['sha256'])==64 for x in p['windows']))
if __name__=='__main__':unittest.main()
