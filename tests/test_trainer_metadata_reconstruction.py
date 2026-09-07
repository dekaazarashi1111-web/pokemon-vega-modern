"""metadata復元は意味の近似ではなく歴史的byte identityで閉じる。"""
import hashlib
import json
import io
import zipfile
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import types

from scripts.reconstruct_trainer_metadata import AUTHORING, PACKAGE, REPORT, _undo_ref1012, recover_metadata


class TrainerMetadataReconstructionTests(unittest.TestCase):
    def _recover(self, source, expected, *, available=None, size=None, digest=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / REPORT
            path.parent.mkdir(parents=True)
            path.write_bytes(source)
            entry = {'path': 'VEGA_TRAINER_CHANGEKIT_TASK02_TOHOKU_EARLY/KIT_MANIFEST.json',
                     'size': len(expected) if size is None else size,
                     'sha256': hashlib.sha256(expected).hexdigest() if digest is None else digest}
            return recover_metadata(root, [entry], available or {})

    def test_nested_validator_snapshot_preserves_received_key_order(self):
        original = {'task': 'TASK02', 'baseline': 'fixed', 'notes': '原本'}
        expected = (json.dumps(original, ensure_ascii=False, indent=2) + '\n').encode()
        report = json.dumps({'validators': {'task02': {'manifest': original}}}, sort_keys=True).encode()
        template = json.dumps({'task': 'TASK05', 'baseline': 'fixed', 'notes': '別の入力'}).encode()
        available = {'VEGA_TRAINER_CHANGEKIT_TASK05_LEAGUE_POSTGAME/KIT_MANIFEST.json': template}
        result = self._recover(report, expected, available=available)
        self.assertEqual(list(result.values()), [expected])
        self.assertEqual(len(available), 1)

    def test_wrong_size_or_hash_is_never_accepted(self):
        expected = b'{\n  "task": "TASK02"\n}\n'
        report = b'{"validators":{"task02":{"manifest":{"task":"TASK02"}}}}'
        self.assertEqual(self._recover(report, expected, size=len(expected) + 1), {})
        self.assertEqual(self._recover(report, expected, digest='0' * 64), {})

    def test_metadata_value_drift_is_not_normalized_away(self):
        expected = b'{\n  "task": "TASK02"\n}\n'
        self.assertEqual(self._recover(b'{"manifest":{"task":"TASK06"}}', expected), {})

    def test_ref1012_inverse_changes_only_proven_field(self):
        source = b'encounter_key,battle_type,notes\nOTHER,SINGLE,keep\nENC_TOHOKU_REF_1012,DOUBLE,"quoted, note"\n'
        expected = source.replace(b'REF_1012,DOUBLE,', b'REF_1012,UNKNOWN,')
        self.assertEqual(_undo_ref1012(source), expected)
        self.assertEqual(source.count(b'DOUBLE'), 1)

    def test_inverse_rejects_missing_duplicate_and_wrong_preimage(self):
        header = b'encounter_key,battle_type\n'
        row = b'ENC_TOHOKU_REF_1012,DOUBLE\n'
        for raw in (header, header + row + row, header + row.replace(b'DOUBLE', b'SINGLE')):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                _undo_ref1012(raw)

    def test_unrequested_metadata_and_missing_provenance_are_not_synthesized(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(recover_metadata(Path(temporary), [], {}), {})
            self.assertEqual(recover_metadata(Path(temporary), [{'path': 'TASK/KIT_MANIFEST.json',
                'size': 10, 'sha256': '0' * 64}], {}), {})

    def test_verified_package_reverses_correction_with_its_own_generators(self):
        source = b'encounter_key,battle_type\nENC_TOHOKU_REF_1012,DOUBLE\n'
        original = source.replace(b'DOUBLE', b'UNKNOWN')
        historical = (hashlib.sha256(original).hexdigest() + '\tdata\n').encode()
        build = "import pathlib,sys; p=pathlib.Path(sys.argv[2]); assert b'UNKNOWN' in (p/'source/v5/data/trainer_encounters.csv').read_bytes()\n"
        package = "import hashlib,pathlib,sys; p=pathlib.Path(sys.argv[2]); raw=(p/'source/v5/data/trainer_encounters.csv').read_bytes(); (p/'AUTHORING_MANIFEST_SHA256.tsv').write_text(hashlib.sha256(raw).hexdigest()+'\\tdata\\n')\n"
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            for name, raw in {
                'source/v5/data/trainer_encounters.csv': source,
                'tools/build_partitions.py': build.encode(),
                'tools/package_authoring_kit.py': package.encode(),
                'AUTHORING_MANIFEST_SHA256.tsv': b'corrected\tdata\n',
            }.items():
                archive.writestr(AUTHORING + '/' + name, raw)
        raw = buffer.getvalue()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / PACKAGE
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            report = {'schema_version': 1, 'status': 'PASS', 'original_inputs_mutated': False,
                      'correction': {'encounter_key': 'ENC_TOHOKU_REF_1012',
                                     'authoring_battle_type': {'before': 'UNKNOWN', 'after': 'DOUBLE'}},
                      'packages': {'authoring': {'path': PACKAGE, 'size': len(raw),
                                                'sha256': hashlib.sha256(raw).hexdigest()}}}
            report_path = root / REPORT
            report_path.parent.mkdir(parents=True)
            report_path.write_text(json.dumps(report))
            entry = {'path': AUTHORING + '/AUTHORING_MANIFEST_SHA256.tsv',
                     'size': len(historical), 'sha256': hashlib.sha256(historical).hexdigest()}
            self.assertEqual(recover_metadata(root, [entry], {}), {entry['path']: historical})
            self.assertEqual(path.read_bytes(), raw)
            report['packages']['authoring']['sha256'] = '0' * 64
            report_path.write_text(json.dumps(report))
            self.assertEqual(recover_metadata(root, [entry], {}), {})


    def test_transport_candidates_preserve_values_and_historical_bytes(self):
        original = b'\xef\xbb\xbf{\r\n  "task": "TASK02"\r\n}\r\n'
        received = b'{"task":"TASK02"}'
        entry = {'path': 'TASK/KIT_MANIFEST.json', 'size': len(original),
                 'sha256': hashlib.sha256(original).hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(recover_metadata(root, [entry], {},
                metadata_candidates=[received]), {entry['path']: original})
            self.assertEqual(recover_metadata(root, [entry], {},
                metadata_candidates=[received.replace(b'TASK02', b'TASK03')]), {})
            entry['sha256'] = '0' * 64
            self.assertEqual(recover_metadata(root, [entry], {},
                metadata_candidates=[received]), {})

    def test_tsv_transport_does_not_change_manifest_rows(self):
        original = b'\xef\xbb\xbf012345\tpath.csv\r\n'
        received = original.removeprefix(b'\xef\xbb\xbf').replace(b'\r\n', b'\n')
        entry = {'path': AUTHORING + '/AUTHORING_MANIFEST_SHA256.tsv',
                 'size': len(original), 'sha256': hashlib.sha256(original).hexdigest()}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(recover_metadata(root, [entry], {},
                metadata_candidates=[received]), {entry['path']: original})
            self.assertEqual(recover_metadata(root, [entry], {},
                metadata_candidates=[received.replace(b'012345', b'012346')]), {})

    def test_restore_scanner_does_not_discard_different_size_metadata(self):
        from scripts.prepare_trainer_unit_inputs import MANIFEST, restore_inputs, TrainerInputError

        # CSV復元はこのtestの責務ではない。metadata用の既存scannerを実行する。
        csv_module = types.ModuleType('scripts.reconstruct_trainer_csv_inputs')
        csv_module.reconstruct = lambda *args, **kwargs: {}
        source_module = types.ModuleType('scripts.invert_trainer_normalization')
        source_module.SOURCE_INPUTS = {}
        original = b'\xef\xbb\xbf{\r\n  "task": "TASK02"\r\n}\r\n'
        received = b'{"task":"TASK02"}'
        relative = 'VEGA_TRAINER_CHANGEKIT_TASK02_TOHOKU_EARLY/KIT_MANIFEST.json'
        entry = {'path': relative, 'size': len(original),
                 'sha256': hashlib.sha256(original).hexdigest()}
        for location in ('loose', 'nested_zip', 'wrong_value', 'unsafe_zip'):
            with self.subTest(location=location), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                manifest = root / MANIFEST
                manifest.parent.mkdir(parents=True)
                manifest.write_text(json.dumps({'schema_version': 1, 'inputs': [entry]}))
                if location == 'loose':
                    source = root / 'userfile' / relative
                    source.parent.mkdir(parents=True)
                    source.write_bytes(received)
                else:
                    buffer = io.BytesIO()
                    member = '../KIT_MANIFEST.json' if location == 'unsafe_zip' else relative
                    raw = received.replace(b'TASK02', b'TASK03') if location == 'wrong_value' else received
                    with zipfile.ZipFile(buffer, 'w') as inner:
                        inner.writestr(member, raw)
                    source = root / 'userfile/inputs.zip'
                    source.parent.mkdir(parents=True)
                    with zipfile.ZipFile(source, 'w') as archive:
                        archive.writestr('nested.zip', buffer.getvalue())
                before = source.read_bytes()
                with patch.dict('sys.modules', {
                    csv_module.__name__: csv_module, source_module.__name__: source_module,
                }):
                    if location in ('wrong_value', 'unsafe_zip'):
                        with self.assertRaises(TrainerInputError):
                            restore_inputs(root)
                        self.assertFalse((root / '.local/trainer-unit-inputs/integration_inputs').exists())
                    else:
                        result = restore_inputs(root)
                        self.assertEqual((result / relative).read_bytes(), original)
                        self.assertEqual(restore_inputs(root), result)
                self.assertEqual(source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
