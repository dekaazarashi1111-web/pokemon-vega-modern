import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_union_ui as u
class UnionUI(unittest.TestCase):
 def test_closed_fixture_and_observation(self):self.assertGreater(u.validate_header((ROOT/u.HEADER).read_text())['size'],1000)
 def test_register_write_rejected(self):
  with self.assertRaises(ValueError):u.validate_header((ROOT/u.HEADER).read_text()+'\nvoid evil(){cpu->gprs[2]=1;}\n')
 def test_general_fixture_rejected(self):
  with self.assertRaises(ValueError):u.validate_header((ROOT/u.HEADER).read_text()+'\nvoid evil(){si_restore();}\n')
if __name__=='__main__':unittest.main()
