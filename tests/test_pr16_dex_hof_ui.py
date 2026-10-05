import sys,unittest,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_hof_ui as f
class HofUI(unittest.TestCase):
 def test_closed_header(self):f.validate_header((ROOT/f.HEADER).read_text())
 def test_exact_nine_byte_fixture(self):
  p=json.loads((ROOT/f.BINDINGS).read_bytes());self.assertEqual(p['ui_only_fixture']['addresses'],list(range(0x03003130,0x03003138))+[0x03003568]);self.assertEqual(p['ui_only_fixture']['bytes'],9)
 def test_no_automatic_retry_and_payload_lifetime(self):
  s=(ROOT/f.HEADER).read_text();self.assertIn('hu_payload_check(c);hu_payload_checked_at_ack=1;hu_display_started=1;',s);self.assertIn('hu_stock_calls==1',s);self.assertIn('hu_stat_calls==1',s);self.assertIn('hu_tick(c,2)',s)
 def test_closed_publication(self):
  import pr16_dex_publication as p
  p.contract(ROOT,f.WF,f.PUBLIC,f.ARTIFACT,'scripts/pr16_dex_hof_ui.py')
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaises(ValueError):p.output(Path(d))
if __name__=='__main__':unittest.main()
