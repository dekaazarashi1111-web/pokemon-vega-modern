from __future__ import annotations

import unittest
from pathlib import Path

from scripts.run_stage58_mgba_validation import validation_contract


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_stage58_mgba_validation.py"
BUILDER = ROOT / "scripts/build_stage58_qol_world_convenience_debug.py"


class Stage58MgbaValidationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.builder = BUILDER.read_text(encoding="utf-8")

    def test_full_profile_has_seven_inherited_and_three_stage58_domains(self) -> None:
        self.assertIn(
            'NEW_DOMAINS = ("qol_items", "economy", "convenience")',
            self.runner,
        )
        for domain in (
            "static", "story", "menu", "route505", "species",
            "collection", "world", "qol_items", "economy", "convenience",
        ):
            self.assertIn(f'"{domain}"', self.runner)
        self.assertIn('"collection_mode": collection_mode', self.runner)
        self.assertIn('document.get("collection_mode") != "full"', self.builder)
        self.assertIn(
            'domains.get("collection", {}).get("mode") != "full"',
            self.builder,
        )

    def test_stage36_stale_all_feature_runner_is_not_stage58_gate(self) -> None:
        self.assertNotIn(
            '_compile(ROOT / "tools/mgba_qol_production_smoke.c"',
            self.runner,
        )
        self.assertIn("mgba_stage58_qol_item_effects_smoke.c", self.runner)
        self.assertIn("effect_item_count", self.runner)

    def test_effect_and_convenience_are_two_chain_fresh_process_contracts(self) -> None:
        self.assertIn('result["process_runs"] = chains * 2', self.runner)
        self.assertGreaterEqual(self.runner.count('"phase1"'), 4)
        self.assertGreaterEqual(self.runner.count('"reload"'), 4)
        self.assertIn('if runs != 2:', self.runner)

    def test_convenience_gate_requires_runtime_wild_sales_and_natural_codex(self) -> None:
        for key in (
            "kanto_wild_runtime_land_rate_species_level_field_return",
            "codex_result_win_loss_draw_table_exact",
            "kanto_wild_runtime_water_rate_species_level_field_return",
            "kanto_wild_runtime_rock_rate_species_level_field_return",
            "kanto_wild_runtime_fishing_rate_species_level_field_return",
            "kanto_wild_fishing_old_good_super_rng_boundaries",
            "thin_events_blockdata_walkable_non_event_adjacent",
            "thin_events_bag_full_retry_all_6",
            "thin_events_native_flag_neighbor_bits_stable",
            "thin_events_quest_log_normal_save_recorded",
            "thin_events_quest_log_reload_next_input_flag_stable",
            "mart_normal_ui_sell_ball",
            "mart_normal_ui_sell_item",
            "codex_npc_normal_a_battle_start_finish_field_return",
            "codex_natural_readkeys_all_11_requests",
            "codex_forfeit_result_kind_4",
            "codex_disconnect_cpu_controller_uninstalled",
            "codex_disconnect_cpu_normal_input_field_reward_return",
            "codex_cpu_win_thin_quantities_preserved",
            "codex_forfeit_thin_quantities_preserved",
            "codex_cpu_win_save_layout_restored",
            "codex_forfeit_save_layout_restored",
            "codex_external_capabilities_7fff_preserved",
            "codex_request_window_not_cleared",
            "codex_post_battle_closed_reset_boundary",
            "codex_external_mailbox_volatile_reset",
        ):
            self.assertIn(key, self.runner)
            self.assertIn(key, self.builder)
        self.assertIn('coverage.get("thin_retry") != 6', self.runner)
        self.assertIn('coverage.get("fishing_tiers") != 3', self.runner)
        self.assertIn('coverage.get("fishing_rng_samples") != 300', self.runner)
        self.assertIn(
            'coverage.get("codex_result_routes_exact") != 3', self.runner,
        )
        self.assertIn(
            'coverage.get("codex_battle_paths") != 2', self.runner,
        )
        self.assertIn(
            '"thin_events_quantities_preserved_across_normal_saves"',
            self.runner,
        )
        self.assertIn(
            '"codex_disconnect_cpu_win_result_kind_1"', self.runner,
        )
        self.assertIn(
            'get("evidence", {}).get("cpu_battle", {})', self.runner,
        )
        self.assertIn(
            'int(cpu_battle.get("outcome", -1)) != 1', self.runner,
        )
        self.assertIn(
            'int(cpu_battle.get("result_kind", -1)) != 1', self.runner,
        )
        self.assertIn('save_layout[f"{owner}_before"]', self.runner)
        self.assertIn('save_layout[f"{owner}_after_cpu"]', self.runner)
        self.assertIn('save_layout[f"{owner}_after_forfeit"]', self.runner)
        self.assertIn('save_layout[f"{owner}_before"]', self.builder)
        self.assertIn(
            'or coverage.get("wild_runtime_modes") != 4', self.runner,
        )
        for token in (
            'phase_coverage.get("thin_retry") != 6',
            'phase_coverage.get("wild_modes") != 4',
            'phase_coverage.get("wild_runtime_modes") != 4',
            'phase_coverage.get("fishing_rng_samples") != 300',
            'phase_coverage.get("codex_battle_paths") != 2',
            'phase_coverage.get("codex_result_routes_exact") != 3',
        ):
            self.assertIn(token, self.builder)

    def test_economy_gate_is_transaction_specific_and_fail_closed(self) -> None:
        self.assertIn("mgba_stage58_economy_smoke.c", self.runner)
        for key in (
            "normal_menu_cancel_no_mutation", "bag_full_no_debit",
            "cross_store_fault_rollback", "limited_repeatable_reopen",
            "normal_trainer_victory_prize_honey_normal_save_phase1",
            "factory_prepare_real_battles_bp_patch_normal_save_phase1",
            "fresh_process_trainer_prize_honey_reload",
            "fresh_process_factory_reward_ability_patch_reload",
        ):
            self.assertIn(key, self.runner)
        for token in (
            '"normal_trainer_victory_to_prize_honey_normal_save": True',
            '"factory_prepare_to_real_battle_to_bp_reward": True',
            '"fresh_process_earned_purchases_reload": True',
            'result["transaction_cases"] = 5',
            'result["economy_test_cases"] = len(phase1_tests | reload_tests)',
            'trainer.get("money_after_honey")',
            'factory.get("payload_starts")',
            'reload_evidence.get("ability_patch")',
            're.fullmatch(r"0x[0-9a-f]{16}", encoded_hash)',
            'normal_trainer_fixture_scope',
            'factory_fixture_scope',
        ):
            self.assertIn(token, self.runner)

    def test_cases_require_normal_bag_ui_and_effect_reload(self) -> None:
        self.assertIn(
            '"normal_bag_ui_family_paths_required": True', self.builder,
        )
        self.assertIn(
            '"cancel_effect_ineligible_reload_required": True', self.builder,
        )

    def test_final_gate_rejects_pending_mgba_evidence(self) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        rebuild = (ROOT / "scripts/rebuild_stage58_qol_world_convenience_debug_from_clean.py").read_text(encoding="utf-8")
        self.assertIn('"--require-mgba", action="store_true"', self.builder)
        self.assertIn('metadata.get("status") != "PASS"', self.builder)
        self.assertIn('stage58-final-gate:', makefile)
        self.assertGreaterEqual(makefile.count("--require-mgba"), 4)
        self.assertIn('source_metadata.get("status") != "PASS"', rebuild)
        self.assertLess(
            self.builder.index('if args.require_mgba and metadata.get("status") != "PASS"'),
            self.builder.index('if args.mode == "build"'),
        )

    def test_evidence_is_bound_to_cases_and_runner_sources(self) -> None:
        for token in (
            "VALIDATION_CONTRACT_ROOT_FILES",
            "_validation_contract_files",
            '"cases_sha256"',
            '"sources_sha256"',
            '"contract_sha256"',
            '"validation_contract": validation_contract(cases_path)',
        ):
            self.assertIn(token, self.runner)
        self.assertIn(
            'document.get("validation_contract") != expected_contract',
            self.builder,
        )
        self.assertIn(
            'Stage58 mGBA evidenceのcases/runner検証契約hash不一致',
            self.builder,
        )
        required = {
            "generated/runtime/collection_supply_v1_symbols.json",
            "generated/runtime/stage57_comprehensive_debug_repair_symbols.json",
            "generated/runtime/collection_supply_v1_mgba_cases.json",
            "build/stages/36_qol_production.json",
            "scripts/run_stage57_mgba_validation.py",
            "scripts/build_species_surface.py",
            "tools/mgba_species_runtime_smoke.c",
            "scripts/build_world_runtime_e2e_repair.py",
            "tools/world_runtime_e2e_repair.py",
            "tools/mgba_world_runtime_input_e2e.c",
            "tools/stage57_story_trainer_audit.py",
            "tools/mgba_codex_battle_ipad_bootstrap.c",
            "tools/mgba_battle_core_smoke.c",
            "tools/mgba_ai_fixture_runner.c",
            "tools/mgba_windows_box14_vault_smoke.c",
            "tools/mgba_windows_battle_catalog_smoke.c",
            "tools/mgba_codex_battle_rewards_smoke.c",
            "tools/mgba_codex_battle_runtime_smoke.c",
        }
        self.assertTrue(
            required <= set(validation_contract()["sources_sha256"])
        )


if __name__ == "__main__":
    unittest.main()
