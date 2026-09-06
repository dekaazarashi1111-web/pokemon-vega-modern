import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts.inspect_private_unit_remaining import collect_trainer_context, safe_member, wanted_text


class RemainingFixtureDiagnosticTests(unittest.TestCase):
    def test_only_named_text_inputs_are_selected(self):
        self.assertTrue(wanted_text('TRAINER_KIT/KIT_MANIFEST.json'))
        self.assertTrue(wanted_text('TRAINER_KIT/source/v5/data/trainer_encounters.csv'))
        for name in ('TRAINER_KIT/source.gba', 'TRAINER_KIT/save.srm', 'TRAINER_KIT/key.pem', '../KIT_MANIFEST.json'):
            self.assertFalse(wanted_text(name))

    def test_path_traversal_is_rejected(self):
        for name in ('/KIT_MANIFEST.json', '../KIT_MANIFEST.json', 'a/../../b', 'a\\b', ''):
            self.assertFalse(safe_member(name))

    def test_private_text_context_is_hash_bound_and_never_exports_rom(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            kit = root / 'userfile/TRAINER_KIT'
            kit.mkdir(parents=True)
            (kit / 'KIT_MANIFEST.json').write_text('{"schema_version":1}\n')
            (kit / 'source.gba').write_bytes(b'not a ROM')
            output = root / 'build/context.zip'
            result = collect_trainer_context(root, output)
            self.assertEqual(result['file_count'], 1)
            with zipfile.ZipFile(output) as archive:
                manifest = json.loads(archive.read('CONTEXT_MANIFEST.json'))
                self.assertEqual(len(archive.namelist()), 2)
                row = manifest['files'][0]
                raw = archive.read(row['path'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
                self.assertEqual(len(raw), row['size'])
