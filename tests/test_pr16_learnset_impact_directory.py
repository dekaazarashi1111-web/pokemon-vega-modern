"""既存unit証拠を残したproof directory初期化の限定修復。"""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_learnset_impact as m

class DirectoryTests(unittest.TestCase):
    def test_new_nested_directory(self):
        with tempfile.TemporaryDirectory() as td,patch.object(m,'PROOF',Path(td)/'work/proof'):
            m.prepare_proof()
            self.assertTrue(m.PROOF.is_dir())
    def test_preserve_existing_unit(self):
        with tempfile.TemporaryDirectory() as td,patch.object(m,'PROOF',Path(td)/'proof'):
            m.PROOF.mkdir();p=m.PROOF/'unit.txt';p.write_text('original evidence\n')
            m.prepare_proof();m.prepare_proof()
            self.assertEqual(p.read_text(),'original evidence\n')
    def test_file_collision_rejected(self):
        with tempfile.TemporaryDirectory() as td,patch.object(m,'PROOF',Path(td)/'proof'):
            m.PROOF.write_text('not a directory')
            with self.assertRaises(FileExistsError):m.prepare_proof()

if __name__=='__main__':unittest.main()
