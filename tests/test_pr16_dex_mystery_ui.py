import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_mystery_ui as f
class MysteryUI(unittest.TestCase):
 def test_closed_ui_fixture(self):self.assertGreater(f.validate_header((ROOT/f.HEADER).read_text())['size'],5000)
 def test_reject_register_and_generic_fixture(self):
  s=(ROOT/f.HEADER).read_text()
  for x in ('writeRegister(c,"pc",0);','si_call(c,0,0,0,0,0);','loadState(c,0);'):
   with self.assertRaises(ValueError):f.validate_header(s+x)
 def test_reject_duplicate_fixture(self):
  s=(ROOT/f.HEADER).read_text()
  with self.assertRaises(ValueError):f.validate_header(s+'mu_fixture(c,1);')
if __name__=='__main__':unittest.main()
