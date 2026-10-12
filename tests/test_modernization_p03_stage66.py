from __future__ import annotations

import copy
import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts import build_modernization_p03_stage66 as builder  # noqa: E402
from tools import modernization_p03_stage66 as core  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


class ModernizationP03Stage66Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(
            (ROOT / builder.DEFAULT_CONFIG).read_text(encoding="utf-8")
        )
        outputs = cls.config["outputs"]
        cls.parent = (ROOT / cls.config["inputs"]["parent_rom"]["path"]).read_bytes()
        cls.output = (ROOT / outputs["rom"]).read_bytes()
        cls.metadata = json.loads(
            (ROOT / outputs["metadata"]).read_text(encoding="utf-8")
        )
        cls.checkpoint = json.loads(
            (ROOT / outputs["checkpoint"]).read_text(encoding="utf-8")
        )
        cls.route_audit = json.loads(
            (ROOT / outputs["route_audit"]).read_text(encoding="utf-8")
        )
        cls.change_audit = json.loads(
            (ROOT / outputs["change_audit"]).read_text(encoding="utf-8")
        )
        cls.evidence = json.loads(
            (ROOT / outputs["mgba_evidence"]).read_text(encoding="utf-8")
        )
        cls.allocation = json.loads(
            (ROOT / outputs["allocation"]).read_text(encoding="utf-8")
        )
        cls.index = json.loads(
            (ROOT / cls.config["inputs"]["p03_compiled_index"]["path"]).read_text(
                encoding="utf-8"
            )
        )
        # 1回だけimmutable ZIP全体をstreamし、公開生成物とのbyte一致を検査する。
        cls.built = core.build_stage66_image(ROOT, builder.DEFAULT_CONFIG)

    def test_exact_generator_matches_published_core_artifacts(self) -> None:
        outputs = self.config["outputs"]
        self.assertEqual(self.built.rom, self.output)
        self.assertEqual(
            core.stable_json(self.built.allocation),
            (ROOT / outputs["allocation"]).read_bytes(),
        )
        self.assertEqual(
            core.stable_json(self.built.route_audit),
            (ROOT / outputs["route_audit"]).read_bytes(),
        )
        self.assertEqual(
            core.stable_json(self.built.change_audit),
            (ROOT / outputs["change_audit"]).read_bytes(),
        )

    def test_all_level_routes_are_accounted_and_runtime_ready_subset_is_serialized(self) -> None:
        level = self.route_audit["materialization"]["level_up"]
        self.assertEqual(level["input_routes"], 18530)
        self.assertEqual(level["target_count"], 1300)
        self.assertEqual(level["runtime_ready_routes_materialized"], 18515)
        self.assertEqual(level["move_1063_routes_deferred"], 15)
        deferred = level["deferred_routes"]
        self.assertEqual(len(deferred), 15)
        self.assertTrue(all(row["project_move_id"] == 1063 for row in deferred))
        self.assertTrue(all(
            row["reason"] == "MOVE_1063_ENGINE_AND_TABLES_NOT_IMPLEMENTED"
            for row in deferred
        ))

        level_root = int(self.change_audit["roots"]["level_root_runtime_address"], 16)
        level_root_offset = level_root - core.ROM_BASE
        payload_start = self.change_audit["output_tables"]["level_payload_rom_offset"]
        payload_end = payload_start + self.change_audit["output_tables"]["level_payload_size"]
        serialized_count = 0
        pointers: list[int] = []
        for record in self.index["records"]:
            species_id = record["canonical_id"]
            pointer = struct.unpack_from("<I", self.output, level_root_offset + species_id * 4)[0]
            pointers.append(pointer)
            self.assertEqual(pointer % 2, 0)
            cursor = pointer - core.ROM_BASE
            self.assertGreaterEqual(cursor, payload_start)
            self.assertLess(cursor, payload_end)
            while True:
                move = self.output[cursor] | self.output[cursor + 1] << 8
                level_value = self.output[cursor + 2]
                cursor += 3
                if move == 0 and level_value == 0xFF:
                    break
                self.assertLessEqual(move, 1062)
                self.assertNotEqual(move, 1063)
                serialized_count += 1
        self.assertEqual(len(set(pointers)), 1300)
        self.assertEqual(serialized_count, 18515)

    def test_existing_slot_machine_routes_replace_1300_target_rows(self) -> None:
        machine = self.route_audit["materialization"]["machine"]
        self.assertEqual(machine["input_routes"], 55380)
        self.assertEqual(machine["existing_slot_routes_materialized"], 29033)
        self.assertEqual(machine["unique_target_slot_bits"], 29033)
        self.assertEqual(machine["supply_required_routes_deferred"], 26347)
        self.assertEqual(machine["targets_with_set_bits"], 1261)
        self.assertEqual(machine["targets_with_zero_bits"], 39)

        root = int(
            self.change_audit["roots"]["machine_compatibility_root_runtime_address"],
            16,
        ) - core.ROM_BASE
        total_bits = 0
        for record in self.index["records"]:
            offset = root + record["canonical_id"] * 16
            total_bits += sum(value.bit_count() for value in self.output[offset:offset + 16])
        self.assertEqual(total_bits, 29033)

    def test_all_nine_compiled_consumers_match_the_p03_contract(self) -> None:
        validation = self.route_audit["source_validation"]
        self.assertEqual(validation["corrected_target_count"], 1300)
        self.assertEqual(validation["compiled_route_count"], 118528)
        self.assertTrue(validation["all_nine_consumers_streamed_and_validated"])
        self.assertEqual(
            {key: row["count"] for key, row in validation["compiled_consumers"].items()},
            core.EXPECTED_CONSUMER_COUNTS,
        )
        self.assertTrue(all(
            row["matches_p03_contract"]
            for row in validation["compiled_consumers"].values()
        ))
        materialization = self.route_audit["materialization"]
        self.assertEqual(materialization["materialized_routes"], 47548)
        self.assertEqual(materialization["deferred_routes"], 70980)
        self.assertEqual(
            materialization["move_1063_routes_by_consumer"],
            core.EXPECTED_SIDE_CHANGE_COUNTS,
        )

    def test_roots_are_measured_and_only_declared_domains_change(self) -> None:
        roots = self.change_audit["roots"]
        self.assertEqual(roots["level_root_runtime_address"], "0x093A4CAC")
        self.assertEqual(
            roots["machine_compatibility_root_runtime_address"], "0x0944BD00"
        )
        self.assertEqual(roots["machine_catalog_root_runtime_address"], "0x0944BB80")
        self.assertTrue(roots["measured_from_exact_stage65_parent"])
        self.assertEqual(self.change_audit["changed_byte_count"], 81693)
        self.assertEqual(self.change_audit["changed_span_count"], 3520)
        self.assertEqual(self.change_audit["outside_declared_range_count"], 0)
        self.assertEqual(
            hashlib.sha256(self.output).hexdigest(),
            "0d92f5377b4ad1a2fa5cbf905f81b5b6162e16cdd09a12c65c4a342e73c5c97e",
        )
        changed = [
            index
            for index, (before, after) in enumerate(zip(self.parent, self.output, strict=True))
            if before != after
        ]
        self.assertEqual(len(changed), 81693)
        self.assertEqual(
            core.sha256(core.stable_json(changed)),
            self.change_audit["changed_offsets_sha256"],
        )

    def test_non_adopted_vega_rows_and_parent_payloads_are_preserved(self) -> None:
        preservation = self.change_audit["preservation"]
        self.assertEqual(preservation["non_adopted_species_count"], 321)
        self.assertTrue(preservation["non_adopted_rows_unchanged"])
        self.assertFalse(preservation["parent_level_payloads_destructively_overwritten"])
        self.assertTrue(preservation["replacement_policy_applies_only_to_corrected_targets"])
        target_ids = {row["canonical_id"] for row in self.index["records"]}
        level_root = int(self.change_audit["roots"]["level_root_runtime_address"], 16) \
            - core.ROM_BASE
        machine_root = int(
            self.change_audit["roots"]["machine_compatibility_root_runtime_address"],
            16,
        ) - core.ROM_BASE
        for species_id in sorted(set(range(core.SPECIES_COUNT)) - target_ids):
            self.assertEqual(
                self.parent[level_root + species_id * 4:level_root + species_id * 4 + 4],
                self.output[level_root + species_id * 4:level_root + species_id * 4 + 4],
            )
            self.assertEqual(
                self.parent[machine_root + species_id * 16:machine_root + species_id * 16 + 16],
                self.output[machine_root + species_id * 16:machine_root + species_id * 16 + 16],
            )

    def test_allocation_is_first_fit_non_overlapping_and_accounted(self) -> None:
        added = self.allocation["allocations"][-1]
        self.assertEqual(added["sequence"], 68)
        self.assertEqual(added["region"], "future_tail")
        self.assertEqual(added["placement"], "FIRST_FIT")
        self.assertEqual(added["start"], 0x01FDA248)
        self.assertEqual(added["end_exclusive"], 0x01FE8D1C)
        self.assertEqual(added["size"], 60116)
        self.assertEqual(
            added["content_sha256"],
            "0bde103cdbc375ec7842a72b79ba9cd85a9ea54e2d489848f5e098696281a09b",
        )
        for region in ("integration_modules", "future_tail"):
            intervals = sorted(
                (row["start"], row["end_exclusive"])
                for row in self.allocation["allocations"]
                if row["region"] == region
            )
            self.assertTrue(all(
                left[1] <= right[0] for left, right in zip(intervals, intervals[1:])
            ))
        self.assertEqual(self.allocation["summaries"]["overlap_count"], 0)
        self.assertEqual(self.allocation["summaries"]["allocated_bytes"], 3059412)
        self.assertEqual(
            self.allocation["summaries"]["remaining_allocatable_bytes"], 1855788
        )

    def test_incremental_and_clean_bps_round_trip(self) -> None:
        outputs = self.config["outputs"]
        incremental = (ROOT / outputs["incremental_bps"]).read_bytes()
        clean_bps = (ROOT / outputs["clean_bps"]).read_bytes()
        clean = (ROOT / self.config["inputs"]["clean_rom"]["path"]).read_bytes()
        self.assertEqual(apply_bps(self.parent, incremental), self.output)
        self.assertEqual(apply_bps(clean, clean_bps), self.output)
        self.assertEqual(len(incremental), 86322)
        self.assertEqual(
            hashlib.sha256(incremental).hexdigest(),
            "6d3bd8f75b8603f00d0f729ae0fe8bbcedce515ecaaaeecc423d13e0f0e14ed0",
        )
        self.assertTrue(self.checkpoint["bps"]["incremental"]["round_trip"])
        self.assertTrue(self.checkpoint["bps"]["clean"]["round_trip"])

    def test_mgba_two_processes_execute_four_representatives(self) -> None:
        evidence = self.evidence
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(
            evidence["classification"],
            "REAL_CONSUMER_DIRECT_CALL_BOUNDED_NOT_SCHEDULER_E2E",
        )
        self.assertEqual(evidence["execution"]["process_runs"], 2)
        self.assertTrue(evidence["execution"]["independent_processes"])
        self.assertTrue(evidence["execution"]["identical_results"])
        samples = evidence["runtime_result"]["samples"]
        self.assertEqual(
            [row["species_id"] for row in samples], [10, 858, 1620, 649]
        )
        self.assertEqual([row["level_count"] for row in samples], [13, 15, 13, 3])
        self.assertTrue(all(row["positive_result"] == 1 for row in samples))
        self.assertTrue(all(row["negative_result"] == 0 for row in samples))
        self.assertTrue(evidence["runtime_result"]["payload_pc_seen"])
        self.assertFalse(evidence["claims"]["scheduler_e2e"])
        self.assertFalse(evidence["claims"]["full_p03_acceptance"])

    def test_checkpoint_explicitly_keeps_full_p03_open(self) -> None:
        for document in (self.metadata, self.checkpoint):
            self.assertEqual(document["status"], "CHECKPOINT")
            self.assertFalse(document["done"])
            self.assertEqual(document["checkpoint_marker"], "CHECKPOINT_NOT_P03_DONE")
            self.assertEqual(
                document["scope"]["routes_materialized_by_this_checkpoint"], 47548
            )
            self.assertEqual(
                document["scope"]["routes_not_materialized_by_this_checkpoint"], 70980
            )
            self.assertFalse(document["scope"]["all_p03_routes_implemented"])
            self.assertFalse(document["scope"]["move_1063_implemented"])
            self.assertEqual(
                document["acceptance"]["full_p03_materialization_gate"],
                "PARTIAL_NOT_COMPLETE",
            )

    def test_scope_tamper_fails_before_source_stream(self) -> None:
        tampered = copy.deepcopy(self.config)
        tampered["bulk_scope"]["machine_existing_slot_routes"] += 1
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p03-stage66-test-", dir=local) as raw:
            path = Path(raw) / "tampered.json"
            path.write_bytes(core.stable_json(tampered))
            with self.assertRaisesRegex(
                core.ModernizationP03Stage66Error,
                "bulk scope",
            ):
                core.build_stage66_image(ROOT, path)

    def test_runner_is_read_only_and_stack_isolated(self) -> None:
        source = (ROOT / self.config["runtime_gate"]["runner_source"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("BATTLE_CORE_ISOLATE_HOST_CALL_STACK", source)
        self.assertIn("P03_SAMPLE_COUNT = 4U", source)
        self.assertIn("call_bounded(", source)
        self.assertIn("mCoreLoadFile", source)
        self.assertNotIn("mCoreLoadSaveFile", source)
        self.assertIn('\\"read_only\\":true', source)
        self.assertIn('\\"artifacts_written\\":[]', source)


if __name__ == "__main__":
    unittest.main()
