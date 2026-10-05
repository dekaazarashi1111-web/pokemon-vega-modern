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
 def test_publication_paths_match(self):
  import pr16_dex_publication as p,pr16_dex_union_formatter_actions as f
  p.contract(ROOT,u.WF,u.PUBLIC,'pr16-dex-union-ui-text-only','scripts/pr16_dex_union_ui.py')
  p.contract(ROOT,f.WF,f.PUBLIC,'pr16-dex-union-formatter-text-only','scripts/pr16_dex_union_formatter_actions.py')
 def test_empty_or_wrong_directory_rejected(self):
  import pr16_dex_publication as p,tempfile
  with tempfile.TemporaryDirectory()as d:
   with self.assertRaises(ValueError):p.output(Path(d))
  with self.assertRaises(ValueError):p.contract(ROOT,u.WF,ROOT/'wrong-output','pr16-dex-union-ui-text-only','scripts/pr16_dex_union_ui.py')
if __name__=='__main__':unittest.main()
