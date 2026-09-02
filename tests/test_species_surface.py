#!/usr/bin/env python3
"""T09 Species surfaceと孵化QOLの焦点試験。"""

from __future__ import annotations

import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.build_species_surface import (
    ARTIFACTS,
    SPECIES_PICTURE_BOUND_THUNK_CAVE,
    build_model,
    check,
    thumb_bl,
)

ROOT = Path(__file__).resolve().parents[1]


class SpeciesSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts, cls.metadata, cls.rom = build_model(ROOT)
        cls.species = json.loads((ROOT / "generated/engine/species/species_port.json").read_text())

    def test_required_outputs_and_table_bounds(self) -> None:
        self.assertEqual(set(self.artifacts), set(ARTIFACTS))
        sizes = {
            "front.bin": 1621 * 8, "back.bin": 1621 * 8,
            "icon.bin": 1621 * 4, "icon_palette.bin": 1621,
            "cry.bin": 1621 * 12, "dex_entries.bin": 1621 * 28,
            "national_dex.bin": 1621 * 2,
        }
        for name, size in sizes.items():
            self.assertEqual(len(self.artifacts[f"generated/engine/species_assets/{name}"]), size)
        self.assertEqual(len(self.artifacts["generated/engine/evolutions/evolutions.bin"]), 1621 * 128)
        self.assertEqual(len(self.artifacts["generated/engine/learnsets/tmhm.bin"]), 1621 * 16)
        self.assertEqual(len(self.artifacts["generated/engine/learnsets/tutor.bin"]), 1621 * 16)

    def test_vega_prefix_is_lossless_and_reserved_egg_caterpie_rows_are_displayable(self) -> None:
        stage = (ROOT / "build/stages/07_species.gba").read_bytes()
        front = self.artifacts["generated/engine/species_assets/front.bin"]
        old_root = struct.unpack_from("<I", stage, 0x128)[0] - 0x08000000
        self.assertEqual(front[:412 * 8], stage[old_root:old_root + 412 * 8])
        for species_id in (412, 649):
            for name, stride in (("front", 8), ("back", 8), ("icon", 4), ("footprint", 4),
                                 ("cry", 12), ("dex_entries", 28)):
                row = self.artifacts[f"generated/engine/species_assets/{name}.bin"][
                    species_id * stride:(species_id + 1) * stride
                ]
                self.assertNotEqual(row, bytes(stride), f"{name}:{species_id}")
        fixture = self.species["first_appended_fixture"]
        self.assertEqual(fixture["canonical_id"], 413)
        self.assertEqual(fixture["dpe_id"], 11)
        self.assertEqual(self.species["runtime_reservation"]["canonical_id"], 412)
        self.assertEqual(self.species["runtime_reservation"]["displaced_canonical_id"], 649)

    def test_evolutions_are_canonical_and_form_explicit(self) -> None:
        model = json.loads(self.artifacts["generated/engine/evolutions/evolutions.json"])
        self.assertEqual(model["status"], "PASS")
        self.assertGreater(model["nonzero_rows"], 600)
        for row in model["rows"]:
            self.assertLess(row["from_id"], 1621)
            self.assertLess(row["target_id"], 1621)
            self.assertIn("from_form_key", row)
            self.assertIn("target_form_key", row)
        self.assertTrue(any(row["from_id"] >= 412 and row["target_id"] < 412 for row in model["rows"]))
        v2 = json.loads(self.artifacts["generated/engine/evolutions/v2_normalized.json"])
        self.assertEqual(v2["source_rows"], 553)
        self.assertEqual(v2["semantic_duplicates_removed"], 43)
        self.assertTrue(all(isinstance(row["from_national_dex"], int) for row in v2["rows"]))

    def test_stage_roots_and_cry_adapter_are_installed(self) -> None:
        runtime_sites = {
            row["site"] for row in self.metadata["runtime"]["patches"]
        }
        for key, row in self.metadata["repoints"].items():
            sites = row.get("sites", [row.get("site")])
            self.assertTrue(sites, key)
            for site in sites:
                if site in runtime_sites:
                    continue
                expected = row["old"] if row.get("applied") is False else row["new"]
                self.assertEqual(struct.unpack_from("<I", self.rom, site)[0], expected)
        self.assertGreater(self.metadata["repoints"]["evolution_runtime"]["count"], 0)
        old = struct.pack("<I", self.metadata["repoints"]["evolution_runtime"]["old"])
        self.assertFalse(any(self.rom[index:index + 4] == old
                             for index in range(0, len(self.rom) - 3, 4)))
        self.assertEqual(self.rom[0x429F4:0x429FC].hex(), "0130704700bf00bf")
        self.assertGreater(self.metadata["allocation"]["free"], 0)

    def test_all_level_up_rows_use_one_three_byte_abi(self) -> None:
        model = json.loads(self.artifacts["generated/engine/learnsets/learnsets.json"])
        level = model["level_up"]
        self.assertEqual(level["format"], "U16_MOVE_U8_LEVEL")
        self.assertEqual(level["stride"], 3)
        self.assertEqual(level["converted_vega_rows"], 412)
        self.assertEqual(level["translated_dpe_rows"], 1209)
        pointers = self.artifacts["generated/engine/learnsets/level_up_pointers.bin"]
        data = self.artifacts["generated/engine/learnsets/level_up_data.bin"]
        base = self.metadata["repoints"]["level_up"]["new"]
        data_base = next(
            row["address"] for row in self.metadata["allocation"]["entries"]
            if row["name"] == "level_up_data"
        )
        self.assertEqual(len(pointers), 1621 * 4)
        self.assertEqual(base, next(
            row["address"] for row in self.metadata["allocation"]["entries"]
            if row["name"] == "level_up_pointers"
        ))
        for species in range(1621):
            address = struct.unpack_from("<I", pointers, species * 4)[0]
            cursor = address - data_base
            self.assertGreaterEqual(cursor, 0)
            for _ in range(256):
                move = struct.unpack_from("<H", data, cursor)[0]
                move_level = data[cursor + 2]
                cursor += 3
                if move == 0 and move_level == 0xFF:
                    break
            else:
                self.fail(f"unterminated canonical learnset: {species}")

    def test_cfru_learn_hooks_names_and_form_namespace_are_live(self) -> None:
        for row in self.metadata["learn_move_hooks"]:
            site = row["site"]
            self.assertEqual(self.rom[site:site + 8].hex(), row["replacement_hex"])
            self.assertEqual(struct.unpack_from("<I", self.rom, site + 4)[0], row["target"])
        names = self.artifacts["generated/engine/species/species_names_legacy.bin"]
        canonical = (ROOT / "generated/engine/species/species_names.bin").read_bytes()
        self.assertEqual(len(names), 1621 * 8)
        for species in range(1621):
            canonical_row = canonical[species * 11:(species + 1) * 11]
            visible = canonical_row.split(b"\xFF", 1)[0]
            compatibility_row = names[species * 8:(species + 1) * 8]
            self.assertEqual(compatibility_row[:len(visible)], visible)
            self.assertEqual(compatibility_row[len(visible):], b"\xFF" * (8 - len(visible)))
        self.assertEqual(self.metadata["repoints"]["species_names_legacy"]["count"], 40)
        self.assertEqual(self.metadata["repoints"]["species_names_legacy"]["new_stride"], 8)
        self.assertEqual(
            struct.unpack_from("<I", self.rom, 0x4346C)[0],
            self.metadata["repoints"]["level_up"]["new"],
        )
        native = self.metadata["repoints"]["level_up"]
        self.assertFalse(native["applied"])
        self.assertTrue(native["legacy_root_preserved"])
        self.assertEqual(
            struct.unpack_from("<I", self.rom, native["site"])[0],
            native["old"],
        )
        form_namespace = struct.pack(
            "<III", (-1322) & 0xFFFFFFFF, (-1374) & 0xFFFFFFFF, 1374,
        )
        self.assertEqual(self.rom.count(form_namespace), 1)

    def test_six_glyph_names_and_all_stock_consumers_are_closed(self) -> None:
        inventory = json.loads(self.artifacts[
            "generated/engine/species/species_name_consumers.json"
        ])
        names = inventory["name_table"]
        self.assertEqual(names["length_distribution"], {
            "1": 14, "2": 4, "3": 93, "4": 452, "5": 924, "6": 134,
        })
        self.assertEqual(names["six_glyph_count"], 134)
        self.assertEqual(len(names["six_glyph_rows"]), 134)
        rows = {row["id"]: row for row in names["six_glyph_rows"]}
        self.assertEqual(rows[1288]["display_name"], "エースバーン")
        self.assertEqual(rows[1288]["canonical_hex"], "54ae5d96ae7eff")
        self.assertEqual(rows[1363]["display_name"], "ムゲンダイナ")
        self.assertEqual(rows[1363]["canonical_hex"], "718a7e915265ff")

        self.assertEqual(inventory["consumer_count"], 40)
        self.assertEqual(inventory["instruction_patch_count"], 48)
        self.assertEqual(inventory["unreviewed_count"], 0)
        self.assertEqual(inventory["unmigrated_count"], 0)
        self.assertEqual(inventory["unknown_boundary_count"], 0)
        self.assertEqual(inventory["battle_nickname_transfer_count"], 4)
        self.assertEqual(inventory["nickname_display_bound"]["direct_call_count"], 13)
        self.assertEqual(
            inventory["nickname_display_bound"]["cfru_long_call_literal_count"], 3,
        )
        self.assertEqual(self.rom[0x88A8:0x88AA], bytes.fromhex("0624"))
        self.assertTrue(all(row["boundary_known"] and row["migrated"]
                            for row in inventory["consumers"]))
        for patch in inventory["instruction_patches"]:
            replacement = bytes.fromhex(patch["replacement_hex"])
            self.assertEqual(
                self.rom[patch["site"]:patch["site"] + len(replacement)],
                replacement,
                patch["label"],
            )
        self.assertTrue(all(
            row["destination_buffer_bytes"] == 8
            and row["new_max_visible_glyphs"] == 6
            and row["migrated"]
            for row in inventory["battle_nickname_transfers"]
        ))
        for row in inventory["battle_nickname_transfers"]:
            replacement = bytes.fromhex(row["replacement_hex"])
            self.assertEqual(
                self.rom[row["site"]:row["site"] + len(replacement)],
                replacement,
            )

    def test_summary_party_pc_battle_evolution_and_dex_display_paths(self) -> None:
        model = json.loads(self.artifacts["generated/engine/species_assets/species_assets.json"])
        self.assertEqual(set(model["display_matrix"]),
                         {"summary", "party", "pc", "battle", "evolution", "dex"})
        strides = {"front": 8, "back": 8, "palette": 8, "shiny_palette": 8,
                   "icon": 4, "icon_palette": 1, "front_coords": 4, "back_coords": 4,
                   "cry": 12, "dex_entries": 28, "national_dex": 2}
        for path, tables in model["display_matrix"].items():
            for table in tables:
                raw = self.artifacts[f"generated/engine/species_assets/{table}.bin"]
                stride = strides[table]
                self.assertEqual(len(raw), 1621 * stride, f"{path}:{table}")
                self.assertEqual(len(raw[412 * stride:413 * stride]), stride, f"{path}:{table}:appended")

        for species_id in range(1621):
            self.assertEqual(struct.unpack_from("<H", self.artifacts[
                "generated/engine/species_assets/front.bin"
            ], species_id * 8 + 6)[0], species_id)
            self.assertEqual(struct.unpack_from("<H", self.artifacts[
                "generated/engine/species_assets/back.bin"
            ], species_id * 8 + 6)[0], species_id)
            self.assertEqual(struct.unpack_from("<H", self.artifacts[
                "generated/engine/species_assets/palette.bin"
            ], species_id * 8 + 4)[0], species_id)
            self.assertEqual(struct.unpack_from("<H", self.artifacts[
                "generated/engine/species_assets/shiny_palette.bin"
            ], species_id * 8 + 4)[0], 1621 + species_id)

    def test_exact_rom_display_hooks_and_samples_are_live(self) -> None:
        patches = self.metadata["runtime"]["patches"]
        self.assertEqual(len(patches), 31)
        for patch in patches:
            replacement = bytes.fromhex(patch["replacement_hex"])
            self.assertEqual(
                self.rom[patch["site"]:patch["site"] + len(replacement)],
                replacement,
                patch["label"],
            )
        self.assertEqual(
            self.rom[
                SPECIES_PICTURE_BOUND_THUNK_CAVE:
                SPECIES_PICTURE_BOUND_THUNK_CAVE + 8
            ],
            bytes.fromhex("0048704754060000"),
        )
        self.assertEqual(
            self.metadata["species_name_consumers"]
                ["species_picture_bound_thunk_cave"],
            SPECIES_PICTURE_BOUND_THUNK_CAVE,
        )
        self.assertEqual(
            self.metadata["species_name_consumers"]
                ["species_picture_bound_thunk_pointer_references"],
            0,
        )
        for site, compare in (
            (0x0E648, 0x4285),
            (0x0EA98, 0x4282),
            (0x0E720, 0x4287),
            (0x0EB64, 0x4287),
        ):
            self.assertEqual(
                self.rom[site:site + 4],
                thumb_bl(site, SPECIES_PICTURE_BOUND_THUNK_CAVE),
            )
            self.assertEqual(
                struct.unpack_from("<HH", self.rom, site + 4),
                (compare, 0xD907),
            )
        for compare_site, fallback_load, bound_literal, fallback_literal in (
            (0x73DFC, 0x73E04, 0x73E08, 0x73E14),
            (0x73ECC, 0x73ED4, 0x73ED8, 0x73EEC),
            (0x73F2C, 0x73F34, 0x73F38, 0x73F4C),
        ):
            self.assertEqual(
                self.rom[compare_site:compare_site + 8],
                bytes.fromhex("0248844204d900bf"),
            )
            literal_pc = (0x08000000 + fallback_load + 4) & ~3
            literal_delta = 0x08000000 + fallback_literal - literal_pc
            self.assertEqual(
                struct.unpack_from("<H", self.rom, fallback_load)[0],
                0x4800 | (literal_delta // 4),
            )
            self.assertEqual(
                struct.unpack_from("<I", self.rom, bound_literal)[0], 1620,
            )
            self.assertNotEqual(
                struct.unpack_from("<I", self.rom, fallback_literal)[0], 1620,
            )
        smoke = self.metadata["runtime_smoke"]
        self.assertEqual(smoke["status"], "PASS")
        self.assertEqual(smoke["species_created"], 1619)
        self.assertEqual(smoke["species_named"], 1620)
        self.assertEqual(smoke["compatibility_names_checked"], 1620)
        self.assertEqual(smoke["six_glyph_names"], 134)
        self.assertTrue(smoke["buffer_canaries"])
        self.assertEqual(smoke["stock_string_routes"], 4)
        self.assertEqual(smoke["surface_name_routes"], 7)
        self.assertEqual(smoke["form_base_names_checked"], 3)
        self.assertEqual(smoke["battle_name_cases"], 2)
        self.assertEqual(smoke["battle_messages"], 2)
        self.assertEqual(smoke["healthbox_tile_cases"], 2)
        self.assertEqual(smoke["level100_form_cases"], 2)
        self.assertEqual(smoke["display_species_checked"], 7)
        self.assertEqual(smoke["dex_species_checked"], 5)
        self.assertEqual(smoke["egg_species"], 412)
        self.assertEqual(smoke["caterpie_species"], 649)

    def test_breeding_fixture_and_runtime(self) -> None:
        fixture = json.loads(self.artifacts["tests/fixtures/breeding_matrix.json"])
        self.assertEqual(fixture["status"], "PASS")
        self.assertGreaterEqual(len(fixture["cases"]), 18)
        with tempfile.TemporaryDirectory(prefix="t09-breed-") as raw:
            exe = Path(raw) / "fixture"
            subprocess.run([
                "cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                "-I", str(ROOT / "overlays/species_surface"),
                str(ROOT / "overlays/species_surface/species_surface.c"),
                str(ROOT / "tests/fixtures/species_surface_fixture.c"),
                "-o", str(exe),
            ], check=True)
            subprocess.run([str(exe)], check=True)


@unittest.skipUnless((ROOT / "build/stages/09_species_surface.json").is_file(), "T09 stage unavailable")
class PublishedSpeciesSurfaceTests(unittest.TestCase):
    def test_check_is_read_only(self) -> None:
        tracked = [ROOT / path for path in ARTIFACTS]
        before = {path: path.read_bytes() for path in tracked}
        self.assertEqual(check(ROOT)["status"], "PASS")
        self.assertEqual(before, {path: path.read_bytes() for path in tracked})


if __name__ == "__main__":
    unittest.main()
