"""既存host/nativeを再実行せず、完了証拠の拒否境界だけを検証する。"""
import copy
import io
import json
import os
from pathlib import Path
import unittest
import zipfile
from scripts import pr16_learnset_runtime_record as r


class RecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = Path(os.environ.get('PR16_RUNTIME_PROOF_DIR', r.ROOT / r.EVIDENCE))
        cls.files = {name: (folder / name).read_bytes() for name in r.PROOF}

    def changed(self, key, value):
        files = copy.copy(self.files)
        v = json.loads(files['verification.json'])
        v[key] = value
        files['verification.json'] = r.encode(v)
        return files

    def test_exact_completed_evidence(self):
        self.assertEqual(r.validate(self.files)['native_probe_calls'], 3382)

    def test_source_head_rejected(self):
        with self.assertRaises(ValueError):
            r.validate(self.changed('source_head', '0' * 40))

    def test_gameplay_promotion_rejected(self):
        with self.assertRaises(ValueError):
            r.validate(self.changed('scope', 'GAMEPLAY_E2E'))

    def test_unaccepted_consumers_rejected(self):
        for key in ('initial_moves_connected', 'natural_level_up_connected', 'conditional_consumers_connected',
                    'physical_archive_supply_verified', 'issue19_complete', 'release_ready'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate(self.changed(key, True))

    def test_claimed_reexecution_rejected(self):
        with self.assertRaises(ValueError):
            r.validate(self.changed('new_arm_links', 1))

    def test_modified_member_rejected(self):
        files = copy.copy(self.files)
        files['native11.json'] += b' '
        with self.assertRaises(ValueError):
            r.validate(files)

    def test_missing_member_rejected(self):
        files = copy.copy(self.files)
        del files['native29.json']
        with self.assertRaises(ValueError):
            r.validate(files)

    def test_unexpected_zip_member_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            for name, raw in self.files.items():
                z.writestr(name, raw)
            z.writestr('../extra.json', '{}')
        with self.assertRaises(ValueError):
            r.unpack(buf.getvalue())

    def test_duplicate_zip_member_rejected(self):
        import warnings
        buf = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(buf, 'w') as z:
                for name, raw in self.files.items():
                    z.writestr(name, raw)
                z.writestr('receipt.json', self.files['receipt.json'])
        with self.assertRaises(ValueError):
            r.unpack(buf.getvalue())

    def test_inherited_compiles_not_zeroed(self):
        with self.assertRaises(ValueError):
            r.validate(self.changed('inherited_arm_compiles', 0))


if __name__ == '__main__':
    unittest.main()
