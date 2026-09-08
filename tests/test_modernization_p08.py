#!/usr/bin/env python3
"""工程8統合監査checkpointのfocused tests。"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_modernization_p08 import render_outputs  # noqa: E402
from tools.modernization_p08_integration import (  # noqa: E402
    EXPECTED_EVIDENCE_SOURCE_COUNTS,
    ModernizationP08Error,
    PARALLEL_OUTPUTS,
    PINNED_IMPLEMENTATION_PATHS,
    PINNED_TRACKED_INPUTS,
    RELEASE_BLOCKERS,
    STATUS,
    _audit_candidate_artifacts,
    _audit_inputs,
    _validate_candidate_chain,
    _validate_contract_chain,
    audit_declared_source_rows,
    build_integration_fingerprint,
    build_integration_matrix,
    build_release_handoff,
    build_runtime_handoff,
    validate_active_baseline,
    validate_integration_matrix,
    verify_exact_bytes,
)


class ModernizationP08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 32 MiB候補ROM群と大きなcontractのhashは一度だけ計算する。
        cls.matrix = build_integration_matrix(ROOT)

    def test_active_play_baseline_remains_exact_stage62(self) -> None:
        active = self.matrix["active_play_baseline"]
        self.assertEqual(active["stage"], 62)
        self.assertFalse(active["changed"])
        self.assertFalse(active["candidate_auto_promoted"])
        self.assertEqual(
            active["config_sha256"],
            "4800257add049ea99cdedda91413a70a255dcff9a85823463596edefa8785053",
        )
        self.assertEqual(
            active["rom"]["sha256"],
            "d97a0d4a6cd6f8f77a1503a5ac6d473b0e94c4892e3d5a94098497ce35cb6e6f",
        )

    def test_only_p01_is_completed(self) -> None:
        phases = {row["phase"]: row for row in self.matrix["phases"]}
        self.assertEqual(phases["P01"]["completion_state"], "COMPLETED")
        for phase in ("P02", "P03", "P04", "P05", "P06", "P07"):
            self.assertEqual(phases[phase]["completion_state"], "CHECKPOINT_NOT_DONE")
        self.assertEqual(phases["P08"]["completion_state"], STATUS)
        self.assertEqual(
            self.matrix["integration_summary"]["completed_phases"], ["P01"]
        )
        self.assertEqual(
            self.matrix["integration_summary"]["highest_pinned_candidate_stage"], 76
        )
        self.assertFalse(self.matrix["integration_summary"]["release_ready"])
        self.assertFalse(self.matrix["release_ready"])

    def test_contract_pass_does_not_mean_phase_done(self) -> None:
        phases = {row["phase"]: row for row in self.matrix["phases"]}
        for phase in ("P02", "P03"):
            self.assertIn("PASS", phases[phase]["contract_statuses"])
            self.assertNotEqual(phases[phase]["completion_state"], "COMPLETED")

        for index in (1, 2):
            false_done = copy.deepcopy(self.matrix)
            false_done["phases"][index]["completion_state"] = "COMPLETED"
            with self.subTest(phase=false_done["phases"][index]["phase"]):
                with self.assertRaises(ModernizationP08Error):
                    validate_integration_matrix(false_done)

    def test_adoption_and_runtime_boundaries_are_explicit(self) -> None:
        phases = {row["phase"]: row for row in self.matrix["phases"]}
        self.assertEqual(phases["P01"]["adoption"]["runtime_corrections"], 2)
        self.assertEqual(phases["P02"]["adoption"]["stage64_changed_rom_bytes"], 2)
        self.assertEqual(phases["P02"]["adoption"]["actual_consumer_case_count"], 24)
        self.assertTrue(
            phases["P02"]["adoption"]["hidden_ability_readback_verified"]
        )
        self.assertEqual(phases["P02"]["adoption"]["hidden_ability_bit_mask"], 16)
        self.assertEqual(
            phases["P02"]["adoption"]["hidden_ability_observed_case_count"], 24
        )
        self.assertEqual(
            phases["P02"]["rom_reflection"],
            {
                "reflected": True,
                "stage": 67,
                "ancestor_stage": 64,
                "scope": "RAYQUAZA_FIX_PLUS_6_SPECIES_PRIORITY_REPAIR_IN_STAGE67_OVERLAY",
            },
        )
        self.assertEqual(phases["P03"]["adoption"]["source_routes"], 118_528)
        self.assertEqual(phases["P03"]["adoption"]["runtime_selected_routes"], 118_369)
        self.assertEqual(phases["P03"]["adoption"]["side_change_1063_source_routes"], 159)
        self.assertEqual(phases["P03"]["adoption"]["side_change_1063_excluded_routes"], 159)
        self.assertEqual(phases["P03"]["adoption"]["side_change_1063_adopted_routes"], 0)
        self.assertIsNone(phases["P03"]["adoption"]["side_change_1063_replacement_move_key"])
        self.assertEqual(phases["P03"]["adoption"]["stage65_preserved_ancestor_routes"], 4)
        self.assertEqual(phases["P03"]["adoption"]["stage65_changed_rom_bytes"], 17)
        self.assertEqual(phases["P03"]["adoption"]["stage66_routes_materialized"], 47_548)
        self.assertEqual(phases["P03"]["adoption"]["stage66_changed_rom_bytes"], 81_693)
        self.assertEqual(phases["P03"]["adoption"]["stage67_new_routes_materialized"], 3_603)
        self.assertEqual(phases["P03"]["adoption"]["stage73_new_runtime_materialized_routes"], 5_363)
        self.assertEqual(phases["P03"]["adoption"]["stage73_existing_owner_accounted_routes"], 35_207)
        self.assertEqual(phases["P03"]["adoption"]["stage73_consumer_boundary_accounted_routes"], 40_570)
        self.assertEqual(
            phases["P03"]["adoption"][
                "stage73_historical_upstream_dependency_overlap_routes"
            ],
            23_595,
        )
        self.assertEqual(phases["P03"]["adoption"]["stage73_hook_count"], 3)
        self.assertEqual(
            phases["P03"]["adoption"]["stage74_direct_supply_materialized_routes"],
            26_648,
        )
        self.assertEqual(phases["P03"]["adoption"]["stage74_direct_machine_routes"], 26_279)
        self.assertEqual(phases["P03"]["adoption"]["stage74_direct_tutor_routes"], 369)
        self.assertEqual(phases["P03"]["adoption"]["stage74_hook_count"], 2)
        self.assertEqual(phases["P03"]["adoption"]["cumulative_routes_materialized"], 83_162)
        self.assertEqual(phases["P03"]["adoption"]["cumulative_routes_accounted"], 118_369)
        self.assertEqual(phases["P03"]["adoption"]["selected_routes_remaining"], 0)
        self.assertEqual(phases["P03"]["adoption"]["preservation_missing_paths"], 4_014)
        self.assertEqual(phases["P03"]["adoption"]["preservation_target_move_pairs"], 2_223)
        self.assertEqual(phases["P03"]["adoption"]["preservation_ui_supply_routes_added"], 0)
        self.assertEqual(phases["P03"]["adoption"]["preservation_route_accounting_added"], 0)
        self.assertEqual(phases["P03"]["adoption"]["build_learnable_maximum_entries"], 238)
        self.assertEqual(phases["P03"]["adoption"]["build_learnable_capacity"], 429)
        self.assertEqual(phases["P03"]["adoption"]["build_learnable_overflow_species"], 0)
        self.assertEqual(phases["P03"]["adoption"]["archive_unlock_flag"], "0x082C")
        self.assertEqual(
            phases["P03"]["adoption"]["archive_economy"], "PROVISIONAL_REPLACEABLE"
        )
        self.assertEqual(
            phases["P03"]["adoption"]["withheld_own_tempo_rockruff_routes"], 38
        )
        self.assertEqual(
            phases["P03"]["adoption"]["stage75_own_tempo_rockruff_species_id"],
            1670,
        )
        self.assertEqual(
            phases["P03"]["adoption"]["stage75_own_tempo_rockruff_ability_id"],
            20,
        )
        self.assertEqual(
            phases["P03"]["adoption"]["stage75_pre_evolution_carry_paths_resolved"],
            38,
        )
        self.assertEqual(phases["P03"]["adoption"]["stage75_missing_owner_paths"], 0)
        self.assertEqual(
            phases["P03"]["adoption"]["stage75_source_owner_clone_routes"], 60
        )
        self.assertEqual(
            phases["P03"]["adoption"]["stage75_route_accounting_delta"], 0
        )
        self.assertEqual(phases["P03"]["adoption"]["stage75_allocation_sequence"], 78)
        self.assertEqual(phases["P03"]["adoption"]["stage75_allocation_count"], 79)
        self.assertEqual(phases["P03"]["adoption"]["browt_pombon_gecqua_materialized"], 0)
        self.assertEqual(phases["P03"]["adoption"]["prohibited_coercions_materialized"], 0)
        self.assertEqual(phases["P03"]["adoption"]["stage67_future_tail_remaining_bytes"], 62_510)
        self.assertEqual(phases["P04"]["adoption"]["selected_candidate_records"], 49)
        self.assertEqual(phases["P04"]["adoption"]["runtime_adopted_records"], 49)
        self.assertEqual(
            phases["P04"]["adoption"]["runtime_materialized_acquisition_routes"],
            46,
        )
        self.assertEqual(phases["P04"]["adoption"]["stone_item_ids_materialized"], 45)
        self.assertEqual(phases["P04"]["adoption"]["stone_shop_entries_materialized"], 45)
        self.assertEqual(phases["P04"]["adoption"]["stone_shop_currency"], "BP")
        self.assertEqual(phases["P04"]["adoption"]["stone_shop_price_each"], 16)
        self.assertEqual(
            phases["P04"]["adoption"]["floette_eternal_existing_species_id"], 1029
        )
        self.assertEqual(phases["P04"]["adoption"]["floette_eternal_gift_level"], 50)
        self.assertTrue(
            phases["P04"]["adoption"]["floette_eternal_exact_party_pc_delivery"]
        )
        self.assertFalse(
            phases["P04"]["adoption"]["floette_eternal_exact_full_and_fresh_reload"]
        )
        self.assertEqual(phases["P04"]["adoption"]["mega_form_battle_runtime_records"], 49)
        self.assertTrue(phases["P04"]["adoption"]["mega_form_species_runtime_materialized"])
        self.assertTrue(phases["P04"]["adoption"]["mega_form_battle_runtime_materialized"])
        self.assertFalse(phases["P04"]["adoption"]["mega_form_runtime_exact_mgba"])
        self.assertEqual(phases["P04"]["adoption"]["adopted_new_species_records"], 0)
        self.assertEqual(
            phases["P04"]["adoption"]["non_adopted_user_scope_records"], 3
        )
        self.assertEqual(phases["P05"]["adoption"]["performance_adjustments"], 0)
        self.assertEqual(phases["P05"]["adoption"]["new_move_requirements"], 0)
        self.assertEqual(phases["P05"]["adoption"]["non_adopted_move_candidates"], 1)
        self.assertEqual(phases["P05"]["adoption"]["non_adopted_p04_records"], 3)
        self.assertEqual(phases["P05"]["adoption"]["ability_host_runtime_cases"], 46)
        self.assertEqual(
            phases["P05"]["adoption"]["ability_ids"],
            [312, 313, 314, 315, 316, 317],
        )
        self.assertEqual(phases["P05"]["adoption"]["ability_rom_runtime_count"], 6)
        self.assertEqual(phases["P05"]["adoption"]["ability_rom_hook_count"], 29)
        self.assertTrue(phases["P05"]["adoption"]["ability_rom_linked"])
        self.assertFalse(phases["P05"]["adoption"]["ability_runtime_exact_mgba"])
        self.assertEqual(phases["P05"]["adoption"]["documented_ai_ui_edges_implemented"], 3)
        self.assertEqual(phases["P05"]["adoption"]["documented_ai_ui_edges_pending"], 1)
        self.assertEqual(phases["P05"]["adoption"]["stage76_allocation_sequence"], 79)
        self.assertEqual(phases["P05"]["adoption"]["stage76_allocation_count"], 80)
        self.assertEqual(phases["P05"]["adoption"]["stage76_changed_bytes"], 2_081)
        self.assertEqual(phases["P05"]["adoption"]["stage76_allowlist_outside"], 0)
        self.assertEqual(
            phases["P02"]["adoption"]["stage71_acceptance_status"],
            "STOPPED_EXACT_UI_PENDING",
        )
        self.assertEqual(
            phases["P02"]["adoption"]["stage71_production_runtime"], "UNJUDGED"
        )
        self.assertFalse(phases["P02"]["adoption"]["stage71_exact_ui_acceptance"])
        self.assertEqual(phases["P06"]["adoption"]["species_adjustment_records"], 0)
        self.assertEqual(phases["P07"]["adoption"]["normal_to_vega_move"], 0)
        self.assertTrue(phases["P03"]["rom_reflection"]["reflected"])
        self.assertEqual(phases["P03"]["rom_reflection"]["stage"], 75)
        self.assertTrue(phases["P04"]["rom_reflection"]["reflected"])
        self.assertEqual(phases["P04"]["rom_reflection"]["stage"], 71)
        self.assertTrue(phases["P05"]["rom_reflection"]["reflected"])
        self.assertEqual(phases["P05"]["rom_reflection"]["stage"], 76)
        self.assertEqual(
            phases["P04"]["adoption"]["asset_staging"],
            {
                "mega_covered": 49, "mega_required": 49,
                "stones_covered": 45, "stones_required": 45,
                "palette_ready": 49, "palette_required": 49,
                "winds_waves_covered": 0, "winds_waves_required": 0,
                "missing_assets": 0,
                "payload_file_count": 670,
                "payload_total_bytes": 426648,
                "asset_set_sha256": "462fed5d292582f44a29007e2da488829973c57b1964f86fa12e6da41c6e749c",
            },
        )
        self.assertEqual(
            phases["P04"]["adoption"]["capacity_reservation"],
            {
                "species_form": [1621, 1669],
                "item": [999, 1043],
                "ability": [312, 317],
                "move": None,
                "move_append_count": 0,
                "capacity_basis_stage": 65,
                "fixed_table_count": 34,
                "fixed_table_delta_bytes": 19857,
                "aligned_bundle_bytes": 636392,
                "integration_modules_remaining_bytes": 1124296,
                "stage66_cross_check": {
                    "allocation_region": "future_tail",
                    "allocation_start": 33399368,
                    "allocation_size": 60116,
                    "allocation_end_exclusive": 33459484,
                    "stage65_future_tail_remaining_bytes": 155064,
                    "stage66_future_tail_remaining_bytes": 94948,
                    "p04_candidate_region": "integration_modules",
                    "p04_candidate_start": 21307984,
                    "p04_candidate_end_exclusive": 23068672,
                    "overlap": False,
                },
                "runtime_ready": False,
            },
        )

    def test_stage76_chain_is_exact_but_not_release_candidate(self) -> None:
        chain = self.matrix["candidate_chain"]
        self.assertEqual(chain["active_stage"], 62)
        self.assertEqual(chain["selected_checkpoint_stage"], 76)
        self.assertTrue(chain["parent_chain_verified"])
        for stage in range(65, 77):
            self.assertTrue(chain[f"stage{stage}_integrated"])
        self.assertFalse(chain["release_candidate"])
        self.assertEqual(
            chain["inheritance"][5]["rom"]["sha256"],
            "13e4ecb6f2bc72eeb5d7ffb5b5e5a7a2ae2876391bf37ec93cb6548587265111",
        )
        self.assertEqual(chain["inheritance"][5]["parent_stage"], 66)
        self.assertEqual(chain["stage65_scope"]["routes_materialized"], 4)
        self.assertFalse(chain["stage65_scope"]["full_p03_done"])
        self.assertEqual(chain["stage66_scope"]["routes_materialized"], 47_548)
        self.assertEqual(chain["stage66_scope"]["routes_remaining"], 70_980)
        self.assertFalse(chain["stage66_scope"]["full_p03_done"])
        self.assertEqual(chain["stage67_scope"]["selected_routes"], 118_369)
        self.assertEqual(chain["stage67_scope"]["non_adopted_move_1063_routes"], 159)
        self.assertEqual(chain["stage67_scope"]["cumulative_materialized_routes"], 51_151)
        self.assertEqual(chain["stage67_scope"]["selected_routes_remaining"], 67_218)
        self.assertEqual(chain["stage67_scope"]["future_tail_remaining_bytes"], 62_510)
        self.assertFalse(chain["stage67_scope"]["full_p03_done"])
        self.assertEqual(
            chain["inheritance"][6]["rom"]["sha256"],
            "1ff9103becdeff8a22b5ffd45d3487b87d23bc7656415d660652d8a413da9639",
        )
        self.assertEqual(
            chain["inheritance"][7]["rom"]["sha256"],
            "6532002dabd3197ee6b8ded8b153a495d3241acf062fc931210987093172cb95",
        )
        expected_latest_chain = [
            (
                70,
                69,
                "5519bda92ddc9024e9dcd7583fc170797f533f78e5fb552bda328f246722f3ef",
            ),
            (
                71,
                70,
                "dbcc1194511f234c7d34c196082d59bfc0cb6aca6bb3b9c0f911bc8add4230bb",
            ),
            (
                72,
                71,
                "f27411a2dcef2ec2c1f3c06de624b24838683f5e77017fafa9bf445edc00d059",
            ),
            (
                73,
                72,
                "25329a1d5dd71a4f3c0adff8b337af1c4b3496e0aae64439ed2adebe338ce26a",
            ),
            (
                74,
                73,
                "481083bc50bd353955990375e3cc5e0a76f9b0f681ae54caa6c31f66ef22d65e",
            ),
            (
                75,
                74,
                "a179c024294f4f1bbf34eb603af255f6896265d9d8523344719b349f8a4495c3",
            ),
            (
                76,
                75,
                "f753f13720aeb5331cfc8a9bf9dd5fd4ad9ac34537356d20d76b73e0100100ac",
            ),
        ]
        for row, (stage, parent_stage, digest) in zip(
            chain["inheritance"][8:], expected_latest_chain
        ):
            self.assertEqual(row["stage"], stage)
            self.assertEqual(row["parent_stage"], parent_stage)
            self.assertEqual(row["rom"]["sha256"], digest)
        self.assertEqual(chain["stage68_scope"]["shop_entry_count"], 45)
        self.assertEqual(chain["stage68_scope"]["price_each"], 16)
        self.assertEqual(chain["stage68_scope"]["exact_rom_runtime_gate"], "PASS")
        self.assertFalse(
            chain["stage68_scope"]["mega_form_battle_runtime_materialized"]
        )
        self.assertEqual(chain["stage69_scope"]["existing_species_id"], 1029)
        self.assertTrue(chain["stage69_scope"]["exact_party_delivery"])
        self.assertTrue(chain["stage69_scope"]["exact_pc_delivery"])
        self.assertFalse(chain["stage69_scope"]["exact_full_and_fresh_reload"])
        self.assertEqual(chain["stage70_scope"]["mega_species_and_forms"], 49)
        self.assertEqual(chain["stage70_scope"]["new_normal_species"], 0)
        self.assertEqual(chain["stage71_scope"]["mega_form_battle_runtime_records"], 49)
        self.assertEqual(chain["stage71_scope"]["forward_entries_added"], 49)
        self.assertEqual(chain["stage71_scope"]["reverse_entries_added"], 49)
        self.assertFalse(chain["stage71_scope"]["exact_mgba"])
        self.assertEqual(
            chain["stage72_scope"]["ability_ids"], [312, 313, 314, 315, 316, 317]
        )
        self.assertEqual(chain["stage72_scope"]["battle_hook_count"], 29)
        self.assertFalse(chain["stage72_scope"]["exact_mgba"])
        stage73 = chain["stage73_scope"]
        self.assertEqual(stage73["new_runtime_materialized_routes"], 5_363)
        self.assertEqual(stage73["existing_owner_accounted_routes"], 35_207)
        self.assertEqual(stage73["consumer_boundary_accounted_routes"], 40_570)
        self.assertEqual(stage73["cumulative_new_runtime_materialized_routes"], 56_514)
        self.assertEqual(
            stage73["cumulative_consumer_boundary_accounted_routes"], 91_721
        )
        self.assertEqual(stage73["remaining_direct_supply_routes"], 26_648)
        self.assertEqual(
            stage73["machine_tutor_upstream_supply_dependency_routes"], 23_595
        )
        self.assertEqual(stage73["hook_count"], 3)
        self.assertEqual(stage73["side_change_materialized"], 0)
        self.assertEqual(stage73["browt_pombon_gecqua_materialized"], 0)
        self.assertEqual(stage73["prohibited_coercions_materialized"], 0)
        self.assertFalse(stage73["full_p03_done"])
        self.assertEqual(
            stage73["new_runtime_materialized_routes"]
            + stage73["existing_owner_accounted_routes"],
            stage73["consumer_boundary_accounted_routes"],
        )
        self.assertEqual(
            chain["stage67_scope"]["cumulative_materialized_routes"]
            + stage73["new_runtime_materialized_routes"],
            stage73["cumulative_new_runtime_materialized_routes"],
        )
        self.assertEqual(
            chain["stage67_scope"]["cumulative_materialized_routes"]
            + stage73["consumer_boundary_accounted_routes"],
            stage73["cumulative_consumer_boundary_accounted_routes"],
        )
        self.assertEqual(
            chain["stage67_scope"]["selected_routes"]
            - stage73["cumulative_consumer_boundary_accounted_routes"],
            stage73["remaining_direct_supply_routes"],
        )
        stage74 = chain["stage74_scope"]
        self.assertEqual(stage74["direct_supply_materialized_routes"], 26_648)
        self.assertEqual(stage74["direct_machine_routes"], 26_279)
        self.assertEqual(stage74["direct_tutor_routes"], 369)
        self.assertEqual(stage74["cumulative_runtime_materialized_routes"], 83_162)
        self.assertEqual(stage74["cumulative_accounted_routes"], 118_369)
        self.assertEqual(stage74["remaining_direct_supply_routes"], 0)
        self.assertEqual(stage74["preservation_missing_paths"], 4_014)
        self.assertEqual(stage74["preservation_target_move_pairs"], 2_223)
        self.assertEqual(stage74["preservation_species"], 501)
        self.assertEqual(
            stage74["preservation_target_move_set_sha256"],
            "0ccf54ee7e2617fefe99f974c1c3451a449c4701fedb6f49be3d8b4dedd02bfb",
        )
        self.assertEqual(stage74["preservation_ui_supply_routes_added"], 0)
        self.assertEqual(stage74["preservation_route_accounting_added"], 0)
        self.assertEqual(stage74["build_learnable_maximum_entries"], 238)
        self.assertEqual(stage74["build_learnable_capacity"], 429)
        self.assertEqual(stage74["build_learnable_overflow_species"], 0)
        self.assertEqual(stage74["unlock_flag"], "0x082C")
        self.assertEqual(stage74["economy"], "PROVISIONAL_REPLACEABLE")
        self.assertEqual(stage74["withheld_own_tempo_rockruff_routes"], 38)
        self.assertEqual(stage74["hook_count"], 2)
        self.assertEqual(stage74["side_change_materialized"], 0)
        self.assertEqual(stage74["browt_pombon_gecqua_materialized"], 0)
        self.assertEqual(stage74["prohibited_coercions_materialized"], 0)
        self.assertFalse(stage74["full_p03_done"])
        self.assertEqual(
            stage73["cumulative_new_runtime_materialized_routes"]
            + stage74["direct_supply_materialized_routes"],
            stage74["cumulative_runtime_materialized_routes"],
        )
        self.assertEqual(
            stage74["cumulative_runtime_materialized_routes"]
            + stage73["existing_owner_accounted_routes"],
            stage74["cumulative_accounted_routes"],
        )
        stage75 = chain["stage75_scope"]
        self.assertEqual(stage75["internal_species_id"], 1670)
        self.assertEqual(stage75["normal_species_id"], 1142)
        self.assertEqual(stage75["dusk_species_id"], 1263)
        self.assertEqual(stage75["national_dex"], 744)
        self.assertEqual(stage75["ability_id"], 20)
        self.assertEqual(stage75["species_count"], 1671)
        self.assertEqual(stage75["pre_evolution_carry_paths"], 38)
        self.assertEqual(stage75["missing_owner_paths"], 0)
        self.assertEqual(stage75["source_owner_clone_routes"], 60)
        self.assertEqual(stage75["route_accounting_delta"], 0)
        self.assertEqual(stage75["cumulative_runtime_materialized_routes"], 83_162)
        self.assertEqual(stage75["cumulative_accounted_routes"], 118_369)
        self.assertFalse(stage75["save_layout_changed"])
        self.assertEqual(stage75["archive_economy"], "PROVISIONAL_REPLACEABLE")
        self.assertEqual(stage75["allocation_sequence"], 78)
        self.assertEqual(stage75["allocation_count"], 79)
        self.assertFalse(stage75["full_p03_done"])
        self.assertFalse(stage75["exact_mgba"])
        stage76 = chain["stage76_scope"]
        self.assertEqual(stage76["implemented_edge_count"], 3)
        self.assertEqual(stage76["pending_edge_count"], 1)
        self.assertEqual(
            stage76["edges"],
            {
                "eelevate_dedicated_switch": (
                    "PENDING_UNSAFE_WITHOUT_FULL_GROUND_ABSORPTION_CONTEXT"
                ),
                "mega_sol_solar_charge_popup": "IMPLEMENT",
                "piercing_drill_ai_virtual_protect_quarter": "IMPLEMENT",
                "spicy_spray_friendly_fire_ai_score": "IMPLEMENT",
            },
        )
        self.assertEqual(stage76["allocation_parent_count"], 79)
        self.assertEqual(stage76["allocation_count"], 80)
        self.assertEqual(stage76["allocation_sequence"], 79)
        self.assertTrue(stage76["parent_first79_rows_all_fields_preserved"])
        self.assertEqual(stage76["rom_diff_allowlist_interval_count"], 5)
        self.assertEqual(stage76["changed_bytes_inside_allowlist"], 2_081)
        self.assertEqual(stage76["changed_bytes_outside_allowlist"], 0)
        self.assertEqual(stage76["eelevate_unsafe_hooks_installed"], 0)
        self.assertEqual(stage76["side_change_materialized"], 0)
        self.assertEqual(stage76["browt_pombon_gecqua_materialized"], 0)
        self.assertFalse(stage76["full_p05_done"])
        self.assertFalse(stage76["release_ready"])
        self.assertFalse(stage76["exact_mgba"])
        expected_latest_bps = [
            (
                "build/stages/69_modernization_floette_gift.gba",
                "build/stages/70_modernization_p04_species_runtime.bps",
                "build/stages/70_modernization_p04_species_runtime.gba",
            ),
            (
                "build/stages/70_modernization_p04_species_runtime.gba",
                "build/patches/stage70-to-stage71-modernization-p04-mega-runtime.bps",
                "build/stages/71_modernization_p04_mega_runtime.gba",
            ),
            (
                "build/stages/71_modernization_p04_mega_runtime.gba",
                "build/patches/stage71-to-stage72-modernization-p05-ability-rom-runtime.bps",
                "build/stages/72_modernization_p05_ability_rom_runtime.gba",
            ),
            (
                "build/stages/72_modernization_p05_ability_rom_runtime.gba",
                "build/patches/stage72-to-stage73-modernization-p03-consumer-runtime.bps",
                "build/stages/73_modernization_p03_consumer_runtime.gba",
            ),
            (
                "build/stages/73_modernization_p03_consumer_runtime.gba",
                "build/patches/stage73-to-stage74-modernization-p03-supply-runtime.bps",
                "build/stages/74_modernization_p03_supply_runtime.gba",
            ),
            (
                "build/stages/74_modernization_p03_supply_runtime.gba",
                "build/patches/stage74-to-stage75-modernization-rockruff-own-tempo.bps",
                "build/stages/75_modernization_rockruff_own_tempo.gba",
            ),
            (
                "build/stages/75_modernization_rockruff_own_tempo.gba",
                "build/patches/stage75-to-stage76-modernization-p05-edges.bps",
                "build/stages/76_modernization_p05_edges.gba",
            ),
        ]
        self.assertEqual(
            [
                (row["source"], row["patch"], row["target"])
                for row in chain["latest_incremental_bps"]
            ],
            expected_latest_bps,
        )
        self.assertEqual(
            [row["status"] for row in chain["latest_incremental_bps"]],
            ["PASS_EXACT_APPLY"] * 7,
        )
        self.assertEqual(
            chain["registry"],
            {
                "path": "config/modernization_candidate.json",
                "schema_version": 2,
                "status": "STAGE76_THREE_P05_EDGES_CHECKPOINT_NOT_RELEASE_CANDIDATE",
                "completed_through": "USER-MODERNIZATION-P01",
                "checkpointed_through": "USER-MODERNIZATION-P05-STAGE76-EDGES-CHECKPOINT",
                "checkpoint_commit": "cbf98eddf712ee677eef011e6fc106a67e536c08",
                "last_committed_checkpoint": "cbf98eddf712ee677eef011e6fc106a67e536c08",
                "release_ready": False,
                "active_parent_stage": 62,
                "parent_stage": 75,
                "candidate_stage": 76,
            },
        )

    def test_checkpointed_through_does_not_extend_completed_through(self) -> None:
        registry = self.matrix["candidate_chain"]["registry"]
        self.assertEqual(registry["completed_through"], "USER-MODERNIZATION-P01")
        self.assertIn("STAGE76", registry["checkpointed_through"])

        false_done = copy.deepcopy(self.matrix)
        false_done["candidate_chain"]["registry"]["completed_through"] = (
            "USER-MODERNIZATION-P03-STAGE67-CONSUMER-CHECKPOINT"
        )
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_done)

    def test_newly_tracked_checkpoints_are_explicitly_integrated(self) -> None:
        snapshot = self.matrix["snapshot"]
        self.assertFalse(snapshot["auto_discovery"])
        self.assertEqual(snapshot["parallel_outputs"], PARALLEL_OUTPUTS)
        pinned = {row["path"] for row in snapshot["tracked_inputs"]}
        for lane in PARALLEL_OUTPUTS.values():
            self.assertTrue(lane["included"])
            self.assertTrue(lane["status"])
            self.assertTrue(lane["expected_paths"])
        self.assertEqual(
            PARALLEL_OUTPUTS["P02_STAGE71_EXACT_UI_ACCEPTANCE"]["status"],
            "STOPPED_EXACT_UI_PENDING_PRODUCTION_UNJUDGED",
        )
        self.assertEqual(
            PARALLEL_OUTPUTS["P03_STAGE74_DIRECT_SUPPLY_RUNTIME"]["status"],
            "INTEGRATED_DIRECT_SUPPLY_CHECKPOINT_NOT_P03_DONE",
        )
        self.assertEqual(
            PARALLEL_OUTPUTS["P03_STAGE75_OWN_TEMPO_ROCKRUFF"]["status"],
            "INTEGRATED_INTERNAL_FORM_CHECKPOINT_NOT_P03_DONE",
        )
        self.assertEqual(
            PARALLEL_OUTPUTS["P05_STAGE76_SAFE_AI_UI_EDGES"]["status"],
            "INTEGRATED_THREE_EDGES_EELEVATE_MGBA_PENDING_NOT_P05_DONE",
        )
        self.assertIn("content/modernization/p03_stage65_checkpoint.json", pinned)
        self.assertIn("content/modernization/p03_stage65_mgba_runtime_gate.json", pinned)
        self.assertIn("config/modernization_p03_stage66.json", pinned)
        self.assertIn("content/modernization/p03_stage66_bulk_route_audit.json", pinned)
        self.assertIn("content/modernization/p03_stage66_change_audit.json", pinned)
        self.assertIn("content/modernization/p03_stage66_checkpoint.json", pinned)
        self.assertIn("content/modernization/p03_stage66_mgba_runtime_gate.json", pinned)
        self.assertIn("content/modernization/p02_acceptance_checkpoint.json", pinned)
        self.assertIn("config/modernization_adoption_decisions.json", pinned)
        self.assertIn("config/modernization_p03_stage67.json", pinned)
        self.assertIn("content/modernization/p03_stage67_checkpoint.json", pinned)
        self.assertIn("content/modernization/p03_stage67_mgba_runtime_gate.json", pinned)
        self.assertIn("content/modernization/p05_ability_runtime_checkpoint.json", pinned)
        self.assertIn("content/modernization/p04_asset_import_manifest.json", pinned)
        self.assertIn(
            "content/modernization/p04_capacity_allocation_manifest.json", pinned
        )
        self.assertIn("content/modernization/mega_shop_checkpoint.json", pinned)
        self.assertIn("content/modernization/mega_shop_mgba_runtime_gate.json", pinned)
        self.assertIn("content/modernization/floette_gift_checkpoint.json", pinned)
        self.assertIn("content/modernization/floette_gift_mgba_runtime_gate.json", pinned)
        latest_tracked = {
            "config/modernization_p02_stage71_acceptance_gate.json",
            "content/modernization/p02_stage71_acceptance_checkpoint.json",
            "config/modernization_p03_stage73_consumers.json",
            "config/modernization_p03_stage73_runtime.json",
            "content/modernization/p03_stage73_consumer_runtime_checkpoint.json",
            "content/modernization/p03_stage73_consumer_runtime_route_audit.json",
            "config/modernization_p03_stage74_supply.json",
            "content/modernization/p03_stage74_supply_runtime_checkpoint.json",
            "config/modernization_p04_species_runtime.json",
            "content/modernization/p04_species_runtime_contract.json",
            "content/modernization/p04_species_runtime_checkpoint.json",
            "config/modernization_p04_mega_runtime.json",
            "content/modernization/p04_mega_runtime_mapping.json",
            "content/modernization/p04_mega_runtime_checkpoint.json",
            "config/modernization_p05_ability_rom_runtime.json",
            "content/modernization/p05_ability_rom_runtime_checkpoint.json",
            "content/modernization/p05_ability_rom_runtime_surface_matrix.json",
            "config/modernization_rockruff_own_tempo_stage75.json",
            "content/modernization/rockruff_own_tempo_stage75_contract.json",
            "content/modernization/rockruff_own_tempo_stage75_checkpoint.json",
            "config/modernization_p05_stage76_edges.json",
            "content/modernization/p05_stage76_edges_contract.json",
            "content/modernization/p05_stage76_edges_checkpoint.json",
        }
        self.assertTrue(latest_tracked <= pinned)
        artifacts = {row["path"] for row in self.matrix["candidate_artifacts"]}
        self.assertTrue(
            {
                "build/stages/66_modernization_p03_bulk_learnsets.gba",
                "build/stages/66_modernization_p03_bulk_learnsets.json",
                "build/stages/66_modernization_p03_allocation.json",
                "build/patches/stage65-to-stage66-modernization-p03-bulk-learnsets.bps",
                "build/patches/firered-jpn-rev0-to-stage66-modernization-p03-bulk-learnsets.bps",
                "build/stages/67_modernization_p02_p03_consumers.gba",
                "build/stages/67_modernization_p02_p03_consumers.json",
                "build/stages/67_modernization_p03_allocation.json",
                "build/patches/stage66-p02-overlay-to-stage67-modernization-p03-consumers.bps",
                "build/patches/firered-jpn-rev0-to-stage67-modernization-p02-p03-consumers.bps",
                "build/stages/68_modernization_mega_shop.gba",
                "build/stages/68_modernization_mega_shop.json",
                "build/stages/68_modernization_mega_shop_allocation.json",
                "build/stages/68_modernization_mega_shop.bps",
                "build/stages/69_modernization_floette_gift.gba",
                "build/stages/69_modernization_floette_gift.json",
                "build/stages/69_modernization_floette_gift_allocation.json",
                "build/stages/69_modernization_floette_gift.bps",
                "build/stages/70_modernization_p04_species_runtime.gba",
                "build/stages/70_modernization_p04_species_runtime.json",
                "build/stages/70_modernization_p04_species_runtime_allocation.json",
                "build/stages/70_modernization_p04_species_runtime.bps",
                "build/stages/71_modernization_p04_mega_runtime.gba",
                "build/stages/71_modernization_p04_mega_runtime.json",
                "build/stages/71_modernization_p04_mega_runtime_allocation.json",
                "build/patches/stage70-to-stage71-modernization-p04-mega-runtime.bps",
                "build/stages/72_modernization_p05_ability_rom_runtime.gba",
                "build/stages/72_modernization_p05_ability_rom_runtime.json",
                "build/stages/72_modernization_p05_ability_rom_runtime_allocation.json",
                "build/patches/stage71-to-stage72-modernization-p05-ability-rom-runtime.bps",
                "build/stages/73_modernization_p03_consumer_runtime.gba",
                "build/stages/73_modernization_p03_consumer_runtime.json",
                "build/stages/73_modernization_p03_consumer_runtime_allocation.json",
                "build/patches/stage72-to-stage73-modernization-p03-consumer-runtime.bps",
                "build/stages/74_modernization_p03_supply_runtime.gba",
                "build/stages/74_modernization_p03_supply_runtime.json",
                "build/stages/74_modernization_p03_supply_runtime_allocation.json",
                "build/patches/stage73-to-stage74-modernization-p03-supply-runtime.bps",
                "generated/runtime/modernization_p03_stage74_supply_runtime.bin",
                "generated/runtime/modernization_p03_stage74_supply_runtime_symbols.json",
                "generated/runtime/modernization_p03_stage74_supply_runtime_audit.json",
                "generated/runtime/modernization_p03_stage74_supply_route_audit.json",
                "build/stages/75_modernization_rockruff_own_tempo.gba",
                "build/stages/75_modernization_rockruff_own_tempo.json",
                "build/stages/75_modernization_rockruff_own_tempo_allocation.json",
                "build/patches/stage74-to-stage75-modernization-rockruff-own-tempo.bps",
                "generated/runtime/modernization_rockruff_own_tempo_stage75.bin",
                "generated/runtime/modernization_rockruff_own_tempo_stage75_symbols.json",
                "generated/runtime/modernization_rockruff_own_tempo_stage75_audit.json",
                "generated/runtime/modernization_rockruff_own_tempo_stage75_route_audit.json",
                "build/stages/76_modernization_p05_edges.gba",
                "build/stages/76_modernization_p05_edges.json",
                "build/stages/76_modernization_p05_edges_allocation.json",
                "build/patches/stage75-to-stage76-modernization-p05-edges.bps",
                "generated/runtime/modernization_p05_stage76_edges.bin",
                "generated/runtime/modernization_p05_stage76_edges_symbols.json",
                "generated/runtime/modernization_p05_stage76_edges_audit.json",
            }
            <= artifacts
        )

    def test_pinned_input_and_referenced_source_hashes_pass(self) -> None:
        snapshot = self.matrix["snapshot"]
        self.assertEqual(snapshot["tracked_input_count"], len(PINNED_TRACKED_INPUTS))
        self.assertEqual(len(snapshot["tracked_inputs"]), len(PINNED_TRACKED_INPUTS))
        self.assertEqual(snapshot["implementation_input_count"], len(PINNED_IMPLEMENTATION_PATHS))
        self.assertEqual(
            len(snapshot["implementation_inputs"]), len(PINNED_IMPLEMENTATION_PATHS)
        )
        self.assertIn(
            "scripts/run_modernization_p03_stage66_mgba.py",
            {row["path"] for row in snapshot["implementation_inputs"]},
        )
        required_direct_implementation_inputs = {
            "scripts/build_trainer_v5_stage32.py",
            "tools/rom_allocator.py",
            "tools/release/__init__.py",
            "tools/release/bps.py",
            "Makefile",
            ".github/workflows/private-runtime.yml",
            ".github/workflows/chatgpt-comment-control.yml",
            "infra/setup_github_actions.sh",
            "infra/toolchain_manifest.json",
            "scripts/build_modernization_p03_stage66.py",
            "scripts/run_modernization_p03_stage66_mgba.py",
            "tools/modernization_p03_stage66.py",
            "tools/mgba_modernization_p03_stage66_smoke.c",
            "tests/test_modernization_p03_stage66.py",
            "scripts/build_modernization_p03_stage67.py",
            "scripts/run_modernization_p03_stage67_mgba.py",
            "tools/modernization_p03_stage67.py",
            "tools/mgba_modernization_p03_stage67_smoke.c",
            "tests/test_modernization_p03_stage67.py",
            "scripts/build_modernization_p05_ability_runtime.py",
            "tools/modernization_p05_ability_runtime.py",
            "tests/test_modernization_p05_ability_runtime.py",
            "scripts/build_modernization_mega_shop.py",
            "scripts/run_modernization_mega_shop_mgba.py",
            "tools/modernization_mega_shop.py",
            "tools/mgba_modernization_mega_shop_smoke.c",
            "tests/test_modernization_mega_shop.py",
            "tests/test_modernization_mega_shop_mgba.py",
            "scripts/build_modernization_floette_gift.py",
            "tools/modernization_floette_gift.py",
            "tests/test_modernization_floette_gift.py",
            "scripts/build_modernization_p04_species_runtime.py",
            "tools/modernization_p04_species_runtime.py",
            "tests/test_modernization_p04_species_runtime.py",
            "overlays/modernization_p04_species_runtime/README.md",
            "scripts/build_modernization_p04_mega_runtime.py",
            "tools/modernization_p04_mega_runtime.py",
            "tests/test_modernization_p04_mega_runtime.py",
            "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle.c",
            "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle.h",
            "overlays/modernization_p04_mega_runtime/modernization_p04_mega_runtime_oracle_host.c",
            "scripts/build_modernization_p05_ability_rom_runtime.py",
            "tools/modernization_p05_ability_rom_runtime.py",
            "tests/test_modernization_p05_ability_rom_runtime.py",
            "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c",
            "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.h",
            "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.ld",
            "overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S",
            "tools/modernization_p03_stage73_consumers.py",
            "tests/test_modernization_p03_stage73_consumers.py",
            "scripts/build_modernization_p03_stage73_runtime.sh",
            "tools/modernization_p03_stage73_runtime.py",
            "tests/test_modernization_p03_stage73_runtime.py",
            "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.c",
            "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.h",
            "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime.ld",
            "overlays/modernization_p03_stage73_consumer_runtime/modernization_p03_stage73_consumer_runtime_hooks.S",
            "scripts/build_modernization_p03_stage74_supply.sh",
            "tools/modernization_p03_stage74_supply.py",
            "tests/test_modernization_p03_stage74_supply.py",
            "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.c",
            "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.h",
            "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.ld",
            "overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime_scripts.S",
            "scripts/run_modernization_p02_stage71_acceptance.py",
            "tools/mgba_modernization_p02_stage71_acceptance_smoke.c",
            "tests/test_modernization_p02_stage71_acceptance.py",
            "scripts/build_modernization_rockruff_own_tempo_stage75.sh",
            "tools/modernization_rockruff_own_tempo_stage75.py",
            "tests/test_modernization_rockruff_own_tempo_stage75.py",
            "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.c",
            "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.h",
            "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.ld",
            "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75_scripts.S",
            "scripts/build_modernization_p05_stage76_edges.sh",
            "tools/modernization_p05_stage76_edges.py",
            "tests/test_modernization_p05_stage76_edges.py",
            "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.c",
            "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.h",
            "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges.ld",
            "overlays/modernization_p05_stage76_edges/modernization_p05_stage76_edges_hooks.S",
        }
        self.assertTrue(
            required_direct_implementation_inputs
            <= {row["path"] for row in snapshot["implementation_inputs"]}
        )
        self.assertEqual(
            len(self.matrix["referenced_source_bindings"]),
            sum(EXPECTED_EVIDENCE_SOURCE_COUNTS.values()),
        )
        self.assertTrue(
            all(row["status"] == "PASS" for row in self.matrix["referenced_source_bindings"])
        )

    def test_declared_evidence_source_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = "tools/source.py"
            path = root / relative
            path.parent.mkdir(parents=True)
            original = b"print('fixed')\n"
            path.write_bytes(original)
            row = {
                "path": relative,
                "size": len(original),
                "sha256": hashlib.sha256(original).hexdigest(),
            }
            self.assertEqual(
                audit_declared_source_rows(
                    root, [row], {relative}, binding="FIXTURE",
                )[0]["status"],
                "PASS",
            )
            path.write_bytes(b"print('drift')\n")
            with self.assertRaises(ModernizationP08Error):
                audit_declared_source_rows(
                    root, [row], {relative}, binding="FIXTURE",
                )

    def test_hash_drift_is_rejected(self) -> None:
        raw = b"fixed input\n"
        digest = hashlib.sha256(raw).hexdigest()
        self.assertEqual(
            verify_exact_bytes("fixture", raw, len(raw), digest)["sha256"], digest
        )
        with self.assertRaises(ModernizationP08Error):
            verify_exact_bytes("fixture", raw + b"drift", len(raw), digest)

        mutated = copy.deepcopy(self.matrix)
        mutated["snapshot"]["tracked_inputs"][0]["sha256"] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(mutated)

        implementation_drift = copy.deepcopy(self.matrix)
        implementation_drift["snapshot"]["implementation_inputs"][0]["sha256"] = (
            "0" * 64
        )
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(implementation_drift)

    def test_active_baseline_change_is_rejected(self) -> None:
        active_doc = json.loads((ROOT / "config/active_play_baseline.json").read_text())
        active_doc["stage"] = 64
        markdown = (ROOT / "design/active_play_baseline.md").read_bytes()
        stage62 = self.matrix["active_play_baseline"]["rom"]
        with self.assertRaises(ModernizationP08Error):
            validate_active_baseline(active_doc, markdown, stage62)

        mutated = copy.deepcopy(self.matrix)
        mutated["active_play_baseline"]["changed"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(mutated)

    def test_candidate_hash_or_false_release_is_rejected(self) -> None:
        bad_hash = copy.deepcopy(self.matrix)
        bad_hash["candidate_artifacts"][0]["sha256"] = "f" * 64
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(bad_hash)

        false_release = copy.deepcopy(self.matrix)
        false_release["release_ready"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_release)

        false_p03_done = copy.deepcopy(self.matrix)
        false_p03_done["candidate_chain"]["stage74_scope"]["full_p03_done"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_p03_done)

        stage75_mutations = (
            ("internal_species_id", 1669),
            ("ability_id", 21),
            ("pre_evolution_carry_paths", 37),
            ("missing_owner_paths", 1),
            ("source_owner_clone_routes", 59),
            ("route_accounting_delta", 1),
            ("allocation_sequence", 77),
            ("allocation_count", 78),
            ("save_layout_changed", True),
            ("archive_economy", "FINAL_FREE"),
            ("full_p03_done", True),
            ("exact_mgba", True),
        )
        for key, value in stage75_mutations:
            mutated = copy.deepcopy(self.matrix)
            mutated["candidate_chain"]["stage75_scope"][key] = value
            with self.subTest(stage75_scope=key):
                with self.assertRaises(ModernizationP08Error):
                    validate_integration_matrix(mutated)

        stage76_mutations = (
            ("implemented_edge_count", 4),
            ("pending_edge_count", 0),
            ("allocation_parent_count", 78),
            ("allocation_count", 79),
            ("allocation_sequence", 78),
            ("parent_first79_rows_all_fields_preserved", False),
            ("rom_diff_allowlist_interval_count", 6),
            ("changed_bytes_inside_allowlist", 2_080),
            ("changed_bytes_outside_allowlist", 1),
            ("eelevate_unsafe_hooks_installed", 1),
            ("full_p05_done", True),
            ("release_ready", True),
            ("exact_mgba", True),
        )
        for key, value in stage76_mutations:
            mutated = copy.deepcopy(self.matrix)
            mutated["candidate_chain"]["stage76_scope"][key] = value
            with self.subTest(stage76_scope=key):
                with self.assertRaises(ModernizationP08Error):
                    validate_integration_matrix(mutated)

        false_eelevate = copy.deepcopy(self.matrix)
        false_eelevate["candidate_chain"]["stage76_scope"]["edges"][
            "eelevate_dedicated_switch"
        ] = "IMPLEMENT"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_eelevate)

        false_stage76_rom = copy.deepcopy(self.matrix)
        next(
            row
            for row in false_stage76_rom["candidate_artifacts"]
            if row["path"] == "build/stages/76_modernization_p05_edges.gba"
        )["sha256"] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_stage76_rom)

        false_stage75_bps = copy.deepcopy(self.matrix)
        false_stage75_bps["candidate_chain"]["latest_incremental_bps"][-2][
            "target"
        ] = "build/stages/74_modernization_p03_supply_runtime.gba"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_stage75_bps)

        false_stage76_bps = copy.deepcopy(self.matrix)
        false_stage76_bps["candidate_chain"]["latest_incremental_bps"][-1][
            "source"
        ] = "build/stages/74_modernization_p03_supply_runtime.gba"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_stage76_bps)

        stage74_mutations = (
            ("direct_supply_materialized_routes", 26_647),
            ("cumulative_runtime_materialized_routes", 106_757),
            ("cumulative_accounted_routes", 141_964),
            ("remaining_direct_supply_routes", 1),
            ("preservation_missing_paths", 4_013),
            ("preservation_target_move_pairs", 2_222),
            ("preservation_ui_supply_routes_added", 1),
            ("preservation_route_accounting_added", 4_014),
            ("build_learnable_maximum_entries", 430),
            ("build_learnable_capacity", 428),
            ("build_learnable_overflow_species", 1),
            ("economy", "FINAL_FREE"),
            ("withheld_own_tempo_rockruff_routes", 0),
            ("side_change_materialized", 1),
            ("browt_pombon_gecqua_materialized", 1),
            ("prohibited_coercions_materialized", 1),
        )
        for key, value in stage74_mutations:
            mutated = copy.deepcopy(self.matrix)
            mutated["candidate_chain"]["stage74_scope"][key] = value
            with self.subTest(stage74_scope=key):
                with self.assertRaises(ModernizationP08Error):
                    validate_integration_matrix(mutated)

        false_preservation_hash = copy.deepcopy(self.matrix)
        false_preservation_hash["candidate_chain"]["stage74_scope"][
            "preservation_target_move_set_sha256"
        ] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_preservation_hash)

        false_side_change = copy.deepcopy(self.matrix)
        false_side_change["phases"][2]["adoption"][
            "side_change_1063_adopted_routes"
        ] = 159
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_side_change)

        false_ability_gate = copy.deepcopy(self.matrix)
        false_ability_gate["phases"][4]["adoption"][
            "ability_host_runtime_cases"
        ] = 44
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_ability_gate)

        false_hidden_ability_readback = copy.deepcopy(self.matrix)
        false_hidden_ability_readback["phases"][1]["adoption"][
            "hidden_ability_readback_verified"
        ] = False
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_hidden_ability_readback)

        false_p02_rom = copy.deepcopy(self.matrix)
        false_p02_rom["phases"][1]["rom_reflection"]["stage"] = 64
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_p02_rom)

        false_p04_rom = copy.deepcopy(self.matrix)
        false_p04_rom["phases"][3]["rom_reflection"]["reflected"] = False
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_p04_rom)

        false_mega_runtime = copy.deepcopy(self.matrix)
        false_mega_runtime["phases"][3]["adoption"][
            "mega_form_battle_runtime_records"
        ] = 0
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_mega_runtime)

        false_accounting = copy.deepcopy(self.matrix)
        false_accounting["candidate_chain"]["stage73_scope"][
            "existing_owner_accounted_routes"
        ] += 1
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_accounting)

        false_materialized = copy.deepcopy(self.matrix)
        false_materialized["candidate_chain"]["stage73_scope"][
            "cumulative_new_runtime_materialized_routes"
        ] = 91_721
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_materialized)

        false_stage73_exclusion = copy.deepcopy(self.matrix)
        false_stage73_exclusion["candidate_chain"]["stage73_scope"][
            "browt_pombon_gecqua_materialized"
        ] = 1
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_stage73_exclusion)

        false_stage72_hook_count = copy.deepcopy(self.matrix)
        false_stage72_hook_count["candidate_chain"]["stage72_scope"][
            "battle_hook_count"
        ] = 28
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_stage72_hook_count)

        false_p02_stage71_acceptance = copy.deepcopy(self.matrix)
        false_p02_stage71_acceptance["phases"][1]["adoption"][
            "stage71_acceptance_status"
        ] = "PASS"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_p02_stage71_acceptance)

        false_bps = copy.deepcopy(self.matrix)
        false_bps["candidate_chain"]["latest_incremental_bps"][0]["status"] = "PASS"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_bps)

        false_bps_source = copy.deepcopy(self.matrix)
        false_bps_source["candidate_chain"]["latest_incremental_bps"][0][
            "source"
        ] = "build/stages/68_modernization_mega_shop.gba"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_bps_source)

        false_bps_patch = copy.deepcopy(self.matrix)
        false_bps_patch["candidate_chain"]["latest_incremental_bps"][0][
            "patch"
        ] = "build/stages/69_modernization_floette_gift.bps"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_bps_patch)

        false_latest_parent = copy.deepcopy(self.matrix)
        false_latest_parent["candidate_chain"]["inheritance"][-1]["parent_stage"] = 71
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_latest_parent)

        false_inheritance_role = copy.deepcopy(self.matrix)
        false_inheritance_role["candidate_chain"]["inheritance"][-1][
            "role"
        ] = "P03_DONE"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_inheritance_role)

        false_inheritance_rom = copy.deepcopy(self.matrix)
        false_inheritance_rom["candidate_chain"]["inheritance"][-1]["rom"][
            "sha256"
        ] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_inheritance_rom)

        false_stage73_side_change = copy.deepcopy(self.matrix)
        false_stage73_side_change["candidate_chain"]["stage73_scope"][
            "side_change_materialized"
        ] = 1
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_stage73_side_change)

        false_ability_ids = copy.deepcopy(self.matrix)
        false_ability_ids["candidate_chain"]["stage72_scope"]["ability_ids"][-1] = 318
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_ability_ids)

        false_chain_release = copy.deepcopy(self.matrix)
        false_chain_release["candidate_chain"]["release_candidate"] = True
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_chain_release)

        false_release_blocker = copy.deepcopy(self.matrix)
        false_release_blocker["release_blockers"][0] = "NOT_A_REAL_BLOCKER"
        with self.assertRaises(ModernizationP08Error):
            validate_integration_matrix(false_release_blocker)

    def test_candidate_registry_semantic_mutations_are_rejected(self) -> None:
        documents, _, _ = _audit_inputs(ROOT)
        artifact_audit, metadata = _audit_candidate_artifacts(ROOT)

        false_patch_target = copy.deepcopy(documents)
        false_patch_target["config/modernization_candidate.json"]["patches"][
            "from_parent"
        ]["target_sha256"] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            _validate_contract_chain(false_patch_target)

        false_stage73_boundary = copy.deepcopy(documents)
        false_stage73_boundary["config/modernization_candidate.json"][
            "adopted_delta"
        ]["p03_stage73_consumer_checkpoint"]["hook_count"] = 2
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                metadata,
                false_stage73_boundary["config/modernization_candidate.json"],
            )

        false_stage74_boundary = copy.deepcopy(documents)
        false_stage74_boundary["config/modernization_candidate.json"][
            "adopted_delta"
        ]["p03_stage74_supply_checkpoint"]["preservation_target_move_pairs"] = 2_222
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                metadata,
                false_stage74_boundary["config/modernization_candidate.json"],
            )

        false_stage74_economy = copy.deepcopy(documents)
        false_stage74_economy["config/modernization_candidate.json"][
            "adopted_delta"
        ]["p03_stage74_supply_checkpoint"]["economy"] = "FINAL_FREE"
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                metadata,
                false_stage74_economy["config/modernization_candidate.json"],
            )

        false_sequence33 = copy.deepcopy(metadata)
        allocation74 = false_sequence33[
            "build/stages/74_modernization_p03_supply_runtime_allocation.json"
        ]
        next(
            row for row in allocation74["allocations"] if row["sequence"] == 33
        )["content_sha256"] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                false_sequence33,
                documents["config/modernization_candidate.json"],
            )

        false_stage75_owner = copy.deepcopy(documents)
        false_stage75_owner["config/modernization_candidate.json"][
            "adopted_delta"
        ]["p03_stage75_own_tempo_checkpoint"]["internal_species_id"] = 1669
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                metadata,
                false_stage75_owner["config/modernization_candidate.json"],
            )

        false_stage75_accounting = copy.deepcopy(documents)
        false_stage75_accounting["config/modernization_candidate.json"][
            "adopted_delta"
        ]["p03_stage75_own_tempo_checkpoint"]["route_accounting_delta"] = 1
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                metadata,
                false_stage75_accounting["config/modernization_candidate.json"],
            )

        false_stage76_edges = copy.deepcopy(documents)
        false_stage76_edges["config/modernization_candidate.json"][
            "adopted_delta"
        ]["p05_stage76_edges_checkpoint"]["pending_edge_count"] = 0
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                metadata,
                false_stage76_edges["config/modernization_candidate.json"],
            )

        false_stage76_allowlist = copy.deepcopy(documents)
        false_stage76_allowlist["config/modernization_candidate.json"][
            "adopted_delta"
        ]["p05_stage76_edges_checkpoint"]["changed_bytes_outside_allowlist"] = 1
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                metadata,
                false_stage76_allowlist["config/modernization_candidate.json"],
            )

        false_sequence77 = copy.deepcopy(metadata)
        allocation74 = false_sequence77[
            "build/stages/74_modernization_p03_supply_runtime_allocation.json"
        ]
        next(
            row for row in allocation74["allocations"] if row["sequence"] == 77
        )["size"] = 70_571
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                false_sequence77,
                documents["config/modernization_candidate.json"],
            )

        false_sequence78 = copy.deepcopy(metadata)
        allocation75 = false_sequence78[
            "build/stages/75_modernization_rockruff_own_tempo_allocation.json"
        ]
        next(
            row for row in allocation75["allocations"] if row["sequence"] == 78
        )["content_sha256"] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                false_sequence78,
                documents["config/modernization_candidate.json"],
            )

        false_sequence79 = copy.deepcopy(metadata)
        allocation76 = false_sequence79[
            "build/stages/76_modernization_p05_edges_allocation.json"
        ]
        next(
            row for row in allocation76["allocations"] if row["sequence"] == 79
        )["start"] += 16
        with self.assertRaises(ModernizationP08Error):
            _validate_candidate_chain(
                ROOT,
                artifact_audit,
                false_sequence79,
                documents["config/modernization_candidate.json"],
            )

        false_stage75_contract = copy.deepcopy(documents)
        false_stage75_contract[
            "content/modernization/rockruff_own_tempo_stage75_checkpoint.json"
        ]["p03"]["missing_owner_paths"] = 1
        with self.assertRaises(ModernizationP08Error):
            _validate_contract_chain(false_stage75_contract)

        false_stage76_contract = copy.deepcopy(documents)
        false_stage76_contract[
            "content/modernization/p05_stage76_edges_checkpoint.json"
        ]["edges"]["eelevate_dedicated_switch"] = "IMPLEMENT"
        with self.assertRaises(ModernizationP08Error):
            _validate_contract_chain(false_stage76_contract)

        false_checkpoint_preservation = copy.deepcopy(documents)
        false_checkpoint_preservation[
            "content/modernization/p03_stage74_supply_runtime_checkpoint.json"
        ]["build_learnable_preservation"]["route_accounting_added"] = 4_014
        with self.assertRaises(ModernizationP08Error):
            _validate_contract_chain(false_checkpoint_preservation)

        false_family_hash = copy.deepcopy(documents)
        false_family_hash["config/modernization_p03_stage74_supply.json"][
            "supply_contract"
        ]["machine"]["set_sha256"] = "0" * 64
        with self.assertRaises(ModernizationP08Error):
            _validate_contract_chain(false_family_hash)

    def test_every_requirement_has_implementation_and_test_mapping(self) -> None:
        trace = self.matrix["traceability"]
        self.assertGreaterEqual(len(trace), 21)
        self.assertEqual(len({row["requirement_key"] for row in trace}), len(trace))
        by_requirement = {row["requirement_key"]: row for row in trace}
        self.assertEqual(
            by_requirement["P04_CAPACITY_RESERVATION"]["implementation_evidence"],
            "49/45/6/0 append reservation + 34-table capacity audit",
        )
        self.assertEqual(
            by_requirement["P03_STAGE74_DIRECT_SUPPLY"]["test_evidence"],
            "tests/test_modernization_p03_stage74_supply.py",
        )
        self.assertEqual(
            by_requirement["P03_STAGE75_OWN_TEMPO_ROCKRUFF"]["test_evidence"],
            "tests/test_modernization_rockruff_own_tempo_stage75.py",
        )
        self.assertEqual(
            by_requirement["P05_STAGE76_SAFE_AI_UI_EDGES"]["test_evidence"],
            "tests/test_modernization_p05_stage76_edges.py",
        )
        for row in trace:
            self.assertTrue(row["implementation_evidence"])
            self.assertTrue(row["test_evidence"])
            self.assertTrue(row["status"])
        for phase in self.matrix["phases"]:
            self.assertTrue(phase["required_gates"])
            if phase["phase"] != "P01":
                self.assertTrue(phase["blockers"])

    def test_runtime_and_release_handoffs_stay_blocked(self) -> None:
        runtime = build_runtime_handoff(self.matrix)
        release = build_release_handoff(self.matrix)
        self.assertEqual(runtime["status"], STATUS)
        self.assertFalse(runtime["release_ready"])
        self.assertFalse(runtime["runtime_execution"]["new_rom_written"])
        self.assertEqual(
            runtime["integration_fingerprint"],
            self.matrix["snapshot"]["integration_fingerprint"],
        )
        self.assertEqual(release["status"], STATUS)
        self.assertFalse(release["release_ready"])
        self.assertFalse(release["promotion"]["authorized"])
        self.assertEqual(release["completed_phases"], ["P01"])
        self.assertEqual(release["candidate_stage"], 76)
        self.assertEqual(
            release["integration_fingerprint"],
            self.matrix["snapshot"]["integration_fingerprint"],
        )
        self.assertEqual(release["release_blockers"], list(RELEASE_BLOCKERS))

    def test_composite_fingerprint_changes_for_one_byte_implementation_drift(self) -> None:
        snapshot = self.matrix["snapshot"]
        original = snapshot["integration_fingerprint"]
        implementation = copy.deepcopy(snapshot["implementation_inputs"])
        source_path = ROOT / implementation[0]["path"]
        one_byte_drift = source_path.read_bytes() + b"\x00"
        implementation[0]["size"] = len(one_byte_drift)
        implementation[0]["sha256"] = hashlib.sha256(one_byte_drift).hexdigest()
        changed = build_integration_fingerprint(
            snapshot["tracked_inputs"],
            implementation,
            self.matrix["referenced_source_bindings"],
            self.matrix["candidate_artifacts"],
            self.matrix["phases"],
        )
        self.assertNotEqual(changed["sha256"], original["sha256"])
        self.assertNotEqual(
            changed["components"]["implementation_inputs"]["sha256"],
            original["components"]["implementation_inputs"]["sha256"],
        )

    def test_generated_outputs_are_deterministic(self) -> None:
        outputs = render_outputs(self.matrix)
        self.assertEqual(
            set(outputs),
            {
                "content/modernization/p08_integration_matrix.json",
                "content/modernization/p08_runtime_handoff.json",
                "content/modernization/p08_release_handoff.json",
            },
        )
        for relative, raw in outputs.items():
            self.assertEqual((ROOT / relative).read_bytes(), raw, relative)
            self.assertIsInstance(json.loads(raw), dict)


if __name__ == "__main__":
    unittest.main()
