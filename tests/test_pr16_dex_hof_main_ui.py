import sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_main_ui as u
class HofMainUi(unittest.TestCase):
 def test_exact_nine_byte_fixture_and_barriers(self):
  u.validate_header((ROOT/u.HEADER).read_text())
 def test_mutation_surface_rejected(self):
  s=(ROOT/u.HEADER).read_text()
  for extra in [' c->rawWrite8(c,0,0);',' cpu->gprs[0]=1;',' c->loadState(c,0);']:
   with self.assertRaises(ValueError):u.validate_header(s+extra)
 def test_five_cases_and_counter_scope(self):
  s=(ROOT/'scripts/pr16_dex_hof_main_ui.py').read_text();self.assertIn("[(3,'hof28-fault'),(4,'hof29-fault'),(1,'main-fault'),(2,'outer-fault'),(0,'healthy')]",s);self.assertIn('counter=102 if mode in(0,2)else 101',s);self.assertIn('whole changed copy and original RTC',s);self.assertIn('entire durable2048 QOL ledger exact',s)
  for mode,address in [(0,0xFFFFFFFF),(1,0),(2,131071),(3,28*4096),(4,29*4096)]:
   row=dict(fault_writes=0 if mode==0 else 3,fault_physical_address=address);u.validate_fault(row,mode)
   for bad in [dict(row,fault_writes=17),dict(row,fault_physical_address=131072)]:
    with self.assertRaises(ValueError):u.validate_fault(bad,mode)
 def test_closed_publication(self):
  import pr16_dex_publication as p
  p.contract(ROOT,u.WF,u.PUBLIC,u.ARTIFACT,'scripts/pr16_dex_hof_main_ui.py')
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaises(ValueError):p.output(Path(d))
if __name__=='__main__':unittest.main()
