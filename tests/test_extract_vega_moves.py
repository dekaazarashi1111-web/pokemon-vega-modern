#!/usr/bin/env python3
"""Focused tests for the pointer-rooted Vega move extractor."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from tools.engine.extract_vega_moves import (
    MOVE_COUNT,
    VegaMoveExtractionError,
    default_policy,
    extract_vega_moves,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = REPO_ROOT / "build/reference/vega.gba"


@unittest.skipUnless(ROM_PATH.is_file(), "fixed Vega reference ROM is unavailable")
class FixedVegaMoveExtractionTests(unittest.TestCase):
    rom: bytes
    result: dict[str, object]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rom = ROM_PATH.read_bytes()
        cls.result = extract_vega_moves(REPO_ROOT, cls.rom, default_policy())

    def test_exact_schema_count_and_frozen_ids(self) -> None:
        self.assertEqual(set(self.result), {"schema_version", "provenance", "tables", "moves", "summaries"})
        self.assertEqual(self.result["schema_version"], 1)
        moves = self.result["moves"]
        self.assertEqual(len(moves), MOVE_COUNT)
        self.assertEqual([row["id"] for row in moves], list(range(512)))
        required = {
            "id", "name_raw", "name_decoded", "effect", "power", "type", "accuracy", "pp",
            "secondary", "target", "priority", "flags", "raw_hex", "description_raw",
            "description_decoded", "normalized_name", "animation_pointer", "effect_script_pointer", "evidence",
        }
        self.assertTrue(all(set(row) == required for row in moves))

    def test_known_move_decodes_and_u32_flags_layout(self) -> None:
        move = self.result["moves"][1]
        self.assertEqual(move["name_raw"], "1a1008ffffffffff")
        self.assertEqual(move["name_decoded"], "はたく")
        self.assertEqual(move["normalized_name"], "はたく")
        self.assertEqual(
            (move["effect"], move["power"], move["type"], move["accuracy"], move["pp"]),
            (0, 40, 0, 100, 35),
        )
        self.assertEqual((move["secondary"], move["target"], move["priority"], move["flags"]), (0, 0, 0, 0x33))
        # ID 13 exercises upper flag bytes: the four bytes at +8 are one LE u32,
        # not a one-byte flag followed by padding.
        raw = bytes.fromhex(self.result["moves"][13]["raw_hex"])
        self.assertEqual(self.result["moves"][13]["flags"], 0x00010032)
        self.assertEqual(self.result["moves"][13]["flags"], int.from_bytes(raw[8:12], "little"))

    def test_all_fixed_tables_are_pointer_rooted_and_boundary_closed(self) -> None:
        tables = self.result["tables"]
        self.assertEqual((tables["move_names"]["count"], tables["move_names"]["record_size"]), (512, 8))
        self.assertEqual((tables["battle_moves"]["count"], tables["battle_moves"]["record_size"]), (512, 12))
        self.assertEqual((tables["descriptions"]["count"], tables["descriptions"]["record_size"]), (512, 60))
        self.assertEqual((tables["animations"]["count"], tables["animations"]["record_size"]), (512, 4))
        self.assertEqual((tables["effects"]["count"], tables["effects"]["record_size"]), (256, 4))
        self.assertEqual(tables["move_names"]["end_address_exclusive"], tables["battle_moves"]["address"])
        self.assertEqual(tables["battle_moves"]["end_address_exclusive"], tables["descriptions"]["address"])
        self.assertEqual(tables["descriptions"]["end_address_exclusive"], tables["animations"]["address"])
        self.assertEqual(tables["effects"]["boundary_evidence"]["entry_count"], 256)
        self.assertEqual(tables["effects"]["boundary_evidence"]["end_guard_hex"], "ff" * 16)
        self.assertTrue(all(table["pointer_sites"] for table in tables.values()))

    def test_description_animation_and_effect_links_are_rom_rooted(self) -> None:
        for row in self.result["moves"]:
            self.assertEqual(len(row["description_raw"]), 120)
            self.assertGreaterEqual(row["animation_pointer"], 0x08000000)
            self.assertLess(row["animation_pointer"], 0x09000000)
            self.assertGreaterEqual(row["effect_script_pointer"], 0x08000000)
            self.assertLess(row["effect_script_pointer"], 0x09000000)
            expected_effect_entry = self.result["tables"]["effects"]["address"] + row["effect"] * 4
            self.assertEqual(row["evidence"]["effect_entry_address"], expected_effect_entry)
        self.assertIn("\n", self.result["moves"][1]["description_decoded"])

    def test_output_is_deterministic_and_sanitized(self) -> None:
        again = extract_vega_moves(REPO_ROOT, self.rom, default_policy())
        first_json = json.dumps(self.result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        second_json = json.dumps(again, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(first_json, second_json)
        self.assertNotIn(str(REPO_ROOT), first_json)
        self.assertNotIn("timestamp", first_json.lower())

    def test_normalized_names_join_all_v3_vega_exclusive_rows(self) -> None:
        v3 = REPO_ROOT / "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/ベガ独自技再調整マスター.csv"
        if not v3.is_file():
            self.skipTest("V3 imported reference is unavailable")
        with v3.open(encoding="utf-8-sig", newline="") as stream:
            expected = {row["move_name"] for row in csv.DictReader(stream)}
        extracted = {row["normalized_name"] for row in self.result["moves"]}
        self.assertEqual(len(expected), 70)
        self.assertEqual(expected - extracted, set())

    def test_wrong_rom_hash_is_rejected(self) -> None:
        policy = default_policy()
        policy["rom"]["sha256"] = "00" * 32
        with self.assertRaisesRegex(VegaMoveExtractionError, "ROM sha256 mismatch"):
            extract_vega_moves(REPO_ROOT, self.rom, policy)

    def test_bad_actual_pointer_is_rejected_even_with_matching_rom_hash(self) -> None:
        mutated = bytearray(self.rom)
        pointer_site = 0x0804E7B4 - 0x08000000
        mutated[pointer_site : pointer_site + 4] = (0x08E0CBB0).to_bytes(4, "little")
        policy = default_policy()
        policy["rom"]["sha256"] = hashlib.sha256(mutated).hexdigest()
        with self.assertRaisesRegex(VegaMoveExtractionError, "move_names pointer mismatch"):
            extract_vega_moves(REPO_ROOT, bytes(mutated), policy)

    def test_bad_boundary_policy_is_rejected(self) -> None:
        policy = default_policy()
        policy["tables"]["descriptions"]["record_size"] = 59
        with self.assertRaisesRegex(VegaMoveExtractionError, "descriptions ABI mismatch"):
            extract_vega_moves(REPO_ROOT, self.rom, policy)

    def test_cli_reads_only_fixed_config_and_reference_and_emits_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools/engine/extract_vega_moves.py"), "--root", str(REPO_ROOT)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        parsed = json.loads(completed.stdout)
        self.assertEqual(parsed["summaries"]["move_count"], 512)
        self.assertEqual(parsed["provenance"]["rom"]["logical_path"], "build/reference/vega.gba")


if __name__ == "__main__":
    unittest.main()
