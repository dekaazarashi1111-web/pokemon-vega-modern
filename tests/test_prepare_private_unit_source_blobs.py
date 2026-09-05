import tempfile
from pathlib import Path
import unittest
from scripts import prepare_private_unit_source_blobs as edit


class SourceBlobPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'scripts/unit.py').write_text('before\n')
        self.row = {'path': 'scripts/unit.py', 'before_sha256': edit.sha(b'before\n'),
                    'after_sha256': edit.sha(b'after\n'), 'replacements': [{'old': 'before', 'new': 'after'}]}

    def plan(self, row=None):
        return {'schema_version': 1, 'task': edit.TASK, 'files': [row or self.row]}

    def test_exact_source_is_prepared_without_modifying_worktree(self):
        self.assertEqual(edit.prepare(self.root, self.plan()), [('scripts/unit.py', b'after\n')])
        self.assertEqual((self.root / 'scripts/unit.py').read_text(), 'before\n')

    def test_before_hash_mismatch_is_rejected(self):
        self.row['before_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'before'):
            edit.prepare(self.root, self.plan())

    def test_after_hash_mismatch_is_rejected(self):
        self.row['after_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'after'):
            edit.prepare(self.root, self.plan())

    def test_nonunique_edit_is_rejected(self):
        self.row['replacements'][0]['old'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'unique'):
            edit.prepare(self.root, self.plan())

    def test_disallowed_paths_and_parent_traversal_are_rejected(self):
        for name in ('main', '.github/workflows/ci.yml', 'scripts/../secret.py', '/scripts/unit.py', 'private.gba'):
            with self.subTest(path=name):
                self.row['path'] = name
                with self.assertRaisesRegex(ValueError, 'path'):
                    edit.prepare(self.root, self.plan())

    def test_symlink_is_rejected(self):
        path = self.root / 'scripts/unit.py'
        path.unlink()
        path.symlink_to(self.root / 'target')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            edit.prepare(self.root, self.plan())

    def test_duplicate_path_is_rejected(self):
        plan = self.plan()
        plan['files'].append(self.row)
        with self.assertRaisesRegex(ValueError, 'path'):
            edit.prepare(self.root, plan)

    def test_logs_only_allow_append(self):
        (self.root / 'design').mkdir()
        (self.root / 'design/run_log.md').write_text('before\n')
        row = {'path': 'design/run_log.md', 'before_sha256': edit.sha(b'before\n'),
               'after_sha256': edit.sha(b'before\n\nafter\n'), 'append': '\nafter\n'}
        self.assertEqual(edit.prepare(self.root, self.plan(row))[0][1], b'before\n\nafter\n')
        row['replacements'] = []
        with self.assertRaisesRegex(ValueError, 'append-only'):
            edit.prepare(self.root, self.plan(row))

    def test_secret_candidate_is_rejected(self):
        candidate = 'gh' + 'p_' + 'z' * 32
        self.row['replacements'][0]['new'] = candidate
        self.row['after_sha256'] = edit.sha((candidate + '\n').encode())
        with self.assertRaisesRegex(ValueError, 'secret'):
            edit.prepare(self.root, self.plan())

    def test_wrong_task_is_rejected(self):
        plan = self.plan()
        plan['task'] = 'another'
        with self.assertRaisesRegex(ValueError, 'task'):
            edit.prepare(self.root, plan)
