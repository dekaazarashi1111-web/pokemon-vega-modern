"""Fail-closed archive and reconciliation tests; no emulator execution."""
import io
from pathlib import Path
import sys
import unittest
import warnings
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_bp_chooser_checkpoint as c


def archive(entries):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for name,data in entries:z.writestr(name,data)
    return out.getvalue()

class ArchiveTests(unittest.TestCase):
    def test_plain_safe_source(self):c.scan(archive([('notes.txt',b'diagnostic only')]))
    def test_safe_named_nested_source(self):c.scan(archive([('sources.zip',archive([('code.c',b'int example;')]))]))
    def test_rom_rejected(self):
        with self.assertRaises(ValueError):c.scan(archive([('test.gba',b'no')]))
    def test_nested_save_rejected(self):
        with self.assertRaises(ValueError):c.scan(archive([('sources.zip',archive([('test.sav',b'no')]))]))
    def test_unknown_archive_rejected(self):
        with self.assertRaises(ValueError):c.scan(archive([('private.zip',archive([('file.c',b'hi')]))]))
    def test_traversal(self):
        with self.assertRaises(ValueError):c.scan(archive([('../notes.txt',b'no')]))
    def test_absolute(self):
        with self.assertRaises(ValueError):c.scan(archive([('/notes.txt',b'no')]))
    def test_backslash(self):
        with self.assertRaises(ValueError):c.scan(archive([('a\\notes.txt',b'no')]))
    def test_duplicate(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore');raw=archive([('notes.txt',b'a'),('notes.txt',b'b')])
        with self.assertRaises(ValueError):c.scan(raw)
    def test_binary(self):
        with self.assertRaises(ValueError):c.scan(archive([('notes.txt',b'\0')]))
    def test_invalid_screenshot(self):
        with self.assertRaises(ValueError):c.scan(archive([('screen.ppm',b'P6\n')]))
    def test_digest_required(self):
        with self.assertRaises(ValueError):c.verify(b'wrong',c.PINS[1])
    def test_private_key_marker(self):
        with self.assertRaises(ValueError):c.scan(archive([('key.txt',b'-----BEGIN OPENSSH PRIVATE KEY-----')]))
    def test_no_missing_evidence(self):
        with self.assertRaises(ValueError):c.make_report([])
    def test_no_emulator_in_retention(self):
        text=(c.ROOT/c.SELF).read_text();self.assertNotIn('native.run(',text)
        self.assertNotIn('layer.run(',text);self.assertNotIn('release_ready=True',text)
    def test_original_conclusions_retained(self):
        self.assertEqual([p[6] for p in c.PINS],['failure','success','failure','success'])
        self.assertEqual(c.PINS[0][4],677365);self.assertEqual(c.PINS[1][4],955191)

if __name__=='__main__':unittest.main()
