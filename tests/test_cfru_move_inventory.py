from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.engine import cfru_move_inventory as inventory


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor/upstream/CFRU-JP"


class CFRUMoveInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = inventory.build_cfru_move_inventory(ROOT, SOURCE)

    def test_fixed_source_is_complete_and_deterministic(self) -> None:
        second = inventory.build_cfru_move_inventory(ROOT, SOURCE)
        self.assertEqual(self.model, second)
        self.assertEqual(
            list(self.model),
            [
                "schema_version",
                "engine",
                "source_commit",
                "provenance",
                "tables",
                "moves",
                "summaries",
            ],
        )
        self.assertEqual(self.model["summaries"]["move_count"], 992)
        self.assertEqual(self.model["summaries"]["unresolved_count"], 0)
        self.assertEqual(
            self.model["summaries"]["external_rom_pointer_counts"],
            {"description": 354, "animation": 330, "effect_script": 173},
        )
        self.assertEqual([row["id"] for row in self.model["moves"]], list(range(992)))
        self.assertEqual(len(self.model["tables"]), 6)
        self.assertRegex(self.model["summaries"]["inventory_sha256"], r"^[0-9a-f]{64}$")

    def test_row_schema_and_v3_exact_name_join(self) -> None:
        pound = self.model["moves"][1]
        self.assertEqual(pound["canonical_key"], "MOVE_KEY_POUND")
        self.assertEqual(pound["cfru_symbol"], "MOVE_POUND")
        self.assertEqual(pound["name_ja"], "はたく")
        self.assertEqual(pound["v3_exact_move_name"], pound["name_ja"])
        self.assertEqual(pound["generation"], 1)
        self.assertEqual(pound["category"], "PHYSICAL")
        self.assertEqual(pound["effect"], "EFFECT_HIT")
        self.assertEqual(pound["type"], "NORMAL")
        self.assertEqual((pound["power"], pound["accuracy"], pound["pp"]), (40, 100, 35))
        self.assertEqual(pound["target"], "SELECTED")
        self.assertEqual(pound["priority"], 0)
        self.assertTrue(pound["flags"])
        self.assertIn("battle_record", pound["source_refs"])
        self.assertEqual(pound["description_mapping_kind"], "EXTERNAL_ROM_POINTER")

        modern = ROOT / "design/imported/VEGA_CFRU_DPE_技調整設計_V3/data/技効果現代化マスター.csv"
        if modern.is_file():
            names = modern.read_text(encoding="utf-8-sig")
            fly = self.model["moves"][19]
            self.assertEqual(fly["v3_exact_move_name"], "そらをとぶ")
            self.assertIn("そらをとぶ", names)

    def test_cfru_official_name_collisions_remain_distinct_append_candidates(self) -> None:
        snipe_shot = self.model["moves"][0x2A7]
        jaw_lock = self.model["moves"][0x2A8]
        self.assertEqual(
            (snipe_shot["canonical_key"], snipe_shot["name_ja"]),
            ("MOVE_KEY_SNIPESHOT", "ねらいうち"),
        )
        self.assertEqual(
            (jaw_lock["canonical_key"], jaw_lock["name_ja"]),
            ("MOVE_KEY_JAWLOCK", "くらいつく"),
        )
        self.assertEqual(snipe_shot["vega_id_relation"], "CFRU_APPEND_CANDIDATE")
        self.assertEqual(jaw_lock["vega_id_relation"], "CFRU_APPEND_CANDIDATE")

    def test_config_preprocessor_selects_exact_active_branch(self) -> None:
        fragment = """
#ifdef ACTIVE
.power = 90,
#else
.power = 95,
#endif
#ifndef OMITTED
.pp = 15,
#endif
"""
        active = inventory._preprocess_fragment(fragment, {"ACTIVE"})
        inactive = inventory._preprocess_fragment(fragment, set())
        self.assertIn(".power = 90", active)
        self.assertNotIn(".power = 95", active)
        self.assertIn(".power = 95", inactive)
        self.assertIn(".pp = 15", inactive)

    def test_duplicate_and_gapped_move_constants_fail(self) -> None:
        duplicate = "#define MOVE_NONE 0\n#define MOVE_POUND 1\n#define MOVE_DUP 1\n"
        with self.assertRaisesRegex(ValueError, "duplicate move id"):
            inventory._parse_move_constants(duplicate, "moves.h")
        gap = "#define MOVE_NONE 0\n#define MOVE_TWO 2\n"
        with self.assertRaisesRegex(ValueError, "contiguous"):
            inventory._parse_move_constants(gap, "moves.h")

    def test_duplicate_string_symbol_and_variable_word_expression_fail(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate string symbol"):
            inventory._parse_string_file(
                "#org @NAME_A\na\n#org @NAME_A\nb\n", "names.string"
            )
        with self.assertRaisesRegex(ValueError, "unsupported .word expression"):
            inventory._parse_word_table(
                "Table:\n.word SYMBOL + 4\n", "table.s", "Table", 1
            )

    def test_numeric_and_flag_resolution_is_fail_closed(self) -> None:
        constants = {"FLAG_A": 1, "FLAG_B": 4}
        self.assertEqual(inventory._flags("FLAG_A | FLAG_B", constants), (["FLAG_A", "FLAG_B"], 5))
        with self.assertRaisesRegex(ValueError, "unresolved numeric symbol"):
            inventory._flags("FLAG_A | FLAG_UNKNOWN", constants)
        with self.assertRaisesRegex(ValueError, "duplicate flag"):
            inventory._flags("FLAG_A | FLAG_A", constants)

    def test_unresolved_animation_is_rejected_by_full_builder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "cfru"
            self._copy_parser_inputs(fixture)
            path = fixture / "assembly/data/attack_anim_table.s"
            text = path.read_text(encoding="utf-8")
            text = text.replace(".word 0x81AAEF0", ".word MISSING_ANIMATION", 1)
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unresolved animation symbol"):
                inventory.build_cfru_move_inventory(root, fixture)

    def test_source_outside_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            with self.assertRaisesRegex(ValueError, "inside root"):
                inventory.build_cfru_move_inventory(Path(first), Path(second))

    def test_fixed_production_path_requires_source_lock_and_git_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "vendor/upstream/CFRU-JP"
            self._copy_parser_inputs(fixture)
            with self.assertRaisesRegex(ValueError, "source-lock identity and git HEAD"):
                inventory.build_cfru_move_inventory(root, fixture)

    @staticmethod
    def _copy_parser_inputs(destination: Path) -> None:
        for relative in inventory._SOURCE_FILES:
            source = SOURCE / relative
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copytree(
            SOURCE / "assembly/battle_scripts",
            destination / "assembly/battle_scripts",
        )


if __name__ == "__main__":
    unittest.main()
