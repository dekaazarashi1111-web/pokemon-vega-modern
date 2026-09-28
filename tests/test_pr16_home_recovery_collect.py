import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from pr16_home_recovery_collect import copy_immutable

class ImmutableCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.a=self.root/'source';self.b=self.root/'dest'
        self.a.write_bytes(b'fixed evidence');self.a.chmod(0o444)
    def test_first_copy(self):
        copy_immutable(self.a,self.b);self.assertEqual(self.a.read_bytes(),self.b.read_bytes())
    def test_repeated_readonly_copy_never_writes(self):
        copy_immutable(self.a,self.b);before=self.b.stat()
        with patch('pr16_home_recovery_collect.shutil.copy2',side_effect=AssertionError('no second write')):
            copy_immutable(self.a,self.b)
        self.assertEqual(before,self.b.stat())
    def test_different_target_preserved(self):
        self.b.write_bytes(b'other');self.b.chmod(0o444)
        with self.assertRaises(ValueError):copy_immutable(self.a,self.b)
        self.assertEqual(self.b.read_bytes(),b'other')
    def test_source_symlink_rejected(self):
        source=self.root/'link';source.symlink_to(self.a)
        with self.assertRaises(ValueError):copy_immutable(source,self.b)
        self.assertFalse(self.b.exists())
    def test_target_symlink_rejected(self):
        self.b.symlink_to(self.a)
        with self.assertRaises(ValueError):copy_immutable(self.a,self.b)
    def test_directory_target_rejected(self):
        self.b.mkdir()
        with self.assertRaises(ValueError):copy_immutable(self.a,self.b)
    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError):copy_immutable(self.root/'missing',self.b)

if __name__=='__main__':unittest.main()
