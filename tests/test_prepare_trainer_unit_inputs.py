import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts import prepare_trainer_unit_inputs as inputs


class TrainerInputRestorationTests(unittest.TestCase):
    def setup_source(self, root, raw=b'key,value\nfixture,1\n'):
        name = 'VEGA_TRAINER_CHANGEKIT_TASK06_KANTO/data/trainer_encounters.csv'
        manifest = root / inputs.MANIFEST
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'schema_version': 1, 'inputs': [
            {'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}]}))
        return name, raw

    def test_nested_zip_restores_exact_pinned_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            name, raw = self.setup_source(root)
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, 'w') as z:
                z.writestr('unpacked/' + name, raw)
            (root / 'userfile').mkdir()
            with zipfile.ZipFile(root / 'userfile/input.zip', 'w') as z:
                z.writestr('kit.zip', inner.getvalue())
            target = inputs.restore_inputs(root)
            self.assertEqual((target / name).read_bytes(), raw)
            self.assertEqual(inputs.restore_inputs(root), target)

    def test_wrong_hash_does_not_publish_partial_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            name, raw = self.setup_source(root)
            (root / 'userfile').mkdir()
            with zipfile.ZipFile(root / 'userfile/input.zip', 'w') as z:
                z.writestr(name, raw.replace(b'1', b'2'))
            with self.assertRaises(inputs.TrainerInputError):
                inputs.restore_inputs(root)
            self.assertFalse((root / inputs.DESTINATION).exists())

    def test_existing_user_data_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            name, raw = self.setup_source(root)
            target = root / inputs.DESTINATION / name
            target.parent.mkdir(parents=True)
            target.write_bytes(b'sentinel')
            with self.assertRaises(inputs.TrainerInputError):
                inputs.restore_inputs(root)
            self.assertEqual(target.read_bytes(), b'sentinel')

    def test_nested_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            name, raw = self.setup_source(root)
            (root / 'userfile').mkdir()
            with zipfile.ZipFile(root / 'userfile/input.zip', 'w') as z:
                z.writestr('../' + name, raw)
            with self.assertRaises(inputs.TrainerInputError):
                inputs.restore_inputs(root)
            self.assertFalse((root / inputs.DESTINATION).exists())
