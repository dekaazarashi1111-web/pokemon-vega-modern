from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tools.engine.cfru_facility_runtime import (
    ABILITY_COUNT,
    BUILD_SOURCE,
    EXPECTED_CFRU_COMMIT,
    EXPECTED_SOURCE_HASHES,
    FORMAT_DISPATCH,
    FRONTIER_SOURCE,
    ITEM_COUNT,
    MOVE_COUNT,
    RULE_DISPATCH,
    RAID_PARTNER_SOURCE,
    SPREAD_SOURCE,
    TRAINER_SOURCE,
    CFRUFacilityRuntimeError,
    apply_facility_runtime_patches,
    build_facility_runtime,
    default_facility_spreads,
    make_vega_species_model,
    patch_builder_safety,
    patch_frontier_safety,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "vendor/upstream/CFRU-JP"


def _json(logical: str) -> dict:
    return json.loads((ROOT / logical).read_text(encoding="utf-8"))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CFRUFacilityRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.move_model = _json("generated/engine/moves/move_port.json")
        cls.id_model = _json("generated/engine/ids/id_spaces.json")
        cls.species_model = make_vega_species_model()
        cls.bundle = build_facility_runtime(
            SOURCE_ROOT, cls.move_model, cls.id_model, cls.species_model
        )

    def test_safety_patches_bound_indexes_exactly(self) -> None:
        source = (SOURCE_ROOT / FRONTIER_SOURCE).read_text(encoding="utf-8")
        patched = patch_frontier_safety(source)
        self.assertNotIn(
            "for (j = 0, tier = tiers[j]; j < numTiers; ++j, tier = tiers[j])",
            patched,
        )
        self.assertIn("for (j = 0; j < numTiers; ++j)", patched)
        self.assertIn("tier = tiers[j];", patched)
        self.assertNotIn(
            "*battleStyle = MathMin(*battleStyle, NUM_TOWER_BATTLE_TYPES);",
            patched,
        )
        self.assertIn(
            "*battleStyle = MathMin(*battleStyle, NUM_TOWER_BATTLE_TYPES - 1);",
            patched,
        )
        builder = (SOURCE_ROOT / BUILD_SOURCE).read_text(encoding="utf-8")
        patched_builder = patch_builder_safety(builder)
        self.assertIn("u32 vegaFacilityAttempts = 0;", patched_builder)
        self.assertIn("if (++vegaFacilityAttempts > 4096)", patched_builder)
        self.assertIn("Free(builder);\n\t\t\t\treturn 0;", patched_builder)
        self.assertIn(
            "spread = &gVegaMonotypeSpreads[Random() % "
            "ARRAY_COUNT(gVegaMonotypeSpreads)];",
            patched_builder,
        )
        self.assertIn("VEGA_FACILITY_SPREAD_SELECTED:", patched_builder)
        self.assertIn(
            "VegaFacilitySpreadIsCurated(spread) || !PokemonTierBan",
            patched_builder,
        )

    def test_non_unbound_fallbacks_are_nonempty_and_vega_safe(self) -> None:
        rendered = self.bundle.render()
        spreads = rendered[SPREAD_SOURCE]
        trainers = rendered[TRAINER_SOURCE]
        manifest = self.bundle.manifest()
        self.assertNotIn("const struct BattleTowerSpread gFrontierSpreads[] =\n{\n\t{\n\t},\n};", spreads)
        self.assertEqual(
            spreads.count("/* VEGA_RENTAL_"),
            sum(manifest["rental"]["array_counts"].values()),
        )
        self.assertIn("const struct BattleTowerTrainer gTowerTrainers[]", trainers)
        self.assertIn("const struct SpecialBattleFrontierTrainer gSpecialTowerTrainers[]", trainers)
        self.assertIn("const struct MultiBattleTowerTrainer gFrontierMultiBattleTrainers[]", trainers)
        fallback = trainers.split(
            "/* T06: non-empty deterministic trainers for Vega facility fixtures. */",
            1,
        )[1]
        for suffix in ("PreBattle", "PlayerWin", "PlayerLose"):
            self.assertIn(f"sFrontierText_Youngster_{suffix}_1", fallback)
            self.assertNotIn(f"sFrontierText_Youngster_{suffix}_2", fallback)
            self.assertNotIn(f"sFrontierText_Youngster_{suffix}_3", fallback)
        self.assertIn("extern const u8 sTrainerName_Red[];", fallback)
        self.assertEqual(fallback.count(".name = sTrainerName_Red,"), 4)
        self.assertEqual(manifest["rental"]["spread_count"], 19)
        self.assertIn(
            "static bool8 VegaFacilitySpreadIsCurated(", spreads
        )
        self.assertEqual(
            [row["key"] for row in manifest["safety_patches"]],
            [
                "ELIGIBILITY_LOOP_BOUNDED_INDEX",
                "BATTLE_STYLE_MAX_INDEX",
                "RENTAL_RETRY_LIMIT_4096",
                "CURATED_VEGA_SPECIES_TIER_AUTHORITY",
            ],
        )
        self.assertEqual(manifest["rental"]["array_counts"]["gFrontierSpreads"], 19)
        self.assertEqual(manifest["rental"]["array_counts"]["gVegaMonotypeSpreads"], 6)
        self.assertEqual(manifest["rental"]["array_counts"]["gLittleCupSpreads"], 6)
        self.assertEqual(manifest["rental"]["array_counts"]["gMiddleCupSpreads"], 6)
        self.assertEqual(
            manifest["rental"]["monotype_witness"],
            {"type_id": 12, "species_ids": [1, 2, 37, 38, 66, 74], "party_size": 6},
        )
        stage = (ROOT / "build/stages/04_moves.gba").read_bytes()
        base_stats = int.from_bytes(stage[0x1BC:0x1C0], "little") - 0x08000000
        for species in manifest["rental"]["monotype_witness"]["species_ids"]:
            row = stage[base_stats + species * 28:base_stats + (species + 1) * 28]
            self.assertIn(manifest["rental"]["monotype_witness"]["type_id"], row[6:8])
        monotype_block = spreads.split(
            "const struct BattleTowerSpread gVegaMonotypeSpreads[]", 1
        )[1].split("const struct BattleTowerSpread gMiddleCupSpreads[]", 1)[0]
        self.assertEqual(monotype_block.count("/* VEGA_RENTAL_"), 6)
        self.assertEqual(
            sorted(
                int(line.split("=", 1)[1].rstrip(", "))
                for line in monotype_block.splitlines()
                if line.strip().startswith(".species =")
            ),
            sorted(manifest["rental"]["monotype_witness"]["species_ids"]),
        )
        self.assertEqual(manifest["trainer_counts"], {
            "gTowerTrainers": 4,
            "gSpecialTowerTrainers": 1,
            "gFrontierBrains": 1,
            "gFrontierMultiBattleTrainers": 2,
        })
        self.assertTrue(all(0 < value < 412 for value in manifest["rental"]["species_ids"]))
        self.assertTrue(all(0 < value < MOVE_COUNT for value in manifest["rental"]["move_ids"]))
        raid = rendered[RAID_PARTNER_SOURCE]
        self.assertEqual(raid.count("/* VEGA_RENTAL_"), 3)
        self.assertIn("[ONE_STAR_RAID ... SIX_STAR_RAID]", raid)

    def test_format_and_rule_dispatch_cover_required_matrix(self) -> None:
        manifest = self.bundle.manifest()
        self.assertEqual(manifest["formats"], list(FORMAT_DISPATCH))
        self.assertEqual(manifest["rules"], list(RULE_DISPATCH))
        self.assertEqual(
            [(row["key"], row["battle_type"], row["random_battle_type"], row["party_size"])
             for row in manifest["formats"]],
            [("SINGLE_3V3", 0, 4, 3), ("DOUBLE_4V4", 1, 5, 4), ("NPC_PARTNER_MULTI", 2, 6, 4)],
        )
        self.assertEqual(
            {row["key"]: row["tier"] for row in manifest["rules"]},
            {"RANDOM": 0, "LITTLE": 4, "MONOTYPE": 6, "UNRESTRICTED": 1,
             "OU": 2, "UBER": 3, "CAMOMONS": 7, "GS": 5},
        )
        self.assertFalse(manifest["link_multi_release"])

    def test_manifest_records_schema_counts_hashes_and_is_deterministic(self) -> None:
        first = self.bundle.manifest()
        second = build_facility_runtime(
            SOURCE_ROOT, self.move_model, self.id_model, self.species_model
        )
        self.assertEqual(self.bundle.render(), second.render())
        self.assertEqual(first, second.manifest())
        self.assertEqual(first["source"]["commit"], EXPECTED_CFRU_COMMIT)
        self.assertEqual(first["source"]["inputs"], dict(EXPECTED_SOURCE_HASHES))
        self.assertEqual(first["models"]["moves"]["count"], MOVE_COUNT)
        self.assertEqual(first["models"]["ids"]["item_count"], ITEM_COUNT)
        self.assertEqual(first["models"]["ids"]["ability_count"], ABILITY_COUNT)
        self.assertEqual(first["models"]["species"]["count"], 412)
        self.assertRegex(first["fingerprint"], r"^[0-9a-f]{64}$")

    def test_render_is_side_effect_free(self) -> None:
        inputs = [SOURCE_ROOT / logical for logical in EXPECTED_SOURCE_HASHES]
        before = {path: _digest(path) for path in inputs}
        rendered = self.bundle.render()
        rendered[FRONTIER_SOURCE] = "tampered"
        after = {path: _digest(path) for path in inputs}
        self.assertEqual(before, after)
        self.assertNotEqual(self.bundle.render()[FRONTIER_SOURCE], "tampered")

    def test_unknown_or_missing_source_is_rejected(self) -> None:
        sources = {
            logical: (SOURCE_ROOT / logical).read_text(encoding="utf-8")
            for logical in EXPECTED_SOURCE_HASHES
        }
        unknown = dict(sources)
        unknown["src/Tables/future_frontier.c"] = ""
        with self.assertRaisesRegex(CFRUFacilityRuntimeError, "unknown"):
            apply_facility_runtime_patches(
                unknown, self.move_model, self.id_model, self.species_model
            )
        missing = dict(sources)
        missing.pop(TRAINER_SOURCE)
        with self.assertRaisesRegex(CFRUFacilityRuntimeError, "missing"):
            apply_facility_runtime_patches(
                missing, self.move_model, self.id_model, self.species_model
            )

    def test_fixed_source_drift_is_rejected_before_patch(self) -> None:
        sources = {
            logical: (SOURCE_ROOT / logical).read_text(encoding="utf-8")
            for logical in EXPECTED_SOURCE_HASHES
        }
        sources[FRONTIER_SOURCE] += "\n/* drift */\n"
        with self.assertRaisesRegex(CFRUFacilityRuntimeError, "SHA-256不一致"):
            apply_facility_runtime_patches(
                sources, self.move_model, self.id_model, self.species_model
            )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for logical in EXPECTED_SOURCE_HASHES:
                target = root / logical
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(sources[logical], encoding="utf-8")
            with self.assertRaisesRegex(CFRUFacilityRuntimeError, "SHA-256不一致"):
                build_facility_runtime(root, self.move_model, self.id_model, self.species_model)

    def test_out_of_range_species_and_move_are_rejected(self) -> None:
        spreads = list(default_facility_spreads())
        spreads[0] = replace(spreads[0], species_id=412)
        with self.assertRaisesRegex(CFRUFacilityRuntimeError, "Vega stable ID範囲外"):
            build_facility_runtime(
                SOURCE_ROOT, self.move_model, self.id_model, self.species_model, spreads=spreads
            )
        spreads = list(default_facility_spreads())
        spreads[0] = replace(spreads[0], move_ids=(MOVE_COUNT, 188, 73, 182))
        with self.assertRaisesRegex(CFRUFacilityRuntimeError, "T04 canonical範囲外"):
            build_facility_runtime(
                SOURCE_ROOT, self.move_model, self.id_model, self.species_model, spreads=spreads
            )

    def test_model_schema_and_row_drift_are_rejected(self) -> None:
        move_model = copy.deepcopy(self.move_model)
        move_model["moves"][33]["id"] = 34
        with self.assertRaisesRegex(CFRUFacilityRuntimeError, "連続canonical"):
            build_facility_runtime(SOURCE_ROOT, move_model, self.id_model, self.species_model)
        id_model = copy.deepcopy(self.id_model)
        id_model["items"][0]["item_key"] = "ITEM_KEY_UNKNOWN"
        with self.assertRaisesRegex(CFRUFacilityRuntimeError, "ITEM_NONE"):
            build_facility_runtime(SOURCE_ROOT, self.move_model, id_model, self.species_model)
        species_model = copy.deepcopy(self.species_model)
        species_model["source"] = "UNKNOWN"
        with self.assertRaisesRegex(CFRUFacilityRuntimeError, "schema/source/count"):
            build_facility_runtime(SOURCE_ROOT, self.move_model, self.id_model, species_model)


if __name__ == "__main__":
    unittest.main()
