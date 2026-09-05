from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
from pathlib import Path

from scripts import build_event_authoring_packet as packet_builder
from scripts.build_event_authoring_packet import PACKET_NAME, build_packet


ROOT = Path(__file__).resolve().parents[1]
HAS_STAGE35_INPUTS = all((ROOT / path).is_file() for path in (
    "build/stages/35_trainer_changekit_final.gba",
    "build/stages/35_trainer_changekit_final.json",
    "build/stages/26_acquisition_events.json",
)) and (ROOT / "generated/maps/kanto").is_dir()


def _fixture_history(base: Path) -> tuple[Path, str, str]:
    repo = base / "history"
    repo.mkdir()
    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-c", "user.name=Unit Fixture", "-c", "user.email=fixture@example.invalid", *args],
            cwd=repo, stderr=subprocess.PIPE, text=True,
        ).strip()
    git("init", "--quiet")
    git("commit", "--allow-empty", "--quiet", "-m", "baseline")
    baseline = git("rev-parse", "HEAD")
    git("commit", "--allow-empty", "--quiet", "-m", "descendant")
    head = git("rev-parse", "HEAD")
    return repo, baseline, head


@unittest.skipUnless(HAS_STAGE35_INPUTS, "Stage35 generated inputs are not present")
class EventAuthoringPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = self.enterContext(tempfile.TemporaryDirectory(prefix="packet-history-"))
        repo, baseline, _ = _fixture_history(Path(temporary))
        # The packet contract is exercised with real Git ancestry, independent
        # of the enclosing checkout's shallow boundary or branch history.
        self.enterContext(mock.patch.object(packet_builder, "STAGE35_BASELINE_COMMIT", baseline))
        self.enterContext(mock.patch.dict(os.environ, {
            "GIT_DIR": str(repo / ".git"), "GIT_WORK_TREE": str(repo),
        }))

    def _build(self, base: Path, name: str) -> tuple[dict[str, object], Path, Path]:
        output = base / f"packet-{name}"
        archive = base / f"{name}.zip"
        result = build_packet(ROOT, output, archive)
        return result, output / PACKET_NAME, archive

    def test_packet_is_deterministic_private_free_and_self_validating(self) -> None:
        with tempfile.TemporaryDirectory(prefix="event-authoring-test-") as temporary:
            base = Path(temporary)
            first, packet, first_zip = self._build(base, "first")
            second, _, second_zip = self._build(base, "second")

            self.assertEqual(first["status"], "PASS")
            self.assertEqual(first["zip_sha256"], second["zip_sha256"])
            self.assertEqual(
                hashlib.sha256(first_zip.read_bytes()).hexdigest(),
                hashlib.sha256(second_zip.read_bytes()).hexdigest(),
            )
            counts = first["catalog_counts"]
            self.assertEqual(counts["maps"], 253)
            self.assertEqual(counts["logical_locations"], 47)
            self.assertEqual(counts["kanto_trainers"], 201)
            self.assertEqual(counts["acquisition_hosts"], 24)
            self.assertEqual(counts["qol_features"], 35)
            self.assertGreater(counts["available_source_object_hosts"], 0)
            self.assertGreater(counts["available_bg_event_hosts"], 0)

            manifest = json.loads((packet / "PACKET_MANIFEST.json").read_text(encoding="utf-8"))
            self.assertFalse(manifest["privacy"]["rom_included"])
            self.assertFalse(manifest["privacy"]["save_included"])
            report = json.loads(
                (packet / "submission_template/VALIDATION_REPORT.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["status"], "PASS")
            with zipfile.ZipFile(first_zip) as archive:
                self.assertIsNone(archive.testzip())
                names = archive.namelist()
                self.assertTrue(all(name.startswith(f"{PACKET_NAME}/") for name in names))
                self.assertFalse(any(name.lower().endswith((".gba", ".sav", ".pyc")) for name in names))

    def test_validator_rejects_cross_map_host_claim(self) -> None:
        with tempfile.TemporaryDirectory(prefix="event-authoring-validator-") as temporary:
            base = Path(temporary)
            _, packet, _ = self._build(base, "validator")
            submission = base / "submission"
            shutil.copytree(packet / "submission_template", submission)
            plan_path = submission / "event_plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["placements"][0]["map_key"] = "KANTO_OUTDOOR_CERULEAN_CITY"
            plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            run = subprocess.run(
                [sys.executable, str(packet / "tools/validate_submission.py"), str(submission),
                 "--packet-root", str(packet), "--allow-template"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertNotEqual(run.returncode, 0)
            report = json.loads(run.stdout)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any("bg host belongs to" in error for error in report["errors"]))


class EventAuthoringHistoryBoundaryTests(unittest.TestCase):
    def test_real_git_ancestry_is_required_even_for_a_valid_packet(self) -> None:
        with tempfile.TemporaryDirectory(prefix="packet-ancestry-") as temporary:
            root = Path(temporary)
            repo, baseline, head = _fixture_history(root)
            stages = root / "build/stages"
            stages.mkdir(parents=True)
            (stages / "35_trainer_changekit_final.gba").write_bytes(b"synthetic unit fixture, not a ROM")
            (stages / "35_trainer_changekit_final.json").write_text("{}")
            packet = root / "packet"
            packet.mkdir()
            (packet / "README.md").write_text("synthetic packet")
            with mock.patch.dict(os.environ, {"GIT_DIR": str(repo / ".git"), "GIT_WORK_TREE": str(repo)}):
                with mock.patch.object(packet_builder, "STAGE35_BASELINE_COMMIT", baseline):
                    manifest = packet_builder._manifest(root, packet, {})
                    self.assertEqual(manifest["baseline"]["git_commit"], baseline)
                    # A shallow boundary must not be mistaken for proof of ancestry.
                    (repo / ".git/shallow").write_text(head + "\n")
                    with self.assertRaisesRegex(packet_builder.PacketError, "not an ancestor"):
                        packet_builder._manifest(root, packet, {})
                    (repo / ".git/shallow").unlink()
                with mock.patch.object(packet_builder, "STAGE35_BASELINE_COMMIT", "f" * 40):
                    with self.assertRaisesRegex(packet_builder.PacketError, "not an ancestor"):
                        packet_builder._manifest(root, packet, {})


if __name__ == "__main__":
    unittest.main()
