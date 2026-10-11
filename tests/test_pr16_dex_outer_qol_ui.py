import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_outer_qol_actions as f
class OuterUI(unittest.TestCase):
 def test_closed_flash_fault(self):self.assertGreater(f.validate_header((ROOT/f.HEADER).read_text())['size'],1000)
 def test_reject_host_fixture(self):
  s=(ROOT/f.HEADER).read_text()
  for x in ['busWrite8(c,0,0);','writeRegister(c,"pc",0);','loadState(c,0);']:
   with self.assertRaises(ValueError):f.validate_header(s+x)
 def test_exact_last_byte_fault_only(self):
  with self.assertRaises(ValueError):f.validate_header((ROOT/f.HEADER).read_text().replace('oq_target=31u*4096u+4095u','oq_target=0'))
if __name__=='__main__':unittest.main()
