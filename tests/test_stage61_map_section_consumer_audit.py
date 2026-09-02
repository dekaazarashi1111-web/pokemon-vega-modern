from __future__ import annotations

import json
from pathlib import Path
import unittest

import tools.stage61_map_section_consumer_audit as audit


ROOT = Path(__file__).resolve().parents[1]


class Stage61MapSectionConsumerAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean = (ROOT / audit.CLEAN_ROM_RELATIVE).read_bytes()
        cls.stage60 = (ROOT / audit.STAGE60_ROM_RELATIVE).read_bytes()
        cls.report = audit.build_audit_report(ROOT)

    def test_exact_input_identities_and_three_source_snapshots(self) -> None:
        report = self.report
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(
            report["status"], "FAIL_UNCOVERED_DANGEROUS_INDEX_CONSUMERS"
        )
        self.assertEqual(
            report["inputs"]["clean_rom"]["sha256"], audit.CLEAN_ROM_SHA256
        )
        self.assertEqual(
            report["inputs"]["stage60_rom"]["sha256"], audit.STAGE60_ROM_SHA256
        )
        self.assertEqual(report["inputs"]["decomp"]["commit"], audit.DECOMP_COMMIT)
        self.assertEqual(report["inputs"]["cfru"]["commit"], audit.CFRU_COMMIT)
        self.assertEqual(report["inputs"]["dpe"]["commit"], audit.DPE_COMMIT)
        self.assertEqual(
            report["inputs"]["cfru"]["profile"]["sha256"],
            audit.CFRU_PROFILE_SHA256,
        )
        self.assertTrue(
            all(report["inputs"]["cfru"]["profile"]["assertions"].values())
        )

    def test_source_and_binary_reverse_reference_universes_are_complete(self) -> None:
        proof = self.report["proof"]
        self.assertEqual(proof["source_references"]["direct_reference_count"], 66)
        self.assertEqual(
            proof["cfru_source_references"]["direct_reference_count"], 41
        )
        self.assertEqual(
            len(proof["clean_xrefs"]["direct_g_map_header_section_reads"]), 16
        )
        stage60_direct = proof["stage60_xrefs"][
            "direct_g_map_header_section_reads"
        ]
        self.assertEqual(len(stage60_direct), 17)
        self.assertIn(
            {
                "literal_load": "0x0911FED0",
                "section_load": "0x0911FED4",
            },
            stage60_direct,
        )
        self.assertNotIn(
            {
                "literal_load": "0x0911FD4A",
                "section_load": "0x0911FD58",
            },
            stage60_direct,
        )
        literal_xrefs = proof["cfru_literal_xrefs"]
        self.assertEqual(
            len(literal_xrefs["GetCurrentRegionMapSectionId"]["literal_sites"]),
            25,
        )
        self.assertEqual(len(literal_xrefs["GetMapName"]["literal_sites"]), 4)
        self.assertEqual(
            len(literal_xrefs["Overworld_GetMapHeaderByGroupAndId"]["literal_sites"]),
            2,
        )

    def test_all_consumer_groups_are_classified_and_required_set_is_exact(self) -> None:
        consumers = self.report["consumers"]
        self.assertEqual(
            [row["consumer_id"] for row in consumers],
            [f"MSC-{index:02d}" for index in range(1, 29)],
        )
        required_ids = {
            row["consumer_id"] for row in self.report["required_fixes"]
        }
        self.assertEqual(
            required_ids,
            {
                "MSC-04",
                "MSC-05",
                "MSC-06",
                "MSC-07",
                "MSC-10",
                "MSC-11",
                "MSC-15",
                "MSC-16",
                "MSC-17",
                "MSC-21",
                "MSC-22",
                "MSC-23",
            },
        )
        self.assertEqual(
            {row["consumer_id"] for row in self.report["dormant_risks"]},
            {"MSC-12", "MSC-26"},
        )

    def test_raid_underflow_is_an_exact_active_oob_contract(self) -> None:
        conclusion = self.report["conclusions"]
        self.assertEqual(conclusion["uncovered_dangerous_index_count"], 2)
        self.assertEqual(
            [
                row["consumer_id"]
                for row in conclusion["uncovered_raw_stock_table_index_consumers"]
            ],
            ["MSC-21", "MSC-22"],
        )
        raid = self.report["proof"]["expanded_tables"]["raid"]
        self.assertEqual(raid["sha256"], audit.RAID_TABLE_SHA256)
        self.assertEqual(raid["row_count"], 109)
        self.assertEqual(raid["row_size"], 56)
        self.assertEqual(raid["populated_rows"], [14])
        self.assertEqual(raid["project_index_range_after_u8_sub_87"], [169, 221])
        self.assertTrue(raid["all_project_indices_out_of_bounds"])
        self.assertEqual(
            raid["pointer_sites"],
            ["0x090F3854", "0x090F3A98", "0x090F3FC8"],
        )

    def test_cfru_roamer_stock_position_tables_are_out_of_bounds(self) -> None:
        roamer = self.report["proof"]["expanded_tables"][
            "town_map_roamer_layout"
        ]
        self.assertEqual(roamer["row_count"], 109)
        self.assertEqual(roamer["project_index_range_after_u8_sub_88"], [168, 220])
        self.assertTrue(roamer["all_project_indices_out_of_bounds"])
        self.assertEqual(
            roamer["corners_pointer_sites"], ["0x080C4F20", "0x09125FB8"]
        )
        self.assertEqual(
            roamer["dimensions_pointer_sites"], ["0x080C4F1C", "0x09125FBC"]
        )

    def test_evolution_and_swarm_consumers_are_proven_dormant(self) -> None:
        tables = self.report["proof"]["expanded_tables"]
        evolution = tables["evolution"]
        self.assertEqual(evolution["sha256"], audit.CFRU_EVOLUTION_TABLE_SHA256)
        self.assertEqual(evolution["evo_map_method"], 19)
        self.assertEqual(evolution["evo_map_rows"], 0)
        self.assertNotIn("19", evolution["method_counts"])
        self.assertEqual(tables["swarm"]["length"], 0)
        self.assertFalse(tables["swarm"]["map_section_comparisons_reachable"])

    def test_pokedex_lookup_is_semantically_empty_but_memory_safe(self) -> None:
        table = self.report["proof"]["pokedex_table"]
        self.assertEqual(table["stage60_sha256"], audit.STAGE60_POKEDEX_KANTO_TABLE_SHA256)
        self.assertEqual(
            table["project_key_hits"],
            [
                {"table_index": 33, "map_section": 0, "dex_area": 0},
                {"table_index": 37, "map_section": 0, "dex_area": 0},
            ],
        )
        self.assertTrue(set(range(1, 53)).isdisjoint(table["stage60_keys"]))

    def test_every_declared_preimage_is_exact_in_its_owner_rom(self) -> None:
        audit.verify_preimages(
            self.clean,
            (*audit.COVERED_BOUNDARY_SITES, *audit.UNRESOLVED_SEMANTIC_SITES),
            label="test clean",
        )
        audit.verify_preimages(
            self.stage60,
            (
                *audit.COVERED_BOUNDARY_SITES,
                *audit.UNRESOLVED_SEMANTIC_SITES,
                *audit.STAGE60_EXPANDED_SITES,
            ),
            label="test Stage60",
        )
        expanded = {row.name: row for row in audit.STAGE60_EXPANDED_SITES}
        self.assertEqual(
            expanded["cfru_raid_determine_species_index"].address, 0x090F371C
        )
        self.assertEqual(
            expanded["cfru_raid_determine_species_index"].expected.hex(),
            "573c2006030e440de41a64194a4ee400a559002d58d03619",
        )
        self.assertEqual(
            expanded["cfru_town_map_roamer_position_index"].address,
            0x09125F12,
        )

    def test_identity_and_preimage_checks_fail_closed(self) -> None:
        mutated_clean = bytearray(self.clean)
        mutated_clean[0] ^= 1
        with self.assertRaisesRegex(
            audit.MapSectionConsumerAuditError, "SHA-256 mismatch"
        ):
            audit.validate_rom_identity(
                bytes(mutated_clean),
                size=audit.CLEAN_ROM_SIZE,
                sha256=audit.CLEAN_ROM_SHA256,
                label="mutated clean",
            )

        site = audit.STAGE60_EXPANDED_SITES[0]
        mutated_stage60 = bytearray(self.stage60)
        mutated_stage60[site.address - audit.ROM_BASE] ^= 1
        with self.assertRaisesRegex(
            audit.MapSectionConsumerAuditError,
            "preimage mismatch: cfru_raid_determine_species_index",
        ):
            audit.verify_preimages(
                bytes(mutated_stage60),
                (site,),
                label="mutated Stage60",
            )

    def test_report_is_machine_readable_json(self) -> None:
        encoded = json.dumps(self.report, ensure_ascii=False, sort_keys=True)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["schema_version"], 2)
        self.assertEqual(decoded["conclusions"]["uncovered_dangerous_index_count"], 2)


if __name__ == "__main__":
    unittest.main()
