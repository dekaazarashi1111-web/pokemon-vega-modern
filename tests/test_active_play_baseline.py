from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zlib
from pathlib import Path

from tools.active_play_baseline import (
    ActivePlayBaselineError,
    load_active_play_baseline,
)


ROOT = Path(__file__).resolve().parents[1]


class ActivePlayBaselineTest(unittest.TestCase):
    def _fixture(self, root: Path, *, stage: int = 62) -> tuple[Path, Path]:
        rom = root / "baseline.gba"
        rom.write_bytes(b"explicitly-adopted-rom")
        raw = rom.read_bytes()
        manifest = root / "baseline.json"
        manifest.write_text(json.dumps({
            "schema_version": 1,
            "policy": "LATEST_EXPLICITLY_ADOPTED",
            "status": "ACTIVE",
            "stage": stage,
            "label": f"Stage{stage} fixture",
            "adopted_on": "2026-09-07",
            "rom": {
                "path": rom.relative_to(ROOT).as_posix(),
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "crc32": f"{zlib.crc32(raw) & 0xFFFFFFFF:08X}",
            },
        }), encoding="utf-8")
        return manifest, rom

    def test_exact_identity_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            manifest, rom = self._fixture(Path(raw))
            baseline = load_active_play_baseline(manifest, ROOT)
            self.assertEqual(baseline["stage"], 62)
            self.assertEqual(Path(baseline["rom"]["resolved_path"]), rom)

    def test_identity_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            manifest, rom = self._fixture(Path(raw))
            rom.write_bytes(b"changed")
            with self.assertRaisesRegex(ActivePlayBaselineError, "identity"):
                load_active_play_baseline(manifest, ROOT)

    def test_automatic_latest_policy_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            manifest, _rom = self._fixture(Path(raw))
            document = json.loads(manifest.read_text(encoding="utf-8"))
            document["policy"] = "HIGHEST_STAGE_ON_DISK"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ActivePlayBaselineError, "自動的"):
                load_active_play_baseline(manifest, ROOT, verify_rom=False)

    def test_workspace_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".local") as raw:
            manifest, _rom = self._fixture(Path(raw))
            document = json.loads(manifest.read_text(encoding="utf-8"))
            document["rom"]["path"] = "../outside.gba"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(ActivePlayBaselineError, "相対GBA"):
                load_active_play_baseline(manifest, ROOT, verify_rom=False)

    def test_repository_policy_doc_matches_manifest(self) -> None:
        manifest = load_active_play_baseline(verify_rom=False)
        policy = (ROOT / "design/active_play_baseline.md").read_text(encoding="utf-8")
        current_section = policy.split("## 直前の基準", 1)[0].replace(",", "")
        for expected in (
            f"Stage{manifest['stage']}",
            manifest["rom"]["path"],
            str(manifest["rom"]["size"]),
            manifest["rom"]["sha256"],
            manifest["rom"]["crc32"],
            manifest["policy"],
        ):
            self.assertIn(expected, current_section)


if __name__ == "__main__":
    unittest.main()
