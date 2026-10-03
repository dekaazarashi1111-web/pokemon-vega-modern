"""原本保持の負例。emulator/networkなし。偽鍵fixtureの完全一致以外は拒否。"""
import io
from pathlib import Path
import sys
import unittest
import warnings
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_bp_progress_checkpoint as c


def archive(items):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,data in items:z.writestr(name,data)
    return out.getvalue()


class RetentionTests(unittest.TestCase):
    def test_plain_text(self):c.scan(archive([('notes.txt',b'bounded notes')]))
    def test_path_and_private_payloads(self):
        for name in ('../a.txt','/a.txt','a\\b.txt','game.gba','save.srm','patch.bps','nested.zip'):
            with self.subTest(name=name),self.assertRaises(ValueError):c.scan(archive([(name,b'test')]))
    def test_binary_and_unapproved_marker(self):
        marker=b'-----BEGIN '+b'OPENSSH PRIVATE KEY-----'
        for data in (b'\0',marker):
            with self.assertRaises(ValueError):c.scan(archive([('notes.txt',data)]))
    def test_exact_existing_negative_fixture_only(self):
        path='tests/test_pr16_bp_chooser_checkpoint.py';raw=(c.ROOT/path).read_bytes()
        c.scan(archive([('sources.zip',archive([(path,raw)]))]))
        for name,data in [(path,raw+b'\n'),('other.py',raw)]:
            with self.subTest(name=name),self.assertRaises(ValueError):c.scan(archive([('sources.zip',archive([(name,data)]))]))
    def test_duplicate_and_symlink(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');raw=archive([('x.txt',b'a'),('x.txt',b'b')])
        with self.assertRaises(ValueError):c.scan(raw)
        symlink=zipfile.ZipInfo('x.txt');symlink.create_system=3;symlink.external_attr=0o120777<<16
        with self.assertRaises(ValueError):c.scan(archive([(symlink,b'target')]))
    def test_outer_pin_and_original_conclusions(self):
        for pin in c.PINS:
            with self.assertRaises(ValueError):c.verify(b'not-original',pin)
        self.assertEqual([p[6] for p in c.PINS],['success','failure','success'])
    def test_no_emulator_calls(self):
        text=(c.ROOT/c.SELF).read_text()
        self.assertNotIn('native.run(',text);self.assertNotIn('release_ready=True',text)

if __name__=='__main__':unittest.main()
