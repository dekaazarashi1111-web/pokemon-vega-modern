import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location('snapshot', Path(__file__).resolve().parents[1] / 'scripts/pr16_restore_cfru_snapshot.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'archived'
        self.source.mkdir()
        M.git(self.source, 'init', '--template=')
        p = self.source / 'src/end_battle.c'
        p.parent.mkdir()
        p.write_bytes(b'void EndOfBattleThings(void) {}\n')
        M.git(self.source, 'add', '.')
        M.git(self.source, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'fixture')
        commit = M.git(self.source, 'rev-parse', 'HEAD').decode().strip()
        self.lock = dict(name='cfru', path='vendor/upstream/CFRU-JP', configured_commit=commit,
                         actual_commit=commit, resolved_commit=commit, configured_commit_verified=True)
        p.write_bytes(b'dirty archived worktree must not be audited\n')
        (self.source / 'generated.c').write_bytes(b'not a pinned source\n')
        (self.source / '.git/objects/info').mkdir(exist_ok=True)
        self.archive = self.root / 'state.zip'
        self.destination = self.root / 'clean'
        self.pack()

    def pack(self, extra=None):
        with zipfile.ZipFile(self.archive, 'w') as z:
            for p in self.source.rglob('*'):
                if p.is_file():
                    z.write(p, M.PREFIX + p.relative_to(self.source).as_posix())
            if extra:
                z.writestr(*extra)
            z.writestr('inputs/private/not-extracted.gba', b'fixture-not-a-rom')
        data = self.archive.read_bytes()
        self.bound = dict(name='state.zip', size=len(data), sha256=hashlib.sha256(data).hexdigest())

    def restore(self):
        return M.restore(self.archive, self.destination, self.bound, self.lock)

    def test_dirty_export_restores_exact_locked_bytes_without_mutating_archive(self):
        before = self.archive.read_bytes()
        result = self.restore()
        self.assertEqual((self.destination / 'src/end_battle.c').read_bytes(), b'void EndOfBattleThings(void) {}\n')
        self.assertFalse((self.destination / 'generated.c').exists())
        self.assertFalse((self.root / 'inputs').exists())
        self.assertEqual(self.archive.read_bytes(), before)
        self.assertEqual((self.source / 'src/end_battle.c').read_bytes(), b'dirty archived worktree must not be audited\n')
        self.assertTrue(result['clean_source_verified'])
        self.assertFalse(result['archived_git_config_used'])
        self.assertEqual(result['new_emulator_processes'], 0)

    def test_bad_hash_rejected_before_destination_created(self):
        self.bound['sha256'] = '0' * 64
        with self.assertRaises(M.SnapshotError): self.restore()
        self.assertFalse(self.destination.exists())

    def test_inconsistent_lock_rejected(self):
        self.lock['actual_commit'] = '0' * 40
        with self.assertRaises(M.SnapshotError): self.restore()
        self.assertFalse(self.destination.exists())

    def test_missing_commit_rejected(self):
        for key in ('configured_commit', 'actual_commit', 'resolved_commit'): self.lock[key] = '0' * 40
        with self.assertRaises(M.SnapshotError): self.restore()

    def test_existing_destination_not_overwritten(self):
        self.destination.mkdir()
        (self.destination / 'keep').write_text('keep')
        with self.assertRaises(M.SnapshotError): self.restore()
        self.assertEqual((self.destination / 'keep').read_text(), 'keep')

    def test_traversal_in_source_archive_rejected(self):
        self.pack((M.PREFIX + '../escape', b'bad'))
        with self.assertRaises(M.SnapshotError): self.restore()
        self.assertFalse(self.destination.exists())

    def test_archive_symlink_rejected(self):
        info = zipfile.ZipInfo(M.PREFIX + 'alias')
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        self.pack((info, b'/outside'))
        with self.assertRaises(M.SnapshotError): self.restore()

    def test_destination_ancestor_symlink_rejected(self):
        (self.root / 'alias').symlink_to(self.source, target_is_directory=True)
        self.destination = self.root / 'alias/new'
        with self.assertRaises(M.SnapshotError): self.restore()
        self.assertFalse((self.source / 'new').exists())

    def test_git_alternates_rejected(self):
        self.pack((M.PREFIX + '.git/objects/info/alternates', b'/outside'))
        with self.assertRaises(M.SnapshotError): self.restore()


if __name__ == '__main__':
    unittest.main()
