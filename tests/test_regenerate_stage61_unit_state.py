from pathlib import Path
import tempfile
import unittest
from scripts import regenerate_stage61_unit_state as regen


class RegenerationBoundaryTests(unittest.TestCase):
    def test_writes_only_new_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / 'original.json'
            original.write_bytes(b'original sentinel')
            target = root / 'candidate'
            regen.write_candidate({'build/stages/state.json': b'new candidate'}, target)
            self.assertEqual((target / 'build/stages/state.json').read_bytes(), b'new candidate')
            self.assertEqual(original.read_bytes(), b'original sentinel')

    def test_existing_candidate_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'candidate'
            target.mkdir()
            sentinel = target / 'state.json'
            sentinel.write_bytes(b'existing')
            with self.assertRaises(ValueError):
                regen.write_candidate({'state.json': b'new'}, target)
            self.assertEqual(sentinel.read_bytes(), b'existing')

    def test_escape_is_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'candidate'
            for name in ('../escape', '/absolute', 'back\\slash'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    regen.write_candidate({'valid.json': b'valid', name: b'bad'}, target)
                self.assertFalse(target.exists())

    def test_symlink_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / 'real'
            real.mkdir()
            (root / 'link').symlink_to(real, target_is_directory=True)
            with self.assertRaises(ValueError):
                regen.write_candidate({'state.json': b'new'}, root / 'link/candidate')
            self.assertFalse((real / 'candidate').exists())
