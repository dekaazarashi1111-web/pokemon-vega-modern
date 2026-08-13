#!/usr/bin/env python3
"""T07 Vega Species extractorの固定ABIテスト。"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.engine.extract_vega_species import VegaSpeciesExtractionError, extract_vega_species


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/species_port.json"
ROM = ROOT / "build/reference/vega.gba"


@unittest.skipUnless(CONFIG.is_file() and ROM.is_file(), "T07 fixed Vega input unavailable")
class VegaSpeciesExtractorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.model = extract_vega_species(ROOT, cls.config)

    def test_exact_frozen_range_and_fields(self) -> None:
        self.assertEqual(self.model["count"], 412)
        self.assertEqual(self.model["ids"], list(range(412)))
        self.assertEqual(self.model["rows"][0]["display_name"], "？？？？？")
        self.assertEqual(self.model["rows"][1]["display_name"], "リープン")
        self.assertEqual(self.model["rows"][411]["display_name"], "シビルドン")
        for row in self.model["rows"]:
            stats = row["base_stats"]
            self.assertEqual(len(bytes.fromhex(row["raw_hex"])), 28)
            self.assertEqual(len(stats["ev_yield"]), 6)
            self.assertLess(stats["type1"], 18)
            self.assertLess(stats["type2"], 18)

    def test_pointer_and_hash_fail_closed(self) -> None:
        broken = copy.deepcopy(self.config)
        broken["vega"]["name_pointer"] += 4
        with self.assertRaisesRegex(VegaSpeciesExtractionError, "name root"):
            extract_vega_species(ROOT, broken)
        broken = copy.deepcopy(self.config)
        broken["vega"]["base_stats_sha256"] = "0" * 64
        with self.assertRaisesRegex(VegaSpeciesExtractionError, "BaseStats table"):
            extract_vega_species(ROOT, broken)


if __name__ == "__main__":
    unittest.main()
