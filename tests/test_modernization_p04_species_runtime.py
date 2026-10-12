from __future__ import annotations

import json
import struct
import unittest
from pathlib import Path

from tools.modernization_p04_species_runtime import (
    ABILITY_TABLE_KEYS,
    SPECIES_TABLE_KEYS,
    _lz77_decompress,
    _lz77_literal,
)


ROOT = Path(__file__).resolve().parents[1]


class SpeciesRuntimeStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = json.loads((ROOT / "config/modernization_p04_species_runtime.json").read_text(encoding="utf-8"))

    def test_scope_and_ids_are_fixed(self) -> None:
        ids = self.config["species_ids"]
        self.assertEqual((ids["old_count"], ids["new_count"]), (1621, 1670))
        self.assertEqual((ids["first_new_id"], ids["last_new_id"]), (1621, 1669))
        self.assertEqual(set(ids["excluded_record_keys"]), {
            "P04_SPECIES_BROWT", "P04_SPECIES_POMBON", "P04_SPECIES_GECQUA",
        })
        self.assertEqual(ids["battle_mega_hooks"], "OUT_OF_SCOPE_STAGE71")

    def test_table_surface_is_explicit(self) -> None:
        keys = [row["table_key"] for row in self.config["tables"]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), set(SPECIES_TABLE_KEYS + ABILITY_TABLE_KEYS))
        for required in (
            "species_front", "species_back", "species_palette", "species_shiny_palette",
            "species_icon", "species_icon_palette", "species_base_stats",
            "species_species_names", "species_front_coords", "species_back_coords",
            "species_elevation", "species_footprint", "species_cry", "species_cry2",
            "species_dex_entries", "species_national_dex", "species_national_dex_runtime",
            "species_level_up_pointers", "species_tmhm", "species_tutor",
            "species_wild_table", "acquisition_collection_defs", "evolution",
        ):
            self.assertIn(required, keys)

    def test_ability_rows_are_safe_and_replaceable(self) -> None:
        rows = self.config["ability_rows"]
        self.assertEqual([row["id"] for row in rows], list(range(312, 318)))
        self.assertEqual(len({row["localization_key"] for row in rows}), 6)
        self.assertTrue(all(row["name_ja"] and row["description_ja"] for row in rows))
        self.assertTrue(all(row["description_ja"] == "こうかは じゅんびちゅう。" for row in rows))
        self.assertTrue(all(row["rating"] == 0 and row["mold_breaker_ignored"] == 0 for row in rows))
        policy = self.config["ability_content_policy"]
        self.assertIn("PROVISIONAL_LOCALIZATION_REPLACEABLE", policy["localization_status"])
        self.assertEqual(policy["effect_hooks"], "OUT_OF_SCOPE_STAGE72")

    def test_literal_lz_roundtrip(self) -> None:
        for size in (32, 1024, 2048):
            raw = bytes((index * 73 + size) & 0xFF for index in range(size))
            encoded = _lz77_literal(raw)
            self.assertEqual(_lz77_decompress(encoded), raw)
            self.assertEqual(encoded[0], 0x10)
            self.assertEqual(encoded[1] | encoded[2] << 8 | encoded[3] << 16, size)
            self.assertEqual(len(encoded) % 4, 0)

    def test_derived_ability_consumers_are_explicit(self) -> None:
        derived = self.config["derived_pointer_consumers"]["sites"]
        bounds = self.config["ability_count_consumers"]["sites"]
        self.assertEqual([row["site"] for row in derived], [0x13CDD10, 0x13CFD30, 0x13D1EE0])
        self.assertTrue(all(row["table_key"] == "ability_descriptions" and row["transform"] == "ADDRESS_RIGHT_SHIFT_2" for row in derived))
        self.assertEqual([row["site"] for row in bounds], [0x13CDCC8, 0x13CFCE8, 0x13D1E98])
        self.assertTrue(all((row["old_hex"], row["new_hex"]) == ("9c23", "9f23") for row in bounds))
        count_sites = self.config["count_consumers"]["sites"]
        self.assertEqual(len(count_sites), 19)
        self.assertTrue({0x73E08, 0x73ED8, 0x73F38, 0x18C35C} <= {row["site"] for row in count_sites})


class SpeciesRuntimeGeneratedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / "config/modernization_p04_species_runtime.json").read_text(encoding="utf-8"))
        metadata_path = ROOT / cls.config["outputs"]["metadata"]
        if not metadata_path.is_file():
            raise unittest.SkipTest("Stage70 generated metadataがありません")
        cls.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        cls.parent = (ROOT / cls.config["inputs"]["rom"]["path"]).read_bytes()
        cls.rom = (ROOT / cls.config["outputs"]["rom"]).read_bytes()

    def test_all_rows_and_prefixes(self) -> None:
        self.assertEqual(len(self.metadata["species"]["records"]), 49)
        self.assertEqual([row["id"] for row in self.metadata["species"]["records"]], list(range(1621, 1670)))
        self.assertEqual(self.metadata["vertical_slice"]["status"], "PASS_BEFORE_BULK_EXPANSION")
        for key, table in self.metadata["tables"].items():
            old = self.parent[table["old_file_offset"]:table["old_file_offset"] + table["old_size"]]
            new = self.rom[table["new_file_offset"]:table["new_file_offset"] + table["old_size"]]
            self.assertEqual(new, old, key)
            self.assertEqual(table["existing_prefix_sha256"], table["old_sha256"])

    def test_evolution_interface_for_stage71(self) -> None:
        table = self.metadata["tables"]["evolution"]
        self.assertEqual((table["old_count"], table["new_count"], table["stride"]), (1621, 1670, 128))
        start = table["new_file_offset"] + table["old_size"]
        self.assertEqual(self.rom[start:start + 49 * 128], bytes(49 * 128))
        self.assertEqual(table["pointer_consumers"]["count"], 39)
        self.assertEqual(len(table["pointer_consumers"]["rows"]), 39)

    def test_ability_table_interface_for_stage71_and_72(self) -> None:
        runtime = self.metadata["ability_runtime"]
        self.assertEqual((runtime["old_count"], runtime["new_count"]), (312, 318))
        self.assertEqual(runtime["effect_runtime_status"], "EFFECT_RUNTIME_PENDING_STAGE72")
        self.assertIn("PROVISIONAL_LOCALIZATION_REPLACEABLE", runtime["localization_status"])
        for key in ABILITY_TABLE_KEYS:
            table = self.metadata["tables"][key]
            self.assertEqual((table["old_count"], table["new_count"]), (312, 318))
            self.assertGreater(table["pointer_consumers"]["count"], 0)
        descriptions = self.metadata["tables"]["ability_descriptions"]
        self.assertEqual(descriptions["pointer_consumers"]["derived_count"], 3)
        for site in descriptions["pointer_consumers"]["derived_site_offsets"]:
            self.assertEqual(struct.unpack_from("<I", self.rom, site)[0], descriptions["new_address"] >> 2)
        self.assertEqual(len(self.metadata["ability_count_consumers"]["rows"]), 3)
        for row in self.metadata["ability_count_consumers"]["rows"]:
            self.assertEqual(self.rom[row["site_offset"]:row["site_offset"] + 2], bytes.fromhex("9f23"))

    def test_species_1029_and_all_existing_bytes_are_preserved(self) -> None:
        for key in SPECIES_TABLE_KEYS:
            table = self.metadata["tables"][key]
            if table["old_count"] <= 1029:
                continue
            stride = table["stride"]
            old_start = table["old_file_offset"] + 1029 * stride
            new_start = table["new_file_offset"] + 1029 * stride
            self.assertEqual(self.parent[old_start:old_start + stride], self.rom[new_start:new_start + stride], key)

    def test_shifted_root_and_count_audits_have_no_unknown_executable_candidate(self) -> None:
        audits = self.metadata["consumer_audits"]
        shifted = audits["shifted_roots"]
        self.assertEqual(shifted["unallowlisted_literal_referenced_sites"], [])
        self.assertEqual(shifted["confirmed_semantic_site_offsets"], [0x13CDD10, 0x13CFD30, 0x13D1EE0])
        counts = audits["species_count_literals"]
        self.assertEqual(counts["unresolved_executable_candidates"], [])
        self.assertEqual(len(self.metadata["count_consumers"]["rows"]), 19)

    def test_base_stats_ability_references_are_in_318_row_range(self) -> None:
        table = self.metadata["tables"]["species_base_stats"]
        for record in self.metadata["species"]["records"]:
            start = table["new_file_offset"] + record["id"] * table["stride"]
            row = self.rom[start:start + table["stride"]]
            self.assertEqual(tuple(row[:6]), tuple(record["stats"]))
            self.assertEqual(tuple(row[6:8]), tuple(record["type_ids"]))
            self.assertTrue(all(struct.unpack_from("<H", row, offset)[0] == record["ability_id"] for offset in (22, 26, 28)))
            self.assertLess(record["ability_id"], 318)


if __name__ == "__main__":
    unittest.main()
