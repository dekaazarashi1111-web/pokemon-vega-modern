from __future__ import annotations

import csv
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "tools" / "mgba_stage58_qol_item_effects_smoke.c"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
CORE_SOURCE = (ROOT / "tools" / "mgba_battle_core_smoke.c").read_text(
    encoding="utf-8"
)
CODEX_RUNTIME_SOURCE = (
    ROOT / "overlays" / "codex_battle_runtime" / "codex_battle_runtime.c"
).read_text(encoding="utf-8")


class Stage58QolItemEffectsSourceTest(unittest.TestCase):
    def test_host_direct_calls_use_restored_ewram_scratch_stack(self) -> None:
        self.assertIn("#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1", SOURCE)
        self.assertIn(
            "#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U", SOURCE
        )
        self.assertIn(
            "#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U", SOURCE
        )
        self.assertIn(
            "BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS", CORE_SOURCE
        )
        self.assertIn("BATTLE_CORE_HOST_STACK_TOP_ADDRESS", CORE_SOURCE)
        self.assertIn(
            '#error "isolated host calls require explicit scratch-stack bounds"',
            CORE_SOURCE,
        )
        self.assertIn("struct HostCallStack", CORE_SOURCE)
        self.assertIn("begin_host_call_stack", CORE_SOURCE)
        self.assertIn("restore_host_call_stack", CORE_SOURCE)
        self.assertIn("stack->original[byte]", CORE_SOURCE)
        self.assertIn("write_register(core, \"sp\", stack->entry_sp)", CORE_SOURCE)
        self.assertIn("direct call overflowed its scratch stack", CORE_SOURCE)
        self.assertIn("CreateMon overflowed its scratch stack", CORE_SOURCE)

        bottom, top = 0x0203DB00, 0x0203DF80
        with (ROOT / "config" / "ram_layout.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            live_ewram = [
                (int(row["start"], 0), int(row["end_exclusive"], 0))
                for row in csv.DictReader(handle)
                if row["address_space"] == "EWRAM" and row["status"] == "LIVE"
            ]
        self.assertTrue(
            all(top <= start or bottom >= end for start, end in live_ewram)
        )
        self.assertIn(
            "G_TERRAIN_TYPE_ADDRESS = 0x0203DFA0u", CODEX_RUNTIME_SOURCE
        )
        self.assertLessEqual(top, 0x0203DFA0)

    def test_exact_task_and_two_process_cli_contract_are_emitted(self) -> None:
        self.assertIn(
            "USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG", SOURCE
        )
        self.assertIn('strcmp(argv[4], "phase1")', SOURCE)
        self.assertIn('strcmp(argv[4], "reload")', SOURCE)
        self.assertIn('"process_contract\\\":2', SOURCE)
        self.assertIn("strcmp(rom_sha256, argv[3])", SOURCE)

    def test_all_36_rows_and_all_three_outcomes_are_exhaustive(self) -> None:
        table = re.search(
            r"s58e_cases\[S58E_EFFECT_COUNT\]\s*=\s*\{(?P<body>.*?)\n\};",
            SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(table)
        rows = re.findall(r"\{(\d+)U,\s*S58E_[A-Z_]+,\s*\d+U\}", table.group("body"))
        self.assertEqual(len(rows), 36)
        self.assertEqual(len(set(rows)), 36)
        self.assertIn(
            "for (unsigned index = 0U; index < S58E_EFFECT_COUNT; ++index)",
            SOURCE,
        )
        self.assertIn("*cancelled == S58E_EFFECT_COUNT", SOURCE)
        self.assertIn("*successful == S58E_EFFECT_COUNT", SOURCE)
        self.assertIn("*effectless == S58E_EFFECT_COUNT", SOURCE)

    def test_normal_bag_gate_covers_five_distinct_families(self) -> None:
        self.assertIn("S58E_NORMAL_FAMILY_COUNT = 5U", SOURCE)
        self.assertRegex(
            SOURCE,
            r"case_indices\[S58E_NORMAL_FAMILY_COUNT\]\s*=\s*\{\s*"
            r"0U,\s*5U,\s*11U,\s*13U,\s*15U,\s*\}",
        )
        for gate in (
            "normal_bag_ui_family_paths",
            "normal_bag_ui_candy",
            "normal_bag_ui_ev_reset",
            "normal_bag_ui_bottle_cap",
            "normal_bag_ui_bottle_silver_cancel",
            "normal_bag_ui_bottle_silver_hp",
            "normal_bag_ui_bottle_gold_all",
            "normal_bag_ui_bottle_effectless_no_consume",
            "normal_bag_ui_bottle_egg_no_consume",
            "normal_bag_ui_bottle_locked_no_consume",
            "normal_bag_ui_bottle_same_core_reopen",
            "normal_bag_ui_bottle_vram_nonalias",
            "normal_bag_ui_bottle_framebuffer_stable",
            "normal_bag_ui_ability",
            "normal_bag_ui_mint",
        ):
            self.assertIn(gate, SOURCE)
        self.assertIn('"normal_bag_ui_families\\\":5', SOURCE)
        self.assertIn('"normal_bag_ui_bottle_boundaries\\\":9', SOURCE)
        self.assertIn("s58e_normal_bottle_reopen", SOURCE)
        self.assertIn("s58e_bottle_menu_vram_contract", SOURCE)
        self.assertIn("s58e_bottle_framebuffer_hash", SOURCE)
        self.assertIn("core->setVideoBuffer(core, s58e_video, 240U)", SOURCE)
        self.assertIn("unchanged * 100U >= 104U * 128U * 90U", SOURCE)
        self.assertIn("struct CpuState scheduler = capture_cpu_state(core)", SOURCE)
        self.assertIn("restore_cpu_state(core, &scheduler)", SOURCE)
        self.assertIn("S58E_BOTTLE_CONTENT_BASE = 0x02BFU", SOURCE)
        self.assertIn("S58E_STD_FRAME_BASE = 0x0214U", SOURCE)

    def test_normal_bag_path_uses_physical_keys_and_steady_callback(self) -> None:
        self.assertIn("S58E_BAG_MAIN_CALLBACK = 0x081089E5U", SOURCE)
        enter = SOURCE[SOURCE.index("static bool s58e_enter_bag_physical") :]
        enter = enter[: enter.index("static bool s58e_keep_only_bag_item")]
        self.assertIn("QOL_KEY_START", enter)
        self.assertIn("QOL_KEY_DOWN", enter)
        self.assertIn("QOL_KEY_A", enter)
        self.assertIn("S58E_BAG_MAIN_CALLBACK", enter)
        scenario = SOURCE[SOURCE.index("static bool s58e_normal_scenario") :]
        scenario = scenario[: scenario.index("static bool s58e_normal_family")]
        self.assertIn("QOL_KEY_B", scenario)
        self.assertIn("s58e_return_to_field", scenario)
        self.assertIn("s58e_normal_effect", scenario)
        family = SOURCE[SOURCE.index("static bool s58e_normal_family") :]
        family = family[: family.index("static unsigned s58e_normal_families")]
        self.assertIn("row, true", family)
        self.assertIn("row, false", family)

    def test_reload_rebinds_bag_and_checks_raw_encrypted_saveblock(self) -> None:
        reload_body = SOURCE[SOURCE.index("static bool s58e_reload(") :]
        reload_body = reload_body[: reload_body.index("int main(")]
        load_pos = reload_body.index("QOL_LOAD_GAME_DATA")
        save_blocks_pos = reload_body.index("S58E_SET_SAVE_BLOCK_POINTERS")
        rebind_pos = reload_body.index("S58E_SET_BAG_POCKETS_POINTERS")
        raw_pos = reload_body.index("s58e_saved_items_exact")
        api_pos = reload_body.index("s58e_bag_exact")
        self.assertLess(save_blocks_pos, load_pos)
        self.assertLess(load_pos, rebind_pos)
        self.assertLess(rebind_pos, raw_pos)
        self.assertLess(raw_pos, api_pos)
        self.assertIn("S58E_SAVE_ITEMS_OFFSET = 0x0310U", SOURCE)
        self.assertIn("S58E_SAVE_ITEMS_SLOTS = 42U", SOURCE)
        self.assertIn("S58E_SAVE_ENCRYPTION_KEY_OFFSET = 0x0F20U", SOURCE)
        self.assertIn("run_key_frames(core, 0U, 2U)", reload_body)

    def test_normal_bottle_success_is_saved_and_fresh_reloaded(self) -> None:
        reopen = SOURCE[SOURCE.index("static bool s58e_normal_bottle_reopen") :]
        reopen = reopen[: reopen.index("static bool s58e_normal_bottle_no_effect")]
        scenario = SOURCE[SOURCE.index("static bool s58e_normal_scenario") :]
        scenario = scenario[: scenario.index("static bool s58e_normal_family")]
        reload_body = SOURCE[SOURCE.index("static bool s58e_reload_normal_bottle") :]
        reload_body = reload_body[: reload_body.index("int main(")]
        self.assertGreaterEqual(reopen.count("QOL_TRY_SAVING_DATA"), 2)
        self.assertGreaterEqual(scenario.count("QOL_TRY_SAVING_DATA"), 2)
        self.assertIn("rom_path, save_base, 4U, &s58e_cases[11U]", reload_body)
        self.assertIn("rom_path, save_base, 10U, &s58e_cases[12U]", reload_body)
        self.assertIn("S58E_HYPER_TRAIN_OFFSET", reload_body)
        self.assertIn("s58e_saved_items_exact", reload_body)
        self.assertIn("s58e_bag_exact", reload_body)
        self.assertIn("fresh_core_normal_bag_ui_bottle_silver_hp", SOURCE)
        self.assertIn("fresh_core_normal_bag_ui_bottle_gold_all", SOURCE)
        self.assertIn('"normal_bag_ui_bottle_saved_cases\\\":2', SOURCE)
        self.assertIn("normal_bag_ui_bottle_records", SOURCE)
        self.assertIn("normal_bag_ui_bottle_bags", SOURCE)

    def test_phase_outputs_are_specific_and_fail_closed(self) -> None:
        main = SOURCE[SOURCE.index("int main(") :]
        phase1_branch = main[main.index("if (phase1)") : main.index("} else {")]
        reload_branch = main[main.index("} else {") :]
        self.assertIn("cancel_no_consume_36", phase1_branch)
        self.assertIn("normal_bag_ui_family_paths", phase1_branch)
        self.assertNotIn("fresh_core_effect_records_36", phase1_branch)
        self.assertIn("fresh_core_effect_records_36", reload_branch)
        self.assertIn("fresh_core_bag_counts_36", reload_branch)
        self.assertNotIn("normal_bag_ui_family_paths", reload_branch)
        self.assertIn("log_problem_count == 0U", main)
        self.assertIn('"warnings_errors\\\":%u', main)

    def test_measured_results_are_reported_as_rom_owned(self) -> None:
        self.assertIn('"host_result_writes\\\":0', SOURCE)
        self.assertIn("s58e_store_result", SOURCE)
        self.assertIn("QOL_SET_BOX_MON", SOURCE)
        self.assertIn("QOL_TRY_SAVING_DATA", SOURCE)
        self.assertNotIn("write_result", SOURCE)

    def test_no_temporary_debug_or_partial_loop_remains(self) -> None:
        for forbidden in (
            "s58e_debug_normal",
            "normal attempt=",
            "normal item task=",
            "phase1 index=",
            "index = 12U",
            "ewram_snapshot",
            "normal bag start",
            "normal party entry",
            "mint after target",
            "mint normal failure",
            "TEMP party",
            "TRACE compat",
            "S58E_TRACE_READKEYS",
        ):
            self.assertNotIn(forbidden, SOURCE)
        phase1 = SOURCE[SOURCE.index("static bool s58e_phase1") :]
        phase1 = phase1[: phase1.index("static bool s58e_reload_record")]
        normal_end = phase1.index("normal, bottle);") + len("normal, bottle);")
        loop_start = phase1.index(
            "for (unsigned index = 0U; index < S58E_EFFECT_COUNT; ++index)"
        )
        self.assertNotIn("return false;", phase1[normal_end:loop_start])


if __name__ == "__main__":
    unittest.main()
