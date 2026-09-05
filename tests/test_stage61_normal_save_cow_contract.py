from __future__ import annotations

import ast
import struct
import unittest
from pathlib import Path
from unittest import mock

from tools import stage61_state_namespace_collision_audit as audit


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / audit.STAGE61_RUNTIME_SOURCE_RELATIVE


class Stage61NormalSaveCowSourceContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE_PATH.read_text(encoding="utf-8")

    def _replace_once(
        self, source: str, old: str, new: str, *, after: str | None = None,
    ) -> str:
        start = source.index(after) if after is not None else 0
        position = source.find(old, start)
        self.assertGreaterEqual(position, 0, old)
        return source[:position] + new + source[position + len(old):]

    def assert_rejected(self, source: str) -> None:
        with self.assertRaises(audit.StateNamespaceCollisionAuditError):
            audit.validate_stage61_normal_save_cow_source(source)

    def test_current_source_satisfies_complete_normal_save_cow_contract(self) -> None:
        result = audit.validate_stage61_normal_save_cow_source(self.source)
        self.assertEqual(result["status"], "SOURCE_CONTROL_FLOW_EXACT")
        self.assertEqual(result["prewrite_calls"], [
            "UpdateSaveAddresses", "SaveSerializedGame",
        ])
        self.assertEqual(result["logical_sector_write_order"], list(range(14)))
        self.assertEqual(result["per_sector_full_readback_bytes"], 0x1000)
        self.assertEqual(result["post_generation_full_readback_count"], 14)
        self.assertTrue(all(result["assertions"].values()))

    def test_source_validation_does_not_depend_on_stale_artifact_sha(self) -> None:
        with mock.patch.object(audit, "STAGE60_ROM_SHA256", "0" * 64):
            result = audit.validate_stage61_normal_save_cow_source(self.source)
        self.assertEqual(result["status"], "SOURCE_CONTROL_FLOW_EXACT")

    def test_comments_cannot_substitute_for_removed_prewrite_call(self) -> None:
        mutated = self._replace_once(
            self.source,
            "    FN_UPDATE_SAVE_ADDRESSES();\n",
            "    /* FN_UPDATE_SAVE_ADDRESSES(); */\n",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        self.assert_rejected(mutated)

    def test_prewrite_duplicate_and_order_mutations_are_rejected(self) -> None:
        duplicate = self._replace_once(
            self.source,
            "    FN_UPDATE_SAVE_ADDRESSES();\n",
            "    FN_UPDATE_SAVE_ADDRESSES();\n"
            "    FN_UPDATE_SAVE_ADDRESSES();\n",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        swapped = self._replace_once(
            self.source,
            "    FN_UPDATE_SAVE_ADDRESSES();\n"
            "    FN_SAVE_SERIALIZED_GAME();\n",
            "    FN_SAVE_SERIALIZED_GAME();\n"
            "    FN_UPDATE_SAVE_ADDRESSES();\n",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        self.assert_rejected(duplicate)
        self.assert_rejected(swapped)

    def test_normal_dispatch_to_stock_writers_is_rejected(self) -> None:
        stock = self._replace_once(
            self.source,
            "        result = stage61_save_normal_copy_on_write();\n",
            "        result = stage61_save_normal_copy_on_write();\n"
            "        result = FN_STOCK_HANDLE_SAVING_DATA(save_type);\n",
            after="u8 Stage61State_HandleSavingData(u8 save_type)",
        )
        try_write = self._replace_once(
            self.source,
            "    FN_SAVE_SERIALIZED_GAME();\n",
            "    FN_SAVE_SERIALIZED_GAME();\n"
            "    (void)FN_TRY_WRITE_SECTOR(0u, (u8 *)0);\n",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        self.assert_rejected(stock)
        self.assert_rejected(try_write)

    def test_existing_save_link_stock_path_must_remain_present(self) -> None:
        removed = self._replace_once(
            self.source,
            "    result = FN_STOCK_HANDLE_SAVING_DATA(save_type);\n",
            "    result = 0u;\n",
            after="u8 Stage61State_HandleSavingData(u8 save_type)",
        )
        self.assert_rejected(removed)

    def test_protected_bank_writer_and_same_bank_target_are_rejected(self) -> None:
        selector_write = self._replace_once(
            self.source,
            "{\n    struct Stage61SaveSlotValidation first;",
            "{\n    stage61_save_mark_damaged(*selected_base);\n"
            "    struct Stage61SaveSlotValidation first;",
            after="stage61_save_choose_protected_generation(",
        )
        same_bank = self._replace_once(
            self.source,
            "STAGE61_SAVE_SLOT_SECTORS * (target_counter & 1u)",
            "STAGE61_SAVE_SLOT_SECTORS * (source_counter & 1u)",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        protected_writer = self._replace_once(
            self.source,
            "live_chunks, id, target_base, target_first_sector,",
            "live_chunks, id, protected_base, target_first_sector,",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        protected_final_read = self._replace_once(
            self.source,
            "u8 physical = (u8)(target_base + written.physical_by_id[id]);",
            "u8 physical = (u8)(protected_base + written.physical_by_id[id]);",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        self.assert_rejected(selector_write)
        self.assert_rejected(same_bank)
        self.assert_rejected(protected_writer)
        self.assert_rejected(protected_final_read)

    def test_newest_complete_generation_selection_is_required(self) -> None:
        always_first = self._replace_once(
            self.source,
            "*selected_base = stage61_save_second_counter_is_newer(\n"
            "                first.counter, second.counter)\n"
            "            ? STAGE61_SAVE_SLOT_SECTORS : 0u;",
            "*selected_base = 0u;",
            after="stage61_save_choose_protected_generation(",
        )
        self.assert_rejected(always_first)

    def test_id13_preinvalidation_and_two_fourteen_sector_loops_are_required(self) -> None:
        no_preinvalidate = self._replace_once(
            self.source,
            "stage61_save_invalidate_normal_target_record(",
            "stage61_save_invalidate_normal_target_record_removed(",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        short_loop = self._replace_once(
            self.source,
            "id < STAGE61_SAVE_SLOT_SECTORS; ++id",
            "id + 1u < STAGE61_SAVE_SLOT_SECTORS; ++id",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        wrong_record = self._replace_once(
            self.source,
            "(target_first_sector + 13u)",
            "(target_first_sector + 12u)",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        self.assert_rejected(no_preinvalidate)
        self.assert_rejected(short_loop)
        self.assert_rejected(wrong_record)

    def test_full_byte_readback_and_signature_last_are_required(self) -> None:
        short_readback = self._replace_once(
            self.source,
            "index < STAGE61_SAVE_SECTION_SIZE; ++index",
            "index < size; ++index",
            after="stage61_save_readback_matches_prepared(",
        )
        early_clear = self._replace_once(
            self.source,
            "    stage61_save_mark_damaged(target_sector);\n",
            "    stage61_save_mark_damaged(target_sector);\n"
            "    stage61_save_clear_damaged(target_sector);\n",
            after="stage61_save_write_normal_live_sector(",
        )
        try_write = self._replace_once(
            self.source,
            "    if (erase_sector(target_sector) != 0u)\n",
            "    (void)FN_TRY_WRITE_SECTOR(target_sector, (u8 *)section);\n"
            "    if (erase_sector(target_sector) != 0u)\n",
            after="stage61_save_write_normal_live_sector(",
        )
        wrong_final_owner = self._replace_once(
            self.source,
            "section, id, size, live_chunks[id].data,\n"
            "                target_counter, record_crc,",
            "section, id, size, live_chunks[0].data,\n"
            "                target_counter, record_crc,",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        self.assert_rejected(short_readback)
        self.assert_rejected(early_clear)
        self.assert_rejected(try_write)
        self.assert_rejected(wrong_final_owner)

    def test_transitive_stock_writer_alias_is_rejected(self) -> None:
        insertion = (
            "\nstatic u8 stage61_unsafe_normal_alias(void)\n"
            "{\n"
            "    return FN_TRY_WRITE_SECTOR(0u, (u8 *)0);\n"
            "}\n\n"
        )
        marker = "static __attribute__((noinline))\n"
        mutated = self.source.replace(marker, insertion + marker, 1)
        mutated = self._replace_once(
            mutated,
            "    FN_SAVE_SERIALIZED_GAME();\n",
            "    FN_SAVE_SERIALIZED_GAME();\n"
            "    (void)stage61_unsafe_normal_alias();\n",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        self.assert_rejected(mutated)

    def test_each_post_write_failure_must_restore_both_selector_fields(self) -> None:
        missing_counter = self._replace_once(
            self.source,
            "            G_SAVE_COUNTER = rollback_counter;\n",
            "",
            after="stage61_save_write_normal_live_sector(",
        )
        missing_rotation = self._replace_once(
            self.source,
            "            G_FIRST_SAVE_SECTOR = rollback_first_sector;\n",
            "",
            after="stage61_save_write_normal_live_sector(",
        )
        conditional_rotation = self._replace_once(
            self.source,
            "            G_FIRST_SAVE_SECTOR = rollback_first_sector;\n",
            "            if (has_protected != 0u)\n"
            "                G_FIRST_SAVE_SECTOR = rollback_first_sector;\n",
            after="stage61_save_write_normal_live_sector(",
        )
        dead_counter = self._replace_once(
            self.source,
            "            G_SAVE_COUNTER = rollback_counter;\n",
            "            if (0u != 0u)\n"
            "                G_SAVE_COUNTER = rollback_counter;\n",
            after="stage61_save_write_normal_live_sector(",
        )
        self.assert_rejected(missing_counter)
        self.assert_rejected(missing_rotation)
        self.assert_rejected(conditional_rotation)
        self.assert_rejected(dead_counter)

    def test_success_promotion_cannot_precede_final_readback(self) -> None:
        promoted_early = self._replace_once(
            self.source,
            "    record_crc = stage61_state_crc();\n",
            "    G_SAVE_COUNTER = target_counter;\n"
            "    G_FIRST_SAVE_SECTOR = target_first_sector;\n"
            "    record_crc = stage61_state_crc();\n",
            after="u8 stage61_save_normal_copy_on_write(void)",
        )
        promoted_early = self._replace_once(
            promoted_early,
            "    G_SAVE_COUNTER = target_counter;\n"
            "    G_FIRST_SAVE_SECTOR = target_first_sector;\n"
            "    return STAGE61_SAVE_STATUS_OK;\n",
            "    return STAGE61_SAVE_STATUS_OK;\n",
            after="stage61_save_readback_matches_prepared(",
        )
        self.assert_rejected(promoted_early)


class Stage61NormalSaveCowMetadataContractTest(unittest.TestCase):
    def test_exact_metadata_is_accepted(self) -> None:
        result = audit._validate_stage61_normal_save_cow_metadata(
            audit.stage61_normal_save_cow_metadata_contract()
        )
        self.assertEqual(result["status"], "METADATA_EXACT")
        self.assertEqual(len(result["contract_sha256"]), 64)

    def test_metadata_key_value_and_order_mutations_are_rejected(self) -> None:
        mutations = []
        removed = audit.stage61_normal_save_cow_metadata_contract()
        removed.pop("protected_bank_flash_policy")
        mutations.append(removed)
        changed = audit.stage61_normal_save_cow_metadata_contract()
        changed["stock_try_write_sector_used"] = True
        mutations.append(changed)
        reordered = audit.stage61_normal_save_cow_metadata_contract()
        reordered["logical_sector_order"] = list(reversed(range(14)))
        mutations.append(reordered)
        extra = audit.stage61_normal_save_cow_metadata_contract()
        extra["unreviewed_bypass"] = True
        mutations.append(extra)
        for declared in mutations:
            with self.subTest(declared=declared):
                with self.assertRaises(audit.StateNamespaceCollisionAuditError):
                    audit._validate_stage61_normal_save_cow_metadata(declared)

    def test_builder_declares_the_same_exact_metadata_contract(self) -> None:
        builder_path = ROOT / "scripts/build_stage61_display_npc_event_audit.py"
        tree = ast.parse(builder_path.read_text(encoding="utf-8"))
        declarations = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) \
                        and key.value == "normal_save_copy_on_write":
                    declarations.append(eval(
                        compile(
                            ast.Expression(value), str(builder_path), "eval"
                        ),
                        {"__builtins__": {}, "list": list, "range": range},
                        {},
                    ))
        expected = audit.stage61_normal_save_cow_metadata_contract()
        full = [row for row in declarations if "stock_entry_address" in row]
        summary = [row for row in declarations if "stock_entry_address" not in row]
        self.assertEqual(full, [expected])
        self.assertEqual(len(summary), 1)
        self.assertEqual(set(summary[0]), {
            "runtime_symbol", "save_type", "stock_handle_saving_data_delegated",
            "stock_try_write_sector_used", "protected_bank_flash_policy",
            "preinvalidation_callback_failure_is_not_ignored",
            "save_failed_screen_wipe_retry_mgba_required",
            "natural_start_menu_second_retry_mgba_required",
            "fresh_core_continue_mgba_required",
        })
        self.assertEqual(summary[0], {key: expected[key] for key in summary[0]})


class Stage61NormalSaveCowObjectContractTest(unittest.TestCase):
    @staticmethod
    def _thumb_bl(site: int, target: int) -> bytes:
        displacement = target - (site + 4)
        if displacement & 1 or not -(1 << 22) <= displacement < (1 << 22):
            raise AssertionError("invalid synthetic Thumb BL displacement")
        displacement &= (1 << 23) - 1
        return struct.pack(
            "<HH",
            0xF000 | ((displacement >> 12) & 0x07FF),
            0xF800 | ((displacement >> 1) & 0x07FF),
        )

    def _fixture(self) -> tuple[bytes, dict[str, int], int, int]:
        code_address = audit.ROM_BASE + 0x100
        code_size = 0x100
        wrapper = code_address
        normal = code_address + 0x40
        sentinel = code_address + 0xC0
        rom = bytearray(0x300)
        rom[0x100:0x104] = self._thumb_bl(wrapper, normal)
        rom[0x108:0x10C] = struct.pack("<I", 0x080DB231)
        rom[0x140:0x144] = struct.pack("<I", 0x080DB1BD)
        rom[0x144:0x148] = struct.pack("<I", 0x0804BAB9)
        symbols = {
            "Stage61State_HandleSavingData": wrapper,
            "stage61_save_normal_copy_on_write": normal,
            "stage61_object_sentinel": sentinel,
            "Stage61State_HandleWriteSector": code_address + 0xD0,
            "Stage61State_HandleReplaceSector": code_address + 0xE0,
        }
        return bytes(rom), symbols, code_address, code_size

    def test_synthetic_object_dispatch_and_literals_are_accepted(self) -> None:
        result = audit._stage61_normal_save_cow_object_contract(*self._fixture())
        self.assertEqual(
            result["status"], "OBJECT_DISPATCH_AND_LITERAL_CLOSURE_EXACT"
        )
        self.assertEqual(result["stock_try_write_literal_count"], 0)
        self.assertEqual(result["normal_dispatch_sites"], [audit.ROM_BASE + 0x100])

    def test_object_dispatch_and_dangerous_literal_mutations_are_rejected(self) -> None:
        raw, symbols, code_address, code_size = self._fixture()
        mutations: list[bytes] = []
        no_dispatch = bytearray(raw)
        no_dispatch[0x100:0x104] = b"\x00" * 4
        mutations.append(bytes(no_dispatch))
        stock_try = bytearray(raw)
        stock_try[0x150:0x154] = struct.pack("<I", 0x080DA9C1)
        mutations.append(bytes(stock_try))
        duplicated_prewrite = bytearray(raw)
        duplicated_prewrite[0x150:0x154] = struct.pack("<I", 0x080DB1BD)
        mutations.append(bytes(duplicated_prewrite))
        missing_link_stock = bytearray(raw)
        missing_link_stock[0x108:0x10C] = b"\x00" * 4
        mutations.append(bytes(missing_link_stock))
        for mutated in mutations:
            with self.subTest(sha=audit._sha(mutated)):
                with self.assertRaises(audit.StateNamespaceCollisionAuditError):
                    audit._stage61_normal_save_cow_object_contract(
                        mutated, symbols, code_address, code_size
                    )

    def test_object_transitive_unsafe_alias_is_rejected(self) -> None:
        raw, symbols, code_address, code_size = self._fixture()
        normal = symbols["stage61_save_normal_copy_on_write"]
        alias = code_address + 0x80
        sentinel = symbols["stage61_object_sentinel"]
        mutated = bytearray(raw)
        mutated[0x148:0x14C] = self._thumb_bl(normal + 8, alias)
        mutated[0x180:0x184] = struct.pack("<I", 0x080DA9C1)
        alias_symbols = dict(symbols)
        alias_symbols["stage61_unsafe_normal_alias"] = alias
        alias_symbols["stage61_object_sentinel"] = sentinel
        with self.assertRaises(audit.StateNamespaceCollisionAuditError):
            audit._stage61_normal_save_cow_object_contract(
                bytes(mutated), alias_symbols, code_address, code_size
            )


if __name__ == "__main__":
    unittest.main()
