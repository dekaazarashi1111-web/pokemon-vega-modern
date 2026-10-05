import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_union_failure as f
class UnionFailure(unittest.TestCase):
 def test_bound_stack(self):
  p=f.proof();self.assertEqual(p['stack_contract'],dict(mode=0,inner_return_offset=8,inner_return=0x0937767B,outer_return_offset=16,outer_return=0x08129A93));self.assertEqual(p['text_contract']['return_offset'],52)
 def test_reserved_after_current_payload(self):
  self.assertEqual((f.BASE,f.END),(0x09FFFB28,0x0A000000));self.assertIn('signed whole unallocated tail is actually FF',(ROOT/'scripts/pr16_dex_union_failure.py').read_text())
 def test_only_existing_state_write(self):
  s=(ROOT/f.SOURCE).read_text();self.assertNotIn('.bss',s);self.assertNotIn('.data',s);self.assertEqual(s.count('strh '),1);self.assertNotIn('strb ',s);self.assertIn('.word 0x09FFFB29',s)
 def test_scoped_string_and_original_scroll(self):
  s=(ROOT/f.SOURCE).read_text();self.assertIn('ldr r0,[sp,#52]',s);self.assertIn('mov r0,r9',s);self.assertIn('.word 0x0812ACBF',s);self.assertIn('.word 0x0812AF71',s)
 def test_failure_wait_and_original_success(self):
  p=f.proof();self.assertEqual(p['wait_contract']['error_exit_state'],12);s=(ROOT/f.SOURCE).read_text();self.assertIn('movs r0,#48',s);self.assertIn('movs r1,#3',s);self.assertIn('.word 0x08129AD1',s)
 def test_current_subowners_reject_old_mystery(self):
  import pr16_dex_subowners as sub
  with self.assertRaisesRegex(ValueError,'collision'):sub.require_codec_lease(0x09FC1D38,128)
  self.assertEqual(sub.available(),[dict(address=0x09FC1D36,size=2),dict(address=0x09FC22D0,size=28)])
 def test_dpcm_first_low_then_next_high_low(self):
  import pr16_dex_tail_lease as t
  self.assertEqual(t.dpcm(bytes([100,0xA1,0x23]),4),bytes([100,101,105,114]))
 def test_typed_tail_scope(self):
  import pr16_dex_tail_lease as t,json
  p=json.loads((ROOT/t.PROOF).read_bytes());self.assertEqual(p['scope']['size'],384);self.assertEqual(len(p['candidates']),16);self.assertEqual(len(p['roots']),12)
if __name__=='__main__':unittest.main()
