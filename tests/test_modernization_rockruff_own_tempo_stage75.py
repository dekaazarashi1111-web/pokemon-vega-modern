from __future__ import annotations

import copy
import hashlib
import json
import struct
import unittest
from pathlib import Path

from tools.modernization_p04_species_runtime import SPECIES_TABLE_KEYS
from tools.modernization_rockruff_own_tempo_stage75 import (
    CONFIG_PATH,
    EGG_MOVES,
    EVOLUTION_ROW,
    EVOLUTION_STRIDE,
    EXPECTED_ARCHIVE_CARRY_MOVES,
    EXPECTED_EXISTING_CARRY_MOVES,
    EXPECTED_ROCKRUFF_ROUTE_SET_SHA256,
    EXPECTED_TOUCHED_ALLOCATION_SEQUENCES,
    GBA_ROM_BASE,
    LYCANROC_DUSK,
    NEW_SPECIES_COUNT,
    NORMAL_ROCKRUFF,
    OWN_TEMPO_ROCKRUFF,
    PROVISIONAL_LOAD_ADDRESS,
    Stage75Error,
    _accounting_chain,
    _dusk_evolution_host,
    _egg_species_host,
    _veneer,
    _wild_species_host,
    build_artifacts,
)
from tools.release.bps import apply_bps


ROOT = Path(__file__).resolve().parents[1]


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class ModernizationRockruffOwnTempoStage75Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / CONFIG_PATH).read_bytes())
        cls.parent = (ROOT / cls.config["inputs"]["rom"]["path"]).read_bytes()
        cls.artifacts = build_artifacts(ROOT)
        paths = cls.config["outputs"]
        cls.rom = cls.artifacts[paths["rom"]]
        cls.payload = cls.artifacts[paths["payload"]]
        cls.metadata = json.loads(cls.artifacts[paths["metadata"]])
        cls.audit = json.loads(cls.artifacts[paths["audit"]])
        cls.route_audit = json.loads(cls.artifacts[paths["route_audit"]])
        cls.contract = json.loads(cls.artifacts[paths["contract"]])
        cls.checkpoint = json.loads(cls.artifacts[paths["checkpoint"]])
        cls.allocation = json.loads(cls.artifacts[paths["allocation"]])
        cls.symbols = json.loads(cls.artifacts[paths["symbols"]])

    def table_row(self, key: str, species: int) -> bytes:
        table = self.metadata["tables"][key]
        index = species - 1 if key == "species_national_dex_runtime" else species
        start = int(table["new_file_offset"]) + index * int(table["stride"])
        return self.rom[start:start + int(table["stride"])]

    def symbol(self, name: str) -> int:
        return int(self.symbols["symbols"][name]["address"], 0)

    def test_identity_is_internal_non_counting_form_with_fixed_ability(self) -> None:
        identity = self.config["identity"]
        self.assertEqual(identity["reference_id"], "scarletviolet:0744.01")
        self.assertEqual(identity["classification"], "INTERNAL_CONDITIONAL_FORM")
        self.assertEqual(identity["species_id"], OWN_TEMPO_ROCKRUFF)
        self.assertEqual(identity["normal_species_id"], NORMAL_ROCKRUFF)
        self.assertEqual(identity["dusk_species_id"], LYCANROC_DUSK)
        self.assertEqual(identity["national_dex"], 744)
        self.assertEqual(identity["ability_slots"], [20, 20, 20])
        self.assertEqual(identity["collection_class"], 4)
        self.assertEqual(identity["collection_weight"], 0)
        self.assertFalse(identity["save_layout_changed"])

    def test_all_species_tables_and_consumers_are_extended_exactly_once(self) -> None:
        tables = self.metadata["tables"]
        self.assertEqual(set(tables), set(SPECIES_TABLE_KEYS))
        self.assertEqual(len(tables), 24)
        self.assertEqual(self.audit["table_pointer_consumer_count"], 310)
        self.assertEqual(self.audit["species_count_consumer_count"], 19)
        self.assertEqual(
            sum(int(row["pointer_consumer_count"]) for row in tables.values()), 310
        )
        for key, row in tables.items():
            expected = NEW_SPECIES_COUNT - (1 if key == "species_national_dex_runtime" else 0)
            self.assertEqual(row["new_count"], expected, key)
            new_pointer = struct.pack("<I", int(row["new_address"]))
            old_pointer = struct.pack("<I", int(row["old_address"]))
            for site in row["pointer_consumers"]:
                offset = int(site["site_offset"])
                self.assertEqual(self.parent[offset:offset + 4], old_pointer, key)
                self.assertEqual(self.rom[offset:offset + 4], new_pointer, key)
            old_prefix = self.parent[
                int(row["old_file_offset"]):int(row["old_file_offset"]) + int(row["old_size"])
            ]
            new_prefix = self.rom[
                int(row["new_file_offset"]):int(row["new_file_offset"]) + int(row["old_size"])
            ]
            if key == "evolution":
                expected_prefix = bytearray(old_prefix)
                start = NORMAL_ROCKRUFF * EVOLUTION_STRIDE + 16
                expected_prefix[start:start + 8] = bytes(8)
                self.assertEqual(new_prefix, bytes(expected_prefix), key)
            else:
                self.assertEqual(new_prefix, old_prefix, key)
        for row in self.metadata["count_consumers"]:
            offset = int(row["site_offset"])
            width = int(row["width"])
            self.assertEqual(
                self.parent[offset:offset + width], int(row["old"]).to_bytes(width, "little")
            )
            self.assertEqual(
                self.rom[offset:offset + width], int(row["new"]).to_bytes(width, "little")
            )

    def test_evolution_row_moves_from_normal_to_own_tempo_form(self) -> None:
        normal = self.table_row("evolution", NORMAL_ROCKRUFF)
        own = self.table_row("evolution", OWN_TEMPO_ROCKRUFF)
        self.assertEqual(normal[16:24], bytes(8))
        self.assertEqual(own[:8], EVOLUTION_ROW)
        self.assertEqual(own[8:EVOLUTION_STRIDE], bytes(EVOLUTION_STRIDE - 8))
        self.assertEqual(EVOLUTION_ROW.hex(), "1c001900ef041411")
        for level in (24, 25):
            for hour in (16, 17, 19, 20):
                expected = (
                    LYCANROC_DUSK
                    if level >= 25 and 17 <= hour < 20
                    else None
                )
                self.assertEqual(
                    _dusk_evolution_host(OWN_TEMPO_ROCKRUFF, level, hour), expected
                )
                self.assertIsNone(_dusk_evolution_host(NORMAL_ROCKRUFF, level, hour))

    def test_ability_national_dex_and_collection_rows_are_byte_exact(self) -> None:
        base = self.table_row("species_base_stats", OWN_TEMPO_ROCKRUFF)
        self.assertEqual(
            tuple(struct.unpack_from("<H", base, offset)[0] for offset in (22, 26, 28)),
            (20, 20, 20),
        )
        self.assertEqual(
            struct.unpack("<H", self.table_row("species_national_dex", OWN_TEMPO_ROCKRUFF))[0],
            744,
        )
        self.assertEqual(
            struct.unpack("<H", self.table_row("species_national_dex_runtime", OWN_TEMPO_ROCKRUFF))[0],
            744,
        )
        self.assertEqual(
            self.table_row("acquisition_collection_defs", OWN_TEMPO_ROCKRUFF),
            struct.pack("<HHBBBB", OWN_TEMPO_ROCKRUFF, 0xFFFF, 0, 0, 4, 0),
        )
        parent_collection = self.metadata["tables"]["acquisition_collection_defs"]
        old_start = int(parent_collection["old_file_offset"]) + NORMAL_ROCKRUFF * 8
        self.assertEqual(
            self.table_row("acquisition_collection_defs", NORMAL_ROCKRUFF),
            self.parent[old_start:old_start + 8],
        )
        self.assertEqual(self.contract["save"]["new_species_field_width"], "existing_u16")
        self.assertFalse(self.contract["save"]["layout_changed"])
        self.assertFalse(self.contract["save"]["migration_required"])

    def test_shared_sprite_and_palette_pointers_use_unique_tags(self) -> None:
        for key in ("species_front", "species_back"):
            normal = self.table_row(key, NORMAL_ROCKRUFF)
            own = self.table_row(key, OWN_TEMPO_ROCKRUFF)
            self.assertEqual(own[:4], normal[:4])
            self.assertEqual(struct.unpack_from("<HH", own, 4), (2048, OWN_TEMPO_ROCKRUFF))
        for key, tag in (
            ("species_palette", OWN_TEMPO_ROCKRUFF),
            ("species_shiny_palette", OWN_TEMPO_ROCKRUFF + 1621),
        ):
            normal = self.table_row(key, NORMAL_ROCKRUFF)
            own = self.table_row(key, OWN_TEMPO_ROCKRUFF)
            self.assertEqual(own[:4], normal[:4])
            self.assertEqual(struct.unpack_from("<HH", own, 4), (tag, 0))
        special = {
            "evolution", "species_base_stats", "acquisition_collection_defs",
            "species_front", "species_back", "species_palette", "species_shiny_palette",
        }
        for key in set(SPECIES_TABLE_KEYS) - special:
            self.assertEqual(
                self.table_row(key, OWN_TEMPO_ROCKRUFF),
                self.table_row(key, NORMAL_ROCKRUFF),
                key,
            )

    def test_p03_source_clone_and_all_38_carry_paths_are_exact(self) -> None:
        clone = self.route_audit["source_route_clone"]
        self.assertEqual(clone["source_reference_id"], "scarletviolet:0744.00")
        self.assertEqual(clone["target_reference_id"], "scarletviolet:0744.01")
        self.assertEqual(clone["route_count"], 60)
        self.assertEqual(clone["route_id_set_sha256"], EXPECTED_ROCKRUFF_ROUTE_SET_SHA256)
        owner = self.route_audit["owner_clone"]
        self.assertEqual(owner["route_counts"], {
            "egg": 4, "level_up": 14, "machine": 38, "shared_egg": 4, "total": 60,
        })
        self.assertEqual(tuple(owner["egg_moves"]), EGG_MOVES)
        carry = self.route_audit["pre_evolution_carry"]
        self.assertEqual(carry["path_count"], 38)
        self.assertEqual(carry["missing_owner_path_count"], 0)
        self.assertEqual(tuple(carry["existing_slot_moves"]), EXPECTED_EXISTING_CARRY_MOVES)
        self.assertEqual(tuple(carry["stage74_archive_moves"]), EXPECTED_ARCHIVE_CARRY_MOVES)
        self.assertEqual(carry["resolution_counts"], {
            "reference_existing_slot": 21, "reference_stage74_archive": 17,
        })
        self.assertEqual(self.route_audit["accounting"]["route_accounting_delta"], 0)
        self.assertEqual(self.route_audit["accounting"]["selected_routes_after"], 118369)
        self.assertEqual(self.route_audit["accounting"]["materialized_routes_after"], 83162)
        self.assertEqual(self.route_audit["exclusions"], {
            "side_change_project_move_id": 1063,
            "side_change_materialized": 0,
            "browt_pombon_gecqua_materialized": 0,
            "prohibited_coercions_materialized": 0,
            "full_p03_done": False,
        })
        parent_metadata = json.loads(
            (ROOT / self.config["inputs"]["metadata"]["path"]).read_bytes()
        )
        stage74_audit = json.loads(
            (ROOT / self.config["inputs"]["stage74_route_audit"]["path"]).read_bytes()
        )
        self.assertEqual(
            _accounting_chain(parent_metadata, stage74_audit),
            {
                "selected_routes_before": 118369,
                "selected_routes_after": 118369,
                "materialized_routes_before": 83162,
                "materialized_routes_after": 83162,
                "route_accounting_delta": 0,
            },
        )
        tampered = copy.deepcopy(parent_metadata)
        tampered["accounting"]["cumulative_runtime_materialized_routes"] += 1
        with self.assertRaisesRegex(Stage75Error, "accounting chain"):
            _accounting_chain(tampered, stage74_audit)

    def test_breeding_intercepts_only_two_species_and_delegates_every_other(self) -> None:
        breeding = self.audit["breeding"]
        self.assertEqual(breeding["get_egg_species_intercepts"], [1263, 1670])
        self.assertEqual(breeding["get_egg_species_result"], 1670)
        self.assertEqual(breeding["all_other_species"], "EXACT_PARENT_TRAMPOLINE")
        self.assertEqual(tuple(breeding["get_egg_moves_1670"]), EGG_MOVES)
        self.assertEqual(_egg_species_host(1263), 1670)
        self.assertEqual(_egg_species_host(1670), 1670)
        for species in (0, 1, 25, 283, 411, 412, 1142, 1143, 1227, 1669):
            self.assertIsNone(_egg_species_host(species), species)
        source = (
            ROOT
            / "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.c"
        ).read_text(encoding="utf-8")
        start = source.index("Stage75U16 Stage75_GetEggSpecies")
        end = source.index("Stage75U8 Stage75_GetEggMoves", start)
        function = source[start:end]
        self.assertNotIn("for (", function)
        self.assertNotIn("Stage75_Table_evolution", function)
        self.assertEqual(function.count("Stage75_OriginalGetEggSpecies(species)"), 1)

    def test_hook_preimages_veneers_and_original_trampolines_are_exact(self) -> None:
        expected_hooks = [
            {"name": "GetEggSpecies", "address": "0x08044F34", "width": 8, "parent_hex": "f0b5474680b40004", "target": "Stage75_GetEggSpecies", "continuation_thumb": "0x08044F3D"},
            {"name": "GetEggMoves", "address": "0x080451EC", "width": 8, "parent_hex": "f0b5474680b48846", "target": "Stage75_GetEggMoves", "continuation_thumb": "0x080451F5"},
            {"name": "TryGenerateWildMon", "address": "0x080826D8", "width": 8, "parent_hex": "004b1847bd414109", "target": "Stage75_TryGenerateWildMonAdapter"},
            {"name": "GetMoveRelearnerMoves", "address": "0x091141D4", "width": 8, "parent_hex": "004b1847a9a05309", "target": "Stage75_GetMoveRelearnerMoves"},
            {"name": "BuildLearnableMoveset", "address": "0x091143B8", "width": 8, "parent_hex": "004b184715a15309", "target": "Stage75_BuildLearnableMoveset"},
        ]
        self.assertEqual(self.config["parent_abi"]["hooks"], expected_hooks)
        for hook in self.config["parent_abi"]["hooks"]:
            offset = int(hook["address"], 0) - GBA_ROM_BASE
            expected = bytes.fromhex(hook["parent_hex"])
            target = self.symbol(hook["target"])
            self.assertEqual(self.parent[offset:offset + 8], expected, hook["name"])
            self.assertEqual(self.rom[offset:offset + 8], _veneer(target), hook["name"])
        item = self.config["parent_abi"]["item_script_pointer"]
        self.assertEqual(item, {
            "address": "0x092D05B4", "parent_hex": "34a65309", "target": "Stage75_ItemScript",
        })
        item_offset = int(item["address"], 0) - GBA_ROM_BASE
        self.assertEqual(self.parent[item_offset:item_offset + 4].hex(), item["parent_hex"])
        self.assertEqual(
            self.rom[item_offset:item_offset + 4],
            struct.pack("<I", self.symbol(item["target"])),
        )
        load = int(self.symbols["load_address"], 0)
        egg_species = self.symbol("Stage75_OriginalGetEggSpecies") - load
        egg_moves = self.symbol("Stage75_OriginalGetEggMoves") - load
        self.assertEqual(self.payload[egg_species:egg_species + 8].hex(), "f0b5474680b40004")
        self.assertIn(bytes.fromhex("3d4f0408"), self.payload[egg_species:egg_species + 24])
        self.assertEqual(self.payload[egg_moves:egg_moves + 8].hex(), "f0b5474680b48846")
        self.assertIn(bytes.fromhex("f5510408"), self.payload[egg_moves:egg_moves + 24])

        expected_stage73 = {
            "Stage73_SharedIndex": "0x09534C9E", "Stage73_SharedMoves": "0x0953594A",
            "Stage73_ReminderIndex": "0x09538088", "Stage73_ReminderMoves": "0x09538D34",
        }
        expected_stage74 = {
            "Stage74_MachineIndex": "0x0953A89A", "Stage74_MachineMoves": "0x0953B546",
            "Stage74_TutorIndex": "0x09548294", "Stage74_TutorMoves": "0x09548F40",
            "Stage74_PreservationIndex": "0x09549222", "Stage74_PreservationMoves": "0x09549ECE",
            "Stage74_GetMoveRelearnerMoves": "0x0953A0A9", "Stage74_BuildLearnableMoveset": "0x0953A115",
            "Stage74_PrepareMachinePages": "0x0953A1D5", "Stage74_CommitMachinePage": "0x0953A1FD",
            "Stage74_SelectedMachinePageHasMoves": "0x0953A23D", "Stage74_OpenArchiveModeMenu": "0x0953A299",
            "Stage74_OpenMachinePageMenu": "0x0953A2B1", "Stage74_TextChooseMon": "0x0953A83C",
            "Stage74_TextNoMoves": "0x0953A850", "Stage74_TextEggRejected": "0x0953A864",
            "Stage74_TextArchiveLocked": "0x0953A870", "Stage74_TextPageNoMoves": "0x0953A888",
        }
        self.assertEqual(self.config["runtime_abi"]["stage73_symbols"], expected_stage73)
        self.assertEqual(self.config["runtime_abi"]["stage74_symbols"], expected_stage74)
        self.assertEqual(len(expected_stage73) + len(expected_stage74), 22)
        for spec in self.config["runtime_abi"]["engine_thumb"].values():
            address = int(spec["address"], 0) & ~1
            offset = address - GBA_ROM_BASE
            expected = bytes.fromhex(spec["parent_hex"])
            self.assertEqual(self.parent[offset:offset + len(expected)], expected)

    def test_wild_conversion_delegates_first_and_is_deterministic_one_eighth(self) -> None:
        source = (
            ROOT
            / "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.c"
        ).read_text(encoding="utf-8")
        start = source.index("Stage75U8 Stage75_TryGenerateWildMonAdapter")
        end = source.index("Stage75U8 Stage75_GetMoveRelearnerMoves", start)
        function = source[start:end]
        self.assertLess(function.index("STAGE75_PARENT_WILD"), function.index("STAGE75_GET_MON_DATA"))
        self.assertIn("mixed *= 0x9E3779B1u", function)
        self.assertIn("mixed ^= mixed >> 16", function)
        self.assertIn("(mixed & 7u) == 0u", function)
        self.assertIn("STAGE75_SET_MON_DATA", function)
        self.assertIn("STAGE75_CALCULATE_STATS", function)

        def selected(pid: int) -> bool:
            return _wild_species_host(1, NORMAL_ROCKRUFF, pid) == OWN_TEMPO_ROCKRUFF

        hits = sum(selected(pid) for pid in range(1 << 16))
        self.assertGreaterEqual(hits, 7900)
        self.assertLessEqual(hits, 8500)
        self.assertTrue(any(not selected(pid) for pid in range(0, 1 << 12, 8)))
        self.assertTrue(any(selected(pid) for pid in range(1, 1 << 12, 8)))
        for pid in (0, 1, 0x12345678, 0xFFFFFFFF):
            self.assertEqual(_wild_species_host(0, NORMAL_ROCKRUFF, pid), NORMAL_ROCKRUFF)
            self.assertEqual(_wild_species_host(1, 25, pid), 25)
        self.assertEqual(function.count("STAGE75_SET_MON_DATA("), 1)
        self.assertNotIn("STAGE75_MON_DATA_MOVE1", function)
        self.assertNotIn("ITEM", function)
        self.assertTrue(self.config["wild_acquisition"]["normal_rockruff_retained"])
        self.assertEqual(self.config["wild_acquisition"]["additional_rng_calls"], 0)

    def test_move_memory_scripts_preserve_wait_failure_and_terminal_reset(self) -> None:
        scripts = (
            ROOT
            / "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75_scripts.S"
        ).read_text(encoding="utf-8")
        main_call = scripts.index("STAGE75_CALLNATIVE Stage75_OpenArchiveModeMenu")
        main_failure = scripts.index("STAGE75_COMPARE 0x800D, 5", main_call)
        main_wait = scripts.index(".byte 0x27", main_failure)
        self.assertLess(main_call, main_failure)
        self.assertLess(main_failure, main_wait)
        page_call = scripts.index("STAGE75_CALLNATIVE Stage75_OpenMachinePageMenu")
        page_failure = scripts.index("STAGE75_COMPARE 0x800D, 0xFFFE", page_call)
        page_wait = scripts.index(".byte 0x27", page_failure)
        self.assertLess(page_call, page_failure)
        self.assertLess(page_failure, page_wait)
        self.assertIn("STAGE75_COMPARE 0x8004, 6", scripts)
        self.assertIn("STAGE75_CALLNATIVE Stage75_ResetMode", scripts)
        finish = scripts.index("STAGE75_EXPORT Stage75_FinishScript")
        self.assertIn(".byte 0x6C, 0x02", scripts[finish:])
        build = self.audit["build_learnable"]
        self.assertEqual(build["legacy_machine_rows"], 21)
        self.assertEqual(build["archive_machine_rows"], 17)
        self.assertEqual(build["preservation_rows"], 0)
        self.assertEqual(build["own_tempo_structural_upper_bound"], 82)
        self.assertLessEqual(build["own_tempo_structural_upper_bound"], 429)
        self.assertLessEqual(build["archive_machine_rows"], 40)
        runtime = (
            ROOT
            / "overlays/modernization_rockruff_own_tempo_stage75/modernization_rockruff_own_tempo_stage75.c"
        ).read_text(encoding="utf-8")
        prepare_start = runtime.index("void Stage75_PrepareMachinePages")
        prepare_end = runtime.index("void Stage75_SelectedMachinePageHasMoves", prepare_start)
        prepare = runtime[prepare_start:prepare_end]
        self.assertIn("STAGE75_MODE_MACHINE_PAGE_0", prepare)
        self.assertIn("STAGE75_SPECIAL_RESULT = 1u", prepare)

    def test_inherited_allocation_layout_is_stable_and_only_nine_hashes_mutate(self) -> None:
        before = json.loads(
            (ROOT / self.config["inputs"]["allocation"]["path"]).read_bytes()
        )["allocations"]
        after = self.allocation["allocations"]
        self.assertEqual(len(before), 78)
        self.assertEqual(len(after), 79)
        layout = (
            "sequence", "name", "region", "alignment", "start", "end_exclusive",
            "gba_start", "gba_end_exclusive", "size", "owner", "purpose", "placement",
        )
        changed = []
        for left, right in zip(before, after[:78], strict=True):
            self.assertTrue(all(left[key] == right[key] for key in layout), left["sequence"])
            if left["content_sha256"] != right["content_sha256"]:
                changed.append(left["sequence"])
        self.assertEqual(tuple(changed), EXPECTED_TOUCHED_ALLOCATION_SEQUENCES)
        self.assertEqual(
            tuple(row["sequence"] for row in self.audit["allocation_mutations"]),
            EXPECTED_TOUCHED_ALLOCATION_SEQUENCES,
        )
        self.assertEqual(before[73]["content_sha256"], after[73]["content_sha256"])
        self.assertEqual(before[77]["content_sha256"], after[77]["content_sha256"])
        new = after[-1]
        self.assertEqual(new["sequence"], 78)
        self.assertEqual(new["start"], PROVISIONAL_LOAD_ADDRESS - GBA_ROM_BASE)
        self.assertEqual(new["content_sha256"], sha256(self.payload))
        self.assertEqual(self.allocation["summaries"]["overlap_count"], 0)

    def test_generated_rom_bps_and_checkpoint_are_reproducible(self) -> None:
        paths = self.config["outputs"]
        self.assertEqual(apply_bps(self.parent, self.artifacts[paths["incremental_bps"]]), self.rom)
        self.assertEqual(self.metadata["output"]["sha256"], sha256(self.rom))
        self.assertEqual(self.audit["output_sha256"], sha256(self.rom))
        self.assertEqual(self.audit["outside_allowlist_count"], 0)
        self.assertEqual(self.audit["payload"]["sha256"], sha256(self.payload))
        self.assertEqual(self.checkpoint["allocation"]["new_sequence"], 78)
        self.assertEqual(self.checkpoint["species_count"], NEW_SPECIES_COUNT)
        self.assertEqual(self.checkpoint["p03"]["missing_owner_paths"], 0)
        self.assertEqual(self.checkpoint["p03"]["accounting"]["route_accounting_delta"], 0)
        self.assertFalse(self.checkpoint["p03"]["full_p03_done"])
        self.assertFalse(self.checkpoint["done"])
        self.assertFalse(self.checkpoint["release_candidate"])
        for key, raw in (
            ("metadata", self.artifacts[paths["metadata"]]),
            ("allocation", self.artifacts[paths["allocation"]]),
            ("symbols", self.artifacts[paths["symbols"]]),
            ("runtime_audit", self.artifacts[paths["audit"]]),
            ("route_audit", self.artifacts[paths["route_audit"]]),
            ("contract", self.artifacts[paths["contract"]]),
        ):
            self.assertEqual(self.checkpoint[key]["size"], len(raw), key)
            self.assertEqual(self.checkpoint[key]["sha256"], sha256(raw), key)
        bps = self.artifacts[paths["incremental_bps"]]
        self.assertEqual(self.checkpoint["bps"]["size"], len(bps))
        self.assertEqual(self.checkpoint["bps"]["sha256"], sha256(bps))
        self.assertEqual(self.checkpoint["bps"]["source_sha256"], sha256(self.parent))
        self.assertEqual(self.checkpoint["bps"]["target_sha256"], sha256(self.rom))
        self.assertTrue(self.checkpoint["bps"]["round_trip"])
        self.assertFalse(self.metadata["release_candidate"])


if __name__ == "__main__":
    unittest.main()
