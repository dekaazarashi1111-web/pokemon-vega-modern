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


# focused-unitの既存入口で、合成資材だけの恒久metadata回帰も実行する。
# 一時診断の仮説assertは残さず、原本identityテストは変更しない。
from tests.test_trainer_metadata_reconstruction import (  # noqa: E402,F401
    TrainerMetadataReconstructionTests,
    TrainerMetadataTransportRegressionTests,
    TrainerMetadataNestedOrderRegressionTests,
    TrainerMetadataGenerationRegression,
)


class TrainerMetadataRecoveryRouteDiagnostics(unittest.TestCase):
    """一時診断。検証済み資材の値・path・本文は出力しない。"""
    @classmethod
    def setUpClass(cls):
        import csv
        from pathlib import PurePosixPath
        import re
        import shutil
        import stat
        import subprocess
        import sys
        from scripts.reconstruct_trainer_metadata import (
            AUTHORING, PACKAGE, REPORT, MAX_TEXT, _inventory_from_files,
            _snapshots, _undo_ref1012,
        )
        from scripts.invert_trainer_normalization import SOURCE_INPUTS

        root = Path(__file__).resolve().parents[1]
        cls.facts = {}
        report_raw = (root / REPORT).read_bytes()
        report = json.loads(report_raw)
        cls.facts['report_within_reader_limit'] = len(report_raw) <= MAX_TEXT
        package = report['packages']['authoring']
        raw = (root / PACKAGE).read_bytes()
        assert package['path'] == PACKAGE
        assert (len(raw), hashlib.sha256(raw).hexdigest()) == (package['size'], package['sha256'])
        assert report['status'] == 'PASS' and report['original_inputs_mutated'] is False
        entries = json.loads((root / inputs.MANIFEST).read_bytes())['inputs']
        targets = {row['path']: row for row in entries if Path(row['path']).name in
                   {'KIT_MANIFEST.json', 'AUTHORING_MANIFEST_SHA256.tsv'}}
        def exact(name, data):
            row = targets[name]
            return (len(data), hashlib.sha256(data).hexdigest()) == (row['size'], row['sha256'])
        tsv_name = AUTHORING + '/AUTHORING_MANIFEST_SHA256.tsv'
        with tempfile.TemporaryDirectory(prefix='trainer-route-') as temporary:
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
            before = {p.relative_to(kit).as_posix(): p.read_bytes() for p in kit.rglob('*') if p.is_file()}
            inventory = before['AUTHORING_MANIFEST_SHA256.tsv']
            parsed = list(csv.reader(io.StringIO(inventory.decode('utf-8-sig')), delimiter='\t'))
            header = [re.sub('[^a-z0-9]', '', field.lower()) for field in parsed[0]]
            def col(names):
                indexes = [i for i, field in enumerate(header) if field in names]
                return indexes[0] if len(indexes) == 1 else None
            pi = col({'path', 'file', 'filepath', 'relativepath', 'relpath'})
            si = col({'size', 'bytes', 'sizebytes', 'filesize'})
            hi = col({'sha256', 'sha256sum', 'sha256hash', 'sha256hex'})
            cls.facts['inventory_has_path_digest_header'] = pi is not None and hi is not None
            cls.facts['inventory_has_size_column'] = si is not None
            cls.facts['inventory_paths_are_kit_relative'] = pi is not None and all(row[pi] in before for row in parsed[1:])
            cls.facts['inventory_records_match_verified_members'] = (
                cls.facts['inventory_paths_are_kit_relative'] and hi is not None and all(
                hashlib.sha256(before[row[pi]]).hexdigest() == row[hi] for row in parsed[1:]))
            cls.facts['inventory_full_refresh_roundtrips'] = _inventory_from_files(inventory, kit) == inventory
            corrected = before['source/v5/data/trainer_encounters.csv']
            cls.facts['full_source_pin_is_corrected_csv'] = (
                len(corrected), hashlib.sha256(corrected).hexdigest()) == SOURCE_INPUTS['trainer_encounters.csv']
            cls.facts['full_source_pin_is_inverse_csv'] = any(
                (len(candidate), hashlib.sha256(candidate).hexdigest()) == SOURCE_INPUTS['trainer_encounters.csv']
                for candidate in (_undo_ref1012(corrected, newline=n, bom=b)
                                  for n in ('\n', '\r\n') for b in (False, True)))
            cls.facts['sparse_inventory_inverse_matches_original'] = False
            cls.facts['inverse_before_partition_inventory_matches_original'] = False
            for newline in ('\n', '\r\n'):
                for bom in (False, True):
                    candidate = work / ('trial-' + str(bom) + '-' + str(len(newline)))
                    shutil.copytree(kit, candidate)
                    (candidate / 'source/v5/data/trainer_encounters.csv').write_bytes(
                        _undo_ref1012(corrected, newline=newline, bom=bom))
                    for stage in ('before', 'partition'):
                        if stage == 'partition':
                            completed = subprocess.run([sys.executable, '-B', str(candidate/'tools/build_partitions.py'),
                                '--authoring-kit', str(candidate)], cwd=work, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, check=False, timeout=120)
                            if completed.returncode:
                                continue
                        if not cls.facts['inventory_paths_are_kit_relative'] or hi is None:
                            continue
                        output = inventory.removeprefix(b'\xef\xbb\xbf').splitlines(keepends=True)
                        valid = True
                        for index, fields in enumerate(parsed[1:], 1):
                            name = fields[pi]
                            old, new = before[name], (candidate/name).read_bytes()
                            if old == new:
                                continue
                            if hashlib.sha256(old).hexdigest() != fields[hi]:
                                valid = False
                                break
                            line = output[index]
                            cells = line.rstrip(b'\r\n').split(b'\t')
                            replacements = {hi: hashlib.sha256(new).hexdigest()}
                            if si is not None:
                                replacements[si] = str(len(new))
                            for column, value in replacements.items():
                                quoted = cells[column].startswith(b'"') and cells[column].endswith(b'"')
                                cells[column] = ('"'+value+'"' if quoted else value).encode()
                            output[index] = b'\t'.join(cells) + line[len(line.rstrip(b'\r\n')):]
                        payload = (b'\xef\xbb\xbf' if inventory.startswith(b'\xef\xbb\xbf') else b'') + b''.join(output)
                        if valid and exact(tsv_name, payload):
                            cls.facts['sparse_inventory_inverse_matches_original'] = True
                            if stage == 'before':
                                cls.facts['inverse_before_partition_inventory_matches_original'] = True

            task_raw = (root / report['packages']['task05']['path']).read_bytes()
            identity = report['packages']['task05']
            assert (len(task_raw), hashlib.sha256(task_raw).hexdigest()) == (identity['size'], identity['sha256'])
            with zipfile.ZipFile(io.BytesIO(task_raw)) as archive:
                originals = [archive.read(p) for p in archive.namelist() if PurePosixPath(p).name == 'KIT_MANIFEST.json']
            assert len(originals) == 1
            template = json.loads(originals[0])
            snapshots = []
            for name, payload in before.items():
                if name.endswith('.json'):
                    snapshots.extend(value for value in _snapshots(json.loads(payload)) if set(value) == set(template))
            cls.facts['manifest_snapshot_has_task05_exact_values'] = any(value == template for value in snapshots)
            for label in ('TASK01', 'TASK02', 'TASK03', 'TASK04', 'TASK06'):
                cls.facts['manifest_snapshot_contains_' + label] = any(
                    label in json.dumps(value) for value in snapshots)
            cls.facts['manifest_snapshot_has_placeholder_values'] = any(
                item in (None, '', 'TODO') for value in snapshots for item in value.values())

            probe = '''import argparse,json,runpy,sys
class Captured(BaseException): pass
def capture(parser,*args,**kwargs):
 print(json.dumps([{'dest':a.dest,'options':a.option_strings,'required':a.required,'choices':list(a.choices) if a.choices is not None else None} for a in parser._actions]))
 raise Captured
argparse.ArgumentParser.parse_args=capture
argparse.ArgumentParser.parse_known_args=capture
p=sys.argv[1]
sys.path.insert(0,str(__import__('pathlib').Path(p).parent))
sys.argv=[p]
try: runpy.run_path(p,run_name='__main__')
except Captured: pass
'''
            declarations = []
            for script in (kit/'tools').glob('*.py'):
                text = script.read_text(encoding='utf-8-sig')
                if not ('KIT_MANIFEST' in text or any(word in script.stem.lower() for word in ('create', 'init', 'make', 'new', 'scaffold'))):
                    continue
                proc = subprocess.run([sys.executable, '-B', '-c', probe, str(script)], cwd=kit,
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=30)
                if proc.returncode or len(proc.stdout) > MAX_TEXT:
                    continue
                try:
                    actions = json.loads(proc.stdout)
                except ValueError:
                    continue
                if isinstance(actions, list):
                    declarations.append(actions)
            for label in ('task', 'task_id', 'task_name', 'task_number', 'partition', 'output', 'out_dir', 'output_dir'):
                cls.facts['declared_creator_argument_' + label] = any(
                    action['dest'] == label for actions in declarations for action in actions)
            cls.facts['creator_has_positional_task_argument'] = any(
                not action['options'] and 'task' in action['dest'] for actions in declarations for action in actions)

            # 復元済みの小さいtextだけをexact identityで読む。ROM/save/log/artifactは対象外。
            wanted = {(row['size'], row['sha256']): name for name, row in targets.items()}
            recovered = set()
            for role in ('reports/generated', 'generated', 'vendor', 'build/validated_inputs'):
                base = root / role
                if not base.is_dir():
                    continue
                for path in base.rglob('*'):
                    if (path.suffix.lower() not in {'.json', '.tsv', '.txt', '.md', '.bak'}
                            or not path.is_file() or any(p.is_symlink() for p in (path, *path.parents))
                            or path.stat().st_size not in {key[0] for key in wanted}):
                        continue
                    data = path.read_bytes()
                    identity = (len(data), hashlib.sha256(data).hexdigest())
                    if identity in wanted:
                        recovered.add(wanted[identity])
            cls.facts['missing_original_metadata_found_in_other_restored_text'] = any(
                name in recovered for name in targets if 'TASK05' not in name)
        assert (root / PACKAGE).read_bytes() == raw


def _trainer_route_check(name):
    def test(self):
        self.assertTrue(self.facts[name])
    return test


for _route in (
    'report_within_reader_limit', 'inventory_has_path_digest_header', 'inventory_has_size_column',
    'inventory_paths_are_kit_relative', 'inventory_records_match_verified_members',
    'inventory_full_refresh_roundtrips', 'full_source_pin_is_corrected_csv', 'full_source_pin_is_inverse_csv',
    'sparse_inventory_inverse_matches_original', 'inverse_before_partition_inventory_matches_original',
    'manifest_snapshot_has_task05_exact_values', 'manifest_snapshot_has_placeholder_values',
    'manifest_snapshot_contains_TASK01', 'manifest_snapshot_contains_TASK02',
    'manifest_snapshot_contains_TASK03', 'manifest_snapshot_contains_TASK04', 'manifest_snapshot_contains_TASK06',
    'declared_creator_argument_task', 'declared_creator_argument_task_id', 'declared_creator_argument_task_name',
    'declared_creator_argument_task_number', 'declared_creator_argument_partition', 'declared_creator_argument_output',
    'declared_creator_argument_out_dir', 'declared_creator_argument_output_dir', 'creator_has_positional_task_argument',
    'missing_original_metadata_found_in_other_restored_text',
):
    setattr(TrainerMetadataRecoveryRouteDiagnostics, 'test_' + _route, _trainer_route_check(_route))
