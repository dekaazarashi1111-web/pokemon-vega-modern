from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from tools.engine import cfru_id_space_inventory as inventory


ROOT = Path(__file__).resolve().parents[1]


class CFRUIdSpaceInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = inventory.extract_cfru_id_spaces(ROOT)

    def test_top_level_contract_counts_and_determinism(self) -> None:
        second = inventory.extract_cfru_id_spaces(ROOT)
        self.assertEqual(self.model, second)
        self.assertEqual(
            list(self.model), ["metadata", "types", "abilities", "items", "aliases"]
        )
        self.assertEqual(
            self.model["metadata"]["counts"],
            {"types": 25, "abilities": 311, "items": 774},
        )
        self.assertEqual(len(self.model["types"]), 25)
        self.assertEqual(len(self.model["abilities"]), 311)
        self.assertEqual(len(self.model["items"]), 774)
        self.assertEqual([row["id"] for row in self.model["types"]], list(range(25)))
        self.assertEqual([row["id"] for row in self.model["abilities"]], list(range(311)))
        self.assertEqual([row["id"] for row in self.model["items"]], list(range(774)))
        self.assertRegex(
            self.model["metadata"]["inventory_sha256"], r"^[0-9a-f]{64}$"
        )

    def test_fixed_source_and_t01_baseline_hashes_are_recorded(self) -> None:
        metadata = self.model["metadata"]
        self.assertEqual(
            metadata["sources"]["cfru"]["commit"],
            "e24a16fe39e27ae162faf5b78596d1f3df18489d",
        )
        self.assertEqual(
            metadata["sources"]["dpe"]["commit"],
            "10ff98c85ebf37ab5cb39a41b6e9b50f06efb19e",
        )
        self.assertRegex(
            metadata["sources"]["cfru"]["source_bundle_sha256"], r"^[0-9a-f]{64}$"
        )
        self.assertEqual(
            metadata["sources"]["cfru"]["source_bundle_sha256"],
            "34b3f2bb10780da2108e2c52d3d33faf9ed23cde642ca0f66f48b3bb4a9d3a61",
        )
        self.assertRegex(
            metadata["sources"]["dpe"]["source_bundle_sha256"], r"^[0-9a-f]{64}$"
        )
        baseline = metadata["t01_baseline"]
        self.assertEqual(baseline["report_identity"], "SEMANTIC_CONTRACT_V1")
        self.assertRegex(baseline["report_contract_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            baseline["fingerprint"],
            "feb30b4f3b3f6324260af767096293c4fc6de79c8cf32334d720e13767a77633",
        )
        self.assertEqual(
            baseline["rom_sha256"],
            "140aa67a38046bcbf3d211550d900929039a4e7c41e55572f9503b6f27d71922",
        )
        self.assertEqual(baseline["rom_size"], 32 * 1024 * 1024)
        self.assertEqual(baseline["symbols"]["gItemData"], "0x090FAAE4")

    def test_t01_contract_excludes_observational_build_fields(self) -> None:
        report = {
            "schema_version": 1,
            "fingerprint": "a" * 64,
            "sources": {"cfru": {"commit": "c", "tree": "t"}},
            "repeatability": {"status": "PASS", "independent_builds_per_variant": 2},
            "builds": [],
        }
        build = {
            "engine": "cfru",
            "profile": "baseline",
            "run": 1,
            "source_commit": "c",
            "source_tree": "t",
            "output_sha256": "b" * 64,
            "elapsed_seconds": 1.25,
            "cache_reused": False,
            "artifact_dir": "build/one",
            "log": "build/one/build.log",
        }
        report["builds"].append(build)
        observed_report = copy.deepcopy(report)
        observed_again = copy.deepcopy(build)
        observed_again.update(
            {
                "elapsed_seconds": 99.0,
                "cache_reused": True,
                "artifact_dir": "build/two",
                "log": "build/two/build.log",
            }
        )
        observed_report["builds"] = [observed_again]
        self.assertEqual(
            inventory._t01_report_contract_sha256(report),
            inventory._t01_report_contract_sha256(observed_report),
        )
        changed_report = copy.deepcopy(report)
        changed_output = copy.deepcopy(build)
        changed_output["output_sha256"] = "d" * 64
        changed_report["builds"] = [changed_output]
        self.assertNotEqual(
            inventory._t01_report_contract_sha256(report),
            inventory._t01_report_contract_sha256(changed_report),
        )

    def test_type_rows_contain_complete_compiled_and_logical_matrix(self) -> None:
        types = self.model["types"]
        self.assertTrue(all(len(row["effectiveness"]) == 25 for row in types))
        self.assertTrue(all(len(row["effectiveness_raw"]) == 25 for row in types))
        self.assertEqual(len([row["display_color"] for row in types]), 25)
        self.assertTrue(
            all(
                set(row["display_color"]) == {"r", "g", "b", "bgr555"}
                for row in types
            )
        )
        self.assertEqual(types[23]["symbol"], "TYPE_FAIRY")
        self.assertEqual(types[23]["name_ja"], "フェアリー")
        self.assertEqual(
            types[23]["display_color"],
            {"r": 29, "g": 17, "b": 25, "bgr555": 29 | (17 << 5) | (25 << 10)},
        )
        self.assertEqual(
            types[23]["source_refs"]["display_color"],
            {"path": "src/terastal.c", "line": 65, "symbol": "sTeraTypeColor[23]"},
        )
        self.assertEqual(types[1]["effectiveness"][23], 500)
        self.assertEqual(types[16]["effectiveness"][23], 1)
        self.assertEqual(types[23]["effectiveness"][16], 2000)
        self.assertEqual(types[0]["effectiveness_raw"][0], 0)
        self.assertEqual(types[0]["effectiveness"][0], 1000)
        self.assertEqual(types[24]["symbol"], "TYPE_STELLAR")
        self.assertIsNone(types[24]["name_ja"])
        self.assertEqual(types[24]["status"], "MISSING_UPSTREAM_NAME")
        self.assertEqual(types[24]["move_menu_icon"]["tile_offset"], 0xE4)
        self.assertEqual(
            types[24]["display_color"],
            {"r": 31, "g": 31, "b": 31, "bgr555": 0x7FFF},
        )
        self.assertEqual(types[24]["source_refs"]["display_color"]["line"], 66)

    def test_tera_color_table_missing_or_invalid_entry_fails_closed(self) -> None:
        source = (ROOT / "vendor/upstream/CFRU-JP/src/terastal.c").read_text(
            encoding="utf-8"
        )
        rows = inventory._parse_tera_type_colors(source, "src/terastal.c", 25)
        self.assertEqual(len(rows), 25)
        missing = source.replace("RGB(21, 21, 15),", "", 1)
        with self.assertRaisesRegex(ValueError, "count changed: 24 != 25"):
            inventory._parse_tera_type_colors(missing, "src/terastal.c", 25)
        invalid = source.replace("RGB(21, 21, 15)", "RGB(32, 21, 15)", 1)
        with self.assertRaisesRegex(ValueError, "outside RGB5 range"):
            inventory._parse_tera_type_colors(invalid, "src/terastal.c", 25)

    def test_ability_rows_join_symbol_japanese_text_description_and_rating(self) -> None:
        expected_fields = {
            "id",
            "symbol",
            "canonical_key",
            "name_ja",
            "description_ja",
            "rating",
            "description_symbol",
            "description_rom_address",
            "source_refs",
        }
        self.assertEqual(set(self.model["abilities"][0]), expected_fields)
        stench = self.model["abilities"][1]
        self.assertEqual(stench["symbol"], "ABILITY_STENCH")
        self.assertEqual(stench["name_ja"], "あくしゅう")
        self.assertEqual(stench["description_ja"], "ポケモンが よりつき にくくなる")
        self.assertEqual(stench["rating"], 1)
        last = self.model["abilities"][310]
        self.assertEqual(last["symbol"], "ABILITY_POISONPUPPETEER")
        self.assertEqual(last["name_ja"], "どくくぐつ")
        self.assertEqual(last["rating"], 4)
        self.assertTrue(last["description_ja"])

    def test_item_rows_expose_logical_fields_icons_palettes_and_callbacks(self) -> None:
        expected_fields = {
            "id",
            "symbol",
            "canonical_key",
            "name_ja",
            "description_ja",
            "table_item_symbol",
            "compiled_item_id",
            "price",
            "hold_effect",
            "hold_effect_symbol",
            "hold_effect_param",
            "description_symbol",
            "description_rom_address",
            "importance",
            "mystery",
            "pocket",
            "pocket_symbol",
            "use_type",
            "use_type_symbol",
            "field_callback_symbol",
            "field_callback_address",
            "battle_usage",
            "battle_callback_symbol",
            "battle_callback_address",
            "secondary_id",
            "icon_symbol",
            "palette_symbol",
            "icon_rom_address",
            "palette_rom_address",
            "item_type_id",
            "item_type_key",
            "item_type_explicit",
            "item_type_source_ref",
            "is_evolution_stone",
            "is_evolution_item",
            "source_refs",
        }
        self.assertEqual(set(self.model["items"][0]), expected_fields)
        master_ball = self.model["items"][1]
        self.assertEqual(master_ball["symbol"], "ITEM_MASTER_BALL")
        self.assertEqual(master_ball["name_ja"], "マスターボール")
        self.assertEqual(master_ball["battle_usage"], 2)
        self.assertEqual(master_ball["battle_callback_symbol"], "gFieldFunc_Pokeballs")
        self.assertRegex(master_ball["battle_callback_address"], r"^0x[0-9A-F]{8}$")
        self.assertEqual(master_ball["icon_symbol"], "gItemIcon_MasterBallTiles")
        self.assertEqual(master_ball["palette_symbol"], "gItemIcon_MasterBallPal")

        capsule = self.model["items"][0x2D8]
        self.assertEqual(capsule["name_ja"], "とくせいカプセル")
        self.assertEqual(capsule["hold_effect_symbol"], "ITEM_EFFECT_ABILITY_CAPSULE")
        self.assertEqual(capsule["field_callback_symbol"], "FieldUseFunc_AbilityCapsule")
        self.assertRegex(capsule["field_callback_address"], r"^0x[0-9A-F]{8}$")
        self.assertTrue(capsule["description_ja"])

        serious_mint = self.model["items"][773]
        self.assertEqual(serious_mint["symbol"], "ITEM_SERIOUS_MINT")
        self.assertEqual(serious_mint["field_callback_symbol"], "FieldUseFunc_NatureMint")
        self.assertRegex(serious_mint["icon_rom_address"], r"^0x[0-9A-F]{8}$")
        self.assertRegex(serious_mint["palette_rom_address"], r"^0x[0-9A-F]{8}$")

    def test_item_type_and_evolution_sets_are_complete(self) -> None:
        contract = self.model["metadata"]["item_type_contract"]
        self.assertEqual(
            {
                key: contract[key]
                for key in (
                    "definition_count",
                    "explicit_item_count",
                    "evolution_stone_count",
                    "evolution_item_count",
                )
            },
            {
                "definition_count": 63,
                "explicit_item_count": 465,
                "evolution_stone_count": 12,
                "evolution_item_count": 40,
            },
        )
        self.assertEqual(
            [row["id"] for row in contract["definitions"]], list(range(63))
        )
        stones = [row for row in self.model["items"] if row["is_evolution_stone"]]
        evolution_items = [row for row in self.model["items"] if row["is_evolution_item"]]
        self.assertEqual(len(stones), 12)
        self.assertEqual(len(evolution_items), 40)
        self.assertEqual(
            {row["symbol"] for row in stones},
            {
                "ITEM_SUN_STONE",
                "ITEM_MOON_STONE",
                "ITEM_FIRE_STONE",
                "ITEM_THUNDER_STONE",
                "ITEM_WATER_STONE",
                "ITEM_LEAF_STONE",
                "ITEM_DAWN_STONE",
                "ITEM_DUSK_STONE",
                "ITEM_SHINY_STONE",
                "ITEM_ICE_STONE",
                "ITEM_OVAL_STONE",
                "ITEM_LINK_CABLE",
            },
        )
        self.assertIn("ITEM_KINGS_ROCK", {row["symbol"] for row in evolution_items})
        self.assertIn(
            "ITEM_UNREMARKABLE_TEACUP", {row["symbol"] for row in evolution_items}
        )
        everstone = self.model["items"][195]
        self.assertEqual(everstone["item_type_key"], "ITEM_TYPE_EVOLUTION_ITEM")
        self.assertTrue(everstone["is_evolution_item"])
        self.assertNotEqual(everstone["hold_effect"], 0)
        master_ball = self.model["items"][1]
        self.assertEqual(master_ball["item_type_key"], "ITEM_TYPE_DEFAULT_0")
        self.assertFalse(master_ball["item_type_explicit"])

    def test_item_type_parser_fails_closed(self) -> None:
        enum_text = (ROOT / "vendor/upstream/CFRU-JP/include/new/item.h").read_text(
            encoding="utf-8"
        )
        table_text = (
            ROOT / "vendor/upstream/CFRU-JP/src/Tables/item_tables.c"
        ).read_text(encoding="utf-8")
        constants, _ = inventory._parse_constants(
            (
                ROOT / "vendor/upstream/CFRU-JP/include/constants/items.h"
            ).read_text(encoding="utf-8"),
            "include/constants/items.h",
            "ITEM_",
        )
        broken = table_text.replace(
            "[ITEM_SUN_STONE] = ITEM_TYPE_EVOLUTION_STONE,", "", 1
        )
        with self.assertRaisesRegex(ValueError, "explicit count changed"):
            inventory._parse_item_types(
                enum_text=enum_text,
                enum_path="include/new/item.h",
                table_text=broken,
                table_path="src/Tables/item_tables.c",
                item_constants=constants,
                expected_count=774,
            )

    def test_aliases_and_fixed_placeholder_anomaly_are_explicit(self) -> None:
        aliases = self.model["aliases"]
        self.assertEqual(len(aliases), 53)
        by_symbol = {row["symbol"]: row for row in aliases}
        self.assertEqual(
            by_symbol["ITEM_ENIGMA_BERRY"]["target_symbol"],
            "ITEM_ENIGMA_BERRY_OLD",
        )
        self.assertEqual(
            (by_symbol["ITEM_TM02_DRAGON_CLAW"]["id"], by_symbol["ITEM_TM02_DRAGON_CLAW"]["target_symbol"]),
            (290, "ITEM_TM02"),
        )
        self.assertEqual(
            (by_symbol["ITEM_HM05_FLASH"]["id"], by_symbol["ITEM_HM05_FLASH"]["target_symbol"]),
            (343, "ITEM_HM05_DIVE"),
        )
        self.assertEqual(
            {row["source_ref"]["path"] for row in aliases},
            {"include/constants/items.h", "include/constants/tmshms.h"},
        )
        self.assertEqual(
            self.model["metadata"]["anomalies"],
            [
                {
                    "kind": "ITEM_TABLE_IDENTITY_MISMATCH",
                    "id": 375,
                    "canonical_symbol": "ITEM_X_SP_DEF",
                    "table_symbol": "ITEM_NONE",
                    "compiled_item_id": 0,
                }
            ],
        )

    def test_default_policy_is_isolated_and_wrapped_cfru_policy_is_accepted(self) -> None:
        first = inventory.default_policy()
        second = inventory.default_policy()
        first["expected_counts"]["types"] = 999
        self.assertEqual(second["expected_counts"]["types"], 25)
        wrapped = inventory.extract_cfru_id_spaces(ROOT, {"cfru": second})
        self.assertEqual(
            wrapped["metadata"]["inventory_sha256"],
            self.model["metadata"]["inventory_sha256"],
        )
        config = json.loads((ROOT / "config/id_spaces.json").read_text(encoding="utf-8"))
        configured = inventory.extract_cfru_id_spaces(ROOT, config)
        self.assertEqual(
            configured["metadata"]["inventory_sha256"],
            self.model["metadata"]["inventory_sha256"],
        )

    def test_wrong_baseline_hash_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "baseline ROM hash differs from policy"):
            inventory.extract_cfru_id_spaces(
                ROOT, {"expected_baseline_sha256": "0" * 64}
            )

    def test_wrong_source_bundle_hash_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "cfru source bundle hash differs from policy"):
            inventory.extract_cfru_id_spaces(
                ROOT,
                {
                    "expected_source_bundle_sha256": {
                        "cfru": "0" * 64,
                        "dpe": inventory.default_policy()["expected_source_bundle_sha256"][
                            "dpe"
                        ],
                    }
                },
            )

    def test_cli_prints_json_without_writing_artifacts(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/engine/cfru_id_space_inventory.py"),
                "--root",
                str(ROOT),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        decoded = json.loads(completed.stdout)
        self.assertEqual(decoded["metadata"]["counts"], self.model["metadata"]["counts"])
        self.assertEqual(
            decoded["metadata"]["inventory_sha256"],
            self.model["metadata"]["inventory_sha256"],
        )
        encoded = completed.stdout
        self.assertNotIn(str(ROOT), encoded)
        self.assertNotIn("generated_at", encoded)


if __name__ == "__main__":
    unittest.main()
