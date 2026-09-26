"""nativeを一度も起動しない公開写像の負の試験。"""
import json
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_research_lifecycle_record as r

class RecordTests(unittest.TestCase):
    def test_lossless_trailing_spaces(self):
        original=b'error\n      | \n  x  \n'
        name,raw=r.public_member('previous-compile.stderr.txt',original)
        self.assertEqual(name,'previous-compile.stderr.json')
        self.assertEqual(r.decode_public(raw),original)
        self.assertTrue(all(line==line.rstrip() for line in raw.splitlines()))
    def test_native_original_unchanged(self):
        original=b'{"status":"PASS"}\n'
        self.assertEqual(r.public_member('new-zero.stdout.txt',original),('new-zero.stdout.txt',original))
    def test_traversal_rejected(self):
        for path in ('../a.txt','/a.txt','folder/a.txt','a\\b.txt'):
            with self.subTest(path=path),self.assertRaises(ValueError):r.public_member(path,b'')
    def test_binary_rejected(self):
        with self.assertRaises(ValueError):r.public_member('sample.txt',b'\0')
    def test_non_utf8_rejected(self):
        with self.assertRaises(UnicodeDecodeError):r.public_member('sample.txt',b'\xff')
    def test_changed_text_rejected(self):
        _,raw=r.public_member('previous-compile.stderr.txt',b'original \n');v=json.loads(raw);v['text']='original\n'
        with self.assertRaises(ValueError):r.decode_public(json.dumps(v))
    def test_duplicate_field_rejected(self):
        _,raw=r.public_member('previous-compile.stderr.txt',b'x')
        raw=raw.replace(b'"schema_version": 1',b'"schema_version": 1, "schema_version": 1')
        with self.assertRaises(ValueError):r.decode_public(raw)
    def test_schema_bool_and_extra_rejected(self):
        _,raw=r.public_member('previous-compile.stderr.txt',b'x')
        for change in ({'schema_version':True},{'extra':1}):
            v=json.loads(raw);v.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):r.decode_public(json.dumps(v))

if __name__=='__main__':unittest.main()
