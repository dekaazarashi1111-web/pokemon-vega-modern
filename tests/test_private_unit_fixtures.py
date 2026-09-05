from __future__ import annotations

import unittest
from unittest import mock
from pathlib import Path
import tempfile

from tests.fixtures import private_unit_fixtures as fixtures


class PrivateUnitFixtureTests(unittest.TestCase):
    def test_mismatched_existing_save_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            output = root / "fixture.srm"
            output.write_bytes(b"synthetic user sentinel")
            with mock.patch.object(fixtures.builder, "ROOT", root), \
                    mock.patch.object(fixtures.builder, "_read_json", return_value={"output": {"save": "fixture.srm"}}), \
                    mock.patch.object(fixtures.builder, "validate_profile"), \
                    mock.patch.object(fixtures.builder, "_compile_runner") as compile_runner:
                with self.assertRaisesRegex(ValueError, "will not be overwritten"):
                    fixtures.ensure_stage60_test_ready_save()
                compile_runner.assert_not_called()
            self.assertEqual(output.read_bytes(), b"synthetic user sentinel")

    def test_symlink_save_is_rejected_before_generation(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "fixture.srm").symlink_to(root / "target.srm")
            with mock.patch.object(fixtures.builder, "ROOT", root), \
                    mock.patch.object(fixtures.builder, "_read_json", return_value={"output": {"save": "fixture.srm"}}), \
                    mock.patch.object(fixtures.builder, "validate_profile"):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    fixtures.ensure_stage60_test_ready_save()
            self.assertFalse((root / "target.srm").exists())
