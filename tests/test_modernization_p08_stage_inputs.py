"""Historical input projection must preserve the real checkout and all contracts."""
from pathlib import Path
from contextlib import ExitStack
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from tools import modernization_p08_stage_inputs as module


class StageInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'history'; self.root.mkdir()
        self.active = self.base / 'active'; self.active.mkdir()
        (self.root / '.git').write_text('gitdir: a-linked-worktree')
        self.old = {name: b'old:' + name.encode() for name in module.INPUTS}
        self.new = {name: b'new:' + name.encode() for name in module.INPUTS}
        identity = lambda value: (len(value), hashlib.sha256(value).hexdigest())
        self.pins = {key: identity(raw) for key, raw in self.old.items()}
        self.next_pins = {key: identity(raw) for key, raw in self.new.items()}
        for name, raw in self.new.items():
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        for name in module.CONFIGS:
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({'inputs': {key: {'path': key, 'size': value[0], 'sha256': value[1]} for key, value in self.pins.items()}}))
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(module, 'INPUTS', self.pins))
        self.stack.enter_context(patch.object(module, 'SUCCESSORS', self.next_pins))
        self.stack.enter_context(patch.object(module.subprocess, 'check_output', side_effect=self.git))

    def git(self, command, **kwargs):
        if command[1:3] == ['rev-parse', 'HEAD']: return module.COMMIT + '\n'
        self.assertEqual(command[:2], ['git', 'show'])
        self.assertTrue(command[2].startswith(module.INPUT_COMMIT + ':'))
        return self.old[command[2].split(':', 1)[1]]

    def check_restored(self):
        for name, raw in self.new.items(): self.assertEqual((self.root / name).read_bytes(), raw)

    def test_exact_projection_is_restored_after_success(self):
        with module.original_stage_inputs(self.root, self.active):
            for name, raw in self.old.items(): self.assertEqual((self.root / name).read_bytes(), raw)
        self.check_restored()

    def test_builder_failure_restores_all_three_inputs(self):
        with self.assertRaisesRegex(RuntimeError, 'builder failed'):
            with module.original_stage_inputs(self.root, self.active): raise RuntimeError('builder failed')
        self.check_restored()

    def test_builder_mutation_is_rejected_and_restored(self):
        with self.assertRaisesRegex(RuntimeError, 'identity mismatch'):
            with module.original_stage_inputs(self.root, self.active):
                (self.root / next(iter(self.old))).write_bytes(b'changed')
        self.check_restored()

    def test_bad_git_blob_fails_before_any_write(self):
        self.old[list(self.old)[-1]] = b'wrong history'
        with self.assertRaises(RuntimeError):
            with module.original_stage_inputs(self.root, self.active): self.fail('must not yield')
        self.check_restored()

    def test_modified_current_input_is_not_hidden(self):
        path = self.root / next(iter(self.new)); path.write_bytes(b'changed')
        with self.assertRaises(RuntimeError):
            with module.original_stage_inputs(self.root, self.active): self.fail('must not yield')
        self.assertEqual(path.read_bytes(), b'changed')

    def test_changed_declared_contract_is_rejected(self):
        (self.root / module.CONFIGS[0]).write_text('{"inputs": {}}')
        with self.assertRaises(RuntimeError):
            with module.original_stage_inputs(self.root, self.active): self.fail('must not yield')
        self.check_restored()

    def test_active_checkout_cannot_be_projected(self):
        with self.assertRaises(RuntimeError):
            with module.original_stage_inputs(self.root, self.root): self.fail('must not yield')
        self.check_restored()

    def test_active_checkout_descendant_cannot_be_projected(self):
        with self.assertRaises(RuntimeError):
            with module.original_stage_inputs(self.root, self.base): self.fail('must not yield')

    def test_unapproved_git_head_is_rejected(self):
        with patch.object(module.subprocess, 'check_output', return_value='wrong-head'):
            with self.assertRaises(RuntimeError):
                with module.original_stage_inputs(self.root, self.active): self.fail('must not yield')
        self.check_restored()

    def test_symlink_input_is_rejected(self):
        path = self.root / next(iter(self.new)); raw = path.read_bytes(); path.unlink()
        target = self.base / 'target'; target.write_bytes(raw); path.symlink_to(target)
        with self.assertRaises(ValueError):
            with module.original_stage_inputs(self.root, self.active): self.fail('must not yield')
        self.assertEqual(target.read_bytes(), raw)

    def test_normal_checkout_is_rejected(self):
        (self.root / '.git').unlink(); (self.root / '.git').mkdir()
        with self.assertRaises(RuntimeError):
            with module.original_stage_inputs(self.root, self.active): self.fail('must not yield')


if __name__ == '__main__': unittest.main()
