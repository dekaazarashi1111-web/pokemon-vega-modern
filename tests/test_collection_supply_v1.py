from __future__ import annotations

import csv
import hashlib
import json
import struct
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_collection_supply_v1 as builder  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


CONFIG = ROOT / "config/collection_supply_v1.json"
MODEL = ROOT / "content/collection_supply_v1/canonical_model.json"
ROM = ROOT / "build/stages/56_collection_supply_v1.gba"
METADATA = ROOT / "build/stages/56_collection_supply_v1.json"
AUDIT = ROOT / "reports/generated/collection_supply_v1_audit.json"
COVERAGE = ROOT / "reports/generated/collection_supply_v1_coverage.json"
WORLD = ROOT / "reports/generated/collection_supply_v1_world_binding.json"
SYMBOLS = ROOT / "generated/runtime/collection_supply_v1_symbols.json"
CASES = ROOT / "generated/runtime/collection_supply_v1_mgba_cases.json"
QUICK = ROOT / "build/stages/56_mgba_collection_supply_v1_quick.json"
FULL = ROOT / "build/stages/56_mgba_collection_supply_v1_full.json"
CLEAN_REBUILD = ROOT / "build/stages/56_collection_supply_v1_clean_rebuild.json"

TASK = "USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION"
LAYOUT_OWNER = "USER_20260827_COLLECTION_SUPPLY_V1"
ROM_SHA256 = "9309c073798dc363174458ebcb75bf3f1e86d475dcd129b74875d5a6bb875778"
ZIP_SHA256 = "8a1b271e9b321f6409f2b766a1b469cec15a8353dfb023d99184cd305fb641db"
FINGERPRINT = "bf957958e2fa3e1672cddb484cb35e8f1d2c3df46a5eef34759ec5007c1de4bd"

COUNTS = {
    "forms": 388, "gmax": 34, "items": 999, "hosts": 14,
    "pool_entries": 292, "reward_entries": 217,
    "host_requirements": 9, "batches": 8, "source_raids": 256,
    "added_gmax_raids": 32, "added_form_raids": 4,
    "shared_captures": 125,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON root must be object: {path}")
    return value


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class CollectionSupplyV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = _json(CONFIG)
        cls.model = _json(MODEL)
        cls.metadata = _json(METADATA)
        cls.audit = _json(AUDIT)

    def test_private_submission_identity_and_validator_are_exact(self) -> None:
        contract = self.config["inputs"]["submission_zip"]  # type: ignore[index]
        archive_path = ROOT / str(contract["path"])  # type: ignore[index]
        self.assertEqual(archive_path.stat().st_size, 41_513)
        self.assertEqual(_sha(archive_path), ZIP_SHA256)
        with zipfile.ZipFile(archive_path) as archive:
            self.assertEqual(tuple(archive.namelist()), builder.EXPECTED_ZIP_ENTRIES)
            self.assertIsNone(archive.testzip())
            report = json.loads(archive.read("VALIDATION_REPORT.json"))
            manifest = json.loads(archive.read("SUBMISSION_MANIFEST.json"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["warnings"], [])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["open_questions"], 0)
        self.assertEqual(report["submission_fingerprint"], FINGERPRINT)
        self.assertEqual(manifest["submission_fingerprint"], FINGERPRINT)

    def test_canonical_rows_routes_and_exclusions_are_complete(self) -> None:
        self.assertEqual(self.model["counts"], COUNTS)
        forms = self.model["forms"]  # type: ignore[assignment]
        gmax = self.model["gmax"]  # type: ignore[assignment]
        items = self.model["items"]  # type: ignore[assignment]
        pools = self.model["pool_entries"]  # type: ignore[assignment]
        rewards = self.model["reward_entries"]  # type: ignore[assignment]
        self.assertEqual(len(forms), 388)
        self.assertEqual(len(gmax), 34)
        self.assertEqual(len(items), 999)
        self.assertEqual(len(pools), 292)
        self.assertEqual(len(rewards), 217)
        self.assertEqual(
            sum(row["source_raid_key"] != "NONE" for row in pools), 256
        )
        self.assertEqual(
            sum(row["source_raid_key"] == "NONE" for row in pools), 36
        )
        excluded = {
            row["item_id"] for row in items if row["source"] == "EXCLUDED"
        }
        self.assertEqual(len(excluded), 69)
        self.assertTrue(excluded.isdisjoint(
            row["item_id"] for row in rewards
        ))
        self.assertEqual(self.model["coverage"], {
            "direct_gmax_species_distribution": 0,
            "excluded_items_in_runtime_supply": 0,
            "factory_primary_items_with_raid_supply": 20,
            "gmax_bases_with_positive_raid_chance": 32,
            "stage26_completion_target": 1206,
            "stage26_enabling_forms": 10,
        })
        self.assertEqual(self.model["item_source_counts"], {
            "MONEY_SHOP": 86, "BP_SHOP": 354, "RESEARCH_SHOP": 207,
            "FACTORY_REWARD": 20, "RAID_REWARD": 64, "NPC_GIFT": 82,
            "FORM_SERVICE": 18, "STORY_EVENT": 30,
            "VEGA_EXISTING": 69, "EXCLUDED": 69,
        })

    def test_exact_rom_patches_and_declared_spans(self) -> None:
        self.assertEqual(ROM.stat().st_size, 32 * 1024 * 1024)
        self.assertEqual(_sha(ROM), ROM_SHA256)
        self.assertEqual(self.metadata["status"], "PASS")
        self.assertEqual(self.metadata["task"], TASK)
        self.assertEqual(self.metadata["output"]["sha256"], ROM_SHA256)  # type: ignore[index]
        self.assertEqual(self.audit["change_audit"]["outside_declared_span_count"], 0)  # type: ignore[index]
        self.assertEqual(self.audit["change_audit"]["declared_span_overlap_count"], 0)  # type: ignore[index]
        self.assertEqual(self.audit["overlap_audit"], {
            "status": "PASS", "rom": 0, "ram": 0, "save": 0,
            "hook": 0, "map_host": 0,
        })
        rom = ROM.read_bytes()
        for patch in self.metadata["hooks"]:  # type: ignore[union-attr]
            start = int(patch["start"])
            self.assertEqual(
                rom[start:int(patch["end_exclusive"])].hex(),
                patch["replacement_hex"],
            )

    def test_fourteen_physical_hosts_are_normal_a_bg_events(self) -> None:
        world = _json(WORLD)
        self.assertEqual(world["status"], "PASS")
        self.assertEqual(world["host_count"], 14)
        self.assertEqual(world["invariants"], {
            "new_maps": 0, "new_objects": 0, "new_full_screen_ui": 0,
            "existing_arrays_preserved_by_copy": True,
            "ordinary_a_input": True, "collision_count": 0,
        })
        rom = ROM.read_bytes()
        seen_maps: set[tuple[int, int]] = set()
        for index, (binding, patch) in enumerate(zip(
                world["bindings"], world["map_pointer_patches"], strict=True)):  # type: ignore[arg-type]
            seen_maps.add((binding["map_group"], binding["map_num"]))
            self.assertEqual(binding["host_index"], index)
            self.assertEqual(binding["input_contract"], "NORMAL_FIELD_A_ON_BG_EVENT")
            self.assertEqual(binding["new_object_count"], 0)
            self.assertEqual(binding["existing_event_collision_count"], 0)
            self.assertEqual(binding["cell"]["collision"], 0)
            self.assertGreaterEqual(binding["cell"]["walkable_adjacent_cells"], 2)
            target = struct.unpack_from("<I", rom, int(patch["start"]))[0]
            self.assertEqual(target, patch["target"])
            event = target - 0x08000000
            self.assertEqual(rom[event + 3], binding["bg_count_after"])
        self.assertEqual(len(seen_maps), 14)

    def test_owner_layout_and_stage26_contract_are_isolated(self) -> None:
        self.assertEqual(self.audit["layout_audit"], {
            "status": "PASS", "owner_address": 0x0203D900,
            "owner_size": 512, "parasite_offset": 0x2818,
            "sector": 31, "sector_read_offset": 0x964,
            "ram_owner_count": 2, "ram_overlap_count": 0,
            "save_owner_count": 1, "save_overlap_count": 0,
        })
        stage26 = self.audit["stage26_regression"]  # type: ignore[assignment]
        self.assertEqual(stage26["status"], "PASS")
        self.assertEqual(stage26["completion_target"], 1206)
        self.assertEqual(stage26["enabling_forms"], 10)
        self.assertEqual(stage26["stage55_to_stage56_changed_bytes"], 0)
        save_rows = _rows(ROOT / "config/save_layout.csv")
        ram_rows = _rows(ROOT / "config/ram_layout.csv")
        self.assertEqual(
            sum(row.get("owner") == LAYOUT_OWNER for row in save_rows), 1
        )
        self.assertEqual(
            sum(row.get("owner") == LAYOUT_OWNER for row in ram_rows), 2
        )

    def test_symbols_mgba_vault_and_world_regressions_are_all_pass(self) -> None:
        symbols = _json(SYMBOLS)
        self.assertTrue(builder.REQUIRED_ENTRYPOINTS <= set(symbols["symbols"]))  # type: ignore[arg-type]
        self.assertEqual(symbols["stage"], 56)
        self.assertIn("upstream_vault", symbols)
        cases = _json(CASES)
        self.assertEqual(cases["expected_tests"], list(builder.EXPECTED_TESTS))
        quick, full = _json(QUICK), _json(FULL)
        for mode, document in (("quick", quick), ("full", full)):
            self.assertEqual(document["mode"], mode)
            self.assertEqual(document["status"], "PASS")
            self.assertEqual(
                set(document["tests"]), set(builder.EXPECTED_TESTS)  # type: ignore[arg-type]
            )
            self.assertTrue(all(document["tests"].values()))  # type: ignore[union-attr]
            self.assertEqual(document["warnings"], 0)
            self.assertEqual(document["warnings_errors"], 0)
            self.assertEqual(document["coverage"]["vault_batch"], 30)  # type: ignore[index]
            self.assertEqual(document["coverage"]["raw_record_bytes"], 80)  # type: ignore[index]
        self.assertEqual(quick["tests"], full["tests"])
        self.assertEqual(quick["rom_sha256"], full["rom_sha256"])
        world_e2e = self.metadata["world_input_e2e"]  # type: ignore[assignment]
        self.assertEqual(world_e2e["status"], "PASS")
        self.assertEqual(world_e2e["process_runs"], 2)
        self.assertEqual(world_e2e["fixture_count"], 22)
        self.assertTrue(world_e2e["identical_results"])
        self.assertEqual(world_e2e["warnings"], 0)
        self.assertEqual(self.audit["vault_regression"]["status"], "PASS")  # type: ignore[index]
        self.assertEqual(self.audit["vault_regression"]["batch_size"], 30)  # type: ignore[index]
        self.assertTrue(self.audit["vault_regression"]["mail_rejection"])  # type: ignore[index]

    def test_bps_and_clean_rebuild_are_exact(self) -> None:
        inputs = self.config["inputs"]  # type: ignore[assignment]
        outputs = self.config["outputs"]  # type: ignore[assignment]
        clean = (ROOT / inputs["clean_rom"]["path"]).read_bytes()
        stage55 = (ROOT / inputs["stage55_rom"]["path"]).read_bytes()
        stage56 = ROM.read_bytes()
        incremental = (ROOT / outputs["incremental_bps"]).read_bytes()
        direct = (ROOT / outputs["clean_bps"]).read_bytes()
        self.assertEqual(apply_bps(stage55, incremental), stage56)
        self.assertEqual(apply_bps(clean, direct), stage56)
        evidence = _json(CLEAN_REBUILD)
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(evidence["output"]["sha256"], ROM_SHA256)  # type: ignore[index]
        self.assertTrue(evidence["routes"]["source_build"]["two_runs_byte_identical"])  # type: ignore[index]
        self.assertFalse(evidence["acceptance"]["ipad_required"])  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
