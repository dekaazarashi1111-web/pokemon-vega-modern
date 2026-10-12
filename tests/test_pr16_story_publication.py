from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pr16_story_route_probe import export_evidence
class PublicationTests(unittest.TestCase):
    def paths(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);base=Path(d.name);a=base/'private-artifact';a.mkdir();return a,base/'public-evidence'
    def test_only_verified_text_screens(self):
        a,z=self.paths();(a/'data.json').write_text('{"scope":"evidence"}\n');(a/'stdout.txt').write_text('normal commands\n');(a/'screen.ppm').write_bytes(b'P6\n240 160\n255\n'+bytes(115200));self.assertEqual(export_evidence(a,z),['data.json','screen.ppm','stdout.txt']);self.assertEqual((z/'data.json').read_bytes(),(a/'data.json').read_bytes())
    def test_rom_rejected_before_public_directory(self):
        a,z=self.paths();(a/'candidate.gba').write_bytes(b'input')
        with self.assertRaises(ValueError):export_evidence(a,z)
        self.assertFalse(z.exists())
    def test_hidden_file_rejected_before_public_directory(self):
        a,z=self.paths();(a/'.hidden.txt').write_text('unapproved')
        with self.assertRaises(ValueError):export_evidence(a,z)
        self.assertFalse(z.exists())
    def test_symlink_rejected_before_public_directory(self):
        a,z=self.paths();(a/'data.json').write_text('{}');(a/'link.txt').symlink_to(a/'data.json')
        with self.assertRaises(ValueError):export_evidence(a,z)
        self.assertFalse(z.exists())
if __name__=='__main__':unittest.main()
