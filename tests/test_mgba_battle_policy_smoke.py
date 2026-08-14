#!/usr/bin/env python3
"""T06 policy/integrationを最終ROMで実行するlibmGBA限定acceptance。"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/mgba_battle_policy_smoke.c"
STAGE_CANDIDATES = [
    ROOT / "build/stages/06_battle_core.gba",
    ROOT / "build/stages/06_battle.gba",
    *sorted((ROOT / "build/stages").glob("06*.gba")),
]

REQUIRED_SYMBOLS = (
    "cfru_integration_stat_inputs_are_valid",
    "cfru_integration_effective_nature",
    "cfru_integration_effective_iv",
    "cfru_integration_ability_slot",
    "cfru_integration_receives_battle_exp",
    "cfru_integration_apply_exp_candy",
    "cfru_integration_trainer_build_apply",
    "VegaConfigureNextBattlePolicy",
    "VegaConfigureNextFacility",
    "VegaConfigureNextMirageItem",
    "VegaConfigureNextRaid",
    "VegaBattlePolicyEnd",
    "VegaFacilityStateIsActive",
    "VegaFacilityStateGet",
    "VegaFacilityStateSet",
    "VegaBattlePolicyCanMega",
    "VegaBattlePolicyMarkMega",
    "VegaBattlePolicyCanZ",
    "VegaBattlePolicyMarkZ",
    "VegaBattlePolicyCanDynamax",
    "VegaBattlePolicyMarkDynamax",
    "VegaBattlePolicyCanTera",
    "VegaBattlePolicyMarkTera",
    "cfru_integration_mechanic_can_use",
    "cfru_integration_mechanic_try_use",
    "cfru_integration_mechanic_is_forced",
    "cfru_integration_persistent_effect_allowed",
    "cfru_integration_mirage_current",
    "cfru_integration_mirage_set_battle_value",
    "cfru_integration_raid_begin",
    "cfru_integration_raid_partner_is_active",
    "cfru_integration_raid_shields_remaining",
    "cfru_integration_raid_break_shield",
    "cfru_integration_raid_set_boss_hp",
    "cfru_integration_raid_advance_turn",
    "cfru_integration_raid_try_capture",
    "cfru_integration_raid_end",
    "GetNumRaidShieldsUp",
    "IsRaidBattle",
    "IsCatchableRaidBattle",
    "sp067_GenerateRandomBattleTowerTeam",
    "HandleInputChooseAction",
    "HandleInputChooseMove",
    "HandleInputChooseTarget",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _integration_symbols(metadata: dict[str, object]) -> dict[str, int] | None:
    runs = metadata.get("upstream_runs")
    if not isinstance(runs, list) or not runs or not isinstance(runs[0], dict):
        return None
    raw = runs[0].get("integration_symbols")
    if not isinstance(raw, dict):
        return None
    result: dict[str, int] = {}
    for name in REQUIRED_SYMBOLS:
        value = raw.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0x09000000 <= value < 0x09200000
            or value & 1
        ):
            return None
        result[name] = value
    return result


def current_stage() -> tuple[Path, dict[str, int]] | None:
    source_sha256 = sha256(SOURCE)
    for path in dict.fromkeys(STAGE_CANDIDATES):
        metadata_path = path.with_suffix(".json")
        if not path.is_file() or not metadata_path.is_file():
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            recorded_source = metadata["fingerprint_inputs"]["files"][
                "tools/mgba_battle_policy_smoke.c"
            ]["sha256"]
            recorded_rom = metadata["output"]["sha256"]
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
        symbols = _integration_symbols(metadata)
        if (
            recorded_source == source_sha256
            and recorded_rom == sha256(path)
            and symbols is not None
        ):
            return path, symbols
    return None


CURRENT_STAGE = current_stage()


class BattlePolicySmokeSourceTests(unittest.TestCase):
    def test_embeds_reviewed_battle_fixture_and_remains_read_only(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("#define BATTLE_CORE_EMBEDDED", source)
        self.assertIn('#include "mgba_battle_core_smoke.c"', source)
        self.assertIn("run_trace_prefix(core)", source)
        self.assertIn("policy_start_configured_trainer", source)
        self.assertIn("core, BATTLE_CORE_START_WILD, 0, 0, 0, 0", source)
        self.assertIn("core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0", source)
        self.assertIn("mCoreLoadFile", source)
        self.assertNotIn("mCoreLoadSaveFile", source)
        self.assertNotIn('fopen(argv[1], "wb")', source)
        self.assertIn(r'\"read_only\":true', source)
        self.assertIn(r'\"artifacts_written\":[]', source)

    def test_all_runtime_symbols_are_explicit_fail_closed_inputs(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        for symbol in REQUIRED_SYMBOLS:
            self.assertIn(f'"{symbol}"', source)
        self.assertIn("required policy symbol argument is missing", source)
        self.assertIn("unknown policy symbol argument", source)
        self.assertIn("duplicate policy symbol argument", source)
        self.assertIn("value < BATTLE_CORE_PAYLOAD_START", source)
        self.assertIn("value >= BATTLE_CORE_PAYLOAD_END", source)
        self.assertIn("bounded policy call exceeded instruction limit", source)
        self.assertIn("payload_pc_seen", source)

    def test_stat_candy_and_trainer_build_contracts_are_real_rom_calls(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("policy_test_stat_inputs", source)
        self.assertIn("EXP Share enabled semantics differ", source)
        self.assertIn("hyper-trained speed", source)
        self.assertIn("policy_test_candy", source)
        self.assertIn("EXP candy selected-target isolation differs", source)
        self.assertIn("EXP candy cap/clamp semantics differ", source)
        self.assertIn("at-cap EXP candy should not consume", source)
        self.assertIn("policy_test_trainer_build", source)
        self.assertIn("unspecified trainer-build fields lost identity", source)
        self.assertIn("fully specified trainer-build IV/EV semantics differ", source)

    def test_mechanic_and_facility_matrix_use_actual_battle_contexts(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("POLICY_MECHANIC_FIRST = 1", source)
        self.assertIn("POLICY_MECHANIC_LAST = 4", source)
        self.assertIn("mechanic side-wide/one-use gate differs", source)
        self.assertIn("simultaneous mechanic was not excluded", source)
        self.assertIn("mechanic state leaked after battle cleanup", source)
        self.assertIn("POLICY_FACILITY_FORMAT_COUNT = 3", source)
        self.assertIn("POLICY_FACILITY_RULE_COUNT = 8", source)
        self.assertIn("policy_start_facility_trainer", source)
        self.assertIn("core, BATTLE_CORE_START_TRAINER, 0, 0, 0, 0", source)
        self.assertIn("format == 0 ? 2 : 4", source)
        self.assertIn("facility format did not initialize real battle controllers", source)
        self.assertIn("facility format/rule/flag state differs", source)
        self.assertIn("POLICY_BATTLE_TYPE_FRONTIER", source)
        self.assertIn("facility allowed a persistent battle effect", source)
        self.assertIn("actual facility faint/end leaked EXP or held-item mutation", source)
        self.assertIn("sp067_GenerateRandomBattleTowerTeam", source)
        self.assertIn("rental generator produced fewer than three mons", source)

    def test_mirage_and_raid_cover_natural_scheduler_completion(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("exit_path < POLICY_EXIT_COUNT", source)
        self.assertIn("pending Mirage opponent item was not isolated in the actual battle", source)
        self.assertIn("Mirage opponent item leaked on a battle exit path", source)
        mirage_body = source.split("static void policy_test_mirage", 1)[1].split(
            "static void policy_sample_raid_end", 1
        )[0]
        self.assertIn("ADDR_ENEMY_PARTY", mirage_body)
        self.assertIn("ADDR_PLAYER_PARTY", mirage_body)
        self.assertIn("ADDR_BATTLE_MONS + BATTLE_MON_SIZE", mirage_body)
        self.assertIn("pending Raid did not initialize the existing three-controller UI path", source)
        self.assertIn("Raid shield count above the fixed UI limit was accepted", source)
        self.assertIn("policy_test_raid_scheduler_e2e", source)
        scheduler_body = source.split(
            "static struct RaidEndEvidence policy_test_raid_scheduler_e2e", 1
        )[1].split("static void policy_test_raid_contracts", 1)[0]
        self.assertIn("policy_run_raid_controller_round", scheduler_body)
        self.assertIn("BATTLE_CORE_ACTION_SELECTION_CURSOR", scheduler_body)
        self.assertIn("BATTLE_CORE_MOVE_SELECTION_CURSOR", source)
        self.assertIn("BATTLE_CORE_BAG_STATE", source)
        self.assertIn("POLICY_G_SAVE_BLOCK3_POINTER = 0x03005050", source)
        self.assertIn("POLICY_PC_BOX_MON_SIZE = 80", source)
        self.assertIn("POLICY_G_RAID_BATTLE_STARS = 0x0203DFC6", source)
        self.assertIn("POLICY_SIX_STAR_RAID = 6", source)
        raid_start_body = source.split(
            "static struct CallObservation policy_start_raid_wild", 1
        )[1].split("static void policy_finish_direct", 1)[0]
        self.assertIn(
            "policy_prepare_raid_party_fixture(core, pc_fixture)", raid_start_body
        )
        self.assertIn(
            "policy_prepare_raid_pc_fixture(core, pc_fixture)", raid_start_body
        )
        self.assertLess(
            raid_start_body.index("policy_prepare_raid_party_fixture(core"),
            raid_start_body.index("BATTLE_CORE_START_WILD"),
        )
        self.assertGreater(
            raid_start_body.index("policy_prepare_raid_pc_fixture(core"),
            raid_start_body.index("BATTLE_CORE_START_WILD"),
        )
        self.assertLess(
            raid_start_body.index("policy_prepare_raid_pc_fixture(core"),
            raid_start_body.index(
                "Raid partner spread moves/PP changed before controller input"
            ),
        )
        self.assertIn(
            "write8(core, POLICY_G_RAID_BATTLE_STARS, POLICY_SIX_STAR_RAID)",
            raid_start_body,
        )
        self.assertNotIn("debug direct build", raid_start_body)
        self.assertNotIn("debug early Raid passed", source)
        party_fixture_body = source.split(
            "static void policy_prepare_raid_party_fixture", 1
        )[1].split(
            "static void policy_prepare_raid_pc_fixture", 1
        )[0]
        pc_helper_body = source.split(
            "static void policy_prepare_raid_pc_fixture", 1
        )[1].split(
            "static struct CallObservation policy_start_raid_wild", 1
        )[0]
        self.assertNotIn("BATTLE_CORE_GET_MON_DATA", pc_helper_body)
        self.assertNotIn("POLICY_GET_BOX_MON_DATA_AT", source)
        self.assertIn("slot_address + POLICY_PC_BOX_MON_SPECIES_OFFSET", pc_helper_body)
        pc_verify_body = pc_helper_body.split(
            "static void policy_verify_raid_pc_capture", 1
        )[1]
        self.assertIn(
            "ADDR_PLAYER_PARTY + slot * POKEMON_SIZE\n"
            "                + POLICY_PC_BOX_MON_SPECIES_OFFSET",
            party_fixture_body,
        )
        self.assertIn(
            "policy_verify_raid_pc_capture(core, &pc_fixture, &evidence)",
            scheduler_body,
        )
        self.assertIn(
            "Raid full-party capture did not use the stock 80-byte PC ABI",
            source,
        )
        self.assertNotIn("0x0202924C", source)
        self.assertIn("real controller attacks did not deplete all five Raid UI shields", source)
        self.assertIn("policy_raid_partner_moves", source)
        self.assertIn("policy_raid_partner_pp", source)
        self.assertIn("115, 123, 127, 128, 131, 143", source)
        self.assertIn("core, policy_raid_player_species[slot], 30", source)
        self.assertIn("{202, 188, 73, 182}", source)
        self.assertIn("{53, 126, 332, 182}", source)
        self.assertIn("{55, 58, 352, 182}", source)
        self.assertIn("partner < 3", source)
        self.assertIn("slot < BATTLE_CORE_MOVE_SLOTS", source)
        self.assertIn("Raid partner spread moves/PP changed before controller input", source)
        self.assertIn("Raid partner party-to-BattleMon moves/PP ABI differs", source)
        self.assertIn("Raid runtime disappeared before a natural outcome", source)
        self.assertIn(r'\"partner_spread_moves_preserved\":%s', source)
        self.assertLess(
            raid_start_body.index(
                "Raid partner spread moves/PP changed before controller input"
            ),
            raid_start_body.index("run_key_frames(core, 1, 2)"),
        )
        self.assertIn("POLICY_NEWBS_RAID_TURNS_ELAPSED_OFFSET", source)
        self.assertIn("POLICY_CONTROLLER_PRINT_STRING = 0x08035959", source)
        controller_body = source.split(
            "static void policy_run_raid_controller_round", 1
        )[1].split("static bool policy_normal_battle_after_raid", 1)[0]
        self.assertNotIn("++evidence->controller_turns", controller_body)
        self.assertIn("real Raid controller damage did not reach the boss capture phase", source)
        self.assertIn("Raid existing-UI capture/end path did not naturally clean up", source)
        self.assertIn("Raid flag/state leaked into a subsequent normal battle", source)
        self.assertIn("POLICY_CB2_OVERWORLD = 0x08055E75", source)
        self.assertIn("POLICY_CB2_EVOLUTION_SCENE_UPDATE = 0x080CF869", source)
        self.assertIn("post-Raid field callback did not become ready", source)
        self.assertIn("POLICY_FIELD_RETURN_INPUT_PULSES = 30", source)
        normal_after_raid = source.split(
            "static bool policy_normal_battle_after_raid", 1
        )[1].split("static struct RaidEndEvidence policy_test_raid_scheduler_e2e", 1)[0]
        self.assertIn("run_key_frames(core, 1, 2)", normal_after_raid)
        self.assertLess(
            normal_after_raid.index("POLICY_CB2_EVOLUTION_SCENE_UPDATE"),
            normal_after_raid.index("clear_parties(core)"),
        )
        self.assertIn("policy_test_raid_turn_limit_scheduler", source)
        self.assertIn("no-capture one-turn Raid setup semantics differ", source)
        turn_limit_body = source.split(
            "static bool policy_test_raid_turn_limit_scheduler", 1
        )[1].split("static void policy_test_raid_contracts", 1)[0]
        for forbidden in (
            "symbols->raid_begin",
            "symbols->raid_break",
            "symbols->raid_hp",
            "symbols->raid_turn",
            "symbols->raid_capture",
            "symbols->raid_end",
            "symbols->policy_end",
        ):
            self.assertNotIn(forbidden, scheduler_body)
            self.assertNotIn(forbidden, turn_limit_body)
        self.assertIn("Raid fixed-UI shield depletion semantics differ", source)
        self.assertIn("Raid boss/partner/shield/capture/cleanup semantics differ", source)
        self.assertIn("Raid turn-limit/no-capture cleanup semantics differ", source)
        self.assertIn(r'\"raid_state_completion_scheduler_e2e\":true', source)
        self.assertIn(r'\"pc_storage_pointer_dynamic\":%s', source)
        self.assertIn(r'\"full_party_pc_routed\":%s', source)
        self.assertIn(r'\"pc_captured_species\":%u', source)
        self.assertIn(r'\"party_species_unchanged\":%s', source)
        self.assertIn(r'\"stock_pc_box_stride_80\":%s', source)
        self.assertIn(r'\"adjacent_pc_slot_unchanged\":%s', source)
        self.assertIn(r'\"non_e2e_routes\":[]', source)
        self.assertIn(r'\"unreached_routes\":[]', source)

    def test_compiles_warning_free_when_mgba_is_available(self) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            self.skipTest("C compiler is unavailable")
        with tempfile.TemporaryDirectory(prefix="t06-policy-compile-") as raw:
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
                    str(Path(raw) / "runner"),
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


@unittest.skipUnless(
    CURRENT_STAGE is not None,
    "current T06 policy-smoke-fingerprinted stage ROM is unavailable",
)
class FixedStageBattlePolicySmokeTests(unittest.TestCase):
    _temporary: tempfile.TemporaryDirectory[str]
    _runner: Path
    _rom: Path
    _rom_sha256: str
    _symbols: dict[str, int]

    @classmethod
    def setUpClass(cls) -> None:
        assert CURRENT_STAGE is not None
        compiler = shutil.which("cc")
        if compiler is None:
            raise unittest.SkipTest("C compiler is unavailable")
        cls._rom, cls._symbols = CURRENT_STAGE
        cls._rom_sha256 = sha256(cls._rom)
        cls._temporary = tempfile.TemporaryDirectory(prefix="t06-policy-live-")
        cls._runner = Path(cls._temporary.name) / "mgba_battle_policy_smoke"
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
        if completed.returncode:
            raise AssertionError(
                f"runner compile failed:\n{completed.stdout}{completed.stderr}"
            )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    @classmethod
    def command(cls, expected_hash: str | None = None) -> list[str]:
        return [
            str(cls._runner),
            str(cls._rom),
            cls._rom_sha256 if expected_hash is None else expected_hash,
            *(f"{name}=0x{cls._symbols[name]:08X}" for name in REQUIRED_SYMBOLS),
        ]

    @classmethod
    def run_once(cls) -> tuple[str, dict[str, object]]:
        workdir = Path(cls._temporary.name)
        before = {
            path.relative_to(workdir)
            for path in workdir.rglob("*")
            if path.is_file()
        }
        environment = {
            "HOME": cls._temporary.name,
            "LC_ALL": "C",
            "LANG": "C",
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "TZ": "UTC",
        }
        completed = subprocess.run(
            cls.command(),
            cwd=workdir,
            env=environment,
            text=True,
            capture_output=True,
            timeout=600,
            check=False,
        )
        if completed.returncode:
            raise AssertionError(
                f"runner failed: rc={completed.returncode}\n"
                f"stdout={completed.stdout}\nstderr={completed.stderr}"
            )
        if completed.stderr:
            raise AssertionError(f"runner emitted stderr: {completed.stderr}")
        lines = completed.stdout.splitlines()
        if len(lines) != 1:
            raise AssertionError(
                f"runner output is not one JSON line: {completed.stdout!r}"
            )
        payload = json.loads(lines[0])
        after = {
            path.relative_to(workdir)
            for path in workdir.rglob("*")
            if path.is_file()
        }
        if after != before:
            raise AssertionError(f"runner retained artifacts: {sorted(after - before)}")
        return completed.stdout, payload

    def assert_payload(self, payload: dict[str, object]) -> None:
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["fixture"], "t06_battle_policy_integration_v1")
        self.assertEqual(payload["rom_sha256"], self._rom_sha256)
        self.assertEqual(payload["fixed_rtc_unix"], 946684800)
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["boot_trace_segments"], 233)
        self.assertEqual(payload["warnings_errors"], 0)
        self.assertGreater(payload["direct_calls"], 200)
        self.assertEqual(payload["payload_calls"], payload["direct_calls"])
        self.assertGreater(payload["direct_call_instructions"], payload["direct_calls"])
        self.assertEqual(payload["actual_battle_setups"], 41)

        self.assertEqual(
            payload["stat_inputs"],
            {
                "exp_share_off_participant_only": True,
                "exp_share_on_unparticipated": True,
                "mint_nature": 6,
                "ability_slot": 2,
                "hyper_trained_iv": 31,
            },
        )
        self.assertEqual(
            payload["exp_candy"],
            {
                "selected_target_only": True,
                "zero_no_effect_not_consumed": True,
                "cap_clamped": True,
                "at_cap_not_consumed": True,
            },
        )
        self.assertEqual(
            payload["trainer_build"],
            {
                "fully_specified": True,
                "unspecified_identity": True,
                "ev_total": 510,
            },
        )
        self.assertEqual(payload["mechanics"]["modes"], ["MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL"])
        for key in ("side_wide_exclusive", "one_use", "cross_mode_exclusive", "cleanup"):
            self.assertTrue(payload["mechanics"][key])

        facility = payload["facility"]
        self.assertEqual(facility["formats"], 3)
        self.assertEqual(facility["rules"], 8)
        self.assertEqual(facility["matrix_cases"], 24)
        self.assertTrue(facility["frontier_flag"])
        self.assertEqual(facility["persistent_effects_denied"], 7)
        self.assertTrue(facility["capture_denied"])
        self.assertTrue(facility["scheduler_faint_end"])
        self.assertEqual(facility["experience_after"], facility["experience_before"])
        self.assertEqual(facility["held_item_before"], 41)
        self.assertEqual(facility["held_item_after"], 41)
        self.assertEqual(facility["outcome"], 1)
        self.assertTrue(facility["enemy_fainted"])
        self.assertTrue(facility["runtime_cleaned"])
        rental = facility["rental_generation"]
        self.assertTrue(rental["bounded_call"])
        self.assertGreaterEqual(rental["party_count"], 3)
        self.assertLessEqual(rental["party_count"], 6)
        self.assertEqual(len(rental["species"]), 6)
        self.assertEqual(
            sum(species != 0 for species in rental["species"]),
            rental["party_count"],
        )
        for species in rental["species"]:
            self.assertLessEqual(species, 411)

        self.assertEqual(
            payload["mirage"],
            {
                "virtual_item": 900,
                "pending_configure_actual_battle": True,
                "owner": "opponent_party_slot_0",
                "opponent_battle_mon_virtualized": True,
                "opponent_original_restored_each_exit": True,
                "player_party_unchanged_each_exit": True,
                "battle_mon_virtualized": True,
                "consume_swap_mutation": True,
                "exit_paths": 7,
                "party_original_restored_each_exit": True,
                "virtual_or_mutated_item_leaked_to_bag": False,
                "leaked_to_bag": False,
            },
        )
        raid = payload["raid"]
        for key in (
            "high_difficulty_policy",
            "pending_configure_actual_battle",
            "existing_three_controller_ui_initialized",
            "boss_fainted",
            "catch_phase_seen",
            "bag_opened",
            "ball_consumed",
            "pc_storage_pointer_dynamic",
            "full_party_pc_routed",
            "party_species_unchanged",
            "stock_pc_box_stride_80",
            "adjacent_pc_slot_unchanged",
            "runtime_cleaned",
            "policy_state_cleaned",
            "normal_wild_no_leak",
            "normal_trainer_no_leak",
            "partner_spread_moves_preserved",
            "turn_limit_scheduler_end",
            "turn_limit_checked",
            "capture_allowed_path",
            "capture_denied_path",
            "contract_unit_direct_calls",
            "cleanup",
        ):
            self.assertTrue(raid[key])
        self.assertEqual(raid["boss_side"], 1)
        self.assertEqual(raid["partner_mask"], 6)
        self.assertEqual(raid["shield_boundary_max"], 5)
        self.assertEqual(raid["initial_shields"], 5)
        self.assertEqual(raid["shield_breaks"], 5)
        self.assertGreater(raid["controller_turns"], 0)
        self.assertGreater(raid["player_pp_before"], raid["player_pp_after"])
        self.assertEqual(raid["capture_action"], 1)
        self.assertEqual(raid["pc_box_id"], 0)
        self.assertEqual(raid["pc_box_position"], 0)
        self.assertEqual(raid["pc_captured_species"], 150)
        self.assertEqual(raid["party_count_after_capture"], 6)
        self.assertEqual(raid["outcome"], 7)
        self.assertTrue(raid["raid_state_completion_scheduler_e2e"])
        self.assertEqual(payload["unreached_routes"], [])
        self.assertEqual(payload["non_e2e_routes"], [])
        self.assertEqual(payload["artifacts_written"], [])

    def test_two_processes_are_byte_deterministic_json_only(self) -> None:
        first_stdout, first = self.run_once()
        second_stdout, second = self.run_once()
        self.assertEqual(first_stdout, second_stdout)
        self.assertEqual(first, second)
        self.assert_payload(first)

    def test_wrong_rom_hash_fails_before_emulation(self) -> None:
        completed = subprocess.run(
            self.command("0" * 64),
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
