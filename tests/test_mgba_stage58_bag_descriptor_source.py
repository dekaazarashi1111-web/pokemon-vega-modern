from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
C_PATH = ROOT / "tools/mgba_stage58_bag_descriptor_smoke.c"
PY_PATH = ROOT / "scripts/run_stage58_bag_descriptor_validation.py"
C_SOURCE = C_PATH.read_text(encoding="utf-8")
PY_SOURCE = PY_PATH.read_text(encoding="utf-8")


class Stage58BagDescriptorSourceTest(unittest.TestCase):
    def test_host_calls_use_a_declared_nonlive_scratch_interval(self) -> None:
        self.assertIn("#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1", C_SOURCE)
        self.assertIn(
            "#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U",
            C_SOURCE,
        )
        self.assertIn(
            "#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U",
            C_SOURCE,
        )
        bottom, top = 0x0203DB00, 0x0203DF80
        with (ROOT / "config/ram_layout.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            live = [
                (int(row["start"], 0), int(row["end_exclusive"], 0))
                for row in csv.DictReader(handle)
                if row["address_space"] == "EWRAM" and row["status"] == "LIVE"
            ]
        self.assertTrue(all(top <= start or bottom >= end for start, end in live))
        self.assertLessEqual(top, 0x0203DFA0)

    def test_all_five_pointer_and_capacity_fields_are_observed(self) -> None:
        self.assertIn("BD_POCKET_COUNT = 5U", C_SOURCE)
        self.assertIn("BD_DESCRIPTOR_STRIDE = 8U", C_SOURCE)
        self.assertIn("contract->descriptor[pocket].offset", C_SOURCE)
        self.assertIn("contract->descriptor[pocket].capacity", C_SOURCE)
        for token in (
            "pointer_before", "pointer_after",
            "capacity_before", "capacity_after",
            "all_five_descriptors_exact_across_lifecycle",
        ):
            self.assertIn(token, C_SOURCE)

    def test_five_pockets_have_independent_encrypted_sentinels(self) -> None:
        self.assertRegex(
            C_SOURCE,
            r"BD_SENTINEL_ITEMS\[BD_POCKET_COUNT\]\s*=\s*\{\s*"
            r"19U,\s*48U,\s*2U,\s*289U,\s*133U,",
        )
        self.assertRegex(
            C_SOURCE,
            r"BD_SENTINEL_QUANTITIES\[BD_POCKET_COUNT\]\s*=\s*\{\s*"
            r"11U,\s*1U,\s*13U,\s*2U,\s*15U,",
        )
        self.assertIn("raw ^ (uint16_t)bd_key(core, contract)", C_SOURCE)
        self.assertIn("normal_key_before", C_SOURCE)
        self.assertIn("normal_key_after", C_SOURCE)
        self.assertIn("fresh_process_five_sentinels_exact", C_SOURCE)

    def test_runner_never_performs_a_host_rebind_or_descriptor_write(self) -> None:
        self.assertIn("set_bag_pockets", C_SOURCE)
        self.assertIn("stock_rom_call_graph_exact", C_SOURCE)
        self.assertNotRegex(
            C_SOURCE,
            r"call_(?:preserving|bounded)\s*\([^;]*set_bag_pockets",
        )
        self.assertNotRegex(
            C_SOURCE,
            r"write(?:8|16|32)\s*\([^;]*contract->bag_pockets",
        )
        self.assertNotIn("FN_SET_BAG_POCKETS_POINTERS", C_SOURCE)
        self.assertNotIn("LOAD_GAME_DATA", C_SOURCE)
        self.assertNotRegex(
            C_SOURCE,
            r"call_(?:preserving|bounded)\s*\([^;]*(?:load|continue)",
        )
        self.assertIn("No SetBagPocketsPointers call is allowed here", C_SOURCE)
        self.assertIn('"host_rebind_performed": False', PY_SOURCE)
        for obsolete in (
            "mis" + "match", "replacement" + "_function", "wrap" + "per",
        ):
            self.assertNotIn(obsolete, C_SOURCE.lower())
            self.assertNotIn(obsolete, PY_SOURCE.lower())

    def test_product_owner_and_addresses_come_from_metadata_cli(self) -> None:
        for field in (
            "saveblock_key_rotation_stock_contract",
            "move_save_blocks_reset_heap",
            "callback_restore_site",
            "apply_all_call_site",
            "original_apply_new_encryption",
            "bag_encryption_call_site",
            "original_bag_encryption",
            "set_bag_pockets_pointers",
        ):
            self.assertIn(field, PY_SOURCE)
        self.assertIn('contract.move_save_blocks = qol_number(argv[arg++]', C_SOURCE)
        self.assertIn('contract.callback_restore_site =', C_SOURCE)
        self.assertIn('contract.bag_encryption_call_site =', C_SOURCE)
        self.assertIn('strcmp(digest, argv[3])', C_SOURCE)
        self.assertNotRegex(C_SOURCE, r"[0-9a-f]{64}")
        self.assertIn('metadata.get("output", {}).get("sha256") != digest', PY_SOURCE)
        self.assertNotIn('metadata.get("status") != "PASS"', PY_SOURCE)

    def test_stock_call_graph_and_natural_save_are_both_required(self) -> None:
        graph = C_SOURCE[C_SOURCE.index("static bool bd_stock_rom_contract") :]
        graph = graph[: graph.index("static bool bd_wait_bag")]
        for token in (
            "bd_thumb_bl_target(core, contract->apply_all_call_site)",
            "bd_thumb(contract->apply_all)",
            "bd_thumb_bl_target(core, contract->bag_encryption_call_site)",
            "bd_thumb(contract->bag_encryption)",
            "contract->move_save_blocks", "contract->callback_restore_site",
        ):
            self.assertIn(token, graph)
        save = C_SOURCE[C_SOURCE.index("static bool bd_normal_save") :]
        save = save[: save.index("static bool bd_continue")]
        self.assertIn("lifecycle->key_before", save)
        self.assertIn("lifecycle->key_after", save)
        self.assertIn("lifecycle->savedata_changed", save)

    def test_normal_bag_reentry_and_normal_save_are_physical(self) -> None:
        self.assertIn("static bool bd_open_bag", C_SOURCE)
        self.assertIn("QOL_KEY_START", C_SOURCE)
        self.assertIn("QOL_KEY_DOWN", C_SOURCE)
        self.assertIn("QOL_KEY_A", C_SOURCE)
        self.assertIn("QOL_KEY_B", C_SOURCE)
        self.assertIn("for (unsigned pass = 0U; pass < 2U; ++pass)", C_SOURCE)
        save = C_SOURCE[C_SOURCE.index("static bool bd_normal_save") :]
        save = save[: save.index("static bool bd_continue")]
        self.assertIn("BD_STARTMENU_SAVE", save)
        self.assertIn("bd_savedata_hash", save)
        self.assertNotIn("set_bag_pockets", save)

    def test_python_runs_phase1_then_reload_as_distinct_processes(self) -> None:
        self.assertIn('"process_runs": 2', PY_SOURCE)
        self.assertIn('"phase1", contract', PY_SOURCE)
        self.assertIn('"reload", contract', PY_SOURCE)
        self.assertGreaterEqual(PY_SOURCE.count("_run("), 3)
        self.assertIn('"fresh_process_reload": True', PY_SOURCE)
        self.assertIn('reload_evidence.get("fresh_entry_save1")', PY_SOURCE)
        self.assertIn('reload_evidence.get("fresh_entry_key")', PY_SOURCE)
        self.assertIn("completed.stderr", PY_SOURCE)
        self.assertIn('document.get("warnings_errors") != 0', PY_SOURCE)

    def test_phase_test_keys_are_exact_and_fail_closed(self) -> None:
        for key in (
            "natural_field_descriptor_owner",
            "five_pocket_sentinels_seeded",
            "stock_normal_save_persistence_observed",
            "all_five_descriptors_exact_across_lifecycle",
            "all_five_encrypted_quantities_preserved",
            "post_save_irq_no_reset",
            "same_core_bag_reentry",
            "same_core_stock_saveblock_relocation_observed",
            "normal_start_menu_save_persisted",
            "fresh_process_continue",
            "fresh_process_stock_saveblock_relocation_observed",
            "fresh_process_five_descriptors_exact",
            "fresh_process_five_sentinels_exact",
            "fresh_process_same_core_bag_reentry",
            "fresh_process_irq_no_reset",
        ):
            self.assertIn(key, C_SOURCE)
            self.assertIn(key, PY_SOURCE)
        self.assertIn("set(tests) != expected_keys", PY_SOURCE)
        self.assertIn("not all(value is True", PY_SOURCE)

    def test_structured_evidence_is_fail_closed(self) -> None:
        for token in (
            'row.get("actual_pointer") == row.get("expected_pointer")',
            'row.get("actual_capacity") == row.get("expected_capacity")',
            'SENTINEL_ITEMS = [19, 48, 2, 289, 133]',
            'SENTINEL_QUANTITIES = [11, 1, 13, 2, 15]',
            '[row.get("raw") ^ (current_key & 0xFFFF) for row in sentinels]',
            'row.get("key_before") == key_before',
            'row.get("key_after") == key_after',
            '_pointer_layout_exact(row.get("pointer_before"))',
            '_pointer_layout_exact(row.get("pointer_after"))',
            'row.get("capacity_before") == POCKET_CAPACITIES',
            'row.get("capacity_after") == POCKET_CAPACITIES',
        ):
            self.assertIn(token, PY_SOURCE)
        for token in (
            "lifecycle->pointer_before",
            "lifecycle->pointer_after",
            '"pointer_before\\\":',
            '"capacity_after\\\":',
        ):
            self.assertIn(token, C_SOURCE)
        self.assertIn("static uint32_t bd_key", C_SOURCE)
        self.assertIn("uint32_t key_before", C_SOURCE)
        self.assertIn('"current_key\\\":%" PRIu32', C_SOURCE)


if __name__ == "__main__":
    unittest.main()
