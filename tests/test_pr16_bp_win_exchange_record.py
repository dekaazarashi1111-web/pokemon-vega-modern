"""記録の安全境界だけ。ROM生成/native processや受入caseを再実行しない。"""
import io
from pathlib import Path
import sys
import unittest
import warnings
import zipfile
sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'scripts')]
import pr16_bp_win_exchange_record as r

class RecordTests(unittest.TestCase):
    def archive(self, entries):
        buf=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(buf,'w') as z:
                for name,raw in entries:z.writestr(name,raw)
        return buf.getvalue()
    def test_valid_process_boundaries(self):
        for code in (0,1):r.checked_process(dict(returncode=code,timed_out=False,spawn_error=None),code)
    def test_process_type_timeout_spawn_fail_closed(self):
        for key,value in [('returncode',True),('returncode',-1),('timed_out',1),('timed_out',True),('spawn_error','failure')]:
            p=dict(returncode=1,timed_out=False,spawn_error=None);p[key]=value
            with self.subTest(key=key,value=value), self.assertRaises(ValueError):r.checked_process(p,1)
    def test_valid_zip_is_read_only(self):
        raw=self.archive([('one.txt',b'one'),('sub/two.json',b'{}')]);before=r.ident(raw)
        self.assertEqual(r.safe_zip(raw),{'one.txt':b'one','sub/two.json':b'{}'})
        self.assertEqual(r.ident(raw),before)
    def test_duplicate_members_rejected(self):
        with self.assertRaises(ValueError):r.safe_zip(self.archive([('x',b'a'),('x',b'b')]))
    def test_path_traversal_absolute_and_backslash_rejected(self):
        for name in ('../escape','/absolute','a/../../b','a\\b'):
            with self.subTest(name=name), self.assertRaises(ValueError):r.safe_zip(self.archive([(name,b'x')]))
    def test_symlink_and_directory_rejected(self):
        link=zipfile.ZipInfo('link');link.create_system=3;link.external_attr=0o120777<<16
        for name in (link,'dir/'):
            with self.assertRaises(ValueError):r.safe_zip(self.archive([(name,b'x')]))
    def test_unbound_or_tampered_archive_rejected(self):
        raw=self.archive([('x',b'bounded')])
        for bound in r.BOUNDS:
            with self.assertRaises(ValueError):r.bundle(raw,bound)
    def test_record_cannot_write_formal_checkpoint_or_engine_sources(self):
        self.assertEqual(len(r.WRITES),len(set(r.WRITES)))
        self.assertNotIn(r.resume.CHECKPOINT,r.WRITES)
        self.assertNotIn(r.native.SOURCE,r.WRITES)
        self.assertNotIn('config/active_play_baseline.json',r.WRITES)
        self.assertEqual(len(r.BOUNDS),3)
        self.assertEqual([x['conclusion'] for x in r.BOUNDS],['failure','failure','success'])
        text=(r.ROOT/r.native.SOURCE).read_text()
        self.assertIn('memcmp(expected,actual,sizeof(actual))',text)
        self.assertIn('if(!w.commit && wx_commit_returned(c))',text)

if __name__=='__main__':unittest.main()
