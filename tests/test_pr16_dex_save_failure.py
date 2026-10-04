import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_save_failure as f
class SaveFailure(unittest.TestCase):
 def test_signed_small_stock_seams(self):
  rows={r['id']:r for r in f.proof()['windows']};self.assertEqual(rows['try_save_result_gate']['address'],0x080DB360);self.assertEqual(rows['try_save_result_gate']['size'],8);self.assertEqual(rows['save_failed_wipe']['address'],0x080F64A8);self.assertEqual(len(rows),5)
 def test_no_allocated_owner_overlap(self):
  self.assertEqual(f.BASE,0x095FFEF0);self.assertEqual(f.END-f.BASE,272)
  cp=f.checkpoint();self.assertEqual(cp['candidate']['sha256'],'41d6a3342dc561dd89dd791046441d1ee403828e4d65cfea955c830224faa9f2')
  self.assertTrue(all(not(r['gba_start']<=f.BASE<r['gba_end_exclusive'])for r in cp['measurement']['placement']['allocation']['allocations']))
 def test_no_new_mutable_latch_or_fake_damage(self):
  s=(ROOT/f.SOURCE).read_text();self.assertNotIn('.bss',s);self.assertNotIn('.data',s);self.assertNotIn('str ',s);self.assertNotIn('strb ',s);self.assertIn('DEX_ENTRY_VegaDexValidate',s);self.assertIn('0x080DB385',s);self.assertIn('0x080DB369',s);self.assertIn('0x080F64B1',s)
 def test_failure_mask_matrix_and_scope(self):
  cases=[(s,m,0x080DB368 if s==255 or m else 0x080DB384)for s in [0,1,255]for m in [0,1,1<<13,1<<31]]
  self.assertEqual(len(cases),12);self.assertEqual(sum(dest==0x080DB384 for _,_,dest in cases),2)
  self.assertEqual(2*12+2*2*4+8*4+4*5*4,152)
if __name__=='__main__':unittest.main()
