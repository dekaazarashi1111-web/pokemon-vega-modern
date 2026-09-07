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


class TrainerMetadataProvenanceDiagnostics(unittest.TestCase):
    """原本値は出力せず、復元元・生成経路の仮説を固定test名で区別する。"""
    @classmethod
    def setUpClass(cls):
        import ast
        import csv
        from pathlib import PurePosixPath
        import stat
        import subprocess
        import sys
        from scripts.reconstruct_trainer_metadata import AUTHORING, PACKAGE, REPORT, _snapshots, _undo_ref1012

        root = Path(__file__).resolve().parents[1]
        cls.facts = {}
        report = json.loads((root / REPORT).read_bytes())
        package = report['packages']['authoring']
        raw = (root / PACKAGE).read_bytes()
        assert package['path'] == PACKAGE
        assert (len(raw), hashlib.sha256(raw).hexdigest()) == (package['size'], package['sha256'])
        assert report['status'] == 'PASS' and report['original_inputs_mutated'] is False
        entries = json.loads((root / inputs.MANIFEST).read_bytes())['inputs']
        target = next(row for row in entries if row['path'] == AUTHORING + '/AUTHORING_MANIFEST_SHA256.tsv')
        def exact(data):
            return (len(data), hashlib.sha256(data).hexdigest()) == (target['size'], target['sha256'])
        with tempfile.TemporaryDirectory(prefix='trainer-provenance-') as temporary:
            work = Path(temporary)
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                assert sum(info.file_size for info in archive.infolist()) <= 256 * 1024 * 1024
                for info in archive.infolist():
                    path = PurePosixPath(info.filename)
                    assert not path.is_absolute() and '..' not in path.parts and '\\' not in info.filename
                    assert not stat.S_ISLNK(info.external_attr >> 16)
                archive.extractall(work)
            kits = [p.parent for p in work.rglob('AUTHORING_MANIFEST_SHA256.tsv')
                    if (p.parent / 'tools/build_partitions.py').is_file()]
            assert len(kits) == 1
            kit = kits[0]
            tsv = kit / 'AUTHORING_MANIFEST_SHA256.tsv'
            original_inventory = tsv.read_bytes()
            source = kit / 'source/v5/data/trainer_encounters.csv'
            corrected = source.read_bytes()
            inverse = _undo_ref1012(corrected)
            source.write_bytes(inverse)
            cls.facts['source_inverse_preserves_transport'] = (
                corrected.startswith(b'\xef\xbb\xbf') == inverse.startswith(b'\xef\xbb\xbf')
                and corrected.count(b'\r\n') == inverse.count(b'\r\n'))
            task05 = report['packages']['task05']
            task_raw = (root / task05['path']).read_bytes()
            assert (len(task_raw), hashlib.sha256(task_raw).hexdigest()) == (task05['size'], task05['sha256'])
            with zipfile.ZipFile(io.BytesIO(task_raw)) as archive:
                manifests = [archive.read(info) for info in archive.infolist()
                             if PurePosixPath(info.filename).name == 'KIT_MANIFEST.json']
            assert len(manifests) == 1
            template = json.loads(manifests[0])
            cls.facts['report_has_task_manifest_snapshots'] = any(
                set(snapshot) == set(template) for snapshot in _snapshots(report))
            cls.facts['package_has_task_manifest_snapshots'] = False
            for path in kit.rglob('*.json'):
                if path.stat().st_size <= 4 * 1024 * 1024:
                    for snapshot in _snapshots(json.loads(path.read_bytes())):
                        if set(snapshot) == set(template):
                            cls.facts['package_has_task_manifest_snapshots'] = True
            tools = []
            for path in (kit / 'tools').glob('*.py'):
                constants = {node.value for node in ast.walk(ast.parse(path.read_bytes()))
                             if isinstance(node, ast.Constant) and isinstance(node.value, str)}
                if '--authoring-kit' in constants and {'--task', '--task-id'} & constants:
                    tools.append((path, constants))
            cls.facts['task_creator_exists'] = bool(tools)
            for flag in ('task', 'task-id', 'output', 'output-dir', 'out', 'out-dir'):
                cls.facts['task_creator_uses_' + flag.replace('-', '_')] = any(
                    '--' + flag in constants for _, constants in tools)
            def run(name, *arguments):
                process = subprocess.run([sys.executable, '-B', str(kit / 'tools' / name),
                                          '--authoring-kit', str(kit), *arguments],
                                         cwd=work, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                         check=False, timeout=120)
                return process.returncode == 0
            cls.facts['inverse_partitions_succeed'] = run('build_partitions.py')
            cls.facts['inverse_packaging_succeeds'] = run('package_authoring_kit.py', '--output', str(work / 'original.zip'))
            cls.facts['inverse_generated_inventory_matches'] = exact(tsv.read_bytes())
            parsed = list(csv.reader(io.StringIO(original_inventory.decode('utf-8-sig')), delimiter='\t'))
            cls.facts['inventory_excludes_self'] = not any(
                field.strip('"').endswith('AUTHORING_MANIFEST_SHA256.tsv') for row in parsed[1:] for field in row)
            cls.facts['inventory_excludes_validation_outputs'] = not any(
                'validation' in field.lower() and field.lower().endswith('.json') for row in parsed[1:] for field in row)
            cls.facts['inventory_excludes_python_cache'] = not any(
                '__pycache__' in field or field.endswith('.pyc') for row in parsed[1:] for field in row)
        assert (root / PACKAGE).read_bytes() == raw


def _metadata_provenance_check(name):
    def test(self):
        self.assertTrue(self.facts[name])
    return test


for _diagnostic_name in (
    'source_inverse_preserves_transport', 'report_has_task_manifest_snapshots',
    'package_has_task_manifest_snapshots', 'task_creator_exists', 'task_creator_uses_task',
    'task_creator_uses_task_id', 'task_creator_uses_output', 'task_creator_uses_output_dir',
    'task_creator_uses_out', 'task_creator_uses_out_dir',
    'inverse_partitions_succeed', 'inverse_packaging_succeeds', 'inverse_generated_inventory_matches',
    'inventory_excludes_self', 'inventory_excludes_validation_outputs', 'inventory_excludes_python_cache',
):
    setattr(TrainerMetadataProvenanceDiagnostics, 'test_' + _diagnostic_name,
            _metadata_provenance_check(_diagnostic_name))
