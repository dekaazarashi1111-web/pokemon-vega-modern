from __future__ import annotations

import hashlib
import json
import stat
import sys
import unittest
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_reward_encounters_v2 as builder  # noqa: E402
from scripts import rebuild_reward_encounters_v2_from_clean as rebuild  # noqa: E402
from tools.release.bps import apply_bps  # noqa: E402


CONFIG = ROOT / "config/reward_encounters_v2.json"
MODEL = ROOT / "content/reward_encounters_v2/canonical_model.json"
RUNTIME = ROOT / "overlays/reward_encounters_v2/reward_encounters_v2.c"
SUBMISSION = (
    ROOT
    / "userfile/imports/Pokemon-Vega_REWARD-ENCOUNTERS-V2_IMPLEMENTATION-READY.zip"
)
STAGE40 = ROOT / "build/stages/40_research_economy_v1.gba"
STAGE41 = ROOT / "build/stages/41_reward_encounters_v2.gba"
METADATA = ROOT / "build/stages/41_reward_encounters_v2.json"
ALLOCATION = ROOT / "build/stages/41_allocation.json"
INCREMENTAL_BPS = (
    ROOT
    / "build/patches/research-economy-stage40-to-reward-encounters-stage41.bps"
)
DIRECT_BPS = (
    ROOT
    / "build/patches/firered-jpn-rev0-to-reward-encounters-stage41.bps"
)
CLEAN = ROOT / "inputs/private/FireRed_JPN_Rev0_clean.gba"
QUICK = ROOT / "build/stages/41_mgba_reward_encounters_v2_quick.json"
FULL = ROOT / "build/stages/41_mgba_reward_encounters_v2_full.json"
MATRIX = ROOT / "build/stages/41_reward_encounters_v2_transaction_matrix.json"
CLEAN_EVIDENCE = ROOT / "build/stages/41_clean_rebuild.json"
COVERAGE = ROOT / "reports/generated/reward_encounters_v2_coverage.json"


ZIP_SHA256 = "b293c9f9c65eaf7acf4a6c5707163460b095d761283dc821d920801b38262195"
ZIP_SIZE = 19_169
FINGERPRINT = "823664fd0f53a88014f361ba592838084ad660101a724e416f3ddffb507a42df"
STAGE40_SHA256 = "b46e28935675198db09f5947e6701918deafb49db27c03343f4b5b2ddaceb488"
CLEAN_SHA256 = "1e4af44b0c75cc8649bfb8649dc4ae5850bf5358bd6b9cd0bf779c99f9db1486"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"JSON root must be an object: {path}")
    return value


class RewardEncountersSourceContractTests(unittest.TestCase):
    def test_private_submission_identity_inventory_and_mode_are_exact(self) -> None:
        self.assertEqual(SUBMISSION.stat().st_size, ZIP_SIZE)
        self.assertEqual(_sha(SUBMISSION), ZIP_SHA256)
        self.assertEqual(stat.S_IMODE(SUBMISSION.stat().st_mode), 0o444)
        with zipfile.ZipFile(SUBMISSION) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), 10)
            self.assertEqual(len(names), len(set(names)))
            self.assertIsNone(archive.testzip())
            self.assertTrue(all(not name.startswith(("/", "../")) for name in names))
            self.assertEqual(set(names), builder.EXPECTED_MEMBERS)
            digest = hashlib.sha256()
            for name in sorted(builder.EXPECTED_MEMBERS - {
                "SUBMISSION_MANIFEST.json", "VALIDATION_REPORT.json",
            }):
                digest.update(name.encode("utf-8"))
                digest.update(b"\0")
                digest.update(archive.read(name))
                digest.update(b"\0")
            self.assertEqual(digest.hexdigest(), FINGERPRINT)

    def test_canonical_rows_prices_and_stable_keys_are_exact(self) -> None:
        model = _json(MODEL)
        services = model["services"]
        pool = model["pool_entries"]
        sources = model["credit_sources"]
        dialogues = model["dialogues"]
        batches = model["batches"]
        self.assertEqual([len(services), len(pool), len(sources), len(dialogues), len(batches)],
                         [4, 24, 10, 4, 5])
        self.assertEqual(
            [(row["tier"], row["credit_cost"], row["bp_direct_price"])
             for row in services],
            [("RANDOM", 1, 8), ("HABITAT", 1, 15),
             ("TYPE", 1, 25), ("RARE", 1, 50)],
        )
        self.assertEqual(Counter(row["tier"] for row in pool), {
            "RANDOM": 6, "HABITAT": 6, "TYPE": 6, "RARE": 6,
        })
        self.assertEqual(len({row["species_id"] for row in pool}), 24)
        self.assertEqual(len({row["entry_key"] for row in pool}), 24)
        flat_dialogues = [row for group in dialogues for row in group]
        self.assertEqual(len(flat_dialogues), 56)
        self.assertEqual(len({row["dialogue_key"] for row in flat_dialogues}), 56)
        self.assertEqual(model["normalization"], {
            "batch_count": 5,
            "credit_source_count": 10,
            "dialogue_count": 56,
            "forbidden_species": 0,
            "open_questions": 0,
            "pool_entry_count": 24,
            "service_count": 4,
            "stable_key_duplicates": 0,
            "unresolved_references": 0,
        })

    def test_runtime_uses_one_persist_owner_and_normal_capture_owner(self) -> None:
        source = RUNTIME.read_text(encoding="utf-8")
        self.assertEqual(source.count("FN_TRY_SAVING_DATA(0u)"), 1)
        self.assertNotIn("FN_TRY_WRITE_SECTOR", source)
        self.assertNotIn("VegaSaveCompleteCapture", source)
        self.assertIn("FN_START_SCRIPTED_WILD_BATTLE", source)
        self.assertIn("REWARD_BATTLE_NO_EXP_EV", source)
        self.assertIn("REWARD_DELEGATE_RESEARCH_WILD_END", source)
        self.assertIn("entry_index / 6u != pending->pool", source)
        self.assertIn("pending->transaction_id == 0u", source)


class RewardEncountersBuildContractTests(unittest.TestCase):
    def test_builder_reproduces_all_static_outputs_without_mutation(self) -> None:
        outputs = builder.build_outputs()
        dynamic = {
            builder.OUTPUT_META.as_posix(),
            builder.OUTPUT_AUDIT.as_posix(),
            builder.OUTPUT_COVERAGE.as_posix(),
            builder.OUTPUT_REPORT.as_posix(),
        }
        for name, expected in outputs.items():
            if name not in dynamic:
                self.assertEqual((ROOT / name).read_bytes(), expected, name)

    def test_stage41_bps_routes_are_byte_identical(self) -> None:
        self.assertEqual(_sha(CLEAN), CLEAN_SHA256)
        self.assertEqual(_sha(STAGE40), STAGE40_SHA256)
        stage41 = STAGE41.read_bytes()
        self.assertEqual(apply_bps(STAGE40.read_bytes(), INCREMENTAL_BPS.read_bytes()), stage41)
        self.assertEqual(apply_bps(CLEAN.read_bytes(), DIRECT_BPS.read_bytes()), stage41)
        metadata = _json(METADATA)
        self.assertEqual(metadata["output"]["sha256"], _sha(STAGE41))
        self.assertEqual(metadata["status"], "PASS")
        self.assertEqual(metadata["overlap_audit"], {
            "hook": 0, "map": 0, "ram": 0, "rom": 0, "save": 0,
        })
        self.assertEqual(metadata["change_audit"]["outside_declared_span_count"], 0)
        self.assertEqual(metadata["change_audit"]["declared_span_overlap_count"], 0)
        self.assertEqual(_json(ALLOCATION)["summaries"]["overlap_count"], 0)

    def test_field_hook_and_upstream_delegation_are_rooted(self) -> None:
        metadata = _json(METADATA)
        field = metadata["physical_binding"]
        self.assertEqual((field["group"], field["number"]), (96, 5))
        self.assertEqual((field["objects_before"], field["objects_after"]), (4, 5))
        self.assertEqual(field["scientist_local_id"], 5)
        self.assertTrue(field["reachable_adjacent"])
        self.assertTrue(field["warps_preserved"])
        bindings = metadata["consumer_bindings"]
        self.assertTrue(bindings["delegate_chain"]["wild_end_to_t23"])
        self.assertEqual(bindings["patch_count"], 2)
        self.assertEqual(metadata["upstream_regression"], {
            "previous_allocations_changed_outside_roots": 0,
            "stage40_mgba_status": "PASS",
            "stage40_status": "PASS",
            "stage40_task": "T23",
        })

    def test_transaction_matrix_and_acceptance_are_complete(self) -> None:
        matrix = _json(MATRIX)
        self.assertEqual(matrix["status"], "PASS")
        self.assertEqual(matrix["row_count"], 32)
        self.assertEqual(sum(matrix["categories"].values()), 32)
        self.assertTrue(all(matrix["checks"].values()))
        coverage = _json(COVERAGE)
        self.assertEqual(set(coverage["acceptance"]), set(builder.ACCEPTANCE_KEYS))
        for row in coverage["acceptance"].values():
            self.assertEqual(row["status"], "PASS")
            self.assertTrue(all(row["evidence"].values()))


class RewardEncountersEvidenceTests(unittest.TestCase):
    def test_mgba_quick_full_are_independent_complete_and_identical(self) -> None:
        quick = _json(QUICK)
        full = _json(FULL)
        for mode, document in (("quick", quick), ("full", full)):
            self.assertEqual(document["mode"], mode)
            self.assertEqual(document["status"], "PASS")
            self.assertEqual(document["process_runs"], 1)
            self.assertEqual(document["warnings"], 0)
            self.assertEqual(document["warnings_errors"], 0)
            self.assertEqual(document["total"], len(document["tests"]))
            self.assertTrue(all(document["tests"].values()))
            self.assertTrue(all(document["acceptance_checks"].values()))
            self.assertEqual(document["coverage"]["transaction_rows"], 32)
        for key in (
            "result_identity", "rom_sha256", "runner_sha256",
            "symbols_sha256", "cases_sha256",
        ):
            self.assertEqual(quick[key], full[key])

    def test_clean_rebuild_evidence_revalidates_without_writes(self) -> None:
        evidence, report, evidence_path = rebuild._validate()
        self.assertEqual(evidence["status"], "PASS")
        self.assertEqual(evidence["task"], "T24")
        self.assertEqual(evidence["input_output"]["stage41_sha256"], _sha(STAGE41))
        self.assertEqual(evidence["mgba"]["process_count"], 2)
        self.assertEqual(evidence["transaction_contract"]["row_count"], 32)
        self.assertTrue(all(evidence["acceptance"].values()))
        self.assertEqual((ROOT / evidence_path).read_bytes(), rebuild._stable(evidence))
        self.assertEqual((ROOT / rebuild.REPORT).read_bytes(), report)


if __name__ == "__main__":
    unittest.main()
