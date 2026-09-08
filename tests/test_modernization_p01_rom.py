from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.modernization_capacity import (
    CapacityAuditError,
    _audit_intervals,
    _scan_egg_moves,
    _scan_evolutions,
    build_modernization_capacity_audit,
    require_pass,
)


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "config" / "active_play_baseline.json"


class ModernizationP01RomAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        cls.rom_path = ROOT / baseline["rom"]["path"]
        cls.report = (
            build_modernization_capacity_audit(ROOT) if cls.rom_path.is_file() else None
        )

    def test_missing_exact_rom_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="modernization-p01-") as raw:
            root = Path(raw)
            (root / "config").mkdir()
            baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
            (root / "config" / "active_play_baseline.json").write_text(
                json.dumps(baseline), encoding="utf-8"
            )
            with self.assertRaises(CapacityAuditError):
                build_modernization_capacity_audit(root)

    def test_interval_audit_rejects_overlap(self) -> None:
        rows = [
            {
                "address_space": "TEST",
                "start": "0x00",
                "end_exclusive": "0x10",
                "size": "16",
                "owner": "A",
                "symbol": "left",
                "status": "LIVE",
            },
            {
                "address_space": "TEST",
                "start": "0x0F",
                "end_exclusive": "0x20",
                "size": "17",
                "owner": "B",
                "symbol": "right",
                "status": "LIVE",
            },
        ]
        report, errors = _audit_intervals(rows, {"TEST": (0, 0x20, "fixture")})
        self.assertEqual(1, report["TEST"]["overlap_count"])
        self.assertTrue(errors)

    def test_decoders_measure_capacity_and_validate_identity_domains(self) -> None:
        evolution = bytearray(2 * 128)
        evolution[0:8] = bytes.fromhex("0400100001000000")
        decoded = _scan_evolutions(bytes(evolution), 2)
        self.assertEqual((32, 1, 31), (
            decoded["declared_entries"],
            decoded["used_entries"],
            decoded["free_entries"],
        ))
        self.assertEqual(0, decoded["invalid_target_count"])

        egg = bytes.fromhex("214e01000200ffff")
        egg_report = _scan_egg_moves(egg, species_count=2, move_count=3)
        self.assertTrue(egg_report["terminator_present"])
        self.assertEqual({1: [1, 2]}, egg_report["records"])
        self.assertEqual(0, egg_report["invalid_move_count"])

    @unittest.skipUnless(
        json.loads(BASELINE.read_text(encoding="utf-8"))["rom"]["path"]
        and (ROOT / json.loads(BASELINE.read_text(encoding="utf-8"))["rom"]["path"]).is_file(),
        "active baseline exact ROM is not restored",
    )
    def test_stage62_exact_rom_capacity_and_roots_pass(self) -> None:
        assert self.report is not None
        require_pass(self.report)
        self.assertEqual("PASS", self.report["status"])
        self.assertEqual(62, self.report["input_identity"]["stage"])
        self.assertEqual(
            1_915_916,
            self.report["physical_rom_capacity"]["declared_free_bytes"],
        )
        self.assertEqual(
            self.report["physical_rom_capacity"]["declared_free_bytes"],
            self.report["physical_rom_capacity"]["actual_erased_free_bytes"],
        )
        self.assertEqual(
            0, self.report["physical_rom_capacity"]["untracked_non_erased_bytes"]
        )

    @unittest.skipUnless(
        (ROOT / json.loads(BASELINE.read_text(encoding="utf-8"))["rom"]["path"]).is_file(),
        "active baseline exact ROM is not restored",
    )
    def test_current_logical_capacity_and_caterpie_egg_are_separate(self) -> None:
        assert self.report is not None
        capacity = self.report["logical_capacity"]
        self.assertEqual((1621, 1063, 312, 999), tuple(
            capacity["id_spaces"][name]["declared_capacity"]
            for name in ("species", "move", "ability", "item")
        ))
        self.assertEqual(0, sum(
            capacity["id_spaces"][name]["free_slots"]
            for name in ("species", "move", "ability", "item")
        ))
        self.assertGreater(capacity["evolution"]["free_entries"], 20_000)
        self.assertEqual(0, capacity["tm_hm"]["free_catalog_slots"])
        self.assertEqual(0, capacity["tutor"]["free_catalog_slots"])
        identity = self.report["caterpie_egg_rom_identity"]
        self.assertEqual("PASS", identity["status"])
        self.assertEqual(649, identity["caterpie"]["manifest"]["id"])
        self.assertEqual(412, identity["internal_egg"]["manifest"]["id"])
        self.assertTrue(identity["caterpie"]["rom"]["meaningful_level_up_moves"])
        self.assertTrue(identity["caterpie"]["rom"]["evolution_entries"])
        self.assertFalse(identity["internal_egg"]["rom"]["evolution_entries"])
        self.assertFalse(identity["internal_egg"]["rom"]["egg_move_record_present"])

    @unittest.skipUnless(
        (ROOT / json.loads(BASELINE.read_text(encoding="utf-8"))["rom"]["path"]).is_file(),
        "active baseline exact ROM is not restored",
    )
    def test_cli_is_read_only_and_emits_same_exact_identity(self) -> None:
        before = self.rom_path.stat().st_mtime_ns
        process = subprocess.run(
            [
                "python3",
                "scripts/audit_modernization_p01_rom.py",
                "--root",
                str(ROOT),
                "--compact",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        output = json.loads(process.stdout)
        self.assertEqual("PASS", output["status"])
        self.assertEqual(
            self.report["input_identity"]["rom"], output["input_identity"]["rom"]
        )
        self.assertEqual(before, self.rom_path.stat().st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
