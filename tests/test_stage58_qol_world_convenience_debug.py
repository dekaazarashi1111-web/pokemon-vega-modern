from __future__ import annotations

import copy
import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_stage58_qol_world_convenience_debug import (  # noqa: E402
    DEFAULT_CONFIG,
    Stage58BuildError,
    _apply_codex_save_layout_repair,
    _build_static,
    _thin_flag_owner_audit,
    _validate_saveblock_key_rotation_stock_contract,
)
from tools.release.bps import apply_bps  # noqa: E402
from tools.stage58_debug_suite import (  # noqa: E402
    Stage58DebugError,
    _codex_result_surface,
    full_audit,
)


class Stage58QolWorldConvenienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / DEFAULT_CONFIG).read_text(encoding="utf-8"))
        cls.outputs = _build_static(DEFAULT_CONFIG)
        paths = cls.config["outputs"]
        cls.rom = cls.outputs[paths["rom"]]
        cls.metadata = json.loads(cls.outputs[paths["metadata"]])
        cls.cases = json.loads(cls.outputs[paths["cases"]])
        cls.stage57 = (
            ROOT / cls.config["inputs"]["stage57_rom"]["path"]
        ).read_bytes()
        cls.stage57_allocation = json.loads((
            ROOT / cls.config["inputs"]["stage57_allocation"]["path"]
        ).read_text(encoding="utf-8"))

    def test_build_is_byte_deterministic(self) -> None:
        self.assertEqual(self.outputs, _build_static(DEFAULT_CONFIG))

    def test_incremental_and_clean_bps_are_exact(self) -> None:
        inputs = self.config["inputs"]
        paths = self.config["outputs"]
        stage57 = (ROOT / inputs["stage57_rom"]["path"]).read_bytes()
        clean = (ROOT / inputs["clean_rom"]["path"]).read_bytes()
        self.assertEqual(
            self.rom,
            apply_bps(stage57, self.outputs[paths["incremental_bps"]]),
        )
        self.assertEqual(
            self.rom,
            apply_bps(clean, self.outputs[paths["clean_bps"]]),
        )

    def test_full_map_script_wild_and_story_audit(self) -> None:
        result = full_audit(self.rom, self.metadata, self.cases)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(678, result["script_cfg"]["physical_maps"])
        self.assertEqual(0, result["script_cfg"]["diagnostic_count"])
        self.assertEqual(0, result["script_cfg"]["removed_root_count"])
        self.assertEqual(9, result["script_cfg"]["added_root_count"])
        self.assertEqual(0, result["wild_surface"]["forbidden_native_inclusion_count"])
        save_contract = result["saveblock_key_rotation_stock_surface"]
        self.assertEqual("PASS", save_contract["status"])
        self.assertEqual(
            [
                "SetSaveBlocksPointersOwnsBagRebind",
                "RestoreSaveBlockCopies",
                "ApplyNewEncryptionKeyToAllEncryptedData",
                "StoreNewEncryptionKey",
            ],
            save_contract["call_order"],
        )
        save_layout = result["codex_save_layout_surface"]
        self.assertEqual("PASS", save_layout["status"])
        self.assertEqual(3, save_layout["function_count"])
        self.assertEqual(6, save_layout["patch_count"])
        self.assertTrue(save_layout["bag_snapshot_restore_removed"])
        self.assertTrue(save_layout["seen_and_personality_restore"])
        self.assertTrue(save_layout["owned_and_header_hash_guarded"])

    def test_codex_hub_and_thin_event_transactions(self) -> None:
        result = full_audit(self.rom, self.metadata, self.cases)
        hub = result["map_events"]["codex_hub"]
        self.assertEqual((10, 13), (
            hub["object_count_before"], hub["object_count_after"],
        ))
        self.assertTrue(hub["existing_objects_preserved"])
        self.assertTrue(hub["warps_coords_bg_preserved"])
        self.assertTrue(hub["pc_waitstate_declared"])
        self.assertTrue(hub["pc_field_return_requires_mgba"])
        self.assertTrue(hub["healer_standard_special"])
        self.assertTrue(hub["normal_money_mart"])
        self.assertEqual(22, hub["mart_item_pocket_field_offset"])
        self.assertTrue(hub["mart_add_before_money_debit"])
        self.assertTrue(hub["mart_bag_full_no_debit_requires_mgba"])
        self.assertEqual(6, result["map_events"]["thin_event_count"])
        self.assertTrue(all(
            row["bag_full_preserves_flag"]
            for row in result["map_events"]["thin_events"]
        ))
        owner = result["map_events"]["thin_flag_owner"]
        self.assertTrue(owner["native_runtime_exact"])
        self.assertEqual(0x02037004, owner["getter_result_address"])
        self.assertTrue(owner["setter_read_modify_write"])
        self.assertEqual([56, 44], [row["size"] for row in owner["runtime_rows"]])
        field_items = result["field_item_surface"]
        self.assertEqual(250, field_items["inherited_transaction_count"])
        self.assertEqual(1000, field_items["inherited_script_segment_count"])
        self.assertEqual(6, field_items["new_atomic_reward_transactions"])
        self.assertEqual(256, field_items["total_transaction_count"])

    def test_thin_native_flag_runtime_is_exact_and_mutation_fails_closed(self) -> None:
        evidence = self.metadata["overlap_audit"]["evidence"]["save"]
        self.assertTrue(evidence["native_runtime_exact"])
        self.assertTrue(evidence["quest_log_safe"])
        self.assertEqual(0x02037004, evidence["getter_result_address"])
        self.assertTrue(evidence["setter_read_modify_write"])
        self.assertEqual([56, 44], [
            row["size"] for row in evidence["native_runtime_rows"]
        ])
        mutated = bytearray(self.rom)
        getter = self.metadata["runtime"]["labels"]["runtime::thin_flag_get"]
        # Exact getter's RESULT address literal is its final u32.
        mutated[getter - 0x08000000 + 52] ^= 0x02
        stage57 = (ROOT / self.config["inputs"]["stage57_rom"]["path"]).read_bytes()
        with self.assertRaisesRegex(Stage58BuildError, "runtime exact byte"):
            _thin_flag_owner_audit(
                stage57, bytes(mutated), self.metadata["world"]["thin_events"],
                self.metadata["runtime"]["labels"],
            )
        mutated_metadata = copy.deepcopy(self.metadata)
        mutated_cases = copy.deepcopy(self.cases)
        mutated_sha = hashlib.sha256(mutated).hexdigest()
        mutated_metadata["output"]["sha256"] = mutated_sha
        mutated_cases["rom_sha256"] = mutated_sha
        with self.assertRaisesRegex(Stage58DebugError, "runtime exact byte"):
            full_audit(bytes(mutated), mutated_metadata, mutated_cases)

    def test_qol_item_graphics_consumers_use_full_canonical_table(self) -> None:
        contract = self.config["qol_item_graphics"]
        evidence = self.metadata["qol_item_graphics"]
        canonical = int(contract["canonical_table"], 0)
        self.assertEqual("PASS", evidence["status"])
        self.assertEqual(999, evidence["item_count"])
        self.assertEqual(3, evidence["repoint_count"])
        self.assertEqual(0, evidence["legacy_literal_remaining_count"])
        self.assertEqual(3, evidence["canonical_literal_owner_count"])
        self.assertEqual(3, evidence["cancel_icon_rebind_count"])
        self.assertTrue(evidence["cancel_icon_exact_row_match"])
        self.assertEqual(1998, evidence["lz77_pointer_count"])
        self.assertGreater(evidence["lz77_unique_stream_count"], 0)
        self.assertGreater(evidence["lz77_decompressed_byte_count"], 0)
        self.assertEqual(0, evidence["invalid_pointer_count"])
        for raw_site in contract["consumer_pointer_sites"]:
            site = int(raw_site, 0)
            self.assertEqual(
                canonical,
                struct.unpack_from("<I", self.rom, site - 0x08000000)[0],
            )
        for raw_site in contract["cancel_icon_item_sites"]:
            site = int(raw_site, 0)
            self.assertEqual(
                589,
                struct.unpack_from("<I", self.rom, site - 0x08000000)[0],
            )
        table = canonical - 0x08000000
        for item_id in range(999):
            graphics, palette = struct.unpack_from(
                "<II", self.rom, table + item_id * 8,
            )
            self.assertEqual(0x10, self.rom[graphics - 0x08000000])
            self.assertEqual(0x10, self.rom[palette - 0x08000000])

    def test_qol_item_id_common_clamp_accepts_full_manifest_range(self) -> None:
        contract = self.config["qol_item_id_clamp"]
        evidence = self.metadata["qol_item_id_clamp"]
        site = int(contract["site"], 0) - 0x08000000
        replacement = bytes.fromhex(contract["replacement"])
        self.assertEqual("PASS", evidence["status"])
        self.assertEqual((0, 998), (
            evidence["valid_min_inclusive"],
            evidence["valid_max_inclusive"],
        ))
        self.assertEqual((999, 0), (
            evidence["invalid_min_inclusive"],
            evidence["invalid_maps_to"],
        ))
        self.assertTrue(evidence["legacy_r1_return_side_effect_preserved"])
        self.assertTrue(evidence["legacy_condition_flags_preserved"])
        self.assertEqual(replacement, self.rom[site:site + len(replacement)])

    def test_bottle_caps_use_normal_bag_adapter_to_service_owner(self) -> None:
        contract = self.config["qol_item_bag_adapter"]
        evidence = self.metadata["qol_item_bag_adapter"]
        table = int(contract["item_table"], 0) - 0x08000000
        replacement = evidence["replacement_callback"]
        self.assertEqual("PASS", evidence["status"])
        self.assertEqual([853, 854], evidence["item_ids"])
        self.assertEqual(2, evidence["row_count"])
        self.assertEqual((4, 1), (
            evidence["expected_type"], evidence["replacement_type"],
        ))
        self.assertEqual(
            "Stage58QolItemAdapter_FieldUseBottleCapAdapter",
            evidence["replacement_symbol"],
        )
        self.assertEqual(1, replacement & 1)
        self.assertEqual(0, evidence["runtime"]["mutable_symbol_count"])
        self.assertEqual(0, evidence["runtime"]["undefined_symbol_count"])
        self.assertFalse(
            evidence["service_owner"]["adapter_direct_bag_mutation"]
        )
        self.assertFalse(evidence["service_owner"]["new_ram_or_save_owner"])
        self.assertEqual(17, evidence["service_owner"]["service"])
        for item_id in (853, 854):
            row = table + item_id * int(contract["row_size"])
            self.assertEqual(
                item_id,
                struct.unpack_from("<H", self.rom, row + 10)[0],
            )
            self.assertEqual(1, self.rom[row + 22])
            self.assertEqual(1, self.rom[row + 23])
            self.assertEqual(
                replacement,
                struct.unpack_from("<I", self.rom, row + 24)[0],
            )

    def test_saveblock_key_rotation_preserves_stock_chain(self) -> None:
        contract = self.config["saveblock_key_rotation_stock_contract"]
        evidence = self.metadata["saveblock_key_rotation_stock_contract"]
        site = int(contract["apply_all_call_site"], 0)
        offset = site - 0x08000000
        bag_site = int(contract["bag_encryption_call_site"], 0)
        bag_offset = bag_site - 0x08000000
        veneer_address = int(contract["veneer"]["address"], 0)
        veneer_offset = veneer_address - 0x08000000
        self.assertEqual("PASS", evidence["status"])
        self.assertEqual("preserve_stock_no_runtime_rebind", evidence["policy"])
        self.assertEqual(0x0804B85D, evidence["move_save_blocks_reset_heap"])
        self.assertEqual(0x0804B8FA, evidence["apply_all_call_site"])
        self.assertEqual(0x0804BD76, evidence["bag_encryption_call_site"])
        self.assertTrue(evidence["stock_callback_restore_preserved"])
        self.assertTrue(evidence["stock_apply_all_preserved"])
        self.assertTrue(evidence["stock_bag_child_preserved"])
        self.assertEqual(0x0809984D, evidence["set_bag_pockets_pointers"])
        self.assertEqual(
            0x0804BD5D, evidence["original_apply_new_encryption"],
        )
        self.assertEqual(0x08099841, evidence["original_bag_encryption"])
        self.assertEqual(0x03005048, evidence["save_block1_pointer"])
        self.assertEqual(0x0300504C, evidence["save_block2_pointer"])
        self.assertEqual(0x020397D8, evidence["bag_pockets"])
        self.assertEqual((8, 5), (
            evidence["descriptor_stride"], evidence["descriptor_count"],
        ))
        self.assertEqual(
            [
                {"name": "items", "save1_offset": 0x0310,
                 "capacity": 42},
                {"name": "key_items", "save1_offset": 0x03B8,
                 "capacity": 30},
                {"name": "poke_balls", "save1_offset": 0x0430,
                 "capacity": 13},
                {"name": "tm_case", "save1_offset": 0x0464,
                 "capacity": 58},
                {"name": "berry_pouch", "save1_offset": 0x054C,
                 "capacity": 43},
            ],
            evidence["bag_pocket_descriptors"],
        )
        self.assertEqual(0, evidence["additional_runtime_rebind_count"])
        self.assertTrue(evidence["host_rebind_after_field_return_forbidden"])
        self.assertEqual(
            [
                "SetSaveBlocksPointersOwnsBagRebind",
                "RestoreSaveBlockCopies",
                "ApplyNewEncryptionKeyToAllEncryptedData",
                "StoreNewEncryptionKey",
            ],
            evidence["call_order"],
        )
        self.assertTrue(evidence["all_stock_encrypted_fields_preserved"])
        self.assertEqual(0, evidence["new_ram_or_save_owner_count"])
        self.assertEqual(
            bytes.fromhex(contract["expected_stock_apply_all_call"]),
            self.rom[offset:offset + 4],
        )
        self.assertEqual(
            bytes.fromhex(contract["veneer"]["expected"]),
            self.rom[veneer_offset:veneer_offset + 8],
        )
        self.assertEqual(0, evidence["veneer"]
                         ["preexisting_pointer_reference_count"])
        self.assertEqual(0, evidence["veneer"]
                         ["prior_allocation_overlap_count"])
        self.assertTrue(evidence["veneer"]["remains_unallocated"])
        self.assertEqual(
            bytes.fromhex(contract["expected_stock_apply_all_call"]),
            self.stage57[offset:offset + 4],
        )
        self.assertEqual(
            bytes.fromhex(contract["expected_bag_encryption_call"]),
            self.rom[bag_offset:bag_offset + 4],
        )
        mutated = bytearray(self.stage57)
        mutated[offset] ^= 0x01
        with self.assertRaisesRegex(
            Stage58BuildError, "stock byte不一致",
        ):
            _validate_saveblock_key_rotation_stock_contract(
                bytearray(mutated), bytes(mutated), contract,
                self.metadata["runtime"]["qol_item_adapter"]["symbols"],
                self.metadata["runtime"]["qol_item_adapter"]["symbol_sizes"],
                self.stage57_allocation,
                [],
            )

    def test_codex_save_layout_repair_is_exact_and_fail_closed(self) -> None:
        contract = self.config["codex_save_layout_repair"]
        evidence = self.metadata["codex_save_layout_repair"]
        self.assertEqual("PASS", evidence["status"])
        self.assertEqual(6, evidence["patch_count"])
        self.assertEqual(3, evidence["adapter_callsite_count"])
        self.assertEqual(164, evidence["snapshot_buffers"]["used"])
        self.assertEqual(166, evidence["snapshot_buffers"]["capacity"])
        self.assertEqual(2, evidence["snapshot_buffers"]["unused"])
        self.assertTrue(evidence["bag_snapshot_restore_removed"])
        self.assertTrue(evidence["existing_public_state_offset_preserved"])
        self.assertEqual(0, evidence["new_ram_or_save_owner_count"])
        self.assertIn(
            "save2_unown_spinda_personalities",
            evidence["snapshot_restore_mirrors"],
        )
        self.assertIn("save2_owned", evidence["hash_mirrors"])
        for row in evidence["patches"]:
            offset = int(row["site"]) - 0x08000000
            self.assertEqual(
                bytes.fromhex(row["expected"]),
                self.stage57[offset:offset + int(row["size"])],
            )
            self.assertEqual(
                bytes.fromhex(row["replacement"]),
                self.rom[offset:offset + int(row["size"])],
            )
        mutated = bytearray(self.stage57)
        site = int(contract["patches"]["snapshot_save1"]["site"], 0)
        mutated[site - 0x08000000] ^= 1
        with self.assertRaisesRegex(
            Stage58BuildError, "Codex save layout expected byte不一致",
        ):
            _apply_codex_save_layout_repair(
                bytearray(mutated), bytes(mutated), contract,
                self.metadata["runtime"]["qol_item_adapter"]["symbols"],
                self.metadata["runtime"]["qol_item_adapter"]["symbol_sizes"],
                [],
            )

    def test_codex_mailbox_stage47_capability_compat_is_exact_guarded(self) -> None:
        contract = self.config["codex_mailbox_compat"]
        evidence = self.metadata["codex_mailbox_compat"]
        site = int(contract["read_keys_pointer_site"], 0) - 0x08000000
        self.assertEqual("PASS", evidence["status"])
        self.assertEqual(0x1FFF, evidence["stage44_capabilities"])
        self.assertEqual(0x7FFF, evidence["stage47_public_capabilities"])
        self.assertEqual(
            "PATCH_STAGE44_INITIALIZER_AND_VALIDATOR_LITERALS_TO_0x7FFF",
            evidence["compatibility_strategy"],
        )
        self.assertEqual(0x7FFF, evidence["external_capabilities_after_delegate"])
        self.assertFalse(evidence["post_delegate_crc_and_sequence_republished"])
        self.assertFalse(evidence["request_owner_changed"])
        self.assertFalse(evidence["mailbox_owner_changed"])
        self.assertEqual(0, evidence["new_ram_or_save_owner_count"])
        self.assertEqual(
            int(contract["expected_delegate"], 0),
            struct.unpack_from("<I", self.rom, site)[0],
        )
        self.assertTrue(evidence["delegate_unchanged"])
        self.assertEqual(2, evidence["patched_literal_count"])
        for literal in evidence["patched_literals"]:
            offset = int(literal["address"]) - 0x08000000
            self.assertEqual(0x7FFF, struct.unpack_from("<I", self.rom, offset)[0])
        config_site = int(contract["stage44_embedded_config_capability_site"], 0)
        self.assertEqual(
            0x1FFF,
            struct.unpack_from("<I", self.rom, config_site - 0x08000000)[0],
        )
        self.assertTrue(evidence["embedded_config_unchanged"])

    def test_codex_win_loss_draw_results_bypass_uninitialized_tower_text_owner(self) -> None:
        contract = self.config["codex_result_compat"]
        evidence = self.metadata["codex_result_compat"]
        table = int(contract["end_turn_function_table"], 0)
        self.assertEqual("PASS", evidence["status"])
        self.assertEqual(
            "CODEX_TRANSACTION_WIN_LOSS_DRAW_CLEAR_TOWER_"
            "OVERRIDE_PICKUP_END2_CONTROLLER_INDEPENDENT_PARTIAL_FAIL_CLOSED",
            evidence["strategy"],
        )
        self.assertEqual(0x093D1E01, evidence["inherited_return_to_field_adapter"])
        self.assertEqual(
            self.metadata["runtime"]["qol_item_adapter"]["symbols"]
                ["Stage58QolItemAdapter_CodexReturnToFieldAdapter"] | 1,
            evidence["return_to_field_adapter"],
        )
        self.assertEqual(0x081BC8BB, evidence["nonpunitive_result_script"])
        self.assertTrue(evidence["non_codex_delegates_preserved"])
        self.assertTrue(evidence["controller_disconnect_safe"])
        self.assertEqual(["win", "loss", "draw"], evidence["owned_result_kinds"])
        self.assertEqual(
            {"win": 1, "loss": 2, "draw": 3, "forfeit": 4},
            evidence["reward_result_taxonomy"],
        )
        self.assertEqual(
            "MAGIC_INVERSE_ACTIVE",
            evidence["return_guard"],
        )
        self.assertEqual(
            "MAGIC_INVERSE_ACTIVE_BOTH_SELECTIONS_"
            "FIELD_COMPLETION_PENDING_TRAINER_OPPONENT_745",
            evidence["result_guard"],
        )
        self.assertTrue(evidence["partial_legacy_hazard_fail_closed"])
        self.assertEqual(
            "STOCK_RESULT_WITHOUT_STAGE47_DELEGATE",
            evidence["partial_legacy_hazard_action"],
        )
        self.assertEqual(0, evidence["new_ram_or_save_owner_count"])
        reward_mapping = self.metadata["codex_reward_result_kind"]
        self.assertEqual("PASS", reward_mapping["status"])
        self.assertEqual(
            {"win": 1, "loss": 2, "draw": 3, "forfeit": 4},
            reward_mapping["taxonomy"],
        )
        self.assertTrue(
            reward_mapping[
                "finalized_and_persisted_by_inherited_owner_after_mapping"
            ]
        )
        self.assertEqual(3, len(evidence["rows"]))
        pointers = {
            row["kind"]: struct.unpack_from(
                "<I", self.rom, int(row["site"]) - 0x08000000,
            )[0]
            for row in evidence["rows"]
        }
        self.assertEqual(
            pointers["win"],
            struct.unpack_from("<I", self.rom, table + 4 - 0x08000000)[0],
        )
        self.assertEqual(
            pointers["loss"],
            struct.unpack_from("<I", self.rom, table + 8 - 0x08000000)[0],
        )
        self.assertEqual(
            pointers["draw"],
            struct.unpack_from("<I", self.rom, table + 12 - 0x08000000)[0],
        )
        self.assertTrue(all(pointer & 1 for pointer in pointers.values()))
        independent = full_audit(
            self.rom, self.metadata, self.cases,
        )["codex_result_surface"]
        self.assertEqual("PASS", independent["status"])
        self.assertEqual(3, len(independent["rows"]))
        self.assertEqual(16, independent["required_literal_count"])
        self.assertEqual(9, independent["exact_function_count"])
        self.assertEqual(6, independent["inherited_exact_surface_count"])
        self.assertEqual(7, independent["legacy_exact_function_count"])
        self.assertEqual(
            {"win": 1, "loss": 2, "draw": 3, "forfeit": 4},
            independent["reward_result_taxonomy"],
        )
        self.assertTrue(independent["reward_mapping_before_finalize_persist"])
        self.assertTrue(independent["runtime_state_guarded"])
        self.assertTrue(independent["controller_disconnect_safe"])
        self.assertTrue(independent["win_loss_draw_owned"])
        self.assertTrue(independent["tower_text_owner_bypassed_for_codex_only"])
        mutated = bytearray(self.rom)
        mutated[table + 4 - 0x08000000] ^= 0x02
        mutated_metadata = copy.deepcopy(self.metadata)
        mutated_cases = copy.deepcopy(self.cases)
        mutated_sha = hashlib.sha256(mutated).hexdigest()
        mutated_metadata["output"]["sha256"] = mutated_sha
        mutated_cases["rom_sha256"] = mutated_sha
        with self.assertRaisesRegex(Stage58DebugError, "win adapter配線"):
            full_audit(bytes(mutated), mutated_metadata, mutated_cases)

        # metadata内のadapter SHAまで攻撃側に合わせても、各ownerの独立した
        # exact命令契約がreturn/guard/finish/win/lossの改変をfail-closeする。
        for symbol in (
            "Stage58QolItemAdapter_CodexReturnToFieldAdapter",
            "Stage58QolItemAdapter_CodexTransactionIdentityValid",
            "Stage58QolItemAdapter_CodexResultStateValid",
            "Stage58QolItemAdapter_CodexBattleResultOwned",
            "Stage58QolItemAdapter_CodexLegacyResultHazard",
            "Stage58QolItemAdapter_CodexRewardResultKind",
            "Stage58QolItemAdapter_FinishNonpunitiveCodexResult",
            "Stage58QolItemAdapter_CodexBattleWonAdapter",
            "Stage58QolItemAdapter_CodexBattleLostAdapter",
        ):
            mutated = bytearray(self.rom)
            runtime = self.metadata["runtime"]["qol_item_adapter"]
            address = int(runtime["symbols"][symbol])
            size = int(runtime["symbol_sizes"][symbol])
            mutated[address - 0x08000000 + size // 3] ^= 0x01
            mutated_metadata = copy.deepcopy(self.metadata)
            adapter = mutated_metadata["runtime"]["qol_item_adapter"]
            load = int(adapter["load_address"]) - 0x08000000
            adapter["sha256"] = hashlib.sha256(
                mutated[load:load + int(adapter["size"])]
            ).hexdigest()
            with self.subTest(symbol=symbol), self.assertRaisesRegex(
                Stage58DebugError, "命令契約不一致",
            ):
                _codex_result_surface(
                    bytes(mutated), self.stage57, mutated_metadata,
                )

        for address in (
            0x093D2090, 0x093D20A0, 0x093D20B0,
            0x093D20CE, 0x093D20D0, 0x093D20D6,
            0x093D2BC0, 0x093D2118, 0x093CB824, 0x093CB85C,
        ):
            mutated = bytearray(self.rom)
            mutated[address - 0x08000000] ^= 0x01
            with self.subTest(address=f"0x{address:08X}"), \
                    self.assertRaisesRegex(
                        Stage58DebugError,
                        "whole-function契約不一致|mapping/finalize/persist契約不一致",
                    ):
                _codex_result_surface(
                    bytes(mutated), self.stage57, self.metadata,
                )

    def test_wild_reward_and_mart_balance_policies_are_enforced(self) -> None:
        balance = self.metadata["content_balance"]
        self.assertEqual("PASS", balance["status"])
        self.assertEqual(5, len(balance["wild_rates"]))
        self.assertTrue(all(row["min"] <= row["rate"] <= row["max"]
                            for row in balance["wild_rates"]))
        self.assertEqual(6, len(balance["thin_rewards"]))
        self.assertTrue(all(row["min"] <= row["total_value"] <= row["max"]
                            for row in balance["thin_rewards"]))
        self.assertEqual(11, balance["mart"]["item_count"])
        self.assertEqual(0, balance["mart"]["duplicate_count"])
        self.assertEqual(0, balance["mart"]["important_item_count"])

    def test_identity_drift_fails_closed(self) -> None:
        cases = copy.deepcopy(self.cases)
        cases["rom_sha256"] = "0" * 64
        with self.assertRaises(Stage58DebugError):
            full_audit(self.rom, self.metadata, cases)


if __name__ == "__main__":
    unittest.main()
