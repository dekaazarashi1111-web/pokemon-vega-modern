#!/usr/bin/env python3
"""Stage79累積mGBA orchestratorの副作用なしpreflight/resume契約test。"""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_modernization_stage79_cumulative_mgba.py"
CONFIG = ROOT / "config/modernization_stage79_cumulative_mgba.json"
GATE = ROOT / "content/modernization/stage79_cumulative_mgba_runtime_gate.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("stage79_cumulative_mgba", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("Stage79 orchestratorをimportできません")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage79CumulativeMgbaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.rom = (
            ROOT / cls.config["input_identity"]["rom"]["path"]
        ).read_bytes()

    def _valid_bounded_result(self, domain_id: str) -> dict:
        rom_sha = self.config["runtime_candidate"]["rom"]["sha256"]
        common = {"schema_version": 1, "status": "PASS", "warnings_errors": 0}
        if domain_id == "p02":
            return {
                **common,
                "classification": "STAGE71_EXACT_ROM_NORMAL_INPUT_AND_FRESH_CORE",
                "rom_sha256": rom_sha,
                "known_good_seed_sha256": (
                    self.config["domains"][0]["seed_save"]["sha256"]
                ),
                "boot_route": "NORMAL_TITLE_CONTINUE_PINNED_SAVE",
                "initial_normal_continue_field": True,
                "fixture_replacement_after_field": True,
                "temporary_save_only": True,
                "direct_conditions": {
                    "level": True, "friendship": True, "known_move": True,
                    "trade": True, "night_form": True,
                    "level_held_item_six": {
                        "species_count": 6, "conditional_selected": 6,
                        "conditional_item_consumed": 6,
                        "below_level_rejected": 6,
                        "wrong_or_missing_item_regular": 12,
                        "hidden_ability_preserved": 24,
                        "payload_pc_seen": True,
                    },
                },
                "normal_evolution_cancel": {
                    key: True for key in (
                        "normal_bag_party_input", "scene_callbacks_seen",
                        "physical_b_cancel", "source_retained",
                        "four_moves_retained", "ability_slot_retained",
                    )
                },
                "normal_evolution_success": {
                    key: True for key in (
                        "normal_bag_party_input", "scene_callbacks_seen",
                        "target_applied", "four_moves_retained",
                        "ability_slot_retained", "ability_matches_slot",
                    )
                },
                "conditional_form_success": {
                    key: True for key in (
                        "normal_bag_party_input", "scene_callbacks_seen",
                        "exact_form_applied", "condition_item_consumed",
                        "four_moves_retained", "hidden_ability_preserved",
                        "ability_matches_hidden",
                    )
                },
                "bag_item_use": {
                    key: True for key in (
                        "normal_start_bag_party_input", "scene_callbacks_seen",
                        "target_applied", "bag_item_consumed",
                        "four_moves_retained",
                    )
                },
                "bag_item_missing": {
                    key: True for key in (
                        "normal_start_bag_input_attempted", "item_absent",
                        "party_not_opened_for_item", "species_unchanged",
                    )
                },
                "save_reload": {
                    key: True for key in (
                        "stock_save_twice", "original_core_destroyed",
                        "fresh_core_created", "stock_load_succeeded",
                        "normal_continue_load_succeeded", "exact_form_reloaded",
                        "four_moves_reloaded", "condition_item_still_consumed",
                        "hidden_ability_reloaded", "ability_matches_hidden",
                    )
                },
            }
        if domain_id == "mega_shop":
            return {
                **common, "stage": 68,
                "checks": {
                    key: True for key in (
                        "physical_npc_script_graph_to_entrypoint",
                        "item_consumer_boundaries_999_1023_1024_1043_1044",
                        "name_hold_effect_and_is_mega_stone_consumers",
                        "probe_and_save_init", "mega_ring_580_gate",
                        "insufficient_bp_no_mutation", "bag_full_no_mutation",
                        "index_0_item_999_price_16",
                        "index_22_item_1021_price_16",
                        "index_44_item_1043_price_16",
                        "claim_flags_14a0_14b6_14cc",
                        "fresh_core_normal_save_reload",
                        "fresh_core_once_rejected",
                    )
                },
                "representative_indices": [0, 22, 44],
                "representative_item_ids": [999, 1021, 1043],
                "representative_claim_flags": [5280, 5302, 5324],
                "accepted_item_boundary_ids": [999, 1023, 1024, 1043],
                "first_rejected_item_id": 1044, "hold_effect": 73,
                "price_bp": 16, "initial_bp": 100, "final_bp": 52,
                "bag_full_capacity": 1,
                "core_instances": 2, "process_runs": 1,
                "framebuffer_transitions": 1,
                "state_fixture": "PRODUCTION_ROM_FUNCTIONS_ONLY",
                "retained_artifacts": [],
            }
        if domain_id == "floette":
            return {
                **common,
                "task": "USER-MODERNIZATION-FLOETTE-ETERNAL-GIFT",
                "stage": 69,
                "checks": {
                    key: True for key in (
                        "physical_npc_script_graph_to_entrypoint",
                        "mega_ring_580_gate",
                        "party_delivery_species1029_level50",
                        "full_party_pc_delivery_species1029_level50",
                        "pc_level50_create_mon_experience_identity",
                        "party_and_pc_full_unclaimed", "claim_flag_14cd",
                        "national670_collection_bit850",
                        "standard_save_fresh_core_reload",
                        "fresh_core_once_rejected",
                    )
                },
                "pc_destination": {"box": 0, "position": 0},
                "core_instances": 2, "process_runs": 1,
                "framebuffer_transitions": 1,
                "state_fixture": "PRODUCTION_ROM_FUNCTIONS_ONLY",
                "retained_artifacts": [],
            }
        if domain_id == "p03":
            return {
                **common,
                "classification": "LATEST_CUMULATIVE_P03_REPRESENTATIVE_DIRECT_CALL",
                "rom_sha256": rom_sha, "process_runs": 1, "read_only": True,
                "checks": {
                    "stage67_level_evolution_tutor_egg": True,
                    "stage73_exact_alias_shared_egg_reminder_rotom": True,
                    "stage74_machine_tutor_paging_cancel_failure_capacity": True,
                    "stage75_species1670_egg_evolution_route_owner": True,
                    "all_known_terminal_mode_reset_source_pinned": True,
                },
                "full_p03_acceptance": False, "scheduler_e2e": False,
                "breeding_e2e": False, "save_reload_e2e": False,
                "artifacts_written": [],
            }
        if domain_id == "p04_mega_runtime":
            return {
                **common, "classification": "DIRECT_CALL_BOUNDED",
                "rom_sha256": rom_sha, "read_only": True,
                "mapping_count": 49, "correct_stone_matches": 49,
                "stone_less_rejections": 49, "mega_species_recognized": 49,
                "base_species_rejected_as_mega": 49,
                "reversions_to_base": 49, "direct_calls": 245,
                "instructions": 1,
                "symbols": {
                    "GetMegaSpecies": "0x09114CF0",
                    "TryRevertMega": "0x09114F74",
                    "IsMegaSpecies": "0x09115098",
                },
                "payload_pc_seen": True, "artifacts_written": [],
            }
        if domain_id == "battle_policy":
            raid_true = (
                "high_difficulty_policy", "pending_configure_actual_battle",
                "existing_three_controller_ui_initialized", "boss_fainted",
                "catch_phase_seen", "bag_opened", "ball_consumed",
                "pc_storage_pointer_dynamic", "full_party_pc_routed",
                "party_species_unchanged", "stock_pc_box_stride_80",
                "adjacent_pc_slot_unchanged", "runtime_cleaned",
                "policy_state_cleaned", "normal_wild_no_leak",
                "normal_trainer_no_leak", "partner_spread_moves_preserved",
                "turn_limit_checked", "turn_limit_scheduler_end",
                "capture_allowed_path", "capture_denied_path",
                "contract_unit_direct_calls", "cleanup",
                "raid_state_completion_scheduler_e2e",
            )
            return {
                **common, "fixture": "t06_battle_policy_integration_v1",
                "rom_sha256": rom_sha, "fixed_rtc_unix": 946684800,
                "read_only": True, "boot_trace_segments": 233,
                "direct_call_instructions": 202, "payload_calls": 201,
                "stat_inputs": {
                    "exp_share_off_participant_only": True,
                    "exp_share_on_unparticipated": True,
                    "mint_nature": 6, "ability_slot": 2,
                    "hyper_trained_iv": 31,
                },
                "exp_candy": {
                    key: True for key in (
                        "selected_target_only", "zero_no_effect_not_consumed",
                        "cap_clamped", "at_cap_not_consumed",
                    )
                },
                "trainer_build": {
                    "fully_specified": True, "unspecified_identity": True,
                    "ev_total": 510,
                },
                "non_e2e_routes": [],
                "unreached_routes": [], "direct_calls": 201,
                "actual_battle_setups": 41,
                "mechanics": {
                    "modes": ["MEGA", "Z_MOVE", "DYNAMAX", "TERASTAL"],
                    "side_wide_exclusive": True, "one_use": True,
                    "cross_mode_exclusive": True, "cleanup": True,
                },
                "facility": {
                    "formats": 3, "rules": 8, "matrix_cases": 24,
                    "frontier_flag": True, "persistent_effects_denied": 7,
                    "capture_denied": True, "scheduler_faint_end": True,
                    "experience_before": 1, "experience_after": 1,
                    "held_item_before": 41, "held_item_after": 41,
                    "outcome": 1, "enemy_fainted": True,
                    "runtime_cleaned": True,
                    "rental_generation": {
                        "bounded_call": True, "party_count": 6,
                        "species": [1, 2, 3, 4, 5, 6],
                    },
                },
                "mirage": {
                    "virtual_item": 900,
                    "pending_configure_actual_battle": True,
                    "owner": "opponent_party_slot_0",
                    "opponent_battle_mon_virtualized": True,
                    "opponent_original_restored_each_exit": True,
                    "player_party_unchanged_each_exit": True,
                    "battle_mon_virtualized": True,
                    "consume_swap_mutation": True, "exit_paths": 7,
                    "party_original_restored_each_exit": True,
                    "virtual_or_mutated_item_leaked_to_bag": False,
                    "leaked_to_bag": False,
                },
                "raid": {
                    **{key: True for key in raid_true},
                    "boss_side": 1, "partner_mask": 6,
                    "shield_boundary_max": 5, "initial_shields": 5,
                    "shield_breaks": 5, "controller_turns": 1,
                    "player_pp_before": 10, "player_pp_after": 9,
                    "capture_action": 1, "pc_box_id": 0,
                    "pc_box_position": 0, "pc_captured_species": 150,
                    "party_count_after_capture": 6, "outcome": 7,
                },
                "artifacts_written": [],
            }
        if domain_id == "p05":
            return {
                **common,
                "classification": "STAGE78_P05_RUNTIME_DIRECT_CALL",
                "rom_sha256": rom_sha, "read_only": True,
                "dispatcher_count": 29, "ability_surface_occurrence_count": 33,
                "normal_delegations": 29, "circus_original_delegations": 29,
                "predicate_truth_table_pass": True,
                "stage76_helpers_preserved": True,
                "suppression_paths_pass": True,
                "stage76_megasol_production_dispatch_pass": True,
                "stage76_suppression_link_count": 3,
                "dispatcher_observations": 203, "direct_calls": 1,
                "dispatcher_instructions": 1, "direct_call_instructions": 1,
                "fifth_stack_argument_observations": 21,
                "fifth_stack_arguments_preserved": True,
                "eelevate_switch_ai_done": True,
                "eelevate_matrix_case_count": 32,
                "eelevate_matrix_observations": 32,
                "eelevate_matrix_sha256": "3b0ce8e8a5fa75857971b59091f2a95d73ec5597d90be4756eb9e3717e8383ed",
                "eelevate_pure_helper_pass": True,
                "eelevate_active_helper_pass": True,
                "eelevate_party_helper_pass": True,
                "eelevate_active_hook_route_pass": True,
                "eelevate_party_hook_route_pass": True,
                "eelevate_active_hook_observations": 13,
                "eelevate_party_hook_observations": 13,
                "eelevate_stub_calls_observed": 1,
                "eelevate_register_continuation_abi_pass": True,
                "full_p05_acceptance": False, "scheduler_e2e": False,
                "artifacts_written": [],
            }
        raise AssertionError(f"unknown domain: {domain_id}")

    def test_dry_plan_pins_repaired_candidate_and_immutable_stage78_parent(self) -> None:
        plan = self.module.build_plan(CONFIG.relative_to(ROOT))
        self.assertEqual(plan["status"], "PREFLIGHT_PASS_NOT_EXECUTED")
        self.assertEqual(plan["input"]["stage"], 80)
        self.assertEqual(plan["input"]["rom"], self.module.EXPECTED_STAGE80_ROM)
        self.assertEqual(plan["input"]["changed_bytes_from_parent"], 51)
        parent = plan["input"]["parent"]
        self.assertEqual(parent["stage"], 78)
        self.assertEqual(parent["commit"], "a98e6fea59db1f020bc902a1b1676699f8c06c41")
        self.assertEqual(parent["rom"]["sha256"],
            "98fde60231175492032f0e28ca16549a73ca5b29e3f37438b77c6e3c80e9d06b")
        self.assertEqual(parent["allocation_count"], 82)
        self.assertEqual(parent["allocation_last_sequence"], 81)
        self.assertFalse(plan["input"]["parent_allocation_content_hashes_reused_as_candidate"])
        self.assertEqual(
            plan["domain_order"], list(self.module.EXPECTED_DOMAIN_ORDER)
        )
        self.assertEqual(plan["p03"]["runner_argument_count"], 94)
        self.assertFalse(plan["p03"]["legacy_stage67_runner_used"])
        self.assertEqual(
            plan["domain_contracts"]["p04_mega_runtime"]["mapping_count"], 49
        )
        self.assertEqual(
            plan["domain_contracts"]["p04_mega_runtime"]["direct_call_count"],
            245,
        )
        self.assertEqual(
            plan["domain_contracts"]["battle_policy"]["symbol_count"], 44
        )
        self.assertEqual(
            plan["domain_contracts"]["p05"]["argument_count"], 167
        )
        self.assertEqual(
            plan["domain_contracts"]["p05"]["dispatcher_count"], 29
        )
        self.assertTrue(
            all(row["state"] == self.module.READY for row in plan["domains"])
        )
        self.assertEqual(plan["product_rom_patch_bytes"], 0)
        self.assertFalse(plan["execution_performed"])

    def test_compile_check_compiles_ready_domains_without_mgba(self) -> None:
        before_gate = GATE.read_bytes() if GATE.exists() else None
        result = self.module.compile_check(CONFIG.relative_to(ROOT))
        self.assertEqual(result["status"], "COMPILE_CHECK_PASS_NOT_EXECUTED")
        self.assertEqual(result["mGBA_process_runs"], 0)
        self.assertEqual(result["artifacts_written"], [])
        self.assertEqual(
            [row["status"] for row in result["domains"]],
            ["COMPILE_PASS"] * 7,
        )
        self.assertEqual(GATE.read_bytes() if GATE.exists() else None, before_gate)

    def test_derived_cli_commands_are_complete_and_source_ordered(self) -> None:
        by_id = {row["id"]: row for row in self.config["domains"]}
        executable = Path("/tmp/stage79-runner")
        rom = ROOT / self.config["input_identity"]["rom"]["path"]
        sha = self.config["runtime_candidate"]["rom"]["sha256"]
        work = ROOT / ".local/stage79-command-unit"

        mega = self.module._command(
            by_id["mega_shop"], executable, rom, sha, work, self.config
        )
        floette = self.module._command(
            by_id["floette"], executable, rom, sha, work, self.config
        )
        p03 = self.module._command(
            by_id["p03"], executable, rom, sha, work, self.config
        )
        p04 = self.module._command(
            by_id["p04_mega_runtime"], executable, rom, sha, work, self.config
        )
        policy = self.module._command(
            by_id["battle_policy"], executable, rom, sha, work, self.config
        )
        p05 = self.module._command(
            by_id["p05"], executable, rom, sha, work, self.config
        )

        self.assertEqual(len(mega), 14)
        self.assertEqual(len(floette), 15)
        self.assertEqual(len(p03), 3 + 94)
        self.assertEqual(sum(arg.startswith("--") for arg in p03), 94)
        self.assertEqual(len(p04), 4 + 49 * 3)
        self.assertEqual(p04[3], "49")
        self.assertEqual(p04[4:7], ["0x34", "0x3e7", "0x655"])
        self.assertEqual(p04[-3:], ["0x3fb", "0x413", "0x685"])
        self.assertEqual(len(policy), 3 + 44)
        self.assertEqual(
            [arg.split("=", 1)[0] for arg in policy[3:]],
            list(self.module.BATTLE_POLICY_SYMBOL_NAMES),
        )
        expected_p05_keys = list(self.module.P05_GLOBAL_ARGUMENT_NAMES)
        for suffix in self.module.P05_DISPATCHER_SUFFIXES:
            expected_p05_keys.extend(
                f"{prefix}{suffix}"
                for prefix in ("HOOK_", "DISPATCH_", "NORMAL_", "SUPPRESSED_")
            )
        self.assertEqual(len(p05), 3 + 167)
        self.assertEqual(
            [arg.split("=", 1)[0] for arg in p05[3:]], expected_p05_keys
        )

    def test_ready_gate_is_honest_about_unexecuted_and_uncovered_boundaries(self) -> None:
        plan = self.module.build_plan(CONFIG.relative_to(ROOT))
        gate = self.module._ready_gate(plan, self.config)
        self.assertEqual(gate["status"], "READY_NOT_RUN")
        self.assertTrue(gate["not_yet_executed"])
        self.assertEqual(gate["execution"]["fresh_mGBA_process_runs"], 0)
        self.assertEqual(gate["execution"]["cached_domain_results_reused"], 0)
        self.assertEqual(gate["execution"]["evidenced_domain_runs"], 0)
        self.assertTrue(gate["execution"]["resume_supported"])
        self.assertEqual(gate["config"], plan["config"])
        self.assertEqual(gate["orchestrator"], plan["orchestrator"])
        self.assertTrue(all(row["status"] == "NOT_RUN" for row in gate["domains"]))
        self.assertEqual(
            [row["runner"] for row in gate["domains"]],
            [row["runner"] for row in self.config["domains"]],
        )
        self.assertTrue(all(value is False for value in gate["claims"].values()))

    def test_check_is_side_effect_free_for_ready_gate(self) -> None:
        self.assertTrue(GATE.is_file(), "prepare済みruntime gateが必要です")
        before = GATE.read_bytes()
        before_mtime = GATE.stat().st_mtime_ns
        with mock.patch.object(
            self.module.subprocess, "run",
            side_effect=AssertionError("check must not execute subprocess"),
        ):
            result = self.module.check(CONFIG.relative_to(ROOT))
        self.assertEqual(result["status"], "CHECK_PASS")
        self.assertEqual(result["mGBA_process_runs"], 0)
        self.assertEqual(result["artifacts_written"], [])
        self.assertEqual(GATE.read_bytes(), before)
        self.assertEqual(GATE.stat().st_mtime_ns, before_mtime)

    def test_heavy_run_requires_explicit_flag_before_run_function(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(
            self.module, "run", side_effect=AssertionError("run must stay blocked")
        ), contextlib.redirect_stderr(stderr):
            result = self.module.main([
                "run", "--config", CONFIG.relative_to(ROOT).as_posix()
            ])
        self.assertEqual(result, 1)
        self.assertIn("--yes-heavy", stderr.getvalue())

    def test_private_rom_copy_isolated_and_mutation_detected(self) -> None:
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="stage79-private-rom-test-", dir=local
        ) as raw:
            root = Path(raw)
            source = root / "source.gba"
            source_raw = bytes(range(64)) * 4
            source.write_bytes(source_raw)
            expected = {
                "size": len(source_raw),
                "sha256": self.module._sha(source_raw),
            }
            private = self.module._ensure_private_rom(
                source, root / "state", expected
            )
            self.assertNotEqual(private, source)
            self.assertEqual(private.read_bytes(), source_raw)
            self.assertEqual(private.stat().st_mode & 0o222, 0)
            self.module._validate_runtime_roms_unchanged(
                source, private, expected
            )

            private.chmod(0o644)
            private.write_bytes(b"changed")
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module._validate_runtime_roms_unchanged(
                    source, private, expected
                )
            self.assertEqual(source.read_bytes(), source_raw)
            repaired = self.module._ensure_private_rom(
                source, root / "state", expected
            )
            self.assertEqual(repaired.read_bytes(), source_raw)
            self.assertEqual(repaired.stat().st_mode & 0o222, 0)

            hardlink_state = root / "hardlink-state"
            hardlink_input = hardlink_state / "input"
            hardlink_input.mkdir(parents=True)
            hardlink = hardlink_input / "stage78-private.gba"
            source.chmod(0o644)
            hardlink.hardlink_to(source)
            self.assertTrue(os.path.samefile(source, hardlink))
            isolated = self.module._ensure_private_rom(
                source, hardlink_state, expected
            )
            self.assertFalse(os.path.samefile(source, isolated))
            self.assertEqual(isolated.stat().st_nlink, 1)

            bad_state = root / "bad-state"
            bad_state.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (bad_state / "input").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module._ensure_private_rom(source, bad_state, expected)

            work = root / "leaf-work"
            work.mkdir()
            outside_save = root / "outside-save.sav"
            outside_save.write_bytes(b"unchanged")
            (work / "p02-private.sav").symlink_to(outside_save)
            p02 = next(
                row for row in self.config["domains"] if row["id"] == "p02"
            )
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module._command(
                    p02, root / "runner", source,
                    self.config["runtime_candidate"]["rom"]["sha256"],
                    work, self.config,
                )
            self.assertEqual(outside_save.read_bytes(), b"unchanged")

            mega_save = work / "mega-shop.sav"
            mega_save.hardlink_to(outside_save)
            mega = next(
                row for row in self.config["domains"]
                if row["id"] == "mega_shop"
            )
            self.module._command(
                mega, root / "runner", source,
                self.config["runtime_candidate"]["rom"]["sha256"],
                work, self.config,
            )
            self.assertEqual(outside_save.read_bytes(), b"unchanged")
            self.assertFalse(os.path.samefile(mega_save, outside_save))
            self.assertEqual(mega_save.stat().st_nlink, 1)

            outside_runner = root / "outside-runner"
            outside_runner.write_bytes(b"unchanged-runner")
            compiled_runner = work / "runner"
            compiled_runner.hardlink_to(outside_runner)
            p05 = next(
                row for row in self.config["domains"] if row["id"] == "p05"
            )
            self.module._compile(p05, compiled_runner)
            self.assertEqual(outside_runner.read_bytes(), b"unchanged-runner")
            self.assertFalse(os.path.samefile(compiled_runner, outside_runner))
            self.assertEqual(compiled_runner.stat().st_nlink, 1)

            symlink_parent = root / "symlink-parent"
            symlink_parent.symlink_to(work, target_is_directory=True)
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module._atomic_write(symlink_parent / "evidence.json", b"{}")

    def test_resume_checkpoint_requires_exact_sequential_pass_prefix(self) -> None:
        plan = self.module.build_plan(CONFIG.relative_to(ROOT))
        checkpoint = {
            "schema_version": 1,
            "task": self.module.TASK,
            "stage": self.module.STAGE,
            "status": "IN_PROGRESS",
            "plan_fingerprint": plan["plan_fingerprint"],
            "input": plan["input"],
            "domain_order": plan["domain_order"],
            "domains": {
                domain_id: ("PASS" if index < 3 else "NOT_RUN")
                for index, domain_id in enumerate(plan["domain_order"])
            },
        }
        self.module._validate_resume_checkpoint(
            checkpoint, plan, self.config
        )
        serialized = json.loads(self.module._stable(checkpoint))
        self.module._validate_resume_checkpoint(serialized, plan, self.config)
        bad = copy.deepcopy(checkpoint)
        bad["domains"]["p04_mega_runtime"] = "PASS"
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_resume_checkpoint(bad, plan, self.config)

        bad = copy.deepcopy(checkpoint)
        bad["status"] = "PASS_WITH_DECLARED_LIMITS"
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_resume_checkpoint(bad, plan, self.config)

    def test_config_and_preimage_mutations_fail_closed(self) -> None:
        bad = copy.deepcopy(self.config)
        bad["domains"][0]["compile"]["flags"].remove("-Werror")
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_config(bad)

        bad = copy.deepcopy(self.config)
        bad["execution"]["domain_order"][3:5] = reversed(
            bad["execution"]["domain_order"][3:5]
        )
        bad["domains"][3:5] = reversed(bad["domains"][3:5])
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_config(bad)

        bad = copy.deepcopy(self.config)
        del bad["latest_rom_preimages"][-1]
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_preimages(bad, self.rom)

        changed_rom = bytearray(self.rom)
        address = int(self.config["latest_rom_preimages"][0]["address"], 0)
        changed_rom[address - self.module.ROM_BASE] ^= 1
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_preimages(self.config, bytes(changed_rom))

    def test_p03_symbol_root_and_argument_mutations_fail_closed(self) -> None:
        bad = copy.deepcopy(self.config)
        bad["p03_contract"]["arguments"]["stage75-probe"] = "0x0954B033"
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_p03(bad, self.rom)

        bad = copy.deepcopy(self.config)
        bad["p03_contract"]["arguments"]["level-root"] = "0x0958B960"
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_p03(bad, self.rom)

        bad = copy.deepcopy(self.config)
        bad["p03_required_argument_keys"].remove("scratch-address")
        del bad["p03_contract"]["arguments"]["scratch-address"]
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_p03(bad, self.rom)

        bad = copy.deepcopy(self.config)
        del bad["p03_contract"]["symbol_bindings"][-1]
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_p03(bad, self.rom)

        bad = copy.deepcopy(self.config)
        del bad["p03_contract"]["terminal_required_tokens"][-1]
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_p03(bad, self.rom)

    def test_domain_source_contract_mutations_fail_closed(self) -> None:
        mutations = (
            ("mega_shop", "arguments_sha256"),
            ("floette", "arguments_sha256"),
            ("p04_mega_runtime", "records_sha256"),
            ("battle_policy", "symbols_sha256"),
            ("p05", "arguments_sha256"),
        )
        for domain_id, key in mutations:
            with self.subTest(domain=domain_id, key=key):
                bad = copy.deepcopy(self.config)
                row = next(row for row in bad["domains"] if row["id"] == domain_id)
                row[key] = "0" * 64
                with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                    self.module._validate_domain_contracts(bad)

        bad = copy.deepcopy(self.config)
        p05 = next(row for row in bad["domains"] if row["id"] == "p05")
        p05["state"] = self.module.PENDING
        p05["kind"] = "generic_json"
        p05["pending_reason"] = "RUNNER_NOT_YET_IMPLEMENTED"
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_domain_contracts(bad)

        bad = copy.deepcopy(self.config)
        p05 = next(row for row in bad["domains"] if row["id"] == "p05")
        p05["contract_sources"]["stage78_symbols"]["sha256"] = "0" * 64
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_domain_contracts(bad)

    def test_input_identity_and_allocation_lineage_mutations_fail_closed(self) -> None:
        bad = copy.deepcopy(self.config)
        bad["input_identity"]["stage"] = 76
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_config(bad)

        bad = copy.deepcopy(self.config)
        bad["input_identity"]["task"] = "USER-MODERNIZATION-P05-STAGE76-EDGES"
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_config(bad)

        bad = copy.deepcopy(self.config)
        bad["input_identity"]["commit"] = "0" * 40
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_config(bad)

        bad = copy.deepcopy(self.config)
        bad["input_identity"]["rom"]["sha256"] = "0" * 64
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_input(bad)

        bad = copy.deepcopy(self.config)
        bad["input_identity"]["allocation_count"] = 80
        bad["input_identity"]["allocation_last_sequence"] = 79
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_input(bad)

        bad = copy.deepcopy(self.config)
        bad["input_identity"]["rom"]["crc32"] = "00000000"
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_input(bad)

        original_fixed = self.module._fixed

        def mutated_allocation(record, label):
            path, raw = original_fixed(record, label)
            if label == "input allocation":
                document = json.loads(raw)
                document["allocations"][-1]["size"] += 1
                raw = self.module._stable(document)
            return path, raw

        with mock.patch.object(
            self.module, "_fixed", side_effect=mutated_allocation
        ):
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module._validate_input(self.config)

        def mutated_checkpoint(record, label):
            path, raw = original_fixed(record, label)
            if label == "input checkpoint":
                document = json.loads(raw)
                document["allocation_lineage"]["new_sequence"] = 79
                raw = self.module._stable(document)
            return path, raw

        with mock.patch.object(
            self.module, "_fixed", side_effect=mutated_checkpoint
        ):
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module._validate_input(self.config)

    def test_p04_result_requires_every_mapping_and_five_calls_each(self) -> None:
        domain = next(
            row for row in self.config["domains"]
            if row["id"] == "p04_mega_runtime"
        )
        result = {
            "schema_version": 1,
            "status": "PASS",
            "classification": "DIRECT_CALL_BOUNDED",
            "rom_sha256": self.config["runtime_candidate"]["rom"]["sha256"],
            "read_only": True,
            "mapping_count": 49,
            "correct_stone_matches": 49,
            "stone_less_rejections": 49,
            "mega_species_recognized": 49,
            "base_species_rejected_as_mega": 49,
            "reversions_to_base": 49,
            "direct_calls": 245,
            "instructions": 1,
            "symbols": {
                "GetMegaSpecies": "0x09114CF0",
                "TryRevertMega": "0x09114F74",
                "IsMegaSpecies": "0x09115098",
            },
            "payload_pc_seen": True,
            "warnings_errors": 0,
            "artifacts_written": [],
        }
        self.module._validate_result(
            domain, result, self.config["runtime_candidate"]["rom"]["sha256"]
        )
        bad = dict(result, direct_calls=244)
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_result(
                domain, bad,
                self.config["runtime_candidate"]["rom"]["sha256"],
            )
        bad = dict(result)
        del bad["warnings_errors"]
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_result(
                domain, bad,
                self.config["runtime_candidate"]["rom"]["sha256"],
            )

    def test_p05_result_requires_exact_bounded_suppression_evidence(self) -> None:
        domain = next(
            row for row in self.config["domains"] if row["id"] == "p05"
        )
        result = {
            "schema_version": 1,
            "status": "PASS",
            "classification": "STAGE78_P05_RUNTIME_DIRECT_CALL",
            "rom_sha256": self.config["runtime_candidate"]["rom"]["sha256"],
            "read_only": True,
            "warnings_errors": 0,
            "dispatcher_count": 29,
            "ability_surface_occurrence_count": 33,
            "normal_delegations": 29,
            "circus_original_delegations": 29,
            "predicate_truth_table_pass": True,
            "stage76_helpers_preserved": True,
            "suppression_paths_pass": True,
            "stage76_megasol_production_dispatch_pass": True,
            "stage76_suppression_link_count": 3,
            "dispatcher_observations": 203,
            "direct_calls": 1,
            "dispatcher_instructions": 1,
            "direct_call_instructions": 1,
            "fifth_stack_argument_observations": 21,
            "fifth_stack_arguments_preserved": True,
            "eelevate_switch_ai_done": True,
            "eelevate_matrix_case_count": 32,
            "eelevate_matrix_observations": 32,
            "eelevate_matrix_sha256": "3b0ce8e8a5fa75857971b59091f2a95d73ec5597d90be4756eb9e3717e8383ed",
            "eelevate_pure_helper_pass": True,
            "eelevate_active_helper_pass": True,
            "eelevate_party_helper_pass": True,
            "eelevate_active_hook_route_pass": True,
            "eelevate_party_hook_route_pass": True,
            "eelevate_active_hook_observations": 13,
            "eelevate_party_hook_observations": 13,
            "eelevate_stub_calls_observed": 1,
            "eelevate_register_continuation_abi_pass": True,
            "full_p05_acceptance": False,
            "scheduler_e2e": False,
            "artifacts_written": [],
        }
        self.module._validate_result(
            domain, result, self.config["runtime_candidate"]["rom"]["sha256"]
        )
        for key, value in (
            ("dispatcher_observations", 202),
            ("full_p05_acceptance", True),
            ("warnings_errors", None),
        ):
            with self.subTest(key=key):
                bad = dict(result, **{key: value})
                with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                    self.module._validate_result(
                        domain, bad,
                        self.config["runtime_candidate"]["rom"]["sha256"],
                    )
        bad = dict(result, release_ready=True)
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_result(
                domain, bad,
                self.config["runtime_candidate"]["rom"]["sha256"],
            )

        policy = next(
            row for row in self.config["domains"] if row["id"] == "battle_policy"
        )
        policy_result = self._valid_bounded_result("battle_policy")
        self.module._validate_result(
            policy, policy_result,
            self.config["runtime_candidate"]["rom"]["sha256"],
        )
        policy_result["stat_inputs"]["hyper_trained_iv"] = 30
        with self.assertRaises(self.module.Stage79CumulativeMgbaError):
            self.module._validate_result(
                policy, policy_result,
                self.config["runtime_candidate"]["rom"]["sha256"],
            )

        for candidate in self.config["domains"]:
            with self.subTest(missing_warnings_errors=candidate["id"]):
                missing = self._valid_bounded_result(candidate["id"])
                del missing["warnings_errors"]
                with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                    self.module._validate_result(
                        candidate, missing,
                        self.config["runtime_candidate"]["rom"]["sha256"],
                    )

    def test_completed_gate_embeds_evidence_and_mutation_fails_closed(self) -> None:
        plan = self.module.build_plan(CONFIG.relative_to(ROOT))
        state = ROOT / ".local/stage79-self-contained-no-cache"
        self.assertFalse((state / "checkpoint.json").exists())
        rows = []
        result_paths = []
        for domain in self.config["domains"]:
            result = self._valid_bounded_result(domain["id"])
            result_path = (
                state / "results" / f"{domain['id']}.json"
            ).relative_to(ROOT).as_posix()
            result_paths.append(result_path)
            rows.append({
                "id": domain["id"],
                "status": "PASS",
                "pending_reason": None,
                "runner": domain["runner"],
                "compilation": {
                    "compiler": "/usr/bin/cc",
                    "flags": domain["compile"]["flags"],
                    "link_flags": domain["compile"]["link_flags"],
                    "executable_size": 1,
                    "executable_sha256": "0" * 64,
                },
                "command_argument_count": (
                    self.module._expected_command_argument_count(domain)
                ),
                "stderr_sha256": "0" * 64,
                "runner_result_sha256": self.module._sha(
                    self.module._stable(result)
                ),
                "runner_result": result,
                "resume_cache_path": result_path,
            })
        checkpoint_path = (
            state / "checkpoint.json"
        ).relative_to(ROOT).as_posix()
        gate = {
            "schema_version": 1,
            "task": self.module.TASK,
            "stage": self.module.STAGE,
            "status": "PASS_WITH_DECLARED_LIMITS",
            "classification": "LATEST_CUMULATIVE_EXACT_ROM_SEQUENTIAL_RESUMABLE",
            "config": copy.deepcopy(plan["config"]),
            "orchestrator": copy.deepcopy(plan["orchestrator"]),
            "input": plan["input"],
            "plan_fingerprint": plan["plan_fingerprint"],
            "domain_order": plan["domain_order"],
            "domains": rows,
            "execution": {
                "fresh_mGBA_process_runs": 7,
                "cached_domain_results_reused": 0,
                "evidenced_domain_runs": 7,
                "individual_results_written_this_invocation": 7,
                "checkpoint_written": True,
                "resume_cache_checkpoint_path": checkpoint_path,
                "resume_supported": True,
                "explicit_heavy_run_required": True,
                "runner_results_embedded": True,
            },
            "claims": self.module._ready_gate(plan, self.config)["claims"],
            "not_yet_executed": False,
            "runner_results_embedded": True,
            "resume_cache": {
                "required_for_check": False,
                "checkpoint_path": checkpoint_path,
                "private_rom_path": (
                    state / "input" / "stage78-private.gba"
                ).relative_to(ROOT).as_posix(),
                "result_paths": result_paths,
            },
            "artifacts_written": [
                self.config["execution"]["runtime_gate"]
            ],
        }
        original_reader = self.module._read_json_path

        def read_without_cache(path: Path, label: str):
            if Path(path).resolve() == GATE.resolve():
                return gate
            if str(path).startswith(str(state)):
                raise AssertionError("check must not read .local resume cache")
            return original_reader(path, label)

        with mock.patch.object(
            self.module, "_state_directory", return_value=state
        ), mock.patch.object(
            self.module, "_read_json_path", side_effect=read_without_cache
        ), mock.patch.object(
            self.module, "_validate_result_record",
            wraps=self.module._validate_result_record,
        ) as validate_record:
            checked = self.module.check(CONFIG.relative_to(ROOT))
        self.assertEqual(checked["status"], "CHECK_PASS")
        self.assertEqual(validate_record.call_count, 7)

        gate["execution"]["fresh_mGBA_process_runs"] = -1
        gate["execution"]["cached_domain_results_reused"] = 8
        with mock.patch.object(
            self.module, "_state_directory", return_value=state
        ), mock.patch.object(
            self.module, "_read_json_path", side_effect=read_without_cache
        ):
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module.check(CONFIG.relative_to(ROOT))
        gate["execution"]["fresh_mGBA_process_runs"] = 7
        gate["execution"]["cached_domain_results_reused"] = 0

        expected_orchestrator = copy.deepcopy(gate["orchestrator"])
        gate["orchestrator"]["sha256"] = "f" * 64
        with mock.patch.object(
            self.module, "_state_directory", return_value=state
        ), mock.patch.object(
            self.module, "_read_json_path", side_effect=read_without_cache
        ):
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module.check(CONFIG.relative_to(ROOT))
        gate["orchestrator"] = expected_orchestrator

        gate["domains"][0]["runner_result"]["mutated"] = True
        with mock.patch.object(
            self.module, "_state_directory", return_value=state
        ), mock.patch.object(
            self.module, "_read_json_path", side_effect=read_without_cache
        ):
            with self.assertRaises(self.module.Stage79CumulativeMgbaError):
                self.module.check(CONFIG.relative_to(ROOT))

    def test_config_change_produces_new_resume_fingerprint(self) -> None:
        original = self.module.build_plan(CONFIG.relative_to(ROOT))
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="stage79-config-test-", dir=local) as raw:
            alternate = Path(raw) / "config.json"
            changed = copy.deepcopy(self.config)
            changed["fingerprint_test_marker"] = "different-config-identity"
            alternate.write_text(
                json.dumps(changed, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            mutated = self.module.build_plan(alternate.relative_to(ROOT))
        self.assertNotEqual(
            original["plan_fingerprint"], mutated["plan_fingerprint"]
        )


if __name__ == "__main__":
    unittest.main()
