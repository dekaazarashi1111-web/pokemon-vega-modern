import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts')]
import pr16_dex_start_fault_ui as f
class FaultUI(unittest.TestCase):
 def test_closed_emulated_flash_fault_no_ram_or_cpu_fixture(self):self.assertGreater(f.validate_header((ROOT/f.HEADER).read_text())['size'],1000)
 def test_reject_host_write(self):
  s=(ROOT/f.HEADER).read_text()
  for extra in ['busWrite8(c,0,0);','writeRegister(c,"pc",0);','si_call(c,0);','loadState(c,0);']:
   with self.assertRaises(ValueError):f.validate_header(s+extra)
 def test_reject_removed_flash_scope(self):
  with self.assertRaises(ValueError):f.validate_header((ROOT/f.HEADER).read_text().replace('FLASH_COMMAND_PROGRAM','FLASH_COMMAND_ERASE'))
if __name__=='__main__':unittest.main()
