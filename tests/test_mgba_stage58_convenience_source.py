from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/mgba_stage58_convenience_smoke.c"


class Stage58ConvenienceMgbaSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_runner_has_exact_rom_and_fresh_process_phase_contract(self) -> None:
        self.assertIn("strcmp(rom_sha256, cases.rom_sha256)", self.source)
        self.assertIn('"phase1"', self.source)
        self.assertIn('"reload"', self.source)
        self.assertNotIn("QOL_TRY_SAVING_DATA", self.source)
        self.assertIn("s58_continue_to_hub", self.source)
        self.assertNotIn("QOL_LOAD_GAME_DATA", self.source)

    def test_host_direct_calls_use_unowned_scratch_stack(self) -> None:
        for token in (
            "#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1",
            "#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U",
            "#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U",
        ):
            self.assertIn(token, self.source)
        self.assertNotIn(
            "#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203F000U",
            self.source,
        )

        bottom, top = 0x0203DB00, 0x0203DF80
        with (ROOT / "config" / "ram_layout.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            live_ewram = [
                row for row in csv.DictReader(handle)
                if row["status"] == "LIVE"
                and row["address_space"] == "EWRAM"
            ]
        overlaps = [
            row["owner"] for row in live_ewram
            if max(bottom, int(row["start"], 0))
            < min(top, int(row["end_exclusive"], 0))
        ]
        self.assertEqual(overlaps, [])
        self.assertLessEqual(top, 0x0203DFA0)

    def test_every_checkpoint_uses_physical_normal_menu_save(self) -> None:
        for token in (
            "s58_bind_bag_pockets",
            "static const uint8_t capacities[5] = {42U, 30U, 13U, 58U, 43U}",
            "read8(core, descriptor + 4U) != capacities[pocket]",
            "save_started && recorded",
            "menu_callback == S58_STARTMENU_SAVE_CALLBACK",
            "S58_STARTMENU_SAVE_CALLBACK = 0x0806EDB9U",
            "Same-file save is DefaultYes",
            "#include <mgba/flags.h>",
            "core->savedataClone(core, &sram)",
            "size != QOL_SAVE_SIZE",
            "savedata_now != savedata_before",
            "S58_SAVE2_KEY_OFFSET",
        ):
            self.assertIn(token, self.source)
        # Host-direct TrySavingData rotates the key without the normal menu's
        # pocket re-encryption owner, so it is forbidden at every checkpoint.
        self.assertEqual(self.source.count("QOL_TRY_SAVING_DATA"), 0)
        self.assertGreaterEqual(
            self.source.count("s58_normal_menu_save("), 7
        )

    def test_hub_services_are_exercised_through_gba_object_input(self) -> None:
        self.assertIn("S58_OBJECT_EVENTS = 0x02036D6CU", self.source)
        self.assertIn("object->x + 7U", self.source)
        self.assertIn("s58_face_and_interact(core, &cases->hub.pc)", self.source)
        self.assertIn("s58_face_and_interact(core, &cases->hub.healer)", self.source)
        self.assertIn("s58_face_and_interact(core, &cases->hub.mart)", self.source)
        self.assertIn("qol_press(core, QOL_KEY_A", self.source)
        self.assertIn("qol_press(core, QOL_KEY_B", self.source)
        self.assertNotRegex(
            self.source,
            re.compile(r"call_preserving\([^;]*\b(?:0x0808C0E5|0x080A1331)U?"),
        )

    def test_pc_uses_normal_ui_deposit_and_proves_fresh_reload(self) -> None:
        for token in (
            "box_was_empty",
            "deposit_source_exact",
            "party_before == 2U",
            "S58_DEPOSIT_BOX",
            "S58_DEPOSIT_SLOT",
            "S58_DEPOSIT_SPECIES",
            "final_bag_bound",
            "S58_SET_BAG_POCKETS_POINTERS",
            "s58_normal_menu_save(core, 0U, &final_save_hash)",
            '\\"pc_normal_ui_deposit\\"',
            '\\"pc_normal_ui_deposit_persisted\\"',
        ):
            self.assertIn(token, self.source)
        self.assertIn("!s58_ewram_pointer(read32(core, QOL_PSS_DATA))", self.source)
        self.assertIn("S58_CB2_OVERWORLD", self.source)
        self.assertIn("read8(core, S58_FIELD_LOCK) == 0U", self.source)

    def test_healer_four_boundaries_are_fail_closed(self) -> None:
        for token in (
            "s58_healer_empty_case",
            "QOL_MON_DATA_IS_EGG",
            "fainted ? 0U : 1U",
            "QOL_MON_DATA_HP",
            "QOL_MON_DATA_MAX_HP",
            "QOL_MON_DATA_STATUS",
            "QOL_MON_DATA_PP1",
            "bool *results[4] = {empty, egg, fainted, normal}",
            "boundary < 4U",
            "core = s58_open(rom, save, false)",
            "s58_continue_to_hub(core, cases)",
            "&& s58_codex_boundaries(core)",
            '\\"healer_zero_party_field_return\\"',
            '\\"healer_egg_hp_pp_status\\"',
            '\\"healer_fainted_hp_pp_status\\"',
            '\\"healer_normal_hp_pp_status\\"',
        ):
            self.assertIn(token, self.source)

    def test_mart_uses_jp_runtime_pockets_and_one_transaction(self) -> None:
        for token in (
            "S58_SET_BAG_POCKETS_POINTERS = 0x0809984DU",
            "S58_BAG_POCKETS = 0x020397D8U",
            "S58_MART_ITEMS_CAPACITY = 13U",
            "S58_ITEM_POCKET_OFFSET = 22U",
            "descriptor + 4U",
            "purchase_pulses",
            "failure_pulses == purchase_pulses",
            "100000U - target_price",
            '\\"mart_money_purchase\\"',
            '\\"mart_bag_full_no_charge\\"',
            '\\"mart_money_purchase_persisted\\"',
        ):
            self.assertIn(token, self.source)
        for stale_offset in (
            "S58_BAG_ITEMS_OFFSET",
            "S58_BAG_KEY_ITEMS_OFFSET",
            "S58_BAG_BALLS_OFFSET",
            "S58_BAG_TM_OFFSET",
            "S58_BAG_BERRIES_OFFSET",
        ):
            self.assertNotIn(stale_offset, self.source)

    def test_mart_sells_ball_and_item_through_normal_ui_and_reloads(self) -> None:
        for token in (
            "s58_mart_sell_one",
            "S58_BAG_MAIN_CALLBACK = 0x081089E5U",
            "read8(core, S58_BAG_MENU_STATE + 4U) != 2U",
            "money_after == money_before + price / 2U",
            "s58_item_quantity(core, item) == 0U",
            "candidate_pocket == 3U",
            "candidate_pocket == 1U",
            '\\"mart_normal_ui_sell_ball\\"',
            '\\"mart_normal_ui_sell_item\\"',
            '\\"mart_normal_ui_sales_persisted\\"',
        ):
            self.assertIn(token, self.source)

    def test_thin_six_pickups_repeat_and_full_retry_are_dynamic(self) -> None:
        for token in (
            "cases->thin_event_count != 6U",
            "s58_thin_blockdata_adjacent",
            "s58_thin_event_tile",
            "layout + 12U",
            "((block >> 10U) & 3U) != 0U",
            "s58_thin_warp_adjacent",
            "s58_face_and_interact(core, &object)",
            "s58_pocket_fill",
            "s58_pocket_restore",
            "s58_flag_get_direct",
            "quantity_before + event->quantity",
            "s58_flag_byte_direct",
            "flag_byte_before | flag_bit",
            "s58_codex_owner_hash(core) == owner_hash",
            '\\"thin_codex_owner_hash_unchanged\\"',
            '\\"hub_codex_boundaries_valid\\"',
            '\\"thin_events_initial_pickup\\"',
            '\\"thin_events_repeat_no_duplicate\\"',
            '\\"thin_events_blockdata_walkable_non_event_adjacent\\"',
            '\\"thin_events_bag_full_retry_all_6\\"',
            '\\"thin_events_native_flag_neighbor_bits_stable\\"',
            '\\"thin_events_quest_log_normal_save_recorded\\"',
            '\\"thin_events_quest_log_reload_next_input_flag_stable\\"',
            '\\"thin_events_quantities_preserved_across_normal_saves\\"',
            "s58_thin_quantities_exact",
            "actual != event->quantity",
            "read32(core, descriptor) != save1 + offsets[pocket]",
            "read-only boundary assertion",
            '\\"thin_events_pickups_persisted\\"',
            '\\"thin_events\\":%u',
            '\\"thin_retry\\":%u',
        ):
            self.assertIn(token, self.source)
        self.assertIn("!s58_flag_get_direct(core, event->flag)", self.source)
        self.assertIn("s58_thin_full_retry(\n            core, cases, event",
                      self.source)
        self.assertIn("s58_thin_post_questlog_path", self.source)
        self.assertIn("s58_quest_log_observed", self.source)
        self.assertIn("s58_normal_menu_save", self.source)
        self.assertIn("ordinary Pokemart transaction is a stock Quest Log owner",
                      self.source)
        self.assertIn(
            "natural ReadKeys requests are not relying on transient playback state",
            self.source,
        )
        self.assertIn("S58_STARTMENU_SAVE", self.source)
        self.assertIn("QOL_START_MENU_ORDER + target", self.source)
        self.assertIn("s58_sync_host_call_pc", self.source)
        self.assertIn("host ROM call前scheduler PC同期失敗", self.source)
        for debug_switch in (
            "MGBA_STAGE58_DIAG_SKIP_SHA",
            "MGBA_STAGE58_PC_ONLY",
            "MGBA_STAGE58_CODEX_ONLY",
            "MGBA_STAGE58_WATCH_BATTLE_HEAP",
        ):
            self.assertNotIn(debug_switch, self.source)

    def test_wild_fixture_compares_every_method_and_slot(self) -> None:
        self.assertIn("s58_wild_contract", self.source)
        self.assertIn("s58_wild_mode", self.source)
        self.assertIn("read8(core, actual_info)", self.source)
        self.assertIn("read16(core, row + 2U)", self.source)
        self.assertIn("representatives == 4U", self.source)
        self.assertIn("physical_mode_count == 4U", self.source)
        self.assertIn("{12U, 5U, 5U, 10U}", self.source)

    def test_wild_runtime_owners_generate_species_level_and_return_field(self) -> None:
        for token in (
            "S58_WILD_LAND_WATER_ROCK_OWNER = 0x080826D8U",
            "S58_WILD_FISHING_OWNER = 0x08082750U",
            "s58_wild_runtime_one",
            "s58_map_rom",
            "s58_find_land_pair",
            "s58_find_water_edge",
            "s58_find_rock_object",
            "s58_wild_natural_land",
            "s58_wild_natural_water",
            "s58_wild_natural_rock",
            "s58_wild_natural_fishing",
            "s58_walk_step",
            "s58_wild_battle_ready",
            "s58_wild_flee",
            "s58_wild_generated_matches_info",
            "ADDR_BATTLE_MONS + BATTLE_MON_SIZE",
            "S58_MOVE_SURF",
            "S58_MOVE_ROCK_SMASH",
            "S58_ITEM_OLD_ROD",
            "S58_ITEM_GOOD_ROD",
            "S58_ITEM_SUPER_ROD",
            "QOL_KEY_SELECT",
            "read8(core, info) != expected_rate",
            "result->generated == 4U",
            "result->evidence_count == 6U",
            '\\"kanto_wild_runtime_land_rate_species_level_field_return\\"',
            '\\"kanto_wild_runtime_water_rate_species_level_field_return\\"',
            '\\"kanto_wild_runtime_rock_rate_species_level_field_return\\"',
            '\\"kanto_wild_runtime_fishing_rate_species_level_field_return\\"',
        ):
            self.assertIn(token, self.source)
        self.assertNotRegex(
            self.source,
            re.compile(r"write(?:8|16|32)\([^;]*QOL_ENEMY_PARTY"),
        )

    def test_fishing_tiers_and_rng_boundaries_are_fail_closed(self) -> None:
        for token in (
            "s58_fishing_rng_boundary_audit",
            "static const unsigned starts[3] = {0U, 2U, 5U}",
            "static const unsigned ends[3] = {2U, 5U, 10U}",
            "counts[0][0] == 70U && counts[0][1] == 30U",
            "counts[1][2] == 60U && counts[1][3] == 20U",
            "counts[1][4] == 20U",
            "counts[2][5] == 40U && counts[2][6] == 40U",
            "counts[2][7] == 15U && counts[2][8] == 4U",
            "counts[2][9] == 1U",
            "result->fishing_rng_samples == 300U",
            '\\"kanto_wild_fishing_old_good_super_rng_boundaries\\"',
            '\\"fishing_tiers\\":%u',
            '\\"fishing_rng_samples\\":%u',
        ):
            self.assertIn(token, self.source)

    def test_production_runner_has_no_environment_bypass_or_raw_return(self) -> None:
        for forbidden in (
            "MGBA_STAGE58_DIAG_SKIP_SHA",
            "MGBA_STAGE58_PC_ONLY",
            "MGBA_STAGE58_CODEX_ONLY",
            "MGBA_STAGE58_WATCH_BATTLE_HEAP",
            "MGBA_STAGE58_RAW_RETURN",
            "MGBA_STAGE58_RAW_RETURN_B",
            "s58_prepare_hub_save_raw",
            "raw_return",
            "raw trace",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_codex_npc_battle_and_reward_are_normal_input_owned(self) -> None:
        for token in (
            "s58_face_and_interact(core, &cases->hub.npc)",
            "S58_CODEX_PHASE_PLAYER_SELECTION",
            "S58_CODEX_COMMAND_DISCONNECT_FORFEIT = 9U",
            "S58_CODEX_COMMAND_DISCONNECT_CPU = 8U",
            "S58_CODEX_PHASE_CPU = 11U",
            "S58_CODEX_COMMAND_REWARD_CLOSE = 14U",
            "S58_CODEX_EXTERNAL_CAPABILITIES = 0x7FFFU",
            "s58_reward_valid_window(core, S58_REWARD_WINDOW_OPEN)",
            "s58_reward_valid_window(core, S58_REWARD_WINDOW_CLOSED)",
            "BATTLE_CORE_BATTLE_OUTCOME",
            '\\"codex_npc_normal_a_battle_start_finish_field_return\\"',
            '\\"codex_reward_closed_open_closed\\"',
            '\\"codex_transaction_request_owned\\"',
            '\\"codex_natural_readkeys_all_11_requests\\"',
            '\\"codex_external_capabilities_7fff_preserved\\"',
            '\\"codex_request_window_not_cleared\\"',
            "result->result_kind = read8(core, S58_REWARD_OWNER + 22U)",
            "result->result_kind == 4U",
            "result->external_capabilities =",
            "result->request_command =",
            "codex_battle.external_capabilities",
            "codex_battle.request_command",
            '\\"codex_forfeit_result_kind_4\\"',
            '\\"codex_disconnect_cpu_controller_uninstalled\\"',
            '\\"codex_disconnect_cpu_win_result_kind_1\\"',
            '\\"codex_disconnect_cpu_normal_input_field_reward_return\\"',
            '\\"codex_cpu_win_thin_quantities_preserved\\"',
            '\\"codex_forfeit_thin_quantities_preserved\\"',
            '\\"codex_post_battle_closed_reset_boundary\\"',
            '\\"codex_external_mailbox_volatile_reset\\"',
        ):
            self.assertIn(token, self.source)
        self.assertNotRegex(
            self.source,
            re.compile(
                r"write(?:8|16|32)\(core,\s*(?:S58_MAILBOX|"
                r"S58_CODEX_STATE|S58_REWARD_OWNER|"
                r"BATTLE_CORE_BATTLE_OUTCOME)"
            ),
        )

    def test_codex_cpu_disconnect_runs_without_controller_to_field(self) -> None:
        for token in (
            "s58_codex_cpu_disconnect_path",
            "s58_codex_enter_action",
            "S58_CONTROLLER_CHOOSE_POKEMON = 22U",
            "s58_set_party_data(core, S58_MON_DATA_MOVE1, 33U, 2U)",
            "s58_set_party_data(core, QOL_MON_DATA_PP1, 35U, 1U)",
            "read8(core, S58_CODEX_STATE + 45U) == 1U",
            "read8(core, S58_CODEX_STATE + 47U) == 0U",
            "result->natural_cpu_requests == 11U",
            "== S58_CONTROLLER_CHOOSE_POKEMON",
            "? QOL_KEY_B : QOL_KEY_A",
            "qol_press(core, key, BATTLE_CORE_MENU_INPUT_WAIT)",
            "s58_reward_valid_window(core, S58_REWARD_WINDOW_OPEN)",
            "s58_reward_valid_window(core, S58_REWARD_WINDOW_CLOSED)",
            '\\"codex_battle_paths\\":%u',
            '\\"natural_cpu_requests\\":%u',
            '\\"cpu_controller_installed\\":%u',
        ):
            self.assertIn(token, self.source)
        self.assertNotRegex(
            self.source,
            re.compile(
                r"write8\(core,\s*BATTLE_CORE_(?:ACTION|MOVE)_SELECTION_CURSOR"
            ),
        )

    def test_codex_restores_vega_seen_mirrors_without_touching_owned(self) -> None:
        for token in (
            "S58_SAVE1_SEEN_PRIMARY_OFFSET = 0x05F8U",
            "S58_SAVE1_SEEN_SECONDARY_OFFSET = 0x3A18U",
            "S58_SAVE2_POKEDEX_PERSONALITY_OFFSET = 0x001CU",
            "S58_SAVE2_POKEDEX_OWNED_OFFSET = 0x0028U",
            "S58_SAVE2_POKEDEX_SEEN_OFFSET = 0x005CU",
            "S58_POKEDEX_BITMAP_SIZE = 52U",
            "S58_POKEDEX_PERSONALITY_SIZE = 8U",
            "s58_codex_save_sentinel_seed",
            "s58_codex_save_sentinel_matches",
            "codex_battle->cpu_save_layout_restored",
            "codex_battle->forfeit_save_layout_restored",
            '\\"codex_cpu_win_save_layout_restored\\"',
            '\\"codex_forfeit_save_layout_restored\\"',
            '\\"codex_save_layout\\"',
            '\\"seen_after_cpu\\"',
            '\\"personality_after_forfeit\\"',
            '\\"owned_after_forfeit\\"',
        ):
            self.assertIn(token, self.source)

    def test_codex_win_loss_draw_result_table_is_exact_rom_bound(self) -> None:
        for token in (
            'root, "codex_result_compat"',
            'codex_result, "end_turn_function_table"',
            'static const char *const kinds[3] = {"win", "loss", "draw"}',
            "route->site != exact_site",
            "read32(core, route->site) != route->replacement",
            '\\"codex_result_win_loss_draw_table_exact\\"',
            '\\"codex_result_routes_exact\\":%u',
        ):
            self.assertIn(token, self.source)

    def test_codex_external_requests_are_consumed_by_natural_readkeys(self) -> None:
        for token in (
            "s58_codex_write_request",
            "s58_codex_send_field",
            "The external side publishes the request only",
            "run_key_frames(core, 0U, 1U)",
            "s58_codex_request_accepted",
            "result->cpu_outcome == 1U",
            "result->cpu_result_kind == 1U",
            "result->cpu_win_result_kind",
            '\\"cpu_battle\\"',
            "result->natural_requests == 11U",
            "read32(core, S58_CODEX_REQUEST + 88U) == ~sequence",
            "read32(core, S58_CODEX_REQUEST + 92U) == sequence",
        ):
            self.assertIn(token, self.source)
        self.assertNotRegex(
            self.source,
            re.compile(
                r"s58_call_scheduler_safe\(core,\s*S58_CODEX_POLL"
            ),
        )

    def test_phase_specific_json_requires_only_executed_evidence(self) -> None:
        phase1_keys = (
            '\\"thin_events_quantities_preserved_across_normal_saves\\"',
            '\\"mart_normal_ui_sell_ball\\"',
            '\\"mart_normal_ui_sell_item\\"',
            '\\"codex_npc_normal_a_battle_start_finish_field_return\\"',
            '\\"codex_reward_closed_open_closed\\"',
            '\\"codex_transaction_request_owned\\"',
            '\\"codex_natural_readkeys_all_11_requests\\"',
            '\\"codex_external_capabilities_7fff_preserved\\"',
            '\\"codex_request_window_not_cleared\\"',
            '\\"codex_disconnect_cpu_controller_uninstalled\\"',
            '\\"codex_disconnect_cpu_win_result_kind_1\\"',
            '\\"codex_disconnect_cpu_normal_input_field_reward_return\\"',
            '\\"codex_cpu_win_thin_quantities_preserved\\"',
            '\\"codex_forfeit_thin_quantities_preserved\\"',
            '\\"codex_cpu_win_save_layout_restored\\"',
            '\\"codex_forfeit_save_layout_restored\\"',
        )
        reload_keys = (
            '\\"pc_normal_ui_deposit_persisted\\"',
            '\\"mart_money_purchase_persisted\\"',
            '\\"mart_normal_ui_sales_persisted\\"',
            '\\"codex_post_battle_closed_reset_boundary\\"',
            '\\"codex_external_mailbox_volatile_reset\\"',
            '\\"thin_events_pickups_persisted\\"',
            '\\"thin_reload\\"',
            '\\"raw_quantity\\"',
            '\\"decoded_quantity\\"',
        )
        for token in (*phase1_keys, *reload_keys):
            self.assertIn(token, self.source)

    def test_convenience_does_not_claim_effect_item_runner_coverage(self) -> None:
        self.assertIn('s58_member_u32(qol, "effect_item_count")', self.source)
        self.assertNotIn("required_full_cases", self.source)
        self.assertNotIn("qol_delegated_full_cases", self.source)
        self.assertNotIn("delegated_qol_cases", self.source)

    def test_script_liveness_is_read_directly_not_host_called(self) -> None:
        self.assertIn("S58_FIELD_LOCK = 0x03000F9CU", self.source)
        self.assertNotRegex(
            self.source,
            re.compile(r"(?:call_preserving|s58_call_synced)\([^;]*SCRIPT_CONTEXT"),
        )


if __name__ == "__main__":
    unittest.main()
