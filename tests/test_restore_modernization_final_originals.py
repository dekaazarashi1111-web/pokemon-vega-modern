import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import restore_modernization_final_originals as m

class OriginalRecovery(unittest.TestCase):
    def test_create_and_idempotent_exact_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'original.zip';raw=b'original'
            self.assertTrue(m.install(p,raw,m.record.identity(raw)))
            self.assertFalse(m.install(p,raw,m.record.identity(raw)))
            self.assertEqual(p.read_bytes(),raw)
    def test_changed_original_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'original.zip';p.write_bytes(b'original')
            with self.assertRaises(ValueError):m.install(p,b'changed')
            self.assertEqual(p.read_bytes(),b'original')
    def test_wrong_hash_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'original.zip'
            with self.assertRaises(ValueError):m.install(p,b'changed',m.record.identity(b'original'))
            self.assertFalse(p.exists())
    def test_file_and_parent_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'real').mkdir();(root/'link').symlink_to(root/'real',target_is_directory=True)
            with self.assertRaises(ValueError):m.install(root/'link'/'x',b'x')
            (root/'link-file').symlink_to(root/'real'/'x')
            with self.assertRaises(ValueError):m.install(root/'link-file',b'x')
    def test_success_not_reported_without_full_original_validator(self):
        with tempfile.TemporaryDirectory() as td,patch.object(m.record,'ARTIFACTS',{}),patch.object(m.record,'build',side_effect=ValueError('native original failed')):
            with self.assertRaisesRegex(ValueError,'native original failed'):m.restore(Path(td),lambda endpoint:b'{}')
    def test_subprocess_has_timeout_and_does_not_embed_token(self):
        with patch.object(m.subprocess,'run') as run:
            run.return_value.stdout=b'{}';self.assertEqual(m.fetch('actions/runs/1'),b'{}')
            args,kwargs=run.call_args
            self.assertEqual(args[0][0:2],['gh','api']);self.assertTrue(kwargs['check']);self.assertEqual(kwargs['timeout'],180)

if __name__=='__main__':unittest.main()
