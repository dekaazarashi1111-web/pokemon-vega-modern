#!/usr/bin/env python3
"""T06 battle-core libmGBA runnerの限定acceptance。"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/mgba_battle_core_smoke.c"
STAGE_CANDIDATES = [
    ROOT / "build/stages/06_battle_core.gba",
    ROOT / "build/stages/06_battle.gba",
    *sorted((ROOT / "build/stages").glob("06*.gba")),
]
PAYLOAD_START = 0x09000000
PAYLOAD_END = 0x09200000
CANONICAL_MOVE_MAX = 1062
BATTLE_TYPE_TRAINER = 0x0008
BATTLE_TYPE_DOUBLE = 0x0001
EXPECTED_ROUTES = {
    "status": "SCHEDULER_E2E",
    "priority": "SCHEDULER_E2E",
    "multi_target": "SCHEDULER_E2E",
    "switch": "SCHEDULER_E2E",
    "faint": "SCHEDULER_E2E",
    "experience": "SCHEDULER_E2E",
    "capture": "SCHEDULER_E2E",
}
E2E_ROUTES = set(EXPECTED_ROUTES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_stage() -> Path | None:
    source_sha256 = sha256(SOURCE)
    for path in dict.fromkeys(STAGE_CANDIDATES):
        metadata = path.with_suffix(".json")
        if not path.is_file() or not metadata.is_file():
            continue
        try:
            payload = json.loads(metadata.read_text(encoding="utf-8"))
            recorded_source = payload["fingerprint_inputs"]["files"][
                "tools/mgba_battle_core_smoke.c"
            ]["sha256"]
            recorded_rom = payload["output"]["sha256"]
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
        if recorded_source == source_sha256 and recorded_rom == sha256(path):
            return path
    return None


STAGE_ROM = current_stage()


def parse_hex_address(value: object) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9A-F]{8}", value):
        raise AssertionError(f"ROM address表現が不正です: {value!r}")
    return int(value, 16)


class BattleCoreSmokeSourceTests(unittest.TestCase):
    def test_reuses_reviewed_trace_and_is_read_only(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('#include "mgba_ai_fixture_runner.c"', source)
        self.assertIn("BATTLE_CORE_FIELD_TRACE_SEGMENTS = 233", source)
        self.assertIn("natural-new-game", source)
        self.assertIn("mCoreLoadFile", source)
        self.assertNotIn("mCoreLoadSaveFile", source)
        self.assertNotIn("fopen(argv[1], \"wb\")", source)
        self.assertIn("usage: %s ROM EXPECTED_ROM_SHA256", source)
        self.assertIn(r'\"read_only\":true', source)
        self.assertIn(r'\"artifacts_written\":[]', source)

    def test_normal_wild_and_trainer_use_real_setup_paths(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("BATTLE_CORE_START_WILD = 0x0807EE2D", source)
        self.assertIn("BATTLE_CORE_START_TRAINER = 0x0807FB85", source)
        self.assertIn("BATTLE_CORE_TRAINER_OPPONENT_A = 0x020385E2", source)
        self.assertIn("write16(core, BATTLE_CORE_TRAINER_OPPONENT_A, 328)", source)
        self.assertIn("create_mon_image(core, 4, 5", source)
        self.assertIn("create_mon_image(core, 10, 5", source)
        self.assertIn("create_mon_image(core, 7, 5", source)
        self.assertIn("call_bounded(core, BATTLE_CORE_START_WILD", source)
        self.assertIn("call_bounded(core, BATTLE_CORE_START_TRAINER", source)
        self.assertIn("execute_one_turn(core, selected_slot, 0)", source)
        self.assertIn("result.turn = execute_one_turn(core, 0, 0)", source)

    def test_all_gameplay_routes_claim_scheduler_e2e_only(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        for route, classification in EXPECTED_ROUTES.items():
            self.assertIn(f'{{"{route}", "{classification}"', source)
        self.assertIn("Toxic_status_battle_party_persistence_and_cleanup", source)
        self.assertIn("slower_Quick_Attack_precedes_faster_Tackle", source)
        self.assertIn("double_four_controller_spread_damage", source)
        self.assertIn("battle_command_party_menu_controller_switch", source)
        self.assertIn("battle_bag_master_ball_capture_cleanup", source)
        self.assertNotIn("route != ROUTE_PRIORITY", source)
        self.assertNotIn('"priority", "DIRECT_CALL_BOUNDED"', source)
        self.assertIn("bool executed_end_to_end = true", source)
        self.assertIn("BATTLE_CORE_DIRECT_CALL_LIMIT = 5000000", source)
        self.assertIn("payload_pc_seen", source)

    def test_status_priority_faint_exp_and_battle_kinds_use_scheduler(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("BATTLE_CORE_MOVE_SELECTION_CURSOR", source)
        self.assertIn("BATTLE_CORE_MOVE_TOXIC = 92", source)
        self.assertIn("BATTLE_CORE_STATUS_TOXIC = 0x80", source)
        self.assertIn("BATTLE_CORE_TYPE_POISON = 3", source)
        self.assertIn("types do not guarantee a legal status attempt", source)
        self.assertIn("result.opponent_party_status_after", source)
        self.assertIn("run_status_route", source)
        self.assertIn("status_cleared_on_faint", source)
        self.assertIn("BATTLE_CORE_MOVE_QUICK_ATTACK = 98", source)
        self.assertIn("run_priority_route", source)
        self.assertIn("result.player_speed = 10", source)
        self.assertIn("result.opponent_speed = 1000", source)
        self.assertIn("result.first_damage_dealt_by == 0", source)
        self.assertIn("result.turn_order[0] == 0", source)
        self.assertIn("run_faint_experience_end", source)
        self.assertIn("run_trainer_battle_end", source)
        self.assertIn("run_battle_win_end(core, field, true, false)", source)
        self.assertIn("result.experience_after <= result.experience_before", source)
        self.assertIn("result.outcome_seen != BATTLE_CORE_OUTCOME_WON", source)
        self.assertIn("battle end did not clear gNewBS runtime state", source)
        self.assertIn("BATTLE_CORE_BATTLE_OUTCOME = 0x02023DEA", source)

    def test_multi_target_uses_real_double_battlers_and_spread_damage(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("run_multi_target_double", source)
        self.assertIn("read32(core, ADDR_BATTLE_TYPE_FLAGS) | BATTLE_TYPE_DOUBLE", source)
        self.assertIn("result.battler_count == BATTLE_CORE_MAX_BATTLERS", source)
        self.assertIn("result.spread_move != 57", source)
        self.assertIn("result.opponent_hp_after[0] < result.opponent_hp_before[0]", source)
        self.assertIn("result.opponent_hp_after[1] < result.opponent_hp_before[1]", source)

    def test_switch_and_capture_use_real_ui_controller_paths(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("run_switch_menu", source)
        self.assertIn("BATTLE_CORE_ACTION_SWITCH", source)
        self.assertIn("BATTLE_CORE_SWITCH_MENU_PRESSES = 3", source)
        self.assertIn("press < BATTLE_CORE_SWITCH_MENU_PRESSES", source)
        self.assertIn("result.frames = BATTLE_CORE_SWITCH_MENU_PRESSES", source)
        self.assertIn("result.party_menu_opened", source)
        self.assertIn("result.party_index_after != 1", source)
        self.assertIn("run_capture_menu", source)
        self.assertIn("BATTLE_CORE_ADD_BAG_ITEM", source)
        self.assertIn("BATTLE_CORE_BAG_BALL_POCKET", source)
        self.assertIn("result.outcome_seen != BATTLE_CORE_OUTCOME_CAUGHT", source)
        self.assertIn("result.ball_consumed", source)
        self.assertIn(r'\"unreached_routes\":[]', source)
        self.assertIn(r'\"non_e2e_routes\":[]', source)
        self.assertIn(r'\"all_routes_scheduler_e2e\":true', source)

    def test_debug_scheduler_trace_and_observation_stderr_are_removed(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("debug_scheduler", source)
        self.assertNotIn("trace prefix=", source)
        self.assertNotIn("debug trainer=", source)
        self.assertNotIn("task %s id=", source)

    def test_canonical_move_and_repeatability_contract_is_explicit(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("BATTLE_CORE_CANONICAL_MOVE_COUNT = 1063", source)
        self.assertIn("BATTLE_CORE_CANONICAL_MOVE_MAX = 1062", source)
        self.assertIn("BATTLE_CORE_BATTLE_MOVE_SIZE = 12", source)
        self.assertIn("for (unsigned run = 0; run < 2; ++run)", source)
        self.assertIn("two internal battle-core fixture runs differ", source)
        self.assertIn(r'\"internal_runs\":2', source)
        self.assertIn(r'\"status_identical\":true', source)
        self.assertIn(r'\"priority_identical\":true', source)
        self.assertIn(r'\"trainer_end_identical\":true', source)
        self.assertIn(r'\"multi_target_identical\":true', source)
        self.assertIn(r'\"switch_identical\":true', source)
        self.assertIn(r'\"capture_identical\":true', source)

    def test_stale_stage_is_not_selected_for_live_acceptance(self) -> None:
        if STAGE_ROM is not None:
            self.assertEqual(
                json.loads(STAGE_ROM.with_suffix(".json").read_text(encoding="utf-8"))[
                    "fingerprint_inputs"
                ]["files"]["tools/mgba_battle_core_smoke.c"]["sha256"],
                sha256(SOURCE),
            )
            return
        existing = [path for path in dict.fromkeys(STAGE_CANDIDATES) if path.is_file()]
        if not existing:
            self.skipTest("T06 stage has not been generated")
        self.assertTrue(existing)

    def test_runner_compiles_with_werror(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("C compiler is unavailable")
        with tempfile.TemporaryDirectory(prefix="t06-battle-core-source-") as raw:
            executable = Path(raw) / "mgba_battle_core_smoke"
            completed = subprocess.run(
                [
                    compiler,
                    "-std=c11",
                    "-O2",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    str(SOURCE),
                    "-o",
                    str(executable),
                    "-lmgba",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(
                completed.returncode,
                0,
                f"runner compile failed:\n{completed.stdout}{completed.stderr}",
            )


@unittest.skipUnless(STAGE_ROM is not None, "fixed T06 battle-core stage ROM is unavailable")
class FixedStageBattleCoreSmokeTests(unittest.TestCase):
    _temporary: tempfile.TemporaryDirectory[str]
    _runner: Path
    _rom_sha256: str

    @classmethod
    def setUpClass(cls) -> None:
        assert STAGE_ROM is not None
        compiler = shutil.which("cc")
        if compiler is None:
            raise unittest.SkipTest("C compiler is unavailable")
        cls._temporary = tempfile.TemporaryDirectory(prefix="t06-battle-core-live-")
        cls._runner = Path(cls._temporary.name) / "mgba_battle_core_smoke"
        cls._rom_sha256 = sha256(STAGE_ROM)
        completed = subprocess.run(
            [
                compiler,
                "-std=c11",
                "-O2",
                "-Wall",
                "-Wextra",
                "-Werror",
                str(SOURCE),
                "-o",
                str(cls._runner),
                "-lmgba",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(f"runner compile failed:\n{completed.stdout}{completed.stderr}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    @classmethod
    def run_once(cls) -> tuple[str, dict[str, object]]:
        assert STAGE_ROM is not None
        workdir = Path(cls._temporary.name)
        before = {path.relative_to(workdir) for path in workdir.rglob("*") if path.is_file()}
        environment = {
            "HOME": cls._temporary.name,
            "LC_ALL": "C",
            "LANG": "C",
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "TZ": "UTC",
        }
        completed = subprocess.run(
            [str(cls._runner), str(STAGE_ROM), cls._rom_sha256],
            cwd=workdir,
            env=environment,
            text=True,
            capture_output=True,
            timeout=240,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"runner failed: rc={completed.returncode}\n"
                f"stdout={completed.stdout}\nstderr={completed.stderr}"
            )
        if completed.stderr:
            raise AssertionError(f"runner emitted stderr: {completed.stderr}")
        lines = completed.stdout.splitlines()
        if len(lines) != 1:
            raise AssertionError(f"runner output is not one JSON line: {completed.stdout!r}")
        payload = json.loads(lines[0])
        after = {path.relative_to(workdir) for path in workdir.rglob("*") if path.is_file()}
        if after != before:
            raise AssertionError(f"runner retained artifacts: {sorted(after - before)}")
        return completed.stdout, payload

    def assert_call(self, value: object) -> None:
        self.assertIsInstance(value, dict)
        assert isinstance(value, dict)
        self.assertTrue(value["bounded"])
        self.assertEqual(value["instruction_limit"], 5_000_000)
        self.assertGreater(value["instructions"], 0)
        self.assertLessEqual(value["instructions"], value["instruction_limit"])
        self.assertTrue(value["payload_pc_seen"])

    def assert_battle(self, value: object, kind: str) -> None:
        self.assertIsInstance(value, dict)
        assert isinstance(value, dict)
        self.assertEqual(value["kind"], kind)
        self.assertEqual(value["setup_frames"], 360)
        self.assertEqual(value["active_battlers"], 2)
        self.assertEqual(value["absent_flags"], 0)
        self.assertRegex(value["ewram_iwram_fnv1a64"], re.compile(r"^[0-9a-f]{16}$"))
        self.assertEqual(
            value["runtime_initialized"],
            {"gNewBS": True, "gBattleStruct": True, "gBattleResources": True},
        )
        self.assert_call(value["setup_call"])
        battlers = value["battlers"]
        self.assertEqual(len(battlers), 2)
        trainer = kind == "TRAINER"
        expected_species = (
            [7, 4] if trainer else [29, 10] if kind == "WILD_STATUS" else [4, 10]
        )
        self.assertEqual([row["species"] for row in battlers], expected_species)
        for row in battlers:
            self.assertGreater(row["hp"], 0)
            self.assertGreater(row["level"], 0)
            self.assertEqual(len(row["moves"]), 4)
            self.assertEqual(len(row["pp"]), 4)
            populated = 0
            for move, pp in zip(row["moves"], row["pp"], strict=True):
                if move == 0:
                    continue
                populated += 1
                self.assertLessEqual(move, CANONICAL_MOVE_MAX)
                self.assertGreater(pp, 0)
            self.assertGreater(populated, 0)
        self.assertEqual(value["trainer_flag"], trainer)
        self.assertEqual(bool(value["battle_type_flags"] & BATTLE_TYPE_TRAINER), trainer)
        self.assertEqual(value["trainer_id"], 328 if trainer else 0)
        self.assertEqual(
            value["direct_setup"],
            "0x0807FB85" if trainer else "0x0807EE2D",
        )

        turn = value["turn"]
        self.assertEqual(turn["input"], "A_x6")
        self.assertEqual(turn["frames"], 1272)
        self.assertTrue(turn["pp_spent"])
        self.assertEqual(turn["pp_after"], turn["pp_before"] - 1)
        self.assertEqual(turn["outcome_before"], 0)
        self.assertEqual(turn["outcome_after"], 0)
        if kind == "WILD_STATUS":
            self.assertEqual(turn["selected_slot"], 0)
            self.assertEqual(turn["selected_move"], 92)
            self.assertTrue(turn["status_applied"])
            self.assertEqual(turn["opponent_status_before"], 0)
            self.assertEqual(turn["opponent_party_status_before"], 0)
            self.assertTrue(turn["opponent_status_after"] & 0x80)
            self.assertTrue(turn["opponent_party_status_after"] & 0x80)
            self.assertEqual(
                turn["opponent_status_after"] & 0x80,
                turn["opponent_party_status_after"] & 0x80,
            )
        else:
            self.assertEqual(turn["selected_slot"], 0)
            self.assertTrue(turn["hp_changed"])

    def assert_payload(self, payload: dict[str, object]) -> None:
        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["fixture"], "t06_battle_core_scheduler_v3")
        self.assertEqual(payload["rom_sha256"], self._rom_sha256)
        self.assertEqual(payload["fixed_rtc_unix"], 946684800)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["boot_trace_segments"], 233)
        self.assertEqual(payload["warnings_errors"], 0)
        self.assertEqual(payload["artifacts_written"], [])

        move_contract = payload["canonical_move_contract"]
        self.assertEqual(move_contract["count"], 1063)
        self.assertEqual(move_contract["max_id"], CANONICAL_MOVE_MAX)
        self.assertEqual(move_contract["stride"], 12)
        table_pointer = parse_hex_address(move_contract["table_pointer"])
        self.assertGreaterEqual(table_pointer, 0x08000000)
        self.assertLess(table_pointer + 1063 * 12, 0x0A000001)
        self.assertGreater(move_contract["status_moves"], 0)
        self.assertGreater(move_contract["priority_moves"], 0)
        self.assertGreater(move_contract["multi_target_moves"], 0)

        for setup in payload["setup_hooks"].values():
            target = parse_hex_address(setup["target"])
            self.assertGreaterEqual(target & ~1, PAYLOAD_START)
            self.assertLess(target & ~1, PAYLOAD_END)
            self.assertIn(setup["stub_size"], (8, 10))

        routes = {row["route"]: row for row in payload["route_fixtures"]}
        self.assertEqual(set(routes), set(EXPECTED_ROUTES))
        for name, classification in EXPECTED_ROUTES.items():
            row = routes[name]
            self.assertEqual(row["classification"], classification)
            self.assertEqual(row["executed_end_to_end"], name in E2E_ROUTES)
            self.assertGreater(row["evidence_count"], 0)
            target = parse_hex_address(row["hook_target"])
            self.assertGreaterEqual(target & ~1, PAYLOAD_START)
            self.assertLess(target & ~1, PAYLOAD_END)
            self.assertFalse(row["direct_call_bounded"])

        self.assert_battle(payload["battles"]["wild"], "WILD")
        self.assert_battle(payload["battles"]["trainer"], "TRAINER")
        self.assert_battle(payload["battles"]["status"], "WILD_STATUS")

        status_completion = payload["status_completion"]
        self.assertEqual(status_completion["outcome_seen"], 1)
        self.assertTrue(status_completion["enemy_fainted_seen"])
        self.assertEqual(status_completion["status_mask"], 0x80)
        self.assertEqual(status_completion["party_status_after_cleanup"] & 0x80, 0)
        self.assertTrue(status_completion["status_cleared_on_faint"])
        self.assertTrue(status_completion["battle_runtime_cleaned"])
        self.assertGreater(status_completion["cleanup_frames"], 0)

        priority = payload["priority"]
        self.assertEqual(priority["kind"], "WILD_PRIORITY_ORDER")
        self.assertEqual(priority["priority_move"], 98)
        self.assertEqual(priority["alternative_move"], 33)
        self.assertEqual(priority["opponent_move"], 33)
        self.assertGreater(
            priority["priority_value"], priority["opponent_priority_value"]
        )
        self.assertLess(priority["player_speed"], priority["opponent_speed"])
        self.assertEqual(priority["turn_order"], [0, 1])
        self.assertEqual(priority["first_damage_dealt_by"], 0)
        self.assertEqual(
            priority["player_pp_after"], priority["player_pp_before"] - 1
        )
        self.assertEqual(
            priority["opponent_pp_after"], priority["opponent_pp_before"] - 1
        )
        self.assertLess(priority["player_hp_after"], priority["player_hp_before"])
        self.assertLess(
            priority["opponent_hp_after"], priority["opponent_hp_before"]
        )
        self.assertTrue(priority["selected_through_controller"])
        self.assertTrue(priority["both_moves_executed"])
        self.assertTrue(priority["slower_priority_user_moved_first"])
        self.assert_call(priority["setup_call"])

        wild_end = payload["battle_end"]["wild"]
        self.assertEqual(wild_end["kind"], "WILD_WIN")
        self.assertFalse(wild_end["trainer"])
        self.assertEqual(wild_end["outcome_seen"], 1)
        self.assertTrue(wild_end["enemy_fainted_seen"])
        self.assertTrue(wild_end["experience_checked"])
        self.assertTrue(wild_end["experience_increased"])
        self.assertGreater(
            wild_end["experience_after"], wild_end["experience_before"]
        )
        self.assertTrue(wild_end["battle_runtime_initialized"])
        self.assertTrue(wild_end["battle_runtime_cleaned"])
        self.assert_call(wild_end["setup_call"])

        trainer_end = payload["battle_end"]["trainer"]
        self.assertEqual(trainer_end["kind"], "TRAINER_WIN")
        self.assertTrue(trainer_end["trainer"])
        self.assertEqual(trainer_end["outcome_seen"], 1)
        self.assertTrue(trainer_end["enemy_fainted_seen"])
        self.assertFalse(trainer_end["experience_checked"])
        self.assertTrue(trainer_end["battle_runtime_initialized"])
        self.assertTrue(trainer_end["battle_runtime_cleaned"])
        self.assert_call(trainer_end["setup_call"])

        multi_target = payload["multi_target"]
        self.assertEqual(multi_target["kind"], "WILD_DOUBLE")
        self.assertEqual(multi_target["active_battlers"], 4)
        self.assertTrue(multi_target["battle_type_flags"] & BATTLE_TYPE_DOUBLE)
        self.assertTrue(multi_target["four_controllers_initialized"])
        self.assertEqual(multi_target["species"], [4, 10, 7, 11])
        self.assertEqual(multi_target["party_indexes"], [0, 0, 1, 1])
        self.assertEqual(multi_target["spread_move"], 57)
        self.assertEqual(
            multi_target["spread_pp_after"], multi_target["spread_pp_before"] - 1
        )
        self.assertTrue(multi_target["both_opponents_hit"])
        for before, after in zip(
            multi_target["opponent_hp_before"],
            multi_target["opponent_hp_after"],
            strict=True,
        ):
            self.assertLess(after, before)
        self.assert_call(multi_target["setup_call"])

        switch = payload["switch"]
        self.assertEqual(switch["kind"], "PARTY_MENU_SWITCH")
        self.assertEqual(switch["chosen_action"], 2)
        self.assertEqual(switch["selected_party_mon"], 1)
        self.assertEqual(switch["species_before"], 4)
        self.assertEqual(switch["species_after"], 7)
        self.assertEqual(switch["party_index_before"], 0)
        self.assertEqual(switch["party_index_after"], 1)
        self.assertTrue(switch["party_menu_opened"])
        self.assertTrue(switch["controller_returned"])
        self.assertNotEqual(switch["battle_callback"], switch["party_menu_callback"])
        parse_hex_address(switch["battle_callback"])
        parse_hex_address(switch["party_menu_callback"])
        self.assert_call(switch["setup_call"])

        capture = payload["capture"]
        self.assertEqual(capture["kind"], "MASTER_BALL_CAPTURE")
        self.assertEqual(capture["chosen_action"], 1)
        self.assertEqual(capture["outcome_seen"], 7)
        self.assertEqual(capture["party_count_before"], 1)
        self.assertEqual(capture["party_count_after"], 2)
        self.assertEqual(capture["captured_species"], 10)
        self.assertTrue(capture["bag_opened"])
        self.assertTrue(capture["ball_consumed"])
        self.assertTrue(capture["battle_runtime_initialized"])
        self.assertTrue(capture["battle_runtime_cleaned"])
        self.assertEqual(capture["add_ball"]["item"], 1)
        self.assertEqual(capture["add_ball"]["count"], 1)
        self.assertEqual(capture["add_ball"]["result"], 1)
        self.assertGreater(capture["add_ball"]["instructions"], 0)
        self.assert_call(capture["setup_call"])
        self.assertEqual(
            payload["repeatability"],
            {
                "internal_runs": 2,
                "wild_identical": True,
                "trainer_identical": True,
                "status_identical": True,
                "priority_identical": True,
                "wild_end_identical": True,
                "trainer_end_identical": True,
                "multi_target_identical": True,
                "switch_identical": True,
                "capture_identical": True,
            },
        )
        self.assertEqual(
            payload["claims"],
            {
                "wild_trainer_setup_executed": True,
                "wild_trainer_turn_executed": True,
                "wild_trainer_completion_executed": True,
                "status_apply_and_faint_clear_e2e": True,
                "faint_exp_end_executed": True,
                "priority_scheduler_order_e2e": True,
                "multi_target_double_e2e": True,
                "party_menu_switch_e2e": True,
                "bag_ball_capture_e2e": True,
                "all_routes_scheduler_e2e": True,
                "cfru_payload_pc_executed": True,
            },
        )
        self.assertEqual(payload["unreached_routes"], [])
        self.assertEqual(payload["non_e2e_routes"], [])

    def test_stage_is_json_only_and_two_process_deterministic(self) -> None:
        first_stdout, first = self.run_once()
        second_stdout, second = self.run_once()
        self.assertEqual(first_stdout, second_stdout)
        self.assertEqual(first, second)
        self.assert_payload(first)

    def test_wrong_rom_hash_fails_before_emulation(self) -> None:
        assert STAGE_ROM is not None
        completed = subprocess.run(
            [str(self._runner), str(STAGE_ROM), "0" * 64],
            cwd=self._temporary.name,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn("ROM SHA-256 mismatch", completed.stderr)


if __name__ == "__main__":
    unittest.main()
