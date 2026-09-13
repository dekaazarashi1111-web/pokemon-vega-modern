from __future__ import annotations

import copy
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts import build_modernization_p03_stage67 as builder  # noqa: E402
from tools import modernization_p03_stage67 as core  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


class ModernizationP03Stage67Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / builder.DEFAULT_CONFIG).read_text(encoding="utf-8")
        )
        outputs = cls.config["outputs"]
        cls.rom = (ROOT / outputs["rom"]).read_bytes()
        cls.metadata = json.loads(
            (ROOT / outputs["metadata"]).read_text(encoding="utf-8")
        )
        cls.checkpoint = json.loads(
            (ROOT / outputs["checkpoint"]).read_text(encoding="utf-8")
        )
        cls.route = json.loads(
            (ROOT / outputs["route_audit"]).read_text(encoding="utf-8")
        )
        cls.change = json.loads(
            (ROOT / outputs["change_audit"]).read_text(encoding="utf-8")
        )
        cls.allocation = json.loads(
            (ROOT / outputs["allocation"]).read_text(encoding="utf-8")
        )
        cls.evidence = json.loads(
            (ROOT / outputs["mgba_evidence"]).read_text(encoding="utf-8")
        )
        # immutable ZIP全体のstreamはtest processで1回だけ行う。
        cls.built = core.build_stage67_image(ROOT, builder.DEFAULT_CONFIG)

    def test_exact_generator_matches_all_published_core_artifacts(self) -> None:
        outputs = self.config["outputs"]
        self.assertEqual(self.built.rom, self.rom)
        for key, value in (
            ("allocation", self.built.allocation),
            ("route_audit", self.built.route_audit),
            ("change_audit", self.built.change_audit),
        ):
            self.assertEqual(core.stable_json(value), (ROOT / outputs[key]).read_bytes())
        self.assertEqual(
            hashlib.sha256(self.rom).hexdigest(),
            "13e4ecb6f2bc72eeb5d7ffb5b5e5a7a2ae2876391bf37ec93cb6548587265111",
        )

    def test_route_partition_and_move_1063_non_adoption_are_exact(self) -> None:
        validation = self.route["source_validation"]
        material = self.route["materialization"]
        self.assertEqual(validation["source_route_count"], 118528)
        self.assertEqual(validation["selected_route_count"], 118369)
        self.assertEqual(validation["non_adopted_route_count"], 159)
        self.assertEqual(material["parent_stage66_routes_materialized"], 47548)
        self.assertEqual(material["stage67_new_routes_materialized"], 3603)
        self.assertEqual(material["cumulative_routes_materialized"], 51151)
        self.assertEqual(material["selected_routes_deferred"], 67218)
        non_adopted = self.route["non_adopted"]
        self.assertEqual(non_adopted["project_move_id"], 1063)
        self.assertEqual(non_adopted["route_count"], 159)
        self.assertFalse(non_adopted["counts_as_remaining_runtime_work"])
        self.assertTrue(all(row["project_move_id"] == 1063 for row in non_adopted["routes"]))
        self.assertTrue(all(row["replacement_move_key"] is None for row in non_adopted["routes"]))

    def test_all_evolution_routes_are_leading_level_zero_rows(self) -> None:
        root = int(self.change["roots"]["level_root_runtime_address"], 16) - core.ROM_BASE
        payload_start = self.change["output_tables"]["evolution_payload_rom_offset"]
        payload_end = payload_start + self.change["output_tables"]["evolution_payload_size"]
        routes = 0
        for case in self.built.runtime_cases["evolution"]:
            species = case["species_id"]
            pointer = struct.unpack_from("<I", self.rom, root + species * 4)[0]
            offset = pointer - core.ROM_BASE
            self.assertGreaterEqual(offset, payload_start)
            self.assertLess(offset, payload_end)
            for expected in case["moves"]:
                move = self.rom[offset] | self.rom[offset + 1] << 8
                self.assertEqual((move, self.rom[offset + 2]), (expected, 0))
                self.assertNotEqual(move, 1063)
                routes += 1
                offset += 3
        self.assertEqual((len(self.built.runtime_cases["evolution"]), routes), (330, 341))

    def test_all_existing_slot_tutor_routes_replace_target_rows(self) -> None:
        root = int(self.change["roots"]["tutor_root_runtime_address"], 16) - core.ROM_BASE
        catalog = int(self.change["roots"]["tutor_catalog_runtime_address"], 16) - core.ROM_BASE
        total = 0
        for case in self.built.runtime_cases["tutor"]:
            row = self.rom[root + case["species_id"] * 16:root + case["species_id"] * 16 + 16]
            slots = core._set_bits(row, slots=64)
            self.assertEqual(slots, case["set_slots"])
            moves = [struct.unpack_from("<H", self.rom, catalog + slot * 2)[0] for slot in slots]
            self.assertEqual(moves, case["moves"])
            total += len(slots)
        self.assertEqual((len(self.built.runtime_cases["tutor"]), total), (290, 740))

    def test_normal_egg_table_repairs_both_roots_and_excludes_special_routes(self) -> None:
        roots = self.change["roots"]
        self.assertEqual(roots["egg_output_root_runtime_address"], "0x09FED0C4")
        self.assertEqual(roots["egg_output_scan_limit"], 7557)
        for site in (0x45214, 0x4528C):
            self.assertEqual(struct.unpack_from("<I", self.rom, site)[0], 0x09FED0C4)
        self.assertEqual(struct.unpack_from("<I", self.rom, 0x45288)[0], 7557)
        rows, order, raw = core._parse_egg_table(self.rom, 0x09FED0C4)
        expected = {row["species_id"]: tuple(row["moves"]) for row in self.built.runtime_cases["egg"]}
        self.assertEqual(len(expected), 450)
        self.assertEqual(sum(map(len, expected.values())), 2522)
        self.assertTrue(all(rows[species] == moves for species, moves in expected.items()))
        self.assertNotIn(344, rows[24])
        self.assertEqual((len(order), len(raw), hashlib.sha256(raw).hexdigest()), (
            1399, 15118, "d9feba3494b83578dab53ab260705fada1f6ca64a18b5b5e52e37c3abab1f3a8",
        ))
        egg = self.route["egg_boundary"]
        self.assertEqual((egg["special_breeding_routes_deferred"],
                          egg["legacy_alias_collision_routes_deferred"],
                          egg["incense_union_conflict_routes_deferred"]), (1, 9, 31))

    def test_p02_overlay_and_declared_change_domains_are_preserved(self) -> None:
        self.assertEqual(self.change["changed_byte_count"], 46455)
        self.assertEqual(self.change["outside_declared_range_count"], 0)
        self.assertEqual(self.change["stage66_cumulative_changed_byte_count"], 46515)
        self.assertTrue(self.change["parent_chain"]["p02_overlay_bytes_preserved"])
        spans = (0x1F898B8, 0x1F91AB8, 0x1F94DB8, 0x1F98FB8, 0x1F993B8, 0x1F9CFB8)
        for offset in spans:
            self.assertEqual(struct.unpack_from("<H", self.rom, offset)[0], 4)
            self.assertEqual(struct.unpack_from("<H", self.rom, offset + 8)[0], 35)
        changed = [
            index for index, pair in enumerate(zip(self.built.parent, self.rom, strict=True))
            if pair[0] != pair[1]
        ]
        self.assertEqual(core.sha256(core.stable_json(changed)), self.change["changed_offsets_sha256"])

    def test_allocation_is_first_fit_non_overlapping_and_in_bounds(self) -> None:
        summary = self.allocation["summaries"]
        self.assertEqual((summary["allocation_count"], summary["overlap_count"]), (71, 0))
        added = self.allocation["allocations"][-2:]
        self.assertEqual([row["sequence"] for row in added], [69, 70])
        self.assertEqual([row["start"] for row in added], [0x1FE8D1C, 0x1FED0C4])
        self.assertEqual([row["size"] for row in added], [17319, 15118])
        ordered = sorted(self.allocation["allocations"], key=lambda row: row["start"])
        self.assertTrue(all(left["end_exclusive"] <= right["start"]
                            for left, right in zip(ordered, ordered[1:])))

    def test_bps_round_trips_bind_exact_parent_and_clean_rom(self) -> None:
        outputs = self.config["outputs"]
        incremental = (ROOT / outputs["incremental_bps"]).read_bytes()
        clean_bps = (ROOT / outputs["clean_bps"]).read_bytes()
        clean = (ROOT / self.config["inputs"]["clean_rom"]["path"]).read_bytes()
        self.assertEqual(apply_bps(self.built.parent, incremental), self.rom)
        self.assertEqual(apply_bps(clean, clean_bps), self.rom)
        self.assertEqual(self.metadata["bps"]["incremental"]["source_sha256"],
                         hashlib.sha256(self.built.parent).hexdigest())

    def test_mgba_gate_executed_every_materialized_route_in_two_processes(self) -> None:
        self.assertEqual(self.evidence["status"], "PASS")
        self.assertEqual(self.evidence["execution"]["process_runs"], 2)
        self.assertTrue(self.evidence["execution"]["independent_processes"])
        result = self.evidence["runtime_result"]
        self.assertEqual(result["counts"], {
            "evolution_species": 330, "evolution_routes": 341,
            "tutor_species": 290, "tutor_positive_routes": 740,
            "tutor_negative_calls": 290, "egg_species": 450, "egg_routes": 2522,
        })
        self.assertTrue(result["payload_pc_seen"])
        self.assertFalse(result["scheduler_e2e"])
        self.assertFalse(result["breeding_e2e"])
        self.assertFalse(result["save_reload_e2e"])
        self.assertFalse(result["full_p03_acceptance"])

    def test_checkpoint_never_claims_p03_done_and_rejects_scope_tamper(self) -> None:
        self.assertEqual(self.metadata["status"], "CHECKPOINT")
        self.assertFalse(self.metadata["done"])
        self.assertEqual(self.checkpoint["checkpoint_marker"], "CHECKPOINT_NOT_P03_DONE")
        self.assertEqual(self.checkpoint["remaining_work"]["selected_routes"], 67218)
        self.assertFalse(self.checkpoint["scope"]["all_p03_routes_implemented"])
        tampered = copy.deepcopy(self.config)
        tampered["scope"]["cumulative_materialized_routes"] += 1
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "tampered.json"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaisesRegex(core.ModernizationP03Stage67Error, "scope"):
                core.build_stage67_image(ROOT, path)


if __name__ == "__main__":
    unittest.main()
