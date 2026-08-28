from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/mgba_stage58_economy_smoke.c"
RAM_LAYOUT = ROOT / "config/ram_layout.csv"


class Stage58EconomySmokeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_exact_identity_warning_and_task_contract(self) -> None:
        for token in (
            "sha256_file(argv[1], digest)",
            "warnings_errors",
            "passed && warnings",
            "USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG",
            "fresh-core-two-phase",
            "#include <mgba/flags.h>",
        ):
            self.assertIn(token, self.source)

    def test_host_stack_is_exact_and_disjoint_from_all_live_ewram(self) -> None:
        self.assertIn(
            "BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U", self.source
        )
        self.assertIn(
            "BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U", self.source
        )
        self.assertIn("S58E_SCHEDULER_SCRATCH_END <= 0x0203DFA0U", self.source)
        scratch_start, scratch_end = 0x0203DB00, 0x0203DFA0
        with RAM_LAYOUT.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                if row["address_space"] != "EWRAM" or row["status"] != "LIVE":
                    continue
                start = int(row["start"], 0)
                end = int(row["end_exclusive"], 0)
                self.assertTrue(
                    end <= scratch_start or start >= scratch_end,
                    f"runner scratch intersects LIVE owner {row['owner']}",
                )

    def test_ewram_is_script_data_only_and_armv4t_unsafe_veneer_is_absent(self) -> None:
        for forbidden in (
            "0x4798U",
            "0xF000U",
            "0xF803U",
            "blx r3",
            "MGBA_STAGE58_RAW_RETURN",
        ):
            self.assertNotIn(forbidden, self.source)
        for token in (
            "Data-only field bytecode",
            "S58E_SCHEDULER_STUB + 0U, 0x23U",
            "S58E_SCHEDULER_STUB + 5U, 0x02U",
            "frame < 3600U && stable < 30U",
            "s58e_repair_wait_pc(core)",
        ):
            self.assertIn(token, self.source)

    def test_actual_trainer_prize_honey_and_normal_save_are_exact(self) -> None:
        for token in (
            "S58E_NORMAL_TRAINER_ID = 89U",
            "S58E_NORMAL_TRAINER_SOURCE = 0x09376713U",
            "S58E_TRAINER_MONEY_BEFORE = 3000U",
            "S58E_TRAINER_PRIZE_EXPECTED = 128U",
            "S58E_TRAINER_MONEY_AFTER = 3128U",
            "S58E_TRAINER_MONEY_AFTER_HONEY = 2228U",
            "battle.outcome_seen == BATTLE_CORE_OUTCOME_WON",
            "battle.enemy_fainted_seen",
            "battle.battle_runtime_cleaned",
            "s58e_actual_honey_purchase(core)",
            "s58e_normal_menu_save(core, &save_hash)",
            "normal_trainer_victory_prize_honey_normal_save_phase1",
        ):
            self.assertIn(token, self.source)
        trainer = self.source.split("static bool s58e_actual_trainer_chain", 1)[1]
        trainer = trainer.split("static void s58e_disable_script_contexts", 1)[0]
        self.assertNotIn("S58E_ADD_MONEY", trainer)

    def test_factory_prepare_three_real_battles_and_bp_reward_are_dynamic(self) -> None:
        for token in (
            "S58E_FACILITY_BP_BEFORE =",
            "S58E_FACILITY_REWARD_BP = 9U",
            "BATTLE_CORE_START_TRAINER",
            "launch.instructions == 0U || !launch.payload_pc_seen",
            "evidence->factory_payload_starts",
            "evidence->factory_outcomes[0] == BATTLE_CORE_OUTCOME_WON",
            "evidence->factory_outcomes[1] == BATTLE_CORE_OUTCOME_WON",
            "evidence->factory_outcomes[2] == BATTLE_CORE_OUTCOME_WON",
            "evidence->factory_bp_delta == S58E_FACILITY_REWARD_BP",
            "factory_prepare_real_battles_bp_patch_normal_save_phase1",
        ):
            self.assertIn(token, self.source)
        factory_battle = self.source.split(
            "static bool s58e_factory_battle_once", 1
        )[1].split("static bool s58e_actual_factory_chain", 1)[0]
        self.assertNotRegex(factory_battle, r"write(?:8|16|32)\([^;]*BATTLE_OUTCOME")
        self.assertNotRegex(factory_battle, r"write(?:8|16|32)\([^;]*FACTORY_BP")

    def test_facility_void_specialvar_owner_abi_is_split_by_safe_route(self) -> None:
        for target in ("ENTER", "COMMIT", "PREPARE"):
            self.assertRegex(
                self.source,
                rf"s58e_scheduler_expect_r0\([^;]*S58E_FACILITY_{target}",
            )
        for target in ("AFTER", "SKIP_EXCHANGE", "COMPLETE"):
            self.assertRegex(
                self.source,
                rf"s58e_facility_direct_expect\([^;]*S58E_FACILITY_{target}",
            )
        self.assertIn("actual == 0x08000001U", self.source)
        self.assertIn("VOID_SPECIALVAR_OWNER_ABI", self.source)

    def test_factory_fixture_scope_is_explicit_and_not_overclaimed(self) -> None:
        for token in (
            "S58E_FACILITY_SELECTED_ORDER",
            "S58E_BATTLE_MON_MOVES_OFFSET",
            "S58E_FACTORY_FIXTURE_MOVE = 165U",
            "S58E_BATTLE_MON_PP_OFFSET",
            "factory_physical_npc_and_selection_ui\\\":false",
            "factory_unmodified_battle_fixture\\\":false",
            "HOST_SELECTED_ORDER_HP_MAXHP_SPEED_MOVE_PP_ACTION_AND_MOVE_",
            "CURSORS_NO_OUTCOME_OR_REWARD_WRITE",
        ):
            self.assertIn(token, self.source)

    def test_five_transaction_boundaries_have_independent_evidence(self) -> None:
        fields = (
            "normal_menu_cancel_no_mutation",
            "bag_full_no_debit",
            "insufficient_no_mutation",
            "cross_store_fault_rollback",
            "limited_repeatable_reopen",
        )
        for field in fields:
            self.assertIn(f"evidence->{field}", self.source)
            self.assertIn(f'\\"{field}\\":%s', self.source)
        self.assertIn("QOL_STATUS_CAPACITY", self.source)
        self.assertIn("QOL_STATUS_INSUFFICIENT_CURRENCY", self.source)
        self.assertIn("QOL_STATUS_PERSIST_FAILED", self.source)
        self.assertIn("same_session_limited", self.source)
        self.assertIn("s58e_cancel_menu(core, symbols)", self.source)
        self.assertNotRegex(
            self.source,
            r'normal_menu_cancel_no_mutation\\":%s[^;]{0,800}passed \?',
        )

    def test_insufficient_and_fault_rollback_cover_full_owner_and_flash(self) -> None:
        for token in (
            "insufficient_ledger",
            "== insufficient_ledger",
            "symbols->inject_persist_fault",
            "for (uint32_t mode = 1U; mode <= 2U; ++mode)",
            "call_preserving(core, QOL_LOAD_GAME_DATA",
            "s58e_bind_bag_pockets(core)",
            "flash_ok",
        ):
            self.assertIn(token, self.source)

    def test_ability_patch_purchase_uses_real_owner_result_and_not_bp_add(self) -> None:
        for token in (
            "S58E_ABILITY_PATCH_INDEX = 35U",
            "S58E_ABILITY_PATCH_ITEM = 943U",
            "S58E_ABILITY_PATCH_PRICE = 64U",
            "S58E_BP_SHOP_PURCHASE_BY_INDEX = 0x09377181U",
            "purchase_result == 0U",
            "S58E_SPECIAL_VAR_RESULT) == 0U",
            "factory_bp_after_purchase == 0U",
            "PRODUCTION_BPSHOP_PURCHASE_BY_INDEX_RAW_AND_SPECIAL_RESULT",
        ):
            self.assertIn(token, self.source)
        factory = self.source.split("static bool s58e_actual_factory_chain", 1)[1]
        factory = factory.split("static bool s58e_reward_unlock_allowed", 1)[0]
        self.assertNotIn("S58E_FACTORY_ADD_BP", factory)

    def test_static_economy_audits_remain_complete(self) -> None:
        initializer = self.source.split(
            "static const struct S58eResearchReprice "
            "S58E_RESEARCH_REPRICES[] = {",
            1,
        )[1].split("};", 1)[0]
        self.assertEqual(
            len(re.findall(r"\{\d+U, \d+U, \d+U\}", initializer)), 71
        )
        for token in (
            "sample < 65536U",
            "pre_total == 460U && post_total == 550U",
            "*pre_hits == 0U && *post_hits != 0U",
            "*count_out == 47U",
            "*count_out == 71U",
            "S58E_HONEY_SELL_PRICE < S58E_HONEY_BUY_PRICE",
        ):
            self.assertIn(token, self.source)

    def test_phase_specific_keys_and_claims_are_truthful(self) -> None:
        for key in (
            "normal_trainer_victory_prize_honey_normal_save_phase1",
            "factory_prepare_real_battles_bp_patch_normal_save_phase1",
            "fresh_process_trainer_prize_honey_reload",
            "fresh_process_factory_reward_ability_patch_reload",
            "fresh_process_earned_purchases_reload",
        ):
            self.assertIn(key, self.source)
        self.assertIn(
            "ACTUAL_TRAINER_AND_FACTORY_EARN_PURCHASE_NORMAL_SAVE", self.source
        )
        self.assertIn(
            "AUTHORED_TRAINER89_SCRIPT_COPY_AND_ENEMY_HP1_NO_OUTCOME_",
            self.source,
        )
        self.assertIn("phase1_transaction_boundaries_contract", self.source)
        self.assertIn("transaction_boundaries_observed_this_phase", self.source)
        self.assertIn("FRESH_PROCESS_RELOAD", self.source)
        self.assertIn("INCOMPLETE_RUNTIME_GATE", self.source)
        self.assertNotIn("OWNER_API_INTEGRATION_ONLY_EARN_E2E_UNPROVEN", self.source)

    def test_fresh_process_reload_checks_exact_earned_purchases(self) -> None:
        for token in (
            "evidence->reload_money == S58E_TRAINER_MONEY_AFTER_HONEY",
            "evidence->reload_honey == 1U",
            "evidence->reload_bp == 0U",
            "evidence->reload_patch == 1U",
            "s58e_saved_item_count(core, S58E_HONEY_ITEM) == 1U",
            "s58e_saved_item_count(core, S58E_ABILITY_PATCH_ITEM) == 1U",
            "observed_in_fresh_process",
        ):
            self.assertIn(token, self.source)

    def test_synthetic_currency_owner_is_separate_from_actual_earn(self) -> None:
        self.assertIn("currency_owner_api_integration_boundary", self.source)
        self.assertIn("synthetic_currency_owner_api_is_actual_earn\\\":false", self.source)
        self.assertIn("s58e_currency_owner_api_add(core)", self.source)
        self.assertNotIn("DIRECT_STOCK_ADDMONEY_AND_FACTORY_ADD_BP_OWNER_APIS_TO_", self.source)


if __name__ == "__main__":
    unittest.main()
