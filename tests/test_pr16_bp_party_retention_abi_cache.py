from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pr16_bp_party_retention_abi_cache",
    ROOT / "scripts/pr16_bp_party_retention_abi_cache.py",
)
assert SPEC and SPEC.loader
cache = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cache)


class CacheDiscoveryTests(unittest.TestCase):
    def test_two_complete_runs_are_selected(self) -> None:
        fingerprint = "a" * 64
        root = f"build/battle-core/{fingerprint}"
        names = [
            f"{root}/run-1/linked.o",
            f"{root}/run-1/outcome.json",
            f"{root}/run-2/linked.o",
            f"{root}/run-2/outcome.json",
            "ignored.txt",
        ]
        groups = cache.discover(names)
        self.assertEqual(set(groups), {fingerprint})
        self.assertEqual(groups[fingerprint][2]["linked.o"], names[2])

    def test_duplicate_member_is_rejected(self) -> None:
        fingerprint = "b" * 64
        member = f"build/battle-core/{fingerprint}/run-1/linked.o"
        with self.assertRaisesRegex(cache.CacheAuditError, "duplicate cache member"):
            cache.discover([member, member])


if __name__ == "__main__":
    unittest.main()
