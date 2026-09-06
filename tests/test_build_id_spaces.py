#!/usr/bin/env python3
"""T05 ID space model/generatorのfocused tests。"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_id_spaces import (
    ABILITY_MANIFEST_HEADER,
    ARTIFACT_PATHS,
    ITEM_MANIFEST_HEADER,
    TYPE_MANIFEST_HEADER,
    IdSpaceBuildError,
    _compile_probe,
    build_id_space_model,
    check,
    render_artifacts,
    validate_id_space_model,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/id_spaces.json"
VEGA_ROM = ROOT / "build/reference/vega.gba"
# baseline path/hashは現行configで固定済み。古いcache pathでskipしない。
class IdSpaceBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        baseline = ROOT / cls.config["cfru"]["baseline_rom_path"]
        if hashlib.sha256(baseline.read_bytes()).hexdigest() != cls.config["cfru"]["baseline_rom_sha256"]:
            raise ValueError("T05 configured baseline ROM hash differs")
        cls.model = build_id_space_model(ROOT, cls.config)
        cls.artifacts = render_artifacts(cls.model)

    def test_exact_contiguous_counts_and_ranges(self) -> None:
        self.assertEqual([row["id"] for row in self.model["types"]], list(range(25)))
        self.assertEqual([row["id"] for row in self.model["abilities"]], list(range(312)))
        self.assertEqual([row["id"] for row in self.model["items"]], list(range(999)))
        self.assertEqual(
            self.model["summary"],
            {
                "type_count": 25,
                "active_type_count": 20,
                "ability_count": 312,
                "frozen_ability_count": 78,
                "appended_ability_count": 234,
                "item_count": 999,
                "frozen_item_count": 375,
                "cfru_appended_item_count": 613,
                "qol_appended_item_count": 11,
                "cfru_ability_alias_count": 311,
                "cfru_item_alias_count": 827,
                "item_semantic_identity_count": 161,
                "item_type_explicit_count": 465,
                "evolution_stone_count": 12,
                "evolution_item_count": 40,
                "ball_kind_count": 27,
                "qol_effect_count": 45,
                "text_width_overflow_count": 0,
                "last_ability_id": 311,
                "last_item_id": 998,
            },
        )

    def test_vega_frozen_prefix_and_cross_id_gold_teeth_mapping(self) -> None:
        self.assertEqual(
            [row["vega_id"] for row in self.model["abilities"][:78]], list(range(78))
        )
        self.assertEqual(
            [row["vega_id"] for row in self.model["items"][:375]], list(range(375))
        )
        self.assertTrue(all(row["status"] == "FROZEN" for row in self.model["items"][:375]))
        gold = self.model["items"][353]
        self.assertEqual(
            (gold["item_key"], gold["cfru_id"], gold["cfru_symbol"]),
            ("ITEM_KEY_GOLD_TEETH", 348, "ITEM_GOLD_TEETH"),
        )
        self.assertEqual(len(bytes.fromhex(gold["vega_raw"]["raw_hex"])), 40)
        self.assertEqual(gold["vega_raw"]["item_id"], 353)
        dire_hit = self.model["items"][74]
        self.assertEqual(
            (dire_hit["item_key"], dire_hit["cfru_id"], dire_hit["cfru_symbol"]),
            ("ITEM_KEY_DIRE_HIT", 74, "ITEM_DIRE_HIT"),
        )
        self.assertEqual(dire_hit["display_name"], "クリティカッター")
        self.assertEqual(dire_hit["price"], dire_hit["vega_raw"]["price"])

    def test_item_identity_requires_semantic_equivalence(self) -> None:
        aliases = {row["source_symbol"]: row for row in self.model["item_aliases"]}
        self.assertEqual(
            sum(
                row["classification"] == "VEGA_CFRU_CANONICAL"
                for row in self.model["items"][:375]
            ),
            161,
        )
        for source_id, symbol in (
            (80, "ITEM_POKE_DOLL"),
            (153, "ITEM_POMEG_BERRY"),
            (154, "ITEM_KELPSY_BERRY"),
            (155, "ITEM_QUALOT_BERRY"),
            (156, "ITEM_HONDEW_BERRY"),
            (157, "ITEM_GREPA_BERRY"),
            (158, "ITEM_TAMATO_BERRY"),
            (175, "ITEM_ENIGMA_BERRY_OLD"),
            (182, "ITEM_EXP_SHARE"),
            (218, "ITEM_UP_GRADE"),
            (276, "ITEM_RED_ORB"),
            (277, "ITEM_BLUE_ORB"),
            (289, "ITEM_TM01_FOCUS_PUNCH"),
        ):
            canonical_id = aliases[symbol]["canonical_id"]
            self.assertGreaterEqual(canonical_id, 375, symbol)
            self.assertEqual(self.model["items"][canonical_id]["cfru_id"], source_id)
            self.assertIsNone(self.model["items"][canonical_id]["vega_id"])
            self.assertEqual(self.model["items"][source_id]["vega_id"], source_id)
            self.assertIsNone(self.model["items"][source_id]["cfru_id"])

        for symbol, canonical_id in (
            ("ITEM_DIRE_HIT", 74),
            ("ITEM_CHOICE_BAND", 186),
            ("ITEM_GOLD_TEETH", 353),
        ):
            self.assertEqual(aliases[symbol]["canonical_id"], canonical_id)

        broken = copy.deepcopy(self.config)
        broken["mapping_policy"]["item"]["automatic_match"] = "SAME_SOURCE_ID_NFKC_NAME"
        with self.assertRaisesRegex(IdSpaceBuildError, "automatic match"):
            build_id_space_model(ROOT, broken)

    def test_ability_airlock_shift_preserves_cacophony(self) -> None:
        abilities = self.model["abilities"]
        aliases = {row["source_symbol"]: row for row in self.model["ability_aliases"]}
        self.assertEqual(
            (abilities[76]["ability_key"], abilities[76]["display_name"]),
            ("ABILITY_KEY_CACOPHONY", "そうおん"),
        )
        self.assertEqual(
            (abilities[77]["ability_key"], abilities[77]["display_name"]),
            ("ABILITY_KEY_AIRLOCK", "エアロック"),
        )
        self.assertEqual(aliases["ABILITY_AIRLOCK"]["canonical_id"], 77)
        self.assertEqual(aliases["ABILITY_TANGLEDFEET"]["canonical_id"], 78)
        self.assertEqual(aliases["ABILITY_POISONPUPPETEER"]["canonical_id"], 311)

    def test_fairy_and_stellar_have_complete_active_contracts(self) -> None:
        types = self.model["types"]
        fairy = types[23]
        stellar = types[24]
        self.assertEqual(
            (
                fairy["display_name"],
                fairy["tera_input_code"],
                fairy["effectiveness"][1],
                fairy["effectiveness"][16],
                fairy["effectiveness"][17],
                types[16]["effectiveness"][23],
            ),
            ("フェアリー", 24, 2000, 2000, 2000, 1),
        )
        self.assertEqual(
            (
                stellar["display_name"],
                stellar["classification"],
                stellar["status"],
                stellar["special_rule"],
                stellar["runtime_binding"],
            ),
            (
                "ステラ",
                "CFRU_APPEND",
                "APPENDED",
                "STELLAR_CFRU_SPECIAL",
                "T06_RUNTIME_BIND_PENDING",
            ),
        )
        self.assertTrue(stellar["icon_key"] and stellar["color_key"])
        self.assertEqual(len(stellar["effectiveness"]), 25)
        self.assertEqual(
            (fairy["icon_geometry"], fairy["display_color"]),
            (
                {"width": 32, "height": 12, "tile_offset": 224},
                {"r": 29, "g": 17, "b": 25, "bgr555": 26173},
            ),
        )
        self.assertEqual(
            (stellar["icon_geometry"], stellar["display_color"]),
            (
                {"width": 32, "height": 12, "tile_offset": 228},
                {"r": 31, "g": 31, "b": 31, "bgr555": 32767},
            ),
        )
        self.assertIn("assembly/data/type_tables.s", stellar["icon_source"])
        self.assertIn("src/terastal.c", stellar["color_source"])

    def test_vega_type_matrix_behavior_overrides_are_preserved(self) -> None:
        types = self.model["types"]
        self.assertEqual(types[7]["effectiveness"][8], 500)
        self.assertEqual(types[17]["effectiveness"][8], 500)
        self.assertEqual(types[0]["effectiveness"][7], 1)

    def test_all_source_symbols_resolve_exactly_once(self) -> None:
        ability_aliases = self.model["ability_aliases"]
        item_aliases = self.model["item_aliases"]
        self.assertEqual(len(ability_aliases), len({row["source_symbol"] for row in ability_aliases}))
        self.assertEqual(len(item_aliases), len({row["source_symbol"] for row in item_aliases}))
        self.assertEqual([row["source_id"] for row in ability_aliases], list(range(311)))
        self.assertEqual(len([row for row in item_aliases if row["source_symbol"] == "ITEM_ENIGMA_BERRY"]), 1)
        self.assertEqual(len(item_aliases), 827)
        aliases = {row["source_symbol"]: row for row in item_aliases}
        self.assertEqual(aliases["ITEM_TM02_DRAGON_CLAW"]["canonical_id"], aliases["ITEM_TM02"]["canonical_id"])
        self.assertEqual(aliases["ITEM_HM05_FLASH"]["canonical_id"], aliases["ITEM_HM05_DIVE"]["canonical_id"])

    def test_qol_candy_and_ev_reset_contracts_are_appended(self) -> None:
        items = {row["item_key"]: row for row in self.model["items"]}
        for suffix, value in zip(("XS", "S", "M", "L", "XL"), (100, 800, 3000, 10000, 30000)):
            row = items[f"ITEM_KEY_EXP_CANDY_{suffix}"]
            self.assertEqual((row["field_effect_key"], int(row["field_effect_param"])), ("EXP_ADD_FIXED", value))
            self.assertEqual((row["consume_policy"], row["target_policy"]), ("ON_EFFECT", "PARTY_ONE"))
        for stat in ("HP", "ATK", "DEF", "SPEED", "SPATK", "SPDEF"):
            row = items[f"ITEM_KEY_EV_RESET_{stat}"]
            self.assertEqual((row["field_effect_key"], row["field_effect_param"]), ("EV_SET_ZERO", f"STAT_{stat}"))
            self.assertNotIn("BERRY", row["item_key"])

    def test_training_items_have_qol_semantics_and_supply_keys(self) -> None:
        items = {row["item_key"]: row for row in self.model["items"]}
        self.assertEqual(items["ITEM_KEY_OVAL_CHARM"]["field_effect_key"], "BREEDING_CHECK_MULTIPLIER_X2_CAP100")
        self.assertEqual(items["ITEM_KEY_BOTTLE_CAP"]["field_effect_key"], "HYPER_TRAIN_ONE")
        self.assertEqual(items["ITEM_KEY_GOLD_BOTTLE_CAP"]["field_effect_key"], "HYPER_TRAIN_ALL")
        mints = [row for key, row in items.items() if key.endswith("_MINT")]
        self.assertEqual(len(mints), 21)
        self.assertTrue(all(row["field_effect_key"] == "NATURE_MODIFIER_SET_KEEP_PERSONALITY" for row in mints))
        self.assertTrue(all(row["supply_key"].startswith("SUPPLY_") for row in items.values()))
        for key in (
            "ITEM_KEY_EVERSTONE",
            "ITEM_KEY_DESTINY_KNOT",
            "ITEM_KEY_POWER_WEIGHT",
            "ITEM_KEY_POWER_BRACER",
            "ITEM_KEY_POWER_BELT",
            "ITEM_KEY_POWER_ANKLET",
            "ITEM_KEY_POWER_LENS",
            "ITEM_KEY_POWER_BAND",
        ):
            self.assertEqual(
                (items[key]["consume_policy"], items[key]["target_policy"]),
                ("NEVER", "HELD"),
            )
        self.assertEqual(
            (
                items["ITEM_KEY_OVAL_CHARM"]["consume_policy"],
                items["ITEM_KEY_OVAL_CHARM"]["target_policy"],
            ),
            ("NEVER", "PASSIVE_KEY_ITEM"),
        )

    def test_qol_assets_are_resolved_source_symbols(self) -> None:
        items = {row["item_key"]: row for row in self.model["items"]}
        for suffix in ("XS", "S", "M", "L", "XL"):
            row = items[f"ITEM_KEY_EXP_CANDY_{suffix}"]
            self.assertEqual(
                (row["icon_key"], row["palette_key"]),
                ("gItemIcon_RareCandyTiles", "gItemIcon_RareCandyPal"),
            )
        expected = {
            "HP": "PomegBerry",
            "ATK": "KelpsyBerry",
            "DEF": "QualotBerry",
            "SPEED": "TamatoBerry",
            "SPATK": "HondewBerry",
            "SPDEF": "GrepaBerry",
        }
        for stat, asset in expected.items():
            row = items[f"ITEM_KEY_EV_RESET_{stat}"]
            self.assertEqual(
                (row["icon_key"], row["palette_key"]),
                (f"gItemIcon_{asset}Tiles", f"gItemIcon_{asset}Pal"),
            )

        broken = copy.deepcopy(self.config)
        broken["new_items"][0]["icon_key"] = "gItemIcon_TypoTiles"
        with self.assertRaisesRegex(IdSpaceBuildError, "icon is not resolved"):
            build_id_space_model(ROOT, broken)

    def test_ball_pocket_and_evolution_axes_are_resolved(self) -> None:
        items = self.model["items"]
        balls = [row for row in items if row["ball_kind"] != "NONE"]
        self.assertEqual(len(balls), 27)
        self.assertEqual(len({row["ball_kind"] for row in balls}), 27)
        self.assertTrue(
            all(row["pocket"] == "POCKET_POKE_BALLS" and row["role"] == "BALL" for row in balls)
        )
        self.assertEqual(items[1]["ball_kind"], "BALL_KIND_MASTER")
        self.assertEqual(items[12]["ball_kind"], "BALL_KIND_PREMIER")
        self.assertEqual(
            {row["pocket"] for row in items},
            {
                "POCKET_ITEMS",
                "POCKET_KEY_ITEMS",
                "POCKET_POKE_BALLS",
                "POCKET_TM_CASE",
                "POCKET_BERRIES",
            },
        )
        self.assertEqual(sum(row["is_evolution_stone"] for row in items), 12)
        self.assertEqual(sum(row["is_evolution_item"] for row in items), 40)
        self.assertEqual(
            sum(row["is_evolution_item"] and row["hold_effect_key"] != "NONE" for row in items),
            9,
        )

    def test_source_mystery_byte_is_separate_from_secondary_id(self) -> None:
        items = {row["item_key"]: row for row in self.model["items"]}
        for key, mystery in (
            ("ITEM_KEY_TM01", 1),
            ("ITEM_KEY_HM01_CUT", 121),
            ("ITEM_KEY_CHERI_BERRY", 1),
            ("ITEM_KEY_LONELY_MINT", 1),
        ):
            self.assertEqual(items[key]["source_mystery"], mystery)
            self.assertEqual(items[key]["secondary_id"], 0)

    def test_manifest_headers_rows_and_none_sentinels(self) -> None:
        contracts = (
            ("manifests/type_ids.csv", TYPE_MANIFEST_HEADER, 25),
            ("manifests/ability_ids.csv", ABILITY_MANIFEST_HEADER, 312),
            ("manifests/item_ids.csv", ITEM_MANIFEST_HEADER, 999),
        )
        for logical, header, count in contracts:
            reader = csv.DictReader(io.StringIO(self.artifacts[logical].decode("utf-8")))
            rows = list(reader)
            self.assertEqual(tuple(reader.fieldnames or ()), header)
            self.assertEqual(len(rows), count)
            self.assertFalse(any(value == "" for row in rows for value in row.values()))
        type_rows = list(csv.DictReader(io.StringIO(self.artifacts["manifests/type_ids.csv"].decode())))
        self.assertEqual(type_rows[18]["cfru_symbol"], "NONE")
        self.assertEqual(type_rows[24]["cfru_symbol"], "TYPE_STELLAR")

    def test_artifacts_are_deterministic_and_complete(self) -> None:
        self.assertEqual(set(self.artifacts), set(ARTIFACT_PATHS))
        self.assertEqual(self.artifacts, render_artifacts(self.model))
        public = json.loads(self.artifacts["generated/engine/ids/id_spaces.json"])
        self.assertEqual(public["fingerprint"], self.model["fingerprint"])
        self.assertNotIn("manifests", public)
        self.assertEqual(len(self.model["fingerprint"]), 64)
        self.assertEqual(
            hashlib.sha256(self.artifacts["generated/engine/ids/ids_generated.h"]).hexdigest(),
            hashlib.sha256(render_artifacts(self.model)["generated/engine/ids/ids_generated.h"]).hexdigest(),
        )
        header = self.artifacts["generated/engine/ids/ids_generated.h"].decode("ascii")
        self.assertIn("#define TYPE_NORMAL TYPE_KEY_NORMAL", header)
        self.assertIn("#define TYPE_FAIRY TYPE_KEY_FAIRY", header)
        self.assertIn("#define TYPE_STELLAR TYPE_KEY_STELLAR", header)
        self.assertNotIn("#define TYPE_RESERVED_18", header)
        type_c = self.artifacts["generated/engine/ids/type_tables.c"].decode("ascii")
        self.assertIn("26173u", type_c)
        self.assertIn("32767u", type_c)
        item_c = self.artifacts["generated/engine/ids/item_tables.c"].decode("ascii")
        self.assertIn("ID_SPACE_ITEM_FLAG_EVOLUTION_ITEM", header)
        for field in (
            "description_token",
            "source_mystery",
            "source_use_type_token",
            "role_token",
            "field_callback_token",
            "battle_callback_token",
            "supply_token",
            "runtime_binding_token",
        ):
            self.assertIn(field, header)
        self.assertIn("ITEM_KEY_EXP_CANDY_XS", item_c)
        self.assertIn("#define ITEMS_COUNT ID_SPACE_ITEM_COUNT", header)
        self.assertIn("#define ABILITIES_COUNT ID_SPACE_ABILITY_COUNT", header)
        self.assertIn("#ifdef ITEM_TM02_DRAGON_CLAW", header)

    def test_generated_c_compile_and_semantic_probe(self) -> None:
        if shutil.which("cc") is None:
            self.skipTest("host C compiler is unavailable")
        result = _compile_probe(self.artifacts)
        self.assertEqual(result["result"], "PASS")

    def test_t06_runtime_handoff_requires_canonical_positional_tables(self) -> None:
        handoff = self.model["runtime_handoff"]
        self.assertFalse(handoff["semantic_tables_are_runtime_abi"])
        self.assertEqual(
            {(row["table_key"], row["canonical_rows"]) for row in handoff["canonical_rebuilds"]},
            {
                ("ITEM_DATA", 999),
                ("ITEM_GRAPHICS", 999),
                ("ABILITY_NAMES", 312),
                ("ABILITY_DESCRIPTIONS", 312),
            },
        )
        self.assertIn("REPOINT_ALL_RUNTIME_CONSUMERS", handoff["hard_gates"])
        broken = copy.deepcopy(self.model)
        broken["runtime_handoff"]["canonical_rebuilds"][0]["canonical_rows"] = 774
        with self.assertRaisesRegex(IdSpaceBuildError, "positional runtime-table handoff"):
            validate_id_space_model(broken)

    def test_model_validation_fails_closed(self) -> None:
        broken = copy.deepcopy(self.model)
        broken["items"][375]["id"] = 9999
        with self.assertRaisesRegex(IdSpaceBuildError, "contiguous"):
            validate_id_space_model(broken)
        broken = copy.deepcopy(self.model)
        broken["item_aliases"].append(copy.deepcopy(broken["item_aliases"][0]))
        with self.assertRaisesRegex(IdSpaceBuildError, "every CFRU item"):
            validate_id_space_model(broken)

    def test_check_is_read_only_and_matches_published_bytes(self) -> None:
        # Releaseは過去の検証source fingerprintを含むため、現行generatorで
        # 独立workspaceへ生成してcheckを検証する。復元済み成果は変更しない。
        from scripts.build_id_spaces import FINGERPRINT_FILES, build as publish
        original = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                    for name in ARTIFACT_PATHS}
        with tempfile.TemporaryDirectory(prefix="t05-published-fixture-") as directory:
            root = Path(directory)
            for name in ("vendor/upstream/CFRU-JP", "vendor/upstream/DPE-JP"):
                shutil.copytree(ROOT / name, root / name)
            inputs = set(FINGERPRINT_FILES) | {
                "reports/generated/upstream_repro.json",
                self.config["vega"]["rom_path"],
                self.config["cfru"]["baseline_rom_path"],
                self.config["cfru"]["offsets_path"],
            }
            for name in sorted(inputs):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            (root / "build").mkdir(exist_ok=True)
            published = publish(root)
            self.assertEqual(published["fingerprint"], self.model["fingerprint"])
            for name, expected in self.artifacts.items():
                self.assertEqual((root / name).read_bytes(), expected, name)
            before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                      for name in ARTIFACT_PATHS}
            result = check(root)
            after = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                     for name in ARTIFACT_PATHS}
            self.assertEqual(result["side_effects"], "NONE")
            self.assertEqual(before, after)
            # stale byte拒否を負例で維持する。実generator/checkをmockしない。
            corrupt = root / "generated/engine/ids/ids_generated.h"
            corrupt.write_bytes(corrupt.read_bytes() + b"\n/* deliberate drift */\n")
            with self.assertRaisesRegex(IdSpaceBuildError, "published artifact is stale"):
                check(root)
        self.assertEqual(original, {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                    for name in ARTIFACT_PATHS})


if __name__ == "__main__":
    unittest.main()
