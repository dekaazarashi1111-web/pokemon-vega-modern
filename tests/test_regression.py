import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools.regression.model import build_outputs as build_model_outputs
from tools.regression.rom_runtime import (
    GBA_ROM_BASE,
    STAGE17,
    STAGE17_META,
    build_runtime_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


class RegressionReleaseCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = build_runtime_outputs(ROOT)
        cls.rom = cls.outputs[STAGE17.as_posix()]
        cls.meta = json.loads(cls.outputs[STAGE17_META.as_posix()])

    def test_exact_rom_payload_and_invariants(self):
        self.assertEqual(len(self.rom), 32 * 1024 * 1024)
        self.assertEqual(hashlib.sha256(self.rom).hexdigest(), self.meta["output"]["sha256"])
        start = self.meta["payload"]["offset"]
        size = self.meta["payload"]["size"]
        self.assertEqual(
            hashlib.sha256(self.rom[start:start + size]).hexdigest(),
            self.meta["payload"]["sha256"],
        )
        self.assertTrue(all(self.meta["invariants"].values()))
        self.assertEqual(self.meta["allocation"]["overlap_count"], 0)

    def test_generated_trainers_are_bound_to_engine_abi(self):
        trainer = self.meta["trainers"]
        self.assertEqual(trainer["generated_trainers"], 29)
        self.assertEqual(trainer["production_rows_bound"], 174)
        self.assertEqual(trainer["repoint_count"], 24)
        root = trainer["address"] - GBA_ROM_BASE
        for trainer_id in (751, 763):
            record = root + trainer_id * trainer["record_size"]
            self.assertEqual(self.rom[record], 3)
            self.assertEqual(self.rom[record + 0x18], 6)
            self.assertEqual(struct.unpack_from("<I", self.rom, record + 0x14)[0], 5)
            party = struct.unpack_from("<I", self.rom, record + 0x1C)[0]
            self.assertGreaterEqual(party, GBA_ROM_BASE)
            self.assertLess(party, GBA_ROM_BASE + len(self.rom))

    def test_tohoku_wild_overlay_is_live_on_the_first_route(self):
        overlay = self.meta["wild"]["tohoku_overlay"]
        coverage = overlay["coverage"]
        self.assertEqual(coverage["source_rows"], 293)
        self.assertEqual(coverage["source_locations"], 41)
        self.assertEqual(coverage["runtime_source_rows"], 293)
        self.assertEqual(coverage["runtime_source_locations"], 41)
        self.assertEqual(coverage["runtime_candidate_bindings"], 294)
        self.assertEqual(coverage["deferred_source_rows"], 0)
        self.assertEqual(coverage["runtime_methods"], {
            "DexNav隠し枠": 7,
            "DexNav隠し枠／低確率タマゴ": 11,
            "いわくだき／DexNav": 22,
            "ずつき／朝昼オーバーレイ": 28,
            "夜間オーバーレイ": 34,
            "夜間水上オーバーレイ": 1,
            "大量発生": 29,
            "屋内異常遭遇／DexNav": 8,
            "水上オーバーレイ": 23,
            "水上／釣りオーバーレイ": 1,
            "洞窟・屋内オーバーレイ": 31,
            "草むらオーバーレイ": 77,
            "釣りオーバーレイ": 21,
        })
        self.assertEqual(coverage["deferred_methods"], {})
        self.assertTrue(coverage["conditional_unlocks_bound"])
        self.assertEqual(coverage["swarm_entry_count"], 9)
        self.assertEqual(
            sum(row["candidate_count"] for row in overlay["rows"]), 294
        )
        self.assertEqual(overlay["entry_count"], 95)
        self.assertEqual(
            sum(sum(row["radar_overrides"]) for row in overlay["rows"]), 1
        )
        first = next(
            row for row in overlay["rows"]
            if row["logical_location"] == "T501"
            and row["area"] == 0 and row["layer"] == 0
        )
        self.assertEqual((first["group"], first["map"]), (3, 19))
        self.assertEqual(first["rate_percent"], 5)
        self.assertEqual(first["candidate_count"], 8)
        self.assertIn(950, first["species"])   # ヤヤコマ
        self.assertIn(1491, first["species"])  # パモ
        hook = overlay["hook"]
        site = hook["site"] - GBA_ROM_BASE
        self.assertEqual(struct.unpack_from("<I", self.rom, site + 4)[0], hook["target"])
        fishing_hook = overlay["fishing_hook"]
        fishing_site = fishing_hook["site"] - GBA_ROM_BASE
        self.assertEqual(
            struct.unpack_from("<I", self.rom, fishing_site + 4)[0],
            fishing_hook["target"],
        )
        radar = overlay["ecology_radar"]
        item = radar["item_address"] - GBA_ROM_BASE
        self.assertEqual(struct.unpack_from("<H", self.rom, item + 10)[0], 348)
        self.assertEqual(
            struct.unpack_from("<I", self.rom, item + 24)[0],
            radar["field_callback"],
        )
        self.assertTrue(overlay["normal_tables_preserved"])

        mgba = json.loads((ROOT / "build/stages/17_mgba_smoke.json").read_text())
        self.assertTrue(mgba["checks"]["first_route_wild_overlay"])
        self.assertTrue(mgba["checks"]["first_route_wild_generation"])
        self.assertTrue(mgba["checks"]["wild_overlay_isolated"])
        self.assertTrue(mgba["checks"]["special_ecology_modes"])
        self.assertTrue(mgba["checks"]["rtc_auto_ecology"])
        self.assertTrue(mgba["checks"]["radar_ticket_alternative"])
        self.assertTrue(mgba["checks"]["fishing_ecology"])
        self.assertTrue(mgba["checks"]["hidden_ecology"])
        self.assertTrue(mgba["checks"]["hidden_mode_isolated"])
        self.assertTrue(mgba["checks"]["hidden_battle_scheduled"])
        self.assertTrue(mgba["checks"]["ecology_radar_item"])
        self.assertTrue(mgba["checks"]["ecology_radar_menu"])
        observed = mgba["first_route_wild_overlay"]
        self.assertEqual(observed["calls"], 4096)
        self.assertGreaterEqual(observed["hits"], 120)
        self.assertLessEqual(observed["hits"], 300)
        self.assertEqual(observed["candidate_mask"], 0xFF)
        self.assertGreater(observed["generation_calls"], 0)
        self.assertIn(observed["generated_species"], first["species"])

    def test_kanto_progression_is_physical_and_ordered(self):
        progression = self.meta["progression"]
        self.assertEqual(progression["physical_battle_objects"], 13)
        self.assertEqual(len(progression["certification_flags"]), 8)
        self.assertEqual(len(progression["league_flags"]), 5)
        self.assertEqual(progression["final_objective_flag"], 0x140C)
        self.assertIn("progress::PewterCity_Gym", self.meta["symbols"])
        self.assertIn("progress::PokemonLeague_ChampionsRoom", self.meta["symbols"])

    def test_kanto_safe_world_events_are_not_discarded(self):
        recovery = self.meta["maps"]["safe_world_recovery"]
        self.assertEqual(recovery["policy"], "LOCAL_NPC_AND_NORMAL_SIGN_ONLY")
        self.assertEqual(recovery["nurses"], 12)
        self.assertGreaterEqual(recovery["mart_clerks"], 8)
        self.assertGreaterEqual(recovery["civilian_objects"], 700)
        self.assertGreaterEqual(recovery["signs"], 350)
        self.assertFalse(recovery["fire_red_story_scripts_imported"])
        self.assertFalse(recovery["hidden_items_imported"])
        self.assertTrue(all(row["object_count"] <= 15 for row in self.meta["maps"]["rows"]))

    def test_regression_model_matches_generated_artifacts(self):
        mgba = json.loads((ROOT / "build/stages/17_mgba_smoke.json").read_text())
        qol = json.loads((ROOT / "tests/fixtures/qol_b.json").read_text())
        outputs = build_model_outputs(ROOT, self.meta, mgba, qol)
        for relative, raw in outputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), raw, relative)
        fixture = json.loads(outputs["tests/fixtures/regression.json"])
        self.assertEqual(fixture["status"], "PASS")
        self.assertEqual(fixture["round_trips"]["total"], 400)
        self.assertEqual(fixture["maps"]["reachable_from_vermilion"], 253)
        self.assertEqual(fixture["shared_captures"]["shared_keys"], 125)
        self.assertEqual(fixture["events"]["branch_cases"], 238)


if __name__ == "__main__":
    unittest.main()
