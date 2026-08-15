#!/usr/bin/env python3
"""T07 Species mapping、generator、stage、publish checkの焦点テスト。"""

from __future__ import annotations

import copy
import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.build_species_port import (
    ARTIFACT_PATHS,
    SpeciesPortError,
    build_species_model,
    build_stage,
    check,
    render_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/species_port.json"
STAGE06 = ROOT / "build/stages/06_battle_core.gba"
sys.path.insert(0, str(ROOT / "scripts"))
import validate_manifests as manifest_validator  # noqa: E402


@unittest.skipUnless(CONFIG.is_file() and STAGE06.is_file(), "T07 fixed inputs unavailable")
class SpeciesPortBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.model = build_species_model(ROOT, cls.config)

    def test_exact_counts_frozen_prefix_and_alias_coverage(self) -> None:
        self.assertEqual(
            self.model["summary"],
            {
                "vega_frozen_count": 412,
                "dpe_table_count": 1440,
                "dpe_source_count": 1415,
                "canonical_count": 1621,
                "dpe_alias_to_vega_count": 206,
                "dpe_appended_count": 1209,
                "official_national_count": 1025,
                "official_form_duplicate_group_count": 209,
                "official_form_row_count": 597,
                "unofficial_vega_count": 207,
            },
        )
        rows = self.model["species"]
        self.assertEqual([row["id"] for row in rows], list(range(1621)))
        self.assertEqual([row["vega_id"] for row in rows[:412]], list(range(412)))
        self.assertTrue(all(row["status"] == "FROZEN" for row in rows[:412]))
        self.assertTrue(all(row["status"] == "APPENDED" for row in rows[412:]))
        source_ids = {row["source_id"] for row in self.model["aliases"]}
        self.assertEqual(len(source_ids), 1415)
        self.assertNotIn(252, source_ids)
        self.assertIn(1439, source_ids)
        self.assertEqual(
            self.model["runtime_reservation"],
            {
                "canonical_id": 412,
                "species_key": "SPECIES_KEY_EGG",
                "dpe_id": 412,
                "displaced_species_key": "SPECIES_KEY_CATERPIE",
                "displaced_canonical_id": 649,
                "status": "PASS",
            },
        )
        self.assertEqual(rows[412]["species_key"], "SPECIES_KEY_EGG")
        self.assertEqual(rows[649]["species_key"], "SPECIES_KEY_CATERPIE")

    def test_official_count_deduplicates_forms(self) -> None:
        rows = self.model["species"]
        official = [row for row in rows if row["is_official"]]
        self.assertEqual({row["canonical_national_dex"] for row in official}, set(range(1, 1026)))
        ogerpon = [row for row in official if row["canonical_national_dex"] == 1017]
        self.assertGreater(len(ogerpon), 1)
        self.assertEqual(len({row["canonical_national_dex"] for row in ogerpon}), 1)
        appended_forms = [row for row in official if row["classification"] == "DPE_FORM_APPEND"]
        self.assertTrue(all(row["form_key"].startswith("FORM_KEY_") for row in appended_forms))

    def test_generated_tables_have_complete_canonical_rows(self) -> None:
        artifacts = render_artifacts(self.model)
        self.assertEqual(set(artifacts), set(ARTIFACT_PATHS))
        self.assertEqual(len(artifacts["generated/engine/species/base_stats.bin"]), 1621 * 32)
        self.assertEqual(len(artifacts["generated/engine/species/species_names.bin"]), 1621 * 11)
        self.assertEqual(len(artifacts["generated/engine/species/national_dex.bin"]), 1621 * 2)
        source = artifacts["generated/engine/species/official_species_count.c"].decode("ascii")
        self.assertIn("for (unsigned national = 1; national <= 1025; ++national)", source)
        self.assertNotIn("row->", source)
        base_stats = artifacts["generated/engine/species/base_stats.bin"]
        for species_id in range(1621):
            row = base_stats[species_id * 32:(species_id + 1) * 32]
            self.assertLess(int.from_bytes(row[12:14], "little"), 999)
            self.assertLess(int.from_bytes(row[14:16], "little"), 999)
            self.assertLess(int.from_bytes(row[22:24], "little"), 312)
            self.assertLess(int.from_bytes(row[26:28], "little"), 312)
            self.assertLess(int.from_bytes(row[28:30], "little"), 312)

    def test_existing_reference_domains_are_all_resolved(self) -> None:
        validation = self.model["reference_validation"]
        self.assertEqual(validation["status"], "PASS")
        self.assertEqual(
            set(validation["sources"]),
            {"trainer_parties", "wild_tables", "scripts_and_gifts", "evolutions"},
        )
        for source in validation["sources"].values():
            self.assertEqual(source["status"], "PASS")
            self.assertTrue(all(0 <= value <= 411 for value in source["unique_ids"]))

    def test_stage_repoints_all_canonical_base_stats_consumers(self) -> None:
        stage, metadata = build_stage(ROOT, self.config, self.model)
        old = int(self.config["runtime"]["old_base_stats_address"]).to_bytes(4, "little")
        new = int(self.config["runtime"]["new_base_stats_address"]).to_bytes(4, "little")
        self.assertEqual(metadata["base_stats"]["repoint_count"], 105)
        self.assertTrue(all(stage[site:site + 4] == new for site in metadata["base_stats"]["repoint_sites"]))
        self.assertEqual(sum(stage[index:index + 4] == old for index in range(0, len(stage) - 3, 4)), 0)
        offset = self.config["runtime"]["new_base_stats_offset"]
        self.assertEqual(stage[offset:offset + 32], bytes.fromhex(self.model["base_stats_hex"][:64]))

    def test_mapping_policy_is_fail_closed(self) -> None:
        broken = copy.deepcopy(self.config)
        broken["mapping_policy"]["reuse_frozen_holes"] = True
        with self.assertRaisesRegex(SpeciesPortError, "frozen Species range"):
            build_species_model(ROOT, broken)

    def test_manifest_validator_rejects_form_count_inflation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="t07-manifests-") as raw:
            temporary = Path(raw)
            shutil.copytree(ROOT / "manifests", temporary / "manifests")
            shutil.copytree(ROOT / "content", temporary / "content")
            (temporary / "reports/generated").mkdir(parents=True)
            shutil.copy2(
                ROOT / "reports/generated/id_inventory.json",
                temporary / "reports/generated/id_inventory.json",
            )
            path = temporary / "manifests/species_ids.csv"
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
                header = list(rows[0])
            form = next(row for row in rows if row["classification"] == "DPE_FORM_APPEND")
            form["canonical_national_dex"] = "0"
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            errors = manifest_validator.collect_errors(temporary)
            self.assertTrue(any("official National Dex out of range" in error for error in errors))


@unittest.skipUnless((ROOT / "build/stages/07_species.json").is_file(), "T07 stage not published")
class PublishedSpeciesPortTests(unittest.TestCase):
    def test_check_is_read_only_and_passes(self) -> None:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        tracked = [
            ROOT / config["runtime"]["output_rom_path"],
            ROOT / config["runtime"]["output_metadata_path"],
            *(ROOT / path for path in ARTIFACT_PATHS),
        ]
        before = {path: path.read_bytes() for path in tracked}
        result = check(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["species"], 1621)
        self.assertEqual(before, {path: path.read_bytes() for path in tracked})


if __name__ == "__main__":
    unittest.main()
