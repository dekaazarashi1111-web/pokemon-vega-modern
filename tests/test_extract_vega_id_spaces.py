#!/usr/bin/env python3
"""固定rootに基づくVega Type/Ability/Item extractorのfocused tests。"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.engine.extract_vega_id_spaces import (
    ABILITY_COUNT,
    ITEM_COUNT,
    TYPE_COUNT,
    VegaIdSpaceExtractionError,
    default_policy,
    extract_vega_id_spaces,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = REPO_ROOT / "build/reference/vega.gba"
CHARMAP_PATH = REPO_ROOT / "vendor/upstream/CFRU-JP/charmap.tbl"


@unittest.skipUnless(ROM_PATH.is_file(), "fixed Vega reference ROM is unavailable")
class FixedVegaIdSpaceExtractionTests(unittest.TestCase):
    result: dict[str, object]

    @classmethod
    def setUpClass(cls) -> None:
        cls.result = extract_vega_id_spaces(REPO_ROOT)

    def test_exact_top_level_schema_counts_and_frozen_ids(self) -> None:
        self.assertEqual(
            set(self.result),
            {"metadata", "types", "abilities", "items", "type_effectiveness"},
        )
        self.assertEqual(self.result["metadata"]["schema_version"], 1)
        self.assertEqual([row["id"] for row in self.result["types"]], list(range(TYPE_COUNT)))
        self.assertEqual(
            [row["id"] for row in self.result["abilities"]], list(range(ABILITY_COUNT))
        )
        self.assertEqual([row["id"] for row in self.result["items"]], list(range(ITEM_COUNT)))
        self.assertEqual(
            self.result["metadata"]["counts"],
            {
                "types": 18,
                "abilities": 78,
                "item_slots": 375,
                "defined_items_excluding_none": 307,
                "unused_item_slots": 67,
                "type_effectiveness_semantic_entries": 110,
            },
        )

    def test_public_row_fields_are_stable_and_json_compatible(self) -> None:
        self.assertEqual(
            set(self.result["types"][0]),
            {
                "id",
                "name_raw",
                "name_decoded",
                "normalized_name",
                "name_encoded_length",
                "name_line_encoded_widths",
                "display_icon_index",
                "display_icon_width",
                "display_icon_height",
                "display_icon_tile_offset",
                "display_icon_raw",
                "evidence",
            },
        )
        self.assertEqual(
            set(self.result["abilities"][0]),
            {
                "id",
                "name_raw",
                "name_decoded",
                "normalized_name",
                "name_encoded_length",
                "name_line_encoded_widths",
                "description_raw",
                "description_decoded",
                "description_encoded_length",
                "description_line_encoded_widths",
                "evidence",
            },
        )
        self.assertEqual(
            set(self.result["items"][0]),
            {
                "id",
                "item_id",
                "slot_state",
                "name_raw",
                "name_decoded",
                "normalized_name",
                "name_encoded_length",
                "name_line_encoded_widths",
                "price",
                "hold_effect",
                "hold_effect_param",
                "description_pointer",
                "description_raw",
                "description_decoded",
                "description_encoded_length",
                "description_line_encoded_widths",
                "importance",
                "registrability",
                "pocket",
                "field_use_type",
                "field_callback_pointer",
                "battle_usage",
                "battle_callback_pointer",
                "secondary_id",
                "icon_pointer",
                "palette_pointer",
                "icon_entry_raw",
                "raw_hex",
                "evidence",
            },
        )
        self.assertEqual(
            set(self.result["type_effectiveness"][0]),
            {
                "attacking_type_id",
                "defending_type_id",
                "multiplier_tenths",
                "foresight_bypassable",
                "raw_entry_index",
                "raw_hex",
            },
        )
        # A successful result must need no custom JSON encoder.
        json.dumps(self.result, ensure_ascii=False, sort_keys=True)

    def test_all_tables_are_hash_and_pointer_rooted(self) -> None:
        expected = {
            "type_effectiveness": (0x0820BF24, 112, 3, 9),
            "type_names": (0x0820C074, 18, 5, 5),
            "type_display_icons": (0x08411AFC, 24, 4, 1),
            "ability_names": (0x0820C274, 78, 8, 4),
            "ability_descriptions": (0x0820C4E4, 78, 19, 2),
            "items": (0x083A06F8, 375, 40, 15),
            "item_icons": (0x0839C79C, 376, 8, 3),
        }
        tables = self.result["metadata"]["tables"]
        self.assertEqual(set(tables), set(expected))
        for name, (address, count, record_size, pointer_count) in expected.items():
            table = tables[name]
            self.assertEqual((table["address"], table["count"], table["record_size"]), (address, count, record_size))
            self.assertEqual(table["end_address_exclusive"], address + count * record_size)
            self.assertEqual(len(table["sha256"]), 64)
            self.assertEqual(len(table["pointer_sites"]), pointer_count)
            self.assertTrue(all(row["target_address"] == address for row in table["pointer_sites"]))
        self.assertEqual(tables["type_effectiveness"]["end_address_exclusive"], tables["type_names"]["address"])
        self.assertEqual(tables["ability_names"]["end_address_exclusive"], tables["ability_descriptions"]["address"])
        self.assertEqual(tables["item_icons"]["frozen_item_icon_count"], 375)
        self.assertEqual(tables["item_icons"]["extra_ui_entry_count"], 1)
        self.assertEqual(
            self.result["metadata"]["roots"],
            {
                "type_display_palette": {
                    "address": 0x08411B7C,
                    "pointer_sites": [
                        {"site_address": 0x08108868, "target_address": 0x08411B7C}
                    ],
                },
                "type_display_tiles": {
                    "address": 0x08411B9C,
                    "pointer_sites": [
                        {"site_address": 0x081088B4, "target_address": 0x08411B9C}
                    ],
                },
            },
        )

    def test_type_names_and_id_plus_one_display_icon_mapping(self) -> None:
        types = self.result["types"]
        self.assertEqual(types[0]["name_raw"], "69ae6f79ff")
        self.assertEqual(types[0]["name_decoded"], "ノーマル")
        self.assertEqual(types[9]["name_decoded"], "？？？")
        self.assertEqual(types[17]["name_decoded"], "あく")
        for row in types:
            self.assertEqual(row["display_icon_index"], row["id"] + 1)
            self.assertEqual((row["display_icon_width"], row["display_icon_height"]), (30, 12))
        self.assertEqual(types[0]["display_icon_tile_offset"], 0x20)
        self.assertEqual(types[16]["display_icon_tile_offset"], 0xA0)
        self.assertEqual(types[17]["display_icon_tile_offset"], 0x8C)

    def test_type_effectiveness_is_losslessly_normalized(self) -> None:
        rows = self.result["type_effectiveness"]
        boundary = self.result["metadata"]["tables"]["type_effectiveness"]["boundary_evidence"]
        self.assertEqual(
            boundary,
            {
                "raw_entry_count": 112,
                "semantic_entry_count": 110,
                "foresight_marker_index": 108,
                "terminator_index": 111,
                "default_multiplier_tenths": 10,
                "normalization": "marker and terminator removed; post-marker rows tagged foresight_bypassable",
            },
        )
        lookup = {
            (row["attacking_type_id"], row["defending_type_id"], row["foresight_bypassable"]): row
            for row in rows
        }
        self.assertEqual(lookup[(0, 5, False)]["multiplier_tenths"], 5)
        self.assertEqual(lookup[(13, 4, False)]["multiplier_tenths"], 0)
        self.assertEqual(lookup[(0, 7, True)]["multiplier_tenths"], 0)
        self.assertEqual(lookup[(1, 7, True)]["multiplier_tenths"], 0)
        self.assertFalse(any(row["multiplier_tenths"] == 10 for row in rows))

        # The normalized rows retain source order, so the exact 3-byte ABI can be rebuilt.
        reconstructed = bytearray()
        for row in rows:
            if row["raw_entry_index"] == boundary["foresight_marker_index"] + 1:
                reconstructed.extend(b"\xFE\xFE\x00")
            reconstructed.extend(bytes.fromhex(row["raw_hex"]))
        reconstructed.extend(b"\xFF\xFF\x00")
        self.assertEqual(len(reconstructed), 112 * 3)
        self.assertEqual(
            hashlib.sha256(reconstructed).hexdigest(),
            self.result["metadata"]["tables"]["type_effectiveness"]["sha256"],
        )

    def test_vega_ability_identity_changes_and_air_lock_slot_are_frozen(self) -> None:
        abilities = self.result["abilities"]
        self.assertEqual(abilities[24]["name_decoded"], "きずつけボディ")
        self.assertEqual(abilities[24]["description_decoded"], "さわった あいてを キズつける")
        self.assertEqual(abilities[59]["name_decoded"], "てんきや")
        self.assertIn("テルテン", abilities[59]["description_decoded"])
        self.assertEqual(abilities[76]["name_decoded"], "そうおん")
        self.assertEqual(abilities[77]["name_decoded"], "エアロック")
        self.assertEqual(self.result["metadata"]["encoded_widths"]["ability_name_max"], 7)
        self.assertEqual(self.result["metadata"]["encoded_widths"]["ability_description_max"], 18)

    def test_item_struct_keeps_all_semantic_fields_and_custom_rows(self) -> None:
        items = self.result["items"]
        row = items[218]
        self.assertEqual(
            (
                row["item_id"],
                row["name_decoded"],
                row["price"],
                row["hold_effect"],
                row["hold_effect_param"],
                row["pocket"],
                row["field_use_type"],
                row["field_callback_pointer"],
                row["battle_usage"],
                row["battle_callback_pointer"],
                row["secondary_id"],
            ),
            (218, "アップグレード", 100, 60, 60, 1, 4, 0x080A34F9, 0, 0, 0),
        )
        self.assertEqual(row["icon_pointer"], 0x08D8FC5C)
        self.assertEqual(row["palette_pointer"], 0x08D8FD18)
        self.assertIn("ノーマルタイプ", row["description_decoded"])
        self.assertEqual(items[225]["name_decoded"], "フラフラフープ")
        self.assertIn("パッチール", items[225]["description_decoded"])
        self.assertEqual(items[374]["name_decoded"], "シリウス")

        # raw_hex is the exact 40-byte ABI, not a lossy field-only rendering.
        raw = bytes.fromhex(row["raw_hex"])
        self.assertEqual(len(raw), 40)
        self.assertEqual(int.from_bytes(raw[10:12], "little"), row["item_id"])
        self.assertEqual(int.from_bytes(raw[24:28], "little"), row["field_callback_pointer"])
        self.assertEqual(int.from_bytes(raw[32:36], "little"), row["battle_callback_pointer"])

    def test_unused_item_slots_are_frozen_instead_of_reused(self) -> None:
        items = self.result["items"]
        unused = [row["id"] for row in items if row["slot_state"] == "unused"]
        self.assertEqual(
            unused,
            [
                *range(52, 63),
                72,
                82,
                *range(87, 93),
                *range(99, 103),
                105,
                *range(112, 121),
                *range(176, 179),
                *range(226, 254),
                267,
                347,
                348,
            ],
        )
        self.assertEqual(items[0]["slot_state"], "none")
        self.assertTrue(all(row["item_id"] in (0, row["id"]) for row in items))

    def test_encoded_widths_cover_names_and_multiline_item_descriptions(self) -> None:
        widths = self.result["metadata"]["encoded_widths"]
        self.assertEqual(
            (widths["type_name_min"], widths["type_name_max"]),
            (2, 4),
        )
        self.assertEqual((widths["item_name_min"], widths["item_name_max"]), (2, 8))
        self.assertEqual((widths["item_description_min"], widths["item_description_max"]), (5, 49))
        self.assertEqual(widths["item_description_line_max"], 16)
        self.assertEqual(widths["item_description_line_count_max"], 4)
        self.assertEqual(self.result["items"][13]["description_line_encoded_widths"], [14, 13, 12])

    def test_default_and_config_vega_section_policies_match(self) -> None:
        defaults = default_policy()
        flat_vega = {
            "rom_path": defaults["rom"]["logical_path"],
            "rom_size": defaults["rom"]["size"],
            "rom_sha256": defaults["rom"]["sha256"],
            "frozen_type_count": 18,
            "frozen_ability_count": 78,
            "frozen_item_count": 375,
        }
        direct = extract_vega_id_spaces(REPO_ROOT, flat_vega)
        full_config = extract_vega_id_spaces(
            REPO_ROOT,
            {
                "schema_version": 1,
                "vega": flat_vega,
                "charmap": {
                    "path": defaults["charmap"]["logical_path"],
                    "sha256": defaults["charmap"]["sha256"],
                },
                "unrelated_build_section": {"ignored": True},
            },
        )
        canonical = json.dumps(self.result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(json.dumps(direct, ensure_ascii=False, sort_keys=True, separators=(",", ":")), canonical)
        self.assertEqual(json.dumps(full_config, ensure_ascii=False, sort_keys=True, separators=(",", ":")), canonical)

    def test_output_is_deterministic_and_sanitized(self) -> None:
        again = extract_vega_id_spaces(REPO_ROOT, default_policy())
        first = json.dumps(self.result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        second = json.dumps(again, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(first, second)
        self.assertNotIn(str(REPO_ROOT), first)
        self.assertNotIn("timestamp", first.lower())

    def test_wrong_rom_hash_and_frozen_count_are_rejected(self) -> None:
        policy = default_policy()
        policy["rom"]["sha256"] = "00" * 32
        with self.assertRaisesRegex(VegaIdSpaceExtractionError, "ROM sha256 mismatch"):
            extract_vega_id_spaces(REPO_ROOT, policy)
        flat = {
            "rom_path": "build/reference/vega.gba",
            "rom_size": 16_777_216,
            "rom_sha256": default_policy()["rom"]["sha256"],
            "frozen_type_count": 19,
            "frozen_ability_count": 78,
            "frozen_item_count": 375,
        }
        with self.assertRaisesRegex(VegaIdSpaceExtractionError, "frozen_type_count must be 18"):
            extract_vega_id_spaces(REPO_ROOT, flat)

    def test_bad_actual_pointer_is_rejected_even_with_matching_rom_hash(self) -> None:
        mutated = bytearray(ROM_PATH.read_bytes())
        pointer_site = 0x0809A2E4 - 0x08000000
        mutated[pointer_site : pointer_site + 4] = (0x0839C79C).to_bytes(4, "little")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "vega.gba").write_bytes(mutated)
            (root / "charmap.tbl").write_bytes(CHARMAP_PATH.read_bytes())
            policy = default_policy()
            policy["rom"].update(
                {"logical_path": "vega.gba", "sha256": hashlib.sha256(mutated).hexdigest()}
            )
            policy["charmap"]["logical_path"] = "charmap.tbl"
            with self.assertRaisesRegex(VegaIdSpaceExtractionError, "items pointer mismatch"):
                extract_vega_id_spaces(root, policy)

    def test_cli_emits_the_same_fixed_json_contract(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "tools/engine/extract_vega_id_spaces.py"),
                "--root",
                str(REPO_ROOT),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        parsed = json.loads(completed.stdout)
        self.assertEqual(parsed["metadata"]["counts"]["item_slots"], 375)
        self.assertEqual(parsed["metadata"]["rom"]["logical_path"], "build/reference/vega.gba")


if __name__ == "__main__":
    unittest.main()
