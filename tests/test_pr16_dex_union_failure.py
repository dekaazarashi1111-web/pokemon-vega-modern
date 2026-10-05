import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_union_failure as f
class UnionFailure(unittest.TestCase):
 def test_bound_stack(self):
  p=f.proof();self.assertEqual(p['stack_contract'],dict(mode=0,inner_return_offset=8,inner_return=0x0937767B,outer_return_offset=16,outer_return=0x08129A93));self.assertEqual(p['text_contract']['return_offset'],52)
 def test_reserved_after_current_payload(self):
  self.assertEqual((f.BASE,f.END),(0x09FC1DB8,0x09FC22EC));self.assertIn('every prospective suffix byte actually blank',(ROOT/'scripts/pr16_dex_union_failure.py').read_text())
 def test_only_existing_state_write(self):
  s=(ROOT/f.SOURCE).read_text();self.assertNotIn('.bss',s);self.assertNotIn('.data',s);self.assertEqual(s.count('strh '),1);self.assertNotIn('strb ',s);self.assertIn('.word 0x09FC1D39',s)
 def test_scoped_string_and_original_scroll(self):
  s=(ROOT/f.SOURCE).read_text();self.assertIn('ldr r0,[sp,#52]',s);self.assertIn('mov r0,r9',s);self.assertIn('.word 0x0812ACBF',s);self.assertIn('.word 0x0812AF71',s)
 def test_failure_wait_and_original_success(self):
  p=f.proof();self.assertEqual(p['wait_contract']['error_exit_state'],12);s=(ROOT/f.SOURCE).read_text();self.assertIn('movs r0,#48',s);self.assertIn('movs r1,#3',s);self.assertIn('.word 0x08129AD1',s)
if __name__=='__main__':unittest.main()
