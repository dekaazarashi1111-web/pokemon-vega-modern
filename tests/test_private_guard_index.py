from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import guard_private_files as guard  # noqa: E402


class PrivateGuardIndexTest(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
        return temporary, root

    def run_guard(self, root: Path) -> tuple[int, str]:
        output = io.StringIO()
        with mock.patch.object(guard, 'repo_root', return_value=root):
            with contextlib.redirect_stdout(output):
                result = guard.main()
        return result, output.getvalue()

    def test_document_scan_reads_staged_blob_not_safe_worktree_replacement(self) -> None:
        temporary, root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        document = root / 'notes.md'
        document.write_text('/home/alice/private/input.gba\n', encoding='utf-8')
        subprocess.run(['git', 'add', 'notes.md'], cwd=root, check=True)
        document.write_text('portable text only\n', encoding='utf-8')

        result, output = self.run_guard(root)

        self.assertEqual(result, 1)
        self.assertIn('notes.md: lines 1', output)

    def test_zip_scan_reads_staged_blob_not_safe_worktree_replacement(self) -> None:
        temporary, root = self.make_repo()
        self.addCleanup(temporary.cleanup)
        archive = root / 'payload.zip'
        with zipfile.ZipFile(archive, 'w') as handle:
            handle.writestr('private/rom.gba', b'')
        subprocess.run(['git', 'add', 'payload.zip'], cwd=root, check=True)
        archive.unlink()
        with zipfile.ZipFile(archive, 'w') as handle:
            handle.writestr('README.txt', b'safe worktree replacement')

        result, output = self.run_guard(root)

        self.assertEqual(result, 1)
        self.assertIn('payload.zip: private/rom.gba', output)


if __name__ == '__main__':
    unittest.main()
