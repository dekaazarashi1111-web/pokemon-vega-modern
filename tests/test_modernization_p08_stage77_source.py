"""Authenticate the exact historical newline; reject generic source rewriting."""
from pathlib import Path
import copy
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from tools import modernization_p08_stage77_source as module
from tools.modernization_p05_stage77_suppression import _implementation_identity, _source_identities, stable_json

ROOT = Path(__file__).resolve().parents[1]


class Stage77SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'history'; self.root.mkdir()
        self.active = self.base / 'active'; self.active.mkdir()
        (self.root / '.git').write_text('gitdir: isolated-worktree')
        files = [row['path'] for row in _implementation_identity(ROOT)['files']]
        for name in [*files, module.CHECKPOINT]:
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        mock = patch.object(module.subprocess, 'check_output', return_value=module.COMMIT + '\n')
        mock.start(); self.addCleanup(mock.stop)
        self.raw = (self.root / module.SOURCE).read_bytes()

    def context(self):
        return module.original_stage77_source(self.root, self.active)

    def restored(self):
        self.assertEqual((self.root / module.SOURCE).read_bytes(), self.raw)

    def test_exact_one_byte_source_replay_matches_published_six_file_identity(self):
        with self.context():
            self.assertEqual((self.root / module.SOURCE).read_bytes(), self.raw + b'\n')
            self.assertEqual(_implementation_identity(self.root)['sha256'], module.IMPLEMENTATION)
        self.restored()

    def test_builder_failure_always_restores_current_source(self):
        with self.assertRaisesRegex(RuntimeError, 'failed builder'):
            with self.context(): raise RuntimeError('failed builder')
        self.restored()

    def test_builder_source_mutation_is_rejected_and_restored(self):
        with self.assertRaises(RuntimeError):
            with self.context(): (self.root / module.SOURCE).write_bytes(b'wrong')
        self.restored()

    def test_changed_current_source_is_not_hidden(self):
        path = self.root / module.SOURCE; path.write_bytes(b'changed')
        with self.assertRaises(RuntimeError):
            with self.context(): self.fail('must not yield')
        self.assertEqual(path.read_bytes(), b'changed')

    def test_other_implementation_file_change_is_rejected(self):
        path = self.root / 'tests/test_modernization_p05_stage77_suppression.py'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(RuntimeError, 'six-file'):
            with self.context(): self.fail('must not yield')
        self.restored()

    def test_original_source_pin_may_not_drift(self):
        with patch.object(module, 'ORIGINAL', (4841, '0' * 64)):
            with self.assertRaises(RuntimeError):
                with self.context(): self.fail('must not yield')
        self.restored()

    def test_published_checkpoint_pin_may_not_drift(self):
        (self.root / module.CHECKPOINT).write_text('{"implementation_sha256":"wrong"}')
        with self.assertRaises(RuntimeError):
            with self.context(): self.fail('must not yield')
        self.restored()

    def test_active_checkout_cannot_be_projected(self):
        with self.assertRaises(RuntimeError):
            with module.original_stage77_source(self.root, self.root): self.fail('must not yield')
        self.restored()

    def test_wrong_historical_commit_is_rejected(self):
        with patch.object(module.subprocess, 'check_output', return_value='wrong'):
            with self.assertRaises(RuntimeError):
                with self.context(): self.fail('must not yield')
        self.restored()

    def test_symlink_source_is_rejected_without_touching_target(self):
        path = self.root / module.SOURCE; target = self.base / 'target'
        path.rename(target); path.symlink_to(target)
        with self.assertRaises(ValueError):
            with self.context(): self.fail('must not yield')
        self.assertEqual(target.read_bytes(), self.raw)

    def test_all_metadata_bytes_match_the_original_pinned_artifact(self):
        # Independent reconstruction from the published checkpoint and unchanged
        # cumulative allocation: not a writer or substitute for the ROM builder.
        checkpoint = json.loads((ROOT / module.CHECKPOINT).read_bytes())
        allocation = json.loads((ROOT / 'build/stages/78_modernization_p05_eelevate_switch_ai_allocation.json').read_bytes())
        with self.context():
            metadata = {key: copy.deepcopy(checkpoint[key]) for key in
                        ('schema_version', 'task', 'stage', 'status', 'parent', 'output',
                         'payload', 'allocation_sequence', 'allocation_lineage', 'bps',
                         'checks', 'active_play_baseline', 'release_ready', 'full_p05_done', 'done')}
            metadata.update({
                'allocation': allocation['allocations'][80],
                'suppression': {'battle_circus_global_fixed': True, 'ordinary_suppression_changed': False,
                                'hook_count': 29, 'ability_surface_occurrence_count': 33},
                'remaining_work': checkpoint['pending'], 'source_identities': _source_identities(self.root),
                'implementation': _implementation_identity(self.root), 'artifact_count': 9,
            })
            raw = stable_json(metadata)
            self.assertEqual(len(raw), 5933)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),
                             '773042fc80d4a048e4f4a894e01de8f073d6de42cf5f4029421c882b0c35b6ff')
        self.restored()


if __name__ == '__main__': unittest.main()
