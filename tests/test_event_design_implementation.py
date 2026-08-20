from __future__ import annotations

import csv
import hashlib
import json
import struct
import unittest
from collections import Counter
from pathlib import Path

from scripts import build_event_design_stage as event_design
from tools.release.bps import apply_bps


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content/event_design_implementation"
BINDINGS = ROOT / "config/event_design_bindings.csv"
FLAGS = ROOT / "manifests/flags.csv"
ROM = ROOT / event_design.OUTPUT_ROM
META = ROOT / event_design.OUTPUT_META
ALLOC = ROOT / event_design.OUTPUT_ALLOC
SYMBOLS = ROOT / event_design.OUTPUT_SYMBOLS
CASES = ROOT / event_design.OUTPUT_CASES
AUDIT = ROOT / event_design.OUTPUT_AUDIT
COVERAGE = ROOT / event_design.OUTPUT_COVERAGE
QUICK = ROOT / event_design.OUTPUT_MGBA_QUICK
FULL = ROOT / event_design.OUTPUT_MGBA_FULL
CLEAN_EVIDENCE = ROOT / "build/stages/37_clean_rebuild.json"


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON root must be an object: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EventDesignSourceTests(unittest.TestCase):
    def test_normalized_source_is_byte_pinned_and_validator_clean(self) -> None:
        manifest = _json(CONTENT / "source_manifest.json")
        self.assertEqual(manifest["source_zip"]["sha256"], event_design.EXPECTED_ZIP_SHA256)
        self.assertEqual(
            manifest["source_zip"]["submission_sha256"],
            event_design.EXPECTED_SUBMISSION_SHA256,
        )
        self.assertEqual(manifest["source_zip"]["entry_count"], 6)
        self.assertEqual({row["path"] for row in manifest["files"]},
                         set(event_design.SOURCE_FILES))
        for row in manifest["files"]:
            path = CONTENT / row["path"]
            self.assertEqual(path.stat().st_size, row["size"])
            self.assertEqual(_sha(path), row["sha256"])
        report = event_design._validate_submission()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["warnings"], [])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["counts"]["open_questions"], 0)

    def test_model_counts_references_operations_and_batch_dag_are_exact(self) -> None:
        model = event_design._load_model()
        plan = model["plan"]
        self.assertEqual(
            {key: len(plan[key]) for key in (
                "arcs", "states", "actors", "placements", "conditions",
                "rewards", "events", "batches",
            )},
            {key: event_design.EXPECTED_COUNTS[key] for key in (
                "arcs", "states", "actors", "placements", "conditions",
                "rewards", "events", "batches",
            )},
        )
        self.assertEqual(len(model["dialogues"]), 326)
        self.assertEqual(len(model["coverage"]), 98)
        self.assertEqual(
            Counter(step["op"] for row in plan["events"] for step in row["steps"]),
            {
                "SHOW_DIALOGUE": 287, "CHECK_CONDITION": 106, "END": 76,
                "SET_STATE": 73, "YES_NO": 39, "START_TRAINER_BATTLE": 8,
                "GIVE_REWARD": 7, "CALL_ACQUISITION_HOST": 5,
                "OPEN_SERVICE": 3, "HEAL_PARTY": 1, "WARP_SAFE": 1,
            },
        )
        self.assertEqual(model["batch_order"][0], "BATCH_KEY_PILOT_VERMILION")
        self.assertEqual(len(model["batch_order"]), 7)
        logical = [row for row in model["coverage"]
                   if row["subject_kind"] == "LOGICAL_LOCATION"]
        self.assertEqual(len(logical), 47)
        self.assertEqual(len({row["subject_key"] for row in logical}), 47)

    def test_state_flags_use_the_exact_collision_free_monotonic_window(self) -> None:
        rows = _rows(FLAGS)
        owned = [row for row in rows if row["owner"] == "T20"]
        self.assertEqual(len(owned), 80)
        self.assertEqual(
            {int(row["id"], 0) for row in owned},
            set(range(event_design.STATE_FLAG_BASE, event_design.STATE_FLAG_END)),
        )
        all_ids = [int(row["id"], 0) for row in rows]
        self.assertEqual(len(all_ids), len(set(all_ids)))


class EventDesignPhysicalBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rom = ROM.read_bytes()
        cls.metadata = _json(META)
        cls.bindings = _rows(BINDINGS)
        cls.cases = _rows(CASES)
        cls.symbols = _json(SYMBOLS)

    def test_stage37_identity_allocator_and_declared_spans_are_exact(self) -> None:
        self.assertEqual(len(self.rom), event_design.ROM_SIZE)
        self.assertEqual(_sha(ROM), self.metadata["output"]["sha256"])
        self.assertEqual(self.metadata["input"]["sha256"],
                         event_design.EXPECTED_STAGE36_SHA256)
        self.assertEqual(self.metadata["change_audit"]["outside_declared_span_count"], 0)
        self.assertEqual(self.metadata["change_audit"]["declared_span_overlap_count"], 0)
        self.assertEqual(_json(ALLOC)["summaries"]["overlap_count"], 0)
        self.assertTrue(all(self.metadata["static_acceptance"]["checks"].values()))

    def test_all_63_bindings_are_rooted_to_live_dispatchers(self) -> None:
        self.assertEqual(len(self.bindings), 63)
        self.assertEqual(len({row["placement_key"] for row in self.bindings}), 63)
        self.assertEqual(Counter(row["allocation_policy"] for row in self.bindings), {
            "REPOINT_SOURCE_BG": 36, "RESTORE_SOURCE_OBJECT": 16,
            "NO_PHYSICAL_HOST": 9, "ALLOCATE_SAFE_TILE": 2,
        })
        payload = self.metadata["runtime"]["payload"]
        start = payload["address"]
        end = start + payload["size"]
        for row in self.bindings:
            dispatcher = int(row["dispatcher_address"], 0)
            record = int(row["stage37_record_address"], 0)
            script_site = int(row["stage37_script_pointer_address"], 0)
            self.assertTrue(start <= dispatcher < end, row["placement_key"])
            self.assertTrue(start <= record < end or row["stage37_binding_kind"]
                            == "MAP_SCRIPT_ON_TRANSITION")
            self.assertTrue(start <= script_site < end, row["placement_key"])
            self.assertIn(self.rom[dispatcher - event_design.GBA_ROM_BASE],
                          (0x6A, 0x16), row["placement_key"])
            if row["stage37_binding_kind"] != "MAP_SCRIPT_ON_TRANSITION":
                observed = struct.unpack_from(
                    "<I", self.rom, script_site - event_design.GBA_ROM_BASE,
                )[0]
                self.assertEqual(observed, dispatcher, row["placement_key"])
        orphan = [row for row in self.bindings if not row["event_keys"]]
        self.assertEqual(len(orphan), 1)
        self.assertTrue(orphan[0]["fallback_address"])

    def test_76_event_cases_and_every_root_patch_are_physical(self) -> None:
        self.assertEqual(len(self.cases), 76)
        self.assertEqual(len({row["event_key"] for row in self.cases}), 76)
        self.assertEqual(len({row["batch_key"] for row in self.cases}), 7)
        self.assertEqual(len({row["placement_key"] for row in self.cases}), 62)
        physical = self.metadata["physical_bindings"]
        self.assertEqual(physical["count"], 63)
        self.assertEqual(physical["map_event_root_count"], 57)
        self.assertEqual(physical["map_script_root_count"], 2)
        self.assertEqual(physical["direct_acquisition_roots_rebound"], 5)
        for row in physical["root_patches"]:
            offset = row["address"] - event_design.GBA_ROM_BASE
            self.assertEqual(
                self.rom[offset:offset + row["size"]],
                bytes.fromhex(row["replacement_hex"]),
                row["name"],
            )

    def test_upstream_trainer_acquisition_qol_and_service_owners_are_preserved(self) -> None:
        regression = self.metadata["regression"]
        self.assertEqual(regression["trainer_encounters"], 1302)
        self.assertEqual(regression["trainer_members"], 6490)
        self.assertEqual(regression["trainer_double"], 74)
        self.assertEqual(regression["kanto_trainers"], 201)
        self.assertEqual(regression["trainer_commands_compared"], 1302)
        self.assertEqual(regression["acquisition_events"], 201)
        self.assertEqual(regression["qol_features"], 35)
        self.assertEqual(regression["qol_hooks_compared"], 97)
        self.assertTrue(
            regression["factory_raid_save_cleanup_preserved_outside_declared_map_roots"]
        )
        self.assertEqual(
            Counter(row["result_policy"] for row in self.cases),
            {"NO_BATTLE": 63, "WIN_REQUIRED": 8,
             "ACQUISITION_TRANSACTION": 5},
        )

    def test_incremental_and_clean_direct_patches_round_trip(self) -> None:
        stage36 = (ROOT / event_design.INPUT_ROM).read_bytes()
        clean = (ROOT / event_design.CLEAN_ROM).read_bytes()
        incremental = (ROOT / event_design.PATCH_INCREMENTAL).read_bytes()
        direct = (ROOT / event_design.PATCH_CLEAN).read_bytes()
        self.assertEqual(apply_bps(stage36, incremental), self.rom)
        self.assertEqual(apply_bps(clean, direct), self.rom)


class EventDesignMgbaAndCleanRebuildTests(unittest.TestCase):
    def test_quick_full_are_independent_all_pass_and_identity_equal(self) -> None:
        quick = _json(QUICK)
        full = _json(FULL)
        for mode, document, paths in (("quick", quick, 7), ("full", full, 76)):
            self.assertEqual(document["status"], "PASS")
            self.assertEqual(document["mode"], mode)
            self.assertEqual(document["warnings_errors"], 0)
            self.assertEqual(document["process_runs"], 1)
            self.assertTrue(all(document["checks"].values()))
            self.assertEqual(document["coverage"]["executed_field_paths"], paths)
        self.assertEqual(quick["result_identity"], full["result_identity"])
        self.assertEqual(quick["rom_sha256"], full["rom_sha256"])
        self.assertEqual(quick["runner_sha256"], full["runner_sha256"])
        self.assertEqual(quick["cases_sha256"], full["cases_sha256"])
        self.assertEqual(_json(COVERAGE)["status"], "PASS")
        self.assertEqual(_json(AUDIT)["mgba"]["process_count"], 2)

    def test_clean_rebuild_chain_and_direct_identity_are_published(self) -> None:
        evidence = _json(CLEAN_EVIDENCE)
        self.assertEqual(evidence["status"], "PASS")
        self.assertTrue(evidence["bps"]["chain_direct_identity_equal"])
        self.assertTrue(evidence["bps"]["stage36_incremental"]["round_trip_exact"])
        self.assertTrue(evidence["bps"]["clean_direct"]["round_trip_exact"])
        self.assertEqual(evidence["declared_span"]["outside_declared_span_count"], 0)
        self.assertEqual(evidence["allocator_overlap_count"], 0)
        self.assertEqual(evidence["mgba"]["process_count"], 2)


if __name__ == "__main__":
    unittest.main()
