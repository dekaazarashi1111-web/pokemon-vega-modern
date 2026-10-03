from __future__ import annotations

import copy
import hashlib
import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts import build_modernization_p03_stage65 as builder  # noqa: E402
from scripts import run_modernization_p03_stage65_mgba as mgba  # noqa: E402
from tools import modernization_p03_stage65 as core  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


class ModernizationP03Stage65Tests(unittest.TestCase):
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
        cls.allocation = json.loads(
            (ROOT / outputs["allocation"]).read_text(encoding="utf-8")
        )
        cls.evidence = json.loads(
            (ROOT / outputs["mgba_evidence"]).read_text(encoding="utf-8")
        )

    def test_stable_identity_and_exact_four_route_contract(self) -> None:
        target = self.config["target"]
        self.assertEqual(target["species_key"], "SPECIES_KEY_CATERPIE")
        self.assertEqual(target["species_id"], 649)
        self.assertEqual(target["reference_id"], "swordshield:0010.00")
        self.assertEqual(
            target["adoption_policy"],
            "REPLACE_NORMAL_TARGET_WITH_FIXED_REFERENCE_NOT_UNION",
        )
        self.assertEqual(
            [
                (row["route_id"], row["project_move_id"], row["learning_level"])
                for row in target["level_up_routes"]
            ],
            [
                ("e84468471e2a5389cab08c6e", 33, 1),
                ("bcf11b7de237f5503621f3b4", 81, 1),
                ("9d24844ef808e40888791e37", 535, 9),
            ],
        )
        self.assertEqual(
            (
                target["machine_route"]["route_id"],
                target["machine_route"]["source_machine_item"],
                target["machine_route"]["project_move_id"],
                target["machine_route"]["runtime_slot_zero_based"],
            ),
            ("f47d1fe9a44cbb635c1de248", "TM82", 489, 116),
        )
        self.assertEqual(self.checkpoint["contract_gate"]["corrected_routes"], 118528)
        self.assertEqual(self.checkpoint["contract_gate"]["caterpie_routes_selected"], 4)

    def test_level_table_uses_real_root_and_replacement_rows(self) -> None:
        audit = self.checkpoint["change_audit"]["level_up"]
        self.assertEqual(audit["root_runtime_address"], "0x093A4CAC")
        self.assertEqual(audit["parent_species_pointer"], "0x0939B81E")
        self.assertEqual(audit["stage65_species_pointer"], "0x09FDA23C")
        pointer_offset = audit["species_pointer_entry_rom_offset"]
        self.assertEqual(struct.unpack_from("<I", self.output, pointer_offset)[0], 0x09FDA23C)
        payload_offset = audit["payload_rom_offset"]
        self.assertEqual(
            self.output[payload_offset:payload_offset + 12].hex(),
            "2100015100011702090000ff",
        )
        self.assertEqual(
            audit["stage65_rows"],
            [
                {"project_move_id": 33, "level": 1},
                {"project_move_id": 81, "level": 1},
                {"project_move_id": 535, "level": 9},
            ],
        )
        self.assertIn({"project_move_id": 562, "level": 26}, audit["parent_rows"])
        self.assertNotIn({"project_move_id": 562, "level": 26}, audit["stage65_rows"])
        self.assertTrue(audit["replacement_not_union"])

    def test_tm82_maps_to_catalog_move489_at_runtime_slot116_only(self) -> None:
        audit = self.checkpoint["change_audit"]["machine"]
        self.assertEqual(audit["compatibility_root_runtime_address"], "0x0944BD00")
        self.assertEqual(audit["catalog_root_runtime_address"], "0x0944BB80")
        self.assertEqual(audit["source_machine_item"], "TM82")
        self.assertEqual(audit["runtime_slot_zero_based"], 116)
        self.assertEqual(audit["catalog_project_move_id"], 489)
        self.assertEqual(audit["parent_set_slots"], [44, 63])
        self.assertEqual(audit["stage65_set_slots"], [116])
        offset = audit["compatibility_row_rom_offset"]
        row = self.output[offset:offset + 16]
        self.assertEqual([slot for slot in range(128) if row[slot // 8] & 1 << slot % 8], [116])
        self.assertTrue(audit["replacement_not_union"])

    def test_change_is_only_declared_17_bytes_in_three_table_domains(self) -> None:
        differences = [
            index
            for index, (before, after) in enumerate(zip(self.parent, self.output, strict=True))
            if before != after
        ]
        self.assertEqual(len(differences), 17)
        self.assertEqual(
            self.checkpoint["change_audit"]["changed_spans"],
            [
                {"start": 0x013A56D0, "end_exclusive": 0x013A56D3, "size": 3},
                {"start": 0x0144E595, "end_exclusive": 0x0144E596, "size": 1},
                {"start": 0x0144E597, "end_exclusive": 0x0144E598, "size": 1},
                {"start": 0x0144E59E, "end_exclusive": 0x0144E59F, "size": 1},
                {"start": 0x01FDA23C, "end_exclusive": 0x01FDA247, "size": 11},
            ],
        )
        self.assertEqual(self.checkpoint["change_audit"]["outside_declared_range_count"], 0)
        self.assertEqual(
            hashlib.sha256(self.output).hexdigest(),
            "116781c8be7cbd327ba7783ebdad9d9dda77554c33839eebed15ae6b065bb680",
        )

    def test_allocation_is_first_fit_non_overlapping_and_accounted(self) -> None:
        added = self.allocation["allocations"][-1]
        self.assertEqual(added["sequence"], 67)
        self.assertEqual(added["region"], "future_tail")
        self.assertEqual(added["placement"], "FIRST_FIT")
        self.assertEqual(added["start"], 0x01FDA23C)
        self.assertEqual(added["end_exclusive"], 0x01FDA248)
        self.assertEqual(added["size"], 12)
        self.assertEqual(added["content_sha256"], core.sha256(bytes.fromhex(
            "2100015100011702090000ff"
        )))
        for region in ("integration_modules", "future_tail"):
            intervals = sorted(
                (row["start"], row["end_exclusive"])
                for row in self.allocation["allocations"] if row["region"] == region
            )
            self.assertTrue(all(left[1] <= right[0] for left, right in zip(intervals, intervals[1:])))
        self.assertEqual(self.allocation["summaries"]["overlap_count"], 0)
        self.assertEqual(self.allocation["summaries"]["allocated_bytes"], 2999296)
        self.assertEqual(self.allocation["summaries"]["remaining_allocatable_bytes"], 1915904)

    def test_incremental_and_clean_bps_round_trip(self) -> None:
        outputs = self.config["outputs"]
        incremental = (ROOT / outputs["incremental_bps"]).read_bytes()
        clean_bps = (ROOT / outputs["clean_bps"]).read_bytes()
        clean = (ROOT / self.config["inputs"]["clean_rom"]["path"]).read_bytes()
        self.assertEqual(apply_bps(self.parent, incremental), self.output)
        self.assertEqual(apply_bps(clean, clean_bps), self.output)
        self.assertEqual(len(incremental), 63)
        self.assertTrue(self.checkpoint["bps"]["incremental"]["round_trip"])
        self.assertTrue(self.checkpoint["bps"]["clean"]["round_trip"])

    def test_mgba_two_processes_execute_both_real_consumers(self) -> None:
        evidence = self.evidence
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(
            evidence["classification"],
            "REAL_CONSUMER_DIRECT_CALL_BOUNDED_NOT_SCHEDULER_E2E",
        )
        self.assertEqual(evidence["execution"]["process_runs"], 2)
        self.assertTrue(evidence["execution"]["independent_processes"])
        self.assertTrue(evidence["execution"]["identical_results"])
        result = evidence["runtime_result"]
        self.assertEqual(result["level_up"]["symbol"], "0x091142A0")
        self.assertEqual(result["level_up"]["rows"], [[33, 1], [81, 1], [535, 9]])
        self.assertEqual(result["level_up"]["moves"], [33, 81, 535])
        self.assertEqual(result["machine"]["symbol"], "0x09110184")
        self.assertEqual(result["machine"]["catalog_move_id"], 489)
        self.assertEqual(result["machine"]["cases"]["slot116"]["result"], 1)
        self.assertEqual(result["machine"]["cases"]["old_slot44"]["result"], 0)
        self.assertEqual(result["machine"]["cases"]["old_slot63"]["result"], 0)
        self.assertTrue(result["payload_pc_seen"])
        self.assertFalse(evidence["claims"]["scheduler_e2e"])
        self.assertFalse(evidence["claims"]["full_p03_acceptance"])

    def test_level_tamper_fails_closed_before_rom_mutation(self) -> None:
        tampered = copy.deepcopy(self.config)
        tampered["target"]["level_up_routes"][2]["learning_level"] = 10
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="p03-stage65-test-", dir=local) as raw:
            path = Path(raw) / "tampered.json"
            path.write_bytes(core.stable_json(tampered))
            with self.assertRaisesRegex(
                core.ModernizationP03Stage65Error,
                "採用済み1/1/9",
            ):
                core.build_stage65_image(ROOT, path)

    def test_checkpoint_explicitly_keeps_full_p03_open(self) -> None:
        for document in (self.metadata, self.checkpoint):
            self.assertEqual(document["status"], "CHECKPOINT")
            self.assertFalse(document["done"])
            self.assertEqual(document["checkpoint_marker"], "CHECKPOINT_NOT_P03_DONE")
            self.assertEqual(document["scope"]["routes_materialized_by_this_checkpoint"], 4)
            self.assertEqual(document["scope"]["routes_not_materialized_by_this_checkpoint"], 118524)
            self.assertFalse(document["scope"]["all_p03_routes_implemented"])
            self.assertFalse(document["scope"]["move_1063_implemented"])
            self.assertEqual(document["acceptance"]["full_p03_materialization_gate"], "NOT_RUN")
        self.assertEqual(
            self.checkpoint["remaining_work"]["move_1063"],
            "BLOCKING_RUNTIME_DEPENDENCY_NOT_IMPLEMENTED",
        )

    def test_check_commands_are_deterministic_and_read_only(self) -> None:
        output_paths = [
            ROOT / value
            for key, value in self.config["outputs"].items()
            if key != "mgba_evidence"
        ] + [ROOT / self.config["outputs"]["mgba_evidence"]]
        before = {
            path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
            for path in output_paths
        }
        commands = [
            ["python3", "scripts/run_modernization_p03_stage65_mgba.py", "check"],
            ["python3", "scripts/build_modernization_p03_stage65.py", "check"],
        ]
        for command in commands:
            completed = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("PASS", completed.stdout)
        after = {
            path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
            for path in output_paths
        }
        self.assertEqual(before, after)

    def test_runner_source_is_read_only_and_stack_isolated(self) -> None:
        source = (ROOT / self.config["runtime_gate"]["runner_source"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("BATTLE_CORE_ISOLATE_HOST_CALL_STACK", source)
        self.assertIn("P03_GET_LEVEL_UP_SYMBOL = 0x091142A0U", source)
        self.assertIn("P03_CAN_LEARN_TMHM_SYMBOL = 0x09110184U", source)
        self.assertIn("call_bounded(", source)
        self.assertIn("mCoreLoadFile", source)
        self.assertNotIn("mCoreLoadSaveFile", source)
        self.assertIn(r'\"read_only\":true', source)
        self.assertIn(r'\"artifacts_written\":[]', source)


if __name__ == "__main__":
    unittest.main()
