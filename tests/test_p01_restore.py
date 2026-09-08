"""P01: report衝突を上書き・無視せず、両snapshotを保全する回帰試験。"""
from pathlib import Path
import tempfile
import unittest

from scripts.github_private_environment import PrivateEnvironmentError, build_archive, restore_archive
from scripts.restore_p01_environment import REPORT, blob_identity, preserve_report


class PreservationTests(unittest.TestCase):
    def fixture(self, root):
        path = root / REPORT
        path.parent.mkdir(parents=True)
        path.write_bytes(b'{"current": true}\n')
        return path, path.read_bytes()

    def test_success_preserves_both_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, before = self.fixture(root)
            with preserve_report(root, blob_identity(before)) as evidence:
                self.assertFalse(path.exists())
                path.write_bytes(b'{"historical": true}\n')
            self.assertEqual(path.read_bytes(), before)
            self.assertTrue(evidence["current_preserved"])
            archived = list((root / ".local").glob("p01-snapshot-report-*/archived.json"))
            self.assertEqual(len(archived), 1)
            self.assertEqual(archived[0].read_bytes(), b'{"historical": true}\n')

    def test_exception_restores_current_and_keeps_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, before = self.fixture(root)
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                with preserve_report(root, blob_identity(before)):
                    path.write_bytes(b"historical")
                    raise RuntimeError("fixture failure")
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(next((root / ".local").glob("*/archived.json")).read_bytes(), b"historical")

    def test_exception_before_restore_still_recovers_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, before = self.fixture(root)
            with self.assertRaises(RuntimeError):
                with preserve_report(root, blob_identity(before)):
                    raise RuntimeError("no archive restored")
            self.assertEqual(path.read_bytes(), before)

    def test_wrong_head_pin_rejected_without_side_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, before = self.fixture(root)
            with self.assertRaisesRegex(PrivateEnvironmentError, "HEAD_IDENTITY_MISMATCH"):
                with preserve_report(root, "0" * 40):
                    self.fail("must not enter")
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse((root / ".local").exists())

    def test_backup_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp)
            path, before = self.fixture(root)
            (root / ".local").symlink_to(outside)
            with self.assertRaisesRegex(PrivateEnvironmentError, "BACKUP_SYMLINK"):
                with preserve_report(root, blob_identity(before)):
                    self.fail("must not enter")
            self.assertEqual(path.read_bytes(), before)

    def test_report_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path, before = self.fixture(root)
            backing = root / "backing"
            backing.write_bytes(before)
            path.unlink()
            path.symlink_to(backing)
            with self.assertRaisesRegex(PrivateEnvironmentError, "NOT_REGULAR"):
                with preserve_report(root, blob_identity(before)):
                    self.fail("must not enter")
            self.assertEqual(backing.read_bytes(), before)

    def test_original_restore_hash_and_collision_guards_still_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source, target = base / "source", base / "target"
            source.mkdir()
            target.mkdir()
            path, before = self.fixture(target)
            data = source / "reports"
            data.mkdir()
            (data / "stage61_wiki.json").write_bytes(b"historical")
            spec = {"name": "fixture.zip", "sources": [{"source": "reports", "destination": "reports/generated", "exclude": []}]}
            archive = base / "fixture.zip"
            pin = build_archive(source, spec, archive)
            original = archive.read_bytes()
            with self.assertRaisesRegex(PrivateEnvironmentError, "衝突"):
                restore_archive(target, archive, pin, False)
            with preserve_report(target, blob_identity(before)):
                result = restore_archive(target, archive, pin, False)
                self.assertEqual(result["restored"], 1)
                self.assertEqual(path.read_bytes(), b"historical")
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(archive.read_bytes(), original)
            with self.assertRaisesRegex(PrivateEnvironmentError, "外側hash"):
                restore_archive(target, archive, dict(pin, sha256="0" * 64), False)


if __name__ == "__main__":
    unittest.main()
