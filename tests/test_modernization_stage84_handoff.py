import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import apply_modernization_stage84_patch as app


class HandoffProtectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = self.root/'stage83-to-stage84.bps'
        self.patch.write_bytes(b'invalid')
        self.source = self.root/'source.gba'; self.source.write_bytes(b'original')
        self.output = self.root/'new.gba'

    def test_existing_output_never_overwritten(self):
        self.output.write_bytes(b'preserve')
        with self.assertRaises(ValueError): app.apply(self.patch,self.source,self.output)
        self.assertEqual(self.output.read_bytes(),b'preserve')
        self.assertEqual(self.source.read_bytes(),b'original')

    def test_save_not_an_input_or_output(self):
        for source,output in ((self.root/'actual.srm',self.output),(self.source,self.root/'actual.sav')):
            with self.assertRaises(ValueError): app.apply(self.patch,source,output)
        self.assertFalse(self.output.exists())

    def test_wrong_patch_size_and_unknown_patch(self):
        for patch in (self.patch,self.root/'other.bps'):
            with self.assertRaises(ValueError): app.apply(patch,self.source,self.output)
        self.assertFalse(self.output.exists())

    def test_symlink_input_and_destination(self):
        link=self.root/'link.gba'; link.symlink_to(self.source)
        with self.assertRaises(ValueError): app.apply(self.patch,link,self.output)
        self.output.symlink_to(self.source)
        with self.assertRaises(ValueError): app.apply(self.patch,self.source,self.output)
        self.assertEqual(self.source.read_bytes(),b'original')

    def test_hardlinked_input_refused(self):
        alias=self.root/'alias.gba'; alias.hardlink_to(self.source)
        with self.assertRaises(ValueError): app.read_regular(self.source,8)

    def test_symlink_directory_and_parent_traversal_refused(self):
        alias=self.root/'alias';alias.symlink_to(self.root,target_is_directory=True)
        for path in (alias/'new.gba',self.root/'..'/'new.gba'):
            with self.assertRaises(ValueError): app.no_links(path)

    def test_known_identities_not_approved_release(self):
        self.assertEqual(len(app.PATCHES),4)
        self.assertEqual({r[3] for r in app.PATCHES.values()},{app.S80,app.S83,app.S84})
        self.assertNotEqual(app.S80,app.S84)


if __name__ == '__main__': unittest.main()
