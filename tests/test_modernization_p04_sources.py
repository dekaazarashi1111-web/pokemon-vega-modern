#!/usr/bin/env python3
"""工程4の公式候補・固定source監査に対するfocused test。"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.modernization_p04_sources import (
    P04SourceError,
    _load_csv_keys,
    _parse_jasc_palette,
    _parse_png,
    _validate_candidate_contract,
    _validate_official_sources,
    audit_p04_sources,
)


class ModernizationP04SourcesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = ROOT / ".local/modernization_sources/pokeemerald-expansion"
        if not cls.source_root.is_dir():
            raise unittest.SkipTest("固定source checkoutがローカルにないため実素材testを省略")
        cls.result = audit_p04_sources(ROOT, source_root=cls.source_root)

    def test_candidate_counts_and_manifest_diff(self) -> None:
        self.assertEqual("PASS", self.result["status"])
        self.assertFalse(self.result["implementation_ready"])
        self.assertEqual(
            {
                "all_records": 54,
                "adoption_candidate_records": 49,
                "classification_hold_records": 2,
                "non_adopted_user_scope_records": 3,
                "mega_runtime_records": 49,
                "mega_identity_groups": 48,
                "unique_mega_stones": 45,
                "new_species_records": 3,
                "adopted_new_species_records": 0,
            },
            self.result["candidate_counts"],
        )
        self.assertEqual(49, self.result["manifest_diff"]["new_species_or_form_key_count"])
        self.assertEqual(45, self.result["manifest_diff"]["new_item_key_count"])
        self.assertEqual(6, self.result["manifest_diff"]["new_ability_dependency_key_count"])

    def test_selected_checkout_is_exact_and_gba_ready(self) -> None:
        checkout = self.result["source_checkout"]
        self.assertEqual("cafe0221cefb2a991cc0ece429174ade877d037d", checkout["commit"])
        self.assertTrue(checkout["clean"])
        self.assertFalse(checkout["redistribution_allowed"])
        self.assertEqual(49, checkout["coverage"]["mega_runtime_records"]["covered"])
        self.assertEqual(48, checkout["coverage"]["unique_mega_asset_directories"]["covered"])
        self.assertEqual(45, checkout["coverage"]["mega_stones"]["covered"])
        self.assertEqual(0, checkout["coverage"]["winds_waves_new_species"]["covered"])
        self.assertEqual(0, checkout["coverage"]["winds_waves_new_species"]["required"])
        self.assertEqual(64, len(checkout["asset_set_sha256"]))

    def test_winds_waves_species_keep_provenance_without_active_reservations(self) -> None:
        excluded = self.result["non_adopted_user_scope"]
        self.assertEqual(
            {"P04_SPECIES_BROWT", "P04_SPECIES_POMBON", "P04_SPECIES_GECQUA"},
            set(excluded["records"]),
        )
        self.assertEqual(0, excluded["id_reservation_count"])
        self.assertEqual(0, excluded["asset_requirement_count"])
        self.assertEqual(
            {
                "SPECIES_KEY_BROWT", "SPECIES_KEY_POMBON", "SPECIES_KEY_GECQUA",
            },
            set(excluded["preserved_candidate_species_keys"]),
        )
        self.assertNotIn(
            "BLOCKER_WINDS_WAVES_ASSETS",
            {item["blocker_key"] for item in self.result["blockers"]},
        )

    def test_non_adopted_winds_waves_record_cannot_be_silently_reactivated(self) -> None:
        candidate = json.loads((ROOT / "content/modernization/p04_candidate_manifest.json").read_text(encoding="utf-8"))
        official = json.loads((ROOT / "content/modernization/p04_official_sources.json").read_text(encoding="utf-8"))
        candidate = copy.deepcopy(candidate)
        target = next(row for row in candidate["records"] if row["record_key"] == "P04_SPECIES_BROWT")
        target["implementation_scope"] = "ADOPT_CANDIDATE"
        sources = _validate_official_sources(official)
        species, _ = _load_csv_keys(ROOT / "manifests/species_ids.csv", "species_key")
        items, _ = _load_csv_keys(ROOT / "manifests/item_ids.csv", "item_key")
        abilities, _ = _load_csv_keys(ROOT / "manifests/ability_ids.csv", "ability_key")
        with self.assertRaisesRegex(P04SourceError, "容量拡張前のID割当は禁止"):
            _validate_candidate_contract(candidate, sources, species, items, abilities)

    def test_temporary_abilities_have_unique_replacement_keys(self) -> None:
        data = json.loads((ROOT / "content/modernization/p04_candidate_manifest.json").read_text(encoding="utf-8"))
        rows = [row for row in data["records"] if row["ability_status"] == "TEMPORARY_REPLACEABLE"]
        replacements = [row["ability_replacement_key"] for row in rows]
        self.assertEqual(16, len(rows))
        self.assertEqual(len(replacements), len(set(replacements)))
        self.assertTrue(all(key.startswith("REPLACEMENT_KEY_ABILITY_") for key in replacements))

    def test_missing_temporary_replacement_fails_closed(self) -> None:
        candidate = json.loads((ROOT / "content/modernization/p04_candidate_manifest.json").read_text(encoding="utf-8"))
        official = json.loads((ROOT / "content/modernization/p04_official_sources.json").read_text(encoding="utf-8"))
        candidate = copy.deepcopy(candidate)
        target = next(row for row in candidate["records"] if row["ability_status"] == "TEMPORARY_REPLACEABLE")
        target["ability_replacement_key"] = None
        sources = _validate_official_sources(official)
        species, _ = _load_csv_keys(ROOT / "manifests/species_ids.csv", "species_key")
        items, _ = _load_csv_keys(ROOT / "manifests/item_ids.csv", "item_key")
        abilities, _ = _load_csv_keys(ROOT / "manifests/ability_ids.csv", "ability_key")
        with self.assertRaisesRegex(P04SourceError, "replacement key必須"):
            _validate_candidate_contract(candidate, sources, species, items, abilities)

    def test_missing_checkout_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "not-fetched"
            with self.assertRaisesRegex(P04SourceError, "固定asset sourceがありません"):
                audit_p04_sources(ROOT, source_root=missing, require_checkout=True)

    def test_png_and_palette_contract_samples(self) -> None:
        sprite = self.source_root / "graphics/pokemon/clefable/mega/front.png"
        palette = self.source_root / "graphics/pokemon/clefable/mega/normal.pal"
        self.assertEqual(
            {"width": 64, "height": 64, "bit_depth": 8, "color_type": 3},
            _parse_png(sprite),
        )
        self.assertEqual(
            {"declared_colors": 16, "actual_colors": 16},
            _parse_jasc_palette(palette),
        )

    def test_cli_check_has_no_tracked_side_effects(self) -> None:
        observed = [
            ROOT / "content/modernization/p04_candidate_manifest.json",
            ROOT / "content/modernization/p04_official_sources.json",
            ROOT / "content/modernization/p04_asset_sources.json",
            ROOT / "manifests/species_ids.csv",
            ROOT / "manifests/item_ids.csv",
            ROOT / "manifests/ability_ids.csv",
        ]
        before = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in observed}
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_modernization_p04_sources.py"), "--compact"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        report = json.loads(completed.stdout)
        self.assertEqual("PASS", report["status"])
        after = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in observed}
        self.assertEqual(before, after)


class ModernizationP04SourcesPureSafetyTest(unittest.TestCase):
    """外部checkoutが無いclean環境でもskipしない契約negative test。"""

    def test_missing_checkout_fails_closed_without_real_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "not-fetched"
            with self.assertRaisesRegex(P04SourceError, "固定asset sourceがありません"):
                audit_p04_sources(ROOT, source_root=missing, require_checkout=True)

    def test_missing_temporary_replacement_fails_without_real_checkout(self) -> None:
        candidate = json.loads(
            (ROOT / "content/modernization/p04_candidate_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        official = json.loads(
            (ROOT / "content/modernization/p04_official_sources.json").read_text(
                encoding="utf-8"
            )
        )
        candidate = copy.deepcopy(candidate)
        target = next(
            row for row in candidate["records"]
            if row["ability_status"] == "TEMPORARY_REPLACEABLE"
        )
        target["ability_replacement_key"] = None
        sources = _validate_official_sources(official)
        species, _ = _load_csv_keys(ROOT / "manifests/species_ids.csv", "species_key")
        items, _ = _load_csv_keys(ROOT / "manifests/item_ids.csv", "item_key")
        abilities, _ = _load_csv_keys(ROOT / "manifests/ability_ids.csv", "ability_key")
        with self.assertRaisesRegex(P04SourceError, "replacement key必須"):
            _validate_candidate_contract(
                candidate, sources, species, items, abilities,
            )


if __name__ == "__main__":
    unittest.main()
