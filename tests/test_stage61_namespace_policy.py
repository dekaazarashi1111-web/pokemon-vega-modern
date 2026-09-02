from __future__ import annotations

from collections import Counter
import struct
import unittest
from pathlib import Path

from tools.stage61_event_semantic_relocator import plan_from_files
from tools.stage61_namespace_policy import (
    ALLOCATABLE_SCRIPT_FLAG_IDS,
    ENGINE_SPECIAL_FLAG_RANGE,
    ENGINE_SYSTEM_FLAG_IDS,
    ENGINE_SYSTEM_FLAG_SHADOW_TARGETS,
    FLAG_NAMESPACE_RANGE,
    MULTICHOICE_REMAP,
    MULTICHOICE_STOCK_COUNT,
    MULTICHOICE_TABLE_ADDRESS,
    OBJECT_ONLY_FLAG_NAMESPACE_RANGE,
    ROM_BASE,
    TEMP_FLAG_IDS,
    UNALLOCATED_SCRIPT_FLAG_GUARD,
    VAR_NAMESPACE_RANGE,
    Stage61NamespacePolicyError,
    allocate_stage61_object_visibility_namespace,
    build_stage61_local_object_namespace_plan,
    build_stage61_namespace_policy,
    build_stage61_object_visibility_namespace_plan,
    materialize_multichoice_runtime_contract,
    materialize_stage61_missing_object_templates,
)


ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
STAGE60_PATH = ROOT / "build/stages/60_wild_species_root_repair.gba"
OWNER_LEDGER_PATH = ROOT / "reports/generated/world_runtime_owner_ledger.json"
CHARMAP_PATH = ROOT / "vendor/upstream/CFRU-JP/charmap.tbl"
CANONICAL_MAP_DIRECTORY = ROOT / "generated/maps/kanto"


class Stage61NamespacePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = CLEAN_PATH.read_bytes()
        cls.stage60 = STAGE60_PATH.read_bytes()
        cls.full_cfg = plan_from_files(
            STAGE60_PATH,
            CLEAN_PATH,
            OWNER_LEDGER_PATH,
            CHARMAP_PATH,
            CANONICAL_MAP_DIRECTORY,
        ).full_cfg_plan(cls.clean)
        cls.policy, cls.report = build_stage61_namespace_policy(
            ROOT, cls.full_cfg, cls.clean, cls.stage60
        )

    def test_real_full_cfg_policy_passes_and_materializes_every_operand(self) -> None:
        self.assertEqual(self.report["status"], "PASS")
        self.assertEqual(self.report["policy_audit"]["status"], "PASS")
        self.assertEqual(self.full_cfg.policy_audit(self.policy)["status"], "PASS")
        self.assertEqual(len(self.full_cfg.instructions), 9046)
        self.assertEqual(len(self.full_cfg.numeric_references), 8949)
        self.assertEqual(len(self.full_cfg.effect_requirements), 163)
        self.assertEqual(self.full_cfg.unsupported_pointer_references, ())

        materialized = self.full_cfg.materialize(0x09E00000, self.policy)
        self.assertEqual(len(materialized.payload), 85738)
        self.assertTrue(materialized.to_report()["verified"])
        self.assertTrue(all(materialized.verification_assertions.values()))

    def test_state_namespace_is_exact_deterministic_and_temp_flags_stay_temp(self) -> None:
        flag_mapping = self.policy.mappings["flag"]
        var_mapping = self.policy.mappings["var"]
        self.assertEqual(len(flag_mapping), 124)
        self.assertEqual(len(var_mapping), 19)
        self.assertEqual(
            list(flag_mapping.values()), list(ALLOCATABLE_SCRIPT_FLAG_IDS)
        )
        self.assertEqual(list(var_mapping.values()), list(VAR_NAMESPACE_RANGE))
        self.assertTrue(set(flag_mapping).isdisjoint(TEMP_FLAG_IDS))
        self.assertEqual(
            self.policy.mappings["temp_flag"], {1: 1, 2: 2, 3: 3}
        )
        self.assertEqual(
            self.policy.mappings["special_flag"], {0x4001: 0x4001}
        )
        self.assertEqual(
            self.policy.mappings["engine_system_flag"], {0x0805: 0x0805}
        )
        self.assertEqual(ENGINE_SYSTEM_FLAG_IDS, {0x0805})
        self.assertEqual(ENGINE_SYSTEM_FLAG_SHADOW_TARGETS, {0x0805: 0x18B3})
        self.assertNotIn(0x0805, flag_mapping)
        self.assertNotIn(0x18B3, flag_mapping.values())
        self.assertEqual(flag_mapping[0x04B7], 0x18B2)
        self.assertEqual(flag_mapping[0x0820], 0x18B4)
        self.assertTrue(all(
            source in ENGINE_SPECIAL_FLAG_RANGE
            for source in self.policy.mappings["special_flag"]
        ))
        self.assertNotIn(
            UNALLOCATED_SCRIPT_FLAG_GUARD, flag_mapping.values()
        )
        self.assertEqual(
            self.report["reserved_state_namespace"][
                "unallocated_script_flag_guard"
            ]["id"],
            "0x18C4",
        )
        engine_system = self.report["reserved_state_namespace"][
            "engine_system_flags"
        ]
        self.assertEqual(engine_system["status"], "PASS")
        self.assertEqual(engine_system["mapping"], {"0x0805": "0x0805"})
        self.assertEqual(engine_system["unallocated_shadow_guard"], "0x18B3")
        self.assertEqual(len(engine_system["script_sites"]), 2)
        self.assertEqual(len(engine_system["native_sites"]), 12)
        self.assertEqual(self.policy.identity_categories, frozenset())

        visibility_mapping = allocate_stage61_object_visibility_namespace(
            self.full_cfg, [0x4001]
        )
        self.assertEqual(visibility_mapping[0x4001], 0x4001)
        self.assertNotIn(0x4001, set(FLAG_NAMESPACE_RANGE))
        self.assertNotIn(0x4001, set(OBJECT_ONLY_FLAG_NAMESPACE_RANGE))

        policy2, report2 = build_stage61_namespace_policy(
            ROOT, self.full_cfg, self.clean, self.stage60
        )
        self.assertEqual(policy2.mappings, self.policy.mappings)
        self.assertEqual(policy2.operand_overrides, self.policy.operand_overrides)
        self.assertEqual(report2, self.report)

    def test_strength_engine_system_flag_materializes_identity_and_native_mutation_fails_closed(
        self,
    ) -> None:
        materialized = self.full_cfg.materialize(0x09E00000, self.policy)
        expected = {
            0x081A48D0: bytes.fromhex("2b0508"),
            0x081A4914: bytes.fromhex("290508"),
        }
        for source, raw in expected.items():
            target = materialized.instruction_addresses[source]
            offset = target - materialized.payload_base
            self.assertEqual(
                materialized.payload[offset:offset + len(raw)], raw
            )

        mutated = bytearray(self.stage60)
        mutated[0x0805B654 - 0x08000000] ^= 0x01
        with self.assertRaisesRegex(
            Stage61NamespacePolicyError,
            "Strength engine system flag native ABI preimage不一致",
        ):
            build_stage61_namespace_policy(
                ROOT, self.full_cfg, self.clean, bytes(mutated)
            )

    def test_manifest_crosswalk_and_site_specific_mappings_are_semantic(self) -> None:
        self.assertEqual(self.policy.mappings["species"][143], 491)
        self.assertEqual(self.policy.mappings["species"][100], 223)
        self.assertEqual(self.policy.mappings["item"][182], 472)
        self.assertEqual(self.policy.mappings["item"][315], 546)
        self.assertEqual(self.policy.mappings["move"][53], 53)
        self.assertEqual(self.policy.mappings["map"][(1, 47)], (97, 47))
        self.assertNotIn((3, 8), self.policy.mappings["map"])
        self.assertEqual(self.policy.mappings["map"][(0, 0)], (0, 0))
        self.assertEqual(
            self.policy.mappings["trainer"],
            {
                170: 170,
                178: 4182,
                179: 4184,
                180: 4186,
                213: 4180,
                214: 4183,
                215: 4185,
                348: 348,
                355: 355,
            },
        )
        self.assertEqual(len(self.policy.operand_overrides), 348)
        self.assertEqual(len(self.report["special_argument_overrides"]), 138)
        species_arguments = [
            row
            for row in self.report["special_argument_overrides"]
            if row["semantic"] == "SPECIES_ID"
        ]
        self.assertTrue(species_arguments)
        self.assertTrue(any(row["source"] == 143 and row["target"] == 491
                            for row in species_arguments))

    def test_all_local_object_sites_are_resolved_by_map_context(self) -> None:
        plan = build_stage61_local_object_namespace_plan(
            ROOT, self.full_cfg, self.clean, self.stage60
        )
        report = plan.to_report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(plan.site_rows), 210)
        self.assertEqual(len(plan.operand_overrides), 210)
        self.assertEqual(report["existing_object_nonidentity_override_count"], 46)
        self.assertEqual(len(plan.missing_templates), 1)
        self.assertNotIn("local_object", self.policy.mappings)
        self.assertEqual(
            plan.operand_overrides[("script", 0x08163FFB, 1, "local_object")],
            8,
        )
        self.assertEqual(
            plan.operand_overrides[("script", 0x0816638F, 1, "local_object")],
            6,
        )
        self.assertEqual(
            plan.operand_overrides[("script", 0x08166392, 1, "local_object")],
            7,
        )
        missing = plan.missing_templates[0]
        self.assertEqual(missing.source_map, "RocketHideout_B4F")
        self.assertEqual(missing.source_script_label,
                         "RocketHideout_B4F_EventScript_SilphScope")
        self.assertEqual(missing.source_script_pointer, 0x081663AC)
        self.assertEqual((missing.target_group, missing.target_map), (97, 45))
        self.assertEqual((missing.target_index, missing.target_local_id), (6, 7))

    def test_missing_silph_scope_template_materializes_and_rebases_old_array(self) -> None:
        local_plan = build_stage61_local_object_namespace_plan(
            ROOT, self.full_cfg, self.clean, self.stage60
        )
        visibility_plan = build_stage61_object_visibility_namespace_plan(
            ROOT, self.full_cfg, self.clean, self.stage60
        )
        full_materialized = self.full_cfg.materialize(0x09E00000, self.policy)
        result = materialize_stage61_missing_object_templates(
            ROOT,
            local_plan,
            full_materialized,
            self.clean,
            self.stage60,
            0x09F10000,
            graphics_id_mapping={92: 92},
            visibility_flag_mapping=visibility_plan.source_to_target,
        )
        self.assertTrue(all(result.verification_assertions.values()))
        self.assertEqual(len(result.payload), 200)
        self.assertEqual(len(result.patches), 2)
        self.assertEqual(result.patches[0].expected, b"\x06")
        self.assertEqual(result.patches[0].replacement, b"\x07")

        clone_offset = result.object_array_address - result.payload_base + 6 * 24
        clone = result.payload[clone_offset:clone_offset + 24]
        self.assertEqual(clone[0], 7)
        self.assertEqual(clone[1], 92)
        self.assertEqual(struct.unpack_from("<I", clone, 16)[0],
                         result.script_address)
        self.assertEqual(
            struct.unpack_from("<H", clone, 20)[0],
            visibility_plan.source_to_target[0x37],
        )
        old_array = struct.unpack("<I", result.patches[1].expected)[0]
        self.assertEqual(
            result.rebase_object_address(old_array + 20),
            result.object_array_address + 20,
        )
        self.assertEqual(
            result.rebase_object_address(old_array + 5 * 24 + 16),
            result.object_array_address + 5 * 24 + 16,
        )
        self.assertIsNone(result.rebase_object_address(old_array - 1))

        with self.assertRaisesRegex(
            Stage61NamespacePolicyError, "graphics IDの明示mapping",
        ):
            materialize_stage61_missing_object_templates(
                ROOT,
                local_plan,
                full_materialized,
                self.clean,
                self.stage60,
                0x09F10000,
                graphics_id_mapping={},
                visibility_flag_mapping=visibility_plan.source_to_target,
            )

    def test_all_163_effects_have_machine_readable_classification_and_basis(self) -> None:
        rows = self.report["effect_approvals"]
        self.assertEqual(len(rows), 163)
        self.assertEqual(len({row["requirement"] for row in rows}), 163)
        self.assertEqual(
            Counter(row["class"] for row in rows),
            {
                "RELOCATED_SCRIPT_OPCODE": 69,
                "SPECIAL_CALL": 90,
                "STANDARD_SCRIPT_CALL": 4,
            },
        )
        replacements = [
            row for row in rows
            if row["approval_basis"] == "AUDITED_PROJECT_SEMANTIC_REPLACEMENT"
        ]
        self.assertEqual(
            [(row["requirement"], row["symbol"]) for row in replacements],
            [("SPECIAL:0083", "CalculatePlayerPartyCount")],
        )
        self.assertTrue(all(row.get("approval_basis") for row in rows))

    def test_object_visibility_uses_source_label_not_target_index(self) -> None:
        plan = build_stage61_object_visibility_namespace_plan(
            ROOT, self.full_cfg, self.clean, self.stage60
        )
        self.assertTrue(all(plan.assertions.values()))
        self.assertEqual(len(plan.owner_rows), 469)
        self.assertEqual(len(plan.patches), 469)
        self.assertEqual(len(plan.source_to_target), 151)

        persistent_visibility = {
            int(row["source_flag"])
            for row in plan.owner_rows
            if int(row["source_flag"]) != 0
        }
        script_flags = set(self.policy.mappings["flag"])
        object_only = persistent_visibility - script_flags
        self.assertEqual(len(persistent_visibility), 34)
        self.assertEqual(len(object_only), 27)
        self.assertEqual(
            {plan.source_to_target[value] for value in object_only},
            set(OBJECT_ONLY_FLAG_NAMESPACE_RANGE),
        )

        dream_eater = next(
            row for row in plan.owner_rows
            if row["source_label"] == "ViridianCity_EventScript_DreamEaterTutor"
        )
        self.assertEqual(dream_eater["source_index"], 0)
        self.assertEqual(dream_eater["target_index"], 8)
        route12_snorlax = next(
            row for row in plan.owner_rows
            if row["source_label"] == "Route12_EventScript_Snorlax"
        )
        self.assertEqual(route12_snorlax["source_index"], 4)
        self.assertEqual(route12_snorlax["target_index"], 14)
        self.assertEqual(route12_snorlax["target_flag_after"], 0x18D0)

        for patch in plan.patches:
            offset = patch.address - ROM_BASE
            self.assertEqual(
                self.stage60[offset:offset + len(patch.expected)], patch.expected
            )

    def test_topology_and_object_visibility_share_one_injective_flag_binding(self) -> None:
        topology = {
            **{source: 0x162D + source - 0x40 for source in range(0x40, 0x4E)},
            0x58: 0x163B,
            0x59: 0x163C,
            0x2D2: 0x163D,
            0x2D3: 0x163E,
        }
        plan = build_stage61_object_visibility_namespace_plan(
            ROOT, self.full_cfg, self.clean, self.stage60, topology
        )
        self.assertTrue(all(plan.assertions.values()))
        self.assertEqual(
            {source: plan.source_to_target[source] for source in (0x49, 0x4B, 0x58)},
            {source: topology[source] for source in (0x49, 0x4B, 0x58)},
        )
        self.assertEqual(
            Counter(row["mapping_basis"] for row in plan.owner_rows)[
                "SHARED_TOPOLOGY_FLAG_NAMESPACE"
            ],
            3,
        )
        targets = [
            plan.source_to_target[source]
            for source in {
                int(row["source_flag"]) for row in plan.owner_rows
                if int(row["source_flag"]) != 0
            }
        ]
        self.assertEqual(len(targets), len(set(targets)))

    def test_caller_visibility_inventory_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            Stage61NamespacePolicyError,
            "caller指定object visibility flag",
        ):
            build_stage61_namespace_policy(
                ROOT,
                self.full_cfg,
                self.clean,
                self.stage60,
                object_visibility_flag_ids=(0x1234,),
            )


class Stage61MultichoiceRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = CLEAN_PATH.read_bytes()
        cls.stage60 = STAGE60_PATH.read_bytes()
        cls.base = 0x09F00000
        cls.materialized = materialize_multichoice_runtime_contract(
            cls.clean, cls.stage60, cls.base
        )

    def test_preserves_stage60_rows_and_clones_clean_kanto_assets_exactly(self) -> None:
        result = self.materialized
        stock_offset = MULTICHOICE_TABLE_ADDRESS - ROM_BASE
        stock_size = MULTICHOICE_STOCK_COUNT * 8
        self.assertEqual(
            result.payload[:stock_size],
            self.stage60[stock_offset:stock_offset + stock_size],
        )
        self.assertEqual(result.source_to_target, MULTICHOICE_REMAP)
        self.assertEqual(len(result.asset_rows), 9)

        for source, target in MULTICHOICE_REMAP.items():
            clean_row_offset = stock_offset + source * 8
            source_list, count = struct.unpack_from(
                "<IB", self.clean, clean_row_offset
            )
            target_list, target_count = struct.unpack_from(
                "<IB", result.payload, target * 8
            )
            self.assertEqual(target_count, count)
            self.assertGreaterEqual(target_list, result.payload_base)
            list_offset = target_list - result.payload_base
            for index in range(count):
                source_text = struct.unpack_from(
                    "<I", self.clean, source_list - ROM_BASE + index * 8
                )[0]
                target_text = struct.unpack_from(
                    "<I", result.payload, list_offset + index * 8
                )[0]
                source_start = source_text - ROM_BASE
                source_end = self.clean.index(0xFF, source_start) + 1
                target_start = target_text - result.payload_base
                target_end = result.payload.index(0xFF, target_start) + 1
                self.assertEqual(
                    result.payload[target_start:target_end],
                    self.clean[source_start:source_end],
                )

    def test_patch_contract_and_output_are_deterministic(self) -> None:
        result = self.materialized
        self.assertEqual(len(result.patches), 6)
        table_patches = [
            patch for patch in result.patches
            if patch.role == "MULTICHOICE_TABLE_EXPANSION_LITERAL"
        ]
        operand_patches = [
            patch for patch in result.patches
            if patch.role == "MULTICHOICE_CLEAN_SCRIPT_OPERAND_REMAP"
        ]
        self.assertEqual(len(table_patches), 2)
        self.assertEqual(len(operand_patches), 4)
        for patch in result.patches:
            offset = patch.address - ROM_BASE
            self.assertEqual(
                self.stage60[offset:offset + len(patch.expected)], patch.expected
            )
        for patch in table_patches:
            self.assertEqual(patch.replacement, struct.pack("<I", self.base))
        self.assertEqual(
            {
                patch.expected[0]: patch.replacement[0]
                for patch in operand_patches
            },
            {57: 70, 58: 71, 59: 72, 60: 73},
        )
        again = materialize_multichoice_runtime_contract(
            self.clean, self.stage60, self.base
        )
        self.assertEqual(again, result)

    def test_literal_preimage_mismatch_fails_before_materialization(self) -> None:
        corrupted = bytearray(self.stage60)
        literal_offset = 0x0809C534 - ROM_BASE
        corrupted[literal_offset] ^= 1
        with self.assertRaisesRegex(
            Stage61NamespacePolicyError,
            "multichoice table literal preimage不一致",
        ):
            materialize_multichoice_runtime_contract(
                self.clean, bytes(corrupted), self.base
            )

    def test_ferry_branch_preimage_mismatch_fails_before_materialization(self) -> None:
        corrupted = bytearray(self.stage60)
        branch_offset = 0x08196546 - ROM_BASE + 20
        corrupted[branch_offset] ^= 1
        with self.assertRaisesRegex(
            Stage61NamespacePolicyError,
            "Sevii ferry choice branch SHA-256不一致",
        ):
            materialize_multichoice_runtime_contract(
                self.clean, bytes(corrupted), self.base
            )


if __name__ == "__main__":
    unittest.main()
