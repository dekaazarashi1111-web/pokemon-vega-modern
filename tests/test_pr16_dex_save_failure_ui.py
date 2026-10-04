import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_save_failure_ui as u
class NegativeUI(unittest.TestCase):
 def test_single_crc_exception_with_seven_barriers(self):u.validate_header((ROOT/u.HEADER).read_text())
 def test_no_extra_write_exception(self):
  s=(ROOT/u.HEADER).read_text()
  for extra in ['sf_fixture_write8(c,0,0);','si_restore(c,0);','si_call(c,0);','write_register(c,0);']:
   with self.assertRaises(ValueError):u.validate_header(s+extra)
 def test_barrier_must_precede_first_frame(self):
  s=(ROOT/u.HEADER).read_text().replace('si_guard(c);','')
  with self.assertRaises(ValueError):u.validate_header(s+'si_guard(c);')
if __name__=='__main__':unittest.main()
