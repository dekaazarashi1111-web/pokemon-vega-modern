from __future__ import annotations

from collections import Counter
from dataclasses import replace
import hashlib
import struct
import unittest
from pathlib import Path

import tools.stage61_graphics_namespace as gfx


ROOT = Path(__file__).resolve().parents[1]
MATERIALIZE_ADDRESS = 0x09500000
SNORLAX_INFO_ADDRESS = 0x095F0000
GRAPHICS_TABLE_ADDRESS = 0x09510000

EXPECTED_MISMATCHED_IDS = (
    0, 49, 53, 63, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81,
    82, 83, 84, 85, 86, 87, 88, 98, 109, 110, 111, 112, 113,
    115, 116, 121, 125, 126, 128, 129, 130, 131, 132, 133, 134,
    139, 151,
)


class Stage61GraphicsNamespaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba").read_bytes()
        cls.plan = gfx.build_graphics_namespace_plan(ROOT)
        cls.materialized = cls.plan.materialize(MATERIALIZE_ADDRESS)

    def test_exact_inputs_inventory_and_complete_object_preimages(self) -> None:
        plan = self.plan
        self.assertEqual(plan.clean_rom_sha256, gfx.CLEAN_ROM_SHA256)
        self.assertEqual(plan.stage60_rom_sha256, gfx.STAGE60_ROM_SHA256)
        self.assertEqual(plan.canonical_importer_sha256,
                         gfx.CANONICAL_IMPORTER_SHA256)
        self.assertEqual(plan.canonical_maps_sha256, gfx.CANONICAL_MAPS_SHA256)
        self.assertEqual(plan.map_count, 253)
        self.assertEqual(len(plan.object_records), 1060)
        self.assertEqual(len(plan.used_graphics_ids), 106)
        self.assertEqual(
            hashlib.sha256(bytes(plan.used_graphics_ids)).hexdigest(),
            "c47a305c9050dd0c3b32040aa1d4d8cc22f9871523dcc4936dcb718be29aa631",
        )
        self.assertEqual(plan.mismatched_graphics_ids, EXPECTED_MISMATCHED_IDS)
        self.assertEqual(
            plan.graphics_id_remap,
            dict(zip(EXPECTED_MISMATCHED_IDS, range(152, 194))),
        )
        self.assertEqual(
            Counter(row.action for row in plan.object_records),
            {
                "KEEP_IDENTICAL_CLOSURE": 937,
                "REMAP_CLEAN_CLOSURE": 121,
                "PRESERVE_DYNAMIC_GRAPHICS_ID": 2,
            },
        )

        offsets = [row.record_offset for row in plan.object_records]
        self.assertEqual(len(set(offsets)), 1060)
        for row in plan.object_records:
            self.assertEqual(len(row.record_preimage), gfx.OBJECT_EVENT_SIZE)
            self.assertEqual(
                plan.stage60_rom[
                    row.record_offset:row.record_offset + gfx.OBJECT_EVENT_SIZE
                ],
                row.record_preimage,
            )
            self.assertEqual(row.record_preimage[1], row.source_graphics_id)
        self.assertEqual(
            hashlib.sha256(
                b"".join(row.record_preimage for row in plan.object_records)
            ).hexdigest(),
            "848e5251db66ea9926d2382ed516b996cb32a7d1129a617abab026c98353d2e3",
        )
        manifest = b"".join(
            struct.pack("<I", row.record_offset)
            + row.record_preimage
            + bytes((row.source_graphics_id, row.runtime_graphics_id))
            for row in plan.object_records
        )
        self.assertEqual(
            hashlib.sha256(manifest).hexdigest(),
            "f0c36555bb331df8930b1f00729ee77675c01dcc846e117913a56c1266cf4642",
        )

    def test_invisible_id_zero_is_fail_closed_cloned_and_dynamic_ids_are_kept(self) -> None:
        invisible = [
            row for row in self.plan.object_records
            if row.source_graphics_id == 0
        ]
        dynamic = [
            row for row in self.plan.object_records
            if row.source_graphics_id >= gfx.DYNAMIC_GRAPHICS_ID_START
        ]
        self.assertEqual(len(invisible), 15)
        self.assertTrue(all(row.record_preimage[9] == 76 for row in invisible))
        self.assertTrue(all(row.runtime_graphics_id == 152 for row in invisible))
        self.assertTrue(all(
            row.action == "REMAP_CLEAN_CLOSURE" for row in invisible
        ))
        self.assertEqual([row.source_graphics_id for row in dynamic], [240, 240])
        self.assertTrue(all(row.runtime_graphics_id == 240 for row in dynamic))
        self.assertEqual(
            self.plan.closure_signatures_clean[0].sha256,
            "bdef69347d7d7fef1ec629b5b9f90d860db507758088aede468787b6a75da278",
        )
        self.assertIn(
            "unresolved_stage60_closure",
            self.plan.closure_signatures_stage60[0].components,
        )
        self.assertNotIn(240, self.plan.closure_signatures_clean)

    def test_structural_closure_comparison_and_exact_manifest_hash(self) -> None:
        plan = self.plan
        compared = {
            value for value in plan.used_graphics_ids
            if value < gfx.DYNAMIC_GRAPHICS_ID_START
        }
        self.assertEqual(set(plan.closure_signatures_clean), compared)
        self.assertEqual(set(plan.closure_signatures_stage60), compared)
        actual_mismatch = {
            graphics_id for graphics_id in compared
            if plan.closure_signatures_clean[graphics_id].sha256
            != plan.closure_signatures_stage60[graphics_id].sha256
        }
        self.assertEqual(actual_mismatch, set(EXPECTED_MISMATCHED_IDS))
        self.assertEqual(
            plan.payload.source_closure_sha256,
            "7a43739bd5f9021028a74ce6e3f45585a9dd178e37d97994a3d59184a22ebb87",
        )
        self.assertEqual(
            plan.closure_signatures_clean[49].sha256,
            "297d5b563f2b3f49179e44f34b2c74f5e7c22a59a4166daa74ab1915d861eb13",
        )
        self.assertEqual(
            plan.closure_signatures_stage60[49].sha256,
            "7818406e075227e830643208cb999546c6f91bef56d6655fc835a38931b13a15",
        )
        required_components = {
            "info_scalars", "oam", "subsprites", "animations", "images",
            "affine_animations", "palettes",
        }
        for signature in plan.closure_signatures_clean.values():
            self.assertEqual(set(signature.components), required_components)

        # A pointer-only palette relocation is structurally identical.  The
        # signature records payload/tag/alias semantics, never source address.
        relocated = bytearray(self.clean)
        palette_table_offset = gfx.OBJECT_PALETTE_TABLE - gfx.GBA_BASE
        source_pointer, source_tag = struct.unpack_from(
            "<IH", relocated, palette_table_offset + 3 * 8
        )
        self.assertEqual(source_tag, 0x1106)
        source_offset = source_pointer - gfx.GBA_BASE
        relocated_offset = len(relocated) - 0x100
        relocated[relocated_offset:relocated_offset + 32] = \
            relocated[source_offset:source_offset + 32]
        struct.pack_into(
            "<I", relocated, palette_table_offset + 3 * 8,
            gfx.GBA_BASE + relocated_offset,
        )
        self.assertEqual(
            gfx.extract_graphics_closure_signature(bytes(relocated), 16).sha256,
            plan.closure_signatures_clean[16].sha256,
        )

    def test_object_patch_plan_changes_only_the_121_graphics_bytes(self) -> None:
        plan = self.plan
        patches = plan.object_patches
        self.assertEqual(len(patches), 121)
        self.assertEqual(len({patch.offset for patch in patches}), 121)
        patch_manifest = b"".join(
            struct.pack("<I", patch.offset) + patch.expected + patch.replacement
            for patch in patches
        )
        self.assertEqual(
            hashlib.sha256(patch_manifest).hexdigest(),
            "0d29ebe56bcba640df0e0835aee820cce158bbec3cc6bb1af609a316b83e75fa",
        )

        output = plan.apply_object_patches(plan.stage60_rom)
        self.assertEqual(
            hashlib.sha256(output).hexdigest(),
            "6d8021bd5c6253c93546263a3affb1c661dd0785144cb629d3a99b53ad47cf48",
        )
        for row in plan.object_records:
            expected = bytearray(row.record_preimage)
            expected[1] = row.runtime_graphics_id
            self.assertEqual(
                output[row.record_offset:row.record_offset + gfx.OBJECT_EVENT_SIZE],
                bytes(expected),
            )

        wrong = bytearray(plan.stage60_rom)
        wrong[0] ^= 1
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "exact Stage60"):
            plan.apply_object_patches(bytes(wrong))

    def test_static_allocator_is_confined_below_reserved_and_dynamic_ids(self) -> None:
        full = gfx.allocate_graphics_ids(range(87))
        self.assertEqual(tuple(full.values()), tuple(range(152, 239)))
        self.assertNotIn(239, full.values())
        self.assertTrue(all(value < 240 for value in full.values()))
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "exhausted"):
            gfx.allocate_graphics_ids(range(88))
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "proven-free"):
            gfx.allocate_graphics_ids([49], allocation_start=151)
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "proven-free"):
            gfx.allocate_graphics_ids([49], allocation_end=239,
                                      reserved_ids=())
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "boundary"):
            gfx.allocate_graphics_ids([49], dynamic_start=241)
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "outside u8"):
            gfx.allocate_graphics_ids([49], reserved_ids=(-1,))
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "stock static"):
            gfx.allocate_graphics_ids([152])

    def test_payload_materialization_preserves_exact_bytes_aliases_and_fixups(self) -> None:
        plan = self.plan
        materialized = self.materialized
        self.assertEqual(len(plan.payload.nodes), 350)
        self.assertEqual(len(materialized.payload), 56604)
        self.assertEqual(materialized.fixup_count, 672)
        self.assertEqual(
            materialized.sha256,
            "6047ea39a7ae18149f09394e93a9d30c398ef11145bd0c6aaa09ab39b98cbdfc",
        )

        source_ranges: list[tuple[int, int]] = []
        roles: set[str] = set()
        target_use_count: Counter[str] = Counter()
        for node in plan.payload.nodes:
            roles.update(role.split("::", 1)[0] for role in node.roles)
            start = materialized.node_offsets[node.key]
            self.assertEqual(start % node.alignment, 0)
            emitted = bytearray(
                materialized.payload[start:start + len(node.raw)]
            )
            for fixup in node.fixups:
                target_use_count[fixup.target_key] += 1
                self.assertIn(fixup.target_key, materialized.node_addresses)
                self.assertEqual(
                    struct.unpack_from("<I", emitted, fixup.offset)[0],
                    materialized.node_addresses[fixup.target_key]
                    + fixup.target_delta,
                )
                emitted[fixup.offset:fixup.offset + 4] = \
                    node.raw[fixup.offset:fixup.offset + 4]
            self.assertEqual(bytes(emitted), node.raw)

            if node.source_address is not None:
                offset = node.source_address - gfx.GBA_BASE
                source = self.clean[offset:offset + len(node.raw)]
                if any(role.startswith("graphics_info::") for role in node.roles):
                    actual = bytearray(node.raw)
                    actual[2:6] = source[2:6]
                    self.assertEqual(bytes(actual), source)
                else:
                    self.assertEqual(node.raw, source)
                source_ranges.append(
                    (node.source_address, node.source_address + len(node.raw))
                )

        self.assertEqual(
            roles,
            {
                "graphics_info", "image_table", "image_data", "oam",
                "subsprite_table", "subsprite_data", "animation_table",
                "animation_commands", "affine_table", "affine_commands",
                "object_palette", "extended_object_palette_table",
            },
        )
        source_ranges.sort()
        self.assertTrue(all(
            previous_end <= current_start
            for (_, previous_end), (current_start, _) in zip(
                source_ranges, source_ranges[1:]
            )
        ))
        self.assertGreater(sum(count > 1 for count in target_use_count.values()), 50)

        # IDs 49 and 53 share the exact standard animation pointer table.
        def info_pointer(source_id: int, field_offset: int) -> int:
            info_address = materialized.graphics_info_addresses[source_id]
            offset = info_address - materialized.load_address + field_offset
            return struct.unpack_from("<I", materialized.payload, offset)[0]

        self.assertEqual(info_pointer(49, 0x18), info_pointer(53, 0x18))
        self.assertNotEqual(info_pointer(49, 0x18), 0x083673F0)

    def test_palette_table_is_extended_with_private_tags_and_exact_data(self) -> None:
        plan = self.plan
        materialized = self.materialized
        expected_remap = {
            0x1100: 0x7000,
            0x1102: 0x7001,
            0x1103: 0x7002,
            0x1104: 0x7003,
            0x1105: 0x7004,
            0x1106: 0x7005,
            0x1115: 0x7006,
        }
        self.assertEqual(plan.payload.palette_tag_remap, expected_remap)
        self.assertEqual(materialized.palette_tag_remap, expected_remap)
        table_node = next(
            node for node in plan.payload.nodes
            if node.key == plan.payload.palette_table_node
        )
        self.assertEqual(len(table_node.raw), (18 + 7 + 1) * 8)
        table_offset = materialized.node_offsets[table_node.key]
        table = materialized.payload[
            table_offset:table_offset + len(table_node.raw)
        ]
        old_offset = gfx.OBJECT_PALETTE_TABLE - gfx.GBA_BASE
        self.assertEqual(
            table[:18 * 8],
            plan.stage60_rom[old_offset:old_offset + 18 * 8],
        )

        clean_by_tag: dict[int, tuple[int, bytes]] = {}
        for index in range(18):
            pointer, tag = struct.unpack_from(
                "<IH", self.clean, old_offset + index * 8
            )
            palette_offset = pointer - gfx.GBA_BASE
            clean_by_tag[tag] = (
                pointer, self.clean[palette_offset:palette_offset + 32]
            )
        for index, (source_tag, runtime_tag) in enumerate(expected_remap.items()):
            pointer, tag, padding = struct.unpack_from(
                "<IHH", table, (18 + index) * 8
            )
            self.assertEqual((tag, padding), (runtime_tag, 0))
            self.assertTrue(
                materialized.load_address <= pointer
                < materialized.load_address + len(materialized.payload)
            )
            payload_offset = pointer - materialized.load_address
            self.assertEqual(
                materialized.payload[payload_offset:payload_offset + 32],
                clean_by_tag[source_tag][1],
            )
        self.assertEqual(
            table[-8:], struct.pack("<IHH", 0, gfx.OBJECT_PALETTE_SENTINEL, 0)
        )

        old_pointer = struct.pack("<I", gfx.OBJECT_PALETTE_TABLE)
        occurrences: list[int] = []
        cursor = 0
        while True:
            offset = plan.stage60_rom.find(old_pointer, cursor)
            if offset < 0:
                break
            occurrences.append(offset)
            cursor = offset + 1
        self.assertEqual(
            occurrences,
            [site - gfx.GBA_BASE for site in gfx.OBJECT_PALETTE_POINTER_SITES],
        )
        self.assertEqual(len(materialized.palette_pointer_patches), 3)
        for patch in materialized.palette_pointer_patches:
            self.assertEqual(
                plan.stage60_rom[patch.offset:patch.offset + 4], patch.expected
            )
            self.assertEqual(
                patch.replacement,
                struct.pack("<I", materialized.palette_table_address),
            )

    def test_palette_allocation_collisions_and_nonprivate_ranges_are_rejected(self) -> None:
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "exhausted"):
            gfx.build_graphics_namespace_plan(
                ROOT,
                reserved_palette_tags=range(
                    gfx.CLONE_PALETTE_TAG_START,
                    gfx.CLONE_PALETTE_TAG_END + 1,
                ),
            )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "private range"):
            gfx.build_graphics_namespace_plan(ROOT, palette_tag_start=0x6FFF)

    def test_extended_table_and_all_live_consumer_patches_are_complete(self) -> None:
        plan = self.plan
        materialized = self.materialized
        table = plan.build_extended_graphics_table(
            materialized,
            reserved_graphics_pointers={239: SNORLAX_INFO_ADDRESS},
        )
        self.assertEqual(len(table), 240 * 4)
        entries = struct.unpack("<240I", table)
        self.assertEqual(entries[:152], plan.stage60_graphics_pointers)
        for source_id, runtime_id in plan.graphics_id_remap.items():
            self.assertEqual(
                entries[runtime_id], materialized.graphics_info_addresses[source_id]
            )
        fallback = plan.stage60_graphics_pointers[16]
        self.assertEqual(entries[194:239], (fallback,) * 45)
        self.assertEqual(entries[239], SNORLAX_INFO_ADDRESS)

        pointer_patches = plan.graphics_table_pointer_patches(
            GRAPHICS_TABLE_ADDRESS
        )
        self.assertEqual(
            [patch.offset for patch in pointer_patches],
            [site - gfx.GBA_BASE for site in gfx.OBJECT_GRAPHICS_POINTER_SITES],
        )
        self.assertEqual(len(plan.graphics_table_installation_patches(
            GRAPHICS_TABLE_ADDRESS
        )), 4)
        for patch in pointer_patches:
            self.assertEqual(
                plan.stage60_rom[patch.offset:patch.offset + 4], patch.expected
            )
            self.assertEqual(patch.expected, struct.pack("<I", gfx.OBJECT_GRAPHICS_TABLE))
            self.assertEqual(patch.replacement, struct.pack("<I", GRAPHICS_TABLE_ADDRESS))
        limit = plan.graphics_static_limit_patch()
        self.assertEqual(limit.offset, 0x5EBA0)
        self.assertEqual(limit.expected.hex(), "9729")
        self.assertEqual(limit.replacement.hex(), "ef29")

        # The expanded-ROM sites are proven consumers: the first is a fallback
        # literal used by three ldr instructions, the second is bank zero read
        # through the pointer at 0x090DF0A4.
        stage = plan.stage60_rom
        self.assertEqual(stage[0x10DF03E:0x10DF044].hex(), "194a9b009b58")
        self.assertEqual(struct.unpack_from("<I", stage, 0x10DF0A4)[0], 0x09163828)
        self.assertEqual(struct.unpack_from("<I", stage, 0x1163828)[0],
                         gfx.OBJECT_GRAPHICS_TABLE)
        self.assertEqual(struct.unpack_from("<I", stage, 0x10DF0B0)[0],
                         gfx.OBJECT_GRAPHICS_TABLE)

    def test_table_collisions_bad_reservations_and_wrong_materialization_fail(self) -> None:
        plan = self.plan
        materialized = self.materialized
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "missing"):
            plan.build_extended_graphics_table(
                materialized, reserved_graphics_pointers={}
            )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "extra"):
            plan.build_extended_graphics_table(
                materialized,
                reserved_graphics_pointers={
                    238: SNORLAX_INFO_ADDRESS,
                    239: SNORLAX_INFO_ADDRESS,
                },
            )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "invalid"):
            plan.build_extended_graphics_table(
                materialized, reserved_graphics_pointers={239: 0x07000000}
            )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "invalid"):
            plan.build_extended_graphics_table(
                materialized, reserved_graphics_pointers={239: 0x09FFFFFC}
            )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "dynamic ID 240"):
            plan.build_extended_graphics_table(
                materialized,
                reserved_graphics_pointers={239: SNORLAX_INFO_ADDRESS},
                entry_count=241,
            )
        malicious = replace(plan, graphics_id_remap={49: 151})
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "proven-free"):
            malicious.build_extended_graphics_table(
                materialized,
                reserved_graphics_pointers={239: SNORLAX_INFO_ADDRESS},
            )
        wrong_materialized = replace(materialized, graphics_info_addresses={})
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "missing"):
            plan.build_extended_graphics_table(
                wrong_materialized,
                reserved_graphics_pointers={239: SNORLAX_INFO_ADDRESS},
            )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "invalid"):
            plan.graphics_table_pointer_patches(0x09510002)
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "invalid"):
            plan.graphics_table_pointer_patches(0x09FFFFFC)

    def test_unresolved_or_out_of_rom_pointers_are_rejected(self) -> None:
        bad = bytearray(self.clean)
        struct.pack_into(
            "<I", bad,
            gfx.OBJECT_GRAPHICS_TABLE - gfx.GBA_BASE + 49 * 4,
            0x07000000,
        )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "outside image"):
            gfx.extract_graphics_closure_signature(bytes(bad), 49)

        root_node = gfx.PayloadNode(
            key="root",
            raw=bytes(4),
            alignment=4,
            source_address=None,
            roles=("synthetic_test",),
            fixups=(gfx.PayloadFixup(0, "missing"),),
        )
        unresolved = gfx.RelocatableGraphicsPayload(
            nodes=(root_node,),
            graphics_info_nodes={},
            palette_table_node="root",
            palette_tag_remap={},
            source_closure_sha256="0" * 64,
        )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "unresolved"):
            unresolved.materialize(MATERIALIZE_ADDRESS)

        target_node = gfx.PayloadNode(
            key="target",
            raw=b"\xAA",
            alignment=1,
            source_address=None,
            roles=("synthetic_target",),
        )
        bad_delta = replace(
            unresolved,
            nodes=(
                replace(root_node, fixups=(gfx.PayloadFixup(0, "target", 1),)),
                target_node,
            ),
        )
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "target delta"):
            bad_delta.materialize(MATERIALIZE_ADDRESS)
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "word-aligned"):
            self.plan.materialize(MATERIALIZE_ADDRESS + 2)
        with self.assertRaisesRegex(gfx.GraphicsNamespaceError, "outside 32 MiB"):
            self.plan.materialize(0x09FFF000)


if __name__ == "__main__":
    unittest.main()
