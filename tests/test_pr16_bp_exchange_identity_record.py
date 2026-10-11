"""原本ZIPの境界と保存済み照合。network/emulatorは使用しない。"""
import io
from pathlib import Path
import sys
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_bp_exchange_identity_record as p

class RecordTests(unittest.TestCase):
    def archive(self, entries):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            for name,data in entries:z.writestr(name,data)
        return out.getvalue()
    def test_safe_text_archive(self):
        self.assertEqual(p.unpack(self.archive([('native/a.json',b'{}')])) ,{'native/a.json':b'{}'})
    def test_path_escape_rejected(self):
        for name in ('../escape.txt','/tmp/escape.txt','native/../../escape.txt','native\\escape.txt'):
            with self.subTest(name=name),self.assertRaises(ValueError):p.unpack(self.archive([(name,b'{}')]))
    def test_duplicate_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            raw=self.archive([('a.json',b'{}'),('a.json',b'{}')])
        with self.assertRaises(ValueError):p.unpack(raw)
    def test_text_binary_rejected(self):
        for raw in (b'a\0b',b'\xff'):
            with self.assertRaises(ValueError):p.unpack(self.archive([('a.txt',raw)]))
    def test_receipt_head_and_members_fail_closed(self):
        root='pr16-bp-exchange-identity/'
        with self.assertRaises(ValueError):p.verify_members({root+'receipt.json':p.stable(dict(tested_head='0'*40,status=p.native.STATUS))})
        receipt=dict(tested_head=p.TESTED,status=p.native.STATUS,members={'a.txt':p.ident(b'original')})
        with self.assertRaises(ValueError):p.verify_members({root+'receipt.json':p.stable(receipt),root+'a.txt':b'changed'})
    def test_task_is_diagnostic_and_push_nonforce(self):
        text=(p.ROOT/p.SELF).read_text()
        self.assertNotIn("git('push','--force",text)
        self.assertIn("oldrow=resume.load(ROOT,'content/modernization/pr16_bp_win_exchange_evidence/native-result.json')",text)
        self.assertIn("current()==head,'concurrent push HEAD'",text)
        self.assertIn('native_bp_earning_accepted=False',text)

if __name__=='__main__':unittest.main()
