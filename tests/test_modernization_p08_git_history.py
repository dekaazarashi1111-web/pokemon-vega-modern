"""Exercise real shallow Git clones; never bypass parent commit validation."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('p08_history_bootstrap', ROOT / '.github/scripts/stage79_p08_bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class HistoricalGitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.origin = self.root / 'origin'; self.origin.mkdir()
        self.clone = self.root / 'clone'
        self.git('init', cwd=self.origin)
        self.commits = []
        for index in range(5):
            (self.origin / 'fixture').write_text(str(index))
            self.git('add', 'fixture', cwd=self.origin)
            self.git('commit', '-m', str(index), cwd=self.origin)
            self.commits.append(self.git('rev-parse', 'HEAD', cwd=self.origin))
        self.git('clone', '--depth=1', self.origin.as_uri(), str(self.clone), cwd=self.root)
        first = patch.object(bootstrap.history, 'COMMIT', self.commits[-2])
        second = patch.object(bootstrap.stage_inputs, 'INPUT_COMMIT', self.commits[1])
        first.start(); second.start()
        self.addCleanup(first.stop); self.addCleanup(second.stop)

    def git(self, *args, cwd=None):
        return subprocess.check_output(
            ['git', '-c', 'user.name=P08 fixture', '-c', 'user.email=p08@example.invalid', *args],
            cwd=cwd or self.clone, text=True, stderr=subprocess.PIPE).strip()

    def verify_unchanged_checkout_and_real_ancestry(self):
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.commits[-1])
        self.assertEqual((self.clone / 'fixture').read_text(), '4')
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.git('merge-base', '--is-ancestor', self.commits[1], self.commits[-2])
        self.assertEqual(self.git('rev-parse', self.commits[1] + '^'), self.commits[0])

    def test_shallow_clone_gains_original_parent_chain_without_changing_head(self):
        self.assertEqual(self.git('rev-parse', '--is-shallow-repository'), 'true')
        bootstrap.fetch_historical_objects(self.clone)
        self.assertEqual(self.git('rev-parse', '--is-shallow-repository'), 'false')
        self.verify_unchanged_checkout_and_real_ancestry()

    def test_full_clone_is_not_made_shallow_again(self):
        self.git('fetch', '--unshallow', 'origin')
        bootstrap.fetch_historical_objects(self.clone)
        self.assertEqual(self.git('rev-parse', '--is-shallow-repository'), 'false')
        self.verify_unchanged_checkout_and_real_ancestry()

    def test_missing_pinned_object_is_rejected(self):
        with patch.object(bootstrap.stage_inputs, 'INPUT_COMMIT', '0' * 40):
            with self.assertRaises(subprocess.CalledProcessError):
                bootstrap.fetch_historical_objects(self.clone)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.commits[-1])
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_unknown_shallow_state_is_rejected_before_fetch(self):
        with patch.object(bootstrap.subprocess, 'check_output', return_value='unknown'):
            with patch.object(bootstrap, 'run') as run:
                with self.assertRaises(RuntimeError):
                    bootstrap.fetch_historical_objects(self.clone)
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
