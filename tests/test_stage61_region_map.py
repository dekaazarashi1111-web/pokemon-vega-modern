from __future__ import annotations

import importlib.util
import hashlib
from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/stage61_region_map.py"
SPEC = importlib.util.spec_from_file_location("stage61_region_map", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
REGION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REGION
SPEC.loader.exec_module(REGION)


def decode_thumb_bl(source: int, encoded: bytes) -> int:
    high, low = struct.unpack("<HH", encoded)
    value = ((high & 0x7FF) << 11) | (low & 0x7FF)
    if value & (1 << 21):
        value -= 1 << 22
    return source + 4 + value * 2


class Stage61RegionMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = REGION.build_region_map_plan(ROOT)

    def test_exact_inputs_and_all_53_sections_are_resolved(self) -> None:
        self.assertEqual(len(self.plan.sections), 53)
        self.assertEqual(
            [row.runtime_id for row in self.plan.sections], list(range(53))
        )
        self.assertEqual(self.plan.sections[0].source_id, 88)
        self.assertEqual(self.plan.sections[41].source_id, 131)
        self.assertEqual(self.plan.sections[52].source_id, 142)
        self.assertTrue(
            all(
                row.destination_group in REGION.IMPORTED_KANTO_GROUPS
                for row in self.plan.sections
            )
        )
        destinations = bytes(
            value
            for row in self.plan.sections
            for value in (row.destination_group, row.destination_map)
        )
        self.assertEqual(
            hashlib.sha256(destinations).hexdigest(),
            "7291a87efbcc07aa2e3ece6eb27e193960da2a24e911b6c49931ed1c8ffa36e8",
        )

    def test_clean_grid_is_translated_without_runtime_namespace_leaks(self) -> None:
        grid = self.plan.payload("kanto_region_grid").data
        self.assertEqual(len(grid), 2 * 15 * 22)
        values = set(grid)
        self.assertTrue(values <= set(range(53)) | {REGION.MAPSEC_NONE})
        # Pallet, Route 12 and both Diglett's Cave icons use project IDs.
        map_layer = grid[: 15 * 22]
        dungeon_layer = grid[15 * 22 :]
        self.assertEqual(map_layer[11 * 22 + 4], 0)
        self.assertEqual(map_layer[9 * 22 + 18], 22)
        self.assertEqual(dungeon_layer[5 * 22 + 4], 41)
        self.assertEqual(dungeon_layer[9 * 22 + 15], 41)
        # Source-only Route 4/10 Pokémon Center sections are normalized to the
        # project Route 4/10 identities rather than leaking IDs 99/100.
        self.assertEqual(map_layer[3 * 22 + 8], 14)
        self.assertEqual(map_layer[3 * 22 + 18], 20)
        self.assertEqual(
            hashlib.sha256(grid).hexdigest(),
            "7d41f04c1c3a2de846a19404aae9729a0ce8c65b8fe25c4c68638260617f8ed5",
        )

    def test_position_table_has_safe_source_semantic_anchors(self) -> None:
        positions = self.plan.payload("kanto_section_positions").data
        self.assertEqual(len(positions), 53 * 6)
        rows = [struct.unpack_from("<BBBBBB", positions, i * 6) for i in range(53)]
        self.assertEqual(rows[22], (18, 7, 1, 5, 18, 9))
        self.assertEqual(rows[41][4:], (15, 9))
        self.assertEqual(rows[42][4:], (2, 4))
        self.assertEqual(rows[50][4:], (18, 6))
        for _, _, _, _, anchor_x, anchor_y in rows:
            self.assertLess(anchor_x, 22)
            self.assertLess(anchor_y, 15)
        self.assertEqual(
            hashlib.sha256(positions).hexdigest(),
            "ddbc20c663a8c4bfd674afa66dd68d558bfd02816686734a111989b02962438c",
        )

    def test_fly_records_use_imported_physical_maps_and_exact_landing_coords(self) -> None:
        fly = self.plan.payload("kanto_fly_records").data
        self.assertEqual(len(fly), 53 * 6)
        rows = [struct.unpack_from("<BBBBBB", fly, i * 6) for i in range(53)]
        self.assertEqual(rows[0], (96, 0, 6, 8, 1, 0))
        self.assertEqual(rows[5], (96, 5, 15, 7, 1, 5))
        self.assertEqual(rows[10], (96, 10, 24, 39, 1, 10))
        self.assertEqual(rows[22][:2], (96, 23))
        self.assertEqual(rows[41][:2], (97, 37))
        self.assertEqual(sum(row[4] for row in rows), 11)
        self.assertEqual(
            hashlib.sha256(fly).hexdigest(),
            "848070f9bb7072b0001f4f0d5b1221513e163781f987dda3cdff6ae210be77dd",
        )
        legacy = self.plan.payload("kanto_fly_destinations_legacy").data
        self.assertEqual(len(legacy), 53 * 3)
        self.assertTrue(all(legacy[i * 3 + 2] == 0 for i in range(53)))

    def test_visit_flags_require_a_distinct_project_namespace(self) -> None:
        requirements = self.plan.visit_flag_requirements
        self.assertEqual(len(requirements), 28)
        self.assertEqual(
            [row.runtime_id for row in requirements],
            [*range(11), *range(36, 53)],
        )
        self.assertEqual(requirements[0].source_flag, 0x0890)
        self.assertEqual(requirements[10].source_flag, 0x089A)
        self.assertEqual(requirements[11].source_flag, 0x08A4)
        self.assertEqual(requirements[-1].source_flag, 0x08B4)
        self.assertEqual(
            requirements[15].source_symbol,
            "FLAG_WORLD_MAP_UNDERGROUND_PATH_EAST_WEST_TUNNEL",
        )

        allocated = {
            row.runtime_id: 0x0900 + index
            for index, row in enumerate(requirements)
        }
        payload = self.plan.materialize_visit_flag_payload(allocated)
        self.assertEqual(payload.macro, "STAGE61_KANTO_VISIT_FLAGS")
        self.assertEqual(len(payload.data), 53 * 2)
        values = struct.unpack("<53H", payload.data)
        self.assertEqual(values[0], 0x0900)
        self.assertEqual(values[10], 0x090A)
        self.assertEqual(values[11:36], (0xFFFF,) * 25)
        self.assertEqual(values[36], 0x090B)
        self.assertEqual(values[52], 0x091B)

        legacy_alias = {
            row.runtime_id: row.source_flag for row in requirements
        }
        with self.assertRaisesRegex(
            REGION.RegionMapPlanError, "0x0900|alias"
        ):
            self.plan.materialize_visit_flag_payload(legacy_alias)

    def test_patch_preimages_cover_every_normal_town_map_consumer_boundary(self) -> None:
        sites = {row.name: row for row in self.plan.patches}
        expected = {
            "region_map_gfx_decompress": (0x080C14F2, "36f0edf9"),
            "region_map_tilemap_decompress": (0x080C153A, "06f1a9fa"),
            "get_mapsec_type": (0x080C47C0, "00b50006000e5838"),
            "get_dungeon_mapsec_type": (0x080C4A5C, "00b50006000e7e38"),
            "get_player_position_on_region_map_overrides": (
                0x080C4F24,
                "30b5fff7ddfe0004",
            ),
            "get_selected_map_section": (
                0x080C5348,
                "30b50006000e051c09060c0e1204120c",
            ),
            "set_fly_warp_destination": (0x080C6460, "30b5000408494018"),
        }
        self.assertEqual(set(sites), set(expected))
        for name, (address, preimage) in expected.items():
            self.assertEqual(sites[name].address, address)
            self.assertEqual(sites[name].expected.hex(), preimage)

    def test_stock_trampolines_preserve_tohoku_and_relocate_internal_bl(self) -> None:
        address = 0x09100000
        specs = {row.name: row for row in self.plan.trampolines}
        for index, spec in enumerate(self.plan.trampolines):
            payload = REGION.materialize_trampoline(spec, address + index * 0x20)
            if spec.relocated_bl_offset is None:
                if spec.preserve_four_args:
                    self.assertEqual(len(payload), 32)
                    self.assertEqual(
                        struct.unpack_from("<6H", payload, 16),
                        (0xB410, 0x4C02, 0x46A4, 0xBC10, 0x4760, 0x46C0),
                    )
                    self.assertEqual(
                        struct.unpack_from("<I", payload, 28)[0],
                        spec.resume_address | 1,
                    )
                else:
                    self.assertEqual(len(payload), 16)
                    self.assertEqual(
                        struct.unpack_from("<H", payload, 8)[0], 0x4B00
                    )
                    self.assertEqual(
                        struct.unpack_from("<H", payload, 10)[0], 0x4718
                    )
                    self.assertEqual(
                        struct.unpack_from("<I", payload, 12)[0],
                        spec.resume_address | 1,
                    )
        player = specs["stock_get_player_position"]
        player_address = address + list(specs).index(player.name) * 0x20
        payload = REGION.materialize_trampoline(player, player_address)
        self.assertEqual(len(payload), 24)
        self.assertEqual(
            decode_thumb_bl(player_address + 2, payload[2:6]), player_address + 12
        )
        self.assertEqual(struct.unpack_from("<HH", payload, 8), (0x4B02, 0x4718))
        self.assertEqual(struct.unpack_from("<HH", payload, 12), (0x4B00, 0x4718))
        self.assertEqual(struct.unpack_from("<I", payload, 16)[0], 0x080C4CE5)
        self.assertEqual(
            struct.unpack_from("<I", payload, 20)[0], player.resume_address | 1
        )

        # A near allocation retains the compact relocated BL form.
        near_address = 0x08100000
        near = REGION.materialize_trampoline(player, near_address)
        self.assertEqual(len(near), 16)
        self.assertEqual(
            decode_thumb_bl(near_address + 2, near[2:6]), 0x080C4CE4
        )

    def test_clean_kanto_visual_payload_sizes_are_exact(self) -> None:
        gfx = self.plan.payload("kanto_region_gfx_lz").data
        tilemap = self.plan.payload("kanto_region_tilemap_lz").data
        self.assertEqual(len(gfx), 3347)
        self.assertEqual(int.from_bytes(gfx[1:4], "little"), 10240)
        self.assertEqual(len(tilemap), 605)
        self.assertEqual(int.from_bytes(tilemap[1:4], "little"), 1200)

    def test_source_crosswalk_and_cfru_roamer_tables_are_total(self) -> None:
        source = self.plan.payload("kanto_source_section_ids").data
        self.assertEqual(len(source), 53)
        self.assertEqual(list(source[:11]), list(range(88, 99)))
        self.assertEqual(list(source[11:]), list(range(101, 143)))

        corners = self.plan.payload("cfru_safe_roamer_corners").data
        dimensions = self.plan.payload("cfru_safe_roamer_dimensions").data
        self.assertEqual(len(corners), 256 * 4)
        self.assertEqual(len(dimensions), 256 * 4)
        stage60 = (ROOT / "build/stages/60_wild_species_root_repair.gba").read_bytes()
        for payload, address in (
            (corners, REGION.CFRU_STOCK_MAP_SECTION_CORNERS),
            (dimensions, REGION.CFRU_STOCK_MAP_SECTION_DIMENSIONS),
        ):
            offset = address - REGION.ROM_BASE
            self.assertEqual(
                payload[: REGION.CFRU_STOCK_MAP_SECTION_COUNT * 4],
                stage60[offset : offset + REGION.CFRU_STOCK_MAP_SECTION_COUNT * 4],
            )
        # Project Route 12 (22) wraps to u8 row 190 after subtracting 88.
        wrapped = (22 - 88) & 0xFF
        self.assertEqual(struct.unpack_from("<HH", corners, wrapped * 4), (18, 7))
        self.assertEqual(
            struct.unpack_from("<HH", dimensions, wrapped * 4), (1, 5)
        )
        # Every otherwise-unused byte index remains a bounded zero row.
        self.assertEqual(corners[109 * 4 : 168 * 4], bytes((168 - 109) * 4))


if __name__ == "__main__":
    unittest.main()
