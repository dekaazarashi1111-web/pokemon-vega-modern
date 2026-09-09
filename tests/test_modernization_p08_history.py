"""Keep historical provenance strict while retaining the repaired Stage79 runner."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

from tools import modernization_p08_historical_sources as history
from tools import modernization_p08_integration as p08

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('p08_bootstrap', ROOT / '.github/scripts/stage79_p08_bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class HistoricalSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in (history.SOURCE, history.ARCHIVE):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        self.row = {'path': history.SOURCE, 'size': history.HISTORICAL[0], 'sha256': history.HISTORICAL[1]}
        self.tracked = {history.SOURCE, history.ARCHIVE}

    def audit(self, binding='P02_STAGE64_MGBA'):
        return p08.audit_declared_source_rows(self.root, [self.row], self.tracked, binding=binding)[0]

    def test_exact_archive_and_current_successor_are_both_verified(self):
        for binding in sorted(history.BINDINGS):
            row = self.audit(binding)
            self.assertEqual(row['sha256'], history.HISTORICAL[1])
            resolution = row['source_resolution']
            self.assertEqual(resolution['current_source']['sha256'], history.CURRENT[1])
            self.assertEqual(resolution['git_blob'], history.GIT_BLOB)
            self.assertEqual(resolution['commit'], history.COMMIT)
            self.assertFalse(resolution['historical_result_relabelled_as_current'])

    def test_tampered_current_source_is_rejected(self):
        path = self.root / history.SOURCE
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_tampered_archive_is_rejected(self):
        path = self.root / history.ARCHIVE
        raw = bytearray(path.read_bytes()); raw[0] ^= 1; path.write_bytes(raw)
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_current_bytes_cannot_replace_old_archive(self):
        (self.root / history.ARCHIVE).write_bytes((self.root / history.SOURCE).read_bytes())
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_reverting_current_runner_is_not_an_approved_successor(self):
        (self.root / history.SOURCE).write_bytes((self.root / history.ARCHIVE).read_bytes())
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_changed_historical_declaration_is_rejected(self):
        self.row['sha256'] = history.CURRENT[1]
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_unrelated_binding_cannot_use_historical_fallback(self):
        with self.assertRaises(p08.ModernizationP08Error): self.audit('UNAPPROVED')

    def test_archive_must_be_tracked(self):
        self.tracked.remove(history.ARCHIVE)
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_current_must_be_tracked(self):
        self.tracked.remove(history.SOURCE)
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_missing_archive_is_rejected(self):
        (self.root / history.ARCHIVE).unlink()
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_symlink_archive_is_rejected(self):
        path = self.root / history.ARCHIVE
        target = self.root / 'archive.c'; path.rename(target); path.symlink_to(target)
        with self.assertRaises(p08.ModernizationP08Error): self.audit()

    def test_symlink_parent_is_rejected(self):
        path = (self.root / history.ARCHIVE).parent
        target = self.root / 'moved'; path.rename(target); path.symlink_to(target, target_is_directory=True)
        with self.assertRaises(p08.ModernizationP08Error): self.audit()


class HistoricalArtifactCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'; self.source.mkdir()
        self.dest = self.root / 'destination'; self.dest.mkdir()
        self.relative = 'build/stages/historical.bin'
        self.raw = b'pinned historical bytes'
        path = self.source / self.relative; path.parent.mkdir(parents=True); path.write_bytes(self.raw)
        self.contracts = {self.relative: (len(self.raw), hashlib.sha256(self.raw).hexdigest(), None)}

    def run_copy(self, tracked=()):
        bootstrap.copy_artifacts(self.source, self.dest, set(tracked), self.contracts)

    def test_only_exact_allowlisted_bytes_are_copied(self):
        (self.source / 'extra').write_bytes(b'not allowed')
        self.run_copy()
        self.assertEqual((self.dest / self.relative).read_bytes(), self.raw)
        self.assertFalse((self.dest / 'extra').exists())

    def test_exact_tracked_destination_is_never_written(self):
        self.run_copy(); target = self.dest / self.relative
        before = target.stat().st_mtime_ns
        self.run_copy([self.relative])
        self.assertEqual(target.stat().st_mtime_ns, before)

    def test_missing_tracked_destination_is_rejected(self):
        with self.assertRaises(RuntimeError): self.run_copy([self.relative])
        self.assertFalse((self.dest / self.relative).exists())

    def test_conflicting_destination_is_preserved(self):
        self.run_copy(); target = self.dest / self.relative; target.write_bytes(b'current')
        with self.assertRaises(p08.ModernizationP08Error): self.run_copy()
        self.assertEqual(target.read_bytes(), b'current')

    def test_tampered_source_fails_before_any_copy(self):
        extra = 'build/stages/other.bin'
        (self.source / extra).write_bytes(b'wrong')
        self.contracts[extra] = self.contracts[self.relative]
        with self.assertRaises(p08.ModernizationP08Error): self.run_copy()
        self.assertFalse((self.dest / self.relative).exists())

    def test_crc_mismatch_is_rejected(self):
        self.contracts[self.relative] = (*self.contracts[self.relative][:2], '00000000')
        with self.assertRaises(RuntimeError): self.run_copy()

    def test_destination_symlink_is_rejected(self):
        path = self.dest / self.relative; path.parent.mkdir(parents=True)
        path.symlink_to(self.source / self.relative)
        with self.assertRaises(RuntimeError): self.run_copy()

    def test_destination_symlink_parent_is_rejected(self):
        (self.dest / 'build').symlink_to(self.source / 'build', target_is_directory=True)
        with self.assertRaises(bootstrap.environment.PrivateEnvironmentError): self.run_copy()

    def test_source_symlink_is_rejected(self):
        target = self.source / self.relative; target.unlink()
        other = self.root / 'original'; other.write_bytes(self.raw); target.symlink_to(other)
        with self.assertRaises(p08.ModernizationP08Error): self.run_copy()

    def test_unsafe_contract_path_is_rejected(self):
        self.contracts['../escape'] = self.contracts.pop(self.relative)
        with self.assertRaises(p08.ModernizationP08Error): self.run_copy()


if __name__ == '__main__':
    unittest.main()
