"""公開manifestの各原本が、固定size/SHAで独立に特定できることを検証する。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest

from scripts.prepare_trainer_unit_inputs import MANIFEST, TrainerInputError, _rows, restore_inputs

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = _rows(ROOT)


class TrainerHistoricalInputIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 以前の実行のreportを今回の成功証拠として再利用しない。
        report_path = ROOT / 'build/private-unit-focus/trainer-input-restoration-all.json'
        if report_path.is_symlink():
            raise ValueError('Trainer identity report symlink rejected')
        report_path.unlink(missing_ok=True)
        cls.target = None
        cls.missing = set()
        try:
            cls.target = restore_inputs(ROOT)
        except TrainerInputError:
            # 既存の統合testは従来どおり例外を報告する。この追加test群では
            # 部分一致を全体PASSとせず、未一致の公開manifest項目を個別にFAILにする。
            if not report_path.is_file():
                raise
            report = json.loads(report_path.read_text())
            missing = report.get('missing')
            names = {row['path'] for row in ENTRIES}
            if not (
                report.get('schema_version') == 1 and report.get('profile') == 'all'
                and report.get('required') == len(ENTRIES)
                and isinstance(missing, list) and all(isinstance(name, str) for name in missing)
                and len(set(missing)) == len(missing) and set(missing) <= names
                and report.get('matched') == len(ENTRIES) - len(missing)
                and missing
                and report.get('manifest_sha256') == hashlib.sha256((ROOT / MANIFEST).read_bytes()).hexdigest()
            ):
                raise ValueError('Trainer identity report is not this complete manifest')
            cls.missing = set(missing)


def _test_identity(entry):
    def test(self):
        self.assertNotIn(entry['path'], self.missing)
        if self.target is not None:
            path = self.target / entry['path']
            self.assertFalse(any(part.is_symlink() for part in (path, *path.parents)))
            raw = path.read_bytes()
            self.assertEqual(len(raw), entry['size'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
    return test


# IDに使うのはGit管理されたsource_manifest内のpathだけ。private値や例外本文は使わない。
for _entry in ENTRIES:
    _name = 'test_' + re.sub(r'[^A-Za-z_0-9]', '_', _entry['path'])
    if hasattr(TrainerHistoricalInputIdentityTests, _name):
        raise ValueError('Trainer identity test name collision')
    setattr(TrainerHistoricalInputIdentityTests, _name, _test_identity(_entry))
