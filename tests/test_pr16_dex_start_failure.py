import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_valid_failure as f
class StartFailure(unittest.TestCase):
 def test_only_signed_start_callback_and_modes(self):
  p=f.proof();self.assertEqual(p['callback'],0x0806F131);self.assertEqual(p['modes'],[0,4]);self.assertEqual([w['address']for w in p['windows']],[0x0806F130,0x0806F16C])
 def test_existing_gate_retained_with_explicit_failure_owner(self):
  s=(ROOT/f.SOURCE).read_text();self.assertIn('DEX_ENTRY_VegaDexValidate',s);self.assertIn('cmp r5,#0',s);self.assertIn('cmp r5,#4',s);self.assertIn('0x03000FA4',s);self.assertIn('0x0806F131',s);self.assertNotIn('.data',s);self.assertNotIn('.bss',s)
  for op in ['str ','strb ','strh ']:self.assertNotIn(op,s)
  cp=f.checkpoint();self.assertEqual(cp['candidate']['sha256'],'d3dcb55ad09a509fa247e65a3ca3db1de4bdd5b5534288b2b03ddbacca65b314');self.assertEqual(len(cp['updated_gates']['measurement']['placement']['allocation']['allocations']),111)
 def test_all_byte_modes_do_not_imply_all_mode_acceptance(self):
  for callback in [0,0x0806F131,0x0806F16D,0x080F3195]:
   for mode in range(256):self.assertEqual(callback==0x0806F131 and mode in(0,4),callback==f.proof()['callback']and mode in f.proof()['modes'])
if __name__=='__main__':unittest.main()
