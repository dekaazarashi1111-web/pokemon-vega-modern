#!/usr/bin/env python3
"""T04 stage driverのfocused contract tests。"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts.build_move_port import build_move_model, render_artifacts
from scripts.build_move_stage import (
    MoveStageError,
    _allocation,
    _read_config,
    _summary_counts,
    _validate_smoke,
    build_stage_bytes,
    discover_table_repoints,
)


@unittest.skipUnless(
    (ROOT / "build/stages/03_harness.gba").is_file()
    and (ROOT / "build/reference/vega.gba").is_file(),
    "fixed T03/Vega artifacts are unavailable",
)
class FixedMoveStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = _read_config(ROOT)
        cls.stage03 = (ROOT / "build/stages/03_harness.gba").read_bytes()
        cls.model = build_move_model(ROOT, cls.config)
        cls.artifacts = render_artifacts(cls.model)
        cls.bridge = cls.artifacts["generated/engine/moves/vega_bridge.bin"]

    def test_model_bridge_and_manifest_contract(self) -> None:
        summary = _summary_counts(self.model)
        self.assertEqual(summary["frozen_count"], 512)
        self.assertEqual(summary["appended_count"], 551)
        self.assertEqual(summary["move_count"], 1063)
        self.assertEqual(summary["exact_match_count"], 442)
        self.assertEqual(summary["exact_match_identity_count"], 441)
        self.assertEqual(summary["v3_modern_count"], 61)
        self.assertEqual(summary["v3_exclusive_count"], 70)
        self.assertEqual(len(self.bridge), 44032)
        manifest = self.artifacts["manifests/move_ids.csv"].decode("utf-8")
        self.assertIn("MOVE_KEY_SOUL_BITE,470,470", manifest)
        self.assertIn("MOVE_KEY_DARK_SNIPE,509,509", manifest)

    def test_real_stage_has_exact_178_repoints_and_one_bridge(self) -> None:
        candidate, rows, layout = build_stage_bytes(
            self.stage03, self.bridge, self.config
        )
        self.assertEqual(len(candidate), 32 * 1024 * 1024)
        self.assertEqual(len(rows), 178)
        self.assertEqual(
            {name: sum(row["table"] == name for row in rows) for name in layout},
            {"names": 32, "battle": 137, "descriptions": 2, "animations": 1, "effects": 6},
        )
        start = int(self.config["bridge"]["start"], 0)
        self.assertEqual(candidate[start : start + len(self.bridge)], self.bridge)
        allowed = set(range(start, start + len(self.bridge)))
        for row in rows:
            allowed.update(range(row["rom_offset"], row["rom_offset"] + 4))
        changed = {
            index
            for index, (before, after) in enumerate(zip(self.stage03, candidate, strict=True))
            if before != after
        }
        self.assertTrue(changed)
        self.assertEqual(changed - allowed, set())

    def test_repoint_count_and_destination_are_fail_closed(self) -> None:
        bad_config = copy.deepcopy(self.config)
        bad_config["vega"]["tables"]["names"]["reference_count"] = 31
        with self.assertRaisesRegex(MoveStageError, "repoint count mismatch"):
            discover_table_repoints(
                self.stage03,
                bad_config,
                bridge_start=int(self.config["bridge"]["start"], 0),
                bridge_size=len(self.bridge),
            )
        occupied = bytearray(self.stage03)
        occupied[int(self.config["bridge"]["start"], 0)] = 0
        with self.assertRaisesRegex(MoveStageError, "not erased"):
            build_stage_bytes(bytes(occupied), self.bridge, self.config)

    def test_allocator_cross_links_t03_and_t04(self) -> None:
        allocation = _allocation(ROOT, self.bridge, self.config)
        self.assertEqual(allocation["summaries"]["overlap_count"], 0)
        self.assertEqual(allocation["summaries"]["allocation_count"], 2)
        rows = {row["name"]: row for row in allocation["allocations"]}
        self.assertEqual(rows["vega_adapter_module"]["start"], 0x01200000)
        self.assertEqual(rows["vega_adapter_module"]["end_exclusive"], 0x01200022)
        self.assertEqual(rows["move_table_bridge"]["start"], 0x01200024)
        self.assertEqual(rows["move_table_bridge"]["end_exclusive"], 0x0120AC24)


class MoveSmokeValidationTests(unittest.TestCase):
    @staticmethod
    def fixture() -> dict[str, object]:
        battlers = [
            {"index": 0, "species": 4, "hp": 20, "moves": [33, 43, 0, 0], "pp": [35, 30, 0, 0]},
            {"index": 1, "species": 10, "hp": 20, "moves": [64, 45, 116, 0], "pp": [35, 25, 30, 0]},
        ]
        after_battlers = copy.deepcopy(battlers)
        after_battlers[0]["pp"][0] = 34
        after_battlers[1]["hp"] = 14
        return {
            "schema_version": 1,
            "status": "PASS",
            "fixture": "synthetic_rooted_early_wild_battle",
            "battle_kind": "WILD",
            "rom_sha256": "a" * 64,
            "fixed_rtc_unix": 946684800,
            "provenance": {
                "field_base": "natural_T03_233_segment_trace",
                "rooted_species": {"player": 4, "enemy": 10, "level": 5},
                "direct_rom_calls": {
                    "CreateMon": "0x0803D1C1",
                    "BattleSetup_StartWildBattle": "0x0807EE2D",
                },
            },
            "boot_trace_segments": 233,
            "progress_frames": 300,
            "move_id_contract": {"zero_slot_allowed": True, "nonzero_min": 1, "nonzero_max": 511},
            "warnings_errors": 0,
            "before": {
                "wild_battle_active": True,
                "battle_type_flags": 4,
                "active_battlers": 2,
                "absent_flags": 0,
                "ewram_iwram_fnv1a64": "0123456789abcdef",
                "pc": 0x08000100,
                "battlers": copy.deepcopy(battlers),
            },
            "move_execution": {
                "input": "A_x6_slot0",
                "player_pp_spent": True,
                "hp_changed": True,
            },
            "after": {
                "wild_battle_active": True,
                "battle_type_flags": 4,
                "active_battlers": 2,
                "absent_flags": 0,
                "ewram_iwram_fnv1a64": "fedcba9876543210",
                "pc": 0x08000200,
                "battlers": after_battlers,
            },
            "core_alive_after_progression": True,
            "active_move_ids_stable": True,
            "artifacts_written": [],
        }

    def test_valid_and_tampered_smoke(self) -> None:
        fixture = self.fixture()
        self.assertEqual(_validate_smoke(fixture, "a" * 64), fixture)
        for mutation in (
            lambda value: value.update({"battle_kind": "TRAINER"}),
            lambda value: value["before"].update({"battle_type_flags": 12}),
            lambda value: value["after"]["battlers"][1].update({"moves": [600, 45, 116, 0]}),
            lambda value: value["after"].update({"ewram_iwram_fnv1a64": "0123456789abcdef"}),
        ):
            bad = copy.deepcopy(fixture)
            mutation(bad)
            with self.assertRaises(MoveStageError):
                _validate_smoke(bad, "a" * 64)


if __name__ == "__main__":
    unittest.main()
